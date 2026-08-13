# Voxel Platform: Content Model And Accounts

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

- **Common usage patterns**: search filter `terms-filter` (taxonomy-bound dropdown / multi-select), card heading category, `ts-term-feed` widget for taxonomy-grid rendering.

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
