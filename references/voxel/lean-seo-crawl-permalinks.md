# lean-seo crawl / permalinks / linking — indexing, URL structure, Voxel CPTs

Three modules that govern how crawlers reach and traverse a Voxel site. Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) first.

## Crawl module — sitemap, robots, HTML sitemap, noindex

`modules/crawl/` (files: `sitemap.php`, `robots.php`, `html-sitemap.php`, plus `indexnow.php`, `sitemap-xsl.php`). Categories: `crawl`, `noindex`, `ai_crawler`.

### XML sitemap — CPT enumeration

`lean_seo_get_sitemap_post_types()` (`includes/helpers.php`, memoized) is the single source:

```
types = get_post_types(['public'=>true])
      + lean_seo_sitemap_extra_types()      // tweak 'sitemap_extra_types' CSV + filter
      - lean_seo_sitemap_exclude()          // attachment, internals, noindex types, tweak 'sitemap_exclude_types'
```

**The list settings live in the `tweak` category, NOT `crawl`** (`sitemap_extra_types`, `sitemap_exclude_types`, `sitemap_high_priority_types` — default `['page']`). So **any Voxel CPT registered `public=true` is auto-included** — no per-CPT opt-in. To drop one: flag it noindex (below) or add its slug to `tweak.sitemap_exclude_types`. `lean_seo_is_sitemap_post_type($pt)` is the shared membership gate used by crawl/IndexNow/llms. The `crawl` category itself holds toggles like `sitemap_index` (flat vs split-index mode). Sitemap is index-mode-optional, batched (`LEAN_SEO_SITEMAP_QUERY_BATCH=2000`), transient-cached 1h, per-post entries rendered via `lean_seo_voxel_render_groups()`. Geo entries pull Voxel `geo-lat`/`geo-lng`.

### Noindex decisions — per-CPT + per-post overlay

