# Decision Support Tool Implementation

Implementation note for the Decision Support Tool (`DST`) layer.

This document describes how DST should combine:

- governed candidate discovery
- typed normalization
- formal evaluation
- workstation curation
- publication consumption

It is aligned to the governing repo theory, decision-review, publication, and normalization contracts.

## Current Implementation Direction

The next DST extension should be an additive revision layer.

That means:

- keep the current snapshot pipeline intact
- add explicit revision-aware structures around it
- preserve existing client contracts while introducing model-evolution semantics

This matters because current consumers already depend on the snapshot-oriented DST surface:

- discovery results
- normalized cases
- projected `DecisionFrame`
- projected `DecisionReviewItem`
- projected `coordinated_transformation.Model`
- workstation construct-candidate refresh and decision-analysis refresh

Those consumers should continue to receive the same kinds of objects with the same meanings.

The revision layer should therefore explain:

- how one case snapshot becomes another
- when prior judgments become stale
- which prior results can be preserved
- which parts must be recomputed

It should not redefine what an existing snapshot means.

## Compatibility Constraint

Backward compatibility is a first-order implementation rule here.

The safe rule is:

> every current DST client should continue to work if it knows nothing about revision semantics

That means the first revision-capable implementation must not break:

- current fixture loading
- current markdown source parsing
- current deterministic discovery and normalization runners
- current orchestration output
- current projection functions
- current workstation Draft / Review / Publication consumption

Revision awareness should arrive through additive structures, additive metadata, or new helper functions.

It must not require existing callers to change just to keep doing what they already do.

## Why This Must Be Additive

`DST` already has one correct core behavior:

- take source material
- discover candidate paths
- normalize them into an explicit case
- project the result into decision-facing structures
- evaluate under `coordinated_transformation`

That is the snapshot pipeline.

The revision layer answers a different question:

- what changed when later material arrived

So the revision layer must wrap the snapshot pipeline rather than replace it.

If we merged the two too early, we would risk breaking:

- current workstation flows
- current deterministic fixture tests
- current BDD stories
- current publication continuity

The implementation should therefore be staged.

## Current State

The first DST code slice is now in place:

- markdown use-case source lives in [src/dst](src/dst)
- checked-in typed fixtures live in the packaged DST fixture area
- [src/dst/core.py](src/dst/core.py) treats typed fixtures as authoritative and uses markdown parsing only for reconciliation
- [src/dst/discovery.py](src/dst/discovery.py) provides the first governed discovery seam:
  - typed discovery fixtures
  - `reduce_not`-oriented candidate-path discovery prompt shaping
  - structured DST-lexicon-governed discovery framing
  - governed discovery -> typed normalization input shaping
- [src/dst/normalization.py](src/dst/normalization.py) provides the first typed normalization seam:
  - strict typed loading and validation of the normalized DST JSON contract
  - normalized-case -> `coordinated_transformation.Model`
- [src/dst/projection.py](src/dst/projection.py) provides the first bridge from typed DST fixtures into:
  - `DecisionFrame`
  - `DecisionReviewItem`
  - a first `coordinated_transformation.Model`
- [src/dst/orchestration.py](src/dst/orchestration.py) now provides the first execution seam:
  - build the structured `reduce_not` discovery prompt packet
  - run discovery then normalization through injected runners
  - project the normalized case into `DecisionFrame`
  - build the normalized-case `coordinated_transformation.Model`
  - execute runtime-backed DST discovery and normalization proposals over root non-achievedness through an explicit caller-provided `DstControllerBootstrap`
  - fail closed when the caller has not supplied that controller realization

That bridge is intentionally conservative:

- all typed candidate paths are preserved in the DST-side decision projection
- only direct one-step path candidates are currently mapped into immediate formal decisions in `coordinated_transformation`
- multi-step candidate paths remain present in the projected decision frame, but are not yet expanded into formal multi-step plan evaluation

So the current implementation status is:

- typed DST fixture substrate: complete
- first governed discovery seam: complete
- first typed normalization seam: complete
- first decision-frame bridge: complete
- first theory-facing model bridge: complete
- first orchestration seam: complete
- first runtime-backed live DST execution seam: complete
- first workstation construct-candidate persistence and `Draft Model` curation: complete
- first live workstation construct discovery for non-fixture subjects: complete, with deterministic fallback
- first lane-aware Draft Model curation and relation editing slice: complete
- first assignment-binding and missing-relation inspection slice in Draft Model: complete
- first capability dependency/boundary relation-binding slice in Draft Model: complete
- first bounded multi-step admissible path enumeration seam into `Explore`: complete
- first continuity-preserving DST refresh/upsert slice in `Itemize -> Suggest Constructs`: complete
- first continuity-preserving DST refresh/upsert slice in `Draft -> Refresh DST Analysis`: complete
- first Review/Publication continuity slice for DST model access: complete
- live workstation DST flow and persistence: not complete

