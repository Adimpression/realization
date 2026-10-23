"""Stable application identities for recoverable conversation stages."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from typing import Any


def canonical_payload_digest(value: Mapping[str, Any]) -> str:
    """Return a stable digest for one JSON-compatible object."""

    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable_contribution_id(session_id: str, idempotency_key: str) -> str:
    return _stable_id("contribution", (session_id, idempotency_key))


def stable_planning_attempt_id(
    contribution_id: str,
    planning_attempt_key: str,
) -> str:
    return _stable_id("planning", (contribution_id, planning_attempt_key))


def stable_normalized_request_id(
    request_payload: Mapping[str, Any],
) -> str:
    return f"request_{canonical_payload_digest(request_payload)}"


def stable_result_id(
    normalized_request_id: str,
    execution_attempt_id: str,
) -> str:
    return _stable_id(
        "result",
        (normalized_request_id, execution_attempt_id),
    )


def stable_rendering_attempt_id(
    result_id: str,
    rendering_attempt_key: str,
) -> str:
    return _stable_id("rendering", (result_id, rendering_attempt_key))


def stable_receipt_id(
    stage: str,
    correlation_ids: Mapping[str, str],
    receipt_key: str,
) -> str:
    return _stable_id(
        "receipt",
        (
            stage,
            canonical_payload_digest(dict(correlation_ids)),
            receipt_key,
        ),
    )


def stable_recovery_decision_id(
    contribution_id: str,
    stage: str,
    action: str,
    decision_key: str = "primary",
) -> str:
    return _stable_id(
        "recovery",
        (contribution_id, stage, action, decision_key),
    )


def _stable_id(prefix: str, parts: Sequence[str]) -> str:
    normalized = [str(part).strip() for part in parts]
    if not prefix.strip() or any(not part for part in normalized):
        raise ValueError("Stable identity inputs must be non-empty.")
    digest = canonical_payload_digest(
        {"identity_kind": prefix, "parts": normalized}
    )
    return f"{prefix}_{digest}"


__all__ = [
    "canonical_payload_digest",
    "stable_contribution_id",
    "stable_normalized_request_id",
    "stable_planning_attempt_id",
    "stable_receipt_id",
    "stable_recovery_decision_id",
    "stable_rendering_attempt_id",
    "stable_result_id",
]
