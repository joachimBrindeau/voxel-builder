# lean-seo crawl / permalinks / linking — indexing, URL structure, Voxel CPTs

Three modules that govern how crawlers reach and traverse a Voxel site. Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) first.

## Crawl module — sitemap, robots, HTML sitemap, noindex

`modules/crawl/` (files: `sitemap.php`, `robots.php`, `html-sitemap.php`, plus `indexnow.php`, `sitemap-xsl.php`). Categories: `crawl`, `noindex`, `ai_crawler`.

### XML sitemap — CPT enumeration

Sitemap output is intentionally minimal: a featured image emits only the canonical `<image:loc>` element. Do not add deprecated `<image:title>` or `<image:caption>` children; deploys that change sitemap output require a rewrite flush plus cache purge and a fetch of both the root and representative per-CPT sitemap.

`lean_seo_get_sitemap_post_types()` (`includes/helpers.php`, memoized) is the single source:

```
types = get_post_types(['public'=>true])
      + lean_seo_sitemap_extra_types()      // tweak 'sitemap_extra_types' CSV + filter
      - lean_seo_sitemap_exclude()          // attachment, internals, noindex types, tweak 'sitemap_exclude_types'
```

**The list settings live in the `tweak` category, NOT `crawl`** (`sitemap_extra_types`, `sitemap_exclude_types`, `sitemap_high_priority_types` — default `['page']`). So **any Voxel CPT registered `public=true` is auto-included** — no per-CPT opt-in. To drop one: flag it noindex (below) or add its slug to `tweak.sitemap_exclude_types`. `lean_seo_is_sitemap_post_type($pt)` is the shared membership gate used by crawl/IndexNow/llms. The `crawl` category itself holds toggles like `sitemap_index` (flat vs split-index mode). Sitemap is index-mode-optional, batched (`LEAN_SEO_SITEMAP_QUERY_BATCH=2000`), transient-cached 1h, per-post entries rendered via `lean_seo_voxel_render_groups()`. Geo entries pull Voxel `geo-lat`/`geo-lng`.

### Noindex decisions — per-CPT + per-post overlay

