# Publication

Formal design for governed, deterministic, reproducible publication output built from [LEARNING_CONTEXT.md](LEARNING_CONTEXT.md).

This file introduces a new concept:

`Publication`

with the first supported publication type:

`Report`

## Problem

The repository already uses the word `report` in several places, but mostly in the sense of:

- validation reports
- CLI run reports
- audit summaries
- trace and test output

Those are useful, but they are not the same thing as a governed knowledge publication.

A published report in this system should not be:

- an ad hoc markdown file
- a transcript dump
- a validation JSON blob
- a free-form rendered note

It should be:

- a structured projection from `LearningContext`
- assembled from typed knowledge units
- built under deterministic rules
- linked to provenance and review state
- reproducible from explicit inputs

That is why the correct new concept is not simply `report`.

It is:

`Publication`

with:

`publication_type = report`

as the first publication kind.

## Core Decision

`Publication` should be a first-class governed projection object above `LearningContext`.

The architecture should be:

`LearningContext -> PublicationSpec -> PublicationBuild -> RenderArtifact`

This means:

- `LearningContext` remains the durable semantic truth for the subject
- `Publication` defines a governed shipping view over a chosen portion of that context
- `PublicationBuild` captures one deterministic build instance
- `RenderArtifact` captures the final emitted files such as PDF, HTML, Typst source, or markdown export

## Publication Is Optional

`LearningContext` should not exist only to feed publication.

The correct relationship is:

- some subject contexts will remain internal governed memory only
- some subject contexts will project into skills, subject documents, or workstation views only
- some subject contexts will additionally produce one or more governed publications

Therefore:

- not every `LearningContext` should become a `Publication`
- publication should be an explicit governed release act, not the default endpoint of learning
- publication needs stronger structure than general subject memory because it carries shipping, review, citation, and audit obligations

## Publication Is Not Truth

`Publication` must not become a second competing source of subject truth.

The truth split should be:

- `LearningContext` = subject memory
- `Publication` = governed presentation and release object
- `RenderArtifact` = emitted output artifact

Therefore:

- claims do not become true because they are printed
- documents do not become authoritative because they were rendered
- publication is a projection and release act over already governed learning

## Publication Type

The first supported publication type should be:

- `report`

Later publication types may exist, for example:

- `brief`
- `memo`
- `guide`
- `specification`
- `policy`
- `appendix_bundle`

But the initial implementation should stay narrow:

- `Publication`
- `publication_type = report`

## Why `Publication` Instead Of Only `Document`

`Document` is too weak for this need.

The system needs more than writing.

It needs:

- stable references
- cross-linked claims
- source-backed evidence
- governed section roles
- review status
- deterministic builds
- reproducibility
- release metadata

That is not merely document authoring.

It is governed publishing.

## Publication Structure

Each publication should be a structured tree, not a prose blob.

Minimum node kinds:

- `document`
- `chapter`
- `section`
- `subsection`
- `paragraph`
- `figure`
- `table`
- `appendix`

Every node should have a stable id.

That id should be stable independently of rendered numbering.

In practice:

- canonical ids identify the publication nodes
- ordinals and numbering are render projections
- reordering sections may change displayed numbering without changing canonical section identity

Examples:

- `pub:ai-readiness-singapore-schools-2026`
- `sec-03-governance`
- `sec-03-02-risk-model`
- `tbl-approval-classes`
- `clm-03-02-004`

Stable ids are required for:

- deterministic references
- reproducible numbering
- stable diffs
- section reuse
- claim reuse
- review tracking

## Publication Inputs

A `Publication` should be built from typed inputs, not only free text.

Minimum input classes:

- section tree
- blocks
- claims
- entities
- facts
- sources
- cross-references
- review and approval records
- render settings

The prose in the final report should be a renderable projection of these typed inputs.

Facts are valuable here, but they do not need to be the first implementation cut if sections, claims, sources, entities, xrefs, and deterministic rendering are not yet complete.

The immediate priority order should be:

