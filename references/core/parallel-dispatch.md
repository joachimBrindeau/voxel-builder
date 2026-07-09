# Parallel-atomic subagent dispatch

The voxel-builder skill's audit, build, and fix pipelines all rely on the same dispatch contract: **the main agent is an orchestrator; specialist work fans out to parallel subagents whose scopes are atomic; returned evidence/JSON is aggregated by the orchestrator**. This file is the canonical reference. Every subagent prompt cites it.

> **Portability note.** This document describes the contract in the vocabulary of one host agent (a "Workflow" runner with `parallel()`/`pipeline()`/`agent()` primitives, and an inline "Agent"/"Task" dispatch). These are **capabilities, not product names**. Map them to whatever your host provides:
> - "Workflow `parallel()` / `pipeline()`" → any deterministic parallel-step runner (a background workflow engine, a job queue, or a scripted loop).
> - "inline single-message Agent/Task dispatch" → your host's subagent facility, or — if it has none — reading each subagent brief and doing its scoped work sequentially yourself.
> - "the Workflow tool", "`agent()`", "opted into multi-agent orchestration" → the same idea in your host's terms.
> The **atomic-scope rule** (one widget / one section / one criterion per subagent) and the **judgment-gates-stay-with-the-orchestrator** rule are host-independent and always apply.

Two dispatch mechanisms express that contract; pick per session:

- **Workflow-tool fan-out (preferred when the user has opted into multi-agent orchestration).** Each deterministic parallel fan-out runs as a `parallel()` / `pipeline()` Workflow step that backgrounds, returns schema-validated objects, and resumes unchanged legs from cache. Use this when the user opts in (ultracode on, the keyword `ultracode`, or an explicit "use a workflow" request).
- **Inline single-message Agent dispatch (always-available fallback).** Send all subagents in one message; aggregate the batch return in the orchestrator. Use this when Workflow isn't opted into, for small in-turn fan-outs, or when a result is needed immediately in the same reasoning step.

Both mechanisms obey the same atomic-scope rule below — one widget / one section / one criterion per subagent. Workflow's `parallel()` IS the single-message fan-out, just deterministic and backgroundable. Never call Workflow unconditionally; the inline path stays valid at all times.

## Orchestrator duties

The orchestrator is not a leaf worker. It:

1. Selects the routed workflow and reads only the shared references needed for that route.
2. Produces the fan-out plan: which named subagent, which mode, which atomic scope,
   and which evidence/return schema each dispatch owns.
3. Dispatches all same-phase leaf scopes concurrently where possible.
4. Rejects returns that cross scope, mix modes, omit evidence, or propose writes from
   a read-only brief.
5. Owns judgment between fan-outs: rebuild-vs-revise, §2f reconciliation, §2g gate,
   verify-to-repair convergence, and user escalation.
6. Writes once after build/fix fan-out returns have been validated and assembled.

If the host lacks a real subagent runtime, the orchestrator still follows this
contract by reading the matching brief and executing one atomic scope at a time as
a degraded inline fallback. It must record `subagent-runtime-unavailable`; the
fallback is not permission to do a whole-page build or audit as one blob.

## Why atomic-scope parallel dispatch

`_elementor_data` is a single nested JSON blob. Two subagents writing to the same blob in parallel race the file. Two subagents reasoning about overlapping subtrees produce conflicting findings. The atomic-scope rule eliminates both classes of failure: each subagent's input is a leaf (one widget, one section, one global concern), each subagent's output is independent, and the orchestrator owns assembly.

Atomic scope also unlocks two tier-orthogonal concerns:

- **Wall-time savings.** Eight widgets verified one-after-another costs 8× the time of a single-message fan-out.
- **Mode discipline.** Read-only investigation mode is only safe under atomic scope — a subagent can't accidentally couple findings across widgets it doesn't own.

## Three dispatch modes

