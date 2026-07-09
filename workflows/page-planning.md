# Page Planning Pipeline — section-by-section, adversarially-reviewed, SSOT-driven

The mandatory Phase 2 sub-pipeline for the build workflow (`workflows/build.md`) and the migration workflow (`workflows/migrate.md`) (entry point: [`build.md`](build.md) §Phase 2, [`migrate.md`](migrate.md) §Phase 2). Replaces the prior one-sentence "decide the widget tree top-down" instruction that produced thin templates (single-`ef-card`-at-root, unsurfaced relation fields, no semantic hierarchy — a data-rich CPT rendered as a near-empty tree, an `ef-wrapper > ef-card` stub with fields and relations unsurfaced, while the CPT carries many fields plus traversable relations).

The pipeline is **structural, gated, and adversarial**. The orchestrator produces a Plan Document; the relevant adversarial reviewers — one concern each, dispatched in parallel — try to break it. Default to the full panel (coverage, density, hierarchy, data-wiring, pattern-reuse, relations, ssot-integrity, + migration-preservation when migrating); narrow it only with a stated reason. The orchestrator addresses every finding (or writes an explicit `override: <reason>` line) before fan-out. No heuristic thresholds — every rejection comes from a reviewer agent that re-derives its judgment from the live data and the committed SSOT.

## Orchestration model — Workflow fan-outs, orchestrator-owned gates

This pipeline alternates **mechanical parallel fan-outs** (§2c→§2d composition dispatch, §2e adversarial review) with **judgment gates** the orchestrator owns between them (the Phase-0 rebuild-vs-revise call, §2f reconciliation, the computed §2g gate). The two never merge: the fan-out is deterministic and parallelizable; the gate is a reasoning step that decides whether to fan out again.

