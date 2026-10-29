# MODULES

Terse repository map. Read this file before editing Python modules.

Top-line rule used in Python files:
- `# See MODULES.md for the repository module map before editing.`

## Workstation Distribution Boundaries

- `workstation/contracts_api/` publishes `workstation.contracts`, the stable,
  transport-neutral API/ABI surface for subject workflow, shell, and event types.
  It may contain dataclasses, runtime-checkable protocols, and deterministic
  routing helpers, but no runtime, UI, service, adapter, or provider imports.
- `workstation/runtime_core/` owns workstation runtime execution, the
  workstation conversation/tool loop, caller-specific provider policy, and
  projection-event subscriber control. It also realizes optional direct
  itemization proposals through the injected controller-runtime provider,
  returning only controller-neutral subject values. Its LLM driver consumes the stateless
  typed transport exported by `realized-core-llm`; it does not import or invoke
  a provider SDK directly.
- `workstation/subject_core/` is the canonical subject-domain owner. Its staged
  extraction currently owns subject workflow coordination, host-effect ports,
  Gather source persistence, itemization extraction, continuity and
  persistence, itemization validation, the canonical learning-context
  aggregate, corpus/decision-review path vocabulary, and authoritative corpus
  JSON/index persistence. It also owns deterministic `subject.md` and
  `subject.typ` rendering plus projected-skill identity derivation, without
  compiling or writing portable skill exchange documents. It owns CTFS-backed decision
  policy, analysis projection and receipts, and publication values,
  validation, projection, and rendering. Historical root modules remain compatibility
  aliases while the remaining learning, itemization, decision-review, and
  review-composition dependencies move in reverse-topological cuts. Optional
  direct itemization uses a typed outbound proposal port and never receives a
  controller or runtime state object.
- `workstation/subject_service/` owns the subject workflow application service,
  client-session registry, markdown-to-subject learning-capture application
  service, persist-then-project learning-context coordination, derived-skill
  document construction, external URL acquisition adapter, and subject
  in-process/gRPC client adapters. Exchange materialization is supplied through
  a caller-composed callback; this package does not import YAML or compiler
  adapters. The historical root `url_learning_capture` path is an exact module
  alias to this package-owned adapter.
- `workstation/shell_core/` owns shell application services, chat orchestration,
  and shell in-process/gRPC client adapters. Its additive governed-conversation
  mode composes the public `realized-core-conversation` application surface and
  `realized-core-llm` provider adapter directly; it does not depend on the
  `realized-core` CLI package or duplicate product planning behavior.
- `workstation/foundation_events/` owns event publication. Its historical
  `subscriber_controllers` module is a compatibility alias to `runtime_core`.
- `workstation/foundation_host/` owns the workstation-backed host adapter. Its
  historical `client_sessions`, `learning_capture`, and `llm_driver` modules
  are compatibility aliases to `subject_service`, `subject_service`, and
  `runtime_core`, respectively. Its process-local
  controller, subject-client, artifact-repository, and skill-exchange providers
  are composition seams: entry modules register concrete adapters, while
  runtime and UI consumers receive only the corresponding contracts.
- `workstation/shell_core/.../shell_prompt_routing.py` is a compatibility alias to
  the deterministic helper in `workstation.contracts.shell_prompt_routing`.
- `workstation/grpc_implementation/` owns gRPC server adapters; protobuf message
  definitions remain in `workstation/grpc_definitions/`.
- `workstation/ui_textual/`, `workstation/subject_textual/`, and
  `workstation/ui_flutter/` are clients of the application/contracts boundary, not
  owners of workflow behavior. `subject_textual` adapts transport-neutral subject
  views for terminal widgets and depends only on `workstation.contracts`; the
  entry layer injects the configured subject client into `ui_textual`.

Compatibility paths are intentionally retained through the current qualification
cycle. Canonical imports should use the owners above; do not add new consumers to
legacy aliases.

## Core Runtime, Theory, Governance, and Exchange
- `coordinated_transformation/`: Independently buildable, dependency-free
  `coordinated-transformation` UV project. It owns the snapshot-local CTFS
  carriers, relations, admissibility, readiness, risk, decision validity,
  executability, reachability, and axiom checks used by subject decision
  analysis. It does not discover facts from prose, revise model snapshots,
  invoke models or hosts, persist workflow state, or own workstation behavior.
- `dst/`: Measured `dst` UV workspace project for the cohesive Decision Support
  Tool subdomain. Its `src/dst` package owns the checked-in source cases, typed
  fixtures, governed candidate-path discovery, strict normalization, CTFS
  projection, and revision substrate. It is independently buildable and
  importable without repository-root modules. Live proposal orchestration
  accepts an explicit controller-bootstrap port; subject workflow supplies that
  port through its host-actions contract, and the executable composition root
  binds it to the application controller runtime.
- `core_semantics/`: Independently buildable `realized-core-semantics` UV
  project. It owns the Pydantic formal-theory value model and narrow read-only
  artifact protocols, plus dependency-light Prolog-title representation,
  semantic-text normalization, semantic-title derivation, stable proposal
  vocabulary, subject identity, itemization values, decision-review values,
  transformation-construct candidate projection, Markdown IR parsing and
  deterministic semantic views, identifier, timestamp, and JSON value
  projection helpers. It contains no governance decisions,
  persistence, controller orchestration, model calls, host execution, or
  workstation code. `pure_theory_types.py`, `artifact_contracts.py`,
  `prolog.py`, `semantic_text.py`, `title_semantics.py`, `itemize_models.py`,
  `decision_review_models.py`, and `markdown_ir.py` are historical facades.
- `blend/`: Independently buildable `realized-blend` UV project. It owns the
  dependency-light Blend domain values and pure rules for context, actors,
  operator descriptors, opaque invocation handles, catalog providers,
  deterministic query/resolution, and applicability, plus sessions, worlds,
  workflow plans and runs, authoritative history references, coordination
  records, execution observations, generic workflow resolution, and
  port-driven workflow orchestration. Composition, operator invocation,
  persistence, clock, identifier, and best-effort observation are explicit
  outbound protocols. It depends only
  on `realized-core-semantics` and imports no workstation, runtime, governance
  implementation, event transport, filesystem adapter, UI, or provider code.
  Workstation context/session projection lives in
  `workstation.runtime.core.blend_adapters`; skill-compose conversion, JSON
  repository adapters, concrete skill execution, governance, host effects, and
  event publication remain outside this package. Canonical workflow/world
  repository and execution protocols are injected through
  `realized_blend.ports`. Historical root Blend paths remain qualified
  compatibility surfaces during the migration cycle.
