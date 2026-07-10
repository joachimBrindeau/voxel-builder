# Voxel Field Types — Complete Catalog

Reference for every field type a Voxel CPT blueprint can declare. Each entry: PHP class, type key, required/optional config keys, validation, dynamic-tag exposure, gotchas.

Source of truth for native Voxel fields: `themes/voxel/app/config/post-types.config.php` `field_types` registry. All concrete field classes extend `Voxel\Post_Types\Fields\Base_Post_Field`, which extends `Voxel\Utils\Object_Fields\Base_Field`. Native registered field types: **33** (plus 2 timeline-internal fields not usable in CPT blueprints). For exact site availability including voxel-addon fields/replacements (`vote`, `slug`, `published-date`, `icon`, `excerpt`, `author`, `parent`, `main-color`, replacement `post-relation`), read [`voxel-field-inventory.md`](voxel-field-inventory.md) first.

## How to use this reference

- Looking up the shape of a field on an existing CPT? Run `wpdev voxel:fields <site> <cpt_key>` first to dump live config.
- Adding a field? Read [`voxel-field-inventory.md`](voxel-field-inventory.md) first to pick from the live native + voxel-addon availability, then use this catalog for deep native JSON/config notes and verify with `wpdev voxel:fields <site> <cpt>` (re-reads the registered field list).
- Most blueprint surfaces accept the universal base props (see below); only field-specific config keys are listed per type.

## Split Catalog

| Need | Reference |
|---|---|
| Universal props and scalar/editor/date/select fields | `voxel-field-types-core.md` |
| Taxonomy, location, media, relations, product, UI, repeater, recurring/profile fields | `voxel-field-types-advanced.md` |
| Timeline-only fields, selection patterns, validation, and storage | `voxel-field-types-patterns.md` |
