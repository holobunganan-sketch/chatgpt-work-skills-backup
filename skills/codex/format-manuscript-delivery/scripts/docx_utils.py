from __future__ import annotations

import json
import math
import re
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS, "r": R_NS}


def qn(local: str, namespace: str = W_NS) -> str:
    return f"{{{namespace}}}{local}"


def validate_docx_path(path: Path) -> None:
    if path.suffix.lower() != ".docx":
        raise ValueError(f"Expected a .docx file: {path}")
    if not path.is_file():
        raise FileNotFoundError(path)
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Invalid DOCX/ZIP package: {path}")


def read_package(path: Path) -> dict[str, bytes]:
    validate_docx_path(path)
    with zipfile.ZipFile(path, "r") as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def write_package(source: Path, output: Path, replacements: dict[str, bytes]) -> None:
    validate_docx_path(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() == output.resolve():
        temp_dir = Path(tempfile.mkdtemp(prefix="format-manuscript-"))
        temp_output = temp_dir / source.name
    else:
        temp_dir = None
        temp_output = output

    try:
        with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(
            temp_output, "w"
        ) as dst:
            seen: set[str] = set()
            for info in src.infolist():
                data = replacements.get(info.filename, src.read(info.filename))
                dst.writestr(info, data)
                seen.add(info.filename)
            for name, data in replacements.items():
                if name not in seen:
                    dst.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        if temp_dir is not None:
            shutil.move(str(temp_output), str(output))
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


def parse_xml(data: bytes) -> etree._Element:
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    return etree.fromstring(data, parser=parser)


def serialize_xml(root: etree._Element) -> bytes:
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )


def get_or_add(parent: etree._Element, tag: str) -> etree._Element:
    child = parent.find(tag)
    if child is None:
        child = etree.SubElement(parent, tag)
    return child


def get_or_add_first(parent: etree._Element, tag: str) -> etree._Element:
    child = parent.find(tag)
    if child is not None:
        return child
    child = etree.Element(tag)
    parent.insert(0, child)
    return child


def paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()


def cell_text(cell: etree._Element) -> str:
    return " ".join(
        text
        for text in (
            paragraph_text(p) for p in cell.xpath(".//w:p", namespaces=NS)
        )
        if text
    ).strip()


def paragraph_style_id(paragraph: etree._Element) -> str:
    style = paragraph.find("./w:pPr/w:pStyle", namespaces=NS)
    if style is None:
        return ""
    return style.get(qn("val"), "")


def is_heading_style(style_id: str, text: str = "") -> bool:
    token = style_id.casefold().replace(" ", "")
    if any(key in token for key in ("heading", "subtitle", "小标题", "标题")):
        return True
    stripped = text.strip()
    return bool(
        re.match(
            r"^(?:\d+(?:\.\d+){0,3}|[一二三四五六七八九十]+[、.])\s*\S+",
            stripped,
        )
        and len(stripped) <= 80
    )


def caption_kind(paragraph: etree._Element) -> str | None:
    text = paragraph_text(paragraph)
    style = paragraph_style_id(paragraph).casefold()
    if re.match(r"^\s*(?:table|表)\s*[sS]?\d+", text, flags=re.I):
        return "table"
    if re.match(r"^\s*(?:figure|fig\.?|图)\s*[sS]?\d+", text, flags=re.I):
        return "figure"
    if "caption" in style or "题注" in style:
        lowered = text.casefold()
        if lowered.startswith(("table", "表")):
            return "table"
        if lowered.startswith(("figure", "fig", "图")):
            return "figure"
    return None


def paragraph_has_drawing(paragraph: etree._Element) -> bool:
    return bool(
        paragraph.xpath(
            ".//w:drawing | .//w:pict | .//w:object",
            namespaces=NS,
        )
    )


def inside_table(element: etree._Element) -> bool:
    return any(ancestor.tag == qn("tbl") for ancestor in element.iterancestors())


def ensure_run_properties(run: etree._Element) -> etree._Element:
    return get_or_add_first(run, qn("rPr"))


def ensure_paragraph_properties(paragraph: etree._Element) -> etree._Element:
    return get_or_add_first(paragraph, qn("pPr"))


def set_run_typography(
    run: etree._Element,
    *,
    chinese_font: str,
    latin_font: str,
    color: str,
    size_half_points: int | None = None,
    bold: bool | None = None,
) -> None:
    rpr = ensure_run_properties(run)
    fonts = get_or_add(rpr, qn("rFonts"))
    fonts.set(qn("ascii"), latin_font)
    fonts.set(qn("hAnsi"), latin_font)
    fonts.set(qn("cs"), latin_font)
    fonts.set(qn("eastAsia"), chinese_font)
    color_element = get_or_add(rpr, qn("color"))
    color_element.set(qn("val"), color.upper())
    if size_half_points is not None:
        size = get_or_add(rpr, qn("sz"))
        size.set(qn("val"), str(size_half_points))
        size_cs = get_or_add(rpr, qn("szCs"))
        size_cs.set(qn("val"), str(size_half_points))
    if bold is not None:
        bold_element = get_or_add(rpr, qn("b"))
        bold_element.set(qn("val"), "1" if bold else "0")
        bold_cs = get_or_add(rpr, qn("bCs"))
        bold_cs.set(qn("val"), "1" if bold else "0")


