# Page Planning Pipeline — section-by-section, adversarially-reviewed, SSOT-driven

Plan non-trivial EF pages/templates before build or migration. The orchestrator owns the
Plan Document and gates; specialists return bounded leaf batches for phrasing, layout, and
adversarial criteria. No specialist edits the Plan Document.

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

**Entry:** Shared fields and representative post data from the caller are available.

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

**Entry:** Phase 2a inventory is complete and codegen/check passed.

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

## Phase 2c - Select Archetypes And Vocabulary

**Entry:** Field Inventory and Widget Catalog are complete.

1. Read `references/core/page-plan-archetypes.md`.
2. Assign each required information group to one archetype and section id.
3. Dispatch heading-curator plan leaves and layout-architect section leaves through the
   bounded batch contract; do not create one worker per section.
4. For a full page/single/archive/hub, first check the **Pages** table in `templates/index.md`: when a `scope: page` template matches the target archetype, bind the whole page to it (its section set/order come pre-composed) and record the page template id. Otherwise assign per-section archetypes/templates.
5. Record deliberate field exclusions and saved-template bindings (page-scope and section-scope).

**Exit:** Every public field/relation is assigned or excluded; section order, archetypes,
and phrasing inputs are complete.

## Phase 2d - Compose Section Blueprints

**Entry:** Phase 2c assignments and layout/phrasing leaves validate.

1. Read `references/core/page-plan-contract.md`.
2. Compose every section and widget row using the required Blueprint columns.
3. Resolve all dynamic bindings on representative complete, sparse, and typical posts.
4. Prove root/landmark/heading order and layout occupancy.
5. Write the Plan Document once, then validate it against the contract before review.

**Exit:** The Plan Document is schema-complete, every Blueprint row is attributable to a
field/archetype, and all bindings have evidence.

## Phase 2e - Adversarial Review

**Entry:** The Plan Document validates against the contract and all Phase 2d bindings have
evidence.

1. Select every applicable plan/both criterion from `references/core/criteria.md`.
2. Partition 5-10 criteria per `voxel-plan-reviewer` batch. Run bounded waves through
   `references/core/parallel-dispatch.md`; do not create one worker per criterion.
3. Require one leaf envelope per criterion with positive pass evidence or scoped findings.
4. Reject cross-criterion findings and missing evidence. Retry rejected criteria at most
   twice.
5. Merge valid findings into `/tmp/findings-<post_id>.jsonl` and render
   `/tmp/plan-review-<post_id>.md` sorted by criterion, severity, and finding id.

**Exit:** Returned criterion ids equal the selected set; all findings have evidence and no
required criterion is silently missing.

## Phase 2f - Reconcile Findings

**Entry:** Phase 2e findings bus and human-readable review exist.

1. Assign every finding exactly one outcome: `resolved`,
   `override: <concrete evidence-backed reason>`, or `deferred: <tracked item>`.
2. Reject generic/evidence-free overrides and keep their Critical finding open.
3. Revise the Plan for resolved findings and rerun only affected criterion leaves through
   bounded batches.
4. Track the open-Critical fingerprint. Continue only when the set strictly shrinks; if it
   stalls, halt and escalate the residual instead of retrying indefinitely.
5. Keep the JSONL bus authoritative and render the Markdown review from it.

**Exit:** Every finding has a valid outcome; the Plan matches resolutions; open Criticals
are empty or explicitly escalated.

## Phase 2g — Gate (autonomous by default, human on exception)

**Entry:** Phase 2f outcomes are complete and the Plan contract validates.

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

## Plan Document Contract

The required document structure, Blueprint schema, examples, and gate block live in
`references/core/page-plan-contract.md`. Treat that file as the output schema; do not
invent alternate headings or columns.

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
