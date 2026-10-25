# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import hashlib
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from applied_theory_types import Artifact, CrossBoundaryResult, json_safe, utc_now
from capability_runtime import (
    issue_capability_grants_for_artifact,
    required_authority_for_effect_kind,
)
from execution_frameworks import (
    execute_cross_boundary,
    normalize_ability_runtime_content,
    normalize_executor_framework_name,
)
from realized_host_interaction.context import host_interaction_virtual_mounts, host_interaction_workspace_root
from host_abi import host_abi_version
from host_brokers import invoke_host_broker
from runtime_governance_context import (
    runtime_artifact_governance_context,
    runtime_artifact_trace_context,
)
from semantic_text import collapse_ws


EFFECT_TRACE_RECEIPT_SCHEMA_VERSION = "bssc_effect_receipt.v1"


@dataclass
class EffectRequest:
    effect_kind: str
    artifact_id: str
    artifact_title: str
    semantic_unit: str
    executor_framework: str
    invocation_payload: Any
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime host mediation for skill effects, helps with expressing one requested effect as a durable typed record before any boundary action occurs.

        Reference to Theory:
            Supports bundle-style host mediation by making each material effect request explicit and inspectable before execution.

        Example Input Output:
            Input: `to_dict()`
            Output: {'effect_kind': 'execute.python3', 'artifact_id': 'artifact-force-function', 'executor_framework': 'python3'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)


@dataclass
class EffectDecision:
    allowed: bool
    rationale: str
    required_authority: str = ""
    grant_ids: list[str] = field(default_factory=list)
    evaluated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime host mediation for governed skills, helps with serializing the allow-or-deny decision attached to one effect request.

        Reference to Theory:
            Supports open governance by preserving the policy-and-authority decision that stood between a skill and a material host effect.

        Example Input Output:
            Input: `to_dict()`
            Output: {'allowed': True, 'rationale': 'Effect request is covered by issued runtime grants.', 'required_authority': 'execute'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)


def _canonical_admission_status(value: Any) -> str:
    normalized = collapse_ws(str(value)).lower()
    if normalized in {"legacy_implicit_admit", "admitted"}:
        return "admitted"
    return normalized


def _canonical_receipt_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            key_text = collapse_ws(str(key))
            if key_text in {"id", "issued_at", "created_at", "evaluated_at", "updated_at"}:
                continue
            current = value.get(key)
            if key_text == "status":
                current = _canonical_admission_status(current)
            normalized[key_text] = _canonical_receipt_payload(current)
        return normalized
    if isinstance(value, list):
        return [_canonical_receipt_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_canonical_receipt_payload(item) for item in value]
    return json_safe(value)


def _effect_receipt(kind: str, payload: Any) -> dict[str, Any]:
    canonical = _canonical_receipt_payload(payload)
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
        "kind": collapse_ws(str(kind)),
        "digest": digest,
    }


