# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping

from applied_theory_types import (
    Commitment,
    NodeStatus,
    PauseBoundary,
    PausePoint,
    Product,
    ProposedCommitment,
    SemanticNode,
    SupportScore,
    SupportView,
    ThreeLevel,
)
from normalization_primitives import normalize_pause_boundary
from semantic_text import collapse_ws
from title_semantics import derive_semantic_title_depth_view


def should_pause(self, node: SemanticNode) -> bool:
    """
    High Level Purpose:
        In circumstances like governed recursive reduction where a node may need to stop and wait for a boundary return instead of drifting into false closure, helps with deciding whether the active node should commit to pause.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `should_pause(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: True

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `should_pause`. Expected type: `SemanticNode`.

    Returns:
        bool: Result produced by `should_pause`.
    """
    if node.id in self.state.paused:
        return True
    if self.prior_learning_fast_path_ready(node):
        return False
    if self.is_closed(node) or self.is_committable(node):
        return False

    children = self.refinement_children(node)
    control = self.control_decision_payload(node)
    if self.proposal_flag(control, "should_decompose", default=self.fallback_control_decision(node)["should_decompose"]) and not children and self.structural_can_decompose(node):
        return False

    open_children = [child for child in children if self.state.node_status(child.id) == NodeStatus.OPEN]
    if open_children:
        return False

    if node.decomposition_mode == "OR" and any(self.child_is_satisfied(child) for child in children):
        return False

    return self.proposal_flag(
        control,
        "should_pause",
        default=self.fallback_control_decision(node)["should_pause"],
    )


def needs_reframing(self, node: SemanticNode) -> bool:
    """
    High Level Purpose:
        In circumstances like governed recursive reduction where the current node cannot be completed faithfully inside its present framing, helps with deciding whether the runtime should zoom out and reframe upward.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `needs_reframing(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: True

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `needs_reframing`. Expected type: `SemanticNode`.

    Returns:
        bool: Result produced by `needs_reframing`.
    """
    if self.prior_learning_fast_path_ready(node):
        return False
    if not self.can_reframe_within_decomposition(node):
        return False
    if node.metadata.get("force_reframe"):
        return True
    control = self.control_decision_payload(node)
    return self.proposal_flag(
        control,
        "needs_reframe",
        default=self.fallback_control_decision(node)["needs_reframe"],
    )


def pause_boundary_for(self, node: SemanticNode) -> tuple[PauseBoundary, bool]:
    """
    High Level Purpose:
        In circumstances like committing a governed pause, helps with determining the required boundary and whether external retrieval must accompany the pause.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `pause_boundary_for(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: (PauseBoundary.RESUME_SIGNAL, False)

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `pause_boundary_for`. Expected type: `SemanticNode`.

    Returns:
        tuple[PauseBoundary, bool]: Result produced by `pause_boundary_for`.
    """
    control = self.control_decision_payload(node)
    fallback_boundary, fallback_needs_retrieval = self.fallback_pause_boundary(node)
    should_pause_flag = self.proposal_flag(
        control,
        "should_pause",
        default=self.fallback_control_decision(node)["should_pause"],
    )
    if not should_pause_flag and node.id not in self.state.paused:
        return PauseBoundary.RESUME_SIGNAL, False
    boundary = normalize_pause_boundary(
        self.proposal_text(control, "required_boundary", default=fallback_boundary),
        default=fallback_boundary,
    )
    needs_retrieval = self.proposal_flag(
        control,
        "needs_retrieval",
        default=fallback_needs_retrieval,
    )
    return boundary, needs_retrieval


def pause_reason(self, node: SemanticNode) -> str:
    """
    High Level Purpose:
        In circumstances like committing a governed pause point, helps with recovering the bounded reason surface that explains why reduction cannot continue yet.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `pause_reason(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: 'Need a confirming measurement before continuing.'

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `pause_reason`. Expected type: `SemanticNode`.

    Returns:
        str: Result produced by `pause_reason`.
    """
    control = self.control_decision_payload(node)
    should_pause_flag = self.proposal_flag(
        control,
        "should_pause",
        default=self.fallback_control_decision(node)["should_pause"],
    )
    if not should_pause_flag and node.id not in self.state.paused:
        return ""
    reason = str(control.get("pause_reason", "")).strip()
    if reason:
        return reason
    return self.fallback_pause_reason(node)


