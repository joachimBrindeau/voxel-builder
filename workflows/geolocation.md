# Geolocation Derivation Workflow

Derive a canonical `exp` service into a **geolocated deep mirror** re-rooted under a
`geo` city post — a structural clone of the canonical subtree where the branch root
attaches to the `geo` post and each descendant mirrors its canonical parent, with a
manual canonical slug, `location` + `service-reference` reference fields, city-unique
content, and `location`-sourced schema. The knowledge (the three-mechanism model, the
`location`-relation `areaServed` source, the swap test, the URL rationale) lives in
[`../references/voxel/seo-geolocation-pages.md`](../references/voxel/seo-geolocation-pages.md);
this file is the numbered, gated process.

## When to use

- "Geolocate a service", "create a city version of a page", "derive a geolocated
  service", "page service à `<ville>`", "mirror a service under a city".
- A canonical `exp` service exists and you want a per-city variant that ranks locally
  without becoming a doorway.

## Entry criteria

1. A **canonical `exp` service** exists (a service post under the services landing
   page — klarc: `4658` "Nos services" with pillars `7267`/`7213`/`7214`).
2. A **target `geo` post** exists and is published (klarc: Toulouse `2187`, Lyon `2186`).
3. **Voxel + lean-seo + the Hierarchy module** are active with cross-CPT `nest_urls`
   (`voxel_addon_hierarchy_config`: `exp` + `geo` `nest_urls:true`).

If any input is missing, halt — do not enter Phase 0.

## Phase 0 — Preflight & baseline

**Entry:** Entry criteria met.

**Actions:**

1. **Confirm the geo target + cross-CPT nesting.** Verify the `geo` post is published
   and `voxel_addon_hierarchy_config` allows an `exp` post to parent under it (no
   per-CPT parent restriction; `depth_cap` not exceeded). Confirm the `geo` post
   carries a `geo-city` field and the `exp` CPT has the `location` /
   `service-reference` / `geolocated` fields (the city signal read in Phase 3).
2. **Capture a claude-seo BASELINE on the LIVE canonical page — MANDATORY, gated
   (`claude-seo-baseline`).** This is not advisory: no authoring starts until the baseline
   gap-list file exists. Follow [`../references/voxel/claude-seo-authoring.md`](../references/voxel/claude-seo-authoring.md) §1:
   1. Resolve the installed `seo-local` skill through the host's skill catalog as
      described in the authoring reference; do not assume a fixed cache path.
   2. Invoke it natively when supported. Otherwise **read** its resolved `SKILL.md`
      (and optionally `seo-page` / `seo-schema`) and follow it inline. Record which
      method and source path were used; do not claim native execution for a read fallback.
   3. Apply its Analysis Dimensions to the **live canonical** service URL (READ-ONLY: fetch
      the URL, write a `.md` report). Write the report to `/tmp/BASELINE-<canonical-slug>.md`.
   4. Note the **gap list** — areaServed/doorway/uniqueness/title-signal issues the derive
      pipeline must close.

**Exit:** Geo target + cross-CPT nesting confirmed; `/tmp/BASELINE-<canonical-slug>.md`
exists with a non-empty gap list (`claude-seo-baseline` Critical — a docs-only or advisory
mention does NOT satisfy it).

## Phase 1 — Derivation plan (plug into page-planning §2a–§2g)

**Entry:** Phase 0 passed.

**Actions:**

1. **Field-inventory the canonical `exp`** per [`page-planning.md`](page-planning.md) §2a
   (Field Inventory) — sample multiple posts, don't classify from one. Geo delta:
   inventory the **SUBTREE**, mapping each node → its mirrored parent (not just the one
   canonical post).
2. **Walk the canonical SUBTREE and plan a structural clone.** The derivation is a
   **deep mirror**, not one flat node: map **each canonical node → its mirrored parent**
   (the **branch root** → the `geo` post; every **descendant** → the mirrored version of
   its own canonical parent). For each node, plan the **reference wiring** (`location` →
   the geo city; `service-reference` → the canonical node) and the **slug reuse**
   (`post_name` = the mirrored canonical node's own slug — the differing parent chain
   keeps the permalink unique). See the reference §The derivation model + §The three
   link fields.
