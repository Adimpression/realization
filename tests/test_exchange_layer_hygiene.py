# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_ROOT = REPO_ROOT / "compatibility_api" / "src"


def module_import_map(path: Path) -> dict[str, set[str]]:
    """
    High Level Purpose:
        In circumstances like architectural regression testing over the entry/exchange layer, helps with extracting imported names by source module so layer boundaries can be asserted without executing the module.

    Reference to Theory:
        Verifies the six-layer architecture by checking that governed installation depends on the canonical exchange/schema surface for portable skill documents rather than on compatibility facades.

    Example Input Output:
        Input: `module_import_map(path=Path('/workspace/realized/governed_skill_installation.py'))`
        Output: {'realized_exchange.skill_schema': {'artifact_from_skill_document', 'resolve_import_skill_files'}, 'realized_exchange.skill_export': {'export_skill_bundle_text'}}

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
        Input: `module_import_roots(path=Path('/workspace/realized/skill_registry.py'))`
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
            Verifies the six-layer architecture boundary that keeps installation dependent on canonical exchange/schema hydration for document loading while allowing artifact construction to pass through the dedicated compiler surface.

        Example Input Output:
            Input: `test_governed_skill_installation_uses_skill_schema_io_for_schema_hydration()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_map(
            COMPATIBILITY_ROOT / "governed_skill_installation.py"
        )
        schema_imports = imports.get("realized_exchange.skill_schema", set())
        self.assertTrue(
            {
                "_runtime",
                "load_skill_yaml_payload_documents",
                "normalized_skill_bundle_filename_for_source",
                "resolve_import_skill_files",
            }.issubset(schema_imports)
        )
        compiler_imports = imports.get("realized_exchange.compiler", set())
        self.assertTrue(
            {
                "compile_skill_document",
                "compiled_skill_summary_from_artifact",
            }.issubset(compiler_imports)
        )
        self.assertFalse(
            {
                "_runtime",
                "load_skill_yaml_payload_documents",
                "normalized_skill_bundle_filename_for_source",
                "resolve_import_skill_files",
            } & imports.get("skill_schema_io", set()),
            msg="governed_skill_installation must not source schema hydration through the compatibility facade",
        )
        self.assertNotIn(
            "skill_compiler",
            imports,
            msg="governed_skill_installation must not import the compiler compatibility facade",
        )

    def test_governed_skill_installation_uses_skill_export_projection_for_export_projection(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining exchange-layer separation over time, helps with verifying that governed skill installation sources portable export projection from the dedicated export module instead of from the compatibility shell.

        Reference to Theory:
            Verifies the six-layer architecture boundary that keeps installation dependent on the canonical exchange/export surface rather than on compatibility glue.

        Example Input Output:
            Input: `test_governed_skill_installation_uses_skill_export_projection_for_export_projection()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_map(
            COMPATIBILITY_ROOT / "governed_skill_installation.py"
        )
        projection_imports = imports.get("realized_exchange.skill_export", set())
        self.assertTrue(
            {"export_skill_bundle_text"}.issubset(projection_imports)
        )
        self.assertIn(
            "skill_kind_from_artifact",
            imports.get("realized_skill_application.projection", set()),
        )
        self.assertFalse(
            {
                "_skill_kind_from_artifact",
                "export_skill_bundle_text",
                "skill_kind_from_artifact",
            } & imports.get("skill_export_projection", set()),
            msg="governed_skill_installation must not source projection through the compatibility facade",
        )

    def test_exchange_entrypoints_and_replay_paths_use_skill_export_projection(self) -> None:
        """
        High Level Purpose:
            In circumstances like preventing the exchange layer from drifting back toward the compatibility shell, helps with verifying that entrypoints, replay export, and registry projection all depend on the dedicated export module.

        Reference to Theory:
            Verifies the six-layer architecture boundary that keeps core exchange/export paths on the canonical exchange package instead of the historical compatibility facade.

        Example Input Output:
            Input: `test_exchange_entrypoints_and_replay_paths_use_skill_export_projection()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        module_expectations = {
            COMPATIBILITY_ROOT / "controller_entrypoints.py": {
                "handle_export_skill_command"
            },
            REPO_ROOT
            / "exchange"
            / "src"
            / "realized_exchange"
            / "run_bundle.py": {"skill_export_document"},
            REPO_ROOT
            / "exchange"
            / "src"
            / "realized_exchange"
            / "registry.py": {"skill_export_document"},
        }
        for path, expected_names in module_expectations.items():
            imports = module_import_map(path)
            self.assertTrue(
                expected_names.issubset(imports.get("realized_exchange.skill_export", set())),
                msg=f"{path.name} should import {sorted(expected_names)} from realized_exchange.skill_export",
            )
            self.assertFalse(
                expected_names & imports.get("skill_export_projection", set()),
                msg=f"{path.name} must not import {sorted(expected_names)} through the compatibility facade",
            )

    def test_skill_registry_uses_package_apis_not_main_for_registry_export(self) -> None:
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
        imports = module_import_roots(
            REPO_ROOT / "exchange" / "src" / "realized_exchange" / "registry.py"
        )
        self.assertNotIn("main", imports)
        self.assertNotIn("artifact", imports)
        self.assertNotIn("store", imports)
        self.assertIn("realized_core_semantics", imports)
        self.assertIn("realized_core_engine", imports)

    def test_skill_schema_io_uses_canonical_semantics_not_main_for_schema_hydration(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing exchange-layer extraction, helps with verifying that skill schema hydration depends on canonical semantic helpers instead of importing controller/runtime composition from `main.py`.

        Reference to Theory:
            Verifies that exchange-facing schema hydration stays on the semantic package rather than reaching into controller/runtime composition directly.

        Example Input Output:
            Input: `test_skill_schema_io_uses_canonical_semantics_not_main_for_schema_hydration()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_roots(
            REPO_ROOT / "exchange" / "src" / "realized_exchange" / "skill_schema.py"
        )
        self.assertNotIn("main", imports)
        self.assertNotIn("artifact", imports)
        self.assertNotIn("store", imports)
        self.assertNotIn("semantic_text", imports)
        self.assertIn("realized_core_semantics", imports)
        self.assertIn("realized_core_engine", imports)

    def test_replay_verifier_uses_engine_controller_not_entry_composition(self) -> None:
        """
        High Level Purpose:
            In circumstances like continuing replay-path extraction, helps with verifying that run-bundle replay constructs the controller from the engine boundary instead of importing executable workstation or `main.py` composition.

        Reference to Theory:
            Verifies that replay verification stays on the engine boundary for an already reconstructed state and does not depend upward on entry composition.

        Example Input Output:
            Input: `test_replay_verifier_uses_engine_controller_not_entry_composition()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        imports = module_import_roots(COMPATIBILITY_ROOT / "replay_verifier.py")
        self.assertNotIn("main", imports)
        self.assertNotIn("constitutional_trace", imports)
        self.assertNotIn("run_bundle_io", imports)
        self.assertNotIn("runtime_controller_api", imports)
        self.assertNotIn("workstation", imports)
        self.assertNotIn("store", imports)
        self.assertIn("realized_core_engine", imports)
        self.assertIn("realized_exchange", imports)
