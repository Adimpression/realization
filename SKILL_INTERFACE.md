# Skill Interface

`import-skill` and `export-skill` define the external governed skill interface.
`export-skill-registry` exports the current local governed registry index for installed skills.

The design is now split into three explicit layers:

1. a minimal artifact kernel for import survival
2. an optional compatibility envelope for foreign-surface lineage and projection
3. an optional governance envelope for audit-complete export

It also supports two schema generations:

- `bssc_skill.v1`
  - compact portable kernel
  - backward-compatible
  - no policy admission required
- `bssc_skill.v2`
  - declaration-first governed skill form
  - policy artifacts participate in admission
  - approval artifacts can satisfy non-automatic approval requirements during admission
  - non-policy skills are held unless admitted by installed policy
  - lifecycle state remains separate from admission and can still deactivate or quarantine a skill after admission

Export defaults:
- `export-skill` emits `bssc_skill.v2`
- stored v2 declarations are preserved as-is
- legacy artifacts with no stored declaration are exported with a synthesized conservative v2 declaration
- `import-skill` remains backward-compatible with both `bssc_skill.v1` and `bssc_skill.v2`
- brokered governed skills may also export a `governance.host_abi_version` field that pins the current host broker ABI

Old commands remain unchanged and are still useful for testing:
- `artifact-import`
- `artifact-export`

## Ability Delivery Boundaries

Shipping an ability and supplying the host operation that realizes it are
separate acts:

1. The portable ability declares intent, contracts, authority requirements,
   side effects, and its exact executor framework or governed broker surface.
2. `import-skill` compiles the document, evaluates policy and approvals, and
   persists its governed lifecycle and admission result.
3. An admitted ability becomes visible globally or through explicit subject
   scope. Retrieval may use deterministic semantic ranking and optional LLM
   assistance to select a visible candidate for an ordinary request.
4. The host independently supplies the named executor or broker. Runtime then
   checks current admission, lifecycle, authority, declared realizer identity,
   and host support before invoking that exact realizer.

Subject linkage does not admit a skill, grant authority, install an executor,
or create a broker. An LLM may assist candidate selection, but it does not
provide host support or choose an undeclared execution mechanism.

## Identity And Idempotence

Every skill document has an immutable `title`.

Import derives a deterministic artifact id from the normalized title:

```text
artifact-skill-<title-hash>
```

Repeated `import-skill` runs for the same title are therefore idempotent under the title-immutable assumption.

## Schema v1

Use v1 when you only need portable import/export survival.

Common kernel:

```yaml
schema: bssc_skill.v1
kind: knowledge | ability
title: <immutable title>
```

Optional compatibility envelope:

```yaml
compatibility:
  adapters:
    - direction: import | export
      format: <foreign surface name>
      name: <foreign callable name>
```

This envelope is optional on import and export.
It records foreign-surface lineage or projection intent without changing the canonical skill kernel.

Optional hosted metadata envelope:

```yaml
hosting_metadata:
  executor_framework: python3 | wasm_wasi | bash | ansible
  representation: python_script | wasm_module | shell_script | ansible_playbook
  entrypoint: <hosted entrypoint name>
```

This envelope is optional on export.
It projects canonical hosted-runtime metadata without changing the portable skill kernel.

### Minimal Knowledge Skill

```yaml
schema: bssc_skill.v1
kind: knowledge
title: What Is Force?
question: What is force?
answer: Force equals mass times acceleration.
```

Required kernel:
- `schema`
- `kind: knowledge`
- `title`
- `answer`

### Minimal Python Ability Skill

```yaml
schema: bssc_skill.v1
kind: ability
title: Open Browser URL
executor: python3
entrypoint: main
inputs:
  browser: browser application name
  url: target URL
outputs:
  status: open status
dependencies:
  - webbrowser
python: |
  def main(browser: str, url: str, __dependencies__: tuple[str, ...] = ()):
      import webbrowser
      webbrowser.open(url)
      return {"status": "opened", "browser": browser, "url": url}
```

### Minimal Shell Ability Skill

```yaml
schema: bssc_skill.v1
kind: ability
title: Find Symbol Occurrences
executor: bash
inputs:
  symbol: symbol to search
  root: search root
outputs:
  result: printed matches
shell: |
  rg -n "$symbol" "$root"
```

### Minimal Ansible Ability Skill

