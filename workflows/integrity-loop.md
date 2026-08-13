# Resumable Voxel Integrity Loop

Run a database-wide, read-only integrity scan across live Voxel-managed CPT records
and every registered taxonomy term. The loop produces resumable local evidence and
routes findings; it never repairs, deletes, reindexes, or writes WordPress state.

## When To Use

- Audit all Voxel records or registered taxonomy terms rather than one rendered page.
- Resume a large integrity scan after an interruption.
- Produce stable evidence for required values, malformed storage, relation/media
  targets, core/meta contradictions, content-spec drift, or exact duplicate bodies.

## Entry Criteria

1. The target is a local or explicitly authorized environment resolvable by `wpdev`.
2. A writable local checkpoint path and report path are selected.
3. No production mutation is authorized or performed by this workflow.

## Phase 1 — Start Or Resume

**Entry:** Site and local checkpoint/report paths are known; no mutation is authorized.

1. Start a new scan:

   ```bash
   wpdev voxel:integrity <site> \
     --checkpoint /tmp/<site>-voxel-integrity.checkpoint.json \
     --report /tmp/<site>-voxel-integrity.report.json
   ```

2. Resume only the same checkpoint:

   ```bash
   wpdev voxel:integrity <site> \
     --checkpoint /tmp/<site>-voxel-integrity.checkpoint.json \
     --report /tmp/<site>-voxel-integrity.report.json \
     --resume
   ```

3. Confirm the command discovers live Voxel CPT schemas and registered taxonomies,
   sorts scopes deterministically, freezes each scope's initial maximum ID, then
   keyset-pages through `cursor < ID <= boundary`. `--max-pages` may pause a proof run.
4. On resume, require the same site and schema fingerprint. A changed fingerprint
   blocks remaining scopes rather than combining old and new schemas.
5. Record additions above the boundary, updates during the run where available,
   deletions within the boundary, and unsupported term-update detection as drift.

**Exit:** A checkpoint has deterministic frozen scopes and an unchanged schema
contract, or remaining scopes are explicitly blocked.

## Phase 2 — Evidence Contract

**Entry:** A checkpoint has at least one scanned page or an explicit blocked scope.

1. Require a stable fingerprint from scope, entity, rule/version, field path, and
   canonical observed state.
2. Require entity kind/id, source owner, observed digest, bounded excerpt when safe,
   metrics, expected state, confidence, and exactly one `handoffWorkflow`.
3. Keep raw field values in WordPress; the report stores digests and bounded excerpts.
4. Use the Voxel field API for interpreted values. Read raw meta only to prove malformed
   storage or a contradiction with authoritative core/field state.
5. Leave unsupported/custom shapes and read errors blocked. Cluster exact normalized
   long-body signatures deterministically.

**Exit:** Every finding satisfies the evidence contract without exporting raw database
values or guessing unsupported shapes.

## Phase 3 — Coverage And Zero-Write Gate

**Entry:** All intended pages ran or the scan intentionally paused at a checkpoint.

1. Require every scope to be `complete` or explicitly `blocked`.
2. Record scanned/expected coverage and all cursor/boundary values.
3. Keep drift outside the frozen scan population.
4. Prove an unchanged rerun preserves logical fingerprints without duplicates.
5. Capture before/after read-only counts or checksums proving no WordPress writes.

**Exit:** Coverage, drift, resume stability, and zero-write evidence are complete or a
specific missing proof is named as blocked.

## Phase 4 — Exclusive Handoffs

**Entry:** The report satisfies the evidence and coverage contracts.

1. Route each finding using this exclusive map:

   | Finding owner | Receiving workflow |
   |---|---|
   | Field read/schema/custom shape blocked | `workflows/cpt-repair.md` |
   | Required values, core/meta contradictions, relation targets | `workflows/curation.md` |
   | Length metrics needing generation | `workflows/content-generation.md` |
   | Suspected off-topic or duplicate-body content | `workflows/content-review.md` |
   | Confirmed structural orphan proposed for deletion | `workflows/database-cleanup.md` |
   | Page/template/rendered symptom | `workflows/audit.md` |

2. Use the read-only
   [`voxel-integrity-reviewer`](../references/subagents/voxel-integrity-reviewer.md)
   for bounded 5-10-finding batches when evidence sufficiency or ownership is disputed.
3. Require database cleanup to create a backup and pass both confirmation gates. No
   finding, including a confirmed orphan, authorizes deletion by itself.
4. Keep rendered/page evidence with audit; record findings are not layout failures.

**Exit:** Every finding has exactly one receiving workflow or a blocked owner verdict.

## Phase 5 — Verification And Report Gate

**Entry:** Exclusive handoffs are assigned.

1. Verify the report covers every frozen scope or names the blocker.
2. Verify findings are deduplicated and each has one owner/handoff.
3. Verify drift and unsupported detection are explicit.
4. Verify WordPress state is unchanged.
5. Verify every open finding has an active owning workflow or a blocked verdict.

**Exit:** The integrity run is evidence-complete, read-only, resumable, and fully routed.
