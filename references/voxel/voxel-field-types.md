# Voxel Field Types — Complete Catalog

Reference for every field type a Voxel CPT blueprint can declare. Each entry: PHP class, type key, required/optional config keys, validation, dynamic-tag exposure, gotchas.

Source of truth for native Voxel fields: `themes/voxel/app/config/post-types.config.php` `field_types` registry. All concrete field classes extend `Voxel\Post_Types\Fields\Base_Post_Field`, which extends `Voxel\Utils\Object_Fields\Base_Field`. Native registered field types: **33** (plus 2 timeline-internal fields not usable in CPT blueprints). For exact site availability including voxel-addon fields/replacements (`vote`, `slug`, `published-date`, `icon`, `excerpt`, `author`, `parent`, `main-color`, replacement `post-relation`), read [`voxel-field-inventory.md`](voxel-field-inventory.md) first.

## How to use this reference

- Looking up the shape of a field on an existing CPT? Run `wpdev voxel:fields <site> <cpt_key>` first to dump live config.
- Adding a field? Read [`voxel-field-inventory.md`](voxel-field-inventory.md) first to pick from the live native + voxel-addon availability, then use this catalog for deep native JSON/config notes and verify with `wpdev voxel:fields <site> <cpt>` (re-reads the registered field list).
- Most blueprint surfaces accept the universal base props (see below); only field-specific config keys are listed per type.

## Universal base props (apply to all fields unless noted)

Every field inherits these from `Base_Post_Field`. Type-specific entries below only list keys beyond these.

| Key | Type | What it does |
|---|---|---|
| `type` | string | Field type key (e.g. `text`, `repeater`). Always required. |
| `key` | string | Unique field identifier within the CPT. Always required. Used as meta key, dynamic-tag handle, search filter source. |
| `label` | string | Admin / form display label. |
| `description` | string | Sub-label help text shown beneath the input in the admin form. |
| `required` | bool | Whether the field must have a value at save time. Server-enforced. |
| `hidden` | bool | Hides the field from the admin form (data may still exist if previously saved). |
| `css_class` | string | Extra class added to the form-row container; used by Elementor styling and custom CSS. |
| `enable-conditions` | bool | Master toggle for `conditions` array. |
| `conditions` | array | Groups of conditional rules (`{field, op, value}`) that decide whether this field appears. AND within a group, OR between groups. |
| `conditions_behavior` | `"show"` \| `"hide"` | Whether matching conditions show or hide the field. Default `"show"`. |
| `visibility_rules` | array | Role / capability rules (`{role, capability, …}`) controlling who sees the field. |
| `visibility_behavior` | `"show"` \| `"hide"` | Whether matching `visibility_rules` show or hide. Default `"show"`. |
| `overrides_enabled` | bool | Master toggle for per-rule overrides of inner model values (e.g. raise `maxlength` for premium plans). |
| `overrides` | array | List of `{visibility_rule, model_overrides}` blocks applied when the rule matches. |

> `default` is not in `Base_Post_Field::base_props()` — it's a per-field opt-in (most concrete field classes declare `'default' => null` and accept dynamic-tag syntax like `@author.first_name`, `@site.url`). UI-only fields (`ui-step`, `ui-heading`, `ui-image`, `ui-html`) do not.

For visibility-rule type strings (`user:role`, `user:logged_in`, `template:is_single_post`, …) and the JSON shape of a single rule, see [`voxel-field-visibility.md`](voxel-field-visibility.md) — that is the canonical catalogue, this file only consumes it.

Inherited methods every field services via overrides: `get_models()` (form-builder UI), `sanitize($value)`, `validate($value)`, `update($value)` (persistence), `get_value_from_post()` (read), `dynamic_data()` (exposes `@post(<key>)`).

---

## Catalog

### title

- **PHP class**: `Voxel\Post_Types\Fields\Singular\Title_Field`
- **File**: `app/post-types/fields/singular/title-field.php`
- **Type key**: `title`
- **Required config**: `key` (always `title`), `type` (always `title`)
- **Optional config**: `label`, `placeholder`, `minlength` (int|null), `maxlength` (int|null), `required` (default `true`), `default`, `description`, `css_class`, `hidden`
- **Validation**: `minlength` / `maxlength` enforced on character count via `mb_strlen`. Sanitized through `sanitize_text_field`.
- **Frontend behaviour**: Single-line text input. Writes to `wp_posts.post_title` (NOT post meta).
- **Dynamic-tag exposure**: Inherits post-level tag — `@post(title)` returns the title string. No custom `dynamic_data()`.
- **JSON template**:
```json
{ "type": "title", "key": "title", "label": "Titre", "required": true, "minlength": null, "maxlength": null }
```
- **Gotchas**: Singular — one per CPT, not allowed inside repeaters. `required` defaults to `true`. Lives in the `post_title` column, never in post meta.

### description

- **PHP class**: `Voxel\Post_Types\Fields\Singular\Description_Field` (extends `Texteditor_Field`)
- **File**: `app/post-types/fields/singular/description-field.php`
- **Type key**: `description`
- **Required config**: `key` (always `description`), `type` (always `description`)
- **Optional config**: `editor-type` (`plain-text` | `wp-editor-basic` | `wp-editor-advanced`, default `wp-editor-basic`), `placeholder`, `minlength`, `maxlength`, `required`, `default`, `description`, `css_class`, `hidden`
- **Validation**: `minlength` / `maxlength` (with `strip_tags` when WYSIWYG). For WYSIWYG, content is `wp_kses_post`-sanitized. Gutenberg block comments (`<!-- wp:* -->`) are stripped at save time.
- **Frontend behaviour**: Textarea (plain-text) or TinyMCE editor. Writes to `wp_posts.post_content` (NOT meta).
- **Dynamic-tag exposure**: Inherits post-level content tag — `@post(content)` returns raw post content.
- **JSON template**:
```json
{ "type": "description", "key": "description", "label": "Description", "editor-type": "wp-editor-basic" }
```
- **Gotchas**: Singular. Lives in `post_content`, never in meta. WYSIWYG mode silently strips Gutenberg block markers.

