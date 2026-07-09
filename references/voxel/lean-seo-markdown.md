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
3. **Rendered page context** (`lean_seo_rendered_context_for_markdown`) — appended under `## Rendered page content` **only when** the structured body misses visible copy. This is the site-agnostic catch-all.

## The critical gap: structured maps miss single-template layout

**A Voxel/Elementor single template is not stored in `post_content`.** Field maps capture the post's own fields, but the theme/builder single template — relation carousels, "related services" card loops, static Elementor hero/CTA sections, glossary "see also" cards — renders from a *separate* template. No generic field map can know those.

Two-tier fallback closes it, both agnostic:

- **`@post(lean_seo:rendered_html)`** (special dtag key) → `lean_seo_post_html()` → `lean_seo_html_to_text()`. Use in a `dtag_fields` body when a **page** stores its content as Elementor Framework shortcodes (`[ef_row]`, `[ef_col]`) rather than raw HTML — raw `post_content` renders empty otherwise.
- **`lean_seo_frontend_html_for_post()`** → `wp_remote_get( permalink, [timeout=8, sslverify=false] )` → `lean_seo_html_to_text()`. Self-fetches the *public rendered page*, capturing the full single-template layout (loops, cards, relation carousels) for **any** site/CPT/builder. This is what makes `testimonials` (13-item related-avis carousel) and `org` (service card grid) reach parity — their extra content lives only in the template, never in fields.

`lean_seo_rendered_context_for_markdown` tries the frontend fetch first, falls back to `lean_seo_post_html`, then runs the redundancy guard.

## Redundancy guard (avoid double-printing the body)

`lean_seo_markdown_text_is_redundant( $candidate, $existing )`:
- normalizes both to lowercase token sets (>3 chars);
- skips the candidate if `$existing` already **contains** the normalized candidate, **or** token overlap ratio > `0.85`.

So a page whose field map already surfaces the full body won't get the whole rendered page appended again; a page whose fields cover only a fraction will.

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

Two storage caveats: (1) the option is a **JSON string**, not a serialized PHP array — a manual `update_option` with an array breaks `lean_seo_get_md_field_maps()` (it `json_decode`s; legacy arrays tolerated on read only), so always encode. (2) A baked `post` default (`text_fields:['body']`, `repeaters:{faq:'FAQ'}`) merges **under** the stored map and applies even with no stored `post` entry — override by saving an explicit `post` map.

## Verifying parity

crawl4ai MCP **blocks `.test` / loopback hosts (SSRF guard)** — do not use it against a local WP install. Use the Playwright or camofox MCP to crawl the live single, extract `h1,h2,h3` + `body.innerText`, then diff against `lean_seo_generate_markdown( get_post($id) )`. An ad-hoc `wp eval` loop asserting each expected heading/string is `str_contains($md, …)` and that no unresolved `@post(` / `@author(` / `@tags()` / `@endtags()` leak is the fast gate.
