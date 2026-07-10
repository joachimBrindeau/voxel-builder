# Backup-vs-Live Diff & Surgical Token Restore

When a **specific word/phrase was globally deleted** (bad find-replace, over-eager
AI-marker cleanup, typo migration) and you must put it back **only where its loss
broke meaning/SEO** — while preserving all the *other* legitimate edits made since —
use a cross-DB diff, not gzip grep. Grep on compressed SQL is unreliable: values are
SQL-escaped, split across rows, and multi-occurrence; a plausible-looking `grep -c`
of 0 is a false negative.

## 1. Find the RIGHT baseline (peak, not latest)

The latest backup may already be post-corruption. Scan a token count across many
backups over time to find the **peak before the loss**:

```bash
cd backups/<site>
for f in <candidate backups spanning the timeline>; do
  case "$f" in
    *.gz) n=$(gzcat "$f" | grep -oi TOKEN | wc -l);;
    *)    n=$(grep -oi TOKEN "$f" | wc -l);;
  esac
  printf "%-42s %8s\n" "$f" "$(echo $n|tr -d ' ')"
done
```

Growth over time is normal (real content added). Look for a **drop** between two
adjacent dates — that window is the corruption. Pick the backup just before the drop.
Pitfall: raw grep counts ALL tables (revisions, options); confirm the loss is in
source content by re-checking per-table after import.

## 2. Import backup into an ISOLATED scratch schema (read-only baseline)

Never restore over the live DB. Import into a throwaway schema you only SELECT from.

```bash
mysql -u root -e "DROP DATABASE IF EXISTS wp_<site>_baseline;
  CREATE DATABASE wp_<site>_baseline CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
# strip deprecation noise that WP-CLI dumps can capture into the .sql at export time
gzcat <peak-backup>.sql.gz | grep -v '^Deprecated:' > /tmp/baseline.sql
mysql -u root wp_<site>_baseline < /tmp/baseline.sql
mysql -u root -N -e "SELECT COUNT(*) FROM wp_<site>_baseline.wp_posts"   # sanity
```

Local dev DB: host MySQL usually listens on 127.0.0.1:3306, `root` with empty
password + socket auth works. `lsof -nP -iTCP:3306 -sTCP:LISTEN` to confirm.
A dump can contain `Deprecated:` lines at the TOP if it was created by WP-CLI on a
newer PHP — those cause `ERROR 1064 near 'Deprecated:'` on import. Strip them first.

## 3. Cross-DB diff: per meta_key and per post

Occurrence-count expression (counts multiple hits per row, TOKEN=8 chars for 'innovant'):
`(CHAR_LENGTH(x)-CHAR_LENGTH(REPLACE(LOWER(x),'token','')))/LENGTH('token')`

```sql
-- per source Voxel/content meta_key: baseline vs live
SELECT b.meta_key,
  ROUND(SUM((CHAR_LENGTH(b.meta_value)-CHAR_LENGTH(REPLACE(LOWER(b.meta_value),'token','')))/8)) base,
  ...same from live... 
FROM wp_<site>_baseline.wp_postmeta b ... ;

-- per (post_id, meta_key) worklist where baseline had token AND live differs
SELECT b.post_id, b.meta_key
FROM wp_<site>_baseline.wp_postmeta b
JOIN wp_<site>.wp_postmeta l ON l.post_id=b.post_id AND l.meta_key=b.meta_key
WHERE LOWER(b.meta_value) LIKE '%token%' AND l.meta_value <> b.meta_value;
```

Restrict `meta_key IN (...)` to **source** fields (h1, body, faq, description,
conversion-*, definition, content-*, role...). EXCLUDE generated/derived keys
(`_lean_seo_md`, `_elementor_data`, `_wp_attachment_metadata`) — those regenerate
from source and restoring them clobbers later work.

## 4. Classify SAFE vs FLAGGED (the crux)

Not every field is a clean restore. Since the baseline date, fields may have ALSO
been legitimately rewritten. Split them:

- **SAFE** — `normalize(strip_token(baseline)) == normalize(live)`: live is exactly
  baseline minus the deleted token, nothing else changed → restoring baseline
  verbatim is safe.
- **FLAGGED** — live diverged further (other words changed). Do a **word-level
  `difflib.SequenceMatcher`** between baseline and live tokens; if EVERY diff is a
  deletion of the target token (± adjacent punctuation) it's still safe. If diffs
  include real replacements (`expertise`→`expérience`, `Examinons`→`Voici`, name
  changes, dropped transition phrases), those are **voluntary edits** — DO NOT
  restore the field. Reinsert only the missing token into the CURRENT live text.

