# EF Helpers: Loops, Actions, Links, And Responsive Primitives

## Loop

Loop expansion + transform machinery. Distinct from Voxel sub-resolvers — these are the **generic** loop helpers (composite-repeater row expansion, visibility per row, transform application).

### Full-doc helpers

#### ef_expand_definition( $definition, $rows, $outer_loop )
- **Signature**: `function ef_expand_definition( object $definition, array $rows, string $outer_loop = '' ): array`
- **File**: `includes/loop/expansion.php:17`
- **Behavior**: Expand composite-repeater rows through their row definition (Action, Heading, Tag, etc.). For each row: read its `_vx_loop` cell, iterate the looper, and call `$definition->resolve_row()` per item.
- **Returns**: Flat list of resolved row blocks (heading-blocks for Heading, action-items for Action, etc.).
- **Used by**: `Headings::to_context()`, `Tags::to_context()`, `Actions::render()`.

#### ef_expand_row_loops( $rows, $row_renderer, $outer_loop )
- **Signature**: `function ef_expand_row_loops( array $rows, callable $row_renderer, string $outer_loop = '' ): array`
- **File**: `includes/loop/expansion.php:25`
- **Behavior**: Expand rows through a caller-supplied `$row_renderer` callback. Used by `Nav_Item` whose row resolution isn't a single per-row method.
- **Returns**: Flat list of whatever the renderer returns per call.

#### ef_iterate_voxel_loop( ... )
- **Signature**: `function ef_iterate_voxel_loop( string $loop_key, int $limit, int $offset, callable $per_item, ?array $transforms = null ): void`
- **File**: `includes/loop/iteration.php:61`
- **Behavior**: Core Voxel loop iterator. Resolves `$loop_key` via the looper, applies `$transforms` (filter/sort/reverse) when supplied, then calls `$per_item($item, $index)` for each. Note: the `$transforms` parameter is still accepted by signature but the transform layer (`_ef_loop_transform` row cell + per-row transform helpers) is retired in the current EF tree — callers should pass `null` and let row-definition resolvers handle ordering instead.
- **Used by**: every loop driver (rows, widgets, navbar tree).

#### ef_with_voxel_loop( $settings, $callback )
- **Signature**: `function ef_with_voxel_loop( array $settings, callable $callback ): void`
- **File**: `includes/loop/iteration.php:180`
- **Behavior**: Read `_vx_loop` from settings → call `ef_iterate_voxel_loop` → for each item, push post context, run `$callback`, pop post context.
- **Used by**: widget-level loops (replicate full widget per item).

#### ef_with_voxel_query_loop( $settings, $callback )
- **Signature**: `function ef_with_voxel_query_loop( array $settings, callable $callback ): void`
- **File**: `includes/loop/iteration.php:257`
- **Behavior**: WP_Query-driven counterpart to `ef_with_voxel_loop`. Resolves a query-source row (via `ef_row_loop_query`) into a WP_Query and walks results, pushing per-post context per iteration.

#### ef_row_loop_settings( $row )
- **Signature**: `function ef_row_loop_settings( array $row ): array`
- **File**: `includes/loop/config.php:32`
- **Behavior**: Read the `_vx_loop` cell from one composite-repeater row.
- **Returns**: `{tag, limit, offset}` or empty array.

#### ef_row_loop_query( $row )
- **Signature**: `function ef_row_loop_query( array $row ): ?array`
- **File**: `includes/loop/config.php:68`
- **Behavior**: Read the row's WP_Query loop config (post type, count, args) — pairs with `ef_with_voxel_query_loop`.

#### ef_row_visibility_passes( $row )
- **Signature**: `function ef_row_visibility_passes( array $row ): bool`
- **File**: `includes/loop/visibility.php:17`
- **Behavior**: Visibility check for one composite-repeater row. Reads `_vx_visibility` cell and dispatches to Voxel's visibility resolver. Returns `true` if no rules.

#### ef_visibility_passes( $settings )
- **Signature**: `function ef_visibility_passes( array $settings ): bool`
- **File**: `includes/loop/visibility.php:24`
- **Behavior**: Visibility check for a widget instance.

