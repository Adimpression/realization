# Research And Publish Flow Implementation

Implementation tracker for the workstation subject workflow that now spans:

- `Gather`
- `Itemize`
- `Draft`
- `Review`
- `Publication`

The wider workstation shell also includes:

- `Chat`
- `Permissions`
- `Activity`
- `Skills`

This file tracks only the five-phase subject workflow inside that wider shell.

This file tracks:

- what is already live in code
- what is only partially surfaced in the UI
- what must change to reach the target ideal flow

## Current Code Anchors

Primary modules:

- [workstation/chat_ui.py](workstation/chat_ui.py)
- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [workstation/subject_workflow_state_transitions.py](workstation/subject_workflow_state_transitions.py)
- [itemize.py](itemize.py)
- [review_composition.py](review_composition.py)
- [decision_review.py](decision_review.py)
- [publication_projection.py](publication_projection.py)
- [publication_render.py](publication_render.py)
- [publication_validation.py](publication_validation.py)
- [publication.py](publication.py)
- [tests/test_subject_workflow.py](tests/test_subject_workflow.py)
- [tests/test_workstation_chat_ui.py](tests/test_workstation_chat_ui.py)

## What Is Already Implemented

### Live subject discovery and gather admission

Implemented in [workstation/subject_workflow.py](workstation/subject_workflow.py):

- subject scenarios are loaded from real `LearningContext` material
- source counts, delta counts, unit counts, and applied-delta counts are surfaced
- maintained subject projection summaries are surfaced
- markdown ingress and URL ingress are wired into the live corpus workflow
- governed assistant-message capture into gather admission is live
- subject activation and maintained-file comparison are live

### Live itemization

Implemented across:

- [itemize.py](itemize.py)
- [itemize_validation.py](subject_core/src/workstation/subject/core/itemize_validation.py)
- [workstation/subject_workflow.py](workstation/subject_workflow.py)

This includes:

- persisted `ItemizationSession`
- deterministic candidate extraction
- promote/reject/restore
- split/merge/hold flows
- decision-role candidate assignment
- workstation `Itemize` tab integration

### Live draft composition

Implemented across:

- [review_composition.py](review_composition.py)
- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [publication_projection.py](publication_projection.py)

This includes:

- persisted `ReviewComposition` and `ReviewItem`
- composition seeding from current non-rejected itemized candidates
- semantic/render/evidence/transform orientation
- child split, sibling merge, and child-to-root promotion
- transform receipts
- report-plan shaping over review-owned structure

### Live review gate

Implemented in [workstation/subject_workflow.py](workstation/subject_workflow.py):

- maintained `subject.md` / `subject.typ` comparison
- alignment or drift verdict
- report-plan approval gate
- review blocking unless maintained files align and the draft is current

### Live publication build

Implemented in:

- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [publication_projection.py](publication_projection.py)
- [publication_render.py](publication_render.py)
- [publication_validation.py](publication_validation.py)
- [publication.py](publication.py)

This includes:

- locking publication inputs
- requiring an approved current composition before lock/build
- building one `publication_type = report`
- validating the publication graph
- rendering markdown
- rendering Typst
- attempting Typst compile to PDF
- persisting publication/build/artifact records
- opening release packet and output previews

### Live Textual semantics

Implemented in:

- [workstation/chat_ui.py](workstation/chat_ui.py)

This includes:

- shared subject-workflow semantics
- shared prompt-target chat semantics
- gRPC-backed workflow routing so shell affordances stay separate from workflow authority

### Live URL ingress and durable source bundles

Implemented through the current URL-learning path:

- entering one URL from `Gather`
- browser-backed or fallback capture
- persistence as one admitted `LearningSource`
- persistence of richer source-bundle artifacts such as:
  - `rendered.html`
  - `screenshot.png`
  - `elements.json`
  - `asset-manifest.json`

This means URL-origin fetched material is already durable and inspectable on disk.

What is not yet live is the stronger source-workbench shape around it:

- source-first staging before admission
- source-specific chat over selected saved sources
- source revision management beyond the first curation slice
- source merge-back proposals

## What Is Not Yet Correct

### Gather is not yet a full intake orchestration workbench

The assistant-capture bridge and ingress actions are live, but `Gather` still does not yet provide the full intended source workbench:

- richer source queue management
- fuller source observation actions
- broader multi-source intake orchestration
- richer topic/query collections and saved queries
- broader LLM/manual source curation loops that remain source-layer work
- explicit source import and source merge-back proposal handling
- explicit `Gather <-> Chat` routing for source discovery and curation beyond the current selected-source and selected-source-set curation paths
- a first-class saved-source browser over refresh/curation history and richer selected source-set management

### Shared neutral layout metadata is incomplete

[workstation/layout.py](workstation/layout.py) still models only the coarser shell/tab set and does not yet explicitly represent the live `Itemize` and `Draft` phases.

### Publication preview surface is still incomplete

The publication build writes:

- `report.md`
- `report.typ`
- `report.pdf`

But Typst is still not exposed as a fully first-class publication preview path in the same way markdown and PDF are.

### Some shell naming remains misleading

[workstation/chat_ui.py](workstation/chat_ui.py) still contains stale local alias names from the older mock/trail era.

## Target Implementation Shape

The shells should remain phase-oriented, but the user flow should now be described accurately:

### Gather

Purpose:

- discover, save, observe, refresh, and curate sources before corpus admission
- keep a staged source knowledgebase linked to the active subject
- resolve or choose subject identity
- run explicit governed source import into corpus when the operator is ready

Required live additions:

- richer source collections organized by topic/query and saved query state
- source records and source revisions that stay outside `LearningContext` until explicit import
- source observation and refresh receipts
- source curation through:
  - `Chat` with gather-scoped prompt targets
  - manual editing
- explicit import actions that create admitted `LearningSource`
- explicit merge-back/diff proposals from corpus/intermediate work into staged source notes
- broader intake orchestration beyond one markdown or last assistant message
- source inspection actions such as:
  - open source markdown
  - open rendered capture
  - open screenshot
  - open asset/source metadata
  - open one selected saved source set in gather-scoped chat

Current first-cut reality:

- one default per-subject source set: `All Gather Sources`
- first operator-managed selected source sets on top of that default set
- source-set metadata curation through `@llm` and `=`
- one first saved-query discovery path:
  - `Find Sources In Chat`
  - `Apply Discovered Sources`
  - `Discard Discovered Sources`
- one first staged-source refresh path:
  - `Refresh Selected Source`
  - one new staged `refresh` revision over the selected URL-backed staged source
- one first source-set sync path:
  - `Sync Source Set`
  - batch URL refresh over the selected source set's URL-backed staged sources
- one first selected-source merge-back path:
  - `Merge Back In Chat`
  - `Apply Merge-Back Proposal`
  - `Discard Merge-Back Proposal`
- one first selected source-set merge-back path:
  - `Merge Source Set In Chat`
  - `Apply Source-Set Merge-Back`
  - `Discard Source-Set Merge-Back`
- selected staged-source detail now shows revision history and a latest-change summary against the previous revision when one exists
- `Change Diff Baseline (...)` now lets operators compare the selected staged source against older revisions
- selected staged-source detail now shows a first deterministic `Export proposal preview` from current governed learnings without auto-applying a merge
- selected source-set detail now shows a first deterministic `Source-set export preview` from current governed learnings without auto-applying a merge
- discovery stays at the source layer and does not auto-import into `LearningContext`

Suggested first-cut staged source model:

- `SourceCollection`
  - one topic/query-oriented source set for the active subject
- `StagedSource`
  - one saved source record that is still only a source, not yet corpus
- `SourceRevision`
  - one captured or edited revision of that staged source
- `SourceCurationReceipt`
  - one LLM/manual/source-refresh action over a staged source