- `blend_application/`: Independently buildable `realized-blend-application`
  UV project. It owns concrete artifact/capability-to-operator projection,
  skill-compose/workflow translation, skill-composition execution adaptation,
  and JSON workflow/world repository adapters for the dependency-light Blend
  domain. It depends only on Blend plus core runtime/semantic and skill
  application/semantic contracts. It does not own Blend values, workstation
  sessions, request-to-ability selection, governance decisions, host-realizer
  provision, model invocation, or exchange parsing. The six historical root
  Blend adapter paths preserve exact module identity as compatibility aliases.
- `core_governance/`: Independently buildable `realized-core-governance` UV
  project. Its first package-native cut owns governed-skill vocabulary,
  deterministic normalization, lifecycle states, conservative lifecycle
  synthesis, read-only artifact lifecycle projection, lifecycle-only
  current-use eligibility, approval-record normalization/projection/matching,
  and revocation/incident normalization, matching, and supplied-record safety
  overlays, stored declaration/policy/admission projection, governed v2 skill
  declaration and admission-policy normalization, reviewable policy summaries,
  read-only inventory loading and independent governance-record classification
  through a structural port, policy-and-approval admission evaluation over
  supplied records and an injected clock, final current-use eligibility over a
  supplied schema, admission, and already-composed effective lifecycle,
  deny-by-default authority coverage over a supplied required authority and
  invocation grants, a structural batch-writer port that forwards
  already-prepared governed artifacts without owning storage mechanics, plus
  data-class normalization and supplied-context data-access rules. It depends
  only on `realized-core-semantics` and
  `realized-skill-semantics`; it does not parse YAML, synthesize declarations
  from artifacts or host code, inspect broker availability or executable
  source, retrieve or recompute current-use state, issue authority, implement
  persistence, manage inventory cache lifetime, open virtual mounts, connect to
  SQLite, define schemas or transactions, execute queries, invoke host brokers,
  execute skills, invoke models, or own controller/workstation behavior. The
  root admission orchestrator
  retains host preflight, assembles concrete current-use state, and delegates
  only portable policy-and-approval and final eligibility decisions. Retrieval
  and semantic ranking remain controller concerns, but controller consumers
  must apply final current-use eligibility before promoting a retrieved
  governed artifact as an answer or invocation candidate.
  `skill_governance_primitives.py`, `skill_lifecycle.py`,
  `approval_governance.py`, `skill_safety_governance.py`, and
  `data_governance.py` are historical identity-preserving facades.
- `skill_semantics/`: Independently buildable `realized-skill-semantics` UV
  project. It owns the portable canonical skill IR value, alias/family identity
  metadata, immutable invocation request/result values, immutable composition
  plan and static-analysis result values, deterministic invocation mapping
  normalization, supported declaration schema versions, deterministic
  schema-version normalization, explicit composition-right target projection,
  portable executor descriptor vocabulary, descriptor alias normalization,
  deterministic descriptor inference, executable-content field selection,
  typed-leaf ledger, boundary-region polarity, reconstructible canonical path
  notation, and normalization of explicit boundary values
  shared by skill projection, composition, and planning. It
  depends only on `realized-core-semantics` and contains no admission,
  authority, lifecycle, persistence, host-availability, provider,
  prerequisite, execution, effect, model, or workstation behavior.
  `skill_leaf_types.py` and `skill_path_notation.py` are historical facades.
- `skill_application/`: Independently buildable `realized-skill-application`
  UV project. It owns artifact-to-skill normalization, governed-artifact IR
  and skill-kind projection, and explicit composition-plan analysis and execution. It depends
  only on core semantic, governance, runtime, and portable skill contracts; it
  does not parse exchange formats, persist artifacts, manage workstation
  sessions, discover host realizers, or invoke models. The historical root
  skill normalization, IR, and composition modules preserve their import
  identities as compatibility aliases.
- `exchange/`: Independently buildable `realized-exchange` UV project. It owns
  artifact-bundle YAML parsing/rendering, portable-skill schema hydration,
  canonical bundle export and naming, supported foreign-format translation,
  portable-skill compilation, learning-context derived-skill YAML
  materialization, the compatibility-complete outer learning-context
  persistence adapter, portable skill-registry projection, governed run-bundle
  construction and YAML loading/rendering, and the concrete workstation
  `SkillExchangeProvider` composed at the CLI entrypoint. It translates
  representations but does not decide admission,
  current use, authority, semantic commitment, request-to-ability selection,
  host realization, or execution. `side.py`, `side_runtime_dependencies.py`,
  `skill_schema_io.py`, `skill_export_projection.py`,
  `skill_compatibility_import.py`, `skill_compatibility_export.py`,
  `skill_registry.py`, and `run_bundle_io.py` are exact module-identity
  compatibility aliases.
- `core_app/`: Independently buildable `realized-core` UV project. Its wheel
  contains the narrow CLI/composition surface and compatibility imports; it
  owns no engine, conversational application, or provider implementation.
- `core_conversation/`: Independently buildable `realized-core-conversation`
  UV project. It owns the transport-neutral governed-conversation application
  service, typed turn plans, exact selector materialization, and translation
  between advisory model values and the engine ABI. It contains no terminal,
  Flutter, Textual, trial, or provider implementation.
- `core_llm/`: Independently buildable `realized-core-llm` UV project. It owns
  provider-neutral planning and rendering contracts, schemas, model-side
  operation vocabulary, typed OpenAI-compatible response values, stateless
  provider transport, and provider-client construction. Callers declare their
  own retry, compatibility, and multipart-content policies. It does not retain
  conversation, reduction, resumption, or cached answer state; import the
  engine; or decide causal identity, selector resolution, admission, authority,
  realizer dispatch, host effects, or semantic commitment.
- `core_engine/`: Independently buildable `realized-core-engine` UV project. Its
  package source tree owns the canonical governed engine closure, state model,
  host mediation, and plain SQLite persistence path without any CLI,
  workstation, UI, gRPC, or publication code. Wheel and source distributions
  are built directly from that package tree; no root-module manifest or copy
  step participates in packaging. Its typed
  `realized_core_engine` package is the public `run` / `resume` / `inspect` ABI;
  the separately packaged CLI no longer imports canonical implementation
  modules directly. `EngineConfiguration.supported_executors` permits packaged
  executor frameworks; it does not install an ability, admit it, bind it to a
  subject, or provide a new executor implementation. It also owns
  constitutional state, composition-chain, decision-flow, transcript, and
  replay-comparison projection over its concrete controller state, plus the
  deterministic encounter-to-artifact semantics used by external Markdown
  ingestion.
