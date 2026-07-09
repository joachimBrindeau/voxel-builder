# Audit Pipeline

How to assess an existing page or template and propose fixes by cross-referencing four sources of truth: the **rendered DOM** (agent-browser), the **available data** (Voxel CPT fields + values), the **stored structure** (`_elementor_data`), and the **live schema** (EF V4). Findings feed back into the build pipeline (see [`build.md`](build.md) §Modifying).

Mandatory companion reads before running an audit: [`rules.md`](../references/core/rules.md) (the eight rules; rule 6 prune, rule 7 screenshot, rule 8 plan-pipeline), [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) (atomic-scope contract), [`briefs.md`](../references/audit/briefs.md) (per-tier brief templates), [`behavior-contract.md`](../references/verification/behavior-contract.md) (pre-mutation gate for any existing-data fix), [`browser.md`](../references/verification/browser.md) (the `agent-browser` CLI protocol that Stream D + Phase 5 verification run on), and [`page-planning.md`](page-planning.md) (entered from Pass 2 / Pass 3 whenever a fix adds or restructures sections).

This is read-only until the user approves fixes. The audit produces a categorised findings report; it does not mutate `_elementor_data`. The main agent is the audit orchestrator: it resolves the target, gathers shared streams, dispatches named subagents for page/section/widget/browser scopes, then aggregates and confidence-gates their findings.

## When to run an audit

- "Audit this page" / "review this template" / "what's wrong with X"
- "Why does this card look broken in production"
- "Is this page using the available data well"
- "Find improvements on this template"
- After a third-party migration / DB import where templates may be stale
- Before a non-trivial modification, to know the existing surface and gotchas

For the narrower "I just wrote this — does it render" check, use Phase 6 of [`build.md`](build.md) instead. Audit is broader and looks for *opportunities*, not just regressions.

## Hierarchy + iteration model

The audit walks **top-down** (page → section → widget) so structural problems surface before leaf-level noise; the fix runs **bottom-up** (widget → layout → page) so the smallest-scope changes land first and reveal what the next tier actually needs. The full loop re-runs whenever a fix tier has materially changed the plan; it stops when findings converge, and surfaces the residual to the operator if it won't converge.

```
Audit DOWN          Fix UP                     Re-audit and loop
═══════════         ═══════                    ═════════════════
Global   ────┐                                       ▲
             ▼                                       │
Section  ────┼──→  Widget  ────┐                     │
             ▼                 ▼                     │
Widget   ────┘     Layout  ────┼──→  Page    ────────┘ (re-run until convergence)
                               ▼
                               (re-audit ↺)
```

**Why top-down audit.** A widget-level finding ("byline avatar binds to wrong field") is meaningless if the section it lives in shouldn't exist at all, or if the template is the wrong role for the URL. Walking from page → section → widget lets each tier filter what's worth investigating below it: a section flagged for removal makes its widget findings moot.

**Why bottom-up fix.** Widget mutations are the smallest, safest unit — a single prop change. Layout/section changes (move, group, restructure) touch multiple widgets and are riskier. Page-level changes (add a section, change role assignment) touch the most. Fixing leaves first reduces the diff each step requires, and surfaces higher-tier problems clearly: once every widget renders correctly, gaps and redundancies in the layout become visible *because* nothing else is broken to distract.

**Why loop.** Fixing one tier shifts findings at others:
- Widget fixes can reveal that a now-correctly-rendering widget makes a sibling redundant (section-tier finding).
- Layout fixes can reveal that a widget moved into a new section needs different bindings (widget-tier finding re-emerges).
- Page fixes can reveal that the new section needs widgets that don't exist yet.

A single pass leaves these emergent findings invisible. Re-audit after each fix tier to catch them.

**When to skip the loop.** For a known-narrow scope ("just fix this one widget binding"), one pass through Phase 5 is fine — don't re-audit if the user only approved a single widget fix and nothing structural shifted. The loop pays off when findings span multiple tiers OR when the goal is "make this page good," not "fix this one thing."

## Parallel dispatch + atomic scope

Each tier of the walk fans out to **parallel subagents whose scopes are atomic** — one widget, one section, one global concern. Atomic scope means a finding stands alone: applying its fix doesn't require touching anything in another agent's scope. This unlocks parallel **audit** (fan out per scope unit at each tier) AND parallel **fix** (apply per-widget mutations from a single message; main agent assembles the returns into one `_elementor_data` write).

### Fan-out per tier

| Tier | Fan-out unit | Subagent scope | Wall-time benefit |
|---|---|---|---|
| `[G]` Global | One global-scope audit dispatch, with cheap CLI probes prepared by the orchestrator | Whole page (lint, tree shape, role context, cache freshness, revisions) | Low — included for mode consistency |
| `[S]` Section | One subagent per top-level wrapper | One section's subtree + its DOM region (anchored by `_cssid` / wrapper id) | N×, where N = top-level sections |
| `[W]` Widget | One subagent per non-trivial widget OR per cluster of ≤4 trivial widgets | One widget's settings + its DOM render | M×, where M = non-trivial widgets |

Send all fan-out subagents in **a single message** so they run concurrently. Sequential dispatch defeats the purpose — verifying 8 widgets one-after-another costs 8× the wall time. Same rule applies on the fix side (Phase 5 Pass 1 / Pass 2).

### Workflow-tool orchestration (preferred when opted in)