**Retired** (no replacement — transform layer removed from EF): `ef_with_voxel_loop_transformed`, `ef_row_loop_transforms`, `ef_loop_transform_defaults`, `ef_loop_transforms_active`, `ef_loop_apply_transforms`. Row-definition `resolve_row()` implementations now handle filter/sort/reverse inline.

---
## Voxel sub-resolvers

The Voxel-specific resolvers that bridge `_vx_loop` and `_vx_visibility` cells to the looper/visibility APIs.

### Full-doc helpers

#### ef_voxel_resolve_loop( $settings )
- **Signature**: `function ef_voxel_resolve_loop( array $settings ): array`
- **File**: `includes/voxel/loop-resolver.php:40`
- **Behavior**: Resolve a widget's `_vx_loop` cell to looper params `{tag, limit, offset}`. Returns empty array if no loop or Voxel unavailable.

#### ef_voxel_resolve_visibility( $settings )
- **Signature**: `function ef_voxel_resolve_visibility( array $settings ): array`
- **File**: `includes/voxel/visibility-resolver.php:36`
- **Behavior**: Resolve `_vx_visibility` rules → `{behavior:'show'|'hide', rules:[…]}` or empty.

**Retired** (transform sub-resolver removed alongside the row-level transform layer): `ef_voxel_resolve_transform`, `ef_voxel_sort_args`, `ef_voxel_apply_transform`.

---

## Action types & controls

The action surface — 28 action types (link, call, send_email, open_modal, scroll_to_section, share_post, add_to_cart, edit_post, …), per-type field specs, V3 round-trip, V4 atomic props/controls, render resolution. Build agents reach for `ef_atomic_action_props()` to add an action slot to a widget; audit agents reach for `ef_action_types()` to validate types.

### Full-doc helpers

#### ef_action_types()
- **Signature**: `function ef_action_types(): array`
- **File**: `includes/catalogs/action-types.php:111`
- **Behavior**: Registry of `EF_ACTION_*` constants → label map. ~28 types total (link, get_directions, call, send_email, open_modal, scroll_to_section, action_gcal, action_ical, share_post, add_to_cart, promote_post, action_follow_post, action_follow, action_save, edit_post, delete_post, unpublish_post, publish_post, show_post_on_map, view_post_stats, go_back, select_addition, back_to_top, open_vx_inbox, open_vx_notifications, open_vx_cart, open_vx_user_menu). Read `ef_action_types()` body for the authoritative current list.

#### ef_action_field_specs()
- **Signature**: `function ef_action_field_specs(): array`
- **File**: `includes/catalogs/action-types.php:189`
- **Behavior**: Per-type input specs. Each spec is `{key, type:'link'|'text'|'phone'|'email'|'select', scope:'both'|'scalar', v3_key:'string', shown_when:[…]}`.
- **Returns**: `array` of specs (one per per-type field across all action types).

#### ef_action_storage_keys( $prefix )
- **Signature**: `function ef_action_storage_keys( string $prefix = '' ): array`
- **File**: `includes/catalogs/action-types.php:276`
- **Behavior**: All storage keys for the scalar action suite (e.g., for one slot: `<prefix>_action_type`, `<prefix>_action_link`, …).

#### ef_atomic_action_types()
- **Signature**: `function ef_atomic_action_types(): array`
- **File**: `includes/action-controls.php:132`
- **Behavior**: V4-compatible action types list (subset of `ef_action_types()` that work in V4 atomic). Use this for action-type select options in V4 controls.

