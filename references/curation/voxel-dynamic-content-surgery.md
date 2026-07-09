# Voxel dynamic content surgery

Lesson from Klarc French-copy repair: rendered text often comes from Voxel CPT post meta, not static Elementor page content.

## Source map

Read the Voxel field model first:

```bash
wp option get 'voxel:post_types' > /tmp/voxel-post-types.json
```

Common fields by CPT:

- `exp` services: `h1`, `description`, `faq`, `heading-*`, `conversion-*`, `keyword-prefix`, `provider`.
- `geo` locations: `h1`, `content`, `description`, `qualities`.
- `testimonials`: `author-name`, `author-title`, `company-name`, `content`.
- `glossaire`: `h1`, `definition`, `content`, `faq`.
- `post` articles/guides: `h1`, `body`, `faq`.
- `events`: `title`, `excerpt`, `description`, `access_instructions`, `outcomes`, `target_audience`, `agenda`, `faq`.

Lean SEO/generated surfaces:

- `_lean_seo_title`
- `_lean_seo_description`
- `_lean_seo_md`
- `_lean_seo_uri` for URL source of truth; do not alter unless fixing permalink hierarchy.

## Correct workflow

1. Capture rendered bad snippet from browser or `.md` URL.
2. Map URL to post ID (sitemap, `wp post list`, or `_lean_seo_uri`).
3. Inspect source meta:
   ```bash
   wp post meta list <ID> --format=json
   ```
4. Patch exact Voxel field (`h1`, `description`, `content`, `body`, etc.).
5. Refresh/cache-clean generated Lean SEO surfaces only after the source field is clean.
6. Verify rendered page and `.md` output.

## Pitfall

Do not only patch `_elementor_data` when bad copy appears inside a loop/card/archive. The template may only contain dynamic tags (`@site(...)`, `@post(...)`), while the corrupted words live in Voxel post meta.
