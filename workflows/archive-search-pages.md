# Archive And Search Page Workflow

Build or repair the public searchable page for one Voxel post type. This route owns the
archive/search URL and result surface; general templates stay in the build route.

## Entry Criteria

1. Site, post type, search-root page, desired URL, and intended legacy-preservation policy
   are known.

## Phase 0 - Inspect Sibling Pattern

**Entry:** Entry criteria are met; no write has occurred.

1. List search-root children and inspect at least two sibling Elementor trees.
2. Select the closest sibling by URL role, filters, result shape, and empty state.
3. Export that sibling and the target page when it already exists.

**Exit:** Sibling pattern, source page id, target page id/status, and rollback exports exist.

## Phase 1 - Define URL And Ownership

**Entry:** Phase 0 sibling evidence exists.

1. Record target `post_parent`, slug, localized title, canonical URL, and post type.
2. Check conflicts with native archives, standalone marketing pages, and sibling routes.
3. Keep native Voxel archive/search wiring enabled; do not solve conflicts by disabling it.
4. When Voxel binds an archive to a regular page, record both the bound page ID and the
   WordPress reading option. A curated page that owns `/blog` independently of the built-in
   `post` archive requires `page_for_posts=0`; otherwise Voxel's `home.php` route can shadow
   the page while the stored Elementor tree remains correct.

**Exit:** One non-conflicting URL/page owner is recorded and existing landing pages remain
separate unless the sibling pattern proves otherwise.

## Phase 2 - Retarget Elementor Data

**Entry:** Phase 1 ownership is unambiguous.

1. Copy the sibling tree and update hero/result copy without importing project-specific ids.
2. Configure an EF wrapper loop/template surface for the target post type.
3. Preserve existing `ts-search-form`/`ts-post-feed` nodes verbatim only when legacy search
   behavior is explicitly retained; never add new `ts-*` nodes.
4. Validate offline, then import with `--save` and read `_elementor_data` back.

**Exit:** Stored target data matches the retargeted tree, sibling layout remains intentional,
and result/filter ownership points to the target CPT.

## Phase 3 - Reindex And Verify

**Entry:** Phase 2 read-back passes.

1. Run `wpdev rebuild <site> --only reindex,css,purge --recreate`.
2. Verify tree, Voxel index/published counts, HTTP 200, canonical URL, browser heading,
   filters/results, empty state, and console/page errors.
3. Compare a complete and sparse result record so visibility/fallback behavior is exercised.
4. For a page-backed archive, prove the rendered Elementor document ID and canonical query
   owner, not just the requested URL. A `200` from the wrong WordPress template is a failure.

**Exit:** The archive/search URL, EF/approved legacy surface, index, results, and browser
assertions all pass.

## Rationalizations To Reject

- Do not invent a new archive pattern before inspecting siblings.
- Do not repurpose a marketing page silently.
- Do not add Voxel search/feed widgets to a new EF build.
- Do not report success from a tree or HTTP check without rendered result/filter evidence.
