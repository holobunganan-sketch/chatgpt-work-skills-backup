#!/usr/bin/env python3
"""验证修订台账的闭环完整性，并核对可选的交付文件路径。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DECISIONS = {"accept", "partial", "decline", "clarify", "defer"}
STATUSES = {"resolved", "deferred", "open"}
ACTION_WORDS = re.compile(
    r"\b(revis(?:e|ed|ion)|modif(?:y|ied|ication)|add(?:ed|ition)?|remove[ds]?|"
    r"update[ds]?|clarif(?:y|ied|ication))\b|已修改|已补充|已删除|已更新|已澄清",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证要求—决策—修改—回应的可追溯台账")
    parser.add_argument("ledger", type=Path, help="台账 JSON")
    parser.add_argument("--delivery-root", type=Path, help="用于核对 artifact 路径的交付目录")
    parser.add_argument("--policy", type=Path, help="审计策略 JSON")
    parser.add_argument("--json-out", type=Path, help="审计报告输出路径")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def finding(
    findings: list[dict[str, Any]], item_id: str, severity: str,
    rule_id: str, message: str, evidence: str = "",
) -> None:
    findings.append({
        "item_id": item_id,
        "severity": severity,
        "rule_id": rule_id,
        "message": message,
        "evidence": evidence[:500],
        "status": "open",
    })


def safe_artifact_path(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def main() -> int:
    args = parse_args()
    try:
        ledger = load_json(args.ledger)
        policy = load_json(args.policy) if args.policy else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"错误：无法读取 JSON：{exc}", file=sys.stderr)
        return 3

    if not isinstance(ledger, dict):
        print("错误：台账顶层必须是 JSON 对象", file=sys.stderr)
        return 3

    findings: list[dict[str, Any]] = []
    protocol = str(ledger.get("protocol", ""))
    if not protocol.startswith("formal-revision-traceability/1."):
        finding(findings, "GLOBAL", "major", "LEDGER-PROTOCOL", "协议缺失或主版本不兼容", protocol)

    items = ledger.get("items")
    if not isinstance(items, list):
        finding(findings, "GLOBAL", "critical", "LEDGER-ITEMS", "items 必须是数组")
        items = []

    release_candidate = bool(policy.get("release_candidate", True))
    require_source = bool(policy.get("require_source_text", True))
    require_response = bool(policy.get("require_response", True))
    allow_deferred = bool(policy.get("allow_deferred_items", False))
    require_paths = bool(policy.get("require_existing_artifact_paths", bool(args.delivery_root)))
    delivery_root = args.delivery_root.resolve() if args.delivery_root else None

    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            finding(findings, f"INDEX-{index}", "critical", "ITEM-TYPE", "事项必须是对象")
            continue
        item_id = str(item.get("id", "")).strip() or f"INDEX-{index}"
        if item_id in seen:
            finding(findings, item_id, "major", "ITEM-DUPLICATE-ID", "事项 ID 重复")
        seen.add(item_id)

        source_text = str(item.get("source_text", "")).strip()
        if require_source and not source_text:
            finding(findings, item_id, "major", "ITEM-SOURCE", "缺少来源原文")

        decision = str(item.get("decision", "")).strip()
        if decision not in DECISIONS:
            finding(findings, item_id, "major", "ITEM-DECISION", "decision 无效或缺失", decision)

        status = str(item.get("status", "")).strip()
        if status not in STATUSES:
            finding(findings, item_id, "major", "ITEM-STATUS", "status 无效或缺失", status)
        elif release_candidate and status == "open":
            finding(findings, item_id, "major", "ITEM-OPEN", "发布候选中仍有未关闭事项")
        elif release_candidate and status == "deferred" and not allow_deferred:
            finding(findings, item_id, "major", "ITEM-DEFERRED", "发布策略不允许延期事项")

        response = str(item.get("response", "")).strip()
        if require_response and status == "resolved" and not response:
            finding(findings, item_id, "major", "ITEM-RESPONSE", "已关闭事项缺少正式回应")

        change_required = item.get("change_required")
        if not isinstance(change_required, bool):
            finding(findings, item_id, "major", "ITEM-CHANGE-FLAG", "change_required 必须是布尔值")
            change_required = False

        changes = item.get("actual_changes", [])
        if not isinstance(changes, list):
            finding(findings, item_id, "major", "ITEM-CHANGES-TYPE", "actual_changes 必须是数组")
            changes = []

        if status == "resolved" and change_required and decision in {"accept", "partial", "clarify"} and not changes:
            finding(findings, item_id, "major", "ITEM-NO-EVIDENCE", "事项要求修改，但没有实际修改证据")
        if not changes and response and ACTION_WORDS.search(response):
            finding(
                findings, item_id, "major", "ITEM-CLAIM-WITHOUT-CHANGE",
                "正式回应声称实施修改，但台账没有实际修改记录", response,
            )

        for change_index, change in enumerate(changes, start=1):
            if not isinstance(change, dict):
                finding(findings, item_id, "major", "CHANGE-TYPE", f"第 {change_index} 条修改不是对象")
                continue
            artifact = str(change.get("artifact", "")).strip()
            anchor = str(change.get("anchor", "")).strip()
            evidence = str(change.get("evidence", "")).strip()
            if not artifact:
                finding(findings, item_id, "major", "CHANGE-ARTIFACT", "修改记录缺少 artifact")
            if not anchor:
                finding(findings, item_id, "major", "CHANGE-ANCHOR", "修改记录缺少可核查位置", artifact)
            if not evidence:
                finding(findings, item_id, "minor", "CHANGE-EVIDENCE", "修改记录缺少证据摘要", artifact)
            if artifact and delivery_root and require_paths:
                candidate = safe_artifact_path(delivery_root, artifact)
                if candidate is None:
                    finding(findings, item_id, "critical", "CHANGE-PATH-ESCAPE", "artifact 路径越出交付目录", artifact)
                elif not candidate.exists():
                    finding(findings, item_id, "major", "CHANGE-PATH-MISSING", "修改指向的交付文件不存在", artifact)

    counts = Counter(item["severity"] for item in findings)
    result = {
        "auditor": "traceable-release-auditor/1.0",
        "ledger": str(args.ledger.resolve()),
        "delivery_root": str(delivery_root) if delivery_root else None,
        "items_checked": len(items),
        "summary": {level: counts.get(level, 0) for level in ("critical", "major", "minor", "observation")},
        "result": "fail" if counts.get("critical", 0) or counts.get("major", 0) else "pass",
        "findings": findings,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 2 if result["result"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
