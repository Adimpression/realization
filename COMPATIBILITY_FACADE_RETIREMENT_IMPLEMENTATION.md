# Compatibility Facade Retirement Implementation

## Status

This document governs the staged retirement of repository-root historical
import facades. Its control plane and internal-consumer migration are now
implemented, and its first qualified exact-alias cohort has been retired.
Further deletion remains cohort-specific and requires the same isolated review
and qualification; no retirement change may introduce runtime behavior change.

In this document, **compatibility facade** means a root Python module retained
to preserve a historical import, module identity, aggregate API, patch target,
or executable path after canonical ownership moved into a package. It does not
mean that the behavior behind the facade is obsolete.

The program continues Phase 11 of
[6-LAYER_ARCHITECTURE_IMPLEMENTATION.md](6-LAYER_ARCHITECTURE_IMPLEMENTATION.md).
The machine-readable starting point is
[architecture/compatibility-facades.json](architecture/compatibility-facades.json).

## Intended Outcome

- [ ] Every supported behavior remains owned and exercised through its
  canonical package API or packaged application entrypoint.
- [x] Every retained facade has an explicit, reviewable reason and retirement
  state.
- [ ] Every removed facade has a migration map, consumer evidence,
  qualification evidence, and a reintroduction guard.
- [ ] No supported persisted value, import identity, patch point, command,
  workflow, receipt, or artifact changes accidentally as a consequence of
  facade removal.
- [ ] Repository-root Python files consist only of deliberate entrypoints and
  validation/trial programs after the compatibility inventory reaches zero.

Zero root Python files is not an objective. Compatibility retirement and
entrypoint relocation are separate architecture programs.

## Governing Constraints

The retirement must preserve the following theory and architecture
distinctions:

- [ ] A compatibility facade is a projection of a canonical owner; it may not
  become a second owner of semantics, policy, state, or execution.
- [ ] Semantic identity is not inferred from similarity. Historical and
  canonical objects are equivalent only where explicit identity, serialization,
  or adapter contracts prove that relationship.
- [ ] Removal is an admitted transition supported by evidence. Absence of a
  known consumer is not, by itself, proof that an import is unsupported.
- [ ] Canonical state, provenance, authority, receipts, and replay identity
  remain with their current owners. A facade-retirement change may not migrate
  or reinterpret them.
- [ ] Import-time registration and extension installation are behavior. They
  must be replaced explicitly before a module providing those effects can be
  removed.
- [ ] Historical executable paths and historical import paths are separate
  compatibility obligations even when one file currently provides both.
- [ ] LLM output is irrelevant to retirement eligibility. Discovery,
  compatibility matching, and removal decisions are mechanical and reviewable.
- [ ] Each removal is independently revertible by restoring only the facade and
  its compatibility tests; canonical implementation must not move in the same
  change.

## Theory And Architecture Derivation

This program is derived from the repository theory rather than from a desired
root-file count:

- **BSSC boundary identity:** an import facade is a historical carrier at a
  boundary. Its replacement is valid only when the canonical package preserves
  the relied-on values, references, polarity, and reconstructible identity.
- **Artifact-mediated verification:** a passing scanner or aggregate test is
  not intrinsic authority. Contract cards, old-material fixtures, isolated
  distributions, command comparisons, and qualification outputs are the
  independently checkable artifacts supporting one removal decision.
- **Attention is not verification:** source search nominates possible
  consumers; it does not prove that an unobserved external or durable consumer
  does not exist. Support policy and durable-name evidence remain separate from
  retrieval results.
- **Resumption and interruption:** retirement is a resumable sequence of
  admitted states. An interrupted cohort remains at its last evidenced state;
  no partial migration silently becomes deletion authorization.
- **Augmentation, redirection, and realignment:** discovering another consumer
  augments the evidence. Changing a support classification redirects the
  cohort. Policy, migration, and qualification must then be realigned before
  work continues; evidence is retained rather than rewritten.
- **CTFS model revision:** ordinary execution through a facade is behavior
  inside the current architecture snapshot. Removing the facade revises the
  architecture model itself. The revised snapshot must still satisfy ownership,
  dependency, distribution, and compatibility invariants before it is
  accepted.
- **Six-layer ownership:** retirement may remove an outer historical carrier;
  it may not move semantics, governance, authority, LLM judgment, runtime
  realization, workstation behavior, or entry/exchange composition into the
  wrong layer.

The resulting implementation rule is:

```text
observe -> freeze contract -> classify support -> migrate consumers
        -> qualify -> delete separately -> retain tombstone
```

No step may be inferred from the completion of a different step.

## Measured Starting Point

Snapshot date: 2026-10-29.

- [x] The architecture ledger classifies 128 root Python modules.
- [x] 120 modules are retained compatibility facades.
- [x] Eight root modules are deliberate entrypoints or validation programs and
  are outside this retirement scope.
- [x] The v1 facade inventory recorded 405 static Python imports:
  - 401 test imports
  - three compatibility-facade consumers
  - one trial consumer
- [x] The v2 facade inventory records 490 static consumers:
  - 405 ordinary imports
  - 85 string patch targets
  - 486 test consumers
  - three compatibility-facade consumers
  - one trial consumer
- [x] The v2 facade inventory separately records 942 non-import references
  across commands, module file paths, documentation, trials, tests,
  architecture material, tooling, and configuration or fixtures.
- [x] No canonical workspace package imports a root compatibility facade.
- [x] No canonical root module imports a compatibility facade.
- [x] Public README code examples and repository example code have no measured
  facade imports.
- [x] All 35 registered workspace projects build as wheels and source
  distributions and import without the repository root on `sys.path`.
- [x] The current qualification baseline records all 17 declared gates as
  passing.
- [x] One stable qualification cycle is recorded after the final canonical
  production-consumer migration.
- [x] The current facade shapes are:
  - 95 exact `sys.modules` aliases
  - 19 symbol re-export facades
  - one aggregate re-export facade, `normalize`
  - five behavior-bearing compatibility adapters: `blend_context`,
    `blend_session`, `controller_runtime`, `itemize`, and `main`
- [x] Three facade-to-facade dependency chains remain:
  - `main -> controller_entrypoint_binding`
  - `main -> controller_runtime`
  - `itemize -> runtime_controller_api`
- [x] The former trial consumer of `store` was migrated to
  `realized_core_engine.store`; no non-test trial imports a retained facade.

These counts are evidence about the current checkout, not permanent targets.
They must be regenerated before each cohort is selected.

### Current Implementation Evidence

Snapshot date: 2026-10-30.

- [x] Generated observations and human policy are separated between
  `architecture/compatibility-facades.json` and
  `architecture/compatibility-facade-policy.json`.
- [x] The current policy classifies 26 source-checkout-only facades as
  repository-internal, contract-qualified candidates, keeps 41 facades on
  explicit holds, and permanently tombstones 53 retired aliases.
  Qualification makes a retained facade eligible for a later isolated deletion
  review; it does not itself delete or deprecate it.
- [x] The executable contract ledger contains all 67 retained-facade cards:
  - 42 exact-module-object identity proofs
  - 19 exported-symbol identity proofs
  - one manual multi-owner aggregate mapping
  - five manual behavior-equivalence surfaces
  - 35 facades carrying 133 exercised protocol-zero pickle globals
- [x] Static consumers were reduced from the measured v2 baseline to 74:
  - 69 imports in the designated compatibility-contract suite
  - two imports in the dedicated `main` executable/CLI contract test
  - three facade-to-facade links in the held behavior-adapter chain
- [x] No canonical package, public README example, or repository example
  imports a root facade.
- [x] The current scanner records 603 non-AST references with dispositions:
  - 376 historical narrative references
  - 54 durable provenance references from checked-in receipts
  - 57 compatibility-test evidence references
  - five architecture evidence references
  - 111 runtime, durable-runtime, or runnable-guidance references
- [x] All 111 blocking references belong to supported held surfaces:
  - 78 executable, build, validation, and guidance references to `main`
  - 33 executable-skill, trial, and distribution references to
    `python_skill_host`
