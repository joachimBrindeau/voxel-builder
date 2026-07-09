# Bulk excerpt / meta-description optimization (lean-seo)

Redraft WordPress `post_excerpt` values (and the real per-CPT description source) as SEO meta
descriptions across all CPTs. Strips AI markers, enforces a 120–155 char limit, applies per-CPT
intent rules, and runs an LLM row-by-row review when asked.

Use when: "remove AI markers from excerpts", "optimize excerpts for meta descriptions", "fix meta
descriptions across CPTs", "find every excerpt outside Google best-practice range", bulk SEO
cleanup, or "lean-seo markdown `.md` truncates the Author excerpt / author bio".

This is the **excerpt/meta-description** companion to [`../../workflows/settings.md`](../../workflows/settings.md)
(lean-seo Meta surface) and [`lean-seo-metadata.md`](lean-seo-metadata.md).

## CRITICAL — decode the description resolver FIRST (post_excerpt ≠ meta description)

Before writing a single character, find out **which field actually feeds `<meta
name="description">` per post type**. On lean-seo, `lean_seo_get_post_description()` (in
`plugins/custom/lean-seo/includes/seo.php`) resolves in order:

1. per-type **`desc_template_<type>`** setting (a token string like `%hook%`, `%excerpt%`) — if
   set, it WINS and the excerpt is ignored.
2. a Voxel description meta key (via `lean_seo_description_meta_key` filter; empty by default).
3. **`post_excerpt`** (fallback).
4. site tagline.

So `post_excerpt` is the source ONLY for types with no `desc_template_<type>`. Dump the settings
and read them:

```bash
# lean-seo stores settings in the 'lean_seo_meta' option (NOT lean_seo_settings)
./wpdev wp <site> option get lean_seo_meta --format=json | grep -v '^Deprecated' \
  | python3 -m json.tool | grep -iE 'desc_template|archive_desc'
```

Route each type to its real field. Example: `desc_template_glossaire = %hook%` → the glossaire
meta description comes from the Voxel **`hook`** meta, so agents must write `hook`
(`update_post_meta($id,'hook',…)`), NOT `post_excerpt`, for that type. `archive_desc_post =
%excerpt%` is the POST-ARCHIVE description only, not singular. Types with no template fall through
to `post_excerpt`.

**`LEAN_SEO_DESC_LIMIT = 155`**: lean-seo hard-truncates the resolved description at 155 chars on a
word boundary. Target **120–152** (buffer); never author over 155 — anything longer is silently
clipped mid-word.

## Workflow

### 1. Determine scope and current excerpt lengths

List public post types first; include only public content CPTs. Skip `attachment`, Elementor
internals, floating buttons, and private/system types unless asked.

```bash
./wpdev wp <site> post-type list --public=1 --fields=name,label --format=csv
```

Fast length audit via SQL before exporting heavy content:

```bash
./wpdev wp <site> db query "SELECT post_type, COUNT(*) total,
  SUM(CHAR_LENGTH(TRIM(post_excerpt))<120 OR CHAR_LENGTH(TRIM(post_excerpt))>155) bad,
  MIN(CHAR_LENGTH(TRIM(post_excerpt))) min_len, MAX(CHAR_LENGTH(TRIM(post_excerpt))) max_len
  FROM wp_posts WHERE post_status='publish'
  AND post_type IN ('post','page','events','exp','geo','glossaire','testimonials')
  GROUP BY post_type;"
```

Then export current excerpts for drafting:

```bash
./wpdev wp <site> post list --post_type=<cpts> --post_status=publish \
  --fields=ID,post_type,post_title,post_excerpt --format=json > /tmp/excerpts-export.json
```

### 2. Inspect for AI markers + length issues

```python
import json, collections
data = json.load(open('/tmp/excerpts-export.json'))
print('rows', len(data)); print(collections.Counter(r['post_type'] for r in data))
for r in data:
    e = r.get('post_excerpt') or ''
    if not e or len(e) > 155 or any(s.lower() in e.lower() for s in
        ['découvrez','essentiel','boostez','plongez','incontournable',
         'nous vous accompagnons','vous accompagne','nos experts','notre service']):
        print(r['ID'], r['post_type'], len(e), r['post_title'])
```

### 3. Redraft and audit

Default bulk cleanup can use deterministic scripts, but if the user says "LLM audit" / "full
audit" / "no programmatic check only", run an actual **LLM row-by-row audit** for every exported
excerpt. Programmatic regex/length checks are hard gates AFTER LLM review, not a substitute. Chunk
rows (e.g. 20), require each ID exactly once, and save the LLM audit JSON artifact.

**Rules (content-quality standard):**
- **Site language only.** One sentence, no HTML, no markdown, no line breaks.
- **Length:** 120–155 chars, never over 155.
- **AI markers to strip:** Découvrez, Explorez, Plongez, Boostez, incontournable, essentiel, dans
  cet article, guide complet, notre service, nos experts, nous vous accompagnons, `<brand>` vous
  accompagne, vous accompagne (and variants).
- **Keep brand only where useful** (services/org/geo). Don't start every service with the brand.
- **Per-CPT intent** — map each type to its intent (e.g. service = concrete meta + benefit;
  glossary = definition-style, precise, neutral; testimonials = client proof; profile =
  expertise/person; events = webinar description from title; geo = local presence; org =
  organization; job = recruitment).
- **No false claims.** Preserve facts, accents, apostrophes. Avoid duplicate descriptions.

**Implementation:** apply regex replacement chains for known AI patterns, then trim to the last
sentence/word boundary within 155 chars, add a trailing period if missing, drop trailing connector
words (de, des, du, le, la, les, et, ou, à, au, aux, en, par, pour, sur…).

