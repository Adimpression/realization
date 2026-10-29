from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from dst.core import CORE_USE_CASE_SECTION_KEYS, DST_TYPED_FIXTURE_ROOT, DstUseCaseFixture
from realized_core_semantics.semantic_text import collapse_ws


DST_DISCOVERY_SCHEMA_VERSION = "dst_discovery.v1"
DST_DISCOVERY_FIXTURE_ROOT = DST_TYPED_FIXTURE_ROOT / "discovery"
DST_SORT_ATOM_ORDER = (
    "Actor",
    "Objective",
    "Capability",
    "Dependency",
    "Constraint",
    "Boundary",
    "State",
    "Transition",
    "Decision",
    "TimePoint",
)


def _ordered_unique_texts(items: list[object] | tuple[object, ...] | set[object] | None) -> tuple[str, ...]:
    if not items:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        text = collapse_ws(str(item))
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


def _stable_path_id(title: str, index: int) -> str:
    normalized = collapse_ws(title).lower().replace(" ", "-")
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch == "-").strip("-")
    return f"p{index}" if not normalized else f"p{index}-{normalized[:48]}".rstrip("-")


@dataclass(frozen=True)
class DstDiscoverySortAtomContext:
    actors: tuple[str, ...] = ()
    objectives: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    boundaries: tuple[str, ...] = ()
    states: tuple[str, ...] = ()
    transitions: tuple[str, ...] = ()
    decisions: tuple[str, ...] = ()
    timepoints: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstDiscoverySortAtomContext":
        return cls(
            actors=_ordered_unique_texts(payload.get("actors", [])),
            objectives=_ordered_unique_texts(payload.get("objectives", [])),
            capabilities=_ordered_unique_texts(payload.get("capabilities", [])),
            dependencies=_ordered_unique_texts(payload.get("dependencies", [])),
            constraints=_ordered_unique_texts(payload.get("constraints", [])),
            boundaries=_ordered_unique_texts(payload.get("boundaries", [])),
            states=_ordered_unique_texts(payload.get("states", [])),
            transitions=_ordered_unique_texts(payload.get("transitions", [])),
            decisions=_ordered_unique_texts(payload.get("decisions", [])),
            timepoints=_ordered_unique_texts(payload.get("timepoints", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "actors": list(self.actors),
            "objectives": list(self.objectives),
            "capabilities": list(self.capabilities),
            "dependencies": list(self.dependencies),
            "constraints": list(self.constraints),
            "boundaries": list(self.boundaries),
            "states": list(self.states),
            "transitions": list(self.transitions),
            "decisions": list(self.decisions),
            "timepoints": list(self.timepoints),
        }


@dataclass(frozen=True)
class DstDiscoveryPath:
    path_id: str
    title: str
    path_kind: str
    route_expression: str
    summary: str
    supporting_points: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    required_information: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DstDiscoveryPath":
        return cls(
            path_id=collapse_ws(str(payload.get("path_id", ""))),
            title=str(payload.get("title", "") or ""),
            path_kind=collapse_ws(str(payload.get("path_kind", ""))) or "unknown",
            route_expression=collapse_ws(str(payload.get("route_expression", ""))),
            summary=str(payload.get("summary", "") or ""),
            supporting_points=_ordered_unique_texts(payload.get("supporting_points", [])),
            blockers=_ordered_unique_texts(payload.get("blockers", [])),
            required_information=_ordered_unique_texts(payload.get("required_information", [])),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "path_id": self.path_id,
            "title": self.title,
            "path_kind": self.path_kind,
            "route_expression": self.route_expression,
            "summary": self.summary,
            "supporting_points": list(self.supporting_points),
            "blockers": list(self.blockers),
            "required_information": list(self.required_information),
        }


@dataclass(frozen=True)
class DstDiscoveryDistinction:
    distinction_id: str
    title: str
    description: str
    separates_path_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DstDiscoveryDistinction":
        return cls(
            distinction_id=collapse_ws(str(payload.get("distinction_id", ""))),
            title=str(payload.get("title", "") or ""),
            description=str(payload.get("description", "") or ""),
            separates_path_ids=_ordered_unique_texts(payload.get("separates_path_ids", [])),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "distinction_id": self.distinction_id,
            "title": self.title,
            "description": self.description,
            "separates_path_ids": list(self.separates_path_ids),
        }


@dataclass(frozen=True)
class DstDiscoveryResult:
    fixture_id: str
    source_ref: str
    system_name: str
    decision_problem: str
    root_non_achievedness: str
    candidate_paths: tuple[DstDiscoveryPath, ...] = ()
    dominant_distinctions: tuple[DstDiscoveryDistinction, ...] = ()
    sort_atom_context: DstDiscoverySortAtomContext = DstDiscoverySortAtomContext()
    shared_blockers: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    ambiguities: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    schema_version: str = DST_DISCOVERY_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DstDiscoveryResult":
        result = cls(
            fixture_id=collapse_ws(str(payload.get("fixture_id", ""))),
            source_ref=collapse_ws(str(payload.get("source_ref", ""))),
            system_name=str(payload.get("system_name", "") or ""),
            decision_problem=str(payload.get("decision_problem", "") or ""),
            root_non_achievedness=str(payload.get("root_non_achievedness", "") or ""),
            candidate_paths=tuple(
                DstDiscoveryPath.from_dict(item)
                for item in list(payload.get("candidate_paths", []))
                if isinstance(item, dict)
            ),
            dominant_distinctions=tuple(
                DstDiscoveryDistinction.from_dict(item)
                for item in list(payload.get("dominant_distinctions", []))
                if isinstance(item, dict)
            ),
            sort_atom_context=DstDiscoverySortAtomContext.from_dict(dict(payload.get("sort_atom_context", {}))),
            shared_blockers=_ordered_unique_texts(payload.get("shared_blockers", [])),
            assumptions=_ordered_unique_texts(payload.get("assumptions", [])),
            ambiguities=_ordered_unique_texts(payload.get("ambiguities", [])),
            missing_information=_ordered_unique_texts(payload.get("missing_information", [])),
            schema_version=collapse_ws(str(payload.get("schema_version", DST_DISCOVERY_SCHEMA_VERSION))) or DST_DISCOVERY_SCHEMA_VERSION,
        )
        result._validate()
        return result

    def _validate(self) -> None:
        path_ids = {item.path_id for item in self.candidate_paths}
        if len(path_ids) != len(self.candidate_paths):
            raise ValueError("duplicate discovery path ids")
        for item in self.candidate_paths:
            if not item.path_id:
                raise ValueError("discovery path missing id")
            if not item.title:
                raise ValueError("discovery path missing title")
        for distinction in self.dominant_distinctions:
            if not distinction.distinction_id:
                raise ValueError("dominant distinction missing id")
            for path_id in distinction.separates_path_ids:
                if path_id not in path_ids:
                    raise ValueError(f"dominant distinction references unknown path id: {path_id}")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "fixture_id": self.fixture_id,
            "source_ref": self.source_ref,
            "system_name": self.system_name,
            "decision_problem": self.decision_problem,
            "root_non_achievedness": self.root_non_achievedness,
            "candidate_paths": [item.to_dict() for item in self.candidate_paths],
            "dominant_distinctions": [item.to_dict() for item in self.dominant_distinctions],
            "sort_atom_context": self.sort_atom_context.to_dict(),
            "shared_blockers": list(self.shared_blockers),
            "assumptions": list(self.assumptions),
            "ambiguities": list(self.ambiguities),
            "missing_information": list(self.missing_information),
        }


def list_dst_discovery_fixture_paths() -> tuple[Path, ...]:
    if not DST_DISCOVERY_FIXTURE_ROOT.exists():
        return ()
    return tuple(sorted(DST_DISCOVERY_FIXTURE_ROOT.glob("*.json")))


def load_dst_discovery_results() -> tuple[DstDiscoveryResult, ...]:
    results: list[DstDiscoveryResult] = []
    for path in list_dst_discovery_fixture_paths():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"invalid discovery fixture payload: {path}")
        results.append(DstDiscoveryResult.from_dict(payload))
    return tuple(results)


