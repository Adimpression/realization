# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest
from collections.abc import Mapping
from typing import Any

from realized_core_engine.controller_runtime import BSSCController
from realized_core_engine.state import SystemState
from realized_core_semantics.applied_model import Artifact, ArtifactType
from realized_core_semantics.applied_primitives import (
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    LearningRelation,
)
from realized_exchange.skill_schema import artifact_from_skill_document


def _authority_bound(authority: str) -> dict[str, Any]:
    return {
        "scope": "local_skill_store",
        "target": f"knowledge_{authority}",
        "context": "explicit_user_prompt",
        "duration": "single_invocation",
        "triggering_conditions": ["user asks the declared question"],
        "approval_class": "automatic",
    }


def _governed_knowledge(
    *,
    admission_status: str = "admitted",
    lifecycle: Mapping[str, Any] | None = None,
    authorities: tuple[str, ...] = ("read",),
) -> Artifact:
    admitted = admission_status == "admitted"
    content: dict[str, Any] = {
        "question": "What is orbital quartz?",
        "answer": "Orbital quartz is the exact but governed answer.",
        "aliases": ["orbital quartz"],
        "skill_schema": "bssc_skill.v2",
        "skill_kind": "knowledge",
        "skill_declaration": {
            "intent": "Answer what orbital quartz is.",
            "inputs": {"question": "knowledge request"},
            "outputs": {"answer": "knowledge answer"},
            "authorities_requested": list(authorities),
            "authority_bounds": {
                authority: _authority_bound(authority)
                for authority in authorities
            },
            "data_classes_touched": ["public"],
            "side_effects": ["none"],
            "persistence_behavior": "none",
            "invocation_rights": ["direct_user_invocation"],
            "composition_rights": [],
            "escalation_rights": [],
            "approval_requirements": ["automatic"],
            "risk_tier": "tier0_passive",
        },
        "skill_admission": {
            "status": admission_status,
            "admitted": admitted,
            "rationale": "" if admitted else f"Artifact is {admission_status}.",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
        },
    }
    if lifecycle is not None:
        content["skill_lifecycle"] = dict(lifecycle)
    return Artifact(
        id="artifact-orbital-quartz",
        artifact_type=ArtifactType.KNOWLEDGE,
        title="Orbital Quartz Definition",
        representation=ArtifactRepresentation.YAML,
        function_bit=0,
        scope="answer orbital quartz questions",
        provenance=["test"],
        reusability=ArtifactReuse.BROAD_REUSE,
        admissibility=ArtifactAdmission.ADMITTED,
        template_schema={},
        learning_relation=LearningRelation.NEW_FAMILY,
        related_artifact_ids=[],
        content=content,
        justification="Exercise governance before answer selection.",
    )


def _controller_with_inventory(*artifacts: Artifact) -> BSSCController:
    controller = BSSCController(
        SystemState.bootstrap("What is orbital quartz?"),
        llm_policy="off",
    )
    controller.artifact_store.load_all_artifacts = lambda: list(artifacts)  # type: ignore[method-assign]
    return controller


def _candidate_ids(controller: BSSCController) -> tuple[list[str], list[str]]:
    prompt = "What is orbital quartz?"
    persisted = [
        artifact.id
        for artifact in controller.persisted_direct_knowledge_candidates(
            semantic_unit=prompt,
        )
    ]
    focused = [
        artifact.id
        for _, artifact in controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            include_unmatched_pool=True,
        )
    ]
    return persisted, focused


