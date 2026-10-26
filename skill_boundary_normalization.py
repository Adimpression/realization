# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from applied_theory_types import Artifact
from realized_skill_semantics.normalization import (
    SKILL_NORMALIZATION_VERSION,
    normalize_skill_region_body,
    normalized_skill_normalization_payload,
    reconstruct_skill_region_body,
    synthesized_skill_normalization,
)
from realized_core_governance.records import artifact_skill_declaration
from skill_governance import synthesized_skill_declaration_for_artifact


def synthesized_skill_normalization_for_artifact(
    artifact: Artifact,
) -> dict[str, Any]:
    """Adapt one stored artifact into the portable normalization contract."""
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    declaration = artifact_skill_declaration(
        artifact
    ) or synthesized_skill_declaration_for_artifact(artifact)
    input_contract = (
        dict(content.get("input_contract", {}))
        if isinstance(content.get("input_contract", {}), Mapping)
        else {}
    )
    output_contract = (
        dict(content.get("output_contract", {}))
        if isinstance(content.get("output_contract", {}), Mapping)
        else {}
    )
    input_values = input_contract or (
        dict(declaration.get("inputs", {}))
        if isinstance(declaration.get("inputs", {}), Mapping)
        else {}
    )
    output_values = output_contract or (
        dict(declaration.get("outputs", {}))
        if isinstance(declaration.get("outputs", {}), Mapping)
        else {}
    )
    if not output_values and str(content.get("answer", "")).strip():
        output_values = {"answer": str(content.get("answer", "")).strip()}
    return synthesized_skill_normalization(
        input_values=input_values,
        output_values=output_values,
    )
