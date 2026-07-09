# wpdev ops appendix

Generic wpdev operations that matter around Voxel/Elementor work. Use this only for site/remote/db safety context; Voxel build/audit commands remain in `command-surface.md`.

## Source of truth

Prefer live CLI help when exact flags matter:

```bash
wpdev --help
wpdev <command> --help
```

Current verified CLI version during absorption: `wpdev v2.0.0`.

## Site lifecycle

```bash
wpdev init                              # initialize workspace once
wpdev work <site>                       # create if needed, generate .mcp.json, open editor
wpdev new <site>                        # create site + DB + symlinks + SSL
wpdev list                              # list sites
wpdev open <site> --admin               # open wp-admin
wpdev link <site> <plugin-or-theme>     # symlink workspace asset into site
wpdev unlink <site> <slug>              # remove symlinked asset
wpdev destroy <site> --force            # remove site + DB
```

Site names are lowercase/hyphenated. Databases use `wp_<site>` with hyphens converted to underscores. Local URLs use `https://<site>.test`.

## MCP config

```bash
wpdev mcp <site>              # generate site .mcp.json with MySQL MCP by default
wpdev mcp <site> --wordpress  # add WordPress MCP adapter
wpdev mcp <site> --show       # print current config
```

`wpdev work <site>` creates `.mcp.json` if missing. This is generic site MCP config, not EMCP. For Elementor live editor reads, see `command-surface.md` §EMCP vs headless wpdev reads.

## WP-CLI passthrough

Always use:

```bash
wpdev wp <site> <wp-cli args...>
```

Never rely on `cd sites/<site> && wp ...`; shell cwd persists across tool calls and repeated relative `cd` can break.

## Database operations

```bash
wpdev db:export <site> [--output file.sql]
wpdev db:import <site> file.sql [--replace-url https://prod.example]
wpdev db:reset <site> --force
wpdev db:encoding <site> [--fix --yes]
wpdev db:hierarchy <site> [--type page] [--audit]
```

Exports handle GTID with `--set-gtid-purged=OFF`. Import/pull paths strip PHP warning noise that can corrupt SQL streams.

## Backup operations

```bash
wpdev backup:create <site>
wpdev backup:remote <remote>
wpdev backup:list [remote-or-site]
wpdev backup:restore <site> backups/<name>/<file>.sql.gz [--replace-url https://prod.example]
wpdev backup:delete <name> <file> --yes
```

Remote backups use SSH + `mysqldump`, not `wp db export`, because some hosts disable PHP `exec()`. Empty backup files are rejected.

## Remote operations

```bash
wpdev remote:add <name> --host=<host> --user=<user> --port=<port> --path=<wp_path> --url=<url>
wpdev remote:list
wpdev remote:ssh <name>
wpdev remote:wp <name> option get siteurl
wpdev remote:tunnel <name> [--port 3307]
wpdev remote:sync:pull <name> --db --uploads --local-site=<site>
wpdev remote:sync:push <name> --plugins --themes --mu-plugins --yes
wpdev remote:sync:push <name> --dry-run
```

Push is destructive. It creates a safety backup first, then confirms unless `--force`/`--yes` is passed. Prefer scoped pushes (`--plugins`, `--themes`, `--mu-plugins`) over full DB pushes unless explicitly required.

## Remote deploy checklist

```bash
wpdev backup:remote <remote>
wpdev remote:sync:push <remote> --plugins --themes --mu-plugins --yes
wpdev remote:wp <remote> "eval 'flush_rewrite_rules(true);'"
wpdev remote:wp <remote> "litespeed-purge all"
```

Post-push cache flushing in wpdev covers Elementor CSS, object cache, transients, rewrite rules, LiteSpeed, OPcache, and Cloudflare if configured.

## Rebuild / purge

```bash
wpdev rebuild <site>                    # tokens + purge + CSS + Voxel reindex
wpdev rebuild <site> --only tokens
wpdev rebuild <site> --only purge
wpdev rebuild <site> --only css
wpdev rebuild <site> --only reindex
wpdev rebuild <site> --only reindex --recreate
wpdev purge <site>                      # legacy top-level alias still exposed
```

Use `--recreate` after Voxel blueprint/search-filter changes so index-table columns match current filter graph.

## Diagnostics

```bash
wpdev doctor
wpdev debug:on <site>
wpdev debug:tail <site>
wpdev debug:off <site>
wpdev audit <site> [--scope technical|a11y|wordpress|db-content|elementor|density|performance]
wpdev perf <site> [--json]
wpdev quality <plugin> [--tool=phpstan|phpcs|phpmd|insights]
```

Run narrow checks first. For plugin PHP changes, prefer `wpdev quality <plugin> --tool=<tool>`.

## Remote gotchas

- SSH multiplexing (`ControlMaster=auto`, `ControlPersist=60`) avoids server rate-limit failures on rapid SSH calls.
- Hostinger commonly uses SSH port `65002`; o2switch often requires cPanel SSH IP whitelisting.
- rsync push uses delete semantics; stale remote files disappear.
- File sync excludes `.git`, `node_modules`, `vendor`, `.env*`, logs, tests, lockfiles, and known dev-only plugins.
- URL replacement must handle JSON-escaped Elementor URLs (`https:\/\/...`) after normal `wp search-replace`.

## PHP output-buffer gotcha

In output-buffer callbacks, never return raw `preg_replace()` output without a fallback. `preg_replace()` returns `null` on regex error; returning null from `ob_start()` can cache an empty page.

```php
$result = preg_replace($pattern, $replacement, $html);
return $result ?? $html;
```

Variable-length lookbehinds such as `(?<!aria-label[^>]*)` are invalid in PHP PCRE.
