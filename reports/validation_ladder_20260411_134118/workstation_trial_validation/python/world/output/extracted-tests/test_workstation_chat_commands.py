# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workstation.chat_commands import (
    canonical_workstation_chat_slash_command_text,
    run_workstation_chat_slash_command,
    run_workstation_natural_language_shell_command,
)
from workstation.session import launch_workstation_session, load_workstation_session


class WorkstationChatCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "root"
        self.workspace = Path(self.tempdir.name) / "workspace"
        self.skills_sqlite = Path(self.tempdir.name) / "skills.sqlite3"
        (self.workspace / "trials").mkdir(parents=True, exist_ok=True)
        (self.workspace / "exports").mkdir(parents=True, exist_ok=True)
        (self.workspace / "trials" / "demo.skill.yaml").write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Imported Skill",
                    "answer: hello from imported skill",
                ]
            )
            + "\n"
        )
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Test workstation chat slash commands.",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_import_and_list_skills_slash_commands(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct workstation chat lifecycle control, helps with verifying that slash-command import and listing reuse the governed skill-store path without going through the LLM.

        Reference to Theory:
            Verifies direct chat commands remain a host-owned shell layer over the same skill-management substrate used by deterministic CLI operations.

        Example Input Output:
            Input: `test_import_and_list_skills_slash_commands()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/import-skill trials/demo.skill.yaml",
        )
        self.assertTrue(handled)
        self.assertIn("Import status: ok", rendered)
        self.assertIn("Demo Imported Skill", rendered)

    def test_natural_language_import_prompt_routes_to_shell_import(self) -> None:
        handled, report = run_workstation_natural_language_shell_command(
            root=self.root,
            prompt="Import the skill file at trials/demo.skill.yaml into this workstation.",
        )
        self.assertTrue(handled)
        self.assertEqual(report["fulfilled_by"], "ws.skill.import")
        self.assertIn("Import status: ok", report["assistant_text"])
        self.assertIn("Demo Imported Skill", report["assistant_text"])

        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/list-skills demo",
        )
        self.assertTrue(handled)
        self.assertIn("Demo Imported Skill", rendered)

    def test_describe_and_permissions_slash_commands(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct workstation chat inspection of worker metadata, helps with verifying that slash commands can show skill declaration and declared permissions without an LLM round-trip.

        Reference to Theory:
            Verifies direct shell inspection commands remain grounded in the same workstation-visible worker inventory used for invocation.

        Example Input Output:
            Input: `test_describe_and_permissions_slash_commands()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        handled, described = run_workstation_chat_slash_command(
            root=self.root,
            command_text='/describe-skill "Workstation Repo Search"',
        )
        self.assertTrue(handled)
        self.assertIn("Title: Workstation Repo Search", described)
        self.assertIn("Authorities requested: execute, read", described)

        handled, permissions = run_workstation_chat_slash_command(
            root=self.root,
            command_text='/permissions "Workstation Repo Search"',
        )
        self.assertTrue(handled)
        self.assertIn("Declared permissions: execute, read", permissions)
        self.assertIn("Invocation note:", permissions)

    def test_permissions_lists_available_and_granted_session_capabilities(self) -> None:
        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/permissions",
        )
        self.assertTrue(handled)
        self.assertIn("Granted session capabilities:", rendered)
        self.assertIn("Available capabilities:", rendered)
        self.assertIn("ws.skill.catalog", rendered)
        self.assertIn("ws.repo.search", rendered)
        self.assertIn("ws.net.http", rendered)

    def test_slash_aliases_and_workstation_root_command(self) -> None:
        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/import-skill trials/demo.skill.yaml",
        )
        self.assertTrue(handled)
        self.assertIn("Import status: ok", rendered)

        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/s demo",
        )
        self.assertTrue(handled)
        self.assertIn("Demo Imported Skill", rendered)

        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/p",
        )
        self.assertTrue(handled)
        self.assertIn("Granted session capabilities:", rendered)

        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/workstation-root",
        )
        self.assertTrue(handled)
        self.assertIn(str(self.root.resolve()), rendered)

        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/prepare-markdown dilution relation",
        )
        self.assertTrue(handled)
        self.assertIn("interactive workstation chat target", rendered)

        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/start-research-into Chemistry",
        )
        self.assertTrue(handled)
        self.assertIn("interactive workstation chat target", rendered)

        self.assertEqual(canonical_workstation_chat_slash_command_text("/h"), "/help")
        self.assertEqual(canonical_workstation_chat_slash_command_text("/q"), "/quit")

    def test_grant_and_revoke_permission_commands_persist_session_capabilities(self) -> None:
        session_payload = json.loads((self.root / "SESSION.json").read_text())
        session_payload["allowed_capabilities"] = [
            "ws.skill.catalog",
            "ws.skill.import",
            "ws.skill.export",
            "ws.skill.invoke",
        ]
        (self.root / "SESSION.json").write_text(json.dumps(session_payload))

        handled, granted = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/grant-permission ws.repo.search",
        )
        self.assertTrue(handled)
        self.assertIn("Granted capability: ws.repo.search", granted)
        reloaded = load_workstation_session(self.root)
        self.assertIn("ws.repo.search", reloaded.allowed_capabilities)

        handled, revoked = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/revoke-permission ws.repo.search",
        )
        self.assertTrue(handled)
        self.assertIn("Revoked capability: ws.repo.search", revoked)
        reloaded = load_workstation_session(self.root)
        self.assertNotIn("ws.repo.search", reloaded.allowed_capabilities)

    def test_revoke_permission_rejects_protected_shell_capabilities(self) -> None:
        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text="/revoke-permission ws.skill.catalog",
        )
        self.assertTrue(handled)
        self.assertIn("Cannot revoke protected shell capability: ws.skill.catalog", rendered)

    def test_export_skill_slash_command_can_write_into_workspace(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct workstation chat lifecycle management, helps with verifying that one imported skill can be exported from chat into a workspace-relative destination path.

        Reference to Theory:
            Verifies direct shell skill utilities stay on the governed export path while still targeting intuitive workspace-relative outputs.

        Example Input Output:
            Input: `test_export_skill_slash_command_can_write_into_workspace()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        run_workstation_chat_slash_command(
            root=self.root,
            command_text="/import-skill trials/demo.skill.yaml",
        )
        handled, rendered = run_workstation_chat_slash_command(
            root=self.root,
            command_text='/export-skill "Demo Imported Skill" exports/demo-export.skill.yaml',
        )
        self.assertTrue(handled)
        self.assertIn("Export status: ok", rendered)
        self.assertTrue((self.workspace / "exports" / "demo-export.skill.yaml").exists())


if __name__ == "__main__":
    unittest.main()
