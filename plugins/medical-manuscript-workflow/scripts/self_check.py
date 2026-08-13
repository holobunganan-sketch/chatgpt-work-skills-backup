from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {
    "manuscript-workflow-orchestrator",
    "source-pack-builder",
    "write-evidence-grounded-manuscript",
    "writing-result-centered-discussion",
    "argument-centered-formal-editor",
    "human-in-loop-revision",
    "docx-precision-edit",
    "format-manuscript-delivery",
    "journal-format-reviewer",
    "cross-artifact-consistency",
    "traceable-release-auditor",
    "formal-deliverable-boundary-guard",
}
SCHEMA_EXAMPLES = {
    "project-contract.schema.json": "project-contract.example.json",
    "reviewer-ledger.schema.json": "reviewer-ledger.example.json",
    "delivery-policy.schema.json": "delivery-policy.default.json",
}
ORCHESTRATOR_REFERENCES = {
    "ROUTING.md",
    "PROJECT_CONTRACT.md",
    "REVIEWER_REVISION.md",
    "DELIVERY_BOUNDARY.md",
    "QUALITY_GATES.md",
}
PROHIBITED_WRITING_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"不是.{0,100}而是",
        r"并非.{0,100}而是",
        r"与其说.{0,100}不如说",
        r"不只.{0,100}还",
        r"不仅.{0,100}更",
        r"表面上.{0,100}本质上",
        r"真正关键的",
    )
]


def _problem(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    loaded = yaml.safe_load(text[4:end])
    return loaded if isinstance(loaded, dict) else None


def structure_issues(root: Path | None = None) -> list[dict[str, str]]:
    root = Path(root) if root else ROOT
    issues: list[dict[str, str]] = []
    manifest_path = root / ".codex-plugin/plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return [_problem("invalid_manifest", str(manifest_path), str(exc))]
    if manifest.get("name") != "medical-manuscript-workflow":
        issues.append(_problem("invalid_plugin_name", str(manifest_path), "Unexpected plugin name."))
    if manifest.get("skills") != "./skills/":
        issues.append(_problem("invalid_skills_path", str(manifest_path), "Manifest must expose ./skills/."))
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", str(manifest.get("version", ""))):
        issues.append(_problem("invalid_version", str(manifest_path), "Plugin version must be semantic."))

    skills_root = root / "skills"
    present = {path.name for path in skills_root.iterdir() if path.is_dir()} if skills_root.is_dir() else set()
    if present != EXPECTED_SKILLS:
        missing = sorted(EXPECTED_SKILLS - present)
        extra = sorted(present - EXPECTED_SKILLS)
        issues.append(_problem("skill_inventory_mismatch", str(skills_root), f"missing={missing}; extra={extra}"))
    for skill_name in sorted(EXPECTED_SKILLS & present):
        skill_path = skills_root / skill_name / "SKILL.md"
        metadata = _frontmatter(skill_path) if skill_path.exists() else None
        if metadata is None:
            issues.append(_problem("invalid_skill_frontmatter", str(skill_path), "Missing or invalid YAML frontmatter."))
            continue
        if metadata.get("name") != skill_name:
            issues.append(_problem("skill_name_mismatch", str(skill_path), "Frontmatter name must match the Skill directory."))
        description = metadata.get("description")
        if not isinstance(description, str) or not 1 <= len(description) <= 1024:
            issues.append(_problem("invalid_skill_description", str(skill_path), "Skill description must contain 1 to 1024 characters."))

    reference_root = skills_root / "manuscript-workflow-orchestrator/references"
    reference_names = {path.name for path in reference_root.glob("*.md")}
    if reference_names != ORCHESTRATOR_REFERENCES:
        issues.append(_problem("orchestrator_reference_mismatch", str(reference_root), "Orchestrator references are incomplete or unexpected."))

    for schema_name, example_name in SCHEMA_EXAMPLES.items():
        schema_path = root / "schemas" / schema_name
        example_path = root / "assets" / example_name
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            example = json.loads(example_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            errors = list(Draft202012Validator(schema).iter_errors(example))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            issues.append(_problem("invalid_schema_asset", str(schema_path), str(exc)))
            continue
        for error in errors:
            issues.append(_problem("schema_example_mismatch", str(example_path), error.message))

    scan_paths = list((skills_root / "manuscript-workflow-orchestrator").rglob("*.md"))
    scan_paths.extend(path for path in (root / "README.md", root / "CHANGELOG.md") if path.exists())
    placeholder_pattern = re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE)
    for path in scan_paths:
        text = path.read_text(encoding="utf-8")
        if placeholder_pattern.search(text):
            issues.append(_problem("placeholder_in_guidance", str(path), "Guidance contains an unresolved placeholder marker."))
        for pattern in PROHIBITED_WRITING_PATTERNS:
            if pattern.search(text):
                issues.append(_problem("prohibited_sentence_pattern", str(path), f"Matched {pattern.pattern}"))
    return issues


def main() -> int:
    issues = structure_issues()
    if issues:
        print(json.dumps({"passed": False, "issues": issues}, ensure_ascii=False, indent=2))
        return 1
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        return result.returncode
    combined = result.stdout + result.stderr
    match = re.search(r"Ran (\d+) tests?", combined)
    test_count = int(match.group(1)) if match else 0
    print(f"PASS: plugin structure, schemas, workflow gates, and {test_count} tests validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
