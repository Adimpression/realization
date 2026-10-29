# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from typing import Any

from realized_core_semantics.semantic_text import collapse_ws, ordered_unique, titleize_semantic_unit
from workstation.subject.core.learning_context import (
    learning_context_projected_skill_ids,
)


def _knowledge_skill_declaration(*, context: Any, unit: Any) -> dict[str, Any]:
    return {
        "intent": f"Provide subject knowledge for {context.canonical_title}: {unit.canonical_title}.",
        "inputs": {},
        "outputs": {"answer": "knowledge answer"},
        "authorities_requested": [],
        "authority_bounds": {},
        "data_classes_touched": ["public"],
        "side_effects": [],
        "persistence_behavior": "none",
        "invocation_rights": ["direct_user_invocation"],
        "composition_rights": [],
        "escalation_rights": [],
        "approval_requirements": ["automatic"],
        "risk_tier": "tier1_bounded_transform",
    }


def _ability_skill_declaration(
    *,
    context: Any,
    unit: Any,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
) -> dict[str, Any]:
    return {
        "intent": f"Execute derived ability for {context.canonical_title}: {unit.canonical_title}.",
        "inputs": dict(inputs),
        "outputs": dict(outputs),
        "authorities_requested": ["execute"],
        "authority_bounds": {
            "execute": {
                "scope": "local_executor",
                "target": "derived_learning_context_skill",
                "context": "explicit_user_prompt",
                "duration": "single_invocation",
                "triggering_conditions": ["user invokes derived learning-context skill"],
                "approval_class": "automatic",
            }
        },
        "data_classes_touched": ["public"],
        "side_effects": ["local executor invocation"],
        "persistence_behavior": "none",
        "invocation_rights": ["direct_user_invocation"],
        "composition_rights": [],
        "escalation_rights": [],
        "approval_requirements": ["automatic"],
        "risk_tier": "tier1_bounded_transform",
    }


def _knowledge_skill_document_from_unit(
    *,
    context: Any,
    unit: Any,
    skill_id: str,
) -> dict[str, Any]:
    skill_title = f"{context.canonical_title} / {unit.canonical_title} / {skill_id}"
    return {
        "schema": "bssc_skill.v2",
        "kind": "knowledge",
        "title": skill_title,
        "description": f"Derived skill projection for {context.canonical_title} unit {unit.canonical_title}.",
        "question": unit.canonical_title or skill_id,
        "answer": unit.statement or unit.canonical_title or skill_id,
        "declaration": _knowledge_skill_declaration(context=context, unit=unit),
        "aliases": ordered_unique([unit.canonical_title, *unit.aliases, skill_id]),
        "family": {
            "label": context.canonical_title,
            "key": context.subject_id,
            "variant": unit.canonical_title or titleize_semantic_unit(skill_id),
        },
        "governance": {
            "scope": f"learning_context:{context.subject_id}",
            "related_titles": ordered_unique([context.canonical_title, unit.canonical_title]),
            "provenance": list(unit.provenance_refs),
        },
        "compatibility": {
            "adapters": [
                {
                    "format": "learning_context_projection",
                    "version": "v1",
                    "subject_id": context.subject_id,
                    "unit_id": unit.unit_id,
                    "skill_id": skill_id,
                }
            ]
        },
    }


def projected_skill_document_from_learning_unit(
    *,
    context: Any,
    unit: Any,
    skill_id: str,
) -> dict[str, Any] | None:
    if unit.status != "admitted":
        return None
    if unit.unit_kind == "ability":
        structured = dict(unit.structured_fields)
        executor = collapse_ws(str(structured.get("executor", "")))
        if executor and any(collapse_ws(str(structured.get(key, ""))) for key in ("python", "shell", "ansible", "wasm")):
            skill_title = f"{context.canonical_title} / {unit.canonical_title} / {skill_id}"
            payload: dict[str, Any] = {
                "schema": "bssc_skill.v2",
                "kind": "ability",
                "title": skill_title,
                "description": f"Derived executable skill projection for {context.canonical_title} unit {unit.canonical_title}.",
                "executor": executor,
                "inputs": dict(structured.get("inputs", {})) if isinstance(structured.get("inputs", {}), dict) else {},
                "outputs": dict(structured.get("outputs", {})) if isinstance(structured.get("outputs", {}), dict) else {},
                "declaration": _ability_skill_declaration(
                    context=context,
                    unit=unit,
                    inputs=dict(structured.get("inputs", {})) if isinstance(structured.get("inputs", {}), dict) else {},
                    outputs=dict(structured.get("outputs", {})) if isinstance(structured.get("outputs", {}), dict) else {},
                ),
                "aliases": ordered_unique([unit.canonical_title, *unit.aliases, skill_id]),
                "family": {
                    "label": context.canonical_title,
                    "key": context.subject_id,
                    "variant": unit.canonical_title or titleize_semantic_unit(skill_id),
                },
                "governance": {
                    "scope": f"learning_context:{context.subject_id}",
                    "related_titles": ordered_unique([context.canonical_title, unit.canonical_title]),
                    "provenance": list(unit.provenance_refs),
                },
                "compatibility": {
                    "adapters": [
                        {
                            "format": "learning_context_projection",
                            "version": "v1",
                            "subject_id": context.subject_id,
                            "unit_id": unit.unit_id,
                            "skill_id": skill_id,
                        }
                    ]
                },
            }
            for key in ("python", "shell", "ansible", "wasm"):
                value = collapse_ws(str(structured.get(key, "")))
                if value:
                    payload[key] = value
            return payload
        return None
    return _knowledge_skill_document_from_unit(context=context, unit=unit, skill_id=skill_id)


__all__ = [
    "learning_context_projected_skill_ids",
    "projected_skill_document_from_learning_unit",
]
