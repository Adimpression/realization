# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from learning_context import (
    LearningDelta,
    LearningDeltaOperation,
    LearningUnit,
    apply_learning_delta,
    load_learning_context,
    load_learning_delta,
    load_learning_source,
    stable_learning_unit_id,
)
from main import BSSCController, SystemState
from tests.learning_xref_test_support import generated_large_markdown


class LargeMarkdownLearningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = BSSCController(SystemState.bootstrap("large markdown learning"), llm_policy="off")

    def _learn_markdown(
        self,
        root: Path,
        filename: str,
        markdown_text: str,
        *,
        max_artifacts: int = 64,
    ) -> dict[str, object]:
        path = root / filename
        path.write_text(markdown_text, encoding="utf-8")
        return self.controller.learn_from_markdown_document(path, max_artifacts=max_artifacts)

    def test_large_markdown_learning_persists_expected_context_records(self) -> None:
        markdown = generated_large_markdown(
            document_title="Large Mechanics Notes",
            subject_title="Mechanics",
            subject_family="Physics",
            section_prefix="Dynamics",
            start_index=1,
            section_count=18,
        )

        with tempfile.TemporaryDirectory(prefix="large_markdown_learning_") as tmpdir:
            root = Path(tmpdir)
            result = self._learn_markdown(root, "large_mechanics.md", markdown)
            report = dict(result.get("learning_context", {}))
            subject_id = str(report.get("subject_id", ""))
            source_id = str(report.get("source_id", ""))
            delta_id = str(report.get("delta_id", ""))

            context = load_learning_context(root, subject_id)
            source = load_learning_source(root, subject_id, source_id)
            delta = load_learning_delta(root, subject_id, delta_id)

            self.assertEqual(subject_id, "mechanics")
            self.assertEqual(result["document"]["section_count"], 18)
            self.assertEqual(source.section_count, 18)
            self.assertEqual(context.canonical_title, "Mechanics")
            self.assertEqual(context.subject_family, "Physics")
            self.assertEqual(context.summary, "Generated large markdown lesson for Mechanics.")
            self.assertEqual(context.governance_status, "active")
            self.assertGreaterEqual(len(context.units), 18)
            self.assertGreaterEqual(len(delta.proposed_units), 18)
            self.assertEqual(len(delta.operations), len(delta.proposed_units))
            self.assertTrue(all(item.operation_kind == "initiate" for item in delta.operations))
            self.assertTrue(all(item.evidence_refs == (source_id,) for item in delta.operations))
            self.assertEqual(
                {item.proposed_unit_ids for item in delta.operations},
                {(unit.unit_id,) for unit in delta.proposed_units},
            )
            self.assertGreaterEqual(len({unit.canonical_title for unit in context.units}), 18)
            self.assertEqual(len(context.applied_delta_ids), 1)
            self.assertEqual(context.linked_source_ids, (source_id,))

    def test_large_markdown_learning_reuses_subject_across_multiple_documents(self) -> None:
        first = generated_large_markdown(
            document_title="Mechanics Volume One",
            subject_title="Mechanics",
            subject_family="Physics",
            section_prefix="Kinematics",
            start_index=1,
            section_count=12,
        )
        second = generated_large_markdown(
            document_title="Mechanics Volume Two",
            subject_title="Mechanics",
            subject_family="Physics",
            section_prefix="Energy",
            start_index=13,
            section_count=12,
        )

        with tempfile.TemporaryDirectory(prefix="large_markdown_learning_reentry_") as tmpdir:
            root = Path(tmpdir)
            first_result = self._learn_markdown(root, "mechanics_one.md", first)
            second_result = self._learn_markdown(root, "mechanics_two.md", second)

            first_report = dict(first_result.get("learning_context", {}))
            second_report = dict(second_result.get("learning_context", {}))
            subject_id = str(second_report.get("subject_id", ""))
            second_source_id = str(second_report.get("source_id", ""))
            second_delta_id = str(second_report.get("delta_id", ""))

            context = load_learning_context(root, subject_id)
            second_source = load_learning_source(root, subject_id, second_source_id)
            second_delta = load_learning_delta(root, subject_id, second_delta_id)

            self.assertEqual(first_report.get("subject_id"), "mechanics")
            self.assertEqual(second_report.get("subject_id"), "mechanics")
            self.assertEqual(second_report.get("matched_existing_subject_id"), "mechanics")
            self.assertEqual(second_source.section_count, 12)
            self.assertGreaterEqual(len(second_delta.operations), 12)
            self.assertEqual(len(second_delta.operations), len(second_delta.proposed_units))
            self.assertGreaterEqual(len(context.units), 24)
            self.assertEqual(len(context.applied_delta_ids), 2)
            self.assertEqual(len(context.linked_source_ids), 2)
            self.assertEqual(context.canonical_title, "Mechanics")
            self.assertEqual(context.subject_family, "Physics")

    def test_large_markdown_learning_context_supports_update_lifecycle_operations(self) -> None:
        markdown = generated_large_markdown(
            document_title="Large Chemistry Notes",
            subject_title="Chemistry",
            subject_family="Science",
            section_prefix="Reaction",
            start_index=1,
            section_count=14,
        )

        with tempfile.TemporaryDirectory(prefix="large_markdown_learning_lifecycle_") as tmpdir:
            root = Path(tmpdir)
            result = self._learn_markdown(root, "chemistry_large.md", markdown)
            report = dict(result.get("learning_context", {}))
            subject_id = str(report.get("subject_id", ""))
            context = load_learning_context(root, subject_id)
            units = sorted(context.units, key=lambda item: item.unit_id)
            self.assertGreaterEqual(len(units), 6)

            append_target, improve_target, link_target, replace_target, remove_target = units[:5]
            replacement_unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id=subject_id,
                    unit_kind=replace_target.unit_kind,
                    canonical_title=f"{replace_target.canonical_title} Corrected",
                ),
                subject_id=subject_id,
                unit_kind=replace_target.unit_kind,
                canonical_title=f"{replace_target.canonical_title} Corrected",
                statement=f"Corrected statement for {replace_target.canonical_title}.",
                status="admitted",
            )
            update_delta = LearningDelta(
                delta_id="delta_large_markdown_lifecycle_update",
                subject_id=subject_id,
                source_kind="manual",
                proposed_units=(replacement_unit,),
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_large_append",
                        operation_kind="append",
                        target_unit_ids=(append_target.unit_id,),
                        evidence_refs=("review_append_001",),
                        patch={
                            "statement_append": "This append note preserves the same unit identity.",
                            "aliases_add": ("Appended Alias",),
                        },
                    ),
                    LearningDeltaOperation(
                        operation_id="op_large_improve",
                        operation_kind="improve",
                        target_unit_ids=(improve_target.unit_id,),
                        evidence_refs=("review_improve_001",),
                        patch={
                            "statement": f"Improved statement for {improve_target.canonical_title}.",
                            "structured_fields_merge": {"reviewed": True},
                        },
                    ),
                    LearningDeltaOperation(
                        operation_id="op_large_link",
                        operation_kind="link",
                        target_unit_ids=(link_target.unit_id,),
                        evidence_refs=("review_link_001",),
                        patch={
                            "linked_artifact_ids_add": ("artifact_review_example",),
                            "linked_section_ids_add": ("analysis",),
                        },
                    ),
                    LearningDeltaOperation(
                        operation_id="op_large_replace",
                        operation_kind="replace",
                        target_unit_ids=(replace_target.unit_id,),
                        proposed_unit_ids=(replacement_unit.unit_id,),
                        evidence_refs=("review_replace_001",),
                    ),
                    LearningDeltaOperation(
                        operation_id="op_large_remove",
                        operation_kind="remove",
                        target_unit_ids=(remove_target.unit_id,),
                        evidence_refs=("review_remove_001",),
                    ),
                ),
                status="applied",
            )
            updated_context = apply_learning_delta(context, update_delta)
            restored_context = apply_learning_delta(
                updated_context,
                LearningDelta(
                    delta_id="delta_large_markdown_lifecycle_restore",
                    subject_id=subject_id,
                    source_kind="manual",
                    operations=(
                        LearningDeltaOperation(
                            operation_id="op_large_restore",
                            operation_kind="restore",
                            target_unit_ids=(remove_target.unit_id,),
                            evidence_refs=("review_restore_001",),
                        ),
                    ),
                    status="applied",
                ),
            )

            updated_by_id = {item.unit_id: item for item in updated_context.units}
            restored_by_id = {item.unit_id: item for item in restored_context.units}

            self.assertEqual(len(updated_context.units), len(context.units) + 1)
            self.assertIn("This append note preserves the same unit identity.", updated_by_id[append_target.unit_id].statement)
            self.assertIn("Appended Alias", updated_by_id[append_target.unit_id].aliases)
            self.assertEqual(
                updated_by_id[improve_target.unit_id].structured_fields.get("reviewed"),
                True,
            )
            self.assertIn(
                "artifact_review_example",
                updated_by_id[link_target.unit_id].linked_artifact_ids,
            )
            self.assertIn(
                "analysis",
                updated_by_id[link_target.unit_id].linked_section_ids,
            )
            self.assertEqual(updated_by_id[replace_target.unit_id].status, "superseded")
            self.assertEqual(updated_by_id[replacement_unit.unit_id].status, "admitted")
            self.assertEqual(updated_by_id[remove_target.unit_id].status, "deprecated")
            self.assertEqual(restored_by_id[remove_target.unit_id].status, "admitted")
            self.assertEqual(len(restored_context.applied_delta_ids), len(context.applied_delta_ids) + 2)

    def test_large_markdown_learning_context_supports_structural_and_rejection_operations(self) -> None:
        markdown = generated_large_markdown(
            document_title="Large Biology Notes",
            subject_title="Biology",
            subject_family="Science",
            section_prefix="Cell",
            start_index=1,
            section_count=10,
        )

        with tempfile.TemporaryDirectory(prefix="large_markdown_learning_structural_") as tmpdir:
            root = Path(tmpdir)
            result = self._learn_markdown(root, "biology_large.md", markdown)
            report = dict(result.get("learning_context", {}))
            subject_id = str(report.get("subject_id", ""))
            context = load_learning_context(root, subject_id)
            units = sorted(context.units, key=lambda item: item.unit_id)
            self.assertGreaterEqual(len(units), 5)

            split_target = units[0]
            merge_targets = units[1:3]
            split_units = (
                LearningUnit(
                    unit_id=stable_learning_unit_id(
                        subject_id=subject_id,
                        unit_kind=split_target.unit_kind,
                        canonical_title=f"{split_target.canonical_title} Part A",
                    ),
                    subject_id=subject_id,
                    unit_kind=split_target.unit_kind,
                    canonical_title=f"{split_target.canonical_title} Part A",
                    statement=f"First split for {split_target.canonical_title}.",
                    status="admitted",
                ),
                LearningUnit(
                    unit_id=stable_learning_unit_id(
                        subject_id=subject_id,
                        unit_kind=split_target.unit_kind,
                        canonical_title=f"{split_target.canonical_title} Part B",
                    ),
                    subject_id=subject_id,
                    unit_kind=split_target.unit_kind,
                    canonical_title=f"{split_target.canonical_title} Part B",
                    statement=f"Second split for {split_target.canonical_title}.",
                    status="admitted",
                ),
            )
            merged_unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id=subject_id,
                    unit_kind=merge_targets[0].unit_kind,
                    canonical_title="Merged Biology Principle",
                ),
                subject_id=subject_id,
                unit_kind=merge_targets[0].unit_kind,
                canonical_title="Merged Biology Principle",
                statement="Merged principle from two previously separate biology units.",
                status="admitted",
            )
            rejected_unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id=subject_id,
                    unit_kind="misconception",
                    canonical_title="Rejected Biology Misconception",
                ),
                subject_id=subject_id,
                unit_kind="misconception",
                canonical_title="Rejected Biology Misconception",
                statement="Cells function identically in every organismal context.",
                status="proposed",
            )
            structural_delta = LearningDelta(
                delta_id="delta_large_markdown_structural",
                subject_id=subject_id,
                source_kind="manual",
                proposed_units=split_units + (merged_unit, rejected_unit),
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_large_split",
                        operation_kind="split",
                        target_unit_ids=(split_target.unit_id,),
                        proposed_unit_ids=tuple(unit.unit_id for unit in split_units),
                        evidence_refs=("review_split_001",),
                    ),
                    LearningDeltaOperation(
                        operation_id="op_large_merge",
                        operation_kind="merge",
                        target_unit_ids=tuple(unit.unit_id for unit in merge_targets),
                        proposed_unit_ids=(merged_unit.unit_id,),
                        evidence_refs=("review_merge_001",),
                    ),
                    LearningDeltaOperation(
                        operation_id="op_large_reject",
                        operation_kind="reject",
                        proposed_unit_ids=(rejected_unit.unit_id,),
                        evidence_refs=("review_reject_001",),
                    ),
                ),
                status="applied",
            )
            updated_context = apply_learning_delta(context, structural_delta)
            updated_by_id = {item.unit_id: item for item in updated_context.units}

            self.assertEqual(updated_by_id[split_target.unit_id].status, "superseded")
            self.assertEqual(updated_by_id[split_units[0].unit_id].status, "admitted")
            self.assertEqual(updated_by_id[split_units[1].unit_id].status, "admitted")
            self.assertEqual(updated_by_id[merge_targets[0].unit_id].status, "superseded")
            self.assertEqual(updated_by_id[merge_targets[1].unit_id].status, "superseded")
            self.assertEqual(updated_by_id[merged_unit.unit_id].status, "admitted")
            self.assertEqual(updated_by_id[rejected_unit.unit_id].status, "rejected")
            self.assertEqual(updated_by_id[rejected_unit.unit_id].provenance_refs, ("review_reject_001",))


if __name__ == "__main__":
    unittest.main()
