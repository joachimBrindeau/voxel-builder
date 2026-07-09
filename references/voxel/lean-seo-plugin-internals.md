# lean-seo plugin internals — architecture map (for reading/modifying the PHP)

`plugins/custom/lean-seo` is a first-party, module-based WordPress SEO plugin in this workspace, replacing Rank Math / Permalink Manager / Yoast with a lean, Voxel-aware engine. This is the map to its **source architecture** — read this when reading, modifying, or debugging the plugin's PHP, not when configuring a site (that's [`../../workflows/settings.md`](../../workflows/settings.md) + the per-surface refs). The exhaustive source-verified function/path reference is [`lean-seo-crawl-permalinks-linking-reference.md`](lean-seo-crawl-permalinks-linking-reference.md).

## When to use this file

- Reading/modifying any module under `modules/<name>/` (crawl, permalinks, linking, meta, schema, llms, redirects, code, performance, media, maintenance).
- Tracing why a Voxel CPT/post does or doesn't appear in the XML sitemap, HTML sitemap, robots meta, or llms feed.
- Debugging permalink resolution (404s, duplicate URLs, canonical URI drift) or internal-link suggestions.
- Adding a setting, filter hook, or per-CPT behavior in the plugin.
- Producing a technical reference of lean-seo behavior for a Voxel site.

## Architecture at a glance

- **Module registry**: `includes/modules.php` → `lean_seo_modules()`. Each module declares `files`, `categories` (settings-store buckets), `page_title`, `render`. Submenu order in `includes/settings.php` → `lean_seo_submenu_order()`.
- **Unified settings store**: `includes/settings-store.php`. Each *category* is ONE `wp_option` named `lean_seo_<category>` holding a JSON map `key => {value,type,description}`. Read with `lean_seo_settings_get_value($cat,$key,$def)`, `lean_seo_settings_map($cat)` (key⇒value), `lean_seo_settings_values/keys()`. Write with `lean_seo_settings_set/update()`. Only `tweak`+`variable` autoload. Per-category memo → call `lean_seo_settings_flush_cache()` after writes; most enumerators are also `static`-memoized per request.
- **Constants**: `includes/config.php` (`LEAN_SEO_META_NOINDEX='_lean_seo_noindex'`, `LEAN_SEO_ENDPOINT_SITEMAP='sitemap.xml'`, `LEAN_SEO_CACHE_SITEMAP=HOUR_IN_SECONDS`, sitemap changefreq day thresholds, noindex meta-kind slugs `LEAN_SEO_META_KIND_NOINDEX_*`).
- **Voxel guard layer**: `includes/voxel.php`. ALL Voxel access is guarded (`lean_seo_has_voxel()`) so it degrades on non-Voxel sites. `lean_seo_post_value($post,'permalink')` / `lean_seo_post_text_value($post,'title')` are the Voxel-aware resolvers used EVERYWHERE — that's what makes every surface honor Voxel fields uniformly. (Full resolver table in [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) §Voxel guard layer.)

## The single-source-of-truth predicates (memorize these)

These are the join points where "does this post/type belong on a crawl surface?" is decided ONCE and reused by XML sitemap, HTML sitemap, llms, and singular robots-meta — change one and all move together (by design):

- `lean_seo_get_sitemap_post_types()` (`includes/helpers.php`): `public=true` types + `tweak.sitemap_extra_types` − `lean_seo_sitemap_exclude()` (attachment + internals + `lean_seo_noindex_post_types()` + `tweak.sitemap_exclude_types`). **Voxel CPTs with `public=true` are auto-included.**
- `lean_seo_noindex_post_types()` (`includes/config.php`): `['attachment']` + any scope where the Meta module's per-CPT `noindex_post_type` toggle is on. Subtracted from the sitemap too.
- `lean_seo_post_is_index_excluded($post)` (`includes/helpers/noindex.php`): per-post overlay — `_lean_seo_noindex` meta, OR title-less published placeholder (`lean_seo_post_is_titleless`, Voxel profiles saved before naming), OR path match `lean_seo_is_excluded()` against `noindex` category patterns (trailing `*` wildcard).

## Module quick map

- **crawl** (categories `crawl`,`noindex`,`ai_crawler`; sitemap type-lists live in `tweak`): `crawl.sitemap_index='1'` splits into `sitemap-<type>.xml` (rewrite rules only register when enabled → FLUSH rewrites after toggling). robots.txt from `noindex` paths + `ai_crawler` allow/disallow map. `[sitemap]` HTML shortcode mirrors the XML surface via the SSOT predicates.
- **permalinks** (category `permalink_default`): canonical-URI SSOT — one indexed meta `_lean_seo_uri` per managed post, built from the `post_parent` ancestor chain. Generation (`page_link`/`post_link`/`post_type_link`) and resolution (`request` filter) key off the SAME string → symmetric round-trip. Managed types fold in Voxel-owned CPTs via `voxel_addon_hierarchy_post_parent_owned_cpts` and drop flat CPTs via `voxel_addon_hierarchy_flat_url_cpts`. Default-parent + auto-parent give Voxel CPTs clean nested URLs. Author archives 301 to the Voxel profile CPT. CLI: `wp lean-seo permalinks backfill|parent-backfill|verify`.
- **linking** (category `linking`): internal-link suggestions with manual approval. Field configs use `core:<column>` / `meta:<key>`. Voxel custom fields surface as selectable `meta:<key>` (decoded from `voxel:post_types` option). Hierarchy enforcement matches native `post_parent` OR a Voxel relation meta value (single ID / serialized / JSON / CSV).