- [x] Representative SQLite state confirms that persisted executable skill
  source imports `python_skill_host`; the runtime distribution deliberately
  ships that top-level module. It is therefore a durable compatibility
  obligation, not a low-risk alias candidate.
- [x] Ordinary Python consumers of retained qualified aliases and all 19 symbol
  re-export facades use canonical package owners; the two remaining exact
  alias consumers belong to the held behavior-adapter dependency chain.
- [x] Every one of the 26 retained qualified candidates has no non-contract consumer,
  no blocking runtime reference, no known durable-qualified-name obligation,
  and one unambiguous canonical replacement.
- [x] The 41 holds preserve the proven pickle-qualified-name obligations and
  the remaining behavior, aggregate, composition, executable, and durable-skill
  surfaces rather than mechanically rewriting them.
- [x] `fence_extraction_strategy` is held separately from ordinary exact
  aliases because it preserves a historical `__main__` path. The scanner now
  rejects deletion eligibility whenever an executable facade has no explicit
  executable-obligation classification.
- [x] The first seven `core_semantics`, ten `core_runtime`, two governance,
  four Blend application, nine subject-core, one subject-service, two
  validation, ten exchange, one controller-binding, one persistence, and six
  controller-selection exact aliases are removed, their canonical replacements
  remain unchanged, and tombstones reject accidental reintroduction.

## Known Measurement Gap

The v2 inventory is necessary but insufficient for deletion. It now scans
Python AST imports, constant-string `importlib.import_module` calls, literal
patch targets, executable and module paths, shell and build configuration,
JSON/TOML/YAML/spec files, all Markdown, README code fences, and example
Python. It also resolves relative imports, follows aliased literal dynamic
imports, distinguishes comments/docstrings and historical narrative from
runnable guidance, scans checked-in durable JSONL/binary material, and records
representative local SQLite evidence. It cannot establish arbitrary
non-literal module strings, unknown external consumers, or unobserved durable
stores. Those limits are represented as policy holds, not silently treated as
absence.

`main.py` remains the concrete high-risk example: the expanded inventory now
shows its scripts, validators, qualification gates, PyInstaller configuration,
runtime command assembly, and documentation references, but those references
must still be reviewed and migrated. Discovery is not removal approval.

## Scope

### In Scope

- [ ] Strengthen facade discovery and retirement controls.
- [ ] Classify every facade by compatibility shape and supported surface.
- [ ] Migrate repository consumers to canonical package APIs or packaged
  application entrypoints.
- [ ] Preserve compatibility for an explicit notice and qualification period
  where required.
- [ ] Remove qualified facades in small, owner-cohesive cohorts.
- [ ] Ratchet every accepted removal into architecture controls and CI.

### Out Of Scope

- [ ] Do not redesign theory, reduction, resumption, governance, skills,
  subject workflow, Blend, UI, or publication behavior.
- [ ] Do not move canonical source while deleting its facade.
- [ ] Do not change persisted schemas, identifiers, receipts, action labels,
  command output, or artifact formats.
- [ ] Do not turn root entrypoint or validation modules into facades merely to
  reduce the root-file count.
- [ ] Do not create replacement aliases under new names.
- [ ] Do not retain compatibility through broad `__getattr__`, import hooks,
  fallback search paths, or another unmeasured alias layer.
- [ ] Do not update a baseline to make an unexplained dependency or behavior
  difference pass.

## Target Boundary And Transition Map

Retirement changes only the historical carrier at the repository boundary.
The canonical owner, its dependency direction, and its behavior remain fixed.
Each facade must follow the transition appropriate to its measured shape:

| Facade shape or obligation | Canonical destination | Required transition | Required proof before deletion | Stop condition |
| --- | --- | --- | --- | --- |
| Exact module alias | Existing package module | Migrate consumers to the canonical module; retain only the narrow identity contract until deletion | Exact module identity while retained, zero non-contract consumers, no executable or durable-name obligation, isolated package qualification | Any import effect, adapter behavior, durable qualified name, executable path, or ambiguous target |
| Symbol re-export | Existing package symbol owner or owners | Migrate each imported symbol independently; do not replace the facade with another aggregate | Export-by-export identity/signature/default/constant map, patch-target proof, old pickle fixture proof where applicable | A relied-on symbol has no intentional public owner or its identity/behavior differs |
| Aggregate re-export | Multiple existing owners | Split consumers by responsibility | Complete consumer-to-owner map, wildcard and `__all__` coverage, no replacement aggregate | A consumer depends on aggregate ordering, collision behavior, or an unmapped private name |
| Behavior-bearing adapter | Existing application or composition package | First expose or select an explicit application surface in a separate additive change, then migrate callers | Direct old/new behavior differential, import-effect replacement, stable qualification cycle after migration | Canonical lower package would need to absorb composition, runtime, host, UI, or executable behavior |
| Historical executable path | Existing packaged application command | Migrate scripts, build specs, validators, qualification commands, and runnable guidance | Namespace/default/exit/stdout/stderr/environment/artifact parity on a clean host | Any command behavior lacks a packaged equivalent or the historical path is still supported without notice |
| Durable qualified name | Existing canonical type or callable owner plus an explicit compatibility decoder/migration | Keep the name, or introduce and qualify a durable-data migration separately before facade deletion | Representative persisted material, protocol-zero pickle globals, state/run-bundle/skill fixtures, and clean-checkout decoding | Unknown durable stores, generated source, or shipped distributions still contain the historical name |
| Import-time registration or extension installation | Owning application composition root | Replace incidental import order with explicit installation before consumer migration | Fresh-process registration differential and proof that canonical imports remain side-effect bounded | Removal changes registration order, extension availability, environment reads, or module mutation |

The transition map is exclusive by obligation, not by syntax. A three-line
alias with an executable path or durable qualified name follows the stricter
row. A facade may advance only after all applicable rows are satisfied.

### Desired End State

- [ ] Canonical packages remain the only semantic, governance, runtime, LLM,
  subject, Blend, exchange, and workstation implementation owners.
- [ ] Supported launch behavior is provided by package-owned commands rather
  than repository-root composition reach-through.
- [ ] Durable historical names are either deliberately retained or decoded by
  a separately qualified migration; deletion never makes old state unreadable.
- [ ] The root boundary contains deliberate entry/validation programs and no
  unmeasured compatibility behavior.
- [ ] Removed facade names remain tombstoned so the architecture ratchet makes
  the improvement irreversible.

## Assumption Register

Each assumption must be tested for the selected facade cohort. A failed
assumption pauses only that cohort; it does not justify forcing the plan onto
the code.

- [x] **R1 - Canonical package ownership is established.** The architecture
  checker and isolated-distribution gate show no canonical package dependency
  on root facades. If this regresses, repair the dependency before considering
  removal.

- [ ] **R2 - The canonical replacement covers every supported operation of a
  candidate facade.** Compare exported names, call signatures, defaults,
  exceptions, constants, private-but-relied-on names, module identity, and
  import side effects. If coverage differs, either retain the facade or add an
  explicit package/application API in a separate, behavior-qualified change.

- [x] **R3 - Repository consumer discovery is complete enough for cohort
  classification.**
  Extend discovery across Python imports, patch strings, commands,
  configuration, build files, scripts, docs, serialization fixtures, and
  generated inputs. If a class of reference cannot be measured reliably, keep
  the affected facade until a conservative manual review is recorded.

- [x] **R4 - Durable material is classified conservatively.** Check
  representative SQLite rows, state JSON, run bundles, subject corpus files,
  skill documents, publication records, receipts, and pickle fixtures. If a
  path is persisted, first add a canonical decoder or migration in a separate
  compatibility change and qualify old material on a clean checkout.
  Representative state currently proves a retained `python_skill_host`
  obligation; pickle-global contract tests preserve other known historical
  names. This assumption does not assert that any held facade is removable.