3. **Decide seed vs uniqueness set, and author the uniqueness set through claude-seo
   methodology — gated (`content-methodology`).** Structural fields (title, canonical body
   shape) are the **seed**; the **MANDATORY uniqueness set** — the REAL `exp` fields written
   distinctly per city: `h1`, `hook`, `description` (≥500-word body), `faq`, and the
   `conversion-*` fields — comes from the reference's §The uniqueness model. Author them by
   **following claude-seo content methodology via Read-fallback** per
   [`../references/voxel/claude-seo-authoring.md`](../references/voxel/claude-seo-authoring.md) §2
   (Read `seo-content-brief/SKILL.md` + `seo-local/SKILL.md`): enforce keyword placement, the
   meta-length bound (the `hook`/description-source field ≤ `LEAN_SEO_DESC_LIMIT` 155, target
   120–152), a **stated information-gain** vs the canonical (the genuine local specifics — real
   programmes/ecosystem, never fabricated), E-E-A-T, and the ≥500-word / >60 %-unique bar. These
   are what defeat the swap test. Ad-hoc prose that skips this fails `content-methodology`.
4. **Subtree-scope decision.** Choose single leaf (one service × one city) vs mirroring
   the N-node subtree × cities. Reference the **30+/50+ page-count triggers** (checklist
   subsection l): 30+ geo-child pages is a review trigger, 50+ a justification gate.
5. Run the plan through page-planning §2a→§2g (inventory → SSOT → archetype → blueprint
   → adversarial fan-out → reconciliation → computed §2g gate).

**Exit:** A **gated plan doc** exists per [`../references/core/rules.md`](../references/core/rules.md)
rule 8 (§2g gate green); the node→mirrored-parent map, reference wiring, per-node slug,
uniqueness set, and subtree scope are decided. The `claude-seo-baseline` gap-list is captured
(Phase 0) and the uniqueness set is authored through claude-seo methodology
(`content-methodology`) — both are Critical criteria in the §2e adversarial fan-out.

## Phase 2 — Build the geo-child exp

**Entry:** Phase 1 plan gated green.

**Actions:**

1. **Snapshot before mutation** (rule 6): if touching an existing template, run the
   revisions-prune snapshot first.
2. **Build the subtree PARENT-BEFORE-CHILD.** Create the **branch root** under the
   `geo` post (`post_parent = <geo id>`), then each **descendant** under its
   already-created **mirrored parent** (`post_parent = <that mirrored parent's id>`) —
   never all-to-geo. Use the CPT lifecycle / curation surface
   ([`cpt-lifecycle.md`](cpt-lifecycle.md) for the post shape,
   [`curation.md`](curation.md) for create/reparent; do NOT invent a create verb).
3. **For EACH node, wire it fully:**
   - set `post_name` = the **mirrored page's own slug** (copy the canonical node's slug;
     set explicitly — NOT the auto "à \<ville\>" title slug — the different parent chain
     keeps the full permalink unique);
   - set the `location` relation → the **geo city** post;
   - set the `service-reference` relation → the **canonical twin** node;
   - set the `geolocated` switcher **on**;
   - author the REAL content fields distinctly per city (`h1`, `hook`, `description`,
     `faq`, `conversion-*`) from the Phase-1 uniqueness set.
4. The **shared template renders it** (klarc `2033`); the breadcrumb auto-resolves to
   the city via `@post(parent.title)` — **no template change needed**.

**Exit:** The subtree exists parent-before-child; a descendant's
`_lean_seo_uri = villes/<city>/<parent-slug>/<child-slug>`; every node has `post_name`
= the mirrored canonical node's slug, `location` + `service-reference` relations set,
`geolocated` on, and the uniqueness-set fields populated (passes the swap test on inspection).

## Phase 3 — SEO wiring

**Entry:** Phase 2 post built.

**Actions:**

1. **Route S — geo-child schema.** Source the Service node's `areaServed` from the
   `location` relation per the reference §Schema — `relation_field:location.geo-city`
   inside a `Place` (or the klarc convenience `area_served:location`), **NOT** a
   `hierarchy:parent` gate and **NOT** `area_served:site_branches`. Empty `location` on
   canonical services means they emit no city node — no `@require` needed.
   `wpdev schema:set <site> exp @/tmp/exp-schema.json`.
2. **Route M — city-aware title/meta.** Author a `%token%` title/description that
   incorporates the city (from `parent.title` / a city field) — [`settings.md`](settings.md)
   §Route M. Identical title/meta vs canonical is the top doorway tell.
3. **Route C — permalink.** Backfill + flush per [`settings.md`](settings.md) §Route C, run
   **AFTER the whole subtree is parented** (the delta vs the standard: the deep
   ancestor-chain requires the subtree parented first); verify a descendant's
   `_lean_seo_uri = villes/<city>/<parent-slug>/<child-slug>`.

**Exit:** Schema validates, the nested URL resolves, and the title/meta are
city-aware.

## Phase 4 — Verify & gate

**Entry:** Phase 3 wiring done.

**Actions:**

