#!/usr/bin/env python3
"""Validate workflow-skill architecture and bounded atomic delegation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
KNOWN_TOOLS = {
    "Bash", "Read", "Write", "Edit", "Glob", "Grep", "AskUserQuestion",
    "Task", "TaskCreate", "TaskList", "TaskUpdate", "TodoRead", "TodoWrite",
}

errors: list[str] = []


def fail(path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"')
    return values


skill_text = SKILL.read_text()
skill_meta = frontmatter(skill_text)
for key in ("name", "description", "allowed-tools"):
    if not skill_meta.get(key):
        fail(SKILL, f"missing frontmatter key {key}")

tools = set(skill_meta.get("allowed-tools", "").split())
unknown = tools - KNOWN_TOOLS
if unknown:
    fail(SKILL, f"unknown allowed-tools: {', '.join(sorted(unknown))}")

for heading in ("## When to Use", "## When NOT to Use", "## Success Criteria"):
    if heading not in skill_text:
        fail(SKILL, f"missing {heading}")

principles_match = re.search(
    r"## Essential Principles\n(.*?)(?=\n## )", skill_text, re.S
)
principle_count = len(re.findall(r"^\d+\.\s", principles_match.group(1), re.M)) if principles_match else 0
if not 3 <= principle_count <= 5:
    fail(SKILL, f"expected 3-5 essential principles, found {principle_count}")

if len(skill_text.splitlines()) >= 500:
    fail(SKILL, "must remain under 500 lines")

route_match = re.search(
    r"## Primary Route Ownership\n(.*?)(?=\n### Route Precedence)", skill_text, re.S
)
route_paths = (
    re.findall(r"`(workflows/[^`]+\.md)`", route_match.group(1))
    if route_match else []
)
if not route_match:
    fail(SKILL, "missing Primary Route Ownership table")
if len(route_paths) != len(set(route_paths)):
    fail(SKILL, "primary route table contains duplicate workflow owners")
if "If no row matches" not in skill_text:
    fail(SKILL, "missing explicit no-match routing fallback")

workflow_index = ROOT / "workflows" / "README.md"
workflow_index_text = workflow_index.read_text()
primary_match = re.search(
    r"## Primary Workflows\n(.*?)(?=\n## Supporting Sub-Pipeline)",
    workflow_index_text,
    re.S,
)
indexed_routes = (
    [f"workflows/{name}" for name in re.findall(r"\[`([^`]+\.md)`\]", primary_match.group(1))]
    if primary_match else []
)
if not primary_match:
    fail(workflow_index, "missing Primary Workflows section")
if set(route_paths) != set(indexed_routes):
    missing = sorted(set(indexed_routes) - set(route_paths))
    extra = sorted(set(route_paths) - set(indexed_routes))
    fail(
        SKILL,
        "router/index ownership mismatch "
        f"(missing from router: {missing}; absent from index: {extra})",
    )
if "workflows/page-planning.md" in route_paths:
    fail(SKILL, "supporting page-planning pipeline may not be a primary route")

phase_re = re.compile(r"^(#{2,3}) Phase\s+[^\n]+", re.M | re.I)
for path in sorted((ROOT / "workflows").glob("*.md")):
    if path.name == "README.md":
        continue
    text = path.read_text()
    lines = len(text.splitlines())
    if lines >= 300:
        fail(path, f"workflow must remain under 300 lines ({lines})")
    phases = list(phase_re.finditer(text))
    if not phases:
        fail(path, "has no numbered Phase headings")
        continue
    final_label = phases[-1].group(0)
    if not re.search(r"verify|verification|gate|report", final_label, re.I):
        fail(path, f"final phase is not an explicit verification/gate/report ({final_label})")
    for index, phase in enumerate(phases):
        end = phases[index + 1].start() if index + 1 < len(phases) else len(text)
        block = text[phase.end():end]
        label = phase.group(0).lstrip("# ")
        if not re.search(r"^\*\*Entry(?: criteria)?(?:\*\*)?:", block, re.M | re.I):
            fail(path, f"{label} missing explicit Entry")
        if not re.search(r"^\*\*Exit(?: criteria)?(?:\*\*)?:", block, re.M | re.I):
            fail(path, f"{label} missing explicit Exit")
        if not re.search(r"^\d+\.\s", block, re.M):
            fail(path, f"{label} missing numbered actions")

for path in sorted((ROOT / "references").rglob("*.md")):
    lines = len(path.read_text().splitlines())
    if lines >= 400:
        fail(path, f"reference must remain under 400 lines ({lines})")

reference_index_corpus = (
    skill_text
    + (ROOT / "references" / "README.md").read_text()
    + (ROOT / "references" / "subagents" / "README.md").read_text()
    + "".join(path.read_text() for path in (ROOT / "workflows").glob("*.md"))
)
for path in sorted((ROOT / "references").rglob("*.md")):
    relative = path.relative_to(ROOT).as_posix()
    if "/icons/material-symbols/by-prefix/" in relative or path.name == "README.md":
        continue
    if path.name not in reference_index_corpus and relative not in reference_index_corpus:
        fail(path, "hand-authored reference is not indexed or linked by a workflow")

subagent_dir = ROOT / "references/subagents"
for path in sorted(subagent_dir.glob("voxel-*.md")):
    text = path.read_text()
    meta = frontmatter(text)
    lines = len(text.splitlines())
    if lines >= 300:
        fail(path, f"subagent brief must remain under 300 lines ({lines})")
    if not meta.get("tools"):
        fail(path, "missing tools frontmatter")
        continue
    agent_tools = {tool.strip() for tool in meta["tools"].split(",")}
    if "Task" in agent_tools:
        fail(path, "leaf specialist may not spawn nested Task workers")
    if "read-only" in meta.get("description", "").lower() and "Write" in agent_tools:
        fail(path, "read-only role declares Write")

fanout_patterns = re.compile(
    r"one (?:subagent|agent|worker) per (?:file|widget|section|criterion|url|entity|post|page|record|item)"
    r"|one content item per dispatch",
    re.I,
)
for base in (ROOT / "workflows", ROOT / "references"):
    for path in base.rglob("*.md"):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if fanout_patterns.search(line) and not re.search(
                r"never|do not|reject|rationalization|instead of", line, re.I
            ):
                fail(path, f"line {number} contains unbounded worker-per-item language")

if errors:
    print("Workflow structure failures:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

workflow_count = len(list((ROOT / "workflows").glob("*.md"))) - 1
reference_count = len(list((ROOT / "references").rglob("*.md")))
agent_count = len(list(subagent_dir.glob("voxel-*.md")))
print(
    f"  PASS  workflow structure: {workflow_count} workflows, "
    f"{reference_count} references, {agent_count} leaf briefs"
)
