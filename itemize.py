# See MODULES.md for the repository module map before editing.
"""Compatibility adapter for canonical subject itemization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from realized_core_semantics.proposals import ProposalType, SupplementMode
from runtime_controller_api import bootstrap_runtime_controller
from workstation.subject.core import itemization as _canonical


# Preserve historical incidental attribute access while canonical consumers use
# the package's explicit public surface.
for _name, _value in vars(_canonical).items():
    if not _name.startswith("_"):
        globals()[_name] = _value


@dataclass(frozen=True)
class _LegacyItemizationProposal:
    proposal_id: str
    source: str
    payload: dict[str, object]


class _LegacyRuntimeItemizationProposalPort:
    """Realize the historical implicit-controller default at the root edge."""

    def request_itemization_proposal(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        target_scope: str,
        instructions: str,
        fallback_payload: dict[str, object],
        schema_hint: dict[str, object],
    ) -> _canonical.ItemizationProposalResult:
        _state, controller = bootstrap_runtime_controller(
            semantic_unit=semantic_unit,
            llm_policy=llm_policy,
        )
        proposal = controller.request_proposal(
            proposal_type=ProposalType.NOT_DECOMPOSITION,
            node=None,
            target_scope=target_scope,
            instructions=instructions,
            fallback_payload=fallback_payload,
            mode=SupplementMode.DEEP,
            schema_hint=schema_hint,
        )
        return _LegacyItemizationProposal(
            proposal_id=str(proposal.id),
            source=str(proposal.source),
            payload=dict(proposal.payload or {}),
        )


def extract_itemized_candidates_from_learning_context(
    root_path: Path,
    context: _canonical.LearningContext,
    *,
    allow_direct_llm_decomposition: bool = False,
    proposal_port: _canonical.ItemizationProposalPort | None = None,
) -> tuple[_canonical.ItemizedSubjectItem, ...]:
    """Preserve the historical controller-backed default at the root facade."""
    effective_port = proposal_port
    if allow_direct_llm_decomposition and effective_port is None:
        effective_port = _LegacyRuntimeItemizationProposalPort()
    return _canonical.extract_itemized_candidates_from_learning_context(
        root_path,
        context,
        allow_direct_llm_decomposition=allow_direct_llm_decomposition,
        proposal_port=effective_port,
    )


def materialize_itemization_session(
    root_path: Path,
    subject_id: str,
    *,
    allow_direct_llm_decomposition: bool = False,
    proposal_port: _canonical.ItemizationProposalPort | None = None,
) -> tuple[_canonical.ItemizationSession, tuple[_canonical.ItemizedSubjectItem, ...]]:
    """Preserve the historical controller-backed default at the root facade."""
    effective_port = proposal_port
    if allow_direct_llm_decomposition and effective_port is None:
        effective_port = _LegacyRuntimeItemizationProposalPort()
    return _canonical.materialize_itemization_session(
        root_path,
        subject_id,
        allow_direct_llm_decomposition=allow_direct_llm_decomposition,
        proposal_port=effective_port,
    )


__all__ = list(_canonical.__all__)
