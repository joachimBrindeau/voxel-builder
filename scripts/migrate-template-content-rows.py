#!/usr/bin/env python3
"""Migrate legacy ef-card text-like content rows in stored templates."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

LEGACY_KINDS = {"heading", "rich_text", "tag", "button", "media", "datafield"}
MODIFIER_ORDER = ["field", "subtitle", "rich_text", "media", "action", "expand"]
MEDIA_SUFFIXES = [
    "type",
    "image",
    "image_alt",
    "image_loading",
    "video_url",
    "icon",
    "svg",
    "map_pins",
    "map_zoom",
    "caption",
    "fit",
]


def value(cell: Any) -> Any:
    return cell.get("value") if isinstance(cell, dict) else None


def string_cell(text: str) -> dict[str, Any]:
    return {"$$type": "string", "value": text}


def boolean_cell(flag: bool) -> dict[str, Any]:
    return {"$$type": "boolean", "value": flag}


def responsive_string_cell(text: str) -> dict[str, Any]:
    return {
        "$$type": "ef-responsive-string",
        "value": {device: string_cell(text) for device in ("desktop", "tablet", "mobile")},
    }


def parse_modifiers(cell: Any) -> list[str]:
    raw = value(cell)
    if raw in (None, ""):
        return []
    items = raw.split(",") if isinstance(raw, str) else raw
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise ValueError("malformed modifiers cell")
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def finish_modifiers(cells: dict[str, Any], required: list[str]) -> None:
    modifiers = parse_modifiers(cells.get("modifiers"))
    for modifier in required:
        if modifier not in modifiers:
            modifiers.append(modifier)
    rank = {name: index for index, name in enumerate(MODIFIER_ORDER)}
    modifiers.sort(key=lambda name: (rank.get(name, len(rank)), name))
    if modifiers:
        cells["modifiers"] = string_cell(",".join(modifiers))
    else:
        cells.pop("modifiers", None)


def assign(cells: dict[str, Any], source: str, target: str) -> None:
    if source not in cells:
        return
    if target in cells and value(cells[target]) not in (None, "") and cells[target] != cells[source]:
        raise ValueError(f"ambiguous {source}/{target} cells")
    cells[target] = cells.pop(source)


def migrate_inline_media(cells: dict[str, Any]) -> bool:
    has_media = any(value(cells.get(f"inline_{suffix}")) not in (None, "") for suffix in MEDIA_SUFFIXES)
    for suffix in MEDIA_SUFFIXES:
        assign(cells, f"inline_{suffix}", f"media_{suffix}")
    assign(cells, "inline_modifiers", "modifiers_media")
    if has_media:
        cells["media_position"] = responsive_string_cell("inline")
    return has_media


def migrate_row(cells: dict[str, Any]) -> dict[str, Any]:
    kind = value(cells.get("kind"))
    if kind not in LEGACY_KINDS:
        return cells

    migrated = copy.deepcopy(cells)
    migrated["kind"] = string_cell("text")
    migrated["appearance"] = string_cell("pill" if kind == "tag" else "button" if kind == "button" else "plain")
    required: list[str] = []

    if kind == "heading":
        assign(migrated, "subtitle", "description")
        if value(migrated.get("description")) not in (None, ""):
            required.append("subtitle")
        if migrate_inline_media(migrated):
            required.append("media")
        if value(migrated.get("type")) == "default":
            migrated.pop("type", None)
    elif kind == "rich_text":
        if "body" in migrated and "text" not in migrated:
            migrated["text"] = migrated.pop("body")
        migrated.setdefault("text", string_cell(""))
        migrated["tag"] = string_cell("rich_text")
        required.append("rich_text")
    elif kind in {"tag", "button"}:
        if migrate_inline_media(migrated):
            required.append("media")
        if value(migrated.get("type")) not in (None, ""):
            required.append("action")
        if kind == "button" and value(migrated.get("icon_only")) is True:
            required.append("no_label")
    elif kind == "media":
        migrated.setdefault("text", string_cell(""))
        required.append("media")
        migrated.setdefault("media_position", responsive_string_cell("top-edge"))
    elif kind == "datafield":
        assign(migrated, "datafield_label", "description")
        assign(migrated, "datafield_value", "text")
        migrated["appearance"] = string_cell("field")
        required.append("field")
        if value(migrated.get("icon")) not in (None, ""):
            assign(migrated, "icon", "media_icon")
            migrated["media_type"] = string_cell("icon")
            migrated["media_position"] = responsive_string_cell("inline")
            required.append("media")
        else:
            migrated.pop("icon", None)

    finish_modifiers(migrated, required)
    split_field_appearance(migrated)
    return migrated


def row_repeats(cells: dict[str, Any]) -> bool:
    """Mirror EF step 2390: a looped or multiple-value field renders its values as pills."""
    if value(cells.get("multiple")) is True:
        return True
    for key in ("_vx_loop", "_ef_loop_query"):
        loop = cells.get(key)
        if isinstance(loop, dict) and isinstance(loop.get("value"), dict):
            if any(value(inner) not in (None, "") for inner in loop["value"].values()):
                return True
    return False


def split_field_appearance(cells: dict[str, Any]) -> bool:
    """Mirror EF migration step 2390 (`field-label-value-split`).

    The `field` appearance was retired: a text row shows its label through
    `field_enabled`, the former `description`/`media_*` cells become the label's
    `label_text`/`label_media_*`, and the value keeps `plain` (or `pill` when the
    row repeats). The migrator previously emitted `field` itself, so stored
    templates failed `elementor:validate` with an enum violation.
    """
    if value(cells.get("kind")) != "text" or value(cells.get("appearance")) != "field":
        return False
    cells["field_enabled"] = boolean_cell(True)
    cells["appearance"] = string_cell("pill" if row_repeats(cells) else "plain")
    moved = {key: cell for key, cell in cells.items() if key == "description" or key.startswith("media_")}
    for key, cell in moved.items():
        target = "label_text" if key == "description" else f"label_{key}"
        cells[target] = cell
        if key != "media_enabled":
            cells.pop(key)
    cells["media_enabled"] = boolean_cell(False)
    if "media_enabled" not in moved:
        cells.setdefault("label_media_enabled", boolean_cell(False))
    modifiers = [name for name in parse_modifiers(cells.get("modifiers")) if name != "field"]
    if modifiers:
        cells["modifiers"] = string_cell(",".join(modifiers))
    else:
        cells.pop("modifiers", None)
    return True


def normalize_canonical_row(cells: dict[str, Any]) -> bool:
    changed = False
    kind = value(cells.get("kind"))
    if kind == "text":
        if value(cells.get("type")) == "default":
            cells.pop("type", None)
            changed = True
        if split_field_appearance(cells):
            changed = True
    return changed


def migrate_document(document: Any) -> int:
    changed = 0
    stack = [document]
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(item)
            continue
        if not isinstance(item, dict):
            continue
        if item.get("elType") == "ef-card":
            rows = value(item.get("settings", {}).get("content_blocks"))
            if isinstance(rows, list):
                for row in rows:
                    cells = value(row)
                    if isinstance(cells, dict) and value(cells.get("kind")) in LEGACY_KINDS:
                        row["value"] = migrate_row(cells)
                        changed += 1
                    elif isinstance(cells, dict) and normalize_canonical_row(cells):
                        changed += 1
        stack.extend(child for child in item.values() if isinstance(child, (dict, list)))
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    total = 0
    stale: list[str] = []
    for path in args.paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        changed = migrate_document(document)
        total += changed
        if not changed:
            continue
        if args.check:
            stale.append(f"{path}: {changed} legacy row(s)")
        else:
            path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"migrated {changed} row(s): {path}")
    if stale:
        print("Legacy ef-card rows remain:", file=sys.stderr)
        for finding in stale:
            print(f"  - {finding}", file=sys.stderr)
        return 1
    print(f"legacy content-row migration clean ({total} row(s) changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
