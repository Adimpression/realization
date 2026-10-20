# Research And Publish Flow

Formal position for the workstation user workflow that now spans:

- subject gathering
- typed itemization
- draft composition
- review approval
- report publication

This document distinguishes:

- what the code already does
- what the current workstation shells expose
- what the next deepening cuts should still add

## Current Truth In Code

The current Textual shell and the Flutter migration target are connected to the live subject/publication workflow layer.

The relevant files are:

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

Important clarification:

- [workstation/chat_ui.py](workstation/chat_ui.py) still contains some stale local alias naming
- but the shells now run against the live subject workflow, not a mock publication path

## What The Current Workstation Flow Actually Does

The current workstation shell now exposes nine top-level tabs:

- `Chat`
- `Gather`
- `Itemize`
- `Draft`
- `Review`
- `Publication`
- `Permissions`
- `Activity`
- `Skills`

The governed subject workflow inside that shell spans five working phases:

- `Gather`
- `Itemize`
- `Draft`
- `Review`
- `Publication`

Per-subject workflow progress is resumed from:

- `corpus/<subject_id>/receipts/workflow_progress.json`

### Gather

The live `Gather` phase is now the intake and subject-activation surface.

It currently does these things:

- loads live subjects from the corpus
- shows linked sources, admitted items, recent deltas, and maintained projection summaries
- shows source-set selector options with source counts and saved-query state
- can create topic/query source sets directly from explicit chat or command input
- when a source set is selected, surfaces explicit source-set workbench readiness for:
  - finding sources
  - synthesizing the source set into maintained summary/open-question/query metadata
  - syncing the source set
  - applying set export previews
  - merging source-set metadata
  - merging set sources back into staged source revisions
- when a staged source or source set is selected, shows table-backed revision history, change summary, export preview, and source-set export surfaces
- when a staged source set is selected, shows the same readiness state again in the selected target/detail surface so the operator can inspect it without inferring from button enablement
- the first full staged-source/source-set workbench slice is now live, including topic/query set creation and source-set synthesis
- the next product sequence is now explicit:
  - first broaden `Gather` from that workbench into a broader cross-set topic/query knowledgebase
  - then deepen `Gather <-> Chat` so saved-query maintenance, broader discovery, and multi-source synthesis can route through chat without implicit corpus admission
  - then widen `Draft Model` so richer relation editing can reduce blocked decision-analysis and publication outcomes
- allows subject refresh and subject activation
- supports markdown ingress and URL ingress
- supports governed staging of the last assistant message into gather admission
- requires explicit confirmation before mutating maintained subject truth
- supports maintained-file comparison when the workflow needs it
- supports import-source staging and import creation

### Itemize

The live `Itemize` phase is materially real.

It currently does these things:

- generates a persisted itemization session for the active subject snapshot
- surfaces deterministic typed candidates such as claims, entities, glossary terms, equations, variables, xrefs, and decision-role candidates
- preserves manual item edits across refresh
- supports promote, reject, restore, split, merge, and decision-role cycling
- provides the normalized inventory that feeds `Draft`

### Draft

The live `Draft` phase is materially real.

It currently does these things:

- materializes and persists `ReviewComposition`
- carries itemized candidates into draft composition by default unless rejected
- lets the operator orient draft items by semantic/render/evidence/transform mode
- supports split/merge/root-promotion and ordering over draft review items
- shapes report-plan scope and review-owned structure
- hosts the first decision-review handoff and frame creation paths

Decision-analysis recovery precedence is:

- if no decision frame exists: `Start Decision Analysis`
- if a decision frame exists and is current: `Run Decision Analysis`
- if a later same-subject import invalidates an older DST-backed frame: `Refresh DST Analysis`

A `blocked` receipt is not a dead end. It must still leave a Draft recovery action available, and later phases must route back to that Draft recovery action instead of pretending approval/build can continue normally.

### Review

The live `Review` phase is the explicit approval/sign-off gate.

It currently does these things:

- compares maintained `subject.md` and `subject.typ`
- records an alignment or drift verdict
- blocks approval unless maintained projections are aligned and the draft is current
- previews report scope and draft outputs for approval
- when the result pane is opened, shows table-backed comparison and latest-receipt summaries
- remains the last gate before `Publication`

### Publication

The live `Publication` phase is materially real.

It currently does these things:

- locks report publication inputs
- builds a report from approved draft/review state
- validates the publication graph
- renders `report.md`
- renders `report.typ`
- attempts Typst compile to `report.pdf`
- persists publication records and build records
- when the result pane is opened, shows table-backed build, validation, and diff summaries
- exposes release-packet and preview actions

