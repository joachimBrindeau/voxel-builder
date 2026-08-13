# Cloudflare Edge Audit And Convergence

Autonomously audit and converge the Cloudflare zone in front of a Voxel/Elementor
site toward a known-good posture: SSL/TLS, DNS integrity, security, caching,
performance, rules/routing, the analytics-proxy Worker, and edge crawlability.
Cloudflare only — never inspect or mutate WordPress, the origin filesystem/DB,
the hosting panel, or application code from this workflow.

## When To Use

- Audit or harden the Cloudflare edge for a Voxel/Elementor site's zone.
- Reconcile the zone to the desired posture (min TLS, DNSSEC, CAA, cache-bypass
  for sitemaps/search, HSTS/security headers, performance toggles).
- Verify the `a.<domain>` analytics-proxy Worker exposes only the tracker and
  collector, and that crawlers are not blocked or served stale content.

## When Not To Use

- WordPress/origin/application changes: those belong to their owning workflow;
  this workflow is Cloudflare-edge only.
- Runtime page performance (LCP/CWV/generated CSS/N+1): use
  [`performance.md`](performance.md).
- lean-seo output (metadata/schema/sitemap generation at the origin): use
  [`settings.md`](settings.md); this workflow only governs edge caching of it.

## Entry Criteria

1. The zone's apex domain is known (derive from the site home URL, strip `www.`).
2. A Cloudflare API token with Zone read/edit + DNS edit is available from
   `VOXEL_CLOUDFLARE_API_TOKEN` or the workspace `.env`. Never print, echo, log,
   or persist the token; pass it only via an `Authorization: Bearer` header read
   from the environment.
3. The account id is available but the zone id is discovered via the API by name.

## Phase 0 — Resolve Zone And Token Scope

**Entry:** Entry criteria are met.

1. Load the token from the environment without emitting its value; verify it can
   read the zone by name (`GET /zones?name=<domain>`) and record the zone id.
2. Probe which surfaces the token can read (settings, DNS, rulesets, DNSSEC,
   workers). Record any surface that returns an auth error as permission-limited
   so later phases separate confirmed findings from unavailable checks.
3. If the token cannot read the zone, stop and report a credential/scope blocker;
   do not guess or fall back to an unrelated token silently.

**Exit:** Zone id resolved, readable-surface map recorded, token value never
disclosed.

## Phase 1 — Read Current State

**Entry:** Zone id is resolved.

1. Read DNS records (proxy status, dangling/duplicate, mail/CAA, TTLs, apex/www,
   `a.<domain>`), DNSSEC status, and all zone settings.
2. Read the rulesets for `http_request_cache_settings`,
   `http_request_dynamic_redirect`, `http_response_headers_transform`, managed
   WAF, and page rules where readable.
3. Probe edge behavior read-only over HTTPS: apex/www redirects, `robots.txt`,
   `sitemap*.xml` (status + `cf-cache-status` + origin `Cache-Control`), a search
   URL, `wp-login.php`/`wp-admin`, and homepage with a logged-in cookie.
4. Pin `a.<domain>` and probe `/a.js`, `/api/send`, and admin paths
   (`/`, `/login`, `/dashboard`, `/api/*`) plus non-idempotent methods to measure
   Worker exposure. Confirm the upstream analytics host.
5. Detect origin exposure: for the proxied apex A record, probe the origin IP
   directly with a spoofed Host; a non-Cloudflare `server` banner answering the
   site host is a WAF/cache-bypass finding.

**Exit:** A current-state snapshot exists for every readable surface, with edge
evidence for cache/crawl/Worker/origin behavior.

## Phase 2 — Diff Against Desired Posture

**Entry:** Current-state snapshot exists.

1. Compare each surface to the desired posture and emit a finding per gap with
   severity, current evidence, impact, and the exact setting/rule to reach it:

| Surface | Desired | Fix locus |
|---|---|---|
| min TLS | `1.2` | `settings/min_tls_version` |
| TLS 1.3 / HTTPS rewrites / Always HTTPS / SSL mode | on / on / on / `strict` | `settings/*` |
| HSTS + security headers | HSTS 1y `includeSubDomains`, nosniff, referrer, frame, permissions | header-transform rule (reuse if present) |
| DNSSEC | enabled + DS at registrar | `dnssec` (DS step is manual) |
| DNS-AID | `_index._agents.<domain>` and `_mcp._agents.<domain>` SVCB/HTTPS records present, pointing to the site host | DNS SVCB/HTTPS records, add-only |
| CAA | `issue`+`issuewild` for every active issuer (edge + origin CAs) | DNS CAA records, add-only |
| Sitemap/search cache | bypass `*sitemap*.xml` and `?s=`/`?p=` | cache-settings ruleset, inserted before any trailing auth bypass |
| Markdown-for-agents | requests with `Accept: text/markdown` must not be served the cached HTML | cache-settings ruleset: configure Cache Rules `vary` for `accept` with normalized `text/html` + `text/markdown`; otherwise bypass when `http.request.headers["accept"][0] contains "text/markdown"` |
| Performance | Brotli, HTTP/3, Early Hints, 0-RTT on | `settings/*` |
| Origin exposure | origin firewalled to Cloudflare IPs (+ AOP) | origin-side, manual/risky |
| Analytics Worker | only `GET /a.js` + `POST/OPTIONS /api/send`; else 404 | Worker source, manual/risky |

