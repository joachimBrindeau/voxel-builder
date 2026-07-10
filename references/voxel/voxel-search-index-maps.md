# Voxel Search: Index Table, Maps, Dates, And Work Hours

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

## Rebuild And Type-Drift Gate

Use the current workspace command, not historical aliases:

```bash
wpdev rebuild <site> --only reindex
wpdev rebuild <site> --only reindex --recreate
```

Use `--recreate` after field/filter schema changes so the physical table is rebuilt. Before and
afterward, compare the CPT field definition, inferred map, and actual database column types.
Values that appear correct in `_postmeta` can still be truncated or coerced by a stale index
column. Verify indexed/published counts and exercise a query using every changed filter or sort;
a successful rebuild alone does not prove compatible types or query behavior.

## Cross-reference — other feature files in this cluster

| File | Covers | When to read |
|---|---|---|
| [`voxel-timeline.md`](voxel-timeline.md) | Timeline, reviews, comments, follows, mentions, direct messages, notifications | The follow-related filters (`followed-by-filter`, `following-user-filter`, `following-post-filter`) are documented HERE for filter mechanics, but the underlying follow-state model lives in the timeline file. `rating-order` sort uses review-score aggregates from there |
| [`voxel-commerce.md`](voxel-commerce.md) | Products, cart, orders, bookings, memberships, paid listings, claims, promotions, payments | `availability-filter` joins against bookings (commerce). `priority-order` sort respects promotion priority (commerce). Vendor-search pages use `nearby-order` for location-based vendor discovery |
| [`voxel-platform.md`](voxel-platform.md) | Post types, taxonomies, roles + registration, collections, full Voxel widget catalog, post relations, verification, async jobs, auth, print templates | Post-types define the FIELD list that drives index-table column inference. Taxonomies drive `terms-filter` options. Post-relations drive `relations-filter`. Async-jobs/cron drives index-table background rebuilds |

For dynamic-tag syntax of any group mentioned here (`@site.query_var`, `@current_user(profile.location)`), see `voxel-tags.md`.
