# Event Bus Implementation

Implementation plan for the host-owned workstation event bus defined in [EVENT_BUS.md](EVENT_BUS.md).

This file is intentionally concrete.

It defines:

- where the event bus should live
- what the primary event granularity should be
- where publication should occur in the current codebase
- how host-owned panels should subscribe
- what rollout order is sensible
- which validation scenarios are required

## Current Status

Landed so far:

- Phase 1: workstation-local bus wrapper in [workstation/event_bus.py](workstation/event_bus.py)
- bounded Phase 2: turn, receipt, session, permissions, and skill-catalog publication from workstation mutation points
- Phase 3: real Blend workflow and step lifecycle publication from [blend_workflow_execution.py](blend_workflow_execution.py) with `workflow_execution_id`, including:
  - `blend_workflow_started`
  - `blend_step_started`
  - `blend_step_skipped`
  - `blend_step_blocked`
  - `blend_step_completed`
  - `blend_step_failed`
  - `blend_workflow_completed`
  - `blend_workflow_failed`
  - `blend_workflow_persisted`

Still pending:

- Phase 4 subscriber controllers beyond the existing shell/Flutter polling/projection path
- Phase 5 broader explicit context/UI state surfaces

## Implementation Rule

The event bus must be implemented as a **host-owned workstation facility**.

It must not become a new required dependency of:

- controller correctness
- governed runtime correctness
- skill runtime correctness
- host mediation correctness

The workstation must remain correct with zero active subscribers.

The event bus improves coordination, responsiveness, and observability.

It does not establish truth.

## Dependency Rule

Allowed direction:

- `workstation UI / host surfaces -> event bus`
- `workstation session / projection helpers -> event bus`
- `entry surfaces that host workstation UI -> event bus`
- `blend workflow execution as hosted by workstation -> event bus`

Disallowed direction:

- `runtime -> event bus`
- `controller -> event bus`
- `governance correctness -> event bus`
- `skill runtime correctness -> event bus`

If Blinker is used, it should sit behind a repo-local workstation event-bus wrapper.

The rest of the repo should depend on that wrapper, not on Blinker directly.

## Primary Granularity Decision

The most important implementation decision is:

**the primary composition event granularity should be the Blend workflow step lifecycle**

not:

- only whole-workflow completion
- and not only raw operator invocation

Reason:

- whole-workflow events are too coarse
- raw operator invocation is too narrow because a step may skip or block before a successful invocation exists

Therefore the implementation must support three strata.

### 1. Host / Workbench Events

For panel recomposition and host-side coordination.

### 2. Blend Step Events

For composition observability.

These are the primary execution events.

### 3. Workflow Aggregate Events

For run-level summaries and persistence.

These remain necessary but are not the main composition signal.

## State Surfaces Required

The event bus benefits from explicit workstation state surfaces, but it should not wait on the full UI-state model before becoming useful.

Implementation should therefore:

- use already-landed workstation session, workflow, activity, and projection surfaces first
- add explicit context and UI/workstation state only after the first host and step-lifecycle event slices are working

The following surfaces still matter.

### Document State

Already largely present through:

- skill store
- workflow store
- workspace attachments
- response artifacts
- imports and exports

No event-specific persistence should be added here.

### Context / Session State

The current `WorkstationSession` is not enough to express the full host-facing current situation.

Implementation should add an explicit workstation context state surface covering items such as:

- selected skill
- selected workflow plan or run
- current mode
- focused attachment or target
- active task lens
- approval boundary posture

This state should be reconstructible from session-root material rather than only existing in memory.

### UI / Workstation State

Implementation should add an explicit UI/workstation state surface covering items such as:

- active panel
- active tab
- sidebar state
- section expansion
- catalog query
- workflow detail focus

This state may be:

- persisted where continuity matters
- or ephemeral where continuity does not matter

What matters is that it becomes explicit rather than remaining hidden in widget internals.

## Event Bus Surface

Implementation should add a workstation-local event-bus module under the workstation package.

That module should provide:

- one bus object or factory
- named semantic event channels
- publish and subscribe operations
- a stable payload convention
- a best-effort failure boundary around subscriber execution

Required constraints:

- session-scoped notifications
- semantic event naming
- no widget references in payloads
- no truth-bearing authority in payloads

## Correlation Requirement

Blend step events occur before workflow persistence completes.

That means durable `workflow_id` and `workflow_run_id` may not yet exist when early events are emitted.

