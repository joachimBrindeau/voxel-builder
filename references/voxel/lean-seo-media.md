# lean-seo media — WebP, `<picture>` wrapping, upload flattening, featured-image renaming

The `media` module (`modules/media/`) is code-driven with **no admin page and no options** — behavior is hardcoded via WordPress filters. Two concerns: image WebP delivery (`images.php`) and upload-path flattening + featured-image renaming (`uploads.php`). Its SEO relevance is image SEO + Core Web Vitals + keeping OG/featured-image URLs stable. Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) first.

## Images — WebP + `<picture>`

**Generation:**
- `wp_image_editors` filter → moves `WP_Image_Editor_Imagick` to front (better WebP).
- `image_editor_output_format` filter → maps `image/jpeg`→`image/webp`, `image/png`→`image/webp`, so **WP 6.1+ generates `.webp` sub-sizes natively** alongside originals on upload.

**`<picture>` wrap** — an output-buffer pass on `template_redirect` **priority -1** (`ob_start('lean_seo_webp_buffer')`, skips admin/feed/AJAX/REST). For every local `<img src=.jpg|.jpeg|.png>` whose sibling `.webp` exists on disk, it wraps: `<picture><source srcset="{webp}" type="image/webp">{original <img>}</picture>`. Existing `<picture>` blocks are stashed to avoid double-wrapping.

**Why output-buffer, not `.htaccess`:** the Accept-rewrite approach breaks behind CDNs that ignore `Vary: Accept` (Cloudflare Free/Pro default) — WebP bytes get cached under `.png/.jpg` URLs and served to non-WebP clients (Gmail's image proxy). The output-buffer `<picture>` markup is CDN-safe. The legacy `Lean SEO WebP` `.htaccess` block is auto-removed on `admin_init`.

**Coverage — reaches Voxel/Elementor output.** Because it's an output-buffer pass (not a content filter), it wraps `<img>` in post content, **Elementor widgets, Voxel templates**, and anything else in the rendered HTML — precisely what `wp_content_img_tag` can't reach. **Residual gap:** CSS `background-image` and JS-injected `<img>` stay PNG/JPG (needs an edge transform like Cloudflare Polish).

## Uploads — flatten + featured-image rename

**Flatten** — `upload_dir` filter at **PHP_INT_MAX** priority clears `subdir` and points `path`/`url` at the base dir, so new uploads skip `YYYY/MM` folders. Max priority so it runs after offload-media / multilingual filters. Companion `uploads_use_yearmonth_folders=0` option is set at plugin activation.

**Featured-image rename to `{post-slug}-{post-type}.{ext}`** — `lean_seo_rename_featured_image()` (`uploads.php`), triggered on:
- `added_post_meta`/`updated_post_meta` (only `_thumbnail_id`),
- `post_updated` prio 20 (slug change),
- `transition_post_status` (→ publish).

It computes a collision-free basename (<250 bytes), renames the main file + **all registered sizes** + the `.webp` companions, updates `_wp_attachment_metadata` + `update_attached_file`, then **rewrites old→new URLs across `post_content` and `_elementor_data`** (handles plain, JSON-escaped `\/`, and Elementor URLs) and flushes Elementor's CSS cache. Skips WP-CLI and autosave/revision.

## SEO impact & the `featured_img` seam

- Slug-named files (`{slug}-{post-type}.jpg`) improve image SEO/context.
- The renamed URL propagates to **OG image tags** and the **`featured_img` field** ("Featured image URL", in the shared field catalog) that the [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) §Meta and [`lean-seo-markdown.md`](lean-seo-markdown.md) surfaces read — so canonical image URLs stay consistent after a rename.
- WebP `<picture>` cuts image bytes → Core Web Vitals / LCP.

## Voxel / Elementor interaction

No Voxel-specific code, but two explicit touches worth knowing: the WebP output-buffer **targets Voxel-template-rendered `<img>`** (unreachable by content filters), and the rename path **patches Elementor `_elementor_data`** and clears Elementor's CSS cache. `featured_img` is a lean-seo field-catalog key, not a Voxel field.

## Gotchas

- Rename rewrites DB `post_content`/`_elementor_data` with `REPLACE()` — a slug that's a substring of another filename could over-match; the `basename LIKE` guard scopes it but review after bulk renames.
- Flatten at PHP_INT_MAX means any plugin re-adding subdirs after it loses; ordering-sensitive with offload-media.
- WebP wrapping only fires if the `.webp` sibling **exists on disk** — regenerate thumbnails after enabling for old media.
- `_thumbnail_id` handler skips WP-CLI, so bulk CLI imports won't auto-rename.
- Serving via `<picture>` markup means `Vary: Accept` is a non-issue, but full-page HTML caches must be purged after enabling (see [`lean-seo-purge.md`](lean-seo-purge.md)).
