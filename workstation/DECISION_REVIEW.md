# Decision Review

Formal design for the decision-oriented review layer that sits inside
[workstation/REVIEW.md](workstation/REVIEW.md)
and feeds the later, high-value recommendation sections of
[workstation/PUBLICATION.md](workstation/PUBLICATION.md).

Concrete implementation planning for this layer lives in
[DECISION_REVIEW_IMPLEMENTATION.md](DECISION_REVIEW_IMPLEMENTATION.md).

This is the part of the report system intended to become the crown jewel:

- industry-standard decision aids
- traceable recommendations
- bounded, explicit actual decisions where policy allows them
- simple diagrams and decision-oriented illustrations that are derived from governed corpus material rather than invented freehand

## Objective

The system should be able to take reviewed corpus material and produce one of two things:

1. decision-making aids
- decision tables
- option comparison matrices
- transition roadmaps
- dependency checklists
- risk/control matrices
- actor assignment views
- simple flow or dependency diagrams

2. actual decisions
- a selected option
- a justification for that selection
- explicit residual risks
- explicit prerequisites and owners
- explicit statement of what is still uncertain

The second class should only happen when the model has enough explicit structure to justify it.

Otherwise the system should stop at a decision aid.

## Problem

Current review is strong enough to:

- include or exclude material
- build and approve report plans
- orient items toward tables, diagrams, and rewritten prose

That is necessary, but not yet sufficient for decision-oriented reporting.

Decision sections need more than composition.

They need:

- explicit options
- explicit constraints
- explicit dependencies
- explicit actors and assignments
- explicit current and target states
- explicit admissibility and risk checks
- explicit policy or ranking rules
- explicit trace from source material to recommendation

Without that layer, reports can look polished while still hiding how the recommendation was arrived at.

## Core Decision

Decision-oriented reporting should use a separate `DecisionReview` layer rather than trying to force everything through generic composition.

The correct relationship is:

`Learning unit -> Itemized subject item -> Review item -> Decision review item -> Decision aid / recommendation block -> Publication output`

This keeps the responsibilities separated:

- `LearningContext` stores admitted source-derived truth
- `Review` shapes material compositionally
- `DecisionReview` turns selected reviewed material into explicit decision structure
- `Publication` renders the final decision aids and recommendation sections

## The Two Engines

Two existing systems can help here, but they do different jobs.

### 1. Coordinated Transformation Theory

Where:
- [coordinated_transformation/core.py](coordinated_transformation/core.py)
- [COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md](COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md)

What it is good for:

- explicit actors, objectives, capabilities, dependencies, constraints, boundaries, states, transitions, and decisions
- deterministic admissibility checking
- deterministic decision validity and executability checking
- deterministic risk and boundary-friction checks
- deterministic reachability and transition closure
- explicit axiom validation over the decision model

What it is not:

- a prose reduction system
- a fuzzy discovery engine
- a ranking or policy engine by itself

It tells us:

- which transitions are admissible
- which decisions are valid
- which decisions are executable
- where risk appears
- what states are reachable

It does not by itself tell us:

- which option is best
- which option should be recommended
- which tradeoff policy should dominate

### 2. Runtime Semantic Reduction

Where:
- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)
- [MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md](MARKDOWN_LEARNING_VS_RUNTIME_REDUCTION.md)

What it is good for:

- decomposing messy or under-structured semantic material
- surfacing hidden missingness
- generating candidate intermediate structure when the corpus is still not explicit enough
- finding unresolved dependencies, assumptions, or semantic gaps

What it is not:

- the final decision engine for publication
- the publication composition model
- the canonical source of recommendation truth

The architectural rule should remain:

- do not drive publication through `reduce_not()`
- use `reduce_not()` only as an assistive discovery or missingness-repair step where explicitly allowed

## Design Rule

Use the coordinated transformation model for explicit, deterministic decision evaluation.

Use `reduce_not()` only for bounded assistive discovery before or around that model.

Do not let `reduce_not()` emit the final recommendation directly.

The final recommendation must come from an explicit reviewed decision model plus an explicit policy layer.

## Where Reduce-Not Is Allowed

Allowed uses:

- identify whether a reviewed corpus item contains a latent option, dependency, constraint, state change, or actor assignment
- decompose a long paragraph into candidate decision facts
- explain why a decision candidate is incomplete
- suggest missing prerequisites or unresolved assumptions
- propose candidate options for user review

Allowed result shape:

- proposals
- missingness reports
- candidate facts
- candidate transitions
- candidate decision frames

## Where Reduce-Not Is Forbidden

Forbidden uses:

- silently deciding the final publication recommendation
- bypassing explicit review of decision facts
- replacing the deterministic decision model
- emitting “the chosen option” with no explicit reviewed policy layer
- mutating the published decision section without explicit user-governed review

## Decision Review Item

The system needs a decision-specific reviewed object model.

Each `DecisionReviewItem` should carry at least:

- `decision_review_item_id`
- `review_item_id`
- `decision_role`
- `included`
- `notes`
- `children`
- `ordering`
- `source_refs`
- `confidence`
- `review_state`

Useful decision roles include:

- actor
- objective
- capability
- dependency
- constraint
- boundary
- current state fact
- target state fact
- transition candidate
- decision candidate
- assignment candidate
- policy rule
- risk statement
- evidence-only support

## Decision Frame

A reportable decision section should start from an explicit frame.

Minimum frame:

- `subject`
- `decision question`
- `current state`
- `target state`
- `primary objective`
- `scope boundary`
- `decision mode`