```yaml
schema: bssc_skill.v1
kind: ability
title: Ensure Package Installed
executor: ansible
inputs:
  package_name: package to install
ansible: |
  - hosts: localhost
    gather_facts: false
    tasks:
      - name: Ensure package is installed
        package:
          name: "{{ package_name }}"
          state: present
```

### Minimal Wasm Ability Skill

```yaml
schema: bssc_skill.v1
kind: ability
title: Say Hi From Wasm
executor: wasm_wasi
entrypoint: run
outputs:
  greeting: string greeting
wasm_abi_version: bssc.wasm.v1
wasm_format: wat
wasm: |
  (module
    (import "bssc" "write_output" (func $write_output (param i32 i32) (result i32)))
    (memory (export "memory") 1)
    (data (i32.const 0) "{\"status\":\"ok\",\"answer\":\"hi\",\"result\":{\"greeting\":\"hi\"}}")
    (func (export "run") (result i32)
      (drop (call $write_output (i32.const 0) (i32.const 55)))
      (i32.const 0)))
```

Current Wasm rules:
- `executor: wasm_wasi`
- body field: `wasm`
- current `wasm_format` default: `wat`
- current `entrypoint`: `run`
- current ABI version: `bssc.wasm.v1`
- current tier is compute-only:
  - no ambient filesystem
  - no ambient network
  - no ambient SQLite
  - no ambient stdio, clock, randomness, or environment

### Compatibility-Tier Declaration-Only Ability

```yaml
schema: bssc_skill.v1
kind: ability
title: repo_search
description:
  - Compatibility-tier imported OpenAI tool declaration.
inputs:
  symbol: required symbol to find
  root: workspace root
outputs:
  result: tool result
compatibility:
  adapters:
    - direction: import
      format: openai_tool
      surface: function
      name: repo_search
```

Rules:
- this is importable and exportable
- this preserves callable shape and foreign-surface lineage
- this is not automatically invokable until a hosted runtime implementation is attached
- compatibility metadata never overrides `title`, `kind`, or deterministic title-based identity

## Schema v2

Use v2 when the skill must be governed by declaration, risk tier, authority bounds, and policy admission.

### Declaration-First Skill

```yaml
schema: bssc_skill.v2
kind: ability
title: Open Browser URL
executor: python3
entrypoint: main
python: |
  def main(browser: str, url: str, __dependencies__: tuple[str, ...] = ()):
      import webbrowser
      webbrowser.open(url)
      return {"status": "opened", "browser": browser, "url": url}
declaration:
  intent: Open a browser URL.
  inputs:
    browser: browser application name
    url: target URL
  outputs:
    status: open status
  authorities_requested:
    - execute
  authority_bounds:
    execute:
      scope: local_desktop
      target: browser_application
      context: explicit_user_prompt
      duration: single_invocation
      triggering_conditions:
        - user invokes skill
      approval_class: automatic
  data_classes_touched:
    - public
  side_effects:
    - launch browser
  persistence_behavior: none
  invocation_rights:
    - direct_user_invocation
  composition_rights: []
  escalation_rights: []
  approval_requirements:
    - automatic
  risk_tier: tier1_bounded_transform
```

Required declaration fields in v2:
- `intent`
- `inputs`
- `outputs`
- `authorities_requested`
- `data_classes_touched`
- `side_effects`
- `persistence_behavior`
- `invocation_rights`
- `composition_rights`
- `escalation_rights`
- `approval_requirements`
- `risk_tier`

Required authority bound fields for every requested authority:
- `scope`
- `target`
- `context`
- `duration`
- `triggering_conditions`
- `approval_class`

Important rule:
- collection fields may be explicitly empty
- they still must be declared
- `composition_rights: []` and `escalation_rights: []` are valid declarations

### Lifecycle

`bssc_skill.v2` exports also carry a `lifecycle` block.

This is not part of the declaration kernel. It is current governed state.

Typical fields:
- `review_status`
- `admission_status`
- `installation_status`
- `activation_status`
- `trust_status`
- `quarantine_status`
- `status_reason`
- `updated_at`

### Host ABI

Brokered governed abilities may carry host-ABI metadata in their governance envelope:

- `governed_host_brokers`
- `governed_authorities`
- `host_abi_version`

Current runtime contract:

- `host_abi_version: bssc.host.v1`
- stable broker surfaces:
  - `fs.read_mount`
  - `fs.write_mount`
  - `fs.list_mount`
  - `store.named_query`
  - `store.skill_state`
  - `net.http_get_json`
  - `tool.invoke`
  - `skill.invoke`
  - named macOS brokers such as `macos.open_browser`
