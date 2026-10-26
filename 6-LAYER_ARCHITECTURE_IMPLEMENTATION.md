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

## Package-Native Boundary Convergence

### Purpose

The host-interaction extraction completed one bounded architectural cut. It did
not complete the larger transition from a root-hosted implementation graph to
package-native ownership.

The next program must make the theory-defined responsibilities real in source,
dependency, distribution, and public-interface boundaries while preserving the
behavior of this highly qualified repository. The objective is not to remove
every Python file from the repository root. The objective is that canonical
behavior has one cohesive owner and that root files are limited to deliberate
entrypoints, validation programs, and temporary compatibility facades.

This is a strangler migration. Every cut must be independently reviewable,
revertible, and behavior-preserving.

### Meaning Of Package-Native

A responsibility is package-native only when all of the following are true:

- [ ] Its canonical source lives under the owning project's import package.
- [ ] Its public API is explicit, narrow, and exported through a tested
  `__all__` or equivalent package surface.
- [ ] Its project metadata declares every runtime dependency it imports.
- [ ] Its canonical modules do not import repository-root implementation
  modules.
- [ ] Its wheel and source distribution can be built and exercised without the
  repository root on `sys.path`.
- [ ] Historical import paths, where still required, are one-way compatibility
  facades over the canonical package implementation.
- [ ] Compatibility facades preserve documented object identities and do not
  acquire new behavior.
- [ ] The architecture ratchet recognizes the canonical owner and rejects new
  dependencies on the displaced root implementation.
- [ ] Persisted schemas, identifiers, receipts, command output, and externally
  visible workflow behavior remain compatible unless a separately approved
  migration explicitly changes them.

### Migration Protocol

- [ ] Treat current qualified behavior as the compatibility baseline; do not
  combine source relocation with semantic redesign.
- [ ] Move one cohesive dependency edge or tightly coupled cluster at a time;
  do not perform repository-wide import rewrites in one change.
- [ ] Introduce the canonical package implementation before changing consumers.
- [ ] Replace the historical module with a minimal re-exporting facade only
  after equivalence and object-identity tests pass.
- [ ] Migrate one consumer class at a time: core, workstation, entry/exchange,
  then tests and trials.
- [ ] Update package metadata and the architecture manifest in the same change
  that introduces the real dependency.
- [ ] Run the slice-specific gates and the global deterministic gates before
  beginning the next cut.
- [ ] Retain each compatibility path for at least one complete qualification
  cycle after the last production consumer moves.
- [ ] Delete a compatibility facade only after repository search, wheel
  inspection, isolated installation, and tests prove that it has no supported
  consumer.
- [ ] If an assumption below fails, stop that workstream, record the evidence,
  revise this plan, and re-qualify the dependency direction before continuing.

### Assumption Register

Each assumption is a testable planning input, not a fact to force onto the
implementation.

- [ ] **A1 - Current behavior is authoritative during relocation.** Validate by
  capturing the architecture qualification baseline, deterministic BDD paths,
  representative receipts, SQLite state, report artifacts, CLI output, and
  isolated wheel behavior before the first move. If the current outputs conflict
  with theory, classify the conflict separately as a behavior defect; do not
  silently encode it into a package boundary.

- [ ] **A2 - Theory-defined responsibility is the unit of ownership.** Validate
  each proposed package against a cohesive purpose, stable vocabulary, and a
  defensible public interface. If a proposed package is only a collection of
  files or helpers, keep the code with its actual owner rather than creating a
  project for it.

- [ ] **A3 - Pure and dependency-light semantic values can be separated from
  policy and orchestration.** Validate the import closure of theory terms,
  artifact contracts, boundary values, and normalization primitives. If they
  require storage, model providers, controller state, or workstation types,
  split owner-specific values and adapters instead of creating a central grab
  bag.

- [ ] **A4 - Governance can be consumed through decisions and ports rather than
  controller implementation objects.** Validate admission, approval, authority,
  lifecycle, revocation, incident, and data-policy call sites. If governance
  needs a controller-owned object, introduce the smallest governance request or
  result type and translate at the caller; do not make governance depend upward.

- [ ] **A5 - Persistence is an adapter, not the owner of semantic policy.**
  Validate which SQLite operations merely store canonical records and which
  currently make admission, matching, or lifecycle decisions. If policy is
  embedded in persistence, first extract and characterize that policy with
  tests before moving either side.

- [ ] **A6 - Ability declaration, ability selection, realizer availability,
  authority, and execution remain separate mechanisms.** Validate the complete
  ability journey using admitted, held, inactive, rejected, revoked,
  near-similar, unavailable-realizer, and denied-authority cases. If any call
  path collapses these stages, repair the boundary under its own behavior change
  before relocating that path.

- [ ] **A7 - The shared host-interaction package remains a lower substrate, not
  a governance or workstation owner.** Validate that provider registration,
  attachment resolution, delegation narrowing, dispatch, and receipt shaping
  can be expressed without importing workstation sessions, controller
  reduction, skill admission, or LLM code. If not, keep the upper policy in its
  owner and add a narrow port rather than expanding the substrate.

- [ ] **A8 - The subject lifecycle is one cohesive domain with internal
  stages.** Validate that learning context, Gather, Itemize, Decision Review,
  Review, and Publication share subject identity, provenance, and persistence
  invariants. If Publication or another stage has independent consumers and a
  genuinely separate lifecycle, use an internal package boundary first and
  graduate it to a UV project only after that independence is demonstrated.

- [ ] **A9 - Blend is a domain model below workstation presentation.** Validate
  that context, operator, session, world, workflow, history, and coordination
  can be represented without importing workstation UI, shell, or session
  implementation types. If workstation-specific state is intrinsic rather than
  adapted, define the missing Blend contract before extracting implementation.

- [ ] **A10 - The controller can become source-native after lower concerns are
  extracted.** Validate the remaining `core_engine/module_manifest.txt` closure
  after semantic contracts, governance, and runtime realization have owners. If
  the closure still mixes unrelated domains, continue extracting those domains
  rather than moving the mixed graph wholesale under `realized_core_engine`.

- [ ] **A11 - Existing import identities are compatibility obligations until
  proven otherwise.** Validate public documentation, tests, trials, downstream
  packages, and serialized qualified names. If a path is demonstrably private,
  record that evidence before removing it; otherwise preserve identity through
  a facade.

- [ ] **A12 - UV workspace membership is not sufficient evidence of a
  boundary.** Validate every project with isolated wheel/sdist tests and without
  the repository root on `sys.path`. If an isolated project imports root code,
  it remains transitional even when the architecture graph is acyclic.

- [ ] **A13 - The root project remains a development and composition
  workspace.** Validate that supported user execution goes through packaged
  application entrypoints. If a supported integration still requires direct
  root imports, preserve the needed facade while migrating that integration to
  an explicit package API.

- [ ] **A14 - LLM output is advisory and cannot own causal identity,
  governance, commitment, or realizer dispatch.** Validate all extracted
  interfaces with LLM-off tests. If an interface requires model output to
  establish a mechanical fact, correct the responsibility before packaging it.

- [ ] **A15 - No persisted-format migration is necessary for source
  modularization.** Validate SQLite schemas, artifact encodings, skill YAML,
  run bundles, subject corpus files, report plans, receipts, and resumption
  records. If a format embeds Python module paths or concrete class names, add
  a separately tested compatibility decoder before moving the source.

- [ ] **A16 - Performance may not regress materially merely because a boundary
  moved.** Capture representative reduction, retrieval, row-selection,
  publication, and workstation-flow timings. If adapters introduce material
  overhead, profile the boundary and revise the API rather than hiding the
  regression with caching that changes semantics.

- [ ] **A17 - Portable skill semantics form a domain distinct from governance
  and execution.** Validate that declarations, canonical IR, boundary normal
  form, invocation contracts, and composition structures can be represented
  without admitting a skill, granting authority, selecting a realizer, or
  executing an effect. If that separation does not hold for a type, assign the
  type to governance or runtime and translate at the skill-domain boundary.

- [ ] **A18 - The LLM layer can remain advisory and provider-isolated.** Validate
  provider-neutral planning/rendering contracts, controller prompt assembly,
  workstation model adapters, and the historical supplement path. If provider
  state or prompt state currently carries causal application state, first
  replace that reliance with explicit persisted state and bounded projections.

- [ ] **A19 - Events and receipts describe accepted transitions but are not the
  authoritative domain state.** Validate event publication, replay, Blend
  observations, workstation activity, and governance receipts. If a consumer
  reconstructs truth solely from lossy presentation events, define the missing
  state/query contract before relocating the event code.

### Phase 0 - Establish The Accepted Baseline

- [x] Run the architecture checker without updating its baseline and require a
  clean result.
- [x] Run the declared deterministic qualification ladder and archive the
  machine-readable result.
- [x] Run provider-backed and browser qualifications that are required for the
  boundary being changed; do not require unrelated manual gates.
- [ ] Capture representative SQLite databases for reduction, learned
  artifacts, governed skills, subject workflow, Blend workflow, and resumption.
- [ ] Capture representative run bundles, governance receipts, event order,
  report plans, publication outputs, and rendered UI evidence.
- [ ] Record public import identities and package exports for every module that
  may move.
- [ ] Record wheel contents and isolated-install behavior for every current UV
  project.
- [ ] Record performance distributions with at least three runs for
  performance-sensitive paths.
- [ ] Confirm that all baseline artifacts are reproducible and contain no
  machine-local paths or credentials.

Exit condition:

- [ ] A future slice can prove equivalence against durable evidence rather than
  against memory or a passing aggregate test count.

### Phase 1 - Make Ownership Explicit Before Moving Code

- [x] Classify every canonical root module and top-level Python package family
  under exactly one responsibility:
  semantic model, governance, runtime/skill execution, controller, LLM,
  workstation subject domain, Blend, entry/exchange, persistence adapter,
  compatibility, or validation/trial.
- [x] Reject ambiguous ownership rather than assigning it from the filename.
- [x] For each ambiguous module, identify the reasons for change represented by
  its functions and types; split only when more than one independent reason is
  demonstrated by callers and tests.
- [x] Extend the architecture manifest with a target owner for each canonical
  root module and top-level package family, and a separate status for
  entrypoints, validations, and compatibility facades.
- [x] Define the target dependency direction for every proposed owner before
  creating a project.
- [x] Define each owner's public API, private implementation surface, and
  persistence ports.
- [x] Add a CI check that rejects unowned root modules or top-level package
  families and ratchets every dependency direction among root modules,
  top-level package families, and UV workspace packages.
- [x] Keep existing package-to-root observations as a shrinking baseline; do
  not normalize them as the desired architecture.
- [x] Add a check that a root compatibility facade may import its canonical
  package, but canonical package code may never import the facade.

Exit condition:

- [x] Every implementation module has a justified target owner, and the target
  graph is acyclic before source movement begins.

#### Phase 1 Ownership Decisions

The machine-readable ownership and target-direction ledgers live in
`architecture/boundaries.toml`; their deterministic rendering lives in
`architecture/DEPENDENCY_REPORT.md`. The target graph is acyclic. Existing
cross-owner imports remain measured violations and are not permissions.

The ownership inventory includes the top-level package families that are not
yet UV projects: `coordinated_transformation` and `dst` belong to the subject
domain, while `design` is a validation/trial package. Their imports participate
in the same combined-cycle and shrinking-edge ratchets as root modules and UV
workspace components.

| Responsibility | Public API obligation | Private implementation | Persistence ports |
| --- | --- | --- | --- |
| Semantic model | Immutable theory terms, artifact read contracts, stable identifiers, semantic text/title operations, and dependency-light normalization | Parsing shortcuts and owner-local reconstruction helpers | None; semantic values are persistence-neutral |
| Portable skills | Ability declarations, canonical skill IR, boundary regions, composition plans, and portable invocation values | Compiler parsing, compatibility shaping, and mapper internals | Registry projection ports only; admission and execution remain outside this owner |
| Governance | Admission, approval, lifecycle, authority, current-use, revocation, incident, replay, and data-policy requests/results | Policy matching and decision derivation | Governance repository protocols for approvals, lifecycle, incidents, and admitted declarations |
| Runtime/skill execution | Realizer descriptors, host ABI, invocation/effect requests and results, mediation, and execution receipts | Executor implementations, broker adapters, child runtimes, and platform realizers | Runtime-state, trace, and receipt sinks defined as ports rather than SQLite calls |
| Controller | Typed run, resume, reduction, inspection, closure, and outcome surfaces | Recursive reduction, retrieval/ranking, decomposition, and commitment orchestration | Artifact/state repositories plus governance, runtime, and LLM ports |
| LLM | Provider-neutral planning/rendering requests, advisory outputs, and provider protocol | Prompt construction, schema adaptation, retries, and provider adapters | No causal domain persistence; conversation caching cannot establish application truth |
| Subject domain | Subject identity/context, Gather, Itemize, Decision Review, Review, Publication actions, views, and workflow client contract | Stage orchestration, projection, validation, and rendering internals | Subject context, source, review, report-plan, and publication repository protocols |
| Blend | Context, operator, session, world, workflow, query, and observation contracts | Applicability resolution, provider adaptation, workflow execution, and projections | Operator catalog, world, workflow, run-history, and observation ports |
| Entry/exchange | CLI commands, run-bundle and skill-bundle schemas, import/export, and launch surfaces | Argument dispatch, compatibility encoding, and composition wiring | No domain-owned store; entry composition supplies concrete adapters |
| Persistence adapter | Constructors and adapters implementing owner-defined repository protocols | SQLite schema/queries, indexing, migration, and transaction details | This responsibility realizes ports; it does not define domain policy |
| Compatibility | Historical import names and documented object identities only | No new behavior; each file is a one-way facade | None |
| Validation/trial | Explicit validator inputs, machine-readable outcomes, and trial entrypoints | Fixtures, probes, report assembly, and temporary-runtime setup | Disposable validation stores and report sinks only |

Ambiguous modules are treated explicitly:

- `normalize.py` is a multi-owner compatibility facade. It cannot become a
  canonical package and may disappear only after consumers use owner APIs.
- `main.py` is both an executable entrypoint and an import-identity facade. Its
  status is orthogonal to its entry/exchange ownership.
- `side.py` and `side_runtime_dependencies.py` are entry/exchange bridge code,
  not general compatibility ownership; their artifact hydration and store
  dependencies must be replaced with owner contracts before movement.
- `runtime_controller_api.py` and `controller_runtime_binding.py` are
  composition seams. They remain entry/exchange until the injected controller
  contract fully replaces concrete bootstrap reach-through.
- `runtime_governance_context.py` is governance-facing resolution, not runtime
  execution merely because its caller is runtime code.
- `applied_theory_types.py` is semantic ownership with an execution-framework
  normalization leak. Move the value contract only after that normalization is
  translated at the runtime boundary.
- `artifact.py` is semantic serialization with fallback-generation and
  compatibility-normalization leaks. Separate structural serialization from
  controller fallback behavior before relocation.
- `semantic_text.py` now owns the learning-token constants that were formerly
  imported upward from controller learning code. Its remaining migration risk
  is its broad consumer set and dependency on title semantics, not a controller
  import.
- `skill_invocation_contract.py` is a compatibility facade for portable skill
  invocation values; its status does not make the invocation contract part of
  compatibility ownership.
- Root `host_interaction_*.py` files are runtime/host-substrate compatibility
  facades over the existing package and may not be imported by package code.
- `coordinated_transformation` and `dst` are cohesive subject-domain package
  families with standalone project metadata, but they are not UV workspace
  members or architecture components. `dst` is not self-contained because it
  imports undeclared repository-root modules. Preserve their current import ABI
  until the subject-domain extraction can move them with their consumers and
  complete dependency declarations.
- `design` is a standalone project-shaped validation/trial package rather than
  production application ownership. Do not promote it into the operational
  dependency graph merely because it already has packaging metadata.

### Phase 2 - Establish The Dependency-Light Semantic Contract Surface

This phase is conditional on A3. It may result in a dependency-free contract
project, owner-local types plus adapters, or a smaller extension of an existing
contract package. The decision must follow the measured closure.

- [ ] Inventory the consumers of pure theory terms, applied theory primitives,
  artifact contracts, boundary shapes, identifiers, and JSON-safe value
  projection.
- [ ] Separate immutable semantic values and structural protocols from policy,
  persistence, model calls, and orchestration.
- [ ] Decide whether the resulting closure is cohesive enough for one shared
  core semantic-contract project.
- [ ] If a shared project is justified, give it no dependency on controller,
  governance implementation, runtime, LLM, workstation, or storage.
- [ ] If a shared project is not justified, assign each value to its true owner
  and define explicit adapter types at boundaries.
- [ ] Preserve enum values, dataclass field names, defaults, serialization
  order, stable identifiers, and structural protocol behavior.
- [ ] Add serialization golden tests and old-path/new-path object-identity tests.
- [ ] Move the lowest-level consumers first and replace old root modules with
  facades only after their dependency closures are clean.
- [ ] Prohibit this surface from becoming a miscellaneous `common` or `utils`
  package.

#### Phase 2 Cut 1 - Formal Semantic Contracts

