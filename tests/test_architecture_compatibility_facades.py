from __future__ import annotations

import pickle
import unittest

import applied_theory_types
import approval_governance
import args
import blend_context
import blend_operator
import blend_operator_store
import blend_session
import blend_workflow_execution
import blend_workflow_models
import blend_world_models
from realized_core_engine import controller_runtime
import data_governance
import decision_review
import decision_review_constructs
import decision_review_models
import execution_framework_primitives
import execution_frameworks
import fence_extraction_strategy
import governance_inventory
import host_mediation
import itemize
import itemize_models
import learning_context
import learning_context_paths
import markdown_ir
import external_markdown_learning_pipeline
import pure_theory_types
import review_composition
import python_skill_host
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
from realized_host_interaction import models as packaged_host_models
from realized_host_interaction._normalization import (
    collapse_ws as host_interaction_collapse_ws,
    json_safe as host_interaction_json_safe,
)
from realized_core_semantics import artifacts as packaged_artifact_contracts
from realized_core_semantics import applied_model as packaged_applied_theory_types
from realized_core_semantics import applied_primitives as packaged_applied_theory_primitives
from realized_core_semantics import decision_review as packaged_decision_review
from realized_core_semantics import identifiers as packaged_identifiers
from realized_core_semantics import itemization as packaged_itemization
from realized_core_semantics import markdown as packaged_markdown
from realized_core_semantics import proposals as packaged_proposals
from realized_core_semantics import semantic_text as packaged_semantic_text
from realized_core_semantics import theory as packaged_theory
from realized_core_semantics import transformation_constructs as packaged_transformation_constructs
from realized_core_semantics import values as packaged_values
from realized_blend import context as packaged_blend_context
from realized_blend import execution as packaged_blend_execution
from realized_blend import observations as packaged_blend_observations
from realized_blend import operators as packaged_blend_operators
from realized_blend import sessions as packaged_blend_sessions
from realized_blend import workflows as packaged_blend_workflows
from realized_blend import worlds as packaged_blend_worlds
from realized_blend_application import execution as packaged_blend_application_execution
from realized_blend_application import operators as packaged_blend_application_operators
from realized_blend_application import workflows as packaged_blend_application_workflows
from realized_blend_application import worlds as packaged_blend_application_worlds
from realized_core_governance import admission as packaged_governance_admission
from realized_core_governance import approval as packaged_approval_governance
from realized_core_governance import authority as packaged_governance_authority
from realized_core_governance import current_use as packaged_governance_current_use
from realized_core_governance import data as packaged_data_governance
from realized_core_governance import declarations as packaged_governance_declarations
from realized_core_governance import inventory as packaged_governance_inventory
from realized_core_governance import lifecycle as packaged_skill_lifecycle
from realized_core_governance import persistence as packaged_governance_persistence
from realized_core_governance import records as packaged_governance_records
from realized_core_governance import safety as packaged_skill_safety
from realized_core_governance import trace as packaged_governance_trace
from realized_core_governance import vocabulary as packaged_governance_vocabulary
from realized_core_engine import constitutional_trace as packaged_constitutional_trace
from realized_core_engine import configuration as packaged_engine_configuration
from realized_core_engine import artifact_semantics as packaged_artifact_semantics
from realized_core_engine import governance_inventory as packaged_engine_governance_inventory
from realized_core_engine import host_mediation as packaged_host_mediation
from realized_core_engine import skill_governance as packaged_engine_skill_governance
from realized_core_engine.store import ArtifactStore, SQLiteVectorArtifactStore
from realized_core_runtime import execution as packaged_runtime_execution
from realized_core_runtime import executor_support as packaged_executor_support
from realized_core_runtime import fence_extraction as packaged_fence_extraction
from realized_core_runtime import python_host as packaged_python_host
from realized_skill_semantics import composition as packaged_skill_composition
from realized_skill_semantics import declaration as packaged_skill_declaration
from realized_skill_semantics import execution as packaged_skill_execution
from realized_skill_semantics import leaves as packaged_skill_leaves
from realized_skill_semantics import ir as packaged_skill_ir
from realized_skill_semantics import invocation as packaged_skill_invocation
from realized_skill_semantics import normalization as packaged_skill_normalization
from realized_skill_semantics import paths as packaged_skill_paths
from workstation.skills.core import invocation_contract
from realized_skill_application import composition as packaged_skill_application_composition
from realized_skill_application import ir as packaged_skill_application_ir
from realized_skill_application import normalization as packaged_skill_application_normalization
from realized_exchange import learning_context as packaged_learning_context
from realized_exchange import markdown_learning_pipeline as packaged_markdown_learning_pipeline
from workstation.subject.core import decision_review as packaged_subject_decision_review
from workstation.subject.core import decision_review_constructs as packaged_subject_decision_review_constructs
from workstation.subject.core import itemization as packaged_subject_itemization
from workstation.subject.core import learning_context as packaged_subject_learning_context
from workstation.subject.core import learning_context_paths as packaged_subject_learning_context_paths
from workstation.subject.core import review_composition as packaged_review_composition


