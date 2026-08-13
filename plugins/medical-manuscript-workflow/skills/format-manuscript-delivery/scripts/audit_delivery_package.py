from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from lxml import etree

from docx_utils import (
    NS,
    format_parts,
    list_all_files,
    package_plain_text,
    parse_xml,
    qn,
    read_package,
)


ALLOWED_ROLES = {
    "figure",
    "table",
    "supplementary_figure",
    "supplementary_table",
    "supplementary_material",
    "submission_checklist",
}

ROLE_SUFFIXES = {
    "manuscript": {".docx"},
    "figure": {".png"},
    "table": {".docx", ".xlsx"},
    "supplementary_figure": {".png"},
    "supplementary_table": {".docx", ".xlsx"},
    "supplementary_material": {".docx", ".xlsx", ".pdf", ".csv", ".png"},
    "submission_checklist": {".docx", ".pdf", ".xlsx"},
}

PROCESS_PATTERNS = [
    (r"\bCodex\b", "Codex 痕迹"),
    (r"\bChatGPT\b", "ChatGPT 痕迹"),
    (r"\bAI[- ]?generated\b|AI生成", "AI 生成说明"),
    (r"模型思考过程|模型推理过程|内部推理", "模型过程"),
    (r"根据用户要求|用户让我|与用户讨论", "用户讨论过程"),
    (r"工作记录|内部清单|内部审计|审计报告", "内部工作材料"),
    (r"\bTODO\b|待办事项|占位符", "待办或占位符"),
    (r"文件状态\s*[:：]|本稿基于现有|供后续模型", "过程性文件说明"),
]

REVIEW_PATTERNS = [
    (r"本稿", "“本稿”需确认是否属于过程性说明"),
    (r"本文件", "“本文件”需确认是否属于过程性说明"),
    (r"证据边界|证据仍有限|目前证据有限", "需确认是否属于无正式用途的证据边界说明"),
    (r"尚不能说明|仍需更多研究|仍待进一步验证", "需确认是否属于习惯性保留或自我保护式表述"),
]

INTERNAL_FILENAME = re.compile(
    r"(?:^|[-_.\s])(index|audit|report|log|working|worklog|backup|draft|archive)(?:$|[-_.\s])"
    r"|内部|工作记录|审计报告|文件目录说明",
    flags=re.I,
)


def add_issue(
    issues: list[dict],
    severity: str,
    code: str,
    message: str,
    location: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "location": location,
        }
    )


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_registered_path(root: Path, relative: str) -> Path:
    raw = Path(relative)
    if raw.is_absolute():
        raise ValueError(f"Manifest path must be relative: {relative}")
    resolved = (root / raw).resolve()
    if not is_relative_to(resolved, root.resolve()):
        raise ValueError(f"Manifest path escapes delivery directory: {relative}")
    return resolved


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema_version") != 1:
        raise ValueError("Manifest schema_version must be 1.")
    if not isinstance(data.get("manuscript"), str) or not data["manuscript"]:
        raise ValueError("Manifest must declare manuscript.")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("Manifest artifacts must be an array.")
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            raise ValueError(f"Artifact {index} must be an object.")
        missing = {"role", "label", "path"}.difference(artifact)
        if missing:
            raise ValueError(f"Artifact {index} missing {sorted(missing)}.")
        if artifact["role"] not in ALLOWED_ROLES:
            raise ValueError(
                f"Artifact {index} has unsupported role: {artifact['role']}"
            )
    return data


def inspect_docx(
    path: Path, relative: str, issues: list[dict]
) -> str:
    package = read_package(path)
    if "word/comments.xml" in package:
        root = parse_xml(package["word/comments.xml"])
        comments = root.xpath(".//w:comment", namespaces=NS)
        if comments:
            add_issue(
                issues,
                "error",
                "COMMENTS_PRESENT",
                f"正式 DOCX 含 {len(comments)} 条批注。",
                relative,
            )

    tracked = 0
    hidden = 0
    for part in format_parts(package):
        root = parse_xml(package[part])
        tracked += len(
            root.xpath(
                ".//w:ins | .//w:del | .//w:moveFrom | .//w:moveTo",
                namespaces=NS,
            )
        )
        hidden += len(root.xpath(".//w:vanish", namespaces=NS))
    if tracked:
        add_issue(
            issues,
            "error",
            "TRACKED_CHANGES_PRESENT",
            f"正式 DOCX 含 {tracked} 处修订对象。",
            relative,
        )
    if hidden:
        add_issue(
            issues,
            "error",
            "HIDDEN_TEXT_PRESENT",
            f"正式 DOCX 含 {hidden} 处隐藏文字。",
            relative,
        )

    text = package_plain_text(package)
    for pattern, label in PROCESS_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            add_issue(
                issues,
                "error",
                "PROCESS_CONTENT",
                f"检测到{label}。",
                relative,
            )
    for pattern, label in REVIEW_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            add_issue(
                issues,
                "warning",
                "PROCESS_CONTENT_REVIEW",
                label,
                relative,
            )
    return text


def label_pattern(label: str) -> re.Pattern[str]:
    pieces = [re.escape(piece) for piece in label.split()]
    return re.compile(r"\s*".join(pieces), flags=re.I)


