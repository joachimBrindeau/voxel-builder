# Voxel Dynamic Tags, Loops, Visibility, and Feeds

Voxel-runtime concepts that apply across templates and pages. Stable across recent Voxel releases — the EF V4 atomic schema (separately) is the volatile surface.

## Static vs dynamic decision

| Render context | Default | Override when |
|---|---|---|
| CPT template (single, card, archive) | Voxel dynamic tags | A label/heading is the same for every post → static |
| Page template (`wp-page`) | Static | Page is bound to a CPT loop or shows live data |
| Loop child (inside `_vx_loop` wrapper) | `@site(loop_<type>.field)` | Same as above |
| Standalone landing page | Static | Pulling site-wide data → `@site(...)` |

**When unsure, run `wpdev voxel:data <site> --id <example_post>` and see what tags resolve to on a real post.**

## Expression syntax

Source: `app/dynamic-data/config.php` (registered groups), `app/dynamic-data/voxelscript/tokenizer.php` (parser).

The parser tokenizes `@<group>(<path>)` then a chain of `.<modifier>(<args>)` calls. Group and modifier keys must match `/^[a-zA-Z0-9_]+$/`.

| Form | Meaning |
|---|---|
| `@post(field_key)` | Current post's field value |
| `@post(:property)` | Core WP property (`:title`, `:content`, `:excerpt`, `:date`, `:id`, `:url`) |
| `@post(field:<key>)` | **Disambiguator** — forces the CPT custom-field lookup when `<key>` collides with a built-in property/group name (see Pitfall below). E.g. `@post(field:status.label)`. |
| `@post(field.subfield)` | Repeater / object-list sub-field (e.g. `@post(faq.question)`) |
| `@post(relation.field)` | Related post's field (e.g. `@post(<relation>.<field>)`) |
| `@post(parent.field)` | Parent post's field (post_parent linkage) |
| `@author(property)` | Post author data (`avatar`, `display_name`, `profile.permalink`, `profile.<field>`) |
| `@site(property)` | Site-wide data |
| `@site(loop_<type>.field)` | Current item in an EF loop iteration |
| `@current_user(property)` | Logged-in user data |
| `@term(property)` | Current term (in taxonomy templates) |
| `@user(...)`, `@user/membership(...)` | User group / membership data |
| `@order(...)`, `@orders/booking(...)`, `@orders/promotion(...)` | Order data groups |
| `@message(...)`, `@timeline/status(...)`, `@timeline/review(...)`, `@timeline/reply(...)` | Activity-feed groups |
| `{{post.field}}` / `{{author.property}}` | Template syntax (equivalent to `@`) |

Registered groups (full list): `post`, `simple-post`, `posts/relation-request`, `site`, `term`, `user`, `user/membership`, `order`, `orders/booking`, `orders/promotion`, `message`, `timeline/status`, `timeline/review`, `timeline/reply`, `value`, `noop`.

For the list of valid `<field_key>` values on a CPT, run `wpdev voxel:fields <site> <cpt_key>`.

### Pitfall — field-key collisions with built-in properties (the `field:` prefix)

When a CPT's custom field key matches a name Voxel's `post` group already resolves as a **built-in property** — `status`, `url`, `title`, `date`, `author`, `id`, `content`, `excerpt`, `slug` — the bare `@post(<key>)` resolves the **built-in**, not your field. The classic production bite: a CPT with a custom `status` select (values `open` / `closed`) wired as `@post(status.label)` renders the **WordPress post status** ("Published"), never the field's choice label.

This is silent — lint passes, no console error, the page just shows the wrong word. The disambiguator is the **`field:` prefix**, which forces the custom-field branch:

```
@post(field:status.label)     # ✅ the CPT select's label ("Open")
@post(status.label)           # ✗ resolves the WP post status ("Published")
@post(field:url)              # ✅ a CPT field literally named "url"
@post(:url)                   # the post permalink (built-in; the ':' form)
```

**How to detect the collision before it bites:** if `wpdev voxel:fields <site> <cpt_key>` lists a field whose key is in the built-in set above, always address it as `@post(field:<key>...)`. When in doubt, resolve both forms on a real post with `wpdev voxel:data <site> --id <post>` and compare — if `@post(<key>)` returns a WP system value rather than the field's data, switch to `field:`. The data-wiring plan-review criterion should flag any blueprint tag on a collision-prone key that omits the `field:` prefix.

