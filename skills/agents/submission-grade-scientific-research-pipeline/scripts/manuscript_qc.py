#!/usr/bin/env python3
"""Run manuscript-level quality checks for submission-grade drafts."""

from __future__ import annotations

import argparse
import re
import statistics
import zipfile
from pathlib import Path


HEADING_PATTERNS = {
    "introduction": re.compile(r"^(introduction|引言)$", re.I),
    "methods": re.compile(r"^(methods?|materials and methods|材料与方法|方法)$", re.I),
    "results": re.compile(r"^(results?|结果)$", re.I),
    "discussion": re.compile(r"^(discussion|讨论)$", re.I),
    "conclusion": re.compile(r"^(conclusion|结论)$", re.I),
    "references": re.compile(r"^(references|参考文献)$", re.I),
}

BANNED_PATTERNS = [
    re.compile(r"\bdemo\b", re.I),
    re.compile(r"\bworkflow\b", re.I),
    re.compile(r"\btemplate paper\b", re.I),
    re.compile(r"\bexample manuscript\b", re.I),
    re.compile(r"\bsynthetic\b", re.I),
    re.compile(r"合成研究模式"),
    re.compile(r"示范稿"),
]

TABLE_CALLOUT = re.compile(r"\bTable\s+\d+\b", re.I)
FIGURE_CALLOUT = re.compile(r"\bFigure\s+\d+\b", re.I)
AMA_CITATION = re.compile(r"(?<!\d)(?:\[\d+(?:[-,]\d+)*\]|\b\d{1,3}(?:,\d{1,3})*\b(?=[\].,;:)]|\s))")


