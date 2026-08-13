#!/usr/bin/env bash
set -euo pipefail
SKILL_NAME="gpt-image-to-editable-ppt"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_ROOT="$HOME/.agents/skills"
TARGET="$TARGET_ROOT/$SKILL_NAME"
mkdir -p "$TARGET_ROOT"
rm -rf "$TARGET"
cp -R "$SOURCE_DIR" "$TARGET"
echo "Installed to $TARGET"
echo 'Restart Codex if needed. Invoke with $gpt-image-to-editable-ppt.'
