# Geolocated Service Pages (deriving an `exp` service under a `geo` city)

The reusable recipe for **mirroring a canonical Voxel service into a per-city page
parented to a `geo` post**. It produces a city-nested URL, a city-aware breadcrumb,
city-signalled `LocalBusiness`/`Service` schema, and field-enforced unique content —
without becoming a doorway page.

Use-case-agnostic: `<exp>` (the service CPT), `<geo>` (the location CPT), and
`<city>` are parameters. The klarc.test values (`exp` service tree, `geo` cities
Toulouse/Lyon) are shown as the worked example — substitute the site's own.

## When to use

- A **canonical service already exists** (an `exp` post under the services landing
  page) and you want a **city variant** that ranks locally.
- The site runs **Voxel + lean-seo + the Hierarchy module** with `nest_urls` on both
  CPTs (cross-CPT nesting), so a post of one CPT can parent under a post of another.
- You want the city page to signal locality in URL + breadcrumb + schema + content
  **without duplicating the canonical page** into a doorway.

NOT for **defined terms** (glossary / dictionary singles). Those stay **flat** and
are grouped by taxonomy, never nested — see [`seo-defined-terms.md`](seo-defined-terms.md)
§Flat URLs. The one-line difference: a `geo` parent is a *real place hierarchy*
(city → service-in-city) that SHOULD nest; a term category is a *grouping* that
should NOT.

## The derivation model

The geo-mirror is a **DEEP structural clone of the canonical subtree, re-rooted under
the city** — NOT a flat "one node per (city × service) parented directly to geo". Only
the **branch-root** node attaches to the `geo` post; every **descendant** parents under
the **mirrored version of its own canonical parent**, so the whole canonical parent
chain is preserved beneath `villes/<city>/`.

**Three SEPARATE mechanisms, each with ONE job — do NOT conflate them:**

1. **`post_parent` drives the URL hierarchy (and the breadcrumb).** The clean
   `_lean_seo_uri` is built from the WP `post_parent` ancestor chain. The mirror clones
   the canonical parent chain: the **branch-root** node → `post_parent = <geo post id>`;
   every **descendant** → `post_parent = the MIRRORED version of its canonical parent`
   (NOT the geo). This is the only URL driver.
