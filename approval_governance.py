# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from artifact_contracts import ArtifactContentView
from semantic_text import collapse_ws
from skill_governance_primitives import (
    normalize_skill_approval_class,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)

APPROVAL_RECORD_STATUSES = (
    "approved",
    "revoked",
    "expired",
)


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [collapse_ws(str(item)) for item in value if collapse_ws(str(item))]
    return [collapse_ws(str(value))] if collapse_ws(str(value)) else []


def normalize_approval_record_status(value: Any, *, default: str = "approved") -> str:
    """
    High Level Purpose:
        In circumstances like approval artifact import and invocation checks, helps with normalizing approval record status into one explicit governance ladder.

    Reference to Theory:
        Supports open governance section 13 by making approval records machine-checkable instead of relying on free-form wording.

    Example Input Output:
        Input: `normalize_approval_record_status(value='approved')`
        Output: 'approved'

    Args:
        value: Value for `value` used by `normalize_approval_record_status`. Expected type: `Any`.
        default: Value for `default` used by `normalize_approval_record_status`. Expected type: `str`. Defaults to `'approved'`.

    Returns:
        str: Result produced by `normalize_approval_record_status`.
    """
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in APPROVAL_RECORD_STATUSES:
        return normalized
    return default


def skill_approval_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing governed approval artifacts, helps with normalizing the approval record into one machine-checkable structure before admission evaluation.

    Reference to Theory:
        Supports open governance sections 6 and 13 by treating approval as a governed artifact rather than an implicit side note.

    Example Input Output:
        Input: `skill_approval_from_payload(payload={'schema': 'bssc_skill.v2', 'kind': 'approval', 'approval': {'intent': 'Approve browser opening.', 'approval_class': 'operator_approved', 'subject_titles': ['Open Browser URL'], 'issued_by': 'operator://local-admin', 'rationale': 'Approved local browser use.'}})`
        Output: {'intent': 'Approve browser opening.', 'approval_class': 'operator_approved', 'subject_titles': ['Open Browser URL'], 'subject_kinds': [], 'approved_authorities': [], 'approved_risk_tiers': [], 'issued_by': 'operator://local-admin', 'rationale': 'Approved local browser use.', 'status': 'approved', 'valid_from': '', 'valid_until': ''}

    Args:
        payload: Value for `payload` used by `skill_approval_from_payload`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `skill_approval_from_payload`.
    """
    schema = collapse_ws(str(payload.get("schema", "")))
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    if schema != "bssc_skill.v2" or kind != "approval":
        return {}
    approval = dict(payload.get("approval", {})) if isinstance(payload.get("approval", {}), Mapping) else {}
    normalized = {
        "intent": collapse_ws(str(approval.get("intent", ""))),
        "approval_class": normalize_skill_approval_class(approval.get("approval_class", "automatic")),
        "subject_titles": _string_list(approval.get("subject_titles", [])),
        "subject_kinds": [normalize_skill_kind(item) for item in _string_list(approval.get("subject_kinds", []))],
        "approved_authorities": normalize_skill_authorities(approval.get("approved_authorities", [])),
        "approved_risk_tiers": [normalize_skill_risk_tier(item) for item in _string_list(approval.get("approved_risk_tiers", []))],
        "issued_by": collapse_ws(str(approval.get("issued_by", ""))),
        "rationale": collapse_ws(str(approval.get("rationale", ""))),
        "status": normalize_approval_record_status(approval.get("status", "approved")),
        "valid_from": collapse_ws(str(approval.get("valid_from", ""))),
        "valid_until": collapse_ws(str(approval.get("valid_until", ""))),
    }
    missing_fields = [
        field_name
        for field_name in ("intent", "approval_class", "subject_titles", "issued_by", "rationale")
        if normalized.get(field_name) in (None, "", [], {})
    ]
    if missing_fields:
        raise ValueError(
            "Approval artifact v2 requires non-empty fields: " + ", ".join(missing_fields)
        )
    return normalized


def approval_answer_summary(approval: Mapping[str, Any]) -> str:
    """
    High Level Purpose:
        In circumstances like approval artifact import and export, helps with projecting the normalized approval record into a readable summary answer surface.

    Reference to Theory:
        Supports open governance by keeping approval artifacts inspectable to humans while still being machine-governed.

    Example Input Output:
        Input: `approval_answer_summary(approval={'approval_class': 'operator_approved', 'subject_titles': ['Open Browser URL'], 'status': 'approved'})`
        Output: 'Approval record operator_approved approved for Open Browser URL.'

    Args:
        approval: Value for `approval` used by `approval_answer_summary`. Expected type: `Mapping[str, Any]`.

    Returns:
        str: Result produced by `approval_answer_summary`.
    """
    subjects = ", ".join(_string_list(approval.get("subject_titles", []))) or "unspecified skill"
    approval_class = normalize_skill_approval_class(approval.get("approval_class", "automatic"))
    status = normalize_approval_record_status(approval.get("status", "approved"))
    return f"Approval record {approval_class} {status} for {subjects}."


def artifact_skill_approval(artifact: ArtifactContentView) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like admission checks and governed export, helps with reading the normalized approval specification stored on an approval artifact.

    Reference to Theory:
        Supports open governance sections 6 and 13 by making approval artifacts machine-readable during admission and review.

    Example Input Output:
        Input: `artifact_skill_approval(artifact=Artifact(id='artifact-skill-approval', title='Operator Approval', artifact_type='knowledge', representation='yaml'))`
        Output: {'approval_class': 'operator_approved', 'subject_titles': ['Open Browser URL']}

    Args:
        artifact: Value for `artifact` used by `artifact_skill_approval`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_skill_approval`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    return dict(content.get("skill_approval", {})) if isinstance(content.get("skill_approval", {}), Mapping) else {}


def artifact_is_approval_record(artifact: ArtifactContentView) -> bool:
    """
    High Level Purpose:
        In circumstances like export, admission, and invocation gating, helps with detecting that an artifact is an approval record rather than an invokable or explanatory user-facing skill.

    Reference to Theory:
        Supports open governance by keeping approval artifacts reviewable without letting them masquerade as ordinary invokable skills.

    Example Input Output:
        Input: `artifact_is_approval_record(artifact=Artifact(id='artifact-skill-approval', title='Operator Approval', artifact_type='knowledge', representation='yaml'))`
        Output: True

    Args:
        artifact: Value for `artifact` used by `artifact_is_approval_record`. Expected type: `Artifact`.

    Returns:
        bool: Result produced by `artifact_is_approval_record`.
    """
    return bool(artifact_skill_approval(artifact))


def _valid_at_or_open(value: str, *, upper_bound: bool = False) -> bool:
    text = collapse_ws(value)
    if not text:
        return True
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
        now = datetime.now(moment.tzinfo)
    except Exception:
        return True
    return now <= moment if upper_bound else now >= moment


def approval_matches_skill(
    approval: Mapping[str, Any],
    *,
    skill_title: str,
    kind: str,
    requested_authorities: list[str],
    risk_tier: str,
    required_approval_class: str,
) -> bool:
    """
    High Level Purpose:
        In circumstances like admission-time approval resolution, helps with deciding whether one approval record satisfies the current skill invocation requirements.

    Reference to Theory:
        Supports open governance section 13 by making approval artifacts a concrete precondition for higher-risk or policy-gated admission.

    Example Input Output:
        Input: `approval_matches_skill(approval={'approval_class': 'operator_approved', 'subject_titles': ['Open Browser URL'], 'status': 'approved'}, skill_title='Open Browser URL', kind='ability', requested_authorities=['execute'], risk_tier='tier3_sensitive', required_approval_class='operator_approved')`
        Output: True

    Args:
        approval: Value for `approval` used by `approval_matches_skill`. Expected type: `Mapping[str, Any]`.
        skill_title: Value for `skill_title` used by `approval_matches_skill`. Expected type: `str`.
        kind: Value for `kind` used by `approval_matches_skill`. Expected type: `str`.
        requested_authorities: Value for `requested_authorities` used by `approval_matches_skill`. Expected type: `list[str]`.
        risk_tier: Value for `risk_tier` used by `approval_matches_skill`. Expected type: `str`.
        required_approval_class: Value for `required_approval_class` used by `approval_matches_skill`. Expected type: `str`.

    Returns:
        bool: Result produced by `approval_matches_skill`.
    """
    if normalize_approval_record_status(approval.get("status", "approved")) != "approved":
        return False
    if not _valid_at_or_open(str(approval.get("valid_from", "")), upper_bound=False):
        return False
    if not _valid_at_or_open(str(approval.get("valid_until", "")), upper_bound=True):
        return False
    subject_titles = set(_string_list(approval.get("subject_titles", [])))
    if collapse_ws(skill_title) not in subject_titles:
        return False
    subject_kinds = [normalize_skill_kind(item) for item in _string_list(approval.get("subject_kinds", []))]
    if subject_kinds and normalize_skill_kind(kind) not in subject_kinds:
        return False
    approved_authorities = normalize_skill_authorities(approval.get("approved_authorities", []))
    if approved_authorities and set(requested_authorities) - set(approved_authorities):
        return False
    approved_risk_tiers = [normalize_skill_risk_tier(item) for item in _string_list(approval.get("approved_risk_tiers", []))]
    if approved_risk_tiers and normalize_skill_risk_tier(risk_tier) not in approved_risk_tiers:
        return False
    approval_class = normalize_skill_approval_class(approval.get("approval_class", "automatic"))
    approval_order = {
        "automatic": 0,
        "operator_approved": 1,
        "multi_party_approved": 2,
        "organization_approved": 3,
        "emergency_approved": 4,
        "prohibited": 5,
    }
    return approval_order[approval_class] >= approval_order[normalize_skill_approval_class(required_approval_class)]


def matching_approval_artifacts(
    approval_artifacts: list[ArtifactContentView] | None,
    *,
    skill_title: str,
    kind: str,
    requested_authorities: list[str],
    risk_tier: str,
    required_approval_class: str,
) -> list[ArtifactContentView]:
    """
    High Level Purpose:
        In circumstances like governed admission under explicit approval requirements, helps with collecting the installed approval artifacts that currently satisfy the requested skill.

    Reference to Theory:
        Supports open governance section 13 by turning approval records into explicit governed evidence rather than informal operator memory.

    Example Input Output:
        Input: `matching_approval_artifacts(approval_artifacts=[Artifact(id='artifact-skill-approval', title='Operator Approval', artifact_type='knowledge', representation='yaml')], skill_title='Open Browser URL', kind='ability', requested_authorities=['execute'], risk_tier='tier3_sensitive', required_approval_class='operator_approved')`
        Output: [Artifact(id='artifact-skill-approval', title='Operator Approval', artifact_type='knowledge', representation='yaml')]

    Args:
        approval_artifacts: Value for `approval_artifacts` used by `matching_approval_artifacts`. Expected type: `list[Artifact] | None`.
        skill_title: Value for `skill_title` used by `matching_approval_artifacts`. Expected type: `str`.
        kind: Value for `kind` used by `matching_approval_artifacts`. Expected type: `str`.
        requested_authorities: Value for `requested_authorities` used by `matching_approval_artifacts`. Expected type: `list[str]`.
        risk_tier: Value for `risk_tier` used by `matching_approval_artifacts`. Expected type: `str`.
        required_approval_class: Value for `required_approval_class` used by `matching_approval_artifacts`. Expected type: `str`.

    Returns:
        list[Artifact]: Result produced by `matching_approval_artifacts`.
    """
    matches: list[ArtifactContentView] = []
    for artifact in approval_artifacts or []:
        approval = artifact_skill_approval(artifact)
        if not approval:
            continue
        if approval_matches_skill(
            approval,
            skill_title=skill_title,
            kind=kind,
            requested_authorities=requested_authorities,
            risk_tier=risk_tier,
            required_approval_class=required_approval_class,
        ):
            matches.append(artifact)
    return matches
