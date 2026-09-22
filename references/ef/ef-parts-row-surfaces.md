# EF Parts: Generated Row Surfaces

## Generated row-surface tables

The tables below enumerate the per-row cell schemas (the prop surfaces parts expose to composite repeaters: `action-row`, `content-block-row`, `field-row`, `map-pin-row`, `mega-row`, `tag-row`). Generated from the resolved row sub-schemas in `cli/src/generated/widget-schemas.json` (sourced from `plugins/custom/elementor-framework/schemas/parts/rows/*.schema.json`). The per-part conceptual prose above remains the authoritative description of class hierarchy, contracts, composition rules, and render semantics — only the enumerative cell tables are generated here.

<!-- AUTO-GENERATED:ef-parts START — edit schemas, run `wpdev elementor:docs:gen`, do not hand-edit -->

### Row surface `action-row` — Action row

8 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `flyout_template` | `string` (direct vx) | `''` | Saved Elementor template shown as an anchored interactive flyout |
| `icon` | `string` (direct vx) | `''` | Icon shown on the button |
| `label` | `string` (direct vx) | `''` | Button text |
| `payload` | `action_payload` (nested vx leaves) | — | Fields for the selected action type |
| `require_login` | `boolean` (direct vx) | `false` | Require authentication before this action can resolve or execute |
| `tooltip` | `string` (direct vx) | `''` | Short hover text shown on the button |
| `type` | enum: `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `copy_to_clipboard` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `claim_post` \| `relist_post` \| `switch_listing_plan` \| `upgrade_listing_plan` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `select_addition` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `ask_chatgpt` \| `ask_perplexity` \| `ask_claude` \| `ask_copilot` \| `ask_mistral` \| `ask_google_ai` \| `vote_upvote` \| `vote_downvote` (direct vx) | `action_link` | Choose what opens on click |

### Row surface `comparison-field-row` — Comparison field row

2 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `label` | `string` (dynamic disabled) | `''` | Label shown in the first comparison column |
| `value` | `string` (direct vx) | `''` | Comparison value |

### Row surface `content-block-row` — Content block row

62 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `appearance` | enum: `plain` \| `field` \| `pill` \| `button` (direct vx) | `plain` | Choose the canonical text presentation |
| `brand_color` | `string` (direct vx) | `primary` | Booking accent color |
| `compare_destination` | `source` (nested vx leaves) | — | Optional override for the comparison page the floating tray opens |
| `compare_fields` | repeater `ef-comparison-field-rows` (nested vx leaves) | `[]` | Ordered comparison fields |
| `compare_label` | `string` (direct vx) | `Compare` | Comparison action label |
| `compare_label_field` | `string` (direct vx) | `''` | Optional dynamic tag for comparison column labels |
| `compare_maximum` | `number` (direct vx) | `4` | Maximum persisted comparison selection |
| `compare_source_field` | `string` (direct vx) | `''` | Optional post-relation field whose related posts are compared instead of the selected posts |
| `compare_template` | `string` (direct vx) | `''` | Saved Elementor template rendered as each selected item's preview inside the tray |
| `compare_tray_label` | `string` (direct vx) | `Selected items` | Accessible label for the automatic tray |
| `description` | `string` (direct vx) | `''` | Shared supporting text |
| `filters` | repeater `ef-filter-item-rows` (nested vx leaves) | `[]` | Ordered visitor filters applied to the selected results loop |
| `flyout_template` | `string` (direct vx) | `''` | Template-flyout cell — data only |
| `hide_details` | `boolean` (direct vx) | `false` | Hide event details |
| `icon` | `string` (direct vx) | `''` | Icon cell — data only |
| `kind` | enum: `text` \| `media` \| `group` \| `accordion` \| `filter` \| `calendar` \| `toc` \| `reviews` \| `select` \| `comparison` \| `custom_code` \| `auth` (direct vx) | `text` | Choose what this content block shows |
| `label` | `richtext` (direct vx) | `''` | Human-facing title for accordion, table-of-contents, and filter sort controls |
| `layout` | enum: `''` \| `inline` \| `stacked` \| `floating` \| `week_view` \| `month_view` \| `column_view` (direct vx) | `''` | Choose the kind-specific content layout |
| `max_heading` | enum: `h2` \| `h3` \| `h4` \| `h5` \| `h6` (direct vx) | `h3` | Deepest heading level included in the table of contents |
| `media_icon` | `string` (direct vx) | `''` | Choose an icon |
| `media_image` | `image` (nested vx leaves) | `[]` | Choose an image |
| `media_image_alt` | `string` (direct vx) | `''` | Describe the image for screen readers |
| `media_image_alt_mode` | enum: `inherit` \| `custom` \| `decorative` (direct vx) | `inherit` | Choose whether alt text comes from the attachment, a custom value, or is intentionally empty for a decorative image |
| `media_image_loading` | enum: `auto` \| `lazy` \| `eager` (direct vx) | `auto` | Choose when the image loads |
| `media_map_pins` | repeater `ef-map-pin-rows` (nested vx leaves) | `[]` | Add pins to the map |
| `media_map_zoom` | `string` (direct vx) | `14` | Starting map zoom level |
| `media_modifiers` | `string` (direct vx) | `''` | Optional image behavior flags |
| `media_position` | enum: `inline` \| `top-edge` \| `auto-main` \| `right-main` \| `top-main` (responsive, nested vx leaves) | `inline` | Choose the placement of a standalone media row at each screen size |
| `media_type` | enum: `''` \| `image` \| `video` \| `icon` \| `map` (direct vx) | `''` | Choose what kind of media to show |
| `media_video_loading` | enum: `native` \| `facade` (direct vx) | `native` | Keep the initial player on video watch pages |
| `media_video_url` | `source` (nested vx leaves) | `''` | Video link or file |
| `mobile_slots_first` | `boolean` (direct vx) | `true` | Show times first on mobile |
| `mode` | enum: `login` \| `register` (direct vx) | `login` | Choose the password credential mode this row shows |
| `modifiers` | `string` (direct vx) | `''` | Kind-scoped behavior flags shared by text, group, and reviews rows |
| `open` | `boolean` (direct vx) | `false` | Open this accordion by default |
| `overflow_limit` | `number` (direct vx) | `1` | Rows shown before the overflow affordance appears |
| `overflow_suffix` | `string` (direct vx) | `''` | Word after a hidden count of one (for example +1 product) |
| `overflow_suffix_plural` | `string` (direct vx) | `''` | Word after a hidden count of two or more |
| `payload` | `action_payload` (nested vx leaves) | — | Fields for the selected action type |
| `placement` | enum: `content` \| `footer` (direct vx) | `content` | Choose the card surface that owns this group |
| `position` | enum: `left` \| `center` \| `right` \| `spread` (direct vx) | `left` | Align inline or floating group members to the left, center, or right, or spread them across the available row |
| `redirect` | `string` (direct vx) | `''` | Optional URL the visitor lands on after a successful login or registration |
| `require_login` | `boolean` (direct vx) | `false` | Require authentication before this action can resolve or execute |
| `reviews_category` | `string` (direct vx) | `''` | Stable native Voxel review category key |
| `reviews_icon` | `string` (direct vx) | `ms:ms ms-star` | Repeated icon used to visualize the aggregate rating |
| `reviews_presentation` | enum: `icon` \| `bars` \| `compact` (direct vx) | `icon` | Choose repeated icons, one rounded progress bar, or a compact category-and-score pill |
| `reviews_star_color` | `string` (direct vx) | `yellow` | Filled rating icon or rounded bar color |
| `scope` | `string` (direct vx) | `''` | Element ID to build the table of contents from |
| `social_label` | `string` (direct vx) | `''` | Optional divider label above the provider buttons, for example 'or continue with' |
| `sorts` | repeater `ef-sort-item-rows` (nested vx leaves) | `[]` | Manifest-authorized orderings for the selected results loop |
| `style` | enum: `''` \| `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `body` \| `small` (direct vx) | `''` | Visual size of this row's heading text, independent of its semantic tag |
| `submit_label` | `string` (direct vx) | `''` | Optional submit button label override |
| `tag` | enum: `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `p` \| `span` \| `address` \| `ol_item` \| `ul_item` \| `rich_text` (direct vx) | `h3` | Choose the semantic HTML tag for canonical text, or switch the same Text field to rich-text content |
| `target` | `string` (dynamic disabled) | `''` | Comma-separated canonical Elementor element IDs of the compatible EF loops this filter updates |
| `theme` | enum: `light` \| `dark` \| `auto` (direct vx) | `light` | Light, dark, or automatic theme |
| `tooltip` | `string` (direct vx) | `''` | Short hover text shown on the button |
| `type` | enum: `''` \| `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `copy_to_clipboard` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `claim_post` \| `relist_post` \| `switch_listing_plan` \| `upgrade_listing_plan` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `select_addition` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `ask_chatgpt` \| `ask_perplexity` \| `ask_claude` \| `ask_copilot` \| `ask_mistral` \| `ask_google_ai` \| `vote_upvote` \| `vote_downvote` (direct vx) | `''` | Choose what opens on click |
| `url` | `source` (nested vx leaves) | — | Optional absolute booking URL override |
| `value` | `richtext` (direct vx) | `''` | Primary authored content for text, accordion, and custom-code rows |

