# Voxel Platform — Post Types, Taxonomies, Roles, Collections, Widget Catalog, Relations, Verification, Async, Auth, Misc

The foundational platform surface of Voxel: the post-type / taxonomy / role abstractions every other feature builds on, the full catalog of `ts-*` / `vx-*` Elementor widgets, post relations, verification, the file uploader, statistics, async jobs, privacy, nav menus, the templates library, text-formatter / link-previewer / sharer utilities, auth (social + 2FA), and print/QR templates.

Source theme: `sites/<site>/wp-content/themes/voxel/app/` (paths below are relative to `app/` unless noted).

## How to use this reference

Read this file when:
- Building or auditing any Voxel template — you need the full `ts-*` / `vx-*` widget catalog.
- Working with `\Voxel\Post` / `\Voxel\Post_Type` / `\Voxel\Taxonomy` / `\Voxel\User` PHP APIs.
- Setting up Roles + Registration fields (gating which profile fields users fill at signup).
- Implementing Collections (user-saved post lists / wishlists).
- Wiring Post Relations (cross-CPT linking with optional approval flow).
- Implementing Verification badges (`voxel:verified` meta + visibility rules).
- Configuring private File Uploads (e.g. claim-listing proofs).
- Enabling per-post visit Statistics + `ts-visits-chart`.
- Adding async background jobs or scheduled cron tasks.
- Wiring social-login (Google/Facebook/Apple OAuth) or 2FA.
- Adding QR-code or print-template (invoice) outputs.

For dynamic-tag syntax (`@post`, `@user`, `@term`, etc.) see `voxel-tags.md`. This file documents the *system* — APIs, settings, widget catalog, events, gotchas.

For commerce-touching widgets and APIs see `voxel-commerce.md`. For social/timeline widgets and APIs see `voxel-timeline.md`. For search-related widgets see `voxel-search.md`.

---

## Post Types (the deep contract)

- **Path**: `post-types/`, `post.php`, `post-type.php`
- **Purpose**: The core abstraction for any content type managed by Voxel. Wraps WordPress CPTs with a config-driven blueprint (fields, filters, search orders, templates, schema, reviews, timeline, revisions, index table). Every Voxel listing/profile/post type is a `\Voxel\Post_Type` with a sub-system stack.

- **Sub-system stack** (accessible via `\Voxel\Post_Type` instance properties):

  | Property | Class | Role |
  |---|---|---|
  | `->repository` | `Post_Type_Repository` | Indexable-statuses, status visibility, query helpers |
  | `->schema` | `Post_Type_Schema` | JSON-LD schema.org output for SEO |
  | `->reviews` | `Post_Type_Reviews` | Per-CPT review categories / rating levels (see `voxel-timeline.md`) |
  | `->revisions` | `Post_Type_Revisions` | Revision history management |
  | `->templates` | `Post_Type_Templates` | Template bindings (single / archive / card / form / preview) |
  | `->timeline` | `Post_Type_Timeline` | Per-CPT timeline visibility + moderation (see `voxel-timeline.md`) |
  | `->index_table` | `Index_Table` | Per-CPT search index (see `voxel-search.md`) |
  | `->index_query` | `Index_Query` | Filtered SQL builder against the index |

- **Data shape**: WordPress `wp_posts` + `wp_postmeta`. Custom indexed mirror in `{prefix}voxel_index_{post_type}` (one table per CPT — see `voxel-search.md`). Per-CPT config stored in the `voxel:post_types` option.

- **Public API (`\Voxel\Post`)**:
  - `\Voxel\Post::get( $id | WP_Post )` — singleton-cached post wrapper.
  - Field accessors: `get_field('key')`, `get_fields()`.
  - URL/identity: `get_link()`, `get_edit_link()`, `get_logo_id()`, `get_logo_markup()`, `get_avatar_url()`.
  - Author: `get_author()` — returns `\Voxel\User`.
  - Permission gates: `is_editable_by_current_user()`, `is_viewable_by_current_user()`, `is_deletable_by_current_user()`.
  - State: `is_verified()`, `should_index()`.
  - Time: `get_expiry_date()`.
  - Ranking: `get_priority()` (promotion-aware — see `voxel-commerce.md` → Promotions).
  - Timeline: `get_timeline_publisher_config()` — the persona dropdown logic for `published_as`.
  - Index: `index()`, `unindex()`.
  - Timezone: `get_timezone()` (post `timezone` field if present, else `wp_timezone()`).