- [ ] **R5 - Import-time effects are either absent or explicitly composed
  elsewhere.** Import each candidate in isolation and compare registrations,
  extension installation, environment reads, and module mutations. If import
  has an effect, move the supported composition to the owning application in a
  separate change before retirement.

- [ ] **R6 - Monkey-patch and test-seam behavior has a canonical target.** A
  facade may preserve module identity specifically so patches affect canonical
  calls. Migrate patches to the canonical module and prove interception still
  occurs before removing that facade.

- [x] **R7 - External support classification is explicit.** The root project is
  a non-package development/composition workspace, so source-checkout-only
  facades with no durable or executable obligation are explicitly classified
  `repository_internal`. `main` remains a supported executable path and
  `python_skill_host` remains a supported historical import shipped in the
  runtime distribution. Any future change to those classifications requires a
  policy decision, replacement map, and notice; repository silence alone is
  not evidence of zero downstream use.

- [ ] **R8 - A cohort is behaviorally homogeneous.** A cohort may contain
  multiple facades only when they have the same owner, compatibility shape,
  support state, qualification surface, and rollback method. Otherwise split
  it.

- [x] **R9 - Test migration does not erase compatibility evidence early.**
  Move behavior tests to canonical APIs first, but retain a narrow facade
  contract test until the facade is actually removed. If a test proves a
  supported historical behavior rather than only identity, retain it through
  the notice period.

- [ ] **R10 - Packaged entrypoints cover historical executable use.** Validate
  command namespaces, defaults, exit codes, stdout/stderr, environment
  behavior, and artifacts against `realized-core` and `realized-workstation`.
  If a historical command has no packaged equivalent, `main` is not eligible.

- [ ] **R11 - Removal does not materially change performance.** Measure at
  least the paths affected by import startup, reduction, retrieval,
  publication, and workstation launch. If performance moves beyond the
  qualification tolerance, investigate rather than adding semantic caches.

- [x] **R12 - The qualification baseline is reproducible.** Rerun every
  default gate and every affected opt-in gate. Preserved historical evidence
  may not be used to approve a deletion when that deletion changes the surface
  the gate exercises. The current pre-deletion checkpoint reproduced all
  default gates on 2026-10-30; no opt-in provider, browser, or screenshot
  surface is affected by the control-plane and consumer-migration slice.

## Retirement State Model

The generated inventory no longer derives policy from file existence. Human
policy classifies source-checkout-only facades separately from supported
executable, distributed-import, durable-qualified-name, aggregate, and
behavior-bearing surfaces. Before selecting a deletion cohort, advance it
through the policy state machine:

The mandatory path is:

`retained -> candidate -> consumers_migrated -> qualified -> removed`

For a supported external import or executable surface, `deprecated` is an
additional policy state between `candidate` and `qualified`; it may be entered
before or after internal consumer migration, but the documented notice and
earliest-removal condition must both be satisfied before `qualified`.
Repository-internal facades do not receive a fictitious deprecation period.
`removed` is represented by a tombstone, not by a live facade-policy record.

An orthogonal `held` state records why a candidate cannot advance.

Required policy fields:

- [x] historical module and path
- [x] canonical replacement module or packaged command
- [x] compatibility shape
- [x] owning responsibility
- [x] support classification
- [x] import and executable obligations
- [x] known durable-qualified-name obligations
- [x] deprecation/notice reference, if required
- [x] earliest eligible removal release or condition
- [x] current retirement state
- [x] hold reason, if any
- [x] last consumer scan evidence
- [x] last qualification evidence
- [x] removal change reference and removal date, represented on tombstones once
  a removal exists

Generated observations and human policy must be separate. Regenerating an
inventory may update measured consumers and shapes; it must not silently reset
support status, notice, holds, or approval decisions.

Removed facades remain in a tombstone ledger. The architecture checker must
reject their reintroduction unless a separately reviewed policy change
explicitly reopens them.

## Phase 0 - Make Retirement Measurable

- [x] Split generated facade observations from human-authored retirement
  policy, or evolve the current schema so generated updates preserve policy.
- [x] Add a deterministic facade-shape classifier for exact aliases, symbol
  re-exports, aggregate re-exports, behavior-bearing adapters, and
  executable/import dual surfaces.
- [x] Record canonical replacement names at symbol and command level where a
  module-level target is insufficient.
- [x] Add a tombstone state for removed facades.
- [x] Reject new facade consumers in every repository scope unless the policy
  explicitly identifies the file as a compatibility contract test.
- [x] Keep the existing hard rejection of canonical-package consumers.
- [x] Add machine-readable output for candidate cohorts and hold reasons.
- [x] Add tests proving that policy fields survive inventory regeneration.
- [x] Add tests proving that a removed facade cannot be silently reintroduced.

Exit condition:

- [x] The control plane can represent staged retirement without deriving
  support policy from file existence.

## Phase 1 - Complete Consumer Discovery

- [x] Scan all Python imports, including relative resolution, literal dynamic
  imports, and imports hidden behind aliases.
- [x] Scan string patch targets used by `unittest.mock`, `pytest`, and local
  helpers.
- [x] Scan shell scripts, Cloud Build, TOML, YAML, JSON, PyInstaller specs,
  task runners, and subprocess argument lists for executable/module paths.
- [x] Scan all Markdown and documentation, not only README code fences, while
  distinguishing historical narrative from runnable guidance.
- [x] Scan serialized fixtures and representative durable stores for qualified
  module names.
- [x] Inspect package entrypoints, generated stubs, and build manifests.
- [x] Produce separate counts for canonical behavior tests, facade contract
  tests, patch targets, commands, trials, tooling, docs, persisted references,
  and unknown references.
- [x] Manually review unresolved string matches rather than accepting or
  deleting them through heuristics.
- [x] Capture the resulting report as qualification evidence in
  `architecture/compatibility-facades.json`.

Immediate known work:

- [x] Replace the trial's `store` import with `realized_core_engine.store` and
  verify its LLM-off trial behavior in a consumer-migration change.
- [x] Inventory every measured `main.py` path invocation before considering
  `main`.
- [x] Inventory patch targets such as `url_learning_capture.*` and
  `supplement.*`.
- [x] Prove canonical replacement patch targets intercept the same runtime
  calls before migrating those test seams.

Exit condition:

- [x] Every facade has zero unresolved repository references and an explicit
  external-support classification.

## Phase 2 - Freeze The Compatibility Contract Per Facade

The executable ledger now generates one retirement card per facade. Mechanical
capture is complete; human review remains cohort-specific:

- [x] Capture facade path, owner, shape, and canonical target.
- [x] Capture public names, explicit `__all__`, callable signatures and
  defaults, and constant types.
- [x] Prove exact module-object or exported-symbol identity where that is the
  facade contract.
- [x] Exercise and capture known protocol-zero pickle globals rather than
  inferring durable identity from source text.
- [x] Classify import effects, executable surfaces, command replacements,
  support status, proof strategy, contract evidence, and facade-only rollback.
- [x] Make the contract ledger deterministic and fail CI when live capture
  differs from the checked-in artifact.
- [ ] For each selected deletion cohort, manually review private-but-relied-on
  names, exceptions, `__module__`, repr, registration/module-mutation effects,
  and command semantics that cannot be established by generic introspection.
- [ ] Bind the reviewed card to the cohort's exact consumer migration, focused
  tests, global gates, notice decision, and rollback rehearsal.

Do not normalize differences away. A mismatch is evidence that the facade is
an adapter or supported aggregate surface, not proof that the canonical API
should absorb it during deletion.

Exit condition:

- [ ] Every selected facade has a reviewed contract and no unexplained behavior.

## Phase 3 - Migrate Internal Consumers Without Removing Facades

- [x] Reclassify measured consumers as canonical behavior tests,
  compatibility-contract tests, held behavior-surface tests, or held
  facade-to-facade composition links.
- [x] Move ordinary behavior tests for the 79 qualified candidates to package
  APIs while retaining their behavioral assertions unchanged.
- [x] Move candidate patch targets to canonical modules and verify that they
  intercept production calls.
