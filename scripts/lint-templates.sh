#!/usr/bin/env bash
# lint-templates.sh — verification + codegen-drift gate for the section-template
# store (templates/**/template.json). For each template it runs five checks:
#
#   (a) SCHEMA-FRESH — `wpdev elementor:validate --file` runs the schema-aware
#       Ajv validator over the committed widget-schemas.json SSOT (offline, no
#       site/DB). FAILS on any finding (type-mismatch / v3-shape / enum-violation
#       / malformed-responsive / node-shape / unknown-widget / missing-prop).
#       This is the drift gate — NOT an `elementor:normalize` no-op, which can't
#       see renamed/removed/new-required props.
#   (b) DTAG ALLOWLIST — every dynamic tag in a string value must be covered by
#       an allowlist regex from references/templates/placeholder-policy.md §1.
#   (c) DENYLIST — zero matches for the §3 denylist patterns (site TLD, email,
#       phone, real URL, curated proper nouns).
#   (d) META.YML — sibling meta.yml exists, parses, has all required keys, and
#       its dtags_used set equals (both directions) the allowlist dtags in JSON.
#   (e) INDEX ROW — templates/index.md has a row for the template id in the
#       table matching its meta.yml scope.
#
# The allowlist/denylist regexes are read live from placeholder-policy.md (the
# SSOT shared with the U2 sanitizer) — never hand-rolled here.
#
# Usage:
#   bash scripts/lint-templates.sh                              # scan all templates
#   bash scripts/lint-templates.sh templates/sections/<id>     # one template
#
# Exit 0 = every check passed on every scanned template; non-zero otherwise.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
. "$SCRIPT_DIR/lib.sh"

WPDEV_SOURCE_ROOT=$(find_wpdev_root || true)
if [ -n "$WPDEV_SOURCE_ROOT" ] && [ -x "$WPDEV_SOURCE_ROOT/wpdev" ]; then
  WPDEV_CMD="$WPDEV_SOURCE_ROOT/wpdev"
else
  WPDEV_CMD=$(command -v wpdev 2>/dev/null || true)
fi

cd "$SKILL_ROOT" || { printf "cannot cd to skill root\n"; exit 1; }

POLICY="references/templates/placeholder-policy.md"
INDEX="templates/index.md"

fails=0
pass()    { printf "  \033[32mPASS\033[0m  %s\n" "$1"; }
fail()    { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; fails=$((fails+1)); }
heading() { printf "\n\033[1m%s\033[0m\n" "$1"; }

command -v python3 >/dev/null 2>&1 || { printf "python3 is required\n"; exit 2; }
[ -n "$WPDEV_CMD" ] || { printf "wpdev is required (check (a) schema gate)\n"; exit 2; }
[ -f "$POLICY" ] || { printf "policy SSOT not found: %s\n" "$POLICY"; exit 2; }
[ -f "$INDEX" ]  || { printf "index not found: %s\n" "$INDEX"; exit 2; }

# --- (a) schema-fresh gate: real Ajv validator over the committed SSOT --------
# FAILS when the offline validator reports ANY finding. A clean template returns
# total:0; every category (type-mismatch, v3-shape, enum-violation, malformed
# responsive → v3-shape, node-shape, unknown-widget, missing-prop) is real drift.
check_schema() {
  tj="$1"
  out=$("$WPDEV_CMD" elementor:validate --file "$tj" --json 2>/dev/null)
  rc=$?
  if [ $rc -ne 0 ] || [ -z "$out" ]; then
    fail "(a) schema  — elementor:validate --file failed (rc=$rc) on $tj"
    return
  fi
  summary=$(printf '%s' "$out" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin); s=d["sites"][0]
except Exception as e:
    print(f"PARSE_ERR {e}"); sys.exit(0)
cats={k:v for k,v in s.get("by_category",{}).items() if v}
print(("FAIL "+str(s.get("total",0))+" "+", ".join(f"{k}={v}" for k,v in cats.items())) if s.get("total",0)>0 else "OK")
')
  case "$summary" in
    OK) pass "(a) schema  — 0 schema violations (SSOT-fresh)" ;;
    PARSE_ERR*) fail "(a) schema  — could not parse validator JSON: ${summary#PARSE_ERR }" ;;
    FAIL*) fail "(a) schema  — schema drift: ${summary#FAIL }" ;;
    *) fail "(a) schema  — unexpected validator output: $summary" ;;
  esac
}

