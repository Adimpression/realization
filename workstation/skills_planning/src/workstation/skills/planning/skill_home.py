# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from workstation.foundation.host.governance import ensure_workstation_skill_home_policy
from workstation.skills.core.skill_invocation import workstation_skill_store


def workstation_codex_home() -> Path:
    """
    High Level Purpose:
        In circumstances like persistent workstation skill-home resolution, helps with resolving the host-level Codex home directory that should anchor default workstation storage.

    Reference to Theory:
        Supports the workstation shell by giving persistent workstation assets one stable host-owned root instead of scattering them across session-local temporary paths.

    Example Input Output:
        Input: `workstation_codex_home()`
        Output: Path('/Users/example/.workstation')

    Args:
        None.

    Returns:
        Path: Result produced by `workstation_codex_home`.
    """
    configured = str(os.getenv("WORKSTATION_HOME", "")).strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".workstation").resolve()


def resolve_workstation_skill_home(
    *,
    skills_sqlite_path: Path | None = None,
    ensure_exists: bool = True,
) -> dict[str, Path]:
    """
    High Level Purpose:
        In circumstances like workstation launch and persistent skill lifecycle operations, helps with resolving the durable workstation skill-home paths for the governed skill store and canonical export/import directories.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by giving governed workers one persistent home that remains usable both inside and outside workstation sessions.

    Example Input Output:
        Input: `resolve_workstation_skill_home(skills_sqlite_path=None)`
        Output: {'home_path': Path('/Users/example/.workstation/workstation/skills'), 'store_path': Path('/Users/example/.workstation/workstation/skills/store.sqlite3'), 'exports_path': Path('/Users/example/.workstation/workstation/skills/exports'), 'imports_path': Path('/Users/example/.workstation/workstation/skills/imports')}

    Args:
        skills_sqlite_path: Value for `skills_sqlite_path` used by `resolve_workstation_skill_home`. Expected type: `Path | None`. Defaults to `None`.
        ensure_exists: Value for `ensure_exists` used by `resolve_workstation_skill_home`. Expected type: `bool`. Defaults to `True`.

    Returns:
        dict[str, Path]: Result produced by `resolve_workstation_skill_home`.
    """
    if skills_sqlite_path is not None:
        store_path = Path(skills_sqlite_path).expanduser().resolve()
        home_path = store_path.parent.resolve()
    else:
        home_path = (workstation_codex_home() / "workstation" / "skills").resolve()
        store_path = (home_path / "store.sqlite3").resolve()
    exports_path = (home_path / "exports").resolve()
    imports_path = (home_path / "imports").resolve()
    if ensure_exists:
        home_path.mkdir(parents=True, exist_ok=True)
        exports_path.mkdir(parents=True, exist_ok=True)
        imports_path.mkdir(parents=True, exist_ok=True)
        store = workstation_skill_store(store_path)
        store.load_all_artifacts()
        ensure_workstation_skill_home_policy(store)
    return {
        "home_path": home_path,
        "store_path": store_path,
        "exports_path": exports_path,
        "imports_path": imports_path,
    }


def workstation_skill_home_metadata(paths: dict[str, Path]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation discovery-file materialization and capability receipts, helps with projecting resolved workstation skill-home paths into a stable JSON-friendly metadata mapping.

    Reference to Theory:
        Supports the persistent workstation skill-home model by making the durable worker storage layout explicit to both the host and the workstation session.

    Example Input Output:
        Input: `workstation_skill_home_metadata({'home_path': Path('/tmp/home'), 'store_path': Path('/tmp/home/store.sqlite3'), 'exports_path': Path('/tmp/home/exports'), 'imports_path': Path('/tmp/home/imports')})`
        Output: {'home_path': '/tmp/home', 'store_path': '/tmp/home/store.sqlite3', 'exports_path': '/tmp/home/exports', 'imports_path': '/tmp/home/imports'}

    Args:
        paths: Value for `paths` used by `workstation_skill_home_metadata`. Expected type: `dict[str, Path]`.

    Returns:
        dict[str, Any]: Result produced by `workstation_skill_home_metadata`.
    """
    return {
        "home_path": str(paths["home_path"]),
        "store_path": str(paths["store_path"]),
        "exports_path": str(paths["exports_path"]),
        "imports_path": str(paths["imports_path"]),
    }