Every deterministic parallel fan-out in this pipeline — the Stream D browser pool, the `[S]`/`[W]` audit tiers, Pass-1 widget mutations, the Pass-2/3 §2e review panel and widget fan-out, and final verification — is a **Workflow `parallel()` / `pipeline()`** when the user has opted into multi-agent orchestration (ultracode on, the keyword `ultracode`, or an explicit "use a workflow" request), or **inline single-message Agent dispatch** otherwise (always valid; never invoke Workflow unconditionally). The rationale (what Workflow buys) and the orphan caveat are the SSOT in [`../references/core/parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Expressing a fan-out through the Workflow tool.

Atomic scope is unchanged: one scope unit (one criterion / one section / one widget / one URL) per `agent()` call. The audit-specific legs, dispatched via `agent(prompt, {agentType, schema})`:

| Fan-out point | Inline fallback | Workflow expression |
|---|---|---|
| Stream D browser pool (§Phase 2 / Multi-URL) | one browser subagent per URL in one message | `parallel(urls.map(u => () => agent(streamDBrief(u), {schema: STREAM_D})))` |
| `[S]`/`[W]` audit tiers (§3B/3C) | all section + widget agents in one message | `pipeline(sections, s => agent(audit(s), {agentType:'voxel-builder:voxel-page-auditor', schema: FINDINGS}), f => parallel(f.findings.map(verify)))` |
| Pass-1 widget mutations (§Phase 5 Pass 1) | all widget-mutation subagents in one message | `parallel(rows.map(r => () => agent(fixBrief(r), {agentType:'voxel-builder:voxel-elementor-fixer', schema: NODE})))` → orchestrator assembles + imports |
| Pass-2/3 §2e review panel | M plan-reviewers in one message | `parallel(criteria.map(c => () => agent(reviewerBrief(c), {agentType:'voxel-builder:voxel-plan-reviewer', schema: FINDINGS})))` → orchestrator reconciles |
| Pass-2/3 widget fan-out | per-section builders in one message | `parallel(rows.map(r => () => agent(builderBrief(r), {agentType:'voxel-builder:voxel-widget-builder', schema: NODE})))` |
| Final verification (§Editor save) | one verify subagent per sample URL in one message | `parallel(urls.map(u => () => agent(verifyBrief(u), {schema: VERDICT})))`; verify→repair loop = `while` on the convergence guard |

**The orchestrator gates stay OUTSIDE the Workflow.** A Workflow runs ONE mechanical fan-out; the judgment between fan-outs belongs to the orchestrator: the Phase-0 rebuild-vs-revise call, the Phase-4 confidence gate (`confirmed` vs `suspected` / `sme_question` routing), the §2f reconciliation and computed §2g gate on any Pass-2/3 page-planning entry, and the verify→repair convergence decision. Read the structured results, reason at the gate, then launch the next per-phase Workflow — multi-phase work is several scoped workflows in sequence, never one giant workflow that swallows the gates.

### Failure-class taxonomy

The same five **tier** failure classes (`[G]`/`[S]`/`[W]`) recur across the audit tiers — these are the first five of the six in [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Failure classes; the sixth, **Broken Plan Document**, is plan-tier and fires only in the page-planning §2e review, never during audit. Each subagent checks the classes that apply to its scope — name them explicitly in the brief; never leave them implicit.

| Class | Storage signature | DOM signature | Tier where it surfaces |
|---|---|---|---|
| **Broken dynamic tags** | `@post(...)` / `@author(...)` / `@site(...)` unwrapped, mistyped, or referencing a non-existent field | Literal `@post(title)` text leaking; or empty rendered string when source has data | `[W]` |
| **Broken dynamic loops** | `_voxel_loop` / `_vx_loop` source resolves empty; loop tag references the wrong relation/repeater field; iteration heading uses scope-mismatched path | Loop produces zero iterations despite source data being present | `[W]` and `[S]` |
| **Broken filters** | `_ef_loop_transform.filter_*` excludes everything; visibility `compare` operator wrong for field shape (e.g. `is_equal_to` against an array post-relation) | Loop renders nothing OR widget hidden when source data says it should show | `[W]` and `[S]` |
| **Broken visibility** | `_voxel_visibility_rules` / `_vx_visibility` evaluates false on real posts; legacy key on post-relation paths that the legacy evaluator can't navigate | Widget / section never renders | `[W]` and `[S]` |
| **Broken layouts** | Single `ef-card` root-wrapped; depth > 4; sibling wrappers with identical settings; missing required surface (h1, contact); wrong `html_tag` for purpose | Section visually misaligned; required content absent; wrappers without semantic role | `[G]` and `[S]` |

Each finding's report line carries: tier tag (`[G]/[S]/[W]`), severity (`C/I/K`), failure class, evidence, suggested fix.

### Silent-failure detection probes (mandatory)

Four failure modes are **render-valid but semantically wrong** — they pass lint, pass the screenshot check, and produce plausible-looking output, so the ordinary tier walk misses them. Each is a documented production regression. Run all four on every audit. Each emits as a `suspected` finding (Phase 4 confidence gate) carrying a one-line `sme_question`, because a probe may over-fire (a deliberately intentional `var()` fallback, an empty row that is correct) — routing to human review is right; blocking is not. A probe **never** silent-passes: when its introspection tool is unavailable it degrades to flagging the broad pattern as `suspected` with a "source-check skipped" note.

| Probe | Symptom (render-valid, easy to miss) | Detection method | Class · tier | Known-silent-failure source |
|---|---|---|---|---|
| **Relation-loop self-traversal** | A `_vx_loop` over `@post(<rel>)` whose inner tags read `@post(<rel>.<field>)` re-traverses the *iterated* post's relation, so each row resolves the wrong post (or drops to empty). N pills all reading the same wrong value; some rows vanish. | For each `_vx_loop` block in Stream A, take the loop's relation key and scan every inner `@post(<key>.<field>)` tag in the same row. A match on `<key>` = self-traversal. The fix is `@post(<field>)` — the looped post's own field, no relation prefix. | broken dynamic loops · `[W]` (also `[S]` for section-level loops) | `docs/solutions/runtime-errors/voxel-relation-loop-self-traversal-2026-05-02.md` |
| **CSS-token fallback drift** | `var(--ef-token, <fallback>)` where `<fallback>` was transcribed from a stale spec and no longer matches the token. Tokens inject fine in the normal case, so the fallback is dead code — until injection fails and the page silently renders designer-unapproved values. | Grep Stream A stored CSS + rendered DOM `<style>` for `var(--ef-[^,)]+,\s*[^)]+)`. For each hit, resolve the token's canonical value (EF token catalog — `EF_Tokens::DEFAULTS` in the elementor-framework source) and compare to `<fallback>`. Mismatch = drift. Bare `var(--ef-token)` with **no** fallback is the correct convention — never flag it. Degrade: token source unreachable (standalone install) → flag every `var(--ef-…, …)` fallback `suspected`, note "source-check skipped". | broken layouts · `[G]` (per-widget custom CSS → `[W]`) | `docs/solutions/best-practices/css-token-fallback-anti-pattern-2026-04-30.md` |
| **Reindex-after-filter** | A CPT's search filters changed but the index table's column structure wasn't recreated — rows silently drop to 0 on the next reindex, so every feed/loop over that CPT returns nothing while the template itself looks fine. | In `wpdev voxel:status <site>`, flag any CPT whose index row-count is 0 (or far below its published-post count) — the stale-schema signature after a filter change. Cross-check the filter list via `wpdev voxel:fields`. The fix is `wpdev rebuild <site> --only reindex --recreate` (plain reindex against a drifted schema re-drops to 0; `--recreate` rebuilds columns first). | broken filters · `[G]` | `docs/solutions/best-practices/voxel-filters-ontology-2026-04-29.md` §3 |
| **Unicode corruption** | Accented text stored as literal `u00e9` — the backslash was lost through WordPress slashing layers because a write skipped `JSON_UNESCAPED_UNICODE`. `é` renders as `u00e9`. | Grep `wpdev elementor:dump <site> --post <post_id>` for `[a-zA-Z]u00[0-9a-f]{2}` outside legitimate CSS escapes / encoded URLs. The fix is `wpdev elementor:fix:unicode <site>` (Pass 2, site-wide; snapshot first per rule 6). | broken dynamic tags · `[G]` | root `CLAUDE.md` §Encoding |

These probes map onto the five failure classes above (loop / layout / filter / tag) — they are the *specific, silent* instances of each class that the generic walk and the screenshot check let through. Wire them into the tier walks: relation-loop runs in the `[W]`/`[S]` walk (Phase 3C); css-drift, reindex, and unicode run in the `[G]` walk (Phase 3A).

### Atomic-scope contract for subagents

Every subagent brief enforces three rules:

1. **One scope, one report.** A widget agent reports only on its widget's props and that widget's DOM region. A section agent reports only on its wrapper-level concerns. Cross-scope observations get dropped or escalated to the orchestrator — never bundled into a finding from a different scope.
2. **Failure classes named explicitly.** Brief lists which of the five classes the agent must check. Out-of-scope classes (e.g. layout checks at the widget tier when the widget isn't a wrapper) are explicitly excluded.
3. **Findings independently committable.** Phrasing suggested fixes as point mutations. Anything that requires touching another widget/section is reframed as a section-tier or global-tier finding instead.

## Entry criteria

1. User request names a site plus page/template/CPT/card target, or provides a URL that can be resolved to one.
2. `wpdev voxel:templates` or `wpdev elementor:templates` can resolve a template id, except for explicit standalone pages.
3. At least one representative rendered URL exists for DOM/browser Stream D.
4. Audit scope is read-only unless user approves a later fix pass.

## Exit criteria

1. Report groups confirmed findings by tier (`[G]`, `[S]`, `[W]`) and severity (`Critical`, `Improvement`, `Cosmetic`).
2. Suspected findings are separated with `sme_question` and not mixed into confirmed tables.
3. Every Critical finding has concrete evidence from at least one gather stream and a one-line fix route.
4. If fixes are approved, each pass re-audits the mutated scope and converges to zero Critical findings or a surfaced residual.

## Phase 0 — Resolve the template + offer revision prune

Two pre-flight steps that EVERY audit opens with. Skipping either has cost real sessions multiple turns.

**0a. Resolve the template id from the user's request via `wpdev voxel:templates`, NOT raw SQL.** Even if the user names a CPT or page, `voxel:templates` returns the role → post-id map directly:

```bash
wpdev voxel:templates <site>                     # all role assignments + post ids
wpdev elementor:templates <site>                 # editable Elementor template list
```

Raw `mcp__mysql__run_select_query` against `wp_posts` is the fallback ONLY when `voxel:templates` doesn't surface the target (e.g. unbound page post, non-Voxel template). Opening with `voxel:templates` is the default.

**0b. Offer revision pruning before any subsequent fix work.** Audit itself is read-only, but most audits are followed by a fix pass — pre-flighting the prune avoids surprise revision bloat mid-loop:

```bash
wpdev elementor:revisions:prune <site> --post <template_post_id> --dry   # count only
```

Surface the count to the user. If they consent, run without `--dry` (the command snapshots the pre-prune `_elementor_data` to `/tmp/elementor-revisions-<id>-<timestamp>.json` before deleting, so a manual restore via `wpdev elementor:import` against that snapshot is possible).

## Phase 1 — Resolve the target

Determine **what** is being audited and **what URL** renders it. Three target shapes:

| Target shape | Example | URL to navigate |
|---|---|---|
| Standalone page (post) | About, contact, landing page | the post permalink |
| CPT single template | "Treatment" single template | a published post of that CPT |
| CPT card template | "Treatment - small" card | a feed-bearing page (archive / search / parent), card renders inside |
| CPT archive template | Treatments archive | the archive URL (parent page slug) |

Use the `wpdev voxel:templates <site>` output already gathered in Phase 0 to map URL ↔ template. For card templates, the audit URL is the **feed-bearing page**, not the post itself — the card only renders inside a `ts-post-feed` context.

Pick one representative URL per audit. Multi-URL audits are valid (run audit per URL and aggregate), but each subagent owns one URL.

## Phase 2 — Gather (parallel)

Five gather streams. Dispatch in parallel where possible. The orchestrator owns the aggregation. **Re-run on every loop iteration** — the dump and DOM both change after each fix tier.

### Stream A — stored structure

```bash
wpdev elementor:dump <site> all --post <template_post_id> --json > /tmp/audit-data-<id>.json
wpdev elementor:tree <site> <template_post_id> > /tmp/audit-tree-<id>.txt
wpdev elementor:lint <site> --post <template_post_id> > /tmp/audit-lint-<id>.txt
```

`elementor:lint` is the schema-correctness oracle. Its output drives all `unknown-prop` / `type-mismatch` / `enum-violation` / `v3-shape` findings — read it before drilling deeper.

For round-trip editing later, also pull the canonical nested form via `mcp__mysql__run_select_query` against `wp_postmeta._elementor_data` (the `wpdev elementor:dump` output is denormalised flat-array, useful for analysis but not for `elementor:import`).

### Stream B — available data (CPT only)

```bash
wpdev voxel:fields <site> <cpt_key>             # what @post(<key>) tags ARE valid
wpdev voxel:data   <site> --id <example_id>     # what those tags currently RESOLVE to
```

Pick `<example_id>` to match the URL chosen in Phase 1. For non-CPT pages skip Stream B.

### Stream C — live schema

```bash
wpdev elementor:schema <site>                    # widget catalog
```

Per-widget schemas are loaded only by subagents that need them in Phase 3C. The main agent only needs the catalog.

### Stream D — rendered DOM (`agent-browser` CLI subagent)

Dispatch one subagent per URL, each under a unique `--session vb-<post_id>-<n>` (the isolation that prevents the profile-lock degradation — see [`browser.md`](../references/verification/browser.md)). When opted into Workflow, this pool is `parallel(urls.map(u => () => agent(streamDBrief(u), {schema: STREAM_D})))` (see §Workflow-tool orchestration); otherwise dispatch all URL subagents in one message. The brief follows the [`browser.md`](../references/verification/browser.md) command table: `open` → `wait --load networkidle` → `wait` for a known selector → `screenshot --full /tmp/audit-shot-<id>-<n>.png` → `get html "#<root_cssid>"` (save `/tmp/audit-html-<id>.html`) → `console` → `errors` → `network requests` → `get url` → the layout-assertion `eval --stdin` block → `close`. Subagent returns: HTTP status, screenshot path + a written description of what the PNG shows, HTML path, console errors/page errors (separated), network failures, the layout-assertion JSON, and any `eval` counts (e.g. feed-card count via `get count`). There is no `mcp__agent-browser__*` server — this is the `agent-browser` CLI via `Bash`.

### Stream E — context signals (cheap)

```bash
wpdev elementor:revisions:prune <site> --post <template_post_id> --dry   # revision count
wpdev voxel:templates <site>                                             # role assignments
```

## Phase 3 — Walk DOWN (page → section → widget)

Each finding is **Critical** (broken render or schema-invalid), **Improvement** (data underused or structure suboptimal), or **Cosmetic** (housekeeping). Tagged severity letters used in finding ids and subagent reports: **C** = Critical, **I** = Improvement, **K** = housekeeping (Cosmetic; mnemonic: hous**K**eeping). Each finding is **tagged with the tier it belongs to**: `[G]` global, `[S]` section, `[W]` widget. The tier governs fix order in Phase 5. Finding-id grammar is `[<tier>-<severity><n>]` where `<n>` is a positive integer allocated per scope (one subagent's findings start at 1: `[W-C1]`, `[W-C2]`, `[W-I1]`, …).

Each finding also carries a **confidence**: `confirmed` (verified by a concrete method — tool flagged it AND the agent confirmed by reading source/DOM/data) or `suspected` (pattern seen but not cross-confirmed, OR any uncalibrated Silent-failure detection probe hit). `confirmed` findings flow into the tier tables below; `suspected` findings route to the `## Suspected (needs verification)` bucket in Phase 4 and MUST each carry a one-line `sme_question` whose answer resolves the uncertainty. There are no numeric anchors and no cross-agent promotion — two values, and in this HITL flow the human approving each fix is the real confidence gate.

