# Solution Absorption Workflow

Maintain Voxel Builder from the WordPress workspace's `docs/solutions/` corpus. This is
a supporting maintenance pipeline, not a primary user-task route.

## Entry Criteria

1. The WordPress workspace and voxel-builder skill roots are known.
2. The solution inventory is readable and the skill worktree can be validated.
3. Existing unrelated worktree changes have been identified and will be preserved.

## Phase 0 - Inventory And Classify

**Entry:** No solution file has been edited, moved, or deleted.

1. Run `python3 scripts/audit-solution-absorption.py <workspace-root>`.
2. Classify each unregistered file as `absorb`, `supersede`, `relocate`, or `retain`.
3. Select exactly one owning workflow/reference for every `absorb` item.
4. Keep site TODOs as plans, measurements/design assessments as audits, operational
   procedures as runbooks, and unrelated WordPress patterns as retained solutions.

**Exit:** Every solution has one disposition and no ambiguous owner remains.

## Phase 1 - Prove Freshness

**Entry:** Phase 0 classification is complete.

1. Check every command name against `cli/src/index.ts` or `wpdev --help`.
2. Check PHP/JS APIs, paths, schemas, and generated filenames against current source.
3. Reproduce behavior with the narrowest current unit/integration/browser probe.
4. Mark contradictions, removed APIs, unimplemented proposals, and historical site data
   as stale. Never promote them as current instructions.
5. Record concrete evidence paths in `references/core/solution-absorption.json`.

**Exit:** Each absorbable claim is current and source-backed; stale claims have an
explicit supersession reason.

## Phase 2 - Absorb Into One Owner

**Entry:** Freshness evidence is complete.

1. Add only durable, reusable behavior to the selected owner.
2. Reconcile contradictions in favor of current source/tests; do not preserve incident
   chronology in operational instructions.
3. Replace skill links to `docs/solutions/` with local owners.
4. Keep owner files within the workflow-skill size limits and update indexes.
5. Update the registry entry with disposition, owner, evidence, and concise reason.

**Exit:** The skill can execute the guidance without reading the source solution.

## Phase 3 - Validate Coverage

**Entry:** The owner contains the proposed absorbed guidance.

1. Compare every still-current section of the source with the owner.
2. Run relevant code tests plus `bash scripts/lint.sh` in the skill.
3. Run the absorption audit and require zero unclassified files and zero forbidden
   `docs/solutions/` dependencies in active skill files.
4. Search the WordPress workspace for inbound links to any source slated for removal.

**Exit:** Current guidance is complete, links resolve, tests pass, and removal is safe.

## Phase 4 - Retire, Relocate, And Final Gate

**Entry:** Phase 3 is green.

1. `absorb`: delete the source only after its owner is complete.
2. `supersede`: delete obsolete guidance after the registry records its current
   replacement/evidence.
3. `relocate`: move the file to `docs/plans/`, `docs/audits/`, or `docs/runbooks/`.
4. `retain`: leave unrelated reusable solutions in place and keep them classified.
5. Re-run the audit and all relevant link/quality checks.

**Exit:** No absorbed/superseded source remains, relocated records exist at their new
paths, retained files are intentional, and the repository is green.

## Rationalizations To Reject

- "The note is probably still right": source/test proof is mandatory.
- "Copy everything before deleting": incident chronology and stale APIs create drift.
- "The skill links back to the solution, so it is absorbed": that is a dependency,
  not absorption.
- "This TODO is knowledge": unfinished site work belongs in `docs/plans/`.
- "Delete it because it is old": age alone is not a disposition.
