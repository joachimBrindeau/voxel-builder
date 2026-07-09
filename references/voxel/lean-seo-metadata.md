# lean-seo metadata — title, description, canonical, OG/Twitter, per-CPT

The `meta` module (`modules/meta/`) owns the `<title>`, meta description, canonical URL, Open Graph, Twitter Card, and pagination link tags. Config persists in the **`lean_seo_meta`** option via the shared store. Read [`lean-seo-settings-substrate.md`](lean-seo-settings-substrate.md) first — this file assumes the store, field catalog, and Voxel guard layer.

## Config model — kind × scope keys

`includes/config.php` → `lean_seo_meta_setting_kinds()` is the SSOT of what's configurable. Each **kind** has `label`, `scoped` (bool), `value_type`, `default`, `description`:

| Kind constant | Key stem | Scoped? | Default | Purpose |
|---|---|---|---|---|
| `TITLE_TEMPLATE` | `title_template` | yes | `%title%` | SERP `<title>` template |
| `DESC_TEMPLATE` | `desc_template` | yes | `%excerpt%` | meta description template |
| `ARCHIVE_TITLE` | `archive_title` | yes | `%title%` | archive `<title>` |
| `ARCHIVE_DESC` | `archive_desc` | yes | `%description%` | archive description |
| `DEFAULT_OG_IMAGE` | `default_og_image` | yes | — | per-type OG image fallback (attachment id) |
| `GLOBAL_OG_IMAGE_ID` | `default_og_image_id` | **no** | — | site-wide OG image fallback |
| `OG_TYPE` | `og_type` | yes | `article` | Open Graph object type (enum) |
| `TITLE_SEPARATOR` | `title_separator` | no | — | the `%sep%` glyph |
| `TWITTER_CARD_TYPE` | `twitter_card_type` | no | — | Twitter card type |
| `NOINDEX_POST_TYPE` / `NOINDEX_SEARCH` / `NOINDEX_404` / `NOINDEX_PAGINATED` / `NOINDEX_ARCHIVE_SUBPAGES` / `NOINDEX_EMPTY_TAXONOMIES` / `NOINDEX_PASSWORD_PROTECTED` | `noindex_*` | mixed | — | robots noindex rules |

**Scoped** kinds get one row per content target; the stored key is `<kind>_<scope>` built by `lean_seo_build_meta_setting_key( $kind, $scope )` where `$scope` is the **bare post-type slug** (e.g. `title_template_org`) or `taxonomy-<slug>` for taxonomies (e.g. `og_type_places`, `desc_template_post`, `title_template_taxonomy-category`). Empty scope = global. Parse back with `lean_seo_parse_meta_setting_key()`. Unscoped kinds store a single bare-kind key. Read via `lean_seo_meta_setting_value($kind,$scope,$default)`.

Stored rows look like:

```json
{
  "title_template_org": { "value": "%title% %sep% %sitename%", "type": "text", "description": "" },
  "desc_template_org":  { "value": "%excerpt%", "type": "text", "description": "" },
  "og_type_profile":    { "value": "profile",  "type": "enum:website,article,profile,...", "description": "" },
  "title_separator":    { "value": "|", "type": "text", "description": "" },
  "default_og_image_id":{ "value": "1234", "type": "attachment_id", "description": "" }
}
```

Required kinds are **non-deletable** (`lean_seo_is_required_meta_setting_key`; AJAX delete blocked) and auto-injected into the settings UI even when unset (`lean_seo_settings_with_required_meta_rows()`), so every public type shows title/desc/og_type/og_image controls.

## Token dialect — `%token%`

Title/description templates use `%token%` placeholders, NOT `@post()`. The insertable catalog is `includes/template-tokens.php` → `lean_seo_template_tokens()`, grouped as:

- **Field tokens** — `%title%`, `%excerpt%`, `%content%`, `%author%`, plus every **Voxel field** as `%{key}%` and every post-meta key (regex `/%([a-zA-Z0-9_:-]+)%/`). Sourced from the shared `lean_seo_available_field_groups($target)`, so on a Voxel site the picker lists that CPT's Voxel fields automatically.
- **`%vx(...)%` wrapper** — a RankMath-style Voxel-dynamic-tag wrapper: `%vx(@post(h1))%`, `%vx(@author(display_name))%`, `%vx(@site(seo.org_phone))%` → run through `lean_seo_voxel_render`. Use this for full Voxel dynamic-data expressions inside a `%token%` template; a bare `%h1%` only does a `get_post_meta` fallback.
- **Site tokens** — `%site_name%`, `%site_description%`, `%site_url%` (+ archive aliases `%sitename%`, `%sitedesc%`, `%site%`, `%description%`/`%desc%`), resolved via `lean_seo_var()`.
- **Structure tokens** — `%sep%` (the configured separator), `%page%` (pagination "Page N").