def dst_discovery_schema_hint() -> dict[str, Any]:
    return {
        "schema_version": DST_DISCOVERY_SCHEMA_VERSION,
        "fixture_id": "",
        "source_ref": "",
        "system_name": "",
        "decision_problem": "",
        "root_non_achievedness": "",
        "candidate_paths": [
            {
                "path_id": "",
                "title": "",
                "path_kind": "",
                "route_expression": "",
                "summary": "",
                "supporting_points": [],
                "blockers": [],
                "required_information": [],
            }
        ],
        "dominant_distinctions": [
            {
                "distinction_id": "",
                "title": "",
                "description": "",
                "separates_path_ids": [],
            }
        ],
        "sort_atom_context": DstDiscoverySortAtomContext().to_dict(),
        "shared_blockers": [],
        "assumptions": [],
        "ambiguities": [],
        "missing_information": [],
    }


def default_root_non_achievedness(fixture: DstUseCaseFixture) -> str:
    return (
        f"What are the materially distinct admissible transformation paths for {fixture.title}, "
        "what unresolved distinctions separate those paths, and what missing facts block commitment?"
    )


def _fixture_source_block(fixture: DstUseCaseFixture) -> str:
    lines = [
        f"Use case title: {fixture.title}",
        f"Source ref: {fixture.source_ref}",
    ]
    if fixture.summary:
        lines.extend(["", "Summary:", fixture.summary])
    for section_key in CORE_USE_CASE_SECTION_KEYS:
        section = fixture.section(section_key)
        if section is None:
            continue
        lines.extend(["", f"{section.title}:"])
        if section.narrative:
            lines.append(section.narrative)
        for entry in section.entries:
            if entry.code:
                lines.append(f"- {entry.code}: {entry.text}")
            else:
                lines.append(f"- {entry.text}")
    if fixture.candidate_paths:
        lines.extend(["", "Explicit candidate paths already present in the use case:"])
        for path in fixture.candidate_paths:
            lines.append(f"- {path.title}: {path.route_expression or '<no route>'}")
            if path.narrative:
                lines.append(f"  {path.narrative}")
    return "\n".join(lines).strip()


