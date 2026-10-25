# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from blend_context import blend_context_from_workstation_session
from blend_operator_store import (
    BlendOperatorProvider,
    BlendOperatorRecord,
    blend_capability_operator_record,
    new_blend_capability_operator_provider,
    new_blend_skill_operator_provider,
)
from blend_workflow import (
    blend_workflow_plan_from_skill_compose_arguments,
)
from blend_workflow_execution import (
    BlendWorkflowExecutionEvent,
    execute_blend_workflow,
    resolve_blend_workflow_steps_from_providers,
)
from blend_workflow_store import (
    load_blend_workflow_plan,
    load_blend_workflow_run,
)
from capability_runtime import runtime_skill_declaration_for_artifact
from execution_frameworks import ability_executor_framework, normalize_ability_runtime_content
from applied_theory_types import json_safe
from realized_host_interaction.action_dispatch import (
    execute_shared_host_interaction_action,
    is_shared_host_interaction_action_capability,
)
from realized_host_interaction.delegation import (
    artifact_with_delegated_virtual_mounts,
    build_host_interaction_delegated_mounts,
    host_interaction_delegation_requires_escalation,
    normalized_requested_delegation,
)
from realized_host_interaction.models import HostInteractionAttachment
from realized_host_interaction.resolution import (
    normalize_host_interaction_attachment_relative_path,
    normalize_host_interaction_delegation_targets,
    primary_workspace_attachment,
    resolve_host_interaction_attachment_reference,
    safe_join_within_attachment_root,
)
from semantic_text import collapse_ws
from skill_lifecycle import synthesized_skill_lifecycle
from skill_schema_io import normalized_skill_bundle_filename_for_source
from skill_export_projection import batch_skill_export_filename, skill_kind_from_artifact
from skill_governance import evaluate_skill_admission
from workstation.foundation.host.governance import workstation_governance_inventory
from workstation.foundation.host.controller_runtime import controller_runtime_provider
from workstation.foundation.events.event_bus import publish_workstation_event
from workstation.foundation.host.host_interaction import workstation_host_interaction_attachments
from workstation.foundation.models import WorkstationAttachment, WorkstationSession
from workstation.foundation.projections import workstation_workflow_graph_view
from workstation.skills.core.skill_management import (
    export_workstation_skill,
    import_workstation_skill_file,
    workstation_skill_catalog_payload,
    write_workstation_skill_catalog,
)
from workstation.skills.core.skill_invocation import (
    bounded_nested_capability_grants,
    bounded_nested_effect_traces,
    bounded_nested_output_payload,
    list_available_workstation_skills,
    resolve_workstation_skill,
    workstation_nested_skill_terminal_error,
    workstation_explicit_invocation_payload,
    workstation_skill_invocation_request,
    workstation_skill_invocation_result,
    workstation_missing_required_inputs,
    workstation_nested_skill_answer_text,
    workstation_nested_skill_failure_answer_text,
    workstation_skill_invocation_error_answer,
    workstation_skill_invocation_payload,
    workstation_skill_invocation_status_answer,
    workstation_skill_store,
)
from workstation.runtime.core.workstation_core import workstation_workflow_query_view
from workstation.runtime.core.workstation_core import (
    workstation_operator_detail_view,
    workstation_operator_summary_list_view,
    workstation_workflow_summary_list_view,
)


_CAPABILITY_OPERATOR_AUTHORITIES: dict[str, tuple[str, ...]] = {
    "ws.repo.tree": ("read",),
    "ws.repo.search": ("read",),
    "ws.fs.read": ("read",),
    "ws.process.run": ("execute",),
    "ws.net.http": ("communicate",),
}


DEFAULT_WORKSTATION_CAPABILITIES = (
    "ws.fs.read",
    "ws.process.run",
    "ws.markdown.create",
    "ws.markdown.append",
    "ws.skill.catalog",
    "ws.skill.import",
    "ws.skill.export",
    "ws.skill.invoke",
    "ws.skill.compose",
)

AVAILABLE_WORKSTATION_CAPABILITIES = DEFAULT_WORKSTATION_CAPABILITIES + (
    "ws.repo.tree",
    "ws.repo.search",
    "ws.workflow.list",
    "ws.workflow.get",
    "ws.workflow.run",
    "ws.net.http",
    "ws.operator.list",
    "ws.operator.get",
)


