# EF Design Tokens Workflow — Brand Palette Setup

Set or change a Voxel/EF site's brand colors (primary/secondary/accent + custom hues like
a brand purple) at the **token source of truth**, so every widget and generated stylesheet
inherits the change once. Owns the `--ef-color-*` palette; does not author per-widget CSS.

> **Never add a new token unless the user explicitly asks for one.** A new
> `color-<name>` in `DEFAULTS` changes the shared framework vocabulary for **every**
> site. Default to the existing **system slots** (`primary`, `secondary`, `text`,
> `accent`) set per-site via the `ef_tokens` option. Adding, renaming, or removing a
> `DEFAULTS` key is a framework change — do it only on an explicit, in-scope request,
> and never infer it from a branding task that a system slot can hold.

Mandatory companion read: [`../references/ef/ef-color-tokens.md`](../references/ef/ef-color-tokens.md)
(palette SSOT, `_light` 10% derivation, extraction method). Process lives here.

## When to run this workflow

- "Set the site's primary green and brand purple as EF tokens."
- "Match production colors from `<url>` into the framework palette."
- "Add a `_light` (opaque ~tint) variant for a brand color."
- "Change the accent/secondary color across the whole site."

For consuming existing tokens in a widget/template, that is `build.md`. For a hardcoded-
literal lint failure, that is `--tool=var-fallback` (see `ef-authoring-ssot.md`).

## Hard stops

Halt and resolve before mutating:

- Target site and intended base hex per slot are unknown.
- You are about to edit color literals in generated `assets/css/ef.css` (forbidden — it is
  overwritten). Only `DEFAULTS` / the kit is authoritative.
- A system slot (`primary`/`secondary`/`text`/`accent`) has a **kit override** you have
  not read — the constant may not be the effective value.
- You cannot regenerate + read back the emitted `--ef-color-*` value.
- You are about to add/rename/remove a `DEFAULTS` color key without an explicit user
  request naming that token. Map the hue to a system slot instead, or stop and ask.
- The requested brand hue can fit an existing system slot but you are reaching for a
  new custom token anyway. Prefer the slot.

## Entry criteria

1. Companion reference read; palette SSOT + `_light` rule understood.
2. Base hex chosen per slot (opaque 6-digit). Source: brand decision or extracted from a
   live site (reference §Extracting).
3. Decided which hues are **system slots** vs **custom** `color-<name>` additions.
4. `_light` weight decided — **10%** (framework default) unless intentionally deviating.

---

## Phase 1 — Resolve the palette

**Entry:** Entry criteria met.

1. List each token to set: base name, base hex, intent (system slot or custom).
2. If matching a production site, extract effective colors per reference §Extracting;
   record which hex is a **base** and which is a **tint**, and which hue the tint derives
   from (may differ from the solid).
3. Compute each `_light` at the chosen weight (reference §Compute). Record base→`_light`
   pairs.

**Exit:** A palette table: `color-<name>` → base hex, `color-<name>_light` → derived hex.

## Phase 2 — Capture rollback

**Entry:** Palette resolved.

1. Record current `DEFAULTS` color block (git diff baseline is enough) and, for system
   slots, the current live kit override value.
2. Note the current emitted `--ef-color-<name>` from the generated cascade for before/after
   comparison.

**Exit:** Rollback evidence captured for every token you will touch.

## Phase 3 — Write the source of truth

**Entry:** Rollback captured.

1. Edit `DEFAULTS` in
   `plugins/custom/elementor-framework/includes/tokens/runtime-facade.php`:
   set/add each `color-<name>` base and its mirrored `color-<name>_light`.
2. **Only if the user explicitly requested a new named token** and no system slot fits:
   add both `color-<name>` and `color-<name>_light` to shared `DEFAULTS` (framework
   change — separate commit, note the scope). Otherwise assign the hue to a system slot.
3. For a **system slot** whose effective value comes from a kit override, update the kit
   value too (constant alone will not win). Keep the constant in sync as the fallback.
4. Do not touch generated `ef.css` or any widget literal.

**Exit:** `DEFAULTS` (and kit, if applicable) hold the new base+`_light` pairs.

## Phase 4 — Regenerate & lint

**Entry:** Source edited.

1. Regenerate EF assets through the repo workflow (`wpdev elementor:codegen` + `--check`),
   so the emitted `:root{--ef-color-*}` cascade reflects the new values.
2. Run `./wpdev quality elementor-framework --tool=var-fallback` to confirm no hardcoded
   literal now shadows the token.
3. Run the relevant `./wpdev quality elementor-framework` gate for touched PHP.

**Exit:** Assets regenerated clean; lint green.

## Phase V — Verify

**Entry:** Regenerated + linted.

1. Read back the emitted `--ef-color-<name>` and `--ef-color-<name>_light` from the
   generated cascade; assert they equal the Phase 1 table.
2. Confirm `_light` = base tinted at the intended weight (spot-check one pair).
3. Load a page using each color (base + a tint surface: hover/selection/pill/light bg);
   confirm the new hue renders and the tint is legible.
4. For system-slot changes, confirm the Elementor kit UI shows the new swatch.

**Exit:** Emitted tokens equal the resolved palette; base + `_light` render correctly on a
live surface; before/after delta matches intent.

## Worked example — best-matcha

Brand green + brand purple, no new token added:

- green → **`primary`** system slot; purple → **`secondary`** system slot.
- Per-site only: `wp <site> option update ef_tokens '{"color-primary":"#067800","color-secondary":"#992AA6"}' --format=json`, then `wp <site> ef tokens sync`
  (projects to kit, clears CSS bundle, purges LiteSpeed).
- `_light` auto-derived at 10%: `#E6F2E6` / `#F5EAF6`. No `DEFAULTS` edit, no new
  `color-purple` token.

## Exit artifact

Read-back-equal `--ef-color-*` cascade (base + derived `_light`) sourced from `DEFAULTS`
(and kit for system slots), regenerated, var-fallback-clean, and browser-verified on a
base and a tint surface.
