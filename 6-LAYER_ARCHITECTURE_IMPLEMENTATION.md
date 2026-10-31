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
allowed capability names, and an immutable `HostRealizerProvider`. The provider
ABI exposes exact executor and broker identities, inspectable prerequisites,
and callable dispatch without importing workstation or application
implementations into the shared substrate.

The boundary now keeps three independent facts separate:

- an ability is installed and admitted by governance
- an admitted ability is visible in a subject/controller scope and selected for
  a request
- the application host supplies the exact declared executor and broker
  realizers needed for one invocation

Runtime mediation preflights exact declaration-to-realizer binding and runtime
prerequisites before issuing invocation grants. Concrete host and workstation
providers are assembled at composition boundaries; there is no mutable global
provider registry. Python child execution uses an invocation-scoped,
authenticated parent bridge so the parent rechecks declaration, admission,
authority, and ABI arguments before dispatching a broker operation.

## Next Convergence Cut

Goal:
- make the subject lifecycle package-native without changing workflow behavior,
  persisted formats, action labels, or UI contracts
- first invert the remaining concrete subject-core dependencies on workstation
  runtime/session and host-capture implementations
- only then move the root subject-domain implementation into
  `workstation.subject.core` in dependency-safe slices

The actual combined dependency graph disproves a values-first relocation while
`subject_core` still imports `runtime_core` and `foundation_host`: converting
their root subject dependencies into facades at that point would close package
cycles. Phase 7 therefore begins with dependency inversion, not file movement.

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

- [x] **A8 - The subject lifecycle is one cohesive domain with internal
  stages.** Validate that learning context, Gather, Itemize, Decision Review,
  Review, and Publication share subject identity, provenance, and persistence
  invariants. If Publication or another stage has independent consumers and a
  genuinely separate lifecycle, use an internal package boundary first and
  graduate it to a UV project only after that independence is demonstrated.

  Validation found one subject identity and corpus root carried from source
  admission through itemization, decision review, review composition, and
  optional publication. Each later stage preserves or projects the same
  provenance and snapshot identities; no stage has an independently admitted
  aggregate or external consumer lifecycle that justifies another UV project.

- [x] **A9 - Blend is a domain model below workstation presentation.** Validate
  that context, operator, session, world, workflow, history, and coordination
  can be represented without importing workstation UI, shell, or session
  implementation types. If workstation-specific state is intrinsic rather than
  adapted, define the missing Blend contract before extracting implementation.

  Validation produced one independently buildable Blend domain containing
  context, operator, session, world, workflow, history, coordination, and
  observation contracts. Workstation sessions are translated through
  `workstation.runtime.core.blend_adapters`; UI and shell types do not enter the
  domain, while concrete composition, invocation, persistence, and event
  publication remain behind outward ports and adapters.

- [x] **A10 - The controller can become source-native after lower concerns are
  extracted.** Validate the remaining `core_engine/module_manifest.txt` closure
  after semantic contracts, governance, and runtime realization have owners. If
  the closure still mixes unrelated domains, continue extracting those domains
  rather than moving the mixed graph wholesale under `realized_core_engine`.

  Validation classified the residual closure after the semantic, governance,
  runtime, subject, and Blend cuts. Controller state, reduction, retrieval,
  closure, host mediation, replay/resumption coordination, and the plain-SQLite
  repository adapter now have one package-native owner. Entry/exchange and
  subject extensions remain outside the engine and are attached only at outer
  composition boundaries. The engine distribution is built directly from its
  source tree without a root-module manifest or copy step.

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

- [x] **A14 - LLM output is advisory and cannot own causal identity,
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

- [x] **A18 - The LLM layer can remain advisory and provider-isolated.** Validate
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

The ownership inventory includes top-level package families that are not yet UV
projects: `dst` belongs to the subject domain, while `design` is a
validation/trial package. Their imports participate in the same combined-cycle
and shrinking-edge ratchets as root modules and UV workspace components.
`coordinated_transformation` began in that inventory and graduated to a
dependency-free workspace component in Phase 7 Cut 9.

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
- `coordinated_transformation` is a dependency-free subject-domain workspace
  component with an explicit package API and independently qualified wheel and
  sdist. `dst` remains a cohesive top-level subject-domain package family and is
  not self-contained because it imports repository-root modules in addition to
  the declared CTFS component. Preserve both import ABIs while the remaining
  subject-domain consumers move in reverse-topological cuts.
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

- [x] Define a governance public API for declaration validation, admission,
  approval, authority evaluation, lifecycle state, revocation, incidents,
  current-use checks, data policy, and trace requirements.
- [x] Define dependency-inverted ports for governance inventory and persistence.
- [x] Keep CLI parsing, YAML parsing, LLM prompting, controller reduction,
  workstation session handling, and host execution outside governance.
- [x] Move dependency-light governance primitives and lifecycle rules first.
- [x] Move approval and authority evaluation after their inputs and outputs are
  represented by governance-owned contracts.
- [x] Move skill governance, safety overlays, and current-use checks without
  moving skill execution into governance.
- [x] Move data governance without moving virtual filesystem or SQLite adapter
  mechanics into governance.
- [x] Adapt the existing SQLite store through governance ports rather than
  allowing the governance package to import application composition.
- [x] Migrate controller, skills, and workstation consumers one at a time, and
  confirm that subject packages have no direct governance consumer to migrate.
- [x] Preserve root governance imports as identity-preserving facades during
  qualification.
- [x] Add deny-by-default, held, inactive, rejected, revoked, expired,
  denied-authority, and incident-overlay contract tests; confirm that
  `superseded` is a learning/resumption relation rather than inventing it as a
  governed-skill lifecycle state.
- [x] Verify that semantic similarity cannot override lifecycle or authority
  decisions.

Exit condition:

- [x] Governance is independently testable and importable without controller,
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

#### Phase 4 Cut 9 - Final Current-Use Eligibility

Measured scope and falsifiable assumptions:

- [x] **A4.9.1:** Confirm that final current-use eligibility over a supplied
  schema version, admission record, and already-composed effective lifecycle is
  one deterministic governance operation. If it requires artifact retrieval,
  policy recomputation, safety-record discovery, persistence, host inspection,
  authority issuance, execution, controller state, or workstation state, stop
  and leave those responsibilities outside the package.
- [x] **A4.9.2:** Preserve the legacy-v1 compatibility bypass as a terminal
  decision. Admission and lifecycle state must not be inspected for a legacy
  schema, and unsupported schemas must retain their exact failure behavior.
- [x] **A4.9.3:** Preserve deny-by-default governed admission behavior, status
  normalization, rationale normalization, fallback messages, lifecycle gate
  precedence, exact denial messages, and exact exception behavior.
- [x] **A4.9.4:** Preserve the historical root short-circuit order. A missing,
  held, rejected, or governance-record admission must return before lifecycle
  projection or safety-overlay composition is attempted.
- [x] **A4.9.5:** Keep concrete artifact adaptation, current policy and approval
  recomputation, effective-lifecycle projection, and revocation/incident overlay
  assembly in the historical root adapter. The package consumes only supplied
  values and does not discover governance state.
- [x] **A4.9.6:** Keep `artifact_current_use_admission`,
  `artifact_admitted_for_use`, and
  `artifact_admitted_for_use_with_governance` root-owned and protocol-zero
  pickle-resolvable. Current-use eligibility is not an authority grant and must
  not move capability issuance or execution into governance.
- [x] **A4.9.7:** Accept no new dependency edge, cycle, baseline exception,
  wildcard surface, or upward import. A file-level observation on an existing
  declared edge is acceptable only when the generated report and measured
  graph otherwise remain unchanged.
- [x] Capture the complete pre-cut `skill_governance.py` independently as
  `/tmp/realized-pre-phase4-current-use.py`, SHA-256
  `cfc4c31fe4658a9b9c2a5efc9b8dabbd3818d670ba8b34cb9e7580935c81892f`,
  so the historical adapter can be loaded and exercised independently.
- [x] Add package-owned `current_use` to `realized-core-governance`, exposing a
  staged admission gate and final admission-plus-lifecycle decision over
  supplied values only.
- [x] Delegate from the historical root artifact adapter while preserving its
  compatibility signature, legacy bypass, admission short-circuit, lifecycle
  and safety assembly, return values, failures, and call order.
- [x] Add package tests for legacy compatibility, missing and non-admitted
  records, rationale normalization, malformed values, exact failures, terminal
  short-circuiting, and lifecycle denial precedence.
- [x] Add compatibility coverage proving package ownership of the portable
  rules while the three historical artifact-facing functions remain root-owned
  and pickle-resolvable.
- [x] Extend package API, metadata, import hygiene, wheel/sdist contents,
  isolated-wheel verification, module documentation, Cloud Build, and
  distribution checks for the current-use module.
- [x] Regenerate only the deterministic dependency report after confirming the
  baseline graph is unchanged; do not update the dependency baseline.
- [x] Run the governance package, independently loaded old/new differential,
  focused root integration, exact deterministic Cloud Build selections,
  architecture ratchet, fresh isolated distribution verification, and complete
  qualification ladder.

Cut exit condition:

- [x] Final current-use eligibility over supplied governance state has one
  independently buildable governance owner. Artifact retrieval and adaptation,
  re-admission, safety-state discovery, persistence, authority grants, runtime,
  controller, LLM, and workstation behavior have not moved, and observable
  current-use behavior is unchanged.

Cut 9 qualification evidence:

- [x] The pre-cut source is preserved at
  `/tmp/realized-pre-phase4-current-use.py`, SHA-256
  `cfc4c31fe4658a9b9c2a5efc9b8dabbd3818d670ba8b34cb9e7580935c81892f`.
  An independently loaded old/new differential passed 3,405 exact checks across
  schema, admission, rationale, lifecycle, safety-overlay, and malformed-content
  combinations. It compared exact return values, exact exception types and
  messages, and adapter call order.
- [x] The complete governance package passed 78 tests. Focused skill-I/O,
  host-mediation, compatibility, function-boundary, and invocation integration
  passed 167 tests. The exact deterministic Cloud Build selections passed 490
  architecture/core tests and 102 BDD/UI tests.
- [x] Fresh isolated distributions contained 18 governance-wheel entries and
  40 governance-sdist entries, including the current-use owner and package
  tests. The engine wheel remains at 91 entries with all 77 declared canonical
  modules. Isolated verification exercised legacy, inactive, and missing-
  admission decisions, then created SQLite and runtime state through the
  packaged CLI.
- [x] The accepted graph remains unchanged at 28 components, 126 owned root
  modules, 3 owned root package families, 78 package edges, 571 grandfathered
  observations, and 631 combined edges, with zero cycles, undeclared edges, or
  forbidden edges. The generated report adds `current_use.py` only to the
  existing declared `core_governance -> skill_semantics` edge; no dependency
  baseline update was required.
- [x] The full qualification baseline records 15 passing gates, zero failures,
  zero blocked gates, and zero gates not run. Fresh gates include 780 root
  tests, 603 workstation tests, 3 skill-routing BDDs, 34 publication BDDs, the
  incremental publication BDD, publication reference capture, Flutter
  analysis, and all Flutter widget tests. The seven package-local current-use
  tests are included in the separately run 78-test governance suite rather than
  root discovery. Six accepted live/provider/browser/trial gates were retained
  through the declared baseline merge. Candidate and promoted baseline are
  byte-identical at SHA-256
  `626fd39cf9acfe9beac3327e0a17253edf18f6caf44da8fd5d3bcfe0bd17c89f`.
- [x] A4.9.1 through A4.9.7 held without qualification. The package owns only
  deterministic final eligibility over supplied schema, admission, and
  effective lifecycle values. Artifact and safety-state assembly, current
  re-admission, host inspection, persistence, authority issuance, execution,
  controller, LLM, and workstation behavior remain with their existing owners.

#### Phase 4 Cut 10 - Governance Persistence Ports

Measured scope and falsifiable assumptions:

- [x] **A4.10.1:** Confirm that governance installation depends on only two
  storage capabilities: loading the complete artifact inventory and persisting
  one already-prepared artifact batch with a run identifier. If installation
  requires transactions, schema management, connection ownership, indexing,
  serialization, search, or cache policy to cross into governance, stop and
  leave those mechanics in the existing store owner.
- [x] **A4.10.2:** Confirm that the writer boundary can treat each artifact as an
  opaque generic value. Governance must not acquire the concrete root
  `Artifact`, mutate values inside the persistence module, or prescribe the
  persistence representation.
- [x] **A4.10.3:** Preserve the exact four installation batches and their order:
  policy, approval, safety, and skill. Preserve the exact run identifiers,
  artifact iterable identity, report object identity, exception propagation,
  and all caller-side timing and summary behavior.
- [x] **A4.10.4:** Keep the existing inventory reader and the new artifact writer
  as separate structural ports. A consumer may implement either capability
  independently; the governance package must not require a concrete combined
  repository object.
- [x] **A4.10.5:** Adapt both current root stores structurally. Do not introduce
  a wrapper that duplicates `ArtifactStore` or `SQLiteVectorArtifactStore`, and
  do not change either store's methods, database layout, fallback behavior, or
  write semantics.
- [x] **A4.10.6:** Keep compilation, artifact-content updates, admission,
  lifecycle synthesis, installed-state discovery, normalized export, CLI
  output, and batch orchestration in the root installation adapter. This cut
  establishes dependency inversion; it does not move installation policy or
  implement a governance repository.
- [x] **A4.10.7:** Accept no new dependency edge, cycle, baseline exception,
  wildcard surface, or upward import. A package-local standard-library-only
  port and a root-to-existing-package import are acceptable only if the
  measured graph remains unchanged.
- [x] Preserve the complete pre-cut installer independently as
  `/tmp/realized-pre-phase4-persistence-port.py`, SHA-256
  `b6f2a68c7873c5f84c730c822112dc0de2f171916a4a4e3af1711eb2759d039d`.
- [x] Add package-owned `persistence` with the runtime-checkable generic
  `GovernanceArtifactWriter` protocol and exact `persist_governed_artifacts`
  forwarding seam.
- [x] Type the existing inventory loader against its structural reader port
  without changing its single-read, collection-identity, classification,
  ordering, or timing behavior.
- [x] Route all four existing installer batch writes through the writer port
  while preserving batch construction and all behavior around the write.
- [x] Add package contract tests for structural conformance, exact iterable and
  report identity, explicit and default run identifiers, and unchanged failure
  propagation.
- [x] Add root integration coverage proving that both current artifact-store
  implementations satisfy the inventory and persistence ports without an
  adapter class.
- [x] Extend the package API, metadata, module documentation, Cloud Build,
  wheel/sdist contents, and isolated-distribution smoke for the persistence
  port.
- [x] Regenerate only the deterministic dependency report after confirming the
  baseline graph is unchanged; do not update the dependency baseline.
- [x] Run an independently loaded pre/post differential, the complete
  governance and skill-I/O suites, exact deterministic Cloud Build selections,
  architecture ratchet, fresh isolated distribution verification, and the
  complete qualification ladder.

Cut exit condition:

- [x] Governance inventory reads and governed-artifact batch writes depend on
  explicit structural ports, and the existing stores are injected
  implementations. The package owns no database or installation orchestration,
  and observable installation and persistence behavior is unchanged.

Cut 10 qualification evidence:

- [x] An independently loaded old/new installer differential passed the normal
  policy-approval-safety-skill sequence and injected failures at both safety
  and skill batch boundaries. It compared exact return values, exceptions,
  store call order, run identifiers, artifact IDs, and normalized output after
  removing timing-only fields.
- [x] The complete governance package passed 82 tests and the complete skill-I/O
  suite passed 45 tests. The exact deterministic Cloud Build selections passed
  494 architecture/core tests and 103 BDD/UI tests. The initial sandboxed core
  selection denied child `uv` cache access in 11 execution tests; the unchanged
  selection passed completely with normal child-runtime access.
- [x] Fresh isolated distributions contained 19 governance-wheel entries and
  42 governance-sdist entries, including the persistence owner and its tests.
  The isolated smoke proved structural writer use, exact report and batch
  forwarding, package ownership, and the existing SQLite/runtime startup path.
- [x] The accepted graph remains unchanged at 28 components, 126 owned root
  modules, 3 owned root package families, 78 package edges, 571 grandfathered
  observations, and zero cycles, undeclared edges, or forbidden edges. The
  persistence module is standard-library-only, so no dependency-baseline update
  was required.
- [x] The assembled qualification record contains 15 passing gates with zero
  failures, blocked gates, or omitted gates. Fresh gates include 781 root tests,
  603 workstation tests with one expected skip, 3 skill-routing BDDs, 34
  publication BDDs, the incremental publication BDD, publication reference,
  Flutter analysis, and 51 Flutter widget tests. Six accepted live, browser,
  screenshot, and trial gates were retained through the declared baseline
  merge. Candidate and promoted baseline are byte-identical at SHA-256
  `286952a17b2403320c58e30c39596cfae25e726aa5cf932dfaadc58ecaa60b2c`.
- [x] A4.10.1 through A4.10.7 held without qualification. The package owns only
  the structural storage contracts and exact forwarding seam; concrete store,
  schema, transaction, serialization, indexing, installation, execution,
  controller, LLM, and workstation behavior remain in their existing owners.

#### Phase 4 Cut 11 - Invocation Authority Coverage

Measured scope and falsifiable assumptions:

- [x] **A4.11.1:** Separate authority coverage from runtime effect assembly.
  Governance may decide whether a supplied current-use result and supplied
  invocation grants cover a supplied required authority. It must not derive an
  authority from an effect kind, inspect a host, select an executor, issue a
  grant, dispatch an effect, or construct a runtime trace.
- [x] **A4.11.2:** Preserve denial precedence exactly: an artifact that is not
  currently admitted is denied first; an admitted request without a required
  authority mapping is denied second; a mapped authority without a matching
  grant is denied third; only a matching grant permits authority coverage.
- [x] **A4.11.3:** Treat authority and grant values as supplied governance
  facts. Preserve case-sensitive matching, grant order, duplicate grant IDs,
  empty-ID filtering, malformed mapping behavior, and the exact historical
  rationale strings.
- [x] **A4.11.4:** Keep effect-kind-to-authority mapping and executor-framework
  compatibility in runtime. The governance evaluator must remain portable and
  must not import capability runtime, executor normalization, host mediation,
  or any concrete artifact type.
- [x] **A4.11.5:** Keep `EffectDecision`, decision timestamps, grant issuance,
  trace construction, receipt correlation, host dispatch, and effect execution
  in their existing runtime owners. The package result is an immutable
  governance value consumed by those runtime operations, not their replacement.
- [x] **A4.11.6:** Route host mediation through the existing narrow runtime
  governance adapter rather than adding a new direct root-to-governance edge.
  If the architecture ratchet requires a new edge or exception, stop and revise
  the dependency route.
- [x] **A4.11.7:** Preserve historical runtime object ownership and serialized
  identity. No existing `EffectDecision` import path, pickle global, request
  shape, trace shape, or public host-mediation call signature may change.
- [x] Preserve the complete pre-cut authority evaluator independently as
  `/tmp/realized-pre-phase4-authority-evaluation.py`, SHA-256
  `dde80d0cbf5592ef425d59969388cbcd891747127c7786b7afc70d16bb13fb64`.
- [x] Add package-owned `authority` with immutable `AuthorityEvaluation` and
  deterministic `evaluate_authority_grants` over explicit effect, authority,
  current-use, reason, and grant inputs.
- [x] Keep the runtime-owned authority mapping before the package call and the
  runtime-owned executor-framework check after it. Convert the package result
  back into the existing runtime `EffectDecision` without changing timestamps,
  list shape, or rationale.
- [x] Expose the evaluator only through the existing runtime governance adapter
  to host mediation, and add a hygiene assertion that prevents host mediation
  from acquiring a direct governance-package import.
- [x] Add package contract tests for denial precedence, fallback admission
  rationale, absent authority mappings, missing grants, order and duplicates,
  case sensitivity, and malformed grant behavior.
- [x] Add compatibility tests proving package ownership of the new authority
  value and evaluator while preserving runtime ownership, import paths, and
  pickle resolution for `EffectDecision` and `evaluate_effect_request`.
- [x] Extend the package API, metadata, module documentation, Cloud Build,
  wheel/sdist contents, and isolated-distribution smoke for authority coverage.
- [x] Run an independently loaded old/new differential across admitted state,
  rationale, authority mapping, grant collections, effect kinds, executor
  declarations, requested executors, and malformed grants before accepting the
  cut.
- [x] Regenerate only deterministic reports and qualification evidence after
  confirming that no dependency edge, cycle, baseline exception, or package
  ownership rule changed.

Cut exit condition:

- [x] Invocation authority coverage has one deterministic governance owner over
  explicit inputs, while authority mapping, grant issuance, executor matching,
  runtime decisions, tracing, dispatch, and effects remain in runtime. Existing
  behavior and public runtime identities are unchanged.

Cut 11 qualification evidence:

- [x] The independently loaded old/new differential passed 3,240 cases and
  compared exact allow/deny values, rationale text, required authority, grant
  ID order, exception types, and exception messages. Only decision timestamps,
  which remain runtime-owned, were excluded.
- [x] The complete governance package passed 89 tests and the focused host
  mediation and function-boundary suites passed 69 tests. The exact
  deterministic Cloud Build selections passed 501 architecture/core tests and
  104 BDD/UI tests.
- [x] Fresh isolated distributions contained 20 governance-wheel entries and
  44 governance-sdist entries. The engine distribution exposed 77 canonical
  modules, and isolated authority, SQLite, and runtime-state smoke checks
  passed without repository imports.
- [x] The accepted graph remains unchanged at 28 components, 126 owned root
  modules, 3 owned root package families, 78 package edges, and 571
  grandfathered observations, with zero cycles, undeclared edges, or forbidden
  edges. No dependency-baseline update was required.
