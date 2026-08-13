#!/usr/bin/env python3
"""对正式交付目录执行确定性边界预筛查。

脚本只生成候选发现；语义风险必须由使用者结合上下文复核。
"""

from __future__ import annotations

import argparse
import fnmatch
import html
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_POLICY: dict[str, Any] = {
    "allow_globs": [],
    "deny_name_tokens": [
        "internal", "draft", "backup", "temp", "notes", "handoff", "audit",
        "delivery_index", "source_pack", "worklog", "qc_report",
        "批注", "草稿", "备份", "临时", "笔记", "思考过程", "工作记录",
        "过程文件", "内部报告", "审计报告", "核查报告", "交付说明",
        "提交说明", "操作清单", "内部索引", "证据映射",
    ],
    "content_review_patterns": [
        "TODO", "FIXME", "待确认", "待补充", "待完善", "待专家确认",
        "内部讨论", "AI生成", "模型生成", "根据批注", "根据反馈",
        "专家批注意见", "文件状态", "本稿", "本文件", "前九条",
        "第十条规定", "表决前预评估", "正式发布前", "本轮修改",
        "本次修改", "修改说明", "编辑说明", "已完成以下",
    ],
    "allowed_exceptions": [],
    "scan_docx_internals": True,
    "scan_pptx_internals": True,
    "scan_xlsx_internals": True,
    "scan_pdf_internals": True,
    "default_export_allowed": False,
}

TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".tsv", ".json", ".yaml", ".yml",
    ".xml", ".html", ".htm", ".rtf",
}
TEMP_SUFFIXES = {".tmp", ".bak", ".old", ".swp"}
SEVERITY = {"info": 0, "review": 1, "block": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描正式交付包中的边界风险")
    parser.add_argument("target", type=Path, help="待扫描的文件或目录")
    parser.add_argument("--policy", type=Path, help="JSON 策略文件")
    parser.add_argument("--json-out", type=Path, help="JSON 报告输出位置；应位于交付目录之外")
    parser.add_argument(
        "--fail-on", choices=("none", "review", "block"), default="block",
        help="达到指定等级时返回非零状态；默认 block",
    )
    return parser.parse_args()


def load_policy(path: Path | None) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    if path:
        with path.open("r", encoding="utf-8-sig") as handle:
            supplied = json.load(handle)
        if not isinstance(supplied, dict):
            raise ValueError("策略文件顶层必须是 JSON 对象")
        policy.update(supplied)
    return policy


def iter_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return
    for path in sorted(target.rglob("*")):
        if path.is_file():
            yield path


def relative_text(path: Path, target: Path) -> str:
    base = target if target.is_dir() else target.parent
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return str(path)


def matches_glob(rel: str, pattern: str) -> bool:
    return fnmatch.fnmatch(rel, pattern) or (
        pattern.startswith("**/") and fnmatch.fnmatch(rel, pattern[3:])
    )


def is_excepted(rel: str, policy: dict[str, Any]) -> bool:
    return any(matches_glob(rel, pattern) for pattern in policy.get("allowed_exceptions", []))


def add_finding(
    findings: list[dict[str, Any]], rel: str, rule_id: str, severity: str,
    message: str, evidence: str = "",
) -> None:
    findings.append({
        "artifact": rel,
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "evidence": evidence[:500],
        "status": "open",
    })


def scan_name(path: Path, rel: str, policy: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    lower = path.name.casefold()
    if path.name.startswith("~$") or path.suffix.casefold() in TEMP_SUFFIXES:
        add_finding(findings, rel, "FS-TEMP", "block", "发现临时、锁定或备份文件", path.name)
    for token in policy.get("deny_name_tokens", []):
        if str(token).casefold() in lower:
            add_finding(
                findings, rel, "FS-NAME-REVIEW", "review",
                "文件名包含通常用于内部材料的标记，需要确认文件身份", str(token),
            )
            break
    allow_globs = policy.get("allow_globs", [])
    if allow_globs and not any(matches_glob(rel, pattern) for pattern in allow_globs):
        add_finding(findings, rel, "FS-NOT-ALLOWLISTED", "review", "文件不匹配发布允许模式", rel)


def decode_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "gb18030", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def scan_content_patterns(
    text: str, rel: str, policy: dict[str, Any], findings: list[dict[str, Any]], source: str,
) -> None:
    folded = text.casefold()
    for pattern in policy.get("content_review_patterns", []):
        needle = str(pattern).casefold()
        if needle and needle in folded:
            index = folded.find(needle)
            start = max(0, index - 80)
            end = min(len(text), index + len(str(pattern)) + 120)
            excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
            add_finding(
                findings, rel, "CONTENT-CONTEXT-REVIEW", "review",
                f"{source}命中需结合上下文判断的候选表达", excerpt,
            )


def extract_ooxml_text(xml: bytes) -> str:
    decoded = xml.decode("utf-8", errors="replace")
    parts = re.findall(
        r"<(?:[A-Za-z0-9_]+:)?t(?:\s[^>]*)?>(.*?)</(?:[A-Za-z0-9_]+:)?t>",
        decoded,
        flags=re.DOTALL,
    )
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", part)) for part in parts)


def scan_docx(path: Path, rel: str, policy: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    try:
        with zipfile.ZipFile(path) as package:
            names = set(package.namelist())
            comment_members = {
                "word/comments.xml", "word/commentsExtended.xml", "word/commentsExtensible.xml",
            }
            present_comments = sorted(comment_members.intersection(names))
            if present_comments:
                add_finding(
                    findings, rel, "DOCX-COMMENTS", "block",
                    "DOCX 包含批注结构", ", ".join(present_comments),
                )
            if "word/document.xml" not in names:
                add_finding(findings, rel, "DOCX-NO-DOCUMENT", "block", "DOCX 缺少主文档 XML")
                return
            xml = package.read("word/document.xml")
            tracked = [tag for tag in (b"<w:ins", b"<w:del", b"<w:moveFrom", b"<w:moveTo") if tag in xml]
            if tracked:
                add_finding(
                    findings, rel, "DOCX-TRACKED-CHANGES", "block",
                    "DOCX 包含修订标记", ", ".join(tag.decode("ascii") for tag in tracked),
                )
            if b"<w:vanish" in xml or b"<w:webHidden" in xml:
                add_finding(findings, rel, "DOCX-HIDDEN-TEXT", "block", "DOCX 包含隐藏文字属性")
            if "docProps/custom.xml" in names:
                add_finding(
                    findings, rel, "DOCX-CUSTOM-PROPS", "review",
                    "DOCX 包含自定义属性，需要确认是否含内部元数据",
                )
            scan_content_patterns(extract_ooxml_text(xml), rel, policy, findings, "DOCX 正文")
    except (zipfile.BadZipFile, OSError) as exc:
        add_finding(findings, rel, "DOCX-INVALID", "block", "DOCX 无法作为有效压缩包读取", str(exc))


def scan_pptx(path: Path, rel: str, policy: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    try:
        with zipfile.ZipFile(path) as package:
            names = set(package.namelist())
            comments = sorted(
                name for name in names
                if name.startswith("ppt/comments/") or name.startswith("ppt/threadedComments/")
            )
            if comments:
                add_finding(
                    findings, rel, "PPTX-COMMENTS", "block",
                    "PPTX 包含批注或线程评论", ", ".join(comments[:10]),
                )
            notes = sorted(name for name in names if name.startswith("ppt/notesSlides/notesSlide"))
            if notes:
                add_finding(
                    findings, rel, "PPTX-NOTES", "review",
                    "PPTX 包含演讲者备注，需要确认是否为正式讲稿", f"{len(notes)} 个备注页",
                )
            presentation = package.read("ppt/presentation.xml") if "ppt/presentation.xml" in names else b""
            if re.search(rb'\bshow="(?:0|false)"', presentation, flags=re.IGNORECASE):
                add_finding(findings, rel, "PPTX-HIDDEN-SLIDES", "review", "PPTX 包含隐藏幻灯片")
            for member in sorted(names):
                if member.startswith("ppt/slides/slide") and member.endswith(".xml"):
                    scan_content_patterns(
                        extract_ooxml_text(package.read(member)),
                        rel, policy, findings, f"PPTX 页面 {member}",
                    )
                elif member.startswith("ppt/notesSlides/notesSlide") and member.endswith(".xml"):
                    scan_content_patterns(
                        extract_ooxml_text(package.read(member)),
                        rel, policy, findings, f"PPTX 备注 {member}",
                    )
    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        add_finding(findings, rel, "PPTX-INVALID", "block", "PPTX 无法作为有效压缩包读取", str(exc))


def scan_xlsx(path: Path, rel: str, policy: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    try:
        with zipfile.ZipFile(path) as package:
            names = set(package.namelist())
            comments = sorted(
                name for name in names
                if name.startswith("xl/comments") or name.startswith("xl/threadedComments/")
            )
            if comments:
                add_finding(
                    findings, rel, "XLSX-COMMENTS", "block",
                    "XLSX 包含批注或线程评论", ", ".join(comments[:10]),
                )
            workbook = package.read("xl/workbook.xml") if "xl/workbook.xml" in names else b""
            hidden = re.findall(rb'\bstate="(hidden|veryHidden)"', workbook, flags=re.IGNORECASE)
            if hidden:
                add_finding(
                    findings, rel, "XLSX-HIDDEN-SHEETS", "review",
                    "XLSX 包含隐藏工作表，需要确认是否含内部计算或过程内容",
                    f"{len(hidden)} 个隐藏状态",
                )
            external_links = sorted(name for name in names if name.startswith("xl/externalLinks/"))
            if external_links:
                add_finding(
                    findings, rel, "XLSX-EXTERNAL-LINKS", "review",
                    "XLSX 包含外部链接，需要确认可用性和信息边界",
                    ", ".join(external_links[:10]),
                )
            for member in sorted(names):
                if member == "xl/sharedStrings.xml" or (
                    member.startswith("xl/worksheets/sheet") and member.endswith(".xml")
                ):
                    scan_content_patterns(
                        extract_ooxml_text(package.read(member)),
                        rel, policy, findings, f"XLSX 内容 {member}",
                    )
    except (zipfile.BadZipFile, OSError, KeyError) as exc:
        add_finding(findings, rel, "XLSX-INVALID", "block", "XLSX 无法作为有效压缩包读取", str(exc))


def scan_pdf(path: Path, rel: str, policy: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        add_finding(findings, rel, "PDF-READ", "block", "PDF 无法读取", str(exc))
        return
    if not raw.startswith(b"%PDF-"):
        add_finding(findings, rel, "PDF-INVALID", "block", "文件缺少 PDF 头标记")
        return
    for marker, rule, message in (
        (b"/Annots", "PDF-ANNOTATIONS", "PDF 可能包含注释或批注"),
        (b"/EmbeddedFiles", "PDF-EMBEDDED-FILES", "PDF 可能包含嵌入附件"),
        (b"/OCProperties", "PDF-LAYERS", "PDF 可能包含可选图层或隐藏内容"),
    ):
        if marker in raw:
            add_finding(findings, rel, rule, "review", message, marker.decode("ascii"))
    if b"/JavaScript" in raw or b"/JS" in raw:
        add_finding(findings, rel, "PDF-JAVASCRIPT", "block", "PDF 包含 JavaScript 动作")
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        scan_content_patterns(text, rel, policy, findings, "PDF 可提取正文")
        metadata = reader.metadata or {}
        metadata_text = " ".join(str(value) for value in metadata.values() if value)
        scan_content_patterns(metadata_text, rel, policy, findings, "PDF 元数据")
    except ImportError:
        add_finding(
            findings, rel, "PDF-TEXT-NOT-SCANNED", "info",
            "未安装 pypdf，已完成 PDF 结构预筛查，正文仍需语义复核",
        )
    except Exception as exc:  # pypdf raises several parser-specific exceptions
        add_finding(findings, rel, "PDF-TEXT-READ", "review", "PDF 正文提取失败，需要人工复核", str(exc))


def scan_zip(path: Path, rel: str, policy: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    try:
        with zipfile.ZipFile(path) as package:
            for member in package.namelist():
                lowered = member.casefold()
                if member.split("/")[-1].startswith("~$") or any(
                    str(token).casefold() in lowered for token in policy.get("deny_name_tokens", [])
                ):
                    add_finding(
                        findings, rel, "ZIP-MEMBER-REVIEW", "review",
                        "压缩包成员名称提示可能存在内部或临时材料", member,
                    )
    except (zipfile.BadZipFile, OSError) as exc:
        add_finding(findings, rel, "ZIP-INVALID", "block", "压缩包无法读取", str(exc))


def main() -> int:
    args = parse_args()
    target = args.target.resolve()
    if not target.exists():
        print(f"错误：目标不存在：{target}", file=sys.stderr)
        return 3
    json_out = args.json_out.resolve() if args.json_out else None
    if target.is_dir() and json_out and json_out.is_relative_to(target):
        print("错误：扫描报告必须位于交付目录之外", file=sys.stderr)
        return 3
    try:
        policy = load_policy(args.policy.resolve() if args.policy else None)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"错误：无法读取策略：{exc}", file=sys.stderr)
        return 3

    findings: list[dict[str, Any]] = []
    scanned = 0
    for path in iter_files(target):
        scanned += 1
        rel = relative_text(path, target)
        if is_excepted(rel, policy):
            continue
        scan_name(path, rel, policy, findings)
        suffix = path.suffix.casefold()
        if suffix in TEXT_EXTENSIONS:
            try:
                scan_content_patterns(decode_text(path.read_bytes()), rel, policy, findings, "文本")
            except OSError as exc:
                add_finding(findings, rel, "FILE-READ", "review", "文件无法读取", str(exc))
        elif suffix == ".docx" and policy.get("scan_docx_internals", True):
            scan_docx(path, rel, policy, findings)
        elif suffix == ".pptx" and policy.get("scan_pptx_internals", True):
            scan_pptx(path, rel, policy, findings)
        elif suffix == ".xlsx" and policy.get("scan_xlsx_internals", True):
            scan_xlsx(path, rel, policy, findings)
        elif suffix == ".pdf" and policy.get("scan_pdf_internals", True):
            scan_pdf(path, rel, policy, findings)
        elif suffix == ".zip":
            scan_zip(path, rel, policy, findings)

    counts = Counter(item["severity"] for item in findings)
    report = {
        "scanner": "formal-deliverable-boundary-guard/2.0",
        "target": str(target),
        "files_scanned": scanned,
        "summary": {key: counts.get(key, 0) for key in ("block", "review", "info")},
        "notice": "关键词和结构命中只形成候选发现；语境风险必须人工或语义复核。",
        "findings": findings,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(rendered, encoding="utf-8")
    print(rendered)

    if args.fail_on == "none":
        return 0
    threshold = SEVERITY[args.fail_on]
    return 2 if any(SEVERITY[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
