# Voxel Field Inventory — theme + voxel-addon

Use this when a task asks "which field types exist?" or when authoring CPT field JSON. It is an exact inventory from source registration maps, not UI memory.

## Source-of-truth commands

```bash
# Native Voxel registry
sed -n '10,44p' sites/<site>/wp-content/themes/voxel/app/config/post-types.config.php

# voxel-addon overlay registry
grep -n "case 'field'\|=> \[\|post-relation" plugins/custom/voxel-addon/src/Components/ItemRegistry.php

# Live site merged registry, after filters/toggles/replacements
./wpdev wp <site> eval 'foreach (array_keys(\\Voxel\\config("post_types.field_types")) as $k) echo $k,"\n";'

# Existing CPT field config
./wpdev voxel:fields <site> <cpt_key>
```

## Counts

- Native Voxel post-type field types: 33, from `sites/klarc/wp-content/themes/voxel/app/config/post-types.config.php:10`.
- voxel-addon post-type field registry entries: 9, from `plugins/custom/voxel-addon/src/Components/ItemRegistry.php:79`.
- voxel-addon net-new post-type field keys: 8 (`post-relation` is a replacement/extension, not a new key).
- Live merged post-type field registry on `klarc`: 41 keys (33 native + 8 net-new addon; `post-relation` overridden in place).
- Native product subfields under `product`: 10, from `sites/klarc/wp-content/themes/voxel/app/config/product-types.config.php:27`.
- Native role/auth registration fields: `voxel:auth-email`, `voxel:auth-password`; `voxel:auth-username` class exists but is not forced by role bootstrap.
- Timeline-internal fields documented in `voxel-field-types.md` are not CPT blueprint fields.

## Native Voxel theme fields