- `core_runtime/`: Independently buildable `realized-core-runtime` package. It owns
  only the dependency-inverted run/resume lifecycle and stable protocols for
  state, domain reduction, closure, finalization, and persistence adapters; it
  imports no application, workstation, model-provider, or storage implementation.
- `validation/`: Independently buildable, dependency-free
  `realized-validation` development-tooling project. It owns reusable layered
  validation orchestration, structured validation reports, disposable or
  RAM-backed SQLite allocation, and durable SQLite report archival. It does
  not own domain trial semantics, curricula, corpora, or production runtime
  behavior. `validation_ladder.py` and `validation_sqlite.py` are exact
  module-identity compatibility aliases.
- `host_interaction/`: Independently buildable `realized-host-interaction` UV
  project. It owns the backend-neutral attachment models, bounded resolution
  and actions, delegated-rights narrowing, receipt shaping, and immutable
  executor/broker provider contracts shared by the controller and workstation.
  It has no third-party or workstation dependency and does not select or admit
  abilities, grant authority, or supply concrete host realizers. Concrete
  providers are attached at application/session composition boundaries; there
  is no mutable global provider registry. The historical root
  `host_interaction_*.py` paths are explicit compatibility facades over this
  package.
- `applied_theory_primitives.py`: Applied-theory enums, pure-theory aliases,
  derived value sets, and compatibility re-exports of the canonical timestamp
  and JSON projection helpers in `realized_core_semantics.values`.
- `artifact_contracts.py`: Compatibility facade for the canonical read-only
  artifact protocols in `realized_core_semantics.artifacts`.
- `applied_theory_types.py`: Applied dataclasses and compatibility re-exports
  for the canonical proposal vocabulary, plus root-owned artifacts, abilities,
  controller payloads, and the historical `json_safe` import path.
- `approval_governance.py`: Compatibility facade for approval rules owned by
  `realized_core_governance.approval`.
- `args.py`: Historical aggregate entry parser. It composes canonical
  workstation command registration with core/exchange/validation syntax while
  reusing engine-owned runtime-configuration adapters; it is not an engine
  compatibility alias.
- `artifact_answer_resolution.py`: Artifact answer extraction and direct formula/explanation resolution helpers.
- `artifact.py`: Artifact serialization and YAML-facing helper utilities.
- `blend_context.py`: Compatibility surface for canonical
  `realized_blend.context` values and the historical workstation projection
  entrypoint, which delegates to the runtime adapter.
- `blend_operator.py`: Exact module-identity compatibility alias for canonical
  `realized_blend.operators` values and pure interpretation rules.
- `blend_operator_store.py`: Identity-preserving compatibility alias for
  operator projection adapters owned by `realized_blend_application.operators`.
- `blend_session.py`: Compatibility surface for the canonical Blend session
  value and the historical workstation projection entrypoint, which delegates
  to the runtime adapter.
- `blend_world.py`: Identity-preserving compatibility alias for world
  materialization owned by `realized_blend_application.worlds`.
- `blend_world_models.py`: Exact module-identity compatibility alias for
  canonical `realized_blend.worlds` values.
- `blend_world_store.py`: Identity-preserving compatibility alias for the JSON
  world repository adapter owned by `realized_blend_application.world_store`.
- `blend_workflow.py`: Identity-preserving compatibility alias for workflow
  translation owned by `realized_blend_application.workflows`.
- `blend_workflow_models.py`: Exact module-identity compatibility alias for
  canonical `realized_blend.workflows` values.
- `blend_workflow_execution.py`: Identity-preserving compatibility alias for
  execution adapters owned by `realized_blend_application.execution`.
- `blend_workflow_store.py`: Identity-preserving compatibility alias for the
  JSON workflow repository owned by
  `realized_blend_application.workflow_store`.
- `boundary.py`: Boundary-shape typing and boundary reasoning helpers.
- `capability_runtime.py`: Runtime capability-grant issuance and
  capability-to-broker/executor mapping. Governance evaluates a supplied
  required authority against supplied grants; runtime still maps concrete
  effects, creates invocation grants, and binds realizers.
- `constitutional_trace.py`: Exact module-identity compatibility alias for
  engine-owned constitutional state snapshots, composition/decision/transcript
  signatures, and replay comparison. The canonical engine implementation
  preserves exact aliases for the dependency-light effect-answer and
  effect-signature requirements owned by `realized_core_governance.trace`.
- `controller_entrypoint_binding.py`: Dependency-light registration seam between the historical executable facade and outer CLI composition.
- `controller_entrypoints.py`: Historical aggregate command adapter. It
  preserves the root command surface while delegating package-native
  workstation parsing, composition, and dispatch to `workstation.app.cli`.
- `controller_governance_bridge.py`: Controller-facing governance bridge methods rebound onto `BSSCController`.
- `controller_runtime.py`: Canonical `BSSCController` implementation and historical public runtime surface.
- `controller_runtime_binding.py`: Dependency-inversion seam used by nested host brokers to construct the application-registered controller without importing its implementation.
- `data_governance.py`: Compatibility facade for data-class and access rules
  owned by `realized_core_governance.data`.
- `decision_review_models.py`: Module-identity compatibility alias for
  dependency-light decision-frame and review-item semantics owned by
  `realized_core_semantics.decision_review`.
- `decision_review.py`: Module-identity compatibility alias for decision-review
  persistence and review-item mapping owned by
  `workstation.subject.core.decision_review`; shared decision values remain in
  `realized_core_semantics.decision_review`.
- `decision_review_constructs.py`: Module-identity compatibility alias for
  transformation-construct corpus paths and JSON persistence owned by
  `workstation.subject.core.decision_review_constructs`. Candidate values and
  deterministic item projection remain in
  `realized_core_semantics.transformation_constructs`.
- `review_composition.py`: Module-identity compatibility alias for canonical
  subject review-composition values, deterministic item/tree transformations,
  transform receipts, and corpus persistence owned by
  `workstation.subject.core.review_composition`.
- `direct_knowledge_reuse.py`: Direct knowledge reuse matching and lookup helpers.
- `example.py`: Small Wasmtime/example surface used as a runtime proof-of-life.
- `execution_framework_primitives.py`: Host-advertised supported-framework environment/default normalization plus exact compatibility aliases for portable descriptors now owned by `realized_skill_semantics.execution`.
- `execution_frameworks.py`: Python, Bash, Ansible, and Wasm learning and
  execution surfaces plus exact compatibility re-exports for portable executor
  descriptors and host-support normalization. Execution accepts an injected
  exact-identity host-realizer provider; imported Python abilities receive
  deterministic literal broker-declaration enrichment only when explicit
  broker metadata is absent.
