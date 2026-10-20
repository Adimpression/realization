# Itemize Implementation

Implementation plan for the typed normalization layer defined in
[ITEMIZE.md](ITEMIZE.md).

This file is intentionally concrete.

It describes:

- what already exists that can support `Itemize`
- what still needs to be implemented
- what object models should be introduced
- how the workstation should expose the layer
- and how to phase the work safely

## Current Position

The repo already has ingredients that make `Itemize` feasible:

- admitted subject material in `LearningContext`
- deterministic source and delta persistence
- maintained subject projections
- publication composition and review scaffolding
- URL-origin bundles that preserve richer artifacts than markdown alone

Implemented in:

- [learning_context.py](learning_context.py)
- [learning_context_projection.py](learning_context_projection.py)
- [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
- [url_learning_capture.py](url_learning_capture.py)

What does not yet exist is a separate itemization substrate.

Right now:

- some extraction happens during learning
- some structure is implicit in maintained subject projections
- some later shaping is pushed into review/publication

That is not enough for a real `Itemize` stage.

## Core Implementation Decision

Implement `Itemize` as a subject-scoped, persisted, typed intermediate layer.

Do not implement it as:

- a loose tag list
- workstation-only transient state
- implicit metadata hidden inside later publication composition

The layer should be explicit on disk and explicit in the workstation.

## Source Cleanup And Rephrase Boundary

The source layer and the itemization layer must stay separate.

Rules:

- source cleanup is narrow:
  - remove internal jargon
  - remove formatting noise
  - keep the source readable as source
- source cleanup must not try to make the source read like the final publication
- rephrase belongs in `Itemize`, not in source cleanup
- `Itemize` should support both:
  - rephrase using LLM
  - rephrase using manual editing
- the first workstation slice now exists:
  - `@llm` on the selected itemized candidate opens a rephrase request in `Chat`
  - that chat turn now stages a pending LLM rephrase target for the selected intermediate
  - the latest assistant reply can then be explicitly applied or discarded back into the persisted itemized intermediate
  - `=` on the selected itemized candidate opens a manual rephrase file and applies it back into the persisted itemized intermediate
- the next preservation slice now also exists:
  - when itemization regenerates from refreshed source/context material, it keeps stable item identity through source-continuity matching rather than regenerating a brand-new intermediate every time
  - if an itemized intermediate was explicitly rephrased in `Itemize`, whether manually or through an applied LLM reply, that wording is preserved across regeneration while the latest generated wording is still recorded in metadata for later inspection
- the broader DST workstation entry point now follows the same rule:
  - `Itemize -> Suggest Constructs` upserts refreshed DST construct suggestions through continuity-based merge rather than replacing them by fresh generated ids
  - curated construct ids, notes, accepted state, and canonical wording therefore survive refreshed discovery and label churn while the latest generated wording remains visible in metadata

That keeps source prose as provenance while allowing normalized items to improve over time.

## Required New Modules

The first implementation slice should introduce:

- `itemize.py`
- `itemize_projection.py`
- `itemize_validation.py`

Optional later helpers:

- `itemize_search.py`
- `itemize_decision_mapping.py`

## First Object Model

### `ItemizedSubjectItem`

Required fields:

- `itemized_item_id`
- `subject_id`
- `source_unit_id`
- `item_kind`
- `canonical_label`
- `aliases`
- `summary`
- `source_refs`
- `status`
- `confidence`
- `linked_item_ids`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`
- `schema_version`

### `ItemizationSession`

Required fields:

- `itemization_session_id`
- `subject_id`
- `learning_context_snapshot_hash`
- `item_ids`
- `status`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`

### `ItemizationReceipt`

Required fields:

- `receipt_id`
- `itemization_session_id`
- `operator`
- `input_snapshot_hash`
- `output_snapshot_hash`
- `notes`
- `created_at_epoch_ms`

## First Item Kinds

The first narrow implementation should support:

- `glossary_term`
- `keyword`
- `entity`
- `claim`
- `assumption`
- `equation`
- `variable`
- `metric`
- `table_candidate`
- `figure_candidate`
- `diagram_candidate`
- `citation_anchor`
- `xref_candidate`
- `decision_role_candidate`

Later widening can split `decision_role_candidate` into narrower first-class kinds.

## Persistence Layout

The layer should persist under the subject corpus tree, for example:

- `corpus/<subject>/itemization/session.json`
- `corpus/<subject>/itemization/items/<item-id>.json`
- `corpus/<subject>/itemization/receipts/<receipt-id>.json`

The exact layout can vary, but the invariants should be:

- subject-scoped
- deterministic
- snapshot-aware
- independently queryable

## Implementation Phases

### Phase 1. Subject-Scoped Item Storage

Add:

- `ItemizedSubjectItem`
- `ItemizationSession`
- deterministic persistence and loading

Goal:

- make itemization explicit and durable

Acceptance:

- a subject can persist an itemization session
- items round-trip deterministically

### Phase 2. Narrow Auto-Itemization

Add a bounded extractor over learned units for:

- glossary terms
- entities
- equations
- claims
- decision-role candidates

Goal:

- populate useful initial candidates without pretending the system solved all semantics

Acceptance:

- a fresh subject can generate an initial itemization set
- low-confidence items are marked as such

### Phase 3. Manual Normalization

Expose workstation actions for:

- rename canonical label
- add alias
- change item kind
- merge duplicate items
- split overloaded items
- promote candidate to stable item
- reject noisy item

Goal:

- put the user in control of normalization quality

Acceptance:

- manual edits persist deterministically
- merge/split actions retain provenance

### Phase 4. Downstream Projections

Add mapping from itemized items into:

- `ReviewItem` proposals
- glossary blocks
- figure/table candidates
- decision-role candidates for `DecisionReview`

Goal:

- make `Itemize` a real upstream layer rather than a dead-end inventory

Acceptance:

- draft/review can consume itemized items directly

### Phase 5. Search And Indexing

Add query/index support for:

- canonical labels
- aliases
- item kind
- source refs
- decision-role candidates

This is the right place to later use SQLite FTS5 where helpful.

## Workstation Actions

The current first cut of the `Itemize` tab already exposes:

- `Generate Itemization`
- `Refresh Itemization`
- `Promote Item`
- `Reject Item`
- `Return To Candidate`
- `Cycle Decision Role`
- `Hold For Merge` / `Unhold Item`
- `Merge Held Items`
- `Split Item`
- `Preview Selected Item`

The next cuts should expose:

- `Promote To Glossary Term`
- `Promote To Entity`
- `Promote To Claim`
- `Promote To Equation`
- `Promote To Decision Candidate`
- `Merge Items`
- `Split Item`
- `Edit Canonical Label`
- `Add Alias`
- `Reject Item`
- `Open Source Basis`

## Validation

Itemization validation should aim to enforce:

- no duplicate canonical item ids
- explicit item kind for every persisted item
- source refs present for every item
- no merge without preserved provenance
- no alias cycle corruption
- no downstream projection from rejected items

## Testing Strategy

Prefer seam-level tests:

- item roundtrip tests
- duplicate merge tests
- split tests
- alias normalization tests
- initial extractor tests
- projection tests into review and decision layers

Only after those are stable should workstation interaction tests be widened.

## Recommended Immediate Next Step

The next clean step is to deepen the handoff from `Itemize` into `Draft`:

1. add explicit item filtering and item-kind views inside the `Itemize` tab
2. add alias editing and source-basis inspection
3. project promoted itemized candidates into a persisted draft-composition substrate
4. let `Draft` operate over itemized candidates directly instead of only over the current publication-scope tree

That is the smallest next cut that turns the current item inventory/editor into a true upstream composition substrate.
