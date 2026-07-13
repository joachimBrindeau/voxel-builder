# Field-metadata operations

Executable runbook for [`../../workflows/field-metadata.md`](../../workflows/field-metadata.md).
Semantic policy lives in [`field-metadata-spec.md`](field-metadata-spec.md); machine support policy
lives in [`field-metadata-contract.json`](field-metadata-contract.json); exact CLI spellings live in
[`../core/command-surface.md`](../core/command-surface.md).

## Artifact contract

Create a private unique run directory with `mktemp -d`, verify it is owned by the current user,
not a symlink, and mode `0700`; refuse predictable/reused paths. Keep every artifact inside it so
gates are auditable and rollback survives partial failure:

```text
${RUN_DIR}/
  run.json
  before-option.json
  before-option.sha256
  before-db.sql
  source-owner.json
  blueprints/<cpt>/before.json
  blueprints/<cpt>/after.json
  blueprints/<cpt>/blueprint.diff
  inventory.json
  expected-scopes.json
  candidates.json
  validated.json
  dry-run.json
  apply.json
  after-option.json
  option.diff
  verification.json
```

`run.json` is exact: `{\"version\":1,\"nonce\":\"<32 lowercase hex>\",\"created_at\":\"<UTC ISO-8601>\",\"path\":\"<resolved RUN_DIR>\",\"site\":\"<wpdev site>\",\"uid\":<uid>,\"mode\":\"0700\",\"device\":<st_dev>,\"inode\":<st_ino>}`. Generate nonce with `secrets.token_hex(16)` when directory is created. Validator requires timestamp within 24 hours and matching path/owner/mode/device/inode; reused or copied proof rejects. Every consumed artifact must be current-user-owned, regular, non-symlink, single-link (`st_nlink == 1`), inside run directory, and mode `0600` or stricter. Checks reduce replacement risk but do not claim impossible TOCTOU elimination; immutable baseline hashes and opened-file metadata remain proof.

A mutating run halts when any required backup/source snapshot fails. On malformed option data,
unexpected changes, incomplete CPT application, read-back mismatch, record-safety failure, or first
failed scalar write: stop all later CPTs and restore. After restore, read option/blueprint back, compare
them byte-for-byte to baseline, clear cache, and record proof. Unproven recovery is
`rollback-failed`, never `rolled-back`. Cache failure blocks completion and triggers retry/diagnosis;
it does not by itself justify restoring otherwise-correct definitions.

## Source-owner convergence

Record one state per CPT in `source-owner.json`: `blueprint-managed`, `runtime-only-debt`, or
`not-applicable`. For blueprint-managed CPTs, snapshot the blueprint, apply metadata changes to that
source first through its owning lifecycle mechanism, and record per-CPT `before_artifact`,
`after_artifact`, and complete `diff_artifact` paths under `blueprints/<cpt>/`. Live apply then
converges runtime to blueprint.
Verification fails if complete per-CPT blueprint read-back differs from intended source or complete blueprint/live CPT definitions diverge; patched-scalar equality alone is insufficient.
Runtime-only legacy CPTs may patch live registry but must retain an explicit debt item and source path
absence; never fabricate a blueprint.

## Inventory and expected scopes

1. Read `voxel:post_types` once into `before-option.json`, hash it, and export the DB.
2. Normalize every target field at arbitrary repeater depth into `inventory.json`. Each row contains
   `cpt`, JSON-array `field_path`, `key`, `type`, `label`, ownership (`user-input`, `system-derived`,
   `presentational`, `runtime-aggregate`), current metadata, overrides, and current numeric path.
3. Treat numeric paths as evidence only. Resolve every nested segment by key again immediately before
   dry-run and apply. Duplicate keys at any traversed depth block the scope.
4. Join inventory rows to `field-metadata-contract.json`. Exclude row/type/key system rules. Inventory
   `overrides[].model_overrides` recursively but report them as excluded definition debt unless a
   blueprint/source-owner route handles the nested object; base convergence never silently claims
   override convergence. Produce one expected scope per included path:

