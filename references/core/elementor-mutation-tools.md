# Elementor Existing-Data Mutation Tools


> Migrating a page OFF legacy Elementor V3 (containers + `heading`/`text-editor`/`button`/`counter`/`nested-accordion`) onto EF V4 atomics is its own workflow — see [`migrate.md`](../../workflows/migrate.md) for the Iron Law (drop structure/styling aggressively, preserve data verbatim), the `migrate:main`/`migrate:containers` structural pass, and the parallel fan-out consolidation. That per-section consolidation fan-out follows the same dispatch shape as Phase 3 build — **a Workflow `parallel()` step when opted into multi-agent orchestration (with per-section isolation if writing files), inline single-message dispatch otherwise** — per [`parallel-dispatch.md`](./parallel-dispatch.md) §Fan-out → Workflow expression map. The notes below cover smaller in-place edits.

Same pipeline, with one extra Phase 0:

**Phase 0 — Capture current state.**
```bash
wpdev elementor:dump <site> all --post <id> --json > /tmp/before-<id>.json
wpdev elementor:tree <site> <id> > /tmp/before-tree-<id>.txt
```

Then proceed through Phases 1-5. The captured before-state is the rollback target.

**Mandatory gate — Behavior Contract + DOM-text baseline.** Before mutating existing data, the command-host authors a Behavior Contract triple (what must not change / allowed structural delta / forbidden semantic delta) and captures a DOM-text baseline of the affected widgets' data-bound props, per [`behavior-contract.md`](../verification/behavior-contract.md). The post-mutation re-audit diffs the new DOM-text against that baseline — a changed data-bound value the contract pinned is a Forbidden Semantic Delta violation → roll back. No baseline → no fix. The contract is authored by the command-host (not the fixer) and the re-audit is the reviewer; that author≠repairer≠reviewer separation is what makes "this is a refactor, not a behaviour change" verifiable rather than asserted. Greenfield builds (no prior data) skip this gate.

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
| Fix unicode corruption (`u00e9` leaks) | `wpdev db:encoding <site> --fix -y` | `elementor:fix:unicode` was retired in `c939f922f`; mojibake repair now lives in `db:encoding`, which works at the DB layer and so covers post meta beyond `_elementor_data`. **Site-wide only** — no `--post` filter exists. Snapshot every Elementor post first via `wpdev elementor:revisions:prune <site>` (no `--post`); run once per fix loop. |

**Hard rule: never use `wp eval '...'` heredoc for `_elementor_data` mutations.** Backslash-escape and PHP-namespace separators inside heredocs parse-fail in shells and have cost multiple sessions a debug round. Always:

1. Write the patcher to `/tmp/<task>-mutator.php` first (regular `Write` tool). The script reads `_elementor_data`, `json_decode`s it, walks the tree, mutates by widget id, re-encodes with `JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES`, and writes back via `update_post_meta`. Use the `EF\Envelope::responsive_string(...)` / `::image(...)` / `::vx_visibility(...)` factories for any `$$type` envelope (see [`actions.md`](../ef/actions.md) §Loopable action-rows) — hand-authored envelopes with missing inner `$$type` markers render as absent and lint can't always catch a partial shape.
2. Run it through the atomic loop: `wpdev elementor:mutate <site> <id> /tmp/<task>-mutator.php` — never raw `wp eval-file` for a single-post `_elementor_data` change, because that skips the CSS-regen + cache-purge tail and the page renders stale. Add `--fetch "https://<site>.<tld>/<slug>/"` to surface a 4xx/5xx the lint can't see.
3. Then run Phase 6 browser verification ([`browser.md`](../verification/browser.md)).

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

$json = wp_json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
// WordPress unslashes only the new value; prev_value is compared RAW.
update_post_meta($post_id, '_elementor_data', wp_slash($json), $raw);
if (get_post_meta($post_id, '_elementor_data', true) !== $json) { exit("write conflict\n"); }
echo "patched\n";
```

**Pass `prev_value` raw, never `wp_slash($raw)`.** The compare-and-set arm of
`update_post_meta` matches `prev_value` against the stored value verbatim, while it
unslashes only the new value. Slashing both makes every compare miss, so the write is
skipped and the call still returns without an error — a silent no-op that looks like
success until a read-back proves otherwise. Always assert the read-back equals the
encoded JSON before reporting a post as written.

Always `JSON_UNESCAPED_UNICODE` — French accents (`é`, `è`, `ç`) round-trip through WP slashing layers cleanly only with this flag (otherwise `é` can lose its backslash and end up as literal `u00e9`).

### Changing an EF schema default is a data mutation

The EF save normalizer prunes every stored cell equal to its schema default, so a
default is not a cosmetic fallback — it is the persisted value for every author who
accepted it. Flipping `default` in `schemas/**/*.schema.json` therefore silently
rewrites what already-saved documents mean, and no test catches it because fixtures
and unit suites are regenerated from the new default.

The reference failure: the shared media Part's `default_type` moved from `image` /
`icon` to the None sentinel `''`. Every slot authored on the old default had been
stored WITHOUT its `{prefix}_type` cell, so those slots resolved to no handler and
their media vanished sitewide — image, icon, inline heading media alike.

When a default changes, before merging:

1. Ask whether the old default was *persisted by absence*. If the normalizer prunes
   that cell, the answer is yes and existing data now reads differently.
2. Quantify with a read-only `wp eval-file` scan over every `_elementor_data` row —
   count rows whose cell is absent/empty while the old default's own source cell
   still carries content. Cover pages, `elementor_library` templates, and every post
   status, plus nested repeater `children`.
3. Ship a `migrations/steps/<NNN>-*.php` step in the SAME change that writes the old
   default back, gated on that source cell still having content so a genuinely empty
   slot keeps the new default. See
   `1336-content-row-media-type-none-recovery.php`.
4. Verify by re-running the scan (expect zero) and by rendering an affected URL —
   stored equality alone does not prove the handler resolves.
