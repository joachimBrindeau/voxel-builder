# Masonry / Bento layouts (col-span + row-span + track ratios)

How to turn a flat grid of equal cards into a **bento masonry** — a section where
cell *size* communicates hierarchy. This is the production-safe technique for EF
V4 (native CSS `grid-lanes`/masonry is not yet production-safe across browsers —
do not use it). EF builds masonry from three primitives that already ship:

1. **Wrapper track ratios** — the section's `cols` prop (`1fr 1fr 1fr 1fr`, `1fr 2fr`, `3fr 2fr`).
2. **`col_span`** — a card consuming N column tracks (enum: `2`, `3`, `4`, `full`; responsive `ef-responsive-string`).
3. **`row_span`** — a card consuming N implicit row tracks (enum: `2`, `3`, `4`; non-responsive plain `string`).

The grid's implicit rows are content-sized and auto-created, so a `row_span:2`
card grows to occupy two stacked rows' worth of height while its short siblings
keep their natural height — that height difference is the masonry effect.

## The bulletproof procedure (do THIS, don't eyeball)

Masonry looks like an aesthetic problem but EF makes it a **deterministic
arithmetic problem** — solve it mechanically and it cannot come out wrong. The
reason: EF wrappers use `grid-auto-flow: row` (the `dense` value is silently
ignored — see Mechanics). So the browser places cards **strictly in DOM order,
left-to-right, top-to-bottom, and a card that doesn't fit in the columns left on
the current row jumps to the next row — leaving a hole behind it.** Therefore the
ONLY way to avoid holes is: **every grid row's col-spans sum to exactly C**
(the column count). That is the whole game. Follow these six steps:

### Step 1 — Classify every card by content (build a table)
For each card, read its actual content (`wpdev elementor:tree <site> <post_id>`
or its `content_blocks` / `media_*` settings) and assign a **weight class**:

| Weight | Trigger (read the card) | Footprint (cols × rows) |
|---|---|---|
| **A — anchor** | the section's thesis / most important card; carries media AND heading+body | `2 × 2` |
| **B — tall** | carries media (image/video) but is not the anchor | `1 × 2` |
| **C — wide** | long body (≥3 lines) and no media | `2 × 1` |
| **D — small** | short body (≤2 lines), no media | `1 × 1` |

Media lives on an A or B card — **never on a D**. If the only image is sitting on
a small card, move it onto the anchor (Step 6 re-checks the donor).

### Step 2 — Pick the column count C
`C = 4` for 5–8 cards, `C = 3` for 3–4 cards, `C = 2` for 2 cards. More cards →
more rows, not more columns (never widen past what content justifies).

### Step 3 — Cell-budget check (necessary condition)
Sum every card's cells: `T = Σ (cols × rows)`. The block can only be a rectangle
if **`T` is a multiple of `C`**. `rows_used = T / C`. If `T` isn't a multiple of
C, change one card's footprint (Step 1 weights have slack: a C↔D or B↔A swap
shifts T by ±1 or ±2) until it divides. *Example (klarc, C=4): A(4)+B(2)+D(1)+D(1)
+? — that's 8 so far for the first cards; the last two D cards at 1+1 give T=10,
not ÷4. Promote both trailing D→C (2+2): T=12=4×3. Rectangle possible.*

### Step 4 — Place cards with the real CSS rule: forward-only cursor in DOM order
EF grids are `grid-auto-flow: row` (NOT `dense` — see Mechanics). The placement
cursor moves **forward only**: for each card in DOM order it advances left → right
then down, and drops the card at the first spot **at or after the cursor** where
its full `cols × rows` footprint fits. Critically — **a gap the cursor has already
passed is NEVER backfilled.** (Verified empirically: a 3-wide card that can't fit
the 2 columns left on a row drops to the next row, and the 2 cells it skipped stay
**permanently empty** — a later `1×1` lands *after* the cursor, not back in the
hole. Only `grid-auto-flow: row dense` would backfill, and EF ignores `dense`.)

Consequences you must simulate:
- A `2×2` anchor placed first occupies cols 0–1 of rows 0 AND 1 — so on rows 0
  and 1 only cols 2–3 remain for the next cards.
- A wide card that doesn't fit the columns left on the current row drops to the
  next row and **leaves a permanent hole** in the skipped cells.

Because there is no backfill, the only safe layout is one where **the cards, in
DOM order, fill each row to exactly C with no skipped cell** — which is precisely
what Step 3 (budget ÷ C) and Step 5 (ASCII gate) enforce. DOM order is the lever:
put the anchor first, then order the remaining cards so each row's running width
closes to exactly C before the next row begins.

### Step 5 — Draw the ASCII grid and VERIFY (the gate)
Before writing any `_elementor_data`, render the plan as a `C`-wide character
grid, one letter per card, one cell per character. Every cell MUST be filled and
every card's letters must form a solid rectangle of its `cols × rows`:

```
C = 4, DOM order: A(2×2) B(1×1) C(1×1) D(2×1) E(2×1) F(2×1)
A A B C     row 1  (A cols1-2 + B + C = 4 ✓)
A A D D     row 2  (A continues cols1-2; D=2×1 closes cols3-4 = 4 ✓)
E E F F     row 3  (two 2×1 closers = 4 ✓)
```
(This is the verified klarc grid — every letter is a solid rectangle of its
footprint, every row is exactly 4 wide, no blank cell.)
If any cell is blank, or a letter isn't a clean rectangle, or a row ≠ C wide →
**the layout has a hole; go back to Step 3/4.** Do not proceed to write until the
ASCII grid is a fully-filled C×rows_used block. This drawing step is the
bullet-proofing: an LLM that draws the grid *cannot* ship the bottom-right hole.

### Step 6 — Emit, then re-verify in a browser screenshot
Write the spans, render the live page, screenshot the section, and confirm the
silhouette is a filled rectangle (check the bottom-right corner specifically) and
each large cell is *full* of content (no empty 2×2). If you moved media in Step 1,
confirm the donor card didn't end up empty.

The prose below explains *why* these rules hold; the six steps above are *what to
execute*. When in doubt, draw the ASCII grid.

## The one rule: size = hierarchy

A flat grid where every card is the same size is "a card layout with rounded
corners, not bento" — the exact failure mode this reference fixes. Hierarchy
comes from size variation:

- **One anchor per block.** Exactly one hero cell (the most important card) gets
  the biggest footprint — typically `col_span:2 + row_span:2`. Two heroes per
  visible block is the practical ceiling; three cancel each other out (the eye
  loses its anchor).
- **One or two mid cells.** A card with an image or a longer body earns
  `row_span:2` (tall) so the image has room and the column stays balanced.
- **The rest stay 1×1.** Small cards flow around the anchors. Content earns
  small; don't inflate a one-line card.
- **Larger cell = more whitespace**, not more crammed content.

If every card is equally important, you don't want masonry — use a plain uniform
grid. Masonry is a hierarchy tool.

## The non-negotiable rule: the block must tile to a complete rectangle

A bento block's outer silhouette must be a filled rectangle — **no holes, no
stair-step bottom edge.** A hole (a tall hero leaving the bottom-right cells
empty) reads as broken, not intentional. Because the grid never backfills (Step
4), this is purely the arithmetic the procedure already enforces:

> **`Σ (col_span × row_span) over all cards  ==  C × rows_used`** (Step 3), AND
> **every row fills to exactly C in DOM order** (Step 4), AND
> **the ASCII grid has no blank cell** (Step 5).

When the budget doesn't divide or a row falls short, widen a card (`col_span`) or
promote a weight class until the rectangle closes. The Worked example below walks
the klarc case through all six steps.

## Derive spans from each card's CONTENT, not by position

Don't assign spans by slot — **read what each card holds** and let the content
type pick the footprint. This is the step that's easy to skip and produces
"content not recognized" layouts:

| Card content | Footprint | Why |
|---|---|---|
| Section thesis / hero statement (longest, most important) | `col_span:2 + row_span:2` | The anchor — earns the dominant cell |
| Has an **image / media** | `row_span:2` (tall) | The image needs vertical room; a 1×1 crops it to a sliver |
| Long body (3+ lines) | `row_span:2` *or* `col_span:2` | Give the text room; tall if in a multi-row column, wide if on the closing row |
| Short body (1–2 lines), no media | `1×1`, or `col_span:2` **only to close the rectangle** | Stays small unless arithmetic needs it wide |

**A large cell must be FILLED, not just big.** The hero footprint (`2×2`) has to
be earned by enough content to occupy it — ideally **media + text together**. If
the section has one image and a `2×2` thesis card, put the image *on the hero*
(media top, heading+body below) so the big cell is full; don't leave the hero as
a near-empty text card while a *small* card carries the photo (the photo then
can't breathe and the hero looks hollow — the "media on the wrong card" mistake).
When you move media onto the hero, re-check the card that lost it: it usually
drops to `1×1`, which changes the cell arithmetic — re-close the rectangle.

Inspect the actual card before composing: does it carry a media block? how many
lines is its body? what's its `variant` (a `primary`/branded card is usually the
hero)? Use `wpdev elementor:tree <site> <post_id>` or read `content_blocks` to
classify each card, then apply the table — never guess from grid position.

## Worked example (klarc homepage "synergie" block — dogfooded 2026-06-12)

Six cards, originally a flat `1fr 1fr 1fr 1fr` grid of six identical 276×304
tiles (the bad state). The fix, on the section wrapper + its card children:

| Card | content | col_span | row_span | cells | placement |
|---|---|---|---|---|---|
| La synergie (teal `primary`) | hero thesis | `2` | `2` | 4 | rows 1–2, cols 1–2 |
| Comprendre | has image | — | `2` | 2 | rows 1–2, col 3 |
| Identifier | short body | — | — | 1 | row 1, col 4 |
| Agir | short body | — | — | 1 | row 2, col 4 |
| Piloter | short body | `2` | — | 2 | row 3, cols 1–2 |
| Notre but | short body | `2` | — | 2 | row 3, cols 3–4 |

