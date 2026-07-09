# SEO-Optimized Defined Terms (Glossary / Dictionary CPT)

The reusable recipe for a Voxel CPT whose singles are **definitions** — glossary,
dictionary, term bank, concept index. Produces `schema.org/DefinedTerm` +
`DefinedTermSet` JSON-LD, a SERP-safe title/description, and a field model that
*enforces* answer-block quality instead of hoping editors comply.

Use-case-agnostic: the CPT key, the title suffix, and the entity language are
parameters. Substitute the site's own values for `<cpt>` and `<suffix>`.

## When to use

- The CPT's singles answer "what is X" / "define X" definitional queries.
- The site runs **lean-seo** (config-only Schema Builder) + Voxel.

Definitional queries are the most snippet-resilient and most AI-Overview-prone
category simultaneously — a well-formed answer block wins Featured Snippets *and*
feeds AI Overview synthesis from the same span. That convergence is why the
field model below is worth enforcing.

## The field model

Every field maps to exactly one schema property **and** one SERP surface. The
length bounds are the whole point — they are enforced by Voxel `maxlength`/
`minlength` at input so bad data cannot be saved.

| Field key | Voxel type | required | limits | schema property | SERP surface |
|---|---|---|---|---|---|
| `h1` | text | **yes** | max 70 | `DefinedTerm.name` + `<title>` | title tag |
| `acronym` | text | no | max 12 | `termCode` + `alternateName` | entity code |
| `hook` | text | **yes** | **35-120** | — | **meta description** |
| `definition` | texteditor | **yes** | **200-400** (≈40-60 words) | `DefinedTerm.description` | **answer block** (Featured Snippet / AI Overview) |
| `content` | texteditor | **yes** | **min ~2500 chars (≈400-800 words)** | — | **deep body — the anti-thin-content requirement** |
| `sameas` | repeater `{source select, url}` | no | max ~6 | `sameAs` | entity resolution |
| `faq` | repeater `{question, answer}` | no | — | **none** (optional on-page only) | optional on-page Q&A |

Mark `h1`, `hook`, `definition`, **and `content`** as `required: true` **and** set the length bounds — required-ness alone lets an empty string save; the `minlength`/`maxlength` pair is what enforces quality. **`content` is required, not optional**: a term that is only an answer block is a thin page (see the **Tier 4** section below).

`faq` is optional and content-gated. Add rows only when a specific term has real
follow-up intent that the definition/body does not already answer cleanly: "How is
X different from Y?", "When should you use X?", "What is an example of X?". Do
not auto-generate generic questions for every term, do not use FAQ to compensate
for a thin `content` body, and do not let an FAQ section push the core definition
or body below the fold.

Reuse existing structural data instead of adding fields:
- **category grouping** → a **taxonomy** (`<cpt>_category`), **NOT** the `parent`
  hierarchy — parenting a term to a category *post* nests the URL (see
  the **Flat URLs** section below).
- **A-Z index** → an alphabetical `order` option on the search config
- **"see also" lateral links** → the `siblings` hierarchy relation (see the **Internal linking** section below)
- **`dateModified`** → native `post:modified` (no editorial date field)

## The two-surface rule (the #1 mistake to avoid)

The **answer block** and the **meta description** are different surfaces with
different length budgets:

- Answer block (`definition`) = 40-60 words ≈ 300 chars. Extracted verbatim by
  Google/AI. Feeds `DefinedTerm.description`.
- Meta description ≤ 155 chars (SERP display). Feeds the `<meta name="description">`.

Pointing `desc_template` at the 300-char `definition` **truncates mid-sentence**.
Point it at `hook` instead — a field Voxel bounds to 35-120 chars, structurally
guaranteed below 155, so the meta description is always complete. This is the
"let the Voxel field `maxlength` enforce the SERP bound" pattern: the field limit
(120) sits safely under the display limit (155).

## Tier 4 — every term needs a long-form body (anti-thin-content)

**The single most common failure: shipping terms that are only an answer block.**
A page that is a 40-60 word definition and nothing else is, to Google's
scaled-content and doorway-abuse classifiers, indistinguishable from a templated
term-farm — the pattern with documented 70-96% traffic losses. The answer block is
the **citable hook**; the `content` body is the **clickable depth** that (a) makes
the page non-thin and (b) gives a human a reason to click through an AI Overview
that already quoted the definition.

**Every term's `content` field is required and must carry 400-800 words** of
genuine domain-expert material. Structure it (H2s in the body):

