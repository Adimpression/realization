# Workstation

Formal position for the workstation as it exists today.

The workstation is no longer one terminal shell.

It is:

- one host-owned session/runtime boundary
- one capability and workflow surface
- one evented activity/receipt surface
- multiple UI projections over the same core

Current projections:

- [workstation/chat_ui.py](workstation/chat_ui.py): Textual-first terminal workstation, with prompt-toolkit retained as fallback
- [workstation/ui_flutter](workstation/ui_flutter): Flutter workstation shell over the same gRPC-backed workflow contract

Current core seams:

- [workstation/workstation_core.py](workstation/workstation_core.py)
- [workstation/workstation_shell_backend.py](workstation/workstation_shell_backend.py)
- [workstation/projection_models.py](workstation/projection_models.py)
- [workstation/subscriber_controllers.py](workstation/subscriber_controllers.py)
- [workstation/event_bus.py](workstation/event_bus.py)
- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [workstation/subject_workflow_state_transitions.py](workstation/subject_workflow_state_transitions.py)
- [workstation/subject_workflow_api.py](workstation/subject_workflow_api.py)
- [workstation/subject_workflow_repository.py](workstation/subject_workflow_repository.py)
- [workstation/subject_workflow_client.py](workstation/subject_workflow_client.py)
- [workstation/subject_workflow_textual_backend.py](workstation/subject_workflow_textual_backend.py)
- [workstation/subject_workflow_grpc.py](workstation/subject_workflow_grpc.py)
- [workstation/protos/subject_workflow.proto](workstation/protos/subject_workflow.proto)

Current shared UI substrate:

- [workstation/layout.py](workstation/layout.py): renderer-neutral tabs/panes/sizing hints
- [workstation/colors.py](workstation/colors.py): shared palette
- [workstation/theme.py](workstation/theme.py): shared UI semantic role mapping
- [DESIGN.md](../design/AXIOMATIC_SYSTEM_FOR_DESIGN.md): axiomatic design constraints for perceptual clarity, cognitive coherence, actionability, feedback, effort, and error

## Core Decision

The workstation should now be treated as:

`WorkstationCore + Subject Workflow + Projection Contracts + Host Event Bus + UI Projections`

not as:

`prompt_toolkit shell with some attached helpers`

This means:

- Textual is the reference projection while Flutter converges on the same contract
- receipts, workflows, permissions, skills, and approvals belong to the core
- layout/theme convergence should happen through shared substrate, not duplicated renderer logic
- workstation UI changes should be judged against [DESIGN.md](../design/AXIOMATIC_SYSTEM_FOR_DESIGN.md)

## API Boundary Rule

The workstation backend extraction direction is now explicit:

- the backend contract should use `gRPC + Protobuf`
- the first extracted API surface is the subject workflow
- the service should run in-process first and be tested that way
- transport should remain thin over the real workstation service logic

This means:

- Textual should not become the backend
- gRPC handlers should adapt structured workstation views and commands
- UI-specific widget concerns should stay out of the API contract
- the same service should remain callable directly from Python tests without network dependency

Current state:

- the subject workflow already has unary gRPC reads and commands for:
  - subject listing
  - phase view
  - control bundle
  - pane bundle
  - workflow snapshot
  - action application
- the subject workflow also already has a server-side streaming watch surface:
  - `WatchSubjectWorkflow`
- Textual subject tabs now use that watch stream as the primary invalidation/update path for active subject projections
- Textual currently uses an in-process backend/client seam:
  - [workstation/subject_workflow_client.py](workstation/subject_workflow_client.py)
  - [workstation/subject_workflow_textual_backend.py](workstation/subject_workflow_textual_backend.py)
- subject-workflow persistence now has a first explicit repository seam:
  - [workstation/subject_workflow_repository.py](workstation/subject_workflow_repository.py)
- non-subject shell projections now also have a first backend seam:
  - [workstation/workstation_shell_backend.py](workstation/workstation_shell_backend.py)
- bidi streaming is not required for the current workstation shape

Recommended transport posture:

- unary reads for snapshots and bundles
- unary commands for mutations
- server-side streaming for watch/update delivery
- bidi only if a later session protocol truly needs continuous client event streaming

## Chat And Governed Reduction Boundary

Workstation conversation remains host-owned. A normal prompt still follows the
existing shell, LLM, skill, and tool route; it does not enter the core reduction
loop implicitly.

The shared shell contract also exposes an explicit per-turn
`governed_reduction` route. That route crosses the typed
governed-turn extension to the `ControllerRuntimeProvider` seam, whose
implementation is registered only by the outer application composition root.
The extension is interface-segregated so existing providers remain valid until
that route is selected. Workstation packages do not import the core engine or
receive controller objects.

The four governed treatments are deliberately distinct:

- `independent` starts a new run
- `human_contribution` attaches only the selected message, with message and
  turn provenance, then resumes a paused or incomplete run
- `follow_up` starts a new linked run using only the committed prior result
- `correction` starts a new corrective run rather than reopening a closed run

Each new transcript record has a stable message ID, turn ID, and session-local
sequence position. Existing transcript rows without those additive fields
remain readable. `GOVERNED_TURNS.jsonl` binds Workstation turn/message IDs to
run IDs and checkpoint paths; `governed_reduction/states/` owns state JSON and
`governed_reduction/artifacts.sqlite3` owns reusable core artifacts. These
stores are correlated, not conflated.

