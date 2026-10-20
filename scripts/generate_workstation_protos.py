#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROTO_FILENAMES = (
    "workstation_assets.proto",
    "workstation_bootstrap.proto",
    "subject_workflow.proto",
    "workstation_shell.proto",
)


def _resolve_dart_plugin() -> str:
    candidates = (
        shutil.which("protoc-gen-dart"),
        str(Path.home() / ".pub-cache" / "bin" / "protoc-gen-dart"),
    )
    for candidate in candidates:
        if candidate and Path(candidate).expanduser().exists():
            return str(Path(candidate).expanduser().resolve())
    raise SystemExit(
        "Unable to find protoc-gen-dart. Install it with "
        "`dart pub global activate protoc_plugin` first."
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    proto_source_root = repo_root / "workstation" / "grpc_definitions" / "src"
    proto_root = proto_source_root / "workstation" / "grpc" / "definitions"
    dart_output_root = repo_root / "workstation" / "ui_flutter" / "lib" / "src" / "generated"
    dart_output_root.mkdir(parents=True, exist_ok=True)
    proto_paths = [str(proto_root / filename) for filename in PROTO_FILENAMES]

    python_command = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{proto_source_root}",
        f"--python_out={proto_source_root}",
        f"--grpc_python_out={proto_source_root}",
        *proto_paths,
    ]
    python_result = subprocess.call(python_command, cwd=repo_root)
    if python_result != 0:
        return python_result

    dart_command = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{proto_source_root}",
        f"--plugin=protoc-gen-dart={_resolve_dart_plugin()}",
        f"--dart_out=grpc:{dart_output_root}",
        *proto_paths,
    ]
    return subprocess.call(dart_command, cwd=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