1. **Browser verification (rule 7).** Run the `agent-browser` protocol
   ([`../references/verification/browser.md`](../references/verification/browser.md))
   against the **live geo-child** — screenshot + read, assert URL, breadcrumb city,
   city-aware title/meta, and `areaServed` = city in the emitted JSON-LD.
2. **Re-run claude-seo as the acceptance gate.** Re-run the claude-seo `seo-local` /
   `seo-schema` analysis against the **NEW geo-child URL** and compare to the Phase-0
   baseline. **DOCUMENTED-BUT-DEFERRED:** when executed against a live site, run this
   here; it **cannot run until the page exists**, so on a docs-only pass it is recorded,
   not executed.
3. **Swap test** — confirm swapping the city name breaks coherence.

**Exit:** Browser verified + (on live execution) claude-seo re-audit clean +
swap test passes.

## Must-NOT

- **MUST NOT modify the canonical branch** (the services landing page `4658` + its
  descendants) — it is the read-only source.
- **MUST NOT parent every mirrored node directly to `geo`** — only the **branch root**
  attaches to the geo; every descendant parents under its **mirrored parent**.
- **MUST NOT leave the auto "à \<ville\>" slug** — set `post_name` to the mirrored
  page's own slug (copy the canonical node's slug) on every node, or the deep URI breaks.
- **MUST NOT confuse the `location` relation** (template/schema city signal) **with
  `post_parent`** (URL hierarchy) — they are separate mechanisms that only coincide in
  the current live data.
- **MUST NOT source `areaServed` from `site_branches`** for a geo service — source it
  from the `location` relation (`relation_field:location.geo-city`).
- **MUST NOT emit org-wide `areaServed`** on a geo-child — it must name its city.
- **MUST NOT create swap-only doorway pages** — a geo-child that survives the swap test
  is not publishable.
- **MUST NOT invent a `/claude-seo` tool call.** Invoke the routed installed skill by
  name when the host supports it, or resolve and read its `SKILL.md` through the
  documented fallback.
- **MUST NOT claim a claude-seo skill executed if it did not run.**

## Worked example — the Financement subtree → à Toulouse (two levels)

Illustrative thread mirroring the canonical `7214` "Financement" → child `8413`
"Fiscalité" subtree under `geo` Toulouse `2187`. See
[`../references/voxel/seo-geolocation-pages.md`](../references/voxel/seo-geolocation-pages.md)
§The derivation model for the node→parent mapping table (`post_parent` / `location` /
`service-reference` / `post_name` / URI); below is only the phase-by-phase application.

- **Phase 0** — baseline claude-seo `seo-local` against the live canonical
  `/services/financement`; note the org-wide-`areaServed` gap.
- **Phase 1** — field-inventory `7214`+`8413`; map each node → its mirrored parent; plan
  reference wiring + per-node slug; author the uniqueness set for Toulouse.
- **Phase 2** — parent-before-child: create Financement-à-Toulouse (`post_parent = 2187`)
  then Fiscalité-à-Toulouse (`post_parent` = the Financement-à-Toulouse post); on each,
  set `post_name`, `location` → `2187`, `service-reference` → the canonical twin,
  `geolocated` on; author `h1`/`hook`/`description`/`faq`/`conversion-*` for Toulouse.
- **Phase 3** — Service `areaServed` sourced from `relation_field:location.geo-city`
  (→ "Toulouse"); city-aware title `Financement de l'innovation à Toulouse …`; backfill
  the whole subtree → `_lean_seo_uri = villes/toulouse/financement/fiscalite`.
- **Phase 4** — browser-verify the live geo-children; **deferred** post-build claude-seo
  gate on `/villes/toulouse/financement/fiscalite`.

**This workflow does NOT build the live page here — the example is illustrative.**

## Related

- [`../references/voxel/claude-seo-authoring.md`](../references/voxel/claude-seo-authoring.md) — **route all SEO research + writing through claude-seo upstream** (Read-fallback; the `claude-seo-baseline` + `content-methodology` gates)
- [`../references/voxel/seo-geolocation-pages.md`](../references/voxel/seo-geolocation-pages.md) — the knowledge reference (field model, areaServed gate, swap test)
- [`page-planning.md`](page-planning.md) — the §2a–§2g gated planning sub-pipeline
- [`settings.md`](settings.md) — Route M / Route S / Route C process
- [`cpt-lifecycle.md`](cpt-lifecycle.md) — post creation / reparent surface
- [`../references/core/rules.md`](../references/core/rules.md) — rule 6 snapshot, rule 7 browser verify, rule 8 gated plan
- [`../references/verification/browser.md`](../references/verification/browser.md) — the `agent-browser` verification protocol