- `external_markdown_learning_pipeline.py`: Exact module-identity compatibility
  alias for the external Markdown ingestion adapter owned by
  `realized_exchange.markdown_learning_pipeline`.
- `fallback_not_generation.py`: Canonical fallback non-achievedness elaboration generation.
- `fallback_not_semantics.py`: Compatibility facade retaining historical fallback generation and ranking identities.
- `fence_extraction_strategy.py`: Fenced-code extraction and executor-aware fence learning helpers.
- `governance_inventory.py`: Controller inventory-cache adapter plus the
  historical exact alias to package-owned read-only inventory loading and
  classification in `realized_core_governance.inventory`.
- `governed_closure_and_commitment.py`: Closure, pause, incompletion, and commitment logic.
- `governed_prior_learning_reuse.py`: Governed prior-learning reuse and candidate recovery.
- `governed_semantic_reduction_runtime.py`: Compatibility adapter from `BSSCController` into `realized-core-runtime`, plus the existing domain-specific recursive `reduce_not` semantics.
- `governed_skill_access.py`: Current-use governed access checks for skills and artifacts.
- `governed_skill_installation.py`: Deliberate historical command adapter for
  governed `import-skill` installation. It coordinates canonical exchange,
  governance, persistence, and normalization APIs at the entry boundary.
- `host_mediation.py`: Runtime effect requests and trace records, effect-to-
  authority mapping, executor/realizer compatibility checks, and dispatch. It
  delegates only supplied admission-and-grant coverage to
  `realized_core_governance.authority` and per-effect evidence receipt meaning
  to `realized_core_governance.trace`, both through the runtime governance
  adapter.
- `host_interaction_*.py`: Historical compatibility facades preserving the
  pre-package host-interaction import paths and object identities. New code
  imports `realized_host_interaction`.
- `host_abi.py`: Stable host ABI, broker stability rules, and Wasm ABI definitions.
- `host_brokers.py`: Concrete host adapters for fs, store, net, tool, and nested
  skill invocation. Its historical broker table is immutable; application
  composition projects those adapters into an injected exact-identity provider.
- `host_realizers.py`: Application composition adapter that advertises concrete
  executor and broker bindings, inspects runtime prerequisites, and builds one
  immutable provider per composition request.
- `core_semantics/src/realized_core_semantics/identifiers.py`: Canonical dependency-free slug and identifier construction helpers for semantic and runtime values.
- `id_generation.py`: Module-identity compatibility alias for canonical semantic identifier helpers.
- `learn.py`: Learning-token, discriminator, and selection-signal helpers.
- `workstation/subject/core/learning_context.py`: Canonical LearningContext
  aggregate for learning units, deltas and operations, sources, subject
  imports, reasoning scope, deterministic delta application, and authoritative
  `corpus/<subject-id>/...` JSON/index persistence. It does not import document
  projection, skill projection, skill compilation, or export implementations.
- `workstation/subject/core/learning_context_projection.py`: Canonical
  deterministic projection of a `LearningContext` into `subject.typ` and
  compatibility `subject.md` scaffolds.
- `workstation/subject/core/learning_context_markdown.py`: Canonical
  subject-owned Markdown rendering and parsing helpers for learning-context
  documents. It performs no external ingestion or artifact admission.
- `workstation/subject/service/learning_context_persistence.py`: Application
  coordinator that validates required outer materialization, persists
  authoritative state, reloads its normalized form, and regenerates document
  projections before invoking an optional entry-composed skill materializer.
- `workstation/subject/service/learning_context_skills.py`: Pure construction of
  portable derived-skill documents from admitted learning units. It performs no
  YAML serialization, compilation, or file I/O.
- `realized_exchange.learning_context_skills`: Compiles and materializes those
  documents as canonical portable-skill YAML under `derived/skills/`.
- `learning_context.py`: Exact module-identity compatibility alias for
  `realized_exchange.learning_context`, whose outer adapter preserves the
  historical one-call persist-and-project operation while re-exporting the
  package-owned subject values with canonical identities.
- `workstation/subject/core/learning_context_paths.py`: Canonical
  dependency-light corpus, decision-review, source-bundle, and derived-resource
  path construction shared by subject persistence and projection adapters. It
  re-exports the canonical subject identifier from
  `realized_core_semantics.identifiers`.
- `learning_context_paths.py`: Exact module-identity compatibility alias for
  the package-owned subject path vocabulary.
- `workstation/subject/core/gather_sources.py`: Canonical Gather source, revision, collection, path, and JSON persistence model for the subject lifecycle.
- `gather_sources.py`: Module-identity compatibility alias for canonical subject-core Gather source persistence.
- `itemize_models.py`: Module-identity compatibility alias for dependency-light
  itemization values and normalization owned by
  `realized_core_semantics.itemization`.
- `workstation/subject/core/itemization.py`: Canonical deterministic
  itemization extraction, continuity-aware refresh, proposal-result
  interpretation, and corpus persistence. Optional direct decomposition is an
  injected outbound effect; the module imports no controller implementation.
- `itemize.py`: Historical itemization compatibility adapter. It re-exports the
  canonical subject implementation and retains only the former implicit
  controller bootstrap for direct root callers.
- `workstation/subject/core/itemize_validation.py`: Canonical itemization-session validation invariants consumed by the subject workflow.
- `itemize_validation.py`: Identity-preserving compatibility facade for the canonical subject-core itemization validation surface.
- `learning_context_projection.py`: Exact module-identity compatibility alias for the subject-core document renderer.
- `learning_context_skill_projection.py`: Exact module-identity compatibility alias for exchange-owned learning-context skill compilation and YAML materialization. Projection establishes subject scope and provenance; it does not perform governed skill installation or admission.
- `workstation/subject/service/learning_capture.py`: Prompt-scoped subject application service that turns successful workstation chat “save learnings” markdown writes into chat `LearningSource`, `LearningDelta`, and merged `LearningContext` records without making raw markdown tools semantic by default.
- `workstation/foundation/host/learning_capture.py`: Compatibility alias for the canonical subject-service learning-capture module.
- `macos_host_brokers.py`: macOS-specific broker implementations for device actions.
- `main.py`: Historical executable/import facade that preserves `import main` module identity while delegating to `controller_runtime.py` and lazily registering `controller_entrypoints.py`.
- `markdown_ir.py`: Module-identity compatibility alias for dependency-free
  Markdown IR values, parsing, bounded semantic views, symbolic mappings, and
  normalization owned by `realized_core_semantics.markdown`.
- `markdown_learning_artifact_semantics.py`: Exact module-identity compatibility
  alias for deterministic Markdown encounter-to-artifact shaping owned by
  `realized_core_engine.markdown_learning_artifact_semantics`.