def _sort_atom_label(entry: Any) -> str:
    text = collapse_ws(str(getattr(entry, "text", "")))
    if text:
        return text
    seed_name = getattr(entry, "seed_name", None)
    if callable(seed_name):
        return collapse_ws(str(seed_name()))
    return ""


def _sort_atom_context_from_fixture(fixture: DstUseCaseFixture) -> DstDiscoverySortAtomContext:
    return DstDiscoverySortAtomContext(
        actors=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("actors")),
        objectives=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("objectives")),
        capabilities=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("capabilities")),
        dependencies=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("dependencies")),
        constraints=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("constraints")),
        boundaries=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("boundaries")),
        states=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("states")),
        transitions=tuple(_sort_atom_label(entry) for entry in fixture.section_entries("transitions")),
        decisions=tuple(item.title for item in fixture.candidate_paths),
        timepoints=(),
    )


def build_reduce_not_discovery_prompt(fixture: DstUseCaseFixture) -> str:
    lines = [
        "You are performing governed candidate-path discovery for a DST use case.",
        "Treat the root as a non-achievedness about deciding among transformation paths.",
        "",
        "Root non-achievedness:",
        default_root_non_achievedness(fixture),
        "",
        "DST discovery objective:",
        "- identify the smallest set of materially distinct candidate paths, not cosmetic variants",
        "- identify dominant unresolved distinctions that separate those paths",
        "- identify blockers and missing facts that prevent justified commitment",
        "- preserve multiplicity; do not collapse to one recommendation",
        "- keep explicit facts, assumptions, ambiguities, and missing information separate",
        "",
        "DST sort-atom lexicon:",
        "- Actor: who decides, operates, coordinates, benefits, bears cost, or bears risk",
        "- Objective: what outcome, obligation, or public value the path is trying to advance",
        "- Capability: what operational or technical ability must exist, change, or be retired",
        "- Dependency: what enabling condition must be satisfied for a path or transition to work",
        "- Constraint: what binding prohibition, limit, or tradeoff is active",
        "- Boundary: what organizational, jurisdictional, semantic, or system boundary creates friction",
        "- State: what materially different system configuration is being assumed or targeted",
        "- Transition: what change step separates one state from another",
        "- Decision: what commitment selects one path, transition, or coordination arrangement",
        "- TimePoint: what sequencing or phasing distinction matters to viability",
        "",
        "Discovery discipline:",
        "- use DST sort-atom language when you describe why paths differ",
        "- if two paths differ mainly by dependency readiness, constraint activation, boundary friction, or time phasing, say so explicitly",
        "- if a distinction cannot yet be normalized into a final sort atom, still express it in sort-atom-adjacent language",
        "- stop refining once the candidate path set is governably useful",
        "",
        "Return exactly these top-level sections:",
        "1. candidate_path_families",
        "2. dominant_distinctions",
        "3. sort_atom_context",
        "4. shared_blockers",
        "5. assumptions",
        "6. ambiguities",
        "7. missing_information",
        "",
        "Section requirements:",
        "- candidate_path_families: for each path include path_id, title, route/configuration expression, summary, actor lens, objective lens, capability delta, dependency blockers, active constraints, boundary frictions, implicated states, candidate transitions, candidate decisions, time-phasing notes, and required information",
        "- dominant_distinctions: each distinction must name the candidate paths it separates and say whether it is primarily about actors, objectives, capabilities, dependencies, constraints, boundaries, states, transitions, decisions, or time",
        "- sort_atom_context: list the actor/objective/capability/dependency/constraint/boundary/state/transition/decision/timepoint candidates surfaced during discovery, even when they remain provisional",
        "- shared_blockers, assumptions, ambiguities, missing_information: keep them separate and machine-tractable",
        "",
        "Anti-drift rules:",
        "- do not solve the transformation",
        "- do not recommend one path unless the use case itself removes multiplicity",
        "- do not rename materially different paths into one blended future",
        "- do not omit sort-atom-adjacent context just because it is provisional",
        "",
        "Use case:",
        _fixture_source_block(fixture),
    ]
    return "\n".join(lines).strip() + "\n"