class GovernanceSelectionPrecedenceTests(unittest.TestCase):
    def test_exact_match_remains_selectable_when_current_use_allows_it(self) -> None:
        artifact = _governed_knowledge()
        controller = _controller_with_inventory(artifact)

        self.assertTrue(
            controller.artifact_has_answer_capability(
                artifact,
                semantic_unit="What is orbital quartz?",
            )
        )
        self.assertEqual(
            ([artifact.id], [artifact.id]),
            _candidate_ids(controller),
        )

    def test_exact_match_cannot_override_admission_or_lifecycle_denial(self) -> None:
        denied_cases = (
            ("held", None),
            ("rejected", None),
            (
                "admitted",
                {
                    "admission_status": "admitted",
                    "installation_status": "installed",
                    "activation_status": "inactive",
                    "trust_status": "trusted",
                    "quarantine_status": "clear",
                },
            ),
            (
                "admitted",
                {
                    "admission_status": "admitted",
                    "installation_status": "installed",
                    "activation_status": "active",
                    "trust_status": "revoked",
                    "quarantine_status": "clear",
                },
            ),
            (
                "admitted",
                {
                    "admission_status": "admitted",
                    "installation_status": "installed",
                    "activation_status": "active",
                    "trust_status": "trusted",
                    "quarantine_status": "quarantined",
                },
            ),
        )

        for admission_status, lifecycle in denied_cases:
            with self.subTest(
                admission_status=admission_status,
                lifecycle=lifecycle,
            ):
                artifact = _governed_knowledge(
                    admission_status=admission_status,
                    lifecycle=lifecycle,
                )
                controller = _controller_with_inventory(artifact)
                self.assertFalse(
                    controller.artifact_has_answer_capability(
                        artifact,
                        semantic_unit="What is orbital quartz?",
                    )
                )
                self.assertEqual(([], []), _candidate_ids(controller))

    def test_exact_match_cannot_override_revocation_or_incident_overlay(self) -> None:
        overlays = (
            artifact_from_skill_document(
                {
                    "schema": "bssc_skill.v2",
                    "kind": "revocation",
                    "title": "Revoke Orbital Quartz",
                    "revocation": {
                        "intent": "Revoke the named knowledge skill.",
                        "subject_titles": ["Orbital Quartz Definition"],
                        "subject_kinds": ["knowledge"],
                        "trust_status": "revoked",
                        "quarantine_status": "clear",
                        "activation_status": "inactive",
                        "installation_status": "blocked",
                        "status": "active",
                        "issued_by": "operator://test",
                        "rationale": "The knowledge is under review.",
                    },
                }
            ),
            artifact_from_skill_document(
                {
                    "schema": "bssc_skill.v2",
                    "kind": "incident",
                    "title": "Quarantine Orbital Quartz",
                    "incident": {
                        "intent": "Quarantine the named knowledge skill.",
                        "subject_titles": ["Orbital Quartz Definition"],
                        "subject_kinds": ["knowledge"],
                        "severity": "critical",
                        "enforcement_action": "quarantine",
                        "status": "open",
                        "issued_by": "operator://test",
                        "rationale": "The knowledge is incident-affected.",
                    },
                }
            ),
        )

        for overlay in overlays:
            with self.subTest(overlay=overlay.title):
                artifact = _governed_knowledge()
                controller = _controller_with_inventory(artifact, overlay)
                self.assertEqual(([], []), _candidate_ids(controller))

    def test_exact_match_cannot_override_current_policy_authority_denial(self) -> None:
        artifact = _governed_knowledge(authorities=("read", "write"))
        policy = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v2",
                "kind": "policy",
                "title": "Read Only Knowledge Policy",
                "policy": {
                    "intent": "Admit passive read-only knowledge only.",
                    "target_kinds": ["knowledge"],
                    "max_risk_tier": "tier0_passive",
                    "allowed_authorities": ["read"],
                    "denied_authorities": ["write"],
                    "allowed_executors": [],
                    "allowed_data_classes": ["public"],
                    "denied_side_effects": [],
                    "required_approval_for_risk_tiers": {},
                },
            }
        )
        controller = _controller_with_inventory(artifact, policy)

        use_state = controller.current_skill_governance_snapshot()
        self.assertEqual([policy], use_state["policies"])
        self.assertFalse(
            controller.artifact_has_answer_capability(
                artifact,
                semantic_unit="What is orbital quartz?",
            )
        )
        self.assertEqual(([], []), _candidate_ids(controller))


if __name__ == "__main__":
    unittest.main()
