# Template Placeholder / Sanitization Policy (SSOT)

**This file is the single source of truth for template sanitization.** BOTH the
sanitizer (`workflows/section-templates.md`, U3) and the linter
(`scripts/lint-templates.sh`, U5) read the regex patterns below. Do **not**
duplicate the pattern list anywhere else — extend it here and both consumers
inherit the change.

> **Violation statement:** A stored template contains ONLY allowlist-pattern
> dtags + Lorem Ipsum + structural/style props. Any other dynamic tag, OR any
> denylist-pattern match, is a policy violation.

Patterns are written as **regex** (grep `-E` / PCRE compatible), not literal
strings, on purpose. Profile subfields vary (`job`, `avatar`, `permalink`, …)
and slug/title have multiple valid envelope forms, so literal matching
false-positives the moment a subfield changes (S2 review correction). A machine
consumer extracts the fenced `regex` blocks and applies them directly.

---

## 1. Universal-dtag allowlist (regex patterns)

These 8 dtag classes are the ONLY dynamic tags permitted to stay live in a
stored template. The list is **locked at exactly these 8** (Resolved Decisions);
do not add fields (e.g. no `@post(date)`).

Dtag syntax nuances that shape the patterns (from
[`../voxel/voxel-tags.md`](../voxel/voxel-tags.md)):
- String-type props MUST be wrapped `@tags()…@endtags()` before Voxel invokes
  `\Voxel\render()`; without the wrapper the literal leaks.
- The `vx` `$$type` envelope (`{"$$type":"vx","value":"…"}`) holds the raw
  expression WITHOUT `@tags()` — used for non-string prop slots: `_cssid`
  (slug cssid form) and image-id refs (featured image id).

Each entry below is labeled; the fenced `regex` block is the machine-extractable
pattern. Whitespace inside the `@tags()`/`vx` wrappers is tolerated with `\s*`.

### 1.1 parent title — `@tags()@post(parent.title)@endtags()`
```regex
@tags\(\)\s*@post\(parent\.title\)\s*@endtags\(\)
```

### 1.2 slug — bare `@post(slug)` AND cssid form `@post(types.slug)-@post(slug)`
Bare string-prop form:
```regex
@post\(slug\)
```
`vx`-enveloped cssid form (`{"$$type":"vx","value":"@post(types.slug)-@post(slug)"}`):
```regex
@post\(types\.slug\)-@post\(slug\)
```

### 1.3 title — wrapped `@tags()@post(title)@endtags()` AND core-property `@post(:title)`
```regex
@tags\(\)\s*@post\(title\)\s*@endtags\(\)
```
Core-property (`:title`) form, e.g. inline in a sentence:
```regex
@post\(:title\)
```

### 1.4 h1 — `@tags()@post(h1)@endtags()`
```regex
@tags\(\)\s*@post\(h1\)\s*@endtags\(\)
```

### 1.5 excerpt — `@tags()@post(:excerpt)@endtags()`
```regex
@tags\(\)\s*@post\(:excerpt\)\s*@endtags\(\)
```

### 1.6 author name — `@tags()@author(display_name)@endtags()`
```regex
@tags\(\)\s*@author\(display_name\)\s*@endtags\(\)
```

### 1.7 author profile — WILDCARD over ANY profile subfield (`permalink`, `job`, `avatar`, …)
```regex
@tags\(\)\s*@author\(profile\.[a-z_]+\)\s*@endtags\(\)
```

### 1.8 featured image id — `vx`-enveloped `@post(_thumbnail_id.id)` (image-id only)
```regex
"\$\$type"\s*:\s*"vx"\s*,\s*"value"\s*:\s*"@post\(_thumbnail_id\.id\)"
```
Value-only form (when scanning the extracted `value` string alone):
```regex
@post\(_thumbnail_id\.id\)
```

---

## 2. The Lorem-Ipsum rule

**Any static string prop NOT matching an allowlist pattern in §1 MUST be
replaced with Lorem Ipsum placeholder text before a template is stored.** Static
copy carries no live binding, so real wording is either brand-specific
(a proper-noun leak) or arbitrary — either way it must not persist in a reusable
template.

Concrete before → after examples:

| Prop | Before (stored real copy — VIOLATION) | After (Lorem Ipsum — COMPLIANT) |
|---|---|---|
| hero subtitle | `Find your dream artisan in Lyon today` | `Lorem ipsum dolor sit amet consectetur` |
| CTA button label | `Book a klarc pro now` | `Lorem ipsum` |
| section eyebrow | `Trusted by 2,000+ villes` | `Lorem ipsum dolor` |

