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

## Product Types (the umbrella system)

- **Path**: `product-types/`, `controllers/ecommerce/`, `modules/ecommerce/`
- **Purpose**: A pluggable framework that lets a CPT carry a `product-field` whose product-type configures cart behavior, pricing, variations, addons, shipping, and fulfillment. Supports one-time + subscription billing, vendor multi-tenancy via Stripe Connect, guest carts, direct (single-product Buy Now) carts, multi-vendor checkout splits into child orders, refunds.

- **Data shape**:
  - `{prefix}vx_orders` — columns: `id`, `customer_id`, `vendor_id`, `status`, `shipping_status`, `payment_method` (e.g. `stripe_payment`, `paddle_payment`, `paypal_payment`, `offline_payment`, `zero_amount_payment`), `transaction_id`, `details` (JSON: addresses, totals, promo, customer notes), `parent_id` (multi-vendor split), `testmode` (boolean).
  - `{prefix}vx_order_items` — `order_id`, `post_id` (the product post), `product_type` (e.g. `regular`, `booking`, `variable`), `field_key` (which product-field on the source CPT), `details` (JSON: quantity, variation, addons, data-inputs, slot for bookings, usage tracking for listing packages).

- **Sub-system map**:

  | Sub-system | Path | Role |
  |---|---|---|
  | Cart | `product-types/cart/` | Cart aggregator, 3 flavors |
  | Cart Items | `product-types/cart-items/` | Per-item-type cart row |
  | Order Items | `product-types/order-items/` | Persisted variant of a cart item |
  | Orders | `product-types/orders/` | Order entity + status machine + admin list table |
  | Product Fields | `product-types/product-fields/` | Pricing/stock/variations/addons/shipping config |
  | Variations | `product-types/variations/` | Per-variation price/stock |
  | Product Attributes | `product-types/product-attributes/` | Color / size / etc — drives variation matrix |
  | Product Addons | `product-types/product-addons/` | Optional checkout extras |
  | Data Inputs | `product-types/data-inputs/` | Customer-fill fields at checkout |
  | Promotions | `product-types/promotions/` | Paid-listing promotion packages |
  | Shipping | `product-types/shipping/` | Zones + classes + rates |
  | Payment Methods | `product-types/payment-methods/` | Offline / zero-amount / Stripe / Paddle / PayPal |
  | Payment Services | `product-types/payment-services/` | Abstract payment-service base |

- **Cart flavors**:

  | Class | Use case | State |
  |---|---|---|
  | `Customer_Cart` | Logged-in user accumulating items across visits | User meta `voxel:cart` |
  | `Guest_Cart` | Anonymous user (cart lost on session expiry) | PHP session / cookie |
  | `Direct_Cart` | Single-product Buy Now (skip cart, go to checkout) | Ephemeral (lives only for the checkout request) |

  All three inherit from `Base_Cart` and share trait-defined item operations.

- **Cart-Item types** (`product-types/cart-items/`):
  - `Cart_Item_Regular` — fixed-price product (with optional variations/addons).
  - `Cart_Item_Booking` — slot/calendar booking (carries `start`/`end`/`slot`).
  - `Cart_Item_Variable` — explicit variation matrix (carries `variation_key`).

  Factory: `Cart_Item::create( $product_post, $args )` returns the right subclass based on the product-field config.

- **Order-Item types** (`product-types/order-items/`): persisted equivalents — `Order_Item_Regular`, `Order_Item_Booking`, `Order_Item_Variable`. Created from cart items at checkout. Once persisted they decouple from the cart (cart can be cleared without affecting the order).

- **Product Field catalog** (`product-types/product-fields/`):

  | Field | Role |
  |---|---|
  | `base-price-field` | Single price entry |
  | `custom-prices-field` | Multi-tier pricing matrix |
  | `currency-field` | Per-product currency override |
  | `stock-field` | Inventory tracking (count + low-stock threshold) |
  | `booking-field` | Booking calendar + slot config (see Bookings) |
  | `subscription-interval-field` | Recurring billing config (interval + interval_count + trial) |
  | `variations-field` | Variation matrix (uses `product-attributes`) |
  | `addons-field` | Optional checkout extras (uses `product-addons`) |
  | `deliverables-field` | Digital file delivery on order completion |
  | `shipping-field` | Per-product shipping override |
  | `base-product-field` | Internal: the root product-field that wraps all the above |