def _runtime_broker_governance_context(
    self,
    *,
    artifact: Artifact,
    declaration: Mapping[str, Any] | None,
    grants: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like broker-mediated data governance, helps with assembling the runtime context needed by governed mounts, named queries, and per-skill state surfaces.

    Reference to Theory:
        Supports bundle-style data governance by carrying current declaration, grants, store path, and governed data handles into the broker layer without exposing raw host resources directly.

    Example Input Output:
        Input: `_runtime_broker_governance_context(self=controller, artifact=Artifact(id='artifact-demo', title='Demo', artifact_type='ability', representation='python_script'), declaration={'data_classes_touched': ['public']}, grants=[{'authority': 'read'}])`
        Output: {'artifact_id': 'artifact-demo', 'sqlite_path': '/repo/state/common.sqlite3', 'virtual_mounts': {}, 'named_queries': {}}

    Args:
        self: Bound controller instance that owns runtime state and store wiring.
        artifact: Value for `artifact` used by `_runtime_broker_governance_context`. Expected type: `Artifact`.
        declaration: Value for `declaration` used by `_runtime_broker_governance_context`. Expected type: `Mapping[str, Any] | None`.
        grants: Value for `grants` used by `_runtime_broker_governance_context`. Expected type: `list[Mapping[str, Any]]`.

    Returns:
        dict[str, Any]: Result produced by `_runtime_broker_governance_context`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    sqlite_path = collapse_ws(
        str(
            getattr(self.artifact_store, "sqlite_path", "")
            or getattr(getattr(self.artifact_store, "fallback_store", None), "sqlite_path", "")
            or os.getenv("STATE_SQLITE_PATH", "")
        )
    )
    backend_context = getattr(self, "host_interaction_context", None)
    attachment_mounts = host_interaction_virtual_mounts(backend_context)
    explicit_mounts = dict(content.get("virtual_mounts", {})) if isinstance(content.get("virtual_mounts", {}), Mapping) else {}
    merged_mounts = dict(attachment_mounts)
    merged_mounts.update(explicit_mounts)
    return {
        "artifact_id": str(getattr(artifact, "id", "")),
        "artifact_title": collapse_ws(str(getattr(artifact, "title", ""))),
        "host_abi_version": host_abi_version(),
        "sqlite_path": sqlite_path,
        "workspace_root": host_interaction_workspace_root(backend_context, fallback_root=os.getcwd()),
        "declaration": dict(declaration) if isinstance(declaration, Mapping) else {},
        "grants": [dict(item) for item in grants if isinstance(item, Mapping)],
        "virtual_mounts": merged_mounts,
        "named_queries": dict(content.get("named_queries", {})) if isinstance(content.get("named_queries", {}), Mapping) else {},
        "skill_state_namespace": collapse_ws(str(content.get("skill_state_namespace", ""))) or str(getattr(artifact, "id", "")),
    }


def evaluate_effect_request(
    request: EffectRequest,
    *,
    declaration: Mapping[str, Any] | None,
    admitted: bool,
    admission_reason: str,
    grants: list[Mapping[str, Any]],
) -> EffectDecision:
    """
    High Level Purpose:
        In circumstances like governed execution of Python, bash, or ansible skills, helps with deciding whether the requested host effect is permitted under the current declaration, admission state, and issued grants.

    Reference to Theory:
        Supports open governance sections 8, 9, and 10 by turning declaration and admission into an actual runtime allow-or-deny gate.

    Example Input Output:
        Input: `evaluate_effect_request(request=EffectRequest(effect_kind='execute.python3', artifact_id='artifact-force-function', artifact_title='Force from mass and acceleration', semantic_unit='Calculate force from mass=3 and acceleration=4.', executor_framework='python3', invocation_payload={'mass': 3, 'acceleration': 4}), declaration={'authorities_requested': ['execute'], 'executor_framework': 'python3'}, admitted=True, admission_reason='', grants=[{'id': 'grant-1f2e3d4c5b6a', 'authority': 'execute'}])`
        Output: EffectDecision(allowed=True, rationale='Effect request is covered by issued runtime grants.', required_authority='execute')

    Args:
        request: Value for `request` used by `evaluate_effect_request`. Expected type: `EffectRequest`.
        declaration: Value for `declaration` used by `evaluate_effect_request`. Expected type: `Mapping[str, Any] | None`.
        admitted: Value for `admitted` used by `evaluate_effect_request`. Expected type: `bool`.
        admission_reason: Value for `admission_reason` used by `evaluate_effect_request`. Expected type: `str`.
        grants: Value for `grants` used by `evaluate_effect_request`. Expected type: `list[Mapping[str, Any]]`.

    Returns:
        EffectDecision: Result produced by `evaluate_effect_request`.
    """
    required_authority = required_authority_for_effect_kind(request.effect_kind)
    if not admitted:
        return EffectDecision(
            allowed=False,
            rationale=collapse_ws(admission_reason) or "Governed skill is not admitted for this effect.",
            required_authority=required_authority,
        )
    if not required_authority:
        return EffectDecision(
            allowed=False,
            rationale=f"No governed authority mapping is registered for effect kind {request.effect_kind}.",
            required_authority="",
        )
    grant_ids = [
        collapse_ws(str(item.get("id", "")))
        for item in grants
        if collapse_ws(str(item.get("authority", ""))) == required_authority and collapse_ws(str(item.get("id", "")))
    ]
    if not grant_ids:
        return EffectDecision(
            allowed=False,
            rationale=f"Runtime grants do not cover required authority {required_authority} for {request.effect_kind}.",
            required_authority=required_authority,
        )
    declared = dict(declaration) if isinstance(declaration, Mapping) else {}
    declared_executor = normalize_executor_framework_name(declared.get("executor_framework", ""))
    if declared_executor and request.executor_framework and declared_executor != request.executor_framework:
        return EffectDecision(
            allowed=False,
            rationale=(
                f"Declared executor framework {declared_executor} does not match requested effect "
                f"framework {request.executor_framework}."
            ),
            required_authority=required_authority,
            grant_ids=grant_ids,
        )
    return EffectDecision(
        allowed=True,
        rationale="Effect request is covered by issued runtime grants.",
        required_authority=required_authority,
        grant_ids=grant_ids,
    )


def record_effect_trace(
    self,
    *,
    artifact: Artifact,
    request: EffectRequest,
    decision: EffectDecision,
    grants: list[Mapping[str, Any]],
    admission_snapshot: Mapping[str, Any] | None = None,
    lifecycle_snapshot: Mapping[str, Any] | None = None,
    result: CrossBoundaryResult | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed host mediation around skill execution, helps with preserving one constitutional effect trace record that joins request, decision, grants, and outcome.

    Reference to Theory:
        Supports open governance trace requirements by making declaration-derived authority use visible at the level of each material effect.

    Example Input Output:
        Input: `record_effect_trace(self=controller, artifact=Artifact(id='artifact-force-function', title='Force from mass and acceleration', artifact_type='ability', representation='python_script'), request=EffectRequest(effect_kind='execute.python3', artifact_id='artifact-force-function', artifact_title='Force from mass and acceleration', semantic_unit='Calculate force from mass=3 and acceleration=4.', executor_framework='python3', invocation_payload={'mass': 3, 'acceleration': 4}), decision=EffectDecision(allowed=True, rationale='Effect request is covered by issued runtime grants.', required_authority='execute'), grants=[{'id': 'grant-1f2e3d4c5b6a', 'authority': 'execute'}], result=CrossBoundaryResult(ok=True, command=['uv'], exit_code=0, stdout='{}', stderr=''))`
        Output: {'id': 'effect-abc123', 'effect_kind': 'execute.python3', 'allowed': True, 'artifact_id': 'artifact-force-function'}

    Args:
        self: Bound controller instance that owns runtime state and step recording.
        artifact: Value for `artifact` used by `record_effect_trace`. Expected type: `Artifact`.
        request: Value for `request` used by `record_effect_trace`. Expected type: `EffectRequest`.
        decision: Value for `decision` used by `record_effect_trace`. Expected type: `EffectDecision`.
        grants: Value for `grants` used by `record_effect_trace`. Expected type: `list[Mapping[str, Any]]`.
        admission_snapshot: Value for `admission_snapshot` used by `record_effect_trace`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        result: Value for `result` used by `record_effect_trace`. Expected type: `CrossBoundaryResult | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `record_effect_trace`.
    """
    trace_seed = (
        f"{artifact.id}|{request.effect_kind}|{request.created_at}|"
        f"{decision.allowed}|{result.exit_code if result is not None else 'denied'}"
    )
    trace_id = f"effect-{hashlib.sha1(trace_seed.encode('utf-8')).hexdigest()[:12]}"
    trace_context = runtime_artifact_trace_context(
        artifact,
        admission_snapshot=admission_snapshot,
        lifecycle_snapshot=lifecycle_snapshot,
    )
    trace = {
        "id": trace_id,
        "created_at": utc_now(),
        "host_abi_version": host_abi_version(),
        "artifact_id": str(getattr(artifact, "id", "")),
        "artifact_title": collapse_ws(str(getattr(artifact, "title", ""))),
        "request": request.to_dict(),
        "decision": decision.to_dict(),
        "grants": [dict(item) for item in grants if isinstance(item, Mapping)],
        "grant_ids": [collapse_ws(str(item.get("id", ""))) for item in grants if collapse_ws(str(item.get("id", "")))],
        "declaration": dict(trace_context.get("declaration", {})) if isinstance(trace_context.get("declaration", {}), Mapping) else {},
        "admission": dict(trace_context.get("admission", {})) if isinstance(trace_context.get("admission", {}), Mapping) else {},
        "lifecycle": dict(trace_context.get("lifecycle", {})) if isinstance(trace_context.get("lifecycle", {}), Mapping) else {},
        "result": {
            "ok": bool(result.ok) if result is not None else False,
            "exit_code": int(result.exit_code) if result is not None else 1,
            "answer": str(result.answer) if result is not None else "",
            "stderr": str(result.stderr) if result is not None else "",
            "notes": list(result.notes) if result is not None else [],
        },
    }
    trace["receipts"] = {
        "request": _effect_receipt(
            "request",
            {
                "effect_kind": request.effect_kind,
                "executor_framework": request.executor_framework,
                "invocation_payload": request.invocation_payload,
            },
        ),
        "declaration": _effect_receipt("declaration", trace["declaration"]),
        "policy": _effect_receipt(
            "policy",
            {
                "policy_titles": list(trace["admission"].get("policy_titles", [])),
                "required_approval_class": trace["admission"].get("required_approval_class", "automatic"),
            },
        ),
        "approval": _effect_receipt(
            "approval",
            {
                "approval_titles": list(trace["admission"].get("approval_titles", [])),
                "required_approval_class": trace["admission"].get("required_approval_class", "automatic"),
            },
        ),
        "lifecycle": _effect_receipt("lifecycle", trace["lifecycle"]),
        "grants": _effect_receipt("grants", grants),
    }
    self.state.effect_traces.append(json_safe(trace))
    self.state.record_step(
        kind="host_effect_mediation",
        node_id=self.state.root_id,
        intent="Mediate material host effects through declared authority, admission, and issued capability grants.",
        action=f"mediate {request.effect_kind}",
        result="effect allowed" if decision.allowed else "effect denied",
        evaluation=decision.rationale,
        payload={
            "trace_id": trace_id,
            "artifact_id": artifact.id,
            "effect_kind": request.effect_kind,
            "allowed": decision.allowed,
            "grant_ids": trace["grant_ids"],
            "exit_code": trace["result"]["exit_code"],
        },
    )
    return trace


def execute_mediated_artifact_effect(
    self,
    artifact: Artifact,
    *,
    semantic_unit: str,
    executor_framework: str,
    executable_text: str,
    invocation_payload: Any,
    timeout_seconds: float | None = None,
) -> CrossBoundaryResult:
    """
    High Level Purpose:
        In circumstances like executing a learned governed ability against the host environment, helps with routing the effect through runtime grant issuance, mediation, trace, and only then the executor boundary.

    Reference to Theory:
        Supports the first Python-host cut of bundle-style governance by making current executor-backed skills pass through one mediated authority gate without redesigning the controller loop.

    Example Input Output:
        Input: `execute_mediated_artifact_effect(self=controller, artifact=Artifact(id='artifact-force-function', title='Force from mass and acceleration', artifact_type='ability', representation='python_script'), semantic_unit='Calculate force from mass=3 and acceleration=4.', executor_framework='python3', executable_text='def main():\\n    pass', invocation_payload={'mass': 3, 'acceleration': 4}, timeout_seconds=45.0)`
        Output: CrossBoundaryResult(ok=True, command=['uv', 'run'], exit_code=0, stdout='...', stderr='')

    Args:
        self: Bound controller instance that owns runtime state and execution helpers.
        artifact: Value for `artifact` used by `execute_mediated_artifact_effect`. Expected type: `Artifact`.
        semantic_unit: Value for `semantic_unit` used by `execute_mediated_artifact_effect`. Expected type: `str`.
        executor_framework: Value for `executor_framework` used by `execute_mediated_artifact_effect`. Expected type: `str`.
        executable_text: Value for `executable_text` used by `execute_mediated_artifact_effect`. Expected type: `str`.
        invocation_payload: Value for `invocation_payload` used by `execute_mediated_artifact_effect`. Expected type: `Any`.
        timeout_seconds: Value for `timeout_seconds` used by `execute_mediated_artifact_effect`. Expected type: `float | None`. Defaults to `None`.

    Returns:
        CrossBoundaryResult: Result produced by `execute_mediated_artifact_effect`.
    """
    normalized_executor = normalize_executor_framework_name(executor_framework or "python3") or "python3"
    effect_kind = f"execute.{normalized_executor}"
    governed_context = runtime_artifact_governance_context(self, artifact)
    declaration = dict(governed_context.get("declaration", {})) if isinstance(governed_context.get("declaration", {}), Mapping) else {}
    current_admission = dict(governed_context.get("admission", {})) if isinstance(governed_context.get("admission", {}), Mapping) else {}
    effective_lifecycle = dict(governed_context.get("lifecycle", {})) if isinstance(governed_context.get("lifecycle", {}), Mapping) else {}
    admitted = bool(governed_context.get("admitted"))
    admission_reason = str(governed_context.get("admission_reason", ""))
    grants = issue_capability_grants_for_artifact(
        artifact,
        effect_kind=effect_kind,
        executor_framework=normalized_executor,
        semantic_unit=semantic_unit,
        admission_snapshot=current_admission,
    ) if admitted else []
    if grants:
        self.use_capability(
            "capability_granting",
            node=None,
            contribution=f"issue governed runtime grants for {artifact.title}",
        )
        self.state.capability_grants.extend(json_safe(grants))
    request = EffectRequest(
        effect_kind=effect_kind,
        artifact_id=str(getattr(artifact, "id", "")),
        artifact_title=collapse_ws(str(getattr(artifact, "title", ""))),
        semantic_unit=collapse_ws(str(semantic_unit)),
        executor_framework=normalized_executor,
        invocation_payload=json_safe(invocation_payload),
    )
    self.use_capability(
        "host_mediation",
        node=None,
        contribution=f"mediate {effect_kind} for {artifact.title}",
    )
    decision = evaluate_effect_request(
        request,
        declaration=declaration,
        admitted=admitted,
        admission_reason=admission_reason,
        grants=grants,
    )
    if not decision.allowed:
        denied_result = CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr=decision.rationale,
            notes=["Host mediation denied the requested governed effect before boundary execution."],
        )
        record_effect_trace(
            self,
            artifact=artifact,
            request=request,
            decision=decision,
            grants=grants,
            admission_snapshot=current_admission,
            lifecycle_snapshot=effective_lifecycle,
            result=denied_result,
        )
        return denied_result
    broker_governance_context = _runtime_broker_governance_context(
        self,
        artifact=artifact,
        declaration=declaration,
        grants=grants,
    )
    runtime_executable_text = str(executable_text or "")
    if normalized_executor == "bash":
        runtime_content = normalize_ability_runtime_content(
            dict(artifact.content) if isinstance(artifact.content, Mapping) else {},
            title=collapse_ws(str(getattr(artifact, "title", ""))),
        )
        shell_script = runtime_content.get("shell_script")
        if isinstance(shell_script, str) and shell_script.strip():
            runtime_executable_text = shell_script
    result = execute_cross_boundary(
        framework=normalized_executor,
        executable_text=runtime_executable_text,
        stdin_payload=invocation_payload,
        timeout_seconds=timeout_seconds,
        host_runtime_context={
            "artifact_id": str(getattr(artifact, "id", "")),
            "artifact_title": collapse_ws(str(getattr(artifact, "title", ""))),
            "semantic_unit": collapse_ws(str(semantic_unit)),
            "host_abi_version": host_abi_version(),
            "declaration": declaration,
            "admission": dict(current_admission),
            "grants": grants,
            "sqlite_path": broker_governance_context.get("sqlite_path", ""),
            "workspace_root": broker_governance_context.get("workspace_root", ""),
            "virtual_mounts": broker_governance_context.get("virtual_mounts", {}),
            "named_queries": broker_governance_context.get("named_queries", {}),
            "skill_state_namespace": broker_governance_context.get("skill_state_namespace", ""),
        },
    )
    child_host_traces = []
    if isinstance(result.metadata, Mapping):
        child_host_traces = [
            dict(item)
            for item in result.metadata.get("host_traces", [])
            if isinstance(item, Mapping)
        ]
    nested_capability_grants = []
    if isinstance(result.metadata, Mapping):
        nested_capability_grants = [
            dict(item)
            for item in result.metadata.get("nested_capability_grants", [])
            if isinstance(item, Mapping)
        ]
    if nested_capability_grants:
        self.state.capability_grants.extend(json_safe(nested_capability_grants))
    nested_effect_traces = []
    if isinstance(result.metadata, Mapping):
        nested_effect_traces = [
            dict(item)
            for item in result.metadata.get("nested_effect_traces", [])
            if isinstance(item, Mapping)
        ]
    if nested_effect_traces:
        self.state.effect_traces.extend(json_safe(nested_effect_traces))
        self.state.record_step(
            kind="host_effect_subtrace_ingest",
            node_id=self.state.root_id,
            intent="Preserve governed nested effect traces emitted by alternate runtimes that compose with other governed skills or tools.",
            action="ingest nested governed host traces",
            result=f"{len(nested_effect_traces)} nested host effects recorded",
            evaluation="alternate-runtime governed composition remained visible to the parent constitutional trace surface",
            payload={"count": len(nested_effect_traces), "artifact_id": artifact.id},
        )
    if child_host_traces:
        self.state.effect_traces.extend(json_safe(child_host_traces))
        self.state.record_step(
            kind="host_effect_subtrace_ingest",
            node_id=self.state.root_id,
            intent="Preserve governed sub-effect traces emitted by broker-aware Python skills.",
            action="ingest child host broker traces",
            result=f"{len(child_host_traces)} child host effects recorded",
            evaluation="python skill host effects remained visible to the parent governed trace surface",
            payload={"count": len(child_host_traces), "artifact_id": artifact.id},
        )
    record_effect_trace(
        self,
        artifact=artifact,
        request=request,
        decision=decision,
        grants=grants,
        admission_snapshot=current_admission,
        lifecycle_snapshot=effective_lifecycle,
        result=result,
    )
    return result


def execute_mediated_host_broker_request(
    self,
    artifact: Artifact,
    *,
    broker_name: str,
    broker_arguments: Mapping[str, Any] | None = None,
    semantic_unit: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like moving device, filesystem, store, or network actions behind named host brokers, helps with mediating one broker request through declaration-derived grants before the broker is invoked.

    Reference to Theory:
        Supports the next Python-host step toward the bundle target by making non-executor host actions go through the same admission, authority, and trace layer as executable abilities.

    Example Input Output:
        Input: `execute_mediated_host_broker_request(self=controller, artifact=Artifact(id='artifact-write-file', title='Write text file', artifact_type='ability', representation='python_script'), broker_name='fs.write_text', broker_arguments={'path': '/tmp/demo.txt', 'text': 'hello'}, semantic_unit='Write hello to a file.')`
        Output: {'status': 'ok', 'path': '/tmp/demo.txt', 'bytes_written': 5, 'effect_trace_id': 'effect-abc123'}

    Args:
        self: Bound controller instance that owns runtime state and execution helpers.
        artifact: Value for `artifact` used by `execute_mediated_host_broker_request`. Expected type: `Artifact`.
        broker_name: Value for `broker_name` used by `execute_mediated_host_broker_request`. Expected type: `str`.
        broker_arguments: Value for `broker_arguments` used by `execute_mediated_host_broker_request`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        semantic_unit: Value for `semantic_unit` used by `execute_mediated_host_broker_request`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `execute_mediated_host_broker_request`.
    """
    effect_kind = collapse_ws(str(broker_name))
    governed_context = runtime_artifact_governance_context(self, artifact)
    declaration = dict(governed_context.get("declaration", {})) if isinstance(governed_context.get("declaration", {}), Mapping) else {}
    current_admission = dict(governed_context.get("admission", {})) if isinstance(governed_context.get("admission", {}), Mapping) else {}
    effective_lifecycle = dict(governed_context.get("lifecycle", {})) if isinstance(governed_context.get("lifecycle", {}), Mapping) else {}
    admitted = bool(governed_context.get("admitted"))
    admission_reason = str(governed_context.get("admission_reason", ""))
    grants = issue_capability_grants_for_artifact(
        artifact,
        effect_kind=effect_kind,
        semantic_unit=semantic_unit,
        admission_snapshot=current_admission,
    ) if admitted else []
    if grants:
        self.use_capability(
            "capability_granting",
            node=None,
            contribution=f"issue governed runtime grants for {artifact.title}",
        )
        self.state.capability_grants.extend(json_safe(grants))
    request = EffectRequest(
        effect_kind=effect_kind,
        artifact_id=str(getattr(artifact, "id", "")),
        artifact_title=collapse_ws(str(getattr(artifact, "title", ""))),
        semantic_unit=collapse_ws(str(semantic_unit)),
        executor_framework="",
        invocation_payload=json_safe(dict(broker_arguments or {})),
    )
    self.use_capability(
        "host_mediation",
        node=None,
        contribution=f"mediate {effect_kind} for {artifact.title}",
    )
    decision = evaluate_effect_request(
        request,
        declaration=declaration,
        admitted=admitted,
        admission_reason=admission_reason,
        grants=grants,
    )
    if not decision.allowed:
        denied_result = CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr=decision.rationale,
            notes=["Host mediation denied the requested broker effect before host invocation."],
        )
        trace = record_effect_trace(
            self,
            artifact=artifact,
            request=request,
            decision=decision,
            grants=grants,
            admission_snapshot=current_admission,
            lifecycle_snapshot=effective_lifecycle,
            result=denied_result,
        )
        return {
            "status": "error",
            "broker": effect_kind,
            "error": decision.rationale,
            "effect_trace_id": trace["id"],
        }
    broker_result = invoke_host_broker(
        effect_kind,
        arguments=broker_arguments,
        governance_context=_runtime_broker_governance_context(
            self,
            artifact=artifact,
            declaration=declaration,
            grants=grants,
        ),
    )
    nested_capability_grants = [
        dict(item)
        for item in broker_result.get("nested_capability_grants", [])
        if isinstance(item, Mapping)
    ] if isinstance(broker_result, Mapping) else []
    if nested_capability_grants:
        self.state.capability_grants.extend(json_safe(nested_capability_grants))
    nested_effect_traces = [
        dict(item)
        for item in broker_result.get("nested_effect_traces", [])
        if isinstance(item, Mapping)
    ] if isinstance(broker_result, Mapping) else []
    if nested_effect_traces:
        self.state.effect_traces.extend(json_safe(nested_effect_traces))
        self.state.record_step(
            kind="host_effect_subtrace_ingest",
            node_id=self.state.root_id,
            intent="Preserve governed sub-effect traces emitted by mediated host brokers that invoke other governed skills.",
            action="ingest nested host broker traces",
            result=f"{len(nested_effect_traces)} nested host effects recorded",
            evaluation="broker-mediated skill or tool invocation remained visible to the parent governed trace surface",
            payload={"count": len(nested_effect_traces), "artifact_id": artifact.id, "broker_name": effect_kind},
        )
    success = str(broker_result.get("status", "")).strip().lower() == "ok"
    boundary_result = CrossBoundaryResult(
        ok=success,
        command=[effect_kind],
        exit_code=0 if success else 1,
        stdout="",
        stderr="" if success else str(broker_result.get("error", "")),
        parsed_output=broker_result,
        result=broker_result,
        answer=str(
            broker_result.get("answer", broker_result.get("text", broker_result.get("status", "")))
        ),
        notes=[] if success else ["Host broker returned an error result."],
    )
    trace = record_effect_trace(
        self,
        artifact=artifact,
        request=request,
        decision=decision,
        grants=grants,
        admission_snapshot=current_admission,
        lifecycle_snapshot=effective_lifecycle,
        result=boundary_result,
    )
    return {**broker_result, "effect_trace_id": trace["id"]}
