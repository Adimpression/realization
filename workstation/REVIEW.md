# Review

Formal design for the composable `Review` layer that sits between
[LEARNING_CONTEXT.md](LEARNING_CONTEXT.md)
and
[PUBLICATION.md](PUBLICATION.md).

This design assumes a future explicit
[ITEMIZE.md](ITEMIZE.md)
layer upstream, so composition does not need to do first-pass normalization at
the same time.

For the decision-specific layer that should eventually power
recommendation sections, decision aids, and simple governed diagrams, see
[../DECISION_REVIEW.md](../DECISION_REVIEW.md).

Concrete implementation planning for this composable review layer lives in
[REVIEW_IMPLEMENTATION.md](REVIEW_IMPLEMENTATION.md).

## Problem

The current review surface is still too toggle-shaped.

It can decide:

- include or exclude an item
- approve or block a report plan
- preview maintained projections

That is necessary, but not sufficient.

Industry reports rarely consist of only flat atomic claims.

What arrives in review may be:

- an equation
- a philosophical or normative statement
- a YAML-like table
- a paragraph containing multiple embedded claims
- a decision rule that should become a table
- a process that should become a diagram
- a figure or screenshot that needs captioning and provenance

If review can only toggle these items, then publication becomes either:

- too literal
- too lossy
- too manual outside the governed workflow

So `Review` needs a more composable object model.

## Core Decision

`Review` should not operate only on `included` / `excluded` scope entries.

It should operate on a recursive `ReviewItem` layer.

Each `ReviewItem` should let the workstation decide:

- what kind of thing this is
- how it should be rendered
- how provenance should appear
- whether it should be split, merged, rewritten, diagrammed, or tabulated
- whether it should remain atomic or become a parent of smaller review items

The correct relationship is:

`Learning unit -> Review item -> Render block`

That keeps semantic truth in `LearningContext`, keeps normalization in
`Itemize`, keeps composition decisions in `Review` / later `Draft`, and keeps
final emitted structure in `Publication`.

## Primary Focus

The near-term focus of `Review` is not unlimited visual design.

It is:

- make simple diagrams possible
- make simple illustrations possible
- help the user turn complex prose into clearer decision-oriented structures

This means the first goal is not:

- arbitrary drawing
- complex infographic design
- free-form illustration tooling

It is:

- decision tables
- simple flow diagrams
- simple dependency diagrams
- simple timelines
- compact explanatory figures
- captioned screenshots or preserved illustrations

The important distinction is:

- `Review` should help the user decide how to present meaning
- not merely toggle whether the meaning is present

So the composable review layer must not only support composition.

It must also support decision wiring.

## Decision Wiring

For each review item, the system should help answer:

- should this stay prose?
- should this become a table?
- should this become a diagram?
- should this become an equation block with legend?
- should this become a figure with caption?
- should this be split before any of those decisions are made?

That means `Review` needs guided decision paths, not only free editing.

Useful guided decisions include:

- prose -> table
- prose -> diagram
- equation -> equation block + legend
- paragraph -> split into claims
- decision rule -> decision table
- process description -> flow diagram
- causal chain -> dependency diagram
- screenshot or preserved asset -> figure with caption

The workstation should therefore help the user choose an orientation, then materialize that orientation into review children or renderable blocks.

## Why Toggles Are Not Enough

Toggles answer only one question:

- should this item be included?

But review also needs to answer:

- is this one claim or many?
- is this prose, equation, table, diagram, checklist, or appendix matter?
- should this remain literal or be rewritten?
- should provenance appear inline, in a citation box, or as source basis?
- should this item become a figure, table, or decision aid?
- should this item be decomposed before publication?

Without those answers, review cannot be a real publication-composition layer.

## Review Item Shape

Each review item should carry at least:

- `review_item_id`
- `source_unit_id`
- `semantic_kind`
- `render_kind`
- `evidence_mode`
- `transform_mode`
- `included`
- `children`
- `ordering`
- `notes`

