# LLM Workstation v1

## Purpose

An **LLM Workstation** is a session-scoped, governed host work surface for an LLM.

It is meant to let an LLM work on real host resources under explicit attachment, capability, and receipt rules.

This is not the same thing as the current BSSC controller runtime.

The workstation reuses parts of the current substrate:
- host mediation
- broker / host ABI ideas
- governance checks
- receipts and replay

The workstation does not require the current recursive controller semantics.

Architecture references:
- [6-LAYER_ARCHITECTURE.md](6-LAYER_ARCHITECTURE.md)
- [08_six_layer_architecture_context.puml](semantic_control_flow_diagrams/08_six_layer_architecture_context.puml)
- [09_workstation_and_shared_host_substrate.puml](semantic_control_flow_diagrams/09_workstation_and_shared_host_substrate.puml)

## Naming

Use **Workstation**, not **Codebase** and not **Workbench**.

Reason:
- the attached host surface may be code
- but it may also include general files, browser interaction, downloads, shell commands, and application control

## Implementation Mandate

The workstation must be implemented as a sibling product surface, not as a rewrite of the outer BSSC runtime.

High-level mandate:
- keep the outer 6-layer BSSC architecture intact
- do not repurpose the workstation as a rename of the existing controller/runtime
- keep workstation-specific implementation under the `workstation/` folder
- allow only thin entrypoint wiring outside that folder
- reuse substrate selectively where it helps, but do not entangle workstation code with the current recursive controller semantics

## Non-Goals

Out of scope for v1:
- reuse of recursive `Not` reduction as the workstation control model
- generalized multi-agent orchestration
- rich policy authoring UI
- ambient host access
- raw-shell-first design

## Core Model

A workstation session has five parts:

1. **Task**
- what the LLM is supposed to do

2. **Attachments**
- which host resources are attached to the session

3. **Capabilities**
- what the LLM is allowed to do with those attachments

4. **Discovery Surface**
- what files and metadata the LLM reads to understand the workstation

5. **Receipts**
- what execution and governance records are emitted

## Architectural Position

The workstation is an outer, host-owned session surface.

In the current architecture it is the **fifth layer** in the six-layer model:

1. Runtime + Skill Execution
2. Controller
3. Governance
4. LLM
5. Workstation
6. Entry / Exchange

It is not:
- the current recursive BSSC controller
- a rename of the existing skill runtime
- a single global Wasmtime container in which all workstation behavior lives

Current intended relationship:
- the workstation owns session state, prompt flow, attachment resolution, secret indirection, and capability mediation
- skills are reusable inner behaviors that may be invoked by the workstation
- some skills may use executor runtimes such as `python3`, `bash`, `ansible`, or `wasm_wasi`
- if a skill uses `wasm_wasi`, that skill invocation may run through Wasmtime
- the workstation itself remains host-owned unless a later design explicitly changes that

Reason:
- session control, credential handling, attachment mapping, and audit emission are easier to govern and debug outside the inner skill runtime

## Convergence Rule

The controller/runtime side and the workstation side should converge on a **shared host interaction substrate**, not on a direct workstation dependency.

That means:
- [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py) should not import workstation session or chat code
- the workstation should not become the controller's execution substrate
- both sides may use the same lower-level host interaction contract

That shared contract should eventually cover:
- attachment resolution
- capability execution
- delegated-rights narrowing
- receipt emission
- governed skill invocation

This is the intended way to let the runtime use workstation-style host interactions without reversing the architecture.

## Session Model

A workstation session is created by a launcher.

The launcher:
- receives user-selected attachments
- resolves named credentials
- resolves allowed capabilities
- applies session governance
- materializes a workstation root
- starts the LLM against that root

The workstation root is logical. It may map to host paths, but the LLM should treat it as the session boundary.

## Host-Owned Session Driver

The workstation session must be owned by the host, not by an autonomous controller inside the sandbox.

Minimum v1 runtime pieces:
- `workstation launcher`
  - creates the session
  - resolves attachments
  - resolves secret references
  - materializes the workstation root
- `workstation session driver`
  - owns the LLM conversation state
  - calls the LLM API
  - routes capability calls
  - writes receipts
