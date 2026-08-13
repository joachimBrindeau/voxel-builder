# Voxel Template Resolution + Options Storage

How Voxel picks which template renders, where every config lives, and how revisions accumulate. Read before modifying a CPT or its templates so the change lands in the right option key and the right resolution slot.

## Where Voxel options live

All Voxel theme config is in `wp_options` under the `voxel:` prefix. Inspect with:

```bash
wpdev wp <site> option list --search='voxel:*' --fields=option_name --skip-plugins
wpdev wp <site> option get voxel:post_types --format=json --skip-plugins | jq .
```

| Option key | Stores | Mutated by |
|---|---|---|
| `voxel:post_types` | All CPTs: `<key>.{settings, fields, filters, search, templates, custom_templates}` | Voxel admin → Post Types; `wpdev voxel:create`, `wpdev voxel:cards`, `wpdev voxel:assign`; `\VoxelAddon\Modules\Templates\TemplateImporter::apply()` |
| `voxel:templates` | Global template assignments by role: `{header, footer, 404, auth, inbox, orders, checkout, current_plan, configure_plan, stripe_account, privacy_policy, terms, restricted, post_stats, kit_popups, kit_timeline}` → template post ID | Voxel admin → Settings → General; `wpdev voxel:assign --role <global_role>` |
| `voxel:settings` | Theme-wide settings (structure varies by Voxel version) | Voxel admin → Settings |
| `voxel:roles` | User role definitions | Voxel admin → Roles |
| `voxel:taxonomies` | Custom taxonomy definitions | Voxel admin → Taxonomies |
| `voxel:plans` | Membership plans | Voxel admin → Plans |
| `voxel:payments`, `voxel:product_settings`, `voxel:product_types` | Stripe / commerce config | Voxel admin → Payments / Products |
| `voxel:events` | Voxel event/webhook config | Voxel admin → Events |
| `voxel:versions`, `voxel:taxonomy-versions` | Migration version metadata | Voxel auto-updater |
| `voxel:license`, `voxel:onboarding` | License + first-run state | Voxel admin |
| `voxel:post-type-<key>:revisions` | **Voxel admin-config history** for one CPT (snapshots whenever fields / filters / search / templates change in admin) | Voxel admin save events. Accumulates indefinitely. |

For per-post Elementor data, see "Where Elementor data lives" below.

## Template resolution — single posts

When a single post of CPT `<key>` is rendered, Voxel resolves the `single` template in this order:

1. **Custom templates** (visibility-rule scoped):
   `voxel:post_types[<key>].custom_templates.single[]` — array of `{id, label, visibility_rules}`. Each entry's rules are evaluated against the current post; the **first matching entry wins**.
2. **Per-CPT default**:
   `voxel:post_types[<key>].templates.single` (single template post ID).
3. **Elementor Pro theme builder** (separate system):
   `_elementor_conditions` postmeta on `elementor_library` posts. Conditions like `singular/<post_type>/<id>` can override or supplement Voxel's pick. Inspect with `wpdev voxel:templates <site>`.

The `archive` and `form` roles follow the same custom_templates → templates fallback. `form` rarely uses custom_templates.

### An assigned archive template can still be INERT

`archive.php` resolves the CPT and calls `Post_Type::has_archive_page()`, which requires the
assigned document to pass `is_built_with_elementor()`. A template that is assigned but EMPTY
(0-byte `_elementor_data`) fails that check, so Voxel silently falls through to
`templates/defaults/archive.php`. Auditing "is a template id assigned?" is therefore not
enough — always check the stored BYTE LENGTH of `_elementor_data` for the resolved id, and
re-read `has_archive_page()` after writing to prove the gate flipped.

`print_archive_template()` renders the document standalone via
`get_builder_content_for_display()` and NEVER runs the WordPress loop. A Voxel archive template
is a page layout, not a loop template: the main query still runs, but nothing in the template
reads it. Listing posts is entirely the loop/feed widget’s job, which is why an archive with a
layout but no configured loop renders an empty shell rather than a default post list.

## Template resolution — preview cards

When a post is rendered as a card inside `ts-post-feed` / `ts-term-feed`:

1. **Feed-level override**: the feed widget's `ts_card_template__<post_type>` (or `ts_manual_card_template__<post_type>` for manual mode) — if set, this card template wins for items of that post type in this feed.
2. **CPT custom card** (visibility-rule scoped):
   `voxel:post_types[<key>].custom_templates.card[]` — first matching entry wins. Used for variant cards (small/large/avatar/…).
3. **CPT default card**:
   `voxel:post_types[<key>].templates.card`.

`wpdev voxel:cards <site>` adds entries at level 2 (`custom_templates.card[]`). `wpdev voxel:assign --role card --type <key> --template <id>` sets level 3.

## Template resolution — global parts

For header / footer / 404 / auth / orders / checkout / etc., Voxel reads from `voxel:templates` (the global option, not the per-CPT one). Elementor Pro theme builder (via `_elementor_conditions`) can also place a header/footer at the document level — when both are configured, Elementor's location-based system typically wins for the matched URL. Use `wpdev voxel:templates <site>` to see both sources side-by-side.