- [x] The assembled qualification record contains 15 passing gates with zero
  failures, blocked gates, or omitted gates. Fresh gates include 782 root tests,
  603 workstation tests with one expected skip, 3 skill-routing BDDs, 34
  publication BDDs, the incremental publication BDD, publication reference,
  Flutter analysis, and all 51 Flutter widget tests. Six accepted live,
  provider, browser, screenshot, and trial gates were retained through the
  declared baseline merge. Candidate and promoted baseline are byte-identical
  at SHA-256
  `f0c81c7ba67fe0eba5acedc081803075c6f051f54e84981e1b8f248fe89ca9dc`.
- [x] A4.11.1 through A4.11.7 held without qualification. Governance owns only
  authority coverage over supplied facts. Effect mapping, grant issuance,
  executor compatibility, `EffectDecision`, timestamps, tracing, dispatch,
  host execution, controller, LLM, and workstation behavior remain in their
  existing owners.

#### Phase 4 Cut 12 - Per-Effect Evidence Receipt Semantics

Measured scope and falsifiable assumptions:

- [x] **A4.12.1:** Treat the stable meaning of one per-effect evidence receipt
  as governance-owned while keeping trace capture and storage runtime-owned.
  The package may canonicalize already-supplied evidence and derive its receipt;
  it must not decide when an effect occurred, inspect runtime state, or append a
  trace to any sink.
- [x] **A4.12.2:** Confirm that the current receipt operation is pure and closed
  over a supplied kind and payload: recursively sort mapping entries, normalize
  keys, omit volatile identity/time fields, canonicalize historical admission
  status, project JSON-compatible values, hash canonical JSON, and return the
  versioned receipt value. If runtime or store state is required, stop.
- [x] **A4.12.3:** Preserve exact behavior for nested mappings, lists, tuples,
  dataclasses, enums, bytes, sets, falsey values, mixed key failures, malformed
  values, historical admission status, and all omitted fields. The migration
  must compare exception types and messages as well as successful values.
- [x] **A4.12.4:** Keep the constitutional replay signature and run-bundle
  receipt algorithms outside this cut. They intentionally emit different
  digest representations and omit different volatile fields; similar helper
  names do not establish one contract.
- [x] **A4.12.5:** Keep `record_effect_trace`, trace identifiers, timestamps,
  host ABI snapshots, request/decision/result projection, evidence selection,
  runtime state mutation, ledger recording, nested-trace ingestion, and effect
  dispatch in runtime.
- [x] **A4.12.6:** Route runtime use through the existing runtime-governance
  adapter. Host mediation must not acquire a direct governance-package import,
  and historical private helper names and the receipt-schema constant must
  remain available where current runtime code expects them.
- [x] **A4.12.7:** Accept no new dependency edge, cycle, baseline exception,
  serialized public class, persisted schema change, or observable trace-shape
  change. If the architecture graph changes, stop and explain the ownership
  consequence before updating any baseline.
- [x] Preserve the pre-cut host-mediation and runtime-governance implementations
  independently with content hashes before changing either file.
- [x] Add package-owned `trace` receipt vocabulary and deterministic receipt
  derivation over explicit inputs only.
- [x] Replace the runtime-local receipt algorithm with exact aliases supplied by
  the existing runtime-governance adapter, leaving trace assembly untouched.
- [x] Add package tests for canonicalization, volatile-field omission, status
  normalization, digest stability, collection handling, malformed inputs, and
  deterministic failure behavior.
- [x] Add compatibility and hygiene tests proving package ownership without
  changing runtime trace ownership or introducing an upward import.
- [x] Extend the package API, metadata, module documentation, Cloud Build,
  wheel/sdist contents, and isolated-distribution smoke for the receipt API.
- [x] Run independently loaded old/new differential coverage, focused runtime
  trace tests, complete governance tests, exact deterministic Cloud Build
  selections, architecture ratchet, isolated distributions, and the complete
  qualification ladder.

Cut exit condition:

- [x] Per-effect receipt meaning has one dependency-light governance owner,
  while runtime remains the sole owner of effect observation, trace assembly,
  persistence, dispatch, and execution. Existing traces are byte-for-byte
  equivalent after excluding runtime-generated timestamps and identifiers only
  where the existing qualification comparator already does so.

Cut 12 qualification evidence:

- [x] The preserved host-mediation and runtime-governance implementations have
  SHA-256 hashes
  `c0f4d7a4de3eca5a1d1be58b602f0ec97f80036d76a1d6d5849144b46639c706`
  and
  `d114d1fc902f0338b8ff50a9d1070d34e63ccfb3acff0d5fc4a0b6d28668702a`.
- [x] The independently loaded old/new differential passed 3,675 receipt cases
  with exact values and exact exception types and messages. It also passed 30
  complete `record_effect_trace` cases with exact return values, state appends,
  and ledger steps across allowed and denied decisions, status variants, and
  absent, failed, and successful results.
- [x] The receipt-focused API, distribution, compatibility, and hygiene suites
  passed 70 tests; the complete governance package passed 97 tests; and the
  focused host-mediation and function-boundary suites passed 69 tests. The
  exact deterministic Cloud Build selections passed 509 architecture/core
  tests and 105 BDD/UI tests.
- [x] Fresh isolated distributions contained 21 governance-wheel entries and
  46 governance-sdist entries. The engine distribution exposed 77 canonical
  modules, and the isolated receipt, SQLite, and runtime-state smoke checks
  passed without repository imports.
- [x] The accepted graph remains unchanged at 28 components, 126 owned root
  modules, 3 owned root package families, 78 package edges, and 571
  grandfathered observations, with zero cycles, undeclared edges, or forbidden
  edges. Only the deterministic dependency report changed; no dependency
  baseline update was required.
- [x] The assembled qualification record contains 15 passing gates with zero
  failures, blocked gates, or omitted gates. Fresh gates include 783 root tests,
  603 workstation tests with one expected skip, 3 skill-routing BDDs, 34
  publication BDDs, the incremental publication BDD, publication reference,
  Flutter analysis, and all 51 Flutter widget tests. Six accepted live,
  provider, browser, screenshot, and trial gates were retained through the
  declared baseline merge. Candidate and promoted baseline are byte-identical
  at SHA-256
  `4319fe40a5e893a2ed502e66065c72308247edabf54cc24db450c62e28b94bb5`.
- [x] A4.12.1 through A4.12.7 held without qualification. Governance now owns
  only deterministic receipt meaning over supplied values. Observation,
  evidence selection, trace assembly, identifiers, timestamps, host ABI
  snapshots, runtime mutation, ledger recording, nested-trace ingestion,
  persistence, dispatch, execution, constitutional replay, and run-bundle
  receipt behavior remain in their existing owners.

#### Phase 4 Cut 13 - Constitutional Effect Trace Requirements

Measured scope and falsifiable assumptions:

- [x] **A4.13.1:** Treat the stable replay-significant requirements of one
  already-supplied effect trace as governance-owned. The package may project a
  supplied trace into its constitutional effect signature; it must not capture
  state, assemble a trace, perform replay, or decide whether execution occurs.
- [x] **A4.13.2:** Confirm that `canonical_trace_answer` and
  `effect_trace_signature` are pure and closed over supplied values. Their
  observable contract includes artifact and effect identity, required
  authority, allow/deny outcome, executor, admission and lifecycle status,
  execution result, and the six semantic evidence digests already emitted by
  the implementation. If either function requires `SystemState`, host ABI,
  persistence, controller state, or a model call, stop.
- [x] **A4.13.3:** Preserve exact behavior for absent and malformed nested
  mappings, falsey values, historical admission status, policy-title
  filtering, allowed/admitted lifecycle normalization, answer projection,
  collection handling, integer coercion, and every existing exception type and
  message.
- [x] **A4.13.4:** Keep state composition, controller decision flow, LLM
  transcript signatures, composition-chain requirements, constitutional
  snapshot assembly, snapshot schema, comparison orchestration, replay, and
  bundle persistence outside this cut. Those responsibilities require runtime
  or controller context and are not per-effect governance rules.
- [x] **A4.13.5:** Keep the existing replay-signature digest representation
  distinct from the SHA-256 per-effect evidence receipt API introduced in Cut
  12. Similar canonicalization steps do not make their schemas or digest
  representations interchangeable.
- [x] **A4.13.6:** Preserve the historical `constitutional_trace` public
  function identities as exact package aliases while leaving its private
  snapshot helpers and all existing consumer import paths intact.
- [x] **A4.13.7:** Accept only the truthful same-owner
  `constitutional_trace -> core_governance` observation implied by this cut.
  Reject any new package edge, cross-owner dependency, cycle, undeclared edge,
  compatibility exception, persisted schema change, or observable signature,
  trace, replay, or bundle change.
- [x] Preserve the pre-cut `constitutional_trace` implementation independently
  with a content hash before changing it.
- [x] Extend the package-owned `trace` API with exact answer canonicalization
  and constitutional effect-signature projection over explicit inputs only.
- [x] Replace the root implementations with exact aliases while keeping all
  stateful constitutional trace construction and replay comparison in the
  root runtime surface.
- [x] Add permanent package tests for every projected field, all six semantic
  digests, status normalization, title filtering, malformed inputs, collection
  forms, deterministic failures, and input immutability.
- [x] Add identity, ownership, layer-hygiene, API, metadata, documentation,
  wheel/sdist-content, isolated-distribution, and Cloud Build coverage.
- [x] Run an independently loaded old/new differential, focused constitutional
  trace and replay tests, complete governance tests, exact deterministic Cloud
  Build selections, the architecture dry run and reviewed graph refresh,
  isolated distributions, and the complete qualification ladder.

Cut exit condition:

- [x] Constitutional per-effect trace requirements have one dependency-light
  governance owner and the historical root names are exact aliases. Runtime
  remains the sole owner of trace capture and assembly, controller path
  signatures, state snapshots, comparison orchestration, replay, persistence,
  dispatch, and execution, with no observable behavior change.

Cut 13 qualification evidence:

- [x] The preserved pre-cut `constitutional_trace` implementation has SHA-256
  `940432aec940541e9967049684e0f87143cf6e0b4128d357a075a164f6437deb`.
  The independently loaded differential passed 15 answer cases and 10,005
  effect-trace cases with exact successful values, exception types, exception
  messages, and input immutability.
- [x] Permanent package coverage pins the complete default and populated
  signatures, every projected requirement, all six semantic digests,
  historical status normalization, title filtering, malformed sections,
  deterministic failures, and immutability. The focused package,
  compatibility, hygiene, trace, replay, and bundle suites passed 82 tests;
  the complete governance package passed 103 tests.
- [x] The exact deterministic Cloud Build selections passed 516
  architecture/core tests and 106 BDD/UI tests. `uv lock --check`, syntax
  compilation, and `git diff --check` passed.
- [x] Fresh isolated distributions contained 21 governance-wheel entries and
  46 governance-sdist entries. The engine distribution exposed 77 canonical
  modules, and the isolated constitutional effect signature, SQLite, and
  runtime-state smoke checks passed without repository imports.
- [x] The reviewed graph remains at 28 components, 126 owned root modules, 3
  owned root package families, and 78 package edges. Grandfathered observations
  move from 571 to 572 and the combined graph from 631 to 632 edges solely for
  the planned same-owner `constitutional_trace -> core_governance` dependency;
  cycles, cyclic internal edges, undeclared dependencies, forbidden edges,
  and compatibility exceptions remain zero.
- [x] The final assembled qualification record contains 15 passing gates with
  zero failures, blocked gates, or omitted gates. Fresh gates include 785 root
  tests, a clean isolated rerun of 603 workstation tests with one expected
  skip, 3 skill-routing BDDs, 34 publication BDDs, the incremental publication
  BDD, publication reference, Flutter analysis, and all 51 Flutter widget
  tests. Six accepted live, provider, browser, screenshot, and trial gates were
  retained through the declared baseline merge. Candidate and promoted
  baseline are byte-identical at SHA-256
  `83d07320164e82b85dfd0f00ccce1f4b0aed58c193e86557500f73bd24047eb1`.
- [x] A sandboxed qualification attempt was rejected rather than promoted after
  child Python, Prolog, and Wasm runtimes could not use the UV cache. Its
  surviving workstation process was stopped; the valid normal-access ladder
  passed, and workstation was then rerun alone with a single log writer before
  final assembly.
- [x] A4.13.1 through A4.13.7 held without qualification. Governance owns only
  answer canonicalization and replay-significant projection over supplied
  effect evidence. State capture, trace assembly, composition and decision
  paths, transcript signatures, snapshot schemas, comparison orchestration,
  replay, persistence, dispatch, and execution remain in their existing
  owners.

#### Phase 4 Cut 14 - Governed Selection Precedence And Phase Closure

Measured scope and falsifiable assumptions:

- [x] **A4.14.1:** Treat retrieval as attention and candidate promotion as a
  separate current-use decision. An exact lexical or semantic match may place
  an artifact under consideration, but it must not become an answer candidate
  when its supplied governance state denies current use.
- [x] **A4.14.2:** Reuse the controller's existing
  `artifact_has_answer_capability` composition boundary rather than
  reimplementing admission, lifecycle, safety-overlay, or policy decisions in
  retrieval code. The boundary may probe whether a usable answer surface
  exists, but if it ranks, orders, or promotes candidates, stop and separate
  those concerns before applying it.
- [x] **A4.14.3:** Preserve retrieval, similarity, prompt-focus, ordering, and
  answer-text behavior among eligible artifacts. The only intentional
  behavioral correction is exclusion of governance-ineligible artifacts from
  persisted and focused direct-answer candidate lists.
- [x] **A4.14.4:** Keep retrieval, ranking, inventory loading, concrete
  artifact adaptation, and candidate promotion outside
  `realized-core-governance`. The package continues to decide only over
  supplied declarations and governance state; it does not search for or
  select artifacts.
- [x] **A4.14.5:** Migrate package-owned governance vocabulary imports directly
  to `realized_core_governance.vocabulary` only where the consumer already
  uses those pure values. Do not move artifact synthesis, host preflight,
  current-state assembly, persistence composition, or execution into the
  package as part of import cleanup.
- [x] **A4.14.6:** Retain `skill_governance` as a mixed root adapter solely for
  root-owned artifact and orchestration operations, and enforce that exception
  with a non-vacuous import-hygiene test. Existing pure compatibility facades
  remain exact aliases and retain their public import paths.
- [x] **A4.14.7:** Treat `superseded` according to its actual repository
  meaning: it is a learning/resumption relation, not a skill-governance
  admission, approval, lifecycle, or safety status. Do not manufacture a
  governance state merely to satisfy an over-broad checklist item.
- [x] **A4.14.8:** Accept only the reviewed graph change caused by replacing an
  indirect root-facade dependency with the canonical package dependency.
  Reject any new package edge, cycle, undeclared dependency, compatibility
  exception, or root-owner violation.
- [x] Preserve the pre-cut direct-knowledge selection implementation with a
  content hash and reproduce the exact-match governance leak before changing
  it.
- [x] Apply current-use eligibility through the answer-capability gate before
  retaining artifacts in both persisted and focused direct-knowledge candidate
  promotion paths.
- [x] Add permanent control and denial tests covering admitted, held,
  rejected, inactive, revoked, quarantined, current revocation, open incident,
  and denied-authority cases across both candidate paths.
- [x] Add explicit expired-approval coverage, complete-package status coverage,
  and a source-level import ratchet for the remaining mixed root adapter.
- [x] Move pure vocabulary consumers to the package owner while retaining only
  root-owned synthesis and governance-state orchestration imports from
  `skill_governance`.
- [x] Add the new contract and hygiene suites to deterministic Cloud Build and
  document the selection boundary in the module map and package README.
- [x] Run an independently loaded old/new differential, measure the additional
  governance check, and verify unchanged admitted and legacy behavior.
- [x] Run the complete governance, controller, compatibility, architecture,
  distribution, deterministic Cloud Build, BDD/UI, and 15-gate qualification
  ladder before closing the phase.

Cut exit condition:

- [x] A retrieved governed artifact can become an answer candidate only after
  current-use eligibility succeeds; eligible ordering remains unchanged; the
  governance package owns no retrieval or execution behavior; compatibility
  imports retain identity; and Phase 4 is fully qualified.

Cut 14 qualification evidence:

- [x] The preserved pre-cut `direct_knowledge_reuse` implementation has
  SHA-256
  `7df80838f3c191b68f4d238fcc790f61b89de5ac9210d742db9a2b372ba86a89`.
  Before the correction, an exact held artifact failed
  `artifact_has_answer_capability` but still appeared in both persisted and
  focused answer-candidate lists.
- [x] The independently loaded differential preserves two allow paths exactly:
  one legacy artifact and one governed admitted artifact. It proves seven
  intentional denial corrections for held, rejected, inactive, revoked,
  quarantined, current-revocation, and open-incident cases. Permanent tests
  additionally pin current policy denial of a declared authority.
- [x] A 25-candidate, 20-scan, three-run local differential measured median
  elapsed time of 0.273126 seconds before and 0.525180 seconds after the
  correction: 0.252054 seconds across 20 scans, or approximately 12.6
  milliseconds per 25-candidate scan. No retrieval score, ordering, or
  eligible result changed.
- [x] Five focused selection-precedence and import-hygiene tests pass. The
  broader affected controller suite passed 192 tests, the complete governance
  package passed 103 tests, and the refreshed exact architecture/core Cloud
  Build selection passed all 520 tests with normal child-process access.
- [x] The reviewed architecture delta removes two root-module dependencies on
  `skill_governance`, adds the direct same-owner
  `python_skill_host -> core_governance` observation, and reduces the combined
  graph from 632 to 631 edges. The graph remains at 28 components, 126 owned
  root modules, 3 owned root package families, and 78 package edges, with zero
  cycles, undeclared dependencies, forbidden edges, or compatibility
  exceptions.
- [x] Fresh isolated wheels for the app, conversation, engine, governance,
  host-interaction, LLM, semantics, skill-semantics, and runtime packages, plus
  governance, semantics, and skill-semantics source distributions, passed the
  distribution verifier. The verified surface contains 77 canonical modules,
  no forbidden package entries, and a successful fresh SQLite-backed smoke
  run.
- [x] The assembled qualification candidate passed all 15 required gates with
  zero failures, blocks, or unrun gates. Evidence includes 790 root tests, 603
  workstation tests, 38 deterministic BDD tests, a live publication BDD,
  publication-reference capture, clean Flutter analysis, all 51 Flutter widget
  tests, direct-v10 and scroll browser integrations, 11 subject-tab screenshots,
  workstation trial validation, and the complete validation ladder.
- [x] Record fresh isolated-distribution, deterministic BDD/UI, full root and
  workstation, Flutter, publication, and assembled 15-gate qualification
  evidence, then promote the reviewed qualification baseline. The promoted
  baseline is byte-identical to the reviewed candidate with SHA-256
  `14915ef515c1f147f76ea990f680254fff9a0cbea968179ea8de4287a755e09a`.

### Phase 5 - Make The LLM Boundary Package-Native

- [x] Confirm A18 by tracing every model call, prompt builder, planner, renderer,
  supplement helper, cache, and provider adapter.
- [x] Keep provider-neutral planning and rendering contracts in
  `realized-core-llm` or another explicitly justified LLM-owned package.
- [x] Keep controller-specific semantic reduction policy in the controller,
  passing only bounded planning requests and advisory results across the LLM
  boundary.
- [x] Keep workstation conversational lifecycle and session projections in the
  workstation, with provider calls behind an injected LLM port.
- [x] Move root-hosted LLM implementation only after separating provider
  mechanics from controller, governance, persistence, and CLI concerns.
- [x] Ensure model caches contain provider optimization state only and cannot
  substitute for persisted conversation, reduction, or resumption state.
- [x] Require typed parsing and validation before model output can become a
  proposal considered by controller or workstation logic.
- [x] Preserve LLM-off operation for mechanically decidable paths.
- [x] Add provider-neutral contract tests, invalid-output tests, cache-isolation
  tests, and tests proving that advisory output cannot bypass governance or
  mechanical realizer binding.
- [x] Build and exercise the LLM package independently from controller and
  workstation implementations.

Exit condition:

- [x] All model calls and prompt/rendering contracts have explicit LLM-layer
  ownership, and no model or cache carries authoritative application state.

#### Phase 5 Cut 1 - Stateless Provider Transport And Advisory Enforcement

Measured scope and falsifiable assumptions:

- [x] **A5.1.1:** Place provider SDK construction, one provider request, bounded
  compatibility fallback, bounded transient retry, and provider-response
  normalization in `realized-core-llm`. If this requires controller state,
  workstation session state, persistence, governance, or host execution, stop
  and leave that behavior with its current owner.
- [x] **A5.1.2:** Keep caller-specific prompt assembly and request policy with
  the caller. The governed-conversation provider, historical controller
  supplement, and workstation tool loop intentionally have different content,
  fallback, retry, and receipt semantics; the shared transport must express
  those policies explicitly rather than silently homogenizing them.
- [x] **A5.1.3:** Treat provider text and tool calls as typed advisory values.
  Invalid provider output must fail before application use, and a proposed tool
  call must still pass through the injected workstation mediator; provider
  output may not issue authority, select a concrete realizer, or execute an
  effect directly.
- [x] **A5.1.4:** Keep transport instances stateless across requests. Explicit
  conversation history remains a workstation input, persisted conversation and
  resumption truth remain in their application repositories, and controller
  proposal reuse remains explicit controller state. No provider cache may act
  as application memory.
- [x] **A5.1.5:** Preserve successful response values, provider metadata,
  caller-specific multipart-content handling, declared compatibility
  fallbacks, transient retry budgets, exception propagation, supplement
  receipts, workstation tool receipts, and public compatibility import paths.
  Malformed provider output is the sole intentional tightening: it now raises a
  typed response-contract error before reaching application logic.
