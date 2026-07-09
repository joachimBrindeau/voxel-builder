# Voxel Dynamic Text Cookbook

How to compose **high-quality dynamic strings** on Voxel CPT templates and Elementor pages — fallbacks that don't blank out, prices that localise, lists that read like prose, conditional badges that actually evaluate, relation summaries that survive multi-type relations, and math that respects the runtime.

This file is recipe-first. For the underlying tag grammar, the full modifier registry, the canonical chain-evaluator pseudocode, the visibility-rule registry, the math-executor operator inventory, and the loop-runtime bifurcation, see [`voxel-tags.md`](../voxel/voxel-tags.md). For relation-shape introspection, see [`widgets.md`](widgets.md).

## When to load this file

The voxel-builder routing table sends these requests here:

- "Build dynamic text on a CPT template"
- "Improve the copy on this card / hero / heading"
- "Make this label smart" / "make this dynamic"
- "Show graceful fallback when X is empty"
- "Format the price / date / count"
- "Build a relation summary"
- "Compute X from Y" (anything math-shaped)

If the work is widget-shape / repeater-shape / layout, return to [`build.md`](../../workflows/build.md) or [`widgets.md`](widgets.md).

## Pre-flight: four questions before writing any expression

1. **Where does the value come from?** `@post(...)` (current post field) / `@author(...)` / `@site(...)` / `@current_user(...)` / `@term(...)` / `@site().query_var(...)` (URL param). Inside a loop the row's looped post is `@post(...)` (the loop scopes it) — see [`widgets.md`](widgets.md) for the loop-row gotcha.
2. **What shape is it?** `string` / `number` / `date` / `array` (object-list / repeater / multi-value field). The shape determines which modifiers are useful.
3. **What should the empty case render?** Voxel does not silently render placeholder text. If the field is empty, the tag resolves to `''` and your sentence falls apart unless you wrap with `.fallback(...)` or `.is_empty().then().else(...)`.
4. **Are we inside a loop?** Inside `_vx_loop`, `@post(...)` resolves against the looped post, NOT the page's current post. Inside a loop iterating a relation (`@post(<relation>)`), traversing back through the same relation re-traverses against the looped post and usually yields empty — use `@post(<field>)` against the looped post instead.

## §1 — Chain semantics (summary)

Three rules to remember when authoring recipes (full chain-evaluator pseudocode in [`voxel-tags.md`](../voxel/voxel-tags.md) §Chain semantics):

1. **Every comparison overwrites `$last_condition`.** `.is_greater_than(100).is_less_than(500).then(Mid)` does NOT logically AND — the second comparison clobbers the first. For ranges use `.is_between(100, 500)`. For compound predicates compute via `@site().math(...)` and compare its result.
2. **Non-control-structure modifiers after a failed comparison silently skip their `apply()`** but still run any `passes()` that follow.
3. **`.then(X)` / `.else(X)` are control-structures** that mutate the value when their flag holds, then leave the flag for the next comparison to overwrite.

**Safe two-state pattern:**

```text
@post(price).is_greater_than(500).then(Premium).else(Standard)
```

Single comparison, single emit. Do not chain a second comparison after `.then()` / `.else()` — the second comparison runs against the post-`.then()` value, not the original. For more than two branches: split into separate output fields with `_vx_visibility` rules, or rank inside `@site().math(if(..., ..., ...))` and map once.

## §2 — Recipes by goal

Each recipe lists the expression, an `assert` line showing what it resolves to on a sample post, and notes on variants.

### Recipe 1: graceful empty fallback

```text
@post(<field>).fallback(@post(:title))
```

`assert` — when `<field>` is empty, renders the post title. Otherwise renders the field value.

The `.fallback(...)` arg can itself contain dynamic tags — Voxel resolves nested expressions inside modifier args.

> **Tokenizer note:** like all modifier args, `.fallback(...)` content cannot contain a literal comma at depth 1; the tokenizer treats `,` as an arg boundary. `.fallback(Hello, World)` parses as TWO args and only the first is used. To include a comma, use a non-comma alternative or pre-format the source field.

