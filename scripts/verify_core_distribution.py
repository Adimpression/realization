#!/usr/bin/env python3
"""Inspect and execute built core wheels without the repository on sys.path."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_MANIFEST = REPO_ROOT / "core_engine" / "module_manifest.txt"


def _wheel_entries(path: Path) -> set[str]:
    with zipfile.ZipFile(path) as archive:
        return set(archive.namelist())


def _extract(path: Path, target: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        archive.extractall(target)


def _verify_contents(
    app_wheel: Path,
    conversation_wheel: Path,
    engine_wheel: Path,
    governance_wheel: Path,
    governance_sdist: Path,
    host_interaction_wheel: Path,
    llm_wheel: Path,
    runtime_wheel: Path,
    semantics_wheel: Path,
    semantics_sdist: Path,
    skill_semantics_wheel: Path,
    skill_semantics_sdist: Path,
) -> dict[str, object]:
    app_entries = _wheel_entries(app_wheel)
    conversation_entries = _wheel_entries(conversation_wheel)
    engine_entries = _wheel_entries(engine_wheel)
    governance_entries = _wheel_entries(governance_wheel)
    host_interaction_entries = _wheel_entries(host_interaction_wheel)
    llm_entries = _wheel_entries(llm_wheel)
    runtime_entries = _wheel_entries(runtime_wheel)
    semantics_entries = _wheel_entries(semantics_wheel)
    skill_semantics_entries = _wheel_entries(skill_semantics_wheel)
    declared_modules = {
        line
        for raw_line in MODULE_MANIFEST.read_text(encoding="utf-8").splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    }
    packaged_modules = {
        entry.removesuffix(".py")
        for entry in engine_entries
        if entry.endswith(".py") and "/" not in entry
    }
    undeclared_modules = sorted(packaged_modules - declared_modules)
    unpackaged_modules = sorted(declared_modules - packaged_modules)

    app_required = {
        "realized_core/__init__.py",
        "realized_core/__main__.py",
        "realized_core/chat.py",
        "realized_core/cli.py",
        "realized_core/conversation.py",
        "realized_core/planning.py",
    }
    app_missing = sorted(app_required - app_entries)
    app_python_entries = {
        entry
        for entry in app_entries
        if entry.endswith(".py") and ".dist-info/" not in entry
    }
    app_unexpected = sorted(app_python_entries - app_required)

    conversation_required = {
        "realized_core_conversation/__init__.py",
        "realized_core_conversation/contracts.py",
        "realized_core_conversation/identity.py",
        "realized_core_conversation/journal.py",
        "realized_core_conversation/ports.py",
        "realized_core_conversation/schemas.py",
        "realized_core_conversation/service.py",
    }
    conversation_missing = sorted(
        conversation_required - conversation_entries
    )
    conversation_forbidden = sorted(
        entry
        for entry in conversation_entries
        if entry.startswith("realized_core/")
        or entry.startswith("workstation/")
    )

    llm_required = {
        "realized_core_llm/__init__.py",
        "realized_core_llm/planning.py",
        "realized_core_llm/provider.py",
    }
    llm_missing = sorted(llm_required - llm_entries)
    llm_forbidden = sorted(
        entry
        for entry in llm_entries
        if entry.startswith("realized_core/")
        or entry.startswith("realized_core_conversation/")
        or entry.startswith("realized_core_engine/")
        or entry.startswith("workstation/")
    )

    engine_required = {
        "controller_runtime.py",
        "realized_core_engine/__init__.py",
        "realized_core_engine/api.py",
        "realized_core_engine/cli_support.py",
        "realized_core_engine/contracts.py",
        "store.py",
        "system_state.py",
    }
    engine_missing = sorted(engine_required - engine_entries)
    engine_forbidden = sorted(
        entry
        for entry in engine_entries
        if entry.startswith("realized_core/")
        or entry.startswith("workstation/")
        or entry in {"main.py", "controller_entrypoints.py"}
        or "publication" in entry.lower()
    )

    governance_required = {
        "realized_core_governance/__init__.py",
        "realized_core_governance/_normalization.py",
        "realized_core_governance/admission.py",
        "realized_core_governance/approval.py",
        "realized_core_governance/data.py",
        "realized_core_governance/declarations.py",
        "realized_core_governance/inventory.py",
        "realized_core_governance/lifecycle.py",
        "realized_core_governance/py.typed",
        "realized_core_governance/records.py",
        "realized_core_governance/safety.py",
        "realized_core_governance/vocabulary.py",
    }
    governance_missing = sorted(governance_required - governance_entries)
    governance_forbidden = sorted(
        entry
        for entry in governance_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_core_governance/")
        and ".dist-info/" not in entry
    )
    with tarfile.open(governance_sdist, mode="r:gz") as archive:
        governance_sdist_entries = set(archive.getnames())
    governance_sdist_prefix = "realized_core_governance-0.1.0"
    governance_sdist_required = {
        f"{governance_sdist_prefix}/pyproject.toml",
        f"{governance_sdist_prefix}/src/realized_core_governance/__init__.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/_normalization.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/admission.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/approval.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/data.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/declarations.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/inventory.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/lifecycle.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/py.typed",
        f"{governance_sdist_prefix}/src/realized_core_governance/records.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/safety.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/vocabulary.py",
    }
    governance_sdist_missing = sorted(
        governance_sdist_required - governance_sdist_entries
    )

    host_interaction_required = {
        "realized_host_interaction/__init__.py",
        "realized_host_interaction/_normalization.py",
        "realized_host_interaction/action_dispatch.py",
        "realized_host_interaction/actions.py",
        "realized_host_interaction/context.py",
        "realized_host_interaction/delegation.py",
        "realized_host_interaction/models.py",
        "realized_host_interaction/receipts.py",
        "realized_host_interaction/resolution.py",
    }
    host_interaction_missing = sorted(
        host_interaction_required - host_interaction_entries
    )
    host_interaction_forbidden = sorted(
        entry
        for entry in host_interaction_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_host_interaction/")
        and ".dist-info/" not in entry
    )

    runtime_required = {
        "realized_core_runtime/__init__.py",
        "realized_core_runtime/contracts.py",
        "realized_core_runtime/reduction.py",
    }
    runtime_missing = sorted(runtime_required - runtime_entries)
    semantics_required = {
        "realized_core_semantics/__init__.py",
        "realized_core_semantics/artifacts.py",
        "realized_core_semantics/py.typed",
        "realized_core_semantics/theory.py",
        "realized_core_semantics/values.py",
    }
    semantics_missing = sorted(semantics_required - semantics_entries)
    semantics_forbidden = sorted(
        entry
        for entry in semantics_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_core_semantics/")
        and ".dist-info/" not in entry
    )
    with tarfile.open(semantics_sdist, mode="r:gz") as archive:
        semantics_sdist_entries = set(archive.getnames())
    semantics_sdist_prefix = "realized_core_semantics-0.1.0"
    semantics_sdist_required = {
        f"{semantics_sdist_prefix}/pyproject.toml",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/__init__.py",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/artifacts.py",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/py.typed",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/theory.py",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/values.py",
    }
    semantics_sdist_missing = sorted(
        semantics_sdist_required - semantics_sdist_entries
    )
    skill_semantics_required = {
        "realized_skill_semantics/__init__.py",
        "realized_skill_semantics/composition.py",
        "realized_skill_semantics/declaration.py",
        "realized_skill_semantics/execution.py",
        "realized_skill_semantics/invocation.py",
        "realized_skill_semantics/ir.py",
        "realized_skill_semantics/leaves.py",
        "realized_skill_semantics/normalization.py",
        "realized_skill_semantics/paths.py",
        "realized_skill_semantics/py.typed",
    }
    skill_semantics_missing = sorted(
        skill_semantics_required - skill_semantics_entries
    )
    skill_semantics_forbidden = sorted(
        entry
        for entry in skill_semantics_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_skill_semantics/")
        and ".dist-info/" not in entry
    )
    with tarfile.open(skill_semantics_sdist, mode="r:gz") as archive:
        skill_semantics_sdist_entries = set(archive.getnames())
    skill_semantics_sdist_prefix = "realized_skill_semantics-0.1.0"
    skill_semantics_sdist_required = {
        f"{skill_semantics_sdist_prefix}/pyproject.toml",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/__init__.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/composition.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/declaration.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/execution.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/invocation.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/ir.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/leaves.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/normalization.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/paths.py",
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/py.typed",
    }
    skill_semantics_sdist_missing = sorted(
        skill_semantics_sdist_required - skill_semantics_sdist_entries
    )
    if (
        app_missing
        or app_unexpected
        or conversation_forbidden
        or conversation_missing
        or engine_forbidden
        or engine_missing
        or governance_forbidden
        or governance_missing
        or governance_sdist_missing
        or host_interaction_forbidden
        or host_interaction_missing
        or llm_forbidden
        or llm_missing
        or runtime_missing
        or semantics_forbidden
        or semantics_missing
        or semantics_sdist_missing
        or skill_semantics_forbidden
        or skill_semantics_missing
        or skill_semantics_sdist_missing
        or undeclared_modules
        or unpackaged_modules
    ):
        raise RuntimeError(
            json.dumps(
                {
                    "app_missing": app_missing,
                    "app_unexpected": app_unexpected,
                    "conversation_forbidden": conversation_forbidden,
                    "conversation_missing": conversation_missing,
                    "engine_forbidden": engine_forbidden,
                    "engine_missing": engine_missing,
                    "governance_forbidden": governance_forbidden,
                    "governance_missing": governance_missing,
                    "governance_sdist_missing": governance_sdist_missing,
                    "host_interaction_forbidden": host_interaction_forbidden,
                    "host_interaction_missing": host_interaction_missing,
                    "llm_forbidden": llm_forbidden,
                    "llm_missing": llm_missing,
                    "runtime_missing": runtime_missing,
                    "semantics_forbidden": semantics_forbidden,
                    "semantics_missing": semantics_missing,
                    "semantics_sdist_missing": semantics_sdist_missing,
                    "skill_semantics_forbidden": skill_semantics_forbidden,
                    "skill_semantics_missing": skill_semantics_missing,
                    "skill_semantics_sdist_missing": skill_semantics_sdist_missing,
                    "undeclared_modules": undeclared_modules,
                    "unpackaged_modules": unpackaged_modules,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return {
        "app_entry_count": len(app_entries),
        "app_python_entries": sorted(app_python_entries),
        "canonical_module_count": len(packaged_modules),
        "conversation_entry_count": len(conversation_entries),
        "conversation_forbidden_entries": conversation_forbidden,
        "engine_entry_count": len(engine_entries),
        "engine_forbidden_entries": engine_forbidden,
        "governance_entry_count": len(governance_entries),
        "governance_forbidden_entries": governance_forbidden,
        "governance_sdist_entry_count": len(governance_sdist_entries),
        "host_interaction_entry_count": len(host_interaction_entries),
        "host_interaction_forbidden_entries": host_interaction_forbidden,
        "llm_entry_count": len(llm_entries),
        "llm_forbidden_entries": llm_forbidden,
        "runtime_entry_count": len(runtime_entries),
        "semantics_entry_count": len(semantics_entries),
        "semantics_forbidden_entries": semantics_forbidden,
        "semantics_sdist_entry_count": len(semantics_sdist_entries),
        "skill_semantics_entry_count": len(skill_semantics_entries),
        "skill_semantics_forbidden_entries": skill_semantics_forbidden,
        "skill_semantics_sdist_entry_count": len(skill_semantics_sdist_entries),
    }


def _smoke(
    app_wheel: Path,
    conversation_wheel: Path,
    engine_wheel: Path,
    governance_wheel: Path,
    host_interaction_wheel: Path,
    llm_wheel: Path,
    runtime_wheel: Path,
    semantics_wheel: Path,
    skill_semantics_wheel: Path,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="realized-core-wheel-") as temporary_dir:
        root = Path(temporary_dir).resolve()
        app_installed = root / "app"
        conversation_installed = root / "conversation"
        engine_installed = root / "engine"
        governance_installed = root / "governance"
        host_interaction_installed = root / "host-interaction"
        llm_installed = root / "llm"
        runtime_installed = root / "runtime"
        semantics_installed = root / "semantics"
        skill_semantics_installed = root / "skill-semantics"
        for target in (
            app_installed,
            conversation_installed,
            engine_installed,
            governance_installed,
            host_interaction_installed,
            llm_installed,
            runtime_installed,
            semantics_installed,
            skill_semantics_installed,
        ):
            target.mkdir()
        _extract(app_wheel, app_installed)
        _extract(conversation_wheel, conversation_installed)
        _extract(engine_wheel, engine_installed)
        _extract(governance_wheel, governance_installed)
        _extract(host_interaction_wheel, host_interaction_installed)
        _extract(llm_wheel, llm_installed)
        _extract(runtime_wheel, runtime_installed)
        _extract(semantics_wheel, semantics_installed)
        _extract(skill_semantics_wheel, skill_semantics_installed)
        sqlite_path = root / "state.sqlite3"
        state_path = root / "state.json"
        script = """
