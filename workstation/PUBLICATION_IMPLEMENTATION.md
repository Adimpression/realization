# Publication Implementation

Implementation plan for the governed publication model defined in [PUBLICATION.md](PUBLICATION.md).

This file is intentionally concrete.

It describes:

- where `Publication` should sit in the current architecture
- how it should relate to `LearningContext`
- what first object models are needed
- how deterministic publication builds should work
- what should not be done
- and which validation scenarios should prove the implementation

## Current Position

The first narrow slice now exists:

- typed `Publication`, `PublicationSection`, `PublicationClaim`, `PublicationSource`, `PublicationBuild`, and `RenderArtifact` records
- typed `PublicationComposition` records as the review-owned composition layer between `LearningContext` and `PublicationBuild`
- typed `PublicationCrossReference` records with deterministic section-to-section report links persisted under `xrefs/`
- typed `PublicationBlock` records with deterministic rendered transclusion persisted under `blocks/`
- explicit publication storage under `corpus/<subject-id>/publications/<publication-id>/`
- deterministic `publication_type = report` projection from `LearningContext`
- deterministic composition persistence under `corpus/<subject-id>/publications/<publication-id>/compositions/`
- archived composition revisions under `corpus/<subject-id>/publications/<publication-id>/composition_revisions/`
- review-owned composition shaping over selectable unit scope, section-plan scope, and approved import usage
- review-visible diffing against the previously approved composition when available
- deterministic Typst and markdown outputs
- validation over section ids, block/transclusion integrity, claim/source references, xref integrity, and source-backed descriptive claims
- a workstation review flow that drafts, previews, approves, and then builds from those compositions without re-owning publication semantics in the shell layer

Implemented in:

- [publication.py](publication.py)
- [publication_projection.py](publication_projection.py)
- [publication_render.py](publication_render.py)
- [publication_validation.py](publication_validation.py)
- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [workstation/chat_ui.py](workstation/chat_ui.py)
- [tests/test_publication.py](tests/test_publication.py)

Important scope rule:

- `LearningContext` is broader than publication
- not every subject context should become a publication
- publication remains an optional governed release layer over selected context, not the default purpose of subject memory

## Implementation Decision

Implement:

- `Publication`

as a first-class concept

with initial support for:

- `publication_type = report`

Do not implement “report publishing” as:

- just a Typst file writer
- just a markdown renderer
- just a workstation tool that appends prose

The publication layer must be semantically typed and reproducible.

## Relationship To Existing Repo

This new publication layer should sit:

- above `LearningContext`
- beside skill projection
- below workstation UI projection

In other words:

- `LearningContext` remains the durable subject memory
- `Publication` becomes a governed release/specification layer over that memory
- render output becomes a build artifact

It should not replace:

- existing artifact persistence
- existing skill persistence
- existing runtime evidence/claim machinery
- existing validation and trace `report.json` outputs

## Current Priority Order

The next implementation cuts should favor the typed publication graph needed for governed shipping, not a broad ontology all at once.

Recommended order:

1. continue widening the publication outputs now that the first `dst/*.md` acceptance corpus is green:
   - keep using the existing workstation flow over `dst/*.md`
   - keep source cleanup narrow:
     - remove DST/internal jargon
     - remove formatting noise
     - do not tune source wording into publication prose
   - widen publication quality through learned intermediates, explicit rephrase in `Itemize` and `Draft`, review-owned composition, and publication shaping
   - the current bounded slices now include richer decision tables, fuller option-to-transition / actor-assignment reasoning in the matrix, execution guidance, and recommendation receipt, plus a ranking summary with policy profile / rules / candidate-path count
   - keep part of the corpus source-only and without explicit candidate paths so the workstation path is exercised on discovery-first cases too
   - the latest bounded PDF-quality slice now also replaces the unreadable narrow option grid with full-width option cards in Typst/PDF output, gives the model diagram a clearer state / transition / dependency / boundary layout, and surfaces boundary-governance guidance explicitly in the implementation and receipt surfaces
   - the latest publication-guidance slice now also:
     - adds editorial guidance and reserve / blocked option callouts to the ranking surface
     - explains why reserve options remain in reserve and what must change to promote them
     - explains why blocked options remain disqualified before reconsideration
     - separates recommended, reserve, and blocked paths in the model diagram
     - carries capability / dependency / boundary reasoning with the specific recommended and reserve/blocked options
   - the latest publication-structure slice now also:
     - materializes a real decision-publication section tree instead of a flat scaffold
     - nests analysis/model/risk subsections under `Analysis`
     - nests implementation-guidance subsections under `Implementation`
     - nests receipt/audit subsections under `Appendix`
   - the latest richer-diagramming slice now also:
     - renders a fuller path-and-coordination publication surface instead of only a compressed recommended/reserve/blocked summary
     - carries option-specific actors, capabilities, dependencies, and boundaries with the recommended, reserve, and blocked path cards
     - has been inspected in real workstation-built library and clinic PDFs, not only through markdown / Typst assertions
   - the latest composition/layout slice now also:
     - gives subsections content-aware titles instead of one fixed decision template
     - drops empty scaffold sections from the materialized publication tree
     - keeps longer reserve / blocked option cards readable on paper through page-aware layout
   - the latest readability/formatting slice now also:
     - replaces raw `->` path text with reader-facing `→` arrows in publication outputs
     - turns decision summary and recommendation prose into structured fields instead of paragraph blobs
     - replaces the unreadable risk-matrix grid with stacked risk cards in Typst/PDF
     - prevents ranking-summary content from orphaning or clipping at page boundaries