def commit_closure(self, node: SemanticNode) -> Commitment:
    """
    High Level Purpose:
        In circumstances like governed reduction reaching justified achievedness, helps with converting supported closure into durable committed state and materializing the root product when needed.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `commit_closure(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: Commitment(id='commit-physics-force', node_id='not-force', certainty=<ThreeLevel.HIGH: 'high'>, justification='Evidence and governance jointly justified closure of not-force.', evidence_ids=[])

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `commit_closure`. Expected type: `SemanticNode`.

    Returns:
        Commitment: Result produced by `commit_closure`.
    """
    if node.id in self.state.closed:
        existing = next(commitment for commitment in self.state.commitments.values() if commitment.node_id == node.id)
        return existing

    self.use_capability("closure_commitment", node=node, contribution="convert justified achievedness into durable commitment")
    support = self.state.support.get(node.id, SupportView([], [], SupportScore.VERY_BAD))
    relevant_claim_ids = [
        claim.id
        for claim in self.state.claims.values()
        if claim.node_id == node.id or claim.evidence_id in set(support.direct + support.upstream)
    ]
    proposed = ProposedCommitment(
        id=self.runtime_make_id("proposal", node.semantic_unit),
        node_id=node.id,
        claim_ids=relevant_claim_ids,
        evidence_ids=list(dict.fromkeys(support.direct + support.upstream)),
        justification=f"Proposed closure for {node.not_label} under current evidence and governance.",
        accepted=True,
        provenance=[node.id, *relevant_claim_ids],
    )
    self.state.proposed_commitments[proposed.id] = proposed
    self.state.register_ontology(
        entity_id=proposed.id,
        kind="proposed_commitment",
        semantic_identity=node.semantic_unit,
        authoritative_ref=proposed.id,
        working_semantics={"node_id": node.id, "accepted": proposed.accepted},
        embedded_refs=proposed.provenance,
    )
    self.state.record_step(
        kind="proposed_commitment",
        node_id=node.id,
        intent="Preserve the distinction between supported claim and committed achievedness.",
        action="assemble proposed commitment",
        result="proposed commitment recorded",
        evaluation="closure remained evidence-led rather than narratively asserted",
        payload={"proposal_id": proposed.id, "claim_ids": proposed.claim_ids},
    )
    commitment = Commitment(
        id=self.runtime_make_id("commit", node.semantic_unit),
        node_id=node.id,
        certainty=self.state.certainty.get(node.id, ThreeLevel.LOW),
        justification=f"Evidence and governance jointly justified closure of {node.not_label}.",
        evidence_ids=list(dict.fromkeys(support.direct + support.upstream)),
    )
    self.state.commitments[commitment.id] = commitment
    self.state.closed.add(node.id)
    self.state.paused.discard(node.id)
    self.state.incomplete.discard(node.id)
    self.state.frontier.discard(node.id)
    self.state.status[node.id] = NodeStatus.CLOSED
    self.state.provenance_links.setdefault(node.id, []).append(commitment.id)
    self.state.register_ontology(
        entity_id=commitment.id,
        kind="commitment",
        semantic_identity=node.semantic_unit,
        authoritative_ref=commitment.id,
        working_semantics={"node_id": node.id, "certainty": commitment.certainty},
        embedded_refs=[proposed.id, *commitment.evidence_ids],
    )
    self.state.record_step(
        kind="commitment",
        node_id=node.id,
        intent="Commit closure only where certainty is justified by evidence under governance.",
        action="commit achievedness closure",
        result="node closed",
        evaluation="closure was admitted as durable committed state",
        commit_effect=commitment.id,
        payload={"certainty": commitment.certainty, "evidence_ids": commitment.evidence_ids},
    )
    self.state.record_outlet(
        kind="commitment_expression",
        semantic_identity=node.semantic_unit,
        payload={"node_id": node.id, "commitment_id": commitment.id, "certainty": commitment.certainty},
        provenance=[commitment.id],
    )
    if node.id == self.state.root_id:
        self.materialize_root_product(node, commitment)
    return commitment


