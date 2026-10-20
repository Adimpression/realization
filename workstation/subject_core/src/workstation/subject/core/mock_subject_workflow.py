# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import textwrap
from dataclasses import dataclass, field


MOCK_SUBJECT_PHASES: tuple[str, ...] = ("research", "review", "publication")
MOCK_SUBJECT_PHASE_TITLES: dict[str, str] = {
    "research": "Gather",
    "review": "Review",
    "publication": "Publication",
}


@dataclass(frozen=True)
class MockSubjectSource:
    path: str
    label: str
    observation: str


@dataclass(frozen=True)
class MockSubjectScenario:
    key: str
    title: str
    family_title: str
    context_id: str
    focus: str
    summary: str
    sources: tuple[MockSubjectSource, ...]
    delta_points: tuple[str, ...]
    subject_markdown_preview: str
    subject_typst_preview: str
    report_markdown_preview: str
    report_typst_preview: str


@dataclass
class MockSubjectProgress:
    observed_sources: int = 0
    captured_assistant_messages: list[str] = field(default_factory=list)
    intake_drafted: bool = False
    delta_admitted: bool = False
    context_opened: bool = False
    projections_compared: bool = False
    review_approved: bool = False
    publication_locked: bool = False
    report_built: bool = False
    release_packet_opened: bool = False
    review_preview_kind: str = "subject.md"
    publication_preview_kind: str = "report.typ"
    timeline: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MockSubjectActionSpec:
    key: str
    label: str
    enabled: bool


@dataclass(frozen=True)
class MockSubjectActionResult:
    status_text: str
    timeline_text: str = ""
    next_phase: str | None = None


