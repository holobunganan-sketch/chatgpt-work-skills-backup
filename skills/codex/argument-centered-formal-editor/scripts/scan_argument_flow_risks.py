#!/usr/bin/env python3
"""扫描正式文本中的主线、来源适配、推理桥和具体表达候选风险。

支持 TXT、Markdown、LaTeX、RST、CSV、TSV 和 DOCX。命中结果只用于人工语义复核。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".tex", ".latex", ".rst", ".csv", ".tsv"}


@dataclass
class Finding:
    finding_id: str
    category: str
    rule_id: str
    paragraph_number: int
    excerpt: str
    rationale: str
    review_question: str
    disposition: str = "needs_contextual_review"


PROCESS_PATTERNS = [
    (r"(?:为了|为)(?:回应|回复|满足)(?:审稿|评审|反馈|批注|意见|要求)", "出现反馈处理过程"),
    (r"根据(?:用户|作者|审稿人|评审者|专家|老师|内部)(?:的)?(?:要求|批注|反馈|意见|建议)", "出现内部来源"),
    (r"(?:本次|这一处|此处)(?:修改|修订|调整|新增|删除)", "出现编辑操作"),
    (r"(?:待确认|待补充|待完善|待更新|TODO|TBD|FIXME)", "出现待办或占位内容"),
    (r"(?:to address|in response to|as requested by) (?:the )?(?:reviewer|comment|feedback)", "出现英文反馈处理过程"),
]

FORBIDDEN_TURN_PATTERNS = [
    r"不是[^。；!?]{0,80}而是",
    r"并非[^。；!?]{0,80}而是",
    r"与其说[^。；!?]{0,80}不如说",
    r"不只[^。；!?]{0,80}(?:还|也)",
    r"不仅[^。；!?]{0,80}(?:更|还|也)",
    r"表面上[^。；!?]{0,80}本质上",
    r"真正关键的",
]

FORMULAIC_OPENERS = re.compile(
    r"^(此外|同时|另外|进一步|具体而言|值得注意的是|需要指出的是|应当指出的是|综上所述|不难发现|显而易见|毋庸置疑|从某种意义上说|Moreover|Furthermore|Additionally|Notably|Specifically)[，,:：\s]",
    re.IGNORECASE,
)

DEFENSIVE_PATTERNS = [
    r"(?:无法|不能)(?:据此)?(?:确定|证明|推断|得出|建立)",
    r"(?:不代表|不应解释为|不得据此认为)",
    r"(?:仅限于|仅用于|只能说明|需(?:要)?谨慎解读)",
    r"(?:cannot|does not) (?:establish|prove|determine|demonstrate)",
    r"should not be (?:interpreted|understood) as",
]

ABSTRACT_TERMS = re.compile(
    r"(机制|维度|层面|路径|框架|赋能|协同|抓手|范式|逻辑|价值|意义|体系|格局|能动性|mechanism|dimension|framework|paradigm|synergy|empowerment)",
    re.IGNORECASE,
)

GENERIC_VALUE_PHRASES = re.compile(
    r"(具有(?:重要|重大|积极)?意义|具有(?:重要|重大)?价值|提供(?:了)?(?:新的)?视角|丰富(?:了)?(?:相关)?研究|为后续研究提供(?:了)?参考|值得进一步关注|plays? an important role|is of great significance)",
    re.IGNORECASE,
)

CITATION_PATTERN = re.compile(
    r"(?:"
    r"\[(?=[^\]\r\n]*@[A-Za-z0-9_:.+\-]+)[^\]\r\n]+\]"
    r"|\\(?:cite|citep|citet|autocite|parencite|textcite)\*?(?:\[[^\]]*\]){0,2}\{[^}]+\}"
    r"|\[[0-9,;\-–—\s]+\]"
    r"|\([A-Z][A-Za-z'’\-]+(?:\s+et\s+al\.)?,?\s+(?:19|20)\d{2}[a-z]?\)"
    r"|(?:^|\s)\d{1,3}(?:[-–]\d{1,3})?(?=[,.;，。；])"
    r")"
)

RELATION_MARKERS = re.compile(
    r"(因此|因而|由于|从而|导致|降低|增加|解释|表明|提示|支持|相反|相比|一致|差异|取决于|随后|进而|because|therefore|thus|whereas|compared with|consistent with|suggests?|indicates?|supports?|explains?|increases?|reduces?)",
    re.IGNORECASE,
)

SOURCE_LED_OPENERS = re.compile(
    r"^(?:[A-Z][A-Za-z'’\-]+(?:(?:\s+et\s+al\.)|等)?|[\u4e00-\u9fff]{1,12}(?:等|团队)|某项研究|一项研究|研究人员|作者)(?:发现|报道|指出|认为|观察到|显示|提出| found| reported| observed| showed| suggested)",
    re.IGNORECASE,
)

MECHANICAL_EVIDENCE_OPENERS = re.compile(
    r"^(?:这|该|这些|上述)(?:一|项|些)?(?:结果|发现|证据|研究|数据)?(?:表明|提示|说明|支持)|^(?:This|These|Such) (?:result|results|finding|findings|evidence|study|studies|data) (?:suggests?|indicates?|shows?|supports?)",
    re.IGNORECASE,
)

NUMERIC_PATTERN = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:倍|例|人|项|年|月|周|天|小时|元)|\b(?:19|20)\d{2}\b|\b\d+(?:\.\d+)?\s*(?:patients?|participants?|cases?|studies?|years?|weeks?|days?)\b)",
    re.IGNORECASE,
)


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def read_text_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法使用 UTF-8、UTF-16 或 GB18030 解码文本")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError(f"无法读取 DOCX 正文：{exc}") from exc
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"DOCX 正文 XML 无法解析：{exc}") from exc
    paragraphs: list[str] = []
    for paragraph in root.iter():
        if local_name(paragraph.tag) != "p":
            continue
        chunks: list[str] = []

        def collect(node: ET.Element, is_root: bool = False) -> None:
            if not is_root and local_name(node.tag) == "p":
                return
            name = local_name(node.tag)
            if name == "t" and node.text:
                chunks.append(node.text)
            elif name == "tab":
                chunks.append("\t")
            elif name in {"br", "cr"}:
                chunks.append("\n")
            for child in node:
                collect(child)

        collect(paragraph, is_root=True)
        text = "".join(chunks).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def load_source(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return extract_docx_text(path), "docx"
    if suffix in TEXT_SUFFIXES or not suffix:
        return read_text_file(path), "text"
    raise ValueError("仅支持 DOCX、TXT、Markdown、LaTeX、RST、CSV 或 TSV")


def split_paragraphs(text: str) -> list[str]:
    blocks = re.split(r"(?:\r?\n){2,}", text)
    paragraphs = [re.sub(r"\s+", " ", block).strip() for block in blocks]
    return [paragraph for paragraph in paragraphs if paragraph]


def split_sentences(paragraph: str) -> list[str]:
    pieces = re.split(r"(?<=[。！？!?])\s*|(?<=[.;])\s+(?=[A-Z])", paragraph)
    return [piece.strip() for piece in pieces if piece.strip()]


def clipped(text: str, limit: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def add_finding(
    findings: list[Finding],
    category: str,
    rule_id: str,
    paragraph_number: int,
    excerpt: str,
    rationale: str,
    review_question: str,
) -> None:
    findings.append(
        Finding(
            finding_id=f"R{len(findings) + 1:04d}",
            category=category,
            rule_id=rule_id,
            paragraph_number=paragraph_number,
            excerpt=clipped(excerpt),
            rationale=rationale,
            review_question=review_question,
        )
    )


def sentence_lengths(sentence: str) -> tuple[int, int]:
    chinese_chars = len(re.findall(r"[\u3400-\u9fff]", sentence))
    english_words = len(re.findall(r"\b[A-Za-z][A-Za-z'’\-]*\b", sentence))
    return chinese_chars, english_words


def longest_repeated_chinese_phrase(paragraph: str) -> tuple[str, int] | None:
    compact = re.sub(r"\[[^\]]+\]|\([^)]*\d{4}[^)]*\)", "", paragraph)
    function_chars = set("的在以为与及和")
    for length in range(10, 4, -1):
        phrases = Counter(
            compact[index : index + length]
            for index in range(0, max(0, len(compact) - length + 1))
            if re.fullmatch(r"[\u3400-\u9fff]+", compact[index : index + length])
            and compact[index] not in function_chars
            and compact[index + length - 1] not in function_chars
        )
        repeated = [
            (phrase, count)
            for phrase, count in phrases.items()
            if count >= 2
        ]
        if repeated:
            return max(repeated, key=lambda item: (len(item[0]), item[1]))
    return None


def risk_counts(text: str) -> dict[str, int]:
    paragraphs = split_paragraphs(text)
    findings = scan_paragraphs(paragraphs)
    return dict(Counter(finding.rule_id for finding in findings))


def scan_paragraphs(paragraphs: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for paragraph_number, paragraph in enumerate(paragraphs, start=1):
        sentences = split_sentences(paragraph)

        for pattern, rationale in PROCESS_PATTERNS:
            if match := re.search(pattern, paragraph, re.IGNORECASE):
                add_finding(
                    findings,
                    "过程痕迹",
                    "PROCESS_TRACE",
                    paragraph_number,
                    paragraph[max(0, match.start() - 40) : match.end() + 80],
                    rationale,
                    "该内容是否只描述反馈或编辑过程？",
                )

        for pattern in FORBIDDEN_TURN_PATTERNS:
            if match := re.search(pattern, paragraph, re.IGNORECASE):
                add_finding(
                    findings,
                    "模板化转折叙事",
                    "FORBIDDEN_TURN_TEMPLATE",
                    paragraph_number,
                    paragraph[max(0, match.start() - 30) : match.end() + 50],
                    "命中禁用的转折叙事结构。",
                    "能否改为直接陈述、并列说明、因果说明或具体事实？",
                )

        formulaic_sentences = [s for s in sentences if FORMULAIC_OPENERS.search(s)]
        if formulaic_sentences:
            add_finding(
                findings,
                "机械连接",
                "FORMULAIC_OPENER",
                paragraph_number,
                " ".join(formulaic_sentences[:3]),
                "句首连接语可能代替了具体推理。",
                "删除连接语后，相邻句之间的关系是否仍能复述？",
            )

        defensive_hits = sum(
            len(re.findall(pattern, paragraph, re.IGNORECASE)) for pattern in DEFENSIVE_PATTERNS
        )
        if defensive_hits:
            add_finding(
                findings,
                "防御性或边界表述",
                "DEFENSIVE_PROSE",
                paragraph_number,
                paragraph,
                f"检测到 {defensive_hits} 处候选防御性或边界表述。",
                "该内容是否由本次编辑新增？本技能应当停止主动增写此类内容。",
            )

        source_led = [sentence for sentence in sentences if SOURCE_LED_OPENERS.search(sentence)]
        if len(source_led) >= 2:
            add_finding(
                findings,
                "来源主导写作",
                "SOURCE_LED_SEQUENCE",
                paragraph_number,
                " ".join(source_led[:4]),
                f"同一段有 {len(source_led)} 个句子以作者或研究为主体。",
                "这些来源能否围绕一个本文判断综合组织？",
            )

        mechanical = [
            sentence for sentence in sentences if MECHANICAL_EVIDENCE_OPENERS.search(sentence)
        ]
        if len(mechanical) >= 2:
            add_finding(
                findings,
                "机械证据解释",
                "MECHANICAL_EVIDENCE_EXPLANATION",
                paragraph_number,
                " ".join(mechanical[:3]),
                "多次使用相同解释提示语。",
                "能否用谓语、比较结构或句序直接承担解释？",
            )

        generic = [sentence for sentence in sentences if GENERIC_VALUE_PHRASES.search(sentence)]
        if generic:
            add_finding(
                findings,
                "通用评价",
                "GENERIC_VALUE_CLAIM",
                paragraph_number,
                " ".join(generic[:3]),
                "评价句缺少对具体判断、对象或结果的说明。",
                "该句具体改变什么判断或支持什么后续动作？",
            )

        repeated_phrase = longest_repeated_chinese_phrase(paragraph)
        if repeated_phrase:
            phrase, count = repeated_phrase
            add_finding(
                findings,
                "段落回环",
                "REPEATED_PHRASE_LOOP",
                paragraph_number,
                paragraph,
                f"候选短语“{phrase}”重复出现 {count} 次。",
                "是否存在提前判断、引证重复和同义总结？专业术语的必要复现可以保留。",
            )

        abstract_total = 0
        for sentence in sentences:
            abstract_count = len(ABSTRACT_TERMS.findall(sentence))
            abstract_total += abstract_count
            if abstract_count >= 3:
                add_finding(
                    findings,
                    "抽象表达",
                    "ABSTRACT_DENSITY",
                    paragraph_number,
                    sentence,
                    f"句中出现 {abstract_count} 个候选抽象术语。",
                    "能否写明主体、行为、变量、变化方向和结果？",
                )
            chinese_chars, english_words = sentence_lengths(sentence)
            if chinese_chars >= 120 or english_words >= 55:
                add_finding(
                    findings,
                    "句子负载",
                    "LONG_SENTENCE",
                    paragraph_number,
                    sentence,
                    f"句子约含 {chinese_chars} 个中文字符和 {english_words} 个英文词。",
                    "句子是否承担多个推理环节？拆分后能否保持关系清楚？",
                )
        if abstract_total >= 6 and len(sentences) >= 2:
            add_finding(
                findings,
                "段落抽象度",
                "ABSTRACT_PARAGRAPH",
                paragraph_number,
                paragraph,
                f"段落累计出现 {abstract_total} 个候选抽象术语。",
                "段落中心判断能否改写为具体对象、动作和结果？",
            )

        citations = CITATION_PATTERN.findall(paragraph)
        if len(sentences) >= 3 and len(citations) >= 2:
            relations = RELATION_MARKERS.findall(paragraph)
            if len(relations) <= 1:
                add_finding(
                    findings,
                    "证据拼接",
                    "EVIDENCE_WITHOUT_RELATION",
                    paragraph_number,
                    paragraph,
                    f"段落含 {len(citations)} 个候选引用，具体关系标记较少。",
                    "每项引用完成什么任务？证据顺序是否服从推理？",
                )

        numeric_items = NUMERIC_PATTERN.findall(paragraph)
        if len(sentences) >= 3 and len(numeric_items) >= 3:
            relations = RELATION_MARKERS.findall(paragraph)
            if len(relations) <= 1:
                add_finding(
                    findings,
                    "数值堆积",
                    "NUMERIC_WITHOUT_RELATION",
                    paragraph_number,
                    paragraph,
                    f"段落含 {len(numeric_items)} 个候选数值，具体关系标记较少。",
                    "这些数值分别量化哪个判断？顺序是否推动段落？",
                )
    return findings


def build_payload(
    path: Path,
    source_type: str,
    paragraphs: list[str],
    findings: list[Finding],
    total: int,
) -> dict:
    return {
        "status": "candidates_only",
        "notice": "所有命中均需结合全文语义人工复核。",
        "source": str(path.resolve()),
        "source_type": source_type,
        "paragraphs_scanned": len(paragraphs),
        "candidate_count": len(findings),
        "candidate_count_total": total,
        "truncated": total > len(findings),
        "findings": [asdict(finding) for finding in findings],
    }


def render_text(payload: dict) -> str:
    lines = [
        "主线与证据整合候选风险扫描",
        "以下项目需要人工语义复核。",
        f"来源：{payload['source']}",
        f"扫描段落：{payload['paragraphs_scanned']}；候选项：{payload['candidate_count_total']}",
    ]
    if not payload["findings"]:
        lines.append("当前规则未命中候选风险。")
        return "\n".join(lines)
    for finding in payload["findings"]:
        lines.extend(
            [
                "",
                f"[{finding['finding_id']}] {finding['category']} / {finding['rule_id']} / 第 {finding['paragraph_number']} 段",
                f"片段：{finding['excerpt']}",
                f"理由：{finding['rationale']}",
                f"复核：{finding['review_question']}",
            ]
        )
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描主线、来源适配和推理桥候选风险")
    parser.add_argument("source", type=Path, help="待扫描文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--extract-only", action="store_true", help="仅输出抽取正文")
    parser.add_argument("--max-findings", type=int, default=200, help="最多输出候选项")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    configure_console()
    args = parse_args(argv)
    if args.max_findings < 1:
        print("错误：--max-findings 必须大于 0", file=sys.stderr)
        return 2
    if not args.source.is_file():
        print(f"错误：文件不存在：{args.source}", file=sys.stderr)
        return 2
    try:
        text, source_type = load_source(args.source)
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    if args.extract_only:
        print(text)
        return 0
    paragraphs = split_paragraphs(text)
    all_findings = scan_paragraphs(paragraphs)
    payload = build_payload(
        args.source,
        source_type,
        paragraphs,
        all_findings[: args.max_findings],
        len(all_findings),
    )
    print(
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else render_text(payload)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