- [x] **A5.1.6:** Make `realized-core-llm` the only production owner that imports
  or invokes the OpenAI SDK. Consumers must use its public package ABI, and the
  LLM package must not import engine, governance, persistence, runtime,
  workstation, UI, or exchange implementations.
- [x] **A5.1.7:** Accept only the reviewed `runtime_core -> core_llm` package
  edge and `supplement -> core_llm` root-to-component observation. Reject any
  cycle, undeclared dependency, forbidden edge, compatibility exception, or
  persisted-format change.
- [x] Preserve the pre-cut governed-conversation provider, controller
  supplement, and workstation LLM driver independently with content hashes.
- [x] Add a public typed transport contract, provider-neutral response and tool
  values, explicit content/fallback/retry policies, provider-client
  construction, endpoint normalization, and advisory model discovery to
  `realized-core-llm`.
- [x] Route the governed-conversation provider, historical controller
  supplement, and workstation LLM driver through the shared transport while
  retaining their prompt assembly, semantic policy, session lifecycle, tool
  mediation, receipts, and error surfaces in their existing owners.
- [x] Add transport, distribution, compatibility, layer-hygiene,
  cache-isolation, malformed-output, retry, fallback, and advisory-boundary
  regression coverage, including a denied side-effect proposal that cannot
  bypass the injected workstation mediator.
- [x] Add direct package dependencies, architecture ownership, Cloud Build,
  wheel-content verification, module documentation, and lockfile coverage.
- [x] Run independently loaded old/new differential coverage, exact
  deterministic Cloud Build selections, architecture ratchet, fresh isolated
  distributions, and the complete qualification ladder.

Cut exit condition:

- [x] Every production provider SDK call has one stateless package owner;
  caller-specific prompts and application state remain with their callers;
  provider output crosses the boundary only as validated advisory values; and
  no model response can bypass governance, realizer binding, or injected host
  mediation.

Cut 1 qualification evidence:

- [x] The preserved pre-cut provider, supplement, and workstation driver have
  SHA-256 hashes
  `df5d12cf81fbbedf0fa783a6e77caa6e7894e540f939adeb5fb9cb4a3ca6a6cf`,
  `e86820c599ac6b4210d26fb17d34a7d0a253ed6680f4fc8d1c61488fa707a8fe`,
  and
  `baf743de3e6fc8df273490b7ac6df5ac1ce729dc90cf45a378aaf471b792736e`.
  Independently loaded old/new adapters passed 14 behavior groups covering
  successful and multipart responses, metadata, every declared compatibility
  fallback, transient retries, ordinary failures, JSON receipts, explicit
  history, and mediated tool calls.
- [x] The exact deterministic Cloud Build selections pass 544
  architecture/core tests and 106 BDD/UI tests. A restricted sandbox run
  rejected 11 child-Python function tests; all 40 function-boundary tests and
  then the complete 544-test selection passed with normal host access.
- [x] Fresh isolated distributions contain the package-owned transport in the
  10-entry LLM wheel, expose 77 canonical engine modules, contain no forbidden
  entries, and pass the clean LLM-off SQLite smoke with vectors disabled.
- [x] The reviewed graph remains at 28 components, 126 owned root modules, and
  3 owned root package families. Package edges move from 78 to 79,
  grandfathered observations from 571 to 572, and the combined graph from 631
  to 633 edges solely for the two declared LLM dependencies; cycles,
  undeclared dependencies, forbidden edges, and compatibility exceptions
  remain zero.
- [x] The final assembled qualification record contains 15 passing gates with
  zero failures, blocked gates, or omitted gates, and the promoted baseline is
  byte-identical to the reviewed candidate. The default ladder requalified all
  nine executed gates, including 794 root tests and 603 workstation tests; the
  six intentionally separate qualification gates were retained from their
  passing records when assembling the reviewed 15-gate candidate.

### Phase 6 - Complete Runtime And Realizer Ownership

- [x] Define the callable provider/realizer registration ABI that is still open
  in the six-layer plan.
- [x] Represent advertised executor support separately from an installed
  ability and from an invocation-scoped authority grant.
- [x] Require exact mechanical binding from an admitted ability declaration to
  a registered executor or broker identity.
- [x] Make provider availability and runtime prerequisites inspectable before
  invocation.
- [x] Assign capability grants, execution frameworks, broker dispatch, host
  mediation, Wasm execution, child-runtime hosting, and execution receipts to
  explicit runtime owners.
- [x] Keep attachment resolution, delegated-rights narrowing, shared host
  actions, and generic receipt shaping in `realized-host-interaction` only where
  they remain backend-neutral.
- [x] Keep ability admission and lifecycle in governance.
- [x] Keep request-to-ability semantic matching in controller/retrieval.
- [x] Keep workstation approval UX and session state in workstation.
- [x] Retain reusable skill invocation mechanics in workstation after auditing
  the boundary: discovery, presentation, nested-result projection, and session
  policy are still coupled, so extraction in this cut would invent an unsafe
  abstraction rather than expose a cohesive runtime responsibility.
- [x] Inject concrete providers at entry/composition boundaries; do not add a
  global mutable registry hidden inside the runtime.
- [x] Add end-to-end tests for definition, admission, subject visibility,
  semantic selection, exact realizer binding, authority grant, execution,
  result projection, and receipts.
- [x] Add negative tests for unavailable realizers, mismatched executors,
  undeclared brokers, denied authority, and a semantically similar but wrong
  ability.

Exit condition:

- [x] The complete ability journey respects all three distinct bindings:
  subject-to-ability, request-to-ability, and ability-to-realizer.
- [x] Controller and workstation can use injected realizers without importing
  one another or relying on undeclared root implementation modules.

#### Phase 6 Cut 1 - Exact Injected Host Realizers

Validated assumptions and decisions:

- [x] **A6.1:** Treat the provider as a backend-neutral host ABI. The shared
  package owns immutable descriptors, prerequisite evidence, invocations,
  bindings, provider protocol, composition, and the empty provider; it owns no
  concrete executor, broker, admission, matching, or workstation behavior.
- [x] **A6.2:** Keep installation, admission, subject visibility, semantic
  selection, authority, and host realization as distinct checkpoints. Tests
  prove that one checkpoint cannot synthesize or bypass another.
- [x] **A6.3:** Require exact executor and broker identities from admitted v2
  declarations. Imported Python source receives deterministic literal
  `broker_request(...)` declaration enrichment only when the declaration did
  not explicitly supply broker metadata; dynamic identities are not guessed.
- [x] **A6.4:** Inspect provider registration and runtime prerequisites before
  any invocation-scoped authority grant is issued. Missing, unavailable,
  mismatched, undeclared, and denied paths invoke no callback.
- [x] **A6.5:** Keep provider composition immutable and explicit. The packaged
  host provider and workstation `ws.*` provider are independently constructible
  and combined only at application/session composition boundaries.
- [x] **A6.6:** Keep the parent authoritative across Python child execution. The
  child sends only an exact broker identity and arguments through a bounded,
  invocation-scoped loopback channel; the parent rechecks the token,
  declaration, admission, grant, and broker ABI before provider dispatch.
- [x] **A6.7:** Preserve existing executor and broker outputs, error shapes,
  receipts, nested invocation traces, and workstation action behavior. Nested
  terminal status projection follows only the bounded `result` envelope and
  does not reinterpret unrelated metadata.

Implemented scope:

- [x] Add the immutable public provider ABI to
  `realized_host_interaction.realizers` and attach it to
  `HostInteractionContext` without serializing callable implementation state.
- [x] Build concrete Python, Bash, Ansible, Wasm, and host-broker bindings in the
  application adapter, with executable/module/operating-system prerequisites.
- [x] Route runtime mediation, execution frameworks, Wasm host calls, nested
  tools/skills, and workstation skill invocation through supplied providers.
- [x] Replace the mutable broker table with an immutable compatibility table;
  provider overrides create a new provider rather than mutating process state.
- [x] Forward Python child broker calls to the authoritative parent provider and
  add denial tests for bad tokens, undeclared brokers, missing grants, invalid
  ABI arguments, and unavailable realizers.
- [x] Add provider contract, concrete-adapter, runtime mediation, workstation
  composition, distribution, import-hygiene, and end-to-end routing coverage.

Qualification evidence:

- [x] The exact deterministic Cloud Build architecture/core selection passes
  562 tests. The deterministic BDD/UI selection passes 106 tests.
- [x] Fresh isolated app, conversation, engine, governance, host-interaction,
  LLM, runtime, semantics, and skill distributions pass the distribution
  verifier. The verifier observes 80 canonical engine modules and 94 engine
  distribution entries, with no forbidden modules, and a clean SQLite smoke
  run with vector indexing disabled.
- [x] The architecture ratchet passes with 28 package components, 128 owned root
  modules, 3 owned root package families, 80 package edges, and 586
  grandfathered observations; cycles, undeclared dependencies, forbidden
  edges, and compatibility exceptions remain zero.
- [x] The final assembled qualification record contains all 15 declared gates
  as passing. Fresh default evidence includes 816 root tests, 608 workstation
  tests with one expected skip, 3 skill-routing BDD tests, 34 publication BDD
  tests, the incremental publication BDD, publication-reference reproduction,
  Flutter analysis, and Flutter widget tests. The six explicitly separate
  integration/provider gates retain their previously qualified passing
  evidence.

### Phase 7 - Make The Subject Lifecycle Package-Native

- [x] Confirm A8 against actual identity, provenance, persistence, and consumer
  boundaries.
- [ ] Make `workstation.subject.core` the canonical owner of the subject
  lifecycle unless the cohesion check proves that an independent subdomain is
  required.
- [ ] Organize learning context, Gather, Itemize, Decision Review, Review, and
  Publication as internal domain modules rather than separate UV projects by
  default.
- [ ] Move subject modules in cycle-safe reverse-topological cuts: relocate
  leaf consumers before shared value models whenever moving the values first
  would close a combined root/package cycle, then move persistence adapters
  only after their domain dependencies are package-native.
- [ ] Move learning-context and source-ingestion behavior while preserving
  corpus paths, delta semantics, projection rules, and provenance.
- [ ] Move itemization extraction and validation while preserving stable item
  identities and freshness behavior.
- [ ] Move decision-frame, review-item, policy, and analysis projection behavior
  while preserving the distinction between coordinated transformation and
  runtime semantic reduction.
- [ ] Move review composition without making presentation state the source of
  truth.
- [x] Move publication models, validation, projection, deterministic build, and
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

#### Phase 7 Cut 1 - Invert Subject Runtime Effects

- [x] Reject values-first relocation after the combined dependency graph shows
  that it would close `subject_core` cycles through `runtime_core` and
  `foundation_host`.
- [x] Define segregated subject policy, source-ingress, and assistant-capture
  ports in `workstation.subject.core`, with a runtime-neutral result value and
  a fail-closed uncomposed implementation.
- [x] Move concrete session-policy, source-action, and assistant-capture calls
  behind a stateless `runtime_core` adapter.
- [x] Inject the adapter explicitly at the in-process application and gRPC
  composition roots; do not add a mutable process-global runtime provider.
- [x] Remove `subject_core -> runtime_core` and
  `subject_core -> foundation_host`, then declare the intentional inverse
  `runtime_core -> subject_core` adapter edge.
- [x] Add direct port, adapter normalization, service forwarding, and
  composition tests.
- [x] Qualify the cut against the full subject workflow, architecture ratchet,
  deterministic UI/service tests, and Gather-to-Publication BDD paths before
  moving the first root subject module.

  Qualification passed with 123 subject-workflow tests, 22 subject-service and
  host-port tests, 12 shell/gRPC tests, 91 architecture, facade, and package
  hygiene tests, the affected Textual selection scenarios, all 34 deterministic
  publication BDD paths, and the incremental same-subject publication ladder.
  The promoted dependency graph has 79 package edges and no cyclic nodes or
  cyclic internal edges.

#### Phase 7 Cut 2 - Move Itemization Validation Behind Its Canonical Package ABI

- [x] Re-evaluate relocation order against the combined graph and require
  reverse-topological stage cuts while `subject_workflow` still consumes
  canonical root subject modules.
- [x] Make `workstation.subject.core.itemize_validation` the canonical owner of
  itemization-session validation without changing validation inputs, outputs,
  wording, or freshness semantics.
- [x] Retain `itemize_validation` as an identity-preserving compatibility
  facade and update the subject workflow to consume the canonical package
  module directly.
- [x] Record the facade in the architecture manifest and protect callable
  identity with a compatibility test.
- [x] Verify that the staged dependency substitution reduces the measured
  graph rather than enlarging it: package edges remain 79, combined edges fall
  from 648 to 647, tracked root/package observations fall from 568 to 567, and
  cyclic nodes and internal cyclic edges remain zero.
- [x] Qualify the cut against package metadata, itemization and subject
  workflow tests, architecture/facade hygiene, and every required
  Gather-to-Publication BDD path before moving another subject module.

  Qualification passed with a subject-core sdist and wheel containing the new
  canonical module, 125 itemization and subject-workflow tests, 98
  architecture/facade/package-hygiene tests, all 34 deterministic publication
  BDD paths, and the deterministic incremental same-subject publication
  ladder. The promoted ratchet reports 79 package edges, 586 grandfathered
  observations, and no cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 3 - Relocate The Learning-Capture Application Service

- [x] Reject a direct `gather_sources` move while the implementation remains in
  `foundation_host`, because doing so would force a foundation package to own
  an upward dependency on subject governance.
- [x] Move markdown-to-subject learning capture unchanged into
  `workstation.subject.service`, which already owns subject application
  coordination above domain and workstation foundation values.
- [x] Update `runtime_core` to consume the canonical subject-service module and
  retain the historical foundation-host module as a true compatibility alias.
- [x] Declare both the new runtime dependency and the temporary compatibility
  dependency so installed wheels do not rely on an undeclared import.
- [x] Extend compatibility-identity coverage and classify the old module as a
  compatibility alias in the architecture manifest.
- [x] Verify the intended graph shape before baseline promotion: package edges
  rise from 79 to 81 as the application-service and foundation-value
  dependencies become explicit; tracked root/package observations remain 567;
  forbidden and undeclared edges, cyclic nodes, and cyclic internal edges
  remain zero.
- [x] Qualify all three affected distributions, direct learning-capture and host-port
  behavior, architecture/facade hygiene, subject workflow, and every required
  Gather-to-Publication BDD path before moving `gather_sources`.

  Qualification passed with successful sdists and wheels for foundation-host,
  runtime-core, and subject-service; 21 direct learning-capture, compatibility,
  and host-port tests; 158 runtime integration tests; 98 architecture, facade,
  and package-hygiene tests; 123 subject-workflow tests; all 34 deterministic
  publication BDD paths; and the deterministic incremental same-subject
  publication ladder. The promoted graph has 81 package edges, 586
  grandfathered observations, and no cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 4 - Make Gather Source Persistence Package-Native

- [x] Move Gather source, revision, collection, path, and persistence behavior
  unchanged into `workstation.subject.core.gather_sources`.
- [x] Update subject-core, subject-service, and runtime-core production callers
  to consume the canonical package module.
- [x] Retain root `gather_sources` as a true module alias and protect legacy to
  canonical module identity with a compatibility test.
- [x] Record the root facade in the ownership ledger without permitting any
  package or canonical root module to import it.
- [x] Verify the graph improvement before baseline promotion: package edges
  remain 81, combined edges fall from 649 to 646, tracked root/package
  observations fall from 567 to 564, and forbidden, undeclared, compatibility
  facade-import, and cycle sets remain empty.
- [x] Qualify the subject-core distribution, Gather persistence and capture
  behavior, architecture/facade hygiene, subject workflow, and every required
  Gather-to-Publication BDD path before selecting the next domain leaf.

  Qualification passed with a subject-core sdist and wheel containing canonical
  Gather persistence; 42 focused Gather, learning-capture, workstation-core,
  and subject-service tests; 99 architecture, facade, and package-hygiene
  tests; 123 subject-workflow tests; all 34 deterministic publication BDD
  paths; and the deterministic incremental same-subject publication ladder.
  The promoted graph retains 81 package edges, reduces grandfathered
  observations to 583, and has no cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 5 - Make Publication Projection Package-Native

- [x] Move deterministic learning-context-to-publication projection unchanged
  into `workstation.subject.core.publication_projection` and update the subject
  workflow to consume it directly.
- [x] Retain root `publication_projection` as a true module alias and protect
  legacy to canonical module identity with a compatibility test.
- [x] Detect and repair the one location-sensitive assumption exposed by the
  move: checkout-relative source labels now discover the checkout root through
  repository markers instead of assuming the module lives at repository root.
- [x] Preserve installed-wheel behavior by retaining session/workspace roots as
  the primary normalization sources and treating checkout discovery only as the
  source-tree fallback it replaces.
- [x] Verify the graph improvement before baseline promotion: package edges
  remain 81, combined edges fall from 646 to 639, tracked root/package
  observations fall from 564 to 557, and forbidden, undeclared, compatibility
  facade-import, and cycle sets remain empty.
- [x] Qualify the subject-core distribution, direct publication projection and
  source-label behavior, architecture/facade hygiene, subject workflow, and
  every required Gather-to-Publication BDD path before moving another
  publication module.

Qualification passed with a subject-core sdist and wheel containing the
canonical publication projection; 90 direct projection, source-label, and
compatibility tests; 100 architecture, facade, and package-hygiene tests; 123
subject-workflow tests; all 34 deterministic publication BDD paths; and the
deterministic incremental same-subject publication ladder. The promoted graph
retains 81 package edges, reduces grandfathered observations to 576, and has
no cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 6 - Make Publication Validation Package-Native

- [x] Move deterministic publication validation unchanged into
  `workstation.subject.core.publication_validation` and update the canonical
  publication projection to consume it directly.
- [x] Retain root `publication_validation` as a true module alias and protect
  legacy to canonical module identity with a compatibility test.
- [x] Prove source equivalence with the pre-move SHA-256
  `6a3e69344dff8849a5df52d8df30eb0098f466f33aaa4b1c84b8353d726598c1`.
- [x] Verify the graph before baseline promotion: package edges remain 81,
  combined edges fall from 639 to 637, the canonical
  `subject_core -> publication_validation` root dependency disappears, and
  only the declared root compatibility alias is added. No forbidden,
  undeclared, compatibility-facade import, or cycle set expands.
- [x] Qualify the subject-core distribution, direct publication behavior,
  architecture/facade hygiene, subject workflow, and every required
  Gather-to-Publication BDD path before moving another publication module.

Qualification passed with a subject-core sdist and wheel containing canonical
publication validation; 91 direct publication and compatibility tests; 101
architecture, facade, and package-hygiene tests; 123 subject-workflow tests;
all 34 deterministic publication BDD paths; and the deterministic incremental
same-subject publication ladder. The promoted graph retains 81 package edges,
reduces grandfathered observations to 574, and has no cyclic nodes or cyclic
internal edges.

#### Phase 7 Cut 7 - Make Publication Rendering Package-Native

- [x] Move deterministic Markdown and Typst rendering unchanged into
  `workstation.subject.core.publication_render` and update the canonical
  publication projection to consume it directly.
- [x] Retain root `publication_render` as a true module alias and protect legacy
  to canonical module identity with a compatibility test.
- [x] Prove source equivalence with the pre-move SHA-256
  `756807a7a2285d427aef916b8e76d88ec27ac56d900f2c25595d60d8092d4620`.
- [x] Confirm that the renderer has no module-location assumption and preserves
  its existing publication-value, text-normalization, runtime-temp, Typst, and
  filesystem boundaries unchanged.
- [x] Verify the graph before baseline promotion: package edges remain 81,
  combined edges fall from 637 to 634, the canonical
  `subject_core -> publication_render` root dependency disappears, and only
  the declared root compatibility alias is added. No forbidden, undeclared,
  compatibility-facade import, or cycle set expands.
- [x] Qualify the subject-core distribution, direct publication and render
  behavior, architecture/facade hygiene, subject workflow, and every required
  Gather-to-Publication BDD path before moving another publication module.

Qualification passed with a subject-core sdist and wheel containing canonical
publication rendering; 94 direct publication, Typst validation, and
compatibility tests; 102 architecture, facade, and package-hygiene tests; 123
subject-workflow tests; all 34 deterministic publication BDD paths; and the
deterministic incremental same-subject publication ladder. The promoted graph
retains 81 package edges, reduces grandfathered observations to 571, and has
no cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 8 - Make Publication Values Package-Native

- [x] Reject the first direct publication-value relocation because it exposed a
  new `subject_core -> id_generation` package-to-root dependency; do not
  grandfather that dependency.
- [x] Confirm that the architecture ledger already assigns the dependency-free
  identifier helper to the semantic model, then move it into the existing
  `realized_core_semantics.identifiers` module rather than creating another UV
  project.
- [x] Preserve `slugify` and `make_id` behavior, add their explicit package
  surface and deterministic tests, migrate every production consumer to the
  canonical module, and retain root `id_generation` as a true module alias.
- [x] Move the typed publication values, stable identifiers, diff projection,
  persistence paths, composition records, build records, and render-artifact
  tracking unchanged into `workstation.subject.core.publication`.
- [x] Update all package-owned publication consumers to the canonical module;
  retain root `publication` as a true module alias and mark all four historical
  publication roots as compatibility facades.
- [x] Prove the publication substrate retains its pre-move SHA-256
  `45ea166b875d4351f133634b3957a57c77486f7b0b8d04e9349a9511e86cc994`;
  retain the identifier helper's algorithms from pre-move SHA-256
  `6692553b029f26b5a3d12f084cc8fd964d38bbba4e545141ea73179f04ac25f0`
  while correcting only its inaccurate `limit=16` doc example and adding
  `__all__`.