### Row surface `field-row` — Field row

5 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `label` | `string` (direct vx) | `''` | Field label shown to visitors |
| `payload` | `field_payload` | — | Only the active field type's authored configuration |
| `placeholder` | `string` (direct vx) | `''` | Hint inside the field |
| `required` | `boolean` (direct vx) | `false` | Require visitors to fill this in |
| `type` | enum: `heading` \| `text` \| `email` \| `textarea` \| `select` \| `upload` \| `checkbox` \| `combobox` (direct vx) | `text` | Choose the kind of field |

### Row surface `filter-item-row` — Filter item row

3 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `label` | `string` (direct vx) | `''` | Accessible label shown above the visitor's filter control |
| `options` | `string` (dynamic disabled) | `''` | Optional authored visitor choices, one value per line |
| `predicate` | `predicate` (nested vx leaves) | — | Indexed predicate source, comparison, and authored arguments |

### Row surface `map-pin-row` — Map pin row

7 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `label` | `string` (direct vx) | `''` | Marker label, tooltip, or popup text |
| `location` | `string` (direct vx) | `''` | Voxel location JSON containing numeric latitude and longitude |
| `media_image` | `image` (nested vx leaves) | `[]` | Choose an image |
| `media_image_alt` | `string` (direct vx) | `''` | Describe the image for screen readers |
| `media_image_loading` | enum: `auto` \| `lazy` \| `eager` (direct vx) | `auto` | Choose when the image loads |
| `media_type` | enum: `image` (direct vx) | `image` | Fixed image discriminator for the canonical map pin media payload |
| `template` | `string` (direct vx) | `''` | Per-pin Elementor card template rendered (lazily, on pin click) in the pin's related-post context |