### timezone

- **PHP class**: `Voxel\Post_Types\Fields\Singular\Timezone_Field`
- **File**: `app/post-types/fields/singular/timezone-field.php`
- **Type key**: `timezone`
- **Required config**: `key` (always `timezone`), `type` (always `timezone`)
- **Optional config**: `label`, `description`, `required`, `css_class`
- **Validation**: must be a valid IANA timezone from `timezone_identifiers_list()`.
- **Frontend behaviour**: Searchable timezone dropdown that shows UTC offsets.
- **Dynamic-tag exposure**: `@post(timezone)` returns the IANA string (e.g. `Europe/Paris`).
- **JSON template**:
```json
{ "type": "timezone", "key": "timezone", "label": "Fuseau horaire", "required": true }
```
- **Gotchas**: Singular. Stored as post meta. Required by event-style CPTs that use `recurring-date` — accurate UTC normalization depends on it.

### text

- **PHP class**: `Voxel\Post_Types\Fields\Text_Field`
- **File**: `app/post-types/fields/text-field.php`
- **Type key**: `text`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `suffix` (input adornment), `minlength`, `maxlength`, `pattern` (regex), `default`, `description`, `required`, `css_class`, `hidden`
- **Validation**: `validate_minlength` / `validate_maxlength`. `pattern` is configured but only enforced **client-side** via HTML5 `pattern` attribute — no server check.
- **Frontend behaviour**: Single-line input.
- **Dynamic-tag exposure**: `Tag::String` — `@post(<key>)` returns the raw string.
- **JSON template**:
```json
{ "type": "text", "key": "h1", "label": "Titre H1", "required": true, "minlength": null, "maxlength": null }
```
- **Gotchas**: Sanitized via `sanitize_text_field`. Repeatable. Supports overrides for min/max length. `pattern` is not server-validated — anything that bypasses the form (REST, wp-cli) is unfiltered.

### texteditor

- **PHP class**: `Voxel\Post_Types\Fields\Texteditor_Field`
- **File**: `app/post-types/fields/texteditor-field.php`
- **Type key**: `texteditor`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `editor-type` (`plain-text` default | `wp-editor-basic` | `wp-editor-advanced`), `placeholder`, `minlength`, `maxlength`, `default`, `description`, `required`, `css_class`, `hidden`
- **Validation**: `minlength` / `maxlength` (`strip_tags` applied when WYSIWYG).
- **Frontend behaviour**: Textarea (plain-text) or TinyMCE editor with selected toolbar set.
- **Dynamic-tag exposure**: `Tag::String` — `@post(<key>)` returns `wpautop()`-wrapped content. Plain-text editor returns raw text.
- **JSON template**:
```json
{ "type": "texteditor", "key": "content", "label": "Contenu", "editor-type": "wp-editor-advanced" }
```
- **Gotchas**: For WYSIWYG saves, sanitized via `wp_kses_post`. Repeatable. `editor-type` is override-friendly.

### number

- **PHP class**: `Voxel\Post_Types\Fields\Number_Field`
- **File**: `app/post-types/fields/number-field.php`
- **Type key**: `number`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `suffix`, `min` (default `0`), `max` (default `1000`), `step` (default `1`, can be float), `display` (`input` | `stepper`), `default`, `required`, `css_class`, `hidden`, `description`
- **Validation**: `min <= value <= max` (rejects out-of-range with localized error).
- **Frontend behaviour**: Number input or stepper widget. Decimal precision derived from `step`.
- **Dynamic-tag exposure**: `Tag::Number` — `@post(<key>)` returns numeric. Indexed to a MySQL column auto-sized to `TINYINT`/`SMALLINT`/`MEDIUMINT`/`INT`/`BIGINT` based on `(min, max, step)`.
- **JSON template**:
```json
{ "type": "number", "key": "price", "label": "Prix", "min": 0, "max": 10000, "step": 0.01, "display": "input", "suffix": "€" }
```
- **Gotchas**: Indexable for `range` and `stepper` filters and `number-field` orderby. `step` determines the integer-storage multiplier in the index (e.g. `step: 0.01` stores `12.34` as `1234`). Re-indexing required after changing `min` / `max` / `step` because the underlying column type may change.

### switcher

- **PHP class**: `Voxel\Post_Types\Fields\Switcher_Field`
- **File**: `app/post-types/fields/switcher-field.php`
- **Type key**: `switcher`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `default` (`"1"` for checked, anything else unchecked), `required`, `css_class`, `description`, `hidden`
- **Validation**: cast to bool (`!! $value`).
- **Frontend behaviour**: Toggle switch.
- **Dynamic-tag exposure**: `Tag::Bool` — `@post(<key>)` returns `'1'` or `''`.
- **JSON template**:
```json
{ "type": "switcher", "key": "featured", "label": "Mis en avant", "default": "" }
```
- **Gotchas**: Meta is **deleted** when the value is false (not stored as `0`). Pairs with the `switcher` search filter. Querying for `meta_key=featured` will miss unchecked posts.

### email

- **PHP class**: `Voxel\Post_Types\Fields\Email_Field`
- **File**: `app/post-types/fields/email-field.php`
- **Type key**: `email`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `default`, `required`, `css_class`, `description`, `hidden`
- **Validation**: `validate_email` (uses WordPress `is_email`).
- **Frontend behaviour**: Email input. Sanitized via `sanitize_email`.
- **Dynamic-tag exposure**: `Tag::Email` — `@post(<key>)` returns the email string.
- **JSON template**:
```json
{ "type": "email", "key": "contact_email", "label": "Email de contact", "required": false }
```
- **Gotchas**: No custom max-length; relies on WordPress sanitization.

### phone

- **PHP class**: `Voxel\Post_Types\Fields\Phone_Field`
- **File**: `app/post-types/fields/phone-field.php`
- **Type key**: `phone`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `default`, `required`, `css_class`, `description`, `hidden`
- **Validation**: none beyond `sanitize_text_field`. **No format check**.
- **Frontend behaviour**: Single text input (no country-code picker).
- **Dynamic-tag exposure**: `Tag::String`.
- **JSON template**:
```json
{ "type": "phone", "key": "phone", "label": "Téléphone", "placeholder": "+33 1 23 45 67 89" }
```
- **Gotchas**: Effectively a text field with semantic naming. If you need a country picker or format validation, build it client-side or in a save hook.