For the full config-oriented treatment of these three surfaces see [`lean-seo-crawl-permalinks.md`](lean-seo-crawl-permalinks.md); for the exhaustive source reference see [`lean-seo-crawl-permalinks-linking-reference.md`](lean-seo-crawl-permalinks-linking-reference.md).

## Meta + Schema surfaces (token grammars)

The crawl/permalinks/linking map above is deep; the **meta** and **schema** modules add their own resolution grammars — do not confuse the four dialects (wrong dialect is the #1 misconfiguration). Full treatment in [`lean-seo-metadata.md`](lean-seo-metadata.md) and [`lean-seo-schema.md`](lean-seo-schema.md); the essentials:

- **Meta** (`modules/meta/`, category `meta`, option `lean_seo_meta`): kind×scope keys built by `lean_seo_build_meta_setting_key($kind,$scope)` where `$scope` is the **bare post-type slug** (`title_template_org`) or `taxonomy-<slug>` — NOT a `post:<cpt>` target. Templates use the **`%token%`** dialect (`includes/template-tokens.php`) plus the `%vx(@post(key))%` wrapper for a full Voxel dynamic tag; a bare `%key%` only does a meta fallback. Title fallback: template → `lean_seo_title_meta_key()` (**defaults to `'h1'`**, a Voxel field; override with the `lean_seo_title_meta_key` filter on non-Voxel sites) → post title. Per-post overrides in `_lean_seo_{description,canonical,noindex,og_image}`.
- **Schema** (`modules/schema/`): **stored per-target** — `lean_seo_schema:{target}` (JSON string) + index `lean_seo_schema_targets`. A legacy monolithic `lean_seo_schema` is auto-migrated on `plugins_loaded` prio 5 then deleted — do NOT write it. CRUD via `lean_seo_schema_save_config()` / `_delete_config()` / `_get_configs()` (there is NO `schema` settings-store category). Leaves are **`prefix:key|transform`** source strings resolved by `lean_seo_schema_resolve_source()` (`modules/schema/sources.php`, 22-prefix registry). Voxel prefixes: `voxel:` / `relation:` / `relation_field:` / `related:` / `hierarchy:`. Control keys `@each`/`@map`/`@filter`/`@require`/`@list`; `relation:` needs `@each`; prefer `voxel:` over `meta:`.
- **Markdown/llms** (`modules/llms/`, option `lean_seo_markdown_field_maps`): **`@post(key)`** dtag dialect; details + the frontend-fetch single-template fallback in [`lean-seo-markdown.md`](lean-seo-markdown.md).

**The agnostic field-catalog seam:** every surface's field picker draws from `lean_seo_available_field_groups($target)` (`includes/available-fields.php`) → Core / Voxel / Meta groups; Voxel keys are walked recursively from the `voxel:post_types` option by `lean_seo_collect_voxel_field_labels`. Register a field as Voxel/meta and it appears in every picker — never hardcode a site's field.

**Author↔profile seam:** Voxel rewrites `author_base` to the `profile` CPT, so `/profile/<nicename>` are author archives. `includes/voxel.php` canonicalizes author URLs to the linked profile permalink AND renders the `profile` schema config against the profile post (filter `lean_seo_schema_author_context`) — miss this and you get duplicate author/CPT URLs.

## Key gotchas

- **Rewrite flush** required after enabling `crawl.sitemap_index` and after Voxel CPT registration changes.
- **Memoization + caching**: type enumerators and `build_uri`/`clean_slug` are `static`-cached per request; sitemap/HTML outputs are transient-cached 1h. Settings changes need a new request or `lean_seo_settings_flush_cache()`.
- **`tweak` vs `crawl` category split**: `sitemap_exclude_types` / `sitemap_extra_types` / `sitemap_high_priority_types` live in `tweak`, NOT `crawl`. Easy to look in the wrong option.
- **Non-page CPT at `post_parent=0` gets NO `_lean_seo_uri`** (avoids phantom bare-slug URLs) → keeps default `/cpt/slug`.
- **Migration/import order**: `wp lean-seo permalinks parent-backfill` (assign parents) BEFORE `backfill` (persist URIs), then `verify`. Changing a default parent → re-run with `--previous-default=<old_id>`.
- **Voxel filter dependency**: `voxel_addon_hierarchy_*` filters are consumed but DEFINED by voxel-addon; without it they default to `[]` and only `page` + `public&&hierarchical` CPTs are managed.

## Related

- Full module-by-module source reference (crawl/permalinks/linking + Voxel interaction, exact function names + option shapes): [`lean-seo-crawl-permalinks-linking-reference.md`](lean-seo-crawl-permalinks-linking-reference.md).
- Shared config substrate (option store, field catalog, Voxel guard, token dialects): [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md).
- Per-CPT configuration process (Phase-0 field-catalog preflight → per-surface verify): [`../../workflows/settings.md`](../../workflows/settings.md).
- Excerpt/meta-description bulk work + the llms.txt markdown truncation pitfall: `wp-seo-excerpts` skill.
