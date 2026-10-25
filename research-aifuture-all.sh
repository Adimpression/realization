#!/usr/bin/env bash

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
research_root="${REALIZED_RESEARCH_HOME:-$HOME/research}"
workstation_root="${REALIZED_RESEARCH_WORKSTATION_HOME:-$research_root/workstations/ai}"
cd "$repo_root"

rm -rf ./ram/tmp/
source local.env
uv run python ./main.py workstation-launch --root "$workstation_root" --workspace "$research_root" --task "Research"
uv run python ./main.py workstation-chat --root "$workstation_root"
