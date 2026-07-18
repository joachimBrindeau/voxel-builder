# EF Parts: Generated Row Surfaces

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
| `variant` | enum: `transparent` \| `white` \| `primary` \| `primary_light` \| `secondary` \| `secondary_light` \| `positive` \| `negative` | `''` | Button colors |
| `vote_field_key` | `string` (dynamic) | `''` | Vote field to update |

### Row surface `content-block-row` — Content block row

72 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `accordion_open` | `boolean` | `false` | Open this accordion by default |
| `accordion_variant` | `string` | `transparent` | Accordion colors |
| `address` | `string` (dynamic) | `''` | Address for directions |
| `body` | `richtext` (dynamic) | `''` | Body text with formatting |
| `brand_color` | `string` | `primary` | Booking accent color |
| `button_variant` | enum: `transparent` \| `white` \| `primary` \| `primary_light` \| `secondary` \| `secondary_light` \| `positive` \| `negative` | `''` | Button colors |
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
| `calendar_url` | `source` | — | Optional absolute booking URL override |
| `cart_text` | `string` (dynamic) | `''` | Button text after adding |
| `datafield_label` | `string` (dynamic) | `''` | Field label, like 'Surface' or 'Bedrooms' |
| `datafield_value` | `string` (dynamic) | `''` | Field value |
| `email` | `string` (dynamic) | `''` | Email address to contact |
| `group` | `string` | `default` | Placement / membership for this tag or button |
| `group_name` | `string` | `''` | Group name |
| `group_over_media` | `boolean` | `false` | Place this group over the media |
| `group_overflow_suffix` | `string` (dynamic) | `''` | Word after the hidden tag count when it is 1 (e.g |
| `group_overflow_suffix_plural` | `string` (dynamic) | `''` | Word after the hidden tag count when it is 2+ (e.g |
| `group_type` | enum: `tags` \| `buttons` | `tags` | Only rows of this type may join the group |
| `group_visible_rows` | `number` | `1` | Lines shown before +N appears |
| `hide_event_details` | `boolean` | `false` | Hide event details |
| `icon` | `string` | `''` | Optional leading icon shown on the heading line, tag pill, or button |
| `icon_active` | `string` (dynamic) | `''` | Icon shown after click |
| `kind` | enum: `heading` \| `rich_text` \| `byline` \| `separator` \| `accordion` \| `tag` \| `datafield` \| `group` \| `calendar` \| `toc` \| `button` \| `media` | `heading` | Choose what this content block shows |
| `label` | `string` (dynamic) | `''` | Button text |
| `label_active` | `string` (dynamic) | `''` | Text shown after click |
| `layout` | enum: `week_view` \| `month_view` \| `column_view` | `week_view` | Choose the layout |
| `link` | `source` (dynamic) | — | Page or link to open |
| `media_caption` | `string` | `''` | Caption shown with the media |
| `media_fit` | enum: `cover` \| `contain` | `cover` | How the image fills the space |
| `media_icon` | `string` | `''` | Choose an icon |
| `media_image` | `image` | `[]` | Choose an image |
| `media_image_alt` | `string` (dynamic) | `''` | Describe the image for screen readers |
| `media_image_loading` | enum: `auto` \| `lazy` \| `eager` | `auto` | Choose when the image loads |
| `media_map_pins` | repeater `ef-map-pin-rows` | `[]` | Add pins to the map |
| `media_map_zoom` | `string` | `14` | Starting map zoom level |
| `media_svg` | `svg` | — | Choose an uploaded vector image |
| `media_type` | enum: `image` \| `video` \| `icon` \| `svg` \| `map` | `image` | Choose what kind of media to show |
| `media_video_url` | `source` (dynamic) | `''` | Video link or file |
| `modal_id` | `string` (dynamic) | `''` | On-page modal or saved template to open |
| `phone` | `string` (dynamic) | `''` | Phone number to call |
| `position` | enum: `left-edge` \| `top-edge` \| `left-main` \| `top-main` \| `in-content` | `top-edge` | Choose media placement for each screen size |
| `scroll_to` | `string` (dynamic) | `''` | Section to scroll to |
| `separator_color` | `string` | `gray_light` | Divider color |
| `separator_spacing` | enum: `s` \| `m` \| `l` | `m` | Space above and below the divider |
| `separator_variant` | enum: `full` \| `centered` \| `partial` | `full` | Divider width |
| `slots_view_mobile` | `boolean` | `true` | Show times first on mobile |
| `style` | enum: `''` \| `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `small` | `''` | Title size |
| `tag` | enum: `h1` \| `h2` \| `h3` \| `h4` \| `h5` \| `h6` \| `p` \| `span` \| `address` | `h3` | Choose the title level |
| `text` | `string` (dynamic) | `''` | Main text for this block |
| `theme` | enum: `light` \| `dark` \| `auto` | `light` | Light, dark, or automatic theme |
| `toast_message` | `string` (dynamic) | `''` | Short message after click |
| `toc_max_heading` | enum: `h2` \| `h3` \| `h4` \| `h5` \| `h6` | `h3` | Deepest heading level included in the table of contents |
| `toc_scope` | `string` | `''` | Element ID to build the table of contents from |
| `toc_variant` | enum: `transparent` \| `primary` \| `secondary` \| `negative` \| `positive` | `transparent` | Table-of-contents link colors |
| `tooltip` | `string` | `''` | Short hover text shown on the button |
| `type` | enum: `''` \| `action_link` \| `get_directions` \| `call` \| `send_email` \| `open_modal` \| `scroll_to_section` \| `action_gcal` \| `action_ical` \| `share_post` \| `add_to_cart` \| `promote_post` \| `action_follow_post` \| `action_follow` \| `action_save` \| `edit_post` \| `delete_post` \| `unpublish_post` \| `publish_post` \| `show_post_on_map` \| `view_post_stats` \| `go_back` \| `back_to_top` \| `action_login` \| `action_logout` \| `direct_message` \| `direct_message_user` \| `open_vx_inbox` \| `open_vx_notifications` \| `open_vx_cart` \| `open_vx_user_menu` \| `open_vx_quick_search` \| `access_markdown` \| `vote_upvote` \| `vote_downvote` | `''` | Choose what opens on click |
| `variant` | enum: `white` \| `transparent` \| `primary_light` \| `secondary_light` \| `primary` \| `secondary` \| `positive` \| `negative` | `''` | Tag colors |
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

3 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `card_template` | `string` | `''` | Per-pin Elementor card template rendered (lazily, on pin click) in the pin's related-post context |
| `location` | `string` (dynamic) | `''` | Voxel location JSON or a plain address string |
| `name` | `string` (dynamic) | `''` | Marker label, tooltip, or popup text |

### Row surface `mega-row` — Mega row

8 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `link` | `source` | — | Link this item opens |
| `loop_anchor` | `string` (dynamic) | `''` | Post used for repeated links |
| `loop_anchor_type` | enum: `''` \| `custom` | `''` | Choose the source for repeated links |
| `loop_overflow_suffix` | `string` (dynamic) | `''` | Word after the hidden item count when it is 1 (e.g |
| `loop_overflow_suffix_plural` | `string` (dynamic) | `''` | Word after the hidden item count when it is 2+ (e.g |
| `loop_visible_rows` | `number` | `0` | Lines shown before +N appears |
| `meta` | `string` (dynamic) | `''` | Optional subtitle |
| `text` | `string` (dynamic) | `''` | Menu item text |

### Row surface `recipient-row` — Recipient row

1 cells.

| Cell | Type / enum | Default | Brief |
|---|---|---|---|
| `email` | `string` | `''` | Email address receiving a copy |

<!-- AUTO-GENERATED:ef-parts END -->