- **How it works / mechanism** — the substance behind the one-line definition.
- **Criteria / eligibility / conditions** — who/what qualifies, thresholds, limits.
- **A worked example** — a concrete case with real numbers or a real scenario.
- **Edge cases / common confusions** — what people get wrong; distinctions from
  adjacent terms.
- **Related terms** — contextual links to sibling terms (see Internal linking).

The bar is the research's thin-content test: **"Could this page only have been
written by someone who actually knows the field?"** If a generic paraphrase of
Wikipedia would produce the same page, it is thin — deepen it or don't publish it.

Format (Tier 1.3): the lead is always the **paragraph** answer block. Inside the
body, use a **list** only where the concept is genuinely enumerable (eligibility
criteria, steps, types), and a **table** only for a genuine comparison (this term
vs an adjacent one, tiers, rates). Do not list-ify prose for cosmetics.

**Index-bloat discipline:** do not publish a term that cannot sustain a real body.
Better ten deep terms than fifty thin ones — a mass of thin pages drags the whole
CPT's quality signal down. Noindex or consolidate near-duplicate terms.

## Flat URLs (Tier 3.2) — do not nest under category posts

Term URLs must be **flat**: `/<cpt>/<term-slug>`, not
`/<cpt>/<category>/<term-slug>`. The research is explicit that deep nesting pushes
pages away from the crawl frontier and implies a hierarchy the linking may not
support.

