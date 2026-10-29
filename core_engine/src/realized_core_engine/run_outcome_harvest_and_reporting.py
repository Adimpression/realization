# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from typing import Any

from realized_core_semantics.applied_model import (
    DiscoveryAudit,
    GainClass,
    PainClass,
    ProposalGovernanceStatus,
    ProposalObject,
    ProposalType,
    RunOutcome,
    SupplementMode,
    json_safe,
)
from realized_core_semantics.normalization import (
    normalize_artifact_type,
    normalize_gain_class,
    normalize_pain_class,
)


def perform_discovery_harvest(self, node) -> DiscoveryAudit:
    """
    High Level Purpose:
        In circumstances like closing a governed run after a root has already been reduced as far as it will go, helps with harvesting bounded reusable residue without letting that secondary pass destabilize the main semantic outcome.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `perform_discovery_harvest(self=controller, node=SemanticNode(id='not-force', semantic_unit='Calculate force from mass=3 and acceleration=4.'))`
        Output: DiscoveryAudit(id='discovery-abc123', node_id='not-force', run_outcome=RunOutcome.COMPLETED, pain_class=PainClass.PAIN, gain_class=GainClass.GAIN)

    Args:
        self: Bound controller instance that owns proposal, artifact, and state operations.
        node: Value for `node` used by `perform_discovery_harvest`.

    Returns:
        DiscoveryAudit: Result produced by `perform_discovery_harvest`.
    """
    self.use_capability("discovery_harvest", node=node, contribution="extract bounded reusable residue from the completed encounter")
    try:
        proposal = self.propose_discovery_audit(node)
    except Exception as exc:
        payload = self.fallback_discovery_audit(node)
        proposal = ProposalObject(
            id=self.runtime_make_id("proposal", ProposalType.DISCOVERY_AUDIT.value),
            proposal_type=ProposalType.DISCOVERY_AUDIT,
            target_scope=node.semantic_unit,
            originating_not_id=node.id,
            mode=SupplementMode.DEEP,
            prompt_state_reference=self.build_prompt_state_reference(node),
            revision_count=self.state.next_proposal_revision(ProposalType.DISCOVERY_AUDIT, node.id),
            governance_status=ProposalGovernanceStatus.SUGGESTED,
            payload=payload,
            source="heuristic",
            provider=self.llm.provider,
            model=self.llm.model_for_mode(SupplementMode.DEEP),
            rationale=str(exc),
        )
        self.state.register_proposal(proposal)
        self.admit_proposal(
            proposal,
            rationale="Discovery harvest fell back to bounded local extraction when the supplement path was unavailable.",
        )
        self.state.record_step(
            kind="llm_fallback",
            node_id=node.id,
            intent="Fall back cleanly when discovery supplementation is unavailable or times out.",
            action="fallback for DiscoveryAuditProposal",
            result="heuristic discovery audit used",
            evaluation="developmental harvest remained bounded and available despite supplement failure",
            payload={"proposal_id": proposal.id, "error": str(exc)},
        )
    artifact_ids: list[str] = []
    rejected_titles: list[str] = []
    immediate_learning_ids: list[str] = []
    immediate_learning_units: list[dict[str, Any]] = []
    artifacts_payload = self.proposal_mapping_list(proposal.payload, "artifacts")
    derived_payloads = self.derived_discovery_artifact_payloads(node)
    if derived_payloads:
        existing_signatures = {
            (
                normalize_artifact_type(item.get("artifact_type", "knowledge")),
                str(item.get("title", "")).strip().lower(),
            )
            for item in artifacts_payload
        }
        prepend: list[dict[str, Any]] = []
        for item in derived_payloads:
            signature = (
                normalize_artifact_type(item.get("artifact_type", "knowledge")),
                str(item.get("title", "")).strip().lower(),
            )
            if signature not in existing_signatures:
                prepend.append(item)
        if prepend:
            artifacts_payload = prepend + artifacts_payload
    for candidate in artifacts_payload[:3]:
        artifact = self.build_artifact_from_payload(
            node=node,
            payload=candidate,
            provenance=[proposal.id, node.id],
        )
        if artifact is None:
            rejected_titles.append(str(candidate.get("title", candidate.get("artifact_type", "artifact"))))
            continue
        artifact_ids.append(artifact.id)

    immediate_learning_payloads = self.proposal_mapping_list(proposal.payload, "immediate_learning")
    immediate_learning_proposal: ProposalObject | None = None
    try:
        immediate_learning_proposal = self.propose_immediate_learning(node)
    except Exception as exc:
        immediate_learning_proposal = ProposalObject(
            id=self.runtime_make_id("proposal", ProposalType.IMMEDIATE_LEARNING.value),
            proposal_type=ProposalType.IMMEDIATE_LEARNING,
            target_scope=node.semantic_unit,
            originating_not_id=node.id,
            mode=SupplementMode.DEEP,
            prompt_state_reference=self.build_prompt_state_reference(node),
            revision_count=self.state.next_proposal_revision(ProposalType.IMMEDIATE_LEARNING, node.id),
            governance_status=ProposalGovernanceStatus.SUGGESTED,
            payload=self.fallback_immediate_learning(node),
            source="heuristic",
            provider=self.llm.provider,
            model=self.llm.model_for_mode(SupplementMode.DEEP),
            rationale=str(exc),
        )
        self.state.register_proposal(immediate_learning_proposal)
        self.admit_proposal(
            immediate_learning_proposal,
            rationale="Adjacent-learning expansion fell back to an empty bounded result when the supplement path was unavailable.",
        )
        self.state.record_step(
            kind="llm_fallback",
            node_id=node.id,
            intent="Fall back cleanly when adjacent-learning supplementation is unavailable or malformed.",
            action="fallback for ImmediateLearningProposal",
            result="heuristic adjacent-learning proposal used",
            evaluation="bounded discovery expansion remained optional rather than destabilizing the run",
            payload={"proposal_id": immediate_learning_proposal.id, "error": str(exc)},
        )
    immediate_learning_payloads.extend(
        self.proposal_mapping_list(
            immediate_learning_proposal.payload if immediate_learning_proposal is not None else {},
            "immediate_learning",
        )
    )
    deduped_learning_payloads: list[dict[str, Any]] = []
    seen_learning_units: set[str] = set()
    for candidate in immediate_learning_payloads:
        semantic_key = str(candidate.get("semantic_unit") or candidate.get("question") or "").strip().lower()
        if not semantic_key or semantic_key in seen_learning_units:
            continue
        deduped_learning_payloads.append(candidate)
        seen_learning_units.add(semantic_key)
    immediate_learning_payloads = deduped_learning_payloads
    if immediate_learning_payloads:
        self.use_capability(
            "immediate_learning",
            node=node,
            contribution="harvest a very small set of adjacent learn-now items so nearby future runs have stronger reusable support",
        )
    for candidate in immediate_learning_payloads[:3]:
        semantic_unit = str(candidate.get("semantic_unit") or candidate.get("question") or "").strip()
        why_now = str(candidate.get("why_now") or candidate.get("justification") or "").strip()
        artifact = self.build_immediate_learning_artifact(
            node=node,
            payload=candidate,
            related_artifact_ids=artifact_ids[:6],
            provenance=[proposal.id, node.id],
        )
        unit_record = {
            "semantic_unit": semantic_unit,
            "encountered_not": str(candidate.get("encountered_not", "")).strip(),
            "why_now": why_now,
            "component_nots": [
                str(item).strip()
                for item in candidate.get("component_nots", [])
                if str(item).strip()
            ] if isinstance(candidate.get("component_nots", []), list) else [],
            "composed_not": str(candidate.get("composed_not", "")).strip(),
            "answer": str(candidate.get("answer", "")).strip(),
        }
        if artifact is None:
            rejected_titles.append(semantic_unit or str(candidate.get("title", "immediate_learning")))
            unit_record["stored"] = False
            immediate_learning_units.append(unit_record)
            continue
        artifact_ids.append(artifact.id)
        immediate_learning_ids.append(artifact.id)
        unit_record["stored"] = True
        unit_record["artifact_id"] = artifact.id
        immediate_learning_units.append(unit_record)

    structured_learning_artifact = self.build_structured_learning_artifact(
        node=node,
        related_artifact_ids=artifact_ids,
    )
    if structured_learning_artifact is not None and structured_learning_artifact.id not in artifact_ids:
        artifact_ids.append(structured_learning_artifact.id)

    gain_types = [self.state.artifacts[artifact_id].artifact_type for artifact_id in artifact_ids if artifact_id in self.state.artifacts]
    gain_class = normalize_gain_class(
        proposal.payload.get("gain_class", GainClass.GAIN if artifact_ids else GainClass.NO_GAIN),
        default=GainClass.GAIN if artifact_ids else GainClass.NO_GAIN,
    )
    if artifact_ids and gain_class == GainClass.NO_GAIN:
        gain_class = GainClass.GAIN

    audit = DiscoveryAudit(
        id=self.runtime_make_id("discovery", node.semantic_unit),
        node_id=node.id,
        run_outcome=self.state.run_outcome,
        pain_class=normalize_pain_class(proposal.payload.get("pain_class", PainClass.PAIN), default=PainClass.PAIN),
        gain_class=gain_class,
        gain_types=sorted(set(gain_types or [normalize_artifact_type(item) for item in proposal.payload.get("gain_types", [])])),
        enablers=self.proposal_list(proposal.payload, "enablers"),
        diagnostics=self.proposal_list(proposal.payload, "diagnostics") + [f"rejected_artifact:{title}" for title in rejected_titles],
        artifact_ids=artifact_ids,
        immediate_learning_ids=immediate_learning_ids,
        immediate_learning_units=immediate_learning_units,
        provenance=[proposal.id, node.id],
    )
    self.state.register_discovery_audit(audit)
    self.state.record_outlet(
        kind="artifact_manifest",
        semantic_identity=node.semantic_unit,
        payload={
            "node_id": node.id,
            "audit_id": audit.id,
            "pain_class": audit.pain_class,
            "gain_class": audit.gain_class,
            "gain_types": audit.gain_types,
            "artifact_ids": audit.artifact_ids,
            "immediate_learning_ids": audit.immediate_learning_ids,
        },
        provenance=[audit.id, *artifact_ids],
    )
    return audit


