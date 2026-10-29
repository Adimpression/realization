from __future__ import annotations

from pathlib import Path
import os
import subprocess
import tarfile
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from realized_core_engine import controller_runtime as engine_controller_runtime
from realized_core_engine import (
    markdown_learning_artifact_semantics as markdown_artifact_semantics,
)
from realized_exchange import markdown_learning_pipeline
from workstation.app.cli.arguments import build_workstation_parser
from workstation.app.cli import cli


APP_ROOT = Path(__file__).resolve().parents[1]


class WorkstationApplicationEntrypointTests(unittest.TestCase):
    def test_package_composition_installs_markdown_learning_extensions(self) -> None:
        self.assertIs(
            engine_controller_runtime.BSSCController.learn_from_markdown_document,
            markdown_learning_pipeline.learn_from_markdown_document,
        )
        self.assertIs(
            engine_controller_runtime.BSSCController.build_markdown_learning_artifact,
            markdown_artifact_semantics.build_markdown_learning_artifact,
        )
        self.assertIs(
            engine_controller_runtime.markdown_ability_collision_identity,
            markdown_artifact_semantics.markdown_ability_collision_identity,
        )

    def test_distribution_declares_installable_workstation_command(self) -> None:
        project = tomllib.loads(
            (APP_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]

        self.assertEqual(
            "workstation.app.cli.cli:main",
            project["scripts"]["realized-workstation"],
        )
        self.assertTrue(
            (
                APP_ROOT
                / "src"
                / "workstation"
                / "app"
                / "cli"
                / "__main__.py"
            ).is_file()
        )

    def test_parser_supports_canonical_and_historical_command_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "workstation"
            workspace = Path(temporary_dir) / "workspace"
            parser = build_workstation_parser()

            canonical = parser.parse_args(
                ["launch", "--root", str(root), "--workspace", str(workspace)]
            )
            historical = parser.parse_args(
                [
                    "workstation-launch",
                    "--root",
                    str(root),
                    "--workspace",
                    str(workspace),
                ]
            )

        self.assertEqual("launch", canonical.workstation_action)
        self.assertEqual("launch", historical.workstation_action)
        self.assertEqual(canonical.root, historical.root)
        self.assertEqual(canonical.workspace, historical.workspace)
        self.assertTrue(canonical.allow_direct_llm_decomposition)

    def test_main_dispatches_to_existing_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "workstation"
            workspace = Path(temporary_dir) / "workspace"
            with patch.object(
                cli,
                "handle_workstation_launch_command",
                return_value=23,
            ) as handler:
                status = cli.main(
                    [
                        "launch",
                        "--root",
                        str(root),
                        "--workspace",
                        str(workspace),
                        "--no-allow-direct-llm-decomposition",
                    ]
                )

        self.assertEqual(23, status)
        args = handler.call_args.args[0]
        self.assertEqual("launch", args.workstation_action)
        self.assertFalse(args.allow_direct_llm_decomposition)

    def test_source_distribution_contains_command_and_module_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            environment = dict(os.environ)
            environment["UV_CACHE_DIR"] = "/tmp/realized-uv-cache"
            subprocess.run(
                [
                    "uv",
                    "build",
                    "--no-build-isolation",
                    "--sdist",
                    "--out-dir",
                    temporary_dir,
                    "workstation/app_cli",
                ],
                cwd=APP_ROOT.parents[1],
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            archives = list(Path(temporary_dir).glob("*.tar.gz"))
            self.assertEqual(1, len(archives))
            with tarfile.open(archives[0], mode="r:gz") as archive:
                names = set(archive.getnames())

        prefix = "realized_workstation_app_cli-0.1.0"
        self.assertIn(f"{prefix}/README.md", names)
        self.assertIn(f"{prefix}/src/workstation/app/cli/__main__.py", names)
        self.assertIn(f"{prefix}/src/workstation/app/cli/arguments.py", names)
        self.assertIn(f"{prefix}/src/workstation/app/cli/cli.py", names)
        self.assertIn(f"{prefix}/src/workstation/app/cli/composition.py", names)
        self.assertIn(f"{prefix}/src/workstation/app/cli/runtime_controller.py", names)


if __name__ == "__main__":
    unittest.main()
