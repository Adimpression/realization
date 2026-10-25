# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import platform
import sqlite3
import subprocess
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
RAM_LINK = REPO_ROOT / "ram"
FALLBACK_ROOT = REPO_ROOT / "tmp" / "validation-sqlite"
DEFAULT_VOLUME_NAME = "REALIZED_RAMDISK"


def validation_sqlite_use_ramdisk() -> bool:
    """
    High Level Purpose:
        In circumstances like long-running validation runs that spend time in SQLite persistence and indexing, helps with deciding whether runtime SQLite files should be placed on a RAM-backed store.

    Reference to Theory:
        Supports validation harness performance without changing controller or workstation semantics.

    Example Input Output:
        Input: `validation_sqlite_use_ramdisk()`
        Output: True

    Args:
        None.

    Returns:
        bool: Result produced by `validation_sqlite_use_ramdisk`.
    """
    raw = str(os.getenv("VALIDATION_SQLITE_USE_RAMDISK", "1")).strip().lower()
    return raw not in {"0", "false", "no", "off"}


def validation_sqlite_volume_name() -> str:
    """
    High Level Purpose:
        In circumstances like creating or reusing one repo-local validation RAM disk on macOS, helps with choosing the volume name deterministically.

    Reference to Theory:
        Supports stable validator runtime storage naming without affecting validation semantics.

    Example Input Output:
        Input: `validation_sqlite_volume_name()`
        Output: 'REALIZED_RAMDISK'

    Args:
        None.

    Returns:
        str: Result produced by `validation_sqlite_volume_name`.
    """
    return str(os.getenv("VALIDATION_SQLITE_RAMDISK_VOLUME", DEFAULT_VOLUME_NAME)).strip() or DEFAULT_VOLUME_NAME


def validation_sqlite_ramdisk_size_mb() -> int:
    """
    High Level Purpose:
        In circumstances like allocating one RAM-backed validator SQLite volume, helps with choosing a bounded default size with optional environment override.

    Reference to Theory:
        Supports validation harness performance tuning without changing controller semantics.

    Example Input Output:
        Input: `validation_sqlite_ramdisk_size_mb()`
        Output: 2048

    Args:
        None.

    Returns:
        int: Result produced by `validation_sqlite_ramdisk_size_mb`.
    """
    raw = str(os.getenv("VALIDATION_SQLITE_RAMDISK_SIZE_MB", "2048")).strip()
    try:
        return max(256, int(raw))
    except ValueError:
        return 2048


def ensure_validation_ram_root() -> Path:
    """
    High Level Purpose:
        In circumstances like validation runs that should keep runtime SQLite state off slower disk paths, helps with provisioning the repo-local `ram/` path and returning the SQLite runtime root beneath it.

    Reference to Theory:
        Supports validation harness performance and observability without changing controller semantics.

    Example Input Output:
        Input: `ensure_validation_ram_root()`
        Output: Path('/workspace/realized/ram/sqlite')

    Args:
        None.

    Returns:
        Path: Result produced by `ensure_validation_ram_root`.
    """
    override = str(os.getenv("VALIDATION_SQLITE_ROOT", "")).strip()
    if override:
        root = Path(override).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        return root
    if not validation_sqlite_use_ramdisk():
        FALLBACK_ROOT.mkdir(parents=True, exist_ok=True)
        return FALLBACK_ROOT
    if platform.system() == "Darwin":
        target = _ensure_darwin_ramdisk()
        link = _ensure_ram_link(target)
        sqlite_root = link / "sqlite"
        sqlite_root.mkdir(parents=True, exist_ok=True)
        return sqlite_root
    RAM_LINK.mkdir(parents=True, exist_ok=True)
    sqlite_root = RAM_LINK / "sqlite"
    sqlite_root.mkdir(parents=True, exist_ok=True)
    return sqlite_root


def validation_sqlite_paths(*, report_dir: Path, basename: str) -> tuple[Path, Path]:
    """
    High Level Purpose:
        In circumstances like running validators with fast runtime SQLite but durable archived reports, helps with returning both the runtime database path and the archived report-local copy path.

    Reference to Theory:
        Supports validation harness performance while preserving durable report artifacts.

    Example Input Output:
        Input: `validation_sqlite_paths(report_dir=Path('/tmp/report'), basename='physics.sqlite3')`
        Output: (Path('/workspace/realized/ram/sqlite/report/physics.sqlite3'), Path('/tmp/report/physics.sqlite3'))

    Args:
        report_dir: Value for `report_dir` used by `validation_sqlite_paths`. Expected type: `Path`.
        basename: Value for `basename` used by `validation_sqlite_paths`. Expected type: `str`.

    Returns:
        tuple[Path, Path]: Result produced by `validation_sqlite_paths`.
    """
    archived_path = report_dir / basename
    runtime_root = ensure_validation_ram_root() / report_dir.name
    runtime_root.mkdir(parents=True, exist_ok=True)
    return (runtime_root / basename, archived_path)


def archive_validation_sqlite(runtime_path: Path, archived_path: Path) -> Path:
    """
    High Level Purpose:
        In circumstances like RAM-backed validator execution, helps with copying the finished runtime SQLite database into the durable report directory without changing the database contents.

    Reference to Theory:
        Supports durable validation evidence while leaving controller semantics unchanged.

    Example Input Output:
        Input: `archive_validation_sqlite(Path('/ram/physics.sqlite3'), Path('/tmp/report/physics.sqlite3'))`
        Output: Path('/tmp/report/physics.sqlite3')

    Args:
        runtime_path: Value for `runtime_path` used by `archive_validation_sqlite`. Expected type: `Path`.
        archived_path: Value for `archived_path` used by `archive_validation_sqlite`. Expected type: `Path`.

    Returns:
        Path: Result produced by `archive_validation_sqlite`.
    """
    if not runtime_path.exists():
        return archived_path if archived_path.exists() else runtime_path
    try:
        if runtime_path.resolve() == archived_path.resolve():
            return archived_path
    except FileNotFoundError:
        pass
    archived_path.parent.mkdir(parents=True, exist_ok=True)
    if archived_path.exists():
        archived_path.unlink()
    source = sqlite3.connect(f"file:{runtime_path}?mode=ro", uri=True)
    destination = sqlite3.connect(str(archived_path))
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    return archived_path


def _ensure_darwin_ramdisk() -> Path:
    volume_name = validation_sqlite_volume_name()
    volume_path = Path("/Volumes") / volume_name
    if volume_path.exists():
        return volume_path
    sectors = validation_sqlite_ramdisk_size_mb() * 2048
    attached = subprocess.run(
        ["hdiutil", "attach", "-nomount", f"ram://{sectors}"],
        capture_output=True,
        text=True,
        check=True,
    )
    device = attached.stdout.strip().splitlines()[-1].strip().split()[0]
    subprocess.run(
        ["diskutil", "erasevolume", "HFS+", volume_name, device],
        capture_output=True,
        text=True,
        check=True,
    )
    for _ in range(50):
        if volume_path.exists():
            return volume_path
        time.sleep(0.1)
    raise RuntimeError(f"RAM disk volume {volume_name!r} did not appear at {volume_path}.")


def _ensure_ram_link(target: Path) -> Path:
    if RAM_LINK.is_symlink():
        if RAM_LINK.resolve() == target.resolve():
            return RAM_LINK
        RAM_LINK.unlink()
    elif RAM_LINK.exists():
        if RAM_LINK.is_dir() and not any(RAM_LINK.iterdir()):
            RAM_LINK.rmdir()
        else:
            return RAM_LINK
    RAM_LINK.symlink_to(target)
    return RAM_LINK
