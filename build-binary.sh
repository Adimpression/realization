#!/usr/bin/env zsh
set -euo pipefail

cd "$(dirname "$0")"

uv sync --group build
uv run pyinstaller --noconfirm --clean realized.spec

echo "Built binary: $(pwd)/dist/realized"
