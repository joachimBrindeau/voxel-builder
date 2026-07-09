#!/usr/bin/env python3
"""Check wpdev-coverage.md against wpdev CLI registry.

Keeps this skill's coverage map honest without importing TypeScript. It extracts
registered leaf command keys from wpdev's cli/src/index.ts and verifies every
in-scope command has a row in references/core/wpdev-coverage.md.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
COVERAGE = SKILL_ROOT / "references/core/wpdev-coverage.md"
WPDEV_INDEX = Path.home() / "Development/wordpress/cli/src/index.ts"

PREFIXES = (
    "elementor:",
    "voxel:",
    "audit",
    "schema:",
)
BARE = {"headings", "quality", "perf", "purge", "rebuild", "smoke"}

if not WPDEV_INDEX.exists():
    print(f"SKIP wpdev coverage: missing {WPDEV_INDEX}")
    sys.exit(0)

index = WPDEV_INDEX.read_text()
coverage = COVERAGE.read_text()

registered = set(re.findall(r"^\s*'([^']+)':", index, flags=re.M))
registered.update(re.findall(r"^\s*(rebuild|purge|smoke|quality|perf|headings),\s*$", index, flags=re.M))

in_scope = sorted(
    cmd
    for cmd in registered
    if cmd in BARE or any(cmd == p.rstrip(":") or cmd.startswith(p) for p in PREFIXES)
)

missing = [cmd for cmd in in_scope if f"`{cmd}`" not in coverage and f"`{cmd} " not in coverage]

# Commands explicitly claimed absent must not exist.
absent_section = coverage.split("Verbs verified absent from the CLI", 1)[-1]
claimed_absent: list[str] = []
for line in absent_section.splitlines():
    if not line.startswith("- "):
        continue
    m = re.search(r"`([^`]+)`", line)
    if m:
        claimed_absent.append(m.group(1))
now_present = [cmd for cmd in claimed_absent if cmd in registered]

if missing or now_present:
    if missing:
        print("Missing wpdev-coverage.md row(s):")
        for cmd in missing:
            print(f"  - {cmd}")
    if now_present:
        print("Claimed-absent command(s) now present in CLI:")
        for cmd in now_present:
            print(f"  - {cmd}")
    sys.exit(1)

print(f"  PASS  wpdev coverage rows match live registry ({len(in_scope)} in-scope commands)")
