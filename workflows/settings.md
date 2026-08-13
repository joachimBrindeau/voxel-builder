# lean-seo Settings Workflow

Configure a lean-seo SEO surface — metadata, schema, markdown-for-agents, or crawl/permalinks/linking — for a Voxel CPT, correctly and site-agnostically. This is a **routing** workflow: pick the surface, then follow that route's phases. Every route shares one substrate (option store + field catalog + Voxel guard layer) documented in [`../references/voxel/lean-seo-settings-substrate.md`](../references/voxel/lean-seo-settings-substrate.md) — read it before any route.

Mandatory companion reads before configuring: the substrate reference (above), plus the one surface reference for your route (linked per route below). These carry the exact option keys, token dialects, and Voxel resolvers; this workflow carries the *process*.

## When to run this workflow

- "Configure lean-seo title/description/OG for the `<cpt>` CPT"
- "Set up JSON-LD schema for `<cpt>` / add a Voxel relation to the schema graph"
- "The markdown-for-agents `.md` twin is missing content" (routes to the markdown surface)
- "Add this CPT to the sitemap / noindex it / fix its permalink parent"
- "Audit whether lean-seo is configured well for this site's CPTs"

For fixing a *rendered page/template* (not SEO config) or for creating the CPT itself, that's Voxel-template work — see the separate `voxel-builder` skill (its `audit` / `cpt-lifecycle` workflows). Configure SEO here **after** the CPT and its fields exist.

## Hard stops

Halt and resolve before mutating:

- Site slug or target CPT/taxonomy is unknown.
- The CPT's field/relation keys have not been read from the live field catalog (`lean_seo_available_field_groups`) — never guess a Voxel field key.
- You are about to write with the wrong token dialect for the surface (see substrate §token dialects).
- The write path would bypass `lean_seo_settings_set()` / the markdown option / the schema option.
- Verification (Phase V) cannot run.

## Entry criteria (all routes)

1. `wpdev` reaches the site (`wpdev wp <site> option get blogname`).
2. Voxel + lean-seo active (`wp eval 'var_dump(lean_seo_has_voxel());'`).
3. The target CPT exists and is public (or in `sitemap_extra_types`).
4. You know which **surface** you are configuring → pick the route.

## Route table

| Surface | Route | Surface reference | Option / store |
|---|---|---|---|
| Title, description, canonical, OG/Twitter, per-CPT noindex | §Route M — Metadata | [`lean-seo-metadata.md`](../references/voxel/lean-seo-metadata.md) | `lean_seo_meta` |
| JSON-LD structured data (incl. Voxel relations) | §Route S — Schema | [`lean-seo-schema.md`](../references/voxel/lean-seo-schema.md) | `lean_seo_schema:{target}` (+ index `lean_seo_schema_targets`) |
| Markdown-for-agents `.md` twin | §Route K — Markdown | [`lean-seo-markdown.md`](../references/voxel/lean-seo-markdown.md) | `lean_seo_markdown_field_maps` (JSON string) |
| Sitemap / robots / noindex / permalink parent / internal linking | §Route C — Crawl & Permalinks | [`crawl-permalinks-linking-reference.md`](../references/voxel/lean-seo-crawl-permalinks.md) | `lean_seo_crawl` / `lean_seo_noindex` / `lean_seo_tweak` (lists) / `lean_seo_permalink_default` / `lean_seo_linking` |

**Other surfaces (no CPT-routing needed — read the reference and apply directly):** 301 redirects → [`lean-seo-redirects.md`](../references/voxel/lean-seo-redirects.md); analytics + Search Console/Bing/Yandex verification → [`lean-seo-code.md`](../references/voxel/lean-seo-code.md); WebP/image handling → [`lean-seo-media.md`](../references/voxel/lean-seo-media.md); SEO-safe 503 maintenance → [`lean-seo-maintenance.md`](../references/voxel/lean-seo-maintenance.md); cache purge / Last-Modified epoch → [`lean-seo-purge.md`](../references/voxel/lean-seo-purge.md). These are per-site or automatic, not per-CPT, so they skip the Phase-0→V routing below — but still verify the rendered/served result.

---

## Phase 0 — Shared preflight (every route)

**Entry:** Entry criteria met; route chosen.

**Actions:**

