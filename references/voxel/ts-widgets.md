# `ts-*` Widgets — Voxel theme widget catalogue (settings reference)

The Voxel theme registers ~30 `ts-*` Elementor widgets (full catalogue in [`voxel-platform.md`](voxel-platform.md) §Voxel-native Elementor Widget Catalog). **Their setting shapes cannot be introspected via `wpdev elementor:schema`** — that command targets EF V4 atomic widgets only.

This file documents the data-bearing settings (post-type / behavior / messages / labels) for the most commonly built `ts-*` widgets. It does NOT document the style / icon controls — they are widget-class register-only and never need to be hand-written into JSON; the Elementor editor sets them on save.

---

## Discovery rule (mandatory — [`rules.md`](../core/rules.md) Rule 2 of 8)

Before writing any `ts-*` widget JSON from scratch, get a known-good shape from a real production instance:

```bash
wpdev elementor:dump <site> <ts-widget> --post <real_id> --json
```

Then strip the leading "unknown meta keys" warning and adapt the first array element. Golden fixtures committed under [`examples/`](../../examples) save this round-trip for the most common widgets — currently `ts-post-feed`, `ts-create-post`.

---

## `ts-create-post` — submission / edit form for any CPT

Renders the public submission form for a single Voxel CPT (`ts_post_type`). Drives both:
- **Create mode**: blank form, builds a new post on submit.
- **Edit mode**: pre-fills with an existing post and updates it on submit. Voxel theme native: edit mode is triggered by `?post_id=N` URL parameter where the current user has edit-permission on post N (see `app/widgets/create-post.php:5067`). EA4V extends this with the `ts_load_default_post` setting (see below).

### Voxel theme native settings (always read by core)

These keys are read by `Create_Post::render()` in `themes/voxel/app/widgets/create-post.php`:

| Setting | Type | Required | Source line | Notes |
|---|---|---|---|---|
| `ts_post_type` | string | **yes** | line 5033 | CPT key (e.g. `"<cpt_key>"`). Empty string → widget renders nothing. |
| `ts_submit_label_draft` | string | no | line 5041 | Toast: "Your post has been saved as draft." (placeholder default) |
| `ts_submit_label_submitted_for_review` | string | no | line 5041 | Toast: "Your post has been submitted for review." |
| `ts_submit_label_published` | string | no | line 5041 | Toast: "Your post has been published." |
| `ts_submit_label_changes_submitted_for_review` | string | no | line 5041 | Edit-mode toast: "Your changes have been submitted for review." |
| `ts_submit_label_changes_applied` | string | no | line 5041 | Edit-mode toast: "Your changes have been applied." |
| `_ts_admin_mode` | bool/string | no | line 5038 | Internal flag — bypasses some permission checks. Set by Voxel admin tooling. Do not hand-write. |
| `_ts_admin_mode_nonce` | string | no | line 5050 | Paired with `_ts_admin_mode`. Do not hand-write. |

Plus the many `*_icon` controls (`popup_icon`, `info_icon`, `ts_media_ico`, `next_icon`, `prev_icon`, … 25+ icon picks) — visual only, leave to the editor to set.

**Important — Voxel core does NOT read** `ts_btn_*`, `ts_msg_*`, `ts_load_default_post`, `set_custom_params`, `ts_*_custom_btns`, `schedule_label`, `ts_filter_list__*`, or any `ea4v_*` key. Those are all EA4V extensions (see below). The Voxel-native submit/save toasts use `ts_submit_label_*` only.

### EA4V settings (Essential Addons for Voxel — third-party plugin)

When the EA4V plugin is active, it injects additional controls into the `ts-create-post` widget panel. **None of these keys live in any source under `plugins/custom/` or `themes/voxel/` in this workspace** — they originate in the EA4V plugin (may not be present locally; a site can carry `wp-content/uploads/ea4v-generated/` artifacts from a past install without the plugin code). Document them based on the production dump shape; behavior is inferred from key names and confirmed where possible.

#### Button labels (EA4V — TODO: verify against EA4V source)

| Setting | Type | Empirical purpose |
|---|---|---|
| `ts_btn_previous_step` | string | Previous-step button label in multi-step forms |
| `ts_btn_next_step` | string | Next-step button label |
| `ts_btn_publish` | string | Submit / publish button label |
| `ts_btn_save_changes` | string | Edit-mode submit button label |
| `ts_btn_view_button` | string | Generic "View" button label |
| `ts_btn_view_<post_type>_button` | string | **Dynamically named per CPT** — e.g. `ts_btn_view_profile_button`. Post-submit redirect/view button. |
| `ts_btn_back_to_edit_button` | string | Post-submit "back to editing" link |
| `ts_btn_increase_limit` | string | Submission-limit-exceeded CTA |
| `ts_btn_switch_plan` | string | Submission-limit-exceeded alt CTA |
| `ts_btn_view_plan` | string | Submission-capability-missing CTA |

