# EF Parts: Media Handlers, Navigation, And Catalog

## Media sub-handlers (6, under `parts/media/`)

All extend the abstract `EF\Parts\Media\Type` base. Each handler is auto-discovered by `ef_discover_handlers()` keyed by its `key()` return value. Per-handler files: `parts/media/image.php`, `parts/media/video.php`, `parts/media/icon.php`, `parts/media/svg.php`, `parts/media/map.php`, `parts/media/color.php`.

### EF_Part_Media_Image

- **Class hierarchy**: `EF\Parts\Media\Image extends EF\Parts\Media\Type`
- **File**: `parts/media/image.php`
- **`key()`**: `'image'`
- **Props contributed** (via `props($prefix)`): `{prefix}_image` (Lenient_Image envelope — `{src: {id, url}, size}`)
- **Controls**: `EF\Controls\Image` (the slim Image_Control variant without Resolution dropdown)
- **Render**: emits `<img>` (or `<picture>` when source set is provided) with `loading="lazy"`, sizes, srcset
- **`supports_caption()`**: yes
- **`supports_fit()`**: yes
- **Used by**: every widget Media slot (card media/logo/byline_avatar, wrapper bg_media)
- **Gotchas**: ALWAYS emits both `src` AND `size` envelope cells (the resolver short-circuits on missing size). Lenient prop chain (Lenient_Image → Lenient_Image_Src → Lenient_Image_Attachment_Id + Lenient_Url) preserves dtag templates

### EF_Part_Media_Video

- **Class hierarchy**: `EF\Parts\Media\Video extends EF\Parts\Media\Type`
- **File**: `parts/media/video.php`
- **`key()`**: `'video'`
- **Props contributed**: `{prefix}_video_url` (Lenient_Url), `{prefix}_video_autoplay` (Boolean), `{prefix}_video_muted` (Boolean), `{prefix}_video_loop` (Boolean), `{prefix}_video_poster` (Lenient_Image)
- **Controls**: text + switches + image picker for poster
- **Render**: emits `<video>` for self-hosted, `<iframe>` for YouTube/Vimeo embeds (provider detection from URL pattern)
- **`supports_caption()`**: yes
- **`supports_fit()`**: yes (applied to underlying video / iframe)
- **Used by**: card media slot, wrapper bg_media
- **Gotchas**: muted autoplay required by browsers; the part doesn't enforce it but the default is `autoplay=false`

### EF_Part_Media_Icon

- **Class hierarchy**: `EF\Parts\Media\Icon extends EF\Parts\Media\Type` (DISTINCT from the `EF\Parts\Icon\Icon` static utility — same name, different file, different role)
- **File**: `parts/media/icon.php`
- **`key()`**: `'icon'`
- **Props contributed**: `{prefix}_icon` (String_Prop_Type — `library class` string) plus icon-color override
- **Controls**: `Vx_Icon` (icon picker + Voxel-tag bolt)
- **Render**: delegates to `EF\Parts\Icon\Icon::render_class()` for the actual emission
- **`supports_caption()`**: no
- **`supports_fit()`**: no
- **Used by**: card logo slot (often), anywhere an icon should occupy a Media slot
- **Gotchas**: the name clash with `EF\Parts\Icon\Icon` (static utility) is intentional — the Media handler IS-A "Type" that happens to render an icon, while `EF\Parts\Icon\Icon` is the icon-rendering primitive. The handler uses the primitive

### EF_Part_Media_Svg

- **Class hierarchy**: `EF\Parts\Media\Svg extends EF\Parts\Media\Type`
- **File**: `parts/media/svg.php`
- **`key()`**: `'svg'`
- **Props contributed**: `{prefix}_svg` (String_Prop_Type — inline SVG markup)
- **Controls**: `Vx_Svg` (SVG control + bolt)
- **Render**: emits SVG markup directly after `ef_sanitize_svg()` (via enshrined/svg-sanitize)
- **`supports_caption()`**: no
- **`supports_fit()`**: yes
- **Used by**: card media slot, wrapper bg_media (for vector backgrounds)
- **Gotchas**: SVG markup is sanitized at render — strips scripts, on* handlers, external refs

