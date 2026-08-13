from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


READING_STATUSES = {
    "full_text",
    "relevant_sections",
    "abstract_only",
    "metadata_only",
    "unavailable",
}
SUBSTANTIVE_READING = {"full_text", "relevant_sections"}
DECISIONS = {"include", "move", "background_only", "exclude"}
EVIDENCE_TASKS = {
    "establish_fact",
    "quantify",
    "define",
    "explain",
    "compare",
    "distinguish",
    "bridge",
    "method",
    "counterpoint",
    "support_action",
}
CONTINUITY_VALUES = {"continuous", "requires_adaptation", "incompatible"}
CONTINUITY_FIELDS = {
    "subject",
    "terminology",
    "tone",
    "abstraction_level",
    "sentence_function",
}
SUBSTANTIVE_FIELDS = {
    "mainline_node",
    "section",
    "evidence_task",
    "minimum_usable_proposition",
    "upstream_anchor",
    "missing_relation",
    "downstream_advance",
    "citation_entry_point",
}


def add_issue(
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


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def validate_mainline(data: dict, issues: list[dict]) -> set[str]:
    mainline = data.get("document_mainline")
    if not isinstance(mainline, dict):
        add_issue(
            issues,
            "error",
            "MAINLINE_MISSING",
            "document_mainline must be an object.",
            "document_mainline",
        )
        return set()
    for field in ("core_question", "target_answer"):
        if not nonempty(mainline.get(field)):
            add_issue(
                issues,
                "error",
                "MAINLINE_FIELD",
                f"{field} must be specific and non-empty.",
                f"document_mainline.{field}",
            )
    nodes = mainline.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        add_issue(
            issues,
            "error",
            "MAINLINE_NODES",
            "At least one mainline node is required.",
            "document_mainline.nodes",
        )
        return set()

    node_ids: set[str] = set()
    next_links: list[tuple[str, str]] = []
    for index, node in enumerate(nodes, start=1):
        location = f"document_mainline.nodes[{index}]"
        if not isinstance(node, dict):
            add_issue(
                issues, "error", "NODE_TYPE", "Node must be an object.", location
            )
            continue
        node_id = node.get("id")
        if not nonempty(node_id):
            add_issue(
                issues, "error", "NODE_ID", "Node id is required.", location
            )
            continue
        if node_id in node_ids:
            add_issue(
                issues,
                "error",
                "NODE_DUPLICATE",
                "Mainline node ids must be unique.",
                location,
            )
        node_ids.add(node_id)
        if not nonempty(node.get("judgment")):
            add_issue(
                issues,
                "error",
                "NODE_JUDGMENT",
                "Each node needs a specific judgment.",
                location,
            )
        next_node = node.get("next_node")
        if next_node is not None:
            if not nonempty(next_node):
                add_issue(
                    issues,
                    "error",
                    "NEXT_NODE",
                    "next_node must be a node id or null.",
                    location,
                )
            else:
                next_links.append((node_id, next_node))

    for node_id, next_node in next_links:
        if next_node not in node_ids:
            add_issue(
                issues,
                "error",
                "NEXT_NODE_UNKNOWN",
                f"{next_node} is not a declared mainline node.",
                f"node {node_id}",
            )
    return node_ids


def validate_passages(
    source: dict, issues: list[dict], location: str
) -> list[dict]:
    passages = source.get("passages")
    if not isinstance(passages, list):
        add_issue(
            issues,
            "error",
            "PASSAGES_TYPE",
            "passages must be an array.",
            location,
        )
        return []
    valid: list[dict] = []
    for index, passage in enumerate(passages, start=1):
        passage_location = f"{location}.passages[{index}]"
        if not isinstance(passage, dict):
            add_issue(
                issues,
                "error",
                "PASSAGE_TYPE",
                "Passage must be an object.",
                passage_location,
            )
            continue
        if not nonempty(passage.get("locator")):
            add_issue(
                issues,
                "error",
                "PASSAGE_LOCATOR",
                "Claim-level evidence requires an exact locator.",
                passage_location,
            )
        if not nonempty(passage.get("supported_proposition")):
            add_issue(
                issues,
                "error",
                "PASSAGE_PROPOSITION",
                "Passage must state the exact supported proposition.",
                passage_location,
            )
        if nonempty(passage.get("locator")) and nonempty(
            passage.get("supported_proposition")
        ):
            valid.append(passage)
    return valid


def validate_continuity(
    use: dict, issues: list[dict], location: str, decision: str
) -> None:
    continuity = use.get("continuity")
    if not isinstance(continuity, dict):
        add_issue(
            issues,
            "error",
            "CONTINUITY_MISSING",
            "Substantive use requires a continuity check.",
            location,
        )
        return
    requires_adaptation = False
    for field in CONTINUITY_FIELDS:
        value = continuity.get(field)
        if value not in CONTINUITY_VALUES:
            add_issue(
                issues,
                "error",
                "CONTINUITY_VALUE",
                f"{field} must use a permitted continuity value.",
                location,
            )
            continue
        if value == "requires_adaptation":
            requires_adaptation = True
        if value == "incompatible" and decision in {"include", "move"}:
            add_issue(
                issues,
                "error",
                "CONTINUITY_INCOMPATIBLE",
                "An incompatible source cannot be approved for substantive use.",
                location,
            )
    if requires_adaptation and not nonempty(use.get("adaptation_instruction")):
        add_issue(
            issues,
            "error",
            "ADAPTATION_MISSING",
            "Continuity repair requires an adaptation instruction.",
            location,
        )


def validate_source(
    source: dict,
    index: int,
    node_ids: set[str],
    issues: list[dict],
) -> int:
    location = f"sources[{index}]"
    if not isinstance(source, dict):
        add_issue(
            issues, "error", "SOURCE_TYPE", "Source must be an object.", location
        )
        return 0
    source_id = source.get("source_id")
    if not nonempty(source_id):
        add_issue(
            issues, "error", "SOURCE_ID", "source_id is required.", location
        )
    if not nonempty(source.get("citation")):
        add_issue(
            issues, "error", "CITATION", "citation is required.", location
        )
    reading_status = source.get("reading_status")
    if reading_status not in READING_STATUSES:
        add_issue(
            issues,
            "error",
            "READING_STATUS",
            "reading_status is invalid.",
            location,
        )
    passages = validate_passages(source, issues, location)
    uses = source.get("uses")
    if not isinstance(uses, list):
        add_issue(
            issues,
            "error",
            "USES_TYPE",
            "uses must be an array.",
            location,
        )
        return 0

    included = 0
    for use_index, use in enumerate(uses, start=1):
        use_location = f"{location}.uses[{use_index}]"
        if not isinstance(use, dict):
            add_issue(
                issues,
                "error",
                "USE_TYPE",
                "Use must be an object.",
                use_location,
            )
            continue
        decision = use.get("decision")
        if decision not in DECISIONS:
            add_issue(
                issues,
                "error",
                "DECISION",
                "Use decision is invalid.",
                use_location,
            )
            continue
        if decision not in {"include", "move"}:
            continue
        included += 1
        if reading_status not in SUBSTANTIVE_READING:
            add_issue(
                issues,
                "error",
                "INSUFFICIENT_READING",
                "Substantive use requires full text or complete claim-relevant sections.",
                use_location,
            )
        if not passages:
            add_issue(
                issues,
                "error",
                "NO_CLAIM_LEVEL_PASSAGE",
                "Substantive use requires at least one exact supporting passage.",
                use_location,
            )
        for field in SUBSTANTIVE_FIELDS:
            if not nonempty(use.get(field)):
                add_issue(
                    issues,
                    "error",
                    "SUBSTANTIVE_FIELD",
                    f"{field} is required for substantive use.",
                    use_location,
                )
        if use.get("mainline_node") not in node_ids:
            add_issue(
                issues,
                "error",
                "MAINLINE_NODE_UNKNOWN",
                "Use must map to a declared mainline node.",
                use_location,
            )
        if use.get("evidence_task") not in EVIDENCE_TASKS:
            add_issue(
                issues,
                "error",
                "EVIDENCE_TASK",
                "Use must have one permitted evidence task.",
                use_location,
            )
        upstream = use.get("upstream_anchor")
        downstream = use.get("downstream_advance")
        proposition = use.get("minimum_usable_proposition")
        if nonempty(upstream) and nonempty(downstream):
            if normalize(upstream) == normalize(downstream):
                add_issue(
                    issues,
                    "error",
                    "NO_ARGUMENT_ADVANCE",
                    "The downstream judgment must advance beyond the upstream judgment.",
                    use_location,
                )
        if nonempty(proposition) and nonempty(downstream):
            if normalize(proposition) == normalize(downstream):
                add_issue(
                    issues,
                    "error",
                    "EVIDENCE_RESTATED",
                    "The downstream judgment cannot merely repeat the source proposition.",
                    use_location,
                )
        validate_continuity(use, issues, use_location, decision)
    return included


def validate(data: dict) -> dict:
    issues: list[dict] = []
    if data.get("schema_version") != 1:
        add_issue(
            issues,
            "error",
            "SCHEMA_VERSION",
            "schema_version must be 1.",
            "schema_version",
        )
    node_ids = validate_mainline(data, issues)
    sources = data.get("sources")
    if not isinstance(sources, list):
        add_issue(
            issues,
            "error",
            "SOURCES_TYPE",
            "sources must be an array.",
            "sources",
        )
        sources = []

    source_ids: set[str] = set()
    substantive_uses = 0
    for index, source in enumerate(sources, start=1):
        if isinstance(source, dict):
            source_id = source.get("source_id")
            if nonempty(source_id):
                if source_id in source_ids:
                    add_issue(
                        issues,
                        "error",
                        "SOURCE_DUPLICATE",
                        "source_id values must be unique.",
                        f"sources[{index}]",
                    )
                source_ids.add(source_id)
        substantive_uses += validate_source(source, index, node_ids, issues)

    if sources and substantive_uses == 0:
        add_issue(
            issues,
            "warning",
            "NO_SUBSTANTIVE_SOURCE",
            "No source has passed internal alignment for substantive use.",
            "sources",
        )

    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    return {
        "status": "pass" if errors == 0 else "fail",
        "counts": {
            "mainline_nodes": len(node_ids),
            "sources": len(sources),
            "substantive_uses": substantive_uses,
            "errors": errors,
            "warnings": warnings,
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the internal argument-evidence alignment map."
    )
    parser.add_argument("alignment_map", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.alignment_map.read_text(encoding="utf-8"))
        report = validate(data)
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