def build_dst_prompt_input(
    fixture: DstUseCaseFixture,
    discovery: DstDiscoveryResult,
) -> str:
    lines = [
        f"System name: {discovery.system_name or fixture.title}",
        f"Decision problem: {discovery.decision_problem or f'Decide how to guide {fixture.title}.'}",
    ]
    if discovery.root_non_achievedness:
        lines.extend(["", "Governed discovery root:", discovery.root_non_achievedness])
    lines.extend(["", "Source use case:", _fixture_source_block(fixture)])
    if discovery.candidate_paths:
        lines.extend(["", "Governed discovery candidate paths:"])
        for item in discovery.candidate_paths:
            lines.append(
                f"- {item.path_id} | {item.title} | kind={item.path_kind} | route={item.route_expression or '<none>'}"
            )
            if item.summary:
                lines.append(f"  summary: {item.summary}")
            if item.supporting_points:
                lines.append(f"  support: {'; '.join(item.supporting_points)}")
            if item.blockers:
                lines.append(f"  blockers: {'; '.join(item.blockers)}")
            if item.required_information:
                lines.append(f"  required_information: {'; '.join(item.required_information)}")
    if discovery.dominant_distinctions:
        lines.extend(["", "Dominant distinctions:"])
        for item in discovery.dominant_distinctions:
            lines.append(
                f"- {item.distinction_id} | {item.title} | separates={', '.join(item.separates_path_ids)}"
            )
            if item.description:
                lines.append(f"  {item.description}")
    if any(
        (
            discovery.sort_atom_context.actors,
            discovery.sort_atom_context.objectives,
            discovery.sort_atom_context.capabilities,
            discovery.sort_atom_context.dependencies,
            discovery.sort_atom_context.constraints,
            discovery.sort_atom_context.boundaries,
            discovery.sort_atom_context.states,
            discovery.sort_atom_context.transitions,
            discovery.sort_atom_context.decisions,
            discovery.sort_atom_context.timepoints,
        )
    ):
        lines.extend(["", "Governed discovery sort atom context:"])
        if discovery.sort_atom_context.actors:
            lines.append(f"- actors: {', '.join(discovery.sort_atom_context.actors)}")
        if discovery.sort_atom_context.objectives:
            lines.append(f"- objectives: {', '.join(discovery.sort_atom_context.objectives)}")
        if discovery.sort_atom_context.capabilities:
            lines.append(f"- capabilities: {', '.join(discovery.sort_atom_context.capabilities)}")
        if discovery.sort_atom_context.dependencies:
            lines.append(f"- dependencies: {', '.join(discovery.sort_atom_context.dependencies)}")
        if discovery.sort_atom_context.constraints:
            lines.append(f"- constraints: {', '.join(discovery.sort_atom_context.constraints)}")
        if discovery.sort_atom_context.boundaries:
            lines.append(f"- boundaries: {', '.join(discovery.sort_atom_context.boundaries)}")
        if discovery.sort_atom_context.states:
            lines.append(f"- states: {', '.join(discovery.sort_atom_context.states)}")
        if discovery.sort_atom_context.transitions:
            lines.append(f"- transitions: {', '.join(discovery.sort_atom_context.transitions)}")
        if discovery.sort_atom_context.decisions:
            lines.append(f"- decisions: {', '.join(discovery.sort_atom_context.decisions)}")
        if discovery.sort_atom_context.timepoints:
            lines.append(f"- timepoints: {', '.join(discovery.sort_atom_context.timepoints)}")
    if discovery.shared_blockers:
        lines.extend(["", "Shared blockers:"] + [f"- {item}" for item in discovery.shared_blockers])
    if discovery.assumptions:
        lines.extend(["", "Assumptions:"] + [f"- {item}" for item in discovery.assumptions])
    if discovery.ambiguities:
        lines.extend(["", "Ambiguities:"] + [f"- {item}" for item in discovery.ambiguities])
    if discovery.missing_information:
        lines.extend(["", "Missing information:"] + [f"- {item}" for item in discovery.missing_information])
    return "\n".join(lines).strip() + "\n"


