# Migration Pipeline — legacy Elementor → EF V4 atomics

How to migrate an existing page/template off legacy Elementor V3 (`container` + `heading`/`text-editor`/`button`/`counter`/`nested-accordion`) onto the elementor-framework's EF V4 atomic widgets — **aggressively consolidating** into composite EF widgets while **losing zero data**.

This is distinct from [`audit.md`](audit.md) (find problems) and [`build.md`](build.md) (greenfield build). Migration mutates EXISTING `_elementor_data`, so the [`behavior-contract.md`](../references/verification/behavior-contract.md) gate applies and verification is mandatory.

## The Iron Law

> **Aggressive on structure and styling. Improve content where it earns its keep. Never silently drop information.**

The migration is a chance to do better, not a transcription job. Three concerns, separated:

1. **Structure is fungible.** Drop V3 wrappers, collapse legacy widgets into composite EF widgets, reshuffle section order — that's the whole point.
2. **Content is improvable.** Fix typos. Modernize stale copy. Tighten verbose paragraphs. Fix factual errors. Sharpen CTAs. Improve heading hierarchy. Migration is the chance to do this — taking the chance is encouraged.
3. **Information is the floor.** A feature paragraph, a CTA, a service line, a price, a phone number, an answer in an FAQ — if it was on production, it must be on the migrated page OR explicitly declared in the §2d Improvements log as `improvement:<unit_id> → <new text>` or `removed:<unit_id> → <reason>`. Silent drops fail the migration-preservation criterion; declared improvements pass.
4. **EF widgets are the ONLY target — zero legacy widgets survive in a migrated region.** "Convert to EF" is exhaustive, not best-effort: after migrating a region there must be **no `widget:*` node** (`heading`, `text-editor`, `list`, `image`, `icon`, `button`, `counter`, `eael_*`, `jet_*`) left inside it — only `ef-wrapper` / `ef-card` / `ef-navbar` / `ef-toc` / `ef-form` / `ef-cal` (and preserved `ts-*` theme widgets, which are the ONE allowed exception — see PRESERVE). **Every legacy widget has an EF home** ([`../references/ef/widgets.md`](../references/ef/widgets.md) §Retired widgets): an `image` widget → `ef-card` media slot (`media_enabled:true` + `media_image`) or `ef-wrapper.bg_media`, NEVER a surviving `widget:image`; a `button`/EAEL-or-Jet `list`-as-button → `ts_actions` action rows; an `icon` → a heading-row `icon` cell or `ef-card` logo slot. A migrated region that still contains a legacy `widget:*` node (other than `ts-*`) is an **incomplete migration** — the verification pass MUST grep the touched subtree for `widgetType` and fail on any non-`ts-*` hit. Keeping a legacy `image` "because it renders fine" is the exact trap: it renders, but it never entered the design system and it violates this rule.

**The baseline for "did we preserve the information?" is the PRODUCTION page's rendered markdown, not the legacy `_elementor_data` dump.** The legacy dump carries V3 wrapper noise, dead styling, plugin pollution (`eael_*`, `jet_*`), and admin-only fields that never reach the visitor — flagging those as "missing" produces false positives. The page-planning §2e migration-preservation criterion reads the live production page's rendered text via the `agent-browser` CLI ([`browser.md`](../references/verification/browser.md) §Production-page baseline — it renders JS, so dynamic tags resolve as a visitor sees them), decomposes into **information units** (claims / facts / offers / CTAs / features / services / prices / instructions / headings — not words, not sentences), and asserts every unit either appears in some §2d blueprint cell OR is acknowledged in the Improvements log. Improvements are first-class — the contract is "no silent drops," not "no edits."

