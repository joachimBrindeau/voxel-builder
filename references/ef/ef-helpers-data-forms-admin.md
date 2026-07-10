# EF Helpers: Elementor Data, Forms, Admin, And Registry

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
