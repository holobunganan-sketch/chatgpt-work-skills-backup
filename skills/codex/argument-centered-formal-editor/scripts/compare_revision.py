#!/usr/bin/env python3
"""比较原文与修订稿的数字、引用对象和候选写作风险。

该脚本帮助发现事实标识丢失、引用对象变化、来源主导结构未改善和新增防御性表达。
结果只用于人工复核。
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

from scan_argument_flow_risks import (
    CITATION_PATTERN,
    load_source,
    risk_counts,
    split_paragraphs,
    split_sentences,
)


NUMBER_PATTERN = re.compile(
    r"(?<![\w])(?:\d+(?:\.\d+)?%?|\d+(?:\.\d+)?\s*(?:倍|例|人|项|年|月|周|天|小时|元)|p\s*[<=>]\s*0?\.\d+)(?![\w])",
    re.IGNORECASE,
)


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_numbers(text: str) -> Counter[str]:
    return Counter(normalize_space(item) for item in NUMBER_PATTERN.findall(text))


def extract_citations(text: str) -> Counter[str]:
    items: list[str] = []
    for match in CITATION_PATTERN.finditer(text):
        raw = re.sub(r"\s+", "", match.group(0)).strip()
        if raw.startswith("[") and raw.endswith("]") and "@" in raw:
            items.extend(
                f"@{key}"
                for key in re.findall(r"@([A-Za-z0-9_:.+\-]+)", raw)
            )
            continue
        if raw.startswith("\\"):
            brace_match = re.search(r"\{([^}]+)\}", raw)
            if brace_match:
                items.extend(
                    f"@{key.strip()}"
                    for key in brace_match.group(1).split(",")
                    if key.strip()
                )
            continue
        if raw.startswith("[") and raw.endswith("]"):
            body = raw[1:-1]
            for part in re.split(r"[,;，；]", body):
                range_match = re.fullmatch(r"(\d+)[\-–—](\d+)", part)
                if range_match:
                    start, end = map(int, range_match.groups())
                    if start <= end and end - start <= 200:
                        items.extend(str(number) for number in range(start, end + 1))
                        continue
                if part.isdigit():
                    items.append(part)
            continue
        item = raw.strip("[]() ,.;，。；").lower()
        if item:
            items.append(item)
    return Counter(items)


def extract_citation_objects(text: str) -> Counter[str]:
    return Counter(normalize_space(match.group(0)) for match in CITATION_PATTERN.finditer(text))


def counter_delta(before: Counter[str], after: Counter[str]) -> tuple[list[str], list[str]]:
    missing = list((before - after).elements())
    added = list((after - before).elements())
    return sorted(missing), sorted(added)


def structural_stats(text: str) -> dict[str, int]:
    paragraphs = split_paragraphs(text)
    return {
        "characters": len(re.sub(r"\s+", "", text)),
        "paragraphs": len(paragraphs),
        "sentences": sum(len(split_sentences(paragraph)) for paragraph in paragraphs),
    }


def compare(original_text: str, revised_text: str) -> dict:
    original_numbers = extract_numbers(original_text)
    revised_numbers = extract_numbers(revised_text)
    missing_numbers, added_numbers = counter_delta(original_numbers, revised_numbers)
    original_citations = extract_citations(original_text)
    revised_citations = extract_citations(revised_text)
    missing_citations, added_citations = counter_delta(original_citations, revised_citations)
    original_citation_objects = extract_citation_objects(original_text)
    revised_citation_objects = extract_citation_objects(revised_text)
    missing_citation_objects, added_citation_objects = counter_delta(
        original_citation_objects,
        revised_citation_objects,
    )

    before_risks = risk_counts(original_text)
    after_risks = risk_counts(revised_text)
    risk_ids = sorted(set(before_risks) | set(after_risks))
    risk_delta = {
        risk_id: {
            "before": before_risks.get(risk_id, 0),
            "after": after_risks.get(risk_id, 0),
            "change": after_risks.get(risk_id, 0) - before_risks.get(risk_id, 0),
        }
        for risk_id in risk_ids
    }

    similarity = difflib.SequenceMatcher(
        None,
        normalize_space(original_text),
        normalize_space(revised_text),
        autojunk=False,
    ).ratio()

    review_flags: list[dict[str, str]] = []
    if missing_numbers:
        review_flags.append(
            {
                "code": "MISSING_NUMBERS",
                "message": f"修订稿缺少原文数值：{', '.join(missing_numbers)}",
            }
        )
    if added_numbers:
        review_flags.append(
            {
                "code": "ADDED_NUMBERS",
                "message": f"修订稿新增数值：{', '.join(added_numbers)}",
            }
        )
    if missing_citations:
        review_flags.append(
            {
                "code": "MISSING_CITATIONS",
                "message": f"修订稿缺少原文引用标识：{', '.join(missing_citations)}",
            }
        )
    if added_citations:
        review_flags.append(
            {
                "code": "ADDED_CITATIONS",
                "message": f"修订稿新增引用标识：{', '.join(added_citations)}",
            }
        )
    if missing_citation_objects or added_citation_objects:
        review_flags.append(
            {
                "code": "CHANGED_CITATION_OBJECTS",
                "message": "修订前后的完整引用对象发生变化；需要检查 citation key、组合关系、页码、命令参数或动态引文。",
            }
        )

    for risk_id in (
        "SOURCE_LED_SEQUENCE",
        "EVIDENCE_WITHOUT_RELATION",
        "ABSTRACT_DENSITY",
        "ABSTRACT_PARAGRAPH",
        "GENERIC_VALUE_CLAIM",
        "DEFENSIVE_PROSE",
        "FORBIDDEN_TURN_TEMPLATE",
        "PROCESS_TRACE",
    ):
        if after_risks.get(risk_id, 0) > before_risks.get(risk_id, 0):
            review_flags.append(
                {
                    "code": f"RISK_INCREASE_{risk_id}",
                    "message": f"{risk_id} 候选从 {before_risks.get(risk_id, 0)} 增至 {after_risks.get(risk_id, 0)}",
                }
            )

    unresolved_core_risks = sum(
        after_risks.get(risk_id, 0)
        for risk_id in ("SOURCE_LED_SEQUENCE", "EVIDENCE_WITHOUT_RELATION")
    )
    if similarity >= 0.92 and unresolved_core_risks:
        review_flags.append(
            {
                "code": "HIGH_SIMILARITY_WITH_UNRESOLVED_STRUCTURE",
                "message": "修订幅度较小，来源主导或证据关系候选仍然存在；需要检查编辑深度。",
            }
        )

    return {
        "status": "review_candidates",
        "similarity_ratio": round(similarity, 4),
        "original": structural_stats(original_text),
        "revised": structural_stats(revised_text),
        "numbers": {
            "missing": missing_numbers,
            "added": added_numbers,
        },
        "citations": {
            "missing": missing_citations,
            "added": added_citations,
        },
        "citation_objects": {
            "missing": missing_citation_objects,
            "added": added_citation_objects,
        },
        "risk_delta": risk_delta,
        "review_flags": review_flags,
    }


def render_text(payload: dict, original: Path, revised: Path) -> str:
    lines = [
        "修订前后结构比较",
        f"原文：{original.resolve()}",
        f"修订稿：{revised.resolve()}",
        f"文本相似度：{payload['similarity_ratio']:.4f}",
        f"原文段落/句子：{payload['original']['paragraphs']}/{payload['original']['sentences']}",
        f"修订稿段落/句子：{payload['revised']['paragraphs']}/{payload['revised']['sentences']}",
    ]
    if payload["review_flags"]:
        lines.append("复核候选：")
        for flag in payload["review_flags"]:
            lines.append(f"- {flag['code']}: {flag['message']}")
    else:
        lines.append("当前规则未发现新增数值、引用或核心结构风险。")
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比较原文与修订稿")
    parser.add_argument("original", type=Path, help="原文")
    parser.add_argument("revised", type=Path, help="修订稿")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    configure_console()
    args = parse_args(argv)
    for path in (args.original, args.revised):
        if not path.is_file():
            print(f"错误：文件不存在：{path}", file=sys.stderr)
            return 2
    try:
        original_text, _ = load_source(args.original)
        revised_text, _ = load_source(args.revised)
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    payload = compare(original_text, revised_text)
    print(
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else render_text(payload, args.original, args.revised)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