| Mode | Subagent output | When to use |
|---|---|---|
| **Build** | Widget JSON (or section JSON) the orchestrator inserts into the tree | User said "build", "create", "scaffold", or "fix this widget" |
| **Read-only investigation** | Findings only — never a patch, never a write | User said "audit", "review", "investigate", "what's wrong", "find improvements" |
| **Adversarial Plan Document review** | Per-criterion findings array — never a patch, never a Plan Document edit | Phase 2e of the build workflow (`workflows/build.md`) or the migration workflow (`workflows/migrate.md`) — the relevant adversarial reviewers, one concern each, dispatched in parallel; also dispatched from `voxel-elementor-fixer` when a fix adds/restructures sections |

The eight named subagents map to these modes:

| Subagent | Mode | Fan-out role |
|---|---|---|
| `voxel-widget-builder` | Build or read-only (binary per dispatch) | Leaf — builder dispatches in build; auditor dispatches in read-only |
| `voxel-page-auditor` | Read-only | Orchestrator — dispatches `voxel-widget-builder` (read-only) |
| `voxel-elementor-fixer` | Build | Orchestrator — dispatches `voxel-widget-builder` (build); re-dispatches `voxel-plan-reviewer` + `voxel-layout-architect` + `voxel-heading-curator` when a fix adds/restructures sections |
| `voxel-schema-detective` | Read-only | Leaf — no fan-out |
| `voxel-plan-reviewer` | Adversarial Plan Document review (read-only — tool list excludes `Write`) | Leaf — one criterion per dispatch (`coverage`, `density`, `hierarchy`, `data-wiring`, `pattern-reuse`, `relations`, `ssot-integrity`, `migration-preservation`); orchestrator fans out the relevant reviewers, one concern each, in a single message. Default to the full panel (`migration-preservation` added when migrating); narrow it only with a stated reason |
| `voxel-layout-architect` | Build (Layout map block) — tool list excludes `Write`; orchestrator splices the returned block | Leaf — one per §2c-selected section, all dispatched in a single message at §2c→§2d transition |
| `voxel-heading-curator` | Read-only — extracts production heading-phrasing palette | Leaf — ONE dispatch per plan at §2c→§2d transition (not per section) |
| `voxel-curator-agent` | Read-only — Voxel entity-curation investigation (CPT/taxonomy/profile/user/merge/delete) via `wpdev voxel:*` | Leaf — one entity per dispatch; see the curation workflow [`../../workflows/curation.md`](../../workflows/curation.md) |

See [`AGENTS.md`](../subagents/README.md) for the per-agent contracts and dispatch graph.

## Expressing a fan-out through the Workflow tool

When the user has opted into multi-agent orchestration, express each deterministic parallel fan-out as a Workflow step instead of an inline single-message dispatch. The concrete wins over inline dispatch:

- **Background + non-blocking.** The panel / build / verify fan-out runs in the background; the orchestrator is notified on completion (watch `/workflows`).
- **Structured output.** `agent(prompt, {schema})` forces each subagent to return a schema-validated object — a findings array, a widget-JSON node, or a pass/fail verdict — which removes the hand-normalizing of free-text returns that aggregation otherwise requires.
- **Resumability.** `resumeFromRunId` returns cached results for unchanged `agent()` calls (content-addressed); a re-run after a tweak only re-executes the changed leg.
- **Budget-aware scaling.** `budget.remaining()` lets the finder / verifier pool size scale to the user's token target.
- **Concurrency cap + determinism.** `parallel()` / `pipeline()` give deterministic control flow with an automatic concurrency cap — no manual batching.

Dispatch the named subagents through Workflow with `agent(prompt, {agentType, schema})`:

- `agentType: 'voxel-builder:voxel-plan-reviewer'` + findings-array schema → §2e adversarial panel.
- `agentType: 'voxel-builder:voxel-layout-architect'` + layout-map-block schema → §2c→§2d.
- `agentType: 'voxel-builder:voxel-heading-curator'` + phrasing-palette schema → one per plan.
- `agentType: 'voxel-builder:voxel-widget-builder'` + one-node schema → Phase 3 build; same agent read-only for audit tiers.
- `agentType: 'voxel-builder:voxel-page-auditor'` → audit-tier orchestration.

**Multi-phase work = several workflows in sequence, one per phase.** Scout inline → Workflow fan-out → read structured results → reason at the gate → next phase. The orchestrator stays in the loop between phases.

**The judgment gates stay with the orchestrator, NOT inside a Workflow:** the Phase-0 rebuild-vs-revise call, §2f plan-review reconciliation, the computed §2g gate, and the verify→repair convergence decision. The Workflow runs the mechanical parallel fan-out; the orchestrator decides between fan-outs. This preserves the author ≠ repairer ≠ reviewer separation and the human-on-exception gate.

### Fan-out → Workflow expression map

| Pipeline point | Inline (fallback) | Workflow expression |
|---|---|---|
| §2c→§2d planning | curator + N architects in one message | `parallel([() => agent(curator,{schema}), ...sections.map(s => () => agent(architect(s),{agentType,schema}))])` |
| §2e adversarial review | M plan-reviewers in one message | `parallel(criteria.map(c => () => agent(reviewerBrief(c),{agentType:'voxel-builder:voxel-plan-reviewer',schema:FINDINGS})))` → orchestrator reconciles at §2f |
| Phase 3 build | K widget-builders in one message | `parallel(rows.map(r => () => agent(builderBrief(r),{agentType:'voxel-builder:voxel-widget-builder',schema:NODE})))` → orchestrator assembles + imports |
| Phase 6 verify | V verifiers in one message | `parallel(urls.map(u => () => agent(verifyBrief(u),{schema:VERDICT})))`; verify→repair loop = `while` on the convergence guard, evaluated by the orchestrator |
| audit tiers | per-tier subagents in one message | `pipeline(sections, s => agent(audit(s),{schema}), f => parallel(f.findings.map(verify)))` |
| migration Phase 3 | per-section builders in one message | same as Phase 3 build, with per-section isolation if writing files |

The atomic-scope contract is unchanged — one criterion / one section / one widget per `agent()` call. The `parallel()` legs ARE the single-message fan-out.

**Orphan caveat.** A backgrounded Workflow can stall or orphan if the session goes idle or is compacted for a long time mid-run. Keep per-phase workflows scoped to minutes, not hours; watch `/workflows`; and rely on `resumeFromRunId` to resume. For a short fan-out whose result is needed immediately in the same reasoning step, the inline single-message Agent dispatch is simpler and avoids the orphan risk.

## Fan-out per tier (audit)

The audit walk is **top-down** (page → section → widget); the fix loop is **bottom-up** (widget → section → page). Both fan out per tier.

| Tier | Fan-out unit | Subagent scope | Wall-time benefit |
|---|---|---|---|
| `[G]` Global | Single main-agent walk | Whole page (lint, tree shape, role context, cache freshness, revisions) | None — already cheap |
| `[S]` Section | One subagent per top-level wrapper | One section's subtree + its DOM region (anchored by `_cssid` / wrapper id) | N×, where N = top-level sections |
| `[W]` Widget | One subagent per non-trivial widget OR per cluster of ≤4 trivial widgets | One widget's settings + its DOM render | M×, where M = non-trivial widgets |

**Run all fan-out subagents concurrently** — as one Workflow `parallel()` / `pipeline()` step when opted in, or as a single inline message otherwise. Sequential dispatch defeats the purpose.

See [`audit.md`](../../workflows/audit.md) for the audit pipeline that uses this fan-out.

## Failure-class taxonomy