A dynamic prop that already matches §1 (e.g. the H1 bound to
`@tags()@post(h1)@endtags()`) is kept AS-IS — never Lorem-ized.

---

## 3. Proper-noun / real-data denylist (regex pattern classes)

Zero matches allowed. These pattern classes are the machine-checkable half of
the violation statement (the "denylist-pattern match" clause). The linter (U5)
scans every string in the JSON against them.

### 3.1 site TLD — `.test` (dev host) and, contextually, real production TLDs
```regex
\.test\b
```
> **Curated list — extend this.** `.test` is the local dev TLD. Real production
> TLDs/hosts a template was sourced from (e.g. a live `.com`) MUST also be
> denylisted contextually. This is a curated set that grows as more templates
> are seeded; add production hosts here when they appear.

### 3.2 email address
```regex
[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}
```

### 3.3 phone number (international / grouped / local forms)
```regex
(?:\+?\d[\d\s().-]{6,}\d)
```

### 3.4 real URL — `http(s)://` excluding placeholder/example domains
Matches a real absolute URL but not `example.com` / `example.org` /
`placeholder`:
```regex
https?://(?!(?:www\.)?(?:example\.(?:com|org|net)|placeholder))[^\s"'<>]+
```

### 3.5 curated proper-noun word list
Whole-word, case-insensitive. **This list must grow as more templates are
seeded** — every real site/brand/city/service name discovered during extraction
gets appended here.
```regex
\b(klarc|Lyon|villes)\b
```
Seed entries and their kind:
- `klarc` — site / brand name
- `Lyon` — city name (seen in `hero-city-geo`)
- `villes` — service/section noun (French "cities")

---

## 4. Image placeholder rule

Non-featured images — decorative graphics, static illustration images, logos,
background art — MUST use a **neutral placeholder image reference**, not a real
attachment id or a real asset URL. Only the featured-image-id dtag (§1.8,
`@post(_thumbnail_id.id)` inside the `vx` envelope) is allowed to stay live,
because it is a universal, post-scoped binding that resolves per-post at render
time. Any hard-coded `id`/`url` on a non-featured image slot is a denylist
concern (real asset leak) and must be swapped for the placeholder before storage.

---

## 5. Classification pitfalls (read before sanitizing)

The allowlist in §1 is easy to misapply. These three traps false-green a naive
sanitizer/linter — internalize them before classifying any dtag.

### 5.1 Allowlist patterns must FULL-MATCH the whole dtag, not prefix-match

The §1 regexes match the **entire dtag value**, not a prefix or substring. A
dtag that merely *looks* related to an allowlisted one is **not** allowlisted →
neutralize (blank a routing slot / Lorem-ize display copy). Two recurring
lookalikes:

| Non-allowlist dtag | Why it FAILS the allowlist | Correct action |
|---|---|---|
| `@post(parent.permalink)` | §1.1 allows only `@post(parent.title)`. Any other `parent.*` subfield is non-allowlist. | neutralize (routing slot → `#`) |
| `@post(excerpt)` (bare) | §1.5 requires `@post(:excerpt)` — the **leading colon is load-bearing**. The bare form has no colon → not allowlisted. | Lorem-ize |

A "starts with `@post(parent.`" or "contains `excerpt`" check FALSE-GREENS both.
**Match the WHOLE dtag value** (regex `fullmatch`, not prefix/substring).

### 5.2 Proper nouns hide INSIDE dtag copy strings

Real brand/place names can be **embedded in a `@tags()…@endtags()` (or `vx`)
wrapper**, never as a standalone word — e.g.
`@tags()Bureau <Brand> à @post(geo-city)@endtags()`. A denylist scan that only
inspects **non-dtag** strings MISSES these. **Scan EVERY string value**,
including the literal text inside `@tags()`/`vx` wrappers.

### 5.3 Loop-source / geo / SEO dtags are NOT allowlisted

Only the 8 dtag classes in §1 stay live. These common families are **all
non-allowlist** → neutralize (blank a routing/binding slot, Lorem-ize display
copy):

- `@site(loop_*)` — loop-source bindings
- `@post(geo-*)` — geo / location fields
- `@site(seo.*)` — SEO-config fields
- `@post(<field>).fallback(...)` — any field-with-fallback expression

The reusable card **STRUCTURE** survives sanitization; the consuming agent
re-binds the loop/source when they splice the template. Do not preserve the live
binding just because the card is loop-shaped.
