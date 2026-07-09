# Voxel changelog → standardized JSON

Turn the canonical Voxel release changelog into one flat, queryable JSON. Use when asked to
fetch/update/parse Voxel changelogs, look up **when a Voxel feature or fix shipped** ("which
version added Paddle support?"), list new features or bug fixes for a version, **check whether
Voxel now does something natively** (before hand-building it in EF), or answer "what changed in
Voxel X.Y". Produces a flat list of `{version, date, type (new|fixed), description, source_url}`.

Every entry is normalized to:

```json
{ "version": "1.7.8", "date": "May 15, 2026", "type": "new", "description": "Dynamic tags: New \"Shuffle list\" modifier — randomizes the order of any list", "source_url": "https://getvoxel.io/changelog/" }
```

- `type` is `"new"` (features / additions / improvements) or `"fixed"` (bug fixes).
- The script discovers **every** release itself, newest down to ~0.9.x, so re-running picks up
  new Voxel versions automatically. No version filtering needed.

## Source (important)

The canonical, always-current changelog is the **`voxel_release`** post feed behind
`https://getvoxel.io/changelog/`. The script calls that feed's `search_posts` AJAX endpoint
directly — one request returns every release as server-rendered HTML.

Do **not** use the docs.getvoxel.io changelog articles as the source: they are a curated subset
and lag behind point releases (e.g. they froze at 1.7.1.1 while the live theme was already
1.7.8.1). The getvoxel.io feed is the complete, authoritative list.

## File

- [`../../scripts/build_changelog_json.py`](../../scripts/build_changelog_json.py) — fetch +
  parse + classify. **Stdlib only** (urllib + `re`); no pip installs, no browser, no MCP.
  Handles both release-body formats (newer `<ul><li>` lists and older `<p>– entry<br>…</p>`
  en-dash lists).

## Build / update the dataset

`build` and `update` are the **same** command (re-running overwrites the JSON); querying is done
with `jq` against the output file, not the script.

```bash
# Pretty JSON to a file:
python3 <skill>/scripts/build_changelog_json.py --pretty -o /tmp/voxel-changelog.json

# Print to stdout / pipe into jq:
python3 <skill>/scripts/build_changelog_json.py | jq '.entry_count'

# Debug a subset (first N releases):
python3 <skill>/scripts/build_changelog_json.py --limit 5 --pretty
```

Flags: `-o/--output`, `--pretty`, `--limit N` (first N releases), `--quiet` (no stderr
progress). Progress (one line per release with its entry count) prints to **stderr**, so stdout
stays clean for piping.

## Output schema

Top level: `source`, `source_url`, `generated_at`, `version_count`, `entry_count`,
`type_counts`, `versions` (array of `{version, date}`, newest-first), and `entries` (flat array,
newest-first).

## Querying

```bash
F=/tmp/voxel-changelog.json

# Everything new in a version
jq -r '.entries[] | select(.version=="1.7.8" and .type=="new") | .description' "$F"

# All fixes mentioning a keyword, with version + date
jq -r '.entries[] | select(.type=="fixed" and (.description|test("Mapbox";"i")))
       | "\(.version)  \(.date)  \(.description)"' "$F"

# When did a feature first appear? (oldest version containing a keyword)
# entries are newest-first, so `last` returns the earliest matching version
jq -r '[.entries[] | select(.description|test("Paddle";"i")) | .version] | last' "$F"

# Only the 1.7.x line, new features
jq -r '.entries[] | select(.version|test("^1\\.7")) | select(.type=="new")
       | "\(.version) \(.description)"' "$F"

# Count entries per version
jq -r '.entries | group_by(.version)[] | "\(.[0].version): \(length)"' "$F"
```

## How parsing works (for maintenance)

1. **Fetch** — one GET to the `voxel_release` feed:
   `https://getvoxel.io/?vx=1&action=search_posts&type=voxel_release&pg=1&limit=2000`. Returns
   every release card as SSR HTML.
2. **Split** — split the document at each version `<h2>` (e.g. `1.7.8`). Each release's body sits
   between its heading and the next.
3. **Anchor** — extraction is anchored to the release's `vx-post-body` text-editor block and cut
   at the trailing `ts-preview` card render, so the preview markup never leaks. A version `<h2>`
   with no `vx-post-body` (a preview-card duplicate) is skipped.
4. **Extract entries** — `<ul><li>` releases: each `<li>` is one atomic entry (no dash splitting,
   so "Per order – Fixed cost" stays intact). Older `<p>`+`<br>` releases: split each `<p>…</p>`
   on `<br>` / en-dash into entries.
5. **Classify** — `description` starting with `fix`/`fixed` (optionally after a `Category:` label)
   → `"fixed"`, else `"new"`.
6. **De-dupe** on `(version, type, description)`; sort newest-first; capture each release's date.

### Known limitations

- Grouped entries with a bare category label (e.g. "User dynamic data") appear as their own short
  "new" entry alongside their sub-points. Harmless, occasionally low-signal.
- `<li>`-format entries are kept atomic; older `<p>`-format entries are split on en/em-dashes and
  `<br>`. ASCII hyphens are always preserved ("drag-and-drop" stays intact).
- Classification is two-bucket only (`new`/`fixed`); "Tweak"/"Improvement" entries map to `new`.
