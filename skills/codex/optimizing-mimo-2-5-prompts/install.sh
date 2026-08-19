#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_ROOT="${1:-$HOME/.agents/skills}"
SKILL_NAME="$(basename "$SOURCE_DIR")"
DEST="$DEST_ROOT/$SKILL_NAME"
mkdir -p "$DEST_ROOT"
if [[ -e "$DEST" ]]; then
  echo "Destination exists: $DEST" >&2
  echo "Remove it first or choose another destination root." >&2
  exit 2
fi
cp -R "$SOURCE_DIR" "$DEST"
echo "Installed $SKILL_NAME to $DEST"
