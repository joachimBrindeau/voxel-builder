# scripts/

Utility scripts bundled with the voxel-builder skill. These are portable — they
don't depend on any specific agent host — but the icon/action ones do call the
`wpdev` CLI (see the root [`README.md`](../README.md) prerequisites).

| Script | Purpose | Exit |
|---|---|---|
| [`lint.sh`](lint.sh) | Full skill gate: workflow architecture/phase contracts/size ceilings, tool declarations, bounded fan-out language, wpdev coverage, template schemas, portability, and local links/anchors. | `0` = clean, `1` = failures. |
| [`lint-workflow-structure.py`](lint-workflow-structure.py) | Deterministic workflow-skill-design checks for SKILL/workflow/reference/subagent structure. | `0` = compliant, `1` = findings. |
| [`audit-solution-absorption.py`](audit-solution-absorption.py) | Validate the workspace solution ledger, freshness evidence, owner/destination existence, retirement state, and active-doc independence. | `0` = complete, `1` = incomplete/stale. |
| [`verify-install.sh`](verify-install.sh) | Check a target site and runtime prerequisites: `wpdev`, Voxel, lean-seo, Elementor Framework, committed EF assets, `agent-browser`, and `jq`. Run as `./scripts/verify-install.sh <site>` before first use on a site. | `0` = all required prereqs OK. |
| [`action-spec.sh`](action-spec.sh) | Resolve the action-spec for a Voxel `ts_actions` cell (used by the card-actions workflow). | passthrough. |
| [`generate-icon-reference.ts`](generate-icon-reference.ts) | Regenerate the Material Symbols icon reference (`references/icons/material-symbols/`) from Google's metadata. Run from the skill root; set `WPDEV_ROOT` for a non-sibling WordPress checkout. | passthrough. |

## Running lint

```bash
bash scripts/lint.sh
```

The lint is intentionally lean for the portable form — it dropped the plugin-era
checks (plugin.json validation, version-drift stamps, component-count-vs-README)
that don't apply to a `~/.agents/skills/<name>/` skill.