### Pitfall — Object fields don't auto-stringify

Not every `@post(<key>)` returns a string. Some field types expose to the dtag system as a **`Tag::Object`** with sub-properties (`.value`, `.label`, `.icon`, …), and the bare `@post(<key>)` renders to **empty string** because the Object has no default `__toString`. The bug is silent at lint time — schema validation passes, no console errors at render — and only surfaces as a falsey value in `.is_not_empty()` / `.is_equal_to()` chains, dropping the template into its `.else()` fallback.

**Affected field types** (verified against `app/post-types/fields/` `dynamic_data()` methods):

| Field type | Bare `@post(<key>)` returns | Correct access pattern |
|---|---|---|
| `select` | `Tag::Object` (empty) | `@post(<key>.label)` for display · `@post(<key>.value)` for comparison |
| `multiselect` | Object-list | `@post(<key>.label).list(...)` or iterate via repeater syntax |
| `taxonomy` | Object-list | `@post(<key>.title).list(...)` |
| `post-relation` | Object / object-list (depending on cardinality) | `@post(<relation>.<target_field>)` — traverse, never read directly |
| `location` | `Tag::Object` | `@post(<key>.address)` · `@post(<key>.latitude)` · `@post(<key>.longitude)` |
| `image`, `file` | `Tag::Object` | `@post(<key>.url)` · `@post(<key>.alt)` · `@post(<key>.width)` |
| `repeater` | Object-list | iterate via `@loop` / `@post(<repeater>.<sub>)` |
| `work-hours` | `Tag::Object` | `@post(<key>.monday.from)`, etc. |
| `product` | `Tag::Object` | structured access per product subtype |

Plain string-shaped fields where the bare read works: `text`, `texteditor`, `title`, `description`, `date`, `number`, `email`, `phone`, `url`, `switcher` (returns "1"/""), `slug`, `published_date`, `excerpt`, `author` (display_name as fallback), `timezone`, all `profile-*` text fields.

**How to verify before shipping a template.** Run `wpdev voxel:data <site> --id <example_post>` — the JSON output reports the actual value a field exposes to the dtag system. If a key shows `"product-type": "skincare"` (raw string), the bare read works; if it shows `"product-type": {"value": "skincare", "label": "Skincare"}` or empty `""`, use `.label` / `.value`.

> 💡 **Replace `.is_equal_to()` comparator chains on select fields with `.label`.** For a select field with N choices, the natural-looking template is N nested `.is_equal_to(k).then(L).else(...)` branches. Voxel already maps value → label via `get_selected_choice()`; just write `@post(<key>.label).is_not_empty().then(@post(<key>.label)).else(<fallback>)` and skip the branching entirely.

### Group methods

Source: `app/dynamic-data/modifiers/group-methods/`, `app/dynamic-data/data-groups/base-data-group.php` (`get_modifier`).

> ⚠️ **CRITICAL SYNTAX — group methods are MODIFIERS, not a dot-namespace.** A group method is registered in the group's `methods()` array and resolved through the **exact same modifier path** as `.round()` / `.uppercase()` (`base-data-group.php:110-122` → `dynamic-tag.php:40-56`). It therefore MUST be chained onto a **closed tag** with empty (or property-filled) parens: **`@site().math(...)`**, NOT `@site.math(...)`.
>
> The dot form `@group.method(...)` **never tokenizes** — the tokenizer requires `(` immediately after the group key (`tokenizer.php:64`); a `.` there aborts tag parsing and the whole thing is emitted as **plain text** (silent literal leak, no lint error, no console error). Verified end-to-end via `\Voxel\render()` and at the tokenizer (`@site.math(1+1)` → 0 tags, full text leak; `@site().math(1+1)` → `2`).

| Expression | Group | Purpose |
|---|---|---|
| `@post().meta(<key>)` | post | `get_post_meta()` lookup |
| `@user().meta(<key>)`, `@current_user().meta(<key>)` | user | `get_user_meta()` lookup |
| `@term().meta(<key>)` | term | `get_term_meta()` lookup |
| `@term().post_count(<post_type?>)` | term | Posts attached to this term. Empty arg sums across all CPTs; pass a specific CPT key to scope. |
| `@site().query_var(<name>, raw?)` | site | First checks `\Voxel\get_visibility_context_query_var()` (so feed/popup contexts can inject values), then falls back to `$_GET[name]`. Result is `wp_unslash`'d and HTML-escaped unless the 2nd arg is exactly `raw`. Non-scalar returns null. |
| `@site().math(<expression>)` | site | Evaluates an arithmetic expression — see Math expressions |

