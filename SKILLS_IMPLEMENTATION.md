# Skills Implementation

Implementation tracker for the theory-backed skill model in [SKILLS.md](SKILLS.md), grounded in section 4.6 of [THEORY.md](THEORY.md).

## Purpose

This file turns the skill product model into an implementation plan.

The detailed testing strategy for this implementation lives in [SKILLS_TEST_PLAN.md](SKILLS_TEST_PLAN.md).

The central implementation move is:

- treat skills as canonical governed reusable forms
- compile community inputs into hosted governed skills
- make invocation and composition operate over a region-aware canonical path ledger

This is not a “rewrite everything at once” plan.

It is a staged migration plan that preserves:

- current `bssc_skill.v1` and `bssc_skill.v2` import/export behavior
- current governed installation and lifecycle logic
- current workstation skill UX
- current executor surfaces

## Scope

In scope:

- canonical skill IR
- boundary normalization
- leaf inventory and canonical path notation
- skill compiler pipeline
- compatibility adapters for community formats
- unified invocation contract
- leaf-level composition calculus
- richer permission and receipt semantics for composed skills
- registry and sharing implications

Out of scope for the first implementation cuts:

- replacing the workstation shell
- replacing the controller with workstation
- forcing all executors into Wasmtime
- removing `python3`, `bash`, or `ansible`
- rewriting all existing skills into the new normal form immediately

## Current Codebase Position

The current substrate is already strong enough to support a staged implementation.

Current working surfaces:

- skill schema and import/export:
  - [SKILL_INTERFACE.md](SKILL_INTERFACE.md)
  - [skill_schema_io.py](skill_schema_io.py)
  - [skill_export_projection.py](skill_export_projection.py)
  - [governed_skill_installation.py](governed_skill_installation.py)
- skill governance and lifecycle:
  - [skill_governance.py](skill_governance.py)
  - [skill_lifecycle.py](skill_lifecycle.py)
  - [skill_safety_governance.py](skill_safety_governance.py)
- runtime execution:
  - [execution_frameworks.py](execution_frameworks.py)
  - [wasm_skill_runtime.py](wasm_skill_runtime.py)
  - [python_skill_host.py](python_skill_host.py)
  - [host_brokers.py](host_brokers.py)
