# EF Parts — exhaustive reference

`EF\Parts\*` are the composable building blocks that EF V4 widgets compose to avoid duplicating prop schemas, control wiring, render logic, and Twig context resolution. A widget like `ef-card` does not own the prop schema for its media slot, content-block stack, byline avatar, footer actions, or tag pills — those come from `Media`, `Headings` (which owns the `content_blocks` repeater + injected byline avatar), `Actions`, and `Tags` parts spread into the widget's `define_props_schema()`. The same `Media` part instance is reused three times inside `ef-card` (`media`, `logo`, `byline_avatar`) with different prefixes, and once inside `ef-wrapper` (`bg_media`). This is the entire point of the parts layer: one place to fix a bug, one place to add an option, one place to keep V4 envelope shapes consistent.

**Cross-reference**: see `ef-widgets.md` for the widgets that consume each part and which prefixes they use. The reverse index at the bottom of this file lists every (part × widget) edge.

**Source-of-truth files**: `plugins/custom/elementor-framework/includes/parts/` (23 files total under `parts/` excluding the action-handler subdir — 10 user-facing parts, 3 base contracts, 1 Media handler abstract (`Type`) + 6 Media handlers under `parts/media/`, 2 Nav helper traits under `parts/nav/`, plus `icon-functions.php`).

**Composite-repeater row expansion SSOT**: `EF\Parts\Base::expand_rows( array $settings, string $key, object $definition, string $outer_loop = '' ): array` (`parts/base.php`). Every part that owns a composite repeater (`Actions::render()`, `Headings::to_context()`, `Nav_Item::resolve_unified_rows()`, `Tags::to_context()`) flows rows through this single seam. It applies per-row `_vx_loop` expansion (via `ef_expand_definition()`) + `_vx_visibility` gating + `_ef_loop_transform` defaulting. See [`ef-helpers.md`](ef-helpers.md) for the underlying loop helper.

---

## The Base / Renderable / Context contract trio

Every part extends `EF\Parts\Base`; rendering parts also implement `EF\Parts\Renderable_Part`; context-resolving parts also implement `EF\Parts\Context_Part`. These three contracts define what a part is allowed to do.

### `EF\Parts\Base` (`parts/base.php`)

- **Role**: abstract base for all stateful parts
- **Constructor**: `__construct(Element_Base $widget, string $prefix = '', array $options = [])` — captures the parent widget (`$this->widget`), the key prefix (`$this->prefix`), and the per-instance options bag (`$this->options`)
- **Members**: `protected Element_Base $widget`, `protected string $prefix`, `protected array $options`
- **Helpers**:
  - `id(string $key): string` — returns `"{$prefix}_{$key}"` when prefix is set, else `$key`. Used everywhere a part needs to read a settings cell.
  - `key_prefix(): string` — returns `"{$prefix}_"` or `''`. Used when spreading prop arrays whose keys are already prefixed.
  - `to_html(array $settings, string $suffix = ''): string` — calls `render()` inside `ef_capture_output()`. Available only on parts that implement `Renderable_Part`.
- **Why prefix matters**: a single widget can compose the same part class multiple times. `Headings` inside `ef-card` instantiates a `Media` for `byline_avatar` AND `ef-card` itself instantiates a `Media` for `logo` AND for `media` — three live instances, three prefixes, zero key collisions because every prop / control / settings read goes through `id($key)`.

### `EF\Parts\Renderable_Part` (`parts/renderable_part.php`)

- **Role**: interface declaring the part can emit HTML directly
- **Signature**: `public function render(array $settings, string $suffix = ''): void` — implementations `echo` markup; callers wrap in `ef_capture_output()` when they need a string
- **Implementers**: `Actions`, `Banner`, `Field`, `Media`
- **NOT implementers**: `Action_Slot` (returns structured blocks via `to_link()` / `to_render_item()`, never HTML), `Headings` / `Tags` (return context arrays, Twig renders), `Heading_Enums` / `Icon` / `Nav_Item` (static utility classes, no per-instance render)

### `EF\Parts\Context_Part` (`parts/context_part.php`)