### url

- **PHP class**: `Voxel\Post_Types\Fields\Url_Field`
- **File**: `app/post-types/fields/url-field.php`
- **Type key**: `url`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `default`, `required`, `css_class`, `description`, `hidden`
- **Validation**: regex must match `^(https?|ftp)://…`. Auto-prefixes `https://` when scheme is missing.
- **Frontend behaviour**: URL input. Sanitized via `sanitize_url`.
- **Dynamic-tag exposure**: `Tag::URL`.
- **JSON template**:
```json
{ "type": "url", "key": "website", "label": "Site web", "placeholder": "https://example.com" }
```
- **Gotchas**: Only `http`, `https`, and `ftp` accepted. `mailto:`, `tel:`, and other schemes rejected.

### color

- **PHP class**: `Voxel\Post_Types\Fields\Color_Field`
- **File**: `app/post-types/fields/color-field.php`
- **Type key**: `color`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `default` (hex like `#4129d9`), `required`, `css_class`, `description`, `hidden`
- **Validation**: `sanitize_hex_color` (rejects non-hex). **Hex only** — no `rgba()` or `hsl()`.
- **Frontend behaviour**: Color picker.
- **Dynamic-tag exposure**: `Tag::String` returning sanitized hex.
- **JSON template**:
```json
{ "type": "color", "key": "brand_color", "label": "Couleur de marque", "default": "#4129d9" }
```
- **Gotchas**: Hex only. Default normalized to lowercase. If you need alpha, store opacity in a separate `number` field.

### date

- **PHP class**: `Voxel\Post_Types\Fields\Date_Field`
- **File**: `app/post-types/fields/date-field.php`
- **Type key**: `date`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `enable_timepicker` (bool, default `false`), `placeholder`, `default` (any `strtotime`-parseable string, e.g. `2026-01-01 09:00:00`), `required`, `css_class`, `description`, `hidden`
- **Validation**: any `strtotime`-parseable input accepted; stored as `Y-m-d` (or `Y-m-d H:i:s` when timepicker enabled).
- **Frontend behaviour**: Pikaday date picker (+ optional time picker).
- **Dynamic-tag exposure**: `Tag::Object` with sub-properties `date` (`Tag::Date`) and `is_finished` (`Tag::Bool` — compares against post timezone "now").
- **JSON template**:
```json
{ "type": "date", "key": "event_date", "label": "Date de l'événement", "enable_timepicker": true }
```
- **Gotchas**: Pairs with `date` filter and `date-field` orderby. Indexable. Use `recurring-date` instead if you need multiple dates or repetition.

### time

- **PHP class**: `Voxel\Post_Types\Fields\Time_Field`
- **File**: `app/post-types/fields/time-field.php`
- **Type key**: `time`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `default` (`strtotime`-parseable like `12:30` or `9pm`), `required`, `css_class`, `description`, `hidden`
- **Validation**: `strtotime`-parseable; stored as `H:i`.
- **Frontend behaviour**: Time-only picker.
- **Dynamic-tag exposure**: `Tag::String` returning `H:i`.
- **JSON template**:
```json
{ "type": "time", "key": "checkin_time", "label": "Heure d'arrivée", "default": "15:00" }
```
- **Gotchas**: Pairs with `time-field` orderby. No `supported_conditions` — cannot be used in field-level conditional rules.

### select

- **PHP class**: `Voxel\Post_Types\Fields\Select_Field`
- **File**: `app/post-types/fields/select-field.php`
- **Type key**: `select`
- **Required config**: `key`, `type`, `label`, `choices` (array of `{value, label, icon?}`)
- **Optional config**: `placeholder`, `display_as` (`popup` | `inline`), `default`, `required`, `css_class`, `description`, `hidden`
- **Validation**: value must exist in `choices` array (else nulled).
- **Frontend behaviour**: Single-select dropdown or inline button group.
- **Dynamic-tag exposure**: `Tag::Object` with `value`, `label`, `icon` sub-properties. Access via `@post(<key>.value)`, `@post(<key>.label)`, `@post(<key>.icon)`.
- **JSON template**:
```json
{
  "type": "select", "key": "tier", "label": "Niveau", "display_as": "popup",
  "choices": [
    { "value": "free", "label": "Gratuit" },
    { "value": "pro", "label": "Pro" },
    { "value": "enterprise", "label": "Entreprise" }
  ]
}
```
- **Gotchas**:
  - **`@post(<key>)` returns the `Tag::Object`, NOT a string.** A bare `@post(product-type)` renders to empty in templates because the Object has no default string cast. Always use `@post(<key>.label)` for the human label, `@post(<key>.value)` for the raw key, or `@post(<key>.icon)` for the icon. The full comparator chain — `@post(<key>).is_equal_to(raw_value).then(...).else(...)` — also fails for the same reason; use `@post(<key>.value).is_equal_to(...)` or, if you only need display, replace the whole chain with `@post(<key>.label).is_not_empty().then(@post(<key>.label)).else(<fallback>)` (the choice → label mapping happens server-side via `get_selected_choice()`, no manual branching needed). Verified bug on a `select` field of a data-rich CPT; the callout was promoted into the catalog.
  - Icons go through `Voxel\get_icon_markup`. If you need a filter UI for the value, prefer `taxonomy` over `select` — `select` only pairs with field-level conditions, not search filters.

### multiselect

