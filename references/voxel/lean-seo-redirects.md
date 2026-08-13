# lean-seo redirects — transactional one-hop graph

The `redirects` module is the path-history companion to Lean SEO's permalink engine. Its `{prefix}lean_seo_redirects` table is the only persisted redirect source; no option/meta shadow store exists.

## Repository contract

Every manual, CSV, migration, toggle/delete, and automatic permalink write routes through:

```php
lean_seo_redirects_mutate( array $operations ): array;
```

Operations are `upsert`, `delete`, or `toggle`. The repository normalizes same-host absolute/relative paths, rejects external targets and `/` sources, acquires the stale-recoverable `lean_seo_redirect_write_lock`, requires InnoDB transactions, locks all rows in ID order, applies the complete batch, verifies the stored graph, then commits. On failure it rolls back without flushing cache.

Active exact redirects are a graph. Each source is compacted to its terminal target in the same transaction, including the full reverse ancestor closure. Source status codes (301/302/307/308) and active flags are preserved. Cycles are rejected atomically. Wildcard rows stay opaque because suffix substitution changes their semantics.

After a successful commit the repository flushes `redirects_active_map` once and purges the distinct affected URLs once. Do not add direct redirect-table mutation SQL outside this repository or its versioned upgrade.

## Automatic permalink history

When the module is enabled:

1. `pre_post_update` priority 5 snapshots the old public canonical path for the root and its bounded descendant subtree while the old database state is authoritative.
2. Lean SEO's existing `save_post` priority 20 cascade persists new `_lean_seo_uri` paths.
3. `save_post` priority 100 consumes the snapshot once and submits all changed exact paths as one transactional 301 batch.

Managed hierarchical posts use `_lean_seo_uri`; flat/public posts without it use `get_permalink()`. Autosaves, revisions, drafts/private posts, initial publication, unchanged normalized paths, and metadata-only URI repairs create no redirects. A move back to a historical live path first deletes that live path as a redirect source, preventing `A -> B -> A` cycles.

The canonical content update is never rolled back if redirect persistence fails. Failure logs a bounded machine code and fires `lean_seo_permalink_redirects_failed`; success fires `lean_seo_permalink_redirects_created` with the created root/descendant rows.

## Existing-data upgrade and serving defense

`lean_seo_redirects_data_version=1` owns the one-time graph upgrade. A deterministic `lean_seo_redirect_cycle_report` records existing cyclic components. Acyclic graphs compact to one-hop terminal targets transactionally; data version is stamped only after verification.

The frontend keeps defense in depth: exact redirects resolve through at most 32 active exact edges, preserve the original source code, and emit no redirect for cycles or over-depth data. Exact rows beat longest-prefix wildcard rows. Query strings are preserved.

## Verification

For a redirect batch, prove:

- source returns exactly one allowed 3xx;
- `Location` is same-site and terminal;
- following it returns the expected final response;
- no source is a current live canonical;
- cache/purge occurred once for the committed batch;
- a failed batch left table/cache state unchanged.

`wpdev seo:url-diff` follows redirects and cannot prove the first status or hop count. Use a hop-aware browser/client assertion for redirect lifecycle verification.

## Gotchas

- Non-InnoDB redirect tables fail closed for writes; existing serving remains read-only. Repair the table engine before retrying.
- Do not compute old paths after `save_post`; `_lean_seo_uri` has already changed.
- Flat CPTs may have no URI meta; a meta-only snapshot misses them.
- Direct SQL post writes or APIs that suppress WordPress hooks cannot be observed.
- Wildcard redirects never participate in exact-chain compaction.
