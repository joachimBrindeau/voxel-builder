# CPT Repair Workflow

Repair an existing Voxel CPT when runtime registration, templates, archive/list pages, dynamic entity data, or lean-seo outputs drift from the intended behavior. This workflow is generic: it applies to `events`, services, glossary terms, locations, profiles, testimonials, and future CPTs.

## Entry Criteria

- Site identifier or URL is known.
- CPT key is known or discoverable from the request.
- The problem is tied to Voxel CPT behavior, Elementor/EF template output, Voxel entity data, or lean-seo output.
- A mutating run has permission to write DB/template/config changes.

## Phase 1 — Baseline and Backup

**Entry:** Target site and CPT are known.

1. Capture a DB backup before mutation: `wpdev wp <site> db export /tmp/<site>-before-<cpt>-repair.sql` or equivalent `wp db export`.
2. Record runtime CPT state: public/show UI/archive/rewrite/REST/supports/taxonomies.
3. Record Voxel config state from the Voxel post-type registry option/CLI.
4. List published and non-published records with IDs, slugs, status, and core dates.
5. Sample source fields, post meta, relation fields, and rendered URLs.

**Exit:** There is a rollback file and a written baseline of runtime, Voxel config, source data, and representative rendered output.

## Phase 2 — Classify Fault Surface

**Entry:** Baseline exists.

1. Classify every requested issue into exactly one primary surface using this table:

Classify each issue into exactly one primary surface:

| Surface | Symptoms | Source of Truth |
|---|---|---|
| Runtime registration | wrong label, archive disabled, REST/Gutenberg missing, rewrite mismatch | Voxel CPT config + registered post type object |
| Entity data | wrong field values, stale status, broken excerpts/content/repeaters | Voxel fields, post meta, core post columns |
| Elementor/EF template | placeholder CTAs, duplicated loops, stale static copy, wrong wrapper/template | `_elementor_data`, Voxel template resolution, EF widget schemas |
| Archive/search page | upcoming/past duplication, wrong feed/filter/sort, missing no-results state | page/template driving the route, search widgets, loop config |
| lean-seo output | wrong JSON-LD, thin `.md`, wrong meta/OG/sitemap/permalink/noindex | lean-seo per-target settings/options and source field resolvers |
| Cache/generated assets | fix appears not to apply, stale HTML/CSS, generated CSS 404 | LiteSpeed/object cache, Elementor generated files, lean-seo purge epoch |

**Exit:** Every requested fix has a surface assignment and source-of-truth path.

## Phase 3 — Repair Source of Truth

**Entry:** Fault surfaces are classified.

1. Runtime registration: update the Voxel CPT config, preserving storage type. If the option stores JSON as a string, write a string; do not turn it into an array.
   After a field-definition write, instantiate every changed field through the live Voxel runtime and exercise its `sanitize()` path with a representative valid value. A successful option write is not proof that nested definitions are runtime-compatible. In particular, `select` and `multiselect` `choices` must be a list of `{value,label}` rows, never a value-to-label object.
2. Entity data: update source fields only. For date/status fields, derive status from schedule/end-date policy and write the canonical field used by templates/schema.
3. Elementor/EF templates: patch `_elementor_data` only after reading the real widget/settings shape. Search published templates and Voxel-referenced revisions. Replace placeholder/static values with dynamic tags when the value belongs to entity data.
4. Archive/search pages: repair the page/template that actually drives the URL, not just the native CPT archive. Avoid rendering the same records in mutually exclusive sections unless filters make them exclusive.
   After any filter/taxonomy rename or deletion, audit stored search configs across every `_elementor_data` row — see [`archive-search-pages.md`](archive-search-pages.md) §Stored Search Config Drift. `elementor:lint` and `voxel:filters --audit` do not detect this drift.
5. lean-seo output: use the settings workflow and relevant lean-seo reference. Prefer dynamic sources over hardcoded values; choose `voxel:`, `meta:`, `post:`, `relation:`, or `relation_field:` according to where the value really lives.
6. Cache/generated assets: purge in the correct order and regenerate assets before verification when purge removes generated files.

**Exit:** Each fix is applied to the source of truth and no broad unrelated DB/template edits were made.

## Phase 4 — Cache and Regeneration

**Entry:** Source changes are applied.

