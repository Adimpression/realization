from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_ENGINE_SRC = REPO_ROOT / "core_engine" / "src"
if str(CORE_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_ENGINE_SRC))

from realized_core_engine import (
    ContinuationInlet,
    EngineConfiguration,
    EngineInlet,
    EngineResult,
    GoverningDirection,
    InletRelationship,
    InspectionRequest,
    InspectionTargetKind,
    InspectionView,
    ArtifactRepository,
    StartRequest,
    inspect,
    inspect_resumption,
    resume,
    run,
    start_objective,
    open_sqlite_artifact_repository,
)
from realized_core_engine.api import ResumptionEngine
from realized_core_engine.controller_runtime import BSSCController
from realized_core_engine.persistence import build_artifact_store
from realized_core_engine.state import SystemState
from realized_host_interaction import (
    HostBrokerBinding,
    HostRealizerDescriptor,
    StaticHostRealizerProvider,
    host_native_interaction_context,
)


class CoreEngineApiTests(unittest.TestCase):
    def test_controller_obtains_its_default_repository_through_the_persistence_port(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            sqlite_path = Path(temporary_dir) / "controller.sqlite3"
            with (
                patch.dict(os.environ, {"STATE_SQLITE_PATH": str(sqlite_path)}, clear=False),
                patch(
                    "realized_core_engine.controller_runtime._build_artifact_store",
                    wraps=build_artifact_store,
                ) as repository_factory,
            ):
                controller = BSSCController(
                    SystemState.bootstrap("Use the repository composition port."),
                    llm_policy="off",
                )

            repository_factory.assert_called_once_with()
            self.assertIsInstance(controller.artifact_store, ArtifactRepository)
            self.assertEqual(controller.artifact_store.sqlite_path.resolve(), sqlite_path.resolve())

    def test_public_sqlite_repository_factory_binds_explicit_path_and_vector_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            sqlite_path = Path(temporary_dir) / "artifacts.sqlite3"
            repository = open_sqlite_artifact_repository(
                sqlite_path,
                vector_mode="off",
            )

            self.assertIsInstance(repository, ArtifactRepository)
            self.assertEqual(repository.sqlite_path, sqlite_path.resolve())
            self.assertEqual(repository.vector_mode_override, "off")
            self.assertEqual(repository.load_all_artifacts(), [])
            self.assertTrue(sqlite_path.is_file())

    def test_direct_engine_run_forwards_injected_host_context(self) -> None:
        provider = StaticHostRealizerProvider(
            brokers=(
                HostBrokerBinding(
                    descriptor=HostRealizerDescriptor(
                        kind="broker",
                        identity="fs.read_text",
                    ),
                    callback=lambda invocation, active: {"status": "ok"},
                ),
            ),
        )
        context = host_native_interaction_context(realizer_provider=provider)
        observed: dict[str, object] = {}

        class Controller:
            def __init__(self, state) -> None:
                self.state = state

            def run(self, *, max_steps: int) -> None:
                observed["max_steps"] = max_steps

        def build_controller(*, state, llm_policy, host_interaction_context):
            observed["llm_policy"] = llm_policy
            observed["host_interaction_context"] = host_interaction_context
            return Controller(state)

        with tempfile.TemporaryDirectory() as temporary_dir:
            configuration = EngineConfiguration(
                sqlite_path=Path(temporary_dir) / "state.sqlite3",
                max_steps=0,
                llm_policy="off",
                host_interaction_context=context,
            )
            with patch("realized_core_engine.api.build_controller", build_controller):
                result = run("Forward the provider.", configuration=configuration)

        self.assertIs(observed["host_interaction_context"], context)
        self.assertEqual(observed["llm_policy"], "off")
        self.assertEqual(observed["max_steps"], 0)
        self.assertEqual(result.summary["root"]["semantic_unit"], "Forward the provider.")

    def test_resumption_keeps_provider_out_of_persisted_execution_policy(self) -> None:
        provider = StaticHostRealizerProvider()
        context = host_native_interaction_context(realizer_provider=provider)
        with tempfile.TemporaryDirectory() as temporary_dir:
            sqlite_path = Path(temporary_dir) / "resumption.sqlite3"
            engine = ResumptionEngine(
                configuration=EngineConfiguration(
                    sqlite_path=sqlite_path,
                    max_steps=0,
                    llm_policy="off",
                    host_interaction_context=context,
                )
            )
            request = StartRequest(
                scope_id="scope-provider",
                objective_id="objective-provider",
                branch_id="main",
                initial_inlet=ContinuationInlet(
                    inlet_id="inlet-provider",
                    kind="prompt",
                    payload={"prompt": "Keep callables outside durable policy."},
                    target="root",
                    relationship=InletRelationship.CONTINUATION,
                    source="human",
                    provenance=("message-provider",),
                    correlation={},
                    authority_context={"principal": "tester"},
                ),
                governing_direction=GoverningDirection(
                    objective="Keep callables outside durable policy.",
                    scope="scope-provider",
                ),
            )

            engine.start(request)

            connection = sqlite3.connect(sqlite_path)
            try:
                persisted_policy = json.loads(
                    connection.execute(
                        "SELECT execution_policy_json FROM resumption_attempts LIMIT 1"
                    ).fetchone()[0]
                )
            finally:
                connection.close()

        adapter = engine._service.reduction_controller
        self.assertIs(adapter._host_interaction_context, context)
        self.assertNotIn("host_interaction_context", persisted_policy)
        json.dumps(persisted_policy, sort_keys=True)

    def test_typed_resumption_abi_round_trips_through_plain_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            sqlite_path = Path(temporary_dir) / "resumption.sqlite3"
            request = StartRequest(
                scope_id="scope-api",
                objective_id="objective-api",
                branch_id="main",
                initial_inlet=ContinuationInlet(
                    inlet_id="inlet-api",
                    kind="prompt",
                    payload={"prompt": "Represent this objective durably."},
                    target="root",
                    relationship=InletRelationship.CONTINUATION,
                    source="human",
                    provenance=("message-api",),
                    correlation={},
                    authority_context={"principal": "tester"},
                ),
                governing_direction=GoverningDirection(
                    objective="Represent this objective durably.",
                    scope="scope-api",
                ),
            )
            self.assertEqual(request, StartRequest.from_dict(request.to_dict()))
            configuration = EngineConfiguration(
                sqlite_path=sqlite_path,
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            )

            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                started = start_objective(
                    request,
                    configuration=configuration,
                )
                inspected = inspect_resumption(
                    InspectionRequest(
                        target_kind=InspectionTargetKind.BRANCH_HEAD,
                        target_id="scope-api/objective-api/main",
                        view=InspectionView.CURRENT_STATE,
                        scope_id="scope-api",
                        objective_id="objective-api",
                        branch_id="main",
                    ),
                    configuration=configuration,
                )

            self.assertTrue(sqlite_path.is_file())
            self.assertIsNotNone(started.resulting_revision_identity)
            self.assertEqual(
                "Represent this objective durably.",
                inspected.payload["governing_direction"]["objective"],
            )
            json.dumps(started.to_dict(), sort_keys=True)
            json.dumps(inspected.to_dict(), sort_keys=True)

    def test_resume_admits_only_explicit_typed_human_contribution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "state.sqlite3"
            state_path = root / "run.json"
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                run(
                    "Wait for an explicit human answer.",
                    configuration=EngineConfiguration(
                        state_output_path=state_path,
                        sqlite_path=sqlite_path,
                        max_steps=0,
                        llm_policy="off",
                    ),
                )
                resume(
                    state_path,
                    configuration=EngineConfiguration(
                        state_output_path=state_path,
                        sqlite_path=sqlite_path,
                        max_steps=0,
                        llm_policy="off",
                        inlets=(
                            EngineInlet(
                                kind="human_contribution",
                                content="The selected answer is forty-two.",
                                source_ref="message-42",
                                provenance=("turn-7",),
                                context={"session_id": "session-3"},
                            ),
                        ),
                    ),
                )

            payload = json.loads(state_path.read_text(encoding="utf-8"))
            contributions = list(payload["human_contributions"].values())
            self.assertEqual(1, len(contributions))
            self.assertEqual("The selected answer is forty-two.", contributions[0]["content"])
            self.assertIn("message-42", contributions[0]["provenance"])
            self.assertIn("turn-7", contributions[0]["provenance"])
            self.assertNotIn("unselected transcript text", state_path.read_text(encoding="utf-8"))

    def test_run_applies_typed_configuration_and_plain_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "state.sqlite3"
            state_path = root / "run.json"
            evidence_path = root / "evidence.json"
            evidence_path.write_text(
                json.dumps(
                    [
                        {
                            "target": "root",
                            "observation": "A deterministic supporting observation.",
                            "source": "test",
                            "support_strength": "high",
                            "confidence": "high",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configuration = EngineConfiguration(
                evidence_path=evidence_path,
                state_output_path=state_path,
                sqlite_path=sqlite_path,
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
                prolog_query_priming="force",
                supported_executors=("python3", "bash"),
            )

            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "",
                    "STATE_VECTOR_MODE": "on",
                },
                clear=False,
            ):
                result = run(
                    "Exercise the public engine ABI.",
                    configuration=configuration,
                )

                self.assertEqual("off", os.environ["STATE_VECTOR_MODE"])
                self.assertEqual(str(sqlite_path), os.environ["STATE_SQLITE_PATH"])
                self.assertEqual("force", os.environ["BSSC_PROLOG_QUERY_PRIMING"])

            self.assertIsInstance(result, EngineResult)
            self.assertTrue(sqlite_path.is_file())
            self.assertTrue(state_path.is_file())
            self.assertEqual(
                "Exercise the public engine ABI.",
                result.summary["root"]["semantic_unit"],
            )
            self.assertEqual(1, result.summary["counts"]["evidence"])
            self.assertEqual(
                {
                    "contemplation_enabled": False,
                    "discovery_enabled": False,
                    "reflection_enabled": False,
                    "supported_executors": ["python3", "bash"],
                },
                result.summary["controller_features"],
            )
            self.assertFalse(result.summary["llm"]["artifact_store"]["vector_enabled"])

    def test_resume_and_inspect_preserve_the_durable_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "state.sqlite3"
            initial_state_path = root / "initial.json"
            resumed_state_path = root / "resumed.json"
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                run(
                    "Resume through the public engine ABI.",
                    configuration=EngineConfiguration(
                        state_output_path=initial_state_path,
                        sqlite_path=sqlite_path,
                        max_steps=0,
                        llm_policy="off",
                    ),
                )
                resumed = resume(
                    initial_state_path,
                    configuration=EngineConfiguration(
                        state_output_path=resumed_state_path,
                        sqlite_path=sqlite_path,
                        max_steps=0,
                        llm_policy="off",
                    ),
                )
                inspected = inspect(resumed_state_path)

            self.assertTrue(resumed_state_path.is_file())
            for stable_key in (
                "controller_features",
                "counts",
                "final_answer",
                "frontier",
                "nodes",
                "root",
                "run_id",
                "run_outcome",
                "theory_version",
            ):
                with self.subTest(stable_key=stable_key):
                    self.assertEqual(
                        resumed.summary[stable_key],
                        inspected.summary[stable_key],
                    )


if __name__ == "__main__":
    unittest.main()
