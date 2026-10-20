# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from itemize import list_itemized_subject_items, materialize_itemization_session
from learning_context import (
    LearningContext,
    LearningUnit,
    load_learning_context,
    new_learning_delta,
    new_learning_source,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    stable_learning_unit_id,
)
from review_composition import (
    ReviewTransformReceipt,
    included_review_composition_unit_ids,
    merge_review_item_with_next_sibling,
    list_review_transform_receipts,
    list_review_items,
    load_review_composition,
    persist_review_transform_receipt,
    persist_review_composition,
    promote_review_item_to_root,
    review_composition_from_itemization,
    review_composition_paths,
    split_review_item_into_children,
    stable_review_transform_receipt_id,
)


class ReviewCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _persist_demo_context(self) -> str:
        subject_id = "review-composition-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Controls Notes",
            source_ref="notes/controls.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Controls Notes\n\n"
                "## Alpha Control\nAlpha matters.\n\n"
                "## Beta Control\nBeta matters.\n\n"
                "$$ P = A / B $$\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the initial controls subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Review Composition Demo",
                aliases=("Review Composition Demo",),
                subject_family="Governance",
                summary="Review composition test subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Alpha Control",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Alpha Control",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Beta Control",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Beta Control",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        return subject_id

    def test_review_composition_round_trips_seeded_items(self) -> None:
        subject_id = self._persist_demo_context()
        context = load_learning_context(self.root, subject_id)
        session, itemized_items = materialize_itemization_session(self.root, subject_id)

        composition, review_items = review_composition_from_itemization(
            context,
            session,
            itemized_items,
            build_epoch_ms=123,
            status="draft",
        )
        persist_review_composition(self.root, composition, review_items)

        self.assertTrue(review_composition_paths(self.root, subject_id)["composition"].is_file())
        loaded_composition = load_review_composition(self.root, subject_id)
        loaded_items = list_review_items(self.root, subject_id)

        self.assertEqual(loaded_composition.review_composition_id, composition.review_composition_id)
        self.assertEqual(loaded_composition.learning_context_snapshot_hash, context.content_hash())
        self.assertEqual(len(loaded_items), len(review_items))
        self.assertTrue(any(item.semantic_kind == "equation" for item in loaded_items))
        self.assertTrue(any(item.render_kind == "equation_block" for item in loaded_items))

    def test_review_composition_still_includes_non_rejected_items_when_some_items_are_promoted(self) -> None:
        subject_id = self._persist_demo_context()
        context = load_learning_context(self.root, subject_id)
        session, itemized_items = materialize_itemization_session(self.root, subject_id)

        alpha_item = next(item for item in itemized_items if item.source_unit_id and item.canonical_label == "Alpha Control")
        updated_itemized_items = tuple(
            replace(item, status="promoted")
            if item.itemized_item_id == alpha_item.itemized_item_id
            else item
            for item in itemized_items
        )

        composition, review_items = review_composition_from_itemization(
            context,
            session,
            updated_itemized_items,
            build_epoch_ms=456,
            status="draft",
        )

        included_unit_ids = included_review_composition_unit_ids(review_items)

        self.assertEqual(composition.metadata.get("seed_mode"), "all_non_rejected_items")
        self.assertIn(alpha_item.source_unit_id, included_unit_ids)
        self.assertEqual(len(included_unit_ids), 2)

    def test_review_composition_refresh_preserves_existing_orientation(self) -> None:
        subject_id = self._persist_demo_context()
        context = load_learning_context(self.root, subject_id)
        session, itemized_items = materialize_itemization_session(self.root, subject_id)
        composition, review_items = review_composition_from_itemization(
            context,
            session,
            itemized_items,
            build_epoch_ms=789,
            status="draft",
        )

        target = next(item for item in review_items if item.semantic_kind == "equation")
        preserved = replace(
            target,
            render_kind="citation_callout",
            included=True,
        )
        updated_items = tuple(
            preserved if item.review_item_id == target.review_item_id else item
            for item in review_items
        )
        persist_review_composition(self.root, composition, updated_items)

        refreshed_composition, refreshed_items = review_composition_from_itemization(
            context,
            session,
            itemized_items,
            existing=load_review_composition(self.root, subject_id),
            existing_items=list_review_items(self.root, subject_id),
            build_epoch_ms=790,
            status="draft",
        )
        refreshed_target = next(item for item in refreshed_items if item.review_item_id == target.review_item_id)

        self.assertEqual(refreshed_composition.review_composition_id, composition.review_composition_id)
        self.assertEqual(refreshed_target.render_kind, "citation_callout")
        self.assertTrue(refreshed_target.included)

    def test_review_composition_refresh_preserves_manual_draft_rephrase_across_source_refresh(self) -> None:
        subject_id = self._persist_demo_context()
        context = load_learning_context(self.root, subject_id)
        session, itemized_items = materialize_itemization_session(self.root, subject_id)
        composition, review_items = review_composition_from_itemization(
            context,
            session,
            itemized_items,
            build_epoch_ms=789,
            status="draft",
        )

        alpha_item = next(
            item
            for item in itemized_items
            if item.item_kind == "glossary_term" and item.canonical_label == "Alpha Control"
        )
        target = next(
            item
            for item in review_items
            if item.source_itemized_item_id == alpha_item.itemized_item_id
        )
        preserved = replace(
            target,
            notes="Program governance should be described as one federated control plane.",
            transform_mode="rewrite_manual",
            metadata={
                **dict(target.metadata),
                "canonical_label": "Program Governance Control",
                "last_rephrase_phase": "draft",
                "last_rephrase_mode": "manual",
            },
        )
        updated_items = tuple(
            preserved if item.review_item_id == target.review_item_id else item
            for item in review_items
        )
        persist_review_composition(self.root, composition, updated_items)

        refreshed_context = replace(
            context,
            units=tuple(
                replace(
                    unit,
                    canonical_title="Governance Control",
                    statement="Governance control coordinates alpha oversight."
                )
                if unit.canonical_title == "Alpha Control"
                else unit
                for unit in context.units
            ),
        )
        persist_learning_context(self.root, refreshed_context)
        refreshed_session, refreshed_itemized_items = materialize_itemization_session(self.root, subject_id)

        refreshed_composition, refreshed_items = review_composition_from_itemization(
            refreshed_context,
            refreshed_session,
            refreshed_itemized_items,
            existing=load_review_composition(self.root, subject_id),
            existing_items=list_review_items(self.root, subject_id),
            build_epoch_ms=790,
            status="draft",
        )
        refreshed_target = next(item for item in refreshed_items if item.review_item_id == target.review_item_id)

        self.assertEqual(refreshed_composition.review_composition_id, composition.review_composition_id)
        self.assertEqual(refreshed_target.source_itemized_item_id, alpha_item.itemized_item_id)
        self.assertEqual(
            refreshed_target.notes,
            "Program governance should be described as one federated control plane.",
        )
        self.assertEqual(refreshed_target.metadata.get("canonical_label"), "Program Governance Control")
        self.assertEqual(refreshed_target.transform_mode, "rewrite_manual")

    def test_review_composition_refresh_preserves_llm_draft_rephrase_across_source_refresh(self) -> None:
        subject_id = self._persist_demo_context()
        context = load_learning_context(self.root, subject_id)
        session, itemized_items = materialize_itemization_session(self.root, subject_id)
        composition, review_items = review_composition_from_itemization(
            context,
            session,
            itemized_items,
            build_epoch_ms=701,
            status="draft",
        )
        persist_review_composition(self.root, composition, review_items)

        alpha_item = next(
            item
            for item in itemized_items
            if item.item_kind == "glossary_term" and item.canonical_label == "Alpha Control"
        )
        target = next(
            item
            for item in review_items
            if item.source_itemized_item_id == alpha_item.itemized_item_id
        )
        preserved = replace(
            target,
            notes="Program governance should be described as one federated control plane.",
            transform_mode="rewrite_llm_proposal",
            metadata={
                **dict(target.metadata),
                "canonical_label": "Program Governance Control",
                "last_rephrase_phase": "draft",
                "last_rephrase_mode": "llm_proposal",
            },
        )
        updated_items = tuple(
            preserved if item.review_item_id == target.review_item_id else item
            for item in review_items
        )
        persist_review_composition(self.root, composition, updated_items)

        refreshed_context = replace(
            context,
            units=tuple(
                replace(
                    unit,
                    canonical_title="Governance Control",
                    statement="Governance control coordinates alpha oversight."
                )
                if unit.canonical_title == "Alpha Control"
                else unit
                for unit in context.units
            ),
        )
        persist_learning_context(self.root, refreshed_context)
        refreshed_session, refreshed_itemized_items = materialize_itemization_session(self.root, subject_id)

        refreshed_composition, refreshed_items = review_composition_from_itemization(
            refreshed_context,
            refreshed_session,
            refreshed_itemized_items,
            existing=load_review_composition(self.root, subject_id),
            existing_items=list_review_items(self.root, subject_id),
            build_epoch_ms=791,
            status="draft",
        )
        refreshed_target = next(item for item in refreshed_items if item.review_item_id == target.review_item_id)

        self.assertEqual(refreshed_composition.review_composition_id, composition.review_composition_id)
        self.assertEqual(refreshed_target.source_itemized_item_id, alpha_item.itemized_item_id)
        self.assertEqual(
            refreshed_target.notes,
            "Program governance should be described as one federated control plane.",
        )
        self.assertEqual(refreshed_target.metadata.get("canonical_label"), "Program Governance Control")
        self.assertEqual(refreshed_target.transform_mode, "rewrite_llm_proposal")

    def test_review_composition_split_merge_and_promote_children(self) -> None:
        subject_id = self._persist_demo_context()
        context = load_learning_context(self.root, subject_id)
        session, itemized_items = materialize_itemization_session(self.root, subject_id)
        composition, review_items = review_composition_from_itemization(
            context,
            session,
            itemized_items,
            build_epoch_ms=901,
            status="draft",
        )

        alpha_root = next(item for item in review_items if item.metadata.get("canonical_label") == "Alpha Control")
        alpha_root = replace(
            alpha_root,
            metadata={
                **dict(alpha_root.metadata),
                "aliases": ["Access Control", "Audit Control"],
            },
        )
        beta_root = next(item for item in review_items if item.metadata.get("canonical_label") == "Beta Control")
        updated_review_items = tuple(
            alpha_root if item.review_item_id == alpha_root.review_item_id else item
            for item in review_items
        )

        split_result = split_review_item_into_children(
            composition,
            updated_review_items,
            review_item_id=alpha_root.review_item_id,
            build_epoch_ms=902,
        )
        self.assertIsNotNone(split_result)
        split_composition, split_items, split_parent, child_items = split_result or (None, (), None, ())
        self.assertEqual(split_parent.child_review_item_ids, tuple(item.review_item_id for item in child_items))
        self.assertFalse(split_parent.included)
        self.assertEqual({item.metadata.get("canonical_label") for item in child_items}, {"Access Control", "Audit Control"})

        merge_result = merge_review_item_with_next_sibling(
            split_composition,
            split_items,
            review_item_id=child_items[0].review_item_id,
            build_epoch_ms=903,
        )
        self.assertIsNotNone(merge_result)
        merged_composition, merged_items, merged_item, merged_sources = merge_result or (None, (), None, ())
        self.assertEqual(len(merged_sources), 2)
        self.assertEqual(merged_item.parent_review_item_id, split_parent.review_item_id)
        self.assertEqual(merged_item.metadata.get("origin"), "review_merge")

        promote_result = promote_review_item_to_root(
            merged_composition,
            merged_items,
            review_item_id=merged_item.review_item_id,
            build_epoch_ms=904,
        )
        self.assertIsNotNone(promote_result)
        promoted_composition, promoted_items, promoted_item = promote_result or (None, (), None)
        self.assertEqual(promoted_item.parent_review_item_id, "")
        self.assertIn(promoted_item.review_item_id, promoted_composition.root_review_item_ids)
        self.assertTrue(any(item.review_item_id == beta_root.review_item_id for item in promoted_items))

    def test_review_transform_receipts_round_trip_in_created_order(self) -> None:
        subject_id = self._persist_demo_context()
        context = load_learning_context(self.root, subject_id)
        session, itemized_items = materialize_itemization_session(self.root, subject_id)
        composition, review_items = review_composition_from_itemization(
            context,
            session,
            itemized_items,
            build_epoch_ms=1001,
            status="draft",
        )
        persist_review_composition(self.root, composition, review_items)
        target_item = next(item for item in review_items if item.metadata.get("canonical_label") == "Alpha Control")

        split_receipt = ReviewTransformReceipt(
            receipt_id=stable_review_transform_receipt_id(
                review_item_id=target_item.review_item_id,
                transform_kind="split",
                output_snapshot_hash="split-output",
            ),
            review_item_id=target_item.review_item_id,
            review_composition_id=composition.review_composition_id,
            transform_kind="split",
            input_snapshot_hash="before",
            output_snapshot_hash="split-output",
            operator="test",
            notes="Split Alpha into child items.",
            created_at_epoch_ms=1002,
        )
        merge_receipt = ReviewTransformReceipt(
            receipt_id=stable_review_transform_receipt_id(
                review_item_id=target_item.review_item_id,
                transform_kind="merge",
                output_snapshot_hash="merge-output",
            ),
            review_item_id=target_item.review_item_id,
            review_composition_id=composition.review_composition_id,
            transform_kind="merge",
            input_snapshot_hash="split-output",
            output_snapshot_hash="merge-output",
            operator="test",
            notes="Merged Alpha child items.",
            created_at_epoch_ms=1003,
        )

        persist_review_transform_receipt(self.root, subject_id, merge_receipt)
        persist_review_transform_receipt(self.root, subject_id, split_receipt)

        loaded_receipts = list_review_transform_receipts(self.root, subject_id)

        self.assertEqual(tuple(receipt.transform_kind for receipt in loaded_receipts), ("split", "merge"))
        self.assertEqual(loaded_receipts[0].notes, "Split Alpha into child items.")
        self.assertEqual(loaded_receipts[1].input_snapshot_hash, "split-output")
        self.assertTrue(review_composition_paths(self.root, subject_id)["receipts"].is_dir())
