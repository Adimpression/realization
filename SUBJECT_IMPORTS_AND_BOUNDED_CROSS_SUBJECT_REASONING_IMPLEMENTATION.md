# Subject Imports And Bounded Cross-Subject Reasoning Implementation

## Purpose

This document gives implementation guidance for making cross-subject reasoning real without weakening subject identity, review discipline, or publication reproducibility.

It is intentionally suggestive rather than over-prescriptive.

The implementer should preserve the central rule:

- cross-subject reasoning is allowed
- ambient cross-subject mixing is not

## Current First Cut

The first bounded implementation slice is now present.

Implemented:

- first-class `SubjectImport` persistence under `corpus/<active-subject>/imports/`
- per-subject import index under `corpus/<active-subject>/indexes/imports.json`
- explicit `SubjectReasoningScope` loading from active subject plus active approved imports
- workstation subject-workflow visibility of active import counts and imported-subject counts
- workstation staging of pinned import sources with selectable bounded scope growth from `units only` to `units and skills` to `full context`
- publication dependency disclosure of active approved imports as pinned subject-import sources/xrefs
- subject-aware runtime bootstrap through [runtime_controller_api.py](runtime_controller_api.py)
- bounded preload of active-subject and approved-import skill-shaped projections into controller-visible learned artifacts
- origin metadata in runtime state for preloaded learned artifacts via `primary` and `borrowed` tiers
- controller-side reuse ordering now prefers `primary -> borrowed -> global`
- controller-side ambient store lookup is now blocked when the active subject scope disables global retrieval
- controller trace payloads and node proposal payloads now surface learned-artifact origin tiers so borrowed/global reuse is inspectable in receipts

This means the repository now has an explicit durable cross-subject bridge.
The controller/runtime bridge is now scope-aware at bootstrap time.

This bridge controls visibility and provenance for prior-learning reuse. A
projection is not thereby installed or admitted as a governed ability, and
subject scope does not supply its executor or broker.

What is still later work is richer multi-import operator tooling and higher-level research/publication assistance on top of this bounded bridge.

## Why Implementation Needs A Separate Layer

The current code already supports:

- durable subject maintenance
- durable publication projection
- reusable artifact storage
- controller-side prior-learning reuse

But those capabilities are still attached to different substrates.

The missing capability is not “more intelligence”.

It is:

- a controlled bridge between subject corpus and controller runtime

Without that bridge:

- research remains too local
- publication remains too compiler-like
- controller reuse remains too global

So the implementation target should be a new governed layer, not an incidental retrieval tweak.

## Suggested Implementation Shape

### 1. Introduce A First-Class `SubjectImport` Record

Add a formal record type that binds:

- active subject
- active subject version
- source subject
- source subject version
- import kind
- bounded imported slice
- rationale
- creation timestamp
- review/admission status

Why:

- this is the object that makes cross-subject reasoning explicit
- without a real record, imports will drift into ambient retrieval behavior

Suggested persistence location:

- under the active subject root
- likely a dedicated `imports/` area

Why there:

- imports belong to the working subject’s continuity story
- they are not global facts

### 2. Introduce An Explicit `SubjectReasoningScope`

Build a runtime-facing structure that contains:

- one active subject version
- zero or more imported subject records
- optional global retrieval policy

This structure should be what the workstation passes to any controller-assisted research/review/publication operation.

Why:

- the controller needs a bounded working set
- the subject workflow needs an object that can be resumed, inspected, and audited

### 3. Distinguish Memory Origins In Runtime State

Where imported or preloaded artifacts enter controller-visible memory, preserve origin metadata such as:

- `origin_kind = primary | borrowed | global`
- `source_subject_id`
- `source_subject_version_id`
- `source_import_id`
- `import_kind`

Why:

- reasoning must remain provenance-aware
- later admission and publication disclosure depend on knowing where support came from

### 4. Make Retrieval Subject-Aware Before It Becomes Smarter

Do not start with richer ranking alone.

Start by making reuse and retrieval aware of:

- active subject
- imported subjects
- retrieval priority tier

Suggested priority:

1. active subject artifacts
2. imported subject artifacts
3. global artifact store

Why:

- this preserves subject identity
- it gives the controller useful foreign support without letting global reuse drown the active subject

### 5. Prefer Slice Imports Over Whole-Subject Imports

The initial implementation should bias toward bounded slices:

- unit ids
- skill ids
- source ids
- claim ids
- section/block ids

Why:

- smaller imports are easier to validate
- easier to show in the UI
- easier to replay and resume
- easier to disclose in publication

Whole-subject imports may still be useful later, but they should not be the first operational default.

## Suggested Insertion Points In Current Code

### Subject Corpus Layer

Relevant files:

- [learning_context.py](learning_context.py)
- [workstation/learning_capture.py](workstation/learning_capture.py)

Suggested role:

- persist subject-import records
- bind imports to subject versions and deltas
- expose import indexes for resumption

Why:

- subject corpus is the continuity root
- imports must survive workstation restarts and UI changes

### Workstation Subject Workflow Layer

Relevant file:

- [workstation/subject_workflow.py](workstation/subject_workflow.py)

Suggested role:

