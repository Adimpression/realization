# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from applied_theory_types import ProposalType, RuntimeDeterminismPolicy, SupplementMode
from main import BSSCController
from replay_verifier import replay_run_bundle_document
from run_bundle_io import export_run_bundle_text, load_run_bundle_document
from store import build_artifact_store
from system_state import SystemState, save_state


class CoreRuntimeDeterminismReplayTests(unittest.TestCase):
    def test_system_state_serializes_determinism_policy_and_transcript(self) -> None:
        state = SystemState.bootstrap("Say hi.")
        state.determinism_policy = RuntimeDeterminismPolicy(
            mode="deterministic",
            llm_strategy="record",
            llm_seed=7,
            note="unit test",
        )
        state.llm_transcript.append(
            {
                "proposal_type": ProposalType.NOT_ELABORATION.value,
                "mode": "fast",
                "request_digest": "abc",
                "response_digest": "def",
            }
        )

        cloned = SystemState.from_dict(state.to_dict())
        self.assertEqual(cloned.determinism_policy.mode, "deterministic")
        self.assertEqual(cloned.determinism_policy.llm_strategy, "record")
        self.assertEqual(cloned.determinism_policy.llm_seed, 7)
        self.assertEqual(cloned.determinism_policy.note, "unit test")
        self.assertEqual(len(cloned.llm_transcript), 1)
        self.assertEqual(cloned.llm_transcript[0]["request_digest"], "abc")

    def test_transcript_record_then_replay_avoids_provider_calls(self) -> None:
        previous_provider = os.environ.get("LLM_PROVIDER")
        os.environ["LLM_PROVIDER"] = "llamacpp"
        try:
            state = SystemState.bootstrap("Say hi.")
            state.determinism_policy = RuntimeDeterminismPolicy(
                mode="deterministic",
                llm_strategy="record",
                llm_seed=11,
            )
            controller = BSSCController(state, llm_policy="auto")
            # Controller initialization may perform bounded warm-up proposals; this test asserts the explicit call below.
            state.llm_transcript = []
            node = state.root()

            def fake_ask_llm(prompt: str, **kwargs: object) -> tuple[str, dict[str, object]]:
                # Any valid JSON object is acceptable for this unit test seam.
                return json.dumps({"rationale": "ok"}), {"system_fingerprint": "test-fp"}

            with patch("supplement.ask_llm", new=fake_ask_llm):
                proposal = controller.request_proposal(
                    proposal_type=ProposalType.NOT_ELABORATION,
                    node=node,
                    target_scope="unit_test",
                    instructions="Return rationale JSON.",
                    fallback_payload={"rationale": ""},
                    mode=SupplementMode.FAST,
                )

            self.assertEqual(proposal.source, "llm")
            self.assertEqual(len(state.llm_transcript), 1)
            recorded = dict(state.llm_transcript[0])
            self.assertEqual(recorded.get("proposal_type"), ProposalType.NOT_ELABORATION.value)
            self.assertEqual(recorded.get("mode"), "fast")
            self.assertIn("request_digest", recorded)
            self.assertIsInstance(recorded.get("payload"), dict)

            replay_state = SystemState.bootstrap("Say hi.")
            replay_state.determinism_policy = RuntimeDeterminismPolicy(
                mode="replay",
                llm_strategy="replay",
                llm_seed=11,
            )
            replay_state.llm_transcript = [recorded]
            replay_controller = BSSCController(replay_state, llm_policy="off")
            replay_node = replay_state.root()

            with patch("supplement.ask_llm", side_effect=AssertionError("provider call occurred during replay")):
                replay_proposal = replay_controller.request_proposal(
                    proposal_type=ProposalType.NOT_ELABORATION,
                    node=replay_node,
                    target_scope="unit_test",
                    instructions="Return rationale JSON.",
                    fallback_payload={"rationale": ""},
                    mode=SupplementMode.FAST,
                )

            self.assertEqual(replay_proposal.source, "replay")
            self.assertEqual(replay_proposal.payload.get("rationale"), "ok")
        finally:
            if previous_provider is None:
                os.environ.pop("LLM_PROVIDER", None)
            else:
                os.environ["LLM_PROVIDER"] = previous_provider

    def test_run_bundle_includes_determinism_policy_and_transcript(self) -> None:
        store = build_artifact_store()
        state = SystemState.bootstrap("Say hi.")
        state.determinism_policy = RuntimeDeterminismPolicy(mode="deterministic", llm_strategy="record")
        state.llm_transcript.append(
            {
                "proposal_type": ProposalType.NOT_ELABORATION.value,
                "mode": "fast",
                "request_digest": "abc",
                "response_digest": "def",
                "payload": {"rationale": "ok"},
                "raw_text": "{\"rationale\":\"ok\"}",
            }
        )
        controller = BSSCController(state, llm_policy="off")
        controller.run(max_steps=1)

        with tempfile.TemporaryDirectory(prefix="run_bundle_determinism_") as tempdir:
            state_path = Path(tempdir) / "state.json"
            bundle_path = Path(tempdir) / "bundle.yaml"
            save_state(state, state_path)
            bundle_path.write_text(export_run_bundle_text(state, store, llm_policy="off", max_steps=1))
            bundle = load_run_bundle_document(bundle_path)
            run = dict(bundle.get("run", {}))
            self.assertEqual(run.get("determinism_policy", {}).get("mode"), "deterministic")
            self.assertEqual(run.get("determinism_policy", {}).get("llm_strategy"), "record")
            self.assertEqual(len(run.get("llm_transcript", [])), 1)

    def test_deterministic_bundle_replay_is_strict_and_stable_under_llm_off(self) -> None:
        with tempfile.TemporaryDirectory(prefix="deterministic_bundle_replay_") as tempdir:
            root = Path(tempdir)
            bundle_path = root / "bundle.yaml"
            with patch.dict(
                os.environ,
                {
                    "STATE_SQLITE_PATH": str(root / "original.sqlite3"),
                    "STATE_VECTOR_MODE": "off",
                },
                clear=False,
            ):
                store = build_artifact_store()
                state = SystemState.bootstrap("Say hi.")
                state.determinism_policy = RuntimeDeterminismPolicy(mode="deterministic", llm_strategy="off")
                controller = BSSCController(state, llm_policy="off")
                controller.run(max_steps=12)
                bundle_path.write_text(export_run_bundle_text(state, store, llm_policy="off", max_steps=12))
            report = replay_run_bundle_document(
                load_run_bundle_document(bundle_path),
                sqlite_path=root / "replay.sqlite3",
                llm_policy="off",
                max_steps=12,
            )

        self.assertTrue(report["replay_ok"])
        self.assertEqual(
            report["comparison"]["original_decision_flow_signatures"],
            report["comparison"]["replay_decision_flow_signatures"],
        )
        self.assertEqual(
            report["comparison"]["original_llm_transcript_signatures"],
            report["comparison"]["replay_llm_transcript_signatures"],
        )


if __name__ == "__main__":
    unittest.main()
