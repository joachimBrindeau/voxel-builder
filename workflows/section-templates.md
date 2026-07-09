# Section-template extraction + sanitization workflow

Re-runnable procedure to turn a **live page hero (or reusable section)** into a
sanitized, storable `template.json` + `meta.yml` under
[`../templates/`](../templates/README.md). This is the "how" that produced the
seeds and that authors reuse to add more templates.

**Read first (do not re-derive from them):**

- [`../references/ef/template-transplants.md`](../references/ef/template-transplants.md) — raw-vs-flattened nesting hazard, id-regen rule, sibling-span pitfall.
- [`../references/templates/placeholder-policy.md`](../references/templates/placeholder-policy.md) — the 8 allowlist regex patterns + the denylist pattern classes (SSOT; cite it, never restate the patterns).
- [`../templates/README.md`](../templates/README.md) — the `meta.yml` schema, naming rule, "SSOT wins", and the refresh/migrate framing this workflow reuses.

> **Scope of this doc:** documentation only. It does **not** execute against any
> live site. Running it end-to-end against `klarc` to produce the two seed
> templates is a separate task.

Every command below is the **exact verified shape** — a worker with zero
interview context copies each one as-is. Do not invent alternate syntax.

---

## Phase 0 — Prerequisites

- `wpdev` on `PATH` (`./wpdev` from repo root, or `wpdev` if globally linked).
- `jq` available for subtree selection.
- Target site slug known (seeds use `klarc`).
- Target page path known (the URL path, e.g. `/services` → path `services`).

---

## Phase 1 — Resolve the page URL → postId

Resolve the page path to its WordPress post id.

```bash
wpdev voxel:page klarc --path services
```

- `--path` is the **page path** (e.g. `services` for `/services`, `villes/lyon` for `/villes/lyon`).
- `--url` is the **base HOST** (defaults to the site TLD) — **NEVER** pass a full
  URL like `https://klarc.test/services` as `--url`. That resolves wrong
  (trailing-slash mismatch). Only ever use `--path` for the page path.

The command prints **prose** to stdout, not a bare id:

```
Post: 1234 (page) — Services
```

Parse the id out of that prose:

```bash
wpdev voxel:page klarc --path services | grep -oE 'Post: [0-9]+' | grep -oE '[0-9]+'
```

Alternative bare-id form (skips the prose parse):

```bash
wpdev wp klarc eval 'echo url_to_postid("/services");'
```

Capture the result as `<postId>` for the next phase.

---

## Phase 2 — Export the full page tree

Export the page's Elementor data.

```bash
wpdev elementor:export klarc <postId>
```

- The output path is **auto-named** — the caller cannot choose it. It lands at
  `backups/elementor/klarc/<postId>-<timestamp>.json` (relative to repo root —
  **no** `workspace/` prefix).
- Output is a **bare JSON array** wrapping the full page root node directly —
  `[{...}]`, e.g. `[{"elType":"ef-wrapper", "elements":[...], ...}]`. It is
  **not** wrapped in an `elements` key (`{"elements":[...]}` is wrong).

Locate the newest export file:

```bash
ls -t backups/elementor/klarc/ | head -1
```

Prefix that filename with `backups/elementor/klarc/` to get the path used in
the next phases (call it `<export.json>`).

> **Geo-CPT gotcha (verified real case):** a `geo`-type Voxel post (e.g. a city
> page like `/villes/lyon`) may carry **no `_elementor_data` of its own** — it
> renders through its assigned Theme-Builder `single` template instead. If
> `elementor:export` reports no Elementor data for the resolved `<postId>`,
> resolve the CPT's assigned single-post template id instead (see
> [`../references/voxel/template-resolution.md`](../references/voxel/template-resolution.md))
> and export **that** postId — the hero lives there. Real example: postId
> `2186` was a `geo` type with no own data; its template postId `2642` held
> the actual hero.

---

## Phase 3 — Select the hero subtree

Read the **RAW nested `elements` array** from `<export.json>` (per
[`../references/ef/template-transplants.md`](../references/ef/template-transplants.md)).
**Never** use flattened `elementor:dump` output here — flattening loses
parent/child structure, so you cannot reconstruct a self-contained subtree from
it.

