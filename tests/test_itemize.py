# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import replace
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from itemize import (
    ItemizationSession,
    ItemizedSubjectItem,
    itemization_paths,
    list_itemized_subject_items,
    load_itemization_session,
    load_itemized_subject_item,
    materialize_itemization_session,
    persist_itemization_session,
    stable_itemization_session_id,
    stable_itemized_item_id,
)
from learning_context import (
    LearningContext,
    LearningUnit,
    canonical_learning_subject_id,
    new_learning_source,
    persist_learning_context,
    persist_learning_source,
    persist_learning_source_bundle_files,
)


class ItemizeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_persist_itemization_session_round_trips_items(self) -> None:
        subject_id = canonical_learning_subject_id("Thermodynamics")
        item = ItemizedSubjectItem(
            itemized_item_id="itm_pressure_001",
            subject_id=subject_id,
            item_kind="entity",
            canonical_label="Pressure",
            source_unit_id="unit_pressure",
            aliases=("Pressure", "P"),
            summary="Pressure entity candidate.",
            source_refs=("source:source_thermo_001", "unit:unit_pressure"),
            confidence=0.9,
            linked_item_ids=("itm_pressure_equation",),
            created_at_epoch_ms=100,
            updated_at_epoch_ms=100,
            metadata={"origin": "learning_unit"},
        )
        session = ItemizationSession(
            itemization_session_id=stable_itemization_session_id(
                subject_id=subject_id,
                learning_context_snapshot_hash="abc123",
            ),
            subject_id=subject_id,
            learning_context_snapshot_hash="abc123",
            item_ids=(item.itemized_item_id,),
            status="active",
            created_at_epoch_ms=100,
            updated_at_epoch_ms=100,
            metadata={"item_count": 1},
        )

        session_path = persist_itemization_session(self.root, session, (item,))

        self.assertEqual(session_path, itemization_paths(self.root, subject_id)["session"])
        loaded_session = load_itemization_session(self.root, subject_id)
        loaded_item = load_itemized_subject_item(self.root, subject_id, item.itemized_item_id)

        self.assertEqual(loaded_session.itemization_session_id, session.itemization_session_id)
        self.assertEqual(loaded_session.item_ids, (item.itemized_item_id,))
        self.assertEqual(loaded_item.source_unit_id, "unit_pressure")
        self.assertEqual(loaded_item.aliases, ("Pressure", "P"))
        self.assertEqual(loaded_item.created_at_epoch_ms, 100)
        self.assertEqual(loaded_item.updated_at_epoch_ms, 100)
        self.assertEqual(loaded_item.linked_item_ids, ("itm_pressure_equation",))

    def test_persist_itemization_session_removes_stale_item_files(self) -> None:
        subject_id = canonical_learning_subject_id("Thermodynamics")
        alpha = ItemizedSubjectItem(
            itemized_item_id="itm_alpha_001",
            subject_id=subject_id,
            item_kind="entity",
            canonical_label="Alpha",
            source_refs=("source:source_thermo_001",),
            confidence=0.9,
        )
        beta = ItemizedSubjectItem(
            itemized_item_id="itm_beta_001",
            subject_id=subject_id,
            item_kind="entity",
            canonical_label="Beta",
            source_refs=("source:source_thermo_001",),
            confidence=0.9,
        )
        initial_session = ItemizationSession(
            itemization_session_id=stable_itemization_session_id(
                subject_id=subject_id,
                learning_context_snapshot_hash="abc123",
            ),
            subject_id=subject_id,
            learning_context_snapshot_hash="abc123",
            item_ids=(alpha.itemized_item_id, beta.itemized_item_id),
            status="active",
        )
        persist_itemization_session(self.root, initial_session, (alpha, beta))

        refreshed_session = ItemizationSession(
            itemization_session_id=stable_itemization_session_id(
                subject_id=subject_id,
                learning_context_snapshot_hash="def456",
            ),
            subject_id=subject_id,
            learning_context_snapshot_hash="def456",
            item_ids=(alpha.itemized_item_id,),
            status="active",
        )
        persist_itemization_session(self.root, refreshed_session, (alpha,))

        listed_ids = {item.itemized_item_id for item in list_itemized_subject_items(self.root, subject_id)}
        self.assertEqual(listed_ids, {alpha.itemized_item_id})
        self.assertFalse((itemization_paths(self.root, subject_id)["items"] / f"{beta.itemized_item_id}.json").exists())

    def test_materialize_itemization_session_extracts_units_equations_variables_and_xrefs(self) -> None:
        subject_id = canonical_learning_subject_id("Ideal Gas State Relation")
        markdown_text = """
# Ideal Gas State Relation

## Pressure From Amount Temperature And Volume
How do you calculate pressure from amount, temperature, and volume?
- Inputs: n, R, T, V
- Output: P
- Xref depends_on: Mole Counting

$$ P = \\frac{nRT}{V} $$
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Ideal Gas State Relation",
            source_ref="/tmp/ideal-gas.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Ideal Gas State Relation",
            aliases=("Ideal Gas State Relation",),
            subject_family="Chemistry",
            summary="Relates pressure, amount, temperature, and volume.",
            units=(
                LearningUnit(
                    unit_id="unit_ideal_gas_definition",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Ideal Gas State Relation",
                    statement="The ideal gas relation connects pressure, amount, temperature, and volume.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_pressure_capability",
                    subject_id=subject_id,
                    unit_kind="ability",
                    canonical_title="Calculate Pressure From Amount Temperature And Volume",
                    statement="Calculate pressure from amount, temperature, and volume using the ideal gas relation.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id="unit_pressure_boundary",
                    subject_id=subject_id,
                    unit_kind="boundary",
                    canonical_title="Pressure Validity Boundary",
                    statement="This relation cannot be applied unless the gas behaves ideally.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        session, items = materialize_itemization_session(self.root, subject_id)

        self.assertTrue(itemization_paths(self.root, subject_id)["session"].is_file())
        self.assertEqual(session.subject_id, subject_id)
        self.assertGreaterEqual(len(items), 1)

        items_by_kind: dict[str, list[ItemizedSubjectItem]] = {}
        for item in items:
            items_by_kind.setdefault(item.item_kind, []).append(item)

        glossary_labels = {item.canonical_label for item in items_by_kind.get("glossary_term", [])}
        self.assertIn("Ideal Gas State Relation", glossary_labels)

        claim_source_units = {item.source_unit_id for item in items_by_kind.get("claim", [])}
        self.assertIn("unit_pressure_capability", claim_source_units)

        decision_roles = {
            (item.canonical_label, str(item.metadata.get("decision_role", "")))
            for item in items_by_kind.get("decision_role_candidate", [])
        }
        self.assertIn(("Calculate Pressure From Amount Temperature And Volume", "capability"), decision_roles)
        self.assertIn(("Pressure Validity Boundary", "boundary"), decision_roles)

        equation_labels = [item.canonical_label for item in items_by_kind.get("equation", [])]
        self.assertTrue(any(label.startswith("P =") and "n" in label and "V" in label for label in equation_labels))

        variable_labels = {item.canonical_label for item in items_by_kind.get("variable", [])}
        self.assertTrue({"P", "n", "R", "T", "V"}.issubset(variable_labels))

        xref_items = items_by_kind.get("xref_candidate", [])
        self.assertEqual(len(xref_items), 1)
        self.assertEqual(xref_items[0].metadata["xref_type"], "depends_on")
        self.assertEqual(xref_items[0].metadata["target_label"], "Mole Counting")

    def test_materialize_itemization_session_discovers_sources_even_without_linked_source_ids(self) -> None:
        subject_id = canonical_learning_subject_id("Mole Counting")
        markdown_text = """
