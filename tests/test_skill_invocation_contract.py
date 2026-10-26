# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from skill_invocation_contract import (
    SkillInvocationBinding,
    SkillInvocationRequest,
    skill_invocation_request_from_artifact,
    skill_invocation_result_from_mapping,
)
from skill_schema_io import artifact_from_skill_document


class SkillInvocationContractTests(unittest.TestCase):
    def test_invocation_request_projects_declared_bindings_and_missing_inputs(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Repo Search",
                "inputs": {
                    "symbol": "required symbol to find",
                    "root": "workspace root",
                },
                "compatibility": {
                    "adapters": [
                        {"direction": "import", "format": "openai_tool", "name": "repo_search"}
                    ]
                },
            }
        )

        request = skill_invocation_request_from_artifact(
            artifact,
            semantic_unit="Find BSSCController in the repo.",
            payload={"symbol": "BSSCController"},
            missing_required_inputs=[],
            invocation_mode="llm_routed",
        )

        self.assertEqual(request.skill_title, "Repo Search")
        self.assertEqual(request.invocation_mode, "llm_routed")
        self.assertEqual(request.required_inputs, ["symbol"])
        self.assertEqual(request.bindings[0].status, "provided")
        self.assertEqual(request.bindings[1].status, "missing")
        self.assertEqual(
            {
                "skill_title": "Repo Search",
                "skill_kind": "ability",
                "executor_framework": "python3",
                "invocation_mode": "llm_routed",
                "semantic_unit": "Find BSSCController in the repo.",
                "payload": {"symbol": "BSSCController"},
                "declared_inputs": {
                    "symbol": "required symbol to find",
                    "root": "workspace root",
                },
                "declared_outputs": {"result": "JSON result"},
                "required_inputs": ["symbol"],
                "missing_required_inputs": [],
                "bindings": [
                    {
                        "name": "symbol",
                        "contract_description": "required symbol to find",
                        "status": "provided",
                        "value": "BSSCController",
                    },
                    {
                        "name": "root",
                        "contract_description": "workspace root",
                        "status": "missing",
                        "value": None,
                    },
                ],
            },
            request.to_dict(),
        )

    def test_invocation_result_prefers_result_payload(self) -> None:
        result = skill_invocation_result_from_mapping(
            {
                "status": "ok",
                "skill_title": "Repo Search",
                "answer": "src/app.py",
                "result_payload": {"matches": ["src/app.py"]},
                "nested_run_outcome": "completed",
            }
        )

        self.assertEqual(result.skill_title, "Repo Search")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.output_payload, {"matches": ["src/app.py"]})
        self.assertEqual(result.nested_run_outcome, "completed")

    def test_invocation_request_serialization_shape_remains_stable(self) -> None:
        request = SkillInvocationRequest(
            skill_title="Repo Search",
            skill_kind="ability",
            executor_framework="python3",
            invocation_mode="llm_routed",
            semantic_unit="Find BSSCController.",
            payload={"symbol": "BSSCController"},
            declared_inputs={"symbol": "required symbol"},
            declared_outputs={"matches": "matching paths"},
            required_inputs=["symbol"],
            missing_required_inputs=[],
            bindings=[
                SkillInvocationBinding(
                    name="symbol",
                    contract_description="required symbol",
                    status="provided",
                    value="BSSCController",
                )
            ],
        )

        self.assertEqual(
            request.to_dict(),
            {
                "skill_title": "Repo Search",
                "skill_kind": "ability",
                "executor_framework": "python3",
                "invocation_mode": "llm_routed",
                "semantic_unit": "Find BSSCController.",
                "payload": {"symbol": "BSSCController"},
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
        )


if __name__ == "__main__":
    unittest.main()