- [x] Verify the graph before baseline promotion: package edges move from 81 to
  82 for the declared `subject_core -> core_semantics` edge, combined edges
  remain 634, root-to-root dependencies fall by ten as canonical identifier
  consumers move to their owner, grandfathered observations fall from 571 to
  570, and no forbidden, undeclared, facade-import, or cycle set expands.
- [x] Qualify both distributions, the isolated engine compatibility import,
  every identifier consumer family, architecture/facade hygiene, subject
  workflow, and every required Gather-to-Publication BDD path.

Qualification passed with fresh core-semantics and subject-core sdists and
wheels, plus a fresh core-engine wheel whose historical `id_generation` import
resolves to the exact package module outside the checkout. All 170 focused
semantic, controller, learning-context, itemization, decision-review, DST,
publication, side, and compatibility tests pass; all 104 architecture, facade,
and package-hygiene tests pass; all 123 subject-workflow tests pass; all 34
deterministic publication BDD paths pass; and the deterministic incremental
same-subject publication ladder passes. The promoted graph has 82 package
edges, 570 grandfathered observations, and no cyclic nodes or cyclic internal
edges.

#### Phase 7 Cut 9 - Graduate Coordinated Transformation Into The Workspace

- [x] Stop before moving decision projection when its formal CTFS dependency is
  found to be a project-shaped but unregistered top-level package; do not create
  a `subject_core ->` unregistered-root dependency or conceal it in the
  baseline.
- [x] Preserve `coordinated_transformation` as the import and distribution ABI
  while moving its Python package to a conventional `src/` layout and repairing
  the pre-existing sdist-to-wheel failure caused by a package directory outside
  the sdist build root.
- [x] Replace the historical wildcard re-export with an explicit 73-name CTFS
  API covering formal carriers, relation aliases, judgments, axiom checks, and
  reachability utilities; retain exact package-to-core object identity.
- [x] Register the existing cohesive project as a dependency-free UV workspace
  member and subject-domain architecture component, add the root application
  dependency, and remove only its obsolete root-package ownership entry.
- [x] Keep theory and implementation documents at their stable repository paths,
  include both in the sdist, and keep the runtime wheel limited to executable
  package code and distribution metadata.
- [x] Verify the graph substitution before baseline promotion: component count
  rises from 28 to 29, owned root-package families fall from three to two,
  package edges remain 82, combined graph edges remain 634, grandfathered
  observations fall from 570 to 569, and forbidden, undeclared, wildcard,
  facade-import, and cycle sets remain empty.
- [x] Qualify source, frozen-workspace, wheel-only, and sdist paths before moving
  any decision-review behavior.

Qualification passed with a wheel and sdist built from the repaired project,
an isolated wheel import outside the checkout, 10 direct CTFS API, model, and
distribution tests, 67 DST and decision-review tests, 119 architecture, facade,
and package-hygiene tests, 156 subject-workflow and publication tests, all 34
deterministic publication BDD paths, and the deterministic incremental
same-subject publication ladder. The promoted graph has 29 components, 82
package edges, 634 combined edges, 569 grandfathered observations, and no
cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 10 - Make Decision Analysis Projection Package-Native

- [x] Confirm that decision analysis projection is the reverse-topological leaf:
  only subject-core production modules consume it, it has no module-location
  assumptions, and its formal evaluator is the qualified CTFS component rather
  than runtime semantic reduction.
- [x] Move model projection, deterministic CTFS evaluation, option outcomes,
  risk summaries, recommendation status, receipt values, hashes, persistence,
  and loading unchanged into
  `workstation.subject.core.decision_review_projection`.
- [x] Update package-owned workflow and publication consumers to the canonical
  module, retain root `decision_review_projection` as a true module alias, and
  protect legacy-to-canonical module identity with a compatibility test.
- [x] Prove source equivalence with the pre-move SHA-256
  `880c4c2b217ffc237bdb32bbdcb98ce4f0a31c2f6455411e6be4f4975c7ed340`.
- [x] Declare and lock `subject_core -> coordinated_transformation`; preserve the
  temporary `subject_core -> decision_review_models` leaf edge until the shared
  decision values move in a later cycle-safe cut.
- [x] Verify the graph before baseline promotion: package edges rise from 82 to
  83 for the declared CTFS dependency, combined edges fall from 634 to 631,
  grandfathered observations fall from 569 to 565, and forbidden, undeclared,
  wildcard, facade-import, and cycle sets remain empty.
- [x] Qualify the subject-core distribution, CTFS API, decision analysis,
  compatibility identity, architecture hygiene, subject workflow, and every
  required Gather-to-Publication BDD path.

Qualification passed with a subject-core sdist and wheel containing canonical
decision analysis projection; 10 direct CTFS tests; 103 focused decision,
publication, and compatibility tests; 120 architecture, facade, and
package-hygiene tests; all 123 subject-workflow tests; all 34 deterministic
publication BDD paths; and the deterministic incremental same-subject
publication ladder. The promoted graph has 29 components, 83 package edges,
631 combined edges, 565 grandfathered observations, and no cyclic nodes or
cyclic internal edges.

#### Phase 7 Cut 11 - Make Decision Policy Package-Native

- [x] Select decision policy as the next reverse-topological leaf because all
  production consumers are already canonical subject-core modules and its only
  domain dependencies are decision paths and semantic-text normalization.
- [x] Move policy-profile values, stable identity and content hashes, default
  profile derivation, profile cycling, persistence path, writing, and loading
  unchanged into `workstation.subject.core.decision_review_policy`.
- [x] Update decision analysis, publication projection, and subject workflow to
  consume the canonical policy module; retain root `decision_review_policy` as
  a true module alias and protect module identity with a compatibility test.
- [x] Prove source equivalence with the pre-move SHA-256
  `a6d9d626c9e2e1374d7c56b1beaaf0b8f17e850371499dc4ad02ae2e4dba7f8c`.
- [x] Verify the graph before baseline promotion: package edges remain 83,
  combined edges fall from 631 to 629, grandfathered observations fall from
  565 to 563, and forbidden, undeclared, wildcard, facade-import, and cycle
  sets remain empty.
- [x] Qualify the subject-core distribution, decision and publication behavior,
  compatibility identity, architecture hygiene, subject workflow, and every
  required Gather-to-Publication BDD path.

Qualification passed with a subject-core sdist and wheel containing canonical
decision policy; 104 focused decision, publication, and compatibility tests;
121 architecture, facade, and package-hygiene tests; all 123 subject-workflow
tests; all 34 deterministic publication BDD paths; and the deterministic
incremental same-subject publication ladder. The promoted graph has 29
components, 83 package edges, 629 combined edges, 563 grandfathered
observations, and no cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 12 - Register DST As A Measured Transitional Component

- [x] Stop before moving shared decision values when the dependency audit shows
  that DST is a cohesive, theory-defined subdomain rather than an internal
  subject-workflow folder, and that folding it into `subject_core` would mix
  deterministic decision-support logic with live controller orchestration.
- [x] Preserve the `dst.*` import ABI and logical `dst/<source>.md` references
  while moving package code, prompt, source cases, and typed fixtures into a
  conventional `src/dst` layout; keep DST theory, implementation guidance, and
  distribution tests at the project root.
- [x] Replace wildcard aggregation with an explicit, duplicate-checked 92-name
  package surface and keep every exported object identical to its defining
  module object.
- [x] Register DST in the UV workspace, architecture manifest, root application
  dependencies, subject-core dependencies, lockfile, release classification,
  and Cloud Build without changing decision or workflow behavior.
- [x] Run an isolated wheel probe and retain its failure as architectural
  evidence: importing the complete historical `dst` surface still reaches
  `semantic_text`, and projection/orchestration additionally reach five other
  root modules. Under A12, DST is therefore measured and buildable but remains
  transitional; do not claim it is independently consumable or hide the root
  dependencies in package metadata.
- [x] Prove the ratchet update is a topology reclassification rather than new
  coupling: the existing `dst` root-package relationships become three package
  edges and the same six component-to-root observations. Component count rises
  from 29 to 30, owned root-package families fall from two to one, package edges
  rise from 83 to 86, combined edges remain 629, grandfathered observations
  fall from 563 to 554, and forbidden, undeclared, facade-import, and cycle
  sets remain empty.
- [x] Qualify the source layout, sdist-to-wheel build, wheel contents, package
  resources, subject workflow, Textual DST flows, architecture/release rules,
  and every deterministic Gather-to-Publication path before splitting the
  remaining upper-layer adapters.

Qualification passed with a clean DST sdist-to-wheel build containing all 92
API exports, 18 source cases, the runtime prompt, and 16 typed fixture artifacts;
63 DST tests; 125 architecture, facade, package-hygiene, release-export, and
portability tests; 17 subject-service API tests; all 123 subject-workflow tests;
19 focused Textual DST tests; all 34 deterministic publication BDD paths; and
the deterministic incremental same-subject publication ladder. The promoted
graph has 30 components, 86 package edges, 629 combined edges, 554
grandfathered observations, and no cyclic nodes or cyclic internal edges.

#### Phase 7 Cut 13 - Make Semantic Normalization Package-Native

- [x] Audit the semantic normalization dependency chain before moving it and
  confirm that `prolog`, `title_semantics`, and `semantic_text` form one
  dependency-light semantic-model cluster: Prolog representation is
  dependency-free, title semantics depends only on that representation, and
  semantic-text normalization depends only on title semantics.
- [x] Preserve the pre-move implementations identified by SHA-256 values
  `7c4293938fd408fc5bbc1061546d2376dec527b07f4319dbdc66a090b93cfd90`,
  `1fc9968301902f2de1f0102a3a8d1eb1c1088ce10b83a73662227d7088f565df`,
  and `c34cb2f4d201005ca0a94e6614afe84d2c044372d3d211ffead195e1109daae8`
  for `prolog`, `title_semantics`, and `semantic_text`, respectively.
- [x] Move the cluster unchanged except for canonical relative imports into
  `realized_core_semantics`; expose explicit, duplicate-checked 22-name,
  27-name, and 31-name module APIs; and retain each root import as an exact
  module-identity alias.
- [x] Migrate every package and canonical root consumer to the package owner,
  declare each direct distribution dependency, and classify only the three
  historical root names as compatibility facades.
- [x] Prove the graph change before baseline promotion: 15 package-to-root
  semantic dependencies disappear, 12 explicit package dependencies replace
  them while three coalesce into already-existing package edges, package edges
  move from 86 to 98, grandfathered observations fall from 554 to 514, and the
  combined graph falls from 629 to 601 edges. Forbidden, undeclared,
  canonical-facade-import, wildcard-regression, and cycle sets remain empty.
- [x] Rebuild the semantic and DST distributions and repeat the isolated DST
  probe. The probe now passes semantic normalization and fails first at
  `applied_theory_types`, proving the intended boundary moved while retaining
  evidence that DST is not yet independently consumable.
- [x] Qualify package APIs, exact compatibility identity, Prolog/title behavior,
  CTFS, DST, architecture and import hygiene, subject workflow and service,
  Textual consumers, publication BDD paths, and incremental publication before
  selecting the next reverse-topological subject-domain cut.

Qualification passed with semantic and DST sdist-to-wheel builds; 14 direct
core-semantics tests; 10 CTFS tests; 63 DST tests; 43 Prolog/title behavior
tests; 126 architecture, compatibility, hygiene, release, and portability
tests; 17 subject-service API tests; all 123 subject-workflow tests; all 171
Textual workstation tests; all 34 deterministic publication BDD paths; and the
deterministic incremental same-subject publication ladder. The complete root
suite passed 826 tests, and the complete workstation suite passed 613 tests
with one expected skip. The promoted graph has 30 components, 98 package
edges, 601 combined edges, 514 grandfathered observations, and no cyclic nodes
or cyclic internal edges.

#### Phase 7 Cut 14 - Make Proposal Vocabulary Package-Native

Measured scope and falsifiable assumptions:

- [x] **A7.14.1:** Confirm that supplement depth, proposal governance status,
  and proposal type are immutable cross-domain semantic vocabulary rather than
  applied-theory aggregate behavior. If moving them requires artifact models,
  controller payloads, governance evaluation, persistence, model invocation,
  or workstation state, stop rather than moving `applied_theory_types` as a
  whole.
- [x] **A7.14.2:** Preserve every enum class name, member name, member order,
  member value, equality result, module-level import, and legacy pickle global.
  The historical module must re-export the exact canonical class objects, not
  parallel enum definitions.
- [x] **A7.14.3:** Migrate only canonical DST production code to the package
  owner. Existing callers and tests may retain the historical import until the
  broader applied-theory aggregate is decomposed safely.
- [x] **A7.14.4:** Treat the resulting
  `applied_theory_types -> core_semantics` dependency as a measured,
  same-responsibility compatibility delegation. Accept it only if it replaces
  the opposite DST-to-root dependency, creates no cycle or forbidden owner
  direction, and does not conceal unrelated root reach.
- [x] **A7.14.5:** Require the isolated DST wheel probe to advance beyond
  `applied_theory_types` and expose the next genuine undeclared boundary. Do
  not add root modules as distribution dependencies merely to make the probe
  pass.
- [x] Add `realized_core_semantics.proposals` with an explicit three-name API
  containing `SupplementMode`, `ProposalGovernanceStatus`, and `ProposalType`.
- [x] Replace the three root enum definitions with exact imports from the
  canonical package while retaining the rest of `applied_theory_types` at its
  current owner.
- [x] Migrate DST orchestration to the canonical proposal module and prove the
  legacy classes retain exact object and protocol-zero pickle identity.
- [x] Add package API, member-order/value, distribution-content, compatibility,
  and orchestration tests.
- [x] Rebuild the semantic and DST source distributions and wheels, then repeat
  the repository-root-free DST import probe.
- [x] Promote the graph only after proving that all cycle, forbidden,
  undeclared, compatibility-facade, canonical-facade, and wildcard regression
  sets remain empty.
- [x] Run the semantic package, complete DST suite, architecture and hygiene
  suite, subject service and workflow suites, publication BDD paths,
  incremental publication ladder, and complete root and workstation suites.

Cut exit condition:

- [x] Proposal vocabulary has one dependency-light semantic owner; legacy
  imports remain identity-compatible; DST no longer imports
  `applied_theory_types`; and no proposal-admission, governance, controller,
  provider, persistence, or workstation behavior moved with the vocabulary.

Cut 14 qualification evidence:

- [x] The canonical enum names, order, and values reproduce the pre-cut digest
  `110ed6b991fd43d17aa9235a3dcd8603406a72cedf707728be603a59cac7b8ef`.
  All three historical imports are the canonical class objects, and legacy
  pickle globals resolve to those same objects.
- [x] Both semantic and DST sdist-to-wheel builds passed. The semantic wheel
  contains `proposals.py`; the isolated DST wheel now passes proposal loading
  and fails first at `decision_review_constructs`, proving the intended
  boundary moved without disguising the remaining subject-domain dependency.
- [x] The promoted graph retains 30 components, 98 package edges, 601 combined
  edges, and 514 grandfathered observations. DST root reach falls from five to
  four modules. One same-responsibility root-to-package delegation replaces the
  removed package-to-root dependency; all cycle, forbidden, undeclared, facade,
  and wildcard regression sets remain empty.
- [x] Qualification passed 15 core-semantics tests, all 63 DST tests, 126
  architecture/compatibility/hygiene/metadata/portability tests, 17
  subject-service API and gRPC tests, all 123 subject-workflow tests, all 34
  deterministic publication BDD paths, and the incremental same-subject
  publication ladder. The complete root suite passed 828 tests. The complete
  workstation suite passed 613 tests with one expected skip.
- [x] A7.14.1 through A7.14.5 held without qualification. The extraction moved
  stable vocabulary only; the applied-theory aggregate and all causal behavior
  remain with their existing owners.

#### Phase 7 Cut 15 - Make Shared Subject Semantic Values Package-Native

Measured scope and falsifiable assumptions:

- [x] **A7.15.1:** Treat subject identity, itemization records,
  decision-review records, transformation-construct candidate records, and
  deterministic item-to-construct projection as dependency-light semantic
  values. If their extraction requires corpus paths, filesystem persistence,
  live controller calls, workflow state, governance decisions, or model
  invocation, stop and leave that behavior with its existing application
  owner.
- [x] **A7.15.2:** Do not move `decision_review_constructs.py` as a unit. It
  mixes stable semantic values with subject-corpus persistence; only the pure
  value and deterministic projection portion belongs in `core_semantics`.
- [x] **A7.15.3:** Do not place shared values in `subject_core`. DST already
  sits below `subject_core`; making DST import that package would close a
  package cycle. The existing dependency-light semantic contract package is
  the cohesive owner and avoids creating another UV project.
- [x] **A7.15.4:** Preserve normalized payloads, content hashes, stable IDs,
  enum-like value sets, exception behavior, deterministic projection order,
  confidence values, relation hints, historical imports, exact class identity,
  and legacy pickle globals.
- [x] **A7.15.5:** Keep `itemize.py`, `decision_review.py`, and
  `decision_review_constructs.py` as application and persistence adapters.
  Their live orchestration, paths, on-disk formats, and write behavior must not
  move in this cut.
- [x] **A7.15.6:** Accept compatibility-facade status for
  `itemize_models.py` and `decision_review_models.py` only after proving that
  the change replaces package-to-root reach, creates no cycle or forbidden
  owner direction, and leaves canonical package code free of facade imports.
- [x] Add canonical `itemization`, `decision_review`, and
  `transformation_constructs` modules to `realized_core_semantics`, and move
  canonical subject-ID normalization into the existing identifier module.
- [x] Convert the two historical model modules to exact module aliases; retain
  persistence in the historical application adapters; migrate DST and
  subject-core consumers to canonical value imports.
- [x] Add package API, distribution-content, compatibility-identity,
  legacy-pickle, and deterministic projection coverage.
- [x] Prove pre-cut equivalence independently across valid and malformed values
  before changing the architecture baseline.
- [x] Rebuild the semantic and DST source distributions and wheels, then repeat
  the repository-root-free DST import probe.
- [x] Promote the graph only after proving that all cycle, forbidden,
  undeclared, compatibility-facade, canonical-facade, and wildcard regression
  sets remain empty.
- [x] Run the semantic package, complete DST suite, focused subject-domain
  tests, architecture and hygiene suite, subject service and workflow suites,
  publication BDD paths, incremental publication ladder, and complete root and
  workstation suites.

Cut exit condition:

- [x] Shared subject semantic values have one dependency-light owner; legacy
  imports remain identity-compatible; DST reaches no subject-domain root
  module and retains only its explicit live-controller adapter dependency; and
  no persistence, controller, model, governance, or workflow behavior moved.

Cut 15 qualification evidence:

- [x] The independent pre-cut/new differential passed 43 cases with digest
  `5afac2a94e1a7790e4fcbed0d66012e01a037241647f976e703a85ae3b504934`.
  It covered subject identity, itemization/session values, decision
  frame/review values, transformation candidates, malformed-input exceptions,
  stable IDs, sort transitions, and deterministic multi-candidate projection.
- [x] The focused package and compatibility suite passed 84 tests; all 63 DST
  tests and 23 focused itemization/decision-review tests passed.
- [x] Before baseline promotion, the measured graph retains 30 components and
  98 package edges while combined edges fall from 601 to 591 and grandfathered
  observations fall from 514 to 504. DST root reach falls from four modules to
  only `runtime_controller_api`; cyclic, forbidden, undeclared, facade-import,
  and wildcard regression sets remain empty. The checker reports only the two
  intentional, not-yet-promoted model-facade classifications.
- [x] Both semantic and DST sdist-to-wheel builds passed. The semantic wheel
  contains `decision_review.py`, `itemization.py`, and
  `transformation_constructs.py`; the repository-root-free DST import advances
  through every subject semantic dependency and fails first at
  `runtime_controller_api`, the remaining live-controller adapter.
- [x] The promoted ratchet passes with 30 components, 128 owned root modules,
  one owned root package family, 98 package edges, 504 grandfathered
  observations, and no cyclic nodes or cyclic internal edges.
- [x] Qualification passed 16 core-semantics tests, all 63 DST tests, 23
  focused itemization/decision-review tests, 133 architecture, compatibility,
  hygiene, metadata, and portability tests, 17 subject-service API and gRPC
  tests, all 123 subject-workflow tests, all 34 deterministic publication BDD
  paths, and the incremental same-subject publication ladder. The complete
  root suite passed 830 tests. The complete workstation suite passed 613 tests
  with one expected skip.
- [x] A7.15.1 through A7.15.6 held without qualification. The extraction moved
  shared values and deterministic projection only; corpus persistence, live
  controller interaction, workflow behavior, governance, and model behavior
  remain with their existing owners.

#### Phase 7 Cut 16 - Invert The Live DST Controller Bootstrap

Measured scope and falsifiable assumptions:

- [x] **A7.16.1:** DST owns prompt construction, governed proposal
  orchestration, normalization, and projection, but it does not own selection
  or construction of the application controller runtime. If live DST behavior
  depends on any additional repository-root implementation concern, stop and
  identify that concern before changing the boundary.
- [x] **A7.16.2:** Preserve the public live-DST function names and all
  deterministic DST behavior. The only supported signature extension is an
  explicit caller-provided controller-bootstrap port; a missing port must fail
  closed with a precise boundary error rather than importing a composition
  root dynamically.
- [x] **A7.16.3:** Supply the bootstrap through the existing subject-workflow
  host-actions seam. `subject_core` may select when decision support is needed,
  while `runtime_core` realizes the controller bootstrap; neither DST nor the
  subject domain may import `runtime_controller_api`.
