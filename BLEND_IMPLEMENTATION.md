# Blend Implementation

Implementation plan for moving the current codebase toward the full Blend model described in [BLEND.md](BLEND.md) and made more concrete in [BLEND_EXPANDED.md](BLEND_EXPANDED.md).

This is a staged plan.

It is not a rewrite plan.

The main constraint is:

- preserve current controller, governance, learning, workstation, and trial behavior while making Blend layers explicit

## Purpose

Blend gives us the right long-term architecture vocabulary:

- `DNA`
- `RNA`
- `Operators`
- `Context`
- `UI Abstraction`
- `Actor`
- `Session`
- `Workflow`
- `Policy`
- `History`
- `Coordination`
- `Agent Orchestration`

The repo already contains substantial pieces of this model, but they are unevenly explicit.

The purpose of this file is to:

- map current code to Blend layers
- identify what is missing
- define the order in which to make those missing parts first-class
- keep the migration grounded in the existing codebase rather than inventing a second architecture beside it

## Core Reading Of Blend For This Repo

The most important practical reading from [BLEND.md](BLEND.md) and [BLEND_EXPANDED.md](BLEND_EXPANDED.md) is:

- the system is a world, not a set of screens
- UI is a projection of semantics plus context
- operators are the lawful verbs of the world
- context is not just “extra metadata”; it is active situated state
- actors, sessions, workflows, policy, and history are not optional once the system becomes work-grade
- automation and AI must appear as explicit actors with explicit plans and limits

For this repo, the user’s decomposition is the correct working one:

- knowledge
  - primarily `DNA`
- prolog
  - `DNA + Operators`
- functions
  - `DNA + Operators`
- leaves
  - primarily `RNA`
  - especially when enriched with labels, descriptions, path meaning, and types
- context
  - mappings plus workstation/controller active state
- UI
  - actor-facing interaction projection
  - AI tool surface, deterministic automation surface, or HITL surface
- actor
  - AI, deterministic automation, or human/HITL

That means a skill is not “one Blend layer.”

A hosted skill is a cross-layer packet:

- persisted body and declarations
- reflective semantic normalization
- invocable operators
- contextual execution rules
- policy-constrained use
- history-bearing execution

## Scope

In scope:

- making Blend layers explicit where they are currently implicit
- first-class session and workflow objects
- stronger actor attribution and actor projection
- context as a shared modeled substrate, not just ad hoc prompt/session state
- explicit operator and workflow representations for skills and host actions
- history and policy that narrate and constrain real runs
- future UI projection surfaces for AI, automation, and HITL

Out of scope for the first cuts:

- replacing the current controller with the workstation
- replacing the workstation shell with a completely different UI stack
- forcing all execution runtimes into Wasmtime
- rewriting existing skill/governance/trial systems from scratch

## Current Codebase Mapping

The repo is already partially Blend-shaped.

### DNA

Current DNA-heavy surfaces:

- [applied_theory_types.py](applied_theory_types.py)
- [artifact.py](artifact.py)
- [store.py](store.py)
- [system_state.py](system_state.py)
- [skill_schema_io.py](skill_schema_io.py)
- [skill_export_projection.py](skill_export_projection.py)
- [run_bundle_io.py](run_bundle_io.py)

Current position:

- persisted artifacts, skill bundles, stores, governance records, and run bundles exist
- persistent truth is artifact-centered
- this should remain the base persistence substrate

### RNA

Current RNA-heavy surfaces:

- [skill_leaf_types.py](skill_leaf_types.py)
- [skill_path_notation.py](skill_path_notation.py)
- [skill_boundary_normalization.py](skill_boundary_normalization.py)
- [skill_ir.py](skill_ir.py)
- [title_semantics.py](title_semantics.py)
- [semantic_text.py](semantic_text.py)
- [skill_governance.py](skill_governance.py)

Current position:

- canonical leaf ledgers now exist
- canonical path notation exists
- portable skills have an initial compiler seam and IR
- meaning is still scattered across multiple modules and not yet projected uniformly into workflow/session/UI layers

### Operators

Current operator-heavy surfaces:

- [skill_composition.py](skill_composition.py)
- [execution_frameworks.py](execution_frameworks.py)
- [host_brokers.py](host_brokers.py)
- [host_interaction_actions.py](host_interaction_actions.py)
- [workstation/capabilities.py](workstation/capabilities.py)
- [workstation/skill_invocation.py](workstation/skill_invocation.py)

