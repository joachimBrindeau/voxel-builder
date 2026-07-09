# Elementor Build Pipeline

How to construct or modify `_elementor_data` JSON correctly. Schema-driven, orchestrator-led, parallel-subagent dispatch, no hardcoded widget shapes.

The main agent coordinates this pipeline; it does not act as the page builder. It
collects shared context, produces/updates the Plan Document, dispatches named
subagents for section planning, adversarial review, widget construction, and
browser verification, validates returns, assembles `_elementor_data`, writes once,
and owns every judgment gate between fan-outs.

## Entry criteria

1. Target site, post/template id, and render URL are known.
2. `wpdev elementor:codegen --check` passes or the live schema fallback is explicitly documented.
3. Page-planning §2 has approved section blueprints for non-trivial builds.
4. Existing `_elementor_data` is exported before mutation when modifying live content.

## Exit criteria

1. Imported `_elementor_data` validates with `wpdev elementor:lint <site> --post <id>` at 0 findings.
2. Per-post CSS is regenerated and caches purged.
3. Browser verification passes screenshot, computed-style, console/error, and content checks.
4. No Behavior Contract Forbidden Semantic Delta exists when modifying existing data.

## When to use this pipeline

- Building a single / archive / page / popup template body programmatically
- Adding widgets to an existing post's `_elementor_data`
- Migrating a page's structure (replacing widgets, restructuring containers)
- Adding feed/list/repeated surfaces with Elementor Framework (`ef-*`) widgets and `ef-wrapper` template/loop wrappers; do not add Voxel `ts-*` widgets
- Verifying a recently-modified template renders correctly across multiple example posts (browser smoke-test)

For preview cards (the `card` role), prefer `wpdev voxel:cards` over this pipeline — it's purpose-built and idempotent.

## Phase 0 — Drift preflight, snapshot, prune to latest, decide rebuild-vs-revise

