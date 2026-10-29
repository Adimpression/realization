from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from workstation.subject.core.decision_review import DecisionReviewItem
from dst import discovery_result_from_fixture, normalized_case_from_fixture, run_dst_pipeline_from_fixture
from dst.core import DstUseCaseFixture
from dst.orchestration import DstOrchestrationResult


_REPO_ROOT = Path(__file__).resolve().parents[3]
_LADDER_SPEC_PATH = (
    _REPO_ROOT / "workstation" / "tests" / "fixtures" / "report_creation" / "smart_city_travel_incremental_ladder.json"
)
_DST_FIXTURE_PATH = (
    _REPO_ROOT
    / "dst"
    / "src"
    / "dst"
    / "tests"
    / "fixtures"
    / "dst"
    / "smart-city-travel-incremental.json"
)


@dataclass(frozen=True)
class IncrementalWorkflowHealthExpectation:
    subject_id: str
    itemization_freshness: str
    itemization_validation: str
    draft_composition_current: bool
    report_build_completed: bool

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "IncrementalWorkflowHealthExpectation":
        return cls(
            subject_id=str(payload.get("subject_id", "")),
            itemization_freshness=str(payload.get("itemization_freshness", "")),
            itemization_validation=str(payload.get("itemization_validation", "")),
            draft_composition_current=bool(payload.get("draft_composition_current", False)),
            report_build_completed=bool(payload.get("report_build_completed", False)),
        )


@dataclass(frozen=True)
class IncrementalLadderRung:
    name: str
    markdown_files: tuple[str, ...]
    decision_analysis_expected: bool
    required_markdown_substrings: tuple[str, ...]
    forbidden_markdown_substrings: tuple[str, ...]
    required_workflow_health: IncrementalWorkflowHealthExpectation
    optional_typst_substrings: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "IncrementalLadderRung":
        return cls(
            name=str(payload.get("name", "")),
            markdown_files=tuple(str(item) for item in list(payload.get("markdown_files", []))),
            decision_analysis_expected=bool(payload.get("decision_analysis_expected", False)),
            required_markdown_substrings=tuple(
                str(item) for item in list(payload.get("required_markdown_substrings", []))
            ),
            forbidden_markdown_substrings=tuple(
                str(item) for item in list(payload.get("forbidden_markdown_substrings", []))
            ),
            required_workflow_health=IncrementalWorkflowHealthExpectation.from_dict(
                dict(payload.get("required_workflow_health", {}))
            ),
            optional_typst_substrings=tuple(str(item) for item in list(payload.get("optional_typst_substrings", []))),
        )


@dataclass(frozen=True)
class IncrementalLadderSpec:
    schema_version: str
    subject_id: str
    subject_title: str
    rungs: tuple[IncrementalLadderRung, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "IncrementalLadderSpec":
        return cls(
            schema_version=str(payload.get("schema_version", "")),
            subject_id=str(payload.get("subject_id", "")),
            subject_title=str(payload.get("subject_title", "")),
            rungs=tuple(
                IncrementalLadderRung.from_dict(item)
                for item in list(payload.get("rungs", []))
                if isinstance(item, dict)
            ),
        )


def load_smart_city_travel_incremental_ladder_spec() -> IncrementalLadderSpec:
    payload = json.loads(_LADDER_SPEC_PATH.read_text(encoding="utf-8"))
    return IncrementalLadderSpec.from_dict(payload)


def load_smart_city_travel_incremental_dst_fixture() -> DstUseCaseFixture:
    payload = json.loads(_DST_FIXTURE_PATH.read_text(encoding="utf-8"))
    return DstUseCaseFixture.from_dict(payload)


def cumulative_required_markdown_substrings(
    spec: IncrementalLadderSpec,
    *,
    rung_index: int,
) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for rung in spec.rungs[: rung_index + 1]:
        for item in rung.required_markdown_substrings:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)


def cumulative_optional_typst_substrings(
    spec: IncrementalLadderSpec,
    *,
    rung_index: int,
) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for rung in spec.rungs[: rung_index + 1]:
        for item in rung.optional_typst_substrings:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)


def rung_requires_staged_route_projection(rung: IncrementalLadderRung) -> bool:
    return bool(rung.decision_analysis_expected)


def deterministic_incremental_dst_pipeline(
    fixture: DstUseCaseFixture,
    *,
    staged_route_projection: bool,
    **kwargs: Any,
) -> DstOrchestrationResult:
    result = run_dst_pipeline_from_fixture(
        fixture,
        discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(fixture).to_dict(),
        normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
            fixture,
            runner_kwargs["discovery"],
        ).to_dict(),
        subject_id=str(kwargs.get("subject_id", "")),
        question=str(kwargs.get("question", "")),
        decision_mode=str(kwargs.get("decision_mode", "decision_aid") or "decision_aid"),
        build_epoch_ms=int(kwargs.get("build_epoch_ms", 0) or 0),
    )
    if not staged_route_projection:
        return result
    staged_transition_item_ids = _transition_item_ids_by_normalized_id(
        result.decision_projection.items,
        transition_ids=("t1", "t2", "t3"),
    )
    if len(staged_transition_item_ids) != 3:
        return result
    updated_items: list[DecisionReviewItem] = []
    for item in result.decision_projection.items:
        if (
            item.decision_role == "decision_candidate"
            and str(item.metadata.get("decision_id", "")) == "x1"
        ):
            metadata = dict(item.metadata)
            metadata["selected_transition_decision_review_item_id"] = staged_transition_item_ids[0]
            metadata["selected_transition_decision_review_item_ids"] = list(staged_transition_item_ids)
            updated_items.append(replace(item, metadata=metadata))
            continue
        updated_items.append(item)
    updated_projection = replace(
        result.decision_projection,
        items=tuple(updated_items),
    )
    return replace(
        result,
        decision_projection=updated_projection,
    )


def _transition_item_ids_by_normalized_id(
    items: tuple[DecisionReviewItem, ...],
    *,
    transition_ids: tuple[str, ...],
) -> tuple[str, ...]:
    item_by_transition_id = {
        str(item.metadata.get("transition_id", "")): item.decision_review_item_id
        for item in items
        if item.decision_role == "transition_candidate"
    }
    return tuple(item_by_transition_id[item_id] for item_id in transition_ids if item_id in item_by_transition_id)


__all__ = [
    "IncrementalLadderRung",
    "IncrementalLadderSpec",
    "IncrementalWorkflowHealthExpectation",
    "cumulative_optional_typst_substrings",
    "cumulative_required_markdown_substrings",
    "deterministic_incremental_dst_pipeline",
    "load_smart_city_travel_incremental_dst_fixture",
    "load_smart_city_travel_incremental_ladder_spec",
    "rung_requires_staged_route_projection",
]
