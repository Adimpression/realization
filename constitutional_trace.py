# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from applied_theory_types import json_safe, utc_now
from host_abi import host_abi_version
from system_state import SystemState

CONSTITUTIONAL_TRACE_SCHEMA_VERSION = "bssc_constitutional_trace.v1"


_DECISION_FLOW_KINDS: set[str] = {
    "frontier_selection",
    "proposal_registered",
    "proposal_governance",
}


def controller_decision_flow_signature(state: SystemState) -> list[dict[str, Any]]:
    """
    Extract a stable, replay-oriented signature of the controller's *decision flow*.

    This is intentionally smaller and more stable than the full step log:
    it avoids timestamps and explanatory prose, and focuses on structural choices
    (frontier selection ordering + proposal governance events).
    """
    signatures: list[dict[str, Any]] = []

    def node_focus(node_id: str | None) -> str:
        if not node_id:
            return ""
        node = state.graph.nodes.get(str(node_id))
        return str(node.semantic_unit) if node is not None else ""

    for record in state.ledger:
        if record.kind not in _DECISION_FLOW_KINDS:
            continue
        entry: dict[str, Any] = {
            "kind": str(record.kind),
            "focus": node_focus(record.node_id),
        }
        if record.kind == "frontier_selection":
            order: list[str] = []
            for item in record.payload.get("candidate_order", []):
                candidate_id = str(item).strip()
                if not candidate_id:
                    continue
                order.append(node_focus(candidate_id) or candidate_id)
            entry["candidate_order"] = order
            entry["selected_focus"] = node_focus(record.node_id)
        elif record.kind == "proposal_registered":
            entry["proposal_type"] = str(record.payload.get("proposal_type", "")).strip()
            entry["source"] = str(record.payload.get("source", "")).strip()
            entry["governance_status"] = str(record.payload.get("governance_status", "")).strip()
        elif record.kind == "proposal_governance":
            entry["status"] = str(record.payload.get("status", "")).strip()
        entry["receipt_digest"] = _receipt_digest(entry)
        signatures.append(entry)
    return signatures


def llm_transcript_signature(state: SystemState) -> list[dict[str, Any]]:
    transcript = list(getattr(state, "llm_transcript", []) or [])
    signatures: list[dict[str, Any]] = []
    for item in transcript:
        if not isinstance(item, Mapping):
            continue
        signatures.append(
            {
                "proposal_type": str(item.get("proposal_type", "")).strip(),
                "mode": str(item.get("mode", "")).strip(),
                "request_digest": str(item.get("request_digest", "")).strip(),
                "response_digest": str(item.get("response_digest", "")).strip(),
            }
        )
    return signatures


def _canonical_admission_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"legacy_implicit_admit", "admitted"}:
        return "admitted"
    return normalized


