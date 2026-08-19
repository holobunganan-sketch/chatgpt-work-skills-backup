#!/usr/bin/env bash
set -euo pipefail
SKILL_NAME="optimizing-deepseek-v4-flash-prompts"
SOURCE="$(cd "$(dirname "$0")" && pwd)"
TARGET_ROOT="$HOME/.agents/skills"
TARGET="$TARGET_ROOT/$SKILL_NAME"
mkdir -p "$TARGET_ROOT"
rm -rf "$TARGET"
cp -R "$SOURCE" "$TARGET"
python3 "$TARGET/scripts/deepseek_prompt_tool.py" doctor
echo "Installed: $TARGET"
