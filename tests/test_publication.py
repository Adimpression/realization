# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import replace
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from workstation.subject.core.decision_review import DecisionFrame, DecisionReviewItem
from workstation.subject.core.decision_review_policy import default_decision_policy_profile
from workstation.subject.core.decision_review_projection import DecisionAnalysisReceipt
from realized_exchange.learning_context import (
    LearningContext,
    LearningUnit,
    list_subject_imports,
    new_learning_source,
    new_subject_import,
    persist_learning_context,
    persist_learning_source,
    persist_subject_import,
)
from workstation.subject.core.publication import (
    Publication,
    PublicationBlock,
    PublicationClaim,
    PublicationComposition,
    PublicationCrossReference,
    PublicationEntity,
    PublicationReviewRecord,
    PublicationSection,
    PublicationSource,
    list_publication_compositions,
    publication_child_sections,
    publication_claim_ids_for_entity,
    publication_claim_ids_impacted_by_entity_ids,
    publication_claim_ids_impacted_by_source_ids,
    publication_claim_ids_impacted_by_unit_ids,
    publication_claim_ids_for_source,
    publication_diff_summary,
    publication_reviews_for_target,
    publication_xrefs_for_node,
)
from workstation.subject.core.publication_projection import (
    materialize_report_publication_from_learning_context,
    publication_composition_from_learning_context,
    publication_from_learning_context,
)
from workstation.subject.core.publication_render import render_publication_markdown, render_publication_typst
from workstation.subject.core.publication_validation import validate_publication
from workstation.subject.core.review_composition import ReviewItem, ReviewTransformReceipt, stable_review_transform_receipt_id


class PublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_publication_from_learning_context_surfaces_decision_outputs_and_transform_provenance(self) -> None:
        source = new_learning_source(
            subject_id="decision-publication",
            title="Decision Notes",
            source_ref="/tmp/decision_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Decision Notes\n")
        context = LearningContext(
            subject_id="decision-publication",
            canonical_title="Decision Publication",
            subject_family="Operations",
            units=(
                LearningUnit(
                    unit_id="unit_policy",
                    subject_id="decision-publication",
                    unit_kind="definition",
                    canonical_title="Policy Automation",
                    statement="Policy automation can reduce manual approval effort.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        frame = DecisionFrame(
            decision_frame_id="decfrm_demo",
            subject_id=context.subject_id,
            question="Should the report recommend policy automation?",
            decision_mode="decision_aid",
            current_state_ids=("state_current",),
            target_state_ids=("state_target",),
            primary_objective_ids=("objective_reduce_manual_review",),
            created_at_epoch_ms=1,
            updated_at_epoch_ms=1,
        )
        policy_profile = default_decision_policy_profile(
            decision_frame_id=frame.decision_frame_id,
            build_epoch_ms=2,
            profile_kind="balanced",
        )
        decision_review_items = (
            DecisionReviewItem(
                decision_review_item_id="decitm_current",
                review_item_id="rvw_current",
                decision_frame_id=frame.decision_frame_id,
                decision_role="current_state",
                ordering=1,
                included=True,
                metadata={"canonical_label": "Manual Review"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decitm_target",
                review_item_id="rvw_target",
                decision_frame_id=frame.decision_frame_id,
                decision_role="target_state",
                ordering=2,
                included=True,
                metadata={"canonical_label": "Policy Automation"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decitm_transition",
                review_item_id="rvw_transition",
                decision_frame_id=frame.decision_frame_id,
                decision_role="transition_candidate",
                ordering=3,
                included=True,
                metadata={
                    "canonical_label": "Introduce Approval Routing",
                    "source_state_decision_review_item_id": "decitm_current",
                    "target_state_decision_review_item_id": "decitm_target",
                    "changed_capability_decision_review_item_ids": ("decitm_capability",),
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="decitm_dependency",
                review_item_id="rvw_dependency",
                decision_frame_id=frame.decision_frame_id,
                decision_role="dependency",
                ordering=4,
                included=True,
                metadata={"canonical_label": "Workflow Inventory"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decitm_boundary",
                review_item_id="rvw_boundary",
                decision_frame_id=frame.decision_frame_id,
                decision_role="boundary",
                ordering=5,
                included=True,
                metadata={"canonical_label": "Approval Governance Boundary"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decitm_capability",
                review_item_id="rvw_capability",
                decision_frame_id=frame.decision_frame_id,
                decision_role="capability",
                ordering=6,
                included=True,
                metadata={
                    "canonical_label": "Routing Engine",
                    "required_dependency_decision_review_item_ids": ("decitm_dependency",),
                    "crossed_boundary_decision_review_item_ids": ("decitm_boundary",),
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="decitm_actor",
                review_item_id="rvw_actor",
                decision_frame_id=frame.decision_frame_id,
                decision_role="actor",
                ordering=7,
                included=True,
                metadata={"canonical_label": "Approvals Team"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decitm_decision",
                review_item_id="rvw_decision",
                decision_frame_id=frame.decision_frame_id,
                decision_role="decision_candidate",
                ordering=8,
                included=True,
                metadata={
                    "canonical_label": "Policy Automation",
                    "selected_transition_decision_review_item_ids": ("decitm_transition",),
                    "assigned_actor_decision_review_item_ids": ("decitm_actor",),
                },
            ),
        )
        receipt = DecisionAnalysisReceipt(
            receipt_id="decrct_demo",
            decision_frame_id=frame.decision_frame_id,
            model_snapshot_hash="modelhash",
            policy_snapshot_hash=policy_profile.content_hash(),
            admissible_transition_ids=("transition_one",),
            valid_decision_ids=("Policy Automation",),
            executable_decision_ids=("Policy Automation",),
            risk_summary={
                "capability_risk_count": 0,
                "transition_risk_count": 0,
                "included_item_count": 8,
                "supporting_evidence_count": 1,
                "boundary_count": 0,
                "transition_candidate_count": 1,
                "dependency_count": 0,
            },
            reachable_pairs_count=1,
            blocking_conditions=(),
            recommendation_status="recommendable",
            created_at_epoch_ms=3,
            metadata={
                "policy_profile_id": policy_profile.policy_profile_id,
                "policy_profile_kind": policy_profile.profile_kind,
                "policy_rule_ids": tuple(policy_profile.rule_ids),
                "recommended_option_ids": ("Policy Automation",),
                "candidate_path_count": 1,
                "candidate_path_signatures": ("Manual Review --Introduce Approval Routing--> Policy Automation",),
                "option_outcomes": (
                    {
                        "option_id": "Policy Automation",
                        "status": "recommended",
                        "score": 120,
                        "reasons": ("executable", "source support present"),
                    },
                ),
            },
        )
        transform_receipt = ReviewTransformReceipt(
            receipt_id=stable_review_transform_receipt_id(
                review_item_id="rvw_demo",
                transform_kind="split",
                output_snapshot_hash="split1",
            ),
            review_item_id="rvw_demo",
            review_composition_id="rvwcomp_demo",
            transform_kind="split",
            input_snapshot_hash="before",
            output_snapshot_hash="after",
            operator="draft_split",
            notes="Split a draft item into decision-oriented child items.",
            created_at_epoch_ms=4,
        )

        publication, sections, blocks, claims, sources, _entities, _xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            title="Decision Publication Report",
            build_epoch_ms=5,
            composition_metadata={
                "decision_frame": frame.to_dict(),
                "decision_policy_profile": policy_profile.to_dict(),
                "decision_review_items": [item.to_dict() for item in decision_review_items],
                "decision_analysis_receipt": receipt.to_dict(),
                "review_transform_receipts": [transform_receipt.to_dict()],
            },
        )
        rendered_markdown = render_publication_markdown(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
        )
        rendered_typst = render_publication_typst(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
        )

        block_kinds = {block.block_kind for block in blocks}
        block_kind_by_id = {block.block_id: block.block_kind for block in blocks}
        summary_section = next(section for section in sections if section.section_id == "report-summary")
        analysis_section = next(section for section in sections if section.section_id == "report-analysis")
        option_section = next(section for section in sections if section.section_id == "report-analysis-options")
        model_section = next(section for section in sections if section.section_id == "report-analysis-model")
        risk_section = next(section for section in sections if section.section_id == "report-analysis-risk")
        implementation_section = next(section for section in sections if section.section_id == "report-implementation")
        implementation_guidance_section = next(section for section in sections if section.section_id == "report-implementation-guidance")
        appendix_section = next(section for section in sections if section.section_id == "report-appendix")
        appendix_receipt_section = next(section for section in sections if section.section_id == "report-appendix-receipt")

        self.assertIn("decision_summary", block_kinds)
        self.assertIn("decision_matrix", block_kinds)
        self.assertIn("decision_transition_roadmap", block_kinds)
        self.assertIn("decision_simple_diagram", block_kinds)
        self.assertIn("decision_ranking_summary", block_kinds)
        self.assertIn("decision_dependency_checklist", block_kinds)
        self.assertIn("decision_risk_matrix", block_kinds)
        self.assertIn("decision_recommendation_receipt", block_kinds)
        self.assertIn("review_transform_receipts", block_kinds)
        self.assertEqual(
            publication.root_section_ids,
            ("report-summary", "report-definitions", "report-analysis", "report-implementation", "report-appendix"),
        )
        self.assertEqual(analysis_section.child_section_ids, ("report-analysis-options", "report-analysis-model", "report-analysis-risk"))
        self.assertEqual(implementation_section.child_section_ids, ("report-implementation-guidance",))
        self.assertEqual(appendix_section.child_section_ids, ("report-appendix-receipt",))
        self.assertEqual(option_section.title, "Option Assessment and Ranking")
        self.assertEqual(model_section.title, "Path and Coordination Model")
        self.assertEqual(risk_section.title, "Dependencies and Risk")
        self.assertEqual(implementation_guidance_section.title, "Execution Guidance")
        self.assertEqual(appendix_receipt_section.title, "Decision Receipt and Audit Trail")
        self.assertIn("decision_summary", {block_kind_by_id[block_id] for block_id in summary_section.block_ids})
        self.assertIn("decision_matrix", {block_kind_by_id[block_id] for block_id in option_section.block_ids})
        self.assertIn("decision_ranking_summary", {block_kind_by_id[block_id] for block_id in option_section.block_ids})
        self.assertIn("decision_transition_roadmap", {block_kind_by_id[block_id] for block_id in model_section.block_ids})
        self.assertIn("decision_simple_diagram", {block_kind_by_id[block_id] for block_id in model_section.block_ids})
        self.assertIn("decision_dependency_checklist", {block_kind_by_id[block_id] for block_id in risk_section.block_ids})
        self.assertIn("decision_risk_matrix", {block_kind_by_id[block_id] for block_id in risk_section.block_ids})
        self.assertIn("decision_execution_guidance", {block_kind_by_id[block_id] for block_id in implementation_guidance_section.block_ids})
        self.assertIn("decision_recommendation_receipt", {block_kind_by_id[block_id] for block_id in appendix_receipt_section.block_ids})
        self.assertIn("review_transform_receipts", {block_kind_by_id[block_id] for block_id in appendix_receipt_section.block_ids})
        self.assertIn("Decision Recommendation", rendered_markdown)
        self.assertIn("### 3.1 Option Assessment and Ranking", rendered_markdown)
        self.assertIn("### 3.2 Path and Coordination Model", rendered_markdown)
        self.assertIn("### 3.3 Dependencies and Risk", rendered_markdown)
        self.assertIn("### 4.1 Execution Guidance", rendered_markdown)
        self.assertIn("### 5.1 Decision Receipt and Audit Trail", rendered_markdown)
        self.assertIn("Decision Option Matrix", rendered_markdown)
        self.assertIn("Decision Transition Roadmap", rendered_markdown)
        self.assertIn("Decision Model Diagram", rendered_markdown)
        self.assertIn("Recommended option: Policy Automation", rendered_markdown)
        self.assertIn("Recommended path:", rendered_markdown)
        self.assertIn("Recommended actors: Approvals Team", rendered_markdown)
        self.assertIn("Recommended capabilities: Routing Engine", rendered_markdown)
        self.assertIn("Recommended dependencies: Workflow Inventory", rendered_markdown)
        self.assertIn("Recommended boundaries: Approval Governance Boundary", rendered_markdown)
        self.assertIn("Decision Ranking Summary", rendered_markdown)
        self.assertIn("Decision Dependency Checklist", rendered_markdown)
        self.assertIn("Decision Risk Matrix", rendered_markdown)
        self.assertIn("Case Frame", rendered_markdown)
        self.assertIn("Execution Guidance", rendered_markdown)
        self.assertIn("Decision Recommendation Receipt", rendered_markdown)
        self.assertIn("Decision question: Should the report recommend policy automation?", rendered_markdown)
        self.assertIn("Recommendation status: recommendable.", rendered_markdown)
        self.assertIn("Option | Status | Score | Transitions | Actors | Basis", rendered_markdown)
        self.assertIn(
            "Policy Automation | recommended | 120 | Manual Review → Introduce Approval Routing → Policy Automation | Approvals Team | Conclusion: executable. Evidence: source support present.",
            rendered_markdown,
        )
        self.assertIn("Top ranked option: Policy Automation (score 120)", rendered_markdown)
        self.assertIn("Policy guidance:", rendered_markdown)
        self.assertIn("Why the recommendation leads:", rendered_markdown)
        self.assertIn("Ranking rules:", rendered_markdown)
        self.assertIn("Candidate path count: 1", rendered_markdown)
        self.assertIn("Top option transitions: Manual Review → Introduce Approval Routing → Policy Automation", rendered_markdown)
        self.assertIn("Top option actors: Approvals Team", rendered_markdown)
        self.assertIn("Top option capabilities: Routing Engine", rendered_markdown)
        self.assertIn("Top option dependencies: Workflow Inventory", rendered_markdown)
        self.assertIn("Manual Review → Introduce Approval Routing → Policy Automation", rendered_markdown)
        self.assertIn("Primary responsible actors:", rendered_markdown)
        self.assertIn("- Approvals Team", rendered_markdown)
        self.assertIn("Capabilities activated in the recommendation:", rendered_markdown)
        self.assertIn("- Routing Engine", rendered_markdown)
        self.assertIn("Implementation prerequisites:", rendered_markdown)
        self.assertIn("- Workflow Inventory", rendered_markdown)
        self.assertIn("Coordination boundaries to govern:", rendered_markdown)
        self.assertIn("- Approval Governance Boundary", rendered_markdown)
        self.assertIn("Draft Transform Provenance", rendered_markdown)
        self.assertIn("Policy Automation", rendered_markdown)
        self.assertNotIn("Decision question: Should the report recommend policy automation?.", rendered_markdown)
        self.assertIn("Decision Risk Matrix", rendered_typst)
        self.assertIn("Decision Recommendation Receipt", rendered_typst)
        self.assertIn("Decision Transition Roadmap", rendered_typst)
        self.assertIn("Decision Model Diagram", rendered_typst)
        self.assertIn("Decision Ranking Summary", rendered_typst)
        self.assertIn('#heading(level: 2, numbering: none)[3.1. Option Assessment and Ranking]', rendered_typst)
        self.assertIn('#heading(level: 2, numbering: none)[3.2. Path and Coordination Model]', rendered_typst)
        self.assertIn('#heading(level: 2, numbering: none)[3.3. Dependencies and Risk]', rendered_typst)
        self.assertIn('#heading(level: 2, numbering: none)[4.1. Execution Guidance]', rendered_typst)
        self.assertEqual(rendered_markdown.count("Governed report projection derived from the current LearningContext snapshot"), 0)
        self.assertIn("Should the report recommend policy automation?", rendered_typst)
        self.assertIn("Policy Automation", rendered_typst)
        self.assertIn("Approvals Team", rendered_typst)
        self.assertIn("Governance and controls", rendered_typst)
        self.assertIn("Assessment summary", rendered_typst)
        self.assertIn("Recommended option", rendered_typst)
        self.assertIn("Recommended path and coordination", rendered_typst)
        self.assertIn("Current state", rendered_typst)
        self.assertIn("Transition candidates", rendered_typst)
        self.assertIn("Capabilities", rendered_typst)
        self.assertIn("Boundaries to govern", rendered_typst)
        self.assertIn("Ranked option rationale", rendered_typst)

    def test_publication_from_learning_context_projects_section_guidance_from_composition_metadata(self) -> None:
        source = new_learning_source(
            subject_id="section-guidance-demo",
            title="Section Guidance Demo",
            source_ref="/tmp/section_guidance.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Section Guidance Demo\n")
        context = LearningContext(
            subject_id="section-guidance-demo",
            canonical_title="Section Guidance Demo",
            subject_family="Operations",
            units=(
                LearningUnit(
                    unit_id="unit_summary",
                    subject_id="section-guidance-demo",
                    unit_kind="definition",
                    canonical_title="Program Overview",
                    statement="The program is modernizing service access.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        publication, sections, blocks, _claims, _sources, _entities, _xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            title="Section Guidance Demo Report",
            build_epoch_ms=5,
            composition_metadata={
                "section_guidance_by_id": {
                    "report-summary": {
                        "label": "Executive summary brief",
                        "text": "Lead with the approved decision and the reason the reader should trust it.",
                        "mode": "manual",
                    }
                }
            },
        )

        summary_section = next(section for section in sections if section.section_id == "report-summary")
        section_guidance_block = next(block for block in blocks if block.block_kind == "section_guidance")
        markdown = render_publication_markdown(
            publication,
            sections=sections,
            blocks=blocks,
            claims=(),
            sources=(),
        )

        self.assertIn(section_guidance_block.block_id, summary_section.block_ids)
        self.assertEqual(section_guidance_block.title, "Executive summary brief")
        self.assertIn("Lead with the approved decision", section_guidance_block.body)
        self.assertIn("Executive summary brief", markdown)
        self.assertIn("Lead with the approved decision", markdown)

    def test_publication_from_learning_context_generates_review_owned_blocks_for_non_paragraph_render_kinds(self) -> None:
        source = new_learning_source(
            subject_id="review-blocks",
            title="Review Blocks Notes",
            source_ref="/tmp/review_blocks.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Review Blocks\n")
        context = LearningContext(
            subject_id="review-blocks",
            canonical_title="Review Blocks Demo",
            subject_family="Operations",
            units=(
                LearningUnit(
                    unit_id="unit_table",
                    subject_id="review-blocks",
                    unit_kind="definition",
                    canonical_title="Control Criteria",
                    statement="Control criteria should be reviewed in a structured table.",
                    structured_fields={
                        "table_headers": ["Criterion", "Meaning"],
                        "table_rows": [
                            ["Coverage", "The control spans the critical path"],
                            ["Evidence", "The control has source-backed support"],
                        ],
                    },
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        review_item = ReviewItem(
            review_item_id="rvw_table",
            subject_id=context.subject_id,
            source_itemized_item_id="itm_table",
            source_unit_id="unit_table",
            semantic_kind="table_like",
            render_kind="typst_table",
            evidence_mode="source_basis_panel",
            transform_mode="convert_to_table",
            included=True,
            ordering=1,
            notes="Control criteria should be reviewed in a structured table.",
            metadata={"canonical_label": "Control Criteria"},
            status="active",
        )
        publication, sections, blocks, claims, sources, _entities, _xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            title="Review Blocks Report",
            build_epoch_ms=10,
            review_items=(review_item,),
        )

        rendered_markdown = render_publication_markdown(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
        )
        rendered_typst = render_publication_typst(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
        )
        block_kinds = {block.block_kind for block in blocks}

        self.assertIn("review_typst_table", block_kinds)
        self.assertIn("Criterion | Meaning", rendered_markdown)
        self.assertIn("Coverage | The control spans the critical path", rendered_markdown)
        self.assertIn("Control Criteria", rendered_typst)
        self.assertIn("#grid(", rendered_typst)

    def test_materialize_report_publication_from_learning_context_persists_separate_publication_tree(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id="kinematics",
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_solver",
                    subject_id="kinematics",
                    unit_kind="ability",
                    canonical_title="Solve Constant Acceleration",
                    statement="Use the constant-acceleration equations to solve missing motion values.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_example",
                    subject_id="kinematics",
                    unit_kind="example",
                    canonical_title="Ball Drop Example",
                    statement="A falling ball example provides supporting motion evidence.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Kinematics Report",
            build_epoch_ms=0,
        )

        publication_path = Path(str(report["publication_path"]))
        build_path = Path(str(report["build_path"]))
        self.assertTrue(publication_path.is_file())
        self.assertTrue(build_path.is_file())
        self.assertEqual(report["validation_status"], "ok")
        self.assertGreaterEqual(int(report["block_count"]), 1)
        self.assertGreaterEqual(int(report["xref_count"]), 1)
        self.assertGreaterEqual(int(report["entity_count"]), 1)
        self.assertGreaterEqual(int(report["review_count"]), 1)
        publication_root = publication_path.parent
        self.assertEqual(publication_root.parent.name, "publications")
        self.assertFalse((publication_root / "report.json").exists())
        self.assertTrue((publication_root / "blocks").is_dir())
        self.assertTrue(any((publication_root / "blocks").glob("*.json")))
        self.assertTrue((publication_root / "entities").is_dir())
        self.assertTrue(any((publication_root / "entities").glob("*.json")))
        self.assertTrue((publication_root / "xrefs").is_dir())
        self.assertTrue(any((publication_root / "xrefs").glob("*.json")))
        self.assertTrue((publication_root / "reviews").is_dir())
        self.assertTrue(any((publication_root / "reviews").glob("*.json")))
        output_root = publication_root / "outputs" / str(report["build_id"])
        self.assertTrue((output_root / "report.pdf").is_file())
        self.assertTrue((output_root / "report.typ").is_file())
        self.assertTrue((output_root / "report.md").is_file())
        rendered_markdown = (output_root / "report.md").read_text(encoding="utf-8")
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        self.assertIn("Executive Summary", rendered_markdown)
        self.assertIn("Key Findings", rendered_markdown)
        self.assertIn("## Sources", rendered_markdown)
        self.assertIn("## Build Notes", rendered_markdown)
        self.assertIn("[S1]", rendered_markdown)
        self.assertNotIn("Sources: ", rendered_markdown)
        self.assertIn("GOVERNED INSIGHT REPORT", rendered_typst)
        self.assertIn("Executive Summary", rendered_typst)
        self.assertIn("Key Findings", rendered_typst)
        self.assertIn("= Sources <sources>", rendered_typst)
        self.assertIn("Source Register", rendered_typst)
        self.assertIn("Build Notes", rendered_typst)
        self.assertIn("SECTION 01", rendered_typst)
        self.assertIn("Source 01", rendered_typst)
        self.assertLess(rendered_typst.find("Key Findings"), rendered_typst.find("Source Register"))
        self.assertLess(rendered_typst.find("SECTION 01"), rendered_typst.find("= Sources <sources>"))
        self.assertNotIn("Report Navigation", rendered_typst)
        self.assertNotIn("Traceable units", rendered_typst)
        self.assertNotIn("Source basis", rendered_typst)
        build_payload = json.loads(build_path.read_text(encoding="utf-8"))
        self.assertEqual(build_payload["validation_report"]["status"], "ok")
        self.assertEqual(build_payload["build_status"], "ok")
        typst_compile = build_payload["validation_report"].get("render_validation", {}).get("typst_compile", {})
        if shutil.which("typst"):
            self.assertEqual(typst_compile.get("status"), "ok")
        else:
            self.assertEqual(typst_compile.get("status"), "unavailable")

    def test_materialized_report_normalizes_workspace_source_paths_to_relative_labels(self) -> None:
        workspace = self.root / "workspace"
        source_path = workspace / "trials" / "chemistry" / "motion-notes.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("# Motion Notes\n", encoding="utf-8")
        (self.root / "SESSION.json").write_text(
            json.dumps({"workspace_path": str(workspace.resolve())}),
            encoding="utf-8",
        )

        source = new_learning_source(
            subject_id="chemistry",
            title="Chemistry Notes",
            source_ref=str(source_path.resolve()),
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Chemistry Notes\n")
        context = LearningContext(
            subject_id="chemistry",
            canonical_title="Chemistry Notes",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_conservation",
                    subject_id="chemistry",
                    unit_kind="definition",
                    canonical_title="Conservation",
                    statement="Conservation constrains grouped counting relations.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Chemistry Report",
            build_epoch_ms=0,
        )

        publication_root = Path(str(report["publication_path"])).parent
        output_root = publication_root / "outputs" / str(report["build_id"])
        rendered_markdown = (output_root / "report.md").read_text(encoding="utf-8")
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        source_payload = json.loads(next((publication_root / "sources").glob("*.json")).read_text(encoding="utf-8"))

        self.assertEqual(source_payload["source_ref"], "trials/chemistry/motion-notes.md")
        self.assertIn("trials/chemistry/motion-notes.md", rendered_markdown)
        self.assertIn("trials/chemistry/motion-notes.md", rendered_typst)
        self.assertNotIn(str(source_path.resolve()), rendered_markdown)
        self.assertNotIn(str(source_path.resolve()), rendered_typst)

    def test_materialized_report_normalizes_repo_source_paths_to_relative_labels_without_session_workspace(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        source_path = repo_root / "trials" / "chemistry" / "08_LEARN_CHEMISTRY_RELATIONS_IDEAL_GAS.md"

        source = new_learning_source(
            subject_id="chemistry-repo-path",
            title="Chemistry Relations 08 — Ideal Gas State Relation",
            source_ref=str(source_path.resolve()),
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Chemistry Relations 08 — Ideal Gas State Relation\n")
        context = LearningContext(
            subject_id="chemistry-repo-path",
            canonical_title="Chemistry Relations 08 — Ideal Gas State Relation",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_ideal_gas",
                    subject_id="chemistry-repo-path",
                    unit_kind="relation",
                    canonical_title="Pressure from amount, temperature, and volume",
                    statement="The ideal gas law connects pressure, amount, temperature, and volume.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Chemistry Repo Path Report",
            build_epoch_ms=0,
        )

        publication_root = Path(str(report["publication_path"])).parent
        output_root = publication_root / "outputs" / str(report["build_id"])
        rendered_markdown = (output_root / "report.md").read_text(encoding="utf-8")
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        source_payload = json.loads(next((publication_root / "sources").glob("*.json")).read_text(encoding="utf-8"))

        self.assertEqual(source_payload["source_ref"], "trials/chemistry/08_LEARN_CHEMISTRY_RELATIONS_IDEAL_GAS.md")
        self.assertIn("trials/chemistry/08_LEARN_CHEMISTRY_RELATIONS_IDEAL_GAS.md", rendered_markdown)
        self.assertIn("trials/chemistry/08\\_LEARN\\_CHEMISTRY\\_RELATIONS\\_IDEAL\\_GAS.md", rendered_typst)
        self.assertNotIn(str(source_path.resolve()), rendered_markdown)
        self.assertNotIn(str(source_path.resolve()), rendered_typst)

    def test_publication_from_learning_context_preserves_explicit_composition_order(self) -> None:
        source = new_learning_source(
            subject_id="ordering",
            title="Ordering Notes",
            source_ref="notes/ordering.md",
            source_kind="markdown",
        )
        persist_learning_source(self.root, source, source_text="# Ordering\n")
        import_a = LearningContext(
            subject_id="import-a",
            canonical_title="Import A",
            governance_status="active",
        )
        import_b = LearningContext(
            subject_id="import-b",
            canonical_title="Import B",
            governance_status="active",
        )
        persist_learning_context(self.root, import_a)
        persist_learning_context(self.root, import_b)
        context = LearningContext(
            subject_id="ordering",
            canonical_title="Ordering Demo",
            subject_family="Physics / Ordering",
            units=(
                LearningUnit(
                    unit_id="unit_alpha",
                    subject_id="ordering",
                    unit_kind="definition",
                    canonical_title="Alpha",
                    statement="Alpha statement.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_beta",
                    subject_id="ordering",
                    unit_kind="relation",
                    canonical_title="Beta",
                    statement="Beta statement.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_gamma",
                    subject_id="ordering",
                    unit_kind="ability",
                    canonical_title="Gamma",
                    statement="Gamma statement.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        persist_subject_import(
            self.root,
            new_subject_import(
                active_subject_id="ordering",
                active_subject_version_id=context.content_hash(),
                active_subject_title=context.canonical_title,
                source_subject_id=import_a.subject_id,
                source_subject_version_id=import_a.content_hash(),
                source_subject_title=import_a.canonical_title,
                rationale="Use import A.",
            ),
        )
        persist_subject_import(
            self.root,
            new_subject_import(
                active_subject_id="ordering",
                active_subject_version_id=context.content_hash(),
                active_subject_title=context.canonical_title,
                source_subject_id=import_b.subject_id,
                source_subject_version_id=import_b.content_hash(),
                source_subject_title=import_b.canonical_title,
                rationale="Use import B.",
            ),
        )

        selected_import_ids = (
            next(item.import_id for item in list_subject_imports(self.root, "ordering") if item.source_subject_id == "import-b"),
            next(item.import_id for item in list_subject_imports(self.root, "ordering") if item.source_subject_id == "import-a"),
        )
        publication, sections, _blocks, claims, sources, _entities, _xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            included_unit_ids=("unit_gamma", "unit_alpha", "unit_beta"),
            selected_subject_import_ids=selected_import_ids,
            section_ids=("report-analysis", "report-summary", "report-definitions"),
        )

        self.assertEqual(
            tuple(claim.related_unit_ids[0] for claim in claims),
            ("unit_gamma", "unit_alpha", "unit_beta"),
        )
        self.assertEqual(
            tuple(section.section_id for section in sections),
            ("report-analysis", "report-summary", "report-definitions"),
        )
        imported_titles = tuple(
            source_item.title
            for source_item in sources
            if source_item.trust_class == "subject_import"
        )
        self.assertEqual(
            imported_titles,
            ("Imported Subject: Import B", "Imported Subject: Import A"),
        )

    def test_publication_render_preserves_explicit_composition_order_in_key_findings(self) -> None:
        source = new_learning_source(
            subject_id="ordering-render",
            title="Ordering Render Notes",
            source_ref="notes/ordering-render.md",
            source_kind="markdown",
        )
        persist_learning_source(self.root, source, source_text="# Ordering Render\n")
        context = LearningContext(
            subject_id="ordering-render",
            canonical_title="Ordering Render Demo",
            governance_status="active",
            units=(
                LearningUnit(
                    unit_id="unit_alpha",
                    subject_id="ordering-render",
                    unit_kind="definition",
                    canonical_title="Alpha",
                    statement="Alpha statement.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_beta",
                    subject_id="ordering-render",
                    unit_kind="relation",
                    canonical_title="Beta",
                    statement="Beta statement.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_gamma",
                    subject_id="ordering-render",
                    unit_kind="ability",
                    canonical_title="Gamma",
                    statement="Gamma statement.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
        )
        persist_learning_context(self.root, context)

        publication, sections, blocks, claims, sources, _entities, _xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            included_unit_ids=("unit_gamma", "unit_alpha", "unit_beta"),
        )
        rendered_markdown = render_publication_markdown(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
        )
        rendered_typst = render_publication_typst(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
        )

        self.assertLess(rendered_markdown.find("Gamma statement."), rendered_markdown.find("Alpha statement."))
        self.assertLess(rendered_markdown.find("Alpha statement."), rendered_markdown.find("Beta statement."))
        self.assertLess(rendered_typst.find("Gamma statement."), rendered_typst.find("Alpha statement."))
        self.assertLess(rendered_typst.find("Alpha statement."), rendered_typst.find("Beta statement."))

    def test_materialized_report_consumes_draft_review_leaf_structure(self) -> None:
        source = new_learning_source(
            subject_id="review-structured",
            title="Controls Notes",
            source_ref="notes/controls.md",
            source_kind="markdown",
        )
        persist_learning_source(self.root, source, source_text="# Controls\n")
        context = LearningContext(
            subject_id="review-structured",
            canonical_title="Review Structured Demo",
            governance_status="active",
            units=(
                LearningUnit(
                    unit_id="unit_controls",
                    subject_id="review-structured",
                    unit_kind="definition",
                    canonical_title="Controls",
                    statement="Access and audit controls matter.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
        )
        persist_learning_context(self.root, context)

        base_composition = publication_composition_from_learning_context(
            self.root,
            context,
            included_unit_ids=("unit_controls",),
        )
        review_parent = ReviewItem(
            review_item_id="rvw_parent_controls",
            subject_id=context.subject_id,
            source_itemized_item_id="itm_controls",
            source_unit_id="unit_controls",
            semantic_kind="claim",
            render_kind="paragraph",
            evidence_mode="inline_handles",
            transform_mode="split",
            included=False,
            ordering=1,
            child_review_item_ids=("rvw_child_access", "rvw_child_audit"),
            source_refs=(source.source_id,),
            metadata={"canonical_label": "Controls"},
        )
        review_child_access = ReviewItem(
            review_item_id="rvw_child_access",
            subject_id=context.subject_id,
            source_itemized_item_id="itm_controls",
            source_unit_id="unit_controls",
            parent_review_item_id="rvw_parent_controls",
            semantic_kind="definition",
            render_kind="paragraph",
            evidence_mode="inline_handles",
            transform_mode="keep",
            included=True,
            ordering=1,
            source_refs=(source.source_id,),
            metadata={"canonical_label": "Access Controls", "origin": "review_split"},
        )
        review_child_audit = ReviewItem(
            review_item_id="rvw_child_audit",
            subject_id=context.subject_id,
            source_itemized_item_id="itm_controls",
            source_unit_id="unit_controls",
            parent_review_item_id="rvw_parent_controls",
            semantic_kind="definition",
            render_kind="paragraph",
            evidence_mode="inline_handles",
            transform_mode="keep",
            included=True,
            ordering=2,
            source_refs=(source.source_id,),
            metadata={"canonical_label": "Audit Controls", "origin": "review_split"},
        )
        composition = PublicationComposition.from_dict(
            {
                **base_composition.to_dict(),
                "metadata": {
                    **dict(base_composition.metadata),
                    "draft_review_composition_id": "rvwcomp_demo",
                    "draft_review_items": [
                        review_parent.to_dict(),
                        review_child_access.to_dict(),
                        review_child_audit.to_dict(),
                    ],
                },
            }
        )

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            composition=composition,
            build_epoch_ms=0,
        )

        publication_root = Path(str(report["publication_path"])).parent
        output_root = publication_root / "outputs" / str(report["build_id"])
        rendered_markdown = (output_root / "report.md").read_text(encoding="utf-8")
        claim_payloads = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((publication_root / "claims").glob("*.json"))
        ]

        self.assertEqual(tuple(payload["statement"] for payload in claim_payloads), ("Access Controls", "Audit Controls"))
        self.assertIn("Access Controls", rendered_markdown)
        self.assertIn("Audit Controls", rendered_markdown)
        self.assertLess(rendered_markdown.find("Access Controls"), rendered_markdown.find("Audit Controls"))

    def test_publication_composition_explicit_scope_excludes_question_units(self) -> None:
        source = new_learning_source(
            subject_id="composition-question",
            title="Composition Question Notes",
            source_ref="notes/composition-question.md",
            source_kind="markdown",
        )
        persist_learning_source(self.root, source, source_text="# Composition Question\n")
        context = LearningContext(
            subject_id="composition-question",
            canonical_title="Composition Question Demo",
            governance_status="active",
            units=(
                LearningUnit(
                    unit_id="unit_question",
                    subject_id="composition-question",
                    unit_kind="relation",
                    canonical_title="Question Unit",
                    statement="How do you calculate P_times_V from n, R, T?",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_statement",
                    subject_id="composition-question",
                    unit_kind="relation",
                    canonical_title="Statement Unit",
                    statement="Pressure relates to amount, temperature, and volume.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
        )
        persist_learning_context(self.root, context)

        composition = publication_composition_from_learning_context(
            self.root,
            context,
            included_unit_ids=("unit_question", "unit_statement"),
        )

        self.assertEqual(composition.included_unit_ids, ("unit_statement",))
        self.assertIn("unit_question", composition.excluded_unit_ids)

    def test_materialized_report_typst_compiles_when_typst_is_available(self) -> None:
        if not shutil.which("typst"):
            self.skipTest("typst is not installed")

        source = new_learning_source(
            subject_id="chemistry",
            title="Chemistry Notes",
            source_ref="/tmp/chemistry_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Chemistry Notes\n")
        context = LearningContext(
            subject_id="chemistry",
            canonical_title="Chemistry Notes",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_chem_source",
                    subject_id="chemistry",
                    unit_kind="definition",
                    canonical_title="Conservation",
                    statement="Use source_users-demo_123 as the stable source id and preserve T{before} = T{after}.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Chemistry Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        typ_path = output_root / "report.typ"
        self.assertTrue((output_root / "report.pdf").is_file())
        process = subprocess.run(
            ["typst", "compile", str(typ_path), str(output_root / "report.pdf")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_materialized_report_typst_renders_math_delimiters_as_typst_math(self) -> None:
        source = new_learning_source(
            subject_id="chemistry",
            title="Chemistry Notes",
            source_ref="/tmp/chemistry_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Chemistry Notes\n")
        context = LearningContext(
            subject_id="chemistry",
            canonical_title="Chemistry Notes",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_conservation_math",
                    subject_id="chemistry",
                    unit_kind="definition",
                    canonical_title="Conservation Formula",
                    statement=(
                        "The reusable formula is $$ T{before} = T{after} $$ "
                        "and the normalized fraction is $\\\\frac{m}{v}$."
                    ),
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Chemistry Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        self.assertNotIn("$$", rendered_typst)
        self.assertIn('$T_"before" = T_"after"$', rendered_typst)
        self.assertIn("$frac(m, v)$", rendered_typst)

    def test_materialized_report_typst_handles_multi_letter_group_factor_without_runaway_quoting(self) -> None:
        source = new_learning_source(
            subject_id="chemistry",
            title="Grouped Counting Notes",
            source_ref="/tmp/grouped_counting.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Grouped Counting\n")
        context = LearningContext(
            subject_id="chemistry",
            canonical_title="Grouped Counting",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_grouped_counting",
                    subject_id="chemistry",
                    unit_kind="definition",
                    canonical_title="Grouped Counting",
                    statement="The reusable formula is $$ C = G cg $$.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Grouped Counting Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        self.assertIn('$C = G "cg"$', rendered_typst)
        self.assertNotIn('""cg""', rendered_typst)

    def test_materialized_report_typst_key_findings_do_not_double_escape_source_handles(self) -> None:
        source = new_learning_source(
            subject_id="chemistry",
            title="Chemistry Notes",
            source_ref="/tmp/chemistry_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Chemistry Notes\n")
        context = LearningContext(
            subject_id="chemistry",
            canonical_title="Chemistry Notes",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_counting_relation",
                    subject_id="chemistry",
                    unit_kind="relation",
                    canonical_title="Counting Relation",
                    statement="Grouped counting is the broader reusable substrate.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Chemistry Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        self.assertIn(r"Sources: \[S1\]", rendered_typst)
        self.assertNotIn(r"(\\[S1\\])", rendered_typst)

    def test_materialized_report_typst_claim_citations_render_on_separate_source_line(self) -> None:
        source = new_learning_source(
            subject_id="chemistry",
            title="Mole Notes",
            source_ref="/tmp/mole_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Mole Notes\n")
        context = LearningContext(
            subject_id="chemistry",
            canonical_title="Mole Notes",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_mole_definition",
                    subject_id="chemistry",
                    unit_kind="definition",
                    canonical_title="Grouped Counting",
                    statement="The reusable formula is $$ C = G cg $$ input: G input: cg output: C",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Mole Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        self.assertIn(r'- The reusable formula is $C = G "cg"$ input: G input: cg output: C', rendered_typst)
        self.assertIn(r'Sources: \[S1\]', rendered_typst)
        self.assertNotIn(r'(\[S1\])', rendered_typst)

    def test_materialized_report_normalizes_inline_markdown_blockquote_examples_in_claims(self) -> None:
        source = new_learning_source(
            subject_id="language",
            title="Basic Language Notes",
            source_ref="/tmp/basic_language.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Basic Language Notes\n")
        context = LearningContext(
            subject_id="language",
            canonical_title="Basic Language Notes",
            subject_family="Language",
            units=(
                LearningUnit(
                    unit_id="unit_time_question",
                    subject_id="language",
                    unit_kind="definition",
                    canonical_title="Time Question",
                    statement='If you want to ask for the time, say, > Velawa Kiiyadha',
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_greeting",
                    subject_id="language",
                    unit_kind="definition",
                    canonical_title="Greeting",
                    statement=(
                        "If you want to greet someone, say, > Ayubowan "
                        "That's a Sri Lankan greeting saying 'May your lifespan increase'."
                    ),
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Basic Language Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")

        self.assertIn('If you want to ask for the time, say "Velawa Kiiyadha".', rendered_typst)
        self.assertIn('If you want to greet someone, say "Ayubowan".', rendered_typst)
        self.assertIn("That's a Sri Lankan greeting saying 'May your lifespan increase'.", rendered_typst)
        self.assertNotIn("> Velawa Kiiyadha", rendered_typst)
        self.assertNotIn("\\> Velawa Kiiyadha", rendered_typst)
        self.assertNotIn("> Ayubowan", rendered_typst)
        self.assertNotIn("\\> Ayubowan", rendered_typst)

    def test_materialized_report_normalizes_markdown_links_in_claims(self) -> None:
        source = new_learning_source(
            subject_id="reference",
            title="Reference Notes",
            source_ref="/tmp/reference_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Reference Notes\n")
        context = LearningContext(
            subject_id="reference",
            canonical_title="Reference Notes",
            subject_family="Reference",
            units=(
                LearningUnit(
                    unit_id="unit_reference_link",
                    subject_id="reference",
                    unit_kind="definition",
                    canonical_title="Reference Link",
                    statement="[Open Wikipedia](https://en.wikipedia.org)",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Reference Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        self.assertIn("Open Wikipedia (https://en.wikipedia.org)", rendered_typst)
        self.assertNotIn("[Open Wikipedia](https://en.wikipedia.org)", rendered_typst)
        self.assertNotIn("\\[Open Wikipedia\\](https://en.wikipedia.org)", rendered_typst)

    def test_materialized_report_typst_spaces_uppercase_compound_symbol_in_math(self) -> None:
        source = new_learning_source(
            subject_id="physics",
            title="Physics Notes",
            source_ref="/tmp/physics_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Physics Notes\n")
        context = LearningContext(
            subject_id="physics",
            canonical_title="Physics Notes",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_einstein",
                    subject_id="physics",
                    unit_kind="definition",
                    canonical_title="Einstein",
                    statement="$$ E = MC^2$$",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            title="Physics Report",
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")
        self.assertIn("$E = M C^2$", rendered_typst)
        self.assertNotIn('$E = "MC"^2$', rendered_typst)

    def test_materialized_exact_draft_publication_renders_only_the_drafted_equation_without_report_shell(self) -> None:
        source = new_learning_source(
            subject_id="physics",
            title="Physics Notes",
            source_ref="/tmp/physics_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Physics Notes\n\n$$ E = MC^2 $$\n")
        context = LearningContext(
            subject_id="physics",
            canonical_title="Physics Notes",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_einstein",
                    subject_id="physics",
                    unit_kind="definition",
                    canonical_title="Einstein",
                    statement="$$ E = MC^2$$",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        composition = publication_composition_from_learning_context(
            self.root,
            context,
            publication_type="exact_draft",
            title="Physics Report",
            included_unit_ids=("unit_einstein",),
            build_epoch_ms=0,
            status="approved",
        )

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            composition=composition,
            build_epoch_ms=0,
        )
        output_root = Path(str(report["publication_path"])).parent / "outputs" / str(report["build_id"])
        rendered_typst = (output_root / "report.typ").read_text(encoding="utf-8")

        self.assertIn("$E = M C^2$", rendered_typst)
        self.assertNotIn("Executive Summary", rendered_typst)
        self.assertNotIn("= Sources <sources>", rendered_typst)
        self.assertNotIn("= Build Notes <report-controls>", rendered_typst)
        self.assertNotIn("SECTION 01", rendered_typst)

    def test_publication_projection_materializes_blocks_and_transclusion(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id="kinematics",
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_example",
                    subject_id="kinematics",
                    unit_kind="example",
                    canonical_title="Ball Drop Example",
                    statement="A falling ball example provides supporting motion evidence.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )

        publication, sections, blocks, _claims, _sources, _entities, _xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
            scope_summary="Focused governed publication for motion fundamentals.",
        )

        block_by_title = {block.title: block for block in blocks}
        section_by_id = {section.section_id: section for section in sections}
        self.assertIn("Governed Publication Basis", block_by_title)
        self.assertIn("Report Scope", block_by_title)
        self.assertIn("Summary Lead", block_by_title)
        summary_lead = block_by_title["Summary Lead"]
        self.assertEqual(
            summary_lead.included_block_refs,
            (
                block_by_title["Governed Publication Basis"].block_id,
                block_by_title["Report Scope"].block_id,
            ),
        )
        self.assertIn(summary_lead.block_id, section_by_id["report-summary"].block_ids)
        self.assertIn(block_by_title["Evidence Lead"].block_id, section_by_id["report-evidence"].block_ids)
        self.assertEqual(tuple(block.block_id for block in blocks), publication.block_ids)

    def test_publication_projection_records_active_subject_imports_as_dependencies(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        imported_context = LearningContext(
            subject_id="dynamics",
            canonical_title="Dynamics",
            subject_family="Physics",
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        persist_learning_context(self.root, imported_context)
        subject_import = new_subject_import(
            active_subject_id=context.subject_id,
            active_subject_version_id=context.content_hash(),
            active_subject_title=context.canonical_title,
            source_subject_id=imported_context.subject_id,
            source_subject_version_id=imported_context.content_hash(),
            source_subject_title=imported_context.canonical_title,
            import_kind="publication_dependency",
            imported_unit_ids=("unit_force",),
            rationale="Use dynamics as an explicit neighboring dependency for this publication.",
        )
        persist_subject_import(self.root, subject_import)

        publication, _sections, _blocks, _claims, sources, _entities, xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
            scope_summary="Focused governed publication for motion fundamentals.",
        )

        import_source = next(item for item in sources if item.source_id == subject_import.import_id)
        import_xref = next(
            item
            for item in xrefs
            if item.from_kind == "publication" and item.to_kind == "source" and item.to_id == subject_import.import_id
        )

        self.assertIn(subject_import.import_id, publication.source_ids)
        self.assertEqual(import_source.trust_class, "subject_import")
        self.assertEqual(import_source.source_ref, "corpus/dynamics/context.json")
        self.assertIn("publication_dependency", import_source.excerpt)
        self.assertEqual(import_xref.xref_type, "depends_on")
        self.assertEqual(import_xref.metadata["dependency_kind"], "subject_import")
        self.assertEqual(import_xref.metadata["source_subject_id"], "dynamics")

    def test_materialized_report_build_uses_publication_composition_scope(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_drop_example",
                    subject_id="kinematics",
                    unit_kind="example",
                    canonical_title="Drop Example",
                    statement="A dropped object illustrates acceleration under gravity.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        imported_context = LearningContext(
            subject_id="dynamics",
            canonical_title="Dynamics",
            subject_family="Physics",
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        persist_learning_context(self.root, imported_context)
        subject_import = new_subject_import(
            active_subject_id=context.subject_id,
            active_subject_version_id=context.content_hash(),
            active_subject_title=context.canonical_title,
            source_subject_id=imported_context.subject_id,
            source_subject_version_id=imported_context.content_hash(),
            source_subject_title=imported_context.canonical_title,
            import_kind="publication_dependency",
            imported_unit_ids=("unit_force",),
            rationale="Use dynamics as an explicit neighboring dependency for this publication.",
            review_status="approved",
            status="active",
        )
        persist_subject_import(self.root, subject_import)

        composition = publication_composition_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Selective Kinematics Report",
            included_unit_ids=("unit_velocity",),
            selected_subject_import_ids=(),
            section_ids=("report-summary", "report-definitions"),
            build_epoch_ms=1,
            status="approved",
        )
        self.assertIsInstance(composition, PublicationComposition)

        report = materialize_report_publication_from_learning_context(
            self.root,
            context,
            composition=composition,
            build_epoch_ms=1,
        )

        self.assertEqual(report["composition_id"], composition.composition_id)
        self.assertEqual(report["composition_status"], "approved")
        self.assertEqual(int(report["claim_count"]), 1)
        self.assertEqual(int(report["import_count"]), 0)
        persisted_compositions = list_publication_compositions(self.root, context.subject_id, composition.publication_id)
        self.assertTrue(persisted_compositions)
        self.assertEqual(persisted_compositions[-1].composition_id, composition.composition_id)
        self.assertEqual(persisted_compositions[-1].status, "approved")

    def test_default_report_composition_curates_weak_and_duplicate_units(self) -> None:
        source = new_learning_source(
            subject_id="chemistry",
            title="Chemistry Notes",
            source_ref="/tmp/chemistry_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Chemistry Notes\n")
        context = LearningContext(
            subject_id="chemistry",
            canonical_title="Chemistry",
            subject_family="Chemistry",
            units=(
                LearningUnit(
                    unit_id="unit_conservation_definition",
                    subject_id="chemistry",
                    unit_kind="definition",
                    canonical_title="Conservation",
                    statement="When the total amount before a process equals the total amount after a process, the reusable family is conservation.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_conservation_duplicate",
                    subject_id="chemistry",
                    unit_kind="definition",
                    canonical_title="Conservation Duplicate",
                    statement="When the total amount before a process equals the total amount after a process, the reusable family is conservation.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_question_ability",
                    subject_id="chemistry",
                    unit_kind="ability",
                    canonical_title="Solve Conservation",
                    statement="How do you calculate m_reactants from m_products?",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_mass_analysis",
                    subject_id="chemistry",
                    unit_kind="relation",
                    canonical_title="Mass Conservation",
                    statement="Mass conservation and atom conservation reuse the broader conservation substrate but preserve different quantities.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        composition = publication_composition_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Chemistry Report",
            build_epoch_ms=1,
            status="draft",
        )

        self.assertEqual(composition.metadata.get("unit_selection_mode"), "curated_default")
        self.assertEqual(set(composition.included_unit_ids), {"unit_conservation_definition", "unit_mass_analysis"})
        self.assertIn("unit_conservation_duplicate", set(composition.excluded_unit_ids))
        self.assertIn("unit_question_ability", set(composition.excluded_unit_ids))
        self.assertEqual(int(composition.metadata.get("auto_excluded_unit_count", 0)), 2)

    def test_publication_projection_materializes_typed_section_xrefs(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id="kinematics",
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_solver",
                    subject_id="kinematics",
                    unit_kind="ability",
                    canonical_title="Solve Constant Acceleration",
                    statement="Use the constant-acceleration equations to solve missing motion values.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_example",
                    subject_id="kinematics",
                    unit_kind="example",
                    canonical_title="Ball Drop Example",
                    statement="A falling ball example provides supporting motion evidence.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )

        publication, sections, _blocks, _claims, _sources, _entities, xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
        )

        section_by_id = {section.section_id: section for section in sections}
        xref_specs = {(xref.from_id, xref.xref_type, xref.to_id) for xref in xrefs}
        self.assertIn(("report-analysis", "depends_on", "report-definitions"), xref_specs)
        self.assertIn(("report-implementation", "depends_on", "report-analysis"), xref_specs)
        self.assertIn(("report-evidence", "supports", "report-analysis"), xref_specs)
        self.assertTrue(any(xref.from_kind == "claim" and xref.to_kind == "unit" for xref in xrefs))
        self.assertTrue(any(xref.from_kind == "claim" and xref.to_kind == "source" for xref in xrefs))
        self.assertTrue(any(xref.from_kind == "claim" and xref.to_kind == "entity" for xref in xrefs))
        self.assertTrue(
            any(
                xref.from_kind == "claim"
                and xref.to_kind == "unit"
                and xref.to_id == "unit_velocity"
                for xref in xrefs
            )
        )
        analysis_xrefs = set(section_by_id["report-analysis"].xref_ids)
        implementation_xrefs = set(section_by_id["report-implementation"].xref_ids)
        evidence_xrefs = set(section_by_id["report-evidence"].xref_ids)
        self.assertTrue(any(xref.from_id == "report-analysis" and xref.xref_id in analysis_xrefs for xref in xrefs))
        self.assertTrue(any(xref.from_id == "report-implementation" and xref.xref_id in implementation_xrefs for xref in xrefs))
        self.assertTrue(any(xref.from_id == "report-evidence" and xref.xref_id in evidence_xrefs for xref in xrefs))
        self.assertTrue(all(xref.publication_id == publication.publication_id for xref in xrefs))

    def test_validate_publication_rejects_descriptive_claim_without_source(self) -> None:
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    status="admitted",
                ),
            ),
            governance_status="active",
        )

        publication, sections, blocks, claims, sources, entities, xrefs, reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
        )
        validation = validate_publication(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
            entities=entities,
            xrefs=xrefs,
            reviews=reviews,
        )

        self.assertEqual(validation["status"], "error")
        self.assertTrue(any("descriptive claim" in str(item) for item in validation["errors"]))

    def test_validate_publication_rejects_broken_xref(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id="kinematics",
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        publication, sections, blocks, claims, sources, entities, xrefs, reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
        )
        broken_xref = PublicationCrossReference(
            xref_id="xref_broken",
            publication_id=publication.publication_id,
            from_id="report-analysis",
            to_id="report-missing",
            xref_type="depends_on",
            from_kind="section",
            to_kind="section",
            status="active",
        )

        validation = validate_publication(
            publication,
            sections=sections,
            blocks=blocks,
            claims=claims,
            sources=sources,
            entities=entities,
            xrefs=xrefs + (broken_xref,),
            reviews=reviews,
        )

        self.assertEqual(validation["status"], "error")
        self.assertTrue(any("missing section report-missing" in str(item) for item in validation["errors"]))

    def test_validate_publication_rejects_section_tree_cycle_and_root_parent_mismatch(self) -> None:
        publication = Publication(
            publication_id="pub_demo",
            publication_type="report",
            subject_id="demo",
            title="Demo Report",
            status="draft",
            scope_summary="Demo scope.",
            learning_context_ref="corpus/demo/context.json",
            learning_context_snapshot_hash="snap",
            root_section_ids=("sec-root",),
        )
        sections = (
            PublicationSection(
                section_id="sec-root",
                publication_id="pub_demo",
                parent_section_id="",
                role="summary",
                title="Summary",
                ordinal="1",
                child_section_ids=("sec-child",),
            ),
            PublicationSection(
                section_id="sec-child",
                publication_id="pub_demo",
                parent_section_id="sec-cycle",
                role="analysis",
                title="Analysis",
                ordinal="1.1",
                child_section_ids=("sec-cycle",),
            ),
            PublicationSection(
                section_id="sec-cycle",
                publication_id="pub_demo",
                parent_section_id="sec-child",
                role="analysis",
                title="Cycle",
                ordinal="1.1.1",
                child_section_ids=("sec-child",),
            ),
        )

        validation = validate_publication(
            publication,
            sections=sections,
            blocks=(),
            claims=(),
            sources=(),
            entities=(),
            xrefs=(),
            reviews=(),
        )

        self.assertEqual(validation["status"], "error")
        self.assertTrue(any("lists child sec-child but that child declares parent sec-cycle" in str(item) for item in validation["errors"]))
        self.assertTrue(any("section tree cycle detected" in str(item) for item in validation["errors"]))

    def test_validate_publication_rejects_child_section_role_mismatch(self) -> None:
        publication = Publication(
            publication_id="pub_demo",
            publication_type="report",
            subject_id="demo",
            title="Demo Report",
            status="draft",
            scope_summary="Demo scope.",
            learning_context_ref="corpus/demo/context.json",
            learning_context_snapshot_hash="snap",
            root_section_ids=("sec-analysis",),
        )
        sections = (
            PublicationSection(
                section_id="sec-analysis",
                publication_id="pub_demo",
                parent_section_id="",
                role="analysis",
                title="Analysis",
                ordinal="1",
                child_section_ids=("sec-evidence",),
            ),
            PublicationSection(
                section_id="sec-evidence",
                publication_id="pub_demo",
                parent_section_id="sec-analysis",
                role="evidence",
                title="Evidence",
                ordinal="1.1",
            ),
        )

        validation = validate_publication(
            publication,
            sections=sections,
            blocks=(),
            claims=(),
            sources=(),
            entities=(),
            xrefs=(),
            reviews=(),
        )

        self.assertEqual(validation["status"], "error")
        self.assertTrue(any("uses role evidence under parent sec-analysis with role analysis" in str(item) for item in validation["errors"]))

    def test_validate_publication_rejects_unknown_transcluded_block(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        publication, sections, blocks, claims, sources, entities, xrefs, reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
        )
        broken_block = PublicationBlock(
            block_id="blk_broken",
            publication_id=publication.publication_id,
            block_kind="section_lead",
            title="Broken Lead",
            body="Broken transclusion block.",
            included_block_refs=("blk_missing",),
            status="active",
        )

        validation = validate_publication(
            publication,
            sections=sections,
            blocks=blocks + (broken_block,),
            claims=claims,
            sources=sources,
            entities=entities,
            xrefs=xrefs,
            reviews=reviews,
        )

        self.assertEqual(validation["status"], "error")
        self.assertTrue(any("includes missing block blk_missing" in str(item) for item in validation["errors"]))

    def test_publication_projection_materializes_entities_reviews_and_query_helpers(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )

        publication, _sections, _blocks, claims, _sources, entities, _xrefs, reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
        )

        self.assertTrue(any(entity.canonical_name == "Velocity" for entity in entities))
        velocity_entity = next(entity for entity in entities if entity.canonical_name == "Velocity")
        self.assertEqual(publication_claim_ids_for_entity(claims, velocity_entity.entity_id), ("clm-001",))
        self.assertEqual(publication_claim_ids_for_source(claims, source.source_id), ("clm-001",))
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].target_id, publication.publication_id)
        self.assertEqual(reviews[0].review_state, "approved")

    def test_validate_publication_rejects_missing_entity_and_broken_review_target(self) -> None:
        source = new_learning_source(
            subject_id="kinematics",
            title="Motion Notes",
            source_ref="/tmp/motion_notes.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text="# Motion Notes\n")
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        publication, sections, blocks, claims, sources, entities, xrefs, _reviews = publication_from_learning_context(
            self.root,
            context,
            publication_type="report",
            title="Kinematics Report",
        )
        broken_claim = replace(claims[0], entity_ids=("ent_missing",))
        broken_review = PublicationReviewRecord(
            review_id="review_broken",
            publication_id=publication.publication_id,
            target_kind="section",
            target_id="report-missing",
            review_state="changes_requested",
            reviewer="tester",
            reason="broken test",
            created_at_epoch_ms=0,
        )

        validation = validate_publication(
            publication,
            sections=sections,
            blocks=blocks,
            claims=(broken_claim,),
            sources=sources,
            entities=entities,
            xrefs=xrefs,
            reviews=(broken_review,),
        )

        self.assertEqual(validation["status"], "error")
        self.assertTrue(any("references missing entity ent_missing" in str(item) for item in validation["errors"]))
        self.assertTrue(any("references missing section report-missing" in str(item) for item in validation["errors"]))

    def test_publication_query_helpers_cover_impacted_claims_xrefs_reviews_and_children(self) -> None:
        sections = (
            PublicationSection(
                section_id="sec-root",
                publication_id="pub_demo",
                parent_section_id="",
                role="summary",
                title="Summary",
                ordinal="1",
                child_section_ids=("sec-evidence",),
            ),
            PublicationSection(
                section_id="sec-evidence",
                publication_id="pub_demo",
                parent_section_id="sec-root",
                role="evidence",
                title="Evidence",
                ordinal="1.1",
                claim_ids=("clm-001",),
                xref_ids=("xref-001",),
            ),
        )
        claims = (
            PublicationClaim(
                claim_id="clm-001",
                publication_id="pub_demo",
                statement="Velocity is the rate of change of position.",
                claim_kind="descriptive",
                scope="physics",
                status="approved",
                certainty="high",
                source_ids=("src-001",),
                entity_ids=("ent-001",),
                related_unit_ids=("unit-001",),
                xref_ids=("xref-001",),
                last_reviewed_epoch_ms=1,
            ),
        )
        xrefs = (
            PublicationCrossReference(
                xref_id="xref-001",
                publication_id="pub_demo",
                from_id="sec-evidence",
                to_id="clm-001",
                xref_type="supports",
                from_kind="section",
                to_kind="claim",
            ),
        )
        reviews = (
            PublicationReviewRecord(
                review_id="review-001",
                publication_id="pub_demo",
                target_kind="section",
                target_id="sec-evidence",
                review_state="approved",
                reviewer="qa",
                reason="ready",
                created_at_epoch_ms=1,
            ),
        )

        self.assertEqual(tuple(section.section_id for section in publication_child_sections(sections, "sec-root")), ("sec-evidence",))
        self.assertEqual(publication_claim_ids_impacted_by_source_ids(claims, ("src-001",)), ("clm-001",))
        self.assertEqual(publication_claim_ids_impacted_by_entity_ids(claims, ("ent-001",)), ("clm-001",))
        self.assertEqual(publication_claim_ids_impacted_by_unit_ids(claims, ("unit-001",)), ("clm-001",))
        self.assertEqual(tuple(xref.xref_id for xref in publication_xrefs_for_node(xrefs, node_kind="section", node_id="sec-evidence")), ("xref-001",))
        self.assertEqual(tuple(review.review_id for review in publication_reviews_for_target(reviews, target_kind="section", target_id="sec-evidence")), ("review-001",))

    def test_publication_diff_summary_reports_added_removed_and_changed_records(self) -> None:
        previous_sections = (
            PublicationSection(
                section_id="sec-root",
                publication_id="pub_demo",
                parent_section_id="",
                role="summary",
                title="Summary",
                ordinal="1",
            ),
            PublicationSection(
                section_id="sec-analysis",
                publication_id="pub_demo",
                parent_section_id="sec-root",
                role="analysis",
                title="Analysis",
                ordinal="2",
            ),
        )
        current_sections = (
            previous_sections[0],
            replace(previous_sections[1], title="Updated Analysis"),
            PublicationSection(
                section_id="sec-appendix",
                publication_id="pub_demo",
                parent_section_id="",
                role="appendix",
                title="Appendix",
                ordinal="3",
            ),
        )
        previous_claims = (
            PublicationClaim(
                claim_id="clm-001",
                publication_id="pub_demo",
                statement="Velocity is the rate of change of position.",
                claim_kind="descriptive",
                scope="physics",
                status="approved",
                certainty="high",
                source_ids=("src-001",),
                entity_ids=("ent-001",),
                last_reviewed_epoch_ms=1,
            ),
        )
        current_claims = (
            replace(previous_claims[0], statement="Velocity is directional rate of change of position."),
            PublicationClaim(
                claim_id="clm-002",
                publication_id="pub_demo",
                statement="Acceleration is the rate of change of velocity.",
                claim_kind="descriptive",
                scope="physics",
                status="approved",
                certainty="high",
                source_ids=("src-002",),
                entity_ids=("ent-002",),
                last_reviewed_epoch_ms=2,
            ),
        )
        previous_sources = (
            PublicationSource(
                source_id="src-001",
                publication_id="pub_demo",
                title="Motion Notes",
                publisher="",
                source_ref="/tmp/motion.md",
                published_at="",
                retrieved_at_epoch_ms=1,
                trust_class="corpus_source",
                freshness_class="captured",
                jurisdiction="",
                excerpt="Motion Notes",
            ),
        )
        current_sources = previous_sources + (
            PublicationSource(
                source_id="src-002",
                publication_id="pub_demo",
                title="Acceleration Notes",
                publisher="",
                source_ref="/tmp/acceleration.md",
                published_at="",
                retrieved_at_epoch_ms=2,
                trust_class="corpus_source",
                freshness_class="captured",
                jurisdiction="",
                excerpt="Acceleration Notes",
            ),
        )
        previous_xrefs = (
            PublicationCrossReference(
                xref_id="xref-001",
                publication_id="pub_demo",
                from_id="sec-analysis",
                to_id="clm-001",
                xref_type="supports",
                from_kind="section",
                to_kind="claim",
            ),
        )
        previous_reviews = (
            PublicationReviewRecord(
                review_id="review-001",
                publication_id="pub_demo",
                target_kind="section",
                target_id="sec-analysis",
                review_state="approved",
                reviewer="qa",
                reason="ready",
                created_at_epoch_ms=1,
            ),
        )
        current_reviews = (
            replace(previous_reviews[0], review_state="changes_requested"),
        )

        diff = publication_diff_summary(
            previous_sections=previous_sections,
            current_sections=current_sections,
            previous_claims=previous_claims,
            current_claims=current_claims,
            previous_sources=previous_sources,
            current_sources=current_sources,
            previous_xrefs=previous_xrefs,
            current_xrefs=(),
            previous_reviews=previous_reviews,
            current_reviews=current_reviews,
        )

        self.assertEqual(diff["sections"]["changed"], ("sec-analysis",))
        self.assertEqual(diff["sections"]["added"], ("sec-appendix",))
        self.assertEqual(diff["claims"]["changed"], ("clm-001",))
        self.assertEqual(diff["claims"]["added"], ("clm-002",))
        self.assertEqual(diff["sources"]["added"], ("src-002",))
        self.assertEqual(diff["xrefs"]["removed"], ("xref-001",))
        self.assertEqual(diff["reviews"]["changed"], ("review-001",))
