#!/usr/bin/env bash

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$repo_root"

rm -rf ./ram/tmp/
source local.env
uv run realized-workstation launch --root ./ram/tmp/workstation-root --workspace ./dst --task "Review learning contexts and build a report."
uv run realized-workstation chat --root ./ram/tmp/workstation-root
