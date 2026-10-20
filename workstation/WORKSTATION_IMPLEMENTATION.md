# Workstation Implementation

Implementation tracker for the current workstation direction.

This file is intentionally concrete.

It tracks:

- what the workstation already is
- which parts are legacy
- what the current subject workflow actually looks like
- where Textual is already mature and Flutter is converging
- and what still needs widening

## Current Position

The workstation is already beyond “one shell”.

Implemented substrate:

- host-owned workstation core/service boundary
- first shell projection backend for non-subject surfaces
- neutral projection models
- workstation-local event bus and subscriber controllers
- Textual-first terminal projection
- Flutter projection
- shared palette/theme substrate for both UIs
- shared subject-workflow module and state-transition module
- subject-workflow gRPC/Protobuf API boundary with in-process client/backend use in Textual
- first subject-workflow repository seam for persistence

Implemented user-facing shell tabs:

- Chat
- Gather
- Itemize
- Draft
- Review
- Publication
- Permissions
- Activity
- Skills

## Direct LLM Decomposition Policy

For weakly structured prose, the workstation now treats direct LLM decomposition as an `Itemize` policy, not a `Gather` policy.

Rules:

- `Gather` still stores sources and admits corpus material without making `reduce_not` the admission engine
- `Itemize` may run bounded direct `reduce_not`-style decomposition over selected raw prose chunks or source snapshots
- that decomposition yields candidate itemized material only
- it does not rewrite the source, auto-admit new corpus truth, or generate publication prose

Launch control:

- workstation launch defaults to allowing direct LLM decomposition
- explicit flag: `--allow-direct-llm-decomposition`
- explicit opt-out: `--no-allow-direct-llm-decomposition`

Implementation rule:

- the launch policy is persisted in the workstation session contract and read back by subject-workflow itemization actions
- deterministic extraction still remains the non-LLM fallback path and merge source for stable markdown-derived slices

Important nuance:

- the user-facing five-phase subject workflow is live
- the neutral layout substrate now models `Gather`, `Itemize`, `Draft`, `Review`, and `Publication` explicitly
- the remaining layout gap is now in finer workbench metadata, not missing phase tabs

## Legacy Clarification

`Learn Markdown` is still valid code, but it is now legacy product shape.

It still proves:

- non-chat workstation actions
- progress/result panes
- bridge into governed markdown learning

But conceptually it is only one ingress capability inside `Gather`.

It does not define the workstation learning story anymore.

## Current Subject Workflow

The current user-facing subject workflow is:

`Gather -> Itemize -> Draft -> Review -> Publication`

Ownership of each phase:

- `Gather`
  - ingest/admit source material into `LearningContext`
  - activate the subject
  - compare maintained files when needed
  - stage imports and intake
  - this is also the intended future home of a staged source knowledgebase that exists before corpus admission
- `Itemize`
  - generate and refine typed normalized candidates from admitted material
- `Draft`
  - own composition structure and orientation over itemized material
  - shape report scope and decision handoff
- `Review`
  - remain the explicit approval/sign-off gate
  - compare maintained projections
  - approve the draft/report plan
- `Publication`
  - lock approved inputs
  - build, validate, preview, and release

## What Is Already Live

The workstation already has:

- live corpus-backed subject discovery
- governed gather admission from markdown, URL, and chat-originated material
- persisted `ItemizationSession` and `ItemizedSubjectItem` handling
- persisted `ReviewComposition` and `ReviewItem` handling
- child split / merge / root-promotion in `Draft`
- report-plan shaping and approval
- maintained `subject.md` / `subject.typ` comparison
- report publication build/review/release
- decision-review substrate with persisted frames, items, policy profiles, and receipts
- widened publication outputs for decision summary, matrices, checklists, roadmap, diagram, and recommendation receipt
- a live transport-ready backend seam for subject workflows:
  - [workstation/protos/subject_workflow.proto](workstation/protos/subject_workflow.proto)
  - [workstation/subject_workflow_api.py](workstation/subject_workflow_api.py)
  - [workstation/subject_workflow_client.py](workstation/subject_workflow_client.py)
  - [workstation/subject_workflow_textual_backend.py](workstation/subject_workflow_textual_backend.py)
  - [workstation/subject_workflow_grpc.py](workstation/subject_workflow_grpc.py)

