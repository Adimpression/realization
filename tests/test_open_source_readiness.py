from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_open_source_readiness.py"
SPEC = importlib.util.spec_from_file_location("check_open_source_readiness", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
readiness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = readiness
SPEC.loader.exec_module(readiness)


class OpenSourceReadinessTest(unittest.TestCase):
    @staticmethod
    def _write_ready_candidate(root: Path) -> None:
        for document in readiness.REQUIRED_DOCUMENTS:
            content = "# Document\n"
            if document == "SECURITY.md":
                content += "Report privately at security@example.invalid.\n"
            (root / document).write_text(content, encoding="utf-8")
        for relative_path in readiness.REQUIRED_RELEASE_FILES:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("release control\n", encoding="utf-8")
        (root / "LICENSE").write_text("Test license\n", encoding="utf-8")
        (root / "local.env.example").write_text(
            'OPENAI_API_KEY=""\nSTATE_DB_PASSWORD=""\n',
            encoding="utf-8",
        )
        (root / "offline.env.example").write_text(
            'LLAMACPP_API_KEY=""\nCONSOLE_SSH_PASSWORD=""\n',
            encoding="utf-8",
        )

    def test_minimal_candidate_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)

            self.assertEqual([], readiness.audit(root))

    def test_local_configuration_and_generated_artifacts_are_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "local.env").write_text("OPENAI_API_KEY=private\n", encoding="utf-8")
            (root / "state").mkdir()
            (root / "runtime.sqlite3").write_text("state", encoding="utf-8")
            (root / "view.sync-conflict-20261020.py").write_text(
                "pass\n", encoding="utf-8"
            )

            findings = readiness.audit(root)
            codes = {finding.code for finding in findings}

            self.assertIn("local-configuration", codes)
            self.assertIn("local-directory", codes)
            self.assertIn("local-database", codes)
            self.assertIn("sync-conflict", codes)

    def test_nonempty_secret_in_example_is_a_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "offline.env.example").write_text(
                'LLAMACPP_API_KEY="not-for-release"\n', encoding="utf-8"
            )

            findings = readiness.audit(root)

            self.assertTrue(
                any(finding.code == "nonempty-example-secret" for finding in findings)
            )

    def test_missing_license_and_security_contact_are_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "LICENSE").unlink()
            (root / "SECURITY.md").write_text(
                "PUBLIC-SECURITY-CONTACT-REQUIRED\n", encoding="utf-8"
            )

            findings = readiness.audit(root)
            codes = {finding.code for finding in findings}

            self.assertIn("missing-license", codes)
            self.assertIn("missing-security-contact", codes)

    def test_authored_ai_response_residue_is_a_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "DESIGN.md").write_text(
                "Yes. With your Rust core + SQLite store, the cleanest design is:\n"
                "#### 9. So yes, this is the next layer.\n"
                "> So your intuition is right.\n"
                "- Here is the clean mental model.\n"
                "Since you also asked for another form, here it is.\n"
                "Implemented the current architecture.\n"
                "You can summarize it internally as follows.\n"
                "I also added a validation path.\n"
                "If you want the next step, it is ready.\n"
                "## 12. Clean next extension, if you want it\n"
                "One remaining limitation: I would use the old path.\n"
                "Your final answer should include the implementation.\n"
                "Phase 12 is now complete in the intended shape.\n"
                "https://example.invalid/?utm_source=chatgpt.com\n",
                encoding="utf-8",
            )

            findings = readiness.audit(root)
            codes = {finding.code for finding in findings}

            self.assertIn("ai-response-residue", codes)
            self.assertIn("ai-copy-tracking-parameter", codes)
            self.assertGreaterEqual(
                sum(finding.code == "ai-response-residue" for finding in findings),
                12,
            )

    def test_instructional_second_person_is_not_response_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "GUIDE.md").write_text(
                "# Guide\n\n"
                "If you want to run the pieces manually, use the commands below.\n"
                "If you want the slanted side, solve for c.\n"
                "You should see a successful result.\n",
                encoding="utf-8",
            )

            self.assertEqual([], readiness.audit(root))

    def test_private_chat_history_is_a_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "CHAT_HISTORY.md").write_text(
                "User: private conversation\n",
                encoding="utf-8",
            )

            findings = readiness.audit(root)

            self.assertTrue(
                any(finding.code == "private-transcript" for finding in findings)
            )

    def test_temporary_working_document_is_a_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "TMP.md").write_text("# Working notes\n", encoding="utf-8")

            findings = readiness.audit(root)

            self.assertTrue(
                any(finding.code == "temporary-document" for finding in findings)
            )

    def test_empty_authored_markdown_is_a_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            (root / "EMPTY.md").touch()

            findings = readiness.audit(root)

            self.assertTrue(
                any(finding.code == "empty-document" for finding in findings)
            )

    def test_captured_model_output_is_not_treated_as_authored_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            reports = root / "reports"
            reports.mkdir()
            (reports / "captured-output.md").write_text(
                "Yes. With your Rust core + SQLite store, the cleanest design is:\n",
                encoding="utf-8",
            )

            self.assertEqual([], readiness.audit(root))

    def test_nonessential_architecture_evidence_is_a_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_ready_candidate(root)
            evidence = root / "architecture" / "baselines" / "old"
            evidence.mkdir(parents=True)
            (evidence / "QUALIFICATION.md").write_text(
                "Yes. With the prior run, the migration is complete.\n",
                encoding="utf-8",
            )

            findings = readiness.audit(root)
            codes = {finding.code for finding in findings}

            self.assertIn("nonessential-architecture-artifact", codes)
            self.assertIn("ai-response-residue", codes)


if __name__ == "__main__":
    unittest.main()
