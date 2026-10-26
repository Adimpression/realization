# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Iterable

from realized_host_interaction.context import host_interaction_descriptor_payload
from realized_core_runtime import resume_to_realization, run_to_realization

from applied_theory_types import (
    BoundaryShapeTerm,
    DecompositionMode,
    EdgeType,
    NodeStatus,
    PriorityLevel,
    ProposalType,
    Result,
    SemanticNode,
)
from normalization_primitives import (
    normalize_boundary_shape,
    normalize_closure_rule,
    normalize_decomposition_mode,
    normalize_priority,
)
from semantic_text import (
    collapse_ws,
    ordered_unique,
    semantic_bearing_level,
    semantic_chain_decomposition_components,
    semantic_requested_output_phrases,
    titleize_semantic_unit,
)
from semantic_prompt_posture import semantic_prompt_directive_profile
from system_state import SystemState
from title_semantics import (
    classify_title_depth_relation,
    derive_semantic_title_depth_segments,
    normalize_semantic_title_identity,
    semantic_namespace_key,
    structured_title_identity_text,
    title_depth_theory_prompt_block,
)


def run(self, *, max_steps: int = 256) -> SystemState:
    """
    High Level Purpose:
        In circumstances like governed frontier execution over recursive semantic reduction, helps with driving the top-level run loop while preserving the current recursive reduction behavior.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `run(max_steps=3)`
        Output: SystemState.bootstrap(prompt='Compute force from mass and acceleration.')

    Args:
        self: Bound instance that owns the runtime state used by this method.
        max_steps: Value for `max_steps` used by `run`. Expected type: `int`. Defaults to `256`.

    Returns:
        SystemState: Result produced by `run`.
    """
    return run_to_realization(self, max_steps=max_steps)


def runtime_host_interaction_context_payload(self) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed semantic runtime execution against a pluggable host backend, helps with projecting the active host-interaction context into one stable runtime payload.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by letting the same reduction runtime describe whether it is executing against a host-native or workstation-backed interaction surface without importing workstation code.

    Example Input Output:
        Input: `runtime_host_interaction_context_payload()`
        Output: {'backend_kind': 'host', 'attachments': [], 'allowed_capabilities': [], 'metadata': {}}

    Args:
        self: Bound instance that owns the runtime state used by this method.

    Returns:
        dict[str, Any]: Result produced by `runtime_host_interaction_context_payload`.
    """
    descriptor_callable = getattr(self, "describe_host_interaction_context", None)
    if callable(descriptor_callable):
        descriptor = descriptor_callable()
        if isinstance(descriptor, Mapping):
            return dict(descriptor)
        return host_interaction_descriptor_payload(descriptor)
    return host_interaction_descriptor_payload(None)


def resume(self, *, max_steps: int = 256) -> SystemState:
    """
    High Level Purpose:
        In circumstances like resuming a partially governed semantic run, helps with reopening eligible nodes and re-entering the same recursive runtime loop without changing the control shape.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `resume(max_steps=3)`
        Output: SystemState.bootstrap(prompt='Compute force from mass and acceleration.')

    Args:
        self: Bound instance that owns the runtime state used by this method.
        max_steps: Value for `max_steps` used by `resume`. Expected type: `int`. Defaults to `256`.

    Returns:
        SystemState: Result produced by `resume`.
    """
    return resume_to_realization(
        self,
        open_status=NodeStatus.OPEN,
        max_steps=max_steps,
    )


def pop_best_frontier(self) -> SemanticNode | None:
    """
    High Level Purpose:
        In circumstances like governed frontier stepping, helps with choosing the next active node while preserving the existing candidate ordering and proposal-based selection behavior.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `pop_best_frontier()`
        Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

    Args:
        self: Bound instance that owns the runtime state used by this method.

    Returns:
        SemanticNode | None: Result produced by `pop_best_frontier`.
    """
    candidates = [self.state.graph.get_node(node_id) for node_id in self.state.frontier if node_id in self.state.graph.nodes]
    candidates = [node for node in candidates if not self.is_terminal(node)]
    if not candidates:
        self.state.frontier.clear()
        return None
    candidates = sorted(candidates, key=lambda item: (item.depth, item.semantic_unit.lower(), item.id))
    proposal = self.propose_candidate_selection(
        context_node=self.state.root(),
        candidates=candidates,
        selection_kind="frontier selection",
    )
    ordered = self.normalize_candidate_order(
        candidates,
        self.proposal_list(proposal.payload, "ordered_candidate_ids") if proposal is not None else [],
    )
    selected_id = self.proposal_text(proposal.payload, "selected_candidate_id") if proposal is not None else ""
    best = next((candidate for candidate in ordered if candidate.id == selected_id), ordered[0])
    self.state.frontier.discard(best.id)
    best.metadata["frontier_selection_proposal_id"] = proposal.id if proposal is not None else ""
    best.metadata["frontier_candidate_order"] = [candidate.id for candidate in ordered]
    return best


def refresh_frontier(self) -> None:
    """
    High Level Purpose:
        In circumstances like re-stabilizing the governed runtime after local semantic change, helps with rebuilding the frontier from current node statuses without changing the recursive reduction behavior.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `refresh_frontier()`
        Output: None

    Args:
        self: Bound instance that owns the runtime state used by this method.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    refreshed: set[str] = set()
    for node in self.state.graph.nodes.values():
        status = self.state.node_status(node.id)
        if status in {NodeStatus.OPEN, NodeStatus.BLOCKED, NodeStatus.CLOSABLE}:
            refreshed.add(node.id)
    if self.state.root_id not in self.state.closed:
        refreshed.add(self.state.root_id)
    refreshed -= self.state.closed
    refreshed -= self.state.paused
    refreshed -= self.state.incomplete
    refreshed -= self.state.inadmissible
    self.state.frontier = refreshed