## Decision-Analysis Recovery Rule

Decision analysis must remain recoverable across same-subject imports and later-phase navigation.

The implemented recovery precedence is:

- if no decision frame exists: `Start Decision Analysis`
- if a decision frame exists and is current: `Run Decision Analysis`
- if a later same-subject import invalidates an older DST-backed frame: `Refresh DST Analysis`

Additional rules:

- a `blocked` decision-analysis receipt must not strand the subject in later phases
- `Review` and `Publication` must surface the Draft recovery path instead of surfacing later-phase approval/build actions as if the attached analysis were healthy
- `Current Step -> Actions` stays selective, but one recovery/progression action must remain available for decision-analysis-eligible subjects

## Shared Convergence Rule

Do not let Flutter and Textual invent separate meanings for the new surfaces.

Keep convergence through:

- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [workstation/subject_workflow_state_transitions.py](workstation/subject_workflow_state_transitions.py)
- [workstation/colors.py](workstation/colors.py)
- [workstation/theme.py](workstation/theme.py)
- the shared workstation core/projection seam

The renderers may differ in mechanics.

They should not differ in:

- tab meaning
- pane meaning
- workflow semantics
- prompt-target behavior

## Current Gaps

The main remaining workstation gaps are now narrower:

### 1. Shared layout metadata is still coarser than the live workbenches

[workstation/layout.py](workstation/layout.py) now models the real subject-workflow phase tabs, but it still does not capture the deeper pane/workbench semantics that the live Textual shell is already using inside those tabs.

### 2. Textual/Flutter parity is still uneven

The deeper subject-workflow interactions exist first in Textual.

Flutter is converged in broad semantics, but not yet at the same interaction depth for:

- item inventory editing
- draft shaping interactions
- some preview/maximize flows

### 3. Some shell naming and copy are still legacy

The repo still contains leftover `mock_*` names and older doc/copy trails in places even though the flow is live.

### 4. Publication preview surface is still narrower than the artifact set

The build writes:

- `report.md`
- `report.typ`
- `report.pdf`

The user-facing preview surface still needs fuller first-class Typst exposure and better artifact history/diff workflows.

### 5. Gather and Chat are only partially integrated around staged source work

The current flow can ingest from markdown, URL, and chat. URL ingress and Gather chat capture now stage source material in Gather first, and explicit import is what admits that staged source into `LearningContext`.

What is now live:

- staged URL source capture in Gather
- explicit import from a selected/latest staged source into `LearningContext`
- a selectable staged-source inventory in `Gather`
- a selected-source detail pane in `Gather`
- a default per-subject source set: `All Gather Sources`
- first operator-managed selected source sets on top of that default set
- a first selected-source `@llm` curation entry point that stays at the source layer
- explicit `Apply LLM Curation` / `Discard LLM Curation` back into staged `SourceRevision` state
- explicit `Merge Back In Chat` / `Apply Merge-Back Proposal` / `Discard Merge-Back Proposal` for one selected staged source using current subject learnings while staying at the source layer
- selected source-set `@llm` curation and manual source-set curation that update `SourceCollection` metadata only
- first saved-query source discovery for the selected operator-managed source set through gather-scoped chat
- explicit `Apply Discovered Sources` / `Discard Discovered Sources` back into staged source records without corpus admission
- explicit `Merge Source Set In Chat` / `Apply Source-Set Merge-Back` / `Discard Source-Set Merge-Back` for one selected operator-managed source set using current subject learnings while staying at the source layer
- staged-source URL refresh through `Refresh Selected Source`, which writes a new staged `refresh` revision without corpus admission
- source-set URL sync through `Sync Source Set`, which batch-refreshes the selected set's URL-backed staged sources and records set-level sync metadata without corpus admission
- first selected-source revision inspection in Gather:
  - `Revision history` and `Latest change summary` now render as `DataTable` surfaces below the selected-source detail pane
  - `Change Diff Baseline (...)` updates the selected-source tables and the baseline preview together
- first deterministic selected-source export preview in Gather:
  - `Export proposal preview` now shows likely source-layer additions derived from current summary, items, itemized candidates, and draft emphasis without auto-applying a merge
