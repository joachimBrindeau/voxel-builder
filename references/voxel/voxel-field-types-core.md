# Voxel Field Types: Base And Core Fields

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
