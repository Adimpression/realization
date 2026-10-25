from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
import textwrap
import tomllib
import unittest
from email.parser import Parser
from pathlib import Path

import gather_sources


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_architecture_boundaries.py"
SPEC = importlib.util.spec_from_file_location("check_architecture_boundaries", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
architecture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(architecture)


class RepositoryArchitectureBoundaryTest(unittest.TestCase):
    @staticmethod
    def _exported_names(path: Path) -> set[str]:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for statement in module.body:
            if not isinstance(statement, ast.Assign):
                continue
            if not any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in statement.targets
            ):
                continue
            value = ast.literal_eval(statement.value)
            return {str(name) for name in value}
        raise AssertionError(f"{path} does not declare __all__")

    def test_google_cloud_build_runs_the_architecture_and_trial_ratchets(self) -> None:
        build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")
        trigger = (REPO_ROOT / "cloudbuild_trigger.tf").read_text(encoding="utf-8")
        gcloudignore = (REPO_ROOT / ".gcloudignore").read_text(encoding="utf-8")
        architecture_test_step = build.split(
            "id: 'architecture-ratchet-tests'", 1
        )[1].split("id: 'deterministic-trial-bdd'", 1)[0]

        self.assertIn("id: 'architecture-ratchet'", build)
        self.assertIn("args: ['scripts/check_architecture_boundaries.py']", build)
        self.assertIn("id: 'architecture-ratchet-tests'", build)
        self.assertIn("uv sync --frozen", architecture_test_step)
        self.assertIn("uv build --wheel host_interaction", architecture_test_step)
        self.assertIn("uv build core_runtime", architecture_test_step)
        self.assertIn(
            "uv run --frozen python -m unittest",
            architecture_test_step,
        )
        self.assertIn("tests.test_architecture_boundaries", build)
        self.assertIn("tests.test_side_boundary_extraction", build)
        self.assertIn(
            "workstation.tests.test_workstation_package_import_hygiene",
            build,
        )
        self.assertIn("tests.test_runtime_layer_hygiene", build)
        self.assertIn("tests.test_controller_layer_hygiene", build)
        self.assertIn("tests.test_llm_layer_hygiene", build)
        self.assertIn("tests.test_exchange_layer_hygiene", build)
        self.assertIn("tests.test_artifact_boundary_shape", build)
        self.assertIn("tests.test_boundary_shape_typing", build)
        self.assertIn("tests.test_function_boundary", build)
        self.assertIn("tests.test_skill_boundary_normalization", build)
        self.assertIn(
            "workstation.tests.test_six_layer_workstation_boundary_hygiene",
            build,
        )
        self.assertIn("id: 'deterministic-trial-bdd'", build)
        self.assertIn("uv==0.10.10", build)
        self.assertIn("workstation.tests.bdd.test_report_creation_bdd", build)
        self.assertIn(
            "workstation.tests.bdd.test_smart_city_travel_incremental_report_ladder_bdd",
            build,
        )
        self.assertIn("workstation.tests.bdd.test_trial_skill_routing_bdd", build)
        self.assertIn("tests.test_architecture_compatibility_facades", build)
        self.assertIn("workstation.tests.test_workstation_activity_view", build)
        self.assertIn(
            "test_load_current_workstation_session_does_not_rewrite_discovery_files",
            build,
        )
        self.assertIn(
            "test_load_legacy_workstation_session_persists_attachment_upgrade",
            build,
        )
        self.assertIn(
            "test_workstation_chat_context_reads_workspace_and_skill_inventory",
            build,
        )
        self.assertIn("OPENAI_API_KEY=", build)
        self.assertNotIn("dir: 'realized'", build)
        self.assertIn('name        = "realization-github"', trigger)
        self.assertIn('filename = "cloudbuild.yaml"', trigger)
        self.assertIn("github {", trigger)
        self.assertIn("owner = var.github_owner", trigger)
        self.assertIn("name  = var.github_repository", trigger)
        self.assertIn('"**"', trigger)
        self.assertIn("prevent_destroy = true", trigger)
        self.assertIn(".git/**", gcloudignore)
        self.assertIn("**/*.tfstate", gcloudignore)
        self.assertIn("**/*.tfstate.*", gcloudignore)
        self.assertIn("**/.gcloud/**", gcloudignore)
        self.assertIn("local.env", gcloudignore)
        self.assertIn("offline.env", gcloudignore)
        self.assertIn("state/**", gcloudignore)

    def test_workstation_package_manifests_match_sources_and_dependencies(self) -> None:
        for sources_path in sorted(
            (REPO_ROOT / "workstation").glob("*/src/*.egg-info/SOURCES.txt")
        ):
            project_root = sources_path.parents[2]
            actual_modules = {
                path.relative_to(project_root).as_posix()
                for path in (project_root / "src").rglob("*.py")
                if ".egg-info" not in path.parts and "__pycache__" not in path.parts
            }
            listed_modules = {
                line.strip()
                for line in sources_path.read_text(encoding="utf-8").splitlines()
                if line.strip().endswith(".py") and ".egg-info/" not in line
            }
            project = tomllib.loads(
                (project_root / "pyproject.toml").read_text(encoding="utf-8")
            )["project"]
            expected_dependencies = list(project.get("dependencies", []))
            package_metadata = Parser().parsestr(
                sources_path.with_name("PKG-INFO").read_text(encoding="utf-8")
            )
            metadata_dependencies = package_metadata.get_all("Requires-Dist", []) or []
            requires_path = sources_path.with_name("requires.txt")
            requirements = (
                [
                    line
                    for line in requires_path.read_text(encoding="utf-8").splitlines()
                    if line and not line.startswith("[")
                ]
                if requires_path.is_file()
                else []
            )
            with self.subTest(package=project_root.name):
                self.assertEqual(actual_modules, listed_modules)
                self.assertEqual(expected_dependencies, metadata_dependencies)
                self.assertEqual(expected_dependencies, requirements)

    def test_gather_sources_uses_path_notation_without_loading_learning_orchestration(self) -> None:
        source = (REPO_ROOT / "gather_sources.py").read_text(encoding="utf-8")

        self.assertIn(
            "from learning_context_paths import canonical_learning_subject_id, learning_context_home",
            source,
        )
        self.assertNotIn("from learning_context import", source)

        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "nested" / "record.json"
            gather_sources._write_json(target, {"second": 2, "first": 1})
            self.assertEqual(
                '{\n  "first": 1,\n  "second": 2\n}\n',
                target.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                {"first": 1, "second": 2},
                gather_sources._read_json(target),
            )
            target.write_text("not-json", encoding="utf-8")
            self.assertEqual({}, gather_sources._read_json(target))

    def test_cli_and_textual_callers_use_the_explicit_application_facades(self) -> None:
        shell_facade = (
            REPO_ROOT
            / "workstation/shell_core/src/workstation/shell/core/application_facade.py"
        )
        subject_facade = (
            REPO_ROOT
            / "workstation/subject_textual/src/workstation/subject/textual/application_facade.py"
        )
        cli = (
            REPO_ROOT
            / "workstation/app_cli/src/workstation/app/cli/cli.py"
        ).read_text(encoding="utf-8")
        textual = (
            REPO_ROOT
            / "workstation/ui_textual/src/workstation/ui/textual/chat_ui.py"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            {
                "AVAILABLE_WORKSTATION_CAPABILITIES",
                "DEFAULT_WORKSTATION_CAPABILITIES",
                "InProcessWorkstationShellClient",
                "WorkstationDelegationEscalationDecision",
                "WorkstationDelegationEscalationRequest",
                "WorkstationProjectionSubscriberController",
                "append_workstation_receipt_and_publish",
                "canonical_workstation_chat_slash_command_text",
                "execute_workstation_capability",
                "launch_workstation_session",
                "load_workstation_session",
                "prompt_workstation_session",
                "run_workstation_chat_slash_command",
                "workstation_chat_context",
                "workstation_chat_help_text",
                "workstation_chat_prepare_last_assistant_resolution",
                "workstation_chat_prepare_markdown_prompt",
                "workstation_chat_prompt_target_plan",
                "workstation_chat_resume_research_prompt",
                "workstation_chat_routed_llm_prompt_text",
                "workstation_chat_slash_commands",
                "workstation_export_learned_skill_bundle_action",
            },
            self._exported_names(shell_facade),
        )
        self.assertEqual(
            {
                "MOCK_SUBJECT_PHASES",
                "MockSubjectActionSpec",
                "MockSubjectGateAction",
                "MockSubjectProgress",
                "MockSubjectScenario",
                "MockSubjectSelectSpec",
                "MockSubjectSelectionListSpec",
                "MockSubjectSwitchSpec",
                "MockSubjectTableSpec",
                "TextualSubjectWorkflowProjectionBackend",
                "latest_source_revision",
                "mock_source_collection_option_label",
                "mock_subject_research_source_collection_workbench_rows",
                "mock_subject_status_title",
                "new_mock_subject_progress",
                "normalize_itemized_decision_role",
            },
            self._exported_names(subject_facade),
        )
        self.assertIn(
            "from workstation.shell.core.application_facade import (",
            cli,
        )
        self.assertIn(
            "from workstation.shell.core.application_facade import (",
            textual,
        )
        self.assertIn(
            "from workstation.subject.textual.application_facade import (",
            textual,
        )
        self.assertIn(
            "from workstation.foundation.host.subject_workflow import create_subject_workflow_client",
            cli,
        )
        self.assertIn(
            "subject_workflow_client=create_subject_workflow_client()",
            cli,
        )
        self.assertNotIn("from workstation.foundation.host", textual)
        for forbidden_prefix in (
            "from workstation.foundation.events",
            "from workstation.foundation.models",
            "from workstation.runtime.core",
            "from workstation.shell.core.chat_shell",
            "from workstation.subject.core",
            "from workstation.subject.service",
        ):
            self.assertNotIn(forbidden_prefix, cli)
            self.assertNotIn(forbidden_prefix, textual)

    def test_repository_matches_checked_in_dependency_baseline(self) -> None:
        manifest = architecture.load_manifest(
            REPO_ROOT / "architecture" / "boundaries.toml"
        )
        measured = architecture.analyze(REPO_ROOT, manifest)
        baseline = json.loads(
            (REPO_ROOT / "architecture" / "dependency-baseline.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual([], measured["parse_errors"])
        self.assertEqual([], measured["baseline"]["cycles"])
        self.assertEqual([], measured["baseline"]["forbidden_edges"])
        self.assertEqual([], measured["baseline"]["undeclared_dependencies"])
        metrics = measured["baseline"]["combined_graph_metrics"]
        self.assertEqual(
            sum(len(cycle) for cycle in measured["baseline"]["combined_cycles"]),
            metrics["cyclic_node_count"],
        )
        cut_impacts = measured["baseline"]["single_edge_cut_impacts"]
        if metrics["cyclic_node_count"]:
            self.assertTrue(cut_impacts)
            self.assertTrue(
                all(
                    row["cyclic_node_reduction"] > 0
                    or row["cyclic_internal_edge_reduction"] > 1
                    or row["largest_cyclic_scc_node_reduction"] > 0
                    for row in cut_impacts
                )
            )
        else:
            self.assertEqual([], cut_impacts)
        classifications = measured["baseline"]["root_boundary_classifications"]
        self.assertEqual(
            len(measured["baseline"]["root_module_dependencies"])
            + len(measured["baseline"]["root_to_component_dependencies"]),
            len(classifications),
        )
        self.assertEqual(
            {"pure_helper"},
            {
                row["category"]
                for row in classifications
                if row["target"] == "semantic_text"
            },
        )
        self.assertEqual(
            {"persistence"},
            {
                row["category"]
                for row in classifications
                if row["target"] == "store"
            },
        )
        self.assertEqual(
            {
                ("foundation_events", "runtime_core"),
                ("foundation_host", "runtime_core"),
                ("foundation_host", "subject_service"),
                ("shell_core", "contracts"),
            },
            {
                (row["source"], row["target"])
                for row in measured["baseline"]["compatibility_edges"]
            },
        )
        self.assertEqual(
            [],
            measured["components"]["contracts"]["project"]["project"].get(
                "dependencies", []
            ),
        )
        self.assertEqual(
            [],
            measured["components"]["governed_core"]["project"]["project"].get(
                "dependencies", []
            ),
        )
        self.assertEqual(
            [],
            measured["components"]["host_interaction"]["project"]["project"].get(
                "dependencies", []
            ),
        )
        self.assertEqual(
            {
                "realized-core-conversation==0.1.0",
                "realized-core-engine==0.1.0",
                "realized-core-llm==0.1.0",
            },
            set(
                measured["components"]["core_app"]["project"]["project"].get(
                    "dependencies", []
                )
            ),
        )
        actual_edges = {
            (row["source"], row["target"])
            for row in measured["baseline"]["actual_edges"]
        }
        self.assertTrue(
            {
                ("core_app", "core_conversation"),
                ("core_app", "core_llm"),
                ("core_conversation", "core_engine"),
                ("core_conversation", "core_llm"),
                ("shell_core", "core_conversation"),
                ("shell_core", "core_llm"),
            }.issubset(actual_edges)
        )
        self.assertFalse(
            {
                ("core_conversation", "core_app"),
                ("core_conversation", "shell_core"),
                ("core_llm", "core_app"),
                ("core_llm", "core_conversation"),
                ("core_llm", "shell_core"),
            }
            & actual_edges
        )
        self.assertIn(
            "realized-core-runtime==0.1.0",
            measured["components"]["core_engine"]["project"]["project"].get(
                "dependencies", []
            ),
        )
        self.assertIn(
            "realized-host-interaction==0.1.0",
            measured["components"]["core_engine"]["project"]["project"].get(
                "dependencies", []
            ),
        )
        self.assertFalse(
            any(
                row["source"] in {"contracts", "governed_core", "host_interaction"}
                for row in measured["baseline"]["actual_edges"]
            )
        )
        self.assertFalse(
            any(
                row["source"] == "governed_core"
                for row in measured["baseline"]["root_module_dependencies"]
            )
        )
        for source_path in sorted(
            (REPO_ROOT / "core_runtime" / "src" / "realized_core_runtime").glob(
                "*.py"
            )
        ):
            syntax = ast.parse(
                source_path.read_text(encoding="utf-8"),
                filename=str(source_path),
            )
            imported_roots = {
                imported.partition(".")[0]
                for node in ast.walk(syntax)
                for imported in (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else []
                )
                if imported
            }
            with self.subTest(source=source_path.name):
                self.assertTrue(
                    imported_roots <= sys.stdlib_module_names | {"realized_core_runtime"},
                    imported_roots,
                )
        self.assertEqual([], architecture.compare(measured["baseline"], baseline))
        self.assertNotIn(str(REPO_ROOT), json.dumps(baseline, sort_keys=True))
        report = architecture.render_report(REPO_ROOT, manifest, measured)
        self.assertEqual(report, architecture.render_report(REPO_ROOT, manifest, measured))
        self.assertEqual(
            report,
            (REPO_ROOT / "architecture" / "DEPENDENCY_REPORT.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertIn("## Combined Graph Metrics", report)
        self.assertIn("## Single-Edge SCC Sensitivity", report)
        self.assertIn("## Root-Boundary Classification Ledger", report)


class ArchitectureBoundaryRatchetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "architecture").mkdir()
        self._write_component("a", "example.a", "example-a", "VALUE = 'a'\n")
        self._write_component("b", "example.b", "example-b", "VALUE = 'b'\n")
        (self.root / "architecture" / "boundaries.toml").write_text(
            textwrap.dedent(
                """
                schema_version = 1
                workspace_glob = "workstation/*/pyproject.toml"
                baseline_path = "architecture/dependency-baseline.json"
                report_path = "architecture/DEPENDENCY_REPORT.md"
                root_module_glob = "*.py"
                exclude_globs = ["**/tests/**"]

                [components.a]
                project_dir = "workstation/a"
                distribution = "example-a"
                module_prefix = "example.a"
                layer = "application"
                allowed_dependencies = []

                [components.b]
                project_dir = "workstation/b"
                distribution = "example-b"
                module_prefix = "example.b"
                layer = "foundation"
                allowed_dependencies = []
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        self.manifest = architecture.load_manifest(
            self.root / "architecture" / "boundaries.toml"
        )

    def _write_component(
        self, name: str, module_prefix: str, distribution: str, source: str
    ) -> None:
        project_dir = self.root / "workstation" / name
        package_dir = project_dir / "src" / Path(*module_prefix.split("."))
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text(source, encoding="utf-8")
        (project_dir / "pyproject.toml").write_text(
            textwrap.dedent(
                f"""
                [project]
                name = "{distribution}"
                version = "0.0.0"
                dependencies = []
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def _package_file(self, component: str, module_prefix: str) -> Path:
        return (
            self.root
            / "workstation"
            / component
            / "src"
            / Path(*module_prefix.split("."))
            / "__init__.py"
        )

    def test_new_edge_is_rejected_even_when_it_is_not_a_cycle(self) -> None:
        baseline = architecture.analyze(self.root, self.manifest)["baseline"]
        self._package_file("a", "example.a").write_text(
            "from example.b import VALUE\n", encoding="utf-8"
        )

        current = architecture.analyze(self.root, self.manifest)["baseline"]
        regressions = architecture.compare(current, baseline)

        self.assertIn("new dependency edge: a -> b", regressions)
        self.assertIn("new forbidden edge: a -> b", regressions)
        self.assertIn("new undeclared dependency: a -> b", regressions)

    def test_multiple_workspace_globs_discover_separate_project_families(self) -> None:
        project_dir = self.root / "core_runtime"
        package_dir = project_dir / "src" / "example" / "core"
        package_dir.mkdir(parents=True)
        (package_dir / "__init__.py").write_text("VALUE = 'core'\n", encoding="utf-8")
        (project_dir / "pyproject.toml").write_text(
            textwrap.dedent(
                """
                [project]
                name = "example-core"
                version = "0.0.0"
                dependencies = []
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        self.manifest.pop("workspace_glob")
        self.manifest["workspace_globs"] = [
            "core_runtime/pyproject.toml",
            "workstation/*/pyproject.toml",
        ]
        self.manifest["components"]["core"] = {
            "project_dir": "core_runtime",
            "distribution": "example-core",
            "module_prefix": "example.core",
            "layer": "core",
            "allowed_dependencies": [],
        }

        measured = architecture.analyze(self.root, self.manifest)

        self.assertEqual([], measured["baseline"]["unregistered_components"])
        self.assertEqual({"a", "b", "core"}, set(measured["components"]))

    def test_uv_workspace_member_cannot_be_hidden_by_manifest_globs(self) -> None:
        hidden_project = self.root / "hidden"
        hidden_package = hidden_project / "src" / "example" / "hidden"
        hidden_package.mkdir(parents=True)
        (hidden_package / "__init__.py").write_text(
            "VALUE = 'hidden'\n",
            encoding="utf-8",
        )
        (hidden_project / "pyproject.toml").write_text(
            textwrap.dedent(
                """
                [project]
                name = "example-hidden"
                version = "0.0.0"
                dependencies = []
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (self.root / "pyproject.toml").write_text(
            textwrap.dedent(
                """
                [tool.uv.workspace]
                members = ["workstation/a", "workstation/b", "hidden"]
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

        measured = architecture.analyze(self.root, self.manifest)

        self.assertEqual(
            ["hidden"],
            measured["baseline"]["unregistered_components"],
        )

    def test_new_cycle_is_rejected(self) -> None:
        self._package_file("a", "example.a").write_text(
            "from example.b import VALUE\n", encoding="utf-8"
        )
        baseline = architecture.analyze(self.root, self.manifest)["baseline"]
        self._package_file("b", "example.b").write_text(
            "from example.a import VALUE\n", encoding="utf-8"
        )

        current = architecture.analyze(self.root, self.manifest)["baseline"]
        regressions = architecture.compare(current, baseline)

        self.assertIn("new or enlarged cycle: a -> b", regressions)

    def test_new_wildcard_export_is_rejected(self) -> None:
        package_dir = self._package_file("a", "example.a").parent
        (package_dir / "values.py").write_text("VALUE = 'a'\n", encoding="utf-8")
        baseline = architecture.analyze(self.root, self.manifest)["baseline"]
        self._package_file("a", "example.a").write_text(
            "from .values import *\n", encoding="utf-8"
        )

        current = architecture.analyze(self.root, self.manifest)["baseline"]
        regressions = architecture.compare(current, baseline)

        self.assertTrue(
            any(regression.startswith("new wildcard export:") for regression in regressions)
        )

    def test_smaller_cycle_is_an_improvement_not_a_regression(self) -> None:
        baseline = {
            "schema_version": 1,
            "actual_edges": [],
            "cycles": [["a", "b", "c"]],
            "forbidden_edges": [],
            "root_module_dependencies": [],
            "undeclared_dependencies": [],
            "unregistered_components": [],
            "wildcard_exports": [],
        }
        current = {**baseline, "cycles": [["a", "b"]]}

        self.assertEqual([], architecture.compare(current, baseline))

    def test_compatibility_alias_edge_is_visible_but_not_canonical(self) -> None:
        compatibility_path = self._package_file("a", "example.a")
        self.manifest["compatibility_alias_globs"] = [
            compatibility_path.relative_to(self.root).as_posix()
        ]
        baseline = architecture.analyze(self.root, self.manifest)["baseline"]
        compatibility_path.write_text(
            "from example.b import VALUE\n", encoding="utf-8"
        )

        current = architecture.analyze(self.root, self.manifest)["baseline"]
        regressions = architecture.compare(current, baseline)

        self.assertEqual([], current["actual_edges"])
        self.assertEqual(
            [{"source": "a", "target": "b"}],
            current["compatibility_edges"],
        )
        self.assertIn("new compatibility-alias edge: a -> b", regressions)

    def test_new_root_to_component_dependency_is_rejected(self) -> None:
        baseline = architecture.analyze(self.root, self.manifest)["baseline"]
        (self.root / "entrypoint.py").write_text(
            "from example.a import VALUE\n", encoding="utf-8"
        )

        current = architecture.analyze(self.root, self.manifest)["baseline"]
        regressions = architecture.compare(current, baseline)

        self.assertEqual(
            [{"source": "entrypoint", "target": "a"}],
            current["root_to_component_dependencies"],
        )
        self.assertIn(
            "new root-to-component dependency: entrypoint -> a",
            regressions,
        )

    def test_new_root_to_root_dependency_is_rejected(self) -> None:
        (self.root / "shared.py").write_text("VALUE = 'shared'\n", encoding="utf-8")
        baseline = architecture.analyze(self.root, self.manifest)["baseline"]
        (self.root / "entrypoint.py").write_text(
            "from shared import VALUE\n", encoding="utf-8"
        )

        current = architecture.analyze(self.root, self.manifest)["baseline"]
        regressions = architecture.compare(current, baseline)

        self.assertEqual(
            [{"source": "entrypoint", "module": "shared"}],
            current["root_to_root_dependencies"],
        )
        self.assertIn(
            "new root-to-root dependency: entrypoint -> shared",
            regressions,
        )

    def test_new_cycle_spanning_root_and_component_is_rejected(self) -> None:
        (self.root / "entrypoint.py").write_text(
            "from example.a import VALUE\n", encoding="utf-8"
        )
        baseline = architecture.analyze(self.root, self.manifest)["baseline"]
        self._package_file("a", "example.a").write_text(
            "from entrypoint import VALUE\n", encoding="utf-8"
        )

        current = architecture.analyze(self.root, self.manifest)["baseline"]
        regressions = architecture.compare(current, baseline)

        self.assertEqual(
            [["component:a", "root:entrypoint"]],
            current["combined_cycles"],
        )
        self.assertEqual(
            {
                "node_count": 3,
                "edge_count": 2,
                "cyclic_scc_count": 1,
                "cyclic_node_count": 2,
                "cyclic_internal_edge_count": 2,
                "largest_cyclic_scc_node_count": 2,
            },
            current["combined_graph_metrics"],
        )
        self.assertEqual(
            [
                {
                    "source": "component:a",
                    "target": "root:entrypoint",
                    "cyclic_node_reduction": 2,
                    "cyclic_internal_edge_reduction": 2,
                    "largest_cyclic_scc_node_reduction": 2,
                    "resulting_cyclic_node_count": 0,
                    "resulting_cyclic_internal_edge_count": 0,
                },
                {
                    "source": "root:entrypoint",
                    "target": "component:a",
                    "cyclic_node_reduction": 2,
                    "cyclic_internal_edge_reduction": 2,
                    "largest_cyclic_scc_node_reduction": 2,
                    "resulting_cyclic_node_count": 0,
                    "resulting_cyclic_internal_edge_count": 0,
                },
            ],
            current["single_edge_cut_impacts"],
        )
        self.assertIn(
            "new or enlarged combined cycle: component:a -> root:entrypoint",
            regressions,
        )

    def test_combined_cycle_metrics_cannot_expand_silently(self) -> None:
        baseline = {
            "schema_version": 1,
            "combined_graph_metrics": {
                "cyclic_node_count": 2,
                "cyclic_internal_edge_count": 2,
                "largest_cyclic_scc_node_count": 2,
            },
        }
        current = {
            **baseline,
            "combined_graph_metrics": {
                "cyclic_node_count": 2,
                "cyclic_internal_edge_count": 3,
                "largest_cyclic_scc_node_count": 2,
            },
        }

        self.assertIn(
            "combined cyclic internal edge count increased: 2 -> 3",
            architecture.compare(current, baseline),
        )

    def test_root_boundary_classification_change_is_rejected(self) -> None:
        baseline = {
            "schema_version": 1,
            "root_boundary_classifications": [
                {
                    "direction": "component_to_root",
                    "source": "a",
                    "target": "helper",
                    "category": "pure_helper",
                }
            ],
        }
        current = {
            **baseline,
            "root_boundary_classifications": [
                {
                    "direction": "component_to_root",
                    "source": "a",
                    "target": "helper",
                    "category": "orchestration",
                }
            ],
        }

        self.assertIn(
            "root-boundary classification changed: component_to_root a -> helper "
            "(pure_helper -> orchestration)",
            architecture.compare(current, baseline),
        )


if __name__ == "__main__":
    unittest.main()
