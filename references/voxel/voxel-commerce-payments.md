# Voxel Commerce: Promotions And Payment Providers

## Promotions (Featured / Boosted Listings)

- **Path**: `posts/post-promotions.php`, `product-types/promotions/promotion-package.php`, `events/promotions/`
- **Purpose**: Pay-to-promote a listing. Sets `voxel:promotion` post meta; while `status=active`, the post's `get_priority()` returns the promotion's priority value (overriding any organic priority), surfacing it ahead of organic results in any search that sorts by `priority-order`.

- **`voxel:promotion` meta shape** (per post):
  ```
  {
    status: 'active' | 'expired' | 'canceled',
    priority: <integer>,           // higher = ranked first
    package: <order_id>,           // the order that bought this promotion
    expires_at: <unix_timestamp>,
  }
  ```

- **Priority interplay with `priority-order` sort**:
  - `Post::get_priority()` returns the promotion's priority IF promotion status == `active`.
  - Otherwise returns the organic `voxel:priority` meta (manually set by admin).
  - The `priority-order` sort clause (`post-types/order-by/priority-order.php`) sorts by `get_priority()` DESC — so active promotions naturally win.
  - When promotion expires (cron job flips `status` to `expired`), the post falls back to its organic priority.

- **Voxel-native widgets**: in `modules/paid-listings/widgets/` — the promotion picker is part of the submission form when promotions are enabled.

- **Dynamic tags**: `@orders/promotion(...)` — see `voxel-tags.md`. Group at `dynamic-data/data-groups/orders/promotion-data-group.php`.

- **Settings surface**: Voxel → Settings → Paid Listings → Promotions:
  - Available packages: each has `price`, `duration_days`, `priority_value`, `post_type_allowlist`.
  - Payment mode: `instant` (charge on submit) / `approval` (admin approves before charge).

- **Triggers / events** (under `events/promotions/`):
  - `Promotion_Activated_Event` — promotion begins (post becomes boosted).
  - `Promotion_Canceled_Event` — promotion ends (revert to organic priority).

- **Gotchas**:
  - Promotion expiration is cron-driven (not lazy on read). If cron is broken, expired promotions stay `active` in the meta and continue boosting until cron catches up. See `voxel-platform.md` → Async Jobs & Cron.
  - Multiple active promotions on one post: only the latest takes effect; older active promotions are flipped to `canceled` by the activation flow.
  - `priority-order` is a multi-key sort: `(get_priority() DESC, date_modified DESC)`. Ties break by recency.

---

## Stripe Connect (Multi-Vendor Payments)

- **Path**: `modules/stripe-connect/`
- **Purpose**: Vendor onboarding (Standard / Express / Custom Connect accounts), per-vendor payouts, vendor commission, vendor-side dashboards (stats, payouts, transfers).

- **Sub-systems**:
  - `Vendor_Stats` — per-vendor aggregate metrics (revenue, orders, refunds) for dashboard widgets.
  - Payment-method bindings under `payment-methods/` (Stripe Connect-aware variant of the standard Stripe payment method).
  - Dedicated widgets + templates for vendor onboarding wizard, payouts page, transfers page.

- **Public API**: extends `\Voxel\User` via `Vendor_Trait`:
  - `->is_vendor()` — boolean.
  - `->get_vendor_shipping_zone( $key )` — per-zone shipping config for this vendor.
  - `->has_bought_product_from_vendor( $vendor_id )` — used for `customers_only` timeline visibility scoped to a specific vendor's customers.
  - Methods on `Vendor_Stats` for analytics.

- **Multi-vendor commission**: configured at Settings → Stripe Connect:
  - Commission can be a flat amount or a percentage of each child order's subtotal.
  - Commission is deducted from the vendor's payout (collected as `application_fee` on the Stripe Connect transfer).

- **Parent/child order split**: as documented above, a multi-vendor cart at checkout creates ONE parent order (no vendor, `vendor_id=NULL`) and N child orders (one per vendor, `parent_id=parent.id`). Stripe's payment intent has multiple `transfer_data` instructions, one per Connect account.

- **Settings surface**: Voxel → Settings → Stripe Connect:
  - Connect mode: Standard / Express / Custom.
  - Commission config.
  - Vendor onboarding URL.

- **Triggers / events**:
  - Filter: `voxel/stripe_connect/enable_onboarding_for_admins` (default: admins are excluded from vendor onboarding flow).

