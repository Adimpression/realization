# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from workstation.subject.core.learning_context_paths import decision_review_paths
from realized_core_semantics.semantic_text import collapse_ws


DECISION_POLICY_SCHEMA_VERSION = "decision_review_policy.v1"
DECISION_POLICY_PROFILE_KIND_ORDER: tuple[str, ...] = (
    "conservative",
    "balanced",
    "permissive",
)
VALID_DECISION_POLICY_PROFILE_KINDS = frozenset(DECISION_POLICY_PROFILE_KIND_ORDER)
DECISION_POLICY_PROFILE_RULES: dict[str, tuple[str, ...]] = {
    "conservative": (
        "prefer_executable_over_merely_valid",
        "reject_unresolved_critical_dependencies",
        "penalize_active_high_friction_boundaries",
        "penalize_coordination_heavy_transitions",
        "prefer_shorter_reachable_paths",
        "prefer_lower_residual_risk",
        "require_source_support_above_minimum_threshold",
    ),
    "balanced": (
        "prefer_executable_over_merely_valid",
        "reject_unresolved_critical_dependencies",
        "penalize_active_high_friction_boundaries",
        "prefer_shorter_reachable_paths",
        "prefer_lower_residual_risk",
    ),
    "permissive": (
        "prefer_executable_over_merely_valid",
        "prefer_shorter_reachable_paths",
        "prefer_lower_residual_risk",
    ),
}
DEFAULT_DECISION_POLICY_RULES: tuple[str, ...] = DECISION_POLICY_PROFILE_RULES["conservative"]


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _normalized_profile_kind(value: Any) -> str:
    normalized = collapse_ws(str(value)).lower().replace(" ", "_")
    return normalized if normalized in VALID_DECISION_POLICY_PROFILE_KINDS else "conservative"


def stable_decision_policy_profile_id(*, decision_frame_id: str, profile_kind: str) -> str:
    rendered = f"{collapse_ws(decision_frame_id)}::{_normalized_profile_kind(profile_kind)}"
    return f"decpol_{hashlib.sha256(rendered.encode('utf-8')).hexdigest()[:10]}"


@dataclass(frozen=True)
class DecisionPolicyProfile:
    policy_profile_id: str
    decision_frame_id: str
    profile_kind: str = "conservative"
    rule_ids: tuple[str, ...] = DEFAULT_DECISION_POLICY_RULES
    status: str = "active"
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = DECISION_POLICY_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_profile_id": self.policy_profile_id,
            "decision_frame_id": self.decision_frame_id,
            "profile_kind": self.profile_kind,
            "rule_ids": list(self.rule_ids),
            "status": self.status,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "updated_at_epoch_ms": self.updated_at_epoch_ms,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DecisionPolicyProfile":
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        profile_kind = _normalized_profile_kind(payload.get("profile_kind", "conservative"))
        rule_ids = tuple(
            collapse_ws(str(item))
            for item in payload.get("rule_ids", DECISION_POLICY_PROFILE_RULES[profile_kind])
            if collapse_ws(str(item))
        ) or DECISION_POLICY_PROFILE_RULES[profile_kind]
        return cls(
            policy_profile_id=collapse_ws(str(payload.get("policy_profile_id", ""))),
            decision_frame_id=collapse_ws(str(payload.get("decision_frame_id", ""))),
            profile_kind=profile_kind,
            rule_ids=rule_ids,
            status=collapse_ws(str(payload.get("status", "active"))) or "active",
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            metadata={str(key): value for key, value in metadata.items()},
            schema_version=collapse_ws(str(payload.get("schema_version", DECISION_POLICY_SCHEMA_VERSION))) or DECISION_POLICY_SCHEMA_VERSION,
        )


def default_decision_policy_profile(
    *,
    decision_frame_id: str,
    build_epoch_ms: int = 0,
    profile_kind: str = "conservative",
) -> DecisionPolicyProfile:
    normalized_kind = _normalized_profile_kind(profile_kind)
    normalized_frame_id = collapse_ws(decision_frame_id)
    return DecisionPolicyProfile(
        policy_profile_id=stable_decision_policy_profile_id(
            decision_frame_id=normalized_frame_id,
            profile_kind=normalized_kind,
        ),
        decision_frame_id=normalized_frame_id,
        profile_kind=normalized_kind,
        rule_ids=DECISION_POLICY_PROFILE_RULES[normalized_kind],
        status="active",
        created_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
    )


def next_decision_policy_profile_kind(current_kind: str) -> str:
    normalized_kind = _normalized_profile_kind(current_kind)
    current_index = DECISION_POLICY_PROFILE_KIND_ORDER.index(normalized_kind)
    return DECISION_POLICY_PROFILE_KIND_ORDER[(current_index + 1) % len(DECISION_POLICY_PROFILE_KIND_ORDER)]


def decision_policy_profile_path(root_path: Path, subject_id: str) -> Path:
    return decision_review_paths(root_path, subject_id)["root"] / "policy.json"


def persist_decision_policy_profile(
    root_path: Path,
    subject_id: str,
    profile: DecisionPolicyProfile,
) -> Path:
    target = decision_policy_profile_path(root_path, subject_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = DecisionPolicyProfile.from_dict(profile.to_dict())
    target.write_text(json.dumps(normalized.to_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def load_decision_policy_profile(root_path: Path, subject_id: str) -> DecisionPolicyProfile:
    target = decision_policy_profile_path(root_path, subject_id)
    if not target.is_file():
        return DecisionPolicyProfile(
            policy_profile_id="",
            decision_frame_id="",
            profile_kind="conservative",
            rule_ids=(),
            status="draft",
        )
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return DecisionPolicyProfile(
            policy_profile_id="",
            decision_frame_id="",
            profile_kind="conservative",
            rule_ids=(),
            status="draft",
        )
    return DecisionPolicyProfile.from_dict(payload if isinstance(payload, dict) else {})
