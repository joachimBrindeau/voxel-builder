#!/usr/bin/env bash
# action-spec.sh — SSOT lookup for EF card/navbar action types.
#
# Prints an action type's required cells + each cell's field spec straight from
# the codegen catalog (cli/src/generated/ef-catalogs.json — extracted from
# ef_action_types() + ef_action_field_specs() by `wpdev elementor:codegen`).
# The card-actions workflow uses this to collect EXACTLY the cells the resolver
# consumes for a chosen action — no guessing, no drift from the PHP registry.
#
# Usage:
#   action-spec.sh                 # list every action id + label + required cells
#   action-spec.sh action_link     # one action: required cells + field specs
#   EF_CATALOGS=/abs/ef-catalogs.json action-spec.sh call   # override catalog path
#
# Resolves the catalog relative to the current wpdev repo (the skill always runs
# inside it); honors $EF_CATALOGS for out-of-tree invocations.
set -euo pipefail

catalogs="${EF_CATALOGS:-}"
if [[ -z "$catalogs" ]]; then
  if [[ -f cli/src/generated/ef-catalogs.json ]]; then
    catalogs="cli/src/generated/ef-catalogs.json"
  elif root="$(git rev-parse --show-toplevel 2>/dev/null)" && [[ -f "$root/cli/src/generated/ef-catalogs.json" ]]; then
    catalogs="$root/cli/src/generated/ef-catalogs.json"
  fi
fi

[[ -n "$catalogs" && -f "$catalogs" ]] || { printf 'ef-catalogs.json not found — run `wpdev elementor:codegen`, or set $EF_CATALOGS.\n' >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf 'jq is required.\n' >&2; exit 1; }

id="${1:-}"

if [[ -z "$id" ]]; then
  printf 'Action catalog (%s):\n\n' "$catalogs"
  jq -r '.action_types[]
    | "\(.id // "''")\t\(.label)\t[\((.required_fields // []) | join(", "))]"' "$catalogs" \
    | column -t -s $'\t'
  exit 0
fi

jq -r --arg id "$id" '
  .action_field_specs as $specs
  | (.action_types[] | select(.id == $id)) as $a
  | if $a == null then
      "unknown action id: \($id)  — run with no args to list valid ids"
    else
      "action: \($a.id)  (\($a.label))",
      ( "required cells: " + (if ((($a.required_fields)//[]) | length) > 0 then (($a.required_fields)|join(", ")) else "none (self-contained / Voxel-runtime)" end) ),
      "",
      ( (($a.required_fields)//[])[] as $k
        | ($specs[] | select(.key == $k)) as $f
        | "  - \($k): kind=\($f.kind)  | e.g. \($f.placeholder // "-")\n    \($f.description)"
      )
    end
' "$catalogs"
