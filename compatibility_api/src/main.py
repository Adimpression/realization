# See MODULES.md for the repository module map before editing.
"""Historical import and executable facade for the canonical controller runtime."""
from __future__ import annotations

import sys

from realized_core_engine import controller_runtime as _runtime
from realized_core_engine.controller_entrypoint_binding import (
    register_controller_entrypoint,
)


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


def _install_historical_entry_surface() -> None:
    """Compose the historical aggregate only at the outer application edge."""
    import args as configuration
    from realized_exchange import artifact_yaml as exchange
    from realized_exchange.markdown_learning_pipeline import (
        install_markdown_learning_extensions,
    )

    _runtime.add_controller_feature_toggle_arguments = (
        configuration.add_controller_feature_toggle_arguments
    )
    _runtime.parse_args = configuration.parse_args
    for name in _ENTRY_EXCHANGE_EXPORTS:
        setattr(_runtime, name, getattr(exchange, name))
    install_markdown_learning_extensions(_runtime)


def _run_controller_entrypoint() -> int:
    """Load the optional CLI composition surface only when it is executed."""
    from controller_entrypoints import main as controller_main

    return int(controller_main())


_install_historical_entry_surface()
register_controller_entrypoint(_run_controller_entrypoint)

if __name__ == "__main__":
    raise SystemExit(_runtime.main())

# Preserve historical object identity and patch paths for `import main` callers.
sys.modules[__name__] = _runtime
