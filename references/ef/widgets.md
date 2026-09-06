# Widget Catalog (router)

For per-widget detail see [`ef-widgets.md`](ef-widgets.md); for the shared parts they compose see [`ef-parts.md`](ef-parts.md); for the helpers they call see [`ef-helpers.md`](ef-helpers.md); for **dedicated `ef-wrapper mode:masonry` vs CSS Grid bento** (automatic CSS Columns packing vs explicit responsive numeric `col_span` + `row_span`) see [`masonry.md`](masonry.md); for **section background rhythm** (segmenting a page with alternating `transparent`/`secondary` tints via the wrapper `variant`, and the clash rule that keeps tints off colored-card sections) see [`section-rhythm.md`](section-rhythm.md). This file is the **router** — quick "which widget?" lookup plus the canonical cross-widget references (reserved keys, `$$type` envelopes, EF surface-churn timeline) that span every widget.

## EF widget catalog → per-widget detail

Only four EF widgets/elements are registered on disk (`ef-card`, `ef-form`,
`ef-navbar`, and `ef-wrapper`). Anything else (`ef-media`, `ef-button`,
`ef-buttons`, `ef-breadcrumb`, `ef-button-group`, `ef-map-pin`, `ef-map`) is a
**phantom** — no PHP file exists; do not dispatch. See
[`ef-widgets.md#phantom-widgets--do-not-use`](ef-widgets.md).

The atomic-widget catalog below is generated from `cli/src/generated/widget-schemas.json` (the SSOT corpus produced by `wpdev elementor:codegen`). `ef-wrapper` is registered as an *element* (not a widget), so it lives in the prose, not the table. For per-widget detail see [`ef-widgets.md`](ef-widgets.md).

<!-- AUTO-GENERATED:widgets START — edit schemas, run `wpdev elementor:docs:gen`, do not hand-edit -->

4 EF V4 atomic widgets registered under `schemas/widgets/` (the SSOT corpus). `ef-wrapper` is registered as an *element* and is documented in the prose above.

| Widget | Title | Props | Row surfaces | PHP class |
|---|---|---|---|---|
| `ef-card` | Card | 4 | `content-block-row`, `filter-item-row`, `map-pin-row`, `sort-item-row` | `EF\Widgets\Card` |
| `ef-form` | Form | 8 | `field-row`, `recipient-row` | `EF\Widgets\Form` |
| `ef-navbar` | Navbar | 12 | `action-row`, `map-pin-row`, `mega-row` | `EF\Widgets\Navbar` |
| `ef-wrapper` | Wrapper | 17 | `map-pin-row` | `EF\Elements\Wrapper` |

<!-- AUTO-GENERATED:widgets END -->

Other surfaces (not in the SSOT corpus):