# --- (b)(c)(d)(e): dtag/denylist/meta/index in one python pass ----------------
# Reads the allowlist/denylist regexes live from placeholder-policy.md §1/§3 and
# emits one `PASS <letter> <msg>` or `FAIL <letter> <msg>` line per check.
check_bcde() {
  tdir="$1"
  python3 - "$tdir" "$POLICY" "$INDEX" <<'PY'
import json, re, sys, os

tdir, policy_path, index_path = sys.argv[1], sys.argv[2], sys.argv[3]
tj = os.path.join(tdir, "template.json")
tm = os.path.join(tdir, "meta.yml")
tid = os.path.basename(os.path.normpath(tdir))

def emit(letter, ok, msg): print(f"{'PASS' if ok else 'FAIL'} {letter} {msg}")

# --- extract the regex SSOT (fenced ```regex blocks under §1 and §3) ----------
txt = open(policy_path, encoding="utf-8").read()
def section(a, b):
    i = txt.index(a); j = txt.index(b) if b else len(txt); return txt[i:j]
allow_src = re.findall(r"```regex\n(.*?)\n```", section("## 1. Universal-dtag allowlist", "## 2. The Lorem-Ipsum rule"), re.S)
deny_src  = re.findall(r"```regex\n(.*?)\n```", section("## 3. Proper-noun / real-data denylist", "## 4. Image placeholder rule"), re.S)
ALLOW = [re.compile(p) for p in allow_src]
DENY  = [(p, re.compile(p)) for p in deny_src]
WRAPPER = re.compile(r"@endtags\(\)|@tags\(\)")   # bare Voxel tag wrappers, not dtags
DTAG_TOKEN = re.compile(r"@[a-z_]+\(")            # a dynamic-tag opener
INNER = re.compile(r"@[a-z_]+\([^)]*\)")          # a bare dtag expr, e.g. @post(parent.title)

# --- load template.json (a single node, an array, or {elements:[…]}) ----------
try:
    tree = json.load(open(tj, encoding="utf-8"))
except Exception as e:
    for L in "abcd": emit(L, False, f"cannot read/parse template.json: {e}")
    sys.exit(0)

def all_strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from all_strings(v)
    elif isinstance(o, list):
        for v in o: yield from all_strings(v)

strings = list(all_strings(tree))

# --- (b) dtag allowlist + collect the covered inner-dtag set (for (d)) --------
def coverage(s):
    """None if an uncovered dtag remains; else the set of covered inner exprs."""
    stripped = s
    for rx in ALLOW: stripped = rx.sub("", stripped)
    stripped = WRAPPER.sub("", stripped)
    if DTAG_TOKEN.search(stripped):
        return None
    return set(INNER.findall(WRAPPER.sub(" ", s)))

found = set()
uncovered = []
for s in strings:
    if not DTAG_TOKEN.search(WRAPPER.sub("", s)):
        continue
    cov = coverage(s)
    if cov is None:
        rem = s
        for rx in ALLOW: rem = rx.sub("", rem)
        rem = WRAPPER.sub("", rem)
        uncovered.append((s, DTAG_TOKEN.search(rem).group() if DTAG_TOKEN.search(rem) else "?"))
    else:
        found |= cov
if uncovered:
    detail = "; ".join(f"{tok}… in {s!r}" for s, tok in uncovered[:5])
    emit("b", False, f"non-allowlist dtag(s): {detail}")
else:
    emit("b", True, f"all dtags allowlist-covered ({len(found)} distinct)")

# --- (c) denylist -------------------------------------------------------------
hits = []
for s in strings:
    for pat, rx in DENY:
        m = rx.search(s)
        if m:
            hits.append((pat, m.group(0), s))
if hits:
    detail = "; ".join(f"/{pat}/ matched {frag!r}" for pat, frag, _ in hits[:5])
    emit("c", False, f"denylist match(es): {detail}")
else:
    emit("c", True, "no denylist matches")

# --- (d) meta.yml consistency -------------------------------------------------
REQUIRED = ["id","scope","type","name","tags","widgets","dtags_used","requires_plugins","source_note","breakpoints"]
def load_yaml(path):
    try:
        import yaml
        return yaml.safe_load(open(path, encoding="utf-8")), None
    except ImportError:
        return _mini_yaml(path), None
    except Exception as e:
        return None, str(e)

def _mini_yaml(path):
    """Fallback parser for the flat meta.yml shape (scalars + simple inline/block lists)."""
    data, cur = {}, None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and cur is not None:
            data[cur].append(_scalar(line.strip()[2:]))
            continue
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            k = k.strip(); v = v.strip()
            if v == "":
                data[k] = []; cur = k
            elif v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                data[k] = [_scalar(x.strip()) for x in inner.split(",")] if inner else []
                cur = None
            else:
                data[k] = _scalar(v); cur = None
    return data

def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v

if not os.path.exists(tm):
    emit("d", False, "meta.yml missing")
else:
    meta, err = load_yaml(tm)
    if err is not None or not isinstance(meta, dict):
        emit("d", False, f"meta.yml does not parse as YAML mapping: {err}")
    else:
        missing = [k for k in REQUIRED if k not in meta or meta[k] in (None, "")]
        if meta.get("scope") == "global" and ("location" not in meta or meta.get("location") in (None, "")):
            missing.append("location")
        if missing:
            emit("d", False, f"meta.yml missing required key(s): {', '.join(missing)}")
        elif str(meta.get("id")) != tid:
            emit("d", False, f"meta.yml id '{meta.get('id')}' != folder '{tid}'")
        else:
            raw_used = meta.get("dtags_used") or []
            if not isinstance(raw_used, list):
                emit("d", False, "meta.yml dtags_used is not a list")
            else:
                meta_set = set()
                for e in raw_used:
                    meta_set |= set(INNER.findall(WRAPPER.sub(" ", str(e))))
                only_json = found - meta_set
                only_meta = meta_set - found
                if only_json or only_meta:
                    parts = []
                    if only_json: parts.append(f"in JSON not meta: {sorted(only_json)}")
                    if only_meta: parts.append(f"in meta not JSON: {sorted(only_meta)}")
                    emit("d", False, f"dtags_used mismatch — {'; '.join(parts)}")
                else:
                    emit("d", True, f"meta.yml valid; dtags_used matches JSON ({len(found)})")

    # --- (e) index row (needs the parsed scope) -------------------------------
    scope = meta.get("scope") if isinstance(meta, dict) else None
    scope_heading = {"global": "## Global", "section": "## Sections", "page": "## Pages"}.get(scope)
    if scope_heading is None:
        emit("e", False, f"cannot check index row — meta.yml scope '{scope}' invalid")
    else:
        idx = open(index_path, encoding="utf-8").read()
        start = idx.find(scope_heading)
        if start == -1:
            emit("e", False, f"index.md has no '{scope_heading}' table")
        else:
            nxt = idx.find("\n## ", start + 1)
            block = idx[start: nxt if nxt != -1 else len(idx)]
            row_re = re.compile(r"^\|\s*" + re.escape(tid) + r"\s*\|", re.M)
            if row_re.search(block):
                emit("e", True, f"index.md row present under {scope_heading}")
            else:
                emit("e", False, f"no index.md row for id '{tid}' under {scope_heading}")
PY
}

