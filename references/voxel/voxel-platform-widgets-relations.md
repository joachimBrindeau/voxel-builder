# Voxel Platform: Widgets, Relations, Verification, Media, And Stats

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