def set_paragraph_spacing(paragraph: etree._Element, multiple: float) -> None:
    ppr = ensure_paragraph_properties(paragraph)
    spacing = get_or_add(ppr, qn("spacing"))
    spacing.set(qn("line"), str(round(240 * multiple)))
    spacing.set(qn("lineRule"), "auto")


def set_paragraph_alignment(paragraph: etree._Element, value: str) -> None:
    ppr = ensure_paragraph_properties(paragraph)
    alignment = get_or_add(ppr, qn("jc"))
    alignment.set(qn("val"), value)


def set_row_bold(row: etree._Element) -> None:
    for run in row.xpath(".//w:r", namespaces=NS):
        rpr = ensure_run_properties(run)
        bold = get_or_add(rpr, qn("b"))
        bold.set(qn("val"), "1")
        bold_cs = get_or_add(rpr, qn("bCs"))
        bold_cs.set(qn("val"), "1")


def run_is_bold(run: etree._Element) -> bool:
    bold = run.find("./w:rPr/w:b", namespaces=NS)
    if bold is None:
        return False
    return bold.get(qn("val"), "1").casefold() not in {"0", "false", "off"}


def row_is_bold(row: etree._Element) -> bool:
    text_runs = [
        run
        for run in row.xpath(".//w:r", namespaces=NS)
        if run.xpath(".//w:t/text()", namespaces=NS)
    ]
    return bool(text_runs) and all(run_is_bold(run) for run in text_runs)


def parse_p_value(value: str) -> float | None:
    token = value.strip().replace(" ", "")
    token = token.replace("≤", "<=").replace("＜", "<").replace("＝", "=")
    if not token:
        return None
    if token.casefold() in {"na", "n/a", "—", "-", "notapplicable"}:
        return None
    match = re.search(
        r"(?:p(?:-?value)?\s*[=:<>≤]*)?([0-9]*\.[0-9]+|[01])",
        token,
        flags=re.I,
    )
    if not match:
        return None
    try:
        numeric = float(match.group(1))
    except ValueError:
        return None
    if 0 <= numeric <= 1:
        return numeric
    return None


def find_p_value_column(table: etree._Element) -> int | None:
    rows = table.xpath("./w:tr", namespaces=NS)
    if not rows:
        return None
    headers = [
        cell_text(cell).casefold().replace(" ", "").replace("-", "")
        for cell in rows[0].xpath("./w:tc", namespaces=NS)
    ]
    matches = [
        index
        for index, header in enumerate(headers)
        if header in {"p", "pvalue", "p值", "pvalue*"}
        or re.fullmatch(r"p(?:value|值).*", header)
    ]
    return matches[0] if len(matches) == 1 else None


def significant_rows(
    table: etree._Element, threshold: float = 0.05
) -> list[tuple[int, etree._Element, float]]:
    p_column = find_p_value_column(table)
    if p_column is None:
        return []
    results: list[tuple[int, etree._Element, float]] = []
    rows = table.xpath("./w:tr", namespaces=NS)
    for row_index, row in enumerate(rows[1:], start=2):
        cells = row.xpath("./w:tc", namespaces=NS)
        if p_column >= len(cells):
            continue
        raw = cell_text(cells[p_column])
        numeric = parse_p_value(raw)
        if numeric is not None and numeric < threshold:
            results.append((row_index, row, numeric))
    return results


def set_border(
    parent: etree._Element,
    name: str,
    *,
    value: str,
    size: str = "8",
    color: str = "000000",
) -> None:
    border = get_or_add(parent, qn(name))
    border.set(qn("val"), value)
    if value not in {"nil", "none"}:
        border.set(qn("sz"), size)
        border.set(qn("space"), "0")
        border.set(qn("color"), color)


def apply_three_line_table(table: etree._Element) -> None:
    tbl_pr = get_or_add_first(table, qn("tblPr"))
    borders = get_or_add(tbl_pr, qn("tblBorders"))
    set_border(borders, "top", value="single")
    set_border(borders, "bottom", value="single")
    for name in ("left", "right", "insideH", "insideV"):
        set_border(borders, name, value="nil")

    rows = table.xpath("./w:tr", namespaces=NS)
    if not rows:
        return
    for cell in rows[0].xpath("./w:tc", namespaces=NS):
        tc_pr = get_or_add_first(cell, qn("tcPr"))
        tc_borders = get_or_add(tc_pr, qn("tcBorders"))
        set_border(tc_borders, "bottom", value="single")
        for name in ("left", "right", "insideH", "insideV"):
            set_border(tc_borders, name, value="nil")


