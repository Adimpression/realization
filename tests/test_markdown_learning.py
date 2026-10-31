# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
MAIN_COMMAND = (sys.executable, "-m", "main")
MARKDOWN_SOURCE = ROOT / "LEARN_NEWTOWNS_LAWS.md"
if not MARKDOWN_SOURCE.exists():
    MARKDOWN_SOURCE = ROOT / "trials" / "LEARN_NEWTOWNS_LAWS.md"
LOCAL_ENV = ROOT / "local.env"


def load_local_env() -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with loading local environment variables from disk.

    Reference to Theory:
        Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

    Example Input Output:
        Input: `load_local_env()`
        Output: {'OPENAI_API_KEY': 'test-key'}

    Args:
        None.

    Returns:
        dict[str, str]: Result produced by `load_local_env`.
    """
    if not LOCAL_ENV.exists():
        return {}
    result: dict[str, str] = {}
    for raw_line in LOCAL_ENV.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def configured_environment() -> dict[str, str]:
    """Load local defaults without overriding an explicit process setting."""
    env = os.environ.copy()
    for key, value in load_local_env().items():
        env.setdefault(key, value)
    return env


class MarkdownLearningEnvironmentTests(unittest.TestCase):
    def test_explicit_provider_off_setting_wins_over_local_defaults(self) -> None:
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            self.assertEqual(configured_environment().get("OPENAI_API_KEY"), "")


class MarkdownLearningNewtonTests(unittest.TestCase):
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
        env = configured_environment()
        if not env.get("OPENAI_API_KEY"):
            raise unittest.SkipTest("OPENAI_API_KEY is not configured in the environment or local.env.")

        cls.tempdir = tempfile.TemporaryDirectory(prefix="markdown_learning_newton_")
        cls.sqlite_path = str(Path(cls.tempdir.name) / "newton_learning.sqlite3")
        cls.report_path = Path(cls.tempdir.name) / "markdown_learn_report.json"
        env.pop("STATE_DB_URL", None)
        env.pop("STATE_DB_PORT", None)
        env.pop("STATE_DB_NAME", None)
        env.pop("STATE_DB_USER", None)
        env.pop("STATE_DB_PASSWORD", None)
        env["STATE_SQLITE_PATH"] = cls.sqlite_path
        env["LLM_PROVIDER"] = "openai"
        env["LLM_TIMEOUT_SECONDS"] = env.get("LLM_TIMEOUT_SECONDS", "180")
        cls.env = env

        learn_cmd = [
            *MAIN_COMMAND,
            "markdown-learn",
            "--markdown-file",
            str(MARKDOWN_SOURCE),
            "--llm",
            "required",
            "--max-artifacts",
            "8",
            "--report-out",
            str(cls.report_path),
        ]
        completed = None
        last_error = None
        for attempt_index in range(3):
            try:
                completed = subprocess.run(
                    learn_cmd,
                    cwd=str(ROOT),
                    env=cls.env,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                last_error = None
                break
            except subprocess.CalledProcessError as exc:
                last_error = exc
                if attempt_index < 2:
                    time.sleep(min(3 * (attempt_index + 1), 6))
        if completed is None:
            raise last_error  # type: ignore[misc]
        cls.learn_report = json.loads(completed.stdout)

    @classmethod
    def tearDownClass(cls) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling tearDownClass.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `tearDownClass()`
            Output: None

        Args:
            cls: Bound class used to construct or inspect class-level behavior.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        cls.tempdir.cleanup()

    def run_probe(self, prompt: str) -> dict[str, object]:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling run probe.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `run_probe(prompt='Compute force from mass and acceleration.')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            prompt: Value for `prompt` used by `run_probe`. Expected type: `str`.

        Returns:
            dict[str, object]: Result produced by `run_probe`.
        """
        completed = subprocess.run(
            [
                *MAIN_COMMAND,
                "run",
                "--prompt",
                prompt,
                "--llm",
                "off",
                "--max-steps",
                "24",
            ],
            cwd=str(ROOT),
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout)

    def run_probe_with_state(self, prompt: str) -> tuple[dict[str, object], dict[str, object]]:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling run probe with state.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `run_probe_with_state(prompt='Compute force from mass and acceleration.')`
            Output: {'controller_features': {'discovery_enabled': False, 'reflection_enabled': True, 'contemplation_enabled': True}}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            prompt: Value for `prompt` used by `run_probe_with_state`. Expected type: `str`.

        Returns:
            tuple[dict[str, object], dict[str, object]]: Result produced by `run_probe_with_state`.
        """
        state_path = Path(self.tempdir.name) / f"state_{abs(hash(prompt))}.json"
        completed = subprocess.run(
            [
                *MAIN_COMMAND,
                "run",
                "--prompt",
                prompt,
                "--llm",
                "off",
                "--max-steps",
                "24",
                "--state-out",
                str(state_path),
            ],
            cwd=str(ROOT),
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout), json.loads(state_path.read_text())

    def test_markdown_learning_persists_artifacts(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing markdown learning persists artifacts.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_markdown_learning_persists_artifacts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(self.learn_report["run_outcome"], "completed")
        self.assertGreaterEqual(int(self.learn_report["learned_count"]), 4)
        titles = {str(item["title"]) for item in self.learn_report["learned_artifacts"]}
        self.assertTrue(any("First Law" in title for title in titles))
        self.assertTrue(any("Second Law" in title for title in titles))
        self.assertTrue(any("Third Law" in title for title in titles))
        self.assertTrue(any("/" in title and "First Law" in title for title in titles))

        connection = sqlite3.connect(self.sqlite_path)
        try:
            artifact_count = connection.execute("SELECT COUNT(*) FROM bssc_artifacts").fetchone()[0]
            function_artifact_count = connection.execute(
                "SELECT COUNT(*) FROM bssc_artifacts WHERE artifact_type = 'ability' AND function_bit = 1"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertGreaterEqual(int(artifact_count), 4)
        self.assertGreaterEqual(int(function_artifact_count), 1)

    def test_first_law_reuse_without_llm(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing first law reuse without llm.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_first_law_reuse_without_llm()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        result = self.run_probe("What is Newton's first law of motion?")
        self.assertEqual(result["run_outcome"], "completed")
        self.assertFalse(result["llm"]["enabled"])
        answer = str(result.get("final_answer") or "").lower()
        self.assertTrue("external force" in answer or "uniform motion" in answer or "remain at rest" in answer)

    def test_second_law_reuse_without_llm(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing second law reuse without llm.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_second_law_reuse_without_llm()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        result = self.run_probe("What is Newton's second law of motion?")
        self.assertEqual(result["run_outcome"], "completed")
        self.assertFalse(result["llm"]["enabled"])
        answer = str(result.get("final_answer") or "").lower()
        self.assertTrue("f = m * a" in answer or "acceleration" in answer or ("force" in answer and "mass" in answer))

    def test_third_law_reuse_without_llm(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing third law reuse without llm.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_third_law_reuse_without_llm()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        result = self.run_probe("What is Newton's third law of motion?")
        self.assertEqual(result["run_outcome"], "completed")
        self.assertFalse(result["llm"]["enabled"])
        answer = str(result.get("final_answer") or "").lower()
        self.assertTrue("equal and opposite" in answer or "action" in answer and "reaction" in answer)

    def test_force_calculation_reuse_without_llm(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing force calculation reuse without llm.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_force_calculation_reuse_without_llm()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        result = self.run_probe("Calculate force for mass=3 and acceleration=4.")
        self.assertEqual(result["run_outcome"], "completed")
        self.assertFalse(result["llm"]["enabled"])
        answer = str(result.get("final_answer") or "").strip().lower()
        self.assertTrue(answer in {"12", "12.0"})

    def test_force_calculation_uses_cross_boundary_function(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing force calculation uses cross boundary function.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_force_calculation_uses_cross_boundary_function()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        result, state = self.run_probe_with_state("Use Newton's second law to compute force with mass=5 and acceleration=2.")
        self.assertEqual(result["run_outcome"], "completed")
        self.assertFalse(result["llm"]["enabled"])
        answer = str(result.get("final_answer") or "").strip().lower()
        self.assertTrue(answer in {"10", "10.0"})

        evidence_items = list((state.get("evidence") or {}).values())
        evidence_contexts = [
            item.get("context", {})
            for item in evidence_items
            if isinstance(item, dict)
        ]
        self.assertTrue(any(bool(context.get("cross_boundary_execution")) for context in evidence_contexts))
        self.assertTrue(
            any(int(context.get("function_bit", 0)) == 1 for context in evidence_contexts)
        )


if __name__ == "__main__":
    unittest.main()
