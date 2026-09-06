# Voxel-builder wpdev namespace coverage map

What this is: a skill-scoped map, not a repository-wide command inventory or ownership claim. It covers every current `wpdev` command in the namespaces and standalone surfaces this skill's mission selects (`voxel:`, `elementor:`, `audit*`, `schema:*`, `rebuild --only *`, `smoke`, `headings`, `perf`, `quality`), with a coverage status and the specific agent / command / reference that surfaces it. Nested `elementor:*` families are sections of the current `elementor:` namespace, including `elementor:ef:`, `elementor:strip:`, `elementor:migrate:`, `elementor:revisions:`, `elementor:reset:`, and `elementor:codegen*`. Companion to [`command-surface.md`](command-surface.md) — that file is the prose cheatsheet for currently-surfaced commands; this file is the namespace audit table that catches drift.

How to keep this current: when wpdev gains a new command in any of the namespaces above, add a row here. Status taxonomy is a closed set — pick exactly one:

- `surfaced` — the plugin actively invokes the command via at least one agent, command, or reference.
- `surface-pending` — relevant to the skill's mission, but not yet wired up. Each row carries a 1-line plan for where it will land.
- `out-of-scope` — wpdev exposes it, but it lives outside the build / audit / CPT-lifecycle / introspection mission. Each row carries a 1-line rationale.
- `defer` — relevant but waiting on usage data, ergonomics work, or a CLI-side flag the plugin needs. Each row carries a 1-line rationale.

Agents / commands / references referenced in the `Location` column live under `Development/skills/voxel-builder/`.

Completeness is enforced mechanically: `scripts/lint.sh` §"CLI verb drift" cross-checks this file against the live CLI registry (`cli/src/index.ts`) on every run — every `elementor:`/`voxel:` verb the CLI exposes must have a row here, and no verb in the "verified absent" list below may exist in the registry. The build fails otherwise, so this map can't silently rot.

## `voxel:` namespace

