# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLLER_LAYER_MODULES = (
    REPO_ROOT / "controller_runtime.py",
)
SHARED_HOST_INTERACTION_MODULES = tuple(
    sorted(
        (
            REPO_ROOT
            / "host_interaction"
            / "src"
            / "realized_host_interaction"
        ).glob("*.py")
    )
)
RUNTIME_HOST_BACKEND_MODULES = (
    REPO_ROOT / "core_engine" / "src" / "realized_core_engine" / "host_mediation.py",
    REPO_ROOT / "core_engine" / "src" / "realized_core_engine" / "reduction_runtime.py",
)
WORKSTATION_RUNTIME_BOUNDARY_MODULES = (
    REPO_ROOT / "workstation" / "runtime_core" / "src" / "workstation" / "runtime" / "core" / "capabilities.py",
)
SUBJECT_TEXTUAL_ROOT = REPO_ROOT / "workstation" / "subject_textual" / "src" / "workstation" / "subject" / "textual"
FORBIDDEN_WORKSTATION_SHELL_IMPORT_ROOTS = {
    "workstation",
}


def module_import_roots(path: Path) -> set[str]:
    """
    High Level Purpose:
        In circumstances like six-layer boundary regression testing, helps with extracting one module's import roots so direct workstation-shell couplings can be detected without executing the module.

    Reference to Theory:
        Verifies the six-layer architecture rule that keeps controller and the packaged shared host-interaction substrate below workstation shell code.

    Example Input Output:
        Input: `module_import_roots(path=Path('/workspace/realized/controller_runtime.py'))`
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


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(str(alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(str(node.module))
    return imported


def compares_against_workstation_backend(path: Path) -> bool:
    """
    High Level Purpose:
        In circumstances like six-layer backend-boundary regression testing, helps with detecting whether one runtime-facing module branches directly on the workstation backend label instead of staying on the shared host-interaction contract.

    Reference to Theory:
        Verifies the six-layer rule that backend choice remains on the host-interaction contract boundary rather than as workstation-specific conditionals inside runtime-facing code.

    Example Input Output:
        Input: `compares_against_workstation_backend(path=Path('/workspace/realized/host_mediation.py'))`
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
    def test_shared_host_interaction_substrate_has_no_external_dependency(self) -> None:
        for module_path in SHARED_HOST_INTERACTION_MODULES:
            with self.subTest(module=str(module_path.relative_to(REPO_ROOT))):
                imported_roots = {
                    name.split(".", 1)[0]
                    for name in imported_module_names(module_path)
                }
                self.assertEqual(
                    [],
                    sorted(imported_roots - sys.stdlib_module_names),
                )

    def test_subject_textual_adapter_depends_only_on_contracts_and_local_models(self) -> None:
        allowed_workstation_prefixes = (
            "workstation.contracts",
            "workstation.subject.textual",
        )
        for module_path in sorted(SUBJECT_TEXTUAL_ROOT.glob("*.py")):
            with self.subTest(module=str(module_path.relative_to(REPO_ROOT))):
                imported = imported_module_names(module_path)
                forbidden_workstation = sorted(
                    name
                    for name in imported
                    if name == "workstation"
                    or (
                        name.startswith("workstation.")
                        and not name.startswith(allowed_workstation_prefixes)
                    )
                )
                forbidden_root_modules = sorted(
                    name
                    for name in imported
                    if name.split(".", 1)[0] not in sys.stdlib_module_names
                    and not name.startswith("workstation.")
                )
                self.assertEqual(forbidden_workstation, [])
                self.assertEqual(forbidden_root_modules, [])

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
                    "realized_host_interaction",
                    imported,
                    msg=f"{module_path.name} should use the shared host-interaction package for backend scope",
                )
                self.assertFalse(
                    compares_against_workstation_backend(module_path),
                    msg=f"{module_path.name} should not branch directly on the workstation backend label",
                )

    def test_workstation_runtime_bootstrap_uses_registered_runtime_contract_not_main(self) -> None:
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
                source = module_path.read_text(encoding="utf-8")
                self.assertNotIn(
                    "main",
                    imported,
                    msg=f"{module_path.name} should not import main directly for runtime bootstrap",
                )
                self.assertNotIn(
                    "runtime_controller_api",
                    imported,
                    msg=f"{module_path.name} should not depend on the root controller facade",
                )
                self.assertIn(
                    "from workstation.foundation.host.controller_runtime import controller_runtime_provider",
                    source,
                    msg=f"{module_path.name} should use the registered controller runtime contract",
                )