def reduce_not(self, node: SemanticNode, visiting: set[str] | None = None) -> Result:
    """
    High Level Purpose:
        In circumstances like recursive semantic descent under governed reduction, helps with reducing one active non-achievedness while preserving recursive child-first reduction and closure timing.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `reduce_not(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), visiting={'not-root'})`
        Output: Result.CLOSED

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `reduce_not`. Expected type: `SemanticNode`.
        visiting: Value for `visiting` used by `reduce_not`. Expected type: `set[str] | None`. Defaults to `None`.

    Returns:
        Result: Result produced by `reduce_not`.
    """
    if visiting is None:
        visiting = set()

    self.propagate([node])

    if node.id in visiting:
        return Result.DEFERRED
    if self.is_closed(node):
        return Result.CLOSED
    if self.is_committable(node):
        self.commit_closure(node)
        return Result.CLOSED
    if self.should_pause(node):
        self.commit_pause(node)
        return Result.PAUSED
    if self.needs_reframing(node):
        reframed = self.reframe_upward(node)
        if reframed is None:
            self.commit_incompletion(node)
            return Result.INCOMPLETE
        return self.reduce_not(reframed, visiting)

    visiting.add(node.id)
    try:
        if self.reflection_enabled() and self.should_reflect(node):
            self.reflect(node)
        elif not self.reflection_enabled():
            self.state.record_step(
                kind="reflection_skipped",
                node_id=node.id,
                intent="Honor the controller feature policy for reflection.",
                action="skip reflection",
                result="reflection disabled",
                evaluation="retrospective reflection remained off by controller configuration",
            )
        if self.contemplation_enabled():
            self.contemplate(node)
        else:
            self.state.record_step(
                kind="contemplation_skipped",
                node_id=node.id,
                intent="Honor the controller feature policy for contemplation.",
                action="skip contemplation",
                result="contemplation disabled",
                evaluation="prospective contemplation remained off by controller configuration",
            )

        children = self.decompose_or_refine(node)
        children = self.filter_by_faithfulness(children, node)
        children = self.order_children(children)

        if not children:
            if self.can_refine_directly(node):
                self.refine_directly(node)
                self.propagate([node])

                if self.is_committable(node):
                    self.commit_closure(node)
                    return Result.CLOSED
                if self.should_pause(node):
                    self.commit_pause(node)
                    return Result.PAUSED

            self.commit_incompletion(node)
            return Result.INCOMPLETE

        for child in children:
            child_result = self.reduce_not(child, visiting)
            self.propagate([child, node])

            if self.is_committable(node):
                self.commit_closure(node)
                return Result.CLOSED

            if self.should_pause(node):
                if child_result == Result.CLOSED:
                    continue
                self.commit_pause(node)
                return Result.PAUSED

        if self.is_committable(node):
            self.commit_closure(node)
            return Result.CLOSED

        if self.should_pause(node):
            self.commit_pause(node)
            return Result.PAUSED

        self.commit_incompletion(node)
        return Result.INCOMPLETE
    finally:
        visiting.remove(node.id)