Templates are resolved by `lean_seo_post_template_text_value()` (singular) / `lean_seo_text_template_value()` (archives). Defaults: title `%title%`, desc `%excerpt%`, archive_title `%title%`, archive_desc `%description%`, og_type `article`.

### Voxel resolution inside `%token%`

When a `%{voxel_field}%` token expands, the value comes through the post-value layer which, for Voxel fields, routes to Voxel's own field resolution — so a `%location%` or repeater-derived token resolves the same way Voxel renders it, not as raw meta. Free-form `@post(...)`/`@site(...)` dynamic tags embedded in a template are additionally passed through `lean_seo_voxel_render()`.

## Voxel/profile specifics + fallback chains

- **Title** `lean_seo_get_singular_title($id)`: `title_template_<type>` (rendered) → else the title meta key `lean_seo_title_meta_key()` (**defaults to `'h1'`**, the Voxel H1 field; filter `lean_seo_title_meta_key`) → else post `title`.
- **Description** `lean_seo_get_post_description($id)`: `desc_template_<type>` → `lean_seo_description_meta_key()` (filter, default `''` — opt-in Voxel field) → `get_the_excerpt` → site tagline.
- **OG image**: post thumbnail → `default_og_image_<type>` → global `default_og_image_id` → site icon.
- **Geo tags**: `lean_seo_get_geo_meta` reads Voxel geo meta keys `geo-lat/geo-lng/geo-street/geo-city/geo-zip/geo-region/phone/email` (filter `lean_seo_geo_meta_keys`).
- **Author archives** render as the linked Voxel `profile` post (see substrate §author↔profile). So the meta title/description/canonical for `/profile/<nicename>` derive from the `profile` CPT's scoped meta settings and its Voxel fields.
- **Canonical** (`modules/meta/inc/canonical.php`) — lean-seo removes WP core + Elementor Pro canonicals and emits its own for all page types, using the parent-derived permalink; author URLs canonicalize to the profile permalink.

## Per-post overrides vs type defaults

- **Per-post overrides** — post meta `_lean_seo_description`, `_lean_seo_canonical`, `_lean_seo_noindex`, `_lean_seo_og_image` (constants in `config.php`); the result of `lean_seo_get_data()` is filterable via `lean_seo_data`. The description producer also reads the per-post Voxel `h1`/description field.
- **Type/scope defaults** live in `lean_seo_meta` (this file's model).
- **Global defaults** — bare-kind `lean_seo_meta` rows + site variables (`lean_seo_variable`).

## Configure via WP-CLI

```bash
# set a scoped title template for the 'org' CPT (scope = bare slug)
wp eval 'lean_seo_settings_set("meta", lean_seo_build_meta_setting_key(LEAN_SEO_META_KIND_TITLE_TEMPLATE, "org"), "%title% %sep% %sitename%", "text");'
# read it back
wp option get lean_seo_meta
```

## Gotchas

- **Wrong dialect**: putting `@post(field)` bare into a title template does nothing useful — meta wants `%field%` or the `%vx(@post(field))%` wrapper. Conversely `%field%` in markdown/schema won't resolve.
- **Scope key format**: scoped keys are `<kind>_<scope>` with a **bare slug** (`title_template_org`), taxonomies `taxonomy-<slug>`. Always build via `lean_seo_build_meta_setting_key`; don't hand-write `post:org`-style keys — they won't match the renderer.
- **`title_meta_key='h1'` default is Voxel/Klarc-specific** — on a non-Voxel or differently-keyed site set the `lean_seo_title_meta_key` filter (return `''` to fall straight to `post_title`). This is the key agnostic caveat.
- **Required rows**: an empty `lean_seo_meta` doesn't mean "unconfigured" — required kinds are materialized in the UI from `lean_seo_meta_setting_kinds()` defaults and can't be deleted.
- **OG image is an attachment ID**, not a URL.
- **Limits**: title trimmed to `document_title_limit` (default 60, filterable), description to `LEAN_SEO_DESC_LIMIT=155`, both with word-boundary/dangling-word trimming (EN + FR locale sets).