- first deterministic selected source-set export preview in Gather:
  - `Source-set export preview` now shows likely source-set metadata additions derived from current summary, items, itemized candidates, and draft emphasis without auto-applying a merge
- first selected source-set member revision/history browsing in Gather:
  - `Member export status`, `Member revision history`, `Merge/export history`, `Actionable export targets`, and `Export-applied targets` now render as `DataTable` surfaces
  - the selected source-set detail pane keeps the explanation/proposal layer, while table surfaces carry the history and export-state browsing
- first deterministic selected-source export application in Gather:
  - `Apply Selected Source Export Preview` now applies the current selected-source export preview as a staged `merge` revision
  - that revision remains source-only and does not auto-import into `LearningContext`
- first deterministic multi-source export application in Gather:
  - `Apply Set Export Preview` now applies the current per-member export targets as staged `merge` revisions
  - those revisions remain source-only and do not auto-import into `LearningContext`

The first full staged-source workbench slice is now live:

- operator-managed source sets on top of `All Gather Sources`
- topic/query source-set creation from explicit chat or command input
- saved-query-aware set selection
- source-set synthesis into maintained summary, open questions, and query/topic metadata without corpus admission
- selected-source refresh, diff baseline, revision history, and change summary
- selected-source export preview and export-preview application
- selected source-set discovery, sync, metadata curation, source merge-back, set-source merge-back, export preview, export-preview application, member revision browsing, member export-state browsing, actionable export browsing, and export-applied browsing
- gather-scoped chat routing into those same staged-source and source-set operations without implicit corpus admission

What remains is the broader knowledgebase/product layer above that workbench:

- richer multi-query collections and saved-search management beyond the current operator-managed source-set model
- broader multi-set and multi-source comparison flows beyond the current selected-source and selected-source-set paths
- fuller source curation history and merge-back handling that remains source-only
- broader topic/query knowledgebase navigation, cross-set synthesis, and multi-set summary maintenance over staged sources

Execution order from here is now explicit:

1. broaden `Gather` into that broader topic/query knowledgebase
2. deepen `Gather <-> Chat` on top of that knowledgebase
3. then widen `Draft Model` so richer relation editing and lane-aware construct curation can directly reduce blocked decision-analysis and publication outcomes

### 6. The subject-workflow backend seam is live, but it is not yet the full workstation backend

What is now live:

- protobuf contract for:
  - subject listing
  - phase view projection
  - control bundle projection
  - pane bundle projection
  - workflow snapshot projection
  - action application
  - server-side workflow watch streaming
- plain Python subject-workflow service underneath that transport
- first repository seam under that service:
  - [workstation/subject_workflow_repository.py](workstation/subject_workflow_repository.py)
- in-process client/backend seam used by Textual:
  - [workstation/subject_workflow_client.py](workstation/subject_workflow_client.py)
  - [workstation/subject_workflow_textual_backend.py](workstation/subject_workflow_textual_backend.py)
- subject-tab refresh in Textual now uses the workflow watch stream as the main invalidation path instead of only manual refresh/coalescing
- in-process gRPC testing over the same subject-workflow logic
- first shell backend seam for non-subject surfaces:
  - [workstation/workstation_shell_backend.py](workstation/workstation_shell_backend.py)

What is still missing:

- widening watch-driven refresh beyond the current subject-tab path where it materially helps
- widening repository coverage beyond the current first subject-workflow repository seam
- widening the same API/backend discipline beyond the current shell projections and subject workflow where it pays off
- deciding whether Textual should keep the current in-process backend seam or switch to a gRPC client implementation behind the same client protocol

This is also where the current shell split is still too thin:

- `Chat` remains general and skill-capable
- `Gather` should own staged source state
- prompt-target routing between them is only first-cut so far

## Recommended Next Cuts

Recommended order:

1. deepen `Gather` beyond the current staged-source workbench into a broader topic/query knowledgebase:
   - keep the current staged-source and source-set layer as the operator workbench
   - widen into richer saved-query management, topic collections, and broader multi-source comparison/synthesis workflows on top of that workbench
   - keep staged sources distinct from admitted `LearningSource`