Useful decision modes:

- advisory only
- shortlist only
- recommend one option
- commit a bounded decision

If the system cannot fill the minimum frame from reviewed material, it should not try to make a real decision.

It should produce a decision aid and a missingness receipt instead.

## Corpus To Model Mapping

Selected reviewed items need to map into the coordinated transformation carriers and relations.

Examples:

- reviewed owner or stakeholder item -> `Actor`
- reviewed goal item -> `Objective`
- reviewed operating ability or mechanism -> `Capability`
- reviewed prerequisite -> `Dependency`
- reviewed active restriction -> `Constraint`
- reviewed cross-organization or legal separation -> `Boundary`
- reviewed present operating mode -> `State`
- reviewed change path -> `Transition`
- reviewed candidate choice -> `Decision`

The important point is:

- reviewed corpus does not directly become recommendation prose
- reviewed corpus first becomes an explicit model

## Policy And Ranking Layer

This is the missing layer above the theory.

The coordinated transformation theory tells us feasibility and risk.

A separate explicit policy layer must tell us preference.

Each decision workflow should allow explicit policy rules like:

- prefer executable decisions over merely valid ones
- reject options with unresolved critical dependencies
- penalize options that cross high-friction boundaries
- prefer options that reduce mixed-mode exposure
- prefer options with fewer actor coordination requirements
- require explicit assignment for each changed capability
- prefer shortest reachable path to target state
- prefer lower residual risk
- require evidence from at least two independent source units

This layer must be inspectable and overridable.

It should never be implicit.

## Required Outputs

Decision review should be able to produce the following structured outputs.

### 1. Decision Aid Outputs

- decision table
- option comparison matrix
- transition roadmap
- dependency checklist
- actor assignment matrix
- risk/control table
- assumption register
- unknowns register
- simple flow diagram
- simple dependency diagram
- simple approval-gate diagram

### 2. Recommendation Outputs

- selected option
- recommendation rationale
- blocking conditions
- residual risks
- required assignments
- next-step transition sequence
- evidence basis
- confidence and caveat statement

### 3. Decision Receipts

- extracted decision facts
- model validation results
- policy/ranking results
- recommendation explanation
- unresolved missingness

## Decision Workflow

The intended workstation flow should be:

1. choose reviewed items that are relevant to a decision section
2. orient them into decision roles
3. build or update the `DecisionFrame`
4. let the system propose candidate model facts
5. review and correct those facts
6. materialize a deterministic `Model`
7. compute admissibility, validity, executability, risk, and reachability
8. apply explicit policy/ranking rules
9. emit either:
- a decision aid
- or a recommendation with receipts
10. render the result into publication sections and simple diagrams

## Workstation Actions

The workstation should eventually expose explicit actions like:

- `Create Decision Frame`
- `Promote To Decision Fact`
- `Promote To Option`
- `Promote To Constraint`
- `Promote To Dependency`
- `Promote To Actor`
- `Promote To Current State`
- `Promote To Target State`
- `Run Decision Analysis`
- `Generate Decision Table`
- `Generate Option Matrix`
- `Generate Simple Diagram`
- `Propose Missing Facts`
- `Apply Policy Profile`
- `Preview Recommendation`

These are deliberately explicit.

The user should be able to see when the system is:

- shaping composition
- shaping a decision model
- producing a recommendation

## Publication Rendering

Decision review should feed later publication sections such as:

- Recommendation
- Options Considered
- Transition Path
- Risks And Controls
- Dependencies And Preconditions
- Ownership And Next Steps
- Decision Rationale

The publication layer should not re-infer these.

It should render the already-reviewed decision outputs.

## Simple Diagrams

The near-term focus is simple diagrams, not arbitrary drawing.

Examples:

- one-step or multi-step transition flow
- dependency chain
- approval gate sequence
- actor-capability assignment map
- current-state to target-state path

These should be generated from reviewed decision structure, not freehand.

That is what keeps them auditable and governed.

## Industry Standard Decision Aids

The first serious target set should be:

- option comparison table
- decision matrix
- dependency checklist
- RACI-like assignment table
- risk and control matrix
- transition roadmap
- approval gate diagram
- simple state-transition diagram
- shortlist with rationale

This is broad enough to matter across:

- consulting reports
- transformation plans
- operations reports
- governance and compliance reports
- product or vendor selection reports
- strategy reports

## Minimal Implementation Slice

The first implementation cut should not try to solve everything.

It should provide:

1. `DecisionFrame`
2. `DecisionReviewItem`
3. corpus-to-model mapping for a narrow set of roles
4. explicit use of [coordinated_transformation/core.py](coordinated_transformation/core.py)
5. a simple policy/ranking layer
6. publication output for:
- decision table
- option shortlist
- simple transition diagram
- recommendation receipt

## Quality Gates

The system should refuse to produce a hard recommendation when:

- no explicit current state exists
- no explicit target state exists
- no candidate decision exists
- the model has axiom violations
- the selected option is not valid
- the selected option is not executable
- policy rules forbid recommendation under current uncertainty

In those cases, the system should fall back to:

- decision aid only
- plus explicit missingness and blocking conditions

## Practical Conclusion

The right architecture is:

- `Review` for composition
- `DecisionReview` for explicit decision structuring
- `coordinated_transformation` for deterministic decision analysis
- optional `reduce_not()` for bounded discovery and missingness repair
- explicit policy/ranking for recommendation
- `Publication` for rendering the final decision aids and recommendation sections

That is the cleanest route to later sections that are genuinely decision-grade rather than merely well-written prose.