#### Toast / error messages (EA4V)

| Setting | Type | Empirical purpose |
|---|---|---|
| `ts_msg_publish_success_message` | string | Toast after create-mode publish |
| `ts_msg_save_changes_success_message` | string | Toast after edit-mode save |
| `ts_msg_schedule_success_message` | string | Toast after scheduled-post submission |
| `ts_msg_submission_capability_missing` | string | Shown when user's plan lacks the CPT submission cap |
| `ts_msg_submission_limit_exceeded` | string | Shown when user hit their plan's per-CPT submission cap |

> Note: EA4V's `ts_msg_publish_success_message` is functionally redundant with Voxel native `ts_submit_label_published`. Which one wins at runtime depends on EA4V's render override — TODO: verify in EA4V source.

#### Schedule

| Setting | Type | Purpose |
|---|---|---|
| `schedule_label` | string | Label of the "Schedule posting" toggle row. (TODO: verify whether EA4V also gates an entire scheduled-post feature behind a separate toggle.) |

#### Edit mode (EA4V)

| Setting | Type | Purpose |
|---|---|---|
| `ts_load_default_post` | dynamic-tag expression | When set, the form pre-fills with the post resolved by this tag. The expression is evaluated server-side. **Common pattern:** `@tags()@user(profile_id)@endtags()` — loads the current user's profile post (turns the widget into an "edit my profile" form). Voxel core does NOT honor this key; the equivalent native flow is the `?post_id=N` URL param. |
| `ea4v_show_create_post_form_if_user_can_not_edit_default_post` | string (`"yes"` / `""`) | When the `ts_load_default_post` resolves to a post the user can't edit, this flag decides whether to fall back to create-mode (`"yes"`) or hide the form (`""`). |

#### Custom buttons (EA4V)

| Setting | Type | Purpose |
|---|---|---|
| `ts_created_custom_btns` | repeater (array) | Extra buttons rendered after successful create. Each row likely has `{ label, url, icon, style }` — TODO: verify shape against EA4V source. |
| `ts_changed_custom_btns` | repeater (array) | Extra buttons after successful edit-save. |
| `ts_can_not_create_custom_btns` | repeater (array) | Extra buttons shown in the submission-capability-missing state. |

In the live dump all three are `[]` (empty repeaters); refresh the fixture from an instance that actually uses them when you need the row shape.

#### URL params (EA4V)

| Setting | Type | Purpose |
|---|---|---|
| `set_custom_params` | repeater (array) | URL query-string params auto-applied to the form's initial field values. Each row likely `{ param, field_key }` — TODO: verify shape. |

#### Field visibility (EA4V) — dynamically named per CPT

EA4V scans every Voxel-managed CPT registered on the site and adds **two** settings per CPT:

| Setting pattern | Type | Purpose |
|---|---|---|
| `ea4v_only_show_field_<post_type_key>` | array of field keys | **Whitelist** — when non-empty, ONLY the listed fields render in the form. Empty array = show all. Active only when `ts_post_type` matches `<post_type_key>`. |
| `ts_filter_list__<post_type_key>` | array of field keys | TODO: verify behavior. Likely the complementary blacklist OR a step-level filter. Both arrays are typically empty in dumped instances. |

**Sizing**: EA4V generates this pair for every Voxel-managed CPT registered on the site, so the dynamic setting count is `2 × (number of CPTs)`. When you write JSON, include the pair for `<your_post_type>` at minimum; including empty pairs for the other CPTs is harmless but optional.

#### Misc EA4V

| Setting | Type | Purpose |
|---|---|---|
| `ea4v_bypass_required_fields` | string (`"yes"` / `""`) | When `"yes"`, skips required-field validation client-side. Useful for staged / multi-step submission flows where users save partial drafts. |

### Total setting count (confirmed against create-post.php + dump)

- **Voxel-native data settings**: 8 (1 required: `ts_post_type`; 5 submit labels; 2 internal admin-mode).
- **Voxel-native icon/style controls**: ~140 (every `ts_*_icon`, `ts_*_col`, `ts_*_typo`, `ts_*_radius`, `ts_*_spacing`, `ts_*_bg`, etc. registered in `create-post.php`). Editor-managed — never hand-write.
- **EA4V data settings (static)**: 22 (11 button labels + 5 messages + `schedule_label` + 2 edit-mode + 3 custom-button repeaters + 1 URL-params repeater).
- **EA4V data settings (dynamic, per CPT)**: 2 × (number of CPTs registered).

---

### Worked example 1 — submission form scoped to a subset of CPT fields

