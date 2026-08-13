#!/usr/bin/env python3
"""Record privacy-minimized model outcomes for conservative future demotion."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


def default_state_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
    return codex_home / "model-orchestrator" / "model-history.json"


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--risk", required=True, choices=["L0", "L1", "L2", "L3"])
    parser.add_argument("--passed", required=True, choices=["true", "false"])
    parser.add_argument("--repair-count", type=int, default=0)
    parser.add_argument("--validator-failures", type=int, default=0)
    parser.add_argument("--state", default=str(default_state_path()))
    args = parser.parse_args(list(argv) if argv is not None else None)

    state_path = Path(args.state).expanduser()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if state_path.exists():
        data = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        data = {"schema_version": 1, "records": []}
    records = data.setdefault("records", [])
    records.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_id": args.model_id,
            "category": args.category,
            "risk": args.risk,
            "passed": args.passed == "true",
            "repair_count": max(0, args.repair_count),
            "validator_failures": max(0, args.validator_failures),
        }
    )
    # Retain bounded aggregate history without prompts, outputs, filenames, or user content.
    data["records"] = records[-2000:]
    fd, temp_name = tempfile.mkstemp(prefix="model-history-", suffix=".json", dir=state_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, state_path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    print(state_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
