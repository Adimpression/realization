rm -rf ./ram/tmp/
source  local.env
uv run python ./main.py workstation-launch --root /Users/ravindranathakila/research/workstations/ai --workspace /Users/ravindranathakila/research/ --task "Research"
uv run python ./main.py workstation-chat --root /Users/ravindranathakila/research/workstations/ai