- **PHP class**: `Voxel\Post_Types\Fields\Multiselect_Field`
- **File**: `app/post-types/fields/multiselect-field.php`
- **Type key**: `multiselect`
- **Required config**: `key`, `type`, `label`, `choices`
- **Optional config**: `placeholder`, `display_as` (`popup` | `inline`), `default` (**pipe-delimited** e.g. `"Choice A|Choice B"`), `required`, `css_class`, `description`, `hidden`
- **Validation**: each chosen value must exist in `choices`.
- **Frontend behaviour**: Multi-checkbox popup or inline buttons. Stored as JSON array.
- **Dynamic-tag exposure**: `Tag::Object_List` — iterable, each item exposes `value`, `label`, `icon`.
- **JSON template**:
```json
{
  "type": "multiselect", "key": "amenities", "label": "Équipements", "display_as": "inline",
  "choices": [
    { "value": "wifi", "label": "Wi-Fi" },
    { "value": "parking", "label": "Parking" },
    { "value": "pool", "label": "Piscine" }
  ],
  "default": "wifi|parking"
}
```
- **Gotchas**: Default uses **pipe** (`|`) delimiter, NOT comma. `supported_conditions = ['taxonomy']` for field-condition compatibility.

### taxonomy

- **PHP class**: `Voxel\Post_Types\Fields\Taxonomy_Field`
- **File**: `app/post-types/fields/taxonomy-field.php`
- **Type key**: `taxonomy`
- **Required config**: `key`, `type`, `label`, `taxonomy` (taxonomy slug)
- **Optional config**: `placeholder`, `multiple` (bool, default `true`), `display_as` (`popup` | `inline`), `backend_edit_mode` (`custom_field` | `native_metabox`), `min`, `max`, `default` (comma-separated term slugs), `required`, `css_class`, `description`, `hidden`
- **Validation**: when `multiple`, enforces min/max **leaf** term count for hierarchical taxonomies (ancestors with selected children excluded from count).
- **Frontend behaviour**: Hierarchical term picker. Auto-selects all ancestors on save.
- **Dynamic-tag exposure**: Exposed via `Taxonomy_Field\Exports` trait — `@post(<key>)` returns iterable list of terms with `name`, `slug`, `link`, `icon`, etc.
- **JSON template**:
```json
{
  "type": "taxonomy", "key": "category", "label": "Catégorie",
  "taxonomy": "exp_category", "multiple": true, "min": 1, "max": 3,
  "display_as": "popup", "backend_edit_mode": "custom_field"
}
```
- **Gotchas**: `check_dependencies` throws when `taxonomy` doesn't exist — field is then hidden. Caches terms in a transient. Pairs with `terms` search filter. Min/max counts **leaves only**, not ancestors.

### location

- **PHP class**: `Voxel\Post_Types\Fields\Location_Field`
- **File**: `app/post-types/fields/location-field.php`
- **Type key**: `location`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `placeholder`, `always_show_map` (bool), `default` (object: `{address: string, point: "lat,lng"}`), `required`, `css_class`, `description`, `hidden`
- **Validation**: requires non-null `address`, `latitude`, `longitude`. Lat clamped to ±90, lng to ±180. Stored as JSON object with rounded 5-decimal coords.
- **Frontend behaviour**: Geocoded address autocomplete + optional draggable map picker.
- **Dynamic-tag exposure**: `Tag::Object` with `address`, `lat`, `lng`, `short_address` (first comma part), `medium_address` (first 2 parts), `long_address`, `distance.{meters,kilometers,miles}` (only valid inside `nearby` order context).
- **JSON template**:
```json
{
  "type": "location", "key": "location", "label": "Adresse", "always_show_map": true,
  "default": { "address": "Paris, France", "point": "48.8566,2.3522" }
}
```
- **Gotchas**: Pairs with `location` filter and `nearby` orderby. Supports per-subfield conditions on `address`, `latitude`, `longitude`. Calls `Voxel\enqueue_maps()` on render — make sure your Maps provider is configured. `default.point` is `"lat,lng"` as a single comma-separated string.

### work-hours

- **PHP class**: `Voxel\Post_Types\Fields\Work_Hours_Field`
- **File**: `app/post-types/fields/work-hours-field.php`
- **Type key**: `work-hours`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `required`, `description`, `css_class`
- **Validation**: groups validated as `{days: [mon, tue, …], status: hours|open|closed|appointments_only, hours: [{from, to}]}`. No day can appear in two groups.
- **Frontend behaviour**: Weekday-grouping UI; each group picks a status and optional hour slots.
- **Dynamic-tag exposure**: `Tag::Object` with `status` (`open` | `closed` | `appointments_only` | `not_available`), `status_label`, and per-day sub-objects (`mon`, `tue`, …, `today`) each exposing `schedule_key`, `schedule_label`, `hours[{start, end}]`.
- **JSON template**:
```json
{ "type": "work-hours", "key": "opening_hours", "label": "Horaires d'ouverture", "required": false }
```
- **Gotchas**: Maintains an indexed `wp_voxel_work_hours` table for the `open-now` filter (computes ranges in minute-of-week, handles overnight + sun→mon overflow). Pairs with `open-now` filter. Re-indexing required after changes.

### image

- **PHP class**: `Voxel\Post_Types\Fields\Image_Field` (extends `File_Field`)
- **File**: `app/post-types/fields/image-field.php`
- **Type key**: `image`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `max-count` (default `1`), `max-size` (kB, default `2000`), `default` (attachment ID), `required`, `css_class`, `description`, `hidden`. `allowed-types` is hidden — fixed to `image/jpeg,png,webp` via filter.
- **Validation**: count ≤ `max-count`, size ≤ `max-size`, MIME in allowed list.
- **Frontend behaviour**: Image uploader with previews. Sortable when `max-count >= 2`.
- **Dynamic-tag exposure**:
  - `max-count == 1` → `Tag::Object` with `id`, `url`, `name`.
  - `max-count >= 2` → `Tag::Object_List` (loopable) with `id`, `url`, `name`, plus a scalar `ids` (comma-separated string of all IDs).
- **JSON template**:
```json
{ "type": "image", "key": "gallery", "label": "Galerie", "max-count": 8, "max-size": 3000 }
```
- **Gotchas**: Stored as comma-separated attachment IDs in post meta. Single-image fields set the upload's `post_parent` to the parent post. Switching between `max-count: 1` and `max-count >= 2` changes the dynamic-tag shape and **breaks any widget reading the field**.