Current position:

- named skill and host operators exist
- composition operators now exist at leaf level
- an additive shared operator catalog/query seam now exists below workstation, with shared provider factories and workflow-step-aware resolution; it is still session-contextual and not yet a broader cross-runtime registry
- operator execution is no longer purely capability-centric in the workflow path: `BlendContext` now participates directly in operator applicability, target resolution, and shared-world checks there, but not yet across every controller/runtime action path

### Context

Current context-heavy surfaces:

- [workstation/foundation_models/src/workstation/foundation/models/models.py](workstation/foundation_models/src/workstation/foundation/models/models.py)
- [workstation/runtime_core/src/workstation/runtime/core/session.py](workstation/runtime_core/src/workstation/runtime/core/session.py)
- [workstation/task_contract.py](workstation/task_contract.py)
- [host_interaction_context.py](host_interaction_context.py)
- [host_interaction_delegation.py](host_interaction_delegation.py)
- [virtual_mounts.py](virtual_mounts.py)

Current position:

- workstation active state is the strongest concrete context surface today
- host interaction substrate is becoming shared
- context is still mostly operational and local, not a fully modeled first-class Blend layer with uniform projections
- additive `BlendContext` exists and the shared workflow/operator path now consumes it directly, but broader controller/runtime action paths still need to move onto that contract

### UI Abstraction

Current UI-abstraction surfaces:

- [workstation/chat_ui.py](workstation/chat_ui.py)
- [workstation/chat_commands.py](workstation/chat_commands.py)
- [workstation/activity_view.py](workstation/activity_view.py)

Current position:

- the workstation chat is already a meaningful actor-facing projection
- activity/transcript/input panes are the beginning of reusable interface grammar
- shared workstation layout now drives Textual tab labels plus the corresponding Flutter chat, gather, and read-only panel titles
- but the UI layer is still shell-first and not yet explicitly driven by a generalized projection model over DNA + RNA + operators + context

### Actor

Current actor-heavy surfaces:

- [workstation/llm_driver.py](workstation/llm_driver.py)
- [host_interaction_receipts.py](host_interaction_receipts.py)
- [approval_governance.py](approval_governance.py)

Current position:

- actor attribution exists in traces and in practical behavior
- AI and human are operationally distinct
- deterministic automation is not yet modeled as a first-class actor type across the same interaction model

### Session

Current session-heavy surfaces:

- [workstation/runtime_core/src/workstation/runtime/core/session.py](workstation/runtime_core/src/workstation/runtime/core/session.py)
- [workstation/foundation_models/src/workstation/foundation/models/models.py](workstation/foundation_models/src/workstation/foundation/models/models.py)
- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)

Current position:

- workstation sessions are concrete and useful
- controller/runtime has bounded run/resume state
- but there is not yet one explicit Session model spanning:
  - actor
  - active workspace
  - active workflow
  - transient caches
  - approval state
  - undo/replay scope
  - active projections

### Workflow

Current workflow-heavy surfaces:

- [skill_composition.py](skill_composition.py)
- [workstation/skill_composition_planning.py](workstation/skill_composition_planning.py)
- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)

Current position:

- explicit skill composition plans now exist
- controller reduction already represents structured multi-step work
- but workflow is not yet a first-class persisted or inspectable world object

### Policy

Current policy-heavy surfaces:

- [skill_governance.py](skill_governance.py)
- [workstation/governance.py](workstation/governance.py)
- [workstation/capabilities.py](workstation/capabilities.py)
- [runtime_governance_context.py](runtime_governance_context.py)

Current position:

- policy is already one of the stronger parts of the system
- permissions, approvals, risk tiers, and delegation are explicit
- policy still needs to be projected uniformly into actor/session/workflow/UI surfaces

### History

Current history-heavy surfaces:

- [host_interaction_receipts.py](host_interaction_receipts.py)
- [constitutional_trace.py](constitutional_trace.py)
- [run_bundle_io.py](run_bundle_io.py)
- [workstation/activity_view.py](workstation/activity_view.py)

Current position:

- history and receipts are already valuable and visible
- they are still mostly invocation/event centric
- workflow-level history is not yet modeled explicitly enough

### Coordination

