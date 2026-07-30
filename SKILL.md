---
name: voxel-builder
description: "Build, audit, migrate, repair, curate, clean, and verify WordPress sites that use Voxel and Elementor Framework. Use for Voxel CPT configuration, entity data, templates, archives, search, database cleanup, WordPress admin-menu organization, and runtime issues; Elementor Framework V4 data and widgets; source-supported FAQ, visible-copy, and imported-video editorial backfill; CPT-agnostic sameAs identity research and population with Wikipedia, Wikidata, or official profiles; SEO/featured/hero/OG images; lean-seo output; and Voxel/Elementor performance work through wpdev, LiteSpeed, generated assets, or source fixes. Trigger when a request names Voxel, Elementor Framework, EF V4, Voxel CPTs, sameAs or knowledge-graph identity links, database cleanup/orphans/autoload/revisions on a Voxel site, video content backfill, lean-admin menus, or lean-seo. Not for generic WordPress or SEO work without Voxel/Elementor Framework, or for non-WordPress projects."
allowed-tools: Bash Read Write Glob Grep AskUserQuestion Task TaskCreate TaskList TaskUpdate TodoRead TodoWrite
license: MIT
---

# Voxel Builder

Schema-driven Voxel CPT lifecycle, Elementor Framework V4 atomic build/audit, Voxel entity curation, lean-seo configuration/debugging, content surgery, and performance repair for Voxel/Elementor WordPress workspaces.

## When to Use

- Build, migrate, audit, or repair Voxel pages, CPTs, archives, search surfaces,
  entity data, relations, or Elementor Framework V4 templates.
- Configure or debug lean-seo output, visible copy, FAQ content, images, or
  performance for a Voxel/Elementor Framework site.
- Audit or clean WordPress database state for a Voxel/Elementor Framework site.
- Inspect rendered behavior or source-of-truth data before a Voxel/Elementor
  mutation, then verify the resulting runtime state.
- Use the routing table below to select the narrow workflow for the request.

## When NOT to Use

- Generic WordPress work on a site that does not use Voxel or Elementor
  Framework; use the relevant WordPress workflow instead.
- Generic SEO research or audits with no Voxel/Elementor implementation scope;
  use the relevant SEO skill instead.
- Non-WordPress frontend, backend, content, or image work; use the matching
  domain skill instead.

## Essential Principles

1. **One source owner.** Identify whether Voxel config, entity fields, Elementor data,
   lean-seo settings, media, or plugin source owns the requested state. Writing the
   rendered symptom instead of its owner creates drift.
2. **One primary route.** Select exactly one workflow for each independently verifiable
   task. Composite requests become ordered tasks with explicit handoffs; workflows do
   not compete for the same mutation.
3. **Safe writes.** Capture rollback evidence before every mutation, centralize writes,
   and read the authoritative value back. Destructive merge/delete actions require the
   workflow's two confirmation gates.
4. **Bounded atomic delegation.** A leaf result covers one widget, section, criterion,
   URL, entity, or schema question. Batch 5-10 homogeneous leaves per worker and run at
   most the host concurrency cap in waves; every returned leaf remains independently
   attributable and rejectable.
5. **Native, surface-matched output.** Validate stored data and the affected runtime surface;
   DB equality alone cannot prove rendering, schema, behavior, or performance. Express site
   content through native Voxel/Elementor Framework settings, variants, tokens, layout props,
   and source templates — never custom CSS, inline styles, ad-hoc classes, Elementor overrides,
   or screenshot patches. Report native capability gaps at their component/source owner.

## Intake And Routing

Complete intake before reading route-specific detail:

1. Resolve the site, target identifier/URL, requested end state, and whether the user
   wants inspection, creation, mutation, migration, authoring, or optimization.
2. Identify the source owner from the table below. If the owner or intended mutation is
   ambiguous, ask one focused clarification question before routing.
3. Select one primary workflow using the precedence rules. For a composite request,
   create ordered tasks and route each task separately.
4. Read `references/core/rules.md`, `references/core/criteria.md`, the selected workflow,
   and only the references named by that workflow. Follow the selected workflow exactly.

## Orchestrator Contract

Treat every Voxel Builder run as a routed orchestration unless the task is a trivial
single-command lookup.

- **Main agent owns:** route selection, required reads, shared CLI context, rollback
  capture, fan-out planning, aggregation, conflict resolution, §2f/§2g gates,
  write-once assembly, final verification summary, and user-facing decisions.
- **Subagents own:** bounded homogeneous batches of 5-10 leaves using the named briefs
  under `references/subagents/`. Each leaf keeps a separate scope id, evidence set, and
  verdict/output so one failed leaf never contaminates its siblings.
- **No generic fallback agents.** Dispatch the matching named brief. If the host has
  no subagent runtime, read the brief and execute that same atomic scope inline as a
  degraded fallback, recording `subagent-runtime-unavailable`; do not collapse the
  whole page/workflow into one inline pass.
- **Writes stay centralized.** Read-only subagents return findings/evidence only.
  Build subagents return scoped JSON/patch material. The orchestrator validates
  scope, assembles, writes once, then dispatches verification. Field-definition UX
  metadata routes to `voxel-field-metadata-author`; stored record content routes to
  `voxel-content-author`; unknown field support may use `voxel-schema-detective` read-only.

## Primary Route Ownership