2. deepen `Gather <-> Chat` beyond the current selected-source and selected-source-set routing:
   - general chat stays general
   - gather-scoped prompt targets keep preferring source-discovery and source-curation work
   - widen from the current staged-source and source-set action routing into broader knowledgebase-oriented discovery, saved-query maintenance, and multi-source synthesis prompts
   - gather replies can continue to apply back into staged source records without implicit corpus admission
3. widen `Draft Model` after those `Gather` cuts:
   - broaden many-to-many relation editing
   - deepen lane-aware construct curation
   - make blocked decision-analysis outcomes more repairable before `Review` and `Publication`
4. widen the watch-stream refresh path:
   - keep the current subject-tab watch path
   - push the same pattern into other long-lived workstation surfaces only where it reduces UI lag
   - keep unary reads and unary commands as the base shape
5. widen the repository seam:
   - build on [workstation/subject_workflow_repository.py](workstation/subject_workflow_repository.py)
   - keep subject-workflow service logic from growing more file/store reach-through
   - isolate more subject progress, staged source, itemization, review, and publication persistence explicitly
6. widen the backend discipline beyond subject workflow where useful:
   - build on [workstation/workstation_shell_backend.py](workstation/workstation_shell_backend.py)
   - activity
   - permissions
   - skills
   - possibly selected workflow/operator surfaces
7. refine the shared neutral layout substrate from phase-tab coverage into deeper workbench metadata
8. keep carrying deeper live subject-workflow interactions across Flutter while preserving semantic parity
9. keep removing stale local naming and copy trails
10. deepen publication preview/history/diff without moving composition logic back into the shell
11. continue pushing high-level shell behavior toward reusable skills where appropriate

## Textual Widget Migration Plan

The workstation needs a careful Textual widget migration, but this should not be attempted as one large replacement of the current shell.

The goal is:

- better widget semantics
- no regression in workflow behavior
- no fork between Textual and Flutter semantics

### Migration Principles

1. [workstation/subject_workflow.py](workstation/subject_workflow.py) remains the semantic source of truth.
2. `chat_ui.py` should render richer controls, not invent new workstation logic.
3. The first slices should map widget changes back into the existing workflow actions instead of rewriting those actions.
4. Inventory and history surfaces should migrate only after the phase action row is stable.
5. Maximize behavior should use `ContentSwitcher` inside the active tab area, not overlay the phase tabs.
6. Widget labels and group titles must use plain user-facing language; do not leak internal terms such as `LearningContext`, `unit`, `construct`, or `binding` when a simpler surface label exists.

### Phase 1: Typed Phase Action Controls

This is the first implementation slice and the one that should go live first.

Scope:

- keep the existing phase action row in place
- replace cycle-style controls with `Select`
- replace true booleans with `Switch`
- keep real commands as `Button`

Wire-in steps:

1. Extend `SubjectActionSpec` so it can optionally describe:
   - control kind
   - control label
   - current value
   - allowed options
2. Add small helper types for control options in [workstation/subject_workflow.py](workstation/subject_workflow.py).
3. Decorate `subject_more_action_specs(...)` with widget metadata for the safest cases only:
   - `cycle_research_source_collection`
   - `cycle_research_source_revision_baseline`
   - `advance_import_selection`
   - `cycle_selected_itemized_item_decision_role`
   - `hold_selected_itemized_item`
   - `cycle_selected_draft_construct_sort`
   - `cycle_selected_draft_construct_lane`
   - `cycle_decision_policy_profile`
   - `cycle_selected_draft_review_semantic_kind`
   - `cycle_selected_draft_review_render_kind`
   - `cycle_selected_draft_review_evidence_mode`
   - `cycle_selected_draft_review_transform_mode`
   - `toggle_selected_report_scope_item`
   - `toggle_selected_composition_unit`
   - `cycle_publication_diff_baseline`
   - `cycle_composition_unit_target`
   - `cycle_publication_section_plan`
   - `cycle_publication_output_mode`
   - `cycle_publication_import_target`
   - `cycle_selected_publication_import_usage`
   - `toggle_selected_publication_import`
   - `toggle_selected_publication_section`
   - `toggle_selected_staged_source_in_collection`
4. In [workstation/chat_ui.py](workstation/chat_ui.py), replace the hardcoded four `Button` widgets per phase row with four stable slot containers.
5. During refresh, mount exactly one control per slot:
   - `Button`
   - `Select`
   - `Switch`