### EF_Part_Media_Map

- **Class hierarchy**: `EF\Parts\Media\Map extends EF\Parts\Media\Type`
- **File**: `parts/media/map.php`
- **`key()`**: `'map'`
- **Props contributed**: `{prefix}_map_*` — provider, center, zoom, marker config
- **Controls**: text/select for provider + center/zoom controls
- **Render**: emits `<div data-ef-map="...">` placeholder which the `ef-map` script (Leaflet or Google Maps based on `ef_map_providers()` config) initializes
- **`supports_caption()`**: yes
- **`supports_fit()`**: no (map fits its container by design)
- **Used by**: card media slot, wrapper bg_media (for "card with map" patterns)
- **Gotchas**: enqueues map assets via `ef_register_map_assets()` only when a Media slot's active type is `map` AND that handler is in the widget's `enabled_types`

### EF_Part_Media_Color

- **Class hierarchy**: `EF\Parts\Media\Color extends EF\Parts\Media\Type`
- **File**: `parts/media/color.php`
- **`key()`**: `'color'`
- **`default_enabled()`**: `false` — opt-in only; absent from a widget's enabled types unless explicitly added
- **Render**: emits no media layer (`has_content()` is always `false`) — the slot's colour is applied instead via the wrapper's variant modifier class (e.g. `.ef-wrapper--primary`), so a "media" slot can resolve to a flat brand colour with no `<img>`/`<svg>`
- **`supports_caption()`**: no
- **`supports_fit()`**: no
- **Used by**: wrapper `bg_media` (solid-colour backgrounds), card media slot (colour-block cards)

---
## Nav helper traits (2, under `parts/nav/`)

These are stateless trait classes (PHP traits) composed into `Nav_Item` to factor its row-resolution pipeline into named phases. Each trait owns one phase.

### Trait: Nav_Item_Roots

- **File**: `parts/nav/roots.php`
- **Used by**: `Nav_Item`
- **API**:
  - `flush_root($buffered_root): array` — closes the currently-open root, returning the resolved root entry with its accumulated sections / cols / links
- **Phase**: root grouping — runs after row expansion, before mega resolution
- **Gotchas**: stateless — caller maintains the buffer; trait just provides the flush operation

### Trait: Nav_Item_Mega

- **File**: `parts/nav/mega.php`
- **Used by**: `Nav_Item`
- **API**: resolves buffered rows into sections / cols / links per mega-panel layout. Each `root` row's buffered children become a mega panel (a 2D structure: sections × columns × links)
- **Phase**: mega resolution — runs after root grouping; emits the final per-root mega panel structure consumed by Twig
- **Gotchas**: indent map (`root/tree=0, section=1, heading=2, link=3`) is enforced here — out-of-order rows are coerced

---
## Part catalog (generated)

The table below is generated from `plugins/custom/elementor-framework/schemas/parts/*.schema.json` and the widget manifests' `parts:` arrays. Each row enumerates one Part schema with its owned props, configurable options, sub-parts it composes, and the widgets that compose it (direct includes plus transitive composition via sub-parts). The conceptual prose ABOVE — class hierarchy, contracts (`Renderable_Part` / `Context_Part`), render semantics, gotchas, and Media sub-handler / Nav-trait details — remains the source-of-truth for material the JSON SSOT cannot recover.

<!-- AUTO-GENERATED:ef-parts-index START — edit schemas, run `wpdev elementor:docs:gen`, do not hand-edit -->

20 Part schemas under `schemas/parts/` (sourced from `plugins/custom/elementor-framework/schemas/parts/*.schema.json`). The hand-written prose above is the source-of-truth for class hierarchy, contracts, and gotchas; this table enumerates the structural facts the JSON SSOT recovers (owned props, options, sub-parts, widget composers).

