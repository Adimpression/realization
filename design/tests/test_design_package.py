from __future__ import annotations

import unittest

from design import PACKAGE_DOCS
from design.controllers import (
    DesignCompiler,
    DriftDetector,
    EncodingAdmissibilityChecker,
    EncodingRecompiler,
    ObligationValidator,
    RevisionPlanner,
)
from design.core import (
    InteractionInvariant,
    InteractionObligation,
    Intent,
    RecoverabilityRequirement,
    RiskClass,
    TaskMorphology,
)
from design.reality import EvidenceSeverity, TrustFailure
from design.revision import AlignmentStatus, DesignSnapshot, RealitySnapshot


class DesignPackageTests(unittest.TestCase):
    def _build_obligation(self) -> InteractionObligation:
        return InteractionObligation(
            id="obl_primary_commit",
            name="Primary committed action",
            description="Commit the dominant next action safely and clearly.",
            intent_types=(Intent.TRIGGER, Intent.CONFIRM),
            task_morphologies=(TaskMorphology.ONE_SHOT,),
            invariants=(
                InteractionInvariant.VISIBILITY,
                InteractionInvariant.CONSTRAINT,
                InteractionInvariant.FEEDBACK,
            ),
            risk_class=RiskClass.NORMAL,
            recoverability_requirement=RecoverabilityRequirement.BASIC,
        )

    def test_package_docs_registry_is_exposed(self) -> None:
        self.assertEqual(PACKAGE_DOCS["type_system"], "DESIGN_TYPE_SYSTEM.md")
        self.assertEqual(
            PACKAGE_DOCS["type_system_implementation"],
            "DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md",
        )

    def test_compiler_preserves_obligation_trace_into_material_encoding(self) -> None:
        compiler = DesignCompiler()
        obligation = self._build_obligation()

        encoding = compiler.compile_obligation_to_material_button(obligation)

        self.assertEqual(encoding.embodiment_ref, "obl_primary_commit:action")
        self.assertEqual(encoding.obligation_refs, ("obl_primary_commit",))
        self.assertEqual(encoding.payload["label"], "Primary committed action")
        self.assertEqual(encoding.variant, "filled")

    def test_admissibility_checker_rejects_high_risk_button_encoding(self) -> None:
        compiler = DesignCompiler()
        checker = EncodingAdmissibilityChecker()
        obligation = self._build_obligation()
        encoding = compiler.compile_obligation_to_material_button(obligation)

        admissible, reasons = checker.is_encoding_admissible(
            encoding,
            obligation,
            active_risk_class=RiskClass.CRITICAL,
        )

        self.assertFalse(admissible)
        self.assertIn("risk class critical is not admissible for button", reasons)

    def test_obligation_validator_flags_semantically_incomplete_obligation(self) -> None:
        validator = ObligationValidator()
        obligation = InteractionObligation(
            id="obl_incomplete",
            name="Incomplete",
        )

        errors = validator.validate(obligation)

        self.assertEqual(
            errors,
            (
                "obligation must declare at least one intent",
                "obligation must declare at least one task morphology",
                "obligation must declare at least one invariant",
            ),
        )

    def test_drift_detector_and_revision_planner_require_recompilation(self) -> None:
        compiler = DesignCompiler()
        detector = DriftDetector()
        planner = RevisionPlanner()
        obligation = self._build_obligation()
        encoding = compiler.compile_obligation_to_material_button(obligation)
        snapshot = DesignSnapshot(
            snapshot_id="design_v1",
            obligations=(obligation,),
            encodings=(encoding,),
        )
        reality = RealitySnapshot(
            snapshot_id="reality_v2",
            evidence=(
                TrustFailure(
                    evidence_id="ev_trust_1",
                    actor_or_system_source="operators",
                    observed_fact="Users no longer trust the action because it commits too early.",
                    affected_encoding_refs=(encoding.encoding_id,),
                    affected_obligation_refs=(obligation.id,),
                    severity=EvidenceSeverity.HIGH,
                ),
            ),
        )

        drift = detector.detect(snapshot, reality)
        plan = planner.plan_recompilation(drift)

        self.assertEqual(len(drift.alignment_checks), 1)
        self.assertEqual(
            drift.alignment_checks[0].status,
            AlignmentStatus.INVALIDATED,
        )
        self.assertTrue(plan.required)
        self.assertEqual(plan.affected_encoding_refs, (encoding.encoding_id,))

    def test_encoding_recompiler_preserves_existing_trace_and_appends_revision(self) -> None:
        compiler = DesignCompiler()
        recompiler = EncodingRecompiler()
        obligation = self._build_obligation()
        encoding = compiler.compile_obligation_to_material_button(obligation)

        revised = recompiler.recompile_material_button(
            encoding,
            variant="tonal",
            additional_trace_ref="rev_01",
        )

        self.assertEqual(revised.variant, "tonal")
        self.assertEqual(revised.trace_refs, ("obl_primary_commit", "rev_01"))


if __name__ == "__main__":
    unittest.main()
