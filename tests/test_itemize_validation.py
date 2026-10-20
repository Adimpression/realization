# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from itemize import ItemizationSession, ItemizedSubjectItem
from itemize_validation import validate_itemization_session


class ItemizeValidationTests(unittest.TestCase):
    def test_validate_itemization_session_accepts_current_well_formed_session(self) -> None:
        session = ItemizationSession(
            itemization_session_id="itemization_demo",
            subject_id="demo-subject",
            learning_context_snapshot_hash="snap-001",
            item_ids=("itm_alpha",),
            status="active",
            created_at_epoch_ms=100,
            updated_at_epoch_ms=100,
        )
        item = ItemizedSubjectItem(
            itemized_item_id="itm_alpha",
            subject_id="demo-subject",
            item_kind="entity",
            canonical_label="Alpha",
            source_refs=("source:source_demo",),
            confidence=0.8,
            status="candidate",
            created_at_epoch_ms=100,
            updated_at_epoch_ms=100,
        )

        validation = validate_itemization_session(
            session,
            items=(item,),
            learning_context_snapshot_hash="snap-001",
        )

        self.assertEqual(validation["status"], "ok")
        self.assertEqual(validation["snapshot_status"], "current")
        self.assertEqual(validation["item_count"], 1)
        self.assertEqual(validation["item_kind_counts"], {"entity": 1})

    def test_validate_itemization_session_flags_stale_duplicate_and_untracked_items(self) -> None:
        session = ItemizationSession(
            itemization_session_id="itemization_demo",
            subject_id="demo-subject",
            learning_context_snapshot_hash="snap-001",
            item_ids=("itm_alpha", "itm_alpha"),
            status="active",
        )
        alpha = ItemizedSubjectItem(
            itemized_item_id="itm_alpha",
            subject_id="demo-subject",
            item_kind="entity",
            canonical_label="Alpha",
            source_refs=("source:source_demo",),
            status="candidate",
        )
        stray = ItemizedSubjectItem(
            itemized_item_id="itm_stray",
            subject_id="demo-subject",
            item_kind="entity",
            canonical_label="Alpha",
            source_refs=(),
            status="candidate",
        )

        validation = validate_itemization_session(
            session,
            items=(alpha, stray),
            learning_context_snapshot_hash="snap-002",
        )

        self.assertEqual(validation["status"], "error")
        self.assertEqual(validation["snapshot_status"], "stale")
        self.assertTrue(any("item_ids must be unique" in str(item) for item in validation["errors"]))
        self.assertTrue(any("missing from the session" in str(item) for item in validation["errors"]))
        self.assertTrue(any("must declare at least one source_ref" in str(item) for item in validation["errors"]))
        self.assertTrue(any("duplicate item kind/label pairs" in str(item) for item in validation["errors"]))


if __name__ == "__main__":
    unittest.main()
