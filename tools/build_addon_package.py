#!/usr/bin/env python3
"""Build an installable Anki addon package (.ankiaddon/.zip)."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "dist" / "Beautify-Anki_2.0.ankiaddon"


def tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    files = [line.strip() for line in out.splitlines() if line.strip()]

    excluded_prefixes = (
        ".github/",
        "screenshots/",
        "ads/",
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

    if "manifest.json" not in keep:
        keep.append("manifest.json")

    return sorted(set(keep))


def validate_manifest() -> None:
    manifest_path = ROOT / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = [
        "package",
        "name",
        "mod",
        "conflicts",
        "min_point_version",
        "max_point_version",
        "branch_index",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        raise SystemExit(f"manifest.json missing required keys: {', '.join(missing)}")


def build(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    files = tracked_files()
    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as zf:
        for rel in files:
            zf.write(ROOT / rel, arcname=rel)
    print(f"Created {out_path} ({len(files)} files)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    validate_manifest()
    build(args.output)


if __name__ == "__main__":
    main()