1. stable section tree with semantic roles
2. claim objects as the primary publication truth layer
3. source objects and governed citation handling
4. typed cross-references
5. reusable blocks and transclusion
6. entity objects
7. review and approval records
8. deterministic build and validation rules

## Claim-Centered Design

A report is fundamentally a structured bundle of claims.

Claims should be first-class objects.

Each publication claim should carry:

- stable id
- statement
- claim kind
- stance or role
- scope
- status
- evidence/source links
- confidence or certainty class
- validity interval where relevant
- review metadata

Recommended content typing:

- `descriptive`
- `interpretive`
- `normative`
- `procedural`

This separation matters because recommendation text and observed fact should not collapse into one undifferentiated paragraph layer.

## Entities, Facts, And Sources

Publications should not embed everything only as prose.

They should also depend on typed substrate objects:

- `Entity`
- `Fact`
- `Source`

This makes updates and citations controllable.

Examples:

- the same entity can appear across many publications without duplication
- a changed source can identify impacted claims
- a fact can be reused in multiple sections or reports

## Typed Cross-References

Cross-references should be first-class typed links, not fragile “see above” text.

Recommended types:

- `supports`
- `contradicts`
- `defines`
- `extends`
- `depends_on`
- `supersedes`
- `example_of`
- `derived_from`
- `see_also`

The current first implementation cut already persists deterministic section-level typed xrefs for report publications under `xrefs/` and validates xref integrity.

Later cuts should widen this from report-section links into richer claim, entity, and block relationships plus author-managed reference intent.

This turns the publication into a navigable graph over a section tree, not merely a formatted page.

## Semantic Section Roles

Each section should carry a semantic role.

Recommended initial roles:

- `summary`
- `background`
- `definition`
- `evidence`
- `analysis`
- `comparison`
- `recommendation`
- `implementation`
- `appendix`

This enables both validation and rendering discipline.

Examples:

- a `recommendation` section should depend on supporting analysis or evidence
- an `evidence` section should not silently contain unsupported prescriptions

## Reusable Blocks And Transclusion

The system should prefer transclusion over copy-paste.

The current first implementation cut already persists typed publication blocks under `blocks/` and supports deterministic transclusion in rendered report output.

Reusable publication blocks may include:

- definitions
- methodology notes
- policy boilerplate
- recurring figures
- recurring claim clusters
- standard caveats

These blocks should be versioned and explicitly included.

The current report slice uses a narrow deterministic form:

- stable section lead blocks
- a shared governed-publication basis block
- a shared report-scope block
- explicit include references from section blocks to shared blocks

This is necessary for corpus-scale consistency.

## Publication Object Model

Minimum first-class construct set:

- `Publication`
- `PublicationSection`
- `PublicationBlock`
- `PublicationClaim`
- `PublicationFact`
- `PublicationEntity`
- `PublicationSource`
- `PublicationCrossReference`
- `PublicationReviewRecord`
- `PublicationBuild`
- `RenderArtifact`

This is intentionally claim-centered and release-oriented.

## Relationship To Learning Context

A `Publication` should originate from one or more `LearningContext` snapshots.

That origin should be explicit.

Publication inputs should record:

- source learning context ids
- learning context snapshot hashes or versions
- included unit ids
- excluded unit ids where intentionally filtered
- publication scope

This ensures that the publication can be reproduced later from the same semantic state.

## Reproducibility Rule

The key publication property is reproducibility.

For this system, reproducibility should mean:

the same:

- `LearningContext` snapshot
- `PublicationSpec`
- included units
- transcluded block versions
- citation resolution inputs
- renderer version
- template/theme version
- asset set

must yield the same publication output.

This is the publication analogue of deterministic build behavior.

## Deterministic Build Rule

Publication output should be treated as a build artifact.

The build pipeline should be:

```text
LearningContext Snapshot
  -> publication validation
  -> reference resolution
  -> block transclusion
  -> section assembly
  -> numbering
  -> citation assembly
  -> render
  -> final output artifacts
```

The build must preserve:

- stable section ordering
- stable numbering
- stable citation ordering
- stable xref resolution
- stable content hashing

## Versioning Rule

Versioning should exist at multiple levels.

