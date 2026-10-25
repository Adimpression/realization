# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_RUNTIME_GOVERNANCE_IMPORTS = {
    "governed_skill_access",
    "skill_governance",
    "skill_lifecycle",
}


def module_import_roots(path: Path) -> set[str]:
    """
    High Level Purpose:
        In circumstances like architectural regression testing over the runtime layer, helps with extracting one module's import roots so forbidden low-level governance couplings can be detected without executing the module.

    Reference to Theory:
        Verifies the five-layer architecture by checking that runtime mediation depends on a runtime-governance facade instead of several low-level governance modules directly.

    Example Input Output:
        Input: `module_import_roots(path=Path('/workspace/realized/host_mediation.py'))`
        Output: {'json', 'hashlib', 'runtime_governance_context', 'host_brokers'}

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


class RuntimeLayerHygieneTests(unittest.TestCase):
    def test_host_mediation_uses_runtime_governance_facade(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining runtime and governance separation over time, helps with verifying that host mediation depends on the dedicated runtime-governance facade instead of several low-level governance modules directly.

        Reference to Theory:
            Verifies the five-layer architecture boundary that keeps runtime mediation broker-focused while governance resolution stays behind a narrower facade.

        Example Input Output:
            Input: `test_host_mediation_uses_runtime_governance_facade()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imported = module_import_roots(REPO_ROOT / "host_mediation.py")
        forbidden = sorted(imported & FORBIDDEN_RUNTIME_GOVERNANCE_IMPORTS)
        self.assertEqual(
            forbidden,
            [],
            msg=f"host_mediation.py imports forbidden low-level governance modules: {', '.join(forbidden)}",
        )
        self.assertIn(
            "runtime_governance_context",
            imported,
            msg="host_mediation.py should depend on runtime_governance_context for current-use governance resolution",
        )

    def test_system_state_uses_id_generation_not_main_for_runtime_ids(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing runtime-layer extraction, helps with verifying that runtime state id generation depends on a root helper module instead of importing controller composition from `main.py`.

        Reference to Theory:
            Verifies that runtime state construction stays below controller composition by sourcing generic identifier helpers from a lower shared module.

        Example Input Output:
            Input: `test_system_state_uses_id_generation_not_main_for_runtime_ids()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imported = module_import_roots(REPO_ROOT / "system_state.py")
        self.assertNotIn("main", imported)
        self.assertIn("id_generation", imported)

    def test_host_brokers_use_registered_runtime_binding_not_main_for_nested_skill_invoke(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing runtime-layer extraction, helps with verifying that nested governed skill invocation in host brokers depends on the registered controller constructor and root store helper instead of importing controller composition from `main.py`.

        Reference to Theory:
            Verifies that runtime broker execution stays on a narrow dependency-inversion boundary while using lower shared helpers for store access.

        Example Input Output:
            Input: `test_host_brokers_use_registered_runtime_binding_not_main_for_nested_skill_invoke()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imported = module_import_roots(REPO_ROOT / "host_brokers.py")
        self.assertNotIn("main", imported)
        self.assertIn("controller_runtime_binding", imported)
        self.assertNotIn("runtime_controller_api", imported)
        self.assertIn("store", imported)