- **Variations** (`product-types/variations/`): each variation in the matrix can override `variation-base-price-field` and `variation-stock-field`.

- **Product Attributes** (`product-types/product-attributes/`):
  - `custom-attribute` — admin-defined options (free-text values).
  - `predefined-attribute` — color/size/etc with site-wide standardized options.

- **Product Addons** (`product-types/product-addons/`): optional checkout extras the customer can add per cart item.

  | Addon type | UI |
  |---|---|
  | `numeric-addon` | Quantity stepper |
  | `switcher-addon` | Toggle (boolean) |
  | `select-addon` | Single-select dropdown |
  | `multiselect-addon` | Multi-select |
  | `custom-select-addon` | Single-select with admin-configured custom labels/prices |
  | `custom-multiselect-addon` | Multi-select with admin-configured custom labels/prices |

- **Data Inputs at checkout** (`product-types/data-inputs/`): per-cart-item fields the customer FILLS at checkout (e.g. "Engraving text" for an engraved product, "Number of guests" for a booking, "Preferred delivery date").

  Available input types: `text`, `textarea`, `number`, `email`, `phone`, `url`, `select`, `multiselect`, `switcher`, `date`.

  Stored on the order item's `details.data_inputs` JSON.

- **Order Statuses** (12-value enum on `vx_orders.status`):

  | Status | Meaning |
  |---|---|
  | `pending_payment` | Order created, awaiting payment confirmation |
  | `pending_approval` | Payment received, awaiting vendor approval (vendor-must-approve flow) |
  | `completed` | Successfully paid + approved |
  | `canceled` | Canceled by customer or vendor |
  | `refunded` | Refunded (partial or full) |
  | `sub_active` | Subscription active (recurring) |
  | `sub_trialing` | Subscription in trial period |
  | `sub_incomplete` | Subscription created but initial payment failed |
  | `sub_incomplete_expired` | `sub_incomplete` exceeded retry window |
  | `sub_past_due` | Subscription payment failed; retrying |
  | `sub_canceled` | Subscription canceled (will not renew) |
  | `sub_unpaid` | Subscription past_due window exhausted |
  | `sub_paused` | Subscription paused (Stripe-managed pause) |

  Order status transitions are driven by the payment method's `->sync()` callback (which reads the latest state from Stripe/Paddle/PayPal and updates the local row).

- **Shipping** (`product-types/shipping/`):

  Two top-level methods, configured globally in Voxel → Settings → Shipping:

  | Method | Behavior |
  |---|---|
  | `platform_rates` | Cart-wide single zone — one rate matrix per shipping zone applies to the whole order |
  | `vendor_rates` | Per-vendor zones — each vendor has their own rate matrix; multi-vendor cart sums per-vendor shipping |

  Sub-classes: `Shipping_Zone` (geographic zone), `Shipping_Class` (per-product class for differential rates), `Vendor_Shipping_Zone` (per-vendor variant), `Rates/` (flat / calculated / free-over-N), `Vendor_Rates/`.

- **Payment Methods** (`product-types/payment-methods/`): the abstract `Base_Payment_Method` + concrete implementations:

  | Method | Path | Notes |
  |---|---|---|
  | `Offline_Payment` | `product-types/payment-methods/offline-payment.php` | Mark order as paid manually (e.g. cash on delivery) |
  | `Zero_Amount_Payment` | `product-types/payment-methods/zero-amount-payment.php` | Free orders — skip payment gateway |
  | `Zero_Amount_Subscription` | `product-types/payment-methods/zero-amount-subscription.php` | Free trial subscriptions |
  | Stripe | `modules/stripe-payments/payment-methods/stripe-payment-method.php` | Full Stripe Connect support |
  | Paddle | `modules/paddle-payments/payment-methods/` | Alternative gateway |
  | PayPal | `modules/paypal-payments/payment-methods/` | Conditional loader |

  Each implements `->process_checkout()`, `->sync()` (reconcile with gateway), `->refund()`.

- **Payment Services** (`product-types/payment-services/`): `Base_Payment_Service` — higher-level abstraction for payment processors. A payment-service wraps webhook handling, customer onboarding, and per-vendor split logic. Stripe-Connect has its own `Stripe_Payment_Service`.

