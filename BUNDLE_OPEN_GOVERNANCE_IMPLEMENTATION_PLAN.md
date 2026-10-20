# Bundle / Open Governance Implementation Plan

## Objective

Implement the capability-mediated architecture described in [BUNDLE.md](BUNDLE.md) in a way that advances toward the constitutional target in [OPEN_GOVERNANCE.md](OPEN_GOVERNANCE.md), while preserving the current Python runtime, SQLite store, skill import/export, policy admission, and existing executor-backed features.

## Current Status

Implemented now:

- runtime host mediation for current executor-backed ability execution
- declaration-derived runtime capability grant issuance
- per-effect allow-or-deny decisions before executor dispatch
- durable effect trace and runtime capability-grant persistence in `SystemState`
- controller execution routed through mediated execution instead of direct executor dispatch
- named host broker registry for `fs`, `store`, `net`, and macOS actions
- mediated broker-request path for host-broker effects under the same grant-and-trace model
- governed Python skill host API plus broker-aware child trace ingestion
- versioned host ABI contract for broker names and typed payloads:
  - `bssc.host.v1`
- persisted skill lifecycle state with activation, trust, and quarantine checks at invocation time
- approval artifacts and approval-record matching during v2 admission
- import ordering that installs policy and approval artifacts before approval-gated skills are evaluated
- invocation-time re-evaluation against currently installed policy and approval artifacts
- approval revocation handling at invocation time
- governed virtual-mount file brokers:
  - `fs.read_mount`
  - `fs.write_mount`
  - `fs.list_mount`
- governed named-store brokers:
  - `store.named_query`
  - `store.skill_state`
- data-class enforcement at mounted-file, named-query, and skill-state broker boundaries
- skill import/export support for:
  - `virtual_mounts`
  - `named_queries`
  - `skill_state_namespace`
- skill import/export support for broker ABI metadata:
  - `governed_host_brokers`
  - `host_abi_version`
- stable higher-risk admission holds on transitional brokers instead of only raw host-pattern holds
- named tool mediation through:
  - `tool.invoke`
- bounded governed inter-skill invocation through:
  - `skill.invoke`
- nested governed trace/grant ingestion from mediated tool and skill subcalls
- higher-risk Python admission holds raw host patterns:
  - raw `sqlite3`
  - raw path/file access
  - raw network access
  - raw tool/process invocation
- first governed Wasm skill representation in import/export:
  - `executor: wasm_wasi`
  - `representation: wasm_module`
  - `wasm` body field in skill import/export
  - `wasm_abi_version`
  - `wasm_format`
- minimal compute-only Wasm ABI:
  - `bssc.wasm.v1`
  - JSON input/output transport
  - exported `memory`
  - exported `run() -> i32`
  - no ambient fs/net/sqlite/stdio/clock/random/environment
- first embedded Wasmtime runner under Python host governance
- mediated Wasm execution through the same trace and grant path as current executors
- revocation and incident governance records for current-use trust, suspension, and quarantine overlays
- local governed registry export surface through:
  - `export-skill-registry`
- governance snapshot receipts in replay bundles for:
  - policy titles
  - approval titles
  - revocation titles
  - incident titles
  - registry identity
- replay verification of bundled governance receipts against the replay-imported governed skill set

Still pending:

- constitutional trace hardening at the per-effect receipt level:
  - declaration snapshot receipts
  - policy snapshot receipts
  - lifecycle snapshot receipts
  - approval evidence receipts
  - stronger composition-chain receipts
- replay verification hardening beyond final-answer/effect equivalence
  - see [CORE_RUNTIME_DETERMINISM_AND_REPLAY_IMPLEMENTATION_PLAN.md](CORE_RUNTIME_DETERMINISM_AND_REPLAY_IMPLEMENTATION_PLAN.md) for the concrete decision-flow + transcript replay plan over the `reduce_not` runtime
- broker-only enforcement for higher-risk Python skills instead of pattern-based holds alone
- registry hardening beyond the first local governed index export
- explicit revocation / incident receipts at the per-effect constitutional trace level
- broader brokered Wasm hostcalls over the stable host ABI beyond the first bounded subset
- broader Wasm tiers beyond the first compute-only executor

## Fixed Constraints

- Outer host remains Python first.
- Host OS target is macOS first.
- Current features must keep working:
  - governed skill import/export
  - v2 declaration and policy admission
  - Python / bash / ansible executable skills
  - current CLI flows
  - current SQLite-backed artifact store
  - current replay/state substrate

## Core Interpretation

The essential idea in [BUNDLE.md](BUNDLE.md) is not Rust first. The essential idea is:

1. host owns effects
2. skills never get raw host resources
3. every material effect goes through a mediated capability surface
4. mediation is where policy, authority, approval, trace, and replay become real

That can be implemented in Python first.

So the first architectural move is not "replace Python with Rust."
It is "stop letting executable skills behave like raw scripts and make them behave like governed requests against a host broker."

