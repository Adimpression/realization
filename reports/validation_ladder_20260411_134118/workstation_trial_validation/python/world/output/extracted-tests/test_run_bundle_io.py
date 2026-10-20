# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from main import BSSCController, SystemState, build_artifact_store, load_artifact_yaml_documents
from replay_verifier import replay_run_bundle_document
from run_bundle_io import (
    export_run_bundle_text,
    load_run_bundle_document,
    load_run_bundle_from_state_file,
)
from skill_schema_io import artifact_from_skill_document
from system_state import save_state


class RunBundleIOTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="run_bundle_io_")
        self.sqlite_path = str(Path(self.tempdir.name) / "run_bundle.sqlite3")
        self.previous_sqlite_path = os.environ.get("STATE_SQLITE_PATH")
        os.environ["STATE_SQLITE_PATH"] = self.sqlite_path

    def tearDown(self) -> None:
        if self.previous_sqlite_path is None:
            os.environ.pop("STATE_SQLITE_PATH", None)
        else:
            os.environ["STATE_SQLITE_PATH"] = self.previous_sqlite_path
        self.tempdir.cleanup()

    def test_run_bundle_round_trips_executed_ability(self) -> None:
        store = build_artifact_store()
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "boundary_shape_artifacts"
            / "hi_responder.yaml"
        )
        artifacts = load_artifact_yaml_documents(fixture_path)
        for artifact in artifacts:
            store.persist_artifact(artifact, run_id="test_run_bundle_io")

        state = SystemState.bootstrap("Say hi.")
        controller = BSSCController(state, llm_policy="off")
        controller.run(max_steps=64)

        self.assertEqual(state.run_outcome.value, "completed")
        self.assertEqual(state.root_final_answer(), "hi")
        self.assertGreaterEqual(len(state.effect_traces), 1)

        state_path = Path(self.tempdir.name) / "state.json"
        bundle_path = Path(self.tempdir.name) / "bundle.yaml"
        replay_state_path = Path(self.tempdir.name) / "replay_state.json"
        save_state(state, state_path)

        bundle_from_state = load_run_bundle_from_state_file(
            state_path,
            store,
            llm_policy="off",
            max_steps=64,
        )
        self.assertEqual(bundle_from_state["schema"], "bssc_run_bundle.v1")
        self.assertEqual(bundle_from_state["run"]["final_answer"], "hi")
        self.assertIn("governance_snapshot", bundle_from_state)
        self.assertIn("receipts", bundle_from_state["governance_snapshot"])
        self.assertIn(
            "Hi Responder",
            {str(item.get("title", "")).strip() for item in bundle_from_state["skills"]},
        )

        bundle_path.write_text(export_run_bundle_text(state, store, llm_policy="off", max_steps=64))
        bundle = load_run_bundle_document(bundle_path)
        report = replay_run_bundle_document(
            bundle,
            llm_policy="off",
            max_steps=64,
            state_out=replay_state_path,
        )

        self.assertTrue(report["replay_ok"])
        self.assertEqual(report["original_run"]["run_outcome"], "completed")
        self.assertEqual(report["original_run"]["final_answer"], "hi")
        self.assertEqual(report["replay_run"]["run_outcome"], "completed")
        self.assertEqual(report["replay_run"]["final_answer"], "hi")
        self.assertGreaterEqual(report["imported_skill_count"], 1)
        self.assertTrue(replay_state_path.exists())
        original_signatures = report["comparison"]["original_effect_signatures"]
        self.assertGreaterEqual(len(original_signatures), 1)
        self.assertIn("receipt_digests", original_signatures[0])
        self.assertTrue(original_signatures[0]["receipt_digests"])
        self.assertIn("original_governance_receipts", report["comparison"])
        self.assertIn("replay_governance_receipts", report["comparison"])
        self.assertEqual(
            report["comparison"]["original_composition_chain_signatures"],
            report["comparison"]["replay_composition_chain_signatures"],
        )
        self.assertGreaterEqual(report["comparison"]["original_composition_chain_count"], 1)

    def test_run_bundle_round_trips_knowledge_only_run_without_effect_trace(self) -> None:
        store = build_artifact_store()
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "knowledge",
                "title": "What Is Force?",
                "question": "What is force?",
                "answer": "Force equals mass times acceleration.",
                "declaration": {
                    "intent": "Answer a passive physics definition question.",
                    "inputs": {},
                    "outputs": {"answer": "definition answer"},
                    "authorities_requested": ["read"],
                    "authority_bounds": {
                        "read": {
                            "scope": "artifact_store",
                            "target": "knowledge_artifact",
                            "context": "direct_user_question",
                            "duration": "single_invocation",
                            "triggering_conditions": ["user asks the covered question"],
                            "approval_class": "automatic",
                        }
                    },
                    "data_classes_touched": ["public"],
                    "side_effects": [],
                    "persistence_behavior": "none",
                    "invocation_rights": ["direct_user_invocation"],
                    "composition_rights": [],
                    "escalation_rights": [],
                    "approval_requirements": ["automatic"],
                    "risk_tier": "tier0_passive",
                },
            }
        )
        store.persist_artifact(artifact, run_id="test_run_bundle_io")

        state = SystemState.bootstrap("What is force?")
        controller = BSSCController(state, llm_policy="off")
        controller.run(max_steps=64)

        self.assertEqual(state.run_outcome.value, "completed")
        self.assertEqual(state.root_final_answer(), "Force equals mass times acceleration.")
        self.assertEqual(len(state.effect_traces), 0)

        state_path = Path(self.tempdir.name) / "knowledge_state.json"
        bundle_path = Path(self.tempdir.name) / "knowledge_bundle.yaml"
        save_state(state, state_path)
        bundle_document = load_run_bundle_from_state_file(
            state_path,
            store,
            llm_policy="off",
            max_steps=64,
        )
        self.assertEqual(bundle_document["run"]["final_answer"], "Force equals mass times acceleration.")
        self.assertIn(
            "What Is Force?",
            {str(item.get("title", "")).strip() for item in bundle_document["skills"]},
        )

        bundle_path.write_text(export_run_bundle_text(state, store, llm_policy="off", max_steps=64))
        report = replay_run_bundle_document(
            load_run_bundle_document(bundle_path),
            llm_policy="off",
            max_steps=64,
        )

        self.assertTrue(report["replay_ok"])
        self.assertEqual(report["original_run"]["final_answer"], "Force equals mass times acceleration.")
        self.assertEqual(report["replay_run"]["final_answer"], "Force equals mass times acceleration.")
        self.assertEqual(
            report["comparison"]["original_effect_trace_count"],
            0,
        )
        self.assertEqual(
            report["comparison"]["original_composition_chain_signatures"],
            report["comparison"]["replay_composition_chain_signatures"],
        )

    def test_run_bundle_carries_installed_governance_records_for_replay(self) -> None:
        store = build_artifact_store()
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "boundary_shape_artifacts"
            / "hi_responder.yaml"
        )
        for artifact in load_artifact_yaml_documents(fixture_path):
            store.persist_artifact(artifact, run_id="test_run_bundle_io")
        revocation = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "revocation",
                "title": "Revoke Unrelated Skill",
                "revocation": {
                    "intent": "Withdraw trust from an unrelated skill.",
                    "subject_titles": ["Unrelated Skill"],
                    "subject_kinds": ["ability"],
                    "trust_status": "revoked",
                    "quarantine_status": "clear",
                    "activation_status": "inactive",
                    "installation_status": "blocked",
                    "status": "active",
                    "issued_by": "operator://local-admin",
                    "rationale": "Replay should preserve installed governance records.",
                },
            }
        )
        store.persist_artifact(revocation, run_id="test_run_bundle_io")

        state = SystemState.bootstrap("Say hi.")
        controller = BSSCController(state, llm_policy="off")
        controller.run(max_steps=64)

        bundle_path = Path(self.tempdir.name) / "bundle_with_governance.yaml"
        bundle_path.write_text(export_run_bundle_text(state, store, llm_policy="off", max_steps=64))
        bundle = load_run_bundle_document(bundle_path)
        skill_titles = {str(item.get("title", "")).strip() for item in bundle["skills"]}

        self.assertIn("Revoke Unrelated Skill", skill_titles)
        self.assertIn("Revoke Unrelated Skill", bundle["governance_snapshot"]["revocation_titles"])

        report = replay_run_bundle_document(
            bundle,
            llm_policy="off",
            max_steps=64,
        )

        self.assertTrue(report["replay_ok"])
        self.assertEqual(
            report["comparison"]["original_governance_receipts"]["revocation_titles"],
            report["comparison"]["replay_governance_receipts"]["revocation_titles"],
        )


if __name__ == "__main__":
    unittest.main()
