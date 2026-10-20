# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkstationAttachment:
    name: str
    kind: str
    source: str
    access_mode: str
    mount_path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like workstation session materialization and receipt/export writing, helps with turning one attachment declaration into a stable JSON/TOML-friendly mapping.

        Reference to Theory:
            Supports the workstation attachment contract by keeping named resources explicit rather than ambient.

        Example Input Output:
            Input: `WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main').to_dict()`
            Output: {'name': 'main', 'kind': 'workspace', 'source': '/tmp/project', 'access_mode': 'read_write', 'mount_path': '/workstation/mounts/main', 'metadata': {}}

        Args:
            self: Bound workstation attachment instance.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return asdict(self)


@dataclass(frozen=True)
class TaskBoundaryContract:
    semantic_unit: str
    boundary_shape: tuple[str, ...]
    input_values: dict[str, str]
    read_references: tuple[str, ...]
    write_targets: tuple[str, ...]
    output_values: tuple[str, ...]
    side_effects: tuple[str, ...]
    completion_conditions: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_requirements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like workstation task normalization and receipt persistence, helps with serializing the boundary-complete task contract into a JSON-friendly mapping.

        Reference to Theory:
            Supports BSSC boundary-shape completeness by making the normalized task body explicit for planning and replay.

        Example Input Output:
            Input: `TaskBoundaryContract(semantic_unit='Summarize the report.', boundary_shape=('b*', 'd*'), input_values={}, read_references=('report',), write_targets=(), output_values=('summary',), side_effects=(), completion_conditions=('summary returned',), assumptions=(), missing_requirements=()).to_dict()`
            Output: {'semantic_unit': 'Summarize the report.', 'boundary_shape': ['b*', 'd*'], 'input_values': {}, 'read_references': ['report'], 'write_targets': [], 'output_values': ['summary'], 'side_effects': [], 'completion_conditions': ['summary returned'], 'assumptions': [], 'missing_requirements': []}

        Args:
            self: Bound task-boundary contract instance.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "semantic_unit": self.semantic_unit,
            "boundary_shape": list(self.boundary_shape),
            "input_values": dict(self.input_values),
            "read_references": list(self.read_references),
            "write_targets": list(self.write_targets),
            "output_values": list(self.output_values),
            "side_effects": list(self.side_effects),
            "completion_conditions": list(self.completion_conditions),
            "assumptions": list(self.assumptions),
            "missing_requirements": list(self.missing_requirements),
        }


