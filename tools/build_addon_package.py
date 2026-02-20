#!/usr/bin/env python3
"""Build an installable Anki addon package (.zip/.ankiaddon) with valid manifest."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "dist" / "Beautify-Anki_2.0-addon.zip"


def tracked_files() -> list[str]:
    """Return git-tracked files that should go into the addon archive."""
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    files = [line.strip() for line in out.splitlines() if line.strip()]

    excluded_prefixes = (
        ".github/",
        "screenshots/",
        "ads/",
        "dist/",
    )

    excluded_files = {
        "tools/build_addon_package.py",
    }

    keep: list[str] = []

    for file in files:
        if file in excluded_files:
            continue
        if file.startswith(excluded_prefixes):
            continue
        keep.append(file)

    required = {"manifest.json", "meta.json", "__init__.py"}
    keep_set = set(keep)

    missing = sorted(required - keep_set)
    if missing:
        raise SystemExit(f"Missing required package files: {', '.join(missing)}")

    return sorted(keep_set)


def validate_manifest() -> None:
    """Validate manifest.json for required keys and types."""
    manifest_path = ROOT / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    required_keys = [
        "package",
        "name",
        "mod",
        "conflicts",
        "min_point_version",
        "max_point_version",
        "branch_index",
    ]

    missing = [key for key in required_keys if key not in data]
    if missing:
        raise SystemExit(f"manifest.json missing required keys: {', '.join(missing)}")

    if not isinstance(data["package"], str) or not data["package"].strip():
        raise SystemExit("manifest.json: 'package' must be a non-empty string")

    if not isinstance(data["name"], str) or not data["name"].strip():
        raise SystemExit("manifest.json: 'name' must be a non-empty string")

    if not isinstance(data["conflicts"], list):
        raise SystemExit("manifest.json: 'conflicts' must be a list")

    int_keys = ["mod", "min_point_version", "max_point_version", "branch_index"]
    for key in int_keys:
        if not isinstance(data[key], int):
            raise SystemExit(f"manifest.json: '{key}' must be an integer")

    if data["mod"] <= 0:
        raise SystemExit("manifest.json: 'mod' must be > 0")

    if data["min_point_version"] > data["max_point_version"]:
        raise SystemExit("manifest.json: min_point_version must be <= max_point_version")


def build(out_path: Path) -> None:
    """Create the addon zip archive."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    files = tracked_files()

    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as zf:
        for rel in files:
            zf.write(ROOT / rel, arcname=rel)

    # Validate archive contents
    with ZipFile(out_path, "r") as zf:
        names = set(zf.namelist())

    for req in ("manifest.json", "meta.json", "__init__.py"):
        if req not in names:
            raise SystemExit(f"Generated archive is missing {req}")

    print(f"Created {out_path} ({len(files)} files)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    validate_manifest()
    build(args.output)


if __name__ == "__main__":
    main()