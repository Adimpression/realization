# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from pathlib import Path
import re
import unittest


_PROTO_DIR = (
    Path(__file__).resolve().parents[1]
    / "grpc_definitions"
    / "src"
    / "workstation"
    / "grpc"
    / "definitions"
)
_TARGET_PROTOS = (
    "subject_workflow.proto",
    "workstation_assets.proto",
    "workstation_bootstrap.proto",
    "workstation_shell.proto",
)
_COMMENTED_DECLARATION_PATTERNS = (
    re.compile(r"^\s*package\s+\S+\s*;"),
    re.compile(r"^\s*(message|enum|service|oneof)\s+\w+"),
    re.compile(r"^\s*rpc\s+\w+\("),
    re.compile(r"^\s*(?:repeated\s+)?(?:\.[\w]+|[\w.]+)\s+\w+\s*=\s*\d+\s*;"),
    re.compile(r"^\s*[A-Z][A-Z0-9_]*\s*=\s*\d+\s*;"),
)


def _has_leading_comment(lines: list[str], index: int) -> bool:
    cursor = index - 1
    while cursor >= 0 and not lines[cursor].strip():
        cursor -= 1
    return cursor >= 0 and lines[cursor].lstrip().startswith("//")


class WorkstationProtoDocumentationTests(unittest.TestCase):
    def test_proto_surface_declarations_have_leading_comments(self) -> None:
        missing: list[str] = []
        for filename in _TARGET_PROTOS:
            path = _PROTO_DIR / filename
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or stripped.startswith("//"):
                    continue
                if any(pattern.match(line) for pattern in _COMMENTED_DECLARATION_PATTERNS):
                    if not _has_leading_comment(lines, index):
                        missing.append(f"{filename}:{index + 1}:{stripped}")
        self.assertEqual(
            missing,
            [],
            msg="Proto declarations are missing leading documentation comments:\n" + "\n".join(missing),
        )