### 3A — Global / page tier `[G]` (single global-scope audit dispatch)

Cheap and singular, but still scoped through the audit contract. The orchestrator
may run the cheap CLI probes that prepare the brief, then dispatches the
global-scope audit work through `voxel-page-auditor` (or executes that brief inline
only when subagent runtime is unavailable). Run this before dispatching `[S]` and
`[W]` agents so global findings can deprioritise downstream scopes (e.g. if the
role assignment is wrong, drilling into widgets is wasted work).

Failure classes covered: **broken layouts** (root-level), cache-freshness signals, revisions.

- **Role-context fit.** Does the template's role (single / card / archive / page) match the URL being audited? A card template only makes sense rendered inside a feed; auditing it on a post URL is a category error. Source: Stream E `voxel:templates` ∩ Phase-1 target shape.
- **Page mission.** Does the tree tell a coherent story? CPT singles need: title or h1, body, contact / call-to-action, related content. Note any *missing required surface*. Source: Stream A tree shape × Stream B field list × role expectations.
- **Tree shape.** Root has single `ef-card` wrapped by `container` / `e-div-block` / `e-flexbox` → suggest `wpdev elementor:strip:wrappers <site> --fix` (the single-ef-card-at-root case folds in `strip:wrappers`; rule-7 §Success-criteria phrases the same command). Depth > 4 → over-structured. Multiple `ef-wrapper` roots without semantic difference → consolidate. Source: Stream A tree.
- **Cache freshness.** No `<link rel="stylesheet" href="…/elementor-post-<id>.css">` in DOM, OR network log shows that file 404 / stale. Treat as Critical only when other rendering breaks; otherwise Improvement (next editor save resolves it).
- **Revisions.** Stream E count > 50 → Cosmetic "offer prune". > 200 → Improvement (DB bloat).
- **Voxel index health + reindex-after-filter probe.** Run `wpdev voxel:status <site>` once per audit. Stale or broken indexes for the post's CPT cause silent feed/loop failures; treat as `[G-C]` Critical when the post's CPT shows non-`OK`. **Reindex-after-filter detection probe** (see Silent-failure detection probes): a CPT whose index row-count is 0 — or far below its published-post count — is the stale-schema signature of a filter change applied without `wpdev rebuild --only reindex --recreate`; emit `suspected` (`sme_question: "were this CPT's filters changed recently without a --recreate reindex?"`), fix is `wpdev rebuild <site> --only reindex --recreate`. Source: `docs/solutions/best-practices/voxel-filters-ontology-2026-04-29.md` §3.
- **Semantic structure.** `wpdev elementor:structure <site> --type <post_type>` flags `<main>`/`<header>`/`<section>` violations site-wide; `wpdev elementor:semantic <site> <post_id> --headings` audits this specific post's heading hierarchy. Missing h1, h2-skip, or `<section>` without heading → `[G-C]`. Layout-only violations → `[G-I]`.
- **Widget rarity / migration.** `wpdev elementor:widgets <site>` shows usage counts. A widget on this post used `< 3` times site-wide on the same post type → `[G-I]` "consider replacing with a more common widget". `wpdev elementor:widgets <site> --migrate` surfaces legacy-widget pages — a hit on this post triggers a Pass 2/3 fork into the migration pipeline (`elementor:migrate:main`, `elementor:migrate:containers`, `elementor:migrate:loop-index`). See [`migrate.md`](migrate.md) for which migrate command applies to which legacy shape.
- **Unused fields.** `wpdev voxel:empty <site>` lists Voxel fields with no data. A blueprint-defined field that's empty on every post of the CPT → `[G-I]` "field is dead — remove from blueprint or backfill data".
- **CSS-token fallback drift probe** (see Silent-failure detection probes). Grep Stream A stored CSS + rendered `<style>` for `var(--ef-[^,)]+,\s*[^)]+)`. For each fallback, resolve the token's canonical value (`EF_Tokens::DEFAULTS`) and compare; mismatch → emit `suspected` (`sme_question: "is this var() fallback intentional, or drifted from the token source?"`). Bare `var(--ef-token)` with no fallback is correct — never flag. Token source unreachable → flag all fallbacks `suspected`, note "source-check skipped". Source: `docs/solutions/best-practices/css-token-fallback-anti-pattern-2026-04-30.md`.
- **Unicode corruption probe** (see Silent-failure detection probes). Grep `wpdev elementor:dump <site> --post <post_id>` output for `[a-zA-Z]u00[0-9a-f]{2}` outside legitimate contexts (CSS escapes, encoded URLs). Any hit → emit `suspected` (`sme_question: "is this literal u00xx corrupted unicode, or a legitimate CSS/URL escape?"`); confirmed hits are `[G-C]`. Fix in Pass 2 via `wpdev elementor:fix:unicode <site>` (site-wide; snapshot first per rule 6). Source: root `CLAUDE.md` §Encoding.

