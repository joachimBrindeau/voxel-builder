---
name: voxel-builder
description: "This skill should be used when auditing, fixing, building, migrating, or verifying Voxel/Elementor Framework WordPress sites; creating/modifying Voxel CPTs and entity data; generating, attaching, optimizing, or verifying unique SEO/featured/hero/OG images for Voxel/WordPress content; repairing Voxel CPT runtime/template/archive/search issues; configuring or debugging lean-seo output for Voxel CPTs; repairing corrupted visible copy across Voxel CPTs/Elementor templates; or improving Voxel/Elementor frontend/backend performance through wpdev, LiteSpeed, Elementor assets, and source-level fixes. NOT for generic WordPress sites without Voxel/Elementor Framework, generic SEO audits, or non-WordPress projects."
version: 1.1.0
license: MIT
author: Joachim Brindeau
---

# Voxel Builder

Schema-driven Voxel CPT lifecycle, Elementor Framework V4 atomic build/audit, Voxel entity curation, lean-seo configuration/debugging, content surgery, and performance repair for Voxel/Elementor WordPress workspaces.

## Essential Principles

1. **Source of truth first.** Voxel config, Voxel fields, Elementor `_elementor_data`, lean-seo settings, and generated assets each have different owners. Identify the owner before writing.
2. **Workflow files own process.** Use `workflows/` for numbered phases and `references/` for lookup detail. Do not add one-off incident notes for a single CPT when a generic workflow can absorb the lesson.
3. **EF V4 only for new Elementor builds.** Build with Elementor Framework widgets (`ef-*`) and template/loop wrappers. Preserve existing Voxel `ts-*` widgets only when already present and required.
4. **Back up before mutation.** Any DB/template/CPT/SEO-output mutation needs rollback capture and read-back verification.
5. **Verify rendered output.** DB equality is necessary but not sufficient; verify live HTML, browser behavior, schema, markdown, or performance metrics according to the touched surface.
6. **Upload-as-you-finish for content batches.** When producing multiple Voxel records or reader/SERP-facing fields, do not stockpile finished content locally. For each completed item, write/upload it to the site immediately after it passes content gates, read it back, verify the target relation/taxonomy/fields, then update the batch todo/progress list before starting the next item. Large-scale jobs must remain resumable and auditable after every item, not only at the end.
7. **The main agent is the orchestrator.** It routes, gathers shared context, dispatches named subagents with atomic scopes, validates their returns, makes judgment-gate decisions, assembles writes once, and reports outcomes. It does not deep-audit every widget, hand-author every widget node, or improvise generic agents when a `references/subagents/` brief exists.

## Mandatory Reads

Before any build, audit, migration, repair, curation, lean-seo, content-surgery, or performance task:

1. `references/core/rules.md`
2. `references/core/criteria.md`
3. `references/core/parallel-dispatch.md`
4. `references/subagents/README.md`
5. The routed workflow below.
6. **If the task AUTHORS or refactors reader/SERP-facing copy** (geo derivation, CPT-single
   `h1`/`hook`/`description`/`faq`/`conversion-*`, bulk excerpt/meta, content-surgery rewrites):
   also `references/voxel/claude-seo-authoring.md` — research + writing MUST go through the
   claude-seo upstream skills (Read-fallback), gated by `claude-seo-baseline` + `content-methodology`.

## Orchestrator Contract

Treat every Voxel Builder run as a routed orchestration unless the task is a trivial
single-command lookup.

- **Main agent owns:** route selection, required reads, shared CLI context, rollback
  capture, fan-out planning, aggregation, conflict resolution, §2f/§2g gates,
  write-once assembly, final verification summary, and user-facing decisions.
- **Subagents own:** one atomic leaf scope each — one widget, one section, one
  criterion, one URL, one entity, or one schema question — using the named briefs
  under `references/subagents/`.
- **No generic fallback agents.** Dispatch the matching named brief. If the host has
  no subagent runtime, read the brief and execute that same atomic scope inline as a
  degraded fallback, recording `subagent-runtime-unavailable`; do not collapse the
  whole page/workflow into one inline pass.
- **Writes stay centralized.** Read-only subagents return findings/evidence only.
  Build subagents return scoped JSON/patch material. The orchestrator validates
  scope, assembles, writes once, then dispatches verification.

## Routing