- [x] Measure the candidate closure before selecting a destination.
- [x] Confirm that `pure_theory_types.py` is the formal Pydantic theory model
  and has one canonical production consumer, `applied_theory_primitives.py`.
- [x] Confirm that `artifact_contracts.py` contains only two runtime-checkable,
  read-only structural protocols consumed by three governance modules.
- [x] Reject moving `semantic_text.py` in this cut because it has more than one
  hundred production consumers across multiple owners.
- [x] Defer `applied_theory_primitives.py` because it combines applied semantic
  enums with timestamp, JSON projection, execution dependency constants, and a
  compatibility fallback; moving it wholesale would prematurely bless a mixed
  public surface.
- [x] Select one cohesive `realized-core-semantics` project for formal theory
  values and semantic read contracts; this is a shared substrate, not a seventh
  behavioral layer and not one project per source file.
- [x] Add the independently buildable project with explicit Pydantic dependency,
  typed package marker, narrow module-level APIs, and no repository-root import.
- [x] Move the canonical formal model and artifact protocols into that package.
- [x] Replace `pure_theory_types.py` and `artifact_contracts.py` with one-way,
  identity-preserving compatibility facades.
- [x] Migrate `applied_theory_primitives.py`, `approval_governance.py`,
  `skill_lifecycle.py`, and `skill_safety_governance.py` to canonical package
  imports.
- [x] Keep both historical facades in the engine distribution for at least one
  complete qualification cycle.
- [x] Add package API, serialization, identity, import-hygiene, wheel-content,
  sdist, and isolated-install tests.
- [x] Add the package to the workspace, architecture manifest, engine dependency
  metadata, core distribution verifier, and Google Cloud Build wheel gate in the
  same cut.
- [x] Require the architecture ratchet, focused semantic/governance tests, core
  distribution tests, complete deterministic qualification ladder, and isolated
  wheel smoke test to pass before selecting Cut 2.

Cut 1 qualification evidence:

- [x] The architecture ratchet passes with 26 components, 126 owned root
  modules, three owned root package families, no cyclic nodes, and no cyclic
  internal edges.
- [x] The root suite passes 751 tests with no failures or errors.
- [x] The workstation suite passes 603 tests with one expected skip; its
  1,165-second duration is within the accepted tolerance of the 1,148-second
  pre-move run.
- [x] Skill-routing, publication, and incremental-publication BDD gates pass
  three, 34, and one scenarios respectively.
- [x] The regenerated publication reference files are byte-for-byte identical
  to the accepted artifacts.
- [x] Flutter static analysis and widget tests pass.
- [x] The semantic wheel, semantic source distribution, rebuilt engine wheel,
  compatibility identities, and isolated LLM-off SQLite smoke test pass the
  core distribution verifier.
- [x] The assembled qualification baseline records all 15 declared gates as
  passing, with manual-gate evidence retained from its original qualified run.

Cut 1 assumption findings:

- [x] Testing disproved the assumption that a source-run UV child automatically
  sees newly extracted workspace packages. The Python child launcher now adds
  only the discovered import roots required by its declared host-bridge package
  dependencies; it does not expose every workspace project.
- [ ] Package the root-hosted `python_skill_host` bridge under its runtime owner
  and add an isolated installed-wheel broker invocation test in Phase 6. The
  bridge was already absent from the engine distribution before Cut 1, so that
  pre-existing ownership gap is recorded rather than hidden inside the semantic
  extraction.

#### Phase 2 Cut 2 - Semantic Value Projection

Measured scope and assumptions:

- [x] Confirm that `applied_theory_types.py` is not a cohesive extraction unit:
  its dependency-light source still combines controller graph state, runtime
  execution results, governance records, LLM supplements, feature toggles, and
  artifact records.
- [x] Confirm that packaged consumers use only three narrow surfaces from that
  module: `Artifact`, `RuntimeDeterminismPolicy`/`NodeStatus`, and `json_safe`.
- [x] Select only `json_safe` and `utc_now` for this cut because they are pure
  semantic value-projection primitives with standard-library dependencies and
  no policy, storage, model, runtime, or workstation behavior.
- [x] Defer `Artifact` until its normalization and controller-feature coupling
  is separated; defer `RuntimeDeterminismPolicy` and `NodeStatus` to the
  controller source-native phase.
- [x] Correct a falsified isolation assumption discovered by the consumer
  tests: importing the independent `values` submodule still executed the
  eager package initializer, imported `theory`, and required Pydantic inside
  the minimal Python skill-host child. Keep the explicit package API while
  loading its public submodules lazily, and guard the isolation in a fresh
  subprocess.
- [x] Add an explicit `realized_core_semantics.values` API containing
  `json_safe` and `utc_now`.
- [x] Make `applied_theory_primitives.py` re-export the canonical function
  objects so historical imports and all downstream identities remain stable.
- [x] Migrate the `runtime_core` and `skills_core` package consumers from
  `applied_theory_types.json_safe` to the canonical semantic API.
- [x] Declare `realized-core-semantics` in both consumer projects and allow the
  corresponding architecture edges.
- [x] Add projection, timestamp-shape, old-path/new-path identity, package API,
  wheel-content, and isolated-install tests.
- [x] Refresh the lockfile, architecture baseline, dependency report, core
  distribution verifier, and Google Cloud Build inputs only where the measured
  package surface changes.
- [x] Run the focused semantic and compatibility tests, architecture ratchet,
  root suite, affected workstation tests, isolated distribution smoke, and
  applicable BDD gates before accepting the cut.

Cut 2 qualification evidence:

- [x] The focused semantic API, distribution, compatibility-facade, package
  metadata, and architecture suites pass 74 tests.
- [x] The four isolated Python-skill scenarios that exposed the eager package
  import pass after the lazy public-module repair.
- [x] The architecture ratchet passes with 26 components, 126 owned root
  modules, 3 owned root package families, 70 package edges, 594 grandfathered
  observations, and no cycle or undeclared dependency.
- [x] The root suite passes 752 tests in 539.6 seconds and the workstation
  suite passes 603 tests with one expected skip in 1246.8 seconds; both remain
  within the accepted performance tolerance.
- [x] Skill-routing, publication, and incremental-publication BDD gates pass
  3, 34, and 1 tests respectively.
- [x] The regenerated publication reference retains the accepted hashes for
  `reference.json`, `report.md`, and `report.typ`.
- [x] Flutter static analysis reports no issues and all 51 widget tests pass.
- [x] Fresh semantic wheel and source-distribution builds contain `values.py`;
  isolated verification reports 10 wheel entries and 22 sdist entries,
  preserves old/new object identity, and passes the LLM-off SQLite smoke.
- [x] The assembled qualification record contains 15 passing gates with no
  failed, blocked, or omitted gate.

Exit condition:

- [x] No UV workspace package imports `applied_theory_types` merely to project a
  value into JSON-compatible data.

Exit condition:

- [ ] Packages no longer import root modules merely to share semantic values or
  normalization primitives.

### Phase 3 - Give Portable Skill Semantics A Canonical Owner

This phase is conditional on A17. It may establish a core skill-domain project
or a package-owned internal domain consumed by governance, runtime, and
workstation adapters. It must not make workstation the owner of portable skill
meaning.

- [ ] Inventory skill declarations, schema values, canonical IR, leaf types,
  boundary normalization, path notation, invocation request/result types,
  composition plans, compiler outputs, lifecycle policy, compatibility
  adapters, registry behavior, and execution helpers.
- [ ] Separate portable skill meaning from admission, authority, lifecycle
  policy, realizer registration, execution, persistence, and UI management.
- [ ] Define the canonical skill-domain API for declarations, IR, boundary
  normal form, invocation contracts, and composition structures.
- [ ] Keep admission, approval, risk, revocation, and current-use decisions in
  governance.
- [ ] Keep exact executor/broker binding and effect execution in runtime.
- [ ] Keep YAML and foreign-format parsing/rendering in entry/exchange adapters.
- [ ] Keep workstation discovery, catalog presentation, session selection, and
  approval UX in workstation packages.
- [ ] Move dependency-light leaf types, path notation, boundary normalization,
  and IR projection first.
- [ ] Move composition semantics only after distinguishing a declarative plan
  from runtime orchestration and effects.
- [ ] Move compiler behavior only after its output is a portable domain value
  rather than an admitted or installed runtime object.
- [ ] Preserve portable YAML fields, schema versions, stable identifiers,
  foreign compatibility projections, and invocation result semantics.
- [ ] Preserve historical root skill imports as compatibility facades while
  core and workstation consumers migrate.
- [ ] Add round-trip, normalization, composition, permission aggregation,
  compatibility import/export, and object-identity tests.

Exit condition:

- [ ] Portable skill meaning has one canonical owner, while governance and
  runtime consume it without taking ownership of its representation.

#### Phase 3 Cut 1 - Canonical Leaf And Path Substrate

Measured scope and falsifiable assumptions:

- [x] Confirm from Theory section 4.6 and the skill theory documents that a
  region-preserving typed leaf ledger and its canonical path language are one
  cohesive portable semantic responsibility, not governance, persistence,
  execution, planning, or workstation behavior.
- [x] Confirm that `skill_leaf_types.py` and `skill_path_notation.py` form a
  dependency closure over only standard-library values and the canonical
  boundary/value contracts in `realized-core-semantics`.
- [x] Confirm that moving `skill_ir.py` in the same cut would be unsound: its
  current implementation imports executor resolution, compatibility import,
  governance declaration synthesis, and lifecycle state.
- [x] Confirm that moving `skill_boundary_normalization.py` in the same cut
  would also be unsound until its governance-dependent declaration synthesis
  is replaced by an explicit input contract.
- [x] Use one `realized-skill-semantics` UV project for the portable skill
  domain, with `leaves` and `paths` as modules of that domain; do not create a
  project per source file.
- [x] Preserve `BoundaryShapeTerm` object identity by importing the canonical
  theory enum under its historical applied alias rather than introducing a
  second region type.
- [x] Assume no persisted-format migration is needed because these values are
  serialized through explicit dictionaries; validate this through golden
  round-trip tests and historical pickle-global resolution.
- [x] Create the independently buildable project with an explicit dependency
  only on `realized-core-semantics`, a narrow package API, typing marker,
  package metadata, and no upper-layer imports.
- [x] Move canonical leaf types, region normalization, carrier derivation,
  canonical path escaping, rendering, and parsing into the project.
- [x] Replace both historical root modules with one-way identity-preserving
  compatibility facades retained in the engine wheel.
- [x] Migrate canonical production consumers in boundary normalization,
  composition, and workstation skill planning to the package API; keep tests
  on both canonical and compatibility paths where they prove ABI continuity.
- [x] Register the project in the UV workspace and architecture manifest;
  declare it in every distribution that directly imports it or ships a retained
  facade whose implementation requires it.
- [x] Add API, invariant, round-trip, malformed-path, identity, pickle-global,
  import-hygiene, wheel/sdist-content, and isolated-install tests.
- [x] Extend Google Cloud Build and the isolated distribution verifier so the
  skill-semantic package is built and exercised as an independent artifact.
- [x] Accept only the measured graph delta: a lower `skill_semantics ->
  core_semantics` edge, consumer edges to `skill_semantics`, removal of the
  corresponding package-to-root observations, and no cycle or undeclared edge.
- [x] Run focused package and compatibility tests, the architecture ratchet,
  the complete root and workstation suites, skill-routing and publication BDDs,
  distribution smoke, and relevant Flutter gates before accepting the cut.

Cut exit condition:

- [x] No canonical production consumer imports `skill_leaf_types` or
  `skill_path_notation`; historical imports remain facades only.

Cut 1 qualification evidence:

- [x] Focused package, compatibility, normalization, composition, distribution,
  metadata, and boundary suites pass, including all 368 deterministic Cloud
  Build architecture/boundary tests.
- [x] Historical imports and protocol-zero pickle globals resolve to the exact
  canonical objects in `realized_skill_semantics`; fresh wheel extraction
  verifies the same identities without the repository on `sys.path`.
- [x] The architecture ratchet passes with 27 components, 126 owned root
  modules, three owned root package families, 72 package edges, 589
  grandfathered observations, and no cycle or undeclared dependency.
- [x] The accepted graph delta contains only `skill_semantics ->
  core_semantics`, `skills_planning -> skill_semantics`, four expected
  root-to-canonical imports, two compatibility statuses, removal of the two
  workstation-to-root imports, and removal of seven root-to-root imports.
- [x] The root suite passes 755 tests in 485.6 seconds. The workstation suite
  passes 603 tests with one expected skip in 1211.7 seconds. Both remain within
  the accepted performance tolerance.
- [x] Skill-routing, publication, and incremental-publication BDD gates pass;
  publication reference hashes remain unchanged; Flutter analysis and all 51
  widget tests pass.
- [x] Fresh skill-semantic wheel and source-distribution builds contain only
  the intended package surface. The isolated verifier reports nine wheel
  entries and 21 sdist entries and passes the LLM-off SQLite smoke test.
- [x] The assembled qualification record contains 15 passing gates with no
  failed, blocked, omitted, or not-run gate.

Cut 1 assumption findings:

- [x] Testing reconfirmed that the isolated Python skill child does not inherit
  newly extracted workspace projects from engine metadata. Extend its existing
  explicit dependency-root discovery with `realized_skill_semantics`; do not
  expose the workspace generally. Brokerized child tests pass with the narrow
  root set.

#### Phase 3 Cut 2 - Explicit Boundary-Normalization Contract

Measured scope and falsifiable assumptions:

- [x] **A3.2.1:** Confirm that region flattening, reconstruction, normalization
  payload validation, and normalization-document synthesis depend only on
  explicit semantic values, canonical leaf/path types, and the standard
  library. If any of these operations requires admission, lifecycle, host, or
  persistence state, stop and revise the cut rather than importing an upper
  layer into `realized-skill-semantics`.
- [x] **A3.2.2:** Confirm that the existing root module is not one cohesive move:
  `synthesized_skill_normalization_for_artifact` extracts an artifact and asks
  governance to recover or synthesize a declaration. Keep that operation in a
  root adapter until governance and artifact projection have canonical package
  owners.
- [x] **A3.2.3:** Confirm that current behavior can be preserved by giving the
  portable synthesizer explicit `input_values` and `output_values`, while the
  adapter retains the exact precedence of explicit contracts, declaration
  contracts, and answer fallback. Golden equivalence tests must disprove this
  assumption before any consumer migration is accepted.
- [x] **A3.2.4:** Confirm that `collapse_ws` is used only to derive a leaf's
  semantic label. Keep equivalent private text cleanup inside the normalization
  module for this cut; do not pull the broad root `semantic_text` dependency or
  opportunistically reopen Phase 2.
- [x] Add a package-owned `normalization` module with an explicit public API for
  normalization versioning, flattening, reconstruction, payload validation,
  and synthesis from explicit boundary values. This task relies on A3.2.1 and
  must fail import-hygiene tests if an upper-layer dependency appears.
- [x] Keep `synthesized_skill_normalization_for_artifact` as a thin adapter that
  extracts current artifact fields, obtains the governance declaration, and
  calls the portable synthesizer. This task relies on A3.2.2 and A3.2.3; it may
  not duplicate flattening or serialized-shape logic.
- [x] Preserve old root imports of the portable functions as exact object
  aliases, while retaining the artifact adapter under its historical name.
  Add identity and legacy pickle-global resolution tests before migrating
  canonical consumers.
- [x] Migrate composition directly to the package normalization API. Migrate
  IR and entry/exchange modules directly for payload validation, but leave their
  artifact synthesis calls on the adapter until their own boundaries move.
- [x] Add package tests for all eight regions, nested mappings/lists, root
  scalar bodies, value/reference polarity, opaque leaves, malformed region
  payloads, reconstructibility, deterministic ordering, and exact synthesized
  document shape.
- [x] Add adapter-equivalence tests covering explicit contracts, declaration
  fallback, answer fallback, empty regions, and legacy artifact shapes. The
  expected output must be captured from the pre-cut implementation or expressed
  as an exact stable document, not inferred from the new implementation alone.
- [x] Extend package API, distribution-content, isolated-wheel, Cloud Build,
  and compatibility-facade checks for the normalization module.
- [x] Accept only a graph delta that removes root semantic/helper observations
  and redirects canonical consumers toward `skill_semantics`; reject any new
  edge from `skill_semantics` to governance, runtime, persistence, entry, or
  workstation layers.
- [x] Run focused normalization/schema/export/IR/composition tests, all
  deterministic architecture tests, the architecture ratchet, isolated
  distribution verification, then the complete qualification ladder before
  accepting the cut.

Cut exit condition:

- [x] Portable boundary normalization has one package owner; the historical
  root module contains only compatibility aliases and artifact/governance
  adaptation, and no canonical consumer uses it for portable operations.

Cut 2 qualification evidence:

- [x] Loaded the pre-cut implementation directly from `HEAD` and compared it
  with the package implementation across every boundary shape, empty and scalar
  roots, nested mappings and lists, imported normalization payloads, and all
  four artifact-contract precedence cases. Every result was equivalent.
- [x] Focused normalization, schema, IR, export, composition, compatibility, and
  distribution tests pass. The deterministic architecture and boundary suite
  passes 380 tests with `UV_OFFLINE=1`; the environment setting is required so
  nested UV test processes do not consult the network.
