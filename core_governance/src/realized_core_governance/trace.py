"""Canonical per-effect evidence receipts over already-supplied trace values."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from realized_core_semantics.values import json_safe

from ._normalization import collapse_ws


EFFECT_TRACE_RECEIPT_SCHEMA_VERSION = "bssc_effect_receipt.v1"

_VOLATILE_EFFECT_EVIDENCE_FIELDS = {
    "id",
    "issued_at",
    "created_at",
    "evaluated_at",
    "updated_at",
}


def _canonical_admission_status(value: Any) -> str:
    normalized = collapse_ws(str(value)).lower()
    if normalized in {"legacy_implicit_admit", "admitted"}:
        return "admitted"
    return normalized


def canonical_effect_trace_receipt_payload(value: Any) -> Any:
    """Remove volatile fields and normalize supplied effect evidence."""
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            key_text = collapse_ws(str(key))
            if key_text in _VOLATILE_EFFECT_EVIDENCE_FIELDS:
                continue
            current = value.get(key)
            if key_text == "status":
                current = _canonical_admission_status(current)
            normalized[key_text] = canonical_effect_trace_receipt_payload(current)
        return normalized
    if isinstance(value, list):
        return [canonical_effect_trace_receipt_payload(item) for item in value]
    if isinstance(value, tuple):
        return [canonical_effect_trace_receipt_payload(item) for item in value]
    return json_safe(value)


def effect_trace_receipt(kind: str, payload: Any) -> dict[str, Any]:
    """Return the versioned semantic receipt for supplied effect evidence."""
    canonical = canonical_effect_trace_receipt_payload(payload)
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
        "kind": collapse_ws(str(kind)),
        "digest": digest,
    }


def canonical_trace_answer(value: Any) -> str:
    """Project a supplied effect answer into its replay-comparable form."""
    if isinstance(value, str):
        return value.strip()
    if value in (None, "", [], {}):
        return ""
    try:
        return json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"))
    except Exception:
        return str(value).strip()


def _canonical_replay_admission_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"legacy_implicit_admit", "admitted"}:
        return "admitted"
    return normalized


def _canonical_replay_receipt_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            key_text = str(key).strip()
            if key_text in _VOLATILE_EFFECT_EVIDENCE_FIELDS:
                continue
            current = value.get(key)
            if key_text == "status":
                current = _canonical_replay_admission_status(current)
            normalized[key_text] = _canonical_replay_receipt_payload(current)
        return normalized
    if isinstance(value, list):
        return [_canonical_replay_receipt_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_canonical_replay_receipt_payload(item) for item in value]
    return json_safe(value)


def _replay_receipt_digest(payload: Any) -> str:
    canonical = _canonical_replay_receipt_payload(payload)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def _canonical_replay_policy_titles(values: Any) -> list[str]:
    titles: list[str] = []
    for item in values if isinstance(values, list) else []:
        title = str(item or "").strip()
        if not title:
            continue
        if title.startswith("Replay Policy Snapshot /"):
            continue
        if title not in titles:
            titles.append(title)
    return titles


def effect_trace_signature(trace: Mapping[str, Any] | None) -> dict[str, Any]:
    """Project supplied effect evidence into its constitutional replay signature."""
    payload = dict(trace) if isinstance(trace, Mapping) else {}
    request = dict(payload.get("request", {})) if isinstance(payload.get("request", {}), Mapping) else {}
    decision = dict(payload.get("decision", {})) if isinstance(payload.get("decision", {}), Mapping) else {}
    result = dict(payload.get("result", {})) if isinstance(payload.get("result", {}), Mapping) else {}
    admission = dict(payload.get("admission", {})) if isinstance(payload.get("admission", {}), Mapping) else {}
    lifecycle = dict(payload.get("lifecycle", {})) if isinstance(payload.get("lifecycle", {}), Mapping) else {}
    allowed = bool(decision.get("allowed", payload.get("allowed", False)))
    admission_status = _canonical_replay_admission_status(admission.get("status", ""))
    activation_status = str(lifecycle.get("activation_status", ""))
    trust_status = str(lifecycle.get("trust_status", ""))
    if allowed and admission_status == "admitted":
        activation_status = "active"
        trust_status = "trusted"
    semantic_receipts = {
        "request": _replay_receipt_digest(
            {
                "effect_kind": str(request.get("effect_kind", payload.get("effect_kind", ""))),
                "executor_framework": str(request.get("executor_framework", "")),
                "invocation_payload": request.get("invocation_payload", ""),
            }
        ),
        "declaration": _replay_receipt_digest(payload.get("declaration", {})),
        "policy": _replay_receipt_digest(
            {
                "policy_titles": _canonical_replay_policy_titles(admission.get("policy_titles", [])),
                "required_approval_class": str(admission.get("required_approval_class", "automatic")),
            }
        ),
        "approval": _replay_receipt_digest(
            {
                "approval_titles": [
                    str(item).strip()
                    for item in admission.get("approval_titles", [])
                    if str(item).strip()
                ],
                "required_approval_class": str(admission.get("required_approval_class", "automatic")),
            }
        ),
        "lifecycle": _replay_receipt_digest(
            {
                "activation_status": activation_status,
                "admission_status": admission_status,
                "installation_status": str(lifecycle.get("installation_status", "")),
                "quarantine_status": str(lifecycle.get("quarantine_status", "")),
                "review_status": str(lifecycle.get("review_status", "")),
                "trust_status": trust_status,
            }
        ),
        "grants": _replay_receipt_digest(
            [
                {
                    "authority": str(item.get("authority", "")),
                    "scope": str(item.get("scope", "")),
                    "target": str(item.get("target", "")),
                    "context": str(item.get("context", "")),
                    "duration": str(item.get("duration", "")),
                    "triggering_conditions": list(item.get("triggering_conditions", [])),
                    "approval_class": str(item.get("approval_class", "automatic")),
                    "risk_tier": str(item.get("risk_tier", "")),
                    "executor_framework": str(item.get("executor_framework", "")),
                    "effect_kind": str(item.get("effect_kind", "")),
                    "semantic_unit": str(item.get("semantic_unit", "")),
                    "data_classes_touched": list(item.get("data_classes_touched", [])),
                    "side_effects": list(item.get("side_effects", [])),
                    "policy_titles": _canonical_replay_policy_titles(item.get("policy_titles", [])),
                    "admission_status": _canonical_replay_admission_status(item.get("admission_status", "")),
                }
                for item in payload.get("grants", [])
                if isinstance(item, Mapping)
            ]
        ),
    }
    if isinstance(payload.get("realizer"), Mapping):
        semantic_receipts["realizer"] = _replay_receipt_digest(
            payload["realizer"]
        )
    return {
        "artifact_title": str(payload.get("artifact_title", "")),
        "effect_kind": str(request.get("effect_kind", payload.get("effect_kind", ""))),
        "required_authority": str(decision.get("required_authority", "")),
        "allowed": allowed,
        "executor_framework": str(request.get("executor_framework", "")),
        "admission_status": admission_status,
        "activation_status": activation_status,
        "trust_status": trust_status,
        "ok": bool(result.get("ok", False)),
        "exit_code": int(result.get("exit_code", 0) or 0),
        "answer": canonical_trace_answer(result.get("answer", "")),
        "receipt_digests": semantic_receipts,
    }


__all__ = [
    "EFFECT_TRACE_RECEIPT_SCHEMA_VERSION",
    "canonical_trace_answer",
    "canonical_effect_trace_receipt_payload",
    "effect_trace_signature",
    "effect_trace_receipt",
]
