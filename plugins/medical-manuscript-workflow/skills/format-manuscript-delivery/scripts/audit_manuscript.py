from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from lxml import etree

from docx_utils import (
    NS,
    caption_kind,
    count_list_runs,
    document_has_title_page,
    field_inventory,
    format_parts,
    inside_table,
    is_heading_style,
    likely_independent_title_page,
    paragraph_has_drawing,
    paragraph_style_id,
    paragraph_text,
    parse_xml,
    qn,
    read_package,
    row_is_bold,
    significant_rows,
    table_has_three_line_style,
    zotero_inventory,
    zotero_reference_count,
)


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = SKILL_DIR / "assets" / "manuscript-format-profile.json"


def load_profile(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def issue(
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


def run_text(run: etree._Element) -> str:
    return "".join(run.xpath(".//w:t/text()", namespaces=NS)).strip()


def check_run_typography(
    run: etree._Element,
    *,
    profile: dict,
    require_size: bool,
    require_bold: bool,
    issues: list[dict],
    location: str,
) -> None:
    text = run_text(run)
    if not text:
        return
    document = profile["document"]
    rpr = run.find("./w:rPr", namespaces=NS)
    if rpr is None:
        issue(
            issues,
            "error",
            "RUN_FORMAT_MISSING",
            "可见文字缺少明确运行格式。",
            location,
        )
        return
    fonts = rpr.find("./w:rFonts", namespaces=NS)
    if fonts is None:
        issue(
            issues,
            "error",
            "FONT_MISSING",
            "可见文字缺少字体设置。",
            location,
        )
    else:
        expected_latin = document["latin_font"]
        expected_chinese = document["chinese_font"]
        latin_values = [
            fonts.get(qn("ascii")),
            fonts.get(qn("hAnsi")),
            fonts.get(qn("cs")),
        ]
        if any(value != expected_latin for value in latin_values):
            issue(
                issues,
                "error",
                "LATIN_FONT",
                f"英文/数字字体应为 {expected_latin}。",
                location,
            )
        if fonts.get(qn("eastAsia")) != expected_chinese:
            issue(
                issues,
                "error",
                "CHINESE_FONT",
                f"中文字体应为 {expected_chinese}。",
                location,
            )
    color = rpr.find("./w:color", namespaces=NS)
    expected_color = document["text_color"].upper()
    if color is None or color.get(qn("val"), "").upper() != expected_color:
        issue(
            issues,
            "error",
            "TEXT_COLOR",
            "可见文字应为纯黑色。",
            location,
        )
    if require_size:
        expected_size = str(round(float(document["body_font_size_pt"]) * 2))
        size = rpr.find("./w:sz", namespaces=NS)
        size_cs = rpr.find("./w:szCs", namespaces=NS)
        if (
            size is None
            or size.get(qn("val")) != expected_size
            or size_cs is None
            or size_cs.get(qn("val")) != expected_size
        ):
            issue(
                issues,
                "error",
                "BODY_FONT_SIZE",
                f"正文应为 {document['body_font_size_pt']} 磅。",
                location,
            )
    if require_bold:
        bold = rpr.find("./w:b", namespaces=NS)
        if bold is None or bold.get(qn("val"), "1").casefold() in {
            "0",
            "false",
            "off",
        }:
            issue(
                issues,
                "error",
                "SUBHEADING_BOLD",
                "小标题应加粗。",
                location,
            )


def paragraph_line_spacing_ok(paragraph: etree._Element, multiple: float) -> bool:
    spacing = paragraph.find("./w:pPr/w:spacing", namespaces=NS)
    if spacing is None:
        return False
    expected = str(round(240 * multiple))
    return (
        spacing.get(qn("line")) == expected
        and spacing.get(qn("lineRule"), "auto") == "auto"
    )


def paragraph_centered(paragraph: etree._Element) -> bool:
    alignment = paragraph.find("./w:pPr/w:jc", namespaces=NS)
    return alignment is not None and alignment.get(qn("val")) == "center"


def cm_to_twips(value: float) -> int:
    return round(float(value) * 1440 / 2.54)


def check_page_margins(
    root: etree._Element,
    document: dict,
    issues: list[dict],
) -> dict:
    margins_cm = document.get("page_margins_cm")
    if margins_cm is None:
        return {"enabled": False, "sections": []}
    tolerance_cm = float(document.get("page_margin_tolerance_cm", 0.01))
    tolerance_twips = max(1, cm_to_twips(tolerance_cm))
    sections = root.xpath(".//w:sectPr", namespaces=NS)
    if not sections:
        issue(
            issues,
            "error",
            "PAGE_MARGIN_SECTION_MISSING",
            "DOCX 未检测到可设置页边距的节属性。",
            "正文节属性",
        )
    inventory: list[dict] = []
    for section_index, section in enumerate(sections, start=1):
        page_margins = section.find("./w:pgMar", namespaces=NS)
        actual_cm: dict[str, float | None] = {}
        for side in ("top", "bottom", "left", "right"):
            expected_cm = float(margins_cm[side])
            expected_twips = cm_to_twips(expected_cm)
            raw_value = (
                page_margins.get(qn(side))
                if page_margins is not None
                else None
            )
            try:
                actual_twips = int(raw_value) if raw_value is not None else None
            except ValueError:
                actual_twips = None
            actual_cm[side] = (
                round(actual_twips * 2.54 / 1440, 3)
                if actual_twips is not None
                else None
            )
            if (
                actual_twips is None
                or abs(actual_twips - expected_twips) > tolerance_twips
            ):
                actual_label = (
                    "缺失"
                    if actual_twips is None
                    else f"{actual_twips * 2.54 / 1440:.3f} 厘米"
                )
                issue(
                    issues,
                    "error",
                    f"PAGE_MARGIN_{side.upper()}",
                    f"第 {section_index} 节{side}页边距应为 "
                    f"{expected_cm:.2f} 厘米，当前为 {actual_label}。",
                    f"第 {section_index} 节",
                )
        inventory.append(
            {
                "section": section_index,
                "expected_cm": margins_cm,
                "actual_cm": actual_cm,
            }
        )
    return {
        "enabled": True,
        "tolerance_cm": tolerance_cm,
        "sections": inventory,
    }


def paragraph_is_list(paragraph: etree._Element) -> bool:
    return paragraph.find("./w:pPr/w:numPr", namespaces=NS) is not None


def normalize_heading_text(text: str) -> str:
    cleaned = re.sub(
        r"^\s*(?:(?:\d+(?:\.\d+)*)|(?:[一二三四五六七八九十]+))[、.)．。]?\s*",
        "",
        text,
    )
    return re.sub(r"\s+", " ", cleaned.strip(" \t:：")).casefold()


def heading_level(style_id: str, text: str, major: str | None) -> int:
    style_match = re.search(r"(\d+)", style_id)
    if style_match:
        return max(1, int(style_match.group(1)))
    number_match = re.match(r"^\s*(\d+(?:\.\d+)*)[、.)．。]?\s*", text)
    if number_match:
        return number_match.group(1).count(".") + 1
    if re.match(r"^\s*[一二三四五六七八九十]+[、.．。)]", text):
        return 1
    return 1 if major else 2


def major_section_name(text: str, aliases: dict[str, list[str]]) -> str | None:
    normalized = normalize_heading_text(text)
    for section, section_aliases in aliases.items():
        for alias in section_aliases:
            token = normalize_heading_text(alias)
            if normalized == token:
                return section
            if normalized in {
                f"{token}（{normalize_heading_text(section)}）",
                f"{token} ({normalize_heading_text(section)})",
            }:
                return section
            if normalized.startswith((f"{token}（", f"{token} (")):
                return section
    return None


def document_blocks(
    root: etree._Element, aliases: dict[str, list[str]]
) -> list[dict]:
    body = root.find(".//w:body", namespaces=NS)
    if body is None:
        return []
    blocks: list[dict] = []
    for body_index, child in enumerate(body, start=1):
        if child.tag != qn("p"):
            continue
        text = paragraph_text(child)
        if not text:
            continue
        style_id = paragraph_style_id(child)
        major = major_section_name(text, aliases)
        heading = bool(major) or is_heading_style(style_id, text)
        blocks.append(
            {
                "body_index": body_index,
                "element": child,
                "text": text,
                "style_id": style_id,
                "heading": heading,
                "level": heading_level(style_id, text, major) if heading else None,
                "major": major,
                "caption": caption_kind(child),
                "drawing": paragraph_has_drawing(child),
                "list": paragraph_is_list(child),
            }
        )
    return blocks


def section_slice(blocks: list[dict], start_index: int) -> list[dict]:
    start_level = blocks[start_index]["level"] or 1
    for end_index in range(start_index + 1, len(blocks)):
        block = blocks[end_index]
        if block["heading"] and (block["level"] or 99) <= start_level:
            return blocks[start_index + 1 : end_index]
    return blocks[start_index + 1 :]


def content_paragraphs(blocks: list[dict]) -> list[dict]:
    return [
        block
        for block in blocks
        if not block["heading"]
        and not block["caption"]
        and not block["drawing"]
        and block["text"]
    ]


def natural_paragraphs(blocks: list[dict]) -> list[dict]:
    return [block for block in content_paragraphs(blocks) if not block["list"]]


def check_subheading_paragraphs(
    section: str,
    blocks: list[dict],
    expected: int,
    issues: list[dict],
) -> None:
    heading_indexes = [
        index for index, block in enumerate(blocks) if block["heading"]
    ]
    for position, heading_index in enumerate(heading_indexes):
        end_index = (
            heading_indexes[position + 1]
            if position + 1 < len(heading_indexes)
            else len(blocks)
        )
        heading = blocks[heading_index]
        paragraphs = natural_paragraphs(blocks[heading_index + 1 : end_index])
        if len(paragraphs) != expected:
            issue(
                issues,
                "error",
                f"{section.upper()}_SUBHEADING_PARAGRAPH_COUNT",
                f"{section} 小标题“{heading['text']}”下应有 {expected} 个自然段，"
                f"当前识别到 {len(paragraphs)} 个。",
                f"正文块 {heading['body_index']}",
            )


def check_forbidden_subheadings(
    section: str,
    blocks: list[dict],
    issues: list[dict],
) -> None:
    for block in blocks:
        if not block["heading"]:
            continue
        issue(
            issues,
            "error",
            f"{section.upper()}_SUBHEADING_FORBIDDEN",
            f"{section} 不得设置二级及以下小标题：“{block['text']}”。",
            f"正文块 {block['body_index']}",
        )


PLANNING_MARKERS = re.compile(
    r"(?:计划|拟|预计|目标|估算|至少需要|需纳入|应纳入|将纳入|"
    r"plan(?:ned|s|ning)?|intend(?:ed|s)?|target(?:ed)?|anticipat(?:e|ed)|"
    r"estimat(?:e|ed)|requir(?:e|ed)|will\s+(?:include|enroll))",
    flags=re.I,
)

REALIZED_METHOD_PATTERNS = [
    re.compile(
        r"(?:共计|累计|最终|实际|共)\s*"
        r"(?:纳入|入组|获得|得到|提取|检索到|筛选出|收集|分析)(?:了)?\s*"
        r"(?:\d[\d,]*|[XxＸ]+)\s*"
        r"(?:例|名|个|份|条|项|患者|受试者|样本|记录|病例|例数据)",
        flags=re.I,
    ),
    re.compile(
        r"从[^。；;\n]{0,40}(?:数据库|队列|登记系统)[^。；;\n]{0,25}"
        r"(?:获得|得到|提取|检索到|筛选出|纳入|收集)(?:了)?\s*"
        r"(?:\d[\d,]*|[XxＸ]+)\s*"
        r"(?:例|名|个|份|条|项|患者|受试者|样本|记录|病例|例数据)",
        flags=re.I,
    ),
    re.compile(
        r"(?:纳入|入组|获得|得到|提取|检索到|筛选出|收集|分析)(?:了)?\s*"
        r"(?:\d[\d,]*|[XxＸ]+)\s*"
        r"(?:例|名|个|份|条|项|患者|受试者|样本|记录|病例|例数据)",
        flags=re.I,
    ),
    re.compile(
        r"(?:a\s+total\s+of\s+)?(?:\d[\d,]*|x+)\s+"
        r"(?:patients?|participants?|subjects?|samples?|records?|cases?)\s+"
        r"(?:were|was)\s+(?:included|enrolled|retrieved|obtained|identified|"
        r"collected|analy[sz]ed)",
        flags=re.I,
    ),
    re.compile(
        r"(?:we|this\s+study|the\s+study)\s+"
        r"(?:included|enrolled|retrieved|obtained|identified|collected|analy[sz]ed)\s+"
        r"(?:a\s+total\s+of\s+)?(?:\d[\d,]*|x+)",
        flags=re.I,
    ),
]

RESULTS_INTERPRETATION_PATTERNS = [
    re.compile(r"(?:这|这些|上述|该)(?:一|些)?(?:结果|发现)?(?:提示|意味着|说明)", re.I),
    re.compile(r"(?:可能|或许)(?:由于|源于|反映|意味着|与[^。；;]{0,30}有关)", re.I),
    re.compile(r"(?:既往|先前|已有)(?:研究|文献)[^。；;]{0,30}(?:一致|相符|不同|报道)", re.I),
    re.compile(r"(?:this|these)\s+(?:result|finding)s?\s+(?:suggest|imply|indicate)", re.I),
    re.compile(r"may\s+(?:reflect|be\s+due\s+to|result\s+from|suggest|indicate)", re.I),
    re.compile(r"(?:consistent|inconsistent)\s+with\s+(?:previous|prior)", re.I),
]


def check_methods_boundary(blocks: list[dict], issues: list[dict]) -> None:
    for block in content_paragraphs(blocks):
        text = block["text"]
        for pattern in REALIZED_METHOD_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            context_start = max(0, match.start() - 24)
            context = text[context_start : match.end()]
            if PLANNING_MARKERS.search(context):
                continue
            issue(
                issues,
                "error",
                "METHODS_POST_EXECUTION_RESULT",
                "Methods 检测到研究执行后才能确定的实际数量或结果。",
                f"正文块 {block['body_index']}: {text[:80]}",
            )
            break


def check_results_boundary(blocks: list[dict], issues: list[dict]) -> None:
    for block in content_paragraphs(blocks):
        text = block["text"]
        if any(pattern.search(text) for pattern in RESULTS_INTERPRETATION_PATTERNS):
            issue(
                issues,
                "warning",
                "RESULTS_INTERPRETATION",
                "Results 检测到可能属于解释、机制推断或文献比较的表达，需移至 Discussion 或人工确认。",
                f"正文块 {block['body_index']}: {text[:80]}",
            )


def normalized_sentences(blocks: list[dict]) -> set[str]:
    sentences: set[str] = set()
    for block in content_paragraphs(blocks):
        for sentence in re.split(r"(?<=[。！？!?])|(?<=[.!?])\s+", block["text"]):
            normalized = re.sub(r"[\W_]+", "", sentence, flags=re.UNICODE).casefold()
            if len(normalized) >= 25:
                sentences.add(normalized)
    return sentences


def explicit_limitation_markers(text: str) -> int:
    markers = re.findall(
        r"(?:第一|第二|第三|第四|第五|其一|其二|其三|其四|其五|"
        r"首先|其次|再次|最后|first(?:ly)?|second(?:ly)?|third(?:ly)?|"
        r"fourth(?:ly)?|fifth(?:ly)?)",
        text,
        flags=re.I,
    )
    return len(markers)


def check_imrad_structure(
    root: etree._Element, profile: dict, issues: list[dict]
) -> dict:
    structure = profile.get("structure", {})
    if not structure.get("enabled", False):
        return {"enabled": False, "sections": {}}

    required = structure["required_major_sections"]
    blocks = document_blocks(root, structure["heading_aliases"])
    section_positions: dict[str, list[int]] = {name: [] for name in required}
    observed_order: list[str] = []
    for index, block in enumerate(blocks):
        section = block["major"]
        if section in section_positions:
            section_positions[section].append(index)
            observed_order.append(section)

    for section in required:
        positions = section_positions[section]
        if not positions:
            issue(
                issues,
                "error",
                "IMRAD_SECTION_MISSING",
                f"缺少默认 IMRAD 主章节：{section}。",
                "正文结构",
            )
        elif len(positions) > 1:
            issue(
                issues,
                "error",
                "IMRAD_SECTION_DUPLICATED",
                f"主章节 {section} 出现 {len(positions)} 次。",
                "正文结构",
            )

    first_occurrences = [
        section_positions[name][0]
        for name in required
        if section_positions[name]
    ]
    if first_occurrences != sorted(first_occurrences):
        issue(
            issues,
            "error",
            "IMRAD_SECTION_ORDER",
            "主章节应按 Introduction、Methods、Results、Discussion、Conclusion 排列。",
            "正文结构",
        )

    sections: dict[str, list[dict]] = {}
    for name, positions in section_positions.items():
        if positions:
            sections[name] = section_slice(blocks, positions[0])

    introduction = sections.get("Introduction")
    if introduction is not None:
        paragraphs = natural_paragraphs(introduction)
        expected = int(structure["introduction"]["paragraphs"])
        if not structure["introduction"].get("subheadings_allowed", True):
            check_forbidden_subheadings(
                "Introduction", introduction, issues
            )
        if len(paragraphs) != expected:
            issue(
                issues,
                "error",
                "INTRODUCTION_PARAGRAPH_COUNT",
                f"Introduction 应有 {expected} 个自然段，当前识别到 {len(paragraphs)} 个。",
                "Introduction",
            )

    for name, key in (("Methods", "methods"), ("Results", "results")):
        section = sections.get(name)
        if section is None:
            continue
        expected = int(structure[key]["paragraphs_per_subheading"])
        check_subheading_paragraphs(name, section, expected, issues)
        if name == "Methods" and structure[key]["forbid_post_execution_results"]:
            check_methods_boundary(section, issues)
        if name == "Results" and structure[key]["forbid_interpretation"]:
            check_results_boundary(section, issues)

    discussion = sections.get("Discussion")
    if discussion is not None:
        paragraphs = natural_paragraphs(discussion)
        if not structure["discussion"].get("subheadings_allowed", True):
            check_forbidden_subheadings("Discussion", discussion, issues)
        minimum = int(structure["discussion"]["minimum_paragraphs"])
        maximum = int(structure["discussion"]["maximum_paragraphs"])
        if not minimum <= len(paragraphs) <= maximum:
            issue(
                issues,
                "error",
                "DISCUSSION_PARAGRAPH_COUNT",
                f"Discussion 应有 {minimum}–{maximum} 个自然段，当前识别到 {len(paragraphs)} 个。",
                "Discussion",
            )
        if paragraphs:
            first_text = paragraphs[0]["text"]
            if not re.search(r"(?:本研究|本项研究|this\s+study|the\s+present\s+study)", first_text, re.I):
                issue(
                    issues,
                    "warning",
                    "DISCUSSION_OVERVIEW_REVIEW",
                    "Discussion 首段未识别到全文概括标志，需确认其覆盖研究问题、方法、主要结果和全文意义。",
                    f"正文块 {paragraphs[0]['body_index']}",
                )
            last_text = paragraphs[-1]["text"]
            if not re.search(r"(?:局限|限制|不足|limitation)", last_text, re.I):
                issue(
                    issues,
                    "error",
                    "DISCUSSION_LIMITATIONS_MISSING",
                    "Discussion 末段应集中声明本研究的局限。",
                    f"正文块 {paragraphs[-1]['body_index']}",
                )
            marker_count = explicit_limitation_markers(last_text)
            maximum_limitations = int(
                structure["discussion"]["maximum_limitations"]
            )
            if marker_count > maximum_limitations:
                issue(
                    issues,
                    "error",
                    "DISCUSSION_LIMITATION_COUNT",
                    f"Discussion 末段识别到 {marker_count} 个局限枚举标志，"
                    f"不得超过 {maximum_limitations} 点。",
                    f"正文块 {paragraphs[-1]['body_index']}",
                )

    conclusion = sections.get("Conclusion")
    if conclusion is not None:
        paragraphs = natural_paragraphs(conclusion)
        expected = int(structure["conclusion"]["paragraphs"])
        if len(paragraphs) != expected:
            issue(
                issues,
                "error",
                "CONCLUSION_PARAGRAPH_COUNT",
                f"Conclusion 应有 {expected} 个自然段，当前识别到 {len(paragraphs)} 个。",
                "Conclusion",
            )
        if paragraphs:
            conclusion_text = paragraphs[0]["text"]
            if not re.search(
                r"(?:未来|进一步|有望|奠定基础|提供方向|"
                r"future|further|going\s+forward|may\s+inform|foundation)",
                conclusion_text,
                re.I,
            ):
                issue(
                    issues,
                    "warning",
                    "CONCLUSION_FORWARD_LOOKING_REVIEW",
                    "Conclusion 未识别到前瞻性表达，需确认其完成宏观、前瞻的总结。",
                    f"正文块 {paragraphs[0]['body_index']}",
                )
            prior_sentences = normalized_sentences(
                sections.get("Results", []) + sections.get("Discussion", [])
            )
            repeated = normalized_sentences(paragraphs) & prior_sentences
            if repeated:
                issue(
                    issues,
                    "error",
                    "CONCLUSION_REPEATS_PRIOR_TEXT",
                    "Conclusion 与 Results 或 Discussion 存在逐句重复。",
                    f"正文块 {paragraphs[0]['body_index']}",
                )

    return {
        "enabled": True,
        "observed_order": observed_order,
        "sections": {
            name: {
                "occurrences": len(section_positions[name]),
                "natural_paragraphs": len(natural_paragraphs(sections.get(name, []))),
            }
            for name in required
        },
    }


def check_caption_positions(root: etree._Element, issues: list[dict]) -> None:
    body = root.find(".//w:body", namespaces=NS)
    if body is None:
        return
    children = list(body)
    for index, child in enumerate(children):
        if child.tag == qn("p"):
            kind = caption_kind(child)
            if kind and not paragraph_centered(child):
                issue(
                    issues,
                    "error",
                    "CAPTION_ALIGNMENT",
                    "图题和表题应居中。",
                    f"正文块 {index + 1}",
                )
            if kind == "table":
                if index + 1 >= len(children) or children[index + 1].tag != qn(
                    "tbl"
                ):
                    issue(
                        issues,
                        "error",
                        "TABLE_CAPTION_POSITION",
                        "表题应紧邻表格上方。",
                        f"正文块 {index + 1}",
                    )
            if kind == "figure":
                if (
                    index == 0
                    or children[index - 1].tag != qn("p")
                    or not paragraph_has_drawing(children[index - 1])
                ):
                    issue(
                        issues,
                        "error",
                        "FIGURE_CAPTION_POSITION",
                        "图题应紧邻图片下方。",
                        f"正文块 {index + 1}",
                    )
            if paragraph_has_drawing(child):
                if (
                    index + 1 >= len(children)
                    or children[index + 1].tag != qn("p")
                    or caption_kind(children[index + 1]) != "figure"
                ):
                    issue(
                        issues,
                        "warning",
                        "FIGURE_CAPTION_MISSING",
                        "图片下方未识别到标准图题，需人工确认。",
                        f"正文块 {index + 1}",
                    )
        elif child.tag == qn("tbl"):
            if (
                index == 0
                or children[index - 1].tag != qn("p")
                or caption_kind(children[index - 1]) != "table"
            ):
                issue(
                    issues,
                    "warning",
                    "TABLE_CAPTION_MISSING",
                    "表格上方未识别到标准表题，需人工确认。",
                    f"正文块 {index + 1}",
                )


def check_revision_objects(
    package: dict[str, bytes], issues: list[dict], stage: str
) -> None:
    severity = "error" if stage == "final" else "warning"
    if "word/comments.xml" in package:
        root = parse_xml(package["word/comments.xml"])
        comments = root.xpath(".//w:comment", namespaces=NS)
        if comments:
            issue(
                issues,
                severity,
                "COMMENTS_PRESENT",
                f"文稿含 {len(comments)} 条批注。",
                "word/comments.xml",
            )
    tracked = 0
    hidden = 0
    for part_name in format_parts(package):
        root = parse_xml(package[part_name])
        tracked += len(
            root.xpath(
                ".//w:ins | .//w:del | .//w:moveFrom | .//w:moveTo",
                namespaces=NS,
            )
        )
        hidden += len(root.xpath(".//w:vanish", namespaces=NS))
    if tracked:
        issue(
            issues,
            severity,
            "TRACKED_CHANGES_PRESENT",
            f"文稿含 {tracked} 处修订对象。",
            "DOCX XML",
        )
    if hidden:
        issue(
            issues,
            severity,
            "HIDDEN_TEXT_PRESENT",
            f"文稿含 {hidden} 处隐藏文字设置。",
            "DOCX XML",
        )


def audit(
    manuscript: Path,
    profile_path: Path,
    *,
    stage: str,
    compare_source: Path | None,
) -> dict:
    profile = load_profile(profile_path)
    package = read_package(manuscript)
    issues: list[dict] = []
    document_data = package.get("word/document.xml")
    if not document_data:
        raise ValueError("DOCX does not contain word/document.xml")
    root = parse_xml(document_data)
    document = profile["document"]
    threshold = float(profile["tables"]["p_value_threshold"])
    structure_report = check_imrad_structure(root, profile, issues)
    margin_report = check_page_margins(root, document, issues)

    if document_has_title_page(root):
        issue(
            issues,
            "error",
            "TITLE_PAGE_SETTING",
            "文稿启用了独立首页设置。",
            "节属性",
        )
    if likely_independent_title_page(root):
        issue(
            issues,
            "error",
            "INDEPENDENT_TITLE_PAGE",
            "正文开头检测到疑似独立标题页分页。",
            "文稿前 20 段",
        )

    paragraph_index = 0
    for paragraph in root.xpath(".//w:p", namespaces=NS):
        text = paragraph_text(paragraph)
        if not text:
            continue
        paragraph_index += 1
        style_id = paragraph_style_id(paragraph)
        heading = is_heading_style(style_id, text)
        caption = caption_kind(paragraph)
        body = not heading and not caption and not paragraph_has_drawing(paragraph)
        in_table = inside_table(paragraph)
        location = f"段落 {paragraph_index}: {text[:60]}"
        if body and not in_table and not paragraph_line_spacing_ok(
            paragraph, float(document["line_spacing_multiple"])
        ):
            issue(
                issues,
                "error",
                "LINE_SPACING",
                f"正文应使用 {document['line_spacing_multiple']} 倍行距。",
                location,
            )
        for run in paragraph.xpath("./w:r | ./w:hyperlink/w:r", namespaces=NS):
            check_run_typography(
                run,
                profile=profile,
                require_size=body and not in_table,
                require_bold=heading,
                issues=issues,
                location=location,
            )

    longest_list = count_list_runs(root)
    limit = int(document["max_consecutive_list_paragraphs_before_review"])
    if longest_list > limit:
        issue(
            issues,
            "warning",
            "DENSE_LISTS",
            f"检测到连续 {longest_list} 个项目符号段落，需改为自然段或确认保留。",
            "正文",
        )

    check_caption_positions(root, issues)
    for table_index, table in enumerate(
        root.xpath(".//w:tbl", namespaces=NS), start=1
    ):
        if not table_has_three_line_style(table):
            issue(
                issues,
                "error",
                "THREE_LINE_TABLE",
                "表格未满足三线表边框结构。",
                f"Table {table_index}",
            )
        for row_index, row, p_value in significant_rows(table, threshold):
            if not row_is_bold(row):
                issue(
                    issues,
                    "error",
                    "SIGNIFICANT_ROW_BOLD",
                    f"P={p_value:g} 的显著性项目应整行加粗。",
                    f"Table {table_index}, row {row_index}",
                )

    check_revision_objects(package, issues, stage)

    zotero = zotero_inventory(package)
    zotero_fields = [
        field for fields in zotero.values() for field in fields
    ]
    if stage == "final" and not zotero_fields:
        issue(
            issues,
            "error",
            "ZOTERO_FIELDS_MISSING",
            "最终文稿未检测到 Zotero 动态引文字段。",
            "DOCX fields",
        )
    max_refs = int(profile["citations"]["maximum_references_per_citation"])
    for index, field in enumerate(zotero_fields, start=1):
        count = zotero_reference_count(field)
        if count is not None and count > max_refs:
            issue(
                issues,
                "error",
                "CITATION_LIMIT",
                f"同一引文位置包含 {count} 篇文献，最多允许 {max_refs} 篇。",
                f"Zotero field {index}",
            )

    if compare_source is not None:
        source_package = read_package(compare_source)
        if field_inventory(source_package) != field_inventory(package):
            issue(
                issues,
                "error",
                "FIELD_CODE_CHANGED",
                "与源文稿相比，字段代码的数量、顺序或载荷发生变化。",
                "DOCX fields",
            )

    counts = {
        "errors": sum(item["severity"] == "error" for item in issues),
        "warnings": sum(item["severity"] == "warning" for item in issues),
        "zotero_fields": len(zotero_fields),
        "tables": len(root.xpath(".//w:tbl", namespaces=NS)),
        "paragraphs": paragraph_index,
    }
    manual_review_required = [
        "sentence-by-sentence submission suitability, section fit and placement",
        "alignment with the user-specified thesis and manuscript throughline",
        "editorial-process language, defensive caveats and nonfunctional evidence-boundary statements",
        "pagination and page flow",
        "figure language, palette, canvas title and margins",
        "complex table headers and cross-page layout",
        "full-page visual rendering",
    ]
    if structure_report["enabled"]:
        manual_review_required[0:0] = [
            "Discussion opening paragraph whole-study overview",
            "Discussion final paragraph contains one to three limitations",
            "Conclusion is macro, forward-looking and semantically distinct from Results and Discussion",
            "Results interpretation heuristic matches",
        ]
    return {
        "status": "pass" if counts["errors"] == 0 else "fail",
        "manuscript": str(manuscript.resolve()),
        "stage": stage,
        "profile": str(profile_path.resolve()),
        "counts": counts,
        "structure": structure_report,
        "page_margins": margin_report,
        "issues": issues,
        "manual_review_required": manual_review_required,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit manuscript formatting.")
    parser.add_argument("manuscript", type=Path)
    parser.add_argument(
        "--profile", type=Path, default=DEFAULT_PROFILE
    )
    parser.add_argument(
        "--stage", choices=("draft", "final"), default="final"
    )
    parser.add_argument("--compare-source", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = audit(
            args.manuscript,
            args.profile,
            stage=args.stage,
            compare_source=args.compare_source,
        )
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
