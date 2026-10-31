# Repository Dependency Report

This report is generated deterministically by `scripts/check_architecture_boundaries.py`. It records architecture facts; it does not import or execute production code.

## Components

| Component | Layer | Distribution | Public module prefix |
| --- | --- | --- | --- |
| `app_cli` | `entry` | `realized-workstation-app-cli` | `workstation.app.cli` |
| `blend` | `domain` | `realized-blend` | `realized_blend` |
| `blend_application` | `runtime_execution` | `realized-blend-application` | `realized_blend_application` |
| `contracts` | `contracts` | `realized-workstation-contracts` | `workstation.contracts` |
| `coordinated_transformation` | `subject_domain` | `coordinated-transformation` | `coordinated_transformation` |
| `core_app` | `entry` | `realized-core` | `realized_core` |
| `core_conversation` | `workstation` | `realized-core-conversation` | `realized_core_conversation` |
| `core_engine` | `controller` | `realized-core-engine` | `realized_core_engine` |
| `core_governance` | `governance` | `realized-core-governance` | `realized_core_governance` |
| `core_llm` | `llm` | `realized-core-llm` | `realized_core_llm` |
| `core_semantics` | `semantic_contracts` | `realized-core-semantics` | `realized_core_semantics` |
| `dst` | `subject_domain` | `dst` | `dst` |
| `exchange` | `exchange_adapters` | `realized-exchange` | `realized_exchange` |
| `foundation_events` | `foundation` | `realized-workstation-foundation-events` | `workstation.foundation.events` |
| `foundation_host` | `foundation` | `realized-workstation-foundation-host` | `workstation.foundation.host` |
| `foundation_models` | `foundation` | `realized-workstation-foundation-models` | `workstation.foundation.models` |
| `foundation_projections` | `foundation` | `realized-workstation-foundation-projections` | `workstation.foundation.projections` |
| `governed_core` | `core` | `realized-core-runtime` | `realized_core_runtime` |
| `grpc_definitions` | `exchange_contracts` | `realized-workstation-grpc-definitions` | `workstation.grpc.definitions` |
| `grpc_implementation` | `exchange_adapters` | `realized-workstation-grpc-implementation` | `workstation.grpc.implementation` |
| `host_interaction` | `host_substrate` | `realized-host-interaction` | `realized_host_interaction` |
| `namespace` | `namespace` | `realized-workstation` | `workstation` |
| `root_compatibility` | `compatibility` | `realized-compatibility` | `realized_compatibility` |
| `runtime_core` | `controller` | `realized-workstation-runtime-core` | `workstation.runtime.core` |
| `shell_core` | `workstation` | `realized-workstation-shell-core` | `workstation.shell.core` |
| `skill_application` | `skills` | `realized-skill-application` | `realized_skill_application` |
| `skill_semantics` | `skill_contracts` | `realized-skill-semantics` | `realized_skill_semantics` |
| `skills_builtin` | `skills` | `realized-workstation-skills-builtin` | `workstation.skills.builtin` |
| `skills_core` | `skills` | `realized-workstation-skills-core` | `workstation.skills.core` |
| `skills_planning` | `skills` | `realized-workstation-skills-planning` | `workstation.skills.planning` |
| `subject_core` | `governance` | `realized-workstation-subject-core` | `workstation.subject.core` |
| `subject_service` | `governance` | `realized-workstation-subject-service` | `workstation.subject.service` |
| `subject_textual` | `workstation_adapter` | `realized-workstation-subject-textual` | `workstation.subject.textual` |
| `ui_shared` | `workstation` | `realized-workstation-ui-shared` | `workstation.ui.shared` |
| `ui_textual` | `workstation_adapter` | `realized-workstation-ui-textual` | `workstation.ui.textual` |
| `validation` | `validation` | `realized-validation` | `realized_validation` |
| `workstation_compatibility` | `compatibility` | `realized-workstation-compatibility` | `workstation.compatibility` |

## Root Module Ownership

Every repository-root Python module has one explicit responsibility. Status is orthogonal: an entrypoint or compatibility facade retains the owner of the behavior it exposes.

| Module | Owner | Status |
| --- | --- | --- |
| `SEMANTIC_RELATION_VALIDATION` | `validation_trial` | `validation` |
| `TRIAL_DOMAIN_VALIDATION` | `validation_trial` | `validation` |
| `tablet_safety_validation` | `validation_trial` | `validation` |
| `title_depth_learning_validation` | `validation_trial` | `validation` |

