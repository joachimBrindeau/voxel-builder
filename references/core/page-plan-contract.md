# Page Plan And Blueprint Contract

## Section Blueprint Schema

**Goal:** for each chosen archetype, produce a Section Blueprint — a concrete table that the widget-builder subagents can consume in Phase 3 as their brief.

Every section in §2c produces THREE artifacts in §2d: an **Improvements log** (migration only), a **Layout map** (always), and a **Blueprint** (always). The Layout map defines the visual structure (grid tracks, gaps, responsive collapse, per-widget placement); the Blueprint defines the widget JSON settings; the Improvements log declares what changed from production. The hierarchy criterion inspects the Layout map; the data-wiring + ssot-integrity criteria inspect the Blueprint; the migration-preservation criterion inspects the Improvements log against production markdown.

**A section blueprint MAY bind to a saved template** in [`../../templates/sections/`](../../templates/sections/) (matched via [`../../templates/index.md`](../../templates/index.md) in §2c) instead of requiring full widget-by-widget synthesis — record the bound template id in the blueprint row so Phase 4 splices its `template.json` and patches only the deltas. The bound tree stays subordinate to §2b: the SSOT wins on any disagreement ([`../../templates/README.md`](../../templates/README.md) §SSOT wins), so the template is a starting tree the blueprint still validates prop-by-prop, never an authoritative spec.

**Composition inputs:** validated heading-palette and Layout-map leaf envelopes from
Phase 2c. The batching/wave mechanics live only in
`references/core/parallel-dispatch.md`; this file defines the artifact they must satisfy.
If a layout leaf returns `escalate_split`, revise the archetype assignment before writing
this contract block.

**Per-section §2d block** (one per section in the Plan Document):

```
## Section: <id> — <archetype>

### Improvements log (migration mode only — omit in greenfield build, omit when copy matches production verbatim)
- improvement: hero-tagline → "<new tagline>" (was: "<old tagline>")
- improvement: services-list-item-3 → fixed typo "<misspelling>" → "<correction>"
- removed: legacy-stat-block → "<stale stat>" (reason: stat is stale; no current equivalent)

### Layout map

#### Section wrapper (the outer `ef-wrapper`)
| Prop | Value | Notes |
|---|---|---|
| `tag` | `section` | semantic HTML wrapper (or `aside` for sidebar-only archetypes, `main` for hero-only) |
| `_cssid` | `<section-overview>` | stable selector for browser-verification + Behavior Contract DOM anchor |
| Section width | `contained` \| `full-bleed` \| `narrow` | maps to design-token max-width band |
| Background | `transparent` \| `white` \| `secondary` \| `primary` | wrapper **`variant`** (surface SSOT) — NOT invented tokens. Assign via the P1–P6 ladder + set `bg_media_type:color` (else inert). See [`../ef/section-rhythm.md`](../ef/section-rhythm.md) |
| Vertical rhythm | `sm` \| `md` \| `lg` \| `xl` | top/bottom padding band (design tokens) |
| Sticky | `none` \| `sidebar-sticky` | only when the archetype calls for it |

#### Grid tracks (responsive)
| Breakpoint | `cols` track string | Row gap | Column gap | Justify items |
|---|---|---|---|---|
| desktop (≥1024) | `1fr 2fr` | `lg` | `lg` | `start` |
| tablet (640–1023) | `1fr 1fr` | `md` | `md` | `start` |
| mobile (<640) | `1fr` | `md` | — | `start` |

Track ratio guidance: `1fr` (single column), `1fr 1fr` (50/50), `1fr 2fr` (33/67 — sidebar left), `2fr 1fr` (67/33 — sidebar right), `1fr 1fr 1fr` (thirds — specs grid), `1fr 1fr 1fr 1fr` (quarters — counter row of atomic items). Let the content's hierarchy decide column count; prefer more sections over more columns. Mobile always collapses to `1fr` unless the section is a small counter row of atomic items. For **asymmetric / bento masonry** sections (a hero card + smaller peers, sized by content rather than a uniform grid) — the size=hierarchy rule, content→span decision table, and the rectangle-tiling invariant (`Σ(col_span × row_span) == cols × rows_used`, no holes) — see [`../ef/masonry.md`](../ef/masonry.md).

#### Widget placement (every Blueprint row gets one row here)
| Blueprint # | Widget | Desktop column | Desktop col-span | Desktop row-span | Tablet column | Tablet col-span | Mobile order |
|---|---|---|---|---|---|---|---|
| 1 | ef-card overview-body | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | ef-card overview-aside | 2 | 1 | 1 | 2 | 1 | 2 |
| 3 | ef-card overview-cta | 1 | 2 (full) | 1 | 1 | 2 (full) | 3 |
| ... |

Placement guidance: every Blueprint row MUST have a placement row. "Full" col-span = the whole track count; named col-spans (1, 2, full) — no fractional spans. Mobile order = top-to-bottom stacking order after grid collapse (lower number stacks higher).

### Blueprint
| # | Widget | Settings (prop → FULL $$type envelope) | Tag wrap | Dynamic affordance (per prop) | Role | Expected DOM | Pre-resolved (Post A/B/C) |
|---|---|---|---|---|---|---|---|
| 1 | ef-card | _cssid: "<section-overview-body>"; heading rows: [{tag: h2, text: @post(title), text-affordance: on}, {tag: p, text: @post(<field>), text-affordance: on}, ...] | @tags() | text-row-0: on (text), text-row-1: on (text); _cssid: vx envelope | dynamic-card | <article class="<section-overview-body>"><h2>{title}</h2>...</article> | "<post A title>" / "..." / "..." |
| 2 | ef-card | _cssid: "<section-overview-aside>"; heading rows + tag-row {<relation>} | @tags() | tag-row.text: on (dynamic from relation field); heading text: on | dynamic-card | <aside><ul><li>{relation.title}</li></ul></aside> | "<item / item / ...>" / empty / "..." |
| ... | | | | | | | |
```
**Mandatory columns (Blueprint):**

