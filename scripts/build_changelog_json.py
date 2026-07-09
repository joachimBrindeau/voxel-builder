#!/usr/bin/env python3
"""Build a standardized JSON of every Voxel theme release from the canonical changelog.

Source of truth: the live changelog feed at getvoxel.io, which is a Voxel `voxel_release`
post feed (the same data behind https://getvoxel.io/changelog/). One request returns every
release from the newest down to ~0.9.x. This is more complete and more current than the
docs.getvoxel.io articles (which are a curated subset and lag behind point releases).

Output: a flat, queryable list of entries:

    { "version": "1.7.8", "date": "May 15, 2026", "type": "new"|"fixed",
      "description": "...", "source_url": "https://getvoxel.io/changelog/" }

Stdlib only (urllib + re). Re-run any time to pick up newer releases.

Usage:
    python3 build_changelog_json.py [-o OUTPUT.json] [--pretty] [--limit N] [--quiet]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html as _html
import json
import re
import sys
import urllib.request
from urllib.error import HTTPError, URLError

CHANGELOG_URL = "https://getvoxel.io/changelog/"
# Voxel `search_posts` AJAX for the `voxel_release` CPT — SSR-renders every release card.
FEED_URL = "https://getvoxel.io/?vx=1&action=search_posts&type=voxel_release&pg=1&limit=2000"
UA = "Mozilla/5.0 (compatible; voxel-changelog-skill/2.0; +wpdev)"

VERSION_H2_RE = re.compile(r"<h2[^>]*>\s*(\d+\.\d[\d.]*)\s*</h2>", re.I)


def fetch(url: str, retries: int = 3, timeout: int = 45) -> str:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:  # noqa: PERF203
            last = exc
            import time

            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def classify(description: str) -> str:
    """'fixed' for bug fixes, else 'new'. Tolerates a leading 'Category:' label."""
    d = description.strip()
    if re.match(r"fix(ed|es)?\b|fix\b", d, re.I):
        return "fixed"
    m = re.match(r"[^:]{1,40}:\s*(.+)", d)
    if m and re.match(r"fix(ed|es)?\b|fix\b", m.group(1), re.I):
        return "fixed"
    return "new"


def extract_entries(body_region: str) -> list[str]:
    """Pull individual changelog entries from one release's vx-post-body region.

    Two historical formats:
      * newer: <ul><li>entry</li>...</ul>          → each <li> is one atomic entry
      * older: <p>- entry<br />- entry ...</p>      → split on <br> and en/em-dashes
    """
    lis = re.findall(r"<li[^>]*>(.*?)</li>", body_region, re.S | re.I)
    if lis:
        out = []
        for li in lis:
            t = strip_tags(li)
            if t and "{{" not in t:
                out.append(t)
        return out

    # older <p>+<br>+en-dash format: process each <p>...</p> block in isolation so no
    # surrounding markup can leak. Convert <br> to newline, then split on newline/en-dash.
    out = []
    for para in re.findall(r"<p[^>]*>(.*?)</p>", body_region, re.S | re.I):
        text = re.sub(r"<br\s*/?>", "\n", para, flags=re.I)
        text = _html.unescape(re.sub(r"<[^>]+>", "", text))
        for raw in re.split(r"[\n–—]+", text):
            frag = re.sub(r"\s+", " ", raw).strip().lstrip("•*-–— ").strip()
            if frag and "{{" not in frag:
                out.append(frag)
    return out


def parse_feed(html: str, limit: int | None = None) -> list[dict]:
    """Parse the rendered voxel_release feed into ordered releases (newest first)."""
    # Split the document at each release version heading; the text-editor body of each
    # release sits between its <h2> and the next. The trailing ts-preview card render is
    # excluded by anchoring extraction to the vx-post-body block and cutting at ts-preview.
    parts = re.split(r"(<h2[^>]*>\s*\d+\.\d[\d.]*\s*</h2>)", html)
    releases: list[dict] = []
    seen: set[str] = set()
    for i in range(1, len(parts), 2):
        version = strip_tags(parts[i])
        if not version or version in seen:
            continue
        body = parts[i + 1] if i + 1 < len(parts) else ""
        anchor = re.search(r"vx-post-body", body)
        if not anchor:
            continue  # a version heading with no body = a preview-card duplicate; skip
        region = body[anchor.end():].split("ts-preview")[0]
        date_m = re.search(r"<span[^>]*>([^<]*\d{4})</span>", body[: anchor.start()])
        date = strip_tags(date_m.group(1)) if date_m else ""
        entries = extract_entries(region)
        if not entries:
            continue
        seen.add(version)
        releases.append({"version": version, "date": date, "entries": entries})
        if limit and len(releases) >= limit:
            break
    return releases


def version_sort_key(v: str):
    nums = [int(n) for n in re.findall(r"\d+", v)]
    nums += [0] * (5 - len(nums))
    return tuple(nums[:5])


def build(limit: int | None = None, quiet: bool = False) -> dict:
    def log(*a):
        if not quiet:
            print(*a, file=sys.stderr)

    html = fetch(FEED_URL)
    releases = parse_feed(html, limit=limit)
    log(f"parsed {len(releases)} releases")

    entries: list[dict] = []
    for rel in releases:
        for desc in rel["entries"]:
            entries.append(
                {
                    "version": rel["version"],
                    "date": rel["date"],
                    "type": classify(desc),
                    "description": desc,
                    "source_url": CHANGELOG_URL,
                }
            )
        log(f"  {len(rel['entries']):4d}  {rel['version']:<12} ({rel['date']})")

    # de-duplicate identical (version, type, description)
    seen = set()
    deduped = []
    for e in entries:
        key = (e["version"], e["type"], e["description"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    deduped.sort(key=lambda e: (version_sort_key(e["version"]), e["type"]), reverse=True)

    versions = []
    for rel in sorted(releases, key=lambda r: version_sort_key(r["version"]), reverse=True):
        versions.append({"version": rel["version"], "date": rel["date"]})

    return {
        "source": "getvoxel.io",
        "source_url": CHANGELOG_URL,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "version_count": len(releases),
        "entry_count": len(deduped),
        "type_counts": {
            "new": sum(1 for e in deduped if e["type"] == "new"),
            "fixed": sum(1 for e in deduped if e["type"] == "fixed"),
        },
        "versions": versions,
        "entries": deduped,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output", help="write JSON to this path (default: stdout)")
    ap.add_argument("--pretty", action="store_true", help="indent the JSON output")
    ap.add_argument("--limit", type=int, help="only process the first N releases (debug)")
    ap.add_argument("--quiet", action="store_true", help="suppress progress on stderr")
    args = ap.parse_args()

    data = build(limit=args.limit, quiet=args.quiet)
    text = json.dumps(data, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        if not args.quiet:
            print(f"wrote {data['entry_count']} entries / {data['version_count']} versions → {args.output}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
