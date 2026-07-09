# EF helpers reference (`ef_*` free functions)

Plugin: `plugins/custom/elementor-framework/`. Helpers load via `includes/bootstrap.php` → per-file `require_once` chain. **~330 free `ef_*` functions** across `includes/*.php` + nested subfolders (run the re-grep at the bottom of this file for the live count — moving target).

This file is the **build/audit-agent surface** for those helpers. The top ~80 (everything an EF build or audit agent ever reaches for) are documented in full; the remaining ~180 (operator surfaces — SMTP admin, internal registry plumbing, low-level CSS bundling, etc.) are indexed by name + file + 1-line purpose. Total coverage: **100% name-findable**, ≥80% effective coverage for build/audit work.

**File-path drift warning.** EF refactors split + rename `includes/` source files routinely. If a `File: includes/<foo>.php:<line>` reference here doesn't match the live tree, the helper has either moved (re-grep `^function ef_<name>` across `includes/`) or been retired (no replacement). Treat line numbers as hints, not absolutes.

## When to use this reference vs. live grep

Use **this file** when:
- You need to know which helper builds a responsive pair, action prop schema, loop transform default, etc.
- You're authoring a new EF widget and need the canonical envelope/prop/control builders.
- You're auditing a widget and need to confirm which helper resolves a loop / visibility / transform.

Use **live grep** (`grep -rn "^function ef_<name>" plugins/custom/elementor-framework/includes/`) when:
- A helper name is in the index but you need the body (e.g., to understand a defaulting rule).
- You suspect this file is stale — re-grep `^function ef_` across `includes/` and reconcile.
- You're chasing a non-`ef_*` symbol (class method, constant, hook callback).

## Category index

