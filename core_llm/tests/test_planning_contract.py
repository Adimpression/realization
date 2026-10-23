from __future__ import annotations

import unittest

from realized_core_llm import (
    PLANNING_PROMPT_VERSION,
    PLANNING_SCHEMA_VERSION,
    ConversationOperation,
    ConversationPlanningContext,
    ConversationRenderContext,
    JsonConversationPlanner,
    JsonConversationRenderer,
)


class PlanningContractTests(unittest.TestCase):
    def test_planner_exposes_versioned_context_schema_and_result(self) -> None:
        captured: dict[str, object] = {}

        def propose(prompt, schema):
            captured["prompt"] = prompt
            captured["schema"] = schema
            return {
                "schema_version": PLANNING_SCHEMA_VERSION,
                "operation": "start",
            }

        result = JsonConversationPlanner(propose).propose(
            ConversationPlanningContext(
                prompt="Begin a plan.",
                scope_id="scope-1",
            )
        )

        schema = captured["schema"]
        assert isinstance(schema, dict)
        self.assertEqual("object", schema["type"])
        self.assertFalse(schema["additionalProperties"])
        properties = schema["properties"]
        self.assertEqual(
            [PLANNING_SCHEMA_VERSION],
            properties["schema_version"]["enum"],
        )
        self.assertEqual(
            {item.value for item in ConversationOperation},
            set(properties["operation"]["enum"]),
        )
        for name in (
            "achieved_items",
            "non_achieved_items",
            "introduced_items",
        ):
            self.assertEqual("object", properties[name]["items"]["type"])
            self.assertEqual(
                ["selector", "kind", "value", "text"],
                properties[name]["items"]["required"],
            )
        self.assertEqual("object", properties["corrections"]["items"]["type"])
        self.assertIn(
            f'"planning_schema_version": "{PLANNING_SCHEMA_VERSION}"',
            captured["prompt"],
        )
        self.assertIn(
            "at least one of value or text must be non-empty",
            captured["prompt"],
        )
        self.assertIn(
            "Changing blue to green or Friday to Monday is correction",
            captured["prompt"],
        )
        self.assertIn(
            "Set the unresolved audience to city officials",
            captured["prompt"],
        )
        self.assertIn(
            "It is not augment merely because the value is newly supplied",
            captured["prompt"],
        )
        self.assertIn(
            "changing a brief into a launch checklist",
            captured["prompt"],
        )
        self.assertIn("Operation decision gate", captured["prompt"])
        self.assertIn(
            "'The project is Cedar' requires an achieved item",
            captured["prompt"],
        )
        self.assertIn(
            "undecided, unknown, unspecified, unresolved, pending, TBD",
            captured["prompt"],
        )
        self.assertIn(
            "Explicit undo, reverse, or restore requests use reverse",
            captured["prompt"],
        )
        self.assertIn(
            "'Undo my last correction' uses reversal_selector 'last correction'",
            captured["prompt"],
        )
        self.assertIn(
            "'Prepare an executive version' means branch",
            captured["prompt"],
        )
        self.assertIn(
            "Branch creates a new alternate line",
            captured["prompt"],
        )
        self.assertIn(
            "already names the bound existing branch",
            captured["prompt"],
        )
        self.assertIn(
            "A selector may occur at most once across achieved_items",
            captured["prompt"],
        )
        self.assertIn(
            "Do not copy current state into semantic arrays",
            captured["prompt"],
        )
        self.assertIn(
            "Exact augmentation example",
            captured["prompt"],
        )
        self.assertIn(
            "Do not copy project, color, deadline, or audience",
            captured["prompt"],
        )
        self.assertIn(
            "Merely seeing an active hold does not make another request",
            captured["prompt"],
        )
        self.assertIn(
            "The current state is context, not a request to repeat or restart",
            captured["prompt"],
        )
        self.assertIn(
            "Separately, start a new objective: plan a weekend hiking trip",
            captured["prompt"],
        )
        self.assertIn(
            "choosing identity from semantic similarity or dissimilarity",
            captured["prompt"],
        )
        self.assertIn(
            "'Instead of a brief, create a launch checklist for Cedar'",
            captured["prompt"],
        )
        self.assertIn(
            "Do not infer applicability from plausibility",
            captured["prompt"],
        )
        self.assertIn(
            "Keep Monday and the budget summary",
            captured["prompt"],
        )
        self.assertIn(
            "resolved_applicability_selectors",
            captured["prompt"],
        )
        self.assertIn(
            "remains non-achieved",
            properties["resolved_applicability_selectors"]["description"],
        )
        self.assertIn(
            "Current achieved and non-achieved semantic items are authoritative",
            captured["prompt"],
        )
        self.assertIn(
            "Keep required_outcome as a stable completion criterion",
            captured["prompt"],
        )
        self.assertIn(
            "an explicitly bound interrupted-attempt resume",
            properties["operation"]["description"],
        )
        self.assertIn(
            "Explicit undo or restore requests are reverse",
            properties["operation"]["description"],
        )
        self.assertIn(
            "absence markers such as undecided",
            properties["achieved_items"]["items"]["properties"]["value"][
                "description"
            ],
        )
        self.assertIn(
            "Treat undecided, unknown, unspecified, unresolved, pending, TBD",
            properties["non_achieved_items"]["description"],
        )
        self.assertIn(
            "Preparing an executive or technical version",
            properties["target_branch"]["description"],
        )
        self.assertEqual(ConversationOperation.START, result.proposal.operation)
        self.assertEqual(PLANNING_SCHEMA_VERSION, result.schema_version)
        self.assertEqual(PLANNING_PROMPT_VERSION, result.prompt_version)

    def test_planning_context_exposes_only_interruption_availability(self) -> None:
        payload = ConversationPlanningContext(
            prompt="Resume without the interrupted candidate.",
            scope_id="scope-1",
            parent_run_id="run-1",
            parent_identity={"revision_id": "revision-1"},
            interrupted_attempt_available=True,
        ).public_payload()

        self.assertIs(True, payload["interrupted_attempt_available"])
        self.assertNotIn("source_attempt_id", payload)

    def test_planning_context_hides_controller_private_holds(self) -> None:
        public_requirement = {
            "item_id": "requirement-audience",
            "kind": "requirement",
            "payload": {
                "semantic_key": "audience",
                "text": "Audience is unresolved.",
            },
        }
        payload = ConversationPlanningContext(
            prompt="Set the audience to city officials.",
            scope_id="scope-1",
            parent_run_id="run-1",
            parent_identity={"revision_id": "revision-1"},
            current_state={
                "achieved": [],
                "non_achievedness": [public_requirement],
                "holds": [
                    {
                        "hold_id": "hold-audience",
                        "unresolved_semantic_object": {
                            "item_id": "requirement-audience"
                        },
                        "resume_predicate": {"kind": "supplied_value"},
                    },
                    {
                        "hold_id": "engine:hold:private-frontier",
                        "unresolved_semantic_object": {
                            "item_id": "engine:node:private-frontier"
                        },
                        "resume_predicate": {"kind": "resume_signal"},
                    },
                ],
            },
        ).public_payload()

        self.assertEqual(
            ["hold-audience"],
            [hold["hold_id"] for hold in payload["active_holds"]],
        )

    def test_unsupported_planning_schema_is_explicitly_unresolved(self) -> None:
        result = JsonConversationPlanner(
            lambda _prompt, _schema: {
                "schema_version": "future",
                "operation": "start",
            }
        ).propose(
            ConversationPlanningContext(
                prompt="Begin a plan.",
                scope_id="scope-1",
            )
        )

        self.assertIn(
            "unsupported planning schema version: future",
            result.proposal.unresolved_interpretation,
        )

    def test_renderer_shape_contains_no_answer_example_to_copy(self) -> None:
        captured: dict[str, object] = {}

        def propose(prompt, schema):
            captured["prompt"] = prompt
            captured["schema"] = schema
            return {"answer": "Cedar remains governed."}

        result = JsonConversationRenderer(propose).render(
            ConversationRenderContext(
                prompt="Summarize Cedar.",
                operation=ConversationOperation.EXPLAIN,
                current_state={},
                path=(),
                structured_result={},
                default_text="fallback",
            )
        )

        schema = captured["schema"]
        assert isinstance(schema, dict)
        self.assertEqual("RealizedConversationRendering", schema["title"])
        self.assertEqual(["answer"], schema["required"])
        self.assertEqual("Cedar remains governed.", result.text)


if __name__ == "__main__":
    unittest.main()