- [x] Move all 15 non-contract `itemize` imports and patch targets to
  `realized_core_semantics.itemization` or
  `workstation.subject.core.itemization`; direct-decomposition tests now inject
  the typed proposal port, while the runtime adapter separately proves the
  exact controller proposal type and mode.
- [x] Move 26 ordinary `main` imports and patch targets to their canonical
  semantic, engine, exchange, or workstation owners. Markdown-learning tests
  now install the optional exchange extension explicitly, and the workstation
  patch seam targets the canonical controller class. The two remaining
  non-contract imports deliberately exercise `main` CLI and executable
  compatibility and therefore remain held with that surface.
- [ ] Move the remaining `main` scripts, validators, build paths, qualification
  commands, and runnable guidance to packaged entrypoints only after complete
  command-equivalence proof.
- [ ] Replace the three held facade-to-facade references only after the
  behavior adapters have explicit canonical application/composition surfaces.
- [x] Leave narrow compatibility-contract coverage for every retained facade
  until its deletion change.
- [x] Preserve assertions and test intent; no behavior test is weakened merely
  to remove a historical import.
- [x] Run the complete affected gate set and record one stable qualification
  cycle after the current ordinary-consumer migration.

Exit condition:

- [x] The current 79-candidate pool has no internal consumer except explicitly
  retained compatibility-contract tests.
- [x] The held `itemize` adapter has no non-contract consumer. It remains held
  for explicit behavior-adapter and durable-qualified-name review, not because
  repository callers still depend on its implicit bootstrap.
- [ ] Held behavior, aggregate, executable, durable-name, and composition
  surfaces have completed their separate consumer migrations.

## Phase 4 - Classify Support And Announce Removal

- [x] Decide explicitly whether each facade is a supported external import,
  supported executable path, repository-internal compatibility path, or
  retained aggregate API.
- [x] Keep the current conservative support status unless evidence and review
  justify changing it.
- [ ] Publish a migration table containing old import/command, canonical
  replacement, behavior differences if any, and removal timing.
- [ ] Add release notes or other documented notice for every supported
  external surface.
- [ ] Use import-time deprecation warnings only if separately approved and
  proven not to alter command output, tests, or embedded applications.
- [x] Record one complete stable qualification cycle after the current final
  ordinary-consumer migration.
- [ ] For each actual deletion cohort, satisfy its notice condition and rerun
  the complete affected qualification ladder after the reviewed deletion.

Exit condition:

- [ ] Every facade in the deletion cohort is eligible under both support policy
  and qualification policy.

### First Qualified Deletion Cohort Review

The first proposed deletion cohort is deliberately restricted to seven exact
module aliases owned by `core_semantics`. This record approves the cohort for
an isolated deletion change after the preceding consumer-migration slice is
checkpointed; it does not itself authorize combining migration and deletion in
one change.

| Historical import | Canonical replacement | Contract shape | Supported behavior difference |
| --- | --- | --- | --- |
| `applied_theory_primitives` | `realized_core_semantics.applied_primitives` | exact module alias | none |
| `boundary` | `realized_core_semantics.boundary` | exact module alias | none |
| `id_generation` | `realized_core_semantics.identifiers` | exact module alias | none |
| `normalization_primitives` | `realized_core_semantics.normalization` | exact module alias | none |
| `prolog` | `realized_core_semantics.prolog` | exact module alias | none |
| `semantic_text` | `realized_core_semantics.semantic_text` | exact module alias | none |
| `title_semantics` | `realized_core_semantics.title_semantics` | exact module alias | none |

Reviewed evidence:

- [x] All seven files contain only the exact `sys.modules` alias to the listed
  canonical module; they define no adapter, registration, environment,
  executable, or composition behavior.
- [x] The executable contract ledger proves exact module-object identity and
  records `module_alias_only` as the import-effect class for every member.
- [x] Public names, signatures, constants, `__all__`, module identity, and
  import effects are therefore the canonical module's own surface rather than
  a second facade-owned surface.
- [x] The current consumer inventory finds no non-contract import or patch
  target for any member, and no canonical package, public README example, or
  repository example imports one.
- [x] No member is executable and no member carries a known protocol-zero
  pickle global, persisted qualified-name obligation, runtime guidance
  reference, or notice requirement.
- [x] Support policy classifies every member as `repository_internal` and
  `qualified`, with removal permitted only after one stable qualification
  cycle and in an isolated deletion change.
- [x] The seven members have the same owner, compatibility shape, support
  state, qualification surface, and rollback method; no symbol re-export,
  aggregate, behavior adapter, executable surface, or durable-name hold is
  included.
- [x] Canonical semantic behavior remains covered by package and root behavior
  tests after the facade-only identity assertions are removed.
- [x] Rollback consists only of restoring each three-line alias and its exact
  identity assertion; no canonical source, state, schema, or consumer must be
  reverted.
- [x] Checkpoint the completed consumer-migration and stable-qualification
  slice before starting this deletion change.
- [x] Delete the seven aliases, transition them to tombstones, remove their
  root ownership records and facade-only assertions, regenerate architecture
  artifacts, and qualify the resulting shrinking-only delta.

Accepted deletion evidence, captured on 2026-10-30:

- [x] The accepted graph is strictly smaller: owned roots `128 -> 121`,
  root-to-component edges and boundary classifications `151 -> 144`, combined
  nodes `164 -> 157`, and combined edges `300 -> 293`, with zero cyclic nodes
  and no added dependency observation.
- [x] The retained inventory contains `113` facades, `119` static consumers,
  zero canonical-package consumers, zero public README references, and zero
  public example consumers; seven semantic aliases are tombstoned.
- [x] The retained contract ledger contains `113` cards, `88` exact aliases,
  `35` facades with `133` durable pickle globals, and `90` facade contract
  tests.
- [x] Architecture, inventory, and compatibility qualification passed `153`
  focused tests; the root suite passed `899` tests and the workstation suite
  passed `633` tests with one expected skip.
- [x] Skill-routing, report-creation, and incremental-publication BDD passed
  `38` cases; publication reference capture reproduced eight actions and two
  artifacts without a tracked artifact change.
- [x] All `35` projects built wheels and source distributions and imported
  their declared public modules in isolation; Flutter analysis found no issue
  and all `51` widget tests passed.
- [x] Rollback remains local: restore the seven alias files, their identity
  assertions, and their active ledger records; no canonical implementation,
  persisted state, workflow, or artifact must be reverted.

Isolated pre-deletion rehearsal evidence, captured on 2026-10-30:

- [x] A mirror of the qualified working tree deleted only the seven facade
  files and changed only their facade-specific tests, tombstones, root
  ownership/classification records, generated architecture artifacts, and
  current module documentation.
- [x] The architecture checker accepted the pre-baseline state as
  shrinking-only: owned root modules `128 -> 121`, root-to-component edges
  `151 -> 144`, root-boundary classifications `151 -> 144`, combined graph
  nodes `164 -> 157`, and combined graph edges `300 -> 293`, with no added
  root, package edge, or cycle.
- [x] The regenerated facade inventory measured `113` facades, `119` static
  consumers, `774` text references, zero canonical-package consumers, zero
  public README references, and zero public example consumers.
- [x] The regenerated contract ledger measured `113` cards, `88` exact-module
  aliases, `35` facades with durable pickle globals, and `90` retained facade
  contract tests.
- [x] The rehearsal identified and updated only expected count/ownership
  assertions: facade candidates `79 -> 72`, exact aliases `95 -> 88`, contract
  cards `120 -> 113`, and removed semantic roots absent from the ownership
  ledger.
- [x] The final generation order is architecture review, shrinking-only
  baseline/report update, compatibility-inventory regeneration, then contract
  ledger regeneration. The inventory embeds architecture-baseline facts and is
  stale if generated before the accepted baseline.
- [x] All 151 architecture, inventory, and compatibility-contract tests passed
  in the corrected mirror.