import json
from pathlib import Path
import sys

app_target = Path(sys.argv.pop(1)).resolve()
conversation_target = Path(sys.argv.pop(1)).resolve()
engine_target = Path(sys.argv.pop(1)).resolve()
governance_target = Path(sys.argv.pop(1)).resolve()
host_interaction_target = Path(sys.argv.pop(1)).resolve()
llm_target = Path(sys.argv.pop(1)).resolve()
runtime_target = Path(sys.argv.pop(1)).resolve()
semantics_target = Path(sys.argv.pop(1)).resolve()
skill_semantics_target = Path(sys.argv.pop(1)).resolve()
sys.path[:0] = [
    str(app_target),
    str(conversation_target),
    str(engine_target),
    str(governance_target),
    str(host_interaction_target),
    str(llm_target),
    str(runtime_target),
    str(semantics_target),
    str(skill_semantics_target),
]
import artifact_contracts
import approval_governance
import applied_theory_primitives
import applied_theory_types
import controller_runtime
import data_governance
import execution_framework_primitives
import execution_frameworks
import governance_inventory
import pure_theory_types
import skill_boundary_normalization
import skill_governance_primitives
import skill_governance
import skill_ir as legacy_skill_ir
import skill_leaf_types
import skill_lifecycle
import skill_path_notation
import skill_safety_governance
import realized_core
import realized_core_conversation
import realized_core_engine
import realized_core_governance
import realized_host_interaction
import realized_core_llm
import realized_core_runtime
import realized_core_semantics
import realized_skill_semantics
from realized_core_semantics import artifacts as semantic_artifacts
from realized_core_semantics import theory as semantic_theory
from realized_core_semantics import values as semantic_values
from realized_core_governance import admission as governance_admission
from realized_core_governance import approval as governance_approval
from realized_core_governance import data as governance_data
from realized_core_governance import declarations as governance_declarations
from realized_core_governance import inventory as governance_inventory_owner
from realized_core_governance import lifecycle as governance_lifecycle
from realized_core_governance import records as governance_records
from realized_core_governance import safety as governance_safety
from realized_core_governance import vocabulary as governance_vocabulary
from realized_skill_semantics import composition as skill_composition
from realized_skill_semantics import declaration as skill_declaration
from realized_skill_semantics import execution as skill_execution
from realized_skill_semantics import leaves as skill_leaves
from realized_skill_semantics import ir as skill_ir
from realized_skill_semantics import invocation as skill_invocation
from realized_skill_semantics import normalization as skill_normalization
from realized_skill_semantics import paths as skill_paths
from realized_core.cli import main

