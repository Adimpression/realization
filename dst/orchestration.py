from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from applied_theory_types import ProposalType, SupplementMode
from coordinated_transformation.core import Model
from decision_review_constructs import TransformationConstructCandidate, deterministic_transformation_construct_candidates_from_itemized_item
from dst.core import DstEntry, DstSection, DstUseCaseFixture
from dst.discovery import (
    DstDiscoveryResult,
    build_dst_prompt_input,
    build_reduce_not_discovery_prompt,
    default_root_non_achievedness,
    discovery_result_from_fixture,
    dst_discovery_schema_hint,
)
from dst.normalization import (
    DstNormalizedCase,
    build_dst_normalization_prompt,
    coordinated_model_from_normalized_case,
    dst_normalized_schema_hint,
    normalized_case_from_fixture,
)
from dst.projection import (
    DstNormalizedConstructProjection,
    DstNormalizedDecisionProjection,
    project_normalized_case_to_transformation_construct_candidates,
    project_normalized_case_to_decision_frame,
)
from id_generation import slugify
from itemize import ItemizedSubjectItem
from runtime_controller_api import bootstrap_runtime_controller
from semantic_text import collapse_ws


class DstDiscoveryRunner(Protocol):
    def __call__(
        self,
        *,
        prompt: str,
        fixture: DstUseCaseFixture,
        root_non_achievedness: str,
    ) -> dict[str, Any]: ...


