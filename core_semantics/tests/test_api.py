from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from realized_core_semantics import (
    applied_model,
    applied_primitives,
    artifacts,
    boundary,
    decision_review,
    executors,
    identifiers,
    itemization,
    markdown,
    normalization,
    prolog,
    proposals,
    semantic_text,
    theory,
    title_semantics,
    transformation_constructs,
    values,
)


class _ArtifactProbe:
    title = "Probe"
    content: Mapping[str, object] = {"answer": "stable"}


class _ProjectionKind(Enum):
    STABLE = "stable"


@dataclass
class _ProjectionRecord:
    kind: _ProjectionKind
    payload: bytes


class CoreSemanticsApiTests(unittest.TestCase):
    def test_package_exports_only_the_cohesive_contract_modules(self) -> None:
        import realized_core_semantics

        self.assertEqual(
            [
                "applied_model",
                "applied_primitives",
                "artifacts",
                "boundary",
                "decision_review",
                "executors",
                "identifiers",
                "itemization",
                "markdown",
                "normalization",
                "prolog",
                "proposals",
                "semantic_text",
                "theory",
                "title_semantics",
                "transformation_constructs",
                "values",
            ],
            realized_core_semantics.__all__,
        )
        self.assertIs(realized_core_semantics.artifacts, artifacts)
        self.assertIs(realized_core_semantics.applied_model, applied_model)
        self.assertIs(realized_core_semantics.applied_primitives, applied_primitives)
        self.assertIs(realized_core_semantics.boundary, boundary)
        self.assertIs(realized_core_semantics.decision_review, decision_review)
        self.assertIs(realized_core_semantics.executors, executors)
        self.assertIs(realized_core_semantics.identifiers, identifiers)
        self.assertIs(realized_core_semantics.itemization, itemization)
        self.assertIs(realized_core_semantics.markdown, markdown)
        self.assertIs(realized_core_semantics.normalization, normalization)
        self.assertIs(realized_core_semantics.prolog, prolog)
        self.assertIs(realized_core_semantics.proposals, proposals)
        self.assertIs(realized_core_semantics.semantic_text, semantic_text)
        self.assertIs(realized_core_semantics.theory, theory)
        self.assertIs(realized_core_semantics.title_semantics, title_semantics)
        self.assertIs(
            realized_core_semantics.transformation_constructs,
            transformation_constructs,
        )
        self.assertIs(realized_core_semantics.values, values)

    def test_module_exports_are_explicit_unique_and_resolvable(self) -> None:
        for module in (
            applied_model,
            applied_primitives,
            artifacts,
            boundary,
            decision_review,
            executors,
            identifiers,
            itemization,
            markdown,
            normalization,
            prolog,
            proposals,
            semantic_text,
            theory,
            title_semantics,
            transformation_constructs,
            values,
        ):
            with self.subTest(module=module.__name__):
                self.assertEqual(len(module.__all__), len(set(module.__all__)))
                for name in module.__all__:
                    self.assertTrue(hasattr(module, name), name)

    def test_proposal_vocabulary_preserves_names_order_and_values(self) -> None:
        self.assertEqual(
            [("FAST", "fast"), ("DEEP", "deep")],
            [(item.name, item.value) for item in proposals.SupplementMode],
        )
        self.assertEqual(
            [
                ("SUGGESTED", "suggested"),
                ("ADMITTED", "admitted"),
                ("REVISED", "revised"),
                ("REJECTED", "rejected"),
                ("HOLDON", "holdon"),
                ("ESCALATED", "escalated"),
            ],
            [
                (item.name, item.value)
                for item in proposals.ProposalGovernanceStatus
            ],
        )
        self.assertEqual(25, len(proposals.ProposalType))
        self.assertEqual(
            ("SEMANTIC_TARGET", "SemanticTargetProposal"),
            (
                next(iter(proposals.ProposalType)).name,
                next(iter(proposals.ProposalType)).value,
            ),
        )
        self.assertEqual(
            ("DST_NORMALIZATION", "DstNormalizationProposal"),
            (
                list(proposals.ProposalType)[-1].name,
                list(proposals.ProposalType)[-1].value,
            ),
        )

    def test_identifier_helpers_preserve_slug_and_id_shapes(self) -> None:
        self.assertEqual("compute-force-fr", identifiers.slugify("Compute force from mass and acceleration.", limit=16))
        self.assertEqual("item", identifiers.slugify("!!!"))
        with patch.object(
            identifiers.uuid,
            "uuid4",
            side_effect=[
                SimpleNamespace(hex="1234567890abcdef"),
                SimpleNamespace(hex="abcdef1234567890"),
            ],
        ):
            self.assertEqual("run_12345678_abcdef", identifiers.make_id("run"))
        with patch.object(
            identifiers.uuid,
            "uuid4",
            return_value=SimpleNamespace(hex="fedcba9876543210"),
        ):
            self.assertEqual(
                "artifact_force-from-mass-and-acceleration_fedcba",
                identifiers.make_id("artifact", "force-from-mass-and-acceleration"),
            )
        self.assertEqual(
            "smart-city-travel",
            identifiers.canonical_learning_subject_id("  Smart City Travel  "),
        )
        self.assertEqual(
            "item",
            identifiers.canonical_learning_subject_id("!!!"),
        )

    def test_subject_semantic_values_preserve_projection_shapes(self) -> None:
        item = itemization.ItemizedSubjectItem.from_dict(
            {
                "itemized_item_id": " item-1 ",
                "subject_id": "Smart City Travel",
                "item_kind": "decision role candidate",
                "canonical_label": " City regulator ",
                "aliases": ["regulator", "regulator", ""],
                "confidence": 2,
                "metadata": {"decision_role": "ACTOR"},
            }
        )
        self.assertEqual("smart-city-travel", item.subject_id)
        self.assertEqual("decision_role_candidate", item.item_kind)
        self.assertEqual(("regulator",), item.aliases)
        self.assertEqual(1.0, item.confidence)
        self.assertEqual("actor", item.metadata["decision_role"])

        candidates = transformation_constructs.deterministic_transformation_construct_candidates_from_itemized_item(
            item,
            build_epoch_ms=7,
            review_item_id="review-1",
        )
        self.assertEqual(1, len(candidates))
        candidate = candidates[0]
        self.assertEqual("actor", candidate.sort_kind)
        self.assertEqual(0.92, candidate.confidence)
        self.assertEqual("review-1", candidate.review_item_id)

        frame = decision_review.DecisionFrame.from_dict(
            {
                "decision_frame_id": " frame-1 ",
                "subject_id": "Smart City Travel",
                "question": "Which path?",
                "status": "ACTIVE",
            }
        )
        self.assertEqual("smart-city-travel", frame.subject_id)
        self.assertEqual("active", frame.status)

    def test_artifact_protocols_remain_runtime_checkable(self) -> None:
        probe = _ArtifactProbe()

        self.assertIsInstance(probe, artifacts.ArtifactContentView)
        self.assertIsInstance(probe, artifacts.TitledArtifactContentView)

    def test_non_achievedness_serialization_is_stable(self) -> None:
        value = theory.NonAchievedness(
            id="not-1",
            semantic_unit="publish the report",
            success_criteria=["report exists"],
            misalignment_types=[theory.NonAchievednessMisalignmentKind.COMPLETION],
            degree=theory.NonAchievednessDegreeKind.PARTIAL,
            boundary_shape=[theory.BoundaryShapeTermKind.OUTPUT_REFERENCE],
        )
        expected = {
            "actual_realization": "",
            "admissibility_condition": "",
            "blocker_ids": [],
            "boundary_shape": ["d'*"],
            "certainty_state_id": None,
            "child_not_ids": [],
            "current_status": "open",
            "degree": "partial",
            "description": "",
            "distorted_components": [],
            "full_repair": [],
            "holdon_ids": [],
            "id": "not-1",
            "intended_object": "",
            "minimal_repair": [],
            "misalignment_types": ["completion"],
            "missing_components": [],
            "origin_layers": [],
            "parent_not_id": None,
            "relevance_to_parent": "",
            "remainder_shapes": [],
            "semantic_unit": "publish the report",
            "semantic_unit_id": None,
            "success_criteria": ["report exists"],
            "why_it_matters": [],
        }

        self.assertEqual(expected, value.model_dump(mode="json"))
        self.assertEqual(
            value,
            theory.NonAchievedness.model_validate_json(value.model_dump_json()),
        )

    def test_formal_system_alias_order_is_stable(self) -> None:
        payload = theory.FormalSystem().model_dump(mode="json", by_alias=True)

        self.assertEqual(
            [
                "N", "D", "O", "E", "C", "K", "A", "Sigma", "H",
                "G", "I", "P", "T", "HoldOn", "R", "E_C", "B",
            ],
            list(payload),
        )
        self.assertEqual(
            payload,
            json.loads(theory.FormalSystem().model_dump_json(by_alias=True)),
        )

    def test_theory_models_still_reject_unknown_fields(self) -> None:
        with self.assertRaises(ValidationError):
            theory.SemanticUnit(id="unit-1", text="value", unexpected=True)

    def test_json_safe_projects_supported_runtime_values_recursively(self) -> None:
        value = {
            7: _ProjectionRecord(
                kind=_ProjectionKind.STABLE,
                payload=b"payload",
            ),
            "nested": (bytearray(b"first"), {"second"}),
        }

        self.assertEqual(
            {
                "7": {"kind": "stable", "payload": "payload"},
                "nested": ["first", ["second"]],
            },
            values.json_safe(value),
        )

    def test_utc_now_returns_a_second_precision_utc_timestamp(self) -> None:
        timestamp = values.utc_now()
        parsed = datetime.fromisoformat(timestamp)

        self.assertEqual(timezone.utc, parsed.tzinfo)
        self.assertEqual(0, parsed.microsecond)

    def test_values_import_does_not_load_the_formal_model_dependency(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "from realized_core_semantics.values import json_safe; "
                    "assert 'pydantic' not in sys.modules; "
                    "assert json_safe(b'payload') == 'payload'"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)


if __name__ == "__main__":
    unittest.main()
