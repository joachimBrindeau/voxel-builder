#!/bin/sh
#
# lib.sh — shared helpers for the voxel-builder DX scripts (lint / changelog /
# release / verify-install). Sourced, never executed directly.
#
# SSOT for: plugin-root resolution, the version reader, conventional-commit
# parsing, and the pass/fail/warn output plumbing. Every script sources this so
# the output format and the "where is plugin.json / what version are we"
# answers live in exactly one place.

# --- Plugin root -------------------------------------------------------------
# Resolve the plugin root from this lib's own location (scripts/ -> parent).
# Works regardless of caller CWD or how the plugin was installed.
_lib_dir() {
  # POSIX-portable dirname of the sourced file.
  d=$(CDPATH= cd -- "$(dirname -- "$1")" && pwd)
  printf "%s" "$d"
}
PLUGIN_ROOT=$(_lib_dir "${0}")
case "$PLUGIN_ROOT" in
  */scripts) PLUGIN_ROOT=$(dirname "$PLUGIN_ROOT") ;;
esac
# Fallback when $0 isn't the script (e.g. sourced interactively): walk up for plugin.json.
if [ ! -f "$PLUGIN_ROOT/.claude-plugin/plugin.json" ]; then
  d=$(pwd)
  while [ "$d" != "/" ]; do
    if [ -f "$d/.claude-plugin/plugin.json" ]; then PLUGIN_ROOT=$d; break; fi
    d=$(dirname "$d")
  done
fi
export PLUGIN_ROOT
MANIFEST="$PLUGIN_ROOT/.claude-plugin/plugin.json"
CHANGELOG="$PLUGIN_ROOT/CHANGELOG.md"

# --- Output plumbing (single source) ----------------------------------------
fail_count=0
warn_count=0
pass()    { printf "  \033[32mPASS\033[0m  %s\n" "$1"; }
fail()    { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; fail_count=$((fail_count + 1)); }
warn()    { printf "  \033[33mWARN\033[0m  %s\n" "$1"; warn_count=$((warn_count + 1)); }
info()    { printf "        %s\n" "$1"; }
heading() { printf "\n\033[1m%s\033[0m\n" "$1"; }

# --- Version reader (SSOT: plugin.json) -------------------------------------
plugin_version() {
  if command -v jq >/dev/null 2>&1; then
    jq -r '.version // ""' "$MANIFEST"
  else
    # jq-less fallback: grep the version line.
    grep -oE '"version"[[:space:]]*:[[:space:]]*"[^"]+"' "$MANIFEST" | head -1 | sed -E 's/.*"([^"]+)"$/\1/'
  fi
}

plugin_name() {
  if command -v jq >/dev/null 2>&1; then
    jq -r '.name // ""' "$MANIFEST"
  else
    grep -oE '"name"[[:space:]]*:[[:space:]]*"[^"]+"' "$MANIFEST" | head -1 | sed -E 's/.*"([^"]+)"$/\1/'
  fi
}

# Top version header in CHANGELOG (e.g. "0.5.1" from "## [0.5.1] - 2026-05-29").
changelog_top_version() {
  grep -m1 -oE '^## \[[0-9]+\.[0-9]+\.[0-9]+\]' "$CHANGELOG" 2>/dev/null \
    | sed -E 's/^## \[([0-9.]+)\]/\1/'
}

# --- Conventional-commit helpers --------------------------------------------
# Map a conventional-commit type to a Keep-a-Changelog section.
cc_section() {
  case "$1" in
    feat)            printf "Added" ;;
    fix)             printf "Fixed" ;;
    refactor|perf|chore|docs|style|build|ci|test) printf "Changed" ;;
    *)               printf "Changed" ;;
  esac
}
