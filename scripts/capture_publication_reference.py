#!/usr/bin/env python3
"""Capture deterministic publication artifacts for architecture qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workstation.runtime.core.session import launch_workstation_session
from workstation.runtime.core.workstation_core import workstation_learn_markdown_action
from workstation.app.cli.composition import ensure_workstation_application_composition
from workstation.runtime.core.subject_host_actions import RuntimeSubjectWorkflowHostActions
from workstation.subject.core.subject_workflow import (
    apply_subject_action,
    default_subject_scenarios,
    load_subject_progress,
)


DEFAULT_FIXTURE = (
    REPO_ROOT
    / "workstation"
    / "tests"
    / "fixtures"
    / "report_creation"
    / "01_FIND_THE_TIME.md"
)
DEFAULT_OUTPUT = REPO_ROOT / "reports" / "architecture_qualification" / "publication_reference"
ACTION_SEQUENCE = (
    "open_context",
    "generate_itemization",
    "refresh_review_composition",
    "compare_projections",
    "refresh_publication_composition",
    "approve_review",
    "lock_publication",
    "build_report",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize(value: Any, *, root: Path) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize(item, root=root) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalize(item, root=root) for item in value]
    if isinstance(value, str):
        normalized = value.replace(str(root), "$WORKSTATION_ROOT").replace(
            str(REPO_ROOT), "$REPO_ROOT"
        )
        replacements = (
            (r"(?<=Snapshot )[0-9a-f]{8}\b", "$SNAPSHOT_HASH"),
            (r"\bitemization_[A-Za-z0-9_-]+\b", "$ITEMIZATION_ID"),
            (r"\brvwcomp_[A-Za-z0-9_-]+\b", "$DRAFT_COMPOSITION_ID"),
            (r"\bpubcomp_[A-Za-z0-9_-]+\b", "$PUBLICATION_COMPOSITION_ID"),
            (r"\bpubbuild_[A-Za-z0-9_-]+\b", "$PUBLICATION_BUILD_ID"),
            (r"\b[0-9a-f]{12,64}\b", "$CONTENT_HASH"),
        )
        for pattern, replacement in replacements:
            normalized = re.sub(pattern, replacement, normalized)
        return normalized
    return value


def capture_publication_reference(*, fixture: Path, output: Path) -> dict[str, Any]:
    fixture = fixture.expanduser().resolve()
    output = output.expanduser().resolve()
    if not fixture.is_file():
        raise FileNotFoundError(f"publication fixture does not exist: {fixture}")

    ensure_workstation_application_composition()

    with tempfile.TemporaryDirectory(prefix="realized-publication-reference-") as temp_dir:
        root = (Path(temp_dir) / "workstation-root").resolve()
        launch_workstation_session(
            root_path=root,
            workspace_path=REPO_ROOT,
            skills_sqlite_path=root / "skills" / "store.sqlite3",
            initial_task="Capture deterministic publication qualification artifacts.",
        )
        learned = workstation_learn_markdown_action(
            root_path=root,
            markdown_path=fixture,
            testing_lightweight=True,
        )
        if learned.status != "ok":
            raise RuntimeError(f"fixture intake failed: {learned.status}")
        subject_id = str(learned.payload["report"]["learning_context"]["subject_id"])
        progress = load_subject_progress(root, subject_id)
        host_actions = RuntimeSubjectWorkflowHostActions()

        def scenario():
            return next(
                item
                for item in default_subject_scenarios(root)
                if item.subject_id == subject_id
            )

        actions: list[dict[str, Any]] = []
        for action_key in ACTION_SEQUENCE:
            result = apply_subject_action(
                root_path=root,
                scenario=scenario(),
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )
            actions.append(
                {
                    "action_key": action_key,
                    "next_phase": result.next_phase or "",
                    "next_tab": result.next_tab or "",
                    "status_text": result.status_text,
                    "receipt_title": progress.latest_receipt_title,
                    "receipt_lines": list(progress.latest_receipt_lines),
                }
            )

        built = scenario()
        report_md = Path(built.report_markdown_path)
        report_typ = Path(built.report_typst_path)
        if not report_md.is_file() or not report_typ.is_file():
            raise RuntimeError("publication flow did not materialize report.md and report.typ")

        output.mkdir(parents=True, exist_ok=True)
        normalized_report_md = str(_normalize(report_md.read_text(encoding="utf-8"), root=root))
        normalized_report_typ = str(_normalize(report_typ.read_text(encoding="utf-8"), root=root))
        (output / "report.md").write_text(normalized_report_md, encoding="utf-8")
        (output / "report.typ").write_text(normalized_report_typ, encoding="utf-8")
        reference = _normalize(
            {
                "schema_version": 1,
                "fixture": fixture.relative_to(REPO_ROOT).as_posix(),
                "fixture_sha256": "",
                "subject_id": subject_id,
                "actions": actions,
                "publication": {
                    "build_status": built.build_status,
                    "validation_status": built.validation_status,
                    "publication_title": built.publication_title,
                    "publication_section_count": built.publication_section_count,
                    "publication_claim_count": built.publication_claim_count,
                    "publication_source_count": built.publication_source_count,
                    "publication_entity_count": built.publication_entity_count,
                    "publication_xref_count": built.publication_xref_count,
                    "publication_review_count": built.publication_review_count,
                },
                "artifacts": {},
            },
            root=root,
        )
        reference["fixture_sha256"] = _sha256(fixture)
        reference["artifacts"] = {
            "report.md": _sha256(output / "report.md"),
            "report.typ": _sha256(output / "report.typ"),
        }
        (output / "reference.json").write_text(
            json.dumps(reference, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return reference


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    reference = capture_publication_reference(fixture=args.fixture, output=args.output)
    print(
        "publication reference captured: "
        f"{len(reference['actions'])} actions, {len(reference['artifacts'])} artifacts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
