#!/usr/bin/env python3
"""Check wpdev-coverage.md against wpdev CLI registry.

Keeps this skill's coverage map honest without importing TypeScript. It reads
the registered command keys from wpdev's generated manifest
(cli/src/generated/command-manifest.json, the same SSOT the wpdev MCP serves)
and verifies every in-scope command has a row in references/core/wpdev-coverage.md.

It also checks the reverse direction: every namespaced `wpdev <cmd>` this skill
tells an agent to run, and every command named in the coverage table's own first
column, must actually be registered. Without that, a retired verb keeps its
documentation forever and the first sign of trouble is an agent pasting a command
that exits "unknown command" mid-task. The table column is checked separately
because the invocation scan cannot see it -- a row is not an invocation -- yet a
row is precisely what an agent reads to conclude a command exists.
"""
from __future__ import annotations

import json
import re
import os
import shutil
import sys
from itertools import chain
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
COVERAGE = SKILL_ROOT / "references/core/wpdev-coverage.md"
MANIFEST = Path("cli/src/generated/command-manifest.json")


def find_wpdev_manifest() -> Path | None:
    """Resolve wpdev source from an override, cwd, or the wpdev executable."""
    candidates: list[Path] = []
    if root := os.environ.get("WPDEV_ROOT"):
        candidates.append(Path(root))
    if source_root := os.environ.get("WPDEV_SOURCE_ROOT"):
        candidates.append(Path(source_root))

    candidates.extend([Path.cwd(), *Path.cwd().parents])
    if executable := shutil.which("wpdev"):
        executable_dir = Path(executable).resolve().parent
        candidates.extend([executable_dir, *executable_dir.parents])

    for root in candidates:
        manifest = root / MANIFEST
        if manifest.is_file():
            return manifest
    return None


WPDEV_MANIFEST = find_wpdev_manifest()

if "--resolve-index" in sys.argv:
    if WPDEV_MANIFEST is None:
        print("FAIL wpdev coverage: source checkout not found; set WPDEV_ROOT or WPDEV_SOURCE_ROOT")
        sys.exit(1)
    print(WPDEV_MANIFEST)
    sys.exit(0)

PREFIXES = (
    "elementor:",
    "voxel:",
    "audit",
    "schema:",
)
BARE = {"headings", "quality", "perf", "purge", "rebuild", "smoke"}
OUT_OF_SCOPE = {
    # Retired presentation-management path. The skill must use atomic dynamic
    # styles and must not document or route agents through this command.
    "elementor:reset:button-variants",
}

if WPDEV_MANIFEST is None:
    print("FAIL wpdev coverage: source checkout not found; set WPDEV_ROOT or WPDEV_SOURCE_ROOT")
    sys.exit(1)

coverage = COVERAGE.read_text()

manifest = json.loads(WPDEV_MANIFEST.read_text(encoding="utf-8"))
entries = manifest if isinstance(manifest, list) else manifest.get("commands", list(manifest.values()))
registered = {entry["command"] for entry in entries if isinstance(entry, dict) and "command" in entry}
if not registered:
    print(f"FAIL wpdev coverage: no commands found in {WPDEV_MANIFEST}")
    sys.exit(1)
# Namespace parents (`wpdev audit`) are real, runnable commands but appear only
# as the prefix of their leaves, never as a key of their own. They count as
# registered for the ghost checks, but only manifest leaves need a coverage row.
leaves = set(registered)
registered.update({cmd.split(':', 1)[0] for cmd in list(registered) if ':' in cmd})

in_scope = sorted(
    cmd
    for cmd in leaves
    if cmd not in OUT_OF_SCOPE
    and (cmd in BARE or any(cmd == p.rstrip(":") or cmd.startswith(p) for p in PREFIXES))
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

# Reverse drift: any namespaced command this skill instructs an agent to *run*
# must exist. Scanning `wpdev <cmd>` invocations rather than every backticked
# token keeps prose that names a retired verb in order to warn about it (and
# option keys such as `voxel:post_types`) out of the check.
ghosts: dict[str, list[str]] = {}

# The coverage table's own first column, which the invocation scan below cannot
# see: a row reads as a command's definitive entry, so a retired verb left there
# outlives its command with nothing to contradict it.
table = coverage.split("Verbs verified absent from the CLI", 1)[0]
for lineno, line in enumerate(table.splitlines(), 1):
    m = re.match(r"\| `([a-z][a-z0-9:_-]*)` \|", line)
    if m and m.group(1) not in registered:
        ghosts.setdefault(m.group(1), []).append(f"{COVERAGE.relative_to(SKILL_ROOT)}:{lineno} (coverage table row)")

for doc in sorted(chain(SKILL_ROOT.glob("references/**/*.md"), SKILL_ROOT.glob("workflows/**/*.md"))):
    if "icons" in doc.parts:
        continue
    text = doc.read_text(encoding="utf-8")
    guarded = "--help" in text and "not present in your checkout" in text
    for lineno, line in enumerate(text.splitlines(), 1):
        for cmd in set(re.findall(r"wpdev\s+([a-z][a-z0-9_-]*:[a-z0-9:_-]+)", line)):
            if cmd in registered or cmd.endswith(":") or guarded:
                continue
            ghosts.setdefault(cmd, []).append(f"{doc.relative_to(SKILL_ROOT)}:{lineno}")

if missing or now_present or ghosts:
    if missing:
        print("Missing wpdev-coverage.md row(s):")
        for cmd in missing:
            print(f"  - {cmd}")
    if now_present:
        print("Claimed-absent command(s) now present in CLI:")
        for cmd in now_present:
            print(f"  - {cmd}")
    if ghosts:
        print("Documented `wpdev` command(s) that are not registered:")
        for cmd in sorted(ghosts):
            print(f"  - {cmd} ({', '.join(ghosts[cmd][:4])})")
    sys.exit(1)

print(
    f"  PASS  wpdev coverage rows match live registry "
    f"({len(in_scope)} in-scope commands; {len(registered)} registered, no documented ghosts)"
)
