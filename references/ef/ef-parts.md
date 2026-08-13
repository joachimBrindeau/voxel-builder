# EF Parts — exhaustive reference

`EF\Parts\*` are the composable building blocks that EF V4 widgets compose to avoid duplicating prop schemas, control wiring, render logic, and Twig context resolution. A widget like `ef-card` does not own the prop schema for its media slot, content-block stack, inline media, footer actions, or tag pills — those come from `Media`, `Headings` (which owns the `content_blocks` repeater + injected `inline` media), `Actions`, and `Tags` parts spread into the widget's `define_props_schema()`. The same `Media` part instance is reused three times inside `ef-card` (`media`, `logo`, `inline`) with different prefixes, and once inside `ef-wrapper` (`bg_media`). This is the entire point of the parts layer: one place to fix a bug, one place to add an option, one place to keep V4 envelope shapes consistent.

**Cross-reference**: see `ef-widgets.md` for the widgets that consume each part and which prefixes they use. The reverse index at the bottom of this file lists every (part × widget) edge.

**Source-of-truth files**: `plugins/custom/elementor-framework/includes/parts/` (23 files total under `parts/` excluding the action-handler subdir — 10 user-facing parts, 3 base contracts, 1 Media handler abstract (`Type`) + 6 Media handlers under `parts/media/`, 2 Nav helper traits under `parts/nav/`, plus `icon-functions.php`).

**Composite-repeater row expansion SSOT**: `EF\Parts\Base::expand_rows( array $settings, string $key, object $definition, string $outer_loop = '' ): array` (`parts/base.php`). Every part that owns a composite repeater (`Actions::render()`, `Headings::to_context()`, `Nav_Item::resolve_unified_rows()`, `Tags::to_context()`) flows rows through this single seam. It applies per-row `_vx_loop` expansion (via `ef_expand_definition()`) + `_vx_visibility` gating + `_ef_loop_transform` defaulting. See [`ef-helpers.md`](ef-helpers.md) for the underlying loop helper.

---

## Split Parts Catalog

| Concern | Reference |
|---|---|
| Base/render contracts and ten user-facing parts | `ef-parts-core.md` |
| Media sub-handlers, nav traits, generated part catalog | `ef-parts-media-nav.md` |
| Generated action/content/field/map/mega row surfaces | `ef-parts-row-surfaces.md` |