## Where Elementor data lives

Per-template / per-post Elementor data is in `wp_postmeta`:

| Meta key | Scope | Purpose |
|---|---|---|
| `_elementor_data` | Any post (`page`, `elementor_library`, CPT instance) | The widget tree as JSON. The actual content. |
| `_elementor_template_type` | `elementor_library` posts only | One of: `wp-page`, `single-page`, `theme_part`, `header`, `footer`, `popup`, etc. — drives the editor's UI affordances. |
| `_elementor_conditions` | `elementor_library` posts (theme builder) | Elementor Pro's display conditions array — drives where this template renders. |
| `_elementor_css` | Any post with `_elementor_data` | Cached compiled CSS. Regenerated on editor save or `wpdev rebuild <site> --only purge`. |
| `_elementor_page_settings` | Any post | Page-level settings (custom CSS, layout). |
| `_elementor_version` | Any post | Editor version that last saved. |
| `_elementor_edit_mode` | Any post | `builder` if Elementor is active on this post. |

To dump everything for a post: `wpdev elementor:dump <site> all --post <id> --json`.

To list all `elementor_library` templates with their type + role + Voxel/Elementor binding:
```bash
wpdev elementor:templates <site>     # Elementor-only view
wpdev voxel:templates <site>         # Voxel + Elementor merged view
```

## Revisions — two distinct systems

This is the canonical reference cited by [`rules.md`](../core/rules.md) Rule 6 and [`build.md`](../../workflows/build.md) §Phase 0.

| Axis | WP post revisions | Voxel admin-config revisions |
|---|---|---|
| Post type / storage | `wp_posts` rows with `post_type='revision'`, `post_parent=<original_id>`; each clones `_elementor_data` postmeta | JSON array inside one `wp_options` row per CPT, key `voxel:post-type-<key>:revisions` |
| Created by | Every Elementor editor save (often multiple per session) | Voxel admin saves on the CPT config screen (fields / filters / search / templates) |
| Bloat profile | Fast — `_elementor_data` × revision count × 2 (revisions + autosaves) on heavily-edited templates | Slow but unbounded — Voxel ships no auto-prune |
| Pruned by | `wpdev elementor:revisions:prune <site> --post <id>` (snapshots before delete; omit `--post` for site-wide); `--dry` to preview | NOT touched by `elementor:revisions:prune`. Hand-edit (`wpdev wp <site> option update 'voxel:post-type-<key>:revisions' ...`) or delete (`wpdev wp <site> option delete 'voxel:post-type-<key>:revisions'`). Voxel admin exposes no UI. |
| Inspect | `wpdev wp <site> post list --post_type=revision --post_parent=<id> --format=count` | `wpdev wp <site> option get 'voxel:post-type-<key>:revisions' --format=json --skip-plugins \| jq 'length'` |

**Rule 6 / Phase 0 obligation.** Before any non-trivial template modification, offer to prune **WP post revisions** (not Voxel admin-config revisions). The snapshot-then-delete behaviour of `wpdev elementor:revisions:prune` makes the operation reversible via `wpdev elementor:revisions:restore`.

## Quick lookups

```bash
# Which template renders for a single post of CPT <key>?
wpdev wp <site> option get voxel:post_types --format=json --skip-plugins | jq '.<key>.templates.single, .<key>.custom_templates.single'

# Which global header template is active?
wpdev wp <site> option get voxel:templates --format=json --skip-plugins | jq '.header'

# Full template assignment view (Voxel + Elementor)
wpdev voxel:templates <site>

# Elementor instance dump for ANY post (including elementor_library template posts)
wpdev elementor:dump <site> all --post <template_post_id> --json

# Count WP revisions for a template
wpdev wp <site> post list --post_type=revision --post_parent=<id> --format=count --skip-plugins

# Count Voxel admin-config revisions for a CPT
wpdev wp <site> option get 'voxel:post-type-<key>:revisions' --format=json --skip-plugins | jq 'length'
```

## Mutation safety

- **Modifying `voxel:post_types`** — always `wp_json_encode($pts, JSON_UNESCAPED_UNICODE)` when writing back, never default `json_encode`. Voxel's importer (`TemplateImporter::apply`) preserves site-specific keys (`templates`, `custom_templates`, `settings.singular`, `settings.plural`, `settings.permalinks`) — use it for blueprint-driven mutations.
- **Modifying `_elementor_data` directly** — write via `update_post_meta` with `wp_slash(wp_json_encode(...))`. Reading back: `json_decode(get_post_meta(...))` should work without `wp_unslash`. If it requires unslashing, the value is double-escaped — fix before continuing.
- **Modifying `voxel:templates`** — same JSON-encoding rules.
- **After any change to `voxel:post_types` or `voxel:templates`**: flush rewrite rules (`wpdev wp <site> rewrite flush`) and clear Elementor's CSS cache (`wpdev rebuild <site> --only purge`).
