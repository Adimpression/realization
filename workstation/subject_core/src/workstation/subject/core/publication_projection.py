# See MODULES.md for the repository module map before editing.
"""Subject-domain projection from governed learning state to publications."""

from __future__ import annotations

import json
from pathlib import Path
import re

from realized_core_semantics.decision_review import DecisionFrame, DecisionReviewItem
from workstation.subject.core.decision_review_policy import DecisionPolicyProfile
from workstation.subject.core.decision_review_projection import DecisionAnalysisReceipt
from workstation.subject.core.learning_context import (
    LearningContext,
    LearningUnit,
    SubjectImport,
    list_subject_imports,
    load_learning_source,
)
from workstation.subject.core.publication import (
    Publication,
    PublicationBlock,
    PublicationClaim,
    PublicationComposition,
    PublicationCrossReference,
    PublicationEntity,
    PublicationReviewRecord,
    PublicationSection,
    PublicationSource,
    persist_publication,
    persist_publication_composition,
    persist_publication_build,
    publication_statement_is_reportable,
    stable_publication_block_id,
    stable_publication_composition_id,
    stable_publication_entity_id,
    stable_publication_id,
    stable_publication_review_id,
    stable_publication_xref_id,
)
from workstation.subject.core.publication_render import (
    publication_build_from_rendered_outputs,
    render_publication_markdown,
    render_publication_typst,
    validate_rendered_typst,
)
from workstation.subject.core.publication_validation import validate_publication
from workstation.subject.core.review_composition import ReviewItem, ReviewTransformReceipt, flatten_review_item_tree, review_item_split_labels
from realized_core_semantics.semantic_text import collapse_ws


_REPORT_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("report-summary", "summary", "Summary"),
    ("report-definitions", "definition", "Definitions"),
    ("report-analysis", "analysis", "Analysis"),
    ("report-implementation", "implementation", "Implementation"),
    ("report-evidence", "evidence", "Evidence"),
    ("report-appendix", "appendix", "Appendix"),
)

_DECISION_REPORT_SECTION_CHILDREN: dict[str, tuple[tuple[str, str, str], ...]] = {
    "report-analysis": (
        ("report-analysis-options", "analysis", "Option Assessment"),
        ("report-analysis-model", "analysis", "Path and Coordination Model"),
        ("report-analysis-risk", "analysis", "Dependencies and Risk"),
    ),
    "report-implementation": (
        ("report-implementation-guidance", "implementation", "Recommended Operating Model"),
    ),
    "report-appendix": (
        ("report-appendix-receipt", "appendix", "Decision Receipt and Audit Trail"),
    ),
}

_SECTION_XREF_RULES: tuple[tuple[str, str, str], ...] = (
    ("report-analysis", "depends_on", "report-definitions"),
    ("report-implementation", "depends_on", "report-analysis"),
    ("report-implementation", "depends_on", "report-definitions"),
    ("report-evidence", "supports", "report-analysis"),
    ("report-appendix", "see_also", "report-analysis"),
)

_SECTION_ROLE_BLOCK_BODIES: dict[str, str] = {
    "summary": "This section summarizes the governed publication scope for the current subject snapshot.",
    "definition": "This section holds stable descriptive anchors and terminology for the subject.",
    "analysis": "This section interprets relations, limits, and explanatory structure across the admitted learning units.",
    "implementation": "This section captures procedural or executable ability derived from the admitted learning units.",
    "evidence": "This section surfaces source-backed examples and supporting evidence carried into the publication.",
    "appendix": "This section retains governed residual material that is useful but not part of the main narrative spine.",
}

_DEFAULT_REPORT_SECTION_LIMITS: dict[str, int] = {
    "report-definitions": 2,
    "report-analysis": 3,
    "report-implementation": 2,
    "report-evidence": 1,
    "report-appendix": 1,
}

_INLINE_BLOCKQUOTE_STATEMENT_RE = re.compile(r"^(?P<prefix>.+?)[,:;]\s*>\s*(?P<remainder>.+)$")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_INLINE_BLOCKQUOTE_EXPLANATION_STARTERS = {
    "a",
    "an",
    "because",
    "but",
    "in",
    "it",
    "it's",
    "its",
    "note",
    "notes",
    "that",
    "that's",
    "the",
    "these",
    "they",
    "this",
    "those",
    "we",
    "when",
    "where",
    "which",
}

_PUBLICATION_SECTION_GUIDANCE_KEY = "section_guidance_by_id"


def report_section_specs() -> tuple[tuple[str, str, str], ...]:
    return _REPORT_SECTIONS


def _expanded_report_sections(*, decision_report_mode: bool) -> tuple[tuple[str, str, str, str], ...]:
    specs: list[tuple[str, str, str, str]] = []
    for root_section_id, role, title in _REPORT_SECTIONS:
        specs.append((root_section_id, role, title, ""))
        if decision_report_mode:
            for child_section_id, child_role, child_title in _DECISION_REPORT_SECTION_CHILDREN.get(root_section_id, ()):
                specs.append((child_section_id, child_role, child_title, root_section_id))
    return tuple(specs)


def _section_title_for_block_kinds(
    section_id: str,
    *,
    default_title: str,
    block_kinds: set[str],
) -> str:
    if section_id == "report-analysis-options":
        has_matrix = "decision_matrix" in block_kinds
        has_ranking = "decision_ranking_summary" in block_kinds
        if has_matrix and has_ranking:
            return "Option Assessment and Ranking"
        if has_ranking:
            return "Option Ranking"
        if has_matrix:
            return "Option Assessment"
    elif section_id == "report-analysis-model":
        has_roadmap = "decision_transition_roadmap" in block_kinds
        has_diagram = "decision_simple_diagram" in block_kinds
        if has_roadmap and has_diagram:
            return "Path and Coordination Model"
        if has_diagram:
            return "Coordination Model"
        if has_roadmap:
            return "Transition Roadmap"
    elif section_id == "report-analysis-risk":
        has_dependencies = "decision_dependency_checklist" in block_kinds
        has_risk = "decision_risk_matrix" in block_kinds
        if has_dependencies and has_risk:
            return "Dependencies and Risk"
        if has_dependencies:
            return "Dependency Conditions"
        if has_risk:
            return "Risk Assessment"
    elif section_id == "report-implementation-guidance":
        if "decision_execution_guidance" in block_kinds:
            return "Execution Guidance"
    elif section_id == "report-appendix-receipt":
        has_decision_receipt = "decision_recommendation_receipt" in block_kinds
        has_transform_receipts = "review_transform_receipts" in block_kinds
        if has_decision_receipt and has_transform_receipts:
            return "Decision Receipt and Audit Trail"
        if has_decision_receipt:
            return "Decision Recommendation Receipt"
        if has_transform_receipts:
            return "Transform Audit Trail"
    return default_title


def _publication_scope_summary_text(*, publication_type: str, subject_title: str) -> str:
    normalized = collapse_ws(publication_type).casefold()
    if normalized == "exact_draft":
        return f"Exact drafted output for {subject_title}."
    return f"Governed {publication_type} projection for {subject_title}."


def _section_guidance_entries_from_metadata(
    composition_metadata: dict[str, object] | None,
) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(composition_metadata, dict):
        return ()
    raw_guidance_by_id = composition_metadata.get(_PUBLICATION_SECTION_GUIDANCE_KEY, {})
    if not isinstance(raw_guidance_by_id, dict):
        return ()
    entries: list[tuple[str, str, str]] = []
    for section_id, raw_entry in raw_guidance_by_id.items():
        normalized_section_id = collapse_ws(str(section_id))
        if not normalized_section_id or not isinstance(raw_entry, dict):
            continue
        label = collapse_ws(str(raw_entry.get("label", "")))
        text = str(raw_entry.get("text", "")).strip()
        if not text:
            continue
        entries.append((normalized_section_id, label, text))
    return tuple(entries)


def _section_guidance_block(
    publication_id: str,
    *,
    section_id: str,
    title: str,
    label: str,
    text: str,
) -> PublicationBlock:
    block_title = label or f"{title} Brief"
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="section_guidance",
            title=block_title,
            anchor_id=section_id,
        ),
        publication_id=publication_id,
        block_kind="section_guidance",
        title=block_title,
        body=text,
        included_block_refs=(),
        status="active",
    )


def _is_exact_draft_publication_type(publication_type: str) -> bool:
    return collapse_ws(publication_type).casefold() == "exact_draft"


def _split_inline_blockquote_remainder(remainder: str) -> tuple[str, str]:
    tokens = collapse_ws(remainder).split()
    if not tokens:
        return "", ""
    cut_index = len(tokens)
    for index, token in enumerate(tokens[1:], start=1):
        normalized = token.strip(".,;:!?\"'“”’()[]{}").casefold()
        if not normalized:
            continue
        if token[:1].isupper() and (
            normalized in _INLINE_BLOCKQUOTE_EXPLANATION_STARTERS or "'" in token or "’" in token
        ):
            cut_index = index
            break
    quoted = " ".join(tokens[:cut_index]).strip(" ,;:.")
    trailing = " ".join(tokens[cut_index:]).strip()
    return quoted, trailing


def _reader_facing_claim_statement(text: str) -> str:
    rendered = collapse_ws(text)
    if not rendered:
        return ""
    rendered = _MARKDOWN_LINK_RE.sub(
        lambda match: f"{collapse_ws(match.group(1))} ({collapse_ws(match.group(2))})",
        rendered,
    )
    match = _INLINE_BLOCKQUOTE_STATEMENT_RE.match(rendered)
    if match is None:
        return rendered
    prefix = collapse_ws(match.group("prefix")).rstrip(",:;")
    quoted, trailing = _split_inline_blockquote_remainder(match.group("remainder"))
    if not quoted:
        return rendered
    if trailing:
        return collapse_ws(f'{prefix} "{quoted}". {trailing}')
    return collapse_ws(f'{prefix} "{quoted}".')


