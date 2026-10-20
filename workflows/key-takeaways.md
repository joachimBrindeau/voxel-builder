# Key Takeaways Authoring Workflow

Write or improve the visible summary block above an article: the key-takeaways
list and, when the page earns one, a TL;DR. This workflow produces reader-facing
summary content; it does not produce schema.

## When to Use

- The user asks to write, improve, audit, or regenerate key takeaways, a TL;DR,
  an "in brief" box, or a summary block.
- A Voxel field such as `takeaways` needs content, while the write/apply step
  stays a separate gated action.
- An existing summary block restates topics instead of stating conclusions.

## When NOT to Use

- Bottom-of-page question-and-answer rows - use [`faq-authoring.md`](faq-authoring.md).
- Glossary definition answer blocks - use `../references/voxel/seo-defined-terms.md`.
- Schema-only work, including any attempt to mark up a summary - use
  [`settings.md`](settings.md). Google requires no markup for summary extraction.
- Pages whose body is missing, thin, or under roughly 800 words; fix the body
  first, because a recap cannot substitute for an article.

## Entry Criteria

1. A content source is available: live URL, post ID/site/CPT, rendered HTML,
   Voxel data packet, or pasted source text.
2. The body is complete. A summary block is written from a finished article, not
   from an outline.
3. The target content type is known or inferable (`guide`, `comparison`,
   `round-up`, `data`, `analysis`, `other`) along with target language.

If the body is unfinished, stop and route the body work first.

## Phase 0 - Resolve Source and Owner

**Entry:** Entry criteria met.

**Actions:**

1. Identify the source-of-truth owner: WordPress post content, a Voxel
   `takeaways` repeater, a Voxel body/description field, Elementor static JSON,
   or pasted text.
2. Fetch the full body. For Voxel records use `wpdev voxel:fields <site> <type>`
   and `wpdev voxel:data <site> --id=<id>`; confirm the repeater's subfield key
   before planning any write.
3. Capture the existing summary block, lead paragraph, FAQ rows, and closing
   section without overwriting them.
4. Write a source packet to `/tmp/takeaways-source-<slug>.md` containing: H1,
   content type, body word count, every H2/H3 with its core claim, every cited
   figure with its source, existing lead/TL;DR/FAQ/conclusion text, claims that
   must not be invented, and the target bullet count.

**Exit:** the packet proves the body supports at least three distinct
conclusions; the field owner and its subfield key are known.

## Phase 1 - Load Standards and SEO Methodology

**Entry:** Phase 0 packet exists.

**Actions:**

1. Read [`../references/voxel/key-takeaways-authoring.md`](../references/voxel/key-takeaways-authoring.md).
2. Apply [`../references/voxel/claude-seo-authoring.md`](../references/voxel/claude-seo-authoring.md)
   because summary blocks are reader- and SERP-facing copy. Use the Read
   fallback for upstream claude-seo methodology and never claim a tool ran when
   it did not.
3. Treat the `Summary blocks (TL;DR and key takeaways) meet SEO and AI-citation
   criteria` branch of `docs/seo-checklist.db` as the checklist source. Use its
   writing and placement rules only; ignore schema and rich-result criteria.

**Exit:** the gates are loaded: conclusion-not-topic, standalone bullets,
specificity, qualifiers, body support, counts, word bands, and placement.

## Phase 2 - Conclusion Inventory and Element Decision

**Entry:** Phase 1 standards loaded.

**Actions:**

1. List every distinct conclusion the body proves, each with the heading,
   sentence, figure, or source that supports it.
2. Drop conclusions that duplicate the H1, the lead, an FAQ answer, or the
   closing synthesis.
3. Decide the element using the page-type fit table: key takeaways, TL;DR plus
   key takeaways, TL;DR only, or neither.
4. If the decision is "neither", stop and report why, naming the rule that
   excluded the block. Do not manufacture a summary to fill a field.
5. Select the final candidate set, normally 3-5 conclusions, and record rejected
   candidates with reasons.

**Exit:** a candidate list with per-item evidence, a stated element decision, and
a rejection log.

## Phase 3 - Author the Block

**Entry:** Phase 2 candidate list complete.

**Actions:**

1. Partition 5-10 homogeneous content items per `voxel-takeaways-author` batch
   and run bounded waves through
   [`../references/core/parallel-dispatch.md`](../references/core/parallel-dispatch.md).
2. Pass each item a stable scope id, the source packet, the candidate list,
   target language, content type, target bullet count, whether a TL;DR is
   requested, and the writing standard.
3. Require one leaf envelope per content item using the output shape in
   `key-takeaways-authoring.md`: `tldr`, `takeaways`, `rejected_candidates`,
   and `qa_notes`.

**Exit:** candidate bullets and any TL;DR exist with evidence and word counts.

## Phase 4 - QA and Revision Gate

**Entry:** Phase 3 rows returned.

**Actions:**

1. Validate every row against the QA gate in `key-takeaways-authoring.md`.
2. Enforce counts and bands: 3-5 bullets, 12-30 words each with 35 as the hard
   maximum, and a TL;DR of 2-4 sentences within 40-100 words.
3. Run the isolation test on each bullet: read it with no surrounding text and
   confirm it delivers a specific conclusion rather than a teaser.
4. Run the duplication test: no bullet may share wording with the TL;DR, the
   lead, an FAQ answer, or the closing section.
5. Revise or reject any `needs-source` or `reject` row. Never invent a figure,
   date, comparison, or outcome to rescue a weak bullet.

**Exit:** every remaining row is `supported`, standalone, non-duplicative, and
inside its word band.

## Phase 5 - Output or Apply

**Entry:** Phase 4 passed.

**Actions:**

1. Default output: the takeaways table plus, when useful, a Voxel
   repeater-ready JSON array shaped to the field's real subfield key, one row
   per bullet.
2. If the user asked to write to the site, enter [`curation.md`](curation.md)
   for the mutation. The orchestrator writes once after backup and read-back
   gates; the `voxel-takeaways-author` subagent never writes.
3. If the block needs a rendering surface in an Elementor template, enter
   [`build.md`](build.md) after the content is approved, and bind the block
   above the body so it falls inside the first 150 words as rendered.

**Exit:** content is delivered, or a separate write workflow is routed with the
source owner and rollback plan known.

## Phase 6 - Verification

**Entry:** Rows delivered or written.

**Actions:**

1. Static verification: re-run the Phase 4 QA gate on the final output.
2. If written to WordPress/Voxel, read back the stored repeater with
   `wpdev voxel:data <site> --id=<id>` and confirm row-by-row equality plus one
   bullet per row.
3. If rendered on a page, apply the browser verification pattern from
   [`build.md`](build.md) Phase 6: screenshot, rendered text, block position
   above the body, no tag leakage, no console or page errors.
4. Confirm rendered placement: the block's text falls inside the first 150 words
   of the page and precedes the first substantive H2.
5. Record deferred verification when the page is not live yet; never mark it
   done.

**Exit:** the final block is statically validated, or live-verified with
read-back and placement proof.

## Output Contract

Return:

1. Source: page/post/content item, owner field, and subfield key.
2. Element decision: takeaways, TL;DR, both, or neither, with the deciding rule.
3. Rows: position, takeaway, conclusion type, evidence, word count.
4. TL;DR when produced: text, sentence count, word count, evidence.
5. Rejected candidates: candidate and reason.
6. QA result: pass/fail against each gate.
7. Apply status: not requested, deferred, or verified write with read-back and
   placement proof.
