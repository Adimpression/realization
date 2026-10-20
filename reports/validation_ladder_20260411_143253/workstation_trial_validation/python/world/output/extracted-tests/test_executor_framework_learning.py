# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
import os
from pathlib import Path

from execution_frameworks import (
    execute_cross_boundary,
    fence_encounter_ability_payload,
    normalize_ability_runtime_content,
    normalize_supported_executor_frameworks,
    supported_fence_learning_records,
)
from skill_schema_io import artifact_from_skill_document
from main import BSSCController, SystemState
from semantic_text import titleize_semantic_unit


class ExecutorFrameworkLearningTests(unittest.TestCase):
    def test_normalize_supported_executor_frameworks_collapses_aliases(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over pluggable executor configuration, helps with checking that executor aliases collapse into the stable supported set used by the controller.

        Reference to Theory:
            Verifies the implemented theory, especially the governed external-boundary rules for executable artifacts.

        Example Input Output:
            Input: `test_normalize_supported_executor_frameworks_collapses_aliases()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(
            normalize_supported_executor_frameworks(["python", "sh", "ansible-playbook"]),
            ["python3", "bash", "ansible"],
        )

    def test_supported_fence_learning_records_reports_unsupported_fences(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over mixed fenced markdown corpora, helps with checking that unsupported executable fences are reported explicitly instead of being silently ignored.

        Reference to Theory:
            Verifies the implemented theory, especially the governed external-boundary rules for executable artifacts.

        Example Input Output:
            Input: `test_supported_fence_learning_records_reports_unsupported_fences()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Mixed

## Browser

```bash
open -a "Google Chrome" "$url"
```

## Finder

```applescript
tell application "Finder" to activate
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "mixed.md"
            path.write_text(markdown, encoding="utf-8")
            supported, failures = supported_fence_learning_records(
                path,
                supported_executors=["bash"],
            )
        self.assertEqual(len(supported), 1)
        self.assertEqual(supported[0]["executor_framework"], "bash")
        self.assertEqual(supported[0]["parameter_names"], ["url"])
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["message"], "no plugged in executor supports applescript")
        self.assertEqual(supported[0]["artifact_title_hint"], "Browser")

    def test_supported_fence_learning_records_use_non_generic_parent_heading_as_title_hint(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over fenced executable learning, helps with checking that generic local scaffold headings do not become the learned capability title hint when a better semantic parent heading exists.

        Reference to Theory:
            Verifies the implemented theory, especially the governed external-boundary rules for executable artifacts.

        Example Input Output:
            Input: `test_supported_fence_learning_records_use_non_generic_parent_heading_as_title_hint()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Launch Browser At Specific URL

## Executable Python relation

```bash
open -a "Google Chrome" "$url"
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "browser.md"
            path.write_text(markdown, encoding="utf-8")
            supported, failures = supported_fence_learning_records(
                path,
                supported_executors=["bash"],
            )
        self.assertEqual(failures, [])
        self.assertEqual(len(supported), 1)
        self.assertEqual(
            supported[0]["artifact_title_hint"],
            titleize_semantic_unit("Launch Browser At Specific URL"),
        )

    def test_execute_cross_boundary_runs_bash_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over pluggable executor dispatch, helps with checking that bash-backed executable artifacts can cross the runtime boundary and return structured output.

        Reference to Theory:
            Verifies the implemented theory, especially the governed external-boundary rules for executable artifacts.

        Example Input Output:
            Input: `test_execute_cross_boundary_runs_bash_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        script = """#!/usr/bin/env bash
set -euo pipefail
printf '{"status":"ok","answer":"opened","result":{"url":"%s"},"notes":[]}\n' "$url"
"""
        result = execute_cross_boundary(
            framework="bash",
            executable_text=script,
            stdin_payload={"url": "https://google.com"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.answer, "opened")
        self.assertEqual(result.result, {"url": "https://google.com"})

    def test_fence_encounter_ability_payload_brokerizes_python_browser_open(self) -> None:
        """
        High Level Purpose:
            In circumstances like learning fenced Python host-effect skills from markdown, helps with checking that a recognized browser-launch snippet is rewritten to the governed broker API instead of preserving raw subprocess access.

        Reference to Theory:
            Verifies the broker-first learning step of the bundle plan so Python-hosted skills prefer named mediated host brokers at learn time.

        Example Input Output:
            Input: `test_fence_encounter_ability_payload_brokerizes_python_browser_open()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = fence_encounter_ability_payload(
            {
                "heading": "Launch Browser At Specific URL",
                "path": ["Launch Browser At Specific URL", "Executable Python relation"],
                "sections": ["Launch Browser At Specific URL"],
                "executor_framework": "python3",
                "entrypoint_name": "main",
                "parameter_names": ["url", "browser"],
                "bullets": [],
                "code_blocks": [
                    "\n".join(
                        [
                            "def main(",
                            "    url: str,",
                            "    *,",
                            '    browser: str = "Google Chrome",',
                            "    __dependencies__: tuple[str, ...] = (),",
                            ") -> dict[str, str]:",
                            "    import subprocess",
                            "",
                            '    subprocess.run(["open", "-a", browser, url], check=True)',
                            '    return {"status": "opened", "browser": browser, "url": url}',
                        ]
                    )
                ],
            }
        )
        self.assertIsNotNone(payload)
        content = dict(payload["content"])
        self.assertIn("from python_skill_host import broker_request", content["python_script"])
        self.assertIn('broker_request("macos.open_browser"', content["python_script"])
        self.assertEqual(content["governed_host_brokers"], ["macos.open_browser"])
        self.assertEqual(content["governed_authorities"], ["execute"])

    def test_fence_encounter_ability_payload_brokerizes_python_directory_listing(self) -> None:
        """
        High Level Purpose:
            In circumstances like learning bounded Python filesystem-read skills from markdown, helps with checking that direct directory listing is rewritten to a brokered filesystem read surface.

        Reference to Theory:
            Verifies that Python host-effect learning can move filesystem inspection behind named brokers while preserving the caller-facing function contract.

        Example Input Output:
            Input: `test_fence_encounter_ability_payload_brokerizes_python_directory_listing()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = fence_encounter_ability_payload(
            {
                "heading": "List Directory Entries",
                "path": ["List Directory Entries", "Executable Python relation"],
                "sections": ["List Directory Entries"],
                "executor_framework": "python3",
                "entrypoint_name": "main",
                "parameter_names": ["path"],
                "bullets": [],
                "code_blocks": [
                    "\n".join(
                        [
                            "def main(path: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, object]:",
                            "    from pathlib import Path",
                            "",
                            "    entries = sorted(item.name for item in Path(path).iterdir())",
                            '    return {"status": "listed", "path": path, "entries": entries}',
                        ]
                    )
                ],
            }
        )
        self.assertIsNotNone(payload)
        content = dict(payload["content"])
        self.assertIn('broker_request("fs.list_directory"', content["python_script"])
        self.assertEqual(content["governed_host_brokers"], ["fs.list_directory"])
        self.assertEqual(content["governed_authorities"], ["execute", "read"])

    def test_artifact_from_skill_document_normalizes_bash_screenshot_skill_to_mount_aware_runtime(self) -> None:
        """
        High Level Purpose:
            In circumstances like importing a prebuilt bash screenshot skill bundle, helps with checking that runtime normalization upgrades the literal example-path shell body into a governed mount-aware script.

        Reference to Theory:
            Verifies that imported legacy bundle artifacts can still be normalized into the shared governed runtime surface instead of preserving unsafe example-path literals verbatim.

        Example Input Output:
            Input: `test_artifact_from_skill_document_normalizes_bash_screenshot_skill_to_mount_aware_runtime()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": "Device User Capabilities 10 — Capture Screenshot To File / Device User Capabilities 10 Capture Screenshot To File",
                "declaration": {
                    "intent": "Capture a screenshot to a governed output path.",
                    "inputs": {"payload": "execution input"},
                    "outputs": {"result": "execution result"},
                    "authorities_requested": ["execute"],
                    "authority_bounds": {
                        "execute": {
                            "scope": "local_executor",
                            "target": "bash_skill_runtime",
                            "context": "explicit_user_prompt",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user invokes skill"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": ["shell command execution"],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier1_bounded_transform",
                    "executor_framework": "bash",
                },
                "executor": "bash",
                "entrypoint": "main",
                "inputs": {"payload": "execution input"},
                "outputs": {"result": "execution result"},
                "shell": "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'screencapture \"/Users/example/Desktop/screen.png\"',
                        "printf '%s\\n' '{\"status\":\"ok\",\"answer\":\"executed\",\"result\":{\"status\":\"executed\"},\"notes\":[]}'",
                    ]
                ),
            }
        )
        content = dict(artifact.content)
        self.assertIn("BSSC_VIRTUAL_MOUNTS_JSON", content["shell_script"])
        self.assertIn("PAYLOAD_RELATIVE_PATH", content["shell_script"])
        self.assertEqual(content["governed_host_brokers"], ["macos.capture_screenshot"])
        self.assertEqual(content["governed_authorities"], ["execute", "write"])

    def test_execute_cross_boundary_runs_mount_aware_screenshot_shell_runtime(self) -> None:
        """
        High Level Purpose:
            In circumstances like executing a normalized bash screenshot skill, helps with checking that the shell runtime can resolve nested payload mount/path inputs against virtual mounts and write to the governed target path.

        Reference to Theory:
            Verifies the governed shell runtime can consume shared world context instead of relying on a baked-in example desktop path.

        Example Input Output:
            Input: `test_execute_cross_boundary_runs_mount_aware_screenshot_shell_runtime()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        normalized = normalize_ability_runtime_content(
            {
                "executor_framework": "bash",
                "shell_script": "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'screencapture \"/Users/example/Desktop/screen.png\"',
                        "printf '%s\\n' '{\"status\":\"ok\",\"answer\":\"executed\",\"result\":{\"status\":\"executed\"},\"notes\":[]}'",
                    ]
                ),
                "input_contract": {"payload": "execution input"},
            },
            title="Device User Capabilities 10 — Capture Screenshot To File / Device User Capabilities 10 Capture Screenshot To File",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            mount_root = tmp / "skill_tmp"
            mount_root.mkdir(parents=True, exist_ok=True)
            fakebin = tmp / "fakebin"
            fakebin.mkdir(parents=True, exist_ok=True)
            screencapture = fakebin / "screencapture"
            screencapture.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'target=\"${@: -1}\"',
                        'mkdir -p \"$(dirname \"$target\")\"',
                        'printf \"fake screenshot\\n\" > \"$target\"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            screencapture.chmod(0o755)
            with patch.dict(os.environ, {"PATH": f"{fakebin}{os.pathsep}{os.environ.get('PATH', '')}"}):
                result = execute_cross_boundary(
                    framework="bash",
                    executable_text=str(normalized["shell_script"]),
                    stdin_payload={"payload": {"mount": "skill_tmp", "relative_path": "deviceuser-screen.png"}},
                    host_runtime_context={
                        "virtual_mounts": {
                            "skill_tmp": {"root": str(mount_root)},
                        }
                    },
                )
                self.assertTrue(result.ok)
                self.assertEqual(result.result, {"status": "captured", "mount": "skill_tmp", "relative_path": "deviceuser-screen.png"})
                self.assertTrue((mount_root / "deviceuser-screen.png").exists())

    def test_prose_python_fallback_brokerizes_host_effect_pattern(self) -> None:
        """
        High Level Purpose:
            In circumstances like LLM-off markdown learning from prose-defined Python relations, helps with checking that recognized host-effect patterns are brokerized on the deterministic fallback path too.

        Reference to Theory:
            Verifies that broker-first learning applies consistently across both fenced and prose-derived Python ability extraction.

        Example Input Output:
            Input: `test_prose_python_fallback_brokerizes_host_effect_pattern()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("prose brokerization"), llm_policy="off")
        payload = controller.fallback_markdown_prose_python_ability_payload(
            {
                "heading": "Executable Python relation",
                "sections": ["Launch Application By Name", "Executable Python relation"],
                "encounter_id": "app-launch",
                "paragraphs": [
                    "This capability should be learned as a reusable Python ability artifact.",
                    "The reusable function signature is `main(app: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`."
                ],
                "bullets": [
                    "import `subprocess`",
                    'run `subprocess.run([\"open\", \"-a\", app], check=True)`',
                    'return `{\"status\": \"launched\", \"app\": app}`',
                ],
            }
        )
        self.assertIsNotNone(payload)
        content = dict(payload["content"])
        self.assertIn('broker_request("macos.open_app"', content["python_script"])
        self.assertEqual(content["governed_host_brokers"], ["macos.open_app"])
        self.assertEqual(content["governed_authorities"], ["execute"])

    def test_markdown_learning_learns_bash_ability_and_reports_unsupported_fence(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over deterministic markdown learning from supported fences, helps with checking that supported executor fences become ability artifacts while unsupported fences are preserved as parsing failures.

        Reference to Theory:
            Verifies the implemented theory, especially the governed external-boundary rules for executable artifacts.

        Example Input Output:
            Input: `test_markdown_learning_learns_bash_ability_and_reports_unsupported_fence()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        markdown = """# Device User Capability

## Browser launch

```bash
open -a "Google Chrome" "$url"
```

## Finder launch

```applescript
tell application "Finder" to activate
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "device.md"
            path.write_text(markdown, encoding="utf-8")
            state = SystemState.bootstrap(
                f"Learn from markdown: {path.name}",
                bootstrap_mode="markdown_ingestion",
            )
            state.controller_features.supported_executors = ["bash"]
            controller = BSSCController(state, llm_policy="off")
            report = controller.learn_from_markdown_document(path, max_artifacts=4)
        self.assertGreaterEqual(int(report["learned_count"]), 1)
        self.assertTrue(
            any(item["representation"] == "shell_script" for item in report["learned_artifacts"])
        )
        self.assertEqual(report["supported_executors"], ["bash"])
        self.assertEqual(report["parsing_failures"][0]["message"], "no plugged in executor supports applescript")


if __name__ == "__main__":
    unittest.main()