## `@tags()` wrapper requirement

Dynamic tag expressions bound to **string-type prop values** in Elementor settings (heading text, body text, action labels, link URLs, image alt, anything resolved as a rendered string at runtime) MUST be wrapped:

```
@tags()@site(loop_post.title)@endtags()
@tags()@post(:excerpt)@endtags()
@tags()@author(display_name)@endtags()
```

Voxel's custom Elementor controls check for the `@tags()` prefix before invoking `\Voxel\render()`. Without the wrapper on a string-type prop, the literal `@post(...)` text leaks into the rendered HTML.

**Exception:** the `vx` `$$type` envelope holds the raw expression without `@tags()`. This is used for non-string prop slots — `_cssid` (id binding) and image-id refs (attachment IDs the renderer dereferences directly):

```
{$$type: 'vx', value: '@post(types.slug)-@post(slug)'}
{$$type: 'vx', value: '@post(_thumbnail_id.id)'}
```

When in doubt about which form to use for a prop, query `wpdev elementor:schema <site> <widget> --prop <key>` — the `default` field shows the canonical envelope shape.

## Modifiers

Source: `app/dynamic-data/config.php` (registry), `app/dynamic-data/modifiers/*.php`. The list below is exhaustive. Voxel has NO `.lower`, `.upper`, `.urlencode`, `.json_encode`, `.strip_tags`, `.add_days`, `.implode`, `.slice`, `.starts_with`, `.ends_with`, `.add/subtract/multiply/divide/modulo`, `.floor/ceil/abs`, `.format_number`, `.format` modifiers — use `@site().math(...)`, `.number_format()`, `.contains()`, or `.list()`.

For composition recipes (graceful empties, currency, relation summaries, math-driven badges, search-context echoes), see [`dynamic-text.md`](../ef/dynamic-text.md) — recipe-first cookbook. The catalog under `docs/solutions/best-practices/voxel-modifier-catalog.md` is the source-of-truth registry walk.

Modifiers chain left-to-right; each receives the previous step's string output. Args are literal strings (no quoting). Nested tag expressions inside an arg ARE expanded (e.g. `.fallback(@post(title))`).

### Chain semantics

Source: `app/dynamic-data/voxelscript/tokens/dynamic-tag.php` lines 39-57. Canonical pseudocode + three rules + footgun explanation live in `docs/solutions/best-practices/voxel-modifier-catalog.md` §"Chain evaluation semantics". Recipe-level patterns in [`dynamic-text.md`](../ef/dynamic-text.md) §1.

### String

Source: `app/dynamic-data/modifiers/{append,prepend,truncate,replace,capitalize,fallback}-modifier.php`.

| Modifier | Args | Purpose |
|---|---|---|
| `.fallback(text)` | text | Returns `text` when value is empty |
| `.append(text)` | text | Concat after value |
| `.prepend(text)` | text | Concat before value |
| `.capitalize()` | — | `ucwords()` — title-cases each word |
| `.truncate(len)` | int (default 130) | Trims to `len` chars via `\Voxel\truncate_text` |
| `.replace(search, replace)` | search, replace | String replace |

### Numeric

Source: `app/dynamic-data/modifiers/{round,number_format,currency_format,abbreviate}-modifier.php`.

| Modifier | Args | Purpose |
|---|---|---|
| `.round(decimals)` | int (default 0; negative rounds tens/hundreds) | `round()` |
| `.number_format(decimals)` | int (default 0) | `number_format()` with thousands separator |
| `.currency_format(currency, in_cents?, force_decimals?)` | currency code or `default`, bool, bool | Renders amount with currency symbol; `in_cents=1` divides by 100 |
| `.abbreviate()` | — | `1500` → `1.5k`, `12000000` → `12m` (suffixes: k/m/b/t) |

### Date

Source: `app/dynamic-data/modifiers/{date_format,time_diff,to_age}-modifier.php`.

