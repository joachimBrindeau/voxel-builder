# Curation workflow — Voxel entity data

Curate Voxel data (records, taxonomies, profiles, linked WordPress users, organizations,
locations, relationships) **without corrupting relations, authors, user links, or generated
display fields**. This is a Sequential-Pipeline: Discover → Plan → Execute → Verify, with a
mandatory **safety gate** before any merge or delete.

## Entry criteria

1. User request names the entity type, record(s), and intended curation action.
2. `wpdev voxel:data` / `wpdev voxel:fields` can inspect the target CPT or taxonomy.
3. Merge/delete work has an evidence plan before mutation.
4. Profile/user operations include the profile↔user invariant check.

## Exit criteria

1. Discover evidence, planned mutation, executed command(s), and verification result are recorded.
2. Relationship targets, authors, generated display fields, and profile↔user links remain valid.
3. Merge/delete operations pass safety gate and preserve inbound references or document intentional removal.
4. `wpdev voxel:data` re-read confirms final state.

## Essential principles

- Use `wpdev voxel:*` first; raw `wp`, SQL, or PHP eval comes last.
- Preserve data evidence: capture before/after with `voxel:data` for every mutation.
- Keep patches narrow: set only changed fields, never re-write sampled whole-record blobs.
- Treat profile/user links as one invariant: profile `post_author` and user meta
  `voxel:profile_id` must agree.
- Delete last: merge/delete needs inbound-relation proof first (the safety gate).

## Phase 1 — Discover

**Entry:** site and target type/record intent known.

**Actions:**
1. Read [`../references/curation/cli-map.md`](../references/curation/cli-map.md).
2. Run narrow discovery:
   ```bash
   wpdev voxel:status <site>
   wpdev voxel:fields <site> <post_type>
   wpdev voxel:data   <site> --id=<id>
   wpdev voxel:sample <site> <post_type> --limit=3
   ```
3. Collect: post-type/taxonomy slug, field keys, expected shapes, author/user/profile links,
   relation targets, duplicates, and index/cache state.
4. For broad duplicate/relation investigation across many records or types, dispatch the
   [`voxel-curator-agent`](../references/subagents/voxel-curator-agent.md) subagent — one
   entity per dispatch (read-only investigation leaf; see
   [`../references/core/parallel-dispatch.md`](../references/core/parallel-dispatch.md) for
   the dispatch contract). If the host has no subagent facility, read the brief and perform
   its scoped investigation inline.

**Exit:** exact records, field schemas, relation targets, and risk areas identified.

## Phase 2 — Plan

**Entry:** discovery evidence available.

**Actions:**
1. Read [`../references/curation/field-semantics.md`](../references/curation/field-semantics.md)
   for profiles/users/relations.
2. Read [`../references/curation/lifecycle-checklists.md`](../references/curation/lifecycle-checklists.md)
   for the requested route (create / edit / merge / delete).
3. For merge/delete, read [`../references/curation/merge-delete-safety.md`](../references/curation/merge-delete-safety.md).
4. Write the action list: target records, exact field mutations, relation rewires,
   user/profile changes, delete/archive candidates, and the verification commands to run
   in Phase 4.

**Exit:** the mutation plan contains exact commands or safe manual steps; the destructive
safety gate (Phase 3, merge/delete) is understood.

## Phase 3 — Execute route

**Entry:** plan is evidence-backed. For merge/delete, the safety gate below must pass.

### Create

```bash
id=$(wpdev wp <site> post create --post_type=<post_type> --post_status=publish --post_title="..." --porcelain)
wpdev voxel:set-field <site> --id="$id" --set='<json>'
```

For **profiles**, create/repair the WP-user link in the same unit of work: set profile
`post_author`, set user meta `voxel:profile_id` with
`wpdev wp <site> user meta update <wp_user_id> voxel:profile_id <profile_id>`, then re-apply
the derived name fields.

### Edit

**`description`-type and `title`-type fields are core columns, not meta — `voxel:set-field --set '{"description":...}'` silently no-ops them.** Voxel maps the `description` field to `post_content` and the `title` field to `post_title`. `voxel:set-field` writes them as meta and the value never lands (the DB shows the field empty on re-read). Set them via the core column instead: `wpdev wp <site> post update <id> --post_content="..."` (description) / `--post_title="..."` (title). The `post_excerpt` (SEO excerpt, surfaced by `@post(excerpt)` in templates/cards) is likewise a core column — `wpdev wp <site> post update <id> --post_excerpt="..."`; posts created via `wp post create` start with an empty excerpt, so a freshly-scaffolded CPT record renders an empty hero byline/card blurb until you set it. After a create-then-populate pass, always re-read `post_content`/`post_excerpt` length, not just the Voxel meta fields.

