#!/usr/bin/env python3
"""Lightweight validator for reflowable Kindle-oriented HTML."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class KindleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.script_count = 0
        self.iframe_count = 0
        self.tables: list[int] = []
        self._in_table = False
        self._row_cols = 0
        self._table_max_cols = 0
        self.headings: list[int] = []
        self.images_missing_alt = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        attrs_dict = {k.lower(): v for k, v in attrs}
        if tag == "script":
            self.script_count += 1
        elif tag == "iframe":
            self.iframe_count += 1
        elif tag == "table":
            self._in_table = True
            self._table_max_cols = 0
        elif tag == "tr" and self._in_table:
            self._row_cols = 0
        elif tag in {"td", "th"} and self._in_table:
            self._row_cols += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        elif tag == "img":
            alt = attrs_dict.get("alt")
            if alt is None or not alt.strip():
                self.images_missing_alt += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "tr" and self._in_table:
            self._table_max_cols = max(self._table_max_cols, self._row_cols)
        elif tag == "table" and self._in_table:
            self.tables.append(self._table_max_cols)
            self._in_table = False


def add_issue(issues: list[tuple[str, str]], level: str, message: str) -> None:
    issues.append((level, message))


def validate(text: str, allow_wide_tables: bool = False) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    lower = text.lower()

    parser = KindleHTMLParser()
    parser.feed(text)

    if parser.script_count:
        add_issue(issues, "ERROR", "script element detected; Kindle reading documents must not depend on scripts")
    if parser.iframe_count:
        add_issue(issues, "ERROR", "iframe detected; embedded web frames are not Kindle-safe")

    css_checks = [
        (r"position\s*:\s*fixed\b", "ERROR", "position: fixed detected; fixed UI is incompatible with linear Kindle reading"),
        (r"position\s*:\s*sticky\b", "ERROR", "position: sticky detected; sticky UI is incompatible with linear Kindle reading"),
        (r"display\s*:\s*grid\b|grid-template-", "ERROR", "CSS Grid detected; use single-column document flow"),
        (r"(?:^|[;{\s])width\s*:\s*\d+(?:\.\d+)?px\b", "ERROR", "fixed pixel width detected; use relative width, %, em, or max-width: 100%"),
        (r"(?:^|[;{\s])height\s*:\s*\d+(?:\.\d+)?px\b", "WARN", "fixed pixel height detected; verify it cannot clip after text reflow"),
        (r"columns?\s*:|column-count\s*:", "ERROR", "multi-column CSS detected; use a single-column reading flow"),
        (r"overflow-x\s*:\s*(?:auto|scroll)\b", "WARN", "horizontal scrolling detected; Kindle content should fit the viewport"),
        (r"display\s*:\s*flex\b", "WARN", "Flexbox detected; review carefully and avoid multi-column or side-by-side reading layouts"),
    ]
    for pattern, level, message in css_checks:
        if re.search(pattern, lower, flags=re.MULTILINE):
            add_issue(issues, level, message)

    for index, cols in enumerate(parser.tables, start=1):
        if cols > 3:
            level = "WARN" if allow_wide_tables else "ERROR"
            add_issue(
                issues,
                level,
                f"wide table detected: table {index} has {cols} columns; split to 2–3 columns or stacked records",
            )

    if parser.images_missing_alt:
        add_issue(issues, "WARN", f"{parser.images_missing_alt} image(s) lack useful alt text")

    for prev, current in zip(parser.headings, parser.headings[1:]):
        if current > prev + 1:
            add_issue(issues, "WARN", f"heading hierarchy skips from H{prev} to H{current}")
            break

    if "<img" in lower:
        has_responsive_img = bool(
            re.search(r"img\s*\{[^}]*?(?:max-width|width)\s*:\s*100%", lower, flags=re.DOTALL)
            and re.search(r"img\s*\{[^}]*?height\s*:\s*auto", lower, flags=re.DOTALL)
        )
        if not has_responsive_img:
            add_issue(issues, "WARN", "responsive image rule not found; prefer max-width/width: 100% and height: auto")

    if "<h1" in lower and not re.search(
        r"h1\s*\{[^}]*?(?:page-break-before|break-before)\s*:\s*(?:always|page)",
        lower,
        flags=re.DOTALL,
    ):
        add_issue(issues, "WARN", "chapter H1 pagination rule not found; consider starting chapters on a new page")

    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Kindle-oriented reflowable HTML")
    ap.add_argument("html", type=Path)
    ap.add_argument(
        "--allow-wide-tables",
        action="store_true",
        help="downgrade >3-column tables from ERROR to WARN when preservation is explicitly required",
    )
    args = ap.parse_args()

    if not args.html.exists():
        print(f"ERROR: file not found: {args.html}")
        return 2

    text = args.html.read_text(encoding="utf-8", errors="replace")
    issues = validate(text, allow_wide_tables=args.allow_wide_tables)

    errors = [x for x in issues if x[0] == "ERROR"]
    warnings = [x for x in issues if x[0] == "WARN"]

    for level, message in issues:
        print(f"{level}: {message}")

    if not issues:
        print("PASS: no Kindle-format issues detected")
    else:
        print(f"SUMMARY: {len(errors)} error(s), {len(warnings)} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