lint_one() {
  tdir="$1"
  tdir="${tdir%/}"
  tj="$tdir/template.json"
  heading "templates: ${tdir#templates/}"
  if [ ! -f "$tj" ]; then
    fail "(-) $tdir has no template.json"
    return
  fi
  check_schema "$tj"
  # Consume the python check lines; map PASS/FAIL to the shared counters.
  while IFS= read -r line; do
    verdict=${line%% *}
    rest=${line#* }
    if [ "$verdict" = "PASS" ]; then pass "($(printf '%s' "$rest" | cut -c1)) ${rest#* }"
    else fail "($(printf '%s' "$rest" | cut -c1)) ${rest#* }"; fi
  done < <(check_bcde "$tdir")
}

# --- target selection --------------------------------------------------------
targets=()
if [ "$#" -gt 0 ]; then
  for a in "$@"; do targets+=("$a"); done
else
  while IFS= read -r tj; do targets+=("$(dirname "$tj")"); done < <(find templates -type f -name template.json | sort)
fi

if [ "${#targets[@]}" -eq 0 ]; then
  printf "No templates found under templates/**/template.json\n"
  exit 0
fi

for t in "${targets[@]}"; do lint_one "$t"; done

printf "\n"
if [ "$fails" -eq 0 ]; then
  printf "\033[32mtemplate-lint: all checks passed (%d template(s)).\033[0m\n" "${#targets[@]}"
  exit 0
else
  printf "\033[31mtemplate-lint: %d check failure(s).\033[0m\n" "$fails"
  exit 1
fi