- **Widget** — must appear in the §2b Widget Catalog.
- **Settings** — every prop the plan binds, written as the **FULL `$$type` envelope**, not the raw value. Example: instead of `text: @tags()@post(title)@endtags()`, write `text: {$$type: string, value: "@tags()@post(title)@endtags()"}`. Responsive primitives MUST include every breakpoint's sub-envelope: `cols: {$$type: ef-responsive-string, value: {desktop: {$$type: string, value: "2fr 1fr"}, tablet: {$$type: string, value: "1fr"}, mobile: {$$type: string, value: "1fr"}}}`. Missing inner `$$type` markers cause EF to silently drop the prop at render — the `wpdev elementor:lint` envelope check catches this (added 2026-05-29). Use the PHP factory `EF\Envelope::responsive_string(...)` / `EF\Envelope::image(...)` / `EF\Envelope::vx_visibility(...)` in mutator scripts to avoid hand-authoring envelopes (see `actions.md` §Loopable action-rows). Reference the corresponding **Widget placement row** by `# index` — the orchestrator splices grid props from the Layout map into `_cssid`'s `cols` / `col_span` envelope at fan-out, so the Blueprint Settings column does NOT duplicate grid declarations.
- **Tag wrap** — `@tags()...@endtags()` for any CPT-template string (Rule 5 / [`voxel-tags.md`](../voxel/voxel-tags.md)); raw `vx` envelope for `_cssid` and image refs; static literal otherwise.
- **Dynamic affordance (per prop)** — for every prop in Settings, name its dynamic-affordance state: `on` when the value is a dynamic tag (`@tags()...@endtags()` or `@post(...)` etc.) — produces a `vx-dynamic` envelope at the EF V4 atomic-prop level; `off` when the value is a static literal — produces a plain `string` envelope; `vx envelope` when the prop type itself carries the affordance (image, link, `_cssid`, etc.). The data-wiring criterion checks this column against the Settings column — `@post(title)` text with affordance `off` is the classic "@-leakage" bug. List affordances per prop, comma-separated; for repeater rows, list per-row (e.g. `text-row-0: on, text-row-1: off`).
- **Role** — one of `static-card | dynamic-card | loop-host | loop-child | sidebar | feed | global-passthrough` (matches the role taxonomy from [`build.md`](../../workflows/build.md)).
- **Expected DOM** — a one-line HTML sketch the verification phase will assert against (selectors + expected text source). MUST cite the `_cssid` from the Settings column.
- **Pre-resolved** — for every dynamic tag, the value `wpdev voxel:data` returned on each post in the sample. A row of empty cells across the sample is a wiring red flag the data-wiring adversary surfaces.

