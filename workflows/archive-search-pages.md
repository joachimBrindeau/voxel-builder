# Archive And Search Page Workflow

Build or repair the public searchable page for one Voxel post type. This route owns the
archive/search URL and result surface; general templates stay in the build route.

## Scaffolding A Native CPT Archive

`wpdev voxel:archives <site>` builds every eligible CPT archive template to one canonical
shape, so do not hand-author an archive tree before running it. The shape it emits is the
SSOT for this route: `main` > `header` (ef-card carrying the single h1 plus a link to the
CPT's search page) > `section` with `mode=pagination` owning `cols`/`rows` > the
`mode=template` loop wrapper. Useful flags: `--cpt`, `--columns`, `--rows`, `--force` to
rebuild an existing document, `--dry-run`, and `--skip-routing`.

Two site facts decide whether an archive is reachable, and neither is visible in the tree:

1. **Voxel's render gate.** Voxel renders an archive template only when Elementor claims the
   document — `_elementor_edit_mode=builder` AND non-empty `_elementor_data`. A document can
   hold perfectly valid JSON and still be skipped, so never infer health from byte count.
2. **Voxel's archive switch**, at `voxel:post_types[<cpt>].settings.options.archive.has_archive`
   (`enabled|disabled|auto`). `disabled` registers the CPT with `has_archive=false`, making the
   URL unreachable no matter how good the document is. The command enables it by default.
3. **Voxel's native archive query**, at
   `voxel:post_types[<cpt>].settings.options.default_archive_query`, which ships `disabled`.
   While off, Voxel's search controller neuters the main query on the archive
   (`post__in=[0]`, `posts_per_page=1`), because its own AJAX search feeds fetch their own
   results. An EF loop archive renders FROM the main query, so the symptom is asymmetric and
   easy to misread: page 1 renders fine while every `/page/N` returns 404. Owning an archive
   means owning its query — `voxel:archives` enables this for every routed CPT and
   `--verify` fails when it is off. The built-in `post` type needs it too, so set it before
   any per-type routing branch that can return early.

Run `wpdev voxel:archives <site> --verify` to assert both, plus registration, data presence,
and published-post count, for every eligible CPT. It writes nothing and exits non-zero on any
failure, so it is the gate to cite — do not write a throwaway render probe.

## The Card A Loop Actually Renders

An archive loop renders the CPT's **primary** card (`templates.card`), not the sized entries in
`custom_templates.card[]`. Those two can disagree, and when they do the failure is silent: the
per-size audit reads fully green while `templates.card` points at an empty or deleted document,
so every result renders as blank markup inside a correctly-built grid. A live archive returning
HTTP 200 with an empty results `section` is this bug, not a query or routing fault.

`wpdev voxel:cards <site> --audit` reports both halves — the sized slots and a "Primary card
defects" table. Voxel auto-creates an empty `<CPT>: Preview card` placeholder when a CPT is
created; if nobody ever designs it, it stays empty and silently breaks every feed and archive
for that CPT. Repair by scaffolding the sized cards (`voxel:cards <site> --type=<cpt>`), which
also normalizes `templates.card` to the large variant — the convention every CPT here follows.
Then rebuild the archive with `--force` so its loop picks up the new card id.

Clean up the dead placeholder through `wpdev voxel:templates <site> --incomplete` (which lists
empty-but-bound documents) and `--prune` (which trashes marked templates and strips dangling
option pointers). Do not hand-delete posts or hand-edit the registry.

Never guess a `/search/<cpt>` link target: WordPress answers ANY unmatched `/search/*` path
with a native search page at HTTP 200, so a guessed link is a soft 404 that looks reachable.
Resolve real published pages under the search root by slug (tolerating the plural/singular
gap between a CPT key and a page slug) and read permalinks rather than building them.

A CPT archive does not outrank a real WordPress page on the same URL. When a page already
owns `/<cpt>`, the archive renders correctly yet stays unreachable there; resolve that
ownership explicitly instead of assuming the archive won.

CLI writes to `_elementor_data` go through `cli/src/utils/elementor/write-document.php`, the
single shared writer. A guard test rejects any new `update_post_meta`/SQL writer outside that
directory; add a caller, never a second write path.

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
2. Configure the EF query-backed loop for the target post type. The loop is an `ef-wrapper`
   carrying FOUR coordinated settings; a partial set silently degrades to raw iteration:
   `mode` = `template`; `_vx_loop` = `{tag: "@site(loop_<cpt>)", limit, offset}` (vx-loop
   envelope); `_ef_loop_query` = `{post_type, order, search_form}` (ef-loop-query envelope);
   `template_id` = a registered card id from `voxel:post_types[<cpt>].custom_templates.card[]`
   (never hand-authored — core rule 3). `ef_voxel_loop_query_config()` returns null when BOTH
   `order` and `search_form` are empty, so always set one. Read valid `order` keys live from
   `voxel:post_types[<cpt>].search.order[].key`; `order` maps to Voxel `sort`, a bound search
   form overrides it, and `rand` is an EF sentinel realized as SQL RAND(), not a Voxel sort.
   These two envelopes are runtime-injected reserved cells: their shapes come from
   `schemas/parts/rows/_envelope-loop.schema.json`, NOT the widget codegen SSOT.
3. Put the loop and the LAYOUT on SEPARATE wrappers. A `mode=template` wrapper suppresses its
   own shell (`should_suppress_template_shell`, default true) and hoists rendered cards into
   the PARENT, so `cols`/`rows` set on the loop wrapper itself are silently discarded. Grid
   tracks and pager mode belong on the parent; `mode=pagination` there gives native EF paging
   (items per page = cols x rows, exposed as `--ef-items` / `--ef-pager-cols` /
   `--ef-pager-rows`). EF paging needs no `ts-*` widget.
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
2b. For an EF query-backed loop, run `wpdev elementor:verify:loop-render <site> --url <path>
   --grid <layout-wrapper-selector> --card <card-selector> --expect-cards <n> --expect-cols <n>`.
   It asserts visible card count, COMPUTED grid tracks, distinct card column offsets, pager
   page size, dynamic-tag leakage, and console/page errors in one pass. A collapsed grid
   returns HTTP 200 with the correct card count and passes every text check — only the
   computed-style and column-offset assertions catch it. Never hand-roll this probe.
3. Compare a complete and sparse result record so visibility/fallback behavior is exercised.
4. For a page-backed archive, prove the rendered Elementor document ID and canonical query
   owner, not just the requested URL. A `200` from the wrong WordPress template is a failure.

**Exit:** The archive/search URL, EF/approved legacy surface, index, results, and browser
assertions all pass.

## Stored Search Config Drift

Renaming or deleting a Voxel filter or taxonomy does NOT rewrite the search widgets that
reference it. `ts_filter_list__<cpt>[].ts_choose_filter`, `ts__<cpt>__taxonomies`, and the
per-CPT `ts_card_template__<cpt>` keys keep the old key forever, and the widget silently
renders nothing for that row. `elementor:lint` and `voxel:filters --audit` both pass: lint
does not know Voxel's filter registry, and the audit only inspects `voxel:post_types`, not
`_elementor_data`. Audit stored configs explicitly after every filter/taxonomy rename.

1. Read the live key sets first — filters live at `voxel:post_types[<cpt>].search.filters[].key`
   (NOT `[<cpt>].filters`, which does not exist), taxonomies at `get_object_taxonomies(<cpt>)`.
2. Scan every `_elementor_data` row, not just the page you were sent to. Drift spreads across
   archive pages, `elementor_library` templates, and single-term templates alike.
3. Classify each stale key as rename (a live key covers the same source field) or drop.
   Carry the row's `<oldkey>:*` / `<oldkey>__*` option keys across on a rename; strip them on
   a drop, or they linger as dead payload.
4. Drop `heading-*` rows left with no filter before the next heading — they label nothing.
5. Prune per-CPT settings whose post type no longer exists. Guard the prune with a registry
   check (`post_type_exists('elementor_library')`): under `--skip-plugins` the plugin CPTs are
   unregistered and the prune would delete live settings. That guard also means such a mutator
   cannot run through `elementor:mutate`, which forces `--skip-plugins` — run it with
   `wpdev wp <site> eval-file`, then reproduce the tail manually: `elementor:lint`,
   `elementor:validate`, `wp elementor flush-css`, `wpdev purge`.
6. Re-run the audit to zero, then verify rendered filters, not just HTTP 200. Flushing
   Elementor CSS 404s every per-post stylesheet until each page is re-rendered once, so
   fetch the affected URLs before trusting a console scan.

## Rationalizations To Reject

- Do not invent a new archive pattern before inspecting siblings.
- Do not repurpose a marketing page silently.
- Do not add Voxel search/feed widgets to a new EF build.
- Do not report success from a tree or HTTP check without rendered result/filter evidence.
