# Content Review Workflow

Audit existing Voxel CPT field content — `definition`, `h1`, `hook`,
`post_excerpt`, `sources`, `faq`, body/`description` — against the
**field-scoped spec**, and report per-field, per-record verdicts with evidence.
This workflow is read-only: it produces findings and a fix list, never writes.

## When to Use

- The user asks to review, audit, QA, or score field content quality (one record
  or a whole CPT) before or after a generation pass.
- A backfill claims "done" and the fill/quality must be proven per field.
- Deciding which records need regeneration vs human sourcing.

## When NOT to Use

- Generating or fixing the content itself - use
  [`content-generation.md`](content-generation.md).
- Auditing or populating entity-equivalence links - use
  [`identity-linking.md`](identity-linking.md).
- Rendered-page/layout audit of Elementor data - use [`audit.md`](audit.md).
- Schema JSON-LD validity only - use the lean-seo/schema route.

## Entry Criteria

1. Site, target CPT, target field(s), and record scope are known.
2. `wpdev voxel:fields` + `wpdev voxel:data` can read the CPT and records.
3. The field-scoped reference for each field (same routing table as
   [`content-generation.md`](content-generation.md) Phase 0) is available.

## Phase 0 - Resolve Field Scope and Spec

**Entry:** Entry criteria met.

**Actions:**

1. Read the field-scoped reference for each target field (definition/h1/hook/
   sources → [`../references/voxel/seo-defined-terms.md`](../references/voxel/seo-defined-terms.md);
   `faq` → [`../references/voxel/faq-authoring.md`](../references/voxel/faq-authoring.md);
   excerpt/meta → [`../references/voxel/lean-seo-excerpt-meta-descriptions.md`](../references/voxel/lean-seo-excerpt-meta-descriptions.md)).
2. Extract each field's machine-checkable acceptance spec: length band, opening
   form, prose rules, source-verification rule, forbidden mechanical transforms.
3. Resolve the field's write owner (for the fix list handoff) via
   `wpdev voxel:fields`.

**Exit:** a per-field acceptance spec and owner map exist.

## Phase 1 - Collect Current State

**Entry:** acceptance spec ready.

**Actions:**

1. Read every in-scope record with `wpdev voxel:data --id=<id>` (or a bulk read),
   plus `post_excerpt`/`post_title` core columns where relevant.
2. Compute deterministic metrics per field: fill (empty/present), length/word
   count vs band, opening-form match, truncation markers, tag/token leakage, and
   for `sources` whether each URL is present and resolves.
3. Flag likely mechanical-transform artifacts (e.g. `hook` equals
   `strip_tags(definition)`; `excerpt` equals a `substr` of the body).

**Exit:** a metrics table per record+field exists.

## Phase 2 - Judge Against Spec

**Entry:** metrics collected.

**Actions:**

1. For subjective gates that metrics cannot decide (dictionary-neutral prose,
   information gain, source relevance), dispatch the read-only
   [`../references/subagents/voxel-content-author.md`](../references/subagents/voxel-content-author.md)
   brief in review mode (or read-fallback), 5-10 records per batch, returning a
   verdict + evidence per record; a reviewer never writes.
2. Assign each record+field a verdict: `pass`, `off-spec:<reason>`,
   `thin`, `needs-source`, or `mechanical-transform`.
3. Keep verdicts independently attributable; one bad record does not fail its siblings.

**Exit:** every record+field carries a verdict with evidence.

## Phase 3 - Report and Gate

**Entry:** verdicts assigned.

**Actions:**

1. Report per-field coverage (`pass/total`), the off-spec breakdown by reason, and
   the exact record ids per bucket.
2. Produce a fix list mapping each failing record+field to the owning write path,
   ready to hand to [`content-generation.md`](content-generation.md) (regenerate)
   or to a human (`needs-source`).
3. State the gate result: `green` only when every in-scope record+field is `pass`;
   otherwise `open` with the failing set. Do not report a pass from fill alone —
   a filled but off-spec field is a fail.

**Exit:** a per-field verdict report and a routed fix list exist; the gate is
green or explicitly open with the failing records named.
