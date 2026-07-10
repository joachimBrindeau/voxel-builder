# lean-seo Source Engineering

Use for source-level lean-seo maintenance, portability, security, and settings
standardization. Runtime configuration remains in dedicated output references.

## Freshness First

Inspect current module registries, settings substrate, hooks, and tests before applying an
old recipe. Preserve storage/read contracts unless a migration and read-back proof cover
every existing site.

## Portable Feature Pattern

1. Replace site identifiers with a documented filter or stored setting.
2. Default optional site-specific features to empty/off.
3. Emit nothing when required identifiers are absent; partial schema/output is failure.
4. Keep site values in a dedicated MU-plugin or explicit site settings.
5. Seed the origin site idempotently and preserve deletion choices.
6. Neutralize locale-shaped defaults or translate them.

Never assume activation migrations rerun on an existing site. Read back the exact target
option/filter after deployment.

## Settings Standardization

Audit `lean_seo_*` options and classify first-class settings, raw keys the plugin already
reads, and intentional escape hatches. Promote only the raw supported keys. Keep the
storage shape, add UI over the existing contract, migrate representation metadata only
when needed, and use one-shot flags so upgrades do not resurrect deleted presets.

## Translation Boundaries

A pre-`init` registry keeps plain strings. Static gettext extraction requires literal
`__( 'Label', 'lean-seo' )` calls. Duplication between a bootstrap registry and post-init
literal label map is load-bearing; do not replace literal gettext calls with variables.

In symlinked workspace plugins, load translations at `init` with `load_textdomain()` and
an explicit absolute `.mo` path from the plugin root. Do not depend on
`load_plugin_textdomain()` reconstructing a symlink-relative basename.

## Security Boundaries

- Treat DB settings and server variables as untrusted at output.
- Validate CSS colors with an allowlist before XSL/CSS emission.
- Parse query strings and rebuild with `http_build_query()` before redirects.
- Extract `REQUEST_URI` path with `wp_parse_url(..., PHP_URL_PATH)`.
- Use `wp_safe_redirect()` and context-appropriate escaping.
- Respect stored toggles; never replace them with unconditional filters.
- Bound public queries and cache bot-facing sitemap/markdown/llms endpoints.

## Request-Lifecycle Performance

Use lazy functions instead of parse-time constants for mutable options. Memoize pure,
stable-within-request helpers with local statics. Invalidate persistent caches on owning
write hooks. Extract duplicated algorithms at a shared function boundary when callers
require identical semantics.

## Verification

1. Audit affected options before and after.
2. Exercise empty/off defaults on a second site.
3. Verify translations with `is_textdomain_loaded()` and one known literal.
4. Test malicious stored colors, CRLF input, and URI query/fragment cases.
5. Confirm public query caps and cache invalidation.
6. Run lean-seo quality/security tests plus live HTML/schema/redirect checks.
