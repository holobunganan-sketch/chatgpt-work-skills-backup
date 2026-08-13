from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compressed_false_spans(flags: Iterable[bool]) -> list[dict[str, int]]:
    values = list(flags)
    spans: list[dict[str, int]] = []
    index = 0
    while index < len(values):
        if values[index]:
            index += 1
            continue
        start = index
        while index < len(values) and not values[index]:
            index += 1
        spans.append({"start": start, "end": index})
    return spans


def issue(code: str, message: str, path: str, **details: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message, "path": path}
    payload.update(details)
    return payload


def cli_result(issues: list[dict[str, Any]]) -> int:
    print(json.dumps({"passed": not issues, "issues": issues}, ensure_ascii=False, indent=2))
    return 0 if not issues else 1
