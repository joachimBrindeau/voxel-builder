# Bounded Atomic Dispatch

Use this contract whenever a Voxel Builder workflow delegates work. Atomicity applies
to the **returned leaf**, not to the number of leaves assigned to a worker.

## Definitions

| Term | Contract |
|---|---|
| Leaf | One independently reviewable widget, section, criterion, URL, entity, or schema question |
| Batch | 5-10 homogeneous, non-overlapping leaves assigned to one named specialist |
| Wave | At most the host concurrency cap of batches; default to four concurrent workers |
| Orchestrator | Selects route, partitions leaves, validates returns, owns gates, and performs centralized writes |
| Worker | Processes one batch in one mode and returns one envelope per leaf |

Batching is a scaling mechanism, not permission to combine evidence. If a worker receives
eight widgets, it returns eight separate widget results. One failed widget does not make
the other seven fail.

## MECE Responsibility Split

| Role | Owns | Must not own |
|---|---|---|
| Main agent | Routing, snapshots, batch plan, reconciliation, write assembly, confirmations, final verification | Deep leaf analysis already assigned to a named specialist |
| `voxel-page-auditor` | Global page context and section/widget inventory | Mutations or widget-level patches |
| `voxel-widget-builder` | Widget leaf analysis or widget JSON, one declared mode per batch | Page-wide judgment or writes to WordPress |
| `voxel-elementor-fixer` | Repair plan and scoped build material for approved findings | Direct concurrent writes to `_elementor_data` |
| `voxel-plan-reviewer` | Criterion-scoped plan findings | Plan edits or implementation patches |
| `voxel-layout-architect` | Section layout-map leaves | Widget content or final tree assembly |
| `voxel-heading-curator` | One production phrasing palette per plan | Section layout or content invention |
| `voxel-schema-detective` | Schema questions with source evidence | Remembered/invented shapes or mutations |
| `voxel-curator-agent` | Entity/relation/user investigation leaves | Database writes or merge/delete approval |
| `voxel-faq-author` | Source-supported FAQ rows per content item | WordPress writes or schema guidance |

## Dispatch Modes

| Mode | Permitted leaf output | Rejected output |
|---|---|---|
| Read-only | Findings and evidence | Patch, mutation command, or write claim |
| Build | Scoped JSON/patch material for orchestrator assembly | Direct shared-state write |
| Plan review | Criterion findings and severity | Plan rewrite or implementation |
| Verification | Pass/fail evidence for one URL/surface | Unverified repair proposal |

Never mix modes inside a batch. Partition by role, mode, and input shape before batching.

## Phase 1 - Partition

**Entry:** The primary workflow, target set, mode, and required return schema are known.

1. Enumerate leaves with stable scope ids such as `widget:<id>`, `section:<cssid>`,
   `url:<canonical>`, or `entity:<post_type>:<id>`.
2. Prove leaves do not overlap. Shared parent context is read-only and may be repeated;
   owned mutation paths may not overlap.
3. Group 5-10 homogeneous leaves per batch. Keep a smaller final batch; never pad with
   unrelated work.
4. Order batches into waves no larger than the host concurrency cap (default four).

**Exit:** Every leaf appears exactly once in a batch; no owned path overlaps; every batch
has one named role, one mode, one schema, and at most 10 leaves.

## Phase 2 - Dispatch

**Entry:** Phase 1 partition passes.

1. Load the matching brief from `references/subagents/`.
2. Send the batch manifest, shared read-only context, applicable criteria, and required
   output envelope. Do not send unrelated workflow history.
3. Run one wave concurrently. Start the next wave only after validating the current wave,
   so malformed returns do not multiply.
4. If the host has no subagent runtime, record `subagent-runtime-unavailable` and process
   the same batches inline. Preserve batch boundaries and output envelopes.

**Exit:** Every dispatched batch has returned, failed explicitly, or been recorded as
blocked; no background session remains unaccounted for.

## Required Leaf Envelope

Each worker returns an array with one object per leaf:

```json
{
  "scope_id": "widget:abc123",
  "mode": "read-only|build|plan-review|verification",
  "status": "pass|finding|ready|blocked",
  "evidence": ["source or command result"],
  "output": {},
  "open_questions": []
}
```

`output` follows the routed brief's schema. Evidence must identify the source, not merely
state that a check ran.

## Phase 3 - Validate And Aggregate

**Entry:** A wave returned leaf envelopes.

1. Reject duplicate/missing scope ids, mixed modes, cross-scope evidence, missing evidence,
   and write claims from read-only roles.
2. Re-dispatch only rejected leaves, at most twice. After three total failed attempts,
   stop that leaf and report the blocking evidence.
3. Merge valid leaves deterministically:
   - build: tree position, then scope id;
   - audit: tier, severity, then scope id;
   - plan review: criterion, severity, then finding id;
   - verification: URL/surface, then assertion.
4. Keep unresolved leaves explicit. Do not convert partial coverage into a pass.

**Exit:** Every leaf is valid, blocked with evidence, or pending a bounded retry; aggregate
coverage equals the Phase 1 manifest.

## Phase 4 - Centralized Write And Verify

**Entry:** All required build leaves validate and the workflow's write gate is open.

1. The orchestrator assembles shared output and performs one authoritative write per
   target record/template.
2. Read the stored value back before starting runtime verification.
3. Dispatch verification in bounded URL/surface batches using different workers from the
   build leaves when the host permits.
4. Re-enter repair only for failed leaf scopes; do not rebuild passing siblings.

**Exit:** Stored state and required runtime surfaces pass, or residual failed leaves are
reported without overstating completion.

## Scaling Rules

- Combine discovery patterns into one search, then filter results before dispatch.
- Never create one worker per file/widget/URL/entity. Use 5-10 leaves per batch.
- Never enqueue an unbounded list. Process waves of at most the host cap, default four.
- Do not split tiny work: one to four simple leaves may run in one batch or inline.
- Keep each batch below the brief's context limit; if a leaf is unusually large, assign it
  alone and record why.

## Rationalizations To Reject

| Rationalization | Why it fails |
|---|---|
| "Worker-per-item fan-out is more atomic" | Atomic evidence does not require one process per item; it creates unbounded fan-out. |
| "The concurrency cap handles everything" | A cap schedules an unbounded queue; batching bounds both queue size and context overhead. |
| "The worker can write its own subtree" | Elementor data is one shared blob; parallel writes race and lose changes. |
| "A batch can return one summary" | Summary output destroys leaf attribution and partial-failure isolation. |
| "Retry until it works" | Unbounded retries hide persistent schema or environment failures. |
