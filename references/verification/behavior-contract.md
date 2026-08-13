# Behavior Contract — the pre-mutation gate for existing-data fixes

> No fixer mutates existing `_elementor_data` without a written Behavior Contract **and** a captured DOM-text baseline. The triple says what must not change; the baseline is the falsifier that proves it didn't.

This applies **only when modifying existing data**. Greenfield builds (no prior `_elementor_data`) skip the contract entirely — there is no behaviour to preserve.

## Who authors it (hard role separation)

The **command-host** — the user-session orchestrator above both `voxel-page-auditor` and `voxel-elementor-fixer` — authors the triple and captures the baseline, **then** dispatches the fixer with both as **read-only inputs**. The fixer never writes its own contract.

Why command-host and not the fixer: an agent that both writes "do not change the loop resolution" and performs the edit has no adversarial pressure to honor it — drift smuggling becomes invisible. The separation that makes the contract real is **author (command-host) ≠ repairer (fixer) ≠ reviewer (the re-audit, a structurally separate read-only `voxel-page-auditor` run)**. "The scope is tighter" does not substitute for this separation.

## The triple (per fix boundary)

One triple per fix boundary (the set of widgets one approved fix touches), written to the audit context before dispatch.

### 1. Behavior Contract — what MUST NOT change

Observable behavior, concrete and verifiable — not aspirational. Examples:
- "Each `_vx_loop` row in widget `abc123` resolves to the same post (and same rendered title) as pre-fix."
- "The card's `@post(title)` heading renders the same text for the example posts in the sample (e.g. `<post_id>`, `<peer_id>`, `<example_post>`)."
- "Stored `_elementor_data` continues to JSON-decode without `wp_unslash()` — the encoding contract is preserved."

### 2. Allowed Structural Delta — what IS permitted this pass

Enumerate the moves. Anything outside is forbidden, even "obvious cleanup". Examples:
- "Add an `action_link` (cell `type` + `link`) to the author-line `heading` content-block row in widget `abc123`."
- "Strip the single-`ef-card` root wrapper via `elementor:strip:wrappers`."

NOT allowed: renaming a `_cssid`, changing a sibling widget's props, "fixing" an unrelated tag while in the file.

### 3. Forbidden Semantic Delta — the scoped negative-space list

Specific prohibitions that stop "tiny improvement" drift. Examples:
- "Do NOT change which post any `_vx_loop` row resolves to."
- "Do NOT alter the `@tags()` wrapper on any prop the fix does not name."
- "Do NOT widen a visibility rule."

## The falsifier — DOM-text baseline

The re-audit re-runs the same heuristics that missed the regression the first time, and a 2-3 screenshot can't catch a render-valid-but-semantically-wrong change (the relation-loop case renders N plausible-looking pills). So the contract is backed by a mechanical check.

**Before mutation** (command-host, via the same `agent-browser` CLI used in audit Stream D / [`rules.md`](../core/rules.md) rule 7 — see [`browser.md`](browser.md); prefer this over a new CLI verb):

```bash
agent-browser --session bc-<post_id> open "https://<site>.<tld>/<slug>/"
agent-browser --session bc-<post_id> wait --load networkidle
# Extract textContent of every data-bound anchor named in the Behavior Contract:
agent-browser --session bc-<post_id> eval --stdin > /tmp/baseline-<post_id>-<widget_id>.txt <<'EOF'
// anchors: [data-id="<widget_id>"] or .s-<cssid> when _cssid is set
const sels = ['[data-id="<widget_id>"] .ef-ih-content', '#<cssid> .ef-tag']; // the contract's data-bound nodes (content-block prose + tag pills)
sels.flatMap(s => Array.from(document.querySelectorAll(s)).map(n => n.textContent.trim())).join('\n');
EOF
agent-browser --session bc-<post_id> close
```

1. Navigate to the post's front-end URL (isolated `--session bc-<post_id>`).
2. Scope to each affected widget's DOM anchor (`[data-id="<widget_id>"]`, or `.s-<cssid>` when `_cssid` is set). Use `.textContent` (not `.innerText`) so collapsed `<details>`/accordion content is captured — `innerText` omits it and reads as a false-negative drop.
3. Extract the `.textContent` of the data-bound nodes named in the Behavior Contract (loop rows, dynamic-tag props).
4. Save to `/tmp/baseline-<post_id>-<widget_id>.txt`, one line per data-bound node.

