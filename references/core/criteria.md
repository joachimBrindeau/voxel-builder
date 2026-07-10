# Criteria checklist — the scope-indexed SSOT for review + verification

> **Machine SSOT: [`criteria.json`](criteria.json)** (schema: [`criteria.schema.json`](criteria.schema.json)). That structured file is what the orchestrator loads and dispatches from — `{id, scope, phase, severity, criterion, evidence, predicate}` per row. **This markdown is the human-readable view of the same rows; when the two disagree, `criteria.json` wins.** Add/remove/retune a check by editing a row in the JSON (validate against the schema), then mirror it here.

**The checklist is the single source of truth for what gets checked, at which scope, in which phase.** The orchestrator selects every applicable row and sends them to bounded reviewer batches using [`parallel-dispatch.md`](parallel-dispatch.md). Adding, removing, or retuning a check means editing a row, never the pipeline.

## Model

- **Scope** — the hierarchy level the criterion applies to: `page` / `section` / `widget` / `prop`. The orchestrator dispatches a criterion only when its scope is present in the work (a page always has `page`; `section` fires once sections exist; `widget` / `prop` fire for every non-trivial widget tree).
- **Phase** — when the criterion runs: `plan` (checked against the Plan Document before fan-out, §2e), `render` (checked against the live browser after write, Phase 6), or `both`.
- **Severity** — `C` (Critical — blocks approval / fails verification), `I` (Improvement — must get a reconciliation outcome), `K` (Cosmetic — batch-acknowledge).
- **Evidence** — the read/CLI/browser action that produces proof for the finding. The agent runs it; it never asserts from memory.

Each returned leaf checks exactly one criterion and stays within that remit. A worker may process 5-10 criterion leaves, returning a separate envelope for each.

## Dispatch rule

1. **Plan review (§2e):** select every row with `phase ∈ {plan, both}` whose `scope` is in play. Batch 5-10 criteria per reviewer and require one leaf envelope per criterion. Drop a criterion only with a stated reason recorded in the plan.
2. **Browser verification (Phase 6):** select every row with `phase ∈ {render, both}` whose `scope` is in play. Batch 5-10 URL/surface leaves per verifier while preserving per-criterion results.
3. **Re-run** the applicable set whenever the artifact (plan or rendered page) has materially changed; stop when it converges; surface residuals to the operator if it won't.

## The catalog

### Scope: page (plan)