#### ef_atomic_action_props( $prefix )
See [Atomic V4](ef-helpers-atomic-settings.md#atomic-v4).

#### ef_atomic_action_controls( $prefix )
- **Signature**: `function ef_atomic_action_controls( string $prefix = '' ): array`
- **File**: `includes/action-controls.php:209`
- **Behavior**: Scalar action suite controls (Vx_Select for type + per-spec controls with `set_dependencies(ef_show_when(...))` gating).

#### ef_action_spec_to_prop( $spec )
- **Signature**: `function ef_action_spec_to_prop( array $spec ): Prop_Type`
- **File**: `includes/action-controls.php:190`
- **Behavior**: Single field spec → Prop_Type (Lenient_Url for link, String_Prop_Type for text/phone/email).

#### ef_action_block_from_row( $row )
- **Signature**: `function ef_action_block_from_row( array $row ): array`
- **File**: `includes/action-controls.php:252`
- **Behavior**: `{href, attrs}` block from one composite row's action cells.

#### ef_action_surface_class( $variant, $embedded, $extra )
- **Signature**: `function ef_action_surface_class( string $variant, bool $embedded = false, array $extra = [] ): string`
- **File**: `includes/action-controls.php:98`
- **Behavior**: Pre-built action surface class string — `ef-action ef-action--{variant} ef-action--{embedded?inline:button} {extra…}`.

#### ef_action_type_options( $include_none )
- **Signature**: `function ef_action_type_options( bool $include_none = true ): array`
- **File**: `includes/action-controls.php:116`
- **Behavior**: Select options for the action-type dropdown.

#### ef_directions_url( $address )
- **Signature**: `function ef_directions_url( string $address ): string`
- **File**: `includes/action-controls.php:31`
- **Behavior**: Google Maps directions URL builder (`https://www.google.com/maps/dir/?api=1&destination=...`).

#### ef_gcal_url( $start, $end, $title, $desc, $location )
- **Signature**: `function ef_gcal_url( string $start, string $end, string $title, string $desc = '', string $location = '' ): string`
- **File**: `includes/action-controls.php:50`
- **Behavior**: Google Calendar "add event" URL builder.

#### ef_twig_link( $action )
- **Signature**: `function ef_twig_link( array $action ): array`
- **File**: `includes/action-controls.php:279`
- **Behavior**: V3-shape adapter for Twig action consumption. Converts a V4-resolved action block into the legacy shape Twig partials expect.

#### ef_twig_rel_attr( $link, $target )
- **Signature**: `function ef_twig_rel_attr( array $link, string $target ): string`
- **File**: `includes/action-controls.php:304`
- **Behavior**: `rel="…"` attribute string from a link block (adds `noopener noreferrer` for `_blank`).

#### ef_render_icon_html( $icon, $attrs )
- **Signature**: `function ef_render_icon_html( array $icon, array $attrs = [ 'aria-hidden' => 'true' ] ): string`
- **File**: `includes/action-controls.php:327`
- **Behavior**: Render an `Icons_Manager`-shape icon array to HTML. Used by action button rendering.

**Retired**: `ef_resolve_actions( Element_Base $widget, array $actions, bool $embedded, string $suffix )` — the `Resolver` flow is now invoked directly from `Actions::render()` / `Action_Slot::to_render_item()` rather than via a free helper.

---

## Icon helpers

Icon resolution for atomic widgets (composite-row icon cells, action-type icons, etc.). Bridges the V4 `String_Prop_Type` storage to `Icons_Manager`-shape render arrays.

### Full-doc helpers

#### ef_atomic_icon_prop( $base )
- **Signature**: `function ef_atomic_icon_prop( string $base ): array`
- **File**: `includes/parts/icon/functions.php:21`
- **Behavior**: Single `String_Prop_Type` for an icon slot. Returns `[ "<base>" => String_Prop_Type ]`.
- **Example**: `array_merge( $schema, ef_atomic_icon_prop( 'icon' ) )` → adds `'icon' => String_Prop_Type`.

#### ef_atomic_icon_resolve( $cells, $base )
- **Signature**: `function ef_atomic_icon_resolve( array $cells, string $base = 'icon' ): array`
- **File**: `includes/parts/icon/functions.php:64`
- **Behavior**: Resolve a row's icon cells to `{library, class, had_dtag}`.
- **Returns**: 3-cell array or empty when no icon.

#### ef_atomic_icon_html( $cells, $base, $wrapper )
- **Signature**: `function ef_atomic_icon_html( array $cells, string $base = 'icon', string $wrapper = 'ef-ih-icon' ): string`
- **File**: `includes/parts/icon/functions.php:116`
- **Behavior**: Full HTML capture for an icon (resolve + render in one call).

#### ef_atomic_icon_placeholder()
- **Signature**: `function ef_atomic_icon_placeholder(): array`
- **File**: `includes/parts/icon/functions.php:89`
- **Behavior**: Placeholder icon for unresolved dtag (editor only — surfaces a "question mark" sprite to indicate the dtag didn't render).

The companion control helpers `ef_atomic_icon_control` (`Vx_Icon` builder) and `ef_atomic_icon_class_resolved_empty` (resolved-class emptiness predicate) live alongside in `parts/icon/functions.php` — re-grep for current line offsets.

---

## Links

Link normalization + URL builders.

### Full-doc helpers

#### ef_build_attributes( $widget, $key, $href, $extras, $extra_attrs )
- **Signature**: `function ef_build_attributes( Element_Base $widget, string $key, string $href, array $extras = [], string $extra_attrs = '' ): string`
- **File**: `includes/links.php:44`
- **Behavior**: Pre-escaped attribute fragment (`href="..." rel="..." target="..." data-...`). Use when rendering a link directly to HTML rather than going through a Twig macro.

#### ef_link_normalize( $link )
- **Signature**: `function ef_link_normalize( $link ): array`
- **File**: `includes/links.php:102`
- **Behavior**: Normalize a Link envelope → `{href, attrs}`. Accepts V4 link object, V3 `{url, is_external, nofollow}`, or raw string.
- **Returns**: `['href' => '…', 'attrs' => ['target' => '_blank', 'rel' => '…']]` (attrs may be empty).

#### ef_tel_url( $phone )
- **Signature**: `function ef_tel_url( string $phone ): string`
- **File**: `includes/links.php:72`
- **Behavior**: Sanitize phone → `tel:…` URL (strips spaces, hyphens, parens; keeps leading `+`).

#### ef_mailto_url( $email )
- **Signature**: `function ef_mailto_url( string $email ): string`
- **File**: `includes/links.php:81`
- **Behavior**: Sanitize email → `mailto:…` URL.

---

## Responsive primitives

Responsive envelope builders + flatten functions. EF widgets use these to read a `{desktop, tablet, mobile}` cell down to the active value at render time.

### Full-doc helpers

#### ef_responsive_default_envelope_typed( $atom, $desktop, $empty )
- **Signature**: `function ef_responsive_default_envelope_typed( string $atom, $desktop, $empty ): array`
- **File**: `includes/responsive.php:54`
- **Behavior**: Build a typed `{desktop, tablet, mobile}` envelope at rest. Each cell is `{$$type: $atom, value: …}`; non-desktop cells get `$empty` (typically `''` for strings, `false` for booleans).
- **Used by**: Responsive_Select, Responsive_Switch, Responsive_Text default-value builders.

#### ef_responsive_select_pair( $key, $options, $label, $non_desktop_options, $desktop_default )
- **Signature**: `function ef_responsive_select_pair( string $key, array $options, string $label, ?array $non_desktop_options = null, string $desktop_default = '' ): array`
- **File**: `includes/responsive.php:96`
- **Behavior**: `[prop, control]` for a Responsive_Select. Pass `$non_desktop_options=null` (default) to reuse the desktop enum on tablet/mobile; pass an explicit array (e.g., desktop options + `'inherit'`) to widen non-desktop cells.
- **Returns**: `['prop' => Responsive_String, 'control' => Responsive_Select]`

#### ef_responsive_text_pair( $key, $label, $desktop_default )
- **Signature**: `function ef_responsive_text_pair( string $key, string $label, string $desktop_default = '' ): array`
- **File**: `includes/responsive.php:134`
- **Behavior**: `[prop, control]` for a Responsive_Text input.

#### ef_responsive_boolean_pair( $key, $label )
- **Signature**: `function ef_responsive_boolean_pair( string $key, string $label ): array`
- **File**: `includes/responsive.php:160`
- **Behavior**: `[prop, control]` for a Responsive_Switch.

#### ef_responsive_flatten( $settings, $key )
- **Signature**: `function ef_responsive_flatten( array $settings, string $key ): array`
- **File**: `includes/responsive.php:257`
- **Behavior**: Flatten a string-typed responsive envelope at render. Returns `{desktop, tablet, mobile}` with each cell guaranteed string.
- **Use at render time** to read a responsive value into a render-ready triple.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_responsive_default_envelope( $desktop_value )` | `responsive.php:36` | String-typed envelope shortcut |
| `ef_responsive_flatten_typed( $value, $atom_type, $empty, $read )` | `responsive.php:196` | Generic typed flatten |
| `ef_responsive_flatten_boolean( $settings, $key )` | `responsive.php:220` | Boolean-typed flatten |

---
