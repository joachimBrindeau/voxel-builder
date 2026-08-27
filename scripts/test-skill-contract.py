#!/usr/bin/env python3
"""Validate voxel-builder SKILL.md frontmatter and routing contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - CI/runtime dependency check
    raise SystemExit(f"PyYAML is required: {exc}")

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
ARCHIVE_META = ROOT / "templates/pages/archive/meta.yml"
TEMPLATE_INDEX = ROOT / "templates/index.md"
BUILD_WORKFLOW = ROOT / "workflows/build.md"
PLANNING_WORKFLOW = ROOT / "workflows/page-planning.md"
ARCHETYPE_REFERENCE = ROOT / "references/core/page-plan-archetypes.md"

errors: list[str] = []
content = SKILL.read_text(encoding="utf-8")

if not content.startswith("---\n"):
    errors.append("SKILL.md frontmatter must start at byte 0")

match = re.search(r"\n---\s*\n", content[4:])
if not match:
    errors.append("SKILL.md frontmatter closing delimiter is missing")
    frontmatter: dict[str, object] = {}
else:
    end = match.start() + 4
    try:
        parsed = yaml.safe_load(content[4:end])
    except yaml.YAMLError as exc:
        errors.append(f"SKILL.md frontmatter is invalid YAML: {exc}")
        parsed = {}
    frontmatter = parsed if isinstance(parsed, dict) else {}
    if not content[end + len(match.group(0)) - 1 :].strip():
        errors.append("SKILL.md body must not be empty")

required = {"name", "description", "version", "author", "license", "platforms", "metadata"}
missing = sorted(required - set(frontmatter))
if missing:
    errors.append(f"SKILL.md frontmatter missing fields: {missing}")

if frontmatter.get("name") != "voxel-builder":
    errors.append("name must equal voxel-builder")

description_value = frontmatter.get("description")
if not isinstance(description_value, str):
    errors.append("description must be a string")
    description = ""
else:
    description = description_value
    if len(description) > 60:
        errors.append(f"description is {len(description)} chars; maximum is 60")
    if not description.endswith("."):
        errors.append("description must end with a period")
    if re.search(r"\b(powerful|comprehensive|seamless|advanced)\b", description, re.I):
        errors.append("description contains marketing language")

version = frontmatter.get("version")
if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
    errors.append("version must be semver")

if frontmatter.get("author") != "Joachim Brindeau (joachimBrindeau), Hermes Agent":
    errors.append("author must credit Joachim Brindeau first and Hermes Agent second")

platforms = frontmatter.get("platforms")
if platforms != ["linux", "macos"]:
    errors.append("platforms must be [linux, macos] for the POSIX shell scripts")

metadata = frontmatter.get("metadata")
hermes = metadata.get("hermes") if isinstance(metadata, dict) else None
if not isinstance(hermes, dict):
    errors.append("metadata.hermes must be a mapping")
else:
    tags = hermes.get("tags")
    if not isinstance(tags, list) or not tags:
        errors.append("metadata.hermes.tags must be a non-empty list")
    related = hermes.get("related_skills")
    if not isinstance(related, list):
        errors.append("metadata.hermes.related_skills must be a list")

if "allowed-tools" in frontmatter:
    errors.append("legacy Claude allowed-tools frontmatter must not be present")

for marker in (
    "`workflows/archive-search-pages.md`",
    "`workflows/integrity-loop.md`",
    "`workflows/organization-profile.md`",
):
    if marker not in content:
        errors.append(f"router missing {marker}")

archive_meta = yaml.safe_load(ARCHIVE_META.read_text(encoding="utf-8"))
if not isinstance(archive_meta, dict) or archive_meta.get("type") != "legacy-page-archive":
    errors.append("archive starter metadata must use type legacy-page-archive")

index_content = TEMPLATE_INDEX.read_text(encoding="utf-8")
if "| archive | legacy-page-archive |" not in index_content:
    errors.append("template index must classify archive as legacy-page-archive")

for route_file in (BUILD_WORKFLOW, PLANNING_WORKFLOW, ARCHETYPE_REFERENCE):
    route_content = route_file.read_text(encoding="utf-8")
    if "legacy-page-archive" not in route_content or "workflows/archive-search-pages.md" not in route_content:
        errors.append(
            f"{route_file.relative_to(ROOT)} must exclude the legacy archive starter from native archive routing"
        )

if len(content) > 100_000:
    errors.append("SKILL.md exceeds 100,000 characters")

if errors:
    print("Skill contract failures:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

print(
    "Skill contract OK "
    f"(description={len(description)} chars; {len(content.splitlines())} lines)"
)
