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

## Populate taxonomy term icons

Term icons are a **different source owner** from Elementor icon cells: they live in the
`voxel_icon` **term meta**, read by `\Voxel\Term::get_icon()`
(`themes/vendor/voxel/app/term.php`) and rendered through `\Voxel\get_icon_markup()`.
`elementor:icons` / `elementor:set-value` only scan and write `_elementor_data`, so they
neither find nor fix a missing term icon. There is no `wpdev` term-meta write command;
use `wp eval-file` with a read-back gate.

Scope the work to **registered** taxonomies first — an unregistered taxonomy renders
nowhere, so icons on it are dead data:

```bash
./wpdev wp <site> eval 'foreach (get_taxonomies([],"objects") as $t) printf("%-28s public=%d\n",$t->name,$t->public);'
./wpdev wp <site> db query "SELECT tt.taxonomy, COUNT(*) terms,
  SUM(CASE WHEN tm.meta_value<>'' THEN 1 ELSE 0 END) with_icon
  FROM wp_term_taxonomy tt
  LEFT JOIN wp_termmeta tm ON tm.term_id=tt.term_id AND tm.meta_key='voxel_icon'
  GROUP BY tt.taxonomy;"
```

### Pick the pack per taxonomy

EF installs six packs (`ef_icon_pack_specs()` in
`plugins/custom/elementor-framework/includes/media/icons.php`). Match the pack to the
term's real-world identity instead of forcing Material Symbols everywhere:

| Pack | Prefix | Storage string | Use for |
|---|---|---|---|
| Material Symbols | `ms` | `ms:ms ms-<name>` | General concepts, the default |
| Phosphor | `ph` | `ph:ph ph-<name>` | Brand/social logos (`ph-facebook-logo`, `ph-x-logo`, `ph-whatsapp-logo`) |
| EF Brands | `efb` | `efb:efb efb-<name>` | EF-owned brand glyphs Phosphor lacks (`trustpilot`, `reviews-io`) |
| Flags | `eff` | `eff:eff eff-<cc>` | Country terms — `eff-jp`, `eff-cn` beat a generic globe |
| Numbers | `efn` | `efn:efn efn-<n>` | Ordered/graded terms |
| Initials | `efi` | `efi:efi efi-<A>` | Last-resort per-letter fallback |

Availability per pack is the shipped JSON, not memory — validate every candidate against
`assets/icons/{phosphor,brands,flags,numbers,initials}.json` and Material Symbols against
`search.tsv` **before** writing.

### Uniqueness and glyph gates

Repeating one icon across a taxonomy destroys the visual signal it exists for. Gate on both:

1. **Uniqueness** — assert `COUNT(*) = COUNT(DISTINCT meta_value)` for `voxel_icon`.
2. **Glyph exists** — a name in the pack JSON still needs a rule in the pack CSS. Grep
   `assets/icons/<pack>.css` for `.<class>` (Material Symbols/Phosphor use
   `::before{content:"\eXXX"}`; `efb`/`eff` use SVG `mask-image`). A missing rule renders
   an invisible box that no DB check catches.

### Apply with read-back, then verify rendering

```php
// /tmp/apply-term-icons.php — rows: [{term_id, icon}, …]
update_term_meta( $tid, 'voxel_icon', $icon );
if ( get_term_meta( $tid, 'voxel_icon', true ) !== $icon ) { /* record failure */ }
```

```bash
ICON_DRY=1 ./wpdev wp <site> eval-file /tmp/apply-term-icons.php   # capture rollback first
./wpdev wp <site> eval-file /tmp/apply-term-icons.php
```

Prove the runtime surface, not just the column:

```bash
./wpdev wp <site> eval '$t=\Voxel\Term::get(<id>); echo \Voxel\get_icon_markup($t->get_icon());'
```

Empty markup means the library prefix or glyph is wrong even though the meta value stored fine.

## Anti-patterns

- Do not invent `ms-*` class names. Search [search.tsv](search.tsv).
- Do not use Font Awesome / Line Awesome as the default for new EF work; prefer Material Symbols unless preserving existing visual parity.
- Do not store bare `ms ms-foo`; EF icon cells should store `ms:ms ms-foo`.
- Do not fill icons casually. `ms-fill` changes visual weight and should be a design choice.
- Do not write term icons with `elementor:set-value`; the owner is `voxel_icon` term meta.
- Do not reuse one icon across a taxonomy, and do not assign icons to unregistered taxonomies.