| Command | Status | Location | Rationale |
|---|---|---|---|
| `voxel:admin-menu` | `defer` | n/a | Reads or adjusts Voxel admin-menu settings. Operator/admin UX territory; surface only if a future curation workflow needs deterministic menu repair. |
| `voxel:archives` | `surfaced` | `workflows/archive-search-pages.md` (archive scaffolding); pairs with `elementor:verify:loop-render` for the post-build proof | Scaffolds Voxel CPT archive templates as EF query-backed loops (header + paginated results grid). Mission-critical: archives are EF loops, so this is the supported alternative to hand-authoring `_elementor_data`. |
| `voxel:assign` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 6 | Assigns templates to roles; canonical Phase 6 step. |
| `voxel:backfill-authors` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 6 | Useful for CPTs whose posts are missing or have stale `post_author`. |
| `voxel:cache` | `surfaced` | `references/core/command-surface.md`; called after CPT-registry mutations | Site-level Voxel cache clear; companion to `rebuild --only purge`. Only action is `clear`. |
| `voxel:cards` | `surfaced` | the cards flow (`workflows/build.md` §Cards), `workflows/build.md` §Cards | Mandatory by rule 3 — never hand-write the card role. |
| `voxel:comparator` | `surfaced` | `references/voxel/voxel-field-visibility.md` §Choosing the right comparator for dtag visibility rules | Resolves the correct dtag visibility comparator (`is_equal_to` vs `contains`) for a Voxel field / repeater sub-field from its field type — the SSOT for the "fragile vis-gate on structured fields" fix class. |
| `voxel:create` | `surfaced` | the CPT lifecycle (`workflows/cpt-lifecycle.md`), `workflows/cpt-lifecycle.md` Phase 1 | Creates CPT + 4 blank templates. |
| `voxel:data` | `surfaced` | `voxel-widget-builder` (data introspection step), `voxel-schema-detective` (CPT-key fallback), `workflows/content-generation.md` / `workflows/curation.md` write gates | Reads rendered field values and `core` (`post_title`, `post_excerpt`, `post_content`) on a real post; required before/after evidence for content writes. |
| `voxel:delete` | `out-of-scope` | n/a | Destructive operational tooling. The plugin's mission is build/audit/lifecycle, not CPT teardown. |
| `voxel:empty` | `surfaced` | `voxel-page-auditor` `[G]`-tier (advisory) | Finds Voxel fields with no data across published posts — surfaces unused fields as audit Improvement findings. |
| `voxel:export` | `defer` | n/a | Cross-site CPT migration. Useful but not part of the audit/build mission. Revisit when usage data justifies. |
| `voxel:field-schema` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 2; `workflows/field-metadata.md` Phase 4; `references/core/command-surface.md` §CPT introspection | Corruption-proof top-level field-definition merge. Lifecycle owns creation-time blueprint convergence; field-metadata owns recursive UX metadata remediation and verification. |
| `voxel:fields` | `surfaced` | the CPT lifecycle Phase 2 (`workflows/cpt-lifecycle.md`), `voxel-widget-builder`, `voxel-schema-detective` | Lists CPT fields — valid `@post(<key>)` tags. |
| `voxel:filters` | `surfaced` | `references/core/command-surface.md` §CPT introspection; `workflows/audit.md` reindex-after-filter failure class | Audits or upserts Voxel CPT search filters (`--mode baseline` universal filters, `--mode derive` per-field filters, `--prune` orphan cleanup); changed filters require recreate+reindex. Scope note: reads only `voxel:post_types[<cpt>].search.filters`, so it never sees stale filter keys stored in `_elementor_data` — audit those separately per `workflows/archive-search-pages.md` §Stored Search Config Drift. |
| `voxel:heading-curator` | `surface-pending` | will surface in the `voxel-heading-curator` agent (read the cache instead of re-extracting) | Extracts production heading phrasings from peer single templates and writes a per-site cache the `voxel-heading-curator` agent should consume — replaces re-running `voxel:templates` + `elementor:dump` extraction on every plan dispatch. |
| `voxel:imports` | `surfaced` | `workflows/database-cleanup.md` (halt a running import before cleanup mutates rows underneath it) | Halts, resumes, or inspects Voxel Addon import execution on a site. Use it to stop a running import before mutating the CPT registry underneath it. |
| `voxel:import-policy` | `surfaced` | `workflows/database-cleanup.md` (the criterion that decides what `voxel:imports` admits) | Shows, sets, or clears the LLM eligibility criterion product imports are screened against (`show`/`set`/`clear`/`check`, `--scope` defaulting to `products:default:all`, which every brand inherits). Pairs with `voxel:imports`: that command controls whether an import runs, this one controls what it is allowed to admit, so a surprising import result is worth checking here before blaming the importer. |
| `voxel:integrity` | `surfaced` | `references/subagents/voxel-integrity-reviewer.md`, `workflows/integrity-loop.md` | Read-only, resumable integrity scan across all Voxel CPT records and registered taxonomy terms. Read-only, so it is always safe as a first probe. |
| `voxel:openapi` | `defer` | n/a | Exports or inspects a Voxel OpenAPI surface. API documentation tooling, not part of page/template build, audit, or icon selection workflows. Surface only if a future API-reference workflow needs it. |
| `voxel:product-price-parity` | `surfaced` | `references/voxel/voxel-commerce-products.md` (price rendering) | Proves `@post(product_price)` matches the `ts-product-price` widget byte-for-byte across real posts, so a dtag-rendered price in an EF card cannot silently diverge from the widget. Reports which pricing branches it actually saw and warns on any branch the sample never exercised, rather than printing a green tick over untested cases. `--source` loads the controller from a voxel-addon checkout for a pre-merge proof, where the default answers the different question of whether the code the site currently runs is correct. |
| `voxel:products-cleanup` | `defer` | n/a | Classifies Voxel products as matcha / non-matcha / ambiguous and can trash the non-matcha bucket. Site-specific (best-matcha) curation policy rather than a general Voxel verb; revisit if a second site needs the same split. |
| `voxel:sample` | `surfaced` | the build workflow (`workflows/build.md`) Phase 1, `page-planning.md` §2a | Ranks published posts of a CPT by completeness (filled fields + relations + repeaters); exports the top N to a temp folder so the Field Inventory samples the richest real data. |
| `voxel:apply-content` | `surfaced` | `references/core/rules.md` rule 9; `workflows/content-generation.md` Phase 4; `workflows/curation.md` write-path gate | Manifest-driven batch content apply: preflights `expectedBeforeSha256` per row, dry-runs by default, `--yes --rollback <path>` applies with per-record read-back + reindex and auto-rollback on any row failure. Preferred path for validated multi-record content batches; single-field writes still use `voxel:set-field`. |
| `voxel:set-field` | `surfaced` | `references/core/rules.md` rule 9; `references/curation/cli-map.md`; `workflows/curation.md`, `workflows/content-generation.md`, `references/curation/bulk-rich-text.md`, `references/curation/field-semantics.md`, `references/curation/lifecycle-checklists.md` | Writes field values on a Voxel post (text/meta, post-relations) via the Voxel field API, and routes the Voxel `title`/`description` aliases to `post_title`/`post_content` via `wp_update_post` itself (no separate core-column call, no silent no-op). Also accepts explicit core keys `post_title`/`post_content`/`post_excerpt`. Single-field write path; sanctioned per core rule 9. |
| `voxel:settings` | `surfaced` | `references/icons/material-symbols/lookup-and-repair.md` (icon field repair/provisioning companion), `references/core/command-surface.md` | Reads and mutates `voxel:post_types`, including `ensure-field` for icon fields and `--migrate-image-ids` for legacy attachment-backed SVG icon metadata. |
| `voxel:sorting` | `surfaced` | `references/core/command-surface.md` §CPT introspection; `workflows/audit.md` reindex-after-filter failure class | Audits or upserts the standard Voxel search-order set across one or all CPTs; preserves custom orders by default, can `--replace`, and reindexes changed CPTs unless disabled. |
| `voxel:page` | `surfaced` | `references/voxel/template-resolution.md` (referenced as introspection helper) | Shows Voxel templates used on a page given its URL path. |
| `voxel:product-form` | `surfaced` | `references/voxel/voxel-commerce-products.md` (product-form gotcha) | Read-only gate that every enabled product subfield resolves to a shipped Vue component or create-post template, exiting non-zero when one cannot render. Reach for it after enabling a product module, and before trusting a product edit screen: an enabled module whose component was never shipped does not degrade, it throws while Vue stringifies the bound props, so the Fields metabox renders blank and a save through it writes a null payload over existing product meta. A site with no Voxel product types reports "nothing to check" rather than passing clean. |
| `voxel:rekey` | `surfaced` | `workflows/cpt-lifecycle.md` (renaming a key after posts exist), `workflows/database-cleanup.md` (orphans left by a partial rename) | Renames a Voxel post-type or taxonomy key everywhere it is stored: registry, posts, Elementor data, plugins, indexes. Reach for this instead of editing the registry key by hand — a manual rename leaves stored `_elementor_data` and index tables pointing at the old key, which surfaces later as empty archives rather than as an error. |
| `voxel:relation-integrity` | `surfaced` | `workflows/database-cleanup.md` (orphaned relation endpoints), `references/voxel/voxel-platform-widgets-relations.md` | Read-only check over `wp_voxel_relations` for cross-parent bleed, orphaned endpoints, and post-type mismatches. Reach for it when a relation field returns another parent's children: a binder that mutates a shared field prototype produces bleed that is invisible per-post and only shows up as an aggregate. |
| `voxel:repair-options` | `defer` | n/a | Repairs corrupted Voxel option blobs (post-type registry, template assignments, etc.). Operator territory; surface if a Phase 0 environment check needs it. |
| `rebuild --only reindex [--recreate]` | `surfaced` | the CPT lifecycle Phase 2 (`workflows/cpt-lifecycle.md`) (mandatory post-write step), `workflows/cpt-lifecycle.md` Phase 2 | Reindexes all Voxel-managed post types in one pass; required after every blueprint write. Use `--recreate` after a blueprint changes search filters — it rebuilds each index table's column set first. (Replaces the retired per-type reindex command.) |
| `voxel:status` | `surfaced` | `voxel-page-auditor` `[G]`-tier, `voxel-schema-detective`, `references/voxel/voxel-commerce-products.md` (product-form gotcha) | Shows Voxel index health for all post types — surfaces stale/broken indexes. Also proves every enabled product subfield resolves to a shipped form component: a module left enabled in `voxel:product_types` after its component was removed renders the wp-admin Fields metabox entirely blank and can erase product meta on save. |
| `voxel:templates` | `surfaced` | `voxel-schema-detective`, `references/voxel/template-resolution.md` | Lists Voxel + Elementor templates with usage signals. |

