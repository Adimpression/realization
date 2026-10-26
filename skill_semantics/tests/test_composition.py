from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, fields
import unittest

from realized_skill_semantics.composition import (
    SkillBindingDiagnostic,
    SkillCompositionBinding,
    SkillCompositionCandidate,
    SkillCompositionCondition,
    SkillCompositionMapper,
    SkillCompositionPlanAnalysis,
    SkillCompositionStep,
    SkillConditionDiagnostic,
)
from realized_skill_semantics.ir import CanonicalSkillIR


def _canonical_ir() -> CanonicalSkillIR:
    return CanonicalSkillIR(
        artifact_id="skill-1",
        title="Portable Skill",
        schema="bssc_skill.v2",
        kind="ability",
        declaration={},
        lifecycle={},
        runtime_package_reference={},
        normalization={},
        aliases=[],
        family={},
        compatibility={},
        hosting_metadata={},
    )


class SkillCompositionValueTests(unittest.TestCase):
    def test_public_records_preserve_field_order_and_defaults(self) -> None:
        expected = {
            SkillCompositionMapper: ["kind", "field"],
            SkillCompositionBinding: [
                "target_region",
                "target_path",
                "source_step_id",
                "source_region",
                "source_path",
                "source_root_name",
                "source_root_region",
                "constant_value",
                "mapper",
                "mapper_kind",
            ],
            SkillCompositionCondition: [
                "source_step_id",
                "source_region",
                "source_path",
                "operator",
                "expected_value",
            ],
            SkillCompositionStep: [
                "step_id",
                "skill",
                "bindings",
                "run_if",
                "iterate_until",
                "branch_label",
            ],
            SkillBindingDiagnostic: [
                "step_id",
                "target_region",
                "target_path",
                "status",
                "source_kind",
                "source_step_id",
                "source_region",
                "source_path",
                "source_root_name",
                "source_root_region",
                "mapper_kind",
                "reason",
            ],
            SkillConditionDiagnostic: [
                "step_id",
                "status",
                "source_step_id",
                "source_region",
                "source_path",
                "operator",
                "reason",
            ],
            SkillCompositionCandidate: [
                "source_region",
                "source_path",
                "target_region",
                "target_path",
                "status",
                "reason",
                "mapper_kind",
            ],
            SkillCompositionPlanAnalysis: [
                "steps",
                "plan_authorities",
                "blocked",
                "unresolved_targets",
            ],
        }

        for record, field_names in expected.items():
            with self.subTest(record=record.__name__):
                self.assertEqual(field_names, [field.name for field in fields(record)])
                self.assertTrue(record.__dataclass_params__.frozen)

        self.assertEqual(SkillCompositionMapper(), SkillCompositionMapper("identity", ""))
        self.assertEqual(
            SkillCompositionBinding("a", "/a/value"),
            SkillCompositionBinding(
                "a",
                "/a/value",
                "",
                "",
                "",
                "",
                "",
                None,
                None,
                "identity",
            ),
        )
        self.assertEqual(
            SkillCompositionCondition("one", "d", "/d/value"),
            SkillCompositionCondition("one", "d", "/d/value", "equals", None),
        )

    def test_mapping_constructors_preserve_normalization_and_falsey_values(self) -> None:
        mapper = SkillCompositionMapper.from_dict(
            {"kind": " project_field\n", "source_key": " text\t"}
        )
        binding = SkillCompositionBinding.from_dict(
            {
                "target_region": " a ",
                "target_path": " /a/value\n",
                "constant_value": False,
                "mapper": {"kind": " project_field ", "field": " text\n"},
                "mapper_kind": " first_item ",
            }
        )
        condition = SkillCompositionCondition.from_dict(
            {
                "source_step_id": " prior\nstep ",
                "source_region": " d ",
                "source_path": " /d/result\t",
                "operator": " not_equals ",
                "expected_value": 0,
            }
        )

        self.assertEqual(SkillCompositionMapper("project_field", "text"), mapper)
        self.assertEqual(False, binding.constant_value)
        self.assertEqual(SkillCompositionMapper("project_field", "text"), binding.mapper)
        self.assertEqual("first_item", binding.mapper_kind)
        self.assertEqual("prior step", condition.source_step_id)
        self.assertEqual(0, condition.expected_value)

    def test_pre_cut_mapping_contract_remains_exact(self) -> None:
        mapper = SkillCompositionMapper.from_dict(
            {
                "kind": "\x00 project\nfield \x7f",
                "source_key": " payload\tvalue ",
            }
        )
        binding = SkillCompositionBinding.from_dict(
            {
                "target_region": " a' ",
                "target_path": " /a'/items/0 ",
                "source_step_id": " prior\nstep ",
                "source_region": " d' ",
                "source_path": " /d'/items/0 ",
                "source_root_name": " input\troot ",
                "source_root_region": " c ",
                "constant_value": False,
                "mapper": {"kind": " project_field ", "field": " text\nvalue "},
                "mapper_kind": "",
            }
        )
        condition = SkillCompositionCondition.from_dict(
            {
                "source_step_id": None,
                "source_region": None,
                "source_path": None,
                "operator": None,
                "expected_value": 0,
            }
        )
        step = SkillCompositionStep.from_dict(
            {
                "step_id": "\x00 next\nstep \x7f",
                "skill": {"title": "Portable"},
                "bindings": [
                    {
                        "target_region": "a",
                        "target_path": "/a/flag",
                        "constant_value": False,
                    }
                ],
                "run_if": [
                    {
                        "source_step_id": "prior",
                        "source_region": "d",
                        "source_path": "/d/count",
                        "expected_value": 0,
                    }
                ],
                "branch_label": " else\nbranch ",
            }
        )

        self.assertEqual({"kind": "project field", "field": "payload value"}, asdict(mapper))
        self.assertEqual(
            {
                "target_region": "a'",
                "target_path": "/a'/items/0",
                "source_step_id": "prior step",
                "source_region": "d'",
                "source_path": "/d'/items/0",
                "source_root_name": "input root",
                "source_root_region": "c",
                "constant_value": False,
                "mapper": {"kind": "project_field", "field": "text value"},
                "mapper_kind": "identity",
            },
            asdict(binding),
        )
        self.assertEqual(
            {
                "source_step_id": "None",
                "source_region": "None",
                "source_path": "None",
                "operator": "None",
                "expected_value": 0,
            },
            asdict(condition),
        )
        self.assertEqual(
            {
                "step_id": "next step",
                "skill": {"title": "Portable"},
                "bindings": (
                    {
                        "target_region": "a",
                        "target_path": "/a/flag",
                        "source_step_id": "",
                        "source_region": "",
                        "source_path": "",
                        "source_root_name": "",
                        "source_root_region": "",
                        "constant_value": False,
                        "mapper": None,
                        "mapper_kind": "identity",
                    },
                ),
                "run_if": (
                    {
                        "source_step_id": "prior",
                        "source_region": "d",
                        "source_path": "/d/count",
                        "operator": "equals",
                        "expected_value": 0,
                    },
                ),
                "iterate_until": (),
                "branch_label": "else branch",
            },
            asdict(step),
        )

    def test_step_constructor_normalizes_nested_records_and_preserves_instances(self) -> None:
        existing_binding = SkillCompositionBinding("a", "/a/existing")
        existing_condition = SkillCompositionCondition("one", "d", "/d/existing")
        step = SkillCompositionStep.from_dict(
            {
                "step_id": " next\nstep ",
                "skill": {"title": "Portable"},
                "bindings": [
                    existing_binding,
                    {"target_region": "a", "target_path": "/a/value"},
                ],
                "run_if": [existing_condition],
                "iterate_until": [
                    {
                        "source_step_id": "next step",
                        "source_region": "d",
                        "source_path": "/d/done",
                        "operator": "equals",
                        "expected_value": True,
                    }
                ],
                "branch_label": " else\nbranch ",
            }
        )

        self.assertEqual("next step", step.step_id)
        self.assertEqual("else branch", step.branch_label)
        self.assertIs(existing_binding, step.bindings[0])
        self.assertIs(existing_condition, step.run_if[0])
        self.assertIsInstance(step.bindings[1], SkillCompositionBinding)
        self.assertIsInstance(step.iterate_until[0], SkillCompositionCondition)
        self.assertIsInstance(
            SkillCompositionStep("canonical", _canonical_ir()).skill,
            CanonicalSkillIR,
        )

    def test_mapping_constructors_reject_non_mapping_payloads(self) -> None:
        constructors = (
            (SkillCompositionMapper.from_dict, "SkillCompositionMapper"),
            (SkillCompositionBinding.from_dict, "SkillCompositionBinding"),
            (SkillCompositionCondition.from_dict, "SkillCompositionCondition"),
            (SkillCompositionStep.from_dict, "SkillCompositionStep"),
        )

        for constructor, name in constructors:
            with self.subTest(constructor=name):
                with self.assertRaises(TypeError) as context:
                    constructor([])  # type: ignore[arg-type]
                self.assertEqual(
                    f"{name}.from_dict requires a mapping payload.",
                    str(context.exception),
                )

    def test_records_are_frozen(self) -> None:
        records = (
            SkillCompositionMapper(),
            SkillCompositionBinding("a", "/a/value"),
            SkillCompositionCondition("one", "d", "/d/result"),
            SkillCompositionStep("one", {"title": "Portable"}),
            SkillBindingDiagnostic("one", "a", "/a/value", "exact", "root"),
            SkillConditionDiagnostic("one", "exact", "prior", "d", "/d/result", "equals"),
            SkillCompositionCandidate("d", "/d/result", "a", "/a/value", "exact", "match"),
            SkillCompositionPlanAnalysis([], [], False, []),
        )

        for record in records:
            with self.subTest(record=type(record).__name__):
                with self.assertRaises(FrozenInstanceError):
                    record.__setattr__(fields(record)[0].name, "changed")

    def test_analysis_projection_is_json_safe_and_complete(self) -> None:
        analysis = SkillCompositionPlanAnalysis(
            steps=[{"tuple": (1, 2)}],
            plan_authorities=["write", "read"],
            blocked=False,
            unresolved_targets=[{"value": b"x"}],
        )

        self.assertEqual(
            {
                "steps": [{"tuple": [1, 2]}],
                "plan_authorities": ["write", "read"],
                "blocked": False,
                "unresolved_targets": [{"value": "x"}],
            },
            analysis.to_dict(),
        )


if __name__ == "__main__":
    unittest.main()