For a concise real-world bulk range audit + SQL verification pattern, see
[`lean-seo-excerpt-bulk-range-audit.md`](lean-seo-excerpt-bulk-range-audit.md).

### 3b. Concurrent LLM generation via 9router (context-aware, not regex cleanup)

When the user wants *rewritten* descriptions "based on page context" (not just marker-stripping),
generate them with a sonnet-class model through a local OpenAI-compatible endpoint, fanned out
concurrently with a validation-retry gate:

- Dump each row with rich context: `id, type, title, url (path = semantic breadcrumb), existing
  excerpt/hook, first ~1200 chars of stripped post_content`.
- One `ThreadPoolExecutor(max_workers=8)` fanning `POST <endpoint>/v1/chat/completions` with a
  sonnet-class model, `Authorization: Bearer <key>` from env — the local endpoint DOES require the
  key.
- Per-type config maps each type to `{field, lo, hi, kind}` so the prompt and applied field are
  both correct (route glossary→`hook`, rest→`post_excerpt` per the resolver section above).
- Deterministic **validation gate** per response: length in `[lo,hi]`, terminal punctuation for
  excerpts, no `…`/dangling-hyphen truncation marker, no url/token/`%..%`/markup. On fail, append
  the bad output + a "non conforme, corrige" turn and retry (≤4 attempts, nudge temperature up).
- Write results to JSONL (`id,type,field,text,len,ok`), then apply with the idempotent no-purge
  script. Sample one id per type FIRST and eyeball quality before running all N.

Full reusable orchestrator + gate:
[`lean-seo-ninerouter-concurrent-generation.md`](lean-seo-ninerouter-concurrent-generation.md).

### 4. Apply via WP-CLI eval-file (idempotent, no per-row purge)

Write ONE PHP script that reads the redrafted JSON and writes direct, neutralizing purge
side-effects during the loop, then does ONE bulk purge at the end (see LSCache pitfall). Apply
with `./wpdev wp <site> eval-file /tmp/apply-script.php`.

### 5. Verify live

```bash
./wpdev wp <site> post list --post_type=<cpts> --fields=ID,post_excerpt \
  | python3 -c "...check over-155, AI markers, empty..."
```

### 6. Backup

Export original excerpts before any mutation:
`cp /tmp/excerpts-export.json /tmp/excerpts-export.backup.$(date +%Y%m%d%H%M%S).json`.

## Pitfalls

- Post titles may be HTML-encoded (`&amp;`). `html.unescape()` before comparing.
- Some CPT items (Voxel profiles with no title) have empty titles — don't skip them; published
  empty-title profiles still need excerpts. Use Voxel field data or a per-CPT default.
- **LSCache purge cascade on bulk `wp_update_post()`** — the real cost. Each `wp_update_post()`
  fires synchronous LiteSpeed purge hooks that purge many URLs per post (post URL, `/`, `.md`,
  `sitemap.xml`, `sitemap-<type>.xml`, `llms.txt`, `llms-full.txt`, `robots.txt`). At ~250 posts
  this floods stdout and blows past a 300s timeout mid-apply. Fix — in the apply PHP script,
  neutralize purge/save side-effects during the loop and write direct, then ONE bulk purge at the
  end:
  ```php
  remove_all_actions('save_post'); remove_all_actions('post_updated'); remove_all_actions('edit_post');
  add_filter('litespeed_can_purge','__return_false',99);
  // for post_excerpt: $wpdb->update($wpdb->posts,['post_excerpt'=>$t],['ID'=>$id]); clean_post_cache($id);
  // for a meta field:  update_post_meta($id,'<key>',$t);
  ```
  Then once: `./wpdev wp <site> litespeed-purge all`. Make the script idempotent (skip rows already
  equal; count APPLIED/ALREADY/FAILED) so a timed-out first run can be re-run safely.
- Avoid updating many rows through one `terminal()` call per row — tool-call caps can stop
  mid-apply. Prefer one `wp eval-file` PHP script that loops all bad IDs.
- WP-CLI JSON output can contain control characters from rich post content. If parsing fails, use
  `json_parse(…, strict=False)` or audit lengths via `wp db query` before exporting full content.
- `wp db query` doesn't reliably accept `--format=csv` in every local setup; plain tabular output
  is enough for verification.
- French connectors (de, des, du, le, la, les…) at the end of a trimmed string leave a dangling
  fragment. Always restore punctuation.
- **lean-seo markdown truncation**: `lean_seo_markdown_author_excerpt()` in
  `modules/llms/inc/markdown.php` may truncate WP user author bios to 28 words with `...`. Remove
  the truncation logic (return `$excerpt` directly). Also update
  `lean_seo_markdown_has_author_excerpt_metadata()` to treat cached lines ending with `...`/`…` as
  stale so they regenerate. Ad-hoc verify script:
  [`../scripts/lean-seo-markdown-truncation-verify.py`](../scripts/lean-seo-markdown-truncation-verify.py).
- **Empty-title profile CPT records**: `post list --post_status=any` shows drafts/pending/publish
  profiles with empty `post_title`. Include them in the export — they're real published Voxel
  profiles. Write custom excerpts from available field data.
- **Local LLM endpoint for audit**: if a first-party CLI isn't callable, use an OpenAI-compatible
  local endpoint. Requires Bearer auth from env. Chunk rows in batches of 20 with `response_format:
  {type: json_object}`.
- **Hard gate after LLM audit**: after the LLM returns rewritten excerpts, always run the
  programmatic gate (over-155, AI-marker regex, empty check) before applying. If it fails, reject
  the whole chunk — don't let bad LLM output reach the DB.
