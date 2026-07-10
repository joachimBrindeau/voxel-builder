# references/ — knowledge to consult

This skill separates **knowledge** (look-it-up reference) from **process** (follow-the-steps). Reference knowledge lives here in three groups; the phased processes live in [`../workflows/`](../workflows/README.md). The router is [`../SKILL.md`](../SKILL.md).

```
../../
├── references/   ← YOU ARE HERE — knowledge to consult
│   ├── core/   — cross-cutting SSOT, read on every session
│   ├── ef/     — Elementor Framework V4 atomic widget reference
│   ├── icons/  — generated Material Symbols lookup + repair workflow
│   └── voxel/  — Voxel platform / domain reference
└── workflows/    — the phased processes (build, plan, migrate, audit, cpt-lifecycle)
```

## Task-shape lookup


| Task shape | Reference |
|---|---|
| "Site prerequisites / plugin not loaded / why did `TemplateImporter` / `lean_seo_settings_set` fail?" | [`cpt-lifecycle.md`](../workflows/cpt-lifecycle.md) §Phase 0 |
| "Creating a transactional CPT (RFQ board / leads / inquiries / support tickets)" | [`cpt-lifecycle.md`](../workflows/cpt-lifecycle.md) + [`transactional-cpt-recipe.md`](voxel/transactional-cpt-recipe.md) |
| "Break up bulky single-paragraph text into rich text (bulleted steps) across many records / reformat a `texteditor` field CPT-wide" | [`bulk-rich-text.md`](curation/bulk-rich-text.md) |
| "Build a glossary / dictionary / defined-term CPT with SEO-perfect JSON-LD (DefinedTerm / DefinedTermSet / sameAs), or write a well-formed definition answer block" | [`seo-defined-terms.md`](voxel/seo-defined-terms.md) |
| "Write FAQ questions and answers for an article, service page, glossary term, local page, event, product, or Voxel content item" | [`../workflows/faq-authoring.md`](../workflows/faq-authoring.md) + [`faq-authoring.md`](voxel/faq-authoring.md) |
| "Geolocate a service / create a city version of a page / derive a geolocated service (`exp` under a `geo` city) / mirror a service under a city" | [`seo-geolocation-pages.md`](voxel/seo-geolocation-pages.md) + [`../workflows/geolocation.md`](../workflows/geolocation.md) |
| "Save/extract a section template / seed a build from a saved hero / reuse a stored section — the store + its conventions" | [`../templates/README.md`](../templates/README.md) + [`../templates/index.md`](../templates/index.md) (store) · [`../workflows/section-templates.md`](../workflows/section-templates.md) (extraction workflow) |
| "What stays a live dtag vs becomes Lorem Ipsum in a stored template / the placeholder + proper-noun denylist policy" | [`templates/placeholder-policy.md`](templates/placeholder-policy.md) |
| "Which Voxel field types exist in theme + voxel-addon?" | [`voxel-field-inventory.md`](voxel/voxel-field-inventory.md) |
| "Configure the lean-seo plugin's SEO output for a CPT (meta / schema / markdown / sitemap / permalinks)" — the phased process | [`../workflows/settings.md`](../workflows/settings.md) |
| "Repair an existing Voxel CPT", "runtime post-type drift", "CTA placeholders", "archive/search duplication", "Event JSON-LD status wrong" | [`../workflows/cpt-repair.md`](../workflows/cpt-repair.md) |
| "Improve Voxel/Elementor performance", "generated CSS", "LSCache", "N+1 queries", "frontend payload", "Lighthouse/CWV" | [`../workflows/performance.md`](../workflows/performance.md) + [`performance-patterns.md`](voxel/performance-patterns.md) |
| "How does lean-seo store settings / read Voxel fields / which token dialect does a surface use?" | [`lean-seo-settings-substrate.md`](voxel/lean-seo-settings-substrate.md) |
| "Set up / fix lean-seo title, description, canonical, OG/Twitter, per-CPT noindex" | [`lean-seo-metadata.md`](voxel/lean-seo-metadata.md) |
| "Configure lean-seo JSON-LD schema, map a Voxel relation/field into the graph, `@each` over a relation" | [`lean-seo-schema.md`](voxel/lean-seo-schema.md) |
| "The `.md` / markdown-for-agents twin is thinner than the rendered page — missing repeaters / relations / single-template loops / card grids" | [`lean-seo-markdown.md`](voxel/lean-seo-markdown.md) |
| "Add a CPT to the sitemap, noindex it, fix its permalink parent, internal linking" | [`lean-seo-crawl-permalinks.md`](voxel/lean-seo-crawl-permalinks.md) |
| "Add a 301 redirect / import redirects / redirect an old URL" | [`lean-seo-redirects.md`](voxel/lean-seo-redirects.md) |
| "Add Search Console / Bing / Yandex verification, or an analytics tag" | [`lean-seo-code.md`](voxel/lean-seo-code.md) |
| "WebP / `<picture>` / upload flattening / featured-image renaming" | [`lean-seo-media.md`](voxel/lean-seo-media.md) |
| "Generate unique featured/hero/OG images for posts/CPTs, attach to WordPress, QA, WebP, nuke AI metadata, verify uniqueness" | [`../workflows/image-generation.md`](../workflows/image-generation.md) + [`image-generation.md`](voxel/image-generation.md); resolve the installed `seo-image-gen` capability for global model/tool logic |
| "SEO-safe 503 maintenance mode (not noindex)" | [`lean-seo-maintenance.md`](voxel/lean-seo-maintenance.md) |
| "Cache purge / Last-Modified not updating / invalidate sitemaps after a change" | [`lean-seo-purge.md`](voxel/lean-seo-purge.md) |
| "Read / modify / debug the lean-seo plugin's PHP source — module architecture, SSOT predicates, a filter hook, why a CPT reaches (or misses) a crawl surface in code" | [`lean-seo-plugin-internals.md`](voxel/lean-seo-plugin-internals.md) + deep source ref [`lean-seo-crawl-permalinks-linking-reference.md`](voxel/lean-seo-crawl-permalinks-linking-reference.md) |
| "What config keys does Voxel field type X accept?" | [`voxel-field-types.md`](voxel/voxel-field-types.md) |
| "Gate a field to admins / logged-in / specific role" | [`voxel-field-visibility.md`](voxel/voxel-field-visibility.md) |
| "Build a reviews / DM / notification / follow surface" | [`voxel-timeline.md`](voxel/voxel-timeline.md) + [`voxel-tags.md`](voxel/voxel-tags.md) |
| "Build a custom search page with filters / sort / map" | [`voxel-search.md`](voxel/voxel-search.md) |
| "Add Stripe Connect / vendor / booking / membership / paid-listing flow" | [`voxel-commerce.md`](voxel/voxel-commerce.md) |
| "Configure post types / taxonomies / roles / collections / verification / async jobs / nav menus / Voxel widget catalog" | [`voxel-platform.md`](voxel/voxel-platform.md) |
| "What's the shape of an ef-card / ef-form / ef-wrapper widget?" | committed SSOT `cli/src/generated/widget-schemas.json` (preferred, offline) → [`ef-widgets.md`](ef/ef-widgets.md) → live `wpdev elementor:schema` (fallback) |
| "Which EF widget should I use? (router / phantom check / reserved keys / `$$type` envelopes)" | [`widgets.md`](ef/widgets.md) |
| "What settings does ts-search-form / ts-post-feed / ts-map / ts-template-tabs / ts-print-template take?" | [`ts-widgets.md`](voxel/ts-widgets.md) |
| "Build a CPT submission / edit form (ts-create-post)" | [`ts-widgets.md`](voxel/ts-widgets.md) §ts-create-post + [`../examples/ts-create-post.json`](../examples/ts-create-post.json) |
| "I'm building an ef-card and need to wire up the `tags` pill repeater or `ts_actions` action rows" | [`widgets.md`](ef/widgets.md) + [`actions.md`](ef/actions.md) |
| "I'm composing section backgrounds / assigning surface variants / building a masonry bento block" | [`section-rhythm.md`](ef/section-rhythm.md) + [`masonry.md`](ef/masonry.md) |
| "Map media doesn't load / is blank when scrolled into view, especially with LSCache/performance JS delay" | [`widgets.md`](ef/widgets.md) §Map media runtime (Leaflet / Google) — LSCache-safe lazy load |
| "Define / fix the card's action buttons (`ts_actions` strip / `cta_ts_actions`) — pick the right action type + cells" | [`card-actions.md`](../workflows/card-actions.md) (process) + [`actions.md`](ef/actions.md) (catalog) |
| "Pick a Material Symbols icon, replace a wrong icon, or audit icon usage in Elementor data" | [`material-symbols/README.md`](icons/material-symbols/README.md) (lookup) + [`lookup-and-repair.md`](icons/material-symbols/lookup-and-repair.md) (repair flow) |
| "Where does this Voxel option live / which template will render / how do revisions stack?" | [`template-resolution.md`](voxel/template-resolution.md) |
| "I'm composing a custom widget and need a part (Field, Banner, Headings…)" | [`ef-parts.md`](ef/ef-parts.md) |
| "I'm calling an `ef_*` helper and need its signature" | [`ef-helpers.md`](ef/ef-helpers.md) |
| "I need a dynamic-tag expression like `@post(field)` or `@if(...)`" | [`voxel-tags.md`](voxel/voxel-tags.md) |
| "I need a fixture for an existing widget" | `../examples/<widget>.json` (golden fixtures) |
| "I need to compose multi-source text (fallbacks, currency, relations, math)" | [`dynamic-text.md`](ef/dynamic-text.md) |
| "I'm building a single/archive template and need to plan sections" | [`page-planning.md`](../workflows/page-planning.md) — Phase 2 sub-pipeline (Field Inventory → SSOT Read → Archetypes → Blueprints → Adversarial review → Reconciliation → Approval) |
| "How do I verify the render / take a screenshot / assert layout / fetch the production page?" | [`browser.md`](verification/browser.md) — the `agent-browser` CLI protocol (no `mcp__*` browser server) |
| "What archetypes do I pick from (hero / specs-grid / detail-tabs / sidebar / relation-feed / faq / cta-footer / …)?" | [`page-plan-archetypes.md`](core/page-plan-archetypes.md) |
| "Which adversarial criterion catches X failure mode (thin templates / unsurfaced fields / heading hierarchy)?" | [`criteria.md`](core/criteria.md) + [`voxel-plan-reviewer.md`](subagents/voxel-plan-reviewer.md) |

