# Elementor Build Pipeline

Build or modify general Elementor Framework `_elementor_data`. Narrow artifacts have their
own primary routes: migration, archives/search, card actions, section-store extraction,
and known-defect repair do not enter here first.

## When To Use

- Build a page, single template, popup body, feed, loop, or general EF section tree.
- Add/restructure multiple widgets in existing Elementor data.
- Apply a gated Plan Document to a Voxel CPT template.

## When Not To Use

- Legacy V3 conversion: use `workflows/migrate.md`.
- Archive/search page ownership: use `workflows/archive-search-pages.md`.
- One action-row strip: use `workflows/card-actions.md`.
- Preview card scaffolding: use `wpdev voxel:cards` and the card reference.

## Entry Criteria

1. Site, target post/template id, role, render URL, and intended change are known.
2. New EF builds have a Plan Document requirement decision: trivial single-widget edit or
   full `workflows/page-planning.md` pipeline.
3. Existing data has a rollback export and Behavior Contract before mutation.

## Phase 0 - Preflight And Strategy

**Entry:** Entry criteria are known; no mutation has occurred.

1. Run `wpdev elementor:codegen` and require `wpdev elementor:codegen --check` to pass.
2. For existing data, export the full JSON/tree and snapshot revisions:
   ```bash
   wpdev elementor:dump <site> all --post <id> --json > /tmp/before-<id>.json
   wpdev elementor:tree <site> <id> > /tmp/before-tree-<id>.txt
   wpdev elementor:revisions:prune <site> --post <id>
   ```
