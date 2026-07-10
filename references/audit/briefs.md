# Audit Subagent Brief Templates

Copy-pasteable Task-tool briefs for the parallel-dispatch points in [`audit.md`](../../workflows/audit.md), [`parallel-dispatch.md`](../core/parallel-dispatch.md), and [`page-planning.md`](../../workflows/page-planning.md). Two audit-side briefs (Section, Widget), one fix-side brief (Pass-1 widget mutation), and one plan-review brief stub (Phase 2e per-criterion). Keep prose minimal — these are templates, not narrative.

Failure-class taxonomy is the six classes in [`parallel-dispatch.md`](../core/parallel-dispatch.md) §Failure-class taxonomy — 5 widget/section/page-tier classes (broken dynamic tags, broken dynamic loops, broken filters, broken visibility, broken layouts) + 1 plan-tier class (broken Plan Document). Briefs below name explicitly which subset of the six their criterion/scope checks; out-of-scope classes are deferred to other agents.

## Severity codes (used in all briefs and reports)

- **C** — Critical (broken render, schema-invalid, blocks the page from working)
- **I** — Improvement (data underused, structure suboptimal, opportunity)
- **K** — Cosmetic (housekeeping; mnemonic: house**K**eeping)

`<n>` = a positive integer, allocated per scope (each subagent starts at 1: `[W-C1]`, `[W-C2]`, `[W-I1]`, …). The orchestrator may renumber on assembly.

## Confidence codes (every finding carries one)

- **confirmed** — the agent verified the symptom by a concrete method: a tool flagged it AND the agent confirmed by reading the source / DOM / data. Flows into the standard `[G]/[S]/[W]` tables.
- **suspected** — a pattern seen but not cross-confirmed, OR a Silent-failure detection probe ([`audit.md`](../../workflows/audit.md)) that hasn't been calibrated. Routes to the Phase 4 `## Suspected (needs verification)` bucket and MUST carry a one-line `sme_question` whose answer would resolve the uncertainty. A `suspected` finding with no `sme_question` is rejected back to the subagent (see [`voxel-page-auditor.md`](../subagents/voxel-page-auditor.md) step 6).

No numeric anchors, no promotion, no fingerprint — two values, and the question is the gate. In this HITL workflow the human approving each fix is the real confidence check; `suspected` simply says "look here first".

## Audit · Read-only investigation brief (use when the user is in DECIDE mode, not BUILD mode)

Use this brief when the user has asked for investigation, research, or "what's going on with X" — explicitly NOT a fix, NOT a patch proposal, and NOT widget-JSON authoring. The agent reads code/data, names what it found, and stops. Stops short even of recommending a specific edit unless asked.

Trigger phrases that select this mode: "investigate and suggest only", "I just want to understand X", "do not patch", "explain what's happening here", "audit and report".

```
Investigate ONE scope on <site> post <template_post_id>. READ-ONLY mode.

Scope: <single widget id | single section id | single failure-class question>
Question: <free-form, e.g. "why does the hero section render empty on this post"
           or "what determines the loop placement here">

Read these gathered files (already on disk):
- /tmp/audit-data-<id>.json   — dump
- /tmp/audit-html-<id>.html   — DOM
- /tmp/audit-tree-<id>.txt    — tree summary
- /tmp/audit-lint-<id>.txt    — lint output

You MAY:
  - Read source files in `sites/<site>/wp-content/plugins/elementor-framework/`
    or `sites/<site>/wp-content/themes/voxel/` to ground claims
  - Run `wpdev elementor:schema <site> <widget> --prop <key>` for shape lookups
  - Run `wpdev voxel:fields` / `wpdev voxel:data` for field-resolution checks

You MUST NOT:
  - Propose a JSON patch
  - Write any file (no /tmp/*.php, no /tmp/built-*.json)
  - Run `wpdev elementor:import`, `wp eval`, `wp eval-file`, or any DB write
  - Recommend a specific edit unless the question explicitly asked for one

Return:
  - Direct answer to the question (1-3 sentences)
  - Evidence: file paths + line numbers, jq paths, or schema-output excerpts
  - Open questions / things that would need a human decision

Cap report at 250 words. No code blocks larger than 8 lines.
```