def canonical_trace_answer(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like replay verification and constitutional trace comparison, helps with reducing a recorded answer surface into one stable comparable string.

    Reference to Theory:
        Supports replay-oriented governance by making final answers and effect answers comparable without depending on incidental Python representation differences.

    Example Input Output:
        Input: `canonical_trace_answer(value={'status': 'ok'})`
        Output: '{"status":"ok"}'

    Args:
        value: Value for `value` used by `canonical_trace_answer`. Expected type: `Any`.

    Returns:
        str: Result produced by `canonical_trace_answer`.
    """
    if isinstance(value, str):
        return value.strip()
    if value in (None, "", [], {}):
        return ""
    try:
        return json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"))
    except Exception:
        return str(value).strip()


def _canonical_receipt_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            key_text = str(key).strip()
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


def _receipt_digest(payload: Any) -> str:
    canonical = _canonical_receipt_payload(payload)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def _canonical_policy_titles(values: Any) -> list[str]:
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


def state_composition_chain(state: SystemState) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like constitutional bundle export, helps with projecting the governed semantic development into one durable ordered chain of node snapshots.

    Reference to Theory:
        Supports open governance trace and replay by preserving the semantically relevant reduction surface instead of only the final outcome.

    Example Input Output:
        Input: `state_composition_chain(state=SystemState.bootstrap(prompt='Say hi.'))`
        Output: [{'node_id': 'not-say-hi', 'semantic_unit': 'Say hi.', 'depth': 0, 'status': 'open'}]

    Args:
        state: Value for `state` used by `state_composition_chain`. Expected type: `SystemState`.

    Returns:
        list[dict[str, Any]]: Result produced by `state_composition_chain`.
    """
    snapshots: list[dict[str, Any]] = []
    for node in sorted(state.graph.nodes.values(), key=lambda item: (item.depth, item.semantic_unit.lower(), item.id)):
        snapshots.append(
            {
                "node_id": node.id,
                "semantic_unit": node.semantic_unit,
                "depth": int(node.depth),
                "role": str(node.role),
                "status": state.node_status(node.id).value,
                "certainty": str(state.certainty.get(node.id, "")),
                "blockers": list(state.blockers.get(node.id, [])),
            }
        )
    return snapshots


def _blocker_classes(values: Any) -> list[str]:
    classes: list[str] = []
    for item in values if isinstance(values, list) else []:
        text = str(item or "").strip()
        if not text:
            continue
        if ":" in text:
            label = text.split(":", 1)[0].strip()
        else:
            label = "dependency"
        if label and label not in classes:
            classes.append(label)
    return sorted(classes)


def composition_chain_signature(value: SystemState | list[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like replay verification of governed semantic development, helps with reducing one raw composition chain into a stable signature that ignores volatile node ids and timestamp-adjacent noise.

    Reference to Theory:
        Supports constitutional replay by comparing semantic development paths rather than only final answers or effect outcomes.

    Example Input Output:
        Input: `composition_chain_signature([{'node_id': 'not-abc', 'semantic_unit': 'Say hi.', 'depth': 0, 'role': 'root', 'status': 'open', 'certainty': 'low', 'blockers': []}])`
        Output: [{'semantic_unit': 'Say hi.', 'depth': 0, 'role': 'root', 'status': 'open', 'certainty': 'low', 'blocker_classes': [], 'blocker_count': 0}]

    Args:
        value: Value for `value` used by `composition_chain_signature`. Expected type: `SystemState | list[Mapping[str, Any]] | None`.

    Returns:
        list[dict[str, Any]]: Result produced by `composition_chain_signature`.
    """
    if isinstance(value, SystemState):
        chain = state_composition_chain(value)
    else:
        chain = [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []
    signatures: list[dict[str, Any]] = []
    for item in chain:
        blockers = item.get("blockers", [])
        signatures.append(
            {
                "semantic_unit": str(item.get("semantic_unit", "")).strip(),
                "depth": int(item.get("depth", 0) or 0),
                "role": str(item.get("role", "")).strip(),
                "status": str(item.get("status", "")).strip(),
                "certainty": str(item.get("certainty", "")).strip(),
                "blocker_classes": _blocker_classes(blockers),
                "blocker_count": len(blockers) if isinstance(blockers, list) else 0,
            }
        )
    return sorted(
        signatures,
        key=lambda item: (
            int(item.get("depth", 0)),
            str(item.get("semantic_unit", "")).lower(),
            str(item.get("role", "")),
            str(item.get("status", "")),
        ),
    )


def effect_trace_signature(trace: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like replay verification of governed effects, helps with collapsing one full effect trace into the stable comparison signature that matters constitutionally.

    Reference to Theory:
        Supports governed replay by comparing effect decisions and outcomes at the broker/executor boundary without depending on volatile timestamps or ids.

    Example Input Output:
        Input: `effect_trace_signature(trace={'artifact_title': 'Say Hi', 'request': {'effect_kind': 'execute.python3'}, 'decision': {'allowed': True}, 'result': {'ok': True, 'answer': 'hi'}})`
        Output: {'artifact_title': 'Say Hi', 'effect_kind': 'execute.python3', 'allowed': True, 'ok': True, 'answer': 'hi'}

    Args:
        trace: Value for `trace` used by `effect_trace_signature`. Expected type: `Mapping[str, Any] | None`.

    Returns:
        dict[str, Any]: Result produced by `effect_trace_signature`.
    """
    payload = dict(trace) if isinstance(trace, Mapping) else {}
    request = dict(payload.get("request", {})) if isinstance(payload.get("request", {}), Mapping) else {}
    decision = dict(payload.get("decision", {})) if isinstance(payload.get("decision", {}), Mapping) else {}
    result = dict(payload.get("result", {})) if isinstance(payload.get("result", {}), Mapping) else {}
    admission = dict(payload.get("admission", {})) if isinstance(payload.get("admission", {}), Mapping) else {}
    lifecycle = dict(payload.get("lifecycle", {})) if isinstance(payload.get("lifecycle", {}), Mapping) else {}
    allowed = bool(decision.get("allowed", payload.get("allowed", False)))
    admission_status = _canonical_admission_status(admission.get("status", ""))
    activation_status = str(lifecycle.get("activation_status", ""))
    trust_status = str(lifecycle.get("trust_status", ""))
    if allowed and admission_status == "admitted":
        activation_status = "active"
        trust_status = "trusted"
    semantic_receipts = {
        "request": _receipt_digest(
            {
                "effect_kind": str(request.get("effect_kind", payload.get("effect_kind", ""))),
                "executor_framework": str(request.get("executor_framework", "")),
                "invocation_payload": request.get("invocation_payload", ""),
            }
        ),
        "declaration": _receipt_digest(payload.get("declaration", {})),
        "policy": _receipt_digest(
            {
                "policy_titles": _canonical_policy_titles(admission.get("policy_titles", [])),
                "required_approval_class": str(admission.get("required_approval_class", "automatic")),
            }
        ),
        "approval": _receipt_digest(
            {
                "approval_titles": [
                    str(item).strip()
                    for item in admission.get("approval_titles", [])
                    if str(item).strip()
                ],
                "required_approval_class": str(admission.get("required_approval_class", "automatic")),
            }
        ),
        "lifecycle": _receipt_digest(
            {
                "activation_status": activation_status,
                "admission_status": admission_status,
                "installation_status": str(lifecycle.get("installation_status", "")),
                "quarantine_status": str(lifecycle.get("quarantine_status", "")),
                "review_status": str(lifecycle.get("review_status", "")),
                "trust_status": trust_status,
            }
        ),
        "grants": _receipt_digest(
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
                    "policy_titles": _canonical_policy_titles(item.get("policy_titles", [])),
                    "admission_status": _canonical_admission_status(item.get("admission_status", "")),
                }
                for item in payload.get("grants", [])
                if isinstance(item, Mapping)
            ]
        ),
    }
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


def constitutional_trace_snapshot(state: SystemState) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed run bundle export, helps with capturing the durable constitutional trace surface needed for later inspection and replay verification.

    Reference to Theory:
        Supports OPEN_GOVERNANCE and BUNDLE requirements by making grants, mediated effects, and semantic development replay-visible as one explicit record.

    Example Input Output:
        Input: `constitutional_trace_snapshot(state=SystemState.bootstrap(prompt='Say hi.'))`
        Output: {'schema': 'bssc_constitutional_trace.v1', 'effect_traces': [], 'capability_grants': [], 'composition_chain': [...]}

    Args:
        state: Value for `state` used by `constitutional_trace_snapshot`. Expected type: `SystemState`.

    Returns:
        dict[str, Any]: Result produced by `constitutional_trace_snapshot`.
    """
    composition_chain = state_composition_chain(state)
    composition_signatures = composition_chain_signature(composition_chain)
    decision_flow = controller_decision_flow_signature(state)
    transcript_signatures = llm_transcript_signature(state)
    return {
        "schema": CONSTITUTIONAL_TRACE_SCHEMA_VERSION,
        "captured_at": utc_now(),
        "run_id": state.run_id,
        "root_id": state.root_id,
        "host_abi_version": host_abi_version(),
        "capability_grants": json_safe(state.capability_grants),
        "effect_traces": json_safe(state.effect_traces),
        "effect_signatures": [effect_trace_signature(trace) for trace in state.effect_traces],
        "composition_chain": composition_chain,
        "composition_chain_signatures": composition_signatures,
        "composition_chain_receipt": {
            "schema": CONSTITUTIONAL_TRACE_SCHEMA_VERSION,
            "kind": "composition_chain",
            "digest": _receipt_digest(composition_signatures),
        },
        "decision_flow_signatures": decision_flow,
        "llm_transcript_signatures": transcript_signatures,
        "decision_flow_receipt": {
            "schema": CONSTITUTIONAL_TRACE_SCHEMA_VERSION,
            "kind": "decision_flow",
            "digest": _receipt_digest(
                {"decision_flow_signatures": decision_flow, "llm_transcript_signatures": transcript_signatures}
            ),
        },
        "recent_trace": [record.to_dict() for record in state.trace[-50:]],
        "recent_ledger": [record.to_dict() for record in state.ledger[-50:]],
    }


def compare_bundle_trace_to_state(
    bundle_trace: Mapping[str, Any] | None,
    replay_state: SystemState,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like replay verification of governed runs, helps with comparing the bundled constitutional trace against the replayed state and reporting concrete mismatches.

    Reference to Theory:
        Supports replay verification by checking that the mediated effect boundary and final outcome remain constitutionally aligned.

    Example Input Output:
        Input: `compare_bundle_trace_to_state(bundle_trace={'effect_signatures': []}, replay_state=SystemState.bootstrap(prompt='Say hi.'))`
        Output: {'matched': True, 'differences': []}

    Args:
        bundle_trace: Value for `bundle_trace` used by `compare_bundle_trace_to_state`. Expected type: `Mapping[str, Any] | None`.
        replay_state: Value for `replay_state` used by `compare_bundle_trace_to_state`. Expected type: `SystemState`.

    Returns:
        dict[str, Any]: Result produced by `compare_bundle_trace_to_state`.
    """
    original = dict(bundle_trace) if isinstance(bundle_trace, Mapping) else {}
    original_signatures = [
        effect_trace_signature(item)
        for item in original.get("effect_traces", [])
        if isinstance(item, Mapping)
    ]
    replay_signatures = [effect_trace_signature(item) for item in replay_state.effect_traces if isinstance(item, Mapping)]
    original_chain_signatures = composition_chain_signature(original.get("composition_chain", []))
    replay_chain_signatures = composition_chain_signature(replay_state)
    original_decision_flow = [
        dict(item) for item in original.get("decision_flow_signatures", []) if isinstance(item, Mapping)
    ]
    replay_decision_flow = controller_decision_flow_signature(replay_state)
    original_transcript = [
        dict(item) for item in original.get("llm_transcript_signatures", []) if isinstance(item, Mapping)
    ]
    replay_transcript = llm_transcript_signature(replay_state)
    differences: list[str] = []
    if original_signatures != replay_signatures:
        differences.append("effect trace signatures differ")
    if original_chain_signatures != replay_chain_signatures:
        differences.append("composition chain signatures differ")
    if strict and original_decision_flow and original_decision_flow != replay_decision_flow:
        differences.append("decision flow signatures differ")
    if strict and original_transcript and original_transcript != replay_transcript:
        differences.append("llm transcript signatures differ")
    return {
        "matched": not differences,
        "differences": differences,
        "original_run_id": str(original.get("run_id", "")).strip(),
        "replay_run_id": replay_state.run_id,
        "original_effect_trace_count": len(original_signatures),
        "replay_effect_trace_count": len(replay_signatures),
        "original_effect_signatures": original_signatures,
        "replay_effect_signatures": replay_signatures,
        "original_composition_chain_count": len(original_chain_signatures),
        "replay_composition_chain_count": len(replay_chain_signatures),
        "original_composition_chain_signatures": original_chain_signatures,
        "replay_composition_chain_signatures": replay_chain_signatures,
        "original_decision_flow_signature_count": len(original_decision_flow),
        "replay_decision_flow_signature_count": len(replay_decision_flow),
        "original_decision_flow_signatures": original_decision_flow,
        "replay_decision_flow_signatures": replay_decision_flow,
        "original_llm_transcript_signature_count": len(original_transcript),
        "replay_llm_transcript_signature_count": len(replay_transcript),
        "original_llm_transcript_signatures": original_transcript,
        "replay_llm_transcript_signatures": replay_transcript,
    }
