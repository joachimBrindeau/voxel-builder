# Voxel Dynamic Tags: Expressions, Modifiers, And Math

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

For composition recipes (graceful empties, currency, relation summaries, math-driven badges, search-context echoes), see [`dynamic-text.md`](../ef/dynamic-text.md) — recipe-first cookbook. This file's registry-derived tables are the modifier catalog; confirm additions against `app/dynamic-data/config.php` and `app/dynamic-data/modifiers/`.

Modifiers chain left-to-right; each receives the previous step's string output. Args are literal strings (no quoting). Nested tag expressions inside an arg ARE expanded (e.g. `.fallback(@post(title))`).

### Chain semantics

Source: `app/dynamic-data/voxelscript/tokens/dynamic-tag.php`. Modifiers run left-to-right on the previous string output; arguments are literal strings after nested-tag expansion, and an empty intermediate value remains input to later fallbacks. Recipe-level patterns live in [`dynamic-text.md`](../ef/dynamic-text.md) §1.

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
