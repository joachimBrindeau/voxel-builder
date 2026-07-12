# 9router concurrent SEO description generation

Reusable pattern for regenerating context-aware SEO meta descriptions for many WordPress posts at once, using sonnet via the local 9router OpenAI-compatible endpoint, with a hard validation-retry gate. Proven on Klarc: 252 public items, 0 failures, all under the lean-seo 155-char truncation limit.

## Field routing (decode plugin settings first — see [`lean-seo-excerpt-meta-descriptions.md`](lean-seo-excerpt-meta-descriptions.md))

| Type | lean-seo desc source | Field to WRITE |
|------|----------------------|----------------|
| glossaire (Klarc) | `desc_template_glossaire = %hook%` | Voxel `hook` meta |
| post, page, exp, events, geo, testimonials | fallback → `%excerpt%` | `post_excerpt` |

Do NOT hardcode this table — read `lean_seo_meta` option's `desc_template_<type>` keys for the actual site. Any type with a `desc_template` uses that token's field, not the excerpt.

## Endpoint facts

- URL: `http://localhost:20128/v1/chat/completions`, models `high`/`medium`/`low` (`medium` = claude-sonnet, vision OK).
- Auth: `Authorization: Bearer $NINEROUTER_KEY`. Key lives in `~/.hermes/.env` (`set -a; . ~/.hermes/.env; set +a`). The local endpoint requires the key — the older "no auth in local" note is stale.
- `.env` may have stray value-only lines that error when sourced (`line NNN: <b64>: command not found`); harmless, ignore.
- Non-stream: send `"stream": false` and read `choices[0].message.content`. Endpoint may still emit SSE for some calls — tolerate both.

## Orchestrator skeleton

```python
import json, os, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE="http://localhost:20128/v1/chat/completions"; MODEL="medium"
KEY=os.environ["NINEROUTER_KEY"].strip()
DUMP=json.load(open("/tmp/dump.json"))   # [{id,type,title,url,excerpt,hook,content}]

# per-type: field to write + strict length band + framing
TYPE_CFG={
 "glossaire":{"field":"hook","lo":90,"hi":118,"kind":"définition de glossaire juridique"},
 "post":{"field":"post_excerpt","lo":120,"hi":152,"kind":"article de blog / guide"},
 "page":{"field":"post_excerpt","lo":120,"hi":152,"kind":"page du site"},
 "exp":{"field":"post_excerpt","lo":120,"hi":152,"kind":"page de service"},
 "events":{"field":"post_excerpt","lo":120,"hi":152,"kind":"événement"},
 "geo":{"field":"post_excerpt","lo":120,"hi":152,"kind":"page locale"},
 "testimonials":{"field":"post_excerpt","lo":120,"hi":152,"kind":"témoignage client"},
}
SYS=("Tu es rédacteur SEO senior FR. Meta descriptions Google, une à deux phrases "
     "complètes, décrire précisément CE contenu (titre+contenu+URL), mot-clé tôt, "
     "ton pro concret. Pas de troncature, pas de guillemets/préfixe/markdown. "
     "Réponds UNIQUEMENT par la description.")

def path_of(u): return re.sub(r"^https?://[^/]+","",u or "").strip("/")

def call(msgs,temp=0.4):
    body=json.dumps({"model":MODEL,"messages":msgs,"temperature":temp,"stream":False}).encode()
    req=urllib.request.Request(BASE,data=body,headers={
        "Content-Type":"application/json","Authorization":f"Bearer {KEY}"})
    raw=urllib.request.urlopen(req,timeout=120).read().decode()
    if raw.lstrip().startswith("data:"):          # tolerate SSE
        t=""
        for ln in raw.splitlines():
            ln=ln.strip()
            if not ln.startswith("data:") or ln[5:].strip()=="[DONE]": continue
            try:
                j=json.loads(ln[5:].strip())
                d=j["choices"][0]
                t+=d.get("delta",{}).get("content","") or d.get("message",{}).get("content","")
            except Exception: pass
        return t.strip()
    return json.loads(raw)["choices"][0]["message"]["content"].strip()

def sane(s): return re.sub(r"\s+"," ",s.strip().strip('"').strip("'").strip())

def valid(s,cfg):
    n=len(s)
    if n<cfg["lo"] or n>cfg["hi"]: return False,f"len {n}"
    if cfg["field"]=="post_excerpt" and not re.search(r"[.!?]$",s): return False,"no end punct"
    if "…" in s or s.endswith("-"): return False,"truncation marker"
    if re.search(r"(https?://|\{\{|%[a-z_]+%|<)",s): return False,"url/token/markup"
    return True,"ok"

def process(rec):
    cfg=TYPE_CFG[rec["type"]]
    user=(f"TYPE: {cfg['kind']}\nTITRE: {rec['title']}\nURL: /{path_of(rec['url'])}\n"
          f"CONTENU:\n{rec['content'][:1200]}\n\nRédige la meta description idéale. "
          f"Longueur STRICTE {cfg['lo']}-{cfg['hi']} caractères. Réponds uniquement par la description.")
    msgs=[{"role":"system","content":SYS},{"role":"user","content":user}]
    for a in range(4):
        try: r=sane(call(msgs,0.4+0.1*a))
        except Exception as e: time.sleep(1.5); continue
        ok,why=valid(r,cfg)
        if ok: return {"id":rec["id"],"type":rec["type"],"field":cfg["field"],"text":r,"len":len(r),"ok":True}
        msgs+=[{"role":"assistant","content":r},
               {"role":"user","content":f"Non conforme ({why}). Corrige: uniquement la description, {cfg['lo']}-{cfg['hi']} car."}]
    return {"id":rec["id"],"type":rec["type"],"field":cfg["field"],"text":"","len":0,"ok":False}

with ThreadPoolExecutor(max_workers=8) as ex, open("/tmp/out.jsonl","w") as f:
    futs={ex.submit(process,r):r for r in DUMP}
    for fut in as_completed(futs):
        f.write(json.dumps(fut.result(),ensure_ascii=False)+"\n")
```