class DstNormalizationRunner(Protocol):
    def __call__(
        self,
        *,
        prompt_input: str,
        fixture: DstUseCaseFixture,
        discovery: DstDiscoveryResult,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class DstDiscoveryPromptPacket:
    fixture_id: str
    source_ref: str
    root_non_achievedness: str
    prompt: str


@dataclass(frozen=True)
class DstOrchestrationResult:
    fixture: DstUseCaseFixture
    discovery_prompt_packet: DstDiscoveryPromptPacket
    discovery_result: DstDiscoveryResult
    normalization_input: str
    normalized_case: DstNormalizedCase
    decision_projection: DstNormalizedDecisionProjection
    coordinated_model: Model
    discovery_proposal_id: str = ""
    normalization_proposal_id: str = ""


@dataclass(frozen=True)
class DstConstructDiscoveryResult:
    fixture: DstUseCaseFixture
    orchestration_result: DstOrchestrationResult
    construct_projection: DstNormalizedConstructProjection
    construct_candidates: tuple[TransformationConstructCandidate, ...]


_SORT_KIND_TO_SECTION_KEY: dict[str, str] = {
    "actor": "actors",
    "objective": "objectives",
    "capability": "capabilities",
    "dependency": "dependencies",
    "constraint": "constraints",
    "boundary": "boundaries",
    "state": "states",
    "transition": "transitions",
}


def _stable_live_fixture_id(subject_id: str, itemized_item_id: str) -> str:
    subject_slug = slugify(collapse_ws(subject_id), limit=32) or "subject"
    item_slug = slugify(collapse_ws(itemized_item_id), limit=32) or "item"
    return f"live-{subject_slug}-{item_slug}"


def _live_title_key(text: str) -> str:
    return slugify(collapse_ws(text), limit=48) or "live-dst-case"


def build_live_dst_fixture_for_itemized_item(
    selected_item: ItemizedSubjectItem,
    *,
    subject_title: str = "",
    subject_summary: str = "",
    subject_source_refs: tuple[str, ...] = (),
    supporting_items: tuple[ItemizedSubjectItem, ...] = (),
) -> DstUseCaseFixture:
    normalized_source_refs = tuple(
        item for item in (collapse_ws(str(ref)) for ref in subject_source_refs) if item
    )
    selected_source_refs = tuple(
        item for item in (collapse_ws(str(ref)) for ref in selected_item.source_refs) if item
    )
    source_ref = (
        normalized_source_refs[0]
        if normalized_source_refs
        else selected_source_refs[0]
        if selected_source_refs
        else f"subject:{collapse_ws(selected_item.subject_id)}"
    )
    summary_parts = [
        f"Selected item: {collapse_ws(selected_item.canonical_label) or selected_item.itemized_item_id} ({selected_item.item_kind}).",
    ]
    if collapse_ws(subject_summary):
        summary_parts.append(collapse_ws(subject_summary))
    if collapse_ws(selected_item.summary):
        summary_parts.append(f"Selected item summary: {collapse_ws(selected_item.summary)}")
    supporting_labels = [
        collapse_ws(item.canonical_label) or item.itemized_item_id
        for item in supporting_items
        if collapse_ws(item.itemized_item_id) != collapse_ws(selected_item.itemized_item_id)
    ][:6]
    if supporting_labels:
        summary_parts.append("Nearby itemized inventory: " + "; ".join(supporting_labels))
    section_entries: dict[str, list[DstEntry]] = {key: [] for key in _SORT_KIND_TO_SECTION_KEY.values()}
    seen_by_section: dict[str, set[str]] = {key: set() for key in _SORT_KIND_TO_SECTION_KEY.values()}

    seed_items = [selected_item]
    seed_items.extend(
        item
        for item in supporting_items
        if collapse_ws(item.itemized_item_id) != collapse_ws(selected_item.itemized_item_id)
    )
    for item in seed_items[:8]:
        for candidate in deterministic_transformation_construct_candidates_from_itemized_item(item):
            section_key = _SORT_KIND_TO_SECTION_KEY.get(collapse_ws(candidate.sort_kind))
            label = collapse_ws(candidate.canonical_label)
            if not section_key or not label or label in seen_by_section[section_key]:
                continue
            seen_by_section[section_key].add(label)
            section_entries[section_key].append(
                DstEntry(code=collapse_ws(item.item_kind), text=label)
            )

    sections = tuple(
        DstSection(
            key=section_key,
            title=section_key.replace("_", " ").title(),
            narrative="",
            entries=tuple(section_entries[section_key]),
        )
        for section_key in (
            "actors",
            "objectives",
            "capabilities",
            "dependencies",
            "constraints",
            "boundaries",
            "states",
            "transitions",
        )
        if section_entries[section_key]
    )
    title = collapse_ws(subject_title) or collapse_ws(selected_item.canonical_label) or selected_item.subject_id
    return DstUseCaseFixture(
        fixture_id=_stable_live_fixture_id(selected_item.subject_id, selected_item.itemized_item_id),
        title=title,
        title_key=_live_title_key(title),
        source_ref=source_ref,
        summary=" ".join(part for part in summary_parts if collapse_ws(part)).strip(),
        sections=sections,
        candidate_paths=(),
    )


def build_reduce_not_discovery_prompt_packet(
    fixture: DstUseCaseFixture,
) -> DstDiscoveryPromptPacket:
    root_non_achievedness = default_root_non_achievedness(fixture)
    return DstDiscoveryPromptPacket(
        fixture_id=fixture.fixture_id,
        source_ref=fixture.source_ref,
        root_non_achievedness=root_non_achievedness,
        prompt=build_reduce_not_discovery_prompt(fixture),
    )


def bootstrap_dst_discovery_controller(
    fixture: DstUseCaseFixture,
    *,
    llm_policy: str = "required",
    subject_scope: Any | None = None,
    subject_scope_root_path: Path | None = None,
) -> tuple[Any, Any, DstDiscoveryPromptPacket]:
    prompt_packet = build_reduce_not_discovery_prompt_packet(fixture)
    state, controller = bootstrap_runtime_controller(
        semantic_unit=prompt_packet.root_non_achievedness,
        llm_policy=llm_policy,
        subject_scope=subject_scope,
        subject_scope_root_path=subject_scope_root_path,
    )
    state.supplement_profile = dict(getattr(state, "supplement_profile", {}) or {})
    state.supplement_profile["dst_discovery_fixture_id"] = fixture.fixture_id
    state.supplement_profile["dst_discovery_source_ref"] = fixture.source_ref
    state.supplement_profile["dst_discovery_root_non_achievedness"] = prompt_packet.root_non_achievedness
    state.supplement_profile["dst_discovery_prompt"] = prompt_packet.prompt
    return state, controller, prompt_packet


def run_runtime_dst_discovery(
    controller: Any,
    fixture: DstUseCaseFixture,
    *,
    node: Any,
    prompt_packet: DstDiscoveryPromptPacket | None = None,
) -> tuple[DstDiscoveryResult, str]:
    packet = prompt_packet or build_reduce_not_discovery_prompt_packet(fixture)
    proposal = controller.request_proposal(
        proposal_type=ProposalType.DST_DISCOVERY,
        node=node,
        target_scope=fixture.fixture_id,
        instructions=packet.prompt,
        fallback_payload=discovery_result_from_fixture(fixture).to_dict(),
        mode=SupplementMode.DEEP,
        schema_hint=dst_discovery_schema_hint(),
    )
    controller.admit_proposal(
        proposal,
        rationale="DST discovery proposals are admitted as governed candidate-path discovery artifacts over the root transformation non-achievedness.",
    )
    node.metadata["dst_discovery_proposal_id"] = proposal.id
    return DstDiscoveryResult.from_dict(dict(proposal.payload)), str(proposal.id)


def run_runtime_dst_normalization(
    controller: Any,
    fixture: DstUseCaseFixture,
    discovery: DstDiscoveryResult,
    *,
    node: Any,
) -> tuple[str, DstNormalizedCase, str]:
    prompt_input = build_dst_prompt_input(fixture, discovery)
    proposal = controller.request_proposal(
        proposal_type=ProposalType.DST_NORMALIZATION,
        node=node,
        target_scope=fixture.fixture_id,
        instructions=build_dst_normalization_prompt(prompt_input),
        fallback_payload=normalized_case_from_fixture(fixture, discovery).to_dict(),
        mode=SupplementMode.DEEP,
        schema_hint=dst_normalized_schema_hint(),
    )
    controller.admit_proposal(
        proposal,
        rationale="DST normalization proposals are admitted as strict typed serializations of already-governed discovery output.",
    )
    node.metadata["dst_normalization_proposal_id"] = proposal.id
    return prompt_input, DstNormalizedCase.from_dict(dict(proposal.payload)), str(proposal.id)


def run_dst_pipeline_from_fixture(
    fixture: DstUseCaseFixture,
    *,
    discovery_runner: DstDiscoveryRunner,
    normalization_runner: DstNormalizationRunner,
    subject_id: str = "",
    question: str = "",
    decision_mode: str = "decision_aid",
    build_epoch_ms: int = 0,
) -> DstOrchestrationResult:
    discovery_prompt_packet = build_reduce_not_discovery_prompt_packet(fixture)
    discovery_payload = discovery_runner(
        prompt=discovery_prompt_packet.prompt,
        fixture=fixture,
        root_non_achievedness=discovery_prompt_packet.root_non_achievedness,
    )
    discovery_result = DstDiscoveryResult.from_dict(dict(discovery_payload))
    normalization_input = build_dst_prompt_input(fixture, discovery_result)
    normalized_payload = normalization_runner(
        prompt_input=normalization_input,
        fixture=fixture,
        discovery=discovery_result,
    )
    normalized_case = DstNormalizedCase.from_dict(dict(normalized_payload))
    decision_projection = project_normalized_case_to_decision_frame(
        normalized_case,
        subject_id=subject_id,
        question=question,
        decision_mode=decision_mode,
        build_epoch_ms=build_epoch_ms,
    )
    coordinated_model = coordinated_model_from_normalized_case(normalized_case)
    return DstOrchestrationResult(
        fixture=fixture,
        discovery_prompt_packet=discovery_prompt_packet,
        discovery_result=discovery_result,
        normalization_input=normalization_input,
        normalized_case=normalized_case,
        decision_projection=decision_projection,
        coordinated_model=coordinated_model,
    )


def run_live_dst_pipeline_from_fixture(
    fixture: DstUseCaseFixture,
    *,
    llm_policy: str = "required",
    subject_scope: Any | None = None,
    subject_scope_root_path: Path | None = None,
    subject_id: str = "",
    question: str = "",
    decision_mode: str = "decision_aid",
    build_epoch_ms: int = 0,
) -> DstOrchestrationResult:
    state, controller, discovery_prompt_packet = bootstrap_dst_discovery_controller(
        fixture,
        llm_policy=llm_policy,
        subject_scope=subject_scope,
        subject_scope_root_path=subject_scope_root_path,
    )
    root = state.root()
    discovery_result, discovery_proposal_id = run_runtime_dst_discovery(
        controller,
        fixture,
        node=root,
        prompt_packet=discovery_prompt_packet,
    )
    normalization_input, normalized_case, normalization_proposal_id = run_runtime_dst_normalization(
        controller,
        fixture,
        discovery_result,
        node=root,
    )
    decision_projection = project_normalized_case_to_decision_frame(
        normalized_case,
        subject_id=subject_id,
        question=question,
        decision_mode=decision_mode,
        build_epoch_ms=build_epoch_ms,
    )
    coordinated_model = coordinated_model_from_normalized_case(normalized_case)
    return DstOrchestrationResult(
        fixture=fixture,
        discovery_prompt_packet=discovery_prompt_packet,
        discovery_result=discovery_result,
        normalization_input=normalization_input,
        normalized_case=normalized_case,
        decision_projection=decision_projection,
        coordinated_model=coordinated_model,
        discovery_proposal_id=discovery_proposal_id,
        normalization_proposal_id=normalization_proposal_id,
    )


def run_live_dst_construct_discovery_for_itemized_item(
    selected_item: ItemizedSubjectItem,
    *,
    subject_title: str = "",
    subject_summary: str = "",
    subject_source_refs: tuple[str, ...] = (),
    supporting_items: tuple[ItemizedSubjectItem, ...] = (),
    llm_policy: str = "required",
    subject_scope: Any | None = None,
    subject_scope_root_path: Path | None = None,
    review_item_id: str = "",
    build_epoch_ms: int = 0,
) -> DstConstructDiscoveryResult:
    fixture = build_live_dst_fixture_for_itemized_item(
        selected_item,
        subject_title=subject_title,
        subject_summary=subject_summary,
        subject_source_refs=subject_source_refs,
        supporting_items=supporting_items,
    )
    orchestration_result = run_live_dst_pipeline_from_fixture(
        fixture,
        llm_policy=llm_policy,
        subject_scope=subject_scope,
        subject_scope_root_path=subject_scope_root_path,
        subject_id=selected_item.subject_id,
        question=f"What transformation constructs should guide '{collapse_ws(selected_item.canonical_label) or selected_item.itemized_item_id}'?",
        decision_mode="decision_aid",
        build_epoch_ms=build_epoch_ms,
    )
    construct_projection = project_normalized_case_to_transformation_construct_candidates(
        orchestration_result.normalized_case,
        subject_id=selected_item.subject_id,
        itemized_item_id=selected_item.itemized_item_id,
        source_refs=selected_item.source_refs,
        review_item_id=review_item_id,
        build_epoch_ms=build_epoch_ms,
    )
    return DstConstructDiscoveryResult(
        fixture=fixture,
        orchestration_result=orchestration_result,
        construct_projection=construct_projection,
        construct_candidates=construct_projection.candidates,
    )


__all__ = [
    "DstConstructDiscoveryResult",
    "DstDiscoveryPromptPacket",
    "DstDiscoveryRunner",
    "DstNormalizationRunner",
    "DstOrchestrationResult",
    "bootstrap_dst_discovery_controller",
    "build_live_dst_fixture_for_itemized_item",
    "build_reduce_not_discovery_prompt_packet",
    "run_live_dst_construct_discovery_for_itemized_item",
    "run_live_dst_pipeline_from_fixture",
    "run_dst_pipeline_from_fixture",
    "run_runtime_dst_discovery",
    "run_runtime_dst_normalization",
]
