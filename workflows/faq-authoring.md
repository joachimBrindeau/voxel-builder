# FAQ Authoring Workflow

Write or improve visible FAQ question-and-answer rows for one specific content
source: article, service page, glossary term, local page, event page, product
page, or Voxel CPT record. This workflow produces reader-facing FAQ content; it
does not produce schema.

## When to Use

- The user asks to write, improve, audit, or regenerate FAQ questions and answers.
- The user provides a URL, post ID, Voxel record, draft text, or content packet.
- A Voxel field such as `faq` needs content, but the write/apply step is separate.

## When NOT to Use

- Schema-only work (`FAQPage`, `QAPage`, JSON-LD) - use the lean-seo/schema route.
- Generic SEO audits with no FAQ authoring request - use `audit.md` or
  `settings.md`.
- Thin pages where the body itself is missing - fix core content first; FAQ
  cannot compensate for a weak page.

## Entry Criteria

1. A content source is available: live URL, post ID/site/CPT, rendered HTML,
   Voxel data packet, or pasted source text.
2. The target content type is known or inferable (`article`, `service`,
   `glossary`, `local`, `event`, `product`, `other`).
3. The target language and whether this is a standalone FAQ page vs embedded FAQ
   section are known or inferable.

If the source content is missing, ask for it before Phase 0.

## Phase 0 - Resolve Source and Owner

**Entry:** Entry criteria met.

**Actions:**

1. Identify the source-of-truth owner: WordPress post content, Voxel `faq`
   repeater, Voxel body/description fields, Elementor static JSON, or pasted text.
2. Fetch the full source content. For Voxel records, use `wpdev voxel:fields` and
   `wpdev voxel:data`; for live pages, capture rendered text/HTML as needed.
3. Capture existing FAQ rows, if present, without overwriting them.
4. Write a compact source packet in memory or `/tmp/faq-source-<slug>.md` with:
   title/H1, content type, target audience, source sections/fields, existing FAQ,
   local/place facts, claims that must not be invented, and target output count.

**Exit:** source packet contains enough evidence to support FAQ answers; owner is
known; existing FAQ state is preserved.

## Phase 1 - Load Standards and SEO Methodology

**Entry:** Phase 0 packet exists.

**Actions:**

1. Read [`../references/voxel/faq-authoring.md`](../references/voxel/faq-authoring.md).
2. Apply [`../references/voxel/claude-seo-authoring.md`](../references/voxel/claude-seo-authoring.md)
   because FAQ rows are reader/SERP-facing copy. Use Read-fallback for upstream
   claude-seo methodology; do not claim a tool ran when it did not.
3. Treat `docs/seo-checklist.db` as the checklist source. Use the writing-only
   rules from the reference; do not add schema or rich-result requirements.

**Exit:** writing gates are loaded: clear Q&A pairs, natural-language questions,
answer-first, self-contained answers, source evidence, page-type specificity, and
length targets.

## Phase 2 - Question Plan

**Entry:** Phase 1 standards loaded.

**Actions:**

1. Classify page type and intent:
   - article: informational follow-up
   - service: eligibility/process/cost/duration/risk/next step
   - glossary: optional genuine follow-up only
   - local: service-area-specific follow-up
   - event: attend/register/location/replay/speaker
   - product: use-case/fit/constraint/support
2. Build 5-10 candidate questions from source gaps, related entities, and user
   follow-up intent.
3. Reject candidates that:
   - duplicate the lead/definition/body without adding follow-up value;
   - require unsupported facts;
   - exist only for schema/rich-result purposes;
   - are boilerplate across many pages;
   - would make a glossary term page look template-farmed.
4. Select the final target set, normally 3-6 rows for an embedded section or
   enough rows for 800+ words on a standalone FAQ page.

**Exit:** final question plan lists selected and rejected questions with reasons.

## Phase 3 - Author FAQ Rows

**Entry:** Phase 2 question plan complete.

**Actions:**

1. Partition 5-10 homogeneous content items per `voxel-faq-author` batch and run
   bounded waves through `references/core/parallel-dispatch.md`.
2. Pass each item a stable scope id, source packet, question plan, target language,
   content type, output count, and FAQ writing standard.
3. Require one leaf envelope per content item using the table shape from
   `faq-authoring.md`:
   `question`, `answer`, `intent`, `evidence`, `word_count`, `confidence`.

**Exit:** candidate FAQ rows exist with evidence and word counts.

## Phase 4 - QA and Revision Gate

**Entry:** Phase 3 rows returned.

**Actions:**

1. Validate every row against the QA gate in `faq-authoring.md`.
2. Enforce length:
   - default 40-80 words per answer;
   - ideal 45-60 for simple answers;
   - 90-160 only when complexity or compliance requires it;
   - standalone FAQ page total must reach 800+ words.
3. Enforce page-type gates:
   - glossary: optional, term-specific, after the main body, no boilerplate;
   - local: locally specific and source-supported;
   - service/product/YMYL: no unsupported guarantees, prices, outcomes, or advice.
4. Revise or reject any `needs-source` or `reject` row. Do not invent facts to
   rescue a weak question.

**Exit:** final rows are all `supported`, non-duplicative, self-contained, and
page-type appropriate.

## Phase 5 - Output or Apply

**Entry:** Phase 4 passed.

**Actions:**

1. Default output: provide the FAQ table and, when useful, a Voxel repeater-ready
   JSON array with `question` and `answer` keys.
2. If the user explicitly asked to write/apply to the site, enter
   [`curation.md`](curation.md) for the actual mutation. The orchestrator writes
   once after backup/read-back gates; the `voxel-faq-author` subagent never writes.
3. If the FAQ belongs in an Elementor template, enter [`build.md`](build.md) for
   render changes after content approval.

**Exit:** FAQ content is delivered, or a separate write workflow has been routed
with source owner and rollback plan known.

## Phase 6 - Verification

**Entry:** FAQ rows delivered or written.

**Actions:**

1. Static verification: re-run the Phase 4 QA gate on the final output.
2. If written to WordPress/Voxel, read back the stored field and confirm equality.
3. If rendered on a page, use the browser verification pattern from `build.md`
   Phase 6: screenshot, rendered text, no tag leakage, no console/page errors.
4. Record deferred verification when the page is not live yet; do not mark it done.

**Exit:** final FAQ is either statically validated or live-verified with read-back.

## Output Contract

Return:

1. Source: page/post/content item and owner.
2. FAQ rows: question, answer, intent, evidence, word count.
3. Rejected questions: question and reason.
4. QA result: pass/fail against writing standard.
5. Apply status: not requested, deferred, or verified write/read-back.
