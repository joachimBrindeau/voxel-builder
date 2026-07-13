# Voxel CPT Lifecycle
Register a new Voxel custom post type with full lean-seo integration: fields, permalinks, schema, sitemap, search filters, index table, and Elementor template scaffolding.

## Entry criteria

1. User request names a concrete CPT purpose, audience, and minimum record shape.
2. Target site runs Voxel, lean-seo, and elementor-framework.
3. Blueprint path is writable and committed source of truth can be updated before runtime config.
4. Required slugs/permalink defaults are known or explicitly chosen before creating posts.

## Exit criteria

1. Blueprint JSON is updated and imported without manual dashboard drift.
2. CPT fields, filters, search, schema, sitemap, and index table pass their workflow gates.
3. Representative post/template renders and passes Elementor lint plus browser verification.
4. Rollback/export artifacts exist for any destructive or schema-changing step.

## Essential principles

1. **Order matters.** Permalink defaults must be configured BEFORE creating any CPT posts. The auto-parent `wp_insert_post` hook only fires if the default already exists.
2. **Blueprint is the source of truth.** All Voxel config (fields, filters, search, options) lives in a blueprint JSON at `plugins/custom/voxel-addon/modules/Templates/blueprints/<key>/post_types.json`. Never configure fields manually — always create/update the blueprint.
3. **`has_archive` must be disabled.** Voxel defaults to `has_archive: true`, which creates a WP rewrite rule conflicting with lean-seo's parent-page permalink model. Always set `settings.options.archive.has_archive: "disabled"` in the blueprint.
4. **All 4 templates must exist.** `wpdev voxel:create` scaffolds single, card, archive, and form templates. The card (preview) template is required for `ts-post-feed` to render items.
5. **Index table before feeds.** Voxel feeds query an index table, not `wp_posts`. Create the table and index existing posts before testing feeds.

## When to use this lifecycle

- Creating a new Voxel CPT on any site using lean-seo's parent-page permalink model
- Adding a content type that needs individual pages, feed listings, and schema markup
- Extending the site with a new post type (glossaire, service, job listing, etc.)
- Setting up Voxel search filters, sort ordering, or index tables for an existing CPT

## When NOT to use

- Modifying fields/config on an existing CPT — use Voxel admin UI or edit the blueprint directly (Phase 2 only)
- Creating a CPT on a site without lean-seo — use Voxel admin UI only
- Taxonomy creation — use the taxonomy blueprint system instead

## Decision fork: public-content vs transactional CPT

**Before Phase 1**, decide which recipe applies. The 7-phase walkthrough below is the **public-content default** (glossaire, services, profile, org — content meant for SEO discovery, indexed, sitemap-included, with explicit Lean SEO Schema Builder JSON-LD).

A **transactional / private CPT** (RFQ board, leads, support tickets, inquiries, internal workflow items) inverts most of Phase 4's assumptions: singles should be `noindex`, the CPT must be excluded from the sitemap, no per-post `schema:set` Article JSON-LD, and contact happens via in-platform DMs rather than rendered email addresses.

| Dimension | Public-content (default) | Transactional / private |
|---|---|---|
| Examples | glossaire, services, profile, org | RFQ board, leads, support tickets, inquiries |
| `publicly_queryable` | enabled | enabled (board renders) |
| Singles in sitemap | yes (Phase 4) | **excluded** via `lean_seo_sitemap_exclude` |
| Singles indexed | yes | **noindex** |
| Per-post schema (`schema:set`) | yes | skip |
| Parent page schema | optional | CollectionPage (optional) |
| Contact channel | publicly rendered | `messages.enabled: true` (in-platform DMs) |
| Workflow fields (`status`, `assigned-to`) | n/a | admin-only via `visibility_rules` (see [`voxel-field-visibility.md`](../references/voxel/voxel-field-visibility.md)) |
| Submission status default | `publish` | `pending` (moderated) |
| Anonymity switcher | n/a | optional buyer-anonymity field |
| Phase 4 work | full (schema + sitemap + markdown) | minimal — sitemap-exclude only |

