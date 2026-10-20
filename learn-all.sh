rm -rf ./ram/tmp/
source  local.env
uv run python ./main.py workstation-launch --root ./ram/tmp/workstation-root --workspace /Users/ravindranathakila/service/realized/dst --task "Review learning contexts and build a report."
uv run python ./main.py workstation-chat --root ./ram/tmp/workstation-root
