# See MODULES.md for the repository module map before editing.
"""Compatibility facade for canonical portable skill invocation records."""

from realized_skill_semantics.invocation import (
    SkillInvocationBinding,
    SkillInvocationRequest,
    SkillInvocationResult,
    required_skill_input_names,
    skill_invocation_result_from_mapping,
)
from workstation.skills.core.invocation_contract import (
    _required_input_names,
    skill_invocation_request_from_artifact,
)

__all__ = [
    "SkillInvocationBinding",
    "SkillInvocationRequest",
    "SkillInvocationResult",
    "required_skill_input_names",
    "skill_invocation_request_from_artifact",
    "skill_invocation_result_from_mapping",
]