def decompose_or_refine(self, node: SemanticNode) -> list[SemanticNode]:
    """
    High Level Purpose:
        In circumstances like recursive governed decomposition, helps with deciding whether the active item should stay whole or split into subordinate child non-achievednesses.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `decompose_or_refine(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: [SemanticNode(id='not-force-mass', semantic_unit='Physics / Force / Mass'), SemanticNode(id='not-force-acceleration', semantic_unit='Physics / Force / Acceleration')]

    Args:
        self: Bound instance that owns the runtime state used by this method.
        node: Value for `node` used by `decompose_or_refine`. Expected type: `SemanticNode`.

    Returns:
        list[SemanticNode]: Result produced by `decompose_or_refine`.
    """
    self.use_capability("decomposition", node=node, contribution="rewrite non-achievedness into subordinate refinements")
    existing = self.refinement_children(node)
    if existing:
        return existing
    if not self.structural_can_decompose(node):
        return []
    stored_structured = node.metadata.get("structured_learning", {})
    if isinstance(stored_structured, Mapping) and str(stored_structured.get("encountered_not", "")).strip():
        structured = dict(stored_structured)
    else:
        structured = self.ensure_not_elaboration(node)

    specs: list[dict[str, Any]] = []
    anchor = node.semantic_unit
    component_nots = [
        str(item).strip()
        for item in structured.get("component_nots", [])
        if str(item).strip()
    ] if isinstance(structured.get("component_nots", []), list) else []
    directive = semantic_prompt_directive_profile(node.semantic_unit)
    directive_kind = collapse_ws(
        str(structured.get("prompt_directive_kind") or directive.get("kind", "")).strip()
    )
    compared_terms = [
        str(item).strip()
        for item in structured.get("prompt_directive_compared_terms", [])
        if str(item).strip()
    ] if isinstance(structured.get("prompt_directive_compared_terms", []), list) else list(
        directive.get("compared_terms", [])
    )
    title_depth_body_split_needed = bool(structured.get("title_depth_body_split_needed", False))
    requires_chain = bool(
        structured.get("prompt_directive_requires_chain", directive.get("requires_chain", False))
    )
    explicit_chain_components = (
        semantic_chain_decomposition_components(node.semantic_unit)
        if directive_kind in {"construct", "derive"} and requires_chain
        else []
    )
    fallback_construct_components = (
        self.fallback_construct_chain_components(node.semantic_unit)
        if directive_kind in {"construct", "derive"} and requires_chain
        else []
    )
    if node.role == "root":
        if (
            directive_kind == "construct"
            and requires_chain
            and not title_depth_body_split_needed
            and not explicit_chain_components
            and self.should_preserve_construct_chain_prompt_surface(node.semantic_unit)
        ):
            node.metadata["decomposition_choice"] = "preserve_parent"
            return []
        if directive_kind == "distinguish" and len(compared_terms) >= 2 and not title_depth_body_split_needed:
            node.metadata["decomposition_choice"] = "preserve_parent"
            return []
        if (
            directive_kind == "identify_reusable_substrate"
            and bool(structured.get("prompt_directive_requires_substrate", False))
            and not title_depth_body_split_needed
        ):
            node.metadata["decomposition_choice"] = "preserve_parent"
            return []
    split_components = list(component_nots)
    split_components_use_component_fallback = False
    title_identity = structured_title_identity_text(structured) or normalize_semantic_title_identity(node.semantic_unit)
    fallback_control = self.fallback_control_decision(node) if node.role == "root" else {}
    fallback_root_decompose = bool(fallback_control.get("should_decompose", False)) if isinstance(fallback_control, Mapping) else False
    if node.role == "root" and fallback_root_decompose:
        parent_title = title_identity or node.semantic_unit
        parent_segments = derive_semantic_title_depth_segments(parent_title)
        parent_segment_namespace_keys = {
            semantic_namespace_key(segment)
            for segment in parent_segments
            if str(segment).strip()
        }
        normalized_components: list[str] = []
        for component in split_components:
            normalized_component = normalize_semantic_title_identity(component)
            if not normalized_component:
                continue
            relation_to_parent, _ = classify_title_depth_relation(parent_title, normalized_component)
            if relation_to_parent == "prior_is_overdetermined_extension" and parent_segments:
                child_segments = derive_semantic_title_depth_segments(normalized_component)
                suffix_segments = child_segments[len(parent_segments):]
                normalized_component = " / ".join(suffix_segments) if suffix_segments else child_segments[-1]
                relation_to_parent, _ = classify_title_depth_relation(parent_title, normalized_component)
            if relation_to_parent in {"same_identity", "prior_is_ground_prefix"}:
                continue
            if semantic_namespace_key(normalized_component) in parent_segment_namespace_keys:
                continue
            normalized_components.append(normalized_component)
        split_components = ordered_unique(item for item in normalized_components if item)
    if node.role == "root" and fallback_root_decompose:
        if len(split_components) < 2 and fallback_construct_components:
            split_components = ordered_unique(
                component
                for component in fallback_construct_components
                if collapse_ws(component)
            )
            split_components_use_component_fallback = bool(split_components)
        requested_output_phrases = semantic_requested_output_phrases(node.semantic_unit)
        requested_output_titles = ordered_unique(
            titleize_semantic_unit(phrase) or phrase
            for phrase in requested_output_phrases
            if titleize_semantic_unit(phrase) or phrase
        )
        if requested_output_titles:
            requested_namespace_keys = {
                semantic_namespace_key(title)
                for title in requested_output_titles
                if semantic_namespace_key(title)
            }
            aligned_requested_keys: set[str] = set()
            for component in split_components:
                component_key = semantic_namespace_key(component)
                if not component_key:
                    continue
                for requested_key in requested_namespace_keys:
                    if (
                        component_key == requested_key
                        or component_key in requested_key
                        or requested_key in component_key
                    ):
                        aligned_requested_keys.add(requested_key)
            if len(split_components) < 2 or len(aligned_requested_keys) < len(requested_namespace_keys):
                split_components = requested_output_titles
                split_components_use_component_fallback = bool(split_components)
    title_depth_prefixes = [
        str(item).strip()
        for item in structured.get("title_depth_prefixes", [])
        if str(item).strip()
    ] if isinstance(structured.get("title_depth_prefixes", []), list) else []

    if node.role == "support":
        specs = [
            {
                "semantic_unit": f"direct supporting evidence for {anchor}",
                "role": "direct_support",
                "description": "Attach direct evidence or support to this branch.",
                "boundary_shape": [
                    BoundaryShapeTerm.READ_VALUE.value,
                    BoundaryShapeTerm.OUTPUT_VALUE.value,
                ],
                "closure_threshold": "strict",
                "evidence_required": True,
                "required": False,
                "priority_bias": "high",
            },
            {
                "semantic_unit": f"upstream or prior committed support for {anchor}",
                "role": "upstream_support",
                "description": "Reuse existing support, earlier decisions, or related closed branches.",
                "boundary_shape": [
                    BoundaryShapeTerm.READ_REFERENCE.value,
                    BoundaryShapeTerm.READ_VALUE.value,
                    BoundaryShapeTerm.OUTPUT_VALUE.value,
                ],
                "closure_threshold": "normal",
                "evidence_required": False,
                "required": False,
                "priority_bias": "medium",
            },
        ]
    elif node.role == "root" and split_components and fallback_root_decompose:
        anchor_prefix = title_identity or node.semantic_unit
        if title_depth_prefixes and anchor_prefix not in title_depth_prefixes:
            anchor_prefix = title_depth_prefixes[-1]
        specs = [
            {
                "semantic_unit": component,
                "role": "generic",
                "description": f"Realize the distinct requested result '{component}' under the active shared family.",
                "boundary_shape": list(node.boundary_shape),
                "decomposition_mode": DecompositionMode.AND.value,
                "closure_threshold": self.default_closure_threshold_for_role("generic"),
                "evidence_required": False,
                "required": True,
                "priority_bias": PriorityLevel.HIGH.value,
                "title_depth_anchor_prefix": anchor_prefix,
                "namespace_rationale": "distinct requested result under the shared family title rather than a restatement of the parent title",
                "component_fallback": True,
                "anchor_under_prefix": split_components_use_component_fallback,
            }
            for component in split_components
        ]

    fallback_decompose_now = bool(specs)
    parent_context = self.decomposition_parent_context_payload(node)
    certain_sibling_context = self.decomposition_certain_sibling_context_payload(node)
    title_depth_prior = {
        "title_identity": title_identity,
        "title_depth_segments": list(structured.get("title_depth_segments", [])),
        "title_depth_prefixes": list(structured.get("title_depth_prefixes", [])),
        "title_depth_exposed_depth": int(structured.get("title_depth_exposed_depth", 0) or 0),
        "title_depth_minimal_sufficient_depth": int(structured.get("title_depth_minimal_sufficient_depth", 0) or 0),
        "title_depth_assessment": str(structured.get("title_depth_assessment", "")).strip(),
        "title_depth_hidden_depth_note": str(structured.get("title_depth_hidden_depth_note", "")).strip(),
        "title_depth_body_split_needed": bool(structured.get("title_depth_body_split_needed", False)),
        "title_depth_body_split_reason": str(structured.get("title_depth_body_split_reason", "")).strip(),
        "title_depth_reuse_bias": str(structured.get("title_depth_reuse_bias", "")).strip(),
    }
    root_local_namespace = self.root_local_title_namespace_payload(node)
    reserved_semantic_units = ordered_unique(
        [node.semantic_unit, title_identity]
        + split_components
        + [item.get("focus", "") for item in certain_sibling_context if str(item.get("focus", "")).strip()]
        + [
            str(item.get("title_identity", "")).strip()
            for item in root_local_namespace.get("titles", [])
            if str(item.get("title_identity", "")).strip()
        ]
    )

    decomposition_proposal = self.request_proposal(
        proposal_type=ProposalType.NOT_DECOMPOSITION,
        node=node,
        target_scope=node.semantic_unit,
        instructions=self.runtime_plain_prompt(
            f"""
            Decide whether the active item should stay whole or be broken into smaller parts.

            Title-depth law (infer from the formal title and context; it is never explicitly specified):
            {title_depth_theory_prompt_block()}
            
            Decompose only when smaller parts would materially help right now.
            
            If it is a question, does it need decomposition?
            If it is knowledge, does it need decomposition?
            If it is a simple enough question, it should say decompose_now is false.
            If it is knowledge that is granular or meaningful already, it should say decompose_now is false.
            
            Decision guidance:
            - decompose_now: true only if smaller parts would materially improve progress.
            - preserve_parent: true if the item should stay whole because it is already narrow, trivial, or better handled directly.
            - preserve_reason: explain why preserving the current item is better if preserve_parent is true.
            - Parent background and prior certain sibling background are informational context only.
            - Use that background to understand what the parent is trying to realize and which nearby sibling work is already sufficiently settled.
            - Do not duplicate already-certain sibling work as new children.
            - Use only the provided root-local title namespace; do not assume any external corpus.
            - You may reuse any provided root-local title if it is already the correct semantic identity.
            - Respect title-level decomposition before proposing body-level children.
            - Do not restate the full title identity or any title prefix as if it were a sibling child.
            - If the remaining work is already adequately covered by prior certain siblings, or a later direct function/template reuse path is more appropriate, prefer preserve_parent over decorative decomposition.
            - If the active full title is already minimally sufficient and no distinct body-level remainder remains, preserve_parent should be true.

            Child guidance:
            - children may be empty when preserve_parent is true.
            - If decompose_now is true, return 1 to {self.state.governance.max_children_per_node} children.
            - Each child must include semantic_unit, description, boundary_shape, decomposition_mode, closure_threshold, evidence_required, required, priority_bias, title_depth_anchor_prefix, and namespace_rationale.
            - semantic_unit should be concrete and narrow.
            - description should explain what the child is for.
            - boundary_shape must be a list using only a*, a'*, b*, b'*, c*, c'*, d*, d'*.
            - In that notation, * means one or more occurrences of the lane kind, not zero-or-more.
            - boundary_shape should say whether the child primarily concerns input, read, write, or output lanes, and whether those lanes carry values or references.
            - decomposition_mode should usually be AND or OR.
            - closure_threshold should be one of light, normal, or strict.
            - priority_bias should be one of low, medium, or high.
            - required should be true only if the parent really depends on that child.
            - title_depth_anchor_prefix must be one of the active title prefixes and should identify the title-depth prefix that grounds the child.
            - namespace_rationale must explain why the child is a distinct body-level unit rather than a restatement of a title segment or prefix.
            - children must not collide with reserved semantic units already present in the root-local title namespace.
            - If the item is trivial or already minimal, set decompose_now to false, preserve_parent to true, and return no children.
            - This prompt is only for deciding decomposition. Do not try to perform later executable or template invocation here; only identify subordinate non-achievedness if a real split is needed.

            Also fill:
            - alternate_decompositions: one or more alternate ways to split the task, if useful.

            Active item:
            {node.semantic_unit}

            Active non-achievedness:
            {json.dumps(node.metadata.get("not_elaboration", {}), indent=2, sort_keys=True)}

            Title-depth prior:
            {json.dumps(title_depth_prior, indent=2, sort_keys=True)}

            Parent overview:
            {json.dumps(parent_context, indent=2, sort_keys=True)}

            Prior certain siblings:
            {json.dumps(certain_sibling_context, indent=2, sort_keys=True)}

            Root-local title namespace:
            {json.dumps(root_local_namespace, indent=2, sort_keys=True)}
            """
        ),
        fallback_payload={
            "decompose_now": fallback_decompose_now,
            "preserve_parent": not fallback_decompose_now,
            "preserve_reason": (
                ""
                if specs
                else "No subordinate split is available here, so the current item should stay whole."
            ),
            "children": specs if fallback_decompose_now else [],
            "alternate_decompositions": [],
            "rationale": "Fallback breakdown stays close to the current item and avoids unnecessary drift.",
        },
        mode=self.select_supplement_mode("decomposition", node),
    )
    node.metadata["decomposition_proposal_id"] = decomposition_proposal.id
    decompose_now = self.proposal_flag(decomposition_proposal.payload, "decompose_now", default=bool(specs))
    preserve_parent = self.proposal_flag(
        decomposition_proposal.payload,
        "preserve_parent",
        default=not decompose_now,
    )
    node.metadata["decomposition_choice"] = "preserve_parent" if preserve_parent or not decompose_now else "decompose"
    if preserve_parent or not decompose_now:
        self.admit_proposal(
            decomposition_proposal,
            rationale="The controller admitted the decision to preserve the current item rather than force a decorative split.",
        )
        self.state.record_step(
            kind="decomposition",
            node_id=node.id,
            intent="Rewrite higher non-achievedness into governed subordinate non-achievednesses only when the split adds real determination.",
            action="evaluate whether decomposition is materially useful",
            result="preserved the current item without subordinate split",
            evaluation="the controller avoided a degenerate refinement and kept the direct-work path available",
            payload={
                "proposal_id": decomposition_proposal.id,
                "preserve_reason": decomposition_proposal.payload.get("preserve_reason", ""),
            },
        )
        return []

    proposed_children = decomposition_proposal.payload.get("children", specs)
    if not isinstance(proposed_children, list) or not proposed_children:
        proposed_children = specs

    children: list[SemanticNode] = []
    reserved_namespace_keys = {
        semantic_namespace_key(item)
        for item in ordered_unique(
            [title_identity]
            + list(title_depth_prior.get("title_depth_prefixes", []))
            + list(reserved_semantic_units)
        )
        if str(item).strip()
    }
    accepted_child_keys: set[str] = set()
    for spec in proposed_children[: self.state.governance.max_children_per_node]:
        if not isinstance(spec, Mapping):
            continue
        component_fallback = bool(spec.get("component_fallback", False))
        title_depth_anchor_prefix = normalize_semantic_title_identity(str(spec.get("title_depth_anchor_prefix", "")).strip())
        raw_child_semantic_unit = collapse_ws(str(spec.get("semantic_unit", anchor)).strip())
        if not raw_child_semantic_unit:
            continue
        raw_title_relation_to_parent, _ = classify_title_depth_relation(title_identity, raw_child_semantic_unit)
        raw_namespace_key = semantic_namespace_key(raw_child_semantic_unit)
        if raw_title_relation_to_parent in {"same_identity", "prior_is_ground_prefix", "prior_is_overdetermined_extension"}:
            continue
        if raw_namespace_key in accepted_child_keys:
            continue
        if raw_namespace_key in reserved_namespace_keys and not component_fallback:
            continue
        if component_fallback:
            child_semantic_unit = normalize_semantic_title_identity(raw_child_semantic_unit)
            reused_child_title = self.reusable_semantic_title_match(
                hint=child_semantic_unit,
                anchor_title="",
                exclude_titles=reserved_semantic_units,
            )
            if reused_child_title:
                child_semantic_unit = reused_child_title
            elif title_depth_anchor_prefix and bool(spec.get("anchor_under_prefix", False)):
                anchored_child_title = normalize_semantic_title_identity(
                    f"{title_depth_anchor_prefix} / {child_semantic_unit}"
                )
                if anchored_child_title:
                    child_semantic_unit = anchored_child_title
        else:
            child_semantic_unit = self.canonicalize_child_semantic_title(
                parent_title=title_identity or node.semantic_unit,
                proposed_title=raw_child_semantic_unit,
                prefer_store_reuse=True,
                exclude_titles=reserved_semantic_units,
            )
        child_namespace_key = semantic_namespace_key(child_semantic_unit)
        if child_namespace_key in accepted_child_keys:
            continue
        if child_namespace_key in reserved_namespace_keys and not component_fallback:
            continue
        if title_depth_anchor_prefix and title_depth_anchor_prefix not in set(title_depth_prior.get("title_depth_prefixes", [])):
            continue
        if not title_depth_anchor_prefix:
            title_depth_anchor_prefix = title_identity or child_semantic_unit
        namespace_rationale = collapse_ws(str(spec.get("namespace_rationale", "")).strip())
        if not namespace_rationale:
            namespace_rationale = "distinct body-level work under the active title identity"
        child = SemanticNode(
            id=self.runtime_make_id("not", child_semantic_unit),
            semantic_unit=child_semantic_unit,
            role=spec.get("role", "generic"),
            description=spec.get("description", ""),
            boundary_shape=normalize_boundary_shape(
                spec.get("boundary_shape"),
                default=node.boundary_shape,
            ),
            decomposition_mode=normalize_decomposition_mode(spec.get("decomposition_mode", DecompositionMode.AND)),
            closure_threshold=normalize_closure_rule(
                spec.get(
                    "closure_threshold",
                    self.default_closure_threshold_for_role(str(spec.get("role", "generic"))),
                )
            ),
            evidence_required=bool(spec.get("evidence_required", False)),
            required=bool(spec.get("required", True)),
            depth=node.depth + 1,
            priority_bias=normalize_priority(spec.get("priority_bias", PriorityLevel.MEDIUM)),
            parent_id=node.id,
            metadata={
                "anchor_semantic": anchor,
                "proposal_id": decomposition_proposal.id,
                "title_depth_anchor_prefix": title_depth_anchor_prefix,
                "namespace_rationale": namespace_rationale,
                "component_fallback": component_fallback,
            },
        )
        child.metadata["faithfulness"] = (
            "high"
            if component_fallback
            else semantic_bearing_level(node.semantic_unit, child.semantic_unit)
        )
        self.state.register_node(child, parent_id=node.id)
        children.append(child)
        accepted_child_keys.add(child_namespace_key)

    if node.role == "support" and len(children) == 2:
        left, right = children
        self.state.graph.add_edge(left.id, right.id, EdgeType.ALTERNATIVE_TO, metadata={"exclusive": False})
        self.state.graph.add_edge(right.id, left.id, EdgeType.ALTERNATIVE_TO, metadata={"exclusive": False})

    if children:
        self.admit_proposal(
            decomposition_proposal,
            rationale="The controller admitted the decomposition proposal into governed child candidates before faithfulness filtering.",
        )
    else:
        self.revise_proposal(
            decomposition_proposal,
            rationale="The decomposition proposal did not yield usable child candidates.",
        )
    self.state.record_step(
        kind="decomposition",
        node_id=node.id,
        intent="Rewrite higher non-achievedness into governed subordinate non-achievednesses.",
        action="decompose into subordinate refinement candidates",
        result=f"created {len(children)} subordinate non-achievednesses",
        evaluation="decomposition was retained durably for later control, trace, and resumption",
        payload={"children": [child.id for child in children], "proposal_id": decomposition_proposal.id},
    )
    return children


