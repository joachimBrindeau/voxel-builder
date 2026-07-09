# CPT Repair Workflow

Repair an existing Voxel CPT when runtime registration, templates, archive/list pages, dynamic entity data, or lean-seo outputs drift from the intended behavior. This workflow is generic: it applies to `events`, services, glossary terms, locations, profiles, testimonials, and future CPTs.

## Entry Criteria

- Site identifier or URL is known.
- CPT key is known or discoverable from the request.
- The problem is tied to Voxel CPT behavior, Elementor/EF template output, Voxel entity data, or lean-seo output.
- A mutating run has permission to write DB/template/config changes.

## Phase 1 — Baseline and Backup

Entry: target site and CPT are known.

1. Capture a DB backup before mutation: `wpdev wp <site> db export /tmp/<site>-before-<cpt>-repair.sql` or equivalent `wp db export`.
2. Record runtime CPT state: public/show UI/archive/rewrite/REST/supports/taxonomies.
3. Record Voxel config state from the Voxel post-type registry option/CLI.
4. List published and non-published records with IDs, slugs, status, and core dates.
5. Sample source fields, post meta, relation fields, and rendered URLs.

Exit: there is a rollback file and a written baseline of runtime, Voxel config, source data, and representative rendered output.

## Phase 2 — Classify Fault Surface

Entry: baseline exists.

Classify each issue into exactly one primary surface:

| Surface | Symptoms | Source of Truth |
|---|---|---|
| Runtime registration | wrong label, archive disabled, REST/Gutenberg missing, rewrite mismatch | Voxel CPT config + registered post type object |
| Entity data | wrong field values, stale status, broken excerpts/content/repeaters | Voxel fields, post meta, core post columns |
| Elementor/EF template | placeholder CTAs, duplicated loops, stale static copy, wrong wrapper/template | `_elementor_data`, Voxel template resolution, EF widget schemas |
| Archive/search page | upcoming/past duplication, wrong feed/filter/sort, missing no-results state | page/template driving the route, search widgets, loop config |
| lean-seo output | wrong JSON-LD, thin `.md`, wrong meta/OG/sitemap/permalink/noindex | lean-seo per-target settings/options and source field resolvers |
| Cache/generated assets | fix appears not to apply, stale HTML/CSS, generated CSS 404 | LiteSpeed/object cache, Elementor generated files, lean-seo purge epoch |

Exit: every requested fix has a surface assignment and source-of-truth path.

## Phase 3 — Repair Source of Truth

Entry: fault surfaces are classified.

1. Runtime registration: update the Voxel CPT config, preserving storage type. If the option stores JSON as a string, write a string; do not turn it into an array.
2. Entity data: update source fields only. For date/status fields, derive status from schedule/end-date policy and write the canonical field used by templates/schema.
3. Elementor/EF templates: patch `_elementor_data` only after reading the real widget/settings shape. Search published templates and Voxel-referenced revisions. Replace placeholder/static values with dynamic tags when the value belongs to entity data.
4. Archive/search pages: repair the page/template that actually drives the URL, not just the native CPT archive. Avoid rendering the same records in mutually exclusive sections unless filters make them exclusive.
5. lean-seo output: use the settings workflow and relevant lean-seo reference. Prefer dynamic sources over hardcoded values; choose `voxel:`, `meta:`, `post:`, `relation:`, or `relation_field:` according to where the value really lives.
6. Cache/generated assets: purge in the correct order and regenerate assets before verification when purge removes generated files.

Exit: each fix is applied to the source of truth and no broad unrelated DB/template edits were made.

## Phase 4 — Cache and Regeneration

Entry: source changes are applied.

1. Flush object cache.
2. Purge LiteSpeed/page cache when installed.
3. Clear Elementor generated files after `_elementor_data` changes.
4. Call lean-seo config/cache invalidation after lean-seo settings changes.
5. Regenerate Elementor/generated assets when the local workflow requires it.
6. Verify against cache-busted URLs or a known cache-miss; do not trust a stale `x-litespeed-cache: hit` response.

Exit: a fresh render path has been forced and generated assets are present.

## Phase 5 — Verify All Affected Surfaces

Entry: caches are purged/regenerated.

1. Verify runtime CPT state with WP-CLI.
2. Verify source fields by reading DB/API values back.
3. Verify every affected rendered URL, not only one representative page, when record count is small; otherwise sample each template/path class.
4. Assert no placeholder domains, dynamic-tag leaks, stale text, duplicated mutually exclusive records, or old schema values remain.
5. Parse JSON-LD and verify key nodes/properties against source data.
6. Verify archive/search pages, single pages, markdown twins, sitemaps/permalinks when those surfaces were touched.

Exit: all assertions pass or remaining failures are explicitly listed with blockers.

## Common Pitfalls

- Voxel CPT config storage type matters; `wp option update --format=json` can break sites that expect a JSON string.
- Elementor revisions/custom-template references may still render even when the published template was patched.
- Escaped placeholders can appear as `https:\/\/example.com`, `https:\\/\\/example.com`, or plain URLs; search rendered HTML and DB values.
- If JSON-LD ignores a meta field, check whether the schema config uses a hardcoded `@value:` or the wrong source prefix.
- Page-cache hits can make successful fixes look unapplied; force a real cache miss before debugging code.