Useful additional state:

- `llm_rewrite_status`
- `manual_override`
- `figure_asset_refs`
- `table_schema`
- `diagram_kind`
- `decision_basis_refs`
- `review_state`

## Review Axes

Every item should be orientable along five axes.

### 1. Semantic Kind

What this thing is.

Examples:

- equation
- claim
- multi-claim paragraph
- table
- process
- policy rule
- screenshot

### 2. Render Kind

How this thing should appear in the publication.

Examples:

- equation block
- claim panel
- citation callout
- typst table
- decision table
- flow diagram
- metric card
- figure with caption

### 3. Evidence Mode

How provenance should be shown.

Examples:

- inline source handles
- source basis panel
- citation box
- footnote-style source list
- appendix-only provenance

### 4. Transform Mode

What review is allowed to do to the item before publication.

Examples:

- keep as-is
- rewrite manually
- rewrite with LLM proposal
- split into children
- merge with sibling
- convert to table
- convert to diagram
- convert to equation + legend

### 5. Composition Structure

Whether the item is atomic or composed.

Examples:

- leaf item
- parent item with child claims
- parent item with equation + variable legend + worked example
- parent item with decision table + explanatory note

## Initial Catalog Of Reviewable Item Kinds

This catalog should be treated as the first serious target for review composition over real industry reports.

### 1. Equation Or Formula

Why:

- equations should rarely remain plain inline prose
- they often need a dedicated box, readable math layout, and later a variable legend or worked example
- financial, engineering, chemistry, and operations reports all use these

Default direction:

- render as `equation_block`

### 2. Variable Legend

Why:

- formulas become opaque if symbols are not explained
- review should let one equation expand into an equation plus variable definitions

Default direction:

- child item under an equation

### 3. Descriptive Factual Claim

Why:

- this is the basic reportable claim type
- it should preserve source traceability and remain cleanly renderable

Default direction:

- render as `claim_panel` or bullet finding

### 4. Philosophical Or Normative Statement

Why:

- these are easy to overstate
- they need stronger provenance and visible grounding than ordinary prose
- policy, governance, and thought-leadership reports contain many of these

Default direction:

- render as `claim_callout` with explicit source basis or citation box

### 5. Multi-Claim Paragraph

Why:

- one paragraph often contains several claims, assumptions, and transitions
- publishing it unchanged makes later structure, citation, and validation weak

Default direction:

- split into child items, then optionally rewrite into cleaner prose

### 6. YAML Or Structured Table

Why:

- structured records should not be flattened back into prose
- tabular material is often already close to the right publication form

Default direction:

- detect and render as `typst_table`

### 7. Decision Table

Why:

- many business, policy, operations, and compliance items are really decision logic
- decision tables are easier to audit than prose rules

Default direction:

- render as `decision_table`

### 8. Comparison Matrix

Why:

- many reports compare vendors, options, jurisdictions, scenarios, or methods
- prose comparisons are hard to scan and easy to misread

Default direction:

- render as `comparison_table` or matrix

### 9. Process Or Procedure

Why:

- procedural text often wants a stepwise structure or flow shape
- many operational and implementation sections are clearer as staged flows

Default direction:

- render as ordered steps or `flow_diagram`

### 10. Causal Or Dependency Chain

Why:

- causal prose is often buried inside long paragraphs
- review should be able to expose dependencies or mechanisms explicitly

Default direction:

- render as dependency map, ordered bullets, or diagram

### 11. Timeline Or Chronology

Why:

- dates, phases, rollout stages, and incident sequences are better understood temporally
- this is common in public policy, strategy, regulation, and operations reports

Default direction:

- render as `timeline_block` or date table

### 12. Metric Snapshot Or KPI Cluster

Why:

- metrics often want compact visual framing rather than prose repetition
- a small grid or metric-card layout is usually better

Default direction:

- render as `metric_grid`

### 13. Threshold, Banding Rule, Or Classification Scheme