Use this aggressively on heading rows and card subtitles where blank fields ruin the layout. For a static fallback: `@post(subtitle).fallback(View details)`.

### Recipe 2: price with currency, optional cents source

```text
@post(price).currency_format(EUR)                  → "€199.00" (whole units, force_decimals=1 to enforce)
@post(price_cents).currency_format(EUR,1)          → "€199.00" (stored as cents, e.g. Stripe)
@post(price).currency_format(default)              → platform-default currency (\Voxel\get_primary_currency())
```

### Recipe 3: graceful price (empty → "On request")

```text
@post(price).is_empty().then(On request).else(@post(price).currency_format(EUR))
```

`assert` — `"On request"` when `price` is missing, `"€199.00"` when set. The `.else(...)` arg re-resolves `@post(price)` — the value isn't shadowed by the `.is_empty()` branch.

### Recipe 4: price with discount badge

```text
@site().math(discount(@post(old_price), @post(price))).round().append(% off)        → "20% off"
@site().math(@post(old_price) - @post(price)).round(2).currency_format(EUR).prepend(Save )  → "Save €40.00"
```

### Recipe 5: relative time

```text
@post(:date).time_diff()                  → "2 hours ago"
@post(:date).time_diff(Europe/Paris)      → with viewer timezone
@post(:date).date_format(j F Y)           → "2 May 2026" (absolute)
@post(date_of_birth).to_age().append( years old)
```

### Recipe 6: list as prose

> **Tokenizer constraint:** modifier args are split on `,` at depth 1 by the tokenizer (`app/dynamic-data/voxelscript/tokenizer.php:165`). There is **no escape syntax** for a literal comma inside an arg. So `.list(, , and )` does NOT parse as `(sep=", ", last_sep=" and ")` — it parses as four args (`""`, `""`, `" and "`, `""`), wrapping every item with `" and "` as the prefix. The full `(sep, last_sep, prefix, suffix)` signature is structurally real but practically inaccessible whenever any arg should contain a comma.

```text
@post(<field>).list()              → "Vegan, Gluten-free, Halal"    (default ", ")
@post(<field>).list( • )           → "Vegan • Gluten-free • Halal"
@post(<field>).list( - )           → "Vegan - Gluten-free - Halal"
@post(<field>).list( | )           → "Vegan | Gluten-free | Halal"
```

For prose joining ("A, B and C"), there's no built-in way. Workarounds: accept the comma form (Oxford style without the "and"); render with bullet separator and let styling carry meaning; register a custom modifier via `voxel/dynamic-data/modifiers` filter.

For relation fields, traverse a sub-key (typically `:title`) before `.list()`:

```text
@post(<single_type_relation>.<field_on_target>).list( • )
@post(<multi_type_relation>.:title).list( • )
```

### Recipe 7: count with pluralisation

```text
@post(faq).count().is_equal_to(0).then(No questions yet).else(@post(faq).count() questions)
@post(reviews).count().is_equal_to(1).then(1 review).else(@post(reviews).count() reviews)
```

Voxel does not provide a `pluralize()` helper. Two-branch `then/else` is the canonical pattern.

### Recipe 8: nth-item picker

`.first()` / `.last()` / `.nth(<i>)` attach at the END of the chain, after the full sub-field path. They do NOT slot into the middle of the property path (the tokenizer would treat `first` as a literal sub-field name and the lookup would return empty).

```text
@post(testimonials.author).first() → "Marie"
@post(testimonials.body).first()   → "Excellent service throughout."
@post(stages.label).nth(-2)        → "the second-to-last"
```

Out-of-bounds returns `''` — wrap with `.fallback(...)` if it matters.

### Recipe 9: conditional badge from numeric range

Three tiers (`€`, `€€`, `€€€`) don't compose in a single dynamic-tag chain because each `.is_*` comparison overwrites the flag. Two valid patterns:

**Option A (preferred): per-row visibility rules.** Three repeater rows or three text widgets, each with `_vx_visibility` rules on the appropriate `is_between` / `is_greater_than` clause. Voxel evaluates each rule independently — no chain interference. See [`voxel-tags.md`](../voxel/voxel-tags.md) §Visibility rules for the full rule registry.

