"""Deterministic authority evaluation over supplied current-use state and grants."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._normalization import collapse_ws


@dataclass(frozen=True, slots=True)
class AuthorityEvaluation:
    """Portable result of evaluating one required authority against grants."""

    allowed: bool
    rationale: str
    required_authority: str = ""
    grant_ids: tuple[str, ...] = ()


def evaluate_authority_grants(
    *,
    effect_kind: Any,
    required_authority: Any,
    admitted: bool,
    admission_reason: Any,
    grants: list[Mapping[str, Any]],
) -> AuthorityEvaluation:
    """Evaluate whether supplied admission and grants cover an authority."""
    authority = collapse_ws(str(required_authority))
    if not admitted:
        return AuthorityEvaluation(
            allowed=False,
            rationale=(
                collapse_ws(str(admission_reason))
                or "Governed skill is not admitted for this effect."
            ),
            required_authority=authority,
        )
    if not authority:
        return AuthorityEvaluation(
            allowed=False,
            rationale=(
                "No governed authority mapping is registered for effect kind "
                f"{effect_kind}."
            ),
        )
    grant_ids = tuple(
        collapse_ws(str(item.get("id", "")))
        for item in grants
        if collapse_ws(str(item.get("authority", ""))) == authority
        and collapse_ws(str(item.get("id", "")))
    )
    if not grant_ids:
        return AuthorityEvaluation(
            allowed=False,
            rationale=(
                f"Runtime grants do not cover required authority {authority} "
                f"for {effect_kind}."
            ),
            required_authority=authority,
        )
    return AuthorityEvaluation(
        allowed=True,
        rationale="Effect request is covered by issued runtime grants.",
        required_authority=authority,
        grant_ids=grant_ids,
    )


__all__ = ["AuthorityEvaluation", "evaluate_authority_grants"]
