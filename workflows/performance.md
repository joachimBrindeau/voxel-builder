# Voxel / Elementor Performance Workflow

Improve performance in a Voxel + Elementor Framework WordPress workspace using source-level fixes and browser/server verification. This workflow covers frontend runtime payload, generated Elementor assets, cache/purge ordering, backend query patterns, and Core Web Vitals loops.

## Entry Criteria

- Target site and URL/path are known.
- The performance symptom is measurable: slow load, Lighthouse/CWV finding, asset bloat, query count/time, generated CSS/JS issue, map/embed delay, or stale cache behavior.
- The task permits code/config/template changes.

## Phase 1 — Baseline

Entry: target URL exists.

1. Capture same-state request timing: status, TTFB, total time, HTML size, cache headers.
2. Capture browser evidence when relevant: Lighthouse JSON, console/network resource inventory, LCP/CLS/TBT/main-thread breakdown, visual UX issue.
3. Capture backend evidence when relevant: project perf command, query count/time, duplicate query groups, PHP time.
4. Record cache state (`x-litespeed-cache`, generated CSS presence, object-cache status) so before/after comparisons use the same state.

Exit: bottleneck has reproducible evidence and a baseline artifact or notes.

## Phase 2 — Classify Bottleneck

Entry: baseline exists.

| Class | Examples | Preferred Fix Layer |
|---|---|---|
| Cache/generated asset ordering | stale HTML, CSS 404/MIME text/html after purge | workflow/config first, then generated asset regeneration |
| Frontend asset payload | icon fonts, global CSS/JS, third-party SDKs | shared plugin/framework enqueue/runtime |
| LCP/image loading | hero lazyloaded, multiple high-priority images, missing dimensions | image renderer or LiteSpeed buffer integration |
| CLS/hydration mismatch | carousel/pager/tabs rewrite DOM after paint | server-render final shell; JS reuses shell |
| JS layout thrash | card/tag grids with high TBT + Style/Layout | shared JS algorithm fix |
| Map/embed runtime | below-fold map SDK loaded early or fails after LSCache defer | dynamic provider script loader + renderability gate |
| Duplicate DB queries | attachment URL lookup, Voxel relation N+1 | request-local cache/batch priming/shared resolver |
| Backend TTFB | slow queries, remote HTTP, autoload/options | backend profiling and plugin/source fix |

Exit: one bottleneck class is selected for the next repair loop.

## Phase 3 — Repair Durable Source

Entry: bottleneck class selected.

1. Prefer shared plugin/framework fixes over page-specific edits.
2. For generated assets, fix source/config and regenerate; do not hand-edit generated output except for temporary live recovery.
3. For LiteSpeed interactions, distinguish native LSCache configuration from things framework code must own: DOM stability, dynamic SDK gating, query patterns, explicit skip signals.
4. For Elementor/EF runtime fixes, read live widget/source shape before patching assumptions into code.
5. For backend query fixes, prove the exact caller stack and add request-local caching or batch priming at the narrow shared resolver.

Exit: one source-level fix is applied and scoped to the selected bottleneck.

## Phase 4 — Purge, Regenerate, Warm

Entry: source change is applied.

1. Purge the correct cache layer. `wpdev purge` may not clear LiteSpeed full-page cache; use LiteSpeed purge when present.
2. Regenerate Elementor CSS/assets if purge or code changes require it.
3. Confirm linked generated CSS/JS URLs return the right status and MIME type before browser verification.
4. Warm once after a real miss when comparing cached HTML behavior.

Exit: the page is served from the intended cache state and generated assets are valid.

## Phase 5 — Verify Delta

Entry: fresh render state is available.

1. Re-run the exact baseline probes.
2. Compare only same-state measurements; do not mix cache-hit and cache-miss numbers without labeling them.
3. For frontend changes, verify browser console/network and visible behavior.
4. For query fixes, verify duplicate query groups/caller stacks shrink or disappear.
5. If canonical test suites are blocked by unrelated environment issues, create a temporary `hermes-verify-*` ad-hoc assertion and delete it after running. Report it as ad-hoc verification, not suite green.

Exit: the performance change is validated, blocked with evidence, or queued for another focused loop.

## High-Impact Patterns

- **Generated CSS after purge:** purge -> regenerate -> verify `200 text/css`; do not run Lighthouse against transient 404s.
- **Attachment URL lookup N+1:** build a request-local upload-path map, normalize derivative filenames, and avoid repeated `attachment_url_to_postid()` when explicit alt/dimensions are already available.
- **Voxel relation N+1:** compute the loop window, prime relation/post/attachment caches, set relation frontier before rendering clones, restore state in `finally`.
- **Map/embed SDKs:** do not hard-depend on Leaflet/Google Maps in the local widget runtime; dynamically load provider scripts when the widget is near viewport and has non-zero layout.
- **Card/tag layout thrash:** avoid hide-one/read-layout loops; use a bounded fitting algorithm and preserve overflow order.
- **LCP lazyload under LiteSpeed:** LiteSpeed can ignore `loading=eager` and `fetchpriority=high`; add an explicit skip signal (`data-no-lazy`) before LiteSpeed lazyload runs, keyed to WP/core or author-explicit LCP hints.
- **Competing high-priority images:** only the true LCP should be high priority; demote site chrome/logo fetch priority where framework code hardcodes it.

## Measurement Rules

- Run multiple warm Lighthouse samples before trusting TBT/Style/Layout deltas on a loaded dev box.
- Cross-check headless results with real browser navigation timing when possible.
- Do not debug PHP hooks against stale full-page cached HTML.
- Do not compute the exact LCP image server-side from intrinsic size or render order; rendered viewport size is browser knowledge.
