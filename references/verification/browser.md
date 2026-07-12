# Browser verification — the `agent-browser` CLI protocol (SSOT)

The single source of truth for **how** every voxel-builder phase drives a browser: Phase 6 of [`build.md`](../../workflows/build.md), Stream D of [`audit.md`](../../workflows/audit.md), Phase 5 of [`migrate.md`](../../workflows/migrate.md), the CPT smoke-test in [`cpt-lifecycle.md`](../../workflows/cpt-lifecycle.md), the Behavior-Contract DOM baseline in [`behavior-contract.md`](behavior-contract.md), and the migration-preservation production baseline in [`page-planning.md`](../../workflows/page-planning.md). Those files describe **what** to assert; this file owns the **tool surface**. Do not duplicate the command list anywhere else — link here.

## The tool is `agent-browser` — a CLI, not an MCP server

Browser work goes through the **`agent-browser` CLI**, invoked via `Bash`. There is **no** `mcp__agent-browser__*` MCP server and there is **no** `mcp__playwright__*` / `mcp__crawl4ai__*` dependency in this skill — citing any of those is a phantom-tool bug. The agent-browser skill (`~/.claude/skills/agent-browser`) is a discovery stub; the live, version-matched command reference is served by the CLI itself:

```bash
agent-browser skills get core           # workflows + common patterns — read first if unfamiliar
agent-browser skills get core --full     # full command reference + templates
agent-browser doctor --offline --quick   # confirm Chrome + daemon are healthy before a run
```

Any subagent with `Bash` can drive it; there is nothing to "connect" first.

## Parallel isolation — one `--session` per subagent (fixes the profile-lock)

The single hardest-won lesson from past sessions: a shared browser profile **locks** when two verification subagents run at once, and the pipeline then silently degrades to `curl` text-scraping that misses every layout regression. `agent-browser` solves this natively — **each `--session <name>` is a fully isolated browser** (own cookies, tabs, refs, Chrome process).