The one-shot `workstation-prompt` CLI and the in-process/gRPC shell contract can
select this route explicitly. Textual and Flutter continue to submit normal
chat by default, preserving current behavior until a deliberate UX exposes the
mode.

## UI Hierarchy Rule

Workstation surfaces should be visually ordered as:

1. primary workflow guidance
   - current step
   - current phase status
   - next-step actions
2. active work surface
   - transcript
   - item inventory/detail
   - draft/review scope
3. supporting operational context
   - more actions
   - latest intake / learned snapshot / subject assets
   - permissions and activity detail
4. archival or status feedback
   - journal panes
   - receipts, history, and build/export tables

If two regions look equally important, the hierarchy is wrong.

## Current Step Actions Rule

`Current Step -> Actions` exists to encapsulate what the user can do next from the current workflow path.

Primary rules:

1. The section should show only the actions that are compatible with the current workflow state.
2. The section has exactly two action forms:
   - links
   - buttons
3. If the next compatible action belongs to the current tab, render it as a button.
4. Clicking a button should trigger the action immediately.
5. If the next compatible action belongs to another tab, render it as a link.
6. The link text should describe the action the user is going to reach there.
7. Clicking a link should navigate the user to that tab.
8. After navigation, the user should always see a button in that destination tab corresponding to the link text they just followed.
9. Ordering must reflect what the user should do next first, then what matters next after that.
10. The section should stay selective; do not stuff it with every available action.

Interpretation:

- buttons are for immediate in-place execution
- links are for guided movement to the tab where the action properly lives
- the row is ordered by workflow importance, not by implementation grouping or convenience

## What Exists Today

Today the workstation already supports:

- chat prompt execution over the workstation tool/capability surface
- prompt-target chat routing shared across the workstation shells
- skill discovery, description, import, export, invocation, and composition paths
- workflow discovery, inspection, rerun, and activity/timeline projection
- permission inspection and mutation
- receipt-backed and event-backed activity rendering
- subject-centered `Gather -> Itemize -> Draft -> Review -> Publication` workflow over the live corpus
- action-capable Textual and Flutter hosts over the same core seams
- shared palette and semantic UI roles across Textual and Flutter through [workstation/colors.py](workstation/colors.py) and [workstation/theme.py](workstation/theme.py)
- Flutter layout policy is still converging while Textual remains the reference shell

Important nuance:

- the user-facing subject workflow now has five explicit phases:
  - `Gather`
  - `Itemize`
  - `Draft`
  - `Review`
  - `Publication`
- the neutral layout substrate in [workstation/layout.py](workstation/layout.py) now models the explicit subject-workflow tabs, but its pane metadata is still coarser than some of the live Textual interactions inside those tabs

## Current Tabs

Current top-level workstation tab set in the user-facing shells:

- Chat
- Gather
- Itemize
- Draft
- Review
- Publication
- Permissions
- Activity
- Skills

The full phase semantics live in:

- [workstation/subject_workflow.py](workstation/subject_workflow.py)
- [workstation/subject_workflow_state_transitions.py](workstation/subject_workflow_state_transitions.py)

## Important Clarification About `Learn Markdown`

`Learn Markdown` should now be treated as:

- legacy ingress capability
- useful as proof that the workstation can host non-chat actions
- useful as a bridge into governed source-to-context learning
- not the workstation product concept itself

Its current implementation is still valid as one ingress action inside `Gather`:

- select markdown
- run workstation markdown learning
- admit learned output into the subject corpus

But that is not the long-term workstation mental model.

The actual theory direction of the repository is now:

`source -> learning context -> itemization -> draft composition -> review approval -> publication`

not:

`markdown file -> learned skill bundle -> done`

See:

- [LEARNING_CONTEXT.md](LEARNING_CONTEXT.md)
- [ITEMIZE.md](ITEMIZE.md)
- [REVIEW.md](REVIEW.md)
- [PUBLICATION.md](PUBLICATION.md)

## Workstation And DST

The workstation should treat DST as a governed draft-to-publication decision-support layer, not as a separate top-level shell.

The correct pipeline is:

`use case or subject corpus -> Gather -> Itemize -> Draft -> Review -> Publication`

with DST-specific internals:

`source/use case -> reduce_not candidate-path discovery -> DST structured projection -> DecisionFrame curation -> coordinated_transformation evaluation -> Review approval -> Publication`

At present, this is the intended full workstation-integrated DST path. The repository now has the first live binding, but not the full end-to-end one.

This means:

- `reduce_not` is used as a governed discovery layer for materially distinct candidate paths and missing distinctions
- [DST_PROMPT.md](DST_PROMPT.md) is used as a typed normalization layer after that discovery
- [coordinated_transformation/core.py](coordinated_transformation/core.py) evaluates the explicit curated candidates
- `Publication` consumes approved typed decision outputs, not prose-time inference

Current implementation reality:

- the repository now has a runtime-backed DST orchestration path that bootstraps a real controller and runs both discovery and normalization proposals over the root non-achievedness
- `Itemize` now persists `TransformationConstructCandidate` records and exposes `Suggest Constructs` on the selected itemized candidate
- `Draft` now has a bounded `Compose | Model` split, and `Draft Model` can accept curated constructs into persisted `DecisionFrame` / `DecisionReviewItem` state
- `Draft Model` now supports first-pass lane-aware curation and relation editing:
  - accepted constructs can cycle lanes
  - accepted transitions can bind source and target states
  - accepted decisions can bind a selected transition
  - accepted transitions can bind a changed capability
  - accepted decisions can bind an assigned actor
  - accepted capabilities can bind required dependencies and crossed boundaries
  - current-step guidance now keeps those bindings visible, inspects the first missing relation, and focuses the next missing construct before analysis runs
- `Explore` now carries a first bounded evaluated-path summary from the formal model rather than only surfaced fixture path titles
- for non-fixture subjects, `Itemize -> Suggest Constructs` now runs live `reduce_not -> DST_PROMPT` discovery/normalization over an ad hoc DST packet centered on the selected itemized candidate, with deterministic fallback when the live path yields nothing usable
- `Itemize -> Suggest Constructs` now also upserts refreshed DST construct suggestions through continuity-based merge, so curated construct ids, notes, accepted state, and canonical wording survive refreshed discovery and label churn
- `Draft -> Refresh DST Analysis` now upserts refreshed DST decision analysis through the same continuity discipline, preserving curated `DecisionFrame`, `DecisionReviewItem`, and accepted construct state across refreshed normalization
- `Review` and `Publication` now keep `Open Model` visible when attached decision work exists, with cross-phase navigation returning to `Draft` where the explicit `Open Model` button remains the in-tab entry into Model; DST-seeded subjects also keep `Refresh DST Analysis` available there, so later phases no longer behave like one-way exits out of model work
- decision-analysis recovery is now explicit rather than implicit:
  - if no decision frame exists, the recovery/progression action is `Start Decision Analysis`
  - if a decision frame exists and is current, the recovery/progression action is `Run Decision Analysis`
  - if a later same-subject import or refresh invalidates an older DST-backed frame, the recovery/progression action is `Refresh DST Analysis`
  - a `blocked` receipt does not remove rerun/refresh capability
  - `Review` and `Publication` must route back to the Draft recovery action instead of hiding blocked or stale attached analysis behind later-phase approval/build actions
- the runtime-backed DST path still uses a governed root-node proposal binding rather than a richer frontier-native `reduce_not` execution path

So the current workstation DST state is:

- product shape decided
- typed seams in place
- runtime-backed execution seam present
- first workstation persistence and Draft binding present
- first lane-aware Draft Model curation present
- richer live discovery and fuller phase binding still missing

The detailed implementation note is:

- [../dst/DST_IMPLEMENTATION.md](../dst/DST_IMPLEMENTATION.md)

The critical workstation rule is:

- DST should deepen `Itemize`, `Draft`, `Review`, and `Publication`
- DST should not yet introduce another top-level workstation tab

## Stable DST Workspace

The main workstation DST risk is not too many screens. It is too many mental models.

The user should not feel they are leaving one tool and entering another when they move from framing a case to modeling it to exploring alternatives.

So the workstation should keep one stable case workspace and expose three DST lenses over the same case object:

- `Frame`
  - what is this case
- `Model`
  - how is it structured
- `Explore`
  - what solutions or paths exist

These lenses should not become new top-level workstation tabs. They should live inside the existing workstation phases and reuse the same object model, inspector, and status model.

## DST Component Contract

For DST-capable workstation surfaces, the component roles should stay fixed:

- phase header or top action area
  - where am I, what case is this, what are the main actions
- workstation phase navigation
  - `Gather`, `Itemize`, `Draft`, `Review`, `Publication`
- DST lens controls
  - `Frame`, `Model`, `Explore`
- tabs within a lens
  - slices of that lens only
- cards
  - one construct, one alternative, or one case summary object
- lists or tables
  - many constructs, relations, or alternatives to scan or compare
- chips
  - filter, status, lane, quick-select, or tag
- right-side inspector
  - what is selected, what it means, what it links to, what is missing, why it matters
- bottom sheet or status band
  - warnings, validation issues, missing links, and temporary secondary detail only

The same object should remain selected across lens changes. If a constraint, transition, or actor is selected in one lens, the corresponding object should stay in focus when the user moves to another lens.

## Mapping DST Lenses Onto The Existing Workstation Flow

The workstation should not replace `Gather -> Itemize -> Draft -> Review -> Publication` with `Frame -> Model -> Explore`.

Instead:

- `Gather`
  - establishes the case and admits material
  - can surface first `Frame` facts, but should not become the main DST workspace
- `Itemize`
  - is the first practical `Frame` entry point
  - discovers actors, objectives, capabilities, dependencies, constraints, boundaries, states, transitions, decisions, and time points as candidates
- `Draft`
  - is the main DST workspace host
  - `Compose` remains report shaping
  - `Model` now exposes a first explicit `Frame | Model | Explore` lens strip over the same selected construct
  - a first shared status snapshot now appears in the inspector, active lens pane, and issue tray across those lenses
  - the next work is to deepen that into a fuller persistent inspector and status model across those lenses