- `non_achievedness_normalization.py`: Structured non-achievedness normalization orchestration over explicit runtime dependencies.
- `normalization_primitives.py`: Canonical dependency-light normalization helpers for schema, representations, boundary values, and runtime enums.
- `normalization_runtime_dependencies.py`: Explicit dependency surface used by structured non-achievedness normalization.
- `normalize.py`: Compatibility facade preserving historical normalization imports and object identities.
- `not_elaboration_ranking.py`: Canonical non-achievedness elaboration ranking.
- `prolog.py`: Prolog/title representation helpers and query support.
- `prompt_directives.py`: Prompt directive classification and intent-shaping helpers.
- `workstation/subject/core/publication.py`: Canonical publication substrate for claim-centered governed report publication, including typed publication/section/claim/source/build/render-artifact records, deterministic snapshot hashing, and explicit on-disk publication persistence under the subject corpus home.
- `publication.py`: Module-identity compatibility alias for the canonical subject-core publication substrate.
- `workstation/subject/core/publication_projection.py`: Canonical deterministic `LearningContext`-to-`Publication` report projection, including admitted-unit claim extraction, section assignment, source loading, validation/build/render orchestration, and separate publication-tree materialization.
- `publication_projection.py`: Module-identity compatibility alias for canonical subject-core publication projection.
- `workstation/subject/core/publication_render.py`: Canonical deterministic Typst and markdown renderers plus reproducible publication build and render-artifact projection.
- `publication_render.py`: Module-identity compatibility alias for canonical subject-core publication rendering.
- `workstation/subject/core/publication_validation.py`: Canonical publication validation rules over unique section ids, claim/source references, and source-backed descriptive claims.
- `publication_validation.py`: Module-identity compatibility alias for canonical subject-core publication validation.
- `pure_theory_types.py`: Compatibility facade for the canonical formal theory
  terms in `realized_core_semantics.theory`.
- `python_skill_brokerization.py`: Python skill inspection and brokerization
  heuristics, including conservative source-ordered extraction of literal
  `broker_request(...)` identities. It never guesses dynamic broker names.
- `python_skill_host.py`: Child Python runtime host API for governed broker
  calls. Under injected execution it uses the invocation-scoped parent bridge;
  its static dispatch path remains a compatibility fallback only.
- `python_skill_host_transport.py`: Authenticated invocation-scoped loopback
  bridge that carries child Python broker requests to the parent-injected
  provider while rechecking the authoritative declaration, admission, ABI, and
  grants before dispatch.
- `replay_verifier.py`: Deliberate historical replay command adapter. It
  coordinates package-owned run-bundle exchange, replay execution, and
  governance receipt verification without becoming their implementation owner.
- `retrieval_ranking.py`: Retrieval scoring and ranking for artifact reuse and prompt matching.
- `run_bundle_io.py`: Exact module-identity compatibility alias for governed
  run-bundle construction, YAML loading/rendering, and governance snapshot
  packaging owned by `realized_exchange.run_bundle`.
- `run_outcome_harvest_and_reporting.py`: Run finalization, discovery harvest, and report emission.
- `runtime_controller_api.py`: Exact module-identity compatibility alias for
  `workstation.app.cli.runtime_controller`.
- `runtime_governance_context.py`: Runtime-facing governance resolution facade.
- `semantic_prompt_posture.py`: Prompt-posture classification and direct-answer preference helpers.
- `SEMANTIC_RELATION_VALIDATION.py`: Standalone semantic relation validation script.
- `semantic_text.py`: Semantic text normalization, literal decoding, and title/text helpers.
- `side.py`: Exact module-identity compatibility alias for artifact-bundle YAML exchange owned by `realized_exchange.artifact_yaml`.
- `side_runtime_dependencies.py`: Exact module-identity compatibility alias for artifact-exchange dependencies owned by `realized_exchange.dependencies`.
- `skill_export_projection.py`: Exact module-identity compatibility alias for canonical portable-skill bundle export owned by `realized_exchange.skill_export`.
- `skill_compiler.py`: Exact module-identity compatibility alias for the portable-skill compiler owned by `realized_exchange.compiler`.
- `skill_compatibility_export.py`: Exact module-identity compatibility alias for foreign-format export adapters owned by `realized_exchange.compatibility_export`.
- `skill_compatibility_import.py`: Exact module-identity compatibility alias for foreign-format import adapters owned by `realized_exchange.compatibility_import`.
- `skill_boundary_normalization.py`: Identity-preserving compatibility alias for artifact-to-skill normalization owned by `realized_skill_application.normalization`.
- `skill_composition.py`: Identity-preserving compatibility alias for composition analysis and execution owned by `realized_skill_application.composition`.
- `skill_governance.py`: Historical governed-skill adapter and admission
  orchestrator. It retains declaration synthesis, host-broker and Python-source
  preflight, current-use state assembly, and compatibility entry points;
  delegates policy-and-approval evaluation to
  `realized_core_governance.admission` and final eligibility to
  `realized_core_governance.current_use`; and
  preserves exact aliases for package-owned portable declaration schema and
  composition-right semantics.
- `skill_governance_primitives.py`: Compatibility facade for package-owned
  governed-skill vocabulary and normalization.
- `skill_ir.py`: Identity-preserving compatibility alias for artifact-centered canonical IR projection owned by `realized_skill_application.ir`.
- `skill_invocation_contract.py`: Compatibility facade preserving historical aliases to package-owned invocation values and normalization while re-exporting the workstation artifact-projection adapter.
- `skill_leaf_types.py`: Compatibility facade for canonical portable skill leaf values in `realized_skill_semantics.leaves`.
- `skill_lifecycle.py`: Compatibility facade for package-owned lifecycle
  normalization, projection, and lifecycle-only invocation-state rules.
- `skill_path_notation.py`: Compatibility facade for canonical portable skill paths in `realized_skill_semantics.paths`.
- `skill_registry.py`: Exact module-identity compatibility alias for portable
  skill-registry projection and `export-skill-registry` support owned by
  `realized_exchange.registry`.
- `skill_safety_governance.py`: Compatibility facade for revocation and
  incident rules owned by `realized_core_governance.safety`.
- `skill_schema_io.py`: Exact module-identity compatibility alias for portable-skill schema hydration and import-file resolution owned by `realized_exchange.skill_schema`.
- `store.py`: SQLite artifact store, indexing, persistence, and batch import support.
- `structured_learning_yaml.py`: Structured-learning YAML rendering helpers.
- `supplement.py`: Controller-owned LLM supplement adapter, proposal-type
  labeling, prompt policy, JSON repair, and supplement receipts. Provider SDK
  construction, request fallback mechanics, retries, and typed response
  parsing are delegated through the public `realized-core-llm` ABI.
