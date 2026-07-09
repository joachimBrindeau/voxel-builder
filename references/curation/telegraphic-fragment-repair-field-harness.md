# Télégraphic-fragment repair via the per-post packet + field.py harness

Some klarc "innovant"/marker-cleanup restore batches ship a **packet harness**
instead of raw WP-CLI. One agent = one post. Recognise it by these files:

```
/tmp/klarc-innovant/AGENT_BRIEF.md          # the rules (read the "ZERO télégraphique" section)
/tmp/klarc-innovant/packets/<POST_ID>.json  # live+baseline for each field of that post
/tmp/klarc-innovant/field.py                # read/write ONE field, safe escaping, verifies write
/tmp/klarc-innovant/work/                    # scratch for .live / .new files
```

## field.py contract (memorise it)

```bash
# read the exact current value into a file (avoids terminal mangling of accents/quotes)
python3 field.py getfile <POST_ID> <KEY> work/<POST_ID>-<KEY>.live
# write an edited value back; prints  ok=True  newlen=NNNN  on success
python3 field.py setfile <POST_ID> <KEY> work/<POST_ID>-<KEY>.new
# count innovant occurrences in the live field
python3 field.py count <POST_ID> <KEY>
```

- Main post body key is **`__content__`**, NOT `post_content`.
- `setfile` self-verifies; if it prints `ok=False`, retry. Always `getfile` again
  after writing and grep to confirm the fix landed and JSON is still valid.
- The packet JSON is often **truncated** for long fields (`faq`, `conversion-timeline`).
  Do NOT trust the truncated `baseline` in the packet — reload the full baseline:
  `python3 -c "import json;print(json.load(open('packets/<id>.json'))['field_data']['<key>']['baseline'])"`
  and write it to a scratch file, then diff against the `getfile` live.

## The core disambiguation: broken fragment vs voluntary rewrite

The bad global replace stripped `innovant` AND collateral nouns
(`expert`, `experts`, `expertise`, `clé`, `complet`). In the SAME fields a
*voluntary* marker-cleanup also ran: `expertise → expérience`,
`savoir-faire → méthode`, dropped transitions, removed superfluous `innovant`,
removed French non-breaking spaces before `?  :  !  %`. **Keep the voluntary
edits; repair only the broken fragments.**

Trap: a word-level `difflib.SequenceMatcher(base, live)` diff *interleaves* both
kinds of change and looks like noise (`ertis`→`érienc` next to a bare deleted
`experts`). Don't act off the raw diff. Instead grep the LIVE text for the
telltale broken fragments and repair each one surgically:

```bash
grep -oE ".{40}(d' [a-z]| du MESRI|des [a-zàâéèêù]+ent |L' [A-Za-z]|composé d'|un du ).{40}" work/<id>-<key>.live
```

Real fragments seen (item → fix), all needing the **noun** `expert(s)` — which is
NOT the same as the voluntary `expérience` rewrite (a person vs a process):

| broken live fragment | repaired |
|---|---|
| `composé d' techniques` | `composé d'experts techniques` |
| `faire appel à un du MESRI` | `faire appel à un expert du MESRI` |
| `des évaluent l'éligibilité` | `des experts évaluent l'éligibilité` |
| `<p>L' analyse les caractéristiques` | `<p>L'expert analyse les caractéristiques` |

Decision rule per fragment: is the live phrase grammatically CASSÉE (truncated
syntagme, dangling article `d' `/`l' `, orphaned punctuation, verb with no
subject)? If yes → restore the missing noun/adjective from baseline. If the live
phrase reads correctly without `innovant` (clean adjective drop) → leave it.
When the missing word is a *noun the sentence needs* (`experts` after `des`,
`expert` after `un`/`L'`), you MUST restore the noun even though `expertise`
elsewhere was voluntarily changed to `expérience` — do not "fix" it to `expérience`.

## Glued punctuation `:` / `?` — repair, don't confuse with voluntary NBSP removal

The bad replace also produces *collapsed* punctuation: it glues the colon or
question mark straight onto the preceding word (`ce sont:`, `mon entreprise?`,
`catégories:`, `plusieurs phases:`). This IS a télégraphique defect and MUST be
repaired to a spaced form. Do NOT confuse it with the *voluntary* edit that
removed a French non-breaking space — those are different things:

- Voluntary NBSP removal = the space is gone but the text still reads as a
  deliberate typographic choice; leave it if the surrounding text is a clean
  rewrite.
- Glued-colon defect = punctuation welded to a word by the bad global replace;
  repair it.

**Match the target spacing to the baseline, don't assume NBSP.** Check the exact
byte the baseline uses before the colon before deciding:

```python
b = json.load(open('packets/<id>.json'))['field_data']['<key>']['baseline']
i = b.find('sont'); seg = b[i:i+8]
print([hex(ord(c)) for c in seg], repr(seg))   # 0x20 = regular space, 0xa0 = NBSP
```

In the klarc `conversion-*` / `faq` / `__content__` fields the baseline uses a
**regular space `0x20`** before `:` / `?`, not U+00A0. So repair `sont:` → `sont :`
and `entreprise?` → `entreprise ?` with a plain space, matching baseline.

## Final residual scan (prove ZERO télégraphique)

After writing every field, `getfile` each one again and grep for any word char
still welded to `:` or `?` (excluding JSON-structural `\":` and escaped `\/`):

```python
import re
bad = re.findall(r'[A-Za-zÀ-ÿ][:?](?![\\\"/])', open('work/<id>-<key>.check').read())
print('residual collés:', bad or 'NONE')
```

**Pitfall — scratch `work/` is shared across posts.** A glob like
`work/*.check` will pick up OTHER agents' / OTHER posts' scratch files (e.g. a
stray `7248-faq.check` when you are post 7299) and report false residuals.
Scan only YOUR post's files by explicit key, or confirm the offending filename
is a different POST_ID before worrying about it.

## Safe write pattern (JSON fields)

Edit the parsed structure, not the raw string, so JSON stays valid; assert each
substring is present exactly once before replacing; re-serialize compact:

```python
import json
lj = json.loads(open('work/<id>-faq.live').read())
for i, k, old, new in reps:
    assert lj[i][k].count(old) == 1, f'ambiguous/missing item {i}: {old!r}'
    lj[i][k] = lj[i][k].replace(old, new)
out = json.dumps(lj, ensure_ascii=False, separators=(',', ':'))
for frag in ["d' techniques", "un du MESRI", "des évaluent", "L' analyse"]:
    assert frag not in out
open('work/<id>-faq.new', 'w').write(out)
```

Then `setfile`, re-`getfile`, grep that no fragment remains and `json.load` passes.

## Report shape the brief wants (French)

Per field: RESTAURÉ / CONSERVÉ TEL QUEL + one-line justification; for each
restoration the avant→après extract (only the changed portion); confirm every
write printed `ok=True`. Note which fields were voluntary rewrites left untouched
(reformulated `<ul>` lists, `expertise→expérience`, dropped non-breaking spaces).
