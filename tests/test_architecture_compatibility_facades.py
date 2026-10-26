from __future__ import annotations

import pickle
import unittest

import applied_theory_primitives
import applied_theory_types
import approval_governance
import artifact
import artifact_contracts
import side
from artifact_contracts import ArtifactContentView, TitledArtifactContentView
import blend_workflow
import blend_workflow_models
import blend_world
import blend_world_models
import controller_runtime
import data_governance
import decision_review
import decision_review_models
import execution_framework_primitives
import execution_frameworks
import fallback_not_generation
import fallback_not_semantics
import governance_inventory
import host_interaction_action_dispatch
import host_interaction_actions
import host_interaction_context
import host_interaction_delegation
import host_interaction_models
import host_interaction_receipts
import host_interaction_resolution
import itemize
import itemize_models
import learn
import learning_context
import learning_context_paths
import normalize
import normalization_primitives
import not_elaboration_ranking
import pure_theory_types
import semantic_text
import skill_governance
import skill_governance_primitives
import skill_composition
import skill_ir
import skill_invocation_contract
import skill_boundary_normalization
import skill_leaf_types
import skill_lifecycle
import skill_path_notation
import skill_safety_governance
from realized_host_interaction import (
    action_dispatch as packaged_host_action_dispatch,
    actions as packaged_host_actions,
    context as packaged_host_context,
    delegation as packaged_host_delegation,
    models as packaged_host_models,
    receipts as packaged_host_receipts,
    resolution as packaged_host_resolution,
)
from realized_host_interaction._normalization import (
    collapse_ws as host_interaction_collapse_ws,
    json_safe as host_interaction_json_safe,
)
from realized_core_semantics import artifacts as packaged_artifact_contracts
from realized_core_semantics import theory as packaged_theory
from realized_core_semantics import values as packaged_values
from realized_core_governance import approval as packaged_approval_governance
from realized_core_governance import admission as packaged_governance_admission
from realized_core_governance import data as packaged_data_governance
from realized_core_governance import declarations as packaged_governance_declarations
from realized_core_governance import inventory as packaged_governance_inventory
from realized_core_governance import lifecycle as packaged_skill_lifecycle
from realized_core_governance import records as packaged_governance_records
from realized_core_governance import safety as packaged_skill_safety
from realized_core_governance import vocabulary as packaged_governance_vocabulary
from realized_skill_semantics import composition as packaged_skill_composition
from realized_skill_semantics import declaration as packaged_skill_declaration
from realized_skill_semantics import execution as packaged_skill_execution
from realized_skill_semantics import leaves as packaged_skill_leaves
from realized_skill_semantics import ir as packaged_skill_ir
from realized_skill_semantics import invocation as packaged_skill_invocation
from realized_skill_semantics import normalization as packaged_skill_normalization
from realized_skill_semantics import paths as packaged_skill_paths
from workstation.skills.core import invocation_contract