- `system_state.py`: System state model, persistence, effect traces, and capability grant storage.
- `tablet_safety_validation.py`: Standalone tablet-safety validation script.
- `title_depth_learning_validation.py`: Standalone title-depth learning validation script.
- `title_semantics.py`: Title semantics, title-depth, and Prolog-title helpers.
- `TRIAL_DOMAIN_VALIDATION.py`: Multi-domain trial runner for fresh-db curriculum validation.
- `validation_ladder.py`: Compatibility alias for
  `realized_validation.ladder`, the package-owned layered acceptance runner.
- `validation_sqlite.py`: Compatibility alias for
  `realized_validation.sqlite_runtime`, the package-owned validation SQLite
  allocation and archival support.
- `virtual_mounts.py`: Virtual mount definitions, safe path resolution, and mount policies.
- `wasm_skill_runtime.py`: Embedded Wasmtime runtime for governed Wasm skill execution.
- `workstation/__init__.py`: Inert namespace initializer for independently packaged workstation components.
- `workstation/builtin_skills.py`: Builtin workstation worker-skill catalog, including repo-search and Wasm demo workers.
- `workstation/capabilities.py`: Workstation capability schemas plus attachment-scoped capability execution, installed-skill invocation, workstation-backed shared Blend operator provider assembly for dynamic skill/capability operators, shared Blend operator/workflow store and execution adapters for `ws.skill.compose`, `ws.workflow.*`, and `ws.operator.*`, workstation publication of Blend workflow/step lifecycle events, and workstation-to-skill delegation shaping.
- `workstation/chat_commands.py`: Direct workstation chat slash-command handlers for skill lifecycle and skill-inspection operations without an LLM round-trip.
- `workstation/chat_ui.py`: Enhanced interactive workstation chat frontend with a Textual-first shell host, prompt-toolkit fallback, context suggestions, command history, and approval prompting over the same workstation session surface.
- `workstation/app_cli/src/workstation/app/cli/arguments.py`: Canonical parser
  registration for the installable workstation command and the historical
  aggregate entry surface.
- `workstation/app_cli/src/workstation/app/cli/cli.py`: Installable workstation
  command dispatcher plus existing handlers for launch, prompt, chat, gRPC,
  skill lifecycle, and trial validation.
- `workstation/app_cli/src/workstation/app/cli/composition.py`: Executable
  workstation composition root that binds concrete controller,
  artifact-repository, subject-workflow, skill-exchange, and host-realizer
  providers without placing their policy in the entry layer.
- `workstation/app_cli/src/workstation/app/cli/runtime_controller.py`:
  Subject-aware state seeding and controller construction retained at the
  workstation application boundary.
- `workstation/delegation.py`: Thin workstation adapter over shared host-interaction delegation helpers.
- `workstation/direct_composition.py`: Prompt-local skill shortlisting and direct worker-composition helpers for workstation turns, including plain-path payload derivation for imported trial skills and action-aware routing across adjacent worker families like remove vs copy.
- `workstation/event_bus.py`: Optional workstation-local event-bus wrapper with typed event envelopes, Blinker-backed publication when available, fallback in-process subscription when not, and receipt-to-host-event derivation helpers.
- `workstation/ui_flutter/`: Flutter Material 3 workstation client over the canonical gRPC shell and subject-workflow services.
- `workstation/governance.py`: Workstation-specific governance helpers, including the skill-home default policy and transient bundle-policy filtering.
- `workstation/foundation_host/src/workstation/foundation/host/host_interaction.py`: Workstation-backed adapter for the shared host-interaction contract.
- `workstation/layout.py`: Renderer-neutral workstation tab/pane layout metadata shared across shell projections, including the explicit subject-workflow phase tabs and coarse pane sizing hints.
- `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py`: Host-owned OpenAI-compatible workstation tool-loop driver, including workflow-run preference and workflow-query guidance when first-class workflow capabilities are available.
- `workstation/runtime_core/src/workstation/runtime/core/blend_adapters.py`: Explicit workstation-to-Blend adapter boundary for session/context projection, concrete skill-composition invocation, JSON repository selection, clocks, identifiers, and canonical workflow execution; canonical Blend remains independent of workstation and root compatibility APIs.
- `workstation/foundation_models/src/workstation/foundation/models/models.py`: Workstation attachment, session, and task-contract dataclasses.
- `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py`: Neutral workstation projection contracts for permissions, activity events/feeds, skill descriptors/forms/catalogs, operator summaries/details, workflow summaries/graphs/timelines, action results, and form grouping metadata, plus additive builders/renderers so shell and future UI surfaces can consume the same view objects.
- `workstation/foundation_projections/src/workstation/foundation/projections/activity_receipts.py`: Receipt-to-activity projection and rendering shared by runtime and UI consumers without a UI-to-runtime dependency.
- `workstation/colors.py`: Shared workstation palette primitives for converged shell rendering.
- `workstation/runtime_core/src/workstation/runtime/core/session.py`: Workstation session materialization, prompt handling, bytes-safe receipt/response persistence, additive Blend context/session/world discovery-file projection, workflow-store initialization, prompt-local preference for `ws.workflow.run`, and final capability receipts after approved escalation retries.
- `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py`: Workstation-local subscriber/controller seam over the event bus for live Blend workflow activity projection and shell context invalidation without coupling UI surfaces to execution code.
- `workstation/subject_workflow_api.py`: Structured subject-workflow application service that projects scenario/phase views and applies subject actions without depending on Textual or Flutter mechanics.
- `workstation/subject_workflow_client.py`: Client protocol plus in-process and gRPC-backed subject-workflow clients for listing subjects, querying snapshots/control bundles/pane bundles, applying actions, and consuming workflow watch streams.
- `workstation/subject_workflow_grpc.py`: Thin gRPC adapter over the subject-workflow application service for in-process or external API transport.
- `workstation/subject_workflow_repository.py`: First persistence seam for subject-workflow state, including subject-progress loading/persisting and shared progress-map/import-staging helpers below the service layer.
- `workstation/subject/core/host_actions.py`: Segregated outbound subject-workflow ports for runtime policy, source ingress, and explicitly confirmed assistant capture, plus the fail-closed uncomposed implementation.
- `workstation/runtime/core/subject_host_actions.py`: Stateless controller-layer adapter that realizes subject-workflow outbound ports through existing workstation session, source-action, and learning-capture implementations.
- `workstation/subject_workflow_textual_backend.py`: Textual-facing projection backend that keeps the UI on a client/service seam while allowing fast in-process progress overrides during local subject-workflow refresh.
- `workstation/theme.py`: Shared workstation semantic theme mapping layered over the palette for converged shell rendering.
- `workstation/workstation_shell_backend.py`: In-process projection backend for non-subject shell surfaces such as activity, permissions, and skills so the UI stays on a backend seam there too.
- `workstation/workstation_core.py`: Additive workstation service boundary for permission panels, activity-feed queries, persisted workflow list/query/timeline/history views, operator summary/detail views, session-capability mutation, skill descriptor/input-form/catalog projections, and narrow action helpers for skill invocation and workflow rerun above the shared Blend/workflow substrate.
- `workstation/protos/subject_workflow.proto`: Protobuf contract for the extracted subject-workflow API boundary.
- `workstation/protos/subject_workflow_pb2.py`: Generated protobuf messages for the subject-workflow API boundary.
- `workstation/protos/subject_workflow_pb2_grpc.py`: Generated gRPC stubs and servicer helpers for the subject-workflow API boundary.
- `workstation/skill_composition_planning.py`: Bounded automatic compose-plan synthesis for obvious multi-step prompts, including conditional, branching, and iterative plans, before the workstation falls back to the generic LLM/tool loop.
- `workstation/skill_home.py`: Persistent workstation skill-home resolution and metadata helpers.
- `workstation/skill_management.py`: Workstation skill catalog, import, export, and `SKILLS.json` refresh helpers.
- `workstation/skill_invocation.py`: Workstation skill discovery, resolution,
  prompt-local invocation shaping, top-level input compatibility, and bounded
  nested-worker answer/receipt projection. Terminal error and approval status
  follow only the bounded nested `result` envelope, not unrelated metadata.
