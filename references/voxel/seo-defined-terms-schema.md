# Defined Terms: Schema Graph, CLI, And Verification

The `DefinedTerm` / `DefinedTermSet` JSON-LD graph for a defined-term CPT, the
apply recipe, and the live verification assertions. Companion to
[`seo-defined-terms.md`](seo-defined-terms.md), which owns the field model,
content rules, and internal linking.

Use-case-agnostic: substitute the site's own values for `<cpt>` and `<suffix>`.

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
      "name": "voxel:h1",
      "alternateName": "voxel:acronym",
      "description": "voxel:definition|strip_tags",
      "termCode": "voxel:acronym",
      "url": "post:permalink",
      "sameAs": { "@each": "voxel:sameAs", "@map": "row:url" },
      "inDefinedTermSet": "@ref:site#definedtermset"
    }
  ]
}
```

Key points:
- **`sameAs` via `@map`.** `{ "@each": "voxel:sameAs", "@map": "row:url" }` projects
  the `sameAs` repeater to a flat URL array. `@map` is the repeater→scalar-list
  projection (each row resolves one source string, empties dropped, de-duplicated).
  Requires current lean-seo. Without `@map`, `@each` only yields object/`@ref`
  arrays — wrong shape for a plain URL list.
- **Identity curation is not citation curation.** Follow
  [`sameas-identity-links.md`](sameas-identity-links.md); never promote a related
  source, broad topic, disambiguation page, or category/list page into `sameAs`.
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

**Scope this to the defined-term target you own.** A site's `page` or `post`
schema target may carry its own `FAQPage` node, typically gated by
`@require: voxel:faq` so it only fires on records that actually have rows. Seeing
`FAQPage` on the homepage is therefore *not* evidence that the glossary work is
non-compliant — check `schema:get <site> <cpt>` for the term target before
concluding anything. Removing a `FAQPage` from a shared `page` target is a
separate, wider content decision affecting every page with `faq` rows, and it
belongs to the owner of that target, not to a glossary task.

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
#   acronym text max 12; hook 35-120; sameAs repeater {required url}.

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


## Related

- Field model, content rules, internal linking: [`seo-defined-terms.md`](seo-defined-terms.md)
- Schema DSL SSOT + CLI: [`../core/command-surface.md`](../core/command-surface.md) §Schema (lean-seo)
- `sameAs` acceptance rules: [`sameas-identity-links.md`](sameas-identity-links.md)
