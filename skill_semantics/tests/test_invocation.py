from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from realized_skill_semantics.invocation import (
    SkillInvocationBinding,
    SkillInvocationRequest,
    SkillInvocationResult,
    required_skill_input_names,
    skill_invocation_result_from_mapping,
)


class SkillInvocationTests(unittest.TestCase):
    def test_request_has_the_stable_json_safe_shape(self) -> None:
        request = SkillInvocationRequest(
            skill_title="Repo Search",
            skill_kind="ability",
            executor_framework="python3",
            invocation_mode="llm_routed",
            semantic_unit="Find BSSCController.",
            payload={"symbol": "BSSCController", "rank": (1, 2)},
            declared_inputs={"symbol": "required symbol"},
            declared_outputs={"matches": "matching paths"},
            required_inputs=["symbol"],
            missing_required_inputs=[],
            bindings=[
                SkillInvocationBinding(
                    name="symbol",
                    contract_description="required symbol",
                    status="provided",
                    value=b"BSSCController",
                )
            ],
        )

        self.assertEqual(
            {
                "skill_title": "Repo Search",
                "skill_kind": "ability",
                "executor_framework": "python3",
                "invocation_mode": "llm_routed",
                "semantic_unit": "Find BSSCController.",
                "payload": {"symbol": "BSSCController", "rank": [1, 2]},
                "declared_inputs": {"symbol": "required symbol"},
                "declared_outputs": {"matches": "matching paths"},
                "required_inputs": ["symbol"],
                "missing_required_inputs": [],
                "bindings": [
                    {
                        "name": "symbol",
                        "contract_description": "required symbol",
                        "status": "provided",
                        "value": "BSSCController",
                    }
                ],
            },
            request.to_dict(),
        )

    def test_invocation_records_are_frozen(self) -> None:
        binding = SkillInvocationBinding("path", "required", "provided", "/tmp/a")
        result = SkillInvocationResult("Read", "ok", "text", "", {}, "completed")

        with self.assertRaises(FrozenInstanceError):
            binding.status = "missing"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.status = "error"  # type: ignore[misc]

    def test_required_inputs_preserve_order_and_current_description_rules(self) -> None:
        self.assertEqual(
            ["symbol", "blank name", "case", "negated"],
            required_skill_input_names(
                {
                    " symbol ": "required symbol to find",
                    "root": "workspace root",
                    "blank\nname": "",
                    "optional": "OPTIONAL",
                    "case": "Required value",
                    "negated": "not required by this mode",
                    "": "required but unnamed",
                }
            ),
        )

    def test_required_inputs_accept_mixed_mapping_values_without_coercion_drift(self) -> None:
        self.assertEqual(
            [],
            required_skill_input_names(
                {"zero": 0, "false": False, "none": None}
            ),
        )

    def test_result_mapping_preserves_text_cleanup_and_complete_shape(self) -> None:
        result = skill_invocation_result_from_mapping(
            {
                "skill_title": " Demo\nSkill ",
                "status": " ok\t",
                "answer": 0,
                "error": None,
                "result_payload": {"matches": ("src/app.py",)},
                "nested_run_outcome": " completed\n",
            }
        )

        self.assertEqual(
            {
                "skill_title": "Demo Skill",
                "status": "ok",
                "answer": "",
                "error": "",
                "output_payload": {"matches": ["src/app.py"]},
                "nested_run_outcome": "completed",
            },
            result.to_dict(),
        )

    def test_result_payload_precedence_falls_back_only_for_none(self) -> None:
        cases = (
            ({"result_payload": {"source": "result_payload"}, "parsed_output": {"source": "parsed"}}, {"source": "result_payload"}),
            ({"result_payload": None, "parsed_output": {"source": "parsed"}, "result": {"source": "result"}}, {"source": "parsed"}),
            ({"result_payload": None, "parsed_output": None, "result": {"source": "result"}}, {"source": "result"}),
            ({"result_payload": {}, "parsed_output": {"source": "parsed"}}, {}),
            ({"result_payload": False, "parsed_output": {"source": "parsed"}}, False),
        )

        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(
                    expected,
                    skill_invocation_result_from_mapping(source).output_payload,
                )


if __name__ == "__main__":
    unittest.main()
