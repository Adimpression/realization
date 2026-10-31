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

## Root Module Ownership

Every repository-root Python module has one explicit responsibility. Status is orthogonal: an entrypoint or compatibility facade retains the owner of the behavior it exposes.

| Module | Owner | Status |
| --- | --- | --- |
| `SEMANTIC_RELATION_VALIDATION` | `validation_trial` | `validation` |
| `TRIAL_DOMAIN_VALIDATION` | `validation_trial` | `validation` |
| `applied_theory_types` | `semantic_model` | `compatibility_facade` |
| `approval_governance` | `governance` | `compatibility_facade` |
| `args` | `entry_exchange` | `entrypoint` |
| `blend_context` | `blend` | `compatibility_facade` |
| `blend_operator` | `blend` | `compatibility_facade` |
| `blend_operator_store` | `blend` | `compatibility_facade` |
| `blend_session` | `blend` | `compatibility_facade` |
| `blend_workflow_execution` | `blend` | `compatibility_facade` |
| `blend_workflow_models` | `blend` | `compatibility_facade` |
| `blend_world_models` | `blend` | `compatibility_facade` |
| `controller_entrypoint_binding` | `entry_exchange` | `compatibility_facade` |
| `controller_entrypoints` | `entry_exchange` | `entrypoint` |
| `controller_runtime` | `controller` | `compatibility_facade` |
| `data_governance` | `governance` | `compatibility_facade` |
| `decision_review` | `subject_domain` | `compatibility_facade` |
| `decision_review_constructs` | `subject_domain` | `compatibility_facade` |
| `decision_review_models` | `subject_domain` | `compatibility_facade` |
| `execution_framework_primitives` | `runtime_execution` | `compatibility_facade` |
| `execution_frameworks` | `runtime_execution` | `compatibility_facade` |
| `external_markdown_learning_pipeline` | `entry_exchange` | `compatibility_facade` |
| `fence_extraction_strategy` | `runtime_execution` | `compatibility_facade` |
| `governance_inventory` | `controller` | `compatibility_facade` |
| `governed_skill_installation` | `governance` | `entrypoint` |
| `host_mediation` | `runtime_execution` | `compatibility_facade` |
| `itemize` | `subject_domain` | `compatibility_facade` |
| `itemize_models` | `subject_domain` | `compatibility_facade` |
| `learning_context` | `entry_exchange` | `compatibility_facade` |
| `learning_context_paths` | `subject_domain` | `compatibility_facade` |
| `main` | `entry_exchange` | `compatibility_facade`, `entrypoint` |
| `markdown_ir` | `subject_domain` | `compatibility_facade` |
| `normalize` | `compatibility` | `compatibility_facade` |
| `pure_theory_types` | `semantic_model` | `compatibility_facade` |
| `python_skill_host` | `runtime_execution` | `compatibility_facade` |
| `replay_verifier` | `governance` | `entrypoint` |
| `review_composition` | `subject_domain` | `compatibility_facade` |
| `runtime_controller_api` | `entry_exchange` | `compatibility_facade` |
| `skill_boundary_normalization` | `portable_skills` | `compatibility_facade` |
| `skill_composition` | `portable_skills` | `compatibility_facade` |
| `skill_governance` | `governance` | `compatibility_facade` |
| `skill_governance_primitives` | `governance` | `compatibility_facade` |
| `skill_invocation_contract` | `portable_skills` | `compatibility_facade` |
| `skill_ir` | `portable_skills` | `compatibility_facade` |
| `skill_leaf_types` | `portable_skills` | `compatibility_facade` |
| `skill_lifecycle` | `governance` | `compatibility_facade` |
| `skill_path_notation` | `portable_skills` | `compatibility_facade` |
| `skill_safety_governance` | `governance` | `compatibility_facade` |
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
| `controller` | `entry_exchange` | no |
| `entry_exchange` | `controller` | yes |
| `entry_exchange` | `governance` | yes |
| `subject_domain` | `entry_exchange` | no |

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

## Cycles

No package cycles were found.

## Compatibility Alias Edges

These edges exist only to preserve historical import paths. They are excluded from the canonical cycle calculation, remain visible here, and are still ratcheted against expansion.