## Existing Test Shield

Before introducing revision-aware behavior, the current DST surface is now covered by three layers inside [dst/tests](tests):

1. unit and package tests
2. client-compatibility tests
3. self-contained BDD tests

The BDD layer is intentionally package-local and fixture-free at the prose level:

- embedded prose lives directly in the BDD test methods
- story harnesses and support builders live in Python support modules
- revision/model-evolution expectations are covered separately from snapshot behavior

That matters because the revision layer should be introduced under a “tests stay green” discipline:

- current snapshot behavior must remain covered
- revision behavior must be added without weakening those expectations

So the implementation sequence is:

1. freeze current behavior
2. add revision behavior tests
3. add revision-layer types and helpers
4. integrate them behind current snapshot outputs
5. only then expose revision-aware workstation behavior

## Intended Revision Layer Shape

The first revision-capable DST implementation should introduce explicit revision-facing concepts without altering the existing snapshot-facing ones.

A safe conceptual split is:

- `DstDiscoveryResult`
  - snapshot-local discovery product
- `NormalizedDstCase`
  - snapshot-local typed case product
- `DecisionFrame`
  - snapshot-local review product
- `coordinated_transformation.Model`
  - snapshot-local evaluation product

and then add revision-layer companions such as:

- `DstCaseSnapshot`
- `DstCaseRevision`
- `DstCaseTimeline` or `DstCaseHistory`
- `RevisionImpact`

The exact names can change.
The important point is the layer boundary:

- current product types remain snapshot products
- new revision types describe cross-snapshot change

## Minimal First Revision Semantics

The first real DST revision layer does not need to solve every continuity problem at once.

It should first support:

1. source-basis continuity
   - what source set or source revision produced this snapshot

2. snapshot identity
   - which normalized case and projected decision frame belong to the same revision point

3. revision traceability
   - what changed between two snapshots

4. invalidation scope
   - which prior discovery/normalization/evaluation results became stale

5. re-evaluation discipline
   - which parts must be recomputed under the new snapshot

That is enough to support a correct first model-evolution layer.

## Revision Rules DST Should Follow

Because `coordinated_transformation` now has explicit implementation guidance for model revision, DST should align to it.

The practical rule is:

- if a revision changes admissibility-relevant facts, prior formal judgments must be treated as stale

So when later source material changes any of the following, DST should force re-evaluation of the affected routes or decisions:

- dependencies
- satisfied/unsatisfied dependency state
- active constraints
- capability admissibility-under facts
- transition admissibility-under facts
- crossed boundaries
- boundary friction
- actor-assignment feasibility
- available alternative transitions

The important discipline is:

- do not reuse an old “blocked”, “valid”, “executable”, or “recommendable” result when the facts it depended on changed

This is exactly the kind of continuity bug the current workstation already exposed in the `v2 -> v10` same-subject path.

So the revision layer is not abstract polish.
It is the correct formalization of behavior we already need.

## First Additive Implementation Phases

The safest sequence is:

### Phase 1: revision data structures only

Add revision-layer structures and helpers without changing current orchestration return types.

Examples:

- snapshot ids
- predecessor snapshot ids
- source-basis ids
- revision reason / revision source
- changed-fact summaries
- invalidation summaries

At this phase, existing clients can ignore the new layer completely.

### Phase 2: snapshot diff and invalidation helpers

Add pure helpers that answer questions like:

- what changed between snapshot A and snapshot B
- which candidate paths were preserved
- which normalized facts were added or removed
- which admissibility-sensitive facts changed
- which prior decision judgments must be recomputed

These helpers should not yet force workstation behavior changes.

### Phase 3: orchestration integration

Teach DST orchestration to produce revision metadata alongside the current snapshot outputs.

This still must preserve the current snapshot outputs as-is.

### Phase 4: workstation continuity integration

Only after the revision layer is stable should the workstation begin to consume it for:

- stale-analysis detection
- refresh guidance
- continuity-preserving draft/update behavior
- newly blocked / newly unblocked decision explanation

### Phase 5: publication continuity integration

After that, publication/review can start to consume revision-aware explanations such as:

- what changed since the prior approved plan
- which options became unavailable
- which route is newly preferred

## What Must Not Change First

The following should not be rewritten as part of the first revision-layer step:

- the public package-root exports that current tests freeze
- deterministic discovery runner contracts
- deterministic normalization runner contracts
- `run_dst_pipeline_from_fixture(...)` return semantics
- current projection return types
- current workstation draft-analysis flows, except where revision stale-state must be corrected

