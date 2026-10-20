# Learning Context

Formal design for closing the loop between:

- external learning documents
- governed learned residue
- exported/runtime skills
- maintained human-readable subject documents

The purpose of this design is to make:

`markdown -> skills -> markdown`

become:

`source docs -> learning context -> derived skills + maintained corpus docs -> further updates into the same learning context`

rather than a set of disconnected import/export actions.

## Problem

The repository already has two strong but separate capabilities.

First:

- governed external-source learning through [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
- formal IR precedence through [markdown_ir.py](markdown_ir.py) and [markdown_learning_artifact_semantics.py](markdown_learning_artifact_semantics.py)

Second:

- governed skill import/export and runtime invocation through the skill stack
- workstation-level markdown open/create/append actions through [workstation/capabilities.py](workstation/capabilities.py)

What is still missing is the durable subject-scoped layer between them.

At present:

- source markdown can be learned into artifacts or portable skill bundles
- chats can save or append markdown
- existing markdown can be opened for observation

But the system still lacks a first-class answer to:

> What is the durable learning state of subject X across sources, discussions, derivations, and exported skills?

Without that layer:

- markdown is treated too much like raw host text
- skills are treated too much like the only durable learned form
- round-trip updates drift
- provenance is too file- and import-centric rather than subject-centric

## Core Decision

The missing object should be a first-class:

`LearningContext`

for a subject or subject-family.

The canonical architecture should be:

`Source Documents <-> LearningContext <-> Derived Skills`

with maintained corpus documents as projections of the same context.

This means:

- source markdown is an ingress surface
- skills are reusable/runtime projections
- maintained Typst-style subject docs are human-facing canonical corpus projections
- `LearningContext` is the durable semantic center

### Projection Is Not Installation

The subject bridge and governed ability lifecycle remain separate:

- corpus admission decides which learning units belong to a `LearningContext`
- skill projection materializes subject-linked portable YAML with provenance
- governed skill installation separately evaluates policy and records admission
- the host separately supplies the exact executor or broker implementation

A file under `derived/skills/` therefore establishes neither runtime admission
nor host support. Subject scope can expose projections for bounded prior-learning
reuse, but it cannot grant authority or create a realizer.

## Learning Context

`LearningContext` is the durable, inspectable, governed subject memory for one subject scope.

It is not:

- a raw markdown file
- a transcript
- a skill export
- a prompt-local task contract

It is:

- the current admitted learning state for a subject
- the bridge between source documents and derived reusable residue
- the subject-scoped context that later updates should re-enter

## Required Contents

A `LearningContext` should store at least:

- stable subject id
- canonical subject title
- aliases and lookup keys
- broader category / subject family
- subject summary
- admitted concepts
- admitted relations
- admitted executable abilities
- examples
- counterexamples
- misconceptions / confusions
- open questions
- unresolved ambiguities
- provenance records
- linked source documents
- linked derived skills
- linked corpus document sections
- update history
- governance/admission status

The key rule is:

- context stores semantic units and their status
- documents and skills project from that

## Learning Units

Inside a `LearningContext`, the system should not store only undifferentiated prose.

It should store typed learning units such as:

- `definition`
- `relation`
- `ability`
- `example`
- `counterexample`
- `boundary`
- `misconception`
- `open_question`
- `source_note`

Each unit should carry:

- stable unit id
- unit kind
- canonical title or identity
- normalized aliases
- human-facing statement
- structured fields where applicable
- provenance support
- admission status
- links to derived artifacts or skills

This keeps the corpus semantically inspectable instead of collapsing into append-only notes.

## Corpus Home

Each subject should live in a durable corpus home.

Suggested layout:

```text
corpus/
  <subject-id>/
    context.json
    subject.typ
    subject.md
    sources/
      <source-id>.md
      <source-id>.json
    deltas/
      <delta-id>.json
    derived/
      skills/
        <skill-id>.yaml
      exports/
        <bundle-id>.yaml
    receipts/
      <receipt-id>.json
    indexes/
      aliases.json
      units.json
```

The intent of this layout is:

- `context.json` = machine-governed durable subject state
- `subject.typ` = canonical maintained human-readable document
- `subject.md` = optional markdown projection for compatibility and review
- `sources/` = imported external documents and source metadata
- `deltas/` = proposed or admitted updates from chat/import/review
- `derived/skills/` = subject-linked skill projections
- `receipts/` = governed learning/update receipts

## Why Typst-Style Documents

The corpus should prefer a Typst-style canonical document over raw markdown for maintained subject material.

Reason:

- stable labeled sections
- better equation and formula handling
- stronger structure for examples and sub-sections
- cleaner long-form subject composition
- better future projection into PDF or review artifacts

Markdown should remain supported for:

- ingress
- compatibility
- lightweight sharing
- fallback projection

But the maintained subject document should not be limited by markdown’s weaker structural anchors.

## Subject Document Role

The canonical subject document should be a projection of admitted context, not the only store of truth.

Its sections should be explicit and stable, for example:

- Subject
- Definitions
- Governing Relations
- Executable Abilities
- Examples
- Counterexamples
- Misconceptions
- Open Questions
- Provenance
- Derived Skills
- Update Log

Each section should be reconstructible from `LearningContext` plus projection rules.

Manual edits may still occur, but the long-term design should make them reconcilable through subject deltas rather than opaque free-form drift.

## Round-Trip Lifecycle

The desired lifecycle is:

1. Observe or ingest one external source.
2. Parse it into formal IR.
3. Propose typed learning units and derived reusable residue.
4. Merge admitted units into the correct `LearningContext`.
5. Materialize updated corpus document projections.
6. Materialize affected skill projections without treating projection as
   governed skill installation.
7. Record receipts and provenance for the update.
8. Allow later conversation or source imports to re-enter the same subject context.

This is the intended round trip:

```text
External Markdown / Notes / Manual
  -> Formal IR
  -> Proposed Learning Delta
  -> LearningContext Merge
  -> Corpus Doc Projection (Typst/Markdown)
  -> Skill Projection / Export
  -> Later Chat Or Source Update
  -> Proposed Learning Delta
  -> Same LearningContext
```

## Learning Deltas

Chat-originated learning should not directly append prose to a markdown file as the primary semantic act.

Instead, the preferred object should be a:

`LearningDelta`

A `LearningDelta` is a proposed additive or corrective update against one existing `LearningContext`.

It should capture:

- target subject id
- originating source kind
- explicit operations over proposed or existing units
- rationale
- evidence/provenance
- derived skill impact
- document projection impact

This allows the system to say:

- observe existing subject state
- propose a learning delta
- admit or reject the delta
- then materialize updated docs and skills

This is much stronger than:

- append this chat text to a markdown file

## Delta Operator Semantics

`LearningDelta` should not rely only on an implicit “all proposed units get added” convention.

The canonical update surface should include explicit operator kinds:

- `initiate`: admit new learning units into the subject context
- `append`: extend an existing unit additively without changing its identity
- `replace`: supersede one or more prior units and introduce replacement units
- `remove`: deprecate a unit without erasing its history
- `improve`: revise an existing unit in place while keeping its identity
- `link`: add provenance or projection links without changing the unit statement
- `split`: supersede one coarse unit into multiple narrower units
- `merge`: supersede multiple narrow units into one merged unit
- `reject`: explicitly reject an existing or proposed unit
- `restore`: reactivate a previously deprecated or rejected unit

Two constraints matter here:

- `proposed_units` should act as the deterministic unit pool referenced by explicit operations
- semantic title or kind changes should use `replace`, not in-place patching, because unit identity is grounded in stable subject/kind/title ids

Legacy deltas without explicit operations may still use the additive compatibility path, but new work should prefer explicit operator intent.

## Future Scope: Typed Learning Cross-References

Learning context still needs first-class unit-to-unit cross-reference management.

That future slice should introduce typed links such as:

- `supports`
- `contradicts`
- `extends`
- `depends_on`
- `supersedes`
- `example_of`
- `derived_from`
- `see_also`

This should become a governed graph over learning units and projections, not loose prose references embedded in statements or markdown sections.

## Capability Surface

The current workstation markdown actions should remain, but they should become leaf host operations below a richer learning surface.

Recommended higher-level capability family:

- `ws.learning.context.open`
- `ws.learning.context.list`
- `ws.learning.delta.propose`
- `ws.learning.delta.review`
- `ws.learning.delta.apply`
- `ws.learning.source.ingest`
- `ws.learning.doc.render`
- `ws.learning.skill.refresh`

These higher-level capabilities should be promoted only after the persistent
`LearningContext` / `LearningDelta` substrate exists. They are not the first
implementation step.

These should sit conceptually above:

- `ws.markdown.open`
- `ws.markdown.create`
- `ws.markdown.append`

The markdown capabilities remain useful for bounded file observation or write materialization, but they should not define the semantics of learning.

## Projection Rule

The system should project from `LearningContext` into at least three external forms.

### 1. Human Corpus Projection

- canonical Typst-style subject document
- optional markdown mirror

### 2. Runtime Projection

- portable skill bundle
- skill store installation payloads
- workflow-relevant ability/knowledge residue

### 3. Inspection Projection

- subject summary views
- provenance views
- delta review views
- update receipts

The projection rule is:

- `LearningContext` is authoritative for subject learning state
- projections are materializations, not competing truth stores

## Provenance Rule

Every derived skill should be linked back to:

- subject id
- unit ids
- source ids
- document section ids
- learning delta ids

Every subject document section should be linked forward to:

- context unit ids
- derived skill ids where applicable

Every update receipt should identify:

- what changed
- why it changed
- what source or conversation supported it
- which projections were regenerated

Without this, markdown-skill-markdown round trips will drift into weak title-based reconstruction.

## Governance Rule

`LearningContext` does not weaken governance.

It should preserve and expose:

- source boundedness
- admission/rejection
- support strength
- unresolved ambiguity
- deprecation or supersession

The presence of a subject context must not allow:

- raw transcript text to become admitted knowledge automatically
- free-form append behavior to bypass review
- skill export to silently redefine subject truth

The rule remains:

- source text proposes
- context admits
- projections materialize

## Determinism Rule

The closer the system gets to subject identity, unit identity, and projection mapping, the less it should depend on heuristic natural-language matching.

Use heuristics for:

- initial source classification
- candidate subject suggestion
- alias suggestion
- merge proposal support

Prefer explicit source-side subject hints when available, for example intro
metadata lines such as:

- `Subject: ...`
- `Subject ID: ...`
- `Aliases: ...`
- `Subject Family: ...`
- `Summary: ...`

Use deterministic structure for:

- subject id selection
- corpus home placement
- unit ids
- section anchors
- skill-to-context links
- provenance edges
- projection regeneration

This is important because the repository already contains heuristic ranking surfaces for natural-language matching. `LearningContext` should reduce, not widen, identity drift.

## Relationship To Current Code

This design should build on the current implementation rather than replace it.

### Already aligned

- [learning_context.py](learning_context.py)
  - now provides subject-scoped durable learning context and learning delta persistence under one deterministic corpus-home layout
- [learning_context_projection.py](learning_context_projection.py)
  - now materializes deterministic `subject.typ` and `subject.md` projection scaffolds from one authoritative `LearningContext`
- [learning_context_skill_projection.py](learning_context_skill_projection.py)
  - now regenerates corpus-admitted linked units into canonical portable skill YAML under `derived/skills/` through the standard skill compiler/export path, without treating projection as governed skill installation
- [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
  - already implements governed external-source learning through formal IR
- [markdown_learning_artifact_semantics.py](markdown_learning_artifact_semantics.py)
  - already repairs and grounds learned residue with provenance-aware shaping
- [workstation/capabilities.py](workstation/capabilities.py)
  - already has bounded markdown observation and materialization primitives
- [workstation/learning_capture.py](workstation/learning_capture.py)
  - now routes prompt-scoped chat “save learnings” markdown flows back into persisted source, delta, and subject-context updates
- [workstation/workstation_core.py](workstation/workstation_core.py)
  - already has a workstation action surface for markdown learning

### Still missing

- richer maintained subject composition beyond the current deterministic subject-document scaffold
- deterministic subject-to-skill-to-doc linkage

This last gap is already called out in [SKILLS_IMPLEMENTATION.md](SKILLS_IMPLEMENTATION.md).

## Suggested Phased Adoption

### Phase 1

Define and persist:

- `LearningContext`
- `LearningDelta`
- corpus home layout

No large UI changes required yet.

### Phase 2

Change markdown learning to target:

- `source -> delta -> learning context`

instead of:

- `source -> learned bundle -> import`

while preserving current compatibility exports.

### Phase 3

Add subject document projection:

- canonical `subject.typ`
- optional `subject.md`

### Phase 4

Regenerate skills from context-linked units and route that through the canonical skill compiler/import path.

### Phase 5

Expose higher-level workstation actions so the LLM can:

- open a subject context
- observe current maintained contents
- propose a learning delta
- apply it under approval/governance
- regenerate affected docs and skills

## What Not To Do

- do not treat transcript append as the primary learning architecture
- do not let markdown files become the only subject memory
- do not let skill exports become the only durable learned form
- do not use fuzzy title matching as the final subject identity rule
- do not bypass learning review by writing directly into corpus docs
- do not create a second unrelated persistence universe beside the current artifact/skill/governance machinery

## Summary

The repository should move from:

- markdown import
- skill import/export
- markdown save/open/append

as mostly separate actions

to:

- a subject-centered corpus architecture
- with `LearningContext` as the durable semantic middle
- Typst-style maintained subject docs as human projections
- skills as reusable runtime projections
- and all future markdown or chat learning re-entering that same context through governed deltas

That is the structure needed to make learning and skills form one round-trip corpus instead of several adjacent tools.
