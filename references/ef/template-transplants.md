# Elementor / Voxel template transplants + template JSON surgery

Use when editing Voxel/Elementor template JSON, copying a section **wrapper** from one
template/page to another, changing EF wrapper/card structure, running a site-wide copy/de-AI
pass over stored template data, or debugging a rendered template section on a `wpdev` site.

This is the **template-JSON** companion to the build/migrate pipeline: it covers reading raw
`_elementor_data`, transplanting a visual wrapper, and verifying the render — without inventing
widget shapes (still read the EF SSOT: [`ef-widgets.md`](ef-widgets.md) / [`widgets.md`](widgets.md)).

## Workflow

1. Identify source and target templates with `wpdev elementor:templates <site>` and
   representative URLs/posts with WP CLI.
2. Inspect both flattened and raw structure:
   - `wpdev elementor:tree <site> <post_id>` for quick shape.
   - `wpdev elementor:dump <site> all --post <post_id> --json` for searchable widget/settings inventory.
   - Raw `_elementor_data` for the actual nested `elements` relationships before edits.
3. For site-wide copy cleanup / de-AI passes, include Elementor and SEO storage, not only post
   bodies — see [`../curation/sitewide-ai-marker-cleanup.md`](../curation/sitewide-ai-marker-cleanup.md)
   for the full scan scope, double-JSON-encoded `ef-wrapper` edit hazard, and TranslatePress miss.
4. For wrapper transplants, copy visual wrapper settings, not blindly all source data:
   - preserve source display keys like `tag`, `cols`, `bg_color`, `bg_media_enabled`, `bg_media_type`.
   - adapt target data/feed keys like `_vx_loop`, `ts_choose_post_type`, relation tags, manual
     post IDs, and visibility rules.
5. Write changed template JSON through `wpdev elementor:import <site> <post_id> <json> --save`; do
   **not** rely only on direct `update_post_meta` — import runs the schema gate, migrations, and
   Elementor CSS save.
6. Run focused verification:
   - `wpdev elementor:lint <site> --post <post_id>`
   - `wpdev rebuild <site> --only purge`
   - browser/MCP visual check on real target URLs.
7. In browser checks, verify more than presence of markup:
   - computed background/color/tag/class for copied wrapper.
   - expected heading/body/feed rendered text.
   - widget/feed count and empty-section height.
   - representative target posts for each post type.

## Minimal verification loop

1. `wpdev elementor:lint <site> --post <template_id>`
2. `wpdev elementor:import <site> <template_id> <json> --save`
3. `wpdev rebuild <site> --only purge`
4. Browser-check representative URLs for each target post type.
5. Inspect DOM/computed styles for the copied wrapper (`section.ef-wrapper`, background token
   RGB, feed widget count, expected text).

## Pitfalls

- `wpdev elementor:dump` can flatten nodes for inspection. Do **not** infer parent/child or
  sibling boundaries from dump output alone; inspect raw `_elementor_data` nested `elements`
  before editing.
- A visible page section may span several top-level sibling nodes, not one wrapper. Search-term
  hits often identify only the heading card, while feed/cards live in later sibling wrappers.
- Homepage/manual sections may use static/manual post IDs. Target templates often need
  relation-driven sources (`@post(testimonials)`, etc.). If a copied section renders empty, check
  target relation data and feed source **before** changing CSS.
- A wrapper can be structurally present but visually empty. Treat this as an incomplete transplant
  until content/feed render is verified.
- When cloning Elementor subtrees into the same site, **regenerate IDs recursively for every
  cloned node**, not only top-level wrappers. Duplicate child IDs can make frontend output appear
  stale or drop cloned content even when `_elementor_data` shows the new section.
- Do not assume "replace Voxel widget with EF widget" is possible just because the visual card is
  EF. Homepage testimonial patterns can use EF wrappers/cards for content while still using Voxel
  `ts-post-feed` for the feed source. Search actual `widgetType` values first, then replace only
  the parts that have an existing EF widget/atomic.
- Direct meta writes are ok for **scratch staging only**; always re-import saved JSON with
  `--save` before claiming done.
- Do not conflate public landing pages with searchable archive pages. Check sibling patterns
  first: if the site has pairs like `/blog` (landing) and `/recherche/articles` (search archive),
  preserve that split for new CPTs too. See [`../voxel/voxel-lean-seo-routing.md`](../voxel/voxel-lean-seo-routing.md)
  and [`../../workflows/archive-search-pages.md`](../../workflows/archive-search-pages.md).

## Related references

- [`../voxel/voxel-lean-seo-routing.md`](../voxel/voxel-lean-seo-routing.md) — when landing/archive
  URLs, lean-seo redirects, LSCache, and Voxel CPT prefixes overlap during a transplant.
- [`../curation/sitewide-ai-marker-cleanup.md`](../curation/sitewide-ai-marker-cleanup.md) — the
  site-wide de-AI pass over posts, excerpts, Elementor JSON, lean-seo meta/markdown, Voxel fields,
  and TranslatePress tables.
