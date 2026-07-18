# EF widget reference (atomic V4)

This file is the **per-widget cheat sheet** for the four EF widgets/elements actually registered by `elementor-framework` on disk: `ef-card`, `ef-form`, `ef-navbar`, `ef-wrapper`. For each one it captures the PHP class, the Twig template, the render-output shape, the full settings schema, the parts it composes, the Twig context it produces, the asset handles it enqueues, and its Voxel / dynamic-data integration surface. Source of truth: the live PHP under `plugins/custom/elementor-framework/includes/`.

## How to use this reference

- **Grep this file** when you need a quick reminder of "what props does this widget take?", "which parts does it compose?", "what asset handles does it enqueue?", "is `@post()` supported here?".
- **Read the committed SSOT** (`cli/src/generated/widget-schemas.json`) for the exact resolved prop envelopes — this is the preferred offline source. It's generated from the EF V4 registration SSOT under `plugins/custom/elementor-framework/schemas/` and CI-gated against drift, so it tracks HEAD without needing a running site.
- **Live-introspect** (`wpdev elementor:schema <site> ef-<name>` / `wpdev elementor:dump <site> ef-<name> --post <id> --json`) as the fallback — when you need to confirm a specific site's actually-registered shape, or that site runs a different EF version than this repo. The atomic V4 schema churns; this doc captures the **conceptual surface**, while the committed SSOT and the introspection commands return the **wire format** at HEAD.
- **Cross-references**:
  - Shared parts (`Action_Slot`, `Actions`, `Banner`, `Field`, `Headings`, `Heading_Enums`, `Icon`, `Media`, `Nav_Item`, `Tags`) live in `ef-parts.md`.
  - Golden fixtures currently exist for `ef-card` and `ef-wrapper` in
    `../../examples/`. Use live introspection for `ef-form` and `ef-navbar`.
  - The canonical V4 `$$type` / `value` envelope cheatsheet lives in `widgets.md`; this file refers back to it at the bottom rather than repeating it.

## Phantom widgets — DO NOT USE

The widgets named `ef-media`, `ef-button`, `ef-buttons`, `ef-breadcrumb`, `ef-button-group`, `ef-map-pin`, `ef-map`, `ef-cal`, and `ef-toc` **are not registered** by elementor-framework. No PHP file exists for any of them under `includes/widgets/` or `includes/elements/`. Discovery is glob-driven (`includes/discover.php` → `ef_glob_register_instances('includes/widgets', …)`), so anything without a file on disk is simply not a widget. If a doc, prompt, or fixture references one of those names, treat it as a bug — the actual surface is the four widgets/elements in this file.

---

## ef-card

