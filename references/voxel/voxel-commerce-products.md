# Voxel Commerce: Products, Cart, And Orders

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
