# Repository Dependency Report

This report is generated deterministically by `scripts/check_architecture_boundaries.py`. It records architecture facts; it does not import or execute production code.

## Components

| Component | Layer | Distribution | Public module prefix |
| --- | --- | --- | --- |
| `app_cli` | `entry` | `realized-workstation-app-cli` | `workstation.app.cli` |
| `contracts` | `contracts` | `realized-workstation-contracts` | `workstation.contracts` |
| `core_app` | `entry` | `realized-core` | `realized_core` |
| `core_conversation` | `workstation` | `realized-core-conversation` | `realized_core_conversation` |
| `core_engine` | `controller` | `realized-core-engine` | `realized_core_engine` |
| `core_llm` | `llm` | `realized-core-llm` | `realized_core_llm` |
| `foundation_events` | `foundation` | `realized-workstation-foundation-events` | `workstation.foundation.events` |
| `foundation_host` | `foundation` | `realized-workstation-foundation-host` | `workstation.foundation.host` |
| `foundation_models` | `foundation` | `realized-workstation-foundation-models` | `workstation.foundation.models` |
| `foundation_projections` | `foundation` | `realized-workstation-foundation-projections` | `workstation.foundation.projections` |
| `governed_core` | `core` | `realized-core-runtime` | `realized_core_runtime` |
| `grpc_definitions` | `exchange_contracts` | `realized-workstation-grpc-definitions` | `workstation.grpc.definitions` |
| `grpc_implementation` | `exchange_adapters` | `realized-workstation-grpc-implementation` | `workstation.grpc.implementation` |
| `namespace` | `namespace` | `realized-workstation` | `workstation` |
| `runtime_core` | `controller` | `realized-workstation-runtime-core` | `workstation.runtime.core` |
| `shell_core` | `workstation` | `realized-workstation-shell-core` | `workstation.shell.core` |
| `skills_builtin` | `skills` | `realized-workstation-skills-builtin` | `workstation.skills.builtin` |
| `skills_core` | `skills` | `realized-workstation-skills-core` | `workstation.skills.core` |
| `skills_planning` | `skills` | `realized-workstation-skills-planning` | `workstation.skills.planning` |
| `subject_core` | `governance` | `realized-workstation-subject-core` | `workstation.subject.core` |
| `subject_service` | `governance` | `realized-workstation-subject-service` | `workstation.subject.service` |
| `subject_textual` | `workstation_adapter` | `realized-workstation-subject-textual` | `workstation.subject.textual` |
| `ui_shared` | `workstation` | `realized-workstation-ui-shared` | `workstation.ui.shared` |
| `ui_textual` | `workstation_adapter` | `realized-workstation-ui-textual` | `workstation.ui.textual` |

## Dependency Edges