- [x] **A7.16.4:** Preserve existing subject action keys, labels, status text,
  timeout behavior, deterministic fallback, proposal IDs, persisted decision
  values, report-plan updates, and test patch points.
- [x] **A7.16.5:** Do not replace the DST root dependency with a new
  `runtime_core` root dependency. Extend the existing controller-runtime
  provider port for subject scope, keep the concrete bootstrap dependency at
  the root composition layer, and require no new component edge or cycle.
- [x] **A7.16.6:** Do not move live decision-support orchestration into
  `subject_core`, hide the dependency with a lazy import, register mutable
  global callbacks, or make the unavailable host-actions implementation
  silently provide a controller.
- [x] Add an explicit DST controller-bootstrap protocol and fail-closed missing
  realization error; thread the port through live pipeline and live construct
  discovery without changing their result models.
- [x] Extend the subject host-actions contract with the live decision-support
  bootstrap operation and implement it in the workstation runtime adapter.
- [x] Add boundary tests for exact argument forwarding, fail-closed unavailable
  composition, injected fake-controller behavior, public API stability, and
  repository-root-free DST import.
- [x] Prove behavior equivalence against the preserved pre-cut implementation
  before promoting the architecture baseline.
- [x] Rebuild DST from sdist to wheel and prove that `import dst` succeeds with
  the repository root absent from `sys.path`.
- [x] Promote the graph only after the final DST root dependency is absent and
  every cycle, forbidden, undeclared, compatibility-facade, canonical-facade,
  and wildcard regression set remains empty.
- [x] Run DST, runtime adapter, subject workflow and service, publication BDD,
  architecture and hygiene, full root, and full workstation qualification.

Cut exit condition:

- [x] DST is an independently importable package with no repository-root
  implementation dependency; live controller selection remains explicit at
  the runtime composition boundary; and subject behavior is unchanged.

Cut 16 qualification evidence:

- [x] The independent pre-cut/new differential passed all eight cases with
  digest `f6e1fc4a197a00e6e3985ecbffb4de33829ec06bbb5f61de3294fe2cfc8e7e18`.
  It covered all seven packaged use cases plus live construct discovery while
  giving the old and new implementations the same fake controller bootstrap.
- [x] Fresh sdists and wheels were built for `realized-core-semantics`,
  `coordinated-transformation`, and `dst`. In an isolated Python 3.14
  environment outside the checkout, the installed DST wheel loaded all seven
  packaged fixtures, constructed a discovery prompt packet, exposed exactly
  94 public names, and did not load `runtime_controller_api`.
- [x] The promoted ratchet passes with 30 components, 128 owned root modules,
  one owned root package family, 98 package edges, 504 grandfathered
  observations, 591 combined edges, and no cyclic nodes or cyclic internal
  edges. The former `dst -> runtime_controller_api` package-to-root edge is
  absent; the concrete dependency is now the explicit same-owner composition
  edge `controller_entrypoints -> runtime_controller_api`.
- [x] Qualification passed all 64 DST tests, 22 runtime-adapter and contract
  tests, 132 architecture/compatibility/hygiene/metadata/portability tests,
  17 subject-service API and gRPC tests, all 123 subject-workflow tests, all 34
  deterministic publication BDD paths, and the incremental same-subject
  publication ladder. The complete root suite passed 830 tests after graph
  promotion, and the complete workstation suite passed 615 tests with one
  expected skip.
- [x] A7.16.1 through A7.16.6 held without qualification. Controller selection
  moved behind an explicit caller-provided port; no decision-support behavior,
  workflow label, persisted value, fallback, timeout, or patch point moved.

#### Phase 7 Cut 17 - Make Decision Review Persistence Package-Native

Measured scope and falsifiable assumptions:

- [x] **A7.17.1:** The remaining root `decision_review` module is a cohesive
  subject-domain leaf: it persists decision frames and review items and maps a
  review-composition item into the dependency-light values already owned by
  `realized_core_semantics.decision_review`. If it owns controller, model,
  governance, or presentation behavior, stop and split that concern first.
- [x] **A7.17.2:** Move this leaf before its lower `review_composition` and
  learning-context dependencies. Those existing package-to-root observations
  may remain temporarily, but this cut may add no new package-to-root category,
  component dependency, or combined cycle.
- [x] **A7.17.3:** Preserve `decision_review` as a true module alias to
  `workstation.subject.core.decision_review`. Existing imports, object identity,
  and historical pickle-global lookup must resolve to the canonical objects.
- [x] **A7.17.4:** Preserve decision-frame and review-item paths, JSON shape,
  stable identifiers, ordering, stale-file removal, normalization, timestamps,
  and exception behavior exactly.
- [x] **A7.17.5:** Keep shared decision values in `realized_core_semantics`; do
  not recreate them in `subject_core` or make DST depend upward on workstation
  behavior.
- [x] **A7.17.6:** Build and inspect the subject-core distribution, but do not
  claim isolated subject-core importability while its measured lower subject
  modules remain at repository root.
- [x] Move the root implementation unchanged into
  `workstation.subject.core.decision_review`, update package-owned callers to
  the canonical module, and retain the historical root alias.
- [x] Add exact module-identity, pickle-compatibility, import-hygiene, and wheel
  content coverage.
- [x] Prove persistence and mapping equivalence against the preserved pre-cut
  implementation before promoting the architecture baseline.
- [x] Qualify direct decision-review behavior, subject workflow and service,
  architecture and hygiene, publication BDD paths, and incremental publication
  before selecting the next leaf.

Cut exit condition:

- [x] Decision-review persistence and mapping have one package-native owner;
  the historical root import is identity-compatible; no new dependency or
  cycle is accepted; and persisted subject behavior is unchanged.

Qualification evidence:

- The preserved pre-cut implementation and package-native implementation
  produced identical decision-review mappings, stable identifiers, persisted
  paths, JSON bytes, reload order, and stale-file removal; the deterministic
  comparison digest was
  `2d39b72e44002ac8d51045355562be21bd48b4a3e5ab588392b32a7f5689257e`.
- The `realized-workstation-subject-core` wheel contains
  `workstation/subject/core/decision_review.py`. Distribution hygiene proves
  package callers do not import the root facade, while compatibility coverage
  proves exact module identity and historical pickle-global lookup.
- Direct and compatibility tests passed 113 cases, subject workflow passed 123,
  subject service passed 17, publication and incremental publication passed 35,
  and the full workstation suite passed 618 with one expected skip. The full
  root suite ran 831 cases before baseline promotion with only the two expected
  stale-baseline observations, then passed all 831 cases after promotion. The
  promoted graph has no cycles and four fewer grandfathered observations.

#### Phase 7 Cut 18 - Make Transformation-Construct Persistence Package-Native

Measured scope and falsifiable assumptions:

- [x] **A7.18.1:** The remaining root `decision_review_constructs` module is a
  cohesive subject-domain leaf: package-neutral candidate values and
  deterministic item projection already belong to
  `realized_core_semantics.transformation_constructs`; the root module retains
  only subject-corpus paths and JSON persistence. If controller, governance,
  model, or presentation behavior is found, stop and split it first.
- [x] **A7.18.2:** Moving this leaf into `subject_core` may retain its existing
  lower learning-context dependency temporarily, but may add no dependency
  category, component edge, or combined cycle.
- [x] **A7.18.3:** Preserve `decision_review_constructs` as a true module alias
  to `workstation.subject.core.decision_review_constructs`. Historical imports,
  semantic-value identity, and pickle-global lookup must continue to resolve.
- [x] **A7.18.4:** Preserve candidate directory paths, JSON shape and bytes,
  stable ordering, normalization, malformed-file handling, stale-file removal,
  and exception behavior exactly.
- [x] **A7.18.5:** Keep candidate semantics and deterministic item projection in
  `realized_core_semantics`; do not duplicate them in `subject_core`.
- [x] **A7.18.6:** Build and inspect the subject-core distribution without
  claiming isolated subject-core importability while lower subject persistence
  modules remain at repository root.
- [x] Move only corpus path and persistence behavior into
  `workstation.subject.core.decision_review_constructs`, update package-owned
  callers, and retain the historical root alias.
- [x] Add exact module-identity, pickle-compatibility, import-hygiene, and wheel
  content coverage.
- [x] Prove persistence equivalence against the preserved pre-cut module before
  promoting any architecture baseline change.
- [x] Qualify transformation-construct behavior, subject workflow and service,
  architecture and hygiene, publication BDD paths, and incremental publication.

Cut exit condition:

- [x] Transformation-construct persistence has one package-native owner; the
  historical root import is identity-compatible; no new dependency or cycle is
  accepted; and persisted subject behavior is unchanged.

Qualification evidence:

- The preserved pre-cut and package-native modules produced identical stable
  candidate identifiers, paths, serialized JSON bytes, load/list ordering,
  malformed-file handling, missing-record values, and stale-file removal. The
  deterministic comparison digest was
  `3db282c1bbc0c6f0a58aa0ba2ccec2d5c1d007b619e9c7bfdb70f305ac051378`.
- The subject-core wheel contains
  `workstation/subject/core/decision_review_constructs.py`; distribution guards
  reject both historical decision-review imports, and compatibility coverage
  proves exact root-module identity, semantic-value identity, and historical
  pickle-global lookup.
- Compatibility and distribution tests passed 73 cases, subject workflow 123,
  subject service 17, publication and incremental publication 35, and the
  Textual compatibility surface 171. The architecture suite's only
  pre-promotion difference was the planned facade transition; promotion removed
  two grandfathered observations without introducing a cycle.

#### Phase 7 Cut 19 - Make Review Composition Package-Native

Measured scope and falsifiable assumptions:

- [x] **A7.19.1:** `review_composition` is one cohesive subject-domain
  responsibility: review-composition values, deterministic item projection and
  tree transformations, and their corpus persistence. It contains no model,
  controller, governance, host, transport, or presentation behavior. If any is
  found, stop and split that behavior before moving the module.
- [x] **A7.19.2:** Its root `itemize` dependency supplies only
  `ItemizationSession` and `ItemizedSubjectItem`, whose canonical identities
  already live in `realized_core_semantics.itemization`; use those identities
  directly rather than retaining a package-to-facade edge.
- [x] **A7.19.3:** The existing lower `learning_context` dependency may remain
  temporarily. This cut may add no dependency category, component edge, or
  combined cycle.
- [x] **A7.19.4:** Preserve `review_composition` as a true module alias to
  `workstation.subject.core.review_composition`. Historical imports, class and
  function identity, and pickle-global lookup must continue to resolve.
- [x] **A7.19.5:** Preserve record schemas and hashes, stable identifiers,
  source-to-review projection, inclusion and ordering, split/merge/promote tree
  semantics, corpus paths, JSON bytes, malformed-file handling, receipt order,
  stale-file removal, timestamps, and exception behavior exactly.
- [x] **A7.19.6:** Build and inspect the subject-core wheel without claiming
  isolated subject-core importability while learning-context and itemization
  application modules remain at repository root.
- [x] Move the complete cohesive module into
  `workstation.subject.core.review_composition`, replace its value-only itemize
  import with the canonical semantic package, update package-owned callers, and
  retain the root alias.
- [x] Add exact module-identity, pickle-compatibility, import-hygiene, and wheel
  content coverage.
- [x] Prove representative persistence, projection, and tree-transform
  equivalence against the preserved pre-cut implementation.
- [x] Qualify the dedicated review-composition and decision-review suites,
  subject workflow and service, architecture and hygiene, publication BDD
  paths, and incremental publication.

Cut exit condition:

- [x] Review composition has one package-native owner; the historical root
  import is identity-compatible; the itemize facade edge is absent; no new
  dependency or cycle is accepted; and persisted subject behavior is unchanged.

Qualification evidence:

- The preserved pre-cut and package-native implementations produced identical
  record hashes, item projection, split/merge/promote results, paths, exact JSON
  bytes, malformed-file handling, stale-file removal, tree flattening, and
  receipt order. The deterministic comparison digest was
  `b867c186d8b773cc3767dd84bec2ae3f1812777ec3628a63789cb643963c71a8`.
- The subject-core wheel contains
  `workstation/subject/core/review_composition.py`. Package import guards reject
  the root facade; compatibility tests prove exact module identity and
  historical class and function pickle-global lookup.
- Dedicated review, decision, publication, compatibility, and distribution
  coverage passed 122 cases; subject workflow passed 123, subject service 17,
  and publication and incremental publication 35. The only pre-promotion
  architecture difference was the planned root alias edge; promotion removed
  three grandfathered observations and introduced no cycle.

#### Phase 7 Cut 20 - Give Markdown IR A Shared Semantic Owner

Measured scope and falsifiable assumptions:

- [x] **A7.20.1:** `markdown_ir` is a cohesive dependency-free semantic
  representation and deterministic interpretation module. It owns Markdown
  section/document values, parsing, bounded prompt views, symbolic mappings,
  aliases, questions, and normalization; it performs no I/O, persistence,
  model invocation, controller decision, governance, host effect, transport, or
  workstation behavior.
- [x] **A7.20.2:** Because controller, subject-core, and subject-service
  consumers share it, the correct owner is an internal
  `realized_core_semantics.markdown` module, not a new one-file UV project and
  not an upward dependency on `workstation.subject.core`.
- [x] **A7.20.3:** Preserve `markdown_ir` as a true module alias to the canonical
  semantic module. Historical imports, value/function identity, and
  pickle-global lookup must continue to resolve.
- [x] **A7.20.4:** Preserve all parsed IR values, ordering, bounded views,
  symbolic mappings, aliases, questions, normalization, placeholder detection,
  and exception behavior exactly; this cut must not revise Markdown semantics.
- [x] **A7.20.5:** Update production consumers to the canonical import, with no
  new component edge, dependency category, or combined cycle.
- [x] **A7.20.6:** Build and import the core-semantics wheel outside the source
  tree and prove that the canonical Markdown module is included without pulling
  root or workstation modules into the distribution.
- [x] Move the implementation unchanged into
  `realized_core_semantics.markdown`, retain the root alias, and migrate
  production imports.
- [x] Add exact module-identity, pickle-compatibility, distribution-content,
  and import-hygiene coverage.
- [x] Qualify Markdown IR, Markdown artifact generation, itemization, learning
  capture, architecture and hygiene, subject workflow, and publication paths.

Cut exit condition:

- [x] Markdown IR has one shared dependency-light owner; historical imports are
  identity-compatible; package consumers no longer import the root facade; and
  deterministic Markdown behavior is unchanged.

Qualification evidence:

- The preserved root implementation and package-native implementation produced
  identical document/section parsing, cluster and encounter views, bounded
  prompts, expression mappings, contract projections, aliases, questions,
  merge behavior, constants, and normalization results. The deterministic
  comparison digest was
  `b5afcf83b7cfb6830149aeb44e62e194d4c2fa4e31db7ea46c2ac5ec24b7adb6`.
- The independently built core-semantics wheel contains
  `realized_core_semantics/markdown.py`. A Python 3.14 environment installed
  only from that wheel parsed representative Markdown through its 42-name
  explicit API without loading `markdown_ir` or repository-root modules.
- Focused semantic, artifact-generation, itemization, learning, capture,
  compatibility, and distribution coverage passed 156 cases. Subject workflow
  passed 123, subject service 17, and publication plus incremental publication
  35. The architecture suite's only pre-promotion failure was the planned root
  facade transition; promotion reduced grandfathered observations from 495 to
  490 and introduced no cycle.

#### Phase 7 Cut 21 - Invert Direct Itemization Proposal Execution

Measured scope and falsifiable assumptions:

- [x] **A7.21.1:** The only controller-owned behavior in `itemize` is the direct
  LLM proposal request. Prompt construction, schema and fallback payloads,
  candidate verification, normalization, merging, and persistence remain
  itemization-domain behavior. If another controller dependency is found, stop
  and expand the port deliberately before relocating itemization.
- [x] **A7.21.2:** A narrow subject-domain proposal port can represent this
  effect using a request method and an immutable proposal result. The port may
  carry semantic-unit, policy, target, instructions, fallback, and schema
  values, but it may not expose controller instances or runtime state.
- [x] **A7.21.3:** The workstation runtime adapter remains responsible for
  bootstrapping the configured controller and mapping the itemization request to
  `NOT_DECOMPOSITION` in `DEEP` mode. The subject package must not import the
  controller bootstrap or proposal implementation.
- [x] **A7.21.4:** Preserve the exact prompt, fallback/schema payloads, proposal
  type and mode, proposal identifiers and source metadata, 12-candidate bound,
  exception-to-empty behavior, deterministic fallback, and disabled-policy
  behavior.
- [x] **A7.21.5:** During this inversion cut, historical direct calls through
  root `itemize` retain their existing controller-backed default. The subject
  workflow explicitly supplies its composed host-actions port; no global
  subject-domain provider is introduced.
- [x] Add the immutable itemization-proposal result and outbound protocol to the
  existing subject host-actions boundary, including a fail-closed unavailable
  implementation.
- [x] Implement the proposal operation in the runtime subject-host adapter using
  the already registered controller-runtime provider.
- [x] Parameterize direct itemization extraction and materialization over the
  port, preserve the root default adapter for this cut, and inject host actions
  from subject workflow orchestration.
- [x] Add contract and adapter tests, migrate workflow/BDD tests to the injected
  seam, and qualify itemization, subject workflow, API, publication, and
  architecture behavior before moving the implementation.

Cut exit condition:

- [x] Itemization-domain code can execute all deterministic paths without a
  controller dependency and can request optional direct decomposition only
  through an injected typed port; controller construction remains outside the
  subject domain and existing behavior is unchanged.

Qualification evidence:

- Direct itemization now consumes a structural proposal port. The subject host
  boundary returns an immutable controller-neutral value, and the workstation
  runtime adapter alone maps that request to `NOT_DECOMPOSITION` in `DEEP` mode
  through the configured controller-runtime provider.
- The historical root default remains covered by the original itemization tests,
  while workflow and BDD tests now patch the injected runtime provider rather
  than the former internal bootstrap symbol. Exact prompt, schema, fallback,
  proposal metadata, disabled behavior, and deterministic fallback assertions
  remain green.
- Focused itemization, host-boundary, and report BDD coverage passed 55 cases;
  the two affected Textual paths passed; subject workflow passed 123, subject
  service 17, and publication plus incremental publication 35. Architecture
  and hygiene passed 139 cases with 98 component edges, 490 grandfathered
  observations, and no cycle or baseline change.

#### Phase 7 Cut 22 - Make Itemization Application Behavior Package-Native

Measured scope and falsifiable assumptions:

- [x] **A7.22.1:** After Cut 21, `itemize` owns one cohesive subject-domain
  responsibility: deterministic candidate extraction, continuity-aware refresh,
  itemization-session persistence, and optional proposal-result interpretation.
  It contains no remaining controller, provider, governance, host, transport,
  or presentation behavior once the historical default adapter is removed.
- [x] **A7.22.2:** The existing root `learning_context` dependency may remain
  temporarily because learning context is the next lower subject-domain cluster.
  This cut may add no dependency category, component edge, or combined cycle.
- [x] **A7.22.3:** Canonical itemization fails closed when optional direct
  decomposition is enabled without an injected proposal port. The historical
  root API preserves its former implicit controller bootstrap through a narrow
  compatibility adapter; package callers always inject the subject host port.
- [x] **A7.22.4:** Because the historical default is executable adapter behavior,
  root `itemize` cannot be an exact module alias in this cut. Shared semantic
  values and unwrapped functions retain canonical identity; the two
  proposal-aware entry functions are behavior-preserving wrappers.
- [x] **A7.22.5:** Preserve stable identifiers, extraction ordering and merging,
  confidence and metadata, continuity matching, manual/split/merge edits,
  timestamps, paths, exact JSON, stale-file removal, fallback behavior, and
  exception behavior.
- [x] **A7.22.6:** Build and inspect the subject-core wheel, but do not claim
  isolated package importability while canonical learning context remains at
  repository root.
- [x] Move the cohesive implementation to
  `workstation.subject.core.itemization`, remove controller/proposal-enum imports
  from it, migrate package-owned callers, and retain a root compatibility
  adapter for historical direct calls.
- [x] Add explicit canonical exports, compatibility identity and wrapper tests,
  package import-hygiene guards, wheel-content coverage, and historical pickle
  lookup coverage.
- [x] Prove representative extraction, persistence, continuity refresh, direct
  proposal, deterministic fallback, and disabled-path equivalence against the
  preserved pre-cut implementation.
- [x] Qualify itemization, decision review, review composition, subject workflow
  and service, Textual integration, publication BDD, architecture, and package
  distribution behavior.

Cut exit condition:

- [x] Itemization application behavior has one package-native subject owner;
  canonical code receives proposal effects only through a port; the root path
  preserves historical behavior without becoming a canonical dependency; and
  persisted and rendered workflow behavior is unchanged.

Qualification evidence:

- The preserved pre-cut and canonical implementations produced identical
  deterministic Markdown extraction, direct-proposal interpretation,
  empty-proposal fallback, disabled operation, continuity-preserved human
  rephrasing, session/item values, and exact persisted JSON. The deterministic
  comparison digest was
  `aad2bc5f8087dd611d8e1142e5aba491085811a9c51453e060aa1ffca24e4cbf`.
- The subject-core wheel contains
  `workstation/subject/core/itemization.py` and no controller-bootstrap or
  proposal-implementation module. Canonical import guards reject root
  `itemize`, `runtime_controller_api`, and `applied_theory_types`; the root
  adapter preserves semantic-value identity, unwrapped function identity,
  historical pickle lookup, and implicit-controller behavior.
- Focused itemization, decision, review, compatibility, distribution, and host
  coverage passed 113 cases; subject workflow passed 123, subject service 17,
  Textual 171, and publication plus incremental publication 35. The only
  pre-promotion architecture failure was the planned facade transition;
  promotion reduced grandfathered observations from 490 to 488 without a new
  component edge or cycle.

