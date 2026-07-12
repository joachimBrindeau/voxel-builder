# Page Plan Archetypes And Vocabulary

## Archetype Selection

**Goal:** pick from a catalog of established section archetypes instead of inventing shapes. Reuse what the site already does well.

**Whole-page lookup (do this BEFORE the per-section lookup, for a full page / single / archive / hub build).** Read the **Pages** table in [`../../templates/index.md`](../../templates/index.md) first: when a `scope: page` composition matches the target archetype (e.g. an `archive` / `single` / `search-hub` / `glossary` page), adopt that complete template as the whole-page starting tree — its section set and order come pre-composed. Replace its documented `__TOKEN__` slots and re-bind loop/source dtags to the target CPT per the template's `source_note`. Only when NO page-scope template matches do you compose the page from per-section templates via the lookup below. A bound page template is a *preferred starting tree*, never a validation bypass: it stays subordinate to §2b (SSOT wins) and every section it carries is still validated prop-by-prop by the §2e adversaries.

**Template-store lookup (do this FIRST, before the static archetype catalog).** For each section the page needs, read [`../../templates/index.md`](../../templates/index.md) and look for a saved section template whose `type` matches the section archetype and whose `tags` overlap the CPT context (e.g. a `hero` archetype for a services/geo CPT → the seeded [`hero-services-search`](../../templates/sections/hero-services-search/) / [`hero-city-geo`](../../templates/sections/hero-city-geo/)). **When a template matches, PREFER it: bind the section to that template id** rather than composing the archetype from scratch. Only sections with NO matching template fall through to the static archetype catalog below and full composition. Discovery is reading `templates/index.md` (its `type` / `tags` / `widgets` / `dtags-used` columns) — there is no `apply-template` command. The bound template is a *preferred starting tree*, never a validation bypass: it stays subordinate to §2b (SSOT wins on any disagreement — [`../../templates/README.md`](../../templates/README.md) §SSOT wins) and every bound section is still validated prop-by-prop by the §2e adversaries.

**Standard archetypes** (when NO saved template matches, pick from this catalog — the fallback behind the template-store lookup above; adding a *new* archetype requires the §2e Pattern-reuse criterion to approve via a peer-template comparison override):

**Root wrapper (always present, exactly once per page):** the Plan Document declares a single `ef-wrapper` with `tag: main` at depth 0 of `_elementor_data` that contains every section. The hierarchy criterion enforces this — multiple or missing `tag: main` = `C`-severity finding.