### 3B — Section tier `[S]` (parallel: one subagent per top-level wrapper)

Build the section list from Stream A — top-level children of the root wrapper. Dispatch one subagent per section, **all in a single message**.

Failure classes each section agent must check: **broken layouts** (intra-section), **broken dynamic loops** (section-level `_vx_loop`), **broken filters** (`_ef_loop_transform`), **broken visibility** (section-level rules). Widget-prop details are explicitly out of scope — defer to `[W]` agents.

**Section subagent brief:** copy-paste from [`briefs.md`](../references/audit/briefs.md) §Audit · Section subagent brief. Substitute the `<site>`, `<template_post_id>`, `<wrapper_id>`, `<_title or _cssid>` placeholders.

Section agents are most valuable when they redirect attention from misleading widget symptoms. A widget that "doesn't render" may be inside a section whose loop produces zero iterations — fixing widget bindings won't help.

### 3C — Widget tier `[W]` (parallel: one subagent per non-trivial widget OR per ≤4-widget cluster)

Build the widget id list from Stream A. **Cluster trivial widgets** (plain `ef-wrapper`s with no settings, repeated bare `ef-card`s) into batches of up to 4 per subagent — they share a brief and reduce subagent count without losing atomic scope. Non-trivial widgets (anything with loops, repeaters, complex props) get their own subagent. Dispatch all in a single message.