2. **`location` and `service-reference` are TEMPLATE/SCHEMA REFERENCE fields — you just
   SET them; they do NOT drive the URL.** `location` (post-relation → `geo`) is the
   **city signal** the shared template and schema `areaServed` read; set it to the geo
   city on **every** node of the mirror. `service-reference` (post-relation → `exp`)
   points at the **canonical twin** the node mirrors. `geolocated` (switcher) turns the
   `is-located` behaviour on. See [§The three link fields](#the-three-link-fields).
3. **Reuse the mirrored page's own slug** — set each mirror node's `post_name` to the
   exact slug of the canonical node it mirrors. WordPress would otherwise auto-derive a
   slug from the "à \<ville\>" title. See
   [§Reuse the mirrored page's slug](#reuse-the-mirrored-pages-slug).

In the live `8388` data `post_parent` AND `location` both point at `2187` **coincidentally**
— they are separate mechanisms. The rule: `post_parent` = mirrored parent chain (geo
only for the branch root); `location` = the geo city (same on every node of the mirror);
`service-reference` = the canonical twin.

- **The canonical branch stays authoritative and UNTOUCHED.** The canonical service
  lives under the services landing page (klarc: post `4658` "Nos services", with
  top pillars `7267` Propriété intellectuelle, `7213` Management de l'innovation,
  `7214` Financement de l'innovation). It is the **read-only source** — you never
  edit it to make a city variant.
- **The geolocated mirror is a NEW `exp` post per canonical node.** The branch-root
  mirror gets `post_parent = <geo post id>`; each descendant mirror gets
  `post_parent = <the mirrored version of its canonical parent>`. Each is a real post
  — **NOT** a dynamic city-token template, and **NOT** a duplicate-and-publish of the
  canonical body.
- **Deep exp-under-exp is already live canonically.** Canonical `7214` "Financement
  de l'innovation" (parent `4658`) → child `8413` "Fiscalité de l'innovation" (parent
  `7214`) resolve to URIs `services/financement` and `services/financement/fiscalite`
  (deep exp-under-exp, VERIFIED live). A mirrored child under a mirrored parent works
  because `voxel_addon_hierarchy_config` has `exp` + `geo` both `nest_urls:true`,
  `depth_cap:20`, and **no per-CPT parent restriction** — any published post can parent
  any other. Re-rooting a depth-5 canonical branch under `villes/<city>/` reaches
  ~depth 6, well within `depth_cap:20`.
- **Concrete mirror under Toulouse (`geo` `2187`).** Cloning the `7214 → 8413` subtree:
  - "Financement de l'innovation à Toulouse" → `post_parent = 2187` (the geo post) →
    URI `villes/toulouse/financement`.
  - "Fiscalité de l'innovation à Toulouse" → `post_parent` = the NEW
    "Financement à Toulouse" post (**NOT** `2187`) → URI
    `villes/toulouse/financement/fiscalite`.
  So each mirrored node's `post_parent` = the mirrored version of its canonical parent,
  **except the branch-root node** whose parent = the geo post. It is **NOT** "every
  geo-child parents directly to geo".
- **Start at the top of the subtree** (a pillar or a branch root) and clone downward.
  Klarc `7214` Financement is a branch root (direct children `7203`/`9625`/`7230`/`8413`;
  30 descendants; tree depth 5) — a good seed because the whole subtree mirrors per city.
- **Live klarc precedent (currently FLAT — the deep mirror is the new, correct pattern).**
  Posts `8386`/`8387`/`8388` are `exp` posts parented **directly** to `geo` Toulouse
  (`2187`); `8416` under Lyon (`2186`). Their resolved `_lean_seo_uri` is
  `villes/toulouse/<slug>` (e.g. `8388` → `villes/toulouse/propriete-intellectuelle`).
  These existing geo-children are only **flat one-level** (all parent directly to
  `2187`); the DEEP mirror that preserves the parent chain is a more correct pattern
  not yet built. The canonical (non-geo) sibling is a **separate post** — no shared
  `post_parent`.

### The three link fields

Three distinct fields wire a mirror node. **`post_parent` ≠ `location`** even though they
coincide in the current live data — one drives the URL, the other is the city signal.

| Field | Type / target | What it does | What to set it to |
|---|---|---|---|
| `post_parent` | WP core (post id) | **Drives the URL + breadcrumb** (`_lean_seo_uri` ancestor chain) | the `geo` post for the **branch root**; the **mirrored parent** for every descendant |
| `location` | post-relation (`belongs_to_one`) → `geo`, relation key `services-locations` | **City signal** for the shared template + schema `areaServed` (NOT a URL driver) | the **geo city** post — the SAME on every node of the mirror (e.g. Toulouse `2187`) |
| `service-reference` | post-relation (single) → `exp` | **Canonical twin** the template references | the **canonical source** node this mirror clones (e.g. `7214`) |
| `geolocated` | switcher | enables the `is-located` condition on `location` (`geolocated=1`) | **on** for a geo-child |

Verified live: `8386`/`8387`/`8388` all have `location` → `[2187]`; canonical `7214` has
`location = []` (empty). That empty-on-canonical property is exactly what makes the
`location`-sourced schema `areaServed` (below) resolve to the city **only** for geo-children.

### Reuse the mirrored page's slug

**Reuse the canonical node's exact slug** — set each mirror node's `post_name` to the
same slug as the canonical page it mirrors (`financement`, `fiscalite`, …). This is
safe because slug uniqueness is **scoped by `post_parent`**: the mirror lives under a
different parent chain, so the full permalink differs even with an identical slug
(`services/financement/fiscalite` for the canonical vs
`villes/toulouse/financement/fiscalite` for the Toulouse mirror). WordPress does **not**
auto-suffix the slug (`-2`) because there is no collision within the same parent, and
the deep URI stays clean.

You must set `post_name` **explicitly**, though: left alone, WordPress derives the slug
from the *title*, so "Fiscalité de l'innovation à Toulouse" → `fiscalite-de-l-innovation-a-toulouse`,
which yields `villes/toulouse/financement/fiscalite-de-l-innovation-a-toulouse` instead
of the intended `…/fiscalite`. Setting `post_name` to the canonical slug is exactly what
the existing `8388` did (title "Propriété intellectuelle à Toulouse", `post_name`
`propriete-intellectuelle`). The rule is simply: **copy the mirrored page's slug**, don't
invent a new one.

## Scope vs the local-SEO checklist

The SEO SSOT branch *"The business has complete local SEO optimization"* has 12
subsections. The derive pipeline **owns the in-page rows**; the off-page rows are
**surfaced so nothing is dropped**, then handed to operational (GBP / citations /
reviews) work outside a page build.

| # | Subsection | Scope |
|---|---|---|
| a | Local schema markup is complete with correct industry subtypes | **in-page** |
| b | Location pages have unique, high-quality content and correct structure | **in-page** |
| c | NAP consistency (name/address/phone) | advisory (off-page) — on-page half is footer NAP + `tel:`; GBP side → see claude-seo seo-local / seo-maps |
| d | GBP descriptive content | advisory (off-page) → see claude-seo seo-local / seo-maps |
| e | GBP media | advisory (off-page) → see claude-seo seo-local / seo-maps |
| f | GBP identity / categorization | advisory (off-page) → see claude-seo seo-local / seo-maps |
| g | GBP features / attributes | advisory (off-page) → see claude-seo seo-local / seo-maps |
| h | Citation coverage across directories | advisory (off-page) → see claude-seo seo-local / seo-maps |
| i | Local authority signals + internal linking | advisory (off-page); internal-linking half IS **in-page** → see claude-seo seo-local |
| j | Review signals | advisory (off-page) → see claude-seo seo-local / seo-maps |
| k | Strong on-page local SEO signals (title/H1 city, hours in HTML, `tel:`, contact engagement) | **in-page** |
| l | Multi-location architecture scales without cannibalisation (URL structure, ≤2 clicks, one page per location, 30+/50+ page-count triggers) | **in-page** |

The derive pipeline is **accountable for the in-page rows** (a, b, i-internal, k, l);
the off-page rows are surfaced so nothing is dropped but are operational work outside
a page build. Cross-branch page criteria this flow must also satisfy: the
**doorway / mad-libs** ban (branch *"Programmatic and at-scale pages…"*), the
**≥500-word** location-page bar (branch *"…high-quality content…"*), and the
**30+/50+ location-page sitemap thresholds** (branch *"…XML sitemap…"*) as review
triggers when mirroring a subtree × cities.

## The uniqueness model (anti-doorway)

**This is the core section.** The `exp` single template (klarc post `2033`) is
**shared** across every service — content is NOT per-post Elementor. So per-city
uniqueness CANNOT come from the template; it **must come from Voxel FIELD values** on
the geo-child post. These are the geo-child's **OWN content fields** — the SAME real
`exp` fields the canonical service uses, just **written distinctly per city** (the
shared template renders them). There is **no** `city_intro`/`local_photos`/
`area_testimonials`/`local_faq` field — use the REAL `exp` fields that carry uniqueness:

| Field key | Voxel type | required | What it carries (write it for THIS city) |
|---|---|---|---|
| `h1` | text | **yes** | The city-specific H1 (distinct from the canonical H1) |
| `hook` | text | **yes** | A city accroche/teaser distinct from the canonical hook → meta description + section subtitle |
| `description` | texteditor | **yes** | The city body — why THIS service in THIS city; the anti-thin ≥500-word body |
| `faq` | repeater | **yes** | City-market FAQ rows (renders via the template; emits `FAQPage` only where the schema config already reads `meta:faq`) |
| `conversion-*` | texteditor (problem / stakes / solution …) | **yes** | The conversion narrative (problem/stakes/solution) written for the city |

**Uniqueness = writing these REAL fields distinctly per city.** The shared template
renders `h1`/`hook`/`description`/`faq`/`conversion-*`; authoring them with genuine
city-specific copy (not a mad-libs city token) is what defeats the swap test.

**The swap test (hard gate — checklist Critical).**

> **If swapping the city name leaves the content coherent, it is a doorway page.**

A geo-child whose only per-city token is the city name in a mad-libs sentence is a
doorway page — the exact pattern the *"Programmatic and at-scale pages…"* branch bans.
The bar is **>60% unique content** vs the canonical sibling and **≥500 words** of
genuine city-specific body (checklist branch *"…high-quality content…"*). A geo-child
that fails the swap test is not publishable — deepen the fields or do not create it.

**Page-count triggers (checklist subsection l).** When mirroring a subtree × cities,
treat **30+** geo-child location pages as a review trigger and **50+** as a
justification gate: at that scale the *"…XML sitemap…"* and cannibalisation criteria
demand a documented reason that every page is a distinct, non-thin local page and not
scaled doorway output.

## Schema: signal the city via the `location` relation

**The verified gap.** `lean_seo_schema:exp` hardcodes
`"areaServed": "area_served:site_branches"`:

```json
{
  "@graph": [
    {
      "@type": "Service",
      "@id": "@ref:self#service",
      "name": "post:title",
      "description": "seo:desc",
      "url": "post:permalink",
      "provider": "@ref:site#organization",
      "areaServed": "area_served:site_branches"
    },
    {
      "@type": "FAQPage",
      "@require": "meta:faq",
      "mainEntity": { "@each": "meta:faq", "@type": "Question", "name": "row:question" }
    }
  ]
}
```

`area_served:site_branches` resolves the **org's branches** relation and **ignores the
per-service `location` entirely** — so a geo-child `exp` still emits org-wide
`areaServed`, NOT its city. That is the doorway / swap-test risk in schema form: the
LocalBusiness signal does not match the URL.

**The fix — source `areaServed` from the `location` relation (NOT a hierarchy gate).**
The immediate `post_parent` of a descendant is another `exp` (its mirrored parent), not
the geo — so a `hierarchy:parent.geo-city` gate is WRONG for this model. The correct,
simpler source is the per-service `location` relation, which is **empty on canonical
services** and **set to the geo city on geo-children** — so it self-selects with **no
`@require` gymnastics**:

```json
{
  "@graph": [
    {
      "@type": "Service",
      "@id": "@ref:self#service",
      "name": "post:title",
      "description": "seo:desc",
      "url": "post:permalink",
      "provider": "@ref:site#organization",
      "areaServed": {
        "@type": "Place",
        "name": "relation_field:location.geo-city"
      }
    },
    {
      "@type": "FAQPage",
      "@require": "meta:faq",
      "mainEntity": { "@each": "meta:faq", "@type": "Question", "name": "row:question" }
    }
  ]
}
```

`relation_field:location.geo-city` reads a field from the **first related post through
relation `location`** (per [`lean-seo-schema.md`](lean-seo-schema.md) §Source grammar):
it resolves geo `2187`'s `geo-city` = `"Toulouse"` on a geo-child, and **nothing** on a
canonical service (empty `location`), where the object-pruning rule then drops the empty
`Place`. No `hierarchy:parent`, no `@require`, no negated gate.

- **Convenience alternative (klarc):** `"areaServed": "area_served:location"` returns the
  whole `Place` from the geo (klarc resolver
  `plugins/custom/lean-seo/modules/schema/sources/area-served.php`, which for a real
  relation field calls `lean_seo_get_related_ids($post_id,'location')` → the geo post →
  derives City/Region from `geo-city`/`geo-region`/`geo-location`). It is a site-specific
  source **not** in the `lean-seo-schema.md` grammar table, so **prefer the portable
  `relation_field:location.geo-city` inside a `Place`** above; use `area_served:location`
  only where the klarc resolver is confirmed present.

**Caution — don't blanket-break canonical `areaServed`.** Because the source is the
`location` field (empty on canonical services), a canonical service simply gets **no
city `areaServed`** from this source — which is correct. If the org-wide
`area_served:site_branches` is still wanted as the canonical fallback, keep it as the
base and note that a service carrying a `location` should override to its city — but the
SIMPLE correct answer is: **source `areaServed` from `location`.**

## URL nesting rationale

The geo-child `exp` **intentionally nests** via `post_parent` — resolved
`_lean_seo_uri = villes/<city>/<parent-slug>/<child-slug>`, built from the WP
`post_parent` **ancestor chain** (`nest_urls:true`, cross-CPT nesting confirmed in
`voxel_addon_hierarchy_config`: `exp` + `geo` both `nest_urls:true`, `depth_cap:20`,
no per-CPT parent restriction). Because the mirror clones the canonical parent chain
(only the branch root attaches to the geo), a two-level branch resolves e.g.
`villes/toulouse/financement/fiscalite`. Each node's **`post_name` must be set to the
mirrored page's own slug** (see [§Reuse the mirrored page's slug](#reuse-the-mirrored-pages-slug)) —
the differing parent chain keeps the full permalink unique, so an identical slug is safe
and correct; only the auto-derived "à \<ville\>" title slug would break the URI. This is the **opposite** of the
flat-URL rule in
[`seo-defined-terms.md`](seo-defined-terms.md) §Flat URLs, which BANS nesting for
glossary terms. The distinction is real vs grouping: a `geo` parent is a genuine
place hierarchy (city → service-in-city), so nesting *is* the correct semantics; a
term category is grouping, so nesting it would falsely imply hierarchy. A future
reader must NOT "flatten" this geo nesting by copying the defined-terms precedent.

## Metadata (Route M) — title + meta must be city-aware

The geo-child `<title>` and meta description **must incorporate the city**. The
shared template already renders a city-aware **breadcrumb** (see below), but the
`<title>` and `<meta name="description">` come from lean-seo Meta, and a title/meta
that is identical to the canonical sibling is **the highest-signal doorway tell** —
breadcrumb-only city-awareness is not enough. Author a city-aware `%token%` template
that references the parent city (via `%vx(@post(parent.title))%` or a city field),
per [`../../workflows/settings.md`](../../workflows/settings.md) §Route M. Example
title: `%title% à %vx(@post(parent.title))% %sep% %sitename%`; description sourced
from the city `hook`, not the canonical hook.

## E-E-A-T + internal linking

- **E-E-A-T:** same principle as [`seo-defined-terms.md`](seo-defined-terms.md) §E-E-A-T —
  named `post_author`, cited sources, `dateModified`.
- **Geo internal-linking (the delta):** the geo-child links **up** to its `geo` city hub
  via the breadcrumb (automatic — the parent is the `geo` post) and **laterally** to
  sibling city services (other `exp` posts under the same `geo` parent). This is the
  **in-page half** of checklist subsection (i); the off-page authority half (citations,
  local links) is advisory → see claude-seo seo-local.

## Preflight

Preflight is the gated Phase 0 of [`../../workflows/geolocation.md`](../../workflows/geolocation.md);
the WHY for each check is inline in the sections below.

## CLI recipe

Only step 3 (the geo-specific `areaServed` schema) is the delta; every other step is a
standard mechanic deferred by pointer.

1. **Create/reparent** via [`../../workflows/cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md)
   (post shape) + [`../../workflows/curation.md`](../../workflows/curation.md)
   (create/reparent); don't invent a create verb. Backup per rule 6.
2. **City-aware title/meta** per [`../../workflows/settings.md`](../../workflows/settings.md)
   §Route M — city token from the `parent.title` / `location` geo-city.
3. **Schema (the delta)** — ADD the gated geo-child `areaServed`/`Place` node to the
   `exp` target; the geo-specific JSON is [§Schema: signal the city via the `location`
   relation](#schema-signal-the-city-via-the-location-relation).

   ```bash
   wpdev schema:set <site> exp @/tmp/exp-schema.json   # validates before persist
   ```
4. **Backfill + flush** per [`../../workflows/settings.md`](../../workflows/settings.md)
   §Route C — run after the whole subtree is parented (see the workflow Phase 3 ordering).
5. **Purge + verify** per [`lean-seo-purge.md`](lean-seo-purge.md) then
   `wpdev schema:validate-live <site>`.

## Per-geo-page completion checklist

The "what must be true" per node. The workflow's Phase 4 owns the "how to verify"
process (agent-browser render, curl `<script type="application/ld+json">` inspection);
this checklist is not a restatement of it. A geo-child is **not done** until every box
is true.

- [ ] `post_parent` = the **mirrored parent** (the `geo` post only for the branch root;
      the mirrored parent node for every descendant), published.
- [ ] `post_name` = the **mirrored page's own slug** (copied from the canonical node;
      set explicitly, not the auto "à \<ville\>" title slug).
- [ ] `location` relation set to the **geo city** post (same on every node of the mirror).
- [ ] `service-reference` relation set to the **canonical service** twin.
- [ ] `geolocated` switcher **on**.
- [ ] City-unique `hook` → meta description, distinct from canonical.
- [ ] `description` body ≥500 words / >60% unique vs canonical (passes swap test).
- [ ] Real content fields written distinctly per city — `h1`, `hook`, `description`,
      `faq`, `conversion-*`.
- [ ] City-aware `<title>` + meta description (Route M, city from parent); **NOT identical**
      to the canonical sibling's title/meta.
- [ ] Descendant live URL = `villes/<city>/<parent-slug>/<child-slug>` (branch root =
      `villes/<city>/<slug>`); breadcrumb shows the city
      (e.g. `Accueil > Villes > Toulouse > <service>`).
- [ ] Schema `areaServed` names the **city** via the `location` relation
      (`relation_field:location.geo-city`), not org-wide branches.
- [ ] Canonical branch (services landing page + descendants) **untouched** — its empty
      `location` yields **no** city `Place` from this source (canonical schema unchanged).
- [ ] `wpdev schema:validate-live` reports 0 errors; no doorway (swap test passes).

## Related

- [`seo-defined-terms.md`](seo-defined-terms.md) — the flat-URL counterpart (why terms do NOT nest)
- [`lean-seo-schema.md`](lean-seo-schema.md) — the schema DSL, `hierarchy:` scopes, `@require`/`@ref`
- [`lean-seo-metadata.md`](lean-seo-metadata.md) — the `%token%` title/description dialect (Route M)
- [`lean-seo-crawl-permalinks.md`](lean-seo-crawl-permalinks.md) — `_lean_seo_uri`, auto-parent, `permalink parent-backfill`
- [`../../workflows/geolocation.md`](../../workflows/geolocation.md) — the phased derivation workflow (owns Preflight/Phase 0, create-verb guidance, verify process)
- [`../../workflows/settings.md`](../../workflows/settings.md) — Route M / Route S / Route C process
- [`../../workflows/cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md) — post creation / reparent surface
- [`../../workflows/curation.md`](../../workflows/curation.md) — record create / reparent / field edits
- [`lean-seo-purge.md`](lean-seo-purge.md) — cache purge after permalink/schema changes
- [`voxel-tags.md`](voxel-tags.md) — `@post(parent.title)` and dynamic-tag syntax
