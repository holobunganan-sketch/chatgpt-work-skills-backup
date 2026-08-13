from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

from docx_utils import (
    NS,
    W_NS,
    apply_three_line_table,
    caption_kind,
    field_inventory,
    format_parts,
    get_or_add,
    get_or_add_first,
    inside_table,
    is_heading_style,
    paragraph_has_drawing,
    paragraph_style_id,
    paragraph_text,
    parse_xml,
    qn,
    read_package,
    serialize_xml,
    set_paragraph_alignment,
    set_paragraph_spacing,
    set_row_bold,
    set_run_typography,
    significant_rows,
    write_package,
)


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = SKILL_DIR / "assets" / "manuscript-format-profile.json"


def load_profile(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        profile = json.load(handle)
    required = {
        "document": {
            "text_color",
            "chinese_font",
            "latin_font",
            "body_font_size_pt",
            "line_spacing_multiple",
            "page_margins_cm",
        },
        "tables": {"p_value_threshold"},
    }
    for section, keys in required.items():
        if section not in profile:
            raise ValueError(f"Profile missing section: {section}")
        missing = keys.difference(profile[section])
        if missing:
            raise ValueError(
                f"Profile section {section} missing keys: {sorted(missing)}"
            )
    return profile


def cm_to_twips(value: float) -> int:
    return round(float(value) * 1440 / 2.54)


def get_or_add_page_margins(section: etree._Element) -> etree._Element:
    existing = section.find("./w:pgMar", namespaces=NS)
    if existing is not None:
        return existing
    node = etree.Element(qn("pgMar"))
    order = {
        "headerReference": 10,
        "footerReference": 20,
        "footnotePr": 30,
        "endnotePr": 40,
        "type": 50,
        "pgSz": 60,
        "pgMar": 70,
        "paperSrc": 80,
        "pgBorders": 90,
        "lnNumType": 100,
        "pgNumType": 110,
        "cols": 120,
        "formProt": 130,
        "vAlign": 140,
        "noEndnote": 150,
        "titlePg": 160,
        "textDirection": 170,
        "bidi": 180,
    }
    target_rank = order["pgMar"]
    for index, child in enumerate(section):
        local_name = etree.QName(child).localname
        if order.get(local_name, 999) > target_rank:
            section.insert(index, node)
            return node
    section.append(node)
    return node


def apply_page_margins(
    root: etree._Element, margins_cm: dict[str, float]
) -> int:
    count = 0
    for section in root.xpath(".//w:sectPr", namespaces=NS):
        page_margins = get_or_add_page_margins(section)
        for side in ("top", "bottom", "left", "right"):
            page_margins.set(qn(side), str(cm_to_twips(margins_cm[side])))
        count += 1
    return count


def set_style_run_properties(
    rpr: etree._Element,
    *,
    chinese_font: str,
    latin_font: str,
    color: str,
    size_half_points: int | None,
    bold: bool | None = None,
) -> None:
    fonts = get_or_add(rpr, qn("rFonts"))
    fonts.set(qn("ascii"), latin_font)
    fonts.set(qn("hAnsi"), latin_font)
    fonts.set(qn("cs"), latin_font)
    fonts.set(qn("eastAsia"), chinese_font)
    color_node = get_or_add(rpr, qn("color"))
    color_node.set(qn("val"), color)
    if size_half_points is not None:
        get_or_add(rpr, qn("sz")).set(qn("val"), str(size_half_points))
        get_or_add(rpr, qn("szCs")).set(qn("val"), str(size_half_points))
    if bold is not None:
        get_or_add(rpr, qn("b")).set(qn("val"), "1" if bold else "0")
        get_or_add(rpr, qn("bCs")).set(qn("val"), "1" if bold else "0")


def patch_styles(data: bytes, profile: dict) -> bytes:
    root = parse_xml(data)
    document = profile["document"]
    chinese_font = document["chinese_font"]
    latin_font = document["latin_font"]
    color = document["text_color"].upper()
    size_half_points = round(float(document["body_font_size_pt"]) * 2)
    line = round(240 * float(document["line_spacing_multiple"]))

    defaults = get_or_add_first(root, qn("docDefaults"))
    rpr_default = get_or_add(defaults, qn("rPrDefault"))
    rpr = get_or_add(rpr_default, qn("rPr"))
    set_style_run_properties(
        rpr,
        chinese_font=chinese_font,
        latin_font=latin_font,
        color=color,
        size_half_points=size_half_points,
    )
    ppr_default = get_or_add(defaults, qn("pPrDefault"))
    ppr = get_or_add(ppr_default, qn("pPr"))
    spacing = get_or_add(ppr, qn("spacing"))
    spacing.set(qn("line"), str(line))
    spacing.set(qn("lineRule"), "auto")

    for style in root.xpath("./w:style", namespaces=NS):
        style_type = style.get(qn("type"), "")
        style_id = style.get(qn("styleId"), "")
        name_node = style.find("./w:name", namespaces=NS)
        display_name = (
            name_node.get(qn("val"), "") if name_node is not None else ""
        )
        heading = is_heading_style(style_id, display_name)
        style_rpr = get_or_add(style, qn("rPr"))
        style_size = None if heading else (
            size_half_points if style_type == "paragraph" else None
        )
        set_style_run_properties(
            style_rpr,
            chinese_font=chinese_font,
            latin_font=latin_font,
            color=color,
            size_half_points=style_size,
            bold=True if heading else None,
        )
        if style_type == "paragraph" and not heading:
            style_ppr = get_or_add(style, qn("pPr"))
            style_spacing = get_or_add(style_ppr, qn("spacing"))
            style_spacing.set(qn("line"), str(line))
            style_spacing.set(qn("lineRule"), "auto")
    return serialize_xml(root)


def reposition_adjacent_captions(root: etree._Element) -> dict[str, int]:
    body = root.find(".//w:body", namespaces=NS)
    counts = {"table_caption_moved": 0, "figure_caption_moved": 0}
    if body is None:
        return counts

    changed = True
    while changed:
        changed = False
        children = list(body)
        for index, child in enumerate(children):
            if child.tag == qn("tbl") and index + 1 < len(children):
                following = children[index + 1]
                if (
                    following.tag == qn("p")
                    and caption_kind(following) == "table"
                ):
                    body.remove(following)
                    body.insert(index, following)
                    counts["table_caption_moved"] += 1
                    changed = True
                    break
            if (
                child.tag == qn("p")
                and paragraph_has_drawing(child)
                and index > 0
            ):
                preceding = children[index - 1]
                if (
                    preceding.tag == qn("p")
                    and caption_kind(preceding) == "figure"
                ):
                    body.remove(preceding)
                    drawing_index = body.index(child)
                    body.insert(drawing_index + 1, preceding)
                    counts["figure_caption_moved"] += 1
                    changed = True
                    break
    return counts


def patch_document_part(
    data: bytes,
    profile: dict,
    *,
    is_main_document: bool,
) -> tuple[bytes, dict[str, int]]:
    root = parse_xml(data)
    document = profile["document"]
    tables_profile = profile["tables"]
    chinese_font = document["chinese_font"]
    latin_font = document["latin_font"]
    color = document["text_color"].upper()
    size_half_points = round(float(document["body_font_size_pt"]) * 2)
    multiple = float(document["line_spacing_multiple"])
    threshold = float(tables_profile["p_value_threshold"])

    stats = {
        "paragraphs_formatted": 0,
        "headings_bolded": 0,
        "tables_formatted": 0,
        "significant_rows_bolded": 0,
        "title_page_settings_removed": 0,
        "page_margin_sections_formatted": 0,
        "table_caption_moved": 0,
        "figure_caption_moved": 0,
    }

    if is_main_document:
        margins_cm = document.get("page_margins_cm")
        if margins_cm is not None:
            stats["page_margin_sections_formatted"] = apply_page_margins(
                root, margins_cm
            )
        moved = reposition_adjacent_captions(root)
        stats.update(
            {
                "table_caption_moved": moved["table_caption_moved"],
                "figure_caption_moved": moved["figure_caption_moved"],
            }
        )
        for title_page in root.xpath(".//w:sectPr/w:titlePg", namespaces=NS):
            parent = title_page.getparent()
            if parent is not None:
                parent.remove(title_page)
                stats["title_page_settings_removed"] += 1

    for paragraph in root.xpath(".//w:p", namespaces=NS):
        text = paragraph_text(paragraph)
        style_id = paragraph_style_id(paragraph)
        heading = is_heading_style(style_id, text)
        caption = caption_kind(paragraph)
        in_table = inside_table(paragraph)
        has_drawing = paragraph_has_drawing(paragraph)
        if caption:
            set_paragraph_alignment(paragraph, "center")
        body_paragraph = bool(text) and not heading and not caption and not has_drawing
        if body_paragraph and not in_table:
            set_paragraph_spacing(paragraph, multiple)
            stats["paragraphs_formatted"] += 1
        if heading:
            stats["headings_bolded"] += 1
        for run in paragraph.xpath("./w:r | ./w:hyperlink/w:r", namespaces=NS):
            run_has_text = bool(
                run.xpath(".//w:t/text() | .//w:instrText/text()", namespaces=NS)
            )
            if not run_has_text:
                continue
            set_run_typography(
                run,
                chinese_font=chinese_font,
                latin_font=latin_font,
                color=color,
                size_half_points=(
                    size_half_points if body_paragraph and not in_table else None
                ),
                bold=True if heading else None,
            )

    for table in root.xpath(".//w:tbl", namespaces=NS):
        apply_three_line_table(table)
        stats["tables_formatted"] += 1
        for _, row, _ in significant_rows(table, threshold):
            set_row_bold(row)
            stats["significant_rows_bolded"] += 1
        for run in table.xpath(".//w:r", namespaces=NS):
            if not run.xpath(".//w:t/text()", namespaces=NS):
                continue
            set_run_typography(
                run,
                chinese_font=chinese_font,
                latin_font=latin_font,
                color=color,
            )

    return serialize_xml(root), stats


def merge_stats(stats_list: list[dict[str, int]]) -> dict[str, int]:
    result: Counter[str] = Counter()
    for stats in stats_list:
        result.update(stats)
    return dict(result)


def enforce(source: Path, output: Path, profile_path: Path) -> dict:
    if source.resolve() == output.resolve():
        raise ValueError("Output must be a separate file; source overwrite is blocked.")
    profile = load_profile(profile_path)
    package = read_package(source)
    before_fields = field_inventory(package)
    replacements: dict[str, bytes] = {}
    part_stats: list[dict[str, int]] = []

    for part_name in format_parts(package):
        if part_name == "word/styles.xml":
            replacements[part_name] = patch_styles(package[part_name], profile)
            continue
        patched, stats = patch_document_part(
            package[part_name],
            profile,
            is_main_document=part_name == "word/document.xml",
        )
        replacements[part_name] = patched
        part_stats.append(stats)

    candidate = dict(package)
    candidate.update(replacements)
    after_fields = field_inventory(candidate)
    if before_fields != after_fields:
        raise RuntimeError(
            "Field-code protection failed. No output was written; source is unchanged."
        )

    write_package(source, output, replacements)
    report = {
        "status": "formatted",
        "source": str(source.resolve()),
        "output": str(output.resolve()),
        "profile": str(profile_path.resolve()),
        "field_codes_preserved": True,
        "field_code_count": sum(len(items) for items in before_fields.values()),
        "changes": merge_stats(part_stats),
        "manual_review_required": [
            "academic figure palette",
            "English-only figure text",
            "absence of canvas titles",
            "wide figure margins",
            "full-page rendering and pagination",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Format a DOCX manuscript while preserving field codes."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--profile",
        type=Path,
        default=DEFAULT_PROFILE,
        help="Project-specific profile JSON; defaults to the skill profile.",
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        report = enforce(args.source, args.output, args.profile)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
