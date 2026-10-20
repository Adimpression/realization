import tempfile
import unittest
from pathlib import Path

from blend_world_store import (
    blend_world_mount_source,
    ensure_blend_world_store,
    ensure_persisted_blend_workstation_world,
    load_blend_world,
    summarize_blend_world,
)


class BlendWorldStoreTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