When N parallel read-only investigators are dispatched on the same `_elementor_data`, they don't conflict — none write. This is the ONLY safe mode for high-fan-out parallel dispatch on a single template.

## Audit · Section subagent brief (Phase 3B)

Dispatch one per top-level wrapper. Send all `[S]` agents in a single message together with all `[W]` agents — scopes are disjoint by construction.

```
Audit ONE section of <site> post <template_post_id>. Atomic scope: report
findings for THIS section ONLY — never adjacent sections, never individual
widget props (those belong to the widget tier).

Section id:        <wrapper_id>
Section title:     <_title or _cssid value, if present>
Section subtree:   jq path → [.[] | .. | objects | select(.id=="<wrapper_id>")]
Section DOM anchor: `[data-id="<wrapper_id>"]` OR `.s-<cssid>` if `_cssid` set

Read these gathered files (already on disk):
- /tmp/audit-data-<id>.json   — dump (extract section subtree)
- /tmp/audit-html-<id>.html   — DOM (extract anchor region)
- /tmp/audit-tree-<id>.txt    — tree summary

Failure classes to check (every applicable one):
  1. Broken layouts
       - empty / orphan wrapper (no widget children)
       - sibling redundancy with another section that has identical settings
       - depth > 4 inside this section
       - `html_tag` mismatch with semantic role (e.g. `nav` for a content body)
  2. Broken dynamic loops at SECTION level
       - `_vx_loop` / `_voxel_loop` on this wrapper produces zero iterations
         despite source data on Stream B
       - loop scope-path inside heading rows refers to wrong relation/repeater
       - relation-loop self-traversal: a section-level `_vx_loop` over
         `@post(<rel>)` with inner `@post(<rel>.<field>)` reusing the same
         relation key (see Widget brief probe) → emit `suspected`
  3. Broken filters at SECTION level
       - `_ef_loop_transform.filter_*` excludes everything
       - filter operator wrong for the field shape (array post-relation, etc.)
  4. Broken visibility at SECTION level
       - `_vx_visibility` / `_voxel_visibility_rules` rule on this wrapper
         evaluates false when source data says it should show
       - legacy key on post-relation `.id` paths

Out of scope (DO NOT report):
  - any widget-prop binding inside this section
  - global tree shape (root wrappers, role assignment)
  - schema lint findings (those go to widget tier)

Return concise findings, one per line:
  [S-C<n>] <failure-class> — <one-line summary>
    Evidence: <file:line OR jq path>
    Fix: <one-line scope, e.g. "remove wrapper", "rebind _vx_loop to @post(<relation>)">
    Confidence: confirmed | suspected
    SME-question: <REQUIRED when suspected — one question whose answer resolves
                   the uncertainty; OMIT this line when confirmed>

Severity letter is C / I / K. Number `<n>` starts at 1 per agent.
Mark a finding `suspected` whenever you did not cross-confirm it (pattern only,
or an uncalibrated detection probe) — and then the SME-question is mandatory.
Cap the report at 250 words.
```

## Audit · Widget subagent brief (Phase 3C)

Dispatch one per non-trivial widget; cluster up to 4 trivial widgets per agent. All in a single message.

