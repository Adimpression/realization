# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from realized_core_engine import markdown_learning_artifact_semantics as _artifact_semantics
from realized_core_semantics.applied_model import Artifact, NodeStatus, ProposalObject, RunOutcome, SupportScore, SupportView, ThreeLevel, json_safe
from realized_core_engine.artifact_semantics import artifact_with_id
from realized_core_runtime.execution import (
    fence_encounter_ability_payload,
    supported_fence_learning_records,
)
from realized_exchange.learning_context import (
    LearningDelta,
    LearningDeltaOperation,
    LearningUnit,
    apply_learning_delta,
    canonical_learning_subject_id,
    find_learning_context_by_lookup,
    load_learning_context,
    new_learning_context,
    new_learning_delta,
    new_learning_source,
    persist_learning_source_bundle_files,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    resolve_learning_context_root,
    learning_source_bundle_root,
    stable_learning_unit_id,
)
from realized_core_semantics.markdown import (
    MarkdownDocumentIR,
    is_generic_synthesis_field_name,
    is_generic_synthesis_question,
    looks_like_placeholder_python_script,
    markdown_direct_expression_mapping,
    markdown_document_symbol_aliases,
    markdown_encounter_aliases,
    markdown_encounter_question,
    markdown_learning_encounter_view,
    markdown_symbolic_mapping_from_encounter,
    merge_markdown_encounter_details,
    parse_markdown_document_ir,
)
from realized_core_semantics.semantic_text import collapse_ws, ordered_unique, titleize_semantic_unit


def _markdown_payload_signature(payload: Mapping[str, Any]) -> tuple[str, str, tuple[str, ...]]:
    """
    High Level Purpose:
        In circumstances like deduplicating multiple ability payloads derived from one markdown document, helps with computing the stable identity signature that decides when two payloads are really the same callable mapping.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `_markdown_payload_signature(payload={'encounter_id': 'ideal-gas', 'title': 'Pressure From Amount Temperature And Volume', 'content': {'output_field': 'P', 'input_contract': {'n': 'number', 'R': 'number', 'T': 'number', 'V': 'number'}}})`
        Output: ('ideal-gas', 'p', ('n', 'r', 't', 'v'))

    Args:
        payload: Value for `payload` used by `_markdown_payload_signature`. Expected type: `Mapping[str, Any]`.

    Returns:
        tuple[str, str, tuple[str, ...]]: Result produced by `_markdown_payload_signature`.
    """
    content = payload.get("content", {}) if isinstance(payload.get("content", {}), Mapping) else {}
    encounter_id = collapse_ws(str(payload.get("encounter_id", "")).strip())
    output_field = collapse_ws(str(content.get("output_field", payload.get("output_field", ""))).strip()).lower()
    input_contract = content.get("input_contract", {})
    if isinstance(input_contract, Mapping):
        input_fields = tuple(sorted(str(key).strip().lower() for key in input_contract.keys() if str(key).strip()))
    else:
        input_fields = tuple(
            sorted(
                str(item).strip().lower()
                for item in payload.get("input_fields", [])
                if str(item).strip()
            )
        ) if isinstance(payload.get("input_fields", []), list) else ()
    return (encounter_id or collapse_ws(str(payload.get("title", "")).strip()).lower(), output_field, input_fields)


def _persist_markdown_pipeline_artifact(self, artifact: Artifact) -> tuple[Artifact, dict[str, Any], str]:
    """
    High Level Purpose:
        In circumstances like persisting one newly learned markdown artifact into the configured store, helps with normalizing the post-persistence artifact identity and collecting the persistence report in one controlled step.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `_persist_markdown_pipeline_artifact(self=controller, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'))`
        Output: (Artifact(id='artifact-force-db', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'), {'artifact_id': 'artifact-force-db', 'status': 'persisted'}, 'artifact-force')

    Args:
        self: Bound controller instance that owns state and artifact-store persistence.
        artifact: Value for `artifact` used by `_persist_markdown_pipeline_artifact`. Expected type: `Artifact`.

    Returns:
        tuple[Artifact, dict[str, Any], str]: Result produced by `_persist_markdown_pipeline_artifact`.
    """
    persisted = _persist_markdown_pipeline_artifacts(self, [artifact])
    if not persisted:
        report = {"artifact_id": artifact.id, "status": "skipped", "reason": "nothing_to_persist"}
        self.state.artifact_persistence.append(json_safe(report))
        return artifact, json_safe(report), artifact.id
    return persisted[0]