- [x] Fresh wheel and sdist verification passes from extracted distributions.
  The skill-semantics wheel contains 10 entries, the sdist contains 23 entries,
  the engine wheel contains 91 entries and 77 canonical modules, compatibility
  identities resolve from the wheels, and the isolated LLM-off SQLite smoke
  path passes.
- [x] The accepted combined graph has 27 package components, 126 owned root
  modules, 72 package edges, and 590 grandfathered observations, with no cycle
  or undeclared dependency. The measured cut adds
  `skill_export_projection -> skill_semantics`,
  `skill_ir -> skill_semantics`, and
  `skill_schema_io -> skill_semantics`; removes
  `skill_boundary_normalization -> semantic_text` and
  `skill_composition -> skill_boundary_normalization`; and introduces no edge
  from `skill_semantics` to an upper layer.
- [x] The canonical qualification capture reran the default gates, including
  761 root tests and 603 workstation tests, and retained the already-passing
  manual/provider/browser evidence. The assembled record contains all 15 gates
  passing with no failed, blocked, omitted, or not-run gate.

Cut 2 assumption findings:

- [x] A3.2.1 and A3.2.4 held: portable normalization closes over the standard
  library plus package-owned leaf/path semantics, and the broad root text helper
  is no longer an observed dependency.
- [x] A3.2.2 held: governance declaration recovery remains an artifact adapter
  responsibility, while all serialized normalization shape logic has one package
  owner.
- [x] A3.2.3 held under differential and exact-document tests: explicit
  contracts, declaration contracts, answer fallback, and legacy empty defaults
  retain their pre-cut precedence and output.

#### Phase 3 Cut 3 - Portable Skill IR Value And Identity Metadata

Measured scope and falsifiable assumptions:

- [x] **A3.3.1:** Confirm that `CanonicalSkillIR` is a portable semantic value:
  its fields contain only JSON-projectable declaration, lifecycle, runtime
  reference, normalization, alias, family, compatibility, and hosting values,
  while construction from an `Artifact` is a separate adapter concern. If the
  value itself requires a store, governance query, executor lookup, or artifact
  method, stop and revise the cut.
- [x] **A3.3.2:** Confirm that explicit alias normalization and conservative
  family metadata derivation are part of portable skill identity rather than
  schema ingress policy. Their dependency closure must remain the standard
  library plus package-owned value projection; malformed or incomplete values
  must retain current normalization behavior exactly.
- [x] **A3.3.3:** Confirm that artifact-to-IR projection cannot move in this cut.
  It currently combines declaration synthesis, lifecycle projection, executor
  framework detection, compatibility import, boundary-normalization fallback,
  and artifact hosting fields. Keep these operations in the historical root
  adapter until each upper-layer input is supplied through an explicit contract.
- [x] **A3.3.4:** Confirm that historical imports and protocol-zero pickle
  globals can resolve the package-owned `CanonicalSkillIR` through exact root
  aliases. If repository evidence shows that newly serialized objects must keep
  `skill_ir` as their emitted module name, stop and design a serialization
  adapter instead of changing object identity.
- [x] Add a package-owned `ir` module whose public API contains the immutable
  canonical IR value and the alias/family identity normalization functions.
  Keep text cleanup private and behaviorally equivalent; do not import the root
  text or normalization modules merely for two dependency-light operations.
- [x] Reduce root `skill_ir.py` to exact aliases for portable IR symbols plus the
  artifact projection adapter, runtime-package projection, hosting projection,
  and artifact convenience functions. Do not duplicate the portable dataclass
  or identity algorithms.
- [x] Migrate schema ingress directly to package alias/family normalization and
  composition directly to the package IR value. Consumers that start from an
  artifact must continue through the root projection adapter in this cut.
- [x] Add package tests for all IR fields, JSON-safe projection, explicit and
  title-derived aliases, deduplication, numbered and unnumbered family titles,
  explicit family precedence, whitespace/control-character normalization,
  malformed metadata, and stable dictionary shape.
- [x] Add differential tests against the pre-cut root implementation and exact
  artifact-projection golden tests. Add root/package identity checks and legacy
  pickle-global resolution before accepting any consumer migration.
- [x] Extend package API, import-hygiene, wheel/sdist-content, isolated-wheel,
  Cloud Build, and compatibility checks for the IR module.
- [x] Accept only a graph delta that redirects portable IR consumers toward
  `skill_semantics`, removes their root `skill_ir` observations where no artifact
  adapter is needed, and introduces no package dependency on governance,
  lifecycle, execution, persistence, entry/exchange, or workstation layers.
- [x] Run focused IR/schema/export/composition/compiler/registry tests, all
  deterministic architecture tests, the architecture ratchet, isolated
  distribution verification, and the complete qualification ladder before
  accepting the cut.

Cut exit condition:

- [x] The canonical IR value and skill identity normalization have one package
  owner; the historical root module retains only exact aliases and
  artifact/runtime/governance adaptation, and no canonical consumer imports it
  merely for a portable value or identity helper.

Cut 3 qualification evidence:

- [x] Loaded the pre-cut `skill_ir.py` directly from `HEAD` and compared it with
  the package implementation across four alias cases, five family cases, one
  canonical-value serialization case, and two complete artifact projections.
  Every result was equivalent. A separate literal golden document covers the
  artifact adapter's declaration, normalization, compatibility, runtime,
  authority, and hosting projections.
- [x] The focused IR, normalization, compatibility, and facade suite passes 77
  tests. The broader schema, registry-facing I/O, import/export, composition,
  compiler, release-export, and learning-context slice passes 93 tests. The
  deterministic Cloud Build architecture/package suite passes 386 tests with
  `UV_OFFLINE=1`.
- [x] Fresh wheels and source distributions pass isolated verification. The
  skill-semantics wheel contains 11 entries, its sdist contains 25 entries, the
  engine wheel contains 91 entries and 77 canonical modules, the extracted
  historical and package IR imports resolve to identical objects, and the
  isolated LLM-off SQLite smoke path passes.
- [x] The accepted graph retains 27 package components, 126 owned root modules,
  and 72 package edges while reducing grandfathered observations from 590 to
  588. The only measured removals are
  `skill_schema_io -> skill_ir` and
  `skill_ir -> normalization_primitives`; no node, package edge, ownership,
  cycle, undeclared dependency, or policy violation was added.
- [x] The canonical qualification capture reran the default gates with required
  host access for provider, local-socket, and Flutter SDK operations. It passed
  764 root tests and 603 workstation tests and retained the already-passing
  provider, browser, screenshot, and trial evidence. The assembled record has
  all 15 gates passing with no failed, blocked, omitted, or not-run gate.

Cut 3 assumption findings:

- [x] A3.3.1 held: the package-owned IR value closes over JSON-projectable data
  and `realized-core-semantics` value projection only; artifact construction and
  all upper-layer lookups remain outside the package.
- [x] A3.3.2 held under edge-case and differential tests: alias ordering,
  deduplication, title variants, control-character cleanup, explicit family
  precedence, conservative title derivation, and malformed inputs preserve
  their pre-cut behavior.
- [x] A3.3.3 held: artifact-to-IR projection still depends on governance,
  lifecycle, executor, compatibility, and normalization adapters, so it remains
  in the historical root module rather than contaminating the portable package.
- [x] A3.3.4 held: root exports are exact package-object aliases, protocol-zero
  lookup of `skill_ir.CanonicalSkillIR` resolves to the package class, and no
  persisted-object evidence required newly emitted values to retain the old
  module name.

#### Phase 3 Cut 4 - Portable Skill Invocation Records

Measured scope and falsifiable assumptions:

- [x] **A3.4.1:** Confirm that `SkillInvocationBinding`,
  `SkillInvocationRequest`, and `SkillInvocationResult` are portable semantic
  values whose fields contain only JSON-projectable declaration, binding,
  request, and terminal-result data. If construction or serialization of the
  values requires an artifact, store, governance query, executor registry,
  workstation session, or host realizer, stop and revise the cut rather than
  importing an upper layer into `realized-skill-semantics`.
- [x] **A3.4.2:** Confirm that required-input derivation and terminal-result
  mapping are deterministic contract normalization rather than workstation
  policy. Preserve the exact current rules: an input is required when its
  normalized description is empty or contains `required` case-insensitively,
  and output payload precedence is `result_payload`, then `parsed_output`, then
  `result`, with fallback occurring only when the preceding value is `None`.
- [x] **A3.4.3:** Confirm that `skill_invocation_request_from_artifact` cannot
  move in this cut because it recovers a runtime declaration, detects an
  executor framework, projects artifact kind, and reads artifact fields. Keep
  that function in `workstation.skills.core` as an adapter over the portable
  values and normalization helpers.
- [x] **A3.4.4:** Confirm that invocation records are persisted and transported
  through explicit dictionaries rather than class-qualified object payloads.
  Historical root imports and protocol-zero pickle globals must still resolve
  to the exact package-owned classes; if newly emitted objects must retain the
  old module name, stop and introduce an explicit serialization adapter.
- [x] **A3.4.5:** Freeze the existing request and result field sets for this
  relocation. The richer invocation model described by skill theory, including
  canonical boundary ledgers, delegated capability requests, attachments, and
  receipt correlation identifiers, is a later additive contract change and
  must not be mixed with this ownership cut.
- [x] Capture pre-cut behavior from the current implementation for required
  input detection, request serialization, result serialization, text cleanup,
  `None`-only output fallback, and legacy object identities before editing the
  implementation.
- [x] Add a package-owned `invocation` module containing the three immutable
  value records, required-input derivation, and result-mapping normalization.
  Its dependency closure must remain the standard library plus
  `realized-core-semantics`; text cleanup must be private and behaviorally
  equivalent to the existing helper.
- [x] Reduce `workstation.skills.core.invocation_contract` to exact aliases for
  portable symbols plus the artifact-to-request projection adapter. Preserve
  the historical private required-input alias while canonical production code
  calls the package API directly.
- [x] Reduce root `skill_invocation_contract.py` to a compatibility facade that
  aliases package-owned values and normalization directly and re-exports the
  workstation artifact adapter without duplicating either responsibility.
- [x] Declare the direct `skills_core -> skill_semantics` distribution and
  architecture dependency. Do not permit the reverse edge or any new package
  dependency from skill semantics to workstation, runtime, governance,
  persistence, host interaction, or execution layers.
- [x] Add package tests for immutable value construction, exact JSON-safe
  shapes, control-character and whitespace normalization, required/optional
  input classification, empty names, mixed mapping values, output precedence,
  falsey non-`None` payloads, and complete terminal-result projection.
- [x] Add adapter-equivalence tests against the captured pre-cut behavior,
  package/workstation/root object-identity tests, and historical pickle-global
  resolution tests. Runtime and receipt contract tests must continue proving
  that explicit dictionaries cross persistence and host boundaries.
- [x] Extend package API, import-hygiene, wheel/sdist-content, isolated-wheel,
  Cloud Build, public package documentation, and compatibility-facade checks
  for the invocation module.
- [x] Measure the dependency graph before updating its baseline. Accept only
  the new declared `skills_core -> skill_semantics` edge plus removal or
  redirection of portable invocation dependencies; reject cycles, undeclared
  edges, upper-layer imports, or expansion of unrelated grandfathered debt.
- [x] Run focused invocation, workstation skill execution, host receipt,
  compatibility, package, and distribution tests; then run all deterministic
  architecture tests, the architecture ratchet, isolated distribution
  verification, and the complete qualification ladder before accepting the
  cut.

Cut exit condition:

- [x] Portable invocation values and deterministic mapping normalization have
  one package owner; artifact projection remains an explicit workstation
  adapter; historical imports preserve identity; and invocation behavior and
  serialized dictionary shapes are unchanged.

Cut 4 qualification evidence:

- [x] Loaded the pre-cut workstation implementation directly from `HEAD` and
  compared it with the package implementation across three required-input
  cases, five terminal-result cases, one request-value serialization case, and
  two complete artifact projections. Every result was equivalent, including
  falsey non-`None` payload precedence and text normalization.
- [x] Focused invocation, identity, compatibility, package, and distribution
  suites pass 71 tests. The runtime-facing host receipt and direct, derived,
  installed, approved, projected, and nested-error skill execution slice passes
  10 tests. The deterministic Cloud Build architecture/package suite passes 392
  tests.
- [x] Fresh wheel and source-distribution verification passes in an isolated
  environment. The skill-semantics wheel contains 12 entries, its sdist
  contains 27 entries, the engine wheel contains 91 entries and 77 canonical
  modules, historical imports resolve to package-owned invocation objects, and
  the isolated LLM-off SQLite smoke path passes.
- [x] The accepted dependency graph has 27 components, 126 owned root modules,
  three owned root package families, 72 package edges, and 589 grandfathered
  observations, with no cycle or undeclared dependency. The cut adds only the
  declared `skills_core -> skill_semantics` edge, removes the temporary direct
  `skills_core -> core_semantics` edge, and redirects the root compatibility
  facade to the package owner while retaining the workstation artifact adapter.
- [x] The canonical qualification capture reran every default gate, including
  765 root tests and 603 workstation tests, and retained current passing
  provider, browser, screenshot, and trial evidence. All 15 gates pass with no
  failed, blocked, omitted, or not-run gate; skill-routing, publication, and
  incremental-publication BDDs, publication artifacts, Flutter analysis, and
  all 51 Flutter widget tests are green.

Cut 4 assumption findings:

- [x] A3.4.1 held: the three records close over JSON-projectable values and
  `realized-core-semantics` value projection only; no artifact, store,
  governance, executor, workstation, or host dependency entered the package.
- [x] A3.4.2 held under differential and edge-case tests: required-input
  classification, text cleanup, output precedence, and `None`-only fallback are
  deterministic normalization and preserve their pre-cut behavior exactly.
- [x] A3.4.3 held: artifact projection still recovers a runtime declaration,
  detects an executor, projects artifact kind, and reads artifact fields, so it
  remains an explicit `workstation.skills.core` adapter.
- [x] A3.4.4 held: runtime and receipt boundaries carry explicit dictionaries;
  root and workstation imports are exact aliases to the package-owned classes,
  and historical protocol-zero pickle globals continue to resolve.
- [x] A3.4.5 held: the existing field sets and serialized shapes are unchanged;
  richer authority, attachment, ledger, and receipt-correlation contracts were
  not introduced during this ownership cut.
- [x] Qualification initially exposed one infrastructure assumption mismatch:
  the baseline runner added only repository and `workstation/*/src` roots to
  `PYTHONPATH`, so newly created top-level UV projects were invisible to its
  subprocesses. The runner now discovers both `*/src` and
  `workstation/*/src` deterministically, with a regression test; no production
  import path or runtime behavior was changed.

#### Phase 3 Cut 5 - Portable Composition Plan Values

Measured scope and falsifiable assumptions:

- [x] **A3.5.1:** Confirm that mapper, binding, condition, step, candidate,
  diagnostic, and plan-analysis records are portable skill-domain values. Their
  canonical fields may contain only canonical skill IR or mapping data,
  declarative binding/condition values, and JSON-projectable analysis results.
  If a value requires an artifact method, store, executor, workstation session,
  governance decision, or host realizer, stop and assign it to an adapter or an
  upper layer instead.
- [x] **A3.5.2:** Confirm that composition execution records, execution events,
  iterative orchestration, invoker callbacks, exception handling, emitted
  runtime leaves, and effect execution are a distinct runtime responsibility.
  Keep all of them out of `realized-skill-semantics` in this cut even where
  their current implementation shares helper code with plan analysis.
- [x] **A3.5.3:** Confirm that each existing `from_dict` constructor performs
  only deterministic representation normalization. Preserve exact defaults,
  nested mapper precedence, whitespace/control-character cleanup, tuple
  conversion, constant values, and malformed non-mapping errors without
  importing the root `semantic_text` helper.
- [x] **A3.5.4:** Confirm that historical callers may still place an `Artifact`
  in `SkillCompositionStep.skill`, but that artifact recovery belongs to the
  root analysis/execution adapter rather than the portable value definition.
  Runtime behavior must remain accepted dynamically while the canonical type
  contract narrows to `CanonicalSkillIR | Mapping[str, Any]`.
- [x] **A3.5.5:** Confirm that plan values cross persistence and transport
  boundaries through explicit dictionaries rather than class-qualified object
  payloads. Historical root imports and protocol-zero pickle globals must still
  resolve to the exact package-owned classes; if newly emitted objects require
  the old module name, stop and add an explicit serialization adapter.
- [x] Capture the pre-cut dataclass fields, constructor defaults, nested mapping
  normalization, frozen behavior, analysis serialization, root import
  identities, and protocol-zero pickle globals before editing implementation.
- [x] Add a package-owned `composition` module containing only the eight
  immutable declaration and static-analysis value records. Its dependency
  closure must remain the standard library plus `realized-core-semantics` and
  the package-owned canonical IR value.
- [x] Replace the corresponding root class definitions with exact package
  aliases. Keep proposal, analysis, artifact projection, mapper execution,
  iterative orchestration, execution events, and invoker calls in the root
  module for this cut.