| Exclusive primary intent / source owner | Distinctive request signals | Workflow |
|---|---|---|
| Read-only diagnosis of a rendered page/template | audit, review, inspect, what is wrong | `workflows/audit.md` |
| Create a new Voxel CPT definition | create/new CPT, blueprint from scratch | `workflows/cpt-lifecycle.md` |
| Repair an existing CPT definition/runtime | missing CPT, field drift, template resolution, registration | `workflows/cpt-repair.md` |
| Converge CPT field-definition UX metadata recursively | description/placeholder/limits, repeater subfields, blueprint/live metadata alignment, self-documenting forms | `workflows/field-metadata.md` |
| Convert legacy Elementor data to EF V4 | migrate, V3 to V4, legacy containers/widgets | `workflows/migrate.md` |
| Create or change general EF `_elementor_data` | build template/page, wrapper, feed, loop, card tree | `workflows/build.md` |
| Create or rebuild complete CPT preview cards | preview cards, small/medium/large/link cards, main card | `workflows/preview-cards.md` |
| Port an artifact between sites and adapt it | copy/clone page, template, section, widget; translate; retarget CPT fields | `workflows/site-port.md` |
| Create or repair an archive/search page | archive, search root, `recherche/*` | `workflows/archive-search-pages.md` |
| Extract/refresh the reusable section store | save/extract/reuse section template | `workflows/section-templates.md` |
| Define only `ts_actions` / navbar action rows | action button, CTA row, `ts_actions` | `workflows/card-actions.md` |
| Apply a documented defect-class repair | known bug, action-row loop, cascade signature | `workflows/fix-known.md` |
| Mutate Voxel records, fields, relations, users, or visible copy | create/edit/merge/delete entity, content surgery, excerpt batch | `workflows/curation.md` |
| Complete imported Video records from source evidence | video backfill, transcript, presenter, service, FAQ, imported drafts | `workflows/video-content-backfill.md` |
| Author visible FAQ rows for existing content | FAQ questions/answers, improve FAQ | `workflows/faq-authoring.md` |
| Research, populate, or audit entity-equivalence links | sameAs, Wikipedia/Wikidata identity, official profiles, knowledge-graph links | `workflows/identity-linking.md` |
| Generate/backfill/improve CPT field content and apply it | write/backfill/regenerate definition, hook, excerpt, sources, h1, body copy; bulk field authoring | `workflows/content-generation.md` |
| Review/QA existing CPT field content against spec | audit/score/verify field content quality, prove backfill quality | `workflows/content-review.md` |
| Derive canonical service into city child | geolocate service, city version, geo-child, page à `<ville>`, mirror service under city | `workflows/geolocation.md` + `references/voxel/seo-geolocation-pages.md` |
| Generate/optimize/attach content images | featured, hero, OG, unique image | `workflows/image-generation.md` |
| Configure or debug lean-seo output | metadata, schema, markdown, sitemap, permalink, redirect, verification tag | `workflows/settings.md` |
| Create or align the WordPress admin menu | lean-admin, Content menu, standardized CPT submenu, missing CPT menu | `workflows/admin-menu.md` |
| Improve measured runtime performance | Lighthouse, CWV, N+1, payload, generated CSS, cache | `workflows/performance.md` |
| Audit or clean database state | database cleanup, orphan rows, dangling relationships, revisions, autoload, cron, plugin residue, optimize | `workflows/database-cleanup.md` |
| Audit and converge the Cloudflare edge (SSL/TLS, DNS, cache, Worker, crawlability) | cloudflare, edge, CDN, DNSSEC, CAA, cache rule, WAF, `a.<domain>` analytics proxy | `workflows/cloudflare.md` |
| Set/change the EF brand color palette | brand color, primary/accent green, brand purple, `--ef-color-*`, `_light` tint, match production colors | `workflows/design-tokens.md` |
| Lookup only; no mutation or full audit | schema shape, icon name, Voxel version/feature | `references/README.md` |

### Route Precedence

1. An explicit narrow artifact route (actions, archive, FAQ, image, geo, section store)
   wins over generic build/curation wording.
2. Migration wins over build; new CPT creation wins over CPT repair.
3. Audit is read-only. If the user asks to change state, route to the owning mutation
   workflow and use its baseline phase instead of routing to audit first.
4. For composite requests, sequence independent tasks by source owner. A workflow may
   hand off only after its exit contract is satisfied; the next workflow takes a named
   artifact, not implicit shared state.
5. If no row matches, ask for the target, source owner, and intended mutation. Do not
   improvise a new route.

## Fallback Routing

- Derive geo-child from canonical CPT post → `workflows/geolocation.md`.

## Reference Index

Always-loaded contracts: `references/core/rules.md`, `references/core/criteria.md`,
`references/core/parallel-dispatch.md`, and `references/subagents/README.md`.
Use `workflows/README.md` for workflow entry/exit contracts and `references/README.md`
for the domain lookup table. Keep loading narrow: open only the selected workflow and
its declared references. A selected workflow's required-reference list is complete;
lateral links inside references are optional lookup aids, not required chained reads.

Saved section templates (reusable hero/section starting trees, one folder per section) live in the `templates/` store — see `templates/README.md` for the on-disk shape, `meta.yml` schema, SSOT-wins discipline, and the refresh/migrate workflow; `templates/index.md` is the master catalog. Templates are starting trees, never authoritative spec.

## Success Criteria

- Correct workflow selected and entry criteria satisfied.
- Exactly one primary route owns each task; composite handoffs name their artifact.
- Named subagent briefs use bounded batches and return atomic leaf results; inline
  fallback is recorded only when no subagent runtime exists.
- Source-of-truth owner identified before mutation.
- Rollback/read-back evidence captured for writes.
- Rendered output or runtime behavior verified for touched surfaces.
- New learnings are folded into generic workflows/references, not one-off incident notes.
