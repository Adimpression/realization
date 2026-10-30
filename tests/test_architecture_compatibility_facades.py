from __future__ import annotations

import pickle
import unittest

import applied_theory_types
import approval_governance
import args
import artifact
import artifact_answer_resolution
import artifact_contracts
import capability_runtime
import side
import side_runtime_dependencies
from artifact_contracts import ArtifactContentView, TitledArtifactContentView
import blend_context
import blend_operator
import blend_operator_store
import blend_session
import blend_workflow
import blend_workflow_execution
import blend_workflow_models
import blend_workflow_store
import blend_world
import blend_world_models
import blend_world_store
import controller_runtime
import controller_entrypoint_binding
import controller_governance_bridge
import controller_runtime_binding
import constitutional_trace
import data_governance
import decision_review
import decision_review_constructs
import decision_review_models
import decision_review_policy
import decision_review_projection
import direct_knowledge_reuse
import execution_framework_primitives
import execution_frameworks
import fence_extraction_strategy
import fallback_not_generation
import fallback_not_semantics
import gather_sources
import governance_inventory
import governed_closure_and_commitment
import governed_prior_learning_reuse
import governed_semantic_reduction_runtime
import governed_skill_access
import host_abi
import host_brokers
import host_realizers
import host_mediation
import host_interaction_action_dispatch
import host_interaction_actions
import host_interaction_context
import host_interaction_delegation
import host_interaction_models
import host_interaction_receipts
import host_interaction_resolution
import itemize
import itemize_models
import itemize_validation
import learn
import learning_context
import learning_context_markdown
import learning_context_paths
import learning_context_projection
import learning_context_skill_projection
import markdown_ir
import markdown_learning_artifact_semantics
import external_markdown_learning_pipeline
import macos_host_brokers
import non_achievedness_normalization
import normalize
import normalization_runtime_dependencies
import not_elaboration_ranking
import pure_theory_types
import publication
import publication_projection
import publication_render
import publication_validation
import python_skill_brokerization
import python_skill_host_transport
import prompt_directives
import retrieval_ranking
import review_composition
import run_bundle_io
import run_outcome_harvest_and_reporting
import runtime_controller_api
import runtime_governance_context
import runtime_temp
import python_skill_host
import semantic_prompt_posture
import skill_governance
import skill_governance_primitives
import skill_composition
import skill_compatibility_export
import skill_compatibility_import
import skill_compiler
import skill_export_projection
import skill_ir
import skill_invocation_contract
import skill_boundary_normalization
import skill_leaf_types
import skill_lifecycle
import skill_path_notation
import skill_registry
import skill_safety_governance
import skill_schema_io
import structured_learning_yaml
import store
import supplement
import system_state
import url_learning_capture
import virtual_mounts
import wasm_skill_runtime
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
from realized_core_semantics import applied_model as packaged_applied_theory_types
from realized_core_semantics import applied_primitives as packaged_applied_theory_primitives
from realized_core_semantics import decision_review as packaged_decision_review
from realized_core_semantics import identifiers as packaged_identifiers
from realized_core_semantics import itemization as packaged_itemization
from realized_core_semantics import markdown as packaged_markdown
from realized_core_semantics import normalization as packaged_normalization_primitives
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
from realized_blend_application import workflow_store as packaged_blend_application_workflow_store
from realized_blend_application import workflows as packaged_blend_application_workflows
from realized_blend_application import world_store as packaged_blend_application_world_store
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
from realized_core_engine import learning as packaged_engine_learning
from realized_core_engine import markdown_learning_artifact_semantics as packaged_markdown_learning_artifact_semantics
from realized_core_engine import constitutional_trace as packaged_constitutional_trace
from realized_core_engine import configuration as packaged_engine_configuration
from realized_core_engine import artifact_answer_resolution as packaged_artifact_answer_resolution
from realized_core_engine import artifact_semantics as packaged_artifact_semantics
from realized_core_engine import direct_knowledge_reuse as packaged_direct_knowledge_reuse
from realized_core_engine import fallback_not_generation as packaged_fallback_not_generation
from realized_core_engine import governed_closure_and_commitment as packaged_governed_closure_and_commitment
from realized_core_engine import governed_prior_learning_reuse as packaged_governed_prior_learning_reuse
from realized_core_engine import governance_inventory as packaged_engine_governance_inventory
from realized_core_engine import reduction_runtime as packaged_reduction_runtime
from realized_core_engine import non_achievedness_normalization as packaged_non_achievedness_normalization
from realized_core_engine import normalization_runtime_dependencies as packaged_normalization_runtime_dependencies
from realized_core_engine import not_elaboration_ranking as packaged_not_elaboration_ranking
from realized_core_engine import run_outcome_harvest_and_reporting as packaged_run_outcome_harvest_and_reporting
from realized_core_engine import prompt_directives as packaged_prompt_directives
from realized_core_engine import retrieval_ranking as packaged_retrieval_ranking
from realized_core_engine import semantic_prompt_posture as packaged_semantic_prompt_posture
from realized_core_engine import host_mediation as packaged_host_mediation
from realized_core_engine import controller_entrypoint_binding as packaged_controller_entrypoint_binding
from realized_core_engine import controller_governance_bridge as packaged_controller_governance_bridge
from realized_core_engine import controller_runtime as packaged_controller_runtime
from realized_core_engine import controller_runtime_binding as packaged_controller_runtime_binding
from realized_core_engine import governed_skill_access as packaged_governed_skill_access
from realized_core_engine import runtime_governance_context as packaged_runtime_governance_context
from realized_core_engine import skill_governance as packaged_engine_skill_governance
from realized_core_engine import structured_learning as packaged_structured_learning
from realized_core_engine import supplement as packaged_engine_supplement
from realized_core_engine import state as packaged_state
from realized_core_engine import store as packaged_engine_store
from realized_core_runtime import capabilities as packaged_runtime_capabilities
from realized_core_runtime import host_abi as packaged_runtime_host_abi
from realized_core_runtime import host_brokers as packaged_runtime_host_brokers
from realized_core_runtime import host_realizers as packaged_runtime_host_realizers
from realized_core_runtime import execution as packaged_runtime_execution
from realized_core_runtime import executor_support as packaged_executor_support
from realized_core_runtime import fence_extraction as packaged_fence_extraction
from realized_core_runtime import macos_brokers as packaged_macos_brokers
from realized_core_runtime import python_brokerization as packaged_python_brokerization
from realized_core_runtime import python_transport as packaged_python_transport
from realized_core_runtime import python_host as packaged_python_host
from realized_core_runtime import temporary as packaged_runtime_temporary
from realized_core_runtime import virtual_mounts as packaged_virtual_mounts
from realized_core_runtime import wasm as packaged_runtime_wasm
from workstation.app.cli import runtime_controller as packaged_runtime_controller_api
from realized_skill_semantics import composition as packaged_skill_composition
from realized_skill_semantics import compatibility as packaged_skill_compatibility
from realized_skill_semantics import declaration as packaged_skill_declaration
from realized_skill_semantics import execution as packaged_skill_execution
from realized_skill_semantics import leaves as packaged_skill_leaves
from realized_skill_semantics import ir as packaged_skill_ir
from realized_skill_semantics import invocation as packaged_skill_invocation
from realized_skill_semantics import normalization as packaged_skill_normalization
from realized_skill_semantics import paths as packaged_skill_paths
from store import ArtifactStore, SQLiteVectorArtifactStore
from workstation.skills.core import invocation_contract
from realized_skill_application import composition as packaged_skill_application_composition
from realized_skill_application import ir as packaged_skill_application_ir
from realized_skill_application import normalization as packaged_skill_application_normalization
from realized_exchange import artifact_yaml as packaged_artifact_yaml
from realized_exchange import compatibility_export as packaged_skill_compatibility_export
from realized_exchange import compatibility_import as packaged_skill_compatibility_import
from realized_exchange import compiler as packaged_skill_compiler
from realized_exchange import dependencies as packaged_exchange_dependencies
from realized_exchange import learning_context as packaged_learning_context
from realized_exchange import learning_context_skills as packaged_learning_context_skills
from realized_exchange import markdown_learning_pipeline as packaged_markdown_learning_pipeline
from realized_exchange import registry as packaged_skill_registry
from realized_exchange import run_bundle as packaged_run_bundle
from realized_exchange import skill_export as packaged_skill_export
from realized_exchange import skill_schema as packaged_skill_schema
from workstation.subject.core import itemize_validation as packaged_itemize_validation
from workstation.subject.core import gather_sources as packaged_gather_sources
from workstation.subject.core import decision_review_projection as packaged_decision_review_projection
from workstation.subject.core import decision_review_policy as packaged_decision_review_policy
from workstation.subject.core import decision_review as packaged_subject_decision_review
from workstation.subject.core import decision_review_constructs as packaged_subject_decision_review_constructs
from workstation.subject.core import itemization as packaged_subject_itemization
from workstation.subject.core import learning_context as packaged_subject_learning_context
from workstation.subject.core import learning_context_markdown as packaged_learning_context_markdown
from workstation.subject.core import learning_context_paths as packaged_subject_learning_context_paths
from workstation.subject.core import learning_context_projection as packaged_learning_context_projection
from workstation.subject.core import publication as packaged_publication
from workstation.subject.core import publication_projection as packaged_publication_projection
from workstation.subject.core import publication_render as packaged_publication_render
from workstation.subject.core import publication_validation as packaged_publication_validation
from workstation.subject.core import review_composition as packaged_review_composition
from workstation.subject.service import url_learning_capture as packaged_url_learning_capture