expected_owners = (
    (controller_runtime, engine_target),
    (realized_core, app_target),
    (realized_core_conversation, conversation_target),
    (realized_core_engine, engine_target),
    (realized_core_governance, governance_target),
    (realized_host_interaction, host_interaction_target),
    (realized_core_llm, llm_target),
    (realized_core_runtime, runtime_target),
    (realized_core_semantics, semantics_target),
    (realized_skill_semantics, skill_semantics_target),
)
for module, owner in expected_owners:
    module_path = Path(module.__file__).resolve()
    if not module_path.is_relative_to(owner):
        raise RuntimeError(
            f"{module.__name__} escaped its wheel extraction: {module_path}"
        )
if artifact_contracts.ArtifactContentView is not semantic_artifacts.ArtifactContentView:
    raise RuntimeError("artifact contract compatibility identity changed")
if pure_theory_types.NonAchievedness is not semantic_theory.NonAchievedness:
    raise RuntimeError("formal theory compatibility identity changed")
for name in ("json_safe", "utc_now"):
    canonical = getattr(semantic_values, name)
    if getattr(applied_theory_primitives, name) is not canonical:
        raise RuntimeError(f"applied theory primitive identity changed: {name}")
    if getattr(applied_theory_types, name) is not canonical:
        raise RuntimeError(f"applied theory facade identity changed: {name}")
