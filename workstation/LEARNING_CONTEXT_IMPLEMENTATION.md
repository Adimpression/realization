# Learning Context Implementation

Implementation tracker for [LEARNING_CONTEXT.md](LEARNING_CONTEXT.md).

This tracker follows the same rule as the other implementation files:

- track the live execution plan
- keep progress current against the theory doc
- prefer narrow substrate cuts before higher-level UI or capability work

## Current Position

The theory is sound.

The first correct cut is Phase 1 substrate only:

- persistent `LearningContext`
- persistent `LearningDelta`
- deterministic corpus-home layout

Not yet in scope for the first cut:

- workstation `ws.learning.*` capabilities
- skill regeneration from context
- publication builds

## Phase 1

- [x] add canonical `LearningUnit`, `LearningDelta`, and `LearningContext` records
- [x] add canonical `LearningSource` records for corpus-side source provenance
- [x] add deterministic `corpus/<subject-id>/...` home layout helpers
- [x] persist `context.json` and `deltas/<delta-id>.json`
- [x] persist `sources/<source-id>.json` plus markdown source bodies under `sources/<source-id>.md`
- [x] persist deterministic alias and unit indexes under `indexes/`
- [x] add deterministic delta application against one subject context
- [x] add seam-level tests for round-trip persistence, listing, and delta application

Implemented in:

- [learning_context.py](learning_context.py)
- [tests/test_learning_context.py](tests/test_learning_context.py)

## Remaining Work

- [ ] add a staged source layer before `LearningContext` admission:
  - persist saved source records, query/topic collections, and richer source revisions under a gather-owned source workbench
  - keep these staged sources distinct from admitted `LearningSource`
  - allow chat- and URL-origin source work to remain source-only until explicit import
- [x] add the first explicit import path from staged source records into admitted `LearningSource` records
- [ ] widen the first governed merge-back proposal path plus first staged-source history/diff inspection, baseline browsing, and deterministic export-preview path into fuller diff/merge-style export from corpus/intermediate work back into staged source notes with reference linkage instead of direct overwrite
- [x] finish routing markdown/chat learning toward `source -> delta -> learning context`; external markdown learning now persists source records, emits one applied delta, updates one subject context, honors explicit subject metadata, and reuses one existing context on deterministic exact alias/title matches, while chat-originated “save learnings” workstation flows now persist chat source records, applied deltas, and merged subject contexts through one prompt-scoped post-turn capture hook
- [x] add subject document projection scaffolding for `subject.typ` and optional `subject.md`; persisted contexts now deterministically materialize grouped Typst and markdown subject documents with stable section anchors from one authoritative `LearningContext`
- [x] regenerate skill projections from context-linked units through the canonical skill path; persisted contexts now regenerate corpus-admitted linked units into canonical portable skill YAML under `derived/skills/` by compiling projected skill documents through the v2 skill compiler and exporting them back through the standard skill export path; materialization does not perform governed skill installation or supply host realization
- [x] make delta operator intent explicit inside `LearningDelta`; the substrate now supports explicit `initiate`, `append`, `replace`, `remove`, and `improve` updates plus structural `link`, `split`, `merge`, `reject`, and `restore` operators, while keeping legacy additive deltas compatible when `operations` is absent, and the live markdown/chat learning producers now emit explicit `initiate` operations instead of relying on implicit upsert semantics
- [x] add seam-level unit tests for delta operator semantics so learning mutation rules stay stable without depending on long controller-path regressions
- [ ] introduce higher-level workstation learning actions only after the substrate above is real
- [ ] add typed learning cross-reference management between units, sources, and projections

## Notes

- The recommended capability family in [LEARNING_CONTEXT.md](LEARNING_CONTEXT.md) should be treated as a later surface, not the first implementation step.
- Phase 1 is intentionally storage- and identity-first so subject memory does not depend on markdown append flows or prompt-local file operations.
- Chat-originated learning currently enters `LearningContext` through prompt-scoped workstation capture of successful `ws.markdown.create` and `ws.markdown.append` “save learnings” turns; raw markdown write capabilities remain non-semantic leaf tools outside that prompt path.
- Explicit delta operators now make update intent part of the persisted substrate rather than leaving “append vs replace vs remove” to be reconstructed from controller behavior after the fact.
- `LearningSource` should remain the admitted corpus provenance object.
- Saved-but-not-admitted source records should live in the future gather source workbench, not inside `LearningContext` as if they were already corpus truth.
- Current implementation reality:
  - URL ingress now creates staged source records in Gather first
  - explicit import is now what creates admitted `LearningSource`
  - Gather now persists:
    - the default source collection per subject: `All Gather Sources`
    - the first operator-managed selected source sets
    - staged-source `llm_curation` and `manual_curation` revisions
    - staged-source `refresh` revisions for URL-backed staged sources
    - staged-source `merge` revisions for the first selected-source merge-back proposal path
    - selected staged-source revision history and latest-change summaries in the Gather detail pane
    - selected staged-source diff baseline browsing in the Gather detail pane
    - selected staged-source deterministic export proposal preview in the Gather detail pane
    - selected source-set sync metadata for batch URL refresh over staged sources
    - selected source-set metadata curation through LLM/manual apply-back paths
    - the first selected source-set discovery path, which can stage new source records or link existing ones back into the selected set without admitting them into corpus
    - the first selected source-set merge-back path, which can apply current subject learnings back into `SourceCollection` metadata without admitting them into corpus
    - the first deterministic selected source-set export proposal preview in the Gather detail pane
  - the next source-workbench cut should widen beyond those first collection/discovery/curation/refresh/sync/merge/history/baseline/export-preview/member-history paths into fuller multi-source diff/export proposal application plus broader export-history browsing
