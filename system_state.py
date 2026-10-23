# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from applied_theory_types import (
    Artifact,
    BSSCCarrier,
    Capability,
    Claim,
    ClaimStance,
    Commitment,
    ControllerFeatureToggles,
    DecompositionMode,
    DiscoveryAudit,
    EdgeType,
    Evidence,
    EvidencePolarity,
    GovernanceRules,
    GraphEdge,
    HumanContribution,
    NodeOrigin,
    NodeStatus,
    OntologyEntry,
    PausePoint,
    PriorityLevel,
    Product,
    ProposalGovernanceStatus,
    ProposalObject,
    ProposedCommitment,
    ProposalType,
    RunOutcome,
    RuntimeDeterminismPolicy,
    SemanticNode,
    StepRecord,
    SupportScore,
    SupportView,
    THEORY_VERSION,
    ThreeLevel,
    enum_text,
    json_safe,
    utc_now,
)
from artifact import build_pure_theory_artifact_projection
from boundary import default_boundary_shape_for_node, is_template_bearing_artifact_type
from id_generation import make_id
from normalize import (
    normalize_evidence_polarity,
    normalize_run_outcome,
    normalize_three_level,
)


def _make_id(prefix: str, text: str = "") -> str:
    """
    High Level Purpose:
        In circumstances like runtime graph construction, node registration, and controller state transitions, helps with creating id.

    Reference to Theory:
        Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

    Example Input Output:
        Input: `_make_id(prefix='Physics / Force / Force From Mass And Acceleration', text='Compute force from mass and acceleration.')`
        Output: 'artifact-force'

    Args:
        prefix: Value for `prefix` used by `_make_id`. Expected type: `str`.
        text: Value for `text` used by `_make_id`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `_make_id`.
    """
    return make_id(prefix, text)


def _default_boundary_shape_for_node(*, semantic_unit: str) -> Any:
    """
    High Level Purpose:
        In circumstances like runtime graph construction, node registration, and controller state transitions, helps with supplying default boundary shape for node.

    Reference to Theory:
        Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `_default_boundary_shape_for_node(semantic_unit='Physics / Force / Force From Mass And Acceleration')`
        Output: 'F = m * a'

    Args:
        semantic_unit: Value for `semantic_unit` used by `_default_boundary_shape_for_node`. Expected type: `str`.

    Returns:
        Any: Result produced by `_default_boundary_shape_for_node`.
    """
    return default_boundary_shape_for_node(semantic_unit=semantic_unit)


