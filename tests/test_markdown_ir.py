# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest
from pathlib import Path

from realized_core_semantics.markdown import (
    bounded_markdown_encounter_prompt_view,
    bounded_markdown_learning_prompt_view,
    markdown_declared_contract_from_encounter,
    markdown_caller_facing_question,
    markdown_direct_expression_mapping,
    markdown_learning_encounter_view,
    parse_markdown_document_ir,
)


ROOT = Path(__file__).resolve().parent.parent
PYTHAGOREAN_SOURCE = ROOT / "GAIN_PYTHOGOREAN_THEORM.md"
if not PYTHAGOREAN_SOURCE.exists():
    PYTHAGOREAN_SOURCE = ROOT / "trials" / "GAIN_PYTHOGOREAN_THEORM.md"
CHEMISTRY_ROOT = ROOT / "trials" / "chemistry"


class MarkdownIRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling setUpClass.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `setUpClass()`
            Output: None

        Args:
            cls: Bound class used to construct or inspect class-level behavior.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        text = PYTHAGOREAN_SOURCE.read_text()
        document = parse_markdown_document_ir(text, source_path=str(PYTHAGOREAN_SOURCE))
        encounters = markdown_learning_encounter_view(document)
        cls.by_heading = {
            str(encounter.get("heading", "")).strip(): encounter
            for encounter in encounters
        }

    def test_declared_contract_is_extracted_from_primary_executable_section(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing declared contract is extracted from primary executable section.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_declared_contract_is_extracted_from_primary_executable_section()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        encounter = self.by_heading["2. The core rule"]
        output_field, input_fields = markdown_declared_contract_from_encounter(encounter)
        self.assertEqual(output_field, "c")
        self.assertEqual(input_fields, ["a", "b"])

    def test_direct_expression_mapping_prefers_explicit_executable_direction(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing direct expression mapping prefers explicit executable direction.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_expression_mapping_prefers_explicit_executable_direction()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        encounter = self.by_heading["2. The core rule"]
        output_field, input_fields, expression = markdown_direct_expression_mapping(encounter)
        self.assertEqual(output_field, "c")
        self.assertEqual(input_fields, ["a", "b"])
        self.assertIn("a ** 2", expression)
        self.assertIn("b ** 2", expression)
        self.assertIn("0.5", expression)

    def test_equal_side_special_case_is_still_extracted_correctly(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing equal side special case is still extracted correctly.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_equal_side_special_case_is_still_extracted_correctly()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        encounter = self.by_heading["5. Equal-side special case"]
        output_field, input_fields, expression = markdown_direct_expression_mapping(encounter)
        self.assertEqual(output_field, "c")
        self.assertEqual(input_fields, ["s"])
        self.assertIn("s", expression)

    def test_caller_facing_question_prefers_family_reference_for_colon_headings(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing caller facing question prefers family reference for colon headings.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_caller_facing_question_prefers_family_reference_for_colon_headings()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        question = markdown_caller_facing_question("Newton's Laws of Motion", "First Law: Law of Inertia")
        self.assertEqual(question, "What is the first law in Newton's Laws of Motion?")

    def test_bounded_learning_prompt_view_compacts_cluster_text(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing bounded learning prompt view compacts cluster text.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bounded_learning_prompt_view_compacts_cluster_text()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Example

Intro paragraph that is intentionally long and repetitive so the compact prompt view has something to trim and summarize instead of forwarding everything verbatim into the learning prompt for the model.

## Section One

This is the first paragraph and it is also intentionally verbose so it exceeds the compact-fragment target and gets trimmed.

This is the second paragraph and should be omitted from the compact prompt view.

* first bullet with some extra descriptive wording
* second bullet with some extra descriptive wording
* third bullet with some extra descriptive wording
* fourth bullet that should be omitted
"""
        document = parse_markdown_document_ir(markdown, source_path="example.md")
        view = bounded_markdown_learning_prompt_view(document, max_clusters=1)
        self.assertEqual(view["cluster_count"], 1)
        cluster = view["clusters"][0]
        self.assertLessEqual(len(cluster["paragraph_fragments"]), 1)
        self.assertLessEqual(len(cluster["bullet_fragments"]), 3)
        self.assertGreaterEqual(cluster["omitted"]["paragraphs"], 1)
        self.assertGreaterEqual(cluster["omitted"]["bullets"], 1)

    def test_bounded_encounter_prompt_view_compacts_encounter_records(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing bounded encounter prompt view compacts encounter records.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bounded_encounter_prompt_view_compacts_encounter_records()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Example

## Compute Value

Use the following relation to compute the output.

* input: a
* input: b
* output: c
* extra bullet one
* extra bullet two

$$
c = a + b
$$
"""
        document = parse_markdown_document_ir(markdown, source_path="example.md")
        view = bounded_markdown_encounter_prompt_view(document, max_encounters=1)
        self.assertEqual(view["encounter_count"], 1)
        encounter = view["encounters"][0]
        self.assertTrue(encounter["equation_bearing"])
        self.assertLessEqual(len(encounter["paragraph_fragments"]), 1)
        self.assertLessEqual(len(encounter["bullet_fragments"]), 3)
        self.assertLessEqual(len(encounter["equation_fragments"]), 2)

    def test_chemistry_particles_from_moles_keeps_case_sensitive_input_symbols(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that chemistry equations do not lose a lower-case input like `n` just because the output is `N`.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_chemistry_particles_from_moles_keeps_case_sensitive_input_symbols()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        source = CHEMISTRY_ROOT / "02_LEARN_CHEMISTRY_RELATIONS_MOLE.md"
        document = parse_markdown_document_ir(source.read_text(), source_path=str(source))
        encounter = next(
            item
            for item in markdown_learning_encounter_view(document)
            if str(item.get("heading", "")).strip() == "2. Particles from moles"
        )
        self.assertEqual(markdown_declared_contract_from_encounter(encounter), ("N", ["n", "N_A"]))
        self.assertEqual(markdown_direct_expression_mapping(encounter), ("N", ["n", "N_A"], "n * N_A"))

    def test_chemistry_fraction_forms_normalize_into_division(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that chemistry fraction laws become usable division expressions instead of leaking `frac` tokens.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_chemistry_fraction_forms_normalize_into_division()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        source = CHEMISTRY_ROOT / "06_LEARN_CHEMISTRY_RELATIONS_CONCENTRATION.md"
        document = parse_markdown_document_ir(source.read_text(), source_path=str(source))
        encounter = next(
            item
            for item in markdown_learning_encounter_view(document)
            if str(item.get("heading", "")).strip() == "2. Molar concentration"
        )
        self.assertEqual(markdown_declared_contract_from_encounter(encounter), ("C", ["n", "V"]))
        self.assertEqual(markdown_direct_expression_mapping(encounter), ("C", ["n", "V"], "( ( n ) / ( V ) )"))

    def test_chemistry_ideal_gas_expression_splits_compacted_product_symbols(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that compact chemistry products like `nRT` are expanded back into the declared inputs before execution and retrieval.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_chemistry_ideal_gas_expression_splits_compacted_product_symbols()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        source = CHEMISTRY_ROOT / "08_LEARN_CHEMISTRY_RELATIONS_IDEAL_GAS.md"
        document = parse_markdown_document_ir(source.read_text(), source_path=str(source))
        encounter = next(
            item
            for item in markdown_learning_encounter_view(document)
            if str(item.get("heading", "")).strip() == "2. Pressure from amount, temperature, and volume"
        )
        self.assertEqual(markdown_declared_contract_from_encounter(encounter), ("P", ["n", "R", "T", "V"]))
        self.assertEqual(
            markdown_direct_expression_mapping(encounter),
            ("P", ["n", "R", "T", "V"], "( ( n * R * T ) / ( V ) )"),
        )


if __name__ == "__main__":
    unittest.main()
