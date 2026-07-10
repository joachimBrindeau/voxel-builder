# Voxel Dynamic Tags: Loops, Visibility, Feeds, Index, And Relations

## Loops

Any `ef-wrapper` becomes a loop by setting `_vx_loop` (Voxel-side scope) and optionally `_ef_loop_transform` (EF-side filter / sort / reverse). The wrapper and its children are cloned once per matched post.

| Key | Owner | Notes |
|---|---|---|
| `_vx_loop` | Voxel | Iteration scope — bound to a post-type loop (`loop_<post_type_key>`) via the Dynamic affordance band's loop picker. Modern preferred name. |
| `_vx_visibility` | Voxel | Conditional rendering — bound via the Dynamic affordance band's visibility picker. Modern preferred name. |
| `_ef_loop_transform` | EF | EF-owned filter / sort / reverse parity for atomic widgets — sibling of `_vx_loop`. Universal on every EF widget (auto-merged by `ef_atomic_base_props()`). |
| `_ef_loop_sort` | EF | Sort order enum on `ef-wrapper` loop hosts — query schema for current values. |
| `_ef_loop_initial` | EF | Initial visible-item count when load-more chunking is on. |
| `_ef_loop_more_label` | EF | Load-more button label. |
| `_ef_loop_less_label` | EF | Load-less button label. |
| `_voxel_loop` / `_voxel_loop_limit` / `_voxel_loop_offset` | legacy | V3 names — still recognized on read by `ef_with_voxel_loop()` for back-compat, but new JSON should use the `_vx_*` / `_ef_loop_*` set above. |
| `_voxel_visibility_rules` / `_voxel_visibility_behavior` | legacy | V3 visibility shape — recognized for back-compat; new JSON uses `_vx_visibility`. |

EF strips Voxel's three (VX) sections (`_vx_loop`, `_vx_visibility`, `_vx_dynamic_css`) from EF widget panels and replaces them with the **General → Dynamic** affordance band — three icon pickers bound to `_vx_loop` / `_vx_visibility` / `_ef_loop_transform`. Voxel's panels still appear on third-party (non-EF) widgets unchanged.

### Placement decision: WIDGET-level vs ROW-level vs ts-post-feed

This is the single most expensive mistake to get wrong. Picking the wrong placement renders something — but it iterates the wrong thing, and the symptom only appears on item 2+. Pick by what should be **replicated**:

| Goal | Place loop here | Source-code evidence |
|---|---|---|
| Replicate the **entire widget** per item (e.g. one `ef-card` becomes N cards) | `settings._vx_loop` (widget-level) on the widget itself | `loop-controller.php:142-173` hooks `elementor/frontend/widget/before_render` and replicates the whole widget per iteration via `Looper::run` |
| Iterate **one row of a composite repeater** (heading row, accordion row, action row) inside one widget | `settings.<repeater>.value[N].value._vx_loop` (row-level, V4 envelope) | `EF_Loopable_Row_Prop_Type` — `includes/props/loopable-row-prop-type.php:43-73` |
| Render a **feed of cards from a relation/CPT** with pagination, sort, search-form connection | `ts-post-feed` widget — NOT `_vx_loop` | [`widgets.md`](../ef/widgets.md) §EF loop vs ts-post-feed |

Before any loop work, **read these two files once** so the placement decision is grounded:

```bash
sites/<site>/wp-content/plugins/elementor-framework/includes/loop-controller.php       # widget-level
sites/<site>/wp-content/plugins/elementor-framework/includes/props/loopable-row-prop-type.php  # row-level
```

Common pattern for a "list of cards" section:
- Outer `ef-wrapper` provides the section structure — NOT looped.
- Inner `ef-card` (or `ef-wrapper`) carries `_vx_loop` at widget level — IS looped.
- Children reference `@site(loop_<type>.field)` — resolved per iteration.
- The `author` sub-property works inside loops (EF registers it on the post data group).

Common pattern for a "row inside a card" loop (e.g. timeline events on a single card):
- The `ef-card` itself is NOT looped (one card renders).
- The card's heading-rows / action-rows / tag-rows repeater carries `_vx_loop` at row level — that ONE row is iterated, the rest of the card is fixed.

For an EF-loop-vs-`ts-post-feed` decision, see [`widgets.md`](../ef/widgets.md) §EF loop vs ts-post-feed.

## Visibility rules

Conditional rendering via `_vx_visibility` (modern) on any widget or repeater item. Shape (verify via `wpdev elementor:schema <site> <widget> --prop _vx_visibility`):

```
_vx_visibility: { rules: [[{type: 'dtag', tag: '@post(:id)', compare: 'is_not_equal_to', arguments: ['<id>']}]], behavior: 'show' }
```

The legacy `_voxel_visibility_rules` array shape is still expanded by `ef_has_voxel_visibility()` for back-compat reads.

Common operators: `is_equal_to`, `is_not_equal_to`, `is_not_empty`, `is_empty`. Outer array is OR-of-AND-groups.

`behavior: 'hide'` inverts (hide when rules match instead of show).