- [x] All 897 root tests passed in the corrected mirror with all mirrored
  workspace `src` directories taking precedence over the original editable
  environment and with the localhost skill bridge enabled.

### Runtime Leaf Deletion Cohort Review

The second proposed deletion cohort contains ten exact aliases owned by
`runtime_execution`. `fence_extraction_strategy` is intentionally excluded:
although it aliases a canonical module, it also preserves a historical
`__main__` executable path and therefore requires separate command-parity
proof.

| Historical import | Canonical replacement |
| --- | --- |
| `capability_runtime` | `realized_core_runtime.capabilities` |
| `host_abi` | `realized_core_runtime.host_abi` |
| `host_brokers` | `realized_core_runtime.host_brokers` |
| `host_realizers` | `realized_core_runtime.host_realizers` |
| `macos_host_brokers` | `realized_core_runtime.macos_brokers` |
| `python_skill_brokerization` | `realized_core_runtime.python_brokerization` |
| `python_skill_host_transport` | `realized_core_runtime.python_transport` |
| `runtime_temp` | `realized_core_runtime.temporary` |
| `virtual_mounts` | `realized_core_runtime.virtual_mounts` |
| `wasm_skill_runtime` | `realized_core_runtime.wasm` |

Reviewed evidence:

- [x] Every member is an exact `sys.modules` alias with
  `module_alias_only` import effects, exact module-object identity, no
  executable surface, and no known durable pickle global.
- [x] Every member is `repository_internal`, has no non-contract consumer or
  blocking reference, and has one canonical `realized_core_runtime` target.
- [x] The scanner now holds an executable facade when its policy claims no
  executable obligation; `fence_extraction_strategy` is explicitly held as a
  repository executable until packaged invocation, exit-status, and output
  parity are qualified.
- [x] The isolated architecture delta was strictly subtractive: owned roots
  `128 -> 118`, root-to-component edges `151 -> 141`, classifications
  `151 -> 141`, graph nodes `164 -> 154`, and graph edges `300 -> 290`, with
  no added root, edge, or cycle.
- [x] The isolated inventory measured `110` facades, `69` qualified
  candidates, `41` holds, `116` static consumers, `779` text references, and
  no canonical-package or public-example consumer.
- [x] The isolated contract ledger measured `110` cards, `85` exact aliases,
  `35` facades with durable pickle globals, and `92` retained contract tests.
- [x] All 154 architecture, inventory, and compatibility-contract tests passed
  in the mirror.
- [x] All 900 root tests passed with mirrored workspace sources and the
  localhost skill bridge enabled, including host mediation, Python transport,
  virtual mounts, Wasm execution, capability mapping, and runtime temporary
  policy behavior.
- [x] Apply this cohort only after the first semantic cohort has completed its
  independent deletion, qualification, and rollback cycle.

Accepted deletion evidence, captured on 2026-10-30:

- [x] The sequential architecture delta is strictly smaller: owned roots
  `121 -> 111`, combined graph nodes `157 -> 147`, combined edges `293 -> 283`,
  and grandfathered observations `163 -> 153`, with zero cyclic nodes and no
  added dependency observation.
- [x] The retained inventory contains `103` facades, `109` static consumers,
  `62` qualified candidates, `41` holds, and `17` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `103` cards, `78` exact aliases,
  `35` facades with `133` durable pickle globals, and `90` facade contract
  tests.
- [x] The focused architecture/compatibility suite passed `153` tests; the
  root suite passed `899` tests and a clean workstation rerun passed `633`
  tests with one expected skip.
- [x] The first workstation run had one late Textual timing assertion failure;
  the exact case then passed four consecutive normal-composition reruns, and
  the complete clean rerun passed. No removed alias participates in that UI
  path and no implementation was changed to mask it.
- [x] The targeted skill-routing, report-creation, and incremental-publication
  BDD passed `38` cases; all `35` wheels and source distributions built and
  imported in isolation; publication capture reproduced eight actions and two
  artifacts; Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the ten aliases, their identity assertions,
  active root-ledger entries, and tombstones; canonical runtime behavior,
  host realization, state, and receipts remain unchanged.

### Governance Alias Deletion Cohort Review

The third proposed deletion cohort contains two exact aliases assigned to the
governance responsibility while delegating to canonical controller-engine
modules. They are kept separate from runtime leaves because their affected
qualification surface is governed current-use and runtime-governance
resolution.

| Historical import | Canonical replacement |
| --- | --- |
| `governed_skill_access` | `realized_core_engine.governed_skill_access` |
| `runtime_governance_context` | `realized_core_engine.runtime_governance_context` |

Reviewed evidence:

- [x] Both files are exact `sys.modules` aliases with `module_alias_only`
  import effects, exact module-object identity, no executable surface, and no
  known durable pickle global.
- [x] Both are `repository_internal`, have no non-contract consumer or
  blocking reference, and have one canonical target.
- [x] The isolated architecture delta removed only two roots, two
  root-to-component observations, two classifications, two graph nodes, and
  two graph edges; it added nothing and retained zero cycles.
- [x] The isolated inventory measured `118` facades, `77` qualified
  candidates, `41` holds, `124` static consumers, `802` text references, and
  no canonical-package or public-example consumer.
- [x] The isolated contract ledger measured `118` cards, `93` exact aliases,
  `35` facades with durable pickle globals, and `92` retained contract tests.
- [x] All 234 real focused architecture, governance-selection, function, and
  host-mediation tests passed; the only initial loader error named a nonexistent
  `tests.test_skill_governance` module and was not a product result.
- [x] All 103 `realized-core-governance` package tests passed.
- [x] All 900 root tests passed with mirrored workspace sources and the
  localhost skill bridge enabled.
- [x] Apply this cohort only after the semantic and runtime-leaf cohorts have
  completed independent deletion, qualification, and rollback cycles.

Accepted deletion evidence, captured on 2026-10-30:

- [x] The sequential architecture delta removed only two owned roots, graph
  nodes, graph edges, root-to-component observations, and classifications:
  owned roots `111 -> 109`, combined nodes `147 -> 145`, combined edges
  `283 -> 281`, and grandfathered observations `153 -> 151`, with no addition
  or cycle.
- [x] The retained inventory contains `101` facades, `107` static consumers,
  `60` qualified candidates, `41` holds, and `19` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `101` cards, `76` exact aliases,
  `35` facades with `133` durable pickle globals, and `90` facade contract
  tests.
- [x] The architecture/compatibility suite passed `153` tests, the canonical
  governance package passed `103` tests, and all `80` governance-selection,
  function-boundary, and host-mediation tests passed under normal application
  composition.
- [x] Directly loading the three integration modules without application
  composition exposed the existing artifact-repository-provider prerequisite;
  the composed run passed without production or test changes and the full root
  suite subsequently passed all `899` tests.
- [x] The workstation suite passed `633` tests with one expected skip; the
  targeted BDD passed `38` cases; all `35` distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the two historical aliases, identity-test
  entries, active root-ledger entries, and tombstones; canonical current-use
  and runtime-governance behavior remain unchanged.

### Blend Application Alias Deletion Cohort Review

The fourth deletion cohort contains four exact aliases for concrete Blend
application translation and JSON repository adapters. The canonical
implementations already live in the independently buildable
`realized-blend-application` project; this cut removes only redundant root
import paths.

| Historical import | Canonical replacement |
| --- | --- |
| `blend_workflow` | `realized_blend_application.workflows` |
| `blend_workflow_store` | `realized_blend_application.workflow_store` |
| `blend_world` | `realized_blend_application.worlds` |
| `blend_world_store` | `realized_blend_application.world_store` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] All four files were pure exact `sys.modules` aliases with no executable
  surface, non-contract consumer, blocking reference, or known durable pickle
  global, and each had one unambiguous canonical replacement.
- [x] Canonical Blend workflow/world behavior comparisons remain in the
  compatibility suite; only assertions for the removed root module identities
  were deleted.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `109 -> 105`, combined nodes `145 -> 141`, combined edges `281 -> 277`, and
  grandfathered observations `151 -> 147`, with no addition or cycle.
