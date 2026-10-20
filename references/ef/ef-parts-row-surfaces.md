# EF Parts: Generated Row Surfaces

## Generated row-surface tables

The tables below enumerate the per-row cell schemas (the prop surfaces parts expose to composite repeaters: `action-row`, `content-block-row`, `field-row`, `map-pin-row`, `mega-row`, `tag-row`). Generated from the resolved row sub-schemas in `cli/src/generated/widget-schemas.json` (sourced from `plugins/custom/elementor-framework/schemas/parts/rows/*.schema.json`). The per-part conceptual prose above remains the authoritative description of class hierarchy, contracts, composition rules, and render semantics — only the enumerative cell tables are generated here.

<!-- AUTO-GENERATED:ef-parts START — edit schemas, run `wpdev elementor:docs:gen`, do not hand-edit -->

### Row surface `action-row` — Action row

11 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `action_payload` | `action_payload` (nested vx leaves) | — | Fields for the selected action type |
| `aria_label` | `string` (direct vx) | `''` | Accessible name override for an empty or icon-only control |
| `disabled` | `boolean` (direct vx) | `false` | Disable this action without removing its configuration |
| `flyout_template` | `string` (direct vx) | `''` | Saved Elementor template shown as an anchored interactive flyout |
| `icon` | `string` (direct vx) | `''` | Icon shown on the button |
| `label` | `string` (direct vx) | `''` | Button text |
| `require_login` | `boolean` (direct vx) | `false` | Require authentication before this action can resolve or execute |
| `tooltip` | `string` (direct vx) | `''` | Short hover text shown on the button |
| `tooltip_disabled` | `string` (direct vx) | `''` | Tooltip shown when this action is disabled |
| `type` | enum: `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `copy_to_clipboard` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `claim_post` \| `relist_post` \| `switch_listing_plan` \| `upgrade_listing_plan` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `select_addition` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `ask_chatgpt` \| `ask_perplexity` \| `ask_claude` \| `ask_copilot` \| `ask_mistral` \| `ask_google_ai` \| `vote_upvote` \| `vote_downvote` \| `set_field_value` (direct vx) | `action_link` | Choose what opens on click |
| `variant` | enum: `dynamic` \| `transparent` \| `white` \| `primary` \| `primary_light` \| `primary_white` \| `secondary` \| `secondary_light` \| `secondary_white` \| `positive` \| `negative` (direct vx) | `dynamic` | Button or pill colors |

### Row surface `comparison-field-row` — Comparison field row

19 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `action_payload` | `action_payload` (nested vx leaves) | — | Fields for the selected action type |
| `appearance` | enum: `plain` \| `field` \| `pill` \| `button` (direct vx) | `plain` | Choose the canonical Text content-row presentation |
| `description` | `string` (direct vx) | `''` | Shared supporting text |
| `disabled` | `boolean` (direct vx) | `false` | Disable this action without removing its configuration |
| `flyout_template` | `string` (direct vx) | `''` | Template-flyout cell — data only |
| `icon` | `string` (direct vx) | `''` | Icon cell — data only |
| `label` | `string` (dynamic disabled) | `''` | Label shown in the first comparison column |
| `links` | `string` (direct vx) | `''` | Optional comma-separated destinations paired by position with pill values |
| `media_image` | `image` (nested vx leaves) | `[]` | Choose an image |
| `media_type` | enum: `''` \| `image` (direct vx) | `''` | Optional image for the comparison value |
| `modifiers` | `string` (direct vx) | `''` | Kind-scoped behavior flags shared by text and reviews content rows |
| `require_login` | `boolean` (direct vx) | `false` | Require authentication before this action can resolve or execute |
| `style` | enum: `''` \| `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `body` \| `small` (direct vx) | `body` | Visual typography for plain Text content rows, independent of the semantic tag |
| `tag` | enum: `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `p` \| `span` \| `address` \| `ol_item` \| `ul_item` \| `rich_text` (direct vx) | `p` | Semantic tag for plain Text content rows, or rich-text mode |
| `tooltip` | `string` (direct vx) | `''` | Short hover text shown on the button |
| `tooltip_disabled` | `string` (direct vx) | `''` | Tooltip shown when this action is disabled |
| `type` | enum: `''` \| `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `copy_to_clipboard` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `claim_post` \| `relist_post` \| `switch_listing_plan` \| `upgrade_listing_plan` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `select_addition` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `ask_chatgpt` \| `ask_perplexity` \| `ask_claude` \| `ask_copilot` \| `ask_mistral` \| `ask_google_ai` \| `vote_upvote` \| `vote_downvote` \| `set_field_value` (direct vx) | `''` | Choose what opens on click |
| `value` | `richtext` (direct vx) | `''` | Primary Text content-row value |
| `variant` | enum: `dynamic` \| `transparent` \| `white` \| `primary` \| `primary_light` \| `primary_white` \| `secondary` \| `secondary_light` \| `secondary_white` \| `positive` \| `negative` (direct vx) | `dynamic` | Shared pill or button colors |

