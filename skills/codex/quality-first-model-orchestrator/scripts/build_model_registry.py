#!/usr/bin/env python3
"""Build a conservative, quality-gated capability registry from a model catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

RISK_ORDER = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
RISK_NAME = {value: key for key, value in RISK_ORDER.items()}


def _profile(model_id: str) -> Dict[str, Any]:
    mid = model_id.lower()
    base = {
        "status": "active",
        "tier": "unknown",
        "efficiency_rank": 5,
        "max_risk_code": "L0",
        "max_risk_non_code": "L0",
        "traits": ["structured-output"],
        "allowed_categories": ["extraction", "formatting"],
        "restrictions": ["probation-only", "no-critical-output"],
        "role_suitability": ["bounded-extractor", "formatter"],
    }

    if "spark" in mid:
        base.update(
            tier="fast-specialist",
            efficiency_rank=0,
            max_risk_code="L1",
            max_risk_non_code="L1",
            traits=[
                "structured-output",
                "source-traceability",
                "fast-iteration",
                "bounded-execution",
                "targeted-code-editing",
            ],
            allowed_categories=[
                "exploration",
                "extraction",
                "classification",
                "formatting",
                "transformation",
                "targeted-coding",
                "targeted-testing",
            ],
            restrictions=["no-L2-synthesis", "no-critical-output", "text-only-unless-catalog-says-otherwise"],
            role_suitability=["explorer", "evidence-extractor", "formatter", "targeted-worker", "test-runner"],
        )
        return base

    if "nano" in mid:
        base.update(
            tier="micro",
            efficiency_rank=0,
            traits=["structured-output", "high-volume"],
            allowed_categories=["extraction", "formatting", "classification"],
            restrictions=["L0-only", "no-open-ended-reasoning", "no-critical-output"],
            role_suitability=["formatter", "classifier", "field-extractor"],
        )
        return base

    if "mini" in mid or "luna" in mid:
        base.update(
            tier="efficient",
            efficiency_rank=1,
            max_risk_code="L1",
            max_risk_non_code="L1",
            traits=[
                "structured-output",
                "source-traceability",
                "large-volume-processing",
                "bounded-analysis",
            ],
            allowed_categories=[
                "exploration",
                "extraction",
                "classification",
                "formatting",
                "transformation",
                "summarization",
                "targeted-coding",
                "targeted-testing",
            ],
            restrictions=["no-L2-final-synthesis", "no-critical-output"],
            role_suitability=["explorer", "extractor", "classifier", "summarizer", "targeted-worker"],
        )
        return base

    if "terra" in mid:
        base.update(
            tier="balanced",
            efficiency_rank=2,
            max_risk_code="L2",
            max_risk_non_code="L2",
            traits=[
                "structured-output",
                "source-traceability",
                "cross-source-synthesis",
                "complex-reasoning",
                "review",
                "tool-use",
            ],
            allowed_categories=[
                "exploration",
                "extraction",
                "classification",
                "formatting",
                "transformation",
                "summarization",
                "analysis",
                "synthesis",
                "review",
                "coding",
                "testing",
            ],
            restrictions=["no-critical-output", "L2-requires-independent-review"],
            role_suitability=["analyst", "reviewer", "researcher", "implementation-worker"],
        )
        return base

    if re.search(r"gpt-5\.4(?:$|[-_])", mid) and "mini" not in mid and "nano" not in mid:
        base.update(
            tier="balanced",
            efficiency_rank=2,
            max_risk_code="L2",
            max_risk_non_code="L2",
            traits=[
                "structured-output",
                "source-traceability",
                "cross-source-synthesis",
                "complex-reasoning",
                "review",
                "tool-use",
            ],
            allowed_categories=[
                "exploration",
                "extraction",
                "classification",
                "formatting",
                "transformation",
                "summarization",
                "analysis",
                "synthesis",
                "review",
                "coding",
                "testing",
            ],
            restrictions=["no-critical-output", "L2-requires-independent-review"],
            role_suitability=["analyst", "reviewer", "researcher", "implementation-worker"],
        )
        return base

    if re.search(r"gpt-5\.5(?:$|[-_])", mid):
        base.update(
            tier="strong",
            efficiency_rank=3,
            max_risk_code="L2",
            max_risk_non_code="L2",
            traits=[
                "structured-output",
                "source-traceability",
                "cross-source-synthesis",
                "complex-reasoning",
                "review",
                "tool-use",
                "long-horizon-work",
            ],
            allowed_categories=[
                "exploration",
                "extraction",
                "classification",
                "formatting",
                "transformation",
                "summarization",
                "analysis",
                "synthesis",
                "review",
                "coding",
                "testing",
            ],
            restrictions=["no-critical-output", "L2-requires-independent-review"],
            role_suitability=["senior-analyst", "reviewer", "researcher", "implementation-worker"],
        )
        return base

    if "codex" in mid and re.search(r"gpt-5\.3", mid):
        base.update(
            tier="coding-specialist",
            efficiency_rank=3,
            max_risk_code="L2",
            max_risk_non_code="L1",
            traits=[
                "structured-output",
                "source-traceability",
                "agentic-coding",
                "complex-reasoning",
                "tool-use",
                "review",
            ],
            allowed_categories=[
                "exploration",
                "extraction",
                "analysis",
                "review",
                "coding",
                "testing",
                "targeted-coding",
                "targeted-testing",
            ],
            restrictions=["non-code-L1-ceiling", "no-critical-output"],
            role_suitability=["code-analyst", "implementation-worker", "code-reviewer", "test-worker"],
        )
        return base

    if "gpt-5.6" in mid or "sol" in mid or "pro" in mid:
        base.update(
            tier="frontier",
            efficiency_rank=4,
            max_risk_code="L2",
            max_risk_non_code="L2",
            traits=[
                "structured-output",
                "source-traceability",
                "cross-source-synthesis",
                "complex-reasoning",
                "review",
                "tool-use",
                "long-horizon-work",
                "ambiguous-planning",
            ],
            allowed_categories=[
                "exploration",
                "extraction",
                "classification",
                "formatting",
                "transformation",
                "summarization",
                "analysis",
                "synthesis",
                "review",
                "coding",
                "testing",
            ],
            restrictions=["no-critical-output-when-subagent", "L2-requires-independent-review"],
            role_suitability=["senior-analyst", "adversarial-reviewer", "complex-worker", "researcher"],
        )
        return base

    base["status"] = "probation"
    return base


def _history_records(history: Any) -> List[Dict[str, Any]]:
    if isinstance(history, list):
        return [x for x in history if isinstance(x, dict)]
    if isinstance(history, dict) and isinstance(history.get("records"), list):
        return [x for x in history["records"] if isinstance(x, dict)]
    return []


def _history_summary(records: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        model = record.get("model_id")
        category = record.get("category", "unknown")
        if model:
            grouped[(str(model), str(category))].append(record)
    result: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for key, items in grouped.items():
        attempts = len(items)
        passes = sum(1 for item in items if bool(item.get("passed")))
        repairs = sum(int(item.get("repair_count", 0) or 0) for item in items)
        result[key] = {
            "attempts": attempts,
            "passes": passes,
            "pass_rate": passes / attempts if attempts else None,
            "repairs": repairs,
        }
    return result


def build_registry(catalog: Dict[str, Any], history: Any = None) -> Dict[str, Any]:
    records = _history_records(history or [])
    summary = _history_summary(records)
    registry_models: List[Dict[str, Any]] = []
    for model in catalog.get("models", []):
        if not isinstance(model, dict) or not model.get("id"):
            continue
        profile = _profile(str(model["id"]))
        model_history = {
            category: value
            for (model_id, category), value in summary.items()
            if model_id == str(model["id"])
        }
        total_attempts = sum(x["attempts"] for x in model_history.values())
        total_passes = sum(x["passes"] for x in model_history.values())
        overall_rate = total_passes / total_attempts if total_attempts else None

        # Empirical history may demote a model. Automatic promotion is intentionally forbidden.
        if total_attempts >= 5 and overall_rate is not None and overall_rate < 0.8:
            for field in ("max_risk_code", "max_risk_non_code"):
                current = RISK_ORDER[profile[field]]
                profile[field] = RISK_NAME[max(0, current - 1)]
            profile["restrictions"] = list(profile["restrictions"]) + ["demoted-by-local-history"]

        registry_models.append(
            {
                "model_id": str(model["id"]),
                "display_name": model.get("display_name") or model["id"],
                "catalog_model": model.get("model") or model["id"],
                "available": True,
                "hidden": bool(model.get("hidden", False)),
                "status": profile["status"],
                "tier": profile["tier"],
                "efficiency_rank": profile["efficiency_rank"],
                "max_risk_code": profile["max_risk_code"],
                "max_risk_non_code": profile["max_risk_non_code"],
                "traits": profile["traits"],
                "allowed_categories": profile["allowed_categories"],
                "restrictions": profile["restrictions"],
                "role_suitability": profile["role_suitability"],
                "supported_reasoning_efforts": model.get("supported_reasoning_efforts", []),
                "default_reasoning_effort": model.get("default_reasoning_effort"),
                "input_modalities": model.get("input_modalities", ["text", "image"]),
                "is_default": bool(model.get("is_default", False)),
                "upgrade": model.get("upgrade"),
                "history": {
                    "overall_attempts": total_attempts,
                    "overall_pass_rate": overall_rate,
                    "by_category": model_history,
                    "can_auto_promote": False,
                },
            }
        )
    return {
        "schema_version": 1,
        "catalog_source": catalog.get("source", "unknown"),
        "quality_policy": {
            "quality_is_hard_constraint": True,
            "unknown_models_are_probationary": True,
            "history_can_demote": True,
            "history_can_auto_promote": False,
            "L3_owner": "current-conversation-model",
        },
        "models": registry_models,
    }


def _load(path: str) -> Any:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--history")
    parser.add_argument("--output", default="-")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        registry = build_registry(_load(args.catalog), _load(args.history) if args.history else [])
    except Exception as exc:
        print(f"Registry build failed: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        sys.stdout.write(text)
    else:
        path = Path(args.output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