- **PHP class**: `EF\Widgets\Card` (extends `EF\Atomic\Base_Widget`)
- **File**: `includes/widgets/card.php`
- **elType key**: `ef-card` — registered as an atomic **element**, so `_elementor_data[].elType` carries `"ef-card"` and there is **NO `widgetType` key** (same as `ef-wrapper` below). Writing a card with the classic `{elType:"widget", widgetType:"ef-card"}` shape makes the parent wrapper render an empty child while lint still passes. Only `ts-*` Voxel widgets use the classic `elType:"widget"` + `widgetType` shape.
- **Twig template**: `templates/card.html.twig` (registered as `ef/elements/card`)
- **Render output**: `<{tag}>` (default `div`; allowed = `EF_Tags::CONTENT ∪ {li, header}`) containing optional tag pills strip (top-right), media frame (figure/div with optional caption + click-through link wrap), logo chip, a content-block stack (the `content_blocks` repeater — interleaved heading / rich_text / byline / separator / accordion / calendar / toc blocks in row order), and a pre-rendered actions footer HTML fragment.
- **Settings schema**: see the [generated per-widget prop table](#generated-prop-tables) for the canonical prop, type, default, section list. Universal injected keys (`classes`, `attributes`, `col_span`, `_cssid`, `_vx_loop`, `_vx_visibility`, `_ef_loop_transform`) come from `ef_atomic_base_props()` and are described in [`widgets.md`](widgets.md#reserved-keys-universal--auto-merged-on-every-ef-widgetelement).
- **Parts used**: `EF\Parts\Media\Media` ×3 instances (`media`, `logo`, `byline_avatar`), `EF\Parts\Actions\Actions` (footer actions), `EF\Parts\Tags`, `EF\Parts\Headings\Headings` (now owns the `content_blocks` repeater + the injected `byline_avatar` Media slot — the byline's text + action live in its own `kind: byline` row, so there is no longer a `byline_action` Action_Slot on the card)
- **Twig context variables** (from `get_render_context()`): `has_body`, `has_heading`, `full_height`, `has_actions`, `has_media`, `blocks` (ordered list of resolved content blocks — each `{kind, …}`), `byline_avatar` (`{avatar, avatar_type}` or null — the card-level avatar slot, one per card), `actions_html` (pre-rendered string), `media` (`{inner_html, caption, fit_contain, wrap_link, link_attrs}` or null), `has_logo`, `logo_html`, `logo_position`, `logo_chip` (resolved via `voxel_addon_get_main_color`), `tags` (`{pills_visible, pills_overflow, overflow_count, more_label, overflow_unique_id, …}`)
- **Asset handles**: stylesheets = `['ef-card','ef-card-tags','ef-accordion','ef-prose','ef-tooltip','ef-footer','ef-separator','ef-toc']`; scripts = `['ef-vx-popup','ef-card-tags','ef-card-counter','ef-actions','ef-toc']`
- **Voxel / dynamic-data integration**: `$include_voxel_runtime_keys = true` **and** `$include_loop_runtime_keys = true`. Per-content-block-row and per-tag-row `_vx_loop` cells expand via `ef_expand_definition()`. `@post()`, `@site()`, `@tags()` round-trip natively through the Lenient prop family + `ef_render()` calls inside the Parts. The whole card can be replicated by a wrapper-level `_vx_loop`.
- **voxel-builder fixture**: `examples/ef-card.json` (golden, from a real post on `<site>`)
- **Gotchas**:
  - `actions_embedded=''` lets the variant decide — if the card variant defaults embedded, the footer goes inline; explicit `'yes'` / `'no'` overrides.
  - Tag pills `aria-controls` id is stamped via `wp_unique_id()` to dedupe across loop iterations — don't hardcode it.
  - The accordion is a `content_blocks` row with `kind: accordion` (a collapsible heading+body unit) — the same widget; it replaces the retired standalone `ef-accordion` (migration step 530). A looped heading+body unit MUST be a single `accordion` block (a loop on a `heading` block + a separate `rich_text` peer would not interleave).
  - Table of contents is a `content_blocks` row with `kind: toc`; migration step 998 absorbs retired standalone `ef-toc` nodes into the nearest card or morphs orphan TOCs into a minimal card.
  - Logo chip color resolves through `voxel_addon_get_main_color($post_id)`; if Voxel main-color resolver returns empty, the chip falls back to the default surface tone.
- **Live introspection**: `wpdev elementor:schema <site> ef-card` for the live shape; `wpdev elementor:dump <site> ef-card --post <id> --json` for a real instance.

---

## ef-form

- **PHP class**: `EF\Widgets\Form` (extends `EF\Atomic\Base_Widget`)
- **File**: `includes/widgets/form.php`
- **elType key**: `ef-form` (atomic element — `_elementor_data[].elType`, NO `widgetType`)
- **Twig template**: `templates/form.html.twig`; per-field rendering via `templates/partials/field.html.twig`
- **Render output**: A `<div>` host containing a `<form>` with hidden security fields (nonce, post_id, widget_id, signed timestamp `ef_t`, salted honeypot), the looped field rows, a submit `<button>` (action-surface class), a success message `<div>` (hidden by default), and an error `<div>`.
- **Settings schema**: see the [generated per-widget prop table](#generated-prop-tables). Per-row field shape comes from the `field-row` sub-schema in [`ef-parts-row-surfaces.md`](ef-parts-row-surfaces.md#row-surface-field-row--field-row).
- **Parts used**: `EF\Parts\Field` (`$field` instance — owns per-row rendering)
- **Twig context**: `post_id`, `widget_id`, `hidden_fields_html` (pre-rendered), `fields` (per-field descriptor arrays — type, name, field_id, label, placeholder, required, options, accept), `button_text`, `submit_class`, `success_message`, `success_message_html`
- **Asset handles**: stylesheets = `['ef-form']`; scripts = `[{handle:'ef-form', localize:'efForm'}]`; localized message bag from `ef_form_messages()`
- **Voxel / dynamic-data integration**: none — forms are WP-native. Submissions are handled by `includes/forms/submission-handler.php` → `ef_handle_form_submit` (AJAX). Field rows do NOT carry `_vx_loop` (the form is not meant to be replicated per Voxel post).
- **voxel-builder fixture**: none; use the live-introspection commands below.
- **Gotchas**:
  - Honeypot name is salted per-site via `ef_form_honeypot_name()` — never hardcode the field name in tests.
  - Signed timestamp `ef_t` is per-IP-prefix (`ef_form_ip_network_prefix()` returns /24 IPv4 or /64 IPv6) — proxy IP detection runs through `ef_form_client_ip()` against `ef_form_ip_in_trusted_proxies()`.
  - Per-IP rate limit runs through `ef_form_check_rate_limit($post_id, $widget_id)` — exceeded requests return JSON error from `ef_form_messages()`.
  - `Field_Row` types are gated to `['heading','text','email','textarea','select','upload','checkbox']` (see `Field::TYPE_OPTIONS`) — `phone` / `date` / `radio` are intentionally absent.
  - Upload accept defaults to `.pdf,.doc,.docx` (`Field::DEFAULT_ACCEPT`); MIME is enforced server-side via `ef_form_upload_accepts_file()`.
- **Live introspection**: `wpdev elementor:schema <site> ef-form` for the live shape; `wpdev elementor:dump <site> ef-form --post <id> --json` for a real instance.

---

## ef-navbar

- **PHP class**: `EF\Widgets\Navbar` (extends `EF\Atomic\Base_Widget`)
- **File**: `includes/widgets/navbar.php`
- **elType key**: `ef-navbar` (atomic element — `_elementor_data[].elType`, NO `widgetType`)
- **Twig template**: `templates/navbar.html.twig`; per-item via `templates/partials/nav-item.html.twig`
- **Render output**: A `<nav>` containing an optional banner strip, a `.ef-navbar` flex row (logo + UL menu + CTA buttons + mobile-drawer toggle), a `<dialog>` mobile drawer with header/body/footer, and an optional `.ef-navbar-breadcrumb` row.
- **Settings schema**: see the [generated per-widget prop table](#generated-prop-tables). The nav-item row grammar (`root` / `section` / `heading` / `link` / `tree`) comes from the `mega-row` sub-schema in [`ef-parts-row-surfaces.md`](ef-parts-row-surfaces.md#row-surface-mega-row--mega-row).
- **Parts used**: `EF\Parts\Actions\Actions` (`$cta`, force-button-mode), `EF\Parts\Banner` (`$banner`), `EF\Parts\Nav\Nav_Item` (via static `resolve_unified_rows()`)
- **Twig context**: `widget_id`, `drawer_id`, `logo_html` (`wp_get_attachment_image` of theme-mod custom_logo), `logo_link_url`, `nav_label`, `home_label`, `menu_toggle_label`, `drawer_label`, `drawer_title`, `drawer_close_label`, `nav_items` (desktop), `nav_items_mobile`, `cta_html`, `cta_mobile_html`, `show_breadcrumb`, `breadcrumb_html` (from `do_shortcode('[breadcrumb]')`), `banner_html`
- **Asset handles**: stylesheets = `['ef-navbar','ef-navbar-banner','ef-breadcrumb','ef-tooltip']`; scripts = `[{handle:'ef-navbar', localize:'efNavbar'},{handle:'ef-vx-popup'}]`; `$base_display = 'block'` override
- **Voxel / dynamic-data integration**: nav items support per-row `_vx_loop` expansion; `tree` row type DFS-walks the Voxel descendant post tree at render time (flattened into the root/section buffer during root grouping, `EF\Parts\Nav_Item_Roots`). CTA + banner actions accept every Voxel action type registered in `ef_action_types()`.
- **voxel-builder fixture**: none; use the live-introspection commands below.
- **Gotchas**:
  - Logo image is read from `get_theme_mod('custom_logo')` — there is **no per-instance image setting**. Change the site logo in Customizer / theme mod, not in the widget.
  - The `tree` row type DFS-walks `parent_post`'s descendant post tree at render — heavy on large hierarchies. Use a `_vx_loop` on a `link` row instead if you want a flat menu of children.
  - Mega rows have an implicit indent: `root/tree=0, section=1, heading=2, link=3`. Misordering the rows (a `link` before any `root`) silently drops the link.
  - Breadcrumb row depends on a `[breadcrumb]` shortcode being registered (Voxel theme provides it). If missing, `breadcrumb_html` is empty.
  - The mobile `<dialog>` uses native `<dialog>` API — fallback styling required for browsers without dialog support.
- **Live introspection**: `wpdev elementor:schema <site> ef-navbar` for the live shape; `wpdev elementor:dump <site> ef-navbar --post <id> --json` for a real instance.

---

## ef-wrapper

- **PHP class**: `EF\Elements\Wrapper` (extends `EF\Atomic\Container_Element` → `EF\Atomic\Base_Element` → `Atomic_Element_Base`)
- **File**: `includes/elements/wrapper.php`
- **elType key**: `ef-wrapper` (atomic element — `_elementor_data[].elType`, NO `widgetType`) — registered via `register_element_type`
- **Twig template**: `templates/wrapper.html.twig`
- **Render output**: `<{tag}>` (default `div`; allowed = `EF_Tags::STRUCTURAL`; `mode=modal` overrides to `<dialog>`; non-empty action URL overrides to `<a>`) containing an optional `.ef-bg-media` first-child, an optional modal close `<form method="dialog">`, then `inner_html` — which is either the captured child render or the template body when `template_id` resolves.
- **Settings schema:**

  | Prop | Type | Default | Brief |
  |---|---|---|---|
  | `tag` | `Enum_String` | `'div'` | enum = `EF_Tags::STRUCTURAL` |
  | `mode` | `Enum_String` | `''` | enum `['','modal','template']` — `template` swaps inner_html for a saved Elementor library template render |
  | `variant` | `Enum_String` | `'transparent'` | From `EF_Tokens::SURFACE_VARIANTS` |
  | `template_id` | `String_Prop_Type` | `''` | Library template ID — gated by `ef_show_when(['mode'],'template')` |
  | `reverse_mobile` | Boolean (`ef_atomic_boolean(false)`) | `false` | Flip flex/grid order on mobile |
  | `cols` | `Responsive_String` (via `ef_cols_pair()`) | `''` | `grid-template-columns` track list, per breakpoint |
  | `action_*` | spread from `Action_Slot::props()` | — | `action_type`, `action_link`, + every per-type field from `ef_action_field_specs()` |
  | `bg_media_*` | spread from `Media::props('bg_media')` | type=`image` | Background media slot |
  | (universal) | — | — | `ef_atomic_base_props()` |

- **Parts used**: `EF\Parts\Media\Media` (`$background` slot, prefix `bg_media`), `EF\Parts\Actions\Action_Slot` (`$action` slot)
- **Base styles** (`define_base_styles()`): a single `min-width: 30px` Style_Variant. Display, grid-template-columns, and min-mobile=1fr lock live in `base.css` under a compound selector — only `min-width` lives in PHP because it can't be expressed via a class rule.
- **Twig context**: `tag`, `root_attrs` (pre-rendered attribute string including class + id + style + href + data-ef-* attrs + action attrs), `is_modal`, `close_label`, `bg_media_html`, `inner_html`
- **REST shell endpoint**: `/ef/v1/render-wrapper-shell` returns the `get_shell_data()` payload (tag, classes, base_style_class, style, id, href, attrs, is_modal, bg_media_html). The editor JS applies this to the live ef-wrapper element rather than swapping `innerHTML` — preserves the Marionette views of children inside the wrapper.
- **Asset handles**: stylesheets = `['ef-wrapper']`; scripts = `['ef-modal']`
- **Voxel / dynamic-data integration**: `$include_voxel_runtime_keys = true`; supports `_vx_loop` for the full loop-wrapper pattern (children replicate per iteration). `Action_Slot` accepts all Voxel action types. The bg_media slot accepts dtag image URLs via `Lenient_Url`.
- **voxel-builder fixture**: `examples/ef-wrapper.json` (golden, from a real post on `<site>`)
- **Gotchas**:
  - `mode='modal'` swaps the rendered tag to `<dialog>` regardless of `tag` setting. Don't set `tag='section'` and expect a section when mode is modal.
  - `mode='template'` requires a valid `template_id` (an Elementor library post). If the template doesn't exist, `inner_html` is empty (silent fail). Check with `ef_render_template($template_id)` directly when debugging.
  - When `action_link` is set and non-empty, the wrapper renders as `<a>` instead of the configured `tag` — this short-circuits semantic tags like `<section>` or `<aside>`. Wrap a `<button>` action in a child instead if you need a non-anchor wrapper.
  - The `_vx_loop` pattern replicates the wrapper **and all its children** per iteration. Pair with `_ef_loop_transform` to filter/sort/reverse the iteration list.
  - Background media is rendered as the first DOM child, **inside** the wrapper, not as a CSS background — so it participates in stacking context and z-index. Use `position: absolute` styling on the `.ef-bg-media` to layer it behind content.
- **Live introspection**: `wpdev elementor:schema <site> ef-wrapper` for the live shape; `wpdev elementor:dump <site> ef-wrapper --post <id> --json` for a real instance.

---

## Quick-pick widget table

| Need this UI? | Use this widget |
|---|---|
| A repeatable content card with heading, body, media, byline, tags, footer actions | `ef-card` |
| An accordion (collapsible heading + body) | `ef-card` with a `content_blocks` row of `kind: accordion` |
| Embed a Cal.com booking widget | `ef-card` with a `content_blocks` row of `kind: calendar` |
| A native form (text, email, textarea, select, upload, checkbox, heading separators) | `ef-form` |
| Site header / navbar with mega menu, mobile drawer, CTA buttons, optional banner, optional breadcrumb | `ef-navbar` |
| Auto-built table of contents that scrolls-spies the current heading | `ef-card` with a `content_blocks` row of `kind: toc` |
| A structural container — `<section>`, `<article>`, `<aside>`, `<header>`, `<footer>`, etc. | `ef-wrapper` |
| A modal dialog | `ef-wrapper` with `mode='modal'` |
| A click-through container (the whole block is an `<a>`) | `ef-wrapper` with `action_link` set |
| Render a saved Elementor library template inline | `ef-wrapper` with `mode='template'` + `template_id` |
| Replicate any block per Voxel iteration | wrap it in an `ef-wrapper` and set `_vx_loop` |
| A background-image / background-video / SVG / icon / map under content | `ef-wrapper` with `bg_media_*` props |
| Click-through buttons / multiple footer CTAs on a card | `ef-card.ts_actions` (composite Action_Rows) |
| Buttons row on the navbar | `ef-navbar.cta_ts_actions` |
| Promotional message strip above the navbar | `ef-navbar` banner_* props |
| Tag pills on a card with overflow popover | `ef-card.tags` + `tags_visible_count` |

For shared building blocks the widgets compose (Action_Slot, Actions, Banner, Field, Headings, Media, Nav_Item, Tags, Icon), see `ef-parts.md`.

## Atomic V4 envelope

Every prop value at rest uses the `{ $$type: '<key>', value: <payload> }` envelope. EF widgets work with a mix of upstream Elementor primitives (`string`, `boolean`, `number`, `size`, `image`, `image-src`, `image-attachment-id`, `url`, `link`, `classes`, `attributes`), Voxel-owned envelopes (`vx`, `vx-loop`, `vx-visibility`, `vx-dynamic-css`), and EF-owned envelopes (`ef-loop-transform`, `ef-responsive-string`, `ef-responsive-boolean`, plus per-row-definition `ef-<key>-row` / `ef-<key>-rows` pairs for `action`, `content-block`, `tag`, `mega`, `field`, `map_pin`).

For the canonical envelope cheatsheet (payload shapes, lenient-vs-strict notes, who owns each `$$type`), see the [`$$type` envelope cheatsheet](widgets.md#type-envelope-cheatsheet) section of `widgets.md`. Use `wpdev elementor:schema <site> ef-<name>` to introspect the live envelope shape on HEAD.

## Generated prop tables

The tables below are generated from `cli/src/generated/widget-schemas.json` (the SSOT corpus produced by `wpdev elementor:codegen`). They enumerate every top-level prop on every EF V4 atomic widget — name, type/enum, default, control section, and a one-line brief sourced from the schema's `description`. `ef-wrapper` is not in the SSOT corpus (it registers as an *element*, not a widget) — see the prose section above for its schema.

<!-- AUTO-GENERATED:ef-widgets START — edit schemas, run `wpdev elementor:docs:gen`, do not hand-edit -->

### `ef-card` — generated prop table

PHP class `EF\Widgets\Card`. 4 props.

| Prop | Type / enum | Default | Section | Brief |
|---|---|---|---|---|
| `content_blocks` | repeater `ef-content-block-rows` | `[]` | content | Add and order card content |
| `full_height` | `boolean` | `true` | settings | Make cards in a row match height |
| `tag` | enum: `div` \| `section` \| `article` \| `aside` \| `li` \| `header` | `div` | settings | Choose what kind of container this is |
| `variant` | enum: `transparent` \| `white` \| `primary` \| `primary_light` \| `secondary` \| `secondary_light` \| `positive` \| `negative` | `white` | content | Choose the colors |

### `ef-form` — generated prop table

PHP class `EF\Widgets\Form`. 6 props.

| Prop | Type / enum | Default | Section | Brief |
|---|---|---|---|---|
| `button_text` | `string` | `Envoyer` | submit | Submit button text |
| `fields` | repeater `ef-field-rows` | `[]` | fields | Add and order fields |
| `honeypot` | `boolean` | `true` | submit | Add hidden spam protection |
| `recipients` | repeater `ef-recipient-rows` | `[]` | recipients | Users or addresses receiving a copy of this form submission |
| `success_message` | `string` | `Merci ! Votre message a bien été envoyé.` | submit | Message shown after sending |
| `variant` | enum: `transparent` \| `white` \| `primary` \| `primary_light` \| `secondary` \| `secondary_light` \| `positive` \| `negative` | `primary` | content | Choose the colors |

### `ef-navbar` — generated prop table

PHP class `EF\Widgets\Navbar`. 26 props.

| Prop | Type / enum | Default | Section | Brief |
|---|---|---|---|---|
| `banner_action_address` | `string` | `''` | content | Address for directions |
| `banner_action_cal_desc` | `string` | `''` | content | Calendar event details |
| `banner_action_cal_end_date` | `string` | `''` | content | Event end date and time |
| `banner_action_cal_location` | `string` | `''` | content | Calendar event location |
| `banner_action_cal_start_date` | `string` | `''` | content | Event start date and time |
| `banner_action_cal_title` | `string` | `''` | content | Calendar event title |
| `banner_action_cal_url` | `source` | — | content | Existing calendar file link |
| `banner_action_cart_text` | `string` | `''` | content | Button text after adding |
| `banner_action_email` | `string` | `''` | content | Email address to contact |
| `banner_action_icon_active` | `string` | `''` | content | Icon shown after click |
| `banner_action_label` | `string` | `''` | content | Banner button text |
| `banner_action_label_active` | `string` | `''` | content | Text shown after click |
| `banner_action_link` | `source` | — | content | Page or link to open |
| `banner_action_modal_id` | `string` | `''` | content | On-page modal or saved template to open |
| `banner_action_phone` | `string` | `''` | content | Phone number to call |
| `banner_action_scroll_to` | `string` | `''` | content | Section to scroll to |
| `banner_action_toast_message` | `string` | `''` | content | Short message after click |
| `banner_action_tooltip` | `string` | `''` | content | Short hover text |
| `banner_action_type` | enum: `''` \| `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `vote_upvote` \| `vote_downvote` | `''` | content | Choose what opens on click |
| `banner_action_vote_field_key` | `string` | `''` | content | Vote field to update |
| `banner_background` | enum: `primary` \| `positive` \| `negative` | `primary` | content | Announcement bar colors |
| `banner_message` | `string` (dynamic) | `''` | content | Announcement text |
| `cta_ts_actions` | repeater `ef-action-rows` | `[]` | content | Add and order buttons |
| `nav_items` | repeater `ef-mega-rows` | `[]` | nav_items | Add and order menu links |
| `show_breadcrumb` | `boolean` | `false` | settings | Show page path links |
| `variant` | enum: `transparent` \| `white` \| `primary` \| `primary_light` \| `secondary` \| `secondary_light` \| `positive` \| `negative` | `transparent` | content | Choose the colors |

### `ef-wrapper` — generated prop table

PHP class `EF\Elements\Wrapper`. 18 props.

| Prop | Type / enum | Default | Section | Brief |
|---|---|---|---|---|
| `bg_color` | `string` | `transparent` | settings | Background color token |
| `bg_media_fit` | enum: `cover` \| `contain` | `cover` | content | How the image fills the space |
| `bg_media_icon` | `string` | `''` | content | Choose an icon |
| `bg_media_image` | `image` | `[]` | content | Choose an image |
| `bg_media_image_alt` | `string` (dynamic) | `''` | content | Describe the image for screen readers |
| `bg_media_image_loading` | enum: `auto` \| `lazy` \| `eager` | `auto` | — | Choose when the image loads |
| `bg_media_map_pins` | repeater `ef-map-pin-rows` | `[]` | content | Add pins to the map |
| `bg_media_map_zoom` | `string` | `14` | content | Starting map zoom level |
| `bg_media_svg` | `svg` | — | content | Choose an uploaded vector image |
| `bg_media_type` | enum: `''` \| `color` \| `image` \| `video` \| `icon` \| `svg` \| `map` | `''` | content | Choose what kind of media to show |
| `bg_media_video_url` | `source` (dynamic) | `''` | content | Video link or file |
| `cols` | `string` (responsive) | `1fr` | settings | Columns for each screen size |
| `mode` | enum: `''` \| `modal` \| `template` \| `tabs` \| `carousel` \| `pagination` \| `masonry` \| `fullscreen` | `''` | settings | Choose how this wrapper works |
| `modifiers` | `string` (responsive) | `''` | settings | Active modifiers per breakpoint (comma-joined flags): sticky, reversed |
| `rows` | `number` (responsive) | `1` | settings | Number of rows per page |
| `tab_variant` | enum: `transparent` \| `white` \| `primary` \| `primary_light` \| `secondary` \| `secondary_light` \| `positive` \| `negative` | `primary` | settings | Active tab colors |
| `tag` | enum: `div` \| `main` \| `section` \| `article` \| `aside` \| `header` \| `footer` \| `nav` | `div` | settings | Choose what kind of container this is |
| `template_id` | `string` | `''` | settings | Saved template to show here |

<!-- AUTO-GENERATED:ef-widgets END -->