Failure classes each widget agent must check: **broken dynamic tags**, **broken dynamic loops** (widget-level), **broken filters** (widget-level), **broken visibility** (widget-level), schema correctness, empty rendered vs populated source, image envelope, console/network errors. **Run the relation-loop self-traversal probe** (see Silent-failure detection probes): inside any `_vx_loop` over `@post(<rel>)`, an inner `@post(<rel>.<field>)` re-traversing the *same* relation key is render-valid but resolves the wrong post — emit `suspected` with `sme_question: "is row index N intentionally resolving the looped relation, or should this be @post(<field>) on the looped post?"`. Source: `docs/solutions/runtime-errors/voxel-relation-loop-self-traversal-2026-05-02.md`.

**Widget subagent brief:** copy-paste from [`briefs.md`](../references/audit/briefs.md) §Audit · Widget subagent brief. Substitute the `<site>`, `<template_post_id>`, `<widget_id>` (or cluster list), `<widgetType>`, `<cpt>`, `<example_id>` placeholders.

Within a single audit pass, `[S]` agents and `[W]` agents are dispatched **in the same message** — the orchestrator does not wait for section reports before fanning out widgets, since their scopes are disjoint by construction. When opted into Workflow, this combined tier walk is the `[S]`/`[W]` `pipeline(...)` over `voxel-builder:voxel-page-auditor` from §Workflow-tool orchestration, with each `agent()` returning a schema-validated FINDINGS array (one section or one widget/cluster per call); the orchestrator reads the structured findings and applies the Phase-4 confidence gate itself. Inline single-message dispatch is the fallback. Section agents may flag a widget id for follow-up (e.g. "this widget belongs in a different section"), but they don't read its props.