- `Review`
  - validates the report plus attached DST outputs without changing the interaction grammar
- `Publication`
  - consumes approved `Explore` outputs as typed publication blocks, tables, diagrams, and receipts

So the shell rule is:

- workstation phases remain stable
- DST lenses live inside the DST-capable portions of those phases
- the case object, selection model, and inspector remain stable throughout

## Workstation And Subject Learning

The workstation now touches `LearningContext` directly through several real paths:

1. markdown ingest through [workstation_learn_markdown_action()](workstation/workstation_core.py), which reaches the external markdown pipeline and persists `LearningContext`
2. URL ingest through workstation URL-learning actions that preserve richer source bundles before admission
3. chat-originated research capture, where `/prepare-markdown <text>` asks the assistant for gather-ingress markdown, `/start-research` stages a Gather source revision from the last assistant message, `/start-research-into <subject title>` lets the user choose the target subject explicitly before confirmation, and the gather-scoped follow-up commands (`/curate-source`, `/merge-source`, `/curate-source-set`, `/find-sources`, `/merge-source-set`, `/merge-set-sources`) route back into staged source maintenance rather than corpus admission
4. chat-originated markdown save/append flows, which are captured after the turn through [workstation/learning_capture.py](workstation/learning_capture.py) and merged into `LearningContext`

So:

- the workstation already owns a real subject workflow over `LearningContext`
- gather admission is confirmation-gated rather than silently mutating maintained subject truth
- itemization and draft composition are now first-class governed stages, not implicit side effects of review/publication

## Workstation And Publication

Publication substrate now exists in the repository:

- [publication.py](publication.py)
- [publication_projection.py](publication_projection.py)
- [publication_render.py](publication_render.py)
- [publication_validation.py](publication_validation.py)

The workstation now exposes publication as a first-class UI workflow in Textual, with Flutter converging onto the same canonical gRPC-backed workflow.

Today publication is:

- a real projection capability
- a workstation-level lock/build/release surface over approved draft/review state
- backed by durable `PublicationComposition`, `PublicationBuild`, and rendered outputs under the subject corpus tree

## Correct Direction From Here

The next workstation concept is not “better markdown import UI”.

It is:

- subject-centered gathering
- typed itemization
- composable draft shaping
- explicit review approval
- deterministic publication build/review/release

That implies the current workstation shape is already:

`Gather -> Itemize -> Draft -> Review -> Publication`

The remaining work is to deepen those phases, not collapse them back into a thinner three-step story.

## Suggested Workstation Product Shape

The correct workstation product shape is now:

1. `Chat`
   - task execution
   - bounded skill/workflow invocation
   - conversational capture into subject workflows when appropriate

2. `Gather`
   - search for, save, and observe source documents
   - manage staged source collections before corpus admission
   - select or resolve the target subject
   - curate source records through Chat or manual editing while they remain sources
   - stage governed source-to-delta learning
   - stage governed admission from the last assistant message
   - manage explicit source import and merge-back proposals

3. `Itemize`
   - normalize admitted material into typed reusable items
   - identify glossary/entity/claim/equation/xref/decision-role candidates
   - merge, split, promote, reject, and retarget candidate items
   - when DST is active, surface governed candidate-path discoveries, dominant distinctions, and missing blockers derived from `reduce_not`
   - persist typed construct candidates that can later feed a `DecisionFrame`

4. `Draft`
   - compose normalized items into review-owned draft structure
   - orient items by semantic/render/evidence/transform mode
   - shape report scope, report blocks, and decision handoff
   - host the active `DecisionFrame`
   - for DST-capable cases, converge toward a stable `Frame | Model | Explore` lens host over the same case object
   - accept carried-forward construct candidates into that frame
   - bind candidate paths, relations, and assignments
   - run formal evaluation through [coordinated_transformation/core.py](coordinated_transformation/core.py)
   - keep this under a bounded `Compose | Model` split rather than a new top-level tab

5. `Review`
   - compare maintained projections
   - inspect and approve the draft/report plan
   - remain the explicit governance gate before publication
   - inspect decision-analysis receipts and recommendation receipts
   - approve or reject the `DecisionFrame`-backed shaped draft

6. `Publication`
   - lock approved inputs
   - build report publication
   - inspect validation/build results
   - review markdown/Typst/PDF outputs
   - release and archive outputs
   - consume only approved typed decision constructs, candidate paths, and evaluation receipts

7. `Permissions`, `Activity`, `Skills`
   - continue as workstation cross-cutting operational surfaces

## DecisionFrame Hookup

`DecisionFrame` should be wired into the workstation in a phase-local way.

### `Gather`

Do not create or edit a `DecisionFrame` here.

This phase only admits and activates subject material.

### `Itemize`

`Itemize` should prepare the future `DecisionFrame` by surfacing:

- construct candidates
- candidate path families
- dominant unresolved distinctions
- missing blockers and missing dependencies

These should come from:

- deterministic itemization where possible
- bounded `reduce_not`-driven decomposition over selected raw prose chunks or source snapshots when the source is weakly structured or materially under-determined
- typed projection through [DST_PROMPT.md](DST_PROMPT.md)

The output of `Itemize` should therefore be a candidate field, not a final frame.

Current first cut:

