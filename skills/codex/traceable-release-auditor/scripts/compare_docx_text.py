#!/usr/bin/env python3
"""比较两份 DOCX 的可见文字，并报告高亮与引文字段概况。"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


VISIBLE_MEMBERS = re.compile(
    r"^word/(document|header\d+|footer\d+|footnotes|endnotes)\.xml$"
)
TOKEN_PATTERN = re.compile(
    r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|<w:tab(?:\s[^>]*)?/>|"
    r"<w:(?:br|cr)(?:\s[^>]*)?/>|</w:p>",
    re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比较 Clean 与标记版 DOCX 的可见文字")
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def visible_text(xml: bytes) -> str:
    decoded = xml.decode("utf-8", errors="replace")
    output: list[str] = []
    for match in TOKEN_PATTERN.finditer(decoded):
        token = match.group(0)
        if token.startswith("<w:t"):
            output.append(html.unescape(match.group(1) or ""))
        elif token.startswith("<w:tab"):
            output.append("\t")
        else:
            output.append("\n")
    return "".join(output)


def inspect(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as package:
        names = sorted(name for name in package.namelist() if VISIBLE_MEMBERS.match(name))
        if "word/document.xml" not in names:
            raise ValueError("缺少 word/document.xml")
        texts: dict[str, str] = {}
        highlights = 0
        zotero_markers = 0
        field_chars = 0
        for name in package.namelist():
            if not name.startswith("word/") or not name.endswith(".xml"):
                continue
            raw = package.read(name)
            highlights += len(re.findall(br"<w:highlight\b", raw))
            zotero_markers += raw.count(b"ZOTERO_ITEM") + raw.count(b"CSL_CITATION")
            field_chars += len(re.findall(br"<w:fldChar\b", raw))
            if name in names:
                texts[name] = visible_text(raw)
        return {
            "path": str(path.resolve()),
            "members": names,
            "texts": texts,
            "highlight_elements": highlights,
            "zotero_markers": zotero_markers,
            "field_char_elements": field_chars,
        }


def first_difference(left: str, right: str) -> dict[str, Any] | None:
    limit = min(len(left), len(right))
    index = next((i for i in range(limit) if left[i] != right[i]), limit)
    if index == len(left) == len(right):
        return None
    start = max(0, index - 80)
    return {
        "index": index,
        "first_context": left[start:index + 120],
        "second_context": right[start:index + 120],
        "first_length": len(left),
        "second_length": len(right),
    }


def main() -> int:
    args = parse_args()
    try:
        first = inspect(args.first)
        second = inspect(args.second)
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        print(f"错误：无法检查 DOCX：{exc}", file=sys.stderr)
        return 3

    findings: list[dict[str, Any]] = []
    members = sorted(set(first["members"]) | set(second["members"]))
    for member in members:
        if member not in first["texts"] or member not in second["texts"]:
            findings.append({
                "severity": "major",
                "rule_id": "DOCX-MEMBER-MISMATCH",
                "member": member,
                "message": "两份 DOCX 的可见部件集合不同",
            })
            continue
        diff = first_difference(first["texts"][member], second["texts"][member])
        if diff:
            findings.append({
                "severity": "major",
                "rule_id": "DOCX-VISIBLE-TEXT-MISMATCH",
                "member": member,
                "message": "两份 DOCX 的可见文字不同",
                "difference": diff,
            })

    if first["zotero_markers"] != second["zotero_markers"]:
        findings.append({
            "severity": "major",
            "rule_id": "DOCX-ZOTERO-MARKER-MISMATCH",
            "message": "两份 DOCX 的 Zotero/CSL 标记数量不同",
            "first": first["zotero_markers"],
            "second": second["zotero_markers"],
        })
    if first["field_char_elements"] != second["field_char_elements"]:
        findings.append({
            "severity": "major",
            "rule_id": "DOCX-FIELD-MISMATCH",
            "message": "两份 DOCX 的域字符数量不同",
            "first": first["field_char_elements"],
            "second": second["field_char_elements"],
        })

    result = {
        "comparator": "traceable-release-auditor/compare-docx-text/1.0",
        "result": "fail" if findings else "pass",
        "first": {key: value for key, value in first.items() if key != "texts"},
        "second": {key: value for key, value in second.items() if key != "texts"},
        "notice": "比较可见文字与字段概况；格式、分页和视觉效果仍需渲染检查。",
        "findings": findings,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 2 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
