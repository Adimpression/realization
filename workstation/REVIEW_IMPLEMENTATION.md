# Review Implementation

Implementation plan for the composable review layer defined in
[REVIEW.md](REVIEW.md).

This plan assumes a future upstream
[ITEMIZE.md](ITEMIZE.md)
layer for typed normalization before composition.

This file is intentionally concrete.

It describes:

- what the current review layer already does
- what is still missing
- which object models should be introduced
- how the workstation should expose them
- and which implementation phases should prove the slice

## Current Position

The current review layer is no longer a trivial toggle strip.

It already has:

- explicit report-plan creation and approval
- persisted `ReviewComposition` and `ReviewItem` records
- semantic/render/evidence/transform orientation for selected draft items
- child split, sibling merge, and child-to-root promotion inside `Draft`
- a report-scope tree
- include/exclude selection
- keyboard-driven reordering and held-block movement
- maintained-file comparison
- publication-composition shaping over unit scope, section scope, and approved import usage
- publication seeding from included draft leaf review items, so split child review items survive into claims and render order
- publication preview/build/release handoff

Implemented primarily in:

- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [workstation/chat_ui.py](workstation/chat_ui.py)
- [publication.py](publication.py)
- [publication_projection.py](publication_projection.py)
- [tests/test_subject_workflow.py](tests/test_subject_workflow.py)
- [tests/test_workstation_chat_ui.py](tests/test_workstation_chat_ui.py)

That means the next problem is not “introduce review at all”.

The next problem is:

- move from scope toggles to composable review items
- keep the existing governed flow intact while widening what review can shape

## Core Implementation Decision

Implement a first-class `ReviewItem` layer between learned subject units and publication blocks.

Do not try to hide this inside:

- publication rendering only
- free-form workstation notes
- ad hoc per-section mutation

The relationship should become:

`Learning unit -> ItemizedSubjectItem -> ReviewItem tree -> PublicationComposition / DecisionReview -> Rendered publication`

## Scope Rule

`Review` is still broader than publication.

It is responsible for:

- orienting learned material
- shaping composition
- deciding whether something becomes prose, table, equation block, diagram, figure, or appendix content

It is not responsible for:

- final report rendering
- final recommendation ranking
- runtime semantic reduction

Those remain elsewhere.

## Current Gaps

The current review flow is still missing:

- figure/table/diagram specialization beyond the basic render-kind flags
- rewrite proposal lifecycle
- direct transform receipts
- fuller publication block/section ownership by review composition instead of only unit-derived defaults

Right now, much of that intent is implicit in the report plan and publication composition.

That is too thin for real industry-report composition.

## First Object Model

The first implementation slice should introduce a dedicated module, likely:

- `review_composition.py`

with optional follow-on helpers such as:

- `review_projection.py`
- `review_validation.py`

### `ReviewItem`

Required fields:

- `review_item_id`
- `subject_id`
- `source_unit_id`
- `parent_review_item_id`
- `semantic_kind`
- `render_kind`
- `evidence_mode`
- `transform_mode`
- `included`
- `ordering`
- `child_review_item_ids`
- `notes`
- `status`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`
- `version_hash`

### `ReviewComposition`

Required fields:

- `review_composition_id`
- `subject_id`
- `learning_context_snapshot_hash`
- `root_review_item_ids`
- `included_review_item_ids`
- `excluded_review_item_ids`
- `status`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`
- `schema_version`

### `ReviewTransformReceipt`

Required fields:

- `receipt_id`
- `review_item_id`
- `transform_kind`
- `input_snapshot_hash`
- `output_snapshot_hash`
- `operator`
- `notes`
- `created_at_epoch_ms`

## Required Enumerations

The first narrow implementation should support:

### Semantic kinds

- `equation`
- `claim`
- `multi_claim_paragraph`
- `table_like`
- `process`
- `decision_rule`
- `definition`
- `metric`
- `timeline`
- `risk_control`
- `figure_asset`

### Render kinds

- `paragraph`
- `equation_block`
- `claim_panel`
- `citation_callout`
- `typst_table`
- `decision_table`
- `flow_diagram`
- `dependency_diagram`
- `metric_card`
- `figure_with_caption`
- `appendix_note`

### Evidence modes

- `inline_handles`
- `source_basis_panel`
- `citation_box`
- `footnote_handles`
- `appendix_only`

### Transform modes