| # | Category | Anchor | Helpers covered | Full / Index |
|---|---|---|---|---|
| 1 | Atomic V4 (envelope + prop builders) | [#atomic-v4](#atomic-v4) | 14 |
| 2 | Pairs (responsive scalar+control bundles) | [#pairs](#pairs) | 8 |
| 3 | Settings sections | [#settings-sections](#settings-sections) | 3 |
| 4 | Select options | [#select-options](#select-options) | 6 |
| 5 | Voxel + dynamic-data | [#voxel--dynamic-data](#voxel--dynamic-data) | 17 |
| 6 | Loop | [#loop](#loop) | 8 |
| 7 | Voxel sub-resolvers | [#voxel-sub-resolvers](#voxel-sub-resolvers) | 2 |
| 8 | Action types & controls | [#action-types--controls](#action-types--controls) | 13 |
| 9 | Icon helpers | [#icon-helpers](#icon-helpers) | 6 |
| 10 | Links | [#links](#links) | 4 |
| 11 | Responsive primitives | [#responsive-primitives](#responsive-primitives) | 8 |
| 12 | Grid | [#grid](#grid) | 7 |
| 13 | Map | [#map](#map) | 4 |
| 14 | CSS / fonts / assets | [#css--fonts--assets](#css--fonts--assets) | 12 |
| 15 | Frontend / editor (gating) | [#frontend--editor-gating](#frontend--editor-gating) | 22 |
| 16 | Editor preview post context | [#editor-preview-post-context](#editor-preview-post-context) | 3 |
| 17 | Dynamic tags | [#dynamic-tags](#dynamic-tags) | 9 |
| 18 | Elementor data | [#elementor-data](#elementor-data) | 5 |
| 19 | Forms | [#forms](#forms) | 13 |
| 20 | SMTP (operator surface) | [#smtp-index-only](#smtp-index-only) | 26 |
| 21 | Admin (operator surface) | [#admin-index-only](#admin-index-only) | 14 |
| 22 | Migrator | [#migrator](#migrator) | 2 |
| 23 | Registry & autodiscovery | [#registry--autodiscovery](#registry--autodiscovery) | 8 |
| 24 | Misc small modules | [#misc-small-modules](#misc-small-modules) | 12 |

Documented surface ≈220 helpers (~80% effective coverage). Remaining ~110 are intra-category internals (e.g., private `_ef_*` helpers, repeated unnamed editor-preview render helpers, spam screening, IP CIDR matchers) — re-grep `^function ef_` across `includes/` when you need the full live list.

---

## Atomic V4

V4 atomic prop + envelope builders. Every EF widget builds its `define_props_schema()` and any free-form atomic value (e.g., default for a settings section) by composing these. Build agents reach here first when scaffolding a new prop; audit agents grep here to confirm a widget is using the canonical builder rather than reimplementing the envelope.

### Full-doc helpers

#### ef_atomic_base_props()
- **Signature**: `function ef_atomic_base_props(): array`
- **File**: `includes/atomic.php:33`
- **Behavior**: Returns the universal prop set merged into every EF widget.
- **Returns**: `array{classes: Classes_Prop_Type, attributes: Key_Value_Array_Prop_Type, col_span: Responsive_String, sticky: Responsive_Boolean, …}` — read the body for the current key set; Voxel/EF runtime cells are merged in by `define_props_schema()` when `$include_voxel_runtime_keys` / `$include_loop_runtime_keys` are true.
- **Example**:
```php
$schema = array_merge(
    ef_atomic_base_props(),
    [ 'tag' => ef_atomic_enum_string([...], 'div'), /* widget-specific props */ ]
);
```

#### ef_atomic_enum_string( $values, $default )
- **Signature**: `function ef_atomic_enum_string( array $values, $default = '' ): \EF\Props\Enum_String`
- **File**: `includes/atomic.php:143`
- **Behavior**: Lenient `Enum_String` factory. Out-of-enum sanitizes to `$default` (unless value is a Voxel dtag template, in which case it round-trips).
- **Returns**: `EF\Props\Enum_String`
- **Example**:
```php
'variant' => ef_atomic_enum_string( EF_Tokens::SURFACE_VARIANTS, 'white' )
```

#### ef_atomic_boolean( $default )
- **Signature**: `function ef_atomic_boolean( bool $default = false )`
- **File**: `includes/atomic.php:165`
- **Behavior**: Stock `Boolean_Prop_Type` wrapper, seeded with `default()`+`initial_value()`.
- **Example**: `'sticky' => ef_atomic_boolean( false )`

#### ef_atomic_image( $default_size )
- **Signature**: `function ef_atomic_image( string $default_size = 'large' ): \EF\Props\Lenient_Image`
- **File**: `includes/atomic.php:201`
- **Behavior**: `Lenient_Image` factory with size seeded.
- **Example**: `'media_image' => ef_atomic_image( 'medium_large' )`

#### ef_envelope_string( $value )
- **Signature**: `function ef_envelope_string( string $value = '' ): object`
- **File**: `includes/atomic-envelopes.php:61`
- **Behavior**: Build a `{$$type:'string', value:…}` envelope at rest.
- **Example**: `ef_envelope_string( 'Hello' )` → `{"$$type":"string","value":"Hello"}`

#### ef_envelope_boolean( $value )
- **Signature**: `function ef_envelope_boolean( bool $value = false ): object`
- **File**: `includes/atomic-envelopes.php:91`
- **Behavior**: Build a `{$$type:'boolean', value:…}` envelope at rest.

#### ef_envelope_responsive_string( $desktop, $tablet, $mobile )
- **Signature**: `function ef_envelope_responsive_string( string $desktop = '', string $tablet = '', string $mobile = '' ): object`
- **File**: `includes/atomic-envelopes.php:47` (note: file ordering shifted — `responsive_string` declared BEFORE the scalar `string` envelope)
- **Behavior**: Build `{$$type:'ef-responsive-string', value:{desktop, tablet, mobile}}` envelope. Each cell is a String envelope.
- **Example**:
```php
ef_envelope_responsive_string( 'horizontal', 'vertical', 'vertical' )
```

#### ef_envelope_responsive_boolean( $desktop, $tablet, $mobile )
- **Signature**: `function ef_envelope_responsive_boolean( bool $desktop = false, bool $tablet = false, bool $mobile = false ): object`
- **File**: `includes/atomic-envelopes.php:77`
- **Behavior**: Build `{$$type:'ef-responsive-boolean', value:{desktop, tablet, mobile}}` envelope. Drives `sticky`.

#### ef_envelope_classes()
- **Signature**: `function ef_envelope_classes(): object`
- **File**: `includes/atomic-envelopes.php:105`
- **Behavior**: Empty `{$$type:'classes', value:[]}` envelope. EF widgets reserve slot 0 for the local-style id on card/wrapper.

#### ef_envelope_attributes()
- **Signature**: `function ef_envelope_attributes(): object`
- **File**: `includes/atomic-envelopes.php:115`
- **Behavior**: Empty `{$$type:'attributes', value:[]}` envelope. Marked `Overridable::ignore`.

#### ef_atomic_base_prop_defaults()
- **Signature**: `function ef_atomic_base_prop_defaults(): array`
- **File**: `includes/atomic-envelopes.php:150`
- **Behavior**: Default values map for `ef_atomic_base_props()` keys — used to fill missing cells on legacy widget instances at load time.

#### ef_atomic_apply_base_prop_defaults( $settings )
- **Signature**: `function ef_atomic_apply_base_prop_defaults( object $settings ): bool`
- **File**: `includes/atomic-envelopes.php:169`
- **Behavior**: Mutate `$settings` to fill any missing base-prop cells with defaults. Returns `true` if any cell was added.
- **Used by**: `ef_normalize_atomic_*` tree walkers.

#### ef_base_style_display( $display, $key )
- **Signature**: `function ef_base_style_display( string $display, string $key = 'base' ): array`
- **File**: `includes/atomic.php:103`
- **Behavior**: Build `['base' => Style_Definition]` for display-only base styles. Lets an element override its CSS `display` (e.g., navbar sets `'block'`) without authoring a full Style_Variant.
- **Example**:
```php
public static function define_base_styles(): array {
    return ef_base_style_display( 'block' );
}
```

#### ef_atomic_action_props( $prefix )
- **Signature**: `function ef_atomic_action_props( string $prefix = '' ): array`
- **File**: `includes/action-controls.php:150`
- **Behavior**: Scalar action suite prop schema for one slot. Spreads `{prefix_}action_type` plus every per-type field via `ef_action_field_specs()`.
- **Returns**: `array` keyed by `<prefix>_<spec_key>`.
- **Example**:
```php
$schema = array_merge( $schema, ef_atomic_action_props( 'banner' ) );
// adds banner_action_type, banner_action_link, banner_action_phone, …
// (live prefix: the ef-navbar banner CTA, composed via Action_Slot)
```
> The retired card byline no longer carries its own scalar `byline_action_*` slot — the byline now lives as a `content_blocks` row and consumes the content-block row's action cells (the shared `loop+actions` envelope), not a flat `ef_atomic_action_props()` spread.

---

## Pairs

A "pair" is a `[prop, control]` tuple — the prop goes into `define_props_schema()`, the control goes into `define_atomic_controls()`. Pairs exist because EF's responsive controls (Responsive_Select, Responsive_Text, Responsive_Switch) need matched prop schemas with the right enum/atom-type cells. Build agents must use pairs verbatim; reinventing them drifts the editor's read/write target per breakpoint.

### Full-doc helpers

#### ef_composite_control( $key, $label, $row_label, $row_definition )
- **Signature**: `function ef_composite_control( string $key, string $label, string $row_label, $row_definition ): \EF\Controls\Composite_Repeatable`
- **File**: `includes/pairs.php:42`
- **Behavior**: Build a `Composite_Repeatable` control bound to a row definition. Chains `bind_to()->set_label()->set_row_label()->set_rows()`. The earlier `$array_class` + `$row_class` positional params were folded into the row-definition object (auto-resolved via `Composite_Repeatable::set_rows()`).
- **Returns**: configured `EF\Controls\Composite_Repeatable`
- **Used by**: every composite repeater control surface (headings, tags, actions, fields, mega).

#### ef_general_section( $element )
- **Signature**: `function ef_general_section( $element )`
- **File**: `includes/pairs.php:84`
- **Behavior**: Auto-injected General section (Dynamic triggers + col_span + sticky + _cssid). Called from `define_atomic_controls()` to surface the General section the editor expects.
- **Returns**: V4 section descriptor object.

#### ef_sticky_pair()
- **Signature**: `function ef_sticky_pair(): array`
- **File**: `includes/pairs.php:126`
- **Behavior**: `[prop, control]` for sticky (responsive boolean). Use when injecting sticky behavior into a custom element.
- **Returns**: `['prop' => Responsive_Boolean, 'control' => Responsive_Switch]`

#### ef_cols_pair()
- **Signature**: `function ef_cols_pair(): array`
- **File**: `includes/pairs.php:135`
- **Behavior**: `[prop, control]` for wrapper `grid-template-columns` track lists. Responsive text control (free-form `1fr 1fr` etc.).
- **Used by**: `ef-wrapper`'s `cols` prop.

#### ef_tag_pair( $allowed, $default )
- **Signature**: `function ef_tag_pair( array $allowed, string $default = 'div' ): array`
- **File**: `includes/pairs.php:147`
- **Behavior**: `[prop, control]` for HTML tag enum. Wraps `ef_atomic_enum_string` + a Vx_Select with `ef_html_tag_options()`.

#### ef_variant_pair( $values_map, $default, $key, $label )
- **Signature**: `function ef_variant_pair( array $values_map, string $default = '', string $key = 'variant', ?string $label = null ): array`
- **File**: `includes/pairs.php:171`
- **Behavior**: Generic variant select pair — used by every element with a variant (card, wrapper, navbar, button, etc.).
- **Returns**: `['prop' => Enum_String, 'control' => Vx_Select]`

#### ef_variant_prop( $key, $default, $allowed, $label )
- **Signature**: `function ef_variant_prop( string $key = 'variant', string $default = 'white', ?array $allowed = null, ?string $label = null ): array`
- **File**: `includes/pairs.php:196`
- **Behavior**: Canonical single-prop variant. Uses `EF_Tokens::variant_labels()` for label resolution; pass `$allowed=null` to use all tokens, or restrict.

**Retired**: `ef_content_section` (use `ef_section( 'content', __( 'Content', 'ef' ), $items )`); `ef_layout_pair` (build the responsive-select pair directly via `ef_responsive_select_pair` with caller-supplied options + `ef_with_inherit` for non-desktop cells).

---

## Settings sections

EF widgets use a small set of canonical section shells so the panel layout stays SSOT. **Do not hand-roll** `Section_Layout::make(...)` — go through these.

### Full-doc helpers

#### ef_settings_section( $items )
- **Signature**: `function ef_settings_section( array $items = [] )`
- **File**: `includes/atomic.php:66`
- **Behavior**: Canonical Settings section shell. Use for variant + tag + layout + sticky controls.
- **Returns**: V4 section descriptor object.
- **Example**:
```php
public static function define_atomic_controls(): array {
    return [
        ef_general_section( static::class ),
        ef_settings_section([ $variant_control, $tag_control, $layout_control ]),
        ef_section( 'content', __( 'Content', 'ef' ), [ $headings_control, $tags_control ] ),
    ];
}
```

#### ef_section( $id, $label, $items )
- **Signature**: `function ef_section( string $id, string $label, array $items )`
- **File**: `includes/atomic.php:85`
- **Behavior**: Generic V4 section shell. Use for one-off sections (Card Media, Banner, etc.) and as the replacement for the retired `ef_content_section`.
- **Example**: `ef_section( 'media', __( 'Media', 'ef' ), [ $media_type_control, $media_image_control ] )`

#### ef_general_section( $element )
See full doc above under [Pairs](#pairs).

**Retired**: `ef_content_section( array $items )` — fold into `ef_section( 'content', __( 'Content', 'ef' ), $items )`.

---

## Select options

Helpers that materialize select options as `[{value, label}]` lists with consistent sort + translation.

### Full-doc helpers

#### ef_select_options( $map )
- **Signature**: `function ef_select_options( array $map ): array`
- **File**: `includes/select-options.php:74`
- **Behavior**: `[value=>label] → [{value,label}]`. Labels are translated; result is sorted alpha with empty pinned at top.
- **Example**:
```php
ef_select_options( [ '' => 'None', 'a' => 'Alpha', 'b' => 'Beta' ] )
// [{value:'', label:'None'}, {value:'a', label:'Alpha'}, {value:'b', label:'Beta'}]
```

#### ef_enum_values( $map )
- **Signature**: `function ef_enum_values( array $map ): array`
- **File**: `includes/select-options.php:100`
- **Behavior**: `array_map('strval', array_keys($map))` — the enum constraint for `Enum_String::with_enum()`.

#### ef_with_inherit( $enum )
- **Signature**: `function ef_with_inherit( array $enum ): array`
- **File**: `includes/select-options.php:114`
- **Behavior**: Prepend `'' => 'Inherit'` to a select-option list (used on tablet/mobile cells of responsive selects).

#### ef_with_default_label( $enum, $label )
- **Signature**: `function ef_with_default_label( array $enum, string $label = 'Default' ): array`
- **File**: `includes/select-options.php:129`
- **Behavior**: Prepend `'' => $label` to a select-option list.

#### ef_html_tag_options( $tags, $default_tag )
- **Signature**: `function ef_html_tag_options( array $tags, string $default_tag = '' ): array`
- **File**: `includes/select-options.php:145`
- **Behavior**: HTML tag select options with default-tag pinned to the top of the list.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_sort_select_options( $options )` | `select-options.php:26` | Alpha sort with empty pinned |

---

## Voxel + dynamic-data

The Voxel integration surface. Predicates (`ef_has_voxel_*`), the `@tag()` resolver (`ef_render`), post-context capture/restore (for loop iteration), and the looper safety primitives. Build agents need `ef_render` + `ef_has_dtag` constantly; audit agents need the predicates to gate Voxel-only feature detection.

### Full-doc helpers

#### ef_voxel_runtime_keys()
- **Signature**: `function ef_voxel_runtime_keys(): array`
- **File**: `includes/voxel.php:32`
- **Behavior**: List of Voxel-owned runtime keys — currently `_voxel_loop`, `_voxel_loop_limit`, `_voxel_loop_offset`, `_voxel_visibility_rules`, `_voxel_visibility_behavior` (V3-flat) plus `_vx_loop`, `_vx_visibility` (V4 envelope). Used by `define_props_schema()` to merge in Voxel runtime cells when `$include_voxel_runtime_keys=true`.

#### ef_loop_runtime_keys()
- **Signature**: `function ef_loop_runtime_keys(): array`
- **File**: `includes/voxel.php:55`
- **Behavior**: List of EF-owned loop-runtime keys — currently `_ef_loop_initial`, `_ef_loop_more_label`, `_ef_loop_less_label` (load-more / paged-show controls; the prior `_ef_loop_transform` cell was retired with the transform layer). Used when `$include_loop_runtime_keys=true`.

#### ef_has_voxel_theme()
- **Signature**: `function ef_has_voxel_theme(): bool`
- **File**: `includes/voxel.php:73`
- **Behavior**: True if Voxel theme is active. Gate every Voxel-only code path.

#### ef_has_dtag( $value )
- **Signature**: `function ef_has_dtag( string $value ): bool`
- **File**: `includes/voxel.php:120`
- **Behavior**: True if string contains `@tags(` / `@post(` / `@site(` / `@profile(`.
- **Example**:
```php
if ( ef_has_dtag( $url ) ) {
    $url = ef_render( $url ); // resolve at render time
}
```

#### ef_render( $value )
- **Signature**: `function ef_render( string $value ): string`
- **File**: `includes/voxel.php:135`
- **Behavior**: Resolve Voxel dynamic tags in a string. **Does NOT** `wp_kses` or `esc_*` the output — caller is responsible for escaping.
- **Returns**: Resolved string (or original if no dtags or Voxel render unavailable).

#### ef_render_kses( $raw, $shortcode )
- **Signature**: `function ef_render_kses( string $raw, bool $shortcode = false ): string`
- **File**: `includes/voxel.php:167`
- **Behavior**: `ef_render` + `wp_kses_post` (+ optional `do_shortcode`). Use for any HTML-bearing field (heading body, banner message).

#### ef_canonicalize_loop_key( $raw )
- **Signature**: `function ef_canonicalize_loop_key( string $raw ): string`
- **File**: `includes/voxel.php:192`
- **Behavior**: Normalize a loop-tag key form (strip `loop:` prefix, trim, etc.). Use before passing keys into looper APIs.

#### ef_capture_output( $fn )
- **Signature**: `function ef_capture_output( callable $fn ): string`
- **File**: `includes/voxel.php:220`
- **Behavior**: `ob_start/get_clean` around a callable. Used for capturing Voxel looper output into a string buffer for template injection.
- **Example**:
```php
$html = ef_capture_output( function () use ( $items ) {
    foreach ( $items as $item ) { /* echo per-item markup */ }
} );
```

#### ef_voxel_current_post()
- **Signature**: `function ef_voxel_current_post(): ?object`
- **File**: `includes/voxel.php:246`
- **Behavior**: Get the current Voxel post context (Voxel post object — NOT WP_Post). Use for resolving `@post(...)` tags.

#### ef_voxel_current_post_id()
- **Signature**: `function ef_voxel_current_post_id(): int`
- **File**: `includes/voxel.php:253`
- **Behavior**: Current Voxel post id, or 0 if no context.

#### ef_voxel_apply_post_context( $item )
- **Signature**: `function ef_voxel_apply_post_context( $item ): void`
- **File**: `includes/voxel.php:307`
- **Behavior**: Push a Voxel post into the global render context so subsequent `@post()` calls resolve against it. Pair with `ef_voxel_restore_post()`.
- **Used by**: loop iterators.

#### ef_voxel_capture_post_context()
- **Signature**: `function ef_voxel_capture_post_context(): callable`
- **File**: `includes/voxel.php:292`
- **Behavior**: Snapshot the current post context. Returns a restorer callable — invoke it to roll back.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_has_voxel_looper()` | `voxel.php:83` | Predicate: looper available |
| `ef_has_voxel_render()` | `voxel.php:92` | Predicate: render service available |
| `ef_has_voxel_post_type()` | `voxel.php:100` | Predicate: `Voxel\Post_Type` class loaded |
| `ef_has_voxel_visibility()` | `voxel.php:108` | Predicate: visibility resolver available |
| `ef_voxel_restore_post( $original )` | `voxel.php:273` | Restore captured post context |
| `ef_looper_mark_running( $loop_key )` | `voxel.php:351` | Mark a looper as running (deadlock guard) |
| `ef_looper_force_release( $loop_key )` | `voxel.php:385` | Force-release a stuck looper |

---

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
See full doc above under [Atomic V4](#atomic-v4).

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

## Grid

Col-span + grid-column conversions.

### Full-doc helpers

#### ef_col_span_pair()
- **Signature**: `function ef_col_span_pair(): array`
- **File**: `includes/grid.php:137`
- **Behavior**: `[prop, control]` for responsive col_span. Use only when injecting col_span into a custom element — every standard EF widget gets this via `ef_atomic_base_props()`.

#### ef_col_span_options( $with_auto )
- **Signature**: `function ef_col_span_options( bool $with_auto ): array`
- **File**: `includes/grid.php:73`
- **Behavior**: Col_span select options (1..12, optional `'auto'`).

#### ef_col_span_to_grid_column( $col_span )
- **Signature**: `function ef_col_span_to_grid_column( string $col_span ): ?string`
- **File**: `includes/grid.php:107`
- **Behavior**: Map a `col_span` value (e.g., `'6'`) to the CSS `grid-column` value (e.g., `'span 6'`). Returns `null` if unmappable.

#### ef_modifier_classes( $settings, $map )
- **Signature**: `function ef_modifier_classes( array $settings, array $map ): array`
- **File**: `includes/grid.php:40`
- **Behavior**: Build a flat list of modifier classes from settings by walking a `key => 'pattern-{}'` map. The `{}` placeholder is replaced with the settings value.
- **Example**:
```php
ef_modifier_classes( $s, [ 'layout' => 'ef-card--layout-{}', 'variant' => 'ef-card--{}' ] )
// returns ['ef-card--layout-horizontal', 'ef-card--white']
```

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_col_span_grid_column_map()` | `grid.php:94` | Static col_span → grid-column map |
| `ef_grid_column_to_col_span( $grid_column )` | `grid.php:121` | Inverse of `ef_col_span_to_grid_column` |
| `ef_global_modifier_class_map()` | `grid.php:164` | Universal modifier map (sticky, etc.) |

---

## Map

Map (Leaflet / Google) provider registry + config. Used by `EF\Parts\Media\Map` handler and the `map_pin` row type.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_map_providers()` | `map.php:17` | Leaflet/Google provider registry |
| `ef_voxel_map_defaults()` | `map.php:29` | Defaults from Voxel theme map settings |
| `ef_map_config()` | `map.php:60` | Full map config for current request |
| `ef_register_map_assets()` | `map.php:93` | Register leaflet + ef-google-maps scripts/styles |

---

## CSS / fonts / assets

Operator-tier surface for asset registration + CSS bundle building. Build/audit agents rarely call these directly — they're invoked by EF's bootstrap and enqueue lifecycle.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_build_core_css()` | `css.php:17` | Concatenate ef-core CSS bundle |
| `ef_critical_css_handles()` | `css.php:43` | List of critical-CSS handles |
| `ef_build_critical_css()` | `css.php:56` | Concatenate ef-critical bundle |
| `ef_resolve_breakpoints( $css )` | `css.php:81` | Replace breakpoint vars in CSS |
| `ef_minify_css( $css )` | `css.php:105` | Minify with comment/whitespace strip |
| `ef_bundle_css( $output, $sources )` | `css.php:148` | Bundle multiple CSS files |
| `ef_css_version( $file )` | `css.php:271` | Stable cache-busting version |
| `ef_compile_css( $relative_path )` | `css.php:289` | Compile CSS file (resolve + minify) |
| `ef_register_script( $handle, $path, $deps, $defer, $footer )` | `css.php:333` | Register frontend script |
| `ef_register_css( $handle, $path, $deps )` | `css.php:376` | Register frontend stylesheet |
| `ef_init_fonts()` | `fonts.php:20` | Voxel kit font enqueue adapter |
| `ef_enqueue_icon_font( $library )` | `elementor-adapter.php:45` | Enqueue an icon-library stylesheet |

---

## Frontend / editor (gating)

Frontend + editor + Elementor-adapter helpers. Build/audit agents need the **gating predicates** (`ef_is_edit_mode`, `ef_in_editor_preview`, `ef_is_experiment_active`) to write branching render code. The rest is operator surface.

### Full-doc helpers

#### ef_in_editor_preview()
- **Signature**: `function ef_in_editor_preview(): bool`
- **File**: `includes/elementor-adapter.php:132`
- **Behavior**: SSOT for "am I in the editor's preview iframe right now?". Use to gate editor-only branches (placeholder labels, force-render fallbacks, dtag scaffolding).
- **Example**:
```php
if ( ef_in_editor_preview() ) {
    $title = $title ?: __( 'TOC placeholder', 'ef' );
}
```

#### ef_is_edit_mode()
- **Signature**: `function ef_is_edit_mode(): bool`
- **File**: `includes/elementor-adapter.php:114`
- **Behavior**: True if Elementor's edit mode is active (any edit surface — preview iframe OR panel rendering).

#### ef_is_experiment_active( $name )
- **Signature**: `function ef_is_experiment_active( string $name ): bool`
- **File**: `includes/elementor-adapter.php:93`
- **Behavior**: Check if an Elementor experiment is on. Use for V4-gating (`ef_is_experiment_active( 'e_atomic_elements' )`).

#### ef_render_template( $template_id )
- **Signature**: `function ef_render_template( int $template_id ): string`
- **File**: `includes/elementor-adapter.php:26`
- **Behavior**: Render a saved Elementor library template by id. Use for `ef-wrapper` mode=template.
- **Returns**: HTML string.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_collect_preload_template_ids()` | `frontend.php:25` | Discover templates to preload |
| `ef_invalidate_preload_cache()` | `frontend.php:90` | Clear preload cache |
| `ef_enqueue_voxel_template_css( $id )` | `frontend.php:110` | Enqueue per-template CSS |
| `ef_enqueue_frontend_styles()` | `frontend.php:122` | Frontend style coordinator |
| `ef_iter_atomic_element_types()` | `frontend.php:170` | Iterate registered EF widget types |
| `ef_force_enqueue_editor_iframe_assets()` | `frontend.php:186` | Pre-enqueue every EF widget JS/CSS for editor canvas |
| `ef_strip_empty_data_settings()` | `frontend.php:209` | Remove empty settings on save |
| `ef_optimize_style_tags( $tag, $handle )` | `frontend.php:232` | Style-tag optimization (preload, etc.) |
| `ef_get_active_kit()` | `elementor-adapter.php:63` | Active Elementor Kit instance |
| `ef_clear_files_cache()` | `elementor-adapter.php:78` | Clear Elementor file cache |
| `ef_enqueue_editor_preview_styles()` | `editor.php:13` | Editor preview CSS |
| `ef_fix_elementor_v4_env_ordering()` | `editor.php:28` | V4 env ordering hack |
| `ef_fix_elementor_v4_env_defaults( $env )` | `editor.php:62` | V4 env defaults patch |
| `ef_editor_preview_always_render_types()` | `editor.php:81` | Widgets that always server-render in editor |
| `ef_localize_voxel_feed_editor()` | `editor.php:95` | Editor JS localization for feed |
| `ef_localize_voxel_tag_strings()` | `editor.php:121` | Editor JS localization for dtag strings |
| `ef_enqueue_editor_scripts()` | `editor.php:150` | Editor JS coordinator |
| `ef_enqueue_editor_panel_styles()` | `editor.php:256` | Editor panel CSS |
| `ef_init_editor()` | `editor.php:276` | Editor init entry |
| `ef_rest_render_buffered( $route_id, $cb )` | `editor-preview-api.php:46` | Buffered REST output capture |
| `ef_register_editor_preview_routes()` | `editor-preview-api.php:68` | Register `/ef/v1/render-widget` + `/ef/v1/render-wrapper-shell` |
| `ef_rest_render_widget( $request )` | `editor-preview-api.php:170` | REST handler for leaf widgets |
| `ef_rest_render_wrapper_shell( $request )` | `editor-preview-api.php:104` | REST handler for wrapper shell |
| `ef_editor_preview_render_element_html( $element_data )` | `editor-preview-api.php` | Unified render — any EF element via `print_element()` (leaf or wrapper, loop fan-out + visibility + template framing) |
| `ef_editor_preview_render_item( $item )` | `editor-preview-api.php` | SSOT render item: leaf→html, plain wrapper→shell, looped/template wrapper→html |
| `ef_resolve_widget_class( $widget_type )` | `editor-preview-api.php` | widget_type → PHP class |

---

## Editor preview post context

Tiny but load-bearing: these three helpers let an editor preview render a widget against the right Voxel post (the template's preview-post setting) without polluting the global post context.

### Full-doc helpers

#### ef_get_voxel_native_preview_post( $template_id )
- **Signature**: `function ef_get_voxel_native_preview_post( int $template_id ): ?object`
- **File**: `includes/editor-preview-post-context.php:28`
- **Behavior**: Get the Voxel preview post for a template (from Voxel's `_voxel_template_preview_post` postmeta).
- **Returns**: Voxel post object, or `null` if none configured.

#### ef_prime_preview_post_context( $preview_post )
- **Signature**: `function ef_prime_preview_post_context( $preview_post ): bool`
- **File**: `includes/editor-preview-post-context.php:51`
- **Behavior**: Prime the global post for `@post()` resolution. Returns `true` if context was primed (so caller knows to restore it).

#### ef_with_preview_post_context( $template_id, $callback )
- **Signature**: `function ef_with_preview_post_context( ?int $template_id, callable $callback )`
- **File**: `includes/editor-preview-post-context.php:85`
- **Behavior**: Callback wrapper. Resolves preview post → primes context → runs callback → restores context. Use this rather than calling prime+restore by hand.

---

## Dynamic tags

Dynamic-tag schema extension + scoping. The "scope" helpers gate whether a prop renders its tag bolt (icon button) in the editor — used by `ef_collapse_vx_sections` to swap Voxel's panel sections for EF's General-section triggers.

### Full-doc helpers

#### ef_init_dynamic_tags()
- **Signature**: `function ef_init_dynamic_tags(): void`
- **File**: `includes/dynamic-tags/panel-controls.php:25`
- **Behavior**: Wire dynamic-tag scoping into Elementor's lifecycle (filters + actions). Called from `ef_bootstrap()`.

#### ef_collapse_vx_sections( $controls, $element )
- **Signature**: `function ef_collapse_vx_sections( array $controls, $element ): array`
- **File**: `includes/dynamic-tags/panel-controls.php:64`
- **Behavior**: Strip Voxel's VX panel sections (filter priority 110, replaces Voxel's filter at 100). EF widgets surface VX cells through the General-section `Triggers` control instead.

#### ef_dynamic_tags_in_scope()
- **Signature**: `function ef_dynamic_tags_in_scope(): bool`
- **File**: `includes/dynamic-tags/scope.php:88`
- **Behavior**: True if we're inside an EF widget control resolution. Use to gate dtag-aware prop type wrapping.

#### ef_tag_prop_type_dynamic( $prop_type )
- **Signature**: `function ef_tag_prop_type_dynamic( Prop_Type $prop_type ): void`
- **File**: `includes/dynamic-tags/scope.php:120`
- **Behavior**: Mark a prop type as dtag-aware (Voxel theme adds an icon button to its control in the editor).

#### ef_extend_custom_dynamic( $schema )
- **Signature**: `function ef_extend_custom_dynamic( array $schema ): array`
- **File**: `includes/dynamic-tags/mapping.php:98`
- **Behavior**: Extend the dtag schema with EF custom envelopes (responsive string, action rows, etc.). Voxel's filter callback uses this to know which EF envelopes can carry a dtag.

#### ef_tag_schema_dynamic( $schema )
- **Signature**: `function ef_tag_schema_dynamic( array $schema ): array`
- **File**: `includes/dynamic-tags/mapping.php:191`
- **Behavior**: Mark schema fields as Voxel-taggable (recursive walk; flags string/url/image-src cells).

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_dynamic_tags_scope( $delta )` | `dynamic-tags/scope.php:73` | Scope counter (get/adjust) |
| `ef_dynamic_tags_scope_push()` | `dynamic-tags/scope.php:80` | Scope counter (push) |
| `ef_dynamic_tags_scope_pop()` | `dynamic-tags/scope.php:84` | Scope counter (pop) |
| `ef_dynamic_taggable_classes()` | `dynamic-tags/scope.php:98` | List of classes that get the Voxel-tag bolt |
| `ef_seed_required_defaults( $prop_type )` | `dynamic-tags/defaults.php:44` | Seed required defaults on a prop type |
| `ef_walk_prop_type( $prop_type )` | `dynamic-tags/mapping.php:116` | Recursive walk of a prop type's schema |

---

## Elementor data

Read/write helpers for the `_elementor_data` post meta. Use these instead of `get_post_meta(... 'elementor_data', true)` — they handle the double-escape edge cases and the `_has_ef_widgets` marker sync.

### Full-doc helpers

#### ef_decode_elementor_data( $post_id )
- **Signature**: `function ef_decode_elementor_data( int $post_id ): ?array`
- **File**: `includes/elementor-data.php:33`
- **Behavior**: Read + decode `_elementor_data` meta. Handles `wp_unslash` and the double-encoded-JSON fallback.
- **Returns**: Decoded tree (array of root elements), or `null` if no data or unrecoverable corruption.

#### ef_write_elementor_data( $meta_id, $data, $post_id )
- **Signature**: `function ef_write_elementor_data( int $meta_id, array $data, int $post_id = 0 ): bool`
- **File**: `includes/elementor-data.php:60`
- **Behavior**: Write encoded data to the meta row. Uses `JSON_UNESCAPED_UNICODE` (workspace convention — see CLAUDE.md "Encoding"). Updates the `_has_ef_widgets` marker via `ef_sync_widget_marker()` automatically.
- **Returns**: `true` on success.

#### ef_post_id_for_meta_id( $meta_id )
- **Signature**: `function ef_post_id_for_meta_id( int $meta_id ): int`
- **File**: `includes/elementor-data.php:123`
- **Behavior**: Look up `post_id` for a `_elementor_data` meta row. Used when only the meta_id is available (e.g., from `update_postmeta` hook).

#### ef_payload_contains_ef_widget( $data )
- **Signature**: `function ef_payload_contains_ef_widget( array $data ): bool`
- **File**: `includes/elementor-data.php:212`
- **Behavior**: Recursive scan of an `_elementor_data` tree for any EF widget. Depth-bounded internally.

#### ef_sync_widget_marker( $post_id, $data )
- **Signature**: `function ef_sync_widget_marker( int $post_id, ?array $data = null ): void`
- **File**: `includes/elementor-data.php:241`
- **Behavior**: Set `_has_ef_widgets` postmeta marker based on whether the tree contains an EF widget. If `$data` is `null`, reads + decodes from the meta row.

---

## Forms

`ef-form` widget machinery — config loading, submission handling, V4 → V3 row hydration, rate limiting, IP detection, honeypot.

### Full-doc helpers

#### ef_form_messages()
- **Signature**: `function ef_form_messages(): array`
- **File**: `includes/forms/config.php:25`
- **Behavior**: Message bag (camelCase keys) for form UI strings. Used by `ef-form` JS localization.

#### ef_form_defaults()
- **Signature**: `function ef_form_defaults(): array`
- **File**: `includes/forms/config.php:56`
- **Behavior**: Default form field values (button_text, success_message, etc.).

#### ef_get_form_config( $post_id, $widget_id )
- **Signature**: `function ef_get_form_config( int $post_id, string $widget_id ): ?array`
- **File**: `includes/forms/field-validator.php:19`
- **Behavior**: Load a form's config from a post by widget_id. Walks `_elementor_data` tree via `ef_find_widget()`, hydrates V4 → V3 row shape via `ef_hydrate_v4_fields()`.
- **Returns**: `{button_text, success_message, fields:[…flat V3 row shape]}` or `null` if widget not found.

#### ef_hydrate_v4_fields( $rows )
- **Signature**: `function ef_hydrate_v4_fields( array $rows ): array`
- **File**: `includes/forms/field-validator.php:73`
- **Behavior**: Convert V4 envelope rows to V3-flat 7-key row shape (`{type, name, field_id, label, placeholder, required, options, accept}`).

#### ef_find_widget( $elements, $widget_id, $expected_widget_type )
- **Signature**: `function ef_find_widget( array $elements, string $widget_id, ?string $expected_widget_type = null )`
- **File**: `includes/forms/field-validator.php:98`
- **Behavior**: Walk an `_elementor_data` tree to find a widget by id. Optionally enforce widget type match (returns `null` on type mismatch).
- **Returns**: The widget element array, or `null`.

#### ef_handle_form_submit()
- **Signature**: `function ef_handle_form_submit(): void`
- **File**: `includes/forms/submission-handler.php:39`
- **Behavior**: AJAX action handler (`wp_ajax_ef_form_submit` + `wp_ajax_nopriv_ef_form_submit`). Validates nonce, honeypot, rate limit, signed timestamp, file uploads → emails the form → emits JSON response.

#### ef_form_check_rate_limit( $post_id, $widget_id )
- **Signature**: `function ef_form_check_rate_limit( int $post_id, string $widget_id ): void`
- **File**: `includes/forms/submission-handler.php:385`
- **Behavior**: Per-IP rate limit (per post + widget). Throws `WP_Error` if exceeded.

#### ef_form_upload_accepts_file( $file, $accept )
- **Signature**: `function ef_form_upload_accepts_file( array $file, string $accept ): bool`
- **File**: `includes/forms/upload-validator.php:19`
- **Behavior**: MIME-type guard for upload-type fields. `$accept` is the HTML `accept` attribute string (e.g., `'.pdf,.doc,.docx'`).

#### ef_form_upload_error_message( $code )
- **Signature**: `function ef_form_upload_error_message( int $code ): string`
- **File**: `includes/forms/upload-validator.php:66`
- **Behavior**: Map PHP upload error code (`UPLOAD_ERR_*`) → human message.

#### ef_form_client_ip()
- **Signature**: `function ef_form_client_ip(): string`
- **File**: `includes/forms/submission-handler.php:437`
- **Behavior**: Client IP, proxy-aware. Walks `HTTP_X_FORWARDED_FOR` only if remote addr is in `ef_form_ip_in_trusted_proxies()`.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_form_ip_network_prefix()` | `forms/submission-handler.php:422` | IP /24 (or /64) for signing |
| `ef_form_honeypot_name()` | `forms/submission-handler.php:505` | Salted honeypot field name |
| `ef_form_ip_in_trusted_proxies( $ip )` | `forms/submission-handler.php:523` | Proxy whitelist check |

The submission spam-screening surface (`forms/spam.php`) — `ef_normalize_email`, `ef_submission_sender_email`, `ef_submission_sender_ip`, `ef_index_submission_sender`, `ef_screen_all_submissions`, `ef_maybe_screen_submissions_once`, `ef_find_submissions_by_sender`, `ef_mark_sender_as_spam`, `ef_unmark_sender_as_spam`, `ef_spam_blocklist`, `ef_is_sender_blocklisted`, `ef_spam_blocklist_add`, `ef_spam_blocklist_remove` — is operator-tier, not on the build/audit path.

---

## SMTP (index-only)

Operator surface for EF's SMTP config UI. **Build/audit agents should never touch these** — they're admin-page + AJAX wiring, not render-pipeline.

| Helper | File | Purpose |
|---|---|---|
| `ef_smtp_messages()` | `smtp.php:81` | Message bag |
| `ef_smtp_field_consts()` | `smtp/config.php:8` | SMTP field constant names |
| `ef_smtp_secure_modes()` | `smtp/config.php:21` | TLS/SSL/none modes |
| `ef_smtp_presets()` | `smtp/config.php:32` | Preset provider configs (Gmail, SendGrid, etc.) |
| `ef_smtp_mailer_plugin_labels()` | `smtp/config.php:112` | Mailer-plugin display labels |
| `ef_smtp_active_mailer_plugins()` | `smtp/config.php:125` | Active mailer plugins (for conflict detection) |
| `ef_smtp_force_enabled()` | `smtp/config.php:142` | Force-enabled gate |
| `ef_smtp_has_mailer_plugin_conflict()` | `smtp/config.php:146` | Conflict detector |
| `ef_smtp_snippet_line( $field, $constant, $settings )` | `smtp/config.php:153` | Single config-snippet line |
| `ef_smtp_snippet_lines( $settings )` | `smtp/config.php:175` | All config-snippet lines |
| `ef_smtp_config()` | `smtp/config.php:191` | Full SMTP config for current request |
| `ef_smtp_add_text_setting(&$clean, $key, $value)` | `smtp/config.php:227` | Sanitize text setting |
| `ef_smtp_add_email_setting(&$clean, $key, $value)` | `smtp/config.php:238` | Sanitize email setting |
| `ef_smtp_add_connection_settings(&$clean, $input)` | `smtp/config.php:249` | Sanitize connection settings |
| `ef_smtp_add_password_setting(&$clean, $input, $existing)` | `smtp/config.php:271` | Sanitize + encrypt password |
| `ef_smtp_encrypt_password( $plaintext )` | `smtp/config.php:295` | Encrypt SMTP password |
| `ef_smtp_decrypt_password( $stored )` | `smtp/config.php:319` | Decrypt SMTP password |
| `ef_smtp_password_key()` | `smtp/config.php:348` | Encryption key for SMTP password |
| `ef_sanitize_smtp_settings( $input, $existing )` | `smtp/config.php:364` | Top-level sanitizer |
| `ef_smtp_test_settings( $input )` | `smtp/config.php:389` | Test settings (dry-run) |
| `ef_smtp_render_form( $settings )` | `smtp/admin-ui.php` | Admin form render |
| `ef_smtp_render_conflict_notice( $plugin_names )` | `smtp/admin-ui.php` | Conflict notice UI |
| `ef_smtp_render_preset_row( $selected, $presets )` | `smtp/admin-ui.php` | Preset row UI |
| `ef_smtp_render_admin_script( $presets )` | `smtp/admin-ui.php` | Admin inline JS |
| (SMTP AJAX handlers — test recipient / settings / send test message) | `smtp/hooks.php` | AJAX wire-up |

---

## Admin (index-only)

Admin pages + tokens UI. Operator surface — not for build/audit agents.

| Helper | File | Purpose |
|---|---|---|
| `ef_init_admin()` | `admin/hooks.php:11` | Admin coordinator |
| `ef_admin_page_tokens()` | `admin/tokens-page.php:113` | Tokens admin page |
| `ef_admin_page_settings()` | `admin/settings-page.php:10` | Settings admin page |
| `ef_admin_page()` | `admin/pages.php:228` | Root admin page |
| `ef_v4_required_notice()` | `admin/pages.php:18` | Admin notice when V4 experiment off |
| `ef_sanitize_settings( $input )` | `admin/settings-page.php:75` | Settings input sanitizer |

Submission moderation surfaces live in `admin/submission-meta-box.php` and `admin/submission-spam.php` (operator-tier; admin-page sanitizers and other token-row helpers live alongside in `admin/`). The earlier `admin.php` → `admin/tools.php` split was reorganized into `admin/hooks.php`, `admin/pages.php`, `admin/settings-page.php`, `admin/tokens-page.php`, and submission-page files; re-grep when you need a specific helper.

---

## Migrator

Migration step loader. Operator surface only.

| Helper | File | Purpose |
|---|---|---|
| `ef_migrator_auto_run()` | `migrator.php:167` | `admin_init` hook gate (idempotent) |
| `ef_migrator_load_steps()` | `migrator.php:187` | `require_once` all migration step files |

---

## Registry & autodiscovery

Glob-loading + class-discovery primitives. Build agents rarely call these directly — they're invoked during bootstrap. The one full-doc entry is `ef_register_row_prop_type()` because new row definitions plug in via that helper.

### Full-doc helpers

#### ef_register_row_prop_type( $key, $shape_factory )
- **Signature**: `function ef_register_row_prop_type( string $key, callable $shape_factory ): void`
- **File**: `includes/registry.php:210`
- **Behavior**: Register the row+rows prop classes for a composite repeater. `$key` is the row type ('action', 'heading', 'tag', etc.); `$shape_factory` returns the row's prop-type shape.
- **Side effect**: Creates `<Studly>_Row` (Object_Prop_Type) and `<Studly>_Rows` (Array_Prop_Type) classes via `ef_define_row_prop_classes()`, then registers both with Elementor's prop registry.
- **Called from**: `includes/register-rows.php`.
- **Example**:
```php
ef_register_row_prop_type( 'tag', function () {
    return [ 'text' => String_Prop_Type::make(), 'variant' => Enum_String::make([...]) ];
} );
```

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_glob_require( $pattern, $skip )` | `registry.php:37` | glob `require_once` |
| `ef_discover_handlers( $base_class, $preferred_order )` | `registry.php:78` | Discover subclasses keyed by `key()` |
| `ef_get_atomic_widgets()` | `registry.php:121` | List of registered EF widget classes |
| `ef_glob_register_instances( $folder, $base_class, $register )` | `registry.php:154` | Load files, validate type, register each |
| `ef_row_prop_type_config( $class )` | `registry.php:247` | Row prop type config metadata |
| `ef_row_prop_type_row_key( $class )` | `registry.php:255` | Row prop type wire key |
| `ef_row_prop_type_rows_key( $class )` | `registry.php:259` | Rows prop type wire key |
| `ef_row_prop_type_row_class( $class )` | `registry.php:263` | Row class metadata |
| `ef_row_prop_type_shape( $class )` | `registry.php:270` | Row shape metadata |
| `ef_define_row_prop_classes( $studly, $base_class )` | `registry.php:281` | eval-define row/rows classes |

---

## Misc small modules

Small one-offs spread across `includes/*.php`. Build/audit agents need `ef_json_encode` (workspace JSON convention), `ef_sanitize_svg` (when writing SVG content), and `ef_ajax_guard` (when adding admin-AJAX endpoints).

### Full-doc helpers

#### ef_json_encode( $data )
- **Signature**: `function ef_json_encode( $data ): string|false`
- **File**: `includes/json.php:20`
- **Behavior**: `json_encode` wrapper that always passes `JSON_UNESCAPED_UNICODE`. **Workspace convention** — see CLAUDE.md "Encoding". Use for any JSON that may end up in `_elementor_data` or any other postmeta to prevent the `é → é → literal u00e9` corruption path.
- **Returns**: JSON string or `false` on encode failure.

#### ef_sanitize_svg( $contents )
- **Signature**: `function ef_sanitize_svg( string $contents ): string`
- **File**: `includes/media.php:91`
- **Behavior**: Sanitize SVG content via `enshrined/svg-sanitize` (bundled in plugin-local `vendor/`). Use when accepting user-uploaded SVGs.

#### ef_ajax_guard( $action, $capability, $nonce_field )
- **Signature**: `function ef_ajax_guard( string $action, string $capability = 'edit_posts', string $nonce_field = 'nonce' ): void`
- **File**: `includes/ajax-security.php:34`
- **Behavior**: Nonce + capability check for an AJAX endpoint. Calls `wp_send_json_error()` and exits on failure.
- **Example**:
```php
function my_ajax_handler() {
    ef_ajax_guard( 'my_action' );
    // safe to proceed
}
```

#### ef_bootstrap()
- **Signature**: `function ef_bootstrap(): void`
- **File**: `includes/bootstrap.php:284`
- **Behavior**: Top-level plugin bootstrap. Loads all `includes/*.php`, wires hooks, registers V4 widget discovery.

### Index-only helpers

| Helper | File | Purpose |
|---|---|---|
| `ef_register_on_hooks( $fn, $hooks, $priority )` | `bootstrap.php:38` | Bind a callable to multiple hooks at once |
| `ef_register_widget_init_script()` | `bootstrap.php:61` | Register `ef-widget-init` |
| `ef_is_v4_active()` | `bootstrap.php:123` | Predicate: V4 experiment on |
| `ef_init_elementor()` | `bootstrap.php:130` | Elementor init coordinator |
| `ef_col_span_args()` | `feed.php:18` | `ts-post-feed` V3 col_span args |
| `ef_init_feed()` | `feed.php:46` | `ts-post-feed` V3 extension |
| `ef_site_uses_la_icons()` | `icons.php:17` | Predicate: site uses Line Awesome |
| `ef_render_voxel_icon_picker_template()` | `icons.php:40` | Render Voxel icon picker template |
| `ef_init_icons( $icon_pack )` | `icons.php:63` | Icon pack init |

---

## Helper density per category

| Category | Helpers | Surface |
|---|---|---|
| Atomic V4 | 14 | Build-critical |
| Pairs | 8 | Build-critical |
| Settings sections | 3 | Build-critical |
| Action types & controls | 13 | Build-critical |
| Voxel + dynamic-data | 17 | Build + audit |
| Loop | 8 | Build + audit |
| Voxel sub-resolvers | 2 | Build + audit |
| Forms | 13 | Form widget only |
| Icon helpers | 6 | Row + action rendering |
| Links | 4 | Build-critical |
| Responsive primitives | 8 | Build-critical |
| Grid | 7 | Layout |
| Map | 4 | Map widget only |
| Frontend / editor | 22 | Operator + 4 gating predicates |
| Editor preview post context | 3 | Editor preview |
| Dynamic tags | 9 | Editor wiring |
| Elementor data | 5 | Data I/O |
| Select options | 6 | Control building |
| Registry | 8 | Bootstrap |
| Misc | 12 | Mixed |
| Admin | 6 | Operator (re-org under `admin/`) |
| SMTP | 19 | Operator |
| Migrator | 2 | Operator |
| **Documented** | **~220 named** | Live count via re-grep is ~330 |

## How to refresh this file

When EF helpers shift (new `ef_*` added, signatures change, helpers removed), re-derive:

```bash
# 1. Re-grep every ef_* function declaration with file + line.
#    $WPDEV_WORKSPACE is the wpdev workspace root (the dir that contains cli/, sites/, plugins/).
grep -rn "^function ef_" "$WPDEV_WORKSPACE/plugins/custom/elementor-framework/includes/"

# 2. Live count (do not hard-code in this file — it drifts every release).
find "$WPDEV_WORKSPACE/plugins/custom/elementor-framework/includes" -name "*.php" \
  -exec grep -h "^function ef_" {} \; | wc -l

# 3. For any new helper: classify (build-critical → full doc, operator → index)
#    and add to the matching category. If category is missing, add a new H2.

# 4. Re-derive signatures by reading the function body's first line:
grep -A 1 "^function ef_<name>" includes/<file>.php
```

**Source of truth:** the helper code in `plugins/custom/elementor-framework/includes/`. This file is a navigation index — when in doubt, read the source. **Known retired** as of this revision: `ef_resolve_actions`, `ef_with_voxel_loop_transformed`, `ef_row_loop_transforms`, `ef_loop_transform_defaults`, `ef_loop_transforms_active`, `ef_loop_apply_transforms`, `ef_voxel_resolve_transform`, `ef_voxel_sort_args`, `ef_voxel_apply_transform`, `ef_content_section`, `ef_layout_pair`, `ef_force_init_wp_scripts`.
