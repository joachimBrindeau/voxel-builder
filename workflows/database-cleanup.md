# WordPress Database Cleanup Workflow

Clean a Voxel + Elementor Framework WordPress database without treating unknown data as
garbage. This workflow owns inventory, retention cleanup, proven structural orphans,
abandoned plugin data, autoload/cron review, Voxel/Elementor regeneration, and database
maintenance. Read `references/voxel/database-cleanup.md` before mutation.

## Entry Criteria

- Target site, environment, database prefix, single-site/multisite scope, and maintenance
  window are known.
- `wpdev` can read WordPress and database state.
- A current database backup exists and its restore command/path is recorded.
- Cleanup intent is explicit: report-only, conservative cleanup, or approved full cleanup.

## Phase 1 — Baseline And Restore Gate

**Entry:** Target and cleanup intent are known.

1. Use `wpdev` before raw `wp`, `mysql`, or direct filesystem operations.
2. Capture active, inactive, MU, network-active plugins, theme, WordPress version,
   multisite state, table prefix, object-cache backend, cron runner, and write traffic.
3. Create a named backup with `wpdev backup:create <site>` and record exact restore path.
4. Capture table row counts/sizes, engine/collation, total/autoload option bytes, revision,
   trash, transient, cron, session, and structural-orphan counts.
5. Capture behavior baselines: home, admin, REST, login, representative Voxel single,
   archive/search, Elementor template, forms/checkout, cron, and error log.
6. Stop every background writer that can re-create what you are about to remove, and
   prove it stopped. On a Voxel Addon site the product importer is such a writer:
   `wpdev voxel:imports <site> halt` records the halt, and
   `wpdev voxel:imports <site> verify` proves it by *attempting* to arm both import
   events with plugins loaded and failing if either survives.
7. Never treat an emptied cron slot as proof a writer stopped. `ImportWorker` re-arms its
   maintenance event on every `init`, so deleting the event is undone by the next HTTP
   request within seconds. Persistent state gates execution; the cron array only reflects
   it. The same shape applies to any scheduler that self-heals: stop the *source*, then
   re-read after real traffic.
8. Hard-stop when backup, ownership scope, or restore path is missing.

**Exit:** Immutable before-state evidence, a usable rollback artifact, and background
writers proven halted.

## Phase 2 — Parallel Ownership Audit

**Entry:** Baseline and backup exist.

1. Fan out read-only scopes in bounded batches: core rows, metadata/orphans, options and
   autoload, cron/sessions/transients, custom tables, Voxel indexes, Elementor data,
   media references, and inactive-plugin residue.
2. Give every candidate an owner: WordPress core, active plugin/theme, inactive plugin,
   removed plugin, Voxel, Elementor/EF, site custom code, or unknown.
3. Classify proof as `api-owned`, `structural-orphan`, `owner-abandoned`,
   `retention-candidate`, or `unknown`. Unknown means no deletion.
4. Treat `term_relationships.object_id NOT IN wp_posts` as a candidate only. Taxonomies
   may relate non-post objects; prove taxonomy object ownership before deletion.
5. When deletion turns on what a record *is* rather than whether it is orphaned, verify
   the deciding signal before trusting it, and expect the obvious one to be wrong. On a
   real Voxel product catalog the taxonomy labeled hoodies, whisks, and books as
   "Matcha"; the Voxel `product.product_type` meta was the same literal string on every
   row; and the Shopify `product_type` was empty on more than half and multilingual on
   the rest. Corroborate at least two independent signals, keep an explicit `ambiguous`
   bucket, and never let a record be destroyed by a signal you have not spot-checked
   against the actual titles.
6. Confirm the post type key against the database (`SELECT DISTINCT post_type`) rather
   than inferring it from the plugin or the UI label. Voxel product CPTs register as
   `products`, and a query for `product` silently returns zero rows, which reads exactly
   like "nothing to clean".
7. Produce a cleanup manifest with candidate query/API, count, owner, proof, risk,
   rollback unit, batch size, expected side effects, and verification.
8. For Voxel-managed records and all registered taxonomy terms, run or consume the
   read-only [`integrity-loop.md`](integrity-loop.md) report. Only confirmed
   structural `orphan-relation`, `orphan-media`, and explicit owner contradictions
   may enter the cleanup candidate manifest. Content findings, suspected findings,
   custom/unsupported shapes, and term-meta unknowns route elsewhere or remain
   blocked. The integrity report is evidence, never mutation approval.

**Exit:** Every proposed deletion has an owner and proof; unknowns remain excluded.

## Phase 3 — Confirmation Gate One

