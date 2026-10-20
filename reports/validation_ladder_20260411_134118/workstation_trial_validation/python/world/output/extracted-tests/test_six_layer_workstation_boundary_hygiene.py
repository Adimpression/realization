# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path("/Users/ravindranathakila/service/realized")
CONTROLLER_LAYER_MODULES = (
    REPO_ROOT / "main.py",
)
SHARED_HOST_INTERACTION_MODULES = tuple(sorted(REPO_ROOT.glob("host_interaction_*.py")))
RUNTIME_HOST_BACKEND_MODULES = (
    REPO_ROOT / "host_mediation.py",
    REPO_ROOT / "governed_semantic_reduction_runtime.py",
)
WORKSTATION_RUNTIME_BOUNDARY_MODULES = (
    REPO_ROOT / "workstation" / "capabilities.py",
)
FORBIDDEN_WORKSTATION_SHELL_IMPORT_ROOTS = {
    "workstation",
}


def module_import_roots(path: Path) -> set[str]:
    """
    High Level Purpose:
        In circumstances like six-layer boundary regression testing, helps with extracting one module's import roots so direct workstation-shell couplings can be detected without executing the module.

    Reference to Theory:
        Verifies the six-layer architecture rule that keeps controller and shared host-interaction substrate below workstation shell code.

    Example Input Output:
        Input: `module_import_roots(path=Path('/Users/ravindranathakila/service/realized/main.py'))`
        Output: {'json', 're', 'controller_governance_bridge', 'host_interaction_context'}

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


def compares_against_workstation_backend(path: Path) -> bool:
    """
    High Level Purpose:
        In circumstances like six-layer backend-boundary regression testing, helps with detecting whether one runtime-facing module branches directly on the workstation backend label instead of staying on the shared host-interaction contract.

    Reference to Theory:
        Verifies the six-layer rule that backend choice remains on the host-interaction contract boundary rather than as workstation-specific conditionals inside runtime-facing code.

    Example Input Output:
        Input: `compares_against_workstation_backend(path=Path('/Users/ravindranathakila/service/realized/host_mediation.py'))`
        Output: False

    Args:
        path: Value for `path` used by `compares_against_workstation_backend`. Expected type: `Path`.

    Returns:
        bool: Result produced by `compares_against_workstation_backend`.
    """
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            left_values = [node.left, *node.comparators]
            for candidate in left_values:
                if isinstance(candidate, ast.Constant) and candidate.value == "workstation":
                    return True
        elif isinstance(node, ast.MatchValue):
            if isinstance(node.value, ast.Constant) and node.value.value == "workstation":
                return True
    return False


class SixLayerWorkstationBoundaryHygieneTests(unittest.TestCase):
    def test_controller_layer_does_not_import_workstation_shell_modules(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining controller and workstation separation over time, helps with verifying that controller modules do not directly depend on workstation shell packages.

        Reference to Theory:
            Verifies the six-layer architecture boundary that keeps controller reasoning independent from workstation session, chat, or CLI code.

        Example Input Output:
            Input: `test_controller_layer_does_not_import_workstation_shell_modules()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        for module_path in CONTROLLER_LAYER_MODULES:
            with self.subTest(module=str(module_path.name)):
                imported = module_import_roots(module_path)
                forbidden = sorted(imported & FORBIDDEN_WORKSTATION_SHELL_IMPORT_ROOTS)
                self.assertEqual(
                    forbidden,
                    [],
                    msg=f"{module_path.name} imports forbidden workstation shell modules: {', '.join(forbidden)}",
                )

    def test_shared_host_interaction_substrate_does_not_import_workstation_shell_modules(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining the shared host-interaction seam below the workstation shell, helps with verifying that root-level host interaction modules do not import workstation packages directly.

        Reference to Theory:
            Verifies the six-layer architecture rule that keeps chat, session, and CLI code out of the shared substrate.

        Example Input Output:
            Input: `test_shared_host_interaction_substrate_does_not_import_workstation_shell_modules()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        for module_path in SHARED_HOST_INTERACTION_MODULES:
            with self.subTest(module=str(module_path.name)):
                imported = module_import_roots(module_path)
                forbidden = sorted(imported & FORBIDDEN_WORKSTATION_SHELL_IMPORT_ROOTS)
                self.assertEqual(
                    forbidden,
                    [],
                    msg=f"{module_path.name} imports forbidden workstation shell modules: {', '.join(forbidden)}",
                )

    def test_runtime_backend_selection_stays_on_shared_contract_boundary(self) -> None:
        """
        High Level Purpose:
            In circumstances like preventing runtime/backend drift over time, helps with verifying that runtime-facing modules use shared host-interaction helpers without branching directly on the workstation backend label.

        Reference to Theory:
            Verifies the six-layer architecture rule that runtime/backend selection remains on the shared host-interaction contract boundary rather than as workstation-specific logic inside runtime-facing code.

        Example Input Output:
            Input: `test_runtime_backend_selection_stays_on_shared_contract_boundary()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        for module_path in RUNTIME_HOST_BACKEND_MODULES:
            with self.subTest(module=str(module_path.name)):
                imported = module_import_roots(module_path)
                self.assertIn(
                    "host_interaction_context",
                    imported,
                    msg=f"{module_path.name} should use shared host_interaction_context helpers for backend scope",
                )
                self.assertFalse(
                    compares_against_workstation_backend(module_path),
                    msg=f"{module_path.name} should not branch directly on the workstation backend label",
                )

    def test_workstation_runtime_bootstrap_uses_runtime_facade_not_main(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing six-layer extraction, helps with verifying that workstation runtime bootstrap goes through the narrow runtime facade instead of importing `main.py` directly from workstation shell code.

        Reference to Theory:
            Verifies the six-layer rule that workstation should depend on a lower runtime contract rather than reaching into controller/runtime internals directly.

        Example Input Output:
            Input: `test_workstation_runtime_bootstrap_uses_runtime_facade_not_main()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        for module_path in WORKSTATION_RUNTIME_BOUNDARY_MODULES:
            with self.subTest(module=str(module_path.name)):
                imported = module_import_roots(module_path)
                self.assertNotIn(
                    "main",
                    imported,
                    msg=f"{module_path.name} should not import main directly for runtime bootstrap",
                )
                self.assertIn(
                    "runtime_controller_api",
                    imported,
                    msg=f"{module_path.name} should use runtime_controller_api for runtime bootstrap",
                )