def _workstation_workspace_root(root_path: Path) -> Path | None:
    session_path = Path(root_path).expanduser().resolve() / "SESSION.json"
    if not session_path.is_file():
        return None
    try:
        payload = json.loads(session_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    workspace_text = collapse_ws(str(payload.get("workspace_path", "")))
    if not workspace_text:
        return None
    try:
        return Path(workspace_text).expanduser().resolve()
    except Exception:
        return Path(workspace_text).expanduser()


def _source_checkout_root() -> Path | None:
    try:
        module_path = Path(__file__).resolve()
    except Exception:
        return None
    for candidate in module_path.parents:
        if (candidate / "MODULES.md").is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    return None


def _publication_source_ref_label(root_path: Path, source_ref: str) -> str:
    normalized = collapse_ws(source_ref)
    if not normalized:
        return ""
    path = Path(normalized).expanduser()
    if not path.is_absolute():
        return normalized
    try:
        resolved = path.resolve(strict=False)
    except Exception:
        resolved = path
    workspace_root = _workstation_workspace_root(root_path)
    candidate_roots: list[Path] = []
    if workspace_root is not None:
        candidate_roots.append(workspace_root)
    try:
        candidate_roots.append(Path(root_path).expanduser().resolve())
    except Exception:
        candidate_roots.append(Path(root_path).expanduser())
    source_checkout_root = _source_checkout_root()
    if source_checkout_root is not None:
        candidate_roots.append(source_checkout_root)
    for candidate_root in candidate_roots:
        try:
            return str(resolved.relative_to(candidate_root))
        except Exception:
            continue
    return normalized


def _decision_frame_from_metadata(metadata: dict[str, object]) -> DecisionFrame | None:
    payload = metadata.get("decision_frame", {})
    if not isinstance(payload, dict):
        return None
    frame = DecisionFrame.from_dict(payload)
    return frame if collapse_ws(frame.decision_frame_id) else None


def _decision_policy_profile_from_metadata(metadata: dict[str, object]) -> DecisionPolicyProfile | None:
    payload = metadata.get("decision_policy_profile", {})
    if not isinstance(payload, dict):
        return None
    profile = DecisionPolicyProfile.from_dict(payload)
    return profile if collapse_ws(profile.policy_profile_id) else None


def _decision_analysis_receipt_from_metadata(metadata: dict[str, object]) -> DecisionAnalysisReceipt | None:
    payload = metadata.get("decision_analysis_receipt", {})
    if not isinstance(payload, dict):
        return None
    receipt = DecisionAnalysisReceipt.from_dict(payload)
    return receipt if collapse_ws(receipt.receipt_id) else None


def _decision_review_items_from_metadata(metadata: dict[str, object]) -> tuple[DecisionReviewItem, ...]:
    payloads = metadata.get("decision_review_items", [])
    if not isinstance(payloads, list):
        return ()
    items: list[DecisionReviewItem] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        item = DecisionReviewItem.from_dict(payload)
        if collapse_ws(item.decision_review_item_id):
            items.append(item)
    return tuple(sorted(items, key=lambda item: (int(item.ordering or 0), item.decision_review_item_id)))


def _review_transform_receipts_from_metadata(metadata: dict[str, object]) -> tuple[ReviewTransformReceipt, ...]:
    payloads = metadata.get("review_transform_receipts", [])
    if not isinstance(payloads, list):
        return ()
    receipts: list[ReviewTransformReceipt] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        receipt = ReviewTransformReceipt.from_dict(payload)
        if collapse_ws(receipt.receipt_id):
            receipts.append(receipt)
    return tuple(receipts)


def _claim_kind_for_unit(unit: LearningUnit) -> str:
    if unit.unit_kind == "ability":
        return "procedural"
    if unit.unit_kind in {"misconception", "boundary", "counterexample"}:
        return "interpretive"
    return "descriptive"


def _section_key_for_unit(unit: LearningUnit) -> str:
    if unit.unit_kind == "definition":
        return "report-definitions"
    if unit.unit_kind == "ability":
        return "report-implementation"
    if unit.unit_kind in {"relation", "misconception", "boundary"}:
        return "report-analysis"
    if unit.unit_kind in {"example", "counterexample", "source_note"}:
        return "report-evidence"
    return "report-appendix"


def _section_key_for_review_item(item: ReviewItem, unit: LearningUnit) -> str:
    render_kind = collapse_ws(item.render_kind)
    semantic_kind = collapse_ws(item.semantic_kind)
    if render_kind == "equation_block":
        return "report-definitions"
    if render_kind in {"decision_table", "flow_diagram", "dependency_diagram"}:
        return "report-analysis"
    if render_kind == "typst_table":
        return "report-evidence"
    if semantic_kind == "definition":
        return "report-definitions"
    if semantic_kind in {"equation", "metric", "decision_rule", "timeline", "risk_control"}:
        return "report-analysis"
    if semantic_kind == "figure_asset":
        return "report-evidence"
    return _section_key_for_unit(unit)


def _review_items_from_composition_metadata(metadata: dict[str, object]) -> tuple[ReviewItem, ...]:
    payloads = metadata.get("draft_review_items", [])
    if not isinstance(payloads, list):
        return ()
    items: list[ReviewItem] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        item = ReviewItem.from_dict(payload)
        if collapse_ws(item.review_item_id):
            items.append(item)
    return tuple(items)


def _ordered_included_leaf_review_items(items: tuple[ReviewItem, ...]) -> tuple[ReviewItem, ...]:
    active_item_ids = {
        collapse_ws(item.review_item_id)
        for item in items
        if collapse_ws(item.status) != "rejected" and collapse_ws(item.review_item_id)
    }
    ordered_leaves: list[ReviewItem] = []
    for item, _depth in flatten_review_item_tree(items):
        if (
            collapse_ws(item.status) == "rejected"
            or not item.included
            or not collapse_ws(item.source_unit_id)
            or any(collapse_ws(child_id) in active_item_ids for child_id in item.child_review_item_ids)
        ):
            continue
        ordered_leaves.append(item)
    return tuple(ordered_leaves)


def _claim_statement_for_review_item(item: ReviewItem, unit: LearningUnit) -> str:
    notes = collapse_ws(item.notes)
    if notes:
        return _reader_facing_claim_statement(notes)
    canonical_label = collapse_ws(str(item.metadata.get("canonical_label", "")))
    if canonical_label and (
        collapse_ws(str(item.metadata.get("origin", ""))) in {"review_split", "review_merge"}
        or canonical_label.casefold() != collapse_ws(unit.canonical_title).casefold()
    ):
        return _reader_facing_claim_statement(canonical_label)
    return _reader_facing_claim_statement(unit.statement or unit.canonical_title or unit.unit_id)


def _review_item_title(item: ReviewItem, unit: LearningUnit) -> str:
    return (
        collapse_ws(str(item.metadata.get("canonical_label", "")))
        or collapse_ws(unit.canonical_title)
        or collapse_ws(item.review_item_id)
        or collapse_ws(unit.unit_id)
        or "Review Item"
    )


def _markdown_pipe_table(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> str:
    if not headers:
        return ""
    normalized_headers = tuple(collapse_ws(header) or f"Column {index}" for index, header in enumerate(headers, start=1))
    line_rows = [
        " | ".join(normalized_headers),
        " | ".join("---" for _ in normalized_headers),
    ]
    for row in rows:
        normalized_row = tuple(collapse_ws(cell) for cell in row)
        if not any(normalized_row):
            continue
        padded = normalized_row + tuple("" for _ in range(max(0, len(normalized_headers) - len(normalized_row))))
        line_rows.append(" | ".join((padded[index] if index < len(padded) else "") for index in range(len(normalized_headers))))
    return "\n".join(line_rows)


def _table_rows_for_review_item(item: ReviewItem, unit: LearningUnit) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    fields = unit.structured_fields if isinstance(unit.structured_fields, dict) else {}
    header_values = fields.get("table_headers") or fields.get("headers") or ()
    row_values = fields.get("table_rows") or fields.get("rows") or ()
    headers: tuple[str, ...] = ()
    rows: list[tuple[str, ...]] = []
    if isinstance(header_values, (list, tuple)):
        headers = tuple(collapse_ws(str(value)) for value in header_values if collapse_ws(str(value)))
    if isinstance(row_values, (list, tuple)):
        for row in row_values:
            if isinstance(row, (list, tuple)):
                rows.append(tuple(collapse_ws(str(cell)) for cell in row))
    if headers and rows:
        return headers, tuple(rows)
    split_labels = review_item_split_labels(item)
    if collapse_ws(item.render_kind) == "decision_table":
        headers = ("Condition", "Outcome")
        if split_labels:
            rows = tuple((label, "Included in the current reviewed decision path") for label in split_labels)
        else:
            rows = (
                (_review_item_title(item, unit), _claim_statement_for_review_item(item, unit)),
            )
        return headers, tuple(rows)
    headers = ("Field", "Value")
    aliases = tuple(collapse_ws(alias) for alias in unit.aliases if collapse_ws(alias))
    rows = [
        ("Item", _review_item_title(item, unit)),
        ("Statement", _claim_statement_for_review_item(item, unit)),
    ]
    if aliases:
        rows.append(("Aliases", ", ".join(aliases[:4])))
    if split_labels:
        rows.append(("Related Items", ", ".join(split_labels[:4])))
    rows.extend(
        (collapse_ws(str(key)).replace("_", " ").title(), collapse_ws(str(value)))
        for key, value in sorted(fields.items())
        if collapse_ws(str(key))
        and collapse_ws(str(value))
        and not isinstance(value, (dict, list, tuple))
    )
    return headers, tuple(rows)


def _diagram_lines_for_review_item(item: ReviewItem, unit: LearningUnit) -> tuple[str, ...]:
    fields = unit.structured_fields if isinstance(unit.structured_fields, dict) else {}
    flow_steps = fields.get("flow_steps") or fields.get("diagram_steps") or ()
    if isinstance(flow_steps, (list, tuple)):
        steps = tuple(collapse_ws(str(step)) for step in flow_steps if collapse_ws(str(step)))
        if steps:
            return tuple(
                f"{index}. {step}" if index == 1 else f"{index}. then {step}"
                for index, step in enumerate(steps, start=1)
            )
    split_labels = review_item_split_labels(item)
    if split_labels:
        return tuple(
            f"{split_labels[index - 1]} -> {split_labels[index]}"
            for index in range(1, len(split_labels))
        ) or split_labels
    return (_claim_statement_for_review_item(item, unit),)


def _review_item_block_body(item: ReviewItem, unit: LearningUnit) -> str:
    render_kind = collapse_ws(item.render_kind)
    statement = _claim_statement_for_review_item(item, unit)
    if render_kind in {"typst_table", "decision_table"}:
        headers, rows = _table_rows_for_review_item(item, unit)
        return _markdown_pipe_table(headers, rows)
    if render_kind in {"flow_diagram", "dependency_diagram"}:
        title = "Dependencies" if render_kind == "dependency_diagram" else "Flow"
        return "\n".join([f"{title}:", *[f"- {line}" for line in _diagram_lines_for_review_item(item, unit)]])
    if render_kind == "metric_card":
        fields = unit.structured_fields if isinstance(unit.structured_fields, dict) else {}
        metric_value = (
            collapse_ws(str(fields.get("metric_value", "")))
            or collapse_ws(str(fields.get("value", "")))
            or statement
        )
        return "\n".join(
            [
                f"Metric: {_review_item_title(item, unit)}",
                f"Value: {metric_value}",
            ]
        )
    if render_kind == "figure_with_caption":
        artifact_refs = tuple(collapse_ws(str(ref)) for ref in unit.linked_artifact_ids if collapse_ws(str(ref)))
        lines = [statement or f"Figure: {_review_item_title(item, unit)}"]
        if artifact_refs:
            lines.append("Artifacts: " + ", ".join(artifact_refs[:3]))
        return "\n".join(lines)
    if render_kind == "equation_block":
        return statement
    evidence_mode = collapse_ws(item.evidence_mode)
    body_lines = [statement]
    if evidence_mode and evidence_mode != "inline_handles":
        body_lines.append(f"Evidence mode: {evidence_mode.replace('_', ' ')}.")
    return "\n".join(line for line in body_lines if collapse_ws(line))


def _review_item_block(
    publication_id: str,
    *,
    publication_type: str,
    item: ReviewItem,
    unit: LearningUnit,
) -> PublicationBlock | None:
    render_kind = collapse_ws(item.render_kind)
    if render_kind in {"", "paragraph"} and not _is_exact_draft_publication_type(publication_type):
        return None
    block_kind_render = render_kind or "paragraph"
    title = _review_item_title(item, unit)
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind=f"review_{block_kind_render}",
            title=title,
            anchor_id=item.review_item_id,
        ),
        publication_id=publication_id,
        block_kind=f"review_{block_kind_render}",
        title=title,
        body=_review_item_block_body(item, unit),
        included_block_refs=(),
        status="active",
    )


def _selected_units(context: LearningContext, included_unit_ids: tuple[str, ...], excluded_unit_ids: tuple[str, ...]) -> tuple[LearningUnit, ...]:
    included = tuple(collapse_ws(unit_id) for unit_id in included_unit_ids if collapse_ws(unit_id))
    excluded = set(excluded_unit_ids)
    if included:
        admitted_by_id = {
            unit.unit_id: unit
            for unit in context.units
            if unit.status == "admitted" and unit.unit_id not in excluded
        }
        return tuple(admitted_by_id[unit_id] for unit_id in included if unit_id in admitted_by_id)
    units = [
        unit
        for unit in context.units
        if unit.status == "admitted"
        and unit.unit_id not in excluded
    ]
    return tuple(sorted(units, key=lambda item: (_section_key_for_unit(item), item.canonical_title, item.unit_id)))


def _section_xrefs(
    publication_id: str,
    section_claim_ids: dict[str, list[str]],
) -> tuple[PublicationCrossReference, ...]:
    xrefs: list[PublicationCrossReference] = []
    for from_section_id, xref_type, to_section_id in _SECTION_XREF_RULES:
        if not section_claim_ids.get(from_section_id) or not section_claim_ids.get(to_section_id):
            continue
        xrefs.append(
            PublicationCrossReference(
                xref_id=stable_publication_xref_id(
                    publication_id=publication_id,
                    from_kind="section",
                    from_id=from_section_id,
                    xref_type=xref_type,
                    to_kind="section",
                    to_id=to_section_id,
                ),
                publication_id=publication_id,
                from_id=from_section_id,
                to_id=to_section_id,
                xref_type=xref_type,
                from_kind="section",
                to_kind="section",
                status="active",
                metadata={"rule_origin": "report_section_graph"},
            )
        )
    return tuple(xrefs)


def _claim_projection_xrefs(
    publication_id: str,
    claims: tuple[PublicationClaim, ...],
) -> tuple[PublicationCrossReference, ...]:
    xrefs: list[PublicationCrossReference] = []
    for claim in claims:
        for unit_id in claim.related_unit_ids:
            normalized_unit_id = collapse_ws(unit_id)
            if not normalized_unit_id:
                continue
            xrefs.append(
                PublicationCrossReference(
                    xref_id=stable_publication_xref_id(
                        publication_id=publication_id,
                        from_kind="claim",
                        from_id=claim.claim_id,
                        xref_type="derived_from",
                        to_kind="unit",
                        to_id=normalized_unit_id,
                    ),
                    publication_id=publication_id,
                    from_id=claim.claim_id,
                    to_id=normalized_unit_id,
                    xref_type="derived_from",
                    from_kind="claim",
                    to_kind="unit",
                    status="active",
                    metadata={"projection_kind": "learning_unit"},
                )
            )
        for source_id in claim.source_ids:
            normalized_source_id = collapse_ws(source_id)
            if not normalized_source_id:
                continue
            xrefs.append(
                PublicationCrossReference(
                    xref_id=stable_publication_xref_id(
                        publication_id=publication_id,
                        from_kind="claim",
                        from_id=claim.claim_id,
                        xref_type="derived_from",
                        to_kind="source",
                        to_id=normalized_source_id,
                    ),
                    publication_id=publication_id,
                    from_id=claim.claim_id,
                    to_id=normalized_source_id,
                    xref_type="derived_from",
                    from_kind="claim",
                    to_kind="source",
                    status="active",
                    metadata={"projection_kind": "source_provenance"},
                )
            )
        for entity_id in claim.entity_ids:
            normalized_entity_id = collapse_ws(entity_id)
            if not normalized_entity_id:
                continue
            xref_type = "defines" if collapse_ws(claim.claim_kind) == "descriptive" else "see_also"
            xrefs.append(
                PublicationCrossReference(
                    xref_id=stable_publication_xref_id(
                        publication_id=publication_id,
                        from_kind="claim",
                        from_id=claim.claim_id,
                        xref_type=xref_type,
                        to_kind="entity",
                        to_id=normalized_entity_id,
                    ),
                    publication_id=publication_id,
                    from_id=claim.claim_id,
                    to_id=normalized_entity_id,
                    xref_type=xref_type,
                    from_kind="claim",
                    to_kind="entity",
                    status="active",
                    metadata={"projection_kind": "entity_anchor"},
                )
            )
    return tuple(xrefs)


