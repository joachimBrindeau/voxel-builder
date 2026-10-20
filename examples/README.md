# Examples — golden `_elementor_data` fixtures

Current production widget snapshots from the approved fixture sources `best-matcha.test` and `klarc.test`. These files concretize Rule 2 of [`../references/core/rules.md`](../references/core/rules.md): Voxel theme `ts-*` widgets have no schema introspection, so a current live dump is the canonical shape reference.

Fixture nodes are stored verbatim, including dynamic tags and source metadata. EF fixtures are convenience starting trees only. Their authoritative prop and row shapes remain the exact skill-local mirror at `references/ef/widget-schemas.json`.

## Inventory

| File | Widget | Source | Role |
|---|---|---|---|
| `ef-card.json` | `ef-card` | `best-matcha:1067`, node `346a3cf` | Current atomic card with a canonical text row. |
| `ef-wrapper.json` | `ef-wrapper` | `best-matcha:1067`, node `93c3112` | Current template-mode atomic wrapper. |
| `quick-search.json` | `quick-search` | `best-matcha:3003`, node `3003` | Current cross-CPT quick search. |
| `ts-advanced-list.json` | `ts-advanced-list` | `best-matcha:1067`, node `5b11e84` | Richest current approved advanced-list action source. |
| `ts-create-post.json` | `ts-create-post` | `best-matcha:51`, node `eaacc37` | Richest current approved create/edit form source. |
| `ts-search-form.json` | `ts-search-form` | `best-matcha:4730`, node `1169174` | Richest current approved search-form source. |
| `ts-post-feed.json` | `ts-post-feed` | `klarc:50184`, node `c9db312` | Richest current approved post-feed source. |

## Freshness metadata

- Recaptured from live nodes: `2026-10-20`
- Approved sources: `best-matcha.test`, `klarc.test`
- Voxel: `1.7.8.8`, source hash `20cf1b0f`
- Elementor Framework: `1.0.0`, source hash `c4e9de99`
- Elementor: `4.3.3`, source hash `103b5ede`
- Selection rule: use the highest setting-key count on the approved sites unless a narrower exact behavioral mode is explicitly required.
- Validation rule: every fixture must remain JSON-identical to its named live source node. Do not normalize or rewrite dynamic tags.
- Do not add fixtures from other sites. If neither approved site has the required widget, record the capability gap instead of importing an older or foreign shape.

## Refresh workflow

```bash
# EF nodes, scoped to the named source post.
./wpdev elementor:dump best-matcha ef-card --post 1067 --json \
  | sed -n '/^\[/,$p' | jq '.[] | select(.id == "346a3cf")' > examples/ef-card.json
./wpdev elementor:dump best-matcha ef-wrapper --post 1067 --json \
  | sed -n '/^\[/,$p' | jq '.[] | select(.id == "93c3112")' > examples/ef-wrapper.json

# Voxel theme widgets, selecting the current approved source node.
./wpdev elementor:dump best-matcha quick-search --json \
  | sed -n '/^\[/,$p' | jq '.[] | select(.id == "3003")' > examples/quick-search.json
./wpdev elementor:dump best-matcha ts-advanced-list --json \
  | sed -n '/^\[/,$p' | jq '.[] | select(.id == "5b11e84")' > examples/ts-advanced-list.json
./wpdev elementor:dump best-matcha ts-create-post --json \
  | sed -n '/^\[/,$p' | jq '.[] | select(.id == "eaacc37")' > examples/ts-create-post.json
./wpdev elementor:dump best-matcha ts-search-form --json \
  | sed -n '/^\[/,$p' | jq '.[] | select(.id == "1169174")' > examples/ts-search-form.json
./wpdev elementor:dump klarc ts-post-feed --json \
  | sed -n '/^\[/,$p' | jq '.[] | select(.id == "c9db312")' > examples/ts-post-feed.json
```

## Verification

```bash
for f in examples/*.json; do
  jq -e 'if .widgetType then .widgetType else .elType end' "$f"
done
```

Before using a `ts-*` fixture, dump its named source node and compare complete canonical JSON with `jq -cS`. Any difference requires refreshing the fixture and this metadata first.
