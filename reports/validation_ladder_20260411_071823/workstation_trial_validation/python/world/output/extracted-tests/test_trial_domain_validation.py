# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from TRIAL_DOMAIN_VALIDATION import (
    ProbeSpec,
    base_env,
    is_transient_markdown_learn_failure,
    learn_retry_delay_seconds_for_attempt,
    learn_timeout_seconds_for_attempt,
    probe_timeout_seconds_for_attempt,
    probe_timeout_seconds_for,
    resolve_domain_skill_bundle,
    run_probe_with_retries,
    run_markdown_learn_with_retries,
)


class TrialDomainValidationTests(unittest.TestCase):
    def test_resolve_domain_skill_bundle_defaults_to_markdown_source_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            bundle = folder / "skill.yaml"
            bundle.write_text("schema: bssc_skill.v2\n")
            previous = os.environ.get("TRIAL_DOMAIN_VALIDATION_USE_BUNDLE")
            try:
                os.environ.pop("TRIAL_DOMAIN_VALIDATION_USE_BUNDLE", None)
                self.assertIsNone(resolve_domain_skill_bundle(folder))
            finally:
                if previous is None:
                    os.environ.pop("TRIAL_DOMAIN_VALIDATION_USE_BUNDLE", None)
                else:
                    os.environ["TRIAL_DOMAIN_VALIDATION_USE_BUNDLE"] = previous

    def test_resolve_domain_skill_bundle_honors_explicit_bundle_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir)
            bundle = folder / "skill.yaml"
            bundle.write_text("schema: bssc_skill.v2\n")
            previous = os.environ.get("TRIAL_DOMAIN_VALIDATION_USE_BUNDLE")
            try:
                os.environ["TRIAL_DOMAIN_VALIDATION_USE_BUNDLE"] = "1"
                self.assertEqual(resolve_domain_skill_bundle(folder), bundle)
            finally:
                if previous is None:
                    os.environ.pop("TRIAL_DOMAIN_VALIDATION_USE_BUNDLE", None)
                else:
                    os.environ["TRIAL_DOMAIN_VALIDATION_USE_BUNDLE"] = previous

    def test_base_env_defaults_validation_runs_to_vector_off(self) -> None:
        previous = os.environ.get("STATE_VECTOR_MODE")        
        try:
            os.environ.pop("STATE_VECTOR_MODE", None)
            env = base_env()
        finally:
            if previous is None:
                os.environ.pop("STATE_VECTOR_MODE", None)
            else:
                os.environ["STATE_VECTOR_MODE"] = previous

        self.assertEqual(env["STATE_VECTOR_MODE"], "off")

    def test_base_env_preserves_explicit_vector_mode_override(self) -> None:
        previous = os.environ.get("STATE_VECTOR_MODE")
        try:
            os.environ["STATE_VECTOR_MODE"] = "on"
            env = base_env()
        finally:
            if previous is None:
                os.environ.pop("STATE_VECTOR_MODE", None)
            else:
                os.environ["STATE_VECTOR_MODE"] = previous

        self.assertEqual(env["STATE_VECTOR_MODE"], "on")

    def test_numeric_probe_timeout_stays_at_default_budget(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing the adaptive trial timeout policy, helps with verifying that short numeric probes keep the baseline timeout instead of paying extra budget meant only for long freeform reasoning prompts.

        Reference to Theory:
            Verifies the practical trial harness boundary so adaptive timeout changes do not distort the faster deterministic probe surface.

        Example Input Output:
            Input: `test_numeric_probe_timeout_stays_at_default_budget()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        probe = ProbeSpec(
            name="force",
            prompt="Calculate force for mass=3 and acceleration=4.",
            expected_mode="numeric",
            expected_value=12.0,
        )

        self.assertEqual(probe_timeout_seconds_for(probe, default_seconds=60), 60)

    def test_short_freeform_probe_timeout_stays_near_default_budget(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing the adaptive trial timeout policy, helps with verifying that ordinary short explanatory prompts do not receive the heavy derivation budget reserved for materially longer reasoning requests.

        Reference to Theory:
            Verifies the practical trial harness boundary so adaptive timeout changes stay proportional to the probe shape rather than flattening all freeform prompts into one slow class.

        Example Input Output:
            Input: `test_short_freeform_probe_timeout_stays_near_default_budget()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        probe = ProbeSpec(
            name="gene_expression",
            prompt="What is gene expression?",
            expected_mode="freeform",
        )

        self.assertEqual(probe_timeout_seconds_for(probe, default_seconds=60), 60)

    def test_long_derivational_freeform_probe_gets_extended_budget(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing the adaptive trial timeout policy, helps with verifying that long derivational prompts asking for explanation and substrate reconstruction receive a materially larger timeout budget than the default.

        Reference to Theory:
            Verifies the practical trial harness boundary so complex reuse/composition probes are not misclassified as failures only because the harness used a brittle uniform timeout.

        Example Input Output:
            Input: `test_long_derivational_freeform_probe_gets_extended_budget()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        probe = ProbeSpec(
            name="molar_mass",
            prompt="Given the relation for molar mass, express how to compute mass from moles and molar mass, and explain how this relates to the reusable substrate.",
            expected_mode="freeform",
        )

        self.assertGreaterEqual(probe_timeout_seconds_for(probe, default_seconds=60), 150)

    def test_formula_explanation_probe_gets_extra_headroom(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing the adaptive trial timeout policy, helps with verifying that short formula-writing prompts that still require explanatory closure receive extra headroom instead of being treated like the fastest factoid prompts.

        Reference to Theory:
            Verifies the practical trial harness boundary so formula-and-variable-role prompts are not misclassified as failures when cold-run execution lands near the baseline timeout.

        Example Input Output:
            Input: `test_formula_explanation_probe_gets_extra_headroom()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        probe = ProbeSpec(
            name="particles_from_moles",
            prompt="Write the formula that relates number of particles to moles, and identify the role of each variable.",
            expected_mode="freeform",
        )

        self.assertGreaterEqual(probe_timeout_seconds_for(probe, default_seconds=60), 90)

    def test_transient_markdown_learn_failure_detects_openai_transport_reset(self) -> None:
        """
        High Level Purpose:
            In circumstances like retrying provider-backed markdown learning during domain validation, helps with verifying that known transient OpenAI transport resets are classified as retryable rather than permanent theory failures.

        Reference to Theory:
            Verifies the practical trial harness boundary so provider instability is separated from controller/runtime failure.

        Example Input Output:
            Input: `test_transient_markdown_learn_failure_detects_openai_transport_reset()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertTrue(
            is_transient_markdown_learn_failure(
                stdout_tail="",
                stderr_tail="openai.InternalServerError: upstream connect error or disconnect/reset before headers. reset reason: connection termination",
            )
        )

    def test_retry_timeout_budget_grows_for_later_markdown_learn_attempts(self) -> None:
        """
        High Level Purpose:
            In circumstances like retrying long markdown-learning lessons after a timeout, helps with verifying that later attempts receive a larger timeout budget than the first attempt.

        Reference to Theory:
            Verifies the practical validation harness boundary so long provider-backed learning work is not prematurely classified as a semantic failure.

        Example Input Output:
            Input: `test_retry_timeout_budget_grows_for_later_markdown_learn_attempts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(learn_timeout_seconds_for_attempt(300, 0), 300)
        self.assertEqual(learn_timeout_seconds_for_attempt(300, 1), 600)
        self.assertEqual(learn_timeout_seconds_for_attempt(300, 2), 900)

    def test_learn_retry_delay_stays_bounded(self) -> None:
        """
        High Level Purpose:
            In circumstances like repeated transient provider failures during domain learning, helps with verifying that the harness adds a short bounded retry delay instead of immediate reconnect churn or unbounded sleeping.

        Reference to Theory:
            Verifies the practical validation harness boundary so provider transport instability is absorbed as bounded harness behavior.

        Example Input Output:
            Input: `test_learn_retry_delay_stays_bounded()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(learn_retry_delay_seconds_for_attempt(0), 0)
        self.assertEqual(learn_retry_delay_seconds_for_attempt(1), 3)
        self.assertEqual(learn_retry_delay_seconds_for_attempt(2), 6)
        self.assertEqual(learn_retry_delay_seconds_for_attempt(10), 15)

    def test_run_markdown_learn_with_retries_retries_once_after_transient_failure(self) -> None:
        """
        High Level Purpose:
            In circumstances like retry-hardening the domain validator, helps with proving that a transient provider failure on the first markdown-learn attempt is retried and that the final result preserves attempt history.

        Reference to Theory:
            Verifies the practical validation harness boundary so transient provider failures do not masquerade as theory regressions.

        Example Input Output:
            Input: `test_run_markdown_learn_with_retries_retries_once_after_transient_failure()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        calls: list[int | None] = []
        attempts = iter(
            [
                CompletedProcess(
                    args=["python3", "main.py", "markdown-learn"],
                    returncode=1,
                    stdout="",
                    stderr="openai.InternalServerError: upstream connect error",
                ),
                CompletedProcess(
                    args=["python3", "main.py", "markdown-learn"],
                    returncode=0,
                    stdout=json.dumps({"timings": {"learn": 1.0}}),
                    stderr="",
                ),
            ]
        )

        def fake_runner(*, cmd, env, cwd, timeout_seconds):
            calls.append(timeout_seconds)
            attempt = next(attempts)
            if isinstance(attempt, BaseException):
                raise attempt
            return attempt

        with tempfile.TemporaryDirectory() as tmp:
            report = run_markdown_learn_with_retries(
                markdown_path=Path(tmp) / "lesson.md",
                report_path=Path(tmp) / "report.json",
                state_path=Path(tmp) / "state.json",
                env={},
                timeout_seconds=300,
                runner=fake_runner,
            )

        self.assertEqual(calls, [300, 600])
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["attempt_count"], 2)
        self.assertEqual(report["attempts"][0]["returncode"], 1)
        self.assertEqual(report["attempts"][1]["returncode"], 0)

    def test_run_markdown_learn_with_retries_honors_explicit_llm_policy_override(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(*, cmd, env, cwd, timeout_seconds):
            calls.append(list(cmd))
            return CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=json.dumps({"timings": {"learn": 1.0}}),
                stderr="",
            )

        with tempfile.TemporaryDirectory() as tmp:
            report = run_markdown_learn_with_retries(
                markdown_path=Path(tmp) / "lesson.md",
                report_path=Path(tmp) / "report.json",
                state_path=Path(tmp) / "state.json",
                env={"TRIAL_MARKDOWN_LEARN_LLM_POLICY": "off"},
                timeout_seconds=300,
                runner=fake_runner,
            )

        self.assertEqual(report["returncode"], 0)
        self.assertEqual(calls[0][calls[0].index("--llm") + 1], "off")

    def test_run_markdown_learn_with_retries_retries_after_timeout_then_transient_failure(self) -> None:
        """
        High Level Purpose:
            In circumstances like long provider-backed domain validation, helps with proving that a timed-out markdown-learn attempt followed by a transient provider error still gets one more bounded retry before the harness classifies the lesson as failed.

        Reference to Theory:
            Verifies the practical validation harness boundary so timeout pressure plus transient provider failure does not masquerade as controller/theory failure.

        Example Input Output:
            Input: `test_run_markdown_learn_with_retries_retries_after_timeout_then_transient_failure()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        calls: list[int | None] = []
        attempts = iter(
            [
                subprocess.TimeoutExpired(cmd=["python3", "main.py", "markdown-learn"], timeout=300),
                CompletedProcess(
                    args=["python3", "main.py", "markdown-learn"],
                    returncode=1,
                    stdout="",
                    stderr="openai.APIConnectionError: Connection error.",
                ),
                CompletedProcess(
                    args=["python3", "main.py", "markdown-learn"],
                    returncode=0,
                    stdout=json.dumps({"timings": {"learn": 1.0}}),
                    stderr="",
                ),
            ]
        )

        def fake_runner(*, cmd, env, cwd, timeout_seconds):
            calls.append(timeout_seconds)
            attempt = next(attempts)
            if isinstance(attempt, BaseException):
                raise attempt
            return attempt

        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"TRIAL_LEARN_RETRIES": "2"}, clear=False):
            report = run_markdown_learn_with_retries(
                markdown_path=Path(tmp) / "lesson.md",
                report_path=Path(tmp) / "report.json",
                state_path=Path(tmp) / "state.json",
                env={},
                timeout_seconds=300,
                runner=fake_runner,
            )

        self.assertEqual(calls, [300, 600, 900])
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["attempt_count"], 3)
        self.assertEqual(report["attempts"][0]["returncode"], -1)
        self.assertEqual(report["attempts"][1]["returncode"], 1)
        self.assertEqual(report["attempts"][2]["returncode"], 0)

    def test_run_markdown_learn_with_retries_handles_multiple_transient_failures_after_timeout(self) -> None:
        """
        High Level Purpose:
            In circumstances like long provider-backed lessons where a timeout is followed by multiple transient connection failures, helps with proving that the harness keeps one more bounded retry window instead of failing too early.

        Reference to Theory:
            Verifies the practical validation harness boundary so repeated transport resets remain separated from controller/theory failure.

        Example Input Output:
            Input: `test_run_markdown_learn_with_retries_handles_multiple_transient_failures_after_timeout()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        calls: list[int | None] = []
        attempts = iter(
            [
                subprocess.TimeoutExpired(cmd=["python3", "main.py", "markdown-learn"], timeout=300),
                CompletedProcess(
                    args=["python3", "main.py", "markdown-learn"],
                    returncode=1,
                    stdout="",
                    stderr="openai.APIConnectionError: Connection error.",
                ),
                CompletedProcess(
                    args=["python3", "main.py", "markdown-learn"],
                    returncode=1,
                    stdout="",
                    stderr="openai.APIConnectionError: Connection error.",
                ),
                CompletedProcess(
                    args=["python3", "main.py", "markdown-learn"],
                    returncode=0,
                    stdout=json.dumps({"timings": {"learn": 1.0}}),
                    stderr="",
                ),
            ]
        )

        def fake_runner(*, cmd, env, cwd, timeout_seconds):
            calls.append(timeout_seconds)
            attempt = next(attempts)
            if isinstance(attempt, BaseException):
                raise attempt
            return attempt

        with tempfile.TemporaryDirectory() as tmp, patch("TRIAL_DOMAIN_VALIDATION.time.sleep") as sleep_mock:
            report = run_markdown_learn_with_retries(
                markdown_path=Path(tmp) / "lesson.md",
                report_path=Path(tmp) / "report.json",
                state_path=Path(tmp) / "state.json",
                env={},
                timeout_seconds=300,
                runner=fake_runner,
            )

        self.assertEqual(calls, [300, 600, 900, 1200])
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["attempt_count"], 4)
        self.assertEqual(sleep_mock.call_count, 2)

    def test_probe_retry_timeout_budget_grows_for_later_attempts(self) -> None:
        """
        High Level Purpose:
            In circumstances like retrying timed-out validation probes, helps with verifying that later attempts receive a larger timeout budget than the first attempt.

        Reference to Theory:
            Verifies the practical validation harness boundary so long-running probe execution is not prematurely classified as semantic failure.

        Example Input Output:
            Input: `test_probe_retry_timeout_budget_grows_for_later_attempts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(probe_timeout_seconds_for_attempt(60, 0), 60)
        self.assertEqual(probe_timeout_seconds_for_attempt(60, 1), 120)

    def test_run_probe_with_retries_retries_once_after_timeout(self) -> None:
        """
        High Level Purpose:
            In circumstances like retry-hardening the domain validator, helps with proving that a timed-out probe is retried once with a larger budget and that the attempt history is preserved.

        Reference to Theory:
            Verifies the practical validation harness boundary so timeout pressure is separated from actual reuse failure.

        Example Input Output:
            Input: `test_run_probe_with_retries_retries_once_after_timeout()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        calls: list[int | None] = []
        probe = ProbeSpec(
            name="force",
            prompt="Calculate force for mass=3 and acceleration=4.",
            expected_mode="numeric",
            expected_value=12.0,
        )

        def fake_runner(*, cmd, env, cwd, timeout_seconds):
            calls.append(timeout_seconds)
            if len(calls) == 1:
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout_seconds)
            return CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="{}",
                stderr="",
            )

        with tempfile.TemporaryDirectory() as tmp:
            report = run_probe_with_retries(
                probe=probe,
                state_path=Path(tmp) / "probe.json",
                env={},
                timeout_seconds=60,
                runner=fake_runner,
            )

        self.assertEqual(calls, [60, 120])
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["attempt_count"], 2)
        self.assertEqual(report["attempts"][0]["returncode"], -1)
        self.assertEqual(report["attempts"][1]["returncode"], 0)
