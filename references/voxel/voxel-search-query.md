# Voxel Search: Filters, Sorts, API, Widgets, And Dynamic Tags

## Search System (the umbrella)

- **Path**: `post-types/filters/`, `post-types/order-by/`, `post-types/filter-conditions/`, `post-types/index-table.php`, `post-types/index-query.php`, `controllers/frontend/search/`
- **Purpose**: Per-CPT indexed search with chained filters, sort clauses, and conditional logic. Filters compile into SQL against the CPT's index table — much faster than `WP_Query` meta lookups. Output is consumed by `ts-search-form` (UI) → `ts-post-feed` (results) → optional `ts-map` (markers) connection chain.

- **Architecture flow**:
  ```
  ts-search-form (UI)          <-- user inputs filter values
       ↓ (form submission → query string)
  controllers/frontend/search   <-- parses query string, calls get_search_results()
       ↓
  get_search_results()          <-- builds query via Index_Query
       ↓
  Post_Type->index_query        <-- chains active filters as SQL clauses
       ↓
  {prefix}voxel_index_<cpt>     <-- the per-CPT mirror table
       ↓
  return { ids[], html, total } <-- consumed by ts-post-feed + ts-map
  ```

---
## Filter Catalog (~17 filter types)

Located at `post-types/filters/`. Each filter is configured per-CPT under the Search tab.

| Filter | Path | Compiles to | UI |
|---|---|---|---|
| `keywords-filter` | `keywords-filter.php` | `MATCH ... AGAINST` fulltext on the `_keywords` column | Search input box |
| `terms-filter` | `terms-filter.php` | `term_id IN (...)` on the taxonomy JSON column | Dropdown / multi-select / button group (configurable) |
| `range-filter` | `range-filter.php` | `<col> BETWEEN <min> AND <max>` | Numeric min/max slider |
| `stepper-filter` | `stepper-filter.php` | `<col> = <value>` | +/- stepper (single integer) |
| `switcher-filter` | `switcher-filter.php` | `<col> = 1` | Boolean toggle |
| `date-filter` | `date-filter.php` | `<col> BETWEEN <start> AND <end>` or `<col> = <date>` | Single date or date range picker |
| `recurring-date-filter` | `recurring-date-filter.php` | Recurring-rule match (custom SQL over the recurring-date JSON) | Single date picker (matches against recurring rule) |
| `availability-filter` | `availability-filter.php` | Booking-availability check (joins against booked slots) | Date range picker, configured against a booking-field |
| `location-filter` | `location-filter.php` | `ST_Distance_Sphere(...) < radius` (or bounding box for simple impl). Also COMPUTES distance for `nearby-order` to consume | Map + radius slider / address input |
| `open-now-filter` | `open-now-filter.php` | Cross-references work-hours JSON with current time-in-timezone | Boolean toggle ("Open right now") |
| `user-filter` | `user-filter.php` | `post_author = <user_id>` | Author selector (typeahead) |
| `followed-by-filter` | `followed-by-filter.php` | Joins `voxel_followers` for the current user's follow list | Boolean toggle ("Posts I follow") |
| `following-user-filter` | `following-user-filter.php` | Joins `voxel_followers` for followers of a specific user | User ID input |
| `following-post-filter` | `following-post-filter.php` | Joins `voxel_followers` for followers of a specific post | Post ID input |
| `relations-filter` | `relations-filter.php` | `EXISTS (... voxel_relations ...)` for posts linked via a `post-relation-field` | Post selector (typeahead) |
| `post-status-filter` | `post-status-filter.php` | `post_status IN (...)` | Status set (publish/pending/draft) |
| `order-by-filter` | `order-by-filter.php` | UI control feeding the chosen sort clause | Dropdown of available sort clauses |
| `ui-heading-filter` | `ui-heading-filter.php` | (no SQL — visual only) | Section heading separator in the filter sidebar |

### Filter notes per type