**Entry:** Cleanup manifest exists.

1. Present before counts, exact categories, retained exceptions, backup path, maintenance
   impact, and operations that log users out, delete recoverable revisions, or rebuild
   indexes/tables.
2. Require explicit approval for manifest scope. Approval of “cleanup” does not approve
   unknown tables/options, all sessions, all revisions, media deletion, or DB repair.
3. Freeze the approved manifest. New candidates require a new audit and approval.

**Exit:** Operator-approved, immutable mutation manifest exists.

## Phase 4 — API-First Retention Cleanup

**Entry:** Gate one approved.

1. Delete expired transients through WordPress/WP-CLI; force database expiry only when
   external object-cache semantics are understood. Never delete all unexpired transients.
2. Apply explicit retention to revisions/autosaves with `wp_delete_post_revision()` or
   `wpdev elementor:revisions:prune`; protect current autosaves and approved rollback depth.
3. Empty only approved aged trash/auto-drafts through `wp_delete_post()` and
   `wp_delete_comment()` so hooks, terms, metadata, children, and caches are handled.
4. Remove stale cron through cron APIs/commands, never by editing serialized `cron`.
   Unscheduling removes an *occurrence*, not a producer: if code re-arms the hook, the
   event returns. Deleting a live plugin's event is a no-op at best, so halt the owner
   instead and confirm with a scheduling attempt, not a cron listing.
5. Destroy sessions only when logout impact is approved; use `WP_Session_Tokens` APIs.
6. Remove abandoned options through `delete_option()`/`delete_site_option()` and change
   autoload through current WordPress APIs, never raw serialized-value edits.
7. Uninstall a plugin before residual cleanup when its uninstall routine is available;
   re-audit residue after uninstall instead of assuming it worked.

**Exit:** Supported APIs handled all approved API-owned and retention candidates.

## Phase 5 — Confirmation Gate Two

**Entry:** API cleanup is complete and remaining direct-SQL/plugin-owned candidates were
re-counted against the frozen manifest.

1. Present exact remaining primary keys/counts, table engines, transaction boundaries,
   owner proof, batch sizes, and regeneration/rollback commands.
2. Require explicit approval for direct SQL, custom-table deletion, media deletion, Voxel
   index recreation, session destruction, `OPTIMIZE`, or any maintenance with locks.
3. Do not inherit gate-one approval when counts, owners, engines, or SQL changed.

**Exit:** High-risk mutation set is explicitly approved with current evidence.

## Phase 6 — Proven Structural Orphans

**Entry:** Gate two approved.

1. Re-run anti-joins; exclude rows already removed by APIs and concurrent recreations.
2. Prefer metadata APIs such as `delete_metadata_by_mid()` for bounded orphan metadata.
3. Use direct SQL only for proof-complete rows with no applicable API. Run transactions
   per ownership class, bounded primary-key batches, and exact `WHERE` predicates.
4. Delete children before parents. Preserve term/taxonomy rows until relationship owner
   is proven; remove terms only when no taxonomy rows remain.
5. Never search/replace or mutate serialized option/meta values during cleanup.
6. After every batch, compare deleted count to manifest expectation. Roll back on drift,
   SQL warnings, lock timeout, unexpected owner, or changed candidate count.

**Exit:** Approved structural-orphan counts reach zero or documented concurrent residue.

## Phase 7 — Voxel, Elementor, And Plugin-Owned Data

**Entry:** Core structural cleanup passes.

1. Inventory every non-core table and map it to current source/uninstall ownership. Table
   name resemblance or inactive status alone is insufficient deletion proof.
2. Preserve Voxel JSON-string options `voxel:post_types` and `voxel:templates`; use
   `wpdev voxel:*` and `wpdev voxel:repair-options`, not raw option edits.
3. Preserve Voxel index tables for registered CPTs. Recreate through
   `\Voxel\Post_Type::get('<key>')->index_table->recreate()` only when schema/index drift
   is proven, then re-index posts; never “optimize” by dropping active indexes.
4. Preserve Voxel relations, fields, timeline/messages, hierarchy jobs, import state, and
   cron queues unless their owning workflow proves abandonment.
5. Preserve `voxel-addon` logs/errors, review/product-import identity and event tables,
   custom-field votes, lifecycle options, and shared indexes until module ownership proves
   their retention/deletion contract. Deactivation does not drop persistent module data.
6. Preserve live `_elementor_data`, kits, library templates, Voxel template assignments,
   EF tokens/fonts, form submissions, and rollback revisions required by current work.
7. After Elementor/EF cleanup, regenerate through repository workflows and flush CSS;
   never delete generated assets without regeneration and MIME/status verification.
