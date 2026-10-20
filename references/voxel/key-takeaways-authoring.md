# Key Takeaways Authoring Standard

Visible summary-block content only: the TL;DR paragraph and the key-takeaways
list that sit above an article. This reference excludes schema, rich results,
and JSON-LD; Google requires no markup for a summary block to be extracted.

## Element Contract

| Element | Job | Shape |
|---|---|---|
| TL;DR | Answers the head query so the reader can decide whether to continue | 2-4 sentences, 40-100 words, read as one unit |
| Key takeaways | Lets a reader or an AI system scan and cite one discrete conclusion | 3-5 bullets, each independently useful |
| Closing synthesis | Adds implications after the evidence has been read | Prose, never a second bullet list |

One claim gets one primary home. If a direct answer already states the page's
only conclusion, omit the takeaways. If takeaways carry distinct findings, keep
the direct answer focused and do not reuse its wording in bullet one.

## Checklist-Derived Rules

Distilled from the `Summary blocks (TL;DR and key takeaways) meet SEO and
AI-citation criteria` branch of `docs/seo-checklist.db`.

- **Conclusion, not topic.** Every bullet states a supported finding. "This guide
  covers three pricing models" is an overview; "Tencha auction prices rose 170%
  year on year in May 2025" is a takeaway.
- **Standalone.** Each bullet stays accurate and understandable when quoted
  without the box, heading, or surrounding paragraph. No "as mentioned above",
  "in this article", or "below we explain".
- **Specific.** Each bullet carries the page's real number, framework,
  comparison, or verdict rather than a vague preview.
- **Qualified.** Include the smallest qualifier needed for accuracy: audience,
  period, condition, measurement, denominator, or exception.
- **Supported.** The body visibly supports every number, comparison, scope, and
  recommendation in the block. Remove a bullet the body cannot prove; hedging
  does not repair weak evidence.
- **Clean.** No CTA, sales message, unsupported superlative, nested component, or
  unverified statistic inside the block.
- **Written last.** Author the block after the body is final so it summarizes
  what the article proves, not what the outline planned.

## Thresholds

| Dimension | Value |
|---|---|
| Bullet count | 3-5 |
| Bullet length | 12-30 words; 35 absolute maximum with a justified qualifier |
| TL;DR length | 2-4 sentences, 40-100 words |
| TL;DR structure | Takeaway, then reason, then constraint or caveat |
| Optional title | 2-8 words, 60 characters maximum |
| Placement | After a 1-2 paragraph intro, inside the first 150 words, before the first substantive H2 |
| Minimum page length | Roughly 800 words; shorter pages carry no summary block |

Placement is evidence-driven, not stylistic. Position studies of AI Overview and
ChatGPT citations put 38% of citations in the first 100 words and 55% in the
first 30% of a page, with a steep decay after that. A summary block below a long
intro, a gate, an ad slab, or a table of contents forfeits that position.

## Page-Type Fit

| Content type | Element | Notes |
|---|---|---|
| Multi-section guide | Key takeaways | The default case: several distinct conclusions |
| Comparison / round-up | Key takeaways | Each decisive finding is separately citable |
| Data or research piece | TL;DR + key takeaways | TL;DR earns the read, bullets expose the figures |
| Single-argument analysis | TL;DR only | One dense non-obvious conclusion, stated plainly |
| How-to under 800 words | Neither | The reader absorbs the body faster than a recap |
| Glossary term | Neither | The definition answer block already occupies this job |
| Local / geo page | Key takeaways only when locally specific | Swapping the city name must break the bullet |

## Rejection Criteria

Reject a candidate bullet when it:

- names a theme, section, or learning promise instead of a conclusion;
- restates the H1, the lead sentence, the meta description, or an FAQ answer;
- requires a fact, number, or source the body does not contain;
- depends on the surrounding paragraph to make sense;
- states an action in a procedure where completion, not insight, is the point;
- is boilerplate that could sit unchanged on a different article;
- sells rather than concludes.

## Output Shape

Return rows in this form:

| position | takeaway | conclusion_type | evidence | word_count | confidence |
|---|---|---|---|---|---|

- `position`: 1-based order in the final list.
- `takeaway`: the bullet text, 12-30 words, sentence case, terminal punctuation.
- `conclusion_type`: `finding`, `mechanism`, `magnitude`, `boundary`,
  `comparison`, or `decision-rule`.
- `evidence`: the section heading, sentence, figure, or source in the body that
  proves the bullet.
- `word_count`: integer count of the bullet.
- `confidence`: `supported`, `needs-source`, or `reject`.

For a TL;DR, return a single row with `position: 0`, the sentence count, and the
same evidence and confidence fields.

## QA Gate

1. Count is 3-5; each bullet is 12-30 words (35 hard maximum).
2. Every bullet is a complete sentence stating a conclusion.
3. Every bullet survives isolation: read alone, it delivers something specific.
4. Every claim maps to named body evidence.
5. No wording overlaps the TL;DR, the lead, the FAQ, or the conclusion.
6. Scope and qualifiers are present wherever a number or comparison appears.
7. No CTA, superlative, hedge, or unverified statistic.
8. The block would sit inside the first 150 words as rendered.

## Storage and Rendering

- On Voxel post types carrying a `takeaways` repeater, each row holds one bullet
  in its `value` subfield as a `texteditor` value. Write one row per bullet; do
  not concatenate a list into a single row.
- The block renders above the post body. Keep it server-rendered, crawlable
  text; never an image, an accordion, or a JavaScript-only injection.
- Do not add summary-specific schema. Structured data, when present, must match
  the visible text.

## Related

- [`faq-authoring.md`](faq-authoring.md) - the bottom-of-page counterpart; FAQ
  rows are the self-contained deep-page citation surface.
- [`claude-seo-authoring.md`](claude-seo-authoring.md) - the mandatory upstream
  routing for reader/SERP-facing copy.
- [`seo-defined-terms.md`](seo-defined-terms.md) - the definition answer block
  that replaces a summary block on glossary pages.