If a change touches one of those surfaces, it should be justified as a compatibility-preserving extension rather than a silent semantic rewrite.

## Decision-Focused Why

This implementation direction exists for one reason:

decision support does not operate on a frozen world.

A serious decision-support system must handle:

- later evidence
- later blockers
- later alternative routes
- later constraints
- later approvals
- later actors

without either:

- erasing continuity
- or reusing stale judgments

So the DST revision layer is the bridge between:

- governed discovery over changing case material
- and CTFS evaluation over explicit snapshot-local decision structure

That is the next implementation step.

## Source Prose And Learned Intermediates

The `dst/*.md` files should now be treated as source prose for governed intake, not as publication text and not as the final semantic truth layer.

That means:

- source cleanup is intentionally narrow:
  - remove internal jargon
  - remove formatting noise
  - keep the source readable as source
- source cleanup must not:
  - tune the source into publication prose
  - smuggle report structure into the source
  - treat the source as the publication draft
- ingestion should continue to preserve the source as provenance
- the durable value should live in the learned intermediate structures:
  - itemized units
  - normalized DST cases
  - decision frames
  - decision review items
  - analysis receipts
- publication should be composed from those intermediate structures, not by echoing raw source prose directly into report sections

Publication-quality wording should instead come from explicit rephrase operations in the workstation:

- `Itemize` rephrase using LLM
- `Itemize` rephrase using manual editing
- `Draft` rephrase using LLM
- `Draft` rephrase using manual editing

This is important because source prose should remain upgradable.

When new prose arrives, the system should support:

`source prose -> governed deltas / learnings -> itemize/draft rephrase -> normalized DST structures -> recomposed publication`

Current implementation slice:

- manual `Itemize` rephrases now survive itemization regeneration when the refreshed material still matches the same source continuity
- manual `Draft` rephrases now survive draft-composition refresh as long as that upstream itemized identity is preserved
- `@llm` rephrase now stages a pending intermediate target instead of stopping at chat seeding alone
- the latest assistant reply can now be explicitly applied or discarded back into `Itemize` and `Draft`
- applied LLM `Itemize` rephrases now survive itemization regeneration through the same continuity path
- applied LLM `Draft` rephrases now survive draft-composition refresh as `rewrite_llm_proposal`
- `Itemize -> Suggest Constructs` now upserts refreshed DST construct suggestions through continuity-based merge, preserving curated ids, notes, accepted state, and canonical wording while recording the latest generated label in metadata
- `Draft -> Refresh DST Analysis` now upserts refreshed DST decision analysis through the same continuity discipline, preserving curated `DecisionFrame`, `DecisionReviewItem`, and accepted construct state across refreshed normalization

The source is therefore editable only as source.
The normalized intermediate layer is what must remain durable, reviewable, and reusable across re-publication.

## Immediate Next Execution Order

The first publication-industrialization hardening pass over [src/dst](src/dst) is now in place:

1. `dst/*.md` is being used as source-only information, not publication text
2. source cleanup is still intentionally narrow:
   - remove DST/internal jargon
   - remove formatting noise
   - do not rewrite source to sound like the finished publication
3. the existing workstation flow is now exercised over that corpus:
   - `Gather`
   - `Itemize`
   - `Draft`
   - `Review`
   - `Publication`
4. the corpus now includes simpler / less-structured cases so the flow is being hardened against weaker source material too
5. part of that simpler corpus is now intentionally source-only and omits explicit candidate paths, so candidate-path discovery has to happen later through the workstation flow instead of being inherited from the source markdown

The next implementation priority is to continue widening the resulting publication outputs.

The current bounded publication slice is now in place:

- decision tables now carry explicit option-to-transition and actor-assignment reasoning
- execution guidance now carries recommended transitions, responsible actors, and activated capabilities
- the recommendation receipt now carries candidate-path count plus top-option transitions and actors
- a new `Decision Ranking Summary` block now carries policy profile, ranking rules, candidate-path count, and ranked-option reasoning
- the Typst/PDF surface now renders decision matrices as full-width option cards instead of unreadable narrow equal-width columns
- the model diagram now lays out current state, transition path, target state, dependencies, and boundaries separately
- execution guidance and recommendation receipts now surface boundary-governance reasoning explicitly
- the ranking surface now also carries publication-grade guidance text:
  - `Policy guidance`
  - `Current reading`
  - reserve / blocked option callouts
- the ranking surface now also carries reserve / blocked policy narration:
  - reserve options explain why they remain in reserve and what must change to promote them
  - blocked options explain why they remain disqualified before reconsideration
- decision publications now also materialize a real section tree:
  - `Analysis` contains nested option/model/risk subsections
  - `Implementation` contains implementation-guidance subsections
  - `Appendix` contains receipt/audit subsections
