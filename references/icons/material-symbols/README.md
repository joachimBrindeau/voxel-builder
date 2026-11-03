# Material Symbols Icon Reference

Generated from the Elementor Framework installed icon font at `../../../plugins/custom/elementor-framework/assets/icons/material-symbols/material-symbols.codepoints.json`, enriched with Google Symbols metadata from `https://fonts.google.com/metadata/icons?incomplete=1&key=material_symbols`. Do not hand-edit generated files; from the skill root run:

```bash
bun run scripts/generate-icon-reference.ts
```

Set `WPDEV_ROOT` when the WordPress workspace is not a sibling checkout.

## Storage format

Use one string cell:

```text
ms:ms ms-<icon_name>
```

Example: `ms:ms ms-calendar_month`. Add `ms-fill` to the class only when a filled Material Symbol is intentionally required: `ms:ms ms-bookmark ms-fill`.

## Fast lookup protocol

1. Use the CLI search when available:

```bash
./wpdev elementor:icon-search "calendar booking schedule" --limit 12
./wpdev elementor:icon-search --categories
```

The CLI expands common intent synonyms, accepts partial `--category` matches, returns match evidence in the table/JSON, and suppresses popularity-only false positives. Hosted agents reach the same index through the `wpdev_elementor__icon-search` MCP tool.

2. Or search the generated index with intent words, not guesses:

```bash
rg -i "calendar|event|schedule|booking" ../skills/voxel-builder/references/icons/material-symbols/search.tsv
```

3. Read [top-picks.md](top-picks.md) for common Voxel/EF use cases.
4. Write exactly `ms:ms ms-<name>` into EF icon cells.

## Coverage

- EF installed icons: 4253.
- Google Symbols metadata-enriched icons: 3879.
- EF icons using generated-name fallback terms: 374.

EF's installed `codepoints` file remains the availability source of truth. Google metadata supplies categories, tags, popularity, versions, and sizes where the current metadata endpoint covers the installed icon name.

## Files

- [lookup-and-repair.md](lookup-and-repair.md) — choose, verify, and repair icons in live Elementor data.
- [top-picks.md](top-picks.md) — short curated map for common build decisions.
- [search.tsv](search.tsv) — full 4253-icon grep index: `name css codepoint categories popularity terms`.
- [manifest.json](manifest.json) — count + source metadata.
