# EF Helpers: Grid, Map, Assets, Editor, And Dynamic Tags

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
