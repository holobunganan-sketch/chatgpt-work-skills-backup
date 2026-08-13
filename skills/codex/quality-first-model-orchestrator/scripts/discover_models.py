#!/usr/bin/env python3
"""Discover and normalize the model catalog exposed by Codex App Server."""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _extract_data(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload.get("models"), list):
        return payload["models"]
    if isinstance(payload.get("data"), list):
        return payload["data"]
    result = payload.get("result")
    if isinstance(result, dict) and isinstance(result.get("data"), list):
        return result["data"]
    raise ValueError("Model catalog must contain models, data, or result.data")


def _normalize_efforts(value: Any) -> List[str]:
    efforts: List[str] = []
    if not isinstance(value, list):
        return efforts
    for item in value:
        if isinstance(item, str):
            effort = item
        elif isinstance(item, dict):
            effort = item.get("reasoningEffort") or item.get("reasoning_effort")
        else:
            effort = None
        if effort and effort not in efforts:
            efforts.append(str(effort))
    return efforts


def normalize_catalog(payload: Dict[str, Any], source: str = "unknown") -> Dict[str, Any]:
    """Return a stable catalog shape from raw App Server or saved JSON output."""
    models: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for raw in _extract_data(payload):
        if not isinstance(raw, dict):
            warnings.append("Ignored a non-object model entry")
            continue
        model_id = raw.get("id") or raw.get("model") or raw.get("model_id")
        if not model_id:
            warnings.append("Ignored a model entry without id/model")
            continue
        efforts = _normalize_efforts(
            raw.get("supportedReasoningEfforts", raw.get("supported_reasoning_efforts", []))
        )
        default_effort = raw.get("defaultReasoningEffort", raw.get("default_reasoning_effort"))
        if default_effort and default_effort not in efforts:
            efforts.append(str(default_effort))
        modalities = raw.get("inputModalities", raw.get("input_modalities"))
        if not isinstance(modalities, list) or not modalities:
            modalities = ["text", "image"]
        upgrade = raw.get("upgrade")
        if isinstance(upgrade, dict):
            upgrade = upgrade.get("id") or upgrade.get("model")
        models.append(
            {
                "id": str(model_id),
                "model": str(raw.get("model") or model_id),
                "display_name": str(raw.get("displayName") or raw.get("display_name") or model_id),
                "hidden": bool(raw.get("hidden", False)),
                "default_reasoning_effort": str(default_effort) if default_effort else None,
                "supported_reasoning_efforts": efforts,
                "input_modalities": [str(x) for x in modalities],
                "supports_personality": raw.get("supportsPersonality", raw.get("supports_personality")),
                "is_default": bool(raw.get("isDefault", raw.get("is_default", False))),
                "upgrade": str(upgrade) if upgrade else None,
            }
        )
    return {
        "schema_version": 1,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "warnings": warnings,
    }


class _JsonlClient:
    def __init__(self, proc: subprocess.Popen[str]):
        self.proc = proc
        self.messages: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self.messages.put(json.loads(line))
            except json.JSONDecodeError:
                self.messages.put({"_invalid_json": line})

    def send(self, message: Dict[str, Any]) -> None:
        if self.proc.stdin is None:
            raise RuntimeError("Codex App Server stdin is unavailable")
        self.proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def response(self, request_id: int, timeout: float) -> Dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            remaining = max(0.05, deadline - time.monotonic())
            try:
                message = self.messages.get(timeout=remaining)
            except queue.Empty:
                break
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"App Server error for request {request_id}: {message['error']}")
                return message
        raise TimeoutError(f"Timed out waiting for App Server response id={request_id}")


def query_app_server(
    codex_bin: str = "codex",
    timeout: float = 15.0,
    include_hidden: bool = False,
    limit: int = 100,
) -> Dict[str, Any]:
    """Query model/list over the local Codex App Server JSONL transport."""
    proc = subprocess.Popen(
        [codex_bin, "app-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    client = _JsonlClient(proc)
    try:
        client.send(
            {
                "method": "initialize",
                "id": 1,
                "params": {
                    "clientInfo": {
                        "name": "quality_first_model_orchestrator",
                        "title": "Quality-First Model Orchestrator",
                        "version": "1.0.0",
                    }
                },
            }
        )
        client.response(1, timeout)
        client.send({"method": "initialized", "params": {}})

        all_models: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        request_id = 2
        while True:
            params: Dict[str, Any] = {"limit": limit, "includeHidden": include_hidden}
            if cursor:
                params["cursor"] = cursor
            client.send({"method": "model/list", "id": request_id, "params": params})
            message = client.response(request_id, timeout)
            result = message.get("result") or {}
            page = result.get("data") or []
            if not isinstance(page, list):
                raise RuntimeError("model/list returned a non-list data field")
            all_models.extend(x for x in page if isinstance(x, dict))
            cursor = result.get("nextCursor")
            if not cursor:
                break
            request_id += 1
        return {"data": all_models}
    finally:
        try:
            if proc.stdin:
                proc.stdin.close()
        except OSError:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def _load_json_source(value: str) -> Dict[str, Any]:
    stripped = value.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(value)
    path = Path(value).expanduser()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-file", help="Read raw or normalized catalog JSON instead of App Server")
    parser.add_argument("--codex-bin", default=os.environ.get("CODEX_BIN", "codex"))
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--output", default="-", help="Output JSON path or - for stdout")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.catalog_file:
            raw = _load_json_source(args.catalog_file)
            source = f"file:{Path(args.catalog_file).expanduser()}"
        elif os.environ.get("CODEX_MODEL_CATALOG_JSON"):
            raw = _load_json_source(os.environ["CODEX_MODEL_CATALOG_JSON"])
            source = "env:CODEX_MODEL_CATALOG_JSON"
        else:
            raw = query_app_server(
                codex_bin=args.codex_bin,
                timeout=args.timeout,
                include_hidden=args.include_hidden,
            )
            source = "codex-app-server:model/list"
        normalized = normalize_catalog(raw, source=source)
    except Exception as exc:  # CLI boundary: return a structured, actionable failure.
        print(f"Model discovery failed: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(normalized, ensure_ascii=False, indent=2) + "\n"
    if args.output == "-":
        sys.stdout.write(text)
    else:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