- `ef-wrapper` — [`ef-widgets.md#ef-wrapper`](ef-widgets.md#ef-wrapper) — structural container, **Voxel-loop host**, modal, template-render, click-through hull, bg-media frame.
- `e-div-block` / `e-flexbox` — upstream Elementor atomic primitives. Use only when EF wrapper features (loops, html_tag enum, bg_media, action suite) aren't needed.

**Wrapping rule:** never wrap a single `ef-card` in any container at the root of `_elementor_data`. The site-wide `wpdev elementor:strip:wrappers <site> [--fix]` tool detects and removes such wrappers at any depth; snapshot first and run only for an approved cleanup.

## Voxel theme widgets (`ts-*`, NOT introspectable)

These are Voxel-theme widgets — they aren't in `wpdev elementor:schema`. To get a known-good shape, dump a real production instance:

```bash
wpdev elementor:dump <site> ts-post-feed --post <prod_post_id> --json
```

| Widget | Use for | Settings shape |
|---|---|---|
| `ts-post-feed` | Paginated/filtered post grids, related posts, manual curation, carousels | Dump from production |
| `ts-search-form` | Search/filter UI connected to a feed (`ts_post_to_feed` references the feed widget's `id`) | Dump from production |
| `ts-print-template` | Render another Elementor template inline (`ts_template_id`) | Dump from production |
| `ts-term-feed` | Taxonomy term grids | Dump from production |
| `ts-map`, `ts-timeline`, `ts-orders`, `ts-profile-wall`, `ts-create-post`, `ts-login`, `ts-messages` | Voxel-native UI | Customize in Voxel admin; preserve unchanged during page builds |

**Connection integrity:** when a page has both `ts-search-form` and `ts-post-feed`, the form's `ts_post_to_feed` references the feed's element `id`. If the feed widget is recreated with a new `id`, update `ts_post_to_feed` to match. Same for `connect_map` (form → map).

**Template ID references** in feed settings (`ts_card_template__<type>`, `ts_manual_card_template__<type>`, `ts_manual_posts[].post_id`, `ts_template_id`): post IDs on the target site. Cross-site migration requires remap; same-site stays valid.

## EF loop vs ts-post-feed

Both render lists of posts. Pick by capability:

| Use EF widget + `_vx_loop` (simpler DOM) | Use `ts-post-feed` |
|---|---|
| Static section showing N items | Pagination (load-more, prev-next) |
| Custom card design via `ef-card` children | Reuses Voxel's card-template assignment |
| Want minimal DOM (just repeated wrappers) | Connected to `ts-search-form` |
| Sort via `_ef_loop_sort` enum (query schema for current values) | Voxel filters / search / index-table queries |
| Simple counter, no filtering UI | Carousel / nowrap mode |

EF loop pattern (widget-level): the EF widget itself (e.g. `ef-card`, `ef-wrapper`) carries `_vx_loop: @site(loop_<type>)` and is replicated per iteration via `loop-controller.php`'s `before_render` hook. Children inside the widget reference `@site(loop_<type>.field)`. For the row-level alternative (one row of a composite repeater iterates while the rest of the widget stays fixed), see [`voxel-tags.md`](../voxel/voxel-tags.md) §Placement decision.

## Map media runtime (Leaflet / Google) — LSCache-safe lazy load

`ef-card` media/logo slots and `ef-wrapper.bg_media` can render `*_type: map` via the `EF\Parts\Media\Map` handler. This is **not** a standalone `ef-map` widget; it is a media type inside the host widget. The emitted DOM is a `.ef-map` div with `data-locations` + `data-zoom`, hydrated by `assets/js/frontend/map.js`.

Best-practice runtime contract (source: elementor-framework `includes/media/map.php` + `assets/js/frontend/map.js`):

- Keep provider SDKs out of WordPress dependency rewriting and LSCache delay/lazy rewrites. `ef-map` should be the only enqueued WP handle; it receives localized `googleMapsUrl` / `leafletUrl` and injects the chosen provider script itself when needed.
- Hydrate only after the map is near the viewport **and** the element is measurable (`getBoundingClientRect().width/height > 0`, not `visibility:hidden`). Hidden accordions/tabs/modals, deferred Elementor sections, and cache-delayed JS can otherwise create a zero-size Leaflet/Google map that never paints correctly.
- After hydration and after any size change, run provider resize repair: `map.invalidateSize()` for Leaflet; `google.maps.event.trigger(map, 'resize')` for Google. Schedule after layout (`requestAnimationFrame` twice) so tile math sees final dimensions.
- Use a single in-flight promise per provider script and marker attributes (`data-ef-leaflet`, `data-ef-google-maps`) to avoid duplicate SDK loads when multiple map media slots enter view together.
- If Google fails and Leaflet is configured/available, fallback through the same runtime loader rather than assuming `window.L` was already loaded by a WP dependency.

When a map "doesn't load when it comes into view", check this contract before changing pins or Voxel data. The usual bug is not data: it is provider JS being delayed/rewritten by LSCache or the map initializing while still zero-size. Verification should include scrolling the map into view, checking console/network for the provider script, and asserting rendered map container dimensions plus Leaflet tiles or Google map panes.

## Retired widgets / props — DO NOT dispatch

Two categories: (a) **widgets that once existed and were removed by a migration step** — old `_elementor_data` may still reference them; the migration step rewrites them. (b) **phantom widgets that never had a PHP file** — they show up only in stale prompts / docs / memory; the actual surface is the four widgets/elements at the top of this file.

| Retired surface | Category | Replacement | Migration step / fix |
|---|---|---|---|
| `ef-accordion` widget | removed | `ef-card` `content_blocks` rows with `kind: accordion` | step 530 (`530-accordion-widget-to-card-headings.php`) |
| `ef-icon-heading` widget | removed | `ef-card` with heading enabled | step that rewrites `ef-icon-heading` → `ef-card` on save |
| `ef-media` | phantom (never registered) | `ef-card.media` slot (composes `EF\Parts\Media\Media`) OR `ef-wrapper.bg_media` | rewrite tree; no migration step exists |
| `ef-button` / `ef-buttons` / `ef-button-group` | phantom (never registered) | `ef-card.ts_actions` (card footer) / `ef-navbar.cta_ts_actions` (navbar) / `ef-wrapper` action suite (any wrapper) | rewrite tree; no migration step exists |
| `ef-breadcrumb` | phantom (never registered) | `ef-navbar.show_breadcrumb` (built-in via `do_shortcode('[breadcrumb]')`) | rewrite tree; no migration step exists |
| `ef-map` / `ef-map-pin` | phantom (never registered) | `ts-map` (Voxel theme widget) for the map; `ef-card.map_pin_row` for in-card pin badges | rewrite tree; no migration step exists |
| Legacy scalar `link` prop on `ef-wrapper` (widget alive, only this prop shape retired) | removed prop | Action suite: `action_type` + `action_link` + per-type fields | step 580 |
| Voxel `_voxel_loop` panel section on EF widgets | replaced surface | General → Dynamic affordance band → `_vx_loop` | EF strips Voxel sections at filter priority 110 |
| Voxel `_voxel_visibility_rules` panel section on EF widgets | replaced surface | General → Dynamic affordance band → `_vx_visibility` | same |

Whenever a session references one of these by name (because the user remembered it from before, or another doc still mentions it), translate to the replacement before any work — never dispatch a subagent on a retired or phantom widget name.

## Reserved keys (universal — auto-merged on every EF widget/element)

The base `EF_Atomic_Widget` / `EF_Atomic_Element` injects these props on every widget without each widget redeclaring them — see `includes/atomic-base-widget.php::ef_atomic_base_props()`. The `_cssid` text field, the `col_span` responsive selector, and the **Dynamic affordance band** (3 icon pickers bound to `_vx_loop` / `_vx_visibility` / `_ef_loop_transform`) all live in an auto-injected **General** Section that fronts every widget panel — replacing Voxel's three (VX) sections (`_vx_loop`, `_vx_visibility`, `_vx_dynamic_css`) which EF strips at filter priority 110 (Voxel registers them at 100). Query `wpdev elementor:schema <site> <widget>` for the live `reservedKeys` list.

| Key | Type | Purpose |
|---|---|---|
| `classes` | classes | Custom CSS class list. Slot 0 is reserved by the EF style system on `ef-card` / `ef-wrapper` (local-style id). |
| `attributes` | attributes | HTML attributes — marked `Overridable::ignore` so component overrides don't strip it. |
| `col_span` | responsive number | CSS Grid placement, range 1–10; `0` = auto. Renders `ef-col-span-{n}` / breakpoint classes. Use with normal-grid bento, not dedicated masonry. See [`masonry.md`](masonry.md). |
| `row_span` | responsive number | CSS Grid row span, range 1–10; `0` = auto. Renders `ef-row-span-{n}` / breakpoint classes. Legacy string/non-responsive shapes are not canonical writes. See [`masonry.md`](masonry.md). |
| `_cssid` | string \| vx | CSS `id` attribute. For Voxel posts: `{$$type: vx, value: '@post(types.slug)-@post(slug)'}`. Lives in the auto-injected General section now (no longer per-widget Settings). **Anchor target = `_cssid`, never raw HTML `id="..."` inside text content** — Elementor strips hand-written `id="..."` attributes during render. To make an anchor target like `#essentiel`, set the widget's `_cssid` to `essentiel`; the rendered DOM gets `id="essentiel"` on the wrapper. |
| `_vx_loop` | vx-loop (Voxel) | Iteration scope. Modern name (preferred). Voxel-runtime registered. |
| `_vx_visibility` | vx-visibility (Voxel) | Conditional render rules. Modern name (preferred). |
| `_ef_loop_transform` | ef-loop-transform | EF-owned filter / sort / reverse parity for atomic widgets — sibling of Voxel's `_vx_loop`. |

Legacy keys still recognized by the helpers' loop expansion (`_voxel_loop`, `_voxel_loop_offset`, `_voxel_loop_limit`, `_voxel_visibility_rules`, `_voxel_visibility_behavior`) and by EF-loop additions (`_ef_loop_sort`, `_ef_loop_initial`, `_ef_loop_more_label`, `_ef_loop_less_label`) round out the loop surface. New JSON should use `_vx_*` and `_ef_loop_*`; legacy `_voxel_*` is preserved on read for V3 compat but not the canonical write target.

## `$$type` envelope cheatsheet

Every prop value in V4 atomic widgets uses a `{$$type, value}` envelope. The cardinal envelopes:

| Envelope | Shape | When |
|---|---|---|
| `string` | `{$$type: 'string', value: 'text'}` | Static text or `@tags()...@endtags()` strings |
| `vx` | `{$$type: 'vx', value: '@post(...)'}` | Raw Voxel dynamic tag (no `@tags()` wrapper) |
| `boolean` | `{$$type: 'boolean', value: true}` | Switches |
| `number` | `{$$type: 'number', value: 42}` | Sliders, counts |
| `image` | `{$$type: 'image', value: {src: <vx \| number>, size: 'string'}}` | Featured image / media slots. **Image writer always emits both `src` AND `size`** — the resolver short-circuits if `size` is missing (option A from `f86a6bc9`). Never write `{src}` alone. |
| `ef-vx-image` | `{$$type: 'ef-vx-image', value: {…}}` | Voxel-tag-aware image input (full-shape writer). Used by `ef-card.media` and `ef-wrapper.bg_media`'s image slot. |
| `link` | `{$$type: 'link', value: {destination: {...url}, isTargetBlank, tag}}` | Links / actions. **SSOT-drift note:** the generated `widget-schemas.json` `link` primitive may declare only `destination` + `isTargetBlank` (no `tag` subkey) and `destination.$$type: string` where live data uses `url` — the **live dump / golden fixture is authoritative** here, not the artifact. A reviewer flagging the `tag` subkey as a "phantom prop" is the artifact lagging; keep the `tag` cell. (Reconcile by regenerating the primitive — tracked separately.) |
| `classes` | `{$$type: 'classes', value: [...]}` | Class lists. Slot 0 reserved for EF-injected local-style id on `ef-card` / `ef-wrapper`. |
| Custom (`ef-content-block-rows`, `ef-action-rows`, `ef-tag-rows`, `ef-form-rows`, `ef-nav-rows`, `vx-loop`, `vx-visibility`, `ef-loop-transform`, `ef-affordance-icon`, …) | `{$$type: '<key>', value: [...] \| {...}}` | Repeaters and structured props |

**Always query `--prop <key>` for the exact envelope on every prop touched.** Hand-rolling these is the #1 source of broken templates. Custom envelope shapes (especially repeater item shapes) change frequently between EF releases.

### Node shape — the silent-empty-render trap (lint-gated)

An EF V4 atomic widget/element is registered via `register_element_type`, so a **valid node uses `elType: '<ef-name>'` and has NO `widgetType` key**:

```jsonc
{ "id": "c1", "elType": "ef-card", "settings": {…}, "elements": [] }   // ✅ correct
{ "id": "c1", "elType": "widget", "widgetType": "ef-card", … }          // ❌ renders EMPTY
```

The classic `{elType:'widget', widgetType:'ef-card'}` shape makes Elementor's `create_element_instance()` return **null** → the node renders as an empty child while **every prop-level lint check still passes**. Only `ts-*` Voxel widgets use the classic `elType:'widget'`+`widgetType` shape. This is now caught by the `node-shape` lint category (an error) in both `elementor:lint` and the `elementor:import` pre-write gate — so a misshapen node is refused before write, not discovered at render. Never author the classic shape for an `ef-*` node.

### Reserved-cell envelopes — `_vx_loop` / `_vx_visibility` (the shapes lint skips)

The reserved keys (`_vx_loop`, `_vx_visibility`, `_ef_loop_transform`, `_cssid`, `col_span`) are **skipped by the prop-level validator** (base-class injected, not in `widget-schemas.json`), so lint will NOT catch a malformed inner shape — these are the highest-risk hand-authored cells. Canonical shapes (source: `Voxel\Dynamic_Data\Visibility_Rules\DTag_Rule`, EF `includes/loop/config.php` `ef_row_loop_settings`; verified against live render):

```jsonc
// _vx_loop — iterate a relation/repeater. `tag` is a BARE dynamic tag
// (NO @tags()…@endtags() wrapper — Voxel's Looper::parse_loopable tokenizes it).
"_vx_loop": { "$$type": "vx-loop", "value": { "tag": "@post(faq)", "limit": null, "offset": null } }

// _vx_visibility — show/hide on a dtag rule. `tag` is BARE; `compare` is a
// modifier key (is_not_empty / is_empty / …); `arguments` is an array.
"_vx_visibility": { "$$type": "vx-visibility", "value": { "behavior": "show",
  "rules": [ [ { "type": "dtag", "tag": "@post(description)", "compare": "is_not_empty", "arguments": [] } ] ] } }
// empty rules = always show:
"_vx_visibility": { "$$type": "vx-visibility", "value": { "behavior": "show", "rules": [] } }
```

**Emptiness-probe tag forms (the subtle part — a bare relation/repeater tag resolves EMPTY in a `.then()` statement):**

| Field kind | Loop `tag` / visibility `tag` | Why |
|---|---|---|
| Repeater (e.g. `faq`) | loop: `@post(faq)` · visibility: `@post(faq).count()` | bare `@post(faq)` works for the loop tokenizer but resolves empty in `@site().then(@post(faq)).is_not_empty()` — use `.count()` for the gate |
| Post-relation (e.g. `hierarchy-children`) | loop: `@post(hierarchy-children)` · visibility: `@post(hierarchy-children.id)` | the gate needs `.id` (the relation's post-id list); the bare relation resolves empty in the modifier statement |
| Scalar text (e.g. `description`, `parent.title`) | `@post(description)` | resolves directly |

Inside a `_vx_loop` row, reference the iterated item's fields with the dotted path: `@post(faq.question)`, `@post(faq.answer)`. Confirm any probe form with `wpdev wp <site> eval` + `\Voxel\render("@site().then(<tag>).is_not_empty().then(yes).else(no)")` on a real post before writing.

### Widget-level vs row-level loop placement — do not put row loops on the host widget

Before adding `_vx_loop`, decide whether the repeated unit is the whole widget or a single composite-repeater row:

| Intended repetition | Correct placement | Example |
|---|---|---|
| Repeat the entire card/wrapper/node once per related post, sibling, service, etc. | Widget/element `settings._vx_loop` | An `ef-card` repeated for each `@site(loop_exp)` item |
| Keep the card/widget once, but repeat one row inside it | The specific row's `value._vx_loop` inside the repeater prop | One `ef-card` with static FAQ heading rows and only the accordion `content_blocks` row repeated over `@post(faq)` |
| Repeat one action/tag/heading/accordion item while sibling rows stay static | The specific `ts_actions` / `tags` / `content_blocks` row | Contact methods, FAQ accordions, repeated chips |

**FAQ accordion rule:** `ef-card.content_blocks` rows with `kind: accordion` are row-loopable. For a glossary FAQ, put `_vx_loop: @post(faq)` on the accordion row (`settings.content_blocks.value[i].value._vx_loop`), never on the `ef-card` widget. Widget-level placement duplicates the heading/card chrome for every FAQ row and is the wrong scope.

**Mechanical pre-write check:** if a widget has both static sibling rows (for example an h2 heading) and one row referencing `@post(<repeater>.<subfield>)`, then `_vx_loop` belongs on that row, not on the widget. After mutation, dump the template and assert: `widget.settings._vx_loop` absent; exactly the row whose cells reference `@post(<repeater>.<subfield>)` has `value._vx_loop`.

## Making a widget prop dynamic-tag-aware

Use `EF_Vx_{Text,Textarea,Select,Switch,Number,Icon}_Control::bind_to(...)` (in place of the native `Text_Control` etc.) for any **content-bearing** prop — the editor renders a bolt next to the input that opens Voxel's tag picker, and the value persists as a `{$$type: 'vx', value: '@post(...)'}` envelope that Voxel's `Vx_Transformer` resolves at render. Full Vx-aware control set under `includes/controls/`: `EF_Vx_Text_Control`, `EF_Vx_Textarea_Control`, `EF_Vx_Select_Control`, `EF_Vx_Switch_Control`, `EF_Vx_Number_Control`, `EF_Vx_Icon_Control`. Layout / variant / CSS-token props keep their native control.

## Recent EF surface changes (re-introspect on every build)

The EF (elementor-framework) plugin's V4 atomic widgets evolve quickly: prop names get renamed, repeater item shapes change, new `$$type` envelopes appear. **Anything memorised from a prior session is suspect.** The committed SSOT `cli/src/generated/widget-schemas.json` is the preferred offline source — it's regenerated from the EF V4 registration SSOT under `plugins/custom/elementor-framework/schemas/` and CI-gated against drift, so it always reflects HEAD; read it on every build even if the same widget was used yesterday. Fall back to live `wpdev elementor:schema` only when you need to confirm a specific site's actually-registered shape or it runs a different EF version. Either way, the cost is much cheaper than producing JSON that fails `elementor:lint`.

For Voxel theme widgets (`ts-post-feed`, `ts-search-form`, …), there's no schema CLI — but `wpdev elementor:dump <site> ts-post-feed --post <real_post> --json` returns the canonical settings shape from a known-working production widget. Use that as the template, never invented JSON. Golden fixtures ship under [`examples/`](../../examples).

Latest moving parts — none replace the rule "query the schema", but they explain why memory will lie:

- **`ef-accordion` no longer exists.** Migration step 530 retired the standalone widget; accordion behaviour now lives on `ef-card` `content_blocks` rows via `kind: accordion` (a collapsible heading+body unit).
- **`ef-icon-heading` no longer exists.** Replaced by `ef-card` with heading enabled; migration step rewrites the widget type on save.
- **Phantom widgets.** `ef-media`, `ef-button`, `ef-buttons`, `ef-breadcrumb`, `ef-button-group`, `ef-map-pin`, `ef-map` have **no PHP files**. They are not registered. The actual EF surface is the four widgets/elements in [`ef-widgets.md`](ef-widgets.md). Card buttons go through `ef-card.ts_actions`; navbar CTAs through `ef-navbar.cta_ts_actions`.
- **General section is auto-injected** on every EF widget — `_cssid`, responsive `col_span`, and a 3-icon **Dynamic affordance band** bound to `_vx_loop` / `_vx_visibility` / `_ef_loop_transform`. EF strips Voxel's three (VX) sections from EF widget panels at filter priority 110.
- **Loop / visibility key naming** — modern is `_vx_loop` / `_vx_visibility` / `_ef_loop_transform`. Legacy `_voxel_loop` / `_voxel_visibility_rules` still recognised on read but not canonical write targets.
- **Image envelope must be full-shape** — `{$$type:'image', value:{src:..., size:'string'}}`. Writing `{src}` alone short-circuits the resolver.
- **`ef-wrapper` carries an action suite** (`action_type` + `action_link` + per-type fields) — replacing the legacy scalar `link` prop (migration step 580). Plus a `bg_media` slot composed via `EF_Part_Media` (full media-type set).
- **`ef-card` inline media (on `heading` rows) + logo** accept the full media-type set (image / video / lottie / icon), not just image.
- **4 new VX user-bar popup actions** in `ts_actions`: `open_vx_inbox`, `open_vx_notifications`, `open_vx_cart`, `open_vx_user_menu`. They emit `data-ef-vx-popup="<slot>"` and require a Voxel user-bar widget on the same page.
- **Voxel-tag-aware controls** — full set is `EF_Vx_{Text,Textarea,Select,Switch,Number,Icon}_Control`; bind via `::bind_to('<prop>')`.

When the schema disagrees with this catalog, trust the schema — the committed SSOT `cli/src/generated/widget-schemas.json` (and live `wpdev elementor:schema <site>` for a site's actual registered shape) win; this file is at best a sketch.
