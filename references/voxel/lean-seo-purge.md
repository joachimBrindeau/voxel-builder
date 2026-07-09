# lean-seo performance / purge — LiteSpeed cache-purge bridge + the invalidation API

The `performance` module (`modules/performance/`) is two things: a **LiteSpeed cache-purge bridge** (`purge.php` + `purge/litespeed.php`) that every other SEO surface depends on for invalidation, plus non-purge protocol tweaks (`includes/tweaks/performance.php`). Category: `preconnect`. lean-seo **no longer ships its own page cache** — caching is owned by the LiteSpeed Cache plugin; this module forwards SEO-driven invalidations to it. Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) first.

## Public purge API (`purge.php`)

```php
lean_seo_purge($urls = null)      // null → full purge; else purge specific URL(s)
lean_seo_purge_all()              // bump cache epoch + full purge   ← use for anything global
lean_seo_bump_cache_epoch()       // advance Last-Modified epoch + drop the preconnect transient
lean_seo_nocache($reason = '')    // no-cache headers for dynamic endpoints
```

- **`lean_seo_purge_all()`** calls `lean_seo_bump_cache_epoch()` **then** a full purge. This is what every "purge after write" instruction across the other references means.
- **`lean_seo_bump_cache_epoch()`** does `update_option('lean_seo_cache_epoch', time())` and drops the `preconnect_domains` transient.

## Cache-epoch → Last-Modified

`lean_seo_cache_epoch` (option) is consumed by the `last_modified_header` tweak: on `send_headers`, singular non-admin pages emit `Last-Modified: max(get_post_modified_time, epoch)`. So bumping the epoch advances `Last-Modified` on **every** page — invalidating browser caches for edits that never touch a post record (a deploy, plugin activation, Elementor CSS flush, or a template/kit/header save). **This is the key gotcha:** those edits don't change `post_modified`, so only `lean_seo_purge_all()` (which bumps the epoch) refreshes them; a bare `lean_seo_purge($urls)` does **not** bump the epoch.

## SEO-URL helpers

`lean_seo_seo_urls($post_type, $post_id=0)` returns `/sitemap.xml`, `/sitemap-{post_type}.xml`, `/llms.txt`, `/llms-full.txt`, `/robots.txt`, plus (when `$post_id>0`) the permalink and its `.md` twin. `lean_seo_collect_post_purge_urls($post_id)` = homepage + permalink + `.md` + archive + all SEO URLs. So a single post change flushes its page, its markdown twin, and every generated SEO surface that lists it.

## Hooks that trigger purges

Per-object (targeted):

| Hook | Priority | Action |
|---|---|---|
| `lean_seo_post_changed` | 20 | purge post + permalink + `.md` + archive + SEO URLs |
| `delete_post` | 20 | purge that post's collected URLs |
| `set_object_terms` | 20 | purge homepage + affected term archives |
| `created_term`/`edited_term`/`delete_term` | default | purge homepage + term archive |

Full-purge (all → `lean_seo_purge_all` → epoch bump + full flush), filterable via `lean_seo_purge_hooks`:

```
wp_update_nav_menu, wp_create_nav_menu, wp_delete_nav_menu,
switch_theme, customize_save_after,
save_post_elementor_library,        // header/footer/kit/card template edits
elementor/core/files/clear_cache
```

These are the theme/menu/template changes that don't touch any single post's `post_modified` — hence full purge + epoch bump. Voxel/Elementor header/footer/kit/card edits land here.

## LiteSpeed backend (`purge/litespeed.php`)

`lean_seo_purge_litespeed($urls, $all)`:
1. **LSCWP active** → `$all` fires `litespeed_purge_all`; else per-URL `litespeed_purge_url`.
2. **LSCWP inactive** → falls back to native `X-LiteSpeed-Purge` response headers, accumulated request-wide and flushed once on `shutdown`/`wp_redirect`.

URLs map to LiteSpeed tags `front,archive` + `P.{id}` + `PT.{post_type}`.

## Non-purge performance tweaks

All in `includes/tweaks/performance.php`, module `performance`, `default: true`:

| Tweak | Effect | SEO relevance |
|---|---|---|
| `last_modified_header` | `Last-Modified: max(post mtime, epoch)` on singulars | **SEO** — crawler/browser freshness; the epoch consumer |
| `auto_preconnect` | auto-detect cross-origin asset domains → preconnect links | perf (CWV) |
| manual preconnect | `<link rel=preconnect>` per domain in the `preconnect` settings category | perf |
| `defer_jquery` | jQuery→footer+defer via a dependency-safety walk; **handles Voxel's force-enqueued `jquery-core`** | perf (CWV) |
| `disable_xmlrpc` / `disable_self_pingbacks` / `disable_outbound_pings` | hardening (pinging obsoleted by IndexNow) | generic |
| LCP/lazyload reconciliation | marks `fetchpriority="high"` imgs `data-no-lazy` so LiteSpeed lazyload doesn't cancel the LCP preload | perf |

Manual preconnect domains are the `preconnect` settings category (`lean_seo_settings_values('preconnect')`); the auto-detected set is a `preconnect_domains` transient (1-day TTL, self-healing — invalidated by the epoch bump).

## Voxel-specific touches

- `defer_jquery` explicitly accounts for Voxel's theme force-enqueuing `jquery-core` into the head — moving it to the footer only when nothing in the head needs it synchronously.
- `save_post_elementor_library` + `elementor/core/files/clear_cache` full-purge hooks cover Voxel/Elementor header/footer/kit/card template edits (which need the epoch bump).

## Gotchas

- **Epoch bump required** for template/kit/header/theme edits — only `lean_seo_purge_all()`-wired hooks bump it; bare `lean_seo_purge($urls)` doesn't.
- **LiteSpeed dependency** — no LSCWP + no LiteSpeed server honouring `X-LiteSpeed-Purge` = purges are no-ops.
- **Module-toggle purge** — enabling/disabling any module full-purges via `lean_seo_set_module_enabled()`; critical for the maintenance module (its enabled state IS the 503 switch).
- Preconnect auto-transient has a 1-day TTL; only epoch bumps invalidate it early.