- **Public API (`\Voxel\Post_Type`)**:
  - `\Voxel\Post_Type::get( $key )` — singleton-cached CPT wrapper.
  - Field accessors: `get_field( $key )`, `get_fields()`.
  - Filter accessors: `get_filter( $key )`, `get_filters()`.
  - Sort accessors: `get_search_order( $key )`, `get_search_orders()`.
  - Templates: `get_templates()` — returns map of `{single, archive, card, form, preview}` → template ID.
  - Settings: `get_settings()`, `get_setting( $key )` — read per-CPT config.
  - Query: `query( $args )` — wraps `WP_Query` with Voxel defaults.
  - Archive: `has_archive_page()`.
  - Tracking: `is_tracking_enabled()` (statistics opt-in).
  - Type checks: `is_managed_by_voxel()`, `is_created_by_voxel()`.
  - Static: `\Voxel\Post_Type::get_voxel_types()` — array of all Voxel-managed CPTs.

- **Field types** (full catalog at `post-types/fields/`):
  - Scalars: `text`, `texteditor`, `number`, `select`, `multiselect`, `switcher`, `phone`, `url`, `email`.
  - Time: `date`, `time`, `recurring-date`.
  - Media: `image`, `file`, `color`.
  - Geo: `location`.
  - Relational: `taxonomy`, `post-relation`.
  - Composite: `repeater`, `product`, `work-hours`.
  - Profile-group (special — only for the profile CPT): `profile-avatar`, `profile-bio`, `profile-first-name`, `profile-last-name`, `profile-name`.
  - Singular (one-per-post): `title`, `description`, `timezone`.
  - UI-only (no data, just layout in the submission form): `ui-heading`, `ui-html`, `ui-image`, `ui-step`.

  > There is no `textarea` field — long-form text uses `texteditor` (`editor-type: plain-text` for plain textarea, `wp-editor-basic` / `wp-editor-advanced` for WYSIWYG). For the singular post-content textarea use `description`. See [`voxel-field-types.md`](voxel-field-types.md) for the full per-type config catalog.

- **Field conditions** (per-field show/hide in the submission form, at `post-types/field-conditions/`):
  - `text-equals`, `text-contains`, `text-starts-with`, `text-ends-with`.
  - `number-gt`, `number-gte`, `number-lt`, `number-lte`, `number-equals`, `number-not-equals`.
  - `date-before`, `date-after`, `date-equals`.
  - `taxonomy-contains`, `taxonomy-not-contains`.
  - `switcher-checked`, `switcher-unchecked`.
  - `file-empty`, `file-not-empty`.

- **Voxel-native widgets**: `ts-search-form`, `ts-post-feed`, `ts-map`, `ts-term-feed`, `ts-create-post`, `ts-template-tabs`, `ts-print-template`, `ts-current-role`. (Full widget catalog below in the Elementor Integration section.)

- **Dynamic tags**: `@post(:title|:content|:excerpt|:slug|:date|:id|:url|:edit_url|:status|:priority|:post_type|:expiry_date)`, `@post(<field_key>)`, `@post(<field>.sub)`, `@post().meta(<key>)`. Group registered at `dynamic-data/data-groups/post/post-data-group.php`. See `voxel-tags.md`.

- **Settings surface**: `wp-admin/edit.php?post_type=<key>&page=edit-post-type-<key>` — full editor with tabs: General / Fields / Settings / Reviews / Timeline / Messages / Submissions / Permissions.

- **Triggers / events**:
  - `voxel/post-types/<key>/created`, `voxel/post-types/<key>/updated`, `voxel/post-types/<key>/deleted` actions.
  - Event classes under `events/posts/`: `Post_Created_Event`, `Post_Approved_Event`, `Post_Rejected_Event`, `Post_Submitted_Event`, `Post_Updated_Event`, `Post_Expired_Event`.