### Row surface `mega-row` — Mega row

21 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `description` | `string` (direct vx) | `''` | Optional subtitle |
| `label` | `string` (direct vx) | `''` | Menu item text |
| `limit` | `boolean` (direct vx) | `false` | Caps the visible rows this row generates (a heading row clamps its column grid, a link row clamps its pill list) and reveals an overflow affordance |
| `link` | `source` (nested vx leaves) | — | Link this item opens |
| `loop_anchor` | `string` (direct vx) | `''` | Post used for repeated links |
| `loop_anchor_type` | enum: `''` \| `custom` (direct vx) | `''` | Choose the source for repeated links |
| `media_icon` | `string` (direct vx) | `''` | Choose an icon |
| `media_image` | `image` (nested vx leaves) | `[]` | Choose an image |
| `media_image_alt` | `string` (direct vx) | `''` | Describe the image for screen readers |
| `media_image_alt_mode` | enum: `inherit` \| `custom` \| `decorative` (direct vx) | `inherit` | Choose whether alt text comes from the attachment, a custom value, or is intentionally empty for a decorative image |
| `media_image_loading` | enum: `auto` \| `lazy` \| `eager` (direct vx) | `auto` | Choose when the image loads |
| `media_map_pins` | repeater `ef-map-pin-rows` (nested vx leaves) | `[]` | Add pins to the map |
| `media_map_zoom` | `string` (direct vx) | `14` | Starting map zoom level |
| `media_modifiers` | `string` (direct vx) | `''` | Optional image behavior flags |
| `media_type` | enum: `''` \| `image` \| `video` \| `icon` \| `map` (direct vx) | `''` | Choose what kind of media to show |
| `media_video_loading` | enum: `native` \| `facade` (direct vx) | `native` | Keep the initial player on video watch pages |
| `media_video_url` | `source` (nested vx leaves) | `''` | Video link or file |
| `overflow_limit` | `number` (direct vx) | `0` | Rows shown before the overflow affordance appears |
| `overflow_suffix` | `string` (direct vx) | `''` | Word after a hidden count of one (for example +1 product) |
| `overflow_suffix_plural` | `string` (direct vx) | `''` | Word after a hidden count of two or more |

### Row surface `recipient-row` — Recipient row

1 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `email` | `string` (direct vx) | `''` | Email address receiving a copy |

### Row surface `sort-item-row` — Sort option row

2 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `label` | `string` (direct vx) | `''` | Visitor-facing label for this ordering option |
| `ordering` | `ordering` (nested vx leaves) | — | Indexed ordering source and direction |

<!-- AUTO-GENERATED:ef-parts END -->

