# wpdev Voxel command map

Use from workspace root.

## Discovery

```bash
./wpdev voxel:status <site>
./wpdev voxel:fields <site> <post_type>
./wpdev voxel:data <site> --id=<id>
./wpdev voxel:sample <site> <post_type> --limit=3
./wpdev voxel:export <site> --output=/tmp/voxel-export.json
```

## Mutation

```bash
id=$(./wpdev wp <site> post create --post_type=<post_type> --post_status=publish --post_title="..." --porcelain)
./wpdev voxel:set-field <site> --id="$id" --set='<json>'                                  # one record/field; title→post_title, description→post_content
./wpdev voxel:apply-content <site> --manifest=/tmp/content.json --rollback=/tmp/rollback.json       # validated batch dry-run/preflight
./wpdev voxel:apply-content <site> --manifest=/tmp/content.json --rollback=/tmp/rollback.json --yes # apply + rollback bundle + read-back/reindex
./wpdev rebuild <site> --only purge                                                          # once after batch
./wpdev wp <site> post delete <id> --force
./wpdev voxel:backfill-authors <site> --post-type=<post_type>
```

`voxel:create`, `voxel:delete`, and `voxel:assign` are CPT/template administration commands, not record curation commands. Do not use them for individual record create/delete/profile-user linkage.

Profile/user linkage repair uses record + user-meta commands:

```bash
./wpdev voxel:set-field <site> --id=<profile_id> --set='{"post_author":<wp_user_id>}'
./wpdev wp <site> user meta update <wp_user_id> voxel:profile_id <profile_id>
```

## Cache / index / template health

```bash
./wpdev voxel:cache <site> clear
./wpdev voxel:templates <site>
./wpdev voxel:repair-options <site>
./wpdev voxel:status <site>
```

## Field rules

- Always inspect `voxel:fields` before `voxel:set-field`.
- Pass relation fields as ID arrays when current data shows array shape.
- Keep JSON narrow: only changed keys.
- Capture before/after with `voxel:data`.

## Fallback ladder

1. Existing `./wpdev voxel:*` command.
2. Existing WordPress admin UI/browser if safer for unknown field widget behavior.
3. `wp` command through `wpdev` utility only if needed.
4. Raw SQL/PHP eval only after backup and reason written.