| Type key | PHP class | Source | Storage / purpose |
|---|---|---|---|
| `title` | `Voxel\Post_Types\Fields\Singular\Title_Field` | `app/config/post-types.config.php:11`; `app/post-types/fields/singular/title-field.php` | `wp_posts.post_title`; singular title field. |
| `description` | `Voxel\Post_Types\Fields\Singular\Description_Field` | `app/config/post-types.config.php:12`; `app/post-types/fields/singular/description-field.php` | `wp_posts.post_content`; singular body/WYSIWYG field. |
| `timezone` | `Voxel\Post_Types\Fields\Singular\Timezone_Field` | `app/config/post-types.config.php:13`; `app/post-types/fields/singular/timezone-field.php` | post meta IANA timezone; needed by recurring dates/events. |
| `text` | `Voxel\Post_Types\Fields\Text_Field` | `app/config/post-types.config.php:14`; `app/post-types/fields/text-field.php` | post meta string; single-line input. |
| `number` | `Voxel\Post_Types\Fields\Number_Field` | `app/config/post-types.config.php:15`; `app/post-types/fields/number-field.php` | post meta numeric + index column sizing; range/order filters. |
| `switcher` | `Voxel\Post_Types\Fields\Switcher_Field` | `app/config/post-types.config.php:16`; `app/post-types/fields/switcher-field.php` | boolean-ish meta; false deletes meta. |
| `texteditor` | `Voxel\Post_Types\Fields\Texteditor_Field` | `app/config/post-types.config.php:17`; `app/post-types/fields/texteditor-field.php` | post meta rich/plain text. |
| `taxonomy` | `Voxel\Post_Types\Fields\Taxonomy_Field` | `app/config/post-types.config.php:18`; `app/post-types/fields/taxonomy-field.php` | WP terms for configured taxonomy. |
| `product` | `Voxel\Post_Types\Fields\Product_Field` | `app/config/post-types.config.php:19`; `app/post-types/fields/product-field.php` | Voxel product data/commerce config. |
| `phone` | `Voxel\Post_Types\Fields\Phone_Field` | `app/config/post-types.config.php:20`; `app/post-types/fields/phone-field.php` | post meta string; no native format validation. |
| `url` | `Voxel\Post_Types\Fields\Url_Field` | `app/config/post-types.config.php:21`; `app/post-types/fields/url-field.php` | post meta URL; http/https/ftp style validation. |
| `email` | `Voxel\Post_Types\Fields\Email_Field` | `app/config/post-types.config.php:22`; `app/post-types/fields/email-field.php` | post meta email; WordPress email validation. |
| `location` | `Voxel\Post_Types\Fields\Location_Field` | `app/config/post-types.config.php:23`; `app/post-types/fields/location-field.php` | address/lat/lng data; powers location/map filters. |
| `work-hours` | `Voxel\Post_Types\Fields\Work_Hours_Field` | `app/config/post-types.config.php:24`; `app/post-types/fields/work-hours-field.php` | structured opening-hours data; powers open-now filter. |
| `image` | `Voxel\Post_Types\Fields\Image_Field` | `app/config/post-types.config.php:25`; `app/post-types/fields/image-field.php` | attachment IDs / media gallery. |
| `file` | `Voxel\Post_Types\Fields\File_Field` | `app/config/post-types.config.php:26`; `app/post-types/fields/file-field.php` | uploaded attachment/file IDs. |
| `ui-step` | `Voxel\Post_Types\Fields\Ui_Step_Field` | `app/config/post-types.config.php:27`; `app/post-types/fields/ui-step-field.php` | UI-only wizard step separator; no persisted value. |
| `ui-image` | `Voxel\Post_Types\Fields\Ui_Image_Field` | `app/config/post-types.config.php:28`; `app/post-types/fields/ui-image-field.php` | UI-only image/help block; no persisted value. |
| `ui-heading` | `Voxel\Post_Types\Fields\Ui_Heading_Field` | `app/config/post-types.config.php:29`; `app/post-types/fields/ui-heading-field.php` | UI-only heading/help text; no persisted value. |
| `ui-html` | `Voxel\Post_Types\Fields\Ui_Html_Field` | `app/config/post-types.config.php:30`; `app/post-types/fields/ui-html-field.php` | UI-only Twig/HTML help block; no persisted value. |
| `repeater` | `Voxel\Post_Types\Fields\Repeater_Field` | `app/config/post-types.config.php:31`; `app/post-types/fields/repeater-field.php` | repeated nested fields; schema owns child fields. |
| `recurring-date` | `Voxel\Post_Types\Fields\Recurring_Date_Field` | `app/config/post-types.config.php:32`; `app/post-types/fields/recurring-date-field.php` | repeated date ranges; event/search recurrence support. |
| `post-relation` | `Voxel\Post_Types\Fields\Post_Relation_Field` | `app/config/post-types.config.php:33`; `app/post-types/fields/post-relation-field.php` | Voxel relation table, relation filters, relation tags. |
| `date` | `Voxel\Post_Types\Fields\Date_Field` | `app/config/post-types.config.php:34`; `app/post-types/fields/date-field.php` | post meta date/time object/string. |
| `time` | `Voxel\Post_Types\Fields\Time_Field` | `app/config/post-types.config.php:35`; `app/post-types/fields/time-field.php` | post meta time. |
| `select` | `Voxel\Post_Types\Fields\Select_Field` | `app/config/post-types.config.php:36`; `app/post-types/fields/select-field.php` | single choice from configured choices. |
| `multiselect` | `Voxel\Post_Types\Fields\Multiselect_Field` | `app/config/post-types.config.php:37`; `app/post-types/fields/multiselect-field.php` | multiple choices from configured choices. |
| `color` | `Voxel\Post_Types\Fields\Color_Field` | `app/config/post-types.config.php:38`; `app/post-types/fields/color-field.php` | hex color meta. |
| `profile-avatar` | `Voxel\Post_Types\Fields\Profile\Profile_Avatar_Field` | `app/config/post-types.config.php:39`; `app/post-types/fields/profile/profile-avatar-field.php` | user meta on post author; profile avatar. |
| `profile-name` | `Voxel\Post_Types\Fields\Profile\Profile_Name_Field` | `app/config/post-types.config.php:40`; `app/post-types/fields/profile/profile-name-field.php` | user/profile display-name data. |
| `profile-first-name` | `Voxel\Post_Types\Fields\Profile\Profile_First_Name_Field` | `app/config/post-types.config.php:41`; `app/post-types/fields/profile/profile-first-name-field.php` | user first-name data. |
| `profile-last-name` | `Voxel\Post_Types\Fields\Profile\Profile_Last_Name_Field` | `app/config/post-types.config.php:42`; `app/post-types/fields/profile/profile-last-name-field.php` | user last-name data. |
| `profile-bio` | `Voxel\Post_Types\Fields\Profile\Profile_Bio_Field` | `app/config/post-types.config.php:43`; `app/post-types/fields/profile/profile-bio-field.php` | user description/bio data. |

## voxel-addon fields

Registered by `plugins/custom/voxel-addon/voxel-addon.php:71` through `VoxelAddon\Components\ItemRegistry::register('field', ...)`. Registry map lives at `plugins/custom/voxel-addon/src/Components/ItemRegistry.php:79`.

