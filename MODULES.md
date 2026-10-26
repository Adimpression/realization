# MODULES

Terse repository map. Read this file before editing Python modules.

Top-line rule used in Python files:
- `# See MODULES.md for the repository module map before editing.`

## Workstation Distribution Boundaries

- `workstation/contracts_api/` publishes `workstation.contracts`, the stable,
  transport-neutral API/ABI surface for subject workflow, shell, and event types.
  It may contain dataclasses, runtime-checkable protocols, and deterministic
  routing helpers, but no runtime, UI, service, adapter, or provider imports.
- `workstation/runtime_core/` owns workstation runtime execution, the LLM/provider
  driver, and projection-event subscriber control.
- `workstation/subject_service/` owns the subject workflow application service,
  client-session registry, and subject in-process/gRPC client adapters.
- `workstation/shell_core/` owns shell application services, chat orchestration,
  and shell in-process/gRPC client adapters. Its additive governed-conversation
  mode composes the public `realized-core-conversation` application surface and
  `realized-core-llm` provider adapter directly; it does not depend on the
  `realized-core` CLI package or duplicate product planning behavior.
- `workstation/foundation_events/` owns event publication. Its historical
  `subscriber_controllers` module is a compatibility alias to `runtime_core`.
- `workstation/foundation_host/` owns the workstation-backed host adapter. Its historical
  `client_sessions` and `llm_driver` modules are compatibility aliases to
  `subject_service` and `runtime_core`, respectively. Its process-local
  controller and subject-client providers are composition seams: entry modules
  register concrete adapters, while runtime and UI consumers receive only the
  corresponding contracts.
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
- `core_semantics/`: Independently buildable `realized-core-semantics` UV
  project. It owns the Pydantic formal-theory value model and narrow read-only
  artifact protocols, plus dependency-light timestamp and JSON value
  projection helpers. It contains no governance decisions, persistence,
  controller orchestration, model calls, host execution, or workstation code.
  `pure_theory_types.py` and `artifact_contracts.py` are historical facades.
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
  supplied records and an injected clock, plus data-class normalization and
  supplied-context data-access rules. It depends only on
  `realized-core-semantics` and
  `realized-skill-semantics`; it does not parse YAML, synthesize declarations
  from artifacts or host code, inspect broker availability or executable
  source, complete current-use authorization, issue authority, persist records,
  manage inventory cache lifetime, open virtual mounts, connect to SQLite,
  execute queries, invoke host brokers, execute skills, invoke models, or own
  controller/workstation behavior. The root admission orchestrator retains host
  preflight and delegates only its policy-and-approval decision.
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
  `skill_leaf_types.py` and `skill_path_notation.py` are historical facades;
  `skill_boundary_normalization.py` retains compatibility aliases plus the
  artifact/governance adapter; `skill_ir.py` retains compatibility aliases plus
  artifact, governance, lifecycle, compatibility, and runtime projection;
  `skill_composition.py` retains exact value aliases plus artifact projection,
  plan analysis, mapper execution, iterative orchestration, runtime events, and
  invoker calls.
- `core_app/`: Independently buildable `realized-core` UV project. Its wheel
  contains the narrow CLI/composition surface and compatibility imports; it
  owns no engine, conversational application, or provider implementation.
- `core_conversation/`: Independently buildable `realized-core-conversation`
  UV project. It owns the transport-neutral governed-conversation application
  service, typed turn plans, exact selector materialization, and translation
  between advisory model values and the engine ABI. It contains no terminal,
  Flutter, Textual, trial, or provider implementation.
- `core_llm/`: Independently buildable `realized-core-llm` UV project. It owns
  provider-neutral planning and rendering contracts, schemas, and model-side
  operation vocabulary. It does not import the engine or decide causal
  identity, selector resolution, admission, or semantic commitment.
- `core_engine/`: Independently buildable, wheel-only `realized-core-engine` UV
  project. It assembles the canonical governed engine module closure, state
  model, host mediation, and plain SQLite persistence path without any CLI,
  workstation, UI, gRPC, or publication code. `module_manifest.txt` is a tested
  distribution manifest, not a second copy of the engine sources. Its typed
  `realized_core_engine` package is the public `run` / `resume` / `inspect` ABI;
  the separately packaged CLI no longer imports canonical implementation
  modules directly. `EngineConfiguration.supported_executors` permits packaged
  executor frameworks; it does not install an ability, admit it, bind it to a
  subject, or provide a new executor implementation.
