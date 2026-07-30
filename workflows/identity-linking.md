# Identity Linking Workflow

Research, audit, and populate `sameAs` identity URLs for any Voxel CPT. This
workflow owns entity-equivalence decisions and stored repeater values. It does
not author citations or general content, and it hands schema configuration to
[`settings.md`](settings.md) so ownership stays MECE.

Required reference: [`../references/voxel/sameas-identity-links.md`](../references/voxel/sameas-identity-links.md).

## When to Use

- Find or populate Wikipedia, Wikidata, official-profile, or knowledge-graph
  identity links for one record or every published record in a CPT.
- Audit an existing `sameAs` field for ambiguity, broad matches, duplicates, or
  broken canonical URLs.
- Add the canonical URL-only repeater before an identity backfill.

## When NOT to Use

- Supporting references and citations - use [`content-generation.md`](content-generation.md).
- General field copy such as definitions, excerpts, or body content - use
  [`content-generation.md`](content-generation.md).
- Schema-only changes with already-curated field data - use [`settings.md`](settings.md).

## Phase 0 - Scope, Owner, and Rollback

**Entry:** site, CPT, record scope, and intended schema entity are known.

1. Read `wpdev voxel:fields <site> --type <cpt>` and representative
   `wpdev voxel:data <site> --id=<id>` output. Confirm the real repeater key and
   URL subfield. New fields use canonical `sameAs` + required `url` only.
2. Inventory every in-scope published record with stable id, title, permalink,
   entity type/context, current `sameAs`, and available source rows. Capture zero
   result proof when the scope is empty.
3. Save `wpdev schema:get <site> <cpt> --json` and export the database before any
   mutation. Record backup paths and SHA-256.
4. Partition records into bounded 5-10-record research batches. When the host has
   no authorized subagent runtime, record `subagent-runtime-unavailable` and keep
   the same batch/evidence boundaries inline.

**Exit:** field owner, record inventory, current schema, and rollback evidence exist.

## Phase 1 - Discover Candidates

**Entry:** Phase 0 inventory complete.

1. Treat existing citations and source URLs as candidate hints only; never copy
   them automatically into `sameAs`.
2. Search in this order:
   - exact record title plus entity type/context;
   - canonical Wikipedia title and linked Wikidata item;
   - Wikidata exact labels/aliases, including the entity's native language;
   - official website or verified official profile for eligible entity types;
   - other stable knowledge graphs only when equivalence semantics are clear.
3. Search endpoints may include the official Wikimedia APIs and a SearxNG JSON
   endpoint such as `https://search.klarc.eu/search?format=json`; throttle requests,
   use bounded batches, and follow candidates to their canonical destination.
4. Capture candidate URL, redirect destination, entity label/type/description,
   identifiers, and the record context used to disambiguate it.

**Exit:** every record has candidates or explicit no-result evidence.

## Phase 2 - Exact-Equivalence Gate

**Entry:** candidates collected.

1. Apply every acceptance/rejection rule in
   [`sameas-identity-links.md`](../references/voxel/sameas-identity-links.md).
2. For an accepted Wikipedia article, include its canonical URL and corresponding
   Wikidata `Q` URL. Use Wikidata-only when the exact item has no exact article.
3. Normalize HTTPS/canonical URLs; remove tracking, mobile-host, redirect, and
   duplicate variants while preserving intentional Wikipedia + Wikidata pairs.
4. Produce one decision object per record: `accepted` with URL rows and evidence,
   or `skipped` with an empty array and a concrete reason. Broad, narrower,
   related, ambiguous, disambiguation, category, and list matches fail.
5. Gate the batch: record count equals inventory count; no duplicate ids or row
   URLs; every URL passes syntax/canonical checks; every Wikipedia/QID pair agrees.

**Exit:** a complete reviewed decision artifact exists; fill rate is not a pass criterion.

## Phase 3 - Prepare and Apply Voxel Data

**Entry:** Phase 2 gate passes and database backup exists.

1. Build an unprepared `voxel:apply-content` manifest for accepted records only.
   Include current `post_excerpt` because the command contract requires it; write
   `fields.sameAs` as ordered `{ "url": "..." }` rows.
2. Run `wpdev voxel:apply-content <site> --manifest=<file> --prepare`, save the
   strict manifest with `expectedBeforeSha256`, then run the prepared manifest
   without `--yes` for the dry-run preflight.
3. Apply once with `--yes` and `--rollback=<file>`. Never write repeater meta via
   raw SQL, `$wpdb`, or `update_post_meta`.
4. Read every accepted record back. Records with `skipped` decisions remain
   untouched; do not create empty writes merely to mark coverage.

**Exit:** accepted rows read back exactly and a rollback bundle exists.

## Phase 4 - Schema Handoff

**Entry:** stored identity data passes read-back.

1. If schema output is requested, hand the saved config and this resolver patch
   to [`settings.md`](settings.md):
   ```json
   "sameAs": {
     "@each": "voxel:sameAs",
     "@map": "row:url"
   }
   ```
2. The settings route places the property on the entity node representing the
   CPT record, runs `wpdev schema:set`, reads the option back, purges caches, and
   runs `wpdev schema:validate-live`.
3. For a noncanonical field key, replace only `sameAs` in `voxel:sameAs` with the
   actual field key. Do not change the schema property name.

**Exit:** schema is either explicitly out of scope or the settings handoff passes.

## Phase 5 - Complete Live Verification

**Entry:** data apply complete; schema handoff complete when requested.

1. Fetch every in-scope permalink, not a sample. Assert HTTP success and locate
   the schema node representing the record entity.
2. Accepted records must emit a flat `sameAs` array exactly equal to stored row
   order. Skipped/empty records must omit `sameAs`, not emit empty strings or row
   objects. No unresolved `voxel:`, `row:`, or `meta:` token may leak.
3. Report total records, accepted/skipped decisions, provider/link counts, live
   passes/failures, backup, rollback, schema validation, and residual no-match ids.

**Exit:** every record has a decision and every live page matches that decision,
or failed record ids remain explicit without overstating completion.