**Rule: every parallel subagent MUST pass a unique `--session` on every command.** Name it `vb-<post_id>-<n>` (n = the subagent's URL index). The orchestrator dispatches all URL subagents in one message; isolation is what makes that safe.

```bash
# subagent #1
agent-browser --session vb-<post_id>-1 open "<URL_1>"
# subagent #2 (concurrent — different session, no lock)
agent-browser --session vb-<post_id>-2 open "<URL_2>"
```

Always `agent-browser --session vb-<post_id>-<n> close` at the end of the subagent so the Chrome process is reclaimed.

## The verification loop (the command surface)

| Step | Command | Replaces the old phantom call |
|---|---|---|
| Navigate | `agent-browser --session <s> open "<URL>"` | `browser_navigate` |
| Settle | `agent-browser --session <s> wait --load networkidle` | implicit |
| Wait for a known node | `agent-browser --session <s> wait --text "<expected>"` or `wait "<css-selector>"` | `browser_wait_for_selector` |
| Accessibility tree | `agent-browser --session <s> snapshot -i` | `browser_snapshot` |
| Full-page screenshot | `agent-browser --session <s> screenshot --full /tmp/verify-<post_id>-<n>.png` | `browser_screenshot` |
| HTML of a node | `agent-browser --session <s> get html "#<_cssid>"` | `browser_get_html` |
| Visible text | `agent-browser --session <s> get text "#<_cssid>"` | — |
| Element count | `agent-browser --session <s> get count ".<feed-card-class>"` | — |
| Bounding box (width/height) | `agent-browser --session <s> get box "#<_cssid>"` | layout assertion |
| Computed styles | `agent-browser --session <s> get styles "#<_cssid>"` | layout assertion |
| Custom JS assertion | `agent-browser --session <s> eval --stdin <<'EOF' … EOF` | `browser_evaluate` |
| Console logs | `agent-browser --session <s> console` | `browser_get_console` |
| Uncaught page errors | `agent-browser --session <s> errors` | — |
| Failed network requests | `agent-browser --session <s> network requests --filter "<glob>"` | `browser_get_network` |
| Current URL / HTTP redirect target | `agent-browser --session <s> get url` | — |
| Close (always) | `agent-browser --session <s> close` | `browser_close_session` |

For any JS with quotes/braces use the heredoc form (`eval --stdin`), never inline `eval "..."` — inline parses fragile for anything past a one-token expression.

## Layout assertions are MANDATORY — text checks alone pass on broken renders

`elementor:lint` validates schema; a screenshot proves CSS loaded; but **the assertion that catches collapsed columns and the CSS-custom-property inheritance bug is a computed-style read**. Text-grep verification has passed on completely-collapsed pages — that is the regression this section exists to prevent. Every Phase-6 / Stream-D / Phase-5 run includes these:

```bash
# Per-section width + grid + inherited token, in one machine-readable pass.
agent-browser --session <s> eval --stdin <<'EOF'
const ids = ["<section-cssid>","<left-cssid>","<right-cssid>"]; // _cssids from the §2d Layout map
const vw = window.innerWidth;
JSON.stringify(ids.map(id => {
  const e = document.getElementById(id);
  if (!e) return { id, missing: true };
  const cs = getComputedStyle(e);
  return {
    id,
    width: Math.round(e.getBoundingClientRect().width),
    vw,
    grid: cs.gridTemplateColumns,
    ef_cols: cs.getPropertyValue('--ef-cols').trim(),
    tag: e.tagName,
  };
}));
EOF
```

Gate the orchestrator on the returned JSON:

- **Section never collapses.** Every top-level section wrapper width ≥ `vw − 240`. A section at < 60% of viewport width is a collapse → Fail.
- **2-track sections report two tracks.** A `1fr 2fr` / `2fr 1fr` section's `grid` has exactly two pixel tracks where one is ≥ 1.5× the other (e.g. `778px 389px`). One track, or a near-equal split when the plan declared asymmetry → Fail.
- **Inner wrappers don't inherit the parent grid.** Inner column wrappers report `ef_cols === "1fr"` (or their own explicit override) — NOT the parent's `2fr 1fr`. A `grid-template-columns: 497px 248px` on a wrapper whose data declared `1fr` is the CSS-custom-property inheritance bug (fixed 2026-05-29; assert it never returns).
- **Hero card is semantic.** The hero card's `tag` is `ARTICLE` (CPT single) or `HEADER` (global header). A `DIV` hero → Fail.

`get box` and `get styles` are the single-element shortcuts when you only need one node; `eval --stdin` is the batch form for the whole section list. Use `get count` to assert feed cards rendered (a feed that silently returns zero is otherwise invisible to a screenshot of an empty band).

## The screenshot must be READ, not just captured

Capturing `screenshot --full` is not verification — the subagent's brief MUST instruct it to **read the PNG it saved and describe what it sees**: hero present? sections stacked vertically or side-by-side as planned? sidebar to the right? feed cards filled with data or empty skeletons? A captured-but-unread screenshot is how broken layouts shipped before. The subagent returns the description text alongside the layout-assertion JSON.

## Standard verification checklist (the subagent returns Pass/Fail per item)

```
[ ] HTTP 200 (get url resolved to a real permalink, not a 404/500 body)
[ ] Target selector found within timeout (wait succeeded — no missing-template-render)
[ ] No uncaught page errors (agent-browser errors is empty)
[ ] No JS console errors (agent-browser console — pre-existing warnings OK)
[ ] No failed network requests for the post's CSS (network requests --filter "**/elementor-post-*.css" shows 200, not 404)
[ ] Expected dynamic-tag values rendered (title non-empty, byline shows the type label, counts are numbers)
[ ] No literal "@post(" / "@tags(" / "@author(" / "@site(" leakage in the rendered text (get text body)
[ ] LAYOUT ASSERTIONS (eval --stdin block above) all pass — width, grid tracks, inherited --ef-cols, hero tag
[ ] FULL-PAGE SCREENSHOT saved AND read — subagent describes hero/sections/sidebar/feed
```

Return: Pass/Fail per item, the console + errors output, the screenshot path, the description, AND the layout-assertion JSON object. **Pass** = every item passes on every example post. **Fail** = any item fails on any post → re-open the build, fix, re-run on the SAME URL set.

## Production-page baseline (migration-preservation) — also `agent-browser`

The migration-preservation criterion's content baseline is **what production actually renders to a visitor** — and `agent-browser` renders JS exactly like a visitor's browser, so it resolves Voxel dynamic tags the same way (a strictly better baseline than a static markdown fetch). Replaces the former crawl4ai dependency.

```bash
# Resolve the host: ./wpdev remote:list gives the live host; ?p=<id> 302-redirects to the canonical permalink for any post type.
agent-browser --session prod-<post_id> open "https://<prod_host>/?p=<post_id>"
agent-browser --session prod-<post_id> wait --load networkidle
agent-browser --session prod-<post_id> get text body > /tmp/prod-content-<post_id>-<url_hash>.txt   # rendered, visitor-visible text
# heading structure for information-unit decomposition:
agent-browser --session prod-<post_id> eval --stdin <<'EOF' >> /tmp/prod-content-<post_id>-<url_hash>.txt
"\n--- HEADINGS ---\n" + Array.from(document.querySelectorAll('h1,h2,h3')).map(h => h.tagName + ': ' + h.innerText.trim()).join('\n')
EOF
agent-browser --session prod-<post_id> close
```

The criterion decomposes the saved text into information units (claims / facts / offers / CTAs / features / services / prices / instructions / headings), drops the nav/footer (text before the first `h1` and after the last `h2`), and checks each unit against the §2d blueprint cells + Improvements log. See [`page-planning.md`](../../workflows/page-planning.md) §2e `migration-preservation` criterion and [`migrate.md`](../../workflows/migrate.md) §Iron Law.

## Before/after visual regression (optional, high-value on migrations)

`agent-browser diff screenshot --baseline <img>` compares the current render against a saved baseline. On a migration, screenshot the production page (or the pre-migration local render) as the baseline, then diff after the write — a fast visual confirmation that nothing the Iron Law meant to preserve visibly vanished. Pair it with, never replace, the information-unit check.

## Fallback protocol when the browser is unavailable (Gap closed)

If `agent-browser open` errors (Chrome missing, daemon stuck, sandbox), do **not** silently fall back to `curl` text-scraping and declare Phase 6 passed — that is exactly how broken layouts shipped. Instead, in order:

1. `agent-browser doctor --offline --quick` — read the diagnosis.
2. If it reports a fixable issue, run `agent-browser doctor --fix` once (reinstalls Chrome / purges stale daemons), then retry the `open`.
3. If still unavailable after one `--fix` retry: **STOP and report to the operator.** State plainly: "Browser verification could not run (agent-browser unavailable: `<reason>`). Schema lint passed but layout/render is UNVERIFIED. Run `agent-browser doctor --fix`, or verify the page manually before treating this build as done." Lint-pass + `curl`-text is **not** a passing Phase 6 — say so explicitly and leave the build flagged `render-unverified`.

A `curl` HTML grep is allowed only as a *supplementary* signal alongside an explicit `render-unverified` flag — never as a substitute that lets the run report success.

## Anti-patterns (HARD)

- **Citing `mcp__agent-browser__*`, `mcp__playwright__*`, or `mcp__crawl4ai__*`.** None exist in this skill's tool surface. Use the `agent-browser` CLI via `Bash`.
- **Sharing one session across parallel subagents.** Locks the profile; degrades to text-scraping. One `--session vb-<post_id>-<n>` per subagent, always.
- **Declaring Phase 6 passed on text/`curl` checks alone.** Layout collapse and the `--ef-cols` inheritance bug are invisible to text. Run the `eval --stdin` layout block every time.
- **Capturing a screenshot without reading it.** The description is the verification; the file alone is not.
- **Skipping the fallback report.** A browser that won't launch means `render-unverified`, surfaced to the operator — not a quiet pass.
