# Migration Pipeline — legacy Elementor → EF V4 atomics

How to migrate an existing page/template off legacy Elementor V3 (`container` + `heading`/`text-editor`/`button`/`counter`/`nested-accordion`) onto the elementor-framework's EF V4 atomic widgets — **aggressively consolidating** into composite EF widgets while **losing zero data**.

This is distinct from [`audit.md`](audit.md) (find problems) and [`build.md`](build.md) (greenfield build). Migration mutates EXISTING `_elementor_data`, so the [`behavior-contract.md`](../references/verification/behavior-contract.md) gate applies and verification is mandatory.

## The Iron Law

> **Aggressive on structure and styling. Improve content where it earns its keep. Never silently drop information.**

The migration is a chance to do better, not a transcription job. Three concerns, separated:

1. **Structure is fungible.** Drop V3 wrappers, collapse legacy widgets into composite EF widgets, reshuffle section order — that's the whole point.
2. **Content is improvable.** Fix typos. Modernize stale copy. Tighten verbose paragraphs. Fix factual errors. Sharpen CTAs. Improve heading hierarchy. Migration is the chance to do this — taking the chance is encouraged.
3. **Information is the floor.** A feature paragraph, a CTA, a service line, a price, a phone number, an answer in an FAQ — if it was on production, it must be on the migrated page OR explicitly declared in the §2d Improvements log as `improvement:<unit_id> → <new text>` or `removed:<unit_id> → <reason>`. Silent drops fail the migration-preservation criterion; declared improvements pass.

**The baseline for "did we preserve the information?" is the PRODUCTION page's rendered markdown, not the legacy `_elementor_data` dump.** The legacy dump carries V3 wrapper noise, dead styling, plugin pollution (`eael_*`, `jet_*`), and admin-only fields that never reach the visitor — flagging those as "missing" produces false positives. The page-planning §2e migration-preservation criterion reads the live production page's rendered text via the `agent-browser` CLI ([`browser.md`](../references/verification/browser.md) §Production-page baseline — it renders JS, so dynamic tags resolve as a visitor sees them), decomposes into **information units** (claims / facts / offers / CTAs / features / services / prices / instructions / headings — not words, not sentences), and asserts every unit either appears in some §2d blueprint cell OR is acknowledged in the Improvements log. Improvements are first-class — the contract is "no silent drops," not "no edits."