**The trap:** in this stack both the URL *and* the breadcrumb derive from
`post_parent` (lean-seo's `breadcrumbs.php` walks `get_post_ancestors`). If you
parent a term to a *category post* to get grouping, you also nest its URL. So:

- **Parent every term to the CPT's landing page** (the `permalink_default` page),
  never to another term/category post → flat URL, breadcrumb `Home > Glossary > Term`.
- **Express category grouping through a taxonomy** (`<cpt>_category`), not
  `post_parent`. The taxonomy gives category archive pages (the sub-hubs of
  Tier 3.1) and optional per-category `DefinedTermSet`s **without** touching the URL.

## Hub-and-spoke + internal linking (Tier 3.1/3.3)

- **Hub:** the CPT landing page links to every term (or to each category archive,
  which links to its terms). Every term links back to the hub via the breadcrumb.
- **Lateral "see also":** set the Voxel `siblings` relation on each term to 2-4
  *genuinely* related terms (e.g. `CIR ↔ CII ↔ JEI`), so related-term links render
  and lateral PageRank flows.
- **Anchor discipline:** vary anchor text (use the related term's name), embed links
  in sentences in the `content` body, and **cap exact-match** internal anchors per
  term. Automated linking must read as editorial, not engineered — over-optimized
  identical internal anchors trip the same suspicion as manipulative backlink anchors.

## E-E-A-T (Tier 4.3)

Definitional/reference content lives or dies on Expertise + Trust:

- **Named author** with demonstrable subject expertise — set `post_author` to a real
  credentialed profile (and wire it into schema if using an `Article` overlay).
- **Cite authoritative primary sources** in the body (the code/law/agency the term
  comes from).
- **Visible freshness** — `dateModified` from `post:modified`; refresh terms that
  evolve (tax rates, regulation).

## Schema graph recipe

Author an explicit `@graph` for the `<cpt>` target. The schema DSL (source
prefixes `post:`/`meta:`/`seo:`/`var:`/`row:`/`query:`, the `@each`/`@ref`/`@map`/
`@list`/`@value:`/`concat:` keys, and the `|strip_tags` transform) is documented
in [`../core/command-surface.md`](../core/command-surface.md) §Schema (lean-seo).
The DefinedTerm-specific worked graph:

```json
{
  "@graph": [
    {
      "@type": "WebPage",
      "@id": "@ref:self#webpage",
      "name": "seo:title",
      "description": "seo:desc",
      "url": "post:permalink",
      "inLanguage": "var:site_language",
      "isPartOf": "@ref:site#website",
      "breadcrumb": "@ref:self#breadcrumb",
      "mainEntity": "@ref:self#definedterm",
      "dateModified": "post:modified"
    },
    {
      "@type": "DefinedTerm",
      "@id": "@ref:self#definedterm",
      "name": "meta:h1",
      "alternateName": "meta:acronym",
      "description": "meta:definition|strip_tags",
      "termCode": "meta:acronym",
      "url": "post:permalink",
      "sameAs": { "@each": "meta:sameas", "@map": "row:url" },
      "inDefinedTermSet": "@ref:site#definedtermset"
    }
  ]
}
```

Key points:
- **`sameAs` via `@map`.** `{ "@each": "meta:sameas", "@map": "row:url" }` projects
  the `sameas` repeater to a flat URL array. `@map` is the repeater→scalar-list
  projection (each row resolves one source string, empties dropped, de-duplicated).
  Requires current lean-seo. Without `@map`, `@each` only yields object/`@ref`
  arrays — wrong shape for a plain URL list.
- **`alternateName` + `termCode` both from `acronym`.** When the acronym is empty
  the renderer prunes both keys (no empty strings emitted).
- **`|strip_tags`** on `description` because `definition` is a texteditor field
  (stored with `<p>` tags); the answer block must reach schema as plain text.
- **`breadcrumb` `@ref:self#breadcrumb`** resolves to `{permalink}#breadcrumb`,
  matching lean-seo's site-wide BreadcrumbList `@id`.

### Site-level DefinedTermSet (the hub node)

Add one `DefinedTermSet` to the site-identity graph (the `front_page` target)
so every term's `inDefinedTermSet` reference resolves and the set reads as one
authored vocabulary:

```json
{
  "@type": "DefinedTermSet",
  "@id": "@ref:site#definedtermset",
  "name": "@value:<Vocabulary name>",
  "description": "@value:<One-sentence set description>",
  "url": "concat:var:site_url,,@value:/<cpt>",
  "inLanguage": "var:site_language",
  "publisher": "@ref:site#organization",
  "hasDefinedTerm": { "@each": "query:<cpt>_ids", "@ref": "definedterm" }
}
```

`query:<cpt>_ids` must exist as a source resolver in lean-seo
(`modules/schema/sources/query.php` — mirrors `query:org_ids`). Add a case for
the CPT if absent; it returns published post IDs. `@ref: "definedterm"` mints
`{permalink}#definedterm` per term, matching each term's DefinedTerm `@id`.

### Optional on-page FAQ; no FAQPage schema

**Do not emit `FAQPage` schema.** Google fully deprecated FAQ rich results on
**May 7, 2026**. The `faq` repeater renders on-page only (accordion or `<dl>`) —
never through a schema `FAQPage` node. This is a hard rule for defined-term CPTs,
not a preference. If a CPT config still carries a `FAQPage` node added solely for
SERP enrichment, **remove it**; it has no Google rich-result upside and distracts
from the supported `DefinedTerm`/`DefinedTermSet` graph.

Visible FAQ content is not banned. Keep it only when the questions are genuinely
term-specific, self-contained, and useful after the main definition/body. Do not
bake a boilerplate FAQ module into every glossary template.

- **`QAPage`** is still active but is only for *genuine user-generated* Q&A
  (community answers), never for editorial definition FAQs. Do not substitute it for
  the removed `FAQPage`.
- **`Speakable`** (optional) can mark the 2-3 sentence definition paragraph for
  voice/TTS. It is beta and news-oriented, so treat it as a low-priority nicety, not
  a requirement.

## Preflight (two dependencies to confirm first)

1. **`BreadcrumbList` source.** The graph's `breadcrumb: "@ref:self#breadcrumb"` assumes a site-wide `BreadcrumbList` already renders (lean-seo emits one when configured). Confirm with `wpdev schema:get <site> --json` (look for an existing breadcrumb node) or curl a live page. If none exists, add an explicit `BreadcrumbList` to the CPT graph or drop the `breadcrumb` key — do not point it at a node that never renders.
2. **`query:<cpt>_ids` resolver.** The site `DefinedTermSet`'s `hasDefinedTerm: {"@each": "query:<cpt>_ids", ...}` requires a matching case in lean-seo's `modules/schema/sources/query.php` (mirrors `query:org_ids`). Grep for it; if absent, add the case (returns published post IDs for the CPT) before `schema:set front_page`, or the DefinedTermSet emits an empty `hasDefinedTerm`.

## CLI recipe

Back up first, then field CRUD via `voxel:settings`, then schema via `schema:set`.

```bash
# 0. Backup the Voxel config
wpdev voxel:settings <site> get --json > /tmp/voxel-post_types.backup.json

# 1. Set field length bounds (enforce the answer block) — one path each
wpdev voxel:settings <site> set "<cpt>/fields" --value=@/tmp/<cpt>-fields.json --dry   # preview
wpdev voxel:settings <site> set "<cpt>/fields" --value=@/tmp/<cpt>-fields.json         # apply
#   fields JSON: h1 maxlength 70; definition minlength 200 maxlength 400;
#   acronym text max 12; hook 35-120; sameas repeater {source select, url}.

# 2. Title + description templates (bounded field for meta description)
#    title_template = "%title% : <suffix>"   desc_template = "%hook%"
#    Set via lean_seo_settings_set() through wp eval, or the settings UI.

# 3. Schema graph
wpdev schema:set <site> <cpt> @/tmp/<cpt>-schema.json           # validates before persist
wpdev schema:set <site> front_page @/tmp/front_page-schema.json # add the DefinedTermSet node

# 4. Purge + verify
wpdev wp <site> litespeed-purge all   # or: wpdev purge <site>
wpdev schema:validate-live <site>
```

## Verification checklist

Curl a live term page and assert:
- `DefinedTerm` node present: `name`, `description` (≤60 words, **no HTML tags**),
  `termCode`+`alternateName` (or both absent when no acronym), `sameAs` array,
  `inDefinedTermSet` `@id` resolving to `#definedtermset`.
- `WebPage` + `BreadcrumbList` present.
- **`FAQPage` absent.**
- `<title>` = `<term> : <suffix> | <site>`.
- `<meta name="description">` = the `hook`, **complete sentence, no mid-word cut**.
- Homepage emits the `DefinedTermSet` with `hasDefinedTerm` listing every term.
- `wpdev schema:validate-live <site>` reports 0 errors.

```bash
curl -sk "https://<site>/<cpt>/<slug>" | \
  grep -oE '<script type="application/ld\+json">.*</script>'   # inspect @graph
```

## Writing the answer block (definition field)

The 40-60 word answer block is the highest-leverage content decision. Write it to
this template so Featured Snippets and AI Overviews extract it cleanly:

> **"[Term] is a [category] that [distinguishing characteristic]. [One sentence of scope, context, or importance]."**

Rules:
- Open with the **term as the grammatical subject** (not "This refers to…").
- **40-60 words** (ideal 45-55). The `definition` field's 200-400 char bound
  enforces this; a one-liner or an essay cannot be saved.
- **Neutral, dictionary-style** prose — no marketing, no first person.
- **Self-contained** — intelligible without the surrounding page, because it is
  extracted verbatim.
- On the page, place it **immediately under an H2 that contains the term**, in the
  first 200 words, with nothing between the H2 and the paragraph.

The `hook` (35-120 chars) is the short teaser — the meta description and the
menu/section subtitle. Write it as one complete, standalone sentence.

## Per-term completion checklist

A term is **not done** until every box is true. Following only the schema/field
setup produces a thin page — the content + linking rows are what make it survive.

- [ ] `h1` set, ≤70 chars.
- [ ] `hook` set, 35-120 chars, one complete sentence (→ meta description).
- [ ] `definition` set, 200-400 chars ≈ 40-60 words, term-as-subject, dictionary
      register (→ answer block + `DefinedTerm.description`).
- [ ] **`content` set, 400-800 words**, real domain-expert body (mechanism, criteria,
      worked example, edge cases) — passes the "only an expert could write this" test.
- [ ] `acronym` set where the term has one (→ `termCode` + `alternateName`).
- [ ] `sameas` rows for canonical entities (Wikidata / Wikipédia) where they exist.
- [ ] If `faq` rows exist, each question is a genuine term-specific follow-up
      (not template filler), renders after the main body, and emits no `FAQPage`.
- [ ] Parented to the **CPT landing page** (flat URL) — not to a category post.
- [ ] Category assigned via **taxonomy** (not `post_parent`).
- [ ] `siblings` set to 2-4 genuinely related terms (lateral links).
- [ ] `post_author` = a credentialed profile (E-E-A-T).
- [ ] Live check: flat URL, breadcrumb `Home > Glossary > Term`, `DefinedTerm` +
      `WebPage` + `BreadcrumbList`, **no `FAQPage`**, meta description complete.

## Related

- Field-type config keys: [`voxel-field-types.md`](voxel-field-types.md)
- Schema DSL SSOT + CLI: [`../core/command-surface.md`](../core/command-surface.md) §Schema (lean-seo)
- Full CPT lifecycle: [`../../workflows/cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md) (Phase 4 points here for defined-term CPTs)
- Dynamic tags for the single template: [`voxel-tags.md`](voxel-tags.md)
