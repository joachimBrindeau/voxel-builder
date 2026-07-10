# Voxel And EF Loop Authoring

Canonical current loop behavior for EF V4 templates, verified against `includes/loop/`
and `includes/voxel/voxel.php` on 2026-07-10.

## Choose The Loop Source

| Source | Meaning |
|---|---|
| `@post(<repeater>)` | Current post repeater rows |
| `@post(<relation>)` | Voxel post-relation items |
| `@site(loop_<cpt>)` | Voxel site/CPT collection |
| `@children(<cpt>[,<cpt>])` | Direct `post_parent` children, optionally CPT-filtered |
| `@post(hierarchy-siblings)` | Precomputed siblings excluding current post |

`@children()` is EF-native and queries published WordPress children. It is not a Voxel
dynamic tag. Use `@children(exp).count()` for an EF visibility gate; EF resolves the
count before handing the rule to Voxel.

## Envelope And Placement

```json
{"$$type":"vx-loop","value":{"tag":"@post(hierarchy-children)","limit":null,"offset":null}}
```

`tag` is raw inside the `vx-loop` envelope. Do not nest a string envelope. Put the loop
on the repeated unit: a card for cards, wrapper for templates, or composite row when only
that row repeats. Never put a row-only loop on the host widget.

## Iteration Context

Current EF rebinds Voxel's current post for post-id loops. Bare `@post(title)` and
`@post(permalink)` are canonical inside an iteration. For compatibility,
`ef_apply_loop_relation_context()` rewrites `@post(<active-relation>.title)` to
`@post(title)`, preventing historical self-traversal. Do not rely on that rewrite in new
content.

Use bare `.permalink`; `.:url` is its supported alias. `.:permalink` and relation `.url`
are not valid assumptions. Query `wpdev voxel:fields` for traversable fields.

Iteration numbers come from EF's loop stack (`@loop(iteration)` and qualified active-loop
bridges). Do not patch Voxel vendor files to inject `index`/`index_zero`; that historical
approach is upgrade-fragile and superseded.

## Mixed-Type Relations

A traversal such as `@post(hierarchy-children.post_type.key)` returns the first item's
scalar, not the full type set. It cannot prove any `exp` exists in a mixed relation.
For direct children, gate the section with:

```text
tag: @children(exp).count()
compare: is_greater_than
arguments: ["0"]
```

If the loop remains relation-backed, also filter each item:

```text
tag: @post(post_type.key)
compare: is_equal_to
arguments: ["exp"]
```

## Verification Matrix

1. Empty source: repeated output absent and owning section gate false.
2. One item: one distinct title and real permalink.
3. Multiple items: unique titles/permalinks and expected order.
4. Mixed relation: only allowed CPTs render.
5. Nested relation: no self-traversal or grandchild leakage.
6. Browser: count roots, inspect hrefs, console, and network.

Use complete, sparse, mixed, and empty posts. Lint/schema success cannot prove loop
context or item filtering.
