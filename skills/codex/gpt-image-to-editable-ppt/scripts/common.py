from __future__ import annotations

import json
import math
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_data(path: str | os.PathLike[str]) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to read YAML files")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    return data or {}


def save_data(path: str | os.PathLike[str], data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to write YAML files")
        p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    else:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def normalize_hex(value: str, fallback: str = "#000000") -> str:
    if not isinstance(value, str):
        return fallback
    value = value.strip()
    if not value.startswith("#"):
        value = f"#{value}"
    if len(value) != 7:
        return fallback
    try:
        int(value[1:], 16)
    except ValueError:
        return fallback
    return value.upper()


def hex_to_rgb(value: str):
    value = normalize_hex(value)
    return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))


def inches_to_emu(value: float) -> int:
    return int(round(value * 914400))


def emu_to_inches(value: int) -> float:
    return value / 914400.0


def rect_intersection(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    x1, y1 = max(ax1, bx1), max(ay1, by1)
    x2, y2 = min(ax2, bx2), min(ay2, by2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    return (x2 - x1) * (y2 - y1)


def occupancy_ratio(rectangles, slide_w: float, slide_h: float, cols: int = 160, rows: int = 90) -> float:
    if not rectangles or slide_w <= 0 or slide_h <= 0:
        return 0.0
    grid = [[False] * cols for _ in range(rows)]
    for x, y, w, h in rectangles:
        if w <= 0 or h <= 0:
            continue
        x1 = max(0, min(cols, int(math.floor(x / slide_w * cols))))
        x2 = max(0, min(cols, int(math.ceil((x + w) / slide_w * cols))))
        y1 = max(0, min(rows, int(math.floor(y / slide_h * rows))))
        y2 = max(0, min(rows, int(math.ceil((y + h) / slide_h * rows))))
        for yy in range(y1, y2):
            for xx in range(x1, x2):
                grid[yy][xx] = True
    used = sum(1 for row in grid for cell in row if cell)
    return used / float(cols * rows)
