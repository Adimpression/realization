"""Adapter between governed resumption and the canonical reduction controller."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

from realized_core_engine.configuration import STATE_SQLITE_PATH_ENV, apply_controller_feature_toggle_overrides
from realized_core_semantics.applied_model import NodeStatus, RuntimeDeterminismPolicy
from realized_core_engine.controller_runtime import build_controller
from realized_host_interaction.context import HostInteractionContext
from realized_core_engine.state import SystemState, attach_evidence_specs
from realized_core_semantics.title_semantics import PROLOG_QUERY_PRIMING_MODE_ENV

from realized_core_runtime import PerformanceRecorder, performance_scope

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
_PROJECTED_ARTIFACT_PREFIX = "engine:artifact:"
_PROJECTED_PRODUCT_PREFIX = "engine:product:"
_PROJECTED_HOLD_PREFIX = "engine:hold:"
_SUBJECT_SCOPE_IMPORT_KIND = "subject_reasoning_scope"


class CanonicalReductionAdapter:
    """Advance typed resumption context through the established controller."""

    def __init__(
        self,
        *,
        host_interaction_context: HostInteractionContext | None = None,
    ) -> None:
        self._host_interaction_context = host_interaction_context

    def reduce(
        self,
        context: ReductionContext,
        *,
        should_stop: Callable[[], bool],
    ) -> ReductionProposal:
        reconstructed = (
            context.projection is not None
            or bool(context.candidate_state.engine_state)
            or bool(context.candidate_state.refinement_graph)
        )
        state = self._load_or_bootstrap_state(context)
        trace_start = len(state.trace) if reconstructed else 0
        existing_proposal_ids = set(state.proposals) if reconstructed else set()
        llm_receipt_start = len(state.llm_transcript) if reconstructed else 0
        capability_receipt_start = (
            len(state.capability_grants) if reconstructed else 0
        )
        effect_receipt_start = len(state.effect_traces) if reconstructed else 0
        self._apply_execution_policy(state, context.execution_policy)
        self._prepare_operation(state, context)
        self._apply_inlet(state, context)
        prepared_frontier = tuple(sorted(state.frontier))

        controller = build_controller(
            state=state,
            llm_policy=str(context.execution_policy.get("llm_policy", "auto")),
            host_interaction_context=self._host_interaction_context,
        )
        controller.attempt_stop_requested = should_stop
        performance = PerformanceRecorder()
        with performance_scope(performance):
            with performance.measure("reduction_latency_ns"):
                controller.run(
                    max_steps=int(
                        context.execution_policy.get("max_steps", 256)
                    )
                )

        resulting = semantic_state_from_system_state(
            state,
            baseline=context.candidate_state,
        )
        proposal_ids = tuple(
            sorted(set(state.proposals) - existing_proposal_ids)
        )
        reduction_trace = tuple(
            _step_replay_record(record)
            for record in state.trace[trace_start:]
        )
        return ReductionProposal(
            resulting_state=resulting,
            semantic_outcome=_semantic_outcome(state),
            proposal_references=proposal_ids,
            proposal_interactions=_proposal_interactions(
                state,
                proposal_ids=proposal_ids,
                llm_receipt_start=llm_receipt_start,
            ),
            reduction_trace=reduction_trace,
            frontier_selections=_frontier_selection_records(
                reduction_trace
            ),
            retrieved_candidate_sets=_retrieved_candidate_records(
                reduction_trace
            ),
            execution_decisions=(
                {
                    "kind": "runtime_outcome",
                    "outcome": state.run_outcome.value,
                    "remaining_frontier": sorted(state.frontier),
                    "paused_node_ids": sorted(state.paused),
                    "incomplete_node_ids": sorted(state.incomplete),
                    "closed_node_ids": sorted(state.closed),
                },
            ),
            capability_receipt_references=_receipt_references(
                state.capability_grants[capability_receipt_start:],
                prefix="capability",
            ),
            effect_receipt_references=_receipt_references(
                state.effect_traces[effect_receipt_start:],
                prefix="effect",
            ),
            performance_measurements=performance.snapshot(),
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
        if context.operation is OperationKind.REDIRECT_AND_REALIGN:
            state = SystemState.bootstrap(
                context.candidate_state.governing_direction.objective
            )
            seed = _root_seed_item(context.candidate_state)
            if seed is not None:
                state.root().metadata["resumption_item_id"] = seed.item_id
            return state

        if context.projection is not None:
            return system_state_from_semantic_state(context.candidate_state)

        inlet_snapshot = (
            context.admitted_inlet.payload.get("engine_state")
            if context.admitted_inlet is not None
            else None
        )
        if (
            context.operation is OperationKind.START
            and isinstance(inlet_snapshot, Mapping)
            and inlet_snapshot
        ):
            return SystemState.from_dict(dict(inlet_snapshot))

        snapshot = context.candidate_state.engine_state
        if snapshot:
            return SystemState.from_dict(dict(snapshot))

        if context.candidate_state.refinement_graph.get("nodes"):
            return system_state_from_semantic_state(context.candidate_state)

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
        candidate = context.candidate_state
        if not candidate.governing_direction.objective:
            candidate = replace(
                candidate,
                governing_direction=replace(
                    candidate.governing_direction,
                    objective=prompt,
                ),
            )
        return system_state_from_semantic_state(candidate)

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

        if context.operation not in {
            OperationKind.CONTINUE,
            OperationKind.RESUME_SUSPENDED,
        }:
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
    baseline_items = {
        item.item_id: item
        for item in (*baseline.achieved, *baseline.non_achievedness)
    }
    for node_id, node in sorted(state.graph.nodes.items()):
        item_id = str(
            node.metadata.get("resumption_item_id")
            or f"{_PROJECTED_NODE_PREFIX}{node_id}"
        )
        status = state.node_status(node_id).value
        prior = baseline_items.get(item_id)
        payload = {
            **(dict(prior.payload) if prior is not None else {}),
            _PROJECTED_ITEM_MARKER: True,
            "node": node.to_dict(),
            "status": status,
            "certainty": _json_value(state.certainty.get(node_id)),
            "blockers": list(state.blockers.get(node_id, ())),
            "conflicts": list(state.conflicts.get(node_id, ())),
        }
        item = SemanticItem(
            item_id=item_id,
            kind=prior.kind if prior is not None else "realization_node",
            payload=payload,
            evidence_references=tuple(
                dict.fromkeys(
                    (
                        *(prior.evidence_references if prior is not None else ()),
                        *state.evidence_by_node.get(node_id, ()),
                    )
                )
            ),
            provenance_references=tuple(
                dict.fromkeys(
                    (
                        *(prior.provenance_references if prior is not None else ()),
                        *state.provenance_links.get(node_id, ()),
                    )
                )
            ),
            governance_references=(
                prior.governance_references if prior is not None else ()
            ),
        )
        projected_items[item_id] = item
        if node_id in state.closed or status == "closed":
            achieved_ids.add(item_id)

    for collection, artifacts in (
        ("artifacts", state.artifacts),
        ("learned_artifacts", state.learned_artifacts),
    ):
        for artifact_id, artifact in sorted(artifacts.items()):
            if _json_value(artifact.admissibility) != "admitted":
                continue
            item_id = f"{_PROJECTED_ARTIFACT_PREFIX}{collection}:{artifact_id}"
            projected_items[item_id] = SemanticItem(
                item_id=item_id,
                kind="realization_artifact",
                payload={
                    _PROJECTED_ITEM_MARKER: True,
                    "engine_collection": collection,
                    "artifact": artifact.to_dict(),
                    "origin": dict(
                        state.learned_artifact_origins.get(artifact_id, {})
                    ),
                },
                provenance_references=tuple(artifact.provenance),
            )
            achieved_ids.add(item_id)

    for product_id, product in sorted(state.products.items()):
        if not product.committed:
            continue
        item_id = f"{_PROJECTED_PRODUCT_PREFIX}{product_id}"
        projected_items[item_id] = SemanticItem(
            item_id=item_id,
            kind="realization_product",
            payload={
                _PROJECTED_ITEM_MARKER: True,
                "engine_collection": "products",
                "product": product.to_dict(),
            },
            provenance_references=tuple(product.provenance),
        )
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
    scope_imports = tuple(
        value
        for value in baseline.scope_imports
        if value.get("kind") != _SUBJECT_SCOPE_IMPORT_KIND
    )
    if state.subject_reasoning_scope:
        scope_imports = (
            *scope_imports,
            {
                "kind": _SUBJECT_SCOPE_IMPORT_KIND,
                "value": dict(state.subject_reasoning_scope),
            },
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
        scope_imports=scope_imports,
        provenance_references=provenance,
        engine_state={},
    )


def system_state_from_semantic_state(state: SemanticState) -> SystemState:
    """Reconstruct active reducer state from admitted semantic fields only."""

    graph = dict(state.refinement_graph)
    nodes = [dict(item) for item in graph.get("nodes", ())]
    bootstrap_payload: dict[str, Any] = {}
    if not nodes:
        bootstrap = SystemState.bootstrap(
            state.governing_direction.objective
        )
        seed = _root_seed_item(state)
        if seed is not None:
            bootstrap.root().metadata["resumption_item_id"] = seed.item_id
        bootstrap_payload = bootstrap.to_dict()
        graph = dict(bootstrap_payload["graph"])
        nodes = [dict(item) for item in graph.get("nodes", ())]

    root = next(
        (item for item in nodes if item.get("role") == "root"),
        next(
            (
                item
                for item in nodes
                if item.get("parent_id") in {None, ""}
            ),
            nodes[0],
        ),
    )
    root_id = str(root["id"])
    edges = [dict(item) for item in graph.get("edges", ())]
    known_node_ids = {
        str(item["id"]) for item in nodes if item.get("id") is not None
    }
    root_seed = _root_seed_item(state)
    root_depth = int(root.get("depth", 0))
    for item in state.non_achievedness:
        if (
            root_seed is not None
            and item.item_id == root_seed.item_id
        ) or _is_projected_item(item):
            continue
        node = item.payload.get("node")
        if isinstance(node, Mapping) and node.get("id") is not None:
            continue
        node_id = f"semantic:{item.item_id}"
        if node_id in known_node_ids:
            continue
        nodes.append(
            {
                "id": node_id,
                "semantic_unit": _semantic_item_text(item),
                "role": "resumption_non_achievedness",
                "description": "Admitted non-achievedness from semantic state.",
                "required": True,
                "depth": root_depth + 1,
                "parent_id": root_id,
                "origin": "controller",
                "metadata": {
                    "resumption_item_id": item.item_id,
                    "resumption_item_kind": item.kind,
                },
            }
        )
        edges.append(
            {
                "src": root_id,
                "dst": node_id,
                "type": "refines",
            }
        )
        known_node_ids.add(node_id)
    graph = {"nodes": nodes, "edges": edges}
    node_ids = set(known_node_ids)

    item_by_node: dict[str, tuple[SemanticItem, bool]] = {}
    items_by_id = {
        item.item_id: (item, achieved)
        for achieved, items in (
            (True, state.achieved),
            (False, state.non_achievedness),
        )
        for item in items
    }
    for achieved, items in (
        (True, state.achieved),
        (False, state.non_achievedness),
    ):
        for item in items:
            node = item.payload.get("node")
            if isinstance(node, Mapping) and node.get("id") is not None:
                item_by_node[str(node["id"])] = (item, achieved)
    for node in nodes:
        metadata = node.get("metadata", {})
        if not isinstance(metadata, Mapping):
            continue
        item_id = metadata.get("resumption_item_id")
        if item_id is not None and str(item_id) in items_by_id:
            item_by_node[str(node["id"])] = items_by_id[str(item_id)]

    status: dict[str, str] = {}
    closed: set[str] = set()
    paused: set[str] = set()
    incomplete: set[str] = set()
    inadmissible: set[str] = set()
    frontier: set[str] = set()
    for node_id in node_ids:
        item_entry = item_by_node.get(node_id)
        item = item_entry[0] if item_entry is not None else None
        achieved = item_entry[1] if item_entry is not None else False
        raw_status = (
            str(item.payload.get("status", "")) if item is not None else ""
        )
        normalized = raw_status or ("closed" if achieved else "open")
        status[node_id] = normalized
        if normalized == "closed" or achieved:
            closed.add(node_id)
        elif normalized == "paused":
            paused.add(node_id)
        elif normalized == "incomplete":
            incomplete.add(node_id)
        elif normalized == "inadmissible":
            inadmissible.add(node_id)
        else:
            frontier.add(node_id)

    pause_points: dict[str, dict[str, Any]] = {}
    for hold in state.holds:
        carrier = hold.continuation_carrier
        hold_node_ids = {
            str(item)
            for item in carrier.get("frontier", ())
            if str(item) in node_ids
        }
        raw_boundary = hold.resume_predicate.get("required_boundary")
        for pause_id in carrier.get("pause_point_ids", ()):
            if not hold_node_ids or not isinstance(raw_boundary, str):
                continue
            node_id = sorted(hold_node_ids)[0]
            pause_points[str(pause_id)] = {
                "id": str(pause_id),
                "node_id": node_id,
                "reason": str(
                    hold.provenance_and_governance.get(
                        "reason", "governed suspension"
                    )
                ),
                "required_boundary": raw_boundary,
                "created_at": str(
                    hold.provenance_and_governance.get("created_at", "")
                ),
            }
            frontier.discard(node_id)
            paused.add(node_id)
            status[node_id] = "paused"

    support = state.evidence_and_support
    evidence = {
        str(key): dict(value)
        for key, value in dict(support.get("evidence", {})).items()
        if isinstance(value, Mapping)
        and str(value.get("node_id", "")) in node_ids
    }
    for item in state.achieved:
        if _is_projected_item(item) or item.payload.get("engine_collection"):
            continue
        raw_node = item.payload.get("node")
        node_id = (
            str(raw_node["id"])
            if isinstance(raw_node, Mapping)
            and str(raw_node.get("id", "")) in node_ids
            else root_id
        )
        evidence_id = f"resumption:evidence:{item.item_id}"
        evidence.setdefault(
            evidence_id,
            {
                "id": evidence_id,
                "node_id": node_id,
                "observation": _semantic_item_text(item),
                "source": "admitted_semantic_state",
                "context": {
                    "resumption_item_id": item.item_id,
                    "resumption_item_kind": item.kind,
                },
                "support_effect": "high",
                "confidence": "high",
                "polarity": "support",
                "provenance": list(item.provenance_references),
                "created_at": str(item.payload.get("created_at", "")),
            },
        )
    evidence_by_node: dict[str, list[str]] = {}
    for evidence_id, value in evidence.items():
        evidence_by_node.setdefault(str(value["node_id"]), []).append(evidence_id)
    claims = {
        str(key): dict(value)
        for key, value in dict(support.get("claims", {})).items()
        if isinstance(value, Mapping)
        and str(value.get("node_id", "")) in node_ids
    }
    capabilities = dict(bootstrap_payload.get("capabilities", {}))
    capabilities.update(
        {
            str(value["id"]): dict(value)
            for value in state.capability_declarations
            if isinstance(value, Mapping)
            and value.get("id") is not None
            and all(
                key in value
                for key in (
                    "affordance",
                    "input_form",
                    "output_form",
                    "limits",
                    "semantic_role",
                )
            )
        }
    )
    commitments = {
        str(value["id"]): dict(value)
        for value in state.commitments
        if isinstance(value, Mapping)
        and value.get("id") is not None
        and str(value.get("node_id", "")) in node_ids
    }
    products: dict[str, dict[str, Any]] = {}
    artifacts: dict[str, dict[str, Any]] = {}
    learned_artifacts: dict[str, dict[str, Any]] = {}
    learned_artifact_origins: dict[str, dict[str, Any]] = {}
    for item in state.achieved:
        if not _is_projected_item(item):
            continue
        collection = str(item.payload.get("engine_collection", ""))
        if collection == "products":
            value = item.payload.get("product")
            if isinstance(value, Mapping) and value.get("id") is not None:
                products[str(value["id"])] = dict(value)
            continue
        if collection not in {"artifacts", "learned_artifacts"}:
            continue
        value = item.payload.get("artifact")
        if not isinstance(value, Mapping) or value.get("id") is None:
            continue
        artifact_id = str(value["id"])
        destination = (
            artifacts if collection == "artifacts" else learned_artifacts
        )
        destination[artifact_id] = dict(value)
        origin = item.payload.get("origin")
        if collection == "learned_artifacts" and isinstance(origin, Mapping):
            learned_artifact_origins[artifact_id] = dict(origin)

    subject_reasoning_scope: dict[str, Any] = {}
    for scope_import in state.scope_imports:
        if scope_import.get("kind") != _SUBJECT_SCOPE_IMPORT_KIND:
            continue
        value = scope_import.get("value")
        if isinstance(value, Mapping):
            subject_reasoning_scope = dict(value)
            break

    restored = SystemState.from_dict(
        {
            **bootstrap_payload,
            "root_id": root_id,
            "graph": {
                "nodes": nodes,
                "edges": [
                    dict(item)
                    for item in graph.get("edges", ())
                    if str(item.get("src", "")) in node_ids
                    and str(item.get("dst", "")) in node_ids
                ],
            },
            "frontier": sorted(frontier),
            "evidence": evidence,
            "evidence_by_node": evidence_by_node,
            "claims": claims,
            "capabilities": capabilities,
            "products": products,
            "artifacts": artifacts,
            "learned_artifacts": learned_artifacts,
            "subject_reasoning_scope": subject_reasoning_scope,
            "learned_artifact_origins": learned_artifact_origins,
            "pause_points": pause_points,
            "commitments": commitments,
            "certainty": {
                key: value
                for key, value in state.certainty.items()
                if key in node_ids
            },
            "status": status,
            "blockers": {
                key: list(value)
                for key, value in state.blockers.items()
                if key in node_ids
            },
            "support": {
                key: dict(value)
                for key, value in dict(support.get("support", {})).items()
                if key in node_ids and isinstance(value, Mapping)
            },
            "conflicts": {
                key: list(value)
                for key, value in state.conflicts.items()
                if key in node_ids
            },
            "closed": sorted(closed),
            "paused": sorted(paused),
            "incomplete": sorted(incomplete),
            "inadmissible": sorted(inadmissible),
            "provenance_links": {
                key: list(value)
                for key, value in dict(
                    support.get("provenance_links", {})
                ).items()
                if key in node_ids
            },
            "run_outcome": "ongoing",
        }
    )
    restored.llm_transcript = []
    restored.proposals = {}
    restored.ledger = []
    restored.trace = []
    restored.capability_grants = []
    restored.effect_traces = []
    restored.artifact_persistence = []
    restored.sequence_counter = 0
    restored.visit_counts = {}
    return restored


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
            holds.append(
                replace(
                    prior,
                    continuation_carrier={
                        key: value
                        for key, value in prior.continuation_carrier.items()
                        if key != "run_id"
                    },
                )
            )
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


def _semantic_item_text(item: SemanticItem) -> str:
    for key in (
        "text",
        "content",
        "statement",
        "observation",
        "title",
        "question",
        "objective",
    ):
        value = item.payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    inlet = item.payload.get("inlet")
    if isinstance(inlet, Mapping):
        for key in ("content", "observation", "text", "statement"):
            value = inlet.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return f"{item.kind}: {item.item_id}"


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


def _proposal_interactions(
    state: SystemState,
    *,
    proposal_ids: tuple[str, ...],
    llm_receipt_start: int,
) -> tuple[dict[str, Any], ...]:
    proposals = [state.proposals[key] for key in proposal_ids]
    receipts = [dict(item) for item in state.llm_transcript[llm_receipt_start:]]
    if not receipts:
        for proposal in proposals:
            if proposal.source != "replay":
                continue
            matching = next(
                (
                    dict(item)
                    for item in state.llm_transcript
                    if str(item.get("proposal_type", ""))
                    == proposal.proposal_type.value
                    and str(item.get("mode", "")) == proposal.mode.value
                    and _json_value(item.get("payload"))
                    == _json_value(proposal.payload)
                ),
                None,
            )
            if matching is not None and matching not in receipts:
                receipts.append(matching)
    if not proposals and not receipts:
        return ()
    return (
        {
            "proposals": [
                proposal.to_dict() for proposal in proposals
            ],
            "llm_receipts": receipts,
            "determinism_policy": state.determinism_policy.to_dict(),
        },
    )


def _step_replay_record(record: Any) -> dict[str, Any]:
    """Externalize decision content without wall-clock presentation noise."""

    return {
        "sequence": int(record.seq),
        "kind": str(record.kind),
        "node_id": record.node_id,
        "intent": str(record.intent),
        "action": str(record.action),
        "result": str(record.result),
        "evaluation": str(record.evaluation),
        "commit_effect": str(record.commit_effect),
        "payload": _json_value(record.payload),
    }


def _frontier_selection_records(
    reduction_trace: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "sequence": record["sequence"],
            "selected_node_id": record.get("node_id"),
            "proposal_id": record.get("payload", {}).get("proposal_id", ""),
            "candidate_order": list(
                record.get("payload", {}).get("candidate_order", ())
            ),
        }
        for record in reduction_trace
        if record.get("kind") == "frontier_selection"
    )


def _retrieved_candidate_records(
    reduction_trace: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    for record in reduction_trace:
        kind = str(record.get("kind", ""))
        payload = record.get("payload", {})
        if not isinstance(payload, Mapping):
            continue
        if kind != "learning_context" and "retriev" not in kind:
            continue
        ordered = next(
            (
                payload[key]
                for key in (
                    "artifact_ids",
                    "ordered_candidate_ids",
                    "candidate_ids",
                    "candidate_order",
                )
                if isinstance(payload.get(key), (list, tuple))
            ),
            (),
        )
        records.append(
            {
                "sequence": record["sequence"],
                "kind": kind,
                "ordered_candidate_ids": [str(item) for item in ordered],
            }
        )
    return tuple(records)


def _json_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


__all__ = [
    "CanonicalReductionAdapter",
    "semantic_state_from_system_state",
    "system_state_from_semantic_state",
]
