#!/bin/sh
#
# verify-install.sh — confirm the voxel-builder skill's runtime prerequisites are present.
#
# Usage: verify-install.sh <site>
# Exit 0: all required prerequisites OK (jq is optional, only warns).
# Exit 1: at least one required prerequisite is missing.

set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/lib.sh"

# verify-install uses its own OK/MISSING verbs and shares warning output plus
# wpdev source discovery with action-spec.sh through lib.sh.
ok()      { printf "  OK      %s\n" "$1"; }
missing() { printf "  MISSING %s\n" "$1"; missing_count=$((missing_count + 1)); }

missing_count=0
site=${1:-}

printf "voxel-builder skill — install verification\n\n"

if [ -z "$site" ]; then
  missing "site argument required (usage: ./scripts/verify-install.sh <site>)"
fi

# --- Required: wpdev CLI -----------------------------------------------------
if command -v wpdev >/dev/null 2>&1; then
  ok "wpdev on PATH"
  if wpdev --version >/dev/null 2>&1; then
    ok "wpdev runs ($(wpdev --version 2>/dev/null | head -n1))"
  else
    missing "wpdev fails to run (\`wpdev --version\` errored)"
  fi
else
  missing "wpdev not on PATH"
fi

# --- Required: target site and runtime components ---------------------------
if command -v wpdev >/dev/null 2>&1 && [ -n "$site" ]; then
  if wpdev list 2>/dev/null | awk 'NR > 2 { print $1 }' | grep -qx "$site"; then
    ok "target site '$site' found via 'wpdev list'"
  else
    missing "target site '$site' not found via 'wpdev list'"
  fi

  if wpdev wp "$site" theme is-active voxel >/dev/null 2>&1; then
    ok "Voxel theme active on '$site'"
  else
    missing "Voxel theme not active on '$site'"
  fi

  for plugin in lean-seo elementor-framework; do
    if wpdev wp "$site" plugin is-active "$plugin" >/dev/null 2>&1; then
      ok "$plugin plugin active on '$site'"
    else
      missing "$plugin plugin not active on '$site'"
    fi
  done
fi

# --- Required: committed EF schema/catalog assets ---------------------------
if wpdev_root=$(find_wpdev_root); then
  for asset in widget-schemas.json ef-catalogs.json; do
    if [ -f "$wpdev_root/cli/src/generated/$asset" ]; then
      ok "committed EF asset found: cli/src/generated/$asset"
    else
      missing "missing cli/src/generated/$asset — run \`wpdev elementor:codegen\`"
    fi
  done
else
  missing "wpdev source checkout not found — set WPDEV_ROOT"
fi

# --- Recommended: agent-browser CLI -----------------------------------------
# Drives all browser verification (Phase 6, audit Stream D, migration Phase 5)
# and the migration-preservation production baseline. There is NO mcp browser
# server — the skill invokes this CLI through the shell. See references/verification/browser.md.
if command -v agent-browser >/dev/null 2>&1; then
  ok "agent-browser on PATH ($(agent-browser --version 2>/dev/null | head -n1))"
else
  warn "agent-browser not on PATH — browser verification can't run; install with \`npm i -g agent-browser && agent-browser install\`, then \`agent-browser doctor\`. See references/verification/browser.md"
fi

# --- Optional: jq -----------------------------------------------------------
if command -v jq >/dev/null 2>&1; then
  ok "jq on PATH (used by examples/)"
else
  warn "jq not on PATH — fixture refresh workflow needs it; see examples/README.md"
fi

printf "\n"
if [ "$missing_count" -eq 0 ]; then
  printf "All required prerequisites OK.\n"
  exit 0
else
  printf "%d required prerequisite(s) missing.\n" "$missing_count"
  exit 1
fi
