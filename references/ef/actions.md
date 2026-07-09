# EF Actions Reference

The `ts_actions` prop on `ef-card` is an `EF_Action_Rows_Prop_Type` repeater (atomic V4 envelope `ef-action-rows`) rendered by `parts/actions/actions.php`. Each row carries a `type` selector that drives which sub-fields the resolver consumes; the rendered output is a footer/strip of buttons (or icon-only chips when no label is set). The same composite-repeater pattern is reused by `ef-navbar` under the prefix `cta_` (storage key `cta_ts_actions`, `embedded=true`). Source of truth: `plugins/custom/elementor-framework/includes/catalogs/action-types.php` (per-type metadata + field specs) and `includes/actions/resolver.php` (settings → render model dispatch).

For exact prop envelopes, read the committed SSOT first, fall back to live introspection:

```bash
# Offline SSOT (preferred, CI-gated against drift)
jq '.widgets[] | select(.name=="ef-card") | .props.ts_actions, .rows."action-row"' \
  cli/src/generated/widget-schemas.json

# Live fallback
wpdev elementor:schema <site> ef-card --prop ts_actions
wpdev elementor:schema <site> ef-navbar --prop cta_ts_actions
```

For known-good rows, dump a real production widget:

```bash
wpdev elementor:dump <site> ef-card --post <prod_id> --json
```

## Action type catalog

The action-type catalog below is generated from `cli/src/generated/ef-catalogs.json` (extracted from `EF_ACTION_*` constants + `ef_action_types()` in `action-types.php`). `Required fields` come from `ef_action_field_specs()`. The per-action behavioural notes (Voxel-runtime caveats, URL wrapping, etc.) live in the prose sections below — only the enumerative catalog is generated.

<!-- AUTO-GENERATED:actions START — edit schemas, run `wpdev elementor:docs:gen`, do not hand-edit -->

35 action types from `ef_action_types()` (see `includes/catalogs/action-types.php`).

Unified action surface — every type works on every action host (slot, byline, tag, card actions).

| Action ID | Label | Required fields |
|---|---|---|
| `''` (None) | None | — |
| `access_markdown` | Access Markdown | — |
| `action_follow` | Follow post author | `icon_active`, `label_active` |
| `action_follow_post` | Follow post | `icon_active`, `label_active` |
| `action_gcal` | Google Calendar | `cal_start_date`, `cal_end_date`, `cal_title`, `cal_desc`, `cal_location` |
| `action_ical` | iCal | `cal_start_date`, `cal_end_date`, `cal_title`, `cal_desc`, `cal_location`, `cal_url` |
| `action_link` | Link | `link` |
| `action_login` | Log in | — |
| `action_logout` | Log out | — |
| `action_save` | Save post | `icon_active`, `label_active` |
| `add_to_cart` | Add to cart | `cart_text` |
| `back_to_top` | Back to top | — |
| `call` | Phone call | `phone` |
| `delete_post` | Delete post | — |
| `direct_message` | Message post | — |
| `direct_message_user` | Message post author | — |
| `edit_post` | Edit post | — |
| `get_directions` | Directions | `address` |
| `go_back` | Go back | — |
| `open_modal` | Open modal | `modal_id` |
| `open_vx_cart` | Open cart | — |
| `open_vx_inbox` | Open inbox | — |
| `open_vx_notifications` | Open notifications | — |
| `open_vx_quick_search` | Open quick search | — |
| `open_vx_user_menu` | Open user menu | — |
| `promote_post` | Promote post | — |
| `publish_post` | Publish post | — |
| `scroll_to_section` | Scroll to section | `scroll_to` |
| `send_email` | Email | `email` |
| `share_post` | Share post | `toast_message` |
| `show_post_on_map` | Show on map | — |
| `unpublish_post` | Unpublish post | — |
| `view_post_stats` | View post stats | — |
| `vote_downvote` | Downvote | `vote_field_key` |
| `vote_upvote` | Upvote | `vote_field_key` |