## `core/` — read first, always

| File | What it is |
|---|---|
| [`rules.md`](core/rules.md) | The mandatory rules + success-criteria checklist. Read at the start of every build/audit/fix. |
| [`criteria.json`](core/criteria.json) + [`criteria.schema.json`](core/criteria.schema.json) | **Machine SSOT** for what gets checked, by scope+phase. Applicable criteria are processed in bounded batches with one result envelope per criterion. |
| [`criteria.md`](core/criteria.md) | Human-readable view of `criteria.json`. |
| [`command-surface.md`](core/command-surface.md) | Voxel/Elementor/lean-seo `wpdev` command surface used by this skill. |
| [`wpdev-ops.md`](core/wpdev-ops.md) | Generic wpdev ops appendix: site lifecycle, DB, backup, remote sync, diagnostics, purge. |
| [`wpdev-coverage.md`](core/wpdev-coverage.md) | Which CLI verbs are surfaced into the skill and where; drift-gated against `cli/src/index.ts`. |
| [`parallel-dispatch.md`](core/parallel-dispatch.md) | The atomic-scope subagent contract every fan-out obeys. |
| [`blueprint-format.md`](core/blueprint-format.md) | The Plan Document blueprint table format. |
| [`page-plan-contract.md`](core/page-plan-contract.md) · [`page-plan-archetypes.md`](core/page-plan-archetypes.md) | Plan/Blueprint output schema and archetype/vocabulary catalog. |
| [`elementor-mutation-tools.md`](core/elementor-mutation-tools.md) · [`build-troubleshooting.md`](core/build-troubleshooting.md) | Existing-data write mechanisms and conditional failure recovery. |