Six failure classes recur across tiers. Each subagent's brief lists which classes apply to its scope; out-of-scope classes are explicitly excluded. The first five are widget/section/page-tier classes that surface during audit and fix; the sixth is plan-tier and surfaces during the page-planning §2e adversarial-review fan-out (see [`page-planning.md`](../../workflows/page-planning.md)). The audit silent-failure probes — relation-loop self-traversal, CSS-token fallback drift, reindex-after-filter, unicode corruption — are categorized under the relevant class with `confidence: suspected` and an `sme_question`; see [`audit.md`](../../workflows/audit.md) §Silent-failure detection probes.

| Class | Storage signature | DOM / Plan signature | Tier where it surfaces |
|---|---|---|---|
| **Broken dynamic tags** | `@post(...)` / `@author(...)` / `@site(...)` unwrapped, mistyped, referencing a non-existent field, or string-prop value missing `@tags()...@endtags()` wrap | Literal `@post(title)` text leaking; or empty rendered string when source has data | `[W]` |
| **Broken dynamic loops** | `_voxel_loop` / `_vx_loop` source resolves empty; loop tag references the wrong relation/repeater field; iteration heading uses scope-mismatched path | Loop produces zero iterations despite source data being present | `[W]` and `[S]` |
| **Broken filters** | `_ef_loop_transform.filter_*` excludes everything; visibility `compare` operator wrong for field shape (e.g. `is_equal_to` against an array post-relation) | Loop renders nothing OR widget hidden when source data says it should show | `[W]` and `[S]` |
| **Broken visibility** | `_voxel_visibility_rules` / `_vx_visibility` evaluates false on real posts; legacy key on post-relation paths that the legacy evaluator can't navigate | Widget / section never renders | `[W]` and `[S]` |
| **Broken layouts** | Single `ef-card` root-wrapped; depth > 4; sibling wrappers with identical settings; missing required surface (h1, contact); wrong `html_tag` for purpose; reference to a retired/phantom widget name (`ef-accordion`, `ef-icon-heading`, `ef-media`, `ef-button`, `ef-buttons`, `ef-breadcrumb`, `ef-button-group`, `ef-map`, `ef-map-pin`) | Section visually misaligned; required content absent; wrappers without semantic role; phantom widget silently dropped at render | `[G]` and `[S]` |
| **Broken Plan Document** | Field-Inventory omissions, density deficit vs peer template, heading-hierarchy bugs (no h1, h2→h4 skip), dynamic tag resolving empty across the representative sample, phantom prop / phantom widget cited from SSOT, traversable relation unsurfaced, retired widget name in §2b, migration content-set deficit (production sentence/word missing from §2d) | Plan-doc text the criterion quotes verbatim from `/tmp/plan-<post_id>.md`; CLI output from `wpdev voxel:fields` / `voxel:data` / `elementor:tree` / the `agent-browser`-rendered production text that contradicts the plan | Plan tier (page-planning §2e), one of the `voxel-plan-reviewer` criteria |

## Atomic-scope contract

Every subagent brief enforces three rules:

1. **One scope, one report.** A widget agent reports only on its widget's props and that widget's DOM region. A section agent reports only on its wrapper-level concerns. A `voxel-plan-reviewer` criterion reports only within its remit (`coverage`, `density`, `hierarchy`, …). Cross-scope observations get dropped or escalated to the orchestrator — never bundled into a finding from a different scope.
2. **Failure classes named explicitly.** Brief lists which of the six classes the agent must check. Out-of-scope classes (e.g., layout checks at the widget tier when the widget isn't a wrapper) are explicitly excluded.
3. **Mode is per-dispatch.** Build, read-only investigation, or adversarial Plan Document review — never two in one dispatch. A read-only subagent that proposes a patch has violated mode and the orchestrator rejects its return. Mode discipline is encoded in the tool list (`voxel-schema-detective` and `voxel-plan-reviewer` literally cannot `Write`), not just in the prompt.

## Brief templates

Copy-paste-ready brief templates for each tier and mode live in [`briefs.md`](../audit/briefs.md). The structure:

- Widget tier (read-only): atomic widget audit with the failure classes named.
- Widget tier (build): atomic widget construction with prop schema preloaded.
- Section tier (read-only): wrapper subtree audit.
- Pass-1 widget mutation (build): per-widget fix dispatched from a `voxel-elementor-fixer` Pass 1.
- Plan-review briefs (read-only, per criterion): one section per `voxel-plan-reviewer` criterion; full per-criterion protocols live in [`voxel-plan-reviewer.md`](../../references/subagents/voxel-plan-reviewer.md).

## Aggregation

The orchestrator's job after fan-out:

1. Wait for all subagents in the batch to return — the single inline message returns its batch at once; a Workflow `parallel()` step returns the schema-validated objects on completion.
2. Validate each return matches its scope. Reject cross-scope or mode-violating returns.
3. Merge:
   - **Build mode:** assemble widget JSON in tree-position order, write `_elementor_data` once.
   - **Read-only mode:** dedupe findings, sort by tier (G/S/W) and severity (Critical/Improvement/Cosmetic), emit aggregated report.
   - **Adversarial Plan Document review:** merge per-criterion findings into `/tmp/plan-review-<post_id>.md`, sort by criterion then severity (C/I/K), then write reconciliation outcomes (`resolved:` / `override: <concrete reason>` / `deferred:`) under each finding in the Plan Document's §2f. See [`page-planning.md`](../../workflows/page-planning.md) §2f.
4. Decide loop continuation:
   - Audit: re-run after fix passes; see [`audit.md`](../../workflows/audit.md) §Hierarchy + iteration model.
   - Plan review: re-dispatch §2e adversaries whenever the plan has materially changed; stop when it converges; surface the residual to the operator if it won't converge. See [`page-planning.md`](../../workflows/page-planning.md) §2f loop rule.

## Anti-patterns

- **Sequential dispatch.** Defeats wall-time savings. Fan out concurrently — a Workflow `parallel()` step when opted in, or one inline message otherwise. Sequential dispatch on N criteria / N widgets / N sections costs N× wall-time for zero correctness gain.
- **Single subagent for the whole page.** Defeats atomic-scope; one subagent's failures cascade.
- **Mixing modes in the same fan-out.** Build with read-only, or audit with plan-review — mode discipline breaks; the orchestrator can't tell whether a return is a finding, a patch, or a criterion-scoped finding.
- **Synthesizing widget settings from `define_props_schema()`.** Always extract from `wpdev elementor:dump` (or a golden fixture under [`examples/`](../../examples)) instead. Schema introspection answers "what props exist"; dump answers "what shape do the values take in the wild". Enforced as rules.md Rule 1 + 2 and as AGENTS.md §Shared anti-patterns.
- **Referencing retired/phantom widget names.** `ef-accordion`, `ef-icon-heading`, `ef-media`, `ef-button`, `ef-buttons`, `ef-breadcrumb`, `ef-button-group`, `ef-map`, `ef-map-pin` are not registered. Translate to the replacement (see [`widgets.md`](../ef/widgets.md) §Phantom + §Retired) before any dispatch; the `ssot-integrity` plan-review criterion flags every occurrence as severity C.
- **Plan-review criterion that proposes a patch.** Read-only contract — return findings only; the orchestrator decides revisions and the widget-builder (Phase 3) implements. A `voxel-plan-reviewer` return containing a patch is rejected.
- **Calling the Workflow tool unconditionally.** Workflow is the preferred fan-out only when the user has opted into multi-agent orchestration; the inline single-message path stays valid at all times. Never force a Workflow when the user hasn't opted in.
- **Burying a judgment gate inside a Workflow.** The rebuild-vs-revise call, §2f reconciliation, the §2g gate, and verify→repair convergence are orchestrator-owned between fan-outs. A Workflow that decides between fan-outs collapses the author ≠ repairer ≠ reviewer separation.