Why:

- many reviews involve tiering, risk bands, approval classes, or maturity levels
- prose hides threshold logic and makes it harder to validate

Default direction:

- render as `banding_table` or decision rule block

### 14. Risk / Control Pair

Why:

- risk material is usually incomplete unless the control or mitigation is shown beside it
- governance and audit readers expect these pairings directly

Default direction:

- render as paired table or structured bullet block

### 15. Quote Or Cited Passage

Why:

- direct quotes need special handling so they do not blend into authored claims
- they often require tighter provenance and bounded usage

Default direction:

- render as quotation block with source basis

### 16. Figure, Screenshot, Or Preserved Illustration

Why:

- URL learning already preserves screenshots and assets
- review should be able to decide whether an image becomes a report figure, appendix artifact, or evidence-only support

Default direction:

- render as `figure_with_caption`

### 17. Taxonomy, Glossary, Or Definition Cluster

Why:

- definitions often form reusable grouped anchors
- they are easier to navigate as grouped structures than scattered prose

Default direction:

- render as `definition_group` or glossary table

### 18. Scenario Set

Why:

- reports often compare best/base/worst case or multi-scenario planning outcomes
- these want explicit scenario structure and easier comparison

Default direction:

- render as scenario table or grouped subsections

### 19. Checklist Or Requirement Set

Why:

- requirements, audit checks, and conformance items should remain explicit and testable
- free prose weakens validation

Default direction:

- render as checklist or requirements table

### 20. Worked Example

Why:

- examples often clarify formulas, procedures, and decisions better than abstract explanation alone
- they should be attachable to the item they explain

Default direction:

- child item beneath equation, rule, or process

## Example Orientations

These should be normal review operations, not unusual exceptions.

### Equation

`Report Scope Item -> is an equation -> pick an equation box`

Why:

- equations need readable math framing and should not compete with ordinary narrative layout

### Philosophical Statement

`Report Scope Item -> is a philosophical statement -> use citation box`

Why:

- normative or reflective claims need stronger visible grounding than ordinary descriptive prose

### YAML Table

`Report Scope Item -> is a YAML table -> pick a Typst table`

Why:

- structured rows and columns should stay structured; this should often be auto-detected by default

### Multi-Claim Paragraph

`Report Scope Item -> is a paragraph of logically related items -> rewrite manually or using an LLM`

Why:

- the paragraph may contain multiple claims that need clearer decomposition before publication

### Decision-Rich Item

`Report Scope Item -> create a decision table or diagram`

Why:

- decision logic is usually clearer, more auditable, and more reusable in tabular or diagrammatic form

### Simple Diagram Or Illustration Candidate

`Report Scope Item -> create a simple diagram or illustration`

Why:

- many important publication improvements come from one simple explanatory shape rather than more prose
- the target is not complex art; it is clearer structure
- industry reports often need lightweight visuals such as flow shapes, dependency shapes, timeline bands, or captioned screenshots

## Review Actions The UI Should Support

Each review item should eventually support actions like:

- include
- exclude
- split into children
- merge with sibling
- rewrite manually
- rewrite with LLM proposal
- convert to table
- convert to diagram
- convert to simple illustration
- convert to equation block
- add citation box
- add source-basis panel
- add variable legend
- add worked example
- mark appendix-only
- mark background-only
- mark headline finding
- mark non-reportable

## First Serious Implementation Cut

The first practical composable review layer should support at least:

- equation
- descriptive claim
- philosophical or normative statement
- multi-claim paragraph
- YAML / structured table
- decision table
- process flow
- simple diagram / illustration candidate
- definition cluster
- metric snapshot
- comparison matrix
- timeline
- figure / screenshot with caption

That is enough to handle a large fraction of real industry-report material without collapsing back into raw toggles.

## One-Sentence Summary

`Review` should become a governed composition layer over typed, orientable, transformable review items rather than a flat include/exclude toggle surface.
