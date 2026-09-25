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
| `sameAs` | repeater `{url}` | no | max ~30 | `sameAs` | entity resolution |
| `faq` | repeater `{question, answer}` | no | — | **none** (optional on-page only) | optional on-page Q&A |

### Defined-term identity contract

For every glossary record, keep the three identity surfaces distinct and enforce
them independently:

- `post_title` is the exact canonical term, with no suffix, definition, or SEO copy.
- `post_name` is `sanitize_title(post_title)` and therefore the term itself slugified.
- `h1` is individually authored by the LLM from the record's evidence packet. It
  starts with the exact term, stays natural and descriptive, and is at most 70
  characters. Never derive sibling H1s through a mechanical suffix/template swap.

Validate all three after every write. A descriptive `post_title`, an inherited old
slug, or a mechanically generated H1 fails the record gate even when page copy is
otherwise valid.

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
- **"see also" lateral links** → the derived `hierarchy-<cpt>-siblings` relation (see the **Internal linking** section below)
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

### The term/service title collision

A glossary term almost always shares its name with something else on the site: a
service page, a product, a category. On the shipped `title_template_<cpt>` default
of `%title%`, `/glossary/horodatage` and the service page `/horodatage` both emit
`<title>Horodatage | MyProof</title>`. Two indexable URLs with an identical title
read as duplicates, and Google may serve the commercial page for a definitional
query, or vice versa.

**Fix at the type-level setting, not per record.** Retitling the current terms
leaves the next one to regress:

```bash
# key is title_template_<cpt> in the `meta` category; derive it rather than
# hardcoding the convention:
#   lean_seo_build_meta_setting_key( LEAN_SEO_META_KIND_TITLE_TEMPLATE, '<cpt>' )
```

Prefer `%h1%` over a mechanical `%title% : définition` suffix **when the CPT
already has an authored `h1`** — it reuses editorial copy instead of generating
boilerplate, and the `h1` is already distinct per term. Check the resolved length
first (`%h1%` plus the site suffix should stay under ~60 chars); fall back to a
short suffix when the `h1` is long. There is no `wpdev` setter for lean-seo
settings, so `lean_seo_settings_set( 'meta', $key, $value, $type, $desc )` is the
path, and a migration should refuse to overwrite anything other than the shipped
default.

