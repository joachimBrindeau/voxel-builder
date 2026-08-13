# EF Authoring And SSOT Contract

Current source ownership for Elementor Framework V4 authoring. Verified against the
workspace source and command registry on 2026-07-10.

## Schema Ownership

| Concern | Current owner | Verification |
|---|---|---|
| Widget/part/primitive shapes | `plugins/custom/elementor-framework/schemas/` | `wpdev elementor:codegen --check` |
| Resolved agent/CLI schema | `cli/src/generated/widget-schemas.json` | generated, never hand-edited |
| TypeScript builders/types | `cli/src/generated/widgets.ts` | generated, never hand-edited |
| Live PHP registration parity | JSON loader under `includes/schema/` | `wpdev elementor:codegen:verify <site>` |
| Golden runtime shape | live dump + schema checks | `wpdev elementor:schema:check <site>` |

Widgets compose parts; parts compose parts/primitives; primitives are leaves. Use `$part`
and `$primitive` only. Prop shape and editor control belong in the same schema declaration.
`responsive` and `dynamic` are prop modifiers, not parallel primitive families. Repeater-row
loop topology belongs to the row Part's `$envelope` declaration.
Current generated filenames come from `wpdev elementor:codegen`; do not copy older
`widget-defaults.ts`/`widget-builders.ts`/`widget-validators.ts` inventories from incidents.

## Atomic Node Detection

Use the shared CLI helpers in `cli/src/utils/elementor/tree.ts`:

- `widgetToken(node)` returns `widgetType ?? elType`.
- `isWidgetType(node, token)` handles legacy and atomic nodes.
- `isWrapper(node)` and `isWidgetNode(node)` own structural classification.
- `unwrapScalar()`/`wrapScalar()` in `envelope.ts` own envelope scalar handling.

Canonical EF V4 nodes use `{elType:'ef-card'}` with no `widgetType`. Legacy
`{elType:'widget',widgetType:'ef-card'}` is migration input, not authoring output.
Regenerate the token vocabulary with `wpdev elementor:codegen:tokens <site>`; do not
maintain a parallel widget list.

## Domain Controls

### Icons

An icon is one string cell, not `_library`/`_value`/`_dynamic` triples:
`la-solid:las la-share`, `ms:ms ms-calendar_month`, or `svg:1234`.
The current PHP surface is `ef_atomic_icon_prop()` plus `EF\Controls\Vx_Icon`
(`ef-vx-icon`). Dynamic binding uses the same `vx` envelope as other bolted strings.
Legacy triples belong only in frozen migration steps.

### Voxel-tag controls

Controls opt into dynamic tags through the registered `ef-vx-*` family. Keep one stored
value and one resolver; the bolt changes the envelope/source, not the domain storage
format. A picker-backed control needs one PHP control, one native JS renderer, one
registry row, and schema ownership. Do not add sibling static/dynamic props.

### Variants

Variant vocabulary comes from `EF_Tokens::VARIANTS` and named sets resolved by
`EF_Tokens::variant_set()`. Schemas reference the set; PHP, editor enums, and generated
CSS consume the same vocabulary. Components may expose a subset but must not invent
local spelling or color maps.

## CSS Token Rule

Global `--ef-*` tokens form a complete cascade. Consume them with bare `var(--ef-...)`.
A hardcoded fallback silently creates a second design system and is allowed only for a
documented component-local property or audited bootstrap boundary. Run
`wpdev quality elementor-framework --tool=var-fallback`; fix the token/source instead of
copying a stale literal.

## Structural Runtime

`EF\Atomic\Compat` remains the structural trait for schema identity, responsive-pair
registration, assets, settings resolution, root wrapper suppression, and editor metadata.
It is not dead compatibility glue. Remove a concern only after its replacement owns every
call site and parity test.

## Authoring Gate

1. Change the schema/source owner.
2. Run `wpdev elementor:codegen` and `--check`.
3. Query the touched prop or inspect a current live dump; never author remembered envelopes.
4. For save-path defects, capture the `save_builder` request and compare its target subtree with raw post-save `_elementor_data` to localize client versus server loss.
5. Route scalar atomic props through `wrapScalar()` before strict validation; prune only when the generated Contract marks the cell optional and its value equals the canonical default. Never infer dead data from an inactive discriminator.
6. Validate/import through `wpdev`, then verify the target subtree after save, reload, and re-save; do not use whole-document hashes because Elementor rewrites unrelated node metadata.
7. Run focused unit/schema tests and browser verification.