- `core_runtime/`: Independently buildable `realized-core-runtime` package. It owns
  only the dependency-inverted run/resume lifecycle and stable protocols for
  state, domain reduction, closure, finalization, and persistence adapters; it
  imports no application, workstation, model-provider, or storage implementation.
- `host_interaction/`: Independently buildable `realized-host-interaction` UV
  project. It owns the backend-neutral attachment models, bounded resolution
  and actions, delegated-rights narrowing, and receipt shaping shared by the
  controller and workstation. It has no third-party or workstation dependency
  and does not select abilities, grant authority, or register concrete host
  realizers. The historical root `host_interaction_*.py` paths are explicit
  compatibility facades over this package.
- `applied_theory_primitives.py`: Applied-theory enums, pure-theory aliases,
  derived value sets, and compatibility re-exports of the canonical timestamp
  and JSON projection helpers in `realized_core_semantics.values`.
- `artifact_contracts.py`: Compatibility facade for the canonical read-only
  artifact protocols in `realized_core_semantics.artifacts`.
- `applied_theory_types.py`: Applied dataclasses and compatibility re-exports for artifacts, proposals, abilities, controller payloads, and the historical `json_safe` import path.
- `approval_governance.py`: Compatibility facade for approval rules owned by
  `realized_core_governance.approval`.
- `args.py`: CLI argument parsing, feature toggles, and SQLite override handling.
- `artifact_answer_resolution.py`: Artifact answer extraction and direct formula/explanation resolution helpers.
- `artifact.py`: Artifact serialization and YAML-facing helper utilities.
- `blend_context.py`: Additive Blend context models plus projection from workstation session attachments, granted capabilities, and shared-world identity/mount continuity.
- `blend_operator.py`: Additive Blend operator and operator-invocation models plus context-applicability and target-resolution helpers for context-applied verbs.
- `blend_operator_store.py`: Shared root-level Blend operator catalog/query surface for dynamically discovered operator providers, provider factories for dynamic skill/capability projection, summary listing, and workflow-step-aware operator resolution.
- `blend_session.py`: Additive Blend session model plus workstation-to-Blend session projection helpers.
- `blend_world.py`: Additive Blend shared-world model for explicit mutable mount continuity across multiple workstation sessions.
- `blend_world_models.py`: Dependency-light Blend shared-world value models used by both the compatibility facade and persistence adapter.
- `blend_world_store.py`: Shared root-level Blend world store/query helpers for persisted world loading, mount lookup, summaries, and workstation-world materialization.
- `blend_workflow.py`: Additive Blend workflow plan/run dataclasses plus projection helpers between raw composition payloads and first-class Blend workflow objects.
- `blend_workflow_models.py`: Dependency-light Blend workflow value models shared by projection and persistence surfaces while preserving the legacy `blend_workflow` exports.
- `blend_workflow_execution.py`: Shared root-level Blend workflow execution surface for typed skill-workflow step resolution, provider-based operator resolution, dynamic operator-descriptor inference/adaptation, context-applied invocation orchestration, step/workflow lifecycle observation with `workflow_execution_id`, halt shaping, and persisted run emission below workstation.
- `blend_workflow_store.py`: Shared root-level Blend workflow persistence and query surface for plan/run storage, indexing, summary listing, and related-run lookup.
- `boundary.py`: Boundary-shape typing and boundary reasoning helpers.
- `capability_runtime.py`: Runtime capability grants and capability-to-broker/executor mapping.
- `constitutional_trace.py`: Constitutional trace snapshots, receipts, and replay comparison helpers.
- `controller_entrypoint_binding.py`: Dependency-light registration seam between the historical executable facade and outer CLI composition.
- `controller_entrypoints.py`: CLI/workstation composition and dispatch; constructs controllers through the canonical runtime owner rather than importing `main`.
- `controller_governance_bridge.py`: Controller-facing governance bridge methods rebound onto `BSSCController`.
- `controller_runtime.py`: Canonical `BSSCController` implementation and historical public runtime surface.
- `controller_runtime_binding.py`: Dependency-inversion seam used by nested host brokers to construct the application-registered controller without importing its implementation.
- `data_governance.py`: Compatibility facade for data-class and access rules
  owned by `realized_core_governance.data`.
