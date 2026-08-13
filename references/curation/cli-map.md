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
./wpdev voxel:set-field <site> --id="$id" --set='<json>'                                  # Voxel field, core alias, or registered post-meta key
./wpdev voxel:set-field <site> --id="$id" --set='<json>' --yes                            # apply in non-interactive/agent runs; title→post_title, description→post_content
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
- Plugin-owned per-post overlays must be registered with WordPress's post-meta schema before
  `voxel:set-field` or `voxel:apply-content` will write them. Pass JSON `null` to delete a
  registered meta row completely; an empty string is a stored value and does not prove absence.
  `voxel:apply-content` includes registered-meta presence/value in its guarded hash and rollback
  bundle, so use it when a multi-record release must remove an overlay atomically. Unregistered
  arbitrary meta remains rejected.
- Pass relation fields as ID arrays when current data shows array shape.
- `voxel:set-field` accepts Voxel `File_Field` subclasses such as `profile-avatar`,
  complete location objects (`address`, `latitude`, `longitude`), and `null` to clear
  a location. Do not fall back to raw meta writes for these profile fields.
- `voxel:set-field` does not accept whole `product` payloads. For a one-off stored
  `Product_Field` migration, write a temporary runner that mutates
  `$field->editing_value()` (never the decoded stored meta), then calls
  `sanitize()` + `validate()` + `update()` — `editing_value()` is what converts stored
  image IDs into the form shape Voxel's validator expects. When restoring
  `enabled=false`, load a fresh field instance for that second write: Voxel's
  disabled-product branch re-reads the in-memory pre-write payload and otherwise
  resurrects keys the migration just dropped.
- A product-type module can veto the payload: with `modules.custom_currency.enabled`
  true, `Currency_Field::sanitize()` nulls the whole product array, so
  `Product_Field::sanitize()` returns null for every product. Disable the owning
  module in `voxel:product_types` before migrating payloads that drop its key.
- For imported commerce data, normalize money into `\Voxel\get_primary_currency()`
  before building the product payload. Prefer an official target-market quote. If that
  market cleanly omits the product, acquire a second official quote whose monetary fields
  carry an explicit currency, then convert once during acquisition with a dated, sealed
  reference rate. Never infer amount currency from store metadata such as `/meta.json`.
  Network, GraphQL, malformed-response, identity, and variant-set failures remain
  acquisition errors and must not trigger FX fallback.
  Store no per-product `currency` when native Voxel primary-currency behavior owns the
  cart, checkout, and orders; verify `can_be_added_to_cart()` after migration.
- Keep JSON narrow: only changed keys.
- Capture before/after with `voxel:data`.
- In non-interactive or agent-run shells, pass `--yes` for the authoritative write. Without
  it, `voxel:set-field` can render a confirmation prompt and exit without mutating data.
  Never treat the prompt output as success; require the `Updated #<id>` result and the
  mandatory `voxel:data` read-back.

## Fallback ladder

1. Existing `./wpdev voxel:*` command.
2. Existing WordPress admin UI/browser if safer for unknown field widget behavior.
3. `wp` command through `wpdev` utility only if needed.
4. Raw SQL/PHP eval only after backup and reason written.