### file

- **PHP class**: `Voxel\Post_Types\Fields\File_Field`
- **File**: `app/post-types/fields/file-field.php`
- **Type key**: `file`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `max-count` (default `1`), `max-size` (kB), `allowed-types` (array of MIME strings — exposed to admin UI for `file` fields), `required`, `css_class`, `description`, `hidden`
- **Validation**: count, size, MIME enforcement via `File_Field_Trait`.
- **Frontend behaviour**: Uploader. Sortable when multi.
- **Dynamic-tag exposure**: Same as `image` — object (max-count=1) or object-list (max-count≥2) with `id`, `url`, `name`, `ids`.
- **JSON template**:
```json
{
  "type": "file", "key": "documents", "label": "Documents",
  "max-count": 5, "max-size": 5000,
  "allowed-types": ["application/pdf", "application/zip"]
}
```
- **Gotchas**: Parent class of `image`, `profile-avatar`, `comment-files`, `status-files`. Stored as comma-separated attachment IDs.

### post-relation

- **PHP class**: `Voxel\Post_Types\Fields\Post_Relation_Field`
- **File**: `app/post-types/fields/post-relation-field.php` (+ `post-relation-field/` traits)
- **Type key**: `post-relation`
- **Required config**: `key`, `type`, `label`, `post_types` (array of CPT keys)
- **Optional config**: `relation_type` (`has_one` default | `has_many` | `belongs_to_one` | `belongs_to_many`), `max_count` (only for `has_many` / `belongs_to_many`), `placeholder`, `allowed_authors` (`current_author` | `any`), `require_author_approval` (`never` | `always`), `allowed_statuses` (array; `publish` always included), `use_custom_key` + `custom_key` (alternate relation key), `default` (comma-separated post IDs), `required`, `css_class`, `description`, `hidden`
- **Validation**: enforces post-status whitelist (publish + `allowed_statuses`); enforces `max_count`; checks authorship / approval workflow.
- **Frontend behaviour**: Async post picker scoped to `post_types`. Pending-approval indicator when `require_author_approval` is set.
- **Dynamic-tag exposure**:
  - `has_one` / `belongs_to_one` → `Tag::Object` exposing the related post (full `Post_Data_Group` if exactly one CPT, else `Simple_Post_Data_Group`).
  - `has_many` / `belongs_to_many` → `Tag::Object_List` (loopable) yielding each related post.
- **JSON template**:
```json
{
  "type": "post-relation", "key": "services", "label": "Services",
  "post_types": ["exp"], "relation_type": "has_many", "max_count": 10,
  "allowed_authors": "any", "require_author_approval": "never"
}
```
- **Gotchas**: Backed by the `wp_voxel_relations` table — **NOT** post meta. `relation_key` defaults to field key but can be customized via `use_custom_key` + `custom_key`. Pairs with `relations`, `following-post`, `parent` filters. Primes related-post caches via `_prime_post_caches`. Changing `relation_type` requires data migration.

### product

- **PHP class**: `Voxel\Post_Types\Fields\Product_Field`
- **File**: `app/post-types/fields/product-field.php` (+ `product-field/methods/`)
- **Type key**: `product`
- **Required config**: `key`, `type`, `label`, `product-types` (array of Voxel `Product_Type` keys)
- **Optional config**: `required`, `description`, `css_class`. Very few top-level — the selected product-type itself defines downstream fields like `base-price`, `stock`, `variations`, `shipping`, `addons`.
- **Validation**: dispatched to the product-type's nested fields (`base-price` required when enabled, `stock` minimum, etc.). Uses `Config_Schema` for typed validation.
- **Frontend behaviour**: Complex multi-section UI driven by the selected `product_type` (regular / booking / variable). Renders nested form for base price, stock, custom prices, variations, addons, shipping.
- **Dynamic-tag exposure**: Exposed via `Product_Field\Exports` trait — provides pricing, availability, currency, base price, discounts, stock data as nested object tags.
- **JSON template**:
```json
{ "type": "product", "key": "product", "label": "Offre", "product-types": ["regular", "booking"] }
```
- **Gotchas**: Singular (`is_singular() = true`, `is_repeatable() = false`). Backed by Voxel `Product_Type` definitions registered separately. Pairs with `Stripe_Connect`, cart, vendor-onboarding flows. The special `voxel:promotion` key is handled distinctly.

### ui-step

- **PHP class**: `Voxel\Post_Types\Fields\Ui_Step_Field`
- **File**: `app/post-types/fields/ui-step-field.php`
- **Type key**: `ui-step`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `visibility_rules` (commonly used to hide admin-only steps from authors), all base props
- **Validation**: none (`is_ui() = true`). No `sanitize` / `validate` / `update` — pure form-organizing marker.
- **Frontend behaviour**: Visual section divider in the admin form / create-post wizard. Groups subsequent fields until the next `ui-step`.
- **Dynamic-tag exposure**: None (no data).
- **JSON template**:
```json
{ "type": "ui-step", "key": "step-general", "label": "Général" }
```
- **Gotchas**: Not repeatable. Use as a section header / tab divider in the field array. Fields after a `ui-step` belong to that step until the next `ui-step`.

### ui-heading

- **PHP class**: `Voxel\Post_Types\Fields\Ui_Heading_Field`
- **File**: `app/post-types/fields/ui-heading-field.php`
- **Type key**: `ui-heading`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `description`, `css_class`
- **Validation**: none (UI only).
- **Frontend behaviour**: Renders an in-form heading + description block. Used to label a sub-section without acting as a step boundary.
- **Dynamic-tag exposure**: None.
- **JSON template**:
```json
{ "type": "ui-heading", "key": "contact-heading", "label": "Coordonnées", "description": "Informations publiques de contact" }
```
- **Gotchas**: Subordinate to `ui-step` — lighter-weight section header. Doesn't create a wizard step boundary.

### ui-html