- `workstation/skills/core/invocation_contract.py`: Canonical invocation request/result records and deterministic artifact/result projections used by workstation skill invocation.
- `workstation/task_contract.py`: Boundary-complete workstation task normalization from natural-language prompts.
- `scripts/generate_workstation_protos.py`: Regenerates the committed workstation protobuf/gRPC Python stubs from the checked-in `.proto` contracts.
- `scripts/verify_core_distribution.py`: Inspects the six built standalone
  core wheels, including `realized-host-interaction`, verifies their distinct
  file ownership, rejects outer-application files, then runs the separately
  extracted wheel contents against plain SQLite outside the repository import
  path.
- `scripts/check_compatibility_facades.py`: Measures every retained root
  compatibility facade and its static consumers, rejects canonical-package or
  public example consumers, and verifies the checked-in retirement ledger.
- `scripts/verify_workspace_distributions.py`: Builds every registered UV
  project as a wheel and source distribution, rejects root-facade imports from
  built Python, assembles all wheels outside the repository, and imports every
  declared public module from that isolated installation.

## Tests
- `core_app/tests/test_distribution.py`: Verifies that the application declares
  only its composition dependencies, owns only CLI composition, and performs
  deterministic plain-SQLite run/resume/inspect operations with durable state.
- `core_engine/tests/test_distribution.py`: Recomputes the explicit engine wheel
  module closure and verifies dependency allowlists, outer-surface exclusions,
  engine metadata, workspace registration, and Cloud Build qualification.
- `core_engine/tests/test_api.py`: Exercises the typed engine ABI against plain
  SQLite, evidence intake, runtime options, durable resume, and inspection.
- `core_runtime/tests/test_reduction.py`: Dependency-free contract tests for immediate closure, bounded frontier execution, terminal/pause exits, and resume preparation in the extracted realization lifecycle.
- `tests/test_core_app_cli_equivalence.py`: Integration test comparing stable
  fresh-SQLite run projections from the existing application CLI and the
  packaged core CLI while allowing generated identifiers to remain run-local.
- `tests/test_core_runtime_package_adapter.py`: Compatibility tests proving the historical governed runtime entry points delegate to the extracted core package without changing their ABI.
- `tests/test_compatibility_facade_inventory.py`: Verifies that the generated
  compatibility ledger is current, complete, and free of canonical-package or
  public documentation/example consumers.
