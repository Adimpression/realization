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
ENGINE_SOURCE_ROOT = REPO_ROOT / "core_engine" / "src"
ENGINE_PACKAGE_ROOT = ENGINE_SOURCE_ROOT / "realized_core_engine"
EXCHANGE_SOURCE_ROOT = REPO_ROOT / "exchange" / "src"
EXCHANGE_PACKAGE_ROOT = EXCHANGE_SOURCE_ROOT / "realized_exchange"


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
    engine_sdist: Path,
    governance_wheel: Path,
    governance_sdist: Path,
    host_interaction_wheel: Path,
    llm_wheel: Path,
    runtime_wheel: Path,
    semantics_wheel: Path,
    semantics_sdist: Path,
    exchange_wheel: Path,
    exchange_sdist: Path,
    blend_application_wheel: Path,
    blend_application_sdist: Path,
    skill_application_wheel: Path,
    skill_application_sdist: Path,
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
    exchange_entries = _wheel_entries(exchange_wheel)
    blend_application_entries = _wheel_entries(blend_application_wheel)
    skill_application_entries = _wheel_entries(skill_application_wheel)
    skill_semantics_entries = _wheel_entries(skill_semantics_wheel)
    engine_required = {
        path.relative_to(ENGINE_SOURCE_ROOT).as_posix()
        for path in ENGINE_PACKAGE_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }

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
        "realized_core_llm/transport.py",
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

    engine_missing = sorted(engine_required - engine_entries)
    engine_forbidden = sorted(
        entry
        for entry in engine_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_core_engine/")
        and ".dist-info/" not in entry
    )
    with tarfile.open(engine_sdist, mode="r:gz") as archive:
        engine_sdist_entries = set(archive.getnames())
    engine_sdist_prefix = "realized_core_engine-0.1.0"
    engine_sdist_required = {
        f"{engine_sdist_prefix}/pyproject.toml",
        f"{engine_sdist_prefix}/README.md",
        *{
            f"{engine_sdist_prefix}/src/{entry}"
            for entry in engine_required
        },
    }
    engine_sdist_missing = sorted(
        engine_sdist_required - engine_sdist_entries
    )
    engine_sdist_forbidden = sorted(
        entry
        for entry in engine_sdist_entries
        if entry in {
            f"{engine_sdist_prefix}/module_manifest.txt",
            f"{engine_sdist_prefix}/setup.py",
        }
    )

    governance_required = {
        "realized_core_governance/__init__.py",
        "realized_core_governance/_normalization.py",
        "realized_core_governance/admission.py",
        "realized_core_governance/approval.py",
        "realized_core_governance/authority.py",
        "realized_core_governance/current_use.py",
        "realized_core_governance/data.py",
        "realized_core_governance/declarations.py",
        "realized_core_governance/inventory.py",
        "realized_core_governance/lifecycle.py",
        "realized_core_governance/persistence.py",
        "realized_core_governance/py.typed",
        "realized_core_governance/records.py",
        "realized_core_governance/safety.py",
        "realized_core_governance/trace.py",
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
        f"{governance_sdist_prefix}/src/realized_core_governance/authority.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/current_use.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/data.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/declarations.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/inventory.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/lifecycle.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/persistence.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/py.typed",
        f"{governance_sdist_prefix}/src/realized_core_governance/records.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/safety.py",
        f"{governance_sdist_prefix}/src/realized_core_governance/trace.py",
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
        "realized_host_interaction/realizers.py",
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
        "python_skill_host.py",
        "realized_core_runtime/__init__.py",
        "realized_core_runtime/execution.py",
        "realized_core_runtime/host_abi.py",
        "realized_core_runtime/host_brokers.py",
        "realized_core_runtime/host_realizers.py",
        "realized_core_runtime/python_host.py",
        "realized_core_runtime/python_transport.py",
        "realized_core_runtime/contracts.py",
        "realized_core_runtime/reduction.py",
        "realized_core_runtime/wasm.py",
    }
    runtime_missing = sorted(runtime_required - runtime_entries)
    semantics_required = {
        "realized_core_semantics/__init__.py",
        "realized_core_semantics/artifacts.py",
        "realized_core_semantics/identifiers.py",
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
        f"{semantics_sdist_prefix}/src/realized_core_semantics/identifiers.py",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/py.typed",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/theory.py",
        f"{semantics_sdist_prefix}/src/realized_core_semantics/values.py",
    }
    semantics_sdist_missing = sorted(
        semantics_sdist_required - semantics_sdist_entries
    )
    exchange_required = {
        path.relative_to(EXCHANGE_SOURCE_ROOT).as_posix()
        for path in EXCHANGE_PACKAGE_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    exchange_missing = sorted(exchange_required - exchange_entries)
    exchange_forbidden = sorted(
        entry
        for entry in exchange_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_exchange/")
        and ".dist-info/" not in entry
    )
    with tarfile.open(exchange_sdist, mode="r:gz") as archive:
        exchange_sdist_entries = set(archive.getnames())
    exchange_sdist_prefix = "realized_exchange-0.1.0"
    exchange_sdist_required = {
        f"{exchange_sdist_prefix}/pyproject.toml",
        f"{exchange_sdist_prefix}/README.md",
        *{
            f"{exchange_sdist_prefix}/src/{entry}"
            for entry in exchange_required
        },
    }
    exchange_sdist_missing = sorted(
        exchange_sdist_required - exchange_sdist_entries
    )
    skill_semantics_required = {
        "realized_skill_semantics/__init__.py",
        "realized_skill_semantics/compatibility.py",
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
        f"{skill_semantics_sdist_prefix}/src/realized_skill_semantics/compatibility.py",
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
    blend_application_required = {
        "realized_blend_application/__init__.py",
        "realized_blend_application/execution.py",
        "realized_blend_application/operators.py",
        "realized_blend_application/py.typed",
        "realized_blend_application/workflow_store.py",
        "realized_blend_application/workflows.py",
        "realized_blend_application/world_store.py",
        "realized_blend_application/worlds.py",
    }
    blend_application_missing = sorted(
        blend_application_required - blend_application_entries
    )
    blend_application_forbidden = sorted(
        entry
        for entry in blend_application_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_blend_application/")
        and ".dist-info/" not in entry
    )
    with tarfile.open(blend_application_sdist, mode="r:gz") as archive:
        blend_application_sdist_entries = set(archive.getnames())
    blend_application_sdist_prefix = "realized_blend_application-0.1.0"
    blend_application_sdist_required = {
        f"{blend_application_sdist_prefix}/pyproject.toml",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/__init__.py",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/execution.py",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/operators.py",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/py.typed",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/workflow_store.py",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/workflows.py",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/world_store.py",
        f"{blend_application_sdist_prefix}/src/realized_blend_application/worlds.py",
    }
    blend_application_sdist_missing = sorted(
        blend_application_sdist_required - blend_application_sdist_entries
    )
    skill_application_required = {
        "realized_skill_application/__init__.py",
        "realized_skill_application/composition.py",
        "realized_skill_application/ir.py",
        "realized_skill_application/normalization.py",
        "realized_skill_application/projection.py",
        "realized_skill_application/py.typed",
    }
    skill_application_missing = sorted(
        skill_application_required - skill_application_entries
    )
    skill_application_forbidden = sorted(
        entry
        for entry in skill_application_entries
        if entry.endswith(".py")
        and not entry.startswith("realized_skill_application/")
        and ".dist-info/" not in entry
    )
    with tarfile.open(skill_application_sdist, mode="r:gz") as archive:
        skill_application_sdist_entries = set(archive.getnames())
    skill_application_sdist_prefix = "realized_skill_application-0.1.0"
    skill_application_sdist_required = {
        f"{skill_application_sdist_prefix}/pyproject.toml",
        f"{skill_application_sdist_prefix}/src/realized_skill_application/__init__.py",
        f"{skill_application_sdist_prefix}/src/realized_skill_application/composition.py",
        f"{skill_application_sdist_prefix}/src/realized_skill_application/ir.py",
        f"{skill_application_sdist_prefix}/src/realized_skill_application/normalization.py",
        f"{skill_application_sdist_prefix}/src/realized_skill_application/projection.py",
        f"{skill_application_sdist_prefix}/src/realized_skill_application/py.typed",
    }
    skill_application_sdist_missing = sorted(
        skill_application_sdist_required - skill_application_sdist_entries
    )
    if (
        app_missing
        or app_unexpected
        or conversation_forbidden
        or conversation_missing
        or engine_forbidden
        or engine_missing
        or engine_sdist_forbidden
        or engine_sdist_missing
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
        or exchange_forbidden
        or exchange_missing
        or exchange_sdist_missing
        or blend_application_forbidden
        or blend_application_missing
        or blend_application_sdist_missing
        or skill_application_forbidden
        or skill_application_missing
        or skill_application_sdist_missing
        or skill_semantics_forbidden
        or skill_semantics_missing
        or skill_semantics_sdist_missing
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
                    "engine_sdist_forbidden": engine_sdist_forbidden,
                    "engine_sdist_missing": engine_sdist_missing,
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
                    "exchange_forbidden": exchange_forbidden,
                    "exchange_missing": exchange_missing,
                    "exchange_sdist_missing": exchange_sdist_missing,
                    "blend_application_forbidden": blend_application_forbidden,
                    "blend_application_missing": blend_application_missing,
                    "blend_application_sdist_missing": blend_application_sdist_missing,
                    "skill_application_forbidden": skill_application_forbidden,
                    "skill_application_missing": skill_application_missing,
                    "skill_application_sdist_missing": skill_application_sdist_missing,
                    "skill_semantics_forbidden": skill_semantics_forbidden,
                    "skill_semantics_missing": skill_semantics_missing,
                    "skill_semantics_sdist_missing": skill_semantics_sdist_missing,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return {
        "app_entry_count": len(app_entries),
        "app_python_entries": sorted(app_python_entries),
        "canonical_module_count": len(
            {
                entry
                for entry in engine_entries
                if entry.startswith("realized_core_engine/")
                and entry.endswith(".py")
            }
        ),
        "conversation_entry_count": len(conversation_entries),
        "conversation_forbidden_entries": conversation_forbidden,
        "engine_entry_count": len(engine_entries),
        "engine_forbidden_entries": engine_forbidden,
        "engine_sdist_entry_count": len(engine_sdist_entries),
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
        "exchange_entry_count": len(exchange_entries),
        "exchange_forbidden_entries": exchange_forbidden,
        "exchange_sdist_entry_count": len(exchange_sdist_entries),
        "blend_application_entry_count": len(blend_application_entries),
        "blend_application_forbidden_entries": blend_application_forbidden,
        "blend_application_sdist_entry_count": len(blend_application_sdist_entries),
        "skill_application_entry_count": len(skill_application_entries),
        "skill_application_forbidden_entries": skill_application_forbidden,
        "skill_application_sdist_entry_count": len(skill_application_sdist_entries),
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
    exchange_wheel: Path,
    blend_wheel: Path,
    blend_application_wheel: Path,
    skill_application_wheel: Path,
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
        exchange_installed = root / "exchange"
        blend_installed = root / "blend"
        blend_application_installed = root / "blend-application"
        skill_application_installed = root / "skill-application"
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
            exchange_installed,
            blend_installed,
            blend_application_installed,
            skill_application_installed,
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
        _extract(exchange_wheel, exchange_installed)
        _extract(blend_wheel, blend_installed)
        _extract(blend_application_wheel, blend_application_installed)
        _extract(skill_application_wheel, skill_application_installed)
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
exchange_target = Path(sys.argv.pop(1)).resolve()
blend_target = Path(sys.argv.pop(1)).resolve()
blend_application_target = Path(sys.argv.pop(1)).resolve()
skill_application_target = Path(sys.argv.pop(1)).resolve()
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
    str(exchange_target),
    str(blend_target),
    str(blend_application_target),
    str(skill_application_target),
    str(skill_semantics_target),
]
from realized_core_runtime import execution as execution_frameworks
import realized_core
import realized_core_conversation
import realized_core_engine
import realized_core_engine.controller_runtime as controller_runtime
import realized_core_engine.governance_inventory as governance_inventory
import realized_core_engine.skill_governance as skill_governance
import realized_core_governance
import realized_host_interaction
import realized_core_llm
import realized_core_runtime
import realized_core_semantics
import realized_exchange
import realized_blend
import realized_blend_application
import realized_skill_application
import realized_skill_semantics
from realized_core_engine import constitutional_trace as engine_constitutional_trace
from realized_core_engine.state import SystemState
from realized_core_governance import admission as governance_admission
from realized_core_governance import authority as governance_authority
from realized_core_governance import current_use as governance_current_use
from realized_core_governance import declarations as governance_declarations
from realized_core_governance import inventory as governance_inventory_owner
from realized_core_governance import persistence as governance_persistence
from realized_core_governance import trace as governance_trace
from realized_core_semantics.applied_model import Artifact
from realized_blend_application import workflow_store as blend_application_workflow_store
from realized_blend_application import worlds as blend_application_worlds
from realized_skill_semantics import composition as skill_composition
from realized_skill_semantics import declaration as skill_declaration
from realized_skill_semantics import execution as skill_execution
from realized_skill_semantics import invocation as skill_invocation
from realized_skill_application import composition as skill_application_composition
from realized_skill_application import ir as skill_application_ir
from realized_skill_application import normalization as skill_application_normalization
from realized_skill_application import projection as skill_application_projection
from realized_exchange import skill_export as exchange_skill_export
from realized_exchange import registry as exchange_registry
from realized_exchange import run_bundle as exchange_run_bundle
from realized_exchange import skill_schema as exchange_skill_schema
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
    (realized_exchange, exchange_target),
    (realized_blend, blend_target),
    (realized_blend_application, blend_application_target),
    (realized_skill_application, skill_application_target),
    (realized_skill_semantics, skill_semantics_target),
)
for module, owner in expected_owners:
    module_path = Path(module.__file__).resolve()
    if not module_path.is_relative_to(owner):
        raise RuntimeError(
            f"{module.__name__} escaped its wheel extraction: {module_path}"
        )
blend_workspace = Path.cwd() / "blend-workspace"
blend_workspace.mkdir()
blend_world = blend_application_worlds.ensure_blend_workstation_world(
    root_path=Path.cwd() / "blend-world",
    workspace_path=blend_workspace,
)
if not blend_world.world_id or blend_world.metadata.get("workspace_path") != str(
    blend_workspace.resolve()
):
    raise RuntimeError("blend application world materialization changed")
blend_store_paths = blend_application_workflow_store.ensure_blend_workflow_store(
    Path.cwd() / "blend-workflows"
)
if not all(
    Path(path).is_dir()
    for key, path in blend_store_paths.items()
    if key != "index"
) or not Path(blend_store_paths["index"]).is_file():
    raise RuntimeError("blend application workflow store materialization changed")
skill_artifact = Artifact.from_dict(
    {
        "id": "artifact-isolated-skill-application",
        "title": "Isolated Skill Application",
        "artifact_type": "ability",
        "representation": "yaml",
        "content": {
            "input_contract": {"query": "String"},
            "output_contract": {"answer": "String"},
        },
    }
)
if skill_application_ir.canonical_skill_ir_from_artifact(
    skill_artifact
).artifact_id != "artifact-isolated-skill-application":
    raise RuntimeError("skill application IR projection changed")
if not skill_application_normalization.synthesized_skill_normalization_for_artifact(
    skill_artifact
).get("regions"):
    raise RuntimeError("skill application normalization changed")
if not callable(skill_application_composition.execute_skill_composition_plan):
    raise RuntimeError("skill application composition surface is unavailable")
if skill_application_projection.skill_kind_from_artifact(skill_artifact) != "ability":
    raise RuntimeError("skill application projection changed")
exchange_artifact = exchange_skill_schema.artifact_from_skill_document(
    {
        "schema": "bssc_skill.v1",
        "kind": "knowledge",
        "title": "Isolated Exchange Knowledge",
        "answer": "The exchange distribution is isolated.",
    }
)
exchange_bundle = exchange_skill_export.export_skill_bundle_text(
    [exchange_artifact]
)
if "Isolated Exchange Knowledge" not in exchange_bundle:
    raise RuntimeError("exchange skill projection changed")
exchange_registry_document = exchange_registry.skill_registry_document(
    [exchange_artifact]
)
if exchange_registry_document.get("entry_count") != 1:
    raise RuntimeError("exchange registry projection changed")
isolated_bundle_state = SystemState.bootstrap(
    "Verify isolated run-bundle exchange."
)
isolated_trace = engine_constitutional_trace.constitutional_trace_snapshot(
    isolated_bundle_state
)
if isolated_trace.get("schema") != "bssc_constitutional_trace.v1":
    raise RuntimeError("engine constitutional trace projection changed")
isolated_bundle = exchange_run_bundle.run_bundle_document(
    isolated_bundle_state,
    None,
    llm_policy="off",
    max_steps=0,
)
if isolated_bundle.get("schema") != "bssc_run_bundle.v1":
    raise RuntimeError("exchange run-bundle projection changed")
host_realizer_calls = []
host_realizer_provider = realized_host_interaction.StaticHostRealizerProvider(
    brokers=(
        realized_host_interaction.HostBrokerBinding(
            descriptor=realized_host_interaction.HostRealizerDescriptor(
                kind="broker",
                identity="test.echo",
            ),
            callback=lambda invocation, active: host_realizer_calls.append(
                invocation.identity
            ) or {"value": invocation.arguments.get("value")},
        ),
        realized_host_interaction.HostBrokerBinding(
            descriptor=realized_host_interaction.HostRealizerDescriptor(
                kind="broker",
                identity="fs.read_text",
            ),
            callback=lambda invocation, active: host_realizer_calls.append(
                invocation.identity
            ) or {
                "status": "ok",
                "path": invocation.arguments.get("path"),
                "text": "response from installed parent provider",
            },
        ),
    ),
)
if not host_realizer_provider.inspect_broker("test.echo").available:
    raise RuntimeError("installed host-realizer ABI did not advertise exact binding")
if host_realizer_provider.inspect_broker("TEST.ECHO").registered:
    raise RuntimeError("installed host-realizer ABI changed exact identity semantics")
host_realizer_result = host_realizer_provider.invoke_broker(
    realized_host_interaction.HostBrokerInvocation(
        identity="test.echo",
        arguments={"value": "isolated"},
    )
)
if host_realizer_result != {"value": "isolated"}:
    raise RuntimeError("installed host-realizer ABI changed invocation result")
if host_realizer_calls != ["test.echo"]:
    raise RuntimeError("installed host-realizer ABI did not invoke exact callback")
host_context = realized_host_interaction.host_native_interaction_context(
    realizer_provider=host_realizer_provider,
)
if realized_host_interaction.host_realizer_provider(host_context) is not host_realizer_provider:
    raise RuntimeError("installed host context did not preserve injected provider identity")
child_execution = execution_frameworks.execute_cross_boundary(
    framework="python3",
    executable_text='''
import json
import sys

from python_skill_host import broker_request

payload = json.load(sys.stdin)
result = broker_request("fs.read_text", path=payload["path"])
print(json.dumps({"status": "ok", "answer": "", "result": result, "notes": []}))
''',
    stdin_payload={"path": "/isolated/example.txt"},
    host_runtime_context={
        "artifact_id": "isolated-python-child",
        "artifact_title": "Installed Python child bridge",
        "semantic_unit": "Verify installed child-to-parent broker invocation.",
        "strict_realizer_declaration": True,
        "declared_host_brokers": ["fs.read_text"],
        "admission": {"status": "admitted", "admitted": True},
        "grants": [{"id": "isolated-read", "authority": "read"}],
    },
    realizer_provider=host_realizer_provider,
)
if not child_execution.ok:
    raise RuntimeError(
        "installed Python child bridge failed: "
        + (child_execution.stderr or child_execution.stdout)
    )
if child_execution.result != {
    "status": "ok",
    "path": "/isolated/example.txt",
    "text": "response from installed parent provider",
}:
    raise RuntimeError("installed Python child bridge changed broker result")
if host_realizer_calls != ["test.echo", "fs.read_text"]:
    raise RuntimeError("installed Python child did not use the injected parent provider")
if not child_execution.metadata.get("host_traces"):
    raise RuntimeError("installed Python child bridge did not return effect trace evidence")
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
if governance_current_use.skill_current_use_allows_invocation(
    schema_version="bssc_skill.v1",
    admission={"status": "rejected"},
    lifecycle={"quarantine_status": "quarantined"},
) != (True, ""):
    raise RuntimeError("legacy current-use compatibility changed")
if governance_current_use.skill_current_use_allows_invocation(
    schema_version="bssc_skill.v2",
    admission={"status": "admitted"},
    lifecycle={"activation_status": "inactive"},
) != (False, "Governed skill activation status is inactive."):
    raise RuntimeError("governed current-use lifecycle evaluation changed")
if governance_current_use.skill_current_use_allows_invocation(
    schema_version="bssc_skill.v2",
    admission=None,
    lifecycle=None,
) != (False, "Governed skill has no admission record."):
    raise RuntimeError("governed current-use admission default changed")
authority_snapshot = governance_authority.evaluate_authority_grants(
    effect_kind="execute.python3",
    required_authority="execute",
    admitted=True,
    admission_reason="",
    grants=[{"id": "grant-execute", "authority": "execute"}],
)
if not authority_snapshot.allowed:
    raise RuntimeError("governance authority coverage changed")
if authority_snapshot.grant_ids != ("grant-execute",):
    raise RuntimeError("governance authority grant projection changed")
effect_receipt = governance_trace.effect_trace_receipt(
    " request ",
    {
        "status": "legacy_implicit_admit",
        "created_at": "volatile",
        "effect_kind": "execute.python3",
    },
)
if effect_receipt != {
    "schema": "bssc_effect_receipt.v1",
    "kind": "request",
    "digest": "cc1d6f82cac827e5302e9945205b3fe3778ac414623c3e2053075a0f836f83e9",
}:
    raise RuntimeError("governance effect receipt semantics changed")
effect_signature = governance_trace.effect_trace_signature(
    {
        "artifact_title": "Bounded ability",
        "request": {
            "effect_kind": "execute.python3",
            "executor_framework": "python3",
            "invocation_payload": {"count": 2},
        },
        "decision": {"allowed": True, "required_authority": "execute"},
        "declaration": {"authorities_requested": ["execute"]},
        "admission": {
            "status": "admitted",
            "policy_titles": ["Policy"],
            "approval_titles": ["Approval"],
            "required_approval_class": "operator_approved",
        },
        "lifecycle": {
            "activation_status": "inactive",
            "trust_status": "revoked",
        },
        "grants": [{"authority": "execute", "admission_status": "admitted"}],
        "result": {"ok": True, "exit_code": 0, "answer": {"answer": 4}},
    }
)
if effect_signature != {
    "artifact_title": "Bounded ability",
    "effect_kind": "execute.python3",
    "required_authority": "execute",
    "allowed": True,
    "executor_framework": "python3",
    "admission_status": "admitted",
    "activation_status": "active",
    "trust_status": "trusted",
    "ok": True,
    "exit_code": 0,
    "answer": '{"answer":4}',
    "receipt_digests": {
        "request": '{"effect_kind":"execute.python3","executor_framework":"python3","invocation_payload":{"count":2}}',
        "declaration": '{"authorities_requested":["execute"]}',
        "policy": '{"policy_titles":["Policy"],"required_approval_class":"operator_approved"}',
        "approval": '{"approval_titles":["Approval"],"required_approval_class":"operator_approved"}',
        "lifecycle": '{"activation_status":"active","admission_status":"admitted","installation_status":"","quarantine_status":"","review_status":"","trust_status":"trusted"}',
        "grants": '[{"admission_status":"admitted","approval_class":"automatic","authority":"execute","context":"","data_classes_touched":[],"duration":"","effect_kind":"","executor_framework":"","policy_titles":[],"risk_tier":"","scope":"","semantic_unit":"","side_effects":[],"target":"","triggering_conditions":[]}]',
    },
}:
    raise RuntimeError("governance constitutional effect signature changed")

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


class _GovernanceWriter:
    def __init__(self):
        self.calls = []
        self.report = {"status": "persisted", "reports": []}

    def persist_artifacts(self, artifacts, *, run_id="artifact_import"):
        self.calls.append((artifacts, run_id))
        return self.report


governance_writer = _GovernanceWriter()
governance_batch = [overlapping_governance_artifact]
governance_write_report = governance_persistence.persist_governed_artifacts(
    governance_writer,
    governance_batch,
    run_id="skill_import:policy_batch",
)
if not isinstance(governance_writer, governance_persistence.GovernanceArtifactWriter):
    raise RuntimeError("governance persistence writer protocol changed")
if governance_write_report is not governance_writer.report:
    raise RuntimeError("governance persistence changed report identity")
if governance_writer.calls != [(governance_batch, "skill_import:policy_batch")]:
    raise RuntimeError("governance persistence changed batch forwarding")
for name in skill_execution.__all__:
    if getattr(execution_frameworks, name) is not getattr(skill_execution, name):
        raise RuntimeError(
            f"runtime execution descriptor identity changed: {name}"
        )
if hasattr(skill_execution, "normalize_supported_executor_frameworks"):
    raise RuntimeError("portable descriptor package acquired host-support behavior")
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
            str(exchange_installed),
            str(blend_installed),
            str(blend_application_installed),
            str(skill_application_installed),
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
    parser.add_argument("--engine-sdist", type=Path, required=True)
    parser.add_argument("--governance-wheel", type=Path, required=True)
    parser.add_argument("--governance-sdist", type=Path, required=True)
    parser.add_argument("--host-interaction-wheel", type=Path, required=True)
    parser.add_argument("--llm-wheel", type=Path, required=True)
    parser.add_argument("--runtime-wheel", type=Path, required=True)
    parser.add_argument("--semantics-wheel", type=Path, required=True)
    parser.add_argument("--semantics-sdist", type=Path, required=True)
    parser.add_argument("--exchange-wheel", type=Path, required=True)
    parser.add_argument("--exchange-sdist", type=Path, required=True)
    parser.add_argument("--blend-wheel", type=Path, required=True)
    parser.add_argument("--blend-application-wheel", type=Path, required=True)
    parser.add_argument("--blend-application-sdist", type=Path, required=True)
    parser.add_argument("--skill-application-wheel", type=Path, required=True)
    parser.add_argument("--skill-application-sdist", type=Path, required=True)
    parser.add_argument("--skill-semantics-wheel", type=Path, required=True)
    parser.add_argument("--skill-semantics-sdist", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "contents": _verify_contents(
            args.app_wheel,
            args.conversation_wheel,
            args.engine_wheel,
            args.engine_sdist,
            args.governance_wheel,
            args.governance_sdist,
            args.host_interaction_wheel,
            args.llm_wheel,
            args.runtime_wheel,
            args.semantics_wheel,
            args.semantics_sdist,
            args.exchange_wheel,
            args.exchange_sdist,
            args.blend_application_wheel,
            args.blend_application_sdist,
            args.skill_application_wheel,
            args.skill_application_sdist,
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
            args.exchange_wheel,
            args.blend_wheel,
            args.blend_application_wheel,
            args.skill_application_wheel,
            args.skill_semantics_wheel,
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