- `SourceImportProposal`
  - one explicit proposal to admit a staged source into `LearningContext`
- `SourceMergeProposal`
  - one diff/merge-style proposal to project corpus/intermediate learnings back into staged source notes

Suggested persistence shape:

- `corpus/<subject>/gather/collections/<collection-id>.json`
- `corpus/<subject>/gather/sources/<source-id>.json`
- `corpus/<subject>/gather/revisions/<revision-id>.json`
- `corpus/<subject>/gather/revisions/<revision-id>.md`
- `corpus/<subject>/gather/bundles/<revision-id>/...`
- `corpus/<subject>/gather/receipts/<receipt-id>.json`
- `corpus/<subject>/gather/imports/<proposal-id>.json`
- `corpus/<subject>/gather/merges/<proposal-id>.json`

This keeps the source layer explicit and durable without pretending it has already become corpus truth.

### Itemize

Purpose:

- turn admitted subject material into a governed typed inventory

Required live additions:

- filtering by item kind and confidence
- alias and canonical-label editing
- direct source-basis opening from item records

### Draft

Purpose:

- own composition structure and orientation before approval

Required live additions:

- deeper block/section composition control
- richer figure/table/diagram specialization
- stronger decision handoff surfaces

### Review

Purpose:

- remain the maintained-truth and approval gate

Required live additions:

- better approval history/diff visibility
- stronger artifact preview history

### Publication

Purpose:

- remain a build/release workflow over approved draft/review state

Required live additions:

- fuller Typst preview
- history/diff/release review surfaces

## Recommended Sequence

### 1. Widen the neutral layout substrate

In [workstation/layout.py](workstation/layout.py):

- represent `Gather`, `Itemize`, `Draft`, `Review`, and `Publication` explicitly
- keep pane semantics converged across hosts

### 2. Remove stale naming and copy

In the workstation hosts:

- remove stale mock/trail local names
- keep workflow copy aligned with the live five-phase subject workflow

### 3. Deepen gather intake

In [workstation/subject_workflow.py](workstation/subject_workflow.py):

- widen source observation
- widen staged intake state
- add staged source collections and source revisions
- add gather-scoped chat entry points for source discovery and curation
- keep saved sources distinct from admitted corpus sources
- add explicit source import and broaden the first merge-back proposal/history/baseline/export-preview/member-history flow into deterministic multi-source export application, broader export-history browsing, first aligned/changed/pending/cleared export-state comparison, first actionable per-member export browsing, and richer multi-source diff/export control
- add explicit prompt-target routing between:
  - general `Chat`
  - gather-scoped source discovery
  - gather-scoped source curation
- keep admission explicitly governed

### 4. Keep Review as the governance gate

Do not weaken review by letting publication bypass:

- maintained projection comparison
- draft/report-plan approval

### 5. Deepen publication preview/history later

After the flow is stable:

- add Typst preview parity
- add build history
- add output diff/review

## Immediate Tracker

- [x] live subject scenario discovery from `LearningContext`
- [x] live gather ingress and governed chat-backed intake
- [x] live itemization layer
- [x] live draft composition layer
- [x] live review gate over maintained projections
- [x] live report publication build from approved draft/review state
- [x] persisted publication tree and output artifacts
- [x] Textual shell connected to the live subject workflow module
- [x] Flutter migration target defined against the same live subject workflow semantics, with Textual kept as the reference client during convergence
- [ ] widen the neutral layout substrate to the full five-phase subject workflow
- [ ] remove stale local alias naming in the shells
- [ ] expose Typst as a first-class publication preview
- [ ] make Gather a richer governed intake workbench
- [ ] later add build history and diff/review workflow

## Working Rule

The critical rule for implementation is:

- gather creates or admits subject change
- itemize normalizes that admitted material
- draft shapes report structure and decision handoff
- review gates maintained truth and approved draft state
- publication projects that approved state

Do not let the shell collapse those layers back into one undifferentiated action surface.