- [x] The retained inventory contains `97` facades, `103` static consumers,
  `56` qualified candidates, `41` holds, and `23` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `97` cards, `72` exact aliases,
  `35` facades with `133` durable pickle globals, and `90` facade contract
  tests.
- [x] Qualification passed `153` focused architecture/compatibility tests,
  `40` Blend tests, all `899` root tests, `633` workstation tests with one
  expected skip, and `38` targeted skill-routing/report/publication BDD cases.
- [x] All `35` wheels and source distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the four historical aliases, identity-test
  entries, active root-ledger entries, and tombstones; canonical Blend domain
  and application behavior remain unchanged.

### Subject-Core Alias Deletion Cohort Review

The fifth deletion cohort contains nine exact aliases for deterministic
subject-domain policy, projection, Gather persistence, learning-context
rendering, and publication behavior. The URL learning-capture alias is not in
this cohort because its canonical owner is `subject_service` and its browser
and extraction qualification surface is distinct.

| Historical import | Canonical replacement |
| --- | --- |
| `decision_review_policy` | `workstation.subject.core.decision_review_policy` |
| `decision_review_projection` | `workstation.subject.core.decision_review_projection` |
| `gather_sources` | `workstation.subject.core.gather_sources` |
| `learning_context_markdown` | `workstation.subject.core.learning_context_markdown` |
| `learning_context_projection` | `workstation.subject.core.learning_context_projection` |
| `publication` | `workstation.subject.core.publication` |
| `publication_projection` | `workstation.subject.core.publication_projection` |
| `publication_render` | `workstation.subject.core.publication_render` |
| `publication_validation` | `workstation.subject.core.publication_validation` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] All nine files were pure exact `sys.modules` aliases with no executable
  surface, non-contract consumer, blocking reference, or known durable pickle
  global, and each had one unambiguous canonical replacement.
- [x] Production, package, and behavior tests already imported the canonical
  subject-core modules; only root-module identity assertions were removed.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `105 -> 96`, combined nodes `141 -> 132`, combined edges `277 -> 268`, and
  grandfathered observations `147 -> 138`, with no addition or cycle.
- [x] The retained inventory contains `88` facades, `94` static consumers,
  `47` qualified candidates, `41` holds, and `32` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `88` cards, `63` exact aliases,
  `35` facades with `133` durable pickle globals, and `82` facade contract
  tests.
- [x] Qualification passed `145` focused architecture/compatibility tests,
  `65` subject-domain/distribution tests, all `891` root tests, `633`
  workstation tests with one expected skip, and `38` targeted
  skill-routing/report/publication BDD cases.
- [x] All `35` wheels and source distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the nine historical aliases, identity-test
  entries, active root-ledger entries, and tombstones; canonical subject policy,
  persistence, projection, rendering, validation, and workflow behavior remain
  unchanged.

### Subject-Service Alias Deletion Cohort Review

The sixth deletion cohort contains the single exact alias for the external URL
learning-capture adapter. It follows the subject-core cohort separately so its
browser, extraction, source-bundle, and service-distribution behavior is
qualified as one responsibility surface.

| Historical import | Canonical replacement |
| --- | --- |
| `url_learning_capture` | `workstation.subject.service.url_learning_capture` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] The file was a pure exact `sys.modules` alias with no executable surface,
  non-contract consumer, blocking reference, or known durable pickle global,
  and one unambiguous canonical replacement.
- [x] Runtime callers, tests, and patch targets already used the canonical
  subject-service module; only the root identity assertion was removed.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `96 -> 95`, combined nodes `132 -> 131`, combined edges `268 -> 267`, and
  grandfathered observations `138 -> 137`, with no addition or cycle.
- [x] The retained inventory contains `87` facades, `93` static consumers,
  `46` qualified candidates, `41` holds, and `33` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `87` cards, `62` exact aliases,
  `35` facades with `133` durable pickle globals, and `81` facade contract
  tests.
- [x] Qualification passed `144` focused architecture/compatibility tests,
  seven URL-capture and subject-service distribution tests, all `890` root
  tests, `633` workstation tests with one expected skip, and `38` targeted
  skill-routing/report/publication BDD cases.
- [x] All `35` wheels and source distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the historical alias, identity-test entry,
  active root-ledger entries, and tombstone; canonical browser acquisition,
  fallback extraction, source-bundle persistence, and service behavior remain
  unchanged.

### Validation Alias Deletion Cohort Review

The seventh deletion cohort contains two exact aliases for development-tooling
validation orchestration and disposable/durable SQLite report handling. The
canonical `realized-validation` project is dependency-free and already owns
all callers and tests.

| Historical import | Canonical replacement |
| --- | --- |
| `validation_ladder` | `realized_validation.ladder` |
| `validation_sqlite` | `realized_validation.sqlite_runtime` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] Both files were pure exact `sys.modules` aliases with no executable
  surface, static consumer, blocking reference, or known durable pickle
  global, and each had one unambiguous canonical replacement.
- [x] Validation tests, CLI integration, and package distribution already used
  `realized_validation`; package documentation was updated to stop advertising
  the retired root imports.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `95 -> 93`, combined nodes `131 -> 129`, combined edges `267 -> 265`, and
  grandfathered observations `137 -> 135`, with no addition or cycle.
- [x] The retained inventory contains `85` facades, `93` static consumers,
  `44` qualified candidates, `41` holds, and `35` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `85` cards, `60` exact aliases,
  `35` facades with `133` durable pickle globals, and `81` facade contract
  tests.
- [x] Qualification passed `144` focused architecture/compatibility tests, ten
  validation ladder/SQLite/distribution tests, all `890` root tests, `633`
  workstation tests with one expected skip, and `38` targeted
  skill-routing/report/publication BDD cases.
- [x] All `35` wheels and source distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the two aliases, active root-ledger entries,
  tombstones, and package documentation; canonical validation command ordering,
  report capture, SQLite allocation, and archival behavior remain unchanged.

### Exchange Exact-Alias Deletion Cohort Review

The eighth deletion cohort contains ten exact aliases for artifact exchange,
portable-skill schema and compilation, compatibility translation, registry and
run-bundle projection, and learning-context skill materialization. The
canonical `realized-exchange` project already owns every implementation and
ordinary consumer.

| Historical import | Canonical replacement |
| --- | --- |
| `learning_context_skill_projection` | `realized_exchange.learning_context_skills` |
| `run_bundle_io` | `realized_exchange.run_bundle` |
| `side` | `realized_exchange.artifact_yaml` |
| `side_runtime_dependencies` | `realized_exchange.dependencies` |
| `skill_compatibility_export` | `realized_exchange.compatibility_export` |
| `skill_compatibility_import` | `realized_exchange.compatibility_import` |
| `skill_compiler` | `realized_exchange.compiler` |
| `skill_export_projection` | `realized_exchange.skill_export` |
| `skill_registry` | `realized_exchange.registry` |
| `skill_schema_io` | `realized_exchange.skill_schema` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] All ten files were pure exact `sys.modules` aliases with no executable
  surface, non-contract consumer, blocking reference, or known durable pickle
  global, and each had one unambiguous canonical replacement.
- [x] Exchange behavior tests, entrypoints, replay paths, workstation
  composition, and distributions already used `realized_exchange`; the held
  `learning_context` facade and the separately reviewed Markdown/controller
  aliases remain untouched.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `93 -> 83`, root-boundary classifications `116 -> 106`, combined nodes
  `129 -> 119`, combined edges `265 -> 255`, and grandfathered observations
  `135 -> 125`, with no addition or cycle.
- [x] The retained inventory contains `75` facades, `83` static consumers,
  `34` qualified candidates, `41` holds, and `45` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `75` cards, `50` exact aliases,
  `35` facades with `133` durable pickle globals, and `79` facade contract
  tests.
- [x] Qualification passed `142` focused architecture/compatibility tests,
  `65` canonical exchange behavior tests, five isolated exchange
  distribution/workstation tests, all `888` root tests, `633` workstation
  tests with one expected skip, and `38` targeted
  skill-routing/report/publication BDD cases.
