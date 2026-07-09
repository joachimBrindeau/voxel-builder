#!/usr/bin/env python3
"""
Ad-hoc verification for Lean SEO markdown author excerpt truncation.
Run from repo root after editing plugins/custom/lean-seo/modules/llms/inc/markdown.php.
This is not a full suite; it proves the specific no-truncation behavior.
"""
from pathlib import Path

path = Path("plugins/custom/lean-seo/modules/llms/inc/markdown.php")
code = path.read_text()
errors = []

if "$words = preg_split" in code:
    errors.append("author excerpt word-splitting truncation still present")
if "array_slice( $words, 0, 28 )" in code:
    errors.append("author excerpt 28-word slice still present")
if "return $excerpt;" not in code:
    errors.append("author excerpt no longer returns full excerpt")
if "return ! preg_match( '/(?:\\.\\.\\.|…)$/u', $excerpt );" not in code:
    errors.append("cached ellipsis author excerpt not treated stale")
if "strlen( trim( $matches[1] ) ) <= 240" in code:
    errors.append("old <=240 compact-cache check still present")

if errors:
    print("FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("PASS: markdown author excerpts are not truncated; cached ellipsis excerpts regenerate")
