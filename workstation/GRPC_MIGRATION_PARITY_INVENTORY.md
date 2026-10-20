# Workstation gRPC Migration Parity Inventory

This file records the canonical backend path for the user-visible workstation
operations that matter during the Textual-to-Flutter migration.

Rule:

- workflow semantics live in the shell and subject-workflow services
- UI clients are renderers and input collectors
- no UI client owns subject-workflow state transitions
- no UI client may call direct runtime workflow actions

Textual remains the reference client until Flutter migration is complete.

## Canonical Operations

### Bootstrap / Open Root

- User operation: open a workstation root
- Canonical path:
  - `WorkstationBootstrapService.ListWorkstationRoots`
  - `WorkstationShellService.OpenClientSession`
  - initial shell/subject projections through snapshot RPCs
- Reference client:
  - Textual: shell/session wiring
  - Flutter: bootstrap screen + root selection
- Forbidden shortcut:
  - directly reading or materializing workstation session files in UI code

### Chat Submit

- User operation: send a chat prompt
- Canonical path:
  - `WorkstationShellService.SubmitChatInput`
  - `WorkstationShellService.GetChatSnapshot`
  - `WorkstationShellService.WatchWorkstationShell`
- Reference client:
  - Textual chat shell
  - Flutter chat tab
- Forbidden shortcut:
  - calling local prompt/session helpers from UI code

### Gather Markdown Intake

- User operation: import markdown into the subject workflow
- Canonical path:
  - file pick in client
  - `WorkstationAssetService.StageMarkdownUpload`
  - `SubjectWorkflowService.GetSubjectWorkflowSnapshot` with staged projection context
  - `SubjectWorkflowService.ApplySubjectAction(action_key="use_markdown_ingress")`
  - `SubjectWorkflowService.WatchSubjectWorkflow`
- Reference client:
  - Textual Gather ingress over subject-workflow client
  - Flutter Gather import flow
- Forbidden shortcut:
  - `workstation_learn_markdown_action` from UI code

### Gather URL Intake

- User operation: stage and admit a URL source
- Canonical path:
  - URL capture in client
  - `SubjectWorkflowService.ApplySubjectAction(action_key="use_url_ingress")`
  - `SubjectWorkflowService.WatchSubjectWorkflow`
- Reference client:
  - Textual Gather URL ingress over subject-workflow client
  - Flutter Gather URL ingress when exposed
- Forbidden shortcut:
  - `workstation_learn_url_action` from UI code

### Import Source Selection / Approval

- User operation: select a source subject, create import, preview/approve import
- Canonical path:
  - `SubjectWorkflowService.ApplySubjectAction(...)`
  - `SubjectWorkflowService.GetSubjectWorkflowSnapshot`
  - `SubjectWorkflowService.WatchSubjectWorkflow`
- Reference client:
  - Textual BDD flow
  - Flutter mirrored BDD flow
- Forbidden shortcut:
  - client-local import state machines that diverge from subject-workflow snapshots

### Itemize Generation

- User operation: generate or refresh typed candidate constructs
- Canonical path:
  - `SubjectWorkflowService.ApplySubjectAction(...)`
  - refreshed subject snapshot and watch events
- Reference client:
  - Textual Itemize tab
  - Flutter Itemize tab
- Forbidden shortcut:
  - client-local generation state treated as workflow truth

### Draft Composition

- User operation: shape draft/report plan
- Canonical path:
  - `SubjectWorkflowService.ApplySubjectAction(...)`
  - refreshed subject snapshot and watch events
- Reference client:
  - Textual Draft tab
  - Flutter Draft tab
- Forbidden shortcut:
  - client recomputation of workflow gates or next phase

### Review Actions

- User operation: inspect maintained state, preview pending import, approve/reject review gates
- Canonical path:
  - `SubjectWorkflowService.ApplySubjectAction(...)`
  - refreshed subject snapshot and watch events
- Reference client:
  - Textual Review tab
  - Flutter Review tab
- Forbidden shortcut:
  - UI-owned review gating logic

### Publication Actions

- User operation: build/rebuild publication artifacts
- Canonical path:
  - `SubjectWorkflowService.ApplySubjectAction(...)`
  - `WorkstationAssetService.ResolveArtifacts` for cross-platform artifact use
- Reference client:
  - Textual Publication tab
  - Flutter Publication tab
- Forbidden shortcut:
  - direct file-open assumptions without artifact resolution for cross-platform clients

### Utility Tabs

- User operations:
  - inspect permissions
  - inspect activity
  - inspect skills
- Canonical path:
  - `WorkstationShellService.GetPermissionsView`
  - `WorkstationShellService.GetActivityView`
  - `WorkstationShellService.GetSkillsView`
  - `WorkstationShellService.WatchWorkstationShell`
- Reference client:
  - Textual utility surfaces
  - Flutter utility tabs
- Forbidden shortcut:
  - direct session-file reads in UI code

## Required Invariants

- Textual is the reference client until Flutter migration completes.
- Flutter behavior must converge to Textual through shared gRPC contracts.
- Flet is removed and must not reappear in active packaging, entrypoints, or product docs.
- Subject placeholder scenarios are valid workflow scenarios, not client-side null states.
- Staged markdown is not terminal state; it must either advance through
  `use_markdown_ingress` or fail with a renderable Gather snapshot.
