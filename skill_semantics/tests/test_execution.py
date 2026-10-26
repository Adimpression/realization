from __future__ import annotations

import unittest
from collections import UserDict

from realized_skill_semantics import execution


class SkillExecutionSemanticsTests(unittest.TestCase):
    def test_public_constants_preserve_the_portable_descriptor_vocabulary(self) -> None:
        self.assertEqual(
            ("python3", "bash", "ansible", "wasm_wasi"),
            execution.SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES,
        )
        self.assertEqual("python3", execution.EXECUTOR_FRAMEWORK_ALIASES["py"])
        self.assertEqual("bash", execution.EXECUTOR_FRAMEWORK_ALIASES["zsh"])
        self.assertEqual(
            "ansible_playbook",
            execution.EXECUTOR_FRAMEWORK_CONTENT_KEYS["ansible"],
        )
        self.assertEqual(
            "wasm_module",
            execution.EXECUTOR_FRAMEWORK_REPRESENTATIONS["wasm_wasi"],
        )

    def test_name_normalization_preserves_alias_and_unknown_behavior(self) -> None:
        expected = {
            None: "",
            "": "",
            " PY ": "python3",
            "Shell": "bash",
            "ansible-playbook": "ansible",
            "WASMTIME": "wasm_wasi",
            "custom-runner": "custom-runner",
        }
        for value, normalized in expected.items():
            with self.subTest(value=value):
                self.assertEqual(
                    normalized,
                    execution.normalize_executor_framework_name(value),
                )

    def test_content_key_normalizes_aliases_and_retains_fallback(self) -> None:
        self.assertEqual(
            "python_script",
            execution.executor_framework_content_key("python"),
        )
        self.assertEqual(
            "shell_script",
            execution.executor_framework_content_key(" SH "),
        )
        self.assertEqual(
            "executable_body",
            execution.executor_framework_content_key("custom-runner"),
        )

    def test_framework_inference_preserves_precedence(self) -> None:
        cases = (
            (
                "explicit",
                "python_script",
                {"executor_framework": "bash", "python_script": "print(1)"},
                "bash",
            ),
            ("representation", "shell_script", {"script_language": "python"}, "bash"),
            ("script_language", "", {"script_language": "wasi"}, "wasm_wasi"),
            ("python_body", "", {"python_script": "print(1)"}, "python3"),
            ("shell_body", "", {"shell_script": "echo ok"}, "bash"),
            ("ansible_body", "", {"ansible_playbook": "- hosts: all"}, "ansible"),
            ("wasm_body", "", {"wasm_module": "00asm"}, "wasm_wasi"),
            ("unknown_language", "", {"script_language": "custom"}, ""),
            ("non_mapping", "python_script", [], "python3"),
        )
        for label, representation, content, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(
                    expected,
                    execution.ability_executor_framework(
                        representation=representation,
                        content=content,
                    ),
                )

    def test_framework_inference_accepts_alternate_mappings(self) -> None:
        self.assertEqual(
            "ansible",
            execution.ability_executor_framework(
                content=UserDict({"executor_framework": "ansible-playbook"})
            ),
        )

    def test_executable_text_uses_selected_field_and_strips_it(self) -> None:
        self.assertEqual(
            "echo ok",
            execution.ability_executable_text(
                content={
                    "executor_framework": "bash",
                    "shell_script": "  echo ok\n",
                    "python_script": "must not win",
                }
            ),
        )
        self.assertEqual(
            "42",
            execution.ability_executable_text(
                content={"executor_framework": "custom", "executable_body": 42}
            ),
        )
        self.assertEqual("", execution.ability_executable_text(content=None))


if __name__ == "__main__":
    unittest.main()