## `elementor:` namespace

| Command | Status | Location | Rationale |
|---|---|---|---|
| `elementor:action-drift` | `defer` | n/a | EF action-type registry drift gate — verifies EF covers every Voxel advanced-list action; exits non-zero on un-accounted drift. Surface if an action-row audit recipe needs the registry-drift signal. |
| `elementor:anchors` | `surfaced` | `references/core/command-surface.md`; pre-input for `elementor:set-cssid` / `set-value` repair | Read-only anchor-link orphan finder. Its JSON output is the canonical input for the two batch-repair verbs below. |
| `elementor:animations` | `defer` | n/a | List/remove all Elementor animations and motion effects. Niche; revisit when animation cleanup becomes a recurring task. |
| `elementor:codegen` | `surfaced` | `rules.md` rule 1 (unconditional regen at start of every build); `page-planning.md` entry criteria; `references/core/command-surface.md` §Schema | Generates the committed SSOT widget-schemas artifact (`cli/src/generated/widget-schemas.json`) from EF widget-registration source. Run unconditionally at the start of every run. |
| `elementor:codegen:tokens` | `defer` | n/a | Sibling codegen for design-token SSOT. Build-time tooling; surface if token-edit recipes need a deterministic regen step. |
| `elementor:codegen:verify` | `surfaced` | `references/core/rules.md` rule 1 (live-site drift gate, companion to `elementor:codegen --check`) | CI-gated drift check between `cli/src/generated/widget-schemas.json` and live registration. Cited next to rule 1 so agents know how the SSOT stays current. |
| `elementor:clean-test-pages` | `out-of-scope` | n/a | Deletes orphaned `elementor-widget-test` pages (`ewt-*` slugs). Test-fixture hygiene, not Voxel build/audit/reference work. |
| `elementor:controls:check` | `defer` | n/a | Per-control schema validation. Niche debugging tool; revisit when an audit recipe needs it. |
| `elementor:create` | `out-of-scope` | n/a | Creates blank Elementor template — handled by `voxel:create` (CPT lifecycle) or directly by the user when scaffolding a single template outside CPT context. |
| `elementor:diagnose` | `defer` | n/a | Runs Elementor Framework diagnostics for a site or one post. Useful for environment/runtime triage, but not yet owned by a specific Voxel workflow; surface it when a recurring diagnosis route defines its evidence and handoff contract. |
| `elementor:docs:gen` | `out-of-scope` | n/a | Regenerates EF widget docs. Documentation tooling, not build/audit. |
| `elementor:dx` | `defer` | n/a | EF DX cleanup suite (comment pruning, LLM context-map, OCD quality gate). Build-time developer hygiene on the EF plugin source, not a Voxel build/audit/reference recipe step; revisit if a quality-gate recipe needs it. |
| `elementor:dump` | `surfaced` | `voxel-widget-builder` (rule 2 — golden snapshot), `voxel-schema-detective` (`ts-*` fallback), `examples/README.md` (refresh workflow), `command-surface.md` §EMCP vs headless wpdev reads | Headless/raw DB instance JSON for widgets and corpus sweeps. For one live editor element, prefer EMCP `get-element-settings`. |
| `elementor:export` | `surfaced` | `command-surface.md` §EMCP vs headless wpdev reads; `workflows/migrate.md` migration round-trip | Headless whole-page raw `_elementor_data` export for controlled migration files. For editor-equivalent live export, prefer EMCP `export-page`. |
| `elementor:fetch-flags` | `defer` | n/a | Pulls EF experiment / feature flags. Niche; surface if a build recipe needs to gate on a flag. |
| `elementor:fetch-phosphor` | `defer` | n/a | Regenerates the EF Phosphor icon CSS/JSON/font artifacts from upstream. Developer asset maintenance, not a per-site Voxel build/audit step; surface in the icon workflow only if Phosphor-specific authoring or drift repair becomes recurring. |
| `elementor:import` | `surfaced` | `workflows/build.md` Phase 5, `references/core/command-surface.md` | Writes `_elementor_data` from a JSON file. The single write path. |
| `elementor:icon-search` | `surfaced` | `references/icons/material-symbols/lookup-and-repair.md` | Ranked EF Material Symbols lookup over the generated `search.tsv` enriched with Google Symbols metadata. Use before choosing a new icon value. |
| `elementor:icons` | `surfaced` | `references/icons/material-symbols/lookup-and-repair.md`; `references/icons/material-symbols/README.md` | DB scanner for all stored Elementor icon values across pages and templates; verifies wrong-icon repairs and audits existing icon-library usage. |
| `elementor:data:converge` | `defer` | n/a | Inventories and converges live `_elementor_data` storage (dry-run by default). Storage-level convergence sits outside the build/audit routes; surface it when a site shows mixed/legacy `_elementor_data` storage shapes rather than per-post prop drift. |
| `elementor:diagnose` | `defer` | n/a | Runs EF diagnostics for a site or one post. Overlaps `elementor:lint` (per-post schema gate) and `elementor:codegen:verify` (runtime-vs-SSOT); reach for it when the failure is EF-runtime-wide rather than a single post's props. |
| `elementor:lint` | `surfaced` | `voxel-page-auditor` `[G]`-tier, `workflows/build.md` Phase 4 | Validates against the live schema — catches `unknown-prop` / `type-mismatch`. |
| `elementor:fix-row-tags` | `surface-pending` | n/a | Restores missing content-block row tags from a database backup. Operational repair command; document a workflow only when the defect class recurs outside its owning regression tests. |
| `elementor:loop-filter` | `defer` | n/a | Loop-filter inspection / debugging. Niche; revisit when loop-filter audit recipes recur. |
| `elementor:mutate` | `surfaced` | `workflows/build.md` §Choosing the mutation tool; `commands/fix-known.md` | Canonical single-post scripted-repair wrapper — runs a PHP mutator on `_elementor_data`, then atomically lints → regenerates per-post CSS → purges caches → optionally HTTP-fetches the URL. The single-post mutation path; prefer over raw `wp eval-file`. |
| `elementor:normalize` | `defer` | n/a | Normalizes _elementor_data shape (whitespace, key order). Surface if a fix-loop recipe needs a deterministic normalizer step before diff. |
| `elementor:rename` | `defer` | n/a | Bulk Navigator-title cleanup. Cosmetic; revisit when batch-rename becomes a recurring task. |
| `elementor:schema` | `surfaced` | rule 1 of `rules.md`, `voxel-widget-builder`, `voxel-schema-detective` | EF V4 atomic widget schema — the canonical prop / `$$type` source. |
| `elementor:schema:check` | `defer` | n/a | Schema drift verification companion to `codegen:verify`. Surface alongside the codegen pair when the SSOT gate is wired in. |
| `elementor:semantic` | `surfaced` | `voxel-page-auditor` `[G]`-tier (per-post) | Semantic HTML structure analysis — single-post audit input. |
| `elementor:set-cssid` | `surfaced` | `references/core/command-surface.md` §Anchor repair; consumed by `voxel-elementor-fixer` Pass 2 when audit finds anchor-target gaps from `elementor:anchors` | Writes a node's `_cssid` (single or `--map` batch) to repair broken in-page anchors. The repair path for `elementor:anchors` output. |
| `elementor:set-value` | `surfaced` | `references/core/command-surface.md` §Anchor repair; consumed by `voxel-elementor-fixer` Pass 2 to repoint broken links / URLs / strings | Scalar-at-path writer — repoints a link or fixes a URL/string at any node-settings key path. Batched via `--map`. |
| `elementor:structure` | `surfaced` | `voxel-page-auditor` `[G]`-tier | Site-wide `<main>`/`<header>`/`<section>` semantic-compliance audit (filter by `--type`). |
| `elementor:styles` | `surfaced` | `voxel-elementor-fixer` Pass 2 (when audit flags style drift); `references/core/command-surface.md` | Audits + fixes Elementor style inconsistencies. Now ships `--fix`, `--sync-voxel`, `--only buttons,shadowed,voxel,units,colors,typography,headings,bloat`. Pair `--dry` with `--fix` for preview. |
| `elementor:templates` | `surfaced` | `voxel-schema-detective` | Lists Elementor saved templates with usage counts. Companion to `voxel:templates`. |
| `elementor:tree` | `surfaced` | `voxel-page-auditor` `[G]`-tier, `workflows/build.md`, `command-surface.md` §EMCP vs headless wpdev reads | Headless/raw DB widget-tree summary — audit structural input. For live editor-equivalent single-page structure, prefer EMCP `get-page-structure`. |
| `elementor:validate` | `defer` | n/a | Offline Ajv validation of `_elementor_data` against the schema SSOT (`--all-sites` validates the whole corpus). The skill uses the live `elementor:lint` as the canonical per-post gate (Phase 4 / `[G]`-tier); surface `elementor:validate` for offline or corpus-wide sweeps (CI-style) when no live site is required. |
| `elementor:verify:idle-churn` | `surfaced` | `workflows/audit.md` (runtime defect class), companion to `elementor:verify:loop-render` | Browser-verifies that a page settles when idle, failing when a widget runtime keeps mutating its own DOM (runaway ResizeObserver/MutationObserver loops). Catches the defect class that looks fine in a screenshot and in stored data, because it exists only in motion. |
| `elementor:verify:loop-filter` | `surfaced` | `workflows/archive-search-pages.md` filter step; companion to `elementor:verify:loop-render` | Browser-verifies the EF loop-filter AUTHOR path end to end: authors a filter the way the editor does, then proves the loop is empty before cron and correctly narrowed after. Every cheaper check stops at the PHP boundary — calling the indexer directly proves the indexer works, not that saving a filter registers a predicate, schedules the cold-start backfill, and ends with the right posts. Refuses a predicate that would not split the corpus, so a non-discriminating run cannot pass green. |
| `elementor:verify:loop-render` | `surfaced` | `workflows/archive-search-pages.md` render-proof step; companion to `voxel:archives` | Browser-verifies a rendered EF query-backed loop: card count, computed grid tracks, pager page size, column offsets, dtag leakage, console/page errors. This is the loop equivalent of a smoke test — it proves the built loop actually renders. |
| `elementor:widgets` | `surfaced` | `voxel-page-auditor` `[G]`-tier (rare-widget findings), `voxel-schema-detective` (`widget=usage`) | Widget usage across all pages. `--migrate` flag surfaces legacy-widget pages — directly feeds Pass 2 migration fork. |

