#!/usr/bin/env python3
"""Validate page blueprint JSON files for the presentation-production-system skill."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL_KEYS = [
    "page_id",
    "deck_position",
    "page_role",
    "narrative_function",
    "page_type",
    "visual_center",
    "graphic_priority",
    "svg_needed",
    "svg_module_candidate",
    "text_density",
    "ppt_native_blocks",
    "chart_or_diagram_goal",
    "key_message",
    "what_must_be_seen_first",
    "what_should_remain_outside_svg",
    "generic_consulting_layout_forbidden",
    "reuse_candidate_module",
    "information_loss_if_text_only",
    "render_strategy",
    "graphic_complexity",
    "text_graphic_ratio",
    "title_zone",
    "main_visual_zone",
    "explanation_zone",
    "conclusion_zone",
    "reference_zone",
    "style_keywords",
    "avoid_list",
    "open_questions",
]

REQUIRED_RENDER_STRATEGIES = {"native-ppt", "hybrid", "data-led", "svg-focused"}
REQUIRED_GRAPHIC_PRIORITIES = {"high", "medium", "low"}
REQUIRED_TEXT_DENSITIES = {"low", "medium", "high"}


def validate_blueprint(data: dict) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"Missing top-level key: {key}")

    render_strategy = data.get("render_strategy")
    if render_strategy and render_strategy not in REQUIRED_RENDER_STRATEGIES:
        errors.append(
            "Invalid render_strategy. Expected one of: "
            + ", ".join(sorted(REQUIRED_RENDER_STRATEGIES))
        )

    if "key_message" in data and not str(data["key_message"]).strip():
        errors.append("key_message must be non-empty")

    if "what_must_be_seen_first" in data and not str(data["what_must_be_seen_first"]).strip():
        errors.append("what_must_be_seen_first must be non-empty")

    if "information_loss_if_text_only" in data and not str(data["information_loss_if_text_only"]).strip():
        errors.append("information_loss_if_text_only must be non-empty")

    ratio = str(data.get("text_graphic_ratio", ""))
    if ratio and ":" not in ratio:
        errors.append("text_graphic_ratio must use '%text:%graphic' format, e.g. '35:65'")

    graphic_priority = data.get("graphic_priority")
    if graphic_priority and graphic_priority not in REQUIRED_GRAPHIC_PRIORITIES:
        errors.append(
            "Invalid graphic_priority. Expected one of: "
            + ", ".join(sorted(REQUIRED_GRAPHIC_PRIORITIES))
        )

    text_density = data.get("text_density")
    if text_density and text_density not in REQUIRED_TEXT_DENSITIES:
        errors.append(
            "Invalid text_density. Expected one of: "
            + ", ".join(sorted(REQUIRED_TEXT_DENSITIES))
        )

    ppt_native_blocks = data.get("ppt_native_blocks")
    if ppt_native_blocks is not None and not isinstance(ppt_native_blocks, list):
        errors.append("ppt_native_blocks must be an array")

    outside_svg = data.get("what_should_remain_outside_svg")
    if outside_svg is not None and not isinstance(outside_svg, list):
        errors.append("what_should_remain_outside_svg must be an array")

    title_zone = data.get("title_zone")
    if title_zone is not None and not isinstance(title_zone, dict):
        errors.append("title_zone must be an object")

    main_visual_zone = data.get("main_visual_zone")
    if main_visual_zone is not None:
        if not isinstance(main_visual_zone, dict):
            errors.append("main_visual_zone must be an object")
        else:
            if "svg_scope" not in main_visual_zone:
                errors.append("main_visual_zone.svg_scope is required")
            if "native_ppt_scope" not in main_visual_zone:
                errors.append("main_visual_zone.native_ppt_scope is required")

    if data.get("svg_needed") is True:
        svg_scope = []
        if isinstance(main_visual_zone, dict):
            svg_scope = main_visual_zone.get("svg_scope", [])
        if not svg_scope:
            errors.append("main_visual_zone.svg_scope must be non-empty when svg_needed is true")

    avoid_list = data.get("avoid_list")
    if avoid_list is not None and not isinstance(avoid_list, list):
        errors.append("avoid_list must be an array")

    style_keywords = data.get("style_keywords")
    if style_keywords is not None and not isinstance(style_keywords, list):
        errors.append("style_keywords must be an array")

    if data.get("generic_consulting_layout_forbidden") not in (True, False):
        errors.append("generic_consulting_layout_forbidden must be a boolean")

    if data.get("render_strategy") == "svg-focused":
        title_zone_text = ""
        if isinstance(title_zone, dict):
            title_zone_text = str(title_zone.get("title", "")).strip()
        if not title_zone_text:
            errors.append("title_zone.title is required even for svg-focused pages")

    if data.get("svg_needed") is True and data.get("graphic_priority") == "low":
        errors.append("graphic_priority cannot be low when svg_needed is true")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_blueprint.py <path-to-blueprint.json>")
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 1

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}")
        return 1

    if not isinstance(data, dict):
        print("Top-level JSON value must be an object")
        return 1

    errors = validate_blueprint(data)
    if errors:
        print("Blueprint validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Blueprint validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
