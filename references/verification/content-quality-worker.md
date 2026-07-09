# Content Quality Worker Checklist

Use for delegated per-record review during Voxel content surgery or a full-corpus quality audit. The worker edits one record or one small batch and must preserve source-of-truth boundaries.

## Inputs

- Written quality standard.
- Record packet with ID, post type, URL, title/H1/excerpt/body/source metas, and any baseline/source-of-intent snippets.
- Exact write helper or command contract for core fields and Voxel meta fields.

## Procedure

1. Read the standard, packet, and exact write contract.
2. Fetch exact live bytes for each surface before editing; packet summaries can be truncated.
3. Decide per surface:
   - `CORRIGÉ` when grammar, meaning, SEO, typography convention, or corruption requires an edit.
   - `CONSERVÉ` when the live text is grammatical and the change from baseline is voluntary or out of scope.
4. Edit the smallest source surface: core title/excerpt/content, Voxel field meta, or Elementor static JSON. Do not edit generated markdown, rendered HTML, or cached output as source.
5. For JSON/repeater fields, parse -> mutate values -> serialize -> parse again before writing.
6. Write only changed fields and confirm the read-back equals the intended value.
7. Report a compact table: surface, decision, before -> after for corrections, verification status.

## Safety Rules

- Never bulk-copy baseline over current live content.
- Never edit off a truncated packet string.
- Preserve measured site typographic conventions; do not introduce non-breaking spaces unless the corpus uses them.
- Restore missing nouns/adjectives when the live phrase is grammatically broken or semantically damaged.
- Keep voluntary rewrites when they still read well and preserve intent.
- Ignore packet artifacts that are just fragments of a multiline field; fetch the real field key.

## Verification

- Every write must have read-back equality.
- JSON fields must round-trip with `json.loads` or equivalent.
- Residual corruption regexes should be zero or explained false positives.
- Live URL check is required for rendered-page tasks.
