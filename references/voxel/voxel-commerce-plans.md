# Voxel Commerce: Bookings, Memberships, Listings, And Claims

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