**Option B: rank inside `@site().math(...)` then map.** The math executor supports comparison operators (`<`, `>=`, …) and a built-in `if(<expr>, <true_val>, <false_val>)` helper:

```text
@site().math(if(@post(price) < 50, 1, if(@post(price) < 200, 2, 3)))
.is_equal_to(1).then(€).else(@site().math(if(@post(price) < 200, 2, 3)).is_equal_to(2).then(€€).else(€€€))
```

`if(...)` (NOT C-style `?:` ternary — that doesn't parse in MathExecutor and the expression returns empty silently). Functional but ugly — Option A is cleaner.

### Recipe 10: conditional badge from string presence

```text
@post(category-name).contains(featured).then(★ Featured).else()
```

Only emits "★ Featured" when the category name contains "featured" (case-insensitive). The `.else()` with empty arg drops to `''`, useful when the heading row's parent has a `.is_not_empty()` visibility rule.

### Recipe 11: search-form context echo

When a `ts-search-form` posts to a `ts-post-feed`, query params land on the URL:

```text
@site().query_var(s).is_not_empty().then(Results for "@site().query_var(s)").else(All results)
```

`@site().query_var(<name>)` HTML-escapes by default. Opt out with `@site().query_var(<name>, raw)` (rare; only when you control the next layer's escaping). Voxel checks the visibility-context query var first (so feed-driven contexts can inject values without `$_GET`), then falls back to `$_GET[<name>]`.

### Recipe 12: relation summary (single-type)

```bash
wpdev voxel:fields <site> <cpt_key>     # Always start here — RELATION TARGET column reports single → <cpt> or multi → ...
```

**Single-type relations** allow traversal into any field on the target:

```text
@post(<relation>.title) — @post(<relation>.<field_on_target>)     → "France — Western Europe"
@post(<relation>.<image_field>.id)                                → image attachment ID
@post(<relation>.permalink)                                       → URL
```

### Recipe 13: relation traversal (multi-type)

Multi-type relations resolve through Voxel's `Simple_Post_Data_Group`, which exposes a fixed accessor surface — **NOT** the target CPT's custom fields. Safe only when the sub-key matches one of the registered accessors.

**Bare ↔ colon-alias accessors:** `title`/`:title`, `permalink` (bare only — NO `:permalink` alias) / `:url`, `excerpt`/`:excerpt`, `id`/`:id`, `date_created`/`:date`, `author`/`:author`, `featured_image`/`:logo`, `status`/`:status`.

```text
@post(<relation>.title) — @post(<relation>.date_created).date_format(Y)
@post(<relation>.:title) — @post(<relation>.:date).date_format(Y)       → "Atelier Brevet — 2024" (both forms equivalent)

@post(<relation>.permalink)        ✓ works
@post(<relation>.:url)             ✓ works (alias for permalink)
@post(<relation>.:permalink)       ✗ EMPTY — no such alias
```

Custom fields on target CPTs (`@post(<multi_relation>.<custom_field>)`) are unreachable regardless of prefix because `Simple_Post_Data_Group` does not expose them. Always check `wpdev voxel:fields` to confirm `single → <cpt>` before traversing into custom fields.

> **Why this differs from single-type:** single-type routes through the target CPT's full `Post_Data_Group` (custom fields ARE exposed). Multi-type and `(no target configured)` route through the simpler `Simple_Post_Data_Group`.

### Recipe 14: parent / children traversal

```text
@post(parent.title)                                 → "Avocats — Paris"    (post_parent)
@post(title) — @post(:excerpt)                      → inside a _vx_loop on @post(children), against the looped child
```

Don't write `@post(children.title)` outside a loop — returns first child only and silently. Use a `_vx_loop` wrapper.

### Recipe 15: meta lookup (post / user / term)

```text
@post().meta(_yoast_wpseo_metadesc)
@user().meta(<key>) / @current_user().meta(<key>) / @term().meta(<key>)
```

Empty `<key>` returns `null`. Result is `get_*_meta(..., true)` — single-value semantics.

### Recipe 16: term post count

```text
@term(name) (@term().post_count() posts)              → "Brevets (42 posts)"
@term().post_count(<cpt_key>)                         → scoped to a single CPT
```

Empty arg sums across all CPTs.

### Recipe 17: math-driven derived field

```text
@site().math(@post(rating_total) / @post(rating_count)).round(1)                                     → "4.6"
@site().math((@post(stock) - @post(reserved)) / @post(stock) * 100).round().append(% available)
@site().math(random_int(5, 25)).append(% off this week)         (re-evaluates per render — don't use for real pricing)
```

### Recipe 18: condition-driven copy block

A "limited-time" tag for posts published after a fixed cutoff. The comparison modifiers (`is_greater_than`, `is_less_than`, `is_between`) coerce non-numeric inputs through `strtotime()` automatically — so an ISO date string compares correctly without `@site().math(...)`:

```text
@post(:date).is_greater_than(2026-04-15).then(🔥 New).else()
```

`@site().math(...)` is for numeric arithmetic on numeric inputs. Don't try to subtract two date strings inside `@site().math(...)` — `NXP\\MathExecutor` expects numeric operands and the expression returns `''` silently. To compute "days since published", store the post date as a Unix timestamp in a numeric field, then `@site().math(<unixtime_now> - @post(<unix_date_field>))`.

## §3 — Modifier reference (use-when / don't-use-when)

For canonical signatures and source paths, see [`voxel-tags.md`](../voxel/voxel-tags.md) §Modifiers.

| Modifier | Use when | Don't use when |
|---|---|---|
| `.fallback(text)` | Field can be empty AND your sentence depends on it | The downstream widget already has a placeholder behavior |
| `.append(text)` / `.prepend(text)` | Adding fixed punctuation, units, suffix labels (` km`, `%`, ` per night`) | The text is conditional — use `.then()/.else()` |
| `.capitalize()` | Title-casing a single-word slug for display | Multi-word locales (`ucwords` is naive); already-cased text |
| `.truncate(len)` | Cards / preview rows where text would overflow | Headings (CSS ellipsis cheaper); when SEO needs full text |
| `.replace(search, replace)` | Lightweight string normalisation (`-` → ` `, slug → label) | Anything that needs regex — there's no regex modifier |
| `.round(decimals)` | Final display of a math result | Currency — `.currency_format` rounds per locale rules |
| `.number_format(decimals)` | Counts, ratings, percentages displayed without currency | Currency amounts; non-numeric values |
| `.currency_format(code, in_cents?, force_decimals?)` | All money. Pass `default` to follow platform setting | Non-money numbers |
| `.abbreviate(precision?)` | Large counts (`12.3k` followers) where exact value is noise | Money; small numbers below 1000 (returns the value untouched) |
| `.date_format(fmt)` | Absolute dates: `j F Y`, `Y-m-d`, `M Y` | Relative time — use `.time_diff` |
| `.time_diff(tz?)` | "2 hours ago" / "3 days ago" cards | Future events; structured itineraries — use `.date_format` |
| `.to_age()` | Profile age display | Already-computed ages (it parses, doesn't pass through) |
| `.count()` | Object-list / repeater size for badges or pluralisation guards | Scalar fields (returns 0 silently) |
| `.first()` / `.last()` / `.nth(i)` | Highlighting one item from a collection | When you actually want all of them — use `.list` or `_vx_loop` |
| `.list(sep, last_sep, prefix, suffix)` | Joining repeater values into prose | Looping with structure — use `_vx_loop` on a wrapper |
| `.is_empty()` / `.is_not_empty()` | Two-branch fallback copy (Recipe 3) | Visibility — use `_vx_visibility` instead, the rule engine is cheaper |
| `.is_equal_to(v)` / `.is_not_equal_to(v)` | Exact-match badges | Range checks — use `.is_between` |
| `.is_greater_than(v, mode?)` / `.is_less_than(v, mode?)` | Numeric tier or date sequencing | Compound conditions — chains don't AND |
| `.is_between(start, end)` | Range tier (numeric or date) | Open-ended ranges — pair `.is_greater_than()` with `_vx_visibility` instead |
| `.is_checked()` / `.is_unchecked()` | Switch / checkbox field state | String fields where empty means missing — use `.is_empty` |
| `.contains(needle)` / `.does_not_contain(needle)` | Substring detection (taxonomy term, comma-separated strings) | Exact match — `.is_equal_to` is faster and clearer |
| `.then(content)` / `.else(content)` | Two-branch ternary | Three+ branches — split into multiple fields or use `_vx_visibility` |

## §4 — Anti-patterns

| Wanted | Voxel doesn't have | Use instead |
|---|---|---|
| Inline arithmetic in a tag | `@post(price * 1.2)` (treated as a literal field path → empty) | `@site().math(@post(price) * 1.2)` always |
| Lowercase / uppercase | `.lower` / `.upper` | None native; hand-author casing in the field or register a custom modifier via the `voxel/dynamic-data/modifiers` filter |
| Floor / ceil / abs / range-slice / `if/?:` ternary | named modifiers | Wrap in `@site().math(floor(...))` / `@site().math(if(<expr>, <a>, <b>))` — see [`voxel-tags.md`](../voxel/voxel-tags.md) §Math expressions |
| Regex replace | `.regex_replace()` | None native; use `.replace()` for fixed strings or register a custom modifier |
| Multi-step pipeline with named bindings | No `let x = ...` | Compute in a hidden field via `_vx_visibility` chains, or pre-compute in PHP via a custom `@<group>(<field>)` group |

## §5 — Relation patterns (depth)

Voxel `post-relation` fields connect CPTs. **Two correctness issues** matter: (1) the loop-runtime distinction (see [`voxel-tags.md`](../voxel/voxel-tags.md) §Loops — the most expensive bug class; read it before authoring any loop-bearing recipe), and (2) the single-vs-multi target distinction below.

### Single-vs-multi target

**Step 1.** Always run `wpdev voxel:fields <site> <cpt>` first. Look at the `RELATION TARGET` column.

**Step 2.** Pick the right traversal:

| Relation kind | What you can pull |
|---|---|
| Single-type (`single → <target_cpt>`) | Any field on the target CPT (`.<field>`, `.<image>.id`, `.<repeater>.<sub>.first()`) plus all `Simple_Post_Data_Group` accessors (bare `.title`, `.permalink`, `.excerpt`, `.id`, `.date_created`, ... or colon aliases `.:title`, `.:url`, `.:excerpt`, `.:id`, `.:date`, ...). |
| Multi-type (`multi → <a>, <b>, ...`) | `Simple_Post_Data_Group` accessors ONLY (bare or colon — both safe). Custom fields on target CPTs are unreachable. **Crucial: there is NO `:permalink` alias** — use bare `.permalink` or `.:url`. |
| `(no target configured)` | Schema reports this when a relation field is registered without an explicit target list. **Treat as multi-type** — restrict to `Simple_Post_Data_Group` accessors until you've verified target shape via `wpdev voxel:data <site> --id <example_post>`. Even when the relation resolves to a single CPT in practice, the skill can't prove that statically. |
| Parent (`parent`) | Same as single-type — parent is a stable single-target relation |
| Children (`children`) | Inside a `_vx_loop` — children iterate as `@post(...)` against each child |

**Step 3.** When in doubt, dump and inspect:

```bash
wpdev voxel:data <site> --id <example_post> | grep -A1 "<relation_field_name>"
```

If your expression doesn't match the resolved keys, fix the expression — don't guess.

**Loop-row gotcha (composite-repeater path only):** inside a row whose `_vx_loop` is set to `@post(<relation>)` *AND the row is part of a composite repeater* (e.g., `content_blocks[*]`, `ts_actions[*]`, `tag_rows[*]` on `ef-card`), EF rebinds the post per iteration via `ef_loop_apply_post_context()`. In that path the iterating context is each related post — write `@post(<field>)` (current looped post's fields), NOT `@post(<relation>.<field>)`. See [`widgets.md`](widgets.md) for the long-form caveat. **For widget-level loops** (`_vx_loop` on a whole `ef-card` / `ef-wrapper`; legacy `_voxel_loop` also recognised) the rule is the opposite — Voxel's Looper does not rebind the post, so you must traverse the relation: `@post(<relation>.<field>)`.

## §6 — Math (recipes)

Operators, helpers (`discount`, `random_int`, `if`), full executor surface, and error semantics live in [`voxel-tags.md`](../voxel/voxel-tags.md) §Math expressions. Recipe-shaped chains:

```text
@site().math(@post(rating_total) / @post(rating_count)).round(1).append(/5)         → "4.6/5"
@site().math(@post(old_price) - @post(price)).round(2).currency_format(EUR).prepend(Save )  → "Save €40.00"
@site().math(@post(visits) * 0.05).abbreviate()                                     → "1.2k"
@site().math(if(@post(stock) > 0, @post(stock), 0))                                 → "5"   (or "0" when stock is empty/negative)
```

**Recipe-author rule:** wrap any user-visible math output in `.is_empty().then(<fallback>).else(...)` — silent error returns are an empty string that propagates into adjacent prose.

## §7 — Verification

**Two-stage verification is non-negotiable.** A `voxel:data` value spot-check confirms the resolver returns the right value in isolation; a browser render confirms the same expression resolves correctly **in the loop runtime that will actually serve the page**. Skip the second stage and you ship the §5 loop-runtime bug.

### Stage 1 — `voxel:data` value spot-check

```bash
wpdev voxel:data <site> --id <example_post>
```

Compare:

- Did your expression's group key match a registered group? (See [`voxel-tags.md`](../voxel/voxel-tags.md) §Expression syntax for group registry.)
- Did your field key appear in the output? If not, the field doesn't exist on this CPT.
- For relations, did the resolved sub-tree match what you traversed? Single-type relations show their target's full field tree; multi-type show only core props.
- For math, did the result resolve to a number? Empty render = expression failed silently.
- For `.then()/.else()` chains, walk the chain with the actual value: which `passes()` was the last to set the flag? Does the next `apply()` run?

If the expression doesn't render correctly, check (in this order):

1. **Missing `@tags()..@endtags()` wrapper** — required in EF widget settings (except `vx`-typed envelopes for `_cssid` and image refs).
2. **Wrong group key** — does the prefix exist? (Run `wpdev voxel:fields <site> <cpt>` to confirm.)
3. **Multi-type relation traversal** — did you traverse into a target field on a multi-target relation?
4. **Mistyped field key** — case-sensitive; check the blueprint or the `voxel:fields` output.
5. **Chain order** — did a comparison earlier in the chain leave the flag false, skipping a later `.apply()`?
6. **Inline arithmetic** — `@post(price * 1.2)` is a path, not math. Wrap in `@site().math(...)`.

### Stage 2 — browser render

After `wpdev elementor:import` lands and the cache is purged, navigate to a representative sample of real posts (one is never enough) in a real browser and inspect the rendered DOM. The browser is the ground truth — Stage 1 cannot detect:

- §5 loop-runtime mismatches (3 identical cards instead of 3 different ones, or vice versa).
- Cache-staleness (LiteSpeed serving the old CSS/JSON).
- HTML escaping in heading body slots that don't accept rich content.
- Visibility rules that suppress the widget your `.then()` chain was supposed to feed.

If the browser render disagrees with the `voxel:data` spot-check, **trust the browser** and walk the loop-runtime section in [`voxel-tags.md`](../voxel/voxel-tags.md) §Loops.

### Worked example — single-type relation summary

Given a `<cpt>` with a single-type relation field `<relation>` pointing at a target CPT:

```text
@tags()@post(<relation>.title) — @post(<relation>.:excerpt)@endtags()    → "France — Western Europe..."
```

Because `<relation>` is single-type (`wpdev voxel:fields <site> <cpt_key>` reports `single → <target_cpt>`), traversal into `.title` and `.:excerpt` on the target is safe. Had the relation been multi-type, the traversal would silently first-match and the recipe would need to drop to `.title` / `.permalink` / `.:id` / `.:excerpt` / `.:date` only.
