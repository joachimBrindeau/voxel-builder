# Geolocated Service Pages (derive an `exp` service under a `geo` city)

Use this reference to derive a canonical Voxel `exp` service into one city-specific
mirror under a `geo` post. It explains required unique field values, schema variants,
URL structure, and local-SEO boundaries. It does not authorize a live change.

## When to use

- Canonical `exp` service exists and needs a city-specific mirror under `geo`.
- Voxel Hierarchy allows cross-CPT nesting and both CPTs use `nest_urls`.
- Need `villes/<city>/<service>` with local content, metadata, and schema.

Not for defined terms. Defined terms remain flat by taxonomy; see
[`seo-defined-terms.md`](seo-defined-terms.md#flat-urls-tier-32--do-not-nest-under-category-posts).
A city parent is real location hierarchy, not grouping.

## Scope vs the local-SEO checklist

| # | Subsection | Scope |
|---|---|---|
| a | Local schema markup is complete with correct industry subtypes | **in-page** |
| b | Location pages have unique, high-quality content and correct structure | **in-page** |
| c | NAP information is consistent across all sources | advisory (off-page); on-page footer NAP and `tel:` remain page checks — see claude-seo `seo-local` / `seo-maps` |
| d | The GBP has complete descriptive content | advisory (off-page) — see claude-seo `seo-local` / `seo-maps` |
| e | The GBP has complete, fresh media assets | advisory (off-page) — see claude-seo `seo-local` / `seo-maps` |
| f | The GBP has correct identity and categorization | advisory (off-page) — see claude-seo `seo-local` / `seo-maps` |
| g | The GBP uses all available features and settings | advisory (off-page) — see claude-seo `seo-local` / `seo-maps` |
| h | The business has complete citation coverage across directories | advisory (off-page) — see claude-seo `seo-local` / `seo-maps` |
| i | The business has local authority signals and internal linking | advisory (off-page); internal-linking half is **in-page** — see claude-seo `seo-local` |
| j | The business has strong review signals across platforms | advisory (off-page) — see claude-seo `seo-local` / `seo-maps` |
| k | The site has strong on-page local SEO signals | **in-page** |
| l | Multi-location architecture scales without cannibalisation | **in-page** |

Pipeline owns in-page rows only. It surfaces advisory rows; it never turns GBP, NAP,
citations, reviews, or local-link acquisition into build steps.

Related gates: scaled pages must not be doorway or mad-libs output; location body needs
at least 500 words; 30+ pages triggers review; 50+ pages requires documented
justification.

## The uniqueness model (anti-doorway)

`exp` single template `2033` is shared. City uniqueness must live in real Voxel field
values, not template edits or a city token.

| Field key | Voxel type | Bound | Local-SEO purpose |
|---|---|---:|---|
| `h1` | text | required; 20-70 chars | city-specific H1, subsection k |
| `hook` | text | required; 35-120 chars | city-specific teaser and meta source, subsection k |
| `description` | texteditor | required; at least 500 words | local service body, subsection b |
| `faq` | repeater | required; local follow-up rows | local intent depth, subsection b |
| `conversion-*` | texteditor | required; city-specific problem/stakes/solution | information gain, subsection b |

At least 60% of written content must be unique from canonical sibling. **Swap test is a
hard gate:** if changing city name leaves page coherent, page is doorway output and must
not publish. Do not invent city facts. Use source-supported local specifics.

For subtree × city work, 30+ geo pages is review trigger. At 50+, require written
justification for distinct value, crawlability, and no cannibalisation before build.

## Schema: two node variants (the `areaServed` gate)

Current canonical `exp` `Service` uses org-wide
`"areaServed": "area_served:site_branches"`. A geo-child needs city `areaServed`.
Keep canonical variant. Add geo-child variant. Schema renderer supports `@require` and
`@require_not`; `hierarchy:parent` resolves immediate WP parent.

**Geo-child node** — only when immediate parent exists. Parent must expose configured
`#localbusiness` fragment before this node can reference it.

```json
{
  "@type": "Service",
  "@id": "@ref:self#service",
  "@require": "hierarchy:parent",
  "name": "post:title",
  "description": "seo:desc",
  "url": "post:permalink",
  "provider": "@ref:site#organization",
  "areaServed": "@ref:hierarchy:parent#localbusiness"
}
```

**Canonical node** — only when no parent exists; retain org-wide service area.

```json
{
  "@type": "Service",
  "@id": "@ref:self#service",
  "@require_not": "hierarchy:parent",
  "name": "post:title",
  "description": "seo:desc",
  "url": "post:permalink",
  "provider": "@ref:site#organization",
  "areaServed": "area_served:site_branches"
}
```

Warning: one unconditional parent override makes a canonical `exp` with no geo parent
resolve `@ref:hierarchy:parent` to null. Renderer prunes dangling reference. Canonical
`Service` then loses `areaServed`. Do not replace both variants with one node.

Before config write, inspect live source catalog and current graph through Route S. This
reference documents shape, not a portable field-key claim.

## URL nesting rationale

Geo-child `exp` intentionally nests through `post_parent`: `villes/toulouse/financement`.
Cross-CPT `nest_urls:true` makes city → service meaningful hierarchy. This differs from
flat defined-term URLs because term categories are grouping, not ancestor semantics.
Canonical branch remains authoritative and unchanged.

## Metadata (Route M) — city-aware title and meta

Breadcrumb city alone is insufficient. Derived `<title>` and meta description must carry
city through Route M `%token%` template, using only live-catalog-confirmed token or
`%vx(@post(parent.title))%`. Identical canonical and city title/meta is doorway signal.
Route M write surface: `lean_seo_meta` through
`lean_seo_settings_set("meta", lean_seo_build_meta_setting_key(...))`.

## E-E-A-T + internal linking

Use named qualified author, visible freshness, and source-supported local claims. Link
up to city hub through breadcrumb and laterally only where real city services exist.
Internal linking is in-page half of subsection i; local authority acquisition remains
advisory.

## CLI recipe

1. Create or reparent through [`../../workflows/cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md)
   and [`../../workflows/curation.md`](../../workflows/curation.md); do not invent create command.
2. Configure title/meta through [`../../workflows/settings.md`](../../workflows/settings.md#route-m--metadata).
3. Configure two schema variants through [`../../workflows/settings.md`](../../workflows/settings.md#route-s--schema).
4. Backfill parent URIs after parenting whole branch through
   [`../../workflows/settings.md`](../../workflows/settings.md#route-c--crawl--permalinks).
5. Validate rendered schema and URL; no live mutation occurs from this reference.

## Per-geo-page completion checklist

- [ ] New `exp` mirror parented to target `geo`; canonical source untouched.
- [ ] Unique `h1`, `hook`, `description`, `faq`, and `conversion-*` meet bounds.
- [ ] Description has at least 500 words and more than 60% unique content.
- [ ] Swap test fails after city replacement.
- [ ] City-aware title and meta description render through Route M.
- [ ] URL is `villes/<city>/<service>` and breadcrumb includes city.
- [ ] Geo-child schema variant emits city `areaServed`.
- [ ] Canonical variant remains guarded by `@require_not` and keeps `site_branches`.
- [ ] Browser and rendered JSON-LD verify without unresolved sources.

## Related

- [`seo-defined-terms.md`](seo-defined-terms.md) — flat URL counterpart.
- [`lean-seo-schema.md`](lean-seo-schema.md) — schema source grammar and guards.
- [`../../workflows/geolocation.md`](../../workflows/geolocation.md) — gated derivation process.
- [`../../workflows/settings.md`](../../workflows/settings.md) — Routes M, S, C.
