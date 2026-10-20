# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main
from args import STATE_SQLITE_PATH_ENV, apply_sqlite_path_override
from main import (
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    BSSCController,
    BoundaryShapeTerm,
    ControllerFeatureToggles,
    LearningRelation,
    Result,
    SystemState,
    artifact_export_document,
    artifact_from_yaml_document,
)


class ControllerFeatureToggleTests(unittest.TestCase):
    def test_state_round_trips_controller_features(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing state round trips controller features.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_state_round_trips_controller_features()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi.")
        state.controller_features = ControllerFeatureToggles(
            discovery_enabled=False,
            reflection_enabled=True,
            contemplation_enabled=False,
            supported_executors=["python3", "bash"],
        )

        restored = SystemState.from_dict(state.to_dict())

        self.assertFalse(restored.controller_features.discovery_enabled)
        self.assertTrue(restored.controller_features.reflection_enabled)
        self.assertFalse(restored.controller_features.contemplation_enabled)
        self.assertEqual(
            restored.summary()["controller_features"],
            {
                "discovery_enabled": False,
                "reflection_enabled": True,
                "contemplation_enabled": False,
                "supported_executors": ["python3", "bash"],
            },
        )

    def test_parse_args_accepts_controller_feature_toggles(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing parse args accepts controller feature toggles.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_parse_args_accepts_controller_feature_toggles()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "run",
                "--prompt",
                "Say hi.",
                "--discovery",
                "off",
                "--reflection",
                "off",
                "--contemplation",
                "on",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.discovery, "off")
        self.assertEqual(args.reflection, "off")
        self.assertEqual(args.contemplation, "on")

    def test_parse_args_accepts_prolog_query_priming_flag(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over CLI configuration for structural Prolog retrieval, helps with testing parse args accepts prolog query priming flag.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_parse_args_accepts_prolog_query_priming_flag()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "run",
                "--prompt",
                "Say hi.",
                "--prolog-query-priming",
                "force",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.prolog_query_priming, "force")

    def test_parse_args_accepts_supported_executors(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over CLI configuration for pluggable external executors, helps with testing that the parser accepts one or more explicitly supported executor frameworks.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_parse_args_accepts_supported_executors()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "markdown-learn",
                "--markdown-file",
                "lesson.md",
                "--supported-executor",
                "python3",
                "--supported-executor",
                "bash",
                "--supported-executor",
                "wasm_wasi",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.supported_executors, ["python3", "bash", "wasm_wasi"])

    def test_parse_args_accepts_convert_markdown_to_yaml_and_sqlite(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over CLI configuration for markdown conversion into portable YAML bundles, helps with testing that the parser accepts the convert-markdown-to-yaml command and the explicit sqlite override path.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_parse_args_accepts_convert_markdown_to_yaml_and_sqlite()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "convert-markdown-to-yaml",
                "--markdown-file",
                "lesson.md",
                "--out",
                "bundle.yaml",
                "--sqlite",
                "state/override.sqlite3",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.command, "convert-markdown-to-yaml")
        self.assertEqual(args.markdown_file, Path("lesson.md"))
        self.assertEqual(args.out, Path("bundle.yaml"))
        self.assertEqual(args.sqlite, Path("state/override.sqlite3"))

    def test_parse_args_accepts_load_yaml_and_run_and_sqlite(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over CLI configuration for loading exported YAML artifacts before a governed runtime probe, helps with testing that the parser accepts the load-yaml-and-run command and the explicit sqlite override path.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_parse_args_accepts_load_yaml_and_run_and_sqlite()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "load-yaml-and-run",
                "--artifact-file",
                "bundle.yaml",
                "--prompt",
                "Say hi.",
                "--sqlite",
                "state/override.sqlite3",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.command, "load-yaml-and-run")
        self.assertEqual(args.artifact_file, [Path("bundle.yaml")])
        self.assertEqual(args.prompt, "Say hi.")
        self.assertEqual(args.sqlite, Path("state/override.sqlite3"))

    def test_parse_args_accepts_export_skill_and_sqlite(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over CLI configuration for compact skill export, helps with testing that the parser accepts the export-skill command and the explicit sqlite override path.

        Reference to Theory:
            Verifies the skill-kernel and governance-envelope CLI surface so compact skill export can coexist with the older artifact export path.

        Example Input Output:
            Input: `test_parse_args_accepts_export_skill_and_sqlite()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "export-skill",
                "--skill-title",
                "What Is Force?",
                "--sqlite",
                "state/override.sqlite3",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.command, "export-skill")
        self.assertEqual(args.skill_title, "What Is Force?")
        self.assertEqual(args.sqlite, Path("state/override.sqlite3"))

    def test_parse_args_accepts_export_skill_registry_and_sqlite(self) -> None:
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "export-skill-registry",
                "--out",
                "registry.yaml",
                "--sqlite",
                "state/override.sqlite3",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.command, "export-skill-registry")
        self.assertEqual(args.out, Path("registry.yaml"))
        self.assertEqual(args.sqlite, Path("state/override.sqlite3"))

    def test_parse_args_accepts_import_skill_and_sqlite(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over CLI configuration for compact skill import, helps with testing that the parser accepts the import-skill command and the explicit sqlite override path.

        Reference to Theory:
            Verifies the skill-kernel and governance-envelope CLI surface so compact skill import can coexist with the older artifact import path.

        Example Input Output:
            Input: `test_parse_args_accepts_import_skill_and_sqlite()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "import-skill",
                "--skill-file",
                "skill.yaml",
                "--sqlite",
                "state/override.sqlite3",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.command, "import-skill")
        self.assertEqual(args.skill_file, [Path("skill.yaml")])
        self.assertEqual(args.sqlite, Path("state/override.sqlite3"))

    def test_parse_args_accepts_export_run_bundle_and_sqlite(self) -> None:
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "export-run-bundle",
                "--state",
                "state.json",
                "--out",
                "bundle.yaml",
                "--sqlite",
                "state/override.sqlite3",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.command, "export-run-bundle")
        self.assertEqual(args.state, Path("state.json"))
        self.assertEqual(args.out, Path("bundle.yaml"))
        self.assertEqual(args.sqlite, Path("state/override.sqlite3"))

    def test_parse_args_accepts_replay_run_bundle_and_sqlite(self) -> None:
        with patch.object(
            main.os.sys,
            "argv",
            [
                "main.py",
                "replay-run-bundle",
                "--bundle-file",
                "bundle.yaml",
                "--report-out",
                "report.json",
                "--state-out",
                "state.json",
                "--sqlite",
                "state/override.sqlite3",
            ],
        ):
            args = main.parse_args()

        self.assertEqual(args.command, "replay-run-bundle")
        self.assertEqual(args.bundle_file, Path("bundle.yaml"))
        self.assertEqual(args.report_out, Path("report.json"))
        self.assertEqual(args.state_out, Path("state.json"))
        self.assertEqual(args.sqlite, Path("state/override.sqlite3"))

    def test_apply_sqlite_path_override_replaces_existing_env_value(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over CLI-targeted store selection, helps with testing that an explicit sqlite override replaces the current environment-selected store path for the active command.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_apply_sqlite_path_override_replaces_existing_env_value()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        previous_value = os.environ.get(STATE_SQLITE_PATH_ENV)
        try:
            os.environ[STATE_SQLITE_PATH_ENV] = "/tmp/original.sqlite3"
            args = main.parse_args(
                [
                    "run",
                    "--prompt",
                    "Say hi.",
                    "--sqlite",
                    "state/override.sqlite3",
                ]
            )

            resolved = apply_sqlite_path_override(args)

            self.assertEqual(resolved, Path("state/override.sqlite3"))
            self.assertEqual(os.environ[STATE_SQLITE_PATH_ENV], "state/override.sqlite3")
        finally:
            if previous_value is None:
                os.environ.pop(STATE_SQLITE_PATH_ENV, None)
            else:
                os.environ[STATE_SQLITE_PATH_ENV] = previous_value

    def test_load_yaml_and_run_imports_into_selected_sqlite_then_runs(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over YAML bundle bootstrap followed by governed execution, helps with testing that load-yaml-and-run imports artifacts into the selected sqlite path and then closes the prompt against that store.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_load_yaml_and_run_imports_into_selected_sqlite_then_runs()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "boundary_shape_artifacts"
            / "hi_responder.yaml"
        )
        previous_value = os.environ.get(STATE_SQLITE_PATH_ENV)
        try:
            os.environ[STATE_SQLITE_PATH_ENV] = "/tmp/ignored.sqlite3"
            with tempfile.TemporaryDirectory() as tempdir:
                sqlite_path = Path(tempdir) / "override.sqlite3"
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    with patch.object(
                        main.os.sys,
                        "argv",
                        [
                            "main.py",
                            "load-yaml-and-run",
                            "--artifact-file",
                            str(fixture_path),
                            "--prompt",
                            "Say hi.",
                            "--llm",
                            "off",
                            "--sqlite",
                            str(sqlite_path),
                        ],
                    ):
                        exit_code = main.main()

                payload = json.loads(stdout.getvalue())

                self.assertEqual(exit_code, 0)
                self.assertEqual(payload["imported_count"], 1)
                self.assertEqual(payload["run"]["run_outcome"], "completed")
                self.assertEqual(payload["run"]["final_answer"], "hi")
                self.assertEqual(os.environ[STATE_SQLITE_PATH_ENV], "/tmp/ignored.sqlite3")
        finally:
            if previous_value is None:
                os.environ.pop(STATE_SQLITE_PATH_ENV, None)
            else:
                os.environ[STATE_SQLITE_PATH_ENV] = previous_value

    def test_reduce_not_skips_reflection_when_disabled(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing reduce not skips reflection when disabled.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_reduce_not_skips_reflection_when_disabled()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi.")
        state.controller_features.reflection_enabled = False
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        reflect_called = False

        def fail_reflect(node):  # type: ignore[no-untyped-def]
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fail reflect.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

            Example Input Output:
                Input: `fail_reflect(node=3)`
                Output: 'F = m * a'

            Args:
                node: Value for `node` used by `fail_reflect`.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            nonlocal reflect_called
            reflect_called = True
            raise AssertionError("reflect() should not run when reflection is disabled.")

        controller.reflect = fail_reflect  # type: ignore[assignment]
        controller.should_reflect = lambda node: True  # type: ignore[assignment]
        controller.contemplate = lambda node: []  # type: ignore[assignment]
        controller.decompose_or_refine = lambda node: []  # type: ignore[assignment]
        controller.can_refine_directly = lambda node: False  # type: ignore[assignment]

        result = controller.reduce_not(root)

        self.assertEqual(result, Result.INCOMPLETE)
        self.assertFalse(reflect_called)
        self.assertTrue(any(record.kind == "reflection_skipped" for record in state.ledger))

    def test_reduce_not_skips_contemplation_when_disabled(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing reduce not skips contemplation when disabled.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_reduce_not_skips_contemplation_when_disabled()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi.")
        state.controller_features.contemplation_enabled = False
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        contemplation_called = False

        def fail_contemplate(node):  # type: ignore[no-untyped-def]
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fail contemplate.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

            Example Input Output:
                Input: `fail_contemplate(node=3)`
                Output: 'F = m * a'

            Args:
                node: Value for `node` used by `fail_contemplate`.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            nonlocal contemplation_called
            contemplation_called = True
            raise AssertionError("contemplate() should not run when contemplation is disabled.")

        controller.should_reflect = lambda node: False  # type: ignore[assignment]
        controller.contemplate = fail_contemplate  # type: ignore[assignment]
        controller.decompose_or_refine = lambda node: []  # type: ignore[assignment]
        controller.can_refine_directly = lambda node: False  # type: ignore[assignment]

        result = controller.reduce_not(root)

        self.assertEqual(result, Result.INCOMPLETE)
        self.assertFalse(contemplation_called)
        self.assertTrue(any(record.kind == "contemplation_skipped" for record in state.ledger))

    def test_finalize_run_skips_discovery_when_disabled(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing finalize run skips discovery when disabled.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_finalize_run_skips_discovery_when_disabled()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi.")
        state.controller_features.discovery_enabled = False
        controller = BSSCController(state, llm_policy="off")
        discovery_called = False

        def fail_discovery(node):  # type: ignore[no-untyped-def]
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fail discovery.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

            Example Input Output:
                Input: `fail_discovery(node=3)`
                Output: 'F = m * a'

            Args:
                node: Value for `node` used by `fail_discovery`.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            nonlocal discovery_called
            discovery_called = True
            raise AssertionError("perform_discovery_harvest() should not run when discovery is disabled.")

        controller.perform_discovery_harvest = fail_discovery  # type: ignore[assignment]
        controller.persist_artifacts = lambda: None  # type: ignore[assignment]
        controller.emit_trace_report = lambda: None  # type: ignore[assignment]

        controller.finalize_run()

        self.assertFalse(discovery_called)
        self.assertEqual(len(state.discovery_audits), 0)
        self.assertTrue(any(record.kind == "discovery_skipped" for record in state.ledger))

    def test_artifact_export_import_round_trips_controller_features(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing artifact export import round trips controller features.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_artifact_export_import_round_trips_controller_features()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = Artifact(
            id="artifact-toggle-roundtrip",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Greeting Knowledge",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when a simple greeting definition is needed",
            provenance=["test"],
            reusability=ArtifactReuse.LOCAL_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is a greeting?",
                "answer": "A greeting is a short socially appropriate opening.",
                "controller_features": {
                    "discovery_enabled": False,
                    "reflection_enabled": True,
                    "contemplation_enabled": False,
                    "supported_executors": ["python3"],
                },
                "structured_learning": {
                    "encountered_not": "Greeting Knowledge",
                    "lookup_keys": ["greeting knowledge"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Test artifact for controller feature export/import.",
            boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
        )

        exported = artifact_export_document(artifact)
        metadata = exported[artifact.title]["Metadata"]
        imported = artifact_from_yaml_document(exported)

        self.assertEqual(
            metadata["controller_features"],
            {
                "discovery_enabled": False,
                "reflection_enabled": True,
                "contemplation_enabled": False,
                "supported_executors": ["python3"],
            },
        )
        self.assertEqual(
            imported.content.get("controller_features"),
            {
                "discovery_enabled": False,
                "reflection_enabled": True,
                "contemplation_enabled": False,
                "supported_executors": ["python3"],
            },
        )


if __name__ == "__main__":
    unittest.main()