`field_path` is canonical identity. Build `scope_id` as
`field-definition:<cpt>:<sha256(canonical-json(field_path))>`; never concatenate dotted keys, which
can collide.

```json
{
  "scope_id": "field-definition:company:<path-sha256>",
  "cpt": "company",
  "field_path": ["faq", "question"],
  "field_type": "text",
  "required": ["description", "placeholder"],
  "supported": ["description", "placeholder", "minlength", "maxlength", "pattern"],
  "missing": ["description"]
}
```

Unknown types, duplicate keys at the same depth, or ambiguous repeater paths block the scope.

## Candidate validation gate

Run `python3 scripts/validate-field-metadata-run.py "$RUN_DIR" --phase prewrite` before any write and
`--phase final` after verification. It validates candidates against inventory, expected scopes,
machine contract, source ownership, and (final phase) gate artifacts. Validation fails nonzero for:

- missing/duplicate/unexpected `scope_id`, or missing expected output;
- envelope mode other than `build-material`, status other than `ready`, or unmatched input/output;
- unknown CPT, field, subfield, or type mismatch;
- unsupported patch attribute or non-scalar patch value;
- nested `fields`/`subfields` inside a patch;
- missing required metadata candidate;
- tightened bound without safe-extreme evidence;
- a blocked scope or unresolved open question.

Candidate envelope and `output` shapes are exact; extra or missing keys reject. A ready envelope has exactly `scope_id`, `mode`, `status`, `evidence`, `output`, and `open_questions`; `open_questions` is empty. Each optional general evidence row is exactly `{"claim":"…","artifact":"relative/path.json"}`. Artifact is exact JSON object `{"scope_id":"<same candidate scope_id>","claim":"<same evidence claim>"}`; both values must byte-for-value match row semantics. Its regular non-symlink file must resolve inside private run directory. This minimum binding prevents unrelated existing files from satisfying candidate proof.

Candidate `output` shape is exact:

```json
{
  "field_path": ["faq", "question"],
  "field_key": "question",
  "field_type": "text",
  "patch": {"description":"…"},
  "preserved": ["maxlength"],
  "tightening_evidence": {
    "maxlength": {"previous":240,"proposed":160,"observed_extreme":148,"result":"safe","artifact":"record-extremes.json"}
  }
}
```

`patch` scalar types must match attribute families: prose/pattern strings; integer/number limits;
`null` only when contract explicitly permits removal. Empty ready patches require all required values
to be present and listed in `preserved`. Blocked envelopes use empty `patch`, `status:blocked`, and one
precise `open_questions` item.

No CPT applies until its complete expected scope set validates. Retain valid leaves for retry, but
re-dispatch failed scopes through the same metadata-author session (maximum two retries). Count units:
`expected`, `ready`, `applied`, and `verified` count field-path scopes; `scalar_mutations` separately
counts attribute writes.

## Record-safety evidence

Before tightening a bound, inspect all existing values for the relevant storage family:

- text/editor/title/excerpt: maximum character count;
- repeater: maximum row count and bounded subfield lengths;
- relation: maximum related-record count;
- image/file: maximum attachment count;
- numeric: observed minimum/maximum and required step compatibility.

Attach evidence under `output.tightening_evidence.<attribute>`. Every new bound is tightening unless existing bound proves proposal is no more restrictive. Upper/lower evidence has exactly `previous` (number or null), `proposed`, `observed_extreme`, `result`, and `artifact`; computed safety requires maximum `<= proposed` for upper bounds and minimum `>= proposed` for lower bounds. Step evidence has exactly `previous`, `proposed`, `observed_min`, `observed_max`, `incompatible_count`, `result`, and `artifact`; safety requires positive proposed step, ordered observed range, and zero incompatible stored values. Validator derives `result`; self-attested `safe` cannot override arithmetic.