- let the user create, inspect, approve, reject, and retire imports
- expose the active subject reasoning scope in Gather, Draft, Review, and Publication
- show what is native and what is borrowed

Why:

- the user needs to understand the active working set
- workflow resumption depends on visible scope, not hidden scope

### Controller Runtime Bridge

Relevant files:

- [runtime_controller_api.py](runtime_controller_api.py)
- [governed_prior_learning_reuse.py](governed_prior_learning_reuse.py)
- [main.py](main.py)
- [store.py](store.py)

Suggested role:

- allow a controller bootstrap that is subject-aware
- preload or filter reusable artifacts by primary/import/global tiers
- record origin-aware reuse inside runtime traces

Why:

- this is the point where cross-subject reasoning becomes real
- but it must remain bounded by an explicit scope object

### Publication Layer

Relevant files:

- [publication_projection.py](publication_projection.py)
- [publication.py](publication.py)
- [publication_render.py](publication_render.py)

Suggested role:

- record publication dependencies on imported subjects
- distinguish native, imported, and synthesized material
- allow deterministic render while disclosing foreign dependencies

Why:

- intelligent publication still needs a deterministic and auditable release path

## Suggested Capability Progression

### Phase 1. Make Imports Explicit

Implement:

- `SubjectImport` persistence
- subject workflow visibility
- import creation and retirement
- resumption indexes

Do not yet:

- deeply integrate with controller reduction

Why:

- first make the imported working set explicit and durable
- otherwise later reasoning behavior will be hard to inspect

Current status:

- `SubjectImport` persistence: implemented
- subject workflow visibility: implemented at count/summary level
- resumption indexes: implemented
- subject-aware runtime bootstrap: implemented
- origin-aware learned artifact preload: implemented
- workstation pin/create/approve/reject/retire import actions: implemented in the shared subject workflow
- workstation staged import selection/inspection: implemented for one pinned source with explicit bounded-scope growth and previewed staged slice counts
- workstation import action surface is still intentionally narrow: one pinned source at a time and latest-import review/retirement

### Phase 2. Make Controller Reuse Scope-Aware

Implement:

- subject-aware runtime bootstrap
- active/import/global retrieval prioritization
- origin-aware learned artifact loading

Why:

- this is the smallest meaningful step toward “intelligent subject work”
- it improves reasoning without yet making publication nondeterministic

Current status:

- runtime bootstrap support in [runtime_controller_api.py](runtime_controller_api.py): implemented
- active/import learned-artifact preload from subject projections: implemented
- controller-side reuse ordering over active/import/global tiers: implemented
- ambient global lookup gate when scope disables global retrieval: implemented
- query-time retrieval now returns ranked local scope artifacts before ambient store fallback: implemented
- broader post-bootstrap retrieval ranking over active/import/global tiers: implemented for controller store lookup and reuse selection
- controller trace/origin surfacing for borrowed/global reuse: implemented in learning-context steps, related-support steps, and proposal-state payloads

### Phase 3. Add Gather Assistance

Use the controller for bounded advisory tasks such as:

- contradiction scanning
- duplicate or overlapping unit detection
- missing-definition detection
- weak-evidence detection
- subject-bound relation synthesis proposals

Why:

- this makes research sharper
- but keeps admission explicit through deltas

### Phase 4. Add Publication Assistance

Use the controller to generate bounded publication-support artifacts such as:

- section-structure proposals
- claim grouping proposals
- dependency suggestions
- evidence coverage diagnostics
- missing-xref diagnostics

Why:

- this gives publication a reasoning layer
- but keeps final publication assembly deterministic

## Important Governance Rule

Controller-assisted output in this area should be treated as:

- advisory by default

It should become subject truth or publication truth only through explicit admission.

Why:

- otherwise cross-subject reasoning becomes hidden mutation
- the architecture would drift back into ambient semantic mixing

## Workflow Resumption Guidance

This area must be designed with large piles of subjects and publications in mind.

The resumption question is:

- when the user returns later, can the system reconstruct the exact active reasoning scope quickly and clearly?

To support that, keep resumable pointers such as:

- active subject
- active subject version
- active imports
- last import review status
- last controller-assisted diagnostics for the subject
- last publication dependency set

Why:

- smooth resumption is not just opening the subject
- it is reopening the subject together with the same bounded borrowed memory and dependency posture

## What Not To Do

- do not let global retrieval silently substitute for imports
- do not let imported material become native automatically
- do not bind publications to floating foreign subject state
- do not let the controller mutate subject or publication records directly without an explicit admission step
- do not hide import provenance in free-form summaries only

## Practical Litmus Test

The implementation is on the right track if, for any research or publication result, the system can answer:

- what was the active subject?
- which foreign subjects were imported?
- which versions were imported?
- why were they imported?
- what exact slices were imported?
- what output was merely advisory?
- what output was admitted?
- what publication dependencies must be disclosed?

If those questions cannot be answered quickly, the implementation is still too ambient.

## One-Sentence Summary

Implement subject imports as a first-class governed layer between subject corpus and controller runtime, so cross-subject reasoning becomes explicit, bounded, resumable, and publication-safe instead of global and ambient.
