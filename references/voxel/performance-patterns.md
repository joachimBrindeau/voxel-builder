# Voxel / Elementor Performance Patterns

Reusable diagnostics and fix patterns for Voxel + Elementor Framework sites. Use through `workflows/performance.md`; this file is reference detail, not a standalone process.

## Cache and Generated Assets

- LiteSpeed full-page cache can serve stale HTML even when object cache was flushed. Force a real miss before concluding a code/template fix failed.
- Some purge flows delete Elementor generated CSS/meta. Safe order: purge -> regenerate assets -> verify linked CSS URLs return `200 text/css` -> run browser/Lighthouse.
- `post_type => any` can miss Elementor libraries/templates. Use concrete post types when regenerating CSS across templates.
- If Elementor deletes empty generated CSS while templates still enqueue it, create a stable placeholder through the canonical regeneration workflow rather than hand-editing random generated output.

## Attachment URL Lookup N+1

Symptom: repeated `_wp_attached_file` queries or `attachment_url_to_postid()` in widget/loop stacks.

Fix order:

1. Prefer explicit dynamic alt text in the EF image/media props so alt does not require attachment lookup.
2. Build request-local caches or a one-time upload-path map for repeated URL -> attachment ID resolution.
3. Normalize local upload URLs to relative upload paths and strip derivative suffixes such as `-683x1024` before lookup.
4. Keep eager/LCP images eligible for responsive behavior when needed.

Verify duplicate query groups and caller stacks shrink or disappear, and rendered images retain alt/width/height without dynamic-tag leaks.

## Relation Query N+1

For Voxel loops rendering related posts:

1. Compute the loop window IDs.
2. Prime post, relation, and attachment caches for the whole window.
3. Set the relation-cache frontier/global before rendering clones.
4. Restore prior context in `finally` for nested-loop safety.

## JS Layout Thrash on Card/Tag Grids

When TBT and Style/Layout dominate but LCP/CLS are acceptable, inspect JS that mutates DOM and immediately reads layout (`offsetTop`, `getBoundingClientRect`, `offsetWidth`) inside a per-item loop.

Preferred fix: replace linear hide-one/read-one loops with a bounded fitting algorithm (usually binary search plus minimal DOM moves). Preserve overflow order after convergence. Do not defer initial clamp to `requestAnimationFrame` if it causes late layout shifts.

## Map and Third-Party Runtime Loading

For below-fold maps/embeds:

- Keep the local widget runtime light.
- Do not register provider SDKs as hard WP dependencies when LSCache/defer/delay can rewrite ordering.
- Localize provider URLs/config and dynamically append scripts once per provider.
- Gate hydration on viewport proximity AND non-zero layout/visibility.
- Invalidate map size after layout and observe resize changes.

## LCP and Lazyload

- LiteSpeed lazyload may rewrite an eager/high-priority hero unless the final `<img>` has an explicit skip signal such as `data-no-lazy`.
- A buffer-level integration is more robust than per-render-path filters because Elementor/Voxel images do not always pass through core content filters.
- Do not compute the exact LCP image server-side from intrinsic size, first image, or render order. The browser decides LCP from rendered size and viewport position.
- If framework chrome/logo is hardcoded `fetchpriority=high`, demote it so the true hero can own the high-priority slot.

## Measurement

- Compare cache-hit to cache-hit and miss to miss; label mixed comparisons.
- Run more than one warm Lighthouse sample on busy dev hardware.
- Cross-check noisy Lighthouse TBT/Layout numbers with real browser navigation timing.
- For HTML assertions that require full output, use uncapped terminal/curl output rather than tools that truncate large pages.

## Media And LiteSpeed Acceptance Rules

- Backfill local WebP siblings through the media owner and verify `<picture>` output. Treat
  unused-media scans as conservative reports: generated sizes, metadata references, CSS, and
  Voxel/Elementor data can make an apparently unreferenced attachment live.
- Start from the smallest LiteSpeed optimization subset that yields a measured win. Reject UCSS,
  CSS combine, or JS combine unless the tested state set covers logged-in/out, responsive,
  interactive, sparse, and cache-hit behavior.
- CSS combine changes URL resolution. Icon-font declarations must use root-relative or otherwise
  stable URLs so the combined stylesheet cannot resolve fonts relative to a cache directory.
- Mark a confirmed above-fold hero with `data-no-lazy` at the final rendered `<img>` boundary.
  Verify the attribute survives Elementor/Voxel rendering and that lower images remain lazy.
- Compare equivalent cache states and warm both variants before drawing a conclusion. Record the
  exact URL, viewport, authentication state, cache state, and run count with each result.