```
Audit ONE widget (or cluster of trivial widgets) of <site> post <template_post_id>.
Atomic scope: findings for THIS widget ONLY, never the section it lives in.

Widget id(s):     <id> (or [id1, id2, id3, id4] for a cluster)
Widget type(s):   <widgetType>
DOM anchor:       `[data-id="<widget_id>"]` OR class derived from `_cssid`

Read:
- /tmp/audit-data-<id>.json     — extract this widget's settings only
- /tmp/audit-html-<id>.html     — DOM region within the widget's anchor
- /tmp/audit-lint-<id>.txt      — only lines naming this widget id
- /tmp/audit-fields-<cpt>.txt   — voxel:fields output (for dynamic-tag checks)
- /tmp/audit-data-<example_id>.txt — voxel:data output (for empty-vs-populated checks)

Run schema only if a finding requires the canonical envelope:
  wpdev elementor:schema <site> <widgetType> --prop <key>

Failure classes to check (every applicable one):
  1. Broken dynamic tags
     a. literal `@(post|author|site|tags)\(...\)` text leaks in DOM region
     b. `@post(...)` / `@author(...)` / `@site(...)` literal in a string prop
        without `@tags()...@endtags()` wrapper
     c. tag references a non-existent field key (cross-check voxel:fields)
  2. Broken dynamic loops (widget-level)
     - `_voxel_loop` / `_vx_loop` on this widget produces zero iterations
       despite source having data on Stream B
     - heading-row paths inside the loop reference wrong scope (`@site(loop_X)`
       vs `@post(<relation>)` shape mismatch)
     - RELATION-LOOP SELF-TRAVERSAL PROBE: when `_vx_loop.tag` is
       `@post(<rel>)`, scan inner row tags for `@post(<rel>.<field>)` reusing
       the SAME relation key — render-valid but resolves the wrong post (rows
       repeat one value or drop empty). Emit `suspected`, sme_question:
       "is row index N intentionally resolving the looped relation, or should
       this be @post(<field>) on the looped post?". Fix: drop the relation
       prefix → `@post(<field>)`.
       Source and current repair contract: [`voxel-loop-authoring.md`](../voxel/voxel-loop-authoring.md).
  3. Broken filters (widget-level)
     - `_ef_loop_transform.filter_*` excludes everything
     - visibility rule `compare` operator wrong for field shape
  4. Broken visibility (widget-level)
     - rule evaluates false when source data says widget should show
  5. Schema correctness
     - lint flags this widget id with unknown-prop / type-mismatch /
       enum-violation / v3-shape
  6. Empty rendered vs populated source
     - per-prop: `@post(<key>)` referenced; source non-empty in voxel:data;
       DOM region shows empty/missing → Critical
     - source empty + DOM empty → skip (not a template bug)
  7. Image envelope shape
     - image-typed prop missing `{src, size}` shape OR wrong $$type
     - `<img>` in DOM region with empty src or 4xx network status
  8. Console / network errors
     - error text mentions this widget id or class
     - network 4xx for an asset URL inside this widget's settings

Out of scope (DO NOT report):
  - section-level loop/visibility/layout
  - tree shape / role assignment
  - findings about adjacent widgets

Return concise findings, one per line:
  [W-C<n>] <failure-class> — <widget_id>.<prop> — <one-line summary>
    Evidence: <file:line>
    Fix: <one-line point mutation>
    Confidence: confirmed | suspected
    SME-question: <REQUIRED when suspected — one question whose answer resolves
                   the uncertainty; OMIT this line when confirmed>

Severity letter is C / I / K. Number `<n>` starts at 1 per agent.
Every Silent-failure detection probe hit is `suspected` until calibrated, so it
always carries its probe-specific SME-question. Mark any non-probe finding
`suspected` too whenever you did not cross-confirm it.
Cap the report at 300 words (350 for clusters).
```

## Fix · Pass-1 widget-mutation subagent brief (Phase 5)

Dispatched per widget that has approved `[W]` findings the main agent isn't applying inline. Mirrors the build pipeline §Phase 3 fan-out shape — main agent assembles all returned widget JSONs into one `wpdev elementor:import` write.

