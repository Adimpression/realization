# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from applied_theory_primitives import utc_now
from artifact_contracts import ArtifactContentView
from semantic_text import collapse_ws

SKILL_REVIEW_STATUSES = (
    "pending_review",
    "reviewed",
    "review_rejected",
)
SKILL_INSTALLATION_STATUSES = (
    "installed",
    "blocked",
)
SKILL_ACTIVATION_STATUSES = (
    "active",
    "inactive",
)
SKILL_TRUST_STATUSES = (
    "trusted",
    "restricted",
    "suspended",
    "revoked",
)
SKILL_QUARANTINE_STATUSES = (
    "clear",
    "quarantined",
)


def _lifecycle_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def normalize_skill_review_status(value: Any, *, default: str = "pending_review") -> str:
    """
    High Level Purpose:
        In circumstances like governed skill import, export, and invocation checks, helps with normalizing review status into one explicit lifecycle ladder.

    Reference to Theory:
        Supports open governance by making review state machine-readable instead of implicit in operator convention.

    Example Input Output:
        Input: `normalize_skill_review_status(value='reviewed')`
        Output: 'reviewed'

    Args:
        value: Value for `value` used by `normalize_skill_review_status`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_review_status`. Expected type: `str`. Defaults to `'pending_review'`.

    Returns:
        str: Result produced by `normalize_skill_review_status`.
    """
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_REVIEW_STATUSES:
        return normalized
    return default


def normalize_skill_installation_status(value: Any, *, default: str = "installed") -> str:
    """
    High Level Purpose:
        In circumstances like governed skill lifecycle persistence, helps with normalizing installation state into one explicit lifecycle ladder.

    Reference to Theory:
        Supports open governance section 9 by separating installation state from admission and invocation.

    Example Input Output:
        Input: `normalize_skill_installation_status(value='installed')`
        Output: 'installed'

    Args:
        value: Value for `value` used by `normalize_skill_installation_status`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_installation_status`. Expected type: `str`. Defaults to `'installed'`.

    Returns:
        str: Result produced by `normalize_skill_installation_status`.
    """
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_INSTALLATION_STATUSES:
        return normalized
    return default


def normalize_skill_activation_status(value: Any, *, default: str = "active") -> str:
    """
    High Level Purpose:
        In circumstances like invocation-time governance, helps with normalizing activation state into one explicit lifecycle ladder.

    Reference to Theory:
        Supports open governance section 9 by making activation a distinct current-use gate rather than assuming admitted means runnable.

    Example Input Output:
        Input: `normalize_skill_activation_status(value='inactive')`
        Output: 'inactive'

    Args:
        value: Value for `value` used by `normalize_skill_activation_status`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_activation_status`. Expected type: `str`. Defaults to `'active'`.

    Returns:
        str: Result produced by `normalize_skill_activation_status`.
    """
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_ACTIVATION_STATUSES:
        return normalized
    return default


def normalize_skill_trust_status(value: Any, *, default: str = "trusted") -> str:
    """
    High Level Purpose:
        In circumstances like invocation-time governance and incident response, helps with normalizing trust state into one explicit lifecycle ladder.

    Reference to Theory:
        Supports open governance by making current trust state inspectable instead of leaving suspension or revocation implicit.

    Example Input Output:
        Input: `normalize_skill_trust_status(value='suspended')`
        Output: 'suspended'

    Args:
        value: Value for `value` used by `normalize_skill_trust_status`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_trust_status`. Expected type: `str`. Defaults to `'trusted'`.

    Returns:
        str: Result produced by `normalize_skill_trust_status`.
    """
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_TRUST_STATUSES:
        return normalized
    return default


def normalize_skill_quarantine_status(value: Any, *, default: str = "clear") -> str:
    """
    High Level Purpose:
        In circumstances like invocation-time governance and incident response, helps with normalizing quarantine state into one explicit lifecycle ladder.

    Reference to Theory:
        Supports open governance by making quarantine visible and enforceable before any effect occurs.

    Example Input Output:
        Input: `normalize_skill_quarantine_status(value='quarantined')`
        Output: 'quarantined'

    Args:
        value: Value for `value` used by `normalize_skill_quarantine_status`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_quarantine_status`. Expected type: `str`. Defaults to `'clear'`.

    Returns:
        str: Result produced by `normalize_skill_quarantine_status`.
    """
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_QUARANTINE_STATUSES:
        return normalized
    return default


