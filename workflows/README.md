# Workflow Ownership Index

`SKILL.md` selects exactly one primary workflow per task. This index defines each route's
exclusive owner and exit artifact. Supporting sub-pipelines are invoked only by a primary
workflow and never compete at intake.

## Primary Workflows

| Workflow | Exclusive owner | Exit artifact/evidence |
|---|---|---|
| [`audit.md`](audit.md) | Read-only page/template diagnosis | Tiered evidence report + one owner per handoff |
| [`cpt-lifecycle.md`](cpt-lifecycle.md) | New Voxel CPT definition/registration | Registered, indexed, configured, verified CPT |
| [`cpt-repair.md`](cpt-repair.md) | Existing CPT config/runtime/template-resolution repair | Source-owner repair + all affected surfaces verified |
| [`migrate.md`](migrate.md) | Legacy Elementor V3 to EF V4 conversion | Preserved-information EF tree + browser proof |
| [`build.md`](build.md) | General EF `_elementor_data` creation/modification | Read-back-equal, linted, browser-verified tree |
| [`archive-search-pages.md`](archive-search-pages.md) | Public archive/search URL and result surface | Canonical searchable page + index/browser proof |
| [`section-templates.md`](section-templates.md) | Reusable section-store extraction/refresh | Sanitized, indexed, linted template package |
| [`card-actions.md`](card-actions.md) | `ts_actions` / navbar action-row strip | Schema-valid actions with runtime destinations |
| [`fix-known.md`](fix-known.md) | Exact known defect signatures | Two-gate mechanical repair + verification/rollback |
| [`curation.md`](curation.md) | Voxel records, fields, relations, users, visible copy | Per-record read-back + invariant verification |
| [`video-content-backfill.md`](video-content-backfill.md) | Imported Video drafts missing editorial/source-supported content | Evidence-complete Video records + publish/read-back/browser proof |
| [`faq-authoring.md`](faq-authoring.md) | Visible FAQ rows for existing content | Supported FAQ rows or verified curation handoff |
| [`geolocation.md`](geolocation.md) | Canonical service to city-child derivation | Unique geo-child/subtree + SEO/browser gates |
| [`image-generation.md`](image-generation.md) | Content-image generation/attachment | Unique optimized attachments + rendered proof |
| [`settings.md`](settings.md) | lean-seo output configuration/debugging | Read-back-equal settings + live output validation |
| [`admin-menu.md`](admin-menu.md) | WordPress Lean Admin menu creation/alignment | `lean_admin_metamenu`-owned menu verified against Voxel CPTs |
| [`performance.md`](performance.md) | Measured runtime performance repair | Same-state before/after delta + behavior proof |
| [`cloudflare.md`](cloudflare.md) | Cloudflare edge audit/convergence for the site zone | Read-back-verified edge posture + staged manual/risky plan |
| [`design-tokens.md`](design-tokens.md) | EF brand color palette (`--ef-color-*` SSOT + `_light`) | Read-back-equal cascade + tint/base browser proof |

## Supporting Sub-Pipeline

| Workflow | Called by | Contract |
|---|---|---|
| [`page-planning.md`](page-planning.md) | build, migrate, structural repair | Gated Plan Document matching the Blueprint contract |

## Supporting Contracts

| Contract | Purpose |
|---|---|
| [`../references/core/parallel-dispatch.md`](../references/core/parallel-dispatch.md) | Bounded 5-10-leaf batches, waves, envelopes, retries, centralized writes |
| [`../references/core/page-plan-contract.md`](../references/core/page-plan-contract.md) | Plan/Blueprint output schema |
| [`../references/verification/behavior-contract.md`](../references/verification/behavior-contract.md) | Existing-data semantic boundary |
| [`../references/verification/browser.md`](../references/verification/browser.md) | Runtime verification commands/assertions |

## Adding A Workflow

Add a primary route only when no existing owner can accept the source state and exit
artifact without overlap. Every workflow must have numbered phases, explicit Entry/Exit,
numbered actions, final verification, and one row here. Update the primary route table in
`SKILL.md` in the same change.