**Improvements log (migration mode — required when the migrated copy diverges from production):**

The migration-preservation criterion compares the plan against the rendered text of the live production page (captured via the `agent-browser` CLI — [`browser.md`](../verification/browser.md) §Production-page baseline). Any information unit on production that does NOT appear in some Blueprint cell AND is NOT acknowledged in the Improvements log is a silent drop (severity `C` finding). The log shape is `improvement:<unit_id> → <new text>` (with the original text in parens) for rewrites, or `removed:<unit_id> → <reason>` for deletions. The operator inspects the log at §2g approval — it's the explicit audit trail of "what changed and why," not a forbidden-edit list.

**Layout map + Semantic HTML invariants (the hierarchy criterion enforces ALL of these):**

*Layout structure:*

- Every section has a Layout map block before its Blueprint. Missing Layout map → finding (severity `C`).
- Every Blueprint row has a corresponding Widget placement row. Mismatched count → finding (severity `C`).
- Let the content's hierarchy decide column count; prefer more sections over more columns. A grid that fights the content → finding (severity `I`) requesting justification.
- Mobile collapses to `1fr` unless the desktop grid is a small counter row of atomic items. Wrong mobile collapse → finding (severity `I`).
- No fractional col-spans. `col-span: 1.5` is invalid in CSS Grid — use named spans (1, 2, full).
- Background / vertical-rhythm / section-width values must come from the design token list (the planner cites the list — never hand-authored color values, never px / rem literals).
- Sticky behavior is only allowed on archetypes that declare it in §2c (sidebars in long-content templates).

*Semantic HTML wrapper hierarchy (every plan must satisfy this — SEO + accessibility critical):*

