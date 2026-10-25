from __future__ import annotations

import pickle
import unittest

import applied_theory_primitives
import applied_theory_types
import artifact
import side
from artifact_contracts import ArtifactContentView, TitledArtifactContentView
import blend_workflow
import blend_workflow_models
import blend_world
import blend_world_models
import controller_runtime
import decision_review
import decision_review_models
import execution_framework_primitives
import execution_frameworks
import fallback_not_generation
import fallback_not_semantics
import host_interaction_action_dispatch
import host_interaction_actions
import host_interaction_context
import host_interaction_delegation
import host_interaction_models
import host_interaction_receipts
import host_interaction_resolution
import itemize
import itemize_models
import learning_context
import learning_context_paths
import normalize
import normalization_primitives
import not_elaboration_ranking
import semantic_text
import skill_governance
import skill_governance_primitives
import skill_invocation_contract
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
from workstation.skills.core import invocation_contract


class ArchitectureCompatibilityFacadeTest(unittest.TestCase):
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
            execution_framework_primitives.normalize_executor_framework_name,
        )
        self.assertIs(
            execution_frameworks.normalize_supported_executor_frameworks,
            execution_framework_primitives.normalize_supported_executor_frameworks,
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
        cases = (
            ("normalize_skill_kind", "ABILITY"),
            ("normalize_skill_risk_tier", "tier3_sensitive"),
            ("normalize_skill_approval_class", "operator_approved"),
            ("normalize_skill_authorities", ["READ", "write", "READ"]),
        )
        for name, value in cases:
            with self.subTest(name=name):
                self.assertEqual(
                    getattr(skill_governance, name)(value),
                    getattr(skill_governance_primitives, name)(value),
                )

    def test_execution_descriptor_helpers_keep_their_legacy_identity(self) -> None:
        for name in (
            "ability_executable_text",
            "ability_executor_framework",
            "executor_framework_content_key",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(execution_frameworks, name),
                    getattr(execution_framework_primitives, name),
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
            "skill_invocation_request_from_artifact",
            "skill_invocation_result_from_mapping",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_invocation_contract, name),
                    getattr(invocation_contract, name),
                )

    def test_legacy_skill_invocation_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(b"cskill_invocation_contract\nSkillInvocationBinding\n."),
            invocation_contract.SkillInvocationBinding,
        )


if __name__ == "__main__":
    unittest.main()