#### Phase 7 Cut 23 - Make Learning Context Package-Native Before Its Paths

Measured scope and falsifiable assumptions:

- [x] **A7.23.1:** `learning_context` is one cohesive subject-domain aggregate:
  learning units, deltas and operations, sources, imports, reasoning scope,
  context normalization, deterministic delta application, and their corpus
  persistence and indexes. It contains no model, controller, governance,
  transport, host-effect, or projection implementation. The historical root
  persistence operation also regenerated document and skill projections; that
  coordination is retained outside the package aggregate rather than pulling
  presentation and skill compilation into the domain module.
- [x] **A7.23.2:** `learning_context_paths` must remain at root for this cut.
  Moving paths first would create a combined cycle while package modules still
  consume root `learning_context`; moving the aggregate first preserves the
  existing one-way `subject_core -> learning_context_paths` transitional edge.
- [x] **A7.23.3:** Package-owned consumers import canonical aggregate values,
  normalization, loading, and delta behavior directly without adding a
  component edge, dependency category, or combined cycle. Subject service and
  workstation runtime retain the root persistence coordinator only where the
  historical projection side effects remain required.
- [x] **A7.23.4:** Preserve schema versions, dataclass fields/defaults,
  normalization, stable identifiers and hashes, delta-operation validation and
  application, source bundles, import slices, reasoning scopes, lookup keys,
  indexes, paths, exact JSON, ordering, timestamps, and exception behavior.
- [x] **A7.23.5 (revised after measurement):** An exact module alias cannot
  preserve both a projection-free aggregate and the historical
  persist-and-project operation. Preserve root `learning_context` as a narrow
  coordinator: every canonical value and non-coordinating function keeps
  package identity and historical pickle lookup, while only
  `persist_learning_context` composes package persistence with the existing
  deterministic projection implementations.
- [x] **A7.23.6:** Build and inspect the subject-core wheel, but do not claim
  isolated package importability until the subsequent paths cut removes the
  final learning-context root dependency.
- [x] Move the complete aggregate into
  `workstation.subject.core.learning_context`, migrate package-owned consumers,
  add an explicit canonical API, and retain the narrow root projection
  coordinator.
- [x] Add value-identity, adapter-distinction, pickle-compatibility,
  import-hygiene, explicit-export, projection-separation, and wheel-content
  coverage.
- [x] Prove representative value normalization, every delta operation family,
  source/import/context persistence, indexes, lookup, reasoning scope, and exact
  persisted-byte equivalence against the preserved pre-cut implementation.
- [x] Qualify learning-context, itemization, decision/review, subject workflow
  and service, publication BDD, architecture, and distribution behavior.

Cut exit condition:

- [x] Learning-context meaning and authoritative JSON/index persistence have one
  package-native subject owner; package consumers use it directly for domain
  behavior; the root coordinator preserves historical document/skill projection
  behavior; the lower root paths module remains the next explicit cut; and no
  persisted, projected, or workflow behavior changes.

Qualification evidence:

- The preserved pre-cut implementation and the transitional root coordinator
  produced identical normalized values, stable identifiers, constructor
  semantics, all ten explicit delta-operation families, legacy delta behavior,
  source bundles, subject imports, reasoning scope, lookup behavior, rendered
  projections, and complete persisted file trees. The deterministic comparison
  digest was
  `467d638abd118f2a689eca44afe5a72c72cea51fc3d1018f65b6997f07ba0c8f`.
- The subject-core wheel contains
  `workstation/subject/core/learning_context.py`. Static distribution guards
  require its explicit API and reject imports of document projection, skill
  projection, skill compiler, and skill export implementations. Isolated wheel
  importability is intentionally not claimed before the paths cut.
- Learning-context, projection, capture, compatibility, and distribution seams
  passed 104 cases; affected itemization, delta, decision, review, controller,
  and Markdown suites passed 77; subject workflow passed 123; subject API 17;
  and publication plus incremental publication passed 35.
- The only pre-promotion architecture difference was the planned one-way root
  coordinator dependency on `subject_core`. Promotion reduced grandfathered
  observations from 488 to 486 while preserving 98 component edges and zero
  combined cycles.

#### Phase 7 Cut 24 - Make Subject Corpus Paths Package-Native

Measured scope and falsifiable assumptions:

- [x] **A7.24.1:** `learning_context_paths` is a dependency-light subject-domain
  path vocabulary. It owns no persistence, projection, governance, controller,
  model, host-effect, or UI behavior.
- [x] **A7.24.2:** Moving paths after the aggregate removes the transitional
  `subject_core -> learning_context_paths` root dependency without creating a
  reverse package edge or combined cycle.
- [x] **A7.24.3:** Preserve exact root resolution precedence: explicit override,
  `LEARNING_CONTEXT_ROOT`, source parent, then resolved current directory.
- [x] **A7.24.4:** Preserve subject-id canonicalization, user expansion,
  absolute resolution, every corpus/review/source-bundle path key and spelling,
  and the exact directory set created by `ensure_learning_context_home`.
- [x] **A7.24.5:** Root `learning_context_paths` can become an exact module alias;
  root `learning_context` and `decision_review` must continue exposing the same
  function objects and historical pickle globals.
- [x] Move the complete path vocabulary into
  `workstation.subject.core.learning_context_paths`, migrate canonical package
  and root projection consumers, expose an explicit public API, and retain the
  exact root alias.
- [x] Add module-identity, pickle-compatibility, import-hygiene, explicit-export,
  wheel-content, precedence, path-map, and directory-materialization coverage.
- [x] Differentially prove all path outputs and environment branches against
  the preserved pre-cut implementation.
- [x] Qualify learning-context, projection, itemization, decision/review,
  subject workflow and service, publication BDD, architecture, and distribution
  behavior.

Cut exit condition:

- [x] Subject corpus and decision-review path construction have one
  package-native owner; all canonical consumers use it; historical root
  imports preserve exact module/function identity; the subject-core package no
  longer depends on a root learning-context implementation or path module; and
  persisted locations and workflow behavior are unchanged.

Qualification evidence:

- The preserved root implementation and package-native owner produced identical
  subject identities, explicit/environment/source/current-directory root
  precedence, corpus/home/review/context/source-bundle path maps, and exact
  created directory trees. The deterministic comparison digest was
  `2f5bed8b7466bd9803d29150678f8fb2a247a2119df5d5f0f2a8d3eb2bb7bc9c`.
- The subject-core wheel contains both
  `workstation/subject/core/learning_context.py` and
  `workstation/subject/core/learning_context_paths.py`; distribution guards
  reject package imports of either historical root path and require the exact
  eight-name path API.
- Focused learning-context, projection, decision, compatibility, and
  distribution coverage passed 102 cases; affected itemization, delta,
  decision/review, controller, and Markdown suites passed 77; subject workflow
  passed 123; subject API 17; and publication plus incremental publication 35.
- Promotion replaced the transitional component-to-root path dependency with
  exact root aliases pointing inward to `subject_core`, reduced grandfathered
  observations from 486 to 485, preserved 98 component edges, and introduced
  no combined cycle.

Exit condition:

- [x] The subject workflow package can be installed and tested without loading
  canonical learning, itemization, review, or publication implementations from
  repository root.

Phase exit evidence:

- The built wheel contains every package-native subject implementation and path
  module established by the reverse-topological cuts. Importing every
  `workstation.subject.core` submodule in a fresh interpreter loaded none of the
  historical root learning-context, itemization, decision-review,
  review-composition, or publication module names.

### Phase 8 - Give Blend A Canonical Domain Boundary

#### Phase 8 Ownership And Direction Model

The Blend boundary is one cohesive domain project, not one project per theory
term. Its internal modules separate domain values, application contracts, and
adapters while retaining one public semantic API.

- `realized_blend` owns context, operator descriptors and applicability,
  sessions, worlds, workflow plans/runs, authoritative history references,
  coordination state, and execution observations.
- `realized_core_semantics` and `realized_skill_semantics` remain the lower
  owners of general semantic values and portable skill meaning. Blend may
  reference those contracts but does not admit skills or execute them.
- governance owns permission, admission, approval, authority, and policy
  decisions. Blend records policy requirements and decision references but
  does not make those decisions.
- runtime and workstation adapters implement operator discovery, concrete
  invocation, host effects, and filesystem persistence through Blend ports.
- workstation foundation projections and UI own presentation derivation. They
  depend on Blend values; Blend never imports their view or widget types.
- controller owns goal decomposition and agent orchestration. It may propose
  Blend workflow plans but does not own Blend workflow truth.
- event buses transport best-effort lifecycle observations. Persisted world,
  plan, run, history, and coordination records remain authoritative.

Theory-layer ownership is therefore:

| Blend layer | Canonical owner | Inward dependency rule |
| --- | --- | --- |
| DNA | semantic/skill domains plus Blend world and workflow records | persistence implements ports over canonical values |
| RNA | semantic and portable-skill domains | Blend consumes reflective contracts only |
| Operators | Blend descriptors/catalog contracts | runtime adapters supply and invoke concrete operators |
| Context | Blend | workstation translates session state into context |
| UI abstraction | workstation projections/UI | presentation depends on Blend, never the reverse |
| Actor | governance identity plus Blend actor/session references | presentation and runtime translate concrete actors |
| Session | Blend | workstation session is an adapter source, not the domain type |
| Workflow | Blend | controller proposes and runtime executes through ports |
| Policy | governance | Blend carries requirements and decision references only |
| History | Blend history contracts over authoritative records | receipts/events may be referenced, not treated as reconstructed truth |
| Coordination | Blend state contracts with governance enforcement | workstation presents and submits coordination operations |
| Agent orchestration | controller | orchestration emits explicit Blend plans and limits |

#### Phase 8 Cut Sequence

##### Phase 8 Cut 25 - Establish The Dependency-Light Blend Domain Package

Measured scope and falsifiable assumptions:

- [x] **A8.25.1:** Context, operator descriptors/applicability, session values,
  world values, workflow values, history references, coordination values, and
  execution observations can be represented without workstation, runtime,
  governance implementation, event transport, filesystem, or UI imports. If a
  value requires one of those imports, split the value from its adapter before
  moving it.
- [x] **A8.25.2:** One `realized-blend` UV project is cohesive because these
  values jointly implement the Blend world/work contract and share lifecycle
  invariants. Do not create a project per module.
- [x] **A8.25.3:** Workstation-to-Blend context/session translation is adapter
  behavior and must move to the workstation runtime boundary. Historical root
  functions remain compatibility wrappers during qualification.
- [x] **A8.25.4:** Skill-compose payload conversion remains a compatibility or
  workstation adapter in this cut. The canonical workflow API owns neutral
  workflow values, not `ws.*` capability vocabulary.
- [x] **A8.25.5:** Operator invocation is represented by a port. Moving the
  descriptor and applicability model must not admit abilities, grant authority,
  select a host realizer, or execute an effect.
- [x] **A8.25.6:** Execution observations are immutable, lossy notifications of
  accepted lifecycle transitions. Dropping an observer must not alter the
  authoritative workflow result or persistence outcome, and observations must
  not be sufficient to reconstruct domain truth.
- [x] **A8.25.7:** Preserve dataclass fields/defaults, normalization, ordering,
  identifier prefixes, target resolution, serialization payloads, exception
  behavior, and historical root import/pickle lookup exactly.
- [x] Create the `realized-blend` project with an explicit public module/API
  surface and isolated wheel/sdist coverage.
- [x] Move only dependency-light values and pure behavior first; retain root
  compatibility facades and adapters.
- [x] Move workstation context/session projection into an explicit runtime
  adapter and migrate package consumers to canonical imports.
- [x] Add architecture, import-hygiene, identity, pickle, differential,
  distribution, LLM-off, and observer-non-authority coverage.

Cut exit condition:

- [x] The canonical Blend value model imports no workstation, runtime,
  governance implementation, event transport, filesystem adapter, or UI code;
  historical imports remain compatible; and all existing behavior is
  unchanged.

Qualification evidence (2026-10-27):

- `realized-blend` wheel and sdist built from the workspace without build
  isolation. An isolated Python 3.14 environment imported all eleven public
  package modules from site-packages while loading no workstation or historical
  root Blend module.
- The preserved pre-cut sources and canonical package produced eleven exact
  differential equivalences for context/session projection, operator values,
  applicability and targeting, workflow/world values, and execution
  observations (`ae6cbd21e7170de0e56b203df3113ded6acad4c3367184dfa03c2042143d5414`).
- 115 Blend, compatibility, distribution, pickle-identity, and observer tests
  passed with `OPENAI_API_KEY` absent. A rejecting observer did not change the
  successful result or its canonical persisted run.
- The promoted ratchet measured 31 components, 128 owned root modules, 101
  package edges, 480 grandfathered observations, and zero package or combined
  root/package cyclic nodes.

##### Phase 8 Cut 26 - Put Workflow And World Persistence Behind Ports

- [x] Define neutral world/workflow repository protocols in `realized_blend`.
- [x] Move the existing JSON implementations behind those protocols without
  changing paths, bytes, identifiers, ordering, replacement behavior, or error
  behavior.
- [x] Inject repositories into application orchestration while retaining the
  historical root functions as compatibility entrypoints.
- [x] Prove exact persisted-tree and query equivalence, including malformed and
  missing-file behavior.

Cut exit condition:

- [x] Canonical Blend values define neutral workflow/world persistence ports;
  JSON and workstation materialization remain adapters; default persistence is
  byte-for-byte compatible; and orchestration can execute against injected
  repositories without writing the canonical JSON files.

Qualification evidence (2026-10-27):

- The committed pre-cut stores and the repository-backed compatibility paths
  produced identical workflow trees, indexes, filtered query results, world
  bytes, and missing/malformed exception types and messages
  (`04ae2b98198b9d8cda41b9f7cce32402e3ae0e8470c16d86dc03c6c097a69b5f`).
- In-memory repository doubles executed workflow persistence and workstation
  world materialization without creating `BLEND_WORKFLOW_INDEX.json`, plan/run
  JSON, or `BLEND_WORLD.json`; default adapters retained the historical paths.
- The updated wheel and sdist built successfully. An isolated Python 3.14
  environment loaded the new ports from site-packages without loading any
  workstation or historical root Blend module.
- Focused store, execution, protocol, compatibility, distribution, and public
  metadata tests passed with model access disabled; the architecture ratchet
  retained 31 components, 128 owned root modules, 101 package edges, 480
  grandfathered observations, and zero cyclic nodes.

##### Phase 8 Cut 27 - Separate Operator Catalog Adapters From Domain Query

- [x] Move generic provider, record, query, applicability, and resolution
  behavior into the canonical Blend API.
- [x] Keep artifact-to-operator and workstation-capability projection in
  runtime/workstation adapters.
- [x] Require adapters to return canonical descriptors plus opaque invocation
  handles; the Blend domain must not import capability runtime or host
  realizers.
- [x] Prove listing, filtering, precedence, step-aware resolution, target
  resolution, and actor visibility equivalence.

Cut exit condition:

- [x] Generic catalog behavior is independently installable in
  `realized_blend`; concrete artifact/capability interpretation remains in an
  adapter; and workflow execution receives an opaque handle without the domain
  importing runtime, governance, host, or workstation implementations.

Qualification evidence (2026-10-27):

- The current pre-cut implementation and canonical catalog produced exact
  equivalence for listing, normalized filtering, duplicate-ID and provider
  precedence, generic and step-aware resolution, adapter projection, opaque
  handles, and actor-visibility data
  (`c200705ff2eae6a459165ac4648e51f1aebae91e9b2689c9ffe90fc2c70c2610`).
- 109 package, catalog, adapter, workflow, and compatibility tests passed with
  model access disabled. The complete affected workstation/operator/workflow
  qualification passed 176 tests when run with its loopback-only skill-host
  bridge available; the sandboxed run was rejected only at socket bind.
- A fresh wheel and sdist built. An isolated Python 3.14 process listed a
  canonical operator from site-packages without importing the historical root
  catalog or any workstation module.
- The architecture ratchet retained 31 components, 128 owned root modules, 101
  package edges, and zero cyclic nodes while reducing grandfathered
  observations from 480 to 479.

##### Phase 8 Cut 28 - Move Workflow Orchestration Onto Explicit Ports

- [x] Define and inject composition, operator-invocation, persistence, clock,
  identifier, and observation ports before relocating orchestration.
- [x] Preserve branch, iteration, skip, halt, delegation aggregation, final
  output fallback, status shaping, persistence, and observer ordering exactly.
- [x] Keep concrete skill execution, governance decisions, host effects, and
  event publication in adapters outside the Blend domain.
- [x] Prove A19 by testing that canonical stored runs remain sufficient when
  observations are absent, duplicated, delayed, or rejected by a consumer.

Cut exit condition:

- [x] Workflow resolution and orchestration are independently installable,
  every nondeterministic or effectful dependency is supplied through an
  explicit port, the historical root API is an adapter, and lossy observations
  cannot affect authoritative run state.

Qualification evidence (2026-10-27):

- The captured pre-cut implementation and canonical orchestration produced
  exact result, stored-run, and lifecycle-event equivalence for successful
  composition, branch labels, skip with final-output fallback, iteration,
  governed halt with delegation aggregation, and generic failure
  (`867ec19381d50a794430ae4787d382a0dc1708625a66915f6602ebef19da0522`).
- 132 package, API, distribution, operator, workflow, world, persistence,
  compatibility-identity, and pickle tests passed with model access disabled.
  Package-native execution tests use deterministic clocks and identifiers and
  prove identical returned and stored truth with no observer, a duplicating
  consumer, a delayed consumer, and a rejecting consumer.
- The wheel and sdist include canonical execution and its package tests. A
  fresh isolated Python 3.14 environment executed and persisted a complete
  workflow through in-memory composition, invocation, repository, clock, and
  identifier ports without loading a historical root Blend module,
  skill-composition implementation, or workstation package.
- The architecture ratchet retained 31 components, 128 owned root modules, 101
  package edges, and zero cyclic nodes while reducing grandfathered
  observations from 479 to 475.

##### Phase 8 Cut 29 - Migrate Consumers And Close The Boundary

- [x] Migrate foundation projections and workstation runtime consumers to the
  canonical Blend API and explicit adapters.
- [x] Preserve all root Blend paths as qualified compatibility facades until a
  later stability cycle proves they are unused externally.
- [x] Build and test the Blend distribution without repository-root imports,
  then run workstation, workflow, architecture, publication, and selected real
  trial gates.
- [x] Promote the architecture baseline only for explained inward aliases and
  removed debt; do not baseline a new cycle or upward dependency.

- [x] Confirm A9 by mapping each Blend theory layer to an owner and dependency
  direction.
- [x] Define public contracts for context, operators, sessions, worlds,
  workflows, history, coordination, and execution observations.
- [x] Keep presentation derivation outside the Blend domain.
- [x] Keep concrete skill execution and host effects behind runtime ports.
- [x] Keep event transport outside the Blend truth model; events describe
  accepted lifecycle transitions rather than becoming the authoritative state.
- [x] Confirm A19 for every workflow and step event before moving its producer
  or consumer.
- [x] Replace direct dependencies on workstation model types with explicit
  adapters at the workstation boundary.
- [x] Move dependency-light Blend models first.
- [x] Move stores behind persistence ports while preserving identifiers,
  ordering, and on-disk formats.
- [x] Move workflow/operator resolution and execution orchestration only after
  their runtime and governance dependencies are explicit.
- [x] Migrate foundation projections and workstation runtime consumers to the
  canonical Blend API.
- [x] Preserve root Blend imports as compatibility facades during qualification.
- [x] Add tests for context applicability, operator resolution, workflow
  branching, iteration, halt behavior, lifecycle observations, persistence,
  replay, and receipt/event ordering.

Exit condition:

- [x] Blend can be reasoned about and tested as a domain independent of
  workstation UI and shell implementation.

Qualification evidence (2026-10-27):

- Foundation workflow projections consume canonical workflow values directly;
  workstation execution resolves and runs canonical Blend plans through the
  explicit runtime adapter rather than the historical orchestration facade.
  The adapter contract test constructs only canonical Blend values, injects an
  in-memory repository, and verifies invocation context, authoritative result,
  persistence, and lifecycle ordering.
- 132 package, API, distribution, workflow, persistence, compatibility, and
  pickle tests passed. The complete affected workstation slice passed 175
  tests with the loopback-only skill host available, and the deterministic
  publication, governed-chat, report-ladder, activity, and skill-routing trial
  bundle passed 127 tests with model access disabled.
- The wheel and sdist rebuilt successfully. A fresh isolated Python 3.14
  environment installed the wheel from local artifacts and executed and
  persisted a canonical workflow through fake ports without loading any
  workstation module or historical root Blend path.
- All 133 architecture, compatibility, layer-hygiene, and workstation import
  tests passed. The promoted ratchet measures 31 components, 128 owned root
  modules, 101 package edges, 474 grandfathered observations, and zero package
  or combined root/package cyclic nodes.

### Phase 9 - Make The Controller Engine Source-Native

- [x] Recompute the `core_engine/module_manifest.txt` closure after the semantic,
  skill, governance, LLM, runtime, subject, and Blend ownership phases.
- [x] Classify every remaining module as controller semantics, controller state,
  a controller adapter, entry/exchange, compatibility, or an unresolved foreign
  responsibility.
- [x] Stop and extract any unresolved foreign responsibility before moving the
  controller closure.
- [x] Move recursive `Not` reduction, decomposition, reuse, closure, reflection,
  contemplation, commitment, resumption coordination, and controller-owned
  state under `realized_core_engine`.