Common use: prevent a related-posts feed item from referencing the current post (filter out by `:id`).

## Migration rule — preserve dynamic expressions

**Never strip, modify, or HTML-encode dynamic tag expressions.** Before any content cleanup, scan the value for these markers and skip if any are present:

```
@post(  @author(  @site(  @current_user(  @tags(
{{post.  {{author.  {{site.
```

Voxel renders these at runtime — escaping or stripping breaks the binding silently.

## Feeds: prerequisites and connection rules

`ts-post-feed` renders nothing without setup. The CPT must have `search.filters` and `search.order` configured (see [`blueprint-format.md`](../core/blueprint-format.md) §Search config) and an index table populated.

### Filter types

The CPT's `search.filters` array supports:

| Type | Purpose |
|---|---|
| `keywords` | Full-text search across `sources` (e.g. `title`, `description`, `content`) |
| `terms` | Filter by taxonomy term |
| `parent` | Filter by parent post (post_parent) |
| `relations` | Filter by a `post-relation` field |
| `date` | Date range filter |

### Sort clause types

The CPT's `search.order[].clauses` support:

| Clause type | Use |
|---|---|
| `text-field` | Sort by text field value (title, h1) |
| `date-created` | Sort by creation date |
| `relevance` | Sort by keyword match score |
| `random` | Random ordering (with optional `seed`) |

### Source modes

`ts-post-feed.ts_source`:
- `search-filters` — dynamic; syncs with page's search form OR uses the feed's own `ts_filter_list__<type>` overrides
- `manual` — fixed list via `ts_manual_posts` (each `{_id, post_id}`)
- `search-form` — feed only renders after form submit
- `archive` — uses WP archive query

### Connection integrity

When a page has both `ts-search-form` and `ts-post-feed`:
- The form's `ts_post_to_feed` references the feed's element `id`
- Recreating the feed widget with a new `id` breaks the connection
- Same applies to `connect_map` (form → map) and `ts_card_template__<type>` / `ts_manual_card_template__<type>` (post IDs to the rendered card templates)
- After any restructure, verify these references resolve

For the canonical settings shape on any `ts-*` widget, dump a known-good production instance:

```bash
wpdev elementor:dump <site> ts-post-feed   --post <prod_post_id> --json
wpdev elementor:dump <site> ts-search-form --post <prod_post_id> --json
```

## Voxel index table

Feeds query the Voxel index table, not `wp_posts` directly. New CPTs need their index table created and posts indexed before feeds render results.

```php
$pt = \Voxel\Post_Type::get('<key>');
$pt->index_table->create();

$posts = get_posts(['post_type' => '<key>', 'post_status' => 'publish', 'posts_per_page' => -1, 'fields' => 'ids']);
foreach ($posts as $post_id) {
    \Voxel\Post::force_get($post_id)->index();
}
```

New posts are auto-indexed on publish. Only the initial setup needs manual indexing.

## Relation fields

Voxel `post-relation` fields create queryable connections between CPTs. Feed filters reference these via `ts_choose_filter` + `<filter_key>:value`. Templates access related data via dot-notation:

- `@post(<relation>.title)` / `.permalink` — core props of the related post (always safe)
- `@post(parent.title)` — parent post (via `post_parent`)
- `@post(children.title)` — child posts (in a loop context)
- `@post(<relation>.:<core>)` — explicit core WP property (e.g. `@post(children.:excerpt)`)

### Single-type vs multi-type relations

A `post-relation` field is configured to point at one or many target CPTs (the `post_types` prop). Traversal behaviour depends on this:

- **Single-type relations** — dot-traversal resolves any field on the target CPT: `@post(<relation>.<field_on_target>)`. Sub-keys like `.id` on image fields work too. Example: `@post(<relation>.<title_field>)` returns the target post's title field; `@post(<relation>.<image_field>.id)` returns the target's image attachment ID.
- **Multi-type relations** — resolution goes through `Simple_Post_Data_Group`, NOT the target CPT's full data group. Custom fields on targets are unreachable. Use the registered base accessors (`title`, `permalink`, `excerpt`, `slug`, `content`, `id`, `date_created`, `status`, `post_type`, ...) or their colon aliases (`.:title`, `.:url` ← alias for `permalink`, `.:excerpt`, `.:id`, `.:date`, ...). **`.:permalink` does NOT exist** — use bare `.permalink` or `.:url`. Confirm the map against the current `Simple_Post_Data_Group` registry.
- **`(no target configured)` relations** — `wpdev voxel:fields` reports this when a relation field is registered without an explicit target list. Treat as multi-type for safety: registered base accessors only. Even when the relation resolves to a single CPT in practice (verifiable via `wpdev voxel:data`), the skill can't prove that statically.

### How to detect single-vs-multi

Run `wpdev voxel:fields <site> <cpt_key>`. The `RELATION TARGET` column reports `single → <cpt>`, `multi → <cpt>, <cpt>`, or `(no target configured)` for every `post-relation` field. Single-type relations are then expanded below the table with the full list of traversable `@post(<relation>.<field>)` expressions for that target — copy-paste ready.