def filter_by_faithfulness(self, children: list[SemanticNode], parent: SemanticNode) -> list[SemanticNode]:
    """
    High Level Purpose:
        In circumstances like governed decomposition, helps with rejecting child candidates that no longer bear on the parent semantic burden before recursive descent continues.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `filter_by_faithfulness(children=[SemanticNode(id='child-force', semantic_unit='Physics / Force / Force From Mass And Acceleration')], parent=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
        Output: [SemanticNode(id='child-force', semantic_unit='Physics / Force / Force From Mass And Acceleration')]

    Args:
        self: Bound instance that owns the runtime state used by this method.
        children: Value for `children` used by `filter_by_faithfulness`. Expected type: `list[SemanticNode]`.
        parent: Value for `parent` used by `filter_by_faithfulness`. Expected type: `SemanticNode`.

    Returns:
        list[SemanticNode]: Result produced by `filter_by_faithfulness`.
    """
    accepted: list[SemanticNode] = []
    for child in children:
        faithfulness = (
            "high"
            if child.metadata.get("component_fallback")
            else semantic_bearing_level(parent.semantic_unit, child.semantic_unit)
        )
        faithful = (
            self.level_at_least_runtime(faithfulness, self.state.governance.faithfulness_requirement)
            or parent.semantic_unit.lower() in child.semantic_unit.lower()
            or child.metadata.get("anchor_semantic") == parent.semantic_unit
        )
        child.metadata["faithfulness"] = faithfulness
        if faithful:
            accepted.append(child)
            continue
        self.state.inadmissible.add(child.id)
        self.state.status[child.id] = NodeStatus.INADMISSIBLE
        self.state.frontier.discard(child.id)
        self.state.record_step(
            kind="faithfulness_rejection",
            node_id=child.id,
            intent="Reject arbitrary decomposition that does not bear on the parent achievedness.",
            action="apply decomposition faithfulness check",
            result="candidate marked inadmissible",
            evaluation="subordinate non-achievedness did not preserve achievedness relevance to its parent",
            payload={"parent_id": parent.id, "faithfulness": faithfulness},
        )
    return accepted