1. Flush object cache.
2. Purge LiteSpeed/page cache when installed.
3. Clear Elementor generated files after `_elementor_data` changes.
4. Call lean-seo config/cache invalidation after lean-seo settings changes.
5. Regenerate Elementor/generated assets when the local workflow requires it.
6. Verify against cache-busted URLs or a known cache-miss; do not trust a stale `x-litespeed-cache: hit` response.

**Exit:** A fresh render path has been forced and generated assets are present.

## Phase 5 — Verify All Affected Surfaces

**Entry:** Caches are purged/regenerated.

1. Verify runtime CPT state with WP-CLI.
2. Verify source fields by reading DB/API values back.
3. Verify every affected rendered URL, not only one representative page, when record count is small; otherwise sample each template/path class.
4. Assert no placeholder domains, dynamic-tag leaks, stale text, duplicated mutually exclusive records, or old schema values remain.
5. Parse JSON-LD and verify key nodes/properties against source data.
6. Verify archive/search pages, single pages, markdown twins, sitemaps/permalinks when those surfaces were touched.

**Exit:** All assertions pass or remaining failures are explicitly listed with blockers.

## Renaming a CPT or Taxonomy Key

> **Check availability first:** run `wpdev voxel:rekey --help`. If it prints the global
> command list instead of its own usage, the command is not present in your checkout and
> this section does not apply yet — it ships on the `feat/voxel-rekey` branch, which is
> not merged into `main`. Do **not** fall back to a hand-rolled rename: the traps below
> are exactly why this command exists. Stop and report the missing command instead.

Renaming a key is **not** a repair edit to the Voxel registry. Use `wpdev voxel:rekey`;
never hand-edit the registry, search-replace the database, or rename the key in the Voxel
admin. A Voxel key is simultaneously a `wp_posts.post_type` value, a dictionary key in
`voxel:post_types`, an embedded token in Elementor control *names* (`ts_filter_list__<cpt>`),
a MySQL table suffix (`wp_voxel_index_<cpt>`), a derived relation key
(`hierarchy-<cpt>-ancestors`), and an option/setting-name suffix. Editing one location
leaves a CPT that half-exists.

```sh
wpdev voxel:rekey <site> --from=<old> --to=<new>            # dry-run plan (default)
wpdev voxel:rekey <site> --from=<old> --to=<new> --apply    # backup, rename, rebuild, verify
wpdev voxel:rekey <site> --from=<old> --to=<new> --verify   # residual check only
wpdev voxel:rekey <site> --from=<old> --to=<new> --type=taxonomy
```

Two traps this command exists to prevent:

- **Public URLs follow the key, not the slug field.** Voxel only honours
  `settings.permalinks.slug` when `settings.permalinks.custom` is `true` (and
  `options.archive.custom_slug` only when `options.archive.slug` is `'custom'`). With the
  usual inert defaults, renaming the key moves every public URL even though a slug field
  holding the old value is still visible in the registry. `--urls=preserve` (the default)
  pins the old path by activating those switches; `--urls=follow` moves URLs deliberately
  and requires you to add redirects.
- **Grepping for the old key is the wrong success test.** `glossaire` is a substring of
  `glossaire_category`, a *different* taxonomy, and of unrelated relation keys and body
  copy. `--verify` instead proves completeness by idempotence (re-running the rule table
  must find nothing) plus delimited-identifier survival.

Rollback is two steps: `wpdev backup:restore <site> <backup>.sql.gz --yes` (not
`db:import`, which does not gunzip), **then** drop the index table the rename created,
since a dump cannot remove a table added after it was taken. The command prints both.

To extend coverage, add the storage location to the rule table in
`cli/src/utils/voxel/rekey/rules.ts` — the single spec that both the dry-run and the apply
execute — rather than editing the applier. See
`docs/solutions/voxel-rekey-post-type-taxonomy-keys.md`.

## Common Pitfalls

- Voxel CPT config storage type matters; `wp option update --format=json` can break sites that expect a JSON string.
- Voxel can load malformed nested field definitions without failing until content is sanitized. Verify changed repeater children through the live field runtime; object-shaped select choices crash native `Select_Field::sanitize()`.
- Elementor revisions/custom-template references may still render even when the published template was patched.
- Escaped placeholders can appear as `https:\/\/example.com`, `https:\\/\\/example.com`, or plain URLs; search rendered HTML and DB values.
- If JSON-LD ignores a meta field, check whether the schema config uses a hardcoded `@value:` or the wrong source prefix.
- Page-cache hits can make successful fixes look unapplied; force a real cache miss before debugging code.