- **PHP class**: `Voxel\Post_Types\Fields\Ui_Html_Field`
- **File**: `app/post-types/fields/ui-html-field.php`
- **Type key**: `ui-html`
- **Required config**: `key`, `type`, `label`, `content` (Twig / dynamic-tag string)
- **Optional config**: `css_class`
- **Validation**: none.
- **Frontend behaviour**: Renders Twig content with `post`, `author`, `site` data groups available. Useful for inline help, custom alerts, computed read-only fields in the form.
- **Dynamic-tag exposure**: None (output only).
- **JSON template**:
```json
{ "type": "ui-html", "key": "intro-html", "label": "Intro", "content": "<p>Bonjour @author.first_name, complète ton profil ci-dessous.</p>" }
```
- **Gotchas**: Content rendered via `\Voxel\render()`. On a new post, the post group is `Noop` (post values still null) — guard with `{% if post.id %}`.

### ui-image

- **PHP class**: `Voxel\Post_Types\Fields\Ui_Image_Field`
- **File**: `app/post-types/fields/ui-image-field.php`
- **Type key**: `ui-image`
- **Required config**: `key`, `type`, `label`, `image` (attachment ID)
- **Optional config**: `css_class`
- **Validation**: none.
- **Frontend behaviour**: Displays a fixed media-library image inside the form. Used for inline visual instructions (e.g. "what your hero photo should look like").
- **Dynamic-tag exposure**: None.
- **JSON template**:
```json
{ "type": "ui-image", "key": "hero-example", "label": "Exemple", "image": 1234 }
```
- **Gotchas**: Outputs the `medium_large` size + alt text. The attachment ID is hard-coded — be careful when migrating between sites (IDs differ).

### repeater

- **PHP class**: `Voxel\Post_Types\Fields\Repeater_Field`
- **File**: `app/post-types/fields/repeater-field.php`
- **Type key**: `repeater`
- **Required config**: `key`, `type`, `label`, `fields` (array of nested field configs)
- **Optional config**: `min`, `max`, `row_label` (key of inner field used as row preview), `l10n_item` (default row label), `l10n_add_row` ("Add row" button text), `required`, `css_class`, `description`
- **Validation**: row count between `min` / `max`; each nested field validated per row.
- **Frontend behaviour**: Draggable list of rows; each row spawns the nested form. `row_label` accepts these inner types: `text`, `number`, `phone`, `email`, `date`, `select`, `multiselect`, `url`, `taxonomy`, `color`, `post-relation`, `time`.
- **Dynamic-tag exposure**: `Tag::Object_List` — iterable. Each item exposes nested fields' `dynamic_data()` tags keyed by inner field key. Use Twig `{% for item in @post(<key>) %}` then access via `item.<inner_key>`.
- **JSON template**:
```json
{
  "type": "repeater", "key": "faq", "label": "FAQ",
  "min": 0, "max": 20, "row_label": "question",
  "l10n_item": "Question", "l10n_add_row": "Ajouter une question",
  "fields": [
    { "type": "text", "key": "question", "label": "Question" },
    { "type": "texteditor", "key": "answer", "label": "Réponse", "editor-type": "wp-editor-advanced" }
  ]
}
```
- **Gotchas**: Stored as JSON-encoded array in post meta. Nested fields inherit step. **File-type nested fields store IDs inline within JSON** instead of a separate meta key. `product` is not appropriate as a nested field; `repeater` inside `repeater` works but is rarely useful.

### recurring-date

- **PHP class**: `Voxel\Post_Types\Fields\Recurring_Date_Field`
- **File**: `app/post-types/fields/recurring-date-field.php`
- **Type key**: `recurring-date`
- **Required config**: `key`, `type`, `label`
- **Optional config**: `allow_multiple` (bool, default `true`), `max_date_count` (default `3`), `allow_recurrence` (bool, default `true`), `enable_timepicker` (bool, default `true`), `required`, `css_class`, `description`
- **Validation**: row count ≤ `max_date_count` when multiple; `end >= start`; recurrence requires `unit` ∈ {`day`, `week`, `month`, `year`} + `frequency >= 1` + `until` date.
- **Frontend behaviour**: One or more date entries, each with optional multi-day, all-day, and "repeat every N {unit} until {date}" settings. Pikaday driven.
- **Dynamic-tag exposure**: `Tag::Object` with three iterable lists: `upcoming`, `previous`, `all`. Each item exposes `start`, `end` (`Tag::Date`), `is_multiday`, `is_happening_now`, `is_allday` (`Tag::Bool`).
- **JSON template**:
```json
{
  "type": "recurring-date", "key": "schedule", "label": "Planning",
  "allow_multiple": true, "max_date_count": 5,
  "allow_recurrence": true, "enable_timepicker": true
}
```
- **Gotchas**: Materialized into the `wp_voxel_recurring_dates` table (normalized UTC timestamps) so the `recurring-date` filter and orderby can use SQL. **Requires the CPT to have a `timezone` field** for accurate localization.

### profile-avatar

- **PHP class**: `Voxel\Post_Types\Fields\Profile\Profile_Avatar_Field` (extends `File_Field`)
- **File**: `app/post-types/fields/profile/profile-avatar-field.php`
- **Type key**: `profile-avatar`
- **Required config**: `key` (typically `voxel:avatar`), `type`
- **Optional config**: `label`, `max-size`, `default` (attachment ID), `required`, `css_class`, `description`
- **Validation**: image MIME types (jpeg, png, webp). `max-count` forced to `1`.
- **Frontend behaviour**: Single image uploader.
- **Dynamic-tag exposure**: Resolved via `@author.avatar` chain (since it writes to USER meta, not post meta).
- **JSON template**:
```json
{ "type": "profile-avatar", "key": "voxel:avatar", "label": "Avatar", "max-size": 2000 }
```
- **Gotchas**: Singular. Writes to **USER meta** on the post author (`update_user_meta($author_id, key, file_id)`), not post meta. Pairs with CPTs that have an "author profile" facet.

### profile-name