for facade, implementation in (
    (approval_governance, governance_approval),
    (data_governance, governance_data),
    (skill_governance_primitives, governance_vocabulary),
    (skill_lifecycle, governance_lifecycle),
    (skill_safety_governance, governance_safety),
):
    for name in facade.__all__:
        if getattr(facade, name) is not getattr(implementation, name):
            raise RuntimeError(
                f"governance compatibility identity changed: {facade.__name__}.{name}"
            )
for name in governance_records.__all__:
    if getattr(skill_governance, name) is not getattr(governance_records, name):
        raise RuntimeError(
            f"skill governance record projection identity changed: {name}"
        )
for name in governance_declarations.__all__:
    if getattr(skill_governance, name) is not getattr(governance_declarations, name):
        raise RuntimeError(
            f"skill governance declaration identity changed: {name}"
        )
if (
    governance_inventory.load_governance_inventory
    is not governance_inventory_owner.load_governance_inventory
):
    raise RuntimeError("governance inventory compatibility identity changed")

declaration_snapshot = governance_declarations.skill_declaration_from_payload(
    {
        "schema": "bssc_skill.v2",
        "declaration": {
            "intent": "Open a browser URL.",
            "inputs": {"url": "target URL"},
            "outputs": {"status": "open status"},
            "authorities_requested": ["execute"],
            "authority_bounds": {
                "execute": {
                    "scope": "local_desktop",
                    "target": "browser_application",
                    "context": "explicit_user_prompt",
                    "duration": "single_invocation",
                    "triggering_conditions": ["user invokes skill"],
                    "approval_class": "automatic",
                }
            },
            "data_classes_touched": ["public"],
            "side_effects": ["launch browser"],
            "persistence_behavior": "none",
            "invocation_rights": ["direct_user_invocation"],
            "composition_rights": [],
            "escalation_rights": [],
            "approval_requirements": ["automatic"],
            "risk_tier": "tier1_bounded_transform",
        },
    },
    kind="ability",
    executor_framework="python",
)
if declaration_snapshot.get("executor_framework") != "python3":
    raise RuntimeError("governance declaration executor normalization changed")
