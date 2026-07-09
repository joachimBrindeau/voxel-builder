# lean-seo — CRAWL, PERMALINKS, LINKING Reference (Voxel-aware)

Exact function names + file paths, verified from source. Portable to any Voxel site.

## 0. Settings storage
`includes/settings-store.php`. One `wp_option` per category `lean_seo_<category>`, JSON map `key => {value,type,description}`.
Accessors: `lean_seo_settings_get_value/map/values/keys/set/update`, memo via `lean_seo_settings_entries`, flush `lean_seo_settings_flush_cache`.
Autoload only `tweak`,`variable`. Category→module in `includes/modules.php` `lean_seo_modules()`:
- crawl → `['crawl','noindex','ai_crawler']` (files sitemap.php, sitemap-xsl.php, html-sitemap.php, robots.php, indexnow.php)
- permalinks → `['permalink_default']`; linking → `['linking']`
Sitemap type-lists live in **`tweak`** category, not crawl.

## 1. CRAWL

### Keys
```
crawl.sitemap_index = '0'|'1'   → lean_seo_sitemap_index_enabled()
ai_crawler map: botName => 'allow'|'disallow'   → lean_seo_robots_ai_crawler_lines()
noindex map: '/path/*' => 'desc'   → lean_seo_noindex_paths()  (trailing * wildcard)
tweak.sitemap_exclude_types / sitemap_extra_types / sitemap_high_priority_types (CSV; default high=['page'])
```
Constants: LEAN_SEO_ENDPOINT_SITEMAP='sitemap.xml', LEAN_SEO_CACHE_SITEMAP=HOUR, LEAN_SEO_META_NOINDEX='_lean_seo_noindex', changefreq DAILY=7d WEEKLY=30d; LEAN_SEO_SITEMAP_QUERY_BATCH=2000.

### XML sitemap (modules/crawl/sitemap.php)
Disables WP core sitemaps. Rewrites on init: `^sitemap\.xml$`, `^sitemap\.xsl$`, and (only if index enabled) `^sitemap-([a-z0-9_-]+)\.xml$`. Served on template_redirect: flat urlset | `<sitemapindex>` | per-type sub-sitemap (unknown type→404).
`lean_seo_generate_sitemap_xml(?$type)`: transient cache (`sitemap_xml`|`sitemap_<type>`), batched get_posts (2000/page, modified DESC), primes caches, per post `lean_seo_build_url_entry()`.
Entry: `<loc>`=lean_seo_post_value($p,'permalink'), lastmod, changefreq (age via `lean_seo_sitemap_changefreq`), priority (0.9 if in `lean_seo_sitemap_high_priority_types()` else 0.8), optional `<image:image>` (featured img) + `<geo:geo>` (Voxel geo-lat/geo-lng). Filters `lean_seo_sitemap_entry`, `lean_seo_sitemap_namespaces`.
Index: `lean_seo_generate_sitemap_index()` one `<sitemap>` per type. Invalidate on `lean_seo_post_changed` (if `lean_seo_is_sitemap_post_type`) + `delete_post`.

### Post-type enumeration SSOT (includes/helpers.php)
`lean_seo_get_sitemap_post_types()` = get_post_types(public=true) + `lean_seo_sitemap_extra_types()` − `lean_seo_sitemap_exclude()`.
`lean_seo_sitemap_exclude()` (config.php) = attachment + `lean_seo_internal_post_types()` + `lean_seo_noindex_post_types()` + tweak.sitemap_exclude_types. Filters: lean_seo_sitemap_exclude / _extra_types.
**Voxel: any public=true CPT auto-included.** `lean_seo_is_sitemap_post_type($pt)` shared gate (crawl/IndexNow/llms).

### robots.txt (modules/crawl/robots.php)
`lean_seo_robots_txt_lines()`: host, `User-agent:*/Allow:/`, `Disallow:/wp-admin/`, one Disallow per noindex path, `Allow:/wp-admin/admin-ajax.php`, llms.txt pointers, AI-crawler block (bots `^[a-zA-Z0-9_-]+$`), Sitemap lines (main + per-type if index). Hook `robots_txt` (private blog → `Disallow:/`).

