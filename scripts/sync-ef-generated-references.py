#!/usr/bin/env python3
"""Sync EF generated schema and reference-table blocks from a WordPress workspace."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SCHEMA = SKILL_ROOT / "references/ef/widget-schemas.json"

REFERENCE_MARKERS = {
    "actions.md": ("actions",),
    "ef-parts-media-nav.md": ("ef-parts-index",),
    "ef-parts-row-surfaces.md": ("ef-parts",),
    "ef-widgets.md": ("ef-widgets",),
    "widgets.md": ("widgets",),
}


def resolve_wpdev_root(explicit: str | None) -> Path:
    candidates = [explicit, os.environ.get("WPDEV_ROOT")]
    for candidate in candidates:
        if not candidate:
            continue
        root = Path(candidate).expanduser().resolve()
        if (root / "cli/src/generated/widget-schemas.json").is_file():
            return root
    raise SystemExit("wpdev source checkout not found; pass --wpdev-root or set WPDEV_ROOT")


def marker_pattern(marker: str) -> re.Pattern[str]:
    return re.compile(
        rf"(<!-- AUTO-GENERATED:{re.escape(marker)} START[^>]*-->)(.*?)(<!-- AUTO-GENERATED:{re.escape(marker)} END -->)",
        re.DOTALL,
    )


def generated_block(text: str, marker: str, path: Path) -> str:
    match = marker_pattern(marker).search(text)
    if not match:
        raise SystemExit(f"{path}: missing AUTO-GENERATED:{marker} marker pair")
    return match.group(2)


def sync_marker(source: Path, target: Path, marker: str, check: bool) -> bool:
    source_text = source.read_text()
    target_text = target.read_text()
    desired = generated_block(source_text, marker, source)
    pattern = marker_pattern(marker)
    match = pattern.search(target_text)
    if not match:
        raise SystemExit(f"{target}: missing AUTO-GENERATED:{marker} marker pair")
    if match.group(2) == desired:
        return False
    if not check:
        target.write_text(target_text[: match.start(2)] + desired + target_text[match.end(2) :])
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wpdev-root", help="WordPress/wpdev workspace containing cli/ and plugins/custom/")
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    args = parser.parse_args()

    wpdev_root = resolve_wpdev_root(args.wpdev_root)
    source_schema = wpdev_root / "cli/src/generated/widget-schemas.json"
    source_refs = wpdev_root / "plugins/custom/elementor-framework/docs/reference"
    if not source_refs.is_dir():
        raise SystemExit(f"generated EF reference directory not found: {source_refs}")

    drifted: list[str] = []
    schema_bytes = source_schema.read_bytes()
    if not LOCAL_SCHEMA.is_file() or LOCAL_SCHEMA.read_bytes() != schema_bytes:
        drifted.append(str(LOCAL_SCHEMA.relative_to(SKILL_ROOT)))
        if not args.check:
            LOCAL_SCHEMA.write_bytes(schema_bytes)

    for filename, markers in REFERENCE_MARKERS.items():
        source = source_refs / filename
        target = SKILL_ROOT / "references/ef" / filename
        if not source.is_file():
            raise SystemExit(f"generated EF reference missing: {source}")
        for marker in markers:
            if sync_marker(source, target, marker, args.check):
                drifted.append(f"{target.relative_to(SKILL_ROOT)}#{marker}")

    if drifted and args.check:
        print("EF generated reference drift:")
        for item in drifted:
            print(f"  - {item}")
        print("Run: python3 scripts/sync-ef-generated-references.py")
        return 1

    verb = "Synchronized" if drifted else "Verified"
    print(f"{verb} EF schema and {sum(map(len, REFERENCE_MARKERS.values()))} generated reference block(s) from {wpdev_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