if declaration_snapshot.get("authorities_requested") != ["execute"]:
    raise RuntimeError("governance declaration authority normalization changed")

policy_snapshot = governance_declarations.skill_policy_from_payload(
    {
        "schema": "bssc_skill.v2",
        "kind": "policy",
        "policy": {
            "intent": "Admit bounded local abilities.",
            "target_kinds": ["ability"],
            "max_risk_tier": "tier2_connected",
            "allowed_authorities": ["read", "execute"],
            "allowed_executors": ["python"],
        },
    }
)
if policy_snapshot.get("allowed_executors") != ["python3"]:
    raise RuntimeError("governance policy executor normalization changed")
if "Admit bounded local abilities" not in governance_declarations.policy_answer_summary(
    policy_snapshot
):
    raise RuntimeError("governance policy summary changed")

class _InventoryArtifact:
    def __init__(self, title, content):
        self.title = title
        self.content = content

class _InventoryReader:
    def __init__(self, artifacts):
        self.artifacts = artifacts
        self.calls = 0

    def load_all_artifacts(self):
        self.calls += 1
        return self.artifacts

admission_policy_artifact = _InventoryArtifact(
    "Bounded local policy",
    {
        "skill_policy": {
            "target_kinds": ["ability"],
            "max_risk_tier": "tier1_bounded_transform",
            "allowed_authorities": ["execute"],
            "denied_authorities": [],
            "allowed_executors": ["python3"],
            "allowed_data_classes": ["public"],
            "denied_side_effects": [],
            "required_approval_for_risk_tiers": {},
        }
    },
)
admission_declaration = {
    "authorities_requested": ["execute"],
    "risk_tier": "tier1_bounded_transform",
    "approval_requirements": ["automatic"],
    "data_classes_touched": ["public"],
    "side_effects": ["local executor invocation"],
}
fixed_evaluation_time = lambda: "2026-10-26T12:00:00Z"
admission_snapshot = governance_admission.evaluate_skill_policy_admission(
    admission_declaration,
    skill_title="Bounded local ability",
    kind="ability",
    executor_framework="python",
    policy_artifacts=[admission_policy_artifact],
    approval_artifacts=[],
    evaluated_at=fixed_evaluation_time,
)
if admission_snapshot.get("status") != "admitted":
    raise RuntimeError("governance policy admission evaluation changed")