class ArchitectureCompatibilityFacadeTest(unittest.TestCase):
    def test_exchange_root_facades_keep_exact_module_identity(self) -> None:
        for facade, canonical in (
            (side, packaged_artifact_yaml),
            (side_runtime_dependencies, packaged_exchange_dependencies),
            (skill_compatibility_export, packaged_skill_compatibility_export),
            (skill_compatibility_import, packaged_skill_compatibility_import),
            (skill_compiler, packaged_skill_compiler),
            (skill_export_projection, packaged_skill_export),
            (skill_schema_io, packaged_skill_schema),
            (learning_context, packaged_learning_context),
            (
                learning_context_skill_projection,
                packaged_learning_context_skills,
            ),
            (run_bundle_io, packaged_run_bundle),
            (skill_registry, packaged_skill_registry),
        ):
            with self.subTest(module=facade.__name__):
                self.assertIs(facade, canonical)

    def test_subject_url_capture_keeps_legacy_module_identity(self) -> None:
        self.assertIs(url_learning_capture, packaged_url_learning_capture)

    def test_markdown_learning_facades_keep_exact_module_identity(self) -> None:
        self.assertIs(
            external_markdown_learning_pipeline,
            packaged_markdown_learning_pipeline,
        )
        self.assertIs(
            markdown_learning_artifact_semantics,
            packaged_markdown_learning_artifact_semantics,
        )
        self.assertIs(
            learning_context_markdown,
            packaged_learning_context_markdown,
        )

    def test_subject_projection_keeps_legacy_module_identity(self) -> None:
        self.assertIs(
            learning_context_projection,
            packaged_learning_context_projection,
        )

    def test_controller_and_runtime_root_aliases_keep_module_identity(self) -> None:
        for facade, canonical in (
            (capability_runtime, packaged_runtime_capabilities),
            (controller_entrypoint_binding, packaged_controller_entrypoint_binding),
            (controller_governance_bridge, packaged_controller_governance_bridge),
            (controller_runtime, packaged_controller_runtime),
            (controller_runtime_binding, packaged_controller_runtime_binding),
            (governed_skill_access, packaged_governed_skill_access),
            (host_mediation, packaged_host_mediation),
            (runtime_governance_context, packaged_runtime_governance_context),
            (skill_governance, packaged_engine_skill_governance),
            (store, packaged_engine_store),
        ):
            with self.subTest(module=facade.__name__):
                self.assertIs(facade, canonical)

    def test_workstation_runtime_controller_alias_keeps_module_identity(self) -> None:
        self.assertIs(runtime_controller_api, packaged_runtime_controller_api)

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

    def test_runtime_leaf_modules_keep_identity(self) -> None:
        self.assertIs(host_abi, packaged_runtime_host_abi)
        self.assertIs(host_brokers, packaged_runtime_host_brokers)
        self.assertIs(host_realizers, packaged_runtime_host_realizers)
        self.assertIs(macos_host_brokers, packaged_macos_brokers)
        self.assertIs(python_skill_brokerization, packaged_python_brokerization)
        self.assertIs(python_skill_host_transport, packaged_python_transport)
        self.assertIs(python_skill_host, packaged_python_host)
        self.assertIs(runtime_temp, packaged_runtime_temporary)
        self.assertIs(virtual_mounts, packaged_virtual_mounts)
        self.assertIs(wasm_skill_runtime, packaged_runtime_wasm)

    def test_controller_adapter_modules_keep_identity(self) -> None:
        self.assertIs(governance_inventory, packaged_engine_governance_inventory)
        self.assertIs(supplement, packaged_engine_supplement)

    def test_controller_state_and_reduction_modules_keep_identity(self) -> None:
        self.assertIs(system_state, packaged_state)
        self.assertIs(governed_semantic_reduction_runtime, packaged_reduction_runtime)

    def test_controller_artifact_and_non_achievedness_modules_keep_identity(self) -> None:
        self.assertIs(artifact, packaged_artifact_semantics)
        self.assertIs(fallback_not_generation, packaged_fallback_not_generation)
        self.assertIs(
            non_achievedness_normalization,
            packaged_non_achievedness_normalization,
        )
        self.assertIs(
            normalization_runtime_dependencies,
            packaged_normalization_runtime_dependencies,
        )
        self.assertIs(not_elaboration_ranking, packaged_not_elaboration_ranking)
        self.assertIs(structured_learning_yaml, packaged_structured_learning)

    def test_controller_policy_helpers_keep_their_historical_module_identity(self) -> None:
        self.assertIs(artifact_answer_resolution, packaged_artifact_answer_resolution)
        self.assertIs(direct_knowledge_reuse, packaged_direct_knowledge_reuse)
        self.assertIs(
            governed_closure_and_commitment,
            packaged_governed_closure_and_commitment,
        )
        self.assertIs(governed_prior_learning_reuse, packaged_governed_prior_learning_reuse)
        self.assertIs(
            run_outcome_harvest_and_reporting,
            packaged_run_outcome_harvest_and_reporting,
        )

    def test_applied_theory_types_keeps_its_historical_identity(self) -> None:
        self.assertIs(applied_theory_types, packaged_applied_theory_types)

    def test_controller_query_helpers_keep_their_historical_module_identity(self) -> None:
        self.assertIs(prompt_directives, packaged_prompt_directives)
        self.assertIs(retrieval_ranking, packaged_retrieval_ranking)
        self.assertIs(semantic_prompt_posture, packaged_semantic_prompt_posture)

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

    def test_subject_decision_policy_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(decision_review_policy, packaged_decision_review_policy)

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

    def test_subject_decision_projection_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(decision_review_projection, packaged_decision_review_projection)

    def test_subject_publication_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(publication, packaged_publication)

    def test_subject_publication_render_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(publication_render, packaged_publication_render)

    def test_subject_publication_validation_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(publication_validation, packaged_publication_validation)

    def test_subject_publication_projection_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(publication_projection, packaged_publication_projection)

    def test_subject_gather_sources_facade_keeps_packaged_module_identity(self) -> None:
        self.assertIs(gather_sources, packaged_gather_sources)

    def test_subject_itemization_validation_facade_keeps_packaged_identity(self) -> None:
        self.assertIs(
            itemize_validation.validate_itemization_session,
            packaged_itemize_validation.validate_itemization_session,
        )

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

    def test_skill_import_reexports_portable_compatibility_normalization(self) -> None:
        self.assertIs(
            skill_compatibility_import.normalized_skill_compatibility_payload,
            packaged_skill_compatibility.normalized_skill_compatibility_payload,
        )

    def test_legacy_skill_composition_pickle_globals_still_resolve(self) -> None:
        for name in packaged_skill_composition.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    pickle.loads(f"cskill_composition\n{name}\n.".encode("ascii")),
                    getattr(packaged_skill_composition, name),
                )

    def test_learning_token_constants_keep_their_historical_identity(self) -> None:
        self.assertIs(learn, packaged_engine_learning)
        for name in packaged_engine_learning.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(learn, name),
                    getattr(packaged_engine_learning, name),
                )
        self.assertIs(
            learn.LEARNING_STOP_TOKENS,
            packaged_semantic_text.LEARNING_STOP_TOKENS,
        )
        self.assertIs(
            learn.LEARNING_COMPONENT_BREAKS,
            packaged_semantic_text.LEARNING_COMPONENT_BREAKS,
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
            packaged_semantic_text.normalize_semantic_component_title,
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
                    getattr(packaged_normalization_primitives, name),
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

        self.assertIsInstance(artifact, ArtifactContentView)
        self.assertIsInstance(artifact, TitledArtifactContentView)
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
        self.assertIsNot(
            itemize.extract_itemized_candidates_from_learning_context,
            packaged_subject_itemization.extract_itemized_candidates_from_learning_context,
        )
        self.assertIsNot(
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
                    getattr(blend_workflow, name),
                    getattr(packaged_blend_workflows, name),
                )
        for name in ("BlendWorld", "BlendWorldMount"):
            with self.subTest(name=name):
                self.assertIs(
                    getattr(blend_world, name),
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
            (blend_workflow, packaged_blend_application_workflows),
            (blend_workflow_execution, packaged_blend_application_execution),
            (blend_workflow_store, packaged_blend_application_workflow_store),
            (blend_world, packaged_blend_application_worlds),
            (blend_world_store, packaged_blend_application_world_store),
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

    def test_constitutional_trace_keeps_exact_packaged_module_identity(self) -> None:
        self.assertIs(constitutional_trace, packaged_constitutional_trace)
        self.assertIs(
            constitutional_trace.canonical_trace_answer,
            packaged_governance_trace.canonical_trace_answer,
        )
        self.assertIs(
            constitutional_trace.effect_trace_signature,
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
                    getattr(constitutional_trace, name).__module__,
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

    def test_learning_token_normalizer_keeps_the_legacy_identity(self) -> None:
        self.assertIs(
            normalize.normalize_learning_lookup_token,
            packaged_semantic_text.normalize_learning_token,
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