### Common widget-tier failure modes (memorise the signatures)

| Symptom | Root cause | Tier of the real fix |
|---|---|---|
| Visible `@post(...)` text in DOM | Missing `@tags()` wrapper | Widget |
| Image `<img>` empty src | Wrong image envelope shape | Widget |
| Widget with `_vx_loop` renders zero items | Loop source wrong OR visibility filter excludes everything | Widget OR Section |
| `_vx_loop` rows all read the same wrong value (or some drop empty) | Relation-loop self-traversal: inner `@post(<rel>.<field>)` re-traverses the looped relation | Widget (relation-loop probe) |
| Section appears empty | Section's wrapper-level `_vx_loop` filters everything | Section |
| Required surface (h1, contact) missing entirely | Page didn't allocate a section for it | Global |
| `elementor-post-<id>.css` 404 | Editor save not run | Global (resolves on next save) |

## Phase 4 — Report (by tier × severity)

Output one markdown report. Group by tier, then severity within tier. Every finding carries: **id**, **tier tag**, **widget path or section anchor**, **prop / context**, **evidence** (file/line refs), **suggested fix** (one-liner or pipeline reference), and **confidence**. Only `confirmed` findings appear in the tier tables; `suspected` findings collect in the `## Suspected (needs verification)` section regardless of tier, each with its mandatory `sme_question`.