- learning and functionalization:
  - [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
  - [execution_frameworks.py](execution_frameworks.py)
  - [python_skill_brokerization.py](python_skill_brokerization.py)
- workstation skill handling:
  - [workstation/skill_management.py](workstation/skill_management.py)
  - [workstation/skill_invocation.py](workstation/skill_invocation.py)
  - [workstation/direct_composition.py](workstation/direct_composition.py)
  - [workstation/capabilities.py](workstation/capabilities.py)

What is missing is not “skill support.”

What is missing is the formal middle layer that makes:

- compilation explicit
- community compatibility first-class
- composition mechanical
- invocation portable across runtime surfaces

## Implementation Gap

Today, the system has:

- titles
- declarations
- runtime bodies
- governance artifacts
- invocation helpers

It does not yet have a first-class canonical boundary normal form.

That causes four practical problems:

1. Composition remains heuristic
- mostly based on prompt inference and ad hoc payload derivation

2. Compatibility imports are shallow
- they can survive import, but they are not compiled into a strongly normalized execution form

3. Invocation contracts are underspecified
- top-level names and prompt shaping do too much work

4. Observability is too coarse
- receipts show invocation and outcomes, but not canonical field-level binding

The implementation plan is therefore centered on one new substrate:

- region-aware canonical path ledgers

Important codebase constraint:

- persisted truth in this repo is still the `Artifact` envelope from [applied_theory_types.py](applied_theory_types.py)
- boundary shape terms already exist there and in [pure_theory_types.py](pure_theory_types.py)
- the new skill model must extend that artifact-centered substrate rather than introduce a second competing persistent object model

## Core Implementation Principle

The canonical object for skill interaction should be:

- a declaration-first governed skill
- plus a canonical path-typed leaf ledger over:
  - `a`
  - `a'`
  - `b`
  - `b'`
  - `c`
  - `c'`
  - `d`
  - `d'`

This ledger should become the shared substrate for:

- compiler output
- invocation binding
- compatibility import/export
- composition
- observability

## Formal Requirements From Theory 4.6

The implementation should follow the formal shape from section 4.6 of [THEORY.md](THEORY.md), not just its general motivation.

The core normalization law is:

- `semantic body -> typed path ledger`

For each boundary region `r`, the implementation should realize:

- `Φ_r(x)`
  - region-local normalization from a structured body `x` into a typed path ledger

And for a full interaction:

- `N(f)`
  - the union of the normalized ledgers over `a, a', b, b', c, c', d, d'`

The implementation invariants are not optional. They should be encoded in tests:

- total
  - every semantically relevant leaf is represented
- stable
  - equivalent bodies normalize to the same path structure
- typed
  - every leaf carries a declared type
- polarity-preserving
  - value vs reference survives normalization
- region-preserving
  - the eight boundary regions stay distinct
- multiplicity-preserving
  - repeated elements remain distinguishable
- reconstructible
  - the structured body can be rebuilt from the ledger

The path language should be implemented as canonical path notation, not as an XML- or JSON-specific one-off.

That means:

- deterministic path formatting
- array support
- map support
- escaping rules
- region-prefixed namespaces such as `/a/...` and `/d'/...`

This section is the hard constraint behind the module plan below.

## Proposed Module Plan

The cleanest implementation is to add a dedicated skill-normalization and skill-composition slice at repo root, not under `workstation/`.

But it should be artifact-centered, not parallel-persistence-centered.

Recommended new modules:

- `skill_leaf_types.py`
  - canonical leaf classes
  - carrier kind enum
  - leaf-type declarations
  - reuse existing boundary-region terms from [applied_theory_types.py](applied_theory_types.py) and [pure_theory_types.py](pure_theory_types.py) instead of introducing a second region enum
- `skill_path_notation.py`
  - canonical path notation rules
  - escaping
  - array indexing
  - path validation and comparison
- `skill_boundary_normalization.py`
  - `Φ_r(x)` normalization
  - total interaction normal form
  - reconstructibility helpers
  - opaque-leaf handling
- `skill_ir.py`
  - canonical skill IR projection helpers
  - artifact-to-IR and IR-to-artifact-content projection
  - declaration + normalization + runtime package references
  - should not replace `Artifact` as the persisted store object
- `skill_compiler.py`
  - community input to canonical hosted skill compilation
  - enrichment and analysis orchestration
- `skill_compatibility_import.py`
  - adapters for MCP, OpenAI tools, Semantic Kernel, LangChain, instruction skills
- `skill_compatibility_export.py`
  - export adapters back into supported community shapes
- `skill_invocation_contract.py`
  - one canonical invocation request and invocation result shape
- `skill_composition.py`
  - leaf-level compatibility calculus
  - binding planner
  - pipeline wiring helpers
- `skill_aliasing.py`
  - aliases
  - family names
  - natural-language trigger hints
- `skill_observability.py`
  - skill-specific receipt shaping for leaf bindings, composition, and compiler lineage

Existing modules to extend rather than replace:

- [applied_theory_types.py](applied_theory_types.py)
  - remains the persisted artifact envelope and boundary-shape carrier
- [pure_theory_types.py](pure_theory_types.py)
  - remains the theory-bearing source of canonical boundary terms
- [skill_schema_io.py](skill_schema_io.py)
  - read and write normalization metadata
- [skill_export_projection.py](skill_export_projection.py)
  - emit canonical boundary-normalized exports
- [governed_skill_installation.py](governed_skill_installation.py)
  - invoke compiler pipeline before persistence
- [skill_governance.py](skill_governance.py)
  - admit normalized skills, not just declarations
  - extend existing `composition_rights` handling rather than creating a second composition policy surface
- [execution_frameworks.py](execution_frameworks.py)
  - expose declared executor capabilities into normalized hosting metadata
  - continue serving as the fence-learning and executable-body synthesis seam
- [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
  - route markdown-learned executable payloads through the compiler path instead of leaving them as a parallel learning path
- [python_skill_brokerization.py](python_skill_brokerization.py)
  - continue supplying host-brokerization and data-surface assessment into compiler analysis
- [workstation/skill_invocation.py](workstation/skill_invocation.py)
  - bind prompts and direct asks through the canonical invocation contract
  - project current `input_contract` and declaration fields into the normalized invocation shape
- [workstation/direct_composition.py](workstation/direct_composition.py)
  - resolve via leaf-level compatibility instead of prompt-only heuristics
- [workstation/capabilities.py](workstation/capabilities.py)
  - surface richer invocation, composition, and receipt semantics

## Phase Plan

### Phase 0: Documentation And Invariants

Goal:

- lock the theory-backed model before writing new normalization code

Deliverables:

- [x] [SKILLS.md](SKILLS.md) formalized against theory section 4.6
- [x] this implementation tracker
- [x] add glossary and invariants to [SKILL_INTERFACE.md](SKILL_INTERFACE.md):
  - region
  - carrier
  - leaf
  - canonical path notation
  - reconstructibility
  - opaque leaf

### Phase 1: Canonical Leaf And Path Substrate

Goal:

- create the mathematical objects from theory as code

Deliverables:

- `skill_leaf_types.py`
- `skill_path_notation.py`
- `skill_boundary_normalization.py`

Integration rule:

- reuse existing boundary-region terms from [applied_theory_types.py](applied_theory_types.py) and [pure_theory_types.py](pure_theory_types.py)
- do not introduce a second independently named region algebra

Required behavior:

- normalize values and references separately
- preserve region and polarity
- produce stable path ledgers
- support arrays and maps
- support reconstructibility
- support partial normalization through opaque leaves
- implement `Φ_r(x)` explicitly for each region
- make `N(f)` a first-class computed form for full interactions

Tests:

- `tests/test_skill_boundary_normalization.py`
- `tests/test_skill_path_notation.py`
- `tests/test_skill_ir.py`

Exit condition:

- a structured boundary body can be flattened and reconstructed deterministically

Current status:

- implemented
- canonical normalization metadata is synthesized conservatively for legacy imports

### Phase 2: Canonical Skill IR

Goal:

- create one explicit in-memory object model for canonical hosted skills

Deliverables:

- `skill_ir.py`
- extension of [skill_schema_io.py](skill_schema_io.py)
- extension of [skill_export_projection.py](skill_export_projection.py)

Structural rule:

- canonical skill IR should be an artifact-centered projection
- persistence remains through `Artifact.content` plus existing declaration/lifecycle/governance fields
- the store schema should not be forked into a second skill-only persistence model

Required fields:

- declaration
- lifecycle
- runtime package reference
- normalization metadata
- canonical boundary normal form
- aliases and family metadata
- hosting metadata

Backward-compatibility rule:

- `bssc_skill.v1` and existing `bssc_skill.v2` imports remain valid
- missing normalization metadata is synthesized conservatively
- canonical ledgers can be partial initially
- existing `input_contract`, `output_contract`, `executor_framework`, `skill_declaration`, and `skill_lifecycle` fields remain the bridge fields during migration

Tests:

- extend [tests/test_skill_io.py](tests/test_skill_io.py)
- add [tests/test_skill_ir.py](tests/test_skill_ir.py)

Exit condition:

- import and export preserve a canonical skill IR even for legacy skills

Current status:

- implemented for artifact-centered projection, alias/family metadata, runtime package reference, and hosting metadata
- import/export now preserve the projection additively without changing store schema

### Phase 3: Skill Compiler

Goal:

- turn “learning as compilation” into a real pipeline

Deliverables:

- `skill_compiler.py`
- compiler entry seam inside [governed_skill_installation.py](governed_skill_installation.py)

Early integration points:

- [external_markdown_learning_pipeline.py](external_markdown_learning_pipeline.py)
- fence-learning helpers in [execution_frameworks.py](execution_frameworks.py)
- brokerization and surface analysis in [python_skill_brokerization.py](python_skill_brokerization.py)

Compiler stages:

1. parse source
2. normalize into intermediate representation
3. enrich
4. analyze
5. emit canonical hosted skill IR
6. hand off to governance and persistence

Analysis should include:

- executor compatibility
- dependency presence
- authority synthesis and validation
- boundary normalization completeness
- reconstructibility
- portability warnings

Tests:

- `tests/test_skill_compiler.py`
- extend [tests/test_markdown_learning.py](tests/test_markdown_learning.py) where relevant

Exit condition:

- imports route through a compiler, not just schema hydration plus installation
- markdown- and fence-derived executable learning also routes through the same compiler path rather than a parallel bespoke path

Current status:

- initial compiler seam implemented for governed portable-skill installation in [governed_skill_installation.py](governed_skill_installation.py)
- compiler summaries are now emitted in import reports
- markdown and fence learning are not yet routed through the compiler

### Phase 4: Compatibility Adapters

Goal:

- treat community skill ecosystems as first-class learning inputs

Deliverables:

- `skill_compatibility_import.py`
- `skill_compatibility_export.py`

Initial import targets:

- MCP:
  - tools
  - prompts
  - resources
- OpenAI tool or function definitions
- Semantic Kernel plugins
- LangChain tools and toolkits
- Codex or Claude-style instruction skill bundles

Implementation rule:

- adapters ingest into canonical boundary normal form
- adapters do not become the hosted runtime model

Tests:

- `tests/test_skill_compatibility_import.py`
- `tests/test_skill_compatibility_export.py`

Current implemented first cut:

- [skill_compatibility_import.py](skill_compatibility_import.py)
  - OpenAI function-tool import adapters
  - MCP tool import adapters
  - instruction-skill bundle import adapters
  - explicit normalized `compatibility.adapters` projection
- [skill_compatibility_export.py](skill_compatibility_export.py)
  - OpenAI function-tool export projection
  - MCP tool export projection
  - instruction-skill bundle export projection
- [skill_schema_io.py](skill_schema_io.py) and [skill_export_projection.py](skill_export_projection.py)
  - `compatibility` now round-trips through `content["skill_compatibility"]`
  - compatibility-tier imported abilities can persist without a hosted executor body

Exit condition:

- at least one representative format from each target ecosystem compiles into canonical hosted skill IR

### Phase 5: Unified Invocation Contract

Goal:

- unify runtime, workstation, and future API invocation shape

Deliverables:

- `skill_invocation_contract.py`
- integration into [workstation/skill_invocation.py](workstation/skill_invocation.py)
- integration into [governed_semantic_reduction_runtime.py](governed_semantic_reduction_runtime.py) through shared substrate use

Required behavior:

- direct named invocation
- LLM-routed invocation
- canonical normalized input binding
- delegated-capability request binding
- leaf-level binding records

Migration rule:

- the canonical invocation contract must project cleanly from the current declaration and `input_contract` / `output_contract` fields
- workstation should not need a second separate prompt-only binding model while migration is in flight

Tests:

- extend [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)
- add `tests/test_skill_invocation_contract.py`

Current implemented first cut:

- [skill_invocation_contract.py](skill_invocation_contract.py)
  - canonical invocation request record
  - canonical invocation result record
- [workstation/skill_invocation.py](workstation/skill_invocation.py)
  - workstation request/result projection helpers over the shared contract
- [workstation/capabilities.py](workstation/capabilities.py)
  - `ws.skill.invoke` now emits `invocation_request` and `invocation_result`

Exit condition:

- all invocation paths can produce a canonical invocation record even when prompted conversationally

### Phase 6: Composition Engine

Goal:

- replace prompt-only composition heuristics with leaf-level compatibility calculus

Deliverables:

- `skill_composition.py`
- composition helpers for workstation and runtime

Current implemented first cut:

- explicit two-skill leaf binding analysis
- explicit sequence-plan validation
- branch-condition and iteration-condition validation
- plan-wide authority aggregation
- trial-backed readiness checks that distinguish exact vs mapper-required composition
- executable composition plans over explicit bindings
- structured mapper specs for composition bindings
- dict-shaped composition plans suitable for LLM-produced mapper payloads
- binding receipts that record source value, mapper kind, and mapped value per step
- explicit mapper functions over source leaves, not just payload-to-payload copying
- additive workstation execution surface via `ws.skill.compose`
- workstation composition execution reusing governed `ws.skill.invoke` permission and approval semantics per step
- structured step-output propagation through workstation composition using `parsed_output` / `result_payload` before answer-text fallback
- bounded automatic workstation composition planning for obvious multi-step prompts before the generic LLM loop
- additive planner support for explicit `run_if` conditions over prior-step output leaves
- additive planner support for explicit branching via inverse `run_if` conditions over prior-step output leaves
- additive planner support for explicit `iterate_until` conditions over current-step output leaves
- compose-result fallback to the last executed branch output when a later planned branch is skipped
- additive Blend workflow projection via:
  - [blend_workflow.py](blend_workflow.py)
  - `workflow_plan` input support on `ws.skill.compose`
  - `workflow_plan` and `workflow_run` result projections from `ws.skill.compose`
  - persisted workflow objects written under the workstation root and indexed via `BLEND_WORKFLOWS.json`
- focused workstation regressions for:
  - explicit two-step mapping execution
  - bounded three-step pipeline execution
  - planner-built conditional composition from one ordinary prompt
  - planner-built branching composition from one ordinary prompt
  - planner-built iterative composition from one ordinary prompt
  - approval-required halting on a write step
  - LLM-emitted `ws.skill.compose` tool calls
  - automatic read-then-write composition from one ordinary prompt
  - additive workflow-plan projection into and out of `ws.skill.compose`

Composition layers:

1. boundary class compatibility
2. canonical path-ledger matching
3. semantic label and carrier adaptation

Supported modes:

- step-wise
- iterative
- pipeline
- algorithmic composition

Initial scope:

- exact leaf match
- type-compatible leaf match
- semantic-label-compatible leaf match
- explicit mapper kinds:
  - `identity`
  - `rename`
  - `first_item`
  - `project_field`
- explicit fallback to user or model clarification when the match is not provable

Tests:

- `tests/test_skill_composition.py`
- targeted workstation composition regressions in [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)
- partial real workstation trial validation slices should stay green while this phase lands, starting with `python` and `ansible`

Current boundary:

- the composition engine is executable and the workstation can call it through `ws.skill.compose`
- first-class workstation workflow execution and query now exist through:
  - `ws.workflow.run`
  - `ws.workflow.list`
  - `ws.workflow.get`
- prompt-local planner execution now prefers `ws.workflow.run`, while `ws.skill.compose` remains a compatibility wrapper
- planner/runtime auto-synthesis of composition plans now exists for bounded multi-step, conditional, branching, and iterative prompts, but it is still intentionally conservative and not yet a broad free-form workflow planner
- Blend workflow objects are now persisted and queried through a shared root-level workflow store/query module, but the current backing store is still workstation-root-scoped and not yet a broader shared workflow registry across all runtimes
- shared workflow execution now also exists below workstation through [blend_workflow_execution.py](blend_workflow_execution.py), including provider-based step resolution over shared operator providers, while workstation remains the invocation adapter
- shared operator catalog/query now also exists below workstation through [blend_operator_store.py](blend_operator_store.py), including shared provider factories for dynamic skill and capability operators, with workstation exposing that seam via `ws.operator.list` and `ws.operator.get`

Next sequencing:

- first keep expanding trial-backed coverage and planner robustness on the existing bounded multi-step / conditional / branching / iterative leaf substrate
- then continue widening the shared operator and workflow execution surfaces beyond workstation-owned skill adapters so controller/runtime/workstation can all drive first-class workflow objects through the same engine
- then continue injecting the broader Blend substrate beneath that path, starting from the additive `BlendContext` / `BlendSession` seam, the shared world continuity/query seam, and then widening beyond workstation-root-backed workflow storage
- see [BLEND_IMPLEMENTATION.md](BLEND_IMPLEMENTATION.md)

Exit condition:

- a pipeline can bind fields mechanically when ledgers prove compatibility

### Phase 7: Permission And Receipt Deepening

Goal:

- make composition and invocation observable and governable at leaf level

Deliverables:

- `skill_observability.py`
- extensions to [host_interaction_receipts.py](host_interaction_receipts.py)
- workstation activity formatting updates where useful

Required receipts:

- compiler lineage
- canonical skill normalization summary
- invocation requested leaves
- auto-bound vs explicit-bound leaves
- permission escalation per step
- emitted leaves summary

Tests:

- extend [tests/test_host_interaction_receipts.py](tests/test_host_interaction_receipts.py)
- extend workstation receipt tests

Current implemented first cut:

- [host_interaction_receipts.py](host_interaction_receipts.py)
  - capability-call receipts now project top-level `invocation` data from `invocation_request` / `invocation_result`
  - capability-call receipts now project top-level `composition` lineage from requested skills, final output selection, and per-step binding / condition receipts
- [workstation/capabilities.py](workstation/capabilities.py)
  - workstation invocation and composition surfaces already emit the structured fields that the shared receipt layer now projects
- focused workstation receipt regressions
  - delegation projection
  - invocation-contract projection
  - composition-lineage projection

Exit condition:

- receipts can explain skill binding and composition without raw debugging

### Phase 8: Registry, Sharing, And Hosted Policy

Goal:

- make canonical hosted skills shareable without weakening trust semantics

Deliverables:

- canonical registry projection updates
- compatibility export projections
- provenance and deprecation metadata extensions

Target modules:

- [skill_registry.py](skill_registry.py)
- [skill_export_projection.py](skill_export_projection.py)
- [governance_inventory.py](governance_inventory.py)

Current implemented first cut:

- [skill_export_projection.py](skill_export_projection.py)
  - export documents now project canonical `hosting_metadata`
- [skill_registry.py](skill_registry.py)
  - registry entries now project canonical hosted metadata plus compiler-summary fields:
    - `family`
    - `alias_count`
    - `compatibility_formats`
    - `normalized_regions`
    - `normalization_leaf_counts`
    - `hosting_metadata`

Exit condition:

- canonical hosted skills can be published with clear lineage, trust tier, and compatibility exports

## Migration Rules

The migration must preserve existing behavior while gradually increasing formal strength.

Rules:

- do not break `bssc_skill.v1`
- do not require every old skill to declare a full canonical ledger on day one
- synthesize conservative normalization metadata for legacy imports
- treat unresolved structures as opaque leaves instead of inventing fake detail
- prefer additive schema evolution over breaking field replacements
- keep current workstation commands and chat flows stable while moving them onto the new invocation contract internally

## Runtime Strategy

The runtime strategy should remain explicit:

- `wasm_wasi`
  - preferred public hosted tier
- `python3`
  - compatibility tier
- `bash`
  - compatibility tier
- `ansible`
  - specialized operational tier

Important rule:

- canonical normalization does not imply sandboxing
- runtime tier and trust tier remain separate fields

## Workstation Strategy

The workstation should consume the canonical skill model, not own it.

That means:

- no `workstation/`-only definition of canonical ledgers
- no workstation-specific composition model
- no separate workstation-only invocation schema

The workstation should instead:

- catalog canonical skills
- preview canonical inputs and outputs
- invoke through the shared contract
- display receipts and activity using canonical binding data

## Controller And Runtime Strategy

The governed runtime should not import workstation shell code.

The correct convergence remains:

- shared host-interaction substrate
- shared invocation contract
- shared canonical skill model

Not:

- runtime depending on workstation internals

## Validation Plan

Minimum gates by phase:

- normalization unit tests
- skill schema and import/export regression tests
- workstation invocation regressions
- fresh-db trial validation for representative skill families
- full unit suite

Suggested progressive gate order:

1. unit tests for new canonical modules
2. [tests/test_skill_io.py](tests/test_skill_io.py)
3. [workstation/tests/test_workstation.py](workstation/tests/test_workstation.py)
4. trial-domain slices for representative skill families
5. full test suite

## Tracker

- [x] formalize the theory-backed skill product model in [SKILLS.md](SKILLS.md)
- [x] define the implementation plan in this file
- [x] add canonical leaf, region, and path notation types
- [x] add boundary normalization and reconstruction helpers
- [x] extend canonical skill IR with normalization metadata
- [x] route governed installation through a compiler pipeline
- [x] add compatibility import adapters
- [x] add compatibility export adapters
- [x] add a unified invocation contract
- [x] replace prompt-only composition with leaf-level compatibility calculus
- [x] extend receipts with leaf binding and composition lineage
- [x] extend registry and export surfaces with hosted canonical metadata
- [x] add glossary and invariants to [SKILL_INTERFACE.md](SKILL_INTERFACE.md)

## Non-Goals

- do not pretend `python3` or `bash` are Wasm-isolated
- do not collapse skill declarations into session permission grants
- do not force all skill usage through chat
- do not make community formats direct hosted truth
- do not couple the runtime to workstation shell code
- do not bypass governance just because a skill compiled successfully

## Success Condition

This implementation is successful when:

- a community skill can be ingested as a learning input
- the compiler produces a canonical governed skill with a stable boundary normal form
- invocation can bind canonical leaves deterministically where compatibility is sufficient
- composition can be resolved mechanically at field level instead of mainly by prompt heuristics
- workstation and runtime can both consume the same invocation and composition substrate
- the user can still use skills naturally in chat and directly in CLI without learning the internal theory first
