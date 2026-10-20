# Subject Imports And Bounded Cross-Subject Reasoning

## Purpose

This document defines the formal position for disciplined cross-subject reasoning inside the workstation research, review, and publication flows.

The core need is subtle:

- subject-bounded work should not become subject-isolated work
- cross-subject reasoning should be possible
- cross-subject reasoning should never become ambient, silent, or unaudited

This matters because the system should be able to produce intelligent research and intelligent publications, not only deterministic projection over one sealed subject.

## Why This Layer Is Needed

The current repository already has:

- governed controller/runtime reasoning
- durable subject corpus admission
- deterministic subject projections
- deterministic publication projection

But it does not yet have a first-class concept for:

- borrowing material from one subject while working inside another subject

Without that layer, the system falls into one of two bad states:

1. it becomes too isolated
- a subject can only use what is already local
- useful prior subject work cannot be brought in cleanly
- publication becomes too shallow or repetitive

2. it becomes too ambient
- global retrieval silently mixes subjects
- borrowed material becomes indistinguishable from native subject truth
- replay, audit, and publication provenance become weak

So the missing construct is not “more retrieval”.

It is:

- explicit subject imports
- bounded cross-subject reasoning

## Core Position

The system should work with:

- one `Active Subject`
- zero or more `Imported Subjects`
- one governed `Reasoning Scope`

The `Active Subject` is the home jurisdiction.

The `Imported Subjects` are temporary, explicit, and bounded supporting contexts.

The `Reasoning Scope` is the controller-visible working memory built from:

- native active-subject material
- explicitly admitted imported-subject slices
- optionally global artifacts, if separately allowed

The controller may reason over all three, but it must preserve their distinction.

## Design Rule

Cross-subject reasoning must be:

- explicit
- scoped
- version-pinned
- typed
- auditable
- non-ambient

That means:

- no silent subject mixing
- no floating “latest” subject borrowing in governed publication work
- no treating borrowed material as native by default

## What A Subject Import Is

A `Subject Import` is a governed record saying:

- while working on subject `A`
- borrow selected material from subject `B`
- at a particular subject version
- for a declared reason
- under a bounded admissibility scope

This is not the same thing as:

- copying units from `B` into `A`
- merging subjects
- global artifact retrieval

It is a governed temporary bridge.

## Why Version Pinning Matters

If imported subject material floats with the latest version, then:

- workflow resumption becomes unstable
- review loses reproducibility
- publication replay loses determinism

So imports should bind to:

- `source_subject_id`
- `source_subject_version_id`

This is especially important for large piles of subjects and publications, where resumption and replay must remain smooth and defensible.

## Typed Import Intent

Every import should declare why it exists.

This is not cosmetic metadata. It is how the system preserves discipline.

Useful import kinds include:

- `definition_support`
- `comparison`
- `method_transfer`
- `example_transfer`
- `counterexample_transfer`
- `background_only`
- `publication_dependency`
- `review_dependency`

Why this matters:

- the controller should reason differently over a background import than over a publication dependency
- publication should disclose dependency imports differently from comparison imports
- later admission should be judged differently depending on the intent

## Scoped Import Slices

The default import should not be “whole foreign subject”.

The default import should be a slice.

Examples of bounded import slices:

- selected unit ids
- selected skill ids
- selected source ids
- selected publication claims
- selected section/block ids

Why this matters:

- smaller imports are easier to audit
- retrieval pressure stays lower
- reasoning remains inside the declared scope
- borrowed material does not overwhelm native subject identity

## Native Versus Borrowed Memory

Inside controller-visible working memory, each reusable item should remain marked as:

- `primary`
- `borrowed`
- `global`

It should also retain:

- `source_subject_id`
- `source_subject_version_id`
- `import_kind`
- `origin_record_id`

Why this matters:

- the controller can use foreign material without confusing its provenance
- research output can remain explicit about where a supporting relation came from
- publication can disclose dependency rather than laundering borrowed material into local truth

## Priority Ordering

Reasoning and retrieval should prioritize:

1. active subject material
2. imported subject material
3. global artifact-store material

Why this matters:

- native subject truth should dominate local reasoning
- borrowed subject material should support, not replace, the active subject
- global retrieval should be weakest because it is least accountable to the current subject

## No Silent Internalization

Borrowed material should not become native subject truth automatically.

If cross-subject reasoning yields a new insight for the active subject, then:

- that result should enter the active subject through a new governed delta
- the borrowed support should remain borrowed unless separately internalized

Why this matters:

- subject identity stays coherent
- admission remains explicit
- publication can show whether a result is native, borrowed, or newly synthesized

## Publication Consequence

Publication should be able to distinguish:

- native subject material
- imported dependency material
- transcluded cross-subject material
- newly synthesized publication-level reasoning

Why this matters:

- intelligent publication should still be honest publication
- publications need to expose dependency, not hide it
- reproducibility depends on knowing what was native and what was borrowed

## Relationship To Current Repository

The repository already has the ingredients for this direction:

- subject corpus and deltas in [learning_context.py](learning_context.py)
- subject workflow in [workstation/subject_workflow.py](workstation/subject_workflow.py)
- controller prior-learning reuse in [governed_prior_learning_reuse.py](governed_prior_learning_reuse.py)
- publication graph/projection in [publication_projection.py](publication_projection.py)

What is missing is the binding layer:

- a first-class subject import record
- a subject-scoped reasoning context that includes imports
- import-aware retrieval priority
- publication disclosure of imported subject dependencies

## What This Is Not

This document does not propose:

- merging all subjects into one corpus blob
- replacing deterministic publication with free-form runtime generation
- letting controller retrieval mix all subjects silently
- making imported material auto-native

## One-Sentence Summary

The correct model is: one active subject, plus explicit version-pinned imported subject slices, inside a governed reasoning scope that preserves provenance and keeps publication both intelligent and auditable.