## `elementor:ef:*` namespace (EF plugin CLI surfaces)

| Command | Status | Location | Rationale |
|---|---|---|---|
| `elementor:ef:migrate` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 0 §EF data-migration health check | EF data migrator — `status` shows pending steps, `run` executes, `release-lock` clears stuck locks. Mission-critical before any Phase 5 `elementor:import` lands on a stale EF install. |
| `elementor:ef:settings` | `defer` | n/a | EF settings read/write. Site-config plumbing, not build/audit territory. Surface only when a build recipe needs to flip a setting deterministically. |
| `elementor:ef:smtp` | `out-of-scope` | n/a | SMTP test / DB-password clear. Operator territory (form delivery wiring), not build/audit. |
| `elementor:ef:submissions` | `defer` | n/a | Lists EF form submissions with decoded fields. Useful for verifying a built `ef-form` widget after deploy; revisit if form-build flows become recurring. |
| `rebuild --only tokens` (was `elementor:ef:tokens sync`) | `surfaced` | `workflows/build.md` Phase 6 (after token/kit-color edits) + `voxel-elementor-fixer` Pass 2 | Design-token re-sync — pushes EF tokens → Elementor kit + clears CSS + purges cache. Closes the loop after token mutations. Token reset is no longer a CLI verb: edit/remove the override in the EF Design Tokens admin page (or `ef_tokens` option), then re-run `rebuild --only tokens`. |
| `elementor:ef:tool` | `defer` | n/a | Tools-tab tool dispatcher (`list` / `run <slug>`). Catalog of one-off ops scripts in `plugins/custom/elementor-framework/migrations/tools/`; surface specific tools individually if a build/audit flow needs them. |

