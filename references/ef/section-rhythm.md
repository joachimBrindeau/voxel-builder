# Section background rhythm (segmenting a page with alternating tints)

How to make a long page read as a sequence of distinct **bands** instead of one
undifferentiated scroll — by alternating section background tints. A reader
should be able to tell where one section ends and the next begins from the
background alone, before reading a word.

## The mechanism (read this first — it has two traps)

A section is an `ef-wrapper`. Its background is set by the **`variant` prop**
(the "surface variant"), which paints the wrapper's `--_variant-bg` slot via
`EF_Tokens::variants_css()` → `.ef-wrapper--{variant}.ef-wrapper { --_variant-bg: … }`.

**Trap 1 — `variant` ALONE does nothing.** The modifier class is only emitted
when **`bg_media_type == 'color'`** (`wrapper.php`: the variant picker is gated
on the background type being "color"). So you MUST set BOTH:

```jsonc
"variant":       { "$$type": "string", "value": "secondary" },
"bg_media_type": { "$$type": "string", "value": "color" }     // REQUIRED or variant is inert
```

Set `variant` without `bg_media_type:color` and the section stays transparent —
the class never renders. (This is the #1 reason a background "doesn't apply".)

**Trap 2 — the tint values are KIT-OVERRIDDEN; never assume.** The variant→color
map (`tinted_surface_variant_slots`) maps each variant to a `*_light` token, but
the *actual hex* comes from the site's Elementor kit and **differs per site.**
On klarc: `secondary` = `#FEF6F7` (cream), `primary` = `#E6EEEF` (light teal) —
NOT the EF defaults (`#F3F4F6`). Always read the live colors before planning the
palette:

```bash
# probe each variant's real background on the target site
./wpdev browser <site> "/"
agent-browser eval "(()=>{const o={};['transparent','white','secondary','primary'].forEach(v=>{const w=document.body.appendChild(document.createElement('div'));w.className='ef-wrapper ef-wrapper-base ef-wrapper--'+v;o[v]=getComputedStyle(w).backgroundColor;w.remove();});return JSON.stringify(o);})()" --session <s>
```

## The surface-variant palette

`SURFACE_VARIANTS = transparent | white | primary | secondary | negative | positive`.
For **segmentation** you only use the light/neutral ones; the saturated ones
(`negative`/`positive`) are status colors, never page rhythm.

| variant | role in rhythm | typical tint |
|---|---|---|
| `transparent` | the **base band** (page background shows through — usually white) | none |
| `secondary` | the **alternate light band** — the workhorse "muted" tint | pale neutral / cream |
| `primary` | **one accent band** for a CTA / closing section (read its live color — light tint on some kits, dark on others; if dark, it's a full-contrast accent, use sparingly) | brand tint |
| `white` | same as transparent on a white page — only useful when the page base is itself tinted | `#FFFFFF` |

## The bulletproof procedure: a hierarchical precedence ladder

Don't eyeball backgrounds and don't run a naïve alternation — both produce the
clash ("a tinted band behind colored cards looks bad") and the doubled-band
("two touching sections same tint"). Instead, assign each section's background by
a **strict precedence ladder**: walk the sections in document order and, for each,
apply the FIRST rule that matches. Higher rules are inviolable — a lower rule may
never override a higher one. This makes the assignment a deterministic function of
the section's content, not a judgment call.

### The ladder (highest precedence first)

**P1 — Colored-card sections are LOCKED to `transparent`.**
If a section contains *any* card whose `variant` is non-neutral (anything except
`transparent`/`white`/unset — i.e. `primary`/`secondary`/`negative`/`positive`),
the section background is `transparent`, full stop. **A tint behind a colored card
clashes** (secondary-cream band under a primary card = muddy). The card already
supplies the color hierarchy; the band must stay neutral so the card reads. This
rule is inviolable — it is never overridden by alternation or dedup below.

**P2 — Header / nav → `transparent`.** The navbar owns its own surface; it sits on
the page base.

**P3 — The hero (first content section) → `transparent`.** Let the hero's own
media/heading carry it; starting on the base makes the first tint change downstream
land harder.

**P4 — At most ONE accent band → `primary`.** Pick the single CTA / conversion /
climax section and give it `primary` *only if it has no colored cards* (else P1
already locked it transparent — then the accent is carried by its cards, which is
fine). Two accents = no accent; never exceed one.

**P5 — Everything else ALTERNATES `secondary` ↔ `transparent`.** Walk the
remaining (unlocked, non-accent) sections and flip between the two light bands.

**P6 — No two ADJACENT sections share a background.** After P1–P5, scan
neighbors: if a section's bg equals the previous section's *emitted* bg, and the
section is NOT locked by P1/P2/P3, flip it to the other light band. Locked
sections never move — if a locked `transparent` ends up beside a free
`transparent`, the free one is the one that flips (to `secondary`); if both are
locked, accept the merged white band (two neutral sections reading as one is
harmless; a clash is not).

### Why this order is bulletproof

The ladder encodes the priority of *failure costs*: a **clash (P1)** is the worst
outcome (it looks broken), so it wins over everything. A **missing boundary (P6)**
is mild (two white sections merge — still readable). Alternation (P5) is the
default texture, overridden only by the higher, content-driven rules. Because each
rule is a pure predicate on the section (does it hold a colored card? is it the
header/hero/accent?), an LLM applies the ladder by a single ordered walk — no
aesthetic guessing, and the colored-card clash can never slip through.

### Pseudocode (execute this verbatim)

```
neutral = {transparent, white, unset}
for each section S in document order:
    if S has any card with variant ∉ neutral:  S.bg = transparent   # P1 LOCK
    elif S.tag == header:                       S.bg = transparent   # P2
    elif S is the hero (first content):         S.bg = transparent   # P3
    elif S is the chosen accent:                S.bg = primary       # P4
    else:                                        S.bg = alternate(secondary, transparent)  # P5
    if S.bg == prev_emitted and S not locked(P1/P2/P3):              # P6
        S.bg = the other light band
    set S.variant = S.bg AND S.bg_media_type = "color"   # Trap 1: both required
    prev_emitted = S.bg
```

### Worked example (klarc homepage — dogfooded 2026-06-12)

12 sections. Running the ladder: the header, hero, the masonry section (holds a
`primary` teal hero card → P1 lock), and the CTA (holds colored cards → P1 lock)
all resolve to `transparent`; the remaining neutral sections alternate
`secondary` ↔ `transparent`. Result: white/cream bands segment the page, and
**every section containing a colored card is on a neutral band** — no cream tint
ever sits behind a primary/secondary card. Each section
visibly distinct, verified by reading every section's computed `background-color`
top-to-bottom (no two adjacent equal). Both traps bit during the build: first
pass set `variant` only → all sections stayed transparent (Trap 1); the palette
was confirmed by probing live colors rather than assuming EF defaults (Trap 2).

## Don't overdo it

- **Tints must stay light.** Alternating white↔cream↔white is rhythm; alternating
  white↔dark↔white is stripes — exhausting to read. Keep both alternation bands
  light; only the single accent may be saturated.
- **Full-bleed sections** (hero, accent CTA) carry their tint edge-to-edge; the
  band reads as a true horizontal stripe. Contained sections still tint their
  full wrapper width, so the rhythm holds.
- **Cards on a tinted band:** an `ef-card--white` card on a `secondary` band pops
  (white on cream); the same card on a `transparent` band needs its border to
  separate. EF already handles this — `.ef-wrapper--secondary .ef-card` rules
  adjust card chrome per surface. Don't hand-tune it.

## Checklist before shipping section rhythm

- [ ] **P1 holds (the clash rule):** every section containing a non-neutral card (`primary`/`secondary`/`negative`/`positive` variant) is `transparent` — NO tinted band behind colored cards. Verify by listing each section's `variant` against its cards' variants.
- [ ] Every section sets BOTH `variant` AND `bg_media_type: "color"` (Trap 1) — else the tint is inert.
- [ ] Palette confirmed by probing the **live** site colors, not assumed from EF defaults (Trap 2).
- [ ] Ladder applied in precedence order (P1 lock → header/hero → ≤1 accent → alternate → no-adjacent-dup); no lower rule overrode a P1/P2/P3 lock.
- [ ] At most one accent band; both alternation bands are light; only the accent may be saturated.
- [ ] Verified in a full-page screenshot that boundaries are visible AND no card sits on a clashing tint.