2. Mark each finding `fixable` (safe reversible edge/DNS change), `manual`
   (origin/Worker/registrar step outside this API surface), or `risky` (can cause
   downtime). Order findings worst-first by severity.
3. Keep permission-limited surfaces as an explicit unavailable list, never as
   silent passes.

**Exit:** A severity-ordered finding set exists, each tagged fixable/manual/risky
with an exact target expression or setting.

## Phase 3 — Capture Rollback

**Entry:** Finding set exists and at least one fixable change is planned.

1. Before any mutation, record the current value of every setting to be changed,
   the full JSON of any ruleset to be edited, and the existing DNS record set.
2. For ruleset edits, preserve existing rules and ordering; plan the new rule as
   an insert keyed by a stable marker so re-runs are idempotent, and keep any
   "must stay last" bypass rule last.
3. For CAA, plan add-only writes; never delete operator-authored CAA records.

**Exit:** Rollback evidence captured for every planned write; edits are idempotent
and non-destructive by construction.

## Phase 4 — Converge Safe Fixes

**Entry:** Rollback evidence exists.

1. Apply only `fixable` findings. Skip `manual` and `risky` findings; list them
   for operator approval with the exact command/expression to apply later.
2. Apply settings via `PATCH settings/<key>`; DNSSEC via `PATCH dnssec`
   (surface the returned DS record for the registrar); CAA via add-only
   `POST dns_records`; cache-bypass via `PUT` on the cache ruleset with the
   preserved-plus-inserted rule array.
3. Reuse existing rules where a security-header or redirect rule already provides
   the desired effect; do not create duplicate or conflicting rules.
4. Support a dry-run mode that reports the same plan without writing, and only
   apply `risky` fixes when the operator explicitly authorizes them.

**Exit:** Every safe fix is applied idempotently; manual/risky items are staged
with exact remediation and never auto-applied without authorization.

## Phase 5 — Verify And Report

**Entry:** Convergence pass has run (or dry-run completed).

1. Read back each changed setting/record and confirm it equals the desired value.
2. Re-run the edge probes: sitemap/search now `DYNAMIC`, homepage still cacheable,
   apex/www redirects intact, `robots.txt` reachable, Googlebot/Bingbot not
   challenged, TLS negotiates ≥1.2.
3. Report confirmed findings vs unavailable/permission-limited checks separately,
   an ordered remediation plan for staged manual/risky items, and the registrar
   DS record if DNSSEC was enabled.
4. If the token was exposed in any transcript, remind the operator to rotate it.

**Exit:** All applied changes are read-back-verified at the API and edge; staged
items and any credential-rotation reminder are reported.

## Desired-Posture Notes

- **Idempotent by marker.** The sitemap/search cache-bypass rule carries a stable
  description marker; a re-run that finds the marker makes no change.
- **Order matters.** In the cache ruleset, last-match-wins: insert the bypass
  after the HTML-cache rule but before the trailing admin/auth bypass so both
  keep working.
- **`Vary: Accept` requires explicit edge configuration.** Cloudflare supports
  Cache Rules `vary` on every plan, but does not consider ordinary origin `Vary`
  values in caching decisions until a matching Cache Rule enables the behavior.
  For lean-seo, configure `accept` with `action: normalize` and a media-type
  allowlist containing `text/html` and `text/markdown`; set the default action to
  `bypass`. A narrower fallback is to bypass cache when the request `Accept`
  header contains `text/markdown`. Confirm the stale-HTML failure with
  `curl -sI -H 'Accept: text/markdown' https://<host>/` returning
  `content-type: text/html` while the same URL with a cache-busting query string
  returns `text/markdown`. Fix that split in the cache ruleset, never with an
  origin `.htaccess` Accept rewrite. Official references:
  <https://developers.cloudflare.com/cache/concepts/vary/> and
  <https://developers.cloudflare.com/cache/how-to/cache-rules/settings/#vary>.
- **CAA breadth.** Cloudflare Universal SSL rotates its edge CA among Google
  (`pki.goog`), Let's Encrypt, SSL.com, and Sectigo; authorize all active edge
  CAs plus the origin's CA (often Let's Encrypt) for both `issue` and `issuewild`
  to avoid renewal breakage.
- **DNS-AID records.** Publish `_index._agents.<domain>` and `_mcp._agents.<domain>`
  as SVCB or HTTPS records targeting the site host with `alpn="h2,h3" port=443
  mandatory=alpn,port`. Cloudflare's API currently rejects unregistered
  SvcParamKey names (`well-known`, `cap`, `bap`), so records carry connectivity
  only until those keys are registered. Validate with the
  [isitagentready.com scanner](https://isitagentready.com/api/scan): `checks.discoverability.dnsAid.status`
  must be `"pass"` and `dnssecValidated` must be `true`. A passing scan proves
  both the records exist and the zone is DNSSEC-signed.
- **Origin and Worker fixes are manual.** Origin lockdown (firewall to Cloudflare
  ranges + Authenticated Origin Pulls) and the Worker least-privilege allow-list
  live outside this API surface and can cause downtime; always stage, never
  auto-apply.

## Success Criteria

- Zone id discovered by name; token scope mapped; token value never disclosed.
- Every surface audited with severity, evidence, impact, and exact target.
- Only safe reversible edge/DNS changes auto-applied; manual/risky staged.
- All writes captured rollback evidence and are idempotent and non-destructive.
- Applied changes read-back-verified at both the API and the edge.
- Confirmed findings separated from unavailable checks; remediation plan ordered.