- [x] All `35` wheels and source distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the ten aliases, facade-only assertions, active
  root-ledger entries, tombstones, and exchange documentation; canonical
  exchange parsing, translation, compilation, projection, registry,
  run-bundle, and learning-context behavior remain unchanged.

### Controller Binding Alias Deletion Cohort Review

The ninth deletion cohort contains the single exact alias for the engine-owned
controller factory registration seam.

| Historical import | Canonical replacement |
| --- | --- |
| `controller_runtime_binding` | `realized_core_engine.controller_runtime_binding` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] The file was a pure exact `sys.modules` alias with no executable surface,
  non-contract consumer, blocking reference, or known durable pickle global,
  and it had one unambiguous canonical replacement.
- [x] Engine controller construction already imports the canonical binding;
  runtime hygiene rejects root-binding reach-through, and no production caller
  depended on the historical module identity.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `83 -> 82`, root-boundary classifications `106 -> 105`, combined nodes
  `119 -> 118`, combined edges `255 -> 254`, and grandfathered observations
  `125 -> 124`, with no addition or cycle.
- [x] The retained inventory contains `74` facades, `82` static consumers,
  `33` qualified candidates, `41` holds, and `46` total tombstones, with no
  canonical-package or public-example consumer.
- [x] The retained contract ledger contains `74` cards, `49` exact aliases,
  `35` facades with `133` durable pickle globals, and `79` facade contract
  tests.
- [x] Qualification passed `146` focused architecture/runtime-hygiene tests,
  all `882` applicable non-provider root tests, `632` applicable non-provider
  workstation tests, and `38` deterministic skill-routing/report/publication
  BDD cases.
- [x] Provider-backed markdown and live-publication tests are outside this
  non-model binding cohort and are not claimed as passing; their seven cases
  remain separately gated on explicit external-data authorization.
- [x] All `35` wheels and source distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis and all `51` widget tests passed.
- [x] Rollback remains local to the alias, facade-only identity assertion,
  active root-ledger entries, tombstone, and module documentation; canonical
  controller registration and construction behavior remain unchanged.

### Persistence Alias Deletion Cohort Review

The tenth deletion cohort contains the single exact alias for the core-engine
SQLite and in-memory artifact-store implementation.

| Historical import | Canonical replacement |
| --- | --- |
| `store` | `realized_core_engine.store` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] The file was a pure exact `sys.modules` alias with no executable surface,
  non-contract consumer, blocking reference, or facade-owned pickle global,
  and it had one unambiguous canonical replacement.
- [x] The former trial consumer already imports `realized_core_engine.store`;
  production code, tests outside the compatibility contract, and workspace
  distributions use the canonical engine module directly.
- [x] Removing the alias does not change durable class identity: the exported
  classes are defined by `realized_core_engine.store`, so the root alias never
  supplied a distinct persisted qualified name.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `82 -> 81`, root-boundary classifications `105 -> 104`, combined nodes
  `118 -> 117`, combined edges `254 -> 253`, and grandfathered observations
  `124 -> 123`, with 35 components, 141 package edges, no addition, and no
  cycle.
- [x] The retained inventory contains `73` facades, `80` static consumers,
  `32` qualified candidates, `41` holds, and `47` total tombstones, with no
  canonical-package, public README, or public-example consumer.
- [x] The retained contract ledger contains `73` cards, `48` exact aliases,
  `35` facades with `133` durable pickle globals, and `79` facade contract
  tests.
- [x] Qualification passed `314` focused architecture, persistence,
  determinism, artifact-selection, and Markdown-artifact tests, all `882`
  applicable non-provider root tests, `632` applicable non-provider
  workstation tests, and `38` deterministic skill-routing/report/publication
  BDD cases.
- [x] Provider-backed Markdown-learning and live-publication tests are outside
  this non-model persistence-alias cohort and are not claimed as passing; their
  seven cases remain separately gated on explicit external-data authorization.
- [x] All `35` wheels and source distributions built and imported in
  isolation; publication capture reproduced eight actions and two artifacts;
  Flutter analysis found no issues and all `51` widget tests passed.
- [x] Rollback remains local to the historical alias, facade-only identity
  assertion, active root-ledger entry, tombstone, and module documentation;
  canonical artifact-store behavior, SQLite schema, persisted values, and
  selection semantics remain unchanged.

### Controller Selection Alias Deletion Cohort Review

The eleventh deletion cohort contains six exact aliases for semantic request
posture, direct-knowledge reuse, fallback elaboration, and retrieval ranking.

| Historical import | Canonical replacement |
| --- | --- |
| `direct_knowledge_reuse` | `realized_core_engine.direct_knowledge_reuse` |
| `fallback_not_generation` | `realized_core_engine.fallback_not_generation` |
| `not_elaboration_ranking` | `realized_core_engine.not_elaboration_ranking` |
| `prompt_directives` | `realized_core_engine.prompt_directives` |
| `retrieval_ranking` | `realized_core_engine.retrieval_ranking` |
| `semantic_prompt_posture` | `realized_core_engine.semantic_prompt_posture` |

Reviewed and accepted evidence, captured on 2026-10-30:

- [x] All six files were pure exact `sys.modules` aliases with no executable
  surface, non-contract consumer, blocking reference, facade-owned pickle
  global, or distinct import effect, and each had one canonical engine target.
- [x] The retained `fallback_not_semantics` symbol facade now proves its two
  exported symbol identities directly against the canonical fallback and
  ranking modules; canonical behavior coverage was preserved while only root
  module-identity assertions were removed.
- [x] The sequential architecture delta only shrank the graph: owned roots
  `81 -> 75`, root-boundary classifications `104 -> 98`, combined nodes
  `117 -> 111`, combined edges `253 -> 247`, and grandfathered observations
  `123 -> 117`, with 35 components, 141 package edges, no addition, and no
  cycle.
- [x] The retained inventory contains `67` facades, `74` static consumers,
  `26` qualified candidates, `41` holds, and `53` total tombstones, with no
  canonical-package, public README, or public-example consumer.
- [x] The retained contract ledger contains `67` cards, `42` exact aliases,
  `35` facades with `133` durable pickle globals, and `78` facade contract
  tests.
- [x] Qualification passed `362` focused architecture, function-boundary,
  answer-selection, ranking, prompt-posture, and governance-precedence tests,
  all `881` applicable non-provider root tests, and a clean rerun of all `632`
  applicable non-provider workstation tests.
- [x] The first workstation run had one late Textual state/timing assertion;
  the exact normal-composition case then passed four consecutive reruns, and
  the complete clean rerun passed. None of the removed aliases participates in
  that UI state transition, and no production or test code was changed to mask
  it.
- [x] Provider-backed Markdown-learning and live-publication tests are outside
  this non-model controller-selection cohort and are not claimed as passing;
  their seven cases remain separately gated on explicit external-data
  authorization.
- [x] All `38` deterministic skill-routing/report/publication BDD cases passed;
  all `35` wheels and source distributions built and imported in isolation;
  publication capture reproduced eight actions and two artifacts; Flutter
  analysis found no issues and all `51` widget tests passed.
- [x] Rollback remains local to the six historical aliases, facade-only
  identity assertions, active root-ledger entries, tombstones, and module
  documentation; canonical request posture, direct reuse, fallback generation,
  retrieval ranking, and answer-selection behavior remain unchanged.

## Phase 5 - Retire Low-Risk Alias Cohorts

Start with exact aliases that have no non-test consumers, no import-time
composition, no persisted qualified-name obligation, and one unambiguous
canonical replacement.

Within that set, use lower-owner-first, owner-cohesive cohorts:

1. semantic value aliases
2. host-interaction and runtime leaf aliases
3. governance aliases
4. portable-skill and skill-application aliases
5. Blend domain/application aliases
6. subject-domain aliases
7. controller and exchange aliases

