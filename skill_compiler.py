# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from applied_theory_types import Artifact, json_safe
from skill_ir import canonical_skill_ir_from_artifact
from skill_schema_io import artifact_from_skill_document


def _normalization_leaf_counts(normalization: Mapping[str, Any]) -> dict[str, int]:
    regions = dict(normalization.get("regions", {})) if isinstance(normalization.get("regions", {}), Mapping) else {}
    counts: dict[str, int] = {}
    for region_name, region_payload in regions.items():
        if not isinstance(region_payload, Mapping):
            continue
        leaves = region_payload.get("leaves", [])
        counts[str(region_name)] = len(leaves) if isinstance(leaves, list) else 0
    return counts


def _compiler_warnings_for_ir(ir: Mapping[str, Any]) -> list[str]:
    hosting = dict(ir.get("hosting_metadata", {})) if isinstance(ir.get("hosting_metadata", {}), Mapping) else {}
    executor_framework = str(hosting.get("executor_framework", "")).strip()
    warnings: list[str] = []
    if executor_framework in {"python3", "bash", "ansible"}:
        warnings.append(
            f"Executor framework {executor_framework} remains a compatibility-tier hosted runtime rather than the preferred wasm_wasi public-hosted tier."
        )
    if executor_framework == "wasm_wasi":
        warnings.append("Executor framework wasm_wasi is compatible with the preferred public hosted tier.")
    normalization = dict(ir.get("normalization", {})) if isinstance(ir.get("normalization", {}), Mapping) else {}
    leaf_counts = _normalization_leaf_counts(normalization)
    if not leaf_counts:
        warnings.append("No canonical boundary normalization metadata was available; conservative synthesis was used.")
    if not dict(ir.get("family", {})) and not list(ir.get("aliases", [])):
        warnings.append("No explicit family or alias metadata is available beyond the canonical title.")
    return warnings


