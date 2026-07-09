# Archive/search pages

Use this workflow when building or fixing a public searchable archive page for a Voxel post type. New listing surfaces must use Elementor Framework widgets (`ef-*`) and `ef-wrapper` template/loop composition; Voxel search/feed widgets are preservation-only legacy nodes, not new build targets.

## Entry criteria

- Target site is known.
- Target post type key is known.
- Existing archive/search pages have been inspected before any write.
- Desired URL is known and checked against sibling URLs.

## Mistake guards

- Do not disable a Voxel archive to fix a URL conflict; search pages need archive/search wiring.
- Do not invent archive structure from scratch when sibling `recherche/*` pages exist.
- Do not reuse a standalone marketing page as the search archive unless siblings do the same.
- Do not hardcode project-specific titles, page IDs, slugs, or post type keys in this workflow.
- Do not add or rebuild Voxel `ts-*` widgets. Preserve existing ones verbatim only when the task explicitly keeps the legacy search page pattern.

## Phase 0 — Inspect sibling pages

1. List children of the search root page:

   ```bash
   ./wpdev wp <site> post list --post_type=page --post_parent=<search_root_id> --fields=ID,post_title,post_name,post_parent --format=csv
   ```

2. Inspect at least two sibling Elementor trees:

   ```bash
   ./wpdev elementor:tree <site> <sibling_page_id>
   ```

3. Export the closest sibling page before copying:

   ```bash
   ./wpdev elementor:export <site> <sibling_page_id>
   ```

## Phase 1 — Preserve URL pattern

For Klarc-style archives, searchable archive pages live under the search root, e.g. `recherche/<plural-slug>`, matching siblings such as `recherche/services`, `recherche/recrutement`, and `recherche/glossaire`.

Create or update a child page of the search root with:

- `post_parent` = search root page ID
- `post_name` = target archive slug
- title = `Recherche de …` / localized equivalent

## Phase 2 — Copy and retarget Elementor data

Copy the closest sibling archive page. In copied `_elementor_data`:

- update hero card heading/body copy
- configure an EF `ef-wrapper` loop/template surface for `<post_type>` results
- preserve any existing Voxel `ts-search-form` / `ts-post-feed` nodes verbatim only when the task is to keep legacy search behavior
- preserve wrapper/card layout from sibling page

Use `./wpdev elementor:import <site> <page_id> <json> --save` when it writes successfully. If import gate passes but page meta remains empty, write `_elementor_data`, `_elementor_edit_mode=builder`, and `_elementor_template_type=wp-page`, then regenerate CSS and purge caches.

## Phase 3 — Rebuild and verify

Run:

```bash
./wpdev rebuild <site> --only reindex,css,purge --recreate
./wpdev elementor:tree <site> <page_id>
```

Verify:

- URL returns HTTP 200.
- Canonical URL equals target `recherche/<slug>`.
- tree shows the EF loop/template wrapper for `<post_type>` results, or unchanged preserved legacy Voxel search/feed nodes when explicitly retained.
- Voxel index status for the post type is `ok` and published count equals indexed count.
- Browser-rendered page shows heading and search/filter UI.

## Exit criteria

- Archive/search page exists at expected `recherche/<slug>` URL.
- Elementor data follows sibling archive pattern.
- Voxel post type remains indexed/searchable.
- Related standalone landing pages, if any, are not silently repurposed.