| Archetype | Purpose | Wrapper tag | Default desktop grid | Mobile collapse | First heading | Internal heading tags | When to use |
|---|---|---|---|---|---|---|---|
| `hero` | Primary subject identification | `section` (within root `main`) | `1fr` (single column, full bleed) — OR `3fr 2fr` / `2fr 3fr` variant when there's a complementary visual / CTA aside (content-asymmetric hero pattern) | `1fr` | **h1** bound to title-class field for CPT templates (contextualized dynamic phrase, not bare `@post(title)`); for non-CPT pages (homepage / landing), use a static h1 with the page subject. Decorative eyebrow before the h1 → a `kind: byline` row (rendered `.ef-ih-byline`). | eyebrow (ONE, directly above the h1) → `kind: byline`; tagline/subtitle → `kind: rich_text` (`p`); sub-CTA labels → `p`; never another `h*` | Every single template. Mandatory. |
| `brief` | Short structured intro paragraph + secondary CTA | `section` | `1fr` or `2fr 1fr` (body + sidebar-cta) | `1fr` | h2 — contextual phrase (e.g. `@tags()About @post(:title)@endtags()`, not bare "About") | body → `p`; CTA label → `span` | When the CPT has an intro/excerpt/hook field separate from the long body. |
| `specs-grid` | Label/value pairs | `section` | `1fr` (single column, label-above-value rows) OR `1fr 1fr` (2-up, label-value pairs side-by-side); **let the content's hierarchy decide column count — prefer more sections over more columns** | `1fr` | h2 — e.g. `@tags()Specifications of @post(:title)@endtags()` | per-item label → `kind: heading, tag: span, style: ''` plain, or `style: label` for a small-caps pill (runtime-valid `.ef-label`); per-item value → `tag: span, style: h3` or `kind: rich_text` (`p`); NEVER `h3` for the value when the label is already the spec name; the section eyebrow is a `kind: byline` row, never `style: byline_label` | When the field group's shape calls for it (atomic select / multiselect / date / number / switcher fields that aren't long-form text). |
| `detail-tabs` | Multiple long-form body sections under tabs | `section` | `1fr` (tabs are the layout) | `1fr` | h2 — e.g. `@tags()Detailed information about @post(:title)@endtags()` | per-tab pane title → `h3` with contextual phrasing (e.g. `@tags()Services provided by @post(:title)@endtags()`); tab body → `p`; existing legacy `ts-*` nodes remain verbatim only if already present | When the field group's shape calls for it (texteditor / wysiwyg fields that benefit from separation — overview / brief / detail / specs). |
| `detail-accordion` | Multiple body sections collapsed by default | `section` | `1fr` | `1fr` | h2 — contextual phrase | per-row question → `h3` (FAQ-style); per-row body → `p` | When tabs would be overkill (≤3 sections) or device-target is mobile-first. |
| `sidebar-contact` | Contact channels (call / email / message) | `aside` (when used as a sidebar) or `section` (when full-width) | `1fr` (it's a sidebar) | `1fr` (last in mobile stack) | h2 — e.g. `@tags()Contact @post(:title)@endtags()`, not bare "Contact" | per-channel label → `tag: span, style: ''` plain (no `byline` row); per-channel CTA → `span` | When the CPT has phone/email/messaging fields OR `ts-` messaging connections. |
| `sidebar-map` | Geo-location surface | `aside` | `1fr` | `1fr` (last in mobile stack) | h2 or h3 — e.g. `@tags()Locate @post(:title)@endtags()` with city/region fallback | label → `tag: span, style: ''` plain (no `byline` row); ts-map nested unchanged | When the CPT has a geo-location field with non-empty data. |
| `sidebar-schedule` | Opening hours / availability | `aside` | `1fr` | `1fr` (last in mobile stack) | h2 or h3 — e.g. `@tags()@post(<field>).fallback(@post(:title)) opening hours@endtags()` | day label → `span`; ts-work-hours nested unchanged | When the CPT has a work-hours field. |
| `relation-feed` | Inline list of related posts via a relation field | `section` | `1fr` OR `1fr 1fr` (2-up); **let the content's hierarchy decide column count** — repeated cards come from an `ef-wrapper` loop/template composition, not `ts-post-feed` | `1fr` | h2 — e.g. `@tags()Other @post(:title.<relation_label>)@endtags()` or relation-named phrasing | per-loop child title comes from the EF card/template child declared in this Blueprint | For every post-relation field with data. Mandatory per relation. |
| `faq-accordion` | FAQ from a composite-repeater field | `section` | `1fr` | `1fr` | h2 — e.g. `@tags()Frequently asked questions about @post(:title)@endtags()` | per-FAQ question → `h3`; per-FAQ answer → `p` | When the CPT has a non-empty FAQ field with genuine reader questions. For glossary/defined-term singles this is optional, never boilerplate, and never a reason to emit `FAQPage` schema. |
| `related-cpt-feed` | "More from this CPT" feed | `section` | `1fr` — the EF loop/template wrapper owns its repeated-card layout (see §Feed-grid note below) | `1fr` | h2 — e.g. `@tags()Other <CPT plural> like @post(:title)@endtags()` or category/region-scoped phrasing | per-loop card title → `h3`; per-loop-card byline → `span` | Every single template. Recommended. |
| `cta-footer` | Closing action band | `section` | `1fr` (full bleed) | `1fr` | h2 — contextual outcome phrase (e.g. `@tags()Ready to work with @post(:title)?@endtags()`) | CTA label → `span`; sub-label → `p` | Every single template that drives a conversion goal. |

The plan picks **N archetypes**. The density adversary will challenge the count; the coverage adversary will challenge the field-to-archetype binding; the **hierarchy criterion** will challenge the wrapper-tag selection AND the heading-tag selection per row; the **pattern-reuse criterion** will challenge any dynamic heading phrasing that doesn't match the production conventions on peer templates.

**Let the content's hierarchy decide column count; prefer more sections over more columns.** Reference exemplar: inspect a rich peer template — mostly `1fr` and `1fr 1fr` sections, plus the occasional symmetric atomic feature row (a feature grid where content is inherently symmetric and each card is atomic: icon + h2 + body line) and content-asymmetric hero pair (the hero + lateral panel). Run `wpdev elementor:tree <site> <peer_id>` to inspect.

The Layout map's `cols` track string values:

- `1fr` — single column. Default for most sections.
- `1fr 1fr` — 50/50 two-column. Body + complementary aside, or 2-up paired items.
- `1fr 2fr` / `2fr 1fr` — sidebar + body or body + sidebar. The 2fr side holds the primary content.
- `3fr 2fr` / `2fr 3fr` — content-asymmetric hero pattern. Use when one side is content-heavy and the other is a single visual/CTA.
- `1fr 1fr 1fr 1fr` — for atomic symmetric items: a feature/icon/expertise grid where each cell is icon + h2/h3 + one body line, not paragraphs, and tablet collapses to `1fr 1fr`, mobile to `1fr`. The `feature-grid` archetype below codifies this.
- `1fr 1fr 1fr` — atomic thirds (a counter row of stats — total clients / years / projects).

Let the content's hierarchy decide column count; **prefer more sections over more columns**; collapse to a single column on small screens; the hierarchy reviewer challenges any grid that fights the content. When the planner reaches for a wide or unusual grid:

- **A specs grid with many fields?** Split into thematic sub-sections (one per coherent field group) each at `1fr` or `1fr 1fr`. The hierarchy criterion will then enforce h2 per sub-section.
- **Many stats?** Split across multiple `1fr 1fr` sections, OR pick the most important and use `1fr 1fr 1fr 1fr`.
- **Feed/list showing many cards in a row?** The EF template/loop wrapper handles repeated children — the section wrapper stays at `1fr`, while the loop child/card controls its own internal stack. Do not solve this with a Voxel `ts-post-feed`.

Why this discipline: **more sections > more columns** is the default. Vertical rhythm is forgiving (mobile collapse is trivial, hierarchy stays clear). Horizontal compression usually fights the design system — but symmetric-atomic feature grids and asymmetric content pairs are sometimes the right call; the catalog below codifies which archetypes earn that shape. The hierarchy reviewer challenges any grid that fights the content; `1fr 1fr 1fr 1fr` belongs to the `feature-grid` archetype with content satisfying the atomic-symmetric test; `3fr 2fr` belongs to the `hero` archetype (with `hero-with-aside` variant declared) or `brief` with a CTA panel.

**Heading-tag policy (SEO-compliant outline):**

The page must read as a valid `h1 → h2 → h3` outline when a screen reader walks document order. The catalog above pins each archetype's "first heading" tag, which produces the page-level sequence: hero h1 → section-N h2 (in document order) → nested h3 inside each h2 section. Decorative text (eyebrows, taxonomy pill labels, CTA labels, taglines) NEVER uses an `h*` tag — it uses `tag: span` or `tag: p`. Body paragraphs use `tag: p`. The hierarchy criterion walks the full sequence in §2e and emits findings on any violation.

**Eyebrow rule — use the `byline` row KIND, not a phantom `style` value (the single most-misused affordance):**

> **SSOT correction (verified 2026-06-14 against `schemas/parts/rows/content-block-row.schema.json`, EF migrations 800/890, `ef.css`, and live peer dumps).** `style: byline_label` is **migrated-away / vestigial** — EF migration step 890 converts `style: byline_label → label` precisely because "byline is now a first-class block kind." Do NOT author `byline_label`. The eyebrow is its own row **`kind: byline`**, not a heading style. `style: label` IS a live runtime value (renders `.ef-label`, small-caps inline label) — but note it is **absent from the schema's `style` enum** (`["", "h1".."h6"]`), so it is runtime-valid yet schema-strict-invalid; prefer it only for genuine inline pills, and expect schema-lint to flag it until the enum is reconciled (tracked separately).

The **eyebrow / kicker** — the small upper-case label sitting directly above a card's main heading — is a content-block row with **`kind: byline`** (cells `byline_primary` / `byline_secondary`), rendered as `.ef-ih-byline`. Confirmed in production: peer service single (post 46083) authors its eyebrow as one `kind: byline` row; no peer uses `style: byline_label`.

- Allowed: exactly ONE `kind: byline` row per card, immediately preceding that card's main heading (e.g. `Overview` above the `h2`, the parent-category kicker above the hero `h1`). At most one per card.
- **Everything else uses a valid style/kind.** Taglines / subtitles → `kind: rich_text` (`tag: p`); per-channel / per-day / map labels, CTA labels → `kind: heading, tag: span, style: ''` (plain) or `style: label` (small-caps inline label, runtime-valid via `.ef-label`); second/third headings → `tag: h3` with `style: ''`. Never an `h*` tag for decorative text, never `byline_label`.
- Rationale: the `byline` kind carries the small-caps intro treatment via `.ef-ih-byline`. One byline row, one main heading, per card.

The hierarchy criterion flags any `kind: byline` row that is not the leading eyebrow of its card (severity `I`), any card with more than one `byline` row (severity `I`), and any `style: byline_label` (severity `C` — migrated-away; use `kind: byline`).

**Production exemplar — eyebrow-before-h2 scaffold:** a rich peer template prefixes every navigable section with a `kind: byline` eyebrow (e.g. Overview / More about / Services / News / Gallery / Contact / FAQ / Send a message / Explore), followed by an `h2` heading with contextual phrasing. The planner SHOULD adopt this scaffold for every non-hero section unless `override:` justifies; the hierarchy criterion surfaces missing eyebrows as severity `I`.

**Per-card semantic tags (production carries semantic role at CARD level, not wrapper level):**

Production templates (a homepage page, a rich CPT single) use a small set of wrapper tags (`main / section / nav / div`) and carry the per-section semantic role on the CARDS via the card's own `tag` prop. Catalog:

- `ef-card tag: article` — hero card on a CPT template (the card IS the article). One per page.
- `ef-card tag: section` — overview / about / in-depth / repeater-host content cards. Multiple per page.
- `ef-card tag: aside` — sidebar utility cards (Contact / Location / Opening hours / on-this-page nav). Multiple per page.
- `ef-card tag: div` — atomic items inside a `feature-grid` 4-up (no semantic anchor of its own; the parent section's h2 carries the outline).

The §2d Blueprint Settings cell for every card MUST declare its `tag` prop. The hierarchy criterion checks that hero is `article`, sidebar utilities are `aside`, repeater hosts and content cards are `section`, and `feature-grid` children are `div`.

**Exit:** the plan lists its chosen archetypes (with section IDs, wrapper tags, grid defaults, first-heading tags, and per-card semantic tags) and shows that every `must`-class field from §2a maps to at least one archetype. Sections **bound to a saved template** are recorded with their template id (from `templates/index.md`) and only need a matched archetype `type`; only **unbound** sections must map to a catalog archetype row. The root `main` wrapper is declared; every chosen archetype's wrapper tag matches the catalog row (deviation requires `override:` with reason).

## Phase 2c.bis — Production vocabulary palettes (consumed by §2d)

Before composing Blueprints, the planner reads the production vocabulary for dynamic-tag transforms, tag-row variants, and action types — these recur across every site's templates and the planner reuses them instead of reinventing. Source: a rich peer template (a data-rich CPT single) plus a homepage page. The `voxel-heading-curator` agent dispatched in this phase samples additional peer templates if needed.

**Dynamic-tag transform chains (use these patterns, not bare `@post(field)`):**

| Pattern | Use case | Example |
|---|---|---|
| `@post(:title)` | Title used as a noun phrase (with surrounding context words). Different from `@post(title)` — the `:` form renders cleaner when wrapped in a sentence. | `@tags()Presentation of @post(:title)@endtags()` |
| `@post(field).fallback(@post(other_field))` | Field A with field B as a backup. | `@tags()@post(<field>).fallback(@post(:title)) opening hours@endtags()` |
| `@post(field).strip_tags().truncate(N).fallback(@post(other))` | Excerpt with HTML strip + length cap + fallback. Production hero subtitle pattern. | `@tags()@post(<field>).strip_tags().truncate(220).fallback(@post(<other_field>))@endtags()` |
| `@post(field).number_format(N)` | Formatted number with N decimals. | `@tags()@post(<field>).number_format(0)€@endtags()` |
| `@post(field).count()` | Count of items in a relation / repeater / multiselect. | `@tags()@post(<relation>).count() items@endtags()` |
| `@site().math(<expr>)` | Arithmetic on dynamic values. Production "X more in this group" pattern. | `@tags()+@site().math(@post(<relation>.<field>).count() - 1) more in @post(<relation>.title)@endtags()` |
| `@site(loop_<type>.field)` | Inside a `_vx_loop` over `<type>`, references the loop iteration's field. | `@tags()@site(loop_<type>.<field>)@endtags()` |
| `@post(rel.field)` | Single-relation traversal. | `@tags()@post(<relation>.title)@endtags()` |

The data-wiring criterion checks every Blueprint dynamic tag against this palette — bare `@post(title)` in a non-hero heading without surrounding context words is flagged as a keyword-stuffing risk (severity `I`).

**Image / media envelope patterns:**

| Pattern | Use case |
|---|---|
| `media_image.src = vx("@post(<image_field>.id)") size: large` | Hero / about media bound to a CPT image field. |
| `logo_image.src = vx("@post(_thumbnail_id.id).fallback(@post(types.icon))") size: large` | Logo with thumbnail-then-type-icon fallback chain. |
| `media_image.src = vx("@post(<relation>.<image_field>.id)")` | Image from a traversed relation. |

`size: "large"` is the universal default token (production exemplar). The planner records `vx envelope` in the Dynamic affordance column for these props.

**Tag-row variant vocabulary** (the `variant` value on each `ef-card.tags` repeater row):

| Variant | Visual role | Production example |
|---|---|---|
| `""` (empty) | Default pill | CPT types pill, regions pill |
| `transparent` | Outline-only, low emphasis | Secondary metadata loop |
| `green` | Affirmative status | "Verified" badge |
| `gray` | Neutral / pending status | "Unverified" badge |
| `primary` | High-emphasis brand pill | Featured / promoted state |

Tag-rows use `loop` to iterate a relation/taxonomy and conditional `_vx_visibility` to gate badges. The planner records the variant per tag-row in the Blueprint Settings cell.

**Action-row type vocabulary** (the `type` value on each `ef-card.ts_actions` repeater row — full list in [`actions.md`](../ef/actions.md); the production-frequency subset is):

| Action type | Use case | Required cells |
|---|---|---|
| `share_post` | Native share UI | (no extra fields) |
| `action_save` | Bookmark / favorite | (no extra fields) |
| `edit_post` | Owner-only edit link | (no extra fields, visibility gated by post:author == current_user) |
| `action_link` | Custom CTA / external link | `link.destination` (literal or dynamic) |
| `phone` | Click-to-call | `phone.value` |
| `email` | Mailto | `email.value` |
| `get_directions` | Maps link | `geo.value` |
| `show_post_on_map` | Pan/zoom the page's ts-map | `map_id` (the `ts-map` widget's element id) |
| `scroll_to` | Anchor scroll | `scroll_target` (target `_cssid`) |

Action-row `variant` vocabulary: `""` (default), `primary`, `secondary` (production usage).

**Section-wrapper aria-label defaults (a11y discipline):**

Production uses `aria-label` on exactly two wrapper roles: `nav` (e.g. `aria-label="On this page"`) and the outermost grid-bearing `section` (e.g. `aria-label="Company details"`). The planner declares aria-label in the Layout map's Section wrapper table for these two roles; other wrappers skip it (the heading inside is sufficient).
