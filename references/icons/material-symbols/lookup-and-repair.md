# Icon Selection And Repair Workflow

This workflow keeps context small while giving access to the full 4253-icon Material Symbols library installed by Elementor Framework. Search is enriched for 3879 installed icons with Google Symbols categories/tags/popularity; the rest use generated name terms.

## Pick the right icon

1. Name the visual job in plain words: action, object, status, place, commerce, document, navigation.
2. Prefer the CLI search for ranked results:

```bash
./wpdev elementor:icon-search "calendar booking schedule" --limit 12
./wpdev elementor:icon-search "external link new tab" --category "UI"
./wpdev elementor:icon-search "trust verified badge" --json
./wpdev elementor:icon-search --categories
```

The CLI expands common workspace intent words such as `reservation`, `trust`, `external`, `address`, and `seo`; use `--json` when you need score, matches, and reasons for each candidate.

3. Or search [search.tsv](search.tsv):

```bash
rg -i "calendar|event|schedule|booking" ../skills/voxel-builder/references/icons/material-symbols/search.tsv
```

4. Prefer literal Material names over cute metaphors. For example, use `calendar_month` for booking, `location_on` for address, `verified` for trust, `open_in_new` for external links.
5. Emit the EF icon string: `ms:ms ms-<name>`.

## Verify site usage

Use the DB scanner after any icon work:

```bash
./wpdev elementor:icons <site> --unique
./wpdev elementor:icons <site> --json
./wpdev elementor:icons <site> --library ms --unique
```

The scanner reads stored `_elementor_data` for pages and templates, including `header`, `footer`, `single-post`, `archive`, `card`, and regular pages.

## Fix a wrong icon

Use the scanner's `postId`, `nodeId`, and `keyPath`. Scanner paths include the `settings.` prefix and use bracket array indexes; `elementor:set-value` wants a path relative to `settings` with dotted array indexes. Convert before writing:

```bash
key_path='settings.ts_actions.value[0].value.icon.value'
set_path=$(printf '%s' "$key_path" | sed 's/^settings\.//; s/\[\([0-9][0-9]*\)\]/.\1/g')

./wpdev elementor:set-value <site> --post <post_id> --node <node_id> --path "$set_path" --value 'ms:ms ms-<name>' --yes
```

For batch edits, write a JSON map with dotted `path` values and run:

```bash
./wpdev elementor:set-value <site> --map /tmp/icon-fixes.json --yes
```

Then verify:

```bash
./wpdev elementor:icons <site> --post <post_id> --json
./wpdev elementor:lint <site> --post <post_id>
```

For non-scalar icon cells or broad structural edits, prefer a small mutator or `elementor:mutate` over forcing `set-value`.

## Provision a Voxel icon field

When the CPT itself needs an icon field for templates/cards to read, use the Voxel settings command instead of editing `voxel:post_types` directly:

```bash
./wpdev voxel:settings <site> ensure-field --type <cpt_key> --fieldKey icon --fieldType icon --label Icon --dry
./wpdev voxel:settings <site> ensure-field --type <cpt_key> --fieldKey icon --fieldType icon --label Icon --yes
```

If legacy icon values are numeric media IDs, migrate them to Voxel's SVG icon string form:

```bash
./wpdev voxel:settings <site> ensure-field --type <cpt_key> --fieldKey icon --fieldType icon --migrate-image-ids --yes
```

## Anti-patterns

- Do not invent `ms-*` class names. Search [search.tsv](search.tsv).
- Do not use Font Awesome / Line Awesome as the default for new EF work; prefer Material Symbols unless preserving existing visual parity.
- Do not store bare `ms ms-foo`; EF icon cells should store `ms:ms ms-foo`.
- Do not fill icons casually. `ms-fill` changes visual weight and should be a design choice.