If the CPT is transactional, read `references/voxel/transactional-cpt-recipe.md`
before Phase 2, then apply its deltas through the same lifecycle. Public-content CPTs use
the base phases unchanged.

## Phase 0 — Prerequisites

**Entry:** A target site has been chosen and the lifecycle is about to run.

1. Verify required/optional plugin activation and surface activation side effects.
2. Check EF data migrations and resolve any stuck lock before template writes.
3. Detect conflicting permalink plugins and obtain agreement before deactivation.
4. Record the prerequisite verdict and any operator decisions.

The lifecycle assumes a specific plugin baseline. Each later phase calls into PHP that only exists when its owning plugin is active. Verify activation **before Phase 1** — activating mid-run is recoverable but the activation hooks may mutate live data on the site (option defaults, default-term inserts, table creates), so the operator must surface what's about to change and get explicit consent.

### Plugin activation gates

| Plugin | Required for | Failure mode if inactive |
|---|---|---|
| `voxel-addon` (workspace plugin) | Phase 2 `TemplateImporter::apply` — full namespace `VoxelAddon\Modules\Templates\TemplateImporter` (see `plugins/custom/voxel-addon/modules/Templates/TemplateImporter.php:5,11`) | `Class 'VoxelAddon\Modules\Templates\TemplateImporter' not found` fatal in `wp eval-file` |
| `lean-seo` (workspace plugin) | Phase 3 (`lean_seo_settings_set` — see `plugins/custom/lean-seo/includes/settings-store.php:143`), Phase 4 (`schema:*` CLI + `lean_seo_schema_graph` / `lean_seo_sitemap_high_priority_types` / `lean_seo_markdown_field_maps` filters) | `Call to undefined function lean_seo_settings_set()` (Phase 3); `schema:*` commands report no targets (Phase 4) |
| `essential-addons-for-voxel` (third-party, optional) | `ea4v_only_show_field_<type>` form-field whitelist on `ts-create-post` widgets — narrows the buyer-facing form to a subset of blueprint fields. Alternative when this skill is absent: native Voxel `visibility_rules` in `references/voxel/voxel-field-visibility.md`. | Whitelist setting persists in widget JSON but is never consumed — every blueprint field renders in the buyer form |

### One-liner gate (run before Phase 1)

```bash
wpdev wp <site> plugin status voxel-addon lean-seo --format=csv         # confirm both report active
wpdev wp <site> plugin status essential-addons-for-voxel --format=csv   # optional — informs Phase 6 form-field strategy
```

If anything is inactive, surface to the user, then:

```bash
wpdev wp <site> plugin activate voxel-addon lean-seo
```

### EF data-migration health check (run before any Phase 5 `elementor:import`)