def _is_template_bearing_artifact_type(artifact_type: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like runtime graph construction, node registration, and controller state transitions, helps with deciding whether template bearing artifact type.

    Reference to Theory:
        Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `_is_template_bearing_artifact_type(artifact_type=3)`
        Output: True

    Args:
        artifact_type: Value for `artifact_type` used by `_is_template_bearing_artifact_type`. Expected type: `Any`.

    Returns:
        bool: Result produced by `_is_template_bearing_artifact_type`.
    """
    return bool(is_template_bearing_artifact_type(artifact_type))


class RefinementGraph:
    def __init__(self, *, nodes: Iterable[SemanticNode] | None = None, edges: Iterable[GraphEdge] | None = None) -> None:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with initializing the surrounding object with a usable starting state.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `__init__(nodes=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], edges=['mass', 'acceleration', 'force'])`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            nodes: Value for `nodes` used by `__init__`. Expected type: `Iterable[SemanticNode] | None`. Defaults to `None`.
            edges: Value for `edges` used by `__init__`. Expected type: `Iterable[GraphEdge] | None`. Defaults to `None`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.nodes: dict[str, SemanticNode] = {}
        self._out: dict[str, list[GraphEdge]] = {}
        self._in: dict[str, list[GraphEdge]] = {}
        for node in nodes or []:
            self.add_node(node)
        for edge in edges or []:
            self.add_edge(edge.src, edge.dst, edge.type, weight=edge.weight, metadata=edge.metadata)

    def add_node(self, node: SemanticNode) -> None:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling add node.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `add_node(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `add_node`. Expected type: `SemanticNode`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self._out.setdefault(node.id, [])
            self._in.setdefault(node.id, [])

    def add_edge(
        self,
        src: str,
        dst: str,
        edge_type: EdgeType,
        *,
        weight: str = "medium",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling add edge.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `add_edge(src='force', dst='force', edge_type=EdgeType.REFINES, weight='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            src: Value for `src` used by `add_edge`. Expected type: `str`.
            dst: Value for `dst` used by `add_edge`. Expected type: `str`.
            edge_type: Value for `edge_type` used by `add_edge`. Expected type: `EdgeType`.
            weight: Value for `weight` used by `add_edge`. Expected type: `str`. Defaults to `'medium'`.
            metadata: Value for `metadata` used by `add_edge`. Expected type: `dict[str, Any] | None`. Defaults to `None`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if src not in self.nodes or dst not in self.nodes:
            raise KeyError("Both edge endpoints must exist before adding an edge.")
        edge = GraphEdge(src=src, dst=dst, type=edge_type, weight=weight, metadata=metadata or {})
        for existing in self._out[src]:
            if existing.src == src and existing.dst == dst and existing.type == edge_type:
                return
        self._out[src].append(edge)
        self._in[dst].append(edge)

    def get_node(self, node_id: str) -> SemanticNode:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling get node.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `get_node(node_id='artifact-force')`
            Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `get_node`. Expected type: `str`.

        Returns:
            SemanticNode: Result produced by `get_node`.
        """
        return self.nodes[node_id]

    def out_edges(self, node_id: str) -> list[GraphEdge]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling out edges.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `out_edges(node_id='artifact-force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `out_edges`. Expected type: `str`.

        Returns:
            list[GraphEdge]: Result produced by `out_edges`.
        """
        return list(self._out.get(node_id, []))

    def in_edges(self, node_id: str) -> list[GraphEdge]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling in edges.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `in_edges(node_id='artifact-force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `in_edges`. Expected type: `str`.

        Returns:
            list[GraphEdge]: Result produced by `in_edges`.
        """
        return list(self._in.get(node_id, []))

    def refinement_children(self, node_id: str) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling refinement children.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `refinement_children(node_id='artifact-force')`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `refinement_children`. Expected type: `str`.

        Returns:
            list[SemanticNode]: Result produced by `refinement_children`.
        """
        return [self.get_node(edge.dst) for edge in self.out_edges(node_id) if edge.type == EdgeType.REFINES]

    def refinement_parents(self, node_id: str) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling refinement parents.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `refinement_parents(node_id='artifact-force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `refinement_parents`. Expected type: `str`.

        Returns:
            list[SemanticNode]: Result produced by `refinement_parents`.
        """
        return [self.get_node(edge.src) for edge in self.in_edges(node_id) if edge.type == EdgeType.REFINES]

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for node_id in self.nodes for edge in self.out_edges(node_id)],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RefinementGraph":
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'RefinementGraph': Result produced by `from_dict`.
        """
        nodes = [SemanticNode.from_dict(item) for item in data.get("nodes", [])]
        edges = [GraphEdge.from_dict(item) for item in data.get("edges", [])]
        return cls(nodes=nodes, edges=edges)


@dataclass
class SystemState:
    root_id: str
    graph: RefinementGraph
    governance: GovernanceRules = field(default_factory=GovernanceRules)
    controller_features: ControllerFeatureToggles = field(default_factory=ControllerFeatureToggles)
    determinism_policy: RuntimeDeterminismPolicy = field(default_factory=RuntimeDeterminismPolicy)
    supplement_profile: dict[str, Any] = field(default_factory=dict)
    llm_transcript: list[dict[str, Any]] = field(default_factory=list)
    frontier: set[str] = field(default_factory=set)
    proposals: dict[str, ProposalObject] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    evidence_by_node: dict[str, list[str]] = field(default_factory=dict)
    claims: dict[str, Claim] = field(default_factory=dict)
    proposed_commitments: dict[str, ProposedCommitment] = field(default_factory=dict)
    capabilities: dict[str, Capability] = field(default_factory=dict)
    human_contributions: dict[str, HumanContribution] = field(default_factory=dict)
    products: dict[str, Product] = field(default_factory=dict)
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    learned_artifacts: dict[str, Artifact] = field(default_factory=dict)
    subject_reasoning_scope: dict[str, Any] = field(default_factory=dict)
    learned_artifact_origins: dict[str, dict[str, Any]] = field(default_factory=dict)
    discovery_audits: dict[str, DiscoveryAudit] = field(default_factory=dict)
    pause_points: dict[str, PausePoint] = field(default_factory=dict)
    waits: dict[str, PausePoint] = field(default_factory=dict)
    commitments: dict[str, Commitment] = field(default_factory=dict)
    ontology: dict[str, OntologyEntry] = field(default_factory=dict)
    certainty: dict[str, ThreeLevel] = field(default_factory=dict)
    status: dict[str, NodeStatus] = field(default_factory=dict)
    blockers: dict[str, list[str]] = field(default_factory=dict)
    support: dict[str, SupportView] = field(default_factory=dict)
    conflicts: dict[str, list[str]] = field(default_factory=dict)
    closed: set[str] = field(default_factory=set)
    paused: set[str] = field(default_factory=set)
    incomplete: set[str] = field(default_factory=set)
    inadmissible: set[str] = field(default_factory=set)
    inlets: list[BSSCCarrier] = field(default_factory=list)
    outlets: list[BSSCCarrier] = field(default_factory=list)
    provenance_links: dict[str, list[str]] = field(default_factory=dict)
    ledger: list[StepRecord] = field(default_factory=list)
    trace: list[StepRecord] = field(default_factory=list)
    capability_grants: list[dict[str, Any]] = field(default_factory=list)
    effect_traces: list[dict[str, Any]] = field(default_factory=list)
    artifact_persistence: list[dict[str, Any]] = field(default_factory=list)
    run_outcome: RunOutcome = RunOutcome.ONGOING
    run_id: str = field(default_factory=lambda: _make_id("run"))
    sequence_counter: int = 0
    visit_counts: dict[str, int] = field(default_factory=dict)
    theory_version: str = THEORY_VERSION

    @classmethod
    def bootstrap(
        cls,
        prompt: str,
        governance: GovernanceRules | None = None,
        *,
        bootstrap_mode: str | None = None,
    ) -> "SystemState":
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with creating a new runtime state from an initial prompt and governance settings.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `bootstrap(prompt='Compute force from mass and acceleration.', governance=GovernanceRules(max_depth=6, max_nodes=64, max_children_per_node=4), bootstrap_mode='force')`
            Output: SystemState.bootstrap(prompt='Compute force from mass and acceleration.')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            prompt: Value for `prompt` used by `bootstrap`. Expected type: `str`.
            governance: Value for `governance` used by `bootstrap`. Expected type: `GovernanceRules | None`. Defaults to `None`.
            bootstrap_mode: Value for `bootstrap_mode` used by `bootstrap`. Expected type: `str | None`. Defaults to `None`.

        Returns:
            'SystemState': Result produced by `bootstrap`.
        """
        root = SemanticNode(
            id=_make_id("not", prompt),
            semantic_unit=prompt.strip(),
            role="root",
            description="High-level represented non-achievedness derived from the incoming prompt.",
            boundary_shape=_default_boundary_shape_for_node(semantic_unit=prompt.strip()),
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=(governance or GovernanceRules()).closure_threshold_default,
            evidence_required=False,
            required=True,
            depth=0,
            priority_bias=PriorityLevel.HIGH,
            origin=NodeOrigin.PROMPT,
        )
        if bootstrap_mode:
            root.metadata["bootstrap_mode"] = str(bootstrap_mode).strip()
        graph = RefinementGraph(nodes=[root])
        state = cls(
            root_id=root.id,
            graph=graph,
            governance=governance or GovernanceRules(),
            controller_features=ControllerFeatureToggles(),
            frontier={root.id},
        )
        state.status[root.id] = NodeStatus.OPEN
        state.certainty[root.id] = ThreeLevel.LOW
        state.blockers[root.id] = []
        state.support[root.id] = SupportView(direct=[], upstream=[], score=SupportScore.VERY_BAD)
        state.conflicts[root.id] = []
        state.register_ontology(
            entity_id=root.id,
            kind="not",
            semantic_identity=root.semantic_unit,
            working_semantics={
                "role": root.role,
                "not": root.not_label,
                "depth": root.depth,
                "boundary_shape": list(root.boundary_shape),
            },
        )
        state.initialize_builtin_capabilities()
        state.record_inlet(
            kind="prompt",
            semantic_identity=root.semantic_unit,
            payload={"node_id": root.id, "not": root.not_label},
        )
        state.record_step(
            kind="run_started",
            node_id=root.id,
            intent="Represent the high-level prompt as a high-level non-achievedness.",
            action="bootstrap durable governed state",
            result="root non-achievedness created",
            evaluation="prompt entered controlled Not-space",
        )
        return state

    def root(self) -> SemanticNode:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling root.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `root()`
            Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            SemanticNode: Result produced by `root`.
        """
        return self.graph.get_node(self.root_id)

    def node_status(self, node_id: str) -> NodeStatus:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling node status.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `node_status(node_id='artifact-force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `node_status`. Expected type: `str`.

        Returns:
            NodeStatus: Result produced by `node_status`.
        """
        return self.status.get(node_id, NodeStatus.OPEN)

    def next_proposal_revision(self, proposal_type: ProposalType, originating_not_id: str | None) -> int:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling next proposal revision.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `next_proposal_revision(proposal_type=ProposalType.NOT_ELABORATION, originating_not_id='artifact-force')`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal_type: Value for `proposal_type` used by `next_proposal_revision`. Expected type: `ProposalType`.
            originating_not_id: Value for `originating_not_id` used by `next_proposal_revision`. Expected type: `str | None`.

        Returns:
            int: Result produced by `next_proposal_revision`.
        """
        revisions = [
            proposal.revision_count
            for proposal in self.proposals.values()
            if proposal.proposal_type == proposal_type and proposal.originating_not_id == originating_not_id
        ]
        return (max(revisions) + 1) if revisions else 0

    def record_step(
        self,
        *,
        kind: str,
        node_id: str | None,
        intent: str,
        action: str,
        result: str,
        evaluation: str,
        commit_effect: str = "",
        payload: dict[str, Any] | None = None,
    ) -> StepRecord:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling record step.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `record_step(kind='ability', node_id='artifact-force', intent='force', action='force')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            kind: Value for `kind` used by `record_step`. Expected type: `str`.
            node_id: Value for `node_id` used by `record_step`. Expected type: `str | None`.
            intent: Value for `intent` used by `record_step`. Expected type: `str`.
            action: Value for `action` used by `record_step`. Expected type: `str`.
            result: Value for `result` used by `record_step`. Expected type: `str`.
            evaluation: Value for `evaluation` used by `record_step`. Expected type: `str`.
            commit_effect: Value for `commit_effect` used by `record_step`. Expected type: `str`. Defaults to `''`.
            payload: Value for `payload` used by `record_step`. Expected type: `dict[str, Any] | None`. Defaults to `None`.

        Returns:
            StepRecord: Result produced by `record_step`.
        """
        self.sequence_counter += 1
        record = StepRecord(
            seq=self.sequence_counter,
            kind=kind,
            node_id=node_id,
            intent=intent,
            action=action,
            result=result,
            evaluation=evaluation,
            commit_effect=commit_effect,
            payload=json_safe(payload or {}),
        )
        self.ledger.append(record)
        self.trace.append(record)
        return record

    def record_inlet(
        self,
        *,
        kind: str,
        semantic_identity: str,
        payload: dict[str, Any],
        provenance: list[str] | None = None,
    ) -> BSSCCarrier:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling record inlet.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `record_inlet(kind='ability', semantic_identity='Physics / Force / Force From Mass And Acceleration', payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, provenance=['mass', 'acceleration', 'force'])`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            kind: Value for `kind` used by `record_inlet`. Expected type: `str`.
            semantic_identity: Value for `semantic_identity` used by `record_inlet`. Expected type: `str`.
            payload: Value for `payload` used by `record_inlet`. Expected type: `dict[str, Any]`.
            provenance: Value for `provenance` used by `record_inlet`. Expected type: `list[str] | None`. Defaults to `None`.

        Returns:
            BSSCCarrier: Result produced by `record_inlet`.
        """
        carrier = BSSCCarrier(
            id=_make_id("inlet", semantic_identity),
            kind=kind,
            semantic_identity=semantic_identity,
            payload=json_safe(payload),
            provenance=list(provenance or []),
            created_at=utc_now(),
        )
        self.inlets.append(carrier)
        self.register_ontology(
            entity_id=carrier.id,
            kind=f"inlet:{kind}",
            semantic_identity=semantic_identity,
            authoritative_ref=carrier.id,
            working_semantics={"payload": carrier.payload, "carrier_kind": carrier.kind},
            embedded_refs=carrier.provenance,
        )
        self.record_step(
            kind="boundary_inlet",
            node_id=payload.get("node_id"),
            intent="Preserve inlet semantics in BSSC-consistent carrier form.",
            action=f"register inlet {kind}",
            result="inlet durably recorded",
            evaluation="boundary transition preserved semantic continuity",
            payload={"carrier_id": carrier.id, "kind": kind},
        )
        return carrier

    def record_outlet(
        self,
        *,
        kind: str,
        semantic_identity: str,
        payload: dict[str, Any],
        provenance: list[str] | None = None,
    ) -> BSSCCarrier:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling record outlet.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `record_outlet(kind='ability', semantic_identity='Physics / Force / Force From Mass And Acceleration', payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, provenance=['mass', 'acceleration', 'force'])`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            kind: Value for `kind` used by `record_outlet`. Expected type: `str`.
            semantic_identity: Value for `semantic_identity` used by `record_outlet`. Expected type: `str`.
            payload: Value for `payload` used by `record_outlet`. Expected type: `dict[str, Any]`.
            provenance: Value for `provenance` used by `record_outlet`. Expected type: `list[str] | None`. Defaults to `None`.

        Returns:
            BSSCCarrier: Result produced by `record_outlet`.
        """
        carrier = BSSCCarrier(
            id=_make_id("outlet", semantic_identity),
            kind=kind,
            semantic_identity=semantic_identity,
            payload=json_safe(payload),
            provenance=list(provenance or []),
            created_at=utc_now(),
        )
        self.outlets.append(carrier)
        self.register_ontology(
            entity_id=carrier.id,
            kind=f"outlet:{kind}",
            semantic_identity=semantic_identity,
            authoritative_ref=carrier.id,
            working_semantics={"payload": carrier.payload, "carrier_kind": carrier.kind},
            embedded_refs=carrier.provenance,
        )
        self.record_step(
            kind="boundary_outlet",
            node_id=payload.get("node_id"),
            intent="Preserve outlet semantics in BSSC-consistent carrier form.",
            action=f"register outlet {kind}",
            result="outlet durably recorded",
            evaluation="boundary transition preserved semantic continuity",
            payload={"carrier_id": carrier.id, "kind": kind},
        )
        return carrier

    def register_proposal(self, proposal: ProposalObject) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with registering proposal.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `register_proposal(proposal=ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal: Value for `proposal` used by `register_proposal`. Expected type: `ProposalObject`.

        Returns:
            ProposalObject: Result produced by `register_proposal`.
        """
        self.proposals[proposal.id] = proposal
        self.register_ontology(
            entity_id=proposal.id,
            kind="proposal",
            semantic_identity=proposal.proposal_type.value,
            authoritative_ref=proposal.id,
            working_semantics={
                "target_scope": proposal.target_scope,
                "originating_not_id": proposal.originating_not_id,
                "mode": proposal.mode.value,
                "governance_status": proposal.governance_status.value,
                "source": proposal.source,
                "provider": proposal.provider,
                "model": proposal.model,
            },
            embedded_refs=[proposal.originating_not_id] if proposal.originating_not_id else [],
        )
        self.record_step(
            kind="proposal_registered",
            node_id=proposal.originating_not_id,
            intent="Register proposal objects durably before governance decides how to use them.",
            action=f"register {proposal.proposal_type.value}",
            result="proposal recorded",
            evaluation="proposal remained non-authoritative pending governance",
            payload={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "source": proposal.source,
                "governance_status": proposal.governance_status.value,
            },
        )
        return proposal

    def set_proposal_status(
        self,
        proposal_id: str,
        status: ProposalGovernanceStatus,
        *,
        rationale: str = "",
    ) -> ProposalObject | None:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling set proposal status.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `set_proposal_status(proposal_id='artifact-force', status=ProposalGovernanceStatus.ADMITTED, rationale='The title is already minimally sufficient.')`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal_id: Value for `proposal_id` used by `set_proposal_status`. Expected type: `str`.
            status: Value for `status` used by `set_proposal_status`. Expected type: `ProposalGovernanceStatus`.
            rationale: Value for `rationale` used by `set_proposal_status`. Expected type: `str`. Defaults to `''`.

        Returns:
            ProposalObject | None: Result produced by `set_proposal_status`.
        """
        proposal = self.proposals.get(proposal_id)
        if proposal is None:
            return None
        proposal.governance_status = status
        if rationale:
            proposal.rationale = rationale
        ontology = self.ontology.get(f"ontology:{proposal.id}")
        if ontology is not None:
            ontology.working_semantics["governance_status"] = status.value
            if rationale:
                ontology.working_semantics["governance_rationale"] = rationale
        self.record_step(
            kind="proposal_governance",
            node_id=proposal.originating_not_id,
            intent="Govern proposal objects separately from proposal generation.",
            action=f"set proposal status to {status.value}",
            result="proposal governance state updated",
            evaluation="kernel retained admission authority over the proposal",
            payload={"proposal_id": proposal.id, "status": status.value, "rationale": rationale},
        )
        return proposal

    def register_ontology(
        self,
        *,
        entity_id: str,
        kind: str,
        semantic_identity: str,
        authoritative_ref: str | None = None,
        working_semantics: dict[str, Any] | None = None,
        embedded_refs: list[str] | None = None,
    ) -> OntologyEntry:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with registering ontology.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `register_ontology(entity_id='artifact-force', kind='ability', semantic_identity='Physics / Force / Force From Mass And Acceleration', authoritative_ref='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            entity_id: Value for `entity_id` used by `register_ontology`. Expected type: `str`.
            kind: Value for `kind` used by `register_ontology`. Expected type: `str`.
            semantic_identity: Value for `semantic_identity` used by `register_ontology`. Expected type: `str`.
            authoritative_ref: Value for `authoritative_ref` used by `register_ontology`. Expected type: `str | None`. Defaults to `None`.
            working_semantics: Value for `working_semantics` used by `register_ontology`. Expected type: `dict[str, Any] | None`. Defaults to `None`.
            embedded_refs: Value for `embedded_refs` used by `register_ontology`. Expected type: `list[str] | None`. Defaults to `None`.

        Returns:
            OntologyEntry: Result produced by `register_ontology`.
        """
        entry_id = f"ontology:{entity_id}"
        entry = OntologyEntry(
            id=entry_id,
            entity_id=entity_id,
            kind=kind,
            semantic_identity=semantic_identity,
            authoritative_ref=authoritative_ref or entity_id,
            working_semantics=json_safe(working_semantics or {}),
            embedded_refs=list(embedded_refs or []),
        )
        self.ontology[entry.id] = entry
        return entry

    def sync_not_ontology_entry(self, node: SemanticNode) -> None:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling sync not ontology entry.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `sync_not_ontology_entry(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `sync_not_ontology_entry`. Expected type: `SemanticNode`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        entry = self.ontology.get(f"ontology:{node.id}")
        if entry is None:
            return
        working = dict(entry.working_semantics)
        working.update(
            {
                "role": node.role,
                "not": node.not_label,
                "depth": node.depth,
                "boundary_shape": list(node.boundary_shape),
                "decomposition_mode": node.decomposition_mode,
            }
        )
        entry.working_semantics = json_safe(working)

    def register_capability(
        self,
        *,
        affordance: str,
        input_form: str,
        output_form: str,
        semantic_role: str,
        limits: dict[str, Any] | None = None,
        validated: bool = True,
        provenance: list[str] | None = None,
        service_axis: str = "governed_reduction",
        realizer: str = "controller",
    ) -> Capability:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with registering capability.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `register_capability(affordance='force', input_form='force', output_form='force', semantic_role='Physics / Force / Force From Mass And Acceleration')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            affordance: Value for `affordance` used by `register_capability`. Expected type: `str`.
            input_form: Value for `input_form` used by `register_capability`. Expected type: `str`.
            output_form: Value for `output_form` used by `register_capability`. Expected type: `str`.
            semantic_role: Value for `semantic_role` used by `register_capability`. Expected type: `str`.
            limits: Value for `limits` used by `register_capability`. Expected type: `dict[str, Any] | None`. Defaults to `None`.
            validated: Value for `validated` used by `register_capability`. Expected type: `bool`. Defaults to `True`.
            provenance: Value for `provenance` used by `register_capability`. Expected type: `list[str] | None`. Defaults to `None`.
            service_axis: Value for `service_axis` used by `register_capability`. Expected type: `str`. Defaults to `'governed_reduction'`.
            realizer: Value for `realizer` used by `register_capability`. Expected type: `str`. Defaults to `'controller'`.

        Returns:
            Capability: Result produced by `register_capability`.
        """
        capability = Capability(
            id=_make_id("capability", affordance),
            affordance=affordance,
            input_form=input_form,
            output_form=output_form,
            limits=limits or {},
            semantic_role=semantic_role,
            service_axis=service_axis,
            realizer=realizer,
            validated=validated,
            provenance=list(provenance or []),
        )
        self.capabilities[capability.id] = capability
        self.register_ontology(
            entity_id=capability.id,
            kind="capability",
            semantic_identity=affordance,
            working_semantics={
                "semantic_role": semantic_role,
                "service_axis": service_axis,
                "realizer": realizer,
                "validated": validated,
            },
            embedded_refs=capability.provenance,
        )
        self.record_step(
            kind="capability_registered",
            node_id=None,
            intent="Register a reusable means of reducing non-achievedness under controlled use.",
            action="register capability",
            result="capability available in controlled state",
            evaluation="capability remains subordinate to Not-centric control",
            payload={"capability_id": capability.id, "semantic_role": semantic_role, "service_axis": service_axis},
        )
        return capability

    def initialize_builtin_capabilities(self) -> None:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling initialize builtin capabilities.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `initialize_builtin_capabilities()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self.capabilities:
            return
        builtins = [
            {
                "affordance": "governed decomposition",
                "semantic_role": "decomposition",
                "input_form": "active non-achievedness",
                "output_form": "subordinate non-achievednesses",
                "service_axis": "decomposition",
            },
            {
                "affordance": "typed propagation",
                "semantic_role": "propagation",
                "input_form": "changed semantic nodes",
                "output_form": "stabilized local semantic region",
                "service_axis": "governance",
            },
            {
                "affordance": "retrospective reflection",
                "semantic_role": "reflection",
                "input_form": "composition subset",
                "output_form": "reassessed control state",
                "service_axis": "reflection",
            },
            {
                "affordance": "prospective contemplation",
                "semantic_role": "contemplation",
                "input_form": "current semantic state",
                "output_form": "candidate trajectories",
                "service_axis": "contemplation",
            },
            {
                "affordance": "evidence intake",
                "semantic_role": "evidence_intake",
                "input_form": "boundary return",
                "output_form": "durable evidence and claims",
                "service_axis": "evidence",
            },
            {
                "affordance": "closure commitment",
                "semantic_role": "closure_commitment",
                "input_form": "committable non-achievedness",
                "output_form": "durable commitment",
                "service_axis": "closure",
            },
            {
                "affordance": "discovery harvest",
                "semantic_role": "discovery_harvest",
                "input_form": "bounded run state",
                "output_form": "typed reusable artifacts and pain-gain audit",
                "service_axis": "development",
            },
            {
                "affordance": "artifact instantiation",
                "semantic_role": "artifact_instantiation",
                "input_form": "admitted artifact plus active non-achievedness",
                "output_form": "support-bearing current witness",
                "service_axis": "reuse",
            },
            {
                "affordance": "cross-boundary ability execution",
                "semantic_role": "cross_boundary",
                "input_form": "stored python script plus structured input payload",
                "output_form": "structured execution result from stdout",
                "service_axis": "ability_execution",
            },
            {
                "affordance": "runtime capability granting",
                "semantic_role": "capability_granting",
                "input_form": "admitted governed declaration plus requested effect",
                "output_form": "issued runtime capability grants",
                "service_axis": "governance",
            },
            {
                "affordance": "host effect mediation",
                "semantic_role": "host_mediation",
                "input_form": "effect request plus runtime grants",
                "output_form": "allow or deny decision with trace",
                "service_axis": "governance",
            },
            {
                "affordance": "structured learning lookup",
                "semantic_role": "structured_learning",
                "input_form": "active non-achievedness",
                "output_form": "prior-encounter, decomposition, and composition matches",
                "service_axis": "learning",
            },
            {
                "affordance": "markdown source compilation",
                "semantic_role": "markdown_learning",
                "input_form": "markdown document plus structural ir",
                "output_form": "typed reusable learning artifacts",
                "service_axis": "learning",
            },
            {
                "affordance": "adjacent learning expansion",
                "semantic_role": "immediate_learning",
                "input_form": "bounded discovery outcome",
                "output_form": "small set of nearby learn-now artifacts for future reuse",
                "service_axis": "learning",
            },
            {
                "affordance": "artifact persistence",
                "semantic_role": "artifact_persistence",
                "input_form": "admitted artifacts",
                "output_form": "durable artifact store write",
                "service_axis": "persistence",
            },
            {
                "affordance": "trace reporting",
                "semantic_role": "trace_reporting",
                "input_form": "trace and provenance state",
                "output_form": "trace report outlet",
                "service_axis": "trace",
            },
        ]
        for item in builtins:
            self.register_capability(
                affordance=item["affordance"],
                input_form=item["input_form"],
                output_form=item["output_form"],
                semantic_role=item["semantic_role"],
                service_axis=item["service_axis"],
                validated=True,
                realizer="builtin_controller_capability",
            )

    def register_node(
        self,
        node: SemanticNode,
        *,
        parent_id: str | None = None,
        edge_type: EdgeType = EdgeType.REFINES,
    ) -> SemanticNode:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with registering node.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `register_node(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), parent_id='artifact-force', edge_type=EdgeType.REFINES)`
            Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `register_node`. Expected type: `SemanticNode`.
            parent_id: Value for `parent_id` used by `register_node`. Expected type: `str | None`. Defaults to `None`.
            edge_type: Value for `edge_type` used by `register_node`. Expected type: `EdgeType`. Defaults to `EdgeType.REFINES`.

        Returns:
            SemanticNode: Result produced by `register_node`.
        """
        self.graph.add_node(node)
        self.status.setdefault(node.id, NodeStatus.OPEN)
        self.certainty.setdefault(node.id, ThreeLevel.LOW)
        self.blockers.setdefault(node.id, [])
        self.support.setdefault(node.id, SupportView(direct=[], upstream=[], score=SupportScore.VERY_BAD))
        self.conflicts.setdefault(node.id, [])
        self.frontier.add(node.id)
        if parent_id:
            self.graph.add_edge(parent_id, node.id, edge_type)
            self.graph.add_edge(node.id, parent_id, EdgeType.CLOSES_TO)
            node.parent_id = parent_id
            self.provenance_links.setdefault(node.id, []).append(parent_id)
        self.register_ontology(
            entity_id=node.id,
            kind="not",
            semantic_identity=node.semantic_unit,
            authoritative_ref=node.id,
            working_semantics={
                "role": node.role,
                "not": node.not_label,
                "depth": node.depth,
                "boundary_shape": list(node.boundary_shape),
                "decomposition_mode": node.decomposition_mode,
            },
            embedded_refs=self.provenance_links.get(node.id, []),
        )
        self.record_step(
            kind="node_registered",
            node_id=node.id,
            intent="Represent a governed non-achievedness durably and inspectably.",
            action="register semantic node",
            result="node added to refinement graph",
            evaluation="node is now available for controlled reduction",
            payload={"role": node.role, "parent_id": parent_id, "edge_type": edge_type.value if parent_id else None},
        )
        return node

    def attach_evidence(self, evidence: Evidence) -> Evidence:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with attaching evidence.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `attach_evidence(evidence=Evidence(statement='F = m * a'))`
            Output: Evidence(statement='F = m * a')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            evidence: Value for `evidence` used by `attach_evidence`. Expected type: `Evidence`.

        Returns:
            Evidence: Result produced by `attach_evidence`.
        """
        self.evidence[evidence.id] = evidence
        self.evidence_by_node.setdefault(evidence.node_id, []).append(evidence.id)
        self.provenance_links.setdefault(evidence.node_id, []).append(evidence.id)
        self.register_ontology(
            entity_id=evidence.id,
            kind="evidence",
            semantic_identity=evidence.observation,
            authoritative_ref=evidence.id,
            working_semantics={
                "node_id": evidence.node_id,
                "source": evidence.source,
                "polarity": evidence.polarity,
            },
            embedded_refs=evidence.provenance,
        )
        self._record_claim_from_evidence(evidence)
        self.paused.discard(evidence.node_id)
        self.incomplete.discard(evidence.node_id)
        self.frontier.add(evidence.node_id)
        self.record_step(
            kind="evidence_attached",
            node_id=evidence.node_id,
            intent="Attach support-bearing content to represented non-achievedness.",
            action="store evidence durably",
            result="evidence added to evidence store",
            evaluation="certainty can now be reassessed under governance",
            payload={"evidence_id": evidence.id, "source": evidence.source, "polarity": evidence.polarity},
        )
        return evidence

    def register_artifact(self, artifact: Artifact) -> Artifact:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with registering artifact.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `register_artifact(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `register_artifact`. Expected type: `Artifact`.

        Returns:
            Artifact: Result produced by `register_artifact`.
        """
        self.artifacts[artifact.id] = artifact
        pure_theory_projection = build_pure_theory_artifact_projection(artifact)
        self.register_ontology(
            entity_id=artifact.id,
            kind=f"artifact:{enum_text(artifact.artifact_type)}",
            semantic_identity=artifact.title or artifact.artifact_type,
            authoritative_ref=artifact.id,
            working_semantics={
                "artifact_type": artifact.artifact_type,
                "representation": artifact.representation,
                "scope": artifact.scope,
                "reusability": artifact.reusability,
                "admissibility": artifact.admissibility,
                "template_bearing": _is_template_bearing_artifact_type(artifact.artifact_type),
                "learning_relation": artifact.learning_relation,
                "pure_theory_model": pure_theory_projection.__class__.__name__ if pure_theory_projection is not None else "",
            },
            embedded_refs=[*artifact.provenance, *artifact.related_artifact_ids],
        )
        self.record_step(
            kind="artifact_registered",
            node_id=artifact.content.get("node_id"),
            intent="Preserve reusable governed residue as a typed artifact.",
            action="register artifact",
            result="artifact stored in durable state",
            evaluation="artifact remained typed, scoped, provenance-bearing, and separately governed",
            payload={
                "artifact_id": artifact.id,
                "artifact_type": artifact.artifact_type,
                "admissibility": artifact.admissibility,
                "reusability": artifact.reusability,
                "learning_relation": artifact.learning_relation,
                "related_artifact_ids": artifact.related_artifact_ids,
                "pure_theory_validated": pure_theory_projection is not None,
            },
        )
        return artifact

    def register_discovery_audit(self, audit: DiscoveryAudit) -> DiscoveryAudit:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with registering discovery audit.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `register_discovery_audit(audit=DiscoveryAudit(query='force formula'))`
            Output: DiscoveryAudit(query='force formula')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            audit: Value for `audit` used by `register_discovery_audit`. Expected type: `DiscoveryAudit`.

        Returns:
            DiscoveryAudit: Result produced by `register_discovery_audit`.
        """
        self.discovery_audits[audit.id] = audit
        self.register_ontology(
            entity_id=audit.id,
            kind="discovery_audit",
            semantic_identity=self.graph.get_node(audit.node_id).semantic_unit if audit.node_id in self.graph.nodes else audit.node_id,
            authoritative_ref=audit.id,
            working_semantics={
                "run_outcome": audit.run_outcome,
                "pain_class": audit.pain_class,
                "gain_class": audit.gain_class,
                "gain_types": audit.gain_types,
            },
            embedded_refs=audit.provenance,
        )
        self.record_step(
            kind="discovery_audit",
            node_id=audit.node_id,
            intent="Run a bounded harvest pass to determine reusable residue from the governed encounter.",
            action="record discovery audit",
            result="discovery audit stored",
            evaluation="present-task outcome was paired with future-governability harvest",
            payload={
                "audit_id": audit.id,
                "pain_class": audit.pain_class,
                "gain_class": audit.gain_class,
                "gain_types": audit.gain_types,
                "artifact_ids": audit.artifact_ids,
            },
        )
        return audit

    def find_nodes(self, *, target: str | None = None, role: str | None = None) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with finding nodes.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `find_nodes(target='force', role='force')`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            target: Value for `target` used by `find_nodes`. Expected type: `str | None`. Defaults to `None`.
            role: Value for `role` used by `find_nodes`. Expected type: `str | None`. Defaults to `None`.

        Returns:
            list[SemanticNode]: Result produced by `find_nodes`.
        """
        matches = list(self.graph.nodes.values())
        if target and target != "root":
            lowered = target.lower()
            matches = [
                node for node in matches if lowered in node.id.lower() or lowered in node.semantic_unit.lower()
            ]
        elif target == "root":
            matches = [self.root()]
        if role:
            matches = [node for node in matches if node.role == role]
        return matches

    def _record_claim_from_evidence(self, evidence: Evidence) -> Claim:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling record claim from evidence.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `_record_claim_from_evidence(evidence=Evidence(statement='F = m * a'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            evidence: Value for `evidence` used by `_record_claim_from_evidence`. Expected type: `Evidence`.

        Returns:
            Claim: Result produced by `_record_claim_from_evidence`.
        """
        stance = ClaimStance.SUPPORTS if evidence.polarity == EvidencePolarity.SUPPORT else ClaimStance.COUNTERS
        claim = Claim(
            id=_make_id("claim", evidence.observation),
            node_id=evidence.node_id,
            evidence_id=evidence.id,
            interpreted_fact=f"The observation from {evidence.source} is relevant to {self.graph.get_node(evidence.node_id).not_label}.",
            claim_text=f"{evidence.source} {stance} reduction of {self.graph.get_node(evidence.node_id).not_label}.",
            stance=stance,
            provenance=[evidence.id, *evidence.provenance],
        )
        self.claims[claim.id] = claim
        self.provenance_links.setdefault(evidence.node_id, []).append(claim.id)
        self.register_ontology(
            entity_id=claim.id,
            kind="claim",
            semantic_identity=claim.claim_text,
            authoritative_ref=claim.id,
            working_semantics={"node_id": claim.node_id, "stance": claim.stance},
            embedded_refs=claim.provenance,
        )
        self.record_step(
            kind="claim_interpreted",
            node_id=evidence.node_id,
            intent="Preserve the distinction between observation, interpreted fact, and claim.",
            action="interpret evidence into claim",
            result="claim recorded",
            evaluation="evidence stratification remained explicit and durable",
            payload={"claim_id": claim.id, "evidence_id": evidence.id, "stance": stance},
        )
        return claim

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "root_id": self.root_id,
            "final_answer": self.root_final_answer(),
            "graph": self.graph.to_dict(),
            "governance": self.governance.to_dict(),
            "controller_features": self.controller_features.to_dict(),
            "determinism_policy": self.determinism_policy.to_dict(),
            "supplement_profile": json_safe(self.supplement_profile),
            "llm_transcript": json_safe(self.llm_transcript),
            "frontier": sorted(self.frontier),
            "proposals": {key: value.to_dict() for key, value in self.proposals.items()},
            "evidence": {key: value.to_dict() for key, value in self.evidence.items()},
            "evidence_by_node": {key: list(value) for key, value in self.evidence_by_node.items()},
            "claims": {key: value.to_dict() for key, value in self.claims.items()},
            "proposed_commitments": {key: value.to_dict() for key, value in self.proposed_commitments.items()},
            "capabilities": {key: value.to_dict() for key, value in self.capabilities.items()},
            "human_contributions": {key: value.to_dict() for key, value in self.human_contributions.items()},
            "products": {key: value.to_dict() for key, value in self.products.items()},
            "artifacts": {key: value.to_dict() for key, value in self.artifacts.items()},
            "learned_artifacts": {key: value.to_dict() for key, value in self.learned_artifacts.items()},
            "subject_reasoning_scope": json_safe(self.subject_reasoning_scope),
            "learned_artifact_origins": json_safe(self.learned_artifact_origins),
            "discovery_audits": {key: value.to_dict() for key, value in self.discovery_audits.items()},
            "pause_points": {key: value.to_dict() for key, value in self.pause_points.items()},
            "waits": {key: value.to_dict() for key, value in self.waits.items()},
            "commitments": {key: value.to_dict() for key, value in self.commitments.items()},
            "ontology": {key: value.to_dict() for key, value in self.ontology.items()},
            "certainty": self.certainty,
            "status": {key: value.value for key, value in self.status.items()},
            "blockers": {key: list(value) for key, value in self.blockers.items()},
            "support": {key: value.to_dict() for key, value in self.support.items()},
            "conflicts": {key: list(value) for key, value in self.conflicts.items()},
            "closed": sorted(self.closed),
            "paused": sorted(self.paused),
            "incomplete": sorted(self.incomplete),
            "inadmissible": sorted(self.inadmissible),
            "inlets": [carrier.to_dict() for carrier in self.inlets],
            "outlets": [carrier.to_dict() for carrier in self.outlets],
            "provenance_links": {key: list(value) for key, value in self.provenance_links.items()},
            "ledger": [record.to_dict() for record in self.ledger],
            "trace": [record.to_dict() for record in self.trace],
            "capability_grants": json_safe(self.capability_grants),
            "effect_traces": json_safe(self.effect_traces),
            "artifact_persistence": json_safe(self.artifact_persistence),
            "run_outcome": self.run_outcome.value,
            "run_id": self.run_id,
            "sequence_counter": self.sequence_counter,
            "visit_counts": self.visit_counts,
            "theory_version": self.theory_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemState":
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: SystemState.bootstrap(prompt='Compute force from mass and acceleration.')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'SystemState': Result produced by `from_dict`.
        """
        return cls(
            root_id=data["root_id"],
            graph=RefinementGraph.from_dict(data["graph"]),
            governance=GovernanceRules.from_dict(data.get("governance", {})),
            controller_features=ControllerFeatureToggles.from_dict(data.get("controller_features", {})),
            determinism_policy=RuntimeDeterminismPolicy.from_dict(data.get("determinism_policy")),
            supplement_profile=dict(data.get("supplement_profile", {})),
            llm_transcript=[
                dict(item) for item in data.get("llm_transcript", []) if isinstance(item, Mapping)
            ],
            frontier=set(data.get("frontier", [])),
            proposals={
                key: ProposalObject.from_dict(value)
                for key, value in data.get("proposals", {}).items()
                if value.get("proposal_type") not in {"DutyFrameProposal", "DutyTemplateProposal"}
            },
            evidence={key: Evidence.from_dict(value) for key, value in data.get("evidence", {}).items()},
            evidence_by_node={key: list(value) for key, value in data.get("evidence_by_node", {}).items()},
            claims={key: Claim.from_dict(value) for key, value in data.get("claims", {}).items()},
            proposed_commitments={
                key: ProposedCommitment.from_dict(value)
                for key, value in data.get("proposed_commitments", {}).items()
            },
            capabilities={key: Capability.from_dict(value) for key, value in data.get("capabilities", {}).items()},
            human_contributions={
                key: HumanContribution.from_dict(value)
                for key, value in data.get("human_contributions", {}).items()
            },
            products={key: Product.from_dict(value) for key, value in data.get("products", {}).items()},
            artifacts={key: Artifact.from_dict(value) for key, value in data.get("artifacts", {}).items()},
            learned_artifacts={key: Artifact.from_dict(value) for key, value in data.get("learned_artifacts", {}).items()},
            subject_reasoning_scope=dict(data.get("subject_reasoning_scope", {})),
            learned_artifact_origins={
                key: dict(value)
                for key, value in data.get("learned_artifact_origins", {}).items()
                if isinstance(value, Mapping)
            },
            discovery_audits={
                key: DiscoveryAudit.from_dict(value)
                for key, value in data.get("discovery_audits", {}).items()
            },
            pause_points={key: PausePoint.from_dict(value) for key, value in data.get("pause_points", {}).items()},
            waits={key: PausePoint.from_dict(value) for key, value in data.get("waits", {}).items()},
            commitments={key: Commitment.from_dict(value) for key, value in data.get("commitments", {}).items()},
            ontology={key: OntologyEntry.from_dict(value) for key, value in data.get("ontology", {}).items()},
            certainty={key: normalize_three_level(value, default=ThreeLevel.LOW) for key, value in data.get("certainty", {}).items()},
            status={key: NodeStatus(value) for key, value in data.get("status", {}).items()},
            blockers={key: list(value) for key, value in data.get("blockers", {}).items()},
            support={key: SupportView.from_dict(value) for key, value in data.get("support", {}).items()},
            conflicts={key: list(value) for key, value in data.get("conflicts", {}).items()},
            closed=set(data.get("closed", [])),
            paused=set(data.get("paused", [])),
            incomplete=set(data.get("incomplete", [])),
            inadmissible=set(data.get("inadmissible", [])),
            inlets=[BSSCCarrier.from_dict(item) for item in data.get("inlets", [])],
            outlets=[BSSCCarrier.from_dict(item) for item in data.get("outlets", [])],
            provenance_links={key: list(value) for key, value in data.get("provenance_links", {}).items()},
            ledger=[StepRecord.from_dict(item) for item in data.get("ledger", [])],
            trace=[StepRecord.from_dict(item) for item in data.get("trace", [])],
            capability_grants=[dict(item) for item in data.get("capability_grants", [])],
            effect_traces=[dict(item) for item in data.get("effect_traces", [])],
            artifact_persistence=[dict(item) for item in data.get("artifact_persistence", [])],
            run_outcome=normalize_run_outcome(data.get("run_outcome", RunOutcome.ONGOING)),
            run_id=data.get("run_id", _make_id("run")),
            sequence_counter=int(data.get("sequence_counter", 0)),
            visit_counts={key: int(value) for key, value in data.get("visit_counts", {}).items()},
            theory_version=data.get("theory_version", THEORY_VERSION),
        )

    def summary(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling summary.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `summary()`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `summary`.
        """
        nodes = []
        for node in sorted(self.graph.nodes.values(), key=lambda item: (item.depth, item.semantic_unit.lower())):
            nodes.append(
                {
                    "id": node.id,
                    "semantic_unit": node.semantic_unit,
                    "not": node.not_label,
                    "role": node.role,
                    "boundary_shape": list(node.boundary_shape),
                    "depth": node.depth,
                    "status": self.node_status(node.id).value,
                    "certainty": self.certainty.get(node.id, "low"),
                    "blockers": list(self.blockers.get(node.id, [])),
                }
            )
        root = self.root()
        latest_audit = max(self.discovery_audits.values(), key=lambda item: item.created_at) if self.discovery_audits else None
        final_answer = self.root_final_answer()
        return {
            "theory_version": self.theory_version,
            "run_id": self.run_id,
            "run_outcome": self.run_outcome.value,
            "final_answer": final_answer,
            "development": {
                "pain_class": latest_audit.pain_class if latest_audit is not None else None,
                "gain_class": latest_audit.gain_class if latest_audit is not None else None,
                "gain_types": latest_audit.gain_types if latest_audit is not None else [],
                "artifact_ids": latest_audit.artifact_ids if latest_audit is not None else [],
                "learned_artifact_ids": sorted(self.learned_artifacts)[:8],
                "subject_reasoning_scope": dict(self.subject_reasoning_scope),
                "artifact_persistence": self.artifact_persistence[-1] if self.artifact_persistence else {},
            },
            "controller_features": self.controller_features.to_dict(),
            "root": {
                "id": root.id,
                "semantic_unit": root.semantic_unit,
                "not": root.not_label,
                "boundary_shape": list(root.boundary_shape),
                "status": self.node_status(root.id).value,
                "certainty": self.certainty.get(root.id, "low"),
            },
            "counts": {
                "nodes": len(self.graph.nodes),
                "edges": sum(len(self.graph.out_edges(node_id)) for node_id in self.graph.nodes),
                "proposals": len(self.proposals),
                "evidence": len(self.evidence),
                "claims": len(self.claims),
                "capabilities": len(self.capabilities),
                "commitments": len(self.commitments),
                "artifacts": len(self.artifacts),
                "learned_artifacts": len(self.learned_artifacts),
                "learned_artifact_origins": len(self.learned_artifact_origins),
                "discovery_audits": len(self.discovery_audits),
                "pause_points": len(self.pause_points),
                "ledger_entries": len(self.ledger),
            },
            "frontier": [
                {
                    "id": node_id,
                    "semantic_unit": self.graph.get_node(node_id).semantic_unit,
                    "status": self.node_status(node_id).value,
                }
                for node_id in sorted(self.frontier)
            ],
            "llm": json_safe(self.supplement_profile),
            "nodes": nodes,
            "recent_ledger": [record.to_dict() for record in self.ledger[-10:]],
        }

    def root_final_answer(self) -> str | None:
        """
        High Level Purpose:
            In circumstances like runtime graph construction, node registration, and controller state transitions, helps with handling root final answer.

        Reference to Theory:
            Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

        Example Input Output:
            Input: `root_final_answer()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            str | None: Result produced by `root_final_answer`.
        """
        root = self.root()
        direct_answer = str(root.metadata.get("direct_resolution_answer", "")).strip()
        if direct_answer:
            return direct_answer

        for product in self.products.values():
            if product.node_id != root.id:
                continue
            content = product.content if isinstance(product.content, Mapping) else {}
            for key in ("answer", "final_answer", "result", "output"):
                value = str(content.get(key, "")).strip()
                if value:
                    return value

        root_claims = sorted(
            (claim for claim in self.claims.values() if claim.node_id == root.id),
            key=lambda item: item.created_at,
        )
        if root_claims:
            claim = root_claims[-1]
            value = str(claim.claim_text or claim.interpreted_fact).strip()
            if value:
                return value

        for evidence_id in reversed(self.evidence_by_node.get(root.id, [])):
            evidence = self.evidence.get(evidence_id)
            if evidence is None:
                continue
            if isinstance(evidence.context, Mapping):
                for key in ("answer", "result", "output"):
                    value = str(evidence.context.get(key, "")).strip()
                    if value:
                        return value
            observation = str(evidence.observation).strip()
            if "': " in observation:
                candidate = observation.split("': ", 1)[1].strip()
                if candidate.endswith("."):
                    candidate = candidate[:-1].strip()
                if candidate:
                    return candidate
            if observation:
                return observation
        return None


def load_state(path: Path) -> SystemState:
    """
    High Level Purpose:
        In circumstances like runtime graph construction, node registration, and controller state transitions, helps with loading state.

    Reference to Theory:
        Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

    Example Input Output:
        Input: `load_state(path=Path('/tmp/physics_force.md'))`
        Output: SystemState.bootstrap(prompt='Compute force from mass and acceleration.')

    Args:
        path: Value for `path` used by `load_state`. Expected type: `Path`.

    Returns:
        SystemState: Result produced by `load_state`.
    """
    return SystemState.from_dict(json.loads(path.read_text()))


def save_state(state: SystemState, path: Path) -> None:
    """
    High Level Purpose:
        In circumstances like runtime graph construction, node registration, and controller state transitions, helps with saving state.

    Reference to Theory:
        Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

    Example Input Output:
        Input: `save_state(state=SystemState.bootstrap(prompt='Compute force from mass and acceleration.'), path=Path('/tmp/physics_force.md'))`
        Output: None

    Args:
        state: Value for `state` used by `save_state`. Expected type: `SystemState`.
        path: Value for `path` used by `save_state`. Expected type: `Path`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    path.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n")


def load_evidence_specs(path: Path) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like runtime graph construction, node registration, and controller state transitions, helps with loading evidence specs.

    Reference to Theory:
        Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

    Example Input Output:
        Input: `load_evidence_specs(path=Path('/tmp/physics_force.md'))`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        path: Value for `path` used by `load_evidence_specs`. Expected type: `Path`.

    Returns:
        list[dict[str, Any]]: Result produced by `load_evidence_specs`.
    """
    raw = json.loads(path.read_text())
    if isinstance(raw, list):
        return [dict(item) for item in raw]
    if isinstance(raw, dict):
        if "evidence" in raw and isinstance(raw["evidence"], list):
            return [dict(item) for item in raw["evidence"]]
        return [dict(raw)]
    raise ValueError("Evidence file must be a JSON object or array.")


def attach_evidence_specs(state: SystemState, evidence_specs: list[dict[str, Any]]) -> None:
    """
    High Level Purpose:
        In circumstances like runtime graph construction, node registration, and controller state transitions, helps with attaching evidence specs.

    Reference to Theory:
        Carries the runtime graph/state model that holds semantic units, refinement state, and controller progress derived from the applied theory.

    Example Input Output:
        Input: `attach_evidence_specs(state=SystemState.bootstrap(prompt='Compute force from mass and acceleration.'), evidence_specs={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: None

    Args:
        state: Value for `state` used by `attach_evidence_specs`. Expected type: `SystemState`.
        evidence_specs: Value for `evidence_specs` used by `attach_evidence_specs`. Expected type: `list[dict[str, Any]]`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    evidence_capability = next(
        (capability for capability in state.capabilities.values() if capability.semantic_role == "evidence_intake"),
        None,
    )
    for spec in evidence_specs:
        target = spec.get("target", "root")
        role = spec.get("role")
        targets = state.find_nodes(target=target, role=role)
        if not targets:
            targets = [state.root()]
        for node in targets:
            external_provenance = [
                str(item).strip()
                for item in spec.get("provenance", [])
                if str(item).strip()
            ]
            evidence = Evidence(
                id=_make_id("evidence", spec.get("observation", node.semantic_unit)),
                node_id=node.id,
                observation=spec.get("observation", f"Support attached to {node.semantic_unit}."),
                source=spec.get("source", "human"),
                context=dict(spec.get("context", {})),
                support_effect=normalize_three_level(
                    spec.get("support_effect", spec.get("support_strength", ThreeLevel.HIGH)),
                    default=ThreeLevel.HIGH,
                ),
                confidence=normalize_three_level(spec.get("confidence", ThreeLevel.HIGH), default=ThreeLevel.HIGH),
                polarity=normalize_evidence_polarity(spec.get("polarity", EvidencePolarity.SUPPORT)),
            )
            carrier = state.record_inlet(
                kind="evidence",
                semantic_identity=node.semantic_unit,
                payload={"node_id": node.id, "source": evidence.source, "observation": evidence.observation},
                provenance=external_provenance,
            )
            evidence.provenance.extend([carrier.id, *external_provenance])
            state.attach_evidence(evidence)
            if evidence_capability is not None:
                state.provenance_links.setdefault(node.id, []).append(evidence_capability.id)
                state.record_step(
                    kind="capability_use",
                    node_id=node.id,
                    intent="Use capabilities only where their contribution bears on relevant non-achievedness reduction.",
                    action=f"use capability {evidence_capability.affordance}",
                    result="evidence intake capability applied",
                    evaluation="boundary evidence entered controlled state under a reusable capability",
                    payload={
                        "capability_id": evidence_capability.id,
                        "semantic_role": evidence_capability.semantic_role,
                        "contribution": "durable evidence intake",
                    },
                )

            if evidence.source == "human":
                contribution = HumanContribution(
                    id=_make_id("human", evidence.observation),
                    content=evidence.observation,
                    related_node_id=node.id,
                    provenance=[carrier.id, evidence.id, *external_provenance],
                )
                state.human_contributions[contribution.id] = contribution
                state.provenance_links.setdefault(node.id, []).append(contribution.id)
                state.register_ontology(
                    entity_id=contribution.id,
                    kind="human_contribution",
                    semantic_identity=contribution.content,
                    authoritative_ref=contribution.id,
                    working_semantics={"node_id": node.id, "accepted": contribution.accepted},
                    embedded_refs=contribution.provenance,
                )
