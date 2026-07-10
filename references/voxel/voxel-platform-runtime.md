# Voxel Platform: Dynamic Data, Jobs, Privacy, Auth, And Utilities

## Dynamic Data Engine (cross-reference)

- **Path**: `dynamic-data/`
- **Purpose**: The runtime that powers every `@group(path).modifier(args)` expression.

For FULL syntax, data groups, data types, modifiers, control structures, and visibility rules, see [`voxel-tags.md`](voxel-tags.md). This file does NOT duplicate that content.

Quick summary:
- Groups: `post`, `simple-post`, `posts/relation-request`, `site`, `term`, `user`, `user/membership`, `order`, `orders/booking`, `orders/promotion`, `message`, `timeline/status`, `timeline/review`, `timeline/reply`, `value`, `noop`.
- Modifiers: see `voxel-tags.md` for the full list (`abbreviate`, `append`, `capitalize`, `count`, etc).
- Visibility rules: see `voxel-tags.md` for the full list.
- Exporter (`exporter.php`): builds a JSON catalog of every available tag for the Elementor dynamic-tag picker UI.

---

## Onboarding / Setup

- **Path**: `controllers/onboarding/`, `controllers/setup-controller.php`
- **Purpose**: First-run wizard — Voxel install, demo import option (`utils/demo-import-utils.php`), permalinks flush, default templates creation, REST API check, async-cron setup.

- **Settings surface**: `admin.php?page=voxel-settings&tab=onboarding`.

- **Gotchas**: re-running onboarding on a populated site can overwrite default templates. The wizard prompts before overwriting, but scripted re-runs (`wp eval ...`) bypass the prompt.

---

## Async Jobs & Cron

- **Path**: `controllers/cron-controller.php`, `controllers/async/`, `utils/async-requests/`
- **Purpose**: Background tasks — order sync, status re-evaluation (expirations, subscription billing cycles, scheduled posts), notification dispatch.

- **Cron tasks** (verified hook names from `controllers/cron-controller.php::schedule_cron_jobs()`):

  | Hook | Interval | Purpose |
  |---|---|---|
  | `voxel/schedule:daily` | Daily | Cleanup of expired notifications, orders, auth codes, and visit stats |
  | `voxel/schedule:cleanup_messages` | Daily | DM thread cleanup (separate hook so it can be filtered independently) |
  | `voxel/schedule:check_for_expired_posts` | `twicedaily` (filterable via `voxel/check_for_expired_posts/frequency`) | Mark posts past their `expiry_date` as expired |
  | `voxel/schedule:check_for_expired_promotions` | `twicedaily` (filterable via `voxel/check_for_expired_promotions/frequency`) | Expire promotion windows so the boosted-priority lift drops |

- **Async dispatcher** (`utils/async-requests/Async_Requests`): sends a non-blocking HTTP request to a self-handler for long jobs. Pattern:
  ```php
  Sync_Order::dispatch( [ 'order_id' => 123 ] );
  ```
  The dispatch returns immediately; the handler runs in a separate worker process.