## Current Baseline

What already exists:

- governed skill identity
- v2 skill declaration
- risk tiers
- policy artifacts
- approval artifacts
- admission evaluation at import time
- persisted lifecycle state distinct from admission
- execution denial for held governed skills
- execution denial for inactive, suspended, revoked, or quarantined governed skills
- execution denial when current installed approval state no longer satisfies the declared approval class
- execution allowance when current installed approval state newly satisfies a previously held skill
- execution through governed virtual mounts instead of raw paths where the skill uses mount brokers
- execution through named queries and namespaced skill state instead of raw SQLite where the skill uses governed store brokers
- constitutional trace snapshot export
- replayable run bundles
- replay verification CLI and runtime path
- executable frameworks for Python, bash, ansible, and first-tier Wasm

What is still missing relative to [OPEN_GOVERNANCE.md](OPEN_GOVERNANCE.md):

- per-effect constitutional receipts for:
  - declaration snapshot
  - policy snapshot
  - lifecycle snapshot
  - approval evidence
  - governed data surfaces touched
- replay completeness at composition-chain level rather than effect equivalence alone
- composition governance at chain level
- revocation and incident handling
- registry/governed publication surface

What is still missing relative to [BUNDLE.md](BUNDLE.md):

- capability-token style runtime receipts instead of only in-memory grant structures
- a compact host ABI profile suitable for alternate inner runtimes like Wasmtime/components
- stable-broker-only policy for higher-risk governed skills
- broker-only enforcement beyond the current stable/transitional admission split
- brokered Wasm hostcalls that reuse the existing host ABI instead of bypassing it

## Target Architecture In Python First

### Host layer

The Python runtime becomes the host boundary.

It owns:

- policy engine
- admission state
- activation state
- capability store
- SQLite broker
- filesystem broker
- network broker
- tool broker
- audit / trace sink
- approval resolver
- incident / revocation state

### Skill layer

Skills remain as they are for now:

- knowledge artifacts
- Python abilities
- bash abilities
- ansible abilities

But at runtime they no longer conceptually "have access to the machine."
They receive an execution context with declared capabilities only.

### macOS layer

On macOS first, we treat host effects as named mediated services such as:

- `macos.open_browser`
- `macos.open_app`
- `macos.open_file`
- `macos.reveal_in_finder`
- `macos.capture_screenshot`
- `fs.read_mount`
- `fs.write_mount`
- `net.http`
- `store.named_query`
- `store.skill_state`

The implementation may use `open`, `osascript`, `subprocess`, `sqlite3`, or Python libraries internally, but the skill surface should never expose those raw mechanisms directly.

## Design Rule

Do not let the declaration describe only the skill.
Also let it describe the mediated effect surface the skill is allowed to use.

That means the current v2 declaration should remain, but runtime execution should add a second layer:

- declared authority
- issued capability grants
- actual mediated effect requests

This is the missing bridge between current governance metadata and real governed execution.

## Ordered Path From Here

Phases 1 through 7 of the original plan are now materially in place:

- host mediation
- capability grants
- lifecycle separation
- approval governance
- data governance and virtual mounts
- constitutional trace baseline
- replay bundle baseline

The remaining work is now about hardening that substrate and then adding Wasmtime without bypassing it.

### Phase 8: Constitutional Trace Hardening

Primary target:
- [OPEN_GOVERNANCE.md](OPEN_GOVERNANCE.md) sections 14 and 15
- [BUNDLE.md](BUNDLE.md) hostcall-level auditability

Do:

- attach explicit per-effect receipts for:
  - declaration snapshot
  - policy snapshot
  - lifecycle snapshot
  - approval evidence
  - governed data surfaces touched
  - grant receipt identity
- make composition-chain receipts first-class in the constitutional trace
- strengthen replay verification so it compares:
  - effect signatures
  - composition-chain signatures
  - declaration/policy/approval receipts

Success condition:

- a replay can show not only that the same answer happened, but that the same governed path justified it

### Phase 9: Stable Broker Surface Enforcement

Primary target:
- [BUNDLE.md](BUNDLE.md) logical handles instead of raw resources
- the existing `bssc.host.v1` surface in [host_abi.py](host_abi.py)

Do:

- tighten stable-only policy from admission holds into clearer broker-only enforcement tiers
- expand named tool mediation coverage while keeping raw subprocess semantics out of governed skills
- harden governed inter-skill invocation around explicit bindings, title resolution, and composition trace assertions

Success condition:

- the stable host ABI becomes the real contract surface for alternate inner runtimes

### Phase 10: Wasm Readiness Contract

Primary target:
- [BUNDLE.md](BUNDLE.md) Wasm inner boundary

Implemented now:

- define the first Wasm skill representation in import/export:
  - `executor_framework: wasm_wasi`
  - one Wasm body field
  - explicit exported entrypoint convention
