# Elementor Node Naming

Name every node in an existing page or template with a concise, native-like word.
The tree expresses hierarchy: `content > overview > introduction`, not parent-prefixed
labels. This route owns naming only, not tree construction or content changes.

## Scope and contract

- Include every root and descendant in `elements`, even hidden nodes, template hosts,
  legacy widgets and unused sections. Repeater content rows are not Elementor nodes.
- A site-wide request inventories all stored Elementor documents, all page/template
  kinds and statuses, and transitively included templates. Account for empty or malformed
  documents explicitly. Historical revisions are evidence, not active naming targets.
- Prefer lowercase single words such as `main`, `header`, `profile`, `content`,
  `overview`, `presentation`, `services`, `gallery`, `contact`, `address`, `hours`.
  Keep an existing suitable word. Choose meaningful distinct roles for children:
  `overview > introduction`, `presentation > description`, `gallery > images > image`.
- Preserve semantic HTML tags and stable node IDs. A name describes purpose, not its
  random ID, widget implementation, ordinal position or ancestor path.
- EF names must be unique within their document. Choose another accurate role word
  before accepting a suffix. If no honest distinct word exists, record the collision
  and use the editor's supported numeric suffix as an explicit exception. Never invent
  misleading synonyms merely to satisfy a regular expression.
- EF's current editor uses `settings._cssid` for Navigator labels, normalized through
  its slugifier. These names also become HTML IDs. Confirm installed behavior in
  `assets/js/editor/preview/wrapper.js` (`efModelName`, `getTitle`) before writing.
  Use the existing atomic string envelope. `_title` is not an EF naming substitute.
  For non-EF nodes, inspect their native title storage. Legacy widgets/containers use
  `settings._title` via `elementor:rename`; native atomics can prioritize
  `node.editor_settings.title` and need a verified writer for that field.

## Phase 0 - Inventory and rollback

**Entry:** Site and target document(s), or explicit site-wide scope, are known.

1. Run `./wpdev --help` and inspect the selected command's help. Read the core safety
   rules and the workspace browser QA skill. Name-only work does not regenerate schemas,
   rebuild trees, prune revisions or change editorial settings to satisfy build gates.
2. Export each target with `./wpdev elementor:export <site> <id>` and retain the JSON
   file path printed by the command. Its stdout is a receipt, not the exported JSON.
   For corpus work, also capture exact raw metadata bytes and SHA256 through sanctioned
   read-only `wpdev db:query`. Raw bytes are authoritative because export can recover
   malformed storage. Require one metadata row per document before writing.
   Capture `elementor:tree`, current lint findings, and source hashes. Retain originals
   and a restore plan without overwriting another task's artifacts.
3. Record a behavior contract: allowed delta is node-name storage only. Child order,
   IDs, tags, content, bindings, links, visibility, style and template references stay exact.
4. Inventory inbound fragment links across documents, literal and dynamic anchor values,
   scripts/styles/probes that select existing IDs, and rendered IDs of included templates.
   Preserve required IDs such as the skip-link target `main`. Direct children of tabs
   derive their visible labels and hash navigation from `_cssid`, so preserve their
   user-facing wording unless the request also authorizes a visible tab-label change.
   Inspect modal and scroll targets as well as links, including cross-page fragments.
   Preserve dynamic IDs on repeated cards and loop descendants when instance identity
   depends on them. A plain role word must not flatten a per-instance `@post(...)` ID.
   Check the installed loop renderer before assuming whether a static host name repeats.
   Renames of depended-on IDs
   require a separately enumerated, explicitly scope-approved reference update and
   verification, never a silent break. Otherwise retain the required name as an exception.
   Capture browser text/headings and layout for affected representative surfaces.

**Exit:** Every target is inventoried with a usable rollback snapshot and dependency map.

## Phase 1 - Author the complete naming map

**Entry:** Inventory and baseline are available.

1. Traverse the tree in context. Author one manifest entry per node, including retained
   names, with document ID, node ID, old name, proposed name, role and dependency verdict.
2. For large scopes, dispatch the named `node-name-author` brief in bounded batches of
   5-10 documents. Workers return maps only. The main agent owns validation and writes.
3. Validate exact coverage, real node IDs, one-word names or documented collision
   exceptions, uniqueness, preserved anchor targets and no contradictory roles.
   Resolve template-composition collisions when they affect runtime behavior.
4. Re-read the live documents before applying. A stale snapshot or changed node is a
   conflict: rebase that document's map, not its unrelated content.

