# Content Generation Workflow

Generate reader-facing / SERP-facing field content for one or many Voxel CPT
records — `definition`, `h1`, `hook`, `post_excerpt`, `sources`, `faq`,
or a body/`description` field — from source evidence, authored to the **field-scoped
spec** and applied through the sanctioned gated write path. This workflow produces
content values; it never invents schema and never writes raw meta/SQL.

## When to Use

- A CPT single's field is empty, thin, or off-spec across one or many records
  (e.g. glossary `definition`/`hook`/`excerpt`/`sources` backfill).
- The user asks to write, backfill, regenerate, or improve field content and to
  apply it to the site.
- Bulk generation is needed and must stay per-record verifiable.

## When NOT to Use

- Reviewing/auditing existing content without regenerating it - use
  [`content-review.md`](content-review.md).
- Elementor `_elementor_data` widget/layout content - use [`build.md`](build.md).
- Schema-only / meta-resolver config with no copy authored - use
  [`settings.md`](settings.md).
- Entity-equivalence research or `sameAs` population - use
  [`identity-linking.md`](identity-linking.md).

## Entry Criteria

1. Site, target CPT, target field(s), and record set (one id, a query, or "all
   published") are known.
2. `wpdev voxel:fields` + `wpdev voxel:data` can read the CPT and a real sample.
3. The 9router endpoint is reachable (`curl $NINEROUTER_URL/api/health`) or an
   equivalent authoring model is available.

If the field set or record scope is ambiguous, ask one focused question before Phase 0.

## Phase 0 - Resolve Field Scope, Owner, and Source Packet

**Entry:** Entry criteria met.

**Actions:**

1. Read the field-scoped authoring reference for every target field from the
   routing table below. That reference owns the spec (length band, structure,
   grammatical form, schema mapping); do not re-derive it.
2. Resolve each field's write owner via `wpdev voxel:fields`. `voxel:set-field`
   writes Voxel fields/meta and routes Voxel `title` → `post_title` and
   `description` → `post_content`; it also accepts explicit core keys
   `post_title`/`post_content`/`post_excerpt`. `voxel:data` exposes those core
   values under `core`. Keep `wpdev wp <site> post update` only as fallback or
   explicit-core-key path. Record repeater subfield shapes and `maxlength`.
   For a definitional CPT, also load and enforce the identity contract from
   `seo-defined-terms.md`: exact-term `post_title`, slugified-term `post_name`, and
   individually LLM-authored term-first `h1` (maximum 70 characters).
3. Before web research or `needs-source`, resolve cross-record business/location/person/service
   claims across all relevant published CPTs: live `voxel:fields`, Voxel-aware corpus reads,
   selected `./wpdev voxel:data <site> --id=<id>` confirmation, aliases, and cycle-safe
   inbound/outbound relations through two hops. Emit `dataset_resolution_state: PASS|BLOCKED`,
   scope/counts/filters/pagination/zero-result proof, and `D##` locator/SHA-256/relation-path/
   classification/approval/redacted-excerpt/confidence rows. Unknown is CONFIDENTIAL; redact
   before external models. Author only from PUBLIC or approved INTERNAL_PUBLISHABLE evidence.
   Self-contained transformations may record `dataset_resolution_state: NOT_APPLICABLE` with reason.
4. Build per-record source packet (`/tmp/gen-<cpt>-<id>.json`) from resolved evidence; capture
   existing values with `wpdev voxel:data --id=<id>` as rollback evidence.

**Field → scoped reference routing:**

| Target field | Field-scoped reference |
|---|---|
| `definition` (answer block) + `h1` + `hook` + `sources` on a definitional CPT | [`../references/voxel/seo-defined-terms.md`](../references/voxel/seo-defined-terms.md) |
| `faq` repeater | [`../references/voxel/faq-authoring.md`](../references/voxel/faq-authoring.md) |
| `post_excerpt` / meta-description field (incl. `hook` used as meta) | [`../references/voxel/lean-seo-excerpt-meta-descriptions.md`](../references/voxel/lean-seo-excerpt-meta-descriptions.md) |
| any reader/SERP copy (methodology + gates) | [`../references/voxel/claude-seo-authoring.md`](../references/voxel/claude-seo-authoring.md) |
| bulk mechanics (9router concurrent generate + validate-retry) | [`../references/voxel/lean-seo-ninerouter-concurrent-generation.md`](../references/voxel/lean-seo-ninerouter-concurrent-generation.md) |

**Exit:** every target field has scoped spec, write owner, dataset gate, and source packet.

## Phase 1 - Load Standards and Methodology

**Entry:** Phase 0 packets exist.

**Actions:**

1. Apply [`../references/voxel/claude-seo-authoring.md`](../references/voxel/claude-seo-authoring.md):
   resolve the upstream SEO capability (or read-fallback its methodology; record
   which). Reader/SERP copy never ships as ad-hoc prose.
2. Load the field-scoped length/structure/grammar gates from the Phase 0
   reference into an explicit per-field acceptance spec used verbatim by both the
   author prompt and the Phase 3 QA gate.
3. Treat `docs/seo-checklist.db` (glossary/definition branch) as the checklist
   source for definitional fields.

**Exit:** a written per-field acceptance spec exists (length band, opening form,
prose rules, source/citation rule, forbidden transforms).

## Phase 2 - Partition and Dispatch Authors

**Entry:** acceptance spec ready.

**Actions:**

1. Enumerate leaves as `entity:<cpt>:<id>` and partition 5-10 homogeneous records
   per batch, waves ≤ host concurrency cap (see
   [`../references/core/parallel-dispatch.md`](../references/core/parallel-dispatch.md)).
2. Dispatch the [`../references/subagents/voxel-content-author.md`](../references/subagents/voxel-content-author.md)
   brief (build mode) for each batch, passing the source packet, the per-field
   acceptance spec, allowed research (e.g. a verifiable Wikipedia/Wikidata fetch
   for `sources`), and the return schema. If no subagent runtime exists, run the
   same brief inline per the concurrent-generation mechanics reference, recording
   `subagent-runtime-unavailable`.
3. Require one envelope per record+field: `value`, `evidence`, `word_count`/`char_count`,
   `sources` (verified only), `confidence` (`supported` / `needs-source` / `reject`).
   A subagent never writes to WordPress.

**Exit:** candidate values with evidence exist for every record; no author wrote to the site.

## Phase 3 - QA Gate

**Entry:** candidate values returned.

**Actions:**

1. Validate every value against the Phase 1 acceptance spec: length band,
   term-as-subject / answer-first form, neutral prose, no truncation markers, no
   leaked tags/tokens, meta fields under the resolver limit.
2. Reject any value that is a mechanical transform of a sibling field, any
    fabricated or unverifiable `sources` row (drop it; empty beats invented), and
    any `needs-source`/`reject` envelope. Regenerate rejected leaves once. Every review
    verdict records candidate input SHA-256; reject it if current SHA differs. Fresh review
    session follows substantive rewrite unless exact SHA proves unchanged.

3. Confirm unrelated fields are untouched in the candidate set (the author only
   returned the targeted fields).

**Exit:** every candidate is `supported`, on-spec, and safe to apply.

## Phase 4 - Apply Through the Gated Write Path

**Entry:** Phase 3 passed.

**Actions:**

1. **Preferred: manifest-driven batch via `wpdev voxel:apply-content`** for many
   candidate records. Build a JSON manifest — one row per record: `id`, the
   record's current `expectedBeforeSha256` (from a `preflight`/`read` pass, so a
   concurrent edit aborts the apply), `post_excerpt`, and `fields` (Voxel field/meta
   keys plus the `title`/`description` aliases the command routes to
   `post_title`/`post_content`). Dry-run first (omit `--yes`) to preflight every
   row's SHA and surface mismatches before any write; only then re-run with `--yes`
   and a `--rollback <path>` bundle. The command captures pre-write originals into
   the rollback file, applies, and on ANY row failure auto-restores every row from
   that bundle — inspect `Unrecovered IDs` in the failure output if restore itself
   fails partially. Candidate hashes are computed from Voxel's canonical sanitized
   values, including repeater rows where empty optional subfields and unchecked
   switchers are omitted on storage; do not pre-normalize those rows with a parallel
   serializer. It performs its own per-record read-back and reindex internally
   and needs exactly one purge after (`wpdev rebuild <site> --only purge`) covering
   the whole batch, not a per-row purge cascade:
   ```bash
   wpdev voxel:apply-content <site> --manifest /tmp/manifest.json --rollback /tmp/rollback.json           # dry run
   wpdev voxel:apply-content <site> --manifest /tmp/manifest.json --rollback /tmp/rollback.json --yes      # apply
   ```
