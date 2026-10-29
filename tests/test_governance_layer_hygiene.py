# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
def _canonical_production_modules() -> tuple[Path, ...]:
    root_modules = tuple(
        path
        for path in REPO_ROOT.glob("*.py")
        if path.name != "skill_governance.py"
    )
    workstation_modules = tuple(
        path
        for path in (REPO_ROOT / "workstation").glob("*/src/**/*.py")
    )
    return root_modules + workstation_modules


class GovernanceLayerHygieneTests(unittest.TestCase):
    def test_canonical_production_does_not_import_skill_governance_facade(self) -> None:
        violations: list[str] = []

        for path in _canonical_production_modules():
            syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(syntax):
                if not isinstance(node, ast.ImportFrom) or node.module != "skill_governance":
                    continue
                relative = path.relative_to(REPO_ROOT)
                violations.append(str(relative))

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
