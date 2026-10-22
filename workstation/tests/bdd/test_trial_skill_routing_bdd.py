from __future__ import annotations

import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controller_entrypoints import ensure_application_controller_runtime
from workstation.shell.core.trial_validation import validate_workstation_trial_domains


REPO_ROOT = Path(__file__).resolve().parents[3]


class WorkstationTrialSkillRoutingBDD(unittest.TestCase):
    def setUp(self) -> None:
        ensure_application_controller_runtime()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.enterContext(
            patch.dict(
                "os.environ",
                {"WORKSTATION_HOME": str(self.root / "workstation-home")},
                clear=False,
            )
        )
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()

    def _trial_root(self, *, domain: str, prompts: tuple[str, ...]) -> Path:
        trials_root = self.root / f"{domain}-trials"
        domain_root = trials_root / domain
        domain_root.mkdir(parents=True)
        shutil.copyfile(REPO_ROOT / "trials" / domain / "skill.yaml", domain_root / "skill.yaml")
        (domain_root / "PROMPTS.md").write_text(
            "".join(f"- {prompt}\n" for prompt in prompts),
            encoding="utf-8",
        )
        return trials_root

    def test_fresh_bash_bundle_creates_archive_from_named_source_directory(self) -> None:
        archive_path = self.root / "realized-tests.tar.gz"
        prompt = f"Create the archive `{archive_path}` from `tests`."
        trials_root = self._trial_root(domain="bash", prompts=(prompt,))

        with patch(
            "workstation.foundation.host.llm_driver.build_workstation_openai_client",
            side_effect=AssertionError("the deterministic trial path must not call a provider"),
        ):
            report = validate_workstation_trial_domains(
                domains=("bash",),
                workspace_path=REPO_ROOT,
                trials_root=trials_root,
                report_root=self.root / "bash-report",
                max_tool_rounds=2,
            )

        prompt_result = report["domains"][0]["prompt_results"][0]
        self.assertEqual("ok", prompt_result["status"], msg=prompt_result)
        self.assertTrue(prompt_result["route"]["used_direct_composition"])
        self.assertTrue(archive_path.is_file())
        with tarfile.open(archive_path, mode="r:gz") as archive:
            member_names = archive.getnames()
        self.assertTrue(any(name.endswith("test_architecture_boundaries.py") for name in member_names))

    def test_fresh_bash_bundle_removes_named_file_without_llm(self) -> None:
        target_path = self.root / "stale.txt"
        target_path.write_text("remove me\n", encoding="utf-8")
        prompt = f"Remove `{target_path}`."
        trials_root = self._trial_root(domain="bash", prompts=(prompt,))

        with patch(
            "workstation.foundation.host.llm_driver.build_workstation_openai_client",
            side_effect=AssertionError("the deterministic trial path must not call a provider"),
        ):
            report = validate_workstation_trial_domains(
                domains=("bash",),
                workspace_path=REPO_ROOT,
                trials_root=trials_root,
                report_root=self.root / "bash-remove-report",
                max_tool_rounds=2,
            )

        prompt_result = report["domains"][0]["prompt_results"][0]
        self.assertEqual("ok", prompt_result["status"], msg=prompt_result)
        self.assertTrue(prompt_result["route"]["used_direct_composition"])
        self.assertTrue(prompt_result["route"]["used_skill_invoke"])
        self.assertIn(
            "Bash Commands 09 — Remove File / Bash Commands 09 Remove File",
            prompt_result["route"]["invoked_skill_titles"],
        )
        self.assertFalse(target_path.exists())

    def test_fresh_physics_bundle_routes_conceptual_prompts_to_knowledge(self) -> None:
        prompts = (
            "What distinguishes a scalar quantity from a vector quantity, and how is this represented in the reusable relation?",
            "Explain how work relates to energy change, and state the work-energy theorem in terms of the transfer substrate.",
        )
        trials_root = self._trial_root(domain="physics", prompts=prompts)

        with patch(
            "workstation.foundation.host.llm_driver.build_workstation_openai_client",
            side_effect=AssertionError("the deterministic trial path must not call a provider"),
        ):
            report = validate_workstation_trial_domains(
                domains=("physics",),
                workspace_path=REPO_ROOT,
                trials_root=trials_root,
                report_root=self.root / "physics-report",
                max_tool_rounds=2,
            )

        domain_report = report["domains"][0]
        self.assertEqual("ok", domain_report["status"], msg=domain_report["prompt_results"])
        self.assertEqual(2, domain_report["prompt_summary"]["ok"])
        for prompt_result in domain_report["prompt_results"]:
            self.assertEqual("ok", prompt_result["terminal_tool_status"], msg=prompt_result)
            self.assertTrue(prompt_result["route"]["used_direct_composition"])
            self.assertTrue(prompt_result["route"]["used_skill_invoke"])
        invoked_titles = [
            title
            for prompt_result in domain_report["prompt_results"]
            for title in prompt_result["route"]["invoked_skill_titles"]
        ]
        self.assertIn(
            "Physics Relations — Scalars and Vectors / Physics Relations Scalars And Vectors",
            invoked_titles,
        )
        self.assertIn(
            "Physics Relations — Work and Energy Transfer / Work-energy theorem",
            invoked_titles,
        )


if __name__ == "__main__":
    unittest.main()