Implementation should therefore introduce a host-owned correlation identifier for active workflow execution, for example:

- `workflow_execution_id`

This identifier should:

- be created when workflow execution begins
- appear on all Blend step events
- appear on all workflow aggregate events emitted before persistence
- later be linked to persisted `workflow_id` and `workflow_run_id` by the workflow-persisted event

Without this, step-level observability will be hard to correlate cleanly.

## Event Families

### Host / Workbench Events

Recommended first slice:

- `turn_started`
- `turn_finished`
- `activity_event`
- `approval_requested`
- `approval_decided`
- `assistant_response_changed`
- `session_changed`
- `permissions_changed`

Deferred host/workstation events:

- `attachments_changed`
- `context_changed`
- `task_contract_changed`
- `selection_changed`
- `mode_changed`
- `focus_changed`
- `ui_state_changed`
- `panel_state_changed`
- `panel_focus_changed`
- `catalog_query_changed`

### Skill / Artifact Events

Recommended first slice:

- `skill_catalog_changed`
- `skill_import_completed`
- `skill_export_completed`

Deferred:

- `skill_lifecycle_projection_changed`

### Blend Step Events

Recommended minimum set:

- `blend_step_started`
- `blend_step_skipped`
- `blend_step_blocked`
- `blend_step_completed`
- `blend_step_failed`

These should be treated as the primary event family for skill-to-skill composition observability.

### Workflow Aggregate Events

Recommended minimum set:

- `blend_workflow_started`
- `blend_workflow_completed`
- `blend_workflow_failed`
- `blend_workflow_persisted`

These are aggregate and container-level.

## Step Event Payload Discipline

Each Blend step event should carry enough information for host-owned observers to understand the step without turning the payload into a second store.

Required fields:

- session id
- workstation root path
- event kind
- timestamp
- `workflow_execution_id`
- `step_id`
- `iteration`

Where applicable it should also include:

- resolved operator id
- resolved operator name
- operator kind
- invocation id
- resolved target
- semantic unit
- input summary
- output summary
- status
- policy summary
- delegation summary
- binding receipts
- condition receipts

`binding_receipts` and `condition_receipts` should travel with step events.

They should not normally become their own top-level event firehose.

## Workflow Aggregate Payload Discipline

Workflow aggregate events should carry:

- session id
- workstation root path
- event kind
- timestamp
- `workflow_execution_id`

Where available they should also include:

- durable `workflow_id`
- durable `workflow_run_id`
- aggregate status
- final output step
- final answer summary
- blocked step id when applicable
- requested operator names

`blend_workflow_persisted` should be the event that binds:

- `workflow_execution_id`

to:

- `workflow_id`
- `workflow_run_id`

## Publication Points In The Current Codebase

Implementation should publish from existing mutation points rather than inventing shadow pathways.

### Workstation Turn Lifecycle

In [workstation/runtime_core/src/workstation/runtime/core/session.py](workstation/runtime_core/src/workstation/runtime/core/session.py):

- publish `turn_started` when prompt execution begins
- publish `task_contract_changed` after task-contract materialization
- publish `assistant_response_changed` after response materialization
- publish `turn_finished` at the end of the turn

### Durable Receipt Append

Publication should happen immediately after durable receipt append, not before.

This should cover:

- prompt receipt
- capability receipt
- approval requested receipt
- approval decision receipt
- assistant response receipt

This is where `activity_event`, `approval_requested`, and `approval_decided` should be derived.

### Session Mutation

In [workstation/workstation_core.py](workstation/workstation_core.py):

- publish `session_changed`
- publish `permissions_changed`

only after session persistence succeeds.

### Skill Catalog Mutation

In [workstation/capabilities.py](workstation/capabilities.py):

- publish `skill_import_completed` after import succeeds
- publish `skill_catalog_changed` after import succeeds
- publish `skill_export_completed` after export succeeds
- publish `skill_lifecycle_projection_changed` when workstation-visible lifecycle or admission projection changes materially

### Workflow Aggregate Publication

In [blend_workflow_execution.py](blend_workflow_execution.py):

- publish `blend_workflow_started` when workflow execution begins and the `workflow_execution_id` is created
- publish `blend_workflow_completed` when the workflow concludes successfully
- publish `blend_workflow_failed` when the workflow concludes unsuccessfully
- publish `blend_workflow_persisted` after workflow plan/run persistence succeeds

## Required Step-Lifecycle Publication Seam

The most important implementation change is this:

step events must be emitted from the actual step-execution path, not reconstructed later from final workflow summaries.

The current code splits step behavior across:

- [blend_workflow_execution.py](blend_workflow_execution.py)
- [skill_composition.py](skill_composition.py)

`skill_composition.py` currently owns:

- skip behavior
- condition evaluation
- binding receipts
- iteration

`blend_workflow_execution.py` currently owns:

- operator resolution
- operator invocation creation
- step-result aggregation
- workflow result shaping

Therefore implementation should add a composition-observer seam so step events are emitted at the correct temporal boundary.

That seam should let the host receive notifications for:

- step skipped
- step started
- step blocked
- step completed
- step failed

with real iteration and binding data at the time those facts become true.

The step event stream should not be synthesized only after the workflow finishes.

## Step Event Semantics In The Current Engine

Implementation should align event meanings with the current engine.

### `blend_step_skipped`

Emit when `run_if` conditions prevent execution.

This should include:

- condition receipts
- iteration
- no invocation id

### `blend_step_started`

Emit when:

- conditions are satisfied
- bindings have been materialized into the step payload
- a real step iteration is about to execute

This should include:

- binding receipts
- condition receipts
- invocation id when created

### `blend_step_blocked`

Emit when a step cannot proceed because of a lawful boundary such as:

- approval requirement
- delegation insufficiency
- unsupported delegation
- target or applicability boundary

When a real invocation exists, include the invocation id.

When the block happens before invocation, do not invent one.

### `blend_step_completed`

Emit after a step iteration completes successfully.

This should include:

- output summary
- parsed-output summary
- result summary
- binding receipts
- condition receipts

### `blend_step_failed`

Emit when a step iteration executes and terminates unsuccessfully.

This should include:

- failure summary
- error summary
- binding receipts
- condition receipts

## Subscriber Strategy

### Chat UI

In [workstation/chat_ui.py](workstation/chat_ui.py):

- activity panes should subscribe to host activity events and Blend step events
- response and transcript surfaces should subscribe to `assistant_response_changed`
- context-sensitive suggestion surfaces should subscribe to session, context, and catalog events

The existing receipt tail should remain a fallback and replay path.

The chat UI must not become dependent on delivered events for correctness.

### Flutter Host

In the Flutter workstation host:

the current dashboard is mostly snapshot-based.

Implementation should add a session-bound dashboard controller that:

- subscribes to the event bus
- decides which panels are invalidated
- rebuilds those panels from the existing projection builders in [workstation/workstation_core.py](workstation/workstation_core.py)

This is where the event bus adds the most architectural value.

### Projection Builders

Projection builders should remain pure read-model builders.

They should not become stateful event subscribers by default.

The better pattern is:

- host controller subscribes
- host controller requests recomputation from projection builders
- host controller rerenders panels

## Required Operator Additions

The event bus will remain incomplete until the workstation has explicit context and UI operators.

Recommended first context operators:

- select skill
- select workflow run
- set mode
- focus attachment
- set active task lens

Recommended first UI/workbench operators:

- open panel
- set active tab
- toggle sidebar
- expand section
- set catalog query

Those operators should:

- mutate explicit context/UI state
- then publish host/workstation events

## Rollout Plan

## Corrected Rollout Order

The practical rollout should prioritize semantically meaningful execution visibility before a broad UI-state model.

The corrected order is:

1. workstation-local event bus wrapper
2. host/session/catalog/receipt publication from existing workstation mutation points
3. Blend step-lifecycle publication with `workflow_execution_id`
4. subscriber controllers for shell/Flutter recomposition
5. broader explicit context/UI state modeling

This matches the current codebase better because:

- workstation persistence and projection seams already exist
- workflow execution and persisted workflow objects already exist
- Textual and Flutter hosts already exist as projection surfaces
- explicit durable UI-state modeling is still additive and should follow proven event consumers rather than precede them

## Rollout Plan

### Phase 1: Introduce A Workstation-Local Bus Wrapper

Deliverables:

- repo-local event-bus abstraction
- semantic event catalog
- typed event envelope / payload convention
- no broad direct dependency on Blinker

Acceptance:

- workstation can publish and subscribe in-process
- subscriber failure does not corrupt state mutation

### Phase 2: Add Host / Workbench Publication From Existing Mutation Points

Deliverables:

- publication from turn lifecycle
- publication from receipt append
- publication from session mutation
- publication from skill import/export mutation

Acceptance:

- current workstation behavior remains green
- host-owned panels can react without polling-only behavior