- the latest validation/xref slice now also:
  - enforces stronger section-role constraints
  - validates richer xref/transclusion integrity
  - materializes typed claim-to-unit/source/entity xrefs for queryability
- the latest composition-diff slice now also:
  - exposes explicit diff-baseline selection in the workstation instead of silently choosing one baseline
  - supports comparing the current report plan against:
    - the last approved plan
    - the previous persisted revision
    - the full current-subject snapshot baseline
  - keeps that chosen baseline visible in Review/Publication workspace text and diff receipts
- the latest composition-scope slice now also:
  - keeps arbitrary unit inclusion in place
  - adds direct per-section shaping through Review-side section briefs (`@llm` and `=`)
  - keeps arbitrary approved-import selection in place
  - widens governed import-usage control beyond the old blind cycle-only path through explicit per-mode actions for the selected imported-support item
- the next widening work is:
  - further reduction of repetitive policy/path narration across ranking, model, and implementation sections
2. continue widening publication composition beyond the current section-brief/import-use slice:
   keep composition guidance publication-facing, reduce repeated policy/path narration, and preserve the source-vs-intermediate boundary
3. strengthen validation and query surfaces around compositions, imports, and review records
4. deepen publication entities and richer review records where the report structure needs them

Deferred until the substrate above is real:

- publication-wide fact modeling as a larger separate substrate
- PDF/HTML output as primary implementation focus
- workstation-owned publication semantics beyond the current thin Textual projection

## First Object Model

Implemented root-level modules:

- `publication.py`
- `publication_render.py`
- `publication_validation.py`
- `publication_projection.py`

Deferred until needed:

- `publication_store.py`

Recommended first workstation integration modules later:

- `workstation/publication_management.py`
- `workstation/publication_actions.py`

## Required Core Types

The first implementation slice should define:

### `Publication`

Required fields:

- `publication_id`
- `publication_type`
- `subject_id`
- `title`
- `status`
- `scope_summary`
- `learning_context_ref`
- `included_unit_ids`
- `excluded_unit_ids`
- `root_section_ids`
- `block_ids`
- `claim_ids`
- `entity_ids`
- `source_ids`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`
- `schema_version`

### `PublicationComposition`

Required fields:

- `composition_id`
- `publication_id`
- `subject_id`
- `publication_type`
- `title`
- `scope_summary`
- `learning_context_snapshot_hash`
- `selected_subject_import_ids`
- `included_unit_ids`
- `excluded_unit_ids`
- `section_ids`
- `import_usage_by_id`
- `status`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`
- `schema_version`

### `PublicationSection`

Required fields:

- `section_id`
- `publication_id`
- `parent_section_id`
- `role`
- `title`
- `ordinal`
- `child_section_ids`
- `block_ids`
- `claim_ids`
- `xref_ids`
- `status`
- `version_hash`

### `PublicationBlock`

Required fields:

- `block_id`
- `publication_id`
- `block_kind`
- `title`
- `body`
- `included_block_refs`
- `status`
- `version_hash`

### `PublicationClaim`

Required fields:

- `claim_id`
- `publication_id`
- `statement`
- `claim_kind`
- `scope`
- `status`
- `certainty`
- `source_ids`
- `entity_ids`
- `related_unit_ids`
- `xref_ids`
- `last_reviewed_epoch_ms`
- `version_hash`

### `PublicationSource`

Required fields:

- `source_id`
- `publication_id`
- `title`
- `publisher`
- `source_ref`
- `published_at`
- `retrieved_at_epoch_ms`
- `trust_class`
- `freshness_class`
- `jurisdiction`
- `excerpt`
- `version_hash`

### `PublicationEntity`

Required fields:

- `entity_id`
- `publication_id`
- `entity_kind`
- `canonical_name`
- `aliases`
- `source_ref`
- `version_hash`

### `PublicationCrossReference`

Required fields:

- `xref_id`
- `publication_id`
- `from_id`
- `to_id`
- `xref_type`
- `from_kind`
- `to_kind`
- `status`
- `metadata`
- `version_hash`

