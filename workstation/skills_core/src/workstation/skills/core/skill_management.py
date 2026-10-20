# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from execution_frameworks import ability_executor_framework
from semantic_text import collapse_ws
from skill_export_projection import (
    batch_skill_export_filename,
    export_skill_bundle_text,
    skill_kind_from_artifact,
)
from skill_lifecycle import skill_lifecycle_from_payload
from skill_schema_io import (
    artifact_from_skill_document,
    load_skill_yaml_payload_documents,
    normalized_skill_bundle_filename_for_source,
    yaml_skill_top_level_document,
)
from side import load_artifact_yaml_documents
from skill_governance import (
    SKILL_SCHEMA_VERSION_V2,
    artifact_skill_declaration,
    evaluate_skill_admission,
    normalize_skill_kind,
    normalize_skill_schema_version,
)
from workstation.foundation.host.governance import (
    workstation_governance_inventory,
    workstation_is_transient_bundle_policy_payload,
)
from workstation.foundation.models import WorkstationSession
from workstation.skills.core.skill_invocation import (
    list_available_workstation_skills,
    resolve_workstation_skill,
    workstation_skill_store,
)


_WORKSTATION_SKILL_SHORTLIST_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "under",
    "what",
    "how",
    "each",
    "only",
    "then",
    "your",
    "their",
    "there",
    "which",
    "using",
    "state",
    "given",
    "explain",
    "write",
}


