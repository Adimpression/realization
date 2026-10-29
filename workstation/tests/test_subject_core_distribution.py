from __future__ import annotations

import ast
from pathlib import Path
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "workstation" / "subject_core"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "workstation" / "subject" / "core"


def _absolute_imports(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module)
    return imported


class SubjectCoreDistributionTests(unittest.TestCase):
    def test_project_discovers_the_canonical_subject_package(self) -> None:
        metadata = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual(
            {"": "src"},
            metadata["tool"]["setuptools"]["package-dir"],
        )
        self.assertEqual(
            ["workstation.subject.core"],
            metadata["tool"]["setuptools"]["packages"]["find"]["include"],
        )
        self.assertTrue((PACKAGE_ROOT / "decision_review.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "decision_review_constructs.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "itemization.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "learning_context.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "learning_context_markdown.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "learning_context_paths.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "learning_context_projection.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "review_composition.py").is_file())

    def test_subject_core_does_not_import_migrated_root_facades(self) -> None:
        forbidden = {
            "decision_review",
            "decision_review_constructs",
            "itemize",
            "learning_context",
            "learning_context_markdown",
            "learning_context_paths",
            "learning_context_projection",
            "review_composition",
        }
        importing_paths = {
            (
                path.relative_to(REPO_ROOT).as_posix(),
                tuple(
                    sorted(
                        {
                            *forbidden,
                        }
                        & _absolute_imports(path)
                    )
                ),
            )
            for path in PACKAGE_ROOT.glob("*.py")
            if forbidden & _absolute_imports(path)
        }

        self.assertEqual(set(), importing_paths)

    def test_canonical_itemization_has_no_controller_or_proposal_implementation_import(self) -> None:
        imported = _absolute_imports(PACKAGE_ROOT / "itemization.py")

        self.assertTrue(
            {
                "applied_theory_types",
                "runtime_controller_api",
            }.isdisjoint(imported)
        )

    def test_learning_context_has_an_explicit_public_surface(self) -> None:
        path = PACKAGE_ROOT / "learning_context.py"
        syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        public = next(
            (
                ast.literal_eval(node.value)
                for node in syntax.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in node.targets
                )
            ),
            None,
        )

        self.assertIsInstance(public, list)
        assert isinstance(public, list)
        self.assertEqual(len(public), len(set(public)))
        self.assertIn("LearningContext", public)
        self.assertIn("apply_learning_delta", public)

    def test_canonical_learning_context_does_not_import_projection_implementations(self) -> None:
        imported = _absolute_imports(PACKAGE_ROOT / "learning_context.py")

        self.assertTrue(
            {
                "learning_context_projection",
                "learning_context_skill_projection",
                "skill_compiler",
                "skill_export_projection",
            }.isdisjoint(imported)
        )

    def test_learning_context_paths_has_an_explicit_public_surface(self) -> None:
        path = PACKAGE_ROOT / "learning_context_paths.py"
        syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        public = next(
            (
                ast.literal_eval(node.value)
                for node in syntax.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in node.targets
                )
            ),
            None,
        )

        self.assertIsInstance(public, list)
        assert isinstance(public, list)
        self.assertEqual(len(public), len(set(public)))
        self.assertEqual(
            {
                "canonical_learning_subject_id",
                "decision_review_paths",
                "ensure_learning_context_home",
                "learning_context_home",
                "learning_context_paths",
                "learning_corpus_root",
                "learning_source_bundle_root",
                "resolve_learning_context_root",
            },
            set(public),
        )

    def test_cloud_build_runs_the_subject_core_distribution_guard(self) -> None:
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn(
            "workstation.tests.test_subject_core_distribution",
            cloud_build,
        )


if __name__ == "__main__":
    unittest.main()