- [x] Preserve the root module's accepted `Artifact` inputs by keeping artifact
  projection in its existing `_skill_ir_dict` adapter; do not add artifact or
  governance dependencies to the package merely to retain the historical type
  annotation.
- [x] Add package tests for every field/default, nested mapper and condition
  construction, mapping validation, whitespace/control-character cleanup,
  immutable records, exact analysis dictionaries, canonical IR and mapping
  step payloads, and falsey constant/expected values.
- [x] Add old-path/new-path object-identity tests, protocol-zero pickle-global
  resolution, and pre-cut differential tests for all mapping constructors and
  analysis serialization. Existing composition execution tests must remain
  unchanged and green.
- [x] Extend package API, import-hygiene, wheel/sdist-content, isolated-wheel,
  Cloud Build, public package documentation, and compatibility-facade checks
  for the composition value module.
- [x] Measure the dependency graph before updating its baseline. Accept only
  the root composition module's canonical ownership observation if it is not
  already represented; reject any package edge to execution, governance,
  persistence, entry/exchange, controller, or workstation layers.
- [x] Run focused package, identity, pickle, differential, composition analysis,
  and composition execution tests; then run deterministic architecture tests,
  the architecture ratchet, isolated distribution verification, and the full
  qualification ladder before accepting the cut.

Cut exit condition:

- [x] Composition plan and static-analysis values have one portable package
  owner; the historical root module is an identity-preserving facade for those
  values while retaining all analysis adapters and runtime execution behavior.

Cut 5 qualification evidence:

- [x] A direct pre-cut/new-path differential compared all eight records across
  177 field, default, frozen, constructor, nested-instance, malformed-input,
  falsey-value, analysis-projection, and root-alias checks; every check passed.
  Permanent golden tests retain the representation-sensitive cases.
- [x] The focused package, API, import-hygiene, root identity, protocol-zero
  pickle, composition analysis, artifact-adapter, and execution suite passed 70
  tests. Syntax compilation and `git diff --check` also passed.
- [x] Fresh wheel/sdist verification passed without the repository on
  `sys.path`: the skill-semantics wheel has 13 entries, its sdist has 29, the
  engine wheel has 91 entries and 77 declared canonical modules, and the
  isolated CLI smoke created both SQLite and state outputs.
- [x] The exact deterministic Cloud Build architecture/package selection passed
  all 399 tests. The measured dependency graph remains 27 components, 126
  owned root modules, 3 owned root package families, 72 package edges, and 589
  grandfathered observations, with zero cycles and zero undeclared edges.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Nine gates were refreshed: 768
  root tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs,
  the incremental publication BDD, publication reference, Flutter analysis,
  and all 51 Flutter widget tests. Six accepted provider, browser, screenshot,
  and trial gates were retained through the baseline merge.

Cut 5 assumption findings:

- [x] A3.5.1 held: the eight records depend only on the standard library,
  `realized-core-semantics`, and package-owned canonical skill IR; no artifact,
  store, executor, governance, controller, or workstation dependency entered
  the package.
- [x] A3.5.2 held: execution records/events, proposal and analysis algorithms,
  artifact adaptation, mapper execution, iteration, callbacks, exceptions, and
  effects remain in the root runtime module.
- [x] A3.5.3 held: package-local normalization reproduced the historical
  control-character and whitespace behavior, defaults, tuple conversion,
  nested mapper precedence, falsey values, and exact malformed-input errors.
- [x] A3.5.4 held: the portable step annotation is now
  `CanonicalSkillIR | Mapping[str, Any]`, while a dedicated root-adapter test
  proves an `Artifact` step still analyzes successfully through `_skill_ir_dict`.
- [x] A3.5.5 held: explicit dictionaries remain the transport/persistence
  representation, root imports are exact package aliases, historical
  protocol-zero globals resolve in the repository compatibility surface, and
  newly emitted objects identify their canonical package owner. No additional
  serialization adapter was required.
- [x] Isolated verification exposed one test-assumption mismatch: the historical
  root `skill_composition` module has never been part of the core-engine wheel.
  Expanding that distribution merely to satisfy the new check would have
  changed an unrelated boundary, so isolated verification now tests the
  package-owned module directly while repository tests own facade identity and
  pickle compatibility. The verifier was also hardened to report child-process
  stdout and stderr on future failures.

#### Phase 3 Cut 6 - Portable Declaration Schema And Composition Rights

Measured scope and falsifiable assumptions:

- [x] **A3.6.1:** Confirm that supported portable skill schema versions,
  deterministic schema-version normalization, and projection of explicit
  composition-right targets are declaration semantics rather than admission,
  authority, realizer-availability, or execution decisions. If any operation
  consults policy, lifecycle, inventory, host capability, or runtime state,
  stop and leave it outside this cut.
- [x] **A3.6.2:** Confirm that this surface closes over only the standard
  library. It may normalize strings already present in an explicit declaration,
  but it must not import governance vocabulary, executor registries, artifacts,
  persistence, controller, LLM, or workstation code.
- [x] **A3.6.3:** Preserve schema behavior exactly: falsey input selects v1,
  internal whitespace and control characters collapse, unknown non-empty
  versions raise the same `ValueError`, and only the existing v1/v2 spellings
  are accepted.
- [x] **A3.6.4:** Preserve composition-target behavior exactly: non-mappings
  yield no targets; list and scalar rights retain input order; accepted
  prefixes are `skill`, `invoke`, and `title` case-insensitively; unknown
  prefixes are ignored; targets are de-duplicated; and `*` short-circuits to
  the single wildcard target.
- [x] **A3.6.5:** Keep declaration payload parsing and validation, policy payload
  parsing, policy summaries, declaration synthesis, admission, lifecycle,
  authority, host binding, and execution outside this module. This cut owns
  only already explicit portable declaration invariants.
- [x] **A3.6.6:** Preserve historical root imports as exact package aliases and
  protocol-zero globals. These functions and constants are not persisted
  class-qualified values, so no data migration should be required; if contrary
  evidence appears, add compatibility decoding before changing ownership.
- [x] Capture the pre-cut `skill_governance.py` independently as
  `/tmp/realized-pre-phase3-declaration-semantics.py`, SHA-256
  `d3d719cefe3f4cd6843ee9c6cb587ff4316f8e2dedd144f041bdd474b3792a82`,
  so the historical functions can be loaded directly for differential
  qualification.
- [x] Add package-owned `declaration` to `realized-skill-semantics` without
  adding any project dependency.
- [x] Move only `SKILL_SCHEMA_VERSION_V1`, `SKILL_SCHEMA_VERSION_V2`,
  `SKILL_SCHEMA_VERSIONS`, `normalize_skill_schema_version`, and
  `composition_binding_targets`; keep private package normalization local and
  behaviorally identical.
- [x] Import the package symbols into `skill_governance.py` as exact aliases and
  remove only their historical definitions. Keep the root module a real
  governance/adapter module rather than classifying it as a facade.
- [x] Migrate canonical schema-version and composition-target consumers directly
  to `realized_skill_semantics.declaration`, preserving separate root imports
  wherever those consumers still need declaration ingestion or governance.
- [x] Add package, identity, protocol-zero, and direct pre-cut/new-path tests for
  every normalization, error, scalar/list, prefix, wildcard, ordering, and
  de-duplication branch.
- [x] Extend package API, import hygiene, wheel/sdist verification, module
  documentation, architecture metadata, and Cloud Build coverage.
- [x] Accept only a graph delta that redirects portable declaration consumers to
  `skill_semantics`, removes obsolete root observations, adds no package
  dependency, and creates no cycle, facade reclassification, or upper-layer
  import.
- [x] Run focused schema/import/export/registry/host-binding/workstation tests,
  the exact deterministic Cloud Build selections, architecture ratchet, fresh
  isolated distribution verification, and full qualification ladder.

Cut exit condition:

- [x] Portable schema-version and explicit composition-right semantics have one
  independently buildable package owner; historical root names are exact
  compatibility aliases; and no declaration ingestion, governance decision,
  realizer availability, host effect, persistence, controller, LLM, or
  workstation behavior moved with them.

Cut 6 qualification evidence:

- [x] Record the pre-cut source hash, differential count, focused and
  deterministic test counts, distribution counts, graph changes,
  qualification status, and the disposition of A3.6.1 through A3.6.6.

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase3-declaration-semantics.py`, SHA-256
  `d3d719cefe3f4cd6843ee9c6cb587ff4316f8e2dedd144f041bdd474b3792a82`.
  An independently loaded old/new differential passed 1,670 checks across
  constants, falsey and malformed schema values, control-character and
  whitespace normalization, exact return and exception outcomes, scalar/list
  rights, ordinary and alternate mappings, prefix case, wildcard position,
  stable ordering, case-sensitive target de-duplication, and exact root alias
  identity.
- [x] Package/API/distribution and compatibility checks passed 91 tests. Focused
  schema/import/export, IR, run-bundle, replay, host-mediation, composition,
  invocation, and workstation consumers passed 280 tests. The exact Cloud Build
  selections passed 454 architecture/core tests and 97 deterministic BDD/UI
  tests.
- [x] Fresh isolated distributions contain 14 skill-semantics wheel entries and
  31 sdist entries, including the declaration owner and its package tests. The
  engine wheel remains at 91 entries and all 77 declared canonical modules.
  Isolated verification preserved owner and compatibility identities and
  created both SQLite and runtime state through the packaged CLI.
- [x] The accepted graph has 28 components, 126 owned root modules, 3 owned root
  package families, 75 package edges, 575 grandfathered observations, and zero
  cycles or undeclared edges. Five planned direct observations now connect
  `governed_skill_installation`, `host_brokers`, `replay_verifier`,
  `run_bundle_io`, and `skill_governance` to `skill_semantics`; the obsolete
  `host_brokers -> skill_governance` root edge is gone. The combined graph moves
  from 628 to 632 edges without adding a package dependency, wildcard export,
  compatibility exception, facade reclassification, or cycle.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Refreshed gates include 775 root
  tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs, the
  incremental publication BDD, publication reference capture, Flutter analysis,
  and all 51 Flutter widget tests; six accepted live/provider/browser/trial
  gates were retained through the declared baseline merge. Candidate and
  promoted baseline are byte-identical at SHA-256
  `f81e42bfc55c6c62971ea61eac5c9d7834da2c1014f31bf51172fbb5f8f6d8ca`.
- [x] A3.6.1 through A3.6.6 held without qualification. The package surface is
  standard-library-only and operates solely on supplied declaration values.
  Payload parsing and validation, policy summaries, declaration synthesis,
  admission, lifecycle, authority, host binding and effects, persistence,
  controller, LLM, and workstation behavior remain in their existing owners.
  Historical names are exact aliases and protocol-zero globals; no serialized
  class-qualified value or data migration was introduced.

#### Phase 3 Cut 7 - Portable Executor Descriptor Semantics

Measured scope and falsifiable assumptions:

- [x] **A3.7.1:** Confirm that canonical executor names, aliases, body-field and
  representation mappings, and deterministic inference from an already
  supplied representation/content mapping describe the portable ability, not
  whether a host currently provides that executor. If any candidate operation
  consults environment, registration, installed software, policy, authority,
  provider health, or runtime state, stop and leave it outside this cut.
- [x] **A3.7.2:** Confirm that the portable descriptor surface closes over only
  the standard library. It must not import artifacts, governance, controller,
  persistence, host ABI, provider implementations, LLM, or workstation code.
- [x] **A3.7.3:** Preserve name normalization exactly: falsey input yields an
  empty name, known aliases collapse to the existing canonical spellings,
  surrounding whitespace and case normalize as before, and unknown non-empty
  names remain normalized rather than being rejected.
- [x] **A3.7.4:** Preserve descriptor precedence exactly: explicit content
  framework, representation, recognized script language, and framework body
  presence are considered in the current order. Preserve non-mapping handling,
  content-key fallback, body-field priority, string conversion, and executable
  text stripping.
- [x] **A3.7.5:** Keep `SUPPORTED_EXECUTOR_FRAMEWORKS_ENV`, the default
  advertised host set, and `normalize_supported_executor_frameworks` outside
  the package owner in this cut. Those values normalize host/application
  availability and must not be conflated with a shipped ability declaration.
- [x] **A3.7.6:** Keep provider registration, prerequisite inspection,
  capability grants, broker binding, dispatch, subprocess/tool invocation, and
  effects outside portable skill semantics. This move must not imply that a
  recognized framework is available on a host.
- [x] **A3.7.7:** Preserve historical imports through exact aliases in both
  `execution_framework_primitives.py` and `execution_frameworks.py`, including
  protocol-zero function globals. The extracted surface contains constants and
  functions rather than persisted class-qualified instances, so no data
  migration should be required.
- [x] Capture the pre-cut `execution_framework_primitives.py` independently,
  including its SHA-256, for direct historical/new-path differential testing.
- [x] Add package-owned `execution` to `realized-skill-semantics` without adding
  a project dependency.
- [x] Move only `SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES`,
  `EXECUTOR_FRAMEWORK_ALIASES`, `EXECUTOR_FRAMEWORK_CONTENT_KEYS`,
  `EXECUTOR_FRAMEWORK_REPRESENTATIONS`, `normalize_executor_framework_name`,
  `executor_framework_content_key`, `ability_executor_framework`, and
  `ability_executable_text`.
- [x] Retain host-support environment/default normalization in
  `execution_framework_primitives.py`, importing package-owned descriptor
  symbols as exact aliases. Keep `execution_frameworks.py` as the real runtime
  learning/execution adapter while it re-exports the portable symbols.
- [x] Migrate canonical descriptor-only consumers directly to
  `realized_skill_semantics.execution`; split imports for consumers that still
  need host-support normalization or concrete execution behavior.
- [x] Add package, identity, protocol-zero, and pre-cut/new-path tests covering
  every alias, unknown name, falsey value, precedence branch, mapping shape,
  content-key fallback, body-field order, string conversion, and whitespace
  behavior.
- [x] Extend package API, import hygiene, wheel/sdist verification, module
  documentation, architecture metadata, package dependencies, and Cloud Build
  coverage.
- [x] Accept only graph changes that redirect descriptor consumers to
  `skill_semantics`, remove obsolete root edges, add no package cycle or
  upper-layer dependency, and leave host availability and execution owners
  unchanged.
- [x] Run focused descriptor, learning, export/import, governance, host,
  controller, runtime, and workstation tests; then run exact deterministic
  Cloud Build selections, architecture ratchet, fresh isolated distribution
  verification, and the full qualification ladder.

Cut exit condition:

- [x] Portable executor descriptor semantics have one independently buildable
  owner, host availability remains a separate runtime concern, historical
  names retain exact identity, and no admission, authority, provider,
  prerequisite, dispatch, effect, persistence, controller, LLM, or workstation
  behavior moved with them.

Cut 7 qualification evidence:

- [x] Record the pre-cut source hash, differential count, focused and
  deterministic test counts, distribution counts, graph changes,
  qualification status, and the disposition of A3.7.1 through A3.7.7.

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase3-execution-semantics.py`, SHA-256
  `9a1af813de96e9074ee3c7742b11be4e65d81a4d087547c9e7d18ba8a765a1bf`.
  An independently loaded old/new differential passed 2,322 checks across
  constants, signatures, falsey and scalar names, every alias, case and
  whitespace variants, unknown names, content-key fallback, explicit,
  representation, script-language, and body-presence precedence, ordinary,
  alternate, custom, and non-mapping inputs, body string conversion and
  stripping, exhaustive descriptor combinations, exact facade identity, and
  separation from host-support normalization.
- [x] Package/API/distribution and compatibility checks passed 98 tests.
  Focused descriptor, learning, schema, import/export, IR, governance,
  composition, host-mediation, controller, runtime, and replay consumers
  passed 244 tests. The exact Cloud Build selections passed 460
  architecture/core tests and 98 deterministic BDD/UI tests.
- [x] Fresh isolated distributions contain 15 skill-semantics wheel entries
  and 33 sdist entries, including the execution owner and its package tests.
  The engine wheel remains at 91 entries and all 77 declared canonical
  modules. Isolated verification preserved both historical facade identities,
  exercised descriptor precedence and body selection, and created SQLite and
  runtime state through the packaged CLI.
- [x] The accepted graph has 28 components, 126 owned root modules, 3 owned
  root package families, 76 package edges, 575 grandfathered observations,
  and zero cycles, undeclared edges, or forbidden edges. The declared
  `runtime_core -> skill_semantics` package edge was added; ten root consumers
  now observe `skill_semantics` directly; nine obsolete root-to-root executor
  adapter edges and the `skills_core -> execution_frameworks` package-to-root
  observation are gone. The combined graph moves from 632 to 633 edges without
  adding a wildcard export, compatibility exception, facade reclassification,
  or cycle.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Refreshed gates include 776 root
  tests, 603 workstation tests with one expected skip, 3 skill-routing BDDs,
  34 publication BDDs, the incremental publication BDD, publication reference
  capture, Flutter analysis, and all 51 Flutter widget tests; six accepted
  live/provider/browser/trial gates were retained through the declared
  baseline merge. Candidate and promoted baseline are byte-identical at
  SHA-256
  `06b7d28e087fee53160cbd4fa7057eb91e60c111de0b51b6da8162c1f5c1e2f0`.
