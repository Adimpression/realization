# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path("/Users/ravindranathakila/service/realized")
CONTROLLER_LAYER_MODULES = (
    REPO_ROOT / "main.py",
)
FORBIDDEN_CONTROLLER_IMPORTS = {
    "approval_governance",
    "governance_inventory",
    "governed_skill_access",
    "skill_governance",
    "skill_lifecycle",
    "skill_safety_governance",
}


def module_import_roots(path: Path) -> set[str]:
    """
    High Level Purpose:
        In circumstances like architectural regression testing over the controller layer, helps with extracting one module's import roots so direct low-level governance dependencies can be detected without executing the module.

    Reference to Theory:
        Verifies the five-layer architecture boundary by ensuring the controller depends on the governance bridge rather than on low-level governance inventory and admission modules directly.

    Example Input Output:
        Input: `module_import_roots(path=Path('/Users/ravindranathakila/service/realized/main.py'))`
        Output: {'json', 're', 'controller_governance_bridge', 'applied_theory_types'}

    Args:
        path: Value for `path` used by `module_import_roots`. Expected type: `Path`.

    Returns:
        set[str]: Result produced by `module_import_roots`.
    """
    tree = ast.parse(path.read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(str(alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(str(node.module).split(".")[0])
    return imported


class ControllerLayerHygieneTests(unittest.TestCase):
    def test_controller_layer_uses_bridge_not_low_level_governance_modules(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining controller and governance separation over time, helps with verifying that the controller entry module does not directly import low-level governance inventory, lifecycle, or admission modules.

        Reference to Theory:
            Verifies the five-layer architecture boundary that keeps the controller dependent on the governance bridge rather than on low-level governance implementation details.

        Example Input Output:
            Input: `test_controller_layer_uses_bridge_not_low_level_governance_modules()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        for module_path in CONTROLLER_LAYER_MODULES:
            with self.subTest(module=str(module_path.name)):
                imported = module_import_roots(module_path)
                forbidden = sorted(imported & FORBIDDEN_CONTROLLER_IMPORTS)
                self.assertEqual(
                    forbidden,
                    [],
                    msg=f"{module_path.name} imports forbidden low-level governance modules: {', '.join(forbidden)}",
                )
                self.assertIn(
                    "controller_governance_bridge",
                    imported,
                    msg=f"{module_path.name} should depend on controller_governance_bridge for controller/governance separation",
                )