Verify by **counting duplicate titles across every published post in every public
post type**, not just the terms you touched: that is what proves the collision is
gone rather than relocated, and it catches sibling scopes the change should not
have moved. Watch for a term whose slug also has a redirect (`/blockchain` →
`/glossary/blockchain`): a matching canonical makes that a redirect, not a second
collision.

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
  This same parent is what materializes the hierarchy relations (see
  [Hub-and-spoke](#hub-and-spoke--internal-linking-tier-3133) below), so it is not
  an optional tidiness step.
- **Express category grouping through a taxonomy** (`<cpt>_category`), not
  `post_parent`. The taxonomy gives category archive pages (the sub-hubs of
  Tier 3.1) and optional per-category `DefinedTermSet`s **without** touching the URL.

## Hub-and-spoke + internal linking (Tier 3.1/3.3)

- **Hub:** the CPT landing page links to every term (or to each category archive,
  which links to its terms). Every term links back to the hub via the breadcrumb.
- **Lateral "see also":** the derived `hierarchy-<cpt>-siblings` relation supplies related-term links, so
  lateral PageRank flows. It is **derived, not writable** — see below.
- **Anchor discipline:** vary anchor text (use the related term's name), embed links
  in sentences in the `content` body, and **cap exact-match** internal anchors per
  term. Automated linking must read as editorial, not engineered — over-optimized
  identical internal anchors trip the same suspicion as manipulative backlink anchors.

### Hierarchy relations are derived from `post_parent`, not writable

`siblings`, `ancestors` and `children` are **computed** by the Hierarchy module's
maintainer from `wp_posts.post_parent`, and stored under prefixed keys
(`hierarchy-<cpt>-siblings`), not under the bare field name.

**`voxel:set-field hierarchy-siblings` therefore reports success and writes
nothing** — `wp_voxel_relations` stays empty. There is no error to notice. Do not
verify these relations from the command's exit status; read the relation rows back.

Set the **parent** instead, and every derived relation materializes at once:

```sh
wp post update <term-id> --post_parent=<hub-id>
```

This single write is what closes four gaps together, so do it before diagnosing
them separately: flat URL + breadcrumb (both walk `post_parent`), the `siblings`
relation, and the `ancestors` trail. Note lean-seo's builder **drops trails under
3 items**, so a term with no real parent emits no `BreadcrumbList` at all — an
absent breadcrumb is usually a missing parent, not a schema misconfiguration.

A related-terms template block must also bind the token that actually has rows:
`hierarchy-<cpt>-siblings` for lateral links. `hierarchy-<cpt>-children` is empty on a
leaf term and renders an invisible, permanently-empty section.

### Verifying prose autolinking: two traps

Autolinking (the linker that turns a term mention in body copy into a link) lives on
a **different surface** from the related-terms cards. Conflating them produces checks
that contradict each other.

- **Scope the check to prose.** "Does the page link term X?" is the wrong question:
  the related-terms **card** legitimately links a sibling that prose must *not*
  link (e.g. a compound term must not link its own constituents inside its
  definition). Collect prose links specifically (`main p a[href]`, `main li a[href]`)
  and assert on those, or a no-self-link rule will fight a related-cards rule.
- **Never require every term page to autolink.** A correct page can have zero prose
  term links: the head term may mention no other term, and a near-miss mention is
  *not* a match — "enveloppe **e-Soleau**" (a distinct product name) must not link the
  term "Enveloppe Soleau". Per-page minimums fail on correct pages.

To still catch "autolinking silently switched off", assert at **corpus level** — at
least one prose term link exists across all terms — plus an untouched control page
that was already autolinking. That fails on a real regression without punishing a
page whose prose has nothing to link. Before changing either the site or the check,
read the actual sentence: `get_post_field( 'post_content', <id> )` shows whether the
mention is a true term occurrence or a near-miss.

## E-E-A-T (Tier 4.3)

Definitional/reference content lives or dies on Expertise + Trust:

- **Named author** with demonstrable subject expertise — set `post_author` to a real
  credentialed profile (and wire it into schema if using an `Article` overlay).
- **Cite authoritative primary sources** in the body (the code/law/agency the term
  comes from).
- **Visible freshness** — `dateModified` from `post:modified`; refresh terms that
  evolve (tax rates, regulation).

## Schema graph, CLI, and verification

The `DefinedTerm` + `DefinedTermSet` `@graph`, the site-level hub node, the
`FAQPage` prohibition, preflight dependencies, the apply recipe, and the live
verification assertions live in
[`seo-defined-terms-schema.md`](seo-defined-terms-schema.md).

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

> **Field names vary per site. Map roles before authoring.** The names below are
> this reference's canonical vocabulary, not a guarantee. Run
> `./wpdev voxel:fields <site> <cpt>` first and bind by *role*, not by name. A
> site may carry no `hook`/`content`/`acronym` at all and instead express the same
> roles as, for example, `definition` (answer block) + `description`
> (long-form body) + `post_excerpt` (meta description). Apply each row's length
> and quality bound to whichever field actually owns that role, and note any role
> the CPT genuinely cannot express rather than inventing a field for it.

- [ ] `h1` set, ≤70 chars.
- [ ] `hook` set, 35-120 chars, one complete sentence (→ meta description).
- [ ] `definition` set, 200-400 chars ≈ 40-60 words, term-as-subject, dictionary
      register (→ answer block + `DefinedTerm.description`).
- [ ] **`content` set, 400-800 words**, real domain-expert body (mechanism, criteria,
      worked example, edge cases) — passes the "only an expert could write this" test.
- [ ] `acronym` set where the term has one (→ `termCode` + `alternateName`).
- [ ] `sameAs` rows pass the exact-equivalence workflow for canonical entities where they exist.
- [ ] If `faq` rows exist, each question is a genuine term-specific follow-up
      (not template filler), renders after the main body, and emits no `FAQPage`.
- [ ] Parented to the **CPT landing page** (flat URL) — not to a category post.
- [ ] Category assigned via **taxonomy** (not `post_parent`).
- [ ] Lateral links present: verify `hierarchy-<cpt>-siblings` rows exist (they are
      **derived** from `post_parent`, never set directly — see Internal linking).
- [ ] `post_author` = a credentialed profile (E-E-A-T).
- [ ] Prose autolinking checked at **corpus level** (≥1 prose term link across all
      terms, plus an untouched control), never as a per-page minimum — see
      "Verifying prose autolinking".
- [ ] `sources` rows render as **visible anchors in the body**, not only inside
      JSON-LD `citation`. Compare the two counts explicitly; see below.
- [ ] Live check after release/noindex removal: flat URL, breadcrumb
      `Home > Glossary > Term`, `DefinedTerm` + `WebPage` + `BreadcrumbList`,
      **no `FAQPage`**, meta description complete. While an intentional editorial
      noindex flag remains, Lean SEO must emit no JSON-LD; verify that exact URL
      and defer the positive schema assertion rather than substituting a
      post-type-wide validator sample.

## Creating the first record of an empty glossary CPT

A CPT with zero published records has a **never-exercised single template**.
Field data can be perfectly stored while the template silently fails to surface
it, so treat the first record as a template audit, not just a content write.

Two defect classes recur and neither is visible from stored data or HTTP 200:

1. **Untranslated donor copy.** Templates ported from an English source keep
   hardcoded strings (section headings, "Learn more", `pluralize(term,terms)`)
   that never appear until a record renders. Diff the rendered headings against
   the site language; a `<h2>` from the *template* is as user-visible as one from
   the content.
2. **A field with no rendering surface.** `sources`, `faq`, or `sameAs` may reach
   JSON-LD through lean-seo while the template has no section for them. The
   schema is then strictly better than the page, which is the wrong direction.
   Assert **visible anchor count == JSON-LD `citation` count**, not merely that
   the schema is populated.

When a section is missing, port the site's existing one (for example a
`*-section-sources` library template) rather than authoring a new tree: the
shipped donor already carries the correct visibility gate. Copying also means
**regenerating element ids** against the ids already present in the target
document, or the duplicate ids will collide.

Verify with a control that has a rendering surface you already trust — an
existing article page — so a whole-template failure cannot be mistaken for a
content problem.


## Related

- Entity-equivalence research and population: [`../../workflows/identity-linking.md`](../../workflows/identity-linking.md)
- `sameAs` acceptance rules: [`sameas-identity-links.md`](sameas-identity-links.md)
- Field-type config keys: [`voxel-field-types.md`](voxel-field-types.md)
- Schema DSL SSOT + CLI: [`../core/command-surface.md`](../core/command-surface.md) §Schema (lean-seo)
- Full CPT lifecycle: [`../../workflows/cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md) (Phase 4 points here for defined-term CPTs)
- Dynamic tags for the single template: [`voxel-tags.md`](voxel-tags.md)