## `elementor:migrate:*` namespace (schema-churn fixers)

| Command | Status | Location | Rationale |
|---|---|---|---|
| `elementor:migrate:containers` | `surfaced` | `references/core/command-surface.md` §Fix-loop mutations; `workflows/migrate.md` Phase 1 | Converts legacy `<container>` nodes to clean `ef-wrapper` (tag from `html_tag`; `cols=N×1fr` only when horizontal). Drops all other styling. |
| `elementor:migrate:loop-index` | `surfaced` | `references/core/command-surface.md` §Fix-loop mutations; `voxel-elementor-fixer` Pass 2 fork point | Rewrites `@<group>(<path>.index)` (broken) → `@<group>(<path>.title).loop_index()` (Voxel canonical). Run on every CPT page that uses loop iteration indexes. |
| `elementor:migrate:main` | `surfaced` | `references/core/command-surface.md` §Fix-loop mutations; `workflows/migrate.md` Phase 1 | Converts every root `<main>` container (`html_tag=main`) into a clean `ef-wrapper(tag=main)`, preserving children. Structural Phase 1 of migration. |
| `elementor:migrate:voxel-feeds` | `surface-pending` | n/a | Converts Voxel `ts-post-feed` instances into EF wrapper template-mode feeds. Keep pending until migrate/build route defines preservation, rollback, and browser proof gates for this broad template mutation. |

