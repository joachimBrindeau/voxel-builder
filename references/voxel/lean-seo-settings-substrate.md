# lean-seo settings substrate — the shared config + Voxel-resolution layer

Every lean-seo SEO surface (meta, schema, markdown, crawl, permalinks, linking) sits on **one shared substrate**: a module registry, a uniform option store, a per-target field catalog, and a Voxel guard layer. Learn this once; each surface reference then only documents its own token dialect and resolvers. This is the seam that makes lean-seo **site-agnostic** — no surface hardcodes a CPT, field, or relation; they all read the live `voxel:post_types` config through the catalog.

Plugin root referenced below: `plugins/custom/lean-seo/`.

## Module registry — one entry per SEO surface

`includes/modules.php` → `lean_seo_modules()` is the SSOT. Each module declares `files`, `categories` (= `lean_seo_{category}` option keys), a `page_title`, and a `render` callback.

| Module slug | Admin page | Option categories | Surface reference |
|---|---|---|---|
| `meta` | Meta | `meta` (option `lean_seo_meta`) | [`lean-seo-metadata.md`](lean-seo-metadata.md) |
| `schema` | Schemas | *(per-target options `lean_seo_schema:{target}` + index `lean_seo_schema_targets` — NOT a `schema` category)* | [`lean-seo-schema.md`](lean-seo-schema.md) |
| `llms` | Markdown Fields | *(none — uses `lean_seo_markdown_field_maps`, a JSON string)* | [`lean-seo-markdown.md`](lean-seo-markdown.md) |
| `crawl` | Crawl | `crawl`, `noindex`, `ai_crawler` (+ list settings in `tweak`) | [`lean-seo-crawl-permalinks.md`](lean-seo-crawl-permalinks.md) |
| `permalinks` | Permalinks | `permalink_default`, `permalink_nesting` (+ `_lean_seo_uri` post meta) | [`lean-seo-crawl-permalinks.md`](lean-seo-crawl-permalinks.md) |
| `linking` | Internal Linking | `linking` | [`lean-seo-crawl-permalinks.md`](lean-seo-crawl-permalinks.md) |
| `code` | Code | `tag` | [`lean-seo-code.md`](lean-seo-code.md) |
| `redirects` | Redirects | *(custom `lean_seo_redirects` DB table)* | [`lean-seo-redirects.md`](lean-seo-redirects.md) |
| `media` | *(none)* | *(no options — filter-driven)* | [`lean-seo-media.md`](lean-seo-media.md) |
| `maintenance` | *(enabled-state IS the switch)* | *(none)* | [`lean-seo-maintenance.md`](lean-seo-maintenance.md) |
| `performance` | Performance | `preconnect` (+ purge bridge) | [`lean-seo-purge.md`](lean-seo-purge.md) |

Site variables live in `lean_seo_variable` (the `variable` category — **autoloaded**), read via `lean_seo_var()` (order: WP-native fields > `variable` option > baked defaults). On Voxel sites every var is published as a dynamic tag `@site(seo.<key>)` (via the `voxel/dynamic-data/groups/site/properties` filter in `includes/voxel.php`).

A module is loaded only when enabled (`lean_seo_module_enabled($slug)`, option `lean_seo_modules`). Toggling a module purges the full-page cache (`lean_seo_purge_all()` / `litespeed_purge_all`). Disabled modules hide their categories from the settings UI (`lean_seo_modules_hidden_categories()`).

## Option store — `lean_seo_{category}` with typed rows

`includes/settings-store.php` is the uniform backend. **Each category is one `wp_option` named `lean_seo_{category}`**, holding a `key => {value, type, description}` map:

```json
{
  "title_template_org": { "value": "%title% %sep% %sitename%", "type": "text", "description": "" },
  "og_type_org":        { "value": "article", "type": "enum:...", "description": "" }
}
```

Accessors (use these, never `get_option` directly):

```php
lean_seo_settings_get_value( $category, $key, $default );   // read one
lean_seo_settings_set( $category, $key, $value, $type, $description );  // write one
lean_seo_settings_update( $category, $key, [ 'value' => ... ] );        // partial update
lean_seo_settings_map( $category );                          // flatten to key => value
```

`tweak` and `variable` categories autoload (read every front-end request); everything else does not (`lean_seo_settings_is_autoload()`). Writes flush the per-request memo via `lean_seo_settings_flush_cache()`.

**Markdown** is the exception: its config is a standalone `lean_seo_markdown_field_maps` option (a JSON string of per-CPT maps), not a settings-store category. **Schema** is also special: one option per target (`lean_seo_schema:{target}`) + an index option, not a `schema` category. **Redirects** uses its own DB table.