@dataclass(frozen=True)
class CompiledSkillDocument:
    artifact: Artifact
    canonical_ir: dict[str, Any]
    analysis: dict[str, Any]
    warnings: list[str]
    source_kind: str = "portable_skill_document"

    def summary(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like governed installation and tests, helps with projecting one compiled skill document into a compact compiler summary without exposing the full executable body.

        Reference to Theory:
            Supports the staged skill compiler plan by surfacing what the compiler learned while leaving artifact persistence anchored in the existing store envelope.

        Example Input Output:
            Input: `compiled.summary()`
            Output: {'schema': 'bssc_skill.v1', 'kind': 'ability', 'executor_framework': 'python3'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `summary`.
        """
        return {
            "source_kind": self.source_kind,
            "schema": str(self.canonical_ir.get("schema", "")),
            "kind": str(self.canonical_ir.get("kind", "")),
            "executor_framework": str(self.analysis.get("executor_framework", "")),
            "representation": str(self.analysis.get("representation", "")),
            "family": dict(self.canonical_ir.get("family", {})) if isinstance(self.canonical_ir.get("family", {}), Mapping) else {},
            "alias_count": len(self.canonical_ir.get("aliases", [])) if isinstance(self.canonical_ir.get("aliases", []), list) else 0,
            "compatibility_formats": [
                str(item.get("format", ""))
                for item in list(self.canonical_ir.get("compatibility", {}).get("adapters", []))
                if isinstance(item, Mapping) and str(item.get("format", "")).strip()
            ]
            if isinstance(self.canonical_ir.get("compatibility", {}), Mapping)
            else [],
            "normalized_regions": list(self.analysis.get("normalized_regions", [])),
            "normalization_leaf_counts": dict(self.analysis.get("normalization_leaf_counts", {}))
            if isinstance(self.analysis.get("normalization_leaf_counts", {}), Mapping)
            else {},
            "warnings": list(self.warnings),
        }


def compile_skill_document(
    payload: Mapping[str, Any],
    *,
    source_kind: str = "portable_skill_document",
) -> CompiledSkillDocument:
    """
    High Level Purpose:
        In circumstances like governed installation of portable skill documents, helps with routing one skill payload through an explicit compiler seam that emits artifact, canonical IR, and bounded analysis.

    Reference to Theory:
        Supports the staged skill compiler plan by making portable-skill ingestion compilation explicit while preserving the current artifact-centered persistence model.

    Example Input Output:
        Input: `compile_skill_document({'schema': 'bssc_skill.v1', 'kind': 'knowledge', 'title': 'What Is Force?', 'answer': 'F = m * a'})`
        Output: CompiledSkillDocument(artifact=Artifact(...), canonical_ir={'schema': 'bssc_skill.v1'}, analysis={'kind': 'knowledge'})

    Args:
        payload: Value for `payload` used by `compile_skill_document`. Expected type: `Mapping[str, Any]`.
        source_kind: Value for `source_kind` used by `compile_skill_document`. Expected type: `str`. Defaults to `'portable_skill_document'`.

    Returns:
        CompiledSkillDocument: Result produced by `compile_skill_document`.
    """
    artifact = artifact_from_skill_document(payload)
    canonical_ir = canonical_skill_ir_from_artifact(artifact).to_dict()
    normalization = dict(canonical_ir.get("normalization", {})) if isinstance(canonical_ir.get("normalization", {}), Mapping) else {}
    analysis = {
        "kind": str(canonical_ir.get("kind", "")),
        "schema": str(canonical_ir.get("schema", "")),
        "executor_framework": str(canonical_ir.get("hosting_metadata", {}).get("executor_framework", "")),
        "representation": str(canonical_ir.get("hosting_metadata", {}).get("representation", "")),
        "normalized_regions": sorted(
            str(region_name)
            for region_name in dict(normalization.get("regions", {})).keys()
            if str(region_name).strip()
        )
        if isinstance(normalization.get("regions", {}), Mapping)
        else [],
        "normalization_leaf_counts": _normalization_leaf_counts(normalization),
    }
    warnings = _compiler_warnings_for_ir(canonical_ir)
    return CompiledSkillDocument(
        artifact=artifact,
        canonical_ir=canonical_ir,
        analysis=analysis,
        warnings=warnings,
        source_kind=str(source_kind),
    )


def compiled_skill_summary_from_artifact(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like reporting over already-hydrated artifacts, helps with recovering the same compact compiler summary shape used during portable skill compilation.

        Reference to Theory:
            Supports the staged compiler plan by letting later callers surface canonical-skill analysis without re-running import or changing persistence semantics.

        Example Input Output:
            Input: `compiled_skill_summary_from_artifact(artifact)`
            Output: {'schema': 'bssc_skill.v1', 'kind': 'ability'}

        Args:
            artifact: Value for `artifact` used by `compiled_skill_summary_from_artifact`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `compiled_skill_summary_from_artifact`.
        """
    canonical_ir = canonical_skill_ir_from_artifact(artifact).to_dict()
    normalization = dict(canonical_ir.get("normalization", {})) if isinstance(canonical_ir.get("normalization", {}), Mapping) else {}
    compiled = CompiledSkillDocument(
        artifact=artifact,
        canonical_ir=canonical_ir,
        analysis={
            "kind": str(canonical_ir.get("kind", "")),
            "schema": str(canonical_ir.get("schema", "")),
            "executor_framework": str(canonical_ir.get("hosting_metadata", {}).get("executor_framework", "")),
            "representation": str(canonical_ir.get("hosting_metadata", {}).get("representation", "")),
            "normalized_regions": sorted(
                str(region_name)
                for region_name in dict(normalization.get("regions", {})).keys()
                if str(region_name).strip()
            )
            if isinstance(normalization.get("regions", {}), Mapping)
            else [],
            "normalization_leaf_counts": _normalization_leaf_counts(normalization),
        },
        warnings=_compiler_warnings_for_ir(canonical_ir),
    )
    return json_safe(compiled.summary())
