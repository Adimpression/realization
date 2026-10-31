# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from realized_core_semantics.applied_model import (
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    LearningRelation,
)
from realized_exchange.learning_context import (
    LearningContext,
    LearningUnit,
    load_learning_context,
    load_subject_reasoning_scope,
    new_subject_import,
    persist_learning_context,
    persist_subject_import,
    stable_learning_unit_id,
)
from workstation.app.cli.runtime_controller import bootstrap_runtime_controller


class RuntimeControllerApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _persist_context(self, *, subject_id: str, title: str, unit_title: str, statement: str, skill_id: str) -> str:
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id=subject_id,
                unit_kind="definition",
                canonical_title=unit_title,
            ),
            subject_id=subject_id,
            unit_kind="definition",
            canonical_title=unit_title,
            statement=statement,
            linked_skill_ids=(skill_id,),
            status="admitted",
        )
        context = LearningContext(
            subject_id=subject_id,
            canonical_title=title,
            aliases=(title,),
            subject_family="Physics",
            summary=statement,
            units=(unit,),
            linked_skill_ids=(skill_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        return unit.unit_id

    def _knowledge_artifact(self, *, artifact_id: str, title: str, answer: str) -> Artifact:
        return Artifact(
            id=artifact_id,
            artifact_type=ArtifactType.KNOWLEDGE,
            title=title,
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="bounded reuse",
            provenance=[],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={"question": title, "answer": answer},
            justification="test fixture",
        )

    def test_bootstrap_runtime_controller_preloads_primary_and_imported_subject_scope_artifacts(self) -> None:
        active_subject_id = "kinematics-active"
        imported_subject_id = "dynamics-borrowed"
        self._persist_context(
            subject_id=active_subject_id,
            title="Kinematics Active",
            unit_title="Velocity",
            statement="Velocity is displacement per unit time.",
            skill_id="velocity-skill",
        )
        imported_unit_id = self._persist_context(
            subject_id=imported_subject_id,
            title="Dynamics Borrowed",
            unit_title="Force",
            statement="Force equals mass times acceleration.",
            skill_id="force-skill",
        )

        active_context = load_learning_context(self.root, active_subject_id)
        imported_context = load_learning_context(self.root, imported_subject_id)
        persist_subject_import(
            self.root,
            new_subject_import(
                active_subject_id=active_subject_id,
                active_subject_version_id=active_context.content_hash(),
                active_subject_title=active_context.canonical_title,
                source_subject_id=imported_subject_id,
                source_subject_version_id=imported_context.content_hash(),
                source_subject_title=imported_context.canonical_title,
                import_kind="definition_support",
                imported_unit_ids=(imported_unit_id,),
                rationale="Borrow the force definition as bounded support.",
            ),
        )
        scope = load_subject_reasoning_scope(self.root, active_subject_id)

        with patch.dict(os.environ, {"STATE_VECTOR_MODE": "off"}, clear=False):
            state, _controller = bootstrap_runtime_controller(
                semantic_unit="Explain velocity with neighboring force context.",
                llm_policy="off",
                subject_scope=scope,
                subject_scope_root_path=self.root,
            )

        titles = {str(artifact.title) for artifact in state.learned_artifacts.values()}
        origin_kinds = {
            str(item.get("origin_kind", ""))
            for item in state.learned_artifact_origins.values()
        }

        self.assertEqual(state.subject_reasoning_scope.get("active_subject_id"), active_subject_id)
        self.assertIn("primary", origin_kinds)
        self.assertIn("borrowed", origin_kinds)
        self.assertTrue(any(title.startswith("Kinematics Active / Velocity") for title in titles))
        self.assertTrue(any(title.startswith("Dynamics Borrowed / Force") for title in titles))

        ordered_titles = [str(artifact.title) for artifact in _controller.reusable_artifact_candidates()]
        self.assertTrue(ordered_titles[0].startswith("Kinematics Active / Velocity"))
        self.assertTrue(any(title.startswith("Dynamics Borrowed / Force") for title in ordered_titles[1:]))

    def test_scope_disabled_skips_ambient_store_lookup_when_no_projected_skills_exist(self) -> None:
        subject_id = "subject-without-projected-skills"
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="No Projection Subject",
            aliases=("No Projection Subject",),
            subject_family="Physics",
            summary="No linked skills means no projected runtime preload.",
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        scope = load_subject_reasoning_scope(self.root, subject_id)

        with patch.dict(os.environ, {"STATE_VECTOR_MODE": "off"}, clear=False):
            state, controller = bootstrap_runtime_controller(
                semantic_unit="Explain the empty subject scope.",
                llm_policy="off",
                subject_scope=scope,
                subject_scope_root_path=self.root,
            )

        store = Mock()
        store.load_relevant_artifacts.return_value = [
            self._knowledge_artifact(
                artifact_id="artifact-global-empty-scope",
                title="Global / Ambient Artifact",
                answer="ambient fallback",
            )
        ]
        controller.artifact_store = store
        controller.load_learning_context(state.root())

        store.load_relevant_artifacts.assert_not_called()
        self.assertEqual(state.learned_artifacts, {})

    def test_scope_disabled_returns_ranked_local_artifacts_without_ambient_store_lookup(self) -> None:
        subject_id = "subject-with-ranked-local-scope"
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Ranked Local Subject",
            aliases=("Ranked Local Subject",),
            subject_family="Physics",
            summary="Local ranked subject scope test.",
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        scope = load_subject_reasoning_scope(self.root, subject_id)

        with patch.dict(os.environ, {"STATE_VECTOR_MODE": "off"}, clear=False):
            state, controller = bootstrap_runtime_controller(
                semantic_unit="Explain velocity in the active subject.",
                llm_policy="off",
                subject_scope=scope,
                subject_scope_root_path=self.root,
            )

        local_velocity = self._knowledge_artifact(
            artifact_id="artifact-local-velocity",
            title="Ranked Local Subject / Velocity",
            answer="Velocity is displacement per unit time.",
        )
        local_momentum = self._knowledge_artifact(
            artifact_id="artifact-local-momentum",
            title="Ranked Local Subject / Momentum",
            answer="Momentum is mass times velocity.",
        )
        state.learned_artifacts = {
            local_velocity.id: local_velocity,
            local_momentum.id: local_momentum,
        }
        state.learned_artifact_origins = {
            local_velocity.id: {"origin_kind": "primary"},
            local_momentum.id: {"origin_kind": "primary"},
        }

        store = Mock()
        store.load_all_artifacts.return_value = []
        controller.artifact_store = store

        artifacts = controller.store_relevant_artifacts("Explain velocity in the active subject.", limit=2)

        store.load_relevant_artifacts.assert_not_called()
        self.assertEqual([artifact.id for artifact in artifacts], [local_velocity.id, local_momentum.id])

    def test_scope_enabled_allows_global_lookup_and_marks_global_origin(self) -> None:
        subject_id = "subject-with-global-enabled"
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Global Enabled Subject",
            aliases=("Global Enabled Subject",),
            subject_family="Physics",
            summary="Global retrieval is enabled for this test.",
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        scope = load_subject_reasoning_scope(self.root, subject_id).to_dict()
        scope["global_retrieval_policy"] = "enabled"

        with patch.dict(os.environ, {"STATE_VECTOR_MODE": "off"}, clear=False):
            state, controller = bootstrap_runtime_controller(
                semantic_unit="Explain the globally enabled subject scope.",
                llm_policy="off",
                subject_scope=scope,
                subject_scope_root_path=self.root,
            )
        state.learned_artifacts = {}
        state.learned_artifact_origins = {}

        global_artifact = self._knowledge_artifact(
            artifact_id="artifact-global-enabled",
            title="Global / Enabled Artifact",
            answer="global fallback",
        )
        store = Mock()
        store.load_relevant_artifacts.return_value = [global_artifact]
        store.load_all_artifacts.return_value = []
        controller.artifact_store = store
        artifacts = controller.store_relevant_artifacts("Explain the globally enabled subject scope.", limit=1)

        store.load_relevant_artifacts.assert_called()
        self.assertEqual([artifact.id for artifact in artifacts], [global_artifact.id])
        self.assertIn(global_artifact.id, state.learned_artifacts)
        self.assertEqual(
            state.learned_artifact_origins.get(global_artifact.id, {}).get("origin_kind"),
            "global",
        )

    def test_scope_enabled_prefers_local_primary_then_borrowed_then_global(self) -> None:
        subject_id = "subject-with-tiered-scope"
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Tiered Scope Subject",
            aliases=("Tiered Scope Subject",),
            subject_family="Physics",
            summary="Tiered scope ordering test.",
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        scope = load_subject_reasoning_scope(self.root, subject_id).to_dict()
        scope["global_retrieval_policy"] = "enabled"

        with patch.dict(os.environ, {"STATE_VECTOR_MODE": "off"}, clear=False):
            state, controller = bootstrap_runtime_controller(
                semantic_unit="Explain force in the tiered scope.",
                llm_policy="off",
                subject_scope=scope,
                subject_scope_root_path=self.root,
            )

        primary_force = self._knowledge_artifact(
            artifact_id="artifact-primary-force",
            title="Tiered Scope Subject / Force",
            answer="Primary force explanation.",
        )
        borrowed_force = self._knowledge_artifact(
            artifact_id="artifact-borrowed-force",
            title="Borrowed Support Subject / Force",
            answer="Borrowed force explanation.",
        )
        global_force = self._knowledge_artifact(
            artifact_id="artifact-global-force",
            title="Global Library / Force",
            answer="Global force fallback.",
        )
        state.learned_artifacts = {
            primary_force.id: primary_force,
            borrowed_force.id: borrowed_force,
        }
        state.learned_artifact_origins = {
            primary_force.id: {"origin_kind": "primary"},
            borrowed_force.id: {"origin_kind": "borrowed"},
        }

        store = Mock()
        store.load_relevant_artifacts.return_value = [global_force]
        store.load_all_artifacts.return_value = []
        controller.artifact_store = store

        artifacts = controller.store_relevant_artifacts("Explain force in the tiered scope.", limit=3)

        store.load_relevant_artifacts.assert_called_once()
        self.assertEqual(
            [artifact.id for artifact in artifacts],
            [primary_force.id, borrowed_force.id, global_force.id],
        )
        self.assertEqual(
            state.learned_artifact_origins.get(global_force.id, {}).get("origin_kind"),
            "global",
        )

    def test_learning_context_trace_and_node_payload_surface_origin_tiers(self) -> None:
        subject_id = "subject-with-origin-trace"
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Origin Trace Subject",
            aliases=("Origin Trace Subject",),
            subject_family="Physics",
            summary="Origin trace surfacing test.",
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        scope = load_subject_reasoning_scope(self.root, subject_id).to_dict()
        scope["global_retrieval_policy"] = "enabled"

        with patch.dict(os.environ, {"STATE_VECTOR_MODE": "off"}, clear=False):
            state, controller = bootstrap_runtime_controller(
                semantic_unit="Explain force in the origin-trace subject.",
                llm_policy="off",
                subject_scope=scope,
                subject_scope_root_path=self.root,
            )

        primary_force = self._knowledge_artifact(
            artifact_id="artifact-primary-trace-force",
            title="Origin Trace Subject / Force",
            answer="Primary force explanation.",
        )
        borrowed_force = self._knowledge_artifact(
            artifact_id="artifact-borrowed-trace-force",
            title="Borrowed Support Subject / Force",
            answer="Borrowed force explanation.",
        )
        global_force = self._knowledge_artifact(
            artifact_id="artifact-global-trace-force",
            title="Global Library / Force",
            answer="Global force fallback.",
        )
        state.learned_artifacts = {
            primary_force.id: primary_force,
            borrowed_force.id: borrowed_force,
        }
        state.learned_artifact_origins = {
            primary_force.id: {"origin_kind": "primary", "source_subject_id": subject_id},
            borrowed_force.id: {
                "origin_kind": "borrowed",
                "source_subject_id": "borrowed-support-subject",
                "source_import_id": "import-borrowed-force",
            },
        }

        store = Mock()
        store.load_relevant_artifacts.return_value = [global_force]
        store.load_all_artifacts.return_value = []
        controller.artifact_store = store

        controller.load_learning_context(state.root())

        learning_step = next(record for record in reversed(state.ledger) if record.kind == "learning_context")
        origin_report = learning_step.payload.get("artifact_origin_report", {})
        self.assertEqual(origin_report.get("counts"), {"primary": 1, "borrowed": 1, "global": 1})
        self.assertEqual(
            [item.get("origin_kind") for item in origin_report.get("items", [])],
            ["primary", "borrowed", "global"],
        )
        node_payload = controller.proposal_state_slice(state.root())
        self.assertEqual(
            node_payload["active_item"]["structured_learning"].get("loaded_artifact_origin_report", {}).get("counts"),
            {"primary": 1, "borrowed": 1, "global": 1},
        )


if __name__ == "__main__":
    unittest.main()
