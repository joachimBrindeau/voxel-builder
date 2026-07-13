# Field-metadata semantics

Human authoring policy for editor-facing Voxel CPT field definitions. Machine support/coverage policy
lives in [`field-metadata-contract.json`](field-metadata-contract.json); operational mechanics live in
[`field-metadata-operations.md`](field-metadata-operations.md).

Field metadata is not record content:

- `description`: helper text under a field.
- `placeholder`: example/hint inside an empty input.
- limits: `minlength`/`maxlength`, `min`/`max`/`step`, `max-count`, `max-size`, `max_count`, or `max_date_count`.

Source owner is the Voxel field-definition registry (`voxel:post_types`). Depth-specific sanctioned
writers are `voxel:field-schema` for top-level fields and `voxel:settings set` for repeater subfields;
exact syntax belongs to [`../core/command-surface.md`](../core/command-surface.md).

## Support policy

Do not reproduce a hand-maintained support table in prose. Read the machine contract. Its row for each
field type declares:

- whether description/placeholder is required, optional, or unsupported;
- supported limit keys;
- whether the type is skipped;
- whether nested subfields are recursively scoped.

Important invariants: relation limits use `max_count`; image/file counts use `max-count` and upload
size uses `max-size`; recurring dates use `max_date_count`. Repeater subfields at every nesting depth
are classified by their own type. `profile-avatar` count is fixed at one, so only its description and
`max-size` are authorable. Unknown types block mutation until source inspection confirms support.

## Description

- One concise sentence (about 160 characters maximum).
- Tell the editor what belongs in the field and why it matters to display, search, matching, or data
  quality; do not restate the label.
- Name the concrete surface when known: H1, card blurb, SERP excerpt, relation, filter, or schema.
- Mention an important bound in plain language when useful.
- Neutral and factual. No marketing filler or invented entity facts.

## Placeholder

- Give a realistic example value, not an instruction. Good: `e.g. Ceremonial-grade matcha from Uji`.
  Bad: `Enter the description`.
- Taxonomy/relation inputs may use a selection hint such as `Select one or more…`.
- Do not duplicate label or description.
- Never author a placeholder for a type marked unsupported by the contract.

## Limits

Set a limit only when the field has a real domain/display constraint:

- Text/title/excerpt/editor/profile-name: use the true surface ceiling. Useful anchors: title/H1
  60–70, meta/excerpt 120–160, tagline about 90, short label up to 140. Body fields use a justified
  high ceiling or none.
- Number: domain `min`/`max`/`step` (for example rating 0–5 step 0.5, price min 0).
- Taxonomy: allowed term count.
- Relation: allowed related-record count.
- Image/file: attachment count and upload-size ceiling; MIME allowlists are excluded non-scalar config.
- Recurring date: allowed occurrence count.
- Repeater: allowed row count; classify nested fields recursively at arbitrary depth.

Supported does not mean required. Preserve sensible existing bounds. Tightening requires complete
live-data extreme evidence for the storage family; unknown storage or an observed value beyond the
proposal blocks tightening. Record repair belongs to `curation.md`, not this workflow.

## Exclusions and ownership

- Non-scalar `allowed-types` MIME lists are blueprint/admin configuration, not scalar metadata output.
- Role/plan `overrides[].model_overrides` are inventoried and reported as definition debt; this scalar
  workflow does not silently claim or mutate nested override convergence.
- Presentational fields and runtime aggregates follow machine skip policy.
- Hidden derived hierarchy relations are system-owned instances; do not require editor help text.
- User-facing profile fields remain in scope even when keys begin with `voxel:`.

## Candidate quality contract

A ready metadata-author leaf:

1. Covers every required missing attribute in its expected scope.
2. Uses only scalar attributes supported by the machine contract.
3. Targets one live field/subfield path with matching type.
4. Contains no record value, command, whole-field object, or nested `fields` array.
5. Carries rationale and safe-extreme evidence for every tightened bound.
6. Preserves already-proper metadata rather than rewriting it without benefit.

## Completion contract

A run passes only when:

1. Required descriptions and placeholders cover every in-scope top-level field and repeater subfield.
2. Selected limits use supported keys and live values still satisfy tightened bounds.
3. Authoritative recursive read-back equals the validated manifest.
4. Complete diff contains only intended scalar metadata changes.
5. Cache clear succeeds and rollback artifacts remain available.