- `workstation capability server`
  - implements the workstation capability surface against the host

The LLM may reason about the workstation from inside the session, but the actual session driver should remain host-owned.

Reason:
- raw credentials should stay outside the workstation
- capability mediation should stay outside the workstation
- receipts and replay should be emitted by a trusted outer process
- when the host-owned driver uses the OpenAI provider path, the active Python environment must provide the `openai` package

## Capability Kernel and Skills

The workstation should have a small capability kernel.

These capabilities are kernel primitives, not user-facing workflows.

Reason:
- some lower layer must actually touch host resources
- those operations need direct mediation, attenuation, and receipts
- skills should depend on a stable substrate instead of inheriting ambient host powers

Kernel primitives should include operations such as:
- `ws.fs.read`
- `ws.fs.write`
- `ws.fs.list`
- `ws.process.run`
- `ws.http.request`
- `ws.browser.open`
- `ws.skill.invoke`
- `ws.llm.request` if brokered inner LLM use is exposed

Higher-level behaviors should generally be modeled as skills, not kernel capabilities.

Examples:
- repository tree inspection
- repository search
- test-running workflows
- file download and summarize
- browser-open-and-extract workflows

Reason:
- they are reusable behaviors, not primitive host effects
- they should be versioned, exported, installed, and governed as skills
- they should be replaceable without changing the workstation kernel

Implication for v1:
- some current built-in workstation capabilities may remain transitional during the first slice
- longer term, user-facing behaviors should migrate toward skills built on the kernel primitives

## Skill-First Usage Policy

Within workstation chat, the model should be steered to use skills in nearly all cases.

That includes both:
- explicit skill requests from the user
- implicit skill mapping from ordinary natural-language asks

Examples:
- `find ...` may map to a search skill family
- `run Python code ...` may map to a Python worker skill family
- `run command ...` may map to a shell or automation worker skill family

Reason:
- user-facing behaviors should resolve to governed reusable workers whenever a good worker exists
- this keeps behavior consistent with the workstation mental model:
  - workstation is the shell
  - skills are pluggable workers
  - Wasmtime is one worker runtime
- it also keeps the generic kernel capability layer smaller and less user-visible

If the user explicitly asks to use a skill or skill family, the workstation should stay on the skill path.

That means it should do one of:
- successfully invoke the chosen skill
- ask a short clarification if invocation inputs cannot be derived
- ask the user for permission escalation if the invocation needs additional authority
- return a bounded skill-invocation failure

It should not silently fall back to unrelated generic workstation tools after an explicit skill request.

## Permission-Constrained Skill Invocation

Skill use should be constrained primarily through permissions and permission prompts, not by discouraging the model from using skills.

The intended behavior is:
- the model may infer a suitable skill from the user ask
- the model may infer the likely permissions needed for that skill invocation
- the workstation may attempt the skill invocation with the currently granted authority
- if the invocation fails because additional permissions are needed, the workstation should ask the user for escalation and then continue

In other words:
- try the skill path first
- catch permission insufficiency
- prompt the user
- continue on approval

Reason:
- the user should not need to pre-wire every skill or permission before beginning work
- permission prompts are the right place to constrain authority
- skill preference is the right place to constrain behavior

This is the intended rule for ordinary workstation chat UX.

## Persistent Workstation Skill Home

The workstation should have one standard governed skill home that is persistent across sessions.

This skill home should be:
- attached to workstation sessions by default unless explicitly overridden
- accessible outside a workstation through normal CLI import/export flows
- separate from Codex instruction-skills stored as `SKILL.md`

Reason:
- workstation governed workers are not the same thing as Codex instruction-skills
- users need one stable place where workstation-visible governed skills live across sessions
- import/export and invocation should operate on the same durable worker inventory

Recommended shape:
- persistent governed skill store:
  - `$WORKSTATION_HOME/workstation/skills/store.sqlite3`
- canonical exports directory:
  - `$WORKSTATION_HOME/workstation/skills/exports/`
- optional imports drop area:
  - `$WORKSTATION_HOME/workstation/skills/imports/`

The workstation should surface this store through a normal skill-store attachment and discovery files such as `SKILLS.json`.

## Workstation Skill Lifecycle Operations