def order_children(self, children: list[SemanticNode]) -> list[SemanticNode]:
    """
    High Level Purpose:
        In circumstances like recursive governed reduction, helps with ordering accepted children before recursive descent while preserving the current proposal-based ordering behavior.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `order_children(children=[SemanticNode(id='child-force', semantic_unit='Physics / Force / Force From Mass And Acceleration')])`
        Output: [SemanticNode(id='child-force', semantic_unit='Physics / Force / Force From Mass And Acceleration')]

    Args:
        self: Bound instance that owns the runtime state used by this method.
        children: Value for `children` used by `order_children`. Expected type: `list[SemanticNode]`.

    Returns:
        list[SemanticNode]: Result produced by `order_children`.
    """
    if not children:
        return children
    parent_id = children[0].parent_id
    parent = self.state.graph.get_node(parent_id) if parent_id and parent_id in self.state.graph.nodes else self.state.root()
    proposal = self.propose_candidate_selection(
        context_node=parent,
        candidates=children,
        selection_kind="child ordering",
    )
    ordered = self.normalize_candidate_order(
        children,
        self.proposal_list(proposal.payload, "ordered_candidate_ids") if proposal is not None else [],
    )
    if proposal is not None:
        parent.metadata.setdefault("child_ordering_proposal_ids", []).append(proposal.id)
        parent.metadata["last_child_order"] = [child.id for child in ordered]
    return ordered
