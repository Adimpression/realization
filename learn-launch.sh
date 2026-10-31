#!/usr/bin/env bash

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$repo_root"

uv run realized-workstation launch --root ./ram/tmp/workstation-root --workspace ./dst --task "Review learning contexts and build a report."