- **PHP class**: `Voxel\Post_Types\Fields\Profile\Profile_Name_Field` (extends `Text_Field`)
- **File**: `app/post-types/fields/profile/profile-name-field.php`
- **Type key**: `profile-name`
- **Required config**: `type`, `key` (typically `voxel:name`)
- **Optional config**: same as `text` — `label`, `placeholder`, `minlength`, `maxlength`, `required`, `default`, etc.
- **Validation**: inherits from `text`.
- **Frontend behaviour**: Text input.
- **Dynamic-tag exposure**: Resolved via author/user chain (`@author.display_name`).
- **JSON template**:
```json
{ "type": "profile-name", "key": "voxel:name", "label": "Nom affiché", "required": true }
```
- **Gotchas**: Singular. Writes the WP user `display_name` via `wp_update_user`, not post meta.

### profile-first-name

- **PHP class**: `Voxel\Post_Types\Fields\Profile\Profile_First_Name_Field` (extends `Text_Field`)
- **File**: `app/post-types/fields/profile/profile-first-name-field.php`
- **Type key**: `profile-first-name`
- **Required config**: `type`, `key` (typically `voxel:first_name`)
- **Optional config**: same as `text`.
- **Validation**: inherits from `text`.
- **Frontend behaviour**: Text input.
- **Dynamic-tag exposure**: Via author chain (`@author.first_name`).
- **JSON template**:
```json
{ "type": "profile-first-name", "key": "voxel:first_name", "label": "Prénom" }
```
- **Gotchas**: Singular. Writes WP user `first_name`.

### profile-last-name

- **PHP class**: `Voxel\Post_Types\Fields\Profile\Profile_Last_Name_Field` (extends `Text_Field`)
- **File**: `app/post-types/fields/profile/profile-last-name-field.php`
- **Type key**: `profile-last-name`
- **Required config**: `type`, `key` (typically `voxel:last_name`)
- **Optional config**: same as `text`.
- **Validation**: inherits from `text`.
- **Frontend behaviour**: Text input.
- **Dynamic-tag exposure**: Via author chain (`@author.last_name`).
- **JSON template**:
```json
{ "type": "profile-last-name", "key": "voxel:last_name", "label": "Nom" }
```
- **Gotchas**: Singular. Writes WP user `last_name`.

### profile-bio

- **PHP class**: `Voxel\Post_Types\Fields\Profile\Profile_Bio_Field` (extends `Texteditor_Field`)
- **File**: `app/post-types/fields/profile/profile-bio-field.php`
- **Type key**: `profile-bio`
- **Required config**: `type`, `key` (typically `voxel:bio`)
- **Optional config**: same as `texteditor`. `editor-type` forced to `plain-text`.
- **Validation**: inherits from `texteditor` (no minlength/maxlength enforced by default).
- **Frontend behaviour**: Textarea.
- **Dynamic-tag exposure**: Via author chain (`@author.description`).
- **JSON template**:
```json
{ "type": "profile-bio", "key": "voxel:bio", "label": "Biographie", "maxlength": 1000 }
```
- **Gotchas**: Singular. Writes WP user `description`. `editor-type` is locked to `plain-text` even if you pass `wp-editor-basic`.

---

## Timeline-only fields

These are NOT registered in `field_types` — they're internal to timeline status / comment forms and **not usable in CPT blueprints**. Documented here only so you don't try to declare them.

### comment-files (timeline-internal)

- **PHP class**: `Voxel\Timeline\Fields\Comment_Files_Field`
- **File**: `app/timeline/fields/comment-files-field.php`
- Drives reply attachments. Reads `max-count` / `max-size` from `settings.timeline.replies.images.*`. Not exposed to CPT blueprints.

### status-files (timeline-internal)

- **PHP class**: `Voxel\Timeline\Fields\Status_Files_Field`
- **File**: `app/timeline/fields/status-files-field.php`
- Drives status-post attachments. Reads from `settings.timeline.posts.images.*`. Not exposed to CPT blueprints.

---

## Quick-pick decision table

| Need | Use this type |
|---|---|
| Post title (always required, one per CPT) | `title` |
| Long-form body content (one per CPT) | `description` |
| Single-line text | `text` |
| Multi-line text / WYSIWYG (custom field) | `texteditor` |
| Number with min / max / step | `number` |
| Boolean toggle | `switcher` |
| Single image | `image` (`max-count: 1`) |
| Image gallery | `image` (`max-count: N`) |
| Generic file(s) | `file` |
| PDF / document upload | `file` (with `allowed-types`) |
| Date picker | `date` |
| Date + time | `date` (`enable_timepicker: true`) |
| Time-only | `time` |
| Event with recurrence | `recurring-date` (requires `timezone` field on CPT) |
| Timezone selector | `timezone` |
| Geo location + map | `location` |
| Business hours / open-now | `work-hours` |
| Single-choice enum | `select` |
| Multi-select enum | `multiselect` |
| Tags / categories (queryable) | `taxonomy` |
| Linked post (one) from another CPT | `post-relation` (`relation_type: has_one`) |
| Linked posts (many) from another CPT | `post-relation` (`relation_type: has_many`) |
| Belongs-to relation (inverse) | `post-relation` (`relation_type: belongs_to_*`) |
| Phone number | `phone` (no format validation) |
| URL | `url` (http/https/ftp only) |
| Email | `email` |
| Price / product / booking / variations | `product` |
| Hex color | `color` |
| Author display-name override | `profile-name` |
| Author first name | `profile-first-name` |
| Author last name | `profile-last-name` |
| Author avatar | `profile-avatar` |
| Author bio | `profile-bio` |
| Repeatable group of fields | `repeater` |
| Wizard / form section boundary | `ui-step` |
| Inline section header | `ui-heading` |
| Inline Twig / HTML / dynamic content | `ui-html` |
| Inline instructional image | `ui-image` |

---

## Common patterns

### Conditional fields (`enable-conditions` + `conditions`)

Each condition row uses `{source, type, value?}` where `source` is the sibling field's key and `type` is one of the registered condition types (`text:equals`, `text:not_empty`, `number:gt`, `switcher:checked`, `taxonomy:contains`, `date:gt`, `file:not_empty`, …). Registry: `themes/voxel/app/config/post-types.config.php` `condition_types`. Groups are `[[AND], OR [AND], …]`.