This ordering is a default, not a substitute for the measured dependency
graph. A generated cohort must be split whenever its consumers, support state,
or qualification surface differ.

For each cohort:

- [ ] Open a consumer-migration change, with no facade deletion.
- [ ] Complete and record the required qualification cycle.
- [ ] Open a separate deletion change containing only eligible facade removal,
  facade-specific test removal, architecture-control updates, and docs.
- [ ] Run the architecture checker before updating baselines and verify that
  every reported delta is a removal.
- [ ] Remove the facade from root ownership/status and compatibility policy,
  retaining its tombstone.
- [ ] Regenerate the compatibility inventory and dependency report.
- [ ] Refresh the architecture baseline only after reviewing the exact delta.
- [ ] Run focused compatibility, package, behavior, and isolated-distribution
  tests.
- [ ] Run the complete qualification ladder required by the cohort.
- [ ] Verify rollback by restoring only the deleted facade and its contract
  test against unchanged canonical packages.

Exit condition:

- [ ] All simple aliases are removed or explicitly held with recorded evidence.

## Phase 6 - Retire Re-Export And Aggregate Facades

These surfaces require symbol-level migration rather than module substitution.

- [ ] Retire the 19 symbol re-export facades only after every relied-on public
  and private alias has a deliberate canonical target.
- [ ] Prove old and canonical symbols have the required identity before removal;
  do not recreate historical private names in canonical packages solely to
  make deletion easy.
- [ ] Split callers of `normalize` across the actual semantic and controller
  owners rather than creating another aggregate normalization module.
- [ ] Verify wildcard imports and generated `__all__` consumers explicitly.
- [ ] Verify historical pickle globals and repr expectations with old fixtures.
- [ ] Apply the same two-change migration/qualification/deletion protocol used
  for exact aliases.

Exit condition:

- [ ] No aggregate compatibility API obscures canonical ownership.

## Phase 7 - Resolve Behavior-Bearing Compatibility Adapters

The following modules are not eligible for mechanical deletion:

- `blend_context` and `blend_session` combine canonical Blend values with
  workstation projection helpers.
- `itemize` supplies a historical implicit controller bootstrap when direct
  decomposition is requested without an explicit proposal port.
- `controller_runtime` mutates the canonical controller module with entry,
  exchange, and optional Markdown extension surfaces at import time.
- `main` is both an executable path and an import-identity alias.

For each adapter:

- [ ] Decide whether the adapter behavior remains supported.
- [ ] If supported, expose it through the correct existing application or
  composition package in a separate additive change; do not move it into a
  lower canonical domain package.
- [ ] If unsupported, document the behavior being retired and its replacement.
- [ ] Add direct equivalence tests for the supported path before migrating any
  consumer.
- [ ] Eliminate implicit import-order registration in favor of explicit
  application composition where required.
- [ ] Complete a stable qualification cycle after the replacement path becomes
  authoritative.
- [ ] Remove the facade only in a later deletion change.

Specific dependency order:

- [ ] Retire `itemize` before `runtime_controller_api`, because the former is a
  facade consumer of the latter.
- [ ] Retire `main` before `controller_entrypoint_binding` and
  `controller_runtime`, because `main` consumes both.
- [ ] Retire `main` last among executable/import aggregate surfaces, after all
  scripts, validators, build specs, qualification gates, docs, and runtime
  command assembly use packaged entrypoints.

Exit condition:

- [ ] No compatibility file owns composition behavior or executable routing.

## Per-Deletion Change Protocol

Every deletion change must contain:

- [ ] the facade file deletion
- [ ] removal of facade-only tests, while canonical behavior tests remain
- [ ] a tombstone/policy transition to `removed`
- [ ] removal of root ownership/status and boundary-classification entries
- [ ] regenerated compatibility inventory
- [ ] regenerated dependency report
- [ ] a reviewed shrinking-only architecture baseline update
- [ ] migration documentation and release note where required
- [ ] focused and global qualification evidence

Every deletion change must exclude:

- [ ] canonical implementation movement
- [ ] new public APIs unrelated to an already qualified replacement
- [ ] semantic or workflow changes
- [ ] persisted-format migrations
- [ ] opportunistic renames or cleanup
- [ ] unrelated baseline changes

## Required Qualification Gates

The following are mandatory for every cohort:

- [ ] architecture ratchet
- [ ] compatibility facade inventory and retirement-policy checks
- [ ] workspace wheel/sdist isolation
- [ ] facade-specific canonical behavior tests
- [ ] root and affected package unit tests
- [ ] serialized-old-material compatibility tests where applicable

Add affected gates according to ownership:

- [ ] controller/runtime: LLM-off run/resume/inspect, replay, host bridge,
  SQLite, and deterministic decision-path tests
- [ ] governance/skills/exchange: admission, current-use, authority,
  import/export, trial routing, and exact realizer binding tests
- [ ] subject/publication: Gather-to-Publication BDD, incremental publication,
  reference artifact hashes, and gRPC contract tests
- [ ] workstation-facing: Textual tests, Flutter analysis/widget tests, and
  affected browser/screenshot flows
- [ ] executable surfaces: packaged CLI equivalence, exit status, stdout/stderr,
  environment, PyInstaller/build configuration, and clean-host invocation
- [ ] provider-backed surfaces: the relevant authorized provider gate; prior
  evidence cannot substitute when the changed facade owned provider wiring

Performance-sensitive cohorts must use the qualification policy's three-run
median and p95 thresholds.

### Current Consumer-Migration Qualification

The 2026-10-30 consumer-migration and control-plane slice passed:

- [x] compatibility inventory and architecture ratchet
- [x] 153 architecture and compatibility-contract tests
- [x] 900 root tests
- [x] 633 workstation tests, with one expected skip
- [x] 35 wheel builds, 35 source distributions, and 35 isolated public-module
  imports
- [x] affected core-engine and DST tests
- [x] deterministic trial-skill, report-publication, and incremental-report
  BDD paths
- [x] deterministic publication reference capture: eight actions and two
  artifacts, with no reference diff
- [x] Flutter static analysis and all 51 widget tests

Provider-backed trials and browser/screenshot integration gates were not run.
They remain mandatory when a future cohort changes provider wiring, browser
integration, executable composition, or a UI-facing contract; this slice did
not change those surfaces.

## Rollback Rule

Rollback restores the deleted compatibility facade and its narrow contract
test, then restores the prior architecture policy/baseline entries. It must not
roll back canonical packages or consumer migrations unless those changes are
independently defective.

If restoring only the facade cannot recover behavior, the deletion cohort was
not properly isolated and must not be accepted.

## Completion Criteria

- [ ] The observed compatibility-facade count is zero, or every remaining
  facade is explicitly held with owner, reason, and review condition.
- [ ] No canonical package, root module, trial, test, script, build file,
  qualification gate, runnable documentation, or persisted fixture depends on
  a removed facade.
- [ ] Removed imports and executable paths have documented canonical
  replacements.
- [ ] All supported external removals satisfied their notice policy.
- [ ] Every removal is represented by a tombstone and rejected on
  reintroduction.
- [ ] All workspace distributions remain independently buildable and runnable.
- [ ] The combined package/root graph remains acyclic with no undeclared or
  forbidden edge.
- [ ] Full behavioral qualification remains green, including BDD, publication,
  replay, Textual, Flutter, trials, and provider-backed gates where affected.
- [ ] Root files that remain are deliberate entrypoints or validation/trial
  programs, not unmeasured compatibility behavior.

## Recommended First Implementation Slice

The first change should alter controls only, not remove a facade:

- [x] introduce persistent retirement policy separate from generated facts
- [x] add facade-shape classification and tombstones
- [x] broaden reference discovery to commands, patch strings, configuration,
  and serialized qualified names
- [x] make new facade consumers fail CI outside designated contract tests
- [x] generate a candidate/hold report from the existing 120 facades
- [x] prove all current default architecture and qualification gates remain
  unchanged

Only after that slice is green should the first low-risk exact-alias cohort be
selected.
