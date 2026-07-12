# EF Color Tokens — Palette SSOT & `_light` Derivation

The brand palette (the `--ef-color-*` cascade) lives in one PHP constant, not in
generated CSS or Elementor kit UI. Setting a site's green/purple/etc. means editing that
constant (or the kit overrides it feeds), then regenerating. This reference carries the
**facts**; `workflows/design-tokens.md` carries the process.

## Source of truth

- **Constant:** `EF_Tokens_Runtime_Facade::DEFAULTS` in
  `plugins/custom/elementor-framework/includes/tokens/runtime-facade.php`.
- Emits the `:root{--ef-color-*}` cascade consumed by `assets/css/ef.css` and every
  widget. `ef.css` is **generated** — never edit color literals there (it is minified and
  overwritten). Change `DEFAULTS`, regenerate, verify the emitted `--ef-color-*` value.
- System color slots surfaced in the Elementor kit UI: `primary`, `secondary`, `text`,
  `accent` (`includes/tokens/admin.php`, `$system_ids`). A kit override for a system slot
  wins over the `DEFAULTS` literal at runtime — read the live kit before assuming the
  constant is the effective value.

## `_light` is derived, not authored

Every base color has a paired `_light` token used for tints, hover/selection
backgrounds, pill/tag fills, and wrapper light backgrounds.

- `_light` **auto-derives** = base white-tinted at `DERIVED_COLOR_WEIGHT` (**10%**):
  `color-mix(in srgb, <base> 10%, white)`. See `derived_color_defaults()` in
  `includes/tokens/admin.php` and the `DERIVED_COLOR_WEIGHT = 10` const in
  `runtime-facade.php`.
- The explicit `color-*_light` values in `DEFAULTS` **mirror** that 10% derivation for
  admin display only. Keep them in sync when you change a base, or they lie in the UI.
- **Do not add a new `color-<name>` unless the user explicitly asks for that named
  token.** Adding one edits shared `DEFAULTS` and changes the token vocabulary for
  every site. Most brand hues (a green, a purple) belong on an existing system slot
  (`primary`/`secondary`/`text`/`accent`) set per-site via the `ef_tokens` option —
  no framework edit. Only when an explicit request names a new token AND no slot fits
  do you add `color-<name>` (+ auto `color-<name>_light` at the same 10% rule).

### Compute a `_light` value

```
python3 -c "b='#992AA6'; c=[int(b[i:i+2],16) for i in (1,3,5)]; w=10; print('#'+''.join(f'{round(x*w/100+255*(1-w/100)):02X}' for x in c))"
# 10% weight → matches framework derivation. Use w=15 only if intentionally deviating.
```

## Extracting production colors (no source access)

To read a live site's effective palette from its served CSS:

1. Fetch page HTML, list stylesheet URLs (LiteSpeed combines into
   `wp-content/litespeed/css/<hash>.css`; Elementor per-post CSS is
   `uploads/elementor/css/post-<id>.css`).
2. Grep the combined CSS for `--e-global-color-*: #......` — these are Elementor's global
   colors. Named ones (`-primary`, `-secondary`, `-accent`, `-text`) map to intent;
   hashed IDs are custom swatches.
3. Distinguish base vs tint: an 8-digit hex (`#RRGGBBAA`) or a `color-mix` is a tint;
   a 6-digit opaque hex is a base. A production tint's alpha ≈ the intended `_light`
   weight (e.g. `#0678002A` ≈ 16%). Note that a site may tint from a **brighter** hue
   than its solid base — confirm which hue you actually want before deriving `_light`.

## Guardrails

- Consume tokens with bare `var(--ef-color-*)`; a hardcoded fallback forks the design
  system (see `ef-authoring-ssot.md` §CSS Token Rule; `--tool=var-fallback`).
- Never write brand colors as literals in widget CSS or `_elementor_data` — reference the
  token so a palette change propagates once.
