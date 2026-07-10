#!/usr/bin/env python3
"""Validate the docs/solutions -> voxel-builder absorption ledger."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LEDGER = SKILL_ROOT / "references/core/solution-absorption.json"
DISPOSITIONS = {"absorbed", "superseded", "relocated", "retained"}


def find_workspace() -> Path | None:
    candidates = [
        Path(os.environ["WPDEV_ROOT"]) if os.environ.get("WPDEV_ROOT") else None,
        Path.cwd(),
        SKILL_ROOT.parent.parent / "wordpress",
    ]
    for candidate in candidates:
        if candidate and (candidate / "cli/src/index.ts").is_file():
            return candidate.resolve()
    return None


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


workspace = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else find_workspace()
if workspace is None or not (workspace / "docs/solutions").is_dir():
    print("SKIP solution absorption: WordPress workspace not found")
    raise SystemExit(0)

entries = json.loads(LEDGER.read_text())
errors: list[str] = []
by_source: dict[str, dict] = {}
for entry in entries:
    source = entry.get("source", "")
    disposition = entry.get("disposition", "")
    if not source or source in by_source:
        fail(errors, f"duplicate or missing source: {source!r}")
        continue
    by_source[source] = entry
    if disposition not in DISPOSITIONS:
        fail(errors, f"{source}: invalid disposition {disposition!r}")
        continue
    source_exists = (workspace / source).is_file()
    if disposition in {"absorbed", "superseded", "relocated"} and source_exists:
        fail(errors, f"{source}: retired source still exists")
    if disposition == "retained" and not source_exists:
        fail(errors, f"{source}: retained source is missing")
    if disposition in {"absorbed", "superseded"} and not entry.get("evidence"):
        fail(errors, f"{source}: missing freshness evidence")
    if disposition == "absorbed":
        for owner in entry.get("owners", []):
            if not (SKILL_ROOT / owner).is_file():
                fail(errors, f"{source}: missing owner {owner}")
        if not entry.get("owners"):
            fail(errors, f"{source}: absorbed entry has no owner")
    if disposition == "relocated":
        destination = entry.get("destination", "")
        if not destination or not (workspace / destination).is_file():
            fail(errors, f"{source}: missing relocation destination {destination!r}")

current = {
    path.relative_to(workspace).as_posix()
    for path in (workspace / "docs/solutions").rglob("*.md")
}
for source in sorted(current - set(by_source)):
    fail(errors, f"{source}: unclassified solution")

active_docs = [
    SKILL_ROOT / "SKILL.md",
    *SKILL_ROOT.glob("workflows/*.md"),
    *SKILL_ROOT.rglob("references/**/*.md"),
]
for path in active_docs:
    if not path.is_file():
        continue
    content = path.read_text()
    for source in by_source:
        if source in content:
            fail(
                errors,
                f"{path.relative_to(SKILL_ROOT)}: active dependency on {source}",
            )

if errors:
    print("Solution absorption failures:")
    for error in errors:
        print(f"  - {error}")
    raise SystemExit(1)

print(f"  PASS  solution absorption: {len(entries)} classified, {len(current)} retained in docs/solutions")
