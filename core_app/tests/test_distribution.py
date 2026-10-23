from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_APP_ROOT = REPO_ROOT / "core_app"
CORE_APP_SRC = CORE_APP_ROOT / "src"
CORE_ENGINE_ROOT = REPO_ROOT / "core_engine"
if str(CORE_APP_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_APP_SRC))

from realized_core import cli
from realized_core_engine import (
    ContinuationInlet,
    GoverningDirection,
    InletRelationship,
    InspectionRequest,
    InspectionTargetKind,
    InspectionView,
    StartRequest,
)


def _root_imports(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.partition(".")[0])
    return imports


def _engine_modules() -> set[str]:
    return {
        line
        for raw_line in (CORE_ENGINE_ROOT / "module_manifest.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    }


class CoreApplicationDistributionTests(unittest.TestCase):
    def test_project_declares_only_product_dependencies_and_command(self) -> None:
        project = tomllib.loads(
            (CORE_APP_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        metadata = project["project"]

        self.assertEqual(
            "realized_core.cli:main",
            metadata["scripts"]["realized-core"],
        )
        self.assertEqual(
            [
                "realized-core-conversation==0.1.0",
                "realized-core-engine==0.1.0",
                "realized-core-llm==0.1.0",
            ],
            metadata["dependencies"],
        )
        self.assertEqual(
            ["realized-core-engine[wasm]==0.1.0"],
            metadata["optional-dependencies"]["wasm"],
        )

    def test_cli_imports_engine_contract_without_owning_engine_modules(self) -> None:
        local_modules = {path.stem for path in REPO_ROOT.glob("*.py")}
        cli_imports = _root_imports(CORE_APP_SRC / "realized_core" / "cli.py")

        self.assertEqual(set(), cli_imports & local_modules)
        self.assertIn("realized_core_engine", cli_imports)
        self.assertTrue(_engine_modules())
        self.assertNotIn("workstation", cli_imports)
        self.assertFalse((CORE_APP_ROOT / "module_manifest.txt").exists())
        self.assertFalse((CORE_APP_ROOT / "setup.py").exists())

    def test_workspace_and_cloud_build_qualify_the_application(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn("core_app", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertIn("uv build --wheel core_app", cloud_build)
        self.assertIn("uv build --wheel core_conversation", cloud_build)
        self.assertIn("uv build --wheel core_llm", cloud_build)
        self.assertIn("core_conversation.tests.test_pipeline", cloud_build)
        self.assertIn("core_llm.tests.test_provider", cloud_build)
        self.assertIn("core_app.tests.test_distribution", cloud_build)
        self.assertIn("core_app.tests.test_chat", cloud_build)
        self.assertIn("core_app.tests.test_resumption_journey", cloud_build)
        self.assertIn("tests.test_resumption_journey_spec", cloud_build)
        self.assertIn("tests.test_core_app_cli_equivalence", cloud_build)
        self.assertIn("scripts/verify_core_distribution.py", cloud_build)

    def test_cli_run_uses_plain_sqlite_and_writes_durable_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "state.sqlite3"
            state_path = root / "run.json"
            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "",
                    "STATE_VECTOR_MODE": "on",
                },
                clear=False,
            ), patch("builtins.print") as output:
                status = cli.main(
                    [
                        "run",
                        "--prompt",
                        "Record a deterministic realization.",
                        "--llm",
                        "off",
                        "--max-steps",
                        "0",
                        "--sqlite",
                        str(sqlite_path),
                        "--state-out",
                        str(state_path),
                    ]
                )
                self.assertEqual("off", os.environ["STATE_VECTOR_MODE"])

            self.assertEqual(0, status)
            self.assertTrue(sqlite_path.is_file())
            self.assertTrue(state_path.is_file())
            summary = json.loads(output.call_args.args[0])
            self.assertEqual(
                "Record a deterministic realization.",
                summary["root"]["semantic_unit"],
            )
            self.assertFalse(summary["llm"]["artifact_store"]["vector_enabled"])

    def test_cli_resumes_and_inspects_the_same_durable_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "state.sqlite3"
            initial_state_path = root / "initial.json"
            resumed_state_path = root / "resumed.json"
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch(
                "builtins.print"
            ) as output:
                self.assertEqual(
                    0,
                    cli.main(
                        [
                            "run",
                            "--prompt",
                            "Resume this deterministic realization.",
                            "--llm",
                            "off",
                            "--max-steps",
                            "0",
                            "--sqlite",
                            str(sqlite_path),
                            "--state-out",
                            str(initial_state_path),
                        ]
                    ),
                )
                output.reset_mock()
                self.assertEqual(
                    0,
                    cli.main(
                        [
                            "resume",
                            "--state-in",
                            str(initial_state_path),
                            "--llm",
                            "off",
                            "--max-steps",
                            "0",
                            "--sqlite",
                            str(sqlite_path),
                            "--state-out",
                            str(resumed_state_path),
                        ]
                    ),
                )
                resumed_summary = json.loads(output.call_args.args[0])
                output.reset_mock()
                self.assertEqual(
                    0,
                    cli.main(["inspect", "--state", str(resumed_state_path)]),
                )
                inspected_summary = json.loads(output.call_args.args[0])

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
                        resumed_summary[stable_key],
                        inspected_summary[stable_key],
                    )
            self.assertEqual(
                "Resume this deterministic realization.",
                inspected_summary["root"]["semantic_unit"],
            )

    def test_cli_exposes_typed_objective_start_and_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "resumption.sqlite3"
            start_request_path = root / "start.json"
            inspect_request_path = root / "inspect.json"
            start_request = StartRequest(
                scope_id="scope-cli",
                objective_id="objective-cli",
                branch_id="main",
                initial_inlet=ContinuationInlet(
                    inlet_id="inlet-cli",
                    kind="prompt",
                    payload={"prompt": "Exercise typed CLI resumption."},
                    target="root",
                    relationship=InletRelationship.CONTINUATION,
                    source="human",
                    provenance=("message-cli",),
                    correlation={},
                    authority_context={"principal": "tester"},
                ),
                governing_direction=GoverningDirection(
                    objective="Exercise typed CLI resumption.",
                    scope="scope-cli",
                ),
            )
            start_request_path.write_text(
                json.dumps(start_request.to_dict()),
                encoding="utf-8",
            )
            inspect_request = InspectionRequest(
                target_kind=InspectionTargetKind.BRANCH_HEAD,
                target_id="scope-cli/objective-cli/main",
                view=InspectionView.GOVERNING_DIRECTION,
                scope_id="scope-cli",
                objective_id="objective-cli",
                branch_id="main",
            )
            inspect_request_path.write_text(
                json.dumps(inspect_request.to_dict()),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False), patch(
                "builtins.print"
            ) as output:
                self.assertEqual(
                    0,
                    cli.main(
                        [
                            "objective-start",
                            "--request",
                            str(start_request_path),
                            "--sqlite",
                            str(sqlite_path),
                            "--llm",
                            "off",
                            "--max-steps",
                            "0",
                            "--discovery",
                            "off",
                            "--reflection",
                            "off",
                            "--contemplation",
                            "off",
                        ]
                    ),
                )
                started = json.loads(output.call_args.args[0])
                output.reset_mock()
                self.assertEqual(
                    0,
                    cli.main(
                        [
                            "resumption-inspect",
                            "--request",
                            str(inspect_request_path),
                            "--sqlite",
                            str(sqlite_path),
                        ]
                    ),
                )
                inspected = json.loads(output.call_args.args[0])

            self.assertEqual("terminated", started["execution_outcome"])
            self.assertEqual(
                "Exercise typed CLI resumption.",
                inspected["payload"]["objective"],
            )


if __name__ == "__main__":
    unittest.main()