- the model diagram now also separates:
  - recommended path
  - reserve paths
  - blocked paths
  - activated capabilities
- capability / dependency / boundary reasoning now follows the recommended and reserve/blocked options in both markdown and Typst/PDF output
- the publication structure is now more composition-aware:
  - subsection titles adapt to the actual block mix instead of one fixed decision template
  - empty scaffold sections are dropped from the materialized publication tree
- the page-aware layout/composition slice is now in place:
  - longer reserve / blocked option cards are rendered as stacked full-width cards and kept readable on paper

The current bounded validation/xref slice is now also in place:

- stronger section-role constraints are enforced in publication validation
- claim-to-unit, claim-to-source, and claim-to-entity typed xrefs are now materialized
- publication query helpers now cover claim impacts through units as well as sources/entities

The current bounded publication-composition diff slice is now also in place:

- the workstation now exposes explicit diff-baseline selection instead of silently choosing one baseline
- the current report plan can now be compared against:
  - the last approved plan
  - the previous persisted revision
  - the current-subject snapshot baseline
- the selected baseline now stays visible in review/publication workspace text and diff receipts

The current bounded publication-composition slice now also includes:

- direct per-section shaping over those richer DST publication structures through Review-side section briefs
- richer import-usage control over selected imported-support items in Review / Publication beyond the old blind cycle-only path

The next widening work after that is:

- reduce repeated policy/path narration across ranking, model, and implementation publication sections

After that, the next deeper DST steps should continue:

- fuller workstation `Itemize -> Draft -> Review -> Publication` live continuity
- fuller persistent inspector/status behavior across `Frame | Model | Explore`
- broader many-to-many relation editing
- richer multi-step path evaluation

## Stable Workspace Constraint

DST implementation now has an additional workstation constraint:

- do not make the user feel they are leaving one tool and entering another

The product shape should be:

- one case workspace
- three DST lenses:
  - `Frame`
  - `Model`
  - `Explore`

Those lenses should sit inside the existing workstation shell rather than introducing a second top-level navigation model.

## Current Execution Gap

The central missing piece is now narrower:

- the runtime-backed executor exists, and the workstation now has a live `reduce_not -> DST_PROMPT` construct-discovery path for `Itemize` plus first lane/relation curation in `Draft Model`, but the fuller persisted workstation path and richer frontier-native `reduce_not` path do not
- `Draft Model` now also exposes the first explicit `Frame | Model | Explore` lens host over the same selected construct, and a first shared status snapshot now appears in the inspector, active lens pane, and issue tray; the fuller persistent inspector/status model is still not complete

The prompt rewrite is now in place:

- the DST `reduce_not` discovery prompt is structured around the DST lexicon
- it asks for fixed top-level sections
- it asks for sort-atom-adjacent language around path families, distinctions, blockers, and missingness

That fixes the earlier variance problem at the contract level.

More concretely, no current method yet performs all of the following in one workstation-governed path for a general live subject:

1. take a raw use case or live corpus selection
2. run `reduce_not` with the DST-specific candidate-path framing from the live workstation/corpus surface
3. collect the governed discovery result
4. run the typed DST normalization contract over that governed packet
5. normalize the result into:
   - `Actor`
   - `Objective`
   - `Capability`
   - `Dependency`
   - `Constraint`
   - `Boundary`
   - `State`
   - `Transition`
   - `Decision`
   - `TimePoint`
6. project that normalized result into:
   - `DecisionFrame`
   - `DecisionReviewItem`
   - `coordinated_transformation.Model`

So the current code now provides:

- the contracts
- the structured prompt
- the typed seams
- the orchestration seam around that path
- an explicit controller-bootstrap port for runtime-backed discovery and normalization

but not the full persisted workstation binding or deeper frontier-native `reduce_not` execution yet.

## Core Decision

DST should not begin with one-shot schema extraction alone.

DST should begin with governed candidate-path discovery.

The correct high-level pipeline is:

`use case -> reduce_not candidate-path discovery -> DST structured projection -> coordinated_transformation evaluation`

At the time of writing, this is partly live:

- the structured prompt exists
- the runtime-backed proposal path exists
- the workstation-integrated persisted path does not yet exist

This is the right split because:

- `THEORY.md` is a theory of governed refinement over unresolved distinctions
- the DST normalization contract is a schema projection layer
- [coordinated_transformation/core.py](../coordinated_transformation/core.py) is a formal evaluator, not a discovery engine

## What `reduce_not` Should Do

With the right prompt framing, `reduce_not` should be the primary engine for:

- finding materially distinct candidate solution paths
- surfacing dominant unresolved distinctions
- surfacing blockers that separate one path from another
- surfacing missing dependencies, constraints, boundaries, and assignments
- preventing premature collapse of multiple viable futures into one vague answer

