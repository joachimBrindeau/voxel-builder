# Elementor Build Troubleshooting


| Symptom | Likely cause | Fix |
|---|---|---|
| `elementor:lint` reports `unknown-prop` for a recently-renamed key | Memorised V3 prop name | Re-query schema, use new name |
| Dynamic tag renders as literal `@post(title)` text | Missing `@tags()...@endtags()` wrapper on a string-type prop | Wrap the value |
| Image renders empty | Image `$$type` wrong; needs `{$$type: image, value: {src: {$$type: vx \| number, value: ...}}}` | Query `--prop <key>` for exact shape |
| Feed renders empty | CPT lacks `search.filters` + `search.order`, or index table missing | Add to blueprint, run index table create + reindex |
| Form submit doesn't update feed | `ts_post_to_feed` references stale widget ID | Update to current feed widget's `id` |
| Single ef-card rendered with extra spacing | Wrapper container present | `wpdev elementor:strip:wrappers <site> --fix --yes` (site-wide; snapshot first, approved cleanup only) |
| CSS not applied after write | `--save` failed or was omitted | Re-run import with `--save`, or open editor URL and click "Update" |
