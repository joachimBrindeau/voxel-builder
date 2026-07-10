# Command surface

The `wpdev` CLI is the source of truth for everything Voxel- and Elementor-related in this workspace. The plugin's slash commands and subagents shell out to these CLI commands — they do not duplicate logic. Keep this reference open while building.

> **Drift audit** — for the structured map of every wpdev verb in our namespaces (surfaced / surface-pending / out-of-scope / defer), see [`wpdev-coverage.md`](wpdev-coverage.md). Add a row there whenever you wire up a new verb here.

## CPT introspection

```bash
wpdev voxel:fields <site> <cpt_key>            # field list — valid @post(<key>) tags
wpdev voxel:field-schema <site> --key <field> --patch '<json>' [--cpts <cpt_key>] [--dry-run] # safe field-definition patch; mirror the blueprint/source first
wpdev voxel:sample <site> <cpt_key>            # export the MOST-COMPLETE posts (ranked) to a temp folder
wpdev voxel:data   <site> --id <example_id>    # rendered field VALUES on a real post
wpdev voxel:templates <site>                   # all template assignments (single, card, archive, …)
wpdev voxel:status <site>                      # Voxel index health for all post types — non-OK = silent failure ahead
wpdev voxel:page   <site> --path <url_path>    # which Voxel templates render a given URL path
wpdev voxel:empty  <site>                      # blueprint fields with no data across published posts
wpdev voxel:filters <site> [<cpt_key>] [--audit] [--mode baseline|derive] [--prune] [-y] # audit/upsert search filters; changed filters recreate+reindex by default
wpdev voxel:sorting <site> [<cpt_key>] [--audit] [--replace] [-y] # audit/upsert the standard search-order set; changed orders reindex by default
wpdev rebuild <site> --only reindex [--recreate] # reindex all Voxel CPTs in one pass (--recreate rebuilds column sets; mandatory after a blueprint changes filters)
wpdev voxel:cache  <site> clear                # invalidate Voxel's cached blueprint copy
wpdev voxel:backfill-authors <site>            # restore stale or missing post_author values
wpdev voxel:settings <site> ensure-field --type <cpt_key> --fieldKey icon --fieldType icon --label Icon --dry  # provision/check a CPT icon field
wpdev voxel:settings <site> get [<path>] --json          # read voxel:post_types (all, or a dot/slash path e.g. "<cpt>/fields")
wpdev voxel:settings <site> set <path> --value=@<file.json> [--dry]  # write a path (CRUD on voxel:post_types); back up with `get --json` first
wpdev voxel:settings <site> delete <path>                # remove a path
```

## Voxel Index_Table — PHP API

`wpdev rebuild <site> --only reindex` reindexes every Voxel-managed CPT in one pass, and `--recreate` rebuilds each index table's column set from the current filter graph before reindexing — so column-schema changes (after a blueprint adds/removes search filters) are handled by `--recreate`, no longer requiring a manual call. The underlying `\Voxel\Post_Types\Index_Table` API is still documented below for direct/manual use (and for understanding what `--recreate` does). Source: `wp-content/themes/voxel/app/post-types/index-table.php` (line numbers below).

Access pattern: `$pt = \Voxel\Post_Type::get( '<key>' ); $pt->index_table->...`

```php
$pt->index_table->recreate()             // DROP + CREATE — safe re-run after blueprint changes (line 326)
$pt->index_table->create()               // CREATE TABLE IF NOT EXISTS — no-op if a stale table exists; prefer recreate() (line 181)
$pt->index_table->drop()                 // DROP TABLE IF EXISTS (also drops the price index table) (line 320)
$pt->index_table->truncate()             // empty rows, keep schema (line 315)
$pt->index_table->exists(): bool         // table-existence check + sanity on `post_status` / `priority` columns (line 331)

$pt->index_table->index( $post_ids, $filters = null )  // INSERT … ON DUPLICATE KEY UPDATE for the given IDs (line 190)
                                                       //   $filters: optional array of filter keys to limit which columns are written
$pt->index_table->unindex( $post_ids )   // DELETE rows for the given post IDs (line 303)

$pt->index_table->get_name()                  // raw table name `wp_voxel_index_<key>` (line 32)
$pt->index_table->get_escaped_name()          // esc_sql() version, safe for string interpolation (line 36)
$pt->index_table->get_price_index_escaped_name()  // sibling price-index table name (line 40)

$pt->index_table->get_sql()                   // CREATE TABLE statement that create() will run (line 121)
$pt->index_table->get_price_index_sql()       // CREATE TABLE for the price index sibling (line 145)
$pt->index_table->has_price_index_table(): bool   // true if CPT has a `product`-type field (line 168)

// SQL-fragment builders — used by Voxel filter classes during get_sql() composition.
// Rarely needed directly unless you're authoring a custom Voxel filter.
$pt->index_table->add_column( $sql )                  // (line 44)
$pt->index_table->add_key( $sql )                     // (line 56)
$pt->index_table->add_foreign_key( $sql )             // (line 68)
$pt->index_table->add_price_index_column( $sql )      // (line 50)
$pt->index_table->add_price_index_key( $sql )         // (line 62)
$pt->index_table->add_price_index_foreign_key( $sql ) // (line 74)
```

