"""Governed skill-declaration and policy normalization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_skill_semantics.declaration import (
    SKILL_SCHEMA_VERSION_V1,
    SKILL_SCHEMA_VERSION_V2,
    normalize_skill_schema_version,
)
from realized_skill_semantics.execution import normalize_executor_framework_name

from ._normalization import collapse_ws
from .vocabulary import (
    SKILL_AUTHORITIES,
    normalize_skill_approval_class,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)


SKILL_DECLARATION_REQUIRED_FIELDS = (
    "intent",
    "inputs",
    "outputs",
    "authorities_requested",
    "data_classes_touched",
    "side_effects",
    "persistence_behavior",
    "invocation_rights",
    "composition_rights",
    "escalation_rights",
    "approval_requirements",
    "risk_tier",
)
SKILL_AUTHORITY_BOUND_FIELDS = (
    "scope",
    "target",
    "context",
    "duration",
    "triggering_conditions",
    "approval_class",
)

_DECLARATION_COLLECTION_FIELDS = {
    "inputs",
    "outputs",
    "authorities_requested",
    "data_classes_touched",
    "side_effects",
    "invocation_rights",
    "composition_rights",
    "escalation_rights",
    "approval_requirements",
}


def _field_declared(
    declaration: Mapping[str, Any],
    payload: Mapping[str, Any],
    field_name: str,
) -> bool:
    if field_name in declaration:
        return True
    return field_name in payload


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [collapse_ws(str(item)) for item in value if collapse_ws(str(item))]
    return [collapse_ws(str(value))] if collapse_ws(str(value)) else []


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, str] = {}
    for key, raw in value.items():
        key_text = collapse_ws(str(key))
        value_text = collapse_ws(str(raw))
        if not key_text or not value_text:
            continue
        normalized[key_text] = value_text
    return normalized


def skill_declaration_from_payload(
    payload: Mapping[str, Any],
    *,
    kind: str,
    fallback_inputs: Mapping[str, Any] | None = None,
    fallback_outputs: Mapping[str, Any] | None = None,
    executor_framework: str = "",
) -> dict[str, Any]:
    """Normalize and validate one governed v2 skill declaration."""
    schema = normalize_skill_schema_version(
        payload.get("schema", SKILL_SCHEMA_VERSION_V1)
    )
    if schema != SKILL_SCHEMA_VERSION_V2 or kind in {
        "policy",
        "approval",
        "revocation",
        "incident",
    }:
        return {}

    declaration = (
        dict(payload.get("declaration", {}))
        if isinstance(payload.get("declaration", {}), Mapping)
        else {}
    )
    normalized_inputs = _string_mapping(
        declaration.get("inputs", fallback_inputs or {})
    )
    normalized_outputs = _string_mapping(
        declaration.get("outputs", fallback_outputs or {})
    )
    authority_bounds_raw = (
        dict(declaration.get("authority_bounds", {}))
        if isinstance(declaration.get("authority_bounds", {}), Mapping)
        else {}
    )
    authority_bounds: dict[str, dict[str, Any]] = {}
    for authority, raw_bounds in authority_bounds_raw.items():
        authority_name = (
            collapse_ws(str(authority))
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )
        if authority_name not in SKILL_AUTHORITIES or not isinstance(
            raw_bounds, Mapping
        ):
            continue
        triggering_conditions = _string_list(
            raw_bounds.get("triggering_conditions", [])
        )
        authority_bounds[authority_name] = {
            "scope": collapse_ws(str(raw_bounds.get("scope", ""))),
            "target": collapse_ws(str(raw_bounds.get("target", ""))),
            "context": collapse_ws(str(raw_bounds.get("context", ""))),
            "duration": collapse_ws(str(raw_bounds.get("duration", ""))),
            "triggering_conditions": triggering_conditions,
            "approval_class": normalize_skill_approval_class(
                raw_bounds.get("approval_class", "automatic")
            ),
        }

    normalized = {
        "intent": collapse_ws(
            str(declaration.get("intent", payload.get("intent", "")))
        ),
        "inputs": normalized_inputs,
        "outputs": normalized_outputs,
        "authorities_requested": normalize_skill_authorities(
            declaration.get(
                "authorities_requested",
                payload.get("authorities_requested", []),
            )
        ),
        "authority_bounds": authority_bounds,
        "data_classes_touched": _string_list(
            declaration.get(
                "data_classes_touched",
                payload.get("data_classes_touched", []),
            )
        ),
        "side_effects": _string_list(
            declaration.get("side_effects", payload.get("side_effects", []))
        ),
        "persistence_behavior": collapse_ws(
            str(
                declaration.get(
                    "persistence_behavior",
                    payload.get("persistence_behavior", ""),
                )
            )
        ),
        "invocation_rights": _string_list(
            declaration.get(
                "invocation_rights",
                payload.get("invocation_rights", []),
            )
        ),
        "composition_rights": _string_list(
            declaration.get(
                "composition_rights",
                payload.get("composition_rights", []),
            )
        ),
        "escalation_rights": _string_list(
            declaration.get(
                "escalation_rights",
                payload.get("escalation_rights", []),
            )
        ),
        "approval_requirements": [
            normalize_skill_approval_class(item)
            for item in _string_list(
                declaration.get(
                    "approval_requirements",
                    payload.get("approval_requirements", []),
                )
            )
        ],
        "risk_tier": normalize_skill_risk_tier(
            declaration.get(
                "risk_tier",
                payload.get("risk_tier", "tier1_bounded_transform"),
            )
        ),
    }
    if executor_framework:
        normalized["executor_framework"] = normalize_executor_framework_name(
            executor_framework
        )

    missing_fields: list[str] = []
    for field_name in SKILL_DECLARATION_REQUIRED_FIELDS:
        if field_name in _DECLARATION_COLLECTION_FIELDS:
            if not _field_declared(declaration, payload, field_name):
                missing_fields.append(field_name)
            continue
        if normalized.get(field_name) in (None, "", [], {}):
            missing_fields.append(field_name)
    if missing_fields:
        raise ValueError(
            "Skill declaration v2 requires declared fields: "
            + ", ".join(missing_fields)
        )
    missing_bounds = [
        authority
        for authority in normalized["authorities_requested"]
        if authority not in normalized["authority_bounds"]
    ]
    if missing_bounds:
        raise ValueError(
            "Skill declaration v2 requires authority_bounds for every "
            "requested authority: "
            + ", ".join(missing_bounds)
        )
    for authority, bounds in normalized["authority_bounds"].items():
        missing_bound_fields = [
            field_name
            for field_name in SKILL_AUTHORITY_BOUND_FIELDS
            if bounds.get(field_name) in (None, "", [], {})
        ]
        if missing_bound_fields:
            raise ValueError(
                f"Skill declaration v2 authority {authority!r} is missing bounds: "
                + ", ".join(missing_bound_fields)
            )
    return normalized


def skill_policy_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize and validate one governed v2 admission policy."""
    schema = normalize_skill_schema_version(
        payload.get("schema", SKILL_SCHEMA_VERSION_V1)
    )
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    if schema != SKILL_SCHEMA_VERSION_V2 or kind != "policy":
        return {}
    policy = (
        dict(payload.get("policy", {}))
        if isinstance(payload.get("policy", {}), Mapping)
        else {}
    )
    normalized_required_approval = {}
    raw_required = (
        dict(policy.get("required_approval_for_risk_tiers", {}))
        if isinstance(policy.get("required_approval_for_risk_tiers", {}), Mapping)
        else {}
    )
    for tier, approval in raw_required.items():
        normalized_required_approval[normalize_skill_risk_tier(tier)] = (
            normalize_skill_approval_class(approval)
        )
    normalized = {
        "intent": collapse_ws(str(policy.get("intent", ""))),
        "target_kinds": [
            normalize_skill_kind(item)
            for item in _string_list(
                policy.get("target_kinds", ["knowledge", "ability"])
            )
        ],
        "max_risk_tier": normalize_skill_risk_tier(
            policy.get("max_risk_tier", "tier1_bounded_transform")
        ),
        "allowed_authorities": normalize_skill_authorities(
            policy.get("allowed_authorities", [])
        ),
        "denied_authorities": normalize_skill_authorities(
            policy.get("denied_authorities", [])
        ),
        "allowed_executors": [
            normalize_executor_framework_name(item)
            for item in _string_list(policy.get("allowed_executors", []))
            if normalize_executor_framework_name(item)
        ],
        "allowed_data_classes": _string_list(
            policy.get("allowed_data_classes", [])
        ),
        "denied_side_effects": _string_list(
            policy.get("denied_side_effects", [])
        ),
        "required_approval_for_risk_tiers": normalized_required_approval,
    }
    missing_fields = [
        field_name
        for field_name in ("intent", "target_kinds", "max_risk_tier")
        if normalized.get(field_name) in (None, "", [], {})
    ]
    if missing_fields:
        raise ValueError(
            "Policy artifact v2 requires non-empty fields: "
            + ", ".join(missing_fields)
        )
    return normalized


def policy_answer_summary(policy: Mapping[str, Any]) -> str:
    """Render one normalized admission policy as a reviewable summary."""
    intent = collapse_ws(str(policy.get("intent", "")))
    target_kinds = ", ".join(_string_list(policy.get("target_kinds", [])))
    max_risk_tier = normalize_skill_risk_tier(
        policy.get("max_risk_tier", "tier1_bounded_transform")
    )
    allowed_authorities = ", ".join(
        normalize_skill_authorities(policy.get("allowed_authorities", []))
    )
    denied_authorities = ", ".join(
        normalize_skill_authorities(policy.get("denied_authorities", []))
    )
    segments = [
        f"Policy intent: {intent}.",
        f"Targets: {target_kinds}.",
        f"Max risk tier: {max_risk_tier}.",
        f"Allowed authorities: {allowed_authorities}.",
    ]
    if denied_authorities:
        segments.append(f"Denied authorities: {denied_authorities}.")
    return " ".join(segment for segment in segments if collapse_ws(segment))


__all__ = [
    "SKILL_AUTHORITY_BOUND_FIELDS",
    "SKILL_DECLARATION_REQUIRED_FIELDS",
    "policy_answer_summary",
    "skill_declaration_from_payload",
    "skill_policy_from_payload",
]