def default_mock_subject_scenarios() -> tuple[MockSubjectScenario, ...]:
    return (
        MockSubjectScenario(
            key="chemistry_conservation",
            title="Chemistry Relations 01 — Conservation of Amount",
            family_title="Chemistry Relations 01 / Conservation",
            context_id="lc-chemistry-conservation-01",
            focus="Turn source material into one stable subject context, then review and publish it as a governed report.",
            summary="A subject-centered chemistry learning flow where markdown sources become admitted units, maintained subject projections, and a report publication.",
            sources=(
                MockSubjectSource(
                    path="trials/chemistry/07_LEARN_CHEMISTRY_RELATIONS_DILUTION.md",
                    label="Dilution relations learning markdown",
                    observation="Subject identity resolves to conservation-of-amount family material with one dilution-specific executable relation.",
                ),
                MockSubjectSource(
                    path="tmp/sources/chemistry/conservation-notes.md",
                    label="Conservation notes",
                    observation="The source reinforces family-level invariants and clarifies where atom, mole, and mass conservation should stay distinct.",
                ),
                MockSubjectSource(
                    path="tmp/sources/chemistry/balance-examples.md",
                    label="Worked balance examples",
                    observation="Examples contribute reviewable claims and example blocks rather than new root subject identity.",
                ),
            ),
            delta_points=(
                "Admit one stable subject context rooted at conservation of amount.",
                "Refresh maintained subject projections: subject.md and subject.typ.",
                "Keep executable dilution ability attached as a derived artifact, not as the subject identity itself.",
                "Carry forward reusable family material under the chemistry conservation family.",
            ),
            subject_markdown_preview=(
                "# Chemistry Relations 01 — Conservation of Amount\n\n"
                "## Subject Position\n"
                "Conservation of amount is the governing relation for this subject family.\n\n"
                "## Maintained Units\n"
                "- family definition: Chemistry Relations 01 / Conservation\n"
                "- subject explanation: conservation of amount across transformations\n"
                "- executable relation: dilution example ability\n"
            ),
            subject_typst_preview=(
                "#let subject-id = \"chemistry-conservation-01\"\n"
                "#show heading: set text(weight: \"bold\")\n\n"
                "= Chemistry Relations 01 — Conservation of Amount\n"
                "This maintained projection is generated from admitted learning units.\n"
            ),
            report_markdown_preview=(
                "# Report: Chemistry Relations 01\n\n"
                "## Scope\n"
                "This report summarizes the admitted subject context, reusable family material, and executable relation coverage.\n"
            ),
            report_typst_preview=(
                "#let publication-id = \"pub-report-chemistry-conservation-01\"\n"
                "#set page(margin: 1in)\n\n"
                "= Report: Chemistry Relations 01\n"
                "== Scope\n"
                "This report is rendered deterministically from the maintained subject context.\n"
            ),
        ),
        MockSubjectScenario(
            key="agentic_governance",
            title="Agentic Workflow Governance / Approval Gates",
            family_title="Governance / Approval Gates",
            context_id="lc-agentic-governance-approval-gates",
            focus="Observe multi-source governance material, review admitted claims, then ship one report-oriented publication with stable provenance.",
            summary="A policy subject where research intake becomes reviewed claims, maintained Typst/markdown projections, and a reproducible report build.",
            sources=(
                MockSubjectSource(
                    path="notes/research/approval-gates-oecd.md",
                    label="OECD approval gates notes",
                    observation="The source contributes descriptive governance evidence and approval gate terminology.",
                ),
                MockSubjectSource(
                    path="notes/research/public-sector-ai-controls.md",
                    label="Public-sector control matrix",
                    observation="The source adds a structured threshold model for when high-impact actions require explicit approval.",
                ),
                MockSubjectSource(
                    path="notes/research/operator-receipts.md",
                    label="Operator receipts and provenance notes",
                    observation="The source sharpens how receipts, artifacts, and approvals should appear in deterministic publications.",
                ),
            ),
            delta_points=(
                "Admit typed claims separating descriptive evidence from normative recommendations.",
                "Refresh the maintained governance subject in subject.md and subject.typ.",
                "Prepare one report publication centered on approval checkpoints and execution provenance.",
                "Expose validation warnings before release rather than burying them in the build output.",
            ),
            subject_markdown_preview=(
                "# Agentic Workflow Governance / Approval Gates\n\n"
                "## Governing Claim\n"
                "High-impact actions require explicit approval checkpoints.\n\n"
                "## Maintained Distinctions\n"
                "- descriptive evidence\n"
                "- normative recommendations\n"
                "- receipt and provenance records\n"
            ),
            subject_typst_preview=(
                "#let subject-id = \"agentic-governance-approval-gates\"\n\n"
                "= Agentic Workflow Governance / Approval Gates\n"
                "This Typst projection is the maintained corpus view for the subject.\n"
            ),
            report_markdown_preview=(
                "# Report: Approval Gates For Agentic Workflows\n\n"
                "## Recommendation Summary\n"
                "Organizations should gate high-impact actions through explicit approval checkpoints.\n"
            ),
            report_typst_preview=(
                "#let publication-id = \"pub-report-agentic-governance-approval-gates\"\n\n"
                "= Report: Approval Gates For Agentic Workflows\n"
                "== Recommendation Summary\n"
                "The report is built from reviewed subject content and typed publication inputs.\n"
            ),
        ),
    )


def new_mock_subject_progress() -> MockSubjectProgress:
    progress = MockSubjectProgress()
    progress.timeline.append("Demo subject opened.")
    return progress


def mock_subject_phase_title(phase: str) -> str:
    return MOCK_SUBJECT_PHASE_TITLES.get(str(phase or ""), "Gather")