### `PublicationReviewRecord`

Required fields:

- `review_id`
- `publication_id`
- `target_kind`
- `target_id`
- `review_state`
- `reviewer`
- `reason`
- `created_at_epoch_ms`

### `PublicationBuild`

Required fields:

- `build_id`
- `publication_id`
- `publication_snapshot_hash`
- `learning_context_snapshot_hash`
- `renderer_id`
- `renderer_version`
- `template_id`
- `template_version`
- `build_status`
- `started_at_epoch_ms`
- `finished_at_epoch_ms`
- `validation_report`
- `render_artifact_ids`

### `RenderArtifact`

Required fields:

- `render_artifact_id`
- `build_id`
- `format`
- `output_path`
- `content_hash`
- `created_at_epoch_ms`

## Initial Storage Layout

The publication layer should live inside the subject corpus home.

Suggested path:

```text
corpus/
  <subject-id>/
    context.json
    publications/
      <publication-id>/
        publication.json
        compositions/
          <composition-id>.json
        composition_revisions/
          <composition-id>__<updated-at>.json
        sections/
          <section-id>.json
        blocks/
          <block-id>.json
        claims/
          <claim-id>.json
        sources/
          <source-id>.json
        entities/
          <entity-id>.json
        xrefs/
          <xref-id>.json
        reviews/
          <review-id>.json
        builds/
          <build-id>.json
        outputs/
          <build-id>/
            report.typ
            report.md
            report.html
            report.pdf
```

This storage should remain explicit and inspectable.

Do not hide publication state only inside one SQLite table initially.

If a store abstraction is added, it should still preserve durable exportable on-disk form.

## Relationship To Learning Context

The first implementation should not permit a publication without explicit origin from `LearningContext`.

That origin should record:

- `subject_id`
- `learning_context_ref`
- `learning_context_snapshot_hash`
- selected unit ids
- publication scope notes

This is required for reproducibility.

But the inverse is not required:

- `LearningContext` may exist without any publication
- publication creation should be an explicit later act over selected context scope

Draft/Review-stage publication composition should sit in between:

- `LearningContext` provides maintained subject truth
- `PublicationComposition` selects the subset and structure approved for shipping
- `PublicationBuild` renders only that approved composition

## Deterministic Build Inputs

Publication reproducibility depends on explicit build inputs.

Each build must freeze:

- publication spec snapshot
- publication composition snapshot
- learning context snapshot
- included unit set
- transcluded block versions
- citation/source resolution payload
- render template
- renderer version
- asset versions

No build should depend on:

- current chat prompt text
- current workstation panel state
- ambient hidden LLM context
- nondeterministic source ordering

## Initial Publication Build Pipeline

Phase-1 build pipeline:

1. load publication spec
2. load approved publication composition snapshot
3. load referenced learning context snapshot
4. load referenced units, sources, entities, and claims
4. validate publication structure
5. resolve xrefs and transclusions
6. deterministically order sections and claims
7. materialize Typst source
8. optionally materialize markdown mirror
9. compute content hashes
10. persist `PublicationBuild`
11. register output `RenderArtifact`s

Initial required outputs:

- `.typ`
- `.md`

Deferred outputs:

- `.pdf`
- `.html`

This keeps the first slice deterministic without blocking on a full PDF toolchain.

## Initial Renderer Strategy

Do not start with a highly dynamic renderer.

Start with:

- one deterministic Typst projection
- one deterministic markdown projection

Both should be generated from the same typed publication substrate.

## Source Prose Versus Publication Truth

As the DST-backed publication flow is industrialized, source markdown should be treated as governed input prose, not as publication truth.

That means:

- source markdown may be cleaned only enough to remove DST/internal jargon and formatting noise
- source markdown must not be tuned into publication prose
- ingestion should preserve that source as provenance
- publication composition should prefer learned intermediate structures such as:
  - normalized DST cases
  - decision frames
  - decision review items
  - analysis receipts
  - review transform receipts
- publication should emit curated report blocks from those intermediates rather than dumping raw source wording into the report body

Publication-quality wording should come from explicit rephrase operations later in the workflow:

- `Itemize` rephrase using LLM
- `Itemize` rephrase using manual editing
- `Draft` rephrase using LLM
- `Draft` rephrase using manual editing

This keeps the source editable while making the publication reproducible and upgradable:

`source prose -> learning context -> itemize/draft rephrase -> normalized DST structures -> approved composition -> publication build`

This will prove:

- stable section ordering
- stable numbering
- stable citation resolution
- stable content assembly

before adding richer formats.

## Validation Rules To Implement First

The first implementation slice should enforce:

- every `PublicationSection` id is unique
- section tree has no cycles
- every referenced claim exists
- every referenced source exists
- every referenced entity exists
- every `recommendation` section depends on at least one `analysis` or `evidence` section
- every descriptive claim has at least one source
- every xref target exists
- every transcluded block exists and is version-bound
- every build stores input snapshot hashes