def discovery_result_from_fixture(
    fixture: DstUseCaseFixture,
    *,
    decision_problem: str = "",
) -> DstDiscoveryResult:
    candidate_paths: list[DstDiscoveryPath] = []
    for index, item in enumerate(fixture.candidate_paths, start=1):
        route_tokens = [token.strip() for token in item.route_expression.split("->") if token.strip()]
        if len(route_tokens) >= 3:
            path_kind = "multi_step"
        elif len(route_tokens) == 2:
            path_kind = "single_step"
        elif "configuration" in item.title.lower() or "configuration" in item.narrative.lower():
            path_kind = "configuration"
        elif item.route_expression:
            path_kind = "configuration"
        else:
            path_kind = "unknown"
        candidate_paths.append(
            DstDiscoveryPath(
                path_id=_stable_path_id(item.title, index),
                title=item.title,
                path_kind=path_kind,
                route_expression=item.route_expression,
                summary=item.narrative,
                supporting_points=item.highlights,
            )
        )
    return DstDiscoveryResult(
        fixture_id=fixture.fixture_id,
        source_ref=fixture.source_ref,
        system_name=fixture.title,
        decision_problem=decision_problem or f"Decide how to guide {fixture.title}.",
        root_non_achievedness=default_root_non_achievedness(fixture),
        candidate_paths=tuple(candidate_paths),
        sort_atom_context=_sort_atom_context_from_fixture(fixture),
    )


__all__ = [
    "DST_DISCOVERY_FIXTURE_ROOT",
    "DST_DISCOVERY_SCHEMA_VERSION",
    "DST_SORT_ATOM_ORDER",
    "DstDiscoveryDistinction",
    "DstDiscoveryPath",
    "DstDiscoveryResult",
    "DstDiscoverySortAtomContext",
    "build_dst_prompt_input",
    "build_reduce_not_discovery_prompt",
    "default_root_non_achievedness",
    "dst_discovery_schema_hint",
    "discovery_result_from_fixture",
    "list_dst_discovery_fixture_paths",
    "load_dst_discovery_results",
]