| Type key | Class | Source | Native ancestry / storage | Notes |
|---|---|---|---|---|
| `vote` | `VoxelAddon\Modules\CustomFields\VoteField` | `ItemRegistry.php:84`; `modules/CustomFields/VoteField.php:47` | extends `Base_Post_Field`; dedicated `wp_voxel_votes` table, no post meta | Runtime aggregate only. No author-submitted value. Dynamic object exposes `upvote`, `downvote`, `total`, `score`. Toggleable. |
| `slug` | `VoxelAddon\Modules\CustomFields\SlugField` | `ItemRegistry.php:89`; `modules/CustomFields/SlugField.php:13` | extends `Base_Post_Field`; writes `wp_posts.post_name` | Singular URL slug editor. Sanitizes with `sanitize_title`; core enforces uniqueness. Toggleable. |
| `published-date` | `VoxelAddon\Modules\CustomFields\PublishedDateField` | `ItemRegistry.php:94`; `modules/CustomFields/PublishedDateField.php:21` | extends native `date`; writes `wp_posts.post_date` / `post_date_gmt` | Singular publish-date field. Uses Date_Field UI/date picker. Toggleable. |
| `icon` | `VoxelAddon\Modules\CustomFields\IconField` | `ItemRegistry.php:99`; `modules/CustomFields/IconField.php:30` | extends `Base_Post_Field`; post meta string | Stores canonical `library:value` icon string (`ms:ms ms-home`, `svg:1234`). Dynamic tag can bind direct to EF icon controls. Toggleable. |
| `excerpt` | `VoxelAddon\Fields\Excerpt_Field` | `ItemRegistry.php:104`; `includes/fields/excerpt.php:24` | extends `Base_Post_Field`; writes `wp_posts.post_excerpt` | Singular excerpt column field. Frontend type aliases to `texteditor` plain text. |
| `author` | `VoxelAddon\Fields\Author_Field` | `ItemRegistry.php:109`; `includes/fields/author.php:33` | extends native `post-relation`; writes `wp_posts.post_author`, not relation table | Profile picker UX, author column storage. Dynamic data exposes user group. Singular. |
| `parent` | `VoxelAddon\Fields\Parent_Field` | `ItemRegistry.php:114`; `includes/fields/parent.php:21` | extends native `select`; writes `wp_posts.post_parent` | Hierarchical parent dropdown. Rejects self-reference. Max choices cap 2000. |
| `main-color` | `VoxelAddon\Modules\MainColor\MainColorField` | `ItemRegistry.php:119`; `modules/MainColor/MainColorField.php:22` | extends native `color`; reads auto color unless override set | Manual override stored under field key; auto color from MainColor helper/meta. Frontend type aliases to `color`. |
| `post-relation` | `VoxelAddon\Modules\SelectionLimiting\ExtendedPostRelationField` | `ItemRegistry.php:129`; `modules/SelectionLimiting/ExtendedPostRelationField.php:29` | replaces native `post-relation`; same relation storage | Adds selection-limiting behavior while preserving native key. Not net-new; `replace => true`. |

## Native product subfields

These are not top-level CPT field types. They are nested under native `product` fields and registered from `sites/klarc/wp-content/themes/voxel/app/config/product-types.config.php:27`.

| Product subfield key | Source | Purpose |
|---|---|---|
| `base-price` | `app/product-types/product-fields/base-price-field.php`; registry `app/config/product-types.config.php:28` | Base product price. |
| `subscription-interval` | `app/product-types/product-fields/subscription-interval-field.php`; registry `app/config/product-types.config.php:29` | Subscription frequency/unit. |
| `deliverables` | `app/product-types/product-fields/deliverables-field.php`; registry `app/config/product-types.config.php:30` | File deliverables nested under product value. |
| `booking` | `app/product-types/product-fields/booking-field.php`; registry `app/config/product-types.config.php:31` | Booking calendar / slot product data. |
| `addons` | `app/product-types/product-fields/addons-field.php`; registry `app/config/product-types.config.php:32` | Product addon selections/prices. |
| `variations` | `app/product-types/product-fields/variations-field.php`; registry `app/config/product-types.config.php:33` | Variation schema with attributes/choices/images. |
| `custom-prices` | `app/product-types/product-fields/custom-prices-field.php`; registry `app/config/product-types.config.php:34` | Date/day/range custom price rules. |
| `stock` | `app/product-types/product-fields/stock-field.php`; registry `app/config/product-types.config.php:35` | Stock quantity/availability. |
| `shipping` | `app/product-types/product-fields/shipping-field.php`; registry `app/config/product-types.config.php:36` | Shipping class/config. |
| `currency` | `app/product-types/product-fields/currency-field.php`; registry `app/config/product-types.config.php:37` | Currency code. |

## Native role/auth registration fields

These are registration/auth fields, not CPT blueprint fields.