These rules are the first guardrail for determinism and governance.

Additional near-term rules to add next:

- canonical section ids stay stable even when rendered ordinals change
- every xref origin and target kind is valid for its `xref_type`
- every transcluded block resolves to one version-bound block record
- every recommendation claim is reachable from supporting analysis/evidence through the section/xref graph

## Integration With Existing Claim And Evidence Machinery

The repo already has runtime `Evidence` and `Claim` machinery in:

- [system_state.py](system_state.py)
- [pure_theory_types.py](pure_theory_types.py)

Publication should not directly reuse those runtime objects as-is.

Reason:

- runtime claims are tied to reduction episodes
- publication claims are curated shipping-layer statements

But publication should still align with the same evidence/claim stratification.

Recommended rule:

- publication claims may be derived from admitted learning units and source records
- publication claims must preserve source and review provenance
- publication claims should not be created from free-form prose alone

## Integration With Markdown And Typst

The first publication implementation should not depend on markdown ingress.

Instead:

- source markdown informs `LearningContext`
- `LearningContext` informs `Publication`
- `Publication` renders Typst and markdown outputs

That preserves the architecture:

`source -> context -> publication -> render artifacts`

not:

`source markdown -> final report directly`

## Integration With Workstation

The workstation layer should not be the first home of publication semantics.

First implement the semantic substrate and build pipeline.

Then add bounded workstation actions such as:

- `ws.publication.create`
- `ws.publication.open`
- `ws.publication.validate`
- `ws.publication.build`
- `ws.publication.list`

Later:

- `ws.publication.review`
- `ws.publication.render`
- `ws.publication.diff`

These should operate on publication objects, not on free-form document writes.

## Initial Workflow Recommendation

The first user-facing lifecycle should be:

1. select subject / learning context
2. compare maintained projections in `Review`
3. draft publication composition of type `report`
4. preview and approve the composition
5. lock publication inputs
6. build publication
7. inspect outputs
8. mark release-ready

This is a bounded first release path.

## Test Scenarios

The implementation should be validated with explicit reproducibility and structural tests.

### Structural Tests

- create a simple publication with one subject, two sections, three claims, and two sources
- verify all ids remain stable after reload
- verify section tree cycles are rejected
- verify duplicate claim ids are rejected

### Validation Tests

- recommendation section without supporting analysis should fail validation
- claim without source should fail validation
- broken xref should fail validation
- transclusion of unknown block should fail validation

### Reproducibility Tests

- same publication snapshot plus same renderer version yields identical Typst output hash
- same publication snapshot plus same renderer version yields identical markdown output hash
- changing section order input changes output hash deterministically
- changing only renderer version records a new build even if content is unchanged

### Provenance Tests

- publication build records learning context snapshot hash
- claim records preserve source linkage
- source update can identify impacted claims

### Release Tests

- publication marked `approved` can be built to final outputs
- publication in `draft` may build preview outputs but not final release outputs

### Non-Collision Tests

- existing validation `report.json` outputs are not treated as publications
- existing workstation trial reports are not loaded by publication store

## Suggested Phase Plan

### Phase 1

Add object models and on-disk serialization for:

- `Publication`
- `PublicationSection`
- `PublicationClaim`
- `PublicationSource`
- `PublicationEntity`
- `PublicationCrossReference`
- `PublicationBuild`
- `RenderArtifact`

### Phase 2

Add publication validation and deterministic assembly.

### Phase 3

Add Typst and markdown render projections.

### Phase 4

Add workstation publication actions and review surfaces.

### Phase 5

Add richer features:

- reusable publication blocks
- PDFs and HTML
- publication diffs
- publication-to-publication reuse
- release profiles

## What Not To Do

- do not implement publication first as a giant markdown template
- do not bind publication truth to UI widget state
- do not let LLM prose generation bypass structured claims and sources
- do not overload current runtime reports as publications
- do not skip snapshot hashing and still call the build reproducible

## Recommended Immediate Next Step

The next concrete implementation move should be:

1. widen composition-aware section structure beyond the current fixed nested decision scaffold while preserving canonical section ids separately from rendered ordinals, and make the richer path cards page-aware so denser reserve / blocked alternatives do not degrade on paper
2. strengthen section-role and xref/transclusion validation over the current typed substrate; `PublicationEntity`, `PublicationReviewRecord`, publication-internal xrefs, and diff/query helpers already exist
3. add typed cross-reference management between learning units and their derived projections, not only publication-internal section/claim links
4. defer broader fact modeling and HTML rendering until the structure above is real; PDF builds and workstation publication actions already exist

That keeps publication moving without collapsing it back into templated markdown or diagnostic report reuse.