**No `delete()` method exists** — destructive verbs are `drop()` and `recreate()`. See [`cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md) §"Common failures" for the symptom catalogue.

## Widget / data introspection

```bash
wpdev elementor:schema <site>                                # EF V4 atomic widget catalog + reserved keys
wpdev elementor:schema <site> <widget>                       # one widget's full prop schema
wpdev elementor:schema <site> <widget> --prop <key>          # one prop's $$type envelope, default, enum
wpdev elementor:dump   <site> <filter> --post <id> --json    # headless/raw DB instance JSON (ts-* widgets, corpus sweeps)
wpdev elementor:tree   <site> <post_id>                      # headless/raw DB widget-tree summary
wpdev elementor:templates <site>                             # saved Elementor templates (companion to voxel:templates)
wpdev elementor:widgets <site>                               # widget usage frequency across all pages
wpdev elementor:widgets <site> --migrate                     # legacy-widget pages needing migration
wpdev elementor:icon-search "external link" [--category "UI actions"] [--limit 12] # ranked Material Symbols lookup from generated metadata
wpdev elementor:icons <site> [--unique] [--library ms] [--json] # icon values across all stored Elementor data, including templates
```

## EMCP vs headless wpdev reads

Use live Elementor MCP (EMCP) when page state must match the editor runtime or browser/editor session, especially for a single page/element:

- `get-page-structure` instead of `wpdev elementor:tree` for live editor-equivalent structure.
- `get-element-settings` instead of `wpdev elementor:dump --post <id>` when reading one live element.
- `export-page` instead of `wpdev elementor:export` when export must include Elementor editor-equivalent normalization.

Use wpdev headless commands when you need raw `_elementor_data`, DB-wide/corpus scans, deterministic offline fixtures, or migration round-trips:

- `wpdev elementor:tree` reads raw `_elementor_data` without Elementor runtime.
- `wpdev elementor:dump` uses raw SQL and can sweep complete widget corpora.
- `wpdev elementor:export` pairs with `wpdev elementor:import` for controlled migration files.
- `wpdev elementor:import --save` is the wpdev write path when you need editor-equivalent save effects after importing JSON.

Priority for Elementor reads: **EMCP live single-page/element reads > wpdev raw/corpus reads > direct SQL**. Priority for writes remains: **wpdev mutation/import wrappers > EMCP update tools > direct SQL**, because wpdev wrappers bundle snapshots, lint, CSS regeneration, and cache purge where applicable.

## Build-time scaffolds

```bash
wpdev voxel:cards    <site> [--type <key>] [--sizes small,large,link] [--replace] [-y]   # preview-card scaffold (default emits all three variants)
wpdev voxel:create   <site> <key> [--label <Label>]                                     # CPT + 4 blank templates
wpdev voxel:assign   <site> --role <role> [--type <key>] --template <id> [--unset] [-y] # assign (or --unset) template to role
```

## Revisions (offer before any modification — see [`rules.md`](rules.md) rule 6)

```bash
wpdev elementor:revisions:prune <site> --post <id> --dry   # count what would be deleted
wpdev elementor:revisions:prune <site> --post <id>         # snapshot + delete
wpdev elementor:revisions:prune <site>                     # global prune (all Elementor posts)
```

## Audit (read-only)

```bash
wpdev elementor:lint      <site> [--post <id>] [--widget <type>] [--only <cats>] [--json]   # schema validation against live EF V4 atomic
wpdev elementor:structure <site> [--type <post_type>] [--all] [-v]   # <main>/<header>/<section|aside> semantic compliance
wpdev elementor:semantic  <site> <url_or_post_id> [--headings]       # single-post structural + heading-hierarchy analysis
wpdev audit               <site> [--scope technical|a11y|wordpress|db-content|elementor|density|performance] [--live <url>]
                                                                     #   workspace-level audit (broader than per-post)
wpdev voxel:status        <site>                                     # CPT index health
```

## Write + verify

```bash
wpdev elementor:import <site> <id> <file>            # write _elementor_data from JSON (auto-snapshots first)
wpdev elementor:import <site> <id> <file> --save     # ALSO run the editor-equivalent save (document migrations + CSS regen) — single-post FULL save path
wpdev rebuild          <site> --only css             # site-wide: regenerate EVERY Elementor post's CSS file (css-only/bulk)
wpdev elementor:lint   <site> --post <id>            # validates against the live schema
wpdev elementor:revisions:restore <site> --post <id> # restore from snapshot taken by revisions:prune
wpdev rebuild          <site> --only purge           # flush all caches (object cache, transients, Elementor CSS, page cache, Voxel)
```

**Why the editor-equivalent save matters.** A direct `update_post_meta('_elementor_data', …)` (or any path that skips Elementor's save pipeline) leaves the per-post CSS file stale, leaves `_elementor_css` postmeta unrefreshed, and skips any pending document migrations registered on that post type. The editor's "Update" button runs `\Elementor\Plugin::$instance->documents->get($id)->save([...])` plus `\Elementor\Core\Files\CSS\Post::create($id)->update()`. For a single post, `wpdev elementor:import <site> <id> <file> --save` invokes both via the shared util — prefer it over a two-step import-then-save. For a site-wide CSS refresh across every Elementor post, `wpdev rebuild <site> --only css` regenerates each post's CSS file (and the full `wpdev rebuild <site>` includes this step).

## Fix-loop mutations (snapshot first per rule 6)

```bash
wpdev elementor:strip:wrappers      <site> --fix --yes                                # redundant wrapper containers (any depth, incl. root) around ef-* widgets
wpdev elementor:strip:styles        <site> [--post <id>] [--widget-type <t>] --fix -y # per-node style overrides → globals
wpdev elementor:fix:unicode         <site> [--post <id>] --fix [--dry] -y             # unicode corruption (u00e9 → é); site-wide unless --post
wpdev elementor:reset:button-variants <site> [--post <id>] --fix [--dry] -y           # ef-card action buttons → primary (first) / white (rest)
wpdev elementor:styles              <site> [--post <id>] --fix --dry                  # preview style normalization; drop --dry to apply
wpdev elementor:styles              <site> --sync-voxel                               # sync Voxel shade tokens into Elementor kit globals
wpdev elementor:styles              <site> --fix --only buttons,shadowed,voxel,units,colors,typography,headings,bloat  # scoped fixers
wpdev elementor:migrate:loop-index  <site> [--post <id>] --fix [--dry] -y             # @grp(path.index) → @grp(path.title).loop_index()
wpdev elementor:migrate:main        <site> [--post <id>] --fix [--dry] -y             # root <main> container → clean ef-wrapper(tag=main)
wpdev elementor:migrate:containers  <site> [--post <id>] --fix [--dry] -y             # legacy container → ef-wrapper (tag from html_tag; cols=N×1fr when horizontal)
wpdev elementor:loop-filter         <site> --post <id> --loop "@site(loop_<key>)" [--post-type <key>] [--filters '{…}'] [--order <sort>] -y  # apply EF query-backed loop filter; --map for batch
wpdev elementor:mutate              <site> <id> <mutator.php> [--fetch <url>] -y      # CANONICAL post-write repair: run a PHP mutator on _elementor_data → lint → CSS regen → purge → optional HTTP fetch
wpdev voxel:repair-options          <site> [--pattern "voxel:%"] --fix -y             # audit/repair double-slashed JSON in voxel:* wp_options (restores CPT registration when one or more CPTs silently vanish)
```

The `migrate:main` / `migrate:containers` pair is the structural Phase 1 of [`migrate.md`](../../workflows/migrate.md) — run them before content consolidation. `--dry` previews when paired with `--fix`; omit `--fix` for a read-only diagnostic.

`elementor:mutate` is the canonical single-post scripted-repair wrapper — prefer it over raw `wp eval-file` for any `_elementor_data` change, because it bundles the lint → per-post CSS regen → cache purge tail that a bare `eval-file` skips (without it the page renders stale). See [`build.md`](../../workflows/build.md) §Choosing the mutation tool for when to reach for it vs `elementor:import`.

## Anchor + scalar repair (consumes `elementor:anchors` output)

```bash
wpdev elementor:anchors  <site>                                                 # read-only: list broken in-page anchors
wpdev elementor:set-cssid <site> --post <id> --node <node_id> --cssid <slug> -y # write a _cssid (single)
wpdev elementor:set-cssid <site> --map /tmp/cssid-map.json -y                   # batch from JSON map
wpdev elementor:set-value <site> --post <id> --node <node_id> --path <dotted> --value <value> -y  # repoint scalar
wpdev elementor:set-value <site> --map /tmp/value-map.json -y                   # batch from JSON map
```

For icon-specific lookup/repair, use [`../icons/material-symbols/lookup-and-repair.md`](../icons/material-symbols/lookup-and-repair.md). It covers `elementor:icon-search` for ranked candidate selection, `elementor:icons` output paths, and the `settings.`/array-index conversion required by `elementor:set-value`.

The `--map` JSON shape:
- `set-cssid`: `[{"post": <post_id>, "node": "<node_id>", "cssid": "<slug>"}, …]`
- `set-value`: `[{"post": <post_id>, "node": "<node_id>", "path": "ts_actions.value.2.value.link.value.destination.value", "value": "<value>"}, …]`

## EF plugin CLI surfaces (`elementor:ef:*`)

```bash
wpdev elementor:ef:migrate <site> status                # show pending EF data-migration steps
wpdev elementor:ef:migrate <site> [run] [--from N] -y   # execute pending steps (run is default)
wpdev elementor:ef:migrate <site> release-lock          # clear a stuck migration lock
wpdev rebuild              <site> --only tokens         # sync EF design tokens → Elementor kit, clear CSS, purge cache (re-fire kit-color chain)
# To reset a token override: edit/remove it in the EF Design Tokens admin page (or the ef_tokens option), then re-run rebuild --only tokens
wpdev elementor:ef:settings <site> get [<key>]          # print all settings or one key
wpdev elementor:ef:settings <site> set <key> <value>    # write one key through the sanitize chain
wpdev elementor:ef:smtp    <site> test <email>          # send a real test message
wpdev elementor:ef:smtp    <site> clear-db-pass         # strip DB-stored SMTP password
wpdev elementor:ef:submissions <site> list              # enumerate form submissions with decoded fields
wpdev elementor:ef:tool    <site> list                  # enumerate registered ops tools
wpdev elementor:ef:tool    <site> run <slug>            # invoke one tool from migrations/tools/
```

## Codegen + CI gates (EF V4 SSOT artifacts)

These regenerate or verify the committed artifacts the skill reads (`cli/src/generated/widget-schemas.json` + sibling token/control fixtures). Run after EF widget-registration changes; `--check` is the CI drift gate.

```bash
wpdev elementor:codegen [--check] [--out <dir>]                  # regenerate widget-schemas.json + widgets.ts from the JSON SSOT
wpdev elementor:codegen:tokens   <site>                          # regenerate utils/elementor/generated/widget-tokens.ts from the live registry
wpdev elementor:codegen:verify   <site> [--widget <type>]        # cross-check PHP runtime registration vs TS codegen (live-site gate)
wpdev elementor:schema:check     <site> [--widget <type>] [--write]   # diff live widget schemas vs golden fixtures (regression gate)
wpdev elementor:controls:check   <site> [--widget <type>] [--write]   # diff live widget control trees vs golden fixtures
wpdev elementor:docs:gen [--check]                               # regenerate AUTO-GENERATED tables in voxel-builder reference .md files
wpdev elementor:fetch-flags [--tag v7.5.0] [--check]             # refresh flag-icons assets from lipis/flag-icons
```

## Schema (lean-seo)

```bash
wpdev schema:get          <site> [<target>] --json      # read Schema Builder config(s); no config means no emitted fallback schema
wpdev schema:set          <site> <target> @<file.json>  # write explicit @type or @graph config (validates before persisting)
wpdev schema:set          <site> <target> @<file.json> --force   # bypass validation warnings
wpdev schema:validate     <site>                        # static validation across all configured targets
wpdev schema:validate-live <site>                       # live JSON-LD validation against rendered pages
                                                        #   gating step for CPT-lifecycle Phase 4
```

Lean SEO schema is config-only. Do not assume hardcoded Organization/WebSite/WebPage/Article/FAQ/Breadcrumb nodes. For hierarchy-aware Voxel CPTs, author explicit `@graph` configs with `hierarchy:trail`, `hierarchy:ancestors`, and `hierarchy:children`; pin fragments in `@each` refs when needed, e.g. `{"@each":"hierarchy:children","@ref":"service"}`.

### Schema config DSL

A config value is a string source, or an object using one of the structural keys below. Source strings are `prefix:key|transform1|transform2`.

| Token | Resolves to |
|---|---|
| `post:<field>` | Native post value — `title`, `permalink`, `date`, `modified`, `excerpt`, `thumbnail_url`, or any `WP_Post` property |
| `meta:<key>` | Post meta (reads Voxel fields directly; repeater fields resolve to a row array) |
| `seo:<key>` | lean-seo computed value — `title`, `desc`, `image` (already SERP-processed) |
| `var:<key>` | Site variable — `site_url`, `site_language`, `org_name`, etc. |
| `row:<subfield>` | Sub-field of the current `@each` row (dot notation: `row:hours.0.from`) |
| `hierarchy:trail` / `:ancestors` / `:children` | Hierarchy projections (parent/child relations) |
| `query:<cpt>_ids` | Published post IDs for a CPT (e.g. `query:org_ids`); add a case in `sources/query.php` for a new CPT |
| `@value:<literal>` | Static literal string |
| `concat:a,,b` | Concatenate sources/literals (`,,` separates parts) |

| Structural key | Behavior |
|---|---|
| `@type` / `@id` | Node type + id. `@id` accepts `@ref:self#frag` (`{permalink}#frag`) or `@ref:site#frag` (`{site_url}#frag`) |
| `@each` + `@type`/props | Iterate a source (repeater rows or ID list), render an object per item |
| `@each` + `@ref` | Each item → `{"@id": "…#fragment"}` reference array |
| `@each` + `@map` | Each item resolves one scalar source (e.g. `row:url`) → **flat, de-duplicated value array** (for `sameAs` etc.). Requires current lean-seo |
| `@list` | Resolve each source, drop nulls, return a flat array |
| `@filter` | Row filter (`"field=value"`) inside `@each` |
| `\|strip_tags` | Transform: strip HTML (use on texteditor fields feeding schema text). Other transforms: `strip_tags`, `int`, `float`, `date`, `phone`, `email`, `decode`, `url_encode` |

Empty/null children are pruned (no empty strings emitted); a node with only static `@value:` children and no dynamic data is dropped.

**For a glossary / dictionary / defined-term CPT** (DefinedTerm + DefinedTermSet + `sameAs`, the field↔SERP-surface model, the answer-block rule, and the no-FAQPage constraint), use the worked recipe in [`../voxel/seo-defined-terms.md`](../voxel/seo-defined-terms.md).

## MCP fallbacks

The wpdev CLI is preferred. When the operation is ad-hoc and a CLI command would require extending the CLI:

- `mcp__elementor__get_page` / `update_page` / `download_page_to_file` — REST API for `_elementor_data`. Use for one-off reads / writes when batching via `wpdev` would be overkill.
- `mcp__mysql__run_select_query` / `read_records` / `update_record` / `bulk_update` — direct SQL on local databases. Use for inspections and rare bulk data fixes.

Priority order for any Voxel operation: **wpdev CLI > MCP tool > raw shell command.**

Raw WP-CLI passthrough (`wpdev wp <site> ...`) and site/remote/db/backup ops live in [`wpdev-ops.md`](wpdev-ops.md), not here. This file stays scoped to Voxel/Elementor/lean-seo command surfaces.
