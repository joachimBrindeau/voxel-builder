# EF Helpers: Atomic, Settings, And Dynamic Data

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
> The retired card byline carried its own scalar `byline_action_*` slot; it does not exist. Its content folded into the `heading` content-block row (migration step 1336), which consumes the content-block row's action cells (the shared `loop+actions` envelope), not a flat `ef_atomic_action_props()` spread.

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