| Part | Title | Prefix | Owned props | Options | Sub-parts | Composed by |
|---|---|---|---|---|---|---|
| `action-slot` | Action slot | yes | 2 (`action_tooltip`, `action_type`) | — | — | `ef-navbar` (via sub-part) |
| `actions` | Buttons | yes | 1 (`ts_actions`) | `default_variant_key`, `embedded` | `action-row` | `ef-card`; `ef-navbar` (prefix=`cta`) |
| `banner` | Banner | yes | 3 (`action_label`, `background`, `message`) | — | `action-slot` | `ef-navbar` (prefix=`banner`) |
| `card-actions-embedded` | Card actions layout | no | 1 (`actions_embedded`) | — | — | `ef-card` |
| `card-full-height` | Card full height toggle | no | 1 (`full_height`) | — | — | `ef-card` |
| `card-logo-position` | Card logo position | no | 1 (`logo_position`) | — | — | `ef-card` |
| `card-media-overlay` | Card media overlay toggle | no | 1 (`media_overlay`) | — | — | `ef-card` |
| `form-button` | Form button text | no | 1 (`button_text`) | — | — | `ef-form` |
| `form-fields` | Form fields | no | 1 (`fields`) | — | `field-row` | `ef-form` |
| `form-honeypot` | Form honeypot | no | 1 (`honeypot`) | — | — | `ef-form` |
| `form-success-message` | Form success message | no | 1 (`success_message`) | — | — | `ef-form` |
| `headings` | Headings | yes | 1 (`content_blocks`) | — | — | `ef-card` |
| `layout` | Layout | no | 1 (`layout`) | `default_layout`, `layouts` | — | `ef-card` |
| `media` | Media slot | yes | 12 (`caption`, `enabled`, `fit`, `icon`, `image`, `image_alt`, `image_loading`, `map_pins`, `map_zoom`, `svg`, `type`, `video_url`) | `caption`, `default_enabled`, `default_type`, `enabled_types`, `type_labels` | — | `ef-card` (prefix=`media`); `ef-card` (prefix=`logo`); `ef-wrapper` (prefix=`bg_media`) |
| `nav-item` | Nav item | no | — | — | — | — |
| `navbar-breadcrumb` | Navbar breadcrumb toggle | no | 1 (`show_breadcrumb`) | — | — | `ef-navbar` |
| `navbar-nav-items` | Navbar nav items | no | 1 (`nav_items`) | — | `mega-row` | `ef-navbar` |
| `tag` | HTML tag | no | 1 (`tag`) | `allowed_tags`, `default_tag` | — | `ef-card`; `ef-wrapper` |
| `variant` | Variant | no | 1 (`variant`) | `default_variant`, `variants` | — | `ef-card`; `ef-form`; `ef-navbar` |
| `wrapper-settings` | Wrapper settings | no | 9 (`autoplay`, `bg_color`, `bg_pattern`, `cols`, `loop`, `mode`, `modifiers`, `tab_variant`, `template_id`) | — | — | `ef-wrapper` |

<!-- AUTO-GENERATED:ef-parts-index END -->

Notes:
- `ef-cal` and `ef-toc` are retired standalone widgets; their behavior lives in `ef-card.content_blocks` rows (`kind: calendar` / `kind: toc`).
- `ef-card` is the most part-heavy widget (Media×3 via `media`/`logo` + `byline_avatar` injected through Headings, plus Headings + Tags + Actions). The byline action is no longer an Action_Slot — it lives on the `byline` content-block row's action suite.
- `ef-wrapper` is not in the table (registered as an *element*, not a widget) — it composes Media (`bg_media`) + Action_Slot (root action) directly in PHP
- `ef-navbar` is the only consumer of `nav-item` / `banner`; its Nav_Item traits (Roots / Mega) are PHP-only and have no schema row
- `ef-form` is the only consumer of `field` (via `form-fields`); it does NOT compose `actions` (submit button is widget-owned via `form-button`)

---