- [x] Keep runtime execution behind runtime ports, governance behind governance
  APIs, model calls behind LLM ports, and persistence behind repository ports.
- [x] Move the plain-SQLite adapter only if its dependency direction remains
  inward toward controller contracts; otherwise keep it as a composition
  adapter.
- [x] Preserve the typed `run`, `resume`, and `inspect` ABI.
- [x] Replace root canonical modules with compatibility facades in small
  clusters and verify identity after each cluster.
- [x] Remove custom root-module copying from `core_engine/setup.py` only after
  the canonical package owns the complete required closure.
- [x] Remove `module_manifest.txt` only after wheel and sdist builds derive
  exclusively from package-owned source and compatibility requirements are
  represented elsewhere.
- [x] Verify LLM-off reduction, LLM-assisted reduction, interruption,
  augmentation, redirection, realignment, branching, replay, and resumed
  execution against the accepted baseline.

Exit condition:

- [x] `realized-core-engine` builds from its own canonical source tree and has no
  production dependency on repository-root implementation modules.

Qualification evidence (2026-10-29):

- The source-native engine contains 39 canonical package modules. Its wheel and
  sdist contain no repository-root implementation module, `setup.py` copy hook,
  or `module_manifest.txt`; the isolated distribution smoke created durable
  state and plain SQLite with vector search disabled and exercised the packaged
  child-to-parent broker bridge.
- The controller obtains its default persistence implementation through the
  public repository port. Historical concrete store names remain compatibility
  exports, while workstation composition receives an explicit repository
  provider instead of importing the controller package.
- 82 engine package tests, 5 deterministic reduction/replay tests, 9 LLM
  advisory/provider-boundary tests, and 135 architecture, compatibility,
  layer-hygiene, and workstation import tests passed.
- The architecture ratchet reports 31 components, 128 classified root modules,
  113 package edges, 274 grandfathered observations, and zero package or
  combined root/package cyclic nodes. It reports no canonical package import of
  a root compatibility facade.

### Phase 10 - Converge Entry, Exchange, And Root Composition

Completed slice - skill application boundary:

- [x] Extract artifact-to-skill normalization, governed-artifact IR projection,
  and explicit composition-plan analysis/execution into the independently
  buildable `realized-skill-application` project.
- [x] Keep foreign-format compatibility import and YAML hydration in the
  entry/exchange surface; move only deterministic compatibility-envelope
  normalization into portable skill semantics.
- [x] Preserve the historical `skill_boundary_normalization`, `skill_ir`, and
  `skill_composition` import identities as compatibility aliases.
- [x] Redirect production consumers to the package-native application API and
  declare every new package dependency in project metadata and the architecture
  manifest.
- [x] Reject the initial `workstation.skills.core` owner after the combined
  graph exposed a five-node root/package cycle; do not baseline that topology.
- [x] Qualify the corrected owner through unit, compatibility, hygiene,
  deterministic routing, wheel, sdist, and isolated distribution gates.

Qualification evidence (2026-10-29):

- The wheel and sdist contain only `realized_skill_application` source and run
  with the repository absent from `sys.path`. The isolated verifier projected
  canonical IR, synthesized normalization, loaded composition execution, ran
  the LLM-off core smoke, and created SQLite and state outputs.
- 50 focused skill application/semantic/adapter tests, 99 compatibility and
  workstation hygiene tests, 89 affected skill/Blend/workstation/routing tests,
  and 148 architecture, facade, layer, metadata, and import-hygiene tests
  passed.
- The promoted ratchet measures 32 components, 128 owned root modules, 119
  package edges, 261 grandfathered observations, and zero package or combined
  root/package cyclic nodes. The rejected intermediate topology was never
  promoted.

Completed slice - Blend application boundary:

- [x] Extract artifact/capability-to-operator projection, skill-compose and
  workflow translation, workflow execution adaptation, and JSON workflow/world
  repositories into the independently buildable
  `realized-blend-application` project.
- [x] Keep canonical Blend values, pure resolution, and port-driven execution
  in the dependency-light `realized-blend` domain package.
- [x] Preserve the six historical root adapter modules as exact
  identity-preserving compatibility aliases.
- [x] Redirect workstation runtime consumers to the package-native application
  API and declare the dependency in UV metadata and the architecture manifest.
- [x] Qualify legacy import/pickle identity, operator/workflow/world behavior,
  workstation adaptation, isolated test composition, wheel/sdist contents, and
  repository-absent execution before promoting the graph.

Qualification evidence (2026-10-29):

- Fresh Python 3.14 environments installed and executed both the wheel and the
  source distribution with the repository absent from `sys.path`; world and
  workflow stores materialized through the package-native API.
- The full isolated distribution verifier found 13 Blend-application wheel
  entries, 25 sdist entries, no forbidden files, and preserved the combined
  LLM-off SQLite/state smoke with vector search disabled.
- 243 consolidated Blend domain/application, compatibility, workstation,
  architecture, metadata, and layer-hygiene tests passed. Blend session tests
  now configure their required artifact-repository provider explicitly rather
  than relying on unrelated import order.
- The promoted ratchet measures 33 components, 128 owned root modules, 125
  package edges, 247 grandfathered observations, and zero package or combined
  root/package cyclic nodes.

Completed slice - subject URL acquisition boundary:

- [x] Move external URL fetching, rendered-page capture, markdown extraction,
  asset acquisition, and capture-bundle shaping into the existing
  `workstation.subject.service` application boundary without changing the
  implementation.
- [x] Preserve `url_learning_capture` as an exact identity-preserving module
  alias so historical imports and monkey-patch targets continue to intercept
  package-native runtime calls.
- [x] Redirect workstation runtime consumers to the package-native module and
  declare Playwright and Trafilatura in the owning distribution.
- [x] Add subject-service distribution, architecture ownership, and Cloud Build
  guards before promoting the reduced graph.
- [x] Qualify direct capture behavior, workstation URL learn/refresh flows,
  subject and chat flows, wheel/sdist contents, and repository-absent imports.

Qualification evidence (2026-10-29):

- 112 focused capture, distribution, compatibility, and workstation tests
  passed. The broader 323-test subject/UI run passed 319 tests in the sandbox;
  its four non-URL DST cases were denied access to the historical user-home
  skill-import directory and then passed unchanged with an isolated writable
  home.
- Fresh Python 3.14 environments installed both the wheel and source
  distribution and imported the canonical capture module with the repository
  absent from `sys.path`.
- The promoted ratchet measures 33 components, 128 owned root modules, 125
  package edges, 246 grandfathered observations, and zero package or combined
  root/package cyclic nodes. The former `runtime_core -> url_learning_capture`
  package-to-root edge is gone.

Completed slice - deterministic skill-kind projection:

- [x] Move governed-artifact-to-portable-kind classification into the existing
  `realized-skill-application` owner without moving YAML parsing, file I/O,
  admission, authority, persistence, or host realization.
- [x] Preserve the historical `skill_export_projection.skill_kind_from_artifact`
  name as the exact package function and redirect canonical workstation
  consumers to the package-native API.
- [x] Declare `skills_core -> skill_application` in UV metadata and the
  architecture manifest before accepting the edge.
- [x] Add package API, distribution-content, identity, and classification tests
  for knowledge, ability, policy, approval, revocation, and incident records.
- [x] Qualify the wheel and source distribution under fresh Python 3.14
  environments with the repository absent from `sys.path`.

Qualification evidence (2026-10-29):

- The wheel and sdist both contain `projection.py`; fresh environments loaded
  the package-owned function and classified a governed ability without a
  repository-root import. The sdist was built and installed through standard
  `pip`, independent of UV workspace source mappings.
- 76 focused skill-application, exchange, skill-I/O, and workstation tests
  passed before the broader architecture qualification.
- The accepted ratchet adds only the declared
  `skills_core -> skill_application` package edge, retains zero package and
  combined root/package cyclic nodes, and corrects `review_composition` from a
  canonical-root label to its existing compatibility-facade status.

Completed slice - artifact and portable-skill exchange boundary:

- [x] Extract artifact-bundle YAML, portable-skill schema hydration, canonical
  skill bundle export/naming, and supported foreign-format translation into
  the independently buildable `realized-exchange` project.
- [x] Add a transport-neutral `SkillExchangeProvider` workstation contract and
  fail-closed host binding; register the concrete adapter only at the CLI
  composition root.
- [x] Redirect canonical root and workstation production consumers to the
  package-native API or injected contract without moving admission, authority,
  semantic selection, host realization, or execution policy.
- [x] Preserve `side`, `side_runtime_dependencies`, `skill_schema_io`,
  `skill_export_projection`, `skill_compatibility_import`, and
  `skill_compatibility_export` as exact module-identity compatibility aliases.
- [x] Declare the package and all new edges in UV metadata, Cloud Build, and
  the architecture manifest before promoting the graph.
- [x] Qualify canonical and compatibility behavior, workstation integration,
  wheel/sdist contents, and repository-absent execution.

Qualification evidence (2026-10-29):

- All 34 workspace projects built both wheels and source distributions without
  build isolation. The isolated verifier loaded the exchange wheel with the
  repository absent from `sys.path`, exercised schema hydration and bundle
  export, and preserved the LLM-off SQLite/state smoke.
- 103 contract, compatibility, and exchange tests; 167 affected workstation
  runtime/core/shell tests; 55 exchange-hygiene, skill-I/O, and compatibility
  tests; and the focused run-bundle replay suite passed. Socket-dependent tests
  were rerun outside the filesystem/network sandbox and passed unchanged.
- The promoted ratchet measures 34 components, 128 owned root modules, 133
  package edges, 217 grandfathered observations, and zero package or combined
  root/package cyclic nodes. It reports no undeclared package dependency or
  canonical production import of the six compatibility aliases. At this
  checkpoint the only remaining package-to-root implementation dependency was
  the separately scoped learning-context coordinator consumed by
  `runtime_core` and `subject_service`.

Completed slice - learning-context projection coordination boundary:

- [x] Keep authoritative `LearningContext` state, JSON/index persistence,
  projected-skill identity derivation, and deterministic subject document
  rendering in `workstation.subject.core`.
- [x] Move persist-then-project coordination and pure derived-skill document
  construction into `workstation.subject.service` without importing exchange
  serialization or compiler implementations.
- [x] Move portable-skill compilation and learning-context skill YAML
  materialization into `realized-exchange`; supply it to subject service through
  the existing `SkillExchangeProvider` composition seam.
- [x] Preserve `learning_context`, `learning_context_projection`,
  `learning_context_skill_projection`, and `skill_compiler` as exact
  module-identity compatibility aliases.
- [x] Fail before authoritative persistence when linked skills require an outer
  materializer but composition omitted it; preview-only capture remains free of
  persistence dependencies.
- [x] Declare the two exchange-to-subject package dependencies in UV metadata
  and the architecture manifest, and reject any package-to-root replacement.
- [x] Qualify persistence, projections, runtime callers, subject flows,
  publication, package contents, isolated distributions, and the combined
  architecture graph before promoting the baseline.

Qualification evidence (2026-10-29):

- 122 focused learning-context, compiler, projection, distribution, and facade
  tests passed; 194 affected runtime, host-action, capture, contract, and
  hygiene tests passed with the real loopback host bridge.
- The deterministic subject, Markdown, publication, HTTP, and gRPC sweep passed
  all 221 tests. The provider-backed Markdown qualification remains an explicit
  credentialed gate and was not used to justify this deterministic cut.
- All 34 workspace projects built wheels and source distributions. The isolated
  verifier found 17 exchange-wheel entries and 29 exchange-sdist entries with no
  forbidden files, and its LLM-off SQLite/state plus host-bridge smoke passed.
- 166 architecture, facade, package-hygiene, metadata, and distribution tests
  passed. The promoted ratchet measures 34 components, 128 owned root modules,
  135 package edges, 204 grandfathered observations, and zero package or
  combined root/package cyclic nodes. No workspace package imports a repository
  root application module.

Completed slice - governed run-bundle exchange boundary:

- [x] Move constitutional state, composition-chain, decision-flow, transcript,
  and replay-comparison projection into `realized-core-engine`, where the
  concrete controller state is owned.
- [x] Move portable skill-registry projection and its CLI adapter into
  `realized-exchange` without moving admission, lifecycle, authority, or store
  ownership.
- [x] Move governed run-bundle document construction, governance snapshotting,
  YAML rendering/loading, and state-file adaptation into `realized-exchange`.
- [x] Keep replay execution orchestration outside this cut; redirect it and CLI
  composition to canonical package APIs rather than broadening the exchange
  owner.
- [x] Preserve `constitutional_trace`, `skill_registry`, and `run_bundle_io` as
  exact module-identity compatibility aliases.
- [x] Qualify schemas, exported skill/governance content, replay receipts,
  deterministic signatures, wheel/sdist contents, and isolated package use
  before promoting the baseline.

Qualification evidence (2026-10-29):

- 153 distribution, compatibility, exchange-hygiene, runtime-hygiene, and skill
  I/O tests passed. Eight run-bundle, replay, and determinism tests passed with
  the real loopback host bridge.
- Rebuilt engine and exchange wheels/source distributions passed the isolated
  verifier. Its repository-absent smoke directly assembled a constitutional
  trace, projected a registry document, constructed a run bundle, and preserved
  the LLM-off SQLite/state and host-bridge checks.
- The promoted ratchet retains 34 components, 128 owned root modules, 135
  package edges, and zero package or combined root/package cyclic nodes while
  reducing grandfathered observations from 204 to 185.

Completed slice - package-native launch and workstation composition:

- [x] Confirm `realized-core` as the supported standalone core executable and
  keep its parser, dispatch, conversation host, and typed resumption commands
  within the `realized-core` distribution.
- [x] Add the installable `realized-workstation` executable with package-owned
  parser registration and dispatch for launch, prompt, chat, gRPC hosting,
  skill exchange, and trial validation.
- [x] Move concrete controller, artifact-repository, subject-workflow, skill
  exchange, host-realizer, and subject-scope bootstrap composition into
  `workstation.app.cli` without moving their underlying policy or behavior.
- [x] Reduce `realized-core-engine.configuration` to runtime configuration
  arguments and override application; keep aggregate entry syntax in the
  historical root `args.py` composition module.
- [x] Preserve `controller_entrypoints` callable names and
  `runtime_controller_api` module identity while directing package-native and
  canonical production consumers to their owning package APIs.
- [x] Build the workstation wheel and source distribution, exercise both
  package console scripts, compare all workstation command namespaces against
  the historical parser, and qualify the combined graph before promotion.

Qualification evidence (2026-10-29):

- The `realized-workstation` wheel and source distribution contain the command
  parser, dispatcher, concrete composition, subject-scoped runtime controller,
  and module entrypoint. Both `realized-core --help` and
  `realized-workstation --help` execute through their declared package scripts.
- 115 focused entrypoint, governed-turn, host-realizer, subject-host-action,
  distribution, and compatibility tests passed. The final affected replay,
  runtime, subject-workflow, architecture, facade, and layer-hygiene gate passed
  all 337 tests with real loopback and Unix transports.
- The promoted ratchet measures 34 components, 128 owned root modules, 141
  package edges, 177 grandfathered observations, and zero package or combined
  root/package cyclic nodes. It reports no undeclared package dependency and no
  canonical root import through a compatibility facade.

Completed slice - reusable validation infrastructure:

- [x] Extract layered validation orchestration, structured validation reports,
  disposable or RAM-backed SQLite allocation, and durable SQLite archival into
  the independently buildable, dependency-free `realized-validation` project.
- [x] Keep domain validators, trial semantics, curricula, corpora, and trial
  entry programs outside the reusable package.
- [x] Preserve `validation_ladder` and `validation_sqlite` as exact
  module-identity compatibility aliases and redirect canonical validator and
  CLI composition consumers to the package API.
- [x] Register the project in UV, Cloud Build, public-package metadata, and the
  architecture manifest without making validation support a production-domain
  owner.
- [x] Build the wheel and source distribution and qualify package contents,
  historical import identity, SQLite behavior, trial integration, and root
  package resolution before promoting the graph.

Qualification evidence (2026-10-29):

- The `realized-validation` wheel and source distribution contain only the
  dependency-free package implementation and metadata. A fresh Python 3.14
  environment imported the wheel with the repository absent from `sys.path`.
- 29 focused package, compatibility, validation-ladder, SQLite, and trial
  integration tests passed; the broader architecture and validation gate
  passed all 171 tests.
- The promoted ratchet measured 35 components, 128 owned root modules, 141
  package edges, 179 grandfathered observations, and zero package or combined
  root/package cyclic nodes.

Completed slice - package-native Markdown learning and root-role closure:

- [x] Keep subject-owned Markdown document rendering and parsing in
  `workstation.subject.core.learning_context_markdown`.
- [x] Move deterministic Markdown encounter-to-artifact shaping into
  `realized_core_engine.markdown_learning_artifact_semantics` without moving
  external document acquisition or command composition into the engine.
- [x] Move the external Markdown ingestion adapter into
  `realized_exchange.markdown_learning_pipeline` and expose explicit extension
  installation rather than relying on incidental root-module import order.
- [x] Install the optional Markdown extensions at the workstation composition
  root while preserving the historical controller entry path.
- [x] Preserve `learning_context_markdown`,
  `markdown_learning_artifact_semantics`, and
  `external_markdown_learning_pipeline` as exact module-identity compatibility
  aliases.
- [x] Classify every remaining repository-root Python module as an approved
  entrypoint, compatibility facade, or validation/trial entrypoint.
- [x] Build the affected wheel and source distributions and qualify extension
  binding, historical import identity, Markdown behavior, architecture, and
  root-role completeness before promoting the graph.

Qualification evidence (2026-10-29):

- All 163 focused engine, exchange, subject, workstation-composition,
  compatibility, Markdown-learning, and host-bridge tests passed. The three
  real-host bridge cases denied loopback access by the sandbox passed unchanged
  with the real transport enabled.
- The `realized-core-engine`, `realized-exchange`, subject-core, and workstation
  application projects built both wheels and source distributions from their
  canonical package trees.
- The promoted ratchet measures 35 components, 128 owned root modules, one
  owned root package family, 141 package edges, 170 grandfathered observations,
  and zero package or combined root/package cyclic nodes. It reports no
  undeclared package dependency, package-to-root implementation edge, canonical
  compatibility-facade import, or unclassified root Python module.

- [x] Make `realized-core` and workstation application packages the supported
  composition and launch surfaces.
- [x] Keep `main.py` only as a historical executable/import facade while it is
  supported.
- [x] Assign skill YAML hydration, compatibility import/export, artifact/skill
  bundle I/O, and schema translation to explicit entry/exchange adapters.
- [x] Assign run-bundle I/O to an explicit entry/exchange adapter.
- [x] Ensure exchange adapters translate representations but do not decide
  admission, authority, semantic commitment, or execution policy.
- [x] Move reusable validation infrastructure under a validation package or
  `scripts/` only if it is not a supported runtime API.
- [x] Keep standalone trials as entry programs rather than forcing them into
  production packages.
- [x] Remove root composition reach-through from nested runtime and workstation
  code.
- [x] Require all production package-to-package dependencies to be declared in
  project metadata and in the architecture manifest.

Exit condition:

- [x] Root production code consists only of deliberate launch facades,
  compatibility facades, and explicitly classified validation/trial entrypoints.

### Phase 11 - Retire Compatibility Paths Deliberately

The detailed, assumption-led execution plan for the deferred retirement work
is [COMPATIBILITY_FACADE_RETIREMENT_IMPLEMENTATION.md](COMPATIBILITY_FACADE_RETIREMENT_IMPLEMENTATION.md).
It treats consumer migration, support/deprecation policy, qualification, and
physical deletion as separate transitions.

- [x] Produce a machine-readable inventory of every remaining compatibility
  facade and its consumers.
- [x] Confirm that canonical production code never imports a compatibility
  facade.
- [x] Confirm that documentation and examples use only canonical APIs.
- [x] Confirm that all independently shipped distributions install and run
  without repository-root imports.
- [x] Complete at least one stable qualification cycle after the final consumer
  migration.
- [x] Announce or document removals for any facade that has become part of a
  supported external surface.
- [ ] Remove facades in separate changes from canonical implementation moves.
- [ ] Refresh the architecture baseline after each removal so the ratchet makes
  the improvement irreversible.

Completed qualification cut - compatibility inventory and retirement hold:

- [x] Add `architecture/compatibility-facades.json` as the deterministic ledger
  of every retained facade, canonical target, root dependency, static consumer,
  support status, and retirement state.
- [x] Add `scripts/check_compatibility_facades.py` and Cloud Build enforcement
  that reject inventory drift, canonical package consumers, and public
  README/example imports of root facades.
- [x] Treat every retained root facade conservatively as a supported historical
  import. Document that removal requires separate review, supported-surface
  notice, and a completed post-migration qualification cycle.
- [x] Add `scripts/verify_workspace_distributions.py` to build every registered
  project as both wheel and source distribution, inspect built Python for root
  facade imports, assemble the wheels outside the repository, and import every
  declared public module.
- [x] Correct the deterministic publication-reference entrypoint to install
  workstation application composition and inject its subject host-actions port
  explicitly. This preserves the accepted direct-decomposition behavior and
  restores all reference artifacts byte-for-byte.
- [x] Record one completed stable qualification cycle after the final consumer
  migration. Keep all facades retained until a later, separate removal change.

Qualification evidence (2026-10-29):

- The inventory records 120 retained compatibility facades and 405 static
  repository consumers, with zero canonical package consumers, zero public
  README references, and zero public example consumers.
- All 35 registered UV projects built one wheel and one source distribution;
  all 35 declared public modules imported from the assembled wheel site with
  the repository absent, and no wheel imported a root facade.
