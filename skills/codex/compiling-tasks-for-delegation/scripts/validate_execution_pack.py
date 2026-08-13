#!/usr/bin/env python3
"""Validate execution packages produced by compiling-tasks-for-delegation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID_DELEGATION = {
    "SAFE_TO_DELEGATE",
    "CONDITIONAL",
    "HIGH_MODEL_REQUIRED",
}

SPARK_EXECUTOR = "GPT-5.3-Codex-Spark"
SPARK_MAX_STEPS = 6
SPARK_MAX_PRIMARY_FILES = 3
SPARK_MAX_CHUNK_CHARS = 24_000

PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b", re.IGNORECASE)
STEP_RE = re.compile(r"(?m)^###\s+STEP\s+\d+\b.*$")
DELEGATION_RE = re.compile(r"(?m)^Delegation:\s*([A-Z_]+)\s*$")
BULLET_RE = re.compile(r"(?m)^\s*[-*]\s+\S.*$")

SINGLE_REQUIRED_SECTIONS = [
    "## Task Goal",
    "## Constraints",
    "## Environment",
    "## Steps",
    "## Acceptance Criteria",
    "## Final Report",
]

MULTI_REQUIRED_FILES = [
    "TASK.md",
    "CONTEXT.md",
    "STEPS.md",
    "ACCEPTANCE.md",
    "EXECUTION_REPORT.md",
]

MULTI_REQUIRED_SECTIONS = {
    "TASK.md": ["## Goal", "## Deliverables", "## Constraints", "## Delegation Summary"],
    "CONTEXT.md": ["## Known Facts", "## Environment", "## Assumptions", "## Boundaries"],
    "ACCEPTANCE.md": ["## Acceptance Criteria", "## Validation Procedure", "## Failure Conditions"],
    "EXECUTION_REPORT.md": [
        "## Status",
        "## Completed Steps",
        "## Evidence",
        "## Deviations",
        "## Stop Codes",
        "## Deliverables",
        "## Unresolved Issues",
    ],
}

SPARK_REQUIRED_FILES = [
    "TASK.md",
    "CONTEXT.md",
    "SPARK_MASTER_INDEX.md",
    "ACCEPTANCE.md",
    "EXECUTION_REPORT.md",
]

SPARK_REQUIRED_SECTIONS = {
    "TASK.md": [
        "## Goal",
        "## Deliverables",
        "## Constraints",
        "## Delegation Summary",
        "## Target Executor",
    ],
    "CONTEXT.md": ["## Known Facts", "## Environment", "## Assumptions", "## Boundaries"],
    "SPARK_MASTER_INDEX.md": ["## Target Executor", "## Execution Rule", "## Chunk Status"],
    "ACCEPTANCE.md": ["## Acceptance Criteria", "## Validation Procedure", "## Failure Conditions"],
    "EXECUTION_REPORT.md": [
        "## Status",
        "## Completed Steps",
        "## Evidence",
        "## Deviations",
        "## Stop Codes",
        "## Deliverables",
        "## Unresolved Issues",
    ],
}

SPARK_CHUNK_REQUIRED_SECTIONS = [
    "## Target Executor",
    "## Chunk Goal",
    "## Why This Chunk Exists",
    "## Required Context",
    "## Context Budget",
    "## Preconditions",
    "## Allowed Scope",
    "## Forbidden Actions",
    "## Files / Resources",
    "## Exact Steps",
    "## Mandatory Verification",
    "## Expected Result",
    "## Evidence to Record",
    "## Failure Branches",
    "## Completion Report",
    "## Next-Chunk Gate",
]

STEP_REQUIRED_FIELDS = [
    "#### Purpose",
    "#### Input",
    "#### Action",
    "#### Expected Result",
    "#### Evidence",
    "#### Verdict",
    "#### Exception Handling",
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def placeholder_errors(label: str, text: str) -> list[str]:
    errors: list[str] = []
    for match in PLACEHOLDER_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        errors.append(f"{label}:{line}: placeholder token '{match.group(0)}' is not allowed")
    return errors


def required_section_errors(label: str, text: str, sections: list[str]) -> list[str]:
    return [f"{label}: missing required section '{section}'" for section in sections if section not in text]


def section_body(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    match = re.search(r"(?m)^##\s+", text[start:])
    end = start + match.start() if match else len(text)
    return text[start:end].strip()


def split_steps(text: str) -> list[tuple[str, str]]:
    matches = list(STEP_RE.finditer(text))
    steps: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        steps.append((match.group(0).strip(), text[start:end]))
    return steps


def validate_steps(label: str, text: str, *, max_steps: int | None = None) -> list[str]:
    errors: list[str] = []
    steps = split_steps(text)
    if not steps:
        return [f"{label}: no '### STEP NN' blocks found"]
    if max_steps is not None and len(steps) > max_steps:
        errors.append(f"{label}: Spark chunk has {len(steps)} steps; maximum is {max_steps} (six)")

    for title, block in steps:
        d = DELEGATION_RE.search(block)
        if not d:
            errors.append(f"{label}: {title}: missing Delegation state")
        elif d.group(1) not in VALID_DELEGATION:
            errors.append(
                f"{label}: {title}: invalid Delegation state '{d.group(1)}'; "
                f"expected one of {sorted(VALID_DELEGATION)}"
            )
        for field in STEP_REQUIRED_FIELDS:
            if field not in block:
                errors.append(f"{label}: {title}: missing step field '{field}'")
    return errors


def validate_single(path: Path) -> list[str]:
    text = read_text(path)
    errors = []
    errors.extend(placeholder_errors(path.name, text))
    errors.extend(required_section_errors(path.name, text, SINGLE_REQUIRED_SECTIONS))
    if "## Steps" in text:
        errors.extend(validate_steps(path.name, text))
    return errors


def validate_multi(root: Path) -> list[str]:
    errors: list[str] = []
    for name in MULTI_REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f"{root}: missing required file '{name}'")

    if errors:
        return errors

    for name, sections in MULTI_REQUIRED_SECTIONS.items():
        text = read_text(root / name)
        errors.extend(placeholder_errors(name, text))
        errors.extend(required_section_errors(name, text, sections))

    steps_text = read_text(root / "STEPS.md")
    errors.extend(placeholder_errors("STEPS.md", steps_text))
    errors.extend(validate_steps("STEPS.md", steps_text))
    return errors


def validate_spark_chunk(path: Path) -> list[str]:
    label = str(path.relative_to(path.parents[1]))
    text = read_text(path)
    errors: list[str] = []
    errors.extend(placeholder_errors(label, text))
    errors.extend(required_section_errors(label, text, SPARK_CHUNK_REQUIRED_SECTIONS))

    if SPARK_EXECUTOR not in section_body(text, "## Target Executor"):
        errors.append(f"{label}: target executor must be exactly '{SPARK_EXECUTOR}'")

    if len(text) > SPARK_MAX_CHUNK_CHARS:
        errors.append(
            f"{label}: chunk instruction file is {len(text)} characters; "
            f"maximum is {SPARK_MAX_CHUNK_CHARS} to preserve Spark context headroom"
        )

    files_body = section_body(text, "## Files / Resources")
    primary_files = BULLET_RE.findall(files_body)
    if len(primary_files) > SPARK_MAX_PRIMARY_FILES:
        errors.append(
            f"{label}: lists {len(primary_files)} primary files/resources; "
            f"maximum is {SPARK_MAX_PRIMARY_FILES} for a Spark chunk"
        )

    verification = section_body(text, "## Mandatory Verification")
    if not verification:
        errors.append(f"{label}: Mandatory Verification must contain an explicit verification action")

    gate = section_body(text, "## Next-Chunk Gate")
    if "USER_APPROVAL_REQUIRED" not in gate:
        errors.append(f"{label}: Next-Chunk Gate must include USER_APPROVAL_REQUIRED")
    if "AUTO_CONTINUE_FORBIDDEN" not in gate:
        errors.append(f"{label}: Next-Chunk Gate must include AUTO_CONTINUE_FORBIDDEN")

    if "## Exact Steps" in text:
        errors.extend(validate_steps(label, section_body(text, "## Exact Steps"), max_steps=SPARK_MAX_STEPS))
    return errors


def validate_spark(root: Path) -> list[str]:
    errors: list[str] = []
    for name in SPARK_REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f"{root}: missing required Spark file '{name}'")

    chunks_dir = root / "chunks"
    if not chunks_dir.is_dir():
        errors.append(f"{root}: missing required Spark directory 'chunks/'")

    if errors:
        return errors

    for name, sections in SPARK_REQUIRED_SECTIONS.items():
        text = read_text(root / name)
        errors.extend(placeholder_errors(name, text))
        errors.extend(required_section_errors(name, text, sections))

    task_text = read_text(root / "TASK.md")
    if SPARK_EXECUTOR not in section_body(task_text, "## Target Executor"):
        errors.append(f"TASK.md: target executor must be exactly '{SPARK_EXECUTOR}'")

    index_text = read_text(root / "SPARK_MASTER_INDEX.md")
    if SPARK_EXECUTOR not in section_body(index_text, "## Target Executor"):
        errors.append(f"SPARK_MASTER_INDEX.md: target executor must be exactly '{SPARK_EXECUTOR}'")

    chunk_files = sorted(chunks_dir.glob("CHUNK-*.md"))
    if not chunk_files:
        errors.append(f"{root}: Spark package requires at least one chunks/CHUNK-NNN.md file")
        return errors

    expected_names = [f"CHUNK-{i:03d}.md" for i in range(1, len(chunk_files) + 1)]
    actual_names = [p.name for p in chunk_files]
    if actual_names != expected_names:
        errors.append(
            f"{root}: Spark chunks must be contiguous from CHUNK-001.md; found {', '.join(actual_names)}"
        )

    for chunk in chunk_files:
        errors.extend(validate_spark_chunk(chunk))
    return errors


def validate_path(path: str | Path) -> list[str]:
    root = Path(path).resolve()
    if root.is_file():
        if root.name != "EXECUTION_PLAN.md":
            return [f"{root}: single-file validation requires EXECUTION_PLAN.md"]
        return validate_single(root)

    if not root.exists():
        return [f"{root}: path does not exist"]
    if not root.is_dir():
        return [f"{root}: path is not a directory"]

    single = root / "EXECUTION_PLAN.md"
    if single.is_file():
        return validate_single(single)

    if (root / "SPARK_MASTER_INDEX.md").exists() or (root / "chunks").exists():
        return validate_spark(root)

    if any((root / name).exists() for name in MULTI_REQUIRED_FILES):
        return validate_multi(root)

    return [
        f"{root}: no execution package found; expected EXECUTION_PLAN.md, a Spark package, "
        f"or {', '.join(MULTI_REQUIRED_FILES)}"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to EXECUTION_PLAN.md or an execution-package directory")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    errors = validate_path(args.path)
    payload = {"valid": not errors, "errors": errors}
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
    else:
        print("VALID")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
