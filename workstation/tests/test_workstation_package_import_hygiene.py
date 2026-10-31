# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSTATION_ROOT = REPO_ROOT / "workstation"
APPROVED_FLAT_WORKSTATION_MODULES = {
    "__init__.py",
}
LEGACY_FLAT_WORKSTATION_MODULES = {
    "activity_view",
    "builtin_skills",
    "capabilities",
    "chat_commands",
    "chat_shell",
    "chat_ui",
    "cli",
    "client_sessions",
    "colors",
    "delegation",
    "direct_composition",
    "desktop_file_dialogs",
    "event_bus",
    "governance",
    "host_interaction",
    "layout",
    "learning_capture",
    "llm_driver",
    "message_tracing",
    "mock_subject_workflow",
    "models",
    "projection_models",
    "shell_prompt_routing",
    "session",
    "skill_composition_planning",
    "skill_home",
    "skill_invocation",
    "skill_management",
    "subject_workflow",
    "subject_workflow_api",
    "subject_workflow_client",
    "subject_workflow_grpc",
    "subject_workflow_repository",
    "subject_workflow_state_transitions",
    "subject_workflow_textual_backend",
    "subscriber_controllers",
    "task_contract",
    "theme",
    "trial_validation",
    "workstation_core",
    "workstation_grpc_host",
    "workstation_shell_api",
    "workstation_shell_backend",
    "workstation_shell_client",
    "workstation_shell_grpc",
    "protos",
}
UI_CLIENT_ROOTS = (
    WORKSTATION_ROOT / "ui_textual",
    WORKSTATION_ROOT / "subject_textual",
)
REMOVED_FLET_PATHS = (
    WORKSTATION_ROOT / "ui_flet",
    WORKSTATION_ROOT / "tests" / "test_workstation_flet_host.py",
)
SUPPORTED_CLIENT_DRIFT_PATHS = (
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "compatibility_api" / "src" / "args.py",
    REPO_ROOT / "compatibility_api" / "src" / "controller_entrypoints.py",
    WORKSTATION_ROOT / "WORKSTATION.md",
    WORKSTATION_ROOT / "RESEARCH_AND_PUBLISH_FLOW.md",
    WORKSTATION_ROOT / "RESEARCH_AND_PUBLISH_FLOW_IMPLEMENTATION.md",
    WORKSTATION_ROOT / "app_cli" / "pyproject.toml",
    WORKSTATION_ROOT / "app_cli" / "src" / "realized_workstation_app_cli.egg-info" / "PKG-INFO",
    WORKSTATION_ROOT / "app_cli" / "src" / "realized_workstation_app_cli.egg-info" / "requires.txt",
)


def iter_repo_python_files() -> list[Path]:
    paths: list[Path] = []
    for base in (REPO_ROOT / "workstation", REPO_ROOT / "tests"):
        paths.extend(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)
    paths.append(
        REPO_ROOT / "compatibility_api" / "src" / "controller_entrypoints.py"
    )
    paths.append(REPO_ROOT / "tests" / "test_host_interaction_context.py")
    paths.append(REPO_ROOT / "tests" / "test_host_mediation.py")
    return sorted(dict.fromkeys(path for path in paths if path.exists()))


def imported_workstation_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = str(alias.name)
                if module == "workstation" or module.startswith("workstation."):
                    imported.add(module)
        elif isinstance(node, ast.ImportFrom) and node.module:
            module = str(node.module)
            if module == "workstation" or module.startswith("workstation."):
                imported.add(module)
    return imported


def imports_direct_runtime_workflow_actions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    direct_actions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "workstation.runtime.core.workstation_core":
            for alias in node.names:
                if alias.name in {"workstation_learn_markdown_action", "workstation_learn_url_action"}:
                    direct_actions.add(str(alias.name))
    return direct_actions


class WorkstationPackageImportHygieneTests(unittest.TestCase):
    def test_only_approved_flat_workstation_modules_remain(self) -> None:
        flat_python_files = {path.name for path in WORKSTATION_ROOT.glob("*.py")}
        self.assertEqual(flat_python_files, APPROVED_FLAT_WORKSTATION_MODULES)

    def test_namespace_distribution_contains_only_the_namespace_initializer(self) -> None:
        namespace_root = WORKSTATION_ROOT / "namespace" / "src" / "workstation"
        self.assertEqual(
            {"__init__.py"},
            {path.name for path in namespace_root.glob("*.py")},
        )

    def test_namespace_initializers_do_not_eagerly_import_components(self) -> None:
        initializers = (
            WORKSTATION_ROOT / "__init__.py",
            WORKSTATION_ROOT / "namespace" / "src" / "workstation" / "__init__.py",
        )
        for path in initializers:
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                self.assertEqual(set(), imported_workstation_modules(path))

    def test_code_does_not_import_retired_flat_workstation_modules(self) -> None:
        for path in iter_repo_python_files():
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                legacy_imports = sorted(
                    module
                    for module in imported_workstation_modules(path)
                    if module.startswith("workstation.")
                    and module.split(".", 2)[1] in LEGACY_FLAT_WORKSTATION_MODULES
                )
                self.assertEqual(
                    legacy_imports,
                    [],
                    msg=f"{path.relative_to(REPO_ROOT)} imports legacy flat workstation modules: {', '.join(legacy_imports)}",
                )

    def test_ui_clients_do_not_import_direct_runtime_workflow_actions(self) -> None:
        for base in UI_CLIENT_ROOTS:
            for path in sorted(base.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                    self.assertEqual(
                        sorted(imports_direct_runtime_workflow_actions(path)),
                        [],
                        msg=(
                            f"{path.relative_to(REPO_ROOT)} imports direct runtime workflow actions instead of "
                            "going through the canonical gRPC-backed workflow contract."
                        ),
                    )

    def test_removed_flet_paths_are_absent(self) -> None:
        for path in REMOVED_FLET_PATHS:
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                self.assertFalse(path.exists(), msg=f"{path.relative_to(REPO_ROOT)} should be removed.")

    def test_supported_client_docs_and_packaging_do_not_reference_flet(self) -> None:
        for path in SUPPORTED_CLIENT_DRIFT_PATHS:
            if not path.exists():
                continue
            text = path.read_text()
            with self.subTest(path=str(path.relative_to(REPO_ROOT))):
                self.assertNotIn("workstation-flet", text)
                self.assertNotIn("realized-workstation-ui-flet", text)
                self.assertNotIn("workstation/ui_flet", text)
                self.assertNotIn("flet_host", text)
