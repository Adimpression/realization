# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from realized_exchange.learning_context import (
    LearningContext,
    LearningDelta,
    LearningSource,
    LearningUnit,
    load_subject_import,
    load_subject_reasoning_scope,
    new_subject_import,
    apply_learning_delta,
    canonical_learning_subject_id,
    find_learning_context_by_lookup,
    learning_context_paths,
    list_subject_imports,
    list_learning_contexts,
    load_learning_context,
    load_learning_delta,
    load_learning_source,
    new_learning_context,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    persist_subject_import,
)


class LearningContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_persist_learning_context_materializes_phase1_corpus_home(self) -> None:
        context = LearningContext(
            subject_id=canonical_learning_subject_id("Newtonian Mechanics"),
            canonical_title="Newtonian Mechanics",
            aliases=("Mechanics", "Newtonian Mechanics"),
            subject_family="Physics",
            summary="Core classical mechanics relations.",
            units=(
                LearningUnit(
                    unit_id="unit_force",
                    subject_id=canonical_learning_subject_id("Newtonian Mechanics"),
                    unit_kind="relation",
                    canonical_title="Force From Mass And Acceleration",
                    aliases=("Newton's Second Law",),
                    statement="Force equals mass times acceleration.",
                    status="admitted",
                    linked_skill_ids=("skill_force",),
                    linked_artifact_ids=("artifact_force",),
                ),
            ),
            governance_status="active",
        )
        context_path = persist_learning_context(self.root, context)
        paths = learning_context_paths(self.root, context.subject_id)

        self.assertEqual(context_path, paths["context"])
        self.assertTrue(paths["root"].is_dir())
        self.assertTrue(paths["sources"].is_dir())
        self.assertTrue(paths["deltas"].is_dir())
        self.assertTrue(paths["derived_skills"].is_dir())
        self.assertTrue(paths["derived_exports"].is_dir())
        self.assertTrue(paths["receipts"].is_dir())
        self.assertTrue(paths["indexes"].is_dir())
        self.assertTrue(paths["context"].is_file())
        self.assertTrue(paths["subject_typ"].is_file())
        self.assertTrue(paths["subject_md"].is_file())
        self.assertTrue(paths["aliases_index"].is_file())
        self.assertTrue(paths["units_index"].is_file())

        loaded = load_learning_context(self.root, context.subject_id)
        self.assertEqual(loaded.subject_id, context.subject_id)
        self.assertEqual(loaded.canonical_title, "Newtonian Mechanics")
        self.assertEqual(len(loaded.units), 1)
        self.assertEqual(loaded.units[0].canonical_title, "Force From Mass And Acceleration")

        aliases_index = json.loads(paths["aliases_index"].read_text(encoding="utf-8"))
        units_index = json.loads(paths["units_index"].read_text(encoding="utf-8"))
        self.assertEqual(aliases_index["subject_id"], context.subject_id)
        self.assertIn("Newtonian Mechanics", aliases_index["lookup_keys"])
        self.assertEqual(units_index["units"][0]["unit_id"], "unit_force")
        self.assertEqual(units_index["units"][0]["linked_skill_ids"], ["skill_force"])
        self.assertIn("## Governing Relations", paths["subject_md"].read_text(encoding="utf-8"))
        self.assertIn("== Governing Relations <governing-relations>", paths["subject_typ"].read_text(encoding="utf-8"))

    def test_persist_learning_delta_round_trips_under_subject_home(self) -> None:
        subject_id = canonical_learning_subject_id("Signal Transduction")
        delta = LearningDelta(
            delta_id="delta_signal_001",
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Capture the receptor activation relation from the lesson.",
            evidence_refs=("source_signal_001",),
            proposed_units=(
                LearningUnit(
                    unit_id="unit_receptor_activation",
                    subject_id=subject_id,
                    unit_kind="relation",
                    canonical_title="Receptor Activation Triggers Signaling Cascade",
                    statement="Activated receptors initiate downstream signaling.",
                    status="proposed",
                ),
            ),
            derived_skill_ids=("skill_signal_summary",),
            document_section_ids=("definitions",),
            status="proposed",
        )

        delta_path = persist_learning_delta(self.root, delta)
        loaded = load_learning_delta(self.root, subject_id, "delta_signal_001")

        self.assertEqual(delta_path, learning_context_paths(self.root, subject_id)["deltas"] / "delta_signal_001.json")
        self.assertEqual(loaded.subject_id, subject_id)
        self.assertEqual(loaded.source_kind, "markdown")
        self.assertEqual(len(loaded.proposed_units), 1)
        self.assertEqual(loaded.proposed_units[0].canonical_title, "Receptor Activation Triggers Signaling Cascade")

    def test_persist_learning_source_writes_json_and_markdown_body(self) -> None:
        subject_id = canonical_learning_subject_id("Thermodynamics")
        source = LearningSource(
            source_id="source_thermo_001",
            subject_id=subject_id,
            source_kind="markdown",
            title="Thermodynamics Notes",
            source_ref="/tmp/thermo.md",
            media_type="text/markdown",
            section_count=3,
            body_relpath="source_thermo_001.md",
        )

        source_path = persist_learning_source(self.root, source, source_text="# Thermodynamics\n\nHeat flows.")
        loaded = load_learning_source(self.root, subject_id, "source_thermo_001")
        body_path = learning_context_paths(self.root, subject_id)["sources"] / "source_thermo_001.md"

        self.assertEqual(source_path, learning_context_paths(self.root, subject_id)["sources"] / "source_thermo_001.json")
        self.assertTrue(body_path.is_file())
        self.assertIn("Heat flows.", body_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded.title, "Thermodynamics Notes")
        self.assertEqual(loaded.section_count, 3)

    def test_apply_learning_delta_merges_units_and_marks_deprecations(self) -> None:
        subject_id = canonical_learning_subject_id("Kinematics")
        context = new_learning_context(canonical_title="Kinematics", subject_family="Physics")
        context = LearningContext(
            subject_id=context.subject_id,
            canonical_title=context.canonical_title,
            aliases=context.aliases,
            subject_family=context.subject_family,
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is rate of change of position.",
                    status="admitted",
                ),
            ),
            governance_status="draft",
        )
        delta = LearningDelta(
            delta_id="delta_kinematics_001",
            subject_id=subject_id,
            source_kind="chat",
            evidence_refs=("chat_turn_001",),
            proposed_units=(
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id=subject_id,
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is rate of change of velocity.",
                    status="admitted",
                    linked_skill_ids=("skill_acceleration_summary",),
                ),
            ),
            deprecated_unit_ids=("unit_velocity",),
            derived_skill_ids=("skill_acceleration",),
            document_section_ids=("governing-relations",),
            status="admitted",
        )

        merged = apply_learning_delta(context, delta)

        self.assertEqual(merged.governance_status, "active")
        self.assertEqual(merged.applied_delta_ids, ("delta_kinematics_001",))
        self.assertEqual(merged.linked_skill_ids, ("skill_acceleration", "skill_acceleration_summary"))
        self.assertEqual(merged.linked_source_ids, ("chat_turn_001",))
        status_by_unit_id = {unit.unit_id: unit.status for unit in merged.units}
        self.assertEqual(status_by_unit_id["unit_velocity"], "deprecated")
        self.assertEqual(status_by_unit_id["unit_acceleration"], "admitted")

    def test_list_learning_contexts_returns_compact_summaries(self) -> None:
        physics = new_learning_context(canonical_title="Physics", subject_family="Science")
        biology = new_learning_context(canonical_title="Biology", subject_family="Science")
        persist_learning_context(self.root, physics)
        persist_learning_context(self.root, biology)

        summaries = list_learning_contexts(self.root)
        self.assertEqual(
            [item["subject_id"] for item in summaries],
            [biology.subject_id, physics.subject_id],
        )
        self.assertTrue(all("unit_count" in item for item in summaries))

    def test_find_learning_context_by_lookup_matches_unique_alias(self) -> None:
        context = LearningContext(
            subject_id=canonical_learning_subject_id("Kinematics"),
            canonical_title="Kinematics",
            aliases=("Motion Notes", "Equations of Motion"),
            subject_family="Physics",
            governance_status="active",
        )
        persist_learning_context(self.root, context)

        matched = find_learning_context_by_lookup(self.root, "Motion Notes")

        self.assertIsNotNone(matched)
        assert matched is not None
        self.assertEqual(matched.subject_id, context.subject_id)
        self.assertEqual(matched.canonical_title, "Kinematics")

    def test_find_learning_context_by_lookup_returns_none_when_ambiguous(self) -> None:
        first = LearningContext(
            subject_id=canonical_learning_subject_id("Kinematics"),
            canonical_title="Kinematics",
            aliases=("Motion Notes",),
            governance_status="active",
        )
        second = LearningContext(
            subject_id=canonical_learning_subject_id("Dynamics"),
            canonical_title="Dynamics",
            aliases=("Motion Notes",),
            governance_status="active",
        )
        persist_learning_context(self.root, first)
        persist_learning_context(self.root, second)

        matched = find_learning_context_by_lookup(self.root, "Motion Notes")

        self.assertIsNone(matched)

    def test_subject_import_persistence_materializes_import_index_and_round_trips(self) -> None:
        active = new_learning_context(canonical_title="Kinematics", subject_family="Physics")
        source = new_learning_context(canonical_title="Dynamics", subject_family="Physics")
        persist_learning_context(self.root, active)
        persist_learning_context(self.root, source)

        subject_import = new_subject_import(
            active_subject_id=active.subject_id,
            active_subject_version_id=active.content_hash(),
            active_subject_title=active.canonical_title,
            source_subject_id=source.subject_id,
            source_subject_version_id=source.content_hash(),
            source_subject_title=source.canonical_title,
            import_kind="definition_support",
            imported_unit_ids=("unit_force", "unit_mass", "unit_acceleration"),
            rationale="Use dynamics definitions as bounded support while reviewing kinematics.",
        )

        import_path = persist_subject_import(self.root, subject_import)
        paths = learning_context_paths(self.root, active.subject_id)
        loaded = load_subject_import(self.root, active.subject_id, subject_import.import_id)
        listed = list_subject_imports(self.root, active.subject_id)
        imports_index = json.loads(paths["imports_index"].read_text(encoding="utf-8"))

        self.assertEqual(import_path, paths["imports"] / f"{subject_import.import_id}.json")
        self.assertTrue(paths["imports"].is_dir())
        self.assertTrue(paths["imports_index"].is_file())
        self.assertEqual(loaded.import_id, subject_import.import_id)
        self.assertEqual(loaded.source_subject_id, source.subject_id)
        self.assertEqual(loaded.import_kind, "definition_support")
        self.assertEqual(loaded.imported_unit_ids, ("unit_force", "unit_mass", "unit_acceleration"))
        self.assertEqual(len(listed), 1)
        self.assertEqual(imports_index["subject_id"], active.subject_id)
        self.assertEqual(imports_index["import_count"], 1)
        self.assertEqual(imports_index["active_import_count"], 1)
        self.assertEqual(imports_index["imported_subject_count"], 1)
        self.assertEqual(imports_index["imports"][0]["unit_count"], 3)

    def test_subject_reasoning_scope_loads_only_active_approved_imports(self) -> None:
        active = new_learning_context(canonical_title="Kinematics", subject_family="Physics")
        source = new_learning_context(canonical_title="Dynamics", subject_family="Physics")
        persist_learning_context(self.root, active)
        persist_learning_context(self.root, source)

        persist_subject_import(
            self.root,
            new_subject_import(
                active_subject_id=active.subject_id,
                active_subject_version_id=active.content_hash(),
                active_subject_title=active.canonical_title,
                source_subject_id=source.subject_id,
                source_subject_version_id=source.content_hash(),
                source_subject_title=source.canonical_title,
                import_kind="comparison",
                imported_unit_ids=("unit_force",),
                review_status="approved",
                status="active",
            ),
        )
        persist_subject_import(
            self.root,
            new_subject_import(
                active_subject_id=active.subject_id,
                active_subject_version_id=active.content_hash(),
                active_subject_title=active.canonical_title,
                source_subject_id=source.subject_id,
                source_subject_version_id=source.content_hash(),
                source_subject_title=source.canonical_title,
                import_kind="background_only",
                imported_unit_ids=("unit_energy",),
                review_status="pending",
                status="active",
            ),
        )

        scope = load_subject_reasoning_scope(self.root, active.subject_id)

        self.assertEqual(scope.active_subject_id, active.subject_id)
        self.assertEqual(scope.active_subject_version_id, active.content_hash())
        self.assertEqual(scope.active_subject_title, active.canonical_title)
        self.assertEqual(scope.global_retrieval_policy, "disabled")
        self.assertEqual(len(scope.imported_subjects), 1)
        self.assertEqual(scope.imported_subjects[0].import_kind, "comparison")


if __name__ == "__main__":
    unittest.main()