This is consistent with `THEORY.md`, especially:

- decomposition of undeterminedness rather than tasks
- best-first governed refinement
- dominant distinction selection
- anti-refinement discipline
- spin prevention

The root non-achievedness should be phrased like:

- what are the materially distinct admissible transformation paths for this use case
- what unresolved distinctions determine which path is viable
- what missing facts prevent commitment between the current candidate paths

So `reduce_not` is not merely a weak helper here.

It is the right governed discovery layer for candidate solution families.

## What `reduce_not` Still Needs For DST

For DST, `reduce_not` should not be prompted as a loose strategic brainstorming layer.

Its discovery prompt should be structured around the DST lexicon so that it still discovers:

- materially distinct path families
- dominant unresolved distinctions
- blockers and missing facts

but expresses them in terms that are easier to normalize into the theory sorts and relations.

So the prompt should explicitly request discovery in terms such as:

- path family
- actor impact
- objective tradeoff
- capability delta
- dependency blocker
- binding constraint
- crossed boundary or boundary friction
- current / target / intermediate state
- transition candidate
- decision commitment
- time-phasing distinction
- assumption
- ambiguity
- missing information

This is not because discovery should become a rigid extractor.

It is because a weakly structured prompt will produce avoidable variance across repeated runs of the same case.

## What `reduce_not` Should Not Do

Even in DST, `reduce_not` should not be the final machine-ingestible source of truth.

It should not directly own:

- stable typed ids
- final normalized JSON schema
- final recommendation commitment
- publication-ready typed output

Those require explicit projection and validation.

## What The Typed DST Normalization Contract Should Do

The typed DST normalization contract should be used after candidate discovery.

Its role is:

- serialize governed discoveries into strict normalized JSON
- preserve assumptions
- preserve ambiguities
- preserve missing information
- provide stable typed fields for downstream persistence

So DST prompt extraction is not the first discovery engine.

It is the typed normalization layer.

## What `coordinated_transformation` Should Do

[coordinated_transformation/core.py](../coordinated_transformation/core.py) should evaluate the explicit modeled candidates.

It should answer questions like:

- which transitions are admissible
- which decisions are valid
- which decisions are executable
- where risk is present
- which states are reachable

At the moment it is a formal evaluator, not a best-solution optimizer.

So DST should not expect `coordinated_transformation` alone to invent the candidate set.

## Resulting Architecture

The clean architecture is:

1. `reduce_not`
- candidate-path discovery
- dominant distinction discovery
- blocker and missingness discovery
- expressed through a DST-lexicon-oriented discovery contract rather than loose freeform strategy language

2. `DST projection`
- strict schema conversion via the typed DST normalization contract or equivalent validated serializer

3. `DST validation`
- schema validation
- explicit assumptions / ambiguities / missing-information checks
- stable id normalization

4. `coordinated_transformation`
- formal evaluation of explicit candidates

5. `Draft / Review / Publication`
- curation
- approval
- governed decision-aid output

## Why Not Start With `DST_PROMPT` Alone

The DST normalization contract can extract structure from a use case, but by itself it is too eager to flatten the problem into one normalized representation.

The DST examples often need:

- multiple rival paths
- path-separating distinctions
- missing blockers
- partial rather than total ordering

That kind of structure is better discovered through governed refinement first, then serialized.

So the rule should be:

- use `DST_PROMPT` alone only when the source is already highly structured and the rival path set is explicit
- otherwise use `reduce_not` first

## Workstation Interpretation

The workstation should use this split as follows:

### `Itemize`

Use governed discovery outputs to surface:

- candidate constructs
- candidate paths
- dominant distinctions
- missing blockers
- the first practical `Frame` view of the case

### `Draft`

Use the typed DST projection to:

- curate accepted constructs
- curate accepted candidate paths
- bind them into the active decision frame
- run formal evaluation
- host the stable DST lens controls over the same case object:
  - `Frame`
  - `Model`
  - `Explore`

The coherent desktop wireframe system is **one case workspace, three lenses, one persistent inspector, and one issue tray**.

On desktop, use a **persistent navigation drawer** for the three app-level lenses, a **top app bar** for case-level actions, **tabs** only within the current lens, **cards** for single objects, **lists/tables** for scanning and comparison, **chips** for quick status/filtering/input, a **standard side sheet** as the always-visible inspector, and a **standard bottom sheet** only for issues and validation. Material’s component guidance aligns with those roles, and its layout guidance explicitly treats the side sheet as a large-screen third pane. NN/g’s current guidance on forms also supports grouping related fields, making progress visible, and placing errors close to the relevant input to reduce cognitive load. ([Material Design][1])