def mock_subject_action_specs(
    *,
    scenario: MockSubjectScenario,
    progress: MockSubjectProgress,
    phase: str,
    can_capture_assistant: bool = False,
) -> tuple[MockSubjectActionSpec, MockSubjectActionSpec, MockSubjectActionSpec, MockSubjectActionSpec]:
    normalized = str(phase or "research")
    if normalized == "review":
        return (
            MockSubjectActionSpec(
                key="open_context",
                label="Open Context",
                enabled=progress.delta_admitted and not progress.context_opened,
            ),
            MockSubjectActionSpec(
                key="compare_projections",
                label="Compare Projections",
                enabled=progress.context_opened and not progress.projections_compared,
            ),
            MockSubjectActionSpec(
                key="approve_review",
                label="Approve For Report",
                enabled=progress.projections_compared and not progress.review_approved,
            ),
            MockSubjectActionSpec(
                key="toggle_review_preview",
                label=f"Preview {progress.review_preview_kind}",
                enabled=progress.delta_admitted,
            ),
        )
    if normalized == "publication":
        return (
            MockSubjectActionSpec(
                key="lock_publication",
                label="Lock Inputs",
                enabled=progress.review_approved and not progress.publication_locked,
            ),
            MockSubjectActionSpec(
                key="build_report",
                label="Build Report",
                enabled=progress.publication_locked and not progress.report_built,
            ),
            MockSubjectActionSpec(
                key="open_release_packet",
                label="Open Release Packet",
                enabled=progress.report_built and not progress.release_packet_opened,
            ),
            MockSubjectActionSpec(
                key="toggle_publication_preview",
                label=f"Preview {progress.publication_preview_kind}",
                enabled=progress.review_approved,
            ),
        )
    return (
        MockSubjectActionSpec(
            key="observe_source",
            label="Observe Next Source",
            enabled=progress.observed_sources < len(scenario.sources),
        ),
        MockSubjectActionSpec(
            key="capture_last_assistant",
            label="Add Last Assistant",
            enabled=can_capture_assistant and not progress.delta_admitted,
        ),
        MockSubjectActionSpec(
            key="draft_intake",
            label="Draft Intake Delta",
            enabled=(progress.observed_sources > 0 or bool(progress.captured_assistant_messages)) and not progress.intake_drafted,
        ),
        MockSubjectActionSpec(
            key="goto_review" if progress.delta_admitted else "admit_delta",
            label="Send To Review" if progress.delta_admitted else "Admit To Context",
            enabled=progress.delta_admitted or progress.intake_drafted,
        ),
    )


