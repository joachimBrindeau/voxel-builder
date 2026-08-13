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

The CLI expands common intent synonyms, accepts partial `--category` matches, returns match evidence in the table/JSON, and suppresses popularity-only false positives.

2. Or search the generated index with intent words, not guesses:

```bash
rg -i "calendar|event|schedule|booking" ../skills/voxel-builder/references/icons/material-symbols/search.tsv
```

3. Read [top-picks.md](top-picks.md) for common Voxel/EF use cases.
4. If needed, open the matching shard under [by-prefix/](by-prefix/) to inspect nearby names.
5. Write exactly `ms:ms ms-<name>` into EF icon cells.

## Coverage

- EF installed icons: 4253.
- Google Symbols metadata-enriched icons: 3879.
- EF icons using generated-name fallback terms: 374.

EF's installed `codepoints` file remains the availability source of truth. Google metadata supplies categories, tags, popularity, versions, and sizes where the current metadata endpoint covers the installed icon name.

## Files

- [lookup-and-repair.md](lookup-and-repair.md) — choose, verify, and repair icons in live Elementor data.
- [top-picks.md](top-picks.md) — short curated map for common build decisions.
- [search.tsv](search.tsv) — full 4253-icon grep index: `name css codepoint categories popularity terms`.
- [metadata.json](metadata.json) — compact metadata cache for EF-installed icons only.
- [manifest.json](manifest.json) — count + source metadata.
- [0-9.md](by-prefix/0-9.md) — 67 icons
- [a.md](by-prefix/a.md) — 330 icons
- [b.md](by-prefix/b.md) — 254 icons
- [c-1.md](by-prefix/c-1.md) — 350 icons
- [c-2.md](by-prefix/c-2.md) — 13 icons
- [d.md](by-prefix/d.md) — 222 icons
- [e.md](by-prefix/e.md) — 148 icons
- [f.md](by-prefix/f.md) — 281 icons
- [g.md](by-prefix/g.md) — 114 icons
- [h.md](by-prefix/h.md) — 157 icons
- [i.md](by-prefix/i.md) — 72 icons
- [j.md](by-prefix/j.md) — 11 icons
- [k.md](by-prefix/k.md) — 45 icons
- [l.md](by-prefix/l.md) — 179 icons
- [m.md](by-prefix/m.md) — 263 icons
- [n.md](by-prefix/n.md) — 154 icons
- [o.md](by-prefix/o.md) — 51 icons
- [p.md](by-prefix/p.md) — 280 icons
- [q.md](by-prefix/q.md) — 20 icons
- [r.md](by-prefix/r.md) — 152 icons
- [s-1.md](by-prefix/s-1.md) — 350 icons
- [s-2.md](by-prefix/s-2.md) — 200 icons
- [t.md](by-prefix/t.md) — 250 icons
- [u.md](by-prefix/u.md) — 40 icons
- [v.md](by-prefix/v.md) — 101 icons
- [w.md](by-prefix/w.md) — 134 icons
- [x.md](by-prefix/x.md) — 1 icon
- [y.md](by-prefix/y.md) — 7 icons
- [z.md](by-prefix/z.md) — 7 icons