- define the minimal initial Wasm skill ABI:
  - compute-oriented
  - no ambient host resources
  - typed input/output payload
- restrict the first Wasm tier to pure or near-pure skills:
  - deterministic transforms
  - parsers
  - mathematical or symbolic helpers

Still intentionally not in this phase:

- macOS/device automation in Wasm
- broad file access in Wasm
- broad network access in Wasm
- registry or incident system before the inner runtime exists

Success condition:

- Wasm skills have a governed artifact shape before they have a runtime

### Phase 11: First Wasmtime Linkage

Primary target:
- a minimal embedded Wasmtime runtime under Python host governance

Implemented now:

- add a new executor framework in [execution_frameworks.py](execution_frameworks.py):
  - `wasm_wasi`
- implement a Python-embedded Wasmtime runner
- run with default-empty WASI:
  - no ambient filesystem
  - no ambient network
  - no ambient SQLite
  - no ambient clock or randomness unless explicitly injected
- route execution through the same mediation and trace path as current executors

Success condition:

- one narrow Wasm skill can run under the existing governed runtime without introducing a second governance model

### Phase 12: Brokered Wasm Hostcalls

Primary target:
- reuse the existing stable host ABI inside Wasmtime

Implemented now:

- bridge Wasm imports to the stable broker subset in [host_abi.py](host_abi.py)
- current Wasm hostcall imports in `bssc.wasm.v1`:
  - `bssc.hostcall`
  - `bssc.read_hostcall_response`
- current bounded hostcall set:
  - `store.skill_state`
  - `store.named_query`
  - `fs.read_mount`
  - `fs.write_mount`
  - `fs.list_mount`
  - `fs.find_mount`
  - `tool.invoke`
  - `skill.invoke`
- governed Wasm hostcall traces are ingested back into parent trace state
- nested governed grants and effect traces from Wasm-mediated `skill.invoke` are ingested back into parent runtime state

Still pending in this phase:

- broader Wasm broker coverage beyond the bounded subset
- selected `net.*` surfaces

Keep the same:
  - lifecycle checks
  - approval checks
  - capability grants
  - constitutional trace
  - replay bundle model

Success condition:

- Wasmtime becomes an inner executor substitution, not a governance fork

### Phase 13: Composition, Revocation, Registry

Primary target:
- [OPEN_GOVERNANCE.md](OPEN_GOVERNANCE.md) sections 11 and 17 through 19

Do:

- governed inter-skill composition with explicit bindings
- revocation records and incident records
- quarantine and trust suspension
- local registry/publication surface

Implemented in this phase now:

- explicit composition-title binding for `skill.invoke`
- active revocation and open-incident lifecycle overlays at invocation time
- import/export support for `kind: revocation` and `kind: incident`
- local registry export:
  - `export-skill-registry`
  - `bssc_skill_registry.v1`
- replay-bundle governance receipts for:
  - policy / approval / revocation / incident titles
  - local registry identity snapshot

Still pending in this phase:

- richer registry publication semantics beyond a local exported index
- explicit revocation / incident receipts inside each per-effect constitutional trace

Success condition:

- trust and composition become governed lifecycle surfaces rather than static metadata

## Immediate Next Cut

The correct next implementation step is no longer first Wasmtime linkage. That stage is already in place.

It is now one of these two bounded follow-ups:

1. continue Phase 13 governance hardening:
   - include explicit revocation / incident receipts in replay bundles
   - add registry verification receipts or digests to exported run bundles
   - add stronger trust/quarantine state reporting for publication and audit
2. continue Wasm integration carefully:
   - selected `net.*` broker surfaces for Wasm under the stable ABI
   - any broader Wasm hostcall growth should build on the already-landed `skill.invoke` and `tool.invoke` path rather than reopening core linkage work

That keeps the order correct: Wasmtime remains an inner executor under the governed host, and new Wasm capability comes only through already-governed broker surfaces.

## What Not To Do Yet

Do not:

- rewrite the core around Rust first
- rewrite skills into Wasm first
- replace SQLite
- replace current CLI flows
- redesign the semantic controller
- widen current executors before mediation exists

Those would increase surface area without first strengthening governance.

## macOS-Specific Practical Notes

On macOS first:

- treat Finder/app/browser/file interactions as named mediated tools
- use virtual mounts instead of raw file path freedom
- keep browser/app launching behind explicit `tool.invoke` calls
- treat desktop-side effects as at least Tier 1, and sometimes Tier 2 or Tier 3 depending on data class and external communication
- if a packaged app comes later, map the same broker model onto Apple sandbox constraints rather than changing the governance model

## Expected Outcome

If this plan is followed in order:

- current features keep working
- current governance metadata starts controlling real effects
- trace and replay become constitutionally meaningful
- skill bundles and compositions become governable
- later Rust / Wasm work becomes an implementation substitution, not a governance rewrite