The workstation should support first-class skill lifecycle operations over the persistent skill home.

These operations are distinct from ordinary user-facing workflow skills.

The minimum operations are:
- `ws.skill.catalog`
- `ws.skill.import`
- `ws.skill.export`
- `ws.skill.invoke`

Reason:
- these operations act on the workstation worker system itself
- they require direct governance, receipts, and stable storage semantics
- they should not bypass the existing governed skill import/export path

These operations should be available through two user-facing surfaces:
- first-class CLI commands for deterministic lifecycle work
- the workstation chat surface for conversational lifecycle work

Direct Python capability calls should be treated as an implementation and test surface, not the intended user-facing product surface.

Reason:
- lifecycle operations need a deterministic interface for scripts, automation, and validation
- chat is appropriate for conversational discovery and ad hoc work, but not as the only verification surface
- direct Python calls are useful for unit tests, but they should not define the product UX

Recommended CLI surface:
- `workstation-skill-catalog`
- `workstation-skill-import`
- `workstation-skill-export`

These commands should operate against a workstation root by default, so they use the same persistent workstation skill home and discovery files as the chat session.

### Import

`ws.skill.import` should:
- accept a `skill.yaml` source
- import it through the existing governed skill import path
- persist it into the persistent workstation skill home
- emit receipts including title, digest, and admission outcome

### Export

`ws.skill.export` should:
- export a skill by title from the persistent workstation skill home
- write a canonical `skill.yaml` either to an explicit destination or to the standard exports directory
- preserve portable governed-skill semantics

### Create and Enhance

`create` and `enhance` are workflow behaviors, not kernel lifecycle primitives.

However, for the current stage:
- `create` may proceed as a workstation workflow around import/export
- `enhance` is explicitly deferred

Reason:
- current enhancement logic does not yet understand governed skill syntax well enough
- we should not invent a weak enhancement surface before the lifecycle substrate is stable

For now, the supported durable loop is:
- import
- invoke
- export

The intended near-term UX split is:
- CLI for deterministic lifecycle operations
- chat for natural-language use of the same lifecycle operations
- tests may still use direct capability calls internally

Longer term, `create` should follow:
- draft
- validate
- import
- export

Longer term, `enhance` should follow:
- export current
- edit
- import updated
- export canonical result

Until then, enhancement should be treated as out of scope for workstation v1.

## Session Lifecycle

Minimum v1 session lifecycle:

1. `create`
- launcher receives task, attachments, allowed capabilities, and credential references

2. `materialize`
- launcher writes the workstation root and discovery files

3. `start`
- host-owned session driver initializes conversation state and begins the turn loop

4. `prompt`
- user sends a message to the workstation session

5. `act`
- the LLM reads workstation files and performs capability calls through the driver

6. `record`
- receipts are written for capability use and session outcomes

7. `resume`
- the host-owned session driver resumes the session from saved state

8. `export`
- the session and receipts can be exported as a replayable bundle

## User Prompt Model

The user should prompt the workstation through a host-owned prompt surface.

Examples:
- CLI
- GUI chat
- API call

The user should not need to edit `TASK.md` manually unless that is an explicit fallback mode.

Prompt flow:
- user submits a prompt to the host-owned session
- session driver records the prompt in session state
- session driver may mirror the prompt into workstation-visible files such as `TASK.md` or `MESSAGES.jsonl`
- session driver sends the conversation turn to the LLM API
- the LLM responds and may request workstation capabilities
- capability results are returned to the session driver and incorporated into the next turn

## Task Boundary Contract

User prompts should be interpreted through BSSC boundary-shape completeness theory, but the user should not be required to write prompts in explicit BSSC notation.

That means:
- user input remains natural language
- the workstation session driver normalizes that input into a boundary-complete task contract
- missing or ambiguous boundary elements become clarification questions, explicit assumptions, or explicit incompleteness markers

### Purpose

The task boundary contract exists to make workstation prompts operationally complete enough for governed execution.

It should help answer:
- what values are being provided
- what references must be read
- what side effects are required
- what outputs are expected
- what is still missing

### Minimum v1 task boundary fields

- `semantic_unit`
  - the normalized task statement
- `input_values`
  - inline values already supplied by the user