6. Map widget changes back to the existing workflow actions:
   - `Select` changes use the existing cycle or setter actions
   - `Switch` changes use the existing toggle action
7. Keep focus-order and keyboard traversal working when a slot now contains a `Select` or `Switch` instead of a `Button`.

Regression requirements:

- all existing phase action commands must still work
- a `Select` must show the current value, not just the available values
- disabled controls must stay visible only when the existing surface already depends on visible disabled state
- widget replacement must not change phase visibility, prompt targets, or selected-row semantics
- every migrated widget batch needs a Textual BDD test that changes the widget and verifies the backing workflow state, not only presence/visibility
- visible row order and keyboard focus order must match; for example Publication import target, include-import, and import-use controls stay adjacent before unit and section scope controls
- exact-value widgets must update the selected target represented by the visible widget; Publication `Use In Report` updates the currently selected support target, not whichever included support happens to be latest
- report-scope target widgets must keep the tree cursor and backing target cursor synchronized; selecting a Review/Publication unit or section target must move the corresponding report-scope row before any toggle runs
- grouped controls must make scope explicit; if nearby dropdowns act on different things, the UI should separate them under titles such as `Report Plan`, `Selected Item`, `Selected Section`, or `Selected Support`
- gate-bar actions that only navigate must render as navigation, not as command buttons; use simple labels such as `Review`, `Draft`, `Publication`, or `Open Model`, and reserve filled action buttons for state-changing work
- current-step actions must never render same-tab navigation; if an action belongs to the current tab it must normalize to a button, and phase-nav actions targeting the current tab are invalid

### Phase 2: Inventory Browsers

After the phase action row is stable:

- move flat inventories from `Log` to `OptionList`
- move hierarchical scope browsers from `Log` to `Tree`
- keep the same selection ids and detail-pane contracts underneath

Targets:

- Gather source inventories
- Itemize inventory
- Draft inventory
- Draft/Review report scope

### Phase 3: History And Diff Surfaces

After inventory selection is stable:

- move revision, diff, merge, export, and compare surfaces from prose summaries to `DataTable`
- retain the existing detail pane as the explanation layer

Textual status: complete.

Targets:

- staged-source revision history
- source-set merge/export history
- publication diff history
- compare/export status surfaces

### Phase 4: Help And Secondary Detail

After the main controls are stable:

- replace the current ad hoc info expansion behavior for short help surfaces with `Collapsible`
- keep detached/maximized pane behavior only for genuinely large reading surfaces

### Phase 5: In-Tab Maximize And Lens Switching

After the preceding phases are stable:

- move pane maximize/restore to `ContentSwitcher` inside the active tab body
- keep the phase tabs visible at all times
- replace any remaining fake lens buttons with actual nested tabs where the semantics are tab-like

Targets:

- Draft Model `Frame | Model | Explore`
- help/preview maximize within tab bodies
- later Flutter convergence on the same pane-role contract

## Suggested Core Additions

The next workstation cuts should likely add or widen higher-level core/projection functions such as:

- list subject contexts
- get one subject context summary/detail
- list recent deltas for one subject
- read maintained subject projections
- read itemization sessions and review compositions
- build one report publication from one subject context
- list prior publication builds for one subject
- list decision-review frames and receipts for one subject

These should remain:

- workstation-core and projection operations
- not shell-local formatting paths

## Immediate Tracker

- [x] projection split between workstation core and shell renderers
- [x] shared UI substrate for colors/theme roles
- [x] evented activity/projection invalidation
- [x] `LearningContext` substrate exists
- [x] `Publication` substrate exists
- [x] workstation subject browser/open surface
- [x] workstation `Gather -> Itemize -> Draft -> Review -> Publication` flow exists in Textual
- [x] workstation publication build/review surface exists
- [x] shared prompt-target chat semantics in Textual and Flutter
- [x] shell lifecycle hardening against destroyed-session background refresh/scroll tasks
- [ ] widen the shared neutral layout substrate to represent the full five-phase subject workflow explicitly
- [ ] carry the deeper live subject-workflow interactions across Flutter while keeping semantics converged
- [ ] expose Typst more fully as a first-class publication preview surface
- [ ] later add diff/review support for subject/publication revisions
