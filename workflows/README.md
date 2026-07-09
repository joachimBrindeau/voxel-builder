# workflows/ — phased processes to follow

The skill's **step-by-step processes** live here, separate from the look-it-up [`../references/`](../references/README.md) knowledge. Each file is a numbered, gated pipeline with entry/exit criteria; the router is [`../SKILL.md`](../SKILL.md).

| File | Process | Phases |
|---|---|---|
| [`build.md`](build.md) | Build / modify a template's `_elementor_data` (entry point for the build + migration commands) | Phase 0 → 6 (preflight → gather → plan → fan-out → assemble → write → verify) |
| [`page-planning.md`](page-planning.md) | The mandatory planning sub-pipeline for any non-trivial build/migration | §2a → §2g (inventory → SSOT → archetypes → blueprints → adversarial review → reconciliation → computed gate) |
| [`migrate.md`](migrate.md) | Legacy Elementor V3 → EF V4 atomic migration | Phase 0 → 5 |
| [`cpt-lifecycle.md`](cpt-lifecycle.md) | Full Voxel CPT registration → verification | Phase 0 → 7 |
| [`archive-search-pages.md`](archive-search-pages.md) | Build / fix searchable Voxel archive pages under the existing search-root URL pattern | Phase 0 → 3 |
| [`geolocation.md`](geolocation.md) | Derive a canonical Voxel service (`exp`) into a geolocated mirror parented under a `geo` city post | Phase 0 → 4 (preflight/baseline → plan → build geo-child → SEO wiring → verify) |
| [`audit.md`](audit.md) | Top-down page→section→widget audit + bottom-up fix loop | Streams A–D + Pass 1–3 |
| [`briefs.md`](../references/audit/briefs.md) | Copy-pasteable subagent briefs for the audit/plan fan-out | — (templates) |
| [`browser.md`](../references/verification/browser.md) | The `agent-browser` CLI render-verification protocol | Phase 6 / audit Stream D |
| [`behavior-contract.md`](../references/verification/behavior-contract.md) | Pre-mutation gate for existing-data edits (Behavior Contract + DOM-text baseline) | gate |
| [`card-actions.md`](card-actions.md) | Define / fix an ef-card `ts_actions` (or ef-navbar `cta_ts_actions`) action strip, SSOT-validated | Phase 0 → 5 (preflight → choose → resolve cells → build envelope → apply → verify) |
| [`settings.md`](settings.md) | Configure a lean-seo SEO surface (metadata / schema / markdown / crawl+permalinks) for a Voxel CPT, agnostically; plus adjacent-module pointers (redirects / code / media / maintenance / purge) | Routing: Phase 0 preflight → Route M/S/K/C → Phase V verify |
| [`image-generation.md`](image-generation.md) | Generate, QA, optimize, upload, attach, and verify unique SEO images for Voxel/Elementor WordPress content while delegating global model/tool logic to `seo-image-gen` | Phase 0 → 7 (backend smoke-test → discover → concept → prompts → generate/QA → optimize → attach → verify) |

## Adding a workflow

A new file here must be a **numbered, phased process** with explicit entry and exit criteria (see [the skill-design standard](https://docs.claude.com/) — number every phase, define "done"). Pure knowledge (schemas, field configs, tag syntax) belongs in [`../references/`](../references/README.md) instead. Cross-links are relative; `scripts/lint.sh` verifies them.
