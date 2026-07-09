# Voxel Search — Filters, Sort Clauses, Index Table, Maps, Recurring Dates, Work Hours

The discovery surface of Voxel: the per-CPT indexed search engine (filters + sort clauses + conditions), the per-CPT index table that backs it, the maps + geocoding provider abstraction, and the recurring-date / work-hours / open-now filters. All search runs against the per-CPT index table (`{prefix}voxel_index_<post_type>`), NOT against `WP_Query` — meta lookups would be too slow at scale.

Source theme: `sites/<site>/wp-content/themes/voxel/app/` (paths below are relative to `app/` unless noted).

## How to use this reference

Read this file when:
- Configuring a CPT's Search tab (defining filter list, sort clauses).
- Building a search page (`ts-search-form` → `ts-post-feed` → `ts-map` connection chain).
- Debugging why a filter isn't matching (likely an index table issue — see Index Table section).
- Implementing a "near me" / geo-distance search (location-filter + nearby-order).
- Adding an "open now" badge or "available this date" filter (work-hours / availability filters).
- Tuning the index table after schema changes (rebuild via `wpdev rebuild <site> --only reindex --recreate`).
- Choosing a map provider (Google Maps / Mapbox / OpenStreetMap).
- Wiring `nearby-order` distance computation that depends on a chosen `location-filter`.

For dynamic-tag syntax (`@site(query_var(...))`) see `voxel-tags.md`. This file documents the *system* — filter catalog, sort catalog, conditions, the `get_search_results()` API, the index table, and the maps abstraction.

For commerce-search intersections (`availability-filter` for bookings, `priority-order` for promotions) see `voxel-commerce.md`. For follow-related filters (`followed-by-filter`, `following-user-filter`, `following-post-filter`) see `voxel-timeline.md`.

---

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

## Index Table (per-CPT search index)

- **Path**: `post-types/index-table.php`, `post-types/index-query.php`
- **Purpose**: Per-CPT mirror table with flattened, query-optimized columns for every filterable field. Eliminates expensive postmeta joins on search.

- **Data shape**: one table per CPT, named `{prefix}voxel_index_<post_type>` (e.g. `wp_voxel_index_listing`, `wp_voxel_index_profile`). Columns inferred from field types — see Column Inference below.

- **Column inference rules**:

  | Field type | Index column type |
  |---|---|
  | `text`, `email`, `url`, `phone` | `VARCHAR(255)` |
  | `textarea` | NOT indexed individually — content folded into `_keywords` fulltext column |
  | `number` | `DECIMAL(20,4)` |
  | `select`, `multiselect` | `VARCHAR(255)` (multiselect = JSON array string) |
  | `switcher` | `TINYINT(1)` |
  | `date` | `BIGINT` (unix timestamp) |
  | `time` | `BIGINT` (seconds since midnight) |
  | `recurring-date` | `JSON` (full rule stored) |
  | `taxonomy` | `JSON` (term ID array) |
  | `location` | `VARCHAR(255)` for address + separate `DECIMAL(10,7)` for `lat` and `lng` + computed `POINT` for `ST_Distance_Sphere` |
  | `image`, `file` | NOT indexed (filter by image is not supported) |
  | `repeater` | NOT indexed at top-level; sub-fields can be promoted to top-level columns via "make filterable" toggle |
  | `post-relation` | NOT a column — filtered via JOIN against `voxel_relations` |
  | `product` | NOT indexed |
  | `work-hours` | `JSON` |
  | `color` | `VARCHAR(20)` |
  | All fields | A `_keywords` FULLTEXT column denormalizes title + content + any field flagged "searchable" |

- **Public API**:
  - `$post_type->get_index_table()->index( [$post_ids] )` — index specific posts (incremental).
  - `$post_type->get_index_table()->unindex( [$post_ids] )` — remove from index.
  - `$post_type->get_index_table()->rebuild()` — full rebuild (drop + recreate + reindex all).
  - `$post_type->get_index_query()->get_posts( $args, $cb )` — chained-filter SQL builder.

- **Indexable statuses**: per-CPT via `repository->get_indexable_statuses()`. Default: `['publish']`. To include drafts/pending in search, override this per CPT.

- **Index version**: tracked via taxonomy versions (`\Voxel\Taxonomy::get_version()`). When a taxonomy version bumps (e.g. a term is renamed), search results referencing that taxonomy are cache-invalidated.

- **Triggers / events**: `voxel/get_search_results/max_limit` filter (default 500).

- **CLI commands**:
  - `wpdev rebuild <site> --only reindex` — reindex every Voxel-managed CPT in one pass (chunked, all types in one round-trip). There is no per-type form anymore; reindex always covers all CPTs.
  - `wpdev rebuild <site> --only reindex --recreate` — also drop and rebuild each index table's column set from the current filter graph before reindexing. Mandatory after a blueprint adds/removes search-filter sources.