def materialize_root_product(self, node: SemanticNode, commitment: Commitment) -> Product:
    """
    High Level Purpose:
        In circumstances like root-level closure, helps with materializing the final committed product surface that downstream reporting and offline runs expose as the run result.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `materialize_root_product(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), commitment=Commitment(id='commit-physics-force', node_id='not-force', certainty=<ThreeLevel.HIGH: 'high'>, justification='Evidence and governance jointly justified closure of not-force.', evidence_ids=[]))`
        Output: Product(id='product-physics-force', node_id='not-force', committed=True, provenance=['commit-physics-force'], content={'semantic_unit': 'Physics / Force', 'commitment_id': 'commit-physics-force', 'certainty': <ThreeLevel.HIGH: 'high'>, 'witness': 'artifact remains secondary to justified achievedness', 'answer': ''})

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `materialize_root_product`. Expected type: `SemanticNode`.
        commitment: Value for `commitment` used by `materialize_root_product`. Expected type: `Commitment`.

    Returns:
        Product: Result produced by `materialize_root_product`.
    """
    existing = next((product for product in self.state.products.values() if product.node_id == node.id), None)
    if existing:
        return existing
    _refresh_split_root_structured_title_from_children(self, node)
    answer = str(node.metadata.get("direct_resolution_answer", "")).strip()
    if not answer:
        answer = _compose_root_answer_from_closed_children(self, node)
    product = Product(
        id=self.runtime_make_id("product", node.semantic_unit),
        node_id=node.id,
        committed=True,
        provenance=[commitment.id],
        content={
            "semantic_unit": node.semantic_unit,
            "commitment_id": commitment.id,
            "certainty": commitment.certainty,
            "witness": "artifact remains secondary to justified achievedness",
            "answer": answer,
        },
    )
    self.state.products[product.id] = product
    self.state.register_ontology(
        entity_id=product.id,
        kind="product",
        semantic_identity=node.semantic_unit,
        authoritative_ref=product.id,
        working_semantics={"node_id": node.id, "committed": product.committed},
        embedded_refs=product.provenance,
    )
    self.state.record_outlet(
        kind="product",
        semantic_identity=node.semantic_unit,
        payload={"node_id": node.id, "product_id": product.id, "commitment_id": commitment.id},
        provenance=[product.id, commitment.id],
    )
    return product


def _compose_root_answer_from_closed_children(self, node: SemanticNode) -> str:
    """
    High Level Purpose:
        In circumstances like root-level closure reached by closing multiple decomposed children, helps with composing one user-facing root answer from the committed child answers instead of leaving the root product blank.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `_compose_root_answer_from_closed_children(self=controller, node=SemanticNode(id='root-cylinder', semantic_unit='Cylinder measures'))`
        Output: 'Total Surface Area Of A Cylinder: 150.79; Volume Of A Cylinder: 141.37'

    Args:
        self: Bound instance that owns refinement-child access.
        node: Value for `node` used by `_compose_root_answer_from_closed_children`. Expected type: `SemanticNode`.

    Returns:
        str: Result produced by `_compose_root_answer_from_closed_children`.
    """
    parts: list[str] = []
    for child in self.refinement_children(node):
        child_answer = collapse_ws(str(child.metadata.get("direct_resolution_answer", "")).strip())
        if not child_answer:
            continue
        child_structured = child.metadata.get("structured_learning", {})
        child_title = ""
        if isinstance(child_structured, Mapping):
            child_title = collapse_ws(str(child_structured.get("title_identity", "")).strip())
        if not child_title:
            child_title = collapse_ws(str(child.semantic_unit or "").strip())
        child_label = collapse_ws(child_title.rsplit("/", 1)[-1].strip()) or child_title
        parts.append(f"{child_label}: {child_answer}")
    return "; ".join(parts)