2. **Single-field path: `wpdev voxel:set-field`.** For a one-off record/field write,
   `voxel:set-field` remains the direct path — it writes Voxel fields/meta and routes
   the `title`/`description` aliases to `post_title`/`post_content` itself (no
   silent no-op, no separate `post update` call needed for aliases). Use
   `wpdev wp <site> post update` only as fallback, or when writing an explicit core
   key (`post_title`/`post_content`/`post_excerpt`) outside the alias path. Never
   `wp eval`/`update_post_meta`/SQL for entity data (core rule 9).
3. Enforce the per-record gate: `wpdev voxel:data --id=<id>` before/after proves the
   targeted key changed to the generated value and unrelated keys are byte-identical;
   skip rows already equal; report `APPLIED/ALREADY/FAILED`. (`voxel:apply-content`
   does this internally per row; for `voxel:set-field` calls, capture it yourself.)
4. Reindex mutated records (`voxel:apply-content` reindexes per row automatically;
   `voxel:set-field` reindexes by default), then run ONE cache purge at the end
   (`wpdev rebuild <site> --only purge`), not a per-row purge cascade.

**Exit:** every applied record passed the before/after gate; failures are listed
for re-run (the apply is idempotent).

## Phase 5 - Verify

**Entry:** apply complete.

**Actions:**

1. Re-read a representative sample (complete + sparse + typical) from the DB and
   assert stored value equals generated value; report fill counts per field and
   length min/median/max within band.
2. Verify the downstream surface: the meta-description resolver, `DefinedTerm`
   JSON-LD, TermIndex/tooltip, or card/loop render actually serves the new copy
   (curl/browser, not DB alone).
   - When a record still carries an intentional editorial noindex flag, first
     confirm the rendered robots directive and confirm that Lean SEO emits no
     JSON-LD for that exact URL. Treat the absence as the expected noindex state,
     not as a schema defect. Record schema verification as deferred until the
     guarded release removes noindex.
   - Do not use a post-type-wide `schema:validate-live` PASS as proof for a
     touched record: that command resolves one representative published URL and
     may select a different, indexable record. Capture the sampled URL, then
     inspect each touched canonical URL directly after noindex removal.
   - After the one required purge, compare the plain canonical URL with a unique
     cache-busted fetch. They must serve the same final content and metadata;
     differing responses are unresolved cache state, not a completed verify.
3. Report per-field coverage (`filled/total`), off-spec count (target 0), and any
   records left `needs-source` for human sourcing.

**Exit:** target fields are on-spec and rendered; residual `needs-source` records
are explicitly reported, not silently filled.