| Source | Target | Declared | Allowed by target policy | Evidence |
| --- | --- | --- | --- | --- |
| `app_cli` | `foundation_host` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `app_cli` | `grpc_implementation` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `app_cli` | `shell_core` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `app_cli` | `ui_shared` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `app_cli` | `ui_textual` | yes | yes | `workstation/app_cli/src/workstation/app/cli/cli.py` |
| `core_app` | `core_conversation` | yes | yes | `core_app/src/realized_core/chat.py`, `core_app/src/realized_core/conversation.py` |
| `core_app` | `core_engine` | yes | yes | `core_app/src/realized_core/cli.py` |
| `core_app` | `core_llm` | yes | yes | `core_app/src/realized_core/chat.py`, `core_app/src/realized_core/cli.py`, `core_app/src/realized_core/planning.py` |
| `core_conversation` | `core_engine` | yes | yes | `core_conversation/src/realized_core_conversation/contracts.py`, `core_conversation/src/realized_core_conversation/ports.py`, `core_conversation/src/realized_core_conversation/service.py` |
| `core_conversation` | `core_llm` | yes | yes | `core_conversation/src/realized_core_conversation/service.py` |
| `core_engine` | `governed_core` | yes | yes | `core_engine/src/realized_core_engine/__init__.py`, `core_engine/src/realized_core_engine/api.py`, `core_engine/src/realized_core_engine/canonical_reduction.py` (+3 more) |
| `foundation_events` | `contracts` | yes | yes | `workstation/foundation_events/src/workstation/foundation/events/event_bus.py` |
| `foundation_host` | `contracts` | yes | yes | `workstation/foundation_host/src/workstation/foundation/host/controller_runtime.py`, `workstation/foundation_host/src/workstation/foundation/host/subject_workflow.py` |
| `foundation_host` | `foundation_models` | yes | yes | `workstation/foundation_host/src/workstation/foundation/host/delegation.py`, `workstation/foundation_host/src/workstation/foundation/host/host_interaction.py`, `workstation/foundation_host/src/workstation/foundation/host/learning_capture.py` (+1 more) |
| `foundation_projections` | `contracts` | yes | yes | `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py` |
| `foundation_projections` | `foundation_models` | yes | yes | `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py` |
| `grpc_implementation` | `contracts` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_shell_grpc.py` |
| `grpc_implementation` | `foundation_events` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_bootstrap_grpc.py` (+1 more) |
| `grpc_implementation` | `grpc_definitions` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_bootstrap_grpc.py` (+2 more) |
| `grpc_implementation` | `runtime_core` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_grpc_host.py` |
| `grpc_implementation` | `shell_core` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_grpc_host.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_shell_grpc.py` |
| `grpc_implementation` | `subject_core` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py` |
| `grpc_implementation` | `subject_service` | yes | yes | `workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_grpc_host.py` |
| `runtime_core` | `contracts` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py` |
| `runtime_core` | `foundation_events` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py` (+2 more) |
| `runtime_core` | `foundation_host` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py` |
| `runtime_core` | `foundation_models` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py` (+2 more) |
| `runtime_core` | `foundation_projections` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py` (+1 more) |
| `runtime_core` | `skills_core` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py` (+2 more) |
| `runtime_core` | `skills_planning` | yes | yes | `workstation/runtime_core/src/workstation/runtime/core/session.py` |
| `shell_core` | `contracts` | yes | yes | `workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_client.py` |
| `shell_core` | `core_conversation` | yes | yes | `workstation/shell_core/src/workstation/shell/core/governed_conversation.py` |
| `shell_core` | `core_llm` | yes | yes | `workstation/shell_core/src/workstation/shell/core/governed_conversation.py` |
| `shell_core` | `foundation_events` | yes | yes | `workstation/shell_core/src/workstation/shell/core/application_facade.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py` |
| `shell_core` | `foundation_models` | yes | yes | `workstation/shell_core/src/workstation/shell/core/application_facade.py` |
| `shell_core` | `foundation_projections` | yes | yes | `workstation/shell_core/src/workstation/shell/core/workstation_shell_backend.py` |
| `shell_core` | `grpc_definitions` | yes | yes | `workstation/shell_core/src/workstation/shell/core/workstation_shell_client.py` |
| `shell_core` | `runtime_core` | yes | yes | `workstation/shell_core/src/workstation/shell/core/application_facade.py`, `workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/trial_validation.py` (+2 more) |
| `shell_core` | `skills_core` | yes | yes | `workstation/shell_core/src/workstation/shell/core/trial_validation.py` |
| `shell_core` | `subject_service` | yes | yes | `workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py` |
| `skills_core` | `contracts` | yes | yes | `workstation/skills_core/src/workstation/skills/core/direct_composition.py` |
| `skills_core` | `foundation_host` | yes | yes | `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py` |
| `skills_core` | `foundation_models` | yes | yes | `workstation/skills_core/src/workstation/skills/core/direct_composition.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py` |
| `skills_core` | `skills_builtin` | yes | yes | `workstation/skills_core/src/workstation/skills/core/skill_invocation.py` |
| `skills_planning` | `contracts` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `foundation_host` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_home.py` |
| `skills_planning` | `foundation_models` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `skills_planning` | `skills_core` | yes | yes | `workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py` |
| `subject_core` | `contracts` | yes | yes | `workstation/subject_core/src/workstation/subject/core/subject_workflow.py` |
| `subject_core` | `foundation_host` | yes | yes | `workstation/subject_core/src/workstation/subject/core/subject_workflow.py` |
| `subject_core` | `runtime_core` | yes | yes | `workstation/subject_core/src/workstation/subject/core/subject_workflow.py` |
| `subject_service` | `contracts` | yes | yes | `workstation/subject_service/src/workstation/subject/service/subject_workflow_api.py`, `workstation/subject_service/src/workstation/subject/service/subject_workflow_client.py` |
| `subject_service` | `foundation_events` | yes | yes | `workstation/subject_service/src/workstation/subject/service/subject_workflow_api.py` |
| `subject_service` | `grpc_definitions` | yes | yes | `workstation/subject_service/src/workstation/subject/service/subject_workflow_client.py` |
| `subject_service` | `subject_core` | yes | yes | `workstation/subject_service/src/workstation/subject/service/client_sessions.py`, `workstation/subject_service/src/workstation/subject/service/subject_workflow_api.py`, `workstation/subject_service/src/workstation/subject/service/subject_workflow_client.py` |
| `subject_textual` | `contracts` | yes | yes | `workstation/subject_textual/src/workstation/subject/textual/application_facade.py`, `workstation/subject_textual/src/workstation/subject/textual/models.py`, `workstation/subject_textual/src/workstation/subject/textual/subject_workflow_textual_backend.py` |
| `ui_shared` | `foundation_projections` | yes | yes | `workstation/ui_shared/src/workstation/ui/shared/activity_view.py` |
| `ui_textual` | `contracts` | yes | yes | `workstation/ui_textual/src/workstation/ui/textual/chat_ui.py` |
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
| `foundation_host` | `subject_service` | `workstation/foundation_host/src/workstation/foundation/host/client_sessions.py` |
| `shell_core` | `contracts` | `workstation/shell_core/src/workstation/shell/core/shell_prompt_routing.py` |

## Combined Graph Metrics

| Metric | Count |
| --- | ---: |
| Nodes | 150 |
| Edges | 641 |
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
| `component_to_root` | `app_cli` | `host_interaction_receipts` | `orchestration` |
| `component_to_root` | `app_cli` | `semantic_text` | `pure_helper` |
| `component_to_root` | `core_engine` | `applied_theory_types` | `dto_constants` |
| `component_to_root` | `core_engine` | `args` | `orchestration` |
| `component_to_root` | `core_engine` | `controller_runtime` | `orchestration` |
| `component_to_root` | `core_engine` | `system_state` | `orchestration` |
| `component_to_root` | `core_engine` | `title_semantics` | `orchestration` |
| `component_to_root` | `foundation_events` | `host_interaction_receipts` | `orchestration` |
| `component_to_root` | `foundation_events` | `semantic_text` | `pure_helper` |
| `component_to_root` | `foundation_host` | `applied_theory_types` | `dto_constants` |
| `component_to_root` | `foundation_host` | `boundary` | `orchestration` |
| `component_to_root` | `foundation_host` | `gather_sources` | `orchestration` |
| `component_to_root` | `foundation_host` | `governance_inventory` | `orchestration` |
| `component_to_root` | `foundation_host` | `host_interaction_context` | `orchestration` |
| `component_to_root` | `foundation_host` | `host_interaction_delegation` | `orchestration` |
| `component_to_root` | `foundation_host` | `host_interaction_models` | `dto_constants` |
| `component_to_root` | `foundation_host` | `learning_context` | `orchestration` |
| `component_to_root` | `foundation_host` | `markdown_ir` | `orchestration` |
| `component_to_root` | `foundation_host` | `semantic_text` | `pure_helper` |
| `component_to_root` | `foundation_host` | `skill_schema_io` | `orchestration` |
| `component_to_root` | `foundation_projections` | `blend_workflow` | `orchestration` |
| `component_to_root` | `foundation_projections` | `semantic_text` | `pure_helper` |
| `component_to_root` | `grpc_implementation` | `semantic_text` | `pure_helper` |
| `component_to_root` | `runtime_core` | `applied_theory_types` | `dto_constants` |
| `component_to_root` | `runtime_core` | `blend_context` | `orchestration` |
| `component_to_root` | `runtime_core` | `blend_operator_store` | `persistence` |
| `component_to_root` | `runtime_core` | `blend_session` | `orchestration` |
| `component_to_root` | `runtime_core` | `blend_workflow` | `orchestration` |
| `component_to_root` | `runtime_core` | `blend_workflow_execution` | `orchestration` |
| `component_to_root` | `runtime_core` | `blend_workflow_store` | `persistence` |
| `component_to_root` | `runtime_core` | `blend_world` | `orchestration` |
| `component_to_root` | `runtime_core` | `blend_world_store` | `persistence` |
| `component_to_root` | `runtime_core` | `capability_runtime` | `orchestration` |
| `component_to_root` | `runtime_core` | `execution_frameworks` | `orchestration` |
| `component_to_root` | `runtime_core` | `gather_sources` | `orchestration` |
| `component_to_root` | `runtime_core` | `host_interaction_action_dispatch` | `orchestration` |
| `component_to_root` | `runtime_core` | `host_interaction_delegation` | `orchestration` |
| `component_to_root` | `runtime_core` | `host_interaction_models` | `dto_constants` |
| `component_to_root` | `runtime_core` | `host_interaction_receipts` | `orchestration` |
| `component_to_root` | `runtime_core` | `host_interaction_resolution` | `orchestration` |
| `component_to_root` | `runtime_core` | `learning_context` | `orchestration` |
| `component_to_root` | `runtime_core` | `semantic_text` | `pure_helper` |
| `component_to_root` | `runtime_core` | `skill_export_projection` | `orchestration` |
| `component_to_root` | `runtime_core` | `skill_governance` | `orchestration` |
| `component_to_root` | `runtime_core` | `skill_ir` | `dto_constants` |
| `component_to_root` | `runtime_core` | `skill_lifecycle` | `orchestration` |
| `component_to_root` | `runtime_core` | `skill_schema_io` | `orchestration` |
| `component_to_root` | `runtime_core` | `url_learning_capture` | `orchestration` |
| `component_to_root` | `shell_core` | `semantic_text` | `pure_helper` |
| `component_to_root` | `skills_builtin` | `applied_theory_types` | `dto_constants` |
| `component_to_root` | `skills_builtin` | `skill_schema_io` | `orchestration` |
| `component_to_root` | `skills_core` | `applied_theory_types` | `dto_constants` |
| `component_to_root` | `skills_core` | `capability_runtime` | `orchestration` |
| `component_to_root` | `skills_core` | `execution_frameworks` | `orchestration` |
| `component_to_root` | `skills_core` | `host_interaction_delegation` | `orchestration` |
| `component_to_root` | `skills_core` | `semantic_text` | `pure_helper` |
| `component_to_root` | `skills_core` | `side` | `orchestration` |
| `component_to_root` | `skills_core` | `skill_export_projection` | `orchestration` |
| `component_to_root` | `skills_core` | `skill_governance` | `orchestration` |
| `component_to_root` | `skills_core` | `skill_lifecycle` | `orchestration` |
| `component_to_root` | `skills_core` | `skill_schema_io` | `orchestration` |
| `component_to_root` | `skills_core` | `store` | `persistence` |
| `component_to_root` | `skills_planning` | `capability_runtime` | `orchestration` |
| `component_to_root` | `skills_planning` | `semantic_text` | `pure_helper` |
| `component_to_root` | `skills_planning` | `skill_composition` | `orchestration` |
| `component_to_root` | `skills_planning` | `skill_ir` | `dto_constants` |
| `component_to_root` | `skills_planning` | `skill_leaf_types` | `dto_constants` |
| `component_to_root` | `skills_planning` | `skill_path_notation` | `orchestration` |
| `component_to_root` | `skills_planning` | `store` | `persistence` |
| `component_to_root` | `subject_core` | `decision_review` | `orchestration` |
| `component_to_root` | `subject_core` | `decision_review_constructs` | `orchestration` |
| `component_to_root` | `subject_core` | `decision_review_policy` | `orchestration` |
| `component_to_root` | `subject_core` | `decision_review_projection` | `orchestration` |
| `component_to_root` | `subject_core` | `gather_sources` | `orchestration` |
| `component_to_root` | `subject_core` | `itemize` | `orchestration` |
| `component_to_root` | `subject_core` | `itemize_validation` | `orchestration` |
| `component_to_root` | `subject_core` | `learning_context` | `orchestration` |
| `component_to_root` | `subject_core` | `publication` | `orchestration` |
| `component_to_root` | `subject_core` | `publication_projection` | `orchestration` |
| `component_to_root` | `subject_core` | `review_composition` | `orchestration` |
| `component_to_root` | `subject_core` | `runtime_temp` | `orchestration` |
| `component_to_root` | `subject_core` | `semantic_text` | `pure_helper` |
| `component_to_root` | `subject_service` | `semantic_text` | `pure_helper` |
| `component_to_root` | `ui_shared` | `host_interaction_receipts` | `orchestration` |
| `component_to_root` | `ui_shared` | `semantic_text` | `pure_helper` |
| `component_to_root` | `ui_textual` | `semantic_text` | `pure_helper` |
| `root_to_component` | `blend_context` | `foundation_models` | `orchestration` |
| `root_to_component` | `blend_session` | `foundation_models` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `app_cli` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `contracts` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `core_engine` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `foundation_host` | `orchestration` |
| `root_to_component` | `controller_entrypoints` | `subject_service` | `orchestration` |
| `root_to_component` | `controller_runtime` | `governed_core` | `orchestration` |
| `root_to_component` | `execution_frameworks` | `governed_core` | `orchestration` |
| `root_to_component` | `governed_semantic_reduction_runtime` | `governed_core` | `orchestration` |
| `root_to_component` | `skill_invocation_contract` | `skills_core` | `compatibility` |

## Root-Module Dependencies

- `app_cli` -> `host_interaction_receipts` (`workstation/app_cli/src/workstation/app/cli/cli.py`)
- `app_cli` -> `semantic_text` (`workstation/app_cli/src/workstation/app/cli/cli.py`)
- `core_engine` -> `applied_theory_types` (`core_engine/src/realized_core_engine/canonical_reduction.py`)
- `core_engine` -> `args` (`core_engine/src/realized_core_engine/api.py`, `core_engine/src/realized_core_engine/canonical_reduction.py`, `core_engine/src/realized_core_engine/cli_support.py`)
- `core_engine` -> `controller_runtime` (`core_engine/src/realized_core_engine/api.py`, `core_engine/src/realized_core_engine/canonical_reduction.py`)
- `core_engine` -> `system_state` (`core_engine/src/realized_core_engine/api.py`, `core_engine/src/realized_core_engine/canonical_reduction.py`)
- `core_engine` -> `title_semantics` (`core_engine/src/realized_core_engine/api.py`, `core_engine/src/realized_core_engine/canonical_reduction.py`)
- `foundation_events` -> `host_interaction_receipts` (`workstation/foundation_events/src/workstation/foundation/events/event_bus.py`)
- `foundation_events` -> `semantic_text` (`workstation/foundation_events/src/workstation/foundation/events/event_bus.py`, `workstation/foundation_events/src/workstation/foundation/events/message_tracing.py`)
- `foundation_host` -> `applied_theory_types` (`workstation/foundation_host/src/workstation/foundation/host/delegation.py`)
- `foundation_host` -> `boundary` (`workstation/foundation_host/src/workstation/foundation/host/task_contract.py`)
- `foundation_host` -> `gather_sources` (`workstation/foundation_host/src/workstation/foundation/host/learning_capture.py`)
- `foundation_host` -> `governance_inventory` (`workstation/foundation_host/src/workstation/foundation/host/governance.py`)
- `foundation_host` -> `host_interaction_context` (`workstation/foundation_host/src/workstation/foundation/host/host_interaction.py`)
- `foundation_host` -> `host_interaction_delegation` (`workstation/foundation_host/src/workstation/foundation/host/delegation.py`)
- `foundation_host` -> `host_interaction_models` (`workstation/foundation_host/src/workstation/foundation/host/host_interaction.py`)
- `foundation_host` -> `learning_context` (`workstation/foundation_host/src/workstation/foundation/host/learning_capture.py`)
- `foundation_host` -> `markdown_ir` (`workstation/foundation_host/src/workstation/foundation/host/learning_capture.py`)
- `foundation_host` -> `semantic_text` (`workstation/foundation_host/src/workstation/foundation/host/governance.py`, `workstation/foundation_host/src/workstation/foundation/host/learning_capture.py`)
- `foundation_host` -> `skill_schema_io` (`workstation/foundation_host/src/workstation/foundation/host/governance.py`)
- `foundation_projections` -> `blend_workflow` (`workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py`)
- `foundation_projections` -> `semantic_text` (`workstation/foundation_projections/src/workstation/foundation/projections/activity_receipts.py`, `workstation/foundation_projections/src/workstation/foundation/projections/projection_models.py`)
- `grpc_implementation` -> `semantic_text` (`workstation/grpc_implementation/src/workstation/grpc/implementation/subject_workflow_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_assets_grpc.py`, `workstation/grpc_implementation/src/workstation/grpc/implementation/workstation_bootstrap_grpc.py`)
- `runtime_core` -> `applied_theory_types` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `blend_context` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `blend_operator_store` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `blend_session` (`workstation/runtime_core/src/workstation/runtime/core/session.py`)
- `runtime_core` -> `blend_workflow` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`)
- `runtime_core` -> `blend_workflow_execution` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`)
- `runtime_core` -> `blend_workflow_store` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `blend_world` (`workstation/runtime_core/src/workstation/runtime/core/session.py`)
- `runtime_core` -> `blend_world_store` (`workstation/runtime_core/src/workstation/runtime/core/session.py`)
- `runtime_core` -> `capability_runtime` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`)
- `runtime_core` -> `execution_frameworks` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `gather_sources` (`workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `host_interaction_action_dispatch` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`)
- `runtime_core` -> `host_interaction_delegation` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`)
- `runtime_core` -> `host_interaction_models` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`)
- `runtime_core` -> `host_interaction_receipts` (`workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `host_interaction_resolution` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`)
- `runtime_core` -> `learning_context` (`workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `semantic_text` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`, `workstation/runtime_core/src/workstation/runtime/core/llm_driver.py`, `workstation/runtime_core/src/workstation/runtime/core/projection_subscriber_controller.py`, `workstation/runtime_core/src/workstation/runtime/core/session.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `skill_export_projection` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/chat_commands.py`)
- `runtime_core` -> `skill_governance` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`)
- `runtime_core` -> `skill_ir` (`workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `skill_lifecycle` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`)
- `runtime_core` -> `skill_schema_io` (`workstation/runtime_core/src/workstation/runtime/core/capabilities.py`, `workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `runtime_core` -> `url_learning_capture` (`workstation/runtime_core/src/workstation/runtime/core/workstation_core.py`)
- `shell_core` -> `semantic_text` (`workstation/shell_core/src/workstation/shell/core/chat_shell.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_api.py`, `workstation/shell_core/src/workstation/shell/core/workstation_shell_client.py`)
- `skills_builtin` -> `applied_theory_types` (`workstation/skills_builtin/src/workstation/skills/builtin/builtin_skills.py`)
- `skills_builtin` -> `skill_schema_io` (`workstation/skills_builtin/src/workstation/skills/builtin/builtin_skills.py`)
- `skills_core` -> `applied_theory_types` (`workstation/skills_core/src/workstation/skills/core/invocation_contract.py`)
- `skills_core` -> `capability_runtime` (`workstation/skills_core/src/workstation/skills/core/invocation_contract.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`)
- `skills_core` -> `execution_frameworks` (`workstation/skills_core/src/workstation/skills/core/invocation_contract.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py`)
- `skills_core` -> `host_interaction_delegation` (`workstation/skills_core/src/workstation/skills/core/skill_invocation.py`)
- `skills_core` -> `semantic_text` (`workstation/skills_core/src/workstation/skills/core/direct_composition.py`, `workstation/skills_core/src/workstation/skills/core/invocation_contract.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py`)
- `skills_core` -> `side` (`workstation/skills_core/src/workstation/skills/core/skill_management.py`)
- `skills_core` -> `skill_export_projection` (`workstation/skills_core/src/workstation/skills/core/invocation_contract.py`, `workstation/skills_core/src/workstation/skills/core/skill_invocation.py`, `workstation/skills_core/src/workstation/skills/core/skill_management.py`)
- `skills_core` -> `skill_governance` (`workstation/skills_core/src/workstation/skills/core/skill_management.py`)
- `skills_core` -> `skill_lifecycle` (`workstation/skills_core/src/workstation/skills/core/skill_management.py`)
- `skills_core` -> `skill_schema_io` (`workstation/skills_core/src/workstation/skills/core/skill_management.py`)
- `skills_core` -> `store` (`workstation/skills_core/src/workstation/skills/core/skill_invocation.py`)
- `skills_planning` -> `capability_runtime` (`workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py`)
- `skills_planning` -> `semantic_text` (`workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py`)
- `skills_planning` -> `skill_composition` (`workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py`)
- `skills_planning` -> `skill_ir` (`workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py`)
- `skills_planning` -> `skill_leaf_types` (`workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py`)
- `skills_planning` -> `skill_path_notation` (`workstation/skills_planning/src/workstation/skills/planning/skill_composition_planning.py`)
- `skills_planning` -> `store` (`workstation/skills_planning/src/workstation/skills/planning/skill_home.py`)
- `subject_core` -> `decision_review` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `decision_review_constructs` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `decision_review_policy` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `decision_review_projection` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `gather_sources` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `itemize` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `itemize_validation` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `learning_context` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `publication` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `publication_projection` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `review_composition` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `runtime_temp` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_core` -> `semantic_text` (`workstation/subject_core/src/workstation/subject/core/subject_workflow.py`)
- `subject_service` -> `semantic_text` (`workstation/subject_service/src/workstation/subject/service/client_sessions.py`, `workstation/subject_service/src/workstation/subject/service/subject_workflow_api.py`, `workstation/subject_service/src/workstation/subject/service/subject_workflow_client.py`)
- `ui_shared` -> `host_interaction_receipts` (`workstation/ui_shared/src/workstation/ui/shared/activity_view.py`)
- `ui_shared` -> `semantic_text` (`workstation/ui_shared/src/workstation/ui/shared/activity_view.py`)
- `ui_textual` -> `semantic_text` (`workstation/ui_textual/src/workstation/ui/textual/chat_ui.py`)

## Root-to-Component Dependencies

- `blend_context` -> `foundation_models` (`blend_context.py`)
- `blend_session` -> `foundation_models` (`blend_session.py`)
- `controller_entrypoints` -> `app_cli` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `contracts` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `core_engine` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `foundation_host` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `subject_service` (`controller_entrypoints.py`)
- `controller_runtime` -> `governed_core` (`controller_runtime.py`)
- `execution_frameworks` -> `governed_core` (`execution_frameworks.py`)
- `governed_semantic_reduction_runtime` -> `governed_core` (`governed_semantic_reduction_runtime.py`)
- `skill_invocation_contract` -> `skills_core` (`skill_invocation_contract.py`)

## Root-to-Root Dependencies

- `SEMANTIC_RELATION_VALIDATION` -> `store` (`SEMANTIC_RELATION_VALIDATION.py`)
- `TRIAL_DOMAIN_VALIDATION` -> `validation_sqlite` (`TRIAL_DOMAIN_VALIDATION.py`)
- `applied_theory_primitives` -> `pure_theory_types` (`applied_theory_primitives.py`)
- `applied_theory_types` -> `applied_theory_primitives` (`applied_theory_types.py`)
- `applied_theory_types` -> `execution_framework_primitives` (`applied_theory_types.py`)
- `applied_theory_types` -> `normalization_primitives` (`applied_theory_types.py`)
- `approval_governance` -> `artifact_contracts` (`approval_governance.py`)
- `approval_governance` -> `semantic_text` (`approval_governance.py`)
- `approval_governance` -> `skill_governance_primitives` (`approval_governance.py`)
- `args` -> `execution_frameworks` (`args.py`)
- `args` -> `normalize` (`args.py`)
- `artifact` -> `applied_theory_types` (`artifact.py`)
- `artifact` -> `boundary` (`artifact.py`)
- `artifact` -> `fallback_not_generation` (`artifact.py`)
- `artifact` -> `normalize` (`artifact.py`)
- `artifact` -> `semantic_text` (`artifact.py`)
- `artifact_answer_resolution` -> `applied_theory_types` (`artifact_answer_resolution.py`)
- `artifact_answer_resolution` -> `prompt_directives` (`artifact_answer_resolution.py`)
- `blend_operator` -> `blend_context` (`blend_operator.py`)
- `blend_operator` -> `semantic_text` (`blend_operator.py`)
- `blend_operator_store` -> `blend_context` (`blend_operator_store.py`)
- `blend_operator_store` -> `blend_operator` (`blend_operator_store.py`)
- `blend_operator_store` -> `capability_runtime` (`blend_operator_store.py`)
- `blend_operator_store` -> `execution_frameworks` (`blend_operator_store.py`)
- `blend_operator_store` -> `semantic_text` (`blend_operator_store.py`)
- `blend_session` -> `blend_context` (`blend_session.py`)
- `blend_workflow` -> `blend_workflow_models` (`blend_workflow.py`)
- `blend_workflow` -> `blend_workflow_store` (`blend_workflow.py`)
- `blend_workflow` -> `semantic_text` (`blend_workflow.py`)
- `blend_workflow_execution` -> `applied_theory_types` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `blend_context` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `blend_operator` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `blend_operator_store` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `blend_workflow` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `blend_workflow_store` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `host_interaction_delegation` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `semantic_text` (`blend_workflow_execution.py`)
- `blend_workflow_execution` -> `skill_composition` (`blend_workflow_execution.py`)
- `blend_workflow_models` -> `semantic_text` (`blend_workflow_models.py`)
- `blend_workflow_store` -> `applied_theory_primitives` (`blend_workflow_store.py`)
- `blend_workflow_store` -> `blend_workflow_models` (`blend_workflow_store.py`)
- `blend_workflow_store` -> `semantic_text` (`blend_workflow_store.py`)
- `blend_world` -> `blend_world_models` (`blend_world.py`)
- `blend_world` -> `blend_world_store` (`blend_world.py`)
- `blend_world_store` -> `blend_world_models` (`blend_world_store.py`)
- `blend_world_store` -> `semantic_text` (`blend_world_store.py`)
- `boundary` -> `applied_theory_types` (`boundary.py`)
- `boundary` -> `normalization_primitives` (`boundary.py`)
- `capability_runtime` -> `applied_theory_types` (`capability_runtime.py`)
- `capability_runtime` -> `execution_framework_primitives` (`capability_runtime.py`)
- `capability_runtime` -> `host_abi` (`capability_runtime.py`)
- `capability_runtime` -> `semantic_text` (`capability_runtime.py`)
- `capability_runtime` -> `skill_governance` (`capability_runtime.py`)
- `constitutional_trace` -> `applied_theory_types` (`constitutional_trace.py`)
- `constitutional_trace` -> `host_abi` (`constitutional_trace.py`)
- `constitutional_trace` -> `system_state` (`constitutional_trace.py`)
- `controller_entrypoints` -> `args` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `controller_runtime` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `governed_skill_installation` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `replay_verifier` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `run_bundle_io` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `runtime_temp` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `side` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `skill_export_projection` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `skill_registry` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `system_state` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `title_semantics` (`controller_entrypoints.py`)
- `controller_entrypoints` -> `validation_ladder` (`controller_entrypoints.py`)
- `controller_governance_bridge` -> `applied_theory_types` (`controller_governance_bridge.py`)
- `controller_governance_bridge` -> `governance_inventory` (`controller_governance_bridge.py`)
- `controller_governance_bridge` -> `governed_skill_access` (`controller_governance_bridge.py`)
- `controller_runtime` -> `applied_theory_types` (`controller_runtime.py`)
- `controller_runtime` -> `args` (`controller_runtime.py`)
- `controller_runtime` -> `artifact` (`controller_runtime.py`)
- `controller_runtime` -> `artifact_answer_resolution` (`controller_runtime.py`)
- `controller_runtime` -> `boundary` (`controller_runtime.py`)
- `controller_runtime` -> `controller_entrypoint_binding` (`controller_runtime.py`)
- `controller_runtime` -> `controller_governance_bridge` (`controller_runtime.py`)
- `controller_runtime` -> `controller_runtime_binding` (`controller_runtime.py`)
- `controller_runtime` -> `direct_knowledge_reuse` (`controller_runtime.py`)
- `controller_runtime` -> `execution_frameworks` (`controller_runtime.py`)
- `controller_runtime` -> `external_markdown_learning_pipeline` (`controller_runtime.py`)
- `controller_runtime` -> `fallback_not_semantics` (`controller_runtime.py`)
- `controller_runtime` -> `governed_closure_and_commitment` (`controller_runtime.py`)
- `controller_runtime` -> `governed_prior_learning_reuse` (`controller_runtime.py`)
- `controller_runtime` -> `governed_semantic_reduction_runtime` (`controller_runtime.py`)
- `controller_runtime` -> `host_interaction_context` (`controller_runtime.py`)
- `controller_runtime` -> `host_mediation` (`controller_runtime.py`)
- `controller_runtime` -> `id_generation` (`controller_runtime.py`)
- `controller_runtime` -> `learn` (`controller_runtime.py`)
- `controller_runtime` -> `markdown_ir` (`controller_runtime.py`)
- `controller_runtime` -> `markdown_learning_artifact_semantics` (`controller_runtime.py`)
- `controller_runtime` -> `normalize` (`controller_runtime.py`)
- `controller_runtime` -> `prolog` (`controller_runtime.py`)
- `controller_runtime` -> `prompt_directives` (`controller_runtime.py`)
- `controller_runtime` -> `retrieval_ranking` (`controller_runtime.py`)
- `controller_runtime` -> `run_outcome_harvest_and_reporting` (`controller_runtime.py`)
- `controller_runtime` -> `semantic_prompt_posture` (`controller_runtime.py`)
- `controller_runtime` -> `semantic_text` (`controller_runtime.py`)
- `controller_runtime` -> `side` (`controller_runtime.py`)
- `controller_runtime` -> `store` (`controller_runtime.py`)
- `controller_runtime` -> `structured_learning_yaml` (`controller_runtime.py`)
- `controller_runtime` -> `supplement` (`controller_runtime.py`)
- `controller_runtime` -> `system_state` (`controller_runtime.py`)
- `controller_runtime` -> `title_semantics` (`controller_runtime.py`)
- `controller_runtime_binding` -> `system_state` (`controller_runtime_binding.py`)
- `data_governance` -> `semantic_text` (`data_governance.py`)
- `decision_review` -> `decision_review_models` (`decision_review.py`)
- `decision_review` -> `id_generation` (`decision_review.py`)
- `decision_review` -> `learning_context` (`decision_review.py`)
- `decision_review` -> `learning_context_paths` (`decision_review.py`)
- `decision_review` -> `review_composition` (`decision_review.py`)
- `decision_review` -> `semantic_text` (`decision_review.py`)
- `decision_review_constructs` -> `id_generation` (`decision_review_constructs.py`)
- `decision_review_constructs` -> `itemize` (`decision_review_constructs.py`)
- `decision_review_constructs` -> `learning_context` (`decision_review_constructs.py`)
- `decision_review_constructs` -> `semantic_text` (`decision_review_constructs.py`)
- `decision_review_models` -> `id_generation` (`decision_review_models.py`)
- `decision_review_models` -> `learning_context_paths` (`decision_review_models.py`)
- `decision_review_models` -> `semantic_text` (`decision_review_models.py`)
- `decision_review_policy` -> `learning_context_paths` (`decision_review_policy.py`)
- `decision_review_policy` -> `semantic_text` (`decision_review_policy.py`)
- `decision_review_projection` -> `decision_review_models` (`decision_review_projection.py`)
- `decision_review_projection` -> `decision_review_policy` (`decision_review_projection.py`)
- `decision_review_projection` -> `learning_context_paths` (`decision_review_projection.py`)
- `decision_review_projection` -> `semantic_text` (`decision_review_projection.py`)
- `direct_knowledge_reuse` -> `applied_theory_types` (`direct_knowledge_reuse.py`)
- `direct_knowledge_reuse` -> `prompt_directives` (`direct_knowledge_reuse.py`)
- `direct_knowledge_reuse` -> `retrieval_ranking` (`direct_knowledge_reuse.py`)
- `direct_knowledge_reuse` -> `semantic_prompt_posture` (`direct_knowledge_reuse.py`)
- `direct_knowledge_reuse` -> `semantic_text` (`direct_knowledge_reuse.py`)
- `direct_knowledge_reuse` -> `title_semantics` (`direct_knowledge_reuse.py`)
- `execution_frameworks` -> `applied_theory_types` (`execution_frameworks.py`)
- `execution_frameworks` -> `execution_framework_primitives` (`execution_frameworks.py`)
- `execution_frameworks` -> `fence_extraction_strategy` (`execution_frameworks.py`)
- `execution_frameworks` -> `host_abi` (`execution_frameworks.py`)
- `execution_frameworks` -> `python_skill_brokerization` (`execution_frameworks.py`)
- `execution_frameworks` -> `runtime_temp` (`execution_frameworks.py`)
- `execution_frameworks` -> `semantic_text` (`execution_frameworks.py`)
- `execution_frameworks` -> `wasm_skill_runtime` (`execution_frameworks.py`)
- `external_markdown_learning_pipeline` -> `applied_theory_types` (`external_markdown_learning_pipeline.py`)
- `external_markdown_learning_pipeline` -> `artifact` (`external_markdown_learning_pipeline.py`)
- `external_markdown_learning_pipeline` -> `execution_frameworks` (`external_markdown_learning_pipeline.py`)
- `external_markdown_learning_pipeline` -> `learning_context` (`external_markdown_learning_pipeline.py`)
- `external_markdown_learning_pipeline` -> `markdown_ir` (`external_markdown_learning_pipeline.py`)
- `external_markdown_learning_pipeline` -> `semantic_text` (`external_markdown_learning_pipeline.py`)
- `fallback_not_generation` -> `applied_theory_primitives` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `boundary` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `normalization_primitives` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `prolog` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `prompt_directives` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `semantic_prompt_posture` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `semantic_text` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `structured_learning_yaml` (`fallback_not_generation.py`)
- `fallback_not_generation` -> `title_semantics` (`fallback_not_generation.py`)
- `fallback_not_semantics` -> `fallback_not_generation` (`fallback_not_semantics.py`)
- `fallback_not_semantics` -> `not_elaboration_ranking` (`fallback_not_semantics.py`)
- `gather_sources` -> `learning_context_paths` (`gather_sources.py`)
- `gather_sources` -> `semantic_text` (`gather_sources.py`)
- `governance_inventory` -> `applied_theory_types` (`governance_inventory.py`)
- `governance_inventory` -> `approval_governance` (`governance_inventory.py`)
- `governance_inventory` -> `skill_governance` (`governance_inventory.py`)
- `governance_inventory` -> `skill_safety_governance` (`governance_inventory.py`)
- `governed_closure_and_commitment` -> `applied_theory_types` (`governed_closure_and_commitment.py`)
- `governed_closure_and_commitment` -> `normalize` (`governed_closure_and_commitment.py`)
- `governed_closure_and_commitment` -> `semantic_text` (`governed_closure_and_commitment.py`)
- `governed_closure_and_commitment` -> `title_semantics` (`governed_closure_and_commitment.py`)
- `governed_prior_learning_reuse` -> `applied_theory_types` (`governed_prior_learning_reuse.py`)
- `governed_prior_learning_reuse` -> `learn` (`governed_prior_learning_reuse.py`)
- `governed_prior_learning_reuse` -> `normalize` (`governed_prior_learning_reuse.py`)
- `governed_prior_learning_reuse` -> `prompt_directives` (`governed_prior_learning_reuse.py`)
- `governed_prior_learning_reuse` -> `retrieval_ranking` (`governed_prior_learning_reuse.py`)
- `governed_prior_learning_reuse` -> `semantic_prompt_posture` (`governed_prior_learning_reuse.py`)
- `governed_prior_learning_reuse` -> `semantic_text` (`governed_prior_learning_reuse.py`)
- `governed_prior_learning_reuse` -> `title_semantics` (`governed_prior_learning_reuse.py`)
- `governed_semantic_reduction_runtime` -> `applied_theory_types` (`governed_semantic_reduction_runtime.py`)
- `governed_semantic_reduction_runtime` -> `host_interaction_context` (`governed_semantic_reduction_runtime.py`)
- `governed_semantic_reduction_runtime` -> `normalize` (`governed_semantic_reduction_runtime.py`)
- `governed_semantic_reduction_runtime` -> `semantic_prompt_posture` (`governed_semantic_reduction_runtime.py`)
- `governed_semantic_reduction_runtime` -> `semantic_text` (`governed_semantic_reduction_runtime.py`)
- `governed_semantic_reduction_runtime` -> `system_state` (`governed_semantic_reduction_runtime.py`)
- `governed_semantic_reduction_runtime` -> `title_semantics` (`governed_semantic_reduction_runtime.py`)
- `governed_skill_access` -> `applied_theory_types` (`governed_skill_access.py`)
- `governed_skill_access` -> `approval_governance` (`governed_skill_access.py`)
- `governed_skill_access` -> `execution_frameworks` (`governed_skill_access.py`)
- `governed_skill_access` -> `governance_inventory` (`governed_skill_access.py`)
- `governed_skill_access` -> `skill_governance` (`governed_skill_access.py`)
- `governed_skill_access` -> `skill_lifecycle` (`governed_skill_access.py`)
- `governed_skill_access` -> `skill_safety_governance` (`governed_skill_access.py`)
- `governed_skill_installation` -> `execution_frameworks` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `governance_inventory` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `skill_compiler` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `skill_export_projection` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `skill_governance` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `skill_lifecycle` (`governed_skill_installation.py`)
- `governed_skill_installation` -> `skill_schema_io` (`governed_skill_installation.py`)
- `host_abi` -> `semantic_text` (`host_abi.py`)
- `host_brokers` -> `applied_theory_types` (`host_brokers.py`)
- `host_brokers` -> `controller_runtime_binding` (`host_brokers.py`)
- `host_brokers` -> `data_governance` (`host_brokers.py`)
- `host_brokers` -> `host_abi` (`host_brokers.py`)
- `host_brokers` -> `macos_host_brokers` (`host_brokers.py`)
- `host_brokers` -> `semantic_text` (`host_brokers.py`)
- `host_brokers` -> `skill_governance` (`host_brokers.py`)
- `host_brokers` -> `store` (`host_brokers.py`)
- `host_brokers` -> `virtual_mounts` (`host_brokers.py`)
- `host_interaction_action_dispatch` -> `host_interaction_actions` (`host_interaction_action_dispatch.py`)
- `host_interaction_action_dispatch` -> `host_interaction_models` (`host_interaction_action_dispatch.py`)
- `host_interaction_actions` -> `host_interaction_models` (`host_interaction_actions.py`)
- `host_interaction_actions` -> `host_interaction_resolution` (`host_interaction_actions.py`)
- `host_interaction_context` -> `host_interaction_models` (`host_interaction_context.py`)
- `host_interaction_context` -> `host_interaction_resolution` (`host_interaction_context.py`)
- `host_interaction_context` -> `semantic_text` (`host_interaction_context.py`)
- `host_interaction_delegation` -> `applied_theory_types` (`host_interaction_delegation.py`)
- `host_interaction_delegation` -> `host_interaction_models` (`host_interaction_delegation.py`)
- `host_interaction_delegation` -> `semantic_text` (`host_interaction_delegation.py`)
- `host_interaction_receipts` -> `applied_theory_primitives` (`host_interaction_receipts.py`)
- `host_interaction_resolution` -> `host_interaction_models` (`host_interaction_resolution.py`)
- `host_interaction_resolution` -> `semantic_text` (`host_interaction_resolution.py`)
- `host_mediation` -> `applied_theory_types` (`host_mediation.py`)
- `host_mediation` -> `capability_runtime` (`host_mediation.py`)
- `host_mediation` -> `execution_frameworks` (`host_mediation.py`)
- `host_mediation` -> `host_abi` (`host_mediation.py`)
- `host_mediation` -> `host_brokers` (`host_mediation.py`)
- `host_mediation` -> `host_interaction_context` (`host_mediation.py`)
- `host_mediation` -> `runtime_governance_context` (`host_mediation.py`)
- `host_mediation` -> `semantic_text` (`host_mediation.py`)
- `itemize` -> `applied_theory_types` (`itemize.py`)
- `itemize` -> `id_generation` (`itemize.py`)
- `itemize` -> `itemize_models` (`itemize.py`)
- `itemize` -> `learning_context` (`itemize.py`)
- `itemize` -> `markdown_ir` (`itemize.py`)
- `itemize` -> `runtime_controller_api` (`itemize.py`)
- `itemize` -> `semantic_text` (`itemize.py`)
- `itemize` -> `title_semantics` (`itemize.py`)
- `itemize_models` -> `learning_context_paths` (`itemize_models.py`)
- `itemize_models` -> `semantic_text` (`itemize_models.py`)
- `itemize_validation` -> `itemize_models` (`itemize_validation.py`)
- `itemize_validation` -> `semantic_text` (`itemize_validation.py`)
- `learning_context` -> `id_generation` (`learning_context.py`)
- `learning_context` -> `learning_context_paths` (`learning_context.py`)
- `learning_context` -> `learning_context_projection` (`learning_context.py`)
- `learning_context` -> `learning_context_skill_projection` (`learning_context.py`)
- `learning_context` -> `semantic_text` (`learning_context.py`)
- `learning_context_markdown` -> `learning_context` (`learning_context_markdown.py`)
- `learning_context_markdown` -> `markdown_ir` (`learning_context_markdown.py`)
- `learning_context_markdown` -> `semantic_text` (`learning_context_markdown.py`)
- `learning_context_paths` -> `id_generation` (`learning_context_paths.py`)
- `learning_context_paths` -> `semantic_text` (`learning_context_paths.py`)
- `learning_context_projection` -> `learning_context_skill_projection` (`learning_context_projection.py`)
- `learning_context_projection` -> `semantic_text` (`learning_context_projection.py`)
- `learning_context_skill_projection` -> `learning_context_paths` (`learning_context_skill_projection.py`)
- `learning_context_skill_projection` -> `semantic_text` (`learning_context_skill_projection.py`)
- `learning_context_skill_projection` -> `skill_compiler` (`learning_context_skill_projection.py`)
- `learning_context_skill_projection` -> `skill_export_projection` (`learning_context_skill_projection.py`)
- `main` -> `controller_entrypoint_binding` (`main.py`)
- `main` -> `controller_entrypoints` (`main.py`)
- `main` -> `controller_runtime` (`main.py`)
- `markdown_learning_artifact_semantics` -> `applied_theory_types` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `execution_frameworks` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `markdown_ir` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `normalize` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `prolog` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `retrieval_ranking` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `semantic_text` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `structured_learning_yaml` (`markdown_learning_artifact_semantics.py`)
- `markdown_learning_artifact_semantics` -> `title_semantics` (`markdown_learning_artifact_semantics.py`)
- `non_achievedness_normalization` -> `applied_theory_primitives` (`non_achievedness_normalization.py`)
- `non_achievedness_normalization` -> `boundary` (`non_achievedness_normalization.py`)
- `non_achievedness_normalization` -> `normalization_primitives` (`non_achievedness_normalization.py`)
- `non_achievedness_normalization` -> `normalization_runtime_dependencies` (`non_achievedness_normalization.py`)
- `normalization_primitives` -> `applied_theory_primitives` (`normalization_primitives.py`)
- `normalization_primitives` -> `semantic_text` (`normalization_primitives.py`)
- `normalization_runtime_dependencies` -> `fallback_not_generation` (`normalization_runtime_dependencies.py`)
- `normalization_runtime_dependencies` -> `prolog` (`normalization_runtime_dependencies.py`)
- `normalization_runtime_dependencies` -> `semantic_text` (`normalization_runtime_dependencies.py`)
- `normalization_runtime_dependencies` -> `structured_learning_yaml` (`normalization_runtime_dependencies.py`)
- `normalization_runtime_dependencies` -> `title_semantics` (`normalization_runtime_dependencies.py`)
- `normalize` -> `non_achievedness_normalization` (`normalize.py`)
- `normalize` -> `normalization_primitives` (`normalize.py`)
- `normalize` -> `semantic_text` (`normalize.py`)
- `not_elaboration_ranking` -> `applied_theory_primitives` (`not_elaboration_ranking.py`)
- `not_elaboration_ranking` -> `artifact` (`not_elaboration_ranking.py`)
- `not_elaboration_ranking` -> `fallback_not_generation` (`not_elaboration_ranking.py`)
- `not_elaboration_ranking` -> `normalization_primitives` (`not_elaboration_ranking.py`)
- `not_elaboration_ranking` -> `retrieval_ranking` (`not_elaboration_ranking.py`)
- `not_elaboration_ranking` -> `semantic_text` (`not_elaboration_ranking.py`)
- `not_elaboration_ranking` -> `title_semantics` (`not_elaboration_ranking.py`)
- `prompt_directives` -> `learn` (`prompt_directives.py`)
- `publication` -> `id_generation` (`publication.py`)
- `publication` -> `semantic_text` (`publication.py`)
- `publication_projection` -> `decision_review` (`publication_projection.py`)
- `publication_projection` -> `decision_review_policy` (`publication_projection.py`)
- `publication_projection` -> `decision_review_projection` (`publication_projection.py`)
- `publication_projection` -> `learning_context` (`publication_projection.py`)
- `publication_projection` -> `publication` (`publication_projection.py`)
- `publication_projection` -> `publication_render` (`publication_projection.py`)
- `publication_projection` -> `publication_validation` (`publication_projection.py`)
- `publication_projection` -> `review_composition` (`publication_projection.py`)
- `publication_projection` -> `semantic_text` (`publication_projection.py`)
- `publication_render` -> `publication` (`publication_render.py`)
- `publication_render` -> `runtime_temp` (`publication_render.py`)
- `publication_render` -> `semantic_text` (`publication_render.py`)
- `publication_validation` -> `publication` (`publication_validation.py`)
- `publication_validation` -> `semantic_text` (`publication_validation.py`)
- `python_skill_brokerization` -> `semantic_text` (`python_skill_brokerization.py`)
- `python_skill_host` -> `capability_runtime` (`python_skill_host.py`)
- `python_skill_host` -> `host_abi` (`python_skill_host.py`)
- `python_skill_host` -> `host_brokers` (`python_skill_host.py`)
- `python_skill_host` -> `semantic_text` (`python_skill_host.py`)
- `python_skill_host` -> `skill_governance` (`python_skill_host.py`)
- `replay_verifier` -> `applied_theory_types` (`replay_verifier.py`)
- `replay_verifier` -> `constitutional_trace` (`replay_verifier.py`)
- `replay_verifier` -> `execution_frameworks` (`replay_verifier.py`)
- `replay_verifier` -> `governance_inventory` (`replay_verifier.py`)
- `replay_verifier` -> `run_bundle_io` (`replay_verifier.py`)
- `replay_verifier` -> `runtime_controller_api` (`replay_verifier.py`)
- `replay_verifier` -> `runtime_temp` (`replay_verifier.py`)
- `replay_verifier` -> `skill_governance` (`replay_verifier.py`)
- `replay_verifier` -> `skill_lifecycle` (`replay_verifier.py`)
- `replay_verifier` -> `skill_schema_io` (`replay_verifier.py`)
- `replay_verifier` -> `store` (`replay_verifier.py`)
- `replay_verifier` -> `system_state` (`replay_verifier.py`)
- `retrieval_ranking` -> `learn` (`retrieval_ranking.py`)
- `retrieval_ranking` -> `prolog` (`retrieval_ranking.py`)
- `retrieval_ranking` -> `prompt_directives` (`retrieval_ranking.py`)
- `retrieval_ranking` -> `semantic_text` (`retrieval_ranking.py`)
- `retrieval_ranking` -> `title_semantics` (`retrieval_ranking.py`)
- `review_composition` -> `id_generation` (`review_composition.py`)
- `review_composition` -> `itemize` (`review_composition.py`)
- `review_composition` -> `learning_context` (`review_composition.py`)
- `review_composition` -> `semantic_text` (`review_composition.py`)
- `run_bundle_io` -> `applied_theory_types` (`run_bundle_io.py`)
- `run_bundle_io` -> `approval_governance` (`run_bundle_io.py`)
- `run_bundle_io` -> `artifact` (`run_bundle_io.py`)
- `run_bundle_io` -> `constitutional_trace` (`run_bundle_io.py`)
- `run_bundle_io` -> `host_abi` (`run_bundle_io.py`)
- `run_bundle_io` -> `skill_export_projection` (`run_bundle_io.py`)
- `run_bundle_io` -> `skill_governance` (`run_bundle_io.py`)
- `run_bundle_io` -> `skill_registry` (`run_bundle_io.py`)
- `run_bundle_io` -> `skill_safety_governance` (`run_bundle_io.py`)
- `run_bundle_io` -> `skill_schema_io` (`run_bundle_io.py`)
- `run_bundle_io` -> `system_state` (`run_bundle_io.py`)
- `run_outcome_harvest_and_reporting` -> `applied_theory_types` (`run_outcome_harvest_and_reporting.py`)
- `run_outcome_harvest_and_reporting` -> `normalize` (`run_outcome_harvest_and_reporting.py`)
- `runtime_controller_api` -> `controller_runtime` (`runtime_controller_api.py`)
- `runtime_controller_api` -> `learning_context` (`runtime_controller_api.py`)
- `runtime_controller_api` -> `learning_context_skill_projection` (`runtime_controller_api.py`)
- `runtime_controller_api` -> `semantic_text` (`runtime_controller_api.py`)
- `runtime_controller_api` -> `skill_schema_io` (`runtime_controller_api.py`)
- `runtime_controller_api` -> `system_state` (`runtime_controller_api.py`)
- `runtime_governance_context` -> `applied_theory_types` (`runtime_governance_context.py`)
- `runtime_governance_context` -> `capability_runtime` (`runtime_governance_context.py`)
- `runtime_governance_context` -> `governed_skill_access` (`runtime_governance_context.py`)
- `runtime_governance_context` -> `skill_governance` (`runtime_governance_context.py`)
- `runtime_governance_context` -> `skill_lifecycle` (`runtime_governance_context.py`)
- `semantic_prompt_posture` -> `prompt_directives` (`semantic_prompt_posture.py`)
- `semantic_prompt_posture` -> `semantic_text` (`semantic_prompt_posture.py`)
- `semantic_text` -> `learn` (`semantic_text.py`)
- `semantic_text` -> `title_semantics` (`semantic_text.py`)
- `side` -> `applied_theory_types` (`side.py`)
- `side` -> `artifact` (`side.py`)
- `side` -> `boundary` (`side.py`)
- `side` -> `execution_framework_primitives` (`side.py`)
- `side` -> `side_runtime_dependencies` (`side.py`)
- `side_runtime_dependencies` -> `applied_theory_primitives` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `applied_theory_types` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `artifact` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `fallback_not_generation` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `id_generation` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `normalize` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `semantic_text` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `store` (`side_runtime_dependencies.py`)
- `side_runtime_dependencies` -> `structured_learning_yaml` (`side_runtime_dependencies.py`)
- `skill_boundary_normalization` -> `applied_theory_types` (`skill_boundary_normalization.py`)
- `skill_boundary_normalization` -> `semantic_text` (`skill_boundary_normalization.py`)
- `skill_boundary_normalization` -> `skill_governance` (`skill_boundary_normalization.py`)
- `skill_boundary_normalization` -> `skill_leaf_types` (`skill_boundary_normalization.py`)
- `skill_boundary_normalization` -> `skill_path_notation` (`skill_boundary_normalization.py`)
- `skill_compatibility_export` -> `normalize` (`skill_compatibility_export.py`)
- `skill_compatibility_export` -> `semantic_text` (`skill_compatibility_export.py`)
- `skill_compatibility_export` -> `skill_export_projection` (`skill_compatibility_export.py`)
- `skill_compatibility_import` -> `semantic_text` (`skill_compatibility_import.py`)
- `skill_compiler` -> `applied_theory_types` (`skill_compiler.py`)
- `skill_compiler` -> `skill_ir` (`skill_compiler.py`)
- `skill_compiler` -> `skill_schema_io` (`skill_compiler.py`)
- `skill_composition` -> `applied_theory_types` (`skill_composition.py`)
- `skill_composition` -> `semantic_text` (`skill_composition.py`)
- `skill_composition` -> `skill_boundary_normalization` (`skill_composition.py`)
- `skill_composition` -> `skill_ir` (`skill_composition.py`)
- `skill_composition` -> `skill_leaf_types` (`skill_composition.py`)
- `skill_composition` -> `skill_path_notation` (`skill_composition.py`)
- `skill_export_projection` -> `applied_theory_types` (`skill_export_projection.py`)
- `skill_export_projection` -> `approval_governance` (`skill_export_projection.py`)
- `skill_export_projection` -> `execution_frameworks` (`skill_export_projection.py`)
- `skill_export_projection` -> `host_abi` (`skill_export_projection.py`)
- `skill_export_projection` -> `side` (`skill_export_projection.py`)
- `skill_export_projection` -> `skill_boundary_normalization` (`skill_export_projection.py`)
- `skill_export_projection` -> `skill_compatibility_import` (`skill_export_projection.py`)
- `skill_export_projection` -> `skill_governance` (`skill_export_projection.py`)
- `skill_export_projection` -> `skill_ir` (`skill_export_projection.py`)
- `skill_export_projection` -> `skill_lifecycle` (`skill_export_projection.py`)
- `skill_export_projection` -> `skill_safety_governance` (`skill_export_projection.py`)
- `skill_export_projection` -> `skill_schema_io` (`skill_export_projection.py`)
- `skill_governance` -> `applied_theory_types` (`skill_governance.py`)
- `skill_governance` -> `approval_governance` (`skill_governance.py`)
- `skill_governance` -> `execution_framework_primitives` (`skill_governance.py`)
- `skill_governance` -> `host_abi` (`skill_governance.py`)
- `skill_governance` -> `python_skill_brokerization` (`skill_governance.py`)
- `skill_governance` -> `semantic_text` (`skill_governance.py`)
- `skill_governance` -> `skill_governance_primitives` (`skill_governance.py`)
- `skill_governance` -> `skill_lifecycle` (`skill_governance.py`)
- `skill_governance` -> `skill_safety_governance` (`skill_governance.py`)
- `skill_governance` -> `virtual_mounts` (`skill_governance.py`)
- `skill_governance_primitives` -> `semantic_text` (`skill_governance_primitives.py`)
- `skill_ir` -> `applied_theory_types` (`skill_ir.py`)
- `skill_ir` -> `execution_frameworks` (`skill_ir.py`)
- `skill_ir` -> `normalize` (`skill_ir.py`)
- `skill_ir` -> `semantic_text` (`skill_ir.py`)
- `skill_ir` -> `skill_boundary_normalization` (`skill_ir.py`)
- `skill_ir` -> `skill_compatibility_import` (`skill_ir.py`)
- `skill_ir` -> `skill_governance` (`skill_ir.py`)
- `skill_ir` -> `skill_lifecycle` (`skill_ir.py`)
- `skill_leaf_types` -> `applied_theory_primitives` (`skill_leaf_types.py`)
- `skill_lifecycle` -> `applied_theory_primitives` (`skill_lifecycle.py`)
- `skill_lifecycle` -> `artifact_contracts` (`skill_lifecycle.py`)
- `skill_lifecycle` -> `semantic_text` (`skill_lifecycle.py`)
- `skill_path_notation` -> `applied_theory_primitives` (`skill_path_notation.py`)
- `skill_path_notation` -> `skill_leaf_types` (`skill_path_notation.py`)
- `skill_registry` -> `applied_theory_types` (`skill_registry.py`)
- `skill_registry` -> `artifact` (`skill_registry.py`)
- `skill_registry` -> `host_abi` (`skill_registry.py`)
- `skill_registry` -> `skill_compiler` (`skill_registry.py`)
- `skill_registry` -> `skill_export_projection` (`skill_registry.py`)
- `skill_registry` -> `skill_governance` (`skill_registry.py`)
- `skill_registry` -> `skill_ir` (`skill_registry.py`)
- `skill_registry` -> `skill_lifecycle` (`skill_registry.py`)
- `skill_registry` -> `skill_safety_governance` (`skill_registry.py`)
- `skill_registry` -> `store` (`skill_registry.py`)
- `skill_safety_governance` -> `artifact_contracts` (`skill_safety_governance.py`)
- `skill_safety_governance` -> `semantic_text` (`skill_safety_governance.py`)
- `skill_safety_governance` -> `skill_lifecycle` (`skill_safety_governance.py`)
- `skill_schema_io` -> `applied_theory_types` (`skill_schema_io.py`)
- `skill_schema_io` -> `approval_governance` (`skill_schema_io.py`)
- `skill_schema_io` -> `artifact` (`skill_schema_io.py`)
- `skill_schema_io` -> `execution_frameworks` (`skill_schema_io.py`)
- `skill_schema_io` -> `host_abi` (`skill_schema_io.py`)
- `skill_schema_io` -> `normalize` (`skill_schema_io.py`)
- `skill_schema_io` -> `semantic_text` (`skill_schema_io.py`)
- `skill_schema_io` -> `side` (`skill_schema_io.py`)
- `skill_schema_io` -> `skill_boundary_normalization` (`skill_schema_io.py`)
- `skill_schema_io` -> `skill_compatibility_import` (`skill_schema_io.py`)
- `skill_schema_io` -> `skill_governance` (`skill_schema_io.py`)
- `skill_schema_io` -> `skill_ir` (`skill_schema_io.py`)
- `skill_schema_io` -> `skill_lifecycle` (`skill_schema_io.py`)
- `skill_schema_io` -> `skill_safety_governance` (`skill_schema_io.py`)
- `skill_schema_io` -> `store` (`skill_schema_io.py`)
- `store` -> `applied_theory_types` (`store.py`)
- `store` -> `artifact` (`store.py`)
- `store` -> `boundary` (`store.py`)
- `store` -> `normalize` (`store.py`)
- `store` -> `semantic_text` (`store.py`)
- `store` -> `structured_learning_yaml` (`store.py`)
- `structured_learning_yaml` -> `semantic_text` (`structured_learning_yaml.py`)
- `structured_learning_yaml` -> `title_semantics` (`structured_learning_yaml.py`)
- `supplement` -> `applied_theory_types` (`supplement.py`)
- `system_state` -> `applied_theory_types` (`system_state.py`)
- `system_state` -> `artifact` (`system_state.py`)
- `system_state` -> `boundary` (`system_state.py`)
- `system_state` -> `id_generation` (`system_state.py`)
- `system_state` -> `normalize` (`system_state.py`)
- `tablet_safety_validation` -> `validation_sqlite` (`tablet_safety_validation.py`)
- `title_depth_learning_validation` -> `validation_sqlite` (`title_depth_learning_validation.py`)
- `title_semantics` -> `prolog` (`title_semantics.py`)
- `url_learning_capture` -> `semantic_text` (`url_learning_capture.py`)
- `virtual_mounts` -> `data_governance` (`virtual_mounts.py`)
- `virtual_mounts` -> `runtime_temp` (`virtual_mounts.py`)
- `virtual_mounts` -> `semantic_text` (`virtual_mounts.py`)
- `wasm_skill_runtime` -> `applied_theory_types` (`wasm_skill_runtime.py`)
- `wasm_skill_runtime` -> `host_abi` (`wasm_skill_runtime.py`)
- `wasm_skill_runtime` -> `host_brokers` (`wasm_skill_runtime.py`)
- `wasm_skill_runtime` -> `semantic_text` (`wasm_skill_runtime.py`)

## Combined Root/Package Cycles

No cycles span root modules and workspace packages.

## Wildcard Exports

- `workstation/app_cli/src/workstation/app/cli/__init__.py` imports `*` from `workstation.app.cli.cli` (line 1)
- `workstation/foundation_models/src/workstation/foundation/models/__init__.py` imports `*` from `workstation.foundation.models.models` (line 1)
- `workstation/foundation_projections/src/workstation/foundation/projections/__init__.py` imports `*` from `workstation.foundation.projections.projection_models` (line 1)
- `workstation/skills_builtin/src/workstation/skills/builtin/__init__.py` imports `*` from `workstation.skills.builtin.builtin_skills` (line 1)
- `workstation/subject_textual/src/workstation/subject/textual/__init__.py` imports `*` from `workstation.subject.textual.subject_workflow_textual_backend` (line 1)
- `workstation/ui_textual/src/workstation/ui/textual/__init__.py` imports `*` from `workstation.ui.textual.chat_ui` (line 1)

## Ratchet Rules

The checked-in baseline records the facts above. Declared compatibility aliases preserve historical ABI; every measured category remains closed to expansion. The checker fails for new dependency edges, undeclared or forbidden edges, package-to-root, root-to-package, or root-to-root dependencies, new compatibility-alias edges, new wildcard exports, unregistered packages, and new or enlarged package or combined strongly connected components. Removing a violation and refreshing the baseline makes that improvement permanent.