def _load_workstation_import_payload_documents(source_file: Path) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like workstation skill import from chat, CLI, or markdown-learning flows, helps with accepting both canonical skill bundles and legacy artifact bundles while normalizing everything into portable skill payloads before persistence.

    Reference to Theory:
        Supports the workstation exchange boundary by keeping the persistent skill home skill-facing, while still tolerating artifact-origin export surfaces that can be projected into governed skills.

    Example Input Output:
        Input: `_load_workstation_import_payload_documents(source_file=Path('/tmp/learned.yaml'))`
        Output: [{'schema': 'bssc_skill.v2', 'kind': 'knowledge', 'title': 'Learned Demo Skill'}]

    Args:
        source_file: Value for `source_file` used by `_load_workstation_import_payload_documents`. Expected type: `Path`.

    Returns:
        list[dict[str, Any]]: Result produced by `_load_workstation_import_payload_documents`.
    """
    try:
        return load_skill_yaml_payload_documents(Path(source_file))
    except ValueError as skill_error:
        try:
            artifacts = load_artifact_yaml_documents(Path(source_file))
        except Exception:
            raise skill_error
        projected_bundle = export_skill_bundle_text(artifacts)
        if not projected_bundle.strip():
            raise ValueError(
                "The source file is an artifact bundle, but it does not contain any exportable skills."
            ) from skill_error
        payloads: list[dict[str, Any]] = []
        for document in yaml.safe_load_all(projected_bundle):
            if document in (None, "", [], {}):
                continue
            payloads.append(yaml_skill_top_level_document(document))
        if not payloads:
            raise ValueError(
                "The source file did not yield any portable skill payloads after artifact projection."
            ) from skill_error
        return payloads


def _skill_semantic_bonus(*, prompt_text_casefold: str, prompt_tokens: set[str], title_casefold: str) -> int:
    """
    High Level Purpose:
        In circumstances like workstation prompt routing over imported trial workers, helps with rewarding obvious semantic matches that do not share the same surface words.

    Reference to Theory:
        Supports direct skill composition by keeping the shell close to user intent even when worker titles use a different wording than the prompt.

    Example Input Output:
        Input: `_skill_semantic_bonus(prompt_text_casefold='open google chrome to https://example.com', prompt_tokens={'open', 'google', 'chrome', 'https', 'example', 'com'}, title_casefold='device user capabilities 01 — launch browser at specific url')`
        Output: 6

    Args:
        prompt_text_casefold: Value for `prompt_text_casefold` used by `_skill_semantic_bonus`. Expected type: `str`.
        prompt_tokens: Value for `prompt_tokens` used by `_skill_semantic_bonus`. Expected type: `set[str]`.
        title_casefold: Value for `title_casefold` used by `_skill_semantic_bonus`. Expected type: `str`.

    Returns:
        int: Result produced by `_skill_semantic_bonus`.
    """
    bonus = 0
    browser_tokens = {"browser", "chrome", "safari", "firefox", "brave", "arc", "edge"}
    if (
        {"open", "launch"} & prompt_tokens
        and (browser_tokens & prompt_tokens or "http://" in prompt_text_casefold or "https://" in prompt_text_casefold or "url" in prompt_tokens)
        and ("browser" in title_casefold or "specific url" in title_casefold)
    ):
        bonus += 6
    if (
        {"launch", "open"} & prompt_tokens
        and ("app" in prompt_tokens or "application" in prompt_tokens)
        and "launch application by name" in title_casefold
    ):
        bonus += 5
    if (
        ({"open", "show"} & prompt_tokens and "finder" in prompt_tokens)
        or "reveal" in prompt_tokens
    ) and ("finder" in title_casefold or "reveal file" in title_casefold or "open folder" in title_casefold):
        bonus += 5
    if "terminal" in prompt_tokens and "terminal" in title_casefold:
        bonus += 5
    if "settings" in prompt_tokens and "settings pane" in title_casefold:
        bonus += 5
    if "clipboard" in prompt_tokens and "clipboard" in title_casefold:
        bonus += 5
    if "screenshot" in prompt_tokens and ("screenshot" in title_casefold or "capture" in title_casefold):
        bonus += 5
    if "web" in prompt_tokens and ("search the web" in title_casefold or ("browser" in title_casefold and "search" in title_casefold)):
        bonus += 4
    return bonus


def workstation_skill_catalog_payload(
    *,
    session: WorkstationSession,
    skill_store_attachment_name: str = "skills",
    query: str = "",
    limit: Any = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation discovery-file refresh and skill catalog capability calls, helps with projecting the current persistent workstation skill home into one stable machine-readable payload.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by making the persistent worker inventory explicit and reusable across sessions.

    Example Input Output:
        Input: `workstation_skill_catalog_payload(session=3, query='repo', limit=5)`
        Output: {'skills': [{'title': 'Workstation Repo Search'}], 'query': 'repo', 'total_skill_count': 3, 'returned_skill_count': 1, 'skill_store_attachment': 'skills', 'skill_home': {'store_path': '/tmp/store.sqlite3'}}

    Args:
        session: Value for `session` used by `workstation_skill_catalog_payload`. Expected type: `WorkstationSession`.
        skill_store_attachment_name: Value for `skill_store_attachment_name` used by `workstation_skill_catalog_payload`. Expected type: `str`. Defaults to `'skills'`.
        query: Value for `query` used by `workstation_skill_catalog_payload`. Expected type: `str`. Defaults to `''`.
        limit: Value for `limit` used by `workstation_skill_catalog_payload`. Expected type: `Any`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `workstation_skill_catalog_payload`.
    """
    attachments_by_name = {attachment.name: attachment for attachment in session.attachments}
    skill_store_attachment = attachments_by_name.get(skill_store_attachment_name)
    if skill_store_attachment is None:
        return {
            "skills": [],
            "query": collapse_ws(str(query)),
            "total_skill_count": 0,
            "returned_skill_count": 0,
            "skill_store_attachment": "",
            "skill_exports_attachment": "",
            "skill_imports_attachment": "",
            "skill_home": {},
        }
    metadata = dict(skill_store_attachment.metadata)
    all_skills = list_available_workstation_skills(Path(skill_store_attachment.source))
    normalized_query = collapse_ws(str(query))
    filtered_skills = list(all_skills)
    if normalized_query:
        tokens = [token for token in normalized_query.casefold().split() if token]
        def matches(entry: Mapping[str, Any]) -> bool:
            haystack = " ".join(
                [
                    str(entry.get("title", "")),
                    str(entry.get("kind", "")),
                    str(entry.get("executor_framework", "")),
                    str(entry.get("source_kind", "")),
                ]
            ).casefold()
            return all(token in haystack for token in tokens)
        filtered_skills = [entry for entry in filtered_skills if matches(entry)]
    bounded_limit = None
    try:
        if limit is not None:
            bounded_limit = max(1, int(limit))
    except (TypeError, ValueError):
        bounded_limit = None
    if bounded_limit is not None:
        filtered_skills = filtered_skills[:bounded_limit]
    return {
        "skills": filtered_skills,
        "query": normalized_query,
        "total_skill_count": len(all_skills),
        "returned_skill_count": len(filtered_skills),
        "skill_store_attachment": skill_store_attachment.name,
        "skill_exports_attachment": "skills_exports" if "skills_exports" in attachments_by_name else "",
        "skill_imports_attachment": "skills_imports" if "skills_imports" in attachments_by_name else "",
        "skill_home": {
            "home_path": str(metadata.get("home_path", "")),
            "store_path": str(metadata.get("store_path", skill_store_attachment.source)),
            "exports_path": str(metadata.get("exports_path", "")),
            "imports_path": str(metadata.get("imports_path", "")),
        },
    }