- **Role**: interface declaring the part produces a structured array for Twig context, not HTML
- **Signature**: `public function to_context(array $settings): array`
- **Implementers**: `Headings`, `Tags`
- **Why a separate contract**: Twig templates for `ef-card` consume `blocks`, `byline_avatar`, and `tags` as structured data (so the template can decide layout, dispatch on each block's `kind`, overflow grouping, etc.). HTML capture would force layout decisions into PHP and re-parse for the template — context arrays preserve the boundary.

---

## User-facing parts (10)

### EF_Part_Action_Slot

- **Class hierarchy**: `EF\Parts\Actions\Action_Slot extends EF\Parts\Base` (no Renderable, no Context — produces structured blocks)
- **File**: `parts/actions/action_slot.php`
- **Prop API**: `Action_Slot::props($prefix)` returns `ef_atomic_action_props($prefix)` — the full scalar action suite: `{prefix_}action_type` (Enum_String of `ef_atomic_action_types()`) plus every per-type field declared in `ef_action_field_specs()` (link, text, phone, email scopes; scope=`scalar` for single-action slots vs `both` for shared-with-repeater)
- **Control API**: `Action_Slot::controls($prefix)` returns `ef_atomic_action_controls($prefix)` — action-type select + dependency-gated per-type fields via `ef_show_when(['action_type'], <type>)`
- **Render contract**: NOT a `Renderable_Part`. Instead exposes two instance methods that produce structured blocks:
  - `to_link(array $settings): array` — `{href: string, attrs: array}` block (used to wrap the wrapper root / navbar banner action in `<a>`)
  - `to_render_item(array $settings, $widget, string $attr_key, string $label, string $variant): array` — `{tag, attrs, icon, label}` for button-style render (used by ts_actions footer rendering)
- **Context contract**: n/a (produces blocks consumed by the calling part / widget, not Twig directly)
- **Routes through**: `EF\Actions\Resolver::from_settings()` — single source of truth for parsing `{prefix_}action_type` + per-type fields into an action descriptor
- **Used by** (widgets):
  - `ef-wrapper` — root click-through action (slot `$action`, no prefix)
  - `ef-navbar` — banner action (prefix `banner_`, via `Banner`)
  - (the `ef-card` byline action is NO LONGER an Action_Slot — it lives on the `byline` content-block row's own action suite, resolved via `ef_action_block_from_row()`)
- **Loop expansion**: no — action slots are single-instance per widget; loop expansion happens at the `Action_Rows` (composite repeater) level, not here
- **Configuration knobs**: none — prefix-only; the action-type set and field specs are global
- **Gotchas**:
  - Single-slot action ≠ `Actions::repeater_control()` — they don't share storage. A slot writes to `{prefix_}action_type` etc., a repeater writes to `{prefix_}ts_actions` with per-row action cells
  - `to_link()` returns `href: ''` for `action_type=''` — callers must gate before wrapping in `<a>`

### EF_Part_Actions

- **Class hierarchy**: `EF\Parts\Actions\Actions extends EF\Parts\Base implements Renderable_Part`
- **File**: `parts/actions/actions.php`
- **Prop API**: not a prop spread — Actions owns a composite repeater. `Actions::repeater_control($prefix, $options)` builds a `Composite_Repeatable` bound to `{prefix_}ts_actions` (or `ts_actions` when prefix is empty), with row definition `Action`. The underlying prop `ts_actions` is registered as `Action_Rows` (`ef-action-rows` wire key)
- **Control API**: same — `repeater_control()` returns the control; the schema entry for `ts_actions` is declared inside the widget's `define_props_schema()`
- **Render contract**: `render(array $settings, string $suffix = ''): void` — reads `{prefix_}ts_actions`, resolves `embedded` mode (from `$options['embedded']`), dispatches each row via `ef_resolve_actions($widget, $rows, $embedded, $suffix)` to action handlers under `parts/actions/`, then renders the Twig partial `ef/partials/actions`
- **Context contract**: n/a (renders HTML directly)
- **Constructor options**:
  - `['embedded' => false]` — when `true`, forces button-mode rendering (used by navbar CTA which must always render as buttons, not anchor-style). Card actions read the per-instance `actions_embedded` enum (auto / yes / no).
- **Used by** (widgets):
  - `ef-card` — footer actions (`ts_actions` repeater)
  - `ef-navbar` — CTA actions (`cta_ts_actions` repeater, `embedded=true`)
- **Action handlers**: 34 files under `includes/parts/actions/` — one per `EF_ACTION_*` constant (representative set: link, get_directions, call, send_email, open_modal, scroll_to_section, action_gcal, action_ical, share_post, add_to_cart, promote_post, action_follow_post, action_follow, action_save, edit_post, delete_post, unpublish_post, publish_post, show_post_on_map, view_post_stats, go_back, select_addition, back_to_top, open_vx_inbox, open_vx_notifications, open_vx_cart, open_vx_user_menu) plus Inert base + Type registry
- **Loop expansion**: yes — per-row `_vx_loop` via the shared `Base::expand_rows($settings, 'ts_actions', new Action_Row_Definition())` seam; `Action_Row` extends `Loopable_Row` so each row carries its own `_vx_loop` / `_vx_visibility` / `_ef_loop_transform` cells
- **Configuration knobs**: `embedded` (force button mode)
- **Gotchas**:
  - `Actions::render_template()` is the SSOT partial dispatcher — Banner reuses it to render its single resolved action so the visual treatment matches widget footer actions

### EF_Part_Banner

- **Class hierarchy**: `EF\Parts\Banner extends EF\Parts\Base implements Renderable_Part`
- **File**: `parts/banner.php`
- **Owns**: an `Action_Slot` instance scoped to its own prefix (so the banner's action storage keys live under `{prefix_}` — typically `banner_`)
- **Prop API**: `Banner::props($prefix)` returns text props (`{prefix_message}`, `{prefix_action_label}`, `{prefix_background}`) plus Action_Slot props spread under the same prefix
- **Control API**: `Banner::controls($prefix)` returns text controls + Action_Slot controls + background-tone select (options come from `EF_Tokens::BANNER_TONES`)
- **Render contract**: `render()` is self-gating — when `{prefix_message}` is empty AND the Action_Slot resolves to no action, it renders nothing (no empty `<div>`). Otherwise emits a `.ef-navbar-banner` row with message, optional CTA, background tone class. Reuses `Actions::render_template()` for partial dispatch (consistency with footer actions)
- **Context contract**: n/a (renders HTML)
- **Used by** (widgets):
  - `ef-navbar` — top banner strip (prefix `banner_`)
- **Loop expansion**: no (single banner per navbar)
- **Configuration knobs**: prefix-only; tone palette is global
- **Gotchas**:
  - Self-gates on EMPTY message AND EMPTY action — set either to make it render. A blank-message banner with action will still render

### EF_Part_Field

- **Class hierarchy**: `EF\Parts\Field extends EF\Parts\Base implements Renderable_Part`
- **File**: `parts/field.php`
- **Constants**:
  - `DEFAULT_TYPE = 'text'`
  - `DEFAULT_ACCEPT = '.pdf,.doc,.docx'`
  - `TYPE_OPTIONS = ['heading','text','email','textarea','select','upload','checkbox']`
- **Prop API**: composite — the Form widget owns a `fields` prop typed as `Field_Rows`; per-row shape comes from `Row_Definitions\Field`. Field part itself doesn't spread props on the widget
- **Control API**: per-row controls declared in `Row_Definitions\Field` (label/placeholder/required/options/accept etc.)
- **Render contract**: `render(array $row, string $suffix = ''): void` — per-type branch:
  - `heading` dispatches to `ef/partials/heading` (same renderer used by card heading rows — visual consistency)
  - `text` / `email` emit `<input type=...>` with label, required attr, placeholder
  - `textarea` emits `<textarea>`
  - `select` emits `<select>` with `select_placeholder()` translated 'Select…' option
  - `upload` emits `<input type=file>` with accept attribute
  - `checkbox` emits `<input type=checkbox>` with adjacent label
- **Context contract**: n/a (renders HTML; Form widget passes per-row descriptors to Twig partial which calls Field render)
- **Used by** (widgets):
  - `ef-form` — every form field row
- **Loop expansion**: no — Field_Row is NOT loopable (`loopable=false` in row definition); each field is a discrete schema slot
- **Helpers**:
  - `select_placeholder(): string` — translated "Select…"
  - `hydrate_v4_row($row): array` — converts a V4 envelope row to V3-flat 7-key row (used by `ef_hydrate_v4_fields()` for AJAX submission handler)
- **Configuration knobs**: none on part; per-row via `Row_Definitions\Field`
- **Gotchas**:
  - The `heading` type is NOT a real input — it's a section header inside the form, rendered via the same partial as card heading rows. Required/placeholder/etc. are ignored for heading rows
  - `accept` defaults to `.pdf,.doc,.docx` for upload — override per row when needed

### EF_Part_Headings

- **Class hierarchy**: `EF\Parts\Headings\Headings extends EF\Parts\Base implements Context_Part`
- **File**: `parts/headings/headings.php`
- **Owns**: the `content_blocks` composite repeater (`Content_Block` row definition, `includes/row_definitions/content_block.php`); plus an optional injected `Media` instance for the byline avatar. (No `Action_Slot` is injected anymore — the byline's action lives on the `byline` row's own action suite.)
- **Prop API**: `Headings::props($prefix = '', $avatar_options = [])` spreads:
  - `content_blocks` — `Content_Block_Rows` (composite repeater of typed `Content_Block` rows; row family `ef-content-block-row(s)`)
  - Media props for `byline_avatar` (spread from `Media::props('byline_avatar', $avatar_options)`) — the card-level avatar slot, one per card
- **Control API**:
  - `Headings::repeater_control()` returns the `Composite_Repeatable` for `content_blocks` rows
- **Render contract**: n/a — implements `Context_Part`, not `Renderable_Part`
- **Context contract**: `to_context(array $settings): array` returns:
  ```
  {
    blocks: [
      // one resolved block per non-empty row, in row order; shape depends on kind:
      // heading  : {kind:'heading',   text, tag, visual_class, role, link:{href,attrs}, icon}
      // rich_text: {kind:'rich_text', body, link:{href,attrs}}
      // byline   : {kind:'byline',    primary, secondary, link:{href,attrs}}
      // separator: {kind:'separator', variant, spacing}
      // accordion: {kind:'accordion', text, body, accordion_open, tag, visual_class, role, link:{href,attrs}, icon}
      ...
    ],
    byline_avatar: { avatar, avatar_type } | null
  }
  ```
  - Each `kind` is the CONTENT discriminator (independent from the action suite's `type`, which is the ACTION discriminator). heading / accordion resolve their tag (h1..h6/p/span via `Heading_Enums::tag_kv_map()`), visual class via `Heading_Enums::visual_class()`, optional inline icon (via `Icon` part), and optional click-through link (via the row's action suite). The byline avatar is the single card-level Media slot (not a per-row cell).
  - `byline_avatar` resolves to `null` when the injected Media instance has no content; empty blocks drop out of `blocks` (`Content_Block::resolve_row()` returns null).
- **Used by** (widgets):
  - `ef-card` — content-block stack (heading / rich_text / byline / separator / accordion, in row order) + the card-level byline avatar
- **Loop expansion**: yes — per-row `_vx_loop` expansion via `Base::expand_rows($settings, 'content_blocks', new Content_Block_Row_Definition())` (which internally calls `ef_expand_definition()`). Content-block rows iterate the same way card-tag rows do, supporting Voxel post-loop iteration. A looped heading+body unit MUST be a single `accordion` block — a loop on a `heading` block plus a separate `rich_text` peer would not interleave.
- **Configuration knobs**:
  - `$avatar_options` — forwarded to `Media::props('byline_avatar', $avatar_options)`; card passes `['caption' => false]` to suppress caption controls on the avatar
- **Gotchas**:
  - The `accordion` kind retired the standalone `ef-accordion` widget (migration step 530); the collapsible heading+body unit now lives in a `content_blocks` row with `kind: accordion` (replaces the old `body_mode: accordion` on a heading row)
  - `Content_Block_Rows` is loopable AND carries the action suite, EXCEPT for `kind: separator` — the row schema's `$actionsWhen` hides the whole action suite (`type` + per-type cells + `icon`/`tooltip`) when `kind == separator`, so a separator is NEVER actionable

### EF_Part_Heading_Enums

- **Class hierarchy**: `EF\Parts\Headings\Enums` — final, static-only, pure metadata (extends nothing meaningful)
- **File**: `parts/headings/enums.php`
- **Prop API**: none — provides enum value sets consumed by `Row_Definitions\Content_Block` (the heading / accordion kinds) and `Row_Definitions\Field` (for the heading field type)
- **Control API**: none directly — controllers consume the kv maps
- **Render contract**: none
- **Context contract**: none
- **API**:
  - `tag_kv_map(): array` — returns `[h1=>'H1', h2=>'H2', ..., h6=>'H6', p=>'P', span=>'Span']`; canonical tag enum for heading rows
  - `style_kv_map(): array` — visual-style enum including label variants (`label`, `byline_label`); maps style key to translated label
  - `visual_class(string $value): string` — maps a style enum value to its CSS modifier class (e.g. `ef-heading--label`); used by Twig to apply visual class without leaking the enum value into the DOM
- **Used by**:
  - `Headings` (via `to_context()` for `tag` and `visual_class`)
  - `Row_Definitions\Content_Block` (for the tag + style select options on the heading / accordion kinds)
  - `Row_Definitions\Field` (heading-type form fields reuse the same enum)
- **Loop expansion**: n/a
- **Configuration knobs**: none — global enum
- **Gotchas**: `final` class, all methods static — do not extend; add new tags / styles by editing the maps directly

### EF_Part_Icon

- **Class hierarchy**: `EF\Parts\Icon\Icon` — final, static-only
- **File**: `parts/icon/icon.php`
- **Constants**:
- **API**:
  - `parse_string(string $s): array` — `{library, class}` parser (e.g. `'la-solid la-arrow-right'` → `{library:'la-solid', class:'la-arrow-right'}`)
  - `to_render_array(string $raw): array` — `{value, library}` in Elementor `Icons_Manager` shape (so existing Elementor renderers accept it)
  - `render_class(string $library, string $class, string $wrapper_class): string` — emits `<span class="{wrapper_class}"><i class="{library} {class}"></i></span>` or `<span><img></span>` for SVG-upload library
- **Companion**: `parts/icon/functions.php` provides 6 free `ef_atomic_icon_*` helpers (`ef_atomic_icon_prop`, `ef_atomic_icon_control`, `ef_atomic_icon_class_resolved_empty`, `ef_atomic_icon_resolve`, `ef_atomic_icon_placeholder`, `ef_atomic_icon_html`) — these are the public building blocks; widgets call them, not `Icon` directly
- **Render contract**: not a `Renderable_Part`; emits strings via static methods
- **Context contract**: none
- **Used by**:
  - Card heading rows (per-row icon slot)
  - Form field rows (heading type)
  - Nav items (per-item icon)
  - Anywhere a row definition declares an icon slot via `ef_atomic_icon_prop()` / `ef_atomic_icon_control()`
- **Loop expansion**: n/a — icon slots are leaf values; loop expansion happens at the row level
- **Configuration knobs**: none
- **Gotchas**:
  - `svg` library is the SVG-upload variant — emits `<img>`, not `<i>`. Round-trips via `ef_sanitize_svg()` for content security
  - `efn` is the EF-native icon library (custom EF icons); other `la-*` / `fa-*` libraries follow Line Awesome / Font Awesome conventions

### EF_Part_Media

- **Class hierarchy**: `EF\Parts\Media\Media extends EF\Parts\Base implements Renderable_Part`
- **File**: `parts/media/media.php`
- **Constants**:
  - `FIT_OPTIONS = ['cover', 'contain']`
  - `HANDLER_ORDER = ['image', 'video', 'icon', 'svg', 'map']` — display order in the type select
- **Sub-handlers** (under `parts/media/`): `Type` (abstract base), `Image`, `Video`, `Icon`, `Svg`, `Map`. Each handler owns its own `key()`, `label()`, `props($prefix)`, `controls($prefix)`, `has_content($settings)`, `render($settings)`, plus opt-in `supports_caption()` / `supports_fit()`. Handlers are auto-discovered via `ef_discover_handlers(Type::class, HANDLER_ORDER)`
- **Prop API**: `Media::props(string $prefix, array $options = [])` — composes:
  - `{prefix}_type` — Enum_String of enabled handler keys (default `'image'`, configurable via `$options['default_type']`)
  - per-handler prop spread for each handler in `$options['enabled_types']` (default: all 5)
  - cross-cutting `{prefix}_caption` — String_Prop_Type (only when `$options['caption'] !== false` AND at least one enabled handler `supports_caption()`)
  - cross-cutting `{prefix}_fit` — Enum_String of `FIT_OPTIONS` (only when at least one enabled handler `supports_fit()`)
- **Control API**: `Media::controls(array $options = [])` mirrors `props()` — type select + per-handler controls (dependency-gated via `ef_show_when(['{prefix}_type'], <handler-key>)`) + caption + fit
- **Render contract**: `render(array $settings, string $suffix = ''): void` — reads `{prefix}_type`, dispatches to the active handler's `render($settings)`, wraps with caption + fit class as appropriate
- **Instance methods**:
  - `type(array $settings): string` — active handler key
  - `has_content(array $settings): bool` — delegates to active handler
  - `caption(array $settings): string` — `{prefix}_caption` value
- **Context contract**: n/a (renders HTML; widgets call `to_html($settings)` to capture)
- **Used by** (widgets):
  - `ef-card` — three instances: `media` (main figure), `logo` (logo chip), `byline_avatar` (avatar in byline block, via `Headings`)
  - `ef-wrapper` — one instance: `bg_media` (background media slot, prefix `bg_media_`)
- **Loop expansion**: no — Media is a single-instance leaf; loop expansion happens upstream at the widget or row level
- **Configuration knobs**:
  - `default_type` — initial handler key (e.g. `'image'`)
  - `enabled_types` — restrict handler set (e.g. `['image']` for image-only slots like avatar)
  - `caption` — `false` to suppress caption controls entirely (avatars, backgrounds)
- **Gotchas**:
  - `HANDLER_ORDER` is the DISPLAY order; `enabled_types` filters but preserves this order
  - Caption + fit cells are HOISTED out of per-handler props because they apply cross-cutting (a caption on an image renders the same way as a caption on a video)
  - `Lenient_Image` / `Lenient_Image_Src` / `Lenient_Image_Attachment_Id` are used by Image handler so dtag-bearing image URLs round-trip without strict validation

### EF_Part_Nav_Item

- **Class hierarchy**: `EF\Parts\Nav\Nav_Item` — static-only; composes traits `Nav_Item_Roots`, `Nav_Item_Mega` from `parts/nav/`
- **File**: `parts/nav/nav_item.php`
- **Prop API**: none directly — Navbar widget owns `nav_items` as `Mega_Rows` (composite repeater of `Mega_Row`); Nav_Item resolves that data structure at render time
- **Control API**: none directly — controls come from `Row_Definitions\Mega`
- **Render contract**: not a Renderable_Part; produces structured data for Twig
- **API**:
  - `resolve_unified_rows(array $rows, string $widget_id, $queried): array` — `{desktop: [...], mobile: [...]}` — the SSOT pipeline transforming raw repeater rows into per-mode render payloads
- **Pipeline** (executed inside `resolve_unified_rows`):
  1. Row expansion — Voxel `_vx_loop` cells expanded through `Base::expand_rows($settings, 'nav_items', new Mega_Row_Definition())` (the shared seam that calls `ef_expand_definition()`)
  2. Root grouping — `Nav_Item_Roots::flush_root()` buffers sections under each `root` row; the authored nested menu tree is flattened into the flat root/section/heading/link buffer here, role assigned by indent (the former standalone tree-expansion phase was folded in here)
  3. Mega resolution — `Nav_Item_Mega` resolves buffered rows into sections / cols / links (per mega-panel layout)
  4. Per-mode payload — desktop gets the mega panel structure, mobile gets a flat collapsible tree
- **Row grammar** (5 types via `Row_Definitions\Mega`):
  - `root` — opens a top-level nav item (indent 0)
  - `section` — opens a sidebar (level 2, indent 1)
  - `heading` — opens a column under current section (indent 2)
  - `link` — appends to current column (indent 3)
  - `tree` — DFS-walks parent_post's descendants at render (indent 0)
- **Used by** (widgets):
  - `ef-navbar` — every nav item
- **Loop expansion**: yes — per-row `_vx_loop` (rows iterate over Voxel posts/terms) AND tree-row DFS expansion (synthetic per-descendant rows)
- **Configuration knobs**: none — static API; behavior driven by row data
- **Gotchas**:
  - `resolve_unified_rows()` is static — no instance state, can be called from anywhere (editor preview, frontend render, REST shell)
  - Traits are stateless helpers; if you add a new row type, add a trait or extend `Nav_Item_Mega`

### EF_Part_Tags

- **Class hierarchy**: `EF\Parts\Tags extends EF\Parts\Base implements Context_Part`
- **File**: `parts/tags.php`
- **Constants**:
  - `OVERFLOW_DEFAULT_SUFFIX = 'tags'`
  - `VISIBLE_MIN = 1`
  - `VISIBLE_MAX = 5`
- **Prop API**: `Tags::props($prefix = '')` returns:
  - `tags` — `Tag_Rows` (composite repeater of `Tag_Row`)
  - `tags_visible_count` — Enum_String `'1' | '2' | '3' | '4' | '5'`
  - `tags_overflow_label` — String_Prop_Type (suffix shown in the overflow "+N more" pill, default `'tags'`)
- **Control API**: `Tags::controls($prefix = '')` — composite repeater + visible-count select + overflow-suffix text input
- **Render contract**: n/a — implements `Context_Part`
- **Context contract**: `to_context(array $settings): array` returns:
  ```
  {
    has_tags,
    pills_visible: [{text, variant, link}, ...],
    pills_overflow: [{text, variant, link}, ...],
    overflow_count,
    overflow_label,
    more_label,
    overflow_group_label,
    overflow_unique_id   // stamped via wp_unique_id() per render
  }
  ```
- **Used by** (widgets):
  - `ef-card` — tag pills strip (top-right of card)
- **Loop expansion**: yes — per-row `_vx_loop` expansion via `Base::expand_rows($settings, 'tags', new Tag_Row_Definition())` (the shared seam that calls `ef_expand_definition()`); each tag row can iterate Voxel taxonomy terms or post tags
- **Configuration knobs**: prefix-only; overflow suffix configurable per instance via `tags_overflow_label`
- **Gotchas**:
  - `overflow_unique_id` is stamped via `wp_unique_id()` SO `aria-controls` doesn't collide when the same card is rendered multiple times inside a Voxel post loop (each iteration gets a fresh id)
  - `Tag_Rows` is loopable + has action suite — each tag row carries its own `_vx_loop` AND its own click-through action (so a tag can iterate AND link to a filtered archive)

---

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

## Generated row-surface tables

The tables below enumerate the per-row cell schemas (the prop surfaces parts expose to composite repeaters: `action-row`, `content-block-row`, `field-row`, `map-pin-row`, `mega-row`, `tag-row`). Generated from the resolved row sub-schemas in `cli/src/generated/widget-schemas.json` (sourced from `plugins/custom/elementor-framework/schemas/parts/rows/*.schema.json`). The per-part conceptual prose above remains the authoritative description of class hierarchy, contracts, composition rules, and render semantics — only the enumerative cell tables are generated here.

<!-- AUTO-GENERATED:ef-parts START — edit schemas, run `wpdev elementor:docs:gen`, do not hand-edit -->

### Row surface `action-row` — Action row

22 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `address` | `string` (dynamic) | `''` | Address for directions |
| `cal_desc` | `string` (dynamic) | `''` | Calendar event details |
| `cal_end_date` | `string` (dynamic) | `''` | Event end date and time |
| `cal_location` | `string` (dynamic) | `''` | Calendar event location |
| `cal_start_date` | `string` (dynamic) | `''` | Event start date and time |
| `cal_title` | `string` (dynamic) | `''` | Calendar event title |
| `cal_url` | `source` (dynamic) | — | Existing calendar file link |
| `cart_text` | `string` (dynamic) | `''` | Button text after adding |
| `email` | `string` (dynamic) | `''` | Email address to contact |
| `icon` | `string` | `''` | Icon shown on the button |
| `icon_active` | `string` (dynamic) | `''` | Icon shown after click |
| `label` | `string` (dynamic) | `''` | Button text |
| `label_active` | `string` (dynamic) | `''` | Text shown after click |
| `link` | `source` (dynamic) | — | Page or link to open |
| `modal_id` | `string` (dynamic) | `''` | On-page modal or saved template to open |
| `phone` | `string` (dynamic) | `''` | Phone number to call |
| `scroll_to` | `string` (dynamic) | `''` | Section to scroll to |
| `toast_message` | `string` (dynamic) | `''` | Short message after click |
| `tooltip` | `string` | `''` | Short hover text shown on the button |
| `type` | enum: `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `vote_upvote` \| `vote_downvote` | `action_link` | Choose what opens on click |
| `variant` | enum: `transparent` \| `white` \| `primary` \| `secondary` \| `negative` \| `positive` | `''` | Button colors |
| `vote_field_key` | `string` (dynamic) | `''` | Vote field to update |

### Row surface `content-block-row` — Content block row

53 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `accordion_open` | `boolean` | `false` | Open this accordion by default |
| `accordion_variant` | `string` | `transparent` | Accordion colors |
| `address` | `string` (dynamic) | `''` | Address for directions |
| `body` | `richtext` (dynamic) | `''` | Body text with formatting |
| `brand_color` | `string` | `primary` | Booking accent color |
| `byline_avatar_enabled` | `boolean` | `false` | Show this media area |
| `byline_avatar_fit` | enum: `cover` \| `contain` | `cover` | How the image fills the space |
| `byline_avatar_icon` | `string` | `''` | Choose an icon |
| `byline_avatar_image` | `image` | `[]` | Choose an image |
| `byline_avatar_image_alt` | `string` (dynamic) | `''` | Describe the image for screen readers |
| `byline_avatar_image_loading` | enum: `auto` \| `lazy` \| `eager` | `auto` | Choose when the image loads |
| `byline_avatar_type` | enum: `image` \| `video` \| `icon` | `image` | Choose what kind of media to show |
| `byline_avatar_video_url` | `source` (dynamic) | `''` | Video link or file |
| `byline_primary` | `string` (dynamic) | `''` | Main byline text, like author name |
| `byline_secondary` | `string` (dynamic) | `''` | Secondary byline text, like date or role |
| `cal_desc` | `string` (dynamic) | `''` | Calendar event details |
| `cal_end_date` | `string` (dynamic) | `''` | Event end date and time |
| `cal_location` | `string` (dynamic) | `''` | Calendar event location |
| `cal_start_date` | `string` (dynamic) | `''` | Event start date and time |
| `cal_title` | `string` (dynamic) | `''` | Calendar event title |
| `cal_url` | `source` (dynamic) | — | Existing calendar file link |
| `calendar_url` | `source` | — | Cal.com booking page link |
| `cart_text` | `string` (dynamic) | `''` | Button text after adding |
| `email` | `string` (dynamic) | `''` | Email address to contact |
| `group` | `string` | `''` | Group this tag belongs to |
| `group_name` | `string` | `''` | Group name |
| `group_over_media` | `boolean` | `false` | Place this group over the media |
| `group_overflow_suffix` | `string` (dynamic) | `''` | Word after the hidden tag count |
| `group_visible_rows` | `number` | `2` | Lines shown before +N appears |
| `hide_event_details` | `boolean` | `false` | Hide event details |
| `icon` | `string` | `''` | Optional leading icon shown on the heading line or in the tag pill |
| `icon_active` | `string` (dynamic) | `''` | Icon shown after click |
| `kind` | enum: `heading` \| `rich_text` \| `byline` \| `separator` \| `accordion` \| `tag` \| `group` \| `calendar` \| `toc` | `heading` | Choose what this content block shows |
| `label_active` | `string` (dynamic) | `''` | Text shown after click |
| `layout` | enum: `week_view` \| `month_view` \| `column_view` | `week_view` | Choose the layout |
| `link` | `source` (dynamic) | — | Page or link to open |
| `modal_id` | `string` (dynamic) | `''` | On-page modal or saved template to open |
| `phone` | `string` (dynamic) | `''` | Phone number to call |
| `scroll_to` | `string` (dynamic) | `''` | Section to scroll to |
| `separator_color` | `string` | `gray_light` | Divider color |
| `separator_spacing` | enum: `s` \| `m` \| `l` | `m` | Space above and below the divider |
| `separator_variant` | enum: `full` \| `centered` \| `partial` | `full` | Divider width |
| `slots_view_mobile` | `boolean` | `true` | Show times first on mobile |
| `style` | enum: `''` \| `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` | `''` | Title size |
| `tag` | enum: `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `p` \| `span` | `h3` | Choose the title level |
| `text` | `string` (dynamic) | `''` | Main text for this block |
| `theme` | enum: `light` \| `dark` \| `auto` | `light` | Light, dark, or automatic theme |
| `toast_message` | `string` (dynamic) | `''` | Short message after click |
| `toc_variant` | enum: `transparent` \| `primary` \| `secondary` \| `negative` \| `positive` | `transparent` | Table-of-contents link colors |
| `tooltip` | `string` | `''` | Tooltip cell — data only |
| `type` | enum: `''` \| `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `vote_upvote` \| `vote_downvote` | `''` | Choose what opens on click |
| `variant` | enum: `transparent` \| `white` \| `primary` \| `secondary` \| `negative` \| `positive` | `''` | Tag colors |
| `vote_field_key` | `string` (dynamic) | `''` | Vote field to update |

### Row surface `field-row` — Field row

6 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `accept` | `string` | `.pdf,.doc,.docx` | Allowed upload file types |
| `label` | `string` | `''` | Field label shown to visitors |
| `options` | `string` | `''` | Choices, one per line |
| `placeholder` | `string` | `''` | Hint inside the field |
| `required` | `boolean` | `false` | Require visitors to fill this in |
| `type` | enum: `heading` \| `text` \| `email` \| `textarea` \| `select` \| `upload` \| `checkbox` | `text` | Choose the kind of field |

### Row surface `map-pin-row` — Map pin row

5 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `address` | `string` (dynamic) | `''` | Address shown in the popup |
| `label` | `string` (dynamic) | `''` | Pin popup text |
| `lat` | `string` | `''` | Latitude |
| `lng` | `string` | `''` | Longitude |
| `location` | `string` (dynamic) | `''` | Pin address or coordinates |

### Row surface `mega-row` — Mega row

7 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `link` | `source` | — | Link this item opens |
| `loop_anchor` | `string` (dynamic) | `''` | Post used for repeated links |
| `loop_anchor_type` | enum: `''` \| `custom` | `''` | Choose the source for repeated links |
| `loop_overflow_suffix` | `string` (dynamic) | `''` | Word after hidden items |
| `loop_visible_rows` | `number` | `0` | Lines shown before +N appears |
| `meta` | `string` (dynamic) | `''` | Optional subtitle |
| `text` | `string` (dynamic) | `''` | Menu item text |

<!-- AUTO-GENERATED:ef-parts END -->