- `decision_review_models.py`: Dependency-light decision-frame and review-item records, value sets, normalization, and stable identifiers; `decision_review.py` preserves the historical import surface while owning persistence and review-item projection.
- `direct_knowledge_reuse.py`: Direct knowledge reuse matching and lookup helpers.
- `example.py`: Small Wasmtime/example surface used as a runtime proof-of-life.
- `execution_framework_primitives.py`: Host-advertised supported-framework environment/default normalization plus exact compatibility aliases for portable descriptors now owned by `realized_skill_semantics.execution`.
- `execution_frameworks.py`: Python, bash, ansible, and Wasm learning and execution surfaces plus exact compatibility re-exports for portable executor descriptors and host-support normalization.
- `external_markdown_learning_pipeline.py`: `markdown-learn` document-to-artifact pipeline.
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
- `governed_skill_installation.py`: Governed `import-skill` installation, admission, persistence, and normalization.
- `host_interaction_*.py`: Historical compatibility facades preserving the
  pre-package host-interaction import paths and object identities. New code
  imports `realized_host_interaction`.
- `host_abi.py`: Stable host ABI, broker stability rules, and Wasm ABI definitions.
- `host_brokers.py`: Governed host brokers for fs, store, net, tool, and nested skill invocation through the current static broker registry.
- `host_mediation.py`: Effect mediation, capability enforcement, and trace recording.
- `id_generation.py`: Shared lower-layer slug and identifier construction helpers extracted below `main.py` for runtime/controller callers that need stable ids without importing controller composition directly.
- `learn.py`: Learning-token, discriminator, and selection-signal helpers.
- `learning_context.py`: Phase 1 LearningContext substrate for canonical learning-unit, learning-delta, learning-delta-operation, and subject-context records plus deterministic `corpus/<subject-id>/...` persistence, indexes, listing, and backward-compatible explicit delta application.
- `learning_context_paths.py`: Dependency-light subject identifiers and canonical corpus, decision-review, and derived-resource path construction shared by persistence and projection adapters.
- `itemize_models.py`: Dependency-light itemization records, value sets, and normalization helpers; `itemize.py` preserves the historical import surface while owning extraction and persistence behavior.
- `learning_context_projection.py`: Deterministic `LearningContext` projection into canonical `subject.typ` and compatibility `subject.md` scaffolds with stable section anchors, grouped unit sections, provenance, derived-skill, and update-log materialization.
- `learning_context_skill_projection.py`: Deterministic `LearningContext` runtime projection into canonical portable skill YAML for corpus-admitted linked units, compiled through the v2 skill document path and materialized under `derived/skills/`. Projection establishes subject scope and provenance; it does not perform governed skill installation or admission.
- `workstation/learning_capture.py`: Prompt-scoped workstation hook that turns successful chat “save learnings” markdown writes into chat `LearningSource`, `LearningDelta`, and merged `LearningContext` records without making raw markdown tools semantic by default.
- `macos_host_brokers.py`: macOS-specific broker implementations for device actions.
- `main.py`: Historical executable/import facade that preserves `import main` module identity while delegating to `controller_runtime.py` and lazily registering `controller_entrypoints.py`.
- `markdown_ir.py`: Markdown parsing and intermediate representation construction.
- `markdown_learning_artifact_semantics.py`: Markdown encounter-to-artifact semantic shaping.
- `non_achievedness_normalization.py`: Structured non-achievedness normalization orchestration over explicit runtime dependencies.
- `normalization_primitives.py`: Canonical dependency-light normalization helpers for schema, representations, boundary values, and runtime enums.
- `normalization_runtime_dependencies.py`: Explicit dependency surface used by structured non-achievedness normalization.
- `normalize.py`: Compatibility facade preserving historical normalization imports and object identities.
- `not_elaboration_ranking.py`: Canonical non-achievedness elaboration ranking.
- `prolog.py`: Prolog/title representation helpers and query support.
- `prompt_directives.py`: Prompt directive classification and intent-shaping helpers.
- `publication.py`: First publication substrate for claim-centered governed report publication, including typed publication/section/claim/source/build/render-artifact records, deterministic snapshot hashing, and explicit on-disk publication persistence under the subject corpus home.
- `publication_projection.py`: Deterministic `LearningContext`-to-`Publication` report projection, including admitted-unit claim extraction, section assignment, source loading, validation/build/render orchestration, and separate publication-tree materialization.
- `publication_render.py`: Deterministic Typst and markdown renderers plus reproducible publication build and render-artifact projection.
- `publication_validation.py`: First publication validation rules over unique section ids, claim/source references, and source-backed descriptive claims.
- `pure_theory_types.py`: Compatibility facade for the canonical formal theory
  terms in `realized_core_semantics.theory`.