Current coordination-heavy surfaces:

- approval and review traces
- governance overlays
- shared store/state

Current position:

- there are pieces of coordination, but no strong explicit coordination layer yet
- coordination should not be added as chat-only convention; it needs real objects and rules

### Agent Orchestration

Current agent-orchestration surfaces:

- [workstation/llm_driver.py](workstation/llm_driver.py)
- [workstation/direct_composition.py](workstation/direct_composition.py)
- [workstation/skill_composition_planning.py](workstation/skill_composition_planning.py)
- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)

Current position:

- explicit AI participation exists
- explicit compose-plan execution exists
- orchestration is still split between controller reduction and workstation planning loops

## Current Architectural Verdict

The repo is:

- stronger than a minimal Blend system
- approaching a work-grade Blend system in some areas
- not yet a full work-grade Blend system overall
- not yet a pipeline-grade Blend system

The strongest implemented layers today are:

- `DNA`
- `RNA`
- `Operators`
- `Policy`
- `History`

The least first-class layers today are:

- `Session`
- `Workflow`
- `Coordination`
- generalized `UI Abstraction`
- actor-projection model across AI, automation, and HITL

## Governing Implementation Principles

### 1. Do not invent a second world model

Blend should be implemented by making the current artifact/governance/workstation/runtime world more explicit.

It should not introduce a disconnected parallel architecture.

### 2. UI is projection, not source of truth

The prompt_toolkit workstation chat is one projection surface.

Future automation and HITL surfaces should project the same semantics, not build separate hidden models.

### 3. Context must become modeled state

`Context` should not remain only:

- temporary local variables
- prompt heuristics
- ad hoc session dicts

It should become a shared substrate for:

- selection
- active workspace/mounts
- mode
- actor identity
- granted capabilities
- current workflow position
- pending approvals

### 3.5. Context must become an explicit operator input

The Blend examples are concrete about this:

- operators are verbs
- context is the current situation
- verbs become meaningful only when applied under context

So `BlendContext` should not only exist as:

- a projection
- a discovery artifact
- an ambient place to look up defaults

It should participate directly in operator behavior:

- applicability
- target resolution
- policy narrowing
- visibility/affordance
- execution

Conceptually, the operator model is not just:

- `operator(inputs) -> outputs`

It is closer to:

- `operator(context, inputs) -> outputs`

or, when actor/session/policy are carried explicitly:

- `operator(actor, session, context, inputs) -> outputs`

The implementation does not need that exact function signature everywhere, but the plan should treat it as the semantic model.

### 4. Workflow must become a world object

The current compose plans are a start, but Blend requires more than ephemeral execution payloads.

We need explicit:

- plan objects
- run objects
- branch state
- checkpoints
- handoff state
- outcomes

### 5. Actor types must share one semantic core

AI, deterministic automation, and HITL should differ by projection and authority, not by incompatible execution models.

### 6. Policy and history must be visible in projection layers

Policy and history already exist.

The next move is not to invent them, but to project them cleanly into:

- workflow execution
- UI surfaces
- actor-visible state

## Proposed First-Class Objects

These are the next missing Blend objects that should become explicit.

### `BlendSession`

Purpose:

- represent a bounded working episode

Fields should include:

- session id
- actor identity and actor kind
- root workspace or active attachment set
- active workflow id
- current context state
- granted capabilities
- pending approvals
- transient caches
- start/end timestamps
- active projection kind

Suggested home:

- new root module: `blend_session.py`
- workstation can adapt to it
- controller/runtime can consume a lower-level version of it

### `BlendWorkflowPlan`

Purpose:

- represent intended goal-oriented work above single operator execution

Fields should include:

- workflow id
- title / goal
- actor scope
- steps
- bindings
- mapper functions
- conditions
- branch points
- iteration rules
- preconditions
- expected outputs
- policy requirements

Suggested home:

- new root module: `blend_workflow.py`

### `BlendWorkflowRun`

Purpose:

- represent one execution of a workflow plan

Fields should include:

- run id
- workflow id
- session id
- per-step state
- mapped inputs
- operator outputs
- branch decisions
- approval state
- failures / retries
- final outputs
- timestamps

Suggested home:

- same `blend_workflow.py` or adjacent `blend_workflow_run.py`

### `BlendOperator`

Purpose:

- represent one lawful verb of the world with explicit contextual applicability

Fields should include:

- operator id
- operator kind
- display name
- semantic description
- declared input shape
- declared output shape
- policy requirements
- actor visibility
- context requirements
- context applicability rules
- target resolution rules
- execution adapter identity

Suggested home:

- new root module: `blend_operator.py`

### `BlendOperatorInvocation`

Purpose:

- represent one concrete application of an operator under a specific context

Fields should include:

- invocation id
- operator id
- actor/session/workflow refs
- context snapshot or context ref
- explicit inputs
- resolved target
- policy decision state
- outputs
- emitted history/receipt refs

Suggested home:

- same `blend_operator.py` or adjacent `blend_operator_run.py`

### `BlendActor`

Purpose:

- normalize actor identity across AI, deterministic automation, and HITL

Fields should include:

- actor id
- actor kind
  - `human`
  - `ai`
  - `automation`
- display name
- capability envelope
- attribution/provenance metadata

Suggested home:

- new root module: `blend_actor.py`

### `BlendProjection`

Purpose:

- represent how the same semantic world is presented to a given actor surface

Examples:

- workstation chat projection
- deterministic API projection
- HITL review projection

Fields should include:

- projection kind
- actor kind
- visible objects
- visible operators
- context summary
- policy overlays
- history slice
- interaction affordances

Suggested home:

- new root module: `blend_projection.py`

### `BlendContext`

Purpose:

- make current situation explicit and portable across controller/runtime/workstation/UI

Fields should include:

- selected objects
- active document/workspace
- mode
- focus
- viewport/tool state where relevant
- current role/capability state
- workflow position
- pending approval focus

Suggested home:

- new root module: `blend_context.py`

## Concrete Mapping From Current Code To Future Blend Objects

The migration should mostly wrap and factor existing surfaces.

### `BlendSession`

Should be built from:

- [workstation/foundation_models/src/workstation/foundation/models/models.py](workstation/foundation_models/src/workstation/foundation/models/models.py)
- [workstation/runtime_core/src/workstation/runtime/core/session.py](workstation/runtime_core/src/workstation/runtime/core/session.py)
- [host_interaction_context.py](host_interaction_context.py)
- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)

### `BlendWorkflowPlan` and `BlendWorkflowRun`

Should extend:

- [skill_composition.py](skill_composition.py)
- [workstation/skill_composition_planning.py](workstation/skill_composition_planning.py)
- controller reduction structures in [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py)

### `BlendOperator` and `BlendOperatorInvocation`

Should be built from:

- [workstation/capabilities.py](workstation/capabilities.py)
- [host_interaction_actions.py](host_interaction_actions.py)
- [host_interaction_action_dispatch.py](host_interaction_action_dispatch.py)
- [workstation/skill_invocation.py](workstation/skill_invocation.py)
- [blend_context.py](blend_context.py)

Key rule:

- every operator surface should be able to answer not only “what are the inputs, outputs, and policy?”
- but also “under what `BlendContext` is this operator meaningful right now?”

### `BlendProjection`

Should first wrap:

- [workstation/chat_ui.py](workstation/chat_ui.py)
- [workstation/chat_commands.py](workstation/chat_commands.py)
- [workstation/activity_view.py](workstation/activity_view.py)

Later it should also support:

- deterministic API projections
- HITL review/action projections

### `BlendActor`

Should first normalize attribution already present in:

- receipts
- approvals
- LLM driver
- automation/service entrypoints

## Implementation Phases

The right order follows the Blend strata, but in a way that preserves current behavior.

### Phase 0 — Inventory And Invariants

Goal:

- explicitly record how current modules map to Blend layers
- define invariants for each new Blend object

Deliverables:

- this file
- layer-to-module map
- object invariants for session, workflow, actor, context, projection

Validation:

- documentation review
- no code changes required

### Phase 0.5 — Planner Widening On The Existing Leaf Substrate

Goal:

- widen composition planning before Blend substrate injection

Reason:

- the repo now already has a real leaf/mapping substrate
- it already has executable composition through [skill_composition.py](skill_composition.py)
- it already has workstation execution through `ws.skill.compose`
- it already has mapper functions over leaves across calls

That means the next practical move is not to stop and re-found everything first.

It is to widen the planner on top of what already works:

- beyond narrow two-step prompts
- into richer bounded multi-step plans
- into bounded conditional plans
- into bounded branching plans
- into bounded iterative plans
- while keeping the same explicit leaf/mapping substrate

Changes:

- extend [workstation/skill_composition_planning.py](workstation/skill_composition_planning.py)
- extend [skill_composition.py](skill_composition.py)
- keep mapper semantics explicit and function-based over leaves
- increase trial-backed composition coverage over real skills
- keep the resulting plans inspectable and bounded

Important constraint:

- planner widening here is still over explicit composition plans and explicit mapper functions
- it should not regress into opaque prompt chaining

Validation:

- expand [tests/test_skill_composition.py](tests/test_skill_composition.py)
- expand workstation composition regressions in [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)
- keep partial real workstation trial slices green, starting with `python` and `ansible`
- use partial real trial slices while widening:
  - `python`
  - `ansible`
  - then broader slices as stability improves

Exit condition:

- the planner can synthesize richer explicit workflow-shaped skill compositions over the current leaf substrate

### Phase 1 — Context And Session Substrate

Goal:

- make `Context` and `Session` first-class below workstation shell code

Changes:

- add `blend_context.py`
- add `blend_session.py`
- project workstation session state into `BlendSession`
- add controller/runtime-facing session/context adapters
- keep workstation behavior unchanged externally

Current implemented first cut:

- additive [blend_context.py](blend_context.py)
- additive [blend_session.py](blend_session.py)
- workstation projection into `BlendContext` and `BlendSession`
- additive discovery files:
  - `BLEND_CONTEXT.json`
  - `BLEND_SESSION.json`
- no behavior change to prompt/runtime execution paths
- validated by:
  - [tests/test_blend_session.py](tests/test_blend_session.py)
  - [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)

Sequencing note:

- this phase happens after planner widening, not before it
- Blend injection should land under an already proven composition substrate rather than blocking that expansion

Key rule from [BLEND_EXPANDED.md](BLEND_EXPANDED.md):

- context affects:
  - operator applicability
  - visibility
  - permissions
  - projection behavior

Validation:

- new unit tests for context/session objects
- workstation regression suite
- controller/runtime hygiene tests
- partial trial slices

### Phase 1.5 — Operator Contract And Contextual Applicability

Goal:

- make operators explicit context-applied verbs before widening workflow/projection machinery further

Changes:

- add `blend_operator.py`
- define:
  - `BlendOperator`
  - `BlendOperatorInvocation`
- require operator descriptors to expose:
  - input shape
  - output shape
  - policy envelope
  - actor visibility
  - context requirements
  - applicability rules
  - target resolution rules
- make `BlendContext` an explicit input to:
  - operator applicability checks
  - operator target resolution
  - policy narrowing
  - execution adapters
- adapt current operator surfaces into this model:
  - skills
  - workstation capabilities
  - shared host actions

This phase matters because workflow steps should ultimately compose operators, not raw capability names plus ambient session assumptions.

Current implemented first cut:

- additive [blend_operator.py](blend_operator.py)
- additive [blend_operator_store.py](blend_operator_store.py)
- explicit `BlendOperator` and `BlendOperatorInvocation`
- context-applicability checks and target resolution helpers
- shared [blend_workflow_execution.py](blend_workflow_execution.py) now consumes `BlendContext` directly during step resolution and invocation
- shared provider factories now build dynamic skill-operator and capability-operator providers below workstation
- shared workflow execution now has provider-based step resolution instead of depending on workstation-local resolution lambdas
- workstation skill workflow execution now dynamically infers `BlendOperator` descriptors from resolved skill artifacts through the shared provider surface instead of depending on a static operator registry
- shared operator providers now expose dynamic skill operators and workstation capability-backed host operators through one root-level catalog/query seam, surfaced in workstation through `ws.operator.list` and `ws.operator.get`
- focused regressions in:
  - [tests/test_blend_operator.py](tests/test_blend_operator.py)
  - [tests/test_blend_operator_store.py](tests/test_blend_operator_store.py)
  - [tests/test_blend_workflow_execution.py](tests/test_blend_workflow_execution.py)
  - [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)

Current boundary:

- the operator contract is currently landed for dynamic skill-backed operators and workstation capability-backed host operators in the shared workflow execution/query path
- controller/runtime surfaces outside workstation still need to move onto the same shared operator contract and provider seam
- `BlendContext` is now part of workflow operator execution, but not yet consumed broadly across all runtime/controller action paths

