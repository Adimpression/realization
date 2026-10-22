"""Adapter between governed resumption and the canonical reduction controller."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

from args import STATE_SQLITE_PATH_ENV, apply_controller_feature_toggle_overrides
from applied_theory_types import RuntimeDeterminismPolicy
from controller_runtime import build_controller
from system_state import SystemState, attach_evidence_specs
from title_semantics import PROLOG_QUERY_PRIMING_MODE_ENV

from realized_core_engine.resumption_contracts import (
    ContinuationInlet,
    HoldOn,
    InletRelationship,
    OperationKind,
    ReductionContext,
    ReductionProposal,
    SemanticItem,
    SemanticOutcome,
    SemanticState,
)


_PROJECTED_ITEM_MARKER = "resumption_projection"
_PROJECTED_NODE_PREFIX = "engine:node:"
_PROJECTED_HOLD_PREFIX = "engine:hold:"


class CanonicalReductionAdapter:
    """Advance typed resumption context through the established controller."""

    def reduce(
        self,
        context: ReductionContext,
        *,
        should_stop: Callable[[], bool],
    ) -> ReductionProposal:
        state = self._load_or_bootstrap_state(context)
        self._apply_execution_policy(state, context.execution_policy)
        self._prepare_operation(state, context)
        self._apply_inlet(state, context)
        prepared_frontier = tuple(sorted(state.frontier))

        controller = build_controller(
            state=state,
            llm_policy=str(context.execution_policy.get("llm_policy", "auto")),
        )
        controller.attempt_stop_requested = should_stop
        controller.run(max_steps=int(context.execution_policy.get("max_steps", 256)))

        resulting = semantic_state_from_system_state(
            state,
            baseline=context.candidate_state,
        )
        return ReductionProposal(
            resulting_state=resulting,
            semantic_outcome=_semantic_outcome(state),
            proposal_references=tuple(sorted(state.proposals)),
            proposal_interactions=_proposal_interactions(state),
            capability_receipt_references=_receipt_references(
                state.capability_grants,
                prefix="capability",
            ),
            effect_receipt_references=_receipt_references(
                state.effect_traces,
                prefix="effect",
            ),
            reconciliation={
                "adapter": "canonical_system_state",
                "run_id": state.run_id,
                "run_outcome": state.run_outcome.value,
                "prepared_frontier": list(prepared_frontier),
                "resulting_frontier": sorted(state.frontier),
            },
            presentation=state.summary(),
        )

    @staticmethod
    def _load_or_bootstrap_state(context: ReductionContext) -> SystemState:
        snapshot = context.candidate_state.engine_state
        if snapshot:
            return SystemState.from_dict(dict(snapshot))

        inlet_payload = (
            context.admitted_inlet.payload
            if context.admitted_inlet is not None
            else {}
        )
        prompt = str(
            inlet_payload.get("prompt")
            or inlet_payload.get("content")
            or context.candidate_state.governing_direction.objective
        ).strip()
        if not prompt:
            raise ValueError("the canonical reduction requires an explicit objective")
        state = SystemState.bootstrap(prompt)
        seed = _root_seed_item(context.candidate_state)
        if seed is not None:
            state.root().metadata["resumption_item_id"] = seed.item_id
        return state

    @staticmethod
    def _apply_execution_policy(
        state: SystemState,
        execution_policy: Mapping[str, Any],
    ) -> None:
        os.environ["STATE_VECTOR_MODE"] = "off"
        sqlite_path = str(execution_policy.get("sqlite_path", "")).strip()
        if sqlite_path:
            os.environ[STATE_SQLITE_PATH_ENV] = sqlite_path
        priming = str(execution_policy.get("prolog_query_priming", "")).strip()
        if priming:
            os.environ[PROLOG_QUERY_PRIMING_MODE_ENV] = priming
        determinism_policy = execution_policy.get("determinism_policy")
        if isinstance(determinism_policy, Mapping):
            state.determinism_policy = RuntimeDeterminismPolicy.from_dict(
                determinism_policy
            )

        apply_controller_feature_toggle_overrides(
            state,
            SimpleNamespace(
                discovery=execution_policy.get("discovery"),
                reflection=execution_policy.get("reflection"),
                contemplation=execution_policy.get("contemplation"),
                supported_executors=execution_policy.get("supported_executors"),
            ),
        )
        evidence_specs = execution_policy.get("evidence_specs", ())
        if isinstance(evidence_specs, Iterable) and not isinstance(
            evidence_specs,
            (str, bytes, Mapping),
        ):
            normalized = [dict(item) for item in evidence_specs if isinstance(item, Mapping)]
            if normalized:
                attach_evidence_specs(state, normalized)

    @staticmethod
    def _prepare_operation(state: SystemState, context: ReductionContext) -> None:
        if context.operation is not OperationKind.RESUME_SUSPENDED:
            return
        if context.projection is None or context.admitted_inlet is None:
            raise ValueError("suspended resumption requires an anchored projection")

        inlet = context.admitted_inlet
        hold_id = str(inlet.payload.get("hold_id") or inlet.target).strip()
        hold = next(
            (item for item in context.projection.state.holds if item.hold_id == hold_id),
            None,
        )
        if hold is None:
            raise ValueError(f"unknown HoldOn continuation: {hold_id}")
        eligible = {
            str(item)
            for item in hold.continuation_carrier.get("frontier", ())
            if str(item) in state.graph.nodes
        }
        state.frontier.clear()
        for node_id in eligible:
            state.paused.discard(node_id)
            state.incomplete.discard(node_id)
            state.status[node_id] = _open_status(state, node_id)
            state.frontier.add(node_id)

        pause_ids = {
            str(value)
            for value in hold.continuation_carrier.get("pause_point_ids", ())
        }
        if hold_id.startswith(_PROJECTED_HOLD_PREFIX):
            pause_ids.add(hold_id.removeprefix(_PROJECTED_HOLD_PREFIX))
        for pause_id in pause_ids:
            state.pause_points.pop(pause_id, None)
            state.waits.pop(pause_id, None)

    @staticmethod
    def _apply_inlet(state: SystemState, context: ReductionContext) -> None:
        inlet = context.admitted_inlet
        if inlet is None or context.operation is OperationKind.START:
            return
        if inlet.relationship is InletRelationship.REDIRECTION:
            return

        content = str(
            inlet.payload.get("content")
            or inlet.payload.get("observation")
            or ""
        ).strip()
        if not content:
            state.record_inlet(
                kind=inlet.kind,
                semantic_identity=inlet.target,
                payload={
                    "inlet_id": inlet.inlet_id,
                    "relationship": inlet.relationship.value,
                },
                provenance=list(inlet.provenance),
            )
            return

        target = str(
            inlet.payload.get("target_node_id")
            or _target_node_id(state, inlet)
            or "root"
        )
        if context.operation is not OperationKind.RESUME_SUSPENDED:
            targets = state.find_nodes(target=target)
            if any(node.id in state.paused for node in targets):
                raise ValueError(
                    "a general inlet cannot reopen suspended state; use hold satisfaction"
                )
        source = {
            "human_contribution": "human",
            "prior_result": "governed_prior_result",
        }.get(inlet.kind, inlet.source or "external")
        attach_evidence_specs(
            state,
            [
                {
                    "target": target,
                    "observation": content,
                    "source": source,
                    "context": {
                        **dict(inlet.payload.get("context", {})),
                        "resumption_inlet_id": inlet.inlet_id,
                        "relationship": inlet.relationship.value,
                    },
                    "provenance": [inlet.inlet_id, *inlet.provenance],
                    "support_strength": inlet.payload.get(
                        "support_strength", "high"
                    ),
                    "confidence": inlet.payload.get("confidence", "high"),
                    "polarity": inlet.payload.get("polarity", "support"),
                }
            ],
        )


def semantic_state_from_system_state(
    state: SystemState,
    *,
    baseline: SemanticState,
) -> SemanticState:
    """Project canonical controller state without promoting transcript text."""

    projected_items: dict[str, SemanticItem] = {}
    achieved_ids: set[str] = set()
    for node_id, node in sorted(state.graph.nodes.items()):
        item_id = str(
            node.metadata.get("resumption_item_id")
            or f"{_PROJECTED_NODE_PREFIX}{node_id}"
        )
        status = state.node_status(node_id).value
        item = SemanticItem(
            item_id=item_id,
            kind="realization_node",
            payload={
                _PROJECTED_ITEM_MARKER: True,
                "node": node.to_dict(),
                "status": status,
                "certainty": _json_value(state.certainty.get(node_id)),
                "blockers": list(state.blockers.get(node_id, ())),
                "conflicts": list(state.conflicts.get(node_id, ())),
            },
            evidence_references=tuple(state.evidence_by_node.get(node_id, ())),
            provenance_references=tuple(state.provenance_links.get(node_id, ())),
        )
        projected_items[item_id] = item
        if node_id in state.closed or status == "closed":
            achieved_ids.add(item_id)

    projected_ids = set(projected_items)
    external_achieved = {
        item.item_id: item
        for item in baseline.achieved
        if not _is_projected_item(item) and item.item_id not in projected_ids
    }
    external_non_achieved = {
        item.item_id: item
        for item in baseline.non_achievedness
        if not _is_projected_item(item) and item.item_id not in projected_ids
    }
    achieved = {
        **external_achieved,
        **{
            item_id: item
            for item_id, item in projected_items.items()
            if item_id in achieved_ids
        },
    }
    non_achieved = {
        **external_non_achieved,
        **{
            item_id: item
            for item_id, item in projected_items.items()
            if item_id not in achieved_ids
        },
    }

    engine_holds = {
        hold.hold_id: hold for hold in _holds_from_system_state(state, baseline)
    }
    retained_holds = {
        hold.hold_id: hold
        for hold in baseline.holds
        if not hold.hold_id.startswith(_PROJECTED_HOLD_PREFIX)
    }
    holds = {**retained_holds, **engine_holds}

    capability_declarations = {
        str(item.get("id") or item): dict(item)
        for item in baseline.capability_declarations
    }
    capability_declarations.update(
        {
            capability.id: capability.to_dict()
            for capability in state.capabilities.values()
        }
    )
    provenance = tuple(
        dict.fromkeys(
            (
                *baseline.provenance_references,
                *(carrier.id for carrier in state.inlets),
                *(carrier.id for carrier in state.outlets),
            )
        )
    )
    return replace(
        baseline,
        achieved=tuple(achieved[key] for key in sorted(achieved)),
        non_achievedness=tuple(
            non_achieved[key] for key in sorted(non_achieved)
        ),
        refinement_graph=state.graph.to_dict(),
        duties_and_obligations=tuple(
            {
                "node_id": node.id,
                "required": node.required,
                "role": node.role,
            }
            for node in sorted(state.graph.nodes.values(), key=lambda item: item.id)
            if node.required
        ),
        certainty={key: _json_value(value) for key, value in state.certainty.items()},
        blockers={key: list(value) for key, value in state.blockers.items()},
        conflicts={key: list(value) for key, value in state.conflicts.items()},
        evidence_and_support={
            "evidence": {
                key: value.to_dict() for key, value in state.evidence.items()
            },
            "claims": {key: value.to_dict() for key, value in state.claims.items()},
            "support": {
                key: value.to_dict() for key, value in state.support.items()
            },
            "provenance_links": {
                key: list(value) for key, value in state.provenance_links.items()
            },
        },
        commitments=tuple(
            value.to_dict()
            for _, value in sorted(state.commitments.items())
        ),
        holds=tuple(holds[key] for key in sorted(holds)),
        capability_declarations=tuple(
            capability_declarations[key]
            for key in sorted(capability_declarations)
        ),
        provenance_references=provenance,
        engine_state=state.to_dict(),
    )


def _holds_from_system_state(
    state: SystemState,
    baseline: SemanticState,
) -> tuple[HoldOn, ...]:
    existing = {hold.hold_id: hold for hold in baseline.holds}
    holds: list[HoldOn] = []
    pause_points = {**state.pause_points, **state.waits}
    for pause_id, pause in sorted(pause_points.items()):
        hold_id = f"{_PROJECTED_HOLD_PREFIX}{pause_id}"
        prior = existing.get(hold_id)
        if prior is not None:
            holds.append(prior)
            continue
        node_item_id = f"{_PROJECTED_NODE_PREFIX}{pause.node_id}"
        if pause.node_id in state.graph.nodes:
            node_item_id = str(
                state.graph.get_node(pause.node_id).metadata.get(
                    "resumption_item_id", node_item_id
                )
            )
        holds.append(
            HoldOn(
                hold_id=hold_id,
                unresolved_semantic_object={"item_id": node_item_id},
                continuation_carrier={
                    "frontier": [pause.node_id],
                    "pause_point_ids": [pause_id],
                    "run_id": state.run_id,
                },
                resume_predicate={
                    "kind": "boundary_contribution",
                    "required_boundary": _json_value(pause.required_boundary),
                },
                failure_or_expiry_predicate={},
                temporal_policy={},
                correlation={"pause_point_id": pause_id},
                multiplicity={"mode": "one"},
                scope={"root_id": state.root_id, "node_id": pause.node_id},
                provenance_and_governance={
                    "reason": pause.reason,
                    "created_at": pause.created_at,
                },
            )
        )
    return tuple(holds)


def _root_seed_item(state: SemanticState) -> SemanticItem | None:
    candidates = [
        item
        for item in state.non_achievedness
        if item.kind == "objective" or item.payload.get("target") == "root"
    ]
    return sorted(candidates, key=lambda item: item.item_id)[0] if candidates else None


def _target_node_id(state: SystemState, inlet: ContinuationInlet) -> str:
    if inlet.target in state.graph.nodes:
        return inlet.target
    for node in state.graph.nodes.values():
        if node.metadata.get("resumption_item_id") == inlet.target:
            return node.id
        if f"{_PROJECTED_NODE_PREFIX}{node.id}" == inlet.target:
            return node.id
    return state.root_id


def _open_status(state: SystemState, node_id: str) -> Any:
    status_type = type(state.status[node_id]) if node_id in state.status else None
    if status_type is not None:
        try:
            return status_type("open")
        except ValueError:
            pass
    from applied_theory_types import NodeStatus

    return NodeStatus.OPEN


def _is_projected_item(item: SemanticItem) -> bool:
    return bool(item.payload.get(_PROJECTED_ITEM_MARKER)) or item.item_id.startswith(
        _PROJECTED_NODE_PREFIX
    )


def _semantic_outcome(state: SystemState) -> SemanticOutcome:
    return {
        "completed": SemanticOutcome.COMPLETED,
        "paused": SemanticOutcome.PAUSED,
        "incomplete": SemanticOutcome.INCOMPLETE,
        "ongoing": SemanticOutcome.EXHAUSTED,
    }.get(state.run_outcome.value, SemanticOutcome.INCOMPLETE)


def _receipt_references(
    receipts: Iterable[Mapping[str, Any]],
    *,
    prefix: str,
) -> tuple[str, ...]:
    references: list[str] = []
    for index, receipt in enumerate(receipts):
        reference = str(
            receipt.get("receipt_id")
            or receipt.get("id")
            or f"{prefix}:{index}"
        ).strip()
        if reference:
            references.append(reference)
    return tuple(dict.fromkeys(references))


def _proposal_interactions(state: SystemState) -> tuple[dict[str, Any], ...]:
    if not state.proposals and not state.llm_transcript:
        return ()
    return (
        {
            "proposals": [
                state.proposals[key].to_dict()
                for key in sorted(state.proposals)
            ],
            "llm_receipts": [dict(item) for item in state.llm_transcript],
            "determinism_policy": state.determinism_policy.to_dict(),
        },
    )


def _json_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


__all__ = ["CanonicalReductionAdapter", "semantic_state_from_system_state"]