def synthesized_skill_lifecycle(
    *,
    admission_status: str = "",
    policy_record: bool = False,
    default_updated_at: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like exporting older governed skills or filling lifecycle gaps during import, helps with synthesizing one conservative lifecycle state from the current admission result.

    Reference to Theory:
        Supports open governance section 9 by making lifecycle state explicit even when older artifacts only carried admission.

    Example Input Output:
        Input: `synthesized_skill_lifecycle(admission_status='admitted', policy_record=False, default_updated_at='2026-03-31T12:00:00+00:00')`
        Output: {'review_status': 'pending_review', 'admission_status': 'admitted', 'installation_status': 'installed', 'activation_status': 'active', 'trust_status': 'trusted', 'quarantine_status': 'clear', 'updated_at': '2026-03-31T12:00:00+00:00'}

    Args:
        admission_status: Value for `admission_status` used by `synthesized_skill_lifecycle`. Expected type: `str`. Defaults to `''`.
        policy_record: Value for `policy_record` used by `synthesized_skill_lifecycle`. Expected type: `bool`. Defaults to `False`.
        default_updated_at: Value for `default_updated_at` used by `synthesized_skill_lifecycle`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `synthesized_skill_lifecycle`.
    """
    normalized_admission = collapse_ws(admission_status).lower()
    if policy_record and not normalized_admission:
        normalized_admission = "admitted"
    if normalized_admission == "admitted":
        installation_status = "installed"
        activation_status = "active"
        trust_status = "trusted"
        status_reason = "Skill is installed, active, and trusted for invocation."
    elif normalized_admission == "held":
        installation_status = "installed"
        activation_status = "inactive"
        trust_status = "restricted"
        status_reason = "Skill remains installed but inactive while admission is held."
    elif normalized_admission == "rejected":
        installation_status = "blocked"
        activation_status = "inactive"
        trust_status = "restricted"
        status_reason = "Skill is blocked because admission was rejected."
    else:
        installation_status = "installed"
        activation_status = "inactive"
        trust_status = "restricted"
        status_reason = "Skill lifecycle was synthesized without a current admitted invocation state."
    return {
        "review_status": "pending_review",
        "admission_status": normalized_admission,
        "installation_status": installation_status,
        "activation_status": activation_status,
        "trust_status": trust_status,
        "quarantine_status": "clear",
        "status_reason": status_reason,
        "updated_at": collapse_ws(default_updated_at) or utc_now(),
    }


def skill_lifecycle_from_payload(
    payload: Mapping[str, Any] | None = None,
    *,
    admission_status: str = "",
    policy_record: bool = False,
    default_updated_at: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing or exporting governed skills, helps with normalizing one lifecycle block and reconciling it with the current admission result.

    Reference to Theory:
        Supports open governance section 9 by making lifecycle state a first-class normalized record rather than a loose optional blob.

    Example Input Output:
        Input: `skill_lifecycle_from_payload(payload={'lifecycle': {'activation_status': 'inactive'}}, admission_status='admitted', policy_record=False, default_updated_at='2026-03-31T12:00:00+00:00')`
        Output: {'review_status': 'pending_review', 'admission_status': 'admitted', 'installation_status': 'installed', 'activation_status': 'inactive', 'trust_status': 'trusted', 'quarantine_status': 'clear', 'updated_at': '2026-03-31T12:00:00+00:00'}

    Args:
        payload: Value for `payload` used by `skill_lifecycle_from_payload`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        admission_status: Value for `admission_status` used by `skill_lifecycle_from_payload`. Expected type: `str`. Defaults to `''`.
        policy_record: Value for `policy_record` used by `skill_lifecycle_from_payload`. Expected type: `bool`. Defaults to `False`.
        default_updated_at: Value for `default_updated_at` used by `skill_lifecycle_from_payload`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `skill_lifecycle_from_payload`.
    """
    raw_payload = _lifecycle_mapping(payload)
    raw_lifecycle = _lifecycle_mapping(raw_payload.get("lifecycle", raw_payload))
    defaults = synthesized_skill_lifecycle(
        admission_status=admission_status or raw_lifecycle.get("admission_status", ""),
        policy_record=policy_record,
        default_updated_at=default_updated_at or raw_lifecycle.get("updated_at", ""),
    )
    return {
        "review_status": normalize_skill_review_status(
            raw_lifecycle.get("review_status", defaults["review_status"])
        ),
        "admission_status": collapse_ws(admission_status or raw_lifecycle.get("admission_status", "")) or defaults["admission_status"],
        "installation_status": normalize_skill_installation_status(
            raw_lifecycle.get("installation_status", defaults["installation_status"])
        ),
        "activation_status": normalize_skill_activation_status(
            raw_lifecycle.get("activation_status", defaults["activation_status"])
        ),
        "trust_status": normalize_skill_trust_status(
            raw_lifecycle.get("trust_status", defaults["trust_status"])
        ),
        "quarantine_status": normalize_skill_quarantine_status(
            raw_lifecycle.get("quarantine_status", defaults["quarantine_status"])
        ),
        "status_reason": collapse_ws(str(raw_lifecycle.get("status_reason", defaults["status_reason"]))),
        "updated_at": collapse_ws(str(raw_lifecycle.get("updated_at", defaults["updated_at"]))) or defaults["updated_at"],
    }


def artifact_skill_lifecycle(artifact: ArtifactContentView) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed export and invocation-time lifecycle checks, helps with reading the stored lifecycle state or synthesizing a conservative default from current artifact content.

    Reference to Theory:
        Supports open governance section 9 by ensuring lifecycle remains explicit even for earlier governed artifacts that only stored admission.

    Example Input Output:
        Input: `artifact_skill_lifecycle(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: {'review_status': 'pending_review', 'admission_status': 'admitted', 'installation_status': 'installed', 'activation_status': 'active', 'trust_status': 'trusted', 'quarantine_status': 'clear'}

    Args:
        artifact: Value for `artifact` used by `artifact_skill_lifecycle`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_skill_lifecycle`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    raw_lifecycle = _lifecycle_mapping(content.get("skill_lifecycle", {}))
    raw_admission = _lifecycle_mapping(content.get("skill_admission", {}))
    if not raw_lifecycle and not raw_admission and not content.get("skill_policy"):
        return {}
    return skill_lifecycle_from_payload(
        raw_lifecycle,
        admission_status=str(raw_admission.get("status", raw_lifecycle.get("admission_status", ""))),
        policy_record=bool(content.get("skill_policy")),
        default_updated_at=str(
            raw_lifecycle.get("updated_at")
            or raw_admission.get("evaluated_at")
            or content.get("created_at")
            or ""
        ),
    )


def artifact_effective_skill_lifecycle(
    artifact: ArtifactContentView,
    *,
    current_admission_status: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like invocation-time governance under current approval or policy state, helps with deriving the lifecycle that should govern current use without letting a merely synthesized stale lifecycle override a newer admission result.

    Reference to Theory:
        Supports open governance section 9 by allowing activation and trust checks to follow current governance state when no explicit lifecycle override has been persisted yet.

    Example Input Output:
        Input: `artifact_effective_skill_lifecycle(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'), current_admission_status='admitted')`
        Output: {'review_status': 'pending_review', 'admission_status': 'admitted', 'installation_status': 'installed', 'activation_status': 'active', 'trust_status': 'trusted', 'quarantine_status': 'clear'}

    Args:
        artifact: Value for `artifact` used by `artifact_effective_skill_lifecycle`. Expected type: `Artifact`.
        current_admission_status: Value for `current_admission_status` used by `artifact_effective_skill_lifecycle`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `artifact_effective_skill_lifecycle`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    raw_lifecycle = _lifecycle_mapping(content.get("skill_lifecycle", {}))
    if raw_lifecycle:
        return artifact_skill_lifecycle(artifact)
    raw_admission = _lifecycle_mapping(content.get("skill_admission", {}))
    if not raw_admission and not current_admission_status and not content.get("skill_policy"):
        return {}
    admission_status = (
        collapse_ws(current_admission_status)
        or collapse_ws(str(raw_admission.get("status", "")))
    )
    return synthesized_skill_lifecycle(
        admission_status=admission_status,
        policy_record=bool(content.get("skill_policy")),
        default_updated_at=str(
            raw_admission.get("evaluated_at")
            or content.get("created_at")
            or ""
        ),
    )


def skill_lifecycle_allows_invocation(lifecycle: Mapping[str, Any] | None) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like runtime host mediation and executor gating, helps with deciding whether the current lifecycle state permits invocation.

    Reference to Theory:
        Supports open governance sections 9 and 10 by making activation, trust, and quarantine real invocation-time gates instead of passive metadata.

    Example Input Output:
        Input: `skill_lifecycle_allows_invocation(lifecycle={'activation_status': 'inactive', 'trust_status': 'trusted', 'quarantine_status': 'clear', 'installation_status': 'installed'})`
        Output: (False, 'Governed skill activation status is inactive.')

    Args:
        lifecycle: Value for `lifecycle` used by `skill_lifecycle_allows_invocation`. Expected type: `Mapping[str, Any] | None`.

    Returns:
        tuple[bool, str]: Result produced by `skill_lifecycle_allows_invocation`.
    """
    normalized = _lifecycle_mapping(lifecycle)
    if not normalized:
        return True, ""
    quarantine_status = normalize_skill_quarantine_status(normalized.get("quarantine_status", "clear"))
    if quarantine_status == "quarantined":
        return False, "Governed skill is quarantined and cannot be invoked."
    trust_status = normalize_skill_trust_status(normalized.get("trust_status", "trusted"))
    if trust_status in {"restricted", "suspended", "revoked"}:
        return False, f"Governed skill trust status is {trust_status}."
    installation_status = normalize_skill_installation_status(
        normalized.get("installation_status", "installed")
    )
    if installation_status != "installed":
        return False, f"Governed skill installation status is {installation_status}."
    activation_status = normalize_skill_activation_status(
        normalized.get("activation_status", "active")
    )
    if activation_status != "active":
        return False, f"Governed skill activation status is {activation_status}."
    return True, ""