# Mole Counting

## Count From Groups
- Inputs: G, cg
- Output: C

$$ C = G cg $$
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Mole Counting",
            source_ref="/tmp/mole-counting.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=1,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Mole Counting",
            aliases=("Mole Counting",),
            subject_family="Chemistry",
            summary="Grouped counting relation.",
            units=(),
            linked_source_ids=(),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        _session, items = materialize_itemization_session(self.root, subject_id)

        equation_labels = {item.canonical_label for item in items if item.item_kind == "equation"}
        self.assertTrue(any(label.startswith("C =") for label in equation_labels))
        variable_labels = {item.canonical_label for item in items if item.item_kind == "variable"}
        self.assertTrue({"C", "G", "cg"}.issubset(variable_labels))

    def test_materialize_itemization_session_merges_direct_llm_decomposition_candidates_when_allowed(self) -> None:
        subject_id = canonical_learning_subject_id("Smart City Travel")
        markdown_text = """
# Smart City Travel

- A city transit authority wants to modernize fare payment.
- Today riders mostly use cash and plastic transit cards.
- The city wants to introduce app-based and contactless bank-card payment.
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Smart City Travel",
            aliases=("Smart City Travel",),
            subject_family="Transit",
            summary="Fare modernization prose.",
            units=(
                LearningUnit(
                    unit_id="unit_smart_city_travel",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Smart City Travel",
                    statement="A city transit authority wants to modernize fare payment.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        captured: dict[str, object] = {}

        class FakeController:
            def request_proposal(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(
                    id="proposal-direct-itemize",
                    source="fake-runtime",
                    payload={
                        "candidates": [
                            {
                                "canonical_label": "Introduce contactless bank-card payment",
                                "item_kind": "decision_role_candidate",
                                "decision_role": "transition",
                                "summary": "Target payment mode introduces contactless bank-card payment.",
                                "confidence": 0.85,
                                "aliases": [],
                            },
                            {
                                "canonical_label": "Fare payment supports contactless bank-card payment",
                                "item_kind": "decision_role_candidate",
                                "decision_role": "state",
                                "summary": "The achieved fare-payment arrangement supports contactless bank-card payment.",
                                "confidence": 0.85,
                                "aliases": [],
                            }
                        ]
                    },
                )

        with patch(
            "itemize.bootstrap_runtime_controller",
            return_value=(SimpleNamespace(), FakeController()),
        ):
            session, items = materialize_itemization_session(
                self.root,
                subject_id,
                allow_direct_llm_decomposition=True,
            )

        labels = {item.canonical_label for item in items}
        self.assertIn("Introduce contactless bank-card payment", labels)
        self.assertIn("Fare payment supports contactless bank-card payment", labels)
        self.assertIn("cash", str(captured["instructions"]).lower())
        self.assertIn("plastic transit cards", str(captured["instructions"]).lower())
        self.assertIn("do not emit bare nouns like 'Cash'", str(captured["instructions"]))
        self.assertIn("emit role-shaped transition labels like 'introduce app-based payment'", str(captured["instructions"]))
        self.assertIn("emit both the transition and the resulting target state or capability", str(captured["instructions"]))
        self.assertIn("fare payment supports contactless bank-card payment", str(captured["instructions"]).lower())
        self.assertEqual(session.metadata["direct_llm_decomposition_status"], "used")
        self.assertEqual(session.metadata["direct_llm_candidate_count"], 2)

    def test_materialize_itemization_session_skips_direct_llm_decomposition_when_disabled(self) -> None:
        subject_id = canonical_learning_subject_id("Smart City Travel")
        markdown_text = """
