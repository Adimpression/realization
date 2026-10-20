# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from workstation.subject.core.subject_workflow import (
    SubjectImportStaging,
    SubjectProgress,
    SubjectScenario,
    default_subject_scenarios,
    load_subject_import_staging,
    load_subject_progress,
    load_subject_progress_map,
    persist_subject_progress,
)


@dataclass(frozen=True)
class SubjectWorkflowRepository:
    def list_scenarios(self, *, root_path: Path) -> tuple[SubjectScenario, ...]:
        return default_subject_scenarios(Path(root_path).expanduser().resolve())

    def load_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
    ) -> SubjectProgress:
        return load_subject_progress(Path(root_path).expanduser().resolve(), subject_id)

    def load_progress_map(
        self,
        *,
        root_path: Path,
        scenarios: tuple[SubjectScenario, ...],
        existing: dict[str, SubjectProgress] | None = None,
    ) -> dict[str, SubjectProgress]:
        return load_subject_progress_map(
            Path(root_path).expanduser().resolve(),
            scenarios,
            existing=existing,
        )

    def persist_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress: SubjectProgress,
    ) -> Path | None:
        return persist_subject_progress(
            Path(root_path).expanduser().resolve(),
            subject_id,
            progress,
        )

    def load_import_staging(
        self,
        *,
        root_path: Path,
    ) -> SubjectImportStaging | None:
        return load_subject_import_staging(Path(root_path).expanduser().resolve())