class ArchitectureCompatibilityFacadeTest(unittest.TestCase):
    def test_formal_semantic_facades_keep_packaged_identities(self) -> None:
        for name in pure_theory_types.__all__:
            with self.subTest(module="pure_theory_types", name=name):
                self.assertIs(
                    getattr(pure_theory_types, name),
                    getattr(packaged_theory, name),
                )
        for name in artifact_contracts.__all__:
            with self.subTest(module="artifact_contracts", name=name):
                self.assertIs(
                    getattr(artifact_contracts, name),
                    getattr(packaged_artifact_contracts, name),
                )

    def test_legacy_formal_theory_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(b"cpure_theory_types\nNonAchievedness\n."),
            packaged_theory.NonAchievedness,
        )

    def test_skill_semantic_facades_keep_packaged_identities(self) -> None:
        for facade, implementation in (
            (skill_leaf_types, packaged_skill_leaves),
            (skill_path_notation, packaged_skill_paths),
        ):
            for name in facade.__all__:
                with self.subTest(module=facade.__name__, name=name):
                    self.assertIs(
                        getattr(facade, name),
                        getattr(implementation, name),
                    )

    def test_legacy_skill_semantic_pickle_globals_still_resolve(self) -> None:
        self.assertIs(
            pickle.loads(b"cskill_leaf_types\nSkillLeaf\n."),
            packaged_skill_leaves.SkillLeaf,
        )
        self.assertIs(
            pickle.loads(b"cskill_leaf_types\nSkillLeafClass\n."),
            packaged_skill_leaves.SkillLeafClass,
        )
        self.assertIs(
            pickle.loads(b"cskill_path_notation\ncanonical_skill_path\n."),
            packaged_skill_paths.canonical_skill_path,
        )

    def test_skill_normalization_compatibility_aliases_keep_packaged_identities(self) -> None:
        for name in (
            "normalize_skill_region_body",
            "normalized_skill_normalization_payload",
            "reconstruct_skill_region_body",
            "synthesized_skill_normalization",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_boundary_normalization, name),
                    getattr(packaged_skill_normalization, name),
                )

    def test_legacy_skill_normalization_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(
                b"cskill_boundary_normalization\nnormalize_skill_region_body\n."
            ),
            packaged_skill_normalization.normalize_skill_region_body,
        )

    def test_skill_ir_compatibility_aliases_keep_packaged_identities(self) -> None:
        for name in packaged_skill_ir.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_ir, name),
                    getattr(packaged_skill_ir, name),
                )

    def test_legacy_skill_ir_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(b"cskill_ir\nCanonicalSkillIR\n."),
            packaged_skill_ir.CanonicalSkillIR,
        )

    def test_skill_composition_value_aliases_keep_packaged_identities(self) -> None:
        for name in packaged_skill_composition.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_composition, name),
                    getattr(packaged_skill_composition, name),
                )

    def test_legacy_skill_composition_pickle_globals_still_resolve(self) -> None:
        for name in packaged_skill_composition.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    pickle.loads(f"cskill_composition\n{name}\n.".encode("ascii")),
                    getattr(packaged_skill_composition, name),
                )

    def test_learning_token_constants_keep_their_historical_identity(self) -> None:
        self.assertIs(
            learn.LEARNING_STOP_TOKENS,
            semantic_text.LEARNING_STOP_TOKENS,
        )
        self.assertIs(
            learn.LEARNING_COMPONENT_BREAKS,
            semantic_text.LEARNING_COMPONENT_BREAKS,
        )

    def test_host_interaction_facades_keep_packaged_identities(self) -> None:
        facade_pairs = (
            (host_interaction_action_dispatch, packaged_host_action_dispatch),
            (host_interaction_actions, packaged_host_actions),
            (host_interaction_context, packaged_host_context),
            (host_interaction_delegation, packaged_host_delegation),
            (host_interaction_models, packaged_host_models),
            (host_interaction_receipts, packaged_host_receipts),
            (host_interaction_resolution, packaged_host_resolution),
        )
        for facade, implementation in facade_pairs:
            for name in facade.__all__:
                with self.subTest(module=facade.__name__, name=name):
                    self.assertIs(getattr(facade, name), getattr(implementation, name))

    def test_host_interaction_private_normalization_preserves_existing_behavior(self) -> None:
        for value in (" alpha\tbeta\n", "alpha\x00beta", "alpha\u2003beta"):
            with self.subTest(value=value):
                self.assertEqual(
                    semantic_text.collapse_ws(value),
                    host_interaction_collapse_ws(value),
                )

        attachment = packaged_host_models.HostInteractionAttachment(
            name="main",
            kind="workspace",
            source="/tmp/project",
            access_mode="read_write",
            mount_path="/workstation/mounts/main",
            metadata={"payload": bytearray(b"payload")},
        )
        value = {
            "region": applied_theory_types.BoundaryShapeTerm.INPUT_VALUE,
            "attachment": attachment,
            "nested": (b"first", {"second"}),
        }
        self.assertEqual(
            applied_theory_primitives.json_safe(value),
            host_interaction_json_safe(value),
        )

    def test_main_facade_is_the_canonical_controller_runtime(self) -> None:
        import main

        self.assertIs(main, controller_runtime)
        self.assertIs(main.BSSCController, controller_runtime.BSSCController)
        self.assertIs(main.build_controller, controller_runtime.build_controller)

    def test_legacy_controller_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(b"cmain\nBSSCController\n."),
            controller_runtime.BSSCController,
        )

    def test_side_export_entry_helpers_keep_their_legacy_identity(self) -> None:
        self.assertIs(side.artifact_export_in_entries, artifact.artifact_export_in_entries)
        self.assertIs(side.artifact_export_out_entries, artifact.artifact_export_out_entries)

    def test_controller_pure_helpers_keep_their_legacy_identity(self) -> None:
        import main

        self.assertIs(
            main.pure_theory_template_schema_from_runtime,
            artifact.pure_theory_template_schema_from_runtime,
        )
        self.assertIs(
            main.normalize_semantic_component_title,
            semantic_text.normalize_semantic_component_title,
        )

    def test_normalization_facade_keeps_canonical_identities(self) -> None:
        for name in (
            "boundary_shape_values",
            "normalize_artifact_representation",
            "normalize_artifact_type",
            "normalize_boundary_shape",
            "normalize_not_degree",
            "normalize_not_misalignment_list",
            "normalize_not_origin_list",
            "normalize_remainder_shape_list",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(normalize, name),
                    getattr(normalization_primitives, name),
                )

    def test_fallback_facade_keeps_canonical_identities(self) -> None:
        self.assertIs(
            fallback_not_semantics.fallback_not_elaboration_for_text,
            fallback_not_generation.fallback_not_elaboration_for_text,
        )
        self.assertIs(
            fallback_not_semantics.not_elaboration_alignment_rank,
            not_elaboration_ranking.not_elaboration_alignment_rank,
        )

    def test_applied_theory_public_types_keep_their_legacy_identity(self) -> None:
        for name in (
            "ArtifactType",
            "BoundaryShapeTerm",
            "NotDegreeKind",
            "RunOutcome",
            "RuntimeStrEnum",
            "json_safe",
            "utc_now",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(applied_theory_types, name),
                    getattr(applied_theory_primitives, name),
                )

    def test_semantic_value_facades_keep_packaged_identities(self) -> None:
        for name in ("json_safe", "utc_now"):
            with self.subTest(name=name):
                packaged_value = getattr(packaged_values, name)
                self.assertIs(
                    getattr(applied_theory_primitives, name),
                    packaged_value,
                )
                self.assertIs(
                    getattr(applied_theory_types, name),
                    packaged_value,
                )

    def test_artifact_content_contract_accepts_the_concrete_record(self) -> None:
        artifact = applied_theory_types.Artifact.from_dict(
            {
                "id": "artifact-contract-probe",
                "title": "Contract Probe",
                "content": {"answer": "stable"},
            }
        )

        self.assertIsInstance(artifact, ArtifactContentView)
        self.assertIsInstance(artifact, TitledArtifactContentView)
        self.assertEqual(artifact.content, {"answer": "stable"})

    def test_legacy_utc_now_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(b"capplied_theory_types\nutc_now\n."),
            applied_theory_primitives.utc_now,
        )

    def test_json_safe_projection_remains_behaviorally_compatible(self) -> None:
        value = {
            "region": applied_theory_types.BoundaryShapeTerm.INPUT_VALUE,
            "payload": bytearray(b"payload"),
            "nested": (b"first", {"second"}),
        }

        self.assertEqual(
            applied_theory_types.json_safe(value),
            {
                "region": "a*",
                "payload": "payload",
                "nested": ["first", ["second"]],
            },
        )

    def test_legacy_json_safe_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(b"capplied_theory_types\njson_safe\n."),
            applied_theory_primitives.json_safe,
        )

    def test_executor_normalizers_keep_their_legacy_identity(self) -> None:
        self.assertIs(
            execution_frameworks.normalize_executor_framework_name,
            packaged_skill_execution.normalize_executor_framework_name,
        )
        self.assertIs(
            execution_framework_primitives.normalize_executor_framework_name,
            packaged_skill_execution.normalize_executor_framework_name,
        )
        self.assertIs(
            execution_frameworks.normalize_supported_executor_frameworks,
            execution_framework_primitives.normalize_supported_executor_frameworks,
        )
        self.assertFalse(
            hasattr(
                packaged_skill_execution,
                "normalize_supported_executor_frameworks",
            )
        )

    def test_learning_context_paths_keep_their_legacy_identity(self) -> None:
        for name in (
            "canonical_learning_subject_id",
            "ensure_learning_context_home",
            "learning_context_home",
            "learning_context_paths",
            "learning_corpus_root",
            "learning_source_bundle_root",
            "resolve_learning_context_root",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(learning_context, name),
                    getattr(learning_context_paths, name),
                )

    def test_decision_review_paths_keep_their_legacy_identity(self) -> None:
        self.assertIs(
            decision_review.decision_review_paths,
            learning_context_paths.decision_review_paths,
        )

    def test_decision_review_models_keep_their_legacy_identity(self) -> None:
        for name in (
            "DECISION_FRAME_STATUSES",
            "DECISION_REVIEW_DECISION_ROLE_ORDER",
            "DECISION_REVIEW_ITEM_STATUSES",
            "DECISION_REVIEW_SCHEMA_VERSION",
            "VALID_DECISION_REVIEW_DECISION_ROLES",
            "DecisionFrame",
            "DecisionReviewItem",
            "normalize_decision_review_role",
            "stable_decision_frame_id",
            "stable_decision_review_item_id",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(decision_review, name),
                    getattr(decision_review_models, name),
                )

    def test_legacy_decision_review_pickle_globals_still_resolve(self) -> None:
        self.assertIs(
            pickle.loads(b"cdecision_review\nDecisionFrame\n."),
            decision_review_models.DecisionFrame,
        )
        self.assertIs(
            pickle.loads(b"cdecision_review\nDecisionReviewItem\n."),
            decision_review_models.DecisionReviewItem,
        )

    def test_itemization_models_keep_their_legacy_identity(self) -> None:
        for name in (
            "ITEMIZATION_SCHEMA_VERSION",
            "ItemizationSession",
            "ItemizedSubjectItem",
            "VALID_ITEMIZATION_SESSION_STATUSES",
            "VALID_ITEMIZED_DECISION_ROLES",
            "VALID_ITEMIZED_ITEM_KINDS",
            "VALID_ITEMIZED_ITEM_STATUSES",
            "normalize_itemized_decision_role",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(itemize, name),
                    getattr(itemize_models, name),
                )

    def test_legacy_itemization_pickle_globals_still_resolve(self) -> None:
        self.assertIs(
            pickle.loads(b"citemize\nItemizationSession\n."),
            itemize_models.ItemizationSession,
        )
        self.assertIs(
            pickle.loads(b"citemize\nItemizedSubjectItem\n."),
            itemize_models.ItemizedSubjectItem,
        )
        self.assertIs(
            pickle.loads(b"cdecision_review\ndecision_review_paths\n."),
            learning_context_paths.decision_review_paths,
        )

    def test_blend_models_keep_their_legacy_identity(self) -> None:
        for name in (
            "BlendWorkflowBinding",
            "BlendWorkflowCondition",
            "BlendWorkflowPlan",
            "BlendWorkflowRun",
            "BlendWorkflowStep",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(blend_workflow, name),
                    getattr(blend_workflow_models, name),
                )
        for name in ("BlendWorld", "BlendWorldMount"):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(blend_world, name),
                    getattr(blend_world_models, name),
                )

    def test_skill_governance_vocabulary_and_normalization_remain_compatible(self) -> None:
        for name in (
            "SKILL_APPROVAL_CLASSES",
            "SKILL_AUTHORITIES",
            "SKILL_KIND_CHOICES",
            "SKILL_RISK_TIERS",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_governance, name),
                    getattr(skill_governance_primitives, name),
                )
                self.assertIs(
                    getattr(skill_governance_primitives, name),
                    getattr(packaged_governance_vocabulary, name),
                )
        cases = (
            ("normalize_skill_kind", "ABILITY"),
            ("normalize_skill_risk_tier", "tier3_sensitive"),
            ("normalize_skill_approval_class", "operator_approved"),
            ("normalize_skill_authorities", ["READ", "write", "READ"]),
        )
        for name, value in cases:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_governance_primitives, name),
                    getattr(packaged_governance_vocabulary, name),
                )
                self.assertEqual(
                    getattr(skill_governance, name)(value),
                    getattr(skill_governance_primitives, name)(value),
                )

    def test_skill_lifecycle_keeps_packaged_identities(self) -> None:
        for name in skill_lifecycle.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_lifecycle, name),
                    getattr(packaged_skill_lifecycle, name),
                )

    def test_approval_governance_keeps_packaged_identities(self) -> None:
        for name in approval_governance.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(approval_governance, name),
                    getattr(packaged_approval_governance, name),
                )

    def test_data_governance_keeps_packaged_identities(self) -> None:
        for name in data_governance.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(data_governance, name),
                    getattr(packaged_data_governance, name),
                )

    def test_skill_safety_governance_keeps_packaged_identities(self) -> None:
        for name in skill_safety_governance.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_safety_governance, name),
                    getattr(packaged_skill_safety, name),
                )

    def test_skill_governance_record_projections_keep_packaged_identities(self) -> None:
        for name in packaged_governance_records.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_governance, name),
                    getattr(packaged_governance_records, name),
                )

    def test_governance_inventory_loader_keeps_packaged_identity(self) -> None:
        self.assertIs(
            governance_inventory.load_governance_inventory,
            packaged_governance_inventory.load_governance_inventory,
        )

    def test_governance_declaration_helpers_keep_packaged_identities(self) -> None:
        for name in packaged_governance_declarations.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_governance, name),
                    getattr(packaged_governance_declarations, name),
                )

    def test_skill_admission_keeps_root_orchestration_and_package_policy_owner(self) -> None:
        self.assertEqual(
            "realized_core_governance.admission",
            packaged_governance_admission.evaluate_skill_policy_admission.__module__,
        )
        self.assertEqual(
            "skill_governance",
            skill_governance.evaluate_skill_admission.__module__,
        )
        self.assertIs(
            pickle.loads(b"cskill_governance\nevaluate_skill_admission\n."),
            skill_governance.evaluate_skill_admission,
        )

    def test_skill_declaration_semantics_keep_packaged_identities(self) -> None:
        for name in packaged_skill_declaration.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_governance, name),
                    getattr(packaged_skill_declaration, name),
                )

    def test_historical_governance_function_pickle_globals_still_resolve(self) -> None:
        for module_name, implementation, names in (
            (
                "governance_inventory",
                packaged_governance_inventory,
                ("load_governance_inventory",),
            ),
            (
                "skill_governance",
                packaged_governance_declarations,
                (
                    "policy_answer_summary",
                    "skill_declaration_from_payload",
                    "skill_policy_from_payload",
                ),
            ),
            (
                "skill_governance",
                packaged_governance_records,
                (
                    "artifact_is_policy_record",
                    "artifact_skill_admission",
                    "artifact_skill_declaration",
                    "artifact_skill_policy",
                ),
            ),
            (
                "skill_governance",
                packaged_skill_declaration,
                (
                    "composition_binding_targets",
                    "normalize_skill_schema_version",
                ),
            ),
            (
                "data_governance",
                packaged_data_governance,
                (
                    "allowed_data_classes_from_governance_context",
                    "ensure_governed_data_access",
                    "normalize_data_class",
                    "normalize_data_class_list",
                    "normalize_named_query_registry",
                    "query_is_read_only",
                ),
            ),
            (
                "approval_governance",
                packaged_approval_governance,
                (
                    "approval_answer_summary",
                    "approval_matches_skill",
                    "artifact_is_approval_record",
                    "artifact_skill_approval",
                    "matching_approval_artifacts",
                    "normalize_approval_record_status",
                    "skill_approval_from_payload",
                ),
            ),
            (
                "skill_governance_primitives",
                packaged_governance_vocabulary,
                (
                    "normalize_skill_approval_class",
                    "normalize_skill_authorities",
                    "normalize_skill_kind",
                    "normalize_skill_risk_tier",
                ),
            ),
            (
                "skill_lifecycle",
                packaged_skill_lifecycle,
                (
                    "artifact_effective_skill_lifecycle",
                    "artifact_skill_lifecycle",
                    "skill_lifecycle_allows_invocation",
                    "skill_lifecycle_from_payload",
                    "synthesized_skill_lifecycle",
                ),
            ),
            (
                "skill_safety_governance",
                packaged_skill_safety,
                (
                    "artifact_is_incident_record",
                    "artifact_is_revocation_record",
                    "artifact_skill_incident",
                    "artifact_skill_revocation",
                    "governed_safety_lifecycle_overlay",
                    "incident_answer_summary",
                    "incident_matches_skill",
                    "matching_incident_artifacts",
                    "matching_revocation_artifacts",
                    "normalize_incident_enforcement_action",
                    "normalize_incident_record_status",
                    "normalize_incident_severity",
                    "normalize_revocation_record_status",
                    "revocation_answer_summary",
                    "revocation_matches_skill",
                    "skill_incident_from_payload",
                    "skill_revocation_from_payload",
                ),
            ),
        ):
            for name in names:
                with self.subTest(module=module_name, name=name):
                    self.assertIs(
                        pickle.loads(f"c{module_name}\n{name}\n.".encode("ascii")),
                        getattr(implementation, name),
                    )

    def test_execution_descriptor_helpers_keep_their_legacy_identity(self) -> None:
        for name in packaged_skill_execution.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(execution_frameworks, name),
                    getattr(packaged_skill_execution, name),
                )
                self.assertIs(
                    getattr(execution_framework_primitives, name),
                    getattr(packaged_skill_execution, name),
                )

    def test_historical_execution_descriptor_pickle_globals_still_resolve(self) -> None:
        for module_name in (
            "execution_framework_primitives",
            "execution_frameworks",
        ):
            for name in (
                "normalize_executor_framework_name",
                "executor_framework_content_key",
                "ability_executor_framework",
                "ability_executable_text",
            ):
                with self.subTest(module=module_name, name=name):
                    self.assertIs(
                        pickle.loads(
                            f"c{module_name}\n{name}\n.".encode("ascii")
                        ),
                        getattr(packaged_skill_execution, name),
                    )

    def test_learning_token_normalizer_keeps_the_legacy_identity(self) -> None:
        self.assertIs(
            normalize.normalize_learning_lookup_token,
            semantic_text.normalize_learning_token,
        )

    def test_skill_invocation_contract_keeps_legacy_identity(self) -> None:
        for name in (
            "SkillInvocationBinding",
            "SkillInvocationRequest",
            "SkillInvocationResult",
            "required_skill_input_names",
            "skill_invocation_result_from_mapping",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_invocation_contract, name),
                    getattr(invocation_contract, name),
                )
                self.assertIs(
                    getattr(skill_invocation_contract, name),
                    getattr(packaged_skill_invocation, name),
                )
        self.assertIs(
            skill_invocation_contract.skill_invocation_request_from_artifact,
            invocation_contract.skill_invocation_request_from_artifact,
        )

    def test_legacy_skill_invocation_pickle_global_still_resolves(self) -> None:
        for name in (
            "SkillInvocationBinding",
            "SkillInvocationRequest",
            "SkillInvocationResult",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    pickle.loads(
                        f"cskill_invocation_contract\n{name}\n.".encode("ascii")
                    ),
                    getattr(packaged_skill_invocation, name),
                )


if __name__ == "__main__":
    unittest.main()
