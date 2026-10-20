from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from build_release_export import build_export
from release_content import load_policy


class ReleaseContentPolicyTests(unittest.TestCase):
    def test_repository_policy_separates_sources_fixtures_and_outputs(self) -> None:
        policy = load_policy(REPO_ROOT)

        self.assertTrue(policy.classify("controller_runtime.py").include)
        self.assertEqual(
            "reviewed-trial-material",
            policy.classify("trials/python/skill.yaml").category,
        )
        self.assertFalse(policy.classify("reports/run/report.json").include)
        self.assertFalse(
            policy.classify("trials/physics/corpus/example/context.json").include
        )
        self.assertFalse(
            policy.classify("trials/LEARN_MOMENTUM_TRIAL.md").include
        )
        self.assertFalse(
            policy.classify("trials/ARTIFACT_ROUND_TRIP_TRIAL.json").include
        )
        self.assertTrue(policy.classify("trials/LEARN_MOMENTUM.md").include)
        self.assertFalse(
            policy.classify(
                "workstation/ui_flutter/android/gradle/wrapper/gradle-wrapper.jar"
            ).include
        )
        generated = policy.classify(
            "workstation/grpc_definitions/src/workstation/grpc/definitions/example_pb2.py"
        )
        self.assertTrue(generated.include)
        self.assertEqual("generated-project-source", generated.provenance.identifier)


class ReleaseExportTests(unittest.TestCase):
    @staticmethod
    def _git(root: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
        )

    def test_export_is_classified_hashed_and_mode_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            source = container / "source"
            source.mkdir()
            (source / "release").mkdir()
            (source / "release" / "release-content.toml").write_text(
                """schema_version = 1
default_include = true
default_category = "project-source"
default_provenance = "project"

[provenance.project]
origin = "Project source."
license = "Apache-2.0"
redistribution = "included"

[provenance.output]
origin = "Generated output."
license = "NOASSERTION"
redistribution = "excluded"

[[rules]]
pattern = "reports/**"
include = false
category = "captured-output"
provenance = "output"
reason = "Generated output is excluded."
""",
                encoding="utf-8",
            )
            (source / "main.py").write_text("print('ok')\n", encoding="utf-8")
            executable = source / "run.sh"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            (source / "reports").mkdir()
            (source / "reports" / "run.json").write_text("{}\n", encoding="utf-8")
            self._git(source, "init", "-q")
            self._git(source, "add", ".")
            self._git(
                source,
                "-c",
                "user.name=Release Test",
                "-c",
                "user.email=release@example.invalid",
                "commit",
                "-qm",
                "fixture",
            )

            output = container / "stage"
            manifest = build_export(source, output)

            self.assertTrue((output / "main.py").is_file())
            self.assertFalse((output / "reports").exists())
            self.assertTrue(os.access(output / "run.sh", os.X_OK))
            self.assertEqual(3, manifest["summary"]["file_count"])
            written = json.loads(
                (output / "release-manifest.json").read_text(encoding="utf-8")
            )
            self.assertFalse(written["source"]["dirty"])
            self.assertEqual(
                {"captured-output": 1}, written["summary"]["excluded_counts"]
            )

    def test_dirty_export_requires_explicit_preview_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            source = container / "source"
            source.mkdir()
            (source / "release").mkdir()
            (source / "release" / "release-content.toml").write_text(
                """schema_version = 1
default_include = true
default_category = "source"
default_provenance = "project"
[provenance.project]
origin = "Project source."
license = "Apache-2.0"
redistribution = "included"
""",
                encoding="utf-8",
            )
            self._git(source, "init", "-q")
            self._git(source, "add", ".")
            self._git(
                source,
                "-c",
                "user.name=Release Test",
                "-c",
                "user.email=release@example.invalid",
                "commit",
                "-qm",
                "fixture",
            )
            (source / "dirty.txt").write_text("dirty\n", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                build_export(source, container / "refused")

            manifest = build_export(
                source,
                container / "preview",
                allow_dirty=True,
                include_untracked=True,
            )
            self.assertTrue(manifest["source"]["dirty"])
            self.assertTrue((container / "preview" / "dirty.txt").is_file())


if __name__ == "__main__":
    unittest.main()
