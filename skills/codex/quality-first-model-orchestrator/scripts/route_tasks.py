#!/usr/bin/env python3
"""Propose conservative subagent model assignments for a task manifest."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

RISK_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
EFFORT_ORDER = ["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"]


def _max_risk(model: Dict[str, Any], domain: str) -> int:
    if domain == "code":
        return RISK_ORDER.get(model.get("max_risk_code"), 0)
    if domain == "mixed":
        return min(
            RISK_ORDER.get(model.get("max_risk_code"), 0),
            RISK_ORDER.get(model.get("max_risk_non_code"), 0),
        )
    return RISK_ORDER.get(model.get("max_risk_non_code"), 0)


def _choose_effort(model: Dict[str, Any], risk: str) -> Optional[str]:
    supported = [str(x) for x in model.get("supported_reasoning_efforts", [])]
    default = model.get("default_reasoning_effort")
    target = {"L0": "low", "L1": "medium", "L2": "high"}.get(risk, "high")
    if target in supported:
        return target
    if supported:
        indexed = sorted(supported, key=lambda x: EFFORT_ORDER.index(x) if x in EFFORT_ORDER else -1)
        desired_idx = EFFORT_ORDER.index(target)
        at_or_above = [x for x in indexed if x in EFFORT_ORDER and EFFORT_ORDER.index(x) >= desired_idx]
        if at_or_above:
            return at_or_above[0]
        return indexed[-1]
    return str(default) if default else None


def _verification(risk: str) -> str:
    return {
        "L0": "deterministic-check",
        "L1": "main-sample-review",
        "L2": "independent-review",
        "L3": "main-final-gate",
    }[risk]


def _prompt_profile(model: Dict[str, Any], risk: str) -> str:
    tier = model.get("tier")
    if tier in {"micro", "fast-specialist", "efficient"}:
        return "narrow-stepwise-evidence-bound"
    if risk == "L2":
        return "structured-analysis-with-countercheck"
    return "bounded-role-contract"


def _qualified(
    model: Dict[str, Any],
    task: Dict[str, Any],
    domain: str,
) -> bool:
    risk = str(task.get("risk"))
    if risk not in RISK_ORDER:
        return False
    if not model.get("available", False):
        return False
    if model.get("status") == "probation" and risk != "L0":
        return False
    if _max_risk(model, domain) < RISK_ORDER[risk]:
        return False
    if risk == "L2":
        supported = set(str(x) for x in model.get("supported_reasoning_efforts", []))
        strong_efforts = {"high", "xhigh", "max", "ultra"}
        if supported and not supported.intersection(strong_efforts):
            return False
    category = str(task.get("category", ""))
    if category and category not in model.get("allowed_categories", []):
        return False
    modalities = set(task.get("required_modalities", ["text"]))
    if not modalities.issubset(set(model.get("input_modalities", ["text", "image"]))):
        return False
    traits = set(task.get("required_traits", []))
    if not traits.issubset(set(model.get("traits", []))):
        return False
    if model.get("model_id") in set(task.get("forbidden_models", [])):
        return False
    return True


def route_manifest(manifest: Dict[str, Any], registry: Dict[str, Any]) -> Dict[str, Any]:
    domain = str(manifest.get("domain", "non-code"))
    main_model_id = manifest.get("main_model_id")
    usage: Counter[str] = Counter()
    assignments: List[Dict[str, Any]] = []
    models = [x for x in registry.get("models", []) if isinstance(x, dict)]

    for task in manifest.get("tasks", []):
        task_id = str(task.get("id", "unnamed"))
        risk = str(task.get("risk", "L3"))
        critical = bool(task.get("critical_output", False))
        allow = bool(task.get("allow_delegation", True))
        if not allow or critical or risk == "L3":
            assignments.append(
                {
                    "task_id": task_id,
                    "execution": "main",
                    "model_id": None,
                    "reasoning_effort": None,
                    "verification_level": _verification("L3" if risk == "L3" else risk),
                    "prompt_profile": "main-agent-full-context",
                    "reason": "Critical, L3, or explicitly non-delegable work remains with the current main agent.",
                }
            )
            continue

        candidates = [model for model in models if _qualified(model, task, domain)]
        non_main = [model for model in candidates if model.get("model_id") != main_model_id]
        if non_main:
            candidates = non_main
        if not candidates:
            assignments.append(
                {
                    "task_id": task_id,
                    "execution": "main",
                    "model_id": None,
                    "reasoning_effort": None,
                    "verification_level": _verification(risk),
                    "prompt_profile": "main-agent-full-context",
                    "reason": "No discovered subagent model meets every quality, risk, modality, category, and trait requirement.",
                }
            )
            continue

        # Every remaining model passed the hard quality gate. Soft preferences now
        # favor current-plan diversity and efficiency.
        candidates.sort(
            key=lambda model: (
                usage[str(model.get("model_id"))],
                int(model.get("efficiency_rank", 99)),
                -_max_risk(model, domain),
                str(model.get("model_id")),
            )
        )
        chosen = candidates[0]
        chosen_id = str(chosen["model_id"])
        usage[chosen_id] += 1
        assignments.append(
            {
                "task_id": task_id,
                "execution": "subagent",
                "model_id": chosen_id,
                "reasoning_effort": _choose_effort(chosen, risk),
                "verification_level": _verification(risk),
                "prompt_profile": _prompt_profile(chosen, risk),
                "reason": "Model passed all hard quality gates; diversity and efficiency were used only as tie-breakers.",
                "candidate_models": [str(x["model_id"]) for x in candidates],
            }
        )

    return {
        "schema_version": 1,
        "main_agent": "current-conversation-model",
        "domain": domain,
        "assignments": assignments,
        "policy": {
            "quality_first": True,
            "diversify_only_after_quality_gate": True,
            "automatic_downgrade_after_failure": False,
        },
    }


def _load(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--output", default="-")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = route_manifest(_load(args.manifest), _load(args.registry))
    except Exception as exc:
        print(f"Task routing failed: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        sys.stdout.write(text)
    else:
        path = Path(args.output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