| Modifier | Args | Purpose |
|---|---|---|
| `.date_format(fmt)` | PHP date format string | Formats a date value (`j F Y`, `Y-m-d`, etc.) |
| `.time_diff(timezone?)` | tz id or offset (e.g. `Europe/London`, `+02:00`) | Human-readable diff (`2 hours ago`) relative to given tz |
| `.to_age()` | — | Years between value (date of birth) and now |

### Collection (object-list / repeater / multi-value fields)

Source: `app/dynamic-data/modifiers/{count,first,last,nth,list}-modifier.php`. All except `.list()` require an array-typed input (`expects() = TYPE_ARRAY`).

| Modifier | Args | Purpose |
|---|---|---|
| `.count()` | — | Item count of an object-list / repeater |
| `.first()` | — | Picks index 0 of the nearest loopable in the property path. Attach AFTER the full sub-field path (`@post(faq.question).first()`), not in the middle (`@post(faq.first.question)` would look for a literal sub-field named `first` and resolve to empty). |
| `.last()` | — | Same, last index. |
| `.nth(index)` | int; negative allowed (`-1` = last) | Same, arbitrary index. Out-of-bounds returns `''`. |
| `.list(separator?, last_separator?, prefix?, suffix?)` | strings | Joins items: e.g. `.list(, , and )` → `a, b and c`; `prefix`/`suffix` wrap each item |

### Comparison (control structures)

Source: `app/dynamic-data/modifiers/control-structures/`. These set a boolean flag consumed by the next `.then()`/`.else()` — they do NOT change the value themselves. Numeric comparisons fall back to `strtotime()` for date strings.

| Modifier | Args | Passes when |
|---|---|---|
| `.is_empty()` | — | value is `''` |
| `.is_not_empty()` | — | value is non-empty |
| `.is_equal_to(v)` | v | strict `===` match |
| `.is_not_equal_to(v)` | v | strict `!==` match |
| `.is_greater_than(v, mode?)` | v, `>=` for inclusive | numeric or date `>` v |
| `.is_less_than(v, mode?)` | v, `<=` for inclusive | numeric or date `<` v |
| `.is_between(start, end)` | start, end | numeric or date in range |
| `.is_checked()` | — | value non-empty (switch/checkbox truthy) |
| `.is_unchecked()` | — | value empty (switch/checkbox falsy) |
| `.contains(needle)` | needle | `mb_stripos` finds needle (case-insensitive) |
| `.does_not_contain(needle)` | needle | inverse of above |

### Conditional output

Source: `app/dynamic-data/modifiers/control-structures/{then,else}-control.php`. `.then()` / `.else()` consume the boolean from the most recent comparison and emit their argument as the new value.

| Modifier | Emits |
|---|---|
| `.then(content)` | `content` if previous comparison passed |
| `.else(content)` | `content` if previous comparison failed |

### Chaining examples

```
@post(:date).date_format(Y).is_equal_to(2026).then(New).else(Archive)
@post(price).is_greater_than(100).then(Premium).else(Standard)
@post(faq).count().is_equal_to(0).then().else(@post(faq).count() questions)
@post(tags.title).list(, , and )
@post(types.slug)-@post(slug).truncate(60)
@site().math(@post(price) * 1.2).round(2).currency_format(EUR)
```

## Math expressions

Source: `app/utils/utils.php` (`evaluate_math_expression`), `app/dynamic-data/modifiers/group-methods/site-math-method.php`. Backed by the `NXP\\MathExecutor` library.

Voxel does NOT support inline arithmetic in `{{ ... }}` or `@post(...)`. To compute, wrap the expression in `@site().math(...)` (empty parens on the `@site` tag, then the `.math` modifier — see the group-methods syntax warning above; `@site.math(...)` leaks as literal text):

```
@site().math(@post(price) * 1.2)
@site().math((@post(stock) - @post(reserved)) / @post(stock) * 100)
@site().math(@post(rating_total) / @post(rating_count))
```

Supported operators: `+`, `-`, `*`, `/`, `%` (modulo), `^` (power), parentheses for precedence. Nested `@<group>(...)` tags inside the expression are resolved BEFORE evaluation, so the math executor sees plain numbers.