Minimum levels:

- publication spec version
- section version
- claim version
- source version
- block version
- build version
- schema version

This allows the system to distinguish:

- semantic changes
- source changes
- layout-only changes
- renderer-only changes

## Review And Approval Rule

Each publication unit should participate in explicit status workflow.

Recommended states:

- `draft`
- `under_review`
- `approved`
- `deprecated`
- `superseded`
- `archived`

At minimum this should apply to:

- publication
- section
- claim
- source inclusion decision
- reusable block

This preserves governance.

## Validation Rule

Publication build must validate before release.

Minimum validation rules:

- every normative claim must depend on analysis or evidence
- every factual claim must have at least one source
- every source must carry freshness metadata
- no broken references
- no undefined entities
- no orphan sections
- no duplicate ids
- all transcluded blocks must be version-bound
- publication scope must match referenced units

This is where structural determinism becomes operational.

## Queryability Rule

Publication substrate should remain queryable.

The system should be able to answer:

- which claims depend on source X
- which publications reuse block Y
- which recommendations are based on outdated evidence
- which sections mention entity Z
- which claims remain unreviewed
- what changed between publication version A and B

This means publication data cannot live only as opaque rendered files.

## Render Artifacts

`RenderArtifact` should capture the emitted publication outputs.

Examples:

- Typst source
- PDF
- HTML
- markdown export
- citation index
- appendix package

Each render artifact should carry:

- artifact id
- publication build id
- output format
- content hash
- output path
- created_at
- renderer identity and version

## Existing Repo Collision Rule

The repo already uses `report` heavily for run diagnostics and validation output.

Therefore:

- those existing runtime reports should remain what they are
- they should not be silently upgraded into `Publication`
- `Publication` should be a separate concept with separate storage and schema

If needed, existing diagnostic reports can later become one source input to a publication, but they are not publications by default.

## Storage Layout

Recommended storage inside a subject corpus home:

```text
corpus/
  <subject-id>/
    publications/
      <publication-id>/
        publication.json
        sections/
          <section-id>.json
        blocks/
          <block-id>.json
        builds/
          <build-id>.json
        outputs/
          <build-id>/
            report.typ
            report.pdf
            report.html
            report.md
```

This keeps publication state near the originating subject context while still separating:

- semantic source state
- publication specification
- concrete build instances
- rendered artifacts

## Publication And Blend Theory

In Blend terms:

- `LearningContext` is primarily DNA plus RNA for subject learning state
- `Publication` is a higher-order structured projection contract
- `PublicationBuild` is an operator result under explicit context and policy
- UI is only a projection over those objects

This means publication should not begin as a UI feature.

It should begin as a governed semantic object model plus deterministic build pipeline.

## Near-Term Recommendation

Do not start with the entire ontology at once.

Start with these eight elements:

1. `Publication`
2. `PublicationSection` with stable ids and roles
3. `PublicationClaim`
4. `PublicationSource`
5. `PublicationEntity`
6. `PublicationCrossReference`
7. `PublicationReviewRecord`
8. `PublicationBuild`

This is enough to get:

- deterministic section assembly
- typed claims
- citation integrity
- reproducible output
- reviewable publication release

## What Not To Do

- do not treat a markdown file as the publication truth model
- do not overload existing validation `report.json` outputs as publications
- do not make rendered prose the only source of claims
- do not allow free-form edits to bypass section/claim/source identity
- do not treat publication generation as an LLM-only act
- do not make publication builds non-reproducible by hidden context or ambient prompt state

## Summary

The correct new concept is:

- `Publication`

with the first publication type:

- `report`

originating from:

- `LearningContext`

and realized through:

- a claim-centered, section-structured, source-backed, deterministic publishing pipeline

That is the right way to ship governed reports from the corpus without collapsing publication, learning, and runtime reporting into one object.


---

# Current truth:

- durable `PublicationComposition` records now exist between maintained subject truth and `PublicationBuild`
- `Draft` now owns first-pass composition shaping over that persisted composition layer
- `Review` now remains the approval/sign-off gate over maintained projections and the current draft/report plan
- [`Publication`](publication_projection.py) now builds from approved composition state rather than blindly from all admitted units
- approved subject imports are already disclosed and selectable as publication dependencies/usage inside the governed composition flow