@dataclass(frozen=True)
class WorkstationSession:
    session_id: str
    root_path: str
    created_at: str
    attachments: tuple[WorkstationAttachment, ...]
    allowed_capabilities: tuple[str, ...]
    openai_profile: str | None
    openai_env_var: str | None
    initial_task: str
    allow_direct_llm_decomposition: bool = True

    def root(self) -> Path:
        """
        High Level Purpose:
            In circumstances like session file materialization and later prompt handling, helps with recovering the session root as a concrete `Path`.

        Reference to Theory:
            Supports the workstation session boundary by keeping the root explicit and reconstructible.

        Example Input Output:
            Input: `WorkstationSession(session_id='ws-1', root_path='/tmp/ws', created_at='2026-04-03T00:00:00+00:00', attachments=(), allowed_capabilities=(), openai_profile=None, openai_env_var=None, initial_task='').root()`
            Output: Path('/tmp/ws')

        Args:
            self: Bound workstation session instance.

        Returns:
            Path: Result produced by `root`.
        """
        return Path(self.root_path)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like workstation session persistence and CLI reporting, helps with turning one session declaration into a stable JSON-friendly mapping.

        Reference to Theory:
            Supports the workstation session contract by making session identity, attachments, and capability scope explicit.

        Example Input Output:
            Input: `WorkstationSession(session_id='ws-1', root_path='/tmp/ws', created_at='2026-04-03T00:00:00+00:00', attachments=(), allowed_capabilities=('ws.repo.tree',), openai_profile='openai_default', openai_env_var='OPENAI_API_KEY', initial_task='Inspect the project.').to_dict()`
            Output: {'session_id': 'ws-1', 'root_path': '/tmp/ws', 'created_at': '2026-04-03T00:00:00+00:00', 'attachments': [], 'allowed_capabilities': ['ws.repo.tree'], 'openai_profile': 'openai_default', 'openai_env_var': 'OPENAI_API_KEY', 'initial_task': 'Inspect the project.'}

        Args:
            self: Bound workstation session instance.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "session_id": self.session_id,
            "root_path": self.root_path,
            "created_at": self.created_at,
            "attachments": [attachment.to_dict() for attachment in self.attachments],
            "allowed_capabilities": list(self.allowed_capabilities),
            "openai_profile": self.openai_profile,
            "openai_env_var": self.openai_env_var,
            "initial_task": self.initial_task,
            "allow_direct_llm_decomposition": bool(self.allow_direct_llm_decomposition),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "WorkstationSession":
        """
        High Level Purpose:
            In circumstances like session reload and prompt resumption, helps with rebuilding the workstation session object from persisted JSON state.

        Reference to Theory:
            Supports the workstation session boundary by making session reload deterministic.

        Example Input Output:
            Input: `WorkstationSession.from_dict({'session_id': 'ws-1', 'root_path': '/tmp/ws', 'created_at': '2026-04-03T00:00:00+00:00', 'attachments': [], 'allowed_capabilities': ['ws.repo.tree'], 'openai_profile': 'openai_default', 'openai_env_var': 'OPENAI_API_KEY', 'initial_task': 'Inspect the project.'})`
            Output: WorkstationSession(session_id='ws-1', root_path='/tmp/ws', created_at='2026-04-03T00:00:00+00:00', attachments=(), allowed_capabilities=('ws.repo.tree',), openai_profile='openai_default', openai_env_var='OPENAI_API_KEY', initial_task='Inspect the project.')

        Args:
            payload: Value for `payload` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            WorkstationSession: Result produced by `from_dict`.
        """
        attachments = tuple(
            WorkstationAttachment(
                name=str(item["name"]),
                kind=str(item["kind"]),
                source=str(item["source"]),
                access_mode=str(item["access_mode"]),
                mount_path=str(item["mount_path"]),
                metadata=dict(item.get("metadata", {})),
            )
            for item in payload.get("attachments", [])
        )
        return cls(
            session_id=str(payload["session_id"]),
            root_path=str(payload["root_path"]),
            created_at=str(payload["created_at"]),
            attachments=attachments,
            allowed_capabilities=tuple(str(item) for item in payload.get("allowed_capabilities", [])),
            openai_profile=payload.get("openai_profile"),
            openai_env_var=payload.get("openai_env_var"),
            initial_task=str(payload.get("initial_task", "")),
            allow_direct_llm_decomposition=bool(payload.get("allow_direct_llm_decomposition", True)),
        )


@dataclass(frozen=True)
class WorkstationDelegationEscalationRequest:
    capability: str
    target: str
    skill_title: str
    requested_delegation: tuple[dict[str, Any], ...]
    rationale: str
    scope: str = "one_invocation"

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like host-owned workstation escalation prompting and receipt writing, helps with serializing one delegated-rights escalation request into a stable JSON-friendly mapping.

        Reference to Theory:
            Supports the workstation escalation model by making requested additional authority explicit, inspectable, and receipt-ready.

        Example Input Output:
            Input: `WorkstationDelegationEscalationRequest(capability='ws.skill.invoke', target='skills', skill_title='Workstation Greeting', requested_delegation=({'capability': 'ws.fs.write', 'target': 'scratch'},), rationale='Need to write a report.').to_dict()`
            Output: {'capability': 'ws.skill.invoke', 'target': 'skills', 'skill_title': 'Workstation Greeting', 'requested_delegation': [{'capability': 'ws.fs.write', 'target': 'scratch'}], 'rationale': 'Need to write a report.', 'scope': 'one_invocation'}

        Args:
            self: Bound escalation-request instance.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "capability": self.capability,
            "target": self.target,
            "skill_title": self.skill_title,
            "requested_delegation": [dict(item) for item in self.requested_delegation],
            "rationale": self.rationale,
            "scope": self.scope,
        }


@dataclass(frozen=True)
class WorkstationDelegationEscalationDecision:
    approved: bool
    scope: str = "one_invocation"
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like host-owned workstation escalation prompting and receipt writing, helps with serializing one escalation decision into a stable JSON-friendly mapping.

        Reference to Theory:
            Supports the workstation escalation model by making approval or denial explicit and replayable.

        Example Input Output:
            Input: `WorkstationDelegationEscalationDecision(approved=True, scope='one_invocation', rationale='User approved.').to_dict()`
            Output: {'approved': True, 'scope': 'one_invocation', 'rationale': 'User approved.'}

        Args:
            self: Bound escalation-decision instance.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "approved": bool(self.approved),
            "scope": self.scope,
            "rationale": self.rationale,
        }