def persist_artifacts(self) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like ending a governed run after artifacts were admitted in memory, helps with performing the best-effort external store persistence pass without letting that write become part of the semantic decision itself.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `persist_artifacts(self=controller)`
        Output: {'status': 'persisted', 'artifact_count': 12}

    Args:
        self: Bound controller instance that owns artifact persistence and state logging.

    Returns:
        dict[str, Any]: Result produced by `persist_artifacts`.
    """
    self.use_capability("artifact_persistence", node=self.state.root(), contribution="persist typed artifacts to the configured state store when available")
    report = self.artifact_store.persist(self.state)
    self.state.artifact_persistence.append(json_safe(report))
    self.state.record_step(
        kind="artifact_persistence",
        node_id=self.state.root_id,
        intent="Persist admitted artifacts for reuse beyond the current in-memory run when a configured store is available.",
        action="persist discovery artifacts",
        result=report.get("status", "skipped"),
        evaluation="artifact persistence remained best-effort and did not overturn the governed run result",
        payload=report,
    )
    return report


def emit_trace_report(self) -> None:
    """
    High Level Purpose:
        In circumstances like closing a run that should leave behind a bounded causal explanation, helps with emitting the final trace outlet without changing the semantic closure state itself.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `emit_trace_report(self=controller)`
        Output: None

    Args:
        self: Bound controller instance that owns explanation drafting and outlet recording.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    self.use_capability("trace_reporting", node=self.state.root(), contribution="emit recoverable causal trace")
    explanation = self.propose_explanation_draft(self.state.root())
    last_commitment = next(
        (record for record in reversed(self.state.ledger) if record.kind == "commitment"),
        None,
    )
    latest_audit = max(self.state.discovery_audits.values(), key=lambda item: item.created_at) if self.state.discovery_audits else None
    payload = {
        "run_id": self.state.run_id,
        "root_id": self.state.root_id,
        "recent_steps": [record.to_dict() for record in self.state.ledger[-8:]],
        "last_commitment": last_commitment.to_dict() if last_commitment is not None else None,
        "explanation_draft": explanation.payload,
        "explanation_proposal_id": explanation.id,
        "latest_discovery_audit": latest_audit.to_dict() if latest_audit is not None else None,
    }
    self.state.record_outlet(
        kind="trace_report",
        semantic_identity=self.state.root().semantic_unit,
        payload=payload,
        provenance=[self.state.root_id, explanation.id],
    )