- **`keywords-filter`**: uses MySQL FULLTEXT index on the `_keywords` column (a denormalized concatenation of title + content + selected fields, populated at index time). Subject to `ft_min_word_len` (default 4 chars in MySQL InnoDB) — short queries silently match nothing. Set `ft_min_word_len=3` in `my.cnf` for sites with short product names.
- **`terms-filter`**: stores selected term IDs as a JSON array column on the index table. The filter operates against the JSON, NOT against `wp_term_relationships`. Bulk term changes require reindex.
- **`range-filter` vs `stepper-filter`**: both numeric, but `range-filter` does `BETWEEN` (user picks min + max) while `stepper-filter` does exact match (user picks one value).
- **`date-filter` modes**: configured per-filter — `range` (start + end inputs), `single` (one date), `dropdown` (preset ranges like "Today", "This week").
- **`recurring-date-filter`**: matches a single date against a recurring rule. Example: "Every Monday 14:00-16:00" + user picks 2026-05-25 (a Monday) → matches.
- **`availability-filter`**: bookings-aware. Filters posts where AT LEAST ONE slot is free in the searched date range. Joins `vx_order_items` to subtract booked slots.
- **`location-filter`**: computes distance via `ST_Distance_Sphere` (MySQL 5.7+). Also EXPOSES the computed distance as a column that `nearby-order` consumes — `nearby-order` requires an active `location-filter` to know what point to measure from.
- **`open-now-filter`**: reads work-hours JSON + timezone (post field or site default), evaluates against current time. Cron does NOT precompute "open now" — it's evaluated at query time.
- **`followed-by-filter`** vs **`following-user-filter`** vs **`following-post-filter`**: subtle distinction:
  - `followed-by-filter` = "posts AUTHORED by users that CURRENT user follows".
  - `following-user-filter` = "posts authored by users that the GIVEN user follows".
  - `following-post-filter` = "posts followed by the GIVEN user".
- **`ui-heading-filter`**: not a real filter, just a visual separator in the filter sidebar (e.g. "── Advanced ──").

---
## Sort Clauses (~12 sort orders)

Located at `post-types/order-by/`. Configured per-CPT and surfaced via the `order-by-filter` UI dropdown.

| Sort | Path | SQL behavior |
|---|---|---|
| `date-created-order` | `date-created-order.php` | `ORDER BY post_date <DIR>` |
| `date-modified-order` | `date-modified-order.php` | `ORDER BY post_modified <DIR>` |
| `date-field-order` | `date-field-order.php` | `ORDER BY <date_field_col> <DIR>` — sort by a chosen date field |
| `time-field-order` | `time-field-order.php` | Same as date-field-order but for time fields |
| `recurring-date-order` | `recurring-date-order.php` | Sort by next-occurrence of a recurring rule |
| `number-field-order` | `number-field-order.php` | `ORDER BY <number_field_col> <DIR>` |
| `text-field-order` | `text-field-order.php` | `ORDER BY <text_field_col> <DIR>` (alphabetical) |
| `latest-activity-order` | `latest-activity-order.php` | `ORDER BY GREATEST(post_modified, last_timeline_activity) DESC` — sorts by most recent timeline activity OR post update |
| `nearby-order` | `nearby-order.php` | `ORDER BY <distance_col> ASC` — requires active `location-filter` |
| `priority-order` | `priority-order.php` | `ORDER BY get_priority() DESC, post_modified DESC` — combines priority field + promotion priority (active promotions win) |
| `random-order` | `random-order.php` | `ORDER BY RAND()` (with optional seed for paginated stability) |
| `rating-order` | `rating-order.php` | `ORDER BY avg_review_score DESC` |
| `relevance-order` | `relevance-order.php` | `ORDER BY <fulltext_score> DESC` — requires active `keywords-filter` |