def _persist_markdown_pipeline_artifacts(
    self,
    artifacts: Sequence[Artifact],
) -> list[tuple[Artifact, dict[str, Any], str]]:
    """
    High Level Purpose:
        In circumstances like persisting one markdown-learning batch into the configured store, helps with normalizing post-persistence artifact identities while preserving per-artifact reports from the store's batched persistence path.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity while avoiding repeated per-artifact persistence overhead.

    Example Input Output:
        Input: `_persist_markdown_pipeline_artifacts(self=controller, artifacts=[Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script')])`
        Output: [(Artifact(id='artifact-force-db', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'), {'artifact_id': 'artifact-force-db', 'status': 'persisted'}, 'artifact-force')]

    Args:
        self: Bound controller instance that owns state and artifact-store persistence.
        artifacts: Value for `artifacts` used by `_persist_markdown_pipeline_artifacts`. Expected type: `Sequence[Artifact]`.

    Returns:
        list[tuple[Artifact, dict[str, Any], str]]: Result produced by `_persist_markdown_pipeline_artifacts`.
    """
    artifact_list = list(artifacts)
    if not artifact_list:
        return []
    batch_report = self.artifact_store.persist_artifacts(artifact_list, run_id=self.state.run_id)
    if hasattr(self, "invalidate_current_skill_governance_snapshot"):
        self.invalidate_current_skill_governance_snapshot()
    report_items = [
        json_safe(dict(item))
        for item in batch_report.get("reports", [])
        if isinstance(item, Mapping)
    ]
    persisted: list[tuple[Artifact, dict[str, Any], str]] = []
    batch_timings = dict(batch_report.get("timings", {})) if isinstance(batch_report.get("timings", {}), Mapping) else {}
    batch_status = collapse_ws(str(batch_report.get("status", "")).strip())
    batch_reason = collapse_ws(str(batch_report.get("reason", "")).strip())
    for index, artifact in enumerate(artifact_list):
        previous_artifact_id = artifact.id
        report = (
            dict(report_items[index])
            if index < len(report_items)
            else {
                "artifact_id": artifact.id,
                "status": batch_status or "skipped",
                "reason": batch_reason,
            }
        )
        if batch_timings:
            report.setdefault("batch_timings", dict(batch_timings))
        persisted_artifact_id = collapse_ws(str(report.get("artifact_id", "")).strip())
        if persisted_artifact_id and persisted_artifact_id != artifact.id:
            artifact = artifact_with_id(artifact, persisted_artifact_id)
            self.state.artifacts.pop(previous_artifact_id, None)
            self.state.learned_artifacts.pop(previous_artifact_id, None)
            self.state.artifacts[artifact.id] = artifact
            self.state.learned_artifacts[artifact.id] = artifact
        self.state.artifact_persistence.append(json_safe(report))
        persisted.append((artifact, json_safe(report), previous_artifact_id))
    return persisted


