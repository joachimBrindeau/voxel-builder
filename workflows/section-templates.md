# Section Template Extraction And Sanitization

Turn one live EF section into a reusable `template.json` + `meta.yml` store entry. The
template is a starting tree; current schema SSOT always wins when reused.

## Entry Criteria

1. Site, page path, target section role/selector, intended template id/scope, and source
   owner are known.
2. Read `templates/README.md`, `references/templates/placeholder-policy.md`, and
   `references/ef/template-transplants.md`.
3. `wpdev`, `jq`, and the template lint dependencies are available.

## Phase 0 - Resolve Source Post

**Entry:** Entry criteria are met.

1. Resolve the page path with `wpdev voxel:page <site> --path <path>`.
2. If the content record has no own Elementor data, resolve and use its assigned template
   post id through the template-resolution reference.
3. Record site, content id, source post/template id, URL, and role.

**Exit:** One source post id that owns the rendered section is proven.

## Phase 1 - Export Raw Tree

**Entry:** Phase 0 source id is known.

1. Run `wpdev elementor:export <site> <source_post_id>`.
2. Locate the exact auto-named export path reported by the command; do not guess by newest
   unrelated backup.
3. Verify the export is a non-empty bare JSON array and record its hash.

**Exit:** Immutable raw export path/hash exist and parse as a page tree.

## Phase 2 - Select Self-Contained Subtree

**Entry:** Phase 1 raw nested export parses.

1. Inspect raw nested `elements`, never a flattened dump.
2. Select the target top-level node by stable id/role/css id and record the exact selector.
3. Extract one self-contained subtree with descendants. If the visual section spans siblings,
   wrap those siblings in one EF wrapper before proceeding.

**Exit:** `subtree.json` has one root, contains all dependencies inside the subtree, and
records source node id/selector.

## Phase 3 - Regenerate Node Ids

**Entry:** Phase 2 subtree is self-contained.

1. Traverse every node recursively and assign a fresh valid Elementor id.
2. Preserve references only when they intentionally point outside the subtree and are
   declared in metadata; otherwise rewrite internal id references.
3. Prove old/new id sets are disjoint and new ids are unique.

**Exit:** Every node has one unique regenerated id and no stale internal id remains.

## Phase 4 - Sanitize Content And Assets

**Entry:** Phase 3 id proof passes.

1. Apply the placeholder policy's key-driven display/routing/structural classification.
2. Sanitize enveloped strings, bare loop/dtag strings, and `vx` envelope strings.
3. Keep only allowlisted universal dtags; replace display copy with neutral placeholders,
   blank routing/PII values, and preserve structural enums.
4. Replace real non-featured attachment ids/URLs with neutral placeholders.
5. Scan the whole JSON once for the combined denylist and non-allowlisted dtag patterns.

**Exit:** The subtree contains only structural/style values, allowlisted dtags, and neutral
placeholder content/assets; combined scans return zero violations.

## Phase 5 - Normalize Structure

**Entry:** Phase 4 sanitization passes.

1. Run `wpdev elementor:normalize <subtree.json> <template.json>`.
2. Review the diff for base-prop/responsive/null healing only.
3. Do not treat normalize as schema validation.

**Exit:** `template.json` parses and structural normalization introduced no content leak.

## Phase 6 - Author Metadata

**Entry:** Phase 5 `template.json` is stable.

1. Create the folder and `meta.yml` using the exact schema in `templates/README.md`.
2. Set `id` equal to the folder name; derive widgets and `dtags_used` from JSON.
3. Record source post/node/selector/hash in `source_note`; include `location` only for global
   scope.

**Exit:** Metadata parses, ids agree, and widget/dtag sets equal the actual template.

## Phase 7 - Register Index Entry

**Entry:** Phase 6 metadata is complete.

1. Add one row to the matching scope table in `templates/index.md`.
2. Verify id/type/tags/widgets/dtags/preview values match metadata exactly.

**Exit:** Exactly one index row owns the template id.

## Phase 8 - Run Full Gate

**Entry:** Template JSON, metadata, and index row exist.

1. Run `bash scripts/lint-templates.sh`.
2. Require schema, dtag allowlist, denylist, metadata parity, and index checks to pass.
3. On failure, repair the source artifact and rerun the same gate; after three total failed
   attempts, stop with the unresolved evidence.

**Exit:** The complete lint gate passes and no generated/background process remains.

## Rationalizations To Reject

- "The flattened dump is easier": it loses subtree ownership.
- "Only the root id must change": descendant collisions break reused sections.
- "Normalize passed": normalize is not schema validation.
- "The string looks structural": classification follows the containing prop key.
- "Metadata is close enough": JSON, metadata, and index sets must be equal.

## Success Criteria

- [ ] Source owner and raw export hash are recorded.
- [ ] Subtree is self-contained with unique regenerated ids.
- [ ] Sanitization scans have zero violations.
- [ ] Metadata and index equal the stored JSON.
- [ ] Full template lint passes.
