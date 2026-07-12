# Named Specialist Briefs

These briefs define leaf semantics. `references/core/parallel-dispatch.md` owns batching,
waves, retry limits, aggregation, and centralized writes. Do not restate those mechanics
inside a role brief.

## Dispatch Rule

1. Select the role whose ownership matches the leaf type.
2. Partition 5-10 homogeneous leaves into a batch; use smaller batches only when the
   leaves are individually large or there are fewer than five.
3. Give every leaf a stable `scope_id` and require one leaf envelope per scope.
4. Run at most the host concurrency cap of batches in a wave (default four).
5. Reject cross-role, cross-mode, or cross-scope output before aggregation.

## MECE Role Index

| Brief | Exclusive responsibility | Mode | Batch unit |
|---|---|---|---|
| [`voxel-page-auditor`](voxel-page-auditor.md) | Page-global context, tier inventory, and report framing | Read-only | 1-4 pages/templates |
| [`voxel-widget-builder`](voxel-widget-builder.md) | Widget settings/DOM analysis or scoped widget JSON | Read-only or build, never mixed | 5-10 widgets |
| [`voxel-elementor-fixer`](voxel-elementor-fixer.md) | Approved finding-to-repair material and repair verification plan | Build | 5-10 non-overlapping findings |
| [`voxel-schema-detective`](voxel-schema-detective.md) | Source-backed widget/field/schema questions | Read-only | 5-10 schema questions |
| [`voxel-plan-reviewer`](voxel-plan-reviewer.md) | Criterion-scoped adversarial findings against a Plan Document | Plan review | 5-10 criteria |
| [`voxel-layout-architect`](voxel-layout-architect.md) | Section Layout map blocks | Build material | 5-10 sections |
| [`voxel-heading-curator`](voxel-heading-curator.md) | One site/plan-level production phrasing palette | Read-only | 1-4 plans |
| [`voxel-curator-agent`](voxel-curator-agent.md) | Entity, relation, taxonomy, profile, and user investigation | Read-only | 5-10 entities |
| [`voxel-faq-author`](voxel-faq-author.md) | Source-supported visible FAQ rows | Read-only authoring | 5-10 content items |
| [`voxel-content-author`](voxel-content-author.md) | Source-supported CPT field content (definition/hook/excerpt/sources/body) | Build (candidate values) or review (verdicts) | 5-10 records |

## Mode Boundaries

- **Read-only:** findings/evidence only. No patches, write commands, or mutation claims.
- **Build material:** scoped JSON/patch material only. The orchestrator performs the
  authoritative write after validating all leaves.
- **Plan review:** criterion findings only. The orchestrator reconciles and edits the plan.
- A role that supports two modes receives exactly one mode per batch.

## Shared Return Envelope

Every role returns an array with one object per scope:

```json
{
  "scope_id": "entity:company:42",
  "mode": "read-only",
  "status": "pass|finding|ready|blocked",
  "evidence": ["wpdev command or source path"],
  "output": {},
  "open_questions": []
}
```

The brief defines `output`. The common envelope makes aggregation deterministic and keeps
partial failures explicit.

## Tool Boundaries

| Tool class | Use |
|---|---|
| Glob | Locate candidate files by pattern |
| Grep | Search combined patterns across the selected scope |
| Read | Inspect specific files or supplied artifacts |
| Bash | Run `wpdev`, schema validators, browser commands, or other real programs only |
| Write | Only roles producing build material files; never direct WordPress writes |

Prefer dedicated file tools over shell file operations. Read-only roles must not declare
`Write`. A role with `Bash` must name the executable commands it is allowed to run.

## Shared Rejection Rules

- No remembered EF/Voxel shapes: read committed SSOT or a current production dump.
- No whole-page catch-all worker: page judgment stays with the orchestrator.
- No overlapping mutation paths across leaves or batches.
- No worker-per-item fan-out: atomic outputs are returned from bounded batches.
- No summary-only batch return: every input `scope_id` must have its own envelope.
- No unlimited retries: after two re-dispatches, return `blocked` with evidence.
