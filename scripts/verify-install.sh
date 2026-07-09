#!/bin/sh
#
# verify-install.sh — confirm the voxel-builder skill's runtime prerequisites are present.
#
# Exit 0: all required prerequisites OK (jq is optional, only warns).
# Exit 1: at least one required prerequisite is missing.

set -u
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/lib.sh"

# verify-install uses its own OK/MISSING verbs (runtime-prereq semantics), but
# shares warn() + the counter discipline from lib.sh. Runtime checks are a
# distinct concern from lint.sh's authoring checks — both share lib.sh plumbing.
ok()      { printf "  OK      %s\n" "$1"; }
missing() { printf "  MISSING %s\n" "$1"; missing_count=$((missing_count + 1)); }

missing_count=0

printf "voxel-builder skill — install verification\n\n"

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

# --- Required: at least one local site --------------------------------------
if command -v wpdev >/dev/null 2>&1; then
  if wpdev list 2>/dev/null | grep -qE "[a-z0-9-]+"; then
    ok "at least one local site found via 'wpdev list'"
  else
    missing "no local sites — \`wpdev list\` returned nothing"
  fi
fi

# --- Recommended: agent-browser CLI -----------------------------------------
# Drives all browser verification (Phase 6, audit Stream D, migration Phase 5)
# and the migration-preservation production baseline. There is NO mcp browser
# server — the plugin invokes this CLI via Bash. See workflows/browser-verify.md.
if command -v agent-browser >/dev/null 2>&1; then
  ok "agent-browser on PATH ($(agent-browser --version 2>/dev/null | head -n1))"
else
  warn "agent-browser not on PATH — browser verification can't run; install with \`npm i -g agent-browser && agent-browser install\`, then \`agent-browser doctor\`. See workflows/browser-verify.md"
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