Pass 1 is point-mutation only. Any Pass 2/3 fix that ADDS a new section, RESTRUCTURES section order/composition, or inserts a new widget shape the original plan didn't anticipate is non-trivial per Rule 8 — the fixer MUST enter [`page-planning.md`](../../workflows/page-planning.md) §2a–§2g (Field Inventory → SSOT Read → Archetype Selection → Section Blueprints → adversarial review → reconciliation → operator `APPROVED`) scoped to just the new/restructured section before any new widget fan-out. See [`audit.md`](../../workflows/audit.md) §Pass 2 / Pass 3 for the add-or-restructure → page-planning §2 trigger.

```
Mutate ONE widget on <site> post <template_post_id>. Atomic scope.

Widget id:    <id>
Widget type:  <widgetType>
Findings to address:
  - [W-C1] <one-line>  → fix: <one-line mutation>
  - [W-I2] <one-line>  → fix: <one-line mutation>

Canonical pattern reference (if needed): <other_post_id> / <jq path>
Schema introspection (run only if needed):
  wpdev elementor:schema <site> <widgetType> --prop <key>

Return ONLY the mutated widget JSON object. No prose, no parent container.
Preserve the widget id and any settings the findings did not touch.
```

## Plan-review · Per-criterion subagent brief (page-planning §2e)

Dispatched once per in-scope plan-phase criterion in a single message during [`page-planning.md`](../../workflows/page-planning.md) §2e — the orchestrator selects the applicable set from [`criteria.md`](../core/criteria.md) (the full panel by default, plus `migration-preservation` when migrating). The per-criterion protocols (full check list per criterion) ship in the agent definition at [`voxel-plan-reviewer.md`](../subagents/voxel-plan-reviewer.md) §Per-criterion protocols — this brief is the orchestrator-side wrapper that selects a criterion and passes the Plan Document. Read-only; the agent's tool list excludes `Write`.

```
Review the Plan Document at <plan_path> as ONE criterion. Atomic scope to that
criterion's remit ONLY — never cross-criterion report.

criterion:          <coverage | density | hierarchy | data-wiring | pattern-reuse |
                   relations | ssot-integrity | migration-preservation>
plan_path:        /tmp/plan-<post_id>.md
site:             <site>
post_id:          <post_id>
cpt_key:          <cpt_key>
example_posts:    [<id_A>, <id_B>, <id_C>]
mode:             build | migration
production_urls:  [<url1>, <url2>, <url3>]   # REQUIRED only for migration-preservation

Per-criterion protocol: see ../../references/subagents/voxel-plan-reviewer.md §Per-criterion protocols.

Failure class checked: broken Plan Document (the sixth class in
parallel-dispatch.md §Failure-class taxonomy).

Return: structured findings array per voxel-plan-reviewer.md §Return format.
No patches. No Plan Document edits. Read-only.
```

The orchestrator merges per-criterion returns into `/tmp/plan-review-<post_id>.md` and writes reconciliation outcomes (`resolved:` / `override: <concrete reason>` / `deferred:`) under each finding in the Plan Document's §2f. See [`page-planning.md`](../../workflows/page-planning.md) §2f.

## When to use which brief

| Phase | Brief | Dispatched per |
|---|---|---|
| Decide-mode | Read-only investigation | One scope (widget / section / question) — when user is investigating only |
| Plan §2e | Plan-review per-criterion | One criterion (7 in build, 8 in migration) per dispatch; all in a single message |
| 3B audit | Section subagent | One top-level wrapper |
| 3C audit | Widget subagent | One non-trivial widget OR ≤4-widget cluster |
| 5 fix Pass 1 | Widget-mutation | One widget with approved `[W]` findings (only when subagent dispatch is warranted; point mutations stay inline in the main agent) |

Pass 2 (`[S]` fix) and Pass 3 (`[G]` fix) typically do not use a single canonical brief — section / page restructures vary too much. Compose a one-off brief from the build pipeline ([`build.md`](../../workflows/build.md) §Phase 3) when the change is large enough to need a subagent. Any Pass 2/3 add-or-restructure also re-enters [`page-planning.md`](../../workflows/page-planning.md) §2 before fan-out (Rule 8).
