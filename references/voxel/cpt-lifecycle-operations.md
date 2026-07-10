# CPT Lifecycle Operational Reference

## Field And Setting Reference

### Field key conventions

| Key | Consumer | Auto-integration |
|-----|----------|-----------------|
| `h1` | `LEAN_SEO_FIELD_TITLE` | `<title>` tag, og:title |
| `faq` (repeater: `question`/`answer`) | `lean_seo_get_repeater()` | optional on-page Q&A only — **do NOT emit `FAQPage` schema** for glossary/definition CPTs (Google deprecated FAQ rich results 2026-05-07) |
| `content` | Standard WYSIWYG | Template content via `@post(content)` |

### Voxel settings that must override defaults

| Setting | Default | Required | Why |
|---------|---------|----------|-----|
| `has_archive` | `"auto"` (=true) | `"disabled"` | Conflicts with lean-seo parent-page URLs |
| `hierarchical` | disabled | `"enabled"` | Required for cross-type routing |
| `publicly_queryable` | enabled | `"enabled"` | Required for sitemap + Smart Internal Linking |
| `with_front` | true | `false` | Prevents double-prefixing |

### Common failures

| Symptom | Root cause | Fix |
|---------|------------|-----|
| `Unknown column '_keywords' in 'field list'` on `wp_insert_post` (or any post save) | Index table column set is stale — blueprint added a filter source after the table was first created, a plain reindex (without `--recreate`) did not regenerate columns | Run `wpdev rebuild <site> --only reindex --recreate` (rebuilds the column set before reindexing), or recreate manually with `\Voxel\Post_Type::get('<key>')->index_table->recreate();` then re-index. This is Phase 2 step 5 and Phase 5 step 1 — re-run them. |
| `Call to undefined method Voxel\Post_Types\Index_Table::delete()` | `delete()` is not part of the API | Use `drop()` (DROP TABLE only) or `recreate()` (DROP + CREATE). See [`command-surface.md`](../core/command-surface.md) §"Voxel Index_Table — PHP API". |
| Reindex reports `0 posts indexed` and a later insert still crashes | The CPT was empty at reindex time, so the table was never touched; `create()` is `IF NOT EXISTS` so a stale table from a prior blueprint shape stays as-is | Always run `wpdev rebuild <site> --only reindex --recreate` on an empty/changed CPT — `--recreate` drops and rebuilds the column set even when there are 0 posts to index, per Phase 2 step 5 |

### Files modified per CPT creation

| File | Changes |
|------|---------|
| `plugins/custom/voxel-addon/modules/Templates/blueprints/<key>/post_types.json` | New blueprint |
| `plugins/custom/voxel-addon/modules/Templates/Templates.php` | Register blueprint |
| `wp_options` (`lean_seo_schema`) | Schema config for the new CPT |

## Revisions accumulate during the lifecycle

Two distinct revision streams accrue while building or modifying a CPT — both deserve a periodic prune:

- **WP post revisions** on the 4 Elementor templates created in Phase 1 (single, card, archive, form). Every editor save creates a `revision` post with its own `_elementor_data` clone. After heavy template editing: `wpdev elementor:revisions:prune <site> --post <template_id> --dry` to count, then drop `--dry` to snapshot+delete.
- **Voxel admin-config revisions** at `voxel:post-type-<key>:revisions` (a wp_options row). Snapshots the CPT's full Voxel config every time fields/filters/search change in admin or via `TemplateImporter::apply()`. Voxel never auto-prunes these. Inspect: `wpdev wp <site> option get 'voxel:post-type-<key>:revisions' --format=json --skip-plugins | jq 'length'`. To drop: `wpdev wp <site> option delete 'voxel:post-type-<key>:revisions' --skip-plugins` (the option is regenerated on the next admin save).

Surface both counts to the user when finishing CPT lifecycle work and offer the prune commands. See [`template-resolution.md`](./template-resolution.md) §Revisions.