| Source | Target | Evidence |
| --- | --- | --- |
| `foundation_events` | `runtime_core` | `workstation/foundation_events/src/workstation/foundation/events/subscriber_controllers.py` |
| `foundation_host` | `runtime_core` | `workstation/foundation_host/src/workstation/foundation/host/llm_driver.py` |
| `foundation_host` | `subject_service` | `workstation/foundation_host/src/workstation/foundation/host/client_sessions.py`, `workstation/foundation_host/src/workstation/foundation/host/learning_capture.py` |
| `shell_core` | `contracts` | `workstation/shell_core/src/workstation/shell/core/shell_prompt_routing.py` |

## Combined Graph Metrics

| Metric | Count |
| --- | ---: |
| Nodes | 86 |
| Edges | 222 |
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
| `root_to_component` | `applied_theory_types` | `core_semantics` | `dto_constants` |
| `root_to_component` | `approval_governance` | `core_governance` | `compatibility` |
| `root_to_component` | `approval_governance` | `core_semantics` | `compatibility` |
| `root_to_component` | `args` | `app_cli` | `orchestration` |
| `root_to_component` | `args` | `core_engine` | `orchestration` |
| `root_to_component` | `blend_context` | `blend` | `compatibility` |
| `root_to_component` | `blend_context` | `runtime_core` | `compatibility` |
| `root_to_component` | `blend_operator` | `blend` | `compatibility` |
| `root_to_component` | `blend_operator_store` | `blend_application` | `compatibility` |
| `root_to_component` | `blend_session` | `blend` | `compatibility` |
| `root_to_component` | `blend_session` | `runtime_core` | `compatibility` |
| `root_to_component` | `blend_workflow_execution` | `blend_application` | `compatibility` |
| `root_to_component` | `blend_workflow_models` | `blend` | `compatibility` |
| `root_to_component` | `blend_world_models` | `blend` | `compatibility` |
| `root_to_component` | `controller_entrypoint_binding` | `core_engine` | `compatibility` |
| `root_to_component` | `controller_entrypoints` | `app_cli` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `core_engine` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `core_semantics` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `exchange` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `governed_core` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `host_interaction` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `validation` | `orchestration` |
| `root_to_component` | `controller_runtime` | `core_engine` | `compatibility` |
| `root_to_component` | `controller_runtime` | `exchange` | `compatibility` |
| `root_to_component` | `data_governance` | `core_governance` | `compatibility` |
| `root_to_component` | `decision_review` | `subject_core` | `orchestration` |
| `root_to_component` | `decision_review_constructs` | `subject_core` | `orchestration` |
| `root_to_component` | `decision_review_models` | `core_semantics` | `dto_constants` |
| `root_to_component` | `execution_framework_primitives` | `governed_core` | `orchestration` |
| `root_to_component` | `execution_frameworks` | `governed_core` | `orchestration` |
| `root_to_component` | `external_markdown_learning_pipeline` | `exchange` | `compatibility` |
| `root_to_component` | `fence_extraction_strategy` | `governed_core` | `orchestration` |
| `root_to_component` | `governance_inventory` | `core_engine` | `orchestration` |
| `root_to_component` | `governed_skill_installation` | `core_engine` | `orchestration` |
| `root_to_component` | `governed_skill_installation` | `core_governance` | `orchestration` |
| `root_to_component` | `governed_skill_installation` | `exchange` | `orchestration` |
| `root_to_component` | `governed_skill_installation` | `skill_application` | `orchestration` |
| `root_to_component` | `governed_skill_installation` | `skill_semantics` | `orchestration` |
| `root_to_component` | `host_mediation` | `core_engine` | `compatibility` |
| `root_to_component` | `itemize` | `core_semantics` | `orchestration` |
| `root_to_component` | `itemize` | `subject_core` | `orchestration` |
| `root_to_component` | `itemize_models` | `core_semantics` | `dto_constants` |
| `root_to_component` | `learning_context` | `exchange` | `orchestration` |
| `root_to_component` | `learning_context_paths` | `subject_core` | `orchestration` |
| `root_to_component` | `markdown_ir` | `core_semantics` | `orchestration` |
| `root_to_component` | `normalize` | `core_engine` | `orchestration` |
| `root_to_component` | `normalize` | `core_semantics` | `orchestration` |
| `root_to_component` | `pure_theory_types` | `core_semantics` | `compatibility` |
| `root_to_component` | `python_skill_host` | `governed_core` | `orchestration` |
| `root_to_component` | `replay_verifier` | `core_engine` | `orchestration` |
| `root_to_component` | `replay_verifier` | `core_governance` | `orchestration` |
| `root_to_component` | `replay_verifier` | `core_semantics` | `orchestration` |
| `root_to_component` | `replay_verifier` | `exchange` | `orchestration` |
| `root_to_component` | `replay_verifier` | `governed_core` | `orchestration` |
| `root_to_component` | `replay_verifier` | `skill_semantics` | `orchestration` |
| `root_to_component` | `review_composition` | `subject_core` | `compatibility` |
| `root_to_component` | `runtime_controller_api` | `app_cli` | `compatibility` |
| `root_to_component` | `skill_boundary_normalization` | `skill_application` | `compatibility` |
| `root_to_component` | `skill_composition` | `skill_application` | `compatibility` |
| `root_to_component` | `skill_governance` | `core_engine` | `compatibility` |
| `root_to_component` | `skill_governance_primitives` | `core_governance` | `compatibility` |
| `root_to_component` | `skill_invocation_contract` | `skill_semantics` | `compatibility` |
| `root_to_component` | `skill_invocation_contract` | `skills_core` | `compatibility` |
| `root_to_component` | `skill_ir` | `skill_application` | `compatibility` |
| `root_to_component` | `skill_leaf_types` | `skill_semantics` | `compatibility` |
| `root_to_component` | `skill_lifecycle` | `core_governance` | `compatibility` |
| `root_to_component` | `skill_path_notation` | `skill_semantics` | `compatibility` |
| `root_to_component` | `skill_safety_governance` | `core_governance` | `compatibility` |
| `root_to_component` | `skill_safety_governance` | `core_semantics` | `compatibility` |
| `root_to_component` | `tablet_safety_validation` | `validation` | `orchestration` |
| `root_to_component` | `title_depth_learning_validation` | `validation` | `orchestration` |