Using the **hospital medication upgrade** example makes the wireframes concrete, but the shell is domain-neutral.

## Interaction contract

These rules never change:

* **Drawer** = switch lens: Frame / Model / Explore
* **Tabs** = subsection within the current lens
* **Cards** = one thing
* **Side sheet** = details for the currently selected thing
* **Bottom sheet** = warnings, missing links, validation, assumptions
* **Selection persists across lenses** = the same object stays selected when the user moves between Frame, Model, and Explore

That last rule is the coherence anchor.

---

# 1) Shared shell

```text
┌────────────────────────────── DESKTOP CASE WORKSPACE ───────────────────────────────-┐
│ TOP APP BAR                                                                          │
│ [☰] Hospital medication upgrade                     [Saved] [Validate] [Generate]    │
│ Status chips: [Frame 80%] [Model 62%] [Explore locked]                               │
├──────────────────┬─────────────────────────────────────────────────┬─────────────────┤
│ NAV DRAWER       │ ACTIVE LENS CONTENT                             │ STANDARD SIDE   │
│                  │                                                 │ SHEET           │
│ ● Frame          │ Tabs vary by lens                               │ Inspector       │
│ ○ Model          │ Cards / lists / tables / forms                  │ - selected item │
│ ○ Explore        │                                                 │ - definition    │
│                  │                                                 │ - relations     │
│                  │                                                 │ - missing info  │
├──────────────────┴─────────────────────────────────────────────────┴─────────────────┤
│ STANDARD BOTTOM SHEET (collapsed): 3 issues • 1 warning • 2 assumptions              │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

This shell should be visually stable. The user should feel they are staying inside one workspace, not moving between different products. That matters because people already have high **intrinsic** cognitive load from the domain itself; the interface should avoid adding extra **extraneous** load through shifting layouts or changing interaction patterns. ([Nielsen Norman Group][2])

---

# 2) Screen A — Frame lens

**Question the user is answering:** “What is this case, in plain language?”

```text
┌──────────────────────────────────────── FRAME ──────────────────────────────────────┐
│ Tabs: [Context] [Actors] [Objectives]                                               │
├──────────────────────────────┬──────────────────────────────────────┬───────────────┤
│ OUTLINED CARD                │ OUTLINED CARD                        │ STANDARD SIDE │
│ Context                      │ Case shape                           │ SHEET         │
│ ───────────────────────────  │ ───────────────────────────────────  │ Inspector     │
│ Title                        │ Single-select chips                  │ Selected item │
│ "Hospital medication         │ [One viable path] [Two good paths]   │ q1 No dual    │
│  system upgrade"             │ [Many good paths] [Unknown]          │ mode          │
│                              │                                      │               │
│ Current situation            │ Supporting text                      │ Type          │
│ Paper prescribing with       │ "Choose the expected solution shape  │ Constraint    │
│ rising medication-error risk │  only if you know it now"            │               │
│                              │                                      │ Seen in       │
│ Desired outcome              │ OUTLINED CARD                        │ framing as a  │
│ Fully digital prescribing    │ Key elements                         │ blocking rule │
│ with safe cutover            │ ───────────────────────────────────  │               │
│                              │ Input chips                          │ Linked later  │
│ Success condition            │ [Clinical safety board] [eRx]        │ in Model and  │
│ No care disruption           │ [Certification] [No dual mode]       │ Explore       │
│                              │ [Mixed-mode]                         │               │
│                              │ Button: + Add element                │               │
├──────────────────────────────┼──────────────────────────────────────┤               │
│ FILLED CARD                  │ FILLED CARD                          │               │
│ Actors                       │ Objectives                           │               │
│ ───────────────────────────  │ ───────────────────────────────────  │               │
│ List items                   │ List items                           │               │
│ • Hospital admin             │ • Reduce medication errors           │               │
│ • Clinical safety board      │ • Keep care running                  │               │
│ • Pharmacy                   │ • Preserve compliance                │               │
│ • IT vendor                  │                                      │               │
├──────────────────────────────┴──────────────────────────────────────┴───────────────┤
│ ACTION ROW: [Save draft] [Validate framing] [Continue to Model]                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Why this screen works

The user starts with **context, people, and intent**, not with formal logic. But the UI quietly turns prose into typed objects via chips and cards. Related information is grouped into obvious sections, which is exactly the kind of structure NN/g recommends for lowering form-related cognitive load. ([Nielsen Norman Group][3])

---

# 3) Screen B — Model lens

**Question the user is answering:** “How does this case actually work?”