**Never give a module a settings category whose `lean_seo_{category}` option name is already owned by another subsystem.** `schema` is the cautionary case: the category option `lean_seo_schema` collides with the Schema Builder's legacy monolithic config, whose `plugins_loaded` migration deletes that option when it does not parse as a schema config. Seeded settings rows therefore vanished on the next request and were re-seeded on every upgrade — silently, since seeding reported success. When auditing settings coverage, verify a seeded row still reads back **on a later request**, not just after the write.

## The field catalog — the agnostic seam

`includes/available-fields.php` is what makes every picker Voxel-aware without hardcoding. Two entry points:

- **`lean_seo_content_targets( $include_taxonomies = true )`** → `['post:{slug}' => {kind,slug,label}, 'tax:{slug}' => ...]` for every public post type + taxonomy. This enumerates the CPT tabs / scope selectors on every surface.
- **`lean_seo_available_field_groups( $target = '' )`** → grouped field map for a target:
  ```
  'Core fields'  => [ title, excerpt, content, date, modified, author, permalink, featured_img ]
  'Voxel fields' => [ <every voxel field key> => 'Label (key)' ]   // present only on Voxel sites
  'Meta fields'  => [ <post-meta keys currently in content> ]
  ```

Voxel fields come from **`lean_seo_decode_voxel_post_types_option()`** (reads `voxel:post_types`, array-or-JSON) walked recursively by **`lean_seo_collect_voxel_field_labels()`** — so repeater sub-fields and nested keys are all surfaced. Filter: `lean_seo_available_field_groups`.

**Consequence:** to add a new field to any surface's picker on any site, you register it as a Voxel field or post-meta — the catalog picks it up automatically. Never edit plugin code to expose a site's field.

## Voxel guard layer — `includes/voxel.php`

All Voxel access goes through these wrappers, which **degrade to null / passthrough when Voxel is absent** (guarded on `lean_seo_has_voxel()` → `VoxelCompat::has_post_class()`). This is why the plugin runs unchanged on non-Voxel WordPress.

| Function | What it resolves |
|---|---|
| `lean_seo_voxel_post( $post )` | `\Voxel\Post` wrapper or null |
| `lean_seo_voxel_field_value( $post, $key )` | A field's value **through Voxel's own field class** (`get_field()->get_value_from_post()`) — correctly reads repeaters, relations, locations, not raw meta |
| `lean_seo_get_related_ids( $post_id, $field_key )` | Published post IDs behind a Voxel **relation** field |
| `lean_seo_voxel_render( $value, $post )` | Resolves `@site(...)`, `@post(...)`, `@author(...)` dynamic tags for a **specific** post context |
| `lean_seo_voxel_render_groups( $post )` | Overrides Voxel's post/author render groups so tags resolve against the target post, not the global queried post (critical in sitemaps / llms.txt / CLI where there is no loop) |
| `lean_seo_voxel_profile_id_for_author( $author_id )` | The Voxel `profile` CPT post linked to a WP user |

### Author ↔ profile canonicalization (a non-obvious seam)

Voxel rewrites `author_base` to the `profile` CPT slug, so `/profile/<nicename>` URLs **are** WP author archives. `includes/voxel.php`:
- filters `lean_seo_schema_author_context` to render the `profile` schema config against the linked profile post on author archives;
- canonicalizes author URLs to the linked profile permalink (else sitemaps/canonical point at the CPT permalink while theme links point at `/profile/...` — duplicate URLs).

Sites linking authors to a different CPT override the `lean_seo_schema_author_context` filter.

## Token dialects — one per surface (do not mix)

Each surface accepts a **different** substitution syntax. Getting the dialect wrong is the most common misconfiguration:

| Surface | Dialect | Resolver |
|---|---|---|
| Meta (title/desc/archive) | `%token%` — plus the `%vx(@post(key))%` wrapper for full Voxel dynamic tags | `post-values.php` expansion + `lean_seo_template_tokens()` picker |
| Markdown dtag_fields | `@post(key)`, `@author(tag)` + special `@post(lean_seo:rendered_html)` | `lean_seo_voxel_render()` |
| Schema field source | `prefix:key\|transform\|transform` (22 prefixes) — NOT `%token%`, NOT bare `@post()` | `lean_seo_schema_resolve_source()` |
| Raw Voxel dynamic text (anywhere passed through the renderer) | `@site()/@post()/@author()` | `lean_seo_voxel_render()` |

The `%token%` picker (`includes/template-tokens.php`) and every other field picker draw their options from the same field catalog above, so the available `%key%` / `voxel:key` / `@post(key)` values are always the live per-CPT field set.

## Common admin editing model

Surfaces render as a WP admin submenu page (the module's `render` callback). The rich surfaces (Meta, Schema, Markdown) use **per-CPT tabs** + field-picker comboboxes populated from `lean_seo_available_field_groups()`, saved over AJAX with the `lean_seo_settings_nonce` action (dispatcher `wp_ajax_lean_seo_settings`). WP-CLI writes go straight through `lean_seo_settings_set()` / `wp option update lean_seo_markdown_field_maps`.
