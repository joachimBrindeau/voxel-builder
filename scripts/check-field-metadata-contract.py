#!/usr/bin/env python3
"""Validate field-metadata policy, ownership, and operational safety contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows/field-metadata.md"
SPEC = ROOT / "references/voxel/field-metadata-spec.md"
OPS = ROOT / "references/voxel/field-metadata-operations.md"
CONTRACT = ROOT / "references/voxel/field-metadata-contract.json"
AUTHOR = ROOT / "references/subagents/voxel-field-metadata-author.md"
CONTENT = ROOT / "references/subagents/voxel-content-author.md"
INDEX = ROOT / "references/subagents/README.md"
COMMANDS = ROOT / "references/core/command-surface.md"

errors: list[str] = []


def require(path: Path, needle: str, message: str) -> None:
    if needle not in path.read_text():
        errors.append(f"{path.relative_to(ROOT)}: {message}")


def reject(path: Path, needle: str, message: str) -> None:
    if needle in path.read_text():
        errors.append(f"{path.relative_to(ROOT)}: {message}")


try:
    contract = json.loads(CONTRACT.read_text())
except Exception as exc:
    errors.append(f"{CONTRACT.relative_to(ROOT)}: invalid JSON: {exc}")
    contract = {}

native = {
    "title", "description", "timezone", "text", "number", "switcher", "texteditor",
    "taxonomy", "product", "phone", "url", "email", "location", "work-hours", "image",
    "file", "ui-step", "ui-image", "ui-heading", "ui-html", "repeater", "recurring-date",
    "post-relation", "date", "time", "select", "multiselect", "color", "profile-avatar",
    "profile-name", "profile-first-name", "profile-last-name", "profile-bio",
}
addon = {"vote", "slug", "published-date", "icon", "excerpt", "author", "parent", "main-color"}
expected_types = native | addon
attributes = contract.get("attributes")
types = contract.get("types")
rules = contract.get("system_rules")
excluded = contract.get("excluded_attributes")

if contract.get("version") != 1:
    errors.append(f"{CONTRACT.relative_to(ROOT)}: version must equal 1")
if not isinstance(attributes, list) or not attributes or len(attributes) != len(set(attributes)):
    errors.append(f"{CONTRACT.relative_to(ROOT)}: attributes must be a non-empty unique list")
    attributes = []
if not isinstance(types, dict):
    errors.append(f"{CONTRACT.relative_to(ROOT)}: types must be an object")
    types = {}
if set(types) != expected_types:
    missing = sorted(expected_types - set(types))
    extra = sorted(set(types) - expected_types)
    errors.append(f"{CONTRACT.relative_to(ROOT)}: type set drift (missing={missing}, extra={extra})")
if not isinstance(excluded, dict) or "allowed-types" not in excluded or "overrides" not in excluded:
    errors.append(f"{CONTRACT.relative_to(ROOT)}: excluded_attributes must own allowed-types and overrides")
if not isinstance(rules, dict):
    errors.append(f"{CONTRACT.relative_to(ROOT)}: system_rules must be an object")
    rules = {}

allowed_policy = {"required", "optional", "unsupported"}
for name, row in types.items():
    if not isinstance(row, dict):
        errors.append(f"{CONTRACT.relative_to(ROOT)}: {name} row must be object")
        continue
    required_keys = {"description", "placeholder", "limit_keys", "skip", "recurse_subfields"}
    if set(row) != required_keys:
        errors.append(f"{CONTRACT.relative_to(ROOT)}: {name} row keys must equal {sorted(required_keys)}")
    if row.get("description") not in allowed_policy or row.get("placeholder") not in allowed_policy:
        errors.append(f"{CONTRACT.relative_to(ROOT)}: {name} has invalid support policy")
    limit_keys = row.get("limit_keys")
    if not isinstance(limit_keys, list) or any(not isinstance(key, str) for key in limit_keys):
        errors.append(f"{CONTRACT.relative_to(ROOT)}: {name}.limit_keys must be string array")
    elif not set(limit_keys).issubset(set(attributes)):
        errors.append(f"{CONTRACT.relative_to(ROOT)}: {name}.limit_keys outside attributes")
    for flag in ("skip", "recurse_subfields"):
        if not isinstance(row.get(flag), bool):
            errors.append(f"{CONTRACT.relative_to(ROOT)}: {name}.{flag} must be boolean")

skip_types = rules.get("skip_types", [])
skip_keys = rules.get("skip_keys", [])
skip_prefixes = rules.get("skip_key_prefixes", [])
presentational = rules.get("presentational_types", [])
for key, value in (("skip_types", skip_types), ("skip_keys", skip_keys),
                   ("skip_key_prefixes", skip_prefixes), ("presentational_types", presentational)):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{CONTRACT.relative_to(ROOT)}: system_rules.{key} must be string array")
if set(skip_types) != {name for name, row in types.items() if isinstance(row, dict) and row.get("skip")}:
    errors.append(f"{CONTRACT.relative_to(ROOT)}: skip_types must equal row-level skip types")
if not set(presentational).issubset(set(skip_types)):
    errors.append(f"{CONTRACT.relative_to(ROOT)}: presentational types must be skipped")

expected_caps = {
    "description": ("required", ["minlength", "maxlength"]),
    "location": ("required", []),
    "profile-name": ("required", ["minlength", "maxlength", "pattern"]),
    "profile-avatar": ("unsupported", ["max-size"]),
    "post-relation": ("required", ["max_count"]),
    "author": ("required", ["max_count"]),
    "image": ("unsupported", ["max-count", "max-size"]),
    "file": ("unsupported", ["max-count", "max-size"]),
    "recurring-date": ("unsupported", ["max_date_count"]),
}
for name, (placeholder, limits) in expected_caps.items():
    row = types.get(name, {})
    if row.get("placeholder") != placeholder or row.get("limit_keys") != limits:
        errors.append(f"{CONTRACT.relative_to(ROOT)}: {name} capability drift")
if not types.get("repeater", {}).get("recurse_subfields"):
    errors.append(f"{CONTRACT.relative_to(ROOT)}: repeater must recurse subfields")
if skip_prefixes:
    errors.append(f"{CONTRACT.relative_to(ROOT)}: key-prefix skips forbidden; voxel:* profile fields are user-facing")
for key in ("hierarchy-ancestors", "hierarchy-children", "hierarchy-siblings"):
    if key not in skip_keys:
        errors.append(f"{CONTRACT.relative_to(ROOT)}: missing system-derived skip key {key}")

workflow_markers = (
    "field-metadata-spec.md", "field-metadata-contract.json", "field-metadata-operations.md",
    "voxel-field-metadata-author", "voxel:field-schema", "voxel:settings set", "rollback",
    "Dry-run", "arbitrary-depth", "argv-safe", "concurrent drift", "blueprint", "complete live/blueprint diffs",
)
for marker in workflow_markers:
    require(WORKFLOW, marker, f"missing workflow contract marker {marker}")
for token in ("<allowed-keys-for(", "<live-field-keys-for-cpt>", "voxel-content-author.md"):
    reject(WORKFLOW, token, f"forbidden workflow token remains: {token}")
reject(SPEC, "only sanctioned write path", "contradictory sole-writer claim")
if len(WORKFLOW.read_text().splitlines()) > 160:
    errors.append(f"{WORKFLOW.relative_to(ROOT)}: orchestration workflow exceeds 160 lines")

ops_markers = (
    "validate-field-metadata-run.py", "--phase prewrite", "--phase final", "mktemp -d", "0700", "not a symlink", "before-option.sha256", "source-owner.json",
    "blueprints/<cpt>/before.json", "blueprints/<cpt>/after.json", "blueprints/<cpt>/blueprint.diff", "runtime-only-debt",
    "arbitrary repeater depth", "canonical-json(field_path)", "tightening_evidence",
    "scalar_mutations", "argument arrays", "Concurrent drift", "failed/mismatched scalar write",
    "rollback-failed", "byte-for-byte", "sorted option diff",
)
for marker in ops_markers:
    require(OPS, marker, f"missing operational safety marker {marker}")
for unsafe in ("| head -", "raw option update"):
    if unsafe == "raw option update":
        require(OPS, "Never write `voxel:post_types` through raw option update", "raw-write ban missing")
    else:
        reject(OPS, unsafe, "truncated diff gate forbidden")

for marker in (
    '"scope_id"', '"mode": "build-material"', '"status": "ready"', '"patch"',
    "scalar metadata attributes only", "tightening_evidence", "canonical identity",
):
    require(AUTHOR, marker, f"missing metadata-author invariant {marker}")
require(CONTENT, "Field-definition help descriptions", "content-author boundary missing")
if INDEX.read_text().count("[`voxel-field-metadata-author`](voxel-field-metadata-author.md)") != 1:
    errors.append(f"{INDEX.relative_to(ROOT)}: metadata-author table row must appear once")

for marker in ("--no-insert-if-missing", "top-level field", "nested scalar", "--dry", "--yes",
               "argv-safe", "concurrent option drift", "every repeater depth"):
    require(COMMANDS, marker, f"command surface missing {marker}")

if errors:
    print("Field-metadata contract failures:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
print(f"Field-metadata contract OK ({len(types)} field types; {len(native)} native + {len(addon)} addon)")
