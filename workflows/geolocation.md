# Geolocation Derivation Workflow

Derive canonical `exp` service into city-specific `exp` mirror under `geo`. Read
[`../references/core/rules.md`](../references/core/rules.md),
[`../references/core/criteria.md`](../references/core/criteria.md), and
[`../references/voxel/seo-geolocation-pages.md`](../references/voxel/seo-geolocation-pages.md)
before work.

## When to use

- Geolocate service.
- Create city version of page.
- Derive geolocated service.
- Mirror service under city.

## Entry criteria

1. Canonical `exp` source and target published `geo` post known.
2. Live site confirms cross-CPT hierarchy and `nest_urls` capability.
3. Live field catalog confirms fields and schema source keys before any write.
4. Canonical branch is read-only source.

Missing input: halt.

## Phase 0 — Preflight and baseline

**Entry:** Entry criteria met.

1. Read canonical service, target city hub, current hierarchy config, current Route M/S/C
   config, and current rendered canonical URL.
2. Confirm expected geo-child URL shape and whether target has `#localbusiness` schema
   fragment required by reference schema variant.
3. Dispatch installed claude-seo `seo-local`, optionally `seo-page` and `seo-schema`, as
   read-only analysis against **live canonical URL**. If host cannot dispatch it, resolve
   and read its `SKILL.md` through host skill catalog, then follow analysis inline.
   Record method and source path. Never claim native execution after read fallback.
4. Capture baseline gaps in a report: local relevance, city signal, title/meta, content
   uniqueness, schema, internal links. `seo-maps` may assess city context; advisory only.

**Exit:** Canonical baseline report exists. Geo target, nesting capability, and
schema-fragment prerequisite are evidenced. No page built.

## Phase 1 — Derivation plan

**Entry:** Phase 0 gate green.

1. Run the mandatory [`local-page-justification.md`](local-page-justification.md) research
   sub-pipeline for each service/location pair. Require dataset resolution and evidence gates
   to pass before treating its report as planning input.
2. Run relevant `page-planning.md` sections §2a–§2g: field inventory, SSOT read,
   archetype, blueprint, adversarial review, reconciliation, computed gate.
3. Mark seed data versus mandatory unique fields. Seed may preserve structural service
   facts. Author city-specific `h1`, `hook`, `description`, `faq`, and `conversion-*`
   from verified local evidence. Enforce reference bounds, 500-word body, >60% unique
   content, and swap test.
4. Decide scope: one service × city, or subtree × cities. At 30+ derived pages trigger
   review. At 50+ require documented distinct-value and cannibalisation justification.
   A blocked dataset, publication, similarity, or mutation gate from the justification
   sub-pipeline blocks the corresponding full geo-child mutation; only its explicit
   emergency neutralization contract may proceed independently.
5. Map canonical source ID, target geo ID, intended parent, expected URI, Route M/S/C
    changes, rollback snapshot, and read-back proof. Review verdict records candidate input
    file SHA-256. Reject verdict when current SHA differs. Substantive rewrite requires fresh
    review session unless exact SHA proves unchanged.

6. Keep GBP, citations, reviews, NAP operations, and local-link acquisition advisory;
   point owner to claude-seo `seo-local` / `seo-maps` rather than adding build steps.

**Exit:** §2g plan gate green. Plan proves unique city content and records page
scope, source owner, rollback, Route M/S/C changes, and verification assertions.

## Phase 2 — Build geo-child

**Entry:** Phase 1 gate green and mutation explicitly authorized.

1. Snapshot writable state per rule 6.
2. Create or reparent through [`cpt-lifecycle.md`](cpt-lifecycle.md) and
   [`curation.md`](curation.md). Do not invent a create command.
3. Set `post_parent` to target `geo`; write only approved city-specific field values.
   Shared template `2033` can render existing parent-city breadcrumb through
   `@post(parent.title)` when live template evidence confirms it.
4. Read stored values back. Canonical service remains unchanged.

**Exit:** Geo-child exists under target city. Stored content matches approved plan.
Canonical branch read-back proves unchanged.

## Phase 3 — SEO wiring

**Entry:** Phase 2 gate green.

1. Route S: configure two `Service` variants from
   [`../references/voxel/seo-geolocation-pages.md`](../references/voxel/seo-geolocation-pages.md#schema-two-node-variants-the-areaserved-gate).
   Geo-child uses parent local-business `areaServed`; canonical guard retains
   `area_served:site_branches`.
2. Route M: set city-aware `%token%` title and description using live-catalog-confirmed
   parent-city source.
3. Route C: backfill parent URI and flush only after hierarchy mutation. Confirm
   `_lean_seo_uri = villes/<city>/<service>`.

**Exit:** Stored Route M/S/C config reads back. Geo-child URL resolves with city
metadata and city `areaServed`; canonical service still has org-wide `areaServed`.

## Phase 4 — Verify and gate

**Entry:** Phase 3 gate green.

1. Run rule 7 browser verification on live geo-child: URL, breadcrumb city, H1, title,
   meta description, canonical, links, and JSON-LD `areaServed`.
2. Re-run claude-seo `seo-local` and `seo-schema` on geo-child URL. This is
   **documented-but-deferred** until live geo-child exists. Use capability language and
   same read-by-skill-path fallback as Phase 0.
3. Compare results to canonical baseline. Re-run swap test. Fail publication if city swap
   leaves copy coherent or schema/meta stays canonical.

**Exit:** Browser and rendered schema pass. On live execution, re-audit closes
baseline gaps. Docs-only work records deferred audit, never claims execution.

## Must-NOT

- Do not mutate canonical services branch.
- Do not create city-token-only or swap-only doorway pages.
- Do not claim claude-seo ran unless session evidence exists.
- Do not invent claude-seo command syntax. Dispatch capability when host supports it;
  otherwise read resolved `SKILL.md` and perform analysis inline.
- Do not turn off-page GBP, citations, reviews, NAP operations, or local-link work into
  page-build steps.
- Do not replace canonical schema with unconditional parent `areaServed` reference.

## Worked example — Financement de l'innovation → Toulouse

**On paper, not built.** Canonical `exp` `7214` (`/services/financement`) derives under
Toulouse `geo` `2187` as `/villes/toulouse/financement`.

1. **Phase 0:** Baseline claude-seo analysis targets live `/services/financement`.
   Record existing org-wide `areaServed`; no geo-child exists, so post-build audit is deferred.
2. **Phase 1:** Plan unique Toulouse H1, hook, 500+ word body, FAQ, conversion copy,
   Route M city metadata, and two schema variants. Confirm city `#localbusiness` fragment.
3. **Phase 2:** When authorized, create new `exp` child with `post_parent = 2187`.
   Shared template breadcrumb can resolve `@post(parent.title)` as Toulouse. Do not edit `7214`.
4. **Phase 3:** Geo-child Service variant resolves Toulouse from
   `@ref:hierarchy:parent#localbusiness`; canonical `7214` variant keeps
   `area_served:site_branches`. Backfill expected URI `villes/toulouse/financement`.
5. **Phase 4:** Browser and claude-seo re-audit target
   `/villes/toulouse/financement` only after page exists. Mark deferred in paper run.

## Related

- [`../references/voxel/seo-geolocation-pages.md`](../references/voxel/seo-geolocation-pages.md)
- [`page-planning.md`](page-planning.md)
- [`settings.md`](settings.md)
- [`cpt-lifecycle.md`](cpt-lifecycle.md)
- [`curation.md`](curation.md)
