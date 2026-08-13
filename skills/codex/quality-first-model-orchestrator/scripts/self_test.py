#!/usr/bin/env python3
"""Run deterministic smoke tests; optionally test live Codex model discovery."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import build_model_registry
import discover_models
import quick_validate
import route_tasks
import validate_orchestration_plan


def fixture_catalog():
    return {
        "data": [
            {
                "id": "gpt-5.6-sol",
                "model": "gpt-5.6-sol",
                "displayName": "GPT-5.6 Sol",
                "defaultReasoningEffort": "medium",
                "supportedReasoningEfforts": [
                    {"reasoningEffort": "medium"},
                    {"reasoningEffort": "high"},
                ],
                "inputModalities": ["text", "image"],
            },
            {
                "id": "gpt-5.5",
                "model": "gpt-5.5",
                "displayName": "GPT-5.5",
                "defaultReasoningEffort": "medium",
                "supportedReasoningEfforts": [
                    {"reasoningEffort": "medium"},
                    {"reasoningEffort": "high"},
                ],
                "inputModalities": ["text", "image"],
            },
            {
                "id": "gpt-5.3-codex-spark",
                "model": "gpt-5.3-codex-spark",
                "displayName": "GPT-5.3-Codex-Spark",
                "defaultReasoningEffort": "medium",
                "supportedReasoningEfforts": [
                    {"reasoningEffort": "low"},
                    {"reasoningEffort": "medium"},
                ],
                "inputModalities": ["text"],
            },
            {
                "id": "unknown-next-model",
                "model": "unknown-next-model",
                "displayName": "Unknown Next Model",
                "defaultReasoningEffort": "medium",
                "supportedReasoningEfforts": [{"reasoningEffort": "medium"}],
                "inputModalities": ["text"],
            },
        ]
    }


def run_smoke():
    root = Path(__file__).resolve().parents[1]
    structural = quick_validate.validate(root)
    assert not structural, structural

    catalog = discover_models.normalize_catalog(fixture_catalog(), source="self-test")
    registry = build_model_registry.build_registry(catalog, history=[])
    by_id = {x["model_id"]: x for x in registry["models"]}
    assert by_id["gpt-5.3-codex-spark"]["max_risk_non_code"] == "L1"
    assert by_id["unknown-next-model"]["status"] == "probation"

    manifest = {
        "version": 1,
        "domain": "non-code",
        "main_model_id": "gpt-5.6-sol",
        "tasks": [
            {
                "id": "extract",
                "role": "evidence-extractor",
                "category": "extraction",
                "risk": "L1",
                "allow_delegation": True,
                "critical_output": False,
                "required_modalities": ["text"],
                "required_traits": ["structured-output", "source-traceability"],
            },
            {
                "id": "final",
                "role": "final-decider",
                "category": "final-decision",
                "risk": "L3",
                "allow_delegation": True,
                "critical_output": True,
                "required_modalities": ["text"],
                "required_traits": [],
            },
        ],
    }
    proposal = route_tasks.route_manifest(manifest, registry)
    assignments = {x["task_id"]: x for x in proposal["assignments"]}
    assert assignments["extract"]["execution"] == "subagent"
    assert assignments["final"]["execution"] == "main"

    plan = {
        "version": 1,
        "domain": "non-code",
        "main_agent": {
            "mode": "current-conversation-model",
            "owns_final_decision": True,
            "owns_final_artifact": True,
        },
        "quality_contract": {
            "objective": "Produce a verified result.",
            "required_deliverables": ["result"],
            "acceptance_criteria": ["Every material claim is verified."],
        },
        "tasks": [
            {
                "id": "extract",
                "role": "evidence-extractor",
                "category": "extraction",
                "risk": "L1",
                "execution": "subagent",
                "assigned_model": assignments["extract"]["model_id"],
                "reasoning_effort": assignments["extract"]["reasoning_effort"],
                "objective": "Extract verified evidence.",
                "inputs": ["source"],
                "output_schema": "evidence-record-v1",
                "acceptance_criteria": ["Every item has a source location."],
                "verification": {"methods": ["source-recheck"], "owner": "main"},
                "writes": [],
                "dependencies": [],
                "escalation": {"on_failure": "retry-once-then-upgrade", "fallback": "main"},
            },
            {
                "id": "final",
                "role": "integrator",
                "category": "final-decision",
                "risk": "L3",
                "execution": "main",
                "assigned_model": None,
                "reasoning_effort": None,
                "objective": "Integrate the final result.",
                "inputs": ["extract"],
                "output_schema": "final-artifact",
                "acceptance_criteria": ["Quality contract passes."],
                "verification": {"methods": ["final-quality-gate"], "owner": "main"},
                "writes": ["final-artifact"],
                "dependencies": ["extract"],
                "escalation": {"on_failure": "main-rework", "fallback": "main"},
            },
        ],
        "final_quality_gate": {
            "owner": "main",
            "checks": ["completeness", "factuality", "consistency", "user-requirements"],
        },
    }
    report = validate_orchestration_plan.validate_plan(plan, registry)
    assert report["valid"], report
    return {"models": len(registry["models"]), "proposal": proposal, "validation": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Also query the installed Codex App Server")
    parser.add_argument("--codex-bin", default="codex")
    args = parser.parse_args()
    result = run_smoke()
    if args.live:
        raw = discover_models.query_app_server(codex_bin=args.codex_bin)
        live = discover_models.normalize_catalog(raw, source="live-self-test")
        assert live["models"], "Live model catalog is empty"
        result["live_models"] = [x["id"] for x in live["models"]]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