- **Common usage patterns**:
  - On `save_post`: Voxel auto-calls `->index([$post_id])` for the saved post.
  - On `delete_post`: Voxel auto-calls `->unindex([$post_id])`.
  - On bulk import: index is auto-rebuilt at end of import.
  - On schema change (added/removed filter on a CPT): `rebuild()` MUST be run to add/drop the column.

- **Gotchas**:
  - Adding a new filter on a CPT does NOT auto-rebuild the index. The new column is missing until `rebuild()` runs. Search against the new filter silently returns no rows until then.
  - Repeater sub-fields are NOT indexed by default. To make a repeater sub-field filterable, toggle "make filterable" in the field config — this promotes it to a top-level column (with rows duplicated per sub-item entry).
  - `_keywords` FULLTEXT column includes only fields flagged "searchable". By default this is just `title` + `content`. Custom field "searchable" toggle adds the field's value to the haystack.
  - The index table is per-CPT — cross-CPT searches require iterating CPTs and merging results (not natively supported by `get_search_results()`; use multiple calls + merge).

---

## Maps + Geocoding

- **Paths**: `modules/google-maps/`, `modules/mapbox/`, `modules/openstreetmap/`
- **Purpose**: Pluggable map-provider abstraction. Each module wires up its provider's JS SDK, geocoding API, and language support for `ts-map` + `location-filter` + `nearby-order`.

- **Provider abstraction**:

  | Provider | Module path | Notes |
  |---|---|---|
  | Google Maps | `modules/google-maps/` | Most accurate geocoder, paid (free tier for low-volume) |
  | Mapbox | `modules/mapbox/` | Beautiful styling, paid (generous free tier) |
  | OpenStreetMap | `modules/openstreetmap/` | Free, Nominatim geocoder (rate-limited — not suitable for high-traffic geocoding) |

  Each module provides:
  - JS SDK loader.
  - Geocoder (address → lat/lng).
  - Reverse geocoder (lat/lng → address).
  - Marker/cluster rendering.
  - `supported-languages.php` enumerating valid `language` parameter values.

- **Public API**:
  - `\Voxel\geocode( $address )` — provider-dispatched. Returns `{lat, lng, formatted_address, components}`.
  - Map provider chosen by `settings.maps.provider`. The chosen provider's module hooks into `\Voxel\geocode()`.

- **Voxel-native widget**: `ts-map` — interactive map with markers. Reads results from a connected `ts-search-form` (the form's `connect_map` setting references the map's Elementor `id` — see §Search Widgets §Connection wiring).

- **Marker chunking**: for large result sets, `preload_additional_ids` option of `get_search_results()` controls how many marker IDs are preloaded beyond the visible page. The map widget then chunks marker requests to avoid overwhelming the browser.

- **`nearby-order` distance source**: when `nearby-order` is the active sort, it READS the distance column populated by `location-filter`. The origin point comes from the user's filter input (either typed address geocoded via `\Voxel\geocode()` or pulled from `@current_user(profile.location)`).

- **Settings surface**: Voxel → Settings → Maps:
  - Provider (Google / Mapbox / OSM).
  - API key (provider-specific).
  - Default center (lat/lng).
  - Default zoom.
  - Language.
  - Map style (provider-specific styling).

- **Common usage patterns**:
  - Directory site: `ts-search-form` (with `location-filter`) + `ts-post-feed` (sorted by `nearby-order`) + `ts-map` (markers for all results).
  - Single-location page: standalone `ts-map` centered on a single post's location, no search.

- **Gotchas**:
  - `supported-languages.php` per module enumerates valid Google/Mapbox/OSM `language` parameter values. Passing an unsupported language causes silent fallback to English.
  - OSM Nominatim rate-limit: 1 request/second per IP. For high-traffic sites, cache geocoded results or switch to Google/Mapbox.
  - The map provider is chosen GLOBALLY (one provider per site). Mixing providers (Google for some maps, Mapbox for others) is not supported.
  - Geocoding happens at POST SAVE time (when a location-field is filled). After-the-fact reverse geocoding is not auto-triggered.

---

## Recurring Dates & Work Hours

- **Path**: `post-types/fields/recurring-date-field.php`, `post-types/fields/work-hours-field.php`, `utils/recurring-date-utils.php`
- **Purpose**: Two related field types for time-based scheduling — recurring event rules and weekly business open hours.

### Recurring Dates

