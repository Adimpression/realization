# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from realized_exchange.learning_context import apply_learning_delta
from tests.learning_xref_test_support import (
    generated_large_markdown,
    materialize_learning_fixture,
)


class LearningXrefPreparationTests(unittest.TestCase):
    def test_fixture_extracts_deterministic_explicit_xref_candidates(self) -> None:
        markdown = generated_large_markdown(
            document_title="Large Dynamics Notes",
            subject_title="Dynamics",
            subject_family="Physics",
            section_prefix="Dynamics",
            start_index=1,
            section_count=6,
            include_explicit_xrefs=True,
        )

        with tempfile.TemporaryDirectory(prefix="learning_xref_fixture_") as tmpdir:
            fixture = materialize_learning_fixture(
                Path(tmpdir),
                filename="dynamics_fixture.md",
                markdown_text=markdown,
                canonical_title="Dynamics",
                subject_family="Physics",
                summary="Generated large markdown lesson for Dynamics.",
            )

            self.assertEqual(len(fixture.sections), 6)
            self.assertEqual(len(fixture.xref_candidates), 5)
            self.assertEqual(
                tuple(candidate.xref_type for candidate in fixture.xref_candidates),
                ("depends_on", "depends_on", "depends_on", "depends_on", "depends_on"),
            )
            self.assertEqual(
                tuple(candidate.target_label for candidate in fixture.xref_candidates),
                (
                    "Dynamics Principle 01",
                    "Dynamics Principle 02",
                    "Dynamics Principle 03",
                    "Dynamics Principle 04",
                    "Dynamics Principle 05",
                ),
            )
            self.assertEqual(
                tuple(candidate.source_section_id for candidate in fixture.xref_candidates),
                tuple(section.section_id for section in fixture.sections[1:]),
            )

    def test_fixture_materialization_builds_learning_records_without_controller(self) -> None:
        markdown = generated_large_markdown(
            document_title="Large Chemistry Notes",
            subject_title="Chemistry",
            subject_family="Science",
            section_prefix="Reaction",
            start_index=1,
            section_count=8,
            include_explicit_xrefs=True,
        )

        with tempfile.TemporaryDirectory(prefix="learning_xref_materialize_") as tmpdir:
            fixture = materialize_learning_fixture(
                Path(tmpdir),
                filename="chemistry_fixture.md",
                markdown_text=markdown,
                canonical_title="Chemistry",
                subject_family="Science",
                summary="Generated large markdown lesson for Chemistry.",
            )

            self.assertEqual(fixture.source.section_count, 8)
            self.assertEqual(len(fixture.context.units), 8)
            self.assertEqual(len(fixture.delta.proposed_units), 8)
            self.assertEqual(len(fixture.delta.operations), 8)
            self.assertEqual(fixture.context.applied_delta_ids, (fixture.delta.delta_id,))
            self.assertEqual(fixture.context.linked_source_ids, (fixture.source.source_id,))
            self.assertTrue(all(unit.unit_kind == "source_note" for unit in fixture.context.units))
            self.assertTrue(all(len(unit.linked_section_ids) == 1 for unit in fixture.context.units))

    def test_fixture_section_handles_are_deterministic_across_materializations(self) -> None:
        markdown = generated_large_markdown(
            document_title="Large Biology Notes",
            subject_title="Biology",
            subject_family="Science",
            section_prefix="Cell",
            start_index=1,
            section_count=5,
            include_explicit_xrefs=True,
        )

        with tempfile.TemporaryDirectory(prefix="learning_xref_deterministic_a_") as first_tmpdir:
            first = materialize_learning_fixture(
                Path(first_tmpdir),
                filename="biology_fixture.md",
                markdown_text=markdown,
                canonical_title="Biology",
                subject_family="Science",
                summary="Generated large markdown lesson for Biology.",
            )
        with tempfile.TemporaryDirectory(prefix="learning_xref_deterministic_b_") as second_tmpdir:
            second = materialize_learning_fixture(
                Path(second_tmpdir),
                filename="biology_fixture.md",
                markdown_text=markdown,
                canonical_title="Biology",
                subject_family="Science",
                summary="Generated large markdown lesson for Biology.",
            )

        self.assertEqual(
            tuple(section.section_id for section in first.sections),
            tuple(section.section_id for section in second.sections),
        )
        self.assertEqual(
            tuple(candidate.raw_bullet for candidate in first.xref_candidates),
            tuple(candidate.raw_bullet for candidate in second.xref_candidates),
        )
        self.assertEqual(
            tuple(candidate.source_section_id for candidate in first.xref_candidates),
            tuple(candidate.source_section_id for candidate in second.xref_candidates),
        )

    def test_fixture_delta_reentry_merges_contexts_without_controller_runtime(self) -> None:
        first_markdown = generated_large_markdown(
            document_title="Mechanics Fixture One",
            subject_title="Mechanics",
            subject_family="Physics",
            section_prefix="Kinematics",
            start_index=1,
            section_count=4,
            include_explicit_xrefs=True,
        )
        second_markdown = generated_large_markdown(
            document_title="Mechanics Fixture Two",
            subject_title="Mechanics",
            subject_family="Physics",
            section_prefix="Energy",
            start_index=5,
            section_count=4,
            include_explicit_xrefs=True,
        )

        with tempfile.TemporaryDirectory(prefix="learning_xref_reentry_") as tmpdir:
            root = Path(tmpdir)
            first = materialize_learning_fixture(
                root,
                filename="mechanics_fixture_one.md",
                markdown_text=first_markdown,
                canonical_title="Mechanics",
                subject_family="Physics",
                summary="Generated large markdown lesson for Mechanics.",
            )
            second = materialize_learning_fixture(
                root,
                filename="mechanics_fixture_two.md",
                markdown_text=second_markdown,
                canonical_title="Mechanics",
                subject_family="Physics",
                summary="Generated large markdown lesson for Mechanics.",
            )

            merged = apply_learning_delta(first.context, second.delta)

            self.assertEqual(first.subject_id, second.subject_id)
            self.assertEqual(len(merged.units), 8)
            self.assertEqual(len(merged.applied_delta_ids), 2)
            self.assertEqual(len(merged.linked_source_ids), 2)
            self.assertIn(first.source.source_id, merged.linked_source_ids)
            self.assertIn(second.source.source_id, merged.linked_source_ids)


if __name__ == "__main__":
    unittest.main()