| Key | Source | Purpose |
|---|---|---|
| `voxel:auth-email` | `app/users/registration-fields/email-field.php`; forced by `app/role.php:279` | Registration email. |
| `voxel:auth-password` | `app/users/registration-fields/password-field.php`; forced by `app/role.php:280` | Registration password. |
| `voxel:auth-username` | `app/users/registration-fields/username-field.php` | Username class exists; not forced by role bootstrap scan. |

## Auto-provisioned voxel-addon field keys

These are field instances that voxel-addon can inject into CPT config. They are not separate field type slugs beyond the type column.

| Field key | Field type | Source | Purpose |
|---|---|---|---|
| `parent` | `parent` | `modules/Hierarchy/AutoProvisioner.php:174` | Parent picker for hierarchy-enabled CPTs. |
| `hierarchy-ancestors` | `post-relation` | `modules/Hierarchy/AutoProvisioner.php:224` | Hidden ancestors relation. |
| `hierarchy-children` | `post-relation` | `modules/Hierarchy/AutoProvisioner.php:267` | Hidden children relation. |
| `hierarchy-siblings` | `post-relation` | `modules/Hierarchy/AutoProvisioner.php:275` | Hidden siblings relation. |
| `main_color` | `main-color` | `modules/MainColor/AutoProvisioner.php:90` | Main-color field auto-added for thumbnail-capable CPTs. |

## Always-present fields (plan for these on every CPT)

Treat this set as present on every CPT you plan, audit, or bind a card/template to — always inventory and design for them even when a specific post leaves them empty.

| Field | Availability | Notes |
|---|---|---|
| `title` | universal | `wp_posts.post_title`; the `@post(title)` tag. Every preview card's linked heading. |
| `excerpt` | universal | `wp_posts.post_excerpt` via the voxel-addon `excerpt` field ("Search summary"); the canonical card body. |
| `permalink` | universal | `@post(permalink)` — the card heading link target. `@post(url)` resolves EMPTY in the current build; only `@post(permalink)` / `@post(:url)` resolve. |
| `_thumbnail_id` (featured image) | universal | WP featured image; the `large` card's cover/media slot. NOT a logo — the logo binds to a real logo field only (see below), never the featured image. |
| `author` | universal | Author group tags `@author(display_name)` / `@author(avatar)` (avatar is the bare attachment id, no `.id` suffix); the card byline is the author. `@post(author.*)` resolves EMPTY — use the `@author(...)` group. |
| `parent` | hierarchy-enabled CPTs | `wp_posts.post_parent`. Auto-provisioned only when the CPT is hierarchy-enabled (`voxel_addon_hierarchy_config.cpts[<slug>].enabled`), never on plain CPTs. |
| `hierarchy-ancestors` | hierarchy-enabled CPTs | Derived ancestors relation. |
| `hierarchy-children` | hierarchy-enabled CPTs | Derived children relation. |
| `hierarchy-siblings` | hierarchy-enabled CPTs | Derived siblings relation. |

**Hierarchy fields are conditional, not literally universal** — they exist only on hierarchy-enabled CPTs. When surfacing any of them on a card or template, wrap the row in a `_vx_visibility` gate keyed on the relation's `.id` (e.g. `@post(hierarchy-children.id) is_not_empty`) so a plain CPT renders nothing rather than an empty row.

**Same-parent loop rule.** Preview cards render in loops of same-parent posts, so `parent`, `hierarchy-ancestors`, and `hierarchy-siblings` resolve identically for every card in the loop — surfacing them makes every card look the same. Only `hierarchy-children` differs per card (each post's own subtree), so it is the single hierarchy field worth binding on a card body; the other three are for single/archive templates and breadcrumbs, not loop cards.

## Authoring rules

- Always inspect live merged registry before declaring a field on a site with voxel-addon enabled: `./wpdev wp <site> eval 'print_r(array_keys(\\Voxel\\config("post_types.field_types")));'`.
- Use `voxel-field-types.md` for deep per-field JSON/model/validation notes; use this file for exact availability and native-vs-addon distinction.
- Treat `title`, `description`, `timezone`, `profile-*`, `excerpt`, `author`, `parent`, `slug`, `published-date` as column/user-meta/singular style fields, not ordinary post meta.
- Treat UI fields (`ui-step`, `ui-heading`, `ui-image`, `ui-html`) as form layout fields; they do not store post data.
- Treat `vote` as runtime aggregate; never populate through create-post/import field values.
- Treat voxel-addon `post-relation` as native-compatible replacement: use key `post-relation`, but remember extra addon constraints can affect picker choices.
- API writes can fail-close on non-native addon types unless type aliasing or validator allowlist covers them; verify `modules/API/Fields/FieldValidator.php` before assuming REST/API writes work for `vote`, `slug`, `published-date`, `icon`, `excerpt`, `author`, `parent`, or `main-color`.
