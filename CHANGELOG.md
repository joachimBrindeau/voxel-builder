# Changelog

Notable changes to the voxel-builder skill. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Entries older than 1.0.0 live in `git log`; this file is not consumed by any script (`scripts/build_changelog_json.py` scrapes the Voxel theme changelog, not this file).

## [Unreleased]

### Changed

- **wpdev MCP is the only operating surface.** `references/core/command-surface.md`
  now defines the discover → describe → execute contract (`command_search`,
  `command_describe`, `command_execute` only when `transport.allowed: true`),
  the structured tool list, and the CLI-only verbs that run through the device
  shell. Generic Elementor REST, MySQL or WordPress MCP tools, `wp eval` writes
  and direct SQL are documented as non-fallbacks; `wpdev-ops.md` says the same
  for the adapters `wpdev mcp <site>` can declare in a client `.mcp.json`.
- **Raw-eval recipes retired.** Bulk Elementor edits route through
  `elementor:set-value --map` or an `elementor:mutate` loop
  (`elementor-mutation-tools.md`); bulk excerpt/meta applies route through
  `voxel:apply-content` with `--prepare` hashes and `--rollback`
  (`lean-seo-excerpt-meta-descriptions.md`); taxonomy term icons use native
  WP-CLI `term meta` through `wpdev wp` with read-back
  (`icons/material-symbols/lookup-and-repair.md`).
- **Coverage checker reads the generated manifest.** `scripts/check-wpdev-coverage.py`
  reads `cli/src/generated/command-manifest.json`, so only manifest leaves need
  `wpdev-coverage.md` rows; added rows for `voxel:compare`, `voxel:lint-fields`,
  `elementor:fetch-simple-icons`.
- `scripts/migrate-template-content-rows.py` gained `split_field_appearance`
  (mirrors EF migration step 2390); `templates/` re-validated with
  `elementor:validate`.
- `references/README.md` names the committed `ef/widget-schemas.json` mirror
  and prefers the live `elementor:schema` tool; EF schema and generated
  reference tables resynced from the workspace.
- `generate-icon-reference.ts` regenerates only `README.md`, `top-picks.md`,
  `search.tsv` and `manifest.json`; `lookup-and-repair.md` is hand-maintained.

### Added

- `workflows/node-naming.md` and site-port learnings.

### Removed

- `references/core/emcp-wordpress-mcp.md` and all EMCP / generic-MCP guidance.
- `references/icons/material-symbols/metadata.json` (3.1 MB fetch cache, now an
  untracked `.metadata-cache.json`) and the 29 `by-prefix/` shards that
  duplicated `search.tsv`.
- `skills-lock.json` and the dangling `.claude/skills` symlinks (no consumers).
- Hermes-host-specific paths and agent-name wording in references.

## [1.0.0] - 2026-06-15

Masonry / bento layout guidance (`references/ef/masonry.md`, wired into the
layout architect and the `ef/widgets.md` router), `voxel:comparator` and
`elementor:codegen:verify` wired into the references, and full wpdev CLI
coverage with the last `surface-pending` rows closed.