- **Common usage patterns**:
  - Marketplace site (Etsy-style): every shop owner is a vendor with Connect Express account; platform takes 10% commission.
  - Restaurant aggregator: each restaurant is a vendor; orders split into one parent (customer's overall order) and one child per restaurant.

- **Gotchas**:
  - Vendor split orders produce `parent_id`-linked child orders (one child per vendor). When querying for analytics, you usually want to query CHILDREN (per-vendor revenue) not the parent (which has no vendor and no items of its own).
  - `customers_only` timeline visibility uses Stripe-tracked purchase history. If a customer paid via offline payment (not Stripe), their purchase counts via `Customer_Trait::has_bought_product_from_platform()` instead.
  - Vendor onboarding state lives on Stripe; Voxel polls Stripe to refresh `is_vendor()` status. If Stripe is unreachable, status reads from cache (may be stale).

---

## Stripe Payments (the concrete payment method)

- **Path**: `modules/stripe-payments/`
- **Purpose**: Concrete Stripe payment-method implementation (one-time payments + subscriptions). Provides `Stripe_Payment_Service`, `Stripe_Client` wrapper, country/tax code lookup tables, asset bundle for the Stripe.js drop-in.

- **Sub-systems**:
  - `payment-methods/` — `Stripe_Payment_Method` (extends `Base_Payment_Method`).
  - `stripe-client.php` — wraps the Stripe SDK.
  - `stripe-payment-service.php` — webhook handler, payment intent creation.
  - `country-codes.php` / `tax-codes.php` — lookup tables for Stripe's tax-collection feature.
  - `controllers/` — REST + webhook endpoints.
  - `templates/` — checkout UI templates.

- **Settings surface**: Voxel → Settings → Stripe:
  - Publishable key + secret key (live + test).
  - Webhook secret.
  - Tax behavior (`exclusive` / `inclusive`).
  - Test mode toggle.

- **Common usage patterns**: nearly every Voxel commerce site uses Stripe Payments. Paddle / PayPal are alternatives but Stripe is the default.

---

## Paddle Payments

- **Path**: `modules/paddle-payments/`
- **Purpose**: Alternative payment processor (Paddle.com). Same shape as Stripe Payments — registers a `Base_Payment_Method` subclass + service + controllers.

- **API surface**: identical pattern to Stripe — `Paddle_Payment_Method`, `Paddle_Payment_Service`, webhook handler. Configuration: publishable key, vendor ID, webhook secret in Voxel → Settings → Paddle.

- **Gotchas**: only loaded if module enabled. Paddle is a merchant-of-record (handles tax, EU VAT, etc.) — different commission model than Stripe.

---

## PayPal Payments

- **Path**: `modules/paypal-payments/`
- **Purpose**: PayPal payment-method integration. Loaded conditionally.

- **API surface**: `PayPal_Payment_Method`, `PayPal_Payment_Service`, webhook handler. Configuration: client ID + secret in Voxel → Settings → PayPal.

- **Gotchas**: PayPal does NOT support Stripe Connect-style multi-vendor split natively. Multi-vendor PayPal orders consolidate to one merchant — vendor payout has to be done manually outside Voxel.

---

## Cross-reference — other feature files in this cluster

| File | Covers | When to read |
|---|---|---|
| [`voxel-timeline.md`](voxel-timeline.md) | Timeline, reviews, comments, follows, mentions, direct messages, notifications | `customers_only` timeline visibility uses `Customer_Trait::has_bought_product()` documented in commerce flows. Order-event-driven notifications cross-reference both files |
| [`voxel-search.md`](voxel-search.md) | Search filters, sort clauses, index table, maps + geocoding, recurring dates + work hours | Booking-related search uses `availability-filter`; promoted listings rely on `priority-order` sort. The `nearby-order` sort drives vendor-finder pages |
| [`voxel-platform.md`](voxel-platform.md) | Post types, taxonomies, roles + registration, collections, full Voxel widget catalog, post relations, verification, async jobs, auth, print templates | Roles bind to membership plans (see Paid Memberships → Role↔plan binding). Async-jobs cover promotion-expiration cron and subscription-renewal cron. Print templates render order invoices |
| [`cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md) | 7-phase CPT creation + transactional / private CPT recipe | Paid-listing / claim / RFQ-style CPTs (the canonical shape behind most commerce flows below) follow the transactional recipe — `messages.enabled: true`, moderation-gated submissions, sitemap-exclude, noindex singles |
| [`voxel-field-visibility.md`](voxel-field-visibility.md) | All 30 visibility rule types | Gating admin-only commerce fields (workflow `status`, internal notes, vendor-only blocks) on the buyer-facing submission form |

For dynamic-tag syntax of any group mentioned here (`@order`, `@orders/booking`, `@orders/promotion`, `@user/membership`), see `voxel-tags.md`.
