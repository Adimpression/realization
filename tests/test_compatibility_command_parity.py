from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = ""
    env["STATE_VECTOR_MODE"] = "off"
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _normalized_output(value: str, aliases: tuple[str, ...]) -> str:
    normalized = value
    for alias in sorted(aliases, key=len, reverse=True):
        normalized = normalized.replace(alias, "<command>")
    return " ".join(normalized.split())


class CompatibilityCommandParityTests(unittest.TestCase):
    def assert_command_parity(
        self,
        *,
        module: str,
        script: str,
        module_program: str,
    ) -> None:
        script_path = Path(sys.executable).with_name(script)
        self.assertTrue(script_path.is_file(), msg=f"missing console script: {script}")
        aliases = (
            str(script_path),
            script,
            f"{Path(sys.executable).name} -m {module}",
            f"python -m {module}",
            module_program,
        )
        for arguments in (["--help"], ["--definitely-invalid-option"]):
            with self.subTest(module=module, arguments=arguments):
                historical = _run([sys.executable, "-m", module, *arguments])
                packaged = _run([str(script_path), *arguments])
                self.assertEqual(historical.returncode, packaged.returncode)
                self.assertEqual(
                    _normalized_output(historical.stdout, aliases),
                    _normalized_output(packaged.stdout, aliases),
                )
                self.assertEqual(
                    _normalized_output(historical.stderr, aliases),
                    _normalized_output(packaged.stderr, aliases),
                )

    def test_main_module_matches_compatibility_console_script(self) -> None:
        self.assert_command_parity(
            module="main",
            script="realized-compatibility",
            module_program="main.py",
        )

    def test_fence_module_matches_fence_console_script(self) -> None:
        self.assert_command_parity(
            module="fence_extraction_strategy",
            script="realized-fence-extraction",
            module_program="fence_extraction_strategy.py",
        )


if __name__ == "__main__":
    unittest.main()
