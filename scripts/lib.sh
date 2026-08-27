#!/bin/sh
#
# lib.sh — shared runtime helpers for bundled voxel-builder scripts.
# Sourced, never executed directly.

# Resolve the wpdev source checkout without assuming the caller's CWD. Callers
# may override discovery with WPDEV_ROOT when wpdev is installed out of tree.
find_wpdev_root() {
  # An explicit WPDEV_ROOT is authoritative. It lets CI and external skill
  # checkouts validate against the workspace whose generated schemas they
  # document, without depending on a possibly stale global `wpdev` shim.
  if [ -n "${WPDEV_ROOT:-}" ] && [ -x "$WPDEV_ROOT/wpdev" ]; then
    printf '%s\n' "$WPDEV_ROOT"
    return 0
  fi

  if [ -n "${WPDEV_SOURCE_ROOT:-}" ] && [ -f "$WPDEV_SOURCE_ROOT/cli/src/index.ts" ]; then
    printf '%s\n' "$WPDEV_SOURCE_ROOT"
    return 0
  fi

  if [ -f "$(pwd)/cli/src/index.ts" ]; then
    pwd
    return 0
  fi

  if command -v git >/dev/null 2>&1; then
    candidate=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [ -n "$candidate" ] && [ -f "$candidate/cli/src/index.ts" ]; then
      printf "%s" "$candidate"
      return 0
    fi
  fi

  if command -v wpdev >/dev/null 2>&1; then
    candidate=$(CDPATH= cd -- "$(dirname -- "$(command -v wpdev)")" && pwd)
    if [ -f "$candidate/cli/src/index.ts" ]; then
      printf "%s" "$candidate"
      return 0
    fi
  fi

  return 1
}

# --- Warning output ----------------------------------------------------------
warn_count=0
warn()    { printf "  \033[33mWARN\033[0m  %s\n" "$1"; warn_count=$((warn_count + 1)); }