Identify the hero by its **top-level container node id** — usually the first
child of the page root (`.[0].elements[0]`), or the first `ef-wrapper`/section
node whose role / `_cssid` marks it as the hero.

Extract the matched subtree with `jq` (index or id) — remember `<export.json>`
is a bare array, so index into the array first (`.[0]`, the page root), then
into that root's `.elements[0]` for its first child:

```bash
jq '.[0].elements[0]' <export.json> > subtree.json
```

**Acceptance for this phase (mandatory):**

- The selected node MUST be a **single self-contained subtree** — one container
  node with all its descendants, not a fragment that references siblings.
- **A hero MAY span multiple sibling nodes.** If so (per the sibling-span
  pitfall in `template-transplants.md`), wrap the siblings together in one
  `ef-wrapper` before proceeding, so the result is again a single subtree.
- **Record the source node id + selector used** (the top-level container node id
  and the `jq` selector) — this goes into the template's
  `meta.yml.source_note` field in Phase 7 (per the `source_note` key in the
  [`../templates/README.md`](../templates/README.md) `meta.yml` schema).

---

## Phase 4 — Regenerate node IDs recursively

Regenerate the id of **every node** in the extracted subtree — top-level
container AND every descendant — not only the top-level wrapper. Duplicate
child ids collide when the template is later spliced into a different page and
can make cloned content render stale or drop (per the id-regen rule in
[`../references/ef/template-transplants.md`](../references/ef/template-transplants.md)).

---

## Phase 5 — Sanitize per the placeholder policy

Apply the sanitization rules from
[`../references/templates/placeholder-policy.md`](../references/templates/placeholder-policy.md)
(SSOT — the 8 allowlist regex patterns and the denylist pattern classes live
there; consume those exact patterns, do not re-derive them):

- **Keep** only the 8 allowlist-pattern dtags live.
- **Replace** every other static string prop with Lorem Ipsum.
- **Strip** every denylist-pattern match — real proper nouns, emails, phones,
  real URLs, the site TLD (`.test`) — swapping for Lorem Ipsum / neutral
  placeholder refs per the policy's image rule.

The violation statement (policy §Violation) holds: after this phase the subtree
contains ONLY allowlist-pattern dtags + Lorem Ipsum + structural/style props.

Before applying the rules, read the classification pitfalls in
[`../references/templates/placeholder-policy.md`](../references/templates/placeholder-policy.md)
§5 (full-match not prefix-match; the `:excerpt` colon is load-bearing; proper
nouns hide inside `@tags()` copy; `@site(loop_*)` / `@post(geo-*)` / `@site(seo.*)`
are non-allowlist). Those are the traps a naive pass false-greens.

### 5a — Key-driven classification (display vs routing vs structural)

Every copy string is enveloped `{"$$type":"string","value":"…"}`. You **cannot**
blanket-Lorem the `value` — it also holds structural enums (`"h2"`, `"primary"`,
`"secondary"`). The **containing prop KEY is the only signal**. Classify by key:

| Key class | Keys (extend as new ones appear) | Action |
|---|---|---|
| **DISPLAY → Lorem-ize** | `text`, `body`, `label`, `label_active`, `tooltip`, `byline_primary`, `byline_secondary`, `group_name`, `group_overflow_suffix`, `cal_title`, `cal_desc`, `cal_location`, `toast_message`, `media_caption`, `media_image_alt` | replace `value` with Lorem Ipsum |
| **ROUTING / PII → blank** | `link` (→ `#`); `modal_id`, `address`, `phone`, `email`, `scroll_to`, `cal_url`, `calendar_url`, `menu`, `vote_field_key`, image `url` (→ `""`) | blank the `value` |
| **STRUCTURAL → keep verbatim** | everything else — enums like `tag` (`h2`/`h3`), `variant`, `kind`, `size`, `source`, `theme`, … | leave untouched |

### 5b — Sanitize bare strings, not only enveloped ones

