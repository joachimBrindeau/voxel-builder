# Voxel Field Visibility Rules

Voxel exposes a native, field-level visibility system that gates an individual blueprint field's render and submission based on the current user, the current post, the current template, or arbitrary dynamic-tag expressions. **No extra plugin is required.** This is the Voxel-native equivalent of (and the right replacement for) the Essential Addons for Voxel `ea4v_only_show_field_<type>` whitelist when EA4V is not installed.

The system has **30 built-in rule types** registered in `themes/voxel/app/dynamic-data/config.php`. They are evaluated by `\Voxel\evaluate_visibility_rules()` (`themes/voxel/app/utils/utils.php`) and applied per-field by `Base_Post_Field::passes_visibility_rules()` (`themes/voxel/app/post-types/fields/base-post-field.php`).

## Mechanism overview

Each blueprint field inherits these visibility-related props from `Base_Post_Field::base_props()` (`base-post-field.php:64–80`):

| Prop | Default | Role |
|---|---|---|
| `enable-conditions` | `false` | Master toggle for the **value-based** `conditions` array (field A depends on field B's value). |
| `conditions_behavior` | `"show"` | `show` or `hide` based on whether `conditions` match. |
| `conditions` | `[]` | Value-conditional rules — `[[ {field, op, value}, … ], …]`. **AND within a group, OR between groups.** |
| `visibility_behavior` | `"show"` | `show` or `hide` based on whether `visibility_rules` match. |
| `visibility_rules` | `[]` | Identity/context rules (user / author / post / template / product / dtag). Same `[[ rule, rule, … ], …]` group shape as `conditions`. |
| `overrides_enabled` | `false` | Master toggle for the `overrides` array (per-rule overrides of inner field props like `maxlength`). |
| `overrides` | `[]` | List of `{visibility_rule, model_overrides}` blocks. |

### Two separate systems, do not confuse

- **`conditions` / `conditions_behavior` / `enable-conditions`** — value-based; gates a field on another field's value (e.g. "show `vendor_url` only when `is_vendor` is checked"). Lives entirely in the form builder.
- **`visibility_rules` / `visibility_behavior`** — identity/context-based; gates a field on the viewer, the author, or the rendering context using the 30 rule types catalogued below. This is the one you want for "admin only", "logged-in only", "specific role only".

Both arrays use the same **two-dimensional group shape**: outer array = OR between groups, inner array = AND within a group. A group with zero rules is treated as no-match (empty groups are skipped). The function returns `true` as soon as one group passes all its rules. The field's `visibility_behavior` then decides whether `true` means show or hide.

### A single rule's JSON shape

A rule object is flat: a `type` key (the rule-type string from the catalogue below) plus whatever args that rule defines via `define_args()`. Args are unpacked by `evaluate_visibility_rules()`:

```php
$rule = new $rule_list[ $rule_config['type'] ];
unset( $rule_config['type'] );
$rule->set_args( $rule_config );
```

So a single rule literally looks like `{"type": "user:role", "value": "administrator"}`.

## Legacy V3 vs current EF V4 envelope — two distinct shapes

Visibility data lives in two different envelopes depending on context. Do not confuse them; the [`migrate.md`](../../workflows/migrate.md) pipeline converts one to the other.

| Context | Meta key / prop | Shape | Where used |
|---|---|---|---|
| **Voxel CPT blueprint field** (current) | `visibility_rules` + `visibility_behavior` | `[[ {type, ...args}, ... ], ...]` + `"show"\|"hide"` — the flat group shape documented above | Field-level gating in `Base_Post_Field::passes_visibility_rules()` — admin form, `ts-create-post`, server-side render |
| **Legacy Elementor V3 widget** | `_voxel_visibility_rules` + `_voxel_visibility_behavior` | Same `[[ {type, ...args}, ... ], ...]` group shape, on the widget settings object | Pre-EF-V4 Voxel pages — `heading`, `text-editor`, `container`, etc. carried these directly. Migration target, not authoring target. |
| **Current EF V4 atomic widget / repeater row** | `_vx_visibility` (single prop, atomic envelope) | `{"$$type": "vx-visibility", "value": {"behavior": "show"\|"hide", "rules": [[ {type, ...args}, ... ], ...]}}` | EF V4 atomic widgets and their repeater rows (e.g. `ef-card` heading rows, `ef-navbar` action rows). The rules array inside `value.rules` uses the same 30 types catalogued here. |

When authoring EF V4 widgets, **always copy the `_vx_visibility` envelope verbatim from a golden node on the same page** (Rule 1) — do not synthesize the `$$type` scaffolding from memory. The rule contents (the catalogue below) are stable across all three envelopes; only the surrounding envelope differs.

## Rule-type catalogue (30)

Source registry: `themes/voxel/app/dynamic-data/config.php`. Each rule lives at `themes/voxel/app/dynamic-data/visibility-rules/<file>.php`.

### User (current viewer)

These check the **currently logged-in user**.

| Type string | Args | Description | Source |
|---|---|---|---|
| `user:logged_in` | — | Viewer is logged in. | `user-is-logged-in.php` |
| `user:logged_out` | — | Viewer is NOT logged in. | `user-is-logged-out.php` |
| `user:role` | `{value: "<role_key>"}` | Viewer has the given WP role (`administrator`, `editor`, `subscriber`, custom roles…). Choices come from `wp_roles()`. | `user-role-is.php` |
| `user:plan` | `{value: "<plan_key>"}` | Viewer's active Voxel membership plan equals `value`. `default` matches users with no active paid plan. | `user-plan-is.php` |
| `user:is_author` | — | Viewer is the author of the **currently rendered post**. | `user-is-author.php` |
| `user:can_create_post` | `{value: "<post_type_key>"}` | Viewer can create a new post of that CPT (capability check). | `user-can-create-post.php` |
| `user:can_edit_post` | — | Viewer can edit the **currently rendered post**. | `user-can-edit-post.php` |
| `user:is_verified` | — | Viewer's account is verified (`is_verified()`). | `user-is-verified.php` |
| `user:is_vendor` | — | Viewer is an active Stripe Connect vendor. | `user-is-vendor.php` |
| `user:has_bought_product` | `{product_id: "<id>"}` (optional — falls back to current post) | Viewer has purchased the given product. | `user-has-bought-product.php` |
| `user:has_bought_product_type` | `{product_type: "<product_type_key>"}` | Viewer has purchased any product of that product type. | `user-has-bought-product-type.php` |
| `user:is_customer_of_author` | `{author_id: "<id>"}` (optional — falls back to current post's author) | Viewer has bought something from this vendor (or from the platform when the vendor is an admin and admin-onboarding is off). | `user-is-customer-of-author.php` |
| `user:follows_post` | `{post_id: "<id>"}` (optional — falls back to current post) | Viewer follows the given post. | `user-follows-post.php` |
| `user:follows_author` | `{author_id: "<id>"}` (optional — falls back to current post's author) | Viewer follows the given user. | `user-follows-author.php` |

### Author (current post's author)

These check the **author of the currently rendered post**, not the viewer.

| Type string | Args | Description | Source |
|---|---|---|---|
| `author:role` | `{value: "<role_key>"}` | Current post's author has that role. | `author-role-is.php` |
| `author:plan` | `{value: "<plan_key>"}` | Current post's author has that membership plan. | `author-plan-is.php` |
| `author:is_verified` | — | Current post's author is verified. | `author-is-verified.php` |
| `author:is_vendor` | — | Current post's author is an active Stripe Connect vendor. | `author-is-vendor.php` |

### Post (current post)

| Type string | Args | Description | Source |
|---|---|---|---|
| `post:is_verified` | — | Currently rendered post is verified. | `post-is-verified.php` |

### Product (current post's product field)

These assume the current post has a field of type `product`.

| Type string | Args | Description | Source |
|---|---|---|---|
| `product:is_available` | — | Current post's `product` field reports available stock. | `product-is-available.php` |
| `product_type:is` | `{value: "<product_type_key>"}` | Current post's `product` field has the given Voxel product type. | `product-type-is.php` |

### Template (current render context)

These match against `\Voxel\get_visibility_context_template()` (Elementor template context) or, when that returns null, the WP query conditionals (`is_front_page()`, `is_page()`, `is_singular()`, etc.). Useful for fields that should only appear in some templates.

| Type string | Args | Description | Source |
|---|---|---|---|
| `template:is_homepage` | — | Rendering the front page. | `template-is-homepage.php` |
| `template:is_404` | — | Rendering a 404. | `template-is-404.php` |
| `template:is_page` | `{page_id: "<post_id>"}` | Rendering a specific page. | `template-is-page.php` |
| `template:is_child_of_page` | `{page_id: "<post_id>"}` | Current page is a descendant of that parent page. | `template-is-child-of-page.php` |
| `template:is_single_post` | `{post_type: "<key>"\|":custom", post_id?: "<id-or-slug>"}` | Rendering a single post of a CPT, or `":custom"` + a specific post id/slug. | `template-is-single-post.php` |
| `template:is_post_type_archive` | `{post_type: "<key>"}` | Rendering a CPT archive (use `post` to match the blog index `is_home()`). | `template-is-post-type-archive.php` |
| `template:is_single_term` | `{taxonomy: "<key>", term_id?: "<id-or-slug>"}` | Rendering a taxonomy term archive. Empty `term_id` matches any term in that taxonomy. | `template-is-single-term.php` |
| `template:is_author` | `{author_id?: "<id-or-nicename>"}` | Rendering an author archive (any author, or a specific id/nicename). | `template-is-author.php` |

### Dynamic-tag

| Type string | Args | Description | Source |
|---|---|---|---|
| `dtag` | `{tag: "<dynamic-tag-expression>", compare: "<control-structure-modifier>", arguments: [<arg>, ...]}` | Evaluates an arbitrary `@site().then(<tag>).<modifier>(<args>).then(yes).else(no)` expression and matches when the result is `yes`. **Escape hatch** when no built-in rule fits. | `dtag-rule.php` |

### Choosing the right comparator for dtag visibility rules

When a `dtag` rule tests a Voxel field value (e.g. `@post(canal_type) is_equal_to "phone"`), the `compare` modifier MUST match the field's storage type. Taxonomy, `post-relation`, and `multiselect` fields store **arrays** — `is_equal_to` silently evaluates `false` against `["phone"]`; use `contains` instead. Scalar fields (`text`, `select`, `switcher`, …) use `is_equal_to`. This type→comparator mismatch is the root of the "fragile vis-gate on structured fields" fix class — don't guess from the field-type name; resolve it from the live field registry:

```bash
wpdev voxel:comparator <site> canal_type          # taxonomy      → contains
wpdev voxel:comparator <site> canals.canal_type   # repeater sub-field (taxonomy) → contains
wpdev voxel:comparator <site> status              # select        → is_equal_to
```

`<field>` accepts a `.<subkey>` for repeater sub-fields; `--cpt <key>` scopes the lookup (defaults to first-hit across all CPTs). Verify the resolved modifier against a real post with `\Voxel\render(...)` before writing the rule.

## Worked examples

### Example 1 — Admin-only field (a moderation `<field>` on a user-submitted `<cpt>`)

Hide the `status` field from buyer-facing `ts-create-post` submissions; show it only when an administrator is rendering or editing the form.

```json
{
  "type": "select",
  "key": "status",
  "label": "Statut",
  "choices": {"open": "Ouverte", "discussing": "En discussion", "fulfilled": "Satisfaite", "closed": "Fermée"},
  "default": "open",
  "required": false,
  "visibility_behavior": "show",
  "visibility_rules": [
    [ {"type": "user:role", "value": "administrator"} ]
  ]
}
```

`visibility_behavior: "show"` + a single group with one `user:role` rule means: "this field appears **only when** the viewer is an administrator". Front-end submitters will neither see nor be able to set the field — it will fall back to its `default` value (`open`) on save.

To pair the same gate with a relation field that should be auto-populated rather than user-chosen, use the same block:

```json
{
  "type": "post-relation",
  "key": "buyer",
  "label": "Acheteur",
  "post_types": ["profile"],
  "multiple": false,
  "required": false,
  "visibility_behavior": "show",
  "visibility_rules": [
    [ {"type": "user:role", "value": "administrator"} ]
  ]
}
```

Auto-population on the front-end side then happens through `default: "@current_user.profile_id"` (or whatever your authoring flow uses), since the field is server-side-hidden, not client-side-removed.

### Example 2 — Logged-in-only field (gate a contact email)

Hide a `contact_email` field's render entirely from logged-out visitors, even on a public single-post template:

```json
{
  "type": "email",
  "key": "contact_email",
  "label": "Email de contact",
  "visibility_behavior": "show",
  "visibility_rules": [
    [ {"type": "user:logged_in"} ]
  ]
}
```

Inverted form — show ONLY to logged-out visitors (e.g. a "register to unlock" notice field):

```json
{
  "visibility_behavior": "show",
  "visibility_rules": [
    [ {"type": "user:logged_out"} ]
  ]
}
```

Or, equivalently, use `visibility_behavior: "hide"` with `user:logged_in`.

### Example 3 — Combining rules with AND / OR

Voxel's group semantics, from `evaluate_visibility_rules()`:

- **Inner array = AND.** Every rule in a group must pass.
- **Outer array = OR.** The overall result passes when at least one group passes.
- An **empty inner group** (no rules) is skipped, not auto-passed.

#### AND — admins who are also vendors

```json
"visibility_rules": [
  [
    {"type": "user:role", "value": "administrator"},
    {"type": "user:is_vendor"}
  ]
]
```

#### OR — admins OR the post's own author

```json
"visibility_rules": [
  [ {"type": "user:role", "value": "administrator"} ],
  [ {"type": "user:is_author"} ]
]
```

This is the canonical pattern for "admin-or-author can edit this field" — exactly what you want for moderation fields on user-submitted CPTs.

#### AND + OR — (admin AND verified) OR (the post's author)

```json
"visibility_rules": [
  [
    {"type": "user:role", "value": "administrator"},
    {"type": "user:is_verified"}
  ],
  [ {"type": "user:is_author"} ]
]
```

### Example 4 — Same rule, EF V4 atomic envelope (widget / repeater row)

The same admin-only gate from Example 1, applied to an `ef-card` action row (or `ef-navbar` action row, or any EF V4 atomic widget that accepts `_vx_visibility`):

```json
{
  "_vx_visibility": {
    "$$type": "vx-visibility",
    "value": {
      "behavior": "show",
      "rules": [
        [ {"type": "user:role", "value": "administrator"} ]
      ]
    }
  }
}
```

The 2-D group shape inside `value.rules` is byte-for-byte the field-level `visibility_rules` array. Only the envelope (`$$type` + `value: {behavior, rules}`) differs. **Always copy this envelope verbatim from a golden node on the same page** — see Rule 1 in [`rules.md`](../core/rules.md). [`migrate.md`](../../workflows/migrate.md) covers the legacy `_voxel_visibility_rules` → `_vx_visibility` conversion when migrating V3 pages.

## Voxel-native rules vs Essential Addons for Voxel whitelist

Both mechanisms gate field rendering, but they belong on opposite ends of the configuration surface.

| | **Voxel-native `visibility_rules`** | **EA4V `ea4v_only_show_field_<type>` whitelist** |
|---|---|---|
| Plugin requirement | None (ships with Voxel). | Requires Essential Addons for Voxel active. |
| Where the config lives | Inside the **blueprint field** (portable across sites, version-controlled with the CPT). | Inside the **`ts-create-post` widget settings** on a specific Elementor template. |
| Granularity | Per-field, evaluated server-side via `passes_visibility_rules()`. | Whole-field whitelist per widget instance. |
| Reusable across forms | Yes — defined once on the field, applies to every widget that renders it (admin, `ts-create-post`, single-post templates, …). | No — must be re-configured per `ts-create-post` instance. |
| Expression power | 30 rule types + AND/OR groups + `dtag` escape hatch. | Static whitelist of field keys. |
| Right tool for | "This field should only ever be visible/editable by admins / verified users / a specific role / under a specific template." Blueprint-portable, EA4V-free. | "On THIS particular submission form, only show these N fields, ignore the rest." Form-scoped trimming. |

**Default for any `<site>` without EA4V:** use `visibility_rules`. It is the only Voxel-native way to gate a field, it survives blueprint re-imports, and it works everywhere the field is rendered (not just the one widget you configured EA4V on).

## Source citations

All paths relative to `wp-content/themes/voxel/`.

- Registry of all 30 rule types: `app/dynamic-data/config.php`.
- Evaluator (group AND/OR semantics): `app/utils/utils.php` (`evaluate_visibility_rules`).
- Field-level integration (props + `passes_visibility_rules`): `app/post-types/fields/base-post-field.php`.
- Base rule class (`define_arg`, `evaluate`, `get_type`): `app/dynamic-data/visibility-rules/base-visibility-rule.php`.
- Canonical rule pattern: `app/dynamic-data/visibility-rules/user-role-is.php`.
- Per-rule sources: `app/dynamic-data/visibility-rules/<rule>.php` — one file per row of the catalogue above.
- EF V4 `_vx_visibility` envelope: copy verbatim from a golden node on the same page; see [`migrate.md`](../../workflows/migrate.md) for legacy V3 → V4 conversion.
