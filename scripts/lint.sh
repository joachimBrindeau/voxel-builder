#!/usr/bin/env bash
# Portable lint for the voxel-builder skill (cross-tool ~/.agents/skills form).
#
# Keeps the host-independent checks that matter for a portable skill:
#   1. no host-path/slash-command coupling leaked back in
#      (${CLAUDE_PLUGIN_ROOT}, bare /voxel-builder: slash refs)
#   2. SKILL.md stays lean (< 500 lines)
#   3. every relative link + #anchor resolves (lychee, when available)
#   4. no hardcoded absolute paths
#
# Dropped from the plugin-era lint: plugin.json validation, version-drift stamps,
# component-count-vs-README, and ${CLAUDE_PLUGIN_ROOT} resolution — none apply to a
# portable skill.
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SKILL_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$SKILL_ROOT" || { printf "cannot cd to skill root\n"; exit 1; }

fails=0
pass()    { printf "  \033[32mPASS\033[0m  %s\n" "$1"; }
fail()    { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; fails=$((fails+1)); }
heading() { printf "\n\033[1m%s\033[0m\n" "$1"; }

# --- 1. No Claude-Code coupling ---------------------------------------------
heading "Portability (no Claude-Code coupling)"

leaks=$(grep -rl 'CLAUDE_PLUGIN_ROOT' --include='*.md' . 2>/dev/null | grep -v CHANGELOG.md)
if [ -z "$leaks" ]; then pass "no \${CLAUDE_PLUGIN_ROOT} in active docs"
else fail "\${CLAUDE_PLUGIN_ROOT} leaked into: $(echo "$leaks" | tr '\n' ' ')"; fi

slash=$(grep -rl '/voxel-builder:' --include='*.md' . 2>/dev/null | grep -v CHANGELOG.md)
if [ -z "$slash" ]; then pass "no bare /voxel-builder: slash-command refs in active docs"
else fail "slash-command refs still in: $(echo "$slash" | tr '\n' ' ')"; fi

# --- 2. SKILL.md lean --------------------------------------------------------
heading "Skill size"
n=$(wc -l < SKILL.md | tr -d ' ')
if [ "$n" -lt 500 ]; then pass "SKILL.md is $n lines (<500)"; else fail "SKILL.md is $n lines (must be <500)"; fi

# --- 3. No hardcoded absolute paths -----------------------------------------
heading "No hardcoded absolute paths"
abs=$(grep -rnE '/(Users|home)/[a-zA-Z]' --include='*.md' . 2>/dev/null | grep -v CHANGELOG.md)
if [ -z "$abs" ]; then pass "no hardcoded /Users or /home paths"
else fail "hardcoded absolute path(s):"; printf "%s\n" "$abs" | sed 's/^/        /'; fi

# --- 4. Workflow-skill architecture -----------------------------------------
heading "Workflow structure"
if python3 scripts/lint-workflow-structure.py; then :; else fail "workflow structure invalid"; fi

# --- 5. Field-metadata contract ---------------------------------------------
heading "Field-metadata contract"
if python3 scripts/check-field-metadata-contract.py && python3 scripts/test-field-metadata-run-validator.py; then :; else fail "field-metadata policy or run-artifact contract invalid"; fi

# --- 6. wpdev coverage drift -------------------------------------------------
heading "wpdev coverage drift"
if python3 scripts/check-wpdev-coverage.py; then :; else fail "wpdev-coverage.md drifted from cli/src/index.ts"; fi

# --- 7. Section-template drift gate -----------------------------------------
heading "Section-template lint (schema/dtag/denylist/meta/index)"
if [ -f templates/index.md ] && find templates -type f -name template.json | grep -q .; then
  tl_out=$(bash scripts/lint-templates.sh 2>&1)
  tl_rc=$?
  if [ "$tl_rc" -eq 0 ]; then
    pass "lint-templates.sh: $(printf '%s' "$tl_out" | grep -oE 'all checks passed \([0-9]+ template\(s\)\)' | head -1)"
  else
    fail "lint-templates.sh reported failures:"
    printf '%s\n' "$tl_out" | grep -E 'FAIL|failure' | sed 's/^/        /'
  fi
else
  printf "  \033[33mSKIP\033[0m  no templates to lint\n"
fi

# --- 8. Deep link + anchor check (lychee, optional) -------------------------
heading "Deep link check (lychee)"
if command -v lychee >/dev/null 2>&1; then
  md_files=$(find . -name '*.md' -not -path './node_modules/*')
  if lychee --offline --include-fragments --no-progress \
       --exclude-path CHANGELOG.md \
       $md_files >/tmp/.vb-lychee.$$ 2>&1; then
    pass "lychee: all local links + #anchors resolve ($(grep -oE '[0-9]+ OK' /tmp/.vb-lychee.$$ | head -1))"
  else
    fail "lychee: broken local link(s)/anchor(s):"
    grep -E 'ERROR|Cannot find' /tmp/.vb-lychee.$$ | head -20 | sed 's/^/        /'
  fi
  rm -f /tmp/.vb-lychee.$$
else
  printf "  \033[33mSKIP\033[0m  lychee not installed (brew install lychee) — link check skipped\n"
fi

printf "\n"
if [ "$fails" -eq 0 ]; then printf "\033[32mAll portable-lint checks passed.\033[0m\n"; exit 0
else printf "\033[31m%d failure(s).\033[0m\n" "$fails"; exit 1; fi
