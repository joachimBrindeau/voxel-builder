---
description: "Match-and-apply fix for known bug classes that are mechanically detectable + mechanically fixable in EF V4 atomic _elementor_data — broken action-row loops, fragile vis-gates on structured fields, malformed envelopes, CSS-cols inheritance cascades, missing root <main> wrapper, missing per-card semantic tags. Skips the full plan-review cycle when the diagnosis fits a known catalog row. Triggers on: 'fix known bugs', 'apply standard fixes', 'fix the action-row loop', 'fix layout cascade', 'fix envelope', 'fix-known'."
---

Apply mechanical fixes for the known catalog of EF V4 / Voxel bugs that recur across templates. Each bug class has a deterministic detection pattern + deterministic fix; the full page-planning + adversarial-review cycle is skipped because the issue is class-matched, not novel.

**Required reading before dispatch:**

1. `SKILL.md`.
2. `references/core/rules.md` — Rule 1, 5, 8 in particular.
3. `references/ef/actions.md` §Loopable action-rows — covers the loop / comparator / vis-gate fix classes.
4. `references/verification/behavior-contract.md` — required when fixes will mutate existing data on a template that's already in production.

**Bug catalog (per-class detection + fix):**

| Class | Detection (mechanical) | Fix (mechanical) |
|---|---|---|
| `loopable-row-missing-loop` | Any `ts_actions` / `tags` / `headings` row whose `text` / `label` / `value` cell references `@post(<repeater>.<scalar>)` AND the row has no `_vx_loop` cell | Add `_vx_loop: vx_loop("@post(<repeater>)")` + per-row `_vx_visibility` filtering on `@post(<repeater>.<filter_subkey>)`. Comparator picked via `EF\Envelope::comparator_for_subfield()`. |
| `array-comparator-mismatch` | Any `_vx_visibility` rule with `compare: is_equal_to` AND the rule's `tag` references a sub-field whose type is taxonomy / multiselect / post-relation (looked up via `wpdev voxel:fields`) | Swap `compare: is_equal_to` → `compare: contains`. |
| `fragile-vis-gate-on-structured-field` | Any section-level `_vx_visibility` with `compare: is_not_empty` on `@post(<field>)` where the field's type is work-hours / location / repeater / product | Either (a) remove the gate (let the `ts-*` widget handle emptiness internally), or (b) gate on a scalar sub-key e.g. `@post(<field>.0.<scalar>)`. Default: (a). |
| `malformed-envelope` | Any prop value where the outer `$$type` is set but inner sub-envelopes (e.g. `cols.value.desktop.value` without `$$type: string` on `desktop`) are missing markers — surfaced by `wpdev elementor:lint` as `v3-shape` on a responsive primitive | Rewrite the prop using `EF\Envelope::responsive_string(...)` / `EF\Envelope::vx_visibility(...)` to ensure full canonical envelope shape. |
| `cols-inheritance-cascade` | Any wrapper inside another wrapper where the parent has explicit `cols` AND the child has `cols.value.desktop.value === ""` (default) — child renders with parent's tracks via CSS custom property inheritance | Set child's `cols.value.desktop.value = "1fr"` with full canonical envelope. ALSO ensure elementor-framework `base.css` has the `--ef-cols: initial` reset (shipped 2026-05-29 in the same release). |
| `missing-root-main` | Root depth-0 of `_elementor_data` is NOT a single `ef-wrapper` with `tag: main` | Wrap all root-level nodes in a new `ef-wrapper(tag: main, _cssid: "<cpt-key>-single")` at depth 0. |
| `missing-hero-header-tag` | First child of root `main` is `ef-card` with `tag: article` or default — should be `header` per hierarchy criterion's wrapper-tag walk | Set first child's `tag` prop to `header`. |
| `cta-aside-mistag` | Last child of root `main` that contains a `ts-post-feed` "related" surface has `tag: section` — should be `aside` (tangentially related content) | Set the wrapper's `tag` to `aside`. |

## Entry criteria

1. A real Voxel CPT or page with `_elementor_data` exists on a reachable site.
2. The user's request names a concrete target or observation matches one catalog class exactly.
3. The operator has reviewed and explicitly approved the dry-run report before applying.
4. `wpdev elementor:codegen --check` passes unless the fix is a single isolated class on an unchanged SSOT.

## Exit criteria

1. `/tmp/fix-known-<post_id>-report.md` exists with all detected issues.
2. If `--dry`: report delivered to operator and no mutation happened.
3. If applied: `wpdev elementor:lint <site> --post <id>` passes with 0 findings.
4. Phase 6 browser verification passes per `references/verification/browser.md`.
5. No fix regresses layout beyond the class's expected delta.

**Protocol:**

- Validate `<site>` and `<post_id>`. Halt if either missing.
- Read `_elementor_data` via `wpdev elementor:dump <site> all --post <post_id> --json`.
- Read `wpdev voxel:fields <site> <cpt_key>` to get field types (needed for comparator picking).
- Walk every node. For each bug-catalog class, run the detection check; if it matches, build the fix patch.
- Output to `/tmp/fix-known-<post_id>-report.md` with one section per detected issue: `{class, node_id, evidence, proposed_fix_diff}`.
- If `--dry`: stop here. Operator reviews the report.
- Otherwise: emit a single PHP mutator at `/tmp/fix-known-<post_id>.php` using `EF\Envelope::*` factories (no hand-authored envelopes), then run the atomic loop `wpdev elementor:mutate <site> <post_id> /tmp/fix-known-<post_id>.php --fetch "https://<site>.<tld>/<slug>/"` — it applies the mutator, lints, regenerates per-post CSS, purges caches, and HTTP-checks the URL in one pass (never raw `wp eval-file` for a single-post `_elementor_data` change — that skips the CSS-regen + purge tail and the page renders stale). Then run Phase 6 browser verification per `references/verification/browser.md` (mandatory — checklist + computed-style layout assertions, one `agent-browser --session` per post). The verify→repair convergence decision stays with the orchestrator, not this command — a fix that regresses layout escalates rather than auto-looping.

**Anti-patterns:**

- Do not invent new classes. The 8 above are the complete catalog as of 2026-05-29; add a new class only after observing the same bug ≥2 times in production and adding it to this file + the `references/ef/actions.md` / `workflows/page-planning.md` cross-references.
- Do not apply a class fix without the detection pattern matching exactly. "It looks like the loop-row bug" is not a fit — the rule is "row references `@post(<repeater>.<scalar>)` AND has no `_vx_loop` cell".
- Do not skip Phase 6 verification. Layout-assertion regressions in past sessions passed every text-only check.
- Do not run `--dry` and then write anyway. Apply only on explicit `APPROVE` after the dry-run report.

**When NOT to use this command:**

- Greenfield builds → the build workflow (`workflows/build.md`) (full plan-page-planning cycle).
- Novel bug classes not in the catalog → audit + plan + reviewer.
- Pure cosmetic changes (eyebrow text, CTA label rewording) → direct edit via blueprint mutation.

## Mistake guards

- Never invent new bug classes inside this fast path.
- Never apply when the catalog detection pattern does not match exactly.
- Never continue after `--dry`; wait for explicit approval before mutation.
