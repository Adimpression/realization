import json
import tempfile
import unittest
from pathlib import Path

from realized_blend.ports import BlendWorldRepository
from realized_blend.worlds import BlendWorld, BlendWorldMount
from realized_blend_application.world_store import (
    JsonBlendWorldRepository,
    blend_world_mount_source,
    ensure_blend_world_store,
    ensure_persisted_blend_workstation_world,
    load_blend_world,
    persist_blend_world,
    summarize_blend_world,
)


class BlendWorldStoreTests(unittest.TestCase):
    def test_json_repository_satisfies_neutral_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsInstance(
                JsonBlendWorldRepository(Path(tmpdir)),
                BlendWorldRepository,
            )

    def test_ensure_blend_world_store_materializes_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = ensure_blend_world_store(Path(tmpdir) / "world")
            self.assertTrue(paths["root"].exists())
            self.assertTrue(paths["scratch"].exists())
            self.assertTrue(paths["output"].exists())
            self.assertEqual(paths["world"].name, "BLEND_WORLD.json")

    def test_load_and_summarize_persisted_blend_world(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workspace = tmp / "project"
            workspace.mkdir(parents=True, exist_ok=True)
            world_root = tmp / "world"
            first = ensure_persisted_blend_workstation_world(root_path=world_root, workspace_path=workspace)
            loaded = load_blend_world(world_root)
            summary = summarize_blend_world(loaded)
            self.assertEqual(loaded.world_id, first.world_id)
            self.assertEqual(summary["world_id"], first.world_id)
            self.assertEqual(summary["workspace_name"], "main")
            self.assertEqual(summary["mount_names"], ["main", "scratch", "output"])
            self.assertEqual(blend_world_mount_source(loaded, "scratch"), (world_root / "scratch").resolve())

    def test_compatibility_functions_and_repository_preserve_world_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "world"
            world = BlendWorld(
                world_id="world-fixed",
                root_path=str(root.resolve()),
                created_at="2026-10-27T00:00:00+00:00",
                mounts=(
                    BlendWorldMount(
                        name="main",
                        kind="workspace",
                        source=str((Path(tmpdir) / "workspace").resolve()),
                        access_mode="read_write",
                        mount_path="/world/mounts/main",
                    ),
                ),
                metadata={"source_kind": "test"},
            )

            wrapper_path = persist_blend_world(world)
            wrapper_bytes = wrapper_path.read_bytes()
            repository = JsonBlendWorldRepository(root)
            repository_ref = repository.persist(world)

            self.assertEqual(str(wrapper_path), repository_ref)
            self.assertEqual(wrapper_bytes, Path(repository_ref).read_bytes())
            self.assertEqual(world, repository.load())

    def test_missing_and_malformed_world_preserve_historical_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = JsonBlendWorldRepository(Path(tmpdir) / "world")

            self.assertFalse(repository.exists())
            with self.assertRaises(FileNotFoundError):
                repository.load()

            world_path = repository.ensure()["world"]
            world_path.write_text("{not-json", encoding="utf-8")
            self.assertTrue(repository.exists())
            with self.assertRaises(json.JSONDecodeError):
                repository.load()

    def test_workstation_world_materialization_accepts_injected_repository(self) -> None:
        class MemoryRepository:
            def __init__(self) -> None:
                self.world = None

            def exists(self) -> bool:
                return self.world is not None

            def load(self):
                if self.world is None:
                    raise FileNotFoundError
                return self.world

            def persist(self, world) -> str:
                self.world = world
                return "memory://blend-world"

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "world"
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            repository = MemoryRepository()

            first = ensure_persisted_blend_workstation_world(
                root_path=root,
                workspace_path=workspace,
                repository=repository,
            )
            second = ensure_persisted_blend_workstation_world(
                root_path=root,
                workspace_path=workspace,
                repository=repository,
            )

            self.assertIsInstance(repository, BlendWorldRepository)
            self.assertIs(first, repository.world)
            self.assertIs(second, first)
            self.assertFalse((root / "BLEND_WORLD.json").exists())


if __name__ == "__main__":
    unittest.main()
