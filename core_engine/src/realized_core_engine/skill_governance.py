# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_semantics.applied_model import Artifact, utc_now
from realized_core_governance.admission import evaluate_skill_admission_with_compatibility
from realized_core_governance.declarations import (
    SKILL_AUTHORITY_BOUND_FIELDS,
    SKILL_DECLARATION_REQUIRED_FIELDS,
    policy_answer_summary,
    skill_declaration_from_payload,
    skill_policy_from_payload,
)
from realized_core_governance.current_use import (
    skill_admission_allows_current_use,
    skill_current_use_allows_invocation,
)
from realized_core_governance.lifecycle import artifact_effective_skill_lifecycle
from realized_core_governance.records import (
    artifact_is_policy_record,
    artifact_skill_admission,
    artifact_skill_declaration,
    artifact_skill_policy,
)
from realized_core_governance.vocabulary import (
    SKILL_APPROVAL_CLASSES,
    SKILL_AUTHORITIES,
    SKILL_KIND_CHOICES,
    SKILL_RISK_TIERS,
    normalize_skill_approval_class,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)
from realized_core_governance.safety import (
    artifact_is_incident_record,
    artifact_is_revocation_record,
    governed_safety_lifecycle_overlay,
)
from realized_skill_semantics.declaration import (
    SKILL_SCHEMA_VERSION_V1,
    SKILL_SCHEMA_VERSION_V2,
    SKILL_SCHEMA_VERSIONS,
    composition_binding_targets,
    normalize_skill_schema_version,
)
from realized_skill_semantics.execution import (
    ability_executor_framework,
    normalize_executor_framework_name,
)
from realized_core_runtime.skill_compatibility import runtime_skill_compatibility_issue
from realized_core_runtime.skill_declarations import synthesized_skill_declaration_for_artifact