- [x] A3.7.1 through A3.7.7 held without qualification. The package surface is
  standard-library-only and operates solely on supplied representation and
  content values. Host-advertised support, provider registration,
  prerequisites, policy, authority, broker binding, dispatch, effects,
  persistence, controller, LLM, and workstation behavior remain in their
  existing owners. Historical names are exact aliases and protocol-zero
  globals; no serialized class-qualified value or data migration was
  introduced.

### Phase 4 - Give Governance A Canonical Owner

- [ ] Define a governance public API for declaration validation, admission,
  approval, authority evaluation, lifecycle state, revocation, incidents,
  current-use checks, data policy, and trace requirements.
- [ ] Define dependency-inverted ports for governance inventory and persistence.
- [ ] Keep CLI parsing, YAML parsing, LLM prompting, controller reduction,
  workstation session handling, and host execution outside governance.
- [x] Move dependency-light governance primitives and lifecycle rules first.
- [ ] Move approval and authority evaluation after their inputs and outputs are
  represented by governance-owned contracts.
- [ ] Move skill governance, safety overlays, and current-use checks without
  moving skill execution into governance.
- [x] Move data governance without moving virtual filesystem or SQLite adapter
  mechanics into governance.
- [ ] Adapt the existing SQLite store through governance ports rather than
  allowing the governance package to import application composition.
- [ ] Migrate controller, skills, subject, and workstation consumers one at a
  time.
- [ ] Preserve root governance imports as identity-preserving facades during
  qualification.
- [ ] Add deny-by-default, held, inactive, rejected, revoked, expired,
  superseded, denied-authority, and incident-overlay contract tests.
- [ ] Verify that semantic similarity cannot override lifecycle or authority
  decisions.

Exit condition:

- [ ] Governance is independently testable and importable without controller,
  runtime, LLM, workstation, or entry/exchange implementation code.

#### Phase 4 Cut 1 - Governance Vocabulary And Lifecycle Rules

Measured scope and falsifiable assumptions:

- [x] **A4.1.1:** Confirm that skill kind, risk tier, approval class, authority,
  review, installation, activation, trust, and quarantine vocabularies are
  governance-owned values rather than controller or execution policy. If any
  normalization requires a controller, store, executor, host, workstation, or
  model call, stop and leave that behavior in its current owner.
- [x] **A4.1.2:** Confirm that lifecycle normalization, conservative lifecycle
  synthesis, artifact-content projection, effective-lifecycle projection, and
  lifecycle-only invocation eligibility form one cohesive rule surface. The
  artifact-facing functions may depend only on a read-only semantic artifact
  protocol; if they require the concrete root `Artifact`, persistence, or
  inventory access, stop and extract an adapter instead.
- [x] **A4.1.3:** Confirm that lifecycle state is not admission, approval,
  authority evaluation, revocation/incident discovery, or execution. This cut
  may normalize or evaluate a supplied lifecycle record, but it must not load
  overlays, decide admission, issue authority, or invoke a realizer.
- [x] **A4.1.4:** Confirm that `skill_lifecycle_allows_invocation` remains a
  lifecycle-only current-use predicate whose result must still be combined
  with the other governance decisions by its existing callers. If any caller
  treats it as complete authorization, stop and correct that boundary before
  moving the function.
- [x] **A4.1.5:** Preserve exact ordered vocabularies, defaults, accepted
  falsey values, duplicate-authority behavior, control/whitespace cleanup,
  lifecycle synthesis reasons, precedence among explicit lifecycle,
  admission, policy, and timestamps, and exact denial messages. A change to
  any of those is behavioral and is out of scope for this ownership cut.
- [x] **A4.1.6:** Confirm that these modules expose functions and immutable
  constants rather than persisted class-qualified values. Historical root
  imports must become exact aliases to package-owned functions and constants;
  if serialized instances or module-qualified globals are discovered, stop
  and add an explicit compatibility adapter before changing ownership.
- [x] Capture the pre-cut `skill_governance_primitives.py` and
  `skill_lifecycle.py` sources with content hashes before editing so the old
  implementation can be loaded independently for differential qualification.
- [x] Create one cohesive `realized-core-governance` UV project with an
  explicit, lazy public module surface. Its first cut may contain only
  `vocabulary` and `lifecycle`, depend only on `realized-core-semantics`, and
  publish typed wheel and source distributions.
- [x] Implement package-local text normalization that exactly reproduces the
  historical control-character and whitespace behavior without importing the
  root `semantic_text` module.
- [x] Move the public vocabulary constants and normalization functions into
  package-owned `vocabulary`; retain private lookup indexes and list
  normalization as implementation details.
- [x] Move lifecycle status constants, normalizers, synthesis, mapping
  projection, artifact-content projection, effective-state projection, and
  lifecycle-only invocation eligibility into package-owned `lifecycle`.
- [x] Replace both historical root modules with identity-preserving facades.
  Retain accidental private helper names only where doing so costs no new
  public package API, and mark both roots as compatibility facades in the
  architecture manifest.
- [x] Do not move approval evaluation, admission, authority grants, policy
  loading, revocation/incident overlay discovery, inventory, SQLite access,
  replay, tracing, controller composition, host mediation, or workstation
  behavior in this cut.
- [x] Add package tests covering every exported constant and function,
  normalization matrices including controls and falsey values, lifecycle
  synthesis branches, payload precedence, artifact protocol projections,
  current-admission precedence, and every allow/deny branch and message.
- [x] Add exact root/package identity tests and a direct pre-cut/new-path
  differential over representative and boundary values. Existing approval,
  admission, safety-overlay, host-mediation, schema, export, registry, and
  workstation tests must remain unchanged and green.
- [x] Add API, import-hygiene, wheel/sdist-content, isolated-wheel, public
  metadata, Cloud Build, architecture-manifest, module-map, and distribution
  verifier coverage for the governance project.
- [x] Migrate every in-repository canonical consumer of the two historical
  roots directly to the package-owned modules. Declare the package dependency
  only in projects that contain such consumers; no package or canonical root
  module may import a compatibility facade after this cut.
- [x] Use the pre-baseline architecture dry run to test the consumer-migration
  assumption. It correctly rejected canonical-root and workstation-package
  imports of the newly classified facades, so this plan now includes direct
  migration of those existing consumers rather than grandfathering facade use.
- [x] Measure the combined dependency graph before updating its baseline.
  Accept only `core_governance -> core_semantics`, actual consumer-project
  dependencies on `core_governance`, canonical-root-to-owner observations,
  and the two root facade ownership observations implied by this cut. Reject
  any governance-package edge to controller, runtime, LLM, persistence,
  entry/exchange, host, or workstation layers.
- [x] Run focused package, identity, differential, lifecycle, approval,
  admission, safety, and host-mediation tests; then run the deterministic Cloud
  Build architecture selection, architecture ratchet, fresh wheel/sdist
  isolation, and the full qualification ladder before accepting the cut.

Cut exit condition:

- [x] Governance vocabulary and lifecycle-only rules have one independently
  buildable package owner; historical root imports are exact compatibility
  aliases; and no admission, authority, persistence, execution, controller,
  LLM, host, or workstation behavior moved with them.

Cut 1 qualification evidence:

- [x] The captured pre-cut modules have SHA-256 digests
  `41ffa392602a9c9cb896e4d954a503de1af85bf66a63dcc147f814b4bf677ec0`
  and
  `2a4350d3495c39501a1637984c7c7ad5e8b28414ed54bcb70fcd41ffc7c56448`.
  Direct old/new differential qualification passed all 431 constant,
  signature, normalization, falsey-value, authority-ordering, lifecycle,
  payload-precedence, artifact-projection, and exact-message checks. Permanent
  package and compatibility tests retain those boundary cases.
- [x] Focused API, package, distribution, identity, and layer-hygiene coverage
  passed 82 tests; host mediation, skill I/O, run-bundle, and workstation
  regression coverage passed 213 tests. Syntax compilation and
  `git diff --check` passed. The exact deterministic Cloud Build selections
  passed 416 architecture/core tests and 92 BDD/UI-adapter tests.
- [x] Fresh distribution verification passed without the repository on
  `sys.path`: the governance wheel has 10 entries, its sdist has 24, the engine
  wheel has 91 entries and 77 declared canonical modules, no archive contains
  a forbidden Python surface, compatibility identities hold, and the isolated
  CLI smoke created both SQLite and state outputs.
- [x] The accepted graph contains 28 components, 126 owned root modules, 3
  owned root package families, 75 package edges, and 584 grandfathered
  observations, with zero cycles, undeclared dependencies, forbidden edges,
  compatibility-facade imports, or canonical-root facade imports. Accepted
  additions are `core_governance -> core_semantics`, direct runtime/skills
  consumer edges to `core_governance`, canonical-root owner observations, and
  compatibility-facade status for the two historical roots. No rejected edge
  was baselined.
- [x] The full assembled qualification baseline records 15 passing gates with
  zero failures, blocked gates, or gates not run. Refreshed evidence includes
  770 root tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication
  BDDs, the incremental publication BDD, publication reference capture,
  Flutter analysis, and all 51 Flutter widget tests; six previously accepted
  provider/browser/trial gates were retained by explicit baseline merge.
- [x] A4.1.1 through A4.1.6 held. Vocabulary and lifecycle are dependency-light
  governance values; artifact projection uses only the read-only semantic
  protocol; lifecycle remains distinct from admission, overlay discovery,
  authority, and execution; its predicate is composed only after admission and
  safety-overlay evaluation; all historical values/messages were preserved;
  and no class-qualified persisted value required migration.
- [x] Two integration assumptions required correction without widening scope.
  First, the architecture ratchet correctly rejected canonical consumers that
  initially reached the package through newly classified facades, so all such
  consumers now import the canonical package directly. Second, isolated Python
  skill execution exports an explicit child-process package-root allowlist;
  adding `realized_core_governance` to that existing import contract was
  required after `skill_governance` adopted the canonical lifecycle owner. No
  host operation or governance decision moved across that boundary.

#### Phase 4 Cut 2 - Approval Records And Matching

Measured scope and falsifiable assumptions:

- [x] **A4.2.1:** Confirm that approval-record status, payload normalization,
  human summary, read-only artifact projection, temporal validity, and matching
  form one cohesive governance rule surface. If any operation loads installed
  artifacts, reads a repository, evaluates policy, admits a skill, issues
  authority, or invokes a realizer, stop and leave that operation outside.
- [x] **A4.2.2:** Confirm that matching an already supplied approval record to
  an already supplied skill requirement is evidence evaluation, not complete
  admission or invocation authorization. Every caller must continue to combine
  a match with policy, declaration, lifecycle, safety-overlay, and runtime
  checks owned elsewhere.
- [x] **A4.2.3:** Confirm that artifact-facing approval helpers require only the
  read-only semantic artifact protocol. If they require the concrete root
  `Artifact`, mutation, persistence identity, or store access, stop and retain
  a root adapter.
- [x] **A4.2.4:** Preserve temporal behavior exactly: empty and malformed bounds
  remain open, ISO `Z` values retain timezone-aware comparison, lower bounds
  are inclusive after their instant, and upper bounds are inclusive before
  their instant. Do not introduce a clock port or alter the public signatures
  in this ownership-only cut.
- [x] **A4.2.5:** Preserve exact schema/kind filtering, required fields,
  whitespace and control cleanup, scalar/list handling, normalized kind/risk/
  approval/authority values, ordering and duplicate behavior, approval-class
  ordering, optional restriction semantics, exact errors, and exact summary
  text.
- [x] **A4.2.6:** Confirm that approval values are dictionaries, immutable
  constants, and functions rather than persisted class-qualified instances.
  Historical root imports must become exact aliases; if serialized globals are
  discovered, stop and add explicit compatibility decoding first.
- [x] Capture the pre-cut `approval_governance.py` source and content hash so
  the historical implementation can be loaded independently for differential
  qualification.
- [x] Add package-owned `approval` to `realized-core-governance` without adding
  any dependency beyond the standard library and `realized-core-semantics`.
- [x] Move approval status, payload normalization, summary, artifact projection,
  temporal validity, record matching, and supplied-artifact filtering into the
  package module. Keep installed-artifact discovery, policy/admission decisions,
  persistence, authority issuance, tracing, execution, and UI behavior outside.
- [x] Replace `approval_governance.py` with an identity-preserving facade,
  retaining accidental private helper names only where doing so does not widen
  the package's public API.
- [x] Migrate every canonical in-repository consumer directly to
  `realized_core_governance.approval`; no canonical module or package may import
  the compatibility facade after this cut.
- [x] Add package tests for all public constants/functions, valid and invalid
  payload matrices, missing-field errors, scalar/list/falsey handling, artifact
  projection, status and temporal denial branches, optional restriction
  semantics, authority subset behavior, approval-class ordering, stable match
  order, and exact summaries.
- [x] Add root/package identity tests and a direct pre-cut/new-path differential
  covering signatures, normalization, payloads, projections, all matching
  branches, deterministic past/future bounds, malformed timestamps, and
  supplied-artifact filtering.
- [x] Extend package API, import hygiene, wheel/sdist contents, isolated-wheel
  verification, module documentation, architecture metadata, and Cloud Build
  checks for the approval module.
- [x] Measure the graph before updating its baseline. Accept only the canonical
  owner observation for the root approval facade and direct root-to-governance
  consumer observations implied by this cut; reject any new package dependency
  or any governance edge to controller, runtime, persistence, host, LLM,
  entry/exchange, or workstation layers.
- [x] Run focused package, identity, differential, approval/admission, schema,
  export, run-bundle, host-mediation, and workstation checks; then run the exact
  deterministic Cloud Build selections, architecture ratchet, fresh isolated
  distribution verification, and the full qualification ladder.

Cut exit condition:

- [x] Approval records and matching have one independently buildable governance
  owner; the historical root is an exact compatibility facade; and no policy,
  admission, authority issuance, persistence, execution, host, controller, LLM,
  or workstation behavior moved with them.

Cut 2 qualification evidence:

- [x] Record pre-cut source hash, differential count, focused and deterministic
  test counts, distribution counts, graph changes, qualification status, and
  the disposition of A4.2.1 through A4.2.6.

- [x] The captured pre-cut source is
  `/tmp/realized-pre-phase4-approval-governance.py`, SHA-256
  `852e939da5ea48415eb980e46befa14a74fd70ce3aeb351846ec9ebbe13d440f`.
  The independently loaded historical implementation and package owner passed
  82 direct differential checks across signatures, constants, normalization,
  payloads and exact errors, summaries, artifact projection, all matching
  branches, deterministic temporal boundaries, malformed bounds, and stable
  supplied-artifact filtering.
- [x] Focused verification passed 75 package/API/distribution/compatibility
  tests, 141 approval/admission/schema/export/run-bundle/host/workstation tests,
  and five explicit workstation approval journeys. The exact Cloud Build
  selections passed 425 architecture/core tests and 93 deterministic BDD and
  UI-adapter tests.
- [x] Fresh artifacts passed isolated installation and execution. The
  governance wheel contains 11 entries and the sdist 26 entries, including the
  new approval owner and its package tests; the full wheel-only CLI smoke test
  created SQLite and state while preserving exact facade/package identities.
- [x] The measured graph remained at 28 components, 126 owned root modules, 3
  owned root package families, 75 package edges, and zero cycles. Only the two
  planned direct observations (`governance_inventory -> core_governance` and
  `run_bundle_io -> core_governance`), two approval-facade boundary
  reclassifications, and the approval root ownership reclassification were
  accepted. Grandfathered observations fell from 584 to 579; no package
  dependency or forbidden layer edge was added.
- [x] The promoted qualification candidate is byte-identical to the captured
  candidate (SHA-256
  `ed4b7141be0b47f99f977b331c11440e007ba29f78faff36209acdb234dcb0bd`)
  and records 15 passing gates with zero failures, blocked gates, or gates not
  run. Refreshed evidence includes 771 root tests, 603 workstation tests, 3
  skill-routing BDDs, 34 publication BDDs, the incremental publication BDD,
  publication reference capture, Flutter analysis, and all 51 Flutter widget
  tests; six manual/provider/browser gates were retained by explicit merge.
- [x] A4.2.1 through A4.2.6 held without qualification. The extracted surface
  evaluates already supplied records only; uses the read-only semantic artifact
  protocol; preserves temporal, normalization, ordering, duplicate, error, and
  summary behavior; leaves discovery, policy, admission, safety, authority,
  persistence, execution, host, controller, LLM, and workstation decisions in
  their prior owners; and introduces no serialized class-qualified value.

#### Phase 4 Cut 3 - Revocation And Incident Safety Overlays

Measured scope and falsifiable assumptions:

- [x] **A4.3.1:** Confirm that revocation/incident vocabularies, payload
  normalization, human summaries, read-only artifact projection, temporal
  validity, record matching, and lifecycle-overlay projection form one cohesive
  governance rule surface. If any operation discovers artifacts, reads a
  repository, mutates lifecycle, admits a skill, grants authority, or invokes a
  realizer, stop and leave that operation outside.
- [x] **A4.3.2:** Confirm that a safety overlay is evidence derived from already
  supplied records, not a complete current-use or invocation decision. Existing
  callers must continue to combine it mechanically with declaration,
  admission, approval, lifecycle, authority, and runtime checks owned elsewhere.
