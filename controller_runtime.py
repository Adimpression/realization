"""Compatibility alias and subject-composition seam for the controller runtime."""

from __future__ import annotations

import sys

from realized_core_engine import controller_runtime as _canonical


_ENTRY_EXCHANGE_EXPORTS = (
    "artifact_export_bundle_text",
    "artifact_export_description",
    "artifact_export_document",
    "artifact_export_in_entries",
    "artifact_export_metadata",
    "artifact_export_out_entries",
    "artifact_export_yaml",
    "artifact_from_yaml_document",
    "artifact_structured_learning_from_import",
    "batch_artifact_export_filename",
    "export_artifact_text",
    "load_artifact_yaml",
    "load_artifact_yaml_documents",
    "load_batch_list",
    "normalized_bundle_filename_for_source",
    "resolve_export_artifact_ids",
    "resolve_import_artifact_files",
    "yaml_top_level_declaration",
)


def _install_entry_exchange_compatibility() -> None:
    """Preserve the historical root surface without packaging entry adapters."""
    import args as configuration
    from realized_exchange import artifact_yaml as exchange

    _canonical.add_controller_feature_toggle_arguments = (
        configuration.add_controller_feature_toggle_arguments
    )
    _canonical.parse_args = configuration.parse_args
    for name in _ENTRY_EXCHANGE_EXPORTS:
        setattr(_canonical, name, getattr(exchange, name))


def _install_subject_learning_extensions() -> None:
    """Attach optional subject ingestion without coupling the engine wheel to it."""
    try:
        from realized_exchange.markdown_learning_pipeline import (
            install_markdown_learning_extensions,
        )
    except ModuleNotFoundError:
        return
    install_markdown_learning_extensions(_canonical)


_install_entry_exchange_compatibility()
_install_subject_learning_extensions()
sys.modules[__name__] = _canonical