def write_workstation_skill_catalog(root: Path, session: WorkstationSession) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation launch and workstation skill lifecycle changes, helps with rewriting `SKILLS.json` so the session discovery surface reflects the current persistent worker inventory.

    Reference to Theory:
        Supports workstation discovery by keeping the worker catalog explicit and synchronized with the durable workstation skill home.

    Example Input Output:
        Input: `write_workstation_skill_catalog(root=Path('/tmp/ws'), session=3)`
        Output: {'skills': [{'title': 'Workstation Repo Search'}], 'skill_store_attachment': 'skills'}

    Args:
        root: Value for `root` used by `write_workstation_skill_catalog`. Expected type: `Path`.
        session: Value for `session` used by `write_workstation_skill_catalog`. Expected type: `WorkstationSession`.

    Returns:
        dict[str, Any]: Result produced by `write_workstation_skill_catalog`.
    """
    payload = workstation_skill_catalog_payload(session=session)
    (Path(root) / "SKILLS.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def workstation_prompt_skill_shortlist_payload(
    *,
    session: WorkstationSession,
    prompt: str,
    limit: int = 12,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation prompt handling against a large worker inventory, helps with projecting a compact shortlist of the installed skills most likely to be relevant to the current prompt.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by favoring direct worker composition before heavier reasoning or generic tool use.

    Example Input Output:
        Input: `workstation_prompt_skill_shortlist_payload(session=3, prompt='Find where main is implemented in this workspace.', limit=5)`
        Output: {'prompt': 'Find where main is implemented in this workspace.', 'skills': [{'title': 'Workstation Repo Search', 'score': 9}], 'returned_skill_count': 1}

    Args:
        session: Value for `session` used by `workstation_prompt_skill_shortlist_payload`. Expected type: `WorkstationSession`.
        prompt: Value for `prompt` used by `workstation_prompt_skill_shortlist_payload`. Expected type: `str`.
        limit: Value for `limit` used by `workstation_prompt_skill_shortlist_payload`. Expected type: `int`. Defaults to `12`.

    Returns:
        dict[str, Any]: Result produced by `workstation_prompt_skill_shortlist_payload`.
    """
    catalog_payload = workstation_skill_catalog_payload(session=session)
    prompt_text = collapse_ws(str(prompt))
    prompt_text_casefold = prompt_text.casefold()
    tokens = [
        token
        for token in re.findall(r"[a-z0-9_]+", prompt_text_casefold)
        if len(token) > 2 and token not in _WORKSTATION_SKILL_SHORTLIST_STOPWORDS
    ]
    scored: list[dict[str, Any]] = []
    for entry in catalog_payload.get("skills", []):
        if not isinstance(entry, Mapping):
            continue
        title_text = str(entry.get("title", ""))
        title_casefold = title_text.casefold()
        haystack = " ".join(
            [
                title_text,
                str(entry.get("kind", "")),
                str(entry.get("executor_framework", "")),
                str(entry.get("source_kind", "")),
            ]
        ).casefold()
        score = 0
        if title_casefold and title_casefold in prompt_text_casefold:
            score += 100
        for token in tokens:
            if token in title_casefold:
                score += 3
            elif token in haystack:
                score += 1
        prompt_token_set = set(tokens)
        score += _skill_semantic_bonus(
            prompt_text_casefold=prompt_text_casefold,
            prompt_tokens=prompt_token_set,
            title_casefold=title_casefold,
        )
        if prompt_token_set & {"find", "search", "locate", "occurrence", "definition", "heading", "symbol", "implemented"}:
            if "repo search" in title_casefold:
                score += 6
            elif "find" in title_casefold or "search" in title_casefold:
                score += 2
        if score <= 0:
            continue
        scored.append(
            {
                **dict(entry),
                "score": score,
            }
        )
    scored.sort(key=lambda item: (-int(item.get("score", 0)), str(item.get("title", "")).casefold()))
    bounded_limit = max(1, int(limit))
    return {
        "prompt": prompt_text,
        "skills": scored[:bounded_limit],
        "returned_skill_count": min(len(scored), bounded_limit),
        "total_skill_count": len(catalog_payload.get("skills", [])),
    }