- `read_references`
  - files, URLs, records, browser targets, or other references that must be read
- `write_targets`
  - files, destinations, or host targets that will be written or changed
- `output_values`
  - expected direct outputs to the user
- `side_effects`
  - browser open, app launch, download, file write, command run, and similar effects
- `completion_conditions`
  - what must be true for the task to count as complete
- `assumptions`
  - assumptions the session driver or LLM is making explicitly
- `missing_requirements`
  - unresolved items that block safe or coherent execution

### Example

Raw user prompt:
- `Open the browser, download the quarterly report, and summarize it.`

Normalized task boundary contract:

```json
{
  "semantic_unit": "Open the browser, obtain the quarterly report, and produce a summary.",
  "input_values": {},
  "read_references": [
    "browser target",
    "quarterly report source"
  ],
  "write_targets": [
    "download destination"
  ],
  "output_values": [
    "summary"
  ],
  "side_effects": [
    "open browser",
    "download file"
  ],
  "completion_conditions": [
    "quarterly report is available in the workstation",
    "summary is returned to the user"
  ],
  "assumptions": [],
  "missing_requirements": [
    "report URL or search target"
  ]
}
```

### Clarification Policy

The session driver should only interrupt the user when missing boundary information materially affects safe or coherent execution.

Typical cases:
- missing write destination for a destructive action
- missing source reference for a required read
- missing selection among multiple plausible targets
- missing authorization or capability needed for a requested side effect

If the missing information is non-critical, the workstation may proceed with explicit assumptions and record them in the task boundary contract.

## Boundary Completeness and Capability Planning

The normalized task boundary contract should drive capability planning.

Examples:
- `read_references` suggests `ws.fs.read`, `ws.repo.search`, `ws.http.download`, or browser/read capabilities
- `write_targets` suggests `ws.fs.write` or other write-side capabilities
- `side_effects` suggests browser, app, process, or network capabilities
- `output_values` shapes the expected response and completion check

This means boundary-shape completeness should be part of task normalization and planning, not just a post hoc validation step.

## Skill Invocation and Delegated Rights

When the workstation invokes a skill, the skill must not inherit the workstation's rights ambiently.

Instead, the workstation should request a delegated invocation grant for that skill.

The host must compute the effective delegated grant as the intersection of:
- session-level allowed capabilities
- the normalized task boundary contract
- the skill declaration
- current policy, approval, lifecycle, and other governance state

This means a skill should receive only the smallest capability subset justified for that invocation.

Examples:
- read access to attachment `main`
- write access to attachment `scratch`
- process execution in attachment `main`
- valid only for the current invocation

It should not receive:
- global `ws.fs.*`
- ambient process execution
- all workstation powers merely because the workstation possesses them

Reason:
- this preserves least authority
- this keeps workstation-session rights separate from skill-invocation rights
- this makes receipts and replay able to explain exactly what was delegated and why

## Declaration, Runtime Discovery, and Escalation

Not all concrete rights can be determined at workstation launch time.

However, runtime discovery must refine and attenuate declared authority, not replace declaration.

The intended model has three stages:

1. `skill declaration`
- the skill declares the broad authority surface it may need
- this is the upper bound for normal use
- examples:
  - `fs.read`
  - `fs.write`
  - `process.run`
  - `browser.open`

2. `invocation planning`
- at invocation time, the workstation session driver or LLM determines the smallest subset needed for the current call
- this binds abstract authority to concrete attachments, targets, and scope
- examples:
  - `fs.read(main)`
  - `fs.write(scratch/reports)`
  - `process.run(main, read-only purpose)`

3. `host governance decision`
- the host compares the requested invocation subset against:
  - the workstation session grant
  - the task boundary contract
  - the skill declaration
  - current policy, lifecycle, approval, and other governance state
- the host then:
  - grants the requested subset
  - narrows it further
  - denies it
  - or requires explicit user approval for escalation

This means:
- declaration provides the normal upper bound
- runtime planning computes the invocation-specific subset
- host governance computes the effective granted subset

Runtime discovery is therefore for:
- narrowing
- attachment binding
- target binding
- escalation detection

It should not be used as a substitute for declaring the expected authority surface of the skill.

