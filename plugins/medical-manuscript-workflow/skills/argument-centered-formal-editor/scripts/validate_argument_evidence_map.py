#!/usr/bin/env python3
"""验证主线—证据工作图的结构完整性和交叉引用。

仅使用 Python 标准库。错误表示工作图无法支持后续编辑；警告需要人工判断。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Issue:
    severity: str
    code: str
    location: str
    message: str


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError(f"无法读取文件：{exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 无法解析：第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("工作图顶层必须是 JSON 对象")
    return data


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def list_of_objects(data: dict[str, Any], key: str, issues: list[Issue]) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list):
        issues.append(Issue("error", "MISSING_ARRAY", key, f"{key} 必须是数组"))
        return []
    objects: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, dict):
            objects.append(item)
        else:
            issues.append(
                Issue("error", "INVALID_ITEM", f"{key}[{index}]", "数组项目必须是对象")
            )
    return objects


def index_unique(
    items: list[dict[str, Any]],
    id_key: str,
    location: str,
    issues: list[Issue],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        item_id = item.get(id_key)
        item_location = f"{location}[{index}].{id_key}"
        if not nonempty(item_id):
            issues.append(Issue("error", "MISSING_ID", item_location, f"缺少 {id_key}"))
            continue
        if item_id in result:
            issues.append(Issue("error", "DUPLICATE_ID", item_location, f"重复标识：{item_id}"))
            continue
        result[item_id] = item
    return result


def require_fields(
    item: dict[str, Any],
    fields: Iterable[str],
    location: str,
    issues: list[Issue],
) -> None:
    for field in fields:
        if not nonempty(item.get(field)):
            issues.append(
                Issue("error", "MISSING_CONTENT", f"{location}.{field}", f"{field} 不能为空")
            )


def validate_document(data: dict[str, Any], issues: list[Issue]) -> None:
    if data.get("schema_version") != "2.0":
        issues.append(
            Issue("error", "SCHEMA_VERSION", "schema_version", "schema_version 必须为 2.0")
        )
    document = data.get("document")
    if not isinstance(document, dict):
        issues.append(Issue("error", "MISSING_OBJECT", "document", "缺少 document 对象"))
        return
    require_fields(
        document,
        ("document_type", "purpose", "core_question", "target_answer"),
        "document",
        issues,
    )


def validate_mainline(
    data: dict[str, Any],
    issues: list[Issue],
) -> dict[str, dict[str, Any]]:
    mainline = data.get("mainline")
    if not isinstance(mainline, dict):
        issues.append(Issue("error", "MISSING_OBJECT", "mainline", "缺少 mainline 对象"))
        return {}
    if not nonempty(mainline.get("one_sentence_summary")):
        issues.append(
            Issue(
                "error",
                "MISSING_MAINLINE_SUMMARY",
                "mainline.one_sentence_summary",
                "缺少主线一句话摘要",
            )
        )
    nodes = mainline.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        issues.append(Issue("error", "MISSING_NODES", "mainline.nodes", "至少需要一个主线节点"))
        return {}
    node_items = [item for item in nodes if isinstance(item, dict)]
    node_index = index_unique(node_items, "node_id", "mainline.nodes", issues)
    active_ids = {
        node_id for node_id, node in node_index.items() if node.get("status") != "remove"
    }
    incoming: dict[str, int] = {node_id: 0 for node_id in active_ids}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in active_ids}

    for node_id, node in node_index.items():
        location = f"mainline.nodes[{node_id}]"
        if node.get("status") == "remove":
            continue
        require_fields(node, ("judgment", "function"), location, issues)
        next_ids = node.get("next_node_ids", [])
        if not isinstance(next_ids, list):
            issues.append(
                Issue("error", "INVALID_LINKS", f"{location}.next_node_ids", "必须是数组")
            )
            continue
        for target in next_ids:
            if target not in active_ids:
                issues.append(
                    Issue(
                        "error",
                        "BROKEN_NODE_LINK",
                        f"{location}.next_node_ids",
                        f"引用不存在或已移除的节点：{target}",
                    )
                )
                continue
            incoming[target] += 1
            adjacency[node_id].append(target)

    roots = [node_id for node_id, count in incoming.items() if count == 0]
    if not roots and active_ids:
        issues.append(
            Issue("error", "NO_MAINLINE_ROOT", "mainline.nodes", "主线没有可识别的起点")
        )
    if len(roots) > 1:
        issues.append(
            Issue(
                "warning",
                "MULTIPLE_MAINLINE_ROOTS",
                "mainline.nodes",
                f"主线存在多个起点：{', '.join(sorted(roots))}",
            )
        )

    reachable: set[str] = set()
    stack = list(roots)
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        stack.extend(adjacency.get(current, []))
    unreachable = active_ids - reachable
    if unreachable:
        issues.append(
            Issue(
                "error",
                "UNREACHABLE_NODES",
                "mainline.nodes",
                f"以下主线节点无法从起点到达：{', '.join(sorted(unreachable))}",
            )
        )
    return node_index


def validate_paragraphs(
    data: dict[str, Any],
    node_index: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> dict[str, dict[str, Any]]:
    paragraphs = list_of_objects(data, "paragraphs", issues)
    paragraph_index = index_unique(paragraphs, "paragraph_id", "paragraphs", issues)
    if not paragraph_index:
        issues.append(Issue("error", "NO_PARAGRAPHS", "paragraphs", "至少需要一个段落记录"))
        return {}
    valid_nodes = {
        node_id for node_id, node in node_index.items() if node.get("status") != "remove"
    }
    for paragraph_id, paragraph in paragraph_index.items():
        location = f"paragraphs[{paragraph_id}]"
        require_fields(
            paragraph,
            ("target_judgment", "reader_enters_knowing", "reader_leaves_knowing"),
            location,
            issues,
        )
        node_ids = paragraph.get("mainline_node_ids")
        if not isinstance(node_ids, list) or not node_ids:
            issues.append(
                Issue("error", "PARAGRAPH_WITHOUT_NODE", location, "段落必须连接主线节点")
            )
            continue
        for node_id in node_ids:
            if node_id not in valid_nodes:
                issues.append(
                    Issue(
                        "error",
                        "BROKEN_PARAGRAPH_NODE",
                        f"{location}.mainline_node_ids",
                        f"引用不存在或已移除的节点：{node_id}",
                    )
                )
    return paragraph_index


ALIGNMENT_ACTIONS = {
    "high": {"retain", "light_adapt", "drop"},
    "partial": {"light_adapt", "extract", "drop"},
    "local_only": {"extract", "drop"},
    "none": {"drop"},
}

ARGUMENT_TASKS = {
    "establish",
    "quantify",
    "explain",
    "compare_consistency",
    "compare_difference",
    "bridge",
    "discriminate",
    "connect",
    "support_next_step",
    "example",
}


def validate_sources(
    data: dict[str, Any],
    paragraph_index: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> dict[str, dict[str, Any]]:
    sources = list_of_objects(data, "sources", issues)
    source_index = index_unique(sources, "source_id", "sources", issues)
    for source_id, source in source_index.items():
        location = f"sources[{source_id}]"
        require_fields(source, ("source_reference",), location, issues)
        alignment = source.get("source_narrative_alignment")
        action = source.get("adaptation_action")
        disposition = source.get("disposition")
        if alignment not in ALIGNMENT_ACTIONS:
            issues.append(
                Issue("error", "INVALID_ALIGNMENT", location, f"未知契合度：{alignment}")
            )
        elif action not in ALIGNMENT_ACTIONS[alignment]:
            issues.append(
                Issue(
                    "error",
                    "ALIGNMENT_ACTION_MISMATCH",
                    location,
                    f"契合度 {alignment} 与处理动作 {action} 不匹配",
                )
            )
        if alignment == "none" and disposition != "drop":
            issues.append(
                Issue(
                    "error",
                    "UNUSABLE_SOURCE_RETAINED",
                    location,
                    "无推进作用的来源必须舍弃",
                )
            )
        if disposition == "drop" and action != "drop":
            issues.append(
                Issue(
                    "error",
                    "DROPPED_SOURCE_ACTION_MISMATCH",
                    location,
                    "舍弃来源时 adaptation_action 必须为 drop",
                )
            )
        if disposition == "use":
            require_fields(
                source,
                (
                    "usable_proposition",
                    "argument_task",
                    "entry_proposition",
                    "inference_gap",
                    "authored_inference",
                    "next_proposition",
                    "citation_anchor",
                ),
                location,
                issues,
            )
            if source.get("argument_task") not in ARGUMENT_TASKS:
                issues.append(
                    Issue(
                        "error",
                        "INVALID_ARGUMENT_TASK",
                        f"{location}.argument_task",
                        f"未知证据任务：{source.get('argument_task')}",
                    )
                )
            target_ids = source.get("target_paragraph_ids")
            if not isinstance(target_ids, list) or not target_ids:
                issues.append(
                    Issue(
                        "error",
                        "USED_SOURCE_WITHOUT_PARAGRAPH",
                        location,
                        "使用中的来源必须连接至少一个段落",
                    )
                )
            else:
                for paragraph_id in target_ids:
                    if paragraph_id not in paragraph_index:
                        issues.append(
                            Issue(
                                "error",
                                "BROKEN_SOURCE_PARAGRAPH",
                                f"{location}.target_paragraph_ids",
                                f"引用不存在的段落：{paragraph_id}",
                    )
                )
        adjustment = source.get("mainline_adjustment_needed")
        if adjustment not in {"none", "local", "section"}:
            issues.append(
                Issue("error", "INVALID_ADJUSTMENT", location, f"未知主线调整值：{adjustment}")
            )
        elif adjustment != "none" and not nonempty(source.get("mainline_adjustment_reason")):
            issues.append(
                Issue(
                    "error",
                    "ADJUSTMENT_WITHOUT_GAIN",
                    location,
                    "调整主线时必须记录全文收益",
                )
            )
    return source_index


def validate_cross_links(
    data: dict[str, Any],
    paragraph_index: dict[str, dict[str, Any]],
    source_index: dict[str, dict[str, Any]],
    issues: list[Issue],
) -> None:
    for paragraph_id, paragraph in paragraph_index.items():
        for source_id in paragraph.get("source_ids", []):
            if source_id not in source_index:
                issues.append(
                    Issue(
                        "error",
                        "BROKEN_PARAGRAPH_SOURCE",
                        f"paragraphs[{paragraph_id}].source_ids",
                        f"引用不存在的来源：{source_id}",
                    )
                )
            elif paragraph_id not in source_index[source_id].get("target_paragraph_ids", []):
                issues.append(
                    Issue(
                        "warning",
                        "ASYMMETRIC_PARAGRAPH_SOURCE_LINK",
                        f"paragraphs[{paragraph_id}].source_ids",
                        f"来源 {source_id} 未反向连接段落 {paragraph_id}",
                    )
                )

    bridges = list_of_objects(data, "bridges", issues)
    bridge_index = index_unique(bridges, "bridge_id", "bridges", issues)
    bridged_sources: set[str] = set()
    for bridge_id, bridge in bridge_index.items():
        location = f"bridges[{bridge_id}]"
        require_fields(
            bridge,
            (
                "from_proposition",
                "inference_gap",
                "evidence_contribution",
                "authored_inference",
                "to_proposition",
                "surface_plan",
            ),
            location,
            issues,
        )
        paragraph_id = bridge.get("paragraph_id")
        if paragraph_id not in paragraph_index:
            issues.append(
                Issue(
                    "error",
                    "BROKEN_BRIDGE_PARAGRAPH",
                    location,
                    f"引用不存在的段落：{paragraph_id}",
                )
            )
        source_ids = bridge.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            issues.append(
                Issue("error", "BRIDGE_WITHOUT_SOURCE", location, "推理桥必须连接来源")
            )
            continue
        for source_id in source_ids:
            if source_id not in source_index:
                issues.append(
                    Issue(
                        "error",
                        "BROKEN_BRIDGE_SOURCE",
                        f"{location}.source_ids",
                        f"引用不存在的来源：{source_id}",
                    )
                )
            else:
                bridged_sources.add(source_id)

    for source_id, source in source_index.items():
        if source.get("disposition") == "use" and source_id not in bridged_sources:
            issues.append(
                Issue(
                    "error",
                    "USED_SOURCE_WITHOUT_BRIDGE",
                    f"sources[{source_id}]",
                    "使用中的来源没有进入推理桥",
                )
            )


def validate_verification(
    data: dict[str, Any],
    require_verified: bool,
    issues: list[Issue],
) -> None:
    verification = data.get("verification")
    if not isinstance(verification, dict):
        issues.append(
            Issue("error", "MISSING_VERIFICATION", "verification", "缺少 verification 对象")
        )
        return
    for key, value in verification.items():
        if not isinstance(value, bool):
            issues.append(
                Issue(
                    "error",
                    "INVALID_VERIFICATION_VALUE",
                    f"verification.{key}",
                    "验证值必须是布尔值",
                )
            )
        elif require_verified and not value:
            issues.append(
                Issue(
                    "error",
                    "UNFINISHED_VERIFICATION",
                    f"verification.{key}",
                    "发布模式要求所有验证项为 true",
                )
            )


def validate(data: dict[str, Any], require_verified: bool) -> list[Issue]:
    issues: list[Issue] = []
    validate_document(data, issues)
    node_index = validate_mainline(data, issues)
    paragraph_index = validate_paragraphs(data, node_index, issues)
    source_index = validate_sources(data, paragraph_index, issues)
    validate_cross_links(data, paragraph_index, source_index, issues)
    validate_verification(data, require_verified, issues)
    return issues


def render_text(path: Path, issues: list[Issue]) -> str:
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    lines = [
        "主线—证据工作图验证",
        f"来源：{path.resolve()}",
        f"错误：{errors}；警告：{warnings}",
    ]
    if not issues:
        lines.append("通过：未发现结构或交叉引用问题。")
        return "\n".join(lines)
    for issue in issues:
        lines.append(
            f"[{issue.severity.upper()}] {issue.code} / {issue.location}: {issue.message}"
        )
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证主线—证据工作图")
    parser.add_argument("source", type=Path, help="待验证的工作图 JSON")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument(
        "--require-verified",
        action="store_true",
        help="要求 verification 中所有项目为 true",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    configure_console()
    args = parse_args(argv)
    if not args.source.is_file():
        print(f"错误：文件不存在：{args.source}", file=sys.stderr)
        return 2
    try:
        data = load_json(args.source)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    issues = validate(data, args.require_verified)
    errors = sum(issue.severity == "error" for issue in issues)
    if args.json:
        payload = {
            "status": "pass" if errors == 0 else "fail",
            "source": str(args.source.resolve()),
            "error_count": errors,
            "warning_count": sum(issue.severity == "warning" for issue in issues),
            "issues": [asdict(issue) for issue in issues],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(args.source, issues))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