def _publication_blocks(
    publication_id: str,
    context: LearningContext,
    *,
    publication_type: str,
    scope_summary: str,
    section_claim_ids: dict[str, list[str]],
) -> tuple[PublicationBlock, ...]:
    scope_block = PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="report_scope",
            title="Report Scope",
            anchor_id="publication",
        ),
        publication_id=publication_id,
        block_kind="report_scope",
        title="Report Scope",
        body=scope_summary or f"Governed {publication_type} projection for {context.canonical_title}.",
        included_block_refs=(),
        status="active",
    )
    basis_block = PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="governed_basis",
            title="Governed Publication Basis",
            anchor_id="publication",
        ),
        publication_id=publication_id,
        block_kind="governed_basis",
        title="Governed Publication Basis",
        body=f"This publication is a governed {publication_type} projection derived from the current LearningContext snapshot for {context.canonical_title}.",
        included_block_refs=(),
        status="active",
    )
    blocks: list[PublicationBlock] = [scope_block, basis_block]
    for section_id, role, section_title in _REPORT_SECTIONS:
        if section_id != "report-summary" and not section_claim_ids.get(section_id):
            continue
        included_block_refs: tuple[str, ...]
        if section_id == "report-summary":
            included_block_refs = (basis_block.block_id, scope_block.block_id)
        elif role == "evidence":
            included_block_refs = (basis_block.block_id,)
        else:
            included_block_refs = ()
        blocks.append(
            PublicationBlock(
                block_id=stable_publication_block_id(
                    publication_id=publication_id,
                    block_kind="section_lead",
                    title=f"{section_title} Lead",
                    anchor_id=section_id,
                ),
                publication_id=publication_id,
                block_kind="section_lead",
                title=f"{section_title} Lead",
                body=_SECTION_ROLE_BLOCK_BODIES.get(role, f"This section carries the {role} role for the publication."),
                included_block_refs=included_block_refs,
                status="active",
            )
    )
    return tuple(blocks)


def _dedupe_section_blocks(
    entries: list[tuple[str, PublicationBlock]],
) -> list[tuple[str, PublicationBlock]]:
    seen_keys: set[tuple[str, str, str, str]] = set()
    deduped: list[tuple[str, PublicationBlock]] = []
    for section_key, block in entries:
        signature = (
            collapse_ws(section_key),
            collapse_ws(block.block_kind),
            collapse_ws(block.title),
            collapse_ws(block.body),
        )
        if signature in seen_keys:
            continue
        seen_keys.add(signature)
        deduped.append((section_key, block))
    return deduped


def _decision_summary_block(
    publication_id: str,
    *,
    frame: DecisionFrame,
    policy_profile: DecisionPolicyProfile | None,
    receipt: DecisionAnalysisReceipt,
) -> PublicationBlock:
    def _with_terminal_period(text: str) -> str:
        normalized = collapse_ws(text)
        if not normalized:
            return "<none>."
        if normalized.endswith((".", "!", "?")):
            return normalized
        return f"{normalized}."

    recommended_option_ids = tuple(str(item) for item in receipt.metadata.get("recommended_option_ids", ()))
    option_outcomes = tuple(
        item for item in receipt.metadata.get("option_outcomes", ())
        if isinstance(item, dict)
    )
    body_lines = [
        f"Decision question: {_with_terminal_period(str(frame.question or '<none>'))}",
        f"Recommendation status: {_with_terminal_period(str(receipt.recommendation_status or 'pending'))}",
        f"Policy profile: {_with_terminal_period(str(getattr(policy_profile, 'profile_kind', 'conservative') or 'conservative'))}",
    ]
    if recommended_option_ids:
        body_lines.append("Recommended options: " + _with_terminal_period(", ".join(recommended_option_ids)))
        top_recommended = next(
            (
                outcome
                for outcome in option_outcomes
                if collapse_ws(str(outcome.get("option_id", ""))) in recommended_option_ids
            ),
            None,
        )
        if top_recommended is not None:
            basis_reading = _decision_basis_reading(top_recommended)
            if basis_reading:
                body_lines.append("Recommendation reading: " + basis_reading)
        blocked_options = tuple(
            collapse_ws(str(item.get("option_id", "")))
            for item in option_outcomes
            if collapse_ws(str(item.get("status", ""))).casefold() == "blocked"
        )
        if blocked_options:
            body_lines.append("Blocked options: " + _with_terminal_period(", ".join(item for item in blocked_options[:3] if item)))
    elif receipt.blocking_conditions:
        body_lines.append(
            "Blocking conditions: "
            + _with_terminal_period("; ".join(collapse_ws(item) for item in receipt.blocking_conditions[:3]))
        )
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_summary",
            title="Decision Recommendation",
            anchor_id="report-summary",
        ),
        publication_id=publication_id,
        block_kind="decision_summary",
        title="Decision Recommendation",
        body="\n".join(body_lines),
        included_block_refs=(),
        status="active",
    )


def _decision_case_frame_block(
    publication_id: str,
    *,
    frame: DecisionFrame,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    actors = _decision_role_labels(decision_items, "actor")
    objectives = _decision_role_labels(decision_items, "objective")
    current_states = _decision_role_labels(decision_items, "current_state")
    target_states = _decision_role_labels(decision_items, "target_state")
    constraints = _decision_role_labels(decision_items, "constraint")
    boundaries = _decision_role_labels(decision_items, "boundary")
    lines = [
        f"Decision focus: {collapse_ws(frame.question) or '<none>'}",
        "",
        "Current state:",
        *(f"- {item}" for item in (current_states[:4] or ("<none>",))),
        "Target state:",
        *(f"- {item}" for item in (target_states[:4] or ("<none>",))),
        "Actors:",
        *(f"- {item}" for item in (actors[:8] or ("<none>",))),
        "Objectives:",
        *(f"- {item}" for item in (objectives[:8] or ("<none>",))),
    ]
    if constraints:
        lines.extend(
            [
                "Operating constraints:",
                *(f"- {item}" for item in constraints[:8]),
            ]
        )
    if boundaries:
        lines.extend(
            [
                "Coordination boundaries:",
                *(f"- {item}" for item in boundaries[:8]),
            ]
        )
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_case_frame",
            title="Case Frame",
            anchor_id="report-definitions",
        ),
        publication_id=publication_id,
        block_kind="decision_case_frame",
        title="Case Frame",
        body="\n".join(lines),
        included_block_refs=(),
        status="active",
    )


def _decision_matrix_block(
    publication_id: str,
    *,
    receipt: DecisionAnalysisReceipt,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    option_context_by_option = _decision_option_context(decision_items)
    option_outcomes = receipt.metadata.get("option_outcomes", ())
    rows: list[str] = [
        "Option | Status | Score | Transitions | Actors | Basis",
        "--- | --- | --- | --- | --- | ---",
    ]
    if isinstance(option_outcomes, (list, tuple)):
        for outcome in option_outcomes:
            if not isinstance(outcome, dict):
                continue
            option_id = collapse_ws(str(outcome.get("option_id", ""))) or "<unknown>"
            option_context = option_context_by_option.get(option_id, {})
            status = collapse_ws(str(outcome.get("status", ""))) or "pending"
            score = str(int(outcome.get("score", 0) or 0))
            reasons = outcome.get("reasons", ())
            if isinstance(reasons, (list, tuple)):
                basis = _decision_basis_reading(outcome)
            else:
                basis = _publication_arrow_text(str(reasons))
            transitions = "; ".join(_publication_arrow_text(item) for item in option_context.get("transitions", ())) or "<none>"
            actors = ", ".join(option_context.get("actors", ())) or "<none>"
            rows.append(f"{option_id} | {status} | {score} | {transitions} | {actors} | {basis or '<none>'}")
    if len(rows) == 2:
        rows.append("No options | blocked | 0 | <none> | <none> | No decision candidates were materialized")
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_matrix",
            title="Decision Option Matrix",
            anchor_id="report-analysis",
        ),
        publication_id=publication_id,
        block_kind="decision_matrix",
        title="Decision Option Matrix",
        body="\n".join(rows),
        included_block_refs=(),
        status="active",
    )


def _decision_role_labels(
    decision_items: tuple[DecisionReviewItem, ...],
    role: str,
) -> tuple[str, ...]:
    return tuple(
        collapse_ws(str(item.metadata.get("canonical_label", ""))) or item.notes or item.decision_review_item_id
        for item in decision_items
        if item.included and collapse_ws(item.status) != "rejected" and collapse_ws(item.decision_role) == role
    )


def _decision_item_by_id(
    decision_items: tuple[DecisionReviewItem, ...],
) -> dict[str, DecisionReviewItem]:
    return {
        collapse_ws(item.decision_review_item_id): item
        for item in decision_items
        if collapse_ws(item.decision_review_item_id)
    }


def _decision_metadata_item_ids(
    metadata: dict[str, object],
    *,
    plural_key: str,
    singular_key: str,
) -> tuple[str, ...]:
    values: list[str] = []
    raw = metadata.get(plural_key)
    if isinstance(raw, (list, tuple, set)):
        values.extend(collapse_ws(str(item)) for item in raw if collapse_ws(str(item)))
    elif collapse_ws(str(raw)):
        values.append(collapse_ws(str(raw)))
    singular = collapse_ws(str(metadata.get(singular_key, "")))
    if singular:
        values.append(singular)
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


def _decision_item_labels_for_ids(
    decision_items: tuple[DecisionReviewItem, ...],
    decision_review_item_ids: tuple[str, ...],
) -> tuple[str, ...]:
    item_by_id = _decision_item_by_id(decision_items)
    labels: list[str] = []
    seen: set[str] = set()
    for decision_review_item_id in decision_review_item_ids:
        item = item_by_id.get(collapse_ws(decision_review_item_id))
        if item is None:
            continue
        label = collapse_ws(str(item.metadata.get("canonical_label", ""))) or item.notes or item.decision_review_item_id
        if not label or label in seen:
            continue
        seen.add(label)
        labels.append(label)
    return tuple(labels)


def _decision_transition_signature(
    transition_item: DecisionReviewItem,
    *,
    decision_items: tuple[DecisionReviewItem, ...],
) -> str:
    transition_label = collapse_ws(str(transition_item.metadata.get("canonical_label", ""))) or transition_item.decision_review_item_id
    item_by_id = _decision_item_by_id(decision_items)
    source_item = item_by_id.get(collapse_ws(str(transition_item.metadata.get("source_state_decision_review_item_id", ""))))
    target_item = item_by_id.get(collapse_ws(str(transition_item.metadata.get("target_state_decision_review_item_id", ""))))
    source_label = (
        collapse_ws(str(source_item.metadata.get("canonical_label", ""))) or source_item.decision_review_item_id
        if source_item is not None
        else ""
    )
    target_label = (
        collapse_ws(str(target_item.metadata.get("canonical_label", ""))) or target_item.decision_review_item_id
        if target_item is not None
        else ""
    )
    if source_label and target_label:
        return f"{source_label} → {transition_label} → {target_label}"
    if source_label:
        return f"{source_label} → {transition_label}"
    if target_label:
        return f"{transition_label} → {target_label}"
    return transition_label


def _publication_arrow_text(text: str) -> str:
    return collapse_ws(str(text or "")).replace(" -> ", " → ")


def _decision_basis_reading(outcome: dict[str, object]) -> str:
    reasons = outcome.get("reasons", ())
    normalized_reasons = (
        tuple(collapse_ws(str(item)) for item in reasons if collapse_ws(str(item)))
        if isinstance(reasons, (list, tuple))
        else tuple(filter(None, (collapse_ws(str(reasons)),)))
    )
    if not normalized_reasons:
        return ""
    conclusion = normalized_reasons[0]
    context_items: list[str] = []
    evidence_items: list[str] = []
    risk_items: list[str] = []
    for reason in normalized_reasons[1:]:
        lowered = reason.casefold()
        if "risk penalty" in lowered or lowered.startswith("risk "):
            risk_items.append(reason)
        elif "reachable path" in lowered or "source support" in lowered:
            evidence_items.append(reason)
        elif "active boundaries" in lowered or "transition candidates" in lowered:
            context_items.append(reason)
        else:
            evidence_items.append(reason)
    clauses = [f"Conclusion: {conclusion}."]
    if context_items:
        clauses.append("Context: " + "; ".join(context_items) + ".")
    if risk_items:
        clauses.append("Risk: " + "; ".join(risk_items) + ".")
    if evidence_items:
        clauses.append("Evidence: " + "; ".join(evidence_items) + ".")
    return " ".join(clauses)


def _decision_basis_editorial_summary(outcome: dict[str, object]) -> str:
    reasons = outcome.get("reasons", ())
    normalized_reasons = (
        tuple(collapse_ws(str(item)) for item in reasons if collapse_ws(str(item)))
        if isinstance(reasons, (list, tuple))
        else tuple(filter(None, (collapse_ws(str(reasons)),)))
    )
    if not normalized_reasons:
        return ""
    conclusion = normalized_reasons[0].casefold()
    if conclusion == "executable":
        lead = "it is executable under current operating conditions"
    elif conclusion == "valid_but_not_executable":
        lead = "it is directionally valid but not yet executable"
    elif conclusion == "not currently valid":
        lead = "it is not currently valid under current operating conditions"
    else:
        lead = normalized_reasons[0]
    clauses = [lead]
    if any("reachable path" in reason.casefold() for reason in normalized_reasons[1:]):
        clauses.append("a reachable path is available")
    if any("source support" in reason.casefold() for reason in normalized_reasons[1:]):
        clauses.append("the source record supports this reading")
    return ", and ".join(clauses[:2]) if len(clauses) > 1 else clauses[0]