class ArchitectureCompatibilityFacadeTest(unittest.TestCase):
    def test_learning_context_root_facade_keeps_exact_module_identity(self) -> None:
        self.assertIs(learning_context, packaged_learning_context)

    def test_external_markdown_learning_facade_keeps_exact_module_identity(self) -> None:
        self.assertIs(
            external_markdown_learning_pipeline,
            packaged_markdown_learning_pipeline,
        )

    def test_retained_controller_and_runtime_root_aliases_keep_module_identity(self) -> None:
        for facade, canonical in (
            (host_mediation, packaged_host_mediation),
            (skill_governance, packaged_engine_skill_governance),
        ):
            with self.subTest(module=facade.__name__):
                self.assertIs(facade, canonical)

    def test_entry_parser_reuses_engine_configuration_without_aliasing_it(self) -> None:
        self.assertIsNot(args, packaged_engine_configuration)
        self.assertFalse(hasattr(packaged_engine_configuration, "parse_args"))
        self.assertIs(
            args.apply_controller_feature_toggle_overrides,
            packaged_engine_configuration.apply_controller_feature_toggle_overrides,
        )
        self.assertIs(
            args.apply_sqlite_path_override,
            packaged_engine_configuration.apply_sqlite_path_override,
        )

    def test_runtime_executor_helper_modules_keep_identity(self) -> None:
        self.assertIs(execution_framework_primitives, packaged_executor_support)
        self.assertIs(execution_frameworks, packaged_runtime_execution)
        self.assertIs(fence_extraction_strategy, packaged_fence_extraction)

    def test_python_skill_host_keeps_identity(self) -> None:
        self.assertIs(python_skill_host, packaged_python_host)

    def test_controller_adapter_modules_keep_identity(self) -> None:
        self.assertIs(governance_inventory, packaged_engine_governance_inventory)

    def test_applied_theory_types_keeps_its_historical_identity(self) -> None:
        self.assertIs(applied_theory_types, packaged_applied_theory_types)

    def test_learning_context_adapter_keeps_packaged_value_identity(self) -> None:
        self.assertIs(learning_context, packaged_learning_context)
        self.assertIsNot(learning_context, packaged_subject_learning_context)
        self.assertEqual(learning_context.__all__, packaged_subject_learning_context.__all__)
        for name in (
            "LearningContext",
            "LearningDelta",
            "LearningDeltaOperation",
            "LearningSource",
            "LearningUnit",
            "SubjectImport",
            "SubjectReasoningScope",
            "apply_learning_delta",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(learning_context, name),
                    getattr(packaged_subject_learning_context, name),
                )
                self.assertIs(
                    pickle.loads(f"clearning_context\n{name}\n.".encode("ascii")),
                    getattr(packaged_subject_learning_context, name),
                )

    def test_subject_semantic_values_keep_packaged_identity(self) -> None:
        self.assertIs(
            learning_context_paths.canonical_learning_subject_id,
            packaged_identifiers.canonical_learning_subject_id,
        )
        self.assertIs(itemize_models, packaged_itemization)
        self.assertIs(decision_review_models, packaged_decision_review)
        for name in (
            "ItemizationSession",
            "ItemizedSubjectItem",
            "normalize_itemized_decision_role",
        ):
            with self.subTest(module="itemize", name=name):
                self.assertIs(getattr(itemize, name), getattr(packaged_itemization, name))
        for name in (
            "DecisionFrame",
            "DecisionReviewItem",
            "normalize_decision_review_role",
            "stable_decision_frame_id",
            "stable_decision_review_item_id",
        ):
            with self.subTest(module="decision_review", name=name):
                self.assertIs(getattr(decision_review, name), getattr(packaged_decision_review, name))
        for name in packaged_transformation_constructs.__all__:
            with self.subTest(module="decision_review_constructs", name=name):
                self.assertIs(
                    getattr(decision_review_constructs, name),
                    getattr(packaged_transformation_constructs, name),
                )

    def test_markdown_ir_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(markdown_ir, packaged_markdown)
        for name in (
            "MarkdownSectionIR",
            "MarkdownDocumentIR",
            "parse_markdown_document_ir",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    pickle.loads(f"cmarkdown_ir\n{name}\n.".encode("ascii")),
                    getattr(packaged_markdown, name),
                )

    def test_legacy_subject_semantic_pickle_globals_still_resolve(self) -> None:
        expected = (
            ("itemize_models", "ItemizationSession", packaged_itemization.ItemizationSession),
            ("itemize_models", "ItemizedSubjectItem", packaged_itemization.ItemizedSubjectItem),
            ("decision_review_models", "DecisionFrame", packaged_decision_review.DecisionFrame),
            ("decision_review_models", "DecisionReviewItem", packaged_decision_review.DecisionReviewItem),
            (
                "decision_review_constructs",
                "TransformationConstructCandidate",
                packaged_transformation_constructs.TransformationConstructCandidate,
            ),
        )
        for module_name, name, canonical in expected:
            with self.subTest(module=module_name, name=name):
                self.assertIs(
                    pickle.loads(f"c{module_name}\n{name}\n.".encode("ascii")),
                    canonical,
                )

    def test_proposal_vocabulary_keeps_packaged_identity(self) -> None:
        self.assertIs(
            applied_theory_types.SupplementMode,
            packaged_proposals.SupplementMode,
        )
        self.assertIs(
            applied_theory_types.ProposalGovernanceStatus,
            packaged_proposals.ProposalGovernanceStatus,
        )
        self.assertIs(
            applied_theory_types.ProposalType,
            packaged_proposals.ProposalType,
        )

    def test_legacy_proposal_pickle_globals_still_resolve(self) -> None:
        for name in (
            "SupplementMode",
            "ProposalGovernanceStatus",
            "ProposalType",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    pickle.loads(f"capplied_theory_types\n{name}\n.".encode("ascii")),
                    getattr(packaged_proposals, name),
                )

    def test_subject_decision_review_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(decision_review, packaged_subject_decision_review)
        self.assertIs(
            pickle.loads(b"cdecision_review\ndecision_review_item_from_review_item\n."),
            packaged_subject_decision_review.decision_review_item_from_review_item,
        )

    def test_subject_decision_review_constructs_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(
            decision_review_constructs,
            packaged_subject_decision_review_constructs,
        )
        self.assertIs(
            pickle.loads(
                b"cdecision_review_constructs\npersist_transformation_construct_candidates\n."
            ),
            packaged_subject_decision_review_constructs.persist_transformation_construct_candidates,
        )

    def test_subject_review_composition_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(review_composition, packaged_review_composition)
        for name in (
            "ReviewItem",
            "ReviewComposition",
            "ReviewTransformReceipt",
            "review_composition_from_itemization",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    pickle.loads(f"creview_composition\n{name}\n.".encode("ascii")),
                    getattr(packaged_review_composition, name),
                )

    def test_formal_theory_facade_keeps_packaged_identities(self) -> None:
        for name in pure_theory_types.__all__:
            with self.subTest(module="pure_theory_types", name=name):
                self.assertIs(
                    getattr(pure_theory_types, name),
                    getattr(packaged_theory, name),
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
        self.assertIs(
            skill_boundary_normalization,
            packaged_skill_application_normalization,
        )
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
        self.assertIs(skill_ir, packaged_skill_application_ir)
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
        self.assertIs(skill_composition, packaged_skill_application_composition)
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

    def test_host_interaction_private_normalization_preserves_existing_behavior(self) -> None:
        for value in (" alpha\tbeta\n", "alpha\x00beta", "alpha\u2003beta"):
            with self.subTest(value=value):
                self.assertEqual(
                    packaged_semantic_text.collapse_ws(value),
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
            packaged_applied_theory_primitives.json_safe(value),
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

    def test_controller_pure_helpers_keep_their_canonical_identity(self) -> None:
        import main

        self.assertIs(
            main.pure_theory_template_schema_from_runtime,
            packaged_artifact_semantics.pure_theory_template_schema_from_runtime,
        )
        self.assertIs(
            main.normalize_semantic_component_title,
            packaged_semantic_text.normalize_semantic_component_title,
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
                    getattr(packaged_applied_theory_primitives, name),
                )

    def test_semantic_value_facades_keep_packaged_identities(self) -> None:
        for name in ("json_safe", "utc_now"):
            with self.subTest(name=name):
                packaged_value = getattr(packaged_values, name)
                self.assertIs(
                    getattr(packaged_applied_theory_primitives, name),
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

        self.assertIsInstance(artifact, packaged_artifact_contracts.ArtifactContentView)
        self.assertIsInstance(
            artifact,
            packaged_artifact_contracts.TitledArtifactContentView,
        )
        self.assertEqual(artifact.content, {"answer": "stable"})

    def test_legacy_utc_now_pickle_global_still_resolves(self) -> None:
        self.assertIs(
            pickle.loads(b"capplied_theory_types\nutc_now\n."),
            packaged_applied_theory_primitives.utc_now,
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
            packaged_applied_theory_primitives.json_safe,
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
        self.assertIs(learning_context_paths, packaged_subject_learning_context_paths)
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
                    getattr(packaged_subject_learning_context_paths, name),
                )
                self.assertIs(
                    pickle.loads(f"clearning_context_paths\n{name}\n.".encode("ascii")),
                    getattr(packaged_subject_learning_context_paths, name),
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

    def test_itemization_application_facade_keeps_canonical_identities(self) -> None:
        self.assertIs(itemize, packaged_subject_itemization)
        for name in (
            "ensure_itemization_home",
            "extract_itemized_candidates_from_markdown_document",
            "itemization_paths",
            "list_itemized_subject_items",
            "load_itemization_session",
            "load_itemized_subject_item",
            "persist_itemization_session",
            "stable_itemization_session_id",
            "stable_itemized_item_id",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(itemize, name),
                    getattr(packaged_subject_itemization, name),
                )
        self.assertIs(
            itemize.extract_itemized_candidates_from_learning_context,
            packaged_subject_itemization.extract_itemized_candidates_from_learning_context,
        )
        self.assertIs(
            itemize.materialize_itemization_session,
            packaged_subject_itemization.materialize_itemization_session,
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
            pickle.loads(b"citemize\nstable_itemized_item_id\n."),
            packaged_subject_itemization.stable_itemized_item_id,
        )
        self.assertIs(
            pickle.loads(b"cdecision_review\ndecision_review_paths\n."),
            learning_context_paths.decision_review_paths,
        )

    def test_blend_models_keep_their_legacy_identity(self) -> None:
        self.assertIs(blend_operator, packaged_blend_operators)
        self.assertIs(blend_workflow_models, packaged_blend_workflows)
        self.assertIs(blend_world_models, packaged_blend_worlds)
        for name in ("BlendContext", "BlendContextAttachment"):
            with self.subTest(module="blend_context", name=name):
                self.assertIs(
                    getattr(blend_context, name),
                    getattr(packaged_blend_context, name),
                )
        self.assertIs(
            blend_session.BlendSession,
            packaged_blend_sessions.BlendSession,
        )
        for name in (
            "BlendWorkflowBinding",
            "BlendWorkflowCondition",
            "BlendWorkflowPlan",
            "BlendWorkflowRun",
            "BlendWorkflowStep",
        ):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(packaged_blend_application_workflows, name),
                    getattr(packaged_blend_workflows, name),
                )
        for name in ("BlendWorld", "BlendWorldMount"):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(packaged_blend_application_worlds, name),
                    getattr(packaged_blend_worlds, name),
                )
        self.assertIs(
            blend_workflow_execution.BlendWorkflowExecutionEvent,
            packaged_blend_observations.BlendWorkflowExecutionEvent,
        )
        for name in (
            "BlendResolvedWorkflowStep",
            "BlendWorkflowExecutionHalt",
            "resolve_blend_skill_workflow_steps",
            "resolve_blend_workflow_steps",
            "resolve_blend_workflow_steps_from_providers",
        ):
            with self.subTest(module="blend_workflow_execution", name=name):
                self.assertIs(
                    getattr(blend_workflow_execution, name),
                    getattr(packaged_blend_execution, name),
                )
        for name in (
            "BlendOperatorProvider",
            "BlendOperatorRecord",
            "get_blend_operator_summary",
            "list_blend_operator_summaries",
            "new_blend_capability_operator_provider",
            "resolve_blend_operator_record",
            "resolve_blend_operator_record_for_workflow_step",
        ):
            with self.subTest(module="blend_operator_store", name=name):
                self.assertIs(
                    getattr(blend_operator_store, name),
                    getattr(packaged_blend_operators, name),
                )

    def test_blend_application_modules_keep_their_legacy_identity(self) -> None:
        expected = (
            (blend_operator_store, packaged_blend_application_operators),
            (blend_workflow_execution, packaged_blend_application_execution),
        )
        for compatibility_module, canonical_module in expected:
            with self.subTest(module=compatibility_module.__name__):
                self.assertIs(compatibility_module, canonical_module)

    def test_legacy_blend_pickle_globals_still_resolve(self) -> None:
        expected = (
            ("blend_context", "BlendContext", packaged_blend_context.BlendContext),
            (
                "blend_context",
                "BlendContextAttachment",
                packaged_blend_context.BlendContextAttachment,
            ),
            ("blend_operator", "BlendOperator", packaged_blend_operators.BlendOperator),
            (
                "blend_operator",
                "BlendOperatorInvocation",
                packaged_blend_operators.BlendOperatorInvocation,
            ),
            (
                "blend_operator_store",
                "BlendOperatorRecord",
                packaged_blend_operators.BlendOperatorRecord,
            ),
            (
                "blend_operator_store",
                "BlendOperatorProvider",
                packaged_blend_operators.BlendOperatorProvider,
            ),
            ("blend_session", "BlendSession", packaged_blend_sessions.BlendSession),
            (
                "blend_workflow_models",
                "BlendWorkflowPlan",
                packaged_blend_workflows.BlendWorkflowPlan,
            ),
            (
                "blend_world_models",
                "BlendWorld",
                packaged_blend_worlds.BlendWorld,
            ),
            (
                "blend_workflow_execution",
                "BlendWorkflowExecutionEvent",
                packaged_blend_observations.BlendWorkflowExecutionEvent,
            ),
            (
                "blend_workflow_execution",
                "BlendResolvedWorkflowStep",
                packaged_blend_execution.BlendResolvedWorkflowStep,
            ),
            (
                "blend_workflow_execution",
                "BlendWorkflowExecutionHalt",
                packaged_blend_execution.BlendWorkflowExecutionHalt,
            ),
        )
        for module_name, name, canonical in expected:
            with self.subTest(module=module_name, name=name):
                self.assertIs(
                    pickle.loads(f"c{module_name}\n{name}\n.".encode("ascii")),
                    canonical,
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

    def test_artifact_stores_satisfy_governance_persistence_ports(self) -> None:
        for store_type in (ArtifactStore, SQLiteVectorArtifactStore):
            with self.subTest(store_type=store_type.__name__):
                store = object.__new__(store_type)
                self.assertIsInstance(
                    store,
                    packaged_governance_inventory.GovernanceInventoryReader,
                )
                self.assertIsInstance(
                    store,
                    packaged_governance_persistence.GovernanceArtifactWriter,
                )

    def test_authority_coverage_and_controller_decision_keep_canonical_owners(self) -> None:
        for name in packaged_governance_authority.__all__:
            with self.subTest(name=name):
                self.assertEqual(
                    "realized_core_governance.authority",
                    getattr(packaged_governance_authority, name).__module__,
                )
        for name in ("EffectDecision", "evaluate_effect_request"):
            with self.subTest(name=name):
                value = getattr(host_mediation, name)
                self.assertEqual("realized_core_engine.host_mediation", value.__module__)
                self.assertIs(value, getattr(packaged_host_mediation, name))
                self.assertIs(
                    pickle.loads(f"chost_mediation\n{name}\n.".encode("ascii")),
                    value,
                )

    def test_effect_receipt_semantics_and_controller_trace_capture_keep_canonical_owners(self) -> None:
        self.assertIs(
            host_mediation._effect_receipt,
            packaged_governance_trace.effect_trace_receipt,
        )
        self.assertEqual(
            packaged_governance_trace.EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
            host_mediation.EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
        )
        self.assertEqual(
            "realized_core_engine.host_mediation",
            host_mediation.record_effect_trace.__module__,
        )

    def test_constitutional_trace_keeps_canonical_owners(self) -> None:
        self.assertIs(
            packaged_constitutional_trace.canonical_trace_answer,
            packaged_governance_trace.canonical_trace_answer,
        )
        self.assertIs(
            packaged_constitutional_trace.effect_trace_signature,
            packaged_governance_trace.effect_trace_signature,
        )
        for name in (
            "state_composition_chain",
            "composition_chain_signature",
            "controller_decision_flow_signature",
            "llm_transcript_signature",
            "constitutional_trace_snapshot",
            "compare_bundle_trace_to_state",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    "realized_core_engine.constitutional_trace",
                    getattr(packaged_constitutional_trace, name).__module__,
                )

    def test_governance_declaration_helpers_keep_packaged_identities(self) -> None:
        for name in packaged_governance_declarations.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(skill_governance, name),
                    getattr(packaged_governance_declarations, name),
                )

    def test_skill_admission_keeps_controller_orchestration_and_package_policy_owner(self) -> None:
        self.assertEqual(
            "realized_core_governance.admission",
            packaged_governance_admission.evaluate_skill_policy_admission.__module__,
        )
        self.assertEqual(
            "realized_core_engine.skill_governance",
            skill_governance.evaluate_skill_admission.__module__,
        )
        self.assertIs(skill_governance, packaged_engine_skill_governance)
        self.assertIs(
            pickle.loads(b"cskill_governance\nevaluate_skill_admission\n."),
            skill_governance.evaluate_skill_admission,
        )

    def test_skill_current_use_keeps_package_rules_and_controller_artifact_adapter(self) -> None:
        for name in packaged_governance_current_use.__all__:
            with self.subTest(name=name):
                self.assertEqual(
                    "realized_core_governance.current_use",
                    getattr(packaged_governance_current_use, name).__module__,
                )
        for name in (
            "artifact_admitted_for_use",
            "artifact_admitted_for_use_with_governance",
            "artifact_current_use_admission",
        ):
            with self.subTest(name=name):
                function = getattr(skill_governance, name)
                self.assertEqual(
                    "realized_core_engine.skill_governance",
                    function.__module__,
                )
                self.assertIs(
                    pickle.loads(f"cskill_governance\n{name}\n.".encode("ascii")),
                    function,
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