### Phase 3: Add Blend Step-Lifecycle Publication

Deliverables:

- `workflow_execution_id`
- composition observer seam
- Blend step event emission during real execution
- workflow aggregate event emission above it

Acceptance:

- host can observe step ordering, step iteration, step skip, step block, step completion, and step failure in real time

### Phase 4: Rework Host UI Surfaces To Subscribe And Recompose

Deliverables:

- chat surfaces subscribing to step and host events
- Flutter dashboard controller subscribing to step and host events
- retained rebuild-from-state fallback

Acceptance:

- no direct panel-to-panel control is required for meaningful coordination
- missed events do not invalidate correctness

### Phase 5: Add Explicit Context And UI State Surfaces

Deliverables:

- context-state model
- UI-state model
- persistence and projection rules

Acceptance:

- host-owned coordination is no longer trapped in widget-local state

## What Not To Implement

Do not implement the event bus as:

- a replacement for receipts
- a replacement for workflow persistence
- a mandatory dependency of skills
- a mandatory dependency of runtime or controller correctness
- a workflow-only event surface with no step-level visibility
- an edge-event firehose for every successful trivial mapper application
- a panel-to-panel imperative RPC layer
- a carrier of raw widget references and mutable GUI objects

Do not model semantic correctness as:

- “if the event fired, the fact is true”

The correct rule remains:

- if durable or reconstructible state says it is true, it is true
- the event only tells the host to look again

## Validation Strategy

Validation must cover host coordination, step-level execution observability, aggregate workflow events, and missed-event recovery.

### Unit Scenarios

1. Event publication and subscription within one workstation session process.
2. Subscriber isolation so one failing subscriber does not corrupt state mutation.
3. Session scoping so one session does not spuriously notify unrelated subscribers.
4. Payload discipline so events carry identifiers and summaries, not mutable GUI authority.
5. No architectural leak so runtime and controller remain free of required event-bus imports.

### Host / Workbench Scenarios

1. Permission grant emits `session_changed` and `permissions_changed` only after durable session persistence.
2. Assistant response update emits `assistant_response_changed` only after response materialization.
3. Receipt append emits corresponding activity or approval notification only after durable receipt append.
4. Skill import updates the catalog projection without requiring a host restart.
5. Flutter or equivalent host panels recompose from shared state without direct panel-to-panel control.

### Blend Step Scenarios

1. A successful one-step workflow emits, in order:
   - `blend_workflow_started`
   - `blend_step_started`
   - `blend_step_completed`
   - `blend_workflow_completed`
   - `blend_workflow_persisted`

2. A step skipped by `run_if` emits `blend_step_skipped` with condition receipts and no invocation id.

3. A step blocked by approval or delegation emits `blend_step_blocked` rather than `blend_step_failed`.

4. A step that executes and errors emits `blend_step_failed`.

5. An iterative step emits multiple step events with the same `step_id` but different `iteration` values.

6. Step events carry binding receipts and condition receipts relevant to that iteration.

7. Step events can be correlated to the enclosing workflow through `workflow_execution_id` before durable workflow ids exist.

### Workflow Aggregate Scenarios

1. Workflow completion emits aggregate events distinct from step events.
2. Workflow failure emits aggregate failure even when step failure or blocking has already been emitted.
3. Workflow-persisted event binds the active `workflow_execution_id` to durable `workflow_id` and `workflow_run_id`.
4. Panels that only care about aggregate summaries can subscribe to workflow events and ignore step events.

### Missed-Event Recovery Scenarios

1. A subscriber that attaches late can reconstruct correct state from stores, session files, and receipts.
2. A temporarily disconnected subscriber does not cause semantic drift.
3. Restarting the host UI after a run reconstructs the correct workflow and activity projections from durable truth.

### Negative Scenarios

1. No test should require delivered events for workstation correctness.
2. No semantic action should lose its durable receipt because an event path exists.
3. No implementation should emit every successful trivial mapper application as a top-level event by default.
4. No host panel should be forced to trust pushed payloads as authority over durable state.

## Minimum Acceptance Bar

The event bus should be considered correctly integrated only when all of the following are true:

- durable state remains authoritative
- receipts remain intact and replayable
- host-owned panels recompose without direct coupling
- Blend composition is visible at the step lifecycle level
- workflow aggregate events remain available above step events
- missed events do not invalidate correctness
- runtime and controller layers remain architecturally clean

That is the implementation target that best fits this repo.