Current implemented continuity seam:

- additive [blend_world.py](blend_world.py)
- shared [blend_world_store.py](blend_world_store.py)
- workstation session launch can now opt into one shared Blend world root so multiple fresh sessions can reuse the same mutable `workspace` / `scratch` / `output` substrate
- shared world loading, mount lookup, and world summary/query now live below workstation instead of only as workstation-local file conventions
- additive [blend_context.py](blend_context.py) now projects `world_id`, `world_root`, and `world_mounts`, so operators can reason about shared-world applicability directly from `BlendContext`
- workstation trial validation now uses a per-domain shared world root, which makes cross-prompt mutable mounts explicit instead of relying on accidental prompt-local continuity
- focused regressions in:
  - [tests/test_blend_world.py](tests/test_blend_world.py)
  - [tests/test_blend_world_store.py](tests/test_blend_world_store.py)
  - [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)

Validation:

- operator descriptor tests
- context-applicability tests
- current capability/workstation regressions
- targeted real trial rerun for `bash`, `python`, and `sdkuser`: `ok`
- fresh full workstation trial sweep: `status: ok`
- successful-prompt terminal receipt audit: `0` prompts ending in `error` or `approval_required`

Current implementation note:

- host-backed session persistence and receipt emission are now bytes-safe at the shared JSON boundary, which prevents byte-bearing worker outputs from breaking Blend/workstation audit runs

### Phase 2 — Workflow As A First-Class World Object

Goal:

- move from ephemeral compose payloads to explicit workflow plans and runs

Changes:

- add `blend_workflow.py`
- define `BlendWorkflowPlan`
- define `BlendWorkflowRun`
- adapt `ws.skill.compose` to accept a typed workflow plan projection
- record per-step bindings, mappers, branch decisions, and outputs in a workflow run object

This phase should absorb:

- sequence plans
- iterative plans
- conditional/branching plans
- cross-skill and skill-to-host operator plans

Sequencing note:

- by the time this phase lands, multi-step planning should already exist on the current leaf substrate
- this phase is where those plans become first-class Blend workflow objects rather than just executable composition payloads

Current implemented first cut:

- additive [blend_workflow.py](blend_workflow.py)
- shared [blend_workflow_store.py](blend_workflow_store.py)
- shared [blend_workflow_execution.py](blend_workflow_execution.py)
- typed `BlendWorkflowPlan` and `BlendWorkflowRun`
- projection helpers between raw `ws.skill.compose` arguments/results and Blend workflow objects
- additive `workflow_plan` acceptance on `ws.skill.compose`
- additive `workflow_plan` and `workflow_run` emission from `ws.skill.compose` results
- first-class workstation workflow capabilities:
  - `ws.workflow.list`
  - `ws.workflow.get`
  - `ws.workflow.run`
- prompt-local workstation composition now prefers `ws.workflow.run` when it is available
- `ws.skill.compose` remains as a compatibility wrapper over the same underlying workflow engine
- persisted workflow objects through the shared workflow store/query surface, currently rooted at the workstation root:
  - `workflows/plans/<workflow_id>.json`
  - `workflows/runs/<workflow_run_id>.json`
  - `BLEND_WORKFLOWS.json`
- durable workflow ids and run ids returned from `ws.skill.compose`
- workflow ids and run ids also returned from `ws.workflow.run`
- focused regressions in:
  - [tests/test_blend_workflow.py](tests/test_blend_workflow.py)
  - [tests/test_blend_workflow_store.py](tests/test_blend_workflow_store.py)
  - [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)
- no breakage to existing callers that still use raw `steps`

Current boundary:

- workflow objects are now persisted and discoverable through a shared root-level workflow store/query module below workstation
- the backing store is still a workstation-root JSON store, not yet a generalized cross-runtime workflow registry
- workflow querying and rerun now exist through both the shared store/query surface and the workstation capability surface
- workflow execution now also exists through a shared root-level execution surface below workstation, while workstation remains the skill-store resolution and invocation adapter
- branch decisions, bindings, and outputs are exposed through the returned workflow run projection and the persisted run object, but not yet through a broader shared history/query surface

Validation:

- unit tests for workflow object lifecycle
- extension of [tests/test_skill_composition.py](tests/test_skill_composition.py)
- workstation composition regressions
- real partial trial slices using actual trial skills

### Phase 3 — Actor And Projection Model

Goal:

- separate “who is acting” from “how the same semantics are presented”

Current additive milestone already landed:

- [workstation/projection_models.py](workstation/projection_models.py) now provides neutral permission-panel and workflow-graph views
- [workstation/workstation_core.py](workstation/workstation_core.py) now provides the first additive workstation service boundary over permission panels, workflow queries, session-capability mutation, skill inspection/form views, and narrow action helpers for skill invocation and workflow rerun
- workstation chat `/permissions` consumes the permission projection instead of rebuilding it ad hoc
- workstation chat `/list-skills` consumes a neutral skill-catalog projection through the core/service layer
- workstation chat `/describe-skill` now consumes a neutral skill-descriptor projection through the core/service layer
- `ws.workflow.list` now consumes a neutral workflow-summary projection through the core/service layer
- `ws.operator.list` and `ws.operator.get` now consume neutral operator summary/detail projections through the core/service layer
- `ws.workflow.get` returns workflow-graph, workflow-timeline, and workflow-run-history projections beside the persisted workflow plan/run payloads
- workstation activity rendering now consumes neutral activity-event/feed projections through the core/service layer
- skill form specs now include context-fed field options, neutral constraint metadata, section/grouping metadata, and placeholders for non-shell projection hosts
- the Flutter workstation host now exists as a second projection surface over `workstation_core`, without changing workstation truth or shell semantics
- workstation-local subscriber controllers now bridge the event bus into shell/Flutter projection recomposition without pulling execution or workflow correctness into widget code
- the shell now consumes live Blend workflow-step activity through that subscriber/controller seam while retaining receipt-backed activity as fallback; the enhanced chat host is now Textual-first with prompt-toolkit retained as fallback while `textual` adoption finishes
- the Flutter host now rebuilds dashboard specs through the same subscriber/controller seam, can merge live workflow-step events with the receipt-backed activity feed, and can invoke skills / rerun workflows without bypassing workstation capability execution
- this is intentionally a narrow seam, not yet the full `blend_projection.py` layer

Changes:

- add `blend_actor.py`
- add `blend_projection.py`
- define projection kinds:
  - `ai_chat`
  - `automation_api`
  - `hitl_review`
- widen projection contracts further for richer form/grouping semantics and workflow history/timeline rendering
- teach workstation chat to consume projection objects instead of ad hoc visibility rules
- widen the Flutter host beyond the first invoke/rerun cut into broader action-capable projection over the same workflow/operator/session substrate

This is where the repo starts moving toward the user’s future requirement:

- the same semantic workflow can be presented to different actors

Validation:

- projection tests over the same workflow/session state
- workstation UI regressions
- no behavior regressions in existing chat flows

### Phase 4 — Unified Operator Catalog

Goal:

- treat skill operators and host operators as one governed operator space

Changes:

- add `blend_operator.py`
- normalize:
  - skill invoke
  - skill compose
  - repo/file/process/net host actions
  - future deterministic automation operations
- operator descriptors should expose:
  - arguments
  - output leaves
  - required policy
  - context applicability
  - actor visibility

Important sequencing note:

- this phase should expand and unify the catalog over the earlier operator contract
- it should not be the first place where operator/context semantics are introduced

This is important because Blend does not care whether the operator originated as:

- a portable skill
- a host capability
- a controller/runtime-native action

It only cares that the world has named lawful operators.

Validation:

- operator catalog tests
- current capability tests
- workstation command regressions

Current implemented bridge:

- additive [blend_operator_store.py](blend_operator_store.py)
- dynamic provider-based operator listing, workflow-step-aware operator resolution, and provider factories below workstation
- workstation query surface through:
  - `ws.operator.list`
  - `ws.operator.get`
- shared workflow execution now resolves steps through the shared operator catalog/query layer and provider-based step-resolution helper instead of workstation-local operator matching

Current boundary:

- the shared operator catalog is still session-contextual and workstation-backed in practice for now
- controller/runtime still need to project their own operators through the same provider/query seam
- the next move is to widen this from a workstation-backed bridge into a broader shared operator registry/query model

### Phase 5 — Policy And History Projection

Goal:

- make policy and history first-class parts of workflow/session/projection objects

Changes:

- add workflow-level policy view
- add workflow-level history records
- keep receipts as source truth, but project them into:
  - session history
  - workflow history
  - actor-facing activity/history panes

This phase should not replace receipts.

It should organize them.

Validation:

- receipt tests
- workflow history tests
- workstation activity/projection tests

### Phase 6 — Coordination

Goal:

- represent multi-actor work structurally

Changes:

- add `blend_coordination.py`
- define:
  - approvals
  - locks/reservations
  - handoffs
  - review requests
  - merge/conflict state

This should build on existing approval/governance surfaces rather than replacing them.

Validation:

- approval/governance regression tests
- coordination object tests

### Phase 7 — Agent Orchestration

Goal:

- make AI and automation planning explicit Blend objects

Changes:

- add `blend_orchestration.py`
- define:
  - goals
  - candidate workflow plans
  - confidence
  - approval requirements
  - delegation boundaries
  - autonomy levels
- adapt workstation/controller planning to emit these objects before execution

This is where planner widening should happen.

The next widening here should build on the already-landed bounded planner plus the additive context/session/workflow seams, not replace them.

Validation:

- planner-object tests
- workstation planning regressions
- trial-backed multi-step planning validation

## Immediate Practical Priorities

The next real implementation moves should be:

1. keep widening composition planning on the current leaf/mapping substrate
- bounded multi-step, conditional, branching, and iterative planning already exist
- the next widening should improve robustness, coverage, and inspectability rather than re-open the earlier substrate question

2. `BlendContext`
- additive first cut already exists
- next step is to let operator and workflow execution consume it directly, not just materialize it as a discovery projection

3. `BlendOperator` and `BlendOperatorInvocation`
- this should come earlier than the broad projection work
- operators should be defined as context-applied verbs before higher workflow/projection layers widen too far
- the key move is to make context applicability and target resolution explicit in the operator contract

4. `BlendSession`
- additive first cut already exists
- next step is deeper runtime/workflow consumption and clearer actor/session linkage

5. `BlendWorkflowPlan` and `BlendWorkflowRun`
- additive first cut already exists through `blend_workflow.py` and `ws.skill.compose`
- next step is to move from typed projections toward first-class persisted workflow objects over an explicit operator contract, not only capability-shaped steps

6. `BlendProjection`
- current workstation UI is already good enough to serve as the first projection host
- this remains the next major Blend object family after workflow persistence

That is the correct sequence.

## Validation Strategy

Each phase should be validated at three levels.

### Unit Level

- object and invariant tests
- normalization and projection tests
- policy/history tests

### Vertical Slice Level

- workstation regression suites
- controller/runtime hygiene tests
- execution/composition tests

### Trial Level

- partial real trial sweeps during each phase
- full trial sweeps only at stable checkpoints

Recommended trial strategy:

- use `python` and `ansible` slices first for behavior-sensitive changes
- use broader workstation trial sweeps at phase boundaries

## Non-Goals And Risks

### Non-goals

- creating a new UI toolkit
- replacing current CLI/workstation usage patterns immediately
- inventing a second artifact store
- detaching Blend implementation from current governance and receipts

### Risks

- over-modeling before enough runtime integration exists
- creating parallel objects that do not actually drive behavior
- widening the planner in a way that escapes the explicit leaf/mapping substrate
- injecting Blend objects too early and slowing down the already-working composition path
- mixing UI concerns with semantic world concerns too early

## Exit Criteria

The repo will be meaningfully Blend-aligned when:

- `DNA`, `RNA`, `Operators`, `Context`, `UI Abstraction`, `Actor`, `Session`, `Workflow`, `Policy`, and `History` are all explicit in code
- the workstation is clearly one projection surface over those semantics
- deterministic automation can consume the same semantic workflow/operator/session model
- HITL can inspect and act on the same workflow state without bespoke hidden logic
- AI orchestration is expressed as explicit plans and limits, not just prompt heuristics

## Short Version

The plan is:

1. widen composition planning on the current leaf/mapping substrate
2. formalize context and session
3. make workflow first-class
4. separate actor from projection
5. unify operator catalogs
6. project policy and history
7. add coordination
8. only then widen agent orchestration aggressively

That is the Blend-aligned route from the current codebase to the future system.