Section wrapper at `cols: 1fr 1fr 1fr 1fr`. Cell arithmetic: 4+2+1+1+2+2 = **12 =
4 cols × 3 rows** → the block tiles to a complete rectangle, no holes. The two
bottom cards are widened to `col_span:2` *specifically to close row 3* (left at
1×1 they leave the bottom-right empty — the first wrong attempt). Reading
hierarchy from size: one 2×2 hero, one 1×2 image card, two 1×1 smalls, two
half-width closers.

Iteration history (why each step): (1) flat 6×(1×1) → no hierarchy. (2) hero
`row_span:2` only → "two tall left cards" reads as two anchors, not one. (3) hero
`col_span:2 + row_span:2` → clear single anchor BUT bottom-right hole (smalls
left 1×1). (4) bottom two → `col_span:2` → rectangle closes. **The hole in (3)
is the lesson: a dominant hero forces you to re-balance the remaining cards so
the silhouette stays rectangular.**

## Track-ratio masonry (the `1fr 2fr` family)

When the asymmetry is *columnar* rather than tile-by-tile, encode it in the
wrapper `cols` ratio instead of per-card spans:

- `1fr 2fr` / `2fr 1fr` — a narrow rail beside a wide main (text + feature, or
  sidebar + content). The wide column is the visual anchor; no card spans needed.
- `3fr 2fr` — a softer split for two near-peer cards where one still leads
  (already used on klarc's homepage CTA section `b0bbcca`).
- Combine with spans: a `1fr 1fr 1fr` grid with one `col_span:2` card creates a
  wide-then-narrow rhythm without a second media query.

Pick track-ratio when the whole column is asymmetric; pick per-card spans when
individual tiles within an even grid need to pop.

## Mechanics & gotchas

- **`row_span` is a no-op on a single-row grid.** It only produces height when
  the grid actually has N+ rows of items. On mobile (grid collapses to `1fr`,
  single column) every span becomes inert and cards stack in DOM order — which
  is the correct responsive collapse, automatically. No mobile-specific span
  values needed.
- **`row_span` is NON-responsive** (one plain-string value at every breakpoint),
  unlike `col_span` (responsive `ef-responsive-string` with desktop/tablet/mobile).
  This is intentional: `grid-row: span N` is structural, and the single-column
  mobile collapse already neutralizes it. Don't look for a `row_span_tablet`.
- **No `full` for row_span.** A row span is content-count-bounded (implicit rows
  created on demand), not bounded by a fixed track count, so "span every row"
  has no stable meaning. `col_span` has `full` (= `1 / -1`); `row_span` does not.
- **`grid-auto-flow: row dense` does NOT take as a bare wrapper setting** — it's
  an atomic *style-schema* prop, not a settings key, so setting
  `settings['grid-auto-flow']` is silently ignored. The flow stays plain `row`,
  which is **forward-only and never backfills** (Step 4): a cell the cursor
  passed stays empty forever. So you cannot rely on `dense` to fill gaps — you
  must lay the cards out (DOM order + spans) so no gap is ever left. This is why
  the Step 3 budget + Step 5 ASCII gate are mandatory, not optional polish.
- **DOM order = source order.** EF masonry preserves source order (unlike the old
  CSS-columns hack), so keyboard/tab order matches the visual reading order. Keep
  the hero first in the children array.

## Storage shapes (for direct `_elementor_data` writes)

```jsonc
// col_span — responsive envelope on the card's settings
"col_span": { "$$type": "ef-responsive-string", "value": {
  "desktop": { "$$type": "string", "value": "2" },
  "tablet":  { "$$type": "string", "value": "" },   // "" = inherit/auto
  "mobile":  { "$$type": "string", "value": "" }
}}

// row_span — plain string on the card's settings (NON-responsive)
"row_span": { "$$type": "string", "value": "2" }
```

Empty string = Auto (no modifier class emitted). Frontend classes:
`ef-col-span-{2,3,4,full}`, `ef-col-t-span-*` (tablet), `ef-row-span-{2,3,4}`.

## Checklist before shipping a masonry section

- [ ] **Drew the ASCII grid (Step 5) and it is a fully-filled C×rows_used block** — every cell a letter, every card a solid rectangle, every row exactly C wide. This single gate subsumes the arithmetic check and is the bullet-proofing — if you skipped it, stop and draw it.
- [ ] **Cell budget divides:** `T = Σ(col_span × row_span)` is a multiple of `C`; `rows_used = T/C`. No hole / stair-step bottom edge.
- [ ] Each card's footprint was **derived from its content** (media → tall, hero thesis → 2×2, short body → 1×1 or widened only to close the rectangle) — not assigned by grid position.
- [ ] Exactly one hero anchor (biggest footprint); ≤2 heroes total.
- [ ] Small cards stay 1×1 unless arithmetic needs them wide; no uniform-everywhere grid masquerading as bento.
- [ ] Hero is first in DOM order (source order = reading order).
- [ ] Verified the desktop render in a browser screenshot — spans produced size variation AND the block is a filled rectangle (check the bottom-right corner specifically).
- [ ] Confirmed mobile collapses to a single stacked column (spans inert, DOM order sane).
