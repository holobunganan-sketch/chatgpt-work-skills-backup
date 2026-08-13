#!/usr/bin/env python3
"""依据产物登记表和变更记录生成受授权范围约束的影响计划。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

SCRIPT_DIR = Path(__file__).absolute().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_artifact_registry import DIMENSIONS, validate_registry


DECISION_STATUSES = {"proposed", "authorized", "rejected", "blocked"}
CHANGE_STATUSES = {
    "proposed",
    "authorized",
    "in_progress",
    "implemented",
    "verified",
    "not_applicable",
    "requires_authorization",
    "blocked",
    "rejected",
}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, allow_empty: bool = True) -> bool:
    return isinstance(value, list) and all(_nonempty_string(item) for item in value) and (allow_empty or bool(value))


def _diagnostic(level: str, code: str, path: str, message: str) -> Dict[str, str]:
    return {"level": level, "code": code, "path": path, "message": message}


def validate_change_record(
    change: Any,
    artifact_ids: Set[str],
    canonical_items: Dict[str, Dict[str, Any]],
) -> List[Dict[str, str]]:
    diagnostics: List[Dict[str, str]] = []
    if not isinstance(change, dict):
        return [_diagnostic("error", "change_root", "$", "变更记录顶层必须是 JSON 对象。")]
    for field in ("schema_version", "change_id", "request_summary"):
        if not _nonempty_string(change.get(field)):
            diagnostics.append(_diagnostic("error", "required_field", field, "必须提供非空字符串。"))

    decision = change.get("decision")
    if not isinstance(decision, dict):
        diagnostics.append(_diagnostic("error", "decision", "decision", "必须提供决定对象。"))
        decision = {}
    if decision.get("status") not in DECISION_STATUSES:
        diagnostics.append(_diagnostic("error", "decision_status", "decision.status", f"允许值：{sorted(DECISION_STATUSES)}。"))
    if decision.get("status") == "authorized" and not _nonempty_string(decision.get("authority")):
        diagnostics.append(_diagnostic("error", "decision_authority", "decision.authority", "授权决定必须标明决定权来源。"))

    scope = change.get("authorized_scope")
    if not isinstance(scope, dict):
        diagnostics.append(_diagnostic("error", "authorized_scope", "authorized_scope", "必须提供授权范围对象。"))
        scope = {}
    scope_artifacts = scope.get("artifact_ids", [])
    if not _string_list(scope_artifacts):
        diagnostics.append(_diagnostic("error", "scope_artifacts", "authorized_scope.artifact_ids", "必须是产物 ID 字符串数组。"))
        scope_artifacts = []
    for artifact_id in scope_artifacts:
        if artifact_id not in artifact_ids:
            diagnostics.append(_diagnostic("error", "scope_unknown_artifact", "authorized_scope.artifact_ids", f"未登记产物 {artifact_id!r}。"))
    scope_dimensions = scope.get("dimensions", [])
    if not _string_list(scope_dimensions):
        diagnostics.append(_diagnostic("error", "scope_dimensions", "authorized_scope.dimensions", "必须是维度字符串数组。"))
        scope_dimensions = []
    unknown_dimensions = sorted(set(scope_dimensions) - DIMENSIONS)
    if unknown_dimensions:
        diagnostics.append(_diagnostic("error", "scope_unknown_dimension", "authorized_scope.dimensions", f"未知维度：{unknown_dimensions}。"))
    if not isinstance(scope.get("allow_transitive", False), bool):
        diagnostics.append(_diagnostic("error", "scope_transitive", "authorized_scope.allow_transitive", "必须是布尔值。"))

    canonical_updates = change.get("canonical_updates", [])
    if not isinstance(canonical_updates, list):
        diagnostics.append(_diagnostic("error", "canonical_updates", "canonical_updates", "必须是数组。"))
        canonical_updates = []
    seen_updates: Set[str] = set()
    for index, update in enumerate(canonical_updates):
        base = f"canonical_updates[{index}]"
        if not isinstance(update, dict):
            diagnostics.append(_diagnostic("error", "canonical_update_type", base, "规范项更新必须是对象。"))
            continue
        item_key = update.get("item_key")
        if item_key not in canonical_items:
            diagnostics.append(_diagnostic("error", "unknown_item", f"{base}.item_key", f"未登记规范项 {item_key!r}。"))
            continue
        if item_key in seen_updates:
            diagnostics.append(_diagnostic("error", "duplicate_item_update", f"{base}.item_key", f"规范项 {item_key!r} 在同一变更中重复。"))
        seen_updates.add(item_key)
        dimension = update.get("dimension")
        expected_dimension = canonical_items[item_key].get("dimension")
        if dimension != expected_dimension:
            diagnostics.append(_diagnostic("error", "item_dimension_mismatch", f"{base}.dimension", f"登记维度为 {expected_dimension!r}。"))
        if "after" not in update:
            diagnostics.append(_diagnostic("error", "missing_after", f"{base}.after", "必须提供新规范值。"))
        if "before" in update and update.get("before") != canonical_items[item_key].get("value"):
            diagnostics.append(_diagnostic("error", "stale_before_value", f"{base}.before", "改前值与登记表规范值不一致；请先解决版本或事实源冲突。"))
        if update.get("status") not in CHANGE_STATUSES:
            diagnostics.append(_diagnostic("error", "update_status", f"{base}.status", f"允许值：{sorted(CHANGE_STATUSES)}。"))

    direct_changes = change.get("direct_artifact_changes", [])
    if not isinstance(direct_changes, list):
        diagnostics.append(_diagnostic("error", "direct_changes", "direct_artifact_changes", "必须是数组。"))
        direct_changes = []
    for index, direct in enumerate(direct_changes):
        base = f"direct_artifact_changes[{index}]"
        if not isinstance(direct, dict):
            diagnostics.append(_diagnostic("error", "direct_change_type", base, "直接改动必须是对象。"))
            continue
        if direct.get("artifact_id") not in artifact_ids:
            diagnostics.append(_diagnostic("error", "direct_unknown_artifact", f"{base}.artifact_id", f"未登记产物 {direct.get('artifact_id')!r}。"))
        if not _nonempty_string(direct.get("locator")):
            diagnostics.append(_diagnostic("error", "direct_locator", f"{base}.locator", "必须提供定位。"))
        if not _nonempty_string(direct.get("action")):
            diagnostics.append(_diagnostic("error", "direct_action", f"{base}.action", "必须提供动作。"))
        dimensions = direct.get("dimensions")
        if not _string_list(dimensions, allow_empty=False):
            diagnostics.append(_diagnostic("error", "direct_dimensions", f"{base}.dimensions", "必须提供至少一个维度。"))
        else:
            unknown = sorted(set(dimensions) - DIMENSIONS)
            if unknown:
                diagnostics.append(_diagnostic("error", "direct_unknown_dimension", f"{base}.dimensions", f"未知维度：{unknown}。"))

    actual_changes = change.get("actual_changes", [])
    if not isinstance(actual_changes, list):
        diagnostics.append(_diagnostic("error", "actual_changes", "actual_changes", "必须是数组。"))
        actual_changes = []
    for index, actual in enumerate(actual_changes):
        base = f"actual_changes[{index}]"
        if not isinstance(actual, dict):
            diagnostics.append(_diagnostic("error", "actual_change_type", base, "实际改动必须是对象。"))
            continue
        if actual.get("artifact_id") not in artifact_ids:
            diagnostics.append(_diagnostic("error", "actual_unknown_artifact", f"{base}.artifact_id", f"未登记产物 {actual.get('artifact_id')!r}。"))
        if not _nonempty_string(actual.get("locator")):
            diagnostics.append(_diagnostic("error", "actual_locator", f"{base}.locator", "必须提供定位。"))
        dimensions = actual.get("dimensions")
        if not _string_list(dimensions, allow_empty=False):
            diagnostics.append(_diagnostic("error", "actual_dimensions", f"{base}.dimensions", "必须提供至少一个维度。"))
        else:
            unknown = sorted(set(dimensions) - DIMENSIONS)
            if unknown:
                diagnostics.append(_diagnostic("error", "actual_unknown_dimension", f"{base}.dimensions", f"未知维度：{unknown}。"))
        status = actual.get("status")
        if status not in CHANGE_STATUSES:
            diagnostics.append(_diagnostic("error", "actual_status", f"{base}.status", f"允许值：{sorted(CHANGE_STATUSES)}。"))
        if status in {"implemented", "verified", "not_applicable"}:
            evidence = actual.get("evidence")
            if not isinstance(evidence, dict) or not _nonempty_string(evidence.get("method")) or not _nonempty_string(evidence.get("value")):
                diagnostics.append(_diagnostic("error", "actual_evidence", f"{base}.evidence", "已实施、已验证或无需修改的记录必须包含方法和证据。"))

    return diagnostics


def _build_edges(registry: Dict[str, Any]) -> DefaultDict[str, List[Dict[str, Any]]]:
    artifact_index = {item["artifact_id"]: item for item in registry.get("artifacts", [])}
    edges: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    seen: Set[Tuple[str, str, str, Tuple[str, ...]]] = set()

    def add_edge(source: str, target: str, mode: str, dimensions: Iterable[str], rule_id: str) -> None:
        dimension_tuple = tuple(sorted(set(dimensions)))
        identity = (source, target, mode, dimension_tuple)
        if identity in seen:
            return
        seen.add(identity)
        edges[source].append(
            {
                "source": source,
                "target": target,
                "mode": mode,
                "dimensions": list(dimension_tuple),
                "rule_id": rule_id,
            }
        )

    for target_id, artifact in artifact_index.items():
        for source_id in artifact.get("derived_from", []):
            add_edge(source_id, target_id, "derived_from", artifact.get("content_dimensions", []), f"derived:{source_id}->{target_id}")
    for rule in registry.get("propagation_rules", []):
        add_edge(
            rule["from_artifact_id"],
            rule["to_artifact_id"],
            rule["mode"],
            rule["dimensions"],
            rule["rule_id"],
        )
    return edges


def _action_for_mode(mode: str) -> str:
    return {
        "derived_from": "regenerate_or_synchronize",
        "generated_from": "regenerate_from_source",
        "must_sync": "synchronize_canonical_content",
        "verify_only": "verify_consistency",
        "reference_only": "verify_reference_target",
    }.get(mode, "verify_and_update")


def build_plan(registry: Dict[str, Any], change: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = {item["artifact_id"]: item for item in registry.get("artifacts", [])}
    items = {item["key"]: item for item in registry.get("canonical_items", [])}
    edges = _build_edges(registry)
    scope = change.get("authorized_scope", {})
    authorized_artifacts = set(scope.get("artifact_ids", []))
    authorized_dimensions = set(scope.get("dimensions", []))
    allow_transitive = bool(scope.get("allow_transitive", False))
    decision_authorized = change.get("decision", {}).get("status") == "authorized"

    task_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def add_task(
        artifact_id: str,
        dimension: str,
        action: str,
        reason: str,
        item_key: Optional[str] = None,
        locator: Optional[str] = None,
        depth: int = 0,
        direct: bool = False,
    ) -> None:
        key = (artifact_id, dimension)
        task = task_map.setdefault(
            key,
            {
                "task_id": f"{artifact_id}:{dimension}",
                "artifact_id": artifact_id,
                "artifact_path": artifacts[artifact_id]["path"],
                "dimension": dimension,
                "actions": [],
                "reasons": [],
                "canonical_item_keys": [],
                "locators": [],
                "minimum_depth": depth,
                "has_direct_basis": direct,
            },
        )
        if action not in task["actions"]:
            task["actions"].append(action)
        if reason not in task["reasons"]:
            task["reasons"].append(reason)
        if item_key and item_key not in task["canonical_item_keys"]:
            task["canonical_item_keys"].append(item_key)
        if locator and locator not in task["locators"]:
            task["locators"].append(locator)
        task["minimum_depth"] = min(task["minimum_depth"], depth)
        task["has_direct_basis"] = task["has_direct_basis"] or direct

    def propagate(seeds: Iterable[str], dimension: str, item_key: Optional[str]) -> None:
        queue = deque((seed, 0) for seed in seeds)
        visited: Dict[str, int] = {}
        while queue:
            source, depth = queue.popleft()
            if source in visited and visited[source] <= depth:
                continue
            visited[source] = depth
            for edge in edges.get(source, []):
                if dimension not in edge["dimensions"] and "all" not in edge["dimensions"]:
                    continue
                target = edge["target"]
                next_depth = depth + 1
                add_task(
                    target,
                    dimension,
                    _action_for_mode(edge["mode"]),
                    f"沿规则 {edge['rule_id']} 从 {source} 传导",
                    item_key=item_key,
                    depth=next_depth,
                    direct=False,
                )
                queue.append((target, next_depth))

    for update in change.get("canonical_updates", []):
        item_key = update["item_key"]
        item = items[item_key]
        dimension = item["dimension"]
        source_id = item["source_artifact_id"]
        add_task(
            source_id,
            dimension,
            "update_authoritative_source",
            f"规范项 {item_key} 的权威值发生变化",
            item_key=item_key,
            locator=item.get("source_locator"),
            direct=True,
        )
        seeds: Set[str] = {source_id}
        for occurrence in item.get("occurrences", []):
            artifact_id = occurrence["artifact_id"]
            seeds.add(artifact_id)
            add_task(
                artifact_id,
                dimension,
                "verify_and_update_occurrence",
                f"规范项 {item_key} 的已登记出现位置",
                item_key=item_key,
                locator=occurrence.get("locator"),
                direct=True,
            )
        propagate(seeds, dimension, item_key)

    for direct in change.get("direct_artifact_changes", []):
        artifact_id = direct["artifact_id"]
        for dimension in direct.get("dimensions", []):
            add_task(
                artifact_id,
                dimension,
                direct["action"],
                "变更记录中的直接产物动作",
                locator=direct.get("locator"),
                direct=True,
            )
            propagate([artifact_id], dimension, None)

    actual_map: DefaultDict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for actual in change.get("actual_changes", []):
        for dimension in actual.get("dimensions", []):
            actual_map[(actual["artifact_id"], dimension)].append(actual)

    tasks: List[Dict[str, Any]] = []
    for key, task in task_map.items():
        artifact_id, dimension = key
        authorized = (
            decision_authorized
            and artifact_id in authorized_artifacts
            and dimension in authorized_dimensions
            and (allow_transitive or task["has_direct_basis"])
        )
        if not decision_authorized:
            status = "awaiting_decision"
        elif not authorized:
            status = "requires_authorization"
        else:
            actuals = actual_map.get(key, [])
            statuses = {item.get("status") for item in actuals}
            if "verified" in statuses:
                status = "verified"
            elif "not_applicable" in statuses:
                status = "not_applicable"
            elif "implemented" in statuses:
                status = "verify_required"
            elif "blocked" in statuses:
                status = "blocked"
            else:
                status = "planned"
        task["status"] = status
        task["actions"].sort()
        task["reasons"].sort()
        task["canonical_item_keys"].sort()
        task["locators"].sort()
        task["actual_change_evidence"] = [
            {
                "locator": item.get("locator"),
                "status": item.get("status"),
                "evidence": item.get("evidence", {}),
            }
            for item in actual_map.get(key, [])
        ]
        tasks.append(task)

    status_order = {
        "blocked": 0,
        "requires_authorization": 1,
        "awaiting_decision": 2,
        "verify_required": 3,
        "planned": 4,
        "not_applicable": 5,
        "verified": 6,
    }
    tasks.sort(key=lambda item: (status_order.get(item["status"], 99), item["minimum_depth"], item["artifact_id"], item["dimension"]))
    counts: Dict[str, int] = defaultdict(int)
    for task in tasks:
        counts[task["status"]] += 1

    return {
        "plan_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_id": registry.get("registry_id"),
        "change_id": change.get("change_id"),
        "authorization": {
            "decision_status": change.get("decision", {}).get("status"),
            "artifact_ids": sorted(authorized_artifacts),
            "dimensions": sorted(authorized_dimensions),
            "allow_transitive": allow_transitive,
            "note": "影响识别不授予写权限；任务状态按显式授权范围计算。",
        },
        "summary": {
            "task_count": len(tasks),
            "status_counts": dict(sorted(counts.items())),
            "release_blocked": any(task["status"] in {"blocked", "requires_authorization", "awaiting_decision", "verify_required", "planned"} for task in tasks),
        },
        "tasks": tasks,
    }


def _write_json(path: Optional[Path], payload: Dict[str, Any], compact: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=None if compact else 2, separators=(",", ":") if compact else None)
    if path is None:
        print(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="生成跨交付物变更影响计划。")
    parser.add_argument("registry", type=Path, help="产物登记表 JSON 路径")
    parser.add_argument("change_record", type=Path, help="变更记录 JSON 路径")
    parser.add_argument("--output", type=Path, help="影响计划输出路径；省略时输出到标准输出")
    parser.add_argument("--compact", action="store_true", help="输出紧凑 JSON")
    parser.add_argument("--fail-on-unauthorized", action="store_true", help="存在待授权目标时返回退出码 3")
    args = parser.parse_args(argv)

    try:
        registry = _load_json(args.registry)
        change = _load_json(args.change_record)
    except FileNotFoundError as exc:
        print(f"输入文件不存在：{exc.filename}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"JSON 解析失败：{exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"无法读取输入：{exc}", file=sys.stderr)
        return 2

    if args.output:
        output_resolved = args.output.resolve()
        if output_resolved in {args.registry.resolve(), args.change_record.resolve()}:
            print("输出路径不得覆盖输入文件。", file=sys.stderr)
            return 2

    registry_issues = validate_registry(registry, args.registry, check_paths=False)
    registry_errors = [item for item in registry_issues if item["severity"] == "error"]
    if registry_errors:
        print(json.dumps({"error": "registry_invalid", "issues": registry_issues}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    artifacts = {item["artifact_id"] for item in registry.get("artifacts", [])}
    canonical_items = {item["key"]: item for item in registry.get("canonical_items", [])}
    diagnostics = validate_change_record(change, artifacts, canonical_items)
    errors = [item for item in diagnostics if item["level"] == "error"]
    if errors:
        print(json.dumps({"error": "change_record_invalid", "diagnostics": diagnostics}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    plan = build_plan(registry, change)
    plan["diagnostics"] = {
        "registry_warnings": [item for item in registry_issues if item["severity"] == "warning"],
        "change_warnings": [item for item in diagnostics if item["level"] == "warning"],
    }
    _write_json(args.output, plan, args.compact)

    unauthorized = plan["summary"]["status_counts"].get("requires_authorization", 0)
    if args.fail_on_unauthorized and unauthorized:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