A stale EF install — `_elementor_data` written against an older EF schema than the plugin at HEAD — silently renders broken (props the current renderer no longer reads, envelopes the migrator hasn't upgraded). Confirm no migration steps are pending before the lifecycle writes template data:

```bash
wpdev elementor:ef:migrate <site> status          # show pending EF data-migration steps + a stuck-lock indicator
wpdev elementor:ef:migrate <site> run -y           # execute pending steps (run is default); --from <N> / --force to replay
wpdev elementor:ef:migrate <site> release-lock     # only if status reports a stuck lock
```

`status` non-empty (pending steps) is a halt: run them (with operator consent — the migrator mutates `_elementor_data` across the site) before Phase 5, or the imported template lands on a drifted EF baseline. Mirrors the rule-1 `elementor:codegen` SSOT freshness gate, but for the live site's stored data rather than the offline schema artifact.

### Permalink-routing prerequisite

`lean-seo` owns CPT permalink routing across the workspace — its `permalink_default` model is authoritative for the rewrite layer. No third-party permalink plugin (e.g. the now-removed Permalink Manager Pro) should be installed. If any such plugin is unexpectedly present it will hijack rewrites and singles will 404, so treat its presence as drift to remove, not a supported branch:

```bash
wpdev wp <site> plugin list --status=active --field=name | grep -i permalink || echo "no third-party permalink plugin (expected)"
```

If a third-party permalink plugin shows up, surface it to the user and get agreement to deactivate it before Phase 3 — lean-seo cannot route singles while it is active.

### Side-effect note

Activating workspace plugins is not a no-op: `voxel-addon` registers blueprint sources on activation, `lean-seo` migrates option keys and seeds defaults. On a long-lived production site these hooks may write to options/tables in ways the operator did not request. Activate prerequisites **explicitly and with consent**, not silently mid-lifecycle.

**Exit:** `voxel-addon` and `lean-seo` confirmed active; no third-party permalink plugin present (or its removal agreed with the user); operator has agreed to any plugin-activation side effects.

## Phase 1 — CPT Registration

**Entry:** Phase 0 prerequisites met. Site exists, key is valid (lowercase alphanumeric + underscores, max 20 chars), CPT doesn't already exist.

1. Run `wpdev voxel:create <site> <key> --label <Label>`
2. Record the 4 returned template IDs (single, card, archive, form)

**Exit:** CPT exists in `voxel:post_types`, 4 blank Elementor template pages created.

## Phase 2 — Blueprint Creation + Apply

**Entry:** Phase 1 complete. Template IDs recorded.

1. Ask the user what fields the CPT needs (or accept a field list if provided)
2. Create blueprint JSON at `plugins/custom/voxel-addon/modules/Templates/blueprints/<key>/post_types.json`
   - Include fields, settings.options (`has_archive: "disabled"`, `hierarchical: "enabled"`, `publicly_queryable: "enabled"`), settings.permalinks (custom, slug, with_front: false)
   - Include search.filters (at minimum: keywords filter) and search.order (at minimum: alphabetical + latest)
   - Follow the blueprint schema in [`blueprint-format.md`](../references/core/blueprint-format.md)
   - Put field descriptions, placeholders, and limits in blueprint source before apply. For later or bulk metadata convergence (including repeater subfields), hand off to [`field-metadata.md`](field-metadata.md) with site, CPT key, blueprint path/source-owner status, and live inventory. Blueprint-managed CPTs update source first; runtime-only legacy CPTs record missing source ownership as debt. Exact writers belong to [`command-surface.md`](../references/core/command-surface.md).
3. Register in `modules/Templates/Templates.php` → `Templates::get_templates()`
4. Apply: `$importer = new \VoxelAddon\Modules\Templates\TemplateImporter(); $importer->apply('<key>', '<key>', 'cpt');`
5. **Reindex + recreate index table (mandatory after every blueprint apply).** Run `wpdev rebuild <site> --only reindex --recreate` and confirm exit 0. A plain reindex inserts post rows into the index table *that already exists* — it does **not** regenerate the table's column set from the new filter graph. When the blueprint adds new search-filter sources (keywords filter, taxonomy filter, date fields, etc.), the column list must be rebuilt by dropping and re-creating the table — which is exactly what `--recreate` now does inline before reindexing. Without it, the next `wp_insert_post` will explode with `Unknown column '_keywords' in 'field list'` (or similar). On a freshly-applied empty CPT, a plain reindex will happily report "0 posts indexed" while leaving the table stale or absent — so `--recreate` is non-negotiable after a blueprint change. (Reindex now covers all Voxel-managed CPTs in one pass; the blueprint apply writes the schema, `--recreate` rebuilds each index table's columns, and the reindex repopulates the rows that drive search filters and field ordering.) Skipping leaves the admin looking correct while production breaks silently.

   To confirm the new sources landed, recreate the table manually and dump the resulting column list with this `wp eval-file` snippet:

   ```bash
   cat > /tmp/recreate-index.php <<'PHP'
   <?php
   $key = '<key>'; // <-- edit
   $pt = \Voxel\Post_Type::get( $key );
   if ( ! $pt ) { fwrite( STDERR, "CPT not found: {$key}\n" ); exit( 1 ); }
   $pt->index_table->recreate();
   global $wpdb;
   $table = $pt->index_table->get_escaped_name();
   $cols  = $wpdb->get_col( "SHOW COLUMNS FROM `{$table}`" );
   echo "Recreated {$table} with " . count( $cols ) . " columns:\n";
   foreach ( $cols as $c ) { echo "  - {$c}\n"; }
   PHP
   wpdev wp <site> "eval-file /tmp/recreate-index.php --skip-plugins=voxel-addon"
   ```

   Confirm the printed columns include the base set (`id`, `post_id`, `post_status`, `priority`) **plus** one column per configured search-filter source (e.g., `_keywords` for the keywords filter). If a configured source is missing from the output, the blueprint's `search.filters` section didn't apply — go back to step 4 before continuing.