Grouped via `order-by-group.php` (provides the `order-by-filter`'s dropdown options).

### Sort-clause notes

- **`nearby-order`** REQUIRES an active `location-filter` to know the origin point. If `nearby-order` is selected without a location, it silently falls back to date order. ALWAYS pair them.
- **`relevance-order`** REQUIRES an active `keywords-filter`. Without a keyword, fulltext score is zero for all rows and the result is effectively unsorted.
- **`priority-order`** is multi-key: primary = `get_priority()` (promotion-aware, see `voxel-commerce.md` → Promotions), secondary = `post_modified DESC`. This is the natural default for marketplace homepages.
- **`latest-activity-order`** denormalizes timeline activity into the index column `last_timeline_activity`, updated on every timeline write. Useful for "trending" feeds.
- **`random-order`** with a seed: pass `seed` arg to keep pagination stable. Without seed, page 2 is a new random shuffle (and likely overlaps page 1).
- **`rating-order`** uses `avg_review_score` — a denormalized column populated by the reviews module (see `voxel-timeline.md` → Reviews).

---

## Filter Conditions (per-filter conditional visibility)

Located at `post-types/filter-conditions/`. Used to show/hide one filter based on another filter's value (e.g. "show 'event date' filter only when 'category' = 'Events'").

| Condition | Comparison |
|---|---|
| `text-equals` | Text equals literal |
| `text-not-equals` | Text does NOT equal literal |
| `text-contains` | Text contains substring |
| `number-gt` | Number greater than |
| `number-gte` | Number greater than or equal |
| `number-lt` | Number less than |
| `number-lte` | Number less than or equal |
| `number-equals` | Number equals |
| `number-not-equals` | Number not equals |
| `is-empty` | Filter has no value selected |
| `is-not-empty` | Filter has a value selected |
| `taxonomy-contains` | Taxonomy includes a specific term |
| `taxonomy-not-contains` | Taxonomy does NOT include a specific term |

### Condition notes

- Conditions are evaluated CLIENT-SIDE (in the search-form JS) for UI show/hide, AND server-side in `get_search_results()` (with `apply_conditional_logic=true`) to skip irrelevant filter clauses when generating SQL.
- A filter can have multiple conditions; they're AND-combined.
- Conditions reference filters by KEY (the filter's `key` attribute in the CPT config), not by label. Renaming a filter key breaks conditions referencing the old key.

---

## `get_search_results()` API

The heart of the search system. Located at `controllers/frontend/search/`.

```php
\Voxel\get_search_results( $args, $options ): array
```

### Args (filter values)

`type` (required) — CPT key.
Plus one key per active filter (`<filter_key> => <value>`). Examples:
- `keywords => "pizza"` (for `keywords-filter`)
- `category => [12, 14]` (for `terms-filter` named "category")
- `price => [0, 50]` (for `range-filter` named "price")
- `location => "lat,lng,radius"` (for `location-filter`)
- `availability => "2026-05-25,2026-05-27"` (for `availability-filter`)

Plus pagination:
- `pg` — page number (1-indexed).
- `limit` — per-page (default from CPT settings, capped at 500 via the `voxel/get_search_results/max_limit` filter).

### Options matrix

| Option | Type | Effect |
|---|---|---|
| `template_id` | int | Override the card template (default: CPT's card template) |
| `delivery_mode` | `ssr` \| `json` \| `markers` | `ssr` returns rendered HTML; `json` returns IDs only; `markers` returns lat/lng pairs for the map |
| `render_cards_with_markers` | bool | When `delivery_mode=markers`, also include rendered HTML for popup card on marker click |
| `apply_conditional_logic` | bool | Apply filter-conditions server-side to skip irrelevant filters |
| `preload_additional_ids` | int | Pre-fetch N extra IDs beyond the visible page (for client-side hover-preview or marker chunking) |
| `priority_min` / `priority_max` | int | Constrain by priority range |
| `exclude` | int[] | Exclude specific post IDs |
| `ids` | int[] | RESTRICT to specific post IDs (useful for "saved posts" pages) |

### Return shape

```php
[
    'ids' => [...],              // matching post IDs (visible page)
    'html' => '<div>...</div>',  // rendered cards HTML (when delivery_mode=ssr)
    'additional_ids' => [...],   // preloaded IDs beyond visible page
    'total' => 142,              // total matching count (across all pages)
    'template_id' => 99,         // the card template used
    // For delivery_mode=markers: also includes 'markers' => [{id, lat, lng}, ...]
]
```

---

## Search Widgets

| Widget | Role | Notes |
|---|---|---|
| `ts-search-form` | Filter UI sidebar/topbar | Connects to a feed via `ts_post_to_feed` and to a map via `connect_map` (both reference Elementor widget `id`s) |
| `ts-post-feed` | Results display | Consumes search results, renders cards. Set `ts_source = "search-filters"` to drive the feed from the form |
| `ts-map` | Map view | Consumes `delivery_mode=markers` output |
| `ts-quick-search` | Compact instant-search | Standalone — types-ahead with debounced query |
| `ts-term-feed` | Taxonomy-term grid | Not really search — renders all terms, but supports filtering by parent term |

### Connection wiring (ts-search-form → ts-post-feed / ts-map)

The form ↔ feed ↔ map chain is wired through two settings on the **`ts-search-form`** widget, each pointing at the **Elementor `id`** of the receiving widget on the same page:

| Setting (on `ts-search-form`) | Points to | Purpose |
|---|---|---|
| `ts_post_to_feed` | `ts-post-feed` widget's Elementor `id` | Form submissions update that feed's results |
| `connect_map` | `ts-map` widget's Elementor `id` | Form submissions also re-render that map's markers |

Receiving widgets:
- `ts-post-feed` must set `ts_source = "search-filters"` so it pulls from the form rather than `ts_manual_posts`.
- `ts-map` reads markers from the same `get_search_results()` call (`delivery_mode=markers`) that the connected form triggers.

**Integrity rule:** if the feed or map widget is recreated, its Elementor `id` changes — update `ts_post_to_feed` / `connect_map` on the form to match. Stale IDs are a silent failure (form submits, nothing visibly updates). See [`rules.md`](../core/rules.md) success-criteria checkbox on connection IDs.

---

## Search settings surface

- **Per CPT** (`wp-admin/edit.php?post_type=<key>&page=edit-post-type-<key>` → Search tab):
  - Define filter list (key + label + filter type + per-filter options + conditions).
  - Define sort clauses (key + label + which sort class + direction).
  - Default sort / default direction.
  - Per-page limit (default 12).
  - Search results template binding (`templates.search` page).

- **Global**: Voxel → Settings → Search:
  - Max results cap (default 500, can be raised via the `voxel/get_search_results/max_limit` filter).

---

## Dynamic tag bridge

Filter default values can reference query vars or current user / post data via dynamic tags:

```
default_value = @site(query_var(category))
default_value = @current_user(profile.city)
```

Current filter values surface to JS via `@site().query_var()` and on the search-form's instance config:

```
@site().query_var(keywords)   <-- current value of the "keywords" query var
```

---

## Configuration Invariants

- Treat filter and order keys as stable API identifiers. Labels may change; keys referenced by
  conditions, query strings, widget settings, and sort dependencies must change atomically.
- Field-derived filters must name a field that exists on the same CPT and is supported by that
  filter type. Verify the generated index column/map before assuming a UI row is queryable.
- Dependency pairs are structural: `nearby-order` needs a location filter and
  `relevance-order` needs a keywords filter. Preserve both members when copying configurations.
- Inspect the complete filter row object when debugging. Settings from a prior filter type can
  remain in the shared row namespace and alter behavior after the visible type changes.
- There is no supported `voxel:filters:apply` command. Inspect current CPT configuration with
  supported `wpdev voxel:*` reads, mutate through the current owner, read it back, then rebuild
  the index. Never promote a proposed command from an incident note as an available interface.