- `python_skill_brokerization.py`: Python skill inspection and brokerization heuristics.
- `python_skill_host.py`: Child Python runtime host API for governed broker calls.
- `replay_verifier.py`: Run-bundle replay verification and governance receipt checks.
- `retrieval_ranking.py`: Retrieval scoring and ranking for artifact reuse and prompt matching.
- `run_bundle_io.py`: Run-bundle export/import and governance snapshot packaging.
- `run_outcome_harvest_and_reporting.py`: Run finalization, discovery harvest, and report emission.
- `runtime_controller_api.py`: Narrow subject-scope-aware bootstrap facade over the canonical controller runtime; preserves standalone callers without importing the historical `main.py` facade.
- `runtime_governance_context.py`: Runtime-facing governance resolution facade.
- `semantic_prompt_posture.py`: Prompt-posture classification and direct-answer preference helpers.
- `SEMANTIC_RELATION_VALIDATION.py`: Standalone semantic relation validation script.
- `semantic_text.py`: Semantic text normalization, literal decoding, and title/text helpers.
- `side.py`: Legacy artifact bundle import/export bridge and YAML artifact hydration helpers with identity-preserving exports from canonical owners.
- `side_runtime_dependencies.py`: Explicit named dependency surface for the legacy side bridge, replacing its former `main` namespace reach-through.
- `skill_export_projection.py`: Portable skill export projection, bundle export, and `export-skill` handling.
- `skill_compiler.py`: Initial portable-skill compiler seam that emits artifact-centered canonical IR analysis for governed installation.
- `skill_compatibility_export.py`: Compatibility-tier export adapters that project canonical skills into representative foreign tool and instruction-bundle surfaces.
- `skill_compatibility_import.py`: Compatibility-tier import adapters plus normalized `compatibility.adapters` payload shaping for foreign tool and instruction-bundle sources.
- `skill_boundary_normalization.py`: Compatibility aliases for package-owned boundary normalization plus the thin artifact/governance adapter used to preserve legacy synthesis precedence.
- `skill_composition.py`: Canonical leaf-level binding analysis, explicit mapper-backed composition execution, sequence-plan validation, and plan-wide permission aggregation for skill composition.
- `skill_governance.py`: Historical governed-skill adapter and admission
  orchestrator. It retains declaration synthesis, host-broker and Python-source
  preflight, current-use composition, and compatibility entry points; delegates
  policy-and-approval evaluation to `realized_core_governance.admission`; and
  preserves exact aliases for package-owned portable declaration schema and
  composition-right semantics.
- `skill_governance_primitives.py`: Compatibility facade for package-owned
  governed-skill vocabulary and normalization.
- `skill_ir.py`: Compatibility aliases for package-owned canonical IR and skill identity values plus the artifact-centered projection adapter for declaration, lifecycle, compatibility, runtime package, and hosting metadata.
- `skill_invocation_contract.py`: Compatibility facade preserving historical aliases to package-owned invocation values and normalization while re-exporting the workstation artifact-projection adapter.
- `skill_leaf_types.py`: Compatibility facade for canonical portable skill leaf values in `realized_skill_semantics.leaves`.
- `skill_lifecycle.py`: Compatibility facade for package-owned lifecycle
  normalization, projection, and lifecycle-only invocation-state rules.
- `skill_path_notation.py`: Compatibility facade for canonical portable skill paths in `realized_skill_semantics.paths`.
- `skill_registry.py`: Local skill registry projection and `export-skill-registry` support.
- `skill_safety_governance.py`: Compatibility facade for revocation and
  incident rules owned by `realized_core_governance.safety`.
