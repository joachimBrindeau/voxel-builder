# Icon Selection And Repair Workflow

This workflow keeps context small while giving access to the full Material Symbols library installed by Elementor Framework (counts live in [manifest.json](manifest.json)). Hosted agents call the same verbs through the wpdev MCP (`wpdev_elementor__icon-search`, `wpdev_elementor__icons`, `wpdev_elementor__set-value`); run `command_describe` first and treat `transport.allowed: false` verbs as device-shell CLI.

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
neither find nor fix a missing term icon. No `wpdev` verb owns term meta yet; the
sanctioned path is native WP-CLI `term meta` through the `wpdev wp` passthrough with a
read-back gate. Do not reach for `wp eval`, `eval-file` or direct SQL for this.

Trace a rendered glyph back through the owning widget before choosing this route. A
classic icon cell can contain `@post(<taxonomy-field>.icon)` rather than a static
library value. In the current Voxel field API, a taxonomy field's `get_value()` returns
`Voxel\Term` objects, not necessarily integer IDs. Use their `get_id()` and `get_icon()`
accessors to identify the real term-meta owner. Preserve the dynamic Elementor binding
instead of replacing it with a fixed icon that only matches one sample record.

Scope the work to **registered** taxonomies first — an unregistered taxonomy renders
nowhere, so icons on it are dead data:

```bash
./wpdev wp <site> taxonomy list --fields=name,public,object_type
./wpdev wp <site> term list <taxonomy> --fields=term_id,slug --format=json \
  | jq -r '.[].term_id' | while read -r tid; do
      printf '%s\t%s\n' "$tid" "$(./wpdev wp <site> term meta get "$tid" voxel_icon 2>/dev/null)"
    done
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

1. **Uniqueness** — the `term_id<TAB>icon` listing above must have no repeated icon value
   (`cut -f2 | sort | uniq -d` prints nothing).
2. **Glyph exists** — a name in the pack JSON still needs a rule in the pack CSS. Grep
   `assets/icons/<pack>.css` for `.<class>` (Material Symbols/Phosphor use
   `::before{content:"\eXXX"}`; `efb`/`eff` use SVG `mask-image`). A missing rule renders
   an invisible box that no DB check catches.

### Apply with read-back, then verify rendering

Capture the current values first (the listing above is the rollback), then write one
term at a time and read it back:

```bash
./wpdev wp <site> term meta update <term_id> voxel_icon 'eff:eff eff-jp'
[ "$(./wpdev wp <site> term meta get <term_id> voxel_icon)" = 'eff:eff eff-jp' ] || echo "READ-BACK FAILED <term_id>"
```

Prove the runtime surface, not just the column: load a page that renders the term
through `\Voxel\get_icon_markup()` (a card or taxonomy archive) and inspect the icon
markup. Empty markup means the library prefix or glyph is wrong even though the meta
value stored fine.

Nonempty markup is still not a painted-glyph pass. In the real browser, inspect the
resolved icon class, computed font family, pseudo-element content and nonzero glyph
geometry, then read a screenshot. If exact term-meta read-back succeeds but the clean
page still emits old icon classes, invalidate the affected site's cached renders with
the supported `wpdev purge <site>` command and revisit the same URL. Do not rewrite the
dynamic template or inject CSS to conceal stale cached output. Keep existing working
icons and unrelated term data unchanged unless the selected scope explicitly includes
them.

## Anti-patterns

- Do not invent `ms-*` class names. Search [search.tsv](search.tsv).
- Do not use Font Awesome / Line Awesome as the default for new EF work; prefer Material Symbols unless preserving existing visual parity.
- Do not store bare `ms ms-foo`; EF icon cells should store `ms:ms ms-foo`.
- Do not fill icons casually. `ms-fill` changes visual weight and should be a design choice.
- Do not write term icons with `elementor:set-value`; the owner is `voxel_icon` term meta.
- Do not reuse one icon across a taxonomy, and do not assign icons to unregistered taxonomies.
