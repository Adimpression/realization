# Itemize

Formal design for the typed normalization layer that should sit between
research intake and later draft composition.

This stage is not lightweight tagging.

It is the phase where incoming subject material is turned into explicit,
reusable, typed items that later composition and decision work can rely on.

## Objective

`Itemize` should answer one question:

- what discrete things are in this subject material?

Those things may later be used for:

- publication composition
- glossary building
- keyword and concept indexing
- decision modeling
- cross-reference construction
- figure and table generation

So the layer should behave like a governed lexicon-plus-ontology step,
not like ad hoc labeling.

## Position In The Workflow

The intended subject workflow should become:

1. `Gather`
- ingest and admit material into `LearningContext`

2. `Itemize`
- identify, normalize, and type the discrete items inside admitted material

3. `Draft`
- compose those items into report structure, draft sections, decision aids,
  and transformed renderable blocks

4. `Review`
- validate, compare, and approve the resulting draft

5. `Publication`
- build, inspect, and release

That means `Itemize` is upstream of composition.

It should reduce ambiguity before the user starts drafting.

## Problem

If `Draft` has to discover entities, glossary terms, equations, definitions,
decision-role candidates, and figure/table candidates at the same time that it
is trying to compose a report, the workflow becomes muddy.

If `Itemize` is implemented only as generic tags, it becomes noisy and too weak.

The right middle ground is:

- a real typed extraction and normalization layer
- narrow enough to be governed
- broad enough to support many report domains

## Core Decision

Introduce a first-class `ItemizedSubjectItem` layer.

The correct relationship should be:

`Source / LearningDelta -> Learning unit -> ItemizedSubjectItem -> ReviewItem -> DecisionReviewItem -> PublicationBlock`

This preserves separation of concerns:

- `LearningContext` owns admitted source-derived truth
- `Itemize` owns discrete typed normalization
- `Draft` / composable review owns structure and orientation
- `DecisionReview` owns explicit decision modeling
- `Publication` owns final rendered output

## What Itemize Should Own

`Itemize` should own:

- identification
- normalization
- naming
- typing
- aliasing
- linking to source provenance

It should not own:

- final report prose
- section composition
- recommendation ranking
- publication rendering
- final approval

## Rephrase Boundary

`Itemize` is allowed to improve wording, but only at the normalized-item layer.

That means:

- source cleanup may remove internal jargon and formatting noise
- source cleanup must not tune source material into publication prose
- `Itemize` may rephrase extracted items:
  - with LLM assistance
  - with manual editing
- those rephrases should preserve facts while making the normalized item clearer, more reusable, and easier for `Draft` to compose

## Initial Catalog Of Itemized Things

The first serious target set should include:

### Lexical / glossary items

- glossary term
- acronym
- domain keyword
- synonym / alias
- canonical concept name

Why:

- industry reports often need a stable vocabulary before they can be composed cleanly

### Entity-like items

- organization
- team
- regulator
- vendor
- product
- system
- process
- dataset
- jurisdiction

Why:

- later cross-reference, comparison, and decision layers depend on stable named entities

### Claim / fact items

- factual claim
- normative claim
- interpretive claim
- assumption
- caveat
- metric fact
- threshold

Why:

- reports and decision aids need explicit claims rather than only paragraph prose

### Quantitative items

- equation
- variable
- unit of measure
- conversion rule
- metric definition
- worked-example candidate

Why:

- quantitative material usually needs special downstream handling

### Structured-content items

- table candidate
- decision-rule candidate
- checklist candidate
- timeline candidate
- comparison-set candidate

Why:

- these are often latent inside prose and should be surfaced before drafting

### Visual candidates

- figure candidate
- screenshot asset
- diagram candidate
- simple flow candidate
- dependency diagram candidate

Why:

- later diagram or figure generation needs explicit source items rather than prose guessing

### Decision-role candidates

- actor candidate
- objective candidate
- capability candidate
- dependency candidate
- constraint candidate
- boundary candidate
- current-state candidate
- target-state candidate
- transition candidate
- decision candidate

Why:

- some of these will later map into
  [coordinated_transformation/core.py](coordinated_transformation/core.py)

### Reference items

- citation anchor
- source excerpt
- xref candidate
- provenance note

Why:

- publication and decision review need explicit, stable evidence references

## Item Shape

Each itemized object should carry at least:

- `itemized_item_id`
- `subject_id`
- `source_unit_id`
- `item_kind`
- `canonical_label`
- `aliases`
- `summary`
- `source_refs`
- `confidence`
- `status`
- `linked_item_ids`
- `created_at_epoch_ms`
- `updated_at_epoch_ms`

Useful additional fields:

- `glossary_definition`
- `keyword_weight`
- `equation_text`
- `variable_refs`
- `entity_type`
- `decision_role_candidate`
- `figure_asset_refs`
- `table_shape_hint`

## Itemize Is Broader Than Coordinated Transformation

The coordinated transformation theory is an important downstream consumer of itemized material.

But it is not the only one.

`Itemize` should be broader than decision modeling.

It should support:

- publication lexicon
- glossary generation
- entity normalization
- source/citation handling
- quantitative extraction
- decision-role candidate discovery
- cross-reference preparation

That is why this stage should not be described as “the coordinated-transformation tagging stage”.

It is a general typed normalization layer.

## Relationship To Draft

`Draft` should assume that the material it is composing is already itemized.

That means `Draft` should be able to consume:

- glossary-ready items
- claim items
- equation items
- table candidates
- figure candidates
- decision-role candidates

and then decide:

- what to include
- how to orient it
- how to render it
- what children to compose

Without `Itemize`, `Draft` has to do discovery and composition at once.

That is avoidable complexity.

## Relationship To Review

`Review` should not be burdened with first-pass identification work.

It should validate and approve a draft that already has:

- normalized items
- composition decisions
- decision-analysis receipts where relevant

That is why `Itemize` should be a separate stage rather than another mode inside `Review`.

## Workstation Shape

The current first cut of the `Itemize` tab now supports:

- generating itemization for the active subject snapshot
- refreshing itemization while preserving manual item edits
- browsing normalized items
- selecting one current item at a time
- promoting, rejecting, and restoring items
- cycling decision-role candidates
- holding, merging, and splitting deterministic candidates

The next cuts should add:

- filtering by item kind
- promoting or demoting candidate kinds
- alias editing
- glossary-definition editing
- linking related items
- converting source-unit fragments into itemized objects
- reviewing low-confidence extracted candidates

The tab should feel like:

- a lexicon / ontology workbench

not:

- a full drafting surface
- a free writing editor

## Quality Gates

The layer should aim to guarantee:

- stable canonical labels
- no duplicate canonical items without explicit aliasing
- provenance retained back to source units
- item kinds are explicit
- decision-role candidates remain separate from final decisions

## Practical Conclusion

`Itemize` is worth adding if it is implemented as:

- typed extraction
- normalization
- aliasing
- lexicon and concept shaping
- decision-role candidate preparation

It is not worth adding if it is only:

- free-form tags
- cosmetic labels
- another vague metadata surface

The correct role is:

- make the subject material discrete and typed before drafting begins