3. Inspect `templates/index.md` and choose exactly one strategy. For a full page or
   single/hub template, check the **Pages** table FIRST: when a non-legacy `scope: page`
   composition matches the target archetype, adopt it as the whole-page starting tree
   rather than synthesizing the composition from loose sections.
   - `adapt-template`: a matching saved template exists — a `scope: page` composition for
     a whole page/single/hub, else `scope: section` parts assembled into the page.
     Splice the stored tree, then replace its documented `__TOKEN__` slots and re-bind
     loop/source dtags to the target CPT (per each template's `source_note`);
   - `rebuild-greenfield`: no matching template and current structure is a thin/broken/legacy liability;
   - `revise`: current structure is sound and the change is local.
4. Compute the run fingerprint from fields, schema hash, sample ids, and plan body. An
   unchanged stored fingerprint is a verified no-op.

**Exit:** Schema is current; rollback exists when required; one strategy and fingerprint
are recorded.

## Phase 1 - Gather Authoritative Context

**Entry:** Phase 0 passes.

1. Gather shared context once:
   ```bash
   wpdev elementor:schema <site>
   wpdev elementor:dump <site> all --post <id> --json
   wpdev elementor:tree <site> <id>
   ```
2. For Voxel CPT templates, gather fields and representative complete/sparse/typical data:
   ```bash
   wpdev voxel:fields <site> <cpt_key>
   wpdev voxel:sample <site> <cpt_key>
   wpdev voxel:data <site> --id <example_post_id>
   ```
3. For loops/templates, read exact `ef-wrapper` loop/template props from committed SSOT.
4. The `archive` page template is a `legacy-page-archive` starter for an intentionally
   retained page-backed search surface only. Never select it for a native CPT archive;
   leave this workflow and use `workflows/archive-search-pages.md` instead.
5. Preserve existing `ts-*` nodes verbatim only when replacement is outside scope. Verify
   every referenced post/template id still exists.

**Exit:** Current tree, authoritative widget shapes, valid fields, sample values, and any
preserved legacy dependencies are captured.

## Phase 2 - Plan

**Entry:** Phase 1 evidence is complete.

1. For a trivial single-widget edit, record the target path, exact prop delta, expected DOM,
   and Behavior Contract assertions.
2. Otherwise execute `workflows/page-planning.md` exactly through its computed gate.
3. Require the Plan Document to validate against
   `references/core/page-plan-contract.md` and carry `GATE: green (auto)` or an explicit
   operator approval on the documented exception path.

**Exit:** Every planned widget has an approved Blueprint row or the trivial-edit contract;
no open Critical plan finding remains.

## Phase 3 - Produce Widget Leaves

**Entry:** Phase 2 gate is green.

1. Enumerate stable widget scopes and non-overlapping insertion/replacement paths.
2. Batch 5-10 homogeneous widgets for `voxel-widget-builder` in build mode. Run waves no
   larger than the host concurrency cap (default four batches).
3. Require one common leaf envelope per widget with node JSON, schema source, insertion
   path, binding evidence, and validation result.
4. Retry rejected leaves at most twice; keep passing siblings.

**Exit:** Manifest coverage is exact; every required widget leaf is valid or explicitly
blocked. Any required blocked leaf halts the build.

## Phase 4 - Assemble And Validate Offline

**Entry:** All required Phase 3 leaves validate.

1. Sort leaves by Plan section order and tree position.
2. Adapt saved subtrees or merge revised nodes without overlapping paths. Regenerate cloned
   node ids and preserve untouched siblings byte-for-byte.
3. Enforce one root `ef-wrapper` with `tag: main` for full pages/templates; a single atomic
   widget may remain unwrapped when that is the complete document.
4. Write `/tmp/built-<id>.json` once and validate it:
   ```bash
   wpdev elementor:validate --file /tmp/built-<id>.json
   ```

**Exit:** One deterministic, schema-valid tree exists and its scope manifest equals the
approved Plan.

## Phase 5 - Write And Read Back

**Entry:** Phase 4 passes; rollback and confirmation gates are satisfied.

1. Select the write mechanism from `references/core/elementor-mutation-tools.md`.
2. For a full tree, run:
   ```bash
   wpdev elementor:import <site> <id> /tmp/built-<id>.json --save
   ```
3. For a surgical edit, run the approved `wpdev elementor:mutate` command. Do not use raw
   `wp eval-file` for single-post Elementor mutations.
4. Read `_elementor_data` back, compare owned paths with the aggregate, and run:
   ```bash
   wpdev elementor:lint <site> --post <id>
   wpdev rebuild <site> --only purge
   ```
5. Append fingerprint, plan/gate, write, rollback, and read-back evidence to the build ledger.

**Exit:** Stored data matches every owned path, untouched paths remain unchanged, lint is
clean, CSS/save hooks ran, and caches are purged.

## Phase 6 - Browser Verification

**Entry:** Phase 5 read-back passes and representative URLs are known.

1. Select complete, sparse, and typical posts whose data exercises planned bindings.
2. Batch 5-10 URL/surface leaves for verification, with unique browser sessions per URL.
3. Require screenshot inspection, computed-style assertions, rendered text/tag checks,
   console/page errors, network failures, canonical URL, and expected item counts.
4. Compare existing-data DOM text with the Behavior Contract baseline.
5. Route only failed scopes back to the owning repair task; keep passing scopes. Bound the
   verify-repair loop to the convergence rule in the dispatch contract.

**Exit:** Every required URL/surface passes, or residual failures are reported as failures.

## Route-Specific References

| Need | Read |
|---|---|
| Existing-data tools/rollback/Behavior Contract | `references/core/elementor-mutation-tools.md` |
| Page/Blueprint schema and examples | `references/core/page-plan-contract.md` |
| Archetype and heading vocabulary | `references/core/page-plan-archetypes.md` |
| Card variants | `references/ef/card-scaffolding.md` |
| Runtime symptom recovery | `references/core/build-troubleshooting.md` |
| Browser commands/assertions | `references/verification/browser.md` |

## Rationalizations To Reject

- "The schema probably has not changed": Phase 0 codegen/check is mandatory.
- "Worker-per-widget fan-out is more atomic": batch workers; keep leaf envelopes atomic.
- "The import succeeded, so the page is correct": stored, lint, and browser evidence are
  separate gates.
- "A missing value is a wiring bug": compare source data first; genuine empty values pass.
- "A worker can import its subtree": all shared-state writes stay centralized.

## Success Criteria

- [ ] Exactly one build strategy and primary route owned the task.
- [ ] Rollback, plan/trivial contract, and schema evidence exist.
- [ ] Widget manifest coverage is exact with bounded batches.
- [ ] One authoritative write was read back and linted.
- [ ] Browser and Behavior Contract assertions pass on representative data.
