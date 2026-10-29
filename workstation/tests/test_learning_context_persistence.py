from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from workstation.subject.core.learning_context import (
    LearningContext,
    LearningUnit,
    canonical_learning_subject_id,
    learning_context_paths,
)
from workstation.subject.service.learning_context_persistence import (
    persist_learning_context,
)


class LearningContextPersistenceTests(unittest.TestCase):
    def _context(self, *, linked_skill_ids: tuple[str, ...] = ()) -> LearningContext:
        subject_id = canonical_learning_subject_id("Projection Boundary")
        units = ()
        if linked_skill_ids:
            units = (
                LearningUnit(
                    unit_id="unit_projection_boundary",
                    subject_id=subject_id,
                    canonical_title="Projection Boundary",
                    statement="Projection follows authoritative persistence.",
                    status="admitted",
                    linked_skill_ids=linked_skill_ids,
                ),
            )
        return LearningContext(
            subject_id=subject_id,
            canonical_title="Projection Boundary",
            units=units,
            governance_status="active",
        )

    def test_context_without_skills_persists_without_exchange_adapter(self) -> None:
        context = self._context()
        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            context_path = persist_learning_context(root, context)
            paths = learning_context_paths(root, context.subject_id)

            self.assertEqual(paths["context"], context_path)
            self.assertTrue(paths["subject_md"].is_file())
            self.assertTrue(paths["subject_typ"].is_file())

    def test_linked_skill_requires_adapter_before_any_state_is_written(self) -> None:
        context = self._context(linked_skill_ids=("skill_projection",))
        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            with self.assertRaisesRegex(RuntimeError, "skill materializer"):
                persist_learning_context(root, context)

            self.assertFalse(
                learning_context_paths(root, context.subject_id)["context"].exists()
            )

    def test_entry_composed_adapter_receives_normalized_context(self) -> None:
        context = self._context(linked_skill_ids=("skill_projection",))
        calls: list[tuple[Path, LearningContext]] = []

        def materialize(
            root_path: Path,
            normalized: LearningContext,
        ) -> tuple[dict[str, object], ...]:
            calls.append((root_path, normalized))
            return ()

        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            persist_learning_context(
                root,
                context,
                skill_materializer=materialize,
            )

            self.assertEqual(1, len(calls))
            self.assertEqual(root, calls[0][0])
            self.assertEqual(context.to_dict(), calls[0][1].to_dict())


if __name__ == "__main__":
    unittest.main()