**Short-text repeater subfields have a `maxlength` — a full sentence written into a label subfield is silently truncated.** Repeater subfields declared `text` carry a maxlength (e.g. events `target_audience.attendee` = 140, `outcomes.outcome` = 180, `agenda.title` = 140); the sibling `texteditor` subfield (`fit`, `details`, `summary`) is unbounded. Writing the same long sentence into both truncates the `text` one mid-word. Author a short semantic label for the `text` subfield and the full prose for the `texteditor` one. Confirm each subfield's type+maxlength before a bulk repeater write via `\Voxel\Post_Type::get(<cpt>)->get_field(<key>)->get_props()['fields']`.

```bash
wpdev voxel:data <site> --id=<id> > /tmp/before.json
wpdev voxel:set-field <site> --id=<id> --set='{"field":"value"}'
wpdev voxel:data <site> --id=<id> > /tmp/after.json
```

Verify the changed fields moved and the unrelated fields did not.

#### Bulk rich-text reformat (many records)

Reformatting a bulky single-`<p>` `texteditor` field into rich text (intro `<p>` →
`<ul><li>` → closing `<p>`) across a whole CPT is a fan-out variant of this Edit route with a
**pre-write QA gate**. Follow [`../references/curation/bulk-rich-text.md`](../references/curation/bulk-rich-text.md):
learn the format from a sibling field, extract per-key+base64 (TSV silently drops rows),
batch-reformat with a strict no-invention prompt, run the machine QA gate (format + fidelity +
links + no-drop + grammar) **before** writing, write through the terminal (not the code
sandbox — `bun` PATH) with payloads from files (HTML quoting), then re-scan the DB to catch
silently-skipped records. **Do not listify prose** (testimonials, short definitions, bios).

### Merge — SAFETY GATE

**Do not delete the duplicate until inbound-relation proof exists.** Gate steps:

1. Freeze all inputs with `voxel:data`.
2. Choose the canonical record by URL, user/profile link, inbound relations, and verified content.
3. Copy missing good fields into the canonical record.
4. Rewire inbound relations from the duplicate to the canonical record.
5. Reindex/cache if needed.
6. **Gate:** verify no live references to the duplicate remain (inbound-relation scan returns empty).
7. Only after that proof: trash/delete the duplicate.

### Delete — SAFETY GATE

1. Confirm identity from `voxel:data`.
2. **Gate:** confirm no inbound refs, no profile/user dependency, and no unique media/data dependency.
3. Prefer trash/archive when any uncertainty remains.
4. Delete only after the gate passes with proof.

**Exit:** the intended mutation is done and before/after evidence is captured.

## Phase 4 — Verify

**Entry:** a route executed, or an audit-only route needs a report.

**Actions:**
1. Run:
   ```bash
   wpdev voxel:data   <site> --id=<id>
   wpdev voxel:status <site>
   ```
2. For profile/user work, verify: profile `post_author`, WP user identity, user meta
   `voxel:profile_id`, and the Voxel name/title/org/location fields.
3. For merge/delete, verify the duplicate no longer has inbound references.
4. Report the exact commands and their results.

**Exit:** status healthy, or remaining warnings classified as pre-existing/unrelated.

## Mistake guards

- Never merge/delete without inbound relation scan and explicit safety gate.
- Never repair profile/user links without checking both WordPress user meta and Voxel record fields.
- Never trust generated display names; re-read stored fields after mutation.

## Success criteria

- [ ] Target records identified from real `wpdev` output (not assumed).
- [ ] Field mutations are narrow and evidence-backed.
- [ ] Profile/user invariant verified when relevant.
- [ ] Merge/delete passed the safety gate with inbound-relation proof.
- [ ] `voxel:data` and `voxel:status` evidence included in the report.

## Reference index

| Need | File |
|---|---|
| Commands | [`../references/curation/cli-map.md`](../references/curation/cli-map.md) |
| Profile/user/relations semantics | [`../references/curation/field-semantics.md`](../references/curation/field-semantics.md) |
| Bulk rich-text reformat (texteditor fields, many records) | [`../references/curation/bulk-rich-text.md`](../references/curation/bulk-rich-text.md) |
| Create/edit/merge/delete checklist | [`../references/curation/lifecycle-checklists.md`](../references/curation/lifecycle-checklists.md) |
| Destructive safety gates | [`../references/curation/merge-delete-safety.md`](../references/curation/merge-delete-safety.md) |
| Broad investigation subagent | [`../references/subagents/voxel-curator-agent.md`](../references/subagents/voxel-curator-agent.md) |