### Row surface `content-block-row` — Content block row

69 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `action_payload` | `action_payload` (nested vx leaves) | — | Fields for the selected action type |
| `appearance` | enum: `plain` \| `field` \| `pill` \| `button` (direct vx) | `plain` | Choose the canonical Text content-row presentation |
| `brand_color` | `string` (direct vx) | `primary` | Booking accent color |
| `compare_bar_variant` | enum: `transparent` \| `white` \| `primary` \| `primary_light` \| `primary_white` \| `secondary` \| `secondary_light` \| `secondary_white` \| `positive` \| `negative` (direct vx) | `white` | Floating bar colors, drawn from the shared surface variant vocabulary so the tray is paintable exactly like a card, navbar, or accordion surface |
| `compare_destination` | `source` (nested vx leaves) | — | Optional override for the comparison page the floating tray opens |
| `compare_fields` | repeater `ef-comparison-field-rows` (nested vx leaves) | `[]` | Ordered comparison fields |
| `compare_image_field` | `string` (direct vx) | `''` | Optional Voxel dynamic tag used as the image above each comparison column, for example @post(product-brand._thumbnail_id.url) |
| `compare_label` | `string` (direct vx) | `Compare` | Comparison action label |
| `compare_label_field` | `string` (direct vx) | `''` | Optional dynamic tag for comparison column labels |
| `compare_maximum` | `number` (direct vx) | `3` | Maximum persisted comparison selection |
| `compare_template` | `string` (direct vx) | `''` | Saved Elementor template rendered as each selected item's preview inside the tray |
| `compare_tray_label` | `string` (direct vx) | `Selected items` | Accessible label for the automatic tray |
| `compare_variant` | enum: `dynamic` \| `transparent` \| `white` \| `primary` \| `primary_light` \| `primary_white` \| `secondary` \| `secondary_light` \| `secondary_white` \| `positive` \| `negative` (direct vx) | `dynamic` | Comparison button colors — the same vocabulary every other EF button offers, so the tray's action cannot drift from the rest of the interface |
| `description` | `string` (direct vx) | `''` | Shared supporting text |
| `disabled` | `boolean` (direct vx) | `false` | Disable this action without removing its configuration |
| `expand` | `boolean` (direct vx) | `true` | Expand this button to fill the available width |
| `filters` | repeater `ef-filter-item-rows` (nested vx leaves) | `[]` | Ordered visitor filters applied to the selected results loop |
| `flyout_template` | `string` (direct vx) | `''` | Template-flyout cell — data only |
| `hide_details` | `boolean` (direct vx) | `false` | Hide event details |
| `icon` | `string` (direct vx) | `''` | Icon cell — data only |
| `inline` | `boolean` (direct vx) | `false` | Run the members together on one line, wrapping at the card edge, instead of one member per line |
| `kind` | enum: `text` \| `media` \| `group` \| `accordion` \| `filter` \| `calendar` \| `toc` \| `reviews` \| `select` \| `comparison` \| `custom_code` \| `auth` (direct vx) | `text` | Choose what this content block shows |
| `label` | `richtext` (direct vx) | `''` | Human-facing title for accordion, table-of-contents, and filter sort controls |
| `layout` | enum: `week_view` \| `month_view` \| `column_view` (direct vx) | `week_view` | Cal.com booker layout |
| `limit` | `boolean` (direct vx) | `false` | Clamp the visible child rows and reveal overflow through the shared disclosure control |
| `max_heading` | enum: `h2` \| `h3` \| `h4` \| `h5` \| `h6` (direct vx) | `h3` | Deepest heading level included in the table of contents |
| `media_icon` | `string` (direct vx) | `''` | Choose an icon |
| `media_image` | `image` (nested vx leaves) | `[]` | Choose an image |
| `media_image_alt` | `string` (direct vx) | `''` | Describe the image for screen readers |
| `media_image_alt_mode` | enum: `inherit` \| `custom` \| `decorative` (direct vx) | `inherit` | Choose whether alt text comes from the attachment, a custom value, or is intentionally empty for a decorative image |
| `media_image_loading` | enum: `auto` \| `lazy` \| `eager` (direct vx) | `auto` | Choose when the image loads |
| `media_image_preload` | `boolean` (direct vx) | `false` | Preload this image when it is a known above-the-fold asset |
| `media_image_sizes` | `string` (direct vx) | `''` | Optional responsive sizes attribute |
| `media_map_pins` | repeater `ef-map-pin-rows` (nested vx leaves) | `[]` | Add pins to the map |
| `media_map_zoom` | `string` (direct vx) | `14` | Starting map zoom level |
| `media_modifiers` | `string` (direct vx) | `''` | Optional media behavior flags |
| `media_position` | enum: `inline` \| `top-edge` \| `auto-main` \| `right-main` \| `top-main` (responsive, nested vx leaves) | `inline` | Choose where this media appears |
| `media_type` | enum: `''` \| `image` \| `video` \| `icon` \| `map` (direct vx) | `''` | Choose what kind of media to show |
| `media_video_loading` | enum: `native` \| `facade` (direct vx) | `native` | Keep the initial player on video watch pages |
| `media_video_url` | `source` (nested vx leaves) | `''` | Video link or file |
| `mobile_slots_first` | `boolean` (direct vx) | `true` | Show times first on mobile |
| `mode` | enum: `login` \| `register` (direct vx) | `login` | Choose the password credential mode this row shows |
| `modifiers` | `string` (direct vx) | `''` | Kind-scoped behavior flags shared by text and reviews content rows |
| `open` | `boolean` (direct vx) | `false` | Open this accordion by default |
| `overflow_limit` | `number` (direct vx) | `1` | Rows shown before the overflow affordance appears |
| `overflow_suffix` | `string` (direct vx) | `''` | Word after a hidden count of one (for example +1 product) |
| `overflow_suffix_plural` | `string` (direct vx) | `''` | Word after a hidden count of two or more |
| `placement` | enum: `content` \| `over-media` \| `floating` \| `footer` (direct vx) | `content` | Choose the card surface that owns this group |
| `position` | enum: `left` \| `center` \| `right` \| `spread` (direct vx) | `left` | Align inline, over-media, or floating group members to the left, center, or right, or spread them across the available row |
| `redirect` | `string` (direct vx) | `''` | Optional URL the visitor lands on after a successful login or registration |
| `require_login` | `boolean` (direct vx) | `false` | Require authentication before this action can resolve or execute |
| `reviews_category` | `string` (direct vx) | `''` | Stable native Voxel review category key |
| `reviews_icon` | `string` (direct vx) | `ms:ms ms-star` | Repeated icon used to visualize the aggregate rating |
| `reviews_presentation` | enum: `icon` \| `bars` \| `compact` (direct vx) | `icon` | Choose repeated icons, one rounded progress bar, or a compact category-and-score pill |
| `reviews_star_color` | `string` (direct vx) | `yellow` | Filled rating icon or rounded bar color |
| `scope` | `string` (direct vx) | `''` | Element ID to build the table of contents from |
| `social_label` | `string` (direct vx) | `''` | Optional divider label above the provider buttons, for example 'or continue with' |
| `sorts` | repeater `ef-sort-item-rows` (nested vx leaves) | `[]` | Manifest-authorized orderings for the selected results loop |
| `style` | enum: `''` \| `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `body` \| `small` (direct vx) | `''` | Visual typography for plain Text content rows, independent of the semantic tag |
| `submit_label` | `string` (direct vx) | `''` | Optional submit button label override |
| `tag` | enum: `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `p` \| `span` \| `address` \| `ol_item` \| `ul_item` \| `rich_text` (direct vx) | `h3` | Semantic tag for plain Text content rows, or rich-text mode |
| `target` | `string` (dynamic disabled) | `''` | Comma-separated canonical Elementor element IDs of the compatible EF loops this filter updates |
| `theme` | enum: `light` \| `dark` \| `auto` (direct vx) | `light` | Light, dark, or automatic theme |
| `tooltip` | `string` (direct vx) | `''` | Short hover text shown on the button |
| `tooltip_disabled` | `string` (direct vx) | `''` | Tooltip shown when this action is disabled |
| `type` | enum: `''` \| `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `copy_to_clipboard` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `claim_post` \| `relist_post` \| `switch_listing_plan` \| `upgrade_listing_plan` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `select_addition` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `ask_chatgpt` \| `ask_perplexity` \| `ask_claude` \| `ask_copilot` \| `ask_mistral` \| `ask_google_ai` \| `vote_upvote` \| `vote_downvote` \| `set_field_value` (direct vx) | `''` | Choose what opens on click |
| `url` | `source` (nested vx leaves) | — | Optional absolute booking URL override |
| `value` | `richtext` (direct vx) | `''` | Primary authored content for text, accordion, and custom-code rows |
| `variant` | enum: `dynamic` \| `transparent` \| `white` \| `primary` \| `primary_light` \| `primary_white` \| `secondary` \| `secondary_light` \| `secondary_white` \| `positive` \| `negative` (direct vx) | `dynamic` | One shared appearance variant for text and accordion rows |

### Row surface `field-row` — Field row

6 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `autocomplete` | enum: `''` \| `name` \| `given-name` \| `family-name` \| `email` \| `tel` \| `organization` (direct vx) | `''` | Explicit browser autofill purpose |
| `label` | `string` (direct vx) | `''` | Field label shown to visitors |
| `payload` | `action_payload` (nested vx leaves) | — | Only the active field type's authored configuration |
| `placeholder` | `string` (direct vx) | `''` | Hint inside the field |
| `required` | `boolean` (direct vx) | `false` | Require visitors to fill this in |
| `type` | enum: `heading` \| `page` \| `text` \| `email` \| `textarea` \| `select` \| `upload` \| `checkbox` \| `combobox` \| `choice` (direct vx) | `text` | Choose the kind of field |

### Row surface `filter-item-row` — Filter item row

5 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `group` | `string` (dynamic disabled) | `''` | Render rows in one group are ANDed; separate groups are ORed |
| `label` | `string` (direct vx) | `''` | Optional author-facing label |
| `options` | `string` (direct vx) | `''` | Optional authored visitor choices, one value per line |
| `predicate` | `predicate` (nested vx leaves) | — | Indexed predicate source, comparison, and authored arguments |
| `scope` | enum: `include` \| `render` (dynamic disabled) | `include` | Framework-owned compatibility cell |

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
| `media_icon` | `string` (direct vx) | `''` | Choose an icon |
| `media_image` | `image` (nested vx leaves) | `[]` | Choose an image |
| `media_image_alt` | `string` (direct vx) | `''` | Describe the image for screen readers |
| `media_image_alt_mode` | enum: `inherit` \| `custom` \| `decorative` (direct vx) | `inherit` | Choose whether alt text comes from the attachment, a custom value, or is intentionally empty for a decorative image |
| `media_image_loading` | enum: `auto` \| `lazy` \| `eager` (direct vx) | `auto` | Choose when the image loads |
| `media_image_preload` | `boolean` (direct vx) | `false` | Preload this image when it is a known above-the-fold asset |
| `media_image_sizes` | `string` (direct vx) | `''` | Optional responsive sizes attribute |
| `media_map_pins` | repeater `ef-map-pin-rows` (nested vx leaves) | `[]` | Add pins to the map |
| `media_map_zoom` | `string` (direct vx) | `14` | Starting map zoom level |
| `media_modifiers` | `string` (direct vx) | `''` | Optional image behavior flags |
| `media_type` | enum: `''` \| `image` \| `video` \| `icon` \| `map` (direct vx) | `''` | Choose what kind of media to show |
| `media_video_loading` | enum: `native` \| `facade` (direct vx) | `native` | Keep the initial player on video watch pages |
| `media_video_url` | `source` (nested vx leaves) | `''` | Video link or file |
| `overflow_limit` | `number` (direct vx) | `0` | Rows shown before the overflow affordance appears |
| `overflow_suffix` | `string` (direct vx) | `''` | Word after a hidden count of one (for example +1 product) |
| `overflow_suffix_plural` | `string` (direct vx) | `''` | Word after a hidden count of two or more |
| `pill_variant` | enum: `dynamic` \| `white` \| `transparent` \| `primary_light` \| `primary_white` \| `secondary_light` \| `secondary_white` \| `primary` \| `secondary` \| `positive` \| `negative` (direct vx) | `dynamic` | Colors for last-level megamenu pills |

### Row surface `recipient-row` — Recipient row

4 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `email` | `string` (direct vx) | `''` | Custom email address receiving a copy |
| `field_rid` | `string` (dynamic disabled) | `''` | Stable row ID of an Email field in this form |
| `source` | enum: `custom` \| `user` \| `input` (dynamic disabled) | `custom` | — |
| `user_id` | `string` (dynamic disabled) | `''` | WordPress user selected by stable numeric ID |

### Row surface `result-content-row` — Result conditional content row

2 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `content` | `richtext` (direct vx) | `''` | — |
| `when` | `field_payload` | — | Optional answer predicate for this fragment |

### Row surface `result-row` — Result row

7 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `content` | `richtext` (direct vx) | `''` | Useful safe formatted result content |
| `content_blocks` | repeater `ef-result-content-rows` (nested vx leaves) | `[]` | Ordered conditional guidance appended after common result content |
| `image` | `image` (nested vx leaves) | — | Optional result image |
| `link_text` | `string` (direct vx) | `Learn more` | Text shown for the optional result link |
| `link_url` | `source` (nested vx leaves) | — | Optional result link |
| `title` | `string` (direct vx) | `''` | Required result title |
| `when` | `field_payload` | — | Optional answer predicate controlling result eligibility |

### Row surface `sort-item-row` — Sort option row

2 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `label` | `string` (direct vx) | `''` | Visitor-facing label for this ordering option |
| `ordering` | `ordering` (nested vx leaves) | — | Indexed ordering source and direction |

<!-- AUTO-GENERATED:ef-parts END -->