Loop-source bindings are **bare `str` values, not enveloped** — e.g.
`settings._vx_loop.value.tag = "@site(loop_geo)"` is a plain string, NOT wrapped
in `{"$$type":"string","value":…}`. An **enveloped-only** pass skips it and
leaks a non-allowlist dtag. **Also sanitize bare dict-string values.** Blank a
`tag` value **only when it contains a dtag** — guard with a has-dtag check so a
real heading `tag: h2` stays untouched.

### 5c — Sanitize `vx`-envelope values too

Some strings are `vx`-enveloped, not `string`-enveloped — e.g.
`{"$$type":"vx","value":"@tags()@site(loop_testimonials.image.url)@endtags()"}`
(often under key `url`). **Sanitize `vx` value strings as well.** Rule: if a `vx`
value is allowlisted (the featured-image-id, §1.8 `@post(_thumbnail_id.id)`) keep
it; otherwise neutralize (blank routing slots, Lorem-ize display copy).

### 5d — Non-featured image ids/urls → neutral placeholder

A hard-coded real attachment `id`/`url` on a **non-featured** image slot is a
real-asset leak — swap for a neutral placeholder (policy §4). Only the
featured-image-id dtag (§1.8) stays live.

---

## Phase 6 — Schema-fresh it (structural survivability pass only)

```bash
wpdev elementor:normalize <subtree.json> <template.json>
```

This is **structural survivability healing only** — base props, responsive
envelopes, null-prop drop. It does **NOT** reconcile per-prop against the schema
(it silently misses renamed props, schema-removed props, and new required nested
cells). Reuse the exact framing from
[`../templates/README.md`](../templates/README.md) §Refresh / migrate:

> ⚠️ The drift signal is the **`elementor:lint` validator**, **never**
> `elementor:normalize`. A normalize diff/no-op is **not** a valid drift check.

Real schema conformance is proven later by the **U5 lint gate**
(`scripts/lint-templates.sh`, not yet built), which runs `elementor:lint`'s
`validateNode`. `elementor:normalize` alone is never the drift gate.

---

## Phase 7 — Author `meta.yml`

Create the sibling `meta.yml` using the **exact key list** from the
[`../templates/README.md`](../templates/README.md) `meta.yml` schema:

`id`, `scope`, `type`, `name`, `tags`, `widgets`, `dtags_used`,
`requires_plugins`, `source_note`, `breakpoints` — plus `location`
(**only** when `scope: global`).

- `id` MUST equal the folder name and the `index.md` row id (kebab
  `<type>-<variant>`, no numeric suffix).
- `dtags_used` MUST equal the dtag-set actually present in `template.json`
  (the U5 lint gate checks both directions).
- `source_note` MUST carry the source node id + selector recorded in Phase 3.

---

## Phase 8 — Add an index row

Add **one row** for the template to
[`../templates/index.md`](../templates/index.md), in the table matching its
`scope` (Global / Sections / Pages), with the catalog columns
`id | type | tags | widgets | dtags-used | preview`.

---

## Phase 9 — Run the lint gate

```bash
bash scripts/lint-templates.sh
```

The template is **not complete** until this passes. This is the schema-fresh +
dtag-clean + denylist-clean + metadata-consistency gate.

> **This gate is live.** `scripts/lint-templates.sh` runs 5 checks: (a) schema-fresh
> via `wpdev elementor:validate --file <template.json>` (an Ajv-backed validator over
> the committed `widget-schemas.json` SSOT — the real codegen drift gate), (b) dtag
> allowlist, (c) denylist, (d) meta.yml↔JSON dtag-set consistency, (e) index row
> presence. `elementor:normalize` (Phase 6) is explicitly NOT a substitute for it —
> normalize does fixed structural healing only and cannot see renamed/removed/
> new-required schema props.

---

## Related

- [`../references/ef/template-transplants.md`](../references/ef/template-transplants.md) — nesting / id-regen / flatten pitfalls, transplant + verification loop.
- [`../references/templates/placeholder-policy.md`](../references/templates/placeholder-policy.md) — allowlist / denylist regex SSOT.
- [`../templates/README.md`](../templates/README.md) — store layout, `meta.yml` schema, SSOT-wins, refresh/migrate workflow.
