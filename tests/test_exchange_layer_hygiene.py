# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def module_import_map(path: Path) -> dict[str, set[str]]:
    """
    High Level Purpose:
        In circumstances like architectural regression testing over the entry/exchange layer, helps with extracting imported names by source module so layer boundaries can be asserted without executing the module.

    Reference to Theory:
        Verifies the five-layer architecture by checking that governed installation depends on the exchange/schema surface for portable skill documents rather than on mixed exchange-export internals.

    Example Input Output:
        Input: `module_import_map(path=Path('/Users/ravindranathakila/service/realized/governed_skill_installation.py'))`
        Output: {'skill_schema_io': {'artifact_from_skill_document', 'resolve_import_skill_files'}, 'skill_export_projection': {'export_skill_bundle_text'}}

    Args:
        path: Value for `path` used by `module_import_map`. Expected type: `Path`.

    Returns:
        dict[str, set[str]]: Result produced by `module_import_map`.
    """
    tree = ast.parse(path.read_text())
    imported: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.setdefault(str(node.module), set()).update(str(alias.name) for alias in node.names)
    return imported


def module_import_roots(path: Path) -> set[str]:
    """
    High Level Purpose:
        In circumstances like exchange-layer extraction regression testing, helps with extracting one module's direct import roots so reach-throughs to `main.py` can be detected without executing the module.

    Reference to Theory:
        Verifies that exchange-facing modules depend on narrower root helpers instead of importing controller/runtime composition directly.

    Example Input Output:
        Input: `module_import_roots(path=Path('/Users/ravindranathakila/service/realized/skill_registry.py'))`
        Output: {'json', 'artifact', 'store', 'skill_export_projection'}

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


class ExchangeLayerHygieneTests(unittest.TestCase):
    def test_governed_skill_installation_uses_skill_schema_io_for_schema_hydration(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining entry/exchange separation over time, helps with verifying that governed skill installation pulls portable skill schema hydration helpers from the dedicated exchange/schema module instead of from the broader skill export surface.

        Reference to Theory:
            Verifies the five-layer architecture boundary that keeps installation dependent on exchange/schema hydration for document loading while allowing artifact construction to pass through the dedicated compiler surface.

        Example Input Output:
            Input: `test_governed_skill_installation_uses_skill_schema_io_for_schema_hydration()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_map(REPO_ROOT / "governed_skill_installation.py")
        schema_imports = imports.get("skill_schema_io", set())
        self.assertTrue(
            {
                "_runtime",
                "load_skill_yaml_payload_documents",
                "normalized_skill_bundle_filename_for_source",
                "resolve_import_skill_files",
            }.issubset(schema_imports)
        )
        compiler_imports = imports.get("skill_compiler", set())
        self.assertTrue(
            {
                "compile_skill_document",
                "compiled_skill_summary_from_artifact",
            }.issubset(compiler_imports)
        )
        skill_io_imports = imports.get("skill_io", set())
        self.assertFalse(
            {
                "_runtime",
                "load_skill_yaml_payload_documents",
                "normalized_skill_bundle_filename_for_source",
                "resolve_import_skill_files",
            } & skill_io_imports,
            msg="governed_skill_installation should no longer source schema hydration helpers from skill_io",
        )

    def test_governed_skill_installation_uses_skill_export_projection_for_export_projection(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining exchange-layer separation over time, helps with verifying that governed skill installation sources portable export projection from the dedicated export module instead of from the compatibility shell.

        Reference to Theory:
            Verifies the five-layer architecture boundary that keeps installation dependent on the narrower exchange/export surface rather than on mixed compatibility glue.

        Example Input Output:
            Input: `test_governed_skill_installation_uses_skill_export_projection_for_export_projection()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_map(REPO_ROOT / "governed_skill_installation.py")
        projection_imports = imports.get("skill_export_projection", set())
        self.assertTrue(
            {
                "export_skill_bundle_text",
                "skill_kind_from_artifact",
            }.issubset(projection_imports)
        )
        self.assertFalse(
            {
                "_skill_kind_from_artifact",
                "export_skill_bundle_text",
                "skill_kind_from_artifact",
            } & imports.get("skill_io", set()),
            msg="governed_skill_installation should no longer source export projection from skill_io",
        )

    def test_exchange_entrypoints_and_replay_paths_use_skill_export_projection(self) -> None:
        """
        High Level Purpose:
            In circumstances like preventing the exchange layer from drifting back toward the compatibility shell, helps with verifying that entrypoints, replay export, and registry projection all depend on the dedicated export module.

        Reference to Theory:
            Verifies the five-layer architecture boundary that keeps core exchange/export paths on the narrower projection surface instead of the broad compatibility facade.

        Example Input Output:
            Input: `test_exchange_entrypoints_and_replay_paths_use_skill_export_projection()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        module_expectations = {
            REPO_ROOT / "controller_entrypoints.py": {"handle_export_skill_command"},
            REPO_ROOT / "run_bundle_io.py": {"skill_export_document"},
            REPO_ROOT / "skill_registry.py": {"skill_export_document"},
        }
        for path, expected_names in module_expectations.items():
            imports = module_import_map(path)
            self.assertTrue(
                expected_names.issubset(imports.get("skill_export_projection", set())),
                msg=f"{path.name} should import {sorted(expected_names)} from skill_export_projection",
            )
            self.assertFalse(
                expected_names & imports.get("skill_io", set()),
                msg=f"{path.name} should no longer import {sorted(expected_names)} from skill_io",
            )

    def test_skill_registry_uses_root_helpers_not_main_for_registry_export(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing exchange-layer extraction, helps with verifying that skill registry export depends on narrower root helpers instead of importing controller/runtime composition from `main.py`.

        Reference to Theory:
            Verifies that exchange-facing registry export stays on the exchange/root-helper surface rather than reaching into controller/runtime composition directly.

        Example Input Output:
            Input: `test_skill_registry_uses_root_helpers_not_main_for_registry_export()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_roots(REPO_ROOT / "skill_registry.py")
        self.assertNotIn("main", imports)
        self.assertIn("artifact", imports)
        self.assertIn("store", imports)

    def test_skill_schema_io_uses_root_helpers_not_main_for_schema_hydration(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing exchange-layer extraction, helps with verifying that skill schema hydration depends on narrower root helpers instead of importing controller/runtime composition from `main.py`.

        Reference to Theory:
            Verifies that exchange-facing schema hydration stays on root helper modules and semantic normalization surfaces rather than reaching into controller/runtime composition directly.

        Example Input Output:
            Input: `test_skill_schema_io_uses_root_helpers_not_main_for_schema_hydration()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_roots(REPO_ROOT / "skill_schema_io.py")
        self.assertNotIn("main", imports)
        self.assertIn("artifact", imports)
        self.assertIn("semantic_text", imports)

    def test_replay_verifier_uses_runtime_facade_not_main_for_replay_bootstrap(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing replay-path extraction, helps with verifying that run-bundle replay depends on the runtime facade and root helpers instead of importing controller/runtime composition from `main.py`.

        Reference to Theory:
            Verifies that replay verification stays on a narrower runtime contract boundary while using root helpers for store construction.

        Example Input Output:
            Input: `test_replay_verifier_uses_runtime_facade_not_main_for_replay_bootstrap()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_roots(REPO_ROOT / "replay_verifier.py")
        self.assertNotIn("main", imports)
        self.assertIn("runtime_controller_api", imports)
        self.assertIn("store", imports)