**After each fixer pass**, the re-audit re-fetches the same anchors and diffs against the baseline:

- Data-bound text the contract said "must not change" but did → **Forbidden Semantic Delta violation → roll back** (restore `/tmp/before-<id>.json`).
- Text changed only where the Allowed Structural Delta expected it → pass.

**If baseline capture fails** (front-end render unavailable, auth wall, render timeout): the fix is **NOT dispatched**. The finding is flagged "unverifiable — baseline capture failed" and surfaced to the user. There is no silent fix-without-baseline; a contract with no falsifier is not a contract.

## `behavior_contract_class`

Every existing-data fix carries one:

- **structural_only** — observable behavior unchanged. Proceed; the triple + baseline constrain the fixer.
- **observable_delta** — the fix intentionally changes something observable (e.g. shifts layout ~4px). The command-host asks the user to opt in (AskUserQuestion) **before** dispatch; on No, the finding is deferred.
- **bug** — this is a defect, not a refactor. Do **NOT** fix it here. Emit a generic marker: *"this is a bug, not a refactor — route it to your debugging workflow."* **No hardcoded `/ce-debug`** — the plugin is standalone; the marker names the user's workflow generically so marketplace installs without compound-engineering still work.

## Worked example — structural fix on a card that contains a loop

Finding `[W-I3]`: wire the author-line `heading` content-block row's action on card widget `abc123` (it renders as `<span>`, should be `<a>`). The card also has a `_vx_loop` tags repeater over `@post(hierarchy-ancestors)`.

**Behavior Contract:**
- Each `_vx_loop` row in `abc123` resolves to the same ancestor post (same rendered title) as pre-fix.
- The card's title and image render identical text / src to pre-fix.

**Allowed Structural Delta:**
- On that `heading` content-block row of `abc123`, set the action suite `type: action_link` + the `link` envelope. Nothing else.

**Forbidden Semantic Delta:**
- `@post(hierarchy-ancestors)` at each `_vx_loop` row index must resolve to the same post as pre-fix.
- Do NOT alter `_vx_loop.tag`, the loop's inner `text` / `link` tags, the `_cssid`, or any sibling widget.

**Falsifier:** the baseline captures each loop row's `.textContent` pre-fix. After the fix lands, the re-audit re-fetches and diffs — rows unchanged → GREEN. If the heading-row edit perturbed the loop (for example, a tree walk re-serialized a tag and violated the current [`loop authoring contract`](../voxel/voxel-loop-authoring.md)), the diff shows changed row text → Forbidden Semantic Delta violation → roll back.

**class:** `structural_only`.

## The negative control — prove the assertion can fail

A regression test that passes against the fixed code has proven nothing: it may
be asserting a property that was already true. Before a test counts as coverage
for a fix, run it against the **pre-fix** artifact and watch it fail.

```bash
# Restore just the pre-fix asset (use the FIX COMMIT's parent, not HEAD~1 —
# other agents may have committed on top of yours since).
git show <fix-sha>~1:<path/to/asset> > <path/to/asset>
<run the test>            # MUST fail; if it passes, the test is not coverage
git checkout <fix-sha> -- <path/to/asset>
<run the test>            # MUST pass
```

When the test passes both ways, do not delete it and do not quietly keep it as
if it were proof. Either tighten the assertion until it discriminates, or
relabel it for what it is — a no-regression guard on already-working behavior —
and say so in a comment next to the test, with the measured numbers. A comment
claiming a failure mode the test never detects is worse than no comment.

Measure before asserting a threshold. Deriving the bound from a real run (for a
snap-scrolling carousel: is the delta a fraction of a page, or a whole page?)
is what separates a bound that discriminates from `not.toBe(0)`, which passes
on any nonzero drift.

## Closing rule

> A fix that cannot capture its baseline is a fix that cannot be verified. Flag it unverifiable and stop — never wave it through.