- **Public API**:
  - `\Voxel\Product_Types\Orders\Order::get( $id )` / `::query( $args )` / `::create_from_cart( $cart, $args )`.
  - `->get_items()` — array of `Order_Item_*` instances.
  - `->get_payment_method()` — payment-method instance.
  - `->should_handle_shipping()` — boolean (false for fully digital orders).
  - `->get_shipping_rate()` / `->get_shipping_zone()` — chosen rate/zone.
  - Totals: `->get_total()`, `->get_subtotal()`, `->get_tax_amount()`, `->get_discount_amount()`, `->get_shipping_amount()`.
  - `->set_status( $key )` / `->save()`.
  - `->sync()` — reconciles status with gateway (Stripe webhook handler invokes this).
  - `->get_actions( $user )` — returns the action buttons for the given viewer (vendor / customer / admin).
  - `\Voxel\Order_Item::query( $args )` — for analytics queries against persisted order items (e.g. "top-selling products this month").

- **Voxel-native widgets**:
  - `ts-cart-summary` — mini-cart drawer or sidebar widget.
  - `ts-product-form` — "Add to cart" / "Reserve" / "Buy now" form on a product single template. Renders variation selector, addon picker, data-input fields, quantity stepper.
  - `ts-product-price` — formatted price + interval (e.g. "$29 / month").
  - `ts-booking-calendar` — visual day/slot picker (paired with `booking-field`).
  - `ts-orders` — vendor or customer order list (filterable by status, date range).
  - `ts-print-template` — render an invoice template inline.

- **Dynamic tags**: `@order(...)`, `@orders/booking(...)`, `@orders/promotion(...)` — see `voxel-tags.md`. Key paths:
  - `@order(:id, :created_at, :link)`
  - `@order(pricing.{total, subtotal, tax, discount, shipping, currency, formatted})`
  - `@order(status.{key, label})`
  - `@order(shipping.{status.{key, label}, tracking_link, shipping_rate.{label, delivery_estimate}, address.{first_name, last_name, country.{key, label}, state.{key, label}, line, zip, formatted}})`
  - `@order(customer_notes)`

- **Settings surface**:
  - Voxel → Settings → Products (currency, tax behavior, refund window).
  - Voxel → Settings → Payments (per-method enable + config).
  - Voxel → Settings → Shipping (zones, classes, rates, method choice platform vs vendor).
  - Per CPT: blueprint editor → `product-field` sub-config.
  - Per user (vendor): profile → vendor settings (Stripe onboarding, shipping zones).

- **Triggers / events**:
  - `events/products/orders/` — per-method status events.
  - Filters: `voxel/order/customer_details`, `voxel/order/actions`, `voxel/order/success_redirect`, `voxel/ecommerce/order_statuses`, `voxel/subscriptions/zero_amount/skip_checkout`, `voxel/payments/zero_amount/skip_checkout`.
  - Actions: `voxel/product-types/orders/order:updated`, `voxel/product-types/orders/order:before_delete`.

- **Common usage patterns**:
  - Vendor dashboard "Orders" tab renders `ts-orders` filtered by `vendor_id=current_user`.
  - Customer dashboard "Orders" tab renders `ts-orders` filtered by `customer_id=current_user`.
  - Multi-vendor marketplace: one customer cart with items from multiple vendors → at checkout, splits into ONE parent order + N child orders (one per vendor).

- **Gotchas**:
  - `pending_approval` is distinct from `pending_payment`. `pending_payment` waits on gateway confirmation; `pending_approval` waits on vendor manual approval AFTER payment is received. Use the right one for the right flow.
  - `parent_id` enables multi-vendor split. Parent order has `vendor_id=NULL`; child orders have `parent_id=parent.id` and `vendor_id=<vendor>`. Status transitions cascade parent → children.
  - Test mode (`testmode=1`) uses separate plan storage (`voxel:test_plan` user meta) and Stripe test keys. Live and test orders/plans never mix in queries.
  - The `details` JSON on `vx_orders` is the source of truth for customer address, totals, applied promo, customer notes. Do NOT recompute totals from `vx_order_items` — they may have been overridden by promo codes.
  - When refunding via the gateway, the local row updates on the NEXT `->sync()` call (webhook). Do not assume immediate consistency.

---

## Bookings

- **Path**: `product-types/product-fields/booking-field.php`, `product-types/cart-items/cart-item-booking.php`, `product-types/order-items/order-item-booking.php`, `events/bookings/`
- **Purpose**: Reservation-style products — slot per day or per timeslot, recurring availability, customer can reschedule/cancel, vendor can confirm/reschedule/cancel.

