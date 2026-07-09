# Bulk rich-text reformatting — Voxel `texteditor` fields

Turn bulky single-`<p>` plaintext into readable rich text (intro `<p>` → `<ul><li>` steps →
closing `<p>`) across **many records at once**, without inventing, dropping, or corrupting
content. This is a specialised **Edit route** of the [curation workflow](../../workflows/curation.md):
same Discover → Plan → Execute → Verify spine, but fanned out over N records with a
**pre-write QA gate** instead of per-record eyeballing.

Use it when a `texteditor` (rich-text) field across a CPT holds one fat paragraph that should
be a scannable list, **and** a sibling field already demonstrates the house rich-text format.

## When NOT to use it

Reformatting is content-destructive if applied to prose that is meant to stay prose. **Do not
listify:**

- Testimonials / customer quotes (narrative voice — check the field's records, not just its label).
- Short definitions ("Définition courte" / summary fields — intentionally compact).
- Biographical narrative (profile `role` / `experience` / `education`, author bios).

Gate every candidate field by **reading real records**, not the field label. One field can be
rich-text-typed yet hold prose that must not be bulleted. When a key like `content` /
`description` spans several post types with different intent, confirm which CPT you're touching
before deciding:

```sql
SELECT p.post_type, COUNT(*) FROM wp_postmeta m JOIN wp_posts p ON p.ID=m.post_id
WHERE m.meta_key='<field>' GROUP BY p.post_type;
```

## Phase 1 — Discover the work set (evidence, not assumption)

1. Enumerate rich-text fields on the CPT and their fill state:
   ```bash
   wpdev voxel:fields <site> <post_type>        # find texteditor-typed fields
   wpdev voxel:sample <site> <post_type> --limit=3
   ```
2. Quantify plain vs already-rich directly in the DB (fast, exact):
   ```bash
   # already-rich (has a list)
   wpdev wp <site> db query "SELECT COUNT(*) FROM wp_postmeta
     WHERE meta_key='<field>' AND meta_value LIKE '%<ul%';" --skip-column-names
   # bulky plain (non-empty, no list)
   wpdev wp <site> db query "SELECT COUNT(*) FROM wp_postmeta
     WHERE meta_key='<field>' AND meta_value<>''
       AND NOT (meta_value LIKE '%<ul%' OR meta_value LIKE '%<li%');" --skip-column-names
   ```
3. **Learn the target format from a sibling, don't invent one.** If `<field>` has sibling
   rich fields already in the house style (e.g. a `-problem`/`-stakes` pair next to a
   `-solution`), sample one and copy its exact tag vocabulary:
   ```bash
   wpdev wp <site> db query "SELECT meta_value FROM wp_postmeta
     WHERE post_id=<rich_id> AND meta_key='<sibling_field>';" --skip-column-names
   ```
   Typical house format observed: intro `<p>` → `<ul><li>` steps → closing `<p>` with `<b>`
   emphasis; **`<b>` not `<strong>`; no `<h2>/<h3>` inside the field; no classes/attributes.**
   Confirm against the actual sibling — house rules differ per site.

## Phase 2 — Extract cleanly (the TSV/base64 pitfall)

`texteditor` meta values contain HTML with embedded newlines, tabs, and apostrophes. Naïve
multi-key TSV dumps **silently corrupt or drop rows** — a value with an embedded tab shifts
columns and the record reads back empty.

**Rules:**
- Pull **one meta_key per query** (never a mixed-key TSV).
- For values that may contain control chars, wrap the read in **base64** and decode in the
  processor:
  ```bash
  wpdev wp <site> db query "SELECT meta_value FROM wp_postmeta
    WHERE post_id=<id> AND meta_key='<field>';" --skip-column-names | base64 > /tmp/raw_<id>.b64
  ```
- Also pull context the reformatter needs (page `h1`, the sibling reference field) so bullets
  stay on-topic.
- **After extraction, assert non-empty.** Any record whose extracted source is empty but whose
  DB value is non-empty was eaten by a parse bug — re-pull it via base64. (This is exactly the
  class of silent skip the Verify phase must re-catch.)

## Phase 3 — Reformat in batch (threaded, validated, retried)

For many French/EN records, a local OpenAI-compatible endpoint (batchable, free) beats N
one-shot subagents. Drive it from a script, not by hand.

**Strict system prompt (do not weaken):**
- Reformat ONLY — invent nothing, drop nothing; reuse the source's own sentences/facts.
- Target: one intro `<p>`, one `<ul>` of 3–6 `<li>` steps, one closing `<p>`; `<b>` on 1–3
  existing key terms max.
- Allowed tags **only**: `<p> <ul> <li> <b>` (+ preserve existing `<a href>`). No `<h2>/<h3>`,
  no attributes/classes.
- Keep **grammatically complete** target-language prose — keep articles/prepositions; do not
  telegraph ("dans la procédure", not "dans procédure").
- Compact HTML: no newlines/whitespace between tags. Output HTML only, no code fences, no commentary.

**Runner shape** (thread pool ~6 workers; per-record retry loop up to ~4 attempts feeding the
validation failure back into the prompt):
- If the endpoint streams SSE, concatenate `delta.content`; strip any `<think>…</think>` and
  ``` fences.
- Persist results to a JSON map `{post_id: html}` so Phase 4 can audit before any write.
- Sequential is too slow (~6 s/record blows a 5-min sandbox cap). Run threaded, and for large
  sets run it as a **background terminal job** (not a 300 s-capped code sandbox).

## Phase 4 — QA gate (run BEFORE writing a single record)

Machine-check all candidates; regenerate failures. Do not write until every record passes:

| Check | Rule | On fail |
|---|---|---|
| Format | starts `<p>`, exactly one `<ul>`, 3–6 `<li>`, a closing `<p>` after `</ul>`, all `<p>/<ul>/<li>/<b>` balanced, no `<h2>/<h3>/div/span/class/style` | regenerate |
| Fidelity | word-set(after) − word-set(before) ≤ ~4 new tokens (only connectors) | regenerate — flags invented facts |
| Links | `href` set identical before/after | regenerate |
| No dropped content | plaintext length(after) ≥ ~55% of before | regenerate |
| Grammar (telegraphic) | article density (le/la/les/un/une/des/du per word) ≥ ~0.55× source | regenerate with "garde un français grammaticalement complet" |

The grammar/article-density check is essential: strict "invent nothing" prompts push models
into telegraphic style that reads badly. Regenerate those with an explicit
keep-full-grammar instruction.

## Phase 5 — Write back (PATH + quoting hazards)

- Write via `wpdev voxel:set-field <site> --id=<id> --set='<json>'`, one record per call
  (it reindexes per record). Batch many as a **background** job.
- **HTML apostrophes/quotes break inline shell quoting.** Write each payload to a file and
  interpolate the file, or feed from the script:
  ```bash
  ./wpdev voxel:set-field <site> --id=<id> --set="$(cat /tmp/payload_<id>.json)"
  ```
- **`bun`/`wpdev` is often NOT on PATH inside the code-sandbox subprocess** (only in the real
  terminal). Run the actual writes through the terminal tool / a bash background job, not the
  Python code sandbox.
- Count `Updated #<id>` successes; record fails.

## Phase 6 — Verify (re-scan the DB, don't trust the write log)

1. Re-run the Phase-1 plain-vs-rich counts. **Plain must be 0** for the reformatted field.
   If it isn't, the leftover IDs are usually the base64-skip victims from Phase 2 — extract,
   reformat, write, re-verify.
2. `wpdev voxel:status <site>` — the CPT stays fully indexed (published == indexed, 0 missing).
3. Purge caches so rendered pages reflect the change:
   ```bash
   wpdev voxel:cache <site> clear
   wpdev wp <site> litespeed-purge all
   ```
4. Fetch one live URL and confirm the list renders (grep for a reformatted `<li>` phrase or
   count `<ul>`), via `agent-browser` or `curl -sk "$(wpdev wp <site> eval 'echo get_permalink(<id>);')"`.

## Mistake guards

- Learn the format from a sibling field; never invent the house tag vocabulary.
- Gate candidates by reading records, not field labels — prose fields must stay prose.
- Extract per-key + base64; assert non-empty; a "plain count > 0" after writing means silent skips.
- QA gate (format + fidelity + links + no-drop + grammar) runs before any write, not after.
- Writes go through the terminal (PATH), payloads via files (quoting), never inline HTML in `--set`.

## Reference index

| Need | File |
|---|---|
| Curation spine (Discover→Plan→Execute→Verify) | [`../../workflows/curation.md`](../../workflows/curation.md) |
| Commands | [`cli-map.md`](cli-map.md) |
| Field semantics (which fields are prose vs list) | [`field-semantics.md`](field-semantics.md) |
| Verify render / screenshot | [`../verification/browser.md`](../verification/browser.md) |
