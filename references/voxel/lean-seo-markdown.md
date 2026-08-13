# lean-seo markdown generator — Voxel-aware LLM `.md` companion

The `lean-seo` plugin emits a per-post markdown twin (the "Version markdown pour agents" link on every single) so LLM crawlers get a clean, structured copy of what a human sees. When a page's markdown twin is **missing visible content** — repeater rows, relation lists, single-template loops, card grids, static Elementor sections — the fix lives in `modules/llms/inc/markdown.php` and the per-CPT field maps stored in the `lean_seo_markdown_field_maps` option. This file is the SSOT for how that generator resolves content, so a page/template audit that flags "the `.md` is thinner than the rendered page" routes here instead of the build pipeline.

## Where content comes from (resolution order)

`lean_seo_generate_markdown( WP_Post )` builds output in layers:

1. **Header** — title, meta description, source URL.
2. **Structured body** (`lean_seo_voxel_to_markdown`) — driven by the CPT's entry in `lean_seo_markdown_field_maps`. Map shapes:
   - `text_fields` → `array<string>` of Voxel field keys, rendered inline.
   - `sections` → `array<{heading, body}>` where `body` is a Voxel field key.
   - `repeaters` → `array<field_key, section_label>` — each repeater row expanded.
   - `dtag_fields` → `array<{label, body}>` — free-text dynamic-tag rows; `body` is a dynamic-tag expression (`@post(key)`, `@author(tag)`) or static text, resolved server-side through Voxel's renderer. Label empty = no heading.
   - `relations` → `array<relation_field_key, section_label>` — Voxel `post-relation` fields rendered as a linked-title list.
3. **Rendered body** (`lean_seo_rendered_markdown_for_post`) — the sole body owner when the CPT has no configured structured fields. It converts the rendered page HTML to Markdown automatically; there is no setting or fallback toggle.

## Ownership rule

Markdown has exactly one body owner per CPT:

- If at least one structured field is configured, the field map owns the body.
- If no structured field is configured — including an absent map, an empty map, or a legacy flag-only map — rendered HTML-to-Markdown owns the body automatically.

"Rendered" means the **public frontend response**, not `post_content`. `lean_seo_rendered_body_for_post()` is the single owner of that resolution: it fetches the live permalink and falls back to the post's own stored/builder HTML only when the loopback fails. This matters because a Voxel CPT or template-driven page renders a full page while its own `post_content` is empty — resolving against stored HTML alone yields a body-less `.md` twin that `regenerate-md` still reports as generated. When auditing markdown coverage, count discoverable posts whose stored `_lean_seo_md` is under the thin threshold; a per-type "N/N regenerated" line does not prove the bodies have content.

Saving the first structured field intentionally switches ownership. A Voxel/Elementor single template is not stored in `post_content`, so the configured map must cover all reader-facing content it owns. Use **`@post(lean_seo:rendered_html)`** in `dtag_fields` when rendered template content must be part of that structured map.

Do not append rendered output to a structured body as a second path. Fix the owning map or explicitly map `lean_seo:rendered_html`.

## Regex gotcha for native `@post()` keys

The native-tag resolver's key pattern must allow underscores and colons — `post_content`, `lean_seo:rendered_html`. Use `[\w|:-]+`, not `[\w-]+`. A too-narrow class silently drops these keys and the section renders empty.

## Editing the maps

The maps are a **DB option**, not code — site-instance data, correctly kept out of the plugin (which stays agnostic). Read/write:

```bash
# read
wp option get lean_seo_markdown_field_maps
# write (edit JSON, then)
wp option update lean_seo_markdown_field_maps "$(python3 -c 'import json; print(json.dumps(json.load(open("/tmp/maps.json")), ensure_ascii=False))')"
```

The admin UI (`modules/llms/settings.php` + `assets/markdown-fields.js`) exposes `text_fields`, `sections`, `repeaters`, `dtag_fields`, and `relations` tables; the AJAX save (`includes/settings-ajax.php`) sanitizes each. Adding a new map shape = touch all four (PHP renderer, admin UI, JS serializer, AJAX sanitizer).

The option is a **JSON string**, not a serialized PHP array — a manual `update_option` with an array breaks `lean_seo_get_md_field_maps()` (it `json_decode`s; legacy arrays tolerated on read only), so always encode. There are no baked per-CPT maps: every CPT with no configured fields uses rendered HTML-to-Markdown uniformly.

## Verifying parity

crawl4ai MCP **blocks `.test` / loopback hosts (SSRF guard)** — do not use it against a local WP install. Use the Playwright or camofox MCP to crawl the live single, extract `h1,h2,h3` + `body.innerText`, then diff against `lean_seo_generate_markdown( get_post($id) )`. An ad-hoc `wp eval` loop asserting each expected heading/string is `str_contains($md, …)` and that no unresolved `@post(` / `@author(` / `@tags()` / `@endtags()` leak is the fast gate.
