# WordPress content surgery — repair corrupted/degraded visible copy

Repair corrupted WordPress copy with minimal, auditable edits. Prefer original backup intent
where available. **Never bulk-restore whole tables/pages** when the ask is manual surgical work.

Use when copy got mangled by migration, typo cleanup, an AI rewrite, Elementor/Voxel data edits,
or SEO copy work — "grammar got messed up", "fix headings and content", "perfect French/English
grammar", "use backups but don't restore in batch", "fix all pages and CPTs", "break up big
paragraphs / rich text instead of big fat text", "Elementor/Voxel/lean-seo copy looks truncated,
ungrammatical, or AI-damaged".

For **bulk rich-text reformatting** of Voxel `texteditor` fields (bulky single-`<p>` → intro/list/closing),
route to [`bulk-rich-text.md`](bulk-rich-text.md). For the **full-corpus quality audit against a
written standard** (every post/page's title/excerpt/H1/prose), see the escalation note in the
Pitfalls.

## Workflow

1. **Scope public content**
   - Identify public post types: `wpdev wp <site> post-type list --public=1 --field=name`.
   - Exclude infrastructure types unless needed: `attachment`, `elementor_library`, `e-floating-buttons`.
   - List published pages/CPTs:
     `wpdev wp <site> post list --post_type=post,page,<cpts> --post_status=publish --fields=ID,post_type,post_title,post_name --format=json`.

2. **Start with the requested priority page**
   - If the user says "start with homepage", inspect it first via browser snapshot and `_elementor_data`.
   - Export current Elementor data before edits: `wpdev wp <site> post meta get <ID> _elementor_data > /tmp/current-elementor.json`.

3. **Find original intent in backups**
   - Search backup SQL/JSON for the target post ID and `_elementor_data` / `post_content`.
   - Compare original phrasing against the current corrupted copy. Use backups as
     **source-of-intent, not bulk restore**.
   - When a specific word/phrase was globally deleted (bad find-replace, AI-marker over-cleanup,
     typo migration) and you must restore it only where meaning/SEO broke, do **not** grep gzip'd
     SQL — it is SQL-escaped, multi-row, and gives false negatives. Import the *peak* backup into
     an isolated scratch schema and run a **cross-DB SQL diff** per post/metakey. Full method:
     [`backup-diff-and-surgical-restore.md`](backup-diff-and-surgical-restore.md).

4. **Patch only exact bad fields/posts**
   - First determine whether rendered text is static template copy or **dynamic entity data**.
   - For Elementor JSON / static template text, load JSON, replace exact strings or narrow
     substrings, then re-import (`wpdev elementor:import … --save`).
   - For Voxel CPTs, do **not** stop at the rendered page or Elementor loop template. Inspect
     `wpdev voxel:post_types` and update the **source post meta** field (`h1`, `description`,
     `content`, `body`, `faq`, `conversion-*`, `author-name`, …). Rendered `.md`, cards, archives,
     loops, and lean-seo outputs read these dynamic fields. See
     [`voxel-dynamic-content-surgery.md`](voxel-dynamic-content-surgery.md).
   - For CPT/page `post_content`, use `wpdev wp <site> post update <ID> --post_content=…` only when
     the source really is `post_content`.
   - Avoid broad regex rewrites across all content unless every replacement is reviewed and logged.

5. **Scan all public pages/CPTs for known corruption patterns**
   - Combine `post_content` and `_elementor_data` per published record.
   - Search for fragments from prior corruption: missing nouns/adjectives, doubled connectors,
     missing apostrophes, malformed punctuation, dangling commas, SEO capitalization issues.
   - Treat programmatic scan as **triage only**; manually review each hit before writing.

6. **Verify live rendering**
   - Flush cache after mutations (`wpdev wp <site> cache flush` + `litespeed-purge all`).
   - Reopen affected URLs with a cache-busting query string; browser-check bad phrases are gone.
   - Re-run the pattern scan; final bad count should be zero or only acceptable false positives.

## French SEO copy rules

- French typographic spacing: space before `:`, `?`, `!`, `%`.
- Prefer sentence-case headings unless brand/legal style requires caps (`Propriété intellectuelle`,
  not `Propriété Intellectuelle`).
- Avoid malformed SEO keyword stuffing. Keep headings useful and grammatical.
- Preserve domain terms: `CIR`, `CII`, `R&D`, `propriété industrielle`, `propriété intellectuelle`.
- Keep testimonials credible: fix obvious grammar/encoding corruption, but do not over-polish into
  generic marketing copy.

## Pitfalls

- **Do not batch restore backups** when the ask is surgical. Backups guide exact edits only.
- **The latest backup may already be post-corruption.** Scan a token count across backups over
  time to find the PEAK before the loss (a *drop* between adjacent dates marks the corruption
  window); restore intent from that peak, not the newest file.
- **Split candidates into SAFE vs FLAGGED before restoring.** SAFE = live is exactly
  baseline-minus-the-deleted-token → verbatim restore OK. FLAGGED = live was ALSO legitimately
  edited since baseline → reinsert ONLY the missing token into the CURRENT live text, never restore
  the whole field. Word-level `difflib.SequenceMatcher` on baseline-vs-live tokens tells them
  apart; FLAGGED reinsertion needs per-post judgment. Batch 5-10 post packets per
  reasoning worker and require a separate field decision for every post.
- **A missing NOUN is not a voluntary adjective drop — restore it even amid a rewrite.** A bad
  replace eats nouns (`experts`, `expertise`, `clé`) leaving dangling `d' `/`l' `, subject-less
  verbs, or truncated NPs, while a voluntary cleanup runs in the SAME field. Keep voluntary edits;
  repair only broken fragments by restoring the missing noun from baseline. Grep the LIVE text for
  fragments (`d' [a-z]`, `L' [A-Z]`, `des …ent `) rather than acting off a raw `difflib` diff.
  Full harness in [`telegraphic-fragment-repair-field-harness.md`](telegraphic-fragment-repair-field-harness.md).
- **Collateral words: restore a NEIGHBOUR only when the live phrase is grammatically CASSÉE.**
  Restore an adjacent eaten word only if the current live text is a broken fragment; if it reads
  correctly, a clean drop is voluntary — apply the meaning/SEO test, not the breakage test. The
  "every occurrence needs it" regex technique (`TOKEN(?! Innovante)` + `subn` count assert +
  `json.loads` revalidate) is in [`backup-diff-and-surgical-restore.md`](backup-diff-and-surgical-restore.md).
- **Restrict the diff to SOURCE fields; exclude generated ones** (`_lean_seo_md`, `_elementor_data`,
  `_wp_attachment_metadata`) — they regenerate from source and restoring them clobbers later work.
- **Writing back via `mysql` hits two traps:** (1) user-var collation clash → `ERROR 1267 Illegal
  mix of collations`; fix with `… = @k COLLATE utf8mb4_unicode_520_ci` + `mysql
  --default-character-set=utf8mb4`. (2) escaping arbitrary bytes inline is fragile → hex-encode and
  `CONVERT(UNHEX('<hex>') USING utf8mb4)`. Always read back and verify after each write.
- A backup `.sql` from WP-CLI on newer PHP can have `Deprecated:` lines at the TOP → `ERROR 1064
  near 'Deprecated:'` on import; `grep -v '^Deprecated:'` before importing.
- `wp` may emit PHP deprecation warnings into stdout; strip lines starting `Deprecated:` before
  parsing JSON.
- Elementor JSON may contain escaped apostrophes and HTML spans; if exact replace misses, inspect
  the actual stored string from `_elementor_data` and patch that exact value.
- Voxel loop/template pages are often dynamic. If a homepage/card/archive shows bad copy from
  `@site(...)`, `@post(...)`, or loop data, fix the Voxel record's post meta source, not only the
  Elementor template or rendered markdown cache.
- lean-seo `.md`/meta outputs may be generated from Voxel fields and cached in `_lean_seo_md`,
  `_lean_seo_description`, `_lean_seo_title`. Fix source fields first; refresh generated SEO meta
  only after source is clean.
- Browser cache / generated assets may show stale text. Flush cache and use `?nocache=…` before
  concluding a fix failed.
- Delegated grammar agents should audit and propose; the orchestrator performs and verifies writes.
- **When the user escalates from "restore token X" to "process EVERY post/page" against a quality
  bar, stop hunting one token and run a full-corpus audit.** Write the quality bar down FIRST as a
  durable, **agnostic** reference doc (good excerpt / title / H1 / prose — length bands,
  keyword-first, benefit-driven, zero-telegraphic, typography, preserve-voluntary-edits) and make
  agents read it as source of truth; do not encode per-post facts in it. Then build ONE audit
  packet per content post carrying live+baseline for ALL surfaces (title, excerpt, post_content,
  every source meta). Batch 5-10 homogeneous post packets per reasoning worker; each post
  retains an independent result covering all four surfaces in order (title → H1 →
  excerpt → prose). Full escalation recipe in
  [`telegraphic-fragment-repair-field-harness.md`](telegraphic-fragment-repair-field-harness.md).
- **Collateral damage lives in fields where the target token count is unchanged — scan for
  breakage signatures, not just token diffs.** Run a signature scan over LIVE source fields for
  elision orphans (`[dlnsjcqu]['’]\s(?=[a-zàâ…])`), `caractère\s*</`, empty `<li>`, double-space —
  but FILTER false positives (skip `__content__` HTML-attribute hits like `href='http`,
  `media='all'`, and legit NBSP-before-punctuation). Merge real hits into the audit worklist.

## References

- [`klarc-french-copy-corruption.md`](klarc-french-copy-corruption.md) — concrete French
  corruption patterns, WP-CLI scan snippets, and verification gate from a real repair session.
- [`telegraphic-fragment-repair-field-harness.md`](telegraphic-fragment-repair-field-harness.md) —
  the per-post packet + `field.py` orchestration harness (getfile/setfile with `ok=True` verify,
  `__content__` key, truncated-baseline reload); broken-fragment vs voluntary-rewrite
  disambiguation; glued `:`/`?` punctuation repair; safe JSON-field write; final residual scan and
  the French RESTAURÉ/CONSERVÉ report shape.
- [`voxel-dynamic-content-surgery.md`](voxel-dynamic-content-surgery.md) — source-map for Voxel CPT
  dynamic fields and the rendered-snippet → post-meta repair workflow.
- [`bulk-rich-text.md`](bulk-rich-text.md) — bulk-reformat bulky single-`<p>` Voxel `texteditor`
  fields into rich text across many records (scope discipline, batch engine, QA gates, TSV
  silent-drop pitfall, write-back + live verify).
- [`../core/emcp-wordpress-mcp.md`](../core/emcp-wordpress-mcp.md) — clean EMCP / WordPress MCP
  wiring, app-password validation, OLS/OrbStack pitfalls, streamable-HTTP handshake verification.

## Reporting

Report concise facts: IDs/URLs changed, bad phrases fixed, backup source used (if any),
verification performed, and residual risk if full human proofreading was not exhaustive.