Express each fan-out as a **Workflow `parallel()`** (when the user has opted into multi-agent orchestration: ultracode on, the keyword `ultracode`, or an explicit "use a workflow" request) or **inline single-message Agent dispatch** (the always-valid default, never wrong) — one fan-out per phase, never one Workflow spanning §2c through §2g, so the gates stay outside the Workflow and the author≠reviewer separation holds. Atomic scope is unchanged either way: one criterion / one section / one widget per `agent()` call. The rationale (what Workflow buys) and the orphan caveat are the SSOT in [`../references/core/parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Expressing a fan-out through the Workflow tool.

The named voxel-builder subagents dispatched through either path are `voxel-heading-curator` (§2d phrasing palette), `voxel-layout-architect` (§2d Layout maps, one per section), and `voxel-plan-reviewer` (§2e, one per criterion); the Phase 3 build fan-out (`voxel-widget-builder`) and the Phase 6 verify fan-out belong to [`build.md`](build.md) and follow the same model there.

## Entry criteria

Before invoking this sub-pipeline, Phase 1 must have produced:

- `wpdev elementor:dump <site> all --post <id> --json` (when modifying existing).
- `wpdev voxel:fields <site> <cpt_key>` output (the universe of available data).
- `wpdev voxel:sample <site> <cpt_key>` run — exports the **most-complete posts** (ranked by filled fields + relations + repeaters) to a temp folder, so the inventory is built from the richest real data the CPT has, not a random or single post. `wpdev voxel:data <site> --id <example_post>` then reads rendered values on those sampled posts (one is never enough — the data-wiring and coverage adversaries reject single-post inventories).
- `wpdev elementor:codegen` was run at the start of the run (regenerates `cli/src/generated/widget-schemas.json` AND syncs it into this skill's `references/ef/widget-schemas.json`). Every widget pick in the plan is validated against that artifact.
- The **rebuild-vs-revise** call was made in Phase 0 (see [`build.md`](build.md) §Phase 0): when the existing tree is worse than starting clean, the plan is composed greenfield and the existing data is discarded at write; otherwise the plan revises in place.
- **For migration mode only:** 1-3 production page URL(s) corresponding to the local post being migrated. Resolve trivially via `./wpdev remote:list` (gives the live host) + `?p=<post_id>` — WordPress core resolves `https://<prod_host>/?p=<id>` to the canonical permalink for any post type via 302 redirect (no CLI helper required, no permalink template knowledge needed). For archive / page templates: list 1-3 representative post ids of the same CPT and pass `?p=<id>` for each. The migration-preservation criterion opens these URLs with the `agent-browser` CLI and reads the rendered, visitor-visible text to build the content baseline (it renders JS, so Voxel dynamic tags resolve exactly as a visitor sees them — see [`browser.md`](../references/verification/browser.md) §Production-page baseline).

If any input is missing, halt — do not enter Phase 2.

**Stale-plan guard (check before composing §2a).** A Plan Document may already exist at `/tmp/plan-<post_id>.md` from a prior session (the orchestrator may have been re-invoked after a context reset). Do NOT blind-`Write` over it — that errors `File has not been read yet` and, worse, can silently discard an already-`APPROVED` plan. `ls /tmp/plan-<post_id>.md` first; if present, `Read` it and present the operator three choices: **continue** (already `APPROVED` → skip to Phase 3 fan-out), **revise** (re-enter §2c–§2f with their notes), or **discard** (delete, start §2a fresh). An existing `APPROVED` line is a prior operator decision — never overwrite it without that explicit choice.

## Exit criteria

The pipeline exits successfully ONLY when:

1. The Plan Document at `/tmp/plan-<post_id>.md` exists and validates against the schema in this file (§Plan Document structure).
2. The relevant adversarial reviewers — defaulting to the full panel, narrowed only with a stated reason — have run in parallel; their findings are aggregated at `/tmp/plan-review-<post_id>.md`.
3. Every Critical / Improvement finding is **addressed** in the Plan Document (either resolved by revising the plan, or annotated with a per-finding `override: <reason>` line — never silently ignored).
4. The §2g gate is green — `GATE: green (auto)` (computed) OR an escalated operator `APPROVED` at the bottom of the Plan Document.

Only then does Phase 3 (widget fan-out) start. Lack of any of the four is a hard halt.

## Phase 2a — Field Inventory

**Goal:** enumerate every CPT field with data on real posts, classify it, and bind each to a target section (or mark `omit` with a reason).

**Steps:**

1. Read `wpdev voxel:fields <site> <cpt_key>` output. List every field (key, type, label) and every traversable-relation expression (`@post(<relation>.<target_field>)`).
   - **Resolve each field's correct accessor up front from the field-type → accessor table in [`../references/voxel/voxel-tags.md`](../references/voxel/voxel-tags.md) §Object fields — do NOT ad-hoc probe with `\Voxel\render`.** The recurring traps: `select`/`multiselect` render empty unless you use `.label` (display) / `.value` (compare); a field key that collides with a built-in property (`status`, `url`, `title`, `date`, `author`, `id`, `content`, `excerpt`, `slug`) needs the **`field:` disambiguator** (`@post(field:status.label)` → "Open", not the WP post status "Published"); dates use `.date_format(j F Y)` (there is no `.format()`); relation/multiselect joins use `.list( • )` (the tokenizer splits args on `,`, so a comma separator is inaccessible); switchers use `@post(<key>).is_checked().then(X).else(Y)`. Record the resolved accessor in the inventory's Settings/affordance notes, then confirm with ONE `wpdev voxel:data` read per field — not a render-probe loop.
2. For each post in the sample, read `wpdev voxel:data <site> --id <example_post>` and record per-field `nonempty: yes|no`.
3. Compute a **Field Inventory Table** in the Plan Document (markdown table, no prose):

   | Key | Type | Label | Post A | Post B | Post C | Class | Target section |
   |---|---|---|---|---|---|---|---|
   | title | title | a title-class field | ✓ | ✓ | ✓ | must | hero |
   | description | texteditor | a long-form body field | ✓ | ✓ | ✓ | must | overview |
   | <relation-field> | post-relation | a relation field | ✓ | ✓ | empty | should | specs-grid + sidebar |
   | <switcher-field> | switcher | a switcher field | ✓ | ✓ | ✓ | may | byline-conditional |
   | <multiselect-field> | multiselect | a multiselect field | ✓ | empty | ✓ | should | specs-grid |
   | ... | | | | | | | |

4. **Classification rule (defended to the coverage reviewer — not a count rule):**
   - `must`: reliably carries data across the sample AND is user-facing (not a UI-step / admin-workflow field).
   - `should`: carries data on part of the sample AND is user-facing.
   - `may`: sometimes present AND value adds editorial signal (e.g. a switcher field).
   - `omit:<reason>`: never surface. The reason is a free-text string — the adversary will challenge it.
5. **Traversable relations are mandatory.** Every `single → <type>` relation that has data on at least one post in the sample becomes its own row in the table (e.g. `<relation-field>.title`, `<relation-field>.description`, `<relation-field>._thumbnail_id`). Surface them at minimum as an inline list, ideally as an EF `ef-wrapper` loop/template section filtered to the relation's posts. Do not plan a new Voxel `ts-post-feed`.

**Exit:** the Field Inventory Table is complete; no field is unclassified.

## Phase 2b — SSOT Read (widgets + envelopes)

**Goal:** ground every widget pick and every prop binding in the committed SSOT — no widget names, no prop shapes from memory.

**Steps:**

1. Read `cli/src/generated/widget-schemas.json`. Build a Widget Catalog table in the Plan Document:

   | Widget | Source | Props count | Row surfaces | Use case (from this plan) |
   |---|---|---|---|---|
   | ef-card | widget-schemas.json | 59 | action-row, heading-row, tag-row | hero, specs-grid, FAQ, sidebar |
   | ef-wrapper | element registration (not in widget-schemas) | reserved-keys + tag | — | section containers |
   | ef-form | widget-schemas.json | 5 | field-row | (none on this plan) |
   | ef-navbar | widget-schemas.json | 22 | action-row, mega-row | (header only — global template) |
   | ef-toc | widget-schemas.json | 2 | — | (consider for long single posts) |
   | ef-cal | widget-schemas.json | 6 | — | (consider for target-date field) |
   | ef-wrapper | schema + reserved keys | loop/template props | template/loop wrapper | repeated sections, related posts, relation surfaces |

2. The plan MUST NOT name new Voxel `ts-*` widgets. If an existing template already contains a `ts-*` node, list it under "legacy preserved nodes" with the dump source and mark it `preserve verbatim`; do not use it as a new section archetype.
3. For every prop the plan binds (heading text, image source, action link, loop source, visibility rule, template id), record the prop's `$$type` envelope shape from the SSOT. The data-wiring adversary will check shape correctness against the live schema.

**Exit:** every new widget in the plan exists in the EF SSOT; every prop has its envelope shape recorded. Any `ts-*` mention is preservation-only and has a verbatim dump source, not a rebuild/customization plan.

## Phase 2c — Archetype Selection

**Goal:** pick from a catalog of established section archetypes instead of inventing shapes. Reuse what the site already does well.

**Template-store lookup (do this FIRST, before the static archetype catalog).** For each section the page needs, read [`../templates/index.md`](../templates/index.md) and look for a saved section template whose `type` matches the section archetype and whose `tags` overlap the CPT context (e.g. a `hero` archetype for a services/geo CPT → the seeded [`hero-services-search`](../templates/sections/hero-services-search/) / [`hero-city-geo`](../templates/sections/hero-city-geo/)). **When a template matches, PREFER it: bind the section to that template id** rather than composing the archetype from scratch. Only sections with NO matching template fall through to the static archetype catalog below and full composition. Discovery is reading `templates/index.md` (its `type` / `tags` / `widgets` / `dtags-used` columns) — there is no `apply-template` command. The bound template is a *preferred starting tree*, never a validation bypass: it stays subordinate to §2b (SSOT wins on any disagreement — [`../templates/README.md`](../templates/README.md) §SSOT wins) and every bound section is still validated prop-by-prop by the §2e adversaries.

**Standard archetypes** (when NO saved template matches, pick from this catalog — the fallback behind the template-store lookup above; adding a *new* archetype requires the §2e Pattern-reuse criterion to approve via a peer-template comparison override):

**Root wrapper (always present, exactly once per page):** the Plan Document declares a single `ef-wrapper` with `tag: main` at depth 0 of `_elementor_data` that contains every section. The hierarchy criterion enforces this — multiple or missing `tag: main` = `C`-severity finding.

| Archetype | Purpose | Wrapper tag | Default desktop grid | Mobile collapse | First heading | Internal heading tags | When to use |
|---|---|---|---|---|---|---|---|
| `hero` | Primary subject identification | `section` (within root `main`) | `1fr` (single column, full bleed) — OR `3fr 2fr` / `2fr 3fr` variant when there's a complementary visual / CTA aside (content-asymmetric hero pattern) | `1fr` | **h1** bound to title-class field for CPT templates (contextualized dynamic phrase, not bare `@post(title)`); for non-CPT pages (homepage / landing), use a static h1 with the page subject. Decorative eyebrow before the h1 → a `kind: byline` row (rendered `.ef-ih-byline`). | eyebrow (ONE, directly above the h1) → `kind: byline`; tagline/subtitle → `kind: rich_text` (`p`); sub-CTA labels → `p`; never another `h*` | Every single template. Mandatory. |
| `brief` | Short structured intro paragraph + secondary CTA | `section` | `1fr` or `2fr 1fr` (body + sidebar-cta) | `1fr` | h2 — contextual phrase (e.g. `@tags()About @post(:title)@endtags()`, not bare "About") | body → `p`; CTA label → `span` | When the CPT has an intro/excerpt/hook field separate from the long body. |
| `specs-grid` | Label/value pairs | `section` | `1fr` (single column, label-above-value rows) OR `1fr 1fr` (2-up, label-value pairs side-by-side); **let the content's hierarchy decide column count — prefer more sections over more columns** | `1fr` | h2 — e.g. `@tags()Specifications of @post(:title)@endtags()` | per-item label → `kind: heading, tag: span, style: ''` plain, or `style: label` for a small-caps pill (runtime-valid `.ef-label`); per-item value → `tag: span, style: h3` or `kind: rich_text` (`p`); NEVER `h3` for the value when the label is already the spec name; the section eyebrow is a `kind: byline` row, never `style: byline_label` | When the field group's shape calls for it (atomic select / multiselect / date / number / switcher fields that aren't long-form text). |
| `detail-tabs` | Multiple long-form body sections under tabs | `section` | `1fr` (tabs are the layout) | `1fr` | h2 — e.g. `@tags()Detailed information about @post(:title)@endtags()` | per-tab pane title → `h3` with contextual phrasing (e.g. `@tags()Services provided by @post(:title)@endtags()`); tab body → `p`; existing legacy `ts-*` nodes remain verbatim only if already present | When the field group's shape calls for it (texteditor / wysiwyg fields that benefit from separation — overview / brief / detail / specs). |
| `detail-accordion` | Multiple body sections collapsed by default | `section` | `1fr` | `1fr` | h2 — contextual phrase | per-row question → `h3` (FAQ-style); per-row body → `p` | When tabs would be overkill (≤3 sections) or device-target is mobile-first. |
| `sidebar-contact` | Contact channels (call / email / message) | `aside` (when used as a sidebar) or `section` (when full-width) | `1fr` (it's a sidebar) | `1fr` (last in mobile stack) | h2 — e.g. `@tags()Contact @post(:title)@endtags()`, not bare "Contact" | per-channel label → `tag: span, style: ''` plain (no `byline` row); per-channel CTA → `span` | When the CPT has phone/email/messaging fields OR `ts-` messaging connections. |
| `sidebar-map` | Geo-location surface | `aside` | `1fr` | `1fr` (last in mobile stack) | h2 or h3 — e.g. `@tags()Locate @post(:title)@endtags()` with city/region fallback | label → `tag: span, style: ''` plain (no `byline` row); ts-map nested unchanged | When the CPT has a geo-location field with non-empty data. |
| `sidebar-schedule` | Opening hours / availability | `aside` | `1fr` | `1fr` (last in mobile stack) | h2 or h3 — e.g. `@tags()@post(<field>).fallback(@post(:title)) opening hours@endtags()` | day label → `span`; ts-work-hours nested unchanged | When the CPT has a work-hours field. |
| `relation-feed` | Inline list of related posts via a relation field | `section` | `1fr` OR `1fr 1fr` (2-up); **let the content's hierarchy decide column count** — repeated cards come from an `ef-wrapper` loop/template composition, not `ts-post-feed` | `1fr` | h2 — e.g. `@tags()Other @post(:title.<relation_label>)@endtags()` or relation-named phrasing | per-loop child title comes from the EF card/template child declared in this Blueprint | For every post-relation field with data. Mandatory per relation. |
| `faq-accordion` | FAQ from a composite-repeater field | `section` | `1fr` | `1fr` | h2 — e.g. `@tags()Frequently asked questions about @post(:title)@endtags()` | per-FAQ question → `h3`; per-FAQ answer → `p` | When the CPT has a non-empty FAQ field with genuine reader questions. For glossary/defined-term singles this is optional, never boilerplate, and never a reason to emit `FAQPage` schema. |
| `related-cpt-feed` | "More from this CPT" feed | `section` | `1fr` — the EF loop/template wrapper owns its repeated-card layout (see §Feed-grid note below) | `1fr` | h2 — e.g. `@tags()Other <CPT plural> like @post(:title)@endtags()` or category/region-scoped phrasing | per-loop card title → `h3`; per-loop-card byline → `span` | Every single template. Recommended. |
| `cta-footer` | Closing action band | `section` | `1fr` (full bleed) | `1fr` | h2 — contextual outcome phrase (e.g. `@tags()Ready to work with @post(:title)?@endtags()`) | CTA label → `span`; sub-label → `p` | Every single template that drives a conversion goal. |

The plan picks **N archetypes**. The density adversary will challenge the count; the coverage adversary will challenge the field-to-archetype binding; the **hierarchy criterion** will challenge the wrapper-tag selection AND the heading-tag selection per row; the **pattern-reuse criterion** will challenge any dynamic heading phrasing that doesn't match the production conventions on peer templates.

**Let the content's hierarchy decide column count; prefer more sections over more columns.** Reference exemplar: inspect a rich peer template — mostly `1fr` and `1fr 1fr` sections, plus the occasional symmetric atomic feature row (a feature grid where content is inherently symmetric and each card is atomic: icon + h2 + body line) and content-asymmetric hero pair (the hero + lateral panel). Run `wpdev elementor:tree <site> <peer_id>` to inspect.

The Layout map's `cols` track string values:

- `1fr` — single column. Default for most sections.
- `1fr 1fr` — 50/50 two-column. Body + complementary aside, or 2-up paired items.
- `1fr 2fr` / `2fr 1fr` — sidebar + body or body + sidebar. The 2fr side holds the primary content.
- `3fr 2fr` / `2fr 3fr` — content-asymmetric hero pattern. Use when one side is content-heavy and the other is a single visual/CTA.
- `1fr 1fr 1fr 1fr` — for atomic symmetric items: a feature/icon/expertise grid where each cell is icon + h2/h3 + one body line, not paragraphs, and tablet collapses to `1fr 1fr`, mobile to `1fr`. The `feature-grid` archetype below codifies this.
- `1fr 1fr 1fr` — atomic thirds (a counter row of stats — total clients / years / projects).

Let the content's hierarchy decide column count; **prefer more sections over more columns**; collapse to a single column on small screens; the hierarchy reviewer challenges any grid that fights the content. When the planner reaches for a wide or unusual grid:

- **A specs grid with many fields?** Split into thematic sub-sections (one per coherent field group) each at `1fr` or `1fr 1fr`. The hierarchy criterion will then enforce h2 per sub-section.
- **Many stats?** Split across multiple `1fr 1fr` sections, OR pick the most important and use `1fr 1fr 1fr 1fr`.
- **Feed/list showing many cards in a row?** The EF template/loop wrapper handles repeated children — the section wrapper stays at `1fr`, while the loop child/card controls its own internal stack. Do not solve this with a Voxel `ts-post-feed`.

Why this discipline: **more sections > more columns** is the default. Vertical rhythm is forgiving (mobile collapse is trivial, hierarchy stays clear). Horizontal compression usually fights the design system — but symmetric-atomic feature grids and asymmetric content pairs are sometimes the right call; the catalog below codifies which archetypes earn that shape. The hierarchy reviewer challenges any grid that fights the content; `1fr 1fr 1fr 1fr` belongs to the `feature-grid` archetype with content satisfying the atomic-symmetric test; `3fr 2fr` belongs to the `hero` archetype (with `hero-with-aside` variant declared) or `brief` with a CTA panel.

**Heading-tag policy (SEO-compliant outline):**

The page must read as a valid `h1 → h2 → h3` outline when a screen reader walks document order. The catalog above pins each archetype's "first heading" tag, which produces the page-level sequence: hero h1 → section-N h2 (in document order) → nested h3 inside each h2 section. Decorative text (eyebrows, taxonomy pill labels, CTA labels, taglines) NEVER uses an `h*` tag — it uses `tag: span` or `tag: p`. Body paragraphs use `tag: p`. The hierarchy criterion walks the full sequence in §2e and emits findings on any violation.

**Eyebrow rule — use the `byline` row KIND, not a phantom `style` value (the single most-misused affordance):**

> **SSOT correction (verified 2026-06-14 against `schemas/parts/rows/content-block-row.schema.json`, EF migrations 800/890, `ef.css`, and live peer dumps).** `style: byline_label` is **migrated-away / vestigial** — EF migration step 890 converts `style: byline_label → label` precisely because "byline is now a first-class block kind." Do NOT author `byline_label`. The eyebrow is its own row **`kind: byline`**, not a heading style. `style: label` IS a live runtime value (renders `.ef-label`, small-caps inline label) — but note it is **absent from the schema's `style` enum** (`["", "h1".."h6"]`), so it is runtime-valid yet schema-strict-invalid; prefer it only for genuine inline pills, and expect schema-lint to flag it until the enum is reconciled (tracked separately).

The **eyebrow / kicker** — the small upper-case label sitting directly above a card's main heading — is a content-block row with **`kind: byline`** (cells `byline_primary` / `byline_secondary`), rendered as `.ef-ih-byline`. Confirmed in production: peer service single (post 46083) authors its eyebrow as one `kind: byline` row; no peer uses `style: byline_label`.

- Allowed: exactly ONE `kind: byline` row per card, immediately preceding that card's main heading (e.g. `Overview` above the `h2`, the parent-category kicker above the hero `h1`). At most one per card.
- **Everything else uses a valid style/kind.** Taglines / subtitles → `kind: rich_text` (`tag: p`); per-channel / per-day / map labels, CTA labels → `kind: heading, tag: span, style: ''` (plain) or `style: label` (small-caps inline label, runtime-valid via `.ef-label`); second/third headings → `tag: h3` with `style: ''`. Never an `h*` tag for decorative text, never `byline_label`.
- Rationale: the `byline` kind carries the small-caps intro treatment via `.ef-ih-byline`. One byline row, one main heading, per card.

The hierarchy criterion flags any `kind: byline` row that is not the leading eyebrow of its card (severity `I`), any card with more than one `byline` row (severity `I`), and any `style: byline_label` (severity `C` — migrated-away; use `kind: byline`).

**Production exemplar — eyebrow-before-h2 scaffold:** a rich peer template prefixes every navigable section with a `kind: byline` eyebrow (e.g. Overview / More about / Services / News / Gallery / Contact / FAQ / Send a message / Explore), followed by an `h2` heading with contextual phrasing. The planner SHOULD adopt this scaffold for every non-hero section unless `override:` justifies; the hierarchy criterion surfaces missing eyebrows as severity `I`.

**Per-card semantic tags (production carries semantic role at CARD level, not wrapper level):**

Production templates (a homepage page, a rich CPT single) use a small set of wrapper tags (`main / section / nav / div`) and carry the per-section semantic role on the CARDS via the card's own `tag` prop. Catalog:

- `ef-card tag: article` — hero card on a CPT template (the card IS the article). One per page.
- `ef-card tag: section` — overview / about / in-depth / repeater-host content cards. Multiple per page.
- `ef-card tag: aside` — sidebar utility cards (Contact / Location / Opening hours / on-this-page nav). Multiple per page.
- `ef-card tag: div` — atomic items inside a `feature-grid` 4-up (no semantic anchor of its own; the parent section's h2 carries the outline).

The §2d Blueprint Settings cell for every card MUST declare its `tag` prop. The hierarchy criterion checks that hero is `article`, sidebar utilities are `aside`, repeater hosts and content cards are `section`, and `feature-grid` children are `div`.

**Exit:** the plan lists its chosen archetypes (with section IDs, wrapper tags, grid defaults, first-heading tags, and per-card semantic tags) and shows that every `must`-class field from §2a maps to at least one archetype. Sections **bound to a saved template** are recorded with their template id (from `templates/index.md`) and only need a matched archetype `type`; only **unbound** sections must map to a catalog archetype row. The root `main` wrapper is declared; every chosen archetype's wrapper tag matches the catalog row (deviation requires `override:` with reason).

## Phase 2c.bis — Production vocabulary palettes (consumed by §2d)

Before composing Blueprints, the planner reads the production vocabulary for dynamic-tag transforms, tag-row variants, and action types — these recur across every site's templates and the planner reuses them instead of reinventing. Source: a rich peer template (a data-rich CPT single) plus a homepage page. The `voxel-heading-curator` agent dispatched in this phase samples additional peer templates if needed.

**Dynamic-tag transform chains (use these patterns, not bare `@post(field)`):**

| Pattern | Use case | Example |
|---|---|---|
| `@post(:title)` | Title used as a noun phrase (with surrounding context words). Different from `@post(title)` — the `:` form renders cleaner when wrapped in a sentence. | `@tags()Presentation of @post(:title)@endtags()` |
| `@post(field).fallback(@post(other_field))` | Field A with field B as a backup. | `@tags()@post(<field>).fallback(@post(:title)) opening hours@endtags()` |
| `@post(field).strip_tags().truncate(N).fallback(@post(other))` | Excerpt with HTML strip + length cap + fallback. Production hero subtitle pattern. | `@tags()@post(<field>).strip_tags().truncate(220).fallback(@post(<other_field>))@endtags()` |
| `@post(field).number_format(N)` | Formatted number with N decimals. | `@tags()@post(<field>).number_format(0)€@endtags()` |
| `@post(field).count()` | Count of items in a relation / repeater / multiselect. | `@tags()@post(<relation>).count() items@endtags()` |
| `@site().math(<expr>)` | Arithmetic on dynamic values. Production "X more in this group" pattern. | `@tags()+@site().math(@post(<relation>.<field>).count() - 1) more in @post(<relation>.title)@endtags()` |
| `@site(loop_<type>.field)` | Inside a `_vx_loop` over `<type>`, references the loop iteration's field. | `@tags()@site(loop_<type>.<field>)@endtags()` |
| `@post(rel.field)` | Single-relation traversal. | `@tags()@post(<relation>.title)@endtags()` |

The data-wiring criterion checks every Blueprint dynamic tag against this palette — bare `@post(title)` in a non-hero heading without surrounding context words is flagged as a keyword-stuffing risk (severity `I`).

**Image / media envelope patterns:**

| Pattern | Use case |
|---|---|
| `media_image.src = vx("@post(<image_field>.id)") size: large` | Hero / about media bound to a CPT image field. |
| `logo_image.src = vx("@post(_thumbnail_id.id).fallback(@post(types.icon))") size: large` | Logo with thumbnail-then-type-icon fallback chain. |
| `media_image.src = vx("@post(<relation>.<image_field>.id)")` | Image from a traversed relation. |

`size: "large"` is the universal default token (production exemplar). The planner records `vx envelope` in the Dynamic affordance column for these props.

**Tag-row variant vocabulary** (the `variant` value on each `ef-card.tags` repeater row):

| Variant | Visual role | Production example |
|---|---|---|
| `""` (empty) | Default pill | CPT types pill, regions pill |
| `transparent` | Outline-only, low emphasis | Secondary metadata loop |
| `green` | Affirmative status | "Verified" badge |
| `gray` | Neutral / pending status | "Unverified" badge |
| `primary` | High-emphasis brand pill | Featured / promoted state |

Tag-rows use `loop` to iterate a relation/taxonomy and conditional `_vx_visibility` to gate badges. The planner records the variant per tag-row in the Blueprint Settings cell.

**Action-row type vocabulary** (the `type` value on each `ef-card.ts_actions` repeater row — full list in [`actions.md`](../references/ef/actions.md); the production-frequency subset is):

| Action type | Use case | Required cells |
|---|---|---|
| `share_post` | Native share UI | (no extra fields) |
| `action_save` | Bookmark / favorite | (no extra fields) |
| `edit_post` | Owner-only edit link | (no extra fields, visibility gated by post:author == current_user) |
| `action_link` | Custom CTA / external link | `link.destination` (literal or dynamic) |
| `phone` | Click-to-call | `phone.value` |
| `email` | Mailto | `email.value` |
| `get_directions` | Maps link | `geo.value` |
| `show_post_on_map` | Pan/zoom the page's ts-map | `map_id` (the `ts-map` widget's element id) |
| `scroll_to` | Anchor scroll | `scroll_target` (target `_cssid`) |

Action-row `variant` vocabulary: `""` (default), `primary`, `secondary` (production usage).

**Section-wrapper aria-label defaults (a11y discipline):**

Production uses `aria-label` on exactly two wrapper roles: `nav` (e.g. `aria-label="On this page"`) and the outermost grid-bearing `section` (e.g. `aria-label="Company details"`). The planner declares aria-label in the Layout map's Section wrapper table for these two roles; other wrappers skip it (the heading inside is sufficient).

## Phase 2d — Section Blueprint Composition

**Goal:** for each chosen archetype, produce a Section Blueprint — a concrete table that the widget-builder subagents can consume in Phase 3 as their brief.

Every section in §2c produces THREE artifacts in §2d: an **Improvements log** (migration only), a **Layout map** (always), and a **Blueprint** (always). The Layout map defines the visual structure (grid tracks, gaps, responsive collapse, per-widget placement); the Blueprint defines the widget JSON settings; the Improvements log declares what changed from production. The hierarchy criterion inspects the Layout map; the data-wiring + ssot-integrity criteria inspect the Blueprint; the migration-preservation criterion inspects the Improvements log against production markdown.

**A section blueprint MAY bind to a saved template** in [`../templates/sections/`](../templates/sections/) (matched via [`../templates/index.md`](../templates/index.md) in §2c) instead of requiring full widget-by-widget synthesis — record the bound template id in the blueprint row so Phase 4 splices its `template.json` and patches only the deltas. The bound tree stays subordinate to §2b: the SSOT wins on any disagreement ([`../templates/README.md`](../templates/README.md) §SSOT wins), so the template is a starting tree the blueprint still validates prop-by-prop, never an authoritative spec.

**Mandatory agent dispatches before composition (one parallel fan-out):**

1. ONE `voxel-heading-curator` dispatch — extracts production heading phrasings from peer templates and returns a palette the orchestrator uses to fill the Blueprint heading-row `text` cells (§2c.bis transform-chain patterns + per-archetype phrasings). Dispatched once per plan (not per section).
2. The section fan-out is **gated on template-binding** — each §2c-selected section takes exactly one of two legs, in parallel:
   - **Bound section (§2c matched a saved template) → delta-plan pass.** No full from-scratch `voxel-layout-architect` compose. Instead a lighter delta-planning pass identifies which `Lorem ipsum` placeholders and structural props of the bound `template.json` need per-post patching, and records those deltas in the blueprint row. The template already supplies the Layout map / widget tree; the delta-plan only validates it against §2b prop-by-prop and lists what Phase 4 must patch.
   - **Unbound section (no matching template) → full `voxel-layout-architect` compose.** One architect dispatch, as today. Each returns its section's complete Layout map block (Section wrapper props + Grid tracks responsive table + Widget placement table). The orchestrator splices the returned blocks into §2d.

The curator, the bound-section delta-plan legs, and the unbound-section architect dispatches form **one fan-out** at the §2c→§2d boundary. The orchestrator does NOT hand-compose Layout maps or heading phrasings for unbound sections; doing so violates the workflow gate and the §2e adversaries will reject the plan.

**Preferred (Workflow opted in):** dispatch the fan-out as a single `parallel()` inside the §2d Workflow, each leg a schema-returning `agent()` call:

```
parallel([
  () => agent(curatorBrief,          {agentType: 'voxel-builder:voxel-heading-curator',  schema: PHRASING_PALETTE}),
  // bound section → lighter delta-plan (no from-scratch compose); unbound → full architect compose
  ...sections.map(s => s.boundTemplateId
    ? () => agent(deltaPlanBrief(s),  {agentType: 'voxel-builder:voxel-layout-architect', schema: TEMPLATE_DELTA})
    : () => agent(architectBrief(s),  {agentType: 'voxel-builder:voxel-layout-architect', schema: LAYOUT_MAP})),
])
```

The Workflow returns one schema-validated palette plus, per section, either a Layout-map block (unbound) or a template-delta block (bound); the orchestrator splices them into §2d, then reasons at the §2c-revision gate below (this gate stays outside the Workflow).

**Fallback (inline):** send the ONE curator dispatch plus, per section, the gated dispatch (bound → delta-plan brief, unbound → full architect brief) in a single message at the §2c→§2d boundary, then splice the returned blocks by hand.

If `voxel-layout-architect` returns `escalate_split: true` for any section, the orchestrator revises §2c (splits the section into sub-sections), re-dispatches the affected architect(s), and proceeds. This split-and-re-dispatch decision is the orchestrator's, made between fan-outs — never inside the Workflow. Re-dispatch whenever a section's shape has materially changed; stop when it converges; surface the residual to the operator if it won't converge.

**Per-section §2d block** (one per section in the Plan Document):

```
## Section: <id> — <archetype>

### Improvements log (migration mode only — omit in greenfield build, omit when copy matches production verbatim)
- improvement: hero-tagline → "<new tagline>" (was: "<old tagline>")
- improvement: services-list-item-3 → fixed typo "<misspelling>" → "<correction>"
- removed: legacy-stat-block → "<stale stat>" (reason: stat is stale; no current equivalent)

### Layout map

#### Section wrapper (the outer `ef-wrapper`)
| Prop | Value | Notes |
|---|---|---|
| `tag` | `section` | semantic HTML wrapper (or `aside` for sidebar-only archetypes, `main` for hero-only) |
| `_cssid` | `<section-overview>` | stable selector for browser-verification + Behavior Contract DOM anchor |
| Section width | `contained` \| `full-bleed` \| `narrow` | maps to design-token max-width band |
| Background | `transparent` \| `white` \| `secondary` \| `primary` | wrapper **`variant`** (surface SSOT) — NOT invented tokens. Assign via the P1–P6 ladder + set `bg_media_type:color` (else inert). See [`../references/ef/section-rhythm.md`](../references/ef/section-rhythm.md) |
| Vertical rhythm | `sm` \| `md` \| `lg` \| `xl` | top/bottom padding band (design tokens) |
| Sticky | `none` \| `sidebar-sticky` | only when the archetype calls for it |

#### Grid tracks (responsive)
| Breakpoint | `cols` track string | Row gap | Column gap | Justify items |
|---|---|---|---|---|
| desktop (≥1024) | `1fr 2fr` | `lg` | `lg` | `start` |
| tablet (640–1023) | `1fr 1fr` | `md` | `md` | `start` |
| mobile (<640) | `1fr` | `md` | — | `start` |

Track ratio guidance: `1fr` (single column), `1fr 1fr` (50/50), `1fr 2fr` (33/67 — sidebar left), `2fr 1fr` (67/33 — sidebar right), `1fr 1fr 1fr` (thirds — specs grid), `1fr 1fr 1fr 1fr` (quarters — counter row of atomic items). Let the content's hierarchy decide column count; prefer more sections over more columns. Mobile always collapses to `1fr` unless the section is a small counter row of atomic items. For **asymmetric / bento masonry** sections (a hero card + smaller peers, sized by content rather than a uniform grid) — the size=hierarchy rule, content→span decision table, and the rectangle-tiling invariant (`Σ(col_span × row_span) == cols × rows_used`, no holes) — see [`../references/ef/masonry.md`](../references/ef/masonry.md).

#### Widget placement (every Blueprint row gets one row here)
| Blueprint # | Widget | Desktop column | Desktop col-span | Desktop row-span | Tablet column | Tablet col-span | Mobile order |
|---|---|---|---|---|---|---|---|
| 1 | ef-card overview-body | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | ef-card overview-aside | 2 | 1 | 1 | 2 | 1 | 2 |
| 3 | ef-card overview-cta | 1 | 2 (full) | 1 | 1 | 2 (full) | 3 |
| ... |

Placement guidance: every Blueprint row MUST have a placement row. "Full" col-span = the whole track count; named col-spans (1, 2, full) — no fractional spans. Mobile order = top-to-bottom stacking order after grid collapse (lower number stacks higher).

### Blueprint
| # | Widget | Settings (prop → FULL $$type envelope) | Tag wrap | Dynamic affordance (per prop) | Role | Expected DOM | Pre-resolved (Post A/B/C) |
|---|---|---|---|---|---|---|---|
| 1 | ef-card | _cssid: "<section-overview-body>"; heading rows: [{tag: h2, text: @post(title), text-affordance: on}, {tag: p, text: @post(<field>), text-affordance: on}, ...] | @tags() | text-row-0: on (text), text-row-1: on (text); _cssid: vx envelope | dynamic-card | <article class="<section-overview-body>"><h2>{title}</h2>...</article> | "<post A title>" / "..." / "..." |
| 2 | ef-card | _cssid: "<section-overview-aside>"; heading rows + tag-row {<relation>} | @tags() | tag-row.text: on (dynamic from relation field); heading text: on | dynamic-card | <aside><ul><li>{relation.title}</li></ul></aside> | "<item / item / ...>" / empty / "..." |
| ... | | | | | | | |
```

**Mandatory columns (Blueprint):**

- **Widget** — must appear in the §2b Widget Catalog.
- **Settings** — every prop the plan binds, written as the **FULL `$$type` envelope**, not the raw value. Example: instead of `text: @tags()@post(title)@endtags()`, write `text: {$$type: string, value: "@tags()@post(title)@endtags()"}`. Responsive primitives MUST include every breakpoint's sub-envelope: `cols: {$$type: ef-responsive-string, value: {desktop: {$$type: string, value: "2fr 1fr"}, tablet: {$$type: string, value: "1fr"}, mobile: {$$type: string, value: "1fr"}}}`. Missing inner `$$type` markers cause EF to silently drop the prop at render — the `wpdev elementor:lint` envelope check catches this (added 2026-05-29). Use the PHP factory `EF\Envelope::responsive_string(...)` / `EF\Envelope::image(...)` / `EF\Envelope::vx_visibility(...)` in mutator scripts to avoid hand-authoring envelopes (see `actions.md` §Loopable action-rows). Reference the corresponding **Widget placement row** by `# index` — the orchestrator splices grid props from the Layout map into `_cssid`'s `cols` / `col_span` envelope at fan-out, so the Blueprint Settings column does NOT duplicate grid declarations.
- **Tag wrap** — `@tags()...@endtags()` for any CPT-template string (Rule 5 / [`voxel-tags.md`](../references/voxel/voxel-tags.md)); raw `vx` envelope for `_cssid` and image refs; static literal otherwise.
- **Dynamic affordance (per prop)** — for every prop in Settings, name its dynamic-affordance state: `on` when the value is a dynamic tag (`@tags()...@endtags()` or `@post(...)` etc.) — produces a `vx-dynamic` envelope at the EF V4 atomic-prop level; `off` when the value is a static literal — produces a plain `string` envelope; `vx envelope` when the prop type itself carries the affordance (image, link, `_cssid`, etc.). The data-wiring criterion checks this column against the Settings column — `@post(title)` text with affordance `off` is the classic "@-leakage" bug. List affordances per prop, comma-separated; for repeater rows, list per-row (e.g. `text-row-0: on, text-row-1: off`).
- **Role** — one of `static-card | dynamic-card | loop-host | loop-child | sidebar | feed | global-passthrough` (matches the role taxonomy from [`build.md`](build.md)).
- **Expected DOM** — a one-line HTML sketch the verification phase will assert against (selectors + expected text source). MUST cite the `_cssid` from the Settings column.
- **Pre-resolved** — for every dynamic tag, the value `wpdev voxel:data` returned on each post in the sample. A row of empty cells across the sample is a wiring red flag the data-wiring adversary surfaces.

**Improvements log (migration mode — required when the migrated copy diverges from production):**

The migration-preservation criterion compares the plan against the rendered text of the live production page (captured via the `agent-browser` CLI — [`browser.md`](../references/verification/browser.md) §Production-page baseline). Any information unit on production that does NOT appear in some Blueprint cell AND is NOT acknowledged in the Improvements log is a silent drop (severity `C` finding). The log shape is `improvement:<unit_id> → <new text>` (with the original text in parens) for rewrites, or `removed:<unit_id> → <reason>` for deletions. The operator inspects the log at §2g approval — it's the explicit audit trail of "what changed and why," not a forbidden-edit list.

**Layout map + Semantic HTML invariants (the hierarchy criterion enforces ALL of these):**

*Layout structure:*

- Every section has a Layout map block before its Blueprint. Missing Layout map → finding (severity `C`).
- Every Blueprint row has a corresponding Widget placement row. Mismatched count → finding (severity `C`).
- Let the content's hierarchy decide column count; prefer more sections over more columns. A grid that fights the content → finding (severity `I`) requesting justification.
- Mobile collapses to `1fr` unless the desktop grid is a small counter row of atomic items. Wrong mobile collapse → finding (severity `I`).
- No fractional col-spans. `col-span: 1.5` is invalid in CSS Grid — use named spans (1, 2, full).
- Background / vertical-rhythm / section-width values must come from the design token list (the planner cites the list — never hand-authored color values, never px / rem literals).
- Sticky behavior is only allowed on archetypes that declare it in §2c (sidebars in long-content templates).

*Semantic HTML wrapper hierarchy (every plan must satisfy this — SEO + accessibility critical):*

- The Plan Document declares a single **root wrapper** — `ef-wrapper` with `tag: main` at depth 0 of `_elementor_data`. There is exactly ONE `tag: main` per page. Multiple or missing main → finding (severity `C`).
- Each top-level section is its own `ef-wrapper` with `tag: section`, nested inside the root main. A `tag: section` at root (without main parent) → finding (severity `C`).
- Sidebar regions use `tag: aside`, NOT `tag: section`. Inline cards inside a section's grid use `tag: article` (when the card is independently meaningful — request listing, company listing) OR `tag: div` (when purely structural). Wrong tag → finding (severity `I`).
- Global templates (`header` template, `footer` template) use `tag: header` / `tag: footer` at root — these are out of single-template scope but the rule applies if the plan touches them.
- `tag: div` / `tag: span` are the fallback ONLY when no semantic tag fits (e.g. inner grid-item wrapper that's not meaningful). Every `tag: div` on an ef-wrapper at depth ≤ 2 → finding (severity `I`) — almost always a missed semantic-tag opportunity.

*SEO-compliant heading hierarchy (every plan must satisfy this — the hierarchy criterion walks document order):*

- Exactly ONE `h1` per page. The h1 lives on a heading row inside the hero section's ef-card, bound to the CPT's title-class field (typically `@post(title)`). Static h1 → finding (severity `C`) unless `override:` justifies (rare — only for landing pages with no dynamic title). Zero or >1 h1 → finding (severity `C`).
- Each section's first heading-row is `h2`, naming the section's purpose (`Overview`, `Services`, `Frequently asked questions`, etc.). Sections without an h2 → finding (severity `I`) — operator may override for purely visual sections like a CTA-footer that doesn't need a heading.
- Nested headings inside a section are `h3` (specs-grid item titles, FAQ questions, related-feed item titles). No `h2` inside another section's `h2` block. No skip from `h2` to `h4`. Skip detected → finding (severity `I`).
- The leading **eyebrow** (the kicker directly above a card's main heading) → a `kind: byline` row (rendered `.ef-ih-byline`). Other decorative text — taxonomy-pill labels, `"service: "` labels, sub-labels, taglines → `kind: heading, tag: span, style: ''` (plain) or `style: label` (small-caps pill, runtime-valid) or `kind: rich_text` (`tag: p`), NEVER an `h*` tag, and NEVER `style: byline_label` (migrated-away — use `kind: byline`). A `kind: byline` row anywhere other than the leading eyebrow → finding (severity `I`). Decorative content as `h*` → finding (severity `C`) — dilutes the heading outline, hurts SEO crawl. A `style: byline_label` value → finding (severity `C`).
- Body paragraphs inside heading rows → `tag: p`. Paragraphs accidentally rendered as `tag: span` or `tag: div` → finding (severity `I`).
- Card heading rows that are NOT the first row in their card (the card title) → must be `h3` or deeper if the card itself is inside an `h2`-headed section. A card with two `h2` rows → finding (severity `I`).
- The criterion walks the full document-order heading sequence `[(section_id, widget_id, row_index, tag, source_field_or_static, text_preview)]` and asserts the sequence reads as a valid outline: `h1 > h2 > h3 > h2 > h3 > h3 > h2 > h3` is fine; `h1 > h2 > h4` is not; `h1 > h2 > h2` inside the same parent is not.

**Section ordering rule.** The plan declares a section order in the Plan Document's top-level table. The hierarchy criterion checks that the order produces a valid heading sequence (h1 once, h2 per section, h3 nested inside h2, no skips) AND a valid layout flow (no aside before its main, no footer before content sections).

**Exit:** every section that appeared in §2c has Improvements-log (if applicable) + Layout map + Blueprint; every cell is filled (empty cells where data is genuinely empty are marked `(empty)` not blank); every Blueprint row has a Widget placement row.

## Phase 2e — Adversarial review fan-out (parallel)

**Goal:** stress-test the Plan Document against the criteria checklist. The orchestrator reads [`criteria.md`](../references/core/criteria.md), **selects every criterion with `phase ∈ {plan, both}` whose `scope` is in play, and dispatches one atomic-scope `voxel-plan-reviewer` subagent per criterion** (each given a single `criterion_id`), all as one fan-out. The checklist is the SSOT — to add, remove, or retune a check, edit a row in `criteria.md`, never this pipeline. No criterion reads another's brief; no finding shadows another; the orchestrator aggregates.

**Preferred (Workflow opted in):** dispatch the per-criterion reviewers as a single `parallel()` inside the §2e Workflow, each leg a schema-returning `agent()` call so the findings come back already structured (no free-text normalizing):

```
parallel(criteria.map(c =>
  () => agent(reviewerBrief(c), {agentType: 'voxel-builder:voxel-plan-reviewer', schema: FINDINGS})))
```

The Workflow returns one findings array per criterion; **the orchestrator then reconciles in §2f** — reconciliation, the convergence guard, and the §2g gate are orchestrator-owned reasoning between fan-outs and stay OUTSIDE the Workflow. A re-review after a plan revision is a fresh §2e Workflow; `resumeFromRunId` returns cached findings for criteria whose plan slice did not change, so only the touched criteria re-run.

**Fallback (inline):** dispatch one `voxel-plan-reviewer` per in-scope criterion in a single message, each given a single `criterion_id`, then aggregate the returned findings by hand.

The plan-phase criteria are the `phase: plan` rows of [`criteria.md`](../references/core/criteria.md) (scopes `page` / `section` / `widget` / `prop`); each criterion's full attack protocol lives in [`voxel-plan-reviewer.md`](../references/subagents/voxel-plan-reviewer.md), keyed by `criterion_id`. The orchestrator does **not** re-enumerate them here — it reads the checklist and dispatches one agent per in-scope row, so adding, removing, or retuning a criterion is a one-row edit to `criteria.md`, never a change to this pipeline. (`migration-preservation` is the migration-only row; build mode skips it.)

**Dispatch rule (atomic-scope contract — [`parallel-dispatch.md`](../references/core/parallel-dispatch.md)):**

- The applicable criteria — every plan-phase row in [`criteria.md`](../references/core/criteria.md) whose scope is in play — are dispatched as **one fan-out** (one `parallel()` under Workflow, one message inline), default to the full applicable set, narrowed only with a stated reason recorded in the plan.
- Each agent's input is **the same Plan Document** (`/tmp/plan-<post_id>.md`) plus a single `criterion_id` from the checklist.
- Each agent's output is an array of findings: `[{criterion_id, finding_id, severity: C|I|K, evidence: '<quote-or-cli-output>', suggested_fix: '<one-line>'}]`.
- Cross-criterion findings (a `coverage` agent noticing a hierarchy bug) are dropped — each agent reports only within its one criterion. The orchestrator catches what falls through the gaps.

**Exit:** all dispatched criteria agents have returned; `/tmp/plan-review-<post_id>.md` contains the merged findings sorted by criterion then severity.

## Phase 2f — Findings reconciliation (finding bus + convergence guard)

**Goal:** every Critical and Improvement finding from §2e is addressed before Phase 3 — by computed outcome, not by an operator eyeballing prose.

**Finding bus (#19 — one structured channel).** Each §2e agent appends its findings to `/tmp/findings-<post_id>.jsonl`, one JSON object per line: `{criterion_id, finding_id, severity, scope, evidence, suggested_fix, outcome?}`. Reconciliation, the convergence guard, and the §2g gate all read this one file — never re-parse prose. `/tmp/plan-review-<post_id>.md` is the human-readable rendering of the same bus.

**Reconciliation rule (every finding gets a machine-readable outcome).** For each finding the orchestrator sets `outcome` on its bus row to exactly one of:

- **`resolved`** — the plan was revised; cite the diff (section ID + what changed). The relevant §2d blueprint table is updated.
- **`override: <reason>`** — acknowledged, intentionally not acted on. **Override-validity (#5) is itself a criterion:** the reason must be concrete and cite evidence — it FAILS (and the finding stays open, severity escalated to `C`) if it matches the generic-reason predicate `/(out of scope|for later|not important|not relevant|won't fix)/i` or carries no evidence. An invalid override is never a silent pass.
- **`deferred`** — real but tracked for a follow-up build (links the issue / TODO).

Cosmetic (`K`) findings batch into one `acknowledged` block.

**Convergence guard (#15 — provable termination, no luck, no magic cap).** Define `open_C = { finding_id | severity==C AND outcome ∉ {resolved, valid-override} }`. Whenever the plan materially changes, re-run the in-scope criteria against the revised plan — each re-run is a fresh §2e fan-out (a new §2e Workflow when opted in, which caches unchanged criteria via `resumeFromRunId`; an inline single message otherwise). The loop itself — deciding whether to re-run, recording `|open_C|`, judging convergence — is **orchestrator-owned and lives between fan-outs, never inside a Workflow.** Each iteration the orchestrator records `|open_C|` and the set fingerprint. **The loop may continue only while `open_C` strictly shrinks** (an iteration that does not reduce the open-Critical fingerprint set is non-converging → halt and escalate to the operator with the residual). This replaces any fixed iteration cap: termination is guaranteed because a strictly-decreasing finite set bottoms out at ∅ (green) or stalls (escalate).

**Exit:** every bus row has an `outcome`; `open_C == ∅` OR the residual has been escalated; §2d revisions match the resolutions.

## Phase 2g — Gate (autonomous by default, human on exception)

**The gate is computed, not approved by default (#4).** Phase 3 fan-out proceeds automatically when ALL of:

1. `open_C == ∅` — every Critical criterion is `pass` or carries a *valid* override (per §2f override-validity).
2. Every Improvement (`I`) finding has an `outcome` on the bus (no silent ignores).
3. **Plan structural validation (#13):** the Plan Document contains every required section (§2a Field Inventory, §2b Widget Catalog, §2c Archetype Selection, §2d Blueprints + Layout maps, §2e findings, §2f reconciliation) per §Plan Document structure — a missing/empty required section fails the gate before fan-out — and `wpdev elementor:codegen --check` passed at entry (drift gate, rule 1).

When the computed gate is green the orchestrator writes `GATE: green (auto)` to the Plan Document and proceeds — **no human approval is required for a green gate.** Autonomy is safe here precisely because every clause above is a predicate, not a judgment.

**Human is the exception path, not the keystone.** The orchestrator escalates to the operator ONLY when the gate cannot go green on its own:
- a Critical finding the auto-repair loop could not resolve (`open_C ≠ ∅` after the convergence guard halts),
- an `override` whose validity is genuinely a judgment call the predicate can't settle,
- or a run the caller explicitly flagged `--require-approval` (high-stakes templates, global header/footer).

On escalation the operator writes exactly one of: `APPROVED` (force the gate green, overriding the residual — logged with the operator as author), `REVISE: <instructions>` (re-enter §2c–§2f), or `REJECT: <reason>` (halt). Silence is not approval and not proceed — an escalated, unanswered gate blocks.

**Exit:** the Plan Document carries `GATE: green (auto)` or an operator `APPROVED`; control returns to the caller pipeline (Phase 3 — widget fan-out).

## Plan Document structure (the artifact at `/tmp/plan-<post_id>.md`)

```markdown
# Plan — <site> post <post_id> (<cpt_key>)

Pipeline: build|migration
Example posts sampled: <id_A>, <id_B>, <id_C>
SSOT artifact: cli/src/generated/widget-schemas.json (sha: <hash>)

## §2a Field Inventory

| Key | Type | Label | Post A | Post B | Post C | Class | Target section |
| ... |

## §2b Widget Catalog

| Widget | Source | Props count | Row surfaces | Use case |
| ... |

## §2c Archetype Selection

| Section ID | Archetype | Purpose | Fields bound |
| ... |

## §2d Section Blueprints

### Section: hero — hero
| # | Widget | Settings | Tag wrap | Role | Expected DOM | Pre-resolved (A/B/C) |
| ... |

### Section: specs — specs-grid
| ... |

...

## §2e Adversarial review

(populated by Phase 2e — one block per criterion)

### Coverage findings
- finding_id: COV-1  severity: C
  evidence: "field `<multiselect-field>` is must-class on part of the sample but no target section"
  suggested_fix: "add to specs-grid"

...

## §2f Reconciliation

### COV-1
resolved: added `<multiselect-field>` to specs-grid blueprint row 3

### DEN-2
override: density is intentionally lower than the peer single because these posts are short-lived and the related-feed archetype dominates discovery

...

## §2g Gate

(orchestrator writes the computed verdict; operator only on escalation)

GATE: green (auto)
```

## How build.md and migrate.md invoke this

Both reference files' Phase 2 sections delegate here entirely. Their pipeline tables now read "Phase 2 — see [`page-planning.md`](page-planning.md)" — no parallel planning prose lives in either of them.

The pipelines differ only in:
- **build** mode: the full panel minus migration-preservation dispatched in §2e (migration-preservation skipped).
- **migration** mode: the full panel including migration-preservation dispatched in §2e (migration-preservation enforced).

Everything else — inventory, SSOT read, archetype selection, blueprint composition, reconciliation, the computed gate — is identical.

## Mistake guards

- Never skip §2e adversarial review for non-trivial builds/migrations.
- Never let a reviewer rewrite the plan; reviewers return findings only.
- Never advance past §2g while any required criterion is red or unresolved.

## Anti-patterns (HARD)

- **Skipping §2a Field Inventory.** "I know what fields this CPT has" is the failure mode that produced a data-rich CPT rendered as a near-empty single-`ef-card` template. Every plan reads `voxel:fields` AND `voxel:data` on a representative sample of real posts.
- **Picking widgets from memory in §2b.** The committed SSOT exists for a reason — every widget pick comes from `cli/src/generated/widget-schemas.json`. If the artifact is stale, regenerate via `wpdev elementor:codegen`.
- **Inventing archetypes in §2c.** Reuse from the §2c catalog. If a new archetype is genuinely needed, dispatch the pattern-reuse adversary explicitly and ask it to find a peer template — silently inventing a one-off shape is the failure mode that produces site-wide visual inconsistency.
- **Single-pass §2e.** Whenever the plan has materially changed, re-run the adversaries — they review the revised plan, not the original.
- **Writing before the §2g gate is green.** A green gate is computed (`GATE: green (auto)` — every Critical criterion `pass`/valid-override) or, on escalation, an operator `APPROVED`. "Looks good" / "go ahead" are never the gate.
- **Inline-only blueprint.** Phase 3 (fan-out) reads the blueprint tables as the per-widget brief; if blueprints are missing rows, the widget builders fill the gaps from memory — which is what this whole pipeline exists to prevent.
- **Treating `must` and `should` as advisory.** They aren't priorities; they're classifications that bind the coverage adversary. A `should`-class field that the plan doesn't surface is a finding the coverage adversary emits — same as `must` — just with severity `I` instead of `C`.

## When to use this pipeline

- Building a single / archive / page template for a data-rich CPT.
- Migrating any V3 page off legacy widgets onto EF V4 atomics.
- Adding a new section to an existing template (mini-version: pipeline scoped to the new section only; the operator approves the section-level blueprint, not the whole-page rewrite).

## When NOT to use this pipeline

- Preview cards (the cards flow (`workflows/build.md` §Cards) is purpose-built and idempotent — see [`build.md`](build.md) §Cards).
- Single-widget surgical patch (e.g. fixing one `_cssid`, swapping one icon). Use the [`build.md`](build.md) §Modifying existing data path with the Behavior Contract instead.
- Global templates (header / footer / 404) that are site-wide and rarely change — direct edit is faster.
- Schema-detective queries (the schema introspection flow (dispatch the `voxel-schema-detective` subagent — `references/subagents/voxel-schema-detective.md`)) — they're read-only introspection.
