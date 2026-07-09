# lean-seo redirects — 301 manager (custom DB table)

The `redirects` module (`modules/redirects/`) is a 301 redirect manager backed by its own DB table (not the `lean_seo_{category}` option store). It's the companion to the permalink engine: when a post's URL changes, a 301 keeps the old URL's link equity. Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) for the shared plugin context.

## Storage — custom table `{prefix}lean_seo_redirects`

Table name from `lean_seo_redirects_table()`; schema created by `lean_seo_redirects_create_table()` (`inc/db.php`) via `dbDelta`, version-tracked in option `lean_seo_redirects_version`:

```sql
CREATE TABLE {prefix}lean_seo_redirects (
    id         mediumint(9)  NOT NULL AUTO_INCREMENT,
    old_path   varchar(500)  NOT NULL,
    new_path   varchar(500)  NOT NULL,
    created_at datetime      DEFAULT CURRENT_TIMESTAMP,
    active     tinyint(1)    DEFAULT 1,
    PRIMARY KEY (id),
    UNIQUE KEY old_path (old_path),   -- dedup enforced at DB level
    KEY active (active)
);
```

**301-only by schema.** `lean_seo_redirects_insert()` accepts a `$code` arg but any non-301 is logged and downgraded to 301 — never dropped. `active=0` rows are stored but excluded from the live map.

## Serving flow

`lean_seo_redirects_handle()` on `template_redirect` **priority 5** (early, before rendering):

1. Bail if `is_admin()` or `lean_seo_redirects_is_reserved_request()` — this **protects the SEO endpoints** `/sitemap*.xml`, `/sitemap.xsl`, `/llms.txt`, `/llms-full.txt` (and their query vars) from ever being intercepted.
2. `$path = lean_seo_redirects_sanitize_path( lean_seo_request_path() )` — parse PATH only, force leading `/`, collapse `//+`→`/`, strip trailing slash (so `old-page/` and `/old-page` normalize identically).
3. Look up `$active_map[$path]`; if empty or equal → return (no-op / loop guard).
4. Preserve the query string from `REQUEST_URI`, append to `home_url($new_path)`.
5. `wp_safe_redirect( $new_url, 301 ); exit;`.

**Active-map cache:** `lean_seo_redirects_get_active_map()` runs one `SELECT ... WHERE active=1` and stores the `old_path => new_path` map in transient `redirects_active_map` for `DAY_IN_SECONDS` (table capped ~10k rows, fits one cached array). **Every write path calls `lean_seo_redirects_flush_cache()`.**

## Write API

`lean_seo_redirects_insert($old, $new, $code=301, $active=1)` (`inc/db.php`) is the single consolidated writer used by all insert sites (CSV import, add form, PM migration, CLI, the PM URI-divergence emitter): sanitize → reject empty/same/`/`-root → dedup pre-check → `$wpdb->insert` → cache flush. Returns insert id or `false`. Admin edits go through `$wpdb->update` + flush; a separate `lean_seo_redirects_validate()` supplies per-error UX messaging (`empty`/`same`/`duplicate`).

## Admin surface

Submenu page `lean_seo_redirects_admin_page` (`inc/admin.php`): add-single form, CSV import, paginated 50/page list table. AJAX inline edit `wp_ajax_lean_seo_update_redirect` → `lean_seo_redirects_handle_update` (nonce `lean_seo_redirects_ajax.nonce`).

**CSV import** (`inc/forms.php`): headers must be `path_old,path_new` (external contract; internal columns `old_path`/`new_path`). Max 10,000 rows. Options: `clear_existing` (`TRUNCATE` first) and `skip_duplicates` (default on). Each row routes through `lean_seo_redirects_insert`.

## Permalink-engine (`_lean_seo_uri`) integration

**Migration-time only.** When a managed post's canonical URI diverges from a legacy Permalink Manager URI, `lean_seo_pm_emit_divergence_redirect($pm_uri, $current_uri)` (`includes/migration/permalink-manager-pro.php`) emits a 301 from the old PM path → the current lean-seo URI via `lean_seo_redirects_insert`. This fires during PM import, **not** on live post-save — the redirects module does not subscribe to post URL changes; the permalink module owns `_lean_seo_uri` and resolution (see [`lean-seo-crawl-permalinks.md`](lean-seo-crawl-permalinks.md)). If you rename/re-parent a post post-migration and want a redirect, add it manually.

## Voxel interaction

None — pure path-based WordPress redirect. Voxel-agnostic.

## Gotchas

- Schema changes need a `lean_seo_redirects_version` bump to re-run `dbDelta`.
- Query strings are preserved and re-appended: `/old?x=1` → `/new?x=1`.
- Forgetting `flush_cache` on a new writer = stale redirects for up to a day (the single `insert` API exists precisely to avoid this).
- 301-only today; per-redirect codes are a deferred feature.