- **Booking field config** (per CPT, on a `product-field` with type `booking`):

  | Setting | Notes |
  |---|---|
  | `calendar_source` | Which `recurring-date-field` on the CPT provides availability |
  | `slot_duration` | Minutes per slot (for time-based booking) |
  | `lead_time` | Minimum hours between booking and slot start |
  | `max_advance_booking` | Max days into the future bookable |
  | `deposit` | Optional partial payment at booking time |
  | `mode` | `date` (full-day) or `timeslot` (sub-day slots) |

- **Cart item shape**: `Cart_Item_Booking` carries `start`, `end`, `slot`, plus customer-filled `data_inputs`.

- **Voxel-native widgets**: `ts-booking-calendar` — visual day/slot picker, paired with `booking-field`. Reads availability from the configured calendar-source field. Drives the booking form on the product single.

- **Dynamic tags**: `@orders/booking(...)` — see `voxel-tags.md`. Properties include slot start/end, calendar source, reschedule URL.

- **Settings surface**: per-CPT product-field → booking config (calendar source field, slot duration, lead time, max advance booking, deposit).

- **Triggers / events** (under `events/bookings/`):
  - `Booking_Placed_Event` — customer places a booking.
  - `Booking_Confirmed_Event` — vendor confirms (or auto-confirmed by config).
  - `Booking_Canceled_By_Customer_Event` / `Booking_Canceled_By_Vendor_Event`.
  - `Booking_Rescheduled_By_Customer_Event` / `Booking_Rescheduled_By_Vendor_Event`.

- **Common usage patterns**:
  - Restaurant table reservation: timeslot mode, 90-minute slots, 24h lead time.
  - Tour booking: date mode, full-day, 7-day lead time, deposit = 30%.
  - Hotel room: date range mode (`mode=date`, accept start + end).

- **Gotchas**:
  - Recurring availability uses `utils/recurring-date-utils.php`. The `availability-filter` (in search) filters posts by AT-LEAST-ONE-FREE-SLOT in the searched date range. See `voxel-search.md`.
  - Customer-initiated reschedule transitions through `Booking_Rescheduled_By_Customer_Event`; vendor reschedule fires the other event class. Both update the booking's slot but do NOT refund — handle refunds separately.
  - Deposits are partial payments; the remainder is collected at vendor confirmation. The order has TWO transactions if a deposit is used.

---

## Paid Memberships (Subscription Plans)

- **Path**: `modules/paid-memberships/`
- **Purpose**: Subscription / recurring billing for member access (role-bound). Users pick a `Plan` (one-time or recurring `Price`); Stripe handles billing; plan grants gated capabilities + custom limits. Test-mode plans stored separately so dev work doesn't break live data.

- **The Plan / Price / Membership trifecta**:

  | Entity | Path | Role |
  |---|---|---|
  | `Plan` | `modules/paid-memberships/plan.php` | Admin-defined offering. Carries: `key`, `label`, `role_binding` (the role granted on subscription), `prices[]` (one or more price tiers), `post_type_limits` (per-CPT post quotas) |
  | `Price` | `modules/paid-memberships/price.php` | A specific price tier on a plan. Carries: `currency`, `amount`, `interval` (`day`/`week`/`month`/`year`), `interval_count`, `billing_cycle_anchor` (specific day/date for billing), `trial_period_days` |
  | `Membership` | `modules/paid-memberships/membership/Base_Membership` | Per-user runtime state of an active subscription. Carries: type (`default`/`order`), selected plan, active plan, current period start/end, parent order |

- **Role↔plan binding**: a plan binds to ONE role. On subscription activation, the user is added to that role; on cancellation/expiry, they are removed.

- **Test-mode storage**: live plan stored in user meta `voxel:plan`; test plan stored in `voxel:test_plan`. The same user can have both simultaneously (live for real customers, test for development).

- **Billing cycle anchor**: Stripe concept — fixes the billing date so all subscribers bill on the same day (e.g. 1st of month). Voxel exposes this as a `Price` config.