```markdown
# Audit: <site> post <id> at <URL> (iteration <N>)

## Global [G]
### Critical
- [G-C1] <summary>
  - Evidence: <file>:<line>
  - Fix: <command or build-pipeline reference>
### Improvement
- [G-I1] ...
### Cosmetic
- [G-K1] revisions count <n>; offer prune
  - Fix: `wpdev elementor:revisions:prune <site> --post <id>`

## Section [S]
### Critical
- [S-C1] section "<wrapper.title or id>" — <summary>
  - Evidence: ...
  - Fix: ...
### Improvement
- [S-I1] ...
### Cosmetic
- [S-K1] ...

## Widget [W]
### Critical
- [W-C1] <widget_id>.<prop> — <summary>
  - Evidence: <file>:<line>
  - Fix: <one-liner>
### Improvement
- [W-I1] ...
### Cosmetic
- [W-K1] ...

## Suspected (needs verification)
Findings the agent could not cross-confirm, plus every uncalibrated detection-probe
hit. Each keeps its tier+severity id and MUST carry an `sme_question`. These are not
in the tables above — resolve them with the user (or by verifying) before fixing.
- [W-C7] <widget_id>.<prop> — <summary> (detection probe: relation-loop self-traversal)
  - Evidence: <file>:<line>
  - SME-question: is row index N intentionally resolving the looped relation, or should this be @post(<field>)?
  - Fix (if confirmed): <one-liner>
- [G-C3] css-token fallback drift — `var(--ef-color-primary, #e6f1f1)`
  - Evidence: <file>:<line>
  - SME-question: is this fallback intentional, or drifted from the token source (#F2F7F7)?

## Underused data
- <field_key> — populated on <X>/<Y> sampled posts, never referenced. Suggested binding: <surface>.

## Notes
- <free-form context>
```

If a finding can't be substantiated by a stream, drop it — speculation produces noise.

## Phase 5 — Fix UP, then loop

Audit is read-only. Fix runs in **three tier-passes**, smallest scope first, with re-audit between passes. The user approves before each pass.

### Pre-fix once

1. Confirm scope with the user (which findings to fix; which tiers in scope; re-run the loop whenever a fix tier materially changes the plan, stop when it converges, and surface the residual to the operator if it won't converge).
2. `wpdev elementor:revisions:prune <site> --post <id> --dry` → offer pruning (rule 6).
3. Capture rollback target: save `/tmp/before-<id>.json` from `wp_postmeta._elementor_data` (the canonical nested form, not the flat dump).
4. **Author the Behavior Contract + DOM-text baseline once per approved fix boundary** (the set of widgets one fix touches). Per [`behavior-contract.md`](../references/verification/behavior-contract.md): the command-host writes the triple (Behavior Contract / Allowed Structural Delta / Forbidden Semantic Delta) and captures the DOM-text baseline at `/tmp/baseline-<post_id>-<widget_id>.txt` BEFORE dispatching the fixer — author (command-host) ≠ repairer (fixer subagent) ≠ reviewer (the re-audit, a structurally separate read-only `voxel-page-auditor` run). If baseline capture fails, the fix is NOT dispatched — flag the finding "unverifiable — baseline capture failed" and surface to the user.

### Pass 1 — Widget-tier fixes `[W]` (parallel atomic mutations)

Smallest scope. Each fix is a point mutation on one widget's settings — atomic by construction, so the whole approved set can land in **one parallel dispatch**.

Procedure:
1. Group findings by widget id. One widget = one fix bundle, regardless of how many findings touch it (a widget with 3 findings → 1 subagent applying all 3).
2. Decide per-widget dispatch:
   - **Inline** (main agent, no subagent): point mutations like rename a prop, fix `@tags()` wrapper, swap image envelope shape, change a string value. These are 1–3 lines of edit; subagent overhead isn't worth it.
   - **Subagent** (dispatch, in parallel with all other widget subagents in the same message): non-trivial widget rebuilds — full prop tree replaced, repeater shape changed, loop binding flipped between `@site(loop_X)` and `@post(<relation>)`, schema-introspection-driven prop construction. Each subagent receives the current widget JSON + the findings to address + the canonical pattern reference (e.g. another template that uses the target shape). When opted into Workflow, this fan-out is `parallel(rows.map(r => () => agent(fixBrief(r), {agentType:'voxel-builder:voxel-elementor-fixer', schema: NODE})))` (see §Workflow-tool orchestration), each subagent returning its mutated widget-JSON node; the orchestrator assembles the returns and owns the import. Inline single-message dispatch is the fallback.
3. **Pass-1 fix brief:** copy-paste from [`briefs.md`](../references/audit/briefs.md) §Fix · Pass-1 widget-mutation subagent brief. Substitute the `<site>`, `<template_post_id>`, `<id>`, `<widgetType>`, findings list, and (optional) canonical-pattern reference.

4. The orchestrator collects all returned widget JSONs (and applies inline mutations directly), writes the combined `_elementor_data` via `wpdev elementor:import <site> <template_post_id> /tmp/built-<id>.json --save`, then lints. This assemble-and-import step is orchestrator-owned — it stays OUTSIDE the Workflow, between the fix fan-out and the re-audit fan-out.
5. **Re-audit** before Pass 2: re-run Streams A + D (the streams the fix mutated). Dispatch the `[W]` widget agents again **only on widgets that changed** plus their direct DOM neighbours (under Workflow, `resumeFromRunId` returns cached results for the unchanged legs, so only the mutated widgets re-execute). Diff findings against the previous report — including the DOM-text baseline diff per [`behavior-contract.md`](../references/verification/behavior-contract.md) §The falsifier; a Forbidden Semantic Delta violation rolls back to `/tmp/before-<id>.json`. New `[W]` findings appearing → fold into Pass 1 and re-dispatch only the affected widget subagents. Zero new `[W]` Critical findings → advance.

### Pass 2 — Layout / section-tier fixes `[S]` (parallel per independent section)

After widgets are clean, layout problems are unambiguous. Group `[S]` findings by section id; sections without dependencies on each other can be mutated **in parallel**, each by its own subagent. Sections that share a parent and conflict (e.g. both want to consume the same wrapper id) serialise within Pass 2.

Common Pass-2 actions:
- Move a widget out of a redundant wrapper.
- Replace two static heading cards with one loop card over a repeater field.
- Insert a missing EF widget/wrapper the section needs (e.g. add an `ef-wrapper` loop/template section for `@post(<relation>)`; do not add a Voxel `ts-post-feed`).
- Consolidate sibling wrappers.
- Rebind a section-level `_vx_loop`.

**Add-or-restructure → page-planning §2 entry (mandatory per rule 8).** Any Pass-2 action that ADDS a new section, RESTRUCTURES the section order/composition, or inserts a new widget shape the plan didn't anticipate is a non-trivial build — it MUST enter [`page-planning.md`](page-planning.md) §2a–§2g (Field Inventory → SSOT Read → Archetype Selection → Section Blueprints → adversarial review → reconciliation → computed §2g gate) scoped to just the new/restructured section. Dispatch the relevant adversarial reviewers, one concern each, in parallel; default to the full panel (coverage, density, hierarchy, data-wiring, pattern-reuse, relations, ssot-integrity, + migration-preservation when migrating), narrowing it only with a stated reason. When opted into Workflow, the §2e panel is `parallel(criteria.map(c => () => agent(reviewerBrief(c), {agentType:'voxel-builder:voxel-plan-reviewer', schema: FINDINGS})))` and any new widget JSON the section requires fans out as `parallel(rows.map(r => () => agent(builderBrief(r), {agentType:'voxel-builder:voxel-widget-builder', schema: NODE})))` (see §Workflow-tool orchestration). **The §2f reconciliation and the computed §2g gate stay OUTSIDE the Workflow** — the orchestrator reads the structured review findings, reconciles them (or writes an explicit `override:`), and clears the gate between the review fan-out and the widget fan-out. Inline single-message dispatch is the fallback. In-place point mutations (move, consolidate, rebind, replace static-with-loop where the binding is already in the inventory) DO NOT re-enter §2. Use the build-pipeline assemble pattern (the orchestrator owns tree shape and dispatches subagents for any new widget JSON the section requires). Write, lint, then **re-audit**: full pass on Streams A + D plus a fresh Stream B if data dependencies shifted. Re-dispatch `[W]` agents on widgets that the section change moved or replaced. New `[W]` findings on those widgets fold into Pass 2 immediately (don't bounce back to Pass 1; treat them as part of this layout change).

### Pass 3 — Page / global-tier fixes `[G]`

Last and largest. Common Pass-3 actions:

- Add an entirely new top-level section the page was missing.
- Restructure root container hierarchy.
- Change role assignment via `wpdev voxel:assign`.
- Migrate legacy `_voxel_loop` keys to `_vx_loop` site-wide on this template (and fork into [`migrate.md`](migrate.md) when legacy V3 widgets are involved — use `elementor:migrate:main` / `:containers` / `:loop-index`).

**Add-or-restructure → page-planning §2 entry (mandatory per rule 8).** Every Pass-3 action that adds a top-level section, restructures the root container hierarchy, or changes the role assignment is BY DEFINITION non-trivial — it MUST enter [`page-planning.md`](page-planning.md) §2a–§2g — dispatch the relevant adversarial reviewers, one concern each, in parallel; default to the full panel (coverage, density, hierarchy, data-wiring, pattern-reuse, relations, ssot-integrity, + migration-preservation when forking from migration), narrowing it only with a stated reason — BEFORE any widget fan-out. The §2e panel and the subsequent widget fan-out use the same Workflow expressions and the same orchestrator-owned §2f/§2g gate as Pass 2 (see §Workflow-tool orchestration); inline single-message dispatch is the fallback. Pass 3 changes are the riskiest — verify with the user before each one. After Pass 3, **final convergence audit**: full pass on all five streams. A clean report (zero Critical at any tier) ends the loop.

### Convergence rules

- **Soft termination:** zero `Critical` findings at any tier → done.
- **Convergence, not a cap:** re-run the full Pass-1→Pass-2→Pass-3 loop whenever a fix tier has materially changed the plan; stop when findings converge. If it won't converge — scope drift or a contested design decision that needs the user — surface the residual findings as a follow-up plan rather than continuing.
- **Iteration receipt.** Each iteration produces its own audit report tagged `iteration <N>`. Keep all reports — diffing them shows which findings auto-resolved vs needed direct action.

### Editor save + cache purge (always at end)

After the final fix iteration:

1. Open the template in the Elementor editor and click "Update" (regenerates `elementor-post-<id>.css`).
2. `wpdev rebuild <site> --only purge` (LiteSpeed + Elementor CSS).
3. Final browser verification per [`build.md`](build.md) §Phase 6 — parallel subagent per sample post URL. When opted into Workflow, this is `parallel(urls.map(u => () => agent(verifyBrief(u), {schema: VERDICT})))` (see §Workflow-tool orchestration), each subagent returning a schema-validated pass/fail verdict; the verify→repair loop is a `while` on the convergence guard, and **that convergence decision stays OUTSIDE the Workflow** — the orchestrator reads the verdicts and decides whether to launch a repair fan-out or stop. Inline single-message dispatch is the fallback. **Screenshot mandatory** (text-grep can't see layout collapse); pre-flight `tail -30 sites/<site>/wp-content/debug.log` to surface unrelated fatals before declaring failure.

## Multi-URL audits

When the same template renders many posts (CPT card on a busy feed), audit on **a representative sample of real post URLs picked across the data distribution (one is never enough)**: max field population, sparse, mid. Findings that only appear on the sparse post often reveal missing visibility rules or fallback content gaps. Dispatch the Stream D run **once per URL in parallel** — the same `parallel(urls.map(...))` Stream D pool from §Workflow-tool orchestration when opted in, inline single-message dispatch otherwise; Streams A, B, C, E run once.

In iterative loops, re-audit Stream D on the **same URL set** after each fix pass, not on new URLs. Pivoting URLs mid-loop hides regressions.

## Mistake guards

- Never fix from an audit report without a separate approved fix pass.
- Suspected findings stay out of confirmed tables until verified.
- Browser Stream D must include screenshot reading; DOM text alone is not layout evidence.

## Anti-patterns

- **Don't audit without reading lint first.** Most schema findings are answered there; running browser checks before lint wastes time.
- **Don't audit bottom-up or fix top-down.** Inverting the hierarchy makes both phases harder: bottom-up audit drowns in widget noise from sections that should be removed; top-down fix risks tearing out structure whose widget-level reasons aren't yet visible.
- **Don't dispatch tier subagents sequentially.** All `[S]` agents go in one message; all `[W]` agents go in one message; ideally `[S]` and `[W]` are dispatched together since their scopes are disjoint. Sequential dispatch erases the wall-time benefit and is the single most common mistake at this layer.
- **Don't bundle multi-scope findings in one subagent report.** Atomic scope is the contract. One widget id = one subagent's reportable surface. A widget agent that says "and also this section is wrong" is leaking scope — drop the cross-scope observation or escalate it to the orchestrator without flagging it as the agent's own finding.
- **Don't pivot URLs mid-loop.** Re-audit Stream D on the **same URL set** after each fix pass, not on new URLs. Pivoting URLs hides regressions on previously-passing posts.
- **Don't skip naming failure classes in subagent briefs.** Agents that aren't told which of the five classes to check produce drifty, inconsistent reports. Always enumerate.
- **Don't skip re-audit between fix passes.** Emergent findings after Pass 1 / Pass 2 are the loop's whole purpose — without re-audit, the loop collapses to a single pass.
- **Don't loop past convergence.** Re-run only while a fix tier has materially changed the plan; once findings converge, stop. If it won't converge, file a follow-up plan rather than thrashing.
- **Don't categorise tag leakage as "warning".** Visible `@post(...)` text is always Critical.
- **Don't skip Stream B on CPT templates.** Without `voxel:data`, Improvement findings around underused fields are guesses.
- **Don't fix during audit.** Audit is read-only. Mixing audit and fix phases makes it impossible to tell which finding the fix addressed.
- **Don't treat empty values as bugs without checking source data.** A blank byline on a post with no byline field set is correct behaviour, not a template defect.