- **Common usage patterns**: every page that renders Voxel data lives inside a single-post template (`get_templates()['single']`), archive (`['archive']`), card (`['card']`), or form (`['form']`).

- **Gotchas**:
  - `profile` CPT is SPECIAL — it's the user-bound post type. `\Voxel\User::get_or_create_profile()` auto-creates one per user on first access. Don't manually create profile posts.
  - Submission limits, expiration rules, and indexable post statuses are all driven by per-CPT settings, NOT by global Voxel settings.
  - `voxel:post_types` option can grow large (thousands of lines for sites with many CPTs). Updates to this option go through `Post_Type_Repository::save()` — don't hand-edit.

---

## Taxonomies

- **Path**: `taxonomy.php`, `term.php`, `taxonomies/`
- **Purpose**: Wraps `WP_Taxonomy` with Voxel config (label, permalinks, hierarchy, REST exposure, default archive query, `show_in_quick_edit`). Stored at `voxel:taxonomies` option. Per-term metadata + post counts cached in `term-post-counts.php`.

- **Public API**:
  - `\Voxel\Taxonomy::get( $key )` — singleton-cached taxonomy wrapper.
  - `::get_voxel_taxonomies()` — array of Voxel-managed taxonomies.
  - `::get_other_taxonomies()` — non-Voxel taxonomies (third-party / WP core).
  - `->get_config()` — full taxonomy config object.
  - `->get_version()` — cache version (incremented on term changes, used to invalidate search caches).
  - `->update_version()` — bumps version (called on bulk term operations).
  - `\Voxel\Term::get( $term_id )` — term wrapper.

- **Term cache versions**: each taxonomy has a version integer (in `voxel:taxonomy:<key>:version` option). Bumped on term create/update/delete. Search caches referencing the taxonomy include this version in the cache key, so a single bump invalidates all term-dependent caches at once.

- **Dynamic tags**: `@term(:key|:name|:slug|:description|:link|:id|:parent)`, `@term(<field>)`, `@term().meta(<key>)`, `@term().post_count(<post_type?>)`. See `voxel-tags.md`.

- **Settings surface**: `admin.php?page=voxel-taxonomies&action=edit-taxonomy&taxonomy=<key>`.

- **Common usage patterns**: search filter `terms-filter` (taxonomy-bound dropdown / multi-select), card byline category, `ts-term-feed` widget for taxonomy-grid rendering.

- **Gotchas**:
  - Voxel taxonomies have ADDITIONAL config beyond WP core (e.g. permalink struct). When registering a custom taxonomy programmatically, Voxel won't see it unless declared in `voxel:taxonomies` option.
  - `get_version()` is the cache-bust mechanism — if you bulk-import terms via direct SQL, manually call `update_version()` afterwards or search results will be stale.

---

## Roles & Membership (free tier) + User Accounts

- **Path**: `role.php`, `user.php`, `users/`
- **Purpose**: Voxel-managed roles with registration field config, role switching, social login, plans gating. `\Voxel\User` wraps `\WP_User` with multiple traits.

- **User traits** (`users/`):

  | Trait | Path | Responsibility |
  |---|---|---|
  | `Security_Trait` | `users/security-trait.php` | Cap gating, 2FA, password change |
  | `Vendor_Trait` | `users/vendor-trait.php` | Stripe Connect, vendor onboarding state (see `voxel-commerce.md`) |
  | `Customer_Trait` | `users/customer-trait.php` | Purchase history (`has_bought_product()`) |
  | `Social_Trait` | `users/social-trait.php` | Follows + follow stats (see `voxel-timeline.md`) |
  | `Member_Trait` | `users/member-trait.php` | Membership / plan state (see `voxel-commerce.md` → Paid Memberships) |

