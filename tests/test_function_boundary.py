# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from retrieval_ranking import artifact_action_alignment_penalty, primary_action_surface_marker

from main import (
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    BSSCController,
    LearningRelation,
    ProposalGovernanceStatus,
    ProposalObject,
    ProposalType,
    Product,
    RunOutcome,
    SupplementMode,
    SystemState,
    cross_boundary,
)


FORCE_SCRIPT = """
# /// script
# requires-python = ">=3.11"
# dependencies = ["msgspec", "orjson"]
# ///

from __future__ import annotations

import argparse
import sys

import msgspec
import orjson


class InputPayload(msgspec.Struct, kw_only=True):
    payload: dict[str, int]


class OutputPayload(msgspec.Struct, kw_only=True):
    status: str
    answer: str
    result: dict[str, int]
    notes: list[str] = []


def run(payload: InputPayload) -> OutputPayload:
    mass = int(payload.payload["mass"])
    acceleration = int(payload.payload["acceleration"])
    force = mass * acceleration
    return OutputPayload(
        status="ok",
        answer=str(force),
        result={"force": force},
        notes=["validated via force = mass * acceleration"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="force function")
    parser.add_argument("--input-json", help="optional JSON payload")
    args = parser.parse_args()
    raw = args.input_json.encode("utf-8") if args.input_json else sys.stdin.buffer.read()
    payload = orjson.loads(raw) if raw else {}
    typed_input = msgspec.convert({"payload": payload}, type=InputPayload)
    result = run(typed_input)
    sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result)))
    sys.stdout.buffer.write(b"\\n")


if __name__ == "__main__":
    main()
""".strip()


def hi_wasm_module_text() -> str:
    payload = {
        "status": "ok",
        "answer": "hi",
        "result": {"greeting": "hi"},
        "notes": ["executed through embedded wasmtime"],
    }
    output_text = json.dumps(payload, separators=(",", ":"))
    escaped_output = output_text.replace("\\", "\\\\").replace('"', '\\"')
    return (
        "(module\n"
        '  (import "bssc" "input_len" (func $input_len (result i32)))\n'
        '  (import "bssc" "read_input" (func $read_input (param i32) (result i32)))\n'
        '  (import "bssc" "write_output" (func $write_output (param i32 i32) (result i32)))\n'
        '  (memory (export "memory") 1)\n'
        f'  (data (i32.const 1024) "{escaped_output}")\n'
        '  (func (export "run") (result i32)\n'
        "    call $input_len\n"
        "    drop\n"
        "    i32.const 0\n"
        "    call $read_input\n"
        "    drop\n"
        "    i32.const 1024\n"
        f"    i32.const {len(output_text)}\n"
        "    call $write_output\n"
        "    drop\n"
        "    i32.const 0))"
    )


class FunctionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling setUp.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `setUp()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.tempdir = tempfile.TemporaryDirectory(prefix="function_boundary_")
        self.sqlite_path = str(Path(self.tempdir.name) / "function_boundary.sqlite3")
        self.previous_sqlite_path = os.environ.get("STATE_SQLITE_PATH")
        os.environ["STATE_SQLITE_PATH"] = self.sqlite_path

    def tearDown(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling tearDown.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `tearDown()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self.previous_sqlite_path is None:
            os.environ.pop("STATE_SQLITE_PATH", None)
        else:
            os.environ["STATE_SQLITE_PATH"] = self.previous_sqlite_path
        self.tempdir.cleanup()

    def make_force_artifact(self) -> Artifact:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with creating force artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `make_force_artifact()`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            Artifact: Result produced by `make_force_artifact`.
        """
        return Artifact(
            id="artifact-force-function",
            artifact_type=ArtifactType.ABILITY,
            title="Force from mass and acceleration",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when force must be computed from mass and acceleration under F = m * a",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={
                "preconditions": ["mass and acceleration are supplied as integers"],
                "invariant_core": "force equals mass times acceleration",
                "variation_parameters": ["mass", "acceleration"],
                "governed_function": "compute force from parameter values",
                "bssc_awareness": {},
                "holdon_awareness": {},
                "completion_conditions": ["the script emits a structured force result"],
                "failure_conditions": ["required inputs are missing"],
                "harvest_conditions": ["later runs can reuse the same function family"],
                "scope_of_reuse": "bounded mechanics calculations of force from mass and acceleration",
            },
            learning_relation=LearningRelation.EXTENDS_PARAMETERS,
            related_artifact_ids=[],
            content={
                "question": "How do you compute force from mass and acceleration?",
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "mass": "integer mass value",
                    "acceleration": "integer acceleration value",
                },
                "output_contract": {"force": "integer force result"},
                "structured_learning": {
                    "encountered_not": "Force Mass Acceleration",
                    "lookup_keys": ["force mass acceleration", "f ma"],
                    "component_nots": ["Force", "Mass", "Acceleration"],
                    "composed_not": "Force Mass Acceleration",
                    "notation_yaml": "",
                },
            },
            justification="A reusable executable artifact for the force law.",
            constraints=["use only for bounded force calculations with supplied numeric parameters"],
        )

    def make_hi_artifact(self) -> Artifact:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with creating hi artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `make_hi_artifact()`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            Artifact: Result produced by `make_hi_artifact`.
        """
        return Artifact(
            id="artifact-hi-function",
            artifact_type=ArtifactType.ABILITY,
            title="Hi responder",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a direct hi response is needed with no inputs",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={
                "preconditions": [],
                "invariant_core": "emit hi with no further input",
                "variation_parameters": [],
                "governed_function": "return a static greeting",
                "bssc_awareness": {},
                "holdon_awareness": {},
                "completion_conditions": ["a structured hi result is emitted"],
                "failure_conditions": [],
                "harvest_conditions": ["later runs reuse the same direct output function"],
                "scope_of_reuse": "bounded greeting output",
            },
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Say hi.",
                "python_script": """
# /// script
# requires-python = \">=3.11\"
# dependencies = [\"msgspec\", \"orjson\"]
# ///

from __future__ import annotations

import argparse
import sys

import msgspec
import orjson


class OutputPayload(msgspec.Struct, kw_only=True):
    status: str
    answer: str
    result: dict[str, str]
    notes: list[str] = []


def run() -> OutputPayload:
    return OutputPayload(status=\"ok\", answer=\"hi\", result={\"greeting\": \"hi\"}, notes=[\"static greeting\"])\n

def main() -> None:
    parser = argparse.ArgumentParser(description=\"hi responder\")
    parser.add_argument(\"--input-json\", help=\"optional JSON payload\")
    parser.parse_args()
    sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(run())))
    sys.stdout.buffer.write(b\"\\n\")


if __name__ == \"__main__\":
    main()
                """.strip(),
                "entrypoint": "main",
                "script_language": "python",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {},
                "output_contract": {"greeting": "string greeting"},
                "structured_learning": {
                    "encountered_not": "Say Hi",
                    "lookup_keys": ["say hi"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="A reusable executable artifact for a direct hi response.",
            boundary_shape=(),
            constraints=["use only for direct greeting output"],
        )

    def test_refresh_expression_ability_content_repairs_fraction_surface_and_prunes_noise(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over persisted markdown abilities with malformed ratio syntax, helps with proving that execution repair can convert `rac * (...) * (...)` into division and drop garbage inputs that no longer participate in the repaired expression.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refresh_expression_ability_content_repairs_fraction_surface_and_prunes_noise()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("expression repair"), llm_policy="off")
        repaired = controller.refresh_expression_ability_content(
            title="Physics / Speed From Distance And Time",
            scope="reuse for speed calculations",
            content={
                "compute_expression": "rac * ( d ) * ( t )",
                "output_field": "ext_times_speed",
                "input_contract": {"rac": "number", "d": "number", "t": "number"},
                "output_contract": {"ext_times_speed": "number"},
                "python_script": "",
            },
        )
        self.assertEqual(repaired.get("compute_expression"), "((d) / (t))")
        self.assertEqual(sorted(repaired.get("input_contract", {}).keys()), ["d", "t"])
        self.assertIn("EXPRESSION = '((d) / (t))'", str(repaired.get("python_script", "")))

    def test_refresh_expression_ability_content_repairs_flattened_superscript_surface(self) -> None:
        """
        High Level Purpose:
            In circumstances like persisted markdown abilities whose exponent notation has been flattened into adjacency, helps with proving that execution repair restores executable power syntax instead of preserving malformed token soup.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refresh_expression_ability_content_repairs_flattened_superscript_surface()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("exponent repair"), llm_policy="off")
        repaired = controller.refresh_expression_ability_content(
            title="Geometry / Hypotenuse From Shorter Sides",
            scope="reuse for right-triangle hypotenuse calculations",
            content={
                "compute_expression": "( a 2 + b 2 ) 0.5",
                "output_field": "c",
                "input_contract": {"a": "number", "b": "number"},
                "output_contract": {"c": "number"},
                "python_script": "",
            },
        )
        self.assertEqual(repaired.get("compute_expression"), "( a ** 2 + b ** 2 ) ** 0.5")
        self.assertIn("EXPRESSION = '( a ** 2 + b ** 2 ) ** 0.5'", str(repaired.get("python_script", "")))

    def test_refresh_expression_ability_content_preserves_valid_power_expression(self) -> None:
        """
        High Level Purpose:
            In circumstances like refreshing already-valid executable formulas, helps with proving that normalization does not strip or flatten legitimate power syntax.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refresh_expression_ability_content_preserves_valid_power_expression()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("valid exponent preservation"), llm_policy="off")
        repaired = controller.refresh_expression_ability_content(
            title="Geometry / Hypotenuse From Shorter Sides",
            scope="reuse for right-triangle hypotenuse calculations",
            content={
                "compute_expression": "(a**2 + b**2)**0.5",
                "output_field": "c",
                "input_contract": {"a": "number", "b": "number"},
                "output_contract": {"c": "number"},
                "python_script": "",
            },
        )
        self.assertEqual(repaired.get("compute_expression"), "(a**2 + b**2)**0.5")
        self.assertIn("EXPRESSION = '(a**2 + b**2)**0.5'", str(repaired.get("python_script", "")))

    def test_refresh_expression_ability_content_repairs_adjacent_superscript_tokens(self) -> None:
        """
        High Level Purpose:
            In circumstances like persisted markdown abilities whose exponents collapse into `a2`-style adjacency, helps with proving that execution repair restores explicit power syntax.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refresh_expression_ability_content_repairs_adjacent_superscript_tokens()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("adjacent exponent repair"), llm_policy="off")
        repaired = controller.refresh_expression_ability_content(
            title="Geometry / Hypotenuse From Shorter Sides",
            scope="reuse for right-triangle hypotenuse calculations",
            content={
                "compute_expression": "( a2 + b2 ) 0.5",
                "output_field": "c",
                "input_contract": {"a": "number", "b": "number"},
                "output_contract": {"c": "number"},
                "python_script": "",
            },
        )
        self.assertEqual(repaired.get("compute_expression"), "( a ** 2 + b ** 2 ) ** 0.5")

    def test_refresh_expression_ability_content_repairs_implicit_pi_multiplication(self) -> None:
        """
        High Level Purpose:
            In circumstances like persisted markdown abilities whose surface omits multiplication around `pi`, helps with proving that execution repair restores an executable constant-backed expression instead of leaving malformed adjacency.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refresh_expression_ability_content_repairs_implicit_pi_multiplication()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("implicit pi repair"), llm_policy="off")
        repaired = controller.refresh_expression_ability_content(
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            scope="reuse for total surface area calculations",
            content={
                "compute_expression": "2 pi r ( r + h )",
                "output_field": "A",
                "input_contract": {"r": "number", "h": "number"},
                "output_contract": {"A": "number"},
                "python_script": "",
            },
        )
        self.assertEqual(repaired.get("compute_expression"), "2 * math.pi * r * ( r + h )")
        self.assertIn("EXPRESSION = '2 * math.pi * r * ( r + h )'", str(repaired.get("python_script", "")))

    def test_refresh_expression_ability_content_preserves_pi_input_symbol(self) -> None:
        """
        High Level Purpose:
            In circumstances like persisted markdown abilities that intentionally use `pi` as a declared input symbol, helps with proving that execution repair does not rewrite that symbol into the math constant.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refresh_expression_ability_content_preserves_pi_input_symbol()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("pi input preservation"), llm_policy="off")
        repaired = controller.refresh_expression_ability_content(
            title="Circle Measures / Circumference From Pi And Radius",
            scope="reuse when pi is supplied externally",
            content={
                "compute_expression": "2 pi r",
                "output_field": "C",
                "input_contract": {"pi": "number", "r": "number"},
                "output_contract": {"C": "number"},
                "python_script": "",
            },
        )
        self.assertEqual(repaired.get("compute_expression"), "2 * pi * r")
        self.assertIn("EXPRESSION = '2 * pi * r'", str(repaired.get("python_script", "")))

    def test_execute_function_artifact_allows_math_pi_constant(self) -> None:
        """
        High Level Purpose:
            In circumstances like executing a repaired geometry formula that needs the circle constant, helps with proving that governed expression execution admits the bounded `math.pi` constant without widening the executable surface beyond that constant access.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_execute_function_artifact_allows_math_pi_constant()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("cylinder area from radius and height")
        controller = BSSCController(state, llm_policy="off")
        content = controller.refresh_expression_ability_content(
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            scope="reuse for total surface area calculations",
            content={
                "compute_expression": "2 pi r ( r + h )",
                "output_field": "A",
                "input_contract": {"r": "number", "h": "number"},
                "output_contract": {"A": "number"},
                "python_script": "",
            },
        )
        artifact = Artifact(
            id="artifact-cylinder-area-expression",
            artifact_type=ArtifactType.ABILITY,
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for total surface area calculations",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.EXTENDS_PARAMETERS,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate total surface area from radius and height?",
                "entrypoint": "main",
                "script_language": "python",
                "dependencies": ["msgspec", "orjson"],
                **content,
            },
            justification="A repaired cylinder-area expression artifact that uses math.pi.",
        )

        execution = controller.execute_function_artifact(
            artifact,
            semantic_unit="Calculate the total surface area of a cylinder with radius=3 and height=5.",
        )

        self.assertTrue(execution.ok)
        self.assertAlmostEqual(float(execution.result["A"]), 48 * 3.141592653589793)

    def test_state_to_dict_promotes_committed_product_answer_to_final_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like persisted run inspection after a bounded computation succeeds, helps with proving that serialized state exposes the committed product answer as the top-level final answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_state_to_dict_promotes_committed_product_answer_to_final_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Calculate force for mass=3 and acceleration=4.")
        root = state.root()
        state.products["product-force"] = Product(
            id="product-force",
            node_id=root.id,
            content={"answer": "12"},
            committed=True,
            provenance=[root.id],
        )
        self.assertEqual(state.to_dict().get("final_answer"), "12")

    def test_cross_boundary_executes_python_script(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing cross boundary executes python script.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_cross_boundary_executes_python_script()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        result = cross_boundary(FORCE_SCRIPT, {"mass": 3, "acceleration": 4})
        self.assertTrue(result.ok)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.answer, "12")
        self.assertIsInstance(result.result, dict)
        self.assertEqual(result.result["force"], 12)

    def test_execute_function_artifact_executes_wasm_wasi_module(self) -> None:
        state = SystemState.bootstrap("Say hi from wasm.")
        state.controller_features.supported_executors = ["python3", "wasm_wasi"]
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-wasm-hi",
            artifact_type=ArtifactType.ABILITY,
            title="Wasm Hi",
            representation=ArtifactRepresentation.WASM_MODULE,
            function_bit=1,
            scope="reuse for bounded wasm hi execution",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "entrypoint": "run",
                "executor_framework": "wasm_wasi",
                "script_language": "wasm",
                "input_contract": {},
                "output_contract": {"greeting": "string greeting"},
                "wasm_module": hi_wasm_module_text(),
                "wasm_abi_version": "bssc.wasm.v1",
                "wasm_format": "wat",
            },
            justification="A bounded embedded Wasm greeting artifact.",
        )

        result = controller.execute_function_artifact(
            artifact,
            semantic_unit="Say hi from wasm.",
            explicit_payload={},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.answer, "hi")
        self.assertIsInstance(result.result, dict)
        self.assertEqual(result.result["greeting"], "hi")
        self.assertEqual(result.metadata.get("wasm_abi_version"), "bssc.wasm.v1")
        self.assertGreaterEqual(len(state.effect_traces), 1)
        self.assertEqual(state.effect_traces[-1]["request"]["effect_kind"], "execute.wasm_wasi")

    def test_callable_snippet_ability_script_preserves_source_main_function(self) -> None:
        """
        High Level Purpose:
            In circumstances like turning a learned fenced Python function named `main` into a reusable executable artifact, helps with proving that the generated CLI wrapper does not shadow the learned callable and still executes it with named payload inputs.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_callable_snippet_ability_script_preserves_source_main_function()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("callable snippet"), llm_policy="off")
        script = controller.callable_snippet_ability_script(
            title="Increment Value",
            scope="reuse for bounded increment-by-one execution",
            justification="test",
            python_code="""