1. **Read the live field catalog for the target CPT** — this is the agnostic anchor for every route:
   ```bash
   wp eval '$g=lean_seo_available_field_groups("post:<cpt>"); foreach($g as $grp=>$f){echo "== $grp ==\n"; foreach($f as $k=>$l){echo "$k\t$l\n";}}'
   ```
   Record the Core / Voxel / Meta field keys. **Every field/relation you reference later must appear here.**
2. **Dump the current config** for the route's option(s) so you diff, not overwrite:
   ```bash
   wp option get <option_key>            # e.g. lean_seo_schema
   ```
3. **Confirm the token dialect** for this surface from the substrate reference (§token dialects). Wrong dialect is the #1 misconfiguration.

**Exit:** You have the CPT's field-key inventory and the current stored config for the route.

---

## Route M — Metadata

Reference: [`lean-seo-metadata.md`](../references/voxel/lean-seo-metadata.md). Dialect: `%token%`.

**Entry:** Phase 0 done. Catalog + current `lean_seo_meta` in hand.

**Actions:**

1. **Pick the kinds to set** from `lean_seo_meta_setting_kinds()` — typically `TITLE_TEMPLATE`, `DESC_TEMPLATE`, `OG_TYPE`, `DEFAULT_OG_IMAGE`, and any `noindex_*`.
2. **Author templates in `%token%`** using only tokens from the Phase-0 catalog (`%title%`, `%excerpt%`, `%{voxel_field}%`, `%site_name%`, `%sep%`). For a full Voxel dynamic tag, use the `%vx(@post(key))%` wrapper — a bare `%key%` only does a meta fallback. Prefer native fields (`%title%`, `%excerpt%`) over Voxel fields when both carry the SERP-worthy text.
3. **Build the scoped key** (scope = **bare slug**, taxonomies `taxonomy-<slug>`) and write:
   ```bash
   wp eval 'lean_seo_settings_set("meta", lean_seo_build_meta_setting_key(LEAN_SEO_META_KIND_TITLE_TEMPLATE,"<cpt>"), "%title% %sep% %sitename%", "text");'
   ```
   OG image is an **attachment ID**, not a URL. Unscoped kinds (separator, twitter card, global OG) use their bare key. Note the site's `title_meta_key` default is `'h1'` (Voxel) — on a differently-keyed site set the `lean_seo_title_meta_key` filter.

**Exit:** `wp option get lean_seo_meta` shows the new `<kind>_<cpt>` scoped rows.

---

## Route S — Schema

Reference: [`lean-seo-schema.md`](../references/voxel/lean-seo-schema.md). Dialect: `prefix:key|transform`.

**Entry:** Phase 0 done. Catalog + current `lean_seo_schema` in hand.

**Actions:**

1. **Choose the `@type`** (or `@graph` of types) for the CPT from the schema.org vocabulary the module allows (`vocabulary.php`).
2. **Preflight every referenced live Voxel field definition before a data migration.** Deploying a plugin blueprint does not apply that blueprint to the live `voxel:post_types` registry. If a migration introduces a field, prepare the missing definition through `wpdev voxel:field-schema` or the canonical `VoxelConfigStore`, verify read-back, then restart the WP-CLI process so Voxel reloads its field registry before entity writes.
3. **Map each schema property to a source string** using the Phase-0 keys:
   - core → `post:title`, `post:permalink`, `post:date|iso8601`
   - Voxel field → `voxel:<key>` (dot-path for structured values, e.g. `voxel:location.address`)
   - Voxel relation as a list → `{ "@each": "relation:<rel_key>", "value": { ... "related:title" ... } }`
   - single related field → `relation_field:<rel_key>.<field_key>`
   - ancestry → `hierarchy:...`; literal → `@value:...`; reference → `@ref:...`