- transitional broker surfaces remain importable for compatibility:
  - `fs.read_text`
  - `fs.write_text`
  - `fs.list_directory`
  - `store.sqlite_query`

For higher-risk v2 Python skills, admission now expects governed host-ABI surfaces instead of:

- raw `sqlite3`
- raw path/file access
- raw network access
- raw tool/process invocation

### Wasm ABI

The first governed Wasm tier is intentionally narrower than the host broker ABI.

Current embedded Wasmtime contract:

- `executor: wasm_wasi`
- `host_abi_version` remains the outer governance contract when host mediation is involved
- `wasm_abi_version: bssc.wasm.v1`
- execution model:
  - embedded Wasmtime inside the Python host
  - the active Python environment must provide the `wasmtime` package
  - no ambient WASI resources
  - no raw access to host fs/net/sqlite

Current `bssc.wasm.v1` imports:
- `bssc.input_len() -> i32`
- `bssc.read_input(ptr: i32) -> i32`
- `bssc.write_output(ptr: i32, len: i32) -> i32`
- optional governed hostcall imports:
  - `bssc.hostcall(ptr: i32, len: i32) -> i32`
  - `bssc.read_hostcall_response(ptr: i32) -> i32`

Current required exports:
- `memory`
- `run() -> i32`

Current transport:
- host passes one UTF-8 JSON input payload
- module returns one UTF-8 JSON output payload
- optional governed hostcalls use one UTF-8 JSON request/response payload per call
- `run()` returns process-style exit code semantics:
  - `0` for success
  - nonzero for failure

Current Wasm hostcall subset:
- `fs.read_mount`
- `fs.write_mount`
- `fs.list_mount`
- `fs.find_mount`
- `store.named_query`
- `store.skill_state`
- `tool.invoke`
- `skill.invoke`

Important constraint:
- this subset is narrower than the full host broker ABI
- Wasm skills do not get ambient WASI resources
- Wasm hostcalls remain mediated through the same grants and declaration checks as other governed execution
- Wasm `skill.invoke` promotes nested governed grants and effect traces back into the parent runtime trace surface

Example:

```yaml
lifecycle:
  review_status: pending_review
  admission_status: admitted
  installation_status: installed
  activation_status: active
  trust_status: trusted
  quarantine_status: clear
  status_reason: Skill is installed, active, and trusted for invocation.
  updated_at: "2026-03-31T12:00:00+00:00"
```

Runtime rule:
- admission alone is not enough
- a v2 skill must also be installed, active, trusted, and not quarantined to be invokable

### Policy Artifact

```yaml
schema: bssc_skill.v2
kind: policy
title: Local Admission Policy
policy:
  intent: Admit only bounded local abilities.
  target_kinds:
    - ability
  max_risk_tier: tier2_connected
  allowed_authorities:
    - read
    - write
    - execute
    - persist
    - export

### Approval Artifact

```yaml
schema: bssc_skill.v2
kind: approval
title: Operator Approval For Open Browser URL
approval:
  intent: Approve browser opening for the named skill.
  approval_class: operator_approved
  subject_titles:
    - Open Browser URL
  subject_kinds:
    - ability
  approved_authorities:
    - execute
  approved_risk_tiers:
    - tier1_bounded_transform
  issued_by: operator://local-admin
  rationale: Operator approved bounded local browser launch.
  status: approved
```

Required approval fields in v2:
- `intent`
- `approval_class`
- `subject_titles`
- `issued_by`
- `rationale`

Optional narrowing fields:
- `subject_kinds`
- `approved_authorities`
- `approved_risk_tiers`
- `valid_from`
- `valid_until`
- `status`

Admission rule:
- if policy requires `automatic`, no approval artifact is needed
- if policy requires a stronger class like `operator_approved`, a matching approval artifact may satisfy that requirement
- approval artifacts are governance records, not invokable skills
- invocation re-checks current installed policy and approval artifacts instead of trusting only the stored import-time admission snapshot
- a revoked or expired approval can therefore deny a previously admitted skill at runtime
- a newly installed matching approval can allow a previously held skill at runtime, subject to lifecycle state
  denied_authorities:
    - approve
    - modify
    - escalate
  allowed_executors:
    - python3
    - bash
  allowed_data_classes:
    - public
    - internal
  denied_side_effects:
    - external human contact
  required_approval_for_risk_tiers:
    tier3_sensitive: operator_approved
    tier4_agentic: organization_approved
    tier5_sovereign: prohibited
```