def apply_mock_subject_action(
    *,
    scenario: MockSubjectScenario,
    progress: MockSubjectProgress,
    action_key: str,
    assistant_message_text: str = "",
) -> MockSubjectActionResult:
    normalized = str(action_key or "")
    if normalized == "reset_subject":
        progress.observed_sources = 0
        progress.intake_drafted = False
        progress.delta_admitted = False
        progress.context_opened = False
        progress.projections_compared = False
        progress.review_approved = False
        progress.publication_locked = False
        progress.report_built = False
        progress.release_packet_opened = False
        progress.review_preview_kind = "subject.md"
        progress.publication_preview_kind = "report.typ"
        progress.timeline[:] = ["Demo subject reset."]
        return MockSubjectActionResult("Mock subject workflow reset.", "Demo subject reset.")
    if normalized == "observe_source":
        if progress.observed_sources >= len(scenario.sources):
            return MockSubjectActionResult("All mock sources are already observed.")
        source = scenario.sources[progress.observed_sources]
        progress.observed_sources += 1
        entry = f"Observed contents from {source.path}."
        progress.timeline.append(entry)
        return MockSubjectActionResult(f"Observed source: {source.label}.", entry)
    if normalized == "capture_last_assistant":
        captured_text = str(assistant_message_text or "").strip()
        if not captured_text:
            return MockSubjectActionResult("No assistant message is available to add.")
        progress.captured_assistant_messages.append(captured_text)
        if progress.intake_drafted and not progress.delta_admitted:
            progress.intake_drafted = False
            entry = "Captured the last assistant message into intake and reopened drafting."
            progress.timeline.append(entry)
            return MockSubjectActionResult("Last assistant message added. Redraft intake.", entry)
        entry = "Captured the last assistant message into research intake."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Last assistant message added to intake.", entry)
    if normalized == "draft_intake":
        if progress.observed_sources <= 0 and not progress.captured_assistant_messages:
            return MockSubjectActionResult("Observe a source or add the last assistant message before drafting intake.")
        if progress.intake_drafted:
            return MockSubjectActionResult("Gather intake is already drafted.")
        progress.intake_drafted = True
        entry = "Drafted governed intake against the selected subject context."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Gather intake drafted.", entry)
    if normalized == "admit_delta":
        if not progress.intake_drafted:
            return MockSubjectActionResult("Draft intake before admitting the delta.")
        if progress.delta_admitted:
            return MockSubjectActionResult("The mock delta is already admitted.")
        progress.delta_admitted = True
        entry = "Admitted the mock learning delta into LearningContext."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Learning delta admitted.", entry)
    if normalized == "goto_review":
        if not progress.delta_admitted:
            return MockSubjectActionResult("Admit the delta before moving to review.")
        entry = "Shifted the subject workflow into Review."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Moved to Review.", entry, next_phase="review")
    if normalized == "open_context":
        if not progress.delta_admitted:
            return MockSubjectActionResult("Admit the mock delta before opening the context.")
        if progress.context_opened:
            return MockSubjectActionResult("The mock subject context is already open.")
        progress.context_opened = True
        entry = f"Opened subject context {scenario.context_id}."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Subject context opened.", entry)
    if normalized == "compare_projections":
        if not progress.context_opened:
            return MockSubjectActionResult("Open the context before comparing projections.")
        if progress.projections_compared:
            return MockSubjectActionResult("Subject projections are already compared.")
        progress.projections_compared = True
        entry = "Compared subject.md and subject.typ projections."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Projections compared.", entry)
    if normalized == "approve_review":
        if not progress.projections_compared:
            return MockSubjectActionResult("Compare projections before approving review.")
        if progress.review_approved:
            return MockSubjectActionResult("Review is already approved for publication.")
        progress.review_approved = True
        entry = "Marked the subject review as ready for report publication."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Review approved for report publication.", entry)
    if normalized == "toggle_review_preview":
        if not progress.delta_admitted:
            return MockSubjectActionResult("Admit the delta before switching review previews.")
        progress.review_preview_kind = "subject.typ" if progress.review_preview_kind == "subject.md" else "subject.md"
        entry = f"Switched review preview to {progress.review_preview_kind}."
        progress.timeline.append(entry)
        return MockSubjectActionResult(f"Showing {progress.review_preview_kind}.", entry)
    if normalized == "lock_publication":
        if not progress.review_approved:
            return MockSubjectActionResult("Approve review before locking publication inputs.")
        if progress.publication_locked:
            return MockSubjectActionResult("Publication inputs are already locked.")
        progress.publication_locked = True
        entry = "Locked report publication inputs."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Publication inputs locked.", entry)
    if normalized == "build_report":
        if not progress.publication_locked:
            return MockSubjectActionResult("Lock publication inputs before building the report.")
        if progress.report_built:
            return MockSubjectActionResult("The mock report build already exists.")
        progress.report_built = True
        entry = "Built the mock report publication."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Report build completed.", entry)
    if normalized == "open_release_packet":
        if not progress.report_built:
            return MockSubjectActionResult("Build the report before opening the release packet.")
        if progress.release_packet_opened:
            return MockSubjectActionResult("The release packet is already open.")
        progress.release_packet_opened = True
        entry = "Opened the mock publication release packet."
        progress.timeline.append(entry)
        return MockSubjectActionResult("Release packet opened.", entry)
    if normalized == "toggle_publication_preview":
        if not progress.review_approved:
            return MockSubjectActionResult("Approve review before switching publication previews.")
        progress.publication_preview_kind = (
            "report.md" if progress.publication_preview_kind == "report.typ" else "report.typ"
        )
        entry = f"Switched publication preview to {progress.publication_preview_kind}."
        progress.timeline.append(entry)
        return MockSubjectActionResult(f"Showing {progress.publication_preview_kind}.", entry)
    return MockSubjectActionResult("No mock action was applied.")