def _refresh_split_root_structured_title_from_children(self, node: SemanticNode) -> None:
    """
    High Level Purpose:
        In circumstances like split-result root closure where the children expose the determinate leaf titles clearly but the root still carries the raw prompt surface, helps with grounding the root back into the shared slash-bearing family title before final product materialization.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `_refresh_split_root_structured_title_from_children(self=controller, node=SemanticNode(id='root-cylinder', semantic_unit='Break this down carefully...'))`
        Output: None

    Args:
        self: Bound instance that owns reusable-family grounding helpers.
        node: Value for `node` used by `_refresh_split_root_structured_title_from_children`. Expected type: `SemanticNode`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    structured = node.metadata.get("structured_learning", {})
    not_elaboration = node.metadata.get("not_elaboration", {})
    split_needed = bool(isinstance(structured, Mapping) and structured.get("title_depth_body_split_needed", False)) or bool(
        isinstance(not_elaboration, Mapping) and not_elaboration.get("title_depth_body_split_needed", False)
    )
    if not split_needed:
        return
    child_titles: list[str] = []
    for child in self.refinement_children(node):
        child_structured = child.metadata.get("structured_learning", {})
        if isinstance(child_structured, Mapping):
            child_title = collapse_ws(str(child_structured.get("title_identity", "")).strip())
            if child_title:
                child_titles.append(child_title)
    direct_parent_titles = {
        " / ".join(title_view.get("segments", [])[:-1]).strip()
        for title in child_titles
        for title_view in [derive_semantic_title_depth_view(title)]
        if len(title_view.get("segments", [])) >= 2 and " / ".join(title_view.get("segments", [])[:-1]).strip()
    }
    family_title = next(iter(direct_parent_titles)) if len(direct_parent_titles) == 1 else self.shared_reusable_family_title(child_titles)
    if not family_title:
        return
    title_view = derive_semantic_title_depth_view(family_title)
    for metadata_key in ("structured_learning", "not_elaboration"):
        current = node.metadata.get(metadata_key, {})
        if not isinstance(current, Mapping):
            continue
        updated = dict(current)
        updated["title_identity"] = family_title
        updated["title_depth_segments"] = list(title_view.get("segments", []))
        updated["title_depth_prefixes"] = list(title_view.get("prefixes", []))
        updated["title_depth_exposed_depth"] = int(title_view.get("exposed_depth", 0))
        minimal_depth = int(updated.get("title_depth_minimal_sufficient_depth", 0) or 0)
        updated["title_depth_minimal_sufficient_depth"] = max(minimal_depth, int(title_view.get("exposed_depth", 0)))
        node.metadata[metadata_key] = updated


def commit_pause(self, node: SemanticNode) -> PausePoint:
    """
    High Level Purpose:
        In circumstances like governed reduction reaching a justified wait boundary, helps with committing the pause state and emitting the boundary-facing retrieval or notification artifacts that allow later resumption.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `commit_pause(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: PausePoint(id='pause-physics-force', node_id='not-force', reason='Need confirming evidence.', required_boundary=<PauseBoundary.EXTERNAL_EVIDENCE: 'external_evidence'>)

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `commit_pause`. Expected type: `SemanticNode`.

    Returns:
        PausePoint: Result produced by `commit_pause`.
    """
    if any(blocker.startswith("missing_evidence:") for blocker in self.state.blockers.get(node.id, [])):
        self.ensure_generated_capability(
            node,
            semantic_role=f"support_acquisition:{node.role}",
            affordance=f"support acquisition for {node.semantic_unit}",
            service_axis="evidence",
        )
    reason = self.pause_reason(node)
    uncertainty = self.propose_uncertainty_assessment(node)
    required_boundary, needs_retrieval = self.pause_boundary_for(node)
    retrieval_plan = None
    if needs_retrieval:
        retrieval_plan = self.propose_retrieval_plan(node)
    pause_point = PausePoint(
        id=self.runtime_make_id("pause", node.semantic_unit),
        node_id=node.id,
        reason=reason,
        required_boundary=required_boundary,
    )
    self.state.pause_points[pause_point.id] = pause_point
    self.state.waits[pause_point.id] = pause_point
    self.state.paused.add(node.id)
    self.state.frontier.discard(node.id)
    self.state.status[node.id] = NodeStatus.PAUSED
    self.state.register_ontology(
        entity_id=pause_point.id,
        kind="wait",
        semantic_identity=node.semantic_unit,
        authoritative_ref=pause_point.id,
        working_semantics={"node_id": node.id, "required_boundary": pause_point.required_boundary},
        embedded_refs=[node.id],
    )
    self.state.record_step(
        kind="pause",
        node_id=node.id,
        intent="Pause coherently when justified continuation depends on a boundary return.",
        action="commit governed pause point",
        result="node paused",
        evaluation="reduction can resume later without semantic rupture",
        commit_effect=pause_point.id,
        payload={"reason": reason, "required_boundary": pause_point.required_boundary},
    )
    self.state.record_outlet(
        kind="state_notification",
        semantic_identity=node.semantic_unit,
        payload={"node_id": node.id, "status": "paused", "reason": reason},
        provenance=[pause_point.id],
    )
    if retrieval_plan is not None:
        self.state.record_outlet(
            kind="question",
            semantic_identity=node.semantic_unit,
            payload={
                "node_id": node.id,
                "queries": retrieval_plan.payload.get("retrieval_queries", []),
                "source_classes": retrieval_plan.payload.get("source_classes", []),
                "uncertainty_loci": uncertainty.payload.get("uncertainty_loci", []),
            },
            provenance=[pause_point.id, retrieval_plan.id, uncertainty.id],
        )
    return pause_point


def commit_incompletion(self, node: SemanticNode) -> None:
    """
    High Level Purpose:
        In circumstances like governed reduction finding no justified closure or pause path, helps with committing explicit incompletion instead of allowing false achievedness.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `commit_incompletion(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: None

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `commit_incompletion`. Expected type: `SemanticNode`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    if node.id in self.state.incomplete:
        return
    self.state.incomplete.add(node.id)
    self.state.paused.discard(node.id)
    self.state.frontier.discard(node.id)
    self.state.status[node.id] = NodeStatus.INCOMPLETE
    self.state.record_step(
        kind="incompletion",
        node_id=node.id,
        intent="Prefer explicit incompletion to false achievedness.",
        action="commit justified incompletion",
        result="node marked incomplete",
        evaluation="no faithful or evidenced continuation was justified at this stage",
    )


def is_committable(self, node: SemanticNode) -> bool:
    """
    High Level Purpose:
        In circumstances like governed reduction deciding whether a node may close now, helps with applying the controller’s commitment law over support, conflicts, blockers, and child satisfaction.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `is_committable(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: True

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `is_committable`. Expected type: `SemanticNode`.

    Returns:
        bool: Result produced by `is_committable`.
    """
    if self.prior_learning_fast_path_ready(node):
        if self.state.conflicts.get(node.id):
            return False
        if self.has_open_blockers(node):
            return False
        return self.support_is_sufficient(node)
    if self.is_inadmissible(node):
        return False
    if self.state.conflicts.get(node.id):
        return False
    if self.has_open_blockers(node):
        return False
    if node.metadata.get("direct_resolution_ready_for_commitment") and self.support_is_sufficient(node):
        return True
    assessment = self.node_assessment_payload(node)
    if not self.proposal_flag(
        assessment,
        "ready_for_commitment",
        default=self.fallback_node_assessment(node)["ready_for_commitment"],
    ):
        return False

    children = self.refinement_children(node)
    if not children:
        return self.support_is_sufficient(node)
    if node.decomposition_mode == "AND":
        if not all(self.child_is_satisfied(child) for child in children if child.required):
            return False
    elif node.decomposition_mode == "OR":
        if not any(self.child_is_satisfied(child) for child in children):
            return False
    return self.support_is_sufficient(node)