Policy artifacts are stored as governed records and are not invokable answer artifacts.

## Admission Semantics

For `bssc_skill.v2`:

- policy artifacts are imported first
- non-policy skills are evaluated against installed policy artifacts
- the resulting admission record is stored on the artifact as `skill_admission`

Admission outcomes:
- `admitted`
  - usable at runtime
- `held`
  - stored but not executable / not answer-capable
  - typical cause: no policy installed or explicit approval still required
- `rejected`
  - stored admission result records the policy conflict
  - not executable / not answer-capable

Current rule:
- v1 artifacts remain backward-compatible and usable without policy admission
- v2 non-policy artifacts are not usable until their admission status is `admitted`

## Governance Envelope

The export path can also include a `governance` block. This is optional on import.

Example:

```yaml
governance:
  scope: reuse when the same or closely related item appears again under an ordinary stable reading
  justification: Imported knowledge artifact from YAML.
  function_bit: 0
  boundary_shape:
    - d*
  reusability: local_reuse
  admissibility: admitted
  learning_relation: new_family
  created_at: 2026-03-31T12:00:00Z
  provenance:
    - imported
  constraints: []
  template_schema: {}
  related_artifact_ids: []
  structured_learning: {}
  virtual_mounts:
    skill_output:
      root: /tmp/skill-output
      permissions: [read, write, list]
      data_class: public
  named_queries:
    artifact_count:
      sql: SELECT COUNT(*) AS artifact_count FROM artifacts
      parameter_order: []
      data_class: internal
  skill_state_namespace: artifact-skill-demo
```

Governance never overrides the kernel:
- not `title`
- not `kind`
- not deterministic title-based identity

Governance may extend the runtime surface:
- `virtual_mounts`
- `named_queries`
- `skill_state_namespace`

Those fields are optional on import, but when present they survive import/export and become available to the governed broker layer.

## Glossary

- region
  - one boundary namespace such as `a`, `a'`, `b`, `b'`, `c`, `c'`, `d`, or `d'`
- carrier
  - the polarity of one leaf, such as a concrete value or a reference-like input
- leaf
  - one typed canonical datum projected onto a deterministic region-prefixed path
- canonical path notation
  - the deterministic `/region/...` path language used to identify normalized leaves
- reconstructibility
  - the requirement that the structured interaction body can be rebuilt conservatively from the normalized ledger
- opaque leaf
  - one fallback normalized leaf used when structure cannot be recovered safely without inventing detail

## Interface Invariants

- kernel identity is title-stable
  - neither compatibility metadata nor governance metadata can override `title`, `kind`, or deterministic title-based identity
- compatibility metadata is descriptive, not authoritative
  - `compatibility` records foreign-surface lineage and export intent; it does not become the hosted runtime body
- governance metadata is additive, not kernel-defining
  - `governance` can extend admission, mounts, queries, and hosted context, but it does not redefine the kernel
- hosted metadata is projected, not persisted as a second truth
  - `hosting_metadata` exposes canonical hosted-runtime facts already recoverable from the artifact and canonical IR
- normalization stays region-preserving
  - canonical paths and leaves remain anchored to explicit boundary regions instead of collapsing into one untyped payload
- normalization stays reconstructible
  - when structure is unclear, the interface should prefer opaque leaves over invented detail
- invocation and composition should stay explainable
  - receipt surfaces should be able to show requested bindings, bound leaves, and composition lineage without raw debugging payloads

## Commands

Export one skill:

```bash
uv run realized-compatibility export-skill \
  --skill-title "What Is Force?" \
  --sqlite state/common.sqlite3
```

Export the local governed registry index:

```bash
uv run realized-compatibility export-skill-registry \
  --out /tmp/skill-registry.yaml \
  --sqlite state/common.sqlite3
```

Import one skill:

```bash
uv run realized-compatibility import-skill \
  --skill-file /tmp/force.skill.yaml \
  --sqlite state/common.sqlite3
```

Batch export:

```bash
uv run realized-compatibility export-skill \
  --skill-titles-file /tmp/skill_titles.json \
  --out-dir /tmp/skills \
  --sqlite state/common.sqlite3
```

Batch import:

```bash
uv run realized-compatibility import-skill \
  --skill-dir /tmp/skills \
  --normalized-out-dir /tmp/normalized_skills \
  --sqlite state/common.sqlite3
```