| id | phase | severity | criterion | evidence |
|---|---|---|---|---|
| `coverage` | plan | C/I | **Computed set-diff (#6), not a judgment:** `set(fields_with_data) ⊆ set(bound ∪ omitted-with-valid-reason)`. Every field with data on the sample is surfaced or carries an `omit:<reason>` that survives challenge. One finding per unsurfaced field. | `wpdev voxel:fields` + §2a Field Inventory + sampled `voxel:data` |
| `density` | plan | I | The plan's section/widget count matches what the CPT's data shape supports, judged against peer templates. Flags thin plans; demands per-section justification below the peer norm. | `wpdev voxel:templates` + `wpdev elementor:tree <site> <peer_id>` |
| `relations` | plan | C | Every post-relation field with data is surfaced (inline list, sidebar, or relation-feed) AND its traversals (`@post(<relation>.<field>)`) actually appear in a blueprint. | §2a relations rows + §2d blueprints |
| `hierarchy` | plan | C | Exactly one `tag: main` root; exactly one `h1` (hero, title-bound); document-order reads as a valid `h1 → h2 → h3` outline, no skips, no second h1, no h2-inside-h2. | §2c wrapper tags + §2d heading rows in document order |
| `section-order` | plan | I | The declared section order yields both a valid heading sequence and a valid layout flow (no aside before its main, no footer before content). | Plan Document top-level section table |
| `ssot-integrity` | plan | C | Every widget named exists in the schema SSOT (`cli/src/generated/widget-schemas.json`) or has an atomic fixture; every bound prop exists in that widget's prop list with the recorded `$$type` envelope. | `cli/src/generated/widget-schemas.json` + `examples/<widget>.json` |
| `pattern-reuse` | plan | I | Archetypes and dynamic-heading phrasings match the conventions peer templates already use; any new shape is justified by a peer comparison. | `wpdev elementor:tree <site> <peer_id>` + heading-curator palette |
| `rebuild-vs-revise` | plan | I | The Phase 0 rebuild-vs-revise call is recorded and justified — greenfield when the existing tree is worse than starting clean, otherwise in-place. | Plan Document Phase 0 note + `wpdev elementor:tree` |
| `migration-preservation` | plan | C | *(migration only)* Every information unit on the production page appears in a blueprint cell OR is acknowledged in the §2d Improvements log. Silent drops fail; declared rewrites/removals pass. | production rendered text via `agent-browser` (see [`browser.md`](../verification/browser.md)) |
| `claude-seo-baseline` | plan | C | *(authoring builds — geo derivation / CPT-single copy / bulk excerpt-meta / content-surgery)* A claude-seo BASELINE gap-list was captured on the LIVE **source** page via native skill invocation or the read fallback **before** authoring. Advisory intent ≠ satisfied — a written `/tmp/BASELINE-<slug>.md` must exist. See [`../voxel/claude-seo-authoring.md`](../voxel/claude-seo-authoring.md) §1. | `/tmp/BASELINE-<slug>.md` plus the native skill name or dynamically resolved `seo-local/SKILL.md` path used on the live source URL |

### Scope: section (plan)

| id | phase | severity | criterion | evidence |
|---|---|---|---|---|
| `wrapper-semantics` | plan | C/I | Each section's wrapper tag fits its role (`section` content, `aside` sidebar, `article` self-contained card, `main` root only); `div` at shallow depth is a missed-semantic-tag flag. | §2c/§2d Section wrapper props |
| `grid-fit` | plan | I | Column count follows the content's hierarchy; **more sections over more columns**; collapses to one column on small screens; no grid that fights the content. | §2d Layout map grid tracks |
| `section-heading` | plan | I | Each section's first heading is an `h2` naming its purpose; the leading eyebrow (one per card, directly above its heading) is a `kind: byline` row; no other decorative text is a heading. `style: byline_label` is migrated-away (use `kind: byline`) — flag any occurrence (severity `C`). | §2d heading rows + kind/style props |

### Scope: widget (plan)

| id | phase | severity | criterion | evidence |
|---|---|---|---|---|
| `widget-in-catalog` | plan | C | Every widget in a blueprint appears in the §2b Widget Catalog (schema SSOT or atomic fixture). | §2b + `cli/src/generated/widget-schemas.json` |
| `blueprint-complete` | plan | C | Every blueprint row has all mandatory cells filled and a matching Widget-placement row; no cell left blank (genuinely-empty → `(empty)`). | §2d tables |
| `ts-fixture-bound` | plan | C | Every `ts-*` widget's shape comes from a complete atomic fixture under `examples/`, and every post-ID reference it carries (`ts_card_template__*`, `ts_post_to_feed`, `connect_map`, …) is a live post on the target site. | `examples/<widget>.json` + `wp post get <ref_id>` |

### Scope: prop (plan)

| id | phase | severity | criterion | evidence |
|---|---|---|---|---|
| `data-wiring` | plan | C/I | Every dynamic tag resolves non-empty on the sample (or declares a fallback); the dynamic-affordance switch matches (on for tags, off for literals); the `$$type` envelope matches the SSOT. | sampled `wpdev voxel:data` + `cli/src/generated/widget-schemas.json` |
| `tag-wrap` | plan | C | CPT-template strings are wrapped `@tags()…@endtags()`; `_cssid` and image refs use the raw `vx` envelope; static literals are neither. | §2d Settings + Tag-wrap columns |
| `design-tokens` | plan | I | Colors, spacing, widths come from design tokens — never hand-authored hex/px/rem literals. | §2d Layout map + Settings |
| `content-methodology` | plan | C | *(authoring builds)* Every authored reader/SERP-facing field (`h1`, `hook`/meta, `description`, `faq`, `conversion-*`, `post_excerpt`) was produced through claude-seo content methodology (Read-fallback of `seo-content-brief` + `seo-local`): keyword placement, meta length ≤`LEAN_SEO_DESC_LIMIT`(155)/target 120–152, stated **information gain** vs source, swap-test + ≥500-word/>60 %-unique for location pages, E-E-A-T. Not ad-hoc prose; no fabricated program/stat. See [`../voxel/claude-seo-authoring.md`](../voxel/claude-seo-authoring.md) §2. | authored field values vs the §2 checklist; swap-test; word/char counts |

### Scope: render (browser, Phase 6)

| id | scope | phase | severity | criterion | evidence |
|---|---|---|---|---|---|
| `selector-found` | section/widget | render | C | Every planned `_cssid` / known selector is present in the DOM (CSS was regenerated; widget actually rendered). | `agent-browser` wait-for-selector |
| `no-tag-leak` | prop | render | C | No literal `@post(...)` / `@tags()` text leaks into the rendered HTML. | `agent-browser` get text / HTML scrape |
| `layout-assert` | section | render | C | Computed section width, grid tracks, inherited `--ef-cols`, and hero tag match the Layout map. | `agent-browser` computed-style `eval` block ([`browser.md`](../verification/browser.md)) |
| `no-console-errors` | page | render | C | No console errors and no page errors at runtime. | `agent-browser` console + errors |
| `screenshot-read` | page | render | C | Full screenshot taken AND read — hero present, sections laid out as planned, feeds filled. | `agent-browser` screenshot --full + read the PNG |
| `text-rendered` | prop | render | I | Expected dynamic values actually appear (empty values confirmed against `voxel:data`, not assumed bugs). | screenshot + `wpdev voxel:data` cross-check |

### Scope: both (silent-failure probes — plan + render)

| id | scope | phase | severity | criterion | evidence |
|---|---|---|---|---|---|
| `relation-loop-self` | widget | both | C | A relation/loop doesn't self-traverse (a post listing itself in its own related feed). | blueprint loop source + rendered feed |
| `css-token-fallback` | prop | both | I | Design-token references resolve (no silent fallback to an unintended default). | computed style vs token |
| `reindex-after-filter` | page | both | I | Feed filters have a matching index-table reindex (feed not silently empty). | feed settings + index table |
| `unicode-integrity` | prop | both | C | No `u00xx` accent corruption in written or rendered text. | regex probe on `_elementor_data` + rendered text |

## Extending the checklist

Add a row in the right scope section with a unique `id`, a `phase`, a `severity`, a one-line `criterion`, and an `evidence` action. The orchestrator picks it up automatically on the next run — no pipeline edit, no new agent. To retire a check, delete its row. To retune severity, edit the cell. The dispatch mechanism never changes; only this data does.
