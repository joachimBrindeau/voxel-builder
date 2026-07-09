# Blueprint JSON Format

A Voxel CPT **blueprint** is the JSON that defines a custom post type's identity, fields, filters, and search configuration. It lives at `plugins/custom/voxel-addon/modules/Templates/blueprints/<key>/post_types.json` and is consumed by the Voxel addon's `TemplateImporter` when a CPT is created or updated.

This file documents the **skeleton** (top-level shape every blueprint must have). For the full catalog of field types — including the exact config schema, validation knobs, dynamic-tag exposure, and JSON template for each of the 33 Voxel field types — see [`voxel-field-types.md`](../voxel/voxel-field-types.md).

## Skeleton

```json
{
  "<key>": {
    "settings": {
      "key": "<key>",
      "singular": "<Label>",
      "plural": "<Labels>",
      "icon": "las la-file",
      "timeline": {"enabled": false, "wall": "disabled", "reviews": "disabled"},
      "messages": {"enabled": false},
      "submissions": {"enabled": false},
      "indexing": {"enabled": true},
      "options": {
        "default_archive_query": "disabled",
        "hierarchical": "enabled",
        "publicly_queryable": "enabled",
        "archive": {"has_archive": "disabled"}
      },
      "permalinks": {
        "custom": true,
        "slug": "<key>",
        "with_front": false
      }
    },
    "fields": [],
    "filters": [],
    "search": {
      "filters": [],
      "order": []
    }
  }
}
```

## Where each part is documented

- **`settings`** — top-level CPT identity, timeline/messages/submissions toggles, permalinks. See [`cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md) §Phase 1 + §Phase 3 (permalinks).
- **`fields`** — the field array. Each entry is `{type, key, label, …type-specific config}`. See [`voxel-field-types.md`](../voxel/voxel-field-types.md) for the complete catalog of every Voxel field type with its config, validation, and JSON template.
- **`filters`** — admin-side post-list filters. Shape parallels `search.filters`.
- **`search`** — frontend search filters + sort orders. See [`voxel-search.md`](../voxel/voxel-search.md) for filter types (keywords, terms, parent, relations, …) and sort clause shapes.

## Field visibility

Every field also inherits `visibility_rules` + `visibility_behavior` from `Base_Post_Field` — the Voxel-native, EA4V-free way to gate a field to a specific role, logged-in users, the post's author, a template context, or an arbitrary dynamic-tag expression. **30 built-in rule types**, AND/OR group semantics. See [`voxel-field-visibility.md`](../voxel/voxel-field-visibility.md) for the full catalogue, JSON shape, and copy-pasteable recipes (admin-only field, logged-in-only field, AND/OR composition, EA4V whitelist comparison).

## Registration in Templates.php

After writing the blueprint JSON, register the template in `plugins/custom/voxel-addon/modules/Templates/Templates.php` so the importer can find it:

```php
'<key>' => [
    'key' => '<key>',
    'label' => '<Label>',
    'field_count' => <N>,
    'type' => 'cpt',
    'description' => '<One-line description>',
    'path' => $blueprints_dir . '/<key>/post_types.json',
],
```

## Apply via PHP

```php
$importer = new \VoxelAddon\Modules\Templates\TemplateImporter();
$result = $importer->apply('<key>', '<key>', 'cpt');
```

The importer preserves site-specific keys on a re-import: `templates`, `custom_templates`, `settings.singular`, `settings.plural`, `settings.permalinks`. Everything else (fields, filters, search) is replaced wholesale.