Never programmatically bulk-reinsert into FLAGGED fields: it takes judgment (is the
token's absence actually breaking meaning/SEO, e.g. `Jeune Entreprise` vs the legal
status `Jeune Entreprise Innovante` = JEI?). Batch 5-10 homogeneous post packets per
reasoning worker and keep one independent decision envelope per post (see below).

### Collateral words (the bad replace ate a NEIGHBOUR too)

The fault replace sometimes deleted **an adjacent word along with the target token**
(e.g. baseline `clé de voûte des projets innovants` → live `de voûte des projets`:
both `clé` AND `innovants` gone), leaving a grammatically broken fragment. Rule for
restoring the collateral word:

- **Test = is the CURRENT live phrase grammatically/semantically CASSÉE?** — a
  truncated syntagme, dangling article/preposition, orphaned punctuation. If yes,
  restore the whole broken fragment from baseline (keeping any voluntary reformulation
  around it). If the live phrase reads correctly without the token, do NOT reinsert —
  it was a voluntary adjective drop.
- Only restore neighbour words that (a) were in the baseline AND (b) whose absence
  breaks grammar. Never re-add words a voluntary edit deliberately removed
  (reformulations, dropped AI-marker transitions, `significatifs` and the like).
- Clean adjective/name drops (`PME innovantes`→`PME`, `Jeune Entreprise Innovante`→
  `Jeune Entreprise`, `situation d'entreprise innovante`→`…d'entreprise`) are NOT
  broken grammar — restore the token there only on the meaning/SEO test, not the
  breakage test. `PME innovantes` requalifies the JEI target → restore; a purely
  emphatic trailing `innovante` may be left if the sentence stands.

### When EVERY occurrence in a field needs the token (JSON/FAQ fields)

If the field is JSON (faq, timeline) and the diff shows the token belongs at *all* N
sites (it's the official dispositif name repeated per Q/A), don't hand-edit N spots.
Use a bounded regex with a negative lookahead so you never double-insert, assert the
replacement count, and re-validate JSON before writeback:

```python
import re, json
s = open('<post>-faq.live').read()
new, n = re.subn(r'Jeune Entreprise(?! Innovante)', 'Jeune Entreprise Innovante', s)
assert n == 12, n            # matches the diff worklist count exactly
json.loads(new)              # structure still valid — HTML/escaping intact
open('<post>-faq.new','w').write(new)
```

For scattered single fixes, prefer literal `s.replace(old, new)` guarded by
`assert s.count(old) == 1` so a non-unique or zero match fails loudly instead of
silently mangling. Then `count <post> <key>` after `setfile` to confirm the live
token tally matches intent.

## 5. Safe single-field writer (collation + arbitrary bytes)

Writing back via `mysql` hits two traps. Helper pattern:

- **Collation clash**: user-var `@k` defaults to `utf8mb4_0900_ai_ci`, columns are
  often `utf8mb4_unicode_520_ci` → `ERROR 1267 Illegal mix of collations`. Fix:
  `... AND meta_key = @k COLLATE utf8mb4_unicode_520_ci` and run mysql with
  `--default-character-set=utf8mb4`.
- **Arbitrary bytes (quotes, newlines, JSON, accents)**: don't try to escape the
  value inline. Hex-encode it and let MySQL decode:
  `UPDATE ... SET col = CONVERT(UNHEX('<utf8-hex>') USING utf8mb4) WHERE ...`.
- Always **read back and compare** after write (`ok=True`). Reading via `-N --raw`
  strips one trailing newline; account for that when comparing.

Provide `get`/`getfile`/`setfile`/`count` subcommands so a delegated agent edits a
file and calls `setfile`, never hand-types SQL. `getfile`/`setfile` (exact bytes to/
from a file) avoid terminal mangling of long HTML/JSON field values.

## 6. Per-post reasoning agents

Build one JSON packet per affected post (`{post_id, type, title, field_data:{key:{live,
baseline}}}`, `__content__` key for post_content). Write ONE shared brief encoding the
decision rules + typography + exact helper usage, then assign 5-10 homogeneous packets
per worker in bounded waves. Each worker returns one envelope per post: reads packet, decides field
by field (restore only where meaning/SEO broke; keep voluntary edits), writes via the
helper, verifies `ok=True`, reports in the site's language. Respond in the user's
language — state it in the agent context.

## Standing user rules for this class

- **NEVER bulk restore.** Scratch schema is read-only compare only; surgical per-field,
  one token at a time, after the user has seen the diff.
- Most removals of the token were often **intentional** (AI-marker cleanup). Restore
  ONLY the subset where the sentence meaning or an official term/SEO keyword broke.
  When unsure, leave the current live text.
