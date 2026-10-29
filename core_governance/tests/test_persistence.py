from __future__ import annotations

from collections.abc import Iterable
from typing import Any
import unittest

from realized_core_governance.persistence import (
    GovernanceArtifactWriter,
    persist_governed_artifacts,
)


class _Writer:
    def __init__(self, result: dict[str, Any] | None = None) -> None:
        self.result = result if result is not None else {"status": "persisted"}
        self.calls: list[tuple[Iterable[object], str]] = []

    def persist_artifacts(
        self,
        artifacts: Iterable[object],
        *,
        run_id: str = "artifact_import",
    ) -> dict[str, Any]:
        self.calls.append((artifacts, run_id))
        return self.result


class _FailingWriter:
    def persist_artifacts(
        self,
        artifacts: Iterable[object],
        *,
        run_id: str = "artifact_import",
    ) -> dict[str, Any]:
        raise RuntimeError(f"failed:{run_id}")


class GovernancePersistenceTests(unittest.TestCase):
    def test_writer_protocol_is_structural(self) -> None:
        self.assertIsInstance(_Writer(), GovernanceArtifactWriter)
        self.assertNotIsInstance(object(), GovernanceArtifactWriter)

    def test_forwarder_preserves_batch_run_id_and_report_identity(self) -> None:
        artifacts = (item for item in [object(), object()])
        report = {"status": "persisted", "reports": []}
        writer = _Writer(report)

        result = persist_governed_artifacts(
            writer,
            artifacts,
            run_id="skill_import:policy_batch",
        )

        self.assertIs(report, result)
        self.assertEqual(1, len(writer.calls))
        self.assertIs(artifacts, writer.calls[0][0])
        self.assertEqual("skill_import:policy_batch", writer.calls[0][1])

    def test_forwarder_preserves_default_run_id(self) -> None:
        writer = _Writer()

        persist_governed_artifacts(writer, [])

        self.assertEqual("artifact_import", writer.calls[0][1])

    def test_forwarder_does_not_translate_writer_failures(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "failed:skill_import:skill_batch"):
            persist_governed_artifacts(
                _FailingWriter(),
                [],
                run_id="skill_import:skill_batch",
            )


if __name__ == "__main__":
    unittest.main()
