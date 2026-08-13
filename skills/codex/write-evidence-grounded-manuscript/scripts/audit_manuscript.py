#!/usr/bin/env python3
"""Audit a Markdown manuscript for structure, section leakage, citations, and assets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
ASSET_RE = re.compile(r"\[\[(TABLE|FIGURE):(\d+)\]\]", re.IGNORECASE)
CITATION_RE = re.compile(r"\[\[CITE:[^\]]+\]\]", re.IGNORECASE)
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?%?")
LIMITATION_RE = re.compile(
    r"\b(?:limit(?:ation|ed|s|ing)?|constraint|weakness|shortcoming|uncertain|bias|lack|absence|"
    r"inconsisten|underrepresent|single[- ](?:center|site)|small sample|retrospective|missing|incomplete|"
    r"overfit|measurement error|confound)\w*\b",
    re.IGNORECASE,
)
FUTURE_ACTION_RE = re.compile(
    r"\b(?:future\s+(?:research|stud(?:y|ies)|work)|next\s+(?:study|phase)|subsequent\s+stud(?:y|ies)|"
    r"should|could|must|need(?:s|ed)?\s+to|is\s+needed|are\s+needed|is\s+required|are\s+required)\b",
    re.IGNORECASE,
)
DISCUSSION_TRANSITIONS = [
    re.compile(r"\b(?:first|firstly|one limitation|the first limitation)\b", re.IGNORECASE),
    re.compile(r"\b(?:second|secondly|a second limitation|the second limitation)\b", re.IGNORECASE),
    re.compile(r"\b(?:third|thirdly|a third limitation|the third limitation)\b", re.IGNORECASE),
]
FOURTH_TRANSITION_RE = re.compile(r"\b(?:fourth|fourthly|a fourth limitation|the fourth limitation)\b", re.IGNORECASE)

HIGH_PRECISION_RESULT_PATTERNS = [
    re.compile(
        r"\b(?:included|comprised|contained|analy[sz]ed)\s+"
        r"\d[\d,]*\s+(?:participants|patients|records|samples|events|deaths|features|genes|variables)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:final|selected|retained|best|optimal)\s+"
        r"(?:model|specification|configuration|parameter|threshold|cutoff)\b.{0,80}"
        r"\b(?:contained|comprised|included|was|were|=|of)\b.{0,30}\d",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:C-index|AUC|accuracy|sensitivity|specificity|hazard ratio|odds ratio|risk ratio|"
        r"calibration slope|Brier score)\b.{0,60}\b(?:was|were|=)\s*[-+]?\d",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:threshold|cutoff|coefficient|estimate)\s+(?:was|were|=)\s*[-+]?\d",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:yielded|resulted in|identified|selected|retained)\b.{0,70}"
        r"\b\d[\d,]*(?:\.\d+)?\b",
        re.IGNORECASE,
    ),
]


@dataclass
class Heading:
    level: int
    title: str
    start: int
    end: int


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).resolve().parent.parent / "assets" / "default-profile.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_headings(text: str) -> list[Heading]:
    matches = list(HEADING_RE.finditer(text))
    return [
        Heading(level=len(match.group(1)), title=match.group(2).strip(), start=match.start(), end=match.end())
        for match in matches
    ]


def section_span(text: str, headings: list[Heading], title: str) -> tuple[int, int, Heading] | None:
    target = normalize(title)
    for index, heading in enumerate(headings):
        if normalize(heading.title) != target:
            continue
        stop = len(text)
        for following in headings[index + 1 :]:
            if following.level <= heading.level:
                stop = following.start
                break
        return heading.end, stop, heading
    return None


def section_at(headings: list[Heading], position: int) -> str | None:
    candidates = [heading for heading in headings if heading.start <= position]
    if not candidates:
        return None
    current = candidates[-1]
    while current.level > 2:
        earlier = [h for h in candidates if h.start < current.start and h.level < current.level]
        if not earlier:
            break
        current = earlier[-1]
    return current.title


def extract_abstract_label(abstract: str, label: str, labels: list[str]) -> str:
    ordered = "|".join(re.escape(item) for item in labels)
    pattern = re.compile(
        rf"(?:\*\*)?{re.escape(label)}\s*:\s*(?:\*\*)?\s*(.*?)"
        rf"(?=(?:\n\s*\n|\s+)(?:\*\*)?(?:{ordered})\s*:|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(abstract)
    return match.group(1).strip() if match else ""


def add_issue(target: list[dict[str, Any]], code: str, message: str, **details: Any) -> None:
    item: dict[str, Any] = {"code": code, "message": message}
    if details:
        item["details"] = details
    target.append(item)


def result_leakage_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in HIGH_PRECISION_RESULT_PATTERNS:
        hits.extend(match.group(0).strip() for match in pattern.finditer(text))
    return hits


def paragraph_count(section: str) -> int:
    return len(extract_paragraphs(section))


def extract_paragraphs(section: str) -> list[str]:
    cleaned = HEADING_RE.sub("", section)
    cleaned = ASSET_RE.sub("", cleaned)
    blocks = [re.sub(r"\s+", " ", block).strip() for block in re.split(r"\n\s*\n", cleaned)]
    return [block for block in blocks if block]


def discussion_final_units(paragraph: str) -> tuple[list[re.Match[str]], list[str]]:
    matches: list[re.Match[str]] = []
    for pattern in DISCUSSION_TRANSITIONS:
        match = pattern.search(paragraph)
        if match:
            matches.append(match)
    matches.sort(key=lambda item: item.start())
    units: list[str] = []
    for index, match in enumerate(matches):
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(paragraph)
        units.append(paragraph[match.start() : stop].strip())
    return matches, units


def audit(args: argparse.Namespace) -> dict[str, Any]:
    manuscript_path = Path(args.manuscript).resolve()
    text = manuscript_path.read_text(encoding="utf-8-sig")
    config = load_config(Path(args.config).resolve() if args.config else None)
    structure = config.get("structure", {})
    boundary = config.get("methods_results", {})
    citation_config = config.get("citations", {})
    headings = parse_headings(text)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required_sections = structure.get("required_sections", [])
    section_positions: list[tuple[str, int]] = []
    for section in required_sections:
        span = section_span(text, headings, section)
        if span is None:
            add_issue(errors, "missing-section", f"Required section is missing: {section}")
        else:
            section_positions.append((section, span[2].start))
    if section_positions != sorted(section_positions, key=lambda item: item[1]):
        add_issue(errors, "section-order", "Required sections are not in configured order")

    abstract_span = section_span(text, headings, "Abstract")
    abstract_text = text[abstract_span[0] : abstract_span[1]] if abstract_span else ""
    abstract_labels = structure.get("abstract_labels", [])
    missing_labels = [label for label in abstract_labels if not extract_abstract_label(abstract_text, label, abstract_labels)]
    if missing_labels:
        add_issue(errors, "abstract-labels", "Structured abstract labels are missing", labels=missing_labels)

    methods_span = section_span(text, headings, "Methods")
    results_span = section_span(text, headings, "Results")
    methods_text = text[methods_span[0] : methods_span[1]] if methods_span else ""
    results_text = text[results_span[0] : results_span[1]] if results_span else ""
    abstract_methods = extract_abstract_label(abstract_text, "Methods", abstract_labels)

    result_terms = list(args.result_term or [])
    if args.result_terms_file:
        terms_path = Path(args.result_terms_file)
        result_terms.extend(
            line.strip() for line in terms_path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    for location, content in (("abstract Methods", abstract_methods), ("main Methods", methods_text)):
        for term in result_terms:
            if normalize(term) in normalize(content):
                add_issue(errors, "result-term-in-methods", f"Verified result term appears in {location}", term=term)
        hits = result_leakage_hits(content)
        for hit in hits:
            add_issue(warnings, "possible-result-in-methods", f"Possible realized result in {location}", text=hit)

    numeric_policy = boundary.get("numeric_policy", "prespecified-only")
    if args.strict_methods_numeric or numeric_policy == "none":
        for location, content in (("abstract Methods", abstract_methods), ("main Methods", methods_text)):
            numbers = NUMBER_RE.findall(content)
            if numbers:
                add_issue(errors, "numeric-methods", f"Numeric tokens appear in {location} under no-numeric policy", tokens=numbers)

    allowed_subsections = {normalize(item) for item in structure.get("subsections_allowed_in", [])}
    max_level = int(structure.get("max_markdown_heading_level", 6))
    for heading in headings:
        if heading.level > max_level:
            add_issue(errors, "heading-depth", "Heading exceeds configured Markdown depth", heading=heading.title, level=heading.level)
        if heading.level < 3:
            continue
        parent = section_at(headings, heading.start)
        if parent and normalize(parent) not in allowed_subsections:
            add_issue(errors, "subsection-location", "Subsection appears in a section that forbids subsections", heading=heading.title, section=parent)

    conclusion_span = section_span(text, headings, "Conclusion")
    if conclusion_span:
        count = paragraph_count(text[conclusion_span[0] : conclusion_span[1]])
        expected = int(structure.get("conclusion_paragraphs", 1))
        if count != expected:
            add_issue(errors, "conclusion-paragraphs", "Conclusion paragraph count does not match profile", expected=expected, actual=count)

    discussion_config = config.get("discussion", {})
    final_discussion_config = discussion_config.get("final_paragraph", {})
    discussion_span = section_span(text, headings, "Discussion")
    discussion_paragraphs = extract_paragraphs(text[discussion_span[0] : discussion_span[1]]) if discussion_span else []
    final_discussion = discussion_paragraphs[-1] if discussion_paragraphs else ""
    transition_matches, limitation_units = discussion_final_units(final_discussion) if final_discussion else ([], [])
    expected_limitations = int(final_discussion_config.get("limitation_count", 0) or 0)
    if final_discussion_config.get("required", False):
        if not final_discussion:
            add_issue(errors, "discussion-final-paragraph", "Discussion has no final paragraph")
        else:
            if not LIMITATION_RE.search(final_discussion):
                add_issue(errors, "discussion-final-limitations", "Final Discussion paragraph does not explicitly discuss limitations")
            if FOURTH_TRANSITION_RE.search(final_discussion):
                add_issue(errors, "discussion-final-limitation-count", "Final Discussion paragraph introduces a fourth limitation")
            if final_discussion_config.get("require_explicit_transitions", False) and len(transition_matches) != expected_limitations:
                add_issue(
                    errors,
                    "discussion-final-limitation-count",
                    "Final Discussion paragraph does not contain the configured number of explicit limitation transitions",
                    expected=expected_limitations,
                    actual=len(transition_matches),
                )
            if final_discussion_config.get("require_paired_future_improvements", False) and limitation_units:
                for index, unit in enumerate(limitation_units, start=1):
                    if not LIMITATION_RE.search(unit):
                        add_issue(
                            errors,
                            "discussion-limitation-unit",
                            "A final-paragraph limitation unit lacks a clear limitation or consequence signal",
                            unit=index,
                            text=unit,
                        )
                    if not FUTURE_ACTION_RE.search(unit):
                        add_issue(
                            errors,
                            "discussion-future-pair",
                            "A final-paragraph limitation is not paired with a concrete future-study improvement",
                            unit=index,
                            text=unit,
                        )

    empirical_section = normalize(boundary.get("empirical_assets_section", "Results"))
    marker_counts: dict[str, list[int]] = {"TABLE": [], "FIGURE": []}
    for marker in ASSET_RE.finditer(text):
        kind = marker.group(1).upper()
        number = int(marker.group(2))
        marker_counts[kind].append(number)
        section = section_at(headings, marker.start())
        if empirical_section and normalize(section or "") != empirical_section:
            add_issue(errors, "asset-section", "Empirical asset marker appears outside configured section", marker=marker.group(0), section=section)
        label = f"{kind.title()} {number}"
        lookback = text[max(0, marker.start() - int(args.citation_window)) : marker.start()]
        if not re.search(rf"\b{re.escape(label)}\b", lookback, re.IGNORECASE):
            add_issue(warnings, "asset-not-cited-before", "Asset marker is not cited in nearby preceding prose", marker=marker.group(0))
    for kind, numbers in marker_counts.items():
        if numbers and numbers != list(range(1, max(numbers) + 1)):
            add_issue(errors, "asset-numbering", f"{kind.title()} markers are not consecutive from 1", numbers=numbers)

    allowed_citation_sections = {normalize(item) for item in citation_config.get("external_citations_allowed_in", [])}
    citation_sections: dict[str, int] = {}
    for citation in CITATION_RE.finditer(text):
        section = section_at(headings, citation.start()) or "Unknown"
        citation_sections[section] = citation_sections.get(section, 0) + 1
        if allowed_citation_sections and normalize(section) not in allowed_citation_sections:
            add_issue(errors, "citation-section", "External citation marker appears in a forbidden section", citation=citation.group(0), section=section)

    result_control_presence = {term: (normalize(term) in normalize(results_text)) for term in result_terms}
    missing_result_terms = [term for term, present in result_control_presence.items() if not present]
    if missing_result_terms:
        add_issue(warnings, "result-term-missing-results", "Verified result terms were not found in Results", terms=missing_result_terms)

    status = "fail" if errors or (args.fail_on_warning and warnings) else "pass"
    return {
        "status": status,
        "manuscript": str(manuscript_path),
        "profile": config.get("profile_name"),
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "required_sections_found": len(section_positions),
            "headings": len(headings),
            "abstract_methods_numeric_tokens": NUMBER_RE.findall(abstract_methods),
            "main_methods_numeric_tokens": NUMBER_RE.findall(methods_text),
            "table_markers": marker_counts["TABLE"],
            "figure_markers": marker_counts["FIGURE"],
            "citation_markers_by_section": citation_sections,
            "result_control_presence": result_control_presence,
            "discussion_paragraphs": len(discussion_paragraphs),
            "discussion_final_limitation_transitions": len(transition_matches),
            "discussion_final_units_with_future_actions": sum(bool(FUTURE_ACTION_RE.search(unit)) for unit in limitation_units),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript", help="Markdown manuscript path")
    parser.add_argument("--config", help="Profile JSON; defaults to the bundled profile")
    parser.add_argument("--result-term", action="append", help="Verified result term that must not occur in Methods and should occur in Results")
    parser.add_argument("--result-terms-file", help="UTF-8 text file with one verified result term per line")
    parser.add_argument("--strict-methods-numeric", action="store_true", help="Reject every numeric token in abstract Methods and main Methods")
    parser.add_argument("--citation-window", type=int, default=1400, help="Characters to inspect before an asset marker")
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--json-out", help="Write the JSON report to this path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit(args)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        Path(args.json_out).write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
