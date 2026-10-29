from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from args import parse_args as parse_historical_args
from workstation.app.cli.arguments import build_workstation_parser
from workstation.app.cli.cli import main as workstation_main


class WorkstationApplicationCliEquivalenceTests(unittest.TestCase):
    def test_package_entrypoint_launches_real_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            base = Path(temporary_dir)
            root = base / "workstation"
            workspace = base / "workspace"
            workspace.mkdir()
            with redirect_stdout(io.StringIO()) as output:
                status = workstation_main(
                    [
                        "launch",
                        "--root",
                        str(root),
                        "--workspace",
                        str(workspace),
                        "--task",
                        "Inspect the project.",
                    ]
                )

            report = json.loads(output.getvalue())
            self.assertEqual(0, status)
            self.assertEqual(str(root.resolve()), report["root_path"])
            self.assertTrue((root / "SESSION.json").is_file())
            self.assertTrue((root / "WORKSTATION.toml").is_file())

    def test_package_parser_preserves_historical_workstation_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            base = Path(temporary_dir)
            root = base / "workstation"
            workspace = base / "workspace"
            skill_file = base / "skill.yaml"
            cases = (
                (
                    [
                        "workstation-launch",
                        "--root",
                        str(root),
                        "--workspace",
                        str(workspace),
                        "--skills-sqlite",
                        str(base / "skills.sqlite3"),
                        "--no-allow-direct-llm-decomposition",
                    ],
                    [
                        "launch",
                        "--root",
                        str(root),
                        "--workspace",
                        str(workspace),
                        "--skills-sqlite",
                        str(base / "skills.sqlite3"),
                        "--no-allow-direct-llm-decomposition",
                    ],
                ),
                (
                    [
                        "workstation-prompt",
                        "--root",
                        str(root),
                        "--prompt",
                        "Inspect the workspace.",
                        "--mode",
                        "governed_conversation",
                        "--governed-treatment",
                        "follow_up",
                    ],
                    [
                        "prompt",
                        "--root",
                        str(root),
                        "--prompt",
                        "Inspect the workspace.",
                        "--mode",
                        "governed_conversation",
                        "--governed-treatment",
                        "follow_up",
                    ],
                ),
                (
                    ["workstation-chat", "--root", str(root)],
                    ["chat", "--root", str(root)],
                ),
                (
                    [
                        "workstation-grpc-host",
                        "--serve-root",
                        str(root),
                        "--port",
                        "0",
                        "--asset-port",
                        "0",
                    ],
                    [
                        "grpc-host",
                        "--serve-root",
                        str(root),
                        "--port",
                        "0",
                        "--asset-port",
                        "0",
                    ],
                ),
                (
                    [
                        "workstation-skill-catalog",
                        "--root",
                        str(root),
                        "--query",
                        "python",
                        "--limit",
                        "5",
                    ],
                    [
                        "skill-catalog",
                        "--root",
                        str(root),
                        "--query",
                        "python",
                        "--limit",
                        "5",
                    ],
                ),
                (
                    [
                        "workstation-skill-import",
                        "--root",
                        str(root),
                        "--skill-file",
                        str(skill_file),
                    ],
                    [
                        "skill-import",
                        "--root",
                        str(root),
                        "--skill-file",
                        str(skill_file),
                    ],
                ),
                (
                    [
                        "workstation-skill-export",
                        "--root",
                        str(root),
                        "--skill-title",
                        "Example Skill",
                    ],
                    [
                        "skill-export",
                        "--root",
                        str(root),
                        "--skill-title",
                        "Example Skill",
                    ],
                ),
                (
                    [
                        "workstation-trial-validate",
                        "--domains",
                        "symbolsearch",
                        "--workspace",
                        str(workspace),
                    ],
                    [
                        "trial-validate",
                        "--domains",
                        "symbolsearch",
                        "--workspace",
                        str(workspace),
                    ],
                ),
            )
            parser = build_workstation_parser()
            ignored = {"command", "workstation_action"}
            for historical_argv, package_argv in cases:
                with self.subTest(command=historical_argv[0]):
                    historical = vars(parse_historical_args(historical_argv))
                    package = vars(parser.parse_args(package_argv))
                    self.assertEqual(
                        {key: value for key, value in historical.items() if key not in ignored},
                        {key: value for key, value in package.items() if key not in ignored},
                    )


if __name__ == "__main__":
    unittest.main()
