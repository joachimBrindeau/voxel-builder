# Section background rhythm with Elementor dynamic styles

Long pages should read as distinct bands rather than one undifferentiated scroll. Build that rhythm with Elementor atomic dynamic styles on each `ef-wrapper` section.

## Canonical mechanism

Use the node's atomic `settings.classes` envelope together with a matching node-local `styles` class record. The current Elementor wire format is:

- `settings.classes`: `{"$$type":"classes","value":["s-<id>-0"]}`
- `styles["s-<id>-0"]`: a class record with `id`, `type: "class"`, `label`, and responsive style entries
- each responsive entry: `meta.breakpoint`, `meta.state`, `props`, and `custom_css`
- CSS property values remain typed envelopes, for example `{"$$type":"string","value":"var(--ef-color-secondary_light)"}` or a `size` envelope

Copy the complete `styles` record shape from a current live atomic node. Do not invent an abbreviated shape, put visual choices in card or row settings, or add ad-hoc frontend classes.

```jsonc
{
  "settings": {
    "classes": {
      "$$type": "classes",
      "value": ["s-a1b2c3d-0"]
    }
  },
  "styles": {
    "s-a1b2c3d-0": {
      "id": "s-a1b2c3d-0",
      "type": "class",
      "label": "Section surface",
      "variants": [
        {
          "meta": { "breakpoint": "desktop", "state": null },
          "props": {
            "background-color": {
              "$$type": "string",
              "value": "var(--ef-color-secondary_light)"
            },
            "color": {
              "$$type": "string",
              "value": "var(--ef-color-text)"
            }
          },
          "custom_css": null
        }
      ]
    }
  }
}
```

`variants` in this wire example is Elementor's name for responsive entries inside an atomic style record. It is not a card or row presentation setting. Never write a presentation field to an `ef-card`, wrapper, content row, tag row, or action row.

## Token vocabulary

Use the live Elementor kit tokens rather than hard-coded colors:

| Visual role | Dynamic-style value |
|---|---|
| Page base | `transparent` |
| White surface | `var(--ef-color-white)` |
| Muted band | `var(--ef-color-secondary_light)` or the site's chosen light surface token |
| Primary accent | `var(--ef-color-primary)` |
| Primary soft surface | `var(--ef-color-primary_light)` |
| Body text | `var(--ef-color-text)` |
| Muted text | `var(--ef-color-text_muted)` |

Token values are kit-controlled and differ by site. Read computed styles on the target site before planning the palette:

```bash
./wpdev browser <site> "/"
agent-browser eval "(()=>{const s=getComputedStyle(document.documentElement);return JSON.stringify({primary:s.getPropertyValue('--ef-color-primary').trim(),primaryLight:s.getPropertyValue('--ef-color-primary_light').trim(),secondary:s.getPropertyValue('--ef-color-secondary').trim(),secondaryLight:s.getPropertyValue('--ef-color-secondary_light').trim(),white:s.getPropertyValue('--ef-color-white').trim(),text:s.getPropertyValue('--ef-color-text').trim()});})()" --session <s>
```

## Deterministic section precedence

Walk sections in document order and apply the first matching rule:

1. **Sections containing a strongly colored card stay on the page base.** A saturated band behind an already colored card muddies the hierarchy.
2. **Header and navigation stay on the page base.** The navbar owns its own surface.
3. **The first content section stays on the page base.** Let hero media and headings carry the opening emphasis.
4. **Use at most one accent band.** Reserve it for the conversion or climax section when its cards are neutral.
5. **Alternate muted and base bands for the remaining sections.**
6. **Avoid equal adjacent free bands.** If two neighboring free sections resolve to the same background, flip the latter. Never override rules 1 to 3 merely to force alternation.

```text
for each section S in document order:
    if S contains a strongly colored card: S.bg = transparent
    elif S is header/navigation:           S.bg = transparent
    elif S is the first content section:   S.bg = transparent
    elif S is the chosen accent:           S.bg = primary
    else:                                  S.bg = alternate(muted, transparent)

    if S.bg == previous and S is free to change:
        S.bg = the other light band

    write S.bg through S.settings.classes + S.styles
    previous = S.bg
```

## Card and row styling

Cards and rows never receive presentation fields. Apply visual treatment through the owning atomic node's dynamic styles:

- Card surface: put `background-color`, `color`, `border-color`, `border-radius`, and `box-shadow` in the `ef-card` node's style record.
- Action rows: style stable descendants from the owning card or navbar style record, such as `.ef-buttons-item` and `.ef-card-action`. Use positional selectors only when row order is intentionally fixed and verified.
- Accordion rows: target `.ef-accordion-item`, `.ef-accordion-toggle`, and `.ef-accordion-content` from the owning card.
- Table of contents rows: target `.ef-toc`, `.ef-toc-title`, and `.ef-toc-link` from the owning card.
- Tag or pill rows: target the rendered pill surface from the owning card. Keep text, links, grouping, and behavior in row data, but keep appearance in dynamic styles.
- Decorative separators: use the semantic width/spacing/color controls that remain in the current row schema. Do not resurrect removed presentation fields.

Prefer typed `props` for properties that Elementor exposes. Use `custom_css` only for stable descendant selectors that cannot be represented as root properties. Keep `custom_css` scoped with `selector` and verify the rendered selector in a browser.

## Verification

1. Run `wpdev elementor:lint <site> --post <id>`.
2. Inspect the node with `wpdev elementor:tree` or `wpdev elementor:dump` and confirm every style class in `settings.classes.value` has a matching `styles` record.
3. Confirm no card or row settings contain presentation fields.
4. In a real browser, read computed `background-color`, `color`, and `border-color` for each touched section/card and for representative action, accordion, ToC, and pill rows.
5. Check desktop, tablet, mobile, hover, focus-visible, active, and open states where applicable.
6. Confirm no two adjacent free sections accidentally share a background and no saturated card sits on a clashing saturated band.

## Checklist

- [ ] Styling is authored only through atomic `classes` plus `styles` records.
- [ ] Card and row settings contain content, behavior, and layout data only.
- [ ] Colors use live `--ef-color-*` tokens rather than hard-coded site colors.
- [ ] Root properties use typed `props`; descendant styling uses scoped `custom_css` only when necessary.
- [ ] Every referenced class id has one matching node-local style record.
- [ ] Section backgrounds follow the precedence rules and render distinctly.
- [ ] Browser verification covers responsive and interaction states.
