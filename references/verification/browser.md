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

For loops, assert a meaningful cardinality rather than `> 0`: record the expected count
or bounded minimum in the build manifest, count rendered cards, and verify the first and
last titles. Then assert the first non-loop sibling still contains its heading/copy/form.
EF/Voxel loop context can leak into following siblings and empty otherwise-valid static
cards without producing schema findings or console errors.

For navigation and modal UI, include a visible-fixed-overlay scan. Report large visible
`position: fixed` drawers/dialogs with class, dimensions, and visibility state. Compare an
untouched source or another target page before blaming the changed artifact; shared header
state is a separate defect, not evidence that the port itself opened the drawer.

## The screenshot must be READ, not just captured

Capturing `screenshot --full` is not verification — the subagent's brief MUST instruct it to **read the PNG it saved and describe what it sees**: hero present? sections stacked vertically or side-by-side as planned? sidebar to the right? feed cards filled with data or empty skeletons? A captured-but-unread screenshot is how broken layouts shipped before. The subagent returns the description text alongside the layout-assertion JSON.

Use the live CLI syntax exactly:
`agent-browser --session <s> screenshot --full /tmp/verify.png`. `--full-page` is not an
`agent-browser` flag and can be misread as the output path.

## A timeout is not a defect — separate the harness from the page

Two harness failures look exactly like broken pages and must be falsified before
either is reported:

- **Navigation timeout on a heavy page.** `agent-browser open` gives up on a
  budget that some image-dense pages exceed, printing `Operation timed out`.
  Re-probe with a plain `eval 'document.readyState'` after a longer wait: a page
  that answers `"complete"` with a sane `document.images.length` and no entries
  in `errors` loaded correctly and merely rendered slowly. Confirm against
  `curl -w '%{http_code} %{time_total}'`; a 200 in a fraction of a second means
  the origin is fine and only the browser budget was short.
- **One long async `eval` that never returns.** A single `eval --stdin` that
  scrolls the whole page and then measures can exceed the CLI's own budget and
  return nothing, which is indistinguishable from a page that failed. Split it:
  scroll with several short `eval` calls, then read counts with one-expression
  evals. Distrust any "no result" that a simpler call contradicts.

Reusing one `--session` across pages also fabricates errors: state from an
earlier page (a third-party widget such as reCAPTCHA, for example) surfaces in
the next page's `errors` buffer and gets attributed to a page that never loaded
it. Before believing any console/page error, reproduce it in a fresh session
that visited only that URL.

## Verify against the origin and the edge separately

A site behind a CDN has two answers for every URL, and they disagree for as long
as the edge TTL allows. Origin-side purges — LiteSpeed, object cache, transients,
OPcache, Elementor CSS — do not evict the CDN. `wpdev purge <site> --remote` now
includes a `cloudflare-edge` step, but it no-ops silently when the site has no
zone id or API token, so confirm the label appears in the purge output rather
than assuming the edge was dropped.

When a page still shows content you know you fixed, separate the two before
diagnosing anything else: refetch with a unique query string (`?cb=$RANDOM`) to
read the origin, and compare against the plain URL. Matching results mean the
defect is real; differing results mean you are looking at a stale edge, and
`age:` plus `cf-cache-status:` on the plain response will confirm it. Fixing
data and re-verifying through a cached edge produces a false failure that can
send you rewriting correct code.

## Generated stylesheet verification

After cache purge/rebuild, extract every same-site `/wp-content/litespeed/css/*.css` URL
from the rendered HTML and fetch each with a bounded timeout. Require HTTP 200 and a
non-empty body. Use per-URL timeouts and print one final failure table; do not let a warm
loop spin indefinitely. A missing generated stylesheet makes visual evidence unreliable
even when Elementor schema lint passes.

## Upload parity verification

**Derive the media set from the database, not from rendered pages.** Rendered HTML only
proves the images one page happened to reference; it cannot show what a deploy omitted.
The authoritative set is the attachment closure: every `_wp_attached_file` value plus every
`sizes[*].file` derivative inside `_wp_attachment_metadata`, resolved against the metadata
`file` directory. Compare that closure against a `find`-based manifest of the deploy source
and of production. Any closure entry missing from production is a blocking defect, however
green the pages look.

**The deploy source is the tree the local web server writes to, which is usually not the
git worktree.** When a site runs on a materialized runtime, the web server mounts only that
runtime, so every upload WordPress creates over HTTP lands there while the worktree keeps
only files committed or written by CLI tooling. Neither tree is a superset. Prove which one
serves before trusting it: fetch a file over local HTTP and compare its hash against the
same relative path in each candidate tree, or inspect the server's mount/document root.
Never infer the served root from a vhost config file inside the worktree — a materialized
runtime has its own copy of that config, and the worktree copy is inert.

Converge the trees before deploying: back up the files unique to each, copy them into the
tree that serves, then re-derive the closure and require zero missing entries. Where the
same relative path holds different bytes in each tree, resolve by ownership — query which
attachment ID the live post actually references (`_thumbnail_id`, post content, Voxel
fields) and keep that file; the other is an orphan from a superseded import.

After sync, re-inventory production and require: zero closure entries missing, and zero
size mismatches against the served tree. Then verify over HTTPS. Note that a `HEAD` request
is not a substitute for `GET` — some CDN-injected assets (for example Cloudflare's
`/cdn-cgi/scripts/.../email-decode.min.js`) reject `HEAD` with a 404 while serving `GET`
normally, so confirm any static-asset 404 with a `GET` and a `Referer` header before
treating it as a defect.

In the browser, scroll lazy-loaded images into view and wait before testing them. Require
`img.complete === true && img.naturalWidth > 0`; visible alt text with `naturalWidth === 0`
is a broken-image failure even when the page itself returns HTTP 200 and has no console error.

## Standard verification checklist (the subagent returns Pass/Fail per item)

```
[ ] HTTP 200 (get url resolved to a real permalink, not a 404/500 body)
[ ] Target selector found within timeout (wait succeeded — no missing-template-render)
[ ] No uncaught page errors (agent-browser errors is empty)
[ ] No JS console errors (agent-browser console — pre-existing warnings OK)
[ ] No failed network requests for the post's CSS (network requests --filter "**/elementor-post-*.css" shows 200, not 404)
[ ] Expected dynamic-tag values rendered (title non-empty, the author-line subtitle shows the type label, counts are numbers)
[ ] Expected feed/card cardinality rendered; first and last expected titles are present
[ ] First sibling after every loop still renders its heading/copy/form/CTA
[ ] No literal "@post(" / "@tags(" / "@author(" / "@site(" leakage in the rendered text (get text body)
[ ] Same-site generated LiteSpeed CSS URLs return HTTP 200 with non-empty bodies
[ ] Edge invalidated after the origin was already correct (purge output lists `cloudflare-edge`; plain-URL `age:` reset), and any surviving defect reproduced against a cache-busted origin fetch
[ ] DB attachment closure (`_wp_attached_file` + metadata `sizes`) has zero entries missing from production, and the deploy source is the tree proven to serve local HTTP
[ ] Lazy-loaded images were scrolled into view; every loaded image has `complete === true` and `naturalWidth > 0`
[ ] No unexpected visible fixed drawer/dialog; shared overlays compared against untouched source
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