**Exit:** Every inventoried node has a reviewed entry and all dependency conflicts have
an explicit safe outcome. A blocked node remains visible in the coverage ledger.

## Phase 2 - Apply centrally

**Entry:** Reviewed maps and fresh source hashes agree.

1. For EF nodes, produce the supported batch shape:
   ```json
   [{"post":13,"node":"b50a152","cssid":"content"}]
   ```
   Before choosing a writer, prove it binds the write to the reviewed source hash and
   preserves each existing naming-cell representation, all document marker metadata,
   and all non-name data. A helper that cannot meet those gates is not eligible.
   `./wpdev elementor:set-cssid <site> --map=<file> --yes` documents the batch shape,
   but is not a blanket permission to bypass CAS or serialization checks. For larger
   transactions inspect `elementor:apply-data` help and its manifest contract
   for a validated CAS write with rollback. It does not run the full editor save or
   unrelated migrations. A full editor Save is not a naming-verification step.
   Preserve the existing tree, changing names only. Inspect candidate serialization:
   a batch PHP decoder using associative arrays can turn empty JSON objects into arrays.
   Reject that drift rather than treating it as cosmetic. An originally empty native
   `settings: []` may become an object containing only its approved `_title` when that
   field is first added. Record and check that exact naming-container initialization,
   not arbitrary array/object conversion. Do not apply EF marker-writing
   helpers to native-only documents. Pre-existing schema debt can block
   a strict apply: report it rather than silently normalizing unrelated content.
   When supported helpers cannot meet the name-only contract, use a reviewed PHP writer
   through `elementor:mutate`, never an ad-hoc database update. Require the runner lock,
   site/document/type/status identity, exactly one metadata row, fresh raw SHA256,
   object-preserving JSON decode, approved naming-cell-only changes, durable private
   raw backup, CAS update and exact readback. Native `_title` and
   `editor_settings.title` stay native, without EF marker metadata. If the mutation
   command exits nonzero, readback hashes determine whether the write happened before
   a later lint failure. Never retry blindly when a rollback backup already exists.
2. Use one central writer, bounded batches, and per-document write receipts. Keep
   intermediate documents valid. Skip unchanged values. Reconcile failed/conflicted
   documents before proceeding, without overwriting concurrent edits. Multi-document
   apply is sequential, not all-or-nothing. On failure inspect actual hashes, classify
   before/after/conflicted documents and recover only confirmed applied records using
   the reviewed rollback evidence. Do not blindly replay a full reverse manifest.
3. Export/read back each changed document. Compare recursively against its baseline:
   only the explicitly approved naming cells and separately approved anchor references
   may differ. Require unchanged IDs, order, child counts and non-name settings.
4. Regenerate CSS/purge through the selected command's supported save tail. If needed,
   use `./wpdev purge <site>` once after the batch, not once per node. A mutate
   invocation using `--no-purge` skips CSS generation as well as cache purging, so this
   final rebuild is required before runtime acceptance.

**Exit:** Every write has matching read-back, name-only diff evidence and rollback.

## Phase 3 - Verify completeness and real editor behavior

**Entry:** All planned writes are accounted for.

1. Re-inventory the full requested scope. Require zero unaccounted documents/nodes,
   zero missing labels, and zero unexplained duplicate names or vocabulary exceptions.
   Prove a second naming pass makes no changes.
2. Run lint and anchor checks again, comparing findings to the baseline. Report existing
   defects separately. Inspect literal references as well as the CLI anchor report,
   which is not proof that every dynamic/script dependency is safe.
3. Open changed representative documents in authenticated Elementor using
   `./wpdev browser <site> '/wp-admin/post.php?post=<id>&action=elementor' --session=<unique>`.
   Expand Structure, observe the names, and reload to prove persistence. Inspect the
   settled screenshot. Check that actual model `getTitle()` values match the manifest.
4. Exercise affected tabs, fragment links and template consumers in a real browser.
   Compare rendered headings/text and layout to baseline, check console/page errors,
   and verify included-template IDs do not break behavior. Use representative documents
   per page/template kind and dependency pattern, not a screenshot as sole acceptance.
5. Close only task-owned sessions. Report document/node totals, renamed versus retained,
   exceptions, blocked items, verification coverage and rollback locations accurately.

**Exit:** Complete stored-data coverage and real-editor/runtime checks pass, or precisely
bounded unresolved items remain explicitly reported. Do not call partial coverage complete.