`lean_seo_noindex_post_types()` (config.php, filter `lean_seo_noindex_post_types`) = `['attachment']` + any scope where the per-CPT `NOINDEX_POST_TYPE` meta kind (the Meta module's "Noindex content type" toggle) is enabled. **This list is subtracted from the sitemap too**, so flagging a Voxel CPT noindex removes it from robots-meta, XML sitemap, HTML sitemap, and llms in one move.

On top of type-level selection, `lean_seo_post_is_index_excluded($post)` (`includes/helpers/noindex.php`) is the SEO index-exclusion SSOT: non-published state, noindex post type, per-post `_lean_seo_noindex`, primary-org duplicate, titleless placeholder, and excluded URL path. `lean_seo_post_is_publicly_discoverable($post)` adds password privacy plus sitemap/crawl-corpus membership. Every plugin-owned discovery path must use one of these two predicates rather than repeating a partial `post_status` check: XML flat/type sitemaps and their index, HTML sitemap, llms indexes/full output, direct or negotiated markdown and its advertised actions/head links/cache/CLI regeneration, singular/archive schema and post-ID relations, IndexNow, internal-link generation/detection/acceptance, author/profile canonicalization, and frontend compatibility links. The other `noindex_*` meta kinds gate search/404/paginated/archive-subpages/empty-taxonomy/password-protected views.

Noindex mutations are lifecycle events, not only render-time decisions. Per-post meta add/update/delete purges stored markdown, sitemap/llms/page caches, and stale internal-link rows; type/path/list option changes flush settings and discovery caches and discard generated suggestions so excluded records cannot remain advertised from cached state.

For release verification, distinguish storage from rendered behavior: a per-post noindex removal passes only when `_lean_seo_noindex` is absent (`metadata_exists(...) === false`) and the served page has no noindex directive. Use `wpdev voxel:apply-content` with a prepared hash-locked manifest and explicit JSON `null` for atomic metadata deletion; retain its rollback bundle. After the write, purge, regenerate stored Markdown, and audit every touched URL with redirects disabled so an old URL cannot pass by silently following a chain.

The discovery outputs have different contracts and must be checked independently:

- XML sitemap: canonical indexable URLs only.
- `/llms.txt`: bounded curated index; configured featured IDs may be required but the hard cap still applies.
- `/llms-full.txt`: complete discoverable corpus.
- Per-post `.md`: current generated content, including configured structured repeater projections.

Keep machine-readable counts and per-URL results. A corpus-level total without the touched-ID membership list is insufficient release evidence.

### robots.txt + AI crawlers

`robots.php` → `lean_seo_robots_txt_lines()` emits the standard block + one `Disallow:` per `lean_seo_noindex_paths()` pattern + llms.txt pointers + the AI-crawler block from `lean_seo_settings_map('ai_crawler')` (category `ai_crawler`, a `bot-name => allow|disallow` map, bot names validated `^[a-zA-Z0-9_-]+$`) + `Sitemap:` lines. `indexnow.php` pings IndexNow on publish. HTML sitemap is the `[sitemap]` shortcode, rendering hierarchical types as a `post_parent` tree and non-hierarchical types grouped under their archive link, filtered through the same `lean_seo_post_is_index_excluded()` so it matches XML exactly.

## Permalinks module — URL structure + parent nesting

`modules/permalinks/` (files: `permalinks.php`, `breadcrumbs.php`, `inc/url-resolution.php`, `inc/canonical-uri.php`, `inc/url-generation.php`, `inc/redirects.php`, `inc/meta-box.php`, `inc/default-parent.php`, `inc/auto-parent.php`). Categories: `permalink_default`, `permalink_nesting`.

### Canonical-URI SSOT — `_lean_seo_uri`

lean-seo is a native permalink engine that derives clean URLs from the **`post_parent` ancestor chain** and stores the result in one indexed post meta, `_lean_seo_uri` (const `LEAN_SEO_URI_META_KEY`, e.g. `services/discovery/early-stage-biotech`, no leading/trailing slash). Generation (`lean_seo_build_uri` — walks `get_post_ancestors()`, cleans slugs, strips the front-page slug) and reverse resolution (`lean_seo_resolve_uri_meta` — a single indexed `meta_query`) key off the **same** string, so the round-trip is symmetric and path-independent (posts are addressed by `page_id`/`p`). A missing/stale `_lean_seo_uri` falls back to legacy path resolution — run the CLI backfill after import/migration.

### Request-filter query-var contract

`inc/url-resolution.php` hooks `request` at priority 1, **after** core and CPT rewrite rules have already matched the raw path and set their own query vars. A clean lean-seo path therefore arrives carrying vars that describe the wrong target — most often core's generic `([^/]+)/([^/]+)/?$ ⇒ attachment` rule, which turns any two-segment taxonomy path into an attachment lookup. Both resolution branches must start from `lean_seo_resolution_clear_vars()`, the single owner of that cleanup (`pagename`, `name`, `error`, `attachment`, `post_type`, `p`, `page_id`, plus every public/managed post type and its `query_var`). Setting the resolved var while leaving the stale one in place lets WordPress serve the stale match: a taxonomy archive silently 301s to an identically-slugged attachment, and every lean-seo head tag, canonical, and JSON-LD block disappears from that URL. When adding a new resolution branch, clear first, then set.

**Structural post types** come from public hierarchical CPTs plus Voxel-owned hierarchy types exposed through `voxel_addon_hierarchy_post_parent_owned_cpts`. `lean_seo_permalink_nesting_post_types()` filters that list to public, viewable, non-built-in CPTs with a safe, unique rewrite base. `lean_seo_permalink_managed_post_types()` includes `page`, configured default-parent CPTs, and only the structural CPTs whose Lean SEO nesting switch remains enabled. Persist gate: pages always; non-page CPTs only when `post_parent > 0`.

### Parent-derived URLs + auto-parent

Two auto-parent behaviors (`inc/auto-parent.php`, closures un-hooked during their own write to avoid recursion):

- **CPT auto-parent on creation** — new non-`page` posts get a default parent via `lean_seo_apply_default_parent()`.
- **Pages under front page** — new pages with no parent are re-parented under `page_on_front`.

### Per-CPT default parent

The `permalink_default` category stores one `page_select` row per managed non-`page` CPT (`<cpt> => {value:<parent_page_id>}`). `lean_seo_apply_default_parent($id,$prev,$dry)` classifies via `lean_seo_default_parent_status()` (`applied`, `already_default`, `manual_parent`, `manual_opt_out`, `no_default`, …) and only `wp_update_post` on `applied`. The default must be a published `page`, not self/ancestor. `_lean_seo_parent_manual` marks an explicit divergence and blocks auto-application (set/cleared by the admin **Parent Page** meta box, `inc/meta-box.php`). Voxel relations feed the managed-type list through the `voxel_addon_hierarchy_*` filters above.

### Per-CPT public URL nesting

The required virtual `permalink_nesting` category stores one boolean row per eligible structural CPT (`<cpt> => {value:"1"|"0"}`). It defaults to `1`:

- `1` — publish the ancestor-derived nested URL and persist `_lean_seo_uri`.
- `0` — preserve `post_parent` and derived relations, but publish `/rewrite-base/slug/`; old nested GET/HEAD requests 301 to the flat canonical.

Disabling nesting is rejected when the CPT has an unsafe or conflicting rewrite base, or when existing posts contain duplicate slugs that would collide once flattened. While flat, `wp_unique_post_slug` enforces CPT-wide slug uniqueness. Option add/update/delete hooks reconcile `_lean_seo_uri`, invalidate rewrite health, and schedule the shared verified repair after all rule producers register.

### Rewrite health — persisted rules are a derived cache

Lean SEO owns an ordered manifest for every enabled plugin rewrite producer: flat CPT rules, sitemap endpoints (including conditional split sitemaps), and llms endpoints. On `init` priority 99 it compares the manifest with the persisted `rewrite_rules` option. A matching signature is only an audit marker; persisted rules are verified on every request, so stale or corrupted rules self-repair after a file-only deploy with no activation hook or plugin version bump.

Repair uses an atomic five-minute lock, a failure-only five-minute backoff, `flush_rewrite_rules(false)`, post-flush verification, and one cache purge. Activation only invalidates the signature; the first complete `init` owns repair. Healthy requests do not flush or purge.

Use these read-only deployment proofs locally and remotely:

```bash
./wpdev wp <site> rewrite list --match='<representative-path>' --format=table
./wpdev remote:wp <site> rewrite list --match='<representative-path>' --format=table
```

For a flat CPT, confirm the exact one-segment rule precedes broader rules with the same rewrite base.

### Automatic historical redirects

When a published post slug or parent changes through normal WordPress APIs, the enabled Redirects module snapshots the old canonical root/subtree before the row changes and reconciles after `_lean_seo_uri` persistence. Every changed root/descendant path becomes an active exact 301 in one transactional batch. Moves back to a historical live path delete the stale source first, so the live canonical never redirects away.

The redirects table is the only persisted redirect source. Its repository normalizes active exact graphs to terminal one-hop destinations, rejects cycles atomically, preserves each source row's status code, leaves wildcard semantics unchanged, flushes its active-map cache once, and purges affected URLs once per committed transaction. If the table is not InnoDB, mutations fail closed while existing redirects continue serving read-only.

### Voxel author/profile URL canonicalization

Voxel rewrites `author_base` to the `profile` CPT, producing `/profile/<nicename>` for author archives. lean-seo canonicalizes those to the linked profile post's parent-derived permalink (substrate §author↔profile) so sitemap + canonical + theme links all agree — otherwise duplicate URLs.

### Breadcrumbs

`breadcrumbs.php` → `lean_seo_breadcrumb_trail()` (shared with schema so they never diverge) walks the same `get_post_ancestors()` chain on singulars (`lean_seo_post_text_value(...,'title')`), and derives archive/taxonomy ancestors from the URL path via `get_page_by_path()`.

### WP-CLI surface — `wp lean-seo permalinks <sub>`

`includes/cli/permalinks.php` (loaded only under `WP_CLI`):

- **`backfill [--dry-run]`** — compute + persist `_lean_seo_uri` for every published managed-type post; idempotent; reports written/cleared per type.
- **`parent-backfill [--dry-run] [--post-type=<slug>] [--previous-default=<id>]`** — apply configured default parents to eligible posts; never overwrites manual parents; `--previous-default` migrates posts still under a prior default; re-persists the URI subtree per applied post.
- **`verify [--format=...]`** — read-only coverage report (with-URI / legitimately-empty / MISSING) + a collision report (posts sharing a `_lean_seo_uri`).

## Linking module — internal link suggestions

`modules/linking/` (category `linking`). Generates automated internal-link suggestions with manual approval (admin: **Internal Linking**, `lean_seo_linking_admin_page`). Its selectable field catalog is Voxel-aware — `voxel:post_types` is decoded into selectable `meta:<key>` fields — and its hierarchy enforcement matches either native `post_parent` **or** a Voxel relation meta (single ID / serialized / JSON / CSV). Files: `modules/linking/inc/admin.php`, `inc/ajax.php`, `inc/fields.php`.

## Configure

```bash
wp option get lean_seo_crawl            # sitemap_index toggle, etc.
wp option get lean_seo_noindex          # path patterns
wp option get lean_seo_ai_crawler       # bot allow/deny map
wp option get lean_seo_tweak            # sitemap_extra_types / _exclude_types / _high_priority_types (CSV)
wp option get lean_seo_permalink_default
wp option get lean_seo_permalink_nesting # per-CPT nested (1) vs flat (0) public URLs
# after permalink/parent changes:
wp lean-seo permalinks backfill         # persist _lean_seo_uri corpus-wide
wp lean-seo permalinks parent-backfill  # apply configured default parents
# rewrite health repairs and verifies persisted rules automatically
```

## Gotchas

- **List settings are in `tweak`, not `crawl`** — `sitemap_extra_types` / `sitemap_exclude_types` / `sitemap_high_priority_types` live in `lean_seo_tweak`; looking in `lean_seo_crawl` for them is the common miss.
- **Rewrite health is automatic** — split-sitemap, llms, flat permalink, module-toggle, and nesting changes invalidate the shared manifest signature; a complete `init` repairs and verifies persisted rules. Do not add a parallel direct flush path. Use the read-only `rewrite list` commands above for rollout proof.
- **File deploys still need canary proof** — runtime self-repair removes the manual flush dependency, but a public representative route and rule-precedence check remain required before declaring a deployment healthy.
- **Run `backfill` after import/migration** — a missing/stale `_lean_seo_uri` silently falls back to legacy resolution; slug/parent edits move the whole descendant subtree (cascade + epoch bump handle it).
- **Backfill order** — configure `permalink_default` *before* `parent-backfill`; it reads the configured default.
- **Cache purge** — sitemap/HTML/permalink/noindex outputs are transient-cached 1h and page-cached (LiteSpeed); purge after writes (`./wpdev wp <site> litespeed-purge all` or `lean_seo_purge_all()`).
- **Memoization** — `lean_seo_get_sitemap_post_types()` / `lean_seo_noindex_post_types()` are `static`; registration/setting changes within a request won't re-read.
- **Sitemap inclusion** — a Voxel CPT missing from the sitemap is usually non-public, in `sitemap_exclude_types`, noindex, or titleless — not a bug.
- **Author duplicate URLs** — if `/profile/...` and the CPT permalink both index, the author-canonicalization filter isn't active (Voxel/voxel-addon inactive or overridden).
