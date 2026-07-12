# EF Card Scaffolding


For the action footer on `ef-card` (call, email, get_directions, show_post_on_map, etc.) see [`actions.md`](./actions.md). For the tag overlay (pill stack + corner ribbons + `+N` overflow popover) see [`widgets.md`](./widgets.md).

Don't hand-write JSON for the `card` role. The CLI does it correctly:

```bash
wpdev voxel:cards <site>                                   # all CPTs, all four variants (small + medium + large + link)
wpdev voxel:cards <site> --type <cpt_key>                  # one CPT
wpdev voxel:cards <site> --sizes small,medium,large,link   # explicit variant list (this is also the default)
wpdev voxel:cards <site> --sizes link                      # one variant only
wpdev voxel:cards <site> --replace                         # rebuild existing
wpdev voxel:cards <site> --type <cpt_key> --audit          # verify posts + Voxel custom_templates.card[] registry
```

The command supports four variants (size is a scaffold recipe in `cli/src/utils/voxel/card-bindings.ts`, NOT an `ef-card` prop — the widget's own axes are `variant` = color surface and `layout` = vertical/horizontal):

| Variant | Shape | Use case |
|---|---|---|
| `small` | Real logo + linked title + `heading`/`span` summary (`@post(hook)` when the CPT has a hook field, else native `@post(excerpt)`); never rich text | Compact grid items, search results |
| `medium` | Horizontal logo + linked title + `heading`/`span` summary (hook-or-excerpt) + author byline; never rich text | Mid-density list rows |
| `large` | Vertical cover + logo + linked title + `heading`/`span` excerpt + author byline + gated hierarchy pills | Hero feeds, archive top-of-fold |
| `link` | One transparent linked `heading`/`span` title with icon; no excerpt or secondary row | Related-post lists, hierarchy/breadcrumb references |

**Logo rule.** The logo binds to a real logo field only — a field labelled "logo", else a `profile-avatar` field (profile CPTs). If the CPT has neither, the card carries NO logo. The featured image is NEVER used as a logo; it is only the `large` card's cover/media slot. So a CPT like `video` (no logo field) renders logo-less cards, with the featured image appearing solely as the large-card cover.

The byline is the **author** — `@author(display_name)` + `@post(date)` + `@author(avatar)` (avatar is the bare attachment id, no `.id`; `@post(author.*)` resolves EMPTY). Because cards render in same-parent loops, only `hierarchy-children` differs per card, so it is the only hierarchy field bound on a card body — see [`../voxel/voxel-field-inventory.md`](../voxel/voxel-field-inventory.md) §Always-present fields. No variant ships a default `ts_actions` strip; add meaningful actions with [`card-actions.md`](../../workflows/card-actions.md).

The command:
- Creates `{key}-small` / `{key}-medium` / `{key}-large` / `{key}-link` Elementor templates.
- Injects an unwrapped `ef-card` widget with the right envelope per variant.
- Registers as `voxel:post_types[<key>].custom_templates.card[]` with `{Singular} - small / - medium / - large / - link` labels.

**Main-card rule.** The command assigns the generated `large` template as the CPT's
base/main `templates.card` value in the same Voxel config write. Voxel's `main` selector
resolves this base assignment; custom-card array order does not define the main card.

**Summary-tag rule.** `@post(excerpt)` is a native Voxel property (`get_excerpt()`) that
resolves on every CPT; `@post(hook)` resolves only when the CPT defines a `hook` field.
Never bind a field-scoped tag on a CPT that lacks that field — it renders empty silently.
Verify each secondary/summary binding against `wpdev voxel:fields` before mutation.

## Clean Replacement Protocol

When the user asks to delete every existing preview card and rebuild cleanly:

1. Run `wpdev voxel:cards <site> --type <key> --audit` and list every extra, duplicate,
   stale, or legacy card registered for that CPT.
2. Also enumerate actual `elementor_library` posts in taxonomy
   `elementor_library_type=card`. The Voxel registry can omit abandoned templates,
   and those orphan posts retain command slugs even after config entries disappear.
   For an all-CPT rebuild, this taxonomy query—not registry IDs—is the deletion set.
3. Export every card's Elementor data and capture its post ID/title before deletion.
4. Permanently delete identified card posts with `wp post delete --force`; trash is not
   enough because retained card slugs make regenerated templates acquire `-2` suffixes.
   Verify the card-taxonomy query returns zero before scaffolding. Preserve single,
   archive, form, and unrelated templates.
5. Run `wpdev voxel:cards <site> --type <key> --sizes small,medium,large,link -y`.
   This creates all four canonical posts and rewrites
   `voxel:post_types[<key>].custom_templates.card[]`, pruning stale registrations.
6. Run `wpdev voxel:templates <site> --type <key>` and prove the base `card` row and
   `custom_card` large row both point to the generated large ID.
7. Run the audit again. Completion requires exactly four `present` rows and zero
   label drift, duplicates, stale entries, or missing slots.
8. Run `wpdev elementor:lint <site> --post <id>` for all four returned IDs and inspect
   each with `wpdev elementor:tree`. A created post without config read-back is not done.

If different card content is needed, run `voxel:cards` first to register the templates, then modify the resulting template via this pipeline (Phase 0 to capture, Phase 1-5 to mutate).
