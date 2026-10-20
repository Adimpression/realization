#!/bin/zsh
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
RAM_LINK="$SCRIPT_DIR/ram"
DEFAULT_VOLUME_NAME="REALIZED_RAMDISK"
VOLUME_NAME="${REALIZED_RAMDISK_VOLUME:-${VALIDATION_SQLITE_RAMDISK_VOLUME:-$DEFAULT_VOLUME_NAME}}"
SIZE_MB="${REALIZED_RAMDISK_SIZE_MB:-${VALIDATION_SQLITE_RAMDISK_SIZE_MB:-2048}}"

if ! [[ "$SIZE_MB" =~ '^[0-9]+$' ]]; then
  echo "REALIZED_RAMDISK_SIZE_MB must be an integer." >&2
  exit 1
fi
if (( SIZE_MB < 256 )); then
  SIZE_MB=256
fi

ensure_link_target() {
  local target="$1"
  if [[ -L "$RAM_LINK" ]]; then
    local current_target
    current_target=$(readlink "$RAM_LINK")
    if [[ "$current_target" == "$target" ]]; then
      return 0
    fi
    rm "$RAM_LINK"
  elif [[ -e "$RAM_LINK" ]]; then
    if [[ -d "$RAM_LINK" ]]; then
      if [[ -n "$(ls -A "$RAM_LINK")" ]]; then
        echo "Refusing to replace non-empty $RAM_LINK." >&2
        exit 1
      fi
      rmdir "$RAM_LINK"
    else
      echo "Refusing to replace non-directory $RAM_LINK." >&2
      exit 1
    fi
  fi
  ln -s "$target" "$RAM_LINK"
}

case "$(uname -s)" in
  Darwin)
    TARGET="/Volumes/$VOLUME_NAME"
    if [[ ! -d "$TARGET" ]]; then
      SECTORS=$((SIZE_MB * 2048))
      DEVICE=$(hdiutil attach -nomount "ram://${SECTORS}" | awk 'END {print $1}')
      diskutil erasevolume HFS+ "$VOLUME_NAME" "$DEVICE" >/dev/null
      for _ in {1..50}; do
        if [[ -d "$TARGET" ]]; then
          break
        fi
        sleep 0.1
      done
      if [[ ! -d "$TARGET" ]]; then
        echo "RAM disk volume $VOLUME_NAME did not appear at $TARGET." >&2
        exit 1
      fi
    fi
    ensure_link_target "$TARGET"
    ;;
  Linux)
    if [[ -d /dev/shm ]]; then
      TARGET="/dev/shm/$VOLUME_NAME"
      mkdir -p "$TARGET"
      ensure_link_target "$TARGET"
    else
      mkdir -p "$RAM_LINK"
      TARGET="$RAM_LINK"
      echo "No /dev/shm available; using regular directory $RAM_LINK." >&2
    fi
    ;;
  *)
    mkdir -p "$RAM_LINK"
    TARGET="$RAM_LINK"
    echo "Unsupported OS $(uname -s); using regular directory $RAM_LINK." >&2
    ;;
esac

mkdir -p "$RAM_LINK/tmp" "$RAM_LINK/sqlite"

echo "ram ready: $RAM_LINK"
echo "target: $TARGET"
echo "volume: $VOLUME_NAME"
echo "size_mb: $SIZE_MB"
