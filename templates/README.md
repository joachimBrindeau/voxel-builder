# Templates — reusable section-template store

Saved `_elementor_data` sections so a build agent starts a page from a composed hero/section instead of synthesizing every widget from scratch. This store reuses the [`examples/`](../examples/README.md) golden-fixture convention (Rule 1 of [`../references/core/rules.md`](../references/core/rules.md)) and extends it with a per-template `meta.yml` sidecar so an agent can pick a template without parsing JSON.

The EF widgets (`ef-card`, `ef-wrapper`, …) inside a `template.json` are convenience starting trees only — their **authoritative SSOT** is the committed `cli/src/generated/widget-schemas.json` (Rule 1, generated from `plugins/custom/elementor-framework/schemas/` and CI-gated against drift). When the SSOT and a template disagree, the SSOT wins. Use templates as starting trees, never as authoritative spec — they should be refreshed when the EF V4 schema churns.

## On-disk shape

One folder per template, keyed by its `id`, under the scope directory (`global/`, `sections/`, `pages/`):

```
templates/
├── index.md                       ← master catalog (3 scope tables)
├── README.md                      ← this file
├── global/                        ← header / footer (one active per site)
├── sections/                      ← reusable page parts — heroes seed here
│   └── hero-search-overlay/
│       ├── template.json            ← the _elementor_data snippet
│       ├── meta.yml                 ← sidecar metadata (schema below)
│       └── preview.png              ← optional
└── pages/                         ← full-page compositions
```

- **`template.json`** — a bare `_elementor_data` object (a single self-contained container subtree), **raw UTF-8, NOT escaped**. Same rule the `examples/*.json` fixtures follow: the on-disk file is the tree an agent splices, not a JSON-in-a-string blob.
- **`meta.yml`** — the sidecar (schema below). Lets an agent choose a template on `type`/`tags`/`widgets` without reading the JSON.
- **`preview.png`** — optional rendered thumbnail. Absent is fine; `preview.png` generation is deferred (see §Empty slots).

## `meta.yml` schema

Every stored template ships a `meta.yml` with these keys:

```yaml
id: hero-search-overlay        # matches the folder name; the catalog key
scope: section                 # global | section | page
type: hero                     # section archetype (hero, features, cta, header, footer, …)
name: "Search overlay hero"    # human-readable label for the catalog
tags: [search, overlay, geo]   # free-form discovery tags
widgets: [ef-wrapper, ef-card] # elType/widgetType list present in template.json
dtags_used:                    # the universal Voxel dynamic tags kept live in the JSON
  - "@post(title)"
  - "@post(:excerpt)"
requires_plugins:              # plugins the template's widgets need
  - elementor-framework
  - voxel
source_note: "hero subtree, source node elements[0] of <page>; sanitized per placeholder policy"
breakpoints: [desktop, tablet, mobile]   # responsive envelopes the tree carries
```

Key reference:

| Key | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Kebab-case identifier; **must equal the folder name** and the `index.md` row id. |
| `scope` | enum `global\|section\|page` | yes | Cardinality tier — `global` = one active per site, `section` = many per page, `page` = full composition. |
| `type` | string | yes | Section archetype (`hero`, `features`, `cta`, `header`, `footer`, …). |
| `name` | string | yes | Human-readable label surfaced in `index.md`. |
| `tags` | string[] | yes | Free-form discovery tags. |
| `widgets` | string[] | yes | The `elType`/`widgetType` values present in `template.json`. |
| `dtags_used` | string[] | yes | The universal Voxel dynamic tags kept live in the JSON; every other string is Lorem Ipsum. Must equal the dtag-set actually in `template.json`. |
| `requires_plugins` | string[] | yes | Plugins whose widgets the tree depends on (`elementor-framework`, `voxel`, …). |
| `source_note` | string | yes | Provenance: the source node id/selector the subtree was extracted from and any sanitization note. |
| `breakpoints` | string[] | yes | Responsive envelopes the tree carries (`desktop`, `tablet`, `mobile`). |
| `location` | enum `header\|footer` | **only when `scope: global`** | Theme Builder location for a global template. Omit for `section`/`page`. |

## Naming rule

Folder / `id` = **`<type>-<variant>`**, kebab-case, **no numeric suffixes**.

- Good: `hero-search-overlay`, `hero-city-geo`, `cta-newsletter-band`
- Bad: `hero-1`, `hero_search`, `HeroSearchOverlay`

The variant describes the distinguishing trait, never a counter.

## SSOT wins

Restated from [`../examples/README.md`](../examples/README.md) so it holds for templates too: **when the SSOT and a template disagree, the SSOT wins. Use templates as starting trees, never as authoritative spec** — they should be refreshed when the EF V4 schema churns. The authoritative shape always lives in `cli/src/generated/widget-schemas.json`; a `template.json` is a convenience tree, never the spec.

## Refresh / migrate workflow

Templates must stay valid as the EF V4 schema evolves (codegen churn). The migration story has two existing primitives used for their real jobs:

**Detect drift** with **`elementor:lint`'s schema-aware `validateNode`** — it reads the `widget-schemas.json` *content* and flags `type-mismatch`, `unknown-prop`, `v3-shape`, `enum-violation`, and malformed responsive envelopes over every `templates/**/template.json`. This is the CI drift gate: when codegen regenerates the schema, any template that no longer conforms turns red.

> ⚠️ The drift signal is the **`elementor:lint` validator**, **never** `elementor:normalize`. `elementor:normalize` does fixed structural healing only (base props, responsive envelopes, null-prop drop) and does **not** reconcile per-prop against the schema — it silently misses renamed props, schema-removed props, and new required nested cells. So a normalize diff/no-op is **not** a valid drift check.

**Refresh** a flagged template through the same path live posts use:

```bash
# 1. structural survivability pass (NOT the drift gate — healing only)
./wpdev elementor:normalize <template.json> <template.json>
# 2. import the tree into a temp post with --save → runs the versioned EF_Migrator steps + $doc->save()
./wpdev elementor:import <site> <postId> --save
# 3. export the migrated tree back over template.json
./wpdev elementor:export <site> <postId>   # locate the newest backups/elementor/<site>/<postId>-<ts>.json → back to template.json
```

Order: **normalize → `elementor:import <site> <postId> --save` → re-`elementor:export`.** Re-run the `elementor:lint` gate afterward; it must be green. Bump the plugin version and add a CHANGELOG entry when templates are refreshed.

## Empty slots

`global/` and `pages/` carry a `.gitkeep` and are **documented-but-empty for v1**. The scope shape exists so agents know where those templates land, but seeding them is deferred to a follow-up (per the plan's Scope Boundaries):

- **`global/`** — header/footer templates (one active per site, `location: header|footer`). Fill when a saved global becomes reusable across sites.
- **`pages/`** — full-page compositions. Fill when a whole-page starting tree is worth storing.

Only `sections/` is seeded in v1. `preview.png` generation is likewise deferred.

## Adding a template

1. Create `templates/<scope>/<id>/` with `template.json` (bare `_elementor_data`, raw UTF-8) + `meta.yml`.
2. Add one row to the matching table in [`index.md`](index.md).
3. Run the `elementor:lint` drift gate over the new `template.json` — it must be green.
