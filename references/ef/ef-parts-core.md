# EF Parts: Base Contracts And User-Facing Parts

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