def main(value: int) -> int:
    return int(value) + 1
            """.strip(),
            function_name="main",
            argument_names=["value"],
        )

        result = cross_boundary(script, {"value": 2})

        self.assertTrue(result.ok)
        self.assertEqual(result.answer, "3")
        self.assertEqual(result.result["result"], 3)

    def test_callable_snippet_ability_script_preserves_keyword_only_inputs(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed Python skills that take mount-relative keyword-only inputs, helps with proving that the generated CLI wrapper forwards keyword-only parameters instead of silently dropping them.

        Reference to Theory:
            Verifies the boundary wrapper generation for learned Python `main(...)` functions so governed mount-path skills remain executable after learning.

        Example Input Output:
            Input: `test_callable_snippet_ability_script_preserves_keyword_only_inputs()`
            Output: None
        """
        controller = BSSCController(SystemState.bootstrap("callable snippet kwonly"), llm_policy="off")
        script = controller.callable_snippet_ability_script(
            title="Echo Mount Path",
            scope="reuse for governed mount-path echo execution",
            justification="test",
            python_code="""
def main(mount: str, *, relative_path: str = "") -> dict[str, str]:
    return {"mount": mount, "relative_path": relative_path}
            """.strip(),
            function_name="main",
            argument_names=["mount", "relative_path"],
        )

        result = cross_boundary(script, {"mount": "skill_input", "relative_path": "trials"})

        self.assertTrue(result.ok)
        self.assertEqual(result.result["result"]["mount"], "skill_input")
        self.assertEqual(result.result["result"]["relative_path"], "trials")

    def test_execute_function_artifact_derives_named_payload(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with building payload data for test execute function artifact derives named.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_execute_function_artifact_derives_named_payload()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Force from mass and acceleration")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_force_artifact()
        execution = controller.execute_function_artifact(
            artifact,
            semantic_unit="Use force from mass and acceleration with mass=3 acceleration=4.",
        )
        self.assertTrue(execution.ok)
        self.assertEqual(execution.answer, "12")
        self.assertEqual(execution.result["force"], 12)
        self.assertEqual(len(state.capability_grants), 1)
        self.assertEqual(state.capability_grants[0]["authority"], "execute")
        self.assertEqual(state.capability_grants[0]["effect_kind"], "execute.python3")
        self.assertEqual(len(state.effect_traces), 1)
        self.assertTrue(state.effect_traces[0]["decision"]["allowed"])
        self.assertEqual(state.effect_traces[0]["request"]["effect_kind"], "execute.python3")

    def test_governed_v2_skill_not_admitted_is_denied_at_execution_boundary(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed runtime mediation for declaration-first skills, helps with proving that a held v2 skill cannot be treated as executable or cross the boundary.

        Reference to Theory:
            Verifies the policy-before-use rule so governed skills with non-admitted status do not become effective merely because they are present in the store.

        Example Input Output:
            Input: `test_governed_v2_skill_not_admitted_is_denied_at_execution_boundary()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Force from mass and acceleration")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_force_artifact()
        artifact.content["skill_schema"] = "bssc_skill.v2"
        artifact.content["skill_kind"] = "ability"
        artifact.content["skill_admission"] = {
            "status": "held",
            "admitted": False,
            "rationale": "No policy artifact is currently installed for governed v2 skills.",
            "policy_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": "2026-03-31T00:00:00Z",
        }

        self.assertFalse(controller.artifact_is_executable_function(artifact))
        execution = controller.execute_function_artifact(
            artifact,
            semantic_unit="Use force from mass and acceleration with mass=3 acceleration=4.",
        )

        self.assertFalse(execution.ok)
        self.assertIn("No policy artifact is currently installed", execution.stderr)
        self.assertEqual(state.capability_grants, [])
        self.assertEqual(len(state.effect_traces), 1)
        self.assertFalse(state.effect_traces[0]["decision"]["allowed"])
        self.assertIn("No policy artifact is currently installed", state.effect_traces[0]["decision"]["rationale"])

    def test_state_round_trips_capability_grants_and_effect_traces(self) -> None:
        """
        High Level Purpose:
            In circumstances like replaying governed execution state after a mediated boundary crossing, helps with proving that runtime grants and effect traces survive state serialization and restoration.

        Reference to Theory:
            Verifies the first bundle-style host mediation cut so effect-level constitutional trace data is durable instead of existing only in memory during one run.

        Example Input Output:
            Input: `test_state_round_trips_capability_grants_and_effect_traces()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Force from mass and acceleration")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_force_artifact()

        execution = controller.execute_function_artifact(
            artifact,
            semantic_unit="Use force from mass and acceleration with mass=6 acceleration=7.",
        )

        self.assertTrue(execution.ok)
        serialized = state.to_dict()
        self.assertEqual(len(serialized.get("capability_grants", [])), 1)
        self.assertEqual(len(serialized.get("effect_traces", [])), 1)

        restored = SystemState.from_dict(serialized)

        self.assertEqual(len(restored.capability_grants), 1)
        self.assertEqual(restored.capability_grants[0]["authority"], "execute")
        self.assertEqual(len(restored.effect_traces), 1)
        self.assertEqual(restored.effect_traces[0]["request"]["effect_kind"], "execute.python3")

    def test_execute_function_artifact_repairs_assignment_shaped_expression_script(self) -> None:
        """
        High Level Purpose:
            In circumstances like persisted executable artifacts that were learned from equation text, helps with proving that execution repairs an assignment-shaped expression script into a governed evaluable form.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_execute_function_artifact_repairs_assignment_shaped_expression_script()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Force from mass and acceleration")
        controller = BSSCController(state, llm_policy="off")
        stale_script = controller.expression_ability_script(
            title="Newton's Laws of Motion / Force-Mass-Acceleration Relationship",
            scope="reuse when force must be computed from mass and acceleration under F = m * a",
            input_contract={"m": "number", "a": "number"},
            output_contract={"F": "number"},
            expression="F = m * a",
            output_field="F",
        )
        artifact = Artifact(
            id="artifact-force-expression",
            artifact_type=ArtifactType.ABILITY,
            title="Newton's Laws of Motion / Force-Mass-Acceleration Relationship",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when force must be computed from mass and acceleration under F = m * a",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.EXTENDS_PARAMETERS,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate F from m, a?",
                "python_script": stale_script,
                "compute_expression": "F = m * a",
                "output_field": "F",
                "entrypoint": "main",
                "script_language": "python",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {"m": "number", "a": "number"},
                "output_contract": {"F": "number"},
            },
            justification="A persisted expression artifact that still carries equation-shaped compute text.",
        )

        execution = controller.execute_function_artifact(
            artifact,
            semantic_unit="Calculate force for mass=3 and acceleration=4.",
        )

        self.assertTrue(execution.ok)
        self.assertEqual(execution.answer, "12")
        self.assertEqual(str(artifact.content.get("compute_expression", "")), "m * a")
        self.assertIn("EXPRESSION = 'm * a'", str(artifact.content.get("python_script", "")))

    def test_single_input_artifact_does_not_guess_from_multiple_numeric_literals(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing single input artifact does not guess from multiple numeric literals.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_single_input_artifact_does_not_guess_from_multiple_numeric_literals()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Hypotenuse prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-equal-side-special-case",
            artifact_type=ArtifactType.ABILITY,
            title="Equal side special case",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse only when one shared side length is given",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "calculate the slanted side from the other two sides?",
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {"s": "shared side length"},
                "output_contract": {"c": "hypotenuse"},
                "structured_learning": {
                    "encountered_not": "Equal Side Special Case",
                    "lookup_keys": ["equal side special case"],
                    "component_nots": ["S", "C"],
                    "composed_not": "Equal Side Special Case",
                    "notation_yaml": "",
                },
            },
            justification="A one-parameter special case function.",
            constraints=["do not reuse when separate a and b values are provided"],
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Calculate the slanted side if a=8 and b=15.",
        )
        self.assertIsNone(payload)

    def test_function_artifact_executes_during_reuse(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing function artifact executes during reuse.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_function_artifact_executes_during_reuse()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Use the stored force function with mass=3 acceleration=4.")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_force_artifact()
        state.learned_artifacts[artifact.id] = artifact
        root = state.root()

        controller.lookup_prior_non_achievedness = lambda node: {
            "current": controller.structured_learning_view(node),
            "match_kind": "encountered_before",
            "matched_artifacts": [artifact],
            "answer_artifact": artifact,
            "answer_match_kind": "encountered_before",
            "answer_preference": "same_key",
            "matched_lookup_keys": ["force mass acceleration"],
        }

        attached = controller.instantiate_reusable_artifact_support(root)
        self.assertTrue(attached)
        self.assertTrue(root.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertEqual(root.metadata.get("direct_resolution_answer"), "12")

    def test_derive_artifact_invocation_payload_extracts_url_and_browser_from_normal_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over device-style executable prompts, helps with proving that a normal natural-language prompt can still populate string-valued invocation inputs such as `url` and `browser` without requiring explicit `url=` syntax.

        Reference to Theory:
            Verifies the implemented theory, especially the artifact/boundary rules used to keep executable reuse aligned with the asked semantic unit.

        Example Input Output:
            Input: `test_derive_artifact_invocation_payload_extracts_url_and_browser_from_normal_prompt()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Open browser prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-browser-url",
            artifact_type=ArtifactType.ABILITY,
            title="Launch Browser At Specific URL",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when the user wants a named browser opened at a URL",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "url": "target web address",
                    "browser": "browser application name",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A two-parameter browser launch ability.",
            constraints=["extract browser name and URL from the prompt"],
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Open Google Chrome to https://google.com.",
        )
        self.assertEqual(
            payload,
            {
                "url": "https://google.com",
                "browser": "Google Chrome",
            },
        )

    def test_derive_artifact_invocation_payload_extracts_mount_and_relative_path_from_normal_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed mount-based task prompts, helps with proving that normal language can populate both the mount name and the mount-relative target path without explicit `mount=` syntax.

        Reference to Theory:
            Verifies the governed data-surface routing needed by mount-oriented Python skills.

        Example Input Output:
            Input: `test_derive_artifact_invocation_payload_extracts_mount_and_relative_path_from_normal_prompt()`
            Output: None
        """
        state = SystemState.bootstrap("Mount prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-list-mounted-directory",
            artifact_type=ArtifactType.ABILITY,
            title="List Directory Entries",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a mounted directory should be listed",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "mount": "governed virtual mount name",
                    "relative_path": "path inside the mount",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A governed mount-list ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="List the entries in mount `skill_input` at `trials`.",
        )
        self.assertEqual(
            payload,
            {
                "mount": "skill_input",
                "relative_path": "trials",
            },
        )

    def test_derive_artifact_invocation_payload_extracts_mount_text_and_path_for_write_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed mounted write prompts, helps with proving that text-bearing prompts can populate literal content plus mount-relative destination arguments.

        Reference to Theory:
            Verifies that mount-oriented Python abilities can be invoked from normal prompts without falling back to incomplete structured-learning residue.

        Example Input Output:
            Input: `test_derive_artifact_invocation_payload_extracts_mount_text_and_path_for_write_prompt()`
            Output: None
        """
        state = SystemState.bootstrap("Mount write prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-write-mounted-file",
            artifact_type=ArtifactType.ABILITY,
            title="Write Text File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when text should be written to a governed mount-relative path",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "mount": "governed virtual mount name",
                    "relative_path": "path inside the mount",
                    "text": "text to write",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A governed mounted-write ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Write `hello world` to mount `skill_tmp` at `python-suite.txt`.",
        )
        self.assertEqual(
            payload,
            {
                "mount": "skill_tmp",
                "relative_path": "python-suite.txt",
                "text": "hello world",
            },
        )

    def test_derive_artifact_invocation_payload_decodes_escaped_newlines_for_text_fields(self) -> None:
        state = SystemState.bootstrap("Mount csv write prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-write-mounted-csv-file",
            artifact_type=ArtifactType.ABILITY,
            title="Write Csv File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when CSV text should be written to a governed mount-relative path",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "mount": "governed virtual mount name",
                    "relative_path": "path inside the mount",
                    "csv_text": "CSV text to write",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A governed mounted CSV-write ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Write the CSV text `name,score\\nAda,10\\nBob,9\\n` to mount `skill_tmp` at `data.csv`.",
        )
        self.assertEqual(
            payload,
            {
                "mount": "skill_tmp",
                "relative_path": "data.csv",
                "csv_text": "name,score\nAda,10\nBob,9\n",
            },
        )

    def test_derive_artifact_invocation_payload_prefers_contract_fields_over_inline_json_object(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed JSON-file write prompts that include a literal JSON object, helps with proving that inline JSON extraction does not override the artifact's named input contract.

        Reference to Theory:
            Verifies that contract-aware invocation payload derivation remains correct for mounted write skills that accept a JSON string as one named input.

        Example Input Output:
            Input: `test_derive_artifact_invocation_payload_prefers_contract_fields_over_inline_json_object()`
            Output: None
        """
        state = SystemState.bootstrap("Mount json write prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-write-mounted-json-file",
            artifact_type=ArtifactType.ABILITY,
            title="Write Json File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when JSON text should be written to a governed mount-relative path",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "mount": "governed virtual mount name",
                    "relative_path": "path inside the mount",
                    "json_text": "JSON text to write",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A governed mounted JSON-write ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit='Write the JSON text `{"status":"ok","enabled":true}` to mount `skill_tmp` at `config.json`.',
        )
        self.assertEqual(
            payload,
            {
                "mount": "skill_tmp",
                "relative_path": "config.json",
                "json_text": '{"status":"ok","enabled":true}',
            },
        )

    def test_derive_artifact_invocation_payload_extracts_source_and_destination_paths(self) -> None:
        """
        High Level Purpose:
            In circumstances like raw-path file manipulation prompts, helps with proving that path-like literals are preserved into source and destination arguments.

        Reference to Theory:
            Verifies that path-bearing executable skills can still be invoked from ordinary prompts that use backticked paths instead of explicit JSON payloads.

        Example Input Output:
            Input: `test_derive_artifact_invocation_payload_extracts_source_and_destination_paths()`
            Output: None
        """
        state = SystemState.bootstrap("Copy file prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-copy-file",
            artifact_type=ArtifactType.ABILITY,
            title="Copy File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a file should be copied from one path to another",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "source_path": "file to copy",
                    "destination_path": "copy destination",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A path-copy ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Copy `/etc/hosts` to `/tmp/python-hosts.copy`.",
        )
        self.assertEqual(
            payload,
            {
                "source_path": "/etc/hosts",
                "destination_path": "/tmp/python-hosts.copy",
            },
        )

    def test_derive_artifact_invocation_payload_extracts_multi_mount_copy_fields(self) -> None:
        """
        High Level Purpose:
            In circumstances like governed cross-mount file operations, helps with proving that normal prompts can populate source and destination mount-relative arguments without explicit JSON payload syntax.

        Reference to Theory:
            Verifies the broker-first data-surface path needed by governed Python skills that copy or move files across named mounts.

        Example Input Output:
            Input: `test_derive_artifact_invocation_payload_extracts_multi_mount_copy_fields()`
            Output: None
        """
        state = SystemState.bootstrap("Copy mount prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-copy-mounted-file",
            artifact_type=ArtifactType.ABILITY,
            title="Copy Mounted File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a file should be copied across governed mounts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "source_mount": "source governed virtual mount name",
                    "source_relative_path": "path inside the source mount",
                    "destination_mount": "destination governed virtual mount name",
                    "destination_relative_path": "path inside the destination mount",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A cross-mount copy ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Copy `trials/python/README.md` from mount `skill_input` to mount `skill_tmp` at `python-readme.copy`.",
        )
        self.assertEqual(
            payload,
            {
                "source_mount": "skill_input",
                "source_relative_path": "trials/python/README.md",
                "destination_mount": "skill_tmp",
                "destination_relative_path": "python-readme.copy",
            },
        )

    def test_derive_artifact_invocation_payload_extracts_role_aware_mount_fields_for_create_zip(self) -> None:
        state = SystemState.bootstrap("Create zip mount prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-create-zip-mounted",
            artifact_type=ArtifactType.ABILITY,
            title="Create Mounted Zip Archive",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a directory should be zipped across governed mounts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "source_mount": "source governed virtual mount name",
                    "source_relative_path": "path inside the source mount",
                    "destination_mount": "destination governed virtual mount name",
                    "destination_relative_path": "path inside the destination mount",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A cross-mount zip creation ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Create `realized-tests.zip` in mount `skill_tmp` from mount `skill_input` at `tests`.",
        )
        self.assertEqual(
            payload,
            {
                "source_mount": "skill_input",
                "source_relative_path": "tests",
                "destination_mount": "skill_tmp",
                "destination_relative_path": "realized-tests.zip",
            },
        )

    def test_derive_artifact_invocation_payload_extracts_mount_relative_path_and_url_for_download_prompt(self) -> None:
        state = SystemState.bootstrap("Download mount prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-download-mounted-file",
            artifact_type=ArtifactType.ABILITY,
            title="Download Url To Mounted File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a URL should be downloaded into a governed mount",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "url": "remote resource url",
                    "mount": "destination governed mount",
                    "relative_path": "destination path inside the mount",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A governed mount download ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Download `https://example.com` to mount `skill_tmp` at `example-python.html`.",
        )
        self.assertEqual(
            payload,
            {
                "url": "https://example.com",
                "mount": "skill_tmp",
                "relative_path": "example-python.html",
            },
        )

    def test_derive_artifact_invocation_payload_extracts_mount_root_and_suffix_for_find_prompt(self) -> None:
        state = SystemState.bootstrap("Find mount prompt")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-find-mounted-suffix",
            artifact_type=ArtifactType.ABILITY,
            title="Find Files By Suffix In Mount",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when suffix matches should be found under a governed mount path",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "mount": "governed mount",
                    "relative_path": "root path inside the mount",
                    "suffix": "matching file suffix",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A governed mount recursive find ability.",
        )
        payload = controller.derive_artifact_invocation_payload(
            artifact,
            semantic_unit="Find files ending in `.md` under mount `skill_input` at `trials`.",
        )
        self.assertEqual(
            payload,
            {
                "mount": "skill_input",
                "relative_path": "trials",
                "suffix": ".md",
            },
        )

    def test_move_prompt_ranks_move_artifact_above_copy_artifact(self) -> None:
        state = SystemState.bootstrap("Move ranking")
        controller = BSSCController(state, llm_policy="off")
        copy_artifact = Artifact(
            id="artifact-copy-mounted-file",
            artifact_type=ArtifactType.ABILITY,
            title="Copy Mounted File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a file should be copied across governed mounts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Copy a file from one governed mount to another.",
                "input_contract": {
                    "source_mount": "source mount",
                    "source_relative_path": "source path",
                    "destination_mount": "destination mount",
                    "destination_relative_path": "destination path",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A copy ability.",
        )
        move_artifact = Artifact(
            id="artifact-move-mounted-file",
            artifact_type=ArtifactType.ABILITY,
            title="Move Mounted File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a file should be moved across governed mounts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Move a file from one governed mount to another.",
                "input_contract": {
                    "source_mount": "source mount",
                    "source_relative_path": "source path",
                    "destination_mount": "destination mount",
                    "destination_relative_path": "destination path",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A move ability.",
        )
        prompt = "Move `python-readme.copy` from mount `skill_tmp` to mount `skill_output` at `python-readme.moved`."
        copy_rank = controller.answer_candidate_rank(
            copy_artifact,
            semantic_unit=prompt,
            current_boundary_shape=state.root().boundary_shape,
        )
        move_rank = controller.answer_candidate_rank(
            move_artifact,
            semantic_unit=prompt,
            current_boundary_shape=state.root().boundary_shape,
        )
        self.assertLess(move_rank, copy_rank)

    def test_primary_action_surface_marker_ignores_action_words_inside_file_names(self) -> None:
        marker = primary_action_surface_marker(
            "Move `python-readme.copy` from mount `skill_tmp` to mount `skill_output` at `python-readme.moved`."
        )
        self.assertEqual(marker, "move")

    def test_action_alignment_penalty_uses_prompt_primary_action_not_filename_tokens(self) -> None:
        copy_artifact = Artifact(
            id="artifact-copy-mounted-file",
            artifact_type=ArtifactType.ABILITY,
            title="Copy Mounted File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a file should be copied across governed mounts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Copy a file from one governed mount to another.",
                "input_contract": {
                    "source_mount": "source mount",
                    "source_relative_path": "source path",
                    "destination_mount": "destination mount",
                    "destination_relative_path": "destination path",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A copy ability.",
        )
        move_artifact = Artifact(
            id="artifact-move-mounted-file",
            artifact_type=ArtifactType.ABILITY,
            title="Move Mounted File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a file should be moved across governed mounts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Move a file from one governed mount to another.",
                "input_contract": {
                    "source_mount": "source mount",
                    "source_relative_path": "source path",
                    "destination_mount": "destination mount",
                    "destination_relative_path": "destination path",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A move ability.",
        )
        prompt = "Move `python-readme.copy` from mount `skill_tmp` to mount `skill_output` at `python-readme.moved`."
        self.assertEqual(artifact_action_alignment_penalty(move_artifact, prompt), 0)
        self.assertEqual(artifact_action_alignment_penalty(copy_artifact, prompt), 12)

    def test_direct_resolution_prompt_can_select_invokable_loaded_ability(self) -> None:
        """
        High Level Purpose:
            In circumstances like device-style action prompts that are not written as numeric compute requests, helps with proving that the governed prior-learning lookup can still promote a reusable invokable ability from the loaded pool instead of falling back to a new structured-learning record.

        Reference to Theory:
            Verifies the implemented theory, especially the controller rules that govern executable reuse and direct resolution.

        Example Input Output:
            Input: `test_direct_resolution_prompt_can_select_invokable_loaded_ability()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Open Google Chrome to https://google.com.")
        state.controller_features.supported_executors = ["bash", "python3"]
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-browser-python-function",
            artifact_type=ArtifactType.ABILITY,
            title="Device User Capabilities 01 — Launch Browser At Specific URL / Python Function",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when the user wants a named browser opened at a URL",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "url": "target web address",
                    "browser": "browser application name",
                },
                "output_contract": {"result": "execution result"},
            },
            justification="A reusable browser launch function.",
            constraints=["derive browser name and URL from the prompt"],
        )
        state.learned_artifacts[artifact.id] = artifact
        root = state.root()

        lookup = controller.lookup_prior_non_achievedness(root)
        answer_artifact = lookup.get("answer_artifact")
        self.assertIsNotNone(answer_artifact)
        self.assertEqual(answer_artifact.id, artifact.id)
        self.assertEqual(
            controller.derive_artifact_invocation_payload(
                answer_artifact,
                semantic_unit="Open Google Chrome to https://google.com.",
            ),
            {
                "url": "https://google.com",
                "browser": "Google Chrome",
            },
        )

    def test_mount_list_prompt_prefers_list_skill_over_append_skill(self) -> None:
        """
        High Level Purpose:
            In circumstances like mount-oriented Python skills that share similar argument shapes, helps with proving that action-family ranking prefers the list-directory skill over an append-text skill for a list prompt.

        Reference to Theory:
            Verifies the executable selection guard that keeps payload completeness from outranking the requested action semantics.

        Example Input Output:
            Input: `test_mount_list_prompt_prefers_list_skill_over_append_skill()`
            Output: None
        """
        state = SystemState.bootstrap("List the entries in mount `skill_input` at `trials`.")
        state.controller_features.supported_executors = ["python3"]
        controller = BSSCController(state, llm_policy="off")

        list_artifact = Artifact(
            id="artifact-list-dir",
            artifact_type=ArtifactType.ABILITY,
            title="Python Commands 01 — List Directory Entries / Python Commands 01 List Directory Entries",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when entries from a mounted directory should be listed",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "question": "How do you use python commands 01 list directory entries from mount, relative_path?",
                "input_contract": {"mount": "required input value", "relative_path": "required input value"},
                "output_contract": {"result": "execution result"},
            },
            justification="A mount-list ability.",
        )
        append_artifact = Artifact(
            id="artifact-append-text",
            artifact_type=ArtifactType.ABILITY,
            title="Python Commands 04 — Append Text File / Python Commands 04 Append Text File",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when text should be appended to a mounted file path",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "executor_framework": "python3",
                "dependencies": ["msgspec", "orjson"],
                "question": "How do you use python commands 04 append text file from mount, relative_path, text?",
                "input_contract": {"mount": "required input value", "relative_path": "required input value", "text": "required input value"},
                "output_contract": {"result": "execution result"},
            },
            justification="A mounted append-text ability.",
        )

        state.learned_artifacts[list_artifact.id] = list_artifact
        state.learned_artifacts[append_artifact.id] = append_artifact
        lookup = controller.lookup_prior_non_achievedness(state.root())
        answer_artifact = lookup.get("answer_artifact")

        self.assertIsNotNone(answer_artifact)
        self.assertEqual(answer_artifact.id, list_artifact.id)

    def test_compute_prompt_prefers_invokable_function_over_structured_learning_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing compute prompt prefers invokable function over structured learning record.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_compute_prompt_prefers_invokable_function_over_structured_learning_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi to name='Ada'.")
        controller = BSSCController(state, llm_policy="off")
        function_artifact = Artifact(
            id="artifact-personalized-hi",
            artifact_type=ArtifactType.ABILITY,
            title="Personalized Greeter",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when a greeting must be computed from a provided name",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Say hi to name='Ada'.",
                "python_script": """
# /// script
# requires-python = \">=3.11\"
# dependencies = [\"msgspec\", \"orjson\"]
# ///
from __future__ import annotations
import sys
import msgspec
import orjson

class OutputPayload(msgspec.Struct, kw_only=True):
    status: str
    answer: str
    result: dict[str, str]
    notes: list[str] = []

def main() -> None:
    payload = orjson.loads(sys.stdin.buffer.read() or b"{}")
    name = str(payload.get("name", "")).strip()
    result = OutputPayload(status=\"ok\", answer=f\"hi, {name}\", result={\"greeting\": f\"hi, {name}\"})
    sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result)))
    sys.stdout.buffer.write(b\"\\n\")

if __name__ == \"__main__\":
    main()
                """.strip(),
                "entrypoint": "main",
                "script_language": "python",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {"name": "name to greet"},
                "output_contract": {"greeting": "string greeting"},
                "structured_learning": {
                    "encountered_not": "Say Hi Ada",
                    "action_posture": "compute_or_template",
                    "lookup_keys": ["say hi ada"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Reusable greeting function.",
            constraints=["use when a greeting must be produced from the supplied name"],
        )
        structured_record = Artifact(
            id="artifact-structured-record",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Say Hi",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when the same prompt family reappears",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Say hi to name='Ada'.",
                "answer": "",
                "structured_learning": {
                    "encountered_not": "Say Hi Ada",
                    "action_posture": "compute_or_template",
                    "lookup_keys": ["say hi ada"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Structured non-achievedness record only.",
            constraints=["support reuse but do not substitute for executable closure"],
        )

        function_rank = controller.answer_candidate_rank(
            function_artifact,
            semantic_unit="Say hi to name='Ada'.",
            current_boundary_shape=state.root().boundary_shape,
        )
        record_rank = controller.answer_candidate_rank(
            structured_record,
            semantic_unit="Say hi to name='Ada'.",
            current_boundary_shape=state.root().boundary_shape,
        )

        self.assertLess(function_rank, record_rank)

    def test_direct_knowledge_focus_alignment_reuse_can_close(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that a focus-aligned direct knowledge reuse is strong enough to close a direct explanatory prompt.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_knowledge_focus_alignment_reuse_can_close()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("What is mass conservation in a reaction?")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-conservation-broad",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Chemistry Relations 01 Conservation of Amount / Conservation",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for chemistry conservation questions",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is conservation?",
                "answer": "Mass conservation in a reaction means the total mass remains unchanged across the full counted system.",
                "structured_learning": {
                    "encountered_not": "Conservation",
                    "lookup_keys": ["mass conservation", "conservation"],
                    "component_nots": ["Conservation"],
                    "composed_not": "Conservation Of Amount",
                    "notation_yaml": "",
                },
            },
            justification="Broader answer-bearing knowledge artifact.",
        )
        state.learned_artifacts[artifact.id] = artifact
        root = state.root()

        controller.lookup_prior_non_achievedness = lambda node: {
            "current": controller.structured_learning_view(node),
            "match_kind": "none",
            "matched_artifacts": [artifact],
            "answer_artifact": artifact,
            "answer_match_kind": "focus_alignment",
            "answer_preference": "focus_alignment",
            "matched_lookup_keys": ["mass conservation"],
        }

        attached = controller.instantiate_reusable_artifact_support(root)
        self.assertTrue(attached)
        self.assertTrue(root.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("mass remains unchanged", str(root.metadata.get("direct_resolution_answer", "")).lower())

    def test_related_solution_support_prefers_invokable_function(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing related solution support prefers invokable function.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_related_solution_support_prefers_invokable_function()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi to name='Ada'.")
        controller = BSSCController(state, llm_policy="off")

        function_artifact = self.make_hi_artifact()
        function_artifact.id = "artifact-hi-function-with-name"
        function_artifact.title = "Personalized Greeter"
        function_artifact.content["question"] = "Say hi to name='Ada'."
        function_artifact.content["input_contract"] = {"name": "name to greet"}
        function_artifact.content["structured_learning"] = {
            "encountered_not": "Say Hi Ada",
            "goal": "Say hi to name='Ada'.",
            "action_posture": "compute_or_template",
            "lookup_keys": ["say hi ada"],
            "component_nots": [],
            "composed_not": "",
            "notation_yaml": "",
        }
        function_artifact.content["python_script"] = """
# /// script
# requires-python = \">=3.11\"
# dependencies = [\"msgspec\", \"orjson\"]
# ///
from __future__ import annotations
import sys
import msgspec
import orjson

class OutputPayload(msgspec.Struct, kw_only=True):
    status: str
    answer: str
    result: dict[str, str]

def main() -> None:
    payload = orjson.loads(sys.stdin.buffer.read() or b"{}")
    name = str(payload.get("name", "")).strip()
    result = OutputPayload(status=\"ok\", answer=f\"hi, {name}\", result={\"greeting\": f\"hi, {name}\"})
    sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result)))
    sys.stdout.buffer.write(b\"\\n\")

if __name__ == \"__main__\":
    main()
        """.strip()

        record_artifact = Artifact(
            id="artifact-structured-record",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Say Hi",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when the same prompt family reappears",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Say hi to name='Ada'.",
                "answer": "",
                "structured_learning": {
                    "encountered_not": "Say Hi Ada",
                    "goal": "Say hi to name='Ada'.",
                    "action_posture": "compute_or_template",
                    "lookup_keys": ["say hi ada"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Structured record only.",
            constraints=[],
        )

        state.artifacts[function_artifact.id] = function_artifact
        state.artifacts[record_artifact.id] = record_artifact

        support = controller.derive_related_solution_support(
            {
                "goal": "Say hi to name='Ada'.",
                "encountered_not": "Say Hi Ada",
                "boundary_shape": ["a*", "d*"],
                "action_posture": "compute_or_template",
                "lookup_keys": ["say hi ada"],
                "component_nots": [],
                "composed_not": "",
            },
            [record_artifact.id, function_artifact.id],
        )

        self.assertEqual(support["source_artifact_id"], function_artifact.id)
        self.assertEqual(support["answer"], "hi, Ada")

    def test_zero_input_function_artifact_executes(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing zero input function artifact executes.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_zero_input_function_artifact_executes()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi.")
        controller = BSSCController(state, llm_policy="off")
        artifact = self.make_hi_artifact()
        execution = controller.execute_function_artifact(
            artifact,
            semantic_unit="Say hi.",
        )
        self.assertTrue(execution.ok)
        self.assertEqual(execution.answer, "hi")

    def test_discovery_harvest_derives_ability_from_python_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing discovery harvest derives ability from python answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_discovery_harvest_derives_ability_from_python_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Write a Python function that calculates a z-score from x, mean, and standard deviation.")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["direct_resolution_answer"] = """
def z_score(x, mean, std):
    if std == 0:
        raise ValueError("Standard deviation must be non-zero")
    return (x - mean) / std
        """.strip()
        root.metadata["direct_resolution_answer_kind"] = "direct_answer"
        state.run_outcome = RunOutcome.COMPLETED

        audit = controller.fallback_discovery_audit(root)
        artifacts = audit.get("artifacts", [])
        ability = next((item for item in artifacts if item.get("artifact_type") == "ability"), None)

        self.assertIsNotNone(ability)
        self.assertEqual(ability.get("function_bit"), 1)
        self.assertEqual(ability.get("representation"), "python_script")
        content = ability.get("content", {})
        self.assertIn("python_script", content)
        self.assertIn("# /// script", content["python_script"])
        self.assertEqual(sorted(content.get("input_contract", {}).keys()), ["mean", "std", "x"])
        execution = cross_boundary(
            str(content.get("python_script", "")),
            {"x": 12, "mean": 10, "std": 2},
        )
        self.assertTrue(execution.ok)
        self.assertEqual(execution.answer, "1")

    def test_perform_discovery_harvest_injects_derived_python_ability(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing perform discovery harvest injects derived python ability.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_perform_discovery_harvest_injects_derived_python_ability()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Write a Python function that calculates a z-score from x, mean, and standard deviation.")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["direct_resolution_answer"] = """
def z_score(x, mean, std):
    if std == 0:
        raise ValueError("Standard deviation must be non-zero")
    return (x - mean) / std
        """.strip()
        root.metadata["direct_resolution_answer_kind"] = "direct_answer"
        state.run_outcome = RunOutcome.COMPLETED

        controller.propose_discovery_audit = lambda node: ProposalObject(
            id="proposal-discovery-test",
            proposal_type=ProposalType.DISCOVERY_AUDIT,
            target_scope=node.semantic_unit,
            originating_not_id=node.id,
            mode=SupplementMode.DEEP,
            prompt_state_reference={},
            revision_count=1,
            governance_status=ProposalGovernanceStatus.ADMITTED,
            payload={"pain_class": "no_pain", "gain_class": "gain", "gain_types": ["knowledge"], "enablers": [], "diagnostics": [], "artifacts": [], "immediate_learning": []},
            source="heuristic",
            provider="test",
            model="test",
            rationale="test",
        )

        audit = controller.perform_discovery_harvest(root)
        harvested = [state.artifacts.get(artifact_id) for artifact_id in audit.artifact_ids]
        ability = next((item for item in harvested if item and item.artifact_type == ArtifactType.ABILITY), None)

        self.assertIsNotNone(ability)
        self.assertEqual(ability.function_bit, 1)
        self.assertIn("# /// script", str(ability.content.get("python_script", "")))

    def test_compute_prompt_matches_generic_executable_family_with_numeric_inputs(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing compute prompt matches generic executable family with numeric inputs.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_compute_prompt_matches_generic_executable_family_with_numeric_inputs()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Write a Python script that computes the z-score for x=12, mean=10, std=2.")
        controller = BSSCController(state, llm_policy="off")
        artifact = Artifact(
            id="artifact-z-score-ability",
            artifact_type=ArtifactType.ABILITY,
            title="Python Z Score Ability",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse when the user asks to compute or script z score in Python under compatible named inputs",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you compute z score in Python?",
                "python_script": FORCE_SCRIPT,
                "entrypoint": "main",
                "script_language": "python",
                "dependencies": ["msgspec", "orjson"],
                "input_contract": {
                    "x": "required input value",
                    "mean": "required input value",
                    "std": "required input value",
                },
                "output_contract": {"result": "computed result"},
                "structured_learning": {
                    "encountered_not": "Python Z Score",
                    "goal": "Compute z score in Python from named inputs.",
                    "action_posture": "compute_or_template",
                    "lookup_keys": [
                        "python z score",
                        "z score function",
                        "z score script",
                        "z score x",
                        "z score mean",
                        "z score std",
                    ],
                    "component_nots": ["Z Score", "Inputs X Mean Std"],
                    "composed_not": "Python Z Score Function",
                    "notation_yaml": "",
                },
            },
            justification="Reusable executable z-score family.",
            constraints=["invoke only with x, mean, and std"],
        )
        current = controller.structured_learning_view(state.root())
        prior = controller.artifact_structured_learning_view(artifact)
        preference = controller.answer_reuse_preference(current, prior, artifact)
        self.assertIn(preference, {"covers_components", "lookup_overlap", "same_composed_family"})


if __name__ == "__main__":
    unittest.main()