def table_has_three_line_style(table: etree._Element) -> bool:
    borders = table.find("./w:tblPr/w:tblBorders", namespaces=NS)
    if borders is None:
        return False

    def border_value(name: str) -> str | None:
        element = borders.find(f"./w:{name}", namespaces=NS)
        return None if element is None else element.get(qn("val"))

    if border_value("top") not in {"single", "thick", "double"}:
        return False
    if border_value("bottom") not in {"single", "thick", "double"}:
        return False
    for name in ("left", "right", "insideH", "insideV"):
        if border_value(name) not in {None, "nil", "none"}:
            return False

    rows = table.xpath("./w:tr", namespaces=NS)
    if not rows:
        return False
    header_cells = rows[0].xpath("./w:tc", namespaces=NS)
    if not header_cells:
        return False
    for cell in header_cells:
        bottom = cell.find("./w:tcPr/w:tcBorders/w:bottom", namespaces=NS)
        if bottom is None or bottom.get(qn("val")) not in {
            "single",
            "thick",
            "double",
        }:
            return False
    return True


def extract_field_instructions(root: etree._Element) -> list[str]:
    instructions: list[str] = []
    active: list[list[str]] = []
    for element in root.iter():
        if element.tag == qn("fldSimple"):
            instruction = element.get(qn("instr"))
            if instruction:
                instructions.append(instruction)
        elif element.tag == qn("fldChar"):
            field_type = element.get(qn("fldCharType"), "").casefold()
            if field_type == "begin":
                active.append([])
            elif field_type == "end" and active:
                instructions.append("".join(active.pop()))
        elif element.tag == qn("instrText"):
            text = element.text or ""
            if active:
                active[-1].append(text)
            elif text:
                instructions.append(text)
    for unfinished in active:
        if unfinished:
            instructions.append("".join(unfinished))
    return instructions


def field_inventory(package: dict[str, bytes]) -> dict[str, list[str]]:
    inventory: dict[str, list[str]] = {}
    for name, data in package.items():
        if not name.startswith("word/") or not name.endswith(".xml"):
            continue
        try:
            root = parse_xml(data)
        except etree.XMLSyntaxError:
            continue
        fields = extract_field_instructions(root)
        if fields:
            inventory[name] = fields
    return inventory


def zotero_inventory(package: dict[str, bytes]) -> dict[str, list[str]]:
    return {
        name: [field for field in fields if "ZOTERO_" in field.upper()]
        for name, fields in field_inventory(package).items()
        if any("ZOTERO_" in field.upper() for field in fields)
    }


def zotero_reference_count(instruction: str) -> int | None:
    if "ZOTERO_ITEM" not in instruction.upper():
        return None
    brace = instruction.find("{")
    if brace < 0:
        return None
    try:
        data, _ = json.JSONDecoder().raw_decode(instruction[brace:])
    except json.JSONDecodeError:
        return None
    items = data.get("citationItems")
    return len(items) if isinstance(items, list) else None


def package_plain_text(package: dict[str, bytes]) -> str:
    parts: list[str] = []
    ordered_names = ["word/document.xml"]
    ordered_names.extend(
        sorted(
            name
            for name in package
            if name.startswith("word/")
            and name.endswith(".xml")
            and name != "word/document.xml"
        )
    )
    for name in ordered_names:
        data = package.get(name)
        if not data:
            continue
        try:
            root = parse_xml(data)
        except etree.XMLSyntaxError:
            continue
        parts.extend(root.xpath(".//w:t/text()", namespaces=NS))
    return "\n".join(parts)


def format_parts(package: dict[str, bytes]) -> list[str]:
    preferred = [
        "word/document.xml",
        "word/styles.xml",
        "word/footnotes.xml",
        "word/endnotes.xml",
    ]
    preferred.extend(
        sorted(
            name
            for name in package
            if re.fullmatch(r"word/(?:header|footer)\d+\.xml", name)
        )
    )
    return [name for name in preferred if name in package]


def count_list_runs(root: etree._Element) -> int:
    longest = 0
    current = 0
    for paragraph in root.xpath(".//w:body/w:p", namespaces=NS):
        if paragraph.find("./w:pPr/w:numPr", namespaces=NS) is not None:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def document_has_title_page(root: etree._Element) -> bool:
    return bool(root.xpath(".//w:sectPr/w:titlePg", namespaces=NS))


def paragraph_has_page_break(paragraph: etree._Element) -> bool:
    if paragraph.xpath(".//w:br[@w:type='page']", namespaces=NS):
        return True
    return bool(paragraph.xpath("./w:pPr/w:pageBreakBefore", namespaces=NS))


def likely_independent_title_page(root: etree._Element) -> bool:
    paragraphs = root.xpath(".//w:body/w:p", namespaces=NS)
    seen_text = 0
    for paragraph in paragraphs[:20]:
        if paragraph_text(paragraph):
            seen_text += 1
        if paragraph_has_page_break(paragraph) and 1 <= seen_text <= 8:
            return True
    return False


def list_all_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not path.name.startswith("~$")
    )
