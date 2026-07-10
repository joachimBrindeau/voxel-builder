# Known Defect-Class Repair

Use this fast path only when a target matches one catalog signature exactly. Novel or
ambiguous defects return to read-only audit and the owning mutation workflow.

## Known-Class Catalog

| Class | Exact detection | Mechanical repair |
|---|---|---|
| `loopable-row-missing-loop` | Repeater-scalar dtag in action/tag/heading row without `_vx_loop` | Add canonical row loop and scalar-subfield visibility |
| `array-comparator-mismatch` | `is_equal_to` against taxonomy/multiselect/relation subfield | Change comparator to `contains` |
| `fragile-vis-gate-on-structured-field` | section `is_not_empty` gate on work-hours/location/repeater/product object | Remove gate or bind a supported scalar child |
| `malformed-envelope` | outer type exists but required nested type markers are missing | Rebuild with authoritative `EF\Envelope` factory |
| `cols-inheritance-cascade` | nested wrapper has empty desktop cols beneath explicit parent cols | Set canonical child desktop `1fr` and verify reset |
| `missing-root-main` | document lacks one root EF wrapper with `tag: main` | Wrap root nodes in one canonical main wrapper |
| `missing-hero-header-tag` | first hero card under main has non-header semantic tag | Set approved hero tag to `header` |
| `cta-aside-mistag` | related/tangential final surface uses `section` | Set its wrapper tag to `aside` |

## Entry Criteria

1. Site, post id, CPT key, render URL, and requested catalog class are known.
2. `wpdev elementor:codegen --check` passes.
3. Existing data has a rollback snapshot and Behavior Contract.

## Phase 0 - Detect And Dry Run

**Entry:** Entry criteria are met; no mutation has occurred.

1. Dump current Elementor data and Voxel fields.
2. Run only the requested catalog detector across the tree.
3. Record every exact match as class, node id/path, evidence, and proposed diff in
   `/tmp/fix-known-<post_id>-report.md`.
4. Do not include near matches or invent a new class.

**Exit:** A complete dry-run report exists and stored state is unchanged.

## Gate 1 - Review Scope

**Entry:** Phase 0 report exists.

1. Present all matches, non-matches, affected paths, Behavior Contract boundaries, and
   expected observable delta in one view.
2. Require explicit selection of matches to repair. Silence or vague approval blocks.

**Exit:** Selected match ids are recorded; rejected/unselected matches remain untouched.

## Gate 2 - Confirm Exact Commands

**Entry:** Gate 1 selection is explicit.

1. Build one idempotent mutator using authoritative `EF\Envelope::*` factories.
2. Show the exact `wpdev elementor:mutate` command, rollback command, and verification
   assertions.
3. Require explicit execute confirmation.

**Exit:** Exact commands are confirmed, or the workflow halts without mutation.

## Phase 1 - Apply Selected Repairs

**Entry:** Both gates pass.

1. Run each target post's approved mutation as a separate command so one failure does not
   block unrelated targets.
2. Read every owned path back and compare it with the selected diff.
3. Run Elementor lint, CSS regeneration, and cache purge through the approved wrapper.

**Exit:** Every selected repair is applied/read back or failed explicitly; unselected paths
remain unchanged.

## Phase 2 - Verify

**Entry:** Phase 1 read-back and lint pass for at least one selected target.

1. Batch representative URL/surface leaves for browser verification with unique sessions.
2. Run screenshot, computed-style, rendered content, console/error, and Behavior Contract
   assertions.
3. Roll back a target whose expected class delta passes but another protected behavior
   regresses. Do not expand the fast path to repair the new issue.

**Exit:** Every selected target passes or is rolled back/reported as failed with evidence.

## Rationalizations To Reject

- "It looks similar": the mechanical detector must match exactly.
- "The dry run is approval": Gate 1 and Gate 2 are separate explicit decisions.
- "We can add a class now": add only after repeated production evidence and reference tests.
- "Lint is enough": class repairs require browser and Behavior Contract verification.

## Success Criteria

- [ ] One existing catalog class owned every repair.
- [ ] Dry run, scope approval, and exact-command approval were recorded.
- [ ] Writes were isolated and read back.
- [ ] Browser/Behavior Contract assertions passed or rollback completed.
