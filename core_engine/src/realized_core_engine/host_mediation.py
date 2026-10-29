# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from realized_core_semantics.applied_model import Artifact, CrossBoundaryResult, json_safe, utc_now
from realized_core_runtime.capabilities import (
    issue_capability_grants_for_artifact,
    required_authority_for_effect_kind,
)
from realized_core_runtime.execution import (
    normalize_ability_runtime_content,
)
from realized_host_interaction.context import (
    host_interaction_virtual_mounts,
    host_interaction_workspace_root,
    host_realizer_provider,
)
from realized_host_interaction.realizers import (
    EMPTY_HOST_REALIZER_PROVIDER,
    HostBrokerInvocation,
    HostExecutorInvocation,
    HostRealizerProvider,
    HostRealizerUnavailableError,
)
from realized_skill_semantics.execution import normalize_executor_framework_name
from realized_core_runtime.host_abi import host_abi_version
from realized_core_engine.runtime_governance_context import (
    EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
    evaluate_runtime_authority_grants,
    runtime_artifact_governance_context,
    runtime_artifact_trace_context,
    runtime_effect_trace_receipt as _effect_receipt,
)
from realized_core_semantics.semantic_text import collapse_ws


@dataclass
class EffectRequest:
    effect_kind: str
    artifact_id: str
    artifact_title: str
    semantic_unit: str
    executor_framework: str
    invocation_payload: Any
    realizer_kind: str = ""
    realizer_identity: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime host mediation for skill effects, helps with expressing one requested effect as a durable typed record before any boundary action occurs.

        Reference to Theory:
            Supports bundle-style host mediation by making each material effect request explicit and inspectable before execution.

        Example Input Output:
            Input: `to_dict()`
            Output: {'effect_kind': 'execute.python3', 'artifact_id': 'artifact-force-function', 'executor_framework': 'python3'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)


@dataclass
class EffectDecision:
    allowed: bool
    rationale: str
    required_authority: str = ""
    grant_ids: list[str] = field(default_factory=list)
    evaluated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime host mediation for governed skills, helps with serializing the allow-or-deny decision attached to one effect request.

        Reference to Theory:
            Supports open governance by preserving the policy-and-authority decision that stood between a skill and a material host effect.

        Example Input Output:
            Input: `to_dict()`
            Output: {'allowed': True, 'rationale': 'Effect request is covered by issued runtime grants.', 'required_authority': 'execute'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)


def _active_realizer_provider(self) -> HostRealizerProvider:
    return (
        host_realizer_provider(getattr(self, "host_interaction_context", None))
        or EMPTY_HOST_REALIZER_PROVIDER
    )


def _declared_host_brokers(artifact: Artifact) -> tuple[str, ...]:
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    raw_brokers = content.get("governed_host_brokers", [])
    if not isinstance(raw_brokers, Sequence) or isinstance(
        raw_brokers,
        (str, bytes, bytearray),
    ):
        return ()
    return tuple(
        dict.fromkeys(
            collapse_ws(str(item))
            for item in raw_brokers
            if collapse_ws(str(item))
        )
    )


def _uses_strict_realizer_declaration(artifact: Artifact) -> bool:
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    return collapse_ws(str(content.get("skill_schema", ""))) == "bssc_skill.v2"


def _preflight_executor_realizer(
    self,
    *,
    artifact: Artifact,
    declaration: Mapping[str, Any],
    executor_identity: str,
) -> tuple[bool, str, dict[str, Any]]:
    declared_executor = normalize_executor_framework_name(
        declaration.get("executor_framework", "")
    )
    if declared_executor and declared_executor != executor_identity:
        rationale = (
            f"Declared executor framework {declared_executor} does not match requested "
            f"effect framework {executor_identity}."
        )
        return False, rationale, {
            "kind": "executor",
            "identity": executor_identity,
            "binding_status": "declaration_mismatch",
            "rationale": rationale,
        }
    provider = _active_realizer_provider(self)
    inspection = provider.inspect_executor(executor_identity)
    evidence: dict[str, Any] = {
        "kind": "executor",
        "identity": executor_identity,
        "binding_status": "available" if inspection.available else "unavailable",
        "inspection": inspection.to_dict(),
    }
    if not inspection.registered or not inspection.available:
        return False, inspection.rationale, evidence
    broker_inspections = [
        provider.inspect_broker(identity)
        for identity in _declared_host_brokers(artifact)
    ]
    evidence["declared_broker_requirements"] = [
        item.to_dict() for item in broker_inspections
    ]
    unavailable = next(
        (
            item
            for item in broker_inspections
            if not item.registered or not item.available
        ),
        None,
    )
    if unavailable is not None:
        rationale = (
            f"Declared nested broker {unavailable.identity!r} is not available: "
            f"{unavailable.rationale}"
        )
        evidence["binding_status"] = "nested_broker_unavailable"
        evidence["rationale"] = rationale
        return False, rationale, evidence
    return True, inspection.rationale, evidence


