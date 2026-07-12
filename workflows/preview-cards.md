# Preview Cards Workflow

Create a complete Voxel CPT card family through one SSOT split:

- `wpdev voxel:cards` owns generated EF envelopes, template posts, Voxel registration,
  duplicate/stale cleanup, Elementor save/CSS, and large-as-main assignment.
- The LLM owns semantic composition after scaffold: field selection, content density,
  media and alt bindings, actions, visibility, language, and site focus.

Never expand `card-bindings.ts` into a site-content policy engine. Command output is a
valid transport scaffold, not the final editorial card design.

## Phase 1 — Inventory

**Entry:** site and CPT key known.

1. Read `references/core/rules.md`, `references/core/criteria.md`, and
   `references/ef/card-scaffolding.md`.
2. Run `wpdev voxel:fields`, `wpdev voxel:sample`, `wpdev voxel:templates`, and
   `wpdev voxel:cards --audit` for the CPT.
3. Classify fields by card use: identity, summary, logo, cover, taxonomy/status pills,
   location, relation/count, trust proof, contact/action destination, and fallback.

**Exit:** field-to-card matrix names every chosen binding and why it belongs.

## Phase 2 — Push Canonical Templates

**Entry:** inventory complete and destructive replacement explicitly approved when needed.

1. For clean replacement, export and delete legacy CPT card posts per
   `references/ef/card-scaffolding.md`. All-CPT replacement must delete every actual
   `elementor_library_type=card` post with `--force`, confirm zero remain, then clear
   base/custom Voxel card registrations before regeneration.
2. Run `wpdev voxel:cards <site> --type <key> --sizes small,medium,large,link -y`.
3. Read returned IDs. Confirm `wpdev voxel:templates` shows large as base `card` and all
   four IDs as `custom_card` rows.

**Exit:** four normalized scaffold posts exist and Voxel config points main to large.

## Phase 3 — LLM Card Blueprints

**Entry:** canonical IDs and field matrix available.

Design each variant independently:

1. `small`: identity, logo when real, concise differentiator, one primary destination.
2. `medium`: small content plus one useful metadata/byline cluster and compact actions.
3. `large`: strongest real cover, logo, identity, richer summary, useful taxonomy/trust
   rows, and complete actions. This is always main.
4. `link`: accessible inline identity and destination; no decorative noise.

Every used dynamic image requires a semantic dynamic alt binding from its owning image
field when available; title is fallback only. Every card needs an accessible permalink
path. Add other actions only when a real field or Voxel-native destination supports them.
Never invent phone, email, URL, relation, taxonomy, or image data.

Preview cards never use `kind: rich_text`. Secondary copy uses `kind: heading` with
`tag: span`. Small and medium bind `@post(hook)` only when the CPT defines a hook field,
else the native `@post(excerpt)` property; large always binds `@post(excerpt)`. Link has
no secondary copy: one linked `heading`/`span` title with an icon only.

Before mutation, confirm every dynamic tag resolves on a live sample via `wpdev voxel:data`.
A field-scoped tag on a CPT without that field renders empty and must be replaced by the
native property or omitted, never left blank.

**Exit:** four blueprints specify content rows, media/logo bindings, alt bindings,
actions, visibility gates, and fallbacks.

## Phase 4 — LLM Mutation

**Entry:** blueprints approved by evidence.

1. Export each scaffold with `wpdev elementor:export`.
2. Mutate through generated widget schema shapes only. Preserve canonical atomic base props.
3. Normalize each candidate with `wpdev elementor:normalize`, then import through the
   supported Elementor command so editor save/CSS regeneration runs.
4. Do not alter Voxel registration IDs during content mutation.

**Exit:** all four stored cards match their field-aware blueprints.

## Phase 5 — Verification Gate and Convergence Proof

**Entry:** mutations written.

1. `wpdev elementor:codegen --check` passes.
2. `wpdev elementor:codegen:verify <site> --widget ef-card` passes.
3. EF migrator reports target version with zero pending steps.
4. Normalize-export comparison is idempotent for all four cards.
5. Elementor lint passes with zero findings for every ID.
6. `wpdev voxel:templates` proves large is base/main and all four custom registrations exist.
7. `wpdev voxel:cards --audit` reports four present and zero drift/duplicate/stale/missing.
8. Browser verification covers populated and sparse sample records, desktop/mobile,
   media alts, actions, tag leakage, console/page errors, and screenshots.

**Exit:** command and LLM stages converge on one schema-valid, registered, rendered card family.
