# EF Masonry and CSS Grid Bento

Two different layout systems. Pick by desired behavior; never combine their rules.

| Need | Host/settings | Layout engine | Child spans |
|---|---|---|---|
| Variable-height items packed automatically | `ef-wrapper`, `mode: masonry`, responsive `cols` | CSS Columns fallback; `grid-lanes` enhancement when supported | Do not use bento span arithmetic |
| Explicit visual hierarchy with designed rectangles | Normal `ef-wrapper` grid (`mode: ""`) and track-list `cols` | CSS Grid | Responsive numeric `col_span` and `row_span` |

## Dedicated masonry mode

Use for feeds/cards whose heights vary and whose packing should be automatic. Masonry
shows all items. It is not carousel or pagination and emits no pager rows.

`cols`, `cols_tablet`, and `cols_mobile` remain responsive wrapper settings. Author them
through current schema envelopes; runtime derives an integer column count from each
track list. CSS Columns flows top-to-bottom then column-to-column and applies
`break-inside: avoid`. Browsers supporting `display: grid-lanes` receive row-major native
enhancement.

Representative resolved settings:

```jsonc
{
  "elType": "ef-wrapper",
  "settings": {
    "mode": { "$$type": "string", "value": "masonry" },
    "cols": { "$$type": "ef-responsive-string", "value": {
      "desktop": { "$$type": "string", "value": "repeat(3, minmax(0, 1fr))" },
      "tablet": { "$$type": "string", "value": "repeat(2, minmax(0, 1fr))" },
      "mobile": { "$$type": "string", "value": "1fr" }
    } }
  },
  "elements": []
}
```

Envelope detail can change. Verify target site before writing:

```bash
wpdev elementor:schema <site> ef-wrapper --prop mode
wpdev elementor:schema <site> ef-wrapper --prop cols
```

Do not add pager structure, `rows`, bento spans, or bare `grid-auto-flow`. Verify all
items render, no `.ef-pager-track`/`.ef-pager-nav` appears, each breakpoint has expected
column count, and keyboard reading order remains acceptable despite CSS Columns visual
flow.

## CSS Grid bento

Use when cell size communicates hierarchy and placement must be explicit. Keep wrapper
in normal grid mode. `cols` is a CSS track list such as `repeat(4, minmax(0, 1fr))` or
`1fr 2fr`; it is not masonry column-count guidance.

`col_span` and `row_span` are now **numeric responsive props**. Current runtime range is
1–10, default 1; `0` means auto/no modifier class. Legacy string enums (`"2"`, `"3"`,
`"4"`, `"full"`) and non-responsive string `row_span` remain migration/V3 knowledge,
not canonical new writes.

Representative span shape:

```jsonc
{
  "col_span": { "$$type": "ef-responsive-number", "value": {
    "desktop": { "$$type": "number", "value": 2 },
    "tablet": { "$$type": "number", "value": 1 },
    "mobile": { "$$type": "number", "value": 1 }
  } },
  "row_span": { "$$type": "ef-responsive-number", "value": {
    "desktop": { "$$type": "number", "value": 2 },
    "tablet": { "$$type": "number", "value": 1 },
    "mobile": { "$$type": "number", "value": 1 }
  } }
}
```

Confirm exact envelope names on target site:

```bash
wpdev elementor:schema <site> ef-card --prop col_span
wpdev elementor:schema <site> ef-card --prop row_span
```

### Bento procedure

1. Read each card's real `content_blocks` and media. Assign one anchor, optional mid
   cells, and small cells based on content—not array position.
2. Choose desktop column count and wrapper tracks.
3. Assign numeric spans. Typical start: anchor 2×2, media/long card 1×2 or 2×1,
   short card 1×1.
4. Draw a DOM-order ASCII grid. Every occupied card must form a rectangle and intended
   outer silhouette must have no accidental holes.
5. Set tablet/mobile spans explicitly; usually 1×1 for stacked reading order.
6. Render and screenshot desktop, tablet, mobile. Check hierarchy, gaps, source order,
   and bottom edge.

Example four-column plan:

```text
DOM: A(2×2) B(1×1) C(1×1) D(2×1) E(2×1) F(2×1)
A A B C
A A D D
E E F F
```

Do not teach or rely on `grid-auto-flow`. Placement behavior belongs to CSS Grid and
browser runtime; author complete source order and spans instead of inventing an atomic
setting.