- The accepted qualification baseline resolves all 17 declared gates as passed
  with zero failures, blocks, or omitted evidence. The rerun default gates
  include 873 root tests, 633 workstation tests, three skill-routing BDD tests,
  34 publication BDD tests, incremental publication, Flutter analysis, and
  Flutter widget tests; opt-in provider/browser evidence remains preserved by
  the baseline merge mechanism.
- The publication reference retains its prior SHA-256 values for
  `reference.json`, `report.md`, and `report.typ`; no behavioral artifact delta
  was accepted to complete the architecture migration.

Completed deletion cut - first semantic exact-alias cohort (2026-10-30):

- [x] Remove the seven repository-internal exact aliases
  `applied_theory_primitives`, `boundary`, `id_generation`,
  `normalization_primitives`, `prolog`, `semantic_text`, and
  `title_semantics` without moving or changing their canonical
  `realized_core_semantics` implementations.
- [x] Remove only facade-identity assertions and root ownership/classification
  entries, retain canonical behavior comparisons, and tombstone every removed
  import with its explicit replacement.
- [x] Accept only the shrinking architecture delta: owned roots `128 -> 121`,
  combined graph nodes `164 -> 157`, combined edges `300 -> 293`, retained
  facades `120 -> 113`, and exact aliases `95 -> 88`, with no new dependency
  or cycle.
- [x] Qualify the deletion with 153 focused architecture/compatibility tests,
  899 root tests, 633 workstation tests, 38 targeted BDD cases, 35 isolated
  wheel/sdist builds, deterministic publication capture, Flutter analysis, and
  51 widget tests.

Completed deletion cut - runtime exact-alias cohort (2026-10-30):

- [x] Remove ten repository-internal aliases for canonical runtime capability,
  host ABI, broker, realizer, transport, temporary-path, virtual-mount, and
  Wasm modules while retaining the separately supported `python_skill_host`
  import and the executable `fence_extraction_strategy` path.
- [x] Accept only the sequential shrinking delta: owned roots `121 -> 111`,
  combined graph nodes `157 -> 147`, combined edges `293 -> 283`, retained
  facades `113 -> 103`, and exact aliases `88 -> 78`, with no new dependency
  or cycle.
- [x] Qualify runtime and host behavior with 153 focused tests, 899 root tests,
  a clean 633-test workstation cycle, 38 targeted BDD cases, 35 isolated
  wheel/sdist builds, deterministic publication capture, Flutter analysis, and
  51 widget tests. One unrelated Textual timing assertion failed once, passed
  four immediate isolated reruns, and passed in the complete clean rerun.

Completed deletion cut - governance exact-alias cohort (2026-10-30):

- [x] Remove the repository-internal `governed_skill_access` and
  `runtime_governance_context` aliases without moving or changing their
  canonical `realized_core_engine` implementations.
- [x] Accept only the sequential shrinking delta: owned roots `111 -> 109`,
  combined graph nodes `147 -> 145`, combined edges `283 -> 281`, retained
  facades `103 -> 101`, and exact aliases `78 -> 76`, with no new dependency
  or cycle.
- [x] Qualify current-use and governance resolution with 153 focused
  architecture/compatibility tests, 103 canonical governance tests, 80
  composed selection/function/mediation tests, 899 root tests, 633 workstation
  tests, 38 targeted BDD cases, all distribution builds, deterministic
  publication capture, Flutter analysis, and 51 widget tests.

Completed deletion cut - Blend application exact-alias cohort (2026-10-30):

- [x] Remove the repository-internal `blend_workflow`,
  `blend_workflow_store`, `blend_world`, and `blend_world_store` aliases
  without moving or changing their canonical `realized_blend_application`
  implementations.
- [x] Retain canonical workflow/world behavior comparisons while removing only
  obsolete root-module identity assertions, ownership/classification entries,
  and compatibility-ledger cards; tombstone all four removed paths.
- [x] Accept only the sequential shrinking delta: owned roots `109 -> 105`,
  combined graph nodes `145 -> 141`, combined edges `281 -> 277`, retained
  facades `101 -> 97`, and exact aliases `76 -> 72`, with no new dependency or
  cycle.
- [x] Qualify the cut with 153 focused architecture/compatibility tests, 40
  Blend tests, 899 root tests, 633 workstation tests, 38 targeted BDD cases,
  all distribution builds and isolated imports, deterministic publication
  capture, Flutter analysis, and 51 widget tests.

Completed deletion cut - subject-core exact-alias cohort (2026-10-30):

- [x] Remove nine repository-internal root aliases for canonical subject-core
  decision policy/projection, Gather sources, learning-context rendering, and
  publication substrate/projection/rendering/validation without changing the
  package-owned implementations.
- [x] Keep the service-owned `url_learning_capture` alias in a separate cohort
  because its browser/extraction behavior and distribution boundary require a
  different qualification surface.
- [x] Accept only the sequential shrinking delta: owned roots `105 -> 96`,
  combined graph nodes `141 -> 132`, combined edges `277 -> 268`, retained
  facades `97 -> 88`, and exact aliases `72 -> 63`, with no new dependency or
  cycle.
- [x] Qualify the cut with 145 focused architecture/compatibility tests, 65
  subject-domain/distribution tests, 891 root tests, 633 workstation tests, 38
  targeted BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and 51 widget tests.

Completed deletion cut - subject-service exact-alias cohort (2026-10-30):

- [x] Remove the repository-internal `url_learning_capture` alias without
  moving or changing the canonical
  `workstation.subject.service.url_learning_capture` implementation.
- [x] Preserve canonical browser acquisition, urllib fallback, extraction,
  source-bundle persistence, patch targets, and service packaging; remove only
  the obsolete root identity assertion and ledger entries, then tombstone the
  retired path.
- [x] Accept only the sequential shrinking delta: owned roots `96 -> 95`,
  combined graph nodes `132 -> 131`, combined edges `268 -> 267`, retained
  facades `88 -> 87`, and exact aliases `63 -> 62`, with no new dependency or
  cycle.
- [x] Qualify the cut with 144 focused architecture/compatibility tests, seven
  URL-capture/service-distribution tests, 890 root tests, 633 workstation tests,
  38 targeted BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and 51 widget tests.

Completed deletion cut - validation exact-alias cohort (2026-10-30):

- [x] Remove the repository-internal `validation_ladder` and
  `validation_sqlite` aliases without moving or changing the canonical
  `realized_validation.ladder` and `realized_validation.sqlite_runtime`
  implementations.
- [x] Preserve validation command ordering, nested-report capture, CLI
  integration, SQLite runtime allocation, and durable archival; remove only the
  root aliases and ledger entries, tombstone the paths, and correct package
  documentation.
- [x] Accept only the sequential shrinking delta: owned roots `95 -> 93`,
  combined graph nodes `131 -> 129`, combined edges `267 -> 265`, retained
  facades `87 -> 85`, and exact aliases `62 -> 60`, with no new dependency or
  cycle.
- [x] Qualify the cut with 144 focused architecture/compatibility tests, ten
  validation tests, 890 root tests, 633 workstation tests, 38 targeted BDD
  cases, all distribution builds and isolated imports, deterministic
  publication capture, Flutter analysis, and 51 widget tests.

Completed deletion cut - exchange exact-alias cohort (2026-10-30):

- [x] Remove ten repository-internal exact aliases for artifact exchange,
  portable-skill schema/compilation/translation, registry and run-bundle
  projection, and learning-context skill materialization without moving or
  changing their canonical `realized_exchange` implementations.
- [x] Preserve the held `learning_context` facade and the separately reviewed
  Markdown/controller aliases; remove only the ten identity shells and their
  ledger entries, tombstone every retired path, and correct exchange and module
  documentation.
- [x] Accept only the sequential shrinking delta: owned roots `93 -> 83`,
  root-boundary classifications `116 -> 106`, combined graph nodes `129 ->
  119`, combined edges `265 -> 255`, grandfathered observations `135 -> 125`,
  retained facades `85 -> 75`, and exact aliases `60 -> 50`, with no new
  dependency or cycle.
- [x] Qualify the cut with 142 focused architecture/compatibility tests, 65
  canonical exchange behavior tests, five isolated exchange package tests,
  888 root tests, 633 workstation tests, 38 targeted BDD cases, all
  distribution builds and isolated imports, deterministic publication capture,
  Flutter analysis, and 51 widget tests.

Completed deletion cut - controller binding exact-alias cohort (2026-10-30):

- [x] Remove the repository-internal `controller_runtime_binding` alias without
  moving or changing the canonical engine-owned controller factory registration
  seam.
- [x] Preserve engine registration and nested controller construction; remove
  only the identity shell and its ledger/test entries, tombstone the path, and
  correct module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `83 -> 82`,
  root-boundary classifications `106 -> 105`, combined graph nodes `119 ->
  118`, combined edges `255 -> 254`, grandfathered observations `125 -> 124`,
  retained facades `75 -> 74`, and exact aliases `50 -> 49`, with no new
  dependency or cycle.
- [x] Qualify the non-model cut with 146 focused architecture/runtime-hygiene
  tests, 882 applicable root tests, 632 applicable workstation tests, 38
  deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and 51 widget tests.
  Seven unrelated provider-backed cases remain explicitly outside this
  cohort's evidence pending external-data authorization.

Completed deletion cut - persistence exact-alias cohort (2026-10-30):

- [x] Remove the repository-internal `store` alias without moving or changing
  the canonical core-engine artifact-store and SQLite implementation.
- [x] Preserve canonical class identity, SQLite schema, persisted values,
  selection semantics, and the already-migrated trial import; remove only the
  identity shell and its ledger/test entries, tombstone the path, and correct
  module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `82 -> 81`,
  root-boundary classifications `105 -> 104`, combined graph nodes `118 ->
  117`, combined edges `254 -> 253`, grandfathered observations `124 -> 123`,
  retained facades `74 -> 73`, and exact aliases `49 -> 48`, with no new
  dependency or cycle.
- [x] Qualify the non-model cut with 314 focused architecture/persistence
  tests, 882 applicable root tests, 632 applicable workstation tests, 38
  deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and 51 widget tests.
  Seven unrelated provider-backed cases remain explicitly outside this
  cohort's evidence pending external-data authorization.

Completed deletion cut - controller selection exact-alias cohort (2026-10-30):

- [x] Remove six repository-internal aliases for request posture,
  direct-knowledge reuse, fallback elaboration, and retrieval ranking without
  moving or changing their canonical core-engine implementations.
- [x] Preserve canonical behavior and point the retained
  `fallback_not_semantics` symbol-identity checks directly at canonical
  modules; remove only identity shells and their ledger/test entries,
  tombstone every path, and correct module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `81 -> 75`,
  root-boundary classifications `104 -> 98`, combined graph nodes `117 ->
  111`, combined edges `253 -> 247`, grandfathered observations `123 -> 117`,
  retained facades `73 -> 67`, and exact aliases `48 -> 42`, with no new
  dependency or cycle.
- [x] Qualify the non-model cut with 362 focused architecture/controller tests,
  881 applicable root tests, a clean 632-test workstation rerun after one
  isolated Textual timing failure passed four exact normal-composition reruns,
  38 deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and 51 widget tests.
  Seven unrelated provider-backed cases remain explicitly outside this
  cohort's evidence pending external-data authorization.

Completed deletion cut - controller normalization/learning exact-alias cohort
(2026-10-30):

- [x] Remove five repository-internal aliases for deterministic learning
  vocabulary, Markdown encounter shaping, non-achievedness normalization, its
  dependency surface, and structured-learning YAML without moving or changing
  their canonical engine implementations.
- [x] Keep the provider/composition-bearing external Markdown facade separate;
  preserve the LLM-layer hygiene assertion by pointing it at canonical engine
  source; remove only identity shells and ledger/test entries, tombstone every
  path, and correct module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `75 -> 70`,
  root-boundary classifications `98 -> 93`, combined graph nodes `111 -> 106`,
  combined edges `247 -> 242`, grandfathered observations `117 -> 112`,
  retained facades `67 -> 62`, and exact aliases `42 -> 37`, with no new
  dependency or cycle.
- [x] Qualify the non-model cut with 234 focused architecture/learning tests,
  880 applicable root tests, 632 applicable workstation tests, 38 deterministic
  BDD cases, all distribution builds and isolated imports, deterministic
  publication capture, Flutter analysis, and 51 widget tests. Seven unrelated
  provider-backed cases remain explicitly outside this cohort's evidence
  pending external-data authorization.

Completed deletion cut - controller reduction/closure exact-alias cohort
(2026-10-30):

- [x] Remove six repository-internal aliases for artifact answer resolution,
  constitutional trace projection, closure and commitment, governed prior-
  learning reuse, reduction coordination, and run-outcome harvesting without
  moving or changing their canonical engine implementations.
- [x] Preserve canonical constitutional-trace ownership, runtime-layer,
  distribution, replay, determinism, artifact-selection, and resumption
  assertions; remove only root identity shells and their facade-only evidence,
  tombstone every path, and correct module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `70 -> 64`,
  root-boundary classifications `93 -> 87`, combined graph nodes `106 -> 100`,
  combined edges `242 -> 236`, grandfathered observations `112 -> 106`,
  retained facades `62 -> 56`, and exact aliases `37 -> 31`, with no new
  dependency or cycle.
- [x] Qualify the non-model cut with 298 focused architecture/reduction tests,
  879 applicable root tests, 632 applicable workstation tests, 46 deterministic
  BDD cases, all distribution builds and isolated imports, deterministic
  publication capture, Flutter analysis, and 51 widget tests. Seven unrelated
  provider-backed cases remain explicitly outside this cohort's evidence
  pending external-data authorization.

Completed deletion cut - controller integration exact-alias cohort
(2026-10-30):

- [x] Remove the three repository-internal `artifact`,
  `controller_governance_bridge`, and `system_state` aliases without moving or
  changing their canonical engine implementations.
- [x] Preserve canonical artifact-helper, governance-selection, state, replay,
  determinism, layer-hygiene, and host-boundary assertions; remove only root
  identity shells and their facade-only evidence, tombstone every path, and
  correct module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `64 -> 61`,
  root-boundary classifications `87 -> 84`, combined graph nodes `100 -> 97`,
  combined edges `236 -> 233`, grandfathered observations `106 -> 103`,
  retained facades `56 -> 53`, and exact aliases `31 -> 28`, with no new
  dependency or cycle.
- [x] Qualify the non-model cut with 325 focused architecture/controller tests,
  877 applicable root tests, 632 applicable workstation tests, 46 deterministic
  BDD cases, all distribution builds and isolated imports, deterministic
  publication capture, Flutter analysis, and 51 widget tests. Seven unrelated
  provider-backed cases remain explicitly outside this cohort's evidence
  pending external-data authorization.

Completed deletion cut - host-interaction symbol re-export cohort
(2026-10-31):

- [x] Remove seven repository-internal symbol projections for canonical host
  action dispatch, actions, context, delegation, models, receipts, and
  resolution without moving or changing the `realized-host-interaction`
  implementation.
- [x] Verify every exported symbol's canonical object identity, the absence of
  wildcard and non-contract consumers, and the absence of facade-owned durable
  pickle globals before deleting only the projections and their single
  facade-only identity loop.
- [x] Accept only the sequential shrinking delta: owned roots `61 -> 54`,
  root-boundary classifications `84 -> 77`, combined graph nodes `97 -> 90`,
  combined edges `233 -> 226`, grandfathered observations `103 -> 96`,
  retained facades `53 -> 46`, and symbol re-exports `19 -> 12`, with no new
  dependency or cycle.
- [x] Qualify the non-model cut with 247 focused architecture/host-interaction
  tests, 876 applicable root tests, 632 applicable workstation tests, 46
  deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and 51 widget tests.
  Seven unrelated provider-backed cases remain explicitly outside this
  cohort's evidence pending external-data authorization.

Completed migration cut - artifact contract re-export consumer
(2026-10-31):

- [x] Migrate the canonical artifact protocol behavior assertion from the
  historical `artifact_contracts` projection to
  `realized_core_semantics.artifacts` without deleting or changing the facade.
- [x] Reduce the retained facade to its single designated symbol-identity
  contract consumer, with no production import, dependency-edge, or behavior
  change.
- [x] Qualify the migration with 241 focused semantic/artifact/compatibility
  tests, 876 applicable root tests, 632 applicable workstation tests, 46
  deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and 51 widget tests.
  Seven unrelated provider-backed cases remain explicitly outside this
  migration's evidence pending external-data authorization.

Completed deletion cut - artifact contract symbol re-export cohort
(2026-10-31):

- [x] Remove the repository-internal `artifact_contracts` projection only
  after its canonical behavior consumer completed the separately committed
  migration cycle to `realized_core_semantics.artifacts`.
- [x] Preserve canonical protocol conformance, artifact-boundary, replay,
  determinism, and selection assertions; remove only the root projection and
  its remaining facade-only identity evidence, tombstone the path, and correct
  module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `54 -> 53`,
  root-boundary classifications `77 -> 76`, combined graph nodes `90 -> 89`,
  combined edges `226 -> 225`, grandfathered observations `96 -> 95`, retained
  facades `46 -> 45`, and symbol re-exports `12 -> 11`, with no new dependency
  or cycle.
- [x] Qualify the non-model cut with `272` focused architecture/semantic tests,
  `877` applicable root tests, `632` applicable workstation tests, `46`
  deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and `51` widget tests.
  Seven unrelated provider-backed cases remain explicitly outside this
  cohort's evidence pending external-data authorization.

Completed deletion cut - fallback semantics symbol re-export cohort
(2026-10-31):

- [x] Remove the repository-internal `fallback_not_semantics` aggregate
  projection after the earlier controller-selection cohort migrated its
  identity contract directly to canonical fallback-generation and ranking
  modules and completed a stable qualification cycle.
- [x] Preserve canonical fallback, ranking, schema, answer-selection,
  title-depth, replay, and function-boundary assertions; remove only the root
  projection and its facade-only identity evidence, tombstone the path, and
  correct module documentation.
- [x] Accept only the sequential shrinking delta: owned roots `53 -> 52`,
  root-boundary classifications `76 -> 75`, combined graph nodes `89 -> 88`,
  combined edges `225 -> 224`, grandfathered observations `95 -> 94`, retained
  facades `45 -> 44`, and symbol re-exports `11 -> 10`, with no new dependency
  or cycle.
- [x] Qualify the non-model cut with `333` focused tests, `876` applicable
  non-provider root tests, `633` applicable non-provider workstation tests,
  `46` deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and `51` widget tests.
  Provider-backed results are not accepted as evidence; a misconfigured first
  exclusion ran six Newton cases, after which corrected verified-ID reruns
  excluded all seven external-data cases and established the recorded totals.

Completed deletion cut - itemization validation symbol re-export cohort
(2026-10-31):

- [x] Remove the repository-internal `itemize_validation` projection after
  subject workflow and direct validator tests had consumed the canonical
  `workstation.subject.core.itemize_validation` owner through stable
  qualification cycles.
- [x] Preserve canonical itemization validation, subject workflow,
  publication, and gRPC assertions; remove only the root projection and its
  facade-only identity evidence, tombstone the path, and redirect current
  implementation guidance to the canonical source.
- [x] Accept only the sequential shrinking delta: owned roots `52 -> 51`,
  root-boundary classifications `75 -> 74`, combined graph nodes `88 -> 87`,
  combined edges `224 -> 223`, grandfathered observations `94 -> 93`, retained
  facades `44 -> 43`, and symbol re-exports `10 -> 9`, with no new dependency
  or cycle.
- [x] Qualify the non-model cut with `353` focused tests, `875` applicable
  non-provider root tests, `633` applicable non-provider workstation tests,
  `46` deterministic BDD cases, all distribution builds and isolated imports,
  deterministic publication capture, Flutter analysis, and `51` widget tests.
  All seven provider-backed cases remain excluded and unclaimed pending
  explicit external-data authorization.

Completed deletion cut - controller supplement exact-alias cohort
(2026-10-31):

- [x] Remove the repository-internal `supplement` alias after all ordinary
  consumers had used the canonical `realized_core_engine.supplement` owner
  through stable qualification cycles.
- [x] Preserve canonical supplement, provider-transport, prompt, retry,
  response-shaping, replay, and controller behavior; remove only the exact
  root alias and its facade-only identity evidence, then tombstone the path.
- [x] Accept only the sequential shrinking delta: owned roots `51 -> 50`,
  root-boundary classifications `74 -> 73`, combined graph nodes `87 -> 86`,
  combined edges `223 -> 222`, grandfathered observations `93 -> 92`, retained
  facades `43 -> 42`, and exact aliases `28 -> 27`, with no new dependency or
  cycle.
- [x] Qualify the import-only cut with `141` focused deterministic tests, `875`
  applicable non-provider root tests, `633` applicable non-provider
  workstation tests, `46` deterministic BDD cases, all distribution builds
  and isolated imports, deterministic publication capture, Flutter analysis,
  and `51` widget tests. All seven provider-backed cases remain excluded and
  unclaimed pending explicit external-data authorization.

Exit condition:

- [x] The root-boundary ledger contains no canonical package-to-root
  implementation edges and only approved entry or compatibility edges remain.

Further retirement work:

- Every currently authorized qualified cohort is retired. The machine-readable
  ledger now reports zero candidates, `42` explicitly held facades, and `78`
  tombstones. Each held surface must satisfy its recorded review condition,
  receive any required external notice, be removed in a separate change, pass
  the complete affected qualification ladder, and reduce the checked-in
  architecture baseline before it can advance.
- `external_markdown_learning_pipeline` remains held until explicit
  external-data authorization permits all six Newton Markdown-learning
  provider cases to qualify the unchanged canonical exchange owner. The other
  holds retain behavior, aggregate-export, executable, durable-qualified-name,
  composition, or dependency-order obligations. They are not deletion
  candidates in the completed retirement program state.

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