- workstation-launched `Itemize` now has a direct-LLM decomposition policy:
  - launch default: bounded direct `reduce_not` decomposition is allowed
  - launch opt-out: `--no-allow-direct-llm-decomposition`
  - launch opt-in spelling remains explicit: `--allow-direct-llm-decomposition`
- this direct LLM decomposition belongs to `Itemize`, not `Gather`
- the decomposition result remains candidate itemization output, not admitted source truth and not publication prose
- deterministic extraction still remains valid as the non-LLM fallback path and as a merge source for stable equation/xref/symbol slices
- the selected itemized candidate can now persist `TransformationConstructCandidate` suggestions directly from `Itemize`
- for non-fixture subjects this can now run a live `reduce_not -> DST_PROMPT` discovery/normalization path, with deterministic fallback if the live path yields nothing usable

Rephrase boundary:

- `Itemize` is an allowed rephrase surface
- rephrase may be done either:
  - with LLM assistance
  - with manual editing
- that rephrase should improve normalized item wording without turning source material into publication prose
- the first workstation slice now exists:
  - `@llm` on the selected itemized candidate opens a rephrase request in `Chat`
  - that chat turn now stages a pending LLM rephrase target for the selected itemized intermediate
  - the latest assistant reply can then be explicitly applied or discarded from `Itemize`
  - `=` on the selected itemized candidate opens a manual rephrase file and applies it back into the persisted itemized intermediate
- regeneration now preserves that intermediate more carefully:
  - itemization refresh matches existing items by source continuity, not only by the currently generated item id
  - both manual and applied-LLM `Itemize` rephrases therefore survive source/context refreshes while the latest generated wording remains visible in metadata

## Gather And Chat Source Workflow

The next workstation gather cut should treat source work as a first-class surface shared between `Gather` and `Chat`.

The governing rule is:

- `Chat` remains a general workstation/skill surface
- `Gather` owns the staged source knowledgebase
- source work moves between them through explicit prompt targets and receipts

This means:

- do not narrow `Chat` into a research-only tool
- do not force source curation to happen only inside `Chat`
- do not auto-import saved sources into the subject corpus

The intended shape is:

`web / markdown / URL / pasted notes / chat result -> staged source knowledgebase in Gather -> explicit source curation -> explicit import into the subject corpus`

### Staged Sources, Not Yet Corpus

`Gather` should persist source-only records that are not yet admitted into subject corpus.

These should be distinct from admitted `LearningSource` records.

They should support:

- topic/query-organized source collections
- saved link sets
- URL-backed capture bundles
- source markdown and notes
- curation receipts
- import/export linkage

The core boundary is:

- staged source = source workbench state
- `LearningSource` = admitted corpus provenance

Current implementation reality:

- URL ingress now lands in a gather-owned staged source workspace first
- each captured URL creates or refreshes:
  - one `StagedSource`
  - one latest `SourceRevision`
  - one persisted markdown body
  - one persisted richer bundle
- explicit import is now what creates admitted `LearningSource`
- later inspection is no longer filesystem-only:
  - `Gather` now shows a selectable staged-source inventory
  - `Gather` now shows a selected-source detail pane with markdown/body and bundle paths plus a content preview
  - `Gather` now persists one default per-subject source set: `All Gather Sources`
  - `Gather` now also supports the first operator-managed selected source sets on top of `All Gather Sources`
  - `Gather` can now create topic/query source sets directly from chat or command input such as `/create-source-set-from-query <title> | <query> | [description]`
  - source-set selector labels now surface count/query state directly, for example `All Gather Sources [1 source, no saved query]`
  - the first saved-query/source-finding path is now live for the selected operator-managed source set
  - the selected source set can now maintain source-only knowledgebase metadata:
    - one maintained summary
    - a maintained open-question list
    - a maintained query/topic string
  - the first URL-backed staged-source refresh path is now live for the selected staged source
  - the selected source set now surfaces explicit workbench readiness for:
    - `Find Sources`
    - `Synthesize Source Set`
    - `Sync Source Set`
    - `Apply Set Export Preview`
    - `Merge Source Set`
    - `Merge Set Sources`
    - refreshable URL count
    - last sync metadata
  - that same source-set workbench readiness now appears in both the Gather source inventory surface and the selected source-set detail/target pane
  - the first full staged-source/source-set workbench slice is now live; what remains is the broader topic/query knowledgebase layer above it

### Gather-Scoped Chat

The workstation should support explicit chat prompt targets such as:

- general chat
- gather source discovery
- gather source curation
- itemize rephrase
- draft rephrase

Behavior rule:

- general chat keeps the full workstation/skill behavior
- gather-scoped chat prefers source-discovery, source-capture, source-curation, and source-sync work
- replies produced under a gather-scoped prompt target should be applicable back into staged source records without auto-import
- `/start-research` and `/start-research-into ...` now follow that same rule: confirmation stages a `chat` source revision in Gather and does not admit corpus material until the operator imports that staged source explicitly

Current implementation reality:

- source-specific chat over one selected staged source is now available as a first-class Gather detail action
- that surface is now widened through the first source-set cut:
  - the first default source set is now part of the prompt context for source-detail curation
  - `@llm` now starts a pending source curation round for the selected staged source
  - `Apply LLM Curation` now writes a new staged `SourceRevision`
  - `Discard LLM Curation` now drops the pending proposal without affecting corpus
  - `Merge Back In Chat` now starts a pending merge-back proposal for the selected staged source using current subject learnings as prompt context
  - `Apply Merge-Back Proposal` now writes a new staged `merge` revision
  - `Discard Merge-Back Proposal` now drops the pending proposal without affecting corpus
- the selected operator-managed source set can now be curated through:
  - `@llm` for source-set metadata curation
  - `=` for manual source-set metadata curation
  - `/curate-source-set` in chat for the same LLM curation path
  - `/edit-source-set` in chat for the same manual source-set metadata curation path
- those source-set actions update `SourceCollection` metadata only and do not affect corpus admission
- `Find Sources In Chat` and `/find-sources` on the selected operator-managed source set now start a pending discovery turn using the set's saved query/topic
- `Apply Discovered Sources` now creates staged discovery revisions for new sources or links existing staged sources back into that set
- `Synthesize Source Set In Chat` and `/synthesize-source-set` on the selected operator-managed source set now start a pending source-set synthesis turn using the set's staged sources and saved query/topic
- `Apply Source-Set Synthesis` now updates `SourceCollection` knowledgebase metadata only:
  - summary
  - open questions
  - query/topic
- `Discard Source-Set Synthesis` now drops the pending proposal without affecting corpus
- `Merge Source Set In Chat` and `/merge-source-set` now start a pending merge-back proposal for the selected operator-managed source set using current subject learnings as prompt context
- `Apply Source-Set Merge-Back` now updates `SourceCollection` metadata only
- `Discard Source-Set Merge-Back` now drops the pending proposal without affecting corpus
- `Merge Set Sources In Chat` and `/merge-set-sources` now start a pending multi-source merge-back proposal for the member staged sources of the selected operator-managed source set using current subject learnings as prompt context
- `Apply Set Source Merge-Back` now writes staged `merge` revisions back into the matched staged sources
- `Discard Set Source Merge-Back` now drops the pending proposal without affecting corpus
- the selected staged source can now be handled through `/curate-source`, `/edit-source`, and `/merge-source`, which route into the same Gather source-layer curation, manual edit, and merge-back turns as the pane actions
- the selected staged source can now also be handled through `/create-source-set`, `/refresh-source`, and `/apply-source-export`, which route into the same Gather source-set creation, source refresh, and export-preview application actions as the pane actions
- the selected source set can now also be handled through:
  - `/sync-source-set`
  - `/apply-source-set-export`
  - `/create-source-set-from-query`
  - `/synthesize-source-set`
  which route into the same Gather source-set sync, export-preview, topic/query creation, and source-set synthesis actions as the pane actions
- `Refresh Selected Source` now re-fetches the selected URL-backed staged source into a new staged `refresh` revision
- `Sync Source Set` now batch-refreshes the selected source set's URL-backed staged sources and records set-level sync metadata without corpus admission
- the selected staged-source detail pane now shows `Revision history` and `Latest change summary` as table-backed surfaces below the detail pane
- `Change Diff Baseline (...)` now lets the operator browse the selected staged source against older revisions
- the selected staged-source detail pane now shows a first deterministic `Export proposal preview` derived from current governed learnings without auto-applying a merge
- the selected source-set detail pane now shows a first deterministic `Source-set export preview` derived from current governed learnings without auto-applying a merge
- the selected source-set detail pane now also shows a `Member export status` table plus first per-member export targets derived from current governed learnings without auto-applying merges
- the selected source-set detail pane now also shows:
  - `Member export status`
  - `Member revision history`
  - aggregated `Merge/export history`
  - `Actionable export targets`
  - `Export-applied targets`
  - recent member revision events, export events, export-applied target previews, export-state comparison, and merge/export counts across the selected source set
- the selected source-set detail pane now also shows source-only knowledgebase state:
  - set type
  - saved query/topic
  - maintained summary
  - maintained open questions
  - synthesis readiness in the shared source-set workbench rows
- per-member export state now distinguishes:
  - `aligned`
  - `changed`
  - `pending`
  - `cleared`
- actionable export browsing now shows the first per-member add/remove shape for `pending`, `changed`, and `cleared` targets
- `Apply Selected Source Export Preview` now turns the current selected-source export preview into a staged `merge` revision without importing it into the subject corpus
- `Apply Set Export Preview` now turns the current per-member source targets into staged `merge` revisions without importing them into the subject corpus
- the first staged-source and source-set revision/history/diff/export/apply slice is now complete enough to treat `Gather` as a real staged-source workbench
- the next high-level step is no longer “make source sets real”; it is to execute the next product sequence in this order:
  - broaden `Gather` from the current operator-managed source sets into a broader topic/query knowledgebase with deeper saved-query, collection, and multi-source comparison workflows
  - deepen `Gather <-> Chat` on top of that knowledgebase so discovery, saved-query maintenance, and multi-source synthesis can be routed through chat without polluting admitted corpus state
  - then widen `Draft Model` with broader many-to-many relation editing and richer lane-aware construct curation so blocked decision analyses become more repairable before `Review` and `Publication`

### Gather Source Operations