## Sticky rail auto-detection

For a two-column layout, compare production geometry before writing. Mark the leading
card as a desktop-sticky candidate when it is a short thesis/intro card and the peer
column contains two or more stacked cards or media rows that continue below it.

Use a neutral nested wrapper around that leading card so grid stretch does not inflate
it. Set `full_height` to `false`; set responsive `sticky` to desktop `true` and
tablet/mobile `false`. Verify desktop sticky behavior and single-column mobile order in
browser screenshots. Do not rely only on legacy stored settings: production geometry
can preserve presentation intent that prior migrations lost.

## Repeated template grid hosts

`ef-wrapper` nodes with `mode: template` emit an identity shell only. Their own `cols`
setting does not control the layout of repeated `_vx_loop` instances. Never write
columns directly onto the template-mode loop node and assume they will apply.

For a repeated template grid:

1. keep `_vx_loop`, `mode`, and `template_id` on the template-mode wrapper;
2. place that node inside a normal `ef-wrapper` grid host;
3. set responsive `cols` on the normal host;
4. verify computed `grid-template-columns` and repeated-item widths in the browser.

Use this pattern for brand, product, article, or other saved-card loops. If repeated
cards render full-width or produce an unexpectedly tall page, inspect the parent host
before changing card spans or template content.

## Full-page screenshot geometry

EF cards use `content-visibility: auto` with a `300px` intrinsic placeholder. A browser
full-page screenshot can capture off-screen cards at that placeholder height instead of
their rendered content height, producing false blank regions and misleading section
measurements. Scrolling the page is not sufficient proof because the browser can discard
off-screen layout again before capture.

For visual-comparison and geometry audits, inject this temporary browser-only override
before measuring or taking the evidence screenshot:

```css
.ef-card {
  content-visibility: visible !important;
  contain-intrinsic-size: none !important;
}
```

Never persist this override into site CSS. Compare production and local screenshots with
the same rendering method. If a card reports exactly `300px` while its body is much
shorter, treat it as placeholder evidence first—not proof of `full_height`, wrapper rows,
or excess padding. Inspect the rendered class (`ef-card--no-full-height`), card-body
height, and grid track after forcing visibility.

The temporary browser override above is verification instrumentation only. Site output
must never receive custom CSS, inline styles, ad-hoc utility classes, Elementor style
overrides, or screenshot-targeted patches. Resolve visual differences through native EF
schema props, variants, tokens, templates, and source-owner fixes.

## Production surface ownership

Match section-wide production color with the top-level semantic wrapper's `bg_color`.
Do not imitate a continuous section surface by assigning the same card variant to every
child: that creates separate bordered islands and loses the production grouping. Use
card variants only for intentional cards inside that surface.

Map colors through live EF token names, not sampled hex values. Wrapper color requires
the complete color-mode trio: `bg_media_enabled:true`, `bg_media_type:color`, and the
token-backed `bg_color`; `bg_color` alone is inert. Set `bg_pattern:false` when production
uses a flat surface. For example, a pale brand-primary section uses wrapper color mode
with `bg_color: primary_light`; a pale primary card uses card `variant: primary`. Verify
the actual site's computed token values because `primary`, `secondary`, and their light
surfaces are site-specific. Preserve production item counts on repeated loops as part of
geometry: an incorrect loop `limit` changes section height even when grid tracks are
correct.

## Decision and verification table

| Check | Dedicated masonry | Grid bento |
|---|---|---|
| Wrapper mode | `masonry` | `""` normal block/grid |
| Wrapper columns | Responsive track lists converted to counts at runtime | Responsive track lists define grid tracks |
| Child size | Natural height, automatic packing | Numeric responsive `col_span` + `row_span` |
| Ordering | CSS Columns fallback is column-major visually | Explicit CSS Grid placement from source order |
| Pager | Forbidden/hidden; all items shown | Not implied; add pager mode only as separate design choice |
| Required proof | Item count, no pager DOM, breakpoint columns, reading order | Schema envelopes, ASCII plan, responsive spans, screenshots |

Authority: `schemas/parts/wrapper-settings.schema.json`, `includes/elements/wrapper.php`,
`assets/css/widgets/wrapper.css`, and `includes/render/grid.php`. If prose conflicts with
schema/runtime, schema/runtime wins. Run `wpdev elementor:lint <site> --post <id>` after
write and verify rendered surface.
