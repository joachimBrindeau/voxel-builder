# voxel-builder

A routed workflow skill for building, auditing, migrating, repairing, curating, and
verifying WordPress sites that use Voxel and Elementor Framework V4. It selects one
source-owning workflow per task, delegates bounded batches through named leaf-specialist
briefs, centralizes authoritative writes, and verifies both stored and rendered state
through `wpdev`.

The current catalogs and coverage guarantees live under `./references/` (knowledge) and
`./workflows/` (phased processes) and are checked by `scripts/lint.sh`; avoid copying
manual coverage totals into prose. The page-planning sub-pipeline (Field Inventory → SSOT Read → Archetype
Selection → Section Blueprints → adversarial review → reconciliation → computed §2g gate)
is Phase 2 of the build pipeline, with a Behavior Contract gate for existing-data fixes.
See [`CHANGELOG.md`](CHANGELOG.md) for version history.

## Prerequisites

This skill drives real infrastructure; confirm these prerequisites before use:

- **`wpdev` CLI on `PATH`** — the engine behind every command (from the wpdev repo). For repository linting that compares command coverage to source, set `WPDEV_ROOT=/path/to/wpdev` when the executable is not inside its checkout.
- **A WordPress site running the Voxel theme + `lean-seo` + the `elementor-framework` (EF V4) plugin.**
- **The skill-local EF V4 SSOT** is `references/ef/widget-schemas.json`. It and the
  generated widget/action/part tables are synchronized from the WordPress workspace's
  `wpdev elementor:codegen` + `wpdev elementor:docs:gen` outputs by
  `scripts/sync-ef-generated-references.py`; `scripts/lint.sh` rejects drift.

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
- **`references/`** — knowledge: `core/` (rules, command-surface, parallel-dispatch, criteria, blueprint-format), `voxel/` (field types, visibility, timeline, commerce, search, platform, tags, template-resolution, SEO/content guidance), `ef/` (widgets, parts, helpers, masonry, section-rhythm, dynamic-text), `icons/` (Material Symbols lookup), and `subagents/` (MECE role briefs indexed in `references/subagents/README.md`).
- **`workflows/`** — primary phased workflows plus supporting pipelines, indexed with exclusive ownership and exit artifacts in [`workflows/README.md`](workflows/README.md).
- **`templates/`** — the reusable section-template store: extracted, sanitized `_elementor_data` subtrees (`global` / `section` / `page` scope) agents can splice into new builds. See `templates/README.md` for the on-disk shape and `templates/index.md` for the master catalog.
- **`examples/`** — four golden `_elementor_data` fixtures (ef-card, ef-wrapper, ts-create-post, ts-post-feed).
- **`scripts/`** — the canonical lint, EF codegen/docs synchronization, prerequisite checks, validators, and generated-reference tooling.

### Curation route

Voxel entity-data curation (profile/user repairs, duplicate merges, delete safety, field
edits, relation audits) is a first-class route: [`workflows/curation.md`](workflows/curation.md),
a 4-phase pipeline (Discover → Plan → Execute → Verify) with a merge/delete safety gate,
backed by [`references/curation/`](references/curation/).

## Routing

`SKILL.md` is the only request-to-primary-workflow router. Start with its **Primary Route
Ownership** table and precedence rules. Use `references/README.md` only for narrow topic
lookup after the primary workflow has been selected.

## Linting

```bash
bash scripts/lint.sh
```

Checks portability, strict skill/workflow/reference size limits, route/index set equality,
phase Entry/action/Exit structure, leaf-role tool boundaries, bounded fan-out language,
wpdev command coverage, EF generated schema/reference drift, templates, and every relative
link/anchor. Set `WPDEV_ROOT` to the wpdev source checkout and, when validating
against a separately staged/generated corpus, set `EF_GENERATED_ROOT` to that WordPress
workspace root.

## License

MIT — see [`LICENSE`](LICENSE).