The next gather workbench should expose source operations such as:

- `Find Sources`
- `Save Search`
- `Capture Source`
- `Refresh Source`
- `Summarize Source`
- `Edit Source Notes`
- `Prepare Import`
- `Prepare Merge Back`

These remain source-layer operations until explicitly imported.

### Skills And Gather

Skills should be usable here, but not in a way that weakens general chat.

The correct rule is:

- when a suitable source-discovery or source-curation skill exists, gather-scoped chat should prefer it
- when no such skill exists, gather-scoped chat may fall back to the workstation host/capability path
- general chat should still be able to invoke unrelated non-research skills without source-workflow interference

### `Draft`

`Draft` should be the place where the operator:

- creates or updates the `DecisionFrame`
- chooses which constructs and path candidates are in scope
- binds relations and assignments
- runs formal DST evaluation
- sees admissibility, validity, executability, risk, and reachability receipts

This is the correct place because `Draft` already owns shaping and composition.

Current first cut:

- `Draft` now has a bounded `Model` submode alongside `Compose`
- `Draft Model` can accept construct candidates into persisted `DecisionFrame` / `DecisionReviewItem` state
- `Itemize -> Suggest Constructs` now seeds those construct candidates through live `reduce_not -> DST_PROMPT` discovery for non-fixture subjects
- after the next `Gather` knowledgebase and `Gather <-> Chat` widening cuts land, the next phase-specific widening step is broader many-to-many relation editing and richer lane-aware construct curation in `Draft Model`

Immediate execution order:

- the first DST publication-hardening pass over [dst](dst) is now in place
- the source boundary stays intact:
  - source markdown stays source-only
  - source cleanup only removes DST/internal jargon and formatting noise
  - publication-quality wording must not be pushed backward into source cleanup
- publication quality is now being pushed forward through the live workstation phases:
  - `Itemize` rephrase
  - `Draft` rephrase
  - `Review`
  - `Publication`
- the DST corpus now includes simpler and less-structured scenarios so the same flow is already being hardened against weaker source material too
- part of that simpler corpus is now intentionally source-only and omits explicit candidate paths, so the workstation has to discover candidate paths later instead of inheriting them from the source file
- the current workstation-side publication slice now carries:
  - richer decision tables with explicit option-to-transition and actor-assignment reasoning
  - execution guidance with recommended transitions, responsible actors, and activated capabilities
  - recommendation receipts with candidate-path count and top-option transition / actor summaries
- the current workstation-side ranking slice now also carries:
  - a `Decision Ranking Summary` with policy profile, ranking rules, candidate-path count, and ranked-option reasoning
- the current workstation-side PDF-quality slice now also carries:
  - readable full-width decision option cards in Typst/PDF output instead of narrow equal-width matrix columns
  - a clearer decision model diagram layout across current state, transition path, target state, dependencies, and boundaries
  - explicit boundary-governance guidance in execution guidance and recommendation receipts
- the current workstation-side publication-guidance slice now also carries:
  - editorial guidance in the ranking summary instead of receipt-only policy text
  - reserve / blocked option callouts in the ranking surface
  - reserve / blocked policy narration so publication readers can see why a reserve option is held back and why a blocked option stays disqualified
  - a diagram that separates recommended, reserve, and blocked paths instead of flattening them together
  - capability / dependency / boundary reasoning tied to the recommended and reserve/blocked options
- the current workstation-side publication-structure slice now also carries:
  - a real section tree for decision publications instead of a flat analysis dump
  - nested analysis/model/risk, implementation-guidance, and receipt/audit subsections instead of one flat scaffold
- the current workstation-side composition/layout slice now also carries:
  - content-aware subsection titles instead of one fixed decision scaffold
  - empty scaffold sections dropped from the materialized publication tree
  - page-aware reserve / blocked option-card layout that stays readable in rendered PDFs
- the current workstation-side validation/xref slice now also carries:
  - stronger publication section-role constraints
  - typed claim-to-unit/source/entity xrefs
  - broader unit/source/entity impact queries over the resulting publication graph
- the current workstation-side composition-diff slice now also carries:
  - explicit diff-baseline selection in Review/Publication instead of silently choosing one baseline
  - comparison against the last approved plan, the previous persisted revision, or the current-subject snapshot baseline
  - visible diff-baseline status in Review/Publication workspace text and diff receipts
- the current workstation-side publication-composition slice now also carries:
  - direct per-section shaping in `Review` through section briefs:
    - `@llm` drafts a section brief for the selected report section
    - `=` opens manual section-brief editing for the selected report section
  - richer import-usage control in `Review` / `Publication`:
    - the fast cycle action still exists
    - More Actions now exposes explicit per-mode import-use actions for the selected imported-support item
- the next workstation-side priority after that is:
  - reduce repeated policy/path narration across ranking, model, and implementation sections

Rephrase boundary:

- `Draft` is also an allowed rephrase surface
- rephrase may be done either:
  - with LLM assistance
  - with manual editing
- this is the place where publication-ready phrasing should be shaped
- it should not be pushed backward into source cleanup
- the first workstation slice now exists:
  - `@llm` on the selected draft item opens a rephrase request in `Chat`
  - that chat turn now stages a pending LLM draft rephrase for the selected review item
  - the latest assistant reply can then be explicitly applied or discarded from `Draft`
  - `=` on the selected draft item opens a manual rephrase file and applies it back into the persisted draft/review intermediate
