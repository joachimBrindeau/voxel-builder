# Transactional And Private CPT Recipe

## Variant Deltas

Use this recipe when the CPT carries **time-expiring, buyer-submitted, or workflow-private** content — RFQ boards, lead-capture forms, support tickets, inquiry inboxes, internal task queues. A canonical example is a public RFQ board where buyers post quotation requests and manufacturers respond:

- Blueprint: `plugins/custom/voxel-addon/modules/Templates/blueprints/<key>/post_types.json`
- Sitemap-exclude MU plugin: `plugins/mu/lean-seo-<site>.php`

Run the 7-phase lifecycle below the deltas in this section. The deltas concentrate in **Phase 2 (blueprint shape)**, **Phase 4 (skip schema/sitemap, add exclusion filter instead)**, **Phase 6 (templates use DM button + anonymity gates)**, and **Phase 7 (verify exclusion + DM UI)**. Phases 1, 3, 5 are unchanged.

### When to choose this recipe

Pick transactional if **any** of these apply:

- Posts contain PII or buyer-specific business detail (budgets, contact preferences, project briefs).
- Posts are **time-expiring** — once a deal closes, fulfilled requests have negative SEO value.
- Posts are **workflow items** with an admin-managed lifecycle (`status: open → discussing → fulfilled → closed`).
- The frontend "contact this person" path should be in-platform messaging, not a publicly rendered email.
- Content is buyer-submitted via a `ts-create-post` form and needs moderation (`submissions.status: "pending"`).
- Identity exposure must be optional (anonymity switcher for the submitter).

Otherwise, use the public-content default.

### Phase 2 deltas — blueprint shape

The blueprint differs from public-content in five places. Snippets below are abridged from a transactional blueprint; see the full file for the complete field array.

**1. `settings.messages.enabled: true`** — replaces the "rendered email + author block" pattern with in-platform DMs. The single template renders a "Send message" button that opens the Voxel DM thread between the viewer and the post author.

```json
"messages": {
  "enabled": true
}
```

**2. `settings.submissions.status: "pending"`** — newly submitted posts land in moderation rather than going live. Pair with `update_status: "pending"` so user edits also re-enter moderation.

```json
"submissions": {
  "enabled": true,
  "status": "pending",
  "update_status": "pending",
  "update_slug": true,
  "deletable": true
}
```

**3. Buyer identity — use the native WP `post_author`, NOT a separate `post-relation` field.**

A first-cut design instinct is to add a `buyer` `post-relation → profile` field and "auto-populate it server-side from `post_author` on submit." **Don't.** It's redundant: WP already stores `post_author` automatically on every `wp_insert_post`, and Voxel exposes the author's profile data via the native [`@author(profile.<field>)`](./voxel-tags.md) dynamic-tag traversal — `@author(profile.firstname)`, `@author(display_name)`, `@author(profile.permalink)`, etc. Adding a parallel relation field duplicates the data, requires writing and maintaining a custom save hook, and creates two sources of truth that can drift.

In templates, reach the buyer's profile via:

```
@author(display_name)             → WP user display name (always present)
@author(profile.firstname)        → profile CPT field on the author's profile post
@author(profile.lastname)
@author(profile.permalink)        → profile single URL
@author(profile.organisation.title) → traversal through the profile's organisation relation
```

If admin needs UI to **re-assign** a post's author (e.g. move a quotation between users), the canonical surface is the **voxel-addon `author` field type** registered by `plugins/custom/voxel-addon/modules/CustomFields/CustomFields.php`. Adding `{"type": "author", "key": "author"}` to the blueprint surfaces a Voxel-native author picker in the admin edit screen — but it still writes to `post_author`, not a new postmeta.

