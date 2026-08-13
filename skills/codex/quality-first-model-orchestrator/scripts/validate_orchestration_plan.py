#!/usr/bin/env python3
"""Validate an orchestration plan against quality-first invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

RISK_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}


def _depends_on(task_id: str, target: str, by_id: Dict[str, Dict[str, Any]], seen: Optional[Set[str]] = None) -> bool:
    seen = seen or set()
    if task_id in seen:
        return False
    seen.add(task_id)
    task = by_id.get(task_id, {})
    for dep in task.get("dependencies", []):
        if dep == target or _depends_on(str(dep), target, by_id, seen):
            return True
    return False


def validate_plan(plan: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    domain = str(plan.get("domain", "non-code"))
    main = plan.get("main_agent") or {}
    if main.get("mode") != "current-conversation-model":
        errors.append("main_agent.mode must be current-conversation-model")
    if main.get("owns_final_decision") is not True:
        errors.append("The current main agent must own the final decision")
    if main.get("owns_final_artifact") is not True:
        errors.append("The current main agent must own the final artifact")

    contract = plan.get("quality_contract") or {}
    if not str(contract.get("objective", "")).strip():
        errors.append("quality_contract.objective is required")
    if not contract.get("required_deliverables"):
        errors.append("quality_contract.required_deliverables must be non-empty")
    if not contract.get("acceptance_criteria"):
        errors.append("quality_contract.acceptance_criteria must be non-empty")

    models = {str(x.get("model_id")): x for x in registry.get("models", []) if x.get("model_id")}
    tasks = [x for x in plan.get("tasks", []) if isinstance(x, dict)]
    by_id: Dict[str, Dict[str, Any]] = {}
    for task in tasks:
        task_id = str(task.get("id", ""))
        if not task_id:
            errors.append("Every task requires a non-empty id")
            continue
        if task_id in by_id:
            errors.append(f"Duplicate task id: {task_id}")
        by_id[task_id] = task

    for task_id, task in by_id.items():
        risk = str(task.get("risk", ""))
        execution = task.get("execution")
        if risk not in RISK_ORDER:
            errors.append(f"Task {task_id}: risk must be one of L0, L1, L2, L3")
            continue
        if execution not in {"main", "subagent"}:
            errors.append(f"Task {task_id}: execution must be main or subagent")
        if not str(task.get("objective", "")).strip():
            errors.append(f"Task {task_id}: objective is required")
        if not task.get("acceptance_criteria"):
            errors.append(f"Task {task_id}: acceptance_criteria must be non-empty")
        verification = task.get("verification") or {}
        if not verification.get("methods"):
            errors.append(f"Task {task_id}: verification.methods must be non-empty")
        if not verification.get("owner"):
            errors.append(f"Task {task_id}: verification.owner is required")
        if not task.get("output_schema"):
            errors.append(f"Task {task_id}: output_schema is required")
        for dep in task.get("dependencies", []):
            if dep not in by_id:
                errors.append(f"Task {task_id}: unknown dependency {dep}")

        escalation = task.get("escalation") or {}
        escalation_text = json.dumps(escalation, ensure_ascii=False).lower()
        if "downgrade" in escalation_text:
            errors.append(f"Task {task_id}: failure handling may not downgrade model capability")
        if execution == "subagent":
            if risk == "L3":
                errors.append(f"Task {task_id}: L3 work cannot be delegated to a subagent")
            if task.get("critical_output") is True:
                errors.append(f"Task {task_id}: critical_output cannot be delegated")
            model_id = task.get("assigned_model")
            if not model_id:
                errors.append(f"Task {task_id}: delegated work requires assigned_model")
                continue
            model = models.get(str(model_id))
            if not model:
                errors.append(f"Task {task_id}: assigned model {model_id} is not in the discovered registry")
                continue
            if not model.get("available", False):
                errors.append(f"Task {task_id}: assigned model {model_id} is unavailable")
            if model.get("status") == "probation" and risk != "L0":
                errors.append(f"Task {task_id}: probation model {model_id} may receive only L0 work")
            field = "max_risk_code" if domain == "code" else "max_risk_non_code"
            if domain == "mixed":
                ceiling = min(
                    RISK_ORDER.get(model.get("max_risk_code"), 0),
                    RISK_ORDER.get(model.get("max_risk_non_code"), 0),
                )
            else:
                ceiling = RISK_ORDER.get(model.get(field), 0)
            if RISK_ORDER[risk] > ceiling:
                errors.append(
                    f"Task {task_id}: risk {risk} exceeds {model_id} quality ceiling for domain {domain}"
                )
            effort = task.get("reasoning_effort")
            supported = model.get("supported_reasoning_efforts", [])
            if effort and supported and effort not in supported:
                errors.append(f"Task {task_id}: effort {effort} is unsupported by {model_id}")
            if risk == "L2":
                strong_efforts = {"high", "xhigh", "max", "ultra"}
                if supported and not set(str(x) for x in supported).intersection(strong_efforts):
                    errors.append(f"Task {task_id}: model {model_id} exposes no strong reasoning effort for L2 work")
                if effort and effort not in strong_efforts:
                    errors.append(f"Task {task_id}: reasoning effort {effort} is below the L2 quality floor")
                marker = " ".join(str(x).lower() for x in verification.get("methods", []))
                if not any(x in marker for x in ("independent", "dual", "counter", "source-recheck")):
                    errors.append(f"Task {task_id}: L2 work requires an independent or countercheck verification method")
        elif execution == "main" and task.get("assigned_model"):
            warnings.append(f"Task {task_id}: assigned_model is ignored because execution is main")

    # Parallel tasks cannot write the same path. A dependency establishes sequencing.
    ids = list(by_id)
    for i, left_id in enumerate(ids):
        left_writes = set(str(x) for x in by_id[left_id].get("writes", []))
        if not left_writes:
            continue
        for right_id in ids[i + 1 :]:
            overlap = left_writes.intersection(str(x) for x in by_id[right_id].get("writes", []))
            if not overlap:
                continue
            ordered = _depends_on(left_id, right_id, by_id) or _depends_on(right_id, left_id, by_id)
            if not ordered:
                errors.append(
                    f"Parallel write conflict: tasks {left_id} and {right_id} both write {sorted(overlap)}"
                )

    gate = plan.get("final_quality_gate") or {}
    if gate.get("owner") != "main":
        errors.append("final_quality_gate.owner must be main")
    required_checks = {"completeness", "factuality", "consistency", "user-requirements"}
    checks = set(str(x) for x in gate.get("checks", []))
    missing_checks = sorted(required_checks - checks)
    if missing_checks:
        errors.append(f"final_quality_gate is missing checks: {missing_checks}")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _load(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--output", default="-")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        report = validate_plan(_load(args.plan), _load(args.registry))
    except Exception as exc:
        print(f"Plan validation failed: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        sys.stdout.write(text)
    else:
        path = Path(args.output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
