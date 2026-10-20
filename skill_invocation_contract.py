# See MODULES.md for the repository module map before editing.
"""Compatibility facade for the canonical workstation skill invocation contract."""

from workstation.skills.core.invocation_contract import (
    SkillInvocationBinding,
    SkillInvocationRequest,
    SkillInvocationResult,
    _required_input_names,
    skill_invocation_request_from_artifact,
    skill_invocation_result_from_mapping,
)

__all__ = [
    "SkillInvocationBinding",
    "SkillInvocationRequest",
    "SkillInvocationResult",
    "skill_invocation_request_from_artifact",
    "skill_invocation_result_from_mapping",
]