6. **Voxel cache clear (mandatory).** Run `wpdev voxel:cache <site> clear` so any cached blueprint copy is invalidated.
7. Verify fields with `wpdev voxel:fields <site> <key>`.
8. **Status check (mandatory before exit).** Run `wpdev voxel:status <site>` and confirm the CPT's index reports `OK`. A non-`OK` result means the blueprint didn't fully apply — halt and surface to the user rather than declaring Phase 2 done.

**Exit:** CPT has fields, filters, search config, and correct options. Blueprint committed. Reindex + table-recreate + cache + status all clean.

## Phase 3 — Parent Page + Permalinks

**Entry:** Phase 2 complete.

1. Find the front page ID: `wpdev wp <site> option get page_on_front`
2. Create parent page: `wpdev wp <site> post create --post_type=page --post_title='<Label>' --post_name=<key> --post_status=publish --post_parent=<front_page_id>`
3. Record the page ID
4. Set permalink default: `lean_seo_settings_set('permalink_default', '<key>', '<page_id>', 'page_select', '...')`
5. Flush rewrite rules: `wpdev wp <site> rewrite flush`
6. **Verify:** Create a test post, confirm URL resolves as `/<key>/<slug>/`, then delete test post
7. **Title/description templates:** set the CPT's `title_template` and `desc_template` via `lean_seo_settings_set`. **If the CPT's singles are definitions (glossary / dictionary / defined term), point `desc_template` at a length-bounded teaser field (e.g. `%hook%`, Voxel-capped 35-120 chars), NOT the answer block** — a 40-60 word answer block exceeds the 155-char SERP limit and truncates mid-sentence. See [`../references/voxel/seo-defined-terms.md`](../references/voxel/seo-defined-terms.md) §The two-surface rule.

**Exit:** Parent page exists, permalink default configured, URL resolution verified, title/description templates set.

### Unexpected permalink plugin drift

Permalink Manager Pro has been fully removed from the workspace. If Phase 0 surfaces any active third-party permalink plugin, stop before Phase 3 and remove/deactivate it with user consent. Do not add one-off per-CPT rewrite workarounds; they bypass the lean-seo permalink-default SSOT and make schema/live URL verification unreliable.

## Phase 4 — Schema, Sitemap, and Markdown Maps

**Entry:** Phase 3 complete. Parent page ID known.

The lean-seo schema system has both a CLI surface (`wpdev schema:*`) and a code-side admin/filter surface. Use the CLI for read / write / validation; reach for filters only when emitting site-specific nodes that cannot be expressed by Schema Builder.

Schema is config-only. Do not rely on or recreate hardcoded fallbacks for Organization, WebSite, WebPage, Article, FAQPage, DefinedTermSet, or BreadcrumbList. Every emitted node must come from the target config or an explicit developer filter.