## Where Publication Artifacts Go

Publication state is persisted beneath the subject corpus tree, not hidden only inside one table or one UI cache.

The publication root is:

`corpus/<subject_id>/publications/<publication_id>/`

That tree contains, at minimum:

- `publication.json`
- `compositions/*.json`
- `composition_revisions/*.json`
- `sections/*.json`
- `blocks/*.json`
- `claims/*.json`
- `sources/*.json`
- `xrefs/*.json`
- `builds/*.json`
- `outputs/<build_id>/report.md`
- `outputs/<build_id>/report.typ`
- `outputs/<build_id>/report.pdf` when Typst compile succeeds

## Current Practical User Workflow

The current practical user flow is:

1. Create or already have a subject in the corpus.
   Current creation can come from:
   - markdown ingress inside `Gather`
   - URL ingress inside `Gather`
   - chat-backed gather capture

2. If starting from chat notes, run:
   - `/prepare-markdown <text>` to ask the assistant for gather-ingress markdown
   - `/start-research` to stage a Gather source revision from the last assistant message
   - `yes` or `no` to confirm or cancel
   - `/start-research-into <subject title>` if the target subject must be chosen explicitly
   - later Gather-source maintenance can stay in chat through `/create-source-set`, `/refresh-source`, `/apply-source-export`, `/curate-source`, `/edit-source`, `/merge-source`, `/sync-source-set`, `/apply-source-set-export`, `/curate-source-set`, `/edit-source-set`, `/find-sources`, `/merge-source-set`, and `/merge-set-sources`

3. Enter `Gather`, choose or activate the subject, inspect current status, and continue the workflow.

4. Use `Itemize`.
   - generate or refresh the typed inventory
   - inspect candidate items
   - normalize what should feed drafting

5. Use `Draft`.
   - shape the draft composition
   - orient items
   - build the report plan and decision handoff

6. Use `Review`.
   - compare maintained files
   - validate and approve the draft/report plan

7. Use `Publication`.
   - lock inputs
   - build report
   - inspect validation result
   - open release packet
   - preview rendered outputs

## Current Gaps

The current gaps are structural, not cosmetic.

### Gather is still narrower than the full ideal intake workbench

The assistant-capture bridge and ingress actions are live, but `Gather` still does not yet provide:

- richer source queue management
- broader source observation beyond the current ingress/result surfaces
- fuller multi-source intake orchestration

### Shared layout metadata is still behind the real workflow

The live shells expose the five-phase subject workflow, but the neutral layout substrate still models only the coarser shell/tab structure.

### Publication preview is still narrower than the stored artifacts

The publication layer writes:

- markdown
- Typst
- PDF

The user-facing preview surface still needs fuller first-class Typst exposure and better artifact history/diff behavior.

### Some shell naming remains stale

The live workflow is real, but some local names in the shells still carry older mock/trail terminology and should be cleaned up.

## Target Ideal Flow

The target ideal should preserve the current phase structure while deepening each phase rather than collapsing them.

The correct shape is:

`Gather -> Itemize -> Draft -> Review -> Publication`

### Target Ideal: Gather

Gather should be a true intake workbench.

The user should be able to:

- choose an existing subject or create a new one
- add or observe sources
- capture the last assistant message from Chat into intake
- stage proposed admission
- admit or reject that staged change

### Target Ideal: Itemize

Itemize should remain the typed normalization workbench.

The user should be able to:

- inspect all deterministic candidates
- filter by type and confidence
- merge, split, promote, reject, and relabel candidates
- prepare a clean typed inventory before drafting

### Target Ideal: Draft

Draft should remain the composition workbench.

The user should be able to:

- shape review-owned draft structure
- orient material toward prose, tables, diagrams, equations, figures, and decision aids
- create and refine report-plan scope
- hand explicit decision structure downstream

### Target Ideal: Review

Review should remain the gate over maintained subject truth and approved draft state.

The user should be able to:

- inspect maintained projection alignment
- inspect draft/report-plan receipts
- approve or reject what is allowed into publication

### Target Ideal: Publication

Publication should remain a pure build/release workflow over already-approved truth.

The user should be able to:

- lock publication inputs
- run validation
- build outputs
- preview markdown, Typst, and PDF
- inspect release packets
- later compare builds or diffs

## Formal Direction

The current code already supports:

- live gather admission
- live itemization
- live draft composition
- live review gates
- live report publication build

The next work is not to invent publication or composition from nothing.

It is to:

- deepen gather intake
- widen neutral layout convergence
- expose publication artifacts more completely
- keep Textual as the reference client and Flutter aligned with the actual live domain layer