## `ef/` — EF V4 atomic widget reference

| File | What it is |
|---|---|
| [`widgets.md`](ef/widgets.md) · [`ef-widgets.md`](ef/ef-widgets.md) | Widget catalog + per-widget prop tables (generated from the schema SSOT). |
| [`ef-parts.md`](ef/ef-parts.md) · [core](ef/ef-parts-core.md) · [media/nav](ef/ef-parts-media-nav.md) · [row surfaces](ef/ef-parts-row-surfaces.md) | Parts index and its three concern-owned catalogs. |
| [`ef-helpers.md`](ef/ef-helpers.md) · [atomic/settings](ef/ef-helpers-atomic-settings.md) · [loops/actions](ef/ef-helpers-loops-actions.md) · [layout/assets](ef/ef-helpers-layout-assets.md) · [data/forms/admin](ef/ef-helpers-data-forms-admin.md) | Helper index and its four concern-owned catalogs. |
| [`card-scaffolding.md`](ef/card-scaffolding.md) | `wpdev voxel:cards` variants and registration behavior. |
| [`masonry.md`](ef/masonry.md) · [`section-rhythm.md`](ef/section-rhythm.md) | Bento/masonry grid composition (`col_span` / `row_span`, track ratios) and section background/spacing rhythm. |
| `widget-schemas.json` | The generated schema SSOT mirror (synced by `wpdev elementor:codegen`; do not hand-edit). |

## `icons/` — icon lookup + repair

