import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from blend_session import BlendSession, blend_session_from_workstation_session
from workstation.foundation.models import WorkstationAttachment, WorkstationSession
from workstation.runtime.core.session import launch_workstation_session, persist_workstation_session


class BlendSessionTests(unittest.TestCase):
    def test_blend_session_projection_from_workstation_session(self) -> None:
        session = WorkstationSession(
            session_id="ws_demo",
            root_path="/tmp/ws-demo",
            created_at="2026-04-05T00:00:00+00:00",
            attachments=(
                WorkstationAttachment(
                    name="session",
                    kind="session_root",
                    source="/tmp/ws-demo",
                    access_mode="read_write",
                    mount_path="/workstation/session",
                ),
                WorkstationAttachment(
                    name="main",
                    kind="workspace",
                    source="/tmp/project",
                    access_mode="read_write",
                    mount_path="/workstation/mounts/main",
                ),
                WorkstationAttachment(
                    name="output",
                    kind="output",
                    source="/tmp/output",
                    access_mode="write",
                    mount_path="/workstation/output",
                ),
                WorkstationAttachment(
                    name="skills",
                    kind="skill_store",
                    source="/tmp/skills.sqlite3",
                    access_mode="read_write",
                    mount_path="/workstation/skills/store.sqlite3",
                ),
                WorkstationAttachment(
                    name="openai",
                    kind="secret_ref",
                    source="host:OPENAI_API_KEY",
                    access_mode="indirect",
                    mount_path="/workstation/secrets/openai",
                ),
            ),
            allowed_capabilities=("ws.repo.tree", "ws.skill.invoke", "ws.skill.compose"),
            openai_profile="openai_default",
            openai_env_var="OPENAI_API_KEY",
            initial_task="Inspect the project.",
        )
        blend_session = blend_session_from_workstation_session(session)
        self.assertEqual(blend_session.actor_kind, "ai_chat")
        self.assertEqual(blend_session.projection_kind, "ai_chat")
        self.assertEqual(blend_session.context.task_focus, "Inspect the project.")
        self.assertEqual(
            blend_session.context.visible_mounts,
            ("session", "main", "output", "skills"),
        )
        self.assertEqual(
            blend_session.context.writable_mounts,
            ("session", "main", "output", "skills"),
        )
        self.assertEqual(
            blend_session.context.granted_capabilities,
            ("ws.repo.tree", "ws.skill.invoke", "ws.skill.compose"),
        )
        self.assertEqual(blend_session.metadata["source_kind"], "workstation_session")
        self.assertNotIn("openai", blend_session.context.visible_mounts)
        self.assertEqual(BlendSession.from_dict(blend_session.to_dict()), blend_session)

    def test_persist_workstation_session_refreshes_blend_discovery_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "ws-root"
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            report = launch_workstation_session(
                root_path=root,
                workspace_path=workspace,
                initial_task="Blend projection smoke test.",
            )
            blend_context_path = root / "BLEND_CONTEXT.json"
            blend_session_path = root / "BLEND_SESSION.json"
            blend_workflows_path = root / "BLEND_WORKFLOWS.json"
            self.assertTrue(blend_context_path.exists())
            self.assertTrue(blend_session_path.exists())
            self.assertTrue(blend_workflows_path.exists())
            self.assertTrue((root / "workflows" / "plans").exists())
            self.assertTrue((root / "workflows" / "runs").exists())

            original_blend_session = json.loads(blend_session_path.read_text())
            self.assertEqual(original_blend_session["session_id"], report["session_id"])
            self.assertEqual(original_blend_session["initial_task"], "Blend projection smoke test.")

            session = WorkstationSession.from_dict(report)
            updated = replace(session, allowed_capabilities=tuple([*session.allowed_capabilities, "ws.repo.search"]))
            persist_workstation_session(root, updated)

            refreshed_context = json.loads(blend_context_path.read_text())
            refreshed_session = json.loads(blend_session_path.read_text())
            refreshed_workflows = json.loads(blend_workflows_path.read_text())
            self.assertIn("ws.repo.search", refreshed_context["granted_capabilities"])
            self.assertIn("ws.repo.search", refreshed_session["context"]["granted_capabilities"])
            self.assertEqual(refreshed_workflows["latest_plan_id"], "")
            self.assertEqual(refreshed_workflows["latest_run_id"], "")

    def test_blend_context_projection_carries_shared_world_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            root = tmp / "ws-root"
            workspace = tmp / "workspace"
            world = tmp / "world"
            workspace.mkdir(parents=True, exist_ok=True)
            report = launch_workstation_session(
                root_path=root,
                workspace_path=workspace,
                blend_world_path=world,
                initial_task="Shared world projection test.",
            )
            blend_context_payload = json.loads((root / "BLEND_CONTEXT.json").read_text())
            blend_session_payload = json.loads((root / "BLEND_SESSION.json").read_text())
            self.assertTrue(str(blend_context_payload["world_id"]).startswith("bworld_"))
            self.assertEqual(
                blend_context_payload["world_root"],
                str(world.resolve()),
            )
            self.assertEqual(
                tuple(blend_context_payload["world_mounts"]),
                ("main", "scratch", "output"),
            )
            self.assertEqual(
                blend_session_payload["context"]["world_id"],
                blend_context_payload["world_id"],
            )
            self.assertEqual(blend_session_payload["session_id"], report["session_id"])


if __name__ == "__main__":
    unittest.main()