- that draft wording now survives composition refresh as long as the upstream itemized identity remains continuous across regeneration, whether it came from manual editing or an applied LLM rephrase proposal

### `Review`

`Review` should not discover DST structure.

It should:

- inspect the resulting analysis
- inspect receipt-backed recommendation structure
- approve or reject the shaped `DecisionFrame`-bearing draft

### `Publication`

`Publication` should consume only:

- approved `DecisionFrame` state
- approved typed construct/path projections
- approved evaluation receipts

It should not:

- infer the decision model from prose at build time
- call `reduce_not` at publication time

## `reduce_not` Boundary In Workstation

The workstation should use `reduce_not` in DST, but only in a bounded way.

Allowed:

- bounded source-side decomposition in `Itemize` over selected raw prose chunks or source snapshots when the workstation launch policy allows direct LLM decomposition
- candidate-path discovery
- dominant distinction discovery
- blocker discovery
- missingness and rival-path discovery during `Itemize` and `Draft`

Not allowed:

- using `reduce_not` as the `Gather` admission engine
- direct publication generation
- silent final recommendation ownership
- replacing typed projection or `DecisionFrame` persistence

So the workstation rule is:

- `reduce_not` discovers
- DST projection normalizes
- `DecisionFrame` curates
- `coordinated_transformation` evaluates
- `Review` approves
- `Publication` renders

## Why Typst Matters In The Workstation

Typst should not remain only an emitted filesystem artifact.

Within the workstation, Typst should remain:

- a maintained subject projection
- a publication preview/review surface
- later a diffable output in review workflows

Markdown still matters for ingress and compatibility.

But the workstation increasingly exposes:

- source markdown as ingress
- `subject.typ` as maintained corpus projection
- publication Typst as review/release projection

## Textual Widget Contract

The Textual workstation should stop using `Button` and `Log` as generic substitutes for every interaction pattern.

The control semantics should now be fixed:

- `Button`
  - a command with side effects
- `Select`
  - choose one value from a multi-value setting
- `Switch`
  - turn one true boolean on or off
- `OptionList`
  - browse one flat selectable inventory
- `Tree`
  - browse one hierarchical inventory or scope
- `SelectionList`
  - manage many independent include/exclude decisions
- `DataTable`
  - inspect revision, diff, and export history
- `Collapsible`
  - reveal help, secondary actions, or supporting detail without changing the main pane model
- `TabbedContent`
  - switch between real sub-lenses such as `Frame | Model | Explore`
- `ContentSwitcher`
  - maximize or swap views inside the current tab body only
- `Markdown`
  - render prose-rich read-only content
- `TextArea`
  - edit inline prose when we stop routing editing through temporary files

This keeps the workstation aligned with [DESIGN.md](../design/AXIOMATIC_SYSTEM_FOR_DESIGN.md):

- no fake dropdowns implemented as repeated button presses
- no fake toggles implemented as relabeled action buttons
- no fake trees or tables implemented as wrapped logs when the user is actually navigating structure
- maximize behavior stays inside the current tab area instead of trying to cover the phase tabs

### Intended Workstation Mapping

The intended widget mapping is:

- `Gather`
  - source-set selection: `Select`
  - selected-source membership: `Switch`
  - staged-source and source-set browsing: `OptionList` first, then `Tree` where hierarchy matters
  - revision/export history: `DataTable`
  - source preview and merge/export preview: `Markdown`
- `Itemize`
  - item inventory: `OptionList`
  - selected item decision role: `Select`
  - hold-for-merge: `Switch`
- `Draft`
  - draft inventory: `OptionList`
  - report scope: `Tree`
  - `Frame | Model | Explore`: nested tabs
  - construct sort, lane, and policy profile: `Select`
  - many-to-many relation binding: `SelectionList`
- `Review` and `Publication`
  - scope and section structure: `Tree`
  - diff baselines, output modes, section plans, import targets, and import usage: `Select`
  - selected-item inclusion state: `Switch`
  - compare and export history: `DataTable`

### Immediate Migration Rule

The first migration slice must be compatibility-preserving.

That means:

1. keep the existing workflow action keys and state transitions intact
2. expose current value and option metadata from [workstation/subject_workflow.py](workstation/subject_workflow.py)
3. render `Select` and `Switch` only where the current phase action row is already acting like a value chooser
4. map widget changes back onto the existing workflow actions underneath
5. leave all real commands as `Button`

So the first live widget migration is:

- `Select` for current cycle-style phase actions
- `Switch` for current true toggle actions
- no immediate inventory, history, or maximize rewrites in the same cut

## Immediate Position

The current truth is:

- the projection split is real
- the shared host interaction substrate is real
- the event bus and projection controllers are real
- `Learn Markdown` is legacy ingress functionality nested inside `Gather`
- the live user workflow is `Gather -> Itemize -> Draft -> Review -> Publication`
- `Review` is now the approval/sign-off gate, not the place where first-pass composition happens
- the next chapter is to deepen intake, preview, history, diff, and host convergence behavior without letting Textual and Flutter drift apart