```text
┌──────────────────────────────────────── MODEL ──────────────────────────────────────┐
│ Tabs: [Capabilities] [Dependencies] [Constraints] [States] [Transitions]            │
│ Search bar: Search objects...    Filter chips: [All] [Only missing links] [Blockers]│
├──────────────────────────────┬──────────────────────────────────────┬───────────────┤
│ LIST COLUMN                  │ MAIN MODEL PANE                      │ STANDARD SIDE │
│                              │                                      │ SHEET         │
│ Constraints                  │ OUTLINED CARD                        │ Inspector     │
│ ───────────────────────────  │ Selected object: q1 No dual mode     │ q1 No dual    │
│ > q1 No dual mode            │                                      │ mode          │
│   q2 Safety validation       │ Relation table                       │               │
│                              │ ┌────────┬──────────────┬──────────┐ │ Definition    │
│ Capabilities                 │ │ From   │ Relation     │ To       │ │ Mixed-mode    │
│ ───────────────────────────  │ ├────────┼──────────────┼──────────┤ │ prescribing   │
│   k1 Paper prescribing       │ │ q1     │ active in    │ s1 Mixed │ │ is not        │
│ > k2 ePrescribing            │ │ q1     │ blocks       │ τ1       │ │ allowed       │
│   k3 Barcode verification    │ │ k2     │ requires     │ d1 Cert  │ │               │
│                              │ │ k2     │ requires     │ d2 Intop │ │ Linked items  │
│ States                       │ └────────┴──────────────┴──────────┘ │ • τ1 blocked  │
│ ───────────────────────────  │                                      │ • s1 affected │
│   s0 Paper only              │ State cards                          │ • k2 affected │
│ > s1 Mixed-mode              │ [s0 Paper only] [s1 Mixed] [s2 Full] │               │
│   s2 Fully electronic        │                                      │ Missing info  │
│                              │ Transition cards                     │ • evidence for│
│ Transitions                  │ [τ1 introduce eRx] [τ2 remove paper] │   d1 in s0    │
│ ───────────────────────────  │ [τ3 direct cutover]                  │               │
│ > τ1 Introduce eRx           │                                      │ Assumption tag│
│   τ2 Remove paper            │                                      │ [estimated]   │
│   τ3 Direct cutover          │                                      │               │
├──────────────────────────────┴──────────────────────────────────────┴───────────────┤
│ STANDARD BOTTOM SHEET: Validation                                                   │
│ • τ1 creates mixed-mode and conflicts with q1                                       │
│ • τ3 still needs explicit evidence that d1 and d2 hold in s0                        │
│ Buttons: [Go to issue] [Mark as assumption] [Resolve now]                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Why this screen works

The left column is for **finding the thing**; the middle is for **seeing its structure**; the right is for **understanding what it means**. Search helps navigate large models; lists support scanning; cards keep single subjects understandable; chips support quick filtering; and the side sheet stays secondary rather than hijacking the main task. Material explicitly assigns those roles to these components. ([Material Design][4])

The bottom sheet is where issues live, not where primary editing happens. That keeps validation visible without breaking flow. Material defines bottom sheets as secondary content anchored to the bottom of the screen, which is exactly the right job here. ([Material Design][5])

---

# 4) Screen C — Explore lens

**Question the user is answering:** “What paths are possible, and why?”

```text
┌─────────────────────────────────────── EXPLORE ─────────────────────────────────────┐
│ Tabs: [Alternatives] [Compare] [Rationale]                                          │
│ Filter chips: [All] [Admissible] [Blocked] [High coordination]                      │
├──────────────────────────────┬──────────────────────────────────────┬───────────────┤
│ ALTERNATIVE LIST             │ SELECTED ALTERNATIVE                 │ STANDARD SIDE │
│                              │                                      │ SHEET         │
│ > Alternative A              │ SUMMARY CARDS                        │ Rationale     │
│   Phased rollout             │ [Admissible: No] [Risk: High]        │               │
│   Status chip: [Blocked]     │ [Actors involved: 4] [Deps unmet:1]  │ Selected alt  │
│                              │                                      │ Alternative A │
│   Alternative B              │ Path list                            │               │
│   Direct cutover             │ s0 Paper only                        │ Why blocked   │
│   Status chip: [Admissible]  │ ↓ τ1 Introduce eRx                   │ q1 No dual    │
│                              │ s1 Mixed-mode                        │ mode is active│
│   Alternative C              │ ↓ τ2 Remove paper                    │ in s1, so the │
│   Defer                      │ s2 Fully electronic                  │ phased path is│
│   Status chip: [Admissible]  │                                      │ inadmissible  │
│                              │ COMPARISON TABLE                     │               │
│                              │ ┌────────────────────┬──────┬──────┐ │ Linked object │
│                              │ │ Criterion          │ A    │ B    │ │ q1 No dual    │
│                              │ ├────────────────────┼──────┼──────┤ │ mode          │
│                              │ │ Constraint pass    │ No   │ Yes  │ │               │
│                              │ │ Dependency complete│ Part │ Yes  │ │ Action        │
│                              │ │ Boundary friction  │ Low  │ Med  │ │ [Go to Model] │
│                              │ └────────────────────┴──────┴──────┘ │               │
├──────────────────────────────┴──────────────────────────────────────┴───────────────┤
│ ACTION ROW: [Refine model] [Keep Alternative B] [Generate brief] [Export]           │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Why this screen works

