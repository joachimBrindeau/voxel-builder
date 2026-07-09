# Voxel lifecycle checklists

## Create CPT record

1. Discover fields: `./wpdev voxel:fields <site> <post_type>`.
2. Sample similar records.
3. Create minimal post with title/status.
4. Set only evidenced fields.
5. Add relation IDs only after target records verified.
6. Run `voxel:data` and `voxel:status`.

## Create profile + user

1. Search existing profile/user first.
2. Create or select WP user.
3. Create profile post.
4. Assign profile author to WP user.
5. Set user meta `voxel:profile_id` to profile ID.
6. Set profile fields: names, title/job, bio, org/location relations.
7. Re-apply derived name fields after author assignment.
8. Verify profile data, WP user, and `voxel:status`.

## Edit record

1. Save before snapshot: `voxel:data`.
2. Read fields schema.
3. Build narrow JSON patch.
4. Apply `voxel:set-field`.
5. Save after snapshot.
6. Diff intended keys only.
7. Run status/reindex/cache if command output says needed.

## Merge records

1. Read all candidates.
2. Choose canonical by URL/history/content completeness.
3. List inbound relations if possible; otherwise export/search relevant post types.
4. Copy missing fields to canonical.
5. Rewire relations to canonical.
6. Verify canonical has all needed data.
7. Verify duplicate has no inbound refs.
8. Trash/delete duplicate.
9. Run `voxel:status`.

## Delete record

1. Confirm record identity from `voxel:data`.
2. Confirm no inbound relations.
3. Confirm no profile/user dependency.
4. Confirm no reusable media/data only stored there.
5. Prefer trash/archive when uncertainty remains.
6. Delete.
7. Verify gone and status healthy.

## Audit

Run:

```bash
./wpdev voxel:status <site>
./wpdev voxel:fields <site> <post_type>
./wpdev voxel:sample <site> <post_type> --limit=5
```

Report:
- broken author/profile links
- duplicate candidates
- empty required fields
- invalid relation targets
- stale derived names
- index/cache warnings