## `elementor:strip:*` namespace (cleanup mutations)

| Command | Status | Location | Rationale |
|---|---|---|---|
| `elementor:strip:styles` | `surfaced` | `voxel-elementor-fixer` Pass 2 | Removes per-node style overrides (local + globals), keeping settings (variants, etc.) intact; Pass 2 mutation when audit finds redundant styles. |
| `elementor:strip:wrappers` | `surfaced` | `references/core/command-surface.md`, `voxel-elementor-fixer` Pass 2, success-criteria checklist | Removes unnecessary wrapper containers around `ef-*` widgets (any depth, including root); covers the single-`ef-card` root-wrapper case. |

## `elementor:reset:*` namespace

| Command | Status | Location | Rationale |
|---|---|---|---|
| `elementor:reset:button-variants` | `defer` | n/a | Resets button-variant assignments across `_elementor_data`. Surface if a fix-loop recipe needs deterministic button-variant normalization beyond what `elementor:styles` covers. |

## `elementor:revisions:*` namespace

| Command | Status | Location | Rationale |
|---|---|---|---|
| `elementor:revisions:prune` | `surfaced` | rule 6 of `rules.md`, all fix-mode dispatches | Mandatory pre-mutation snapshot+delete. |
| `elementor:revisions:restore` | `surfaced` | `voxel-elementor-fixer` rollback path | Restores from a `revisions:prune` snapshot when a fix Pass needs to be undone. |