- `tests/__init__.py`: Test package marker.
- `tests/test_artifact_answer_selection.py`: Tests for answer selection, prompt posture, and retrieval ranking behavior.
- `tests/test_artifact_boundary_shape.py`: Tests for artifact boundary-shape behavior.
- `tests/test_artifact_bundle_io.py`: Tests for legacy artifact bundle import/export behavior.
- `tests/test_artifact_search_hybrid.py`: Tests for hybrid artifact search behavior.
- `tests/test_boundary_shape_typing.py`: Tests for boundary typing and shape compatibility.
- `tests/test_controller_feature_toggles.py`: Tests for CLI/controller feature toggles and related command surfaces.
- `tests/test_controller_layer_hygiene.py`: Hygiene tests for controller-layer imports and boundaries.
- `workstation/tests/test_six_layer_workstation_boundary_hygiene.py`: Hygiene tests for workstation, shared-substrate, and runtime/backend six-layer boundaries.
- `tests/test_decomposition_prompt_context.py`: Tests for decomposition prompt-context construction.
- `tests/test_exchange_layer_hygiene.py`: Hygiene tests for exchange-layer import and export boundaries.
- `tests/test_executor_framework_learning.py`: Tests for executor-aware learning from fenced or scripted artifacts.
- `tests/test_fence_extraction_strategy.py`: Tests for fenced code extraction and executor matching.
- `tests/test_function_boundary.py`: Cross-boundary runtime tests for executable abilities and governed invocation.
- `tests/test_governance_layer_hygiene.py`: Import-hygiene tests ensuring consumers use the canonical governance package for package-owned values and retain the mixed root facade only for root-owned adapters.
- `tests/test_governance_selection_precedence.py`: Contract tests proving governance eligibility precedes direct-answer promotion even for exact semantic matches.
- `tests/test_host_mediation.py`: Tests for host mediation, brokers, grants, and nested effect traces.
- `tests/test_host_interaction_context.py`: Tests for the shared host-interaction contract and workstation-backed adapter.
- `tests/test_host_interaction_delegation.py`: Tests for the shared delegated-rights and ephemeral-mount substrate helpers.
- `tests/test_host_interaction_receipts.py`: Tests for the shared host-interaction receipt builders and canonical JSONL receipt log appends.
- `tests/test_host_interaction_actions.py`: Tests for the shared attachment-scoped host action helpers below workstation.
- `tests/test_host_interaction_action_dispatch.py`: Tests for the shared non-skill host-action dispatcher and its read-resolution injection seam.
- `tests/test_llm_layer_hygiene.py`: Hygiene tests ensuring LLM/prompt modules do not import runtime/governance layers directly.
- `tests/test_learning_context.py`: Tests for LearningContext phase-1 records, corpus-home persistence, listing, and deterministic delta application.
- `tests/test_learning_delta_operations.py`: Focused seam-level tests for explicit LearningDelta operator semantics including initiate, append, replace, remove, improve, link, split, merge, reject, and restore.
- `tests/learning_xref_test_support.py`: Fast fixture builders for large-markdown learning, deterministic section handles, and explicit xref-candidate preparation below full controller ingest.
- `tests/test_large_markdown_learning.py`: Large-volume markdown-learning regressions covering subject-context persistence, repeated subject re-entry across multiple markdown documents, and post-ingest delta lifecycle/structural operations against contexts learned from large markdown corpora.
- `tests/test_learning_xref_preparation.py`: Fast seam-level tests for deterministic explicit-xref preparation and fixture-based large-markdown learning record materialization without controller-runtime cost.
- `tests/test_learning_context_projection.py`: Seam-level tests for deterministic `LearningContext` subject document projection into `subject.typ` and `subject.md`.
- `tests/test_learning_context_skill_projection.py`: Seam-level tests for deterministic `LearningContext` corpus-admitted-unit skill projection through the canonical portable skill document path.
- `tests/test_publication.py`: Seam-level tests for first publication report projection, separate publication-tree persistence, and source-backed descriptive-claim validation.
- `workstation/tests/test_workstation_learning_capture.py`: Seam-level tests for prompt-scoped workstation chat-learning capture into `LearningContext`.
- `tests/test_markdown_artifact_generation.py`: Tests for markdown artifact generation and functionalization.
- `tests/test_markdown_ir.py`: Tests for markdown IR construction.
- `tests/test_markdown_learning.py`: Tests for markdown-learning behavior and artifact persistence.
- `tests/test_not_elaboration_schema.py`: Tests for non-achievedness elaboration schema behavior.
- `tests/test_prolog_title_representation.py`: Tests for Prolog and title representation behavior.
- `tests/test_run_bundle_io.py`: Tests for run-bundle export/import and replay behavior.
- `tests/test_runtime_layer_hygiene.py`: Hygiene tests for runtime-layer imports and governance facades.
- `tests/test_skill_io.py`: Tests for skill schema, export projection, installation, and governance behavior.
- `tests/test_skill_compiler.py`: Tests for the initial compiler seam and compiler summaries over canonical skill IR.
- `tests/test_skill_compatibility_export.py`: Tests for compatibility-tier export adapters into representative foreign tool and instruction-bundle surfaces.
- `tests/test_skill_compatibility_import.py`: Tests for compatibility-tier import adapters and declaration-only compatibility ability hydration.
- `tests/test_skill_composition.py`: Tests for canonical leaf binding analysis, mapper-backed composition execution, sequence-plan validation, and trial-backed composition readiness checks.
- `tests/test_skill_ir.py`: Tests for canonical skill IR projection, alias/family metadata, and export integration.
- `tests/test_skill_invocation_contract.py`: Tests for canonical invocation request/result records over bound payloads and workstation-style terminal results.
- `tests/test_blend_operator.py`: Direct tests for Blend operator applicability, target resolution, and invocation construction.
- `tests/test_blend_world.py`: Direct tests for shared Blend workstation-world materialization and reuse.
- `tests/test_blend_workflow.py`: Tests for additive Blend workflow plan/run projections over `ws.skill.compose` arguments and results.
- `tests/test_blend_workflow_execution.py`: Tests for the shared Blend workflow execution surface, including operator-context applicability, context-fed invocations below workstation, and real workflow/step lifecycle event publication.
- `blend/tests/test_execution.py`: Package-native tests for port-driven Blend
  execution, including branch/iteration/skip propagation, halt and fallback
  shaping, deterministic persistence, observation ordering, and proof that
  absent, duplicated, delayed, or rejecting observation consumers cannot alter
  authoritative stored runs.
- `tests/test_blend_workflow_store.py`: Tests for the shared Blend workflow store/query module below workstation.
- `tests/test_title_depth.py`: Tests for title-depth inference and title semantics.
- `tests/test_validation_ladder.py`: Tests for layered validation command ordering, nested-report capture, and CLI argument handling.
- `tests/test_validation_sqlite.py`: Tests for validation SQLite runtime-root selection and report archival.
- `tests/test_trial_domain_validation.py`: Tests for trial-domain validation budgeting and orchestration.
- `workstation/tests/test_workstation.py`: Workstation vertical-slice launch, prompt, and CLI regression tests.
- `workstation/tests/test_workstation_activity_view.py`: Tests for receipt-driven workstation activity rendering and tailing.
- `workstation/tests/test_workstation_chat_commands.py`: Tests for direct workstation chat slash commands covering import, export, describe, list, and permissions flows.
- `workstation/tests/test_workstation_chat_ui.py`: Tests for the enhanced workstation chat frontend context, suggestions, completion, and fallback detection.
- `workstation/tests/test_workstation_core.py`: Tests for the additive workstation_core service layer over permission mutation, skill descriptors/forms/constraints, workflow query/timeline/history projections, and narrow skill/workflow action helpers.
- `workstation/tests/test_workstation_blend_adapters.py`: Direct consumer-boundary proof that workstation executes canonical Blend plans through explicit ports without the historical orchestration facade, including invocation context, injected persistence, result, and lifecycle ordering.
- `workstation/tests/test_workstation_event_bus.py`: Tests for the workstation-local event bus over subscriber isolation, receipt-derived events, turn lifecycle publication, permission/skill catalog mutation events, and bridged Blend workflow/step lifecycle events.
- `workstation/ui_flutter/test/workstation_app_test.dart`: Flutter widget-level BDD coverage over bootstrap, chat, subject workflow tabs, and utility-tab layout behavior.
- `workstation/tests/test_workstation_projection_models.py`: Tests for neutral workstation permission-panel and workflow-graph projection contracts.
- `workstation/tests/test_workstation_subject_workflow_api.py`: Tests for the extracted subject-workflow application service and in-process gRPC adapter.
- `workstation/tests/test_workstation_subscriber_controllers.py`: Tests for workstation event-bus subscriber controllers over live Blend step activity projection and context/projection invalidation.

## Trial Validators
- `trials/BOUNDARY_SHAPE_VALIDATION.py`: Boundary-shape curriculum validator.
- `trials/LEARNED_FUNCTION_VALIDATION.py`: Learned-function validator for fresh-db function reuse.
- `trials/PROBABILITY_INFORMATION_RELATION_VALIDATION.py`: Probability/information relation curriculum validator.
