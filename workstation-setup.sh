#!/usr/bin/env bash

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$repo_root"

set -a
source ./local.env
set +a

export WORKSTATION_HOME="$PWD/ram/tmp/workstation-home"

rm -rf ./ram/tmp/workstation-home ./ram/tmp/workstation-root ./ram/tmp/workspace
mkdir -p ./ram/tmp/workspace/trials ./ram/tmp/workspace/src ./ram/tmp/workspace/exports

cp ./trials/symbolsearch/skill.yaml ./ram/tmp/workspace/trials/symbolsearch.skill.yaml
cp ./trials/python/skill.yaml ./ram/tmp/workspace/trials/python.skill.yaml

cat > ./ram/tmp/workspace/src/demo.py <<'PY'
class BSSCController:
    pass

class DemoRunner:
    pass
PY