## Current encoding repair command (retired `elementor:fix:*` namespace)

| Command | Status | Location | Rationale |
|---|---|---|---|
| `db:encoding` | `surfaced` | `voxel-elementor-fixer` Pass 2 (when audit finds unicode corruption); `voxel-page-auditor` detects via `elementor:dump` regex grep | Site-wide mojibake fix (the `elementor:fix:unicode` verb was retired in `c939f922f`; `db:encoding` replaces it and repairs at the DB layer, so it covers post meta beyond `_elementor_data`) (`u00e9` → `é`). Workspace has documented `u00e9`-leakage history. |

## `audit*` namespace (workspace-level)

| Command | Status | Location | Rationale |
|---|---|---|---|
| `audit` | `surfaced` | `voxel-page-auditor` (optional broader-context pass when scope ≠ single post) | Full site audit with scopes (technical / a11y / wordpress / db-content / elementor / density / performance). |
| `audit:ai` | `defer` | n/a | AI-content audit. Different mission (content QA, not build hygiene); routes through scrum:audit campaigns instead. |
| `audit:density` | `defer` | n/a | Page-density audit. Subset of `audit --scope density`; revisit if standalone usage justifies. |

## `schema:*` namespace (lean-seo)

| Command | Status | Location | Rationale |
|---|---|---|---|
| `schema` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 4 (as the way to see what the namespace offers) | Namespace parent: prints the schema subcommands. Runnable in its own right, which is why it needs a row — a namespace with no entry reads as a typo when an agent meets it in output. |
| `schema:compile` | `defer` | n/a | Schema compilation. Used inside `schema:set`/`validate`; not directly invoked by the plugin. |
| `schema:delete` | `out-of-scope` | n/a | Destructive operational. CPT lifecycle Phase 4 only sets/validates; deletion is operator territory. |
| `schema:export` | `defer` | n/a | Cross-site schema migration. Same posture as `voxel:export`. |
| `schema:get` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 4 | Reads the existing schema mapping for a CPT target. |
| `schema:import` | `defer` | n/a | Cross-site schema migration. Pair with `schema:export`. |
| `schema:set` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 4 | Writes a new schema config for a CPT target (JSON blob). |
| `schema:validate` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 4 | Static validation against JSON-LD shape. |
| `schema:validate-live` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 4 (gating step before Phase 5) | Live validation against rendered pages — Phase 4's verification step. |
| `schema:rich-results` | `surfaced` | `workflows/cpt-lifecycle.md` Phase 4 (gating step before Phase 5) | Validates emitted JSON-LD against Google Rich Results rules and reports dangling `@id` references — catches the `@ref: true` mis-binding Phase 4 warns about, which `schema:validate-live` does not detect. |

## Current rebuild and smoke commands (retired `cache:*` / `render:*` naming)

| Command | Status | Location | Rationale |
|---|---|---|---|
| `rebuild --only purge` (was `purge`) | `surfaced` | `references/core/command-surface.md`, `workflows/build.md` Phase 6, success-criteria checklist | Flushes all caches (object cache, transients, Elementor CSS, page cache, Voxel) post-write. Standalone `purge` was folded into `wpdev rebuild`. |
| `smoke` | `defer` | n/a | Deterministic `_elementor_data` fingerprint diff harness. Useful for fix-loop verification but currently superseded by browser-screenshot rule (rule 7). Revisit if fingerprint diffs prove faster. |

## Other

| Command | Status | Location | Rationale |
|---|---|---|---|
| `headings` | `defer` | n/a | Live-page heading hierarchy. Subset of `elementor:semantic --headings`; revisit if standalone usage justifies. |
| `perf` | `surfaced` | `voxel-page-auditor` diagnostic findings (not a mission verb but cross-referenced) | Site performance metrics. Referenced by audit findings but not a build command. |
| `quality` | `out-of-scope` | n/a | PHP quality stack on `plugins/custom/`. Wrong layer — quality runs against PHP plugins, not Voxel content. |