- **Common async use cases**:
  - Order sync after Stripe webhook (offload heavy reconciliation work).
  - Notification dispatch (so a status creation doesn't block on N notification rows).
  - Index reindex after bulk imports.

- **Gotchas**:
  - WP-Cron is FAKE-CRON (triggered on page visits, not by a real cron daemon). On low-traffic sites, hourly tasks may run hours late. Use a real OS cron hitting `wp-cron.php`:
    ```
    * * * * * curl -s https://site.com/wp-cron.php?doing_wp_cron > /dev/null
    ```
    Then disable WP-Cron in `wp-config.php`: `define('DISABLE_WP_CRON', true);`.
  - Async requests use loopback HTTP (the site hits its own URL). On hosting that blocks loopback (some shared hosts), async dispatch silently fails — jobs never run.
  - Promotion expirations are cron-driven (see `voxel-commerce.md`). Broken cron = expired promotions still boost.

---

## Privacy / GDPR

- **Path**: `controllers/privacy-controller.php`
- **Purpose**: Personal-data export + erasure handlers. Hooks into WP's standard privacy tools.

- **Events**: `User_Data_Export_Requested_Event` (under `events/membership/`).

- **Per-CPT exporter wiring**: each CPT can declare a custom exporter that maps its fields to GDPR-export columns. Default: all post meta + post content are exported.

- **Gotchas**: Voxel does not yet have a one-click "delete all user data" — admins must use WP's standard erasure tool, which Voxel hooks into.

---

## Nav Menus

- **Path**: `controllers/nav-menus-controller.php`, `utils/nav-menu-walker.php`
- **Purpose**: Registers Voxel nav-menu locations, adds custom per-item fields (icon, override label, override URL, visibility rules) to the standard WP nav-menu editor, and renders dynamic-tag expressions inside menu-item titles/URLs at output time.

- **Registered menu locations** (from `register_menus()`):
  - `voxel-desktop-menu` — Desktop Menu.
  - `voxel-mobile-menu` — Mobile menu.
  - `voxel-user-menu` — User Dashboard Menu.
  - `voxel-create-menu` — Create post menu.
  - Plus any custom locations declared in `settings.nav_menus.custom_locations`.

- **Per-item custom fields** (post meta on the nav-menu item):
  - `_voxel_item_icon` — icon picker output.
  - `_voxel_item_label` — override label (supports dynamic tags).
  - `_voxel_item_url` — override URL (supports dynamic tags).
  - `_voxel_visibility_behavior` + `_voxel_visibility_rules` — show/hide rules (JSON), evaluated through the dynamic-data visibility-rule engine.

- **Dynamic rendering**: `render_nav_menu_tags` filter on `wp_setup_nav_menu_item` resolves `@user(...)`, `@site(...)`, etc. in title/URL — there is no fixed enum of "link types" like Profile/Pricing/Inbox; admins author those URLs via dynamic tags in regular WP menu items.

- **Voxel-native widget consumer**: `ts-navbar` reads the WP nav menu via this walker and renders it.

---

## Library / Templates Marketplace

- **Path**: `controllers/library/`, `controllers/templates/`
- **Purpose**: Browse + import Voxel template library (premium templates hosted on Voxel.us), custom-template management per CPT.

- **Out-of-scope note**: this is mostly an admin-only feature for browsing/importing pre-built templates. Build-time use is limited to occasional template imports. Not relevant for ongoing template-build/audit work.

---

## Text Formatter / Link Previewer / Sharer

- **Paths**: `utils/text-formatter/`, `utils/link-previewer/`, `utils/sharer.php`
- **Purpose**: Three small utility modules used by the timeline composer.

### Text Formatter (`utils/text-formatter/`)

- `\Voxel\text_formatter()` processes timeline status content:
  - Autolinks URLs.
  - Resolves `@mentions` to user-profile links.
  - Resolves `#hashtags` to hashtag-search links.
  - Inline-renders "image-as-link" previews (when a URL points to a direct image, render an `<img>` instead of a link).
  - Finds first link for link-preview generation (passes to `link_previewer()`).

### Link Previewer (`utils/link-previewer/`)

- `\Voxel\link_previewer( $url )` scrapes OG/Twitter cards from URLs:
  - Returns `{title, image, url, domain}` for OG-scraped URLs.
  - Returns `{type: 'youtube', video_id, embed_url}` for YouTube URLs (uses URL-pattern detection, not API calls).

### Sharer (`utils/sharer.php`)

- Social-share URL builders for: Facebook, Twitter/X, WhatsApp, LinkedIn, Reddit, Telegram, Email.
- Used by share buttons on post singles and timeline statuses.

- **Gotchas**:
  - YouTube embed detection is regex-based (matches `youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/shorts/...`). Other video providers (Vimeo, Twitch) are not detected.
  - OG scraping is server-side, on first encounter, then cached in the status's `details.link_preview`. No re-scrape on read.

---

## Auth Utilities (Social Login + 2FA)

- **Path**: `utils/auth-utils.php`, `controllers/frontend/auth/`
- **Purpose**: Social login (Google/Facebook/Apple OAuth), 2FA, registration flow steps (verification email, welcome step, custom redirect).

- **Social login providers** (verified from `controllers/frontend/auth/`):

  | Provider | OAuth flow | Controller |
  |---|---|---|
  | Google | OAuth 2.0 + ID-token verification via Google JWKs | `google-controller.php` |

  Only Google is implemented in the theme today (no Facebook or Apple controller exists). Settings live under `settings.auth.google.*` (`enabled`, `client_id`, `client_secret`); login endpoint is `?vx=1&action=auth.google.login`.

- **2FA**:
  - TOTP-based (Google Authenticator / Authy compatible).
  - Per-user opt-in via user profile settings.
  - Recovery codes generated at enablement.

- **Registration flow steps** (configurable):
  - Email verification (require clicking emailed link before account is activated).
  - Welcome step (intermediate page after registration).
  - Custom redirect (where to send user after successful registration).

- **API surface**: registration controllers under `controllers/frontend/auth/`. The login form is rendered by `ts-login` widget.

- **Gotchas**:
  - Social-login providers require HTTPS callback URLs. Local dev requires SSL (Valet `secure` handles this).
  - 2FA recovery codes are single-use. Once used, they're invalidated — make sure users save them at enablement time.

---

## Print Templates / QR Codes

- **Path**: `widgets/print-template.php`, `widgets/qr-tag-handler.php`
- **Purpose**: Two widget-driven outputs.

### Print Templates (`ts-print-template`)

- Renders any Voxel template inline.
- Common uses: order invoices, ticket PDFs, packing slips.
- Settings: `ts_template_id` (which template to render). The template is rendered with the CURRENT post/order/user context, so the same template can render different data depending on where it's embedded.

### QR Codes (`ts-qr-tag-handler`)

- Generates a QR code on the fly for any data source.
- Common uses: ticket check-in QR, table QR for restaurants, profile-share QR.
- Data source: configurable via dynamic tags (e.g. `@post(:url)` to encode the post URL).
- Rendering: SVG, no external library required.

- **Gotchas**:
  - `ts-print-template` rendering happens at REQUEST time (no precaching). For complex templates this can be slow on page load.
  - QR code data is encoded VERBATIM. Long URLs make dense QR codes that may not scan well — consider URL shortener.

---

## Cross-reference — other feature files in this cluster

| File | Covers | When to read |
|---|---|---|
| [`voxel-timeline.md`](voxel-timeline.md) | Timeline, reviews, comments, follows, mentions, direct messages, notifications | The timeline widgets (`ts-timeline`, `ts-user-bar`, etc.) are LISTED in this file's widget catalog, but their CONFIG and behavior is documented in detail there |
| [`voxel-commerce.md`](voxel-commerce.md) | Products, cart, orders, bookings, memberships, paid listings, claims, promotions, payments | The commerce widgets (`ts-product-form`, `ts-cart-summary`, `ts-orders`, etc.) are LISTED in this file's widget catalog, but their CONFIG and behavior is documented in detail there. Roles bind to membership plans documented there |
| [`voxel-search.md`](voxel-search.md) | Search filters, sort clauses, index table, maps + geocoding, recurring dates + work hours | The search widgets (`ts-search-form`, `ts-post-feed`, `ts-map`, `ts-quick-search`) are LISTED in this file's widget catalog, but their CONFIG and the filter/sort catalog is documented in detail there |

For dynamic-tag syntax of any group / modifier / visibility rule mentioned here, see [`voxel-tags.md`](voxel-tags.md) (the canonical dynamic-data reference).
