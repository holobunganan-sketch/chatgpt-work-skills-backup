#!/usr/bin/env python3
"""Validate this skill's structure without external dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
LINK_RE = re.compile(r"\[[^\]]+\]\((references/[^)]+)\)")


def parse_frontmatter(text: str):
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    lines = text[4:end].splitlines()
    values = {}
    for line in lines:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def validate(skill_root: Path):
    errors = []
    skill_file = skill_root / "SKILL.md"
    if not skill_file.exists():
        return ["Missing SKILL.md"]
    text = skill_file.read_text(encoding="utf-8")
    try:
        metadata = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    if set(metadata) != {"name", "description"}:
        errors.append("Frontmatter must contain only name and description")
    name = metadata.get("name", "")
    if not NAME_RE.fullmatch(name):
        errors.append("name must use lowercase letters, digits, and hyphens and be <=64 characters")
    if skill_root.name != name:
        errors.append(f"Folder name {skill_root.name!r} must equal skill name {name!r}")
    description = metadata.get("description", "")
    if not description:
        errors.append("description is required")
    if len((name + description).encode("utf-8")) > 1024:
        errors.append("Frontmatter name and description exceed 1024 bytes")
    if len(text.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines")
    if re.search(r"\b(TODO|TBD|FIXME)\b", text):
        errors.append("SKILL.md contains an unresolved placeholder")

    for relative in LINK_RE.findall(text):
        if not (skill_root / relative).exists():
            errors.append(f"Missing referenced file: {relative}")

    ui_file = skill_root / "agents" / "openai.yaml"
    if not ui_file.exists():
        errors.append("Missing agents/openai.yaml")
    else:
        ui = ui_file.read_text(encoding="utf-8")
        if "interface:" not in ui:
            errors.append("agents/openai.yaml is missing interface")
        if f"${name}" not in ui:
            errors.append("agents/openai.yaml default_prompt must mention the skill by $name")
        short_match = re.search(r'^\s*short_description:\s*"([^"]+)"\s*$', ui, re.MULTILINE)
        if not short_match:
            errors.append("short_description must be a quoted string")
        elif not 25 <= len(short_match.group(1)) <= 64:
            errors.append("short_description must contain 25-64 characters")
        for line in ui.splitlines():
            if ":" in line and line.strip() and not line.lstrip().startswith("#"):
                key, value = line.split(":", 1)
                if value.strip() and not (value.strip().startswith('"') and value.strip().endswith('"')):
                    errors.append(f"String value must be quoted in agents/openai.yaml: {line.strip()}")

    required_scripts = {
        "discover_models.py",
        "build_model_registry.py",
        "route_tasks.py",
        "validate_orchestration_plan.py",
        "record_outcome.py",
        "self_test.py",
    }
    existing = {x.name for x in (skill_root / "scripts").glob("*.py")}
    for missing in sorted(required_scripts - existing):
        errors.append(f"Missing required script: scripts/{missing}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"VALID: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
