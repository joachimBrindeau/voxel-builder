# Node Name Author

Called only by [`node-naming.md`](../../workflows/node-naming.md) Phase 1.
Read that workflow's Scope and contract before authoring.

## Input

A bounded batch of 5-10 document snapshots, site/IDs, source hashes, node trees,
existing names and dependency constraints. A single unusually large document may
be partitioned into non-overlapping subtrees with shared claimed-name context.

## Work

1. Read every node's role from its settings, child context and visible content.
2. Produce a complete node-ID map, retaining suitable one-word labels. Use actual
   content roles rather than parent prefixes. Choose accurate alternate words for
   collisions and report unavoidable suffix exceptions.
3. Preserve required anchor IDs and identify each proposed dependency update for
   the coordinator. Do not silently rename a referenced ID.
4. Cover roots, hidden nodes and template-host nodes. Referenced documents belong
   to their own inventory entries. Repeater rows are not node-name targets.
5. Return one result per document, independently attributable and rejectable.

## Output

Return an array of common specialist envelopes, one per document, with
`scope_id: "document:<id>"`, `mode: "build"`, `status`, `evidence`, `output` and
`open_questions`. Put `post`, `sourceHash`, `nodeCount`, `entries` and `blockers`
inside `output`.
Each entry has `node`, `oldName`, `name`, `storage` (`_cssid`, verified legacy
`_title`, or native atomic `editor_settings.title`), `role`, `decision` (`rename`, `retain`, `blocked`), and `dependencies`.
Use `oldName: null` for an absent source field, not an invented empty string. Keep
functional anchor or per-instance dynamic ID exceptions exact and explain the consumer.
A proven required exception is `retain`, not an unresolved blocker. State exact node
coverage and collisions. Write scoped output only, never mutate
WordPress, regenerate assets, rename node IDs, commit or overwrite another batch.

**Done:** One independently valid result per input document, every node accounted
for, and unresolved roles/dependencies explicitly blocked rather than guessed.