def artifact_current_use_admission(
    artifact: Artifact,
    *,
    policy_artifacts: list[Artifact] | None = None,
    approval_artifacts: list[Artifact] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like invocation-time governance and host mediation, helps with deriving the admission decision that should govern current use under the currently installed policy and approval artifacts.

    Reference to Theory:
        Supports open governance sections 9, 10, and 13 by preventing invocation from depending only on stale import-time admission when current policy or approval state is available.

    Example Input Output:
        Input: `artifact_current_use_admission(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'), policy_artifacts=[], approval_artifacts=[])`
        Output: {'status': 'held', 'admitted': False, 'rationale': 'No policy artifact is currently installed for governed v2 skills.', 'policy_titles': [], 'approval_titles': [], 'required_approval_class': 'automatic'}

    Args:
        artifact: Value for `artifact` used by `artifact_current_use_admission`. Expected type: `Artifact`.
        policy_artifacts: Value for `policy_artifacts` used by `artifact_current_use_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.
        approval_artifacts: Value for `approval_artifacts` used by `artifact_current_use_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `artifact_current_use_admission`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    schema = normalize_skill_schema_version(content.get("skill_schema", SKILL_SCHEMA_VERSION_V1))
    if schema != SKILL_SCHEMA_VERSION_V2:
        return {
            "status": "legacy_implicit_admit",
            "admitted": True,
            "rationale": "",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    stored_admission = artifact_skill_admission(artifact)
    if artifact_is_policy_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Policy artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [artifact.title],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    from realized_core_governance.approval import artifact_is_approval_record

    if artifact_is_approval_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Approval artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [],
            "approval_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    if artifact_is_revocation_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Revocation artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    if artifact_is_incident_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Incident artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    current_policy_artifacts = policy_artifacts if policy_artifacts is not None else []
    current_approval_artifacts = approval_artifacts if approval_artifacts is not None else []
    if current_policy_artifacts or current_approval_artifacts:
        declaration = artifact_skill_declaration(artifact)
        if not declaration:
            return {
                "status": "held",
                "admitted": False,
                "rationale": "Governed skill has no declaration record for current-use evaluation.",
                "policy_titles": [],
                "approval_titles": [],
                "required_approval_class": "automatic",
                "evaluated_at": utc_now(),
            }
        kind = normalize_skill_kind(content.get("skill_kind", ""), default=str(getattr(artifact.artifact_type, "value", artifact.artifact_type)))
        executor_framework = ability_executor_framework(
            representation=str(getattr(artifact.representation, "value", artifact.representation)),
            content=content,
        )
        return evaluate_skill_admission(
            declaration,
            skill_title=artifact.title,
            kind=kind,
            executor_framework=executor_framework,
            skill_content=content,
            policy_artifacts=current_policy_artifacts,
            approval_artifacts=current_approval_artifacts,
        )
    return stored_admission


def artifact_admitted_for_use(artifact: Artifact) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like runtime reuse and execution gating, helps with deciding whether a governed skill artifact is currently admitted for use.

    Reference to Theory:
        Supports open governance sections 9 and 10 by preventing invocation of governed skills whose admission, activation, trust, or quarantine state does not currently permit use.

    Example Input Output:
        Input: `artifact_admitted_for_use(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: (True, '')

    Args:
        artifact: Value for `artifact` used by `artifact_admitted_for_use`. Expected type: `Artifact`.

    Returns:
        tuple[bool, str]: Result produced by `artifact_admitted_for_use`.
    """
    return artifact_admitted_for_use_with_governance(
        artifact,
        policy_artifacts=None,
        approval_artifacts=None,
    )


def artifact_admitted_for_use_with_governance(
    artifact: Artifact,
    *,
    policy_artifacts: list[Artifact] | None,
    approval_artifacts: list[Artifact] | None,
    revocation_artifacts: list[Artifact] | None = None,
    incident_artifacts: list[Artifact] | None = None,
) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like invocation-time governance and runtime selection, helps with deciding whether a governed skill artifact is currently admitted for use under stored or current governance state.

    Reference to Theory:
        Supports open governance sections 9, 10, and 13 by allowing runtime use decisions to reflect current policy and approval state when available.

    Example Input Output:
        Input: `artifact_admitted_for_use_with_governance(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'), policy_artifacts=[], approval_artifacts=[])`
        Output: (False, 'No policy artifact is currently installed for governed v2 skills.')

    Args:
        artifact: Value for `artifact` used by `artifact_admitted_for_use_with_governance`. Expected type: `Artifact`.
        policy_artifacts: Value for `policy_artifacts` used by `artifact_admitted_for_use_with_governance`. Expected type: `list[Artifact] | None`.
        approval_artifacts: Value for `approval_artifacts` used by `artifact_admitted_for_use_with_governance`. Expected type: `list[Artifact] | None`.

    Returns:
        tuple[bool, str]: Result produced by `artifact_admitted_for_use_with_governance`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    schema = normalize_skill_schema_version(content.get("skill_schema", SKILL_SCHEMA_VERSION_V1))
    if schema != SKILL_SCHEMA_VERSION_V2:
        return skill_current_use_allows_invocation(
            schema_version=schema,
            admission=None,
            lifecycle=None,
        )
    admission = artifact_current_use_admission(
        artifact,
        policy_artifacts=policy_artifacts,
        approval_artifacts=approval_artifacts,
    )
    admission_allowed, admission_reason = skill_admission_allows_current_use(
        schema_version=schema,
        admission=admission,
    )
    if not admission_allowed:
        return False, admission_reason
    lifecycle = artifact_effective_skill_lifecycle(
        artifact,
        current_admission_status=str(admission.get("status", "")),
    )
    overlay = governed_safety_lifecycle_overlay(
        skill_title=artifact.title,
        kind=normalize_skill_kind(
            content.get("skill_kind", ""),
            default=str(getattr(artifact.artifact_type, "value", artifact.artifact_type)),
        ),
        revocation_artifacts=revocation_artifacts,
        incident_artifacts=incident_artifacts,
    )
    lifecycle.update({key: value for key, value in overlay.items() if key not in {"revocation_titles", "incident_titles"} and value not in (None, "", [], {})})
    return skill_current_use_allows_invocation(
        schema_version=schema,
        admission=admission,
        lifecycle=lifecycle,
    )


def evaluate_skill_admission(
    declaration: Mapping[str, Any],
    *,
    skill_title: str = "",
    kind: str,
    executor_framework: str = "",
    skill_content: Mapping[str, Any] | None = None,
    policy_artifacts: list[Artifact] | None = None,
    approval_artifacts: list[Artifact] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like skill import and later activation checks, helps with evaluating whether a declaration-first governed skill is admitted, held, or rejected under the currently installed policy artifacts.

    Reference to Theory:
        Supports open governance sections 8, 9, 10, 13, and 16 by applying policy, authority, approval, and risk checks before use.

    Example Input Output:
        Input: `evaluate_skill_admission(declaration={'intent': 'Open a browser URL.', 'authorities_requested': ['execute'], 'authority_bounds': {'execute': {'scope': 'local_desktop', 'target': 'browser_application', 'context': 'explicit_user_prompt', 'duration': 'single_invocation', 'triggering_conditions': ['user invokes skill'], 'approval_class': 'automatic'}}, 'data_classes_touched': ['public'], 'side_effects': ['launch browser'], 'persistence_behavior': 'none', 'invocation_rights': ['direct_user_invocation'], 'composition_rights': [], 'escalation_rights': [], 'approval_requirements': ['automatic'], 'risk_tier': 'tier1_bounded_transform', 'inputs': {'url': 'target URL'}, 'outputs': {'status': 'open status'}}, skill_title='Open Browser URL', kind='ability', executor_framework='python3', policy_artifacts=[], approval_artifacts=[])`
        Output: {'status': 'held', 'admitted': False, 'rationale': 'No policy artifact is currently installed for governed v2 skills.', 'policy_titles': [], 'approval_titles': [], 'required_approval_class': 'automatic', 'evaluated_at': '2026-03-31T12:00:00Z'}

    Args:
        declaration: Value for `declaration` used by `evaluate_skill_admission`. Expected type: `Mapping[str, Any]`.
        skill_title: Value for `skill_title` used by `evaluate_skill_admission`. Expected type: `str`. Defaults to `''`.
        kind: Value for `kind` used by `evaluate_skill_admission`. Expected type: `str`.
        executor_framework: Value for `executor_framework` used by `evaluate_skill_admission`. Expected type: `str`. Defaults to `''`.
        skill_content: Value for `skill_content` used by `evaluate_skill_admission`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        policy_artifacts: Value for `policy_artifacts` used by `evaluate_skill_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.
        approval_artifacts: Value for `approval_artifacts` used by `evaluate_skill_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `evaluate_skill_admission`.
    """
    normalized_kind = normalize_skill_kind(kind)
    normalized_executor = normalize_executor_framework_name(executor_framework)
    risk_tier = normalize_skill_risk_tier(declaration.get("risk_tier", "tier1_bounded_transform"))
    compatibility_issue = runtime_skill_compatibility_issue(
        kind=normalized_kind,
        executor_framework=normalized_executor,
        risk_tier=risk_tier,
        skill_content=skill_content,
    )
    return evaluate_skill_admission_with_compatibility(
        declaration,
        skill_title=skill_title,
        kind=normalized_kind,
        executor_framework=normalized_executor,
        compatibility_issue=compatibility_issue,
        policy_artifacts=policy_artifacts,
        approval_artifacts=approval_artifacts,
        evaluated_at=utc_now,
    )


__all__ = [
    "SKILL_APPROVAL_CLASSES",
    "SKILL_AUTHORITIES",
    "SKILL_AUTHORITY_BOUND_FIELDS",
    "SKILL_DECLARATION_REQUIRED_FIELDS",
    "SKILL_KIND_CHOICES",
    "SKILL_RISK_TIERS",
    "SKILL_SCHEMA_VERSIONS",
    "artifact_admitted_for_use",
    "artifact_admitted_for_use_with_governance",
    "artifact_current_use_admission",
    "artifact_skill_policy",
    "composition_binding_targets",
    "evaluate_skill_admission",
    "normalize_skill_approval_class",
    "normalize_skill_authorities",
    "normalize_skill_kind",
    "normalize_skill_risk_tier",
    "policy_answer_summary",
    "skill_declaration_from_payload",
    "skill_policy_from_payload",
    "synthesized_skill_declaration_for_artifact",
]