1. **Read existing config:** `wpdev schema:get <site> <key> --json` → returns the current schema JSON-LD config for the CPT target, or empty if none exists. Show the user before writing.
2. **Compose new schema config:** Author the JSON-LD shape (e.g., `Article`, `LocalBusiness`, `DefinedTerm`, or an explicit `@graph` with `WebPage`, `BreadcrumbList`, and domain entity nodes).
   - **For a glossary / dictionary / defined-term CPT**, use the complete worked recipe in [`../references/voxel/seo-defined-terms.md`](../references/voxel/seo-defined-terms.md) — `WebPage` + `DefinedTerm` (`sameAs` via `@each`/`@map`, `termCode`/`alternateName` from an acronym field) + a site-level `DefinedTermSet`, and the hard rule to **never emit `FAQPage`** (deprecated by Google May 7 2026). Visible FAQ content is optional and on-page only: render it only for genuine term-specific follow-up questions, never as boilerplate. **The recipe is not just schema:** it also mandates a required 400-800 word `content` body per term (anti-thin-content), **flat URLs** (parent terms to the CPT landing page, category via taxonomy — never nest under a category post), lateral `siblings` links, and a named author. Ship a term only when its per-term completion checklist is fully green — a definition-only page is thin and risks a scaled-content penalty.
   - Use config sources such as `post:title`, `seo:desc`, `post:permalink`, `hierarchy:trail`, `hierarchy:ancestors`, and `hierarchy:children`.
   - Use `@id` convention: `@ref:self#<fragment>` (e.g., `@ref:self#definedterm`, `@ref:self#localbusiness`, `@ref:self#webpage`)
   - For graph targets, set fragments explicitly in list refs: `{"@each":"hierarchy:children","@ref":"service"}`. `@ref: true` uses the target's configured default fragment and can point to the wrong node when the target's first `@graph` node is `WebPage`.
   - Omit empty fields (graceful degradation)
   - Save to `/tmp/<key>-schema.json` so the CLI consumes it via `@filepath`.
3. **Write config:** `wpdev schema:set <site> <key> @/tmp/<key>-schema.json`. The command runs `schema:validate` automatically before persisting; pass `--force` only when overriding a known-acceptable validation warning.
4. **Static validation:** `wpdev schema:validate <site>` runs structural validation across all configured targets. Must return clean for all targets the CPT touches.
5. **Live validation (gating step):** `wpdev schema:validate-live <site>` fetches a real rendered page for each configured target and validates the emitted JSON-LD against the schema config. **Phase 4 does not exit until this returns clean.** A live-validation failure means the rendered page is dropping or malforming a required field — diagnose before proceeding to Phase 5.
6. **Code-side overlays (when needed):**
   - **Site-specific parent page schema:** Prefer an explicit page target config. If a filter is required, retrieve parent page ID via `lean_seo_settings_map('permalink_default')['<key>']` — NOT `get_page_by_path()`. Memoize with `static $cache`.
   - **No fallback cleanup filters:** Do not add filters that remove auto-emitted FAQ/Breadcrumb/etc.; those nodes should not be auto-emitted.
7. **Sitemap priority:** Add to `lean_seo_sitemap_high_priority_types` filter.
8. **Markdown field maps:** Add entry to `lean_seo_markdown_field_maps` filter with text fields and repeaters.

**Exit:** Schema renders on CPT pages — `wpdev schema:validate-live <site>` returns clean for the CPT target. Sitemap includes CPT. Markdown field map registered.

## Phase 5 — Index Table + Smart Internal Linking

**Entry:** Phase 4 complete.

> **Warning — `create()` is not idempotent.** `\Voxel\Post_Types\Index_Table::create()` runs `CREATE TABLE IF NOT EXISTS` — if a stale table from a prior blueprint shape already exists, `create()` is a no-op and the column set is **never refreshed**. This is the root cause of a recurring failure: a `wp_insert_post` later crashed with `Unknown column '_keywords' in 'field list'` because Phase 2 indexed against a table whose schema predated the keywords filter. Always use `recreate()` (drops + creates) so re-running Phase 5 after blueprint edits is safe.
>
> **Also:** `Index_Table` has no `delete()` method. The destructive verbs are `drop()` (table only) and `recreate()` (drop + create). Calling `->delete()` will fatal with `Call to undefined method`.

1. Create (or recreate) the Voxel index table:
   ```php
   $pt = \Voxel\Post_Type::get('<key>');
   $pt->index_table->recreate();   // drop if exists, then create — safe to re-run
   ```
