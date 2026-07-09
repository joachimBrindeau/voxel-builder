# Elementor / Voxel template wrapper transplants

Use when copying a visual section/wrapper from one Voxel Elementor template/page to another.

## Lessons

- Do not trust `wpdev elementor:dump` alone for structural edits: it is useful for search/inventory but can flatten the tree. For actual subtree/sibling relationships, read raw `_elementor_data` and inspect nested `elements`.
- A visual section may span multiple top-level sibling nodes, not just the wrapper whose heading matched the search term. Homepage testimonial blocks can be a heading wrapper plus later sibling wrappers/feeds.
- When transplanting a wrapper, preserve source wrapper display settings (`tag`, `cols`, `bg_color`, `bg_media_enabled`, `bg_media_type`) but adapt data sources (`@post(posts)` vs `@post(testimonials)`, post type, relation field, manual IDs) to target context.
- After changing `_elementor_data`, re-import through `wpdev elementor:import <site> <post_id> <json> --save` so schema gate, migrations, and Elementor CSS regeneration run. Then purge caches.
- Browser/MCP visual verification is mandatory for UI/template work: check target URLs, computed background/tag/classes, rendered text/feed presence, and screenshots where layout matters.
- Empty rendered sections often mean source structure is right but target relation data is empty or feed source mismatched. Verify relation meta/content before assuming CSS/template failure.

## Minimal verification loop

1. `wpdev elementor:lint <site> --post <template_id>`
2. `wpdev elementor:import <site> <template_id> <json> --save`
3. `wpdev rebuild <site> --only purge`
4. Browser-check representative URLs for each target post type.
5. Inspect DOM/computed styles for copied wrapper (`section.ef-wrapper`, background token RGB, feed widget count, expected text).
