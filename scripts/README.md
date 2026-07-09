# scripts/

Utility scripts bundled with the voxel-builder skill. These are portable — they
don't depend on any specific agent host — but the icon/action ones do call the
`wpdev` CLI (see the skill's Prerequisites).

| Script | Purpose | Exit |
|---|---|---|
| [`lint.sh`](lint.sh) | Portable-skill lint: no Claude-Code coupling (Claude-Code plugin coupling (env-var paths, allowed-tools frontmatter, slash-command refs)), SKILL.md ≤500 lines, no hardcoded absolute paths, and every relative link + `#anchor` resolves (via `lychee` when installed). | `0` = clean, `1` = failures. |
| [`verify-install.sh`](verify-install.sh) | Check the runtime prerequisites are present: `wpdev` on PATH, a local site reachable, `agent-browser`, `jq`. Run before first use on a new machine. | `0` = all prereqs OK. |
| [`action-spec.sh`](action-spec.sh) | Resolve the action-spec for a Voxel `ts_actions` cell (used by the card-actions workflow). | passthrough. |
| [`generate-icon-reference.ts`](generate-icon-reference.ts) | Regenerate the Material Symbols icon reference (`references/icons/material-symbols/`) from Google's metadata. Run to refresh the icon set. | passthrough. |

## Running lint

```bash
bash scripts/lint.sh
```

The lint is intentionally lean for the portable form — it dropped the plugin-era
checks (plugin.json validation, version-drift stamps, component-count-vs-README)
that don't apply to a `~/.agents/skills/<name>/` skill.
