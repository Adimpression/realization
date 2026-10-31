# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from realized_core_engine.fallback_not_generation import fallback_not_elaboration_for_text
from realized_core_engine.non_achievedness_normalization import normalize_not_elaboration_payload


class NotElaborationSchemaTests(unittest.TestCase):
    def test_fallback_not_elaboration_carries_richer_remainder_fields(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing fallback not elaboration carries richer remainder fields.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_fallback_not_elaboration_carries_richer_remainder_fields()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = fallback_not_elaboration_for_text(
            "I have 2 tablets in my hand, 10 mg or 100 mg. What should I do next?"
        )

        for key in (
            "intended_object",
            "success_criteria",
            "actual_realization",
            "missing_components",
            "distorted_components",
            "misalignment_types",
            "origin_layers",
            "degree",
            "remainder_shapes",
            "why_it_matters",
            "minimal_repair",
            "full_repair",
        ):
            self.assertIn(key, payload)

        self.assertEqual(payload["degree"], "dominant")
        self.assertIn("specification", payload["misalignment_types"])
        self.assertIn("epistemic", payload["misalignment_types"])
        self.assertIn("prompt", payload["origin_layers"])
        self.assertIn("knowledge", payload["origin_layers"])
        self.assertIn("underdetermined", payload["remainder_shapes"])
        self.assertIn("blocked", payload["remainder_shapes"])
        self.assertTrue(payload["minimal_repair"])
        self.assertTrue(payload["full_repair"])

    def test_normalize_not_elaboration_payload_normalizes_enum_like_fields(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing normalize not elaboration payload normalizes enum like fields.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_normalize_not_elaboration_payload_normalizes_enum_like_fields()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        normalized = normalize_not_elaboration_payload(
            "What should I do next?",
            {
                "encountered_not": "Decision About Next Step",
                "goal": "What should I do next?",
                "misalignment_types": ["spec", "truth", "faithfulness"],
                "origin_layers": ["prompt_originated", "knowledge_originated", "ontology"],
                "degree": "major",
                "remainder_shapes": ["ambiguous", "wrong", "noise"],
                "minimal_repair": ["Confirm the decisive fact."],
            },
        )

        self.assertEqual(
            normalized["misalignment_types"],
            ["specification", "epistemic", "fidelity"],
        )
        self.assertEqual(
            normalized["origin_layers"],
            ["prompt", "knowledge", "ontological"],
        )
        self.assertEqual(normalized["degree"], "dominant")
        self.assertEqual(
            normalized["remainder_shapes"],
            ["underdetermined", "distorted", "overgenerated"],
        )
        self.assertTrue(normalized["actual_realization"])
        self.assertTrue(normalized["full_repair"])

    def test_normalize_not_elaboration_payload_keeps_repair_terms_in_lookup_keys(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing normalize not elaboration payload keeps repair terms in lookup keys.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_normalize_not_elaboration_payload_keeps_repair_terms_in_lookup_keys()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        normalized = normalize_not_elaboration_payload(
            "I cannot tell which option is correct. What should I do next?",
            {
                "minimal_repair": ["Confirm the exact label before acting."],
                "why_it_matters": ["Different alternatives lead to different next steps."],
            },
        )

        lookup_keys = set(normalized["lookup_keys"])
        self.assertTrue(any("confirm exact" in key or "exact label" in key for key in lookup_keys))
        self.assertTrue(any("different alternative" in key or "different next step" in key for key in lookup_keys))


if __name__ == "__main__":
    unittest.main()
