# lean-seo maintenance — SEO-safe 503 maintenance screen

The `maintenance` module (`modules/maintenance/maintenance.php`) serves a site-wide maintenance screen with a crawler-safe SEO contract. **It has no settings page — the module's enabled state IS the switch**: the file only loads while the module is enabled, so enabling puts the site into maintenance and disabling brings it back. `default: false`, so fresh installs never boot into maintenance. Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) first.

## The SEO contract (why it's safe)

Interception is `template_redirect` at **priority 0** — a hook that never fires for `wp-admin`, `wp-login.php`, cron, `admin-ajax`, or REST, so **admin/login bypass needs no URL allow-listing**.

Guards, in order (`lean_seo_maintenance_render`):
1. `is_robots()` → return. **robots.txt stays 200** so crawlers keep reading directives and observing the per-page 503s. A 503 on robots.txt would make Google pause crawling entirely.
2. `current_user_can('manage_options')` and no `?lean_seo_maintenance_preview=1` → return. **Logged-in admins see the live site**; the preview query var renders the screen without logging out.
3. Otherwise render the screen.

The render sends (only if `! headers_sent()`):
- **`status_header(503)`** — *temporary*, keeps URLs indexed, tells crawlers to retry. This is the SEO signal.
- **`Retry-After`** — `lean_seo_maintenance_retry_after()`, filterable, default `HOUR_IN_SECONDS`.
- `Content-Type: text/html`.
- `nocache_headers()` + `X-LiteSpeed-Cache-Control: no-cache` (+ `litespeed_control_set_nocache`) → **the 503 screen is never cached** by LiteSpeed/CDN (would linger after recovery).
- **Never emits `X-Robots-Tag: noindex`.** The 503 is the SEO signal; noindex would risk dropping pages from the index.

## What's rendered

`lean_seo_maintenance_html()` is fully self-contained — **zero asset requests** (it renders while the stack is offline). Brand surface is existing WordPress settings; styling is EF (elementor-framework) design tokens:
- **Logo** — inline SVG (from `custom_logo` theme mod → `site_logo` option) with hard-coded dims stripped, else `<img>`, else a site-title wordmark. Favicon is the logo SVG as a base64 `data:` URI (no separate request).
- **Title/tagline** — `get_bloginfo('name')`/`('description')`.
- **Heading/messages** — translatable + filterable (`lean_seo_maintenance_heading`, `lean_seo_maintenance_messages`).
- **Contact email** — `lean_seo_var('maintenance_contact_email')` site variable → `admin_email` → filter.
- **Design tokens** — `EF_Tokens::root_css()` when `class_exists('EF_Tokens')` (live SSOT, honours admin overrides), else a minimal hard-coded `:root{--ef-*}` fallback.

## Admin surface

While active, `lean_seo_maintenance_page()` shows a status page: confirms the live state, a "Bring the site back online" button (reuses the module-toggle AJAX endpoint, nonce `lean_seo_module_toggle`), and a preview link. Purely informational.

## Enable/disable → cache purge

The module has no purge logic itself. The toggle path `lean_seo_set_module_enabled()` calls `lean_seo_purge_all()` (see [`lean-seo-purge.md`](lean-seo-purge.md)) so cached 200s don't linger — otherwise the one-click toggle would appear to do nothing.

## Voxel / EF interaction

No direct Voxel interaction. The only coupling is the optional `EF_Tokens::root_css()` for theming (elementor-framework, not Voxel).

## Gotchas

- The 503 must not be cached — handled by the `no-cache` headers in the render; without them the screen would linger after recovery.
- Enabling/disabling full-purges the cache via the module toggle — essential because the enabled state IS the switch.
- `default: false` is deliberate — never ship a fresh install into maintenance.