8. Run media-unused audit separately. Delete attachments only through
   `wp_delete_attachment()` after Elementor JSON, Voxel fields, options, usermeta, CSS,
   and custom-table references are all excluded.
9. For Action Scheduler/WooCommerce or other queue tables, use owner commands/APIs and
   retention policies; never generic age-based SQL against pending/failed jobs.

**Exit:** Plugin-owned cleanup preserves live source owners and rebuilds derived state.

## Phase 8 — Options, Counts, Cache, And Regeneration

**Entry:** Data deletion phases complete.

1. Re-measure autoload bytes. Remove confirmed abandoned rows first; disable autoload only
   for large infrequently needed options after proving request-path ownership.
2. Recount affected comments and taxonomies with WordPress APIs; do not trust stale stored
   term counts after direct relationship cleanup.
3. Clear targeted plugin caches first. Use `wpdev purge`/repository cache helpers for broad
   invalidation; record shared-cache or multisite blast radius.
4. Regenerate Voxel indexes, Elementor CSS/assets, rewrite rules, and plugin caches only
   when their source data changed.

**Exit:** Derived counts, indexes, generated assets, and caches match cleaned source data.

## Phase 9 — Database Maintenance

**Entry:** Application-level verification passes after cleanup.

1. Confirm target table engines. Transaction rollback protects InnoDB DML, not
   nontransactional engines or implicit-commit maintenance statements.
2. Run `wpdev wp <site> db check` and inspect every table result.
3. Use `ANALYZE TABLE`/owner tooling when optimizer statistics need refresh.
4. Run `db optimize` only during the approved maintenance window; expect InnoDB rebuild,
   temporary disk use, metadata locks, and no guaranteed proportional file shrink.
5. Keep `ANALYZE`, `CHECK`, `OPTIMIZE`, and `REPAIR` outside rollback-dependent cleanup
   transactions because MySQL may commit implicitly.
6. Run repair only for reported corruption and only when storage engine supports it.
   `REPAIR TABLE` is not routine InnoDB cleanup.

**Exit:** Database check passes; optional maintenance completed without application drift.

## Phase 10 — Verification, Rollback, And Report

**Entry:** All approved mutations and maintenance complete.

1. Re-run every baseline count/query and produce before/deleted/after totals per manifest
   item. Zero is required only where the manifest says zero is valid.
2. Verify repeated cold/warm WordPress boots, front end, admin, REST, login, Voxel single,
   archive/search, Elementor templates, forms/checkout, cron, queues, and logs.
3. Verify retained plugin behavior by function, hook, option, index, rendered content, or
   owner-specific health check—not plugin activation status alone.
4. Compare logical rows removed separately from physical storage reclaimed.
5. Roll back when behavior, ownership, counts, generated assets, queues, or logs diverge.
6. Record excluded unknowns, concurrent residue, backup/restore command, commands run,
   SQL hashes, final counts, and follow-up owner work.

**Exit:** Cleanup is evidence-complete, behavior-preserving, and independently reversible.

## Production Database Push Safety

When database cleanup is followed by `wpdev remote:sync:push --db`, treat the push as a
separate mutation gate rather than a transport detail:

1. Prove every local base table has a primary key before export. WordPress serialized-safe
   all-table search/replace may refuse keyless tables; repair an owned schema at its source,
   or preserve an owner-abandoned backup table only after proving its candidate key is unique
   and non-null. Never bypass the all-table convergence gate.
2. Stage a complete local export before opening the remote import stream. Export with
   `--single-transaction --hex-blob`, compress to a temporary artifact, validate it with
   `gzip -t`, then atomically promote it. A failed or changing local export must leave the
   remote database untouched.
3. After import, run serialized-safe replacement across every table for the full local URL,
   HTTP variant, and bare local domain. Require exact remote `siteurl`/`home` values and an
   all-table dry-run leftover count of zero.
4. Re-run production hardening after the database overwrite: remove development users and
   their public profiles, use `$wpdb->users` rather than a literal `wp_users` table, and
   prove temporary hardening scripts were removed.
5. Record the last pre-import safety backup, database check, zero-leftover result, canonical
   URLs, deleted-user read-backs, cache purge, and browser smoke evidence in the handoff.

## Non-Negotiable Stops

- No current backup or restore command.
- Unknown owner, multisite scope, or object domain.
- Direct SQL proposed where a supported owner API exists.
- Candidate count changes between approval and mutation without re-approval.
- Active writes, imports, queues, or cron can race cleanup.
- Verification proves only row counts, not Voxel/Elementor/application behavior.
