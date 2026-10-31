import json
import tempfile
import unittest
from pathlib import Path

from realized_blend_application.worlds import BlendWorld, ensure_blend_workstation_world


class BlendWorldTests(unittest.TestCase):
    def test_ensure_blend_workstation_world_materializes_shared_mounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workspace = tmp / "project"
            workspace.mkdir(parents=True, exist_ok=True)
            world_root = tmp / "world"
            world = ensure_blend_workstation_world(root_path=world_root, workspace_path=workspace)
            self.assertTrue(world.world_id.startswith("bworld_"))
            self.assertEqual(world.root(), world_root.resolve())
            self.assertEqual(
                {item.name for item in world.mounts},
                {"main", "scratch", "output"},
            )
            self.assertTrue((world_root / "scratch").exists())
            self.assertTrue((world_root / "output").exists())
            self.assertTrue((world_root / "BLEND_WORLD.json").exists())

    def test_ensure_blend_workstation_world_reuses_existing_world(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workspace = tmp / "project"
            workspace.mkdir(parents=True, exist_ok=True)
            world_root = tmp / "world"
            first = ensure_blend_workstation_world(root_path=world_root, workspace_path=workspace)
            second = ensure_blend_workstation_world(root_path=world_root, workspace_path=workspace)
            self.assertEqual(second.world_id, first.world_id)
            payload = json.loads((world_root / "BLEND_WORLD.json").read_text())
            self.assertEqual(BlendWorld.from_dict(payload).world_id, first.world_id)


if __name__ == "__main__":
    unittest.main()
