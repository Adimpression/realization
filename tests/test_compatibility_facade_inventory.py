from __future__ import annotations

import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_compatibility_facades.py"
SPEC = importlib.util.spec_from_file_location(
    "check_compatibility_facades",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
inventory_checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory_checker)


class CompatibilityFacadeInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = inventory_checker.build_inventory(
            REPO_ROOT,
            REPO_ROOT / "architecture" / "boundaries.toml",
        )

    def test_checked_in_inventory_matches_repository(self) -> None:
        checked_in = json.loads(
            (REPO_ROOT / "architecture" / "compatibility-facades.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(checked_in, self.inventory)

    def test_every_facade_is_inventoried_once(self) -> None:
        modules = [row["module"] for row in self.inventory["facades"]]
        self.assertEqual(len(modules), len(set(modules)))
        self.assertEqual(
            self.inventory["summary"]["facade_count"],
            len(modules),
        )

    def test_canonical_packages_do_not_consume_root_facades(self) -> None:
        self.assertEqual(
            0,
            self.inventory["summary"]["canonical_package_consumer_count"],
        )

    def test_public_documentation_and_examples_use_canonical_apis(self) -> None:
        self.assertEqual(
            [],
            self.inventory["public_documentation_facade_references"],
        )
        self.assertEqual([], self.inventory["public_example_facade_consumers"])

    def test_retirement_policy_distinguishes_terminal_outcomes(self) -> None:
        qualification = self.inventory["qualification"]
        self.assertGreaterEqual(qualification["minimum_stable_cycles"], 1)
        self.assertGreaterEqual(
            qualification["completed_stable_cycles"],
            qualification["minimum_stable_cycles"],
        )
        self.assertFalse(qualification["retirement_hold"])
        self.assertEqual(0, len(self.inventory["retirement_candidates"]))
        self.assertEqual(38, len(self.inventory["supported_abis"]))
        self.assertEqual([], self.inventory["retirement_holds"])

    def test_facade_shapes_match_reviewed_compatibility_cohorts(self) -> None:
        self.assertEqual(
            {
                "aggregate_reexport": 0,
                "behavior_adapter": 3,
                "exact_module_alias": 26,
                "symbol_reexport": 9,
            },
            self.inventory["summary"]["shape_counts"],
        )

    def test_exact_aliases_record_their_full_canonical_module_identity(self) -> None:
        exact_aliases = [
            row
            for row in self.inventory["facades"]
            if row["shape"] == "exact_module_alias"
        ]
        self.assertTrue(
            all(row["canonical_module_identity"] for row in exact_aliases)
        )
        by_module = {row["module"]: row for row in exact_aliases}
        self.assertEqual(
            "realized_core_semantics.applied_model",
            by_module["applied_theory_types"]["canonical_module_identity"],
        )

    def test_policy_fields_survive_inventory_generation(self) -> None:
        by_module = {
            row["module"]: row for row in self.inventory["facades"]
        }
        self.assertEqual("supported_abi", by_module["main"]["policy_source"])
        self.assertEqual(
            [
                "realized-compatibility",
                "realized-core",
                "realized-workstation",
            ],
            by_module["main"]["replacement_commands"],
        )
        self.assertEqual(
            "supported_executable_path",
            by_module["main"]["support_status"],
        )
        self.assertEqual(
            "supported_historical_import",
            by_module["python_skill_host"]["support_status"],
        )
        self.assertEqual(
            "supported",
            by_module["main"]["import_obligation"],
        )
        self.assertEqual(
            "supported",
            by_module["main"]["executable_obligation"],
        )
        self.assertTrue(
            all(row["review_condition"] for row in self.inventory["facades"])
        )
        self.assertEqual(
            "retained",
            by_module["python_skill_host"]["durable_qualified_name_status"],
        )
        self.assertEqual(
            "supported",
            by_module["external_markdown_learning_pipeline"]["retirement_state"],
        )
        self.assertEqual(
            "realized-compatibility",
            by_module["external_markdown_learning_pipeline"][
                "support_distribution"
            ],
        )
        self.assertEqual(
            "architecture/COMPATIBILITY_API.md",
            by_module["external_markdown_learning_pipeline"][
                "support_contract_reference"
            ],
        )

    def test_default_policy_applies_without_a_facade_override(self) -> None:
        policy = json.loads(
            (
                REPO_ROOT
                / "architecture"
                / "compatibility-facade-policy.json"
            ).read_text(encoding="utf-8")
        )
        effective = inventory_checker._effective_facade_policy(
            policy,
            "synthetic_facade",
        )
        self.assertEqual("default", effective["policy_source"])
        self.assertEqual("repository_internal", effective["support_status"])

    def test_executable_facade_requires_an_explicit_obligation(self) -> None:
        assessment = inventory_checker._retirement_assessment(
            facade="historical_entry",
            facade_policy={
                "durable_qualified_name_status": "clear",
                "executable_obligation": "none",
                "hold_reason": "Executable compatibility requires review.",
                "notice_reference": "",
                "retirement_state": "qualified",
                "support_status": "repository_internal",
            },
            executable_surface=True,
            shape="exact_module_alias",
            static_consumers=[],
            text_references=[],
            designated_contract_tests=set(),
            qualification={"retirement_hold": False},
        )

        self.assertFalse(assessment["eligible_for_deletion"])
        self.assertIn(
            "executable surface has no explicit compatibility obligation",
            assessment["hold_reasons"],
        )

    def test_supported_abi_requires_distribution_contract_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            policy = {
                "durable_qualified_name_status": "retained",
                "executable_obligation": "none",
                "hold_reason": "Historical import remains supported.",
                "import_obligation": "supported",
                "retirement_state": "supported",
                "support_contract_reference": "COMPATIBILITY.md",
                "support_contract_tests": ["tests/test_compatibility.py"],
                "support_distribution": "realized-compatibility",
                "support_status": "supported_historical_import",
            }
            incomplete = inventory_checker._supported_abi_assessment(
                root=root,
                facade="historical_api",
                facade_policy=policy,
                distribution_import_modules={},
            )
            self.assertFalse(incomplete["supported_abi"])
            self.assertGreaterEqual(len(incomplete["issues"]), 3)

            (root / "COMPATIBILITY.md").write_text("contract\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_compatibility.py").write_text(
                "pass\n", encoding="utf-8"
            )
            complete = inventory_checker._supported_abi_assessment(
                root=root,
                facade="historical_api",
                facade_policy=policy,
                distribution_import_modules={
                    "realized-compatibility": {"historical_api"}
                },
            )
            self.assertTrue(complete["supported_abi"])
            self.assertEqual([], complete["issues"])

            assessment = inventory_checker._retirement_assessment(
                facade="historical_api",
                facade_policy={
                    **policy,
                    "notice_reference": "",
                },
                executable_surface=False,
                shape="exact_module_alias",
                static_consumers=[],
                text_references=[],
                designated_contract_tests=set(),
                qualification={"retirement_hold": False},
                support_assessment=complete,
            )
            self.assertTrue(assessment["supported_abi"])
            self.assertFalse(assessment["eligible_for_deletion"])
            self.assertEqual([], assessment["hold_reasons"])

    def test_every_supported_facade_has_terminal_evidence(self) -> None:
        held_modules = {
            row["module"] for row in self.inventory["facades"]
            if row["retirement_assessment"]["hold_reasons"]
        }
        self.assertEqual(set(), held_modules)
        self.assertTrue(
            all(
                row["owner"]
                and row["retirement_state"] == "supported"
                and row["hold_reason"]
                and row["review_condition"]
                and row["support_distribution"]
                in {"realized-compatibility", "realized-core-runtime"}
                and row["support_contract_reference"]
                and row["support_contract_tests"]
                and row["retirement_assessment"]["supported_abi"]
                and not row["retirement_assessment"]["hold_reasons"]
                for row in self.inventory["facades"]
            )
        )

    def test_qualified_facades_have_no_unresolved_retirement_hold(self) -> None:
        candidates = {
            row["module"]: row
            for row in self.inventory["facades"]
            if row["module"] in self.inventory["retirement_candidates"]
        }
        self.assertEqual(0, len(candidates))
        self.assertTrue(
            all(
                row["retirement_state"] == "qualified"
                and row["durable_qualified_name_status"] == "clear"
                and row["support_status"] == "repository_internal"
                and row["retirement_assessment"]["eligible_for_deletion"]
                and not row["retirement_assessment"]["hold_reasons"]
                for row in candidates.values()
            )
        )

    def test_removed_aliases_are_tombstoned(self) -> None:
        self.assertEqual(
            {
                "applied_theory_primitives",
                "artifact",
                "artifact_contracts",
                "artifact_answer_resolution",
                "boundary",
                "blend_workflow",
                "blend_workflow_store",
                "blend_world",
                "blend_world_store",
                "capability_runtime",
                "controller_entrypoint_binding",
                "controller_runtime",
                "controller_runtime_binding",
                "constitutional_trace",
                "controller_governance_bridge",
                "decision_review_policy",
                "decision_review_projection",
                "direct_knowledge_reuse",
                "fallback_not_generation",
                "fallback_not_semantics",
                "gather_sources",
                "governed_closure_and_commitment",
                "governed_prior_learning_reuse",
                "governed_semantic_reduction_runtime",
                "host_abi",
                "host_brokers",
                "host_interaction_action_dispatch",
                "host_interaction_actions",
                "host_interaction_context",
                "host_interaction_delegation",
                "host_interaction_models",
                "host_interaction_receipts",
                "host_interaction_resolution",
                "host_realizers",
                "governed_skill_access",
                "id_generation",
                "itemize_validation",
                "learning_context_markdown",
                "learning_context_projection",
                "learning_context_skill_projection",
                "learn",
                "macos_host_brokers",
                "markdown_learning_artifact_semantics",
                "non_achievedness_normalization",
                "normalize",
                "normalization_primitives",
                "normalization_runtime_dependencies",
                "not_elaboration_ranking",
                "prolog",
                "prompt_directives",
                "publication",
                "publication_projection",
                "publication_render",
                "publication_validation",
                "python_skill_brokerization",
                "python_skill_host_transport",
                "runtime_temp",
                "runtime_controller_api",
                "runtime_governance_context",
                "retrieval_ranking",
                "run_outcome_harvest_and_reporting",
                "run_bundle_io",
                "semantic_prompt_posture",
                "semantic_text",
                "side",
                "side_runtime_dependencies",
                "skill_compatibility_export",
                "skill_compatibility_import",
                "skill_compiler",
                "skill_export_projection",
                "skill_registry",
                "skill_schema_io",
                "store",
                "supplement",
                "structured_learning_yaml",
                "system_state",
                "title_semantics",
                "url_learning_capture",
                "validation_ladder",
                "validation_sqlite",
                "virtual_mounts",
                "wasm_skill_runtime",
            },
            set(self.inventory["retirement_policy"]["tombstones"]),
        )

    def test_patch_target_is_discovered_as_a_consumer(self) -> None:
        references = inventory_checker._module_references(
            ast.parse('with patch("store.connect"):\n    pass\n')
        )
        self.assertEqual([("store.connect", 1, "patch_target")], references)

    def test_aliased_dynamic_import_is_discovered_as_a_consumer(self) -> None:
        references = inventory_checker._module_references(
            ast.parse(
                "from importlib import import_module as load_module\n"
                "load_module('store')\n"
            )
        )
        self.assertIn(("store", 2, "dynamic_import"), references)

    def test_relative_import_is_resolved_inside_its_package(self) -> None:
        references = inventory_checker._module_references(
            ast.parse("from ..store import Repository\n"),
            import_package="example.tests",
        )
        self.assertEqual(
            [("example.store", 1, "relative_from_import")],
            references,
        )

    def test_command_and_file_path_references_are_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script = root / "qualify.sh"
            script.write_text(
                "python3 -m main run\npython3 ./main.py run\n",
                encoding="utf-8",
            )
            references = inventory_checker._textual_references(
                script,
                root,
                {"main"},
            )
        self.assertEqual(
            {"module_invocation", "python_file_invocation"},
            {row["reference_kind"] for row in references},
        )

    def test_packaged_file_path_does_not_count_as_root_facade_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script = root / "verify.py"
            script.write_text(
                'required = {"realized_core_runtime/host_abi.py"}\n',
                encoding="utf-8",
            )
            references = inventory_checker._textual_references(
                script,
                root,
                {"host_abi"},
            )
        self.assertEqual([], references)

    def test_documentation_distinguishes_narrative_from_runnable_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            document = root / "GUIDE.md"
            document.write_text(
                "Historically this was implemented by main.py.\n\n"
                "```bash\npython3 main.py run\n```\n",
                encoding="utf-8",
            )
            references = inventory_checker._textual_references(
                document,
                root,
                {"main"},
            )
        self.assertEqual(
            {"historical_narrative", "runnable_guidance"},
            {row["disposition"] for row in references},
        )

    def test_python_comments_and_docstrings_are_not_runtime_path_dependencies(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            module = root / "consumer.py"
            module.write_text(
                '"""Historically this lived in main.py."""\n'
                "# Compatibility note about main.py.\n"
                'runtime_path = "main.py"\n',
                encoding="utf-8",
            )
            references = inventory_checker._textual_references(
                module,
                root,
                {"main"},
            )
        self.assertEqual(
            [
                "historical_narrative",
                "historical_narrative",
                "runtime_reference",
            ],
            [reference["disposition"] for reference in references],
        )

    def test_trial_markdown_path_link_is_narrative_but_command_is_runnable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            document = root / "trials" / "TRIAL.md"
            document.parent.mkdir()
            document.write_text(
                "The old implementation was in store.py.\n\n"
                "```bash\npython3 main.py run\n```\n",
                encoding="utf-8",
            )
            references = inventory_checker._textual_references(
                document,
                root,
                {"main", "store"},
            )
        self.assertEqual(
            {"historical_narrative", "runnable_guidance"},
            {reference["disposition"] for reference in references},
        )

    def test_serialized_code_import_is_a_durable_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            durable = root / "skill.jsonl"
            durable.write_text(
                '{"code":"\\n    from store import Repository\\n"}\n',
                encoding="utf-8",
            )
            references = inventory_checker._textual_references(
                durable,
                root,
                {"store"},
            )
        self.assertEqual(1, len(references))
        self.assertEqual(
            "durable_runtime_reference",
            references[0]["disposition"],
        )

    def test_checked_in_report_receipt_is_provenance_not_runtime_dependency(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            receipt = root / "reports" / "trial" / "receipts" / "events.jsonl"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(
                '{"traceback":"File \\\"store.py\\\"\\nfrom store import Store"}\n',
                encoding="utf-8",
            )
            references = inventory_checker._textual_references(
                receipt,
                root,
                {"store"},
            )
        self.assertEqual(
            {"durable_provenance_evidence"},
            {reference["disposition"] for reference in references},
        )

    def test_tombstoned_facade_cannot_be_reintroduced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "retired.py").write_text("pass\n", encoding="utf-8")
            policy_path = root / "policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "defaults": {},
                        "designated_contract_tests": [],
                        "durable_pickle_facades": [],
                        "facades": {},
                        "schema_version": 3,
                        "supported_abi_defaults": {},
                        "supported_abis": {},
                        "tombstones": {"retired": {"removed_at": "test"}},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "were reintroduced"):
                inventory_checker._load_retirement_policy(
                    root,
                    {"compatibility_policy_path": "policy.json"},
                    set(),
                )

    def test_tombstone_requires_removal_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            policy_path = root / "policy.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "defaults": {},
                        "designated_contract_tests": [],
                        "durable_pickle_facades": [],
                        "facades": {},
                        "schema_version": 3,
                        "supported_abi_defaults": {},
                        "supported_abis": {},
                        "tombstones": {"retired": {"removed_at": "test"}},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "removal_change_reference, replacement",
            ):
                inventory_checker._load_retirement_policy(
                    root,
                    {"compatibility_policy_path": "policy.json"},
                    set(),
                )

    def test_inventory_update_rejects_new_non_contract_consumers(self) -> None:
        previous = {
            "facades": [
                {
                    "module": "store",
                    "static_consumers": [],
                    "text_references": [],
                }
            ],
            "schema_version": 2,
        }
        current = {
            "facades": [
                {
                    "module": "store",
                    "static_consumers": [
                        {
                            "import_kind": "import",
                            "path": "tests/test_new_consumer.py",
                            "scope": "test",
                        }
                    ],
                    "text_references": [],
                }
            ],
            "retirement_policy": {"designated_contract_tests": []},
            "schema_version": 2,
        }
        self.assertEqual(
            [
                "new facade observation is not allowed: consumer | store | "
                "tests/test_new_consumer.py | test | import"
            ],
            inventory_checker._new_observation_errors(current, previous),
        )

    def test_inventory_update_allows_contract_test_and_shrinking_changes(self) -> None:
        previous = {
            "facades": [
                {
                    "module": "store",
                    "static_consumers": [
                        {
                            "import_kind": "import",
                            "path": "tests/test_old_consumer.py",
                            "scope": "test",
                        }
                    ],
                    "text_references": [],
                }
            ],
            "schema_version": 2,
        }
        current = {
            "facades": [
                {
                    "module": "store",
                    "static_consumers": [
                        {
                            "import_kind": "import",
                            "path": "tests/test_architecture_compatibility_facades.py",
                            "scope": "test",
                        }
                    ],
                    "text_references": [],
                }
            ],
            "retirement_policy": {
                "designated_contract_tests": [
                    "tests/test_architecture_compatibility_facades.py"
                ]
            },
            "schema_version": 2,
        }
        self.assertEqual(
            [],
            inventory_checker._new_observation_errors(current, previous),
        )

    def test_discovery_expansion_acceptance_is_explicit_and_update_only(self) -> None:
        parser = inventory_checker.build_parser()
        ordinary = parser.parse_args(["--update"])
        reviewed = parser.parse_args(
            ["--update", "--accept-observation-expansion"]
        )
        self.assertFalse(ordinary.accept_observation_expansion)
        self.assertTrue(reviewed.update)
        self.assertTrue(reviewed.accept_observation_expansion)


if __name__ == "__main__":
    unittest.main()
