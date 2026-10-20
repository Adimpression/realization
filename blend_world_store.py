# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from blend_world_models import BlendWorld, BlendWorldMount
from semantic_text import collapse_ws


def ensure_blend_world_store(root_path: Path) -> dict[str, Path]:
    root = Path(root_path).expanduser().resolve()
    scratch = root / "scratch"
    output = root / "output"
    world_file = root / "BLEND_WORLD.json"
    root.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    return {
        "root": root,
        "scratch": scratch,
        "output": output,
        "world": world_file,
    }


def load_blend_world(root_path: Path) -> BlendWorld:
    paths = ensure_blend_world_store(root_path)
    payload = json.loads(paths["world"].read_text())
    return BlendWorld.from_dict(payload)


def ensure_persisted_blend_workstation_world(
    *,
    root_path: Path,
    workspace_path: Path,
    workspace_name: str = "main",
) -> BlendWorld:
    root = Path(root_path).expanduser().resolve()
    workspace = Path(workspace_path).expanduser().resolve()
    paths = ensure_blend_world_store(root)
    if paths["world"].exists():
        return load_blend_world(root)
    world = BlendWorld(
        world_id=f"bworld_{uuid.uuid4().hex[:12]}",
        root_path=str(root),
        created_at=datetime.now(timezone.utc).isoformat(),
        mounts=(
            BlendWorldMount(
                name=workspace_name,
                kind="workspace",
                source=str(workspace),
                access_mode="read_write",
                mount_path=f"/world/mounts/{workspace_name}",
            ),
            BlendWorldMount(
                name="scratch",
                kind="scratch",
                source=str(paths["scratch"].resolve()),
                access_mode="read_write",
                mount_path="/world/scratch",
            ),
            BlendWorldMount(
                name="output",
                kind="output",
                source=str(paths["output"].resolve()),
                access_mode="read_write",
                mount_path="/world/output",
            ),
        ),
        metadata={
            "source_kind": "workstation_world",
            "workspace_name": workspace_name,
            "workspace_path": str(workspace),
        },
    )
    persist_blend_world(world)
    return world


def persist_blend_world(world: BlendWorld) -> Path:
    paths = ensure_blend_world_store(Path(world.root_path))
    paths["world"].write_text(json.dumps(world.to_dict(), indent=2, sort_keys=True) + "\n")
    return paths["world"]


def blend_world_mounts_by_name(world: BlendWorld) -> dict[str, BlendWorldMount]:
    mounts: dict[str, BlendWorldMount] = {}
    for mount in world.mounts:
        name = collapse_ws(mount.name)
        if name:
            mounts[name] = mount
    return mounts


def blend_world_mount_source(world: BlendWorld | None, mount_name: str) -> Path | None:
    if world is None:
        return None
    mount = blend_world_mounts_by_name(world).get(collapse_ws(mount_name))
    if mount is None:
        return None
    return Path(mount.source).expanduser().resolve()


def summarize_blend_world(world: BlendWorld) -> dict[str, Any]:
    mount_names = tuple(
        collapse_ws(mount.name)
        for mount in world.mounts
        if collapse_ws(mount.name)
    )
    return {
        "world_id": world.world_id,
        "root_path": world.root_path,
        "created_at": world.created_at,
        "mount_count": len(mount_names),
        "mount_names": list(mount_names),
        "workspace_name": str(world.metadata.get("workspace_name", "")),
        "workspace_path": str(world.metadata.get("workspace_path", "")),
    }
