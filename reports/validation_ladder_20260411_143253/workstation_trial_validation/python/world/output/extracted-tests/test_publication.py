# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import replace
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from learning_context import LearningContext, LearningUnit, new_learning_source, persist_learning_context, persist_learning_source
from publication import (
    PublicationBlock,
    PublicationClaim,
    PublicationCrossReference,
    PublicationEntity,
    PublicationReviewRecord,
    PublicationSection,
    PublicationSource,
    publication_child_sections,
    publication_claim_ids_for_entity,
    publication_claim_ids_impacted_by_entity_ids,
    publication_claim_ids_impacted_by_source_ids,
    publication_claim_ids_for_source,
    publication_diff_summary,
    publication_reviews_for_target,
    publication_xrefs_for_node,
)
from publication_projection import materialize_report_publication_from_learning_context, publication_from_learning_context
from publication_validation import validate_publication


class PublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

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
        self.assertIn("Governed Publication Basis", rendered_markdown)
        self.assertIn("Report Scope", rendered_markdown)
        self.assertIn("Sources: ", rendered_markdown)
        self.assertIn(source.source_id, rendered_markdown)
        build_payload = json.loads(build_path.read_text(encoding="utf-8"))
        self.assertEqual(build_payload["validation_report"]["status"], "ok")
        self.assertEqual(build_payload["build_status"], "ok")
        typst_compile = build_payload["validation_report"].get("render_validation", {}).get("typst_compile", {})
        if shutil.which("typst"):
            self.assertEqual(typst_compile.get("status"), "ok")
        else:
            self.assertEqual(typst_compile.get("status"), "unavailable")

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