So the remaining problem is no longer “introduce publication composition at all”.

The remaining problem is to deepen that composition layer.

**Current direction**
Keep `PublicationComposition` as the durable layer that sits between maintained subject truth and `Publication`.

It should contain:
- publication mandate: title, audience, purpose, tone, publication type
- snapshot binding: active subject version, approved import ids, reasoning-scope policy
- composition scope: included/excluded unit ids, selected claims, selected blocks, selected sections
- section plan: ordered section tree with roles and titles
- import usage plan: how each approved import is allowed to appear
- synthesis plan: publication-level claims created in review, with provenance
- approval state: draft, under review, approved, superseded

That is now the thing `Draft` shapes and `Review` approves. `Publication` then only locks, builds, validates, and releases that approved composition.

**How Draft And Review Should Work**

`Draft` should remain the composition workbench with explicit controls:

1. `Mandate`
- define report title, audience, publication type, and scope summary

2. `Scope`
- choose which native subject units/claims are in or out
- choose which sections actually appear
- mark what is “headline”, “supporting”, or “appendix”

3. `Imports`
- inspect approved `SubjectImport`s
- for each import, choose one allowed usage mode:
    - `dependency_only`
    - `background_only`
    - `comparison`
    - `transcluded_support`
- no import should silently appear everywhere

4. `Synthesis`
- allow review-stage synthesis only as explicit publication claims
- every synthesized claim must retain provenance:
    - native support
    - borrowed support
    - reasoning trace

5. `Approval`
- `Review` compares maintained `subject.md` / `subject.typ`
- compare maintained `subject.md` / `subject.typ`
- compare publication composition diff against previous approved composition
- approve the composition snapshot
- only then unlock `Publication`

That gives the operator real control.

**Relation To Subject Imports And Bounded Reasoning**
This should be strict:

- `SubjectImport` defines what foreign material is allowed into scope.
- `SubjectReasoningScope` defines what the controller may reason over.
- `PublicationComposition` defines what of that scoped material is actually allowed into the report.

Those are three different layers.

Rules:
- native subject material is still primary
- imported material is still borrowed
- global retrieval should never enter publication directly
- borrowed material must never be laundered into native truth automatically
- if borrowed reasoning becomes native subject truth, it must first enter through a governed delta in [`learning_context.py`](learning_context.py)

So in publication:
- `dependency_only` import: disclosed in dependency/source register, not used as body truth
- `comparison` import: appears only in explicitly comparative sections
- `transcluded_support` import: may support claims, but remains marked borrowed
- `background_only` import: visible to the controller during review composition, but not emitted as direct report claims unless separately promoted

**Concrete Repo Shape**
Implement it as follows:

1. Add `PublicationComposition` persistence under:
- `corpus/<subject>/publications/<publication-id>/compositions/<composition-id>.json`

2. Extend [`workstation/subject_workflow.py`](workstation/subject_workflow.py) by continuing to deepen the existing `Draft`/`Review` actions around:
- mandate
- scope
- import usage
- composition preview
- composition diff
- approval history

3. Change [`publication_projection.py`](publication_projection.py) so report builds consume `PublicationComposition`, not “all admitted units”

4. Extend validation so publication fails if:
- composition references unapproved imports
- import version pins drift
- borrowed claims are emitted without provenance
- section-role rules are violated

**Bottom Line**
`Gather` should create or admit subject truth.
`Itemize` should normalize that subject truth.
`Draft` should compose publication truth.
`Review` should approve publication truth.
`Publication` should build and release approved composition truth.

That also means source prose is not where publication wording should be tuned.

- source cleanup may remove internal jargon and formatting noise
- publication-quality wording should come later through explicit rephrase operations in `Itemize` and `Draft`

That is the clean separation.

The next implementation slice is:

- deepen section-tree structure
- deepen direct composition editing
- deepen import-aware composition control
- widen publication validation and history/diff over the existing composition layer