Reason:
- pure runtime authority discovery leads to ambient behavior
- declaration is required for governance review and stable reuse
- invocation planning is required for least-authority execution
- host-controlled escalation is required when the current workstation session did not pre-authorize the needed subset

## User Approval for Escalation

If a skill invocation requires permissions outside the workstation session's currently granted authority, the host-owned workstation must ask the user for escalation.

That escalation should:
- identify the skill being invoked
- identify the concrete additional rights being requested
- identify the attachments or resources those rights apply to
- identify whether the grant is one-shot, task-scoped, or session-scoped

The skill itself must not self-authorize the escalation.

The host remains the authority that:
- prompts the user
- records approval or denial
- applies the resulting effective grant
- writes the corresponding receipts

Reason:
- escalation is a workstation/session governance decision, not a skill-local decision
- the user must be able to see the difference between ordinary delegated use and new authority acquisition
- receipts and replay must capture that distinction

## Skill Invocation Request Model

The user should not have to state permissions explicitly.

The user prompt remains natural language.

The workstation session driver or LLM should internally produce a structured skill invocation request containing:
- the target skill
- the invocation arguments
- the requested delegated capabilities
- the attachments or resources those capabilities apply to
- the task-boundary rationale

The host remains the authority that:
- grants the request
- narrows it
- denies it
- or requires approval

Reason:
- the LLM must declare what powers it believes are needed
- but the user should not bear the burden of writing capability policy in the prompt
- the host must remain the final authority over rights

## Delegation Example

Session attachments:
- `main`: repository, read-only
- `scratch`: writable work area

User prompt:
- `Find where workstation chat is implemented.`

Possible workstation plan:
- invoke skill `repo.search`
- arguments:
  - `pattern = "workstation chat"`
- requested delegated capabilities:
  - `fs.read` on attachment `main`
  - `process.run` on attachment `main` if the skill implementation needs `rg`

Effective host grant:
- `fs.read(main)`
- optionally `process.run(main)`

Denied behaviors during that invocation:
- `fs.write(main)`
- `fs.write(scratch)` if not requested or not justified

This is the intended pattern for workstation-to-skill delegation.

## Skill Composition Strategy

The workstation should prefer direct skill composition before attempting to plug in the full BSSC controller.

That means:
- the workstation shell plans capability use and skill invocation directly
- skills may call other skills through explicit invocation surfaces
- higher-level workstation behaviors should be built as ordinary governed skills on top of the workstation kernel

The workstation should not, by default, embed the recursive BSSC controller as its orchestration model.

Reason:
- the workstation product surface is broader than the controller
- direct skill composition is easier to reason about, replay, and govern at the workstation boundary
- plugging in the controller too early would blur the separation between workstation shell, worker skills, and controller semantics

This does not rule out later controller reuse.

It means:
- controller integration is an optional later composition path
- direct governed skill composition is the default workstation model
- any controller/runtime reuse should happen through a shared host interaction contract, not by making the runtime call workstation shell code

Practical consequence:
- import/export/invoke should be first-class workstation operations
- workstation flows should compose skills directly wherever possible
- controller-based orchestration should only be introduced later if direct skill composition proves insufficient

## Boundary Completeness and Receipts

Receipts should reflect the normalized task boundary contract.

This allows replay and audit to answer:
- whether the executed capabilities matched the intended task boundary
- whether side effects exceeded the declared task shape
- whether the session finished with missing requirements or explicit assumptions still in force
- what delegated rights were requested for each skill invocation
- what delegated rights were actually granted
- which attachments and resources those delegated rights applied to

## REPL Model

If a REPL exists, it should be a host-owned REPL bound to one workstation session.

It should not be:
- a free ambient shell inside the sandbox
- a second autonomous controller inside the workstation

It should be:
- a prompt surface for the same host-owned session driver
- another way to send prompts to the current workstation session

## LLM API Model

The host-owned session driver should be the only component that calls the LLM API directly.

The workstation root may describe available LLM-related capabilities, but the actual API call must remain outside the workstation boundary.

Reason:
- the host should own provider configuration
- the host should own credential use
- the host should own request and receipt policy

## Secret and OpenAI Token Flow

OpenAI credentials should be passed as secret references, not as raw secret values exposed inside the workstation.

