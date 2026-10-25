# Six-Layer Architecture Implementation

This filename is legacy. The implementation tracker is now six-layer.

## Current Implementation Position

- [x] Runtime / governance separation is behind a runtime-facing facade.
- [x] Controller / governance separation is behind a controller-facing bridge.
- [x] Exchange/schema/export responsibilities are split out of the old mixed `skill_io` surface.
- [x] Workstation exists as a separate sibling surface under [workstation](workstation).
- [x] Workstation trial validation is green for the current governed portable trial corpus.
- [x] The shared host-interaction contract and common mechanics are packaged as
  the dependency-free `realized-host-interaction` substrate.
- [x] The governed runtime can now describe an injected host backend through that contract without importing workstation shell code.
- [x] The workstation now has a workstation-backed adapter for the shared host-interaction contract.
- [x] A first lower runtime/controller bootstrap facade now exists in [runtime_controller_api.py](runtime_controller_api.py), so workstation nested skill invocation no longer imports `main.py` directly.
- [x] Host mediation now derives worker filesystem scope from the shared host-interaction contract instead of ambient cwd.
- [x] Delegated-rights normalization, escalation splitting, and ephemeral delegated-mount projection now live in the shared host-interaction substrate.
- [x] Receipt shaping and canonical JSONL receipt appends now live in the shared host-interaction substrate.
- [x] The first concrete host actions now live in the shared host-interaction substrate:
  - bounded attachment-scoped tree inspection
  - bounded attachment-scoped text reads
  - bounded attachment-scoped process execution
- [x] Shared non-skill host-action dispatch/result conventions now live in the shared host-interaction substrate.
- [x] Targeted hygiene tests now cover the workstation/controller/runtime boundary.

## Boundary Qualification

The implemented `HostInteractionContext` carries backend identity, attachments,
and allowed capability names. Those values shape mounts and child-runtime
context, but the contract is not a general callable operation-provider registry.
Executor dispatch and the governed host-broker registry remain packaged
implementations.

The following work therefore remains open:

- expose provider injection through a public composition ABI if callers need to
  supply new executor or broker realizers
- verify that advertised support corresponds to a packaged or registered
  provider and its runtime prerequisite
- qualify the complete ability journey independently: definition, admission,
  scope, semantic matching, exact realizer binding, invocation, and receipts

## Next Convergence Cut

Goal:
- let the governed runtime use host-provided operations, including
  workstation-backed implementations
- without making the runtime depend on workstation shell code directly
- do that through pluggable host-interaction backends:
  - `host`
  - `workstation`

This goal is not complete merely because a backend descriptor can be injected.

## Tracker

- [x] define a shared host interaction contract for attachments, capabilities, delegation, and receipts
- [x] represent backend identity explicitly so the governed runtime can describe `host` and `workstation` as different implementations of the same contract
- [x] identify workstation helpers that belong in that shared substrate
- [x] extract the first real helper set below the workstation shell:
  - attachment-backed virtual mounts
  - effective workspace root resolution
- [x] extract the next shared delegation helper set below the workstation shell:
  - requested-delegation normalization
  - escalation splitting against current session grant
  - ephemeral delegated-mount projection
- [x] extract the next shared receipt helper set below the workstation shell:
  - canonical receipt log path resolution
  - append-only JSONL event emission
  - shared receipt payload builders for prompt, capability, assistant, and escalation events
- [x] make workstation and host mediation use the shared substrate implementation for:
  - attachment-derived mounts/root
  - delegated-rights normalization and ephemeral mount projection
- [x] make workstation session and CLI use the shared substrate implementation for:
  - capability receipt shaping
  - assistant/prompt receipt shaping
  - escalation approval receipt shaping
- [x] extract the first shared host action helper set below the workstation shell:
  - attachment-scoped repo tree
  - attachment-scoped text read result shaping
  - attachment-scoped process execution
- [x] make workstation use the shared substrate implementation for the first concrete host actions:
  - `ws.repo.tree`
  - `ws.fs.read`
  - `ws.process.run`
- [x] make workstation use the shared substrate implementation for shared non-skill action dispatch:
  - `ws.repo.tree`
  - `ws.repo.search`
  - `ws.fs.read`
  - `ws.process.run`
- [x] make governed runtime consume the shared substrate through injection for backend identity and attachment/capability scope description
- [x] make governed runtime consume the shared substrate for one real host-interaction seam:
  - child worker `workspace_root`
  - child worker attachment-backed `virtual_mounts`
- [x] keep runtime/backend selection on the contract boundary, not as workstation-specific conditional logic inside the governed runtime
- [x] keep workstation chat/session/CLI out of the shared substrate
- [x] add targeted unit tests for the shared substrate
- [x] rerun workstation suite
- [x] rerun combined workstation trial sweep
- [x] rerun full unit suite

## Non-Goals

- [x] do not make the governed runtime import workstation shell/session code
- [x] do not make controller import workstation shell code
- [x] do not force workstation prompts through `reduce_not`
- [x] do not collapse workstation and controller into one loop
