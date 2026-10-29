"""Entry-layer exchange adapter consumed through the workstation contract."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

from realized_exchange.artifact_yaml import load_artifact_yaml_documents
from realized_exchange.learning_context_skills import (
    materialize_learning_context_skill_projections,
)
from realized_exchange.skill_export import (
    batch_skill_export_filename,
    export_skill_bundle_text,
)
from realized_exchange.skill_schema import (
    artifact_from_skill_document,
    load_skill_yaml_payload_documents,
    normalized_skill_bundle_filename_for_source,
    yaml_skill_top_level_document,
)


class RealizedSkillExchangeProvider:
    """Translate skill representations without deciding their governance."""

    def artifact_from_skill_document(self, document: Any) -> Any:
        return artifact_from_skill_document(document)

    def load_import_payload_documents(self, source_file: Path) -> list[dict[str, Any]]:
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

    def export_skill_bundle_text(self, artifacts: Iterable[Any]) -> str:
        return export_skill_bundle_text(artifacts)

    def normalized_skill_bundle_filename_for_source(self, path: Path) -> str:
        return normalized_skill_bundle_filename_for_source(Path(path))

    def batch_skill_export_filename(self, artifact: Any) -> str:
        return batch_skill_export_filename(artifact)

    def materialize_learning_context_skills(
        self,
        root_path: Path,
        context: Any,
    ) -> tuple[dict[str, Any], ...]:
        return materialize_learning_context_skill_projections(
            Path(root_path),
            context,
        )


__all__ = ["RealizedSkillExchangeProvider"]