def _decision_option_context(
    decision_items: tuple[DecisionReviewItem, ...],
) -> dict[str, dict[str, tuple[str, ...]]]:
    item_by_id = _decision_item_by_id(decision_items)
    contexts: dict[str, dict[str, tuple[str, ...]]] = {}
    for item in decision_items:
        if not item.included or collapse_ws(item.status) == "rejected" or collapse_ws(item.decision_role) != "decision_candidate":
            continue
        option_id = collapse_ws(str(item.metadata.get("canonical_label", ""))) or item.decision_review_item_id
        metadata = dict(item.metadata)
        transition_ids = _decision_metadata_item_ids(
            metadata,
            plural_key="selected_transition_decision_review_item_ids",
            singular_key="selected_transition_decision_review_item_id",
        )
        actor_ids = _decision_metadata_item_ids(
            metadata,
            plural_key="assigned_actor_decision_review_item_ids",
            singular_key="assigned_actor_decision_review_item_id",
        )
        transition_items = [
            item_by_id[item_id]
            for item_id in transition_ids
            if item_id in item_by_id and collapse_ws(item_by_id[item_id].decision_role) == "transition_candidate"
        ]
        transition_signatures = tuple(
            _decision_transition_signature(transition_item, decision_items=decision_items)
            for transition_item in transition_items
        )
        actor_labels = _decision_item_labels_for_ids(decision_items, actor_ids)
        capability_labels = []
        dependency_labels = []
        boundary_labels = []
        seen_capability_labels: set[str] = set()
        seen_dependency_labels: set[str] = set()
        seen_boundary_labels: set[str] = set()
        for transition_item in transition_items:
            capability_ids = _decision_metadata_item_ids(
                dict(transition_item.metadata),
                plural_key="changed_capability_decision_review_item_ids",
                singular_key="changed_capability_decision_review_item_id",
            )
            capability_items = [
                item_by_id[item_id]
                for item_id in capability_ids
                if item_id in item_by_id and collapse_ws(item_by_id[item_id].decision_role) == "capability"
            ]
            for label in _decision_item_labels_for_ids(decision_items, capability_ids):
                if label in seen_capability_labels:
                    continue
                seen_capability_labels.add(label)
                capability_labels.append(label)
            for capability_item in capability_items:
                capability_metadata = dict(capability_item.metadata)
                dependency_ids = _decision_metadata_item_ids(
                    capability_metadata,
                    plural_key="required_dependency_decision_review_item_ids",
                    singular_key="required_dependency_decision_review_item_id",
                )
                boundary_ids = _decision_metadata_item_ids(
                    capability_metadata,
                    plural_key="crossed_boundary_decision_review_item_ids",
                    singular_key="crossed_boundary_decision_review_item_id",
                )
                for label in _decision_item_labels_for_ids(decision_items, dependency_ids):
                    if label in seen_dependency_labels:
                        continue
                    seen_dependency_labels.add(label)
                    dependency_labels.append(label)
                for label in _decision_item_labels_for_ids(decision_items, boundary_ids):
                    if label in seen_boundary_labels:
                        continue
                    seen_boundary_labels.add(label)
                    boundary_labels.append(label)
        contexts[option_id] = {
            "transitions": transition_signatures,
            "actors": actor_labels,
            "capabilities": tuple(capability_labels),
            "dependencies": tuple(dependency_labels),
            "boundaries": tuple(boundary_labels),
        }
    return contexts


def _decision_dependency_checklist_block(
    publication_id: str,
    *,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    grouped_lines: list[str] = []
    role_groups = (
        ("Dependencies", "dependency"),
        ("Constraints", "constraint"),
        ("Boundaries", "boundary"),
        ("Supporting Evidence", "supporting_evidence"),
    )
    for heading, role in role_groups:
        matching = [
            collapse_ws(str(item.metadata.get("canonical_label", ""))) or item.notes or item.decision_review_item_id
            for item in decision_items
            if item.included and collapse_ws(item.status) != "rejected" and collapse_ws(item.decision_role) == role
        ]
        if not matching:
            continue
        grouped_lines.append(f"{heading}:")
        grouped_lines.extend(f"- {label}" for label in matching[:8])
        grouped_lines.append("")
    body = "\n".join(grouped_lines[:-1] if grouped_lines and not grouped_lines[-1] else grouped_lines)
    if not collapse_ws(body):
        body = "Dependencies:\n- No explicit dependency or constraint items were promoted into the decision frame."
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_dependency_checklist",
            title="Decision Dependency Checklist",
            anchor_id="report-analysis",
        ),
        publication_id=publication_id,
        block_kind="decision_dependency_checklist",
        title="Decision Dependency Checklist",
        body=body,
        included_block_refs=(),
        status="active",
    )


def _decision_transition_roadmap_block(
    publication_id: str,
    *,
    frame: DecisionFrame,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    current_states = _decision_role_labels(decision_items, "current_state")
    target_states = _decision_role_labels(decision_items, "target_state")
    transition_candidates = _decision_role_labels(decision_items, "transition_candidate")
    assignment_candidates = tuple(
        item
        for item in _decision_role_labels(decision_items, "assignment_candidate")
        if collapse_ws(item) not in {"0", "<none>"}
    )
    actor_candidates = _decision_role_labels(decision_items, "actor")
    objective_candidates = _decision_role_labels(decision_items, "objective")
    lines = [
        f"Decision question: {collapse_ws(frame.question) or '<none>'}",
        "",
        "1. Current state",
        *(f"   - {item}" for item in (current_states or ("<none>",))),
        "2. Transition candidates",
        *(f"   - {item}" for item in (transition_candidates or ("<none>",))),
        "3. Target state",
        *(f"   - {item}" for item in (target_states or ("<none>",))),
    ]
    if assignment_candidates:
        lines.extend(
            [
                "4. Assignment candidates",
                *(f"   - {item}" for item in assignment_candidates),
            ]
        )
    if actor_candidates:
        lines.extend(
            [
                "Actors",
                *(f"- {item}" for item in actor_candidates),
            ]
        )
    if objective_candidates:
        lines.extend(
            [
                "Objectives",
                *(f"- {item}" for item in objective_candidates),
            ]
        )
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_transition_roadmap",
            title="Decision Transition Roadmap",
            anchor_id="report-analysis",
        ),
        publication_id=publication_id,
        block_kind="decision_transition_roadmap",
        title="Decision Transition Roadmap",
        body="\n".join(lines),
        included_block_refs=(),
        status="active",
    )


def _decision_ranking_summary_block(
    publication_id: str,
    *,
    policy_profile: DecisionPolicyProfile | None,
    receipt: DecisionAnalysisReceipt,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    def _outcome_basis(outcome: dict[str, object]) -> str:
        return _decision_basis_reading(outcome)

    def _outcome_editorial_summary(outcome: dict[str, object]) -> str:
        return _decision_basis_editorial_summary(outcome)

    def _policy_reading_for(
        option_id: str,
        *,
        status: str,
        basis: str,
    ) -> str:
        option_context = option_context_by_option.get(option_id, {})
        dependencies = tuple(option_context.get("dependencies", ()))
        boundaries = tuple(option_context.get("boundaries", ()))
        basis_sentences = tuple(
            collapse_ws(segment)
            for segment in re.split(r"(?<=[.!?])\s+", collapse_ws(basis))
            if collapse_ws(segment)
        )
        clauses: list[str] = []
        if status == "valid_but_not_executable":
            clauses.append("Keep in reserve until execution conditions are materially stronger.")
        elif status == "blocked":
            clauses.append("Do not advance under current conditions.")
        if basis_sentences:
            lead_reason = re.sub(r"^Conclusion:\s*", "", basis_sentences[0], flags=re.IGNORECASE).rstrip(".")
            clauses.append("Reason: " + lead_reason + ".")
        actions: list[str] = []
        if dependencies:
            actions.append("close dependencies " + ", ".join(dependencies[:4]))
        if boundaries:
            actions.append("govern boundaries " + ", ".join(boundaries[:3]))
        if actions:
            clauses.append("To reconsider: " + "; ".join(actions) + ".")
        return " ".join(clauses) if len(clauses) > 1 else f"{option_id}: no governed reading was recorded."

    option_context_by_option = _decision_option_context(decision_items)
    option_outcomes = tuple(
        item for item in receipt.metadata.get("option_outcomes", ())
        if isinstance(item, dict)
    )
    policy_rule_ids = tuple(str(item) for item in receipt.metadata.get("policy_rule_ids", ()))
    profile_kind = collapse_ws(getattr(policy_profile, "profile_kind", "conservative")) or "conservative"
    lines = [
        f"Policy profile: {profile_kind}",
        f"Recommendation status: {collapse_ws(receipt.recommendation_status) or 'pending'}",
        f"Candidate path count: {int(receipt.metadata.get('candidate_path_count', 0) or 0)}",
    ]
    top_outcome = option_outcomes[0] if option_outcomes else {}
    top_option_id = collapse_ws(str(top_outcome.get("option_id", ""))) or ""
    top_basis = _outcome_basis(top_outcome) if isinstance(top_outcome, dict) else ""
    top_editorial = _outcome_editorial_summary(top_outcome) if isinstance(top_outcome, dict) else ""
    reserve_option_ids = tuple(
        collapse_ws(str(item.get("option_id", "")))
        for item in option_outcomes
        if isinstance(item, dict) and collapse_ws(str(item.get("status", ""))).casefold() == "valid_but_not_executable"
    )
    blocked_option_ids = tuple(
        collapse_ws(str(item.get("option_id", "")))
        for item in option_outcomes
        if isinstance(item, dict) and collapse_ws(str(item.get("status", ""))).casefold() == "blocked"
    )
    policy_sentence = (
        f"Under the {profile_kind} policy profile, executable options outrank merely valid ones and unresolved critical dependencies remain disqualifying."
    )
    if top_option_id:
        current_reading = f"Why the recommendation leads: {top_option_id} leads the ranking"
        if top_editorial:
            current_reading += f" because {top_editorial}"
        elif top_basis:
            current_reading += f" because {top_basis}"
        current_reading += "."
        lines.append(f"Policy guidance: {policy_sentence}")
        lines.append(current_reading)
    if reserve_option_ids:
        lines.append(
            "Reserve options: "
            + ", ".join(item for item in reserve_option_ids[:3] if item)
            + "."
        )
    if blocked_option_ids:
        lines.append(
            "Blocked options: "
            + ", ".join(item for item in blocked_option_ids[:3] if item)
            + "."
        )
    reserve_outcomes = tuple(
        item
        for item in option_outcomes
        if collapse_ws(str(item.get("status", ""))).casefold() == "valid_but_not_executable"
    )
    blocked_outcomes = tuple(
        item
        for item in option_outcomes
        if collapse_ws(str(item.get("status", ""))).casefold() == "blocked"
    )
    if reserve_outcomes:
        lines.append("Reserve option readings:")
        for outcome in reserve_outcomes[:4]:
            option_id = collapse_ws(str(outcome.get("option_id", ""))) or "<unknown>"
            lines.append(
                "- "
                + option_id
                + ": "
                + _policy_reading_for(
                    option_id,
                    status="valid_but_not_executable",
                    basis=_outcome_basis(outcome),
                )
            )
    if blocked_outcomes:
        lines.append("Blocked option readings:")
        for outcome in blocked_outcomes[:4]:
            option_id = collapse_ws(str(outcome.get("option_id", ""))) or "<unknown>"
            lines.append(
                "- "
                + option_id
                + ": "
                + _policy_reading_for(
                    option_id,
                    status="blocked",
                    basis=_outcome_basis(outcome),
                )
            )
    if policy_rule_ids:
        lines.extend(
            [
                "Ranking rules:",
                *(f"- {collapse_ws(item)}" for item in policy_rule_ids[:8] if collapse_ws(item)),
            ]
        )
    if option_outcomes:
        lines.append("Ranked options:")
        for index, outcome in enumerate(option_outcomes[:6], start=1):
            option_id = collapse_ws(str(outcome.get("option_id", ""))) or "<unknown>"
            status = collapse_ws(str(outcome.get("status", ""))) or "pending"
            score = int(outcome.get("score", 0) or 0)
            option_context = option_context_by_option.get(option_id, {})
            basis = _outcome_basis(outcome)
            lines.append(f"- {index}. {option_id} | {status} | score {score}")
            actors = option_context.get("actors", ())
            capabilities = option_context.get("capabilities", ())
            if actors:
                lines.append(f"  actors: {', '.join(actors[:6])}")
            if capabilities:
                lines.append(f"  capabilities: {', '.join(capabilities[:6])}")
            if basis:
                lines.append(f"  basis: {basis}")
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_ranking_summary",
            title="Decision Ranking Summary",
            anchor_id="report-analysis",
        ),
        publication_id=publication_id,
        block_kind="decision_ranking_summary",
        title="Decision Ranking Summary",
        body="\n".join(lines),
        included_block_refs=(),
        status="active",
    )


