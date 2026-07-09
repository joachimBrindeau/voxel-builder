# Route all SEO writing through claude-seo upstream (mandatory)

Any time this skill **authors or refactors reader-facing / SERP-facing copy** on a Voxel
site — a geo-child uniqueness set, a CPT single's `h1`/`hook`/`description`/`faq`/
`conversion-*`, bulk `post_excerpt` / meta descriptions, or content-surgery rewrites — the
research and the writing MUST go through the **claude-seo upstream skills**, not ad-hoc
prose. claude-seo is the maintained SEO source of truth; re-deriving SEO judgement inline
produces weaker, drifting copy and silently skips the anti-doorway / E-E-A-T / meta-length
gates. This reference is the portable recipe; the per-surface gates live in
[`../core/criteria.md`](../core/criteria.md) (`claude-seo-baseline`, `content-methodology`).

## This host cannot run `/claude-seo` — use the Read-fallback

There is **no runnable `/claude-seo` tool** on this host and **no `mcp__claude-seo__*`
server**. Citing one is a phantom-tool bug. The only correct invocation is the
**Read-fallback**: `Read` the relevant `SKILL.md` by absolute path and **follow it inline**.
On a Claude Code host the same skills can be invoked natively; the Read-fallback works
everywhere. **MUST NOT claim a claude-seo skill "ran" if it did not** — say "applied the
claude-seo `<skill>` methodology via Read-fallback".

## Where the skills live

Base (version may advance — glob to resolve, do not hardcode the version):

```bash
ls -d ~/.claude/plugins/cache/*/claude-seo/*/skills/
# → /Users/<you>/.claude/plugins/cache/agricidaniel-claude-seo/claude-seo/<ver>/skills/
```

## Surface → claude-seo skill routing

| You are authoring… | Read + follow (Read-fallback) |
|---|---|
| Local / geolocated page (geo-child), local schema, NAP, doorway/swap-test judgement | `skills/seo-local/SKILL.md` |
| The page copy itself — outline, per-section word counts, keyword placement, meta length, **information gain**, E-E-A-T | `skills/seo-content-brief/SKILL.md` |
| Content-quality / E-E-A-T audit of an existing page | `skills/seo-content/SKILL.md` |
| Single-page on-page audit (title/H1/meta/schema/images) | `skills/seo-page/SKILL.md` |
| JSON-LD structured-data shape/validation | `skills/seo-schema/SKILL.md` |
| Featured/OG/hero image generation | `extensions/banana/skills/seo-image-gen/SKILL.md` |

## The two mandatory moments

### 1. BASELINE before you write (research)
Before authoring a derived/geo page, run the claude-seo **baseline** on the LIVE **source**
page (e.g. the canonical service) via the routed skill (usually `seo-local` + optionally
`seo-page`/`seo-schema`). It is **READ-ONLY** (fetches the URL, writes a `.md` report). Capture
its **gap list** — the areaServed/doorway/uniqueness/title-signal issues your write must close.
Write the report to `/tmp/BASELINE-<slug>.md`. **Gate:** no authoring starts until the baseline
gap list exists (`claude-seo-baseline` criterion).

### 2. METHODOLOGY while you write (authoring)
Author every uniqueness / body / meta field against the claude-seo content rules — concretely:
- **Keyword placement** (`seo-content-brief` §Keyword Density and Placement): primary keyword
  near the front of H1 + title, in the first 100 words, density 0.5–2 % (never stuffed).
- **Meta length** (`seo-content-brief` §Meta Tag Rules): the field that feeds
  `<meta name="description">` (per site, often the Voxel `hook`/`excerpt`) authored to the
  claude-seo range, **bounded by lean-seo's `LEAN_SEO_DESC_LIMIT = 155`** (target 120–152).
- **Information gain** (`seo-content-brief` §Information Gain, non-negotiable): state exactly what
  new value the derived page adds that the source does not — for a geo page this is the genuine
  local specifics (real local programmes/ecosystem), never "more detail".
- **Swap test + ≥500-word / >60 %-unique** location-page bar (`seo-local` §Local On-Page SEO):
  replacing the city name MUST break coherence, or it is a doorway page.
- **E-E-A-T** (`seo-content-brief` §E-E-A-T): named author, cited sources/dates; critical for
  YMYL (finance/health/legal).

**Gate:** every authored field passes the above (`content-methodology` criterion). Factual
accuracy is absolute — **MUST NOT invent programmes or statistics** to manufacture local uniqueness.

## The post-build re-audit is DEFERRED, not skipped
The claude-seo **re-audit as acceptance gate** (re-run `seo-local`/`seo-schema` on the NEW live
URL, compare to baseline) **cannot run until the page exists**. On a live execution, run it in the
verify phase; on a docs-only pass, record it as `DEFERRED (live-only)` — never as "done".

## Related
- [`seo-geolocation-pages.md`](seo-geolocation-pages.md) — geo derivation knowledge (Phase 0 baseline, areaServed, swap test)
- [`lean-seo-excerpt-meta-descriptions.md`](lean-seo-excerpt-meta-descriptions.md) — the description resolver + `LEAN_SEO_DESC_LIMIT`
- [`../curation/content-surgery.md`](../curation/content-surgery.md) — copy-repair surface (also routes writing through claude-seo)
- [`../core/criteria.md`](../core/criteria.md) — the `claude-seo-baseline` + `content-methodology` gated criteria
