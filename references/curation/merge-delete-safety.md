# Merge and delete safety

Voxel records often carry hidden dependencies: relations, author links, profile/user metadata, media, templates, and indexed values.

## Merge safety gate

Do not merge until all are known:

- canonical ID
- duplicate ID(s)
- post type
- current status/title/slug for each
- field snapshots saved
- relation fields involving candidates
- user/profile linkage if profile/user involved
- rollback path: before snapshots plus clear reverse mutation plan

## Canonical choice

Prefer record with:

1. correct public URL/slug
2. correct WP author/user/profile link
3. most inbound relations
4. strongest verified content
5. existing media/template references
6. newest correct editorial history only if above tie

## Inbound relation audit

Use cheapest adequate method:

1. `voxel:export` target types and search candidate IDs.
2. `voxel:sample` + `voxel:data` for related types.
3. Raw DB search only if Voxel commands cannot expose relation use.

No hard delete while inbound refs unknown.

## Delete safety gate

Hard delete only when:

- duplicate fields transferred or intentionally discarded
- no inbound relations remain
- not linked from WP user meta `voxel:profile_id`
- not needed as `post_author` profile target
- media/files not uniquely referenced
- `voxel:status` clean after deletion

If any unknown: trash/archive, do not hard delete.

## Verification evidence

Keep concise evidence in final report:

```text
before: /tmp/<site>-<id>-before.json
after: /tmp/<site>-<id>-after.json
commands: voxel:data, voxel:status
result: canonical <id>, duplicate <id> removed/trashed, no inbound refs found
```