> ⚠️ **Parens live in the MODIFIER ARG, never in the group property.** The tokenizer tracks paren depth only inside modifier args (`tokenizer.php:148-189`), NOT inside a tag's property path, which stops at the **first** `)` (`tokenizer.php:80-101`, depth-blind). So `(a - b) / c` MUST sit in the `.math(...)` **arg** — `@site().math((a - b) / c)` ✅. Writing the expression into the property — `@site(math((a - b) / c))` — breaks at the first inner `)`: even `@site(math(2 - 1))` renders as `1)` with the tail leaking. This is why `@site().math(...)` (method) is mandatory, not just stylistic.

Built-in helpers registered by Voxel:
- `discount(old, new)` → percentage discount: `((old - new) / old) * 100`
- `random_int(min=1, max=10)` → integer in range

Standard `MathExecutor` functions are also available (`abs`, `min`, `max`, `round`, `floor`, `ceil`, `sqrt`, `pow`, `sin`, `cos`, `%` / `fmod`, `if(<expr>, <a>, <b>)`, etc.). Errors return an empty string and log via `qm/debug`.

The result is a number — chain `.round()`, `.number_format()`, or `.currency_format()` to format.

### Duration between two date fields (`date_format(U)` → math)

`.time_diff()` is NOT a duration primitive — it takes ONE date and diffs against **now** (its arg is a *timezone string*, not a second date; `Time_Diff_Modifier` → `human_time_diff($ts, time())`). Passing a second date into `.time_diff(<end>)` silently discards it (fails `new DateTimeZone(<end>)` → falls back to site tz) and returns "N days ago"-style elapsed-since-now. To compute a real **start→end duration**, convert each date to a Unix timestamp inline with `.date_format(U)` and subtract inside `@site().math(...)`:

```
# whole hours
@site().math(floor((@post(<field>.previous.end).date_format(U) - @post(<field>.previous.start).date_format(U)) / 3600))
```

`date_format(U)` renders the PHP `U` format (Unix seconds), so no extra numeric field is needed (supersedes the older "store the date as a Unix timestamp in a numeric field" workaround). Divide by `60` for minutes, `86400` for days. `% 60` gives the leftover-minutes component.

**`HhMM` clock format** (e.g. `1h45`, `2h00`) — hours, literal `h`, then zero-padded minutes via a two-branch pad (MathExecutor has no `sprintf`/string-concat, so pad with a control structure):

```
@site().math(floor((<diff>) / 3600))h@site().math((<diff>) / 60 % 60).is_less_than(10).then(0@site().math((<diff>) / 60 % 60)).else(@site().math((<diff>) / 60 % 60))
```

where `<diff>` = `@post(<field>.end).date_format(U) - @post(<field>.start).date_format(U)`. For a `X heure(s)` / `XhMM` mixed format, add an outer `@site().math((<diff>) / 60 % 60).is_equal_to(0).then( heure).else(h<padded-minutes>)` branch, and pluralise the hour word with a separate `@site().math(floor((<diff>)/3600)).is_equal_to(1).then(heure).else(heures)`. Recurring-date fields expose only `start` / `end` / `is_multiday` / `is_allday` (+ `is_happening_now` on `upcoming`) per item — there is **no `duration` property**; you always compute it.

## Loops

Any `ef-wrapper` becomes a loop by setting `_vx_loop` (Voxel-side scope) and optionally `_ef_loop_transform` (EF-side filter / sort / reverse). The wrapper and its children are cloned once per matched post.

| Key | Owner | Notes |
|---|---|---|
| `_vx_loop` | Voxel | Iteration scope — bound to a post-type loop (`loop_<post_type_key>`) via the Dynamic affordance band's loop picker. Modern preferred name. |
| `_vx_visibility` | Voxel | Conditional rendering — bound via the Dynamic affordance band's visibility picker. Modern preferred name. |
| `_ef_loop_transform` | EF | EF-owned filter / sort / reverse parity for atomic widgets — sibling of `_vx_loop`. Universal on every EF widget (auto-merged by `ef_atomic_base_props()`). |
| `_ef_loop_sort` | EF | Sort order enum on `ef-wrapper` loop hosts — query schema for current values. |
| `_ef_loop_initial` | EF | Initial visible-item count when load-more chunking is on. |
| `_ef_loop_more_label` | EF | Load-more button label. |
| `_ef_loop_less_label` | EF | Load-less button label. |
| `_voxel_loop` / `_voxel_loop_limit` / `_voxel_loop_offset` | legacy | V3 names — still recognized on read by `ef_with_voxel_loop()` for back-compat, but new JSON should use the `_vx_*` / `_ef_loop_*` set above. |
| `_voxel_visibility_rules` / `_voxel_visibility_behavior` | legacy | V3 visibility shape — recognized for back-compat; new JSON uses `_vx_visibility`. |

