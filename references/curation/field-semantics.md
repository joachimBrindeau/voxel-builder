# Voxel field semantics

Known profile/user pitfalls and field shapes from real klarc work.

## Profile identity fields

Common profile keys:

- `h1`
- `hook`
- `voxel:name`
- `voxel:first_name`
- `voxel:last_name`
- `one-line`
- `voxel:bio`
- `voxel:avatar`
- `title`
- `job`
- `prefix`
- `video`
- `organisation`
- `location`
- `booking`
- `linkedin`
- `role`
- `experience`
- `education`
- `faq`

## Profile ↔ WordPress user invariant

For a real person profile:

- profile post `post_author` must be correct WP user ID
- WP user meta `voxel:profile_id` must equal profile post ID
- display fields can derive from author/user; after author swap, re-run `voxel:set-field` for name fields
- check WP user login/email/display name before creating duplicate user

## Derived name trap

Voxel profile name can derive from `post_author`. If `voxel:name` stays stale after field edit:

1. fix or create WP user
2. set profile `post_author`
3. set user meta `voxel:profile_id`
4. re-apply profile name fields with `voxel:set-field`
5. reindex/cache/status

## Relation fields

Known relation examples:

- organizations: `3331` = Klarc, `3333` = Klarc Finances
- locations: `2186` = Lyon, `2187` = Toulouse

Rules:

- Never invent relation target IDs.
- Read candidate relation targets first.
- Preserve array vs scalar shape from `voxel:data` / `voxel:fields`.
- On merge, rewire inbound references before deleting duplicate target.

## Content trust

Do not invent:

- external URLs
- media IDs
- booking links
- LinkedIn URLs
- role/title claims
- education/experience facts
- organization memberships

Leave empty or mark for human source if evidence absent.