def _skill_invoke_result_with_contract(result: Mapping[str, Any], *, invocation_request: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(result)
    merged["invocation_request"] = dict(invocation_request)
    merged["invocation_result"] = workstation_skill_invocation_result(merged)
    return merged

WORKSTATION_KERNEL_CAPABILITIES = (
    "ws.fs.read",
    "ws.process.run",
    "ws.markdown.create",
    "ws.markdown.append",
    "ws.skill.catalog",
    "ws.skill.import",
    "ws.skill.export",
    "ws.skill.invoke",
    "ws.skill.compose",
)

WORKSTATION_TRANSITIONAL_CAPABILITIES = (
    "ws.repo.tree",
    "ws.repo.search",
)


def _attachment_reference(
    session: WorkstationSession,
    name: str,
) -> tuple[WorkstationAttachment, str]:
    """
    High Level Purpose:
        In circumstances like workstation capability execution, helps with resolving an attachment reference even when the model supplies an attachment name, a mount path, or a host path nested under one attachment root.

    Reference to Theory:
        Supports the workstation attachment contract by keeping attachment addressing explicit while tolerating the concrete path shapes produced by natural-language tool planning.

    Example Input Output:
        Input: `_attachment_reference(session=3, name='/workstation/mounts/skill_input/trials')`
        Output: (WorkstationAttachment(name='skill_input', kind='workspace', source='/tmp/project', access_mode='read', mount_path='/workstation/mounts/skill_input'), 'trials')

    Args:
        session: Value for `session` used by `_attachment_reference`. Expected type: `WorkstationSession`.
        name: Value for `name` used by `_attachment_reference`. Expected type: `str`.

    Returns:
        tuple[WorkstationAttachment, str]: Result produced by `_attachment_reference`.
    """
    attachment, relative_path = resolve_host_interaction_attachment_reference(
        workstation_host_interaction_attachments(session),
        name,
    )
    return _attachment_by_canonical_name(session, attachment.name), relative_path


def _normalized_attachment_relative_path(
    session: WorkstationSession,
    *,
    raw_target: str,
    explicit_relative_path: str,
) -> tuple[WorkstationAttachment, str]:
    """
    High Level Purpose:
        In circumstances like workstation capability normalization, helps with separating one attachment reference from its in-attachment relative path even when the model conflates them into one string.

    Reference to Theory:
        Supports the workstation attachment boundary by canonicalizing model-produced paths back into attachment name plus bounded relative path.

    Example Input Output:
        Input: `_normalized_attachment_relative_path(session=3, raw_target='/workstation/mounts/skill_input/trials', explicit_relative_path='')`
        Output: (WorkstationAttachment(name='skill_input', ...), 'trials')

    Args:
        session: Value for `session` used by `_normalized_attachment_relative_path`. Expected type: `WorkstationSession`.
        raw_target: Value for `raw_target` used by `_normalized_attachment_relative_path`. Expected type: `str`.
        explicit_relative_path: Value for `explicit_relative_path` used by `_normalized_attachment_relative_path`. Expected type: `str`.

    Returns:
        tuple[WorkstationAttachment, str]: Result produced by `_normalized_attachment_relative_path`.
    """
    attachment, relative_path = normalize_host_interaction_attachment_relative_path(
        workstation_host_interaction_attachments(session),
        raw_target=raw_target,
        explicit_relative_path=explicit_relative_path,
    )
    return _attachment_by_canonical_name(session, attachment.name), relative_path


def _normalize_requested_delegation_targets(
    session: WorkstationSession,
    requested_delegation: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like workstation-to-skill invocation planning, helps with normalizing requested delegation targets onto canonical attachment names even when the model supplies mount paths or host paths.

    Reference to Theory:
        Supports the workstation delegation model by keeping requested rights attachment-scoped and comparable to the current session grant.

    Example Input Output:
        Input: `_normalize_requested_delegation_targets(session=3, requested_delegation=[{'capability': 'ws.fs.read', 'target': '/workstation/mounts/skill_input'}])`
        Output: [{'capability': 'ws.fs.read', 'target': 'skill_input', 'rationale': ''}]

    Args:
        session: Value for `session` used by `_normalize_requested_delegation_targets`. Expected type: `WorkstationSession`.
        requested_delegation: Value for `requested_delegation` used by `_normalize_requested_delegation_targets`. Expected type: `list[dict[str, Any]]`.

    Returns:
        list[dict[str, Any]]: Result produced by `_normalize_requested_delegation_targets`.
    """
    return normalize_host_interaction_delegation_targets(
        workstation_host_interaction_attachments(session),
        requested_delegation,
    )


def _single_workspace_attachment(session: WorkstationSession) -> WorkstationAttachment | None:
    """
    High Level Purpose:
        In circumstances like workstation-to-skill invocation planning, helps with resolving the single attached workspace when the workstation session only exposes one workspace target.

    Reference to Theory:
        Supports the workstation shell / worker model by letting the shell derive bounded defaults from the session boundary instead of requiring ambient path guesses.

    Example Input Output:
        Input: `_single_workspace_attachment(session=3)`
        Output: WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main')

    Args:
        session: Value for `session` used by `_single_workspace_attachment`. Expected type: `WorkstationSession`.

    Returns:
        WorkstationAttachment | None: Result produced by `_single_workspace_attachment`.
    """
    attachment = primary_workspace_attachment(workstation_host_interaction_attachments(session))
    if attachment is None:
        return None
    return _attachment_by_canonical_name(session, attachment.name)


def _normalize_workspace_scoped_invocation_payload(
    session: WorkstationSession,
    payload: Any,
) -> Any:
    """
    High Level Purpose:
        In circumstances like workstation invocation of imported trial workers, helps with projecting root-like relative prompt inputs onto the concrete primary workspace path expected by filesystem-oriented workers.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by letting the shell keep relative user phrasing attachment-scoped while still invoking concrete workers with bounded filesystem paths.

    Example Input Output:
        Input: `_normalize_workspace_scoped_invocation_payload(session=3, payload={'root': 'src'})`
        Output: {'root': '/tmp/project/src'}

    Args:
        session: Value for `session` used by `session`. Expected type: `WorkstationSession`.
        payload: Value for `payload` used by `payload`. Expected type: `Any`.

    Returns:
        Any: Result produced by `_normalize_workspace_scoped_invocation_payload`.
    """
    if not isinstance(payload, Mapping):
        return payload
    workspace_attachment = _single_workspace_attachment(session)
    if workspace_attachment is None:
        return dict(payload)
    updated_payload = dict(payload)
    for mount_key, path_keys in (
        ("mount", ("relative_path", "path")),
        ("source_mount", ("source_relative_path",)),
        ("destination_mount", ("destination_relative_path",)),
    ):
        mount_value = collapse_ws(str(updated_payload.get(mount_key, "")))
        if mount_value:
            try:
                attachment, _relative_path = _attachment_reference(session, mount_value)
                updated_payload[mount_key] = attachment.name
            except ValueError:
                pass
            continue
        if any(
            (
                path_text := collapse_ws(str(updated_payload.get(path_key, "")))
            )
            and not path_text.startswith("/")
            for path_key in path_keys
        ):
            updated_payload[mount_key] = workspace_attachment.name
    for key in ("root", "search_root", "directory", "dir"):
        raw_value = collapse_ws(str(updated_payload.get(key, "")))
        if not raw_value or raw_value.startswith("/") or raw_value.startswith("./"):
            continue
        updated_payload[key] = str(_safe_join(Path(workspace_attachment.source), raw_value))
    return updated_payload


def _heuristic_repo_search_pattern(semantic_unit: str) -> str:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation from natural-language prompts, helps with deriving one bounded repo-search pattern from a user semantic unit when the model omitted a structured payload.

    Reference to Theory:
        Supports BSSC boundary-shape reuse in the workstation by turning the semantic unit into an explicit worker input instead of failing on an omitted payload.

    Example Input Output:
        Input: `_heuristic_repo_search_pattern(semantic_unit='Find where workstation chat is implemented in this workspace.')`
        Output: 'workstation[-_\\s]+chat'

    Args:
        semantic_unit: Value for `semantic_unit` used by `_heuristic_repo_search_pattern`. Expected type: `str`.

    Returns:
        str: Result produced by `_heuristic_repo_search_pattern`.
    """
    normalized = collapse_ws(str(semantic_unit))
    if not normalized:
        return ""
    quoted_match = re.search(r"['\"]([^'\"]+)['\"]", normalized)
    if quoted_match:
        return collapse_ws(str(quoted_match.group(1)))
    patterns = (
        r"(?:find|locate)\s+where\s+(.+?)\s+is\s+implemented",
        r"search\s+for\s+(.+?)(?:\s+in\s+this\s+workspace|\s+within\s+this\s+workspace|$)",
        r"find\s+(.+?)(?:\s+in\s+this\s+workspace|\s+within\s+this\s+workspace|$)",
    )
    for pattern in patterns:
        matched = re.search(pattern, normalized, flags=re.IGNORECASE)
        if matched:
            candidate = collapse_ws(str(matched.group(1)))
            candidate = re.sub(r"^(the|a|an)\s+", "", candidate, flags=re.IGNORECASE)
            candidate = re.sub(
                r"\s+and\s+return\s+.+$",
                "",
                candidate,
                flags=re.IGNORECASE,
            )
            if candidate:
                words = [token for token in re.findall(r"[A-Za-z0-9_]+", candidate) if token]
                if len(words) >= 2:
                    return r"[-_\s]+".join(re.escape(token) for token in words)
                return candidate
    fallback = normalized
    prefixes = (
        "use the skill titled workstation repo search to ",
        "use workstation repo search to ",
    )
    lowered = fallback.casefold()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            fallback = fallback[len(prefix):]
            break
    fallback = re.sub(r"\s+in\s+this\s+workspace\.?$", "", fallback, flags=re.IGNORECASE)
    fallback = re.sub(r"\s+within\s+this\s+workspace\.?$", "", fallback, flags=re.IGNORECASE)
    fallback = re.sub(r"\s+in\s+the\s+workspace\.?$", "", fallback, flags=re.IGNORECASE)
    fallback = re.sub(r"\s+and\s+return\s+.+$", "", fallback, flags=re.IGNORECASE)
    fallback = collapse_ws(fallback)
    words = [token for token in re.findall(r"[A-Za-z0-9_]+", fallback) if token]
    if len(words) >= 2:
        return r"[-_\s]+".join(re.escape(token) for token in words)
    return fallback


def _derive_repo_search_invocation_inputs(
    session: WorkstationSession,
    arguments: dict[str, Any],
    requested_delegation: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """
    High Level Purpose:
        In circumstances like workstation-driven builtin repo-search invocation, helps with deriving a bounded invocation payload and minimum read delegation from the semantic unit when the model omitted explicit skill arguments.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by letting the shell bind a higher-level search worker to explicit attachment-scoped rights rather than falling back to ambient host access or hard failure.

    Example Input Output:
        Input: `_derive_repo_search_invocation_inputs(session=3, arguments={'semantic_unit': 'Find where workstation chat is implemented in this workspace.'}, requested_delegation=[])`
        Output: ({'mount': 'main', 'pattern': 'workstation chat', 'max_matches': 25}, [{'capability': 'ws.fs.read', 'target': 'main', 'rationale': 'Need to inspect repository files for workstation skill invocation.'}])

    Args:
        session: Value for `session` used by `_derive_repo_search_invocation_inputs`. Expected type: `WorkstationSession`.
        arguments: Value for `arguments` used by `_derive_repo_search_invocation_inputs`. Expected type: `dict[str, Any]`.
        requested_delegation: Value for `requested_delegation` used by `_derive_repo_search_invocation_inputs`. Expected type: `list[dict[str, Any]]`.

    Returns:
        tuple[dict[str, Any] | None, list[dict[str, Any]]]: Result produced by `_derive_repo_search_invocation_inputs`.
    """
    invocation_payload = arguments.get("invocation_payload")
    payload = dict(invocation_payload) if isinstance(invocation_payload, Mapping) else {}
    workspace_attachment = _single_workspace_attachment(session)
    preferred_target = ""
    for item in requested_delegation:
        capability = collapse_ws(str(item.get("capability", "")))
        target = collapse_ws(str(item.get("target", "")))
        if capability == "ws.fs.read" and target:
            preferred_target = target
            break
    mount_name = collapse_ws(str(payload.get("mount", ""))) or preferred_target
    if not mount_name and workspace_attachment is not None:
        mount_name = workspace_attachment.name
    pattern = collapse_ws(str(payload.get("pattern", "")))
    if not pattern:
        pattern = _heuristic_repo_search_pattern(str(arguments.get("semantic_unit", "")))
    if not mount_name or not pattern:
        return (payload or None), requested_delegation
    payload["mount"] = mount_name
    payload["pattern"] = pattern
    if "max_matches" not in payload:
        payload["max_matches"] = 25
    normalized_requested = list(requested_delegation)
    has_read_delegation = any(
        collapse_ws(str(item.get("capability", ""))) == "ws.fs.read"
        and collapse_ws(str(item.get("target", ""))) == mount_name
        for item in normalized_requested
    )
    if not has_read_delegation:
        normalized_requested.append(
            {
                "capability": "ws.fs.read",
                "target": mount_name,
                "rationale": "Need to inspect repository files for workstation skill invocation.",
            }
        )
    return payload, normalized_requested


def _derive_requested_delegation_from_invocation_payload(
    *,
    artifact: Any,
    invocation_payload: Any,
    requested_delegation: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like workstation invocation of mount-oriented file skills, helps with turning implied mount access in the final invocation payload into explicit delegated workstation rights.

    Reference to Theory:
        Supports the skill-first workstation policy by steering normal work through skills while keeping permission decisions explicit, receiptable, and escalation-aware instead of relying on ambient mount inheritance.

    Example Input Output:
        Input: `_derive_requested_delegation_from_invocation_payload(artifact=3, invocation_payload={'mount': 'main', 'relative_path': 'src/demo.py'}, requested_delegation=[])`
        Output: [{'capability': 'ws.fs.read', 'target': 'main', 'rationale': 'Need to expose the requested workstation mount to the invoked skill.'}]

    Args:
        artifact: Value for `artifact` used by `artifact`. Expected type: `Any`.
        invocation_payload: Value for `invocation_payload` used by `invocation_payload`. Expected type: `Any`.
        requested_delegation: Value for `requested_delegation` used by `requested_delegation`. Expected type: `list[dict[str, Any]]`.

    Returns:
        list[dict[str, Any]]: Result produced by `_derive_requested_delegation_from_invocation_payload`.
    """
    normalized_requested = normalized_requested_delegation(requested_delegation)
    if not isinstance(invocation_payload, Mapping):
        return normalized_requested
    declaration = runtime_skill_declaration_for_artifact(artifact)
    declared_authorities = {
        collapse_ws(str(item))
        for item in declaration.get("authorities_requested", [])
        if collapse_ws(str(item))
    }
    artifact_content = (
        dict(getattr(artifact, "content", {}) or {})
        if isinstance(getattr(artifact, "content", {}), Mapping)
        else {}
    )
    artifact_content = normalize_ability_runtime_content(
        artifact_content,
        title=collapse_ws(str(getattr(artifact, "title", ""))),
    )
    declared_authorities.update(
        collapse_ws(str(item))
        for item in artifact_content.get("governed_authorities", [])
        if collapse_ws(str(item))
    )
    if not declared_authorities:
        return normalized_requested

    payload_mapping = dict(invocation_payload)
    nested_payload = invocation_payload.get("payload")
    if isinstance(nested_payload, Mapping):
        for key, value in dict(nested_payload).items():
            payload_mapping.setdefault(collapse_ws(str(key)), value)

    seen_pairs = {
        (
            collapse_ws(str(item.get("capability", ""))),
            collapse_ws(str(item.get("target", ""))),
        )
        for item in normalized_requested
    }

    def _append_request(capability: str, target: str) -> None:
        normalized_capability = collapse_ws(str(capability))
        normalized_target = collapse_ws(str(target))
        pair = (normalized_capability, normalized_target)
        if not normalized_capability or not normalized_target or pair in seen_pairs:
            return
        normalized_requested.append(
            {
                "capability": normalized_capability,
                "target": normalized_target,
                "rationale": "Need to expose the requested workstation mount to the invoked skill.",
            }
        )
        seen_pairs.add(pair)

    mount_value = collapse_ws(str(payload_mapping.get("mount", "")))
    if mount_value:
        if "read" in declared_authorities:
            _append_request("ws.fs.read", mount_value)
        if "write" in declared_authorities:
            _append_request("ws.fs.write", mount_value)

    source_mount_value = collapse_ws(str(payload_mapping.get("source_mount", "")))
    if source_mount_value and (
        "read" in declared_authorities
        or "source_relative_path" in payload_mapping
    ):
        _append_request("ws.fs.read", source_mount_value)
    source_mutates = False
    artifact_title = collapse_ws(str(getattr(artifact, "title", ""))).casefold()
    if "move file" in artifact_title:
        source_mutates = True
    side_effects = [
        collapse_ws(str(item)).casefold()
        for item in declaration.get("side_effects", [])
        if collapse_ws(str(item))
    ]
    if any("fs.move_mount" in item or "fs.move_" in item for item in side_effects):
        source_mutates = True
    if source_mount_value and source_mutates and "write" in declared_authorities:
        _append_request("ws.fs.write", source_mount_value)

    destination_mount_value = collapse_ws(str(payload_mapping.get("destination_mount", "")))
    if destination_mount_value and "write" in declared_authorities:
        _append_request("ws.fs.write", destination_mount_value)

    return normalized_requested


def _nested_skill_host_requested_delegation(
    requested_delegation: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like workstation Blend execution of one skill operator, helps with preserving only host-interaction delegation entries that can be projected into the nested skill runtime.

    Reference to Theory:
        Supports the workstation / Blend boundary by separating operator applicability requirements from nested host-effect delegation instead of treating the outer `ws.skill.invoke` capability as a delegated inner right.

    Example Input Output:
        Input: `_nested_skill_host_requested_delegation([{'capability': 'ws.skill.invoke', 'target': 'Demo Skill'}, {'capability': 'ws.fs.read', 'target': 'main'}])`
        Output: [{'capability': 'ws.fs.read', 'target': 'main'}]

    Args:
        requested_delegation: Value for `requested_delegation` used by `requested_delegation`. Expected type: `list[dict[str, Any]] | tuple[dict[str, Any], ...] | None`.

    Returns:
        list[dict[str, Any]]: Result produced by `_nested_skill_host_requested_delegation`.
    """
    normalized = normalized_requested_delegation(requested_delegation or [])
    return [
        dict(item)
        for item in normalized
        if is_shared_host_interaction_action_capability(collapse_ws(str(item.get("capability", ""))))
    ]


def _align_delegated_mount_data_classes(
    *,
    declaration: Mapping[str, Any],
    delegated_mounts: Mapping[str, Any],
    granted_delegation: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """
    High Level Purpose:
        In circumstances like workstation invocation of governed file skills, helps with aligning delegated mount data classes to the skill's declared data boundary so the nested broker can authorize the requested mount operation.

    Reference to Theory:
        Supports the shell / worker permission model by keeping mount delegation explicit while ensuring the delegated data class is compatible with the invoked skill's declared touched-data set.

    Example Input Output:
        Input: `_align_delegated_mount_data_classes(declaration={'data_classes_touched': ['derived']}, delegated_mounts={'main': {'permissions': ['write'], 'data_class': 'public'}}, granted_delegation=[{'mount': 'main', 'permissions': ['write'], 'data_class': 'public'}])`
        Output: ({'main': {'permissions': ['write'], 'data_class': 'derived'}}, [{'mount': 'main', 'permissions': ['write'], 'data_class': 'derived'}])

    Args:
        declaration: Value for `declaration` used by `declaration`. Expected type: `Mapping[str, Any]`.
        delegated_mounts: Value for `delegated_mounts` used by `delegated_mounts`. Expected type: `Mapping[str, Any]`.
        granted_delegation: Value for `granted_delegation` used by `granted_delegation`. Expected type: `list[dict[str, Any]]`.

    Returns:
        tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]: Result produced by `_align_delegated_mount_data_classes`.
    """
    declared_data_classes = [
        collapse_ws(str(item))
        for item in declaration.get("data_classes_touched", [])
        if collapse_ws(str(item))
    ] if isinstance(declaration.get("data_classes_touched", []), list) else []
    if not declared_data_classes:
        return (
            {
                collapse_ws(str(name)): dict(spec)
                for name, spec in dict(delegated_mounts).items()
                if collapse_ws(str(name)) and isinstance(spec, Mapping)
            },
            [dict(item) for item in granted_delegation],
        )

    def _preferred_data_class(permissions: list[str], current_data_class: str) -> str:
        if current_data_class in declared_data_classes:
            return current_data_class
        if "write" in permissions and "derived" in declared_data_classes:
            return "derived"
        return declared_data_classes[0]

    aligned_mounts: dict[str, dict[str, Any]] = {}
    for raw_mount_name, raw_mount_spec in dict(delegated_mounts).items():
        mount_name = collapse_ws(str(raw_mount_name))
        if not mount_name or not isinstance(raw_mount_spec, Mapping):
            continue
        mount_spec = dict(raw_mount_spec)
        permissions = [
            collapse_ws(str(item))
            for item in mount_spec.get("permissions", [])
            if collapse_ws(str(item))
        ] if isinstance(mount_spec.get("permissions", []), list) else []
        mount_spec["data_class"] = _preferred_data_class(
            permissions,
            collapse_ws(str(mount_spec.get("data_class", ""))),
        )
        aligned_mounts[mount_name] = mount_spec

    aligned_grants: list[dict[str, Any]] = []
    for item in granted_delegation:
        aligned_item = dict(item)
        mount_name = collapse_ws(str(aligned_item.get("mount", aligned_item.get("target", ""))))
        permissions = [
            collapse_ws(str(current))
            for current in aligned_item.get("permissions", [])
            if collapse_ws(str(current))
        ] if isinstance(aligned_item.get("permissions", []), list) else []
        if mount_name and mount_name in aligned_mounts:
            aligned_item["data_class"] = collapse_ws(str(aligned_mounts[mount_name].get("data_class", "")))
        else:
            aligned_item["data_class"] = _preferred_data_class(
                permissions,
                collapse_ws(str(aligned_item.get("data_class", ""))),
            )
        aligned_grants.append(aligned_item)
    return aligned_mounts, aligned_grants


def list_workstation_tool_definitions(session: WorkstationSession) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like host-owned LLM prompting for workstation sessions, helps with exposing the currently allowed workstation capabilities as JSON-schema tool definitions.

    Reference to Theory:
        Supports the workstation capability contract by making actions explicit, typed, and attachment-aware rather than ambient.

    Example Input Output:
        Input: `list_workstation_tool_definitions(session=3)`
        Output: [{'type': 'function', 'function': {'name': 'ws.repo.tree', 'parameters': {'type': 'object'}}}]

    Args:
        session: Value for `session` used by `list_workstation_tool_definitions`. Expected type: `WorkstationSession`.

    Returns:
        list[dict[str, Any]]: Result produced by `list_workstation_tool_definitions`.
    """
    definitions: list[dict[str, Any]] = []
    for capability in session.allowed_capabilities:
        if capability == "ws.repo.tree":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "path": {"type": "string"},
                    "max_depth": {"type": "integer"},
                    "max_entries": {"type": "integer"},
                },
                "required": ["target"],
                "additionalProperties": False,
            }
            description = "Return a bounded directory tree for one attached workspace."
        elif capability == "ws.repo.search":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "pattern": {"type": "string"},
                    "relative_path": {"type": "string"},
                    "glob": {"type": "string"},
                    "max_matches": {"type": "integer"},
                },
                "required": ["target", "pattern"],
                "additionalProperties": False,
            }
            description = "Search an attached workspace with ripgrep and return bounded matches."
        elif capability == "ws.fs.read":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "path": {"type": "string"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["target", "path"],
                "additionalProperties": False,
            }
            description = "Read one file from an attached workspace or path attachment."
        elif capability == "ws.process.run":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "argv": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "cwd": {"type": "string"},
                    "timeout_seconds": {"type": "number"},
                    "max_output_chars": {"type": "integer"},
                },
                "required": ["target", "argv"],
                "additionalProperties": False,
            }
            description = "Run one bounded command in the attached workspace without a shell."
        elif capability == "ws.net.http":
            parameters = {
                "type": "object",
                "properties": {
                    "method": {"type": "string"},
                    "url": {"type": "string"},
                    "headers": {"type": "object"},
                    "body": {"type": "string"},
                    "json_body": {},
                    "timeout_seconds": {"type": "number"},
                    "max_response_chars": {"type": "integer"},
                },
                "required": ["url"],
                "additionalProperties": False,
            }
            description = "Issue one bounded explicit HTTP request through the workstation host network surface."
        elif capability == "ws.markdown.create":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "path": {"type": "string"},
                    "markdown_text": {"type": "string"},
                },
                "required": ["path", "markdown_text"],
                "additionalProperties": False,
            }
            description = "Save Learnings as New Markdown by creating one new .md or .markdown file in a writable workstation attachment."
        elif capability == "ws.markdown.append":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "path": {"type": "string"},
                    "markdown_text": {"type": "string"},
                },
                "required": ["path", "markdown_text"],
                "additionalProperties": False,
            }
            description = "Add Learnings to Markdown by appending markdown text to one existing .md or .markdown file in a writable workstation attachment."
        elif capability == "ws.skill.invoke":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "skill_title": {"type": "string"},
                    "semantic_unit": {"type": "string"},
                    "invocation_payload": {"type": "object"},
                    "requested_delegation": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "capability": {"type": "string"},
                                "target": {"type": "string"},
                                "rationale": {"type": "string"},
                            },
                            "required": ["capability"],
                            "additionalProperties": False,
                        },
                    },
                    "rationale": {"type": "string"},
                },
                "required": ["skill_title"],
                "additionalProperties": False,
            }
            description = "Invoke one installed governed skill from a workstation skill-store attachment."
        elif capability == "ws.skill.compose":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "workflow_plan": {"type": "object"},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step_id": {"type": "string"},
                                "skill_title": {"type": "string"},
                                "semantic_unit": {"type": "string"},
                                "branch_label": {"type": "string"},
                                "bindings": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "target_region": {"type": "string"},
                                            "target_path": {"type": "string"},
                                            "source_step_id": {"type": "string"},
                                            "source_region": {"type": "string"},
                                            "source_path": {"type": "string"},
                                            "source_root_name": {"type": "string"},
                                            "source_root_region": {"type": "string"},
                                            "constant_value": {},
                                            "mapper_kind": {"type": "string"},
                                            "mapper": {
                                                "type": "object",
                                                "properties": {
                                                    "kind": {"type": "string"},
                                                },
                                                "required": ["kind"],
                                                "additionalProperties": False,
                                            },
                                        },
                                        "required": ["target_region", "target_path"],
                                        "additionalProperties": False,
                                    },
                                },
                                "run_if": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "source_step_id": {"type": "string"},
                                            "source_region": {"type": "string"},
                                            "source_path": {"type": "string"},
                                            "operator": {"type": "string"},
                                            "expected_value": {},
                                        },
                                        "required": ["source_step_id", "source_region", "source_path"],
                                        "additionalProperties": False,
                                    },
                                },
                                "iterate_until": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "source_step_id": {"type": "string"},
                                            "source_region": {"type": "string"},
                                            "source_path": {"type": "string"},
                                            "operator": {"type": "string"},
                                            "expected_value": {},
                                        },
                                        "required": ["source_step_id", "source_region", "source_path"],
                                        "additionalProperties": False,
                                    },
                                },
                                "requested_delegation": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "capability": {"type": "string"},
                                            "target": {"type": "string"},
                                            "rationale": {"type": "string"},
                                        },
                                        "required": ["capability"],
                                        "additionalProperties": False,
                                    },
                                },
                                "rationale": {"type": "string"},
                            },
                            "required": ["step_id", "skill_title"],
                            "additionalProperties": False,
                        },
                    },
                    "root_inputs": {"type": "object"},
                    "root_references": {"type": "object"},
                    "final_output_step": {"type": "string"},
                    "approved_delegation": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "capability": {"type": "string"},
                                "target": {"type": "string"},
                            },
                            "required": ["capability"],
                            "additionalProperties": False,
                        },
                    },
                    "approved_delegation_scope": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            }
            description = "Execute an explicit multi-step governed skill composition plan with leaf bindings and mapper-backed payload wiring."
        elif capability == "ws.workflow.list":
            parameters = {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "status": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": [],
                "additionalProperties": False,
            }
            description = "List persisted Blend workflow plan or run summaries from the workstation workflow store."
        elif capability == "ws.workflow.get":
            parameters = {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "workflow_run_id": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            }
            description = "Load one persisted Blend workflow plan or workflow run by id."
        elif capability == "ws.operator.list":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "operator_kind": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": [],
                "additionalProperties": False,
            }
            description = "List dynamically inferred Blend operators visible in the current workstation context."
        elif capability == "ws.operator.get":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "operator_name": {"type": "string"},
                    "operator_kind": {"type": "string"},
                },
                "required": ["operator_name"],
                "additionalProperties": False,
            }
            description = "Inspect one dynamically inferred Blend operator visible in the current workstation context."
        elif capability == "ws.workflow.run":
            parameters = {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "workflow_plan": {"type": "object"},
                    "target": {"type": "string"},
                    "root_inputs": {"type": "object"},
                    "root_references": {"type": "object"},
                    "final_output_step": {"type": "string"},
                    "approved_delegation": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "capability": {"type": "string"},
                                "target": {"type": "string"},
                                "rationale": {"type": "string"},
                            },
                            "required": ["capability"],
                            "additionalProperties": False,
                        },
                    },
                    "approved_delegation_scope": {"type": "string"},
                },
                "required": [],
                "additionalProperties": False,
            }
            description = "Run one persisted or inline Blend workflow plan through the governed workstation workflow engine."
        elif capability == "ws.skill.catalog":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "additionalProperties": False,
            }
            description = "Return the current persistent workstation skill catalog and skill-home locations, optionally filtered by a short query."
        elif capability == "ws.skill.import":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "source_target": {"type": "string"},
                    "path": {"type": "string"},
                    "canonical_export_path": {"type": "string"},
                },
                "required": ["path"],
                "additionalProperties": False,
            }
            description = "Import one portable skill.yaml file into the persistent workstation skill home."
        elif capability == "ws.skill.export":
            parameters = {
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "skill_title": {"type": "string"},
                    "destination_target": {"type": "string"},
                    "destination_path": {"type": "string"},
                },
                "required": ["skill_title"],
                "additionalProperties": False,
            }
            description = "Export one governed workstation skill from the persistent workstation skill home."
        else:
            continue
        definitions.append(
            {
                "type": "function",
                "function": {
                    "name": capability,
                    "description": description,
                    "parameters": parameters,
                },
            }
        )
    return definitions


def execute_workstation_capability(
    session: WorkstationSession,
    capability: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like host-owned workstation tool mediation, helps with executing one allowed workstation capability against the attached resources.

    Reference to Theory:
        Supports the workstation capability contract by mediating operations through named capabilities and attachment targets rather than ambient host access.

    Example Input Output:
        Input: `execute_workstation_capability(session=3, capability='ws.repo.tree', arguments={'target': 'main'})`
        Output: {'status': 'ok', 'capability': 'ws.repo.tree', 'target': 'main', 'tree': ['README.md', 'src/']}

    Args:
        session: Value for `session` used by `execute_workstation_capability`. Expected type: `WorkstationSession`.
        capability: Value for `capability` used by `execute_workstation_capability`. Expected type: `str`.
        arguments: Value for `arguments` used by `execute_workstation_capability`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `execute_workstation_capability`.
    """
    if capability not in session.allowed_capabilities:
        raise ValueError(f"Capability {capability} is not allowed in this workstation session.")
    normalized_arguments = _normalize_workstation_capability_arguments(session, capability, arguments)
    if is_shared_host_interaction_action_capability(capability):
        attachment = None
        if capability != "ws.net.http":
            attachment = _attachment_by_name(session, str(normalized_arguments.get("target", "")).strip())
        return _execute_shared_host_interaction_action(
            session=session,
            capability=capability,
            attachment=attachment,
            arguments=normalized_arguments,
        )
    if capability == "ws.markdown.create":
        return _markdown_create(session, normalized_arguments)
    if capability == "ws.markdown.append":
        return _markdown_append(session, normalized_arguments)
    if capability == "ws.skill.invoke":
        return _skill_invoke(
            session,
            _skill_store_attachment(session, str(normalized_arguments.get("target", "")).strip()),
            normalized_arguments,
        )
    if capability == "ws.skill.compose":
        return _skill_compose(
            session,
            _skill_store_attachment(session, str(normalized_arguments.get("target", "")).strip()),
            normalized_arguments,
        )
    if capability == "ws.workflow.list":
        return _workflow_list(session, normalized_arguments)
    if capability == "ws.workflow.get":
        return _workflow_get(session, normalized_arguments)
    if capability == "ws.operator.list":
        return _operator_list(session, normalized_arguments)
    if capability == "ws.operator.get":
        return _operator_get(session, normalized_arguments)
    if capability == "ws.workflow.run":
        return _workflow_run(session, normalized_arguments)
    if capability == "ws.skill.catalog":
        return _skill_catalog(
            session,
            _skill_store_attachment(session, str(normalized_arguments.get("target", "")).strip()),
            normalized_arguments,
        )
    if capability == "ws.skill.import":
        return _skill_import(
            session,
            _skill_store_attachment(session, str(normalized_arguments.get("target", "")).strip()),
            normalized_arguments,
        )
    if capability == "ws.skill.export":
        return _skill_export(
            session,
            _skill_store_attachment(session, str(normalized_arguments.get("target", "")).strip()),
            normalized_arguments,
        )
    raise ValueError(f"Unsupported workstation capability: {capability}")


def _normalize_workstation_capability_arguments(
    session: WorkstationSession,
    capability: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation tool execution, helps with canonicalizing model-produced attachment references and in-attachment paths before the concrete capability implementation runs.

    Reference to Theory:
        Supports the workstation attachment and delegation contracts by mapping natural-language tool arguments back onto explicit attachment names and bounded relative paths.

    Example Input Output:
        Input: `_normalize_workstation_capability_arguments(session=3, capability='ws.repo.tree', arguments={'target': '/workstation/mounts/skill_input/trials'})`
        Output: {'target': 'skill_input', 'path': 'trials'}

    Args:
        session: Value for `session` used by `_normalize_workstation_capability_arguments`. Expected type: `WorkstationSession`.
        capability: Value for `capability` used by `_normalize_workstation_capability_arguments`. Expected type: `str`.
        arguments: Value for `arguments` used by `_normalize_workstation_capability_arguments`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_normalize_workstation_capability_arguments`.
    """
    normalized = dict(arguments)
    if capability == "ws.repo.tree":
        attachment, relative_path = _normalized_attachment_relative_path(
            session,
            raw_target=str(arguments.get("target", "")),
            explicit_relative_path=str(arguments.get("path", "")),
        )
        normalized["target"] = attachment.name
        if relative_path:
            normalized["path"] = relative_path
        else:
            normalized.pop("path", None)
    elif capability == "ws.repo.search":
        attachment, relative_path = _normalized_attachment_relative_path(
            session,
            raw_target=str(arguments.get("target", "")),
            explicit_relative_path=str(arguments.get("relative_path", "")),
        )
        normalized["target"] = attachment.name
        if relative_path:
            normalized["relative_path"] = relative_path
        else:
            normalized.pop("relative_path", None)
    elif capability == "ws.fs.read":
        attachment, relative_path = _normalized_attachment_relative_path(
            session,
            raw_target=str(arguments.get("target", "")),
            explicit_relative_path=str(arguments.get("path", "")),
        )
        normalized["target"] = attachment.name
        if relative_path:
            normalized["path"] = relative_path
    elif capability == "ws.process.run":
        attachment, relative_path = _normalized_attachment_relative_path(
            session,
            raw_target=str(arguments.get("target", "")),
            explicit_relative_path=str(arguments.get("cwd", ".")),
        )
        normalized["target"] = attachment.name
        normalized["cwd"] = relative_path or "."
    elif capability == "ws.net.http":
        normalized["method"] = collapse_ws(str(arguments.get("method", "GET"))).upper() or "GET"
        if isinstance(arguments.get("headers", {}), Mapping):
            normalized["headers"] = {
                collapse_ws(str(key)): str(value)
                for key, value in dict(arguments.get("headers", {})).items()
                if collapse_ws(str(key))
            }
        else:
            normalized.pop("headers", None)
    elif capability in {"ws.markdown.create", "ws.markdown.append"}:
        attachment, relative_path = _normalized_markdown_attachment_relative_path(
            session,
            raw_target=str(arguments.get("target", "")),
            explicit_relative_path=str(arguments.get("path", "")),
        )
        normalized["target"] = attachment.name
        normalized["path"] = relative_path
        normalized["markdown_text"] = str(arguments.get("markdown_text", "") or "")
    elif capability == "ws.skill.import":
        attachment, relative_path = _normalized_attachment_relative_path(
            session,
            raw_target=str(arguments.get("source_target", arguments.get("target", ""))),
            explicit_relative_path=str(arguments.get("path", "")),
        )
        normalized["source_target"] = attachment.name
        if relative_path:
            normalized["path"] = relative_path
    elif capability == "ws.skill.invoke":
        normalized["requested_delegation"] = _normalize_requested_delegation_targets(
            session,
            normalized_requested_delegation(arguments.get("requested_delegation")),
        )
        normalized["approved_delegation"] = _normalize_requested_delegation_targets(
            session,
            normalized_requested_delegation(arguments.get("approved_delegation")),
        )
        payload = normalized.get("invocation_payload")
        if isinstance(payload, Mapping):
            updated_payload = dict(payload)
            mount_value = collapse_ws(str(updated_payload.get("mount", "")))
            if mount_value:
                try:
                    attachment, _relative_path = _attachment_reference(session, mount_value)
                    updated_payload["mount"] = attachment.name
                except ValueError:
                    pass
            normalized["invocation_payload"] = updated_payload
        for mount_key in ("mount", "source_mount", "destination_mount"):
            mount_value = collapse_ws(str(normalized.get(mount_key, "")))
            if not mount_value:
                continue
            try:
                attachment, _relative_path = _attachment_reference(session, mount_value)
                normalized[mount_key] = attachment.name
            except ValueError:
                pass
    elif capability == "ws.skill.compose":
        normalized["target"] = collapse_ws(str(arguments.get("target", ""))) or "skills"
        normalized["approved_delegation"] = _normalize_requested_delegation_targets(
            session,
            normalized_requested_delegation(arguments.get("approved_delegation")),
        )
        workflow_plan = arguments.get("workflow_plan")
        if isinstance(workflow_plan, Mapping):
            normalized["workflow_plan"] = dict(workflow_plan)
            try:
                compose_arguments = skill_compose_arguments_from_blend_workflow_plan(
                    blend_workflow_plan_from_skill_compose_arguments({"workflow_plan": dict(workflow_plan)})
                )
                normalized["target"] = collapse_ws(str(compose_arguments.get("target", ""))) or normalized["target"]
                normalized["steps"] = list(compose_arguments.get("steps", []))
                if "root_inputs" in compose_arguments:
                    normalized["root_inputs"] = dict(compose_arguments.get("root_inputs", {}))
                if "root_references" in compose_arguments:
                    normalized["root_references"] = dict(compose_arguments.get("root_references", {}))
                if "final_output_step" in compose_arguments:
                    normalized["final_output_step"] = compose_arguments.get("final_output_step", "")
            except Exception:
                pass
        raw_steps = arguments.get("steps", [])
        if "steps" not in normalized and isinstance(raw_steps, list):
            normalized_steps: list[dict[str, Any]] = []
            for item in raw_steps:
                if not isinstance(item, Mapping):
                    continue
                step_payload = dict(item)
                step_payload["requested_delegation"] = _normalize_requested_delegation_targets(
                    session,
                    normalized_requested_delegation(step_payload.get("requested_delegation")),
                )
                normalized_steps.append(step_payload)
            normalized["steps"] = normalized_steps
    elif capability == "ws.workflow.run":
        normalized["target"] = collapse_ws(str(arguments.get("target", ""))) or "skills"
        normalized["approved_delegation"] = _normalize_requested_delegation_targets(
            session,
            normalized_requested_delegation(arguments.get("approved_delegation")),
        )
        workflow_plan = arguments.get("workflow_plan")
        if isinstance(workflow_plan, Mapping):
            normalized["workflow_plan"] = dict(workflow_plan)
            target_from_plan = collapse_ws(str(dict(workflow_plan).get("metadata", {}).get("target", "")))
            if target_from_plan:
                normalized["target"] = target_from_plan
        workflow_id = collapse_ws(str(arguments.get("workflow_id", "")))
        if workflow_id:
            normalized["workflow_id"] = workflow_id
        if "root_inputs" in arguments and isinstance(arguments.get("root_inputs"), Mapping):
            normalized["root_inputs"] = dict(arguments.get("root_inputs", {}))
        if "root_references" in arguments and isinstance(arguments.get("root_references"), Mapping):
            normalized["root_references"] = dict(arguments.get("root_references", {}))
        final_output_step = collapse_ws(str(arguments.get("final_output_step", "")))
        if final_output_step:
            normalized["final_output_step"] = final_output_step
    elif capability in {"ws.operator.list", "ws.operator.get"}:
        target_text = collapse_ws(str(arguments.get("target", "")))
        if target_text:
            normalized["target"] = target_text
        operator_kind = collapse_ws(str(arguments.get("operator_kind", "")))
        if operator_kind:
            normalized["operator_kind"] = operator_kind
        operator_name = collapse_ws(str(arguments.get("operator_name", "")))
        if operator_name:
            normalized["operator_name"] = operator_name
        query = collapse_ws(str(arguments.get("query", "")))
        if query:
            normalized["query"] = query
    elif capability == "ws.skill.export":
        normalized["target"] = "skills"
        destination_path_text = collapse_ws(str(arguments.get("destination_path", "")))
        destination_target_text = collapse_ws(str(arguments.get("destination_target", "")))
        if destination_path_text:
            try:
                attachment, relative_path = _normalized_attachment_relative_path(
                    session,
                    raw_target=destination_target_text,
                    explicit_relative_path=destination_path_text,
                )
            except ValueError:
                workspace_attachment = _single_workspace_attachment(session)
                if workspace_attachment is not None and not destination_path_text.startswith("/"):
                    normalized["destination_target"] = workspace_attachment.name
                    normalized["destination_path"] = destination_path_text
                else:
                    normalized["destination_target"] = destination_target_text or "skills_exports"
            else:
                normalized["destination_target"] = attachment.name
                normalized["destination_path"] = relative_path or destination_path_text
        else:
            if destination_target_text:
                try:
                    attachment, _relative_path = _normalized_attachment_relative_path(
                        session,
                        raw_target=destination_target_text,
                        explicit_relative_path="",
                    )
                    normalized["destination_target"] = attachment.name
                except ValueError:
                    normalized["destination_target"] = destination_target_text
            else:
                normalized["destination_target"] = "skills_exports"
    return normalized


def _attachment_by_name(session: WorkstationSession, name: str) -> WorkstationAttachment:
    """
    High Level Purpose:
        In circumstances like workstation capability execution, helps with resolving one named attachment from the current session.

    Reference to Theory:
        Supports the workstation attachment contract by keeping capability execution scoped to declared attachments.

    Example Input Output:
        Input: `_attachment_by_name(session=3, name='main')`
        Output: WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main')

    Args:
        session: Value for `session` used by `_attachment_by_name`. Expected type: `WorkstationSession`.
        name: Value for `name` used by `_attachment_by_name`. Expected type: `str`.

    Returns:
        WorkstationAttachment: Result produced by `_attachment_by_name`.
    """
    attachment, _relative_path = _attachment_reference(session, name)
    return attachment


def _attachment_by_canonical_name(session: WorkstationSession, name: str) -> WorkstationAttachment:
    """
    High Level Purpose:
        In circumstances like mapping shared host-interaction attachments back onto workstation session attachments, helps with recovering the canonical workstation attachment object by name.

    Reference to Theory:
        Supports the shared host-interaction substrate by letting workstation-local code reuse shared attachment-resolution helpers while still returning workstation-native attachment objects.

    Example Input Output:
        Input: `_attachment_by_canonical_name(session=3, name='main')`
        Output: WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main')

    Args:
        session: Value for `session` used by `_attachment_by_canonical_name`. Expected type: `WorkstationSession`.
        name: Value for `name` used by `_attachment_by_canonical_name`. Expected type: `str`.

    Returns:
        WorkstationAttachment: Result produced by `_attachment_by_canonical_name`.
    """
    for attachment in session.attachments:
        if attachment.name == name:
            return attachment
    raise ValueError(f"Unknown canonical workstation attachment: {name}")


def _default_markdown_attachment(session: WorkstationSession) -> WorkstationAttachment:
    workspace_attachment = _single_workspace_attachment(session)
    if workspace_attachment is not None:
        return workspace_attachment
    for attachment in session.attachments:
        if attachment.kind in {"output", "scratch", "session_root"}:
            return attachment
    raise ValueError("A writable workstation attachment is required for markdown learning writes.")


def _skill_store_attachment(session: WorkstationSession, name: str) -> WorkstationAttachment:
    """
    High Level Purpose:
        In circumstances like workstation-to-skill invocation, helps with resolving the bound skill-store attachment that should be used for one invocation.

    Reference to Theory:
        Supports the workstation attachment model by keeping installed-skill access scoped to an explicit skill-store attachment rather than ambient global state.

    Example Input Output:
        Input: `_skill_store_attachment(session=3, name='skills')`
        Output: WorkstationAttachment(name='skills', kind='skill_store', source='/tmp/skills.sqlite3', access_mode='read', mount_path='/workstation/skills/store.sqlite3')

    Args:
        session: Value for `session` used by `_skill_store_attachment`. Expected type: `WorkstationSession`.
        name: Value for `name` used by `_skill_store_attachment`. Expected type: `str`.

    Returns:
        WorkstationAttachment: Result produced by `_skill_store_attachment`.
    """
    normalized_name = str(name or "").strip()
    skill_store_attachments = tuple(
        attachment for attachment in session.attachments if attachment.kind == "skill_store"
    )
    if normalized_name:
        try:
            attachment = _attachment_by_name(session, normalized_name)
        except ValueError:
            if len(skill_store_attachments) == 1:
                return skill_store_attachments[0]
            raise
        if attachment.kind != "skill_store":
            if len(skill_store_attachments) == 1:
                return skill_store_attachments[0]
            raise ValueError(f"Attachment {normalized_name!r} is not a skill-store attachment.")
        return attachment
    if len(skill_store_attachments) == 1:
        return skill_store_attachments[0]
    raise ValueError("A skill-store attachment target is required when the workstation has zero or multiple skill stores.")


def _safe_join(base: Path, relative_path: str) -> Path:
    """
    High Level Purpose:
        In circumstances like workstation file mediation, helps with resolving a user-supplied relative path without allowing escape from the attachment root.

    Reference to Theory:
        Supports governed attachment access by ensuring file operations remain inside the declared attachment boundary.

    Example Input Output:
        Input: `_safe_join(base=Path('/tmp/project'), relative_path='src/app.py')`
        Output: Path('/tmp/project/src/app.py')

    Args:
        base: Value for `base` used by `_safe_join`. Expected type: `Path`.
        relative_path: Value for `relative_path` used by `_safe_join`. Expected type: `str`.

    Returns:
        Path: Result produced by `_safe_join`.
    """
    return safe_join_within_attachment_root(base, relative_path)


def _normalized_markdown_attachment_relative_path(
    session: WorkstationSession,
    *,
    raw_target: str,
    explicit_relative_path: str,
) -> tuple[WorkstationAttachment, str]:
    normalized_path = collapse_ws(str(explicit_relative_path))
    normalized_target = collapse_ws(str(raw_target))
    if not normalized_path and normalized_target:
        attachment, extracted_relative_path = _normalized_attachment_relative_path(
            session,
            raw_target=normalized_target,
            explicit_relative_path="",
        )
        normalized_path = collapse_ws(str(extracted_relative_path))
        normalized_target = attachment.name
    if not normalized_path:
        raise ValueError("Markdown write requires a non-empty path.")
    attachment = (
        _normalized_attachment_relative_path(
            session,
            raw_target=normalized_target,
            explicit_relative_path=normalized_path,
        )[0]
        if normalized_target
        else _default_markdown_attachment(session)
    )
    return attachment, normalized_path


def _markdown_write_target_path(
    session: WorkstationSession,
    arguments: dict[str, Any],
    *,
    capability_name: str,
) -> tuple[WorkstationAttachment, Path, str]:
    target_name = collapse_ws(str(arguments.get("target", ""))) or _default_markdown_attachment(session).name
    attachment = _attachment_by_name(session, target_name)
    if attachment.access_mode not in {"write", "read_write"}:
        raise ValueError(f"Attachment {attachment.name!r} is not writable for {capability_name}.")
    if attachment.kind not in {"workspace", "output", "scratch", "session_root"}:
        raise ValueError(f"Attachment {attachment.name!r} cannot be used for markdown learning writes.")
    relative_path = collapse_ws(str(arguments.get("path", "")))
    if not relative_path:
        raise ValueError(f"{capability_name} requires a non-empty path.")
    suffix = Path(relative_path).suffix.casefold()
    if suffix not in {".md", ".markdown"}:
        raise ValueError(f"{capability_name} only supports .md or .markdown destinations.")
    resolved_path = _safe_join(Path(attachment.source), relative_path)
    return attachment, resolved_path, relative_path


def _normalized_markdown_body(text: str, *, append_mode: bool) -> str:
    body = str(text or "").replace("\r\n", "\n")
    if not body.strip():
        raise ValueError("Markdown write requires non-empty markdown_text.")
    if append_mode:
        return body
    return body if body.endswith("\n") else f"{body}\n"


def _capability_ir_leaf(
    *,
    region_name: str,
    path: str,
    data_type: str,
    semantic_label: str,
) -> dict[str, Any]:
    boundary_term = f"{region_name}*"
    return {
        "region": boundary_term,
        "path": path,
        "carrier_kind": "value",
        "data_type": data_type,
        "semantic_label": semantic_label,
        "leaf_class": "scalar" if data_type not in {"Strings", "Bytess", "Ints", "Bools", "Floats"} else "collection",
    }


def _workstation_capability_canonical_ir(capability: str) -> dict[str, Any]:
    normalized_capability = collapse_ws(capability)
    if normalized_capability == "ws.fs.read":
        input_leaves = [_capability_ir_leaf(region_name="a", path="/a/path", data_type="String", semantic_label="path")]
        output_leaves = [
            _capability_ir_leaf(region_name="d", path="/d/content", data_type="String", semantic_label="text"),
            _capability_ir_leaf(region_name="d", path="/d/path", data_type="String", semantic_label="path"),
            _capability_ir_leaf(region_name="d", path="/d/truncated", data_type="Boolean", semantic_label="truncated"),
        ]
    elif normalized_capability == "ws.repo.tree":
        input_leaves = []
        output_leaves = [
            _capability_ir_leaf(region_name="d", path="/d/tree", data_type="Strings", semantic_label="tree"),
        ]
    elif normalized_capability == "ws.repo.search":
        input_leaves = [_capability_ir_leaf(region_name="a", path="/a/pattern", data_type="String", semantic_label="pattern")]
        output_leaves = [
            _capability_ir_leaf(region_name="d", path="/d/matches", data_type="Strings", semantic_label="matches"),
            _capability_ir_leaf(region_name="d", path="/d/returncode", data_type="Int", semantic_label="returncode"),
        ]
    elif normalized_capability == "ws.process.run":
        input_leaves = [_capability_ir_leaf(region_name="a", path="/a/argv", data_type="Strings", semantic_label="argv")]
        output_leaves = [
            _capability_ir_leaf(region_name="d", path="/d/stdout", data_type="String", semantic_label="stdout"),
            _capability_ir_leaf(region_name="d", path="/d/stderr", data_type="String", semantic_label="stderr"),
            _capability_ir_leaf(region_name="d", path="/d/returncode", data_type="Int", semantic_label="returncode"),
        ]
    elif normalized_capability == "ws.net.http":
        input_leaves = [_capability_ir_leaf(region_name="a", path="/a/url", data_type="String", semantic_label="url")]
        output_leaves = [
            _capability_ir_leaf(region_name="d", path="/d/text", data_type="String", semantic_label="text"),
            _capability_ir_leaf(region_name="d", path="/d/http_status", data_type="Int", semantic_label="http status"),
        ]
    else:
        raise ValueError(f"Unsupported workstation capability operator {capability!r}.")
    input_contract = {
        collapse_ws(str(item["semantic_label"])).replace(" ", "_") or Path(str(item["path"])).name: "required input value"
        for item in input_leaves
    }
    output_contract = {
        collapse_ws(str(item["semantic_label"])).replace(" ", "_") or Path(str(item["path"])).name: "execution result"
        for item in output_leaves
    }
    return {
        "artifact_id": f"workstation-capability-{normalized_capability}",
        "kind": "ability",
        "title": normalized_capability,
        "schema": "bssc_skill.v2",
        "declaration": {
            "intent": normalized_capability,
            "authorities_requested": list(_CAPABILITY_OPERATOR_AUTHORITIES.get(normalized_capability, ())),
        },
        "input_contract": input_contract,
        "output_contract": output_contract,
        "normalization": {
            "regions": {
                **(
                    {
                        "a": {
                            "boundary_term": "a*",
                            "leaves": input_leaves,
                        }
                    }
                    if input_leaves
                    else {}
                ),
                "d": {
                    "boundary_term": "d*",
                    "leaves": output_leaves,
                },
            }
        },
    }


def _default_workstation_capability_attachment(
    session: WorkstationSession,
    *,
    capability: str,
    requested_target: str = "",
) -> WorkstationAttachment | None:
    normalized_capability = collapse_ws(capability)
    if normalized_capability == "ws.net.http":
        return None
    normalized_target = collapse_ws(requested_target)
    if normalized_target:
        return _attachment_by_name(session, normalized_target)
    workspace_attachment = _single_workspace_attachment(session)
    if workspace_attachment is not None:
        return workspace_attachment
    for attachment in session.attachments:
        if attachment.kind in {"secret_ref", "skill_store"}:
            continue
        return attachment
    return None


def _optional_skill_store_attachment(session: WorkstationSession, target: str) -> WorkstationAttachment | None:
    try:
        return _skill_store_attachment(session, target)
    except ValueError:
        return None


def _workstation_operator_providers(
    *,
    session: WorkstationSession,
    skill_attachment: WorkstationAttachment | None,
) -> tuple[BlendOperatorProvider, ...]:
    providers: list[BlendOperatorProvider] = []
    if skill_attachment is not None:
        providers.append(
            new_blend_skill_operator_provider(
                provider_id="workstation_skill_store",
                list_skill_names=lambda _context: [
                    title
                    for entry in list_available_workstation_skills(Path(skill_attachment.source))
                    if (title := collapse_ws(str(entry.get("title", ""))))
                ],
                resolve_skill=lambda operator_name, _context: resolve_workstation_skill(
                    skill_title=operator_name,
                    skill_store_path=Path(skill_attachment.source),
                ),
                visible_targets=(skill_attachment.name,),
                execution_adapter="workstation.skill_invoke",
                metadata={
                    "source_kind": "workstation_skill_store",
                    "skill_attachment": skill_attachment.name,
                },
            )
        )
    providers.append(
        new_blend_capability_operator_provider(
            provider_id="workstation_capabilities",
            list_capability_names=lambda _context: [
                capability
                for capability in session.allowed_capabilities
                if is_shared_host_interaction_action_capability(capability)
            ],
            resolve_capability_record=lambda operator_name, _context: _resolve_workstation_capability_operator_record(
                session=session,
                operator_name=operator_name,
            ),
            resolve_workflow_step_record=lambda workflow_step, _context: _resolve_workstation_capability_operator_record(
                session=session,
                operator_name=collapse_ws(str(getattr(workflow_step, "operator_name", ""))),
                requested_target=collapse_ws(str(getattr(workflow_step, "metadata", {}).get("target", ""))),
            ),
            metadata={"source_kind": "workstation_capability_provider"},
        )
    )
    return tuple(providers)


def _as_host_interaction_attachment(attachment: WorkstationAttachment) -> HostInteractionAttachment:
    """
    High Level Purpose:
        In circumstances like workstation reuse of shared host-action helpers, helps with projecting one workstation attachment into the shared host-interaction attachment shape.

    Reference to Theory:
        Supports the shared host-interaction substrate by letting workstation capability execution call shared action helpers without keeping a duplicate attachment model for those helpers.

    Example Input Output:
        Input: `_as_host_interaction_attachment(attachment=WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'))`
        Output: HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main')

    Args:
        attachment: Value for `attachment` used by `_as_host_interaction_attachment`. Expected type: `WorkstationAttachment`.

    Returns:
        HostInteractionAttachment: Result produced by `_as_host_interaction_attachment`.
    """
    return HostInteractionAttachment(
        name=attachment.name,
        kind=attachment.kind,
        source=attachment.source,
        access_mode=attachment.access_mode,
        mount_path=attachment.mount_path,
        metadata=dict(attachment.metadata),
    )


def _repo_tree(attachment: WorkstationAttachment, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation repo discovery, helps with returning a bounded directory tree for one attached workspace.

    Reference to Theory:
        Supports the workstation discovery and capability model by exposing explicit workspace inspection rather than ambient filesystem browsing.

    Example Input Output:
        Input: `_repo_tree(attachment=WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), arguments={'target': 'main'})`
        Output: {'status': 'ok', 'capability': 'ws.repo.tree', 'target': 'main', 'tree': ['README.md', 'src/']}

    Args:
        attachment: Value for `attachment` used by `_repo_tree`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_repo_tree`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_repo_tree`.
    """
    return execute_shared_host_interaction_action(
        capability="ws.repo.tree",
        attachment=_as_host_interaction_attachment(attachment),
        arguments=dict(arguments),
    )


def _repo_search(attachment: WorkstationAttachment, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation-assisted repository inspection, helps with running a bounded ripgrep search against one attached workspace.

    Reference to Theory:
        Supports the workstation capability model by exposing explicit search over a named attachment rather than ambient shell search.

    Example Input Output:
        Input: `_repo_search(attachment=WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), arguments={'target': 'main', 'pattern': 'main\\('})`
        Output: {'status': 'ok', 'capability': 'ws.repo.search', 'target': 'main', 'matches': ['src/app.py:12:def main():']}

    Args:
        attachment: Value for `attachment` used by `_repo_search`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_repo_search`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_repo_search`.
    """
    return execute_shared_host_interaction_action(
        capability="ws.repo.search",
        attachment=_as_host_interaction_attachment(attachment),
        arguments=dict(arguments),
    )


def _fs_read(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation-guided file inspection, helps with reading one file from a named attachment in a bounded way.

    Reference to Theory:
        Supports explicit read-reference handling in the workstation by constraining file reads to declared attachment boundaries.

    Example Input Output:
        Input: `_fs_read(session=3, attachment=WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), arguments={'target': 'main', 'path': 'README.md'})`
        Output: {'status': 'ok', 'capability': 'ws.fs.read', 'target': 'main', 'path': 'README.md', 'content': '# Project'}

    Args:
        session: Value for `session` used by `_fs_read`. Expected type: `WorkstationSession`.
        attachment: Value for `attachment` used by `_fs_read`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_fs_read`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_fs_read`.
    """
    requested_path = str(arguments["path"])
    resolved = _resolve_workstation_read_path(session, attachment, requested_path)
    return execute_shared_host_interaction_action(
        capability="ws.fs.read",
        attachment=_as_host_interaction_attachment(attachment),
        arguments=dict(arguments),
        resolve_read_path=lambda _requested_path: resolved,
    )


def _resolve_workstation_read_path(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    requested_path: str,
) -> Path:
    """
    High Level Purpose:
        In circumstances like workstation discovery-file access, helps with resolving one requested file path while allowing workstation session discovery files to remain readable even when a model points them at the workspace attachment.

    Reference to Theory:
        Supports the workstation discovery surface by keeping session-root files addressable as explicit workstation data rather than hidden ambient state.

    Example Input Output:
        Input: `_resolve_workstation_read_path(session=3, attachment=WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), requested_path='SKILLS.json')`
        Output: Path('/tmp/ws/SKILLS.json')

    Args:
        session: Value for `session` used by `_resolve_workstation_read_path`. Expected type: `WorkstationSession`.
        attachment: Value for `attachment` used by `_resolve_workstation_read_path`. Expected type: `WorkstationAttachment`.
        requested_path: Value for `requested_path` used by `_resolve_workstation_read_path`. Expected type: `str`.

    Returns:
        Path: Result produced by `_resolve_workstation_read_path`.
    """
    requested_text = str(requested_path)
    attachment_root = Path(attachment.source)
    candidate = _safe_join(attachment_root, requested_text)
    if candidate.exists():
        return candidate
    discovery_names = {
        "README.md",
        "WORKSTATION.toml",
        "ATTACHMENTS.json",
        "TOOLS.json",
        "TASK.md",
        "TASK_CONTRACT.json",
        "SESSION.json",
        "SKILLS.json",
        "LAST_RESPONSE.json",
        "MESSAGES.jsonl",
    }
    if attachment.kind == "workspace" and Path(requested_text).name in discovery_names:
        session_attachment = next(
            (item for item in session.attachments if item.kind == "session_root"),
            None,
        )
        if session_attachment is not None:
            session_candidate = _safe_join(Path(session_attachment.source), requested_text)
            if session_candidate.exists():
                return session_candidate
    return candidate


def _process_run(attachment: WorkstationAttachment, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation-guided repository testing or bounded command execution, helps with running one command without an ambient shell inside a named attachment root.

    Reference to Theory:
        Supports the workstation capability model by keeping process execution explicit, attachment-scoped, and receipt-producing.

    Example Input Output:
        Input: `_process_run(attachment=WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), arguments={'target': 'main', 'argv': ['python3', '--version']})`
        Output: {'status': 'ok', 'capability': 'ws.process.run', 'target': 'main', 'returncode': 0, 'stdout': 'Python 3.11.0', 'stderr': ''}

    Args:
        attachment: Value for `attachment` used by `_process_run`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_process_run`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_process_run`.
    """
    return execute_shared_host_interaction_action(
        capability="ws.process.run",
        attachment=_as_host_interaction_attachment(attachment),
        arguments=dict(arguments),
    )


def _execute_shared_host_interaction_action(
    *,
    session: WorkstationSession,
    capability: str,
    attachment: WorkstationAttachment | None,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation reuse of the shared non-skill host-action substrate, helps with adapting workstation attachment and read-resolution policy onto the shared host-action dispatcher.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by keeping concrete non-skill host-action dispatch below workstation shell code while preserving workstation-specific discovery-file resolution where needed.

    Example Input Output:
        Input: `_execute_shared_host_interaction_action(session=3, capability='ws.fs.read', attachment=WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), arguments={'target': 'main', 'path': 'README.md'})`
        Output: {'status': 'ok', 'capability': 'ws.fs.read', 'target': 'main', 'path': 'README.md', 'content': '# Project'}

    Args:
        session: Value for `session` used by `_execute_shared_host_interaction_action`. Expected type: `WorkstationSession`.
        capability: Value for `capability` used by `_execute_shared_host_interaction_action`. Expected type: `str`.
        attachment: Value for `attachment` used by `_execute_shared_host_interaction_action`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_execute_shared_host_interaction_action`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_execute_shared_host_interaction_action`.
    """
    resolver = None
    if capability == "ws.fs.read" and attachment is not None:
        resolver = lambda requested_path: _resolve_workstation_read_path(session, attachment, requested_path)
    return execute_shared_host_interaction_action(
        capability=capability,
        attachment=_as_host_interaction_attachment(attachment) if attachment is not None else None,
        arguments=dict(arguments),
        resolve_read_path=resolver,
    )


def _skill_catalog(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill discovery, helps with returning the current persistent worker catalog together with the bound workstation skill-home locations.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by making the durable worker inventory explicit instead of hidden behind the underlying store path.

    Example Input Output:
        Input: `_skill_catalog(session=3, attachment=WorkstationAttachment(name='skills', kind='skill_store', source='/tmp/skills.sqlite3', access_mode='read_write', mount_path='/workstation/skills/store.sqlite3'), arguments={'query': 'python'})`
        Output: {'status': 'ok', 'capability': 'ws.skill.catalog', 'skills': [{'title': 'Workstation Greeting'}]}

    Args:
        session: Value for `session` used by `_skill_catalog`. Expected type: `WorkstationSession`.
        attachment: Value for `attachment` used by `_skill_catalog`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_skill_catalog`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_skill_catalog`.
    """
    payload = workstation_skill_catalog_payload(
        session=session,
        skill_store_attachment_name=attachment.name,
        query=str(arguments.get("query", "")),
        limit=arguments.get("limit"),
    )
    return {
        "status": "ok",
        "capability": "ws.skill.catalog",
        "target": attachment.name,
        **payload,
    }


def _markdown_create(
    session: WorkstationSession,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation learning capture, helps with saving one new markdown learning document into a writable workstation attachment without exposing generic host writes.

    Reference to Theory:
        Supports the workstation host-owned artifact model by keeping learning capture explicit, bounded, and attachment-scoped.

    Example Input Output:
        Input: `_markdown_create(session=3, arguments={'target': 'main', 'path': 'notes/learning.md', 'markdown_text': '# Learnings'})`
        Output: {'status': 'ok', 'capability': 'ws.markdown.create', 'target': 'main', 'path': 'notes/learning.md'}

    Args:
        session: Value for `session` used by `_markdown_create`. Expected type: `WorkstationSession`.
        arguments: Value for `arguments` used by `_markdown_create`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_markdown_create`.
    """
    attachment, destination_path, relative_path = _markdown_write_target_path(
        session,
        arguments,
        capability_name="ws.markdown.create",
    )
    if destination_path.exists():
        raise ValueError(f"Markdown destination already exists: {relative_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    body = _normalized_markdown_body(str(arguments.get("markdown_text", "")), append_mode=False)
    destination_path.write_text(body, encoding="utf-8")
    result = {
        "status": "ok",
        "capability": "ws.markdown.create",
        "target": attachment.name,
        "path": relative_path,
        "absolute_path": str(destination_path),
        "markdown_chars": len(body),
    }
    publish_workstation_event(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        event_kind="markdown_saved",
        payload={
            "target": attachment.name,
            "path": relative_path,
            "absolute_path": str(destination_path),
            "mode": "create",
            "markdown_chars": len(body),
        },
    )
    return result


def _markdown_append(
    session: WorkstationSession,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation learning capture, helps with appending new markdown learnings to one existing markdown document in a writable workstation attachment.

    Reference to Theory:
        Supports the workstation host-owned artifact model by keeping additive learning capture explicit, bounded, and attachment-scoped.

    Example Input Output:
        Input: `_markdown_append(session=3, arguments={'target': 'main', 'path': 'notes/learning.md', 'markdown_text': '## More'})`
        Output: {'status': 'ok', 'capability': 'ws.markdown.append', 'target': 'main', 'path': 'notes/learning.md'}

    Args:
        session: Value for `session` used by `_markdown_append`. Expected type: `WorkstationSession`.
        arguments: Value for `arguments` used by `_markdown_append`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_markdown_append`.
    """
    attachment, destination_path, relative_path = _markdown_write_target_path(
        session,
        arguments,
        capability_name="ws.markdown.append",
    )
    if not destination_path.exists():
        raise ValueError(f"Markdown destination does not exist: {relative_path}")
    if destination_path.is_dir():
        raise ValueError("ws.markdown.append requires a file path, not a directory.")
    existing_text = destination_path.read_text(encoding="utf-8")
    body = _normalized_markdown_body(str(arguments.get("markdown_text", "")), append_mode=True)
    separator = ""
    if existing_text and not existing_text.endswith("\n"):
        separator += "\n"
    if existing_text.strip():
        separator += "\n"
    destination_path.write_text(existing_text + separator + body, encoding="utf-8")
    result = {
        "status": "ok",
        "capability": "ws.markdown.append",
        "target": attachment.name,
        "path": relative_path,
        "absolute_path": str(destination_path),
        "appended_chars": len(body),
    }
    publish_workstation_event(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        event_kind="markdown_appended",
        payload={
            "target": attachment.name,
            "path": relative_path,
            "absolute_path": str(destination_path),
            "mode": "append",
            "appended_chars": len(body),
        },
    )
    return result


def _skill_import_source_path(
    session: WorkstationSession,
    arguments: dict[str, Any],
) -> tuple[WorkstationAttachment, Path]:
    """
    High Level Purpose:
        In circumstances like workstation skill import, helps with resolving one portable source file from an explicit attachment target into a concrete bounded path.

    Reference to Theory:
        Supports the workstation attachment model by keeping skill import scoped to declared attachments rather than ambient host paths.

    Example Input Output:
        Input: `_skill_import_source_path(session=3, arguments={'source_target': 'main', 'path': 'skill.yaml'})`
        Output: (WorkstationAttachment(name='main', kind='workspace', ...), Path('/tmp/project/skill.yaml'))

    Args:
        session: Value for `session` used by `_skill_import_source_path`. Expected type: `WorkstationSession`.
        arguments: Value for `arguments` used by `_skill_import_source_path`. Expected type: `dict[str, Any]`.

    Returns:
        tuple[WorkstationAttachment, Path]: Result produced by `_skill_import_source_path`.
    """
    source_target = collapse_ws(str(arguments.get("source_target", ""))) or "session"
    relative_path = collapse_ws(str(arguments.get("path", "")))
    if not relative_path:
        raise ValueError("ws.skill.import requires a non-empty path.")
    source_attachment = _attachment_by_name(session, source_target)
    source_path = _safe_join(Path(source_attachment.source), relative_path)
    if not source_path.exists():
        raise ValueError(f"Import source does not exist: {relative_path}")
    if source_path.is_dir():
        raise ValueError("ws.skill.import requires a file path, not a directory.")
    return source_attachment, source_path


def _skill_import(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill lifecycle operations, helps with importing one portable skill bundle into the persistent workstation skill home and refreshing workstation discovery state.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by reusing governed skill import semantics while keeping the persistent worker catalog explicit and session-visible.

    Example Input Output:
        Input: `_skill_import(session=3, attachment=WorkstationAttachment(name='skills', kind='skill_store', source='/tmp/skills.sqlite3', access_mode='read_write', mount_path='/workstation/skills/store.sqlite3'), arguments={'source_target': 'main', 'path': 'skill.yaml'})`
        Output: {'status': 'ok', 'capability': 'ws.skill.import', 'imported_count': 1}

    Args:
        session: Value for `session` used by `_skill_import`. Expected type: `WorkstationSession`.
        attachment: Value for `attachment` used by `_skill_import`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_skill_import`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_skill_import`.
    """
    source_attachment, source_path = _skill_import_source_path(session, arguments)
    attachments_by_name = {item.name: item for item in session.attachments}
    imports_attachment = attachments_by_name.get("skills_imports")
    exports_attachment = attachments_by_name.get("skills_exports")
    if imports_attachment is None or exports_attachment is None:
        raise ValueError("The workstation session does not expose the persistent skills import/export attachments.")
    staged_source_path = _safe_join(
        Path(imports_attachment.source),
        normalized_skill_bundle_filename_for_source(source_path),
    )
    staged_source_path.parent.mkdir(parents=True, exist_ok=True)
    staged_source_path.write_text(source_path.read_text())
    canonical_export_name = collapse_ws(str(arguments.get("canonical_export_path", ""))) or normalized_skill_bundle_filename_for_source(source_path)
    canonical_export_path = _safe_join(Path(exports_attachment.source), canonical_export_name)
    report = import_workstation_skill_file(
        skill_store_path=Path(attachment.source),
        source_file=staged_source_path,
        canonical_export_path=canonical_export_path,
    )
    write_workstation_skill_catalog(Path(session.root_path), session)
    result = {
        "status": "ok",
        "capability": "ws.skill.import",
        "target": attachment.name,
        "source_target": source_attachment.name,
        "source_path": str(source_path),
        "staged_import_path": str(staged_source_path),
        **report,
    }
    publish_workstation_event(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        event_kind="skill_import_completed",
        payload={
            "target": attachment.name,
            "source_target": source_attachment.name,
            "source_path": str(source_path),
            "imported_count": int(result.get("imported_count", 0) or 0),
            "imported_titles": [
                collapse_ws(str(item.get("title", "")))
                for item in result.get("imported", [])
                if isinstance(item, dict) and collapse_ws(str(item.get("title", "")))
            ],
        },
    )
    publish_workstation_event(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        event_kind="skill_catalog_changed",
        payload={
            "reason": "import",
            "target": attachment.name,
        },
    )
    return result


def _skill_export(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill lifecycle operations, helps with exporting one governed worker from the persistent workstation skill home into a portable skill bundle and refreshing workstation discovery state.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by keeping worker exchange explicit and outside the workstation session boundary.

    Example Input Output:
        Input: `_skill_export(session=3, attachment=WorkstationAttachment(name='skills', kind='skill_store', source='/tmp/skills.sqlite3', access_mode='read_write', mount_path='/workstation/skills/store.sqlite3'), arguments={'skill_title': 'Workstation Greeting'})`
        Output: {'status': 'ok', 'capability': 'ws.skill.export', 'skill_title': 'Workstation Greeting'}

    Args:
        session: Value for `session` used by `_skill_export`. Expected type: `WorkstationSession`.
        attachment: Value for `attachment` used by `_skill_export`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_skill_export`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_skill_export`.
    """
    skill_title = collapse_ws(str(arguments.get("skill_title", "")))
    if not skill_title:
        raise ValueError("ws.skill.export requires a non-empty skill_title.")
    resolved = resolve_workstation_skill(
        skill_title=skill_title,
        skill_store_path=Path(attachment.source),
    )
    if resolved is None:
        raise ValueError(f"No workstation skill matches title {skill_title!r}.")
    resolved_artifact, _skill_source = resolved
    resolved_skill_title = collapse_ws(str(getattr(resolved_artifact, "title", ""))) or skill_title
    destination_target = collapse_ws(str(arguments.get("destination_target", ""))) or "skills_exports"
    destination_attachment = _attachment_by_name(session, destination_target)
    if destination_attachment.kind not in {"skill_exports", "session_root", "output", "scratch", "workspace"}:
        raise ValueError(f"Attachment {destination_attachment.name!r} cannot be used as a skill export destination.")
    destination_path_text = collapse_ws(str(arguments.get("destination_path", "")))
    if not destination_path_text:
        destination_path_text = batch_skill_export_filename(resolved_artifact)
    destination_path = _safe_join(Path(destination_attachment.source), destination_path_text)
    report = export_workstation_skill(
        skill_store_path=Path(attachment.source),
        skill_title=resolved_skill_title,
        destination_path=destination_path,
    )
    write_workstation_skill_catalog(Path(session.root_path), session)
    result = {
        "status": "ok",
        "capability": "ws.skill.export",
        "target": attachment.name,
        "destination_target": destination_attachment.name,
        **report,
    }
    publish_workstation_event(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        event_kind="skill_export_completed",
        payload={
            "target": attachment.name,
            "destination_target": destination_attachment.name,
            "skill_title": collapse_ws(str(result.get("skill_title", resolved_skill_title))),
            "destination_path": collapse_ws(str(result.get("destination_path", ""))),
        },
    )
    publish_workstation_event(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        event_kind="skill_catalog_changed",
        payload={
            "reason": "export",
            "target": attachment.name,
        },
    )
    return result


def _publish_workstation_blend_workflow_event(
    session: WorkstationSession,
    event: BlendWorkflowExecutionEvent,
) -> None:
    publish_workstation_event(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        event_kind=event.kind,
        payload={
            "workflow_execution_id": event.workflow_execution_id,
            "workflow_id": event.workflow_id,
            "workflow_run_id": event.workflow_run_id,
            "capability_name": event.capability_name,
            "target_name": event.target_name,
            "step_id": event.step_id,
            "operator_name": event.operator_name,
            "operator_kind": event.operator_kind,
            "iteration": event.iteration,
            "branch_label": event.branch_label,
            "status": event.status,
            "payload": dict(event.payload),
        },
        timestamp=event.timestamp,
    )


def _execute_workflow(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    workflow_plan: Any,
    *,
    capability_name: str,
    approved_delegation: list[dict[str, Any]] | None = None,
    approved_delegation_scope: str = "",
) -> dict[str, Any]:
    blend_context = blend_context_from_workstation_session(session)
    operator_providers = _workstation_operator_providers(
        session=session,
        skill_attachment=attachment,
    )
    try:
        resolved_steps, ordered_titles = resolve_blend_workflow_steps_from_providers(
            workflow_plan,
            context=blend_context,
            providers=operator_providers,
        )
    except Exception as exc:
        return {
            "status": "error",
            "capability": capability_name,
            "target": attachment.name,
            "requested_operator_names": [
                collapse_ws(str(item.operator_name))
                for item in getattr(workflow_plan, "steps", [])
                if collapse_ws(str(item.operator_name))
            ],
            "error": str(exc),
            "requested_skill_titles": [
                collapse_ws(str(item.operator_name))
                for item in getattr(workflow_plan, "steps", [])
                if collapse_ws(str(item.operator_name))
                and collapse_ws(str(getattr(item, "operator_kind", "skill") or "skill")) == "skill"
            ],
            "steps": [],
        }
    approved = normalized_requested_delegation(approved_delegation or [])
    return execute_blend_workflow(
        root_path=Path(session.root_path),
        session_id=session.session_id,
        context=blend_context,
        workflow_plan=workflow_plan,
        resolved_steps=resolved_steps,
        capability_name=capability_name,
        target_name=attachment.name,
        invoke_step=lambda resolved_step, invocation: _invoke_workstation_blend_operator(
            session=session,
            skill_attachment=attachment,
            resolved_step=resolved_step,
            invocation=invocation,
            approved_delegation=approved,
            approved_delegation_scope=approved_delegation_scope,
        ),
        execution_observer=lambda event: _publish_workstation_blend_workflow_event(session, event),
    )


def _resolve_workstation_capability_operator_record(
    *,
    session: WorkstationSession,
    operator_name: str,
    requested_target: str = "",
) -> BlendOperatorRecord | None:
    capability = collapse_ws(operator_name)
    if not is_shared_host_interaction_action_capability(capability):
        return None
    target_attachment = _default_workstation_capability_attachment(
        session,
        capability=capability,
        requested_target=requested_target,
    )
    required_visible_mounts: list[str] = []
    required_writable_mounts: list[str] = []
    allowed_targets: list[str] = []
    default_target = ""
    if target_attachment is not None:
        default_target = target_attachment.name
        allowed_targets = [target_attachment.name]
        required_visible_mounts = [target_attachment.name]
        if capability == "ws.process.run":
            required_writable_mounts = [target_attachment.name]
    return blend_capability_operator_record(
        capability_name=capability,
        operator=_workstation_capability_canonical_ir(capability),
        operator_source={
            "source_kind": "workstation_capability",
            "source_target": default_target,
        },
        input_shape=dict(_workstation_capability_canonical_ir(capability).get("input_contract", {})),
        output_shape=dict(_workstation_capability_canonical_ir(capability).get("output_contract", {})),
        semantic_description=capability,
        execution_adapter="workstation.capability",
        policy_requirements=_CAPABILITY_OPERATOR_AUTHORITIES.get(capability, ()),
        required_capabilities=(capability,),
        required_visible_mounts=required_visible_mounts,
        required_writable_mounts=required_writable_mounts,
        default_target=default_target,
        allowed_targets=allowed_targets,
        metadata={
            "capability": capability,
            "attachment_kind": target_attachment.kind if target_attachment is not None else "",
        },
    )


def _invoke_workstation_blend_operator(
    *,
    session: WorkstationSession,
    skill_attachment: WorkstationAttachment,
    resolved_step: Any,
    invocation: Any,
    approved_delegation: list[dict[str, Any]],
    approved_delegation_scope: str,
) -> dict[str, Any]:
    execution_adapter = collapse_ws(str(resolved_step.operator_descriptor.execution_adapter))
    if execution_adapter == "workstation.skill_invoke":
        step_requested_delegation = _nested_skill_host_requested_delegation(
            list(resolved_step.requested_delegation)
        )
        return _skill_invoke(
            session,
            skill_attachment,
            {
                "skill_title": resolved_step.operator_name,
                "semantic_unit": resolved_step.semantic_unit or resolved_step.operator_name,
                "invocation_payload": invocation.inputs,
                "requested_delegation": step_requested_delegation,
                "approved_delegation": approved_delegation,
                "approved_delegation_scope": approved_delegation_scope,
                "rationale": resolved_step.rationale,
            },
        )
    if execution_adapter == "workstation.capability":
        capability_arguments = dict(invocation.inputs)
        if invocation.resolved_target and resolved_step.operator_name != "ws.net.http":
            capability_arguments["target"] = invocation.resolved_target
        result = execute_workstation_capability(session, resolved_step.operator_name, capability_arguments)
        if collapse_ws(str(result.get("status", ""))).casefold() == "ok":
            projected_payload = {
                key: value
                for key, value in result.items()
                if key
                not in {
                    "status",
                    "capability",
                    "target",
                    "requested_delegation",
                    "approved_delegation",
                    "escalated_delegation",
                    "granted_delegation",
                    "missing_delegation",
                    "unsupported_delegation",
                    "answer",
                }
            }
            result = {
                **result,
                "result_payload": projected_payload,
                "parsed_output": projected_payload,
            }
        return result
    raise ValueError(f"Unsupported workstation Blend execution adapter {execution_adapter!r}.")


def _skill_compose(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    workflow_plan = blend_workflow_plan_from_skill_compose_arguments(arguments)
    return _execute_workflow(
        session,
        attachment,
        workflow_plan,
        capability_name="ws.skill.compose",
        approved_delegation=list(arguments.get("approved_delegation", [])),
        approved_delegation_scope=collapse_ws(str(arguments.get("approved_delegation_scope", ""))),
    )


def _workflow_list(session: WorkstationSession, arguments: dict[str, Any]) -> dict[str, Any]:
    kind = collapse_ws(str(arguments.get("kind", ""))) or "runs"
    status = collapse_ws(str(arguments.get("status", "")))
    try:
        limit = int(arguments.get("limit", 20) or 20)
    except (TypeError, ValueError):
        limit = 20
    view = workstation_workflow_summary_list_view(
        root_path=Path(session.root_path),
        kind=kind,
        status=status,
        limit=limit,
    )
    return {
        "status": "ok",
        "capability": "ws.workflow.list",
        "workflow_summary_list": view.to_dict(),
        "kind": view.kind,
        "items": [item.to_dict() for item in view.items],
        "returned_count": view.returned_count,
        "total_count": view.total_count,
        "latest_plan_id": view.latest_plan_id,
        "latest_run_id": view.latest_run_id,
        "workflow_store": {
            "index_path": str(Path(session.root_path).expanduser().resolve() / "BLEND_WORKFLOWS.json"),
        },
    }


def _workflow_get(session: WorkstationSession, arguments: dict[str, Any]) -> dict[str, Any]:
    workflow_run_id = collapse_ws(str(arguments.get("workflow_run_id", "")))
    workflow_id = collapse_ws(str(arguments.get("workflow_id", "")))
    try:
        if workflow_run_id or workflow_id:
            result = workstation_workflow_query_view(
                root_path=Path(session.root_path),
                workflow_id=workflow_id,
                workflow_run_id=workflow_run_id,
            )
            return {
                **result,
                "capability": "ws.workflow.get",
            }
    except FileNotFoundError:
        missing_identifier = workflow_run_id or workflow_id
        missing_kind = "workflow run" if workflow_run_id else "workflow plan"
        return {
            "status": "error",
            "capability": "ws.workflow.get",
            "error": f"No persisted {missing_kind} matches id {missing_identifier!r}.",
        }
    return {
        "status": "error",
        "capability": "ws.workflow.get",
        "error": "ws.workflow.get requires workflow_id or workflow_run_id.",
    }


def _operator_list(session: WorkstationSession, arguments: dict[str, Any]) -> dict[str, Any]:
    operator_kind = collapse_ws(str(arguments.get("operator_kind", "")))
    query = collapse_ws(str(arguments.get("query", "")))
    try:
        limit = int(arguments.get("limit", 20) or 20)
    except (TypeError, ValueError):
        limit = 20
    skill_attachment = _optional_skill_store_attachment(
        session,
        collapse_ws(str(arguments.get("target", ""))),
    )
    context = blend_context_from_workstation_session(session)
    providers = _workstation_operator_providers(
        session=session,
        skill_attachment=skill_attachment,
    )
    view = workstation_operator_summary_list_view(
        context=context,
        providers=providers,
        operator_kind=operator_kind,
        query=query,
        limit=limit,
    )
    return {
        "status": "ok",
        "capability": "ws.operator.list",
        "operator_summary_list": view.to_dict(),
        "operator_kind": view.operator_kind,
        "query": view.query,
        "items": [item.to_dict() for item in view.items],
        "returned_count": view.returned_count,
        "provider_ids": list(view.provider_ids),
    }


def _operator_get(session: WorkstationSession, arguments: dict[str, Any]) -> dict[str, Any]:
    operator_name = collapse_ws(str(arguments.get("operator_name", "")))
    operator_kind = collapse_ws(str(arguments.get("operator_kind", "")))
    if not operator_name:
        return {
            "status": "error",
            "capability": "ws.operator.get",
            "error": "ws.operator.get requires operator_name.",
        }
    skill_attachment = _optional_skill_store_attachment(
        session,
        collapse_ws(str(arguments.get("target", ""))),
    )
    context = blend_context_from_workstation_session(session)
    providers = _workstation_operator_providers(
        session=session,
        skill_attachment=skill_attachment,
    )
    view = workstation_operator_detail_view(
        context=context,
        providers=providers,
        operator_name=operator_name,
        operator_kind=operator_kind,
    )
    if view is None:
        return {
            "status": "error",
            "capability": "ws.operator.get",
            "operator_name": operator_name,
            "operator_kind": operator_kind,
            "error": f"No dynamic Blend operator matches {operator_name!r}.",
        }
    return {
        "status": "ok",
        "capability": "ws.operator.get",
        "operator_detail": view.to_dict(),
        "operator": dict(view.operator),
    }


def _workflow_run(session: WorkstationSession, arguments: dict[str, Any]) -> dict[str, Any]:
    workflow_plan_payload = arguments.get("workflow_plan")
    workflow_id = collapse_ws(str(arguments.get("workflow_id", "")))
    if not isinstance(workflow_plan_payload, Mapping):
        if not workflow_id:
            return {
                "status": "error",
                "capability": "ws.workflow.run",
                "error": "ws.workflow.run requires workflow_plan or workflow_id.",
            }
        try:
            workflow_plan_payload = load_blend_workflow_plan(Path(session.root_path), workflow_id).to_dict()
        except FileNotFoundError:
            return {
                "status": "error",
                "capability": "ws.workflow.run",
                "workflow_id": workflow_id,
                "error": f"No persisted workflow plan matches id {workflow_id!r}.",
            }
    effective_workflow_plan = dict(workflow_plan_payload)
    if "root_inputs" in arguments and isinstance(arguments.get("root_inputs"), Mapping):
        effective_workflow_plan["root_inputs"] = dict(arguments.get("root_inputs", {}))
    if "root_references" in arguments and isinstance(arguments.get("root_references"), Mapping):
        effective_workflow_plan["root_references"] = dict(arguments.get("root_references", {}))
    final_output_step = collapse_ws(str(arguments.get("final_output_step", "")))
    if final_output_step:
        effective_workflow_plan["final_output_step"] = final_output_step
    target = collapse_ws(str(arguments.get("target", "")))
    if target:
        metadata = dict(effective_workflow_plan.get("metadata", {})) if isinstance(effective_workflow_plan.get("metadata", {}), Mapping) else {}
        metadata["target"] = target
        effective_workflow_plan["metadata"] = metadata
    plan_metadata = dict(effective_workflow_plan.get("metadata", {})) if isinstance(effective_workflow_plan.get("metadata", {}), Mapping) else {}
    workflow_plan = blend_workflow_plan_from_skill_compose_arguments({"workflow_plan": effective_workflow_plan})
    return _execute_workflow(
        session,
        _skill_store_attachment(
            session,
            collapse_ws(str(plan_metadata.get("target", ""))) or "skills",
        ),
        workflow_plan,
        capability_name="ws.workflow.run",
        approved_delegation=list(arguments.get("approved_delegation", [])),
        approved_delegation_scope=collapse_ws(str(arguments.get("approved_delegation_scope", ""))),
    )


def _skill_invoke(
    session: WorkstationSession,
    attachment: WorkstationAttachment,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation-mediated use of installed governed skills, helps with invoking one skill by title from a session-bound skill store while recording requested and effective delegation data.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by making the workstation invoke installed skills explicitly instead of treating higher-level behaviors as ambient host capabilities.

    Example Input Output:
        Input: `_skill_invoke(session=3, attachment=WorkstationAttachment(name='skills', kind='skill_store', source='/tmp/skills.sqlite3', access_mode='read', mount_path='/workstation/skills/store.sqlite3'), arguments={'skill_title': 'Say Hi From Wasm'})`
        Output: {'status': 'ok', 'capability': 'ws.skill.invoke', 'skill_title': 'Say Hi From Wasm', 'answer': 'hi'}

    Args:
        session: Value for `session` used by `_skill_invoke`. Expected type: `WorkstationSession`.
        attachment: Value for `attachment` used by `_skill_invoke`. Expected type: `WorkstationAttachment`.
        arguments: Value for `arguments` used by `_skill_invoke`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_skill_invoke`.
    """
    skill_title = collapse_ws(str(arguments.get("skill_title", "")))
    if not skill_title:
        raise ValueError("ws.skill.invoke requires a non-empty skill_title.")
    requested_delegation = normalized_requested_delegation(arguments.get("requested_delegation"))
    approved_delegation = normalized_requested_delegation(arguments.get("approved_delegation"))
    resolved = resolve_workstation_skill(
        skill_title=skill_title,
        skill_store_path=Path(attachment.source),
    )
    if resolved is None:
        return {
            "status": "error",
            "capability": "ws.skill.invoke",
            "target": attachment.name,
            "skill_title": skill_title,
            "requested_delegation": requested_delegation,
            "approved_delegation": approved_delegation,
            "escalated_delegation": [],
            "granted_delegation": [],
            "missing_delegation": [],
            "error": f"No workstation skill matches title {skill_title!r}.",
        }
    artifact, skill_source = resolved
    if (
        skill_source.get("source_kind") == "builtin_workstation"
        and skill_title == "Workstation Repo Search"
    ):
        derived_payload, requested_delegation = _derive_repo_search_invocation_inputs(
            session,
            arguments,
            requested_delegation,
        )
        if derived_payload is not None:
            arguments = dict(arguments)
            arguments["invocation_payload"] = derived_payload

    store = workstation_skill_store(Path(attachment.source))
    inventory = workstation_governance_inventory(store)
    declaration = runtime_skill_declaration_for_artifact(artifact)
    resolved_executor_framework = str(
        declaration.get("executor_framework", "")
        or ability_executor_framework(
            representation=str(
                getattr(getattr(artifact, "representation", ""), "value", getattr(artifact, "representation", ""))
            ),
            content=dict(getattr(artifact, "content", {}) or {}),
        )
        or ""
    )
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    current_admission = evaluate_skill_admission(
        declaration,
        skill_title=str(getattr(artifact, "title", "")),
        kind=skill_kind_from_artifact(artifact),
        executor_framework=ability_executor_framework(
            representation=str(getattr(getattr(artifact, "representation", ""), "value", getattr(artifact, "representation", ""))),
            content=content,
        ),
        skill_content=content,
        policy_artifacts=list(inventory.get("policies", [])),
        approval_artifacts=list(inventory.get("approvals", [])),
    )
    content["skill_admission"] = current_admission
    content["skill_lifecycle"] = synthesized_skill_lifecycle(
        admission_status=str(current_admission.get("status", "")),
        policy_record=bool(content.get("skill_policy")),
        default_updated_at=str(current_admission.get("evaluated_at", content.get("created_at", ""))),
    )
    artifact = replace(artifact, content=content)
    declaration = runtime_skill_declaration_for_artifact(artifact)
    executor_framework = ability_executor_framework(
        representation=str(
            getattr(getattr(artifact, "representation", ""), "value", getattr(artifact, "representation", ""))
        ),
        content=dict(getattr(artifact, "content", {}) or {}),
    )
    if not executor_framework:
        executor_framework = resolved_executor_framework
    semantic_unit = collapse_ws(str(arguments.get("semantic_unit", ""))) or skill_title
    content = dict(getattr(artifact, "content", {}) or {})
    input_contract = dict(content.get("input_contract", {}) or {})
    explicit_payload = workstation_explicit_invocation_payload(
        artifact=artifact,
        arguments=arguments,
        explicit_payload=arguments.get("invocation_payload"),
    )
    invocation_payload, missing_required_inputs = workstation_skill_invocation_payload(
        artifact=artifact,
        semantic_unit=semantic_unit,
        explicit_payload=explicit_payload,
    )
    invocation_payload = _normalize_workspace_scoped_invocation_payload(session, invocation_payload)
    missing_required_inputs = workstation_missing_required_inputs(
        artifact=artifact,
        payload=invocation_payload,
    )
    requested_delegation = _derive_requested_delegation_from_invocation_payload(
        artifact=artifact,
        invocation_payload=invocation_payload,
        requested_delegation=requested_delegation,
    )
    if invocation_payload is None and not input_contract:
        invocation_payload = {}
    elif (invocation_payload is None or invocation_payload == {}) and sorted(input_contract) == ["payload"]:
        invocation_payload = {"payload": {}}
        missing_required_inputs = []
    invocation_mode = (
        "llm_routed"
        if collapse_ws(str(arguments.get("semantic_unit", ""))) and collapse_ws(str(arguments.get("semantic_unit", ""))) != skill_title
        else "direct_named"
    )
    invocation_request = workstation_skill_invocation_request(
        artifact=artifact,
        semantic_unit=semantic_unit,
        payload=invocation_payload,
        missing_required_inputs=missing_required_inputs,
        invocation_mode=invocation_mode,
    )
    granted_delegation, missing_delegation = host_interaction_delegation_requires_escalation(
        allowed_capabilities=session.allowed_capabilities,
        requested_delegation=requested_delegation,
    )
    approved_pairs = {
        (
            collapse_ws(str(item.get("capability", ""))),
            collapse_ws(str(item.get("target", ""))),
        )
        for item in approved_delegation
    }
    escalated_delegation: list[dict[str, Any]] = []
    remaining_missing_delegation: list[dict[str, Any]] = []
    for item in missing_delegation:
        item_pair = (
            collapse_ws(str(item.get("capability", ""))),
            collapse_ws(str(item.get("target", ""))),
        )
        if item_pair in approved_pairs:
            escalated_delegation.append(item)
        else:
            remaining_missing_delegation.append(item)
    if remaining_missing_delegation:
        approval_result = {
            "status": "approval_required",
            "capability": "ws.skill.invoke",
            "target": attachment.name,
            "skill_title": skill_title,
            "requested_delegation": requested_delegation,
            "approved_delegation": approved_delegation,
            "escalated_delegation": escalated_delegation,
            "granted_delegation": granted_delegation,
            "missing_delegation": remaining_missing_delegation,
            "error": "The requested delegated rights exceed the current workstation session grant.",
        }
        approval_result["answer"] = workstation_skill_invocation_status_answer(approval_result)
        return _skill_invoke_result_with_contract(approval_result, invocation_request=invocation_request)
    effective_requested_delegation = [*granted_delegation, *escalated_delegation]
    delegated_mounts, effective_granted_delegation, unsupported_delegation = build_host_interaction_delegated_mounts(
        workstation_host_interaction_attachments(session),
        granted_delegation=effective_requested_delegation,
    )
    if unsupported_delegation:
        unsupported_result = {
            "status": "unsupported",
            "capability": "ws.skill.invoke",
            "target": attachment.name,
            "skill_title": skill_title,
            "requested_delegation": requested_delegation,
            "approved_delegation": approved_delegation,
            "escalated_delegation": escalated_delegation,
            "granted_delegation": effective_granted_delegation,
            "missing_delegation": [],
            "unsupported_delegation": unsupported_delegation,
            "error": "Some delegated workstation rights could not be mapped into the nested skill runtime.",
        }
        unsupported_result["answer"] = workstation_skill_invocation_status_answer(unsupported_result)
        return _skill_invoke_result_with_contract(unsupported_result, invocation_request=invocation_request)
    delegated_mounts, effective_granted_delegation = _align_delegated_mount_data_classes(
        declaration=declaration,
        delegated_mounts=delegated_mounts,
        granted_delegation=effective_granted_delegation,
    )
    artifact = artifact_with_delegated_virtual_mounts(
        artifact,
        delegated_mounts=delegated_mounts,
        conflict_label="delegated workstation",
    )
    if missing_required_inputs:
        answer_text = workstation_skill_invocation_error_answer(
            skill_title=skill_title,
            missing_required_inputs=missing_required_inputs,
        )
        return _skill_invoke_result_with_contract({
            "status": "error",
            "capability": "ws.skill.invoke",
            "target": attachment.name,
            "skill_title": skill_title,
            "skill_kind": skill_kind_from_artifact(artifact),
            "skill_source": skill_source,
            "executor_framework": str(executor_framework or declaration.get("executor_framework", "")),
            "declaration_excerpt": {
                "authorities_requested": list(declaration.get("authorities_requested", [])),
                "risk_tier": str(declaration.get("risk_tier", "")),
            },
            "requested_delegation": requested_delegation,
            "approved_delegation": approved_delegation,
            "escalated_delegation": escalated_delegation,
            "granted_delegation": effective_granted_delegation,
            "missing_delegation": [],
            "unsupported_delegation": unsupported_delegation,
            "rationale": str(arguments.get("rationale", "")),
            "approved_delegation_scope": collapse_ws(str(arguments.get("approved_delegation_scope", ""))),
            "answer": answer_text,
            "error": answer_text,
            "notes": [
                f"Missing required invocation inputs: {', '.join(missing_required_inputs)}",
            ],
            "nested_effect_traces": [],
            "nested_capability_grants": [],
            "nested_run_outcome": "ongoing",
            "delegated_virtual_mounts": delegated_mounts,
        }, invocation_request=invocation_request)
    nested_state, nested_controller = controller_runtime_provider().bootstrap_controller(
        semantic_unit=semantic_unit,
        llm_policy="off",
    )
    if executor_framework:
        nested_state.controller_features.supported_executors = list(
            dict.fromkeys(
                [str(item) for item in nested_state.controller_features.supported_executors] + [executor_framework]
            )
        )
    nested_controller.artifact_store = store
    nested_controller._current_skill_governance_snapshot_cache = inventory
    nested_state.supplement_profile["artifact_store"] = store.describe()
    nested_state.learned_artifacts[str(getattr(artifact, "id", ""))] = artifact
    artifact_type_value = str(
        getattr(getattr(artifact, "artifact_type", ""), "value", getattr(artifact, "artifact_type", ""))
    ).strip().lower()
    if artifact_type_value == "ability":
        result = nested_controller.execute_function_artifact(
            artifact,
            semantic_unit=semantic_unit,
            explicit_payload=invocation_payload,
        )
        nested_terminal_error = workstation_nested_skill_terminal_error(result)
        answer_text = workstation_nested_skill_answer_text(result)
        if not answer_text and (not result.ok or nested_terminal_error):
            answer_text = workstation_nested_skill_failure_answer_text(skill_title=skill_title, result=result)
        effective_status = "ok" if result.ok and not nested_terminal_error else "error"
        return _skill_invoke_result_with_contract({
            "status": effective_status,
            "capability": "ws.skill.invoke",
            "target": attachment.name,
            "skill_title": skill_title,
            "skill_kind": skill_kind_from_artifact(artifact),
            "skill_source": skill_source,
            "executor_framework": str(executor_framework or declaration.get("executor_framework", "")),
            "declaration_excerpt": {
                "authorities_requested": list(declaration.get("authorities_requested", [])),
                "risk_tier": str(declaration.get("risk_tier", "")),
            },
            "requested_delegation": requested_delegation,
            "approved_delegation": approved_delegation,
            "escalated_delegation": escalated_delegation,
            "granted_delegation": effective_granted_delegation,
            "missing_delegation": [],
            "unsupported_delegation": unsupported_delegation,
            "rationale": str(arguments.get("rationale", "")),
            "approved_delegation_scope": collapse_ws(str(arguments.get("approved_delegation_scope", ""))),
            "answer": answer_text,
            "stderr": result.stderr,
            "parsed_output": bounded_nested_output_payload(getattr(result, "parsed_output", None)),
            "result_payload": bounded_nested_output_payload(getattr(result, "result", None)),
            "result": bounded_nested_output_payload(getattr(result, "result", None)),
            "notes": list(result.notes),
            "nested_effect_traces": bounded_nested_effect_traces(list(nested_state.effect_traces)),
            "nested_capability_grants": bounded_nested_capability_grants(list(nested_state.capability_grants)),
            "nested_run_outcome": nested_state.run_outcome.value,
            "delegated_virtual_mounts": delegated_mounts,
        }, invocation_request=invocation_request)
    answer = nested_controller.artifact_answer_text(
        artifact,
        semantic_unit=semantic_unit,
        explicit_payload=invocation_payload,
    )
    if not answer:
        return _skill_invoke_result_with_contract({
            "status": "error",
            "capability": "ws.skill.invoke",
            "target": attachment.name,
            "skill_title": skill_title,
            "skill_kind": skill_kind_from_artifact(artifact),
            "executor_framework": str(executor_framework or declaration.get("executor_framework", "")),
            "requested_delegation": requested_delegation,
            "approved_delegation": approved_delegation,
            "escalated_delegation": escalated_delegation,
            "granted_delegation": effective_granted_delegation,
            "missing_delegation": [],
            "unsupported_delegation": unsupported_delegation,
            "error": "Target skill did not expose an invokable ability or answer-bearing knowledge surface.",
        }, invocation_request=invocation_request)
    return _skill_invoke_result_with_contract({
        "status": "ok",
        "capability": "ws.skill.invoke",
        "target": attachment.name,
        "skill_title": skill_title,
        "skill_kind": skill_kind_from_artifact(artifact),
        "skill_source": skill_source,
        "executor_framework": str(executor_framework or declaration.get("executor_framework", "")),
        "declaration_excerpt": {
            "authorities_requested": list(declaration.get("authorities_requested", [])),
            "risk_tier": str(declaration.get("risk_tier", "")),
        },
        "requested_delegation": requested_delegation,
        "approved_delegation": approved_delegation,
        "escalated_delegation": escalated_delegation,
        "granted_delegation": effective_granted_delegation,
        "missing_delegation": [],
        "unsupported_delegation": unsupported_delegation,
        "rationale": str(arguments.get("rationale", "")),
        "approved_delegation_scope": collapse_ws(str(arguments.get("approved_delegation_scope", ""))),
        "answer": answer,
        "parsed_output": None,
        "result_payload": None,
        "result": None,
        "nested_effect_traces": bounded_nested_effect_traces(list(nested_state.effect_traces)),
        "nested_capability_grants": bounded_nested_capability_grants(list(nested_state.capability_grants)),
        "nested_run_outcome": nested_state.run_outcome.value,
        "delegated_virtual_mounts": delegated_mounts,
    }, invocation_request=invocation_request)
