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
rg -i "calendar|event|schedule|booking" references/icons/material-symbols/search.tsv
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

## Site-wide icon replacement

Use this when a site has mixed legacy Font Awesome / Line Awesome / SVG icons, or when a Voxel content set needs a real icon taxonomy for every object.

1. Inventory Elementor icon cells and published Voxel objects first:

```bash
./wpdev elementor:icons <site> --json > /tmp/<site>-elementor-icons-before.json
./wpdev wp <site> post list \
  --post_type=post,page,profile,org,exp,emploi,geo,testimonials,collection,glossaire \
  --post_status=publish \
  --fields=ID,post_type,post_title,post_name,post_parent,menu_order \
  --format=json > /tmp/<site>-posts.json
```

2. Build an explicit assignment map before writing. Requirements for broad replacements:

- Every content icon value must be installed in [search.tsv](search.tsv).
- Store content icon meta as `ms:ms ms-<name>`.
- Keep icons unique when the user asks for uniqueness; fail the map if duplicate values remain.
- Prefer semantic pools by post type and title keywords before generic fallback pools.
- Exclude numeric / resolution / device / photo fallback icons (for example `17mp`, `1k`, `device_*`, `photo_*`) unless the title explicitly needs them.
- Reserve the clearest icons for first-viewport pages and primary CPTs: `home`, `design_services`, `contact_mail`, `location_on`, `work`, `newspaper`, `reviews`, `menu_book`, `corporate_fare`.

3. Write Voxel content icon values through the highest-level command that fits. For one-off edits use `voxel:set-field`; for hundreds of rows a guarded `wpdev wp <site> eval` batch using `update_post_meta( $id, 'icon', $value )` is acceptable when followed by a rebuild/reindex gate.

4. Convert CPT settings icons too. `voxel:post_types` can be JSON-encoded; decode it before editing and write `settings.icon` as `ms:ms ms-<name>` for each CPT.

5. Convert Elementor icon cells from the scanner findings:

- Scalar cells: use `elementor:set-value` with scanner paths converted from `settings.foo[0]` to `foo.0`.
- Elementor object icon controls: set `{ "value": "ms ms-<name>", "library": "ms" }`. Do not store the prefixed `ms:ms ms-<name>` string inside object-shaped controls; it can render as a literal `ms:ms` class.
- SVG object cells usually need a small mutator because `elementor:set-value` only writes scalar leaves.

6. Rebuild after broad writes:

```bash
./wpdev rebuild <site> --only=purge,css,reindex
```

7. Verification gates before declaring done:

```bash
./wpdev elementor:icons <site> --json
./wpdev wp <site> eval '/* count icon meta: total, nonempty, unique, /^ms:ms ms-/ bad rows */'
./wpdev wp <site> option get 'voxel:post_types' --format=json
```

Then browser-sample representative public URLs with `wpdev browser` / `agent-browser` and assert:

- `document.querySelectorAll('[class*="fa-"],[class*="la-"],[class*="efn-"]').length === 0`
- Material icon elements are present on pages that render icons.
- No `ms:ms` literal class remains in the DOM.
- `agent-browser errors` is empty. Existing console warnings unrelated to icons should be reported separately, not treated as icon failures.

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
- Exception: Elementor object-shaped icon controls store `{ "value": "ms ms-<name>", "library": "ms" }`; the `ms:ms` prefix is for scalar EF icon cells.
- Do not fill icons casually. `ms-fill` changes visual weight and should be a design choice.