### robots meta noindex
`lean_seo_robots_should_noindex()` → wp_robots noindex+follow for: 404 (noindex_404), low-value archives (`lean_seo_current_archive_should_noindex()`: search/paginated/empty-term/date/author/non-post-type archive, each gated by a LEAN_SEO_META_KIND_NOINDEX_* setting), singular (`lean_seo_singular_should_noindex()` = noindex post type OR `lean_seo_post_is_index_excluded` OR password if noindex_password_protected), path exclusion.
`lean_seo_noindex_post_types()` = ['attachment'] + scopes with Meta `noindex_post_type` toggle on. **Also subtracted from sitemap** → one flag hides a CPT everywhere. Filter lean_seo_noindex_post_types.

### Per-post SSOT (includes/helpers/noindex.php)
`lean_seo_post_is_index_excluded($post)`: `_lean_seo_noindex` meta OR `lean_seo_post_is_titleless` (empty resolved title, Voxel placeholder; filter lean_seo_post_is_titleless) OR `lean_seo_is_excluded($permalink)`. Applied by XML+HTML+llms+singular robots so they never diverge.

### HTML sitemap (modules/crawl/html-sitemap.php)
`[sitemap]` → `lean_seo_generate_html_sitemap()` cache `sitemap_html`. `lean_seo_sitemap_query_rows()` selects published/non-password/non-noindex-meta across sitemap types, then filters each via `lean_seo_post_is_index_excluded`. Hierarchical types → post_parent tree (depth cap 10) rooted at static front page; non-hierarchical → grouped under `get_post_type_archive_link()`. Voxel-aware permalink/title.

## 2. PERMALINKS

### Canonical-URI SSOT (modules/permalinks/inc/canonical-uri.php)
`const LEAN_SEO_URI_META_KEY='_lean_seo_uri'` (no slashes, e.g. "services/discovery/x"). Generation & resolution key off SAME string.
Managed types `lean_seo_permalink_managed_post_types()` (memoized): always page; public&&hierarchical − excluded (attachment+internals); **+ Voxel-owned** `apply_filters('voxel_addon_hierarchy_post_parent_owned_cpts',[])`; + CPTs with default parent; **− flat** `apply_filters('voxel_addon_hierarchy_flat_url_cpts',[])`; filter lean_seo_permalink_managed_post_types.
Persist gate `lean_seo_permalink_should_persist_uri()`: page always; non-page CPT only if post_parent>0. `lean_seo_persist_uri($id)` write/delete; `lean_seo_persist_uri_subtree()` cascades (MAX_DESCENDANTS=5000, MAX_DEPTH=12). Hooks save_post(20), lean_seo_post_changed. Reverse `lean_seo_resolve_uri_meta($uri,$types)` indexed = match.

### URI build + slug clean (permalinks.php)
`lean_seo_build_uri($id)`: walk get_post_ancestors, implode('/') cleaned post_names, strip front slug; memoized. `lean_seo_clean_slug($slug,$parent)`: strips WP dedup -2/-3 safely (global existence + sibling collision), preserves calendrier-2025; object-cache namespaced by epoch. `lean_seo_permalink_flush_caches()` resets memos+bumps epoch on save_post/deleted_post/lean_seo_post_changed.

### Generation (inc/url-generation.php)
`lean_seo_canonical_uri($id)` = stored meta else build_uri. `page_link` always rewritten (front→home_url('/')). `post_link`/`post_type_link` rewritten only if post_parent set AND managed type.

### Resolution (inc/url-resolution.php)
`request` filter (prio1): clean path from REQUEST_URI, skip wp-json/wp-admin/feed/.xml/.xsl/.txt, strip page/N. Primary `lean_seo_resolve_uri_meta` else legacy `lean_seo_resolve_legacy_fallback` (get_page_by_path + `lean_seo_resolve_clean_path`). Sets page_id|p+post_type (path-independent). Types `lean_seo_resolution_post_types()`.

### Parent resolution (Voxel-relevant)
default-parent.php: category `permalink_default` type page_select, one row per managed non-page CPT. `const LEAN_SEO_PARENT_MANUAL_META_KEY='_lean_seo_parent_manual'`. `lean_seo_apply_default_parent($id,$prev,$dry)` states: applied/already_default/manual_parent/manual_opt_out/no_default/invalid_post/invalid_default. Default must be published page, not self/ancestor.
auto-parent.php: on wp_insert_post non-page CPT → apply default parent; on save_post_page page with parent=0 → parent under page_on_front. Self-referencing closures un-hooked during own write.
meta-box.php (admin): replaces pageparentdiv on post/page/public-queryable CPTs. Save: raw `$wpdb->update(post_parent)` + clean_post_cache + set/clear manual marker + `lean_seo_persist_uri_subtree`.