- **Public API**:
  - `\Voxel\Modules\Paid_Memberships\update_user_plan( $user_id, $details, $is_test_mode = false )` — write user's plan state (called by the Stripe webhook).
  - `\Voxel\User::get_membership()` — returns the active `Membership` instance for current site (live or test depending on context).
  - `Membership::get_type()` — `default` (no active subscription) or `order` (subscription-driven).
  - `Membership::get_selected_plan()` / `->get_active_plan()`.
  - `Membership::get_amount()` / `->get_currency()` / `->get_interval()` / `->get_frequency()`.
  - `Membership::get_current_period_start()` / `->get_current_period_end()`.
  - `Membership::get_order()` — the parent order driving this subscription.

- **Voxel-native widgets**: dedicated pricing widget(s) in `modules/paid-memberships/widgets/`.

- **Dynamic tags**: `@user/membership(...)` — see `voxel-tags.md`. Properties: `plan.{key, label, description}`, `pricing.{formatted, amount, currency, period, status, start_date, current_period_start, current_period_end}`.

- **Settings surface**:
  - Voxel → Settings → Paid Memberships (module toggle, default test mode).
  - Per role: registration tab → "Plans enabled" + pricing page binding.
  - Per plan: admin-defined under Voxel → Plans.

- **Triggers / events**:
  - Action: `voxel/paid_memberships/updated_user_plan`.
  - Events: `User_Registered_Event`, `User_Data_Export_Requested_Event` (under `events/membership/`).
  - Each plan also dispatches subscription-status events via the underlying order (Stripe sub_active, sub_canceled, etc).

- **Common usage patterns**:
  - SaaS-style site: free role + paid role; free role gates basic features, paid role unlocks premium.
  - Membership site: multiple tiers (Silver/Gold/Platinum) each binding to a different role; per-tier post quotas via `post_type_limits`.

- **Gotchas**:
  - `Role::has_plans_enabled()` gates plan offering. If false, the registration form does NOT show the plan picker.
  - `settings.addons.paid_memberships.enabled` is the global module toggle. Disabling does NOT cancel active subscriptions — it just hides the UI.
  - On plan downgrade, posts in excess of the new plan's CPT quota are NOT auto-deleted. The next post-creation attempt is blocked, but existing posts remain.

---

## Paid Listings (per-CPT plans + packages + quotas)

- **Path**: `modules/paid-listings/`
- **Purpose**: Per-CPT submission plans/packages — gate post creation behind a paid plan; enforce per-plan post quotas across CPTs; convert posts back to drafts on re-listing; track usage history; "claim listing" extension piggybacks on this.

- **Sub-systems**:

  | Entity | Path | Role |
  |---|---|---|
  | `Listing_Plan` | `modules/paid-listings/listing-plan.php` | Admin-defined plan: post-type allowlist (which CPTs this plan can post to), post limit per plan |
  | `Listing_Package` | `modules/paid-listings/listing-package.php` | A purchased order item conferring N usable slots. Usage tracked in the order item's `details.meta."voxel:listing_plan_usage"` JSON |

- **Public API** (from `modules/paid-listings/paid-listings.php`):
  - `has_plans_for_post_type( $cpt )` — boolean: any plan covers this CPT?
  - `get_plans_for_post_type( $cpt )` — array of `Listing_Plan` instances.
  - `get_pricing_page_link( $args )` — URL of the configured pricing page with optional pre-selected plan args.
  - `get_order_package( $order )` — `Listing_Package` instance for a given order.
  - `get_used_posts_from_limits( $limits )` — count of currently published posts against the per-CPT limits.
  - `get_upgrade_post_allocation( $current, $target )` — when upgrading a plan, how many slots from the old plan carry over to the new plan. CRITICAL for upgrade flows: returns the number of slots that survive the transition.
  - `get_available_packages( $user, $cpt )` — packages the user owns that can post to the given CPT.
  - `get_assigned_package( $post )` — the package currently allocated to a post.
  - `get_or_create_draft( $package, $cpt, $author )` — creates a blank-draft post (or reuses an existing `_is_blank_draft`-tagged post) so the user can fill the submission form. Reuses to avoid blank-draft accumulation.
  - `prepare_post_for_relisting( $package, $post )` — converts a published post back to draft + assigns a fresh slot from the package. Used when a listing expires and user wants to re-publish.
  - `user_has_bought_plan( $user, $plan )` — boolean.
  - `get_usage_summary_for_user( $user )` — `{plan_key: {used, limit}}` map for dashboard rendering.