4. **Validate mentally against `voxel:` vs `meta:`** — always `voxel:` for Voxel fields; `relation:` needs an `@each` wrapper (never assign a bare ID array to a property).
5. **Write the per-target config** into `lean_seo_schema:<cpt>` (one option per target — do NOT write a monolithic `lean_seo_schema`, it's legacy and auto-deleted):
   ```bash
   wp option get "lean_seo_schema:<cpt>" > /tmp/schema.json   # edit the config tree
   wp option update "lean_seo_schema:<cpt>" "$(cat /tmp/schema.json)"
   # register the target in the index if new:
   wp eval 'lean_seo_schema_save_config("<cpt>", json_decode(file_get_contents("/tmp/schema.json"), true));'
   ```

**Exit:** `wp option get "lean_seo_schema:<cpt>"` holds the config; every leaf is a valid source string over Phase-0 keys.

---

## Route K — Markdown

Reference: [`lean-seo-markdown.md`](../references/voxel/lean-seo-markdown.md). Dialect: `@post(key)` in `dtag_fields`. Option: `lean_seo_markdown_field_maps` (standalone JSON string, per-CPT map).

**Entry:** Phase 0 done. Current `lean_seo_markdown_field_maps` in hand.

**Actions:**

1. **Assemble the per-CPT map** from the shapes `text_fields`, `sections`, `repeaters`, `dtag_fields`, `relations` (see reference). Reference only Phase-0 field/relation keys. For repeaters whose row keys differ from the conventional `title`/`question` + `description`/`answer` shape, configure an explicit projection with `label`, `title`, `body`, `url`, and optional `columns` (`field_key => reader label`). Keep the legacy `field_key => section label` form only for conventional rows.
2. **Prefer structured field ownership for reader content.** A CPT with no configured field map always uses the rendered-page HTML-to-Markdown path; this applies uniformly to built-in posts and custom post types and is not a setting. Once any field map is configured, structured fields become the sole output owner; there is no fallback toggle or mixed structured/rendered path. Cover the CPT's complete reader-facing article before saving its first map. For content only available through the rendered template, configure `@post(lean_seo:rendered_html)` explicitly in a `dtag_fields` body. A nonempty `.md` response does not prove a complete map: verify expected repeater rows appear as native reader-facing Markdown sections rather than only inside JSON-LD or incidentally in rendered prose.
3. **Write the option:**
   ```bash
   wp option update lean_seo_markdown_field_maps "$(python3 -c 'import json;print(json.dumps(json.load(open("/tmp/maps.json")),ensure_ascii=False))')"
   ```

**Exit:** `lean_seo_markdown_field_maps` has the CPT map; Phase V confirms parity with the rendered page.

---

## Route C — Crawl & Permalinks

Reference: [`crawl-permalinks-linking-reference.md`](../references/voxel/lean-seo-crawl-permalinks.md).

**Entry:** Phase 0 done. Current `lean_seo_crawl` / `lean_seo_noindex` / `lean_seo_permalink_default` in hand.

**Actions:**

1. **Sitemap inclusion** — public CPTs are auto-included; otherwise add the slug to the `sitemap_extra_types` CSV **in the `tweak` category** (`wp option get lean_seo_tweak`), or remove via `sitemap_exclude_types`.
2. **Noindex** — set the `NOINDEX_POST_TYPE` meta kind (or a `noindex_*` rule) to exclude the CPT / state from indexing (this also drops it from the sitemap + llms).
3. **Permalink parent** — set the CPT's `permalink_default` row (a `page_select` naming the default parent), then backfill existing posts and flush:
   ```bash
   wp eval 'lean_seo_settings_update("permalink_default","<cpt>",["value"=>"<parent_page_id>"]);'
   wp lean-seo permalinks parent-backfill --post-type=<cpt>
   wp lean-seo permalinks backfill          # persist _lean_seo_uri
   wp rewrite flush
   ```
4. **Internal linking** — enable the module; suggestions are generated and require manual approval in the admin.
5. **Deploy changed sitemap output deliberately** — if the XML sitemap emitter or its image/video extensions changed, deploy the plugin, run `wp rewrite flush`, then purge object/page/LiteSpeed caches. Verify a real `sitemap.xml` and representative `sitemap-<cpt>.xml` response: it must contain the canonical `<image:loc>` for featured images and must not reintroduce deprecated `<image:title>` or `<image:caption>` children.

**Exit:** Config written; **`_lean_seo_uri` backfilled**, **rewrite flushed**, and **cache purged** after any permalink/noindex or sitemap-output change.

---

## Phase V — Verify (every route)

**Entry:** The route's write completed.

**Actions:**

1. **Read back the option** and confirm the CPT entry is present and well-formed (`wp option get <option_key>`).
   For schema, reconcile both layers: `wpdev schema:get <site> --json` must list every valid
   `lean_seo_schema:<target>` option in `lean_seo_schema_targets`. An empty index beside valid
   per-target options is derived-index corruption, not "no configs". Repair through the schema
   store/CLI and preserve the per-target options as the content owner. Migration code must verify
   the stored readback; WordPress `update_option()` returns `false` for an already-equal value and
   that is not a failed write.
2. **For a release batch, capture a strict before-state and rollback bundle before writing.** Export the full-site content audit as JSON and parse its summary, not terminal formatting. Build content changes through `wpdev voxel:apply-content <site> --manifest=<file> --prepare`, dry-run the prepared manifest, then apply with `--rollback=<file> --yes`. A field deletion must be an explicit JSON `null`; omission means preserve the current value. Keep the prepared manifest, rollback file, and apply result as release evidence.
3. **Render a real sample post** of the CPT and assert the output:
   - Metadata: `wp eval 'echo wp_remote_retrieve_body(wp_remote_get(get_permalink(<id>)));'` → grep `<title>`, `<meta name="description"`, `og:*`, `<link rel="canonical"`.
   - Schema: fetch the page, extract `<script type="application/ld+json">`, confirm properties resolved (no bare source strings, no missing relations).
   - Markdown: `wp eval 'echo lean_seo_generate_markdown(get_post(<id>));'` → assert expected headings/sections present, **no unresolved** `@post(` / `@author(` / `%token%` / `prefix:key` leak.
   - Crawl/permalinks: fetch the sitemap / robots / the post URL; confirm inclusion/exclusion and the parent-nested URL; check no duplicate author/profile URL.
4. **Prove every touched public URL, not only one sample.** For each URL, record the final status, canonical, robots/noindex state, expected schema nodes, rendered citations, and redirect history with automatic redirects disabled in the crawler. Exact per-post noindex cleanup means the `_lean_seo_noindex` metadata row is absent; an empty or false-like value is not equivalent proof.
5. **Cross-check all discovery surfaces separately.** Confirm every intended URL is in the XML sitemap, the bounded curated `/llms.txt` when selected, and the complete `/llms-full.txt`. A pass on one surface does not imply a pass on the others. Regenerate stored Markdown after content or field-map changes and inspect every touched `.md` page for its required headings, body, repeater projections, and citations.
6. **Verify rendered ownership and accessibility when templates changed.** On representative desktop and mobile viewports, assert exactly one page-level `main`, the intended header/footer landmark ownership, zero Axe violations, and no console or failed-request errors. Fix the source owner of duplicate landmarks; do not hide the symptom with selector exclusions.
7. **Cross-check agnosticism** — every key you wrote appears in the Phase-0 catalog; no hardcoded field/relation that only exists on this site's snapshot by accident.
8. **Purge cache** if the surface is page-cached (metadata, schema, crawl, permalinks).
   After the purge, compare the plain canonical URL with a unique cache-busted fetch; a
   disagreement is unresolved cache state. For schema, inspect every touched canonical URL
   directly: `schema:validate-live` samples only one published URL per target. Noindexed singular
   pages intentionally emit no JSON-LD, so prove their robots/no-schema state and defer positive
   graph validation until the guarded noindex-removal release.
   The live validator resolves an indexable published sample for each post-type target; a
   noindexed first-created record is not representative because singular schema is intentionally
   suppressed there. If a target has published records but all are noindexed, report the target
   as runtime-unverifiable and validate the configured graph separately until one is released.
9. **Complete the recovery lifecycle** — flush rewrites when required, purge caches, regenerate Markdown, then repeat the touched-URL checks against the served runtime. Keep machine-readable evidence plus an independent reviewer verdict for editorial/source-heavy batches.
10. **Run repository tests for source changes** — `./wpdev test lean-seo --suite=unit`, plus
   `./wpdev test lean-seo --suite=integration` when the integration environment is installed.
   The declared `phpunit-integration.xml.dist` suite additionally requires its Composer
   toolchain and the WordPress test library; if either is absent, report integration as
   environment-unavailable rather than passed.
   CLI config validation must run with active plugins loaded so custom
   `lean_seo_schema_sources` / `lean_seo_schema_transforms` filters participate, and it must fail
   closed when the validator is unavailable. Verify any page-scoped `page:<id>` target against
   that exact published page rather than treating the target key as a post type.

**Exit:** Every touched URL and discovery surface has durable proof, rendered output has zero unresolved tokens or duplicate URLs/landmarks, rollback material exists, and the option reads back clean.

## Verification quick reference

| Surface | One-line check |
|---|---|
| Metadata | fetch permalink → `<title>` / `og:*` / canonical correct |
| Schema | fetch permalink → ld+json properties all resolved |
| Markdown | `lean_seo_generate_markdown(get_post(id))` → no unresolved tags, sections present |
| Crawl | fetch sitemap/robots → CPT included/excluded as intended |
| Permalinks | fetch post URL → parent-nested, single canonical |