<!-- AUTO-GENERATED:actions END -->

**Voxel-runtime caveat** (from `action-types.php` header): the resolver returns an empty payload for native Voxel post-state actions (`edit_post`, `delete_post`, `follow*`, `save`, `share_post`, `promote_post`, `add_to_cart`, `select_addition`, `show_post_on_map`, `view_post_stats`, `go_back`, `back_to_top`, publish/unpublish). They render an inert `<button>` outside Voxel's advanced-list template and only become live when the row renders inside it.

## Action row sub-field shape

The cell table below mirrors the resolved `action-row` sub-schema in `cli/src/generated/widget-schemas.json` (sourced from `plugins/custom/elementor-framework/schemas/parts/rows/action.schema.json`). Each cell has its own `$$type` envelope. 18 cells; cal cells **are** in the row repeater (the historical "scalar-only cal" carve-out is gone — unified action surface, see Rule 8 / "doubt every special case" in CLAUDE.md).

| Cell | Type | Default | Used when `type=` |
|---|---|---|---|
| `type` | enum (29 ids, see catalog above) | `action_link` | — (drives dispatch) |
| `label` | string | `''` | any |
| `icon` | string | `''` | any |
| `variant` | enum: `''` \| `transparent` \| `white` \| `primary` \| `secondary` \| `red` \| `green` \| `gray` | `''` (inherit host's `default_variant_key`) | any |
| `tooltip` | string | `''` | any — non-empty emits `data-tooltip` + `aria-label` |
| `link` | Link primitive (`{url, is_external, nofollow}`) | — | `action_link` |
| `address` | string | `''` | `get_directions` |
| `phone` | string | `''` | `call` |
| `email` | string | `''` | `send_email` |
| `modal_id` | string | `''` | `open_modal` |
| `scroll_to` | string | `''` | `scroll_to_section` |
| `cart_text` | string | `''` | `add_to_cart` |
| `cal_start_date` | string | `''` | `action_gcal`, `action_ical` |
| `cal_end_date` | string | `''` | `action_gcal`, `action_ical` |
| `cal_title` | string | `''` | `action_gcal`, `action_ical` |
| `cal_desc` | string | `''` | `action_gcal`, `action_ical` |
| `cal_location` | string | `''` | `action_gcal`, `action_ical` |
| `cal_url` | string | `''` | `action_ical` |

Plus the inherited loop-envelope cells from `EF_Loopable_Row_Prop_Type` (`_voxel_loop`, `_voxel_loop_limit`, `_voxel_loop_offset`, `_ef_loop_sort`, `_visibility`) — same as `tag-row` / `heading-row` (see [`widgets.md`](widgets.md)).

## Common patterns by use case

| Use case | `type` | Required cells |
|---|---|---|
| Whole-card-clickable to permalink | `action_link` | `link.destination` = vx envelope wrapping `@post(permalink)` |
| Phone call | `call` | `phone` = `@post(<phone_field_key>)` or static |
| Email | `send_email` | `email` = `@post(<email_field_key>)` or static |
| Get directions | `get_directions` | `address` = `@post(location.address)` — always opens new tab |
| Show on map | `show_post_on_map` | none — page must contain a `ts-map` widget |
| Open modal | `open_modal` | `modal_id` = target dialog element's `id` |
| Scroll to section | `scroll_to_section` | `scroll_to` = element id (`#` optional) |
| Share post | `share_post` | none — Voxel runtime opens share sheet |
| Add to cart | `add_to_cart` | optional `cart_text` (label override); requires Voxel commerce |
| Save / Follow post / Follow author | `action_save` / `action_follow_post` / `action_follow` | none — Voxel-runtime, logged-in user |
| Edit / Delete / Publish / Unpublish post | `edit_post` / `delete_post` / `publish_post` / `unpublish_post` | none — Voxel gates by capability |
| Promote / View stats | `promote_post` / `view_post_stats` | none — Voxel commerce/analytics gated |
| Calendar export (Google) | `action_gcal` | `cal_start_date`, `cal_end_date`, `cal_title` (+ optional `cal_desc`, `cal_location`) |
| Calendar export (iCal) | `action_ical` | `cal_url` (or the same `cal_*` group when composing the `.ics` server-side) |
| Back to top / Go back | `back_to_top` / `go_back` | none |
| Select add-on | `select_addition` | none — Voxel commerce add-on flow |
| Open VX inbox / notifications / cart / user-menu | `open_vx_inbox` / `open_vx_notifications` / `open_vx_cart` / `open_vx_user_menu` | none — requires a Voxel user-bar widget on the page |

## Voxel-runtime dependencies

`Resolver::resolve_action_payload()` returns a non-empty `link.url` or `attrs` only for: `action_link`, `get_directions`, `call`, `send_email`, `open_modal`, `scroll_to_section`, `action_gcal`, `action_ical`, `share_post`. Every other action falls into the `default` arm and renders as an inert button unless Voxel's frontend Vue runtime is on the page.

| Action | Voxel piece required |
|---|---|
| `show_post_on_map` | A `ts-map` widget rendered on the same page. |
| `add_to_cart`, `select_addition`, `promote_post` | Voxel commerce module active. |
| `action_save`, `action_follow`, `action_follow_post` | Voxel auth + collections runtime; user logged in. |
| `edit_post`, `delete_post`, `publish_post`, `unpublish_post` | Voxel post-state runtime + post-author capability. |
| `view_post_stats` | Voxel stats panel (`ts-post-stats` template). |
| `share_post` | Voxel share-sheet runtime (resolver emits `data-ef-share`; Vue handles open). |
| `back_to_top`, `go_back` | None beyond Voxel frontend JS bootstrap. |
| `open_vx_inbox`, `open_vx_notifications`, `open_vx_cart`, `open_vx_user_menu` | A Voxel **user-bar widget** rendered on the same page (registers the popup targets). Action emits `data-ef-vx-popup="<slot>"`; `assets/js/vx-popup.js` dispatches to the user-bar's existing popup. |

These actions only "wake up" when the row renders inside Voxel's advanced-list template (or any Voxel template that mounts the runtime). Selecting one outside that context renders an inert button — accepted tradeoff for parity with Voxel's selector.

## Self-exclusion in relation loops/feeds (#18 — by construction)

Whenever a loop or `ts-post-feed` iterates a relation that can include the current post (related-CPT feeds, same-taxonomy feeds, sibling relations), the planner MUST inject an exclusion of the current post id into the query at compose time (the feed's exclude / `post__not_in` setting, or a `_vx_loop` filter). This makes the relation-loop-self regression — a post silently listing itself in its own related feed — **structurally impossible**, not merely something the `relation-loop-self` criterion catches after the fact. The criterion stays as the falsifier; construct-time exclusion is the primary defense.

## Loopable action-rows (contact-method repeaters, taxonomy sub-fields, Voxel taxonomies)

`Action_Row` extends `Loopable_Row` (`ef-parts.md` §Actions §Loop expansion). Each row carries its own `_vx_loop` / `_vx_visibility` / `_ef_loop_transform` cells via the base-class auto-merge, expanded by `Base::expand_rows($settings, 'ts_actions', new Action_Row_Definition())` at render time. The same placement rule applies to other composite row surfaces such as `ef-card.content_blocks`: if only one row is meant to repeat, put `_vx_loop` on that row's `value`, not on the host widget.

**SSOT incompleteness gap (read this before reading the SSOT).** The committed artifact `cli/src/generated/widget-schemas.json` lists each widget's own declared props, but **does NOT include auto-merged base-class props from `Loopable_Row`** (`_vx_loop`, `_vx_visibility`, `_ef_loop_transform`). A bare `jq '.widgets[] | select(.name=="ef-card") | .rows."action-row".props | keys'` returns 18 props — none of which are the loop / visibility cells. Those cells ARE valid on every action-row; the schema artifact just doesn't expose them. To verify a row supports loop / visibility, check `ef-parts.md` §<Part_Name> §Loop expansion (the per-part contract) OR the PHP class declaration of the row's definition object. Treating the SSOT as a closed list for row-level props produces false-negative "phantom prop" findings from the `ssot-integrity` criterion — the criterion MUST cross-reference `ef-parts.md` before flagging row-level `_vx_loop` / `_vx_visibility` / `_ef_loop_transform`.

**Pattern A — row-level loop over a repeater (production-proven for contact-method repeaters):**

```
ts_actions:
  - { type: "call",       phone: "@tags()@post(<repeater>.<value_field>)@endtags()",  label: "@tags()@post(<repeater>.<value_field>)@endtags()",
      _vx_loop: "@post(<repeater>)",
      _vx_visibility: { behavior: show, rules: [[
        { type: "dtag", tag: "@post(<repeater>.<type_field>)", compare: "contains", arguments: ["phone"] }
      ]]} }
  - { type: "send_email", email: "@tags()@post(<repeater>.<value_field>)@endtags()",  label: "@tags()@post(<repeater>.<value_field>)@endtags()",
      _vx_loop: "@post(<repeater>)",
      _vx_visibility: { behavior: show, rules: [[
        { type: "dtag", tag: "@post(<repeater>.<type_field>)", compare: "contains", arguments: ["email"] }
      ]]} }
  # one row per sub-type — e.g. linkedin / facebook / twitter / instagram / website
```

**Canonical stored envelope (golden — never re-derive from PHP source).** The Pattern-A shorthand above maps to these exact `$$type` envelopes in `_elementor_data`. This is the shape `EF\Envelope::vx_loop()` / `::vx_visibility()` / `::vx_rule_dtag()` emit (from `plugins/custom/elementor-framework/includes/envelope-builder.php`) — copy it verbatim, swap the leaf expressions:

```json
{
  "_vx_loop": {
    "$$type": "vx-loop",
    "value": {
      "tag":    { "$$type": "string", "value": "@post(<repeater>)" },
      "limit":  null,
      "offset": null
    }
  },
  "_vx_visibility": {
    "$$type": "vx-visibility",
    "value": {
      "behavior": "show",
      "rules": [
        [ { "type": "dtag", "tag": "@post(<repeater>.<type_field>)", "compare": "contains", "arguments": ["phone"] } ]
      ]
    }
  }
}
```

`rules` is an **array of arrays** — outer = OR groups, inner = AND conditions. `limit`/`offset` are `null` (no cap) or a `{$$type:"number", value:N}` envelope. When no on-site template yet uses `_vx_loop` (first relation-loop deployment — there was no golden node to dump during a relation-field migration on a data-rich CPT), this block IS the golden source; do not read `loop-resolver.php` / `envelope-builder.php` to re-derive it. In mutator scripts, prefer the factory: `EF\Envelope::vx_loop("@post(<repeater>)")` and `EF\Envelope::vx_visibility("show", [[ EF\Envelope::vx_rule_dtag("@post(<repeater>.<type_field>)", "contains", ["phone"]) ]])`.

**Why `contains`, not `is_equal_to`** — `<repeater>.<type_field>` is a **taxonomy / multiselect** sub-field. Its value is `["phone"]` (array), not `"phone"` (string). `is_equal_to "phone"` evaluates false because `["phone"] != "phone"`. `contains "phone"` evaluates true. This applies to ANY repeater sub-field of type taxonomy / multiselect / post-relation: ALWAYS use `contains` for the dtag comparator. The matching pitfall is documented in `voxel-field-types.md:689` for the field-level `conditions` registry (`taxonomy:contains`); the same rule applies at runtime via the dtag comparator. The data-wiring criterion checks for `is_equal_to` on a sub-field whose §2a Field Inventory class is taxonomy / multiselect / post-relation and emits severity `C`.

**Pattern B — splice `ts-advanced-list` (Voxel-runtime alternative):**

Voxel's `ts-advanced-list` widget iterates a repeater natively with per-sub-type sub-templates (each sub-type gets its own `<a>` markup). For any contact-method repeater where every sub-type needs a distinct link shape (`tel:` / `mailto:` / `https://`) — splicing a known-good `ts-advanced-list` instance is simpler than Pattern A. Read it from production via `wpdev elementor:dump <site> ts-advanced-list --post <prod_post_id> --json` and re-embed the entire node (id + every setting) verbatim, then strip plugin pollution (`eael_*`, `jet_*`, `__globals__`, `_voxel_dynamic_attrs`) before re-emitting. Both patterns are valid; pick A when you want EF V4 design-system styling (variant tokens), B when you want zero-config parity with the legacy Voxel UI.

**Visibility-rule fragility on structured-array fields (work-hours, location, repeaters):**

`dtag is_not_empty` on `@post(<key>)` for a **work-hours**, **location**, **repeater**, **product**, or other structured-array field DOES NOT reliably evaluate true even when postmeta contains array data. The dtag comparator's `is_not_empty` was designed for scalar strings; structured-array fields encode emptiness internally (a work-hours field with `status: closed` for every day is "non-empty as a value" but "empty as a schedule"). When you need to gate a section on whether the structured field has meaningful data:

- **Preferred**: let the `ts-*` widget handle emptiness internally (e.g. `ts-work-hours` renders "Closed" labels when the schedule is all-closed; no outer vis-gate needed).
- **Alternative**: gate on a scalar sub-key — e.g. `@post(schedule.0.status) is_not_empty` for the first group, OR `@post(<repeater>.0.<value_field>) is_not_empty` for the first repeater row.
- **Forbidden**: `@post(<structured-field>) is_not_empty` as a section-level gate — it produces silent rendering bugs that lint can't see.

The `hierarchy` criterion surfaces structured-field `is_not_empty` rules as severity `I` with a "fragile vis-gate — prefer widget-internal handling or scalar sub-key gate" finding.

**Phase 6 browser verification is the only catcher for these classes.** Action-row loop + visibility bugs (wrong comparator, missing loop, fragile vis-gate) ALL pass `wpdev elementor:lint` because the prop names are valid; the bug is semantic, not schema-level. Seven-rules.md Rule 7 is the gate.

## `actions_embedded` (ef-card only)

`ef-card` carries a sibling string prop `actions_embedded` that switches the actions strip layout. Enum (from the SSOT — `wpdev elementor:schema <site> ef-card --prop actions_embedded`):

| Value | Label | Meaning |
|---|---|---|
| `''` | Default | Inherit — card resolves to `yes` unless the card is a ghost-with-body, in which case `no`. |
| `'yes'` | Embedded footer strip | Chip-style buttons sharing the card footer (`.ef-card-footer`). |
| `'no'` | Stacked buttons | One button per row, full-width (`.ef-card-actions.ef-buttons`). |

`ef-navbar`'s `cta_ts_actions` does not expose `actions_embedded` — the navbar Actions part is constructed with `embedded=true` and always renders as buttons.

## See also

- [`widgets.md`](widgets.md) — `tags` repeater on `ef-card` (same loop-envelope inheritance pattern as `ts_actions`).
- [`ef-widgets.md`](ef-widgets.md) §ef-card — full `ef-card` prop surface including `actions_embedded` and the `cta_*` action-slot props on `ef-navbar`.
- [`ef-parts.md`](ef-parts.md) §Actions / §Action_Slot — Part-level contracts (`Actions::repeater_control()`, `Action_Slot::props()`, `to_link()`, `to_render_item()`) and the §action-row generated cell table.
- [`rules.md`](../core/rules.md) (eight rules) — Rule 1 (SSOT-first), Rule 5 (static vs dynamic per render context).