Unknown storage shape or an extreme beyond the proposed bound blocks tightening. Preserve the current
bound or route record-value repair through `curation.md`; never truncate silently.

## Dry-run and apply

Use the depth-specific writers documented in `command-surface.md`:

- Top-level field: `voxel:field-schema`, scoped to one CPT/key, update-only, scalar metadata patch.
- Repeater subfield: `voxel:settings set`, one scalar attribute path per write.

Rules:

1. Validate site/CPT/field keys against live allowed identifiers before invocation. Pass commands as
   argument arrays (no `eval`, command strings, or interpolation of candidate values); encode JSON
   scalars in files/argv-safe values.
2. Resolve every arbitrary-depth nested path segment by key before dry-run and again before apply.
3. Dry-run every mutation. Any skip, missing/duplicate match, or unexpected target blocks the CPT.
4. Immediately before CPT apply, re-read/hash the option and compare untouched baseline regions plus
   exact key/type/path identity. Concurrent drift blocks apply and requires re-inventory.
5. Apply only after all CPT dry-runs pass; centralize writes. On first failed/mismatched scalar write,
   stop later writes/CPTs and execute verified rollback.
6. Write structured journals, not free-text claims: each `dry-run.json` mutation row has exactly
   `{mutation_id,status:"pass",writer,argv}` and each `apply.json` mutation row has exactly
   `{mutation_id,status:"applied",writer,argv}`. `argv` must exactly equal one derived sanctioned invocation, including recorded `run.site`, exact CPT/key or resolved numeric nested path, one scalar patch/value, update-only flag, and phase flag. Extra, duplicate, conflicting, alternate-target, unrelated-operation, or shell-like argv rejects. Writer must be `voxel:field-schema` at depth one and `voxel:settings set` below repeaters. `apply.json` also has one CPT row containing its canonical pre-apply
   snapshot artifact and hash. Never write `voxel:post_types` through raw option update, `wp eval`,
   or SQL.

## Read-back, diff, and verification

1. Clear Voxel cache and record the result.
2. Read the authoritative option recursively into `after-option.json`.
3. Compare every validated scalar against read-back; verify every expected scope exactly once.
4. Generate and inspect the **complete** canonical sorted option diff as a JSON unified diff. Human excerpts may be short, but validator recomputes and byte-compares full `option.diff` and every blueprint `diff_artifact`; never truncate gate with `head`.
5. Reject any changed attribute outside the validated manifest.
6. Re-run every tightened-bound safety check.
7. When possible, inspect one representative backend/submit form and confirm help text, placeholder,
   and browser validation render.

`verification.json` records:

```json
{
  "status": "pass|rolled-back|rollback-failed|blocked",
  "source_owner": {"state":"blueprint-managed|runtime-only-debt|not-applicable","path":"","read_back":"pass|fail|debt"},
  "counts": {"expected":0,"ready":0,"applied":0,"verified":0,"scalar_mutations":0},
  "gates": {
    "coverage":"pass",
    "attribute_support":"pass",
    "key_existence":"pass",
    "dry_run":"pass",
    "read_back":"pass",
    "diff_clean":"pass",
    "record_safety":"pass",
    "cache":"pass",
    "rollback":"not-needed|pass|fail"
  },
  "blocked_scopes": [],
  "open_questions": []
}
```

Source-owner rows are exact `{cpt,state,read_back}`. For `status:pass`, `blueprint-managed` and `not-applicable` require `read_back:pass`; `runtime-only-debt` requires `read_back:debt`.

Rollback payload is exact `{restored_option_artifact,restored_blueprints,cache_clear}`; `restored_blueprints` keys exactly equal blueprint-managed CPTs and `cache_clear` is `pass|fail`. Only `status:pass` with matching expected/ready/applied/verified scope counts, required source-owner read-back, and every gate green is complete.