- [x] **A4.3.3:** Confirm that artifact-facing helpers require only read-only
  semantic artifact protocols: content for projection and title plus content
  for matching/overlay evidence. If they require the concrete root `Artifact`,
  persistence identity, mutation, inventory, or store access, stop and retain a
  root adapter.
- [x] **A4.3.4:** Preserve precedence exactly: any matching active revocation
  dominates every incident; the last matching revocation supplies lifecycle
  values; all matching record titles remain in source order; incident strength
  is ordered `none < restrict < suspend < quarantine`; and an equal-strength
  tie keeps the first matching incident selected by `max`.
- [x] **A4.3.5:** Preserve temporal behavior exactly: empty and malformed bounds
  remain open, ISO `Z` values retain timezone-aware comparison, lower bounds
  are inclusive after their instant, and upper bounds are inclusive before
  their instant. Do not add a clock port or alter public signatures in this
  ownership-only cut.
- [x] **A4.3.6:** Preserve exact schema/kind filtering, required fields,
  whitespace and control cleanup, scalar/list/falsey handling, lifecycle
  defaults, subject-title and optional subject-kind matching, status/severity/
  action normalization, exact errors, exact summaries, and empty-overlay shape.
- [x] **A4.3.7:** Confirm that safety values are dictionaries, immutable
  constants, and functions rather than persisted class-qualified instances.
  Historical root imports must become exact aliases; if serialized globals are
  discovered, stop and add explicit compatibility decoding first.
- [x] Capture the pre-cut `skill_safety_governance.py` source independently as
  `/tmp/realized-pre-phase4-skill-safety-governance.py`, SHA-256
  `67c9d58daa9688c1b0e5057820995ee41eeecd8b561f39598061e121f58ad828`,
  so historical behavior can be loaded directly for differential qualification.
- [x] Add package-owned `safety` to `realized-core-governance` without adding a
  dependency beyond the standard library and `realized-core-semantics`.
- [x] Move record constants, normalizers, payload parsing, summaries, artifact
  projections, temporal matching, supplied-artifact filtering, and safety
  overlay computation into the package module. Keep inventory loading,
  current-use composition, policy/admission, authority, persistence, tracing,
  execution, host mediation, controller, LLM, and workstation behavior outside.
- [x] Replace `skill_safety_governance.py` with an identity-preserving facade,
  retaining accidental private helper names only where doing so does not widen
  the package public API.
- [x] Migrate every canonical in-repository consumer directly to
  `realized_core_governance.safety`; no canonical module or package may import
  the compatibility facade after this cut.
- [x] Add package tests for all constants/functions, valid and invalid payload
  matrices, exact missing-field errors, scalar/list/falsey handling, artifact
  projection, status and temporal denial branches, optional kind restrictions,
  stable filtering, revocation dominance, last-revocation selection, incident
  action precedence, equal-strength ties, exact overlay shapes, and summaries.
- [x] Add root/package identity tests and a direct pre-cut/new-path differential
  covering signatures, constants, normalization, payloads/errors, projections,
  all matching branches, deterministic temporal boundaries, malformed bounds,
  supplied-artifact filtering, and every overlay precedence branch.
- [x] Extend package API, import hygiene, wheel/sdist contents, isolated-wheel
  verification, module documentation, architecture metadata, and Cloud Build
  checks for the safety module.
- [x] Measure the graph before updating its baseline. Accept only the canonical
  owner observation for the root safety facade and direct root-to-governance
  consumer observations implied by this cut; reject any new package dependency
  or governance edge to controller, runtime, persistence, host, LLM,
  entry/exchange, or workstation layers.
- [x] Run focused package, identity, differential, safety-overlay, admission,
  schema, export, registry, run-bundle, host-mediation, and workstation checks;
  then run the exact deterministic Cloud Build selections, architecture
  ratchet, fresh isolated distribution verification, and full qualification
  ladder.

Cut exit condition:

- [x] Revocation and incident safety records have one independently buildable
  governance owner; the historical root is an exact compatibility facade; and
  no discovery, policy, admission, authority, persistence, execution, host,
  controller, LLM, or workstation behavior moved with them.

Cut 3 qualification evidence:

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase4-skill-safety-governance.py`, SHA-256
  `67c9d58daa9688c1b0e5057820995ee41eeecd8b561f39598061e121f58ad828`.
- [x] The independent old/new differential passed all 231 signature, constant,
  normalization, payload, error, summary, projection, matching, temporal,
  ordering, identity, and overlay-precedence checks.
- [x] Twelve package-owned safety tests passed. The package/API/distribution/
  compatibility selection passed 88 tests, and the focused safety, admission,
  schema, export, registry, run-bundle, host-mediation, and workstation
  selection passed 165 tests.
- [x] The exact Cloud Build selections passed 437 architecture/core tests and
  94 deterministic BDD/UI-adapter tests.
- [x] Fresh isolated distribution verification passed without the repository on
  `sys.path`: the governance wheel has 12 entries, its sdist has 28, the engine
  wheel has 91 entries and 77 declared canonical modules, and the installed CLI
  created both SQLite and state outputs.
- [x] The accepted graph has 28 components, 126 owned root modules, 3 owned root
  package families, 75 package edges, 571 grandfathered observations, zero
  cycles, and zero undeclared edges. The only ownership changes are the safety
  facade classification and the direct root consumers migrated to the package.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Refreshed gates include 772 root
  tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs, the
  incremental publication BDD, publication reference capture, Flutter analysis,
  and all Flutter widget tests; six accepted live/provider/browser/trial gates
  were retained through the baseline merge. Candidate and promoted baseline are
  byte-identical at SHA-256
  `f77f499b930dab35d245faf43aa4ea59fdc4095a4da7973d729149441519a702`.
- [x] A4.3.1 through A4.3.7 held without qualification. The package evaluates
  already supplied records through read-only artifact protocols, preserves all
  historical precedence, temporal, normalization, filtering, ordering, error,
  and summary behavior, and leaves discovery, complete authorization,
  persistence, execution, host, controller, LLM, and workstation concerns in
  their existing owners.

#### Phase 4 Cut 4 - Data Classification And Access Rules

Measured scope and falsifiable assumptions:

- [x] **A4.4.1:** Confirm that data-class vocabulary, normalization, projection
  from an already supplied governance context, access evaluation, named-query
  declaration normalization, and the read-only-query predicate form one
  cohesive governance rule surface. If any operation opens a mount, executes
  SQL, discovers a registry, reads persistence, or invokes a host broker, stop
  and leave that operation outside.
- [x] **A4.4.2:** Confirm that data access is evaluated only against the supplied
  runtime governance context. The package must not construct grants, infer
  authorities, admit a skill, inspect ambient paths, or claim that a positive
  data-class result is complete authorization for a host effect.
- [x] **A4.4.3:** Preserve exact normalization behavior: ordered data-class
  vocabulary, unknown-value fallback, lowercase/hyphen/space conversion,
  control and whitespace cleanup, list-only collection treatment, stable
  first-occurrence deduplication, falsey handling, and caller-selected defaults.
- [x] **A4.4.4:** Preserve governance-context precedence and diagnostics exactly:
  granted data classes precede declaration data classes, duplicates retain their
  first position, an empty request succeeds, absent grants fail closed, missing
  classes retain request order, and rationale strings keep their historical
  punctuation and normalized operation text.
- [x] **A4.4.5:** Preserve named-query behavior exactly: accept mapping entries
  only, remove blank names and SQL, retain parameter order only when represented
  as a list, preserve duplicates and order, default query data classification to
  `internal`, and do not conflate registry normalization with SQL execution.
- [x] **A4.4.6:** Preserve the current lexical read-only-query predicate exactly,
  including case/whitespace normalization, accepted `select ` and `with `
  prefixes, forbidden mutation fragments, and rejection of empty or otherwise
  shaped SQL. Hardening that policy is a separate behavioral change.
- [x] **A4.4.7:** Confirm that data-governance values are dictionaries, lists,
  tuples, strings, booleans, immutable constants, and functions rather than
  persisted class-qualified instances. Historical root imports must become
  exact aliases; if serialized globals are discovered, stop and add explicit
  compatibility decoding first.
- [x] Capture the pre-cut `data_governance.py` source independently as
  `/tmp/realized-pre-phase4-data-governance.py`, SHA-256
  `4e3ea699c3030db987ab2c7c427110f2bb22b6b77c9525cd68a3875c646ddab8`,
  so historical behavior can be loaded directly for differential qualification.
- [x] Add package-owned `data` to `realized-core-governance` without adding a
  dependency beyond the standard library and the package's existing declared
  dependencies.
- [x] Move data-class constants and normalizers, supplied-context projection,
  access evaluation, named-query normalization, and lexical read-only-query
  evaluation into the package module. Keep virtual mounts, SQLite connections,
  registry discovery, query execution, host brokerage, persistence, tracing,
  controller, LLM, and workstation behavior outside.
- [x] Replace `data_governance.py` with an identity-preserving facade, retaining
  accidental private helper names only where doing so does not widen the package
  public API.
- [x] Migrate every canonical in-repository consumer directly to
  `realized_core_governance.data`; no canonical module or package may import the
  compatibility facade after this cut.
- [x] Add package tests for every constant/function and all normalization,
  falsey, scalar, list-only, duplicate, ordering, context-precedence,
  allow/deny-rationale, named-query, and read-only-query branches.
- [x] Add root/package identity tests and a direct pre-cut/new-path differential
  covering signatures, constants, private helper compatibility, representative
  malformed values, exact result ordering, exact rationale strings, and every
  read-only-query branch.
- [x] Extend package API, import hygiene, wheel/sdist contents, isolated-wheel
  verification, module documentation, architecture metadata, and Cloud Build
  checks for the data module.
- [x] Measure the graph before updating its baseline. Accept only the canonical
  owner observation for the root data-governance facade and direct root consumer
  observations implied by this cut; reject any new package dependency or
  governance edge to controller, runtime, persistence, host, LLM,
  entry/exchange, or workstation layers.
- [x] Run focused package, identity, differential, host-broker, virtual-mount,
  data-access, skill-governance, and workstation checks; then run the exact
  deterministic Cloud Build selections, architecture ratchet, fresh isolated
  distribution verification, and full qualification ladder.

Cut exit condition:

- [x] Data classification and supplied-context access rules have one
  independently buildable governance owner; the historical root is an exact
  compatibility facade; and no filesystem, SQLite, registry-discovery, query-
  execution, host-broker, persistence, controller, LLM, or workstation behavior
  moved with them.

Cut 4 qualification evidence:

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase4-data-governance.py`, SHA-256
  `4e3ea699c3030db987ab2c7c427110f2bb22b6b77c9525cd68a3875c646ddab8`.
- [x] The independent old/new differential passed all 137 signature, constant,
  private-helper, normalization, collection, context-precedence, diagnostic,
  named-query, and read-only-query checks.
- [x] The package/API/distribution/compatibility selection passed 95 tests. The
  host-mediation, host-context, delegation, runtime, executor-learning, skill
  I/O, run-bundle, and workstation selection passed 237 tests.
- [x] The exact Cloud Build selections passed 443 architecture/core tests and
  95 deterministic BDD/UI-adapter tests.
- [x] Fresh isolated distribution verification passed without the repository on
  `sys.path`: the governance wheel has 13 entries, its sdist has 30, the engine
  wheel has 91 entries and 77 declared canonical modules, and the installed CLI
  created both SQLite and state outputs.
- [x] The accepted graph has 28 components, 126 owned root modules, 3 owned root
  package families, 75 package edges, 572 grandfathered observations, zero
  cycles, and zero undeclared edges. Its only new observations are the data
  facade's canonical owner and the two root consumers redirected to that owner;
  no package dependency changed.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Refreshed gates include 773 root
  tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs, the
  incremental publication BDD, publication reference capture, Flutter analysis,
  and all Flutter widget tests; six accepted live/provider/browser/trial gates
  were retained through the baseline merge. Candidate and promoted baseline are
  byte-identical at SHA-256
  `24cca003ef0ae10202826789310247c0e91c9c910c4bfe442a980e941d8027c1`.
- [x] A4.4.1 through A4.4.7 held without behavioral qualification. One test
  assumption was corrected to preserve the historical lexical SQL predicate:
  a mutation token immediately following `(` is not rejected because the
  existing check looks only for space-delimited fragments. Hardening that rule
  remains a separate behavior change rather than being smuggled into this move.

#### Phase 4 Cut 5 - Stored Governance Record Projections

Measured scope and falsifiable assumptions:

- [x] **A4.5.1:** Confirm that declaration, policy, and admission projection from
  an already supplied artifact, plus policy-record classification, form one
  cohesive read-only governance-record surface. If any operation synthesizes a
  declaration, validates a schema, evaluates admission, loads inventory,
  mutates an artifact, or invokes runtime behavior, stop and leave it outside.
- [x] **A4.5.2:** Confirm that all projections require only the canonical
  read-only artifact-content protocol. If a concrete `Artifact`, identifier,
  title, enum, persistence record, controller, store, or executor is required,
  stop and retain the affected operation in its current adapter.
- [x] **A4.5.3:** Preserve projection behavior exactly: non-mapping artifact
  content yields an empty dictionary; absent, falsey, or non-mapping stored
  records yield an empty dictionary; mapping records are defensively copied;
  and a policy record is identified only by a non-empty policy projection.
- [x] **A4.5.4:** Keep stored-record projection distinct from declaration
  synthesis, policy parsing, approval matching, current-use evaluation,
  lifecycle overlays, authority grants, inventory discovery, and execution.
  Consumers must continue to compose those mechanisms explicitly.
- [x] **A4.5.5:** Confirm that these APIs return ordinary dictionaries and a
  boolean rather than persisted class-qualified values. Historical
  `skill_governance` globals must resolve to exact package-owned function
  objects; if serialized values are found, add explicit compatibility decoding
  before changing ownership.
- [x] **A4.5.6:** Confirm that `skill_governance.py` remains a real root adapter
  and orchestration module after this cut, not a compatibility facade. Only the
  four extracted function names become aliases; its declaration synthesis,
  parsing, admission, current-use, host-policy, and executor-dependent behavior
  must remain in place.
- [x] **A4.5.7:** Preserve canonical consumer behavior while removing their
  dependency on `skill_governance` when they need only stored-record projection.
  Consumers that also require synthesis or admission orchestration may retain a
  separate root import for those separate responsibilities.
- [x] Capture the pre-cut `skill_governance.py` source independently as
  `/tmp/realized-pre-phase4-skill-governance-records.py`, SHA-256
  `4231af3063b2d2f13e93a01027ef909004dda62039885c2e90230690f60e8c3a`,
  so the historical projection functions can be loaded directly for
  differential qualification.
- [x] Add package-owned `records` to `realized-core-governance` without adding a
  dependency beyond the standard library and `realized-core-semantics`.
- [x] Move only `artifact_skill_declaration`, `artifact_skill_policy`,
  `artifact_skill_admission`, and `artifact_is_policy_record` into the package
  module using the read-only artifact-content protocol.
- [x] Import those four package functions into `skill_governance.py` as exact
  aliases and remove only their old definitions. Do not classify the root module
  as a facade or move any adjacent synthesis/evaluation behavior opportunistically.
- [x] Migrate canonical consumers directly to
  `realized_core_governance.records` for projection-only dependencies, while
  preserving separate root imports where the same consumer still needs
  non-extracted orchestration.
- [x] Add package tests for invalid content, absent/falsey/non-mapping record
  values, defensive copies, accepted mapping implementations, and exact
  policy-record truth behavior.
- [x] Add root/package identity tests, historical protocol-zero function-global
  checks, and a direct pre-cut/new-path differential covering signatures,
  mutable-source isolation, and all projection/classification branches.
- [x] Extend package API, import hygiene, wheel/sdist contents, isolated-wheel
  verification, module documentation, architecture metadata, and Cloud Build
  checks for the records module.
- [x] Measure the graph before updating its baseline. Accept only direct
  projection-consumer redirection from `skill_governance` to `core_governance`;
  reject a new package dependency, cycle, facade reclassification of
  `skill_governance`, or expansion into runtime/controller/workstation policy.
- [x] Run focused package, identity, differential, inventory, export, registry,
  installation, replay, run-bundle, runtime-governance, skill-boundary, skill-IR,
  and workstation checks; then run the exact deterministic Cloud Build
  selections, architecture ratchet, fresh isolated distribution verification,
  and full qualification ladder.

Cut exit condition:

- [x] Stored declaration, policy, and admission projections have one
  independently buildable governance owner; `skill_governance` exposes exact
  compatibility aliases while retaining its real adapter/orchestration
  responsibilities; and no synthesis, parsing, admission, current-use,
  inventory, authority, execution, controller, LLM, or workstation behavior
  moved with the projections.

Cut 5 qualification evidence:

- [x] Record pre-cut source hash, differential count, focused and deterministic
  test counts, distribution counts, graph changes, qualification status, and
  the disposition of A4.5.1 through A4.5.7.

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase4-skill-governance-records.py`, SHA-256
  `4231af3063b2d2f13e93a01027ef909004dda62039885c2e90230690f60e8c3a`.
  An independently loaded old/new differential passed 1,066 checks across
  callable shape, malformed and falsey content, ordinary and alternate mapping
  implementations, top-level defensive copying, historical shallow-copy
  behavior, policy-record truth behavior, and exact root alias identity.
- [x] Package/API/distribution compatibility checks passed 100 tests: 48
  governance-package tests and 52 root-identity/core-engine distribution tests.
  Focused inventory, export, registry, installation, replay, run-bundle,
  runtime-governance, boundary, skill-IR, controller, and workstation checks
  passed 242 tests. Restricted nested-process runs failed only because the
  sandbox could not resolve child UV dependencies; the same three suites passed
  68, 38, and 136 tests with their declared process/dependency access.
- [x] The exact deterministic Cloud Build selections passed 447
  architecture/core tests and 96 BDD/UI tests. Fresh isolated distributions
  contained 14 governance-wheel entries, 32 governance-sdist entries, and 91
  engine-wheel entries with all 77 canonical engine modules. The isolated
  verifier preserved owner and compatibility identities and created both a
  SQLite database and runtime state through the packaged CLI.
- [x] The accepted graph has 28 components, 126 owned root modules, 3 owned root
  package families, 75 package edges, 571 grandfathered observations, and zero
  cycles or undeclared edges. The measured Cut 5 delta adds only direct
  `capability_runtime -> core_governance` and
  `skill_boundary_normalization -> core_governance` observations, removes three
  obsolete root-to-`skill_governance` edges, and reduces the combined graph from
  629 to 628 edges without adding a package dependency, wildcard export,
  compatibility exception, or facade reclassification.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Refreshed gates include 774 root
  tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs, the
  incremental publication BDD, publication reference capture, Flutter analysis,
  and all Flutter widget tests; six accepted live/provider/browser/trial gates
  were retained through the declared baseline merge. Candidate and promoted
  baseline are byte-identical at SHA-256
  `9bce351e004e4d40e69114b2d01d45fc419e7fe2c4f4ecc49888e23d03b7e045`.
- [x] A4.5.1 through A4.5.7 held without qualification. The package owns only
  structural projection from an already supplied artifact through the canonical
  read-only content protocol. Declaration synthesis, schema and policy parsing,
  admission and current-use evaluation, inventory, authority, persistence,
  execution, controller, LLM, and workstation behavior remain with their
  existing adapters and orchestrators.

#### Phase 4 Cut 6 - Governance Inventory Port And Classification

Measured scope and falsifiable assumptions:

- [x] **A4.6.1:** Confirm that loading all already-persisted artifacts through a
  single read-only operation and classifying supplied artifacts as policy,
  approval, revocation, and incident records form one cohesive governance
  inventory surface. If classification requires controller state, mutation,
  admission, execution, or storage-specific queries, stop and leave it outside.
- [x] **A4.6.2:** Confirm that the existing artifact store satisfies a narrow
  structural inventory-reader protocol without importing the concrete SQLite
  adapter into governance. If the package needs connection management, schema
  creation, SQL, paths, commits, or application composition, stop the cut.
- [x] **A4.6.3:** Preserve inventory behavior exactly: call
  `load_all_artifacts` once; retain the returned collection under `artifacts`;
  classify each record independently so one record may occupy multiple
  categories; return category lists in source order; and retain the rounded,
  non-negative `timings.load_seconds` measurement.
- [x] **A4.6.4:** Keep controller snapshot caching and invalidation in the root
  controller adapter. The governance package may load and classify through its
  port, but it must not own controller attributes, cache lifetime, session
  behavior, persistence invalidation, or workstation state.
- [x] **A4.6.5:** Preserve the historical
  `governance_inventory.load_governance_inventory` import as the exact
  package-owned function object while retaining the three controller-specific
  functions as real root adapter functions.
- [x] **A4.6.6:** Migrate only consumers that require inventory loading directly
  to the package API. Any consumer that depends on controller caching,
  installation orchestration, replay behavior, or workstation presentation
  must retain those separate responsibilities in its existing owner.
- [x] **A4.6.7:** Accept only dependency movement toward the governance package:
  no governance-to-store dependency, no cycle, no concrete adapter import, no
  compatibility exception, and no expansion into admission, authority grants,
  current-use evaluation, execution, controller, LLM, or UI behavior.
- [x] Capture the pre-cut `governance_inventory.py` source independently as
  `/tmp/realized-pre-phase4-governance-inventory.py`, SHA-256
  `9e341a777f13f2759a9595ac65741dd8bdc7a1659c65bf1e1948b5deecf574b5`,
  so the historical loader can be exercised directly in differential tests.
- [x] Add package-owned `inventory` to `realized-core-governance` without adding
  a dependency beyond the standard library and `realized-core-semantics`.
- [x] Define a narrow structural port for `load_all_artifacts` and move only
  inventory loading, independent record classification, and load timing into
  the package module.
- [x] Replace the historical root loader with an exact alias while preserving
  controller snapshot, policy/approval projection, and invalidation behavior in
  `governance_inventory.py`.
- [x] Migrate replay, installation, and workstation-host consumers only where
  they use the loader directly; declare and ratchet any truthful package edge
  in the same cut.
- [x] Add package tests for empty and mixed inventories, independent overlapping
  categories, source order, one loader call, returned-collection identity,
  structural protocol conformance, and timing shape.
- [x] Add root/package identity tests and a direct pre-cut/new-path differential
  covering signatures, exact category membership and ordering, collection
  identity, call count, and timing normalization.
- [x] Extend package API, import hygiene, wheel/sdist contents, isolated-wheel
  verification, module documentation, architecture metadata, and Cloud Build
  checks for the inventory module.
- [x] Measure the graph before updating its baseline. Reject any upward edge,
  governance-to-persistence dependency, cycle, or new package-to-root import.
- [x] Run focused package, compatibility, inventory, installation, replay, and
  workstation checks; then run the exact deterministic Cloud Build selections,
  architecture ratchet, fresh isolated distribution verification, and full
  qualification ladder.

Cut exit condition:

- [x] Governance inventory loading and classification have one independently
  buildable owner behind a narrow read-only port; the concrete store remains an
  adapter; controller caching remains controller-owned; and historical loader
  imports preserve exact identity without moving admission or execution policy.

Cut 6 qualification evidence:

- [x] Record pre-cut source hash, differential count, focused and deterministic
  test counts, distribution counts, graph changes, qualification status, and
  the disposition of A4.6.1 through A4.6.7.

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase4-governance-inventory.py`, SHA-256
  `9e341a777f13f2759a9595ac65741dd8bdc7a1659c65bf1e1948b5deecf574b5`.
  An independently loaded old/new differential passed 17,507 checks across
  public signature shape, structural port conformance, one-read behavior,
  returned-collection identity, list and tuple collections, all 625 combinations
  of absent, empty, malformed, ordinary-mapping, and alternate-mapping record
  values, overlapping category membership, source order, timing rounding, and
  error propagation.
- [x] The full governance package passed 51 tests. Focused compatibility,
  metadata, inventory, installation, replay, run-bundle, layer-hygiene, and
  workstation checks passed their 58-, 59-, and 11-test selections. The exact
  deterministic Cloud Build selections passed 463 architecture/core tests and
  99 BDD/UI tests.
- [x] Fresh isolated distributions contained 15 governance-wheel entries, 34
  governance-sdist entries, and 91 engine-wheel entries with all 77 canonical
  engine modules. Isolated verification preserved the historical loader
  identity, exercised overlapping governance classification through the port,
  and created both SQLite and runtime state through the packaged CLI.
- [x] The accepted graph has 28 components, 126 owned root modules, 3 owned root
  package families, 77 package edges, 572 grandfathered observations, and zero
  cycles or undeclared edges. The measured Cut 6 delta adds only the declared
  `foundation_host -> core_governance` package edge, removes the
  `foundation_host -> governance_inventory` package-to-root observation and the
  `governed_skill_installation -> governance_inventory` and
  `replay_verifier -> governance_inventory` root edges, and reduces the combined
  graph from 633 to 631 edges without adding a governance-to-store dependency,
  compatibility exception, wildcard export, or canonical facade import.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Refreshed gates include 777 root
  tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs, the
  incremental publication BDD, publication reference capture, Flutter analysis,
  and all Flutter widget tests; six accepted live/provider/browser/trial gates
  were retained through the declared baseline merge. Candidate and promoted
  baseline are byte-identical at SHA-256
  `1fab7b333c424418e8a510c70f07cb5f9e97a52523c4591e5501f474ef5fb752`.
- [x] A4.6.1 through A4.6.7 held without qualification. The package owns only a
  read-only structural inventory port, one complete-load operation, independent
  governance-record classification, and load timing. SQLite, persistence,
  controller cache lifetime and invalidation, installation, replay, admission,
  authority, current-use evaluation, runtime execution, LLM, and workstation
  presentation remain with their existing adapters and orchestrators.

#### Phase 4 Cut 7 - Governed Declaration And Policy Normalization

Measured scope and falsifiable assumptions:

- [x] **A4.7.1:** Confirm that validation and normalization of an already
  decoded governed v2 skill declaration form one pure governance operation. If
  the operation needs YAML parsing, artifact synthesis, storage, host
  inspection, execution, controller state, or workstation state, stop and
  leave those concerns outside governance.
- [x] **A4.7.2:** Confirm that normalization of an already decoded admission
  policy and construction of its reviewable summary are pure governance
  operations. If either operation makes an admission decision, checks current
  use, issues authority, consults an inventory, or mutates lifecycle state,
  stop the cut.
- [x] **A4.7.3:** Treat portable skill-kind and executor normalization as lower
  semantic vocabulary rather than duplicating it in governance. The truthful
  dependency may be `core_governance -> skill_semantics`; a reverse edge,
  runtime dependency, or host dependency rejects the cut.
- [x] **A4.7.4:** Preserve declaration and policy behavior exactly, including
  accepted mapping shapes, schema and kind normalization, required and
  authority-bound fields, defaults, string conversion, exact return values,
  exact exception types and messages, and the historical policy-summary text.
- [x] **A4.7.5:** Preserve historical root names as exact package-owned
  function and constant aliases. Keep unrelated vocabulary exports, including
  `SKILL_AUTHORITIES`, available from their established root module without
  moving their ownership opportunistically.
- [x] **A4.7.6:** Migrate only direct consumers of declaration and policy
  normalization. YAML decoding, artifact-to-declaration synthesis, virtual
  mount inference, broker scanning, Python surface inspection, admission,
  current-use checks, authority grants, and execution remain in their existing
  adapters and orchestrators.
- [x] **A4.7.7:** Accept only a graph delta that declares the lower-layer
  governance-to-skill-semantics dependency, removes an obsolete root adapter
  observation, adds no cycle or undeclared edge, and does not broaden any
  compatibility exception or wildcard surface.
- [x] Capture the pre-cut `skill_governance.py` source independently as
  `/tmp/realized-pre-phase4-governance-declarations.py`, SHA-256
  `7b4a133826f2b02e8039ab513f2fe93e1baa6055047a6e2beda9c9c8ce8cd207`,
  so historical behavior can be exercised independently of root aliases.
- [x] Add package-owned `declarations` to `realized-core-governance`, depending
  only on the standard library and the lower semantic packages already
  justified by the extracted operations.
- [x] Move only governed declaration validation and normalization, admission
  policy normalization, and policy-summary construction into the package.
- [x] Replace the corresponding historical root definitions with exact aliases
  while retaining all host, artifact, admission, authority, lifecycle, and
  execution orchestration in `skill_governance.py`.
- [x] Migrate `skill_schema_io` directly to the package-owned declaration and
  vocabulary APIs without moving YAML parsing or exchange-format behavior.
- [x] Add package tests for accepted and rejected schema, kind and executor
  normalization, every required and authority-bound field, policy defaults and
  validation, summary rendering, exact failures, and root/package identity.
- [x] Extend package API, import hygiene, wheel/sdist contents, isolated-wheel
  verification, module documentation, architecture metadata, and Cloud Build
  checks for the declaration module.
- [x] Measure the graph before updating its baseline. Reject any reverse edge,
  upper-layer dependency, cycle, undeclared edge, compatibility exception, or
  expansion into admission and runtime behavior.
- [x] Run focused package, compatibility, schema, governance, replay, host, and
  runtime checks; then run the exact deterministic Cloud Build selections,
  architecture ratchet, fresh isolated distribution verification, and full
  qualification ladder.

Cut exit condition:

- [x] Governed declaration and policy normalization have one independently
  buildable owner; semantic vocabulary remains below governance; YAML and
  artifact adapters remain outside; admission, current-use, authority, host,
  runtime, controller, LLM, and workstation behavior have not moved; and all
  historical names preserve exact compatibility.

Cut 7 qualification evidence:

- [x] Record pre-cut source hash, differential count, focused and deterministic
  test counts, distribution counts, graph changes, qualification status, and
  the disposition of A4.7.1 through A4.7.7.

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase4-governance-declarations.py`, SHA-256
  `7b4a133826f2b02e8039ab513f2fe93e1baa6055047a6e2beda9c9c8ce8cd207`.
  An independently loaded old/new differential passed 7,721 checks across
  function signatures, public constants, schema, kind, declaration, and
  executor combinations, every required and authority-bound field in absent,
  empty, malformed, and valid forms, policy schemas, kinds, and values, exact
  policy failures, the complete four-way summary input cross-product, exact
  return values, and exact exception types and messages.
- [x] The governance package passed 61 tests. Focused declaration, API,
  distribution, compatibility, schema, and metadata checks passed 109 tests;
  broader replay, hygiene, learning, host-mediation, run-bundle, invocation,
  and IR checks passed 79 tests. The exact deterministic Cloud Build selections
  passed 473 architecture/core tests and 100 BDD/UI tests.
- [x] Fresh isolated distributions contained 16 governance-wheel entries and
  36 governance-sdist entries, including the declaration owner and package
  tests. The engine wheel remains at 91 entries with all 77 declared canonical
  modules. Isolated verification preserved historical identities, exercised
  declaration and policy normalization through extracted wheels, and created
  SQLite and runtime state through the packaged CLI.
- [x] The accepted graph has 28 components, 126 owned root modules, 3 owned root
  package families, 78 package edges, 571 grandfathered observations, and zero
  cycles, undeclared edges, or forbidden edges. The declared
  `core_governance -> skill_semantics` package edge replaces the obsolete
  `skill_schema_io -> skill_governance` root observation; the combined graph
  remains at 631 edges without adding a wildcard export, compatibility
  exception, facade reclassification, reverse dependency, or cycle.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Refreshed gates include 778 root
  tests, 603 workstation tests with one expected skip, 3 skill-routing BDDs,
  34 publication BDDs, the incremental publication BDD, publication reference
  capture, Flutter analysis, and all Flutter widget tests; six accepted
  live/provider/browser/trial gates were retained through the declared
  baseline merge. Restricted execution first confirmed that the only failures
  were denied LLM, home-directory, socket, and Flutter-cache capabilities; the
  exact failed gates then passed with their declared host capabilities.
  Candidate and promoted baseline are byte-identical at SHA-256
  `2c08a1f2aa006deb9896c4902a50a5dd0415f7fb6dbcfc7360fad0aa7cdace57`.
- [x] A4.7.1 through A4.7.7 held without qualification. The package owns only
  normalization of already decoded governed declarations and policies plus a
  reviewable policy summary. YAML parsing, artifact synthesis, virtual mounts,
  broker and Python inspection, inventory, persistence, admission, current-use
  checks, authority, execution, controller, LLM, and workstation behavior
  remain with their existing adapters and orchestrators.

#### Phase 4 Cut 8 - Policy And Approval Admission Evaluation

Measured scope and falsifiable assumptions:

- [x] **A4.8.1:** Confirm that admission evaluation over an already normalized
  governed declaration and supplied policy and approval records is one
  deterministic governance operation. If evaluation requires artifact
  retrieval, persistence, broker discovery, Python source inspection, current
  use, authority issuance, execution, controller state, or workstation state,
  stop and keep those responsibilities outside the package.
- [x] **A4.8.2:** Confirm that structural titled-record views are sufficient for
  policy and approval evaluation. The package must not import the concrete
  root `Artifact`, a store, a controller, a workstation module, or an
  application-composition service.
- [x] **A4.8.3:** Treat admission time as an injected dependency. Preserve the
  historical timestamp shape and exact call point while keeping the root clock
  and environmental time ownership outside the portable governance operation.
- [x] **A4.8.4:** Preserve policy iteration order, rationale ordering, policy
  title ordering, status and result shape, approval matching, and exact
  exception behavior. A semantically similar but differently ordered or
  worded decision rejects the cut.
- [x] **A4.8.5:** Preserve the historical root guard order. No-policy and
  executable-authority checks, broker stability checks, and Python source and
  data-surface inspection must complete before the root orchestrator delegates
  policy and approval evaluation to the package.
- [x] **A4.8.6:** Keep historical `evaluate_skill_admission` root-owned and
  protocol-zero pickle-resolvable because it remains the host-aware
  orchestrator. Do not migrate consumers or misrepresent that orchestration as
  a compatibility alias during this cut.
- [x] **A4.8.7:** Accept no new dependency edge, cycle, exception, wildcard
  surface, or upward import. Only package-owned file inventories and generated
  reports may change in the measured architecture graph.
- [x] Capture the complete pre-cut `skill_governance.py` independently as
  `/tmp/realized-pre-phase4-policy-admission.py`, SHA-256
  `40004cd8936e3f6788350b8028268249f163cb31a3ce730c9982b02fdd288a93`,
  so the historical operation can be loaded and exercised independently.
- [x] Add package-owned `admission` to `realized-core-governance`, accepting a
  normalized declaration, titled policy and approval views, and an injected
  clock while importing only lower semantic and governance modules.
- [x] Keep no-policy and executable-authority guards, broker stability checks,
  Python source and data-surface inspection, artifact adaptation, current-use
  composition, and authority issuance in their existing owners.
- [x] Delegate from the historical root orchestrator only after its host
  preflight checks pass, preserving the public signature and exact output and
  failure behavior.
- [x] Add package tests for allowed, denied, and approval-required decisions,
  policy and rationale order, matching and non-matching approvals, structural
  views, injected time, malformed values, exact failures, and root/package
  composition.
- [x] Add compatibility coverage proving package ownership of the portable
  evaluator while the historical root orchestrator remains root-owned and
  pickle-resolvable.
- [x] Extend package API, import hygiene, wheel/sdist contents, isolated-wheel
  verification, module documentation, Cloud Build, and distribution checks for
  the admission module.
- [x] Measure the graph before accepting generated report changes. Reject any
  package edge, root observation, cycle, undeclared dependency, compatibility
  exception, or unrelated baseline movement.
- [x] Run the governance package, focused compatibility and skill-I/O checks,
  broader runtime-facing checks, exact deterministic Cloud Build selections,
  architecture ratchet, fresh isolated distribution verification, and the
  complete qualification ladder.

Cut exit condition:

- [x] Deterministic policy and approval evaluation over supplied records has
  one independently buildable governance owner. The root admission function
  remains the historical host-aware orchestrator; host preflight, persistence,
  current-use authorization, authority grants, runtime, controller, LLM, and
  workstation behavior have not moved, and observable admission behavior is
  unchanged.

Cut 8 qualification evidence:

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase4-policy-admission.py`, SHA-256
  `40004cd8936e3f6788350b8028268249f163cb31a3ce730c9982b02fdd288a93`.
  An independently loaded old/new differential passed 59,724 exact checks
  across kind, executor, authority, risk, approval, data, side-effect, policy,
  approval-record, content, broker, and Python-source combinations. It compared
  exact return values and exact exception types and messages with a fixed clock.