- **Field type**: `recurring-date`. Stored as a JSON **array** of rule objects (one per scheduled occurrence). Each rule shape (per `post-types/fields/recurring-date-field.php::sanitize()`):
  ```json
  [
    {
      "start": "2026-05-25 14:00:00",
      "end":   "2026-05-25 16:00:00",
      "frequency": 1,
      "unit": "week",
      "until": "2027-01-01"
    }
  ]
  ```
  - `unit` ∈ `day` | `week` | `month` | `year`. `frequency` is an integer multiplier (every N units).
  - Non-recurring single-occurrence entries omit `frequency`/`unit`/`until` and only carry `start` + `end`.
  - Multi-day-of-week selection is expressed as multiple entries in the outer array, not as `BYDAY` flags.
- **Compatible filter**: `recurring-date-filter` — matches a single date input against the rule set (via SQL date arithmetic on `start`/`frequency`/`unit`/`until`; no RRULE library).
- **Compatible sort**: `recurring-date-order` — sorts by next-occurrence of the rule (forward in time from now).
- **Utility**: `utils/recurring-date-utils.php` — exposes the SQL fragments used for next-occurrence and in-range matching. Direct PHP helpers are not part of the public API; use `recurring-date-filter` / `recurring-date-order` instead of computing occurrences manually.

### Work Hours

- **Field type**: `work-hours`. Stored as a JSON array of **groups**; each group bundles one or more weekdays sharing a status. Shape (per `post-types/fields/work-hours-field.php::sanitize()`):
  ```json
  [
    {
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "status": "hours",
      "hours": [
        {"from": "09:00", "to": "12:00"},
        {"from": "14:00", "to": "18:00"}
      ]
    },
    { "days": ["saturday"], "status": "appointments_only", "hours": [] },
    { "days": ["sunday"],   "status": "closed",            "hours": [] }
  ]
  ```
  - `status` ∈ `hours` | `open` (open all day) | `closed` | `appointments_only`. `hours[]` only populated when `status === "hours"`.
  - A given weekday key may appear in at most one group (the sanitizer drops duplicates).
  - Also denormalized into `{prefix}voxel_work_hours` for `open-now-filter` SQL evaluation.
- **Compatible filter**: `open-now-filter` — evaluates current time-in-timezone against the schedule.
- **Voxel-native widget**: `ts-work-hours` — renders the weekly schedule + an open/closed badge.

### Timezone source resolution

Both filters need to know the POST's timezone (the business's local timezone). Resolution order:

1. If the post's CPT has a `timezone` field type (`post-types/fields/singular/timezone-field`) and the post has a value, use that.
2. Else, fall back to `wp_timezone()` (the site's WP timezone setting).

Use `\Voxel\Post::get_timezone()` to get the resolved timezone — handles the fallback chain transparently.

- **Settings surface**:
  - Per-post timezone field (`post-types/fields/singular/timezone-field` — not in the standard fields list but available for profile CPT and any CPT that explicitly adds it).
  - Otherwise site timezone.

- **Dynamic tags**: `@post(<work_hours_field>)`, `@post(<recurring_date_field>)`. These return formatted strings (e.g. "Mon 09:00-18:00, Closed Sun") for display.

- **Gotchas**:
  - `open-now-filter` is evaluated at QUERY TIME (no precomputation). For high-traffic sites, this is fine (millisecond cost per row) but on huge datasets consider caching at the query layer.
  - `recurring-date-order` requires the rule's UNTIL date to be in the future. Past-only rules sort to the end.
  - Timezone field is not in the default fields list — to add it to a CPT, the CPT must explicitly declare a `timezone` field in its blueprint.
  - DST transitions: rules referencing fixed local times (e.g. "every Monday 14:00") shift by an hour twice a year. The `rrule` library handles this correctly via local-time interpretation.

---

## Cross-reference — other feature files in this cluster

| File | Covers | When to read |
|---|---|---|
| [`voxel-timeline.md`](voxel-timeline.md) | Timeline, reviews, comments, follows, mentions, direct messages, notifications | The follow-related filters (`followed-by-filter`, `following-user-filter`, `following-post-filter`) are documented HERE for filter mechanics, but the underlying follow-state model lives in the timeline file. `rating-order` sort uses review-score aggregates from there |
| [`voxel-commerce.md`](voxel-commerce.md) | Products, cart, orders, bookings, memberships, paid listings, claims, promotions, payments | `availability-filter` joins against bookings (commerce). `priority-order` sort respects promotion priority (commerce). Vendor-search pages use `nearby-order` for location-based vendor discovery |
| [`voxel-platform.md`](voxel-platform.md) | Post types, taxonomies, roles + registration, collections, full Voxel widget catalog, post relations, verification, async jobs, auth, print templates | Post-types define the FIELD list that drives index-table column inference. Taxonomies drive `terms-filter` options. Post-relations drive `relations-filter`. Async-jobs/cron drives index-table background rebuilds |

For dynamic-tag syntax of any group mentioned here (`@site.query_var`, `@current_user(profile.location)`), see `voxel-tags.md`.
