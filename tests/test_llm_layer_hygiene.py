# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LLM_PACKAGE_ROOT = REPO_ROOT / "core_llm" / "src" / "realized_core_llm"
LLM_TRANSPORT = LLM_PACKAGE_ROOT / "transport.py"
LLM_LAYER_MODULES = (
    REPO_ROOT / "core_engine" / "src" / "realized_core_engine" / "prompt_directives.py",
    REPO_ROOT / "core_engine" / "src" / "realized_core_engine" / "supplement.py",
    REPO_ROOT / "external_markdown_learning_pipeline.py",
    REPO_ROOT
    / "core_engine"
    / "src"
    / "realized_core_engine"
    / "markdown_learning_artifact_semantics.py",
    REPO_ROOT / "core_engine" / "src" / "realized_core_engine" / "semantic_prompt_posture.py",
)
FORBIDDEN_LAYER_IMPORTS = {
    "approval_governance",
    "capability_runtime",
    "controller_governance_bridge",
    "data_governance",
    "governance_inventory",
    "governed_skill_access",
    "governed_skill_installation",
    "host_abi",
    "host_brokers",
    "host_mediation",
    "macos_host_brokers",
    "skill_governance",
    "skill_lifecycle",
    "skill_safety_governance",
    "virtual_mounts",
}


def module_import_roots(path: Path) -> set[str]:
    """
    High Level Purpose:
        In circumstances like architectural regression testing over the LLM layer, helps with extracting the imported module roots from one Python source file so forbidden layer couplings can be detected without executing the module.

    Reference to Theory:
        Verifies the five-layer architecture boundary by ensuring prompt and LLM modules stay free of governance and runtime-mediation imports.

    Example Input Output:
        Input: `module_import_roots(path=Path('/workspace/realized/supplement.py'))`
        Output: {'json', 'os', 're', 'urllib', 'applied_theory_types'}

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


def production_python_paths() -> tuple[Path, ...]:
    package_roots = (
        *REPO_ROOT.glob("*/src"),
        *REPO_ROOT.glob("workstation/*/src"),
    )
    paths = set(REPO_ROOT.glob("*.py"))
    for package_root in package_roots:
        paths.update(package_root.rglob("*.py"))
    return tuple(sorted(paths))


def dotted_name(node: ast.AST) -> str:
    names: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        names.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        names.append(current.id)
    return ".".join(reversed(names))


class LLMLayerHygieneTests(unittest.TestCase):
    def test_llm_layer_modules_do_not_import_governance_or_runtime_layers(self) -> None:
        """
        High Level Purpose:
            In circumstances like maintaining the five-layer architecture over time, helps with verifying that prompt construction and LLM-supplement modules do not directly depend on governance or runtime-mediation layers.

        Reference to Theory:
            Verifies the architecture boundary that keeps the LLM layer focused on prompt construction and proposal generation rather than on policy, approval, lifecycle, host mediation, or governed installation mechanics.

        Example Input Output:
            Input: `test_llm_layer_modules_do_not_import_governance_or_runtime_layers()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        for module_path in LLM_LAYER_MODULES:
            with self.subTest(module=str(module_path.name)):
                imported = module_import_roots(module_path)
                forbidden = sorted(imported & FORBIDDEN_LAYER_IMPORTS)
                self.assertEqual(
                    forbidden,
                    [],
                    msg=f"{module_path.name} imports forbidden layer modules: {', '.join(forbidden)}",
                )

    def test_only_llm_transport_imports_or_invokes_provider_sdk(self) -> None:
        sdk_importers: set[Path] = set()
        completion_callers: set[Path] = set()
        for path in production_python_paths():
            syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            if "openai" in module_import_roots(path):
                sdk_importers.add(path)
            for node in ast.walk(syntax):
                if isinstance(node, ast.Call) and dotted_name(node.func).endswith(
                    ".chat.completions.create"
                ):
                    completion_callers.add(path)

        self.assertEqual({LLM_TRANSPORT}, sdk_importers)
        self.assertEqual({LLM_TRANSPORT}, completion_callers)

    def test_llm_transport_consumers_use_the_package_abi(self) -> None:
        consumers = (
            REPO_ROOT / "core_engine" / "src" / "realized_core_engine" / "supplement.py",
            REPO_ROOT
            / "workstation"
            / "runtime_core"
            / "src"
            / "workstation"
            / "runtime"
            / "core"
            / "llm_driver.py",
        )
        for path in consumers:
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                syntax = ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(path),
                )
                imported_modules = {
                    node.module
                    for node in ast.walk(syntax)
                    if isinstance(node, ast.ImportFrom) and node.module
                }
                self.assertIn("realized_core_llm", imported_modules)
                self.assertNotIn("realized_core_llm.transport", imported_modules)