For a public submission form at post `<post_id>` (a new submission flow, NOT edit-mode). Suppose the target CPT blueprint at `plugins/custom/voxel-addon/modules/Templates/blueprints/<cpt_key>/post_types.json` defines a set of data fields plus a few `ui-step` markers, and that two of those fields are auto-populated or admin-only (e.g. an owner field auto-populated from the user's profile, and a workflow `status` field). The user-visible fields = everything except those.

**User-visible field keys** (from blueprint `fields[]`):

1. `step-one` (ui-step)
2. `title`
3. `<field-a>`
4. `<field-b>`
5. `description`
6. `<field-c>`
7. `<field-d>`
8. `<relation-field-a>`
9. `<field-e>`
10. `<relation-field-b>`
11. `step-two` (ui-step)
12. `<field-f>`

Excluded: `step-workflow` (ui-step), `<owner-field>`, `status`.

**Widget JSON** — adapt the fixture at `../../examples/ts-create-post.json`, drop the EA4V settings that don't apply (when no EA4V plugin is active on the target site, the EA4V keys are inert orphans; keeping them does no harm and survives EA4V being reinstalled later). The minimal correct widget for Voxel-core-only behavior:

```json
{
  "id": "rfq001",
  "elType": "widget",
  "widgetType": "ts-create-post",
  "settings": {
    "ts_post_type": "<cpt_key>",
    "ts_submit_label_published": "Your submission has been received and is awaiting review.",
    "ts_submit_label_submitted_for_review": "Your submission has been received and is awaiting review.",
    "ts_submit_label_changes_applied": "Your submission has been updated."
  }
}
```

If EA4V is installed and you want the whitelist + button labels honored, expand to:

```json
{
  "id": "rfq001",
  "elType": "widget",
  "widgetType": "ts-create-post",
  "settings": {
    "ts_post_type": "<cpt_key>",
    "ts_submit_label_published": "Your submission has been received and is awaiting review.",
    "ts_btn_previous_step": "Previous",
    "ts_btn_next_step": "Continue",
    "ts_btn_publish": "Submit",
    "ts_btn_save_changes": "Save changes",
    "ts_btn_view_button": "View",
    "ts_btn_view_<cpt_key>_button": "View your submission",
    "ts_btn_back_to_edit_button": "Back to editing",
    "ts_msg_publish_success_message": "Your submission has been received and is awaiting review.",
    "ts_msg_save_changes_success_message": "Your changes have been applied.",
    "ea4v_only_show_field_<cpt_key>": [
      "step-one",
      "title",
      "<field-a>",
      "<field-b>",
      "description",
      "<field-c>",
      "<field-d>",
      "<relation-field-a>",
      "<field-e>",
      "<relation-field-b>",
      "step-two",
      "<field-f>"
    ],
    "ea4v_bypass_required_fields": ""
  }
}
```

The `ea4v_only_show_field_<cpt_key>` whitelist enumerates the user-visible field keys (the data fields + ui-steps); the owner field, `status`, and `step-workflow` are excluded so they never render in the user-facing UI even though they exist in the CPT blueprint. Source: the CPT's blueprint at `plugins/custom/voxel-addon/modules/Templates/blueprints/<cpt_key>/post_types.json`.

> Cross-check before deploying: confirm whether EA4V is actually active on the target site. When it is NOT (`wp-content/plugins/` contains no `essential-addons-for-voxel` directory), the EA4V keys in any existing dump are orphaned. The `ea4v_only_show_field_<cpt_key>` whitelist will have no effect; the form will show all CPT entries including the owner field + `status` unless those fields are gated via the CPT's own visibility-rules (set in Voxel admin → CPT → Fields → per-field visibility-conditions, NOT in this widget).

### Worked example 2 — edit-mode profile form (post `<post_id>`)

The dumped fixture (`../../examples/ts-create-post.json`) is the live "Edit profile" form. The key that turns it into an edit form is:

```json
"ts_load_default_post": "@tags()@user(profile_id)@endtags()"
```

EA4V evaluates the dynamic-tag expression server-side. `@user(profile_id)` resolves to the current user's profile-post ID. The widget then pre-fills with that post and submits as an UPDATE rather than CREATE. The post-submit success message uses `ts_msg_save_changes_success_message` ("Your changes have been applied.") instead of `ts_msg_publish_success_message`.

**Equivalent Voxel-core-only flow** (no EA4V): host the same widget on a page where `?post_id=<id>` is appended to the URL, OR rely on Voxel's automatic profile-binding (the `Create_Post::render()` method auto-loads `\Voxel\User::get_or_create_profile()` when `ts_post_type === 'profile'` — see line 5063 of `create-post.php`). So for the specific case of "edit my profile", Voxel core actually already handles it without `ts_load_default_post`; the EA4V key is what generalizes the pattern to any CPT (e.g. "edit my company", "edit my single listing").

---

## ts-post-feed — source modes + relation-feed recipe

Source: `themes/voxel/app/widgets/post-feed.php`. Golden fixture: [`../../examples/ts-post-feed.json`](../../examples/ts-post-feed.json). Bind to the fixture and adapt; the prop shapes below are verified against `post-feed.php` `register_controls()`.

**`ts_source` enum — the ONLY four modes (verified `post-feed.php`):**

| `ts_source` | Drives the feed from | Key props |
|---|---|---|
| `search-filters` | a CPT query with inline filter rows (the workhorse — use for relation surfaces, related-CPT feeds, status-filtered feeds) | `ts_choose_post_type`, `ts_card_template__<cpt>`, `ts_filter_list__<cpt>`, `ts_post_exclude`, `ts_post_number` |
| `search-form` | a connected `ts-search-form` widget's results | `ts_search_form_id` |
| `manual` | a hand-picked static list of post IDs | `ts_manual_post_type`, `ts_manual_posts[].post_id` |
| `archive` | the current archive/loop context | `ts_manual_post_type` |

> **`archive` mode requires the taxonomy/CPT to opt into the native query.** The mode reads `$wp_query->posts`, but `Search_Controller::maybe_disable_native_archive_query()` forces `post__in => [0]` on every Voxel-managed term archive and post-type archive unless the owner sets `default_archive_query = enabled` — taxonomy: `voxel:taxonomies` → `<key>.settings.default_archive_query`; CPT: `options.default_archive_query`. Left at the `disabled` default, the page still renders headings and a correct `@term().post_count()`, and only the grid silently falls back to its empty state — so verify a rendered card, never just the count. Flip it with `\Voxel\set( 'taxonomies.<key>.settings.default_archive_query', 'enabled' )`.

> **There is NO `ts_source: "relation"` mode.** A post-relation surface ("the services this request links to", "other companies in this region") is built with **`search-filters` + a relation filter row**, NOT a relation source. The plan-planning `relation-feed` / `related-cpt-feed` archetypes resolve to this recipe.

**Relation-feed recipe (surface `@post(<relation>)` as cards):**

```jsonc
{
  "ts_source": "search-filters",
  "ts_choose_post_type": "<target-cpt-key>",          // the relation's TARGET cpt (e.g. "services")
  "ts_card_template__<target-cpt-key>": "<card-post-id>",  // a live card template (verify via wpdev voxel:templates)
  "ts_filter_list__<target-cpt-key>": [
    { "ts_choose_filter": "rel-<field>",               // the registered relation filter key on the TARGET cpt
      "rel-<field>:value": "@tags()@post(id)@endtags()" } // bind to the host post id
  ],
  "ts_post_number": "12",
  "ts_feed_column_no": 3
}
```

**Prerequisite (the silent-empty trap):** the `rel-<field>` filter MUST be registered in the **target CPT's search filters** (Voxel admin → CPT → Search & Filters → Relations filter). If it isn't, the filter row is inert and the feed returns the whole CPT (or nothing). After registering one, run `wpdev rebuild <site> --only reindex --recreate` (the index table's column set changes). Confirm registered filters with `wpdev wp <site> eval '$f=\Voxel\Post_Type::get("<cpt>")->get_filters(); echo implode(", ",array_keys($f));'`.

**Self-exclusion (exclude the current post from its own "related" feed):** `ts_post_exclude: "@tags()@post(:id)@endtags()"` (verified prop, `post-feed.php`). There is no "exclude current" filter type — use `ts_post_exclude`.

**Fallback when no `rel-` filter is registered (and you can't add one):** render the relation as a linked inline list inside an `ef-card` (`@post(<relation>.title).list( • )`), or a `kind: heading`/`kind: tag` row loop — not a feed. This is the path to take when the relation is a scope-limiter facet rather than a primary content surface.

> **Node-level `ef-wrapper mode:template + _vx_loop` over a relation** (the alternative "clone a card template per related post" pattern seen in some peer templates) depends on voxel-addon ≥ the per-item `@post`-context-rebind fix (commit `2e2e1a2`); on older addon builds the clones silently render the PARENT post N×. Prefer the `search-filters` feed recipe above unless that addon fix is present. See the [voxel-builder issue tracker] note on template-loop rebind.

## Other `ts-*` widgets in this reference

Add new sections here as `ts-*` widgets are reverse-engineered through dump + source inspection. Candidates to document next based on production usage:

- `ts-search-form` — heavily configurable via [`voxel-search.md`](voxel-search.md); settings catalogue would belong here.
- `ts-search-form` — heavily configurable via [`voxel-search.md`](voxel-search.md); settings catalogue would belong here.
- `ts-template-tabs` — small but widely used.

For each future addition, follow the same recipe: dump → walk widget class `register_controls()` + `render()` → group settings by purpose → mark anything not directly read by the widget class as TODO/verify.
