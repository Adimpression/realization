from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from release_content import load_policy


LOCAL_TOP_LEVEL_DIRECTORIES = frozenset(
    {
        ".git",
        ".idea",
        ".runtime_models",
        ".tmp_pdf_review",
        ".uv-cache",
        ".venv",
        "build",
        "corpus",
        "dist",
        "ram",
        "reports",
        "state",
        "tmp",
        "venv",
    }
)
GENERATED_DIRECTORY_NAMES = frozenset(
    {
        ".dart_tool",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
        "ephemeral",
    }
)
LOCAL_CONFIGURATION_FILES = frozenset({"local.env", "offline.env"})
GENERATED_FILE_NAMES = frozenset(
    {
        ".flutter-plugins-dependencies",
        "Generated.xcconfig",
        "flutter_export_environment.sh",
        "local.properties",
    }
)
MAINTAINER_HOME_PREFIX = ("/Users/" + "ravindranathakila/").encode("utf-8")


class RepositoryPortabilityTest(unittest.TestCase):
    def test_release_eligible_source_has_no_maintainer_home_paths(self) -> None:
        policy = load_policy(REPO_ROOT)
        offenders: list[str] = []

        for current, directories, filenames in os.walk(REPO_ROOT, topdown=True):
            current_path = Path(current)
            retained_directories: list[str] = []
            for name in directories:
                if current_path == REPO_ROOT and name in LOCAL_TOP_LEVEL_DIRECTORIES:
                    continue
                if current_path == REPO_ROOT and name.endswith("-dist"):
                    continue
                if name in GENERATED_DIRECTORY_NAMES or name.endswith(".egg-info"):
                    continue
                retained_directories.append(name)
            directories[:] = retained_directories

            for name in filenames:
                if name in GENERATED_FILE_NAMES:
                    continue
                path = current_path / name
                relative = path.relative_to(REPO_ROOT).as_posix()
                if relative in LOCAL_CONFIGURATION_FILES:
                    continue
                if not policy.classify(relative).include:
                    continue
                if MAINTAINER_HOME_PREFIX in path.read_bytes():
                    offenders.append(relative)

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