- **Data shape**: `wp_users` + per-site user meta:

  | Meta key | Type | Notes |
  |---|---|---|
  | `voxel:profile_id` | int | The profile CPT post bound to this user |
  | `voxel:avatar` | int | Attachment ID for avatar (overrides Gravatar) |
  | `voxel:post_stats` | JSON | Denormalized per-CPT post counts |
  | `voxel:timeline_stats` | JSON | Denormalized timeline-activity stats |
  | `voxel:plan` | JSON | Live membership plan state |
  | `voxel:test_plan` | JSON | Test-mode membership plan state |

- **Public API (`\Voxel\User`)**:
  - `\Voxel\User::get( $id )` — singleton-cached user wrapper.
  - `\Voxel\User::query( $args )` — wraps `WP_User_Query`.
  - `\Voxel\User::get_by_profile_id( $profile_post_id )` — reverse lookup.
  - Profile: `->get_profile()`, `->get_or_create_profile()`.
  - Roles: `->get_role_keys()`, `->get_switchable_roles()`, `->has_role( $role )`, `->set_role( $role )`.
  - State: `->is_verified()`.
  - Permissions: `->can_create_post( $cpt_key )`, `->has_cap( $cap )`.
  - Stats: `->get_post_stats()`, `->get_timeline_stats()`.
  - Membership: `->get_membership()`.
  - Follows: `->follows_user( $id )`, `->follows_post( $id )`, `->get_follow_status( $type, $id )`, `->set_follow_status( $type, $id, $status )`.
  - Purchases: `->has_bought_product()`, `->has_bought_product_from_vendor( $vendor_id )`, `->has_bought_product_from_platform()`.
  - Reviews: `->has_reviewed_post( $post_id )`, `->can_review_post( $post_id )`.
  - Wall posting: `->can_post_to_wall()`.
  - Inbox: `->get_inbox_meta()`, `->set_inbox_activity( $has_activity )` — see `voxel-timeline.md` → Direct Messages.
  - Vendor: `->get_vendor_shipping_zone()` — see `voxel-commerce.md`.
  - Timeline persona: `->get_timeline_publisher_config()`.

- **Registration field types** (`users/registration-fields/`):

  | Field | Path | Role |
  |---|---|---|
  | `Username_Field` | `users/registration-fields/username-field.php` | Sign-up username input |
  | `Email_Field` | `users/registration-fields/email-field.php` | Sign-up email input |
  | `Password_Field` | `users/registration-fields/password-field.php` | Sign-up password input |

  Plus profile-bound fields: any profile CPT field listed in `Role::get_available_profile_fields()`:
  - `text`, `textarea`, `number`, `switcher`, `phone`, `url`, `email`, `taxonomy`, `file`, `image`, `date`.
  - Special: `title`, `description`, `profile-avatar`, `profile-name`, `profile-first-name`, `profile-last-name`, `profile-bio`.
  - Choice: `select`, `multiselect`.

- **Capability gating (`_is_safe_for_registration()`)**: when a custom role is created via Voxel, registered users with that role have caps like `manage_options`, `edit_others_posts`, `unfiltered_html` STRIPPED. This is a safety net — even if an admin accidentally grants such caps to a self-registered role, the cap is removed at registration.

- **Voxel-native widgets**: `ts-user-bar`, `ts-login`, `ts-current-role`.

- **Dynamic tags**: `@current_user(...)`, `@user(...)` — both bind to `User_Data_Group`. Properties: `:id`, `:display_name`, `:username`, `:email`, `:first_name`, `:last_name`, `:edit_link`, `:avatar`, `:profile.<field>`, plus role + verification state. `@user().meta(<key>)`. See `voxel-tags.md`.

- **Settings surface**:
  - Per role: `admin.php?page=voxel-roles&role=<key>&action=edit-role`.
  - Global: Voxel → Settings → Membership (verification required, username behavior, social login, plans enabled).

- **Triggers / events**:
  - `voxel/user/can_create_post` filter (for custom post-creation gating).
  - Events under `events/membership/`: `User_Registered_Event`, `User_Data_Export_Requested_Event`.

- **Common usage patterns**: every Voxel site has a "profile" CPT auto-created per user. Custom registration flows add profile-bound fields to the signup form.