skill_governance.utc_now = fixed_evaluation_time
root_admission_snapshot = skill_governance.evaluate_skill_admission(
    admission_declaration,
    skill_title="Bounded local ability",
    kind="ability",
    executor_framework="python",
    skill_content={},
    policy_artifacts=[admission_policy_artifact],
    approval_artifacts=[],
)
if root_admission_snapshot != admission_snapshot:
    raise RuntimeError("root admission orchestration changed policy evaluation")

overlapping_governance_artifact = _InventoryArtifact(
    "Combined governance record",
    {
        "skill_policy": {"name": "policy"},
        "skill_approval": {"status": "approved"},
        "skill_revocation": {"status": "active"},
        "skill_incident": {"status": "open"},
    },
)
inventory_artifacts = [overlapping_governance_artifact]
inventory_reader = _InventoryReader(inventory_artifacts)
inventory_snapshot = governance_inventory_owner.load_governance_inventory(
    inventory_reader
)
if inventory_reader.calls != 1:
    raise RuntimeError("governance inventory did not read exactly once")
if inventory_snapshot["artifacts"] is not inventory_artifacts:
    raise RuntimeError("governance inventory changed the loaded collection")
for category in ("policies", "approvals", "revocations", "incidents"):
    if inventory_snapshot[category] != inventory_artifacts:
        raise RuntimeError(f"governance inventory classification changed: {category}")
for name in skill_declaration.__all__:
    if getattr(skill_governance, name) is not getattr(skill_declaration, name):
        raise RuntimeError(
            f"skill declaration compatibility identity changed: {name}"
        )
for name in skill_execution.__all__:
    for facade in (execution_framework_primitives, execution_frameworks):
        if getattr(facade, name) is not getattr(skill_execution, name):
            raise RuntimeError(
                f"skill execution descriptor compatibility identity changed: "
                f"{facade.__name__}.{name}"
            )
if (
    execution_frameworks.normalize_supported_executor_frameworks
    is not execution_framework_primitives.normalize_supported_executor_frameworks
):
    raise RuntimeError("host-supported executor normalization identity changed")
if hasattr(skill_execution, "normalize_supported_executor_frameworks"):
    raise RuntimeError("portable descriptor package acquired host-support behavior")
for facade, implementation in (
    (skill_leaf_types, skill_leaves),
    (skill_path_notation, skill_paths),
):
    for name in facade.__all__:
        if getattr(facade, name) is not getattr(implementation, name):
            raise RuntimeError(
                f"skill semantic compatibility identity changed: {facade.__name__}.{name}"
            )
for name in (
    "normalize_skill_region_body",
    "normalized_skill_normalization_payload",
    "reconstruct_skill_region_body",
    "synthesized_skill_normalization",
):
    if getattr(skill_boundary_normalization, name) is not getattr(skill_normalization, name):
        raise RuntimeError(
            f"skill normalization compatibility identity changed: {name}"
        )
for name in skill_ir.__all__:
    if getattr(legacy_skill_ir, name) is not getattr(skill_ir, name):
        raise RuntimeError(f"skill IR compatibility identity changed: {name}")
composition_step = skill_composition.SkillCompositionStep.from_dict(
    {
        "step_id": " Isolated\\nStep ",
        "skill": {"title": "Portable"},
        "bindings": [
            {
                "target_region": "a",
                "target_path": "/a/value",
                "constant_value": False,
                "mapper": {"kind": "rename"},
            }
        ],
    }
)
if composition_step.step_id != "Isolated Step":
    raise RuntimeError("skill composition text normalization changed")
if composition_step.bindings[0].constant_value is not False:
    raise RuntimeError("skill composition falsey constant handling changed")