| File | What it is |
|---|---|
| [`material-symbols/README.md`](icons/material-symbols/README.md) | Short-context entrypoint for the full generated Material Symbols library installed by Elementor Framework. |
| [`material-symbols/top-picks.md`](icons/material-symbols/top-picks.md) | Curated use-case map for common Voxel/EF icon decisions. |
| [`material-symbols/lookup-and-repair.md`](icons/material-symbols/lookup-and-repair.md) | Choose, verify, and repair icons using `wpdev elementor:icon-search`, `elementor:icons`, and `elementor:set-value`. |
| [`material-symbols/search.tsv`](icons/material-symbols/search.tsv) | Full generated grep index: icon name, EF value, codepoint, Google category/popularity, search terms. |
| [`material-symbols/metadata.json`](icons/material-symbols/metadata.json) | Compact cache of Google Symbols tags/categories for EF-installed icons. |
| [`material-symbols/by-prefix/`](icons/material-symbols/by-prefix/) | Generated alphabetical shards for nearby-name inspection without loading all 4k+ icons. |

## `voxel/` — Voxel platform / domain

| File | What it is |
|---|---|
| [`voxel-field-inventory.md`](voxel/voxel-field-inventory.md) · [field index](voxel/voxel-field-types.md) · [core](voxel/voxel-field-types-core.md) · [advanced](voxel/voxel-field-types-advanced.md) · [patterns](voxel/voxel-field-types-patterns.md) · [visibility](voxel/voxel-field-visibility.md) | Field availability, configuration, selection patterns, storage, and visibility. |
| [tag index](voxel/voxel-tags.md) · [expressions](voxel/voxel-tags-expressions.md) · [runtime](voxel/voxel-tags-runtime.md) | Dynamic expressions/modifiers and loops/visibility/feeds/relations. |
| [search index](voxel/voxel-search.md) · [query](voxel/voxel-search-query.md) · [index/maps](voxel/voxel-search-index-maps.md) | Search/filter/sort behavior and index/geospatial storage. |
| [timeline index](voxel/voxel-timeline.md) · [social](voxel/voxel-timeline-social.md) · [messaging](voxel/voxel-timeline-messaging.md) | Timeline/review/social behavior and direct messaging/notifications. |
| [commerce index](voxel/voxel-commerce.md) · [products](voxel/voxel-commerce-products.md) · [plans](voxel/voxel-commerce-plans.md) · [payments](voxel/voxel-commerce-payments.md) | Products/bookings, memberships/listings, and payment/provider behavior. |
| [platform index](voxel/voxel-platform.md) · [content model](voxel/voxel-platform-content-model.md) · [widgets/relations](voxel/voxel-platform-widgets-relations.md) · [runtime](voxel/voxel-platform-runtime.md) | Platform catalog split by content model, UI/data relations, and runtime services. |
| [`template-resolution.md`](voxel/template-resolution.md) · [`ts-widgets.md`](voxel/ts-widgets.md) | Template resolution and `ts-*` widget behavior. |
| [`transactional-cpt-recipe.md`](voxel/transactional-cpt-recipe.md) · [`cpt-lifecycle-operations.md`](voxel/cpt-lifecycle-operations.md) | Transactional/private CPT deltas and conditional lifecycle operations. |
| [`lean-seo-settings-substrate.md`](voxel/lean-seo-settings-substrate.md) | The shared lean-seo config layer — module registry, `lean_seo_{category}` option store, the `lean_seo_available_field_groups` Voxel field catalog, the `includes/voxel.php` guard/resolver layer, the four token dialects. Read before any lean-seo settings work. |
| [`lean-seo-metadata.md`](voxel/lean-seo-metadata.md) | lean-seo Meta surface — title/description/canonical/OG/Twitter/noindex; `<kind>_<slug>` scope keys in `lean_seo_meta`; the `%token%` + `%vx()%` dialect; `h1` title-key default; per-post `_lean_seo_*` overrides; Voxel/profile canonicalization. |
| [`lean-seo-schema.md`](voxel/lean-seo-schema.md) | lean-seo Schema surface — per-target `lean_seo_schema:{target}` JSON-LD; the `prefix:key\|transform` source grammar (22 prefixes); `voxel:` / `relation:` / `relation_field:` / `related:` / `hierarchy:` Voxel resolvers; `@each`/`@map`/`@ref`/`@require` control keys; transforms. |
| [`lean-seo-crawl-permalinks.md`](voxel/lean-seo-crawl-permalinks.md) | lean-seo Crawl/Permalinks/Linking — sitemap CPT enumeration (`tweak`-category lists), noindex overlay, `_lean_seo_uri` canonical SSOT + auto-parent, `permalink_default`, author↔profile URLs, breadcrumbs, `wp lean-seo permalinks` CLI, rewrite-flush/cache-purge gotchas. |
| [`lean-seo-markdown.md`](voxel/lean-seo-markdown.md) | The `lean-seo` markdown-for-agents generator — field-map resolution order, the single-template content gap + frontend-fetch fallback, `@post(lean_seo:rendered_html)`, redundancy guard, parity verification. |
| [`lean-seo-redirects.md`](voxel/lean-seo-redirects.md) | 301 manager — custom `lean_seo_redirects` table, `template_redirect` prio-5 handler, DAY-cached active map, `lean_seo_redirects_insert` write API, CSV import, PM URI-divergence emitter. |
| [`lean-seo-code.md`](voxel/lean-seo-code.md) | Analytics + verification tags — `lean_seo_tag` option, the tag registry (GA4/GTM/Plausible/… + `gsc_code`/`bing_code`/`yandex_code` verification meta), the `*_code` fallback, `wp_head` prio-1 output. |
| [`lean-seo-media.md`](voxel/lean-seo-media.md) | WebP + `<picture>` output-buffer wrap (reaches Voxel/Elementor), upload flattening, featured-image renaming to `{slug}-{post-type}` (feeds OG image + `featured_img`). |
| [`lean-seo-maintenance.md`](voxel/lean-seo-maintenance.md) | SEO-safe 503 maintenance screen — enabled-state IS the switch; 503 + Retry-After, robots.txt stays 200, never noindex, admin bypass; EF-token theming. |
| [`lean-seo-purge.md`](voxel/lean-seo-purge.md) | LiteSpeed cache-purge bridge — `lean_seo_purge`/`lean_seo_purge_all`/`lean_seo_bump_cache_epoch` API, the Last-Modified epoch, the WP hooks that trigger purges, the non-purge perf tweaks. |
| [`voxel-lean-seo-routing.md`](voxel/voxel-lean-seo-routing.md) · [`claude-seo-authoring.md`](voxel/claude-seo-authoring.md) | Voxel-to-lean-seo ownership routing and optional source-supported authoring handoff. |