- **Gotchas**:
  - `administrator` and `editor` roles are HARD-BLOCKED from self-registration (Voxel's signup endpoint rejects them).
  - `display_name` defaults to `user_login` (NOT to first/last name). Override via filter if you want a different default.
  - The Profile CPT and `voxel:profile_id` user meta wire user → profile post. Deleting the profile post DOES NOT delete the user. Deleting the user DOES delete the profile post (via WP's user-deletion cleanup hooks).

---

## Collections (Saved Posts / Wishlists)

- **Path**: `modules/collections/`
- **Purpose**: User-owned `collection` CPT with a `post-relation-field` named `items`. Lets users save posts into curated lists ("Favorites", "Wishlist", "Watch later", etc.).

- **Data shape**:
  - `collection` CPT — one post per collection per user (CPT is auto-registered by the Collections module).
  - Relations stored in `{prefix}voxel_relations` with `parent_id=<collection_post>`, `child_id=<saved_post>`, `relation_key='items'`.

- **Public API** (`modules/collections/collections.php`):
  - `has_saved_post( $user_id, $post_id )` — boolean (with per-user wp_cache prime for hot paths).
  - `prime_collection_cache( $user_id, $post_ids )` — bulk-warm the saved-post cache for a feed render. CALL THIS before rendering a feed where each card needs a "save" button (otherwise N+1 queries).
  - `get_collection_count( $user_id )` — total collections this user owns.
  - `get_collection_limit()` — read from `settings.addons.collections.max_count` (default 10).
  - `user_can_create_collection( $user_id )` — boolean (count vs limit, admin bypass).

- **Dynamic tags**: via the `collection` CPT — `@post(:item_counts.<post_type_key>)` resolves to per-CPT count of items in that collection (defined in `dynamic-data/data-groups/post/post-data-group.php::get_collection_data()`).

- **Settings surface**: Voxel → Settings → Add-ons → Collections:
  - Max collection count per user (default 10).
  - Default privacy (public / private).

- **Common usage patterns**:
  - "Save to collection" button on every card on a search results page. Wrap the feed render in `prime_collection_cache()` first.
  - "My Wishlist" page: a `ts-post-feed` filtered by `ids` = members of the user's wishlist collection (use `get_search_results( [...], [ 'ids' => [...] ] )`).

- **Gotchas**:
  - Admins are UNLIMITED regardless of `max_count`. The `user_can_create_collection()` check bypasses for `manage_options` cap.
  - Without `prime_collection_cache()`, a feed of 12 cards triggers 12 `has_saved_post()` queries. Always prime.
  - The `collection` CPT is hidden from the standard CPT list (Voxel admin) — it's auto-managed by the Collections module.

---

## Voxel-native Elementor Widget Catalog (the full list)

- **Path**: `modules/elementor/`, `app/widgets/`
- **Purpose**: Registers all Voxel widgets (`ts-*` + `vx-*`) with Elementor, adds custom controls (color-with-variable, post-relation, etc.), registers atomic V4 widgets (`atomic-vx/`), Voxel-template documents.

### Sub-systems

- `atomic-vx/` — Voxel's V4 atomic-aware Elementor controls + prop-types (`vx-loop-control`, `vx-visibility-control`, `vx-dynamic-css-control`, plus the matching prop-type and transformer classes). These power the Dynamic affordance band on EF widgets — NOT a set of new "atomic widgets".
- `custom-controls/` — Voxel-specific Elementor controls (color-with-CSS-variable, post-relation picker, etc.).
- `documents/` — page-template document type for Voxel templates.
- `controllers/` — REST endpoints for editor integrations.

### Full widget catalog (29 registered widgets — verified from `get_name()` in `app/widgets/`)

Grouped by purpose. ALL Voxel widgets use the `ts-*` or `vx-*` namespace. **Verify any name before dumping** — `wpdev elementor:dump <site> <widget> --post <id> --json` will return empty for an unregistered name.

> Several files under `app/widgets/` are abstract bases (no `get_name()`) — `image.php`, `nested-accordion.php`, `nested-tabs.php`, `base-widget.php`. They are NOT registered widgets and cannot be dumped or placed. The canonical instant-search widget is registered as bare `quick-search`, not `ts-quick-search` — treat it as undocumented and use `ts-search-form` instead.

#### Containers / Navigation
| Widget | Path | Role |
|---|---|---|
| `ts-navbar` | `widgets/navbar.php` | Site-wide navigation bar (mega-menu support, role-aware links) |
| `ts-template-tabs` | `widgets/template-tabs.php` | Tabs where each tab loads a Voxel template by ID |
| `ts-test-widget-1` | `widgets/popup-kit.php` | Popup-kit framework (modal/drawer/tooltip) — registered under this WIP name; expect rename. Confirm with `wpdev elementor:widgets <site>` before relying on it. |
| `vx-native-dialog` | `widgets/dialog.php` | Native HTML5 `<dialog>` widget |
| `voxel-empty-skin` | `widgets/empty-skin.php` | Empty container (layout reset / wrapper) — note `voxel-` prefix, not `ts-` |

#### Media
| Widget | Role |
|---|---|
| `ts-gallery` | Multi-image gallery (lightbox-enabled) |
| `ts-slider` | Image/content slider |

#### Feeds
| Widget | Role |
|---|---|
| `ts-post-feed` | Filtered post grid (the canonical CPT feed widget) |
| `ts-term-feed` | Filtered taxonomy-term grid |
| `ts-advanced-list` | Power-user feed with custom layouts |

#### Search
| Widget | Role |
|---|---|
| `ts-search-form` | Filter UI (sidebar/topbar) — see `voxel-search.md` |
| `ts-map` | Interactive map with markers — see `voxel-search.md` |

#### Forms
| Widget | Role |
|---|---|
| `ts-create-post` | Submission form for any CPT (gated by paid plans if configured) |
| `ts-login` | Login + signup form |

#### Commerce
| Widget | Role |
|---|---|
| `ts-cart-summary` | Mini-cart drawer / sidebar — see `voxel-commerce.md` |
| `ts-product-form` | Add-to-cart / Reserve / Buy-now form on a product single |
| `ts-product-price` | Formatted price + interval |
| `ts-booking-calendar` | Visual day/slot picker (paired with `booking-field`) |
| `ts-orders` | Vendor or customer order list |
| `ts-pricing-plan` | Single pricing-plan card (membership / paid-listings) |
| `ts-listing-plans` | Grid of paid-listing plan cards |
| `ts-current-plan` | Renders the current user's active plan state |
| `ts-stripe-account` | Vendor Stripe Connect account dashboard |
| `ts-messages` | Direct-messages inbox UI |

#### Social / Timeline
| Widget | Role |
|---|---|
| `ts-timeline` | Status feed widget (4 feed contexts — see `voxel-timeline.md`) |
| `ts-timeline-kit` | Composable timeline building blocks for custom feed UIs |
| `ts-user-bar` | Logged-in user pill (avatar + dropdown with notifications, inbox, plan, logout) |
| `ts-current-role` | Renders the current user's role label |
| `ts-review-stats` | Aggregate rating bar + per-category breakdown chart |

#### Misc
| Widget | Role |
|---|---|
| `ts-countdown` | Countdown timer to a date |
| `ts-print-template` | Render any Voxel template inline (used for invoices, tickets) |
| `ts-qr-tag-handler` | QR-code generator widget |
| `ts-ring-chart` | Ring/donut chart (review aggregates, stats) |
| `ts-bar-chart` | Bar chart (stats / analytics surfaces) |
| `ts-visits-chart` | Per-post visit chart (statistics module) |
| `ts-work-hours` | Weekly schedule + open/closed badge |

#### Option groups (sub-widgets used inside other widgets)
Located at `widgets/option-groups/`:
- `popup-calendar`, `popup-checkbox`, `popup-controller`, `popup-conversation`, `popup-general`, `popup-head`, `popup-icon-button`, `popup-input`, `popup-label`, `popup-menu`, `popup-notifications`, `popup-radio`.
- `file-field` — file uploader option group (used inside forms).

### Loop + Visibility rule registration

Voxel registers Elementor loop + visibility rules at filter priority 100. The Elementor Framework (`elementor-framework` custom plugin) strips/overrides them at priority 110 — so EF's rules win on sites where both are loaded.

### Important note for builders

**Voxel widgets are NOT introspectable via `wpdev elementor:schema`.** That command targets EF V4 atomic widgets only. For Voxel widgets, use:

```
wpdev elementor:dump <site> ts-post-feed --post <id> --json
```

This dumps a real, known-good widget JSON from a live post. Use it as a template for building new instances.

---

## Post Relations (Cross-CPT linking)

- **Path**: `post-types/fields/post-relation-field/`, `app/connections/`, `controllers/` relation pieces, `events/post-relations/`
- **Purpose**: Many-to-many or one-to-one links between posts of (possibly different) CPTs. Supports approval workflow (`relation-requested`, `relation-approved`, `relation-declined`).

- **Data shape**: `{prefix}voxel_relations`:
  - `parent_id` — the post that "owns" the relation (e.g. a collection owns its items).
  - `child_id` — the linked post.
  - `relation_key` — namespace (e.g. `items` for collections, `team_members` for a company CPT).
  - `status` (optional) — for approval-required relations: `relation-requested` / `relation-approved` / `relation-declined`.

- **Cardinality**:
  - Configured per field: one-to-one (max 1 child), one-to-many (max N children), many-to-many (no cap).
  - Reverse lookup: a child post can query its parents via `\Voxel\connections\Relation::get_parents( $child_id, $relation_key )`.

- **Voxel-native widgets**: rendered inside `ts-create-post` (multi-select picker) and feed-style listings (`@post(<relation>.<field>)`).

- **Dynamic tags**: `@post(<relation_key>.<field>)`, plus dedicated `posts/relation-request` group (visibility rules `relation-approved-event`, etc.). Filter type `relations-filter` (see `voxel-search.md`). See `voxel-tags.md`.

- **Triggers / events** (under `events/post-relations/`):
  - `Relation_Requested_Event` — fires when a relation is requested (approval mode).
  - `Relation_Approved_Event` — fires when an approval-pending relation is approved.
  - `Relation_Declined_Event` — fires when an approval-pending relation is rejected.

- **Common usage patterns**:
  - Collections (saved posts) — see Collections section above.
  - Company ↔ employee linking — company CPT has a `team_members` post-relation field pointing to user-profile posts.
  - Course ↔ lessons — course CPT has a `lessons` field; reverse lookup `Relation::get_parents( $lesson_id, 'lessons' )` finds the parent course.

- **Gotchas**:
  - Relations table has no FK constraints. Manual SQL deletes can leave orphans (parent_id or child_id pointing at deleted posts). `Relation::cleanup_orphans()` (run by cron) periodically cleans these up.
  - Approval-required relations need explicit status updates — they don't auto-progress from `requested` to `approved`.

---

## Verification

- **Path**: `post.php::is_verified()`, `user.php::is_verified()`
- **Purpose**: Manual verified-badge flag on either a user (via profile post) or a post. Drives `is_verified` checks in many tags + visibility rules.

- **Data shape**: `voxel:verified` post meta (boolean `1` / absent).

- **Visibility rules** (`dynamic-data/visibility-rules/`):
  - `post-is-verified` — show element only if current post is verified.
  - `user-is-verified` — show element only if current user is verified (via their profile post).
  - `author-is-verified` — show element only if author of current post is verified.

- **Common usage patterns**:
  - Verified badge next to author name on post cards.
  - "Verified business" filter — combine `post-is-verified` visibility rule with a filtered feed.
  - Claim-listing flow auto-sets `voxel:verified=1` on the post when a claim is approved (see `voxel-commerce.md` → Claim Listings).

- **Gotchas**:
  - Verification is currently MANUAL — no automated identity-proofing pipeline (admins toggle it via the post edit screen).
  - User verification = profile-post verification. To verify a user, edit their profile post (not the user account).

---

## File Uploader & Media

- **Path**: `utils/file-uploader.php`, `controllers/frontend/media-library-controller.php`
- **Purpose**: AJAX file upload used by `ts-create-post`, `ts-timeline` status composer, `ts-product-form`, claim-listings proof-of-ownership. Per-field size + mime-type guards. Private upload mode (claim proofs) excludes from the WP media library.

- **Public API**:
  - `\Voxel\Utils\File_Uploader::upload( $file, $args = [] )` — main entry point (single-file upload).
  - `\Voxel\Utils\File_Uploader::prepare( $key, $files )` — prepare/normalize incoming multi-file payloads.
  - `\Voxel\Utils\File_Uploader::create_attachment( $uploaded_file, $args = [] )` — promote uploaded file to a WP attachment; honors `_display_filename` in `$args`.
  - Field-side wrappers: `\Voxel\Utils\Object_Fields\File_Field` (`app/utils/object-fields/file-field.php`) + `File_Field_Trait` (`file-field-trait.php`).

- **Per-field guards**:

  | Guard | Config |
  |---|---|
  | `max_file_size` | Bytes (default per-CPT, overridable per-field) |
  | `max_file_count` | For multi-file fields |
  | `allowed_file_types` | Mime types whitelist (e.g. `image/jpeg,image/png,application/pdf`) |
  | `private_upload` | If true, file is stored in a private subdirectory and excluded from the media library |

- **Private upload mode**:
  - Files uploaded with `private_upload=true` are NOT browsable in the media library.
  - URL access is denied (returns 403 unless requested with a signed URL).
  - Used by claim-listings proof-of-ownership.
  - Stored in `wp-content/uploads/voxel_private/<hash>/` (subdir name is `voxel_private` — underscore, not hyphen — set in `file-field-trait.php`).

- **Display filename**: `_display_filename` post meta on the attachment stores the original filename (separate from the storage filename, which is hash-based).

- **Gotchas**:
  - Mime-type whitelisting happens BOTH at upload (server-side) AND in the file picker (client-side accept attribute). Server-side is authoritative.
  - Private uploads do not show up in `wp_get_attachment_url()` calls. Use the signed-URL helper on `File_Field`.
  - Multi-file fields don't enforce `max_file_count` across edits — uploading 3 files then re-editing and adding 2 more leaves 5 files even if `max_file_count=3`. The check is per-request.

---

## Statistics / Visits

- **Path**: `utils/stat-utils.php`, `controllers/frontend/statistics/`
- **Purpose**: Per-post visit counter + (optionally) per-action stats. Voxel-managed CPTs can opt INTO tracking via `settings.stats.enabled_post_types`.

- **Opt-in model**: tracking is OFF by default per CPT. Toggle on per CPT in Voxel → Settings → Statistics. When enabled, every visit to a single-post template is logged.

- **Public API** (from `utils/stat-utils.php`, all namespaced under `\Voxel\`):
  - `_count_post_views( $post_id, ?\DateInterval $interval = null )` — total post views in the interval (or all-time if null).
  - `_count_post_unique_views( $post_id, ?\DateInterval $interval = null )` — unique-visitor count.
  - `_get_post_top_referrer_domains|urls|devices|browsers|platforms|countries( $post_id )` — top-N breakdowns.
  - `_count_user_views|_count_user_unique_views|_get_user_top_*( $user_id, … )` — user-level mirrors.
  - `cache_post_view_counts( $post_id )` / `cache_post_tracking_stats( $post_id )` — warm the per-post cache (called from the async stats writer).

- **Tag group**: at `dynamic-data/data-groups/post/visits-data.php`.

- **Voxel-native widgets**:
  - `ts-visits-chart` — bar/line chart of visits over time (configurable period).
  - `ts-ring-chart` — also surfaces visit stats (donut chart view).

- **Dynamic tags**: `@post(:stats.*)` — only resolves when CPT has tracking enabled. See `voxel-tags.md`.

- **Chart data shape**: `{ labels: ['2026-05-19', '2026-05-20', ...], data: [12, 15, ...] }` — consumed by the chart widgets via Chart.js.

- **Gotchas**:
  - Disabling tracking on a CPT does NOT delete historical data — it just stops collecting new data.
  - Visit logging is async (queued via the async-jobs system, see below). Live counts may lag by a few seconds.

---

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