The framework does **NOT** auto-restyle legacy widgets at render (no `elementor/widget/render_content` hook; only the versioned data migrator under `migrations/steps/` rewrites EF's OWN widget shapes). So legacy `heading`/`text-editor`/`button`/`counter` left in place stay unstyled — they MUST be converted to EF widgets to enter the design system.

## DROP aggressively (structure + styling)

Everything here is noise the EF render path ignores — never carry it over:

- V3 wrapper containers and intermediate nesting (`container > container > container > widget` collapses to one `ef-card`).
- `__globals__`, `background_*`, `flex_*`, `content_width`, `width`, `min_height`, `padding`, `margin`, alignment, `border_*`.
- Plugin pollution: `eael_*` (Essential Addons), `jet_*` (JetElements), `_voxel_dynamic_attrs`, `_ef_loop_more_label` on dead wrappers.
- Decorative "tag-pill" wrapper containers — fold their label into an `ef-card` `content_blocks` row (`kind: heading`) with `style: label` (the pill style). The legacy `byline_label` style value is retired — `label` is the only role-bearing style.
- Counter count-up animation (ef-card renders static text).

## PRESERVE information — improvements are encouraged, silent drops are forbidden

The contract is "every information unit the visitor sees on production either appears in the migrated tree OR is acknowledged in the §2d Improvements log." That's an information-set check, validated by the migration-preservation criterion against the `agent-browser`-rendered text of the live URL ([`browser.md`](../references/verification/browser.md) §Production-page baseline). Inside the planning blueprint, that translates to:

- **Information units (the actual contract).** Claims, facts, offers, CTAs, features, services, prices, instructions, headings. Every unit visible on production must surface somewhere — either in a §2d blueprint cell (verbatim, paraphrased, restructured, or split across multiple cells) OR as an `improvement:<unit_id> → <new text>` or `removed:<unit_id> → <reason>` row in the §2d Improvements log. Silent drops fail the criterion; declared changes pass.
- **Text that should be improved — improve it.** Typos (`<misspelling>` → `<correction>`), awkward phrasing, outdated copy (a stale year reference), unclear CTAs, weak headings — fix them. Add a one-line `improvement:` entry per fix so the operator sees the change at §2g approval. The criterion does NOT flag rewrites that have an improvement annotation. Migration is the chance to do better; take it.
- **Dynamic tags** — preserve the EXPRESSION byte-for-byte (`@tags()...@endtags()`, `@post(...)`, `@author(...)`, `@site(...)`, `.loop_index()`, `.number_format()`) unless the improvement is explicitly to swap a field. The expression resolves to data; changing the expression changes which CPT field gets read, which IS a content edit that needs an improvement line.
- **Legacy `ts-*` nodes whole** (`ts-post-feed`, `ts-print-template`, `ts-user-bar`, `ts-navbar`): preservation-only. If the migration keeps one, re-embed the ENTIRE node (id + every setting) unchanged. These are Voxel theme widgets — never rebuild them, never touch a single feed/template binding (`ts_source`, `ts_choose_post_type`, `ts_card_template__*`, `ts_template_id`), and never introduce a new one. Read existing nodes via `wpdev elementor:dump <site> <ts-widget> --post <id> --json` (or `all --post <id> --json` for the whole tree) and splice verbatim, or replace the surface with EF `ef-wrapper` template/loop wrappers. The migration-preservation criterion rejects any partial reconstruction.
- **Links / destinations**, button targets, anchor `#ids` — the visible button label is improvable content; the target URL is structural data the criterion inspects via the §2d Settings column. Changing the target = improvement annotation.
- **French accents** — emit valid UTF-8; never let `é` become `u00e9` (see root `CLAUDE.md` §Encoding).
- **Per-item content in repeaters** — every FAQ answer, every menu row. Each item is an information unit; improvements need an annotation, but the unit itself must surface or be marked `removed:` with reason.

**Improvements log shape (in §2d, top-of-section, plain markdown):**

```
### Improvements log (this section)
- improvement: hero-tagline → "<new tagline text>" (was: "<old tagline text>")
- improvement: services-list-item-3 → fixed typo "<misspelling>" → "<correction>"
- removed: legacy-stat-block → "<old stat text>" (reason: stat is stale; no current equivalent; replaced by strengthened cta-footer)
- improvement: faq-q3-answer → tightened from 4 sentences to 1
```

What is NOT in this list (and is migration-discardable per the Iron Law): V3 wrapper containers, dead styling props, `__globals__`, plugin pollution. The criterion will not flag missing wrappers — only silent information drops.

## CONVERT (transform, don't drop)

These change shape but keep meaning:

| V3 source | EF V4 target |
|---|---|
| `_voxel_visibility_rules: [[{type:...}]]` (+ `_voxel_visibility_behavior`) | per-row `_vx_visibility: {$$type:"vx-visibility", value:{behavior:"show"\|"hide", rules:[[{type:...}]]}}` — copy the exact envelope from the local header's `ef-navbar` action rows |
| `heading` wrong `header_size: h1` on a non-hero section | `ef-card` heading row `tag: h2` (fix the hierarchy while migrating) |
| `counter` (number + title) | `ef-card`: `content_blocks` heading block `tag:span style:h1` = number (preserve dynamic tag), heading block `tag:span style:''` (plain) = label (the counter label is a caption under the number; the legacy `byline_label` style is retired) |
| `nested-accordion` / legacy `accordion` | one `ef-card` with N `content_blocks` rows, each `kind:"accordion"`, `tag:"h3"`, `text`=question, `body`=answer |
| loose `heading`+`text-editor`+`button` cluster | ONE `ef-card`: byline/heading/`p` heading rows + `ts_actions` action rows |

## Composite mapping (the consolidation target)

Collapse a whole functional region into the single purpose-built EF widget — do not migrate piecemeal. Reference exemplar: a typical header collapses `{banner heading+button, navbar logo+mega-menu+user-bar, mobile nav, breadcrumb}` (a dozen-odd containers + widgets) into ONE `ef-navbar`.

| Region | Target widget |
|---|---|
| Root `<main>` container | `ef-wrapper` `tag:main` (use `elementor:migrate:main`) |
| Section / layout container | `ef-wrapper` (tag from `html_tag` else `div`; `cols` only when horizontal — use `elementor:migrate:containers`) |
| Header / nav / breadcrumb region | one `ef-navbar` (`nav_items` = `ef-mega-rows`, `cta_ts_actions` = `ef-action-rows`, `banner_*`) |
| Content block (label+heading+body+buttons) | one `ef-card` (heading rows + `ts_actions`) |
| Counters / stat row | `ef-card`s (number + label rows) |
| FAQ / accordion | one `ef-card` (accordion heading rows) |
| Table of contents | `ef-toc` · Form | `ef-form` · Calendar | `ef-cal` |

## Entry criteria

1. Target post or template has legacy Elementor/Voxel structure that should become EF V4 atomic widgets.
2. A representative production URL sample exists (`?p=<post_id>` is acceptable for singles).
3. `wpdev elementor:codegen` and `wpdev elementor:codegen --check` pass before mutation.
4. Backup/export path is writable and rollback target can be captured.

## Exit criteria

1. Legacy content is preserved in EF V4 atomic widgets, with every carried text, dynamic tag, link, visibility rule, and `ts-*` setting mapped.
2. `wpdev elementor:lint <site> --post <id>` passes with 0 findings.
3. Browser verification passes on representative production URL sample.
4. Behavior Contract diff shows no Forbidden Semantic Delta.

## Phased workflow

### Phase 0 — Backup + survey + production content baseline
- **Regenerate + drift-check the SSOT first:** `wpdev elementor:codegen`, then `wpdev elementor:codegen --check`. The computed §2g gate (rule 1) asserts this passed at entry, and migration touches the legacy data most likely to have drifted against the current EF V4 schema — never skip it on the migration path.
- `wpdev elementor:export <site> <post_id>` (durable restore point).
- `wpdev elementor:tree <site> <post_id>` + `wpdev elementor:dump <site> all --post <post_id> --json` to map the real structure (the audit's labels can be wrong — trust the data).
- Run `wpdev elementor:revisions:prune <site> --post <id>` unconditionally (snapshot, then prune all revisions to the latest) per [`rules.md`](../references/core/rules.md) rule 6.
- **Resolve a representative sample of production URLs** for the page being migrated (one is never enough). `./wpdev remote:list` returns the live host; the URL is simply `https://<prod_host>/?p=<post_id>` — WordPress 302-redirects to the canonical permalink regardless of post type or rewrite rules. For archive / page templates that aren't single posts: pick a representative sample of post ids of the affected CPT and use `?p=<id>` for each. These URLs flow into Phase 2 as the migration-preservation baseline for the migration-preservation criterion.
- **Cache the production rendered text** ahead of Phase 2 if convenient: `agent-browser --session prod-<id> open "<url>"` → `wait --load networkidle` → `get text body` → `/tmp/prod-content-<post_id>-<url_hash>.txt` (recipe in [`browser.md`](../references/verification/browser.md) §Production-page baseline). The criterion will capture fresh if these are absent; pre-caching just saves a round trip.

### Phase 1 — Structural skeleton (CLI, mechanical, batch-safe)
Run the two structural migrators FIRST — they are clean, idempotent, and site-wide-safe:
```bash
wpdev elementor:migrate:main <site>              # root <main> container → ef-wrapper(tag=main)
wpdev elementor:migrate:main <site> --fix --yes
wpdev elementor:migrate:containers <site> --post <id>            # preview
wpdev elementor:migrate:containers <site> --post <id> --fix --yes
```
- `migrate:main` — every wrapper with `html_tag:main` → clean `ef-wrapper(tag=main)`, settings stripped to `tag`, children preserved. Pixel-identical (root carries no real layout).
- `migrate:containers` — every `container` → `ef-wrapper`; `tag` = `html_tag` else `div`; `cols` = N equal `1fr` tracks ONLY when `flex_direction:row` (N = direct-child count); all other styling dropped. Recurses every depth. Verify 2-col rows stay side-by-side.
- Lint + screenshot after.

### Phase 2 — Plan the migration (mandatory delegation to page-planning.md)

**Same bulletproof sub-pipeline as greenfield build — see [`page-planning.md`](page-planning.md) §2a–§2g — with one structural difference: migration mode adds the `migration-preservation` reviewer to the §2e panel** (default to the full panel — coverage, density, hierarchy, data-wiring, pattern-reuse, relations, ssot-integrity, + migration-preservation when migrating; narrow it only with a stated reason), dispatched in parallel, one concern each. That criterion is the data-loss guard: it walks the legacy `_elementor_data` dump and verifies every leaf with carried data (text, dynamic tag, link, visibility rule, `ts-*` setting) has a target home in the §2d blueprint. Unmapped legacy data = `C`-severity finding the orchestrator must resolve before fan-out.

The two deterministic fan-outs inside that sub-pipeline — the §2c→2d layout fan-out (heading-curator + one layout-architect per selected section) and the §2e adversarial panel (one plan-reviewer per criterion) — express as Workflow `parallel()` legs when the user has opted into multi-agent orchestration, with single-message Agent dispatch as the always-available fallback (full pattern in [`page-planning.md`](page-planning.md)). For the migration §2e panel specifically:

```
parallel(criteria.map(c => () => agent(reviewerBrief(c), {
  agentType: 'voxel-builder:voxel-plan-reviewer',
  schema: FINDINGS,       // findings array, one criterion per call
})))
// criteria includes 'migration-preservation' in migration mode
```

**The judgment gates stay with the orchestrator, NOT inside any Workflow** — the Phase-0 rebuild-vs-revise call, the §2f reconciliation of findings, and the computed §2g gate are orchestrator-owned reasoning between fan-outs. The Workflow runs the mechanical parallel review; the orchestrator reads the schema-validated findings, reconciles, and decides whether to advance. This preserves the author≠reviewer separation and the §2g human-on-exception gate.

Migration-specific inputs to the sub-pipeline (in addition to the standard build inputs):

- `wpdev elementor:dump <site> all --post <id> --json > /tmp/before-<id>.json` (the migration-preservation criterion's source-of-truth).
- `wpdev elementor:tree <site> <id> > /tmp/before-tree-<id>.txt` (the structural skeleton the §2c Archetype Selection maps over).
- The Behavior Contract triple + DOM-text baseline (from [`behavior-contract.md`](../references/verification/behavior-contract.md)) — the command-host authors this BEFORE entering Phase 2; the Plan Document cites it; the re-audit (Phase 4) uses the baseline as the Forbidden-Semantic-Delta check.

Migration-specific §2d blueprint expectation:

- **Every `ts-*` node** in the legacy dump appears verbatim in a §2d blueprint row, with its FULL settings JSON spliced (not re-described, not summarized). The migration-preservation criterion flags any blueprint that references a `ts-*` widget without the verbatim settings block.
- **Every `_voxel_visibility_rules` array** in the legacy dump is translated to a `_vx_visibility: {$$type: vx-visibility, value: {behavior, rules}}` envelope cell in the blueprint, copied from the local header's `ef-navbar` action rows (the local envelope SSOT). The migration-preservation criterion flags drops or shape errors.
- **Every dynamic-tag expression** is preserved byte-for-byte. The data-wiring criterion checks this; the migration-preservation criterion doubles the check against the legacy dump.

### Phase 3 — Content consolidation (parallel fan-out — reads the approved §2d blueprints)

Once Phase 2's §2g gate is green (auto or operator-`APPROVED`), fan out one `voxel-widget-builder` (build mode) per section. This per-section fan-out is the deterministic parallel leg of the migration ([`parallel-dispatch.md`](../references/core/parallel-dispatch.md)) — atomic scope is **one section per builder**.

**Preferred path (Workflow tool, when the user has opted into multi-agent orchestration** — ultracode on, the keyword `ultracode`, or an explicit "use a workflow" request): express the per-section fan-out as a single `parallel()` over the approved §2d rows, dispatching the named builder subagent with a schema that pins the return to a widget-JSON node:

```
parallel(rows.map(r => () => agent(builderBrief(r), {
  agentType: 'voxel-builder:voxel-widget-builder',
  schema: NODE,           // one ef-wrapper(section) subtree per call
})))
// → orchestrator reads the structured nodes, assembles + imports (gate stays outside the Workflow)
```

(Rationale + orphan caveat: [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Expressing a fan-out through the Workflow tool.)

**Fallback path (always available** — small fan-outs, or when Workflow isn't opted into): dispatch all `voxel-widget-builder` subagents **in a single message** ([`parallel-dispatch.md`](../references/core/parallel-dispatch.md)) and aggregate the returned nodes in the orchestrator. For a short fan-out whose result is needed immediately in the same reasoning step, this inline path is simpler and avoids the orphan risk.

Either path, the contract is identical:

1. **Extract a golden ef-card** from the SAME page (`wpdev elementor:dump` → a real `ef-card` node) → `/tmp/golden-ef-card.json`. This is the envelope SSOT; every builder copies its `$$type` scaffolding and swaps only leaf values. Never synthesize envelopes from memory (Rule 1).
2. Each builder receives: golden template path, the section's node id (to reuse), and **its blueprint row(s) from the Plan Document § 2d verbatim** — the row carries the exact content + dynamic tags + visibility + links + verbatim `ts-*` settings. The builder does NOT re-decide; it serializes the approved row to widget JSON.
3. Builders write `/tmp/<section>.json` (a complete replacement `ef-wrapper(section)` subtree) — they do NOT import. (Under Workflow, the `schema: NODE` return carries the same subtree; if builders write files instead, isolate per-section so concurrent writes don't collide.)
4. Orchestrator splices by node id (replace the section subtree, keep the rest), writes once, imports — **this assembly + import is orchestrator-owned, outside any Workflow**:
```bash
wpdev elementor:import <site> <post_id> /tmp/post-new.json --save   # --save regenerates per-post CSS
```
5. Verify (Phase 5) before the next batch.

### Phase 4 — Dedup + cleanup
- Remove half-finished prior migrations (a partial EF section duplicating a legacy one) — keep the COMPLETE source, fold all items in, delete the subset. No data lost when the removed node is a strict subset.
- Delete empty orphan wrappers (0 children) left at root.
- Splice removals in the same id-keyed transform (a `removeSet` alongside the `replaceMap`).

### Phase 5 — Verification (re-audit + browser)

Per the verification gates below, plus the Behavior Contract re-audit: diff the post-mutation DOM-text against the baseline captured before Phase 2; any data-bound value the contract pinned that changed is a Forbidden Semantic Delta → roll back the section, return to §2d, re-fan-out.

When verifying a representative sample of migrated URLs (archive / page templates span many posts), the per-URL verify fan-out is itself a deterministic parallel leg. **Preferred path under multi-agent opt-in:** express it as a Workflow `parallel()` over the sampled URLs, pinning each verifier's return with a pass/fail schema:

```
parallel(urls.map(u => () => agent(verifyBrief(u), { schema: VERDICT })))
// → orchestrator reads the verdicts; the verify→repair loop is a `while`
//   on the convergence guard, OWNED BY THE ORCHESTRATOR (not the Workflow)
```

**Fallback path:** dispatch the per-URL verifiers in a single message and aggregate. Either way, the verify→repair convergence decision — roll back the section on a Forbidden Semantic Delta, return to §2d, re-fan-out, re-verify — is orchestrator-owned reasoning between fan-outs, never folded into the Workflow. Keep each verify Workflow scoped to minutes and watch `/workflows`; a backgrounded run can stall/orphan if the session goes idle or is compacted for a long time mid-run, so for a single-URL check whose verdict is needed immediately, the inline path is simpler.

## Verification gates (every batch — mandatory)

1. `wpdev elementor:lint <site> --post <id>` → **0 findings** (`unknown-prop`/`type-mismatch` block).
2. `wpdev rebuild <site> --only purge` (LiteSpeed + Elementor CSS).
3. Browser ([`rules.md`](../references/core/rules.md) rule 7, tool surface [`browser.md`](../references/verification/browser.md)): the `agent-browser` CLI — `screenshot --full` (read it) + the layout-assertion `eval --stdin` block + these migration-specific assertions (run inside the same `eval` block or via follow-up `get`/`eval` calls):
   - **No tag leakage**: `get text body` contains no literal `@tags(`/`@post(`/`@author(`/`@site(`.
   - **Feeds present**: `get count` of `ts-post-feed` unchanged from before the migration.
   - **Columns**: horizontal sections render as multi-track grids (the layout block's `grid` field has N tracks) — and inner wrappers don't inherit the parent grid.
   - **Expected text** renders for each migrated cluster.
   - **Accordion caveat**: `innerText` EXCLUDES collapsed `<details>` content — assert accordion questions/answers with `textContent`, not `innerText`, inside the same `eval` block, or they read as missing (false negative).
   - **Before/after** (optional, high-value): `diff screenshot --baseline` against the pre-migration render to confirm nothing the Iron Law meant to keep visibly vanished.
4. Widget-count drop is the consolidation receipt (e.g. 73→24). Lint-clean + count-drop + screenshot = done.

## Known losses (flag, don't silently accept)

- **Counter count-up animation** — ef-card is static. Acceptable; note it.
- **`nested-accordion` `faq_schema: yes`** (`FAQPage` JSON-LD) — ef-card does not emit it. Do **not** re-add it for Google rich-result eligibility; FAQ rich results were deprecated on 2026-05-07. Preserve the visible accordion content when it is useful, and only keep/add FAQ schema where a site has a non-Google consumer and the schema is explicitly required.
- **Section backgrounds / spacing / centering** — dropped by the clean swap; re-apply via `ef-card`/`ef-wrapper` `variant` + grid props in a later styling pass, not by carrying V3 keys.

## Editor naming note

`ef-wrapper` navigator labels derive live from the `tag` prop (`assets/js/editor/preview/wrapper.js` → `syncWrapperTitlesDeep` walks the whole tree; broad `change` listener catches V4 atomic control edits at any depth). No `_title` is baked into the data — keep it that way (zero bloat); the label follows whatever tag is selected.

## Mistake guards

- Never preserve styling/structure at the cost of rendered visitor-visible content.
- Never drop legacy `ts-*` settings, dynamic tags, links, or visibility rules from the blueprint.
- Never migrate from one sample URL only when a template renders many records.

## Anti-patterns

- **Rebuilding a `ts-*` widget** instead of splicing it verbatim — one wrong feed binding empties the feed. Always copy the whole live node.
- **Synthesizing `$$type` envelopes from memory** — always copy from a golden node on the same page.
- **Editing content WITHOUT an Improvements-log entry.** Improving copy is encouraged by the Iron Law — but every typo fix, rewrite, or removal MUST get an `improvement:`/`removed:` line in the §2d Improvements log so the operator sees it at §2g and the migration-preservation criterion doesn't read it as a silent drop. The forbidden move is the *silent* edit, not the edit. **Dynamic-tag EXPRESSIONS are the one exception** — preserve them byte-for-byte (`@tags()…@endtags()`, `@post(…)`, transforms) unless the improvement is explicitly to swap which field is read, which itself needs an `improvement:` line.
- **Sequential per-section dispatch** — fan out all sections at once (atomic scope = one section each): a Workflow `parallel()` leg under multi-agent opt-in, or a single-message Agent dispatch as the fallback. Looping the sections one at a time costs N× wall-time for zero correctness gain.
- **Skipping the screenshot** because lint passed — lint can't see a collapsed layout or a feed that silently returns zero.
- **Deleting a "duplicate" without confirming subset** — verify the removed node's data is fully contained in the kept node first.
