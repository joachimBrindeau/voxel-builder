# Database Cleanup Ownership Reference

Use this reference with `workflows/database-cleanup.md`. It separates structural proof
from ownership guesses and keeps generic SQL from deleting valid Voxel/Elementor data.

## Decision Ladder

1. Does data need deletion, or only cache invalidation/reindexing?
2. Does WordPress or owning plugin expose an API/command? Use it.
3. Is row a structurally impossible orphan independent of plugin semantics?
4. Is absent owner proven by source, uninstall contract, and repository search?
5. If none apply, retain row and file an owner question.

## Ownership Matrix

| Surface | Owner-safe mutation | Required caution |
|---|---|---|
| Posts/pages/CPTs | `wp_delete_post()` | Handles revisions, comments, meta, terms, cache, hooks |
| Attachments | `wp_delete_attachment()` | Prove no Elementor, Voxel, option, usermeta, CSS, or custom-table reference |
| Comments | `wp_delete_comment()` | Recount parent post comments |
| Revisions | `wp_delete_post_revision()` / `wpdev elementor:revisions:prune` | Retain current autosaves and approved rollback depth |
| Post/comment/user meta | metadata APIs by meta ID | Anti-join proof; multisite users need network scope |
| Terms/taxonomies | term/object-term APIs | `object_id` is not universally a post ID |
| Options | `delete_option()` and current autoload APIs | Values may be serialized/shared; name prefix is not ownership proof |
| Transients | expired-only APIs/CLI | External object cache changes storage; unexpired rows may be locks |
| Cron | cron APIs/CLI | Never edit serialized `cron`; map every hook owner |
| Sessions | `WP_Session_Tokens` | Cleanup logs users out; explicit approval required |
| Voxel index tables | Voxel `Index_Table` methods | Active CPT indexes are derived but required; recreate then re-index |
| Elementor data | Elementor/wpdev commands | Preserve live `_elementor_data`, kits, templates, Voxel assignments |
| Plugin custom tables | plugin uninstall/API | Inactive or unfamiliar does not mean abandoned |
| Queue/action tables | owner retention commands | Pending/failed jobs are live state, not generic garbage |

## Audit Queries

Replace `<prefix>` with verified site prefix. These are report-only candidates:

```sql
SELECT COUNT(*) FROM <prefix>postmeta m
LEFT JOIN <prefix>posts p ON p.ID=m.post_id WHERE p.ID IS NULL;

SELECT COUNT(*) FROM <prefix>commentmeta m
LEFT JOIN <prefix>comments c ON c.comment_ID=m.comment_id WHERE c.comment_ID IS NULL;

SELECT COUNT(*) FROM <prefix>usermeta m
LEFT JOIN <prefix>users u ON u.ID=m.user_id WHERE u.ID IS NULL;

SELECT COUNT(*) FROM <prefix>term_relationships r
LEFT JOIN <prefix>term_taxonomy tt ON tt.term_taxonomy_id=r.term_taxonomy_id
WHERE tt.term_taxonomy_id IS NULL;

SELECT COUNT(*) FROM <prefix>term_taxonomy tt
LEFT JOIN <prefix>terms t ON t.term_id=tt.term_id WHERE t.term_id IS NULL;

SELECT COUNT(*) FROM <prefix>termmeta m
LEFT JOIN <prefix>terms t ON t.term_id=m.term_id WHERE t.term_id IS NULL;
```

Do not auto-delete this candidate without taxonomy ownership proof:

```sql
SELECT tt.taxonomy, COUNT(*)
FROM <prefix>term_relationships r
JOIN <prefix>term_taxonomy tt ON tt.term_taxonomy_id=r.term_taxonomy_id
LEFT JOIN <prefix>posts p ON p.ID=r.object_id
WHERE p.ID IS NULL
GROUP BY tt.taxonomy;
```

## Voxel And Elementor Gates

- Registered Voxel CPTs may own `wp_voxel_index_<key>` tables. Compare registered CPTs,
  configured filters, columns, and indexed post counts before drop/recreate.
- Voxel data can live in postmeta, termmeta, usermeta, JSON-string options, custom index
  tables, addon module tables/options, and cron. Source search and live registration matter.
- Voxel CPT configuration and template roles use JSON-string options `voxel:post_types`
  and `voxel:templates`; repair malformed values with `wpdev voxel:repair-options`.
- `voxel-addon` persistent tables include core logs/errors plus module-owned review import,
  product import, and voting tables. Deactivation does not prove them disposable; module
  cleanup paths own retention.
- Elementor live data includes `_elementor_data`, `_elementor_page_settings`, kits,
  `elementor_library`, generated CSS, revisions/autosaves, EF `_ef_has_ef_widget`, tokens,
  fonts, submissions, and Voxel template assignments.
- `wpdev elementor:revisions:prune` owns revision retention. Generated assets follow
  source cleanup, then CSS/rebuild and HTTP MIME verification.
- Media audit must parse serialized/JSON references across postmeta, options, usermeta,
  Voxel fields, Elementor trees, CSS, and custom tables before attachment deletion.

## Transaction And Batch Contract

- Freeze candidate primary keys before mutation; hash/export list.
- Confirm every target table engine; rollback assumptions require transactional tables.
- One transaction per owner/class. Delete children before parents.
- Use bounded PK batches when lock time or undo-log growth matters.
- Assert affected rows equal approved count; rollback otherwise.
- Do not mix DDL (`OPTIMIZE`, table rebuilds) with rollback-dependent DML.
- Treat `ANALYZE`, `CHECK`, `OPTIMIZE`, and `REPAIR` as potential implicit-commit boundaries.
- Pause imports, editors, queues, cron, and background indexing that can race candidates.
- After direct SQL, run owner recount/invalidation/regeneration; SQL success is not enough.

## Maintenance Meaning

- `CHECK TABLE`/`wp db check`: structural engine check, not semantic cleanup.
- `ANALYZE TABLE`: refresh optimizer statistics; no garbage deletion.
- `OPTIMIZE TABLE`: may rebuild InnoDB table/indexes; maintenance cost, not cleanup proof.
- `REPAIR TABLE`: engine-specific recovery; not routine InnoDB maintenance.

## Evidence Ledger

For each category record: owner, source/API, candidate query, approved IDs/count, backup,
batch/transaction, affected rows, recount/cache/index action, before/after count, behavior
probe, log result, and rollback command. Retained unknowns are successful safety outcomes,
not incomplete cleanup.
