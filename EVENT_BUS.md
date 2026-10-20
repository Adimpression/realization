# Event Bus

Formal architecture note for a host-owned workstation event bus.

This document defines the formal need, architectural position, and event model for an event bus in the current repo.

It does not define the rollout details.

Those are covered by [EVENT_BUS_IMPLEMENTATION.md](EVENT_BUS_IMPLEMENTATION.md).

## Purpose

The workstation already has:

- durable state
- durable receipts
- governed skills
- Blend workflows
- projection builders
- host-owned session control

What it does not yet have as a first-class surface is an explicit in-process notification substrate for:

- host-owned inter-panel recomposition
- host-owned observation of Blend composition as it unfolds

This is the gap the event bus is meant to fill.

## Architectural Position

The event bus belongs to the **Workstation** layer and to host-owned UI and coordination surfaces above it.

It does not belong to:

- Runtime + Skill Execution
- Controller
- Governance
- the shared host-interaction substrate as a correctness dependency

Reason:

- the bus is about host-owned coordination and observability
- it is not a persistence substrate
- it is not the controller
- it is not the runtime
- it is not the source of truth

## Two Problems The Event Bus Must Solve

The event bus must solve two different but related problems.

### 1. Host / Workbench Recomposition

When one host-owned panel or operator changes session, context, UI, or history state, dependent projections should know to recompute without direct panel-to-panel control.

### 2. Blend Composition Observability

When a Blend workflow executes across multiple skills or capabilities, the host should be able to observe the composition as a sequence of lawful operations rather than only seeing one final workflow result.

This second problem is critical.

For composition, the event bus must not stop at workflow-level completion events.

## Formal Pattern

For workstation recomposition, the intended pattern is:

**Panel -> Operator -> Shared State Transition -> Event Emission -> Dependent Panel Recomposition**

Not:

**Panel -> Panel imperative control**

For Blend composition, the intended pattern is:

**Workflow -> Step Resolution -> Step Lifecycle -> Workflow Outcome**

Not:

**Workflow -> final result only**

## Blend Reading

In Blend terms, the event bus is not itself `DNA`, `RNA`, or an `Operator`.

It sits in the coordination space between:

- `Operators`
- `Context`
- `UI Abstraction`
- `Session`
- `History`

Practical reading:

- `DNA` remains the durable semantic and artifact-bearing substrate
- `RNA` remains the shaping and interpretation substrate
- `Operators` remain the lawful verbs
- `Context` remains active situated state
- `UI Abstraction` remains actor-facing projection over shared state
- `History` remains receipts, traces, and replay surfaces
- the event bus is the host-owned notification seam by which lawful state transitions become immediately visible to host-owned projections

The bus supports Blend.

It does not replace Blend.

## Event Strata

The event model should be understood as three strata.

### 1. Host / Workbench Events

These are for workstation recomposition and host-owned coordination.

They cover changes such as:

- session mutation
- capability grant or revocation
- context selection
- mode change
- active panel or tab change
- activity and response updates
- approval boundary updates

### 2. Blend Step Events

These are the **primary event granularity for composition**.

This is the key architectural point.

When a Blend workflow runs, the meaningful semantic execution unit is not only the whole workflow run.

It is the **workflow step lifecycle**.

Each workflow step is a lawful operation.

Each step resolves to an operator.

Each step may:

- be skipped
- be blocked
- start execution
- complete
- fail
- repeat under iteration

This means the correct public event unit for composition is not the raw operator alone and not the whole workflow alone.

It is the **Blend workflow step lifecycle**, with operator invocation as the executable core of that step.

### 3. Workflow Aggregate Events

These remain necessary, but they are aggregate and container-level.

They describe:

- workflow start
- workflow completion
- workflow failure
- workflow persistence

They are not sufficient as the primary composition event surface.

## Primary Composition Unit

The primary event unit for composition should be the **Blend workflow step lifecycle**.

This is the right middle position for the current codebase.

Why it should not be only the workflow:

- that is too coarse
- it hides actual semantic progression
- it is weak for inspector panels, HITL review, and composition debugging

Why it should not be only the raw operator invocation:

- a step may be skipped before invocation
- a step may be blocked before successful invocation
- conditions and bindings are evaluated around the step
- iteration is step-scoped, not only invocation-scoped

So the public semantic unit should be:

- the step lifecycle

with:

- the `BlendOperatorInvocation` as the executable core when execution actually occurs

