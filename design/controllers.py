"""Controller utilities for typed design mediation."""

from __future__ import annotations

from dataclasses import replace

from .core import InteractionObligation, InteractionInvariant, RiskClass
from .embodiment import (
    ActionEmbodiment,
    DesignEmbodiment,
    EmbodimentKind,
    SelectionEmbodiment,
)
from .framework.material import MaterialButtonEncoding
from .reality import EvidenceSeverity, RealityEvidence
from .revision import (
    AlignmentCheck,
    AlignmentStatus,
    DesignSnapshot,
    DriftReport,
    InvalidatedEncoding,
    RealitySnapshot,
    RecompilationRequired,
)


class ObligationValidator:
    """Validate minimal semantic completeness of an obligation."""

    def validate(self, obligation: InteractionObligation) -> tuple[str, ...]:
        errors: list[str] = []
        if not obligation.intent_types:
            errors.append("obligation must declare at least one intent")
        if not obligation.task_morphologies:
            errors.append("obligation must declare at least one task morphology")
        if not obligation.invariants:
            errors.append("obligation must declare at least one invariant")
        return tuple(errors)


class DesignCompiler:
    """Compile obligations into embodiments and framework encodings."""

    def compile_obligation_to_embodiment(
        self,
        obligation: InteractionObligation,
        *,
        kind: EmbodimentKind = EmbodimentKind.ACTION,
        name: str | None = None,
    ) -> DesignEmbodiment:
        embodiment_name = name or obligation.name
        common = {
            "embodiment_id": f"{obligation.id}:{kind.value}",
            "name": embodiment_name,
            "obligation_refs": (obligation.id,),
            "invariant_refs": tuple(invariant.value for invariant in obligation.invariants),
            "risk_class": obligation.risk_class,
            "recoverability_posture": obligation.recoverability_requirement,
            "constraints": obligation.constraint_refs,
        }
        if kind is EmbodimentKind.ACTION:
            return ActionEmbodiment(**common)
        if kind is EmbodimentKind.SELECTION:
            return SelectionEmbodiment(**common)
        raise ValueError(f"unsupported embodiment kind: {kind}")

    def compile_embodiment_to_material_button(
        self,
        embodiment: DesignEmbodiment,
        *,
        variant: str = "filled",
        admissible_risk_classes: tuple[RiskClass, ...] = (
            RiskClass.LOW,
            RiskClass.NORMAL,
        ),
    ) -> MaterialButtonEncoding:
        if embodiment.kind not in (EmbodimentKind.ACTION, EmbodimentKind.SELECTION):
            raise ValueError(
                "material button encodings require an action or selection embodiment"
            )
        return MaterialButtonEncoding(
            encoding_id=f"{embodiment.embodiment_id}:material_button",
            embodiment_ref=embodiment.embodiment_id,
            obligation_refs=embodiment.obligation_refs,
            required_invariant_refs=tuple(
                InteractionInvariant(value) for value in embodiment.invariant_refs
            ),
            admissible_risk_classes=admissible_risk_classes,
            payload={"label": embodiment.name},
            trace_refs=embodiment.obligation_refs,
            variant=variant,
        )

    def compile_obligation_to_material_button(
        self,
        obligation: InteractionObligation,
        *,
        variant: str = "filled",
    ) -> MaterialButtonEncoding:
        embodiment = self.compile_obligation_to_embodiment(obligation)
        return self.compile_embodiment_to_material_button(
            embodiment,
            variant=variant,
        )


class EncodingAdmissibilityChecker:
    """Check whether a framework encoding is semantically admissible."""

    def is_encoding_admissible(
        self,
        encoding: MaterialButtonEncoding,
        obligation: InteractionObligation,
        *,
        active_risk_class: RiskClass | None = None,
    ) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        required = set(encoding.required_invariant_refs)
        available = set(obligation.invariants)
        missing = required - available
        if missing:
            reasons.append(
                "missing required invariants: "
                + ", ".join(sorted(invariant.value for invariant in missing))
            )
        effective_risk = active_risk_class or obligation.risk_class
        if effective_risk not in encoding.admissible_risk_classes:
            reasons.append(
                f"risk class {effective_risk.value} is not admissible for "
                f"{encoding.component_type}"
            )
        return (not reasons, tuple(reasons))