## Root Package Family Ownership

Top-level Python package families that are not UV workspace projects are measured by the same responsibility policy as root modules.

| Package family | Owner | Status |
| --- | --- | --- |
| `design` | `validation_trial` | `validation` |

## Target Root-Owner Dependency Policy

This policy describes the intended acyclic responsibility graph. Current violations are measured separately and may only shrink.

| Owner | May depend on |
| --- | --- |
| `blend` | `governance`, `portable_skills`, `runtime_execution`, `semantic_model` |
| `compatibility` | `blend`, `controller`, `governance`, `llm`, `persistence_adapter`, `portable_skills`, `runtime_execution`, `semantic_model`, `subject_domain` |
| `controller` | `blend`, `governance`, `llm`, `portable_skills`, `runtime_execution`, `semantic_model` |
| `entry_exchange` | `blend`, `controller`, `governance`, `llm`, `persistence_adapter`, `portable_skills`, `runtime_execution`, `semantic_model`, `subject_domain` |
| `governance` | `portable_skills`, `semantic_model` |
| `llm` | `semantic_model` |
| `persistence_adapter` | `blend`, `governance`, `portable_skills`, `semantic_model`, `subject_domain` |
| `portable_skills` | `semantic_model` |
| `runtime_execution` | `governance`, `portable_skills`, `semantic_model` |
| `semantic_model` | none |
| `subject_domain` | `governance`, `llm`, `portable_skills`, `runtime_execution`, `semantic_model` |
| `validation_trial` | `blend`, `compatibility`, `controller`, `entry_exchange`, `governance`, `llm`, `persistence_adapter`, `portable_skills`, `runtime_execution`, `semantic_model`, `subject_domain` |

## Current Root-Owner Dependency Edges

| Source | Target | Allowed by target policy |
| --- | --- | --- |

## Package Imports Of Root Compatibility Facades

No workspace package imports a root compatibility facade.

## Canonical Root Imports Of Compatibility Facades

No canonical root module imports a compatibility facade.

## Dependency Edges