def _learned_markdown_artifact_report(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like returning a compact learning report after markdown ingestion, helps with projecting one persisted artifact into the small summary shape used by the learning result payload.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `_learned_markdown_artifact_report(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'))`
        Output: {'artifact_id': 'artifact-force', 'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python_script', 'function_bit': 1, 'question': 'How do you calculate force?', 'related_artifact_ids': [], 'source_sections': []}

    Args:
        artifact: Value for `artifact` used by `_learned_markdown_artifact_report`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `_learned_markdown_artifact_report`.
    """
    return {
        "artifact_id": artifact.id,
        "title": artifact.title,
        "artifact_type": artifact.artifact_type,
        "representation": artifact.representation,
        "function_bit": artifact.function_bit,
        "question": str(artifact.content.get("question", "")).strip(),
        "related_artifact_ids": list(artifact.related_artifact_ids),
        "source_sections": list(artifact.content.get("source_sections", [])),
    }


def _markdown_learning_subject_title(document: MarkdownDocumentIR, source_path: Path) -> str:
    title = collapse_ws(str(document.title or ""))
    if title:
        return title
    return titleize_semantic_unit(source_path.stem) or source_path.stem


def _markdown_learning_subject_metadata(document: MarkdownDocumentIR) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "subject_id": "",
        "canonical_title": "",
        "aliases": (),
        "subject_family": "",
        "summary": "",
    }
    candidate_lines = [
        collapse_ws(str(item))
        for item in [*document.intro_bullets, *document.intro_paragraphs]
        if collapse_ws(str(item))
    ]
    for line in candidate_lines:
        if ":" not in line:
            continue
        raw_key, raw_value = line.split(":", 1)
        key = collapse_ws(raw_key).lower().replace("_", " ")
        value = collapse_ws(raw_value)
        if not value:
            continue
        if key in {"subject", "subject title", "canonical subject", "canonical title"}:
            metadata["canonical_title"] = value
        elif key in {"subject id", "subject identifier"}:
            metadata["subject_id"] = canonical_learning_subject_id(value)
        elif key in {"aliases", "alias"}:
            separator = ";" if ";" in value else ","
            metadata["aliases"] = ordered_unique(item.strip() for item in value.split(separator) if item.strip())
        elif key in {"subject family", "family", "category"}:
            metadata["subject_family"] = value
        elif key == "summary":
            metadata["summary"] = value
    return metadata


def _resolved_markdown_learning_subject(
    document: MarkdownDocumentIR,
    source_path: Path,
    *,
    corpus_root: Path,
) -> dict[str, Any]:
    metadata = _markdown_learning_subject_metadata(document)
    inferred_title = _markdown_learning_subject_title(document, source_path)
    source_title = titleize_semantic_unit(source_path.stem) or source_path.stem
    explicit_subject_id = collapse_ws(str(metadata.get("subject_id", "")))
    explicit_title = collapse_ws(str(metadata.get("canonical_title", "")))
    explicit_aliases = ordered_unique(metadata.get("aliases", ()))
    existing_context = None
    if explicit_subject_id:
        try:
            existing_context = load_learning_context(corpus_root, explicit_subject_id)
        except FileNotFoundError:
            existing_context = None
    if existing_context is None:
        existing_context = find_learning_context_by_lookup(
            corpus_root,
            explicit_title,
            document.title,
            source_title,
            *explicit_aliases,
        )
    subject_id = (
        existing_context.subject_id
        if existing_context is not None
        else explicit_subject_id or canonical_learning_subject_id(explicit_title or inferred_title)
    )
    canonical_title = (
        existing_context.canonical_title
        if existing_context is not None
        else explicit_title or inferred_title
    )
    return {
        "subject_id": subject_id,
        "canonical_title": canonical_title,
        "aliases": ordered_unique(
            [canonical_title]
            + list(getattr(existing_context, "aliases", ()))
            + ([document.title] if collapse_ws(str(document.title)) else [])
            + ([source_title] if source_title else [])
            + list(explicit_aliases)
            + ([explicit_title] if explicit_title else [])
        ),
        "subject_family": collapse_ws(
            str(
                getattr(existing_context, "subject_family", "")
                or metadata.get("subject_family", "")
            )
        ),
        "summary": str(getattr(existing_context, "summary", "") or metadata.get("summary", "")),
        "declared_subject_id": explicit_subject_id,
        "declared_subject_title": explicit_title,
        "matched_existing_subject_id": getattr(existing_context, "subject_id", ""),
    }


def _learning_unit_kind_for_markdown_artifact(artifact: Artifact) -> str:
    artifact_type = collapse_ws(str(getattr(artifact, "artifact_type", ""))).lower()
    if artifact_type == "ability":
        return "ability"
    if list(getattr(artifact, "related_artifact_ids", []) or []):
        return "relation"
    return "definition"


def _learning_unit_from_markdown_artifact(
    artifact: Artifact,
    *,
    subject_id: str,
    source_id: str,
) -> LearningUnit:
    content = artifact.content if isinstance(artifact.content, Mapping) else {}
    statement = str(content.get("answer", "")).strip()
    if not statement:
        statement = str(content.get("question", "")).strip()
    if not statement:
        statement = str(getattr(artifact, "scope", "") or "").strip()
    return LearningUnit(
        unit_id=stable_learning_unit_id(
            subject_id=subject_id,
            unit_kind=_learning_unit_kind_for_markdown_artifact(artifact),
            canonical_title=collapse_ws(str(artifact.title)),
        ),
        subject_id=subject_id,
        unit_kind=_learning_unit_kind_for_markdown_artifact(artifact),
        canonical_title=collapse_ws(str(artifact.title)),
        aliases=ordered_unique(
            [
                str(item).strip()
                for item in content.get("aliases", [])
                if str(item).strip()
            ]
            if isinstance(content.get("aliases", []), list)
            else []
        ),
        statement=statement,
        structured_fields={
            key: json_safe(value)
            for key, value in {
                "artifact_type": getattr(artifact, "artifact_type", ""),
                "representation": getattr(artifact, "representation", ""),
                "question": content.get("question", ""),
                "output_field": content.get("output_field", ""),
                "input_contract": content.get("input_contract", {}),
            }.items()
            if value not in ("", None, {}, [])
        },
        provenance_refs=(source_id,),
        status="admitted",
        linked_artifact_ids=(artifact.id,),
        linked_skill_ids=(),
        linked_section_ids=tuple(
            str(item).strip()
            for item in content.get("source_sections", [])
            if str(item).strip()
        )
        if isinstance(content.get("source_sections", []), list)
        else (),
        metadata={
            "learning_relation": str(getattr(artifact, "learning_relation", "")),
            "scope": str(getattr(artifact, "scope", "")),
        },
    )


def markdown_expression_artifact_payload(
    self,
    *,
    encounter: Mapping[str, Any],
    synthesis_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like turning one executable markdown encounter into a callable artifact candidate, helps with projecting the encounter and synthesis result into an ability payload without committing it yet.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `markdown_expression_artifact_payload(self=controller, encounter={'heading': 'Pressure from amount, temperature, and volume', 'encounter_id': 'ideal-gas'}, synthesis_payload={'parameterized': True, 'input_fields': ['n', 'R', 'T', 'V'], 'output_field': 'P', 'compute_expression': 'n * R * T / V', 'question': 'How do you calculate pressure?'})`
        Output: {'artifact_type': 'ability', 'title': 'Pressure From Amount Temperature And Volume', 'representation': 'python_script'}

    Args:
        self: Bound controller instance that owns markdown question and alias helpers.
        encounter: Value for `encounter` used by `markdown_expression_artifact_payload`. Expected type: `Mapping[str, Any]`.
        synthesis_payload: Value for `synthesis_payload` used by `markdown_expression_artifact_payload`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any] | None: Result produced by `markdown_expression_artifact_payload`.
    """
    parameterized = bool(synthesis_payload.get("parameterized", False))
    input_fields = [str(item).strip() for item in synthesis_payload.get("input_fields", []) if str(item).strip()] if isinstance(synthesis_payload.get("input_fields", []), list) else []
    output_field = str(synthesis_payload.get("output_field", "")).strip()
    compute_expression = str(synthesis_payload.get("compute_expression", "")).strip()
    if not parameterized or not input_fields or not output_field or not compute_expression:
        return None

    inferred_output_field, inferred_input_fields = markdown_symbolic_mapping_from_encounter(encounter)
    if is_generic_synthesis_field_name(output_field) and inferred_output_field:
        output_field = inferred_output_field
    if input_fields and all(is_generic_synthesis_field_name(field) for field in input_fields) and inferred_input_fields:
        original_fields = list(input_fields)
        input_fields = list(inferred_input_fields)
        if len(original_fields) == len(input_fields):
            for old_name, new_name in zip(original_fields, input_fields):
                compute_expression = compute_expression.replace(old_name, new_name)

    heading = str(encounter.get("cluster_heading") or encounter.get("heading") or "").strip()
    title_hint = str(encounter.get("artifact_title_hint", "")).strip()
    title = title_hint or titleize_semantic_unit(heading) or titleize_semantic_unit(output_field)
    semantic_unit = titleize_semantic_unit(title) or title
    question = str(synthesis_payload.get("question", "")).strip()
    if is_generic_synthesis_question(question):
        question = markdown_encounter_question(encounter, output_field=output_field, input_fields=input_fields)
    if not question:
        question = f"How do you calculate {output_field}?"
    aliases = [str(item).strip() for item in synthesis_payload.get("aliases", []) if str(item).strip()] if isinstance(synthesis_payload.get("aliases", []), list) else []
    aliases = ordered_unique(
        aliases
        + markdown_encounter_aliases(encounter)
        + ([str(encounter.get("extracted_form", "")).strip()] if str(encounter.get("extracted_form", "")).strip() else [])
    )
    component_nots = ordered_unique(titleize_semantic_unit(field) for field in input_fields + [output_field] if titleize_semantic_unit(field))
    composed_not = titleize_semantic_unit(title) or title
    sections = [str(item).strip() for item in encounter.get("sections", []) if str(item).strip()] if isinstance(encounter.get("sections", []), list) else []
    why_reusable = str(synthesis_payload.get("why_reusable", "")).strip() or "The parameter mapping can be reused whenever the same named inputs are supplied."
    return {
        "artifact_type": "ability",
        "title": title,
        "semantic_unit": semantic_unit,
        "question": question,
        "related_titles": [],
        "relation_rationale": "",
        "aliases": aliases,
        "component_nots": component_nots,
        "composed_not": composed_not,
        "sections": sections,
        "why_reusable": why_reusable,
        "encounter_id": str(encounter.get("encounter_id", "")).strip(),
        "encounter_kind": str(encounter.get("encounter_kind", "")).strip(),
        "equation_bearing": bool(encounter.get("equation_bearing", False)),
        "parameterized": True,
        "representation": "python_script",
        "scope": f"reuse when later prompts ask to compute {output_field} from {', '.join(input_fields)}",
        "reusability": "broad_reuse",
        "admissibility": "admitted",
        "learning_relation": "extends_parameters",
        "constraints": ["derive only from the supplied encounter"],
        "content": {
            "python_script": "",
            "compute_expression": compute_expression,
            "output_field": output_field,
            "entrypoint": "main",
            "script_language": "python",
            "executor_framework": "python3",
            "dependencies": ["msgspec", "orjson"],
            "input_contract": {field: "number" for field in input_fields},
            "output_contract": {output_field: "number"},
        },
    }


def apply_markdown_batch_relations(
    self,
    artifacts: Sequence[Artifact],
) -> list[Artifact]:
    """
    High Level Purpose:
        In circumstances like finishing one markdown-learning batch after artifact construction, helps with resolving deferred `related_titles` into persisted related-artifact ids across the current and recent learned pool.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `apply_markdown_batch_relations(self=controller, artifacts=[Artifact(id='artifact-bayes', title='Probability / Bayes Update', artifact_type='knowledge', representation='yaml')])`
        Output: [Artifact(id='artifact-bayes', title='Probability / Bayes Update', artifact_type='knowledge', representation='yaml')]

    Args:
        self: Bound controller instance that owns reusable-artifact access and relation-resolution helpers.
        artifacts: Value for `artifacts` used by `apply_markdown_batch_relations`. Expected type: `Sequence[Artifact]`.

    Returns:
        list[Artifact]: Result produced by `apply_markdown_batch_relations`.
    """
    pool: list[Artifact] = []
    seen_ids: set[str] = set()
    recent_store_artifacts = self.artifact_store.load_recent_artifacts(limit=512)
    for artifact in [*recent_store_artifacts, *self.reusable_artifact_candidates(), *list(artifacts)]:
        if artifact.id in seen_ids:
            continue
        seen_ids.add(artifact.id)
        pool.append(artifact)
    changed: list[Artifact] = []
    for artifact in artifacts:
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        related_titles = [
            collapse_ws(str(item).strip())
            for item in content.get("related_titles", [])
            if collapse_ws(str(item).strip())
        ] if isinstance(content.get("related_titles", []), list) else []
        if not related_titles:
            continue
        resolved_ids = self.resolve_related_artifact_ids_from_title_hints(
            related_titles=related_titles,
            pool=pool,
            exclude_artifact_id=artifact.id,
        )
        updated_ids = ordered_unique(list(artifact.related_artifact_ids) + resolved_ids)
        if updated_ids == list(artifact.related_artifact_ids):
            continue
        artifact.related_artifact_ids = updated_ids
        self.state.artifacts[artifact.id] = artifact
        if artifact.id in self.state.learned_artifacts:
            self.state.learned_artifacts[artifact.id] = artifact
        changed.append(artifact)
    return changed


def learn_from_markdown_document(
    self,
    markdown_path: Path,
    *,
    max_artifacts: int = 8,
    source_bundle_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like ingesting one external markdown lesson into the learned corpus, helps with running the full bounded markdown-learning pipeline from parse through persistence and relation resolution.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `learn_from_markdown_document(self=controller, markdown_path=Path('/tmp/physics_force.md'), max_artifacts=3)`
        Output: {'document': {'title': 'Physics Force Lesson', 'source_path': '/tmp/physics_force.md', 'section_count': 4}, 'learned_count': 3, 'run_outcome': 'completed'}

    Args:
        self: Bound controller instance that owns state, proposal orchestration, artifact building, and persistence.
        markdown_path: Value for `markdown_path` used by `learn_from_markdown_document`. Expected type: `Path`.
        max_artifacts: Value for `max_artifacts` used by `learn_from_markdown_document`. Expected type: `int`. Defaults to `8`.

    Returns:
        dict[str, Any]: Result produced by `learn_from_markdown_document`.
    """
    source_path = markdown_path.expanduser().resolve()
    markdown_text = source_path.read_text()
    document: MarkdownDocumentIR = parse_markdown_document_ir(markdown_text, source_path=str(source_path))
    supported_fence_encounters, parsing_failures = supported_fence_learning_records(
        source_path,
        supported_executors=self.supported_executor_frameworks(),
    )
    root = self.state.root()
    root.metadata["markdown_learning_ir"] = document.to_dict()
    root.metadata["markdown_parsing_failures"] = parsing_failures
    self.use_capability(
        "markdown_learning",
        node=root,
        contribution="compile markdown into structural ir and reusable learning artifacts",
    )
    self.state.record_step(
        kind="markdown_ir",
        node_id=root.id,
        intent="Convert external markdown into a formal structural ir before semantic artifact extraction.",
        action="parse markdown document",
        result="markdown ir built",
        evaluation="external source ingestion stayed inspectable and bounded before semantic supplementation",
        payload=document.prompt_view(),
    )

    proposal = self.propose_markdown_learning(root, document, max_artifacts=max_artifacts)
    artifact_payloads = self.proposal_mapping_list(proposal.payload, "artifacts")[:max_artifacts]
    ability_proposal = self.propose_markdown_ability_learning(root, document, max_artifacts=max_artifacts)
    encounter_summaries = self.proposal_mapping_list(ability_proposal.payload, "encounters")
    if not encounter_summaries:
        encounter_summaries = markdown_learning_encounter_view(document)
    else:
        encounter_summaries = merge_markdown_encounter_details(document, encounter_summaries)
    encounter_summaries.extend(supported_fence_encounters)

    ability_payloads: list[dict[str, Any]] = []
    functionalization_proposal: ProposalObject | None = None
    if encounter_summaries:
        functionalization_proposal = self.propose_markdown_functionalization(
            root,
            document,
            encounters=encounter_summaries,
            max_artifacts=max_artifacts,
        )
        ability_payloads = self.proposal_mapping_list(functionalization_proposal.payload, "artifacts")[:max_artifacts]

    valid_ability_payloads: list[dict[str, Any]] = []
    for payload in ability_payloads:
        content = payload.get("content", {}) if isinstance(payload.get("content", {}), Mapping) else {}
        executor_framework = str(content.get("executor_framework", "")).strip().lower()
        python_script = str(content.get("python_script", "")).strip()
        shell_script = str(content.get("shell_script", "")).strip()
        ansible_playbook = str(content.get("ansible_playbook", "")).strip()
        compute_expression = str(content.get("compute_expression", "")).strip()
        if executor_framework == "bash" and shell_script:
            valid_ability_payloads.append(payload)
            continue
        if executor_framework == "ansible" and ansible_playbook:
            valid_ability_payloads.append(payload)
            continue
        if looks_like_placeholder_python_script(python_script) and not compute_expression:
            continue
        valid_ability_payloads.append(payload)
    ability_payloads = valid_ability_payloads

    ability_payload_by_signature: dict[tuple[str, str, tuple[str, ...]], dict[str, Any]] = {}
    for payload in ability_payloads:
        ability_payload_by_signature[_markdown_payload_signature(payload)] = dict(payload)

    for encounter in supported_fence_encounters:
        direct_fence_payload = fence_encounter_ability_payload(encounter)
        if direct_fence_payload is None:
            continue
        ability_payload_by_signature[_markdown_payload_signature(direct_fence_payload)] = direct_fence_payload
        if len(ability_payload_by_signature) >= max_artifacts:
            break

    for encounter in encounter_summaries:
        direct_output_field, direct_input_fields, direct_expression = markdown_direct_expression_mapping(encounter)
        encounter_id = collapse_ws(str(encounter.get("encounter_id", "")).strip())
        if not encounter_id or not direct_output_field or not direct_input_fields or not direct_expression:
            continue
        direct_payload = self.markdown_expression_artifact_payload(
            encounter=encounter,
            synthesis_payload={
                "parameterized": True,
                "input_fields": list(direct_input_fields),
                "output_field": direct_output_field,
                "compute_expression": direct_expression,
                "question": "",
                "aliases": markdown_encounter_aliases(encounter),
                "why_reusable": "The encounter states a direct parameter mapping that should remain callable even when other learned artifacts from the same document are knowledge-shaped.",
            },
        )
        if direct_payload is None:
            continue
        ability_payload_by_signature[_markdown_payload_signature(direct_payload)] = direct_payload
        if len(ability_payload_by_signature) >= max_artifacts:
            break

    ability_payloads = list(ability_payload_by_signature.values())[:max_artifacts]
    if not ability_payloads:
        for encounter in encounter_summaries:
            if not bool(encounter.get("equation_bearing", False)):
                continue
            encounter_kinds = [str(item).strip().lower() for item in encounter.get("candidate_kinds", []) if str(item).strip()] if isinstance(encounter.get("candidate_kinds", []), list) else []
            parameterized_candidate = bool(encounter.get("parameterized", False)) or any(
                kind in {"equation", "template"} for kind in encounter_kinds
            )
            if not parameterized_candidate:
                continue
            synthesis = self.propose_markdown_expression_synthesis(root, document, encounter=encounter)
            synthesized_payload = self.markdown_expression_artifact_payload(
                encounter=encounter,
                synthesis_payload=synthesis.payload,
            )
            if synthesized_payload is not None:
                ability_payloads.append(synthesized_payload)
            if len(ability_payloads) >= max_artifacts:
                break

    artifact_payloads.extend(ability_payloads)
    learned: list[dict[str, Any]] = []
    persisted_reports: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    built_artifacts: list[Artifact] = []

    pending_artifacts: list[Artifact] = []
    for payload in artifact_payloads:
        title_key = collapse_ws(str(payload.get("title", ""))).lower()
        if not title_key or title_key in seen_titles:
            continue
        artifact = self.build_markdown_learning_artifact(
            node=root,
            document=document,
            source_path=source_path,
            payload=payload,
        )
        if artifact is None:
            continue
        seen_titles.add(title_key)
        self.state.learned_artifacts[artifact.id] = artifact
        pending_artifacts.append(artifact)
    for artifact, report, _previous_artifact_id in _persist_markdown_pipeline_artifacts(self, pending_artifacts):
        persisted_reports.append(report)
        built_artifacts.append(artifact)
        learned.append(_learned_markdown_artifact_report(artifact))

    related_updates = self.apply_markdown_batch_relations(built_artifacts)
    for artifact, report, previous_artifact_id in _persist_markdown_pipeline_artifacts(self, related_updates):
        persisted_reports.append(report)
        for item in learned:
            if str(item.get("artifact_id", "")).strip() in {artifact.id, previous_artifact_id}:
                item["related_artifact_ids"] = list(artifact.related_artifact_ids)
                item["artifact_id"] = artifact.id
                break

    learning_context_report: dict[str, Any] = {}
    corpus_root = resolve_learning_context_root(source_path=source_path)
    subject_resolution = _resolved_markdown_learning_subject(
        document,
        source_path,
        corpus_root=corpus_root,
    )
    subject_title = str(subject_resolution.get("canonical_title", ""))
    subject_id = str(subject_resolution.get("subject_id", ""))
    override_payload = (
        dict(source_bundle_override)
        if isinstance(source_bundle_override, Mapping)
        else {}
    )
    override_metadata = (
        dict(override_payload.get("metadata", {}))
        if isinstance(override_payload.get("metadata", {}), Mapping)
        else {}
    )
    source_record = new_learning_source(
        subject_id=subject_id,
        title=collapse_ws(str(override_payload.get("title", ""))) or document.title or source_path.name,
        source_ref=str(override_payload.get("source_ref", "")) or str(source_path),
        source_kind=collapse_ws(str(override_payload.get("source_kind", ""))) or "markdown",
        media_type=collapse_ws(str(override_payload.get("media_type", ""))) or "text/markdown",
        section_count=len(document.sections),
        metadata={
            "declared_subject_id": str(subject_resolution.get("declared_subject_id", "")),
            "declared_subject_title": str(subject_resolution.get("declared_subject_title", "")),
            "matched_existing_subject_id": str(subject_resolution.get("matched_existing_subject_id", "")),
            "resolved_subject_id": subject_id,
            "resolved_canonical_title": subject_title,
            "resolved_aliases": list(subject_resolution.get("aliases", ())),
            "resolved_subject_family": str(subject_resolution.get("subject_family", "")),
            **override_metadata,
        },
    )
    persist_learning_source(corpus_root, source_record, source_text=markdown_text)
    persisted_bundle_paths: tuple[Path, ...] = ()
    if isinstance(override_payload.get("bundle_files", {}), Mapping):
        persisted_bundle_paths = persist_learning_source_bundle_files(
            corpus_root,
            subject_id=subject_id,
            source_id=source_record.source_id,
            bundle_files=override_payload.get("bundle_files", {}),
        )
        if persisted_bundle_paths:
            bundle_root = learning_source_bundle_root(corpus_root, subject_id, source_record.source_id)
            source_record = type(source_record)(
                source_id=source_record.source_id,
                subject_id=source_record.subject_id,
                source_kind=source_record.source_kind,
                title=source_record.title,
                source_ref=source_record.source_ref,
                media_type=source_record.media_type,
                section_count=source_record.section_count,
                body_relpath=source_record.body_relpath,
                metadata={
                    **dict(source_record.metadata),
                    "bundle_root_relpath": str(bundle_root.relative_to(bundle_root.parent.parent)).replace("\\", "/"),
                    "bundle_file_relpaths": [
                        str(path.relative_to(bundle_root.parent.parent)).replace("\\", "/")
                        for path in persisted_bundle_paths
                    ],
                },
            )
            persist_learning_source(corpus_root, source_record, source_text=markdown_text)
    try:
        existing_context = load_learning_context(corpus_root, subject_id)
    except FileNotFoundError:
        existing_context = new_learning_context(
            canonical_title=subject_title,
            subject_id=subject_id,
        )
    existing_units_by_id = {
        collapse_ws(unit.unit_id): unit
        for unit in existing_context.units
        if collapse_ws(unit.unit_id)
    }
    delta = new_learning_delta(
        subject_id=subject_id,
        source_kind=source_record.source_kind,
        rationale=f"Learned reusable units from {source_path.name}.",
    )
    learned_units = tuple(
        _learning_unit_from_markdown_artifact(
            artifact,
            subject_id=subject_id,
            source_id=source_record.source_id,
        )
        for artifact in built_artifacts
    )
    operations: list[LearningDeltaOperation] = []
    for unit in learned_units:
        existing_unit = existing_units_by_id.get(collapse_ws(unit.unit_id))
        if existing_unit is None:
            operations.append(
                LearningDeltaOperation(
                    operation_id=f"op_initiate_{unit.unit_id}",
                    operation_kind="initiate",
                    proposed_unit_ids=(unit.unit_id,),
                    evidence_refs=(source_record.source_id,),
                    rationale=f"Admit learned unit {unit.canonical_title or unit.unit_id} from markdown ingest.",
                )
            )
            continue
        patch: dict[str, Any] = {}
        if str(existing_unit.statement) != str(unit.statement):
            patch["statement"] = str(unit.statement)
        aliases_add = [alias for alias in unit.aliases if alias not in existing_unit.aliases]
        if aliases_add:
            patch["aliases_add"] = aliases_add
        artifact_ids_add = [
            artifact_id
            for artifact_id in unit.linked_artifact_ids
            if artifact_id not in existing_unit.linked_artifact_ids
        ]
        if artifact_ids_add:
            patch["linked_artifact_ids_add"] = artifact_ids_add
        skill_ids_add = [
            skill_id
            for skill_id in unit.linked_skill_ids
            if skill_id not in existing_unit.linked_skill_ids
        ]
        if skill_ids_add:
            patch["linked_skill_ids_add"] = skill_ids_add
        section_ids_add = [
            section_id
            for section_id in unit.linked_section_ids
            if section_id not in existing_unit.linked_section_ids
        ]
        if section_ids_add:
            patch["linked_section_ids_add"] = section_ids_add
        structured_fields_merge = {
            key: value
            for key, value in unit.structured_fields.items()
            if existing_unit.structured_fields.get(key) != value
        }
        if structured_fields_merge:
            patch["structured_fields_merge"] = structured_fields_merge
        metadata_merge = {
            key: value
            for key, value in unit.metadata.items()
            if existing_unit.metadata.get(key) != value
        }
        if metadata_merge:
            patch["metadata_merge"] = metadata_merge
        operations.append(
            LearningDeltaOperation(
                operation_id=f"op_improve_{unit.unit_id}",
                operation_kind="improve",
                target_unit_ids=(unit.unit_id,),
                evidence_refs=(source_record.source_id,),
                patch=patch,
                rationale=f"Improve learned unit {unit.canonical_title or unit.unit_id} from markdown ingest.",
            )
        )
    delta = LearningDelta(
        delta_id=delta.delta_id,
        subject_id=delta.subject_id,
        source_kind=delta.source_kind,
        rationale=delta.rationale,
        evidence_refs=(source_record.source_id,),
        proposed_units=learned_units,
        deprecated_unit_ids=(),
        operations=tuple(operations),
        derived_skill_ids=(),
        document_section_ids=(),
        status="applied" if built_artifacts else "proposed",
        metadata={
            "run_id": self.state.run_id,
            "source_path": str(source_path),
            "learned_artifact_ids": [artifact.id for artifact in built_artifacts],
        },
    )
    persist_learning_delta(corpus_root, delta)
    merged_context = apply_learning_delta(existing_context, delta)
    resolved_subject_family = collapse_ws(str(subject_resolution.get("subject_family", "")))
    if not resolved_subject_family and built_artifacts:
        first_title = collapse_ws(str(built_artifacts[0].title))
        resolved_subject_family = collapse_ws(first_title.split("/", 1)[0]) if "/" in first_title else ""
    merged_context = type(merged_context)(
        subject_id=merged_context.subject_id,
        canonical_title=subject_title or merged_context.canonical_title,
        aliases=tuple(subject_resolution.get("aliases", merged_context.aliases)),
        subject_family=resolved_subject_family or merged_context.subject_family,
        summary=str(subject_resolution.get("summary", "") or merged_context.summary),
        units=merged_context.units,
        linked_source_ids=merged_context.linked_source_ids,
        linked_skill_ids=merged_context.linked_skill_ids,
        linked_document_section_ids=merged_context.linked_document_section_ids,
        applied_delta_ids=merged_context.applied_delta_ids,
        governance_status=merged_context.governance_status,
        metadata=merged_context.metadata,
    )
    context_path = persist_learning_context(corpus_root, merged_context)
    learning_context_report = {
        "corpus_root": str(corpus_root),
        "subject_id": merged_context.subject_id,
        "canonical_title": merged_context.canonical_title,
        "subject_family": merged_context.subject_family,
        "context_path": str(context_path),
        "source_id": source_record.source_id,
        "source_record_path": str((context_path.parent / "sources" / f"{source_record.source_id}.json").resolve()),
        "delta_id": delta.delta_id,
        "delta_path": str((context_path.parent / "deltas" / f"{delta.delta_id}.json").resolve()),
        "unit_count": len(merged_context.units),
        "applied_delta_count": len(merged_context.applied_delta_ids),
        "matched_existing_subject_id": str(subject_resolution.get("matched_existing_subject_id", "")),
        "source_kind": source_record.source_kind,
        "source_bundle_root": (
            str(learning_source_bundle_root(corpus_root, subject_id, source_record.source_id))
            if persisted_bundle_paths
            else ""
        ),
        "source_bundle_file_count": len(persisted_bundle_paths),
    }

    root.metadata["direct_resolution_answer"] = f"Learned {len(learned)} artifacts from {source_path.name}."
    root.metadata["direct_resolution_answer_kind"] = "markdown_learning"
    if learned:
        self.state.status[root.id] = NodeStatus.CLOSED
        self.state.certainty[root.id] = ThreeLevel.HIGH
        self.state.support[root.id] = SupportView(
            direct=["external_markdown_learning"],
            upstream=[],
            score=SupportScore.OK,
        )
        self.state.graph.nodes[root.id].metadata["final_answer"] = root.metadata["direct_resolution_answer"]
        self.state.run_outcome = RunOutcome.COMPLETED
    else:
        self.state.status[root.id] = NodeStatus.INCOMPLETE
        self.state.run_outcome = RunOutcome.INCOMPLETE

    self.state.record_step(
        kind="markdown_learning",
        node_id=root.id,
        intent="Harvest reusable artifacts from an external markdown source under bounded structural control.",
        action="compile markdown ir into admitted learning artifacts",
        result=f"{len(learned)} artifacts learned",
        evaluation="external-source learning produced persisted reusable artifacts without reopening the source as a live task",
        payload={
            "source_path": str(source_path),
            "proposal_id": proposal.id,
            "artifact_ids": [item["artifact_id"] for item in learned],
            "parsing_failures": parsing_failures,
        },
    )
    return {
        "document": {
            "title": document.title,
            "source_path": str(source_path),
            "section_count": len(document.sections),
        },
        "ir": document.prompt_view(),
        "proposal": {
            "proposal_id": proposal.id,
            "source": proposal.source,
            "rationale": proposal.rationale,
        },
        "encounter_proposal": {
            "proposal_id": ability_proposal.id,
            "source": ability_proposal.source,
            "rationale": ability_proposal.rationale,
            "encounters": encounter_summaries,
        },
        "functionalization_proposal": {
            "proposal_id": functionalization_proposal.id if functionalization_proposal is not None else "",
            "source": functionalization_proposal.source if functionalization_proposal is not None else "",
            "rationale": functionalization_proposal.rationale if functionalization_proposal is not None else "",
        },
        "learned_count": len(learned),
        "learned_artifacts": learned,
        "artifact_persistence": persisted_reports,
        "learning_context": learning_context_report,
        "supported_executors": self.supported_executor_frameworks(),
        "parsing_failures": parsing_failures,
        "run_id": self.state.run_id,
        "run_outcome": self.state.run_outcome.value,
        "final_answer": root.metadata.get("direct_resolution_answer"),
    }


def install_markdown_learning_extensions(controller_runtime_module: Any) -> None:
    """Install the optional subject-ingestion methods at an application boundary."""

    controller_runtime_module.markdown_ability_collision_identity = (
        _artifact_semantics.markdown_ability_collision_identity
    )
    extensions = {
        "apply_markdown_batch_relations": apply_markdown_batch_relations,
        "learn_from_markdown_document": learn_from_markdown_document,
        "markdown_expression_artifact_payload": markdown_expression_artifact_payload,
        "build_markdown_knowledge_answer_from_encounter": _artifact_semantics.build_markdown_knowledge_answer_from_encounter,
        "build_markdown_learning_artifact": _artifact_semantics.build_markdown_learning_artifact,
        "propose_markdown_ability_learning": _artifact_semantics.propose_markdown_ability_learning,
        "propose_markdown_expression_synthesis": _artifact_semantics.propose_markdown_expression_synthesis,
        "propose_markdown_functionalization": _artifact_semantics.propose_markdown_functionalization,
        "propose_markdown_learning": _artifact_semantics.propose_markdown_learning,
        "propose_markdown_title_repair": _artifact_semantics.propose_markdown_title_repair,
        "select_markdown_learning_encounter": _artifact_semantics.select_markdown_learning_encounter,
    }
    for name, implementation in extensions.items():
        setattr(controller_runtime_module.BSSCController, name, implementation)


__all__ = [
    "apply_markdown_batch_relations",
    "install_markdown_learning_extensions",
    "learn_from_markdown_document",
    "markdown_expression_artifact_payload",
]