- The Plan Document declares a single **root wrapper** — `ef-wrapper` with `tag: main` at depth 0 of `_elementor_data`. There is exactly ONE `tag: main` per page. Multiple or missing main → finding (severity `C`).
- Each top-level section is its own `ef-wrapper` with `tag: section`, nested inside the root main. A `tag: section` at root (without main parent) → finding (severity `C`).
- Sidebar regions use `tag: aside`, NOT `tag: section`. Inline cards inside a section's grid use `tag: article` (when the card is independently meaningful — request listing, company listing) OR `tag: div` (when purely structural). Wrong tag → finding (severity `I`).
- Global templates (`header` template, `footer` template) use `tag: header` / `tag: footer` at root — these are out of single-template scope but the rule applies if the plan touches them.
- `tag: div` / `tag: span` are the fallback ONLY when no semantic tag fits (e.g. inner grid-item wrapper that's not meaningful). Every `tag: div` on an ef-wrapper at depth ≤ 2 → finding (severity `I`) — almost always a missed semantic-tag opportunity.

*SEO-compliant heading hierarchy (every plan must satisfy this — the hierarchy criterion walks document order):*

- Exactly ONE `h1` per page. The h1 lives on a heading row inside the hero section's ef-card, bound to the CPT's title-class field (typically `@post(title)`). Static h1 → finding (severity `C`) unless `override:` justifies (rare — only for landing pages with no dynamic title). Zero or >1 h1 → finding (severity `C`).
- Each section's first heading-row is `h2`, naming the section's purpose (`Overview`, `Services`, `Frequently asked questions`, etc.). Sections without an h2 → finding (severity `I`) — operator may override for purely visual sections like a CTA-footer that doesn't need a heading.
- Nested headings inside a section are `h3` (specs-grid item titles, FAQ questions, related-feed item titles). No `h2` inside another section's `h2` block. No skip from `h2` to `h4`. Skip detected → finding (severity `I`).
- A **second line** under a heading (an eyebrow, a date, a role, an author name) → the same heading row's `subtitle` cell, rendered `.ef-ih-subtitle`. Set that row's `tag` explicitly; the heading kind defaults to `h3`, so an unset `tag` promotes a decorative two-line block into the document outline. Other decorative text — taxonomy-pill labels, `"service: "` labels, sub-labels, taglines → `kind: heading, tag: span, style: ''` (plain) or `style: small` (de-emphasised, `.ef-small-style`) or `kind: rich_text` (`tag: p`), NEVER an `h*` tag. `kind: byline` and the `byline_*` cells are migrated-away (step 1336 → `kind: heading` + `subtitle`); authoring one → finding (severity `C`), and it renders empty because those cells no longer exist in the schema. Decorative content as `h*` → finding (severity `C`) — dilutes the heading outline, hurts SEO crawl. A `style` value outside the enum `['', h1..h6, small]` → finding (severity `C`); `label` and `byline_label` are both dead and render with no class.
- Body paragraphs inside heading rows → `tag: p`. Paragraphs accidentally rendered as `tag: span` or `tag: div` → finding (severity `I`).
- Card heading rows that are NOT the first row in their card (the card title) → must be `h3` or deeper if the card itself is inside an `h2`-headed section. A card with two `h2` rows → finding (severity `I`).
- The criterion walks the full document-order heading sequence `[(section_id, widget_id, row_index, tag, source_field_or_static, text_preview)]` and asserts the sequence reads as a valid outline: `h1 > h2 > h3 > h2 > h3 > h3 > h2 > h3` is fine; `h1 > h2 > h4` is not; `h1 > h2 > h2` inside the same parent is not.

**Section ordering rule.** The plan declares a section order in the Plan Document's top-level table. The hierarchy criterion checks that the order produces a valid heading sequence (h1 once, h2 per section, h3 nested inside h2, no skips) AND a valid layout flow (no aside before its main, no footer before content sections).

**Exit:** every section that appeared in §2c has Improvements-log (if applicable) + Layout map + Blueprint; every cell is filled (empty cells where data is genuinely empty are marked `(empty)` not blank); every Blueprint row has a Widget placement row.


## Plan Document Structure (the artifact at `/tmp/plan-<post_id>.md`)

```markdown
# Plan — <site> post <post_id> (<cpt_key>)

Pipeline: build|migration
Example posts sampled: <id_A>, <id_B>, <id_C>
SSOT artifact: cli/src/generated/widget-schemas.json (sha: <hash>)

## §2a Field Inventory

| Key | Type | Label | Post A | Post B | Post C | Class | Target section |
| ... |

## §2b Widget Catalog

| Widget | Source | Props count | Row surfaces | Use case |
| ... |

## §2c Archetype Selection

| Section ID | Archetype | Purpose | Fields bound |
| ... |

## §2d Section Blueprints

### Section: hero — hero
| # | Widget | Settings | Tag wrap | Role | Expected DOM | Pre-resolved (A/B/C) |
| ... |

### Section: specs — specs-grid
| ... |

...

## §2e Adversarial review

(populated by Phase 2e — one block per criterion)

### Coverage findings
- finding_id: COV-1  severity: C
  evidence: "field `<multiselect-field>` is must-class on part of the sample but no target section"
  suggested_fix: "add to specs-grid"

...

## §2f Reconciliation

### COV-1
resolved: added `<multiselect-field>` to specs-grid blueprint row 3

### DEN-2
override: density is intentionally lower than the peer single because these posts are short-lived and the related-feed archetype dominates discovery

...

## §2g Gate

(orchestrator writes the computed verdict; operator only on escalation)

GATE: green (auto)
```
