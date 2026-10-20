# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
RUNTIME_TEMP_ROOT_ENV = "BSSC_RUNTIME_TEMP_ROOT"


def preferred_runtime_temp_root() -> Path:
    """
    High Level Purpose:
        In circumstances like replay, cross-boundary execution, and publication compilation, helps with choosing one writable temp root without depending on the platform default temp directory remaining available.

    Reference to Theory:
        Supports stable runtime execution infrastructure without changing controller, workstation, or publication semantics.

    Example Input Output:
        Input: `preferred_runtime_temp_root()`
        Output: Path('/Users/ravindranathakila/service/realized/ram/tmp')

    Args:
        None.

    Returns:
        Path: Result produced by `preferred_runtime_temp_root`.
    """
    override = str(os.getenv(RUNTIME_TEMP_ROOT_ENV, "")).strip()
    candidates = []
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend(
        [
            REPO_ROOT / "ram" / "tmp",
            REPO_ROOT / "tmp" / "runtime",
        ]
    )
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
        except Exception:
            continue
        if os.access(candidate, os.W_OK | os.X_OK):
            return candidate
    return REPO_ROOT


def runtime_temporary_directory(*, prefix: str) -> tempfile.TemporaryDirectory[str]:
    """
    High Level Purpose:
        In circumstances like boundary execution and validation helpers, helps with allocating a temporary directory under the preferred runtime temp root.

    Reference to Theory:
        Supports stable runtime execution infrastructure without changing controller or validator semantics.

    Example Input Output:
        Input: `runtime_temporary_directory(prefix='bssc-demo-')`
        Output: TemporaryDirectory('/Users/ravindranathakila/service/realized/ram/tmp/bssc-demo-abc123')

    Args:
        prefix: Value for `prefix` used by `runtime_temporary_directory`. Expected type: `str`.

    Returns:
        tempfile.TemporaryDirectory[str]: Result produced by `runtime_temporary_directory`.
    """
    return tempfile.TemporaryDirectory(prefix=prefix, dir=str(preferred_runtime_temp_root()))


def runtime_mkdtemp(*, prefix: str) -> str:
    """
    High Level Purpose:
        In circumstances like replay helpers that need one materialized directory path, helps with creating the directory under the preferred runtime temp root.

    Reference to Theory:
        Supports stable runtime execution infrastructure without changing controller or replay semantics.

    Example Input Output:
        Input: `runtime_mkdtemp(prefix='bssc-replay-')`
        Output: '/Users/ravindranathakila/service/realized/ram/tmp/bssc-replay-abc123'

    Args:
        prefix: Value for `prefix` used by `runtime_mkdtemp`. Expected type: `str`.

    Returns:
        str: Result produced by `runtime_mkdtemp`.
    """
    return tempfile.mkdtemp(prefix=prefix, dir=str(preferred_runtime_temp_root()))