def finalize_run(self) -> None:
    """
    High Level Purpose:
        In circumstances like finishing the governed reduction loop for the root non-achievedness, helps with classifying the final run outcome and then performing bounded harvest, persistence, and reporting as non-authoritative follow-on work.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `finalize_run(self=controller)`
        Output: None

    Args:
        self: Bound controller instance that owns propagation, commitment, harvest, persistence, and reporting seams.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    root = self.state.root()
    self.propagate([root])
    if self.is_committable(root):
        self.commit_closure(root)
    self.refresh_frontier()

    if self.is_closed(root):
        outcome = RunOutcome.COMPLETED
    elif root.id in self.state.paused or any(node_id in self.state.paused for node_id in self.ancestor_node_ids(root.id) + [root.id]):
        outcome = RunOutcome.PAUSED
    elif root.id in self.state.incomplete or not self.state.frontier:
        outcome = RunOutcome.INCOMPLETE
    else:
        outcome = RunOutcome.ONGOING

    self.state.run_outcome = outcome
    if self.discovery_enabled():
        try:
            self.perform_discovery_harvest(root)
        except Exception as exc:
            self.state.record_step(
                kind="discovery_audit_failure",
                node_id=root.id,
                intent="Keep bounded harvest failures from overturning the governed run outcome.",
                action="attempt discovery harvest",
                result="discovery harvest failed",
                evaluation="core run state was preserved even though developmental harvest could not be completed",
                payload={"error": str(exc)},
            )
    else:
        self.state.record_step(
            kind="discovery_skipped",
            node_id=root.id,
            intent="Honor the controller feature policy for discovery harvest.",
            action="skip discovery harvest",
            result="discovery disabled",
            evaluation="bounded discovery harvest remained off by controller configuration",
        )
    try:
        self.persist_artifacts()
    except Exception as exc:
        self.state.record_step(
            kind="artifact_persistence_failure",
            node_id=root.id,
            intent="Keep persistence failures from overturning the governed run outcome.",
            action="attempt artifact persistence",
            result="artifact persistence failed",
            evaluation="artifacts remained in durable state even though the external store write did not complete",
            payload={"error": str(exc)},
        )
    try:
        self.emit_trace_report()
    except Exception as exc:
        self.state.record_step(
            kind="trace_report_failure",
            node_id=root.id,
            intent="Keep non-authoritative reporting failures from overturning the governed run outcome.",
            action="attempt trace report",
            result="trace report emission failed",
            evaluation="core run state was preserved even though a secondary explanation artifact was unavailable",
            payload={"error": str(exc)},
        )
    self.state.record_step(
        kind="run_outcome",
        node_id=root.id,
        intent="Summarize the bounded run outcome under current conditions.",
        action="finalize run",
        result=outcome.value,
        evaluation="run ended according to closure, pause, or incompletion conditions",
    )
