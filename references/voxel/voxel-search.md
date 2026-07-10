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

## Split Search Map

| Concern | Reference |
|---|---|
| Search system, filters, sorts, conditions, API, widgets, dynamic tags | `voxel-search-query.md` |
| Index table, maps/geocoding, recurring dates, work hours/timezones | `voxel-search-index-maps.md` |