## Specialized Supporting References

| File | Exclusive purpose |
|---|---|
| [`emcp-wordpress-mcp.md`](core/emcp-wordpress-mcp.md) | Optional WordPress MCP transport when the local `wpdev` path is unavailable. |
| [`content-quality-worker.md`](verification/content-quality-worker.md) | Evidence contract for delegated visible-copy quality checks. |
| [`lean-seo-plugin-internals.md`](voxel/lean-seo-plugin-internals.md) | The plugin's **source architecture** (for reading/modifying/debugging its PHP) — module registry, unified settings store, the SSOT crawl predicates, meta/schema token grammars, the agnostic field-catalog seam, author↔profile seam, and code-level gotchas. |
| [`lean-seo-crawl-permalinks-linking-reference.md`](voxel/lean-seo-crawl-permalinks-linking-reference.md) | Exhaustive **source-verified** reference for the crawl / permalinks / linking modules — exact function names, file paths, option keys, hooks, and Voxel interactions. The deepest developer reference. |

## Full layer index


| Layer | File | Owns |
|---|---|---|
| **Routing** | this file | Request → command/reference mapping |
| **Rules** | [`references/core/rules.md`](core/rules.md) | Eight rules, success criteria |
| **Page planning** | [`../workflows/page-planning.md`](../workflows/page-planning.md) | Phase 2 sub-pipeline — Field Inventory, SSOT Read, Archetype Selection, Section Blueprints, adversarial review (full reviewer panel, parallel, one concern each), reconciliation, computed §2g gate. Mandatory for any non-trivial build or migration. |
| **CLI** | [`references/core/command-surface.md`](core/command-surface.md), [`references/core/wpdev-ops.md`](core/wpdev-ops.md), [`references/core/wpdev-coverage.md`](core/wpdev-coverage.md) | Voxel/Elementor command surface + generic ops appendix + drift-gated coverage map |
| **Dispatch** | [`references/core/parallel-dispatch.md`](core/parallel-dispatch.md), §Orchestrating the parallel fan-outs (above) | Atomic-scope subagent contract; Workflow-tool fan-out (preferred when opted in) vs inline single-message dispatch (fallback) |
| **CPT lifecycle** | [`../workflows/cpt-lifecycle.md`](../workflows/cpt-lifecycle.md), [`references/core/blueprint-format.md`](core/blueprint-format.md) | 7-phase CPT creation, blueprint skeleton |
| **Voxel field inventory** | [`references/voxel/voxel-field-inventory.md`](voxel/voxel-field-inventory.md) | Exact native Voxel + voxel-addon field availability — type key, PHP class, source file, storage, replacement status |
| **Voxel field types** | [`references/voxel/voxel-field-types.md`](voxel/voxel-field-types.md) | Deep native field config — PHP class, config, validation, dynamic-tag exposure |
| **Voxel field visibility** | [`references/voxel/voxel-field-visibility.md`](voxel/voxel-field-visibility.md) | All 30 visibility rule types — JSON shape, AND/OR groups, admin-only / logged-in / role recipes |
| **Voxel timeline** | [`references/voxel/voxel-timeline.md`](voxel/voxel-timeline.md) | Timeline, Reviews, Comments, DMs, Notifications, Follows |
| **Voxel commerce** | [`references/voxel/voxel-commerce.md`](voxel/voxel-commerce.md) | Products, Bookings, Memberships, Paid Listings, Claims, Promotions, Stripe/Paddle/PayPal |
| **Voxel search** | [`references/voxel/voxel-search.md`](voxel/voxel-search.md) | Search filters, sorts, Index Table, Maps, Recurring Dates |
| **Voxel platform** | [`references/voxel/voxel-platform.md`](voxel/voxel-platform.md) | Post Types, Taxonomies, Roles, Collections, ts-* widgets, Relations, Verification, File Uploader, Stats, Dynamic Data, Async Jobs, Privacy, Nav Menus, Library, Text Formatter, Auth, Print Templates |
| **lean-seo settings** | [`../workflows/settings.md`](../workflows/settings.md) + [`references/voxel/lean-seo-settings-substrate.md`](voxel/lean-seo-settings-substrate.md), [`lean-seo-metadata.md`](voxel/lean-seo-metadata.md), [`lean-seo-schema.md`](voxel/lean-seo-schema.md), [`lean-seo-crawl-permalinks.md`](voxel/lean-seo-crawl-permalinks.md), [`lean-seo-markdown.md`](voxel/lean-seo-markdown.md) | Configure lean-seo SEO output per Voxel CPT — Routing workflow (Phase 0 preflight → Route M/S/K/C → Phase V verify) over four surfaces (metadata, schema, markdown, crawl/permalinks), all agnostic via the shared field-catalog substrate; each surface reference carries its option key, token dialect, and Voxel resolvers |
| **lean-seo adjacent modules** | [`references/voxel/lean-seo-redirects.md`](voxel/lean-seo-redirects.md), [`lean-seo-code.md`](voxel/lean-seo-code.md), [`lean-seo-media.md`](voxel/lean-seo-media.md), [`lean-seo-maintenance.md`](voxel/lean-seo-maintenance.md), [`lean-seo-purge.md`](voxel/lean-seo-purge.md) | The SEO-relevant non-CPT-routed modules — 301 redirects (custom table), analytics + Search-Console/Bing/Yandex verification tags, WebP/`<picture>` + featured-image renaming, SEO-safe 503 maintenance, and the LiteSpeed cache-purge/Last-Modified-epoch invalidation API the other surfaces depend on |
| **lean-seo plugin internals** | [`references/voxel/lean-seo-plugin-internals.md`](voxel/lean-seo-plugin-internals.md) + [`lean-seo-crawl-permalinks-linking-reference.md`](voxel/lean-seo-crawl-permalinks-linking-reference.md) | The plugin's **source architecture** for reading/modifying/debugging its PHP — module registry, unified settings store, SSOT crawl predicates, meta/schema grammars, field-catalog + author↔profile seams, code-level gotchas, and the exhaustive source-verified crawl/permalinks/linking reference |
| **Build pipeline** | [`../workflows/build.md`](../workflows/build.md) | gather → plan → fan-out → assemble → write |
| **Migration** | [`../workflows/migrate.md`](../workflows/migrate.md) | Legacy V3 → EF V4 aggressive consolidation; Iron Law (drop styling/structure, preserve the rendered content — the words a visitor sees); content baseline captured via the `agent-browser` CLI against production URL (`?p=<post_id>`) — see [`references/verification/browser.md`](verification/browser.md); `migrate:main`/`migrate:containers`; parallel fan-out; migration-preservation criterion is the data-loss guard |
| **Browser verification** | [`references/verification/browser.md`](verification/browser.md) | The `agent-browser` CLI protocol (SSOT) — parallel `--session` isolation, command table, mandatory computed-style layout assertions, read-the-screenshot rule, production-page baseline, browser-unavailable fallback. Tool surface for Phase 6 / audit Stream D / migration Phase 5. No MCP browser server. |
| **Audit pipeline** | [`../workflows/audit.md`](../workflows/audit.md), [`references/audit/briefs.md`](audit/briefs.md) | Top-down walk, bottom-up fix, brief templates, silent-failure detection probes, confirmed/suspected confidence gate |
| **Behavior Contract** | [`references/verification/behavior-contract.md`](verification/behavior-contract.md) | Pre-mutation gate for existing-data fixes — triple + DOM-text baseline falsifier, command-host authored |
| **EF widgets** | [`references/ef/ef-widgets.md`](ef/ef-widgets.md), [`references/ef/widgets.md`](ef/widgets.md) | All 4 registered EF widgets/elements with deep schema + thin router |
| **EF layout** | [`references/ef/masonry.md`](ef/masonry.md), [`references/ef/section-rhythm.md`](ef/section-rhythm.md) | Bento/masonry grid composition, anchor-card spans, section background ladder, surface/spacing rhythm |
| **TS widgets** | [`references/voxel/ts-widgets.md`](voxel/ts-widgets.md) | Voxel theme `ts-*` widget settings — Voxel-native vs EA4V-extension split, `ts-create-post` deep-dive |
| **EF parts** | [`references/ef/ef-parts.md`](ef/ef-parts.md) | All EF parts — 10 user-facing (Action_Slot, Actions, Banner, Field, Headings, Heading_Enums, Icon, Media, Nav_Item, Tags) + base contracts, Media handlers, Nav traits |
| **EF helpers** | [`references/ef/ef-helpers.md`](ef/ef-helpers.md) | `ef_*` helper catalog — full-doc entries for the build-critical surface + indexed entries for the rest. Counts auto-drift; the file warns against hardcoding totals. |
| **Cards & actions** | [`references/ef/widgets.md`](ef/widgets.md), [`references/ef/actions.md`](ef/actions.md), [`../workflows/card-actions.md`](../workflows/card-actions.md) | ef-card `tags` repeater, `ts_actions` repeater (catalog); card-actions workflow (define/fix the action strip, SSOT-validated) |
| **Icons** | [`references/icons/material-symbols/README.md`](icons/material-symbols/README.md), [`references/icons/material-symbols/lookup-and-repair.md`](icons/material-symbols/lookup-and-repair.md), [`references/icons/material-symbols/top-picks.md`](icons/material-symbols/top-picks.md), generated [`search.tsv`](icons/material-symbols/search.tsv) | EF Material Symbols lookup, exact `ms:ms ms-<name>` storage strings, Google-metadata-enriched full-library index, ranked `elementor:icon-search`, wrong-icon repair via `elementor:icons` / `elementor:set-value` |
| **Dynamic** | [`references/voxel/voxel-tags.md`](voxel/voxel-tags.md), [`references/ef/dynamic-text.md`](ef/dynamic-text.md) | Tag syntax / loops / visibility, text-composition recipes |
| **Resolution** | [`references/voxel/template-resolution.md`](voxel/template-resolution.md) | Voxel option keys, template resolution order, revision distinctions |
| **Defined terms (SEO)** | [`references/voxel/seo-defined-terms.md`](voxel/seo-defined-terms.md) | Glossary/DefinedTerm CPT recipe — answer-block field model, DefinedTerm + DefinedTermSet + sameAs schema, flat URLs, anti-thin-content long-form body, E-E-A-T |
| **FAQ authoring (SEO)** | [`../workflows/faq-authoring.md`](../workflows/faq-authoring.md), [`references/voxel/faq-authoring.md`](voxel/faq-authoring.md), [`references/subagents/voxel-faq-author.md`](subagents/voxel-faq-author.md) | Visible FAQ Q&A workflow for one content source - natural-language questions, answer-first self-contained answers, source evidence, page-type gates, and read-only subagent authoring |
| **Geolocated pages (SEO)** | [`references/voxel/seo-geolocation-pages.md`](voxel/seo-geolocation-pages.md) + [`../workflows/geolocation.md`](../workflows/geolocation.md) | Derive an `exp` service into a per-city mirror under a `geo` post — city-nested URL, city-aware breadcrumb/title/schema `areaServed` gate, field-enforced uniqueness (anti-doorway swap test), local-SEO checklist scope split, Phase 0→4 workflow |
| **Curation** | [`../workflows/curation.md`](../workflows/curation.md), [`references/curation/cli-map.md`](curation/cli-map.md), [`references/curation/field-semantics.md`](curation/field-semantics.md), [`references/curation/bulk-rich-text.md`](curation/bulk-rich-text.md), [`references/curation/content-surgery.md`](curation/content-surgery.md), [`references/curation/backup-diff-and-surgical-restore.md`](curation/backup-diff-and-surgical-restore.md), [`references/curation/telegraphic-fragment-repair-field-harness.md`](curation/telegraphic-fragment-repair-field-harness.md), [`references/curation/klarc-french-copy-corruption.md`](curation/klarc-french-copy-corruption.md), [`references/curation/voxel-dynamic-content-surgery.md`](curation/voxel-dynamic-content-surgery.md), [`references/curation/sitewide-ai-marker-cleanup.md`](curation/sitewide-ai-marker-cleanup.md), [`references/curation/lifecycle-checklists.md`](curation/lifecycle-checklists.md), [`references/curation/merge-delete-safety.md`](curation/merge-delete-safety.md) | Voxel entity-data curation — 4-phase pipeline (Discover → Plan → Execute → Verify) with merge/delete safety gate; create/edit/merge/delete records, bulk rich-text reformatting of `texteditor` fields (QA-gated fan-out), profile↔user invariant, relation rewiring; **plus content surgery** — repair corrupted/degraded visible copy with backup-diff + surgical token restore, telegraphic-fragment repair harness, Voxel dynamic-field source-map, and the site-wide de-AI marker cleanup scan |
| **Content surgery** | [`references/curation/content-surgery.md`](curation/content-surgery.md) | Repair corrupted/degraded WordPress visible copy with minimal auditable edits (no batch restore) — scope public content, backup-as-intent, exact field/post patches, corruption-pattern scan, live verify; SAFE-vs-FLAGGED token restore, missing-noun vs voluntary-rewrite disambiguation, full-corpus quality-audit escalation |
| **lean-seo excerpts** | [`references/voxel/lean-seo-excerpt-meta-descriptions.md`](voxel/lean-seo-excerpt-meta-descriptions.md), [`lean-seo-excerpt-bulk-range-audit.md`](voxel/lean-seo-excerpt-bulk-range-audit.md), [`lean-seo-ninerouter-concurrent-generation.md`](voxel/lean-seo-ninerouter-concurrent-generation.md) | Bulk-optimize `post_excerpt` / real per-CPT description source as SEO meta descriptions — decode the lean-seo description resolver FIRST (`desc_template_<type>` wins over excerpt), 120–155 limit, per-CPT intent rules, LLM row audit, concurrent 9router generation with validation gate, idempotent no-purge apply, author-bio `.md` truncation fix |
| **Template transplants** | [`references/ef/template-transplants.md`](ef/template-transplants.md) | Copy a section wrapper between templates + template-JSON surgery — inspect raw `_elementor_data` (never infer parent/child from flattened dump), preserve display keys / adapt feed keys, recursive ID regen on clones, re-import with `--save`, computed-style verify; ties to sitewide-ai-marker-cleanup + voxel-lean-seo-routing |
| **Section templates (store)** | [`../templates/README.md`](../templates/README.md), [`../templates/index.md`](../templates/index.md), [`../workflows/section-templates.md`](../workflows/section-templates.md) | The `templates/` store — reusable `global \| section \| page` starting trees, one folder per section (`template.json` + `meta.yml`), master index, on-disk conventions, SSOT-wins discipline (a template is a starting tree, never authoritative spec), and the extraction + refresh/migrate workflow; seeded heroes `hero-services-search` / `hero-city-geo`. Build wiring: [`../workflows/build.md`](../workflows/build.md) Phase 0 seed-from-template branch + §2d bind-to-template |
| **Template placeholder policy** | [`references/templates/placeholder-policy.md`](templates/placeholder-policy.md) | The machine-readable SSOT for template sanitization — the universal-dtag allowlist (8 regex classes kept live), the Lorem-Ipsum-everything-else rule, and the proper-noun denylist pattern classes; consumed by both the extraction sanitizer and the template linter |
| **Voxel changelog** | [`references/voxel/voxel-changelog.md`](voxel/voxel-changelog.md) + [`../scripts/build_changelog_json.py`](../scripts/build_changelog_json.py) | Turn the canonical `voxel_release` feed into flat queryable JSON (`{version,date,type,description,source_url}`) — "which version added X", "does Voxel do this natively now", "what changed in X.Y"; stdlib-only fetch/parse/classify, `jq` query recipes |

## Adding a reference

Drop knowledge into `core/`, `ef/`, `icons/`, or `voxel/` and add a row here. Put a *phased process* in [`../workflows/`](../workflows/README.md), not here. Keep each file single-concern. Lateral cross-links are fine, but this file is the full layer index so `SKILL.md` can stay small. Cross-links are relative; `scripts/lint.sh` verifies every link target, `../`-display, and backtick `../`-path resolves.