def extract_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    raw_paras = re.findall(r"<w:p[^>]*>(.*?)</w:p>", xml, flags=re.S)
    paras: list[str] = []
    for para in raw_paras:
        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", para, flags=re.S)
        text = "".join(texts)
        text = (
            text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            paras.append(text)
    return paras


def find_sections(paragraphs: list[str]) -> dict[str, tuple[int, int]]:
    positions: dict[str, int] = {}
    for idx, para in enumerate(paragraphs):
        for key, pattern in HEADING_PATTERNS.items():
            if key not in positions and pattern.match(para.strip()):
                positions[key] = idx
    order = ["introduction", "methods", "results", "discussion", "conclusion", "references"]
    sections: dict[str, tuple[int, int]] = {}
    for i, key in enumerate(order):
        if key not in positions:
            continue
        start = positions[key] + 1
        end = len(paragraphs)
        for next_key in order[i + 1 :]:
            if next_key in positions:
                end = positions[next_key]
                break
        sections[key] = (start, end)
    return sections


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def reference_stats(reference_paras: list[str]) -> tuple[int, int]:
    years = []
    for para in reference_paras:
        m = re.findall(r"\b(20\d{2}|19\d{2})\b", para)
        if m:
            years.append(int(m[0]))
    recent = sum(1 for y in years if y >= 2021)
    return len(reference_paras), recent


def collect_callout_numbers(pattern: re.Pattern[str], paragraphs: list[str]) -> list[int]:
    numbers: list[int] = []
    for para in paragraphs:
        for match in pattern.finditer(para):
            num = re.search(r"\d+", match.group(0))
            if num:
                numbers.append(int(num.group(0)))
    return numbers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx_path")
    args = parser.parse_args()

    path = Path(args.docx_path).resolve()
    paragraphs = extract_paragraphs(path)
    sections = find_sections(paragraphs)
    failures: list[str] = []

    required = ["introduction", "methods", "results", "discussion", "references"]
    for key in required:
        if key not in sections:
            failures.append(f"Missing required section heading: {key}")

    intro_start = sections.get("introduction", (0, 0))[0]
    discussion_end = sections.get("discussion", (0, 0))[1]
    main_text = "\n".join(paragraphs[intro_start:discussion_end]) if discussion_end > intro_start else ""
    main_words = word_count(main_text)
    if main_words and not 4500 <= main_words <= 5000:
        failures.append(f"Main text word count out of target range: {main_words}")

    if "introduction" in sections:
        is_, ie = sections["introduction"]
        intro_paras = [p for p in paragraphs[is_:ie] if p]
        if len(intro_paras) != 3:
            failures.append(f"Introduction paragraph count must be exactly 3: {len(intro_paras)}")
        elif statistics.mean([word_count(p) for p in intro_paras]) < 90:
            failures.append("Introduction paragraphs are too short for medium-length requirement")

    if "discussion" in sections:
        ds, de = sections["discussion"]
        discussion_paras = [p for p in paragraphs[ds:de] if p]
        if len(discussion_paras) != 5:
            failures.append(f"Discussion paragraph count must be exactly 5: {len(discussion_paras)}")
        avg_disc_words = statistics.mean([word_count(p) for p in discussion_paras]) if discussion_paras else 0
        if discussion_paras and avg_disc_words < 140:
            failures.append(f"Discussion paragraphs are too short on average: {avg_disc_words:.1f} words")

    if "conclusion" in sections:
        cs, ce = sections["conclusion"]
        conclusion_paras = [p for p in paragraphs[cs:ce] if p]
        if len(conclusion_paras) != 1:
            failures.append(f"Conclusion paragraph count must be exactly 1: {len(conclusion_paras)}")
        elif word_count(conclusion_paras[0]) < 90:
            failures.append("Conclusion paragraph is too short for medium-to-long requirement")

    body_paras = []
    for key in ["introduction", "methods", "results", "discussion"]:
        if key in sections:
            s, e = sections[key]
            body_paras.extend([p for p in paragraphs[s:e] if p])
    short_body_paras = sum(1 for p in body_paras if word_count(p) < 60)
    if body_paras and short_body_paras / len(body_paras) > 0.35:
        failures.append(f"Too many short body paragraphs: {short_body_paras}/{len(body_paras)}")

    if "references" in sections:
        rs, re_ = sections["references"]
        reference_paras = [p for p in paragraphs[rs:re_] if p]
        ref_count, recent_count = reference_stats(reference_paras)
        if ref_count < 30:
            failures.append(f"Reference count below target: {ref_count}")
        if ref_count and recent_count / ref_count < 0.85:
            failures.append(f"Recent reference ratio below target: {recent_count}/{ref_count}")
        doi_count = sum(1 for p in reference_paras if "doi:" in p.lower())
        if doi_count / ref_count < 0.7:
            failures.append(f"Too few references include DOI strings for verification: {doi_count}/{ref_count}")

    table_nums = sorted(set(collect_callout_numbers(TABLE_CALLOUT, paragraphs)))
    figure_nums = sorted(set(collect_callout_numbers(FIGURE_CALLOUT, paragraphs)))
    if not table_nums:
        failures.append("No numbered table callouts found in manuscript body")
    if not figure_nums:
        failures.append("No numbered figure callouts found in manuscript body")
    if table_nums and table_nums != list(range(1, max(table_nums) + 1)):
        failures.append(f"Table numbering is not sequential: {table_nums}")
    if figure_nums and figure_nums != list(range(1, max(figure_nums) + 1)):
        failures.append(f"Figure numbering is not sequential: {figure_nums}")

    for section_name in ["introduction", "discussion"]:
        if section_name in sections:
            s, e = sections[section_name]
            section_text = "\n".join(paragraphs[s:e])
            if not AMA_CITATION.search(section_text):
                failures.append(f"No in-text numbered citations detected in {section_name}")

    full_text = "\n".join(paragraphs)
    for pattern in BANNED_PATTERNS:
        if pattern.search(full_text):
            failures.append(f"Banned manuscript wording detected: {pattern.pattern}")

    print(f"Document: {path}")
    print(f"Paragraphs: {len(paragraphs)}")
    print(f"Main text words: {main_words}")
    if failures:
        print("QC FAILED")
        for item in failures:
            print(f"- {item}")
        return 1

    print("QC PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