`lean_seo_noindex_post_types()` (config.php, filter `lean_seo_noindex_post_types`) = `['attachment']` + any scope where the per-CPT `NOINDEX_POST_TYPE` meta kind (the Meta module's "Noindex content type" toggle) is enabled. **This list is subtracted from the sitemap too**, so flagging a Voxel CPT noindex removes it from robots-meta, XML sitemap, HTML sitemap, and llms in one move.

On top of type-level selection, every enumerating surface applies the **per-post overlay** `lean_seo_post_is_index_excluded($post)` (`includes/helpers/noindex.php`), cheapest-first: (1) per-post `_lean_seo_noindex` meta present; (2) `lean_seo_post_is_titleless()` — a published post with an empty resolved title (a placeholder Voxel record saved before naming), filterable, keyed on "has a resolvable title" not on any slug/ID; (3) path match against `noindex` patterns. The other `noindex_*` meta kinds gate search/404/paginated/archive-subpages/empty-taxonomy/password-protected views.

### robots.txt + AI crawlers

`robots.php` → `lean_seo_robots_txt_lines()` emits the standard block + one `Disallow:` per `lean_seo_noindex_paths()` pattern + llms.txt pointers + the AI-crawler block from `lean_seo_settings_map('ai_crawler')` (category `ai_crawler`, a `bot-name => allow|disallow` map, bot names validated `^[a-zA-Z0-9_-]+$`) + `Sitemap:` lines. `indexnow.php` pings IndexNow on publish. HTML sitemap is the `[sitemap]` shortcode, rendering hierarchical types as a `post_parent` tree and non-hierarchical types grouped under their archive link, filtered through the same `lean_seo_post_is_index_excluded()` so it matches XML exactly.

## Permalinks module — URL structure + parent nesting

`modules/permalinks/` (files: `permalinks.php`, `breadcrumbs.php`, `inc/url-resolution.php`, `inc/canonical-uri.php`, `inc/meta-box.php`, `inc/default-parent.php`, `inc/auto-parent.php`). Category: `permalink_default`.

### Canonical-URI SSOT — `_lean_seo_uri`

lean-seo is a native permalink engine that derives clean URLs from the **`post_parent` ancestor chain** and stores the result in one indexed post meta, `_lean_seo_uri` (const `LEAN_SEO_URI_META_KEY`, e.g. `services/discovery/early-stage-biotech`, no leading/trailing slash). Generation (`lean_seo_build_uri` — walks `get_post_ancestors()`, cleans slugs, strips the front-page slug) and reverse resolution (`lean_seo_resolve_uri_meta` — a single indexed `meta_query`) key off the **same** string, so the round-trip is symmetric and path-independent (posts are addressed by `page_id`/`p`). A missing/stale `_lean_seo_uri` falls back to legacy path resolution — run the CLI backfill after import/migration.

**Managed post types** `lean_seo_permalink_managed_post_types()`: always `page`; all `public && hierarchical` CPTs minus excluded; **plus Voxel-owned CPTs** via `apply_filters('voxel_addon_hierarchy_post_parent_owned_cpts', [])`; plus any CPT with a configured default parent; **minus flat-URL CPTs** via `apply_filters('voxel_addon_hierarchy_flat_url_cpts', [])` (voxel-addon "nest_urls" off → keep `/cpt/slug`). Persist gate: pages always; non-page CPTs only when `post_parent > 0`.

### Parent-derived URLs + auto-parent

Two auto-parent behaviors (`inc/auto-parent.php`, closures un-hooked during their own write to avoid recursion):

- **CPT auto-parent on creation** — new non-`page` posts get a default parent via `lean_seo_apply_default_parent()`.
- **Pages under front page** — new pages with no parent are re-parented under `page_on_front`.

### Per-CPT default parent

The `permalink_default` category stores one `page_select` row per managed non-`page` CPT (`<cpt> => {value:<parent_page_id>}`). `lean_seo_apply_default_parent($id,$prev,$dry)` classifies via `lean_seo_default_parent_status()` (`applied`, `already_default`, `manual_parent`, `manual_opt_out`, `no_default`, …) and only `wp_update_post` on `applied`. The default must be a published `page`, not self/ancestor. `_lean_seo_parent_manual` marks an explicit divergence and blocks auto-application (set/cleared by the admin **Parent Page** meta box, `inc/meta-box.php`). Voxel relations feed the managed-type list through the `voxel_addon_hierarchy_*` filters above.

### Voxel author/profile URL canonicalization

Voxel rewrites `author_base` to the `profile` CPT, producing `/profile/<nicename>` for author archives. lean-seo canonicalizes those to the linked profile post's parent-derived permalink (substrate §author↔profile) so sitemap + canonical + theme links all agree — otherwise duplicate URLs.

### Breadcrumbs

`breadcrumbs.php` → `lean_seo_breadcrumb_trail()` (shared with schema so they never diverge) walks the same `get_post_ancestors()` chain on singulars (`lean_seo_post_text_value(...,'title')`), and derives archive/taxonomy ancestors from the URL path via `get_page_by_path()`.

### WP-CLI surface — `wp lean-seo permalinks <sub>`

`includes/cli/permalinks.php` (loaded only under `WP_CLI`):

- **`backfill [--dry-run]`** — compute + persist `_lean_seo_uri` for every published managed-type post; idempotent; reports written/cleared per type.
- **`parent-backfill [--dry-run] [--post-type=<slug>] [--previous-default=<id>]`** — apply configured default parents to eligible posts; never overwrites manual parents; `--previous-default` migrates posts still under a prior default; re-persists the URI subtree per applied post.
- **`verify [--format=...]`** — read-only coverage report (with-URI / legitimately-empty / MISSING) + a collision report (posts sharing a `_lean_seo_uri`).

## Linking module — internal link suggestions

`modules/linking/` (category `linking`). Generates automated internal-link suggestions with manual approval (admin: **Internal Linking**, `lean_seo_linking_admin_page`). Its selectable field catalog is Voxel-aware — `voxel:post_types` is decoded into selectable `meta:<key>` fields — and its hierarchy enforcement matches either native `post_parent` **or** a Voxel relation meta (single ID / serialized / JSON / CSV). Files: `modules/linking/inc/admin.php`, `inc/ajax.php`, `inc/fields.php`.

## Configure

```bash
wp option get lean_seo_crawl            # sitemap_index toggle, etc.
wp option get lean_seo_noindex          # path patterns
wp option get lean_seo_ai_crawler       # bot allow/deny map
wp option get lean_seo_tweak            # sitemap_extra_types / _exclude_types / _high_priority_types (CSV)
wp option get lean_seo_permalink_default
# after permalink/parent changes:
wp lean-seo permalinks backfill         # persist _lean_seo_uri corpus-wide
wp lean-seo permalinks parent-backfill  # apply configured default parents
wp rewrite flush
```

## Gotchas

- **List settings are in `tweak`, not `crawl`** — `sitemap_extra_types` / `sitemap_exclude_types` / `sitemap_high_priority_types` live in `lean_seo_tweak`; looking in `lean_seo_crawl` for them is the common miss.
- **Rewrite flush required** — the split-sitemap rewrite (`sitemap-<type>.xml`) only registers when `sitemap_index='1'`; toggling needs `wp rewrite flush` or `sitemap-<type>.xml` 404s. Same for URL-structure/parent changes.
- **Run `backfill` after import/migration** — a missing/stale `_lean_seo_uri` silently falls back to legacy resolution; slug/parent edits move the whole descendant subtree (cascade + epoch bump handle it).
- **Backfill order** — configure `permalink_default` *before* `parent-backfill`; it reads the configured default.
- **Cache purge** — sitemap/HTML/permalink/noindex outputs are transient-cached 1h and page-cached (LiteSpeed); purge after writes (`./wpdev wp <site> litespeed-purge all` or `lean_seo_purge_all()`).
- **Memoization** — `lean_seo_get_sitemap_post_types()` / `lean_seo_noindex_post_types()` are `static`; registration/setting changes within a request won't re-read.
- **Sitemap inclusion** — a Voxel CPT missing from the sitemap is usually non-public, in `sitemap_exclude_types`, noindex, or titleless — not a bug.
- **Author duplicate URLs** — if `/profile/...` and the CPT permalink both index, the author-canonicalization filter isn't active (Voxel/voxel-addon inactive or overridden).
