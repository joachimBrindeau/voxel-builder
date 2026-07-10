# Voxel Field Types: Patterns, Validation, And Storage

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