> ⚠️ **Anti-pattern (don't do this):**
> ```json
> { "type": "post-relation", "key": "buyer", "post_types": ["profile"], "relation_type": "belongs_to_one", ... }
> ```
> A transactional CPT originally shipped with this field; it was removed once the redundancy was caught during template construction. The `@author(...)` dtag is the SSOT.

**4. Anonymity switcher** — a `switcher` field that templates gate buyer/company display on. When `@post(anonymous)` is truthy, the single and card templates suppress the buyer block and show "Anonymous buyer" instead.

```json
{
  "type": "switcher",
  "key": "anonymous",
  "label": "Post anonymously",
  "description": "Hide your profile/company on the public board. Manufacturers can still message you via the platform.",
  "default": null
}
```

**5. Workflow `status` select, admin-only via `visibility_rules`** — the field exists in the blueprint so admins can move posts through the lifecycle, but the buyer submission form must not render it. Two enforcement options:

- **Native Voxel `visibility_rules`** (preferred, no third-party dependency) — gates the field via Voxel's own rule engine. See [`voxel-field-visibility.md`](./voxel-field-visibility.md).
- **`essential-addons-for-voxel` `ea4v_only_show_field_<type>` whitelist** on the `ts-create-post` widget — narrows the form to a buyer-facing subset of blueprint fields. See Phase 0's plugin-activation gate table.

```json
{
  "type": "select",
  "key": "status",
  "label": "Status",
  "description": "Workflow state. Admin-managed; hide from the buyer submission form.",
  "choices": [
    { "value": "open", "label": "Open" },
    { "value": "discussing", "label": "In discussion" },
    { "value": "fulfilled", "label": "Fulfilled" },
    { "value": "closed", "label": "Closed" }
  ],
  "display_as": "inline"
}
```

A complete transactional blueprint groups buyer-facing fields under their original steps, then adds `ui-admin` after the last core field for workflow/admin-owned fields. Unless the user explicitly supplies different rules, set `ui-admin.visibility_rules` to `[[{"type":"user:role","value":"administrator"}]]`; preserve explicit rules and use `visibility_rules`, not `conditions`.

### Phase 3 deltas — none

Identical to the public-content recipe: parent page + permalink default + `wpdev wp <site> rewrite flush` + URL-resolution test post.

### Phase 4 deltas — skip schema/sitemap-inclusion, add exclusion filter

For transactional CPTs, replace the standard Phase 4 (schema:set + sitemap high-priority + markdown field maps) with the **minimal** version:

1. **Skip `wpdev schema:set`** — no per-post `Article` / `DefinedTerm` JSON-LD. (Optional: the parent **board page** may carry `CollectionPage` schema via a `lean_seo_schema_graph` filter, but this is rarely worth it on a moderation-gated low-volume board.)
2. **Skip `lean_seo_sitemap_high_priority_types`** — the CPT shouldn't be in the sitemap at all, let alone high-priority.
3. **Skip `lean_seo_markdown_field_maps`** — only needed for SEO-discoverable content.
4. **Add a `lean_seo_sitemap_exclude` filter in an MU plugin.** The filter lives in lean-seo core at `plugins/custom/lean-seo/includes/config.php` (`lean_seo_sitemap_exclude()`) and accepts an array of post-type slugs to exclude from the XML sitemap. Site-specific filters belong in `plugins/mu/lean-seo-<site>.php` so they ship with the site rather than the lean-seo plugin.

Copy-paste reference (pattern from `plugins/mu/lean-seo-<site>.php`):

```php
<?php
/**
 * Plugin Name: Lean SEO — <site> Overrides
 * Description: <site>-specific filters for Lean SEO — sitemap exclusions
 *              for transactional CPTs, schema overlays, etc.
 */

defined( 'ABSPATH' ) || exit;

/**
 * Exclude the `<key>` CPT from the XML sitemap.
 *
 * Quotation-request singles are transactional, time-expiring, and contain
 * buyer-submitted content with potential confidentiality / freshness issues —
 * indexing them harms site quality. The parent /<key>/ board page still
 * appears in the sitemap (it's a regular page, not part of this CPT).
 */
add_filter(
    'lean_seo_sitemap_exclude',
    static function ( array $types ): array {
        $types[] = '<key>';
        return array_values( array_unique( $types ) );
    }
);
```

5. **Noindex singles.** Singles should not be indexed by search engines. lean-seo already exposes the `lean_seo_noindex_post_types` filter (`plugins/custom/lean-seo/includes/config.php`, consumed by `modules/crawl/robots.php`) — add the CPT slug to it in the same MU plugin. Its default set also feeds `lean_seo_sitemap_exclude()`, so this one filter covers both robots `noindex` and sitemap exclusion:

```php
add_filter(
    'lean_seo_noindex_post_types',
    static function ( array $types ): array {
        $types[] = '<key>';
        return array_values( array_unique( $types ) );
    }
);
```

**Exit:** No `schema:set` for the CPT. CPT slug appears in `lean_seo_sitemap_exclude()` output. Sitemap regenerated does not include the CPT. Singles emit `noindex`.

### Phase 5 deltas — none

Identical to the public-content recipe: `index_table->recreate()` + post indexing + verify SILM inclusion. Smart Internal Linking inclusion is harmless even for a noindex CPT — it just means internal pages can link to RFQ board posts, which is normal navigation, not SEO surface.

### Phase 6 deltas — templates use DM + anonymity gates

The **single** and **card** templates diverge from the public-content default in two structural ways:

1. **Replace the "contact email + author block" with the Voxel messages button.** Because `settings.messages.enabled: true` is set in the blueprint, Voxel exposes a "Send message" UI element bound to the post author. Use the messages widget / button (rather than rendering `@post.author(email)`) so PII never hits the page source. The DM thread opens between the **viewing user** and the **post author**.
2. **Wrap buyer / company identity blocks in an anonymity gate.** Use `@if(@post(anonymous))` visibility logic to hide buyer name, profile link, and company relation when the post is marked anonymous; render an "Anonymous buyer" placeholder block instead. See [`voxel-tags.md`](./voxel-tags.md) §Visibility for the conditional syntax.
3. **Workflow field gating.** The `status` field (and any other admin-only fields) must be hidden from the buyer-facing submission form. Use Voxel `visibility_rules` per [`voxel-field-visibility.md`](./voxel-field-visibility.md), or apply an `ea4v_only_show_field_<type>` whitelist on the `ts-create-post` widget naming only the buyer-facing fields. The admin edit screen still sees the full field set.

Otherwise the template-build pipeline is identical: `wpdev voxel:cards`, then Elementor build pipeline for single/archive widget JSON.

### Phase 7 deltas — verify exclusion + DM UI

In addition to the standard Phase 7 checks:

1. **Verify the CPT is NOT in the sitemap.** Run a quick eval that calls `lean_seo_get_sitemap_post_types()` and confirms the CPT key is absent:

   ```bash
   wpdev wp <site> "eval 'echo in_array(\"<key>\", lean_seo_get_sitemap_post_types(), true) ? \"PRESENT (bug)\" : \"absent (ok)\";'"
   ```

   Or inspect the rendered sitemap directly: `curl -sL https://<site>/sitemap.xml | grep '<key>'` should return nothing.

2. **Verify `lean_seo_sitemap_exclude` includes the CPT.**

   ```bash
   wpdev wp <site> "eval 'print_r(lean_seo_sitemap_exclude());'"
   ```

   The output array must contain the CPT key.

3. **Verify the "Send message" UI element renders** on a test single. Visit a published test post as a logged-in user other than the author — confirm the DM button is visible and clicking it opens the Voxel messages thread.

4. **Verify singles emit `noindex`.** `curl -sL https://<site>/<key>/<slug>/ | grep -i 'robots'` must show `noindex` (either from the plugin surface chosen in Phase 4 step 5 or the `wp_head` fallback).

5. **Verify the anonymity switcher works end-to-end.** Toggle `anonymous` on the test post, reload the single, confirm buyer identity is suppressed.

**Exit:** All public-content Phase 7 checks pass **plus** sitemap-exclusion is verified, DM UI renders, singles are `noindex`, and the anonymity gate works.
