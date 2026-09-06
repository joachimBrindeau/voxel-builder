# scripts/

Utility scripts bundled with the voxel-builder skill. These are portable — they
don't depend on any specific agent host — but the icon/action ones do call the
`wpdev` CLI (see the root [`README.md`](../README.md) prerequisites).

| Script | Purpose | Exit |
|---|---|---|
| [`lint.sh`](lint.sh) | Full skill gate: workflow architecture/phase contracts/size ceilings, tool declarations, bounded fan-out language, field-metadata and geo-payload validators, wpdev coverage, EF generated-reference drift, template schemas, portability, and local links/anchors. | `0` = clean, `1` = failures. |
| [`lint-workflow-structure.py`](lint-workflow-structure.py) | Deterministic workflow-skill-design checks for SKILL/workflow/reference/subagent structure. | `0` = compliant, `1` = findings. |
| [`test-skill-contract.py`](test-skill-contract.py) | Validates Hermes frontmatter, description bounds, platform gating, and critical workflow routes. | `0` = compliant, `1` = findings. |
| [`test-lib.sh`](test-lib.sh) | Regression-tests explicit `WPDEV_ROOT` and `WPDEV_SOURCE_ROOT` checkout discovery, including the Python wpdev-coverage gate. | `0` = clean, `1` = regression. |
| [`migrate-template-content-rows.py`](migrate-template-content-rows.py) | Migrates legacy `heading`, `rich_text`, `tag`, `button`, `media`, and `datafield` EF card rows to canonical text rows; `--check` is the no-write gate. | `0` = clean/migrated, `1` = legacy rows remain in check mode. |
| [`check-field-metadata-contract.py`](check-field-metadata-contract.py) | Locks field-metadata machine policy, ownership, specialist envelope, depth-specific writers, and safety gates. | `0` = compliant, `1` = findings. |
| [`validate-field-metadata-run.py`](validate-field-metadata-run.py) | Enforces fresh `run.json` identity, safe single-link artifacts, exact row/object and writer argv schemas, known types, computed bound safety, source-owner read-back, canonical full diffs, complete blueprint/live equality, and exact proved rollback (`--phase prewrite|final`). | `0` = valid, `1` = findings. |
| [`test-field-metadata-run-validator.py`](test-field-metadata-run-validator.py) | Self-checks valid pass/rolled-back fixtures plus schema, type, evidence, writer/argv, diff, symlink, and path-escape rejection cases. | `0` = clean, `1` = regression. |
| [`validate-geo-payload.py`](validate-geo-payload.py) | Validates one or more geo candidate JSON payloads: required fields, copy bounds, collection counts, source/evidence IDs and URLs, maintainable stale-URL/risky-claim policy, sibling city-swap similarity, and input SHA-256s. Emits JSON only. | `0` = valid, `1` = findings. |
| [`test-geo-payload-validator.py`](test-geo-payload-validator.py) | Self-checks valid, malformed, risky/source-invalid, and city-swap payload cases. | `0` = clean, `1` = regression. |
| [`sync-ef-generated-references.py`](sync-ef-generated-references.py) | Syncs `references/ef/widget-schemas.json` and only the `AUTO-GENERATED` widget/action/part table blocks from the WordPress workspace's EF codegen/docs outputs. `--check` is the drift gate. Set `WPDEV_ROOT`, or `EF_GENERATED_ROOT` in the full lint when the generated corpus is staged separately. | `0` = synchronized/current, `1` = drift or missing source. |
| [`verify-install.sh`](verify-install.sh) | Check a target site and runtime prerequisites: `wpdev`, Voxel, lean-seo, Elementor Framework, committed EF assets, `agent-browser`, and `jq`. Run as `./scripts/verify-install.sh <site>` before first use on a site. | `0` = all required prereqs OK. |
| [`action-spec.sh`](action-spec.sh) | Resolve the action-spec for a Voxel `ts_actions` cell (used by the card-actions workflow). | passthrough. |
| [`generate-icon-reference.ts`](generate-icon-reference.ts) | Regenerate the Material Symbols icon reference (`references/icons/material-symbols/`) from Google's metadata. Run from the skill root; set `WPDEV_ROOT` for a non-sibling WordPress checkout. | passthrough. |

## Running lint

```bash
WPDEV_ROOT=/path/to/wordpress bash scripts/lint.sh
```

`WPDEV_ROOT` (or `WPDEV_SOURCE_ROOT`) is required whenever the skill checkout is
not inside the WordPress workspace: the `wpdev` coverage gate and the section-
template schema lint both resolve `cli/src/index.ts` and `wpdev elementor:validate`
from it, and fail closed without it.

The lint is intentionally lean for the portable form — it dropped the plugin-era
checks (plugin.json validation, version-drift stamps, component-count-vs-README)
that don't apply to a `~/.agents/skills/<name>/` skill.
