# Voxel Commerce — Products, Cart, Orders, Bookings, Memberships, Listings, Claims, Promotions, Payments

The full commerce surface of Voxel: product types, cart/checkout, orders + statuses, bookings, paid memberships, paid listings, claim listings, promotions, multi-vendor split (Stripe Connect), and the payment-method abstraction (Stripe / Paddle / PayPal / Offline). Stable in shape — the major tables (`vx_orders`, `vx_order_items`) and the order-status enum have not changed since the Stripe Connect rewrite.

Source theme: `sites/<site>/wp-content/themes/voxel/app/` (paths below are relative to `app/` unless noted).

## How to use this reference

Read this file when:
- Building or auditing a product single template, vendor dashboard, or customer order list.
- Configuring a CPT's `product-field` blueprint (regular / booking / variable product).
- Wiring `ts-product-form`, `ts-cart-summary`, `ts-orders`, `ts-booking-calendar`.
- Implementing checkout data-inputs (custom per-cart-item fields filled at checkout).
- Setting up multi-vendor Stripe Connect onboarding or commission split.
- Configuring Paid Memberships (subscription plans, role binding) or Paid Listings (per-CPT quotas, claims).
- Implementing Promotions (boosted listings) on top of Paid Listings.

For order-related dynamic tags (`@order`, `@orders/booking`, `@orders/promotion`) see `voxel-tags.md`. This file documents the *system* — tables, classes, sub-systems, status enums, events, gotchas.

For commerce-touching social surfaces (`customers_only` timeline visibility, follow-state gating) see `voxel-timeline.md`. For the `availability-filter` and product-related search filters see `voxel-search.md`. For paid-listing / claim / RFQ-style CPT setup (which is the canonical transactional shape behind every flow below) see [`cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md) §Recipe — transactional / private CPT. For gating admin-only fields (workflow `status`, internal notes) on commerce CPTs, see [`voxel-field-visibility.md`](voxel-field-visibility.md).

---

## Split Commerce Map

| Concern | Reference |
|---|---|
| Product types, cart, orders | `voxel-commerce-products.md` |
| Bookings, memberships, paid listings, claims | `voxel-commerce-plans.md` |
| Promotions, Stripe Connect/payments, Paddle, PayPal | `voxel-commerce-payments.md` |
