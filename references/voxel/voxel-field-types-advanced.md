# Voxel Field Types: Taxonomy, Relations, Media, UI, And Profile

## Catalog

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
