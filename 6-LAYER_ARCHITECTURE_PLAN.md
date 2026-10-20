# Six-Layer Architecture Plan

This filename is legacy. The architecture plan is now six-layer.

## Current Status

- The core BSSC surfaces are clean enough to reason about:
  - controller/governance boundary
  - runtime/governance boundary
  - exchange/schema/export split
- The workstation is now a real sibling surface under [workstation](workstation).
- The workstation trial corpus is green for all current portable governed bundles:
  - `ansible`
  - `apiclient`
  - `bash`
  - `chemistry`
  - `deviceuser`
  - `python`
  - `sdkuser`
  - `symbolsearch`

## Six Layers

1. Runtime + Skill Execution
2. Controller
3. Governance
4. LLM
5. Workstation
6. Entry / Exchange

Reference:
- [6-LAYER_ARCHITECTURE.md](6-LAYER_ARCHITECTURE.md)

## Main Architectural Decision

The next convergence move is:

- **not** `governed_semantic_reduction_runtime -> workstation`
- **not** `controller -> workstation`
- **not** `runtime -> workstation`

It is:

- `controller -> shared host interaction substrate`
- `workstation -> shared host interaction substrate`

with runtime remaining below that substrate.

## Shared Host Interaction Substrate

The shared substrate should own the parts that both controller-side runtime work and workstation-side session work need:

- attachment resolution
- mount normalization
- capability execution
- delegated-rights computation
- governed skill invocation
- receipt writing
- optional approval/escalation hooks

It should not own:
- workstation chat loop
- workstation root materialization
- `WORKSTATION.toml`
- direct controller semantics
- recursive `Not` reduction

## Concrete Refactor Direction

### Phase 1: Define the substrate contract

Add a narrow contract such as:
- `host_interaction_context.py`
- `host_interaction_models.py`

The contract should cover:
- attachments
- capability calls
- delegation requests
- receipts
- governed skill invocation
- backend identity, so the same runtime can execute against:
  - `host`
  - `workstation`

Current state:
- first descriptor/context cut is implemented
- workstation now provides a workstation-backed adapter
- governed runtime now records injected backend identity and attachment/capability scope through the shared contract
- host mediation now uses that contract for one real execution seam:
  - child worker `workspace_root`
  - attachment-backed `virtual_mounts`
- shared delegated-rights helpers now live below workstation:
  - requested-delegation normalization
  - escalation splitting against current grant
  - ephemeral delegated-mount projection
- shared receipt helpers now live below workstation:
  - canonical receipt-log path resolution
  - append-only JSONL event emission
  - shared receipt payload builders for prompts, capability calls, assistant responses, and escalation decisions
- the first shared host-action helpers now live below workstation:
  - attachment-scoped repo tree
  - attachment-scoped text read result shaping
  - attachment-scoped process execution
- shared non-skill host-action dispatch/result conventions now live below workstation:
  - capability membership for the extracted non-skill surface
  - shared dispatch for tree, search, read, and process actions
  - injected read-resolution seam for shell-specific discovery rules
- generalized operation-provider injection is still open: executor dispatch and
  the host-broker registry remain packaged/static, and the public core ABI does
  not accept a provider implementation

### Phase 2: Extract current workstation-specific primitives downward

Move reusable pieces out of the workstation shell layer:
- attachment target normalization
- capability result/receipt shaping
- delegated-rights narrowing helpers
- governed skill invocation helpers

Current state:
- attachment/root helpers are shared
- delegated-rights helpers are shared
- receipt shaping and canonical receipt appends are shared
- the first concrete host actions are shared
- the current non-skill host-action dispatch is shared
- skill lifecycle and skill invocation dispatch are still workstation-local

Keep workstation-only pieces where they are:
- session root files
- chat loop
- workstation CLI

### Phase 3: Let the workstation implement the contract

The workstation remains host-owned, but now through the shared contract rather than workstation-local helpers only.

### Phase 4: Let governed runtime consume the contract

[governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py) should be able to execute against an injected host interaction context.

Important:
- it should consume the contract
- it should not import the workstation package
- it should treat `host` and `workstation` as backend implementations of the same contract, not as hardcoded mode branches
- the host must supply a concrete realizer independently of any ability bundle;
  ability-to-realizer binding is mechanical

### Phase 5: Add a controller planning bridge, not a workstation dependency

The controller should use the shared contract for:
- attachment-aware reads/writes
- governed skill execution
- bounded capability calls

The workstation may optionally use controller planning later, but that is a separate bridge and not the first move.

## Guardrails

- Do not make the runtime depend on workstation session/chat code.
- Do not route all workstation prompts through `reduce_not`.
- Do not move workstation-only UX concerns into the substrate.
- Do not bypass current governance, receipts, or skill invocation rules during extraction.

## Milestone Gates

After substrate contract definition:
- targeted unit tests for the new contract layer
- full workstation suite

After workstation extraction:
- full workstation suite
- combined workstation trial sweep

After runtime adoption:
- full unit suite
- chemistry gate
- learned-function gate
- combined workstation trial sweep again

## Success Condition

We are done with this architecture step when all of the following are true:

- `governed_semantic_reduction_runtime` can execute against an injected host interaction context
- the injected context includes callable realizer providers, not descriptor
  metadata alone
- the workstation provides one implementation of that context
- neither runtime nor controller imports workstation shell/session modules directly
- the workstation trial sweep remains green
- the main unit suite remains green
