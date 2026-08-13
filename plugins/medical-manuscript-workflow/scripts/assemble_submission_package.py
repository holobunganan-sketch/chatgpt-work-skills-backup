from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

try:
    from .validate_submission_package import validate_submission_package
    from .workflow_common import load_json, sha256_file
except ImportError:
    from validate_submission_package import validate_submission_package
    from workflow_common import load_json, sha256_file


ROOT = Path(__file__).resolve().parents[1]


def _validate_policy(policy: dict[str, Any]) -> None:
    schema = load_json(ROOT / "schemas/delivery-policy.schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(policy), key=lambda item: list(item.absolute_path))
    if errors:
        details = "; ".join(f"{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in errors)
        raise ValueError(f"Delivery policy is invalid: {details}")


def _cleanup_owned_staging(staging: Path, parent: Path) -> None:
    if not staging.exists():
        return
    resolved_staging = staging.resolve()
    resolved_parent = parent.resolve()
    if resolved_staging.parent != resolved_parent or not resolved_staging.name.startswith(".mmw-stage-"):
        raise RuntimeError(f"Refusing to remove an unverified staging path: {resolved_staging}")
    shutil.rmtree(resolved_staging)


def assemble_package(policy: dict[str, Any], destination_parent: Path) -> Path:
    _validate_policy(policy)
    destination_parent = Path(destination_parent)
    destination_parent.mkdir(parents=True, exist_ok=True)
    final_path = destination_parent / policy["package_name"]
    if final_path.exists():
        raise FileExistsError(f"Refusing to overwrite an existing submission package: {final_path}")

    registered = policy.get("registered_artifacts", [])
    relative_paths: set[str] = set()
    for artifact in registered:
        source = Path(artifact["source"])
        if not source.is_file():
            raise FileNotFoundError(f"Registered formal source does not exist: {source}")
        if sha256_file(source).lower() != artifact["sha256"].lower():
            raise ValueError(f"Registered formal source hash does not match: {source}")
        relative = PurePosixPath(artifact["relative_path"].replace("\\", "/")).as_posix()
        if relative in relative_paths:
            raise ValueError(f"Duplicate formal relative path: {relative}")
        relative_paths.add(relative)

    staging = Path(tempfile.mkdtemp(prefix=".mmw-stage-", dir=destination_parent))
    try:
        for artifact in registered:
            relative = PurePosixPath(artifact["relative_path"].replace("\\", "/"))
            destination = staging.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(artifact["source"]), destination)
        issues = validate_submission_package(staging, policy)
        if issues:
            codes = ", ".join(sorted({item["code"] for item in issues}))
            raise ValueError(f"Staged submission package failed validation: {codes}")
        os.replace(staging, final_path)
    except Exception:
        _cleanup_owned_staging(staging, destination_parent)
        raise
    return final_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a release-validated submission package.")
    parser.add_argument("policy")
    parser.add_argument("destination_parent")
    args = parser.parse_args()
    print(assemble_package(load_json(args.policy), Path(args.destination_parent)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