## Out-of-scope namespaces (entire surface)

These wpdev namespaces are out of the voxel-builder mission entirely — listed once here so future drift checks don't re-evaluate row by row:

- **Site lifecycle / scaffolding**: `init`, `work`, `new`, `destroy`, `site-rename`, `list`, `link`, `unlink`, `links`, `update`, `open`, `scaffold`, `doctor`, `config`, `mcp`, `plugins`, `themes`, `test`.
- **Database operations** (`db:*`): `db:encoding`, `db:hierarchy`, `db:export`, `db:import`, `db:reset` — DBA territory.
- **Debug** (`debug:*`): `debug:on`, `debug:off`, `debug:tail` — runtime troubleshooting, not build/audit.
- **Backup** (`backup:*`): `backup:create`, `backup:delete`, `backup:list`, `backup:remote`, `backup:restore` — pre-deploy safety, not voxel-builder.
- **Core** (`core:*`): `core:update`, `core:version` — WP core management.
- **Remote** (`remote:*`): `remote:add`, `remote:edit`, `remote:list`, `remote:remove`, `remote:sql`, `remote:ssh`, `remote:wp`, `remote:tunnel`, `remote:sync:push`, `remote:sync:pull` — deploy / SSH territory.
- **Uploads / Media / Settings / Post-import**: `uploads:migrate`, `media:prune`, `media:unused`, `settings:dump`, `settings:pull`, `post-import` — operational tooling. WebP backfill lives in `media:prune` (`--no-webp` opts out); there is no `valet:*` namespace, and Valet is not installed on this Linux host.
- **Scrum** (`scrum:*`): no longer exists. The namespace was removed from the CLI; `scrum` appears nowhere in `cli/src`. Do not reference it.

## Coverage summary (post audit)

- `voxel:` namespace: **18 surfaced** (+ `rebuild --only reindex`), 1 surface-pending (heading-curator), 5 deferred/out-of-scope (admin-menu, delete, export, openapi, repair-options).
- `elementor:` namespace: **18 surfaced** (incl. `codegen`, `codegen:verify`, `export` for migration round-trips), 8 deferred / 2 out-of-scope (action-drift, animations, controls:check, loop-filter, rename, fetch-flags, codegen:tokens, schema:check deferred; create, docs:gen out-of-scope), 0 surface-pending.
- `elementor:ef:*`: **2 surfaced** (`ef:migrate` → cpt-lifecycle Phase 0; `rebuild --only tokens` → elementor-build Phase 6 + fixer Pass 2), 3 deferred / 1 out-of-scope.
- `elementor:migrate:*`: **3 surfaced** (`containers`, `loop-index`, `main`) + **1 surface-pending** (`voxel-feeds`).
- `elementor:strip:*`: **2 surfaced** (`styles`, `wrappers`).
- `elementor:reset:*`: 1 deferred (`button-variants`).
- `elementor:revisions:*`: **2 surfaced** (both).
- Encoding repair: **1 surfaced** (`db:encoding`; retired `elementor:fix:unicode` is historical context only).
- `audit*`: 1 surfaced, 2 deferred.
- `schema:*`: 4 surfaced, 4 deferred/out-of-scope.
- `rebuild --only *` / `smoke`: 1 surfaced, 1 deferred.
- Other: 0 surfaced (`headings` deferred, `quality` out-of-scope, `perf` surfaced in this skill via `voxel-page-auditor` diagnostic findings — not a mission-verb but cross-referenced).

**Total surfaced: 53** of ~60 plugin-relevant commands, with 1 explicit `surface-pending` row (`voxel:heading-curator`) carrying a wiring plan. The per-namespace counts above are a human convenience; the lint gate (see top of file) is the actual completeness guarantee.

**Verbs verified absent from the CLI (do NOT reference):**

- `elementor:strip:card-wrappers` — not a verb. Use `elementor:strip:wrappers` (it handles the single-`ef-card` root-wrapper case among others).
- `elementor:migrate:buttons` — not a verb. Button-shape migration is handled inside the EF data-migrator (`elementor:ef:migrate run`).
- `elementor:migrate:icon-heading` — not a verb. The retired `ef-icon-heading` widget migration is handled inside the EF data-migrator (`elementor:ef:migrate run`).
- `elementor:rollback` — not a verb. Restore via `elementor:revisions:restore`.
- `elementor:migrate:loop` — not a verb (the bare shorthand). The loop-index migrator is `elementor:migrate:loop-index`.
- `voxel:fields-validate` — not a verb. Re-read the registered field list with `voxel:fields`.
