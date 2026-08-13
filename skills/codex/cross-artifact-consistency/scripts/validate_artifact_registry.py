#!/usr/bin/env python3
"""校验跨交付物一致性协调技能使用的产物登记表。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


ARTIFACT_ROLES = {"authoritative", "working", "derived", "deliverable", "internal"}
ARTIFACT_STATUSES = {
    "source_locked",
    "working",
    "sync_pending",
    "verified",
    "release_ready",
}
DIMENSIONS = {
    "term",
    "number",
    "identifier",
    "reference",
    "version",
    "structure",
    "visual",
    "other",
}
PROPAGATION_MODES = {
    "derived_from",
    "must_sync",
    "verify_only",
    "reference_only",
    "generated_from",
}
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _issue(severity: str, code: str, path: str, message: str) -> Dict[str, str]:
    return {"severity": severity, "code": code, "path": path, "message": message}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, allow_empty: bool = True) -> bool:
    if not isinstance(value, list) or not all(_nonempty_string(item) for item in value):
        return False
    return allow_empty or bool(value)


def _normalized_path(value: str) -> str:
    return os.path.normpath(value).replace("\\", "/").casefold()


def _find_cycle(graph: Dict[str, List[str]]) -> Optional[List[str]]:
    state: Dict[str, int] = {node: 0 for node in graph}
    stack: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        state[node] = 1
        stack.append(node)
        for parent in graph.get(node, []):
            if parent not in state:
                continue
            if state[parent] == 0:
                cycle = visit(parent)
                if cycle:
                    return cycle
            elif state[parent] == 1:
                start = stack.index(parent)
                return stack[start:] + [parent]
        stack.pop()
        state[node] = 2
        return None

    for node in graph:
        if state[node] == 0:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


def _ancestor_closure(artifact_id: str, graph: Dict[str, List[str]]) -> Set[str]:
    seen: Set[str] = set()
    pending = list(graph.get(artifact_id, []))
    while pending:
        parent = pending.pop()
        if parent in seen:
            continue
        seen.add(parent)
        pending.extend(graph.get(parent, []))
    return seen


def validate_registry(
    data: Any,
    registry_path: Optional[Path] = None,
    check_paths: bool = False,
) -> List[Dict[str, str]]:
    """返回结构化问题列表；error 表示登记表不可用。"""

    issues: List[Dict[str, str]] = []
    if not isinstance(data, dict):
        return [_issue("error", "root_type", "$", "登记表顶层必须是 JSON 对象。")]

    for field in ("schema_version", "registry_id", "project_id"):
        if not _nonempty_string(data.get(field)):
            issues.append(_issue("error", "required_field", field, "必须提供非空字符串。"))

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        issues.append(_issue("error", "artifacts_required", "artifacts", "必须登记至少一个产物。"))
        artifacts = []

    artifact_index: Dict[str, Dict[str, Any]] = {}
    path_index: Dict[str, str] = {}
    derived_graph: Dict[str, List[str]] = {}

    for index, artifact in enumerate(artifacts):
        base = f"artifacts[{index}]"
        if not isinstance(artifact, dict):
            issues.append(_issue("error", "artifact_type", base, "产物记录必须是对象。"))
            continue
        artifact_id = artifact.get("artifact_id")
        if not _nonempty_string(artifact_id) or not ID_PATTERN.fullmatch(artifact_id):
            issues.append(_issue("error", "artifact_id", f"{base}.artifact_id", "必须使用稳定的字母、数字、点、下划线或连字符 ID。"))
            continue
        if artifact_id in artifact_index:
            issues.append(_issue("error", "duplicate_artifact_id", f"{base}.artifact_id", f"产物 ID {artifact_id!r} 重复。"))
            continue
        artifact_index[artifact_id] = artifact

        path_value = artifact.get("path")
        if not _nonempty_string(path_value):
            issues.append(_issue("error", "artifact_path", f"{base}.path", "必须提供非空路径。"))
        else:
            normalized = _normalized_path(path_value)
            if normalized in path_index:
                issues.append(_issue("error", "duplicate_artifact_path", f"{base}.path", f"路径与产物 {path_index[normalized]!r} 重复。"))
            else:
                path_index[normalized] = artifact_id
            if check_paths and registry_path is not None:
                candidate = Path(path_value)
                if not candidate.is_absolute():
                    candidate = registry_path.parent / candidate
                if not candidate.exists():
                    issues.append(_issue("warning", "path_missing", f"{base}.path", f"路径不存在：{candidate}"))

        role = artifact.get("role")
        if role not in ARTIFACT_ROLES:
            issues.append(_issue("error", "artifact_role", f"{base}.role", f"允许值：{sorted(ARTIFACT_ROLES)}。"))

        status = artifact.get("status")
        if status not in ARTIFACT_STATUSES:
            issues.append(_issue("error", "artifact_status", f"{base}.status", f"允许值：{sorted(ARTIFACT_STATUSES)}。"))

        if not _nonempty_string(artifact.get("format")):
            issues.append(_issue("error", "artifact_format", f"{base}.format", "必须提供格式。"))
        if not _nonempty_string(artifact.get("version")):
            issues.append(_issue("error", "artifact_version", f"{base}.version", "必须提供版本。"))

        tags = artifact.get("tags", [])
        if not _string_list(tags):
            issues.append(_issue("error", "artifact_tags", f"{base}.tags", "必须是字符串数组。"))

        parents = artifact.get("derived_from", [])
        if not _string_list(parents):
            issues.append(_issue("error", "derived_from_type", f"{base}.derived_from", "必须是产物 ID 字符串数组。"))
            parents = []
        if len(parents) != len(set(parents)):
            issues.append(_issue("error", "duplicate_parent", f"{base}.derived_from", "同一上游产物不得重复。"))
        if role == "authoritative" and parents:
            issues.append(_issue("error", "authoritative_has_parent", f"{base}.derived_from", "权威源不得声明派生来源。"))
        if role == "derived" and not parents:
            issues.append(_issue("error", "derived_without_parent", f"{base}.derived_from", "派生物必须声明至少一个上游产物。"))
        derived_graph[artifact_id] = list(parents)

        dimensions = artifact.get("content_dimensions", [])
        if not _string_list(dimensions, allow_empty=False):
            issues.append(_issue("error", "artifact_dimensions", f"{base}.content_dimensions", "必须提供至少一个内容维度。"))
        else:
            unknown = sorted(set(dimensions) - DIMENSIONS)
            if unknown:
                issues.append(_issue("error", "unknown_dimension", f"{base}.content_dimensions", f"未知维度：{unknown}。"))

    for artifact_id, parents in derived_graph.items():
        for parent in parents:
            if parent not in artifact_index:
                issues.append(_issue("error", "unknown_parent", f"artifacts[{artifact_id}].derived_from", f"未登记上游产物 {parent!r}。"))
            if parent == artifact_id:
                issues.append(_issue("error", "self_parent", f"artifacts[{artifact_id}].derived_from", "产物不得派生自自身。"))

    cycle = _find_cycle(derived_graph)
    if cycle:
        issues.append(_issue("error", "derived_cycle", "artifacts[*].derived_from", "派生关系存在循环：" + " -> ".join(cycle)))

    canonical_items = data.get("canonical_items", [])
    if not isinstance(canonical_items, list):
        issues.append(_issue("error", "canonical_items_type", "canonical_items", "必须是数组。"))
        canonical_items = []
    item_keys: Set[str] = set()
    for index, item in enumerate(canonical_items):
        base = f"canonical_items[{index}]"
        if not isinstance(item, dict):
            issues.append(_issue("error", "canonical_item_type", base, "规范项必须是对象。"))
            continue
        key = item.get("key")
        if not _nonempty_string(key) or not ID_PATTERN.fullmatch(key):
            issues.append(_issue("error", "canonical_key", f"{base}.key", "必须提供稳定规范项键。"))
        elif key in item_keys:
            issues.append(_issue("error", "duplicate_canonical_key", f"{base}.key", f"规范项键 {key!r} 重复。"))
        else:
            item_keys.add(key)
        dimension = item.get("dimension")
        if dimension not in DIMENSIONS:
            issues.append(_issue("error", "canonical_dimension", f"{base}.dimension", f"允许值：{sorted(DIMENSIONS)}。"))
        if "value" not in item:
            issues.append(_issue("error", "canonical_value", f"{base}.value", "必须提供规范值；空值也应显式写入。"))
        if not _nonempty_string(item.get("semantics")):
            issues.append(_issue("error", "canonical_semantics", f"{base}.semantics", "必须说明语义、口径或适用范围。"))
        source_id = item.get("source_artifact_id")
        if source_id not in artifact_index:
            issues.append(_issue("error", "canonical_source", f"{base}.source_artifact_id", f"未登记权威产物 {source_id!r}。"))
        elif artifact_index[source_id].get("role") != "authoritative" and "authority" not in artifact_index[source_id].get("tags", []):
            issues.append(_issue("warning", "source_role", f"{base}.source_artifact_id", "规范项来源未标记为 authoritative 或 authority。"))
        if not _nonempty_string(item.get("source_locator")):
            issues.append(_issue("error", "source_locator", f"{base}.source_locator", "必须提供可核查定位。"))
        aliases = item.get("aliases", [])
        if not _string_list(aliases):
            issues.append(_issue("error", "aliases_type", f"{base}.aliases", "必须是字符串数组。"))

        occurrences = item.get("occurrences", [])
        if not isinstance(occurrences, list):
            issues.append(_issue("error", "occurrences_type", f"{base}.occurrences", "必须是数组。"))
            occurrences = []
        occurrence_keys: Set[Tuple[str, str]] = set()
        source_seen = False
        for occ_index, occurrence in enumerate(occurrences):
            occ_path = f"{base}.occurrences[{occ_index}]"
            if not isinstance(occurrence, dict):
                issues.append(_issue("error", "occurrence_type", occ_path, "出现位置必须是对象。"))
                continue
            occ_artifact = occurrence.get("artifact_id")
            locator = occurrence.get("locator")
            if occ_artifact not in artifact_index:
                issues.append(_issue("error", "occurrence_artifact", f"{occ_path}.artifact_id", f"未登记产物 {occ_artifact!r}。"))
            if not _nonempty_string(locator):
                issues.append(_issue("error", "occurrence_locator", f"{occ_path}.locator", "必须提供定位。"))
                locator = ""
            pair = (str(occ_artifact), str(locator))
            if pair in occurrence_keys:
                issues.append(_issue("error", "duplicate_occurrence", occ_path, "出现位置重复。"))
            occurrence_keys.add(pair)
            if occ_artifact == source_id:
                source_seen = True
            required = occurrence.get("required", True)
            if not isinstance(required, bool):
                issues.append(_issue("error", "occurrence_required", f"{occ_path}.required", "必须是布尔值。"))
        if occurrences and source_id in artifact_index and not source_seen:
            issues.append(_issue("warning", "source_occurrence_missing", f"{base}.occurrences", "出现位置未包含规范项权威来源。"))

    propagation_rules = data.get("propagation_rules", [])
    if not isinstance(propagation_rules, list):
        issues.append(_issue("error", "propagation_rules_type", "propagation_rules", "必须是数组。"))
        propagation_rules = []
    rule_ids: Set[str] = set()
    for index, rule in enumerate(propagation_rules):
        base = f"propagation_rules[{index}]"
        if not isinstance(rule, dict):
            issues.append(_issue("error", "propagation_rule_type", base, "传播规则必须是对象。"))
            continue
        rule_id = rule.get("rule_id")
        if not _nonempty_string(rule_id) or not ID_PATTERN.fullmatch(rule_id):
            issues.append(_issue("error", "propagation_rule_id", f"{base}.rule_id", "必须提供稳定规则 ID。"))
        elif rule_id in rule_ids:
            issues.append(_issue("error", "duplicate_rule_id", f"{base}.rule_id", f"规则 ID {rule_id!r} 重复。"))
        else:
            rule_ids.add(rule_id)
        source_id = rule.get("from_artifact_id")
        target_id = rule.get("to_artifact_id")
        if source_id not in artifact_index:
            issues.append(_issue("error", "rule_source", f"{base}.from_artifact_id", f"未登记产物 {source_id!r}。"))
        if target_id not in artifact_index:
            issues.append(_issue("error", "rule_target", f"{base}.to_artifact_id", f"未登记产物 {target_id!r}。"))
        if source_id == target_id:
            issues.append(_issue("error", "rule_self_edge", base, "传播规则不得指向自身。"))
        dimensions = rule.get("dimensions")
        if not _string_list(dimensions, allow_empty=False):
            issues.append(_issue("error", "rule_dimensions", f"{base}.dimensions", "必须提供至少一个维度。"))
        else:
            unknown = sorted(set(dimensions) - DIMENSIONS - {"all"})
            if unknown:
                issues.append(_issue("error", "rule_unknown_dimension", f"{base}.dimensions", f"未知维度：{unknown}。"))
        if rule.get("mode") not in PROPAGATION_MODES:
            issues.append(_issue("error", "rule_mode", f"{base}.mode", f"允许值：{sorted(PROPAGATION_MODES)}。"))
        if not isinstance(rule.get("required", True), bool):
            issues.append(_issue("error", "rule_required", f"{base}.required", "必须是布尔值。"))

    release_sets = data.get("release_sets", [])
    if not isinstance(release_sets, list):
        issues.append(_issue("error", "release_sets_type", "release_sets", "必须是数组。"))
        release_sets = []
    release_ids: Set[str] = set()
    for index, release in enumerate(release_sets):
        base = f"release_sets[{index}]"
        if not isinstance(release, dict):
            issues.append(_issue("error", "release_set_type", base, "发布集合必须是对象。"))
            continue
        release_id = release.get("release_set_id")
        if not _nonempty_string(release_id) or not ID_PATTERN.fullmatch(release_id):
            issues.append(_issue("error", "release_set_id", f"{base}.release_set_id", "必须提供稳定发布集合 ID。"))
        elif release_id in release_ids:
            issues.append(_issue("error", "duplicate_release_id", f"{base}.release_set_id", f"发布集合 ID {release_id!r} 重复。"))
        else:
            release_ids.add(release_id)
        members = release.get("member_artifact_ids")
        if not _string_list(members, allow_empty=False):
            issues.append(_issue("error", "release_members", f"{base}.member_artifact_ids", "必须提供至少一个成员。"))
            members = []
        for member in members:
            if member not in artifact_index:
                issues.append(_issue("error", "release_unknown_member", f"{base}.member_artifact_ids", f"未登记产物 {member!r}。"))
        groups = release.get("content_equivalence_groups", [])
        if not isinstance(groups, list):
            issues.append(_issue("error", "equivalence_groups_type", f"{base}.content_equivalence_groups", "必须是数组。"))
            groups = []
        group_ids: Set[str] = set()
        for group_index, group in enumerate(groups):
            group_path = f"{base}.content_equivalence_groups[{group_index}]"
            if not isinstance(group, dict):
                issues.append(_issue("error", "equivalence_group_type", group_path, "内容等价组必须是对象。"))
                continue
            group_id = group.get("group_id")
            if not _nonempty_string(group_id) or not ID_PATTERN.fullmatch(group_id):
                issues.append(_issue("error", "equivalence_group_id", f"{group_path}.group_id", "必须提供稳定等价组 ID。"))
            elif group_id in group_ids:
                issues.append(_issue("error", "duplicate_group_id", f"{group_path}.group_id", f"组 ID {group_id!r} 重复。"))
            else:
                group_ids.add(group_id)
            group_artifacts = group.get("artifact_ids")
            if not _string_list(group_artifacts, allow_empty=False) or len(group_artifacts) < 2:
                issues.append(_issue("error", "equivalence_members", f"{group_path}.artifact_ids", "内容等价组必须包含至少两个产物。"))
                group_artifacts = []
            source_id = group.get("canonical_source_artifact_id")
            if source_id not in artifact_index:
                issues.append(_issue("error", "equivalence_source", f"{group_path}.canonical_source_artifact_id", f"未登记共同内容源 {source_id!r}。"))
            for member in group_artifacts:
                if member not in artifact_index:
                    issues.append(_issue("error", "equivalence_unknown_member", f"{group_path}.artifact_ids", f"未登记产物 {member!r}。"))
                    continue
                if member not in members:
                    issues.append(_issue("error", "equivalence_not_release_member", f"{group_path}.artifact_ids", f"产物 {member!r} 不在发布集合成员中。"))
                if source_id in artifact_index and source_id != member and source_id not in _ancestor_closure(member, derived_graph):
                    issues.append(_issue("error", "equivalence_source_mismatch", group_path, f"共同内容源 {source_id!r} 未处于产物 {member!r} 的上游关系中。"))
            allowed = group.get("allowed_differences", [])
            if not _string_list(allowed):
                issues.append(_issue("error", "allowed_differences", f"{group_path}.allowed_differences", "必须是字符串数组。"))

    return issues


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _print_text(issues: Iterable[Dict[str, str]], strict: bool) -> None:
    issue_list = list(issues)
    errors = sum(item["severity"] == "error" for item in issue_list)
    warnings = sum(item["severity"] == "warning" for item in issue_list)
    for item in issue_list:
        label = "错误" if item["severity"] == "error" else "警告"
        print(f"[{label}] {item['code']} @ {item['path']}: {item['message']}")
    if not issue_list:
        print("登记表校验通过：未发现结构或关系问题。")
    else:
        strict_note = "；严格模式会把警告视为失败" if strict and warnings else ""
        print(f"校验结果：{errors} 个错误，{warnings} 个警告{strict_note}。")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="校验跨交付物产物登记表。")
    parser.add_argument("registry", type=Path, help="产物登记表 JSON 路径")
    parser.add_argument("--strict", action="store_true", help="出现警告时也返回失败")
    parser.add_argument("--check-paths", action="store_true", help="检查登记路径是否存在")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出校验结果")
    args = parser.parse_args(argv)

    try:
        data = _load_json(args.registry)
    except FileNotFoundError:
        print(f"登记表不存在：{args.registry}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"JSON 解析失败：{exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"无法读取登记表：{exc}", file=sys.stderr)
        return 2

    issues = validate_registry(data, args.registry, args.check_paths)
    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    valid = errors == 0 and (warnings == 0 or not args.strict)

    if args.json:
        print(json.dumps({"valid": valid, "errors": errors, "warnings": warnings, "issues": issues}, ensure_ascii=False, indent=2))
    else:
        _print_text(issues, args.strict)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
