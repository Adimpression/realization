# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import controller_entrypoints
import realized_exchange.artifact_yaml as side
from realized_core_engine import controller_runtime
from realized_core_semantics.applied_model import RunOutcome


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "boundary_shape_artifacts"


class _BatchOnlyStore:
    def __init__(self) -> None:
        self.persist_batches: list[tuple[str, ...]] = []

    def persist_artifacts(self, artifacts, *, run_id: str = "artifact_import") -> dict[str, object]:
        artifact_list = list(artifacts)
        self.persist_batches.append(tuple(str(artifact.id) for artifact in artifact_list))
        return {
            "status": "persisted",
            "persisted_artifacts": len(artifact_list),
            "unchanged_artifacts": 0,
            "error_artifacts": 0,
            "reports": [
                {
                    "artifact_id": artifact.id,
                    "status": "persisted",
                }
                for artifact in artifact_list
            ],
        }

    def persist_artifact(self, artifact, *, run_id: str = "artifact_import") -> dict[str, object]:
        raise AssertionError("bundle import should batch persistence through persist_artifacts")


class _NoOpController:
    def __init__(self, state) -> None:
        self.state = state

    def run(self, max_steps: int = 64) -> None:
        self.state.run_outcome = RunOutcome.COMPLETED


class _RuntimeProxy:
    def __init__(self, store: _BatchOnlyStore) -> None:
        self._store = store

    def build_artifact_store(self) -> _BatchOnlyStore:
        return self._store

    def __getattr__(self, name: str):
        return getattr(controller_runtime, name)


class ImportBatchingTests(unittest.TestCase):
    def test_load_yaml_and_run_batches_imported_artifacts_before_execution(self) -> None:
        fixture_paths = [
            FIXTURE_DIR / "hi_responder.yaml",
            FIXTURE_DIR / "personalized_greeter.yaml",
        ]
        store = _BatchOnlyStore()
        args = argparse.Namespace(
            artifact_file=fixture_paths,
            artifact_files_file=None,
            artifact_dir=None,
            prompt="Say hi.",
            llm="off",
            max_steps=8,
            evidence_file=None,
            state_out=None,
            prolog_query_priming=None,
            discovery=None,
            reflection=None,
            contemplation=None,
            supported_executors=None,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with patch.object(
                controller_entrypoints,
                "_runtime_main",
                return_value=SimpleNamespace(build_artifact_store=lambda: store),
            ):
                with patch.object(
                    controller_entrypoints,
                    "build_controller",
                    side_effect=lambda *, state=None, llm_policy="auto": _NoOpController(state),
                ):
                    exit_code = controller_entrypoints.handle_load_yaml_and_run_command(args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(store.persist_batches), 1)
        self.assertEqual(len(store.persist_batches[0]), 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["imported_count"], 2)
        self.assertTrue(all(item["store_report"]["status"] == "persisted" for item in payload["imported"]))

    def test_artifact_import_batches_multi_file_persistence(self) -> None:
        fixture_paths = [
            FIXTURE_DIR / "hi_responder.yaml",
            FIXTURE_DIR / "personalized_greeter.yaml",
        ]
        store = _BatchOnlyStore()
        args = argparse.Namespace(
            artifact_file=fixture_paths,
            artifact_files_file=None,
            artifact_dir=None,
            normalized_out=None,
            normalized_out_dir=None,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with patch.object(side, "_runtime", return_value=_RuntimeProxy(store)):
                exit_code = side.handle_artifact_import_command(args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(store.persist_batches), 1)
        self.assertEqual(len(store.persist_batches[0]), 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["imported_count"], 2)
        self.assertTrue(all(item["store_report"]["status"] == "persisted" for item in payload["imported"]))