EF strips Voxel's three (VX) sections (`_vx_loop`, `_vx_visibility`, `_vx_dynamic_css`) from EF widget panels and replaces them with the **General → Dynamic** affordance band — three icon pickers bound to `_vx_loop` / `_vx_visibility` / `_ef_loop_transform`. Voxel's panels still appear on third-party (non-EF) widgets unchanged.

### Placement decision: WIDGET-level vs ROW-level vs ts-post-feed

This is the single most expensive mistake to get wrong. Picking the wrong placement renders something — but it iterates the wrong thing, and the symptom only appears on item 2+. Pick by what should be **replicated**:

| Goal | Place loop here | Source-code evidence |
|---|---|---|
| Replicate the **entire widget** per item (e.g. one `ef-card` becomes N cards) | `settings._vx_loop` (widget-level) on the widget itself | `loop-controller.php:142-173` hooks `elementor/frontend/widget/before_render` and replicates the whole widget per iteration via `Looper::run` |
| Iterate **one row of a composite repeater** (heading row, accordion row, action row) inside one widget | `settings.<repeater>.value[N].value._vx_loop` (row-level, V4 envelope) | `EF_Loopable_Row_Prop_Type` — `includes/props/loopable-row-prop-type.php:43-73` |
| Render a **feed of cards from a relation/CPT** with pagination, sort, search-form connection | `ts-post-feed` widget — NOT `_vx_loop` | [`widgets.md`](../ef/widgets.md) §EF loop vs ts-post-feed |

Before any loop work, **read these two files once** so the placement decision is grounded:

```bash
sites/<site>/wp-content/plugins/elementor-framework/includes/loop-controller.php       # widget-level
sites/<site>/wp-content/plugins/elementor-framework/includes/props/loopable-row-prop-type.php  # row-level
```

Common pattern for a "list of cards" section:
- Outer `ef-wrapper` provides the section structure — NOT looped.
- Inner `ef-card` (or `ef-wrapper`) carries `_vx_loop` at widget level — IS looped.
- Children reference `@site(loop_<type>.field)` — resolved per iteration.
- The `author` sub-property works inside loops (EF registers it on the post data group).

Common pattern for a "row inside a card" loop (e.g. timeline events on a single card):
- The `ef-card` itself is NOT looped (one card renders).
- The card's heading-rows / action-rows / tag-rows repeater carries `_vx_loop` at row level — that ONE row is iterated, the rest of the card is fixed.

For an EF-loop-vs-`ts-post-feed` decision, see [`widgets.md`](../ef/widgets.md) §EF loop vs ts-post-feed.

## Visibility rules

Conditional rendering via `_vx_visibility` (modern) on any widget or repeater item. Shape (verify via `wpdev elementor:schema <site> <widget> --prop _vx_visibility`):

```
_vx_visibility: { rules: [[{type: 'dtag', tag: '@post(:id)', compare: 'is_not_equal_to', arguments: ['<id>']}]], behavior: 'show' }
```

The legacy `_voxel_visibility_rules` array shape is still expanded by `ef_has_voxel_visibility()` for back-compat reads.

Common operators: `is_equal_to`, `is_not_equal_to`, `is_not_empty`, `is_empty`. Outer array is OR-of-AND-groups.

`behavior: 'hide'` inverts (hide when rules match instead of show).

Common use: prevent a related-posts feed item from referencing the current post (filter out by `:id`).

## Migration rule — preserve dynamic expressions

**Never strip, modify, or HTML-encode dynamic tag expressions.** Before any content cleanup, scan the value for these markers and skip if any are present:

```
@post(  @author(  @site(  @current_user(  @tags(
{{post.  {{author.  {{site.
```

Voxel renders these at runtime — escaping or stripping breaks the binding silently.

## Feeds: prerequisites and connection rules

`ts-post-feed` renders nothing without setup. The CPT must have `search.filters` and `search.order` configured (see [`blueprint-format.md`](../core/blueprint-format.md) §Search config) and an index table populated.

### Filter types

The CPT's `search.filters` array supports:

