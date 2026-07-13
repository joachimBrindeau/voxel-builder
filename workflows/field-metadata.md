# Field Metadata Workflow

Converge editor-facing `description`, `placeholder`, and supported validation limits across one or
all Voxel CPT field definitions, recursively including repeater subfields. Source owner is
`voxel:post_types`; record values remain owned by `curation.md` / content workflows.

## Route boundary

Run for field-definition UX metadata, recursive field constraints, or blueprint/live metadata
convergence. Do not run for CPT creation/registration (`cpt-lifecycle.md`), runtime/template repair
(`cpt-repair.md`), or stored record content (`curation.md`).

Required reads:

- [`../references/voxel/field-metadata-spec.md`](../references/voxel/field-metadata-spec.md) — semantics.
- [`../references/voxel/field-metadata-contract.json`](../references/voxel/field-metadata-contract.json) — machine policy.
- [`../references/voxel/field-metadata-operations.md`](../references/voxel/field-metadata-operations.md) — executable gates/artifacts.
- [`../references/core/command-surface.md`](../references/core/command-surface.md) — exact CLI syntax.

## Hard stops

Halt when site/CPT scope, source owner, rollback, recursive inventory, writer availability, or
verification is unknown. Never raw-write `voxel:post_types`. Top-level fields use
`voxel:field-schema`; repeater subfields use `voxel:settings set`. Unknown types, duplicate keys,
unsafe tightening, partial candidate coverage, skipped dry-runs, or unexpected diffs block mutation.

## Entry criteria

- `wpdev` reaches the site; Voxel and target CPTs exist.
- Mutating run has permission to update field definitions.
- Blueprint ownership is known. Blueprint-managed CPT changes are mirrored into blueprint source
  before live convergence; runtime-only legacy CPTs record missing source ownership as debt.

## Exit criteria

- Exact expected/ready/applied/verified scope counts match recursively.
- Required metadata is complete; supported limit choices are record-safe.
- Authoritative read-back matches manifest; complete diff is intended-only; cache clear passed.
- Rollback artifacts, logs, verification envelope, and any source-debt note remain available.

## Phase 1 — Baseline and classify

**Entry:** Site, CPT scope, and source owner known.

1. Read required references and verify both depth-specific writers from command surface.
2. Create a private unique run directory; capture option, DB, and blueprint/source-owner rollback artifacts per operations reference.
3. Generate arbitrary-depth inventory for fields, repeater descendants, ownership, and nested overrides.
4. Join inventory to machine contract; derive exact canonical-path scopes, exclusions/debt, and required/supported attributes.
5. Block unknown types, duplicate same-depth keys, ambiguous paths, or missing backups.

**Exit:** Immutable baseline, recursive inventory, exact expected scope set, and source-owner status.

## Phase 2 — Author candidates

**Entry:** Expected scopes validated.

1. Dispatch [`voxel-field-metadata-author`](../references/subagents/voxel-field-metadata-author.md)
   using shared batching/retry rules; repeater descendants are independent leaves.
2. Supply surface context, current metadata, required/supported attributes, and limit-safety context.
3. Require one shared `build-material` envelope per `scope_id`; subagents never write WordPress.
4. Re-dispatch missing/blocked scopes through the same session per shared retry limits. Do not use
   `voxel-content-author`, which owns stored record content.

**Exit:** One candidate envelope for every expected scope, or exact blocked scopes/questions.

## Phase 3 — Validate before write

**Entry:** Candidate set covers expected scopes.

1. Run the operations validation gate against inventory, expected scopes, and machine contract.
2. Reject missing/duplicate scopes, type/key mismatches, unsupported/non-scalar patches, nested field
   blobs, unresolved questions, or worker statuses other than `ready`.
3. Require complete live-data extreme evidence before any bound tightening.
4. Validate one complete CPT apply set at a time; no CPT proceeds with an invalid expected scope.

**Exit:** Validated per-CPT apply manifests with scalar patches and tightening evidence only.

## Phase 4 — Dry-run and apply

**Entry:** CPT manifest fully validated.

1. Dry-run every top-level and subfield mutation through its depth-specific sanctioned writer.
2. Resolve every arbitrary-depth path by key immediately before dry-run and apply; never trust stored indices.
3. Use validated identifiers and argv-safe scalar payloads; never shell-evaluate candidate strings.
4. Re-read/hash baseline before each CPT; concurrent drift, skip, duplicate/missing match, unexpected target, or nested patch blocks apply.
5. Apply only after every CPT dry-run passes. On first scalar failure, stop later writes and perform verified rollback.
6. Clear Voxel cache after writes; cache failure blocks completion.

**Exit:** Complete CPT manifests applied with no partial/unexplained scopes and cache result recorded.

## Phase 5 — Verify and close

**Entry:** Writes and cache clear completed.

1. Read live definitions and blueprint source back recursively; compare every scalar and source-owner state.
2. Verify exact scope counts plus separate scalar-mutation count and arbitrary-depth required coverage.
3. Inspect complete live/blueprint diffs; reject every change outside validated manifests.
4. Re-run tightened-bound checks; optionally inspect one representative backend/submit form.
5. On failure, restore and prove baseline equality plus cache clear. Emit `pass`, `rolled-back`,
   `rollback-failed`, or `blocked` with artifact paths and gate results.

**Exit:** Verification envelope is `pass` with all gates green and matching counts, or rollback/blocked
evidence states exactly what remains.
