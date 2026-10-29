# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from realized_core_runtime.fence_extraction import build_fence_strategy_report
from realized_core_runtime.fence_extraction import extract_markdown_fences
from realized_core_runtime.fence_extraction import fence_strategy_for_record


class FenceExtractionStrategyTests(unittest.TestCase):
    def test_extracts_python_fence_with_heading_path(self) -> None:
        markdown = """# Device User

## Executable Python relation

This section teaches a reusable device action.

```python
def main(
    url: str,
    *,
    browser: str = "Google Chrome",
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    import subprocess

    subprocess.run(["open", "-a", browser, url], check=True)
    return {"status": "opened", "browser": browser, "url": url}
```
"""
        records = extract_markdown_fences(markdown, source_path="/tmp/device.md")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].language, "python")
        self.assertEqual(records[0].heading_path, ["Device User", "Executable Python relation"])

    def test_python_strategy_detects_main_signature_and_calls(self) -> None:
        markdown = """# Device User

## Executable Python relation

```python
def main(
    text: str,
    *,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, str]:
    import subprocess

    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    return {"status": "copied", "text": text}
```
"""
        record = extract_markdown_fences(markdown, source_path="/tmp/clipboard.md")[0]
        strategy = fence_strategy_for_record(record)
        self.assertTrue(strategy.executable)
        self.assertEqual(strategy.entrypoint_name, "main")
        self.assertEqual(strategy.parameter_names, ["text"])
        self.assertEqual(strategy.dependency_metadata_kind, "signature_inline")
        self.assertIn("subprocess", strategy.inline_imports)
        self.assertTrue(any("pbcopy" in call for call in strategy.detected_calls))

    def test_shell_strategy_marks_shell_blocks_as_executable(self) -> None:
        markdown = """# Device User

## Core command

```bash
open -a "Google Chrome" "https://example.com"
```
"""
        record = extract_markdown_fences(markdown, source_path="/tmp/browser.md")[0]
        strategy = fence_strategy_for_record(record)
        self.assertTrue(strategy.executable)
        self.assertEqual(strategy.strategy_name, "shell_command_block")
        self.assertEqual(strategy.recommended_representation, "shell_script")

    def test_report_supports_multiple_languages(self) -> None:
        markdown = """# Mixed

## Python

```python
def main(x: int, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, int]:
    import subprocess
    return {"x": x}
```

## AppleScript

```applescript
tell application "Finder" to activate
```
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "mixed.md"
            path.write_text(markdown, encoding="utf-8")
            report = build_fence_strategy_report([str(path)])
        self.assertEqual(report["document_count"], 1)
        self.assertEqual(report["fence_count"], 2)
        strategy_names = [item["strategy_name"] for item in report["documents"][0]["strategies"]]
        self.assertIn("python_main_entrypoint", strategy_names)
        self.assertIn("generic_fenced_snippet", strategy_names)


if __name__ == "__main__":
    unittest.main()