## Root-Module Dependencies

No workspace package imports a root application module.

## Root-to-Component Dependencies

- `SEMANTIC_RELATION_VALIDATION` -> `core_engine` (`SEMANTIC_RELATION_VALIDATION.py`)
- `TRIAL_DOMAIN_VALIDATION` -> `validation` (`TRIAL_DOMAIN_VALIDATION.py`)
- `applied_theory_types` -> `core_semantics` (`applied_theory_types.py`)
- `approval_governance` -> `core_governance` (`approval_governance.py`)
- `approval_governance` -> `core_semantics` (`approval_governance.py`)
- `args` -> `app_cli` (`args.py`)
- `args` -> `core_engine` (`args.py`)
- `blend_context` -> `blend` (`blend_context.py`)
- `blend_context` -> `runtime_core` (`blend_context.py`)
- `blend_operator` -> `blend` (`blend_operator.py`)
- `blend_operator_store` -> `blend_application` (`blend_operator_store.py`)
- `blend_session` -> `blend` (`blend_session.py`)
- `blend_session` -> `runtime_core` (`blend_session.py`)
- `blend_workflow_execution` -> `blend_application` (`blend_workflow_execution.py`)
- `blend_workflow_models` -> `blend` (`blend_workflow_models.py`)
- `blend_world_models` -> `blend` (`blend_world_models.py`)
- `controller_entrypoint_binding` -> `core_engine` (`controller_entrypoint_binding.py`)
- `controller_entrypoints` -> `app_cli` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `core_engine` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `core_semantics` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `exchange` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `governed_core` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `host_interaction` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `validation` (`controller_entrypoints.py`)
- `controller_runtime` -> `core_engine` (`controller_runtime.py`)
- `controller_runtime` -> `exchange` (`controller_runtime.py`)
- `data_governance` -> `core_governance` (`data_governance.py`)
- `decision_review` -> `subject_core` (`decision_review.py`)
- `decision_review_constructs` -> `subject_core` (`decision_review_constructs.py`)
- `decision_review_models` -> `core_semantics` (`decision_review_models.py`)
- `execution_framework_primitives` -> `governed_core` (`execution_framework_primitives.py`)
- `execution_frameworks` -> `governed_core` (`execution_frameworks.py`)
- `external_markdown_learning_pipeline` -> `exchange` (`external_markdown_learning_pipeline.py`)
- `fence_extraction_strategy` -> `governed_core` (`fence_extraction_strategy.py`)
- `governance_inventory` -> `core_engine` (`governance_inventory.py`)
- `governed_skill_installation` -> `core_engine` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `core_governance` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `exchange` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `skill_application` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `skill_semantics` (`governed_skill_installation.py`)
- `host_mediation` -> `core_engine` (`host_mediation.py`)
- `itemize` -> `core_semantics` (`itemize.py`)
- `itemize` -> `subject_core` (`itemize.py`)
- `itemize_models` -> `core_semantics` (`itemize_models.py`)
- `learning_context` -> `exchange` (`learning_context.py`)
- `learning_context_paths` -> `subject_core` (`learning_context_paths.py`)
- `markdown_ir` -> `core_semantics` (`markdown_ir.py`)
- `normalize` -> `core_engine` (`normalize.py`)
- `normalize` -> `core_semantics` (`normalize.py`)
- `pure_theory_types` -> `core_semantics` (`pure_theory_types.py`)
- `python_skill_host` -> `governed_core` (`python_skill_host.py`)
- `replay_verifier` -> `core_engine` (`replay_verifier.py`)
- `replay_verifier` -> `core_governance` (`replay_verifier.py`)
- `replay_verifier` -> `core_semantics` (`replay_verifier.py`)
- `replay_verifier` -> `exchange` (`replay_verifier.py`)
- `replay_verifier` -> `governed_core` (`replay_verifier.py`)
- `replay_verifier` -> `skill_semantics` (`replay_verifier.py`)
- `review_composition` -> `subject_core` (`review_composition.py`)
- `runtime_controller_api` -> `app_cli` (`runtime_controller_api.py`)
- `skill_boundary_normalization` -> `skill_application` (`skill_boundary_normalization.py`)
- `skill_composition` -> `skill_application` (`skill_composition.py`)
- `skill_governance` -> `core_engine` (`skill_governance.py`)
- `skill_governance_primitives` -> `core_governance` (`skill_governance_primitives.py`)
- `skill_invocation_contract` -> `skill_semantics` (`skill_invocation_contract.py`)
- `skill_invocation_contract` -> `skills_core` (`skill_invocation_contract.py`)
- `skill_ir` -> `skill_application` (`skill_ir.py`)
- `skill_leaf_types` -> `skill_semantics` (`skill_leaf_types.py`)
- `skill_lifecycle` -> `core_governance` (`skill_lifecycle.py`)
- `skill_path_notation` -> `skill_semantics` (`skill_path_notation.py`)
- `skill_safety_governance` -> `core_governance` (`skill_safety_governance.py`)
- `skill_safety_governance` -> `core_semantics` (`skill_safety_governance.py`)
- `tablet_safety_validation` -> `validation` (`tablet_safety_validation.py`)
- `title_depth_learning_validation` -> `validation` (`title_depth_learning_validation.py`)

