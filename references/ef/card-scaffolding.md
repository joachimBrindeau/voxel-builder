# EF Card Scaffolding


For the action footer on `ef-card` (call, email, get_directions, show_post_on_map, etc.) see [`actions.md`](./actions.md). For the tag overlay (pill stack + corner ribbons + `+N` overflow popover) see [`widgets.md`](./widgets.md).

Don't hand-write JSON for the `card` role. The CLI does it correctly:

```bash
wpdev voxel:cards <site>                                   # all CPTs, all four variants (small + medium + large + link)
wpdev voxel:cards <site> --type <cpt_key>                  # one CPT
wpdev voxel:cards <site> --sizes small,medium,large,link   # explicit variant list (this is also the default)
wpdev voxel:cards <site> --sizes link                      # one variant only
wpdev voxel:cards <site> --replace                         # rebuild existing
```

The command supports four variants (size is a scaffold recipe in `cli/src/utils/voxel/card-bindings.ts`, NOT an `ef-card` prop — the widget's own axes are `variant` = color surface and `layout` = vertical/horizontal):

| Variant | Shape | Use case |
|---|---|---|
| `small` | (logo if the CPT has one) + linked h3 title + excerpt body; no media, no byline, no actions | Compact grid items, search results |
| `medium` | `layout: horizontal`; (logo if any) + linked title + excerpt + author byline (name/date/avatar); no cover | Mid-density list rows |
| `large` | `layout: vertical`; featured-image cover (`@post(_thumbnail_id.id)`, cover fit, overlay) + (logo if any) + linked title + excerpt + author byline + a gated `hierarchy-children` pill loop (visibility-gated, renders only on hierarchy CPTs) | Hero feeds, archive top-of-fold |
| `link` | Transparent background; single inline `span` with hashtag icon + linked title + excerpt; nothing else | Related-post lists, hierarchy/breadcrumb references, inline tag-style links |

**Logo rule.** The logo binds to a real logo field only — a field labelled "logo", else a `profile-avatar` field (profile CPTs). If the CPT has neither, the card carries NO logo. The featured image is NEVER used as a logo; it is only the `large` card's cover/media slot. So a CPT like `video` (no logo field) renders logo-less cards, with the featured image appearing solely as the large-card cover.

The byline is the **author** — `@author(display_name)` + `@post(date)` + `@author(avatar)` (avatar is the bare attachment id, no `.id`; `@post(author.*)` resolves EMPTY). Because cards render in same-parent loops, only `hierarchy-children` differs per card, so it is the only hierarchy field bound on a card body — see [`../voxel/voxel-field-inventory.md`](../voxel/voxel-field-inventory.md) §Always-present fields. No variant ships a default `ts_actions` strip; add meaningful actions with [`card-actions.md`](../../workflows/card-actions.md).

The command:
- Creates `{key}-small` / `{key}-medium` / `{key}-large` / `{key}-link` Elementor templates.
- Injects an unwrapped `ef-card` widget with the right envelope per variant.
- Registers as `voxel:post_types[<key>].custom_templates.card[]` with `{Singular} - small / - medium / - large / - link` labels.

If different card content is needed, run `voxel:cards` first to register the templates, then modify the resulting template via this pipeline (Phase 0 to capture, Phase 1-5 to mutate).