Recommended flow:

1. user provides `OPENAI_API_KEY` to the launcher through host env, host secret storage, or a named profile
2. launcher resolves that into a workstation attachment such as `openai_default`
3. workstation session driver creates and owns the OpenAI client
4. all LLM API requests are executed by the host-owned session driver
5. the workstation sees only the named secret or provider reference, not the raw key

This means the LLM inside the workstation should not read the raw `OPENAI_API_KEY` from the environment.

### Example secret reference

```toml
[attachments.openai]
kind = "secret_ref"
source = "host:OPENAI_API_KEY"
access_mode = "indirect"
mount_path = "/workstation/secrets/openai"
metadata.profile = "openai_default"
```

## Capability Calls Versus LLM API Calls

The workstation needs two different outer interactions:

1. **capability calls**
- file reads and writes
- workspace search
- process execution
- browser or application actions

2. **LLM API calls**
- host-owned calls to OpenAI or another provider

Both should be mediated by the host-owned session driver, but they are not the same thing.

The workstation should not treat the raw LLM API as ambient access any more than it should treat the shell as ambient access.

## Optional LLM Capability Surface

If the workstation itself needs an LLM capability, expose it as a named workstation capability rather than raw provider access.

Example:
- `ws.llm.request(profile="openai_default", prompt=...)`

Even in that case, the actual provider call still routes through the host-owned session driver or a host-side capability server.

## Attachment Model

Attachments are named resources, not ambient host access.

Each attachment has:
- `name`
- `kind`
- `source`
- `access_mode`
- `mount_path`
- optional metadata

### Attachment kinds

Minimum v1 kinds:
- `workspace`
  - a host directory the LLM may inspect or edit
- `path`
  - a general file or directory attachment
- `scratch`
  - session-local writable working space
- `output`
  - expected output destination
- `secret_ref`
  - a named credential reference, not raw secret text
- `browser_profile`
  - a named browser/session binding if browser actions are enabled

### Example

```toml
[attachments.main]
kind = "workspace"
source = "/Users/alice/project"
access_mode = "read_write"
mount_path = "/workstation/mounts/main"

[attachments.output]
kind = "output"
source = "/Users/alice/project/.workstation-output"
access_mode = "write"
mount_path = "/workstation/output"

[attachments.openai]
kind = "secret_ref"
source = "host:OPENAI_API_KEY"
access_mode = "indirect"
mount_path = "/workstation/secrets/openai"
```

## Capability Model

The LLM does not act on raw host state directly.

It acts through named workstation capabilities over named attachments.

Capabilities are typed and receipt-producing.

### Minimum v1 capability families

- `ws.fs.read`
- `ws.fs.write`
- `ws.fs.list`
- `ws.fs.find`
- `ws.process.run`
- `ws.http.download`
- `ws.browser.open`
- `ws.app.open`
- `ws.secret.use`
- `ws.repo.search`
- `ws.repo.tree`
- `ws.test.run`

### Capability shape

Each capability call must include:
- capability name
- target attachment or named target
- typed arguments
- optional execution metadata

Example:

```json
{
  "capability": "ws.repo.search",
  "target": "main",
  "args": {
    "pattern": "artifact_from_skill_document"
  }
}
```

The implementation may use `rg`, `python3`, browser automation, or other local tools underneath.

That is an implementation detail.

The contract seen by the LLM is the workstation capability surface.

## Discovery Model

The LLM must not be forced to infer the workstation from raw directory layout alone.

The launcher should generate a small, explicit discovery surface.

### Required files

- `README.md`
  - short human-readable instructions
- `TASK.md`
  - the current assignment and completion criteria
- `WORKSTATION.toml`
  - authoritative machine-readable contract
- `ATTACHMENTS.json`
  - resolved session attachments

### Optional generated files

- `WORKSPACE_INDEX.json`
  - summary for attached workspaces
- `TOOLS.json`
  - available capabilities and argument schemas
- `SESSION.json`
  - session id, timestamps, policy profile, launcher info
- `MESSAGES.jsonl`
  - optional mirror of user and assistant turns visible inside the workstation

## Workspace Discovery

If an attachment kind is `workspace`, the launcher should generate discovery data for it.

