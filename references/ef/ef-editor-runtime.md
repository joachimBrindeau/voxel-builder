# EF Editor And Frontend Runtime Contract

Use when changing Elementor editor preview, runtime hydration, or widget lifecycle.
Current owners were verified on 2026-07-10.

## One Render Path

`ef_in_editor_preview()` is the preview-context predicate. The REST batch renderer sets
its scoped global with restoration in `finally`; widgets do not invent per-widget preview
detection. Editor and frontend emit the same semantic HTML/classes and Twig context.
The editor canvas uses `/ef/v1/render-batch`. Client state may cache the response but must
not become a second resolver.

## Refresh Triggers

`assets/js/editor/preview/canvas.js` funnels refreshes through `dispatchForView(view)`
from exactly three trigger classes:

1. Elementor view `_afterRender`.
2. `model.get('settings').on('change')` for real-time edits.
3. Startup/command-bus discovery for create, paste, duplicate, and import.

Hash dedupe, a 16 ms pending batch, abort/stale-response protection, and model-destroy
cleanup make these safe. Do not add another debounce or bind the container model instead
of the settings model.

## DOM Replacement Lifecycle

Before replacing preview HTML, `teardownSubtree()` walks the root and descendants, calls
each `__efTeardown`, and clears it. `widget-init.js` owns matching registration. Any
widget attaching global listeners, observers, timers, or provider instances returns one
teardown callback. Hydration then follows the same asset/element-ready path as frontend.
Inline script re-execution is shared fallback infrastructure, not preferred bootstrap.

## Assets And Context

Editor iframe dependencies come from the generated widget asset registry. A small unused
dependency is preferable to a preview that cannot exercise runtime state. Dynamic widgets
need representative post context; an empty standalone preview is not frontend evidence.

## Verification

Run `tests/Browser/preview-parity.spec.ts` and require:

- render-batch fires after a settings-only mutation;
- endpoint matching accepts Elementor's `_locale` query string;
- normalized editor/frontend tag and class sets match;
- rapid edits cannot paint stale responses;
- save/re-render cycles do not accumulate listeners or instances;
- Voxel-context widgets use seeded post data.

LiteSpeed must exclude `wp-login.php` on test sites. Fixture clones resolve their new post
by unique slug with bounded retry; never parse an incidental integer from noisy CLI output.

## DX Gate

Use `wpdev elementor:dx` for the composed quality surface and
`wpdev elementor:dx comments --write` only for conservative high-confidence cleanup.
Use narrow `wpdev quality elementor-framework --tool=<name>` checks while iterating.
Do not run generic comment strippers: schema, migration, cache, security, and cross-runtime
comments are load-bearing context.
