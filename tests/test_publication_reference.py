from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "capture_publication_reference.py"
SPEC = importlib.util.spec_from_file_location("capture_publication_reference", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
publication_reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication_reference)


class PublicationReferenceTest(unittest.TestCase):
    def test_reference_capture_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = publication_reference.capture_publication_reference(
                fixture=publication_reference.DEFAULT_FIXTURE,
                output=Path(temp_dir) / "first",
            )
            second = publication_reference.capture_publication_reference(
                fixture=publication_reference.DEFAULT_FIXTURE,
                output=Path(temp_dir) / "second",
            )

            self.assertEqual(first, second)
            self.assertEqual(
                list(publication_reference.ACTION_SEQUENCE),
                [item["action_key"] for item in first["actions"]],
            )
            self.assertEqual("ok", first["publication"]["build_status"])
            self.assertEqual("ok", first["publication"]["validation_status"])
            self.assertEqual(
                (Path(temp_dir) / "first" / "report.md").read_bytes(),
                (Path(temp_dir) / "second" / "report.md").read_bytes(),
            )
            self.assertEqual(
                (Path(temp_dir) / "first" / "report.typ").read_bytes(),
                (Path(temp_dir) / "second" / "report.typ").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
