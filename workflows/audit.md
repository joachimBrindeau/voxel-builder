# Read-Only Page And Template Audit

Audit a rendered Voxel/Elementor page or template without changing state. A request that
already specifies a mutation belongs to its owning mutation workflow, which performs its
own baseline instead of entering audit first.

## When To Use

- Review a page/template, explain what is wrong, or identify improvements.
- Validate a recent build using an independent read-only pass.
- Compare structure, available Voxel data, schema, and rendered behavior.

## When Not To Use

- Apply fixes: route approved findings to build, known-fix, CPT repair, settings, curation,
  or performance according to source owner.
- Create a new page/template: use `workflows/build.md`.
- Diagnose only performance metrics: use `workflows/performance.md`.

## Entry Criteria

1. Site and target post/template id or URL are known.
2. Audit focus and expected role are known or inferable.
3. No mutation is authorized inside this workflow.

## Phase 0 - Resolve Target And Baseline

**Entry:** Entry criteria are met.

1. Resolve post id, post type, template role, canonical/render URL, and representative
   complete/sparse/typical records when one template renders many posts.
2. Capture revision count and current tree fingerprint without pruning or writing.
3. Record iteration id and any prior report being re-audited.
4. Select applicable criteria from `references/core/criteria.md` by scope/phase.

**Exit:** Target identity, role, URL sample, criteria set, and immutable baseline ids are
recorded.

## Phase 1 - Gather Shared Evidence

**Entry:** Phase 0 target set is stable.

1. Gather stored structure once:
   ```bash
   wpdev elementor:lint <site> --post <id>
   wpdev elementor:tree <site> <id>
   wpdev elementor:dump <site> all --post <id> --json
   wpdev elementor:structure <site> --type <post_type>
   ```
2. Gather template/index context:
   ```bash
   wpdev voxel:templates <site>
   wpdev voxel:status <site>
   ```
3. For CPT templates, gather fields and representative values once:
   ```bash
   wpdev voxel:fields <site> <cpt_key>
   wpdev voxel:data <site> --id <sample_post_id>
   ```
4. Read committed schema/catalog artifacts and capture their hashes.

**Exit:** Shared stored, data, role, index, and schema evidence is available without
per-leaf repeated discovery.

When the request expands from a rendered target to every Voxel record or taxonomy
term, stop this page/template route and hand the target site to
[`integrity-loop.md`](integrity-loop.md). Consume its report only as record-level
evidence; this workflow remains the owner for page/template structure and rendered
behavior. Route each returned record finding by its declared `handoffWorkflow` rather
than treating the integrity report as authorization to mutate.

## Phase 2 - Inventory Global And Leaf Scopes

**Entry:** Phase 1 evidence is complete.

1. Run `voxel-page-auditor` on 1-4 page scopes to produce global findings plus section,
   widget, and URL manifests.
2. Check global invariants: template role, one root/main landmark where required, revision
   drift, index health, required content surfaces, and schema-lint status.
3. Run the combined silent-failure probes once across the target set:
   - relation-loop self traversal;
   - CSS-token fallback drift;
   - reindex-after-filter mismatch;
   - unicode escape corruption.
4. Mark probe hits `suspected` with an SME question until leaf/runtime evidence confirms them.

**Exit:** Every discovered section/widget/URL has one stable scope id; global findings are
separate; no leaf appears twice.

## Phase 3 - Audit Leaf Batches

**Entry:** Phase 2 manifests are non-overlapping.

1. Partition widget/section criteria into homogeneous batches of 5-10 leaves for
   `voxel-widget-builder` in audit mode or the applicable read-only specialist.
2. Partition browser verification into 5-10 URL/surface leaves per batch. Use unique
   browser sessions per URL within a bounded wave.
3. Run at most the host concurrency cap of batches (default four), validate each wave, and
   retry rejected leaves at most twice.
4. Require one leaf envelope per scope with positive evidence for passes and exact evidence
   for findings.

**Exit:** Leaf result coverage equals the Phase 2 manifests; every leaf is valid or
explicitly blocked.

## Phase 4 - Falsify And Classify

**Entry:** Phase 3 leaf results returned.

1. Confirm stored-vs-rendered contradictions. A missing DOM value is a bug only when source
   data exists and the relevant binding/visibility path should render it.
2. Classify findings without overlap:
   - dynamic tag;
   - loop/relation;
   - filter/visibility;
   - schema/SSOT;
   - layout/semantics;
   - content/data coverage;
   - runtime/performance signal.
3. Assign tier (`G`, `S`, `W`), severity (`Critical`, `Improvement`, `Cosmetic`), confidence
   (`confirmed`, `suspected`), source owner, and acceptance test.
4. Dedupe by root cause and scope. Preserve all affected scope ids on the canonical finding.

**Exit:** Every finding has one class, one source owner, evidence, confidence, and an
acceptance test; suspected findings remain visibly separate.

## Phase 5 - Report And Route Handoffs

**Entry:** Phase 4 classification is complete.

1. Produce one report with target/fingerprint, coverage manifest, global/section/widget
   findings, suspected items, underused data, and blocked evidence.
2. Sort by severity, tier, then scope id. Do not mix fixes into the report.
3. Map each confirmed finding to exactly one owning workflow:

   | Source owner | Handoff workflow |
   |---|---|
   | `_elementor_data` general structure/widget | `workflows/build.md` |
   | documented defect signature | `workflows/fix-known.md` |
   | CPT definition/runtime | `workflows/cpt-repair.md` |
   | Voxel record/content/relation | `workflows/curation.md` |
   | lean-seo output | `workflows/settings.md` |
   | measured performance | `workflows/performance.md` |

4. For an approved handoff, pass finding ids, owned paths, evidence, acceptance tests, and
   baseline fingerprint. The receiving workflow performs its own rollback/confirmation gate.

**Exit:** The user has a complete read-only report and every proposed next action has one
owner. No state changed during the audit.

## Report Contract

```json
{
  "target": {},
  "baseline_fingerprint": "",
  "coverage": {"expected": [], "returned": [], "blocked": []},
  "findings": [{
    "id": "",
    "tier": "G|S|W",
    "severity": "Critical|Improvement|Cosmetic",
    "class": "",
    "scope_ids": [],
    "source_owner": "",
    "confidence": "confirmed|suspected",
    "evidence": [],
    "acceptance_test": "",
    "handoff_workflow": ""
  }]
}
```

## Rationalizations To Reject

- "Audit and fix in one pass is faster": it destroys the independent baseline/reviewer.
- "One browser worker per URL is atomic": batch workers; keep URL envelopes atomic.
- "Lint passed, so layout passed": schema validity cannot prove visual/runtime behavior.
- "No issue was found, therefore it passed": a pass needs positive criterion evidence.
- "This suspected probe is probably real": keep it suspected until falsified/confirmed.

## Success Criteria

- [ ] Audit remained read-only.
- [ ] Global and leaf manifests are complete, disjoint, and evidence-backed.
- [ ] Bounded batches returned one result per scope.
- [ ] Findings are root-cause deduped and MECE-classified.
- [ ] Every approved next action has exactly one owning workflow.