def write_workstation_prompt_skill_shortlist(
    root: Path,
    *,
    session: WorkstationSession,
    prompt: str,
    limit: int = 12,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation prompt handling, helps with materializing one prompt-local skill shortlist file so both the host and the model can inspect the likely relevant workers for the current ask.

    Reference to Theory:
        Supports direct workstation skill composition by making prompt-relevant worker discovery explicit instead of hidden in an ambient store.

    Example Input Output:
        Input: `write_workstation_prompt_skill_shortlist(root=Path('/tmp/ws'), session=3, prompt='Find where main is implemented in this workspace.')`
        Output: {'prompt': 'Find where main is implemented in this workspace.', 'skills': [{'title': 'Workstation Repo Search', 'score': 9}]}

    Args:
        root: Value for `root` used by `write_workstation_prompt_skill_shortlist`. Expected type: `Path`.
        session: Value for `session` used by `write_workstation_prompt_skill_shortlist`. Expected type: `WorkstationSession`.
        prompt: Value for `prompt` used by `prompt`. Expected type: `str`.
        limit: Value for `limit` used by `limit`. Expected type: `int`. Defaults to `12`.

    Returns:
        dict[str, Any]: Result produced by `write_workstation_prompt_skill_shortlist`.
    """
    payload = workstation_prompt_skill_shortlist_payload(session=session, prompt=prompt, limit=limit)
    (Path(root) / "TASK_SKILLS.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def import_workstation_skill_file(
    *,
    skill_store_path: Path,
    source_file: Path,
    canonical_export_path: Path,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill lifecycle operations, helps with importing one portable `skill.yaml` file into the persistent workstation skill home and writing its canonical export alongside the durable store.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by reusing governed skill import semantics while binding them to the workstation's persistent worker inventory.

    Example Input Output:
        Input: `import_workstation_skill_file(skill_store_path=Path('/tmp/store.sqlite3'), source_file=Path('/tmp/skill.yaml'), canonical_export_path=Path('/tmp/exports/skill.yaml'))`
        Output: {'status': 'ok', 'imported_count': 1, 'canonical_export_path': '/tmp/exports/skill.yaml'}

    Args:
        skill_store_path: Value for `skill_store_path` used by `import_workstation_skill_file`. Expected type: `Path`.
        source_file: Value for `source_file` used by `source_file`. Expected type: `Path`.
        canonical_export_path: Value for `canonical_export_path` used by `canonical_export_path`. Expected type: `Path`.

    Returns:
        dict[str, Any]: Result produced by `import_workstation_skill_file`.
    """
    started = time.perf_counter()
    store = workstation_skill_store(skill_store_path)
    payloads = _load_workstation_import_payload_documents(Path(source_file))
    policy_payloads: list[dict[str, Any]] = []
    skipped_transient_policy_payloads: list[dict[str, Any]] = []
    approval_payloads: list[dict[str, Any]] = []
    safety_payloads: list[dict[str, Any]] = []
    skill_payloads: list[dict[str, Any]] = []
    for payload in payloads:
        kind = normalize_skill_kind(payload.get("kind", "knowledge"))
        if kind == "policy":
            if workstation_is_transient_bundle_policy_payload(payload):
                skipped_transient_policy_payloads.append(payload)
            else:
                policy_payloads.append(payload)
        elif kind == "approval":
            approval_payloads.append(payload)
        elif kind in {"revocation", "incident"}:
            safety_payloads.append(payload)
        else:
            skill_payloads.append(payload)

    imported_artifacts: list[Any] = []
    imported_records: list[dict[str, Any]] = []
    persist_summaries: dict[str, dict[str, Any]] = {}

    def persist_batch(
        *,
        payload_batch: list[dict[str, Any]],
        run_id: str,
        category: str,
        admission_factory: Any,
    ) -> None:
        if not payload_batch:
            return
        artifacts: list[Any] = []
        for payload in payload_batch:
            artifact = artifact_from_skill_document(payload)
            content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
            admission = admission_factory(payload, artifact, content)
            if admission:
                content["skill_admission"] = admission
                content["skill_lifecycle"] = skill_lifecycle_from_payload(
                    payload,
                    admission_status=str(admission.get("status", "")),
                    policy_record=normalize_skill_kind(payload.get("kind", "")) == "policy",
                    default_updated_at=str(admission.get("evaluated_at", "")),
                )
                artifact.content = content
            artifacts.append(artifact)
        summary = store.persist_artifacts(artifacts, run_id=run_id)
        persist_summaries[category] = {
            "persisted_artifacts": int(summary.get("persisted_artifacts", 0) or 0),
            "unchanged_artifacts": int(summary.get("unchanged_artifacts", 0) or 0),
            "error_artifacts": int(summary.get("error_artifacts", 0) or 0),
            "timings": summary.get("timings", {}),
        }
        reports = list(summary.get("reports", []))
        for artifact, report in zip(artifacts, reports, strict=False):
            imported_artifacts.append(artifact)
            imported_records.append(
                {
                    "artifact_id": str(report.get("artifact_id", getattr(artifact, "id", ""))),
                    "title": str(getattr(artifact, "title", "")),
                    "kind": skill_kind_from_artifact(artifact),
                    "status": str(report.get("status", "")),
                }
            )

    persist_batch(
        payload_batch=policy_payloads,
        run_id="workstation_skill_import:policy",
        category="policy",
        admission_factory=lambda _payload, artifact, content: {
            "status": "admitted",
            "admitted": True,
            "rationale": "Policy artifacts are admitted governance records.",
            "policy_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        },
    )
    persist_batch(
        payload_batch=approval_payloads,
        run_id="workstation_skill_import:approval",
        category="approval",
        admission_factory=lambda _payload, artifact, content: {
            "status": "admitted",
            "admitted": True,
            "rationale": "Approval artifacts are admitted governance records.",
            "approval_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        },
    )
    persist_batch(
        payload_batch=safety_payloads,
        run_id="workstation_skill_import:safety",
        category="safety",
        admission_factory=lambda _payload, _artifact, content: {
            "status": "admitted",
            "admitted": True,
            "rationale": "Safety governance artifacts are admitted governance records.",
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        },
    )

    snapshot = workstation_governance_inventory(store)
    installed_policies = list(snapshot.get("policies", []))
    installed_approvals = list(snapshot.get("approvals", []))

    def skill_admission_factory(payload: dict[str, Any], artifact: Any, content: dict[str, Any]) -> dict[str, Any]:
        schema = normalize_skill_schema_version(content.get("skill_schema", "bssc_skill.v1"))
        if schema != SKILL_SCHEMA_VERSION_V2:
            return {}
        return evaluate_skill_admission(
            artifact_skill_declaration(artifact),
            skill_title=artifact.title,
            kind=skill_kind_from_artifact(artifact),
            executor_framework=ability_executor_framework(
                representation=str(getattr(getattr(artifact, "representation", ""), "value", getattr(artifact, "representation", ""))),
                content=content,
            ),
            skill_content=content,
            policy_artifacts=installed_policies,
            approval_artifacts=installed_approvals,
        )

    persist_batch(
        payload_batch=skill_payloads,
        run_id="workstation_skill_import:skill",
        category="skill",
        admission_factory=skill_admission_factory,
    )

    canonical_export_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_export_path.write_text(export_skill_bundle_text(imported_artifacts))
    return {
        "status": "ok",
        "source_file": str(Path(source_file).resolve()),
        "canonical_export_path": str(canonical_export_path.resolve()),
        "canonical_export_filename": normalized_skill_bundle_filename_for_source(Path(source_file)),
        "imported_count": len(imported_records),
        "skipped_transient_policy_count": len(skipped_transient_policy_payloads),
        "imported": imported_records,
        "persist_summaries": persist_summaries,
        "timings": {
            "total_seconds": round(time.perf_counter() - started, 6),
        },
    }


def export_workstation_skill(
    *,
    skill_store_path: Path,
    skill_title: str,
    destination_path: Path,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill lifecycle operations, helps with exporting one governed worker from the persistent workstation skill home into a canonical portable `skill.yaml`.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by keeping worker exchange explicit and portable outside the workstation session boundary.

    Example Input Output:
        Input: `export_workstation_skill(skill_store_path=Path('/tmp/store.sqlite3'), skill_title='Workstation Greeting', destination_path=Path('/tmp/exports/artifact-skill-123.yaml'))`
        Output: {'status': 'ok', 'skill_title': 'Workstation Greeting', 'destination_path': '/tmp/exports/artifact-skill-123.yaml'}

    Args:
        skill_store_path: Value for `skill_store_path` used by `export_workstation_skill`. Expected type: `Path`.
        skill_title: Value for `skill_title` used by `skill_title`. Expected type: `str`.
        destination_path: Value for `destination_path` used by `destination_path`. Expected type: `Path`.

    Returns:
        dict[str, Any]: Result produced by `export_workstation_skill`.
    """
    normalized_title = str(skill_title).strip()
    if not normalized_title:
        raise ValueError("skill_title is required for workstation skill export.")
    resolved = resolve_workstation_skill(
        skill_title=normalized_title,
        skill_store_path=Path(skill_store_path),
    )
    if resolved is None:
        raise ValueError(f"No workstation skill matches title {normalized_title!r}.")
    artifact, _skill_source = resolved
    canonical_title = str(getattr(artifact, "title", "")).strip() or normalized_title
    destination = Path(destination_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(export_skill_bundle_text([artifact]))
    return {
        "status": "ok",
        "skill_title": canonical_title,
        "destination_path": str(destination),
        "filename": batch_skill_export_filename(artifact),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
