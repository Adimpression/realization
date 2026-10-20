# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from learning_context import (
    LearningContext,
    LearningDelta,
    LearningDeltaOperation,
    LearningUnit,
    apply_learning_delta,
    canonical_learning_subject_id,
    load_learning_delta,
    persist_learning_delta,
)


class LearningDeltaOperationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.subject_id = canonical_learning_subject_id("Kinematics")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _unit(
        self,
        unit_id: str,
        title: str,
        *,
        unit_kind: str = "definition",
        statement: str = "",
        status: str = "admitted",
    ) -> LearningUnit:
        return LearningUnit(
            unit_id=unit_id,
            subject_id=self.subject_id,
            unit_kind=unit_kind,
            canonical_title=title,
            statement=statement or title,
            status=status,
        )

    def _context(self, *units: LearningUnit) -> LearningContext:
        return LearningContext(
            subject_id=self.subject_id,
            canonical_title="Kinematics",
            aliases=("Kinematics",),
            subject_family="Physics",
            summary="Motion and change relations.",
            units=tuple(units),
            governance_status="active" if units else "draft",
        )

    def test_learning_delta_round_trip_preserves_operations(self) -> None:
        delta = LearningDelta(
            delta_id="delta_ops_001",
            subject_id=self.subject_id,
            source_kind="manual",
            evidence_refs=("source_kinematics_001",),
            proposed_units=(
                self._unit(
                    "unit_velocity",
                    "Velocity",
                    statement="Velocity is rate of change of position.",
                ),
            ),
            operations=(
                LearningDeltaOperation(
                    operation_id="op_initiate_velocity",
                    operation_kind="initiate",
                    proposed_unit_ids=("unit_velocity",),
                    evidence_refs=("source_kinematics_001",),
                    rationale="Capture the first canonical unit.",
                ),
            ),
            status="admitted",
        )

        persist_learning_delta(self.root, delta)
        loaded = load_learning_delta(self.root, self.subject_id, "delta_ops_001")

        self.assertEqual(len(loaded.operations), 1)
        self.assertEqual(loaded.operations[0].operation_kind, "initiate")
        self.assertEqual(loaded.operations[0].proposed_unit_ids, ("unit_velocity",))
        self.assertEqual(loaded.operations[0].evidence_refs, ("source_kinematics_001",))

    def test_initiate_operation_adds_new_unit(self) -> None:
        delta = LearningDelta(
            delta_id="delta_ops_002",
            subject_id=self.subject_id,
            source_kind="manual",
            proposed_units=(
                self._unit(
                    "unit_acceleration",
                    "Acceleration",
                    unit_kind="relation",
                    statement="Acceleration is rate of change of velocity.",
                ),
            ),
            operations=(
                LearningDeltaOperation(
                    operation_id="op_initiate_acceleration",
                    operation_kind="initiate",
                    proposed_unit_ids=("unit_acceleration",),
                    evidence_refs=("source_acceleration_001",),
                ),
            ),
            status="applied",
        )

        merged = apply_learning_delta(self._context(), delta)
        unit = {item.unit_id: item for item in merged.units}["unit_acceleration"]

        self.assertEqual(unit.status, "admitted")
        self.assertEqual(unit.provenance_refs, ("source_acceleration_001",))
        self.assertEqual(merged.linked_source_ids, ("source_acceleration_001",))

    def test_append_operation_extends_existing_unit_without_replacing_identity(self) -> None:
        context = self._context(
            self._unit(
                "unit_velocity",
                "Velocity",
                statement="Velocity is rate of change of position.",
            ),
        )
        delta = LearningDelta(
            delta_id="delta_ops_003",
            subject_id=self.subject_id,
            source_kind="manual",
            operations=(
                LearningDeltaOperation(
                    operation_id="op_append_velocity",
                    operation_kind="append",
                    target_unit_ids=("unit_velocity",),
                    evidence_refs=("source_velocity_002",),
                    patch={
                        "statement_append": "It has both magnitude and direction.",
                        "aliases_add": ("Vector Velocity",),
                        "linked_skill_ids_add": ("skill_velocity_vector",),
                        "structured_fields_merge": {"quantity_type": "vector"},
                    },
                ),
            ),
            status="applied",
        )

        merged = apply_learning_delta(context, delta)
        unit = {item.unit_id: item for item in merged.units}["unit_velocity"]

        self.assertEqual(unit.unit_id, "unit_velocity")
        self.assertIn("It has both magnitude and direction.", unit.statement)
        self.assertEqual(unit.aliases, ("Vector Velocity",))
        self.assertEqual(unit.linked_skill_ids, ("skill_velocity_vector",))
        self.assertEqual(unit.structured_fields["quantity_type"], "vector")
        self.assertEqual(unit.provenance_refs, ("source_velocity_002",))

    def test_link_operation_adds_linkage_without_changing_statement(self) -> None:
        context = self._context(
            self._unit(
                "unit_acceleration",
                "Acceleration",
                unit_kind="relation",
                statement="Acceleration is rate of change of velocity.",
            ),
        )
        delta = LearningDelta(
            delta_id="delta_ops_004",
            subject_id=self.subject_id,
            source_kind="manual",
            operations=(
                LearningDeltaOperation(
                    operation_id="op_link_acceleration",
                    operation_kind="link",
                    target_unit_ids=("unit_acceleration",),
                    evidence_refs=("source_acceleration_002",),
                    patch={
                        "linked_artifact_ids_add": ("artifact_acceleration_example",),
                        "linked_section_ids_add": ("governing-relations",),
                        "metadata_merge": {"link_reason": "projection"},
                    },
                ),
            ),
            status="applied",
        )

        merged = apply_learning_delta(context, delta)
        unit = {item.unit_id: item for item in merged.units}["unit_acceleration"]

        self.assertEqual(unit.statement, "Acceleration is rate of change of velocity.")
        self.assertEqual(unit.linked_artifact_ids, ("artifact_acceleration_example",))
        self.assertEqual(unit.linked_section_ids, ("governing-relations",))
        self.assertEqual(unit.metadata["link_reason"], "projection")
        self.assertEqual(unit.provenance_refs, ("source_acceleration_002",))

    def test_replace_operation_supersedes_old_unit_and_adds_replacement(self) -> None:
        context = self._context(
            self._unit(
                "unit_speed",
                "Speed",
                statement="Speed is motion.",
            ),
        )
        replacement = self._unit(
            "unit_speed_definition",
            "Speed Definition",
            statement="Speed is the scalar rate of distance change over time.",
        )
        delta = LearningDelta(
            delta_id="delta_ops_005",
            subject_id=self.subject_id,
            source_kind="manual",
            proposed_units=(replacement,),
            operations=(
                LearningDeltaOperation(
                    operation_id="op_replace_speed",
                    operation_kind="replace",
                    target_unit_ids=("unit_speed",),
                    proposed_unit_ids=("unit_speed_definition",),
                    evidence_refs=("source_speed_003",),
                ),
            ),
            status="applied",
        )

        merged = apply_learning_delta(context, delta)
        by_id = {item.unit_id: item for item in merged.units}

        self.assertEqual(by_id["unit_speed"].status, "superseded")
        self.assertEqual(by_id["unit_speed_definition"].status, "admitted")
        self.assertEqual(by_id["unit_speed_definition"].provenance_refs, ("source_speed_003",))

    def test_remove_and_restore_operations_update_unit_lifecycle_without_deleting_history(self) -> None:
        context = self._context(
            self._unit(
                "unit_displacement",
                "Displacement",
                statement="Displacement is net position change.",
            ),
        )
        removed = apply_learning_delta(
            context,
            LearningDelta(
                delta_id="delta_ops_006",
                subject_id=self.subject_id,
                source_kind="manual",
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_remove_displacement",
                        operation_kind="remove",
                        target_unit_ids=("unit_displacement",),
                        evidence_refs=("source_displacement_001",),
                    ),
                ),
                status="applied",
            ),
        )
        restored = apply_learning_delta(
            removed,
            LearningDelta(
                delta_id="delta_ops_007",
                subject_id=self.subject_id,
                source_kind="manual",
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_restore_displacement",
                        operation_kind="restore",
                        target_unit_ids=("unit_displacement",),
                        evidence_refs=("source_displacement_002",),
                    ),
                ),
                status="applied",
            ),
        )

        self.assertEqual({item.unit_id: item for item in removed.units}["unit_displacement"].status, "deprecated")
        restored_unit = {item.unit_id: item for item in restored.units}["unit_displacement"]
        self.assertEqual(restored_unit.status, "admitted")
        self.assertEqual(
            restored_unit.provenance_refs,
            ("source_displacement_001", "source_displacement_002"),
        )

    def test_improve_and_reject_operations_handle_existing_and_proposed_units(self) -> None:
        context = self._context(
            self._unit(
                "unit_time",
                "Time",
                statement="Time is duration.",
            ),
        )
        improved = apply_learning_delta(
            context,
            LearningDelta(
                delta_id="delta_ops_008",
                subject_id=self.subject_id,
                source_kind="manual",
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_improve_time",
                        operation_kind="improve",
                        target_unit_ids=("unit_time",),
                        evidence_refs=("source_time_002",),
                        patch={
                            "statement": "Time is a scalar measure of duration and ordering of events.",
                            "structured_fields_merge": {"quantity_type": "scalar"},
                        },
                    ),
                ),
                status="applied",
            ),
        )
        rejected = apply_learning_delta(
            improved,
            LearningDelta(
                delta_id="delta_ops_009",
                subject_id=self.subject_id,
                source_kind="manual",
                proposed_units=(
                    self._unit(
                        "unit_bad_claim",
                        "Bad Claim",
                        statement="Time has two independent spatial axes.",
                        status="proposed",
                    ),
                ),
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_reject_bad_claim",
                        operation_kind="reject",
                        proposed_unit_ids=("unit_bad_claim",),
                        evidence_refs=("source_time_review_001",),
                    ),
                ),
                status="applied",
            ),
        )

        improved_unit = {item.unit_id: item for item in improved.units}["unit_time"]
        rejected_unit = {item.unit_id: item for item in rejected.units}["unit_bad_claim"]

        self.assertEqual(
            improved_unit.statement,
            "Time is a scalar measure of duration and ordering of events.",
        )
        self.assertEqual(improved_unit.structured_fields["quantity_type"], "scalar")
        self.assertEqual(rejected_unit.status, "rejected")
        self.assertEqual(rejected_unit.provenance_refs, ("source_time_review_001",))

    def test_split_and_merge_operations_preserve_supersession_history(self) -> None:
        context = self._context(
            self._unit(
                "unit_motion_measures",
                "Motion Measures",
                statement="Motion is described by several related measures.",
            ),
        )
        split = apply_learning_delta(
            context,
            LearningDelta(
                delta_id="delta_ops_010",
                subject_id=self.subject_id,
                source_kind="manual",
                proposed_units=(
                    self._unit(
                        "unit_distance",
                        "Distance",
                        statement="Distance is total path length traveled.",
                    ),
                    self._unit(
                        "unit_displacement",
                        "Displacement",
                        statement="Displacement is net position change.",
                    ),
                ),
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_split_motion_measures",
                        operation_kind="split",
                        target_unit_ids=("unit_motion_measures",),
                        proposed_unit_ids=("unit_distance", "unit_displacement"),
                        evidence_refs=("source_motion_010",),
                    ),
                ),
                status="applied",
            ),
        )
        merged = apply_learning_delta(
            split,
            LearningDelta(
                delta_id="delta_ops_011",
                subject_id=self.subject_id,
                source_kind="manual",
                proposed_units=(
                    self._unit(
                        "unit_path_change_pair",
                        "Path Change Pair",
                        statement="Distance and displacement jointly describe total path and net change.",
                    ),
                ),
                operations=(
                    LearningDeltaOperation(
                        operation_id="op_merge_path_change_pair",
                        operation_kind="merge",
                        target_unit_ids=("unit_distance", "unit_displacement"),
                        proposed_unit_ids=("unit_path_change_pair",),
                        evidence_refs=("source_motion_011",),
                    ),
                ),
                status="applied",
            ),
        )

        split_units = {item.unit_id: item for item in split.units}
        merged_units = {item.unit_id: item for item in merged.units}

        self.assertEqual(split_units["unit_motion_measures"].status, "superseded")
        self.assertEqual(split_units["unit_distance"].status, "admitted")
        self.assertEqual(split_units["unit_displacement"].status, "admitted")
        self.assertEqual(merged_units["unit_distance"].status, "superseded")
        self.assertEqual(merged_units["unit_displacement"].status, "superseded")
        self.assertEqual(merged_units["unit_path_change_pair"].status, "admitted")


if __name__ == "__main__":
    unittest.main()
