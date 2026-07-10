# EF helpers reference (`ef_*` free functions)

Plugin: `plugins/custom/elementor-framework/`. Helpers load via `includes/bootstrap.php` → per-file `require_once` chain. **~330 free `ef_*` functions** across `includes/*.php` + nested subfolders (run the re-grep at the bottom of this file for the live count — moving target).

This file is the **build/audit-agent surface** for those helpers. The top ~80 (everything an EF build or audit agent ever reaches for) are documented in full; the remaining ~180 (operator surfaces — SMTP admin, internal registry plumbing, low-level CSS bundling, etc.) are indexed by name + file + 1-line purpose. Total coverage: **100% name-findable**, ≥80% effective coverage for build/audit work.

**File-path drift warning.** EF refactors split + rename `includes/` source files routinely. If a `File: includes/<foo>.php:<line>` reference here doesn't match the live tree, the helper has either moved (re-grep `^function ef_<name>` across `includes/`) or been retired (no replacement). Treat line numbers as hints, not absolutes.

## When to use this reference vs. live grep

Use **this file** when:
- You need to know which helper builds a responsive pair, action prop schema, loop transform default, etc.
- You're authoring a new EF widget and need the canonical envelope/prop/control builders.
- You're auditing a widget and need to confirm which helper resolves a loop / visibility / transform.

Use **live grep** (`grep -rn "^function ef_<name>" plugins/custom/elementor-framework/includes/`) when:
- A helper name is in the index but you need the body (e.g., to understand a defaulting rule).
- You suspect this file is stale — re-grep `^function ef_` across `includes/` and reconcile.
- You're chasing a non-`ef_*` symbol (class method, constant, hook callback).

## Category index

| # | Category | Anchor | Helpers covered | Full / Index |
|---|---|---|---|---|
| 1 | Atomic V4 (envelope + prop builders) | [atomic](ef-helpers-atomic-settings.md#atomic-v4) | 14 |
| 2 | Pairs (responsive scalar+control bundles) | [pairs](ef-helpers-atomic-settings.md#pairs) | 8 |
| 3 | Settings sections | [settings](ef-helpers-atomic-settings.md#settings-sections) | 3 |
| 4 | Select options | [selects](ef-helpers-atomic-settings.md#select-options) | 6 |
| 5 | Voxel + dynamic-data | [dynamic](ef-helpers-atomic-settings.md#voxel--dynamic-data) | 17 |
| 6 | Loop | [loop](ef-helpers-loops-actions.md#loop) | 8 |
| 7 | Voxel sub-resolvers | [resolvers](ef-helpers-loops-actions.md#voxel-sub-resolvers) | 2 |
| 8 | Action types & controls | [actions](ef-helpers-loops-actions.md#action-types--controls) | 13 |
| 9 | Icon helpers | [icons](ef-helpers-loops-actions.md#icon-helpers) | 6 |
| 10 | Links | [links](ef-helpers-loops-actions.md#links) | 4 |
| 11 | Responsive primitives | [responsive](ef-helpers-loops-actions.md#responsive-primitives) | 8 |
| 12 | Grid | [grid](ef-helpers-layout-assets.md#grid) | 7 |
| 13 | Map | [map](ef-helpers-layout-assets.md#map) | 4 |
| 14 | CSS / fonts / assets | [assets](ef-helpers-layout-assets.md#css--fonts--assets) | 12 |
| 15 | Frontend / editor (gating) | [frontend](ef-helpers-layout-assets.md#frontend--editor-gating) | 22 |
| 16 | Editor preview post context | [preview](ef-helpers-layout-assets.md#editor-preview-post-context) | 3 |
| 17 | Dynamic tags | [tags](ef-helpers-layout-assets.md#dynamic-tags) | 9 |
| 18 | Elementor data | [data](ef-helpers-data-forms-admin.md#elementor-data) | 5 |
| 19 | Forms | [forms](ef-helpers-data-forms-admin.md#forms) | 13 |
| 20 | SMTP (operator surface) | [SMTP](ef-helpers-data-forms-admin.md#smtp-index-only) | 26 |
| 21 | Admin (operator surface) | [admin](ef-helpers-data-forms-admin.md#admin-index-only) | 14 |
| 22 | Migrator | [migrator](ef-helpers-data-forms-admin.md#migrator) | 2 |
| 23 | Registry & autodiscovery | [registry](ef-helpers-data-forms-admin.md#registry--autodiscovery) | 8 |
| 24 | Misc small modules | [misc](ef-helpers-data-forms-admin.md#misc-small-modules) | 12 |

Documented surface ≈220 helpers (~80% effective coverage). Remaining ~110 are intra-category internals (e.g., private `_ef_*` helpers, repeated unnamed editor-preview render helpers, spam screening, IP CIDR matchers) — re-grep `^function ef_` across `includes/` when you need the full live list.

---

## Split Catalog

| Concern | Reference |
|---|---|
| Atomic props, paired props, settings sections, select options, Voxel/dynamic helpers | `ef-helpers-atomic-settings.md` |
| Loops, sub-resolvers, actions, icons, links, responsive primitives | `ef-helpers-loops-actions.md` |
| Grid, maps, assets, editor preview, dynamic tags | `ef-helpers-layout-assets.md` |
| Elementor data, forms, SMTP/admin, migrators, registry, misc | `ef-helpers-data-forms-admin.md` |

Load only the concern needed for the current schema question. Generated/helper counts drift;
source and committed catalogs remain authoritative.