- [x] The complete governance package passed 71 tests. Focused compatibility,
  skill-I/O, and metadata checks passed 95 tests; the broader function-boundary,
  host-mediation, run-bundle, replay, compiler, composition, invocation, and IR
  slice passed 107 tests. The exact deterministic Cloud Build selections passed
  483 architecture/core tests and 101 BDD/UI tests.
- [x] Fresh isolated distributions contained 17 governance-wheel entries and
  38 governance-sdist entries, including the admission owner and package tests.
  The engine wheel remains at 91 entries with all 77 declared canonical
  modules. Isolated verification exercised package evaluation and exact
  historical root/package composition equivalence, then created SQLite and
  runtime state through the packaged CLI.
- [x] The accepted graph remains unchanged at 28 components, 126 owned root
  modules, 3 owned root package families, 78 package edges, 571 grandfathered
  observations, and 631 combined edges, with zero cycles, undeclared edges, or
  forbidden edges. No dependency baseline update was required.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Fresh gates include 779 root
  tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs, the
  incremental publication BDD, publication reference capture, Flutter
  analysis, and all Flutter widget tests. The ten package-local admission tests
  are included in the separately run 71-test governance suite rather than the
  root-discovery count. Six accepted live/provider/browser/trial gates were
  retained through the declared baseline merge. Candidate and promoted
  baseline are byte-identical at SHA-256
  `9be8e7af44b539339fe369e4c80d63c39a8cb8175d8d53d9b705f0ce14fc37e7`.
- [x] A4.8.1 through A4.8.7 held without qualification. The package owns only
  policy and approval evaluation over supplied normalized values and an
  injected clock. Host inspection, artifact retrieval, persistence,
  current-use checks, authority issuance, execution, controller, LLM, and
  workstation behavior remain with their existing adapters and orchestrators.

### Phase 5 - Make The LLM Boundary Package-Native

- [ ] Confirm A18 by tracing every model call, prompt builder, planner, renderer,
  supplement helper, cache, and provider adapter.
- [ ] Keep provider-neutral planning and rendering contracts in
  `realized-core-llm` or another explicitly justified LLM-owned package.
- [ ] Keep controller-specific semantic reduction policy in the controller,
  passing only bounded planning requests and advisory results across the LLM
  boundary.
- [ ] Keep workstation conversational lifecycle and session projections in the
  workstation, with provider calls behind an injected LLM port.
- [ ] Move root-hosted LLM implementation only after separating provider
  mechanics from controller, governance, persistence, and CLI concerns.
- [ ] Ensure model caches contain provider optimization state only and cannot
  substitute for persisted conversation, reduction, or resumption state.
- [ ] Require typed parsing and validation before model output can become a
  proposal considered by controller or workstation logic.
- [ ] Preserve LLM-off operation for mechanically decidable paths.
- [ ] Add provider-neutral contract tests, invalid-output tests, cache-isolation
  tests, and tests proving that advisory output cannot bypass governance or
  mechanical realizer binding.
- [ ] Build and exercise the LLM package independently from controller and
  workstation implementations.

Exit condition:

- [ ] All model calls and prompt/rendering contracts have explicit LLM-layer
  ownership, and no model or cache carries authoritative application state.

### Phase 6 - Complete Runtime And Realizer Ownership

- [ ] Define the callable provider/realizer registration ABI that is still open
  in the six-layer plan.
- [ ] Represent advertised executor support separately from an installed
  ability and from an invocation-scoped authority grant.
- [ ] Require exact mechanical binding from an admitted ability declaration to
  a registered executor or broker identity.
- [ ] Make provider availability and runtime prerequisites inspectable before
  invocation.
- [ ] Assign capability grants, execution frameworks, broker dispatch, host
  mediation, Wasm execution, child-runtime hosting, and execution receipts to
  explicit runtime owners.
- [ ] Keep attachment resolution, delegated-rights narrowing, shared host
  actions, and generic receipt shaping in `realized-host-interaction` only where
  they remain backend-neutral.
- [ ] Keep ability admission and lifecycle in governance.
- [ ] Keep request-to-ability semantic matching in controller/retrieval.
- [ ] Keep workstation approval UX and session state in workstation.
- [ ] Extract reusable skill invocation mechanics from workstation only after
  separating workstation-specific discovery, presentation, and session policy.
- [ ] Inject concrete providers at entry/composition boundaries; do not add a
  global mutable registry hidden inside the runtime.
- [ ] Add end-to-end tests for definition, admission, subject visibility,
  semantic selection, exact realizer binding, authority grant, execution,
  result projection, and receipts.
- [ ] Add negative tests for unavailable realizers, mismatched executors,
  undeclared brokers, denied authority, and a semantically similar but wrong
  ability.

Exit condition:

- [ ] The complete ability journey respects all three distinct bindings:
  subject-to-ability, request-to-ability, and ability-to-realizer.
- [ ] Controller and workstation can use injected realizers without importing
  one another or relying on undeclared root implementation modules.

### Phase 7 - Make The Subject Lifecycle Package-Native

- [ ] Confirm A8 against actual identity, provenance, persistence, and consumer
  boundaries.
- [ ] Make `workstation.subject.core` the canonical owner of the subject
  lifecycle unless the cohesion check proves that an independent subdomain is
  required.
- [ ] Organize learning context, Gather, Itemize, Decision Review, Review, and
  Publication as internal domain modules rather than separate UV projects by
  default.
- [ ] Move subject value models and invariants before orchestration and
  persistence adapters.
- [ ] Move learning-context and source-ingestion behavior while preserving
  corpus paths, delta semantics, projection rules, and provenance.
- [ ] Move itemization extraction and validation while preserving stable item
  identities and freshness behavior.
- [ ] Move decision-frame, review-item, policy, and analysis projection behavior
  while preserving the distinction between coordinated transformation and
  runtime semantic reduction.
- [ ] Move review composition without making presentation state the source of
  truth.
- [ ] Move publication models, validation, projection, deterministic build, and
  render-artifact tracking while preserving publication's optional and
  non-truth-bearing role.
- [ ] Keep subject application services in `workstation.subject.service` and UI
  adapters outside the domain owner.
- [ ] Replace package-to-root subject imports with canonical subject-domain
  imports, one workflow stage at a time.
- [ ] Leave root subject modules as compatibility facades through at least one
  full Gather-to-Publication qualification cycle.
- [ ] Run direct-v10, v2-to-v10, incremental, decision-oriented, non-decision,
  blocked-analysis, preview, build, and publication BDD paths after every stage
  cut.

Exit condition:

- [ ] The subject workflow package can be installed and tested without loading
  canonical learning, itemization, review, or publication implementations from
  repository root.

### Phase 8 - Give Blend A Canonical Domain Boundary

- [ ] Confirm A9 by mapping each Blend theory layer to an owner and dependency
  direction.
- [ ] Define public contracts for context, operators, sessions, worlds,
  workflows, history, coordination, and execution observations.
- [ ] Keep presentation derivation outside the Blend domain.
- [ ] Keep concrete skill execution and host effects behind runtime ports.
- [ ] Keep event transport outside the Blend truth model; events describe
  accepted lifecycle transitions rather than becoming the authoritative state.
- [ ] Confirm A19 for every workflow and step event before moving its producer
  or consumer.
- [ ] Replace direct dependencies on workstation model types with explicit
  adapters at the workstation boundary.
- [ ] Move dependency-light Blend models first.
- [ ] Move stores behind persistence ports while preserving identifiers,
  ordering, and on-disk formats.
- [ ] Move workflow/operator resolution and execution orchestration only after
  their runtime and governance dependencies are explicit.
- [ ] Migrate foundation projections and workstation runtime consumers to the
  canonical Blend API.
- [ ] Preserve root Blend imports as compatibility facades during qualification.
- [ ] Add tests for context applicability, operator resolution, workflow
  branching, iteration, halt behavior, lifecycle observations, persistence,
  replay, and receipt/event ordering.

Exit condition:

- [ ] Blend can be reasoned about and tested as a domain independent of
  workstation UI and shell implementation.

### Phase 9 - Make The Controller Engine Source-Native

- [ ] Recompute the `core_engine/module_manifest.txt` closure after the semantic,
  skill, governance, LLM, runtime, subject, and Blend ownership phases.
- [ ] Classify every remaining module as controller semantics, controller state,
  a controller adapter, entry/exchange, compatibility, or an unresolved foreign
  responsibility.
- [ ] Stop and extract any unresolved foreign responsibility before moving the
  controller closure.
- [ ] Move recursive `Not` reduction, decomposition, reuse, closure, reflection,
  contemplation, commitment, resumption coordination, and controller-owned
  state under `realized_core_engine`.
- [ ] Keep runtime execution behind runtime ports, governance behind governance
  APIs, model calls behind LLM ports, and persistence behind repository ports.
- [ ] Move the plain-SQLite adapter only if its dependency direction remains
  inward toward controller contracts; otherwise keep it as a composition
  adapter.
- [ ] Preserve the typed `run`, `resume`, and `inspect` ABI.
- [ ] Replace root canonical modules with compatibility facades in small
  clusters and verify identity after each cluster.
- [ ] Remove custom root-module copying from `core_engine/setup.py` only after
  the canonical package owns the complete required closure.
- [ ] Remove `module_manifest.txt` only after wheel and sdist builds derive
  exclusively from package-owned source and compatibility requirements are
  represented elsewhere.
- [ ] Verify LLM-off reduction, LLM-assisted reduction, interruption,
  augmentation, redirection, realignment, branching, replay, and resumed
  execution against the accepted baseline.

Exit condition:

- [ ] `realized-core-engine` builds from its own canonical source tree and has no
  production dependency on repository-root implementation modules.

### Phase 10 - Converge Entry, Exchange, And Root Composition

- [ ] Make `realized-core` and workstation application packages the supported
  composition and launch surfaces.
- [ ] Keep `main.py` only as a historical executable/import facade while it is
  supported.
- [ ] Assign skill YAML hydration, compatibility import/export, bundle I/O,
  run-bundle I/O, and schema translation to explicit entry/exchange adapters.
- [ ] Ensure exchange adapters translate representations but do not decide
  admission, authority, semantic commitment, or execution policy.
- [ ] Move reusable validation infrastructure under a validation package or
  `scripts/` only if it is not a supported runtime API.
- [ ] Keep standalone trials as entry programs rather than forcing them into
  production packages.
- [ ] Remove root composition reach-through from nested runtime and workstation
  code.
- [ ] Require all production package-to-package dependencies to be declared in
  project metadata and in the architecture manifest.

Exit condition:

- [ ] Root production code consists only of deliberate launch facades,
  compatibility facades, and explicitly classified validation/trial entrypoints.

### Phase 11 - Retire Compatibility Paths Deliberately

- [ ] Produce a machine-readable inventory of every remaining compatibility
  facade and its consumers.
- [ ] Confirm that canonical production code never imports a compatibility
  facade.
- [ ] Confirm that documentation and examples use only canonical APIs.
- [ ] Confirm that all independently shipped distributions install and run
  without repository-root imports.
- [ ] Complete at least one stable qualification cycle after the final consumer
  migration.
- [ ] Announce or document removals for any facade that has become part of a
  supported external surface.
- [ ] Remove facades in separate changes from canonical implementation moves.
- [ ] Refresh the architecture baseline after each removal so the ratchet makes
  the improvement irreversible.

Exit condition:

- [ ] The root-boundary ledger contains no canonical package-to-root
  implementation edges and only approved entry or compatibility edges remain.

### Required Gates For Every Slice

- [ ] The architecture checker reports no new cycle, undeclared dependency,
  forbidden dependency, wildcard export, or expanded compatibility edge.
- [ ] The moved package passes isolated wheel and source-distribution tests with
  the repository root absent from `sys.path`.
- [ ] Old-path/new-path import identity tests pass while compatibility is
  retained.
- [ ] Unit and contract tests for the moved responsibility pass.
- [ ] All affected BDD paths and trials pass with exact action/state semantics.
- [ ] SQLite schemas and representative persisted values remain readable.
- [ ] Artifact, receipt, event, report, and run-bundle comparisons remain
  equivalent apart from explicitly approved nondeterministic fields.
- [ ] LLM-off behavior passes whenever the responsibility is mechanically
  decidable.
- [ ] Provider-backed behavior passes when the moved boundary includes model
  integration.
- [ ] Flutter and Textual behavior pass when a workstation-facing contract is
  affected.
- [ ] Performance remains within the agreed tolerance or the slice is held for
  explicit review.
- [ ] Documentation, package metadata, architecture controls, and generated
  dependency reports describe the same ownership model.

### Program Completion Criteria

- [ ] Every theory-defined operational responsibility has one canonical owner.
- [ ] Every UV project has a narrow public API and independently declared
  dependencies.
- [ ] Every independently shipped wheel and sdist is self-contained for its
  declared responsibility.
- [ ] No canonical package imports repository-root implementation code.
- [ ] Governance, controller, runtime/skill execution, LLM, workstation, and
  entry/exchange dependency directions conform to the six-layer architecture.
- [ ] Semantic values shared across boundaries are dependency-light contracts,
  not leaked implementation objects.
- [ ] Portable skill meaning is independent from governance decisions, runtime
  realization, exchange encodings, and workstation presentation.
- [ ] The LLM layer owns model interaction without owning causal application
  state or mechanical decisions.
- [ ] The ability journey preserves separate admission, scope, semantic
  matching, realizer binding, authority, execution, and receipt stages.
- [ ] The subject lifecycle and Blend each have coherent, testable owners.
- [ ] `realized-core-engine` is source-native and no longer assembled by copying
  canonical root modules.
- [ ] Remaining root Python files are intentional entrypoints, validation/trial
  programs, or time-bounded compatibility facades.
- [ ] Compatibility removals occur only after a stable qualification cycle.
- [ ] The architecture ratchet enforces the completed topology with no
  grandfathered canonical package-to-root implementation dependencies.

### Explicit Non-Goals For This Program

- [ ] Do not create one UV project per Python file.
- [ ] Do not treat directory movement as proof of a boundary.
- [ ] Do not rename theory terms while relocating implementation.
- [ ] Do not redesign workflow logic, UI behavior, storage formats, or model
  prompts in a source-movement change.
- [ ] Do not centralize unrelated helpers in a generic common package.
- [ ] Do not make governance depend on controller, runtime, LLM, workstation,
  or entry implementation.
- [ ] Do not make the runtime choose abilities or admit them.
- [ ] Do not make the host-interaction substrate own workstation sessions or
  governance policy.
- [ ] Do not remove compatibility paths merely to make the tree appear clean.
- [ ] Do not update the architecture baseline to hide a regression.