**Drift preflight (#16 — hard precondition).** The build refuses to start unless `wpdev elementor:codegen --check` passes — a stale schema SSOT (artifact behind the EF widget registration at HEAD) is a halt, not a warning. Phase 1 runs `wpdev elementor:codegen` unconditionally first (rule 1), which makes `--check` pass by construction; if it cannot (uncommitted EF schema churn), halt and surface — never plan against a schema that does not match the site.

Before any modification, **snapshot once and prune ALL revisions** so the build operates on the latest `_elementor_data` only. Each Elementor save clones the full `_elementor_data` into a revision row; the build never targets a historical one.

```bash
# Single template
wpdev elementor:revisions:prune <site> --post <id> --dry      # count only
wpdev elementor:revisions:prune <site> --post <id>            # snapshot + delete

# Bulk (all Elementor posts on the site)
wpdev elementor:revisions:prune <site> --dry                  # count only
wpdev elementor:revisions:prune <site>                        # snapshot + delete
```

The command writes a snapshot of each parent post's current `_elementor_data` before deleting any revisions, so the operation is reversible via `wpdev elementor:revisions:restore`.

**Prune rule (unconditional):** run `wpdev elementor:revisions:prune <site> --post <id>` (no `--dry`, no asking) — it snapshots the current `_elementor_data` then deletes every revision. The snapshot is the rollback point (`wpdev elementor:revisions:restore`).

**Build-strategy gate (decide once, here) — template-match FIRST, custom build as fallback.** Decide the run's strategy in this order and state ONE call — `adapt-template | rebuild-greenfield | revise` — in the Plan Document; the call decides whether Phase 5 imports a spliced-then-patched tree, imports a fresh full tree, or mutates the existing one.

1. **PREFERRED — adapt a saved section template.** Before judging rebuild-vs-revise, read [`../templates/index.md`](../templates/index.md) and check whether a saved template in [`../templates/sections/`](../templates/sections/) matches the section(s) being built — match on `type` (the section archetype: hero, features, cta, …) and `tags` overlapping the CPT context (e.g. a hero — the seeded [`hero-services-search`](../templates/sections/hero-services-search/) / [`hero-city-geo`](../templates/sections/hero-city-geo/)). **When a template matches, PREFER adapting it** — this is the default path for any section that has a matching template. Splice its `template.json` into the build tree as the starting subtree, then have the build agent patch the deltas — fill the `Lorem ipsum` placeholders with the real per-post content and adjust structural props for this context (regenerate node ids to avoid collisions on splice). The spliced tree then runs the normal `elementor:import --save` gate (Phase 5) exactly as any other build output would — no shortcut around lint/verify. **A template is a starting tree, never authoritative spec: preferred-when-matched is not a validation bypass. When the SSOT (`cli/src/generated/widget-schemas.json`) and a template disagree, the SSOT wins** (see [`../templates/README.md`](../templates/README.md) §SSOT wins) — treat the spliced `template.json` as Phase 4 input to be corrected against §2b, not as a finished section. Call this `adapt-template`.
2. **FALLBACK — custom build (rebuild-vs-revise).** Only when NO saved template matches the section does the run fall back to the binary: read the existing tree (`wpdev elementor:tree <site> <id>`) and judge its quality against what the CPT's data could support. **When the current data is worse than starting clean — a thin stub, broken structure, legacy V3 sludge, or so far from the target that surgical edits would cost more than a fresh build — treat the run as greenfield: discard the existing tree and build from the Plan Document** (`rebuild-greenfield`). Otherwise revise in place (`revise`).

**Run fingerprint + ledger (#8/#9 — idempotent re-entry + audit).** Compute a run fingerprint `sha1(cpt fields + widget-schemas.json sha + sample post ids + plan body)` and store it in post meta (`_vb_build_fingerprint`). On re-invocation an **unchanged fingerprint is a no-op** (already built — exit early). On change, re-plan only the delta. Append every run — fingerprint, sample ids, plan path, gate verdict, finding-bus path, write/rollback events — to an append-only ledger (`docs/audits/vb-ledger-<post_id>.jsonl`) keyed by fingerprint, so an unattended run is replayable and auditable after the fact.

This phase does NOT apply to `voxel:post-type-<key>:revisions` — those are Voxel admin-config snapshots stored in `wp_options`, not WP post revisions, and `wpdev elementor:revisions:prune` doesn't touch them. See [`template-resolution.md`](../references/voxel/template-resolution.md) §Revisions.

## Phase 1 — Gather context (parallel, orchestrator-owned)

Run before writing any JSON:

```bash
# Always — regenerate the schema SSOT first (unconditional; also syncs it into references/)
wpdev elementor:codegen
wpdev elementor:schema <site>                          # widget catalog + reserved keys

# When modifying an existing post
wpdev elementor:dump <site> all --post <id> --json     # full current data
wpdev elementor:tree <site> <id>                       # tree summary

# When the post is a Voxel CPT template — gather the MOST COMPLETE sample
wpdev voxel:fields  <site> <cpt_key>                   # valid @post(<key>) tags
wpdev voxel:sample  <site> <cpt_key>                   # export the most-complete posts (ranked by
                                                       #   filled fields + relations + repeaters) to a temp folder
wpdev voxel:data    <site> --id <example_post_id>      # rendered VALUES on a sampled post

# When a feed/list/loop is needed, read EF wrapper loop/template schemas.
# Do not add Voxel ts-* widgets for new builds.
wpdev elementor:schema <site> ef-wrapper --prop _vx_loop
wpdev elementor:schema <site> ef-wrapper --prop template_id
```

`voxel:fields` lists which `@post(<key>)` tags are valid. `voxel:sample` ranks real posts by completeness (filled fields + relations + repeaters, weighted) and writes the top candidates to a temp folder, so the sample is the *most complete* data the CPT has — never a random or single post. `voxel:data` shows what the tags render to on a sampled post — prevents picking dynamic tags that resolve to empty strings.

**EF-only widget rule.** New Elementor builds use only Elementor Framework widgets/elements (`ef-card`, `ef-wrapper`, `ef-form`, `ef-navbar`, `ef-toc`, `ef-cal`). Do not add or rebuild Voxel `ts-*` widgets (`ts-post-feed`, `ts-search-form`, `ts-print-template`, etc.). For feed/list/relation/repeated surfaces, compose an `ef-wrapper` with the canonical `_vx_loop` envelope and, where needed, a template/card child; wrappers in template+loop mode are sufficient and keep the page inside the EF schema SSOT.

**Existing Voxel widget exception (preservation only).** If modifying or migrating a template that already contains a Voxel `ts-*` node, preserve it verbatim unless the explicit task is to replace it with EF wrappers. Do not rebuild its settings and do not introduce a fresh `ts-*` node.

**Verify every post-ID an existing preserved `ts-*` node references actually exists (dead-reference guard).** `ts-post-feed` / `ts-template` settings carry post-ID references — `ts_card_template__<type>`, `ts_manual_card_template__<type>`, `ts_template_id`, `ts_manual_posts[].post_id`, `connect_map`, `ts_post_to_feed`. A node spliced verbatim from a legacy template can point at a card/template post that was since deleted — the feed then renders with no card (silent empty). Before accepting any preserved `ts-*` node,

```bash
# Use `wpdev wp <site> …` — cwd-independent. Never `cd sites/<site> && wp …`:
# the Bash tool persists cwd across calls, so a relative `cd sites/<site>` fails
# the moment a prior call already moved into that directory.
wpdev wp <site> post get <ref_id> --field=post_status --skip-plugins 2>/dev/null \
  || echo "MISSING: <ref_id>"   # MISSING / trash / draft → re-point at a live template before writing
```

Re-point any missing/trashed reference at a current template id (from `wpdev voxel:templates <site>`) before the node enters the tree. This is also a §2b SSOT obligation and a `voxel-widget-builder` brief step.

## Phase 2 — Plan the page (mandatory delegated sub-pipeline)

**Stale-plan guard (run FIRST).** A plan from a prior session may already sit at `/tmp/plan-<post_id>.md`. Do NOT blind-`Write` over it (that errors "File has not been read yet" and, worse, silently discards a gated/approved plan). Check and branch:

```bash
ls -la /tmp/plan-<post_id>.md 2>/dev/null && echo "EXISTS — read before deciding"
```

If it exists: `Read` it, then present the operator with three options — **continue** (it is already gated — `GATE: green (auto)` or operator-`APPROVED` → skip to Phase 3), **revise** (re-enter §2c–§2f with their notes), or **discard** (delete and start §2a fresh). Only after that choice do you proceed. Never infer; an existing gated plan is a prior decision, not noise to overwrite.

**This is the bulletproof planning sub-pipeline — it is NOT optional and NOT a quick prose sketch.** See [`page-planning.md`](page-planning.md) for the full Phase 2a–2g protocol. The historical "decide the widget tree top-down" one-sentence instruction produced thin templates (e.g. a data-rich CPT rendered as a near-empty tree — an `ef-wrapper > ef-card` stub with the CPT's fields and traversable relations all unsurfaced). The new sub-pipeline replaces it.

Summary of what Phase 2 now does (full detail in [`page-planning.md`](page-planning.md)):

- **§2a — Field Inventory.** Run `wpdev voxel:fields` + `wpdev voxel:data` on **a representative sample of real posts (one is never enough)**. Build the Field Inventory Table; classify every field `must` / `should` / `may` / `omit:<reason>` — `must` = reliably carries data across the sample and is user-facing; `should` = carries data on part of the sample and is user-facing; `may` = sometimes present and adds editorial signal (defended to the coverage reviewer, not a count rule); bind each to a target section.
- **§2b — SSOT Read.** Build the Widget Catalog from the committed SSOT (`cli/src/generated/widget-schemas.json`). The catalog is EF-only for new builds; `ts-*` widgets are preservation-only legacy nodes, never new build targets. Record every prop's `$$type` envelope shape, especially `ef-wrapper` loop/template props for repeated surfaces.
- **§2c — Archetype Selection.** Pick from the established catalog (hero / brief / specs-grid / detail-tabs / detail-accordion / sidebar-contact / sidebar-map / sidebar-schedule / relation-feed / faq-accordion / related-cpt-feed / cta-footer). Map every `must`-class field to ≥1 archetype.
- **§2d — Section Blueprint Composition.** Per-section table: widget, settings (with `$$type` envelopes from §2b), tag wrap, role, expected DOM, pre-resolved dynamic-tag values across the sample of real posts. The §2c→§2d layout-architect (one per selected section) + heading-curator (one per plan) fan-out is detailed in [`page-planning.md`](page-planning.md); **when opted into multi-agent orchestration**, express it as a Workflow `parallel([() => agent(curator, {agentType: 'voxel-builder:voxel-heading-curator', schema}), ...sections.map(s => () => agent(architect(s), {agentType: 'voxel-builder:voxel-layout-architect', schema}))])` step, inline single-message dispatch otherwise — the orchestrator splices the returned blocks into §2d either way. Canonical expression: [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Fan-out → Workflow expression map. **A section blueprint SHOULD prefer binding to a saved template** in [`../templates/sections/`](../templates/sections/) — the template-match lookup runs FIRST in §2c (matched via [`../templates/index.md`](../templates/index.md) on `type` + `tags`), and full widget-by-widget synthesis is the fallback only for sections with no matching template — record the bound template id in the blueprint row so Phase 4 splices its `template.json` and patches only the deltas. The bound tree stays subordinate to §2b: the SSOT wins on any disagreement ([`../templates/README.md`](../templates/README.md) §SSOT wins), so the template is a starting tree the blueprint still validates prop-by-prop, never an authoritative spec.
- **§2e — Adversarial review fan-out.** Dispatch the relevant adversarial reviewers, one concern each, via the `voxel-plan-reviewer` agent. **Preferred when opted into multi-agent orchestration:** express the fan-out as a Workflow `parallel(criteria.map(c => () => agent(reviewerBrief(c), {agentType: 'voxel-builder:voxel-plan-reviewer', schema: FINDINGS})))` step — each leg returns a schema-validated findings array, so §2f reconciliation reads structured returns instead of hand-normalizing free text. **Fallback (always valid):** send all reviewers in a single inline message. Either way the orchestrator — not the Workflow — owns the §2f reconciliation and §2g gate. See [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Fan-out → Workflow expression map for the canonical expression and the orphan caveat. Default to the full panel (`coverage` / `density` / `hierarchy` / `data-wiring` / `pattern-reuse` / `relations` / `ssot-integrity`, plus `migration-preservation` when migrating); narrow it only with a stated reason. The `migration-preservation` criterion is the migration-only one that the migration workflow (`workflows/migrate.md`) adds and is skipped in build mode. Atomic scope per criterion — each emits findings only within its remit.
- **§2f — Reconciliation.** Every Critical and Improvement finding receives an outcome line: `resolved:` (plan revised; diff cited), `override: <concrete reason>`, or `deferred:` (linked follow-up). Weak overrides block §2g approval. Re-run §2e whenever the plan has materially changed; stop when it converges; surface the residual to the operator if it won't converge.
- **§2g — Gate (autonomous by default).** The gate is computed: it goes green when `open_C == ∅` (every Critical criterion `pass`/valid-override) and every Improvement finding has an outcome. The orchestrator then writes `GATE: green (auto)` and proceeds — no human approval needed for a green gate. It escalates to the operator only when a Critical can't be auto-resolved or the caller set `--require-approval`; on escalation the operator writes `APPROVED` / `REVISE:` / `REJECT:`.

**Output of this phase:** the approved Plan Document at `/tmp/plan-<post_id>.md`. Phase 3 fan-out reads this document as the per-widget brief — every widget-builder receives its blueprint row(s) verbatim. No widget-builder ever fills gaps from memory; if a row is missing or ambiguous, the orchestrator returns to §2d, not to Phase 3.

**Hard rule.** No Phase 3 dispatch without a green §2g gate (`GATE: green (auto)` or operator-`APPROVED`). The [`rules.md`](../references/core/rules.md) (Eight rules) checklist enforces this at success-criteria time, but the gate is here.

**Greenfield exception.** Build mode skips the `migration-preservation` criterion. All other phases are identical between greenfield build and existing-data modification.

**Tree shape rules (subordinate to §2d):**
- A single `ef-card` at root: NO wrapping container. The `wpdev elementor:strip:wrappers` tool removes redundant wrapper containers around `ef-*` widgets (any depth, incl. root). The density adversary auto-flags this shape on any non-trivial CPT.
- Multiple top-level nodes or section semantics: use `ef-wrapper` with the appropriate `html_tag` (queried from schema; §2b records the value).
- Atomic V4 `e-div-block` / `e-flexbox`: only when EF wrapper features (loops, html_tag enum) are not needed.

## Phase 3 — Fan out: one subagent per widget

For each non-trivial widget node **from the §2d Section Blueprints**, dispatch a `voxel-widget-builder` subagent **in parallel**. The main agent does NOT load every widget's schema — only the subagents do, and each only loads the schema for the one widget it owns.

**Template-bound sections skip the per-widget fan-out.** A section that was adapted from a saved template (strategy `adapt-template` — its subtree arrived pre-composed from `template.json`) already has its widgets built, so it needs NO from-scratch per-widget synthesis. For a template-bound section, Phase 3 shrinks to a **delta-patch pass**: fill the `Lorem ipsum` placeholders with real per-post content and adjust only the specific props that differ for this post (the SSOT still wins prop-by-prop per §2b — patching is not a validation bypass). Only **unbound** sections (no matching template) get the full per-widget `voxel-widget-builder` fan-out described below.

**Preferred when opted into multi-agent orchestration:** express the fan-out as a Workflow `parallel(rows.map(r => () => agent(builderBrief(r), {agentType: 'voxel-builder:voxel-widget-builder', schema: NODE})))` step — each leg returns one schema-validated widget node, backgrounded and resumable (a re-run after a §2d tweak re-executes only the changed leg via `resumeFromRunId`). **Fallback (always valid):** send all widget-builders in a single inline message. **The orchestrator — not the Workflow — owns Phase 4 assembly and the Phase 5 import**; the Workflow runs only the mechanical per-widget fan-out. See [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Fan-out → Workflow expression map for the canonical expression and the orphan caveat.

**The subagent brief carries the blueprint row verbatim.** The widget-builder reads its assigned row from `/tmp/plan-<post_id>.md` (Settings column → prop bindings; Tag wrap column → `@tags()` discipline; Role column → static/dynamic decision; Pre-resolved column → cross-check that the widget will actually render data). Memory-based prop synthesis is forbidden — the SSOT (§2b) plus the blueprint row (§2d) are the only sources of truth.

### Subagent brief template

```
Build the JSON for ONE `<widget_type>` on site <site>.

Render context: <post_id>, post_type=<cpt_key>, role=<single|card|archive|page>, position=<hero|loop_child|...>

Blueprint row (verbatim from /tmp/plan-<post_id>.md §2d):
  - Section: <section_id>
  - Settings (prop → value/binding): <copy from §2d Settings column>
  - Tag wrap: <copy from §2d Tag wrap column>
  - Role: <copy from §2d Role column>
  - Expected DOM: <copy from §2d Expected DOM column>
  - Pre-resolved values across the sampled posts: <copy from §2d Pre-resolved column>

Steps:
  1. Read the committed SSOT `cli/src/generated/widget-schemas.json` for the `<widget_type>` prop list. Use `wpdev elementor:schema <site> <widget_type> [--prop <key>]` only as a live fallback when the SSOT is stale or absent.
  2. For every prop in the blueprint row, copy the `$$type` envelope shape from the SSOT (or from a golden fixture under `examples/<widget>.json`). Memory-based prop synthesis is forbidden.
  3. Wrap dynamic Voxel strings as `@tags()<expression>@endtags()`. Use raw vx envelope for `_cssid` and image-id refs.
  4. Emit ONLY the widget JSON object (id, elType, settings, elements: [], styles: [], interactions: [], editor_settings: [], version: '0.0'). **EF V4 atomic widgets/elements (`ef-card`, `ef-wrapper`, `ef-navbar`, `ef-form`, `ef-toc`, `ef-cal`) are ELEMENTS** — set `elType` to the type itself (e.g. `elType: 'ef-card'`) with NO `widgetType` key. Never emit a new Voxel `ts-*` classic widget; if a legacy `ts-*` node must remain, it is copied verbatim outside this builder path.
  5. Generate a unique 7-char hex `id`.
  6. Return the JSON object — no prose, no parent container. If any blueprint cell is missing or ambiguous, return a NEEDS-§2d-REVISION marker — never fill the gap from memory.
```

### When to dispatch vs inline

| Widget | Dispatch subagent | Inline |
|---|---|---|
| `ef-card` | ✅ — non-trivial prop count (heading rows + actions + tags repeaters) | |
| `ef-form`, `ef-navbar`, `ef-toc`, `ef-cal` | ✅ | |
| Voxel `ts-*` widgets | | Preserve verbatim only when already present; do not add/rebuild/customize. Replace new feed/search/list needs with `ef-wrapper` template/loop composition. |
| `ef-wrapper` with only `html_tag` + maybe `_vx_loop` | | ✅ |
| `e-div-block` / `e-flexbox` with no settings | | ✅ |

The dispatch column above applies only to **unbound** sections. A **template-bound section** (`adapt-template`) short-circuits the table entirely: its widgets already exist in the spliced `template.json`, so it gets a single delta-patch pass (fill placeholders / adjust the differing props), never a per-widget dispatch.

The six registered EF widgets are `ef-card`, `ef-form`, `ef-navbar`, `ef-toc`, `ef-cal`, `ef-wrapper` — there is no standalone button / media / breadcrumb widget. Buttons live inside `ef-card.ts_actions` and `ef-navbar.cta_ts_actions`; media slots are composed into `ef-card` / `ef-wrapper`. Citing `ef-media` / `ef-button` / `ef-breadcrumb` / `ef-map` is a phantom-widget bug — see [`widgets.md`](../references/ef/widgets.md) §Phantom for the host-widget translation; the `ssot-integrity` plan-review criterion flags every occurrence as severity C.

Why fan out: each subagent's context only contains its one widget's schema. The main agent's context only contains the tree plan + assembled IDs, never the raw schemas of every widget on the page.

## Phase 4 — Assemble the tree

Collect the subagents' returned widget JSON, slot them into the parent containers (which the main agent builds inline since wrappers are trivial), and produce the full `_elementor_data` array.

**Content-addressed IDs (#7 — deterministic idempotency).** Assign each node's 7-char id from `sha1("<section_id>:<row_index>:<widget_type>").slice(0,7)`, NOT random hex. Re-running the build on an unchanged plan yields a byte-identical tree — clean diffs, safe re-import, no ID churn. (Collision within a page is effectively impossible given the section:row:type seed is unique per node.)

Save the assembled JSON to `/tmp/built-<post_id>.json` for inspection before write.

## Phase 5 — Write + verify

**Write-time gate (#10/#11/#12 — automatic).** `wpdev elementor:import` snapshots before writing and **refuses to persist** a tree that fails the EF schema lint or carries `u00xx` unicode corruption — writing bad data is unrepresentable, not rolled back. `--no-verify` bypasses (not recommended).

```bash
# Write (positional <post_id> then <file>; --save also runs the editor-equivalent
# save so document migrations + per-post CSS regen happen in the same step)
wpdev elementor:import <site> <id> /tmp/built-<post_id>.json --save

# Verify
wpdev elementor:lint <site> --post <id>            # validates against the live schema
wpdev elementor:tree <site> <id>                   # confirms tree shape
wpdev rebuild <site> --only purge                  # flush all caches (object cache, transients, Elementor CSS, page cache, Voxel)
```

If `elementor:lint` reports `unknown-prop` or `type-mismatch`:
- `unknown-prop`: prop name doesn't exist on the live schema. Re-query and rename.
- `type-mismatch`: `$$type` envelope wrong. Re-query the prop's full spec and patch.
- `enum-violation`: value not in the prop's enum. Pick from the schema's `enum` array.
- `v3-shape`: legacy V3 settings shape — the EF migrator hasn't run or the data was hand-rolled wrong.

The `--save` flag performs the Elementor editor-equivalent save (document migrations + per-post CSS regeneration). If it fails, fall back to opening the editor URL from `wpdev elementor:templates <site>` and clicking "Update" before browser verification.

**If the build touched EF design tokens or kit colors** (not the common case — only when a token override or kit-color changed), re-sync them before browser verification:

```bash
wpdev rebuild <site> --only tokens   # push EF design tokens → Elementor kit, regen CSS, purge cache (re-fires the kit-color chain)
```

This closes the loop after token mutations so the rendered page reads the new token values. (Token *reset* is not a CLI verb — edit/remove the override in the EF Design Tokens admin page or the `ef_tokens` option, then re-run `--only tokens`.) The `voxel-elementor-fixer` Pass 2 runs this as the companion to `elementor:styles --sync-voxel`.

## Phase 6 — Browser verification

**Tool surface lives in [`browser.md`](../references/verification/browser.md)** — the `agent-browser` CLI protocol (parallel `--session` isolation, the command table, the mandatory layout-assertion `eval` block, the read-the-screenshot rule, the browser-unavailable fallback). This section owns only **what to verify and when**; the how is there. There is no `mcp__agent-browser__*` / `mcp__playwright__*` server — browser work is the `agent-browser` CLI via `Bash`.

**Why.** Lint validates schema correctness; browser verification proves the dynamic tags actually resolve, the CSS actually loaded, the action attributes are wired up, and there are no JS console errors at runtime. A schema-clean template can still render visually broken — missing field values, broken images, JS errors from misconfigured `ts-*` connections, dynamic-tag typos that resolve to empty strings, or `@post(...)` literals leaking through because a string wasn't wrapped in `@tags()...@endtags()`.

**When to skip.** Purely structural changes that don't affect render (e.g. moving a widget within a wrapper) OR when no example posts of the relevant CPT exist yet.

**Scope.** Verify on a small representative sample of posts — enough to trust the render across the field shapes the template uses; diminishing returns past that.

### Pre-flight: tail the debug log

Before opening any browser session, surface any pre-existing PHP fatals — they will cascade through unrelated sibling widgets and produce empty navbars / blank pages that look like the new change broke something:

```bash
wpdev wp <site> eval 'if (file_exists(WP_CONTENT_DIR . "/debug.log")) { echo implode("", array_slice(file(WP_CONTENT_DIR . "/debug.log"), -30)); }' --skip-plugins
```

If a non-empty fatal is present (`PHP Fatal error: Call to undefined function …`), report it to the user before starting the verify loop. A pre-existing fatal almost always means: do not declare your change broken until that fatal is resolved.

### Pick example posts

Find good verification candidates by sampling published posts of the CPT whose template was modified:

```bash
# cwd-independent — `wpdev wp <site>` proxies wp-cli with the site's path resolved
# internally. Do NOT `cd sites/<site> && wp …`: Bash-tool cwd persists across calls,
# so a relative cd fails once an earlier call already entered the directory.
wpdev wp <site> post list \
  --post_type=<cpt_key> --post_status=publish \
  --posts_per_page=3 --orderby=rand \
  --fields=ID,post_title,post_name --skip-plugins
```

For card templates: pick posts that appear inside a `ts-post-feed` (the card renders in feed context). Find a feed-bearing page first via `wpdev voxel:templates` or by inspecting an archive page — that page's URL is what subagents navigate to, not the post URL.

For single templates: any single post URL works — `wp post list` then construct `https://<site>.<tld>/<cpt_slug>/<post_slug>/`.

### Parallel verification pattern

The orchestrator owns the URL list and dispatches **one subagent per URL in a single message** (parallel, not sequential). Each subagent runs a self-contained `agent-browser` session under a **unique `--session vb-<post_id>-<n>`** (the isolation that prevents the profile-lock → text-scrape degradation — see [`browser.md`](../references/verification/browser.md) §Parallel isolation) and returns a structured finding. Sequential dispatch defeats the purpose — verifying 3 posts one-after-another costs 3× the wall time.

**Preferred when opted into multi-agent orchestration:** express the per-URL fan-out as a Workflow `parallel(urls.map(u => () => agent(verifyBrief(u), {schema: VERDICT})))` step — each leg returns a schema-validated pass/fail verdict object, so aggregation reads structured returns. **Fallback (always valid):** the single inline message above. **The verify→repair loop stays orchestrator-owned, NOT inside the Workflow:** the orchestrator reads the verdicts, decides repair, and re-dispatches a fresh verify fan-out — the convergence guard below is the orchestrator's `while` on the open-Critical set, not a Workflow construct. Canonical expression + orphan caveat: [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Fan-out → Workflow expression map.

Brief template (the orchestrator fills in `<URL>`, `<n>`, the `_cssid` list, and `<expected>`):

```
Verify the rendered output of <URL>. Use the agent-browser CLI (run
`agent-browser skills get core` first if unfamiliar). Use --session vb-<post_id>-<n>
on EVERY command so this run is isolated from sibling verifiers. Follow the command
table + layout-assertion block in references/verification/browser.md exactly.

Steps: open → wait --load networkidle → wait for a known selector (the card _cssid or a
known h-tag) → screenshot --full /tmp/verify-<post_id>-<n>.png → console → errors →
network requests --filter "**/elementor-post-*.css" → get text body → the eval --stdin
LAYOUT ASSERTION block over these _cssids: [<from the §2d Layout map>] → close.

Return Pass/Fail for the standard checklist in references/verification/browser.md
§Standard verification checklist, PLUS: the console+errors output, the screenshot path,
your written description of the screenshot (READ the PNG — hero present? sections
side-by-side as planned? sidebar right? feed cards filled?), and the layout-assertion
JSON object verbatim.
```

The full checklist and the exact layout-assertion `eval` block are in [`browser.md`](../references/verification/browser.md) — do not re-author them here.

### Aggregation rule

Verification runs the **render-phase criteria** (`criteria.json` rows with `phase ∈ {render, both}`) per sampled post; findings land on the same finding bus (`/tmp/findings-<post_id>.jsonl`) as the plan phase.

**Autonomous verify→repair loop (#14).** **Pass** = every Critical render criterion `pass` on every sampled post. On any Critical fail the orchestrator runs a bounded auto-repair WITHOUT a human: map the failing `criterion_id` to its repair (`selector-found` fail → editor Update + `wpdev rebuild`; `no-tag-leak` → fix the `@tags()` wrap; `layout-assert` → fix the grid envelope via `wpdev elementor:mutate`), apply, then re-run Phase 6 on the SAME URL set. The **convergence guard (#15)** governs it: the open-Critical render-finding set MUST strictly shrink each pass, or the loop halts and escalates. If `agent-browser` won't launch, follow [`browser.md`](../references/verification/browser.md) §Fallback — flag `render-unverified` and surface; never pass on `curl` text alone.

**Empty-vs-bug (#17 — computed, not judged).** A render-empty value is not automatically a failure: the `text-rendered` criterion passes iff `wpdev voxel:data <site> --id <post>` shows that field empty on that post (genuine empty), and fails only when data exists but the DOM is empty (real wiring bug). The orchestrator computes this rather than judging it.

Common failure modes to recognize:
- **Selector not found** → CSS wasn't regenerated; remind user to "Update" in the Elementor editor + run `wpdev rebuild <site> --only purge` (or full `wpdev rebuild <site>`, which regenerates CSS and purges caches in one pass).
- **`@post(...)` leaks in HTML** → dynamic tag wasn't wrapped with `@tags()...@endtags()` or used the wrong envelope.
- **404** → permalink rewrite needs flushing (`wpdev wp <site> rewrite flush`).
- **JS error referencing missing `ts-map`** → page lacks the Voxel widget the action depends on.
- **Empty byline / heading** → resolved by the `text-rendered` empty-vs-bug predicate above (genuine-empty passes; data-present-but-DOM-empty fails). `wpdev voxel:data <site> --id <post>` is the arbiter.

### When example data is missing

If the test post has empty values for fields the template references, browser verification will report "empty heading" failures that aren't real bugs. Run `wpdev voxel:data <site> --id <post>` first; pick posts whose values are non-empty for the fields the template uses.

## Modifying existing data

> Migrating a page OFF legacy Elementor V3 (containers + `heading`/`text-editor`/`button`/`counter`/`nested-accordion`) onto EF V4 atomics is its own workflow — see [`migrate.md`](migrate.md) for the Iron Law (drop structure/styling aggressively, preserve data verbatim), the `migrate:main`/`migrate:containers` structural pass, and the parallel fan-out consolidation. That per-section consolidation fan-out follows the same dispatch shape as Phase 3 build — **a Workflow `parallel()` step when opted into multi-agent orchestration (with per-section isolation if writing files), inline single-message dispatch otherwise** — per [`parallel-dispatch.md`](../references/core/parallel-dispatch.md) §Fan-out → Workflow expression map. The notes below cover smaller in-place edits.

Same pipeline, with one extra Phase 0:

**Phase 0 — Capture current state.**
```bash
wpdev elementor:dump <site> all --post <id> --json > /tmp/before-<id>.json
wpdev elementor:tree <site> <id> > /tmp/before-tree-<id>.txt
```

Then proceed through Phases 1-5. The captured before-state is the rollback target.

**Mandatory gate — Behavior Contract + DOM-text baseline.** Before mutating existing data, the command-host authors a Behavior Contract triple (what must not change / allowed structural delta / forbidden semantic delta) and captures a DOM-text baseline of the affected widgets' data-bound props, per [`behavior-contract.md`](../references/verification/behavior-contract.md). The post-mutation re-audit diffs the new DOM-text against that baseline — a changed data-bound value the contract pinned is a Forbidden Semantic Delta violation → roll back. No baseline → no fix. The contract is authored by the command-host (not the fixer) and the re-audit is the reviewer; that author≠repairer≠reviewer separation is what makes "this is a refactor, not a behaviour change" verifiable rather than asserted. Greenfield builds (no prior data) skip this gate.

If the modification only touches a few widgets, the subagent brief becomes "modify this widget by changing prop X to Y" and the subagent receives the current widget JSON as input. Other widgets are left untouched.

For risky migrations: snapshot revisions first via `wpdev elementor:revisions:prune` (creates a snapshot before pruning) — gives a clean rollback point.

### Choosing the mutation tool

| Mutation type | Tool | Why |
|---|---|---|
| Surgical patch on 1-3 widgets | author `/tmp/<task>-mutator.php`, then `wpdev elementor:mutate <site> <id> /tmp/<task>-mutator.php [--fetch <url>]` | **Canonical post-write repair path** — atomically runs the mutator (via `wp eval-file --skip-plugins`) → lints → regenerates per-post CSS → purges LiteSpeed+page cache → optionally fetches the URL for an HTTP-status check. Replaces the 6 manual commands the loop used to need (CSS regen + purge were forgotten on every iteration before this wrapper existed). |
| Add / remove repeater rows on one widget | same — author mutator, run via `wpdev elementor:mutate` | Re-emitting the whole tree risks losing unrelated edits; the tree-walking patcher preserves siblings. |
| Full subtree rewrite (whole template) | `wpdev elementor:import <site> <id> /tmp/built.json --save` | Lint-checkable before write; `--save` performs document migrations + per-post CSS regen. |
| Bulk same-prop change across many posts | author a `get_posts()`-loop mutator, run via `wp eval-file` (no single post id for `elementor:mutate`) | Batched; purge once at the end with `wpdev rebuild <site>`. |
| Strip redundant wrapper containers around `ef-*` widgets (incl. single-`ef-card` root) | `wpdev elementor:strip:wrappers <site> --fix --yes` | Site-wide canonical wrapper-cleanup; lint-aware, idempotent; handles single-card-at-root + deeper redundant wrappers in one pass. Snapshot first and use only for an approved site-wide cleanup. |
| Strip per-node style overrides | `wpdev elementor:strip:styles <site> --post <id> --fix --yes` | When audit flags style overrides that should be globals. |
| Fix unicode corruption (`u00e9` leaks) | `wpdev elementor:fix:unicode <site> -y` | **Site-wide only** — no `--post` filter exists. Snapshot every Elementor post first via `wpdev elementor:revisions:prune <site>` (no `--post`); run once per fix loop. |

**Hard rule: never use `wp eval '...'` heredoc for `_elementor_data` mutations.** Backslash-escape and PHP-namespace separators inside heredocs parse-fail in shells and have cost multiple sessions a debug round. Always:

1. Write the patcher to `/tmp/<task>-mutator.php` first (regular `Write` tool). The script reads `_elementor_data`, `json_decode`s it, walks the tree, mutates by widget id, re-encodes with `JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES`, and writes back via `update_post_meta`. Use the `EF\Envelope::responsive_string(...)` / `::image(...)` / `::vx_visibility(...)` factories for any `$$type` envelope (see [`actions.md`](../references/ef/actions.md) §Loopable action-rows) — hand-authored envelopes with missing inner `$$type` markers render as absent and lint can't always catch a partial shape.
2. Run it through the atomic loop: `wpdev elementor:mutate <site> <id> /tmp/<task>-mutator.php` — never raw `wp eval-file` for a single-post `_elementor_data` change, because that skips the CSS-regen + cache-purge tail and the page renders stale. Add `--fetch "https://<site>.<tld>/<slug>/"` to surface a 4xx/5xx the lint can't see.
3. Then run Phase 6 browser verification ([`browser.md`](../references/verification/browser.md)).

Pattern for a tree-walking patcher (idempotent, preserves siblings):

```php
<?php
$post_id = <post_id>;
$raw = get_post_meta($post_id, '_elementor_data', true);
$data = json_decode($raw, true);
if (!is_array($data)) { exit("decode failed\n"); }

$walk = function (&$nodes) use (&$walk) {
    foreach ($nodes as &$node) {
        if (($node['id'] ?? '') === '<target_widget_id>') {
            $node['settings']['<prop>'] = ['$$type' => 'string', 'value' => 'new value'];
        }
        if (!empty($node['elements'])) { $walk($node['elements']); }
    }
};
$walk($data);

update_post_meta($post_id, '_elementor_data', wp_slash(wp_json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)));
echo "patched\n";
```

Always `JSON_UNESCAPED_UNICODE` — French accents (`é`, `è`, `ç`) round-trip through WP slashing layers cleanly only with this flag (otherwise `é` can lose its backslash and end up as literal `u00e9`).

## Cards: deferred to `wpdev voxel:cards`

For the action footer on `ef-card` (call, email, get_directions, show_post_on_map, etc.) see [`actions.md`](../references/ef/actions.md). For the tag overlay (pill stack + corner ribbons + `+N` overflow popover) see [`widgets.md`](../references/ef/widgets.md).

Don't hand-write JSON for the `card` role. The CLI does it correctly:

```bash
wpdev voxel:cards <site>                                   # all CPTs, all four variants (small + medium + large + link)
wpdev voxel:cards <site> --type <cpt_key>                  # one CPT
wpdev voxel:cards <site> --sizes small,medium,large,link   # explicit variant list (this is also the default)
wpdev voxel:cards <site> --sizes link                      # one variant only
wpdev voxel:cards <site> --replace                         # rebuild existing
```

The command supports four variants (size is a scaffold recipe in `cli/src/utils/voxel/card-bindings.ts`, NOT an `ef-card` prop — the widget's own axes are `variant` = color surface and `layout` = vertical/horizontal):

| Variant | Shape | Use case |
|---|---|---|
| `small` | (logo if the CPT has one) + linked h3 title + excerpt body; no media, no byline, no actions | Compact grid items, search results |
| `medium` | `layout: horizontal`; (logo if any) + linked title + excerpt + author byline (name/date/avatar); no cover | Mid-density list rows |
| `large` | `layout: vertical`; featured-image cover (`@post(_thumbnail_id.id)`, cover fit, overlay) + (logo if any) + linked title + excerpt + author byline + a gated `hierarchy-children` pill loop (visibility-gated, renders only on hierarchy CPTs) | Hero feeds, archive top-of-fold |
| `link` | Transparent background; single inline `span` with hashtag icon + linked title + excerpt; nothing else | Related-post lists, hierarchy/breadcrumb references, inline tag-style links |

**Logo rule.** The logo binds to a real logo field only — a field labelled "logo", else a `profile-avatar` field (profile CPTs). If the CPT has neither, the card carries NO logo. The featured image is NEVER used as a logo; it is only the `large` card's cover/media slot. So a CPT like `video` (no logo field) renders logo-less cards, with the featured image appearing solely as the large-card cover.

The byline is the **author** — `@author(display_name)` + `@post(date)` + `@author(avatar)` (avatar is the bare attachment id, no `.id`; `@post(author.*)` resolves EMPTY). Because cards render in same-parent loops, only `hierarchy-children` differs per card, so it is the only hierarchy field bound on a card body — see [`../references/voxel/voxel-field-inventory.md`](../references/voxel/voxel-field-inventory.md) §Always-present fields. No variant ships a default `ts_actions` strip; add meaningful actions with [`card-actions.md`](card-actions.md).

The command:
- Creates `{key}-small` / `{key}-medium` / `{key}-large` / `{key}-link` Elementor templates.
- Injects an unwrapped `ef-card` widget with the right envelope per variant.
- Registers as `voxel:post_types[<key>].custom_templates.card[]` with `{Singular} - small / - medium / - large / - link` labels.

If different card content is needed, run `voxel:cards` first to register the templates, then modify the resulting template via this pipeline (Phase 0 to capture, Phase 1-5 to mutate).

## Wrapper-or-no-wrapper rule

- A `_elementor_data` array's root may be `[ widget ]` directly — no wrapping container required.
- A single `ef-card` at root: do NOT wrap. `wpdev elementor:strip:wrappers` removes redundant wrappers around `ef-*` widgets at any depth, including root.
- Multiple top-level nodes or section semantics: use `ef-wrapper` with `html_tag: section` so loop / EF features remain available.
- Atomic V4 `e-div-block` / `e-flexbox`: only when there's a specific need the EF wrapper can't satisfy.

## Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `elementor:lint` reports `unknown-prop` for a recently-renamed key | Memorised V3 prop name | Re-query schema, use new name |
| Dynamic tag renders as literal `@post(title)` text | Missing `@tags()...@endtags()` wrapper on a string-type prop | Wrap the value |
| Image renders empty | Image `$$type` wrong; needs `{$$type: image, value: {src: {$$type: vx \| number, value: ...}}}` | Query `--prop <key>` for exact shape |
| Feed renders empty | CPT lacks `search.filters` + `search.order`, or index table missing | Add to blueprint, run index table create + reindex |
| Form submit doesn't update feed | `ts_post_to_feed` references stale widget ID | Update to current feed widget's `id` |
| Single ef-card rendered with extra spacing | Wrapper container present | `wpdev elementor:strip:wrappers <site> --fix --yes` (site-wide; snapshot first, approved cleanup only) |
| CSS not applied after write | `--save` failed or was omitted | Re-run import with `--save`, or open editor URL and click "Update" |

## Mistake guards

- Never synthesize widget JSON from memory; read SSOT/live schema or a real dump first.
- Never import without rollback export and `--save`/CSS regeneration path.
- Never let subagents import; orchestrator assembles, writes, and verifies.