## Step Lifecycle Semantics

The step lifecycle should distinguish at least the following statuses.

### `blend_step_started`

Emitted when a step enters execution for a specific iteration after its preconditions are satisfied and an invocation is about to occur.

### `blend_step_skipped`

Emitted when a step does not run because its conditions do not permit execution.

This is not failure.

### `blend_step_blocked`

Emitted when the step cannot proceed because of a lawful boundary such as:

- approval requirement
- delegation insufficiency
- policy or applicability boundary
- target-resolution boundary

This is not the same thing as a terminal execution failure.

### `blend_step_completed`

Emitted when the step successfully produces its result for a specific iteration.

### `blend_step_failed`

Emitted when the step attempts execution and terminates unsuccessfully.

## What A Step Event Represents

A step event represents:

- one step
- for one iteration
- under one workflow execution
- with one resolved operator identity
- with one operator invocation when applicable

It should therefore carry:

- step identity
- iteration
- resolved operator identity
- invocation identity when actual invocation exists
- resolved target
- relevant context summary
- input summary
- output or failure summary
- condition receipts
- binding receipts
- delegation and policy summary where relevant

## Binding And Mapping Semantics

Step-to-step field mapping is important, but it should not dominate the event surface.

The current architecture already treats trivial mapping as edge-local semantics:

- `identity`
- `rename`
- `first_item`
- `project_field`

This is correct.

Those transformations are still important to observability, but their natural place is as **receipts attached to step events**, not as the primary top-level event stream.

Therefore:

- step events should carry binding receipts and condition receipts
- successful binding should not, by default, become a separate top-level event firehose

If a future debugger mode needs explicit edge events, those should be additive and secondary.

They should not define the primary architecture.

## Truth Model

The governing rule remains:

**state is truth; events are notification**

This means:

- durable artifacts, workflow stores, session files, and receipts remain authoritative
- event delivery may be lossy or ephemeral
- missing an event must not corrupt correctness
- any subscriber must be able to rebuild from shared state

This rule applies equally to:

- host/workstation events
- step events
- workflow aggregate events

## Event Bus Responsibilities

The event bus should:

- notify host-owned panels and services that relevant state transitions occurred
- let multiple projections react to one operator or one step without direct coupling
- provide immediate host-side observability for Blend composition
- mirror durable state changes into immediate in-process notifications
- preserve the principle that subscribers reread shared state rather than trusting pushed authority

The event bus should not:

- become the source of truth
- replace receipts
- replace stores
- replace session persistence
- replace workflow persistence
- become the controller
- become the runtime

## Relation To Receipts

Receipts remain first-class.

The event bus should be treated as an in-process convenience over durable history, not as a substitute for durable history.

Consequences:

- receipt emission remains mandatory where audit is required
- event emission may occur immediately after durable receipt append
- host-owned activity panes may react to the event bus for responsiveness
- those same panes must still be reconstructible from durable receipts

The workstation must remain understandable under replay even when no subscribers are running.

## Relation To Skills, BlendOperators, And Workflows

The event bus does not change the semantic granularity rules for execution surfaces.

The current intended split remains:

- trivial field-level mapping stays edge-local
- meaningful semantic transforms become BlendOperators
- larger reusable governed behaviors remain skills

The bus should report this world faithfully.

That means:

- the primary composition event unit is the step lifecycle
- operator identity is embedded in that lifecycle
- workflow lifecycle remains aggregate
- edge receipts remain subordinate evidence carried by step events

## What Not To Do

Do not:

- make workflow aggregate events the only composition execution surface
- make every successful field binding a top-level event by default
- make raw operator invocation the only public event unit when steps may skip or block before invocation
- make the event bus the source of truth
- make panels depend on direct control of each other
- make runtime or controller correctness depend on event delivery
- substitute event history for receipt history
- push mutable truth-bearing objects to subscribers as authority
- let subscriber side effects become the only place where meaningful state changes happen

## Non-Goals

The event bus is not meant to:

- replace the shared host-interaction substrate
- replace `BlendContext`
- replace workflow execution records
- replace artifact stores
- solve distributed coordination by itself
- redefine trivial mappers as first-class operators merely for observability

## Design Consequence

The correct design consequence for the current repo is:

- host/workstation events for recomposition
- Blend step events as the primary composition event surface
- workflow aggregate events as container-level summaries
- durable receipts and stores as the enduring truth

That is the event model that best fits the current Blend-shaped codebase.
