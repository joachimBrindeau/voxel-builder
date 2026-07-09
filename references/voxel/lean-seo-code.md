# lean-seo code — analytics scripts + search-engine verification tags

The `code` module (`modules/code/`) outputs analytics vendor scripts and search-engine **site-verification `<meta>` tags** (Google Search Console, Bing, Yandex — the "prove you own this site" tags). Config persists in the **`lean_seo_tag`** option (category `tag`). Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) first.

## Storage — `lean_seo_tag`

Standard typed rows, seeded empty on `admin_init`:

```php
'lean_seo_tag' => [
  '{key}' => [ 'value' => '', 'type' => 'text'|'url', 'description' => '{label}' ],
]
```

Read at render via `lean_seo_settings_map('tag')` (flattens to `key => value`). Renderers auto-activate when a key is populated — no separate enable flag.

## Tag registry

`lean_seo_tag_registry()` (`code.php`, filter `lean_seo_tag_registry`) defines every tag. Each entry is `{ label, type, group, enqueue?, meta? }` in one of three shapes: an **`enqueue` callback** (analytics scripts), a **`meta` string** (verification `<meta>`), or **neither** (a helper field consumed by another tag, e.g. a host URL).

Built-in keys:

| key | group | shape | notes |
|---|---|---|---|
| `gsc_code` | verification | meta `google-site-verification` | Google Search Console |
| `bing_code` | verification | meta `msvalidate.01` | Bing Webmaster |
| `yandex_code` | verification | meta `yandex-verification` | Yandex Webmaster |
| `ga4_id` | analytics | enqueue → gtag.js (async) | GA4 |
| `gtm_id` | analytics | enqueue → inline GTM loader | Google Tag Manager |
| `plausible_domain` | analytics | enqueue → plausible.io script | data-domain |
| `fathom_id` | analytics | enqueue → cdn.usefathom.com | data-site |
| `umami_id` (+ `umami_host` helper) | analytics | enqueue → Umami | data-website-id, needs host |
| `matomo_id` (+ `matomo_host` helper) | analytics | enqueue → inline `_paq` | needs host |
| `simple_analytics_flag` | analytics | enqueue (value `'1'`) | + `<noscript>` pixel |
| `hotjar_id` / `clarity_id` | analytics | enqueue → inline | |

## Output hooks

- **`wp_head` priority 1** → verification `<meta>` tags only (`lean_seo_tag_render_registry_meta` then the fallback). Runs very early, before most theme/Voxel head output.
- **`wp_enqueue_scripts`** → one loop over the registry: any key with a non-empty value **and** an `enqueue` callback is dispatched. Scripts go through the WP script API (registered handles + `strategy` async/defer hints), not raw `wp_head` echo. Helpers: `lean_seo_tag_inline_script()` (bodyless handle + `wp_add_inline_script`), `lean_seo_tag_data_attr_script()` (external CDN src + injected `data-*` via `script_loader_tag`).

## The `*_code` fallback — zero-code custom verification

Any `lean_seo_tag` key **ending in `_code`** that is *not* in the registry auto-renders as `<meta name="{key minus '_code', underscores→hyphens}" content="{value}">`. So storing a custom `pinterest_code` value (via the admin Advanced raw-tags panel) emits `<meta name="pinterest" content="...">` with no filter needed. This is the general "add any verification service" escape hatch.

## Adding custom tags

1. `lean_seo_tag_registry` filter — register a full entry (with `enqueue` or `meta`).
2. `lean_seo_code_providers` filter — add a two-click provider card mapping to `tag` keys.
3. The `*_code` fallback — for zero-code custom verification meta.

## Admin surface

Submenu page `lean_seo_code_page` (`modules/code/providers/render.php`): platform dropdown + progressive-disclosure provider cards (privacy-friendly first: Umami, Plausible, Fathom, Simple Analytics, Matomo, then GA4, GTM, Hotjar, Clarity) + a `<details>` "Advanced: raw verification & custom tags" panel. A card is `enabled` only when every field is filled; it just writes `tag` settings.

## SEO relevance & Voxel interaction

The **verification tags are the SEO-critical part** — they're how you register the site with Search Console / Bing Webmaster / Yandex. Analytics is measurement, not SEO output. No Voxel interaction — pure WP hooks.

## Gotchas

- Umami/Matomo silently no-op unless the `*_host` helper is populated.
- Verification meta prints at `wp_head` prio 1 — before theme/Voxel head output.
- Values stored raw, `esc_attr`'d at output; no format validation on IDs.
- `strategy` async/defer hints need WP 6.3+ for full effect.
