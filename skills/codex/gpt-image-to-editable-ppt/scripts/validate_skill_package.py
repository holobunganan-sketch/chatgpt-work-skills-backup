from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path

REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "assets/default_design_system.yaml",
    "schemas/deck_spec.schema.json",
    "scripts/run_pipeline.py",
    "scripts/build_ppt.py",
    "scripts/validate_ppt.py",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    root = Path(args.root)
    errors = []
    for rel in REQUIRED:
        if not (root / rel).exists():
            errors.append(f"missing: {rel}")
    skill = (root / "SKILL.md").read_text(encoding="utf-8") if (root / "SKILL.md").exists() else ""
    if not re.match(r"^---\s*\nname:\s*[^\n]+\ndescription:\s*[^\n]+\n---", skill):
        errors.append("SKILL.md frontmatter is invalid or missing name/description")
    for script in (root / "scripts").glob("*.py"):
        try:
            py_compile.compile(str(script), doraise=True)
        except Exception as exc:
            errors.append(f"compile failed: {script.name}: {exc}")
    result = {"valid": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