| Request shape | Workflow / reference |
|---|---|
| "Audit page", "review template", "what's wrong with X", "make this page good" | `workflows/audit.md` |
| "Create CPT", "new post type X", "add fields to CPT" | `workflows/cpt-lifecycle.md` + `references/voxel/voxel-field-inventory.md` |
| "Fix/check CPT", "events CPT", "CTA placeholders", "archive duplicates", "JSON-LD status wrong", "runtime post type drift" | `workflows/cpt-repair.md` |
| "Build/modify Elementor data", "build single template", "add feed/list/loop section" | `workflows/build.md` |
| "Build/fix archive page", "search archive", "recherche/*" | `workflows/archive-search-pages.md` |
| "Save/extract a section template", "turn this hero into a reusable template" | `workflows/section-templates.md` |
| "Geolocate a service", "create city version of a page", "derive a geolocated service", "page service à `<ville>`", "mirror a service under a city" | `workflows/geolocation.md` + `references/voxel/seo-geolocation-pages.md` |
| "Migrate page off legacy Elementor", "convert V3 to EF V4" | `workflows/migrate.md` |
| "Scaffold preview cards" | `workflows/build.md` §Cards |
| "Define/fix card actions", "CTA/action buttons", "ts_actions" | `workflows/card-actions.md` |
| "Fix known bug class", "action-row loop", "CSS cascade" | `workflows/fix-known.md` |
| "Create/edit/merge/delete Voxel records", "repair relation/user/profile link", "audit data" | `workflows/curation.md` |
| "Repair corrupted copy", "grammar got messed up", "fix all pages/CPTs", "full corpus quality audit" | `workflows/curation.md` + `references/curation/content-surgery.md` |
| "Bulk SEO metadata/excerpts", "remove AI markers", "fix meta descriptions" | `references/voxel/lean-seo-excerpt-meta-descriptions.md` + `references/voxel/claude-seo-authoring.md` |
| "Write/author SEO copy", "content for this page", "research keywords/competitors", "make this page rank", "improve this page's content" | `references/voxel/claude-seo-authoring.md` (route research + writing through claude-seo upstream — Read-fallback; gated `claude-seo-baseline` + `content-methodology`) |
| "Generate featured images", "hero images", "OG/social images", "unique images for posts/CPTs", "attach SEO images" | `workflows/image-generation.md` + `references/voxel/image-generation.md`; load `seo/claude-seo/extensions/banana/skills/seo-image-gen` for global generation logic |
| "Configure title/description/OG/schema/.md/sitemap/noindex/permalink/redirect/verification tag" | `workflows/settings.md` |
| "Debug lean-seo plugin source", "why does this CPT miss sitemap", "add lean-seo filter" | `references/voxel/lean-seo-plugin-internals.md` |
| "Improve Voxel/Elementor/WordPress performance", "Lighthouse/CWV", "generated CSS", "LSCache", "N+1 queries", "frontend payload" | `workflows/performance.md` + `references/voxel/performance-patterns.md` |
| "Transplant template section", "edit template JSON", "site-wide de-AI pass over templates" | `references/ef/template-transplants.md` |
| "Find/replace/audit Material Symbols icon" | `references/icons/material-symbols/lookup-and-repair.md` |
| "Which Voxel version added X", "what changed in Voxel X.Y" | `references/voxel/voxel-changelog.md` |
| "What schema/widget/field shape exists" | `references/README.md`; dispatch `references/subagents/voxel-schema-detective.md` when needed |

## Fallback Routing

1. Mutates Voxel entity records/taxonomies/users/relations → `workflows/curation.md`.
2. Mutates CPT configuration/runtime/template/archive/search behavior → `workflows/cpt-repair.md` or `workflows/cpt-lifecycle.md` for new CPTs.
3. Mutates `_elementor_data` / EF template JSON → `workflows/build.md`.
4. Converts legacy Elementor/V3 to EF V4 → `workflows/migrate.md`.
5. Configures lean-seo output → `workflows/settings.md`.
6. Generates or attaches SEO images for Voxel/WordPress content → `workflows/image-generation.md` + `references/voxel/image-generation.md`; use `seo-image-gen` for global image backend logic.
7. Repairs visible copy/content quality → `workflows/curation.md` + content-surgery references. **Authors/refactors any reader/SERP-facing copy → additionally route research + writing through `references/voxel/claude-seo-authoring.md` (claude-seo upstream, Read-fallback; gated).**
8. Improves performance → `workflows/performance.md`.
9. Only inspects rendered page/template → `workflows/audit.md`.
10. Derives a geo-child (city variant) from a canonical CPT post → `workflows/geolocation.md`.
11. Still ambiguous → ask for site, target, and intended mutation.

## Reference Index

Use `references/README.md` for the full lookup table. Keep reference loading narrow: open only the workflow/reference needed by the route.

Saved section templates (reusable hero/section starting trees, one folder per section) live in the `templates/` store — see `templates/README.md` for the on-disk shape, `meta.yml` schema, SSOT-wins discipline, and the refresh/migrate workflow; `templates/index.md` is the master catalog. Templates are starting trees, never authoritative spec.

## Success Criteria

- Correct workflow selected and entry criteria satisfied.
- Named subagent briefs used for every non-trivial leaf scope; inline fallback is
  recorded only when no subagent runtime exists.
- Source-of-truth owner identified before mutation.
- Rollback/read-back evidence captured for writes.
- Rendered output or runtime behavior verified for touched surfaces.
- New learnings are folded into generic workflows/references, not one-off incident notes.