| Source | Target | Declared | Allowed by target policy | Evidence |
| --- | --- | --- | --- | --- |
| `app_cli` | `contracts` | yes | yes | `workstation/app_cli/src/workstation/app/cli/composition.py` |
| `app_cli` | `core_engine` | yes | yes | `workstation/app_cli/src/workstation/app/cli/composition.py`, `workstation/app_cli/src/workstation/app/cli/runtime_controller.py` |
| `app_cli` | `core_semantics` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py`, `workstation/app_cli/src/workstation/app/cli/runtime_controller.py` |
| `app_cli` | `exchange` | yes | yes | `workstation/app_cli/src/workstation/app/cli/composition.py`, `workstation/app_cli/src/workstation/app/cli/runtime_controller.py` |
| `app_cli` | `foundation_host` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py`, `workstation/app_cli/src/workstation/app/cli/composition.py` |
| `app_cli` | `governed_core` | yes | yes | `workstation/app_cli/src/workstation/app/cli/composition.py` |
| `app_cli` | `grpc_implementation` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `app_cli` | `host_interaction` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py`, `workstation/app_cli/src/workstation/app/cli/composition.py`, `workstation/app_cli/src/workstation/app/cli/runtime_controller.py` |
| `app_cli` | `runtime_core` | yes | yes | `workstation/app_cli/src/workstation/app/cli/composition.py` |
| `app_cli` | `shell_core` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `app_cli` | `subject_core` | yes | yes | `workstation/app_cli/src/workstation/app/cli/runtime_controller.py` |
| `app_cli` | `subject_service` | yes | yes | `workstation/app_cli/src/workstation/app/cli/composition.py` |
| `app_cli` | `ui_shared` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `app_cli` | `ui_textual` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `blend` | `core_semantics` | yes | yes | `blend/src/realized_blend/execution.py`, `blend/src/realized_blend/observations.py`, `blend/src/realized_blend/operators.py` (+1 more) |
| `blend_application` | `blend` | yes | yes | `blend_application/src/realized_blend_application/execution.py`, `blend_application/src/realized_blend_application/operators.py`, `blend_application/src/realized_blend_application/workflow_store.py` (+3 more) |
| `blend_application` | `core_semantics` | yes | yes | `blend_application/src/realized_blend_application/operators.py`, `blend_application/src/realized_blend_application/workflow_store.py`, `blend_application/src/realized_blend_application/workflows.py` (+1 more) |
| `blend_application` | `governed_core` | yes | yes | `blend_application/src/realized_blend_application/operators.py` |
| `blend_application` | `skill_application` | yes | yes | `blend_application/src/realized_blend_application/execution.py` |
| `blend_application` | `skill_semantics` | yes | yes | `blend_application/src/realized_blend_application/operators.py` |
| `core_app` | `core_conversation` | yes | yes | `core_app/src/realized_core/chat.py`, `core_app/src/realized_core/conversation.py` |
| `core_app` | `core_engine` | yes | yes | `core_app/src/realized_core/cli.py` |
| `core_app` | `core_llm` | yes | yes | `core_app/src/realized_core/chat.py`, `core_app/src/realized_core/cli.py`, `core_app/src/realized_core/planning.py` |
| `core_conversation` | `core_engine` | yes | yes | `core_conversation/src/realized_core_conversation/contracts.py`, `core_conversation/src/realized_core_conversation/ports.py`, `core_conversation/src/realized_core_conversation/service.py` |
| `core_conversation` | `core_llm` | yes | yes | `core_conversation/src/realized_core_conversation/service.py` |
| `core_engine` | `core_governance` | yes | yes | `core_engine/src/realized_core_engine/constitutional_trace.py`, `core_engine/src/realized_core_engine/governance_inventory.py`, `core_engine/src/realized_core_engine/governed_skill_access.py` (+2 more) |
| `core_engine` | `core_llm` | yes | yes | `core_engine/src/realized_core_engine/supplement.py` |
| `core_engine` | `core_semantics` | yes | yes | `core_engine/src/realized_core_engine/api.py`, `core_engine/src/realized_core_engine/artifact_answer_resolution.py`, `core_engine/src/realized_core_engine/artifact_semantics.py` (+29 more) |
| `core_engine` | `governed_core` | yes | yes | `core_engine/src/realized_core_engine/api.py`, `core_engine/src/realized_core_engine/canonical_reduction.py`, `core_engine/src/realized_core_engine/configuration.py` (+11 more) |
| `core_engine` | `host_interaction` | yes | yes | `core_engine/src/realized_core_engine/canonical_reduction.py`, `core_engine/src/realized_core_engine/contracts.py`, `core_engine/src/realized_core_engine/controller_runtime.py` (+4 more) |
| `core_engine` | `skill_semantics` | yes | yes | `core_engine/src/realized_core_engine/configuration.py`, `core_engine/src/realized_core_engine/controller_runtime.py`, `core_engine/src/realized_core_engine/governed_skill_access.py` (+4 more) |
| `core_governance` | `core_semantics` | yes | yes | `core_governance/src/realized_core_governance/admission.py`, `core_governance/src/realized_core_governance/approval.py`, `core_governance/src/realized_core_governance/inventory.py` (+4 more) |
| `core_governance` | `skill_semantics` | yes | yes | `core_governance/src/realized_core_governance/admission.py`, `core_governance/src/realized_core_governance/current_use.py`, `core_governance/src/realized_core_governance/declarations.py` |
| `dst` | `coordinated_transformation` | yes | yes | `dst/src/dst/normalization.py`, `dst/src/dst/orchestration.py`, `dst/src/dst/projection.py` (+1 more) |
| `dst` | `core_semantics` | yes | yes | `dst/src/dst/discovery.py`, `dst/src/dst/normalization.py`, `dst/src/dst/orchestration.py` (+2 more) |
| `exchange` | `core_engine` | yes | yes | `exchange/src/realized_exchange/artifact_yaml.py`, `exchange/src/realized_exchange/dependencies.py`, `exchange/src/realized_exchange/markdown_learning_pipeline.py` (+3 more) |
| `exchange` | `core_governance` | yes | yes | `exchange/src/realized_exchange/registry.py`, `exchange/src/realized_exchange/run_bundle.py`, `exchange/src/realized_exchange/skill_export.py` (+1 more) |
| `exchange` | `core_semantics` | yes | yes | `exchange/src/realized_exchange/artifact_yaml.py`, `exchange/src/realized_exchange/compatibility_export.py`, `exchange/src/realized_exchange/compatibility_import.py` (+8 more) |
| `exchange` | `governed_core` | yes | yes | `exchange/src/realized_exchange/markdown_learning_pipeline.py`, `exchange/src/realized_exchange/registry.py`, `exchange/src/realized_exchange/run_bundle.py` (+2 more) |
| `exchange` | `skill_application` | yes | yes | `exchange/src/realized_exchange/compiler.py`, `exchange/src/realized_exchange/registry.py`, `exchange/src/realized_exchange/skill_export.py` (+1 more) |
| `exchange` | `skill_semantics` | yes | yes | `exchange/src/realized_exchange/artifact_yaml.py`, `exchange/src/realized_exchange/compatibility_import.py`, `exchange/src/realized_exchange/run_bundle.py` (+2 more) |
| `exchange` | `subject_core` | yes | yes | `exchange/src/realized_exchange/learning_context.py`, `exchange/src/realized_exchange/learning_context_skills.py` |
| `exchange` | `subject_service` | yes | yes | `exchange/src/realized_exchange/learning_context.py`, `exchange/src/realized_exchange/learning_context_skills.py` |
| `foundation_events` | `contracts` | yes | yes | `workstation/foundation_events/src/workstation/foundation/events/event_bus.py` |
| `foundation_events` | `core_semantics` | yes | yes | `workstation/foundation_events/src/workstation/foundation/events/event_bus.py`, `workstation/foundation_events/src/workstation/foundation/events/message_tracing.py` |
| `foundation_events` | `host_interaction` | yes | yes | `workstation/foundation_events/src/workstation/foundation/events/event_bus.py` |
| `foundation_host` | `contracts` | yes | yes | `workstation/foundation_host/src/workstation/foundation/host/artifact_repository.py`, `workstation/foundation_host/src/workstation/foundation/host/controller_runtime.py`, `workstation/foundation_host/src/workstation/foundation/host/skill_exchange.py` (+1 more) |
| `foundation_host` | `core_governance` | yes | yes | `workstation/foundation_host/src/workstation/foundation/host/governance.py` |
| `foundation_host` | `core_semantics` | yes | yes | `workstation/foundation_host/src/workstation/foundation/host/delegation.py`, `workstation/foundation_host/src/workstation/foundation/host/governance.py`, `workstation/foundation_host/src/workstation/foundation/host/task_contract.py` |
| `foundation_host` | `foundation_models` | yes | yes | `workstation/foundation_host/src/workstation/foundation/host/delegation.py`, `workstation/foundation_host/src/workstation/foundation/host/host_interaction.py`, `workstation/foundation_host/src/workstation/foundation/host/task_contract.py` |
| `foundation_host` | `host_interaction` | yes | yes | `workstation/foundation_host/src/workstation/foundation/host/delegation.py`, `workstation/foundation_host/src/workstation/foundation/host/host_interaction.py` |
| `foundation_projections` | `blend` | yes | yes | `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py` |
| `foundation_projections` | `contracts` | yes | yes | `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py` |
| `foundation_projections` | `core_semantics` | yes | yes | `workstation/foundation_projections/src/workstation/foundation/projections/activity_receipts.py`, `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py` |
| `foundation_projections` | `foundation_models` | yes | yes | `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py` |
| `governed_core` | `core_governance` | yes | yes | `core_runtime/src/realized_core_runtime/capabilities.py`, `core_runtime/src/realized_core_runtime/host_brokers.py`, `core_runtime/src/realized_core_runtime/python_host.py` (+3 more) |
| `governed_core` | `core_semantics` | yes | yes | `core_runtime/src/realized_core_runtime/capabilities.py`, `core_runtime/src/realized_core_runtime/execution.py`, `core_runtime/src/realized_core_runtime/executor_support.py` (+7 more) |
| `governed_core` | `host_interaction` | yes | yes | `core_runtime/src/realized_core_runtime/execution.py`, `core_runtime/src/realized_core_runtime/host_brokers.py`, `core_runtime/src/realized_core_runtime/host_realizers.py` (+2 more) |
| `governed_core` | `skill_semantics` | yes | yes | `core_runtime/src/realized_core_runtime/capabilities.py`, `core_runtime/src/realized_core_runtime/execution.py`, `core_runtime/src/realized_core_runtime/executor_support.py` (+2 more) |
| `grpc_implementation` | `contracts` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_shell_grpc.py` |
| `grpc_implementation` | `core_semantics` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_bootstrap_grpc.py` |
| `grpc_implementation` | `foundation_events` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_bootstrap_grpc.py` (+1 more) |
| `grpc_implementation` | `grpc_definitions` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_bootstrap_grpc.py` (+2 more) |
| `grpc_implementation` | `runtime_core` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_grpc_host.py` |
| `grpc_implementation` | `shell_core` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_grpc_host.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_shell_grpc.py` |
| `grpc_implementation` | `subject_core` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py` |
| `grpc_implementation` | `subject_service` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_grpc_host.py` |
| `root_compatibility` | `app_cli` | yes | yes | `compatibility_api/src/args.py`, `compatibility_api/src/controller_entrypoints.py` |
| `root_compatibility` | `blend` | yes | yes | `compatibility_api/src/blend_context.py`, `compatibility_api/src/blend_operator.py`, `compatibility_api/src/blend_session.py` (+2 more) |
| `root_compatibility` | `blend_application` | yes | yes | `compatibility_api/src/blend_operator_store.py`, `compatibility_api/src/blend_workflow_execution.py` |
| `root_compatibility` | `core_engine` | yes | yes | `compatibility_api/src/args.py`, `compatibility_api/src/controller_entrypoints.py`, `compatibility_api/src/governance_inventory.py` (+5 more) |
| `root_compatibility` | `core_governance` | yes | yes | `compatibility_api/src/approval_governance.py`, `compatibility_api/src/data_governance.py`, `compatibility_api/src/governed_skill_installation.py` (+4 more) |
| `root_compatibility` | `core_semantics` | yes | yes | `compatibility_api/src/applied_theory_types.py`, `compatibility_api/src/approval_governance.py`, `compatibility_api/src/controller_entrypoints.py` (+6 more) |
| `root_compatibility` | `exchange` | yes | yes | `compatibility_api/src/controller_entrypoints.py`, `compatibility_api/src/external_markdown_learning_pipeline.py`, `compatibility_api/src/governed_skill_installation.py` (+3 more) |
| `root_compatibility` | `governed_core` | yes | yes | `compatibility_api/src/controller_entrypoints.py`, `compatibility_api/src/execution_framework_primitives.py`, `compatibility_api/src/execution_frameworks.py` (+2 more) |
| `root_compatibility` | `host_interaction` | yes | yes | `compatibility_api/src/controller_entrypoints.py` |
| `root_compatibility` | `runtime_core` | yes | yes | `compatibility_api/src/blend_context.py`, `compatibility_api/src/blend_session.py` |
| `root_compatibility` | `skill_application` | yes | yes | `compatibility_api/src/governed_skill_installation.py`, `compatibility_api/src/skill_boundary_normalization.py`, `compatibility_api/src/skill_composition.py` (+1 more) |
| `root_compatibility` | `skill_semantics` | yes | yes | `compatibility_api/src/governed_skill_installation.py`, `compatibility_api/src/replay_verifier.py`, `compatibility_api/src/skill_invocation_contract.py` (+2 more) |
| `root_compatibility` | `skills_core` | yes | yes | `compatibility_api/src/skill_invocation_contract.py` |
| `root_compatibility` | `subject_core` | yes | yes | `compatibility_api/src/decision_review.py`, `compatibility_api/src/decision_review_constructs.py`, `compatibility_api/src/itemize.py` (+2 more) |
| `root_compatibility` | `validation` | yes | yes | `compatibility_api/src/controller_entrypoints.py` |
| `runtime_core` | `blend` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/blend_adapters.py`, `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py` (+1 more) |
| `runtime_core` | `blend_application` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/blend_adapters.py`, `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py` (+1 more) |
| `runtime_core` | `contracts` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py` (+1 more) |
| `runtime_core` | `core_governance` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py` |
| `runtime_core` | `core_llm` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py` |
| `runtime_core` | `core_semantics` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py` (+4 more) |
| `runtime_core` | `foundation_events` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py` (+2 more) |
| `runtime_core` | `foundation_host` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`, `workstation/runtime_core/src/workstation/runtime/core/subject_host_actions.py` (+1 more) |
| `runtime_core` | `foundation_models` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/blend_adapters.py`, `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py` (+3 more) |
| `runtime_core` | `foundation_projections` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py` (+2 more) |
| `runtime_core` | `governed_core` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py` |
| `runtime_core` | `host_interaction` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py` (+1 more) |
| `runtime_core` | `skill_application` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py` |
| `runtime_core` | `skill_semantics` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py` |
| `runtime_core` | `skills_core` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py` (+2 more) |
| `runtime_core` | `skills_planning` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/blend_adapters.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py` |
| `runtime_core` | `subject_core` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/subject_host_actions.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py` |
| `runtime_core` | `subject_service` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/session.py`, `workstation/runtime_core/src/workstation/runtime/core/subject_host_actions.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py` |
| `shell_core` | `contracts` | yes | yes | `workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_client.py` |
| `shell_core` | `core_conversation` | yes | yes | `workstation/shell_core/src/workstation/shell/core/governed_conversation.py` |
| `shell_core` | `core_llm` | yes | yes | `workstation/shell_core/src/workstation/shell/core/governed_conversation.py` |
| `shell_core` | `core_semantics` | yes | yes | `workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_client.py` |
| `shell_core` | `foundation_events` | yes | yes | `workstation/shell_core/src/workstation/shell/core/application_facade.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py` |
| `shell_core` | `foundation_models` | yes | yes | `workstation/shell_core/src/workstation/shell/core/application_facade.py` |
| `shell_core` | `foundation_projections` | yes | yes | `workstation/shell_core/src/workstation/shell/core/workstation_shell_backend.py` |
| `shell_core` | `grpc_definitions` | yes | yes | `workstation/shell_core/src/workstation/shell/core/workstation_shell_client.py` |
| `shell_core` | `runtime_core` | yes | yes | `workstation/shell_core/src/workstation/shell/core/application_facade.py`, `workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/trial_validation.py` (+2 more) |
| `shell_core` | `skills_core` | yes | yes | `workstation/shell_core/src/workstation/shell/core/trial_validation.py` |
| `shell_core` | `subject_service` | yes | yes | `workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py` |
| `skill_application` | `core_governance` | yes | yes | `skill_application/src/realized_skill_application/ir.py`, `skill_application/src/realized_skill_application/normalization.py`, `skill_application/src/realized_skill_application/projection.py` |
| `skill_application` | `core_semantics` | yes | yes | `skill_application/src/realized_skill_application/composition.py`, `skill_application/src/realized_skill_application/ir.py`, `skill_application/src/realized_skill_application/normalization.py` (+1 more) |
| `skill_application` | `governed_core` | yes | yes | `skill_application/src/realized_skill_application/ir.py`, `skill_application/src/realized_skill_application/normalization.py` |
| `skill_application` | `skill_semantics` | yes | yes | `skill_application/src/realized_skill_application/composition.py`, `skill_application/src/realized_skill_application/ir.py`, `skill_application/src/realized_skill_application/normalization.py` |
| `skill_semantics` | `core_semantics` | yes | yes | `skill_semantics/src/realized_skill_semantics/compatibility.py`, `skill_semantics/src/realized_skill_semantics/composition.py`, `skill_semantics/src/realized_skill_semantics/execution.py` (+4 more) |
| `skills_builtin` | `core_semantics` | yes | yes | `workstation/skills_builtin/src/workstation/skills/builtin/builtin_skills.py` |
| `skills_core` | `contracts` | yes | yes | `workstation/skills_core/src/workstation/skills/core/direct_composition.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py` |
| `skills_core` | `core_governance` | yes | yes | `workstation/skills_core/src/workstation/skills/core/governance.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py` |
| `skills_core` | `core_semantics` | yes | yes | `workstation/skills_core/src/workstation/skills/core/direct_composition.py`, `workstation/skills_core/src/workstation/skills/core/governance.py`, `workstation/skills_core/src/workstation/skills/core/invocation_contract.py` (+2 more) |
| `skills_core` | `foundation_host` | yes | yes | `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py` |
| `skills_core` | `foundation_models` | yes | yes | `workstation/skills_core/src/workstation/skills/core/direct_composition.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py` |
| `skills_core` | `governed_core` | yes | yes | `workstation/skills_core/src/workstation/skills/core/governance.py`, `workstation/skills_core/src/workstation/skills/core/invocation_contract.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py` |
| `skills_core` | `host_interaction` | yes | yes | `workstation/skills_core/src/workstation/skills/core/skill_invocation.py` |
| `skills_core` | `skill_application` | yes | yes | `workstation/skills_core/src/workstation/skills/core/invocation_contract.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py` |
| `skills_core` | `skill_semantics` | yes | yes | `workstation/skills_core/src/workstation/skills/core/invocation_contract.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py` |
| `skills_core` | `skills_builtin` | yes | yes | `workstation/skills_core/src/workstation/skills/core/skill_invocation.py` |
| `skills_planning` | `contracts` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `core_semantics` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `foundation_host` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_home.py` |
| `skills_planning` | `foundation_models` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `governed_core` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `skill_application` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `skill_semantics` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `skills_core` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py`, `workstation/skills_planning/src/workstation/skills/planning/skill_home.py` |
| `subject_core` | `contracts` | yes | yes | `workstation/subject_core/src/workstation/subject/core/subject_workflow.py` |
| `subject_core` | `coordinated_transformation` | yes | yes | `workstation/subject_core/src/workstation/subject/core/decision_review_projection.py` |
| `subject_core` | `core_semantics` | yes | yes | `workstation/subject_core/src/workstation/subject/core/decision_review.py`, `workstation/subject_core/src/workstation/subject/core/decision_review_constructs.py`, `workstation/subject_core/src/workstation/subject/core/decision_review_policy.py` (+14 more) |
| `subject_core` | `dst` | yes | yes | `workstation/subject_core/src/workstation/subject/core/subject_workflow.py` |
| `subject_core` | `governed_core` | yes | yes | `workstation/subject_core/src/workstation/subject/core/publication_render.py`, `workstation/subject_core/src/workstation/subject/core/subject_workflow.py` |
| `subject_service` | `contracts` | yes | yes | `workstation/subject_service/src/workstation/subject/service/subject_workflow_api.py`, `workstation/subject_service/src/workstation/subject/service/subject_workflow_client.py` |
| `subject_service` | `core_semantics` | yes | yes | `workstation/subject_service/src/workstation/subject/service/client_sessions.py`, `workstation/subject_service/src/workstation/subject/service/learning_capture.py`, `workstation/subject_service/src/workstation/subject/service/learning_context_skills.py` (+3 more) |
| `subject_service` | `foundation_events` | yes | yes | `workstation/subject_service/src/workstation/subject/service/subject_workflow_api.py` |
| `subject_service` | `foundation_models` | yes | yes | `workstation/subject_service/src/workstation/subject/service/learning_capture.py` |
| `subject_service` | `grpc_definitions` | yes | yes | `workstation/subject_service/src/workstation/subject/service/subject_workflow_client.py` |
| `subject_service` | `subject_core` | yes | yes | `workstation/subject_service/src/workstation/subject/service/client_sessions.py`, `workstation/subject_service/src/workstation/subject/service/learning_capture.py`, `workstation/subject_service/src/workstation/subject/service/learning_context_persistence.py` (+3 more) |
| `subject_textual` | `contracts` | yes | yes | `workstation/subject_textual/src/workstation/subject/textual/application_facade.py`, `workstation/subject_textual/src/workstation/subject/textual/models.py`, `workstation/subject_textual/src/workstation/subject/textual/subject_workflow_textual_backend.py` |
| `ui_shared` | `core_semantics` | yes | yes | `workstation/ui_shared/src/workstation/ui/shared/activity_view.py` |
| `ui_shared` | `foundation_projections` | yes | yes | `workstation/ui_shared/src/workstation/ui/shared/activity_view.py` |
| `ui_shared` | `host_interaction` | yes | yes | `workstation/ui_shared/src/workstation/ui/shared/activity_view.py` |
| `ui_textual` | `contracts` | yes | yes | `workstation/ui_textual/src/workstation/ui/textual/chat_ui.py` |
| `ui_textual` | `core_semantics` | yes | yes | `workstation/ui_textual/src/workstation/ui/textual/chat_ui.py` |
| `ui_textual` | `foundation_projections` | yes | yes | `workstation/ui_textual/src/workstation/ui/textual/chat_ui.py` |
| `ui_textual` | `shell_core` | yes | yes | `workstation/ui_textual/src/workstation/ui/textual/chat_ui.py` |
| `ui_textual` | `subject_textual` | yes | yes | `workstation/ui_textual/src/workstation/ui/textual/chat_ui.py` |
| `ui_textual` | `ui_shared` | yes | yes | `workstation/ui_textual/src/workstation/ui/textual/chat_ui.py` |
| `workstation_compatibility` | `contracts` | yes | yes | `workstation/compatibility_api/src/workstation/shell/core/shell_prompt_routing.py` |
| `workstation_compatibility` | `runtime_core` | yes | yes | `workstation/compatibility_api/src/workstation/foundation/events/subscriber_controllers.py`, `workstation/compatibility_api/src/workstation/foundation/host/llm_driver.py` |
| `workstation_compatibility` | `subject_service` | yes | yes | `workstation/compatibility_api/src/workstation/foundation/host/client_sessions.py`, `workstation/compatibility_api/src/workstation/foundation/host/learning_capture.py` |

## Dynamic Dependency Contracts

No dynamic dependency contracts are required.

## Unobserved Allowed Dependencies

Every allowed dependency is statically observed or dynamically contracted.

## Cycles

No package cycles were found.

## Compatibility Alias Edges

No compatibility-alias dependency edges were found.

## Remaining Architecture Obligations

No forbidden root-owner dependency obligation remains.

### Package Compatibility Aliases

| ID | Component edge | Support | Durable name | Review condition |
| --- | --- | --- | --- | --- |
| `foundation-events-projection-subscriber` | `workstation_compatibility` -> `runtime_core` | `supported` | `canonical_class_module` | Review at each minor release while generic historical qualified-name loading remains supported. |
| `foundation-host-client-sessions` | `workstation_compatibility` -> `subject_service` | `supported` | `canonical_class_module` | Review at each minor release while generic historical qualified-name loading remains supported. |
| `foundation-host-learning-capture` | `workstation_compatibility` -> `subject_service` | `supported` | `none` | Review at each minor release as an explicitly shipped historical import ABI. |
| `foundation-host-llm-driver` | `workstation_compatibility` -> `runtime_core` | `supported` | `canonical_function_module` | Review at each minor release while historical function-module and patch-target support remains public. |
| `shell-prompt-routing-contract` | `workstation_compatibility` -> `contracts` | `supported` | `canonical_function_module` | Review at each minor release while generic historical qualified-name loading remains supported. |

## Combined Graph Metrics

| Metric | Count |
| --- | ---: |
| Nodes | 42 |
| Edges | 163 |
| Cyclic SCCs | 0 |
| Nodes in cyclic SCCs | 0 |
| Edges internal to cyclic SCCs | 0 |
| Largest cyclic SCC nodes | 0 |

## Single-Edge SCC Sensitivity

This is a removal-only topology simulation, not an extraction recommendation. A candidate is safe only if preserving its behavior does not add replacement edges that recreate the cycle.
No single internal edge has structural SCC impact.

## Root-Boundary Classification Ledger

Classifications are explicit policy metadata from `architecture/boundaries.toml`. Unlisted root modules are conservatively classified as `orchestration`.

| Direction | Source | Target | Category |
| --- | --- | --- | --- |
| `root_to_component` | `SEMANTIC_RELATION_VALIDATION` | `core_engine` | `orchestration` |
| `root_to_component` | `TRIAL_DOMAIN_VALIDATION` | `validation` | `orchestration` |
| `root_to_component` | `tablet_safety_validation` | `validation` | `orchestration` |
| `root_to_component` | `title_depth_learning_validation` | `validation` | `orchestration` |

## Root-Module Dependencies

No workspace package imports a root application module.

## Root-to-Component Dependencies

- `SEMANTIC_RELATION_VALIDATION` -> `core_engine` (`SEMANTIC_RELATION_VALIDATION.py`)
- `TRIAL_DOMAIN_VALIDATION` -> `validation` (`TRIAL_DOMAIN_VALIDATION.py`)
- `tablet_safety_validation` -> `validation` (`tablet_safety_validation.py`)
- `title_depth_learning_validation` -> `validation` (`title_depth_learning_validation.py`)

## Root-to-Root Dependencies

No root application module imports another root module.

## Component-to-Root-Package Dependencies

No workspace component imports a top-level package family.

## Root-Module-to-Package Dependencies

No root module imports a top-level package family.

## Root-Package-to-Component Dependencies

No top-level package family imports a workspace component.

## Root-Package-to-Module Dependencies

No top-level package family imports a root module.

## Root-Package-to-Package Dependencies

No top-level package family imports another package family.

## Combined Root/Package Cycles

No cycles span root modules, top-level package families, and workspace packages.

## Wildcard Exports

No wildcard exports were found in scanned production sources.

## Ratchet Rules

The checked-in baseline records the facts above. Declared compatibility aliases preserve historical ABI; every measured category remains closed to expansion. The checker fails for unowned, multiply owned, or stale root modules or package families; changed root ownership; package or canonical-root imports of compatibility facades; new dependency edges; undeclared or forbidden edges; package-to-root, root-to-package, root-to-root, or top-level package-family dependencies; new compatibility-alias edges; new wildcard exports, unregistered packages, and new or enlarged package or combined strongly connected components. Removing a violation and refreshing the baseline makes that improvement permanent.