## Apply — sanctioned gated path only (core rule 9)

The generated `/tmp/out.jsonl` is candidate material, not a license to bulk-write. Apply
through the **sanctioned entity-data write path**, per record, with the core-rule-9 gate —
a raw `wp eval` loop of `update_post_meta` / `$wpdb->update` over field or meta content is
FORBIDDEN even at 250 records (it silently skips the Voxel field API, index, and read-back
that make the write correct). Route each field to its owner:

| Generated `field` | Sanctioned write |
|---|---|
| a Voxel field or arbitrary meta (e.g. `hook`) | `wpdev voxel:set-field <site> --id=<id> --set '{"<field>":"<text>"}'` |
| `post_excerpt` / `post_title` / `post_content` (core columns) | `wpdev wp <site> post update <id> --post_excerpt="<text>"` |

**Per-record gate (every row, not a sample):** capture `wpdev voxel:data <site> --id=<id>`
(or the core-column value) before and after; assert the targeted key changed to the generated
value and every unrelated key is byte-identical; skip rows already equal (report
`APPLIED/ALREADY/FAILED`); reindex. `voxel:set-field` reindexes by default; a `post update`
batch ends with one reindex pass. The proven *cache* discipline still applies — do the writes,
then ONE `wpdev rebuild <site> --only purge` (or `wp litespeed-purge all`) at the end rather
than a per-row purge cascade; see [`lean-seo-excerpt-meta-descriptions.md`](lean-seo-excerpt-meta-descriptions.md)
LSCache pitfall. The idempotent re-run design (write only rows that differ) is unchanged and is
what lets a capped run resume. **Content-quality gate:** the generated text must be authored to
the field's scoped spec (see [`../../workflows/content-generation.md`](../../workflows/content-generation.md)
and the field-scoped reference it routes to), never a mechanical transform of a sibling field.

## Verify

1. Re-read every generated id from DB, assert stored value == generated (`MATCH=N MISMATCH=0`), report len min/median/max (all ≤155).
2. Live-curl 2-3 URLs per field and grep `<meta name="description" content="...">` + `og:description` to confirm the resolver serves the new copy.

## Gotchas

- Sample one id per type and eyeball before the full run — catch tone/field drift early.
- `python3 -c "print(f'...\"key\"...')"` fails: f-strings can't contain backslashes. Put multi-line inspection in a `.py` file and run it, or avoid nested quotes.
- WP-CLI leaks `Deprecated:` lines to stdout on this stack; `grep -v '^Deprecated'` before piping to `json.load`.
- Get the key by SOURCING the env file, never by `grep`-scraping it: `set -a; . ~/.hermes/.env; set +a; export NINEROUTER_KEY`. Ad-hoc `grep -oE 'NINEROUTER_KEY[=:]...'` is fragile (has matched a stray quote → `keylen=1` → 401), and a leftover bad `export NINEROUTER_KEY='...'` from a previous command can shadow the real value. Assert `echo ${#NINEROUTER_KEY}` is ~35 and run one `curl` OK-probe before fanning out ~250 calls.
- Applier idempotency pays off: a first apply run can hit the 300s cap mid-loop from residual purge cost even with hooks removed (LSCache filter may not catch every code path). Re-running the same script writes only the remaining rows (`APPLIED=11 ALREADY=241`) — always report APPLIED/ALREADY/FAILED and design for re-run.
