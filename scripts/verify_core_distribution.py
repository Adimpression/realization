#!/usr/bin/env python3
"""Inspect and execute built core wheels without the repository on sys.path."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
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
    host_interaction_wheel: Path,
    llm_wheel: Path,
    runtime_wheel: Path,
) -> dict[str, object]:
    app_entries = _wheel_entries(app_wheel)
    conversation_entries = _wheel_entries(conversation_wheel)
    engine_entries = _wheel_entries(engine_wheel)
    host_interaction_entries = _wheel_entries(host_interaction_wheel)
    llm_entries = _wheel_entries(llm_wheel)
    runtime_entries = _wheel_entries(runtime_wheel)
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
    if (
        app_missing
        or app_unexpected
        or conversation_forbidden
        or conversation_missing
        or engine_forbidden
        or engine_missing
        or host_interaction_forbidden
        or host_interaction_missing
        or llm_forbidden
        or llm_missing
        or runtime_missing
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
                    "host_interaction_forbidden": host_interaction_forbidden,
                    "host_interaction_missing": host_interaction_missing,
                    "llm_forbidden": llm_forbidden,
                    "llm_missing": llm_missing,
                    "runtime_missing": runtime_missing,
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
        "host_interaction_entry_count": len(host_interaction_entries),
        "host_interaction_forbidden_entries": host_interaction_forbidden,
        "llm_entry_count": len(llm_entries),
        "llm_forbidden_entries": llm_forbidden,
        "runtime_entry_count": len(runtime_entries),
    }


def _smoke(
    app_wheel: Path,
    conversation_wheel: Path,
    engine_wheel: Path,
    host_interaction_wheel: Path,
    llm_wheel: Path,
    runtime_wheel: Path,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="realized-core-wheel-") as temporary_dir:
        root = Path(temporary_dir).resolve()
        app_installed = root / "app"
        conversation_installed = root / "conversation"
        engine_installed = root / "engine"
        host_interaction_installed = root / "host-interaction"
        llm_installed = root / "llm"
        runtime_installed = root / "runtime"
        for target in (
            app_installed,
            conversation_installed,
            engine_installed,
            host_interaction_installed,
            llm_installed,
            runtime_installed,
        ):
            target.mkdir()
        _extract(app_wheel, app_installed)
        _extract(conversation_wheel, conversation_installed)
        _extract(engine_wheel, engine_installed)
        _extract(host_interaction_wheel, host_interaction_installed)
        _extract(llm_wheel, llm_installed)
        _extract(runtime_wheel, runtime_installed)
        sqlite_path = root / "state.sqlite3"
        state_path = root / "state.json"
        script = """
import json
from pathlib import Path
import sys

app_target = Path(sys.argv.pop(1)).resolve()
conversation_target = Path(sys.argv.pop(1)).resolve()
engine_target = Path(sys.argv.pop(1)).resolve()
host_interaction_target = Path(sys.argv.pop(1)).resolve()
llm_target = Path(sys.argv.pop(1)).resolve()
runtime_target = Path(sys.argv.pop(1)).resolve()
sys.path[:0] = [
    str(app_target),
    str(conversation_target),
    str(engine_target),
    str(host_interaction_target),
    str(llm_target),
    str(runtime_target),
]
import controller_runtime
import realized_core
import realized_core_conversation
import realized_core_engine
import realized_host_interaction
import realized_core_llm
import realized_core_runtime
from realized_core.cli import main

expected_owners = (
    (controller_runtime, engine_target),
    (realized_core, app_target),
    (realized_core_conversation, conversation_target),
    (realized_core_engine, engine_target),
    (realized_host_interaction, host_interaction_target),
    (realized_core_llm, llm_target),
    (realized_core_runtime, runtime_target),
)
for module, owner in expected_owners:
    module_path = Path(module.__file__).resolve()
    if not module_path.is_relative_to(owner):
        raise RuntimeError(
            f"{module.__name__} escaped its wheel extraction: {module_path}"
        )
raise SystemExit(main())
"""
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment["OPENAI_API_KEY"] = ""
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(app_installed),
                str(conversation_installed),
                str(engine_installed),
                str(host_interaction_installed),
                str(llm_installed),
                str(runtime_installed),
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
            ],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
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
    parser.add_argument("--host-interaction-wheel", type=Path, required=True)
    parser.add_argument("--llm-wheel", type=Path, required=True)
    parser.add_argument("--runtime-wheel", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "contents": _verify_contents(
            args.app_wheel,
            args.conversation_wheel,
            args.engine_wheel,
            args.host_interaction_wheel,
            args.llm_wheel,
            args.runtime_wheel,
        ),
        "smoke": _smoke(
            args.app_wheel,
            args.conversation_wheel,
            args.engine_wheel,
            args.host_interaction_wheel,
            args.llm_wheel,
            args.runtime_wheel,
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