Minimum workspace discovery:
- root path
- top-level tree
- language hints
- package/build/test manifest hints
- important files if found
  - `README.md`
  - `MODULES.md`
  - `pyproject.toml`
  - `package.json`
  - `Cargo.toml`

This avoids requiring the LLM to guess whether a mounted path is:
- a code repository
- a content folder
- a scratch directory

## Workstation Root Layout

Minimum suggested layout:

```text
/workstation
  README.md
  TASK.md
  WORKSTATION.toml
  ATTACHMENTS.json
  TOOLS.json
  SESSION.json
  mounts/
    main/
  scratch/
  output/
  receipts/
```

The names do not have to be exactly these, but v1 should standardize them if possible.

## Governance Model

The workstation is governed, but it is not the full BSSC controller.

Governance in v1 should cover:
- declared attachments
- declared capabilities
- capability allow/deny policy
- secret indirection
- receipt emission
- replay/export of a session run

The LLM should not receive:
- ambient environment secrets
- undeclared host filesystem access
- undeclared network access
- undeclared process execution

## Secret Model

Secrets should be referenced, not exposed.

The LLM should not need raw key material.

Instead, it should use a named secret profile or named provider binding.

Example:
- `ws.secret.use(name="openai")`
- `ws.http.download(auth_profile="openai_default", ...)`

The launcher/runtime decides how that secret is actually applied.

## Receipts and Replay

Every capability call should emit a receipt.

Minimum receipt fields:
- session id
- timestamp
- attachment target
- capability name
- normalized arguments
- allow/deny decision
- result summary
- side-effect summary

The workstation should support export of a replayable session bundle.

This can reuse the existing bundle / replay direction already present in the current system, but the workstation session should be treated as its own product surface.

## Relation to the Current 6-Layer Architecture

The workstation reuses parts of the current system, but it is not identical to it.

### Reuse

- **Runtime + Skill Execution**
  - broker ideas
  - host ABI ideas
  - mediated execution
- **Governance**
  - capability checks
  - receipts
  - replay/export concepts
- **Entry / Exchange**
  - session launch
  - import/export

### Future shared substrate

- **Controller**
  - should eventually be able to consume the same host interaction contract
  - should not depend on workstation session/chat modules directly

### Not required in v1

- **Controller**
  - recursive semantic reduction
- **LLM**
  - BSSC-specific prompt/controller semantics

So the workstation should be treated as a sibling product surface inside the six-layer model, not as a rename of the whole BSSC runtime and not as a substrate that the controller imports directly.

## Practical v1 Flow

1. User selects a host path and optional credentials.
2. Launcher creates a workstation session.
3. Launcher resolves attachments, allowed capabilities, and secret references.
4. Launcher materializes the workstation root.
5. Host-owned session driver starts and owns the conversation state.
6. User prompts the workstation session through CLI, UI, or API.
7. LLM reads `README.md`, `TASK.md`, `WORKSTATION.toml`, and discovery files.
8. LLM performs work only through workstation capabilities.
9. Host-owned session driver performs any required LLM API calls using named provider profiles or secret references.
10. Receipts are written and the session can be resumed or exported.
7. Receipts are emitted.
8. The session can be exported or replayed.

## Example User Story

User has:
- a local project directory
- an OpenAI API key

User creates a workstation with:
- `main` workspace attached to the project directory
- `openai` secret reference attached indirectly
- allowed capabilities:
  - `ws.repo.search`
  - `ws.fs.read`
  - `ws.fs.write`
  - `ws.process.run`
  - `ws.test.run`

The host-owned session driver then:
- resolves the OpenAI key as a secret reference
- initializes the LLM provider client
- starts the workstation session

The LLM then:
- discovers that `main` is a workspace
- sees the project summary from `WORKSPACE_INDEX.json`
- reads task instructions
- performs file search, edits, and test runs through the workstation capability layer
- never needs ambient shell or raw secret exposure

## Recommended Next Implementation Step

Define `WORKSTATION.toml` as a concrete schema and implement one launcher that can:
- attach a local workspace
- attach a scratch/output area
- attach one indirect secret reference
- expose a small capability set
- emit receipts

That is enough for a real v1 pilot.