def _decision_execution_guidance_block(
    publication_id: str,
    *,
    receipt: DecisionAnalysisReceipt,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    option_context_by_option = _decision_option_context(decision_items)
    recommended_option_ids = tuple(str(item) for item in receipt.metadata.get("recommended_option_ids", ()))
    option_outcomes = receipt.metadata.get("option_outcomes", ())
    recommended_basis = ""
    reserve_options: list[str] = []
    if isinstance(option_outcomes, (list, tuple)):
        for outcome in option_outcomes:
            if not isinstance(outcome, dict):
                continue
            option_id = collapse_ws(str(outcome.get("option_id", "")))
            status = collapse_ws(str(outcome.get("status", ""))).casefold()
            reasons = outcome.get("reasons", ())
            basis = _decision_basis_reading(outcome)
            if option_id in recommended_option_ids and not recommended_basis:
                recommended_basis = _decision_basis_editorial_summary(outcome) or basis
            if status == "valid_but_not_executable" and option_id not in {"0", "<none>", ""}:
                reserve_options.append(option_id)
    dependency_labels = _decision_role_labels(decision_items, "dependency")
    constraint_labels = _decision_role_labels(decision_items, "constraint")
    boundary_labels = _decision_role_labels(decision_items, "boundary")
    recommended_transitions: list[str] = []
    recommended_actors: list[str] = []
    recommended_capabilities: list[str] = []
    recommended_dependencies: list[str] = []
    recommended_boundaries: list[str] = []
    seen_transitions: set[str] = set()
    seen_actors: set[str] = set()
    seen_capabilities: set[str] = set()
    seen_dependencies: set[str] = set()
    seen_boundaries: set[str] = set()
    for option_id in recommended_option_ids:
        option_context = option_context_by_option.get(option_id, {})
        for label in option_context.get("transitions", ()):
            if label not in seen_transitions:
                seen_transitions.add(label)
                recommended_transitions.append(label)
        for label in option_context.get("actors", ()):
            if label not in seen_actors:
                seen_actors.add(label)
                recommended_actors.append(label)
        for label in option_context.get("capabilities", ()):
            if label not in seen_capabilities:
                seen_capabilities.add(label)
                recommended_capabilities.append(label)
        for label in option_context.get("dependencies", ()):
            if label not in seen_dependencies:
                seen_dependencies.add(label)
                recommended_dependencies.append(label)
        for label in option_context.get("boundaries", ()):
            if label not in seen_boundaries:
                seen_boundaries.add(label)
                recommended_boundaries.append(label)
    implementation_prerequisites = tuple(
        item for item in recommended_dependencies[:8]
    ) or dependency_labels[:8]
    coordination_boundaries = tuple(
        item for item in recommended_boundaries[:6]
    ) or boundary_labels[:6]
    lines = [
        "Recommended operating posture:",
        f"- {', '.join(recommended_option_ids) if recommended_option_ids else '<none>'}",
    ]
    if recommended_basis:
        lines.extend(
            [
                "Why this is the current recommendation:",
                f"- {recommended_basis}",
            ]
        )
    if recommended_actors:
        lines.extend(
            [
                "Primary responsible actors:",
                *(f"- {item}" for item in recommended_actors[:6]),
            ]
        )
    if recommended_capabilities:
        lines.extend(
            [
                "Capabilities activated in the recommendation:",
                *(f"- {item}" for item in recommended_capabilities[:8]),
            ]
        )
    if implementation_prerequisites:
        lines.extend(
            [
                "Implementation prerequisites:",
                *(f"- {item}" for item in implementation_prerequisites),
            ]
        )
    if coordination_boundaries:
        lines.extend(
            [
                "Coordination boundaries to govern:",
                *(f"- {item}" for item in coordination_boundaries),
            ]
        )
    if reserve_options:
        lines.extend(
            [
                "Alternatives to keep in reserve:",
            ]
        )
        for option_id in reserve_options[:3]:
            option_context = option_context_by_option.get(option_id, {})
            reserve_actors = option_context.get("actors", ())
            reserve_dependencies = option_context.get("dependencies", ())
            reserve_boundaries = option_context.get("boundaries", ())
            reserve_clauses: list[str] = []
            if reserve_actors:
                reserve_clauses.append("responsible actors: " + ", ".join(reserve_actors[:6]))
            if reserve_dependencies:
                reserve_clauses.append("dependencies to resolve: " + ", ".join(reserve_dependencies[:6]))
            if reserve_boundaries:
                reserve_clauses.append("boundaries to govern: " + ", ".join(reserve_boundaries[:6]))
            if reserve_clauses:
                lines.append(f"- {option_id}: " + "; ".join(reserve_clauses))
            else:
                lines.append(f"- {option_id}")
    if constraint_labels:
        lines.extend(
            [
                "Conditions that remain binding:",
                *(f"- {item}" for item in constraint_labels[:6]),
            ]
        )
    if receipt.blocking_conditions:
        blocking_conditions = tuple(
            collapse_ws(item)
            for item in receipt.blocking_conditions[:6]
            if collapse_ws(item) not in {"0", "<none>"}
        )
    else:
        blocking_conditions = ()
    if blocking_conditions:
        lines.extend(
            [
                "Do not proceed if these blockers remain open:",
                *(f"- {item}" for item in blocking_conditions),
            ]
        )
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_execution_guidance",
            title="Execution Guidance",
            anchor_id="report-implementation",
        ),
        publication_id=publication_id,
        block_kind="decision_execution_guidance",
        title="Execution Guidance",
        body="\n".join(lines),
        included_block_refs=(),
        status="active",
    )


def _decision_simple_diagram_block(
    publication_id: str,
    *,
    receipt: DecisionAnalysisReceipt,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    def _path_end_state(path_text: str) -> str:
        normalized_path = _publication_arrow_text(path_text)
        segments = [collapse_ws(part) for part in normalized_path.split("→") if collapse_ws(part)]
        return segments[-1] if segments else ""

    current_states = _decision_role_labels(decision_items, "current_state")
    target_states = _decision_role_labels(decision_items, "target_state")
    transition_candidates = _decision_role_labels(decision_items, "transition_candidate")
    option_context_by_option = _decision_option_context(decision_items)
    option_outcomes = tuple(
        item for item in receipt.metadata.get("option_outcomes", ())
        if isinstance(item, dict)
    )
    recommended_option_ids = tuple(
        collapse_ws(str(item))
        for item in receipt.metadata.get("recommended_option_ids", ())
        if collapse_ws(str(item))
    )
    reserve_option_ids = tuple(
        collapse_ws(str(item.get("option_id", "")))
        for item in option_outcomes
        if isinstance(item, dict) and collapse_ws(str(item.get("status", ""))).casefold() == "valid_but_not_executable"
    )
    blocked_option_ids = tuple(
        collapse_ws(str(item.get("option_id", "")))
        for item in option_outcomes
        if isinstance(item, dict) and collapse_ws(str(item.get("status", ""))).casefold() == "blocked"
    )
    current_text = ", ".join(current_states[:3]) or "<current>"
    target_text = ", ".join(target_states[:3]) or "<target>"
    recommended_paths: list[str] = []
    recommended_capabilities: list[str] = []
    recommended_dependencies: list[str] = []
    recommended_boundaries: list[str] = []
    seen_capabilities: set[str] = set()
    seen_dependencies: set[str] = set()
    seen_boundaries: set[str] = set()
    for option_id in recommended_option_ids:
        option_context = option_context_by_option.get(option_id, {})
        path_text = "; ".join(option_context.get("transitions", ())[:3])
        if path_text:
            recommended_paths.append(path_text)
        for label in option_context.get("capabilities", ()):
            if label not in seen_capabilities:
                seen_capabilities.add(label)
                recommended_capabilities.append(label)
        for label in option_context.get("dependencies", ()):
            if label not in seen_dependencies:
                seen_dependencies.add(label)
                recommended_dependencies.append(label)
        for label in option_context.get("boundaries", ()):
            if label not in seen_boundaries:
                seen_boundaries.add(label)
                recommended_boundaries.append(label)
    recommended_path_text = " | ".join(recommended_paths[:2]) or ", ".join(transition_candidates[:3]) or "<transition>"
    recommended_target_states: list[str] = []
    seen_recommended_targets: set[str] = set()
    for path_text in recommended_paths:
        end_state = _path_end_state(path_text)
        if end_state and end_state not in seen_recommended_targets:
            seen_recommended_targets.add(end_state)
            recommended_target_states.append(end_state)
    if recommended_target_states:
        target_text = ", ".join(recommended_target_states[:3])

    def _option_card_lines(option_id: str) -> list[str]:
        option_context = option_context_by_option.get(option_id, {})
        lines = [f"- {option_id}"]
        path_text = "; ".join(_publication_arrow_text(item) for item in option_context.get("transitions", ())[:3])
        actor_text = ", ".join(option_context.get("actors", ())[:6])
        capability_text = ", ".join(option_context.get("capabilities", ())[:6])
        dependency_text = ", ".join(option_context.get("dependencies", ())[:6])
        boundary_text = ", ".join(option_context.get("boundaries", ())[:6])
        if path_text:
            lines.append(f"Path: {path_text}")
        if actor_text:
            lines.append(f"Actors: {actor_text}")
        if capability_text:
            lines.append(f"Capabilities: {capability_text}")
        if dependency_text:
            lines.append(f"Dependencies: {dependency_text}")
        if boundary_text:
            lines.append(f"Boundaries: {boundary_text}")
        return lines

    def _alternative_path_lines(option_ids: tuple[str, ...]) -> list[str]:
        lines: list[str] = []
        for option_id in option_ids[:4]:
            lines.extend(_option_card_lines(option_id))
        return lines

    lines = [
        f"Current states: {current_text}",
        f"Recommended option: {', '.join(recommended_option_ids[:3]) or '<none>'}",
        f"Recommended path: {_publication_arrow_text(recommended_path_text)}",
        f"Target states: {target_text}",
    ]
    recommended_actor_labels = []
    seen_recommended_actors: set[str] = set()
    for option_id in recommended_option_ids:
        for label in option_context_by_option.get(option_id, {}).get("actors", ()):
            if label in seen_recommended_actors:
                continue
            seen_recommended_actors.add(label)
            recommended_actor_labels.append(label)
    if recommended_actor_labels:
        lines.append("Recommended actors: " + ", ".join(recommended_actor_labels[:6]))
    elif _decision_role_labels(decision_items, "actor"):
        lines.append("Recommended actors: " + ", ".join(_decision_role_labels(decision_items, "actor")[:6]))
    reserve_lines = _alternative_path_lines(reserve_option_ids)
    blocked_lines = _alternative_path_lines(blocked_option_ids)
    if reserve_lines:
        lines.append("Reserve options:")
        lines.extend(reserve_lines)
    if blocked_lines:
        lines.append("Blocked options:")
        lines.extend(blocked_lines)
    if recommended_capabilities:
        lines.append("Recommended capabilities: " + ", ".join(recommended_capabilities[:6]))
    if recommended_dependencies:
        lines.append("Recommended dependencies: " + ", ".join(recommended_dependencies[:6]))
    elif _decision_role_labels(decision_items, "dependency"):
        lines.append("Recommended dependencies: " + ", ".join(_decision_role_labels(decision_items, "dependency")[:6]))
    if recommended_boundaries:
        lines.append("Recommended boundaries: " + ", ".join(recommended_boundaries[:6]))
    elif _decision_role_labels(decision_items, "boundary"):
        lines.append("Recommended boundaries: " + ", ".join(_decision_role_labels(decision_items, "boundary")[:6]))
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_simple_diagram",
            title="Decision Model Diagram",
            anchor_id="report-analysis",
        ),
        publication_id=publication_id,
        block_kind="decision_simple_diagram",
        title="Decision Model Diagram",
        body="\n".join(lines),
        included_block_refs=(),
        status="active",
    )


def _decision_risk_matrix_block(
    publication_id: str,
    *,
    receipt: DecisionAnalysisReceipt,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    rows: list[tuple[str, str, str, str]] = []
    for item in decision_items:
        if not item.included or collapse_ws(item.status) == "rejected":
            continue
        role = collapse_ws(item.decision_role)
        if role not in {"dependency", "constraint", "boundary", "risk_statement"}:
            continue
        label = collapse_ws(str(item.metadata.get("canonical_label", ""))) or item.decision_review_item_id
        effect = {
            "dependency": "May block execution until resolved",
            "constraint": "May constrain valid options",
            "boundary": "May increase coordination friction",
            "risk_statement": "Carries explicit residual risk",
        }.get(role, "Affects the decision path")
        basis = collapse_ws(item.notes) or collapse_ws(str(item.metadata.get("statement", "")))
        if not basis:
            basis = {
                "dependency": "The current recommendation depends on this condition being resolved before execution.",
                "constraint": "This condition narrows which options remain valid under the current policy.",
                "boundary": "This boundary introduces coordination and approval friction that must be governed.",
                "risk_statement": "This is an explicit residual risk recorded in the current decision model.",
            }.get(role, "This condition materially affects the decision path.")
        rows.append((label, role.replace("_", " ").title(), effect, basis))
    if not rows:
        risk_summary = receipt.risk_summary if isinstance(receipt.risk_summary, dict) else {}
        rows = [
            (
                "Residual model risk",
                "Summary",
                f"Capability risks: {int(risk_summary.get('capability_risk_count', 0) or 0)}; transition risks: {int(risk_summary.get('transition_risk_count', 0) or 0)}",
                "Derived from the current decision analysis receipt",
            )
        ]
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_risk_matrix",
            title="Decision Risk Matrix",
            anchor_id="report-analysis",
        ),
        publication_id=publication_id,
        block_kind="decision_risk_matrix",
        title="Decision Risk Matrix",
        body=_markdown_pipe_table(
            ("Factor", "Category", "Effect", "Basis"),
            tuple(rows),
        ),
        included_block_refs=(),
        status="active",
    )