The framework does **NOT** auto-restyle legacy widgets at render (no `elementor/widget/render_content` hook; only the versioned data migrator under `migrations/steps/` rewrites EF's OWN widget shapes). So legacy `heading`/`text-editor`/`button`/`counter` left in place stay unstyled — they MUST be converted to EF widgets to enter the design system.

## DROP aggressively (structure + styling)

Everything here is noise the EF render path ignores — never carry it over:

- V3 wrapper containers and intermediate nesting (`container > container > container > widget` collapses to one `ef-card`).
- `__globals__`, `background_*`, `flex_*`, `content_width`, `width`, `min_height`, `padding`, `margin`, alignment, `border_*`.
- Plugin pollution: `eael_*` (Essential Addons), `jet_*` (JetElements), `_voxel_dynamic_attrs`, `_ef_loop_more_label` on dead wrappers.
- Decorative "tag-pill" wrapper containers — fold their label into an `ef-card` `content_blocks` row (`kind: heading`) with `style: small`. The `label` and `byline_label` style values are both retired — the `style` enum is `['', h1..h6, small]`.
- Counter count-up animation (ef-card renders static text).

## PRESERVE information — improvements are encouraged, silent drops are forbidden

The contract is "every information unit the visitor sees on production either appears in the migrated tree OR is acknowledged in the §2d Improvements log." That's an information-set check, validated by the migration-preservation criterion against the `agent-browser`-rendered text of the live URL ([`browser.md`](../references/verification/browser.md) §Production-page baseline). Inside the planning blueprint, that translates to:

- **Information units (the actual contract).** Claims, facts, offers, CTAs, features, services, prices, instructions, headings. Every unit visible on production must surface somewhere — either in a §2d blueprint cell (verbatim, paraphrased, restructured, or split across multiple cells) OR as an `improvement:<unit_id> → <new text>` or `removed:<unit_id> → <reason>` row in the §2d Improvements log. Silent drops fail the criterion; declared changes pass.
- **Text that should be improved — improve it.** Typos (`<misspelling>` → `<correction>`), awkward phrasing, outdated copy (a stale year reference), unclear CTAs, weak headings — fix them. Add a one-line `improvement:` entry per fix so the operator sees the change at §2g approval. The criterion does NOT flag rewrites that have an improvement annotation. Migration is the chance to do better; take it.
- **Dynamic tags** — preserve the EXPRESSION byte-for-byte (`@tags()...@endtags()`, `@post(...)`, `@author(...)`, `@site(...)`, `.loop_index()`, `.number_format()`) unless the improvement is explicitly to swap a field. The expression resolves to data; changing the expression changes which CPT field gets read, which IS a content edit that needs an improvement line.
- **Legacy `ts-*` nodes whole** (`ts-post-feed`, `ts-print-template`, `ts-user-bar`, `ts-navbar`): preservation-only. If the migration keeps one, re-embed the ENTIRE node (id + every setting) unchanged. These are Voxel theme widgets — never rebuild them, never touch a single feed/template binding (`ts_source`, `ts_choose_post_type`, `ts_card_template__*`, `ts_template_id`), and never introduce a new one. Read existing nodes via `wpdev elementor:dump <site> <ts-widget> --post <id> --json` (or `all --post <id> --json` for the whole tree) and splice verbatim, or replace the surface with EF `ef-wrapper` template/loop wrappers. The migration-preservation criterion rejects any partial reconstruction.
- **Links / destinations**, button targets, anchor `#ids` — the visible button label is improvable content; the target URL is structural data the criterion inspects via the §2d Settings column. Changing the target = improvement annotation.
- **French accents** — emit valid UTF-8; never let `é` become `u00e9` (see root `CLAUDE.md` §Encoding).
- **Per-item content in repeaters** — every FAQ answer, every menu row. Each item is an information unit; improvements need an annotation, but the unit itself must surface or be marked `removed:` with reason.

**Improvements log shape (in §2d, top-of-section, plain markdown):**

```
### Improvements log (this section)
- improvement: hero-tagline → "<new tagline text>" (was: "<old tagline text>")
- improvement: services-list-item-3 → fixed typo "<misspelling>" → "<correction>"
- removed: legacy-stat-block → "<old stat text>" (reason: stat is stale; no current equivalent; replaced by strengthened cta-footer)
- improvement: faq-q3-answer → tightened from 4 sentences to 1
```

What is NOT in this list (and is migration-discardable per the Iron Law): V3 wrapper containers, dead styling props, `__globals__`, plugin pollution. The criterion will not flag missing wrappers — only silent information drops.

## CONVERT (transform, don't drop)

These change shape but keep meaning:

| V3 source | EF V4 target |
|---|---|
| `_voxel_visibility_rules: [[{type:...}]]` (+ `_voxel_visibility_behavior`) | per-row `_vx_visibility: {$$type:"vx-visibility", value:{behavior:"show"\|"hide", rules:[[{type:...}]]}}` — copy the exact envelope from the local header's `ef-navbar` action rows |
| `heading` wrong `header_size: h1` on a non-hero section | `ef-card` heading row `tag: h2` (fix the hierarchy while migrating) |
| `counter` (number + title) | `ef-card`: `content_blocks` heading block `tag:span style:h1` = number (preserve dynamic tag), heading block `tag:span style:''` (plain) = label (the counter label is a caption under the number; `style: small` de-emphasises it) |
| `nested-accordion` / legacy `accordion` | one `ef-card` with N `content_blocks` rows, each `kind:"accordion"`, `tag:"h3"`, `text`=question, `body`=answer |
| loose `heading`+`text-editor`+`button` cluster | ONE `ef-card`: heading rows (with `subtitle` where a second line is wanted) + `p` rows + `ts_actions` action rows |
| `image` widget (hero/media photo) | fold into `ef-card` **media slot** — never leave a `widget:image`. Add to the content card OR use a **media-only `ef-card`** (empty `content_blocks`, `media_enabled:{$$type:boolean,value:true}`, `media_type:{$$type:string,value:"image"}`, `media_fit:{$$type:string,value:"cover"}`, `media_image:{$$type:"image",value:{src:{$$type:"image-src",value:{id:{$$type:"image-attachment-id",value:<attach_id>},url:null}},size:{$$type:"string",value:"large"}}}`, `media_image_alt:{$$type:string,value:"<alt>"}}`). **Copy the `media_image` envelope from a golden dump of a live `ef-card` that uses media** (`grep -rl media_enabled backups/elementor/`), never hand-roll it. Preserve the production text-left/image-right layout by keeping the parent `ef-wrapper` 2-col `cols` grid with `{content ef-card, media ef-card}` — the single horizontal `ef-card` puts media LEFT and clamps its width (~22rem), so it is NOT a 50/50 hero substitute. |
| EAEL / Jet `list` used as a button row, or a `button` widget | `ts_actions` action rows on the owning `ef-card`. Each row: `{type:action_link, label:"<visible text>", variant:<primary\|white\|transparent\|…>, link:{$$type:"ef-source-value",value:{source:{$$type:string,value:"custom"},value:{$$type:string,value:"<url>"}}}}`. **Copy the full action-row envelope from a live golden dump** (`ef-navbar.cta_ts_actions` on the site's Header template, or any `ef-card.ts_actions`) so every sibling cell (`icon`,`tooltip`,`address`,`phone`,`_vx_loop`,…) is present — a partial row fails the save gate. **Variant pairing:** the emphasis CTA is `primary`; its neighbor is `white`/`transparent`, **never `secondary`** (`primary + secondary` is forbidden — see [`card-actions.md`](card-actions.md) Phase 1 variant-pairing rule). A legacy solid-fill button → `primary`; a legacy outline/ghost button beside it → `white`, NOT `secondary`. Custom-SVG button icons not in the EF icon set are droppable decoration (flag it); the LABEL + DESTINATION are information and must survive. |
| `heading` that is a **styled sub-headline / kicker with a link** (e.g. an underlined `header_size:span` that links to a guide) | an `ef-card` `content_blocks` **heading row**, NOT a real heading tag: `kind:heading`, **`tag:span`** (keeps it off the SEO outline), **`style:h5`** (or the matching size — visual sizing only), optional `icon:{$$type:string,value:"<pack:pack pack-name>"}` (resolve the token with `wpdev elementor:icon-search <term>`), and the link via the action suite: `type:{$$type:string,value:"action_link"}` + `link:{$$type:"ef-source-value",value:{source:{$$type:string,value:"custom"},value:{$$type:string,value:"<url>"}}}`. **The link on such a heading is an information unit — dropping it is a silent drop.** Recover the destination from the legacy node's `link.url` before rebuilding. NEVER emit a real `h5`/`h4`/… tag for decorative styling (see the hierarchy rule below). |

## Heading tag vs visual style — respect the SEO outline (migration bites here)

The `content_blocks` heading row separates **semantic tag** (`tag`) from **visual size** (`style`). They are independent, and conflating them corrupts the SEO heading outline:

- **A real heading in the outline** (the card's title, a section h2, an FAQ h3) → set `tag` to the correct level (`h1`…`h6`) AND usually leave `style:""` (inherits the tag's size) or match it.
- **Decorative / styled text that is NOT a heading** (a kicker, an eyebrow, a sub-headline, a "big number", a styled CTA line) → `tag:span` (or `tag:p` for a paragraph) with `style:h5`/`h4`/… for the LOOK. **Never emit a real `h4`/`h5`/`h6` tag just to get its font size** — a stray `h5` in the DOM pollutes the outline (`h1 → h2 → h5` reads as a broken hierarchy to crawlers and screen readers). The `page-plan-contract.md` hierarchy criterion walks document order and flags this; migration is where it most often slips in because a legacy `header_size:span` heading "looks like a heading" and gets migrated to a real tag.
- **Exactly one `h1` per page**, on the hero card's title row. Do not introduce a second `h1` while migrating a section, and do not demote the existing one.
- **A styled sub-headline that carried a link** keeps BOTH: `tag:span` + `style:h5` for the look, AND the action-suite `type:action_link` + `link` for the destination. Dropping the link is a silent-drop failure (it happened; the fix is to read `link.url` off the legacy node first).

## Composite mapping (the consolidation target)

Collapse a whole functional region into the single purpose-built EF widget — do not migrate piecemeal. Reference exemplar: a typical header collapses `{banner heading+button, navbar logo+mega-menu+user-bar, mobile nav, breadcrumb}` (a dozen-odd containers + widgets) into ONE `ef-navbar`.

| Region | Target widget |
|---|---|
| Root `<main>` container | `ef-wrapper` `tag:main` (use `elementor:migrate:main`) |
| Section / layout container | `ef-wrapper` (tag from `html_tag` else `div`; `cols` only when horizontal — use `elementor:migrate:containers`) |
| Header / nav / breadcrumb region | one `ef-navbar` (`nav_items` = `ef-mega-rows`, `cta_ts_actions` = `ef-action-rows`, `banner_*`) |
| Content block (label+heading+body+buttons) | one `ef-card` (heading rows + `ts_actions`) |
| Content block WITH a photo (hero, media-split) | one `ef-card` carrying the image in its **media slot** (`media_enabled` + `media_image`), OR — to preserve a production 50/50 side-by-side layout — a parent `ef-wrapper` with `cols:"1fr 1fr"` holding `{content ef-card, media-only ef-card}`. Either way the image lives INSIDE an `ef-card`; a sibling `widget:image` is forbidden (Iron Law #4). |
| Counters / stat row | `ef-card`s (number + label rows) |
| FAQ / accordion | one `ef-card` (accordion heading rows) |
| Table of contents | `ef-toc` · Form | `ef-form` · Calendar | `ef-cal` |

## Entry criteria

1. Target post or template has legacy Elementor/Voxel structure that should become EF V4 atomic widgets.
2. A representative production URL sample exists (`?p=<post_id>` is acceptable for singles).
3. `wpdev elementor:codegen` ran (regenerating the schema SSOT) as the first step per [`rules.md`](../references/core/rules.md) rule 1, and `wpdev elementor:codegen --check` passes before mutation.
4. Backup/export path is writable and rollback target can be captured.

## Exit criteria

1. Legacy content is preserved in EF V4 atomic widgets, with every carried text, dynamic tag, link, visibility rule, and `ts-*` setting mapped.
2. `wpdev elementor:lint <site> --post <id>` passes with 0 findings.
3. Browser verification passes on representative production URL sample.
4. Behavior Contract diff shows no Forbidden Semantic Delta.

## Phased Workflow

### Phase 0 - Backup And Production Baseline

**Entry:** Site, post id, role, and representative production URLs are known.

1. Run codegen/check, export the source, dump the full tree, and snapshot/prune revisions.
2. Capture the Behavior Contract and production rendered text for complete, sparse, and
   typical records using the browser reference.
3. Inventory every visible information unit, dynamic tag, link, visibility rule, and
   preserved `ts-*` settings block.

**Exit:** Durable rollback, source tree, behavior baseline, and production information-unit
manifest exist.

### Phase 1 - Mechanical Skeleton

**Entry:** Phase 0 rollback/baselines exist.

1. Preview, then apply the idempotent structural migrators:
   ```bash
   wpdev elementor:migrate:main <site>
   wpdev elementor:migrate:main <site> --fix --yes
   wpdev elementor:migrate:containers <site> --post <id>
   wpdev elementor:migrate:containers <site> --post <id> --fix --yes
   ```
2. Lint and screenshot the skeleton before content consolidation.

**Exit:** Root/main and containers use valid EF wrappers; child content remains present; the
intermediate tree is lint-clean and visually captured.

### Phase 2 - Plan With Preservation Gate

**Entry:** Phase 1 skeleton and Phase 0 information manifest exist.

1. Execute `workflows/page-planning.md` in migration mode.
2. Include `migration-preservation` in the applicable criteria set.
3. Require every legacy information unit to appear in a Blueprint cell or an explicit
   Improvements-log rewrite/removal.
4. Preserve `ts-*` settings and dynamic expressions byte-for-byte unless an approved
   replacement owns them; translate legacy visibility only from an authoritative envelope.

**Exit:** Plan contract validates, migration-preservation has positive coverage evidence,
and the computed gate is green or explicitly approved on the exception path.

### Phase 3 - Consolidate In Bounded Batches

**Entry:** Phase 2 gate is open.

1. Partition 5-10 homogeneous section/widget leaves per `voxel-widget-builder` build batch.
2. Give each leaf its Blueprint rows, source node ids, current settings, and authoritative
   schema/dump. Require one envelope per leaf; workers never import.
3. Validate bounded waves, retry rejected leaves at most twice, and keep passing siblings.
4. Assemble replacement subtrees by node id and import once with `--save`.

**Exit:** Every planned leaf is represented exactly once; the assembled tree is imported,
read back, lint-clean, and CSS-regenerated.

### Phase 4 - Deduplicate And Normalize

**Entry:** Phase 3 read-back passes.

1. Remove only strict-subset legacy duplicates, empty orphan wrappers, and approved style
   residue. Preserve the more complete information-bearing source.
2. Apply removals in one id-keyed transform, then read back and lint again.

**Exit:** No duplicate information surface or empty wrapper remains; no production
information unit was silently lost.

### Phase 5 - Independent Verification

**Entry:** Phase 4 normalized tree is stored and representative URLs are stable.

1. Batch 5-10 URL/surface leaves per verifier, using unique browser sessions per URL.
2. Run the verification gates below and compare DOM text with the Behavior Contract and
   production information-unit manifest.
3. Route only failed scopes back to Phase 2/3. Continue only while the open Critical set
   strictly shrinks; otherwise escalate the residual.

**Exit:** All gates pass on every representative URL, or the migration remains explicitly
failed/blocked with rollback evidence.

## Verification gates (every batch — mandatory)

1. `wpdev elementor:lint <site> --post <id>` → **0 findings** (`unknown-prop`/`type-mismatch` block).
2. `wpdev rebuild <site> --only purge` (LiteSpeed + Elementor CSS).
3. Browser ([`rules.md`](../references/core/rules.md) rule 7, tool surface [`browser.md`](../references/verification/browser.md)): the `agent-browser` CLI — `screenshot --full` (read it) + the layout-assertion `eval --stdin` block + these migration-specific assertions (run inside the same `eval` block or via follow-up `get`/`eval` calls):
   - **No tag leakage**: `get text body` contains no literal `@tags(`/`@post(`/`@author(`/`@site(`.
   - **Feeds present**: `get count` of `ts-post-feed` unchanged from before the migration.
   - **Columns**: horizontal sections render as multi-track grids (the layout block's `grid` field has N tracks) — and inner wrappers don't inherit the parent grid.
   - **Expected text** renders for each migrated cluster.
   - **Accordion caveat**: `innerText` EXCLUDES collapsed `<details>` content — assert accordion questions/answers with `textContent`, not `innerText`, inside the same `eval` block, or they read as missing (false negative).
    - **Before/after** (optional, high-value): `diff screenshot --baseline` against the pre-migration render to confirm nothing the Iron Law meant to keep visibly vanished.
    - **No legacy widget survives** (Iron Law #4): dump the migrated subtree and assert **zero non-`ts-*` `widgetType`** remains in it — e.g. `wpdev elementor:tree <site> <id>` shows no `widget:image`/`widget:heading`/`widget:list`/`widget:text-editor`/`widget:icon`/`widget:button`, only `ef-*` (and preserved `ts-*`). In the browser, `document.querySelector('.elementor-widget-image, .elementor-widget-heading, .elementor-widget-text-editor')` scoped to the migrated section returns null.
    - **Heading outline intact** (SEO): collect `[...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h=>h.tagName)` and confirm the migrated section introduced no stray heading tag for decorative text (a styled kicker must render as `SPAN`, not `H5`) and did not add a second `h1`.
4. Widget-count drop is corroborating evidence of consolidation (e.g. 73→24), not a substitute for the `migration-preservation` information-unit pass — a count drop can co-occur with a silent drop. Done = information-unit pass + lint-clean + layout assertions + screenshot-read + no-legacy-widget grep + heading-outline check; count-drop corroborates.

## Known losses (flag, don't silently accept)

- **Counter count-up animation** — ef-card is static. Acceptable; note it.
- **`nested-accordion` `faq_schema: yes`** (`FAQPage` JSON-LD) — ef-card does not emit it. Do **not** re-add it for Google rich-result eligibility; FAQ rich results were deprecated on 2026-05-07. Preserve the visible accordion content when it is useful, and only keep/add FAQ schema where a site has a non-Google consumer and the schema is explicitly required.
- **Section backgrounds / spacing / centering** — dropped by the clean swap; re-apply via `ef-card`/`ef-wrapper` `variant` + grid props in a later styling pass, not by carrying V3 keys.

## Editor naming note

`ef-wrapper` navigator labels derive live from the `tag` prop (`assets/js/editor/preview/wrapper.js` → `syncWrapperTitlesDeep` walks the whole tree; broad `change` listener catches V4 atomic control edits at any depth). No `_title` is baked into the data — keep it that way (zero bloat); the label follows whatever tag is selected.

## Mistake guards

- Never preserve styling/structure at the cost of rendered visitor-visible content.
- Never drop legacy `ts-*` settings, dynamic tags, links, or visibility rules from the blueprint.
- Never migrate from one sample URL only when a template renders many records.
- Never leave a legacy `widget:*` node (other than `ts-*`) inside a migrated region "because it renders fine" — images go in an `ef-card` media slot, buttons in `ts_actions`, icons in a heading-row `icon` cell (Iron Law #4).
- Never carry a heading's `link` across as a plain span and drop the destination — a linked sub-headline's URL is an information unit; read `link.url` off the legacy node and re-attach it via the action suite.
- Never emit a real `h4`/`h5`/`h6` tag to get a font size — use `tag:span` + `style:h5`; a stray heading tag corrupts the SEO outline.

## Anti-patterns

- **Rebuilding a `ts-*` widget** instead of splicing it verbatim — one wrong feed binding empties the feed. Always copy the whole live node.
- **Synthesizing `$$type` envelopes from memory** — always copy from a golden node on the same page.
- **Editing content WITHOUT an Improvements-log entry.** Improving copy is encouraged by the Iron Law — but every typo fix, rewrite, or removal MUST get an `improvement:`/`removed:` line in the §2d Improvements log so the operator sees it at §2g and the migration-preservation criterion doesn't read it as a silent drop. The forbidden move is the *silent* edit, not the edit. **Dynamic-tag EXPRESSIONS are the one exception** — preserve them byte-for-byte (`@tags()…@endtags()`, `@post(…)`, transforms) unless the improvement is explicitly to swap which field is read, which itself needs an `improvement:` line.
- **Sequential per-section dispatch** — fan out all sections at once (atomic scope = one section each): a Workflow `parallel()` leg under multi-agent opt-in, or a single-message Agent dispatch as the fallback. Looping the sections one at a time costs N× wall-time for zero correctness gain.
- **Skipping the screenshot** because lint passed — lint can't see a collapsed layout or a feed that silently returns zero.
- **Deleting a "duplicate" without confirming subset** — verify the removed node's data is fully contained in the kept node first.
