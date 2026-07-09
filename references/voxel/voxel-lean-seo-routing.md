# Voxel + Lean SEO routing notes

Use when Voxel page/template URLs, CPT prefixes, and Lean SEO redirects overlap.

## Fast checks

Check explicit redirects before deep router debugging:

```bash
./wpdev wp <site> db query "SELECT id, old_path, new_path, active FROM wp_lean_seo_redirects WHERE old_path LIKE '%<slug>%' OR new_path LIKE '%<slug>%'"
```

If stale, deactivate not delete:

```bash
./wpdev wp <site> db query "UPDATE wp_lean_seo_redirects SET active=0 WHERE old_path='/<slug>' AND new_path='/'"
```

Flush after redirect changes:

```bash
./wpdev wp <site> cache flush
./wpdev wp <site> litespeed-purge all
./wpdev rebuild <site> --only css,purge --recreate
./wpdev wp <site> eval 'if (function_exists("lean_seo_redirects_flush_cache")) { lean_seo_redirects_flush_cache(); }'
```

Verify both slash forms:

```bash
for u in https://<host>/<slug>/ https://<host>/<slug>; do
  curl -k -sI -L -H 'Cache-Control: no-cache' "$u" | grep -iE 'HTTP/|location|x-redirect-by|x-litespeed-cache'
done
```

## Resolver pitfall

If Lean SEO resolves right page but `redirect_canonical` sends user elsewhere, inspect resolver query vars. Page resolution should clear post-style vars too, including `p`:

```php
unset( $query['pagename'], $query['name'], $query['error'], $query['attachment'], $query['post_type'], $query['p'] );
```

Prefer fixing stale vars + caches over disabling canonical redirects.

## Landing/archive split

- `/thing` = landing page, cloned from landing sibling like `/blog`.
- `/recherche/thing` = searchable archive, cloned from sibling `recherche/*` pattern.
- Navbar normally links landing page.
- Landing CTA can link search archive.
- CPT singles can remain under `/thing/{post_slug}` if routing supports prefix.
