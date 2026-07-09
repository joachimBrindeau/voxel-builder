# Sitewide AI-marker cleanup in WordPress/Elementor/Voxel sites

Use when removing promotional adjectives, AI markers, and superlatives across a WordPress site, especially when content lives in mixed storage: posts, excerpts, Voxel fields, Elementor JSON, SEO meta, and generated markdown feeds.

## Scope to scan

Check all likely text stores, not only rendered page content:

- `wp_posts.post_title`
- `wp_posts.post_excerpt`
- `wp_posts.post_content`
- `_elementor_data`
- SEO metas such as `_lean_seo_title`, `_lean_seo_description`, `_lean_seo_md`
- Voxel/custom post meta text fields when public-facing
- selected text options, excluding technical options such as `active_plugins`, `cron`, `rewrite_rules`, transients
- TranslatePress dictionary/original-string tables when the site is multilingual: `wp_trp_original_strings.original`, `wp_trp_dictionary_<pair>.original` + `.translated`, `wp_trp_gettext_*` — these feed the `/en/` (or other locale) rendered output and are NOT reached by cleaning posts/meta/Elementor. Clean the source-language string AND its translated column together, in-place per row, matching both the FR marker and its EN rendering (e.g. `accompagnement stratégique`/`strategic support`, `protection efficace`/`effective protection`, `expertise pointue`/`cutting-edge legal expertise`). Preserve legal/status terms like `Jeune Entreprise Innovante`/`Young Innovative Company`.

## Safer cleanup pattern

1. Build a marker list from user examples plus known AI/prose inflation terms.
2. Run a dry-run first with counts and examples.
3. Use recursive string cleanup for decoded Elementor JSON instead of regexing raw JSON blindly.
4. Apply only deterministic replacements for high-confidence words.
5. Re-scan remaining markers by source and context.
6. Do a second context pass for misses like adverbs (`efficacement`) and hyphen variants (`sur-mesure`).
7. Run grammar fixups after aggressive replacement. Examples seen:
   - `bon expérience` -> `expérience`
   - `d'bon conseils` -> `de bons conseils`
   - `un bon conseil` -> `un conseil`
8. Stop before destroying meaning in quotes/testimonials or technical terms unless user explicitly asks for zero raw occurrences.

## EMCP / REST proof path

If an EMCP endpoint returns 401 with an application password on local OpenLiteSpeed, verify whether the hostname resolves to the wrong interface before assuming EMCP itself is broken.

Useful probe pattern:

```bash
APP_PASS=$(./wpdev wp <site> user application-password create wpdev hermes-emcp --porcelain)
AUTH=$(printf 'wpdev:%s' "$APP_PASS" | base64)
curl -sk --resolve <site>.test:443:127.0.0.1 \
  -H "Authorization: Basic $AUTH" \
  https://<site>.test/wp-json/
./wpdev wp <site> user application-password delete wpdev <uuid>
```

Do not leave app passwords or temp password files behind.

## Verification

After writes:

- `php -l <cleanup-script>.php`
- re-run marker count query for posts + targeted meta keys
- `./wpdev rebuild <site> --only purge,css`
- if a script was edited, create and run a focused temporary verifier under OS temp with `hermes-verify-` prefix, then remove it; report as ad-hoc verification, not suite green

## Pitfalls

- `_lean_seo_md` can preserve stale/generated prose even after `_lean_seo_description` and Elementor data are clean. Note: `_lean_seo_md` is an LLM-facing generated feed and is NOT the visible-render source — do not assume a rendered block comes from it just because the words match; the real source is usually a widget in `_elementor_data`.
- Elementor v4 `ef-wrapper` widgets store rich-text (`body`/`value`) DOUBLE-JSON-ENCODED inside `_elementor_data`: closing tags appear as `<\\/strong>` and accented chars as `\uXXXX` (e.g. `exp\u00e9rience`), `&` as `&amp;`. A search on the DECODED text will find the block but a str_replace on decoded text will NOT match the stored bytes. To edit, operate on the raw stored `meta_value` using the escaped forms (`<strong>`, `<\\/strong>`, `\u00e9`, `R&amp;D`), then `json_decode` the OUTER string to validate it still parses before `update_post_meta(..., wp_slash($new))`, and call `\Elementor\Plugin::$instance->files_manager->clear_cache()`.
- TranslatePress tables (`wp_trp_*`) are a common miss: DB posts/meta/Elementor can be fully clean while the front still renders the old marker because TRP serves cached original+translation strings. If a user reports a phrase still visible after posts/meta/Elementor are clean, and DB substring counts on posts/meta/options return 0, scan `wp_trp_original_strings` and `wp_trp_dictionary_<pair>` before blaming browser cache. Verify by fetching both the source-locale and translated-locale URLs with a cache-buster query.
- Raw substring counts overcount revisions, attachments, zip filenames, and technical metadata. Report public-post and targeted-meta counts separately.
- Blind adjective deletion can create broken French. Always run a cleanup pass for grammar artifacts.
- Replacing domain terms like `savoir-faire` can corrupt slugs/URLs and French grammar. Prefer context review before replacing legal/technical terms.