def render_mock_subject_status(
    *,
    scenario: MockSubjectScenario,
    progress: MockSubjectProgress,
    phase: str,
) -> str:
    research_status = (
        f"{progress.observed_sources}/{len(scenario.sources)} sources observed, "
        f"intake={'yes' if progress.intake_drafted else 'no'}, "
        f"delta={'admitted' if progress.delta_admitted else 'pending'}"
    )
    review_status = (
        f"context={'open' if progress.context_opened else 'closed'}, "
        f"compared={'yes' if progress.projections_compared else 'no'}, "
        f"ready={'yes' if progress.review_approved else 'no'}"
    )
    publication_status = (
        f"inputs={'locked' if progress.publication_locked else 'open'}, "
        f"build={'ready' if progress.report_built else 'pending'}, "
        f"packet={'open' if progress.release_packet_opened else 'pending'}"
    )
    lines = [
        "Mode: Mocked subject workflow",
        f"Phase: {mock_subject_phase_title(phase)}",
        f"Subject: {scenario.title}",
        f"Context: {scenario.context_id}",
        f"Family: {scenario.family_title}",
        f"Focus: {scenario.focus}",
        "",
        f"Gather: {research_status}",
        f"Review: {review_status}",
        f"Publication: {publication_status}",
    ]
    return "\n".join(lines)


def render_mock_subject_workspace(
    *,
    scenario: MockSubjectScenario,
    progress: MockSubjectProgress,
    phase: str,
) -> str:
    normalized = str(phase or "research")
    if normalized == "review":
        return _render_review_workspace(scenario=scenario, progress=progress)
    if normalized == "publication":
        return _render_publication_workspace(scenario=scenario, progress=progress)
    return _render_research_workspace(scenario=scenario, progress=progress)


def render_mock_subject_research_sources(
    *,
    scenario: MockSubjectScenario,
    progress: MockSubjectProgress,
) -> str:
    lines = ["Source Queue"]
    for index, source in enumerate(scenario.sources, start=1):
        if index <= progress.observed_sources:
            state = "observed"
        elif index == progress.observed_sources + 1:
            state = "next"
        else:
            state = "queued"
        lines.append("")
        lines.append(f"{index}. [{state}] {source.label}")
        lines.append(f"   {source.path}")
    if progress.observed_sources >= len(scenario.sources):
        lines.extend(["", "All mock sources observed."])
    return "\n".join(lines)


def render_mock_subject_research_observation(
    *,
    scenario: MockSubjectScenario,
    progress: MockSubjectProgress,
) -> str:
    extracted_lines = ["Observed Contents"]
    if progress.observed_sources <= 0:
        extracted_lines.extend(["", "No source observed yet.", "", "Start with `Observe Next Source`."])
    else:
        source = scenario.sources[min(progress.observed_sources - 1, len(scenario.sources) - 1)]
        extracted_lines.extend(
            [
                "",
                f"Current source: {source.label}",
                f"Path: {source.path}",
                "",
                "Contribution",
                source.observation,
            ]
        )
    if progress.captured_assistant_messages:
        extracted_lines.extend(["", "Captured Assistant Messages"])
        for index, item in enumerate(progress.captured_assistant_messages[-3:], start=1):
            extracted_lines.append(
                f"{index}. {textwrap.shorten(collapse_ws_for_mock(item), width=120, placeholder='...')}"
            )
    if progress.intake_drafted:
        extracted_lines.extend(
            [
                "",
                "Drafted Intake",
                "- source classified against the selected subject",
                "- latest assistant reasoning folded into the proposed intake when captured",
                "- contribution prepared as a proposed learning delta",
            ]
        )
    return "\n".join(extracted_lines)


def render_mock_subject_research_target(
    *,
    scenario: MockSubjectScenario,
    progress: MockSubjectProgress,
) -> str:
    lines = [
        "Subject Target",
        "",
        f"Subject: {scenario.title}",
        f"Family: {scenario.family_title}",
        f"Context: {scenario.context_id}",
        "",
        "Intake State",
        f"- observed sources: {progress.observed_sources}/{len(scenario.sources)}",
        f"- captured assistant messages: {len(progress.captured_assistant_messages)}",
        f"- intake drafted: {'yes' if progress.intake_drafted else 'no'}",
        f"- delta admitted: {'yes' if progress.delta_admitted else 'no'}",
        "",
        "Admission Target",
        "- target store: LearningContext",
        "- maintained projections: subject.md, subject.typ",
        "- captured assistant content: source_note / intake material until admitted",
    ]
    if progress.delta_admitted:
        lines.extend(["", "Next handoff", "- send the admitted subject to Review"])
    return "\n".join(lines)