- `skill_schema_io.py`: Portable skill schema hydration and import-file resolution.
- `store.py`: SQLite artifact store, indexing, persistence, and batch import support.
- `structured_learning_yaml.py`: Structured-learning YAML rendering helpers.
- `supplement.py`: LLM supplement/provider utilities and proposal-type labeling.
- `system_state.py`: System state model, persistence, effect traces, and capability grant storage.
- `tablet_safety_validation.py`: Standalone tablet-safety validation script.
- `title_depth_learning_validation.py`: Standalone title-depth learning validation script.
- `title_semantics.py`: Title semantics, title-depth, and Prolog-title helpers.
- `TRIAL_DOMAIN_VALIDATION.py`: Multi-domain trial runner for fresh-db curriculum validation.
- `validation_ladder.py`: Layered acceptance runner for the unit suite, workstation trial sweep, and chemistry milestone domain gate.
- `validation_sqlite.py`: Shared validation SQLite runtime allocation, RAM-disk setup, and report-archive helpers.
- `virtual_mounts.py`: Virtual mount definitions, safe path resolution, and mount policies.
- `wasm_skill_runtime.py`: Embedded Wasmtime runtime for governed Wasm skill execution.
- `workstation/__init__.py`: Inert namespace initializer for independently packaged workstation components.
- `workstation/builtin_skills.py`: Builtin workstation worker-skill catalog, including repo-search and Wasm demo workers.
- `workstation/capabilities.py`: Workstation capability schemas plus attachment-scoped capability execution, installed-skill invocation, workstation-backed shared Blend operator provider assembly for dynamic skill/capability operators, shared Blend operator/workflow store and execution adapters for `ws.skill.compose`, `ws.workflow.*`, and `ws.operator.*`, workstation publication of Blend workflow/step lifecycle events, and workstation-to-skill delegation shaping.
- `workstation/chat_commands.py`: Direct workstation chat slash-command handlers for skill lifecycle and skill-inspection operations without an LLM round-trip.
- `workstation/chat_ui.py`: Enhanced interactive workstation chat frontend with a Textual-first shell host, prompt-toolkit fallback, context suggestions, command history, and approval prompting over the same workstation session surface.
- `workstation/app_cli/src/workstation/app/cli/cli.py`: CLI handlers for workstation launch, prompt, chat, and trial commands.
- `workstation/delegation.py`: Thin workstation adapter over shared host-interaction delegation helpers.
- `workstation/direct_composition.py`: Prompt-local skill shortlisting and direct worker-composition helpers for workstation turns, including plain-path payload derivation for imported trial skills and action-aware routing across adjacent worker families like remove vs copy.
- `workstation/event_bus.py`: Optional workstation-local event-bus wrapper with typed event envelopes, Blinker-backed publication when available, fallback in-process subscription when not, and receipt-to-host-event derivation helpers.
- `workstation/ui_flutter/`: Flutter Material 3 workstation client over the canonical gRPC shell and subject-workflow services.
- `workstation/governance.py`: Workstation-specific governance helpers, including the skill-home default policy and transient bundle-policy filtering.
- `workstation/foundation_host/src/workstation/foundation/host/host_interaction.py`: Workstation-backed adapter for the shared host-interaction contract.
- `workstation/layout.py`: Renderer-neutral workstation tab/pane layout metadata shared across shell projections, including the explicit subject-workflow phase tabs and coarse pane sizing hints.
- `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py`: Host-owned OpenAI-compatible workstation tool-loop driver, including workflow-run preference and workflow-query guidance when first-class workflow capabilities are available.
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
- `workstation/skill_invocation.py`: Workstation skill discovery, resolution, prompt-local invocation shaping, top-level input compatibility, and bounded nested-worker answer/receipt projection.
- `workstation/skills/core/invocation_contract.py`: Canonical invocation request/result records and deterministic artifact/result projections used by workstation skill invocation.
- `workstation/task_contract.py`: Boundary-complete workstation task normalization from natural-language prompts.
- `scripts/generate_workstation_protos.py`: Regenerates the committed workstation protobuf/gRPC Python stubs from the checked-in `.proto` contracts.
- `scripts/verify_core_distribution.py`: Inspects the six built standalone
  core wheels, including `realized-host-interaction`, verifies their distinct
  file ownership, rejects outer-application files, then runs the separately
  extracted wheel contents against plain SQLite outside the repository import
  path.

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
- `workstation/tests/test_workstation_event_bus.py`: Tests for the workstation-local event bus over subscriber isolation, receipt-derived events, turn lifecycle publication, permission/skill catalog mutation events, and bridged Blend workflow/step lifecycle events.
- `workstation/ui_flutter/test/workstation_app_test.dart`: Flutter widget-level BDD coverage over bootstrap, chat, subject workflow tabs, and utility-tab layout behavior.
- `workstation/tests/test_workstation_projection_models.py`: Tests for neutral workstation permission-panel and workflow-graph projection contracts.
- `workstation/tests/test_workstation_subject_workflow_api.py`: Tests for the extracted subject-workflow application service and in-process gRPC adapter.
- `workstation/tests/test_workstation_subscriber_controllers.py`: Tests for workstation event-bus subscriber controllers over live Blend step activity projection and context/projection invalidation.

## Trial Validators
- `trials/BOUNDARY_SHAPE_VALIDATION.py`: Boundary-shape curriculum validator.
- `trials/LEARNED_FUNCTION_VALIDATION.py`: Learned-function validator for fresh-db function reuse.
- `trials/PROBABILITY_INFORMATION_RELATION_VALIDATION.py`: Probability/information relation curriculum validator.
