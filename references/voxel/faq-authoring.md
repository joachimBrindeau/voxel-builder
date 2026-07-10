# FAQ Authoring Standard

Visible FAQ content only. This reference intentionally excludes `FAQPage`,
`QAPage`, rich-result, and JSON-LD guidance; use schema references only when the
user explicitly asks for schema.

## Checklist-Derived Rules

These rules were distilled from `docs/seo-checklist.db` writing/content criteria:

- **Use clear question-and-answer pairs.** FAQ sections on key pages should expose
  explicit Q&A rows that can be extracted by humans and AI systems.
- **Phrase headings as natural-language questions.** Prefer complete questions
  matching how users ask: "How long does X take?", "What is the difference
  between X and Y?", "Can X apply in <place>?".
- **Answer first.** The first sentence answers the question directly before
  adding caveats, examples, or next steps.
- **Make every answer self-contained.** A passage must still form a complete
  answer when extracted without surrounding page context.
- **Default answer length:** 40-80 words, with 45-60 as the normal target.
  Answers below 30 words are usually too thin; answers above 80 words need a
  reason. For complex/YMYL answers, allow 90-160 words only when needed for
  accuracy.
- **Include a concrete fact, definition, criterion, or decision rule** in each
  answer where the source supports it. Do not pad with generic reassurance.
- **Match the page type.** FAQ rows must fill real follow-up intent for this
  page, not duplicate the hero/lead or compensate for thin body content.
- **Local pages need local questions.** For location/service-area pages, include
  locally relevant FAQ content only when the source supports actual service-area
  detail. Swapping the place name should break the answer's coherence.
- **FAQ pages need depth.** A standalone FAQ page should have at least 800 words
  total. A section embedded in another page has no standalone minimum, but each
  row must earn its space.
- **Voice/local search:** complete-question phrasing and concise answers are
  preferred for voice search and local queries.

## Content-Type Question Mix

Choose only questions supported by the source content.

| Content type | Good FAQ topics | Reject |
|---|---|---|
| Article / guide | unresolved subtopic, definition, example, comparison, next step, caveat | questions already fully answered in the intro |
| Service page | eligibility, process, duration, price/range caveat, documents needed, risks, outcomes, next step | claims about guarantees or pricing not in source |
| Glossary term | difference from related term, when to use it, concrete example, common confusion, related concept | boilerplate rows repeated for every term |
| Local / geo page | service area, local logistics, local eligibility, city-specific process, local proof | city-name swaps with no real local detail |
| Event page | registration, tickets, schedule, location/access, speaker/organizer, replay/recap | details not present in the event source |
| Product / offer | use case, fit, constraints, compatibility, proof, shipping/support | unsupported comparisons or performance claims |

## Output Shape

Return rows in this form:

| question | answer | intent | evidence | word_count | confidence |
|---|---|---|---|---|---|

- `question`: one natural-language question, usually 4-12 words; longer is fine
  when needed for clarity.
- `answer`: answer-first, self-contained, 40-80 words by default.
- `intent`: `definition`, `comparison`, `eligibility`, `process`, `cost`,
  `duration`, `local`, `risk`, `example`, `next-step`, or `other:<label>`.
- `evidence`: exact source fact/section/title/field that supports the answer.
- `confidence`: `supported`, `needs-source`, or `reject`.

## QA Gate

A FAQ set passes only when:

1. Every row is supported by source evidence.
2. Every answer starts with the direct answer.
3. Every answer is self-contained and grammatical.
4. No row exists only for schema/rich-result purposes.
5. The set avoids duplicate intent and generic filler.
6. Page-type gates pass: glossary rows are optional and genuine; local rows are
   locally specific; standalone FAQ pages reach 800+ total words.

## Source Query

Use this from the WordPress workspace when refreshing the standard:

```bash
sqlite3 -header -column docs/seo-checklist.db "
SELECT id, parentId, name, description
FROM nodes
WHERE (
  lower(name) LIKE '%faq%' OR lower(description) LIKE '%faq%' OR
  lower(name) LIKE '%question%' OR lower(description) LIKE '%question%' OR
  lower(name) LIKE '%answer%' OR lower(description) LIKE '%answer%' OR
  lower(name) LIKE '%self-contained%' OR lower(name) LIKE '%extract%' OR
  lower(name) LIKE '%natural language%'
)
AND lower(name) NOT LIKE '%schema%'
AND lower(description) NOT LIKE '%schema%'
AND lower(name) NOT LIKE '%rich result%'
AND lower(description) NOT LIKE '%rich result%'
ORDER BY name;"
```