The Explore lens is not a separate “dashboard.” It is the same workspace, now focused on alternatives. The user sees alternatives as cards, compares them in a table, and inspects one rationale in the same right-side inspector. The product is still telling one story: **this object, this structure, this consequence**.

That coherence matters because users perform better when interfaces build on stable mental models and offload memory demands instead of forcing recall. ([Nielsen Norman Group][2])

---

# 5) The cross-lens coherence pattern

This is the part that prevents confusion.

The same object stays visible across all three lenses.

```text
SELECTED OBJECT: q1 "No dual mode"

FRAME
  appears as:
  - input chip in Key elements
  - short explanation in side sheet

MODEL
  appears as:
  - constraint list item
  - relation table source
  - linked blocker in side sheet

EXPLORE
  appears as:
  - rationale for blocked alternative
  - "Go to Model" recovery action
  - same name, same icon, same color, same side-sheet structure
```

That means the user never has to ask:

* “Is this the same thing?”
* “Where did it go?”
* “Why is this called something different here?”

They always know.

---

# 6) The journey through the workspace

```text
┌────────────┐      ┌────────────┐      ┌──────────────┐      ┌───────────────┐
│ FRAME      │ ---> │ MODEL      │ ---> │ EXPLORE      │ ---> │ SELECT /      │
│ define case│      │ structure  │      │ compare paths│      │ EXPORT BRIEF  │
└─────┬──────┘      └─────┬──────┘      └──────┬───────┘      └───────────────┘
      │                   │                    │
      │                   │ blocked alt        │
      │                   └────────<───────────┘
      │                        refine in context/model without losing selection
      │
      └────────────── user can return at any time; shell never changes ───────────────┘
```

## Unlock logic

```text
Frame → Model unlocks when:
- title exists
- at least one actor
- at least one objective
- current and desired situation are clear enough

Model → Explore unlocks when:
- at least one state
- at least one transition
- changed capabilities are assigned
- major missing links are resolved or explicitly marked as assumptions

Explore → Export unlocks when:
- at least one admissible or intentionally deferred alternative exists
```

This fits NN/g’s recommendations for structure, transparency, and support: users see where they are, what remains, and what is blocking progress. ([Nielsen Norman Group][3])

---

# 7) Invariants across screens

```text
Fixed across all screens:
- top app bar position and action order
- drawer destinations and labels
- inspector layout
- issue tray location
- object naming
- object iconography
- status chip meanings
```

```text
Allowed to change by lens:
- tabs
- main content layout
- primary button label
- what the middle pane emphasizes
```

That balance gives the user **variation in task**, but **stability in interaction**.

---

# 8) The single most important design decision

Do **not** let the product feel like:

* a wizard in Frame,
* a database in Model,
* and a dashboard in Explore.

It should feel like **one case workspace** with three lenses:

```text
Frame   = define the case
Model   = structure the case
Explore = reason over the case
```

### `Review`

Inspect:

- accepted model state
- analysis receipts
- recommendation receipts

### `Publication`

Consume only:

- approved typed constructs
- approved typed paths
- approved evaluation receipts

The implementation rule is:

- keep workstation phase navigation for `Gather`, `Itemize`, `Draft`, `Review`, and `Publication`
- use DST lens controls only inside the DST-capable workbench
- keep one persistent inspector, one selection model, and one visible status model across those lenses

## Recommendation

DST should adopt this rule:

- `reduce_not` is the primary discovery engine for candidate solutions
- the typed DST normalization contract is the primary normalization layer
- `coordinated_transformation` is the primary formal evaluation layer
- the workstation should expose this through one case workspace with stable `Frame | Model | Explore` lenses, not a second tool

That is the cleanest way to stay faithful to:

- governed refinement in `THEORY.md`
- strict normalization in `src/dst/DST_PROMPT.md`
- formal analysis in [COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md](../coordinated_transformation/COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md)

## External References

These are repo-wide references that sit outside `dst` and `coordinated_transformation`:

- `THEORY.md`
- `DECISION_REVIEW.md`
- `PUBLICATION.md`
- `src/dst/DST_PROMPT.md`
- `src/dst/tests/fixtures/dst`