### Breadcrumbs (breadcrumbs.php)
`[breadcrumb]` + `lean_seo_breadcrumb_trail()` (shared with schema). Singular: get_post_ancestors chain (skip front). Archive/tax: URL-path via segment-wise get_page_by_path. Voxel-aware title/permalink. Memoized. Filter lean_seo_breadcrumb_class.

### CLI (includes/cli/permalinks.php) — WP_CLI only
`wp lean-seo permalinks backfill|parent-backfill|verify` [--dry-run] [--post-type=] [--previous-default=]. backfill persists _lean_seo_uri for published managed posts; parent-backfill applies defaults (never overwrites manual); verify = coverage + collision report (GROUP BY meta_value HAVING n>1).

### Author↔profile (includes/voxel.php)
`author_link` filter + template_redirect 301 collapse `/profile/<nicename>` onto linked profile CPT permalink (Constants::CPT_PROFILE). Prevents duplicate URLs vs parent-derived profile URL.

## 3. LINKING (modules/linking/)

### Keys (category linking; list keys CSV)
keyword_field=core:post_title, content_field=core:post_content, source_post_type=post, target_post_type='', enforce_hierarchy='0', parent_field='', chars_per_link=1500, batch_size=50, max_target_posts=1000, context_words=5, stop_words='', stopwords_language=auto, excluded_post_types='', allow_multiple_links_per_pair='0', match_selection_strategy=random, whole_word_matching='1'.
Field config `core:<col>`|`meta:<key>` (inc/fields.php `lean_seo_linking_field_parse`). Core cols: post_content/post_title/post_excerpt/post_parent. Default excluded list in `lean_seo_linking_default_excluded_post_types()` (empty setting → falls back to this list, NOT "exclude nothing").

### Admin (inc/admin.php)
Screen lean-seo-linking (hook seo_page_lean-seo-linking). Tabs Suggestions/Settings. Nonce lean_seo_linking. Save action admin_post_lean_seo_linking_save_settings. Statuses LEAN_SEO_LINK_STATUS_SUGGESTED/ACCEPTED/REJECTED/MANUAL. Per-row write enforces current_user_can('edit_post',$source).

### Voxel integration
Field catalog Voxel-aware: `lean_seo_available_field_groups()` (includes/available-fields.php) merges a Voxel group from `lean_seo_voxel_field_labels()` decoding `get_option('voxel:post_types')` (recursive key/label) → Voxel fields selectable as `meta:<key>`.
source/target_post_type = any Voxel CPT slug.
Hierarchy (inc/posts.php, inc/fields.php): enforce_hierarchy+parent_field →
- parent_field=core:post_parent → `AND post_parent=%d`
- parent_field=meta:<key> (Voxel relation) → JOIN pm_parent + match single ID / `%i:<id>;%` / `%"<id>"%` / `,<id>,`.
`lean_seo_linking_field_get_value` reads core off WP_Post or meta via get_post_meta (Voxel field = post meta, no Voxel API at read).

### Linking gotchas
- Voxel relation must be resolvable ID/serialized/JSON/CSV or hierarchy won't match.
- Meta-key dropdown cached 1h (`linking_meta_keys`); new Voxel field may lag.
- Field must be core:/meta: prefixed (bare→unknown→empty).
- Accept writes `<a>` into content field via `lean_seo_linking_field_update_value` (disables revisions during core write).

## 4. Shared Voxel guards (includes/voxel.php)
lean_seo_has_voxel / voxel_post / voxel_render(@site/@post/@author tags) / voxel_field_value / get_related_ids / get_relation. lean_seo_post_value/_text_value = Voxel-aware resolvers used everywhere. Exposes site vars as @site(seo.*).

## 5. Cross-cutting gotchas
- Flush rewrites after crawl.sitemap_index toggle + Voxel CPT changes.
- static-memoized enumerators + 1h transients → settings need new request / flush_cache.
- SSOT: change lean_seo_post_is_index_excluded or get_sitemap_post_types → all 4 surfaces move.
- Backfill order: parent-backfill → backfill → verify; changed default → --previous-default=<old>.
- voxel_addon_hierarchy_* filters defined by voxel-addon; absent → only page+public&&hierarchical managed.
