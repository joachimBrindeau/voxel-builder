# voxel-builder

A routed workflow skill for building, auditing, migrating, repairing, curating, and
verifying WordPress sites that use Voxel and Elementor Framework V4. It selects one
source-owning workflow per task, delegates bounded batches through nine leaf-specialist
briefs, centralizes authoritative writes, and verifies both stored and rendered state
through `wpdev`.

Every Voxel field type (33/33), every documented Voxel feature surface (36/36), every EF
V4 widget/element (4/4), every EF part (10/10 user-facing + base/Media/Nav helpers), and the full
`ef_*` helper catalogue live in `./references/` (knowledge) and `./workflows/` (phased
processes). The page-planning sub-pipeline (Field Inventory → SSOT Read → Archetype
Selection → Section Blueprints → adversarial review → reconciliation → computed §2g gate)
is Phase 2 of the build pipeline, with a Behavior Contract gate for existing-data fixes.
See [`CHANGELOG.md`](CHANGELOG.md) for version history.

## Prerequisites

This skill drives real infrastructure; confirm these prerequisites before use:

- **`wpdev` CLI on `PATH`** — the engine behind every command (from the wpdev repo).
- **A WordPress site running the Voxel theme + `lean-seo` + the `elementor-framework` (EF V4) plugin.**
- **The committed EF V4 SSOT** `cli/src/generated/widget-schemas.json` (regenerated via `wpdev elementor:codegen`).

Verify the runtime prerequisites at any time:

```bash
./scripts/verify-install.sh <site>
```

## Cross-host capability mapping

The core workflows and leaf briefs are written in capability language. Map their
declarations to equivalent host capabilities. Where the workflow says:

- **"dispatch a subagent"** → use your host's subagent/Task facility, or read the brief under [`references/subagents/`](references/subagents/) and do its scoped work inline.
- **"run steps in parallel" / "a workflow"** → any deterministic parallel-step runner your host offers, or a scripted/sequential loop.
- **"ask the user"** → your host's clarification mechanism.

The atomic-output contract (one independently attributable result per widget, section,
criterion, URL, or entity), 5-10-leaf batch rule, and orchestrator-owned judgment gates
are host-independent — see
[`references/core/parallel-dispatch.md`](references/core/parallel-dispatch.md).

## What's inside

- **SKILL.md** — the MECE router: source owner and intent to exactly one primary workflow.
- **`references/`** — knowledge: `core/` (rules, command-surface, parallel-dispatch, criteria, blueprint-format), `voxel/` (field types, visibility, timeline, commerce, search, platform, tags, template-resolution, SEO/content guidance), `ef/` (widgets, parts, helpers, masonry, section-rhythm, dynamic-text), `icons/` (Material Symbols lookup), and `subagents/` (the nine role-briefs).
- **`workflows/`** — 15 primary phased workflows plus the supporting page-planning pipeline, indexed with exclusive ownership and exit artifacts in [`workflows/README.md`](workflows/README.md).
- **`templates/`** — the reusable section-template store: extracted, sanitized `_elementor_data` subtrees (`global` / `section` / `page` scope) agents can splice into new builds. See `templates/README.md` for the on-disk shape and `templates/index.md` for the master catalog.
- **`examples/`** — four golden `_elementor_data` fixtures (ef-card, ef-wrapper, ts-create-post, ts-post-feed).
- **`scripts/`** — `lint.sh` (portable lint), `verify-install.sh` (prereq check), `action-spec.sh`, `generate-icon-reference.ts`.

### Curation route

Voxel entity-data curation (profile/user repairs, duplicate merges, delete safety, field
edits, relation audits) is a first-class route: [`workflows/curation.md`](workflows/curation.md),
a 4-phase pipeline (Discover → Plan → Execute → Verify) with a merge/delete safety gate,
backed by [`references/curation/`](references/curation/).

## When to use

The SKILL.md routing table covers the dominant request shapes:

| Request shape | Goes to |
|---|---|
| "Audit page", "review template", "what's wrong with X" | `workflows/audit.md` |
| "Create CPT", "new post type X" | `workflows/cpt-lifecycle.md` |
| "Build/modify elementor data", "create ef-card", "add feed/list/loop section" | `workflows/build.md` — EF widgets only; use `ef-wrapper` template/loop wrappers instead of Voxel widgets |
| "Build a glossary / defined-term CPT with SEO JSON-LD" | `references/voxel/seo-defined-terms.md` |
| "Migrate page off legacy Elementor" | `workflows/migrate.md` |
| "Fix known bugs" | `workflows/fix-known.md` |
| "Find / replace an icon" | `references/icons/material-symbols/lookup-and-repair.md` |
| "What's the schema of X" | the `voxel-schema-detective` brief (`references/subagents/voxel-schema-detective.md`) |

Anything else falls through to the SKILL.md decision flow.

## Linting

```bash
bash scripts/lint.sh
```

Checks portability, strict skill/workflow/reference size limits, route/index set equality,
phase Entry/action/Exit structure, leaf-role tool boundaries, bounded fan-out language,
wpdev command coverage, templates, and every relative link/anchor.

## License

MIT — see [`LICENSE`](LICENSE).