def _decision_recommendation_receipt_block(
    publication_id: str,
    *,
    frame: DecisionFrame,
    policy_profile: DecisionPolicyProfile | None,
    receipt: DecisionAnalysisReceipt,
    decision_items: tuple[DecisionReviewItem, ...],
) -> PublicationBlock:
    option_context_by_option = _decision_option_context(decision_items)
    recommended_option_ids = tuple(str(item) for item in receipt.metadata.get("recommended_option_ids", ()))
    policy_rule_ids = tuple(str(item) for item in receipt.metadata.get("policy_rule_ids", ()))
    option_outcomes = tuple(
        item for item in receipt.metadata.get("option_outcomes", ())
        if isinstance(item, dict)
    )
    body_lines = [
        f"Question: {collapse_ws(frame.question) or '<none>'}",
        f"Recommendation status: {collapse_ws(receipt.recommendation_status) or 'pending'}",
        f"Policy profile: {collapse_ws(getattr(policy_profile, 'profile_kind', 'conservative')) or 'conservative'}",
        f"Admissible transitions: {len(receipt.admissible_transition_ids)}",
        f"Valid options: {len(receipt.valid_decision_ids)}",
        f"Executable options: {len(receipt.executable_decision_ids)}",
        f"Candidate paths: {int(receipt.metadata.get('candidate_path_count', 0) or 0)}",
    ]
    if recommended_option_ids:
        body_lines.append("Recommended options: " + ", ".join(recommended_option_ids))
    if receipt.blocking_conditions:
        body_lines.append("Blocking conditions: " + "; ".join(collapse_ws(item) for item in receipt.blocking_conditions[:5]))
    if policy_rule_ids:
        body_lines.append("Policy rules: " + ", ".join(policy_rule_ids[:6]))
    if option_outcomes:
        top_outcome = option_outcomes[0]
        top_option_id = collapse_ws(str(top_outcome.get("option_id", ""))) or "<unknown>"
        top_score = int(top_outcome.get("score", 0) or 0)
        top_basis = _decision_basis_reading(top_outcome)
        body_lines.append(f"Top ranked option: {top_option_id} (score {top_score})")
        if top_basis:
            body_lines.append("Top option basis: " + top_basis)
        top_context = option_context_by_option.get(top_option_id, {})
        top_transitions = top_context.get("transitions", ())
        top_actors = top_context.get("actors", ())
        top_capabilities = top_context.get("capabilities", ())
        top_dependencies = top_context.get("dependencies", ())
        top_boundaries = top_context.get("boundaries", ())
        if top_transitions:
            body_lines.append("Top option transitions: " + "; ".join(_publication_arrow_text(item) for item in top_transitions[:4]))
        if top_actors:
            body_lines.append("Top option actors: " + ", ".join(top_actors[:6]))
        if top_capabilities:
            body_lines.append("Top option capabilities: " + ", ".join(top_capabilities[:6]))
        if top_dependencies:
            body_lines.append("Top option dependencies: " + ", ".join(top_dependencies[:6]))
        if top_boundaries:
            body_lines.append("Boundary conditions to govern: " + "; ".join(top_boundaries[:5]))
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="decision_recommendation_receipt",
            title="Decision Recommendation Receipt",
            anchor_id="report-appendix",
        ),
        publication_id=publication_id,
        block_kind="decision_recommendation_receipt",
        title="Decision Recommendation Receipt",
        body="\n".join(body_lines),
        included_block_refs=(),
        status="active",
    )


def _review_transform_block(
    publication_id: str,
    *,
    receipts: tuple[ReviewTransformReceipt, ...],
) -> PublicationBlock:
    body_lines = [
        f"Draft transform receipt count: {len(receipts)}.",
        *[
            f"{receipt.transform_kind}: {collapse_ws(receipt.notes) or receipt.receipt_id}"
            for receipt in receipts[-5:]
        ],
    ]
    return PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="review_transform_receipts",
            title="Draft Transform Provenance",
            anchor_id="report-appendix",
        ),
        publication_id=publication_id,
        block_kind="review_transform_receipts",
        title="Draft Transform Provenance",
        body="\n".join(body_lines),
        included_block_refs=(),
        status="active",
    )


def _normalized_statement_key(statement: str) -> str:
    rendered = collapse_ws(statement).casefold()
    for needle in (",", ".", ";", ":", "?", "!", "(", ")", "[", "]", "{", "}"):
        rendered = rendered.replace(needle, " ")
    return collapse_ws(rendered)


def _reportable_unit(unit: LearningUnit) -> bool:
    return publication_statement_is_reportable(unit.statement, unit_kind=unit.unit_kind)