- **Settings schema** (`get_settings_schema()`):

  | Setting | Notes |
  |---|---|
  | `templates.pricing` | Page ID of the pricing page (where users browse plans) |
  | `auto_select_plan` | If true, a single-plan CPT auto-selects without prompting |
  | `claims.{enabled, proof_of_ownership, approval}` | Claim listings config (see below) |
  | `promotions.{enabled, packages[], payments.mode, order_approval}` | Promotions config (see below) |

- **Per-post meta**: `voxel:listing_plan` JSON stores `{plan: <plan_key>, package: <order_id>, use_slot_on_publish: bool, time: <timestamp>}`. This links a post to the plan that allocated it.

- **`_is_blank_draft` reuse pattern**: When a user clicks "Submit listing", Voxel auto-creates a blank draft so the submission form has a real post to attach files/repeaters to. If the user abandons mid-flow, that draft sits with `_is_blank_draft=1` meta. Next time the user submits, `get_or_create_draft()` finds and reuses that draft instead of creating a new one. Prevents blank-draft accumulation.

- **Slot allocation across upgrades**: when a user buys a new plan while having an active old plan, `get_upgrade_post_allocation( $current, $target )` decides how many published posts can stay published. If the target plan has fewer slots than currently used, the excess goes to... NOT auto-unpublish. Existing posts stay published; new posts are blocked until the user deletes or unpublishes. See Gotchas.

- **Voxel-native widgets**: `modules/paid-listings/widgets/` — plan picker / package selector. `ts-create-post` becomes plan-gated when a CPT has paid plans configured.

- **Dynamic tags**: surfaces via `@order(...)`'s `meta.voxel:listing_plan` shape and via `@post().meta('voxel:listing_plan')`.

- **Settings surface**: Voxel → Settings → Paid Listings.

- **Gotchas**:
  - `_is_blank_draft` reuse is per-user, per-CPT. If a user has multiple abandoned drafts across CPTs, each CPT's submission flow reuses ITS own draft.
  - Slot accounting is denormalized into the order item's `details.meta` JSON. Don't recompute by counting posts — the meta is the source of truth (handles edge cases like expired posts that still consumed a slot).
  - When a plan is admin-deleted, posts tagged with that plan_key in `voxel:listing_plan` become orphans. `get_assigned_package()` returns null; the post stays published but is no longer plan-bound.
  - `prepare_post_for_relisting()` converts published → draft. The post URL stays the same; SEO impact: backlinks now 404 (or redirect to draft preview for admins) until republished.

---

## Claim Listings (extension of Paid Listings)

- **Path**: `modules/claim-listings/`
- **Purpose**: Users can claim ownership of an admin-pre-seeded listing (e.g. a business profile pre-populated by the platform). Optionally uploads proof-of-ownership document; on approval, post author transfers + post is verified.

- **Public API** (from `modules/claim-listings/claim-listings.php`):
  - `is_claimable( $post )` — gates:
    - Claims enabled globally.
    - Post not yet verified (`voxel:verified` meta is not 1).
    - Post type has paid plans available (claim flow piggybacks on Paid Listings).
  - `get_proof_of_ownership_field()` — returns a `File_Field` configured via filters:
    - `voxel/claim_requests/proof_of_ownership/allowed_file_types`
    - `voxel/claim_requests/proof_of_ownership/max_file_size`
    - `voxel/claim_requests/proof_of_ownership/max_file_count`
    - `private_upload=true` (proofs are excluded from the media library — they're stored in a per-claim subdirectory).
  - `get_product()` — auto-creates a `_vx_catalog` post that acts as the product for the claim-request order (so the claim flow uses the standard checkout pipeline).

- **Settings surface**: Voxel → Settings → Paid Listings → Claims:

  | Setting | Values |
  |---|---|
  | Claims enabled | boolean toggle |
  | Proof of ownership | `required` / `optional` / `disabled` |
  | Approval mode | `automatic` (claim auto-approved on payment) / `manual` (admin must review) |

- **Common usage patterns**:
  - Directory site pre-populated with business listings; business owners can claim their listing for a small fee + ID proof.

- **Gotchas**:
  - Piggybacks on Paid Listings + Orders. Even for a free claim flow, the order machinery runs (with `Zero_Amount_Payment`).
  - After approval, the listing becomes the claimant's normal post (subject to the normal plan quota — so the claimant must also have a regular plan, or the listing will count against their next-purchased plan's quota).
  - Proof-of-ownership files use the `private_upload` flag — `File_Uploader` stores them outside the public uploads directory. Direct URL access is denied; admin moderation UI uses signed URLs.

---

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
