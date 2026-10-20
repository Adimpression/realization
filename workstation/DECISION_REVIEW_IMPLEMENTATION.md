# Decision Review Implementation

Implementation plan for the decision-oriented review layer defined in
[DECISION_REVIEW.md](DECISION_REVIEW.md).

This file is intentionally concrete.

It describes:

- how decision review should sit on top of generic review
- how it should use coordinated transformation theory
- where `reduce_not()` is allowed
- what extra policy/ranking layer is required
- and how to deliver publication-grade decision aids and recommendations

## Current Position

The repo now has three relevant ingredients:

1. a shaped review/publication workflow
- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [publication_projection.py](publication_projection.py)

2. a reusable deterministic decision model
- [coordinated_transformation/core.py](coordinated_transformation/core.py)
- [COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md](COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md)

3. a first bridging substrate
- [decision_review.py](decision_review.py)
- [decision_review_projection.py](decision_review_projection.py)
- [decision_review_policy.py](decision_review_policy.py)

What now exists in narrow form is:

- persisted `DecisionFrame`
- persisted `DecisionReviewItem`
- first mapping into `coordinated_transformation.Model`
- first analysis receipts

What does not yet exist is the fuller layer that turns reviewed corpus material into:

- an explicit decision frame
- an explicit decision model
- decision aids
- or a bounded recommendation

That is the gap this implementation plan covers.

## Core Implementation Decision

Implement a separate `DecisionReview` substrate on top of the composable review layer, surfaced primarily through `Draft` and consumed by `Publication`.

Do not try to make publication itself infer decision logic from prose.

Do not let `reduce_not()` directly own the recommendation.

The relationship should become:

`ItemizedSubjectItem -> ReviewItem -> DecisionReviewItem -> CoordinatedTransformation Model -> Policy evaluation -> Publication decision output`

## Boundary Rule

Use:

- [coordinated_transformation/core.py](coordinated_transformation/core.py)

for:

- admissibility
- validity
- executability
- risk
- reachability
- model sanity checking

Use:

- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)

only for:

- optional assistive discovery
- optional missingness repair
- optional candidate extraction

Never use `reduce_not()` as the final recommendation engine.

## Required New Modules

The first implementation slice should introduce:

- `decision_review.py`
- `decision_review_projection.py`
- `decision_review_policy.py`

Deferred until needed:

- `decision_review_render.py`

because publication should own final rendering.

## First Object Model

### `DecisionFrame`

Required fields:

- `decision_frame_id`
- `subject_id`
- `publication_id`
- `question`
- `decision_mode`
- `current_state_ids`
- `target_state_ids`
- `primary_objective_ids`
- `scope_boundary_ids`
- `status`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`

### `DecisionReviewItem`

Required fields:

- `decision_review_item_id`
- `review_item_id`
- `decision_frame_id`
- `decision_role`
- `included`
- `ordering`
- `child_decision_review_item_ids`
- `source_refs`
- `confidence`
- `notes`
- `status`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`

### `DecisionOption`

Required fields:

- `decision_option_id`
- `decision_frame_id`
- `title`
- `selected_transition_ids`
- `selected_assignment_refs`
- `status`
- `notes`

### `DecisionPolicyProfile`

Required fields:

- `policy_profile_id`
- `decision_frame_id`
- `rule_ids`
- `status`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`

### `DecisionAnalysisReceipt`

Required fields:

- `receipt_id`
- `decision_frame_id`
- `model_snapshot_hash`
- `policy_snapshot_hash`
- `admissible_transition_ids`
- `valid_decision_ids`
- `executable_decision_ids`
- `risk_summary`
- `reachable_pairs_count`
- `blocking_conditions`
- `recommendation_status`
- `created_at_epoch_ms`

## Decision Roles

The first narrow implementation should support:

- `actor`
- `objective`
- `capability`
- `dependency`
- `constraint`
- `boundary`
- `current_state`
- `target_state`
- `transition_candidate`
- `decision_candidate`
- `assignment_candidate`
- `risk_statement`
- `supporting_evidence`

## Coordinated Transformation Mapping

Decision review must map reviewed items into the theory carriers and relations.

Examples:

- actor review item -> `Actor`
- objective review item -> `Objective`
- operating mechanism -> `Capability`
- prerequisite -> `Dependency`
- active restriction -> `Constraint`
- organizational/legal edge -> `Boundary`
- present mode -> `State`
- proposed path -> `Transition`
- candidate option -> `Decision`

The mapping layer should be explicit and inspectable.

It should produce a concrete `Model`, not just inferred prose.

## Policy Layer

The theory layer does not choose the best option.

So a separate explicit policy layer must be implemented.

The first policy rules should support:

- prefer executable over merely valid
- reject unresolved critical dependencies
- penalize active high-friction boundaries
- penalize coordination-heavy transitions
- prefer shorter reachable paths
- prefer lower residual risk
- require source support above a minimum threshold

This layer should be fully inspectable and adjustable from review.

## Implementation Phases

### Phase 1. Decision Frame

Status: implemented.

Add:

- `DecisionFrame`
- narrow workstation creation/editing

Goal:

- make the decision question, current state, and target state explicit

Acceptance:

- a publication subject can have a persisted decision frame
- the frame round-trips from disk deterministically

### Phase 2. Decision Roles

Status: implemented for the first narrow slice.

Add:

- `DecisionReviewItem`
- role assignment from selected review items

Goal:

- let the user promote reviewed material into decision structure

Acceptance:

- selected reviewed items can be assigned to decision roles
- those assignments persist and reorder deterministically

### Phase 3. Model Materialization

Status: implemented for the first narrow slice.

Add:

- mapping from `DecisionFrame` + `DecisionReviewItem`s into `coordinated_transformation.Model`

Goal:

- decision review becomes computable instead of only descriptive

Acceptance:

- the system can materialize a valid `Model`
- model construction errors are reported as explicit blocking conditions

### Phase 4. Analysis Receipts

Status: implemented for the first narrow slice.

Use:

- `admissible_transition(...)`
- `valid_decision(...)`
- `executable_decision(...)`
- `risk_capability(...)`
- `risk_transition(...)`
- `least_reachable_closure(...)`

Goal:

- produce deterministic decision-analysis outputs

Acceptance:

- analysis receipts are persisted
- the workstation can preview blocked vs admissible vs executable options

### Phase 5. Policy Evaluation

Status: implemented for the first narrow slice.

Add:

- `DecisionPolicyProfile`
- rule execution over the deterministic model outputs

Goal:

- make recommendation ranking explicit rather than implicit

Acceptance:

- different policy profiles can yield different ranked outcomes over the same model
- the chosen recommendation can be justified by explicit rules

Implemented first cut:

- persisted `DecisionPolicyProfile`
- workstation policy cycling over the active decision frame
- policy-aware analysis receipts with `policy_profile_kind`, rule ids, option outcomes, and recommended option ids
- policy blocking conditions now participate in recommendation status

### Phase 6. Publication Outputs

Status: implemented for the first narrow slice.

Render:

- decision table
- option matrix
- dependency checklist
- risk/control matrix
- transition roadmap
- simple transition or dependency diagram
- recommendation receipt

Goal:

- make the later publication sections decision-grade

Acceptance:

- publication can build a recommendation section from decision-review outputs without re-inferring logic from prose

Implemented first cut:

- publication composition now carries decision frame, policy profile, and latest analysis receipt snapshots
- report publications emit a `Decision Recommendation` summary block
- report publications emit a `Decision Option Matrix` block
- report publications emit a `Decision Transition Roadmap`
- report publications emit a `Decision Model Diagram`
- report publications emit a `Decision Dependency Checklist`
- report publications emit a `Decision Risk Matrix`
- report publications emit a `Decision Recommendation Receipt`
- draft transform provenance is carried alongside the decision outputs

Still missing:

- richer decision tables beyond the current option matrix
- stronger diagramming beyond the current simple roadmap/diagram slice
- fuller recommendation receipts and richer policy/ranking surfaces
- more explicit option-to-transition / assignment reasoning surfaces

## Reduce-Not Integration

`reduce_not()` should only be integrated at bounded seams.

Safe first uses:

- `Discover Decision Frame`
- `Propose Missing Facts`
- `Suggest Candidate Options`
- `Explain Why Blocked`

Each of these must produce proposals or receipts, not final state mutation without review.

## Workstation Actions

The workstation should eventually expose:

- `Create Decision Frame`
- `Edit Decision Frame`
- `Promote To Actor`
- `Promote To Objective`
- `Promote To Dependency`
- `Promote To Constraint`
- `Promote To Current State`
- `Promote To Target State`
- `Promote To Option`
- `Run Decision Analysis`
- `Apply Policy Profile`
- `Generate Decision Table`
- `Generate Simple Diagram`
- `Preview Recommendation`

## Validation

Decision review should block hard recommendation when:

- no current state exists
- no target state exists
- no candidate option exists
- the theory model has axiom violations
- no valid option exists
- no executable option exists
- policy rules do not permit recommendation under current missingness

Fallback behavior should be:

- decision aid only
- plus explicit blocking conditions

## Testing Strategy

Add seam-level tests first:

- decision frame persistence tests
- decision-role mapping tests
- model materialization tests
- policy profile evaluation tests
- analysis receipt tests
- publication-output tests from decision review

Only after those should workstation interaction tests be widened.

## Recommended Immediate Next Step

Implement the next decision-output widening slice:

1. expand policy evaluation from preset profiles into more explicit adjustable ranking surfaces
2. emit richer decision tables, dependency/risk matrices, and simple diagrams from the reviewed model
3. attach fuller recommendation receipts that explain why one option outranked another
4. keep `reduce_not()` bounded to proposal/explanation seams rather than recommendation ownership

That extends the current bounded recommendation slice into stronger industry-report decision aids without collapsing back into prose inference.
