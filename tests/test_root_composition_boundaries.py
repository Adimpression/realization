from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class RootCompositionBoundaryTests(unittest.TestCase):
    def _probe(self, source: str) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-c", source],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_canonical_controller_runtime_does_not_compose_entry_policy(self) -> None:
        result = self._probe(
            "\n".join(
                (
                    "import json",
                    "from realized_core_engine import controller_runtime",
                    "print(json.dumps({",
                    "    'has_parse_args': hasattr(controller_runtime, 'parse_args'),",
                    "    'has_artifact_export_document': hasattr(controller_runtime, 'artifact_export_document'),",
                    "    'has_markdown_extension': hasattr(controller_runtime.BSSCController, 'learn_from_markdown_document'),",
                    "}))",
                )
            )
        )
        self.assertEqual(
            result,
            {
                "has_parse_args": False,
                "has_artifact_export_document": False,
                "has_markdown_extension": False,
            },
        )

    def test_main_composes_the_historical_entry_surface_after_alias_import(self) -> None:
        result = self._probe(
            "\n".join(
                (
                    "import json",
                    "from realized_core_engine import controller_runtime",
                    "before = hasattr(controller_runtime, 'parse_args')",
                    "import main",
                    "print(json.dumps({",
                    "    'before': before,",
                    "    'same_module': main is controller_runtime,",
                    "    'has_parse_args': callable(main.parse_args),",
                    "    'has_artifact_export_document': callable(main.artifact_export_document),",
                    "    'has_markdown_extension': hasattr(main.BSSCController, 'learn_from_markdown_document'),",
                    "}))",
                )
            )
        )
        self.assertEqual(
            result,
            {
                "before": False,
                "same_module": True,
                "has_parse_args": True,
                "has_artifact_export_document": True,
                "has_markdown_extension": True,
            },
        )

    def test_itemize_is_a_pure_alias_for_explicit_port_itemization(self) -> None:
        result = self._probe(
            "\n".join(
                (
                    "import json",
                    "import itemize",
                    "from workstation.subject.core import itemization as canonical",
                    "print(json.dumps({",
                    "    'same_module': itemize is canonical,",
                    "    'same_extract': itemize.extract_itemized_candidates_from_learning_context is canonical.extract_itemized_candidates_from_learning_context,",
                    "    'same_materialize': itemize.materialize_itemization_session is canonical.materialize_itemization_session,",
                    "}))",
                )
            )
        )
        self.assertEqual(
            result,
            {
                "same_module": True,
                "same_extract": True,
                "same_materialize": True,
            },
        )

    def test_production_sources_do_not_execute_deleted_root_main_file(self) -> None:
        deleted_entrypoint = "main" + ".py"
        project_roots = [
            path.parent
            for path in REPO_ROOT.glob("*/pyproject.toml")
            if path.parent.name != "compatibility_api"
        ]
        project_roots.extend(
            path.parent
            for path in (REPO_ROOT / "workstation").glob("*/pyproject.toml")
            if path.parent.name != "compatibility_api"
        )
        source_paths = list(REPO_ROOT.glob("*.py"))
        for project_root in project_roots:
            source_paths.extend(project_root.rglob("*.py"))

        offenders: list[str] = []
        for path in sorted(set(source_paths)):
            relative = path.relative_to(REPO_ROOT)
            if "tests" in relative.parts or "build" in relative.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if any(
                isinstance(node, ast.Constant) and node.value == deleted_entrypoint
                for node in ast.walk(tree)
            ):
                offenders.append(str(relative))

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