def label_number(label: str) -> tuple[str, int] | None:
    normalized = label.strip()
    match = re.match(
        r"^(Figure|Table)\s+(S?)(\d+)$", normalized, flags=re.I
    )
    if not match:
        return None
    prefix = match.group(1).casefold()
    supplementary = bool(match.group(2))
    group = f"{prefix}_{'supplementary' if supplementary else 'main'}"
    return group, int(match.group(3))


def check_labels(
    manuscript_text: str, artifacts: list[dict], issues: list[dict]
) -> None:
    groups: dict[str, list[tuple[int, int, str]]] = {}
    for artifact in artifacts:
        if artifact["role"] not in {
            "figure",
            "table",
            "supplementary_figure",
            "supplementary_table",
        }:
            continue
        label = artifact["label"]
        match = label_pattern(label).search(manuscript_text)
        if not match:
            add_issue(
                issues,
                "error",
                "CALLOUT_MISSING",
                "正文未检测到对应图表引用。",
                label,
            )
            position = 10**12
        else:
            position = match.start()
        parsed = label_number(label)
        if parsed:
            group, number = parsed
            groups.setdefault(group, []).append((number, position, label))
        else:
            add_issue(
                issues,
                "warning",
                "NONSTANDARD_LABEL",
                "图表标签无法自动验证顺序，需人工确认。",
                label,
            )

    for group, entries in groups.items():
        numbers = sorted(number for number, _, _ in entries)
        expected = list(range(1, len(entries) + 1))
        if numbers != expected:
            add_issue(
                issues,
                "error",
                "NUMBER_SEQUENCE",
                f"{group} 编号应连续从 1 开始。",
                ", ".join(label for _, _, label in entries),
            )
        by_number = sorted(entries)
        positions = [position for _, position, _ in by_number]
        if positions != sorted(positions):
            add_issue(
                issues,
                "error",
                "FIRST_APPEARANCE_ORDER",
                f"{group} 编号顺序与正文首次出现顺序不一致。",
                ", ".join(label for _, _, label in by_number),
            )


def audit(delivery_dir: Path, manifest_path: Path) -> dict:
    if not delivery_dir.is_dir():
        raise NotADirectoryError(delivery_dir)
    root = delivery_dir.resolve()
    manifest_resolved = manifest_path.resolve()
    if is_relative_to(manifest_resolved, root):
        raise ValueError("delivery-manifest.json must be outside delivery directory.")
    manifest = load_manifest(manifest_path)
    issues: list[dict] = []

    registered: dict[str, str] = {}
    manuscript_relative = manifest["manuscript"].replace("\\", "/")
    registered[manuscript_relative] = "manuscript"
    for artifact in manifest["artifacts"]:
        relative = artifact["path"].replace("\\", "/")
        if relative in registered:
            add_issue(
                issues,
                "error",
                "DUPLICATE_MANIFEST_PATH",
                "同一文件被重复登记。",
                relative,
            )
        registered[relative] = artifact["role"]

    actual_paths = list_all_files(root)
    actual = {
        path.relative_to(root).as_posix(): path for path in actual_paths
    }

    for relative, role in registered.items():
        try:
            resolved = resolve_registered_path(root, relative)
        except ValueError as exc:
            add_issue(
                issues,
                "error",
                "MANIFEST_PATH",
                str(exc),
                relative,
            )
            continue
        if not resolved.is_file():
            add_issue(
                issues,
                "error",
                "REGISTERED_FILE_MISSING",
                "登记文件不存在。",
                relative,
            )
            continue
        suffix = resolved.suffix.lower()
        if suffix not in ROLE_SUFFIXES[role]:
            add_issue(
                issues,
                "error",
                "ROLE_FILE_TYPE",
                f"{role} 不允许使用 {suffix or '无扩展名'}。",
                relative,
            )
        if INTERNAL_FILENAME.search(resolved.name):
            add_issue(
                issues,
                "error",
                "INTERNAL_FILENAME",
                "文件名显示内部、审计、草稿或工作记录属性。",
                relative,
            )

    for relative in actual:
        if relative not in registered:
            add_issue(
                issues,
                "error",
                "UNREGISTERED_FILE",
                "正式目录含未登记文件。",
                relative,
            )

    manuscript_path = root / manuscript_relative
    manuscript_text = ""
    for relative, role in registered.items():
        path = root / relative
        if path.is_file() and path.suffix.lower() == ".docx":
            text = inspect_docx(path, relative, issues)
            if role == "manuscript":
                manuscript_text = text

    if manuscript_text:
        check_labels(manuscript_text, manifest["artifacts"], issues)

    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    return {
        "status": "pass" if errors == 0 else "fail",
        "delivery_directory": str(root),
        "manifest": str(manifest_resolved),
        "counts": {
            "registered_files": len(registered),
            "actual_files": len(actual),
            "errors": errors,
            "warnings": warnings,
        },
        "issues": issues,
        "manual_review_required": [
            "sentence-by-sentence submission suitability, section fit and placement",
            "alignment with the user-specified thesis and manuscript throughline",
            "defensive caveats and nonfunctional evidence-boundary statements",
            "semantic review of process-content warnings",
            "visual review of every final file",
            "checklist completion in the original template",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a formal delivery package.")
    parser.add_argument("delivery_directory", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        if args.json_out and is_relative_to(
            args.json_out.resolve(), args.delivery_directory.resolve()
        ):
            raise ValueError("Audit report must be outside delivery directory.")
        report = audit(args.delivery_directory, args.manifest)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