| Type | Purpose |
|---|---|
| `keywords` | Full-text search across `sources` (e.g. `title`, `description`, `content`) |
| `terms` | Filter by taxonomy term |
| `parent` | Filter by parent post (post_parent) |
| `relations` | Filter by a `post-relation` field |
| `date` | Date range filter |

### Sort clause types

The CPT's `search.order[].clauses` support:

| Clause type | Use |
|---|---|
| `text-field` | Sort by text field value (title, h1) |
| `date-created` | Sort by creation date |
| `relevance` | Sort by keyword match score |
| `random` | Random ordering (with optional `seed`) |

### Source modes

`ts-post-feed.ts_source`:
- `search-filters` — dynamic; syncs with page's search form OR uses the feed's own `ts_filter_list__<type>` overrides
- `manual` — fixed list via `ts_manual_posts` (each `{_id, post_id}`)
- `search-form` — feed only renders after form submit
- `archive` — uses WP archive query

### Connection integrity

When a page has both `ts-search-form` and `ts-post-feed`:
- The form's `ts_post_to_feed` references the feed's element `id`
- Recreating the feed widget with a new `id` breaks the connection
- Same applies to `connect_map` (form → map) and `ts_card_template__<type>` / `ts_manual_card_template__<type>` (post IDs to the rendered card templates)
- After any restructure, verify these references resolve

For the canonical settings shape on any `ts-*` widget, dump a known-good production instance:

```bash
wpdev elementor:dump <site> ts-post-feed   --post <prod_post_id> --json
wpdev elementor:dump <site> ts-search-form --post <prod_post_id> --json
```

## Voxel index table

Feeds query the Voxel index table, not `wp_posts` directly. New CPTs need their index table created and posts indexed before feeds render results.

```php
$pt = \Voxel\Post_Type::get('<key>');
$pt->index_table->create();

$posts = get_posts(['post_type' => '<key>', 'post_status' => 'publish', 'posts_per_page' => -1, 'fields' => 'ids']);
foreach ($posts as $post_id) {
    \Voxel\Post::force_get($post_id)->index();
}
```

New posts are auto-indexed on publish. Only the initial setup needs manual indexing.

## Relation fields

Voxel `post-relation` fields create queryable connections between CPTs. Feed filters reference these via `ts_choose_filter` + `<filter_key>:value`. Templates access related data via dot-notation:

- `@post(<relation>.title)` / `.permalink` — core props of the related post (always safe)
- `@post(parent.title)` — parent post (via `post_parent`)
- `@post(children.title)` — child posts (in a loop context)
- `@post(<relation>.:<core>)` — explicit core WP property (e.g. `@post(children.:excerpt)`)

### Single-type vs multi-type relations

A `post-relation` field is configured to point at one or many target CPTs (the `post_types` prop). Traversal behaviour depends on this:

- **Single-type relations** — dot-traversal resolves any field on the target CPT: `@post(<relation>.<field_on_target>)`. Sub-keys like `.id` on image fields work too. Example: `@post(<relation>.<title_field>)` returns the target post's title field; `@post(<relation>.<image_field>.id)` returns the target's image attachment ID.
- **Multi-type relations** — resolution goes through `Simple_Post_Data_Group`, NOT the target CPT's full data group. Custom fields on targets are unreachable. Use the registered base accessors (`title`, `permalink`, `excerpt`, `slug`, `content`, `id`, `date_created`, `status`, `post_type`, ...) or their colon aliases (`.:title`, `.:url` ← alias for `permalink`, `.:excerpt`, `.:id`, `.:date`, ...). **`.:permalink` does NOT exist** — use bare `.permalink` or `.:url`. See **Post-relation accessors** in `docs/solutions/best-practices/voxel-modifier-catalog.md` for the verified bare ↔ alias map.
- **`(no target configured)` relations** — `wpdev voxel:fields` reports this when a relation field is registered without an explicit target list. Treat as multi-type for safety: registered base accessors only. Even when the relation resolves to a single CPT in practice (verifiable via `wpdev voxel:data`), the skill can't prove that statically.

### How to detect single-vs-multi

Run `wpdev voxel:fields <site> <cpt_key>`. The `RELATION TARGET` column reports `single → <cpt>`, `multi → <cpt>, <cpt>`, or `(no target configured)` for every `post-relation` field. Single-type relations are then expanded below the table with the full list of traversable `@post(<relation>.<field>)` expressions for that target — copy-paste ready.