def _render_research_workspace(*, scenario: MockSubjectScenario, progress: MockSubjectProgress) -> str:
    next_action = "Observe a source."
    if progress.observed_sources > 0 and not progress.intake_drafted:
        next_action = "Draft intake against the selected subject."
    if progress.intake_drafted and not progress.delta_admitted:
        next_action = "Admit the proposed delta."
    if progress.delta_admitted:
        next_action = "Switch to Review."
    history_lines = [f"- {item}" for item in progress.timeline[-6:]]
    return "\n".join(
        [
            f"Gather Journal: {scenario.title}",
            "",
            "Gather Method",
            "- observe source contents",
            "- optionally add the last assistant message from Chat into intake",
            "- resolve subject and family target",
            "- draft a proposed learning delta",
            "- admit the delta into LearningContext",
            "- hand off to Review",
            "",
            f"Next Intended Action: {next_action}",
            "",
            "Current Delta Shape",
            *[f"- {item}" for item in scenario.delta_points],
            f"- captured assistant messages available to intake: {len(progress.captured_assistant_messages)}",
            "",
            "Recent Mock Events",
            *(history_lines or ["- Demo subject opened."]),
        ]
    )


def collapse_ws_for_mock(text: str) -> str:
    return " ".join(str(text or "").split())


def _render_review_workspace(*, scenario: MockSubjectScenario, progress: MockSubjectProgress) -> str:
    preview_kind = progress.review_preview_kind
    preview_text = (
        scenario.subject_typst_preview if preview_kind == "subject.typ" else scenario.subject_markdown_preview
    )
    gate_line = (
        "Review is blocked until the research delta is admitted."
        if not progress.delta_admitted
        else "Review is active over the admitted subject context."
    )
    history_lines = [f"- {item}" for item in progress.timeline[-6:]]
    return "\n".join(
        [
            f"Review Workspace: {scenario.context_id}",
            "",
            gate_line,
            "",
            "Review Checks",
            f"- context opened: {'yes' if progress.context_opened else 'no'}",
            f"- projections compared: {'yes' if progress.projections_compared else 'no'}",
            f"- ready for report: {'yes' if progress.review_approved else 'no'}",
            "",
            f"Projection Preview [{preview_kind}]",
            preview_text,
            "",
            "Recent Mock Events",
            *(history_lines or ["- Demo subject opened."]),
        ]
    )


def _render_publication_workspace(*, scenario: MockSubjectScenario, progress: MockSubjectProgress) -> str:
    preview_kind = progress.publication_preview_kind
    preview_text = (
        scenario.report_markdown_preview if preview_kind == "report.md" else scenario.report_typst_preview
    )
    validation_lines = [
        f"[{'x' if progress.review_approved else ' '}] reviewed subject selected",
        f"[{'x' if progress.publication_locked else ' '}] publication inputs locked",
        f"[{'x' if progress.report_built else ' '}] report build produced",
        f"[{'x' if progress.release_packet_opened else ' '}] release packet reviewed",
    ]
    history_lines = [f"- {item}" for item in progress.timeline[-6:]]
    return "\n".join(
        [
            f"Publication Workspace: report / {scenario.key}",
            "",
            "Publication Contract",
            "- publication type: Report",
            f"- subject context: {scenario.context_id}",
            "- output family: typst + markdown + receipts",
            "",
            "Validation Snapshot",
            *validation_lines,
            "",
            f"Output Preview [{preview_kind}]",
            preview_text,
            "",
            "Recent Mock Events",
            *(history_lines or ["- Demo subject opened."]),
        ]
    )