- `keep`
- `split`
- `merge`
- `rewrite_manual`
- `rewrite_llm_proposal`
- `convert_to_table`
- `convert_to_diagram`
- `convert_to_equation_legend`

## Implementation Phases

### Phase 1. Typed Review Items

Status: implemented.

Introduce:

- `ReviewItem`
- `ReviewComposition`
- deterministic persistence under the subject corpus tree

Goal:

- stop storing review intent only as thin report-plan state

Acceptance:

- review compositions round-trip on disk
- review items are independently addressable and ordered
- existing report-plan flows still work

### Phase 2. Orientation Controls

Status: implemented.

Expose in the workstation:

- semantic kind
- render kind
- evidence mode
- transform mode

Goal:

- let the user orient an item without needing to leave the governed flow

Acceptance:

- a selected review item can be re-oriented and persisted
- item orientation affects later publication composition deterministically

### Phase 3. Child Composition

Status: implemented for the first deterministic slice.

Expose:

- split item into children
- merge siblings
- reorder children
- promote a child into a first-class review item

Goal:

- allow one learned unit to become multiple publication blocks

Acceptance:

- a paragraph can be split into claims
- an equation can gain a variable legend child
- a decision rule can become a decision table item with an explanatory note child

Implemented first cut:

- split selected draft item into child review items
- merge with next sibling
- promote child review item to root
- child-aware draft inventory ordering and selection

### Phase 4. Rewrite And Conversion Receipts

Status: implemented for the first narrow slice.

Introduce:

- explicit rewrite proposals
- conversion receipts
- retained provenance to source units

Goal:

- composition changes become inspectable and replayable

Acceptance:

- rewrite/convert actions record receipts
- publication output can trace back to review transforms

Implemented first cut:

- `ReviewTransformReceipt` now persists split/merge/promote transform provenance
- `Draft` and `Gather` surface recent transform receipts and receipt counts
- publication composition carries recent transform receipts into composition metadata
- publication materialization emits draft-transform provenance as a governed appendix block

### Phase 5. Publication Integration

Status: implemented for the first narrow slice.

Wire review items into publication composition so that:

- publication renders review-owned structure rather than re-inferring it

Acceptance:

- selected render kinds deterministically affect the built report
- tables, equation blocks, and figure blocks originate from review items

Implemented first cut:

- publication composition persists the current draft review item snapshots
- publication materialization consumes included leaf review items in tree order
- split child review items survive into publication claims and rendered output
- non-paragraph review render kinds now emit review-owned publication blocks
- review-owned table-like blocks now render through the publication layer instead of being only implied by claim order

Still missing:

- fuller section/block ownership by review composition
- direct rewrite proposal lifecycle and conversion-specific receipt families
- broader figure/diagram specialization beyond the current narrow table/metric/diagram text slice
- deeper review-owned block families for figures and richer diagram semantics instead of plain text diagram panels

## Workstation Changes

The workstation review tab will need:

- pane-level item navigation
- drill-in into the selected review item
- item orientation actions
- child management actions
- conversion actions
- rewrite proposal actions
- preview of the render consequence

Near-term actions should include:

- `Set Semantic Kind`
- `Set Render Kind`
- `Set Evidence Mode`
- `Set Transform Mode`
- `Split Into Children`
- `Merge With Previous`
- `Convert To Table`
- `Convert To Diagram`
- `Convert To Equation Block`
- `Add Figure Caption`
- `Preview Render Block`

## Validation

Review validation should eventually enforce:

- no orphan child review items
- stable ordering within a parent
- no invalid semantic/render kind combinations
- no diagram/table render kinds without enough structure
- no figure-with-caption without figure asset refs
- no LLM rewrite acceptance without source linkage retention

## Testing Strategy

Prefer seam-level tests over long controller-path tests.

Add:

- pure review-item roundtrip tests
- orientation validation tests
- split/merge/reorder tests
- receipt-generation tests
- publication-projection tests from review items
- workstation interaction tests only after the seam is stable

## Recommended Immediate Next Step

Implement the next composition-widening slice:

1. add explicit rewrite and conversion actions beyond split/merge/promote
2. persist richer receipt families for `convert_to_table`, `convert_to_diagram`, and rewrite proposals
3. let publication render review-owned table/diagram/figure blocks instead of only prose-claim ordering
4. keep the receipt trail inspectable from `Draft`, `Gather`, and publication outputs

That is the next smallest cut that makes composable review materially richer instead of only more traceable.