class RealityAlignmentChecker:
    """Check whether runtime evidence still supports an encoding."""

    def check_alignment(
        self,
        encoding: MaterialButtonEncoding,
        evidence: tuple[RealityEvidence, ...],
    ) -> AlignmentCheck:
        reasons: list[str] = []
        evidence_refs: list[str] = []
        status = AlignmentStatus.ALIGNED
        for observation in evidence:
            if encoding.encoding_id not in observation.affected_encoding_refs:
                continue
            evidence_refs.append(observation.evidence_id)
            reasons.append(observation.observed_fact)
            if observation.severity in (
                EvidenceSeverity.HIGH,
                EvidenceSeverity.CRITICAL,
            ):
                status = AlignmentStatus.INVALIDATED
            elif status is AlignmentStatus.ALIGNED:
                status = AlignmentStatus.DRIFTED
        return AlignmentCheck(
            encoding_ref=encoding.encoding_id,
            status=status,
            reasons=tuple(reasons),
            evidence_refs=tuple(evidence_refs),
            obligation_refs=encoding.obligation_refs,
        )


class DriftDetector:
    """Detect design drift between encodings and reality evidence."""

    def __init__(self, alignment_checker: RealityAlignmentChecker | None = None) -> None:
        self._alignment_checker = alignment_checker or RealityAlignmentChecker()

    def detect(
        self,
        design_snapshot: DesignSnapshot,
        reality_snapshot: RealitySnapshot,
    ) -> DriftReport:
        checks = tuple(
            self._alignment_checker.check_alignment(
                encoding,
                reality_snapshot.evidence,
            )
            for encoding in design_snapshot.encodings
        )
        invalidated = tuple(
            InvalidatedEncoding(
                encoding_ref=check.encoding_ref,
                reasons=check.reasons,
                evidence_refs=check.evidence_refs,
                obligation_refs=check.obligation_refs,
            )
            for check in checks
            if check.status is AlignmentStatus.INVALIDATED
        )
        reasons = tuple(
            reason
            for check in checks
            if check.status is not AlignmentStatus.ALIGNED
            for reason in check.reasons
        )
        affected_encodings = tuple(
            check.encoding_ref
            for check in checks
            if check.status is not AlignmentStatus.ALIGNED
        )
        affected_obligations = tuple(
            obligation_ref
            for check in checks
            for obligation_ref in check.obligation_refs
            if check.status is not AlignmentStatus.ALIGNED
        )
        recompilation = RecompilationRequired(
            required=bool(affected_encodings),
            affected_encoding_refs=affected_encodings,
            affected_obligation_refs=affected_obligations,
            reasons=reasons,
        )
        return DriftReport(
            report_id=f"{design_snapshot.snapshot_id}:{reality_snapshot.snapshot_id}:drift",
            alignment_checks=checks,
            invalidated_encodings=invalidated,
            recompilation=recompilation,
        )


class RevisionPlanner:
    """Turn drift signals into a concrete recompilation requirement."""

    def plan_recompilation(self, drift_report: DriftReport) -> RecompilationRequired:
        return drift_report.recompilation


class EncodingRecompiler:
    """Produce revised encodings without breaking the mediation chain."""

    def recompile_material_button(
        self,
        encoding: MaterialButtonEncoding,
        *,
        variant: str | None = None,
        additional_trace_ref: str | None = None,
    ) -> MaterialButtonEncoding:
        trace_refs = encoding.trace_refs
        if additional_trace_ref:
            trace_refs = trace_refs + (additional_trace_ref,)
        return replace(
            encoding,
            variant=variant or encoding.variant,
            trace_refs=trace_refs,
        )

