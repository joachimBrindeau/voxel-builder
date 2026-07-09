# voxel-builder

Schema-driven Voxel CPT lifecycle and Elementor V4 atomic build/audit pipeline, as a
**portable agent skill** (`~/.agents/skills/` form — usable by any agent host that reads
the SKILL.md convention: opencode, codex, cursor, gemini-cli, github-copilot, zed, Claude
Code, …). Backed by the `wpdev` CLI. Ships eight subagent role-briefs, a built-in
**curation route** (Voxel entity-data create/edit/merge/delete — see below), and atomic
golden `_elementor_data` fixtures.

Every Voxel field type (33/33), every documented Voxel feature surface (36/36), every EF
V4 widget (6/6), every EF part (10/10 user-facing + base/Media/Nav helpers), and the full
`ef_*` helper catalogue live in `./references/` (knowledge) and `./workflows/` (phased
processes). The page-planning sub-pipeline (Field Inventory → SSOT Read → Archetype
Selection → Section Blueprints → adversarial review → reconciliation → computed §2g gate)
is Phase 2 of the build pipeline, with a Behavior Contract gate for existing-data fixes.
See [`CHANGELOG.md`](CHANGELOG.md) for version history.

## Prerequisites

This skill drives real infrastructure — confirm before use (see also SKILL.md §Prerequisites):

- **`wpdev` CLI on `PATH`** — the engine behind every command (from the wpdev repo).
- **A WordPress site running the Voxel theme + `lean-seo` + the `elementor-framework` (EF V4) plugin.**
- **The committed EF V4 SSOT** `cli/src/generated/widget-schemas.json` (regenerated via `wpdev elementor:codegen`).

Verify the runtime prerequisites at any time:

```bash
./scripts/verify-install.sh
```

## Host-agnostic by design

The skill is written in capability language, not product names. Where it says:

- **"dispatch a subagent"** → use your host's subagent/Task facility, or read the brief under [`references/subagents/`](references/subagents/) and do its scoped work inline.
- **"run steps in parallel" / "a workflow"** → any deterministic parallel-step runner your host offers, or a scripted/sequential loop.
- **"ask the user"** → your host's clarification mechanism.

The atomic-scope contract (one widget / section / criterion per subagent) and the
judgment-gates-stay-with-the-orchestrator rule are host-independent — see
[`references/core/parallel-dispatch.md`](references/core/parallel-dispatch.md).

## What's inside

- **SKILL.md** — the router: request-shape → workflow/reference mapping, the eight rules, subagent role table, orchestration model.
- **`references/`** — knowledge: `core/` (rules, command-surface, parallel-dispatch, criteria, blueprint-format), `voxel/` (field types, visibility, timeline, commerce, search, platform, tags, template-resolution, **seo-defined-terms**), `ef/` (widgets, parts, helpers, masonry, section-rhythm, dynamic-text), `icons/` (Material Symbols lookup), and `subagents/` (the eight role-briefs).
- **`workflows/`** — phased processes: cpt-lifecycle, build, migrate, audit, page-planning, card-actions, curation, fix-known, section-templates.
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

Checks portability (no Claude-Code coupling), SKILL.md size, absolute-path hygiene, and
(when `lychee` is installed) that every relative link + `#anchor` resolves.

## License

MIT — see [`LICENSE`](LICENSE).