# Smart City Travel

- A city transit authority wants to modernize fare payment.
- Today riders mostly use cash and plastic transit cards.
- The city wants to introduce app-based and contactless bank-card payment.
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Smart City Travel",
            aliases=("Smart City Travel",),
            subject_family="Transit",
            summary="Fare modernization prose.",
            units=(
                LearningUnit(
                    unit_id="unit_smart_city_travel",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Smart City Travel",
                    statement="A city transit authority wants to modernize fare payment.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        with patch(
            "itemize.bootstrap_runtime_controller",
            side_effect=AssertionError("direct llm decomposition should be disabled"),
        ):
            _session, items = materialize_itemization_session(
                self.root,
                subject_id,
                allow_direct_llm_decomposition=False,
            )

        self.assertNotIn(
            "Introduce contactless bank-card payment",
            {item.canonical_label for item in items},
        )

    def test_materialize_itemization_session_falls_back_to_generic_source_decomposition_when_direct_llm_returns_empty(self) -> None:
        subject_id = canonical_learning_subject_id("Smart City Travel")
        markdown_text = """
# Smart City Travel

- A city transit authority wants to modernize fare payment.
- Today riders mostly use cash and plastic transit cards.
- The city wants to introduce app-based and contactless bank-card payment.
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Smart City Travel",
            aliases=("Smart City Travel",),
            subject_family="Transit",
            summary="Fare modernization prose.",
            units=(
                LearningUnit(
                    unit_id="unit_smart_city_travel",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Smart City Travel",
                    statement="A city transit authority wants to modernize fare payment.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        class FakeController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        with patch(
            "itemize.bootstrap_runtime_controller",
            return_value=(SimpleNamespace(), FakeController()),
        ):
            session, items = materialize_itemization_session(
                self.root,
                subject_id,
                allow_direct_llm_decomposition=True,
            )

        labels = {item.canonical_label.casefold() for item in items}
        self.assertTrue(
            {
                "city transit authority",
                "modernize fare payment",
                "legacy fare payment via cash",
                "legacy fare payment via plastic transit cards",
                "introduce app-based payment",
                "introduce contactless bank-card payment",
                "fare payment supports app-based payment",
                "fare payment supports contactless bank-card payment",
            }.issubset(labels)
        )
        self.assertEqual(session.metadata["direct_llm_decomposition_status"], "fallback")
        self.assertEqual(session.metadata["direct_llm_candidate_count"], 0)
        self.assertGreaterEqual(int(session.metadata["fallback_candidate_count"]), 8)

    def test_materialize_itemization_session_assigns_single_admitted_unit_to_weak_prose_candidates(self) -> None:
        subject_id = canonical_learning_subject_id("Smart City Travel")
        markdown_text = """
# Smart City Travel

A city transit authority wants to modernize fare payment.
At present, most passengers pay using cash or plastic transit cards.
The city now wants to introduce app-based payment and contactless bank-card payment, while keeping the bus network reliable and accessible.

The main parties involved are the transit authority, private bus operators, the payment processor, the city regulator, and passengers.
Each party has a different concern. The transit authority wants a faster and more reliable fare system.
Private bus operators need changes that can be implemented without disrupting daily service.
The payment processor must support secure and dependable transactions.
The regulator must ensure that the system follows legal, privacy, and inclusion requirements.
Passengers need the payment system to be easy, fast, trustworthy, and fair.
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel-v2.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Smart City Travel",
            aliases=("Smart City Travel",),
            subject_family="Transit",
            summary="Fare modernization prose with stakeholder list.",
            units=(
                LearningUnit(
                    unit_id="unit_smart_city_travel",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Smart City Travel",
                    statement="A city transit authority wants to modernize fare payment.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        class FakeController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        with patch(
            "itemize.bootstrap_runtime_controller",
            return_value=(SimpleNamespace(), FakeController()),
        ):
            _session, items = materialize_itemization_session(
                self.root,
                subject_id,
                allow_direct_llm_decomposition=True,
            )

        weak_prose_labels = {
            "city transit authority",
            "private bus operators",
            "payment processor",
            "city regulator",
            "passengers",
            "introduce app-based payment",
            "introduce contactless bank-card payment",
            "keep bus network reliable",
            "keep bus network accessible",
        }
        resolved_source_unit_ids = {
            item.canonical_label.casefold(): item.source_unit_id
            for item in items
            if item.canonical_label.casefold() in weak_prose_labels
        }

        self.assertTrue(weak_prose_labels.issubset(set(resolved_source_unit_ids)))
        for label, source_unit_id in resolved_source_unit_ids.items():
            self.assertEqual(source_unit_id, "unit_smart_city_travel", label)

    def test_materialize_itemization_session_supplements_direct_llm_with_party_list_actors_and_prunes_temporal_actor_noise(self) -> None:
        subject_id = canonical_learning_subject_id("Smart City Travel")
        markdown_text = """
# Smart City Travel

A city transit authority wants to modernize fare payment.
At present, most passengers pay using cash or plastic transit cards.
The city now wants to introduce app-based payment and contactless bank-card payment, while keeping the bus network reliable and accessible.

The main parties involved are the transit authority, private bus operators, the payment processor, the city regulator, and passengers.
Each party has a different concern. The transit authority wants a faster and more reliable fare system.
Private bus operators need changes that can be implemented without disrupting daily service.
The payment processor must support secure and dependable transactions.
The regulator must ensure that the system follows legal, privacy, and inclusion requirements.
Passengers need the payment system to be easy, fast, trustworthy, and fair.
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel-v2.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Smart City Travel",
            aliases=("Smart City Travel",),
            subject_family="Transit",
            summary="Fare modernization prose with stakeholder list.",
            units=(
                LearningUnit(
                    unit_id="unit_smart_city_travel",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Smart City Travel",
                    statement="A city transit authority wants to modernize fare payment.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        class FakeController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-v2",
                    source="fake-runtime",
                    payload={
                        "candidates": [
                            {
                                "canonical_label": "City now",
                                "item_kind": "decision_role_candidate",
                                "decision_role": "actor",
                                "summary": "The city now wants to introduce app-based payment.",
                                "confidence": 0.82,
                            },
                            {
                                "canonical_label": "Introduce contactless bank-card payment",
                                "item_kind": "decision_role_candidate",
                                "decision_role": "transition",
                                "summary": "Target arrangement introduces contactless bank-card payment.",
                                "confidence": 0.82,
                            },
                        ]
                    },
                )

        with patch(
            "itemize.bootstrap_runtime_controller",
            return_value=(SimpleNamespace(), FakeController()),
        ):
            session, items = materialize_itemization_session(
                self.root,
                subject_id,
                allow_direct_llm_decomposition=True,
            )

        labels_by_role: dict[str, set[str]] = {}
        for item in items:
            role = str(item.metadata.get("decision_role", "")).casefold()
            if not role:
                continue
            labels_by_role.setdefault(role, set()).add(item.canonical_label.casefold())

        self.assertTrue(
            {
                "city transit authority",
                "private bus operators",
                "payment processor",
                "city regulator",
                "passengers",
            }.issubset(labels_by_role.get("actor", set()))
        )
        self.assertNotIn("city now", labels_by_role.get("actor", set()))
        self.assertNotIn("city", labels_by_role.get("actor", set()))
        self.assertIn("keep bus network reliable", labels_by_role.get("constraint", set()))
        self.assertIn("keep bus network accessible", labels_by_role.get("constraint", set()))
        self.assertGreaterEqual(int(session.metadata["fallback_candidate_count"]), 10)

    def test_materialize_itemization_session_extracts_figure_candidates_from_url_bundle(self) -> None:
        subject_id = canonical_learning_subject_id("Study Buddy Guru")
        source = new_learning_source(
            subject_id=subject_id,
            title="Study Buddy Guru",
            source_ref="https://studybuddy.guru",
            source_kind="url",
            media_type="text/markdown",
            section_count=1,
            metadata={"requested_url": "https://studybuddy.guru"},
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Study Buddy Guru\n\nA science learning website.\n",
        )
        persist_learning_source_bundle_files(
            self.root,
            subject_id=subject_id,
            source_id=source.source_id,
            bundle_files={
                "elements.json": json.dumps(
                    [
                        {"kind": "heading", "level": 1, "text": "Study Buddy Guru"},
                        {"kind": "image", "src": "/assets/hero.png", "alt": "Hero Diagram", "mime_type": "image/png"},
                    ],
                    indent=2,
                    sort_keys=True,
                ),
                "asset-manifest.json": json.dumps(
                    [
                        {
                            "asset_url": "https://studybuddy.guru/assets/hero.png",
                            "local_relpath": "assets/image-001.png",
                            "status": "downloaded",
                            "alt_text": "Hero Diagram",
                        }
                    ],
                    indent=2,
                    sort_keys=True,
                ),
            },
        )
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Study Buddy Guru",
            aliases=("Study Buddy Guru",),
            subject_family="Website",
            summary="A science learning website.",
            units=(),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        _session, items = materialize_itemization_session(self.root, subject_id)

        figure_items = [item for item in items if item.item_kind == "figure_candidate"]
        self.assertEqual(len(figure_items), 1)
        self.assertEqual(figure_items[0].canonical_label, "Hero Diagram")
        self.assertEqual(figure_items[0].metadata["asset_src"], "/assets/hero.png")
        self.assertIn(source.source_id, figure_items[0].source_refs)

    def test_materialize_itemization_session_preserves_existing_itemize_edits_and_manual_children(self) -> None:
        subject_id = canonical_learning_subject_id("Controls")
        source = new_learning_source(
            subject_id=subject_id,
            title="Controls Notes",
            source_ref="/tmp/controls.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Controls\n\nAccess and audit controls matter.\n",
        )
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Controls",
            aliases=("Controls",),
            subject_family="Governance",
            summary="Control categories.",
            units=(
                LearningUnit(
                    unit_id="unit_controls",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Controls",
                    aliases=("Access Controls", "Audit Controls"),
                    statement="Access and audit controls matter.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        session, items = materialize_itemization_session(self.root, subject_id)
        entity_item = next(item for item in items if item.item_kind == "entity" and item.canonical_label == "Controls")
        split_child = ItemizedSubjectItem(
            itemized_item_id=stable_itemized_item_id(
                subject_id=subject_id,
                item_kind="entity",
                canonical_label="Access Controls",
                source_refs=entity_item.source_refs,
                disambiguator=f"split:{entity_item.itemized_item_id}",
            ),
            subject_id=subject_id,
            item_kind="entity",
            canonical_label="Access Controls",
            source_unit_id=entity_item.source_unit_id,
            aliases=("Access Controls",),
            summary=entity_item.summary,
            source_refs=entity_item.source_refs,
            confidence=entity_item.confidence,
            status="candidate",
            linked_item_ids=(entity_item.itemized_item_id,),
            created_at_epoch_ms=200,
            updated_at_epoch_ms=200,
            metadata={"origin": "itemize_split", "split_from": entity_item.itemized_item_id},
        )
        edited_items = []
        for item in items:
            if item.itemized_item_id == entity_item.itemized_item_id:
                edited_items.append(
                    ItemizedSubjectItem.from_dict(
                        {
                            **item.to_dict(),
                            "status": "promoted",
                            "metadata": {
                                **item.metadata,
                                "decision_role": "constraint",
                                "split_into": [split_child.itemized_item_id],
                            },
                        }
                    )
                )
            else:
                edited_items.append(item)
        edited_items.append(split_child)
        persist_itemization_session(
            self.root,
            ItemizationSession.from_dict(
                {
                    **session.to_dict(),
                    "item_ids": [item.itemized_item_id for item in edited_items],
                    "metadata": {**session.metadata, "item_count": len(edited_items)},
                }
            ),
            tuple(edited_items),
        )

        refreshed_session, refreshed_items = materialize_itemization_session(self.root, subject_id)

        refreshed_entity = next(
            item for item in refreshed_items
            if item.itemized_item_id == entity_item.itemized_item_id
        )
        preserved_child = next(
            item for item in refreshed_items
            if item.itemized_item_id == split_child.itemized_item_id
        )
        self.assertEqual(refreshed_session.subject_id, subject_id)
        self.assertEqual(refreshed_entity.status, "promoted")
        self.assertEqual(refreshed_entity.metadata.get("decision_role"), "constraint")
        self.assertEqual(preserved_child.metadata.get("origin"), "itemize_split")
        self.assertIn(split_child.itemized_item_id, refreshed_session.item_ids)

    def test_materialize_itemization_session_preserves_rephrased_wording_across_source_refresh(self) -> None:
        subject_id = canonical_learning_subject_id("Continuity Controls")
        source = new_learning_source(
            subject_id=subject_id,
            title="Controls Notes",
            source_ref="/tmp/continuity-controls.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Controls\n\nAlpha and beta controls matter.\n",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Continuity Controls",
                aliases=("Continuity Controls",),
                subject_family="Governance",
                summary="Control continuity test subject.",
                units=(
                    LearningUnit(
                        unit_id="unit_alpha",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Alpha Control",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id="unit_beta",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Beta Control",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                governance_status="active",
            ),
        )

        session, items = materialize_itemization_session(self.root, subject_id)
        alpha_term = next(
            item
            for item in items
            if item.item_kind == "glossary_term" and item.source_unit_id == "unit_alpha"
        )
        beta_term = next(
            item
            for item in items
            if item.item_kind == "glossary_term" and item.source_unit_id == "unit_beta"
        )
        edited_items = tuple(
            replace(
                item,
                canonical_label="Program Steering",
                aliases=tuple(dict.fromkeys((*item.aliases, item.canonical_label))),
                summary="Coordinate the program through one steering forum.",
                metadata={
                    **item.metadata,
                    "last_rephrase_phase": "itemize",
                    "last_rephrase_mode": "manual",
                },
            )
            if item.itemized_item_id == alpha_term.itemized_item_id
            else item
            for item in items
        )
        persist_itemization_session(
            self.root,
            ItemizationSession.from_dict(
                {
                    **session.to_dict(),
                    "item_ids": [item.itemized_item_id for item in edited_items],
                }
            ),
            edited_items,
        )

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Continuity Controls",
                aliases=("Continuity Controls",),
                subject_family="Governance",
                summary="Control continuity test subject.",
                units=(
                    LearningUnit(
                        unit_id="unit_alpha",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Governance Steering Committee",
                        statement="The steering committee coordinates the program.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id="unit_beta",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Risk Register",
                        statement="Track delivery risks.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                governance_status="active",
            ),
        )

        refreshed_session, refreshed_items = materialize_itemization_session(self.root, subject_id)

        refreshed_alpha = next(
            item
            for item in refreshed_items
            if item.item_kind == "glossary_term" and item.source_unit_id == "unit_alpha"
        )
        refreshed_beta = next(
            item
            for item in refreshed_items
            if item.item_kind == "glossary_term" and item.source_unit_id == "unit_beta"
        )

        self.assertEqual(refreshed_session.subject_id, subject_id)
        self.assertEqual(refreshed_alpha.itemized_item_id, alpha_term.itemized_item_id)
        self.assertEqual(refreshed_alpha.canonical_label, "Program Steering")
        self.assertEqual(refreshed_alpha.summary, "Coordinate the program through one steering forum.")
        self.assertEqual(refreshed_alpha.metadata.get("last_rephrase_phase"), "itemize")
        self.assertEqual(
            refreshed_alpha.metadata.get("latest_generated_canonical_label"),
            "Governance Steering Committee",
        )
        self.assertEqual(refreshed_beta.itemized_item_id, beta_term.itemized_item_id)
        self.assertEqual(refreshed_beta.canonical_label, "Risk Register")

    def test_materialize_itemization_session_preserves_llm_rephrased_wording_across_source_refresh(self) -> None:
        subject_id = "continuity-controls-llm"
        source = new_learning_source(
            subject_id=subject_id,
            title="Continuity Controls LLM",
            source_ref="notes/continuity-controls-llm.md",
            source_kind="markdown",
        )
        persist_learning_source(self.root, source, source_text="# Continuity Controls LLM\n")
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Continuity Controls LLM",
                aliases=("Continuity Controls LLM",),
                subject_family="Governance",
                summary="LLM continuity test subject.",
                units=(
                    LearningUnit(
                        unit_id="unit_alpha",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha coordinates the program.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                governance_status="active",
            ),
        )

        session, items = materialize_itemization_session(self.root, subject_id)
        alpha_term = next(
            item
            for item in items
            if item.item_kind == "glossary_term" and item.source_unit_id == "unit_alpha"
        )
        edited_items = tuple(
            replace(
                item,
                canonical_label="Program Steering",
                aliases=tuple(dict.fromkeys((*item.aliases, item.canonical_label))),
                summary="Coordinate the program through one steering forum.",
                metadata={
                    **item.metadata,
                    "last_rephrase_phase": "itemize",
                    "last_rephrase_mode": "llm_proposal",
                },
            )
            if item.itemized_item_id == alpha_term.itemized_item_id
            else item
            for item in items
        )
        persist_itemization_session(
            self.root,
            ItemizationSession.from_dict(
                {
                    **session.to_dict(),
                    "item_ids": [item.itemized_item_id for item in edited_items],
                }
            ),
            edited_items,
        )

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Continuity Controls LLM",
                aliases=("Continuity Controls LLM",),
                subject_family="Governance",
                summary="LLM continuity test subject.",
                units=(
                    LearningUnit(
                        unit_id="unit_alpha",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Governance Steering Committee",
                        statement="The steering committee coordinates the program.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                governance_status="active",
            ),
        )

        _refreshed_session, refreshed_items = materialize_itemization_session(self.root, subject_id)
        refreshed_alpha = next(
            item
            for item in refreshed_items
            if item.item_kind == "glossary_term" and item.source_unit_id == "unit_alpha"
        )

        self.assertEqual(refreshed_alpha.itemized_item_id, alpha_term.itemized_item_id)
        self.assertEqual(refreshed_alpha.canonical_label, "Program Steering")
        self.assertEqual(refreshed_alpha.summary, "Coordinate the program through one steering forum.")
        self.assertEqual(refreshed_alpha.metadata.get("last_rephrase_mode"), "llm_proposal")
        self.assertEqual(
            refreshed_alpha.metadata.get("latest_generated_canonical_label"),
            "Governance Steering Committee",
        )


if __name__ == "__main__":
    unittest.main()