invocation_result = skill_invocation.skill_invocation_result_from_mapping(
    {
        "skill_title": " Isolated\\nSkill ",
        "status": " ok ",
        "result_payload": False,
        "parsed_output": {"must_not": "win"},
    }
)
if invocation_result.to_dict() != {
    "skill_title": "Isolated Skill",
    "status": "ok",
    "answer": "",
    "error": "",
    "output_payload": False,
    "nested_run_outcome": "",
}:
    raise RuntimeError("skill invocation distribution behavior changed")
if skill_declaration.normalize_skill_schema_version(" bssc_skill.v2\\n") != "bssc_skill.v2":
    raise RuntimeError("skill declaration schema normalization changed")
if skill_declaration.composition_binding_targets(
    {
        "composition_rights": [
            "skill: First",
            "UNKNOWN:ignored",
            "INVOKE:Second",
            "title:First",
        ]
    }
) != ["First", "Second"]:
    raise RuntimeError("skill declaration composition-right projection changed")
if skill_execution.normalize_executor_framework_name(" SH ") != "bash":
    raise RuntimeError("skill executor descriptor alias normalization changed")
if skill_execution.ability_executor_framework(
    representation="python_script",
    content={"executor_framework": "wasm"},
) != "wasm_wasi":
    raise RuntimeError("explicit skill executor descriptor precedence changed")
if skill_execution.ability_executor_framework(
    representation="",
    content={"script_language": "shell", "python_script": "print(1)"},
) != "bash":
    raise RuntimeError("skill executor language inference precedence changed")
if skill_execution.ability_executable_text(
    representation="shell_script",
    content={"shell_script": "  printf ready  "},
) != "printf ready":
    raise RuntimeError("skill executable body selection changed")
raise SystemExit(main())
"""
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment["OPENAI_API_KEY"] = ""
        command = [
            sys.executable,
            "-c",
            script,
            str(app_installed),
            str(conversation_installed),
            str(engine_installed),
            str(governance_installed),
            str(host_interaction_installed),
            str(llm_installed),
            str(runtime_installed),
            str(semantics_installed),
            str(skill_semantics_installed),
            "run",
            "--prompt",
            "Verify the isolated core distributions.",
            "--llm",
            "off",
            "--max-steps",
            "0",
            "--sqlite",
            str(sqlite_path),
            "--state-out",
            str(state_path),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                json.dumps(
                    {
                        "returncode": error.returncode,
                        "stderr": error.stderr,
                        "stdout": error.stdout,
                    },
                    indent=2,
                    sort_keys=True,
                )
            ) from error
        summary = json.loads(completed.stdout)
        if not sqlite_path.is_file() or not state_path.is_file():
            raise RuntimeError(
                "isolated distribution run did not create SQLite and state outputs"
            )
        return {
            "sqlite_created": True,
            "state_created": True,
            "semantic_unit": summary["root"]["semantic_unit"],
            "vector_enabled": summary["llm"]["artifact_store"]["vector_enabled"],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-wheel", type=Path, required=True)
    parser.add_argument("--conversation-wheel", type=Path, required=True)
    parser.add_argument("--engine-wheel", type=Path, required=True)
    parser.add_argument("--governance-wheel", type=Path, required=True)
    parser.add_argument("--governance-sdist", type=Path, required=True)
    parser.add_argument("--host-interaction-wheel", type=Path, required=True)
    parser.add_argument("--llm-wheel", type=Path, required=True)
    parser.add_argument("--runtime-wheel", type=Path, required=True)
    parser.add_argument("--semantics-wheel", type=Path, required=True)
    parser.add_argument("--semantics-sdist", type=Path, required=True)
    parser.add_argument("--skill-semantics-wheel", type=Path, required=True)
    parser.add_argument("--skill-semantics-sdist", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "contents": _verify_contents(
            args.app_wheel,
            args.conversation_wheel,
            args.engine_wheel,
            args.governance_wheel,
            args.governance_sdist,
            args.host_interaction_wheel,
            args.llm_wheel,
            args.runtime_wheel,
            args.semantics_wheel,
            args.semantics_sdist,
            args.skill_semantics_wheel,
            args.skill_semantics_sdist,
        ),
        "smoke": _smoke(
            args.app_wheel,
            args.conversation_wheel,
            args.engine_wheel,
            args.governance_wheel,
            args.host_interaction_wheel,
            args.llm_wheel,
            args.runtime_wheel,
            args.semantics_wheel,
            args.skill_semantics_wheel,
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
