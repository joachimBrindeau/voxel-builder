# Examples — golden `_elementor_data` fixtures

Four real production widget snapshots, extracted via `wpdev elementor:dump` from a production `<site>`. They concretize **Rule 2** of [`../../references/core/rules.md`](../references/core/rules.md): Voxel theme `ts-*` widgets have no schema introspection, so a real production dump is the canonical shape reference.

The EF widgets (`ef-card`, `ef-wrapper`) are included here only as convenience templates — their **authoritative SSOT** is the committed `cli/src/generated/widget-schemas.json` (Rule 1, generated from `plugins/custom/elementor-framework/schemas/` and CI-gated against drift). When the SSOT and a fixture disagree, the SSOT wins. Use fixtures as starting trees, never as authoritative spec — they should be refreshed when the EF V4 schema churns.

## Inventory

| File | Widget | `elType` / `widgetType` | Source post id (`<site>`) | Role |
|---|---|---|---|---|
| `ef-card.json` | `ef-card` | `elType: "ef-card"` (atomic element — NO `widgetType`) | `<post_id>` (Single post template) | EF V4 atomic card — byline avatar, dynamic h1, tags row. Convenience starting tree; SSOT is `widget-schemas.json`. |
| `ef-wrapper.json` | `ef-wrapper` | `elType: "ef-wrapper"` | `<post_id>` (Single post template) | EF V4 atomic top-level `<main>` wrapper envelope. Convenience starting tree; SSOT is `widget-schemas.json`. |
| `ts-create-post.json` | `ts-create-post` | `widgetType: "ts-create-post"` (Voxel theme) | `<post_id>` (Edit profile) | Voxel-theme submission/edit form — no schema introspection; this dump IS the canonical shape reference. |
| `ts-post-feed.json` | `ts-post-feed` | `widgetType: "ts-post-feed"` (Voxel theme) | `<post_id>` (Archive template) | Voxel-theme post-feed widget — no schema introspection; this dump IS the canonical shape reference. |

## Refresh workflow

When the EF V4 atomic schema churns (a new migration step lands, a prop is renamed, a `$$type` envelope changes) or a Voxel theme release reshapes a `ts-*` widget, re-extract the affected fixtures:

```bash
# ef-card — pick a current single-post template id
./wpdev elementor:dump <site> ef-card --post <post_id> --json \
  | sed -n '/^\[/,$p' \
  | jq '.[0]' > examples/ef-card.json

# ef-wrapper — pick a post with at least one ef-wrapper instance
./wpdev elementor:dump <site> ef-wrapper --post <post_id> --json \
  | sed -n '/^\[/,$p' \
  | jq '.[0]' > examples/ef-wrapper.json

# ts-create-post — pick a post hosting a submission/edit form
./wpdev elementor:dump <site> ts-create-post --post <post_id> --json \
  | sed -n '/^\[/,$p' \
  | jq '.[0]' > examples/ts-create-post.json

# ts-post-feed — pick any post with a feed
./wpdev elementor:dump <site> ts-post-feed --post <post_id> --json \
  | sed -n '/^\[/,$p' \
  | jq '.[0]' > examples/ts-post-feed.json
```

The `sed` filter strips the leading "unknown meta keys" warning that `wpdev elementor:dump` writes to stdout (yes — to stdout). The `jq '.[0]'` reduces the array of all instances to the first one. Bump the plugin version and add a CHANGELOG entry when fixtures are refreshed.

## Verification

```bash
for f in examples/*.json; do
  jq -e 'if .widgetType then .widgetType else .elType end' "$f"
done
```

All four should print their widget type without error.

## Why these four

- **`ef-card` / `ef-wrapper`** — the two most-used EF V4 atomic widgets across the portfolio. Shipped as convenience starting trees so a build agent doesn't have to dump one before scaffolding. The authoritative shape still lives in `cli/src/generated/widget-schemas.json`.
- **`ts-create-post` / `ts-post-feed`** — Voxel theme widgets whose shapes **cannot** be introspected via `wpdev elementor:schema` (which only covers EF V4 atomic widgets). These dumps are the canonical references the SKILL.md routing table sends agents to for "build a CPT submission/edit form" and "add a post feed" tasks.

Other `ts-*` widgets the skill's prompts reference (`ts-search-form`, etc.) appear less often; if usage data later shows a gap, add a fixture here in a follow-up.