def _report_unit_priority(unit: LearningUnit) -> tuple[int, int, str, str]:
    kind_score = {
        "relation": 60,
        "definition": 55,
        "misconception": 50,
        "boundary": 48,
        "ability": 42,
        "example": 30,
        "counterexample": 26,
        "source_note": 10,
        "open_question": 0,
    }.get(unit.unit_kind, 20)
    statement = collapse_ws(unit.statement)
    length_score = min(len(statement) // 48, 4)
    return (
        kind_score,
        length_score,
        collapse_ws(unit.canonical_title).casefold(),
        unit.unit_id,
    )


def _default_report_unit_selection(
    context: LearningContext,
) -> tuple[tuple[LearningUnit, ...], tuple[LearningUnit, ...], dict[str, object]]:
    admitted_units = _selected_units(context, (), ())
    if not admitted_units:
        return (), (), {"unit_selection_mode": "empty"}
    selected: list[LearningUnit] = []
    excluded: list[LearningUnit] = []
    section_counts: dict[str, int] = {}
    seen_statement_keys: set[str] = set()
    ordered_candidates = sorted(
        admitted_units,
        key=lambda item: (
            -_report_unit_priority(item)[0],
            -_report_unit_priority(item)[1],
            _report_unit_priority(item)[2],
            _report_unit_priority(item)[3],
        ),
    )
    for unit in ordered_candidates:
        statement_key = _normalized_statement_key(unit.statement)
        section_key = _section_key_for_unit(unit)
        if not _reportable_unit(unit):
            excluded.append(unit)
            continue
        if statement_key and statement_key in seen_statement_keys:
            excluded.append(unit)
            continue
        section_limit = _DEFAULT_REPORT_SECTION_LIMITS.get(section_key, 2)
        if section_counts.get(section_key, 0) >= section_limit:
            excluded.append(unit)
            continue
        selected.append(unit)
        if statement_key:
            seen_statement_keys.add(statement_key)
        section_counts[section_key] = section_counts.get(section_key, 0) + 1
    if not selected and admitted_units:
        selected = [admitted_units[0]]
        excluded = [unit for unit in admitted_units[1:]]
    selected_by_id = {unit.unit_id for unit in selected}
    excluded = [unit for unit in admitted_units if unit.unit_id not in selected_by_id]
    metadata = {
        "unit_selection_mode": "curated_default",
        "selection_reason": "Auto-curated report plan prefers declarative, non-duplicative subject units and omits low-signal question-style material by default.",
        "auto_selected_unit_titles": [
            collapse_ws(unit.canonical_title) or unit.unit_id
            for unit in selected
        ],
        "auto_excluded_unit_titles": [
            collapse_ws(unit.canonical_title) or unit.unit_id
            for unit in excluded
        ],
        "auto_selected_unit_count": len(selected),
        "auto_excluded_unit_count": len(excluded),
    }
    return tuple(selected), tuple(excluded), metadata
    basis_block = PublicationBlock(
        block_id=stable_publication_block_id(
            publication_id=publication_id,
            block_kind="governed_basis",
            title="Governed Publication Basis",
            anchor_id="publication",
        ),
        publication_id=publication_id,
        block_kind="governed_basis",
        title="Governed Publication Basis",
        body=f"This publication is a governed {publication_type} projection derived from the current LearningContext snapshot for {context.canonical_title}.",
        included_block_refs=(),
        status="active",
    )
    blocks: list[PublicationBlock] = [scope_block, basis_block]
    for section_id, role, section_title in _REPORT_SECTIONS:
        if section_id != "report-summary" and not section_claim_ids.get(section_id):
            continue
        included_block_refs: tuple[str, ...]
        if section_id == "report-summary":
            included_block_refs = (basis_block.block_id, scope_block.block_id)
        elif role == "evidence":
            included_block_refs = (basis_block.block_id,)
        else:
            included_block_refs = ()
        blocks.append(
            PublicationBlock(
                block_id=stable_publication_block_id(
                    publication_id=publication_id,
                    block_kind="section_lead",
                    title=f"{section_title} Lead",
                    anchor_id=section_id,
                ),
                publication_id=publication_id,
                block_kind="section_lead",
                title=f"{section_title} Lead",
                body=_SECTION_ROLE_BLOCK_BODIES.get(role, f"This section carries the {role} role for the publication."),
                included_block_refs=included_block_refs,
                status="active",
            )
        )
    return tuple(blocks)


def _entity_kind_for_unit(unit: LearningUnit) -> str:
    if unit.unit_kind == "ability":
        return "procedure"
    if unit.unit_kind in {"example", "counterexample", "source_note"}:
        return "example"
    return "concept"


def _publication_entities(publication_id: str, selected_units: tuple[LearningUnit, ...]) -> tuple[PublicationEntity, ...]:
    entities: list[PublicationEntity] = []
    seen_keys: set[tuple[str, str]] = set()
    for unit in selected_units:
        canonical_name = collapse_ws(unit.canonical_title or unit.unit_id)
        if not canonical_name:
            continue
        entity_kind = _entity_kind_for_unit(unit)
        seen_key = (entity_kind, canonical_name.casefold())
        if seen_key in seen_keys:
            continue
        seen_keys.add(seen_key)
        entities.append(
            PublicationEntity(
                entity_id=stable_publication_entity_id(
                    publication_id=publication_id,
                    entity_kind=entity_kind,
                    canonical_name=canonical_name,
                ),
                publication_id=publication_id,
                entity_kind=entity_kind,
                canonical_name=canonical_name,
                aliases=(unit.unit_id,),
                source_ref=f"unit:{unit.unit_id}",
            )
        )
    return tuple(entities)


def _publication_review_records(
    publication_id: str,
    validation_status: str,
    *,
    build_epoch_ms: int,
) -> tuple[PublicationReviewRecord, ...]:
    review_state = "approved" if validation_status == "ok" else "changes_requested"
    reviewer = "publication_validation"
    return (
        PublicationReviewRecord(
            review_id=stable_publication_review_id(
                publication_id=publication_id,
                target_kind="publication",
                target_id=publication_id,
                reviewer=reviewer,
                review_state=review_state,
            ),
            publication_id=publication_id,
            target_kind="publication",
            target_id=publication_id,
            review_state=review_state,
            reviewer=reviewer,
            reason=f"deterministic validation status: {validation_status}",
            created_at_epoch_ms=build_epoch_ms,
        ),
    )


def _approved_subject_imports(root_path: Path, subject_id: str) -> tuple[SubjectImport, ...]:
    return tuple(
        item
        for item in list_subject_imports(root_path, subject_id)
        if item.status == "active" and item.review_status == "approved"
    )


def _selected_subject_imports(
    root_path: Path,
    subject_id: str,
    selected_subject_import_ids: tuple[str, ...] | None,
) -> tuple[SubjectImport, ...]:
    approved = _approved_subject_imports(root_path, subject_id)
    if selected_subject_import_ids is None:
        return approved
    selected = tuple(
        collapse_ws(subject_import_id)
        for subject_import_id in selected_subject_import_ids
        if collapse_ws(subject_import_id)
    )
    if not selected:
        return ()
    approved_by_id = {
        collapse_ws(item.import_id): item
        for item in approved
        if collapse_ws(item.import_id)
    }
    return tuple(approved_by_id[import_id] for import_id in selected if import_id in approved_by_id)


def _subject_import_dependency_summary(subject_import: SubjectImport) -> str:
    slice_parts: list[str] = []
    if subject_import.imported_unit_ids:
        slice_parts.append(f"{len(subject_import.imported_unit_ids)} units")
    if subject_import.imported_skill_ids:
        slice_parts.append(f"{len(subject_import.imported_skill_ids)} skills")
    if subject_import.imported_source_ids:
        slice_parts.append(f"{len(subject_import.imported_source_ids)} sources")
    if subject_import.imported_claim_ids:
        slice_parts.append(f"{len(subject_import.imported_claim_ids)} claims")
    if subject_import.imported_section_ids:
        slice_parts.append(f"{len(subject_import.imported_section_ids)} sections")
    if not slice_parts:
        slice_parts.append("bounded import without explicit slice ids")
    rationale = collapse_ws(subject_import.rationale)
    summary = ", ".join(slice_parts)
    if rationale:
        return f"{subject_import.import_kind}: {summary}. {rationale}"
    return f"{subject_import.import_kind}: {summary}."


def _publication_import_dependency_sources(
    root_path: Path,
    publication_id: str,
    subject_imports: tuple[SubjectImport, ...],
) -> tuple[PublicationSource, ...]:
    return tuple(
        PublicationSource(
            source_id=subject_import.import_id,
            publication_id=publication_id,
            title=(
                f"Imported Subject: {subject_import.source_subject_title}"
                if collapse_ws(subject_import.source_subject_title)
                else f"Imported Subject: {subject_import.source_subject_id}"
            ),
            publisher="",
            source_ref=_publication_source_ref_label(
                root_path,
                f"corpus/{subject_import.source_subject_id}/context.json",
            ),
            published_at="",
            retrieved_at_epoch_ms=subject_import.created_at_epoch_ms,
            trust_class="subject_import",
            freshness_class="snapshot",
            jurisdiction=subject_import.source_subject_id,
            excerpt=_subject_import_dependency_summary(subject_import),
        )
        for subject_import in subject_imports
    )


def _publication_import_dependency_xrefs(
    publication_id: str,
    subject_imports: tuple[SubjectImport, ...],
) -> tuple[PublicationCrossReference, ...]:
    return tuple(
        PublicationCrossReference(
            xref_id=stable_publication_xref_id(
                publication_id=publication_id,
                from_kind="publication",
                from_id=publication_id,
                xref_type="depends_on",
                to_kind="source",
                to_id=subject_import.import_id,
            ),
            publication_id=publication_id,
            from_id=publication_id,
            to_id=subject_import.import_id,
            xref_type="depends_on",
            from_kind="publication",
            to_kind="source",
            status="active",
            metadata={
                "dependency_kind": "subject_import",
                "source_subject_id": subject_import.source_subject_id,
                "source_subject_version_id": subject_import.source_subject_version_id,
                "import_kind": subject_import.import_kind,
            },
        )
        for subject_import in subject_imports
    )


def publication_from_learning_context(
    root_path: Path,
    context: LearningContext,
    *,
    publication_type: str = "report",
    title: str | None = None,
    scope_summary: str = "",
    included_unit_ids: tuple[str, ...] = (),
    excluded_unit_ids: tuple[str, ...] = (),
    selected_subject_import_ids: tuple[str, ...] | None = None,
    section_ids: tuple[str, ...] = (),
    build_epoch_ms: int = 0,
    review_items: tuple[ReviewItem, ...] = (),
    composition_metadata: dict[str, object] | None = None,
) -> tuple[
    Publication,
    tuple[PublicationSection, ...],
    tuple[PublicationBlock, ...],
    tuple[PublicationClaim, ...],
    tuple[PublicationSource, ...],
    tuple[PublicationEntity, ...],
    tuple[PublicationCrossReference, ...],
    tuple[PublicationReviewRecord, ...],
]:
    normalized_title = collapse_ws(title or f"{context.canonical_title} Report")
    publication_id = stable_publication_id(
        subject_id=context.subject_id,
        publication_type=publication_type,
        title=normalized_title,
    )
    active_composition_metadata = dict(composition_metadata or {})
    subject_imports = _selected_subject_imports(root_path, context.subject_id, selected_subject_import_ids)
    selected_units = _selected_units(context, included_unit_ids, excluded_unit_ids)
    selected_units_by_id = {unit.unit_id: unit for unit in selected_units}
    selected_review_items = tuple(
        item
        for item in _ordered_included_leaf_review_items(review_items)
        if collapse_ws(item.source_unit_id) in selected_units_by_id
    )
    if selected_review_items:
        ordered_unit_ids = tuple(
            dict.fromkeys(
                collapse_ws(item.source_unit_id)
                for item in selected_review_items
                if collapse_ws(item.source_unit_id) in selected_units_by_id
            )
        )
        selected_units = tuple(selected_units_by_id[unit_id] for unit_id in ordered_unit_ids) + tuple(
            unit
            for unit in selected_units
            if unit.unit_id not in set(ordered_unit_ids)
        )
        selected_units_by_id = {unit.unit_id: unit for unit in selected_units}
    selected_section_ids = tuple(
        collapse_ws(section_id)
        for section_id in section_ids
        if collapse_ws(section_id)
    )
    exact_draft = _is_exact_draft_publication_type(publication_type)
    selected_section_id_set = set(selected_section_ids)
    decision_frame = _decision_frame_from_metadata(active_composition_metadata)
    decision_policy_profile = _decision_policy_profile_from_metadata(active_composition_metadata)
    decision_receipt = _decision_analysis_receipt_from_metadata(active_composition_metadata)
    decision_review_items = _decision_review_items_from_metadata(active_composition_metadata)
    transform_receipts = _review_transform_receipts_from_metadata(active_composition_metadata)
    section_guidance_entries = _section_guidance_entries_from_metadata(active_composition_metadata)
    decision_report_mode = not exact_draft and decision_frame is not None and decision_receipt is not None
    report_section_specs = _expanded_report_sections(decision_report_mode=decision_report_mode)
    root_section_ids = tuple(section_id for section_id, _role, _title, parent_id in report_section_specs if not parent_id)
    child_section_ids_by_parent = {
        section_id: tuple(
            child_section_id
            for child_section_id, _child_role, _child_title, parent_id in report_section_specs
            if parent_id == section_id
        )
        for section_id in root_section_ids
    }
    section_claim_ids: dict[str, list[str]] = {section_id: [] for section_id, _role, _title, _parent in report_section_specs}
    claims: list[PublicationClaim] = []
    source_ids_seen: list[str] = []
    claim_inputs: list[tuple[LearningUnit, str, str]] = []
    if selected_review_items:
        for item in selected_review_items:
            unit = selected_units_by_id.get(collapse_ws(item.source_unit_id))
            if unit is None:
                continue
            claim_inputs.append(
                (
                    unit,
                    _claim_statement_for_review_item(item, unit),
                    _section_key_for_review_item(item, unit),
                )
            )
    else:
        claim_inputs = [
            (
                unit,
                _reader_facing_claim_statement(unit.statement or unit.canonical_title or unit.unit_id),
                _section_key_for_unit(unit),
            )
            for unit in selected_units
        ]
    for index, (unit, statement, section_key) in enumerate(claim_inputs, start=1):
        if exact_draft:
            source_ids_seen.extend(list(unit.provenance_refs))
            continue
        claim_id = f"clm-{index:03d}"
        canonical_name = collapse_ws(unit.canonical_title or unit.unit_id)
        entity_id = (
            stable_publication_entity_id(
                publication_id=publication_id,
                entity_kind=_entity_kind_for_unit(unit),
                canonical_name=canonical_name,
            )
            if canonical_name
            else ""
        )
        claim = PublicationClaim(
            claim_id=claim_id,
            publication_id=publication_id,
            statement=statement,
            claim_kind=_claim_kind_for_unit(unit),
            scope=context.subject_id,
            status="active",
            certainty="supported",
            source_ids=tuple(unit.provenance_refs),
            entity_ids=((entity_id,) if entity_id else ()),
            related_unit_ids=(unit.unit_id,),
            xref_ids=(),
            last_reviewed_epoch_ms=build_epoch_ms,
        )
        claims.append(claim)
        section_claim_ids[section_key].append(claim_id)
        source_ids_seen.extend(list(unit.provenance_refs))
    blocks = (
        ()
        if exact_draft
        else _publication_blocks(
            publication_id,
            context,
            publication_type=publication_type,
            scope_summary=scope_summary or _publication_scope_summary_text(
                publication_type=publication_type,
                subject_title=context.canonical_title,
            ),
            section_claim_ids=section_claim_ids,
        )
    )
    review_item_blocks: list[tuple[str, PublicationBlock]] = []
    if not decision_report_mode:
        for item in selected_review_items:
            unit = selected_units_by_id.get(collapse_ws(item.source_unit_id))
            if unit is None:
                continue
            block = _review_item_block(
                publication_id,
                publication_type=publication_type,
                item=item,
                unit=unit,
            )
            if block is None:
                continue
            review_item_blocks.append((_section_key_for_review_item(item, unit), block))
        review_item_blocks = _dedupe_section_blocks(review_item_blocks)
    if exact_draft and not review_item_blocks:
        for unit in selected_units:
            fallback_statement = _reader_facing_claim_statement(unit.statement or unit.canonical_title or unit.unit_id)
            if not collapse_ws(fallback_statement):
                continue
            block = PublicationBlock(
                block_id=stable_publication_block_id(
                    publication_id=publication_id,
                    block_kind="review_paragraph",
                    title=collapse_ws(unit.canonical_title) or collapse_ws(unit.unit_id) or "Draft Item",
                    anchor_id=unit.unit_id,
                ),
                publication_id=publication_id,
                block_kind="review_paragraph",
                title=collapse_ws(unit.canonical_title) or collapse_ws(unit.unit_id) or "Draft Item",
                body=fallback_statement,
                included_block_refs=(),
                status="active",
            )
            review_item_blocks.append((_section_key_for_unit(unit), block))
    extra_blocks: list[PublicationBlock] = []
    section_guidance_blocks_by_section: dict[str, list[PublicationBlock]] = {}
    if not exact_draft:
        section_title_by_id = {
            section_id: title
            for section_id, _role, title, _parent in report_section_specs
        }
        for section_id, label, text in section_guidance_entries:
            if section_id not in section_title_by_id:
                continue
            section_guidance_blocks_by_section.setdefault(section_id, []).append(
                _section_guidance_block(
                    publication_id,
                    section_id=section_id,
                    title=section_title_by_id[section_id],
                    label=label,
                    text=text,
                )
            )
    if decision_report_mode:
        extra_blocks.append(
            _decision_case_frame_block(
                publication_id,
                frame=decision_frame,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_summary_block(
                publication_id,
                frame=decision_frame,
                policy_profile=decision_policy_profile,
                receipt=decision_receipt,
            )
        )
        extra_blocks.append(
            _decision_matrix_block(
                publication_id,
                receipt=decision_receipt,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_transition_roadmap_block(
                publication_id,
                frame=decision_frame,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_simple_diagram_block(
                publication_id,
                receipt=decision_receipt,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_ranking_summary_block(
                publication_id,
                policy_profile=decision_policy_profile,
                receipt=decision_receipt,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_dependency_checklist_block(
                publication_id,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_risk_matrix_block(
                publication_id,
                receipt=decision_receipt,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_execution_guidance_block(
                publication_id,
                receipt=decision_receipt,
                decision_items=decision_review_items,
            )
        )
        extra_blocks.append(
            _decision_recommendation_receipt_block(
                publication_id,
                frame=decision_frame,
                policy_profile=decision_policy_profile,
                receipt=decision_receipt,
                decision_items=decision_review_items,
            )
        )
    if not exact_draft and transform_receipts:
        extra_blocks.append(
            _review_transform_block(
                publication_id,
                receipts=transform_receipts,
            )
        )
    blocks = tuple(
        [
            *blocks,
            *(
                block
                for section_id in (
                    section_id for section_id, _role, _title, _parent in report_section_specs
                )
                for block in section_guidance_blocks_by_section.get(section_id, [])
            ),
            *(block for _section_key, block in review_item_blocks),
            *extra_blocks,
        ]
    )
    block_by_id = {block.block_id: block for block in blocks}
    section_block_ids: dict[str, list[str]] = {section_id: [] for section_id, _role, _title, _parent in report_section_specs}
    block_by_title = {block.title: block for block in blocks}
    if not exact_draft:
        for section_id, _role, section_title in _REPORT_SECTIONS:
            if selected_section_ids and section_id not in selected_section_id_set:
                continue
            for guidance_block in section_guidance_blocks_by_section.get(section_id, []):
                section_block_ids[section_id].append(guidance_block.block_id)
            lead_block = block_by_title.get(f"{section_title} Lead")
            if lead_block is not None:
                section_block_ids[section_id].append(lead_block.block_id)
        for section_key, block in review_item_blocks:
            if selected_section_ids and section_key not in selected_section_id_set:
                continue
            section_block_ids.setdefault(section_key, []).append(block.block_id)
        for block in extra_blocks:
            if collapse_ws(block.block_kind) == "decision_summary":
                section_block_ids["report-summary"].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_case_frame":
                section_block_ids["report-definitions"].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_matrix":
                target_section_id = "report-analysis-options" if decision_report_mode else "report-analysis"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_transition_roadmap":
                target_section_id = "report-analysis-model" if decision_report_mode else "report-analysis"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_simple_diagram":
                target_section_id = "report-analysis-model" if decision_report_mode else "report-analysis"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_ranking_summary":
                target_section_id = "report-analysis-options" if decision_report_mode else "report-analysis"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_dependency_checklist":
                target_section_id = "report-analysis-risk" if decision_report_mode else "report-analysis"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_risk_matrix":
                target_section_id = "report-analysis-risk" if decision_report_mode else "report-analysis"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_execution_guidance":
                target_section_id = "report-implementation-guidance" if decision_report_mode else "report-implementation"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "decision_recommendation_receipt":
                target_section_id = "report-appendix-receipt" if decision_report_mode else "report-appendix"
                section_block_ids[target_section_id].append(block.block_id)
            elif collapse_ws(block.block_kind) == "review_transform_receipts":
                target_section_id = "report-appendix-receipt" if decision_report_mode else "report-appendix"
                section_block_ids[target_section_id].append(block.block_id)
    xrefs = () if exact_draft else tuple(
        [
            *_section_xrefs(publication_id, section_claim_ids),
            *_claim_projection_xrefs(publication_id, tuple(claims)),
        ]
    )
    if selected_section_ids and not exact_draft:
        xrefs = tuple(
            xref
            for xref in xrefs
            if (
                collapse_ws(xref.from_kind) != "section"
                and collapse_ws(xref.to_kind) != "section"
            )
            or (
                collapse_ws(xref.from_kind) == "section"
                and collapse_ws(xref.to_kind) == "section"
                and collapse_ws(xref.from_id) in selected_section_id_set
                and collapse_ws(xref.to_id) in selected_section_id_set
            )
        )
    section_xref_ids: dict[str, list[str]] = {section_id: [] for section_id, _role, _title, _parent in report_section_specs}
    for xref in xrefs:
        if xref.from_kind == "section":
            section_xref_ids.setdefault(xref.from_id, []).append(xref.xref_id)
    section_specs_by_id = {
        section_id: (role, section_title, parent_section_id)
        for section_id, role, section_title, parent_section_id in report_section_specs
    }
    section_block_kinds: dict[str, set[str]] = {}
    for section_id, block_ids in section_block_ids.items():
        section_block_kinds[section_id] = {
            collapse_ws(block_by_id[block_id].block_kind)
            for block_id in block_ids
            if block_id in block_by_id and collapse_ws(block_by_id[block_id].block_kind) != "section_lead"
        }

    contentful_section_cache: dict[str, bool] = {}

    def _section_has_content(section_id: str) -> bool:
        cached = contentful_section_cache.get(section_id)
        if cached is not None:
            return cached
        has_claims = bool(section_claim_ids.get(section_id))
        has_substantive_blocks = bool(section_block_kinds.get(section_id))
        has_any_blocks = bool(section_block_ids.get(section_id))
        has_content = has_claims or has_substantive_blocks or (
            section_id == "report-summary" and has_any_blocks
        ) or any(
            _section_has_content(child_section_id)
            for child_section_id in child_section_ids_by_parent.get(section_id, ())
        )
        contentful_section_cache[section_id] = has_content
        return has_content

    if exact_draft:
        sections = ()
    else:
        if selected_section_ids:
            ordered_section_ids = selected_section_ids
            included_root_section_ids = tuple(
                section_id
                for section_id in ordered_section_ids
                if section_id in section_specs_by_id and not section_specs_by_id[section_id][2]
            )
        else:
            included_root_section_ids = tuple(
                section_id
                for section_id in root_section_ids
                if section_id in section_specs_by_id and _section_has_content(section_id)
            )
        included_section_ids: list[str] = []
        for section_id in included_root_section_ids:
            included_section_ids.append(section_id)
            if selected_section_ids:
                included_section_ids.extend(child_section_ids_by_parent.get(section_id, ()))
            else:
                included_section_ids.extend(
                    child_section_id
                    for child_section_id in child_section_ids_by_parent.get(section_id, ())
                    if _section_has_content(child_section_id)
                )
        section_ordinal_by_id: dict[str, str] = {}
        for root_index, section_id in enumerate(included_root_section_ids, start=1):
            section_ordinal_by_id[section_id] = str(root_index)
            visible_child_ids = tuple(
                child_id
                for child_id in child_section_ids_by_parent.get(section_id, ())
                if child_id in included_section_ids
            )
            for child_index, child_id in enumerate(visible_child_ids, start=1):
                if child_id in included_section_ids:
                    section_ordinal_by_id[child_id] = f"{root_index}.{child_index}"
        sections = tuple(
            PublicationSection(
                section_id=section_id,
                publication_id=publication_id,
                parent_section_id=section_specs_by_id[section_id][2],
                role=section_specs_by_id[section_id][0],
                title=_section_title_for_block_kinds(
                    section_id,
                    default_title=section_specs_by_id[section_id][1],
                    block_kinds=section_block_kinds.get(section_id, set()),
                ),
                ordinal=section_ordinal_by_id.get(section_id, str(index)),
                child_section_ids=tuple(
                    child_id
                    for child_id in child_section_ids_by_parent.get(section_id, ())
                    if child_id in included_section_ids
                ),
                block_ids=tuple(section_block_ids.get(section_id, [])),
                claim_ids=tuple(section_claim_ids.get(section_id, [])),
                xref_ids=tuple(section_xref_ids.get(section_id, [])),
                status="active",
            )
            for index, section_id in enumerate(included_section_ids, start=1)
            if section_id in section_specs_by_id
        )
    sources: list[PublicationSource] = []
    for source_id in sorted(set(source_ids_seen)):
        try:
            source = load_learning_source(root_path, context.subject_id, source_id)
        except FileNotFoundError:
            sources.append(
                PublicationSource(
                source_id=source_id,
                publication_id=publication_id,
                title=source_id,
                publisher="",
                source_ref="",
                    published_at="",
                    retrieved_at_epoch_ms=0,
                    trust_class="unknown",
                    freshness_class="snapshot",
                    jurisdiction="",
                    excerpt="",
                )
            )
            continue
        sources.append(
            PublicationSource(
                source_id=source.source_id,
                publication_id=publication_id,
                title=source.title or source.source_id,
                publisher="",
                source_ref=_publication_source_ref_label(root_path, source.source_ref),
                published_at="",
                retrieved_at_epoch_ms=0,
                trust_class="corpus_source",
                freshness_class="snapshot",
                jurisdiction="",
                excerpt=(source.title or source.source_id),
            )
        )
    sources.extend(_publication_import_dependency_sources(root_path, publication_id, subject_imports))
    entities = _publication_entities(publication_id, selected_units)
    xrefs = tuple(list(xrefs) + ([] if exact_draft else list(_publication_import_dependency_xrefs(publication_id, subject_imports))))
    review_records = _publication_review_records(
        publication_id,
        "ok",
        build_epoch_ms=build_epoch_ms,
    )
    publication = Publication(
        publication_id=publication_id,
        publication_type=publication_type,
        subject_id=context.subject_id,
        title=normalized_title,
        status="draft",
        scope_summary=scope_summary or _publication_scope_summary_text(
            publication_type=publication_type,
            subject_title=context.canonical_title,
        ),
        learning_context_ref=f"corpus/{context.subject_id}/context.json",
        learning_context_snapshot_hash=context.content_hash(),
        included_unit_ids=tuple(unit.unit_id for unit in selected_units),
        excluded_unit_ids=tuple(excluded_unit_ids),
        root_section_ids=tuple(section.section_id for section in sections if not collapse_ws(section.parent_section_id)),
        block_ids=tuple(block.block_id for block in blocks),
        claim_ids=tuple(claim.claim_id for claim in claims),
        entity_ids=tuple(entity.entity_id for entity in entities),
        source_ids=tuple(source.source_id for source in sources),
        created_at_epoch_ms=build_epoch_ms,
        updated_at_epoch_ms=build_epoch_ms,
    )
    return publication, sections, blocks, tuple(claims), tuple(sources), entities, xrefs, review_records


def publication_composition_from_learning_context(
    root_path: Path,
    context: LearningContext,
    *,
    publication_type: str = "report",
    title: str | None = None,
    scope_summary: str = "",
    included_unit_ids: tuple[str, ...] = (),
    excluded_unit_ids: tuple[str, ...] = (),
    selected_subject_import_ids: tuple[str, ...] | None = None,
    section_ids: tuple[str, ...] = (),
    build_epoch_ms: int = 0,
    status: str = "draft",
    import_usage_by_id: dict[str, str] | None = None,
) -> PublicationComposition:
    normalized_title = collapse_ws(title or f"{context.canonical_title} Report")
    publication_id = stable_publication_id(
        subject_id=context.subject_id,
        publication_type=publication_type,
        title=normalized_title,
    )
    explicit_unit_scope = bool(included_unit_ids or excluded_unit_ids)
    if explicit_unit_scope:
        explicit_units = _selected_units(context, included_unit_ids, excluded_unit_ids)
        selected_units = tuple(unit for unit in explicit_units if _reportable_unit(unit))
        non_reportable_unit_ids = tuple(unit.unit_id for unit in explicit_units if not _reportable_unit(unit))
        effective_excluded_unit_ids = tuple(
            dict.fromkeys(
                [
                    *(collapse_ws(unit_id) for unit_id in excluded_unit_ids if collapse_ws(unit_id)),
                    *non_reportable_unit_ids,
                ]
            )
        )
        composition_metadata: dict[str, object] = {
            "unit_selection_mode": "explicit",
            "selection_reason": "Report plan unit scope was explicitly shaped in Review.",
        }
    else:
        selected_units, excluded_units, composition_metadata = _default_report_unit_selection(context)
        effective_excluded_unit_ids = tuple(unit.unit_id for unit in excluded_units)
    known_section_ids = {section_id for section_id, _role, _title in _REPORT_SECTIONS}
    exact_draft = _is_exact_draft_publication_type(publication_type)
    effective_section_ids = (
        ()
        if exact_draft
        else (
            tuple(section_id for section_id in section_ids if section_id in known_section_ids)
            if section_ids
            else tuple(section_id for section_id, _role, _title in _REPORT_SECTIONS)
        )
    )
    effective_import_ids = tuple(
        item.import_id
        for item in _selected_subject_imports(root_path, context.subject_id, selected_subject_import_ids)
    )
    composition_id = stable_publication_composition_id(
        publication_id=publication_id,
        learning_context_snapshot_hash=context.content_hash(),
        title=normalized_title,
    )
    return PublicationComposition(
        composition_id=composition_id,
        publication_id=publication_id,
        subject_id=context.subject_id,
        publication_type=publication_type,
        title=normalized_title,
        scope_summary=scope_summary or _publication_scope_summary_text(
            publication_type=publication_type,
            subject_title=context.canonical_title,
        ),
        learning_context_snapshot_hash=context.content_hash(),
        selected_subject_import_ids=effective_import_ids,
        included_unit_ids=tuple(unit.unit_id for unit in selected_units),
        excluded_unit_ids=effective_excluded_unit_ids,
        section_ids=effective_section_ids,
        import_usage_by_id={collapse_ws(str(key)): collapse_ws(str(value)) for key, value in (import_usage_by_id or {}).items() if collapse_ws(str(key))},
        status=collapse_ws(status) or "draft",
        created_at_epoch_ms=build_epoch_ms,
        updated_at_epoch_ms=build_epoch_ms,
        metadata=composition_metadata,
    )


def materialize_report_publication_from_learning_context(
    root_path: Path,
    context: LearningContext,
    *,
    title: str | None = None,
    scope_summary: str = "",
    included_unit_ids: tuple[str, ...] = (),
    excluded_unit_ids: tuple[str, ...] = (),
    selected_subject_import_ids: tuple[str, ...] | None = None,
    section_ids: tuple[str, ...] = (),
    composition: PublicationComposition | None = None,
    build_epoch_ms: int = 0,
) -> dict[str, object]:
    effective_composition = composition
    if effective_composition is not None:
        if collapse_ws(effective_composition.learning_context_snapshot_hash) != collapse_ws(context.content_hash()):
            raise ValueError("publication composition snapshot does not match the current LearningContext snapshot")
        title = effective_composition.title
        scope_summary = effective_composition.scope_summary
        included_unit_ids = effective_composition.included_unit_ids
        excluded_unit_ids = effective_composition.excluded_unit_ids
        selected_subject_import_ids = effective_composition.selected_subject_import_ids
        section_ids = effective_composition.section_ids
    else:
        effective_composition = publication_composition_from_learning_context(
            root_path,
            context,
            publication_type="report",
            title=title,
            scope_summary=scope_summary,
            included_unit_ids=included_unit_ids,
            excluded_unit_ids=excluded_unit_ids,
            selected_subject_import_ids=selected_subject_import_ids,
            section_ids=section_ids,
            build_epoch_ms=build_epoch_ms,
            status="draft",
        )
        title = effective_composition.title
        scope_summary = effective_composition.scope_summary
        included_unit_ids = effective_composition.included_unit_ids
        excluded_unit_ids = effective_composition.excluded_unit_ids
        selected_subject_import_ids = effective_composition.selected_subject_import_ids
        section_ids = effective_composition.section_ids
    review_items = _review_items_from_composition_metadata(effective_composition.metadata)
    subject_imports = _selected_subject_imports(root_path, context.subject_id, selected_subject_import_ids)
    publication, sections, blocks, claims, sources, entities, xrefs, _initial_reviews = publication_from_learning_context(
        root_path,
        context,
        publication_type=effective_composition.publication_type,
        title=title,
        scope_summary=scope_summary,
        included_unit_ids=included_unit_ids,
        excluded_unit_ids=excluded_unit_ids,
        selected_subject_import_ids=selected_subject_import_ids,
        section_ids=section_ids,
        build_epoch_ms=build_epoch_ms,
        review_items=review_items,
        composition_metadata=effective_composition.metadata,
    )
    validation_report = validate_publication(
        publication,
        sections=sections,
        blocks=blocks,
        claims=claims,
        sources=sources,
        entities=entities,
        xrefs=xrefs,
        reviews=(),
    )
    report_typ = render_publication_typst(
        publication,
        sections=sections,
        blocks=blocks,
        claims=claims,
        sources=sources,
    )
    report_md = render_publication_markdown(
        publication,
        sections=sections,
        blocks=blocks,
        claims=claims,
        sources=sources,
    )
    typst_render_validation, report_pdf = validate_rendered_typst(report_typ)
    validation_report = dict(validation_report)
    validation_report["render_validation"] = {
        "typst_compile": typst_render_validation,
    }
    if typst_render_validation.get("status") == "error":
        errors = list(validation_report.get("errors", [])) if isinstance(validation_report.get("errors", []), list) else []
        stderr_text = collapse_ws(str(typst_render_validation.get("stderr", "")))
        errors.append(
            "rendered report.typ failed typst compile"
            + (f": {stderr_text}" if stderr_text else "")
        )
        validation_report["errors"] = errors
        validation_report["status"] = "error"
    review_records = _publication_review_records(
        publication.publication_id,
        collapse_ws(str(validation_report.get("status", ""))) or "error",
        build_epoch_ms=build_epoch_ms,
    )
    publication_path = persist_publication(
        root_path,
        publication,
        sections=sections,
        blocks=blocks,
        claims=claims,
        sources=sources,
        entities=entities,
        xrefs=xrefs,
        reviews=review_records,
    )
    composition_path = persist_publication_composition(
        root_path,
        PublicationComposition.from_dict(
            {
                **effective_composition.to_dict(),
                "publication_id": publication.publication_id,
                "status": collapse_ws(effective_composition.status) or "draft",
                "updated_at_epoch_ms": build_epoch_ms,
            }
        ),
    )
    build, render_artifacts, output_texts, output_blobs = publication_build_from_rendered_outputs(
        publication,
        learning_context_snapshot_hash=context.content_hash(),
        validation_report=validation_report,
        report_typ=report_typ,
        report_md=report_md,
        report_pdf=report_pdf,
        build_epoch_ms=build_epoch_ms,
    )
    build_path = persist_publication_build(
        root_path,
        context.subject_id,
        publication.publication_id,
        build,
        render_artifacts=render_artifacts,
        output_texts=output_texts,
        output_blobs=output_blobs,
    )
    return {
        "publication_id": publication.publication_id,
        "publication_path": str(publication_path),
        "composition_id": effective_composition.composition_id,
        "composition_path": str(composition_path),
        "composition_status": effective_composition.status,
        "build_id": build.build_id,
        "build_path": str(build_path),
        "validation_status": validation_report.get("status", ""),
        "validation_errors": tuple(validation_report.get("errors", ())) if isinstance(validation_report.get("errors", ()), list | tuple) else (),
        "section_count": len(sections),
        "block_count": len(blocks),
        "claim_count": len(claims),
        "source_count": len(sources),
        "entity_count": len(entities),
        "review_count": len(review_records),
        "xref_count": len(xrefs),
        "import_count": len(subject_imports),
        "imported_subject_count": len({item.source_subject_id for item in subject_imports}),
        "output_paths": {artifact.format: artifact.path for artifact in render_artifacts},
    }
