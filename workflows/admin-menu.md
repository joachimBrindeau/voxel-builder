# Voxel Lean Admin menu

Create a complete Lean Admin menu on a new Voxel site or align an existing
site when Voxel CPTs have been added, removed, or renamed. The source owner is
the `lean_admin_metamenu` WordPress option; Voxel's `voxel:post_types` option
and registered UI taxonomies are discovery inputs.

## Required references

- `references/core/rules.md`
- `references/core/criteria.md`

## Invariants

- Use `wpdev voxel:admin-menu`; do not hand-author option JSON.
- Every registered Voxel CPT shown in wp-admin gets one Content entry with
  `List`, `Create`, and `Edit` children.
- A top-level `Tags` group sits immediately after `Content` and contains every
  taxonomy term-management ref (`edit-tags.php?...`), including preserved core
  refs such as Categories and Tags plus discovered Voxel taxonomies.
- Sort top-level groups and every group of navigational siblings alphabetically
  by the label users see, then pin `Tags` immediately after `Content`. Compare
  accent-insensitively so localized labels sort naturally. Preserve intentional
  ref-child action sequences such as `List`, `Create`, `Edit` rather than
  alphabetizing them.
- Materialize inferred native labels into unlabeled refs before sorting when a
  stable post-type, taxonomy, core, or known-plugin label is available. This
  prevents the stored sort key from differing from the label users actually
  see at runtime.
- On an existing site, preserve non-Content groups and explicit non-Voxel
  Content refs, then sort them under the same rule. Update managed CPT refs
  before sorting so newly discovered entries land in their canonical place.
- On a site without a Lean Admin tree, install the command's complete baseline.
- A dry-run, rollback snapshot, persisted read-back, and admin-browser check are
  mandatory. Database equality alone does not prove the sidebar works.

## Phase 1: Resolve and inventory

**Entry:** The target site is known and Voxel plus Lean Admin are expected to be active.

1. Run `wpdev voxel:status <site>` and confirm both plugins are available.
2. Read `lean_admin_metamenu` and `voxel:post_types` through `wpdev wp <site>`.
3. Run `wpdev voxel:admin-menu <site> --tree` for a shell-style comparison of
   the exact stored `Original menu` and normalized `Active menu (planned)`.
   Use `--json` when orchestration needs exportable `originalTree` and
   `activeTree` arrays instead of formatted text.
4. Run `wpdev voxel:admin-menu <site> --dry --json`.
5. Compare reported `postTypes` with Content refs and reported `taxonomies`
   with Tags refs. Also inventory every existing `edit-tags.php?...` ref: core
   taxonomy refs may exist in stored menu even when runtime discovery omits
   them, and must migrate to Tags rather than remain under Content.

**Exit:** The current tree, discovered Voxel types, intended aligned tree, and
whether the operation is `created` or `aligned` are known.

## Phase 2: Capture rollback evidence

**Entry:** Phase 1 proves a change is required.

1. Save the exact current `lean_admin_metamenu` value to a temporary JSON file
   outside the repository. An absent option is recorded as absent, not `[]`.
2. Record the dry-run JSON beside it so the before/after intent is reviewable.
3. Stop if the dry-run replaces an unrelated existing node. Alphabetical
   reordering is expected; removal or semantic regrouping is not.

**Exit:** A restorable pre-write value exists and the dry-run preserves all
unmanaged menu choices.

## Phase 3: Apply once

**Entry:** Rollback evidence exists and the dry-run has no unrelated changes.

1. Run `wpdev voxel:admin-menu <site> --yes --json` once.
2. Require `dryRun: false`; `changed: true` is expected for a repair and
   `changed: false` is valid only when the site was already aligned.
3. Do not follow with direct `wp option update`; the command owns normalization.
4. The command must invalidate the persistent object-cache backend after a
   write. If runtime verification still sees the old tree, run
   `wpdev purge <site>` before diagnosing the stored configuration again.

**Exit:** The command reports a successful create/alignment against
`lean_admin_metamenu`.

## Phase 4: Persisted and idempotence verification

**Entry:** Phase 3 completed without an execution error.

1. Read `lean_admin_metamenu` back through `wpdev wp <site>`.
2. Assert every discovered Voxel CPT has exactly one direct Content ref and its
   children are exactly `List`, `Create`, and `Edit` with CPT-correct slugs.
3. Assert Content contains no `edit-tags.php?...` ref; Tags contains every
   discovered taxonomy ref and every preserved pre-write taxonomy ref exactly
   once, with `Tags` immediately after `Content` at top level.
4. Assert the before snapshot's unmanaged nodes still exist and every group of
   navigational siblings is alphabetically ordered by its displayed label.
5. Assert every ref-child action sequence retains its declared order, notably
   `List`, `Create`, `Edit`.
6. Rerun the dry-run and require `changed: false`.

**Exit:** Stored configuration matches the inventory, preserves unmanaged
choices, and is idempotent.

## Phase 5: Runtime verification

**Entry:** The persisted and idempotence checks pass.

1. Open any authenticated wp-admin screen with `agent-browser` in an isolated
   session and inspect the rendered Lean Admin sidebar. Use a cache-busting
   query parameter on the verification URL after a menu write; reopening the
   identical URL can reuse the browser's previous admin document even when the
   web process and option store already hold the new tree.
2. Expand every rendered top-level group and nested subgroup. Confirm visible
   sibling labels are alphabetically ordered using accent-insensitive
   comparison.
3. Expand each newly added or repaired CPT entry. Confirm `List`, `Create`,
   `Edit` retain that intentional order and resolve to the expected admin
   screens without console or page errors.
4. Capture screenshots showing the aligned and sorted flyouts.

**Exit:** Stored state and the rendered admin sidebar both prove the alignment.

## Example

Input: an existing site adds Voxel CPT `video`, while Content already contains
custom Elementor and plugin entries.

Output: `video` becomes `Videos > List / Create / Edit`; Content and all other
group sibling lists are alphabetized without losing custom entries; the second
dry-run reports no change.

## Success criteria

- The authoritative option is `lean_admin_metamenu`.
- Every current Voxel CPT is standardized under Content exactly once.
- Tags sits immediately after Content and owns every taxonomy term screen.
- All navigational sibling groups are alphabetized while action sequences keep
  their intentional order.
- Existing unmanaged choices are preserved; a new site receives the baseline.
- Rollback evidence, read-back, idempotence, and browser evidence all pass.