Show "event end date" only when "event type" equals `multi-day`:

```json
{
  "type": "date", "key": "event_end", "label": "Fin de l'événement",
  "enable-conditions": true,
  "conditions_behavior": "show",
  "conditions": [
    [{ "source": "event_type", "type": "text:equals", "value": "multi-day" }]
  ]
}
```

Hide "internal notes" from non-admins (`visibility_rules`, not `conditions` — viewer/role-based, not value-based; see [`voxel-field-visibility.md`](voxel-field-visibility.md) for the rule-type catalogue and JSON shape):

```json
{
  "type": "texteditor", "key": "internal_notes", "label": "Notes internes",
  "visibility_behavior": "show",
  "visibility_rules": [
    [ { "type": "user:role", "value": "administrator" } ]
  ]
}
```

### Field overrides per role / plan

Raise `maxlength` for premium users (the `visibility_rule` inside an override uses the same rule shape as `visibility_rules`):

```json
{
  "type": "text", "key": "tagline", "label": "Slogan", "maxlength": 80,
  "overrides_enabled": true,
  "overrides": [
    {
      "visibility_rule": { "type": "user:role", "value": "premium" },
      "model_overrides": { "maxlength": 200 }
    }
  ]
}
```

### Repeater of fields (FAQ pattern)

```json
{
  "type": "repeater", "key": "faq", "label": "FAQ",
  "min": 0, "max": 50, "row_label": "question",
  "fields": [
    { "type": "text", "key": "question", "label": "Question", "required": true },
    { "type": "texteditor", "key": "answer", "label": "Réponse", "editor-type": "wp-editor-basic" }
  ]
}
```

### Cross-CPT relation (full config)

A `studio` CPT linking to multiple `service` posts, any author, no approval gate:

```json
{
  "type": "post-relation", "key": "services_offered", "label": "Services proposés",
  "post_types": ["service"],
  "relation_type": "has_many",
  "max_count": 20,
  "allowed_authors": "any",
  "require_author_approval": "never",
  "allowed_statuses": ["publish", "draft"],
  "use_custom_key": false
}
```

### Wizard step + heading + computed help block

```json
[
  { "type": "ui-step", "key": "step-listing", "label": "Votre annonce" },
  { "type": "ui-heading", "key": "basics-heading", "label": "Informations de base" },
  { "type": "ui-html", "key": "tips", "label": "Conseils", "content": "<p>Une bonne annonce inclut au moins 3 photos et une description détaillée.</p>" },
  { "type": "title", "key": "title", "label": "Titre", "required": true, "minlength": 10, "maxlength": 100 },
  { "type": "description", "key": "description", "label": "Description", "editor-type": "wp-editor-basic", "minlength": 100 }
]
```

---

## Validation summary

| Type | Server-side | Client-only | Notes |
|---|---|---|---|
| `title` | min/max length, required | — | mb_strlen char count |
| `description` | min/max length, required | — | strip_tags applied for WYSIWYG |
| `timezone` | IANA whitelist | — | rejects unknown timezones |
| `text` | min/max length, required | `pattern` (HTML5) | pattern NOT server-enforced |
| `texteditor` | min/max length, required | — | wp_kses_post for WYSIWYG |
| `number` | min/max range, required | step | out-of-range rejected |
| `switcher` | bool cast | — | meta deleted when false |
| `email` | is_email, required | — | sanitize_email |
| `phone` | required only | — | no format check |
| `url` | http/https/ftp regex, required | — | auto-prefixes https:// |
| `color` | sanitize_hex_color, required | — | hex only |
| `date` | strtotime parseable, required | — | stored Y-m-d (+H:i:s) |
| `time` | strtotime parseable, required | — | stored H:i |
| `select` | value ∈ choices | — | unknown values nulled |
| `multiselect` | each value ∈ choices | — | pipe-delimited default |
| `taxonomy` | min/max leaf count, taxonomy exists, required | — | dependency check |
| `location` | non-null address+lat+lng, clamp ±90/±180, required | — | rounded to 5 decimals |
| `work-hours` | day-uniqueness across groups, required | — | indexed for open-now |
| `image` | count, size, MIME, required | — | MIME fixed (jpg/png/webp) |
| `file` | count, size, MIME (allowed-types), required | — | MIME configurable |
| `post-relation` | status whitelist, max_count, author/approval, required | — | uses wp_voxel_relations |
| `product` | dispatched to nested product-type fields | — | Config_Schema |
| `recurring-date` | row count, end≥start, recurrence shape, required | — | needs timezone field |
| `profile-avatar` | image MIME, max-count=1, required | — | writes to USER meta |
| `profile-name` | inherits text | — | writes user display_name |
| `profile-first-name` | inherits text | — | writes user first_name |
| `profile-last-name` | inherits text | — | writes user last_name |
| `profile-bio` | inherits texteditor (forced plain-text) | — | writes user description |
| `repeater` | row min/max + per-row inner validation | — | JSON-encoded meta |
| `ui-step` | — | — | UI only, no data |
| `ui-heading` | — | — | UI only, no data |
| `ui-html` | — | — | UI only, no data |
| `ui-image` | — | — | UI only, no data |

---

## Field-storage cheat sheet

| Type | Storage |
|---|---|
| `title` | `wp_posts.post_title` |
| `description` | `wp_posts.post_content` |
| `post-relation` | `wp_voxel_relations` table |
| `recurring-date` | post meta + `wp_voxel_recurring_dates` index |
| `work-hours` | post meta + `wp_voxel_work_hours` index |
| `number` | post meta + auto-sized indexed column |
| `image` / `file` | post meta (comma-separated attachment IDs) |
| `repeater` | post meta (JSON-encoded array; nested files inline) |
| `profile-*` | **USER meta** on the post author, not post meta |
| `switcher` | post meta (deleted when false) |
| all others | post meta |

When in doubt, run `wpdev voxel:fields <site> <cpt_key>` to dump the live config and verify the on-disk shape before authoring blueprint JSON.
