"""Concrete provider composition for the installable workstation application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from realized_core_engine import (
    EngineConfiguration,
    EngineInlet,
    controller_runtime,
    inspect as inspect_core_state,
    resume as resume_core_run,
    run as start_core_run,
)
from realized_core_engine.configuration import STATE_SQLITE_PATH_ENV
from realized_core_engine.persistence import open_sqlite_artifact_repository
from realized_core_engine.state import SystemState
from realized_core_runtime.host_realizers import packaged_host_realizer_provider
from realized_core_runtime.temporary import runtime_temporary_directory
from realized_exchange.artifact_yaml import export_artifact_bundle_text
from realized_exchange.markdown_learning_pipeline import (
    install_markdown_learning_extensions,
)
from realized_exchange.workstation import RealizedSkillExchangeProvider
from realized_host_interaction.context import (
    HostInteractionContext,
    host_realizer_provider,
    with_host_realizer_provider,
)
from realized_host_interaction.realizers import combine_host_realizer_providers
from workstation.app.cli.runtime_controller import bootstrap_runtime_controller
from workstation.contracts.runtime import GovernedTurnRequest, GovernedTurnResult
from workstation.foundation.host.artifact_repository import (
    register_artifact_repository_provider,
)
from workstation.foundation.host.controller_runtime import (
    register_controller_runtime_provider,
)
from workstation.foundation.host.skill_exchange import register_skill_exchange_provider
from workstation.foundation.host.subject_workflow import (
    register_subject_workflow_client_factory,
)
from workstation.runtime.core.subject_host_actions import (
    RuntimeSubjectWorkflowHostActions,
)
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService
from workstation.subject.service.subject_workflow_client import (
    InProcessSubjectWorkflowClient,
)


install_markdown_learning_extensions(controller_runtime)


class ApplicationControllerRuntimeProvider:
    """Controller implementation supplied by workstation entry composition."""

    def bootstrap_controller(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        subject_scope: Any | None = None,
        subject_scope_root_path: Path | None = None,
    ) -> tuple[Any, Any]:
        return bootstrap_runtime_controller(
            semantic_unit=semantic_unit,
            llm_policy=llm_policy,
            subject_scope=subject_scope,
            subject_scope_root_path=subject_scope_root_path,
        )

    def bootstrap_controller_with_host_interaction(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        host_interaction_context: HostInteractionContext,
    ) -> tuple[Any, Any]:
        combined_provider = combine_host_realizer_providers(
            packaged_host_realizer_provider(),
            host_realizer_provider(host_interaction_context),
        )
        state = SystemState.bootstrap(semantic_unit)
        return state, controller_runtime.build_controller(
            state=state,
            llm_policy=llm_policy,
            host_interaction_context=with_host_realizer_provider(
                host_interaction_context,
                combined_provider,
            ),
        )

    def perform_governed_turn(
        self,
        request: GovernedTurnRequest,
    ) -> GovernedTurnResult:
        checkpoint_path = Path(request.checkpoint_path).expanduser().resolve()
        sqlite_path = Path(request.sqlite_path).expanduser().resolve()
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        treatment = str(request.treatment).strip()
        parent_run_id = str(request.parent_run_id or "").strip()
        parent_summary: dict[str, Any] | None = None
        parent_checkpoint_path = (
            Path(request.parent_checkpoint_path).expanduser().resolve()
            if request.parent_checkpoint_path is not None
            else None
        )

        if treatment != "independent":
            if parent_checkpoint_path is None or not parent_checkpoint_path.is_file():
                raise ValueError(
                    f"{treatment} requires an existing parent reduction checkpoint."
                )
            parent_summary = inspect_core_state(parent_checkpoint_path).summary
            actual_parent_run_id = str(parent_summary.get("run_id", "")).strip()
            if parent_run_id and parent_run_id != actual_parent_run_id:
                raise ValueError("The selected parent run does not match its checkpoint.")
            parent_run_id = actual_parent_run_id

        if treatment == "human_contribution":
            parent_outcome = str((parent_summary or {}).get("run_outcome", ""))
            if parent_outcome not in {"paused", "incomplete"}:
                raise ValueError(
                    "A human contribution may resume only a paused or incomplete run."
                )
            result = resume_core_run(
                parent_checkpoint_path,
                configuration=EngineConfiguration(
                    state_output_path=checkpoint_path,
                    sqlite_path=sqlite_path,
                    max_steps=max(0, int(request.max_steps)),
                    llm_policy=request.llm_policy,
                    inlets=(
                        EngineInlet(
                            kind="human_contribution",
                            content=request.prompt,
                            source_ref=request.user_message_id,
                            provenance=(
                                request.turn_id,
                                request.session_id,
                                parent_run_id,
                            ),
                            context={
                                "session_id": request.session_id,
                                "turn_id": request.turn_id,
                                "parent_run_id": parent_run_id,
                            },
                        ),
                    ),
                ),
            )
        elif treatment in {"follow_up", "correction"}:
            parent_outcome = str((parent_summary or {}).get("run_outcome", ""))
            prior_answer = str(
                (parent_summary or {}).get("final_answer", "") or ""
            ).strip()
            if parent_outcome != "completed" or not prior_answer:
                raise ValueError(
                    f"A {treatment} requires a completed parent run with a committed result."
                )
            result = start_core_run(
                request.prompt,
                configuration=EngineConfiguration(
                    state_output_path=checkpoint_path,
                    sqlite_path=sqlite_path,
                    max_steps=max(0, int(request.max_steps)),
                    llm_policy=request.llm_policy,
                    inlets=(
                        EngineInlet(
                            kind="prior_result",
                            content=prior_answer,
                            source_ref=parent_run_id,
                            provenance=(request.turn_id, request.session_id),
                            context={
                                "relationship": treatment,
                                "parent_run_id": parent_run_id,
                            },
                        ),
                    ),
                ),
            )
        elif treatment == "independent":
            result = start_core_run(
                request.prompt,
                configuration=EngineConfiguration(
                    state_output_path=checkpoint_path,
                    sqlite_path=sqlite_path,
                    max_steps=max(0, int(request.max_steps)),
                    llm_policy=request.llm_policy,
                ),
            )
        else:
            raise ValueError(f"Unsupported governed turn treatment: {treatment}")

        summary = dict(result.summary)
        run_outcome = str(summary.get("run_outcome", "ongoing"))
        root_status = str(dict(summary.get("root", {})).get("status", "open"))
        assistant_text = str(summary.get("final_answer", "") or "").strip()
        if not assistant_text:
            assistant_text = {
                "paused": (
                    "The governed run paused for an explicit boundary contribution."
                ),
                "incomplete": (
                    "The governed run is incomplete and remains available for "
                    "explicit continuation."
                ),
                "ongoing": "The governed run remains in progress.",
            }.get(run_outcome, "The governed run completed without a projected answer.")
        return GovernedTurnResult(
            assistant_text=assistant_text,
            run_id=str(summary.get("run_id", "")),
            parent_run_id=parent_run_id,
            run_outcome=run_outcome,
            root_status=root_status,
            checkpoint_path=checkpoint_path,
            sqlite_path=sqlite_path,
            summary=summary,
        )

    def learn_markdown_bundle(
        self,
        *,
        root_path: Path,
        markdown_path: Path,
        source_label: str,
        bundle_output_path: Path,
        max_artifacts: int,
        source_bundle_override: dict[str, Any] | None,
    ) -> dict[str, Any]:
        previous_learning_context_root = os.environ.get("LEARNING_CONTEXT_ROOT")
        previous_sqlite_path = os.environ.get(STATE_SQLITE_PATH_ENV)
        with runtime_temporary_directory(
            prefix="workstation-url-learn-state-"
        ) as sqlite_directory:
            os.environ["LEARNING_CONTEXT_ROOT"] = str(
                Path(root_path).expanduser().resolve()
            )
            os.environ[STATE_SQLITE_PATH_ENV] = str(
                Path(sqlite_directory) / "state.sqlite3"
            )
            try:
                label = " ".join(str(source_label or "").split()) or markdown_path.name
                state = SystemState.bootstrap(
                    f"Learn from source: {label}",
                    bootstrap_mode="markdown_ingestion",
                )
                controller = controller_runtime.build_controller(
                    state=state,
                    llm_policy=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
                )
                report = controller.learn_from_markdown_document(
                    markdown_path,
                    max_artifacts=max(1, int(max_artifacts)),
                    source_bundle_override=source_bundle_override,
                )
                bundle_output_path.write_text(
                    export_artifact_bundle_text(
                        list(state.learned_artifacts.values())
                    ),
                    encoding="utf-8",
                )
                return dict(report)
            finally:
                if previous_learning_context_root is None:
                    os.environ.pop("LEARNING_CONTEXT_ROOT", None)
                else:
                    os.environ["LEARNING_CONTEXT_ROOT"] = (
                        previous_learning_context_root
                    )
                if previous_sqlite_path is None:
                    os.environ.pop(STATE_SQLITE_PATH_ENV, None)
                else:
                    os.environ[STATE_SQLITE_PATH_ENV] = previous_sqlite_path


class ApplicationArtifactRepositoryProvider:
    """SQLite repository implementation supplied by workstation composition."""

    def open_artifact_repository(
        self,
        *,
        sqlite_path: Path,
        vector_mode: str | None = None,
    ):
        return open_sqlite_artifact_repository(
            sqlite_path,
            vector_mode=vector_mode,
        )


def ensure_workstation_application_composition() -> None:
    """Bind every concrete provider required by the workstation application."""

    register_controller_runtime_provider(ApplicationControllerRuntimeProvider())
    register_artifact_repository_provider(ApplicationArtifactRepositoryProvider())
    register_subject_workflow_client_factory(
        lambda: InProcessSubjectWorkflowClient(
            service=SubjectWorkflowApiService(
                host_actions=RuntimeSubjectWorkflowHostActions(),
            )
        )
    )
    register_skill_exchange_provider(RealizedSkillExchangeProvider())


__all__ = [
    "ApplicationArtifactRepositoryProvider",
    "ApplicationControllerRuntimeProvider",
    "ensure_workstation_application_composition",
]