def _preflight_broker_realizer(
    self,
    *,
    artifact: Artifact,
    broker_identity: str,
) -> tuple[bool, str, dict[str, Any]]:
    declared_brokers = _declared_host_brokers(artifact)
    if _uses_strict_realizer_declaration(artifact) and broker_identity not in declared_brokers:
        rationale = (
            f"Skill declaration does not bind the exact host broker {broker_identity!r}."
        )
        return False, rationale, {
            "kind": "broker",
            "identity": broker_identity,
            "binding_status": "undeclared",
            "declared_brokers": list(declared_brokers),
            "rationale": rationale,
        }
    inspection = _active_realizer_provider(self).inspect_broker(broker_identity)
    evidence = {
        "kind": "broker",
        "identity": broker_identity,
        "binding_status": "available" if inspection.available else "unavailable",
        "declared_brokers": list(declared_brokers),
        "inspection": inspection.to_dict(),
    }
    if not inspection.registered or not inspection.available:
        return False, inspection.rationale, evidence
    return True, inspection.rationale, evidence


def _runtime_broker_governance_context(
    self,
    *,
    artifact: Artifact,
    declaration: Mapping[str, Any] | None,
    grants: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like broker-mediated data governance, helps with assembling the runtime context needed by governed mounts, named queries, and per-skill state surfaces.

    Reference to Theory:
        Supports bundle-style data governance by carrying current declaration, grants, store path, and governed data handles into the broker layer without exposing raw host resources directly.

    Example Input Output:
        Input: `_runtime_broker_governance_context(self=controller, artifact=Artifact(id='artifact-demo', title='Demo', artifact_type='ability', representation='python_script'), declaration={'data_classes_touched': ['public']}, grants=[{'authority': 'read'}])`
        Output: {'artifact_id': 'artifact-demo', 'sqlite_path': '/repo/state/common.sqlite3', 'virtual_mounts': {}, 'named_queries': {}}

    Args:
        self: Bound controller instance that owns runtime state and store wiring.
        artifact: Value for `artifact` used by `_runtime_broker_governance_context`. Expected type: `Artifact`.
        declaration: Value for `declaration` used by `_runtime_broker_governance_context`. Expected type: `Mapping[str, Any] | None`.
        grants: Value for `grants` used by `_runtime_broker_governance_context`. Expected type: `list[Mapping[str, Any]]`.

    Returns:
        dict[str, Any]: Result produced by `_runtime_broker_governance_context`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    sqlite_path = collapse_ws(
        str(
            getattr(self.artifact_store, "sqlite_path", "")
            or getattr(getattr(self.artifact_store, "fallback_store", None), "sqlite_path", "")
            or os.getenv("STATE_SQLITE_PATH", "")
        )
    )
    backend_context = getattr(self, "host_interaction_context", None)
    attachment_mounts = host_interaction_virtual_mounts(backend_context)
    explicit_mounts = dict(content.get("virtual_mounts", {})) if isinstance(content.get("virtual_mounts", {}), Mapping) else {}
    merged_mounts = dict(attachment_mounts)
    merged_mounts.update(explicit_mounts)
    return {
        "artifact_id": str(getattr(artifact, "id", "")),
        "artifact_title": collapse_ws(str(getattr(artifact, "title", ""))),
        "host_abi_version": host_abi_version(),
        "sqlite_path": sqlite_path,
        "workspace_root": host_interaction_workspace_root(backend_context, fallback_root=os.getcwd()),
        "declaration": dict(declaration) if isinstance(declaration, Mapping) else {},
        "grants": [dict(item) for item in grants if isinstance(item, Mapping)],
        "virtual_mounts": merged_mounts,
        "named_queries": dict(content.get("named_queries", {})) if isinstance(content.get("named_queries", {}), Mapping) else {},
        "skill_state_namespace": collapse_ws(str(content.get("skill_state_namespace", ""))) or str(getattr(artifact, "id", "")),
    }


def evaluate_effect_request(
    request: EffectRequest,
    *,
    declaration: Mapping[str, Any] | None,
    admitted: bool,
    admission_reason: str,
    grants: list[Mapping[str, Any]],
) -> EffectDecision:
    """
    High Level Purpose:
        In circumstances like governed execution of Python, bash, or ansible skills, helps with deciding whether the requested host effect is permitted under the current declaration, admission state, and issued grants.

    Reference to Theory:
        Supports open governance sections 8, 9, and 10 by turning declaration and admission into an actual runtime allow-or-deny gate.

    Example Input Output:
        Input: `evaluate_effect_request(request=EffectRequest(effect_kind='execute.python3', artifact_id='artifact-force-function', artifact_title='Force from mass and acceleration', semantic_unit='Calculate force from mass=3 and acceleration=4.', executor_framework='python3', invocation_payload={'mass': 3, 'acceleration': 4}), declaration={'authorities_requested': ['execute'], 'executor_framework': 'python3'}, admitted=True, admission_reason='', grants=[{'id': 'grant-1f2e3d4c5b6a', 'authority': 'execute'}])`
        Output: EffectDecision(allowed=True, rationale='Effect request is covered by issued runtime grants.', required_authority='execute')

    Args:
        request: Value for `request` used by `evaluate_effect_request`. Expected type: `EffectRequest`.
        declaration: Value for `declaration` used by `evaluate_effect_request`. Expected type: `Mapping[str, Any] | None`.
        admitted: Value for `admitted` used by `evaluate_effect_request`. Expected type: `bool`.
        admission_reason: Value for `admission_reason` used by `evaluate_effect_request`. Expected type: `str`.
        grants: Value for `grants` used by `evaluate_effect_request`. Expected type: `list[Mapping[str, Any]]`.

    Returns:
        EffectDecision: Result produced by `evaluate_effect_request`.
    """
    required_authority = required_authority_for_effect_kind(request.effect_kind)
    authority_evaluation = evaluate_runtime_authority_grants(
        effect_kind=request.effect_kind,
        required_authority=required_authority,
        admitted=admitted,
        admission_reason=admission_reason,
        grants=grants,
    )
    if not authority_evaluation.allowed:
        return EffectDecision(
            allowed=False,
            rationale=authority_evaluation.rationale,
            required_authority=authority_evaluation.required_authority,
            grant_ids=list(authority_evaluation.grant_ids),
        )
    grant_ids = list(authority_evaluation.grant_ids)
    declared = dict(declaration) if isinstance(declaration, Mapping) else {}
    declared_executor = normalize_executor_framework_name(declared.get("executor_framework", ""))
    if declared_executor and request.executor_framework and declared_executor != request.executor_framework:
        return EffectDecision(
            allowed=False,
            rationale=(
                f"Declared executor framework {declared_executor} does not match requested effect "
                f"framework {request.executor_framework}."
            ),
            required_authority=required_authority,
            grant_ids=grant_ids,
        )
    return EffectDecision(
        allowed=True,
        rationale=authority_evaluation.rationale,
        required_authority=authority_evaluation.required_authority,
        grant_ids=grant_ids,
    )


def record_effect_trace(
    self,
    *,
    artifact: Artifact,
    request: EffectRequest,
    decision: EffectDecision,
    grants: list[Mapping[str, Any]],
    admission_snapshot: Mapping[str, Any] | None = None,
    lifecycle_snapshot: Mapping[str, Any] | None = None,
    realizer_evidence: Mapping[str, Any] | None = None,
    result: CrossBoundaryResult | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed host mediation around skill execution, helps with preserving one constitutional effect trace record that joins request, decision, grants, and outcome.

    Reference to Theory:
        Supports open governance trace requirements by making declaration-derived authority use visible at the level of each material effect.

    Example Input Output:
        Input: `record_effect_trace(self=controller, artifact=Artifact(id='artifact-force-function', title='Force from mass and acceleration', artifact_type='ability', representation='python_script'), request=EffectRequest(effect_kind='execute.python3', artifact_id='artifact-force-function', artifact_title='Force from mass and acceleration', semantic_unit='Calculate force from mass=3 and acceleration=4.', executor_framework='python3', invocation_payload={'mass': 3, 'acceleration': 4}), decision=EffectDecision(allowed=True, rationale='Effect request is covered by issued runtime grants.', required_authority='execute'), grants=[{'id': 'grant-1f2e3d4c5b6a', 'authority': 'execute'}], result=CrossBoundaryResult(ok=True, command=['uv'], exit_code=0, stdout='{}', stderr=''))`
        Output: {'id': 'effect-abc123', 'effect_kind': 'execute.python3', 'allowed': True, 'artifact_id': 'artifact-force-function'}

    Args:
        self: Bound controller instance that owns runtime state and step recording.
        artifact: Value for `artifact` used by `record_effect_trace`. Expected type: `Artifact`.
        request: Value for `request` used by `record_effect_trace`. Expected type: `EffectRequest`.
        decision: Value for `decision` used by `record_effect_trace`. Expected type: `EffectDecision`.
        grants: Value for `grants` used by `record_effect_trace`. Expected type: `list[Mapping[str, Any]]`.
        admission_snapshot: Value for `admission_snapshot` used by `record_effect_trace`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        result: Value for `result` used by `record_effect_trace`. Expected type: `CrossBoundaryResult | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `record_effect_trace`.
    """
    trace_seed = (
        f"{artifact.id}|{request.effect_kind}|{request.created_at}|"
        f"{decision.allowed}|{result.exit_code if result is not None else 'denied'}"
    )
    trace_id = f"effect-{hashlib.sha1(trace_seed.encode('utf-8')).hexdigest()[:12]}"
    trace_context = runtime_artifact_trace_context(
        artifact,
        admission_snapshot=admission_snapshot,
        lifecycle_snapshot=lifecycle_snapshot,
    )
    trace = {
        "id": trace_id,
        "created_at": utc_now(),
        "host_abi_version": host_abi_version(),
        "artifact_id": str(getattr(artifact, "id", "")),
        "artifact_title": collapse_ws(str(getattr(artifact, "title", ""))),
        "request": request.to_dict(),
        "decision": decision.to_dict(),
        "grants": [dict(item) for item in grants if isinstance(item, Mapping)],
        "grant_ids": [collapse_ws(str(item.get("id", ""))) for item in grants if collapse_ws(str(item.get("id", "")))],
        "declaration": dict(trace_context.get("declaration", {})) if isinstance(trace_context.get("declaration", {}), Mapping) else {},
        "admission": dict(trace_context.get("admission", {})) if isinstance(trace_context.get("admission", {}), Mapping) else {},
        "lifecycle": dict(trace_context.get("lifecycle", {})) if isinstance(trace_context.get("lifecycle", {}), Mapping) else {},
        "result": {
            "ok": bool(result.ok) if result is not None else False,
            "exit_code": int(result.exit_code) if result is not None else 1,
            "answer": str(result.answer) if result is not None else "",
            "stderr": str(result.stderr) if result is not None else "",
            "notes": list(result.notes) if result is not None else [],
        },
    }
    if isinstance(realizer_evidence, Mapping):
        trace["realizer"] = json_safe(dict(realizer_evidence))
    trace["receipts"] = {
        "request": _effect_receipt(
            "request",
            {
                "effect_kind": request.effect_kind,
                "executor_framework": request.executor_framework,
                "invocation_payload": request.invocation_payload,
            },
        ),
        "declaration": _effect_receipt("declaration", trace["declaration"]),
        "policy": _effect_receipt(
            "policy",
            {
                "policy_titles": list(trace["admission"].get("policy_titles", [])),
                "required_approval_class": trace["admission"].get("required_approval_class", "automatic"),
            },
        ),
        "approval": _effect_receipt(
            "approval",
            {
                "approval_titles": list(trace["admission"].get("approval_titles", [])),
                "required_approval_class": trace["admission"].get("required_approval_class", "automatic"),
            },
        ),
        "lifecycle": _effect_receipt("lifecycle", trace["lifecycle"]),
        "grants": _effect_receipt("grants", grants),
    }
    if "realizer" in trace:
        trace["receipts"]["realizer"] = _effect_receipt(
            "realizer",
            trace["realizer"],
        )
    self.state.effect_traces.append(json_safe(trace))
    self.state.record_step(
        kind="host_effect_mediation",
        node_id=self.state.root_id,
        intent="Mediate material host effects through declared authority, admission, and issued capability grants.",
        action=f"mediate {request.effect_kind}",
        result="effect allowed" if decision.allowed else "effect denied",
        evaluation=decision.rationale,
        payload={
            "trace_id": trace_id,
            "artifact_id": artifact.id,
            "effect_kind": request.effect_kind,
            "allowed": decision.allowed,
            "grant_ids": trace["grant_ids"],
            "exit_code": trace["result"]["exit_code"],
        },
    )
    return trace


def execute_mediated_artifact_effect(
    self,
    artifact: Artifact,
    *,
    semantic_unit: str,
    executor_framework: str,
    executable_text: str,
    invocation_payload: Any,
    timeout_seconds: float | None = None,
) -> CrossBoundaryResult:
    """
    High Level Purpose:
        In circumstances like executing a learned governed ability against the host environment, helps with routing the effect through runtime grant issuance, mediation, trace, and only then the executor boundary.

    Reference to Theory:
        Supports the first Python-host cut of bundle-style governance by making current executor-backed skills pass through one mediated authority gate without redesigning the controller loop.

    Example Input Output:
        Input: `execute_mediated_artifact_effect(self=controller, artifact=Artifact(id='artifact-force-function', title='Force from mass and acceleration', artifact_type='ability', representation='python_script'), semantic_unit='Calculate force from mass=3 and acceleration=4.', executor_framework='python3', executable_text='def main():\\n    pass', invocation_payload={'mass': 3, 'acceleration': 4}, timeout_seconds=45.0)`
        Output: CrossBoundaryResult(ok=True, command=['uv', 'run'], exit_code=0, stdout='...', stderr='')

    Args:
        self: Bound controller instance that owns runtime state and execution helpers.
        artifact: Value for `artifact` used by `execute_mediated_artifact_effect`. Expected type: `Artifact`.
        semantic_unit: Value for `semantic_unit` used by `execute_mediated_artifact_effect`. Expected type: `str`.
        executor_framework: Value for `executor_framework` used by `execute_mediated_artifact_effect`. Expected type: `str`.
        executable_text: Value for `executable_text` used by `execute_mediated_artifact_effect`. Expected type: `str`.
        invocation_payload: Value for `invocation_payload` used by `execute_mediated_artifact_effect`. Expected type: `Any`.
        timeout_seconds: Value for `timeout_seconds` used by `execute_mediated_artifact_effect`. Expected type: `float | None`. Defaults to `None`.

    Returns:
        CrossBoundaryResult: Result produced by `execute_mediated_artifact_effect`.
    """
    normalized_executor = normalize_executor_framework_name(executor_framework or "python3") or "python3"
    effect_kind = f"execute.{normalized_executor}"
    governed_context = runtime_artifact_governance_context(self, artifact)
    declaration = dict(governed_context.get("declaration", {})) if isinstance(governed_context.get("declaration", {}), Mapping) else {}
    current_admission = dict(governed_context.get("admission", {})) if isinstance(governed_context.get("admission", {}), Mapping) else {}
    effective_lifecycle = dict(governed_context.get("lifecycle", {})) if isinstance(governed_context.get("lifecycle", {}), Mapping) else {}
    admitted = bool(governed_context.get("admitted"))
    admission_reason = str(governed_context.get("admission_reason", ""))
    request = EffectRequest(
        effect_kind=effect_kind,
        artifact_id=str(getattr(artifact, "id", "")),
        artifact_title=collapse_ws(str(getattr(artifact, "title", ""))),
        semantic_unit=collapse_ws(str(semantic_unit)),
        executor_framework=normalized_executor,
        invocation_payload=json_safe(invocation_payload),
        realizer_kind="executor",
        realizer_identity=normalized_executor,
    )
    self.use_capability(
        "host_mediation",
        node=None,
        contribution=f"mediate {effect_kind} for {artifact.title}",
    )
    binding_allowed, binding_rationale, realizer_evidence = _preflight_executor_realizer(
        self,
        artifact=artifact,
        declaration=declaration,
        executor_identity=normalized_executor,
    )
    if not binding_allowed:
        decision = EffectDecision(
            allowed=False,
            rationale=binding_rationale,
            required_authority=required_authority_for_effect_kind(effect_kind),
        )
        denied_result = CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr=decision.rationale,
            notes=["Host realizer binding failed before any invocation grant was issued."],
        )
        record_effect_trace(
            self,
            artifact=artifact,
            request=request,
            decision=decision,
            grants=[],
            admission_snapshot=current_admission,
            lifecycle_snapshot=effective_lifecycle,
            realizer_evidence=realizer_evidence,
            result=denied_result,
        )
        return denied_result
    grants = issue_capability_grants_for_artifact(
        artifact,
        effect_kind=effect_kind,
        executor_framework=normalized_executor,
        semantic_unit=semantic_unit,
        admission_snapshot=current_admission,
    ) if admitted else []
    if grants:
        self.use_capability(
            "capability_granting",
            node=None,
            contribution=f"issue governed runtime grants for {artifact.title}",
        )
        self.state.capability_grants.extend(json_safe(grants))
    decision = evaluate_effect_request(
        request,
        declaration=declaration,
        admitted=admitted,
        admission_reason=admission_reason,
        grants=grants,
    )
    if not decision.allowed:
        denied_result = CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr=decision.rationale,
            notes=["Host mediation denied the requested governed effect before boundary execution."],
        )
        record_effect_trace(
            self,
            artifact=artifact,
            request=request,
            decision=decision,
            grants=grants,
            admission_snapshot=current_admission,
            lifecycle_snapshot=effective_lifecycle,
            realizer_evidence=realizer_evidence,
            result=denied_result,
        )
        return denied_result
    broker_governance_context = _runtime_broker_governance_context(
        self,
        artifact=artifact,
        declaration=declaration,
        grants=grants,
    )
    runtime_executable_text = str(executable_text or "")
    if normalized_executor == "bash":
        runtime_content = normalize_ability_runtime_content(
            dict(artifact.content) if isinstance(artifact.content, Mapping) else {},
            title=collapse_ws(str(getattr(artifact, "title", ""))),
        )
        shell_script = runtime_content.get("shell_script")
        if isinstance(shell_script, str) and shell_script.strip():
            runtime_executable_text = shell_script
    host_runtime_context = {
        "artifact_id": str(getattr(artifact, "id", "")),
        "artifact_title": collapse_ws(str(getattr(artifact, "title", ""))),
        "semantic_unit": collapse_ws(str(semantic_unit)),
        "host_abi_version": host_abi_version(),
        "declaration": declaration,
        "declared_host_brokers": list(_declared_host_brokers(artifact)),
        "strict_realizer_declaration": _uses_strict_realizer_declaration(artifact),
        "admission": dict(current_admission),
        "grants": grants,
        "sqlite_path": broker_governance_context.get("sqlite_path", ""),
        "workspace_root": broker_governance_context.get("workspace_root", ""),
        "virtual_mounts": broker_governance_context.get("virtual_mounts", {}),
        "named_queries": broker_governance_context.get("named_queries", {}),
        "skill_state_namespace": broker_governance_context.get("skill_state_namespace", ""),
    }
    try:
        result = _active_realizer_provider(self).execute(
            HostExecutorInvocation(
                identity=normalized_executor,
                executable_text=runtime_executable_text,
                stdin_payload=invocation_payload,
                timeout_seconds=timeout_seconds,
                host_runtime_context=host_runtime_context,
            )
        )
    except HostRealizerUnavailableError as exc:
        result = CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr=str(exc),
            notes=["Host realizer became unavailable after pre-invocation inspection."],
        )
    child_host_traces = []
    if isinstance(result.metadata, Mapping):
        child_host_traces = [
            dict(item)
            for item in result.metadata.get("host_traces", [])
            if isinstance(item, Mapping)
        ]
    nested_capability_grants = []
    if isinstance(result.metadata, Mapping):
        nested_capability_grants = [
            dict(item)
            for item in result.metadata.get("nested_capability_grants", [])
            if isinstance(item, Mapping)
        ]
    if nested_capability_grants:
        self.state.capability_grants.extend(json_safe(nested_capability_grants))
    nested_effect_traces = []
    if isinstance(result.metadata, Mapping):
        nested_effect_traces = [
            dict(item)
            for item in result.metadata.get("nested_effect_traces", [])
            if isinstance(item, Mapping)
        ]
    if nested_effect_traces:
        self.state.effect_traces.extend(json_safe(nested_effect_traces))
        self.state.record_step(
            kind="host_effect_subtrace_ingest",
            node_id=self.state.root_id,
            intent="Preserve governed nested effect traces emitted by alternate runtimes that compose with other governed skills or tools.",
            action="ingest nested governed host traces",
            result=f"{len(nested_effect_traces)} nested host effects recorded",
            evaluation="alternate-runtime governed composition remained visible to the parent constitutional trace surface",
            payload={"count": len(nested_effect_traces), "artifact_id": artifact.id},
        )
    if child_host_traces:
        self.state.effect_traces.extend(json_safe(child_host_traces))
        self.state.record_step(
            kind="host_effect_subtrace_ingest",
            node_id=self.state.root_id,
            intent="Preserve governed sub-effect traces emitted by broker-aware Python skills.",
            action="ingest child host broker traces",
            result=f"{len(child_host_traces)} child host effects recorded",
            evaluation="python skill host effects remained visible to the parent governed trace surface",
            payload={"count": len(child_host_traces), "artifact_id": artifact.id},
        )
    record_effect_trace(
        self,
        artifact=artifact,
        request=request,
        decision=decision,
        grants=grants,
        admission_snapshot=current_admission,
        lifecycle_snapshot=effective_lifecycle,
        realizer_evidence=realizer_evidence,
        result=result,
    )
    return result


def execute_mediated_host_broker_request(
    self,
    artifact: Artifact,
    *,
    broker_name: str,
    broker_arguments: Mapping[str, Any] | None = None,
    semantic_unit: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like moving device, filesystem, store, or network actions behind named host brokers, helps with mediating one broker request through declaration-derived grants before the broker is invoked.

    Reference to Theory:
        Supports the next Python-host step toward the bundle target by making non-executor host actions go through the same admission, authority, and trace layer as executable abilities.

    Example Input Output:
        Input: `execute_mediated_host_broker_request(self=controller, artifact=Artifact(id='artifact-write-file', title='Write text file', artifact_type='ability', representation='python_script'), broker_name='fs.write_text', broker_arguments={'path': '/tmp/demo.txt', 'text': 'hello'}, semantic_unit='Write hello to a file.')`
        Output: {'status': 'ok', 'path': '/tmp/demo.txt', 'bytes_written': 5, 'effect_trace_id': 'effect-abc123'}

    Args:
        self: Bound controller instance that owns runtime state and execution helpers.
        artifact: Value for `artifact` used by `execute_mediated_host_broker_request`. Expected type: `Artifact`.
        broker_name: Value for `broker_name` used by `execute_mediated_host_broker_request`. Expected type: `str`.
        broker_arguments: Value for `broker_arguments` used by `execute_mediated_host_broker_request`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        semantic_unit: Value for `semantic_unit` used by `execute_mediated_host_broker_request`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `execute_mediated_host_broker_request`.
    """
    effect_kind = collapse_ws(str(broker_name))
    governed_context = runtime_artifact_governance_context(self, artifact)
    declaration = dict(governed_context.get("declaration", {})) if isinstance(governed_context.get("declaration", {}), Mapping) else {}
    current_admission = dict(governed_context.get("admission", {})) if isinstance(governed_context.get("admission", {}), Mapping) else {}
    effective_lifecycle = dict(governed_context.get("lifecycle", {})) if isinstance(governed_context.get("lifecycle", {}), Mapping) else {}
    admitted = bool(governed_context.get("admitted"))
    admission_reason = str(governed_context.get("admission_reason", ""))
    request = EffectRequest(
        effect_kind=effect_kind,
        artifact_id=str(getattr(artifact, "id", "")),
        artifact_title=collapse_ws(str(getattr(artifact, "title", ""))),
        semantic_unit=collapse_ws(str(semantic_unit)),
        executor_framework="",
        invocation_payload=json_safe(dict(broker_arguments or {})),
        realizer_kind="broker",
        realizer_identity=effect_kind,
    )
    self.use_capability(
        "host_mediation",
        node=None,
        contribution=f"mediate {effect_kind} for {artifact.title}",
    )
    binding_allowed, binding_rationale, realizer_evidence = _preflight_broker_realizer(
        self,
        artifact=artifact,
        broker_identity=effect_kind,
    )
    if not binding_allowed:
        decision = EffectDecision(
            allowed=False,
            rationale=binding_rationale,
            required_authority=required_authority_for_effect_kind(effect_kind),
        )
        denied_result = CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr=decision.rationale,
            notes=["Host realizer binding failed before any invocation grant was issued."],
        )
        trace = record_effect_trace(
            self,
            artifact=artifact,
            request=request,
            decision=decision,
            grants=[],
            admission_snapshot=current_admission,
            lifecycle_snapshot=effective_lifecycle,
            realizer_evidence=realizer_evidence,
            result=denied_result,
        )
        return {
            "status": "error",
            "broker": effect_kind,
            "error": decision.rationale,
            "effect_trace_id": trace["id"],
        }
    grants = issue_capability_grants_for_artifact(
        artifact,
        effect_kind=effect_kind,
        semantic_unit=semantic_unit,
        admission_snapshot=current_admission,
    ) if admitted else []
    if grants:
        self.use_capability(
            "capability_granting",
            node=None,
            contribution=f"issue governed runtime grants for {artifact.title}",
        )
        self.state.capability_grants.extend(json_safe(grants))
    decision = evaluate_effect_request(
        request,
        declaration=declaration,
        admitted=admitted,
        admission_reason=admission_reason,
        grants=grants,
    )
    if not decision.allowed:
        denied_result = CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr=decision.rationale,
            notes=["Host mediation denied the requested broker effect before host invocation."],
        )
        trace = record_effect_trace(
            self,
            artifact=artifact,
            request=request,
            decision=decision,
            grants=grants,
            admission_snapshot=current_admission,
            lifecycle_snapshot=effective_lifecycle,
            realizer_evidence=realizer_evidence,
            result=denied_result,
        )
        return {
            "status": "error",
            "broker": effect_kind,
            "error": decision.rationale,
            "effect_trace_id": trace["id"],
        }
    try:
        broker_result = _active_realizer_provider(self).invoke_broker(
            HostBrokerInvocation(
                identity=effect_kind,
                arguments=dict(broker_arguments or {}),
                governance_context=_runtime_broker_governance_context(
                    self,
                    artifact=artifact,
                    declaration=declaration,
                    grants=grants,
                ),
            )
        )
    except HostRealizerUnavailableError as exc:
        broker_result = {
            "status": "error",
            "broker": effect_kind,
            "error": str(exc),
        }
    nested_capability_grants = [
        dict(item)
        for item in broker_result.get("nested_capability_grants", [])
        if isinstance(item, Mapping)
    ] if isinstance(broker_result, Mapping) else []
    if nested_capability_grants:
        self.state.capability_grants.extend(json_safe(nested_capability_grants))
    nested_effect_traces = [
        dict(item)
        for item in broker_result.get("nested_effect_traces", [])
        if isinstance(item, Mapping)
    ] if isinstance(broker_result, Mapping) else []
    if nested_effect_traces:
        self.state.effect_traces.extend(json_safe(nested_effect_traces))
        self.state.record_step(
            kind="host_effect_subtrace_ingest",
            node_id=self.state.root_id,
            intent="Preserve governed sub-effect traces emitted by mediated host brokers that invoke other governed skills.",
            action="ingest nested host broker traces",
            result=f"{len(nested_effect_traces)} nested host effects recorded",
            evaluation="broker-mediated skill or tool invocation remained visible to the parent governed trace surface",
            payload={"count": len(nested_effect_traces), "artifact_id": artifact.id, "broker_name": effect_kind},
        )
    success = str(broker_result.get("status", "")).strip().lower() == "ok"
    boundary_result = CrossBoundaryResult(
        ok=success,
        command=[effect_kind],
        exit_code=0 if success else 1,
        stdout="",
        stderr="" if success else str(broker_result.get("error", "")),
        parsed_output=broker_result,
        result=broker_result,
        answer=str(
            broker_result.get("answer", broker_result.get("text", broker_result.get("status", "")))
        ),
        notes=[] if success else ["Host broker returned an error result."],
    )
    trace = record_effect_trace(
        self,
        artifact=artifact,
        request=request,
        decision=decision,
        grants=grants,
        admission_snapshot=current_admission,
        lifecycle_snapshot=effective_lifecycle,
        realizer_evidence=realizer_evidence,
        result=boundary_result,
    )
    return {**broker_result, "effect_trace_id": trace["id"]}
