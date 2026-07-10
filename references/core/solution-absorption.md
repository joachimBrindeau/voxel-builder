# Solution Absorption Contract

Use with `workflows/absorb-solutions.md` when promoting workspace learnings into
Voxel Builder.

## Dispositions

| Disposition | Meaning | Source state after completion |
|---|---|---|
| `absorbed` | Current reusable guidance is complete in one skill owner | Removed |
| `superseded` | Guidance is stale, contradictory, or replaced by a current mechanism | Removed |
| `relocated` | Record is a plan, audit, or runbook rather than reusable skill knowledge | Moved |
| `retained` | Reusable solution is outside Voxel Builder's scope | Kept |

## Freshness Evidence

At least one direct evidence item is required for every `absorbed` or `superseded`
entry. Prefer, in order:

1. Current source symbol/path and a focused test.
2. Generated SSOT artifact plus its drift command.
3. Current `wpdev` registry entry and `--help` output.
4. Runtime read-back/browser proof on a representative local site.

Dates, old commit IDs, screenshots, and historical success claims are context, not
freshness proof. Unimplemented proposals are never absorbed as available behavior.

## Coverage Test

A solution is fully absorbed only when all are true:

- Every current invariant, command, data shape, failure mode, and verification step has
  a home or is explicitly rejected as stale.
- Exactly one owner contains the normative rule; other files link to that owner.
- The owner is understandable without the incident document.
- Current commands and examples execute or pass their narrow validation.
- No active skill file depends on `docs/solutions/`.
- Workspace inbound links are updated before source removal.

## Registry

`solution-absorption.json` is the machine-readable retirement ledger. Each row contains:

```json
{
  "source": "docs/solutions/example.md",
  "disposition": "absorbed",
  "owners": ["references/ef/example.md"],
  "evidence": ["plugins/custom/example.php::current_symbol"],
  "reason": "Current invariant promoted; incident chronology omitted."
}
```

Retired source paths stay in the ledger permanently. This preserves provenance without
keeping stale operational instructions searchable as active solutions.

## Continuous Gate

Run from the skill root:

```bash
python3 scripts/audit-solution-absorption.py <wordpress-workspace>
```

The audit fails for unclassified solution files, invalid dispositions, missing owners or
destinations, retired sources that still exist, retained sources that disappeared, or
active skill dependencies on `docs/solutions/`.