## Root-to-Root Dependencies

- `controller_entrypoints` -> `args` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `governed_skill_installation` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `replay_verifier` (`controller_entrypoints.py`)
- `controller_runtime` -> `args` (`controller_runtime.py`)
- `itemize` -> `runtime_controller_api` (`itemize.py`)
- `main` -> `controller_entrypoint_binding` (`main.py`)
- `main` -> `controller_entrypoints` (`main.py`)
- `main` -> `controller_runtime` (`main.py`)

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

- `data_governance.py` imports `*` from `realized_core_governance.data` (line 10)
- `workstation/app_cli/src/workstation/app/cli/__init__.py` imports `*` from `workstation.app.cli.cli` (line 1)
- `workstation/foundation_models/src/workstation/foundation/models/__init__.py` imports `*` from `workstation.foundation.models.models` (line 1)
- `workstation/foundation_projections/src/workstation/foundation/projections/__init__.py` imports `*` from `workstation.foundation.projections.projection_models` (line 1)
- `workstation/skills_builtin/src/workstation/skills/builtin/__init__.py` imports `*` from `workstation.skills.builtin.builtin_skills` (line 1)
- `workstation/subject_textual/src/workstation/subject/textual/__init__.py` imports `*` from `workstation.subject.textual.subject_workflow_textual_backend` (line 1)
- `workstation/ui_textual/src/workstation/ui/textual/__init__.py` imports `*` from `workstation.ui.textual.chat_ui` (line 1)

## Ratchet Rules

The checked-in baseline records the facts above. Declared compatibility aliases preserve historical ABI; every measured category remains closed to expansion. The checker fails for unowned, multiply owned, or stale root modules or package families; changed root ownership; package or canonical-root imports of compatibility facades; new dependency edges; undeclared or forbidden edges; package-to-root, root-to-package, root-to-root, or top-level package-family dependencies; new compatibility-alias edges; new wildcard exports, unregistered packages, and new or enlarged package or combined strongly connected components. Removing a violation and refreshing the baseline makes that improvement permanent.