2. Verify the column set includes every configured search-filter source:
   ```bash
   wpdev wp <site> "db query 'SHOW COLUMNS FROM wp_voxel_index_<key>'"
   ```
   Confirm `_keywords` is present whenever the blueprint declares a keywords filter, and that each field-filter source has its matching column.
3. Index any existing posts (`\Voxel\Post::force_get($id)->index()` per post)
4. Verify Smart Internal Linking includes the CPT (default "Any Type" settings include all public CPTs — just confirm CPT key is not in `silm_excluded_post_types`)

**Exit:** Index table exists (`wp_voxel_index_<key>`) with the full column set, posts indexed, Smart Internal Linking verified.

## Phase 6 — Elementor Templates

**Entry:** Phase 5 complete.

Templates are built in the Elementor editor. Provide the user with:

1. **Template URLs** for each of the 4 templates (from Phase 1 IDs).
2. **Preview cards** — for the `card` role, follow `references/ef/card-scaffolding.md`.
   `wpdev voxel:cards <site> --type <key>` produces small, medium, large, and link
   `ef-card` widgets, registers all four in `custom_templates.card[]`, and the generated
   large template must then be assigned as the base/main `templates.card`. A replacement
   is complete only after delete/export discipline, assignment read-back, registry audit,
   and four-card lint.
3. **For single / archive widget JSON**: run the page-planning sub-pipeline first ([`page-planning.md`](page-planning.md) §2a–§2g — Field Inventory → SSOT Read → Archetype Selection → Section Blueprints → adversarial review → reconciliation → computed §2g gate), then hand off to the [Elementor build pipeline](build.md) for schema-driven, parallel-subagent construction. Both steps are mandatory per [`rules.md`](../references/core/rules.md) rule 8 — never hand-write widget JSON from memory and never skip the Plan Document.
4. **Remind** the user that programmatically-written templates need an Elementor editor save to generate CSS/JS.

**Exit:** User informed of template URLs. Preview cards scaffolded if applicable. For non-trivial single/archive builds, a gated Plan Document (§2g green — auto or operator-`APPROVED`) exists at `/tmp/plan-<post_id>.md` before any widget fan-out begins.
## Phase 7 — Verification
**Entry:** Phase 6 complete.

1. Create a test post with sample data in all fields
2. Verify:
   - URL resolves: `/<key>/<slug>/`
   - Breadcrumbs: Home → Parent → Post
   - Schema: `curl -sL <url> | grep ld+json` — correct `@type`
   - Sitemap: CPT appears in XML sitemap
   - Parent page: renders at `/<key>/`
3. **Visual smoke-test** the new CPT's templates (single + card-in-feed) using [`build.md`](build.md) Phase 6: batch representative URL leaves, keep unique browser sessions per URL, and confirm dynamic tags, CSS, layout assertions, and console/page errors.
4. Delete test post
**Exit:** All verifications pass. CPT is production-ready (pending template visual design).

## Transactional / Private CPT Variant

When the CPT represents RFQs, leads, inquiries, support tickets, or other private
workflow records, read `references/voxel/transactional-cpt-recipe.md` before Phase 2.
That reference owns only the field/access/template deltas; this lifecycle still owns
registration, application order, and verification.
## Operational Reference

Field conventions, mandatory option overrides, failure recovery, modified-file ownership,
and revision-pruning commands live in
`references/voxel/cpt-lifecycle-operations.md`. Read the relevant section when its
condition occurs; do not load it for every lifecycle run.

## Mistake guards

- Never configure Voxel fields manually when a blueprint is the SSOT.
- Never create posts before permalink defaults/parent pages are set.
- Never skip reindex/search/schema/sitemap verification after field or filter changes.
## Success criteria

- [ ] CPT registered with correct settings (has_archive disabled, hierarchical enabled)
- [ ] Blueprint created and committed
- [ ] Fields verified via `wpdev voxel:fields`
- [ ] Parent page exists at `/<key>/`
- [ ] Permalink default configured
- [ ] URL resolution verified with test post
- [ ] Schema renders correctly (verified via curl)
- [ ] Sitemap includes CPT
- [ ] Index table created
- [ ] 4 template URLs provided to user
