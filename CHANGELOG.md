# Changelog

All notable changes to the voxel-builder skill are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Reusable section-template library** (`templates/`) — a portable store of extracted, sanitized `_elementor_data` subtrees agents can splice into new builds instead of synthesizing from scratch every time. Three-tier scope model (`global` / `section` / `page`); each template ships a `template.json` + a `meta.yml` (id, scope, type, tags, widgets, dtags_used, requires_plugins, source_note, breakpoints) and is cataloged in `templates/index.md`. See `templates/README.md` for the on-disk shape, naming rule, and SSOT-wins discipline — the SSOT (`cli/src/generated/widget-schemas.json`) always wins over a template's shape; templates are starting trees, never authoritative spec.
- **`references/templates/placeholder-policy.md`** — the sanitization SSOT: an 8-entry allowlist of universal dynamic tags safe to keep live in a stored template (`parent.title`, `slug`, `title`, `h1`, `:excerpt`, `author.display_name`, `author.profile.*`, featured-image id) plus a denylist (site TLDs, emails, phone numbers, real URLs, curated proper nouns). Every other static string or non-allowlisted dtag is replaced with Lorem Ipsum before a template is stored.
- **`workflows/section-templates.md`** — the extraction+sanitization procedure (postId resolve → export → subtree select → recursive id-regen → sanitize → normalize → meta.yml → index row → lint gate) for turning a live page section into a stored template. Routed from `SKILL.md` ("Save/extract a section template", "turn this hero into a reusable template").
- **Two seeded section templates** — `hero-services-search` and `hero-city-geo`, extracted end-to-end from a real production Voxel site and sanitized against the placeholder policy (zero denylisted proper nouns; only allowlisted dtags survive).
- **`scripts/lint-templates.sh`** — the schema-aware drift/verification gate for the template store: validates every `template.json` against the live EF schema via `wpdev elementor:validate --file`, plus dtag allowlist/denylist scans and `meta.yml`↔JSON dtag-set equality in both directions. Wired into `scripts/lint.sh` as a new check that runs whenever templates exist.
- **Build-workflow wiring** — `workflows/build.md` Phase 0 gains a third rebuild-vs-revise branch ("seed from a saved section template"), and Phase 2 §2d blueprints may now bind a section to a saved template by id instead of full widget-by-widget synthesis; both paths stay subordinate to the schema SSOT and still get patched/validated prop-by-prop. `SKILL.md` and `references/README.md` gain routing and reference-index entries pointing at the new store.

### Changed
- Reframed `voxel-builder` as an orchestrator-first skill: `SKILL.md` now makes named subagent dispatch a core principle and mandatory reference read, `rules.md` promotes the main agent to route/gate/aggregate/write-once duties, and the build/audit workflows now describe leaf work as delegated to atomic subagent briefs instead of performed inline by the main agent.
- Tightened the glossary/defined-term FAQ policy across the skill: on-page FAQ content is optional and must be genuine term-specific Q&A; `FAQPage` schema is not emitted for glossary/definition CPTs; the migration workflow no longer tells agents to re-add legacy FAQPage markup for rich-result eligibility after Google's 2026-05-07 deprecation.
- Surfaced the new `wpdev voxel:field-schema` command in the CPT lifecycle and command surface as the corruption-proof runtime patch path for Voxel field-definition attributes, while preserving the blueprint/source-first rule. Added coverage-map rows for `voxel:field-schema` and `elementor:fetch-phosphor` so the skill lint tracks the live CLI registry again.
- **Merged the `voxel-curator` skill in as the curation route.** The two sibling skills are now one. Voxel entity-data curation (create/edit/merge/delete records, taxonomies, profiles, linked WordPress users, organizations, locations, relationships) is reached from the SKILL.md routing table and runs as `workflows/curation.md` — a 4-phase Sequential-Pipeline (Discover → Plan → Execute → Verify) with a merge/delete safety gate. The curator's `_shared/*` moved to `references/curation/*`; `voxel-curator-agent` joins the subagent set (9 briefs). The SKILL.md description now carries both build and curation triggers. Routing table dropped its stale slash-command column. The standalone `voxel-curator` skill is removed.

### Changed
- `references/voxel/seo-defined-terms.md` now embodies the full Glossary & Definition SEO research, not just Tiers 1-2. Added: the **anti-thin-content mandate** (Tier 4 — `content` is now a required 400-800 word domain-expert body, with the "only an expert could write this" test and index-bloat/doorway risk); the **flat-URL rule** (Tier 3.2 — parent terms to the CPT landing page, express category via a taxonomy, never `post_parent`, because both the URL and the breadcrumb derive from `get_post_ancestors`); **hub-and-spoke + lateral-linking** discipline (Tier 3.1/3.3 — `siblings` relation, varied anchors, capped exact-match); **E-E-A-T** (Tier 4.3 — named author, primary sources, `dateModified`); **format** guidance (Tier 1.3 — paragraph lead, list/table only when genuinely enumerable/comparative); **Speakable/QAPage** notes (Tier 2.3/2.4); and a **per-term completion checklist** so following the recipe yields a complete term, not a thin one. The field model marks `content` required. `cpt-lifecycle.md` Phase 4 pointer restated to surface the content/flat-URL/linking mandates.

### Added
- `references/voxel/seo-defined-terms.md` — the reusable recipe for a glossary / dictionary / defined-term CPT: the field↔SERP-surface model with enforced answer-block length (`definition` 200-400 chars ≈ 40-60 words), the two-surface rule (meta description from a bounded `hook` field, never the answer block), the `DefinedTerm` + `DefinedTermSet` + `sameAs` (`@each`/`@map`) schema graph, the hard no-`FAQPage` rule (deprecated by Google 2026-05-07), the `voxel:settings` + `schema:set` CLI sequence, and answer-block writing guidance. Wired into SKILL.md routing/description and `cpt-lifecycle.md` Phases 3-4.
- `references/core/command-surface.md` §Schema (lean-seo) now documents the full config DSL: source prefixes (`post:`/`meta:`/`seo:`/`var:`/`row:`/`hierarchy:*`/`query:`/`@value:`/`concat:`), structural keys (`@each`/`@ref`/`@map`/`@list`/`@filter`), and transforms (`strip_tags`, …). `@map` (repeater → flat de-duplicated value array, for `sameAs`) is new.

### Fixed
- **Corrected the group-method dynamic-tag syntax across all docs — the dot form was wrong everywhere.** Verified against the live tokenizer (`app/dynamic-data/voxelscript/tokenizer.php`) and `\Voxel\render()`: `@site.math(...)`, `@post.meta(...)`, `@term.post_count(...)`, `@term.meta(...)`, `@user.meta(...)`, `@current_user.meta(...)`, `@site.query_var(...)` **never tokenize** (the tokenizer requires `(` immediately after the group key at line 64; a `.` there aborts tag parsing → whole string emitted as plain text, a silent literal leak with no lint/console error). Group methods are registered as **modifiers** (`base-data-group.php:110-122` → `dynamic-tag.php:40-56`) so the only valid form is `@group().method(...)` — empty parens on the tag, then the method chained like `.round()`. Rewrote ~50 occurrences across `references/voxel/voxel-tags.md`, `references/ef/dynamic-text.md`, `references/voxel/{voxel-search,voxel-platform,voxel-commerce}.md`, and the source-of-truth `docs/solutions/best-practices/voxel-modifier-catalog.md`, and added a ⚠️ syntax-warning block in the group-methods sections of both `voxel-tags.md` and the catalog. Proven end-to-end: `@site().math((10 - 4) / 2)` → `3`, `@site.math(...)` → full text leak.
- **Documented the tokenizer paren-depth asymmetry and the correct date-duration recipe.** Modifier args track paren depth (`tokenizer.php:148-189`) but a tag's **property path does not** (stops at the first `)`, `tokenizer.php:80-101`), so `@site(math((a-b)/c))` breaks (even `@site(math(2-1))` renders `1)`) while `@site().math((a-b)/c)` works — the expression must live in the `.math(...)` **arg**. Added a `voxel-tags.md` §"Duration between two date fields" recipe using `.date_format(U)` to convert dates to Unix inline (`@site().math((@post(f.end).date_format(U) - @post(f.start).date_format(U)) / 3600)`), plus the `HhMM` zero-padded clock-format pattern (MathExecutor has no string-concat, so pad via a control-structure branch). This supersedes the old modifier-catalog "store the date as a Unix timestamp in a numeric field" workaround and corrects the wrong `@site.math(@post(:date) + 86400)` claim (`:date` is a formatted string, not a number). Recurring-date fields expose only `start`/`end`/`is_multiday`/`is_allday` per item — there is no `duration` property; it is always computed.
- `scripts/release.sh` now inserts generated release notes below `## [Unreleased]`, preserving the Keep a Changelog working bucket and avoiding BSD `awk -v` multi-line failures. `scripts/lint.sh` guards this invariant so future releases cannot bury the unreleased section again.
- `scripts/verify-install.sh` now points `agent-browser` guidance at `references/verification/browser.md`, and lint blocks active docs/scripts from reintroducing removed `references/{build,audit}/` or `references/browser-verify` paths.
- `voxel-curator` docs now use real `wpdev` command shapes for `voxel:fields`, `voxel:sample`, `voxel:export`, `voxel:backfill-authors`, record creation/deletion, and profile/user linkage. Lint now validates every shipped skill and blocks the known-wrong CLI forms from returning.
- README and skill indexes now list all shipped commands/skills/agents, including `card-actions`, `voxel-curator`, and `voxel-curator-agent`, and the stale `tags.md` EF reference now points at `widgets.md`.
- CPT-lifecycle and template-resolution docs now route every wp-cli example through `wpdev wp <site>` (cwd-independent SSOT), and lint blocks raw `wp …` inside doc code fences.
- Dropped the Permalink Manager Pro conflict branch from the CPT lifecycle now that PMP is removed workspace-wide; `lean-seo` is documented as the sole permalink-routing authority, and any third-party permalink plugin is treated as drift to remove.

### Changed
- CPT lifecycle Phase 0 replaces the PMP activation branch with a generic "no third-party permalink plugin" prerequisite check.
- `scripts/README.md` now documents the actual CI-only lint enforcement path and marks local hooks as optional instead of claiming a committed `.githooks/pre-commit` exists.
- Remaining EF `tags.md` references in `commands/cards.md`, `commands/schema.md`, and `agents/voxel-widget-builder.md` now point at `widgets.md`/`ef-parts.md` (the tag-row surface's real home), and lint blocks the removed EF `tags.md` filename from returning.
- Voxel curator agent frontmatter now parses as YAML, and the shared curator CLI map uses the required `voxel:cache <site> clear` form.
- Elementor build/fix/audit docs now use real `elementor:import <site> <post_id> <file> --save`, `elementor:strip:wrappers <site> --fix --yes`, and `elementor:ef:migrate <site> <subcommand>` forms. Lint blocks the stale flag/order variants.
- `lint.sh` removed Bash-only `${var//...}` substitutions from the markdown-link check so CI's POSIX `sh scripts/lint.sh` cannot false-green that section.
- `masonry.md` and `section-rhythm.md` are now one hop from both `SKILL.md` and `references/README.md`, matching the reference-index rule.
- Transactional CPT lifecycle guidance now points at current lean-seo filter surfaces (`lean_seo_sitemap_exclude()` and `lean_seo_noindex_post_types`) instead of stale line numbers / TODO fallback text.

## [1.0.0] - 2026-06-15

Masonry / bento layout guidance, and full wpdev CLI coverage — the last two `surface-pending` wiring rows closed (only `voxel:heading-curator`, a perf-cache optimization, deliberately deferred). Coverage 46→48 of ~60 plugin-relevant commands. Closes #8.

### Added
- **`references/ef/masonry.md`** — the size-=-hierarchy rule, a dogfooded worked example (klarc homepage "synergie" block: flat 4×4 grid of six 276×304 tiles → one 2×2 hero + one 1×2 image card + four 1×1 cards), the `1fr 2fr` / `3fr 2fr` track-ratio family, and the span mechanics/gotchas (`row_span` is non-responsive + no `full`; mobile single-column collapse makes spans inert automatically; `grid-auto-flow:dense` is a style-schema prop silently ignored as a bare setting; DOM order = reading order). Production-safe technique only — native CSS `grid-lanes`/masonry is Safari-flagged as of 2026 and explicitly not used.
- Wired into **`voxel-layout-architect`** steps 5 (asymmetric/masonry track selection) and 8 (anchor card spans), and the **`ef/widgets.md`** reference router.
- **`voxel:comparator` wired** into `references/voxel/voxel-field-visibility.md` (§Choosing the right comparator for dtag visibility rules) — resolves `is_equal_to` vs `contains` from a field's storage type (array-typed taxonomy/multiselect/post-relation → `contains`), the SSOT for the "fragile vis-gate on structured fields" fix class. (#8 surface-pending row closed.)
- **`elementor:codegen:verify` wired** into `references/core/rules.md` rule 1 — the live-site SSOT drift gate, companion to the offline `elementor:codegen --check`. (#8 surface-pending row closed.)

### Changed
- `references/core/wpdev-coverage.md` reconciled: 48 surfaced, 1 surface-pending (`voxel:heading-curator`).

## [0.9.0] - 2026-06-03

A dedicated, SSOT-validated workflow for defining card action buttons — closing the gap that let cards ship dead-link / inert-button CTAs that `elementor:lint` cannot see.

### Added
- **the card-actions workflow (`workflows/card-actions.md`)** command + **`workflows/card-actions.md`** (Phase 0→5: preflight → choose → resolve cells → build envelope → apply → verify) — turns "what should this card's buttons do?" into a correct `ef-action-rows` envelope. Gates the two lint-invisible defects at compose time: a destination dtag that resolves empty (the `@post(url)` trap — use `@post(permalink)`) and a Voxel-runtime action selected on a page lacking its runtime piece (inert button). Includes a no-redundancy check (a footer `action_link` duplicating the heading permalink adds nothing).
- **`scripts/action-spec.sh`** — SSOT lookup that prints any action type's required cells + field specs straight from `cli/src/generated/ef-catalogs.json` (generated by `wpdev elementor:codegen` from `ef_action_types()` + `ef_action_field_specs()`). Drives the workflow's Phase-2 cell collection deterministically.
- Routing rows wiring `card-actions` into SKILL.md (routing table + task-picker + reference index) and `workflows/README.md`.

### Fixed
- `wpdev-coverage.md` gained the missing `elementor:validate` row (offline Ajv validator) — the coverage map now matches the live registry again.

## [0.8.0] - 2026-06-03

DX drift-gate hardening + a prose↔CLI/SSOT reconciliation pass. The plugin's own command and criterion vocabularies now answer to machine SSOTs the way widget shapes already did — phantom `wpdev` verbs, criterion-id drift, and broken anchors are now mechanically un-committable.

### Added
- **CLI-verb drift gate** (`scripts/lint.sh` §"CLI verb drift") — two tiers: (a) portable — no `wpdev <verb>` invoked in the docs (and no known-absent verb mentioned in prose) may be in `wpdev-coverage.md`'s "verified absent" list; (b) grounded — when the workspace `cli/` is a sibling, every invoked verb must exist in the real registry (`cli/src/index.ts`) AND the coverage map must stay in sync with it (every real `elementor:`/`voxel:` verb has a row; no "verified absent" verb actually exists). Catches the phantom-command class at commit time.
- **Criteria SSOT consistency gate** — asserts `criteria.json` ↔ `criteria.md` ↔ the `voxel-plan-reviewer` `### <id>` protocol headers share one id set, so the orchestrator can never hand the reviewer a `criterion_id` with no matching protocol.
- **lychee deep-link + anchor check** — validates `#fragment` anchors against target headings and every markdown link form (offline, deterministic), complementing the home-grown relative-link check. Skips gracefully when `lychee` is absent.
- **pre-commit lint trigger** — `.githooks/pre-commit` now runs the plugin lint whenever a `voxel-builder/` file is staged, aborting on any FAIL.
- **Data-driven fallback in `voxel-plan-reviewer`** — a `criterion_id` with no dedicated `### ` protocol block (e.g. `section-order`, `rebuild-vs-revise`) is executed straight from its `criteria.json` row (`evidence` → `predicate`), making "criteria are data, the pipeline is generic" literally true.

### Changed
- **`seven-rules.md` → `rules.md`** — the file carried eight rules; the count-neutral name retires the "(filename is historical)" apology gloss repeated across four command files. All ~66 inbound references rewritten.
- **Criterion ids canonicalized** — `hierarchy-outline` → `hierarchy`, `content-preservation` → `migration-preservation` in `criteria.json`/`criteria.md`, matching the dominant convention and the reviewer agent's executable protocol headers.
- `wpdev-coverage.md` completeness is now enforced by the lint gate (against the live registry) instead of a hand-stamped audit date; `elementor:mutate`, `elementor:action-drift`, `voxel:comparator`, `voxel:heading-curator`, and `voxel:set-field` gained the rows they were missing; `elementor:mutate` added to `command-surface.md`.
- Migration Phase 0 now runs `wpdev elementor:codegen` + `--check`, so the §2g drift clause is satisfiable on the migration path (it was only wired on the build path).
- `audit.md` failure-class taxonomy now states its five tier classes are the first five of the six in `parallel-dispatch.md` (the sixth is plan-tier), removing the 5-vs-6 ambiguity.
- SKILL.md `argument-hint` no longer over-generalizes a uniform `[task description]` the commands don't share.
- **De-duplicated the Workflow-orchestration rationale.** The 5-bullet "what Workflow buys" block + orphan caveat now live once in `parallel-dispatch.md` §"Expressing a fan-out through the Workflow tool"; SKILL.md, page-planning.md, audit.md, migration.md, and elementor-build.md point there and keep only their per-phase legs — honoring SKILL.md's own "each phase doc points to the SSOT" claim, and removing the largest source of drift risk in the skill.
- Section-tier audit now dispatches a named `voxel-page-auditor` (subtree-scoped) instead of an unnamed ad-hoc subagent (the canonical Workflow expression already named it; the inline-dispatch prose now matches). Fixer Pass 2 owns its section mutations (no phantom section build-agent).

### Fixed
- **Phantom `wpdev` verbs purged from agents + prose** — `elementor:rollback` → `elementor:revisions:restore` (3 files); `elementor:strip:card-wrappers` → `elementor:strip:wrappers` (fixer agent, behavior-contract); `elementor:migrate:buttons` / `:icon-heading` → `elementor:ef:migrate run` (fixer agent + its description); `elementor:migrate:loop` → `elementor:migrate:loop-index` (audit); `voxel:fields-validate` → `voxel:fields` (field-types). All were verbs the registry never exposed.
- **EF parts miscount** — SKILL.md + README claimed "16 EF parts"; corrected to the authoritative 10 user-facing parts (+ base contracts / Media handlers / Nav traits) per `ef-parts.md`.
- Broken anchor `ef-parts.md → ef-helpers.md#ef_expand_definition…` (lychee-caught) — fragment dropped (the heading's punctuation makes a fragile slug).
- `voxel-elementor-fixer` "single `Agent` message" → "single `Task` message" (the dispatch primitive it actually has); and `elementor:lint --stdin` (no such flag) → the write-time lint inside `elementor:import` + a post-import `elementor:lint --post`.
- `audit.md` `migrate:loop` shorthand → `migrate:loop-index` (the bare form the first sweep missed); `elementor:migrate:loop` added to the verified-absent list so the gate catches the shorthand too.
- **Stale EF-source accounting in `ef-parts.md`** — added the omitted `Color` media handler (6 handlers, not 5); removed the `Nav_Item_Tree` trait / `tree.php` and its pipeline step (consolidated into the single nested-tree editor in commit `6971d4fc7`, `expand_tree_rows()` gone); corrected the action-handler file count (30 → 34).
- `criteria.schema.json` `severity` now documents that the row value is the gate-blocking ceiling, not the per-finding severity (preempts the recurring "why can a C/I row emit K?" question).

## [0.7.0] - 2026-06-01

Autonomy + bulletproof-by-logic pass and a hierarchical references reorg. The build workflow's human `APPROVED` keystone becomes a computed gate; the criteria checklist becomes a machine SSOT; the writer makes invalid data unrepresentable.

### Added
- **Hierarchical `references/`** — flat 30-file dir reorganized into five atomic groups (`core/` `build/` `audit/` `ef/` `voxel/`) with a navigable [`references/README.md`](skills/voxel-builder/references/README.md) index. Every intra-reference link, `${CLAUDE_PLUGIN_ROOT}` ref, and inline path mention rewritten to the new subpaths.
- **`core/criteria.json` + `core/criteria.schema.json`** — the criteria checklist as a machine SSOT (`{id, scope, phase, severity, criterion, evidence, predicate}` per row); `criteria.md` is the human view. The orchestrator dispatches one `voxel-plan-reviewer` agent per in-scope criterion — expandable by one validated row, no pipeline edit.
- **Write-time gate in `wpdev elementor:import`** — refuses to persist a tree that fails the EF schema lint or carries `u00xx` unicode corruption (shared `lint/run-data.ts` `lintTreeWithSchema`, DRY with `elementor:lint`). `--no-verify` bypasses.
- **`wpdev voxel:sample`** — exports the most-complete posts of a CPT (ranked by filled fields + relations + repeaters) to a temp folder, so planning samples the richest real data.

### Changed
- **Computed gate (autonomy):** §2g proceeds automatically when every Critical criterion passes / carries a valid override (`GATE: green (auto)`); the operator is the exception path, not the keystone. Override-validity is its own criterion; the reconciliation loop is governed by a monotonic convergence guard (strict-shrink-or-escalate) instead of a fixed iteration cap. Findings flow on a single `/tmp/findings-<post_id>.jsonl` bus.
- **By-construction guards:** auto-prune all revisions to latest + rebuild-vs-revise call (Phase 0); drift preflight (`elementor:codegen --check`); relation self-exclusion injected at compose time; empty-vs-bug computed from `voxel:data`; content-addressed widget IDs + run fingerprint + append-only ledger for idempotent, auditable re-entry; ts-* fixture freshness gate.
- `wpdev elementor:codegen` now syncs the schema SSOT mirror into `references/ef/widget-schemas.json` (drift-gated alongside the canonical copy).
- Whole-plugin portfolio-agnostic cleanup — site names, post IDs, named CPTs, and control thresholds replaced with placeholders / hierarchical judgment.

### Fixed
- Reconciled every "operator must write `APPROVED`" assertion across the skill, agents, and commands to the computed-gate model (no internal contradiction).

## [0.6.0] - 2026-05-30

Browser-verification surface rebuilt on the **`agent-browser` CLI** (replacing phantom `mcp__agent-browser__*` / `mcp__playwright__*` / `mcp__crawl4ai__*` tool references that no agent could actually call), plus session-driven hardening from the cosmetic-labs Companies (post 13) + Services (post 46083) builds. Source: `/ce-sessions` review of all voxel-builder invocations on 2026-05-29/30.

### Added
- `references/browser-verify.md` — **new canonical SSOT for the `agent-browser` CLI protocol** (29th reference file). Owns: parallel `--session vb-<post_id>-<n>` isolation (the native fix for the profile-lock → text-scrape degradation that hid layout bugs in past sessions), the full command table (`open` / `snapshot` / `screenshot --full` / `get box` / `get styles` / `eval --stdin` / `console` / `errors` / `network requests` / `close`), the mandatory computed-style layout-assertion block, the read-the-screenshot rule, the production-page baseline recipe (replaces crawl4ai — agent-browser renders JS so Voxel dynamic tags resolve as a visitor sees them), `diff screenshot --baseline` for before/after, and the **browser-unavailable fallback** (`doctor --fix` once, else flag `render-unverified` and surface to operator — never silently pass on `curl` text).
- `references/voxel-tags.md` — the **`field:` prefix disambiguator**: when a CPT field key collides with a Voxel built-in property (`status`, `url`, `title`, `date`, `author`…), `@post(<key>)` resolves the built-in, not the field; `@post(field:<key>)` forces the custom-field branch. Documented with detection guidance and a data-wiring persona check. (Discovered the hard way: a `status` select rendered "Published" instead of "Open".)
- `references/actions.md` — the **canonical stored `_vx_loop` / `_vx_visibility` `$$type` envelope** (golden), grounded in `EF\Envelope::vx_loop()` / `::vx_visibility()` / `::vx_rule_dtag()`. Closes the "no on-site loop example to dump" gap that forced reading `loop-resolver.php` during the Services migration — this block IS the source now.
- Stale-plan guard in `references/elementor-build.md` §Phase 2 and `references/page-planning.md` entry criteria — check for an existing `/tmp/plan-<post_id>.md` and offer continue/revise/discard before composing; never blind-`Write` over an `APPROVED` plan.
- Dead-reference guard for `ts-*` post-ID settings (`ts_card_template__*`, `ts_template_id`, `connect_map`, …) in `references/elementor-build.md` §Phase 1 and the `voxel-widget-builder` agent — verify each referenced post exists (`wp post get <id> --field=post_status`) before emitting the node, so a feed never silently renders with a deleted card template.

### Changed
- **All browser verification migrated to the `agent-browser` CLI** across `references/elementor-build.md` §Phase 6, `references/audit.md` Stream D, `references/migration.md` Phase 5, `references/seven-rules.md` rule 7 + success checklist, `references/cpt-lifecycle.md` smoke-test, and `references/behavior-contract.md` baseline capture. Each now delegates the tool surface to `browser-verify.md` and uses one isolated `--session` per parallel subagent. There is **no** MCP browser server dependency.
- **Migration-preservation production baseline migrated off crawl4ai to `agent-browser`** in `references/page-planning.md` (§entry, §2d, persona 8), `references/migration.md` (§Iron Law, Phase 0), `agents/voxel-plan-reviewer.md` (description, protocol, tools — `mcp__crawl4ai__md` removed; the CLI runs via `Bash`), and `references/parallel-dispatch.md`.
- `elementor:mutate` is now the **canonical post-write repair path** (atomic mutate → lint → CSS regen → purge → optional HTTP check) in `references/elementor-build.md` §Choosing-the-mutation-tool, `commands/fix-known.md`, and `references/behavior-contract.md` — replacing raw `wp eval-file` for single-post `_elementor_data` changes (which skipped the CSS-regen + purge tail and left pages rendering stale).
- `references/page-planning.md` §2d Blueprint Settings column now requires the FULL `$$type` envelope per prop, not just the value. Example shows responsive-string with every breakpoint's inner sub-envelope wrapped. Cites the new PHP envelope helper.
- `commands/audit.md` — Phase 0 revisions audit moved upfront in the dispatch protocol; was historically deferred and only happened when the operator asked.

### Fixed
- **`references/migration.md` self-contradiction.** The anti-patterns list said "'Fixing' content while migrating — out of scope; preserve verbatim", flatly contradicting the file's own Iron Law (improvements encouraged with an Improvements-log entry). The real failure mode is the *silent* edit, not the edit — corrected the anti-pattern to forbid editing-without-an-Improvements-log-entry, with dynamic-tag expressions as the byte-for-byte exception. This drift drove the migration-preservation persona reversals seen in session.
- Paired with concurrent `elementor-framework` release: `wpdev elementor:lint` now validates envelope completeness on responsive primitives (`ef-responsive-string`, `ef-responsive-number`) — recurses into desktop/tablet/mobile sub-envelopes and flags missing inner `$$type` markers as `v3-shape`. Previous lint treated these as opaque and missed silent-drop bugs.

## [0.5.1] - 2026-05-29

Production-tested hardening from the cosmetic-labs Companies single template rebuild + 11 plugin-improvement items.

### Added
- `commands/fix-known.md` — new slash command the fix-known workflow (`workflows/fix-known.md`) for the 8-class catalog of mechanically-detectable + mechanically-fixable bugs (loopable-row-missing-loop, array-comparator-mismatch, fragile-vis-gate-on-structured-field, malformed-envelope, cols-inheritance-cascade, missing-root-main, missing-hero-header-tag, cta-aside-mistag). Skips the full plan-review cycle for class-matched issues.
- `voxel-widget-builder` agent gained 3 new anti-patterns: (a) treating `widget-schemas.json` row-prop lists as closed sets (Loopable_Row auto-merges `_vx_loop`/`_vx_visibility`), (b) `is_equal_to` on array-typed sub-fields, (c) hand-authored atomic envelopes without `$$type` markers. Each cites the canonical reference in `actions.md`.

### Changed
- `references/page-planning.md` §2d Blueprint Settings column now requires the FULL `$$type` envelope per prop, not just the value. Example shows responsive-string with every breakpoint's inner sub-envelope wrapped. Cites the new PHP envelope helper.
- `references/elementor-build.md` §Phase 6 verification gained mandatory LAYOUT ASSERTIONS via `browser_evaluate` — every section wrapper's width / grid-template-columns / inherited `--ef-cols` is inspected. Text-only checklist passed on visually-collapsed pages in past sessions; layout assertions are no longer optional. The subagent brief now demands the verifier READ the full-page screenshot and describe what it sees.
- `commands/audit.md` — Phase 0 revisions audit moved upfront in the dispatch protocol; was historically deferred and only happened when the operator asked.

### Fixed (paired with concurrent `elementor-framework` release)
- `wpdev elementor:lint` now validates envelope completeness on responsive primitives (`ef-responsive-string`, `ef-responsive-number`) — recurses into desktop/tablet/mobile sub-envelopes and flags missing inner `$$type` markers as `v3-shape`. Previous lint treated these as opaque and missed silent-drop bugs.

### Concurrent wpdev CLI commands (companion release)
- `wpdev elementor:codegen` now emits `widget-schemas.json["$runtimeInjectedCells"]` — a discoverable block listing which envelope cell sets (`loop`, `actions`) auto-merge onto each row type at runtime. Eliminates the false-positive "phantom prop" finding for row-level `_vx_loop` / `_vx_visibility` that bit us on cosmetic-labs post 13. Reviewers cross-reference this block before flagging.
- `wpdev elementor:mutate <site> <postId> <mutator.php>` — atomic 5-step mutate loop: mutate → lint → CSS regen → cache purge → optional URL fetch with HTTP-status check. Replaces the previous 6-command manual sequence that operators forgot at least one step of every iteration.
- `wpdev voxel:comparator <site> <field>[.<subkey>]` — resolves the right dtag comparator (`is_equal_to` vs `contains`) from the Voxel field type. Counterpart to the PHP-side `EF\Envelope::comparator_for_subfield()` for scripts that build vis-rules from outside PHP.
- `wpdev voxel:heading-curator <site>` — extracts production heading phrasings from peer single templates and writes a per-site cache at `docs/voxel-site-patterns/<site>.json`. The voxel-heading-curator agent reads this cache instead of re-extracting on every plan dispatch.

### Concurrent elementor-framework changes (companion release)
- `schemas/parts/wrapper-settings.schema.json` — `cols.default` changed from `null` to `"1fr"` so every wrapper emits inline `--ef-cols: 1fr` by default, defeating CSS-custom-property inheritance.
- `assets/css/base.css` — wrapper-base rule resets `--ef-cols / --ef-cols-tablet / --ef-cols-mobile` to `initial` on every wrapper; media queries use `var(--ef-cols, 1fr)` fallback. Prevents nested-grid inheritance bugs where a parent's `--ef-cols: 2fr 1fr` leaked into children.
- `includes/envelope-builder.php` — new `EF\Envelope` class with typed factories for every atomic envelope: `string()`, `responsive_string()`, `vx_string()`, `image()`, `vx_visibility()`, `vx_rule_dtag()`, `vx_loop()`, `link()`, etc. Plus `validate()` for pre-write envelope checking and `comparator_for_subfield()` that picks `contains` vs `is_equal_to` from the Voxel field type. Mutator scripts can no longer hand-author malformed envelopes.

### Production lessons (institutional memory)
- Action_Row extends Loopable_Row; the SSOT artifact does NOT list the auto-merged props. Cross-reference `ef-parts.md` §Actions §Loop expansion, NOT `widget-schemas.json` alone.
- `canals.canal_type` is a taxonomy → array value `["phone"]`. `is_equal_to "phone"` silently evaluates false. The data-wiring persona now flags this; the new `comparator_for_subfield()` helper picks the right one.
- `@post(<work-hours-field>) is_not_empty` doesn't evaluate true for structured-array field types. Prefer letting the `ts-*` widget handle emptiness OR gate on a scalar sub-key.

### Component-standard evaluation (recorded no-build decision — no files added)
Applied the `plugin-dev:hook-development`, `plugin-dev:mcp-integration`, and `plugin-dev:plugin-settings` standards to the plugin. Outcome: **all three component types are not warranted.** No `hooks/hooks.json`, `.mcp.json`, or `.claude/voxel-builder.local.md` were added; the manifest version is unchanged because no component shipped. The decision is the deliverable — recorded here so it is re-auditable rather than silently skipped.
- **Hooks — not warranted.** The strongest candidate was a `PostToolUse` Bash hook to auto-run CSS regen + cache purge after `elementor:import` / `wp eval-file` (the "forgot to regen CSS" gap from the cosmetic-labs rebuild). That gap is **already structurally closed in the `wpdev` CLI** — the correct layer per the workspace CLAUDE.md "CLI-first" + "doubt every special case" doctrines: `wpdev elementor:mutate` runs `lint → regen CSS → purge` atomically (`cli/src/commands/elementor/mutate.ts`); `wpdev elementor:import --save` runs the editor-equivalent save + per-post CSS regen (`cli/src/commands/elementor/import.ts`); `wpdev rebuild --only css|purge` is the site-wide path. The protocol already mandates these post-write steps (`references/command-surface.md` §write+verify, `references/elementor-build.md` Phase 5/6, success-criteria checklist). A `Bash`-matching `PostToolUse` hook would fire on **every** Bash call in **every** repo where the plugin is installed (the matcher cannot be scoped to "a voxel write just happened"), duplicate logic already behind one CLI verb, and re-introduce the exact special-case the CLI was refactored to remove. `PreToolUse` lint-gating is already enforced in-prompt by the eight rules; `SessionStart` PATH checks are covered by `scripts/verify-install.sh`; `Stop` is overreach for a one-post-at-a-time HITL tool. Re-confirms the 0.1.0 hooks rejection (prompt-type `PreToolUse` hooks previously blocked legitimate recovery writes — `feedback_pretooluse_prompt_hooks.md`).
- **MCP — not warranted.** The plugin **consumes ambient, workspace-level MCP servers** (`mcp__mysql__*`, `mcp__elementor__*`, `mcp__crawl4ai__*`, `mcp__playwright__*`) plus the `wpdev` CLI for every read/write surface. A plugin-bundled `.mcp.json` would **duplicate** workspace config, risk version/credential drift, and spawn redundant server processes. No plugin-specific external service exists that the ambient servers + CLI don't already cover, so none *should* exist. Re-confirms the 0.1.0 MCP rejection.
- **Settings (`.claude/voxel-builder.local.md`) — not warranted.** Every candidate (default site, example-post sample size, auto-prune-revisions, archetype defaults) is already a per-invocation argument or a universal skill default, not project-stable state. `<site>`/`<post_id>` are required command args — a "default site" is a foot-gun on a multi-site workspace where deploying to the wrong site is explicitly dangerous (CLAUDE.md deploy guardrails). Sample size and archetype are decided per-page by the page-planning pipeline; revision pruning is already a mandatory Phase 0 audit step. A settings file would add a parse-and-restart surface and a "which value won?" failure mode for zero behavioral gain.

### Added — maintainer DX toolchain (`scripts/`)
- `scripts/lib.sh` — shared helpers sourced by every script: plugin-root resolution (from the script's own location, install-location-independent), version readers (`plugin_version` / `plugin_name` / `changelog_top_version`), conventional-commit → Keep-a-Changelog section mapping (`cc_section`), and the pass/fail/warn output plumbing. Single source for "where is the plugin / what version are we."
- `scripts/lint.sh` — authoring-correctness gate that codifies the manual plugin-dev skill audits: manifest validity + required fields + kebab-case name; **version coherence** (plugin.json `.version` must equal the CHANGELOG top header); no hardcoded absolute/`~` paths in docs; no plugin-version stamps drifting in README/AGENTS; all `${CLAUDE_PLUGIN_ROOT}` references resolve; README command/agent counts match the actual `commands/` + `agents/` file counts; every command has `description`, every agent has `name`/`description`/`tools`/`model`, SKILL.md has `name`/`description` and is ≤500 lines. Would have caught the README "v0.4.0" + marketplace drift automatically. Exit 1 on any FAIL.
- `scripts/changelog.sh` — generates a Keep-a-Changelog draft from the conventional commits touching the plugin since the last `voxel-builder-vX.Y.Z` tag (`feat→Added`, `fix→Fixed`, `refactor/chore/perf/docs/test→Changed`; `wip` checkpoints skipped). Prints to stdout; never writes a file.
- `scripts/release.sh` — version-bump orchestrator: lint gate (hard) → compute next version from `patch|minor|major` → bump plugin.json → insert the generated changelog draft under the top header → re-lint for coherence → print the commit + `git tag voxel-builder-v<version>` steps. The only writer of the version, so plugin.json and the CHANGELOG header cannot drift.
- `scripts/verify-install.sh` — refactored to source `lib.sh`; still owns the distinct **runtime**-prerequisite concern (`wpdev`/`jq` on PATH, ≥1 local site) separate from `lint.sh`'s authoring checks.
- **Version SSOT now enforced:** plugin.json `.version` is the sole machine-readable version; CHANGELOG headers are the human history; `lint.sh` fails on any divergence. The README + marketplace stamps that had drifted to `v0.4.0` (while the plugin was 0.5.1) were removed and are now lint-prevented from recurring.
- `.github/workflows/voxel-builder-lint.yml` — CI gate (mirrors the repo's `ef-codegen-drift` pattern) that runs `scripts/lint.sh` on every PR touching `claude-plugins/plugins/voxel-builder/**`. Pure POSIX sh + `jq`, no Bun/wpdev/DB. Makes the drift classes (version mismatch, hardcoded paths, stale README counts, missing frontmatter) **unmergeable** — the lint gate now runs automatically, not just on demand. Verified to catch injected version drift (exit 1) and pass clean on revert; runs green under dash (CI's `sh`).

## [0.5.0] - 2026-05-28

Page-planning sub-pipeline + parallel adversarial plan review + migration-mode content preservation. Closes the "thin template" failure mode (single-`ef-card`-at-root with N CPT fields unsurfaced) by gating Phase 2 of the build workflow (`workflows/build.md`) (and the migration flow) on an explicit Plan Document that 7-8 named persona reviewers attack in parallel before fan-out. Migration mode further binds preservation to the **production page's rendered markdown** (via `mcp__crawl4ai__md`), not the legacy `_elementor_data` dump — V3 wrapper noise + plugin pollution stop producing false-positive "missing content" findings.

Also includes a corpus-wide quality pass across all 44 markdown surfaces: phantom CLI commands purged (`elementor:strip:card-wrappers` → `strip:wrappers`; non-existent `migrate:buttons` / `migrate:icon-heading` / `rollback` removed), phantom widget catalog rebuilt in `voxel-platform.md` (6 fictional `ts-*` names replaced with 6 real ones), `voxel-field-types.md` `conditions`/`visibility_rules` shapes corrected against theme source, `voxel-search.md` connection model rewritten (`vx_group`/`vx_target`/`vx_side` → real `ts_post_to_feed` / `connect_map`), `voxel-timeline.md` DM widget name + chat URL format + Follow constants corrected, `tags.md` reframed from legacy ribbon/color model to current pills-with-variant-tokens SSOT, `ef-helpers.md` retired 11 helpers + fixed file-path drift across loop/voxel/dynamic-tags/forms/admin/smtp.

### Added
- `agents/voxel-plan-reviewer.md` — single-persona adversarial reviewer dispatched in parallel (one persona per Task() call, atomic-scope contract). Eight personas: `coverage`, `density`, `hierarchy`, `data-wiring`, `pattern-reuse`, `relations`, `ssot-integrity`, `migration-preservation`. Read-only — never patches the plan, never writes `_elementor_data`. Tools list excludes `Write` by construction; includes `mcp__crawl4ai__md` for the migration-preservation persona.
- `skills/voxel-builder/references/page-planning.md` — mandatory Phase 2 sub-pipeline: Field Inventory (§2a) → SSOT Read (§2b) → Archetype Selection (§2c, 12-archetype catalog: hero / brief / specs-grid / detail-tabs / detail-accordion / sidebar-contact / sidebar-map / sidebar-schedule / relation-feed / faq-accordion / related-cpt-feed / cta-footer — each row pins wrapper-tag + default grid + responsive collapse + first-heading + internal heading-tag policy) → Section Blueprints (§2d — three artifacts per section: Improvements log [migration only], **Layout map** [section wrapper props + responsive grid tracks + per-widget placement with col/row span + mobile stack order], Blueprint [widget × settings × tag-wrap × **Dynamic affordance per prop** × role × Expected DOM × Pre-resolved values]) → adversarial review (§2e, 7 build / 8 migration personas) → reconciliation (§2f) → operator `APPROVED` (§2g). Exit blocked until the Plan Document at `/tmp/plan-<post_id>.md` validates and every finding is addressed or carries an explicit `override:` line.
- **Semantic HTML hierarchy** enforced by the `hierarchy` persona: exactly ONE root `ef-wrapper` with `tag: main`; each top-level section is its own `ef-wrapper` with `tag: section` (sidebars: `aside`); wrapper tag matches the §2c archetype catalog; `tag: div` at depth ≤ 2 is flagged as a missed semantic-tag opportunity.
- **SEO-compliant heading-tag policy** enforced by the `hierarchy` persona: exactly ONE `h1` on the hero card bound to the CPT's title-class field; each section's first heading-row is `h2`; nested headings are `h3` with no h2→h4 skips; **decorative content (eyebrows / byline labels / taxonomy pill labels / CTA labels) NEVER uses `h*`** — must be `tag: span` with `style: byline_label` or `tag: p`. The persona walks document-order and emits findings on every violation.
- **Layout map** §2d block: Section wrapper props (tag / `_cssid` / section width / background / vertical rhythm / sticky) + responsive Grid tracks table (desktop / tablet / mobile track strings with row+column gaps) + per-Blueprint Widget placement table (column / col-span / row-span / mobile stack order). The Layout map keeps grid declarations OUT of the Blueprint Settings column — the orchestrator splices grid props into the EF V4 envelope at fan-out.
- **Dynamic-affordance audit** in the `data-wiring` persona: every Settings cell with a dynamic tag must declare its prop affordance `on` in the new `Dynamic affordance` Blueprint column; static literal + affordance `on` flags wasted runtime; dynamic tag + affordance `off` flags the classic `@post(title)` @-leakage bug.
- **Improvements log** §2d block (migration mode): the planner declares every divergence from production as `improvement:<unit_id> → <new text>` or `removed:<unit_id> → <reason>`. The `migration-preservation` persona enforces "every production information unit either appears in some Blueprint cell OR is acknowledged in the Improvements log" — improvements are first-class, only silent drops fail. Information units (claims / facts / offers / CTAs / features / services / prices / instructions / headings) replace word-set / sentence-set comparison — typo fixes, copy modernization, and tightening are encouraged, not flagged.
- `skills/voxel-builder/references/migration.md` — migration pipeline (legacy V3 → EF V4 atomic) with the Iron Law "aggressive on structure and styling, paranoid on rendered content (the words a visitor sees)." DROP / PRESERVE / CONVERT taxonomy; content baseline = production-rendered markdown, not the legacy dump.
- Migration-preservation persona uses `mcp__crawl4ai__md` to fetch the live production page; URL resolution via `./wpdev remote:list` + `?p=<id>` (WordPress core 302-redirects any post type to its canonical permalink, no permalink-template knowledge required).
- Rule 8 in `references/seven-rules.md` — page-planning gate (filename stays historical; one new rule added — file now ships eight rules). Success-criteria checklist extended with 7 new boxes covering the §2a–§2g pipeline + APPROVED-verbatim gate.
- `skills/voxel-builder/SKILL.md` — new "When NOT to use" section (non-Voxel sites, generic V3 outside the EF framework, single-widget surgical patches, preview cards via `/cards`, schema introspection via `/schema`).

### Changed
- `commands/elementor-build.md` — Phase 2 now delegates to `page-planning.md` §2a–§2g; Phase 3 fan-out reads the approved Plan Document blueprints verbatim. Phase 0 (revisions audit) split out explicitly; Phase 5 write gated on the literal `APPROVED` line.
- `references/elementor-build.md` — build pipeline reframed as gather → plan (via page-planning) → fan-out → assemble → write → verify. Phantom CLI commands purged across mutation-tool table.
- `AGENTS.md` — dispatch graph extended with plan-review fan-out arrows (build → 7 personas; migration → 8 personas; fixer → page-planning when fix adds sections); SSOT-first ordering corrected in shared anti-patterns.
- `skills/voxel-builder/SKILL.md` — description rewritten with trigger keywords for all 4 buckets (audit / migration / CPT / build) + explicit "NOT for" scoping; mandatory-reads section gains page-planning.md; Subagents table grows to 5 (adds `voxel-plan-reviewer`); Migration row in Reference Index reframed as content-words preservation + crawl4ai baseline.

### Fixed
- 44-surface quality pass; ~93 Critical + ~93 Major fixes applied across SKILL.md, 28 references, 5 agents, 6 commands, AGENTS.md, README, examples/README, CHANGELOG. Major patterns: phantom CLI commands purged; phantom widgets unflagged; wrong shapes (`conditions` / `visibility_rules` / `ts-*` connection model / Follow constants / chat URL); `seven rules` → `eight rules` residue swept; SSOT-first ordering enforced; page-planning §2 entry wired into every build/migration/fix reference.

### Notes
- the migration workflow (`workflows/migrate.md`) slash command still routes through the build workflow (`workflows/build.md`) (the migration flow is mode-selected by the build command); a dedicated command file will land in 0.5.x if migration use grows.

## [0.4.0] - 2026-05-26

Detection hardening + selective discipline transfer. Leads with turning four production-proven *silent* failure modes into mandatory auditor probes (closing false-negatives — the real session-burners), then adds only the discipline that earns its keep in a HITL workflow. Deliberately lean: cross-reviewer promotion, the 5-anchor confidence enum, pressure scenarios, and `--resume` were evaluated and **cut** (dead-by-construction or theater-without-a-falsifier — see the plan's Scope Boundaries).

### Added
- `references/behavior-contract.md` — pre-mutation gate for existing-`_elementor_data` fixes: the triple (Behavior Contract / Allowed Structural Delta / Forbidden Semantic Delta) backed by a mechanical falsifier — a DOM-text baseline of the affected widgets' data-bound props, captured **before** mutation and diffed by the post-fix re-audit. Authored by the **command-host** (not the fixer) for real author≠repairer≠reviewer separation. `behavior_contract_class`: `structural_only` | `observable_delta` | `bug`; `bug` routes to a generic debugging workflow (no `/ce-debug` hardcode — standalone-safe). No baseline → no fix.
- `references/audit.md` §Silent-failure detection probes — four mandatory `[G]`/`[W]` checks for render-valid-but-wrong regressions that lint and screenshots miss: relation-loop self-traversal (`@post(<rel>.<field>)` inside a `_vx_loop` over the same `<rel>`), CSS-token fallback drift (`var(--ef-token, <drifted-fallback>)`), reindex-after-filter (filter change without `voxel:reindex --recreate`), and unicode corruption (literal `u00e9`). Each cites its `docs/solutions/` source and emits `suspected` with an `sme_question` until calibrated — over-firing routes to human review, never blocks.
- `references/audit.md` Phase 4 — `## Suspected (needs verification)` report bucket; finding model gains a 2-value `confidence: confirmed | suspected`.
- `references/audit-briefs.md` — Confidence-codes section; Section + Widget brief return formats gain `confidence` + a `sme_question` (mandatory when `suspected`); relation-loop self-traversal probe added to both briefs' loop checks.

### Changed
- `agents/voxel-page-auditor.md` — step 5 aggregate gains the confidence gate (a `suspected` finding with no `sme_question` is rejected back to the subagent); step 6 emit carries `confidence` + `sme_question`; anti-patterns forbid numeric scores, `fingerprint`, and cross-agent promotion (impossible under atomic scope).
- `agents/voxel-elementor-fixer.md` — accepts the Behavior Contract + baseline as **read-only** inputs (never authors them); pre-fix reads the contract and confirms the baseline exists; the re-audit diffs new DOM-text against the baseline as the Forbidden-Semantic-Delta check (violation → roll back).
- `commands/audit.md` — command-host now authors the Behavior Contract + captures the baseline before dispatching the fixer for existing-data fixes; classifies each fix and gates `observable_delta`/`bug`.
- `references/elementor-build.md` §Modifying existing data — Behavior Contract + baseline documented as a mandatory pre-mutation gate.
- `references/seven-rules.md` — one-line pointer to the silent-failure detection probes.
- `.claude-plugin/plugin.json` — version 0.3.0 → 0.4.0.

### Deferred (premise-gated, not built)
- **Size-gated audit-file persistence** — premise unverified at ship time: `docs/audits/` holds 0 voxel-page-audit files, so the `/compact`-survival pain is hypothetical at this tool's one-post-at-a-time scale. Revisit in v0.4.1 if a real large audit confirms the pain (then `--resume` becomes viable too).

## [0.3.0] - 2026-05-26

### Added — exhaustive reference coverage
- `references/voxel-field-types.md` — complete catalog of all 33 Voxel field types (PHP class, type-key, required+optional config, validation, dynamic-tag exposure, JSON templates, gotchas). Coverage: 22% → 100%.
- `references/voxel-timeline.md` (410 lines) — Timeline, Reviews, Comments, Direct Messages, Notifications, Follows.
- `references/voxel-commerce.md` (527 lines) — Product Types, Bookings, Paid Memberships, Paid Listings, Claim Listings, Promotions, Stripe/Paddle/PayPal at API-surface depth.
- `references/voxel-search.md` (430 lines) — Search filters (15 types), sort clauses (12 types), Index Table mechanics, Maps + Geocoding, Recurring Dates + Work Hours.
- `references/voxel-platform.md` (670 lines) — Post Types deep contract, Taxonomies, Roles, Collections, full Voxel-native widget catalog (30+ ts-* widgets), Post Relations, Verification, File Uploader, Statistics, Dynamic Data engine, Async Jobs, Privacy, Nav Menus, Library, Text Formatter, Auth, Print Templates.
- `references/ef-widgets.md` (255 lines) — All 6 EF widgets (ef-card, ef-cal, ef-form, ef-navbar, ef-toc, ef-wrapper) with full schema, parts used, Twig context, asset handles. Coverage: 50% → 100%.
- `references/ef-parts.md` (441 lines) — All 16 EF parts catalogued (Action_Slot, Actions, Banner, Field, Headings, Icon, Media, Nav_Item, Tags + base contracts + media sub-handlers + nav helper traits). Coverage: 0% → 100%.
- `references/ef-helpers.md` — 261 `ef_*` helpers (128 full-doc with signatures + examples, 108 indexed). Coverage: 0% → 90%.
- `.gitignore` (.DS_Store / swap files)

### Changed
- `SKILL.md` — description trimmed to ≤200 chars per Jesse Vincent's trigger-conditions-only rule; reference index extended with 9 new entries; new "Pick the right reference for your task" sub-table.
- `references/dynamic-text.md` — trimmed from 521 to ≤400 LOC; modifier catalog inlined to remove cross-repo `docs/solutions/` dependencies.
- `references/widgets.md` — refactored to ~80-line router; per-widget detail moved to `ef-widgets.md`.
- `references/blueprint-format.md` — reduced to thin pointer at `voxel-field-types.md`; skeleton CPT shape kept.
- `references/wpdev-coverage.md` — added ~15 missing verbs (elementor:set-cssid, elementor:set-value, elementor:migrate:loop-index, elementor:unwrap, elementor:ef:*, elementor:styles:*, strip:card-wrappers); refreshed against live `./wpdev --help`.
- `references/command-surface.md` — same sweep; added inbound link to `wpdev-coverage.md`.
- All prose updated from `/voxel:*` → `/voxel-builder:*` to match actual slash-command names.
- `.claude-plugin/plugin.json` — version 0.3.0; description trimmed to ~120 chars; added `homepage`, `repository`, `category`; resolved author email; expanded `keywords`.

### Fixed
- **P0-1** Slash-command name format — removed `name:` from command frontmatter; prose now uses `/voxel-builder:*` namespace matching actual derived command names.
- **P0-2** Install paths corrected: `claude-plugins/voxel-builder/` → `claude-plugins/plugins/voxel-builder/` in README.md (3 lines), examples/README.md (4 lines), CHANGELOG.md (1 line).
- **P0-3** README `[CLAUDE.md](../../CLAUDE.md)` link fixed to `../../../CLAUDE.md`.
- **P0-4** Agent `tools:` lists — replaced `Agent` (non-existent tool) with `Task` (correct dispatch primitive) in `voxel-page-auditor.md` + `voxel-elementor-fixer.md`.
- **P0-5** Removed false advertisement of `wpdev voxel:fields --add` (the flag doesn't exist); blueprint-edit + reimport documented as canonical.
- **P0-6** Stripped 6 phantom widgets from `widgets.md` (ef-media, ef-button, ef-buttons, ef-breadcrumb, ef-button-group, ef-map-pin, ef-map — none exist in the codebase).
- **P0-7** Naming consistency: `elementor:strip-card-wrappers` → `elementor:strip:card-wrappers` across 4 files (commands/elementor-build.md, references/audit.md, references/elementor-build.md, references/widgets.md).

### Coverage gains
- Voxel field types: 22% → 100% (33/33)
- Voxel features: <30% → 100% (36/36 at API-surface depth)
- EF widget coverage: 50% → 100% (6/6 actual widgets; phantom widgets removed)
- EF parts: 0% → 100% (16/16)
- EF helpers: 0% → ~90% effective (128 full-doc + 108 indexed of 261 total)
- Cross-repo doc dependencies: 7+ → 0 (plugin is now standalone)

## 0.2.0 — 2026-05-05

Broadens the skill's wpdev CLI footprint from ~14 commands to **34 of ~46** plugin-relevant verbs. The audit, fix, CPT-lifecycle, and schema-introspection pipelines now invoke the wpdev capabilities they previously claimed to use but didn't. v0.1's six slash commands and four subagents stay byte-stable in name and frontmatter — the changes are inside their decision trees and the references they cite.

### Added

- **`references/wpdev-coverage.md`** — structured coverage map of every wpdev command in the `voxel:`, `elementor:`, `audit*`, `schema:*`, `cache:*`, `render:*`, `headings`, `quality` namespaces with a closed-set status taxonomy (`surfaced` / `surface-pending` / `out-of-scope` / `defer`). Companion to `command-surface.md` (prose cheatsheet) — this is the audit table that catches drift.

### Audit pipeline (`voxel-page-auditor`, `audit.md`)

The `[G]`-tier global walk gains 6 new wpdev sources, each tagged with the command in the aggregated report:

- `wpdev voxel:status` — CPT index health. Non-`OK` is now a `[G-C]` Critical finding.
- `wpdev elementor:structure --type <post_type>` — `<main>`/`<header>`/`<section>` semantic compliance.
- `wpdev elementor:semantic <post_id> --headings` — heading-hierarchy + structural analysis (per-post).
- `wpdev elementor:widgets [--migrate]` — widget rarity findings + legacy-widget detection (the `--migrate` hits feed Pass 2 schema-churn forks in the fixer).
- `wpdev voxel:empty` — unused blueprint fields surfaced as Improvement findings.
- Unicode corruption probe via `wpdev elementor:dump | grep -E 'u00[0-9a-f]{2}'` — Critical finding when hits land outside legitimate contexts (CSS escapes, encoded URLs).

### Fix pipeline (`voxel-elementor-fixer`, `elementor-build.md`)

Pass 2 (section / layout mutations) gains 6 new mutation tools, each gated by audit findings:

- `elementor:strip:wrappers --fix --yes` — redundant nested wrappers (companion to `strip:card-wrappers`).
- `elementor:strip:styles --fix --yes` — per-node style overrides → globals.
- `elementor:fix-unicode -y` — site-wide unicode fix; CLI has no `--post` filter, so the protocol calls it once per fix-loop after a global `revisions:prune` snapshot.
- `elementor:migrate-buttons --post <id> --yes` — `EF_Part_Buttons` → `EF_Part_Actions` (schema-churn fork point).
- `elementor:migrate-icon-heading --post <id> --yes` — retired `ef-icon-heading` widget → `ef-card` heading (schema-churn fork point).

### CPT lifecycle (`commands/cpt-fields.md`, `cpt-lifecycle.md`)

- **the CPT lifecycle Phase 2 (`workflows/cpt-lifecycle.md`)** mandates `voxel:reindex` + `voxel:cache clear` + `voxel:status` as numbered protocol steps 5-8 (was a parenthetical mention in v0.1). Halts if `voxel:status` returns non-`OK`.
- **Phase 2** in `cpt-lifecycle.md` mirrors the same mandatory sequence.
- **Phase 4 schema markup** rewritten as a concrete protocol around `wpdev schema:get`, `wpdev schema:set @<file>`, `wpdev schema:validate`, and `wpdev schema:validate-live`. Phase 4 does not exit until `validate-live` returns clean — silent JSON-LD malformation is no longer possible.

### Schema introspection (`voxel-schema-detective`)

The decision tree gains 4 new routes:

- `widget="status"` → `wpdev voxel:status`.
- `widget="templates"` → fans out to both `wpdev voxel:templates` and `wpdev elementor:templates`.
- `widget="usage"` → `wpdev elementor:widgets`.
- `widget="usage" + prop="migrate"` → `wpdev elementor:widgets --migrate`.

### Cheatsheet (`command-surface.md`)

- Reorganized into 6 sections: CPT introspection, Widget / data introspection, Audit (read-only), Write + verify, Fix-loop mutations, Schema (lean-seo).
- Adds 18 new wpdev verbs to the prose reference: `voxel:status`, `voxel:page`, `voxel:empty`, `voxel:reindex`, `voxel:cache`, `voxel:backfill-authors`, `elementor:templates`, `elementor:widgets`, `elementor:structure`, `elementor:semantic`, `audit`, `elementor:strip:wrappers`, `elementor:strip:styles`, `elementor:fix-unicode`, `elementor:migrate-buttons`, `elementor:migrate-icon-heading`, `schema:get`, `schema:set`, `schema:validate`, `schema:validate-live`.

### Out of scope / deferred (rationales in `wpdev-coverage.md`)

Out-of-scope (won't surface in this skill): `voxel:delete`, `elementor:create`, `elementor:export`, `schema:delete`, `quality`.

Deferred (revisit when usage justifies): `voxel:export`, `elementor:anchors`, `elementor:animations`, `elementor:rename`, `elementor:styles`, `audit:ai`, `audit:density`, `schema:compile`, `schema:export`, `schema:import`, `smoke`, `headings`.

### Notes

- No new slash commands or subagents. The v0.1 surface (6 commands, 4 agents) is sufficient — this release fills decision trees, not the roster.
- `elementor:fix-unicode` reality check: the CLI is site-wide only (no `--post` flag, just `--yes`). The audit-mode probe falls back to a regex grep on `elementor:dump` output instead of a hypothetical `--dry --post` invocation.
- Reference plugin contents (the 11 preserved 2026-EF-state references from v0.1) stay verbatim. Only `audit.md` (Phase 3A `[G]`-tier list), `elementor-build.md` (mutation tool table), and `cpt-lifecycle.md` (Phase 2 + Phase 4) gained content.

## 0.1.0 — 2026-05-05

Initial release. Promoted from the workspace-only skill at `.claude/skills/voxel-builder/`.

### Added

- **Plugin manifest** at `.claude-plugin/plugin.json` (name, version, description, author, license, keywords).
- **Six slash commands** under `commands/`:
  - the audit workflow (`workflows/audit.md`) — top-down audit walk, dispatches `voxel-page-auditor`.
  - the CPT lifecycle (`workflows/cpt-lifecycle.md`) — full 7-phase CPT lifecycle.
  - the CPT lifecycle Phase 2 (`workflows/cpt-lifecycle.md`) — Phase 2 only (modify existing CPT blueprint).
  - the build workflow (`workflows/build.md`) — parallel-atomic build pipeline.
  - the cards flow (`workflows/build.md` §Cards) — scaffold preview cards via `wpdev voxel:cards`.
  - the schema introspection flow (dispatch the `voxel-schema-detective` subagent — `references/subagents/voxel-schema-detective.md`) — read-only schema / fields / dump introspection.
- **Four subagents** under `agents/`:
  - `voxel-page-auditor` — read-only audit orchestrator (sonnet).
  - `voxel-elementor-fixer` — build orchestrator with bottom-up fix loop (sonnet).
  - `voxel-widget-builder` — atomic widget specialist, either mode (sonnet).
  - `voxel-schema-detective` — read-only introspection leaf (haiku).
- **One skill** under `skills/voxel-builder/`:
  - `SKILL.md` rewritten as a thin router (76 lines vs the prior 150-line monolith).
  - Three new reference files extracted from the prior SKILL.md:
    - `references/seven-rules.md` — the seven rules + success-criteria checklist.
    - `references/command-surface.md` — full `wpdev` CLI cheatsheet.
    - `references/parallel-dispatch.md` — atomic-scope subagent contract (consolidates content previously scattered across SKILL.md rule 4, `audit.md`, and `audit-briefs.md`).
  - Eleven preserved reference files kept byte-identical except for the `widgets.md` tail, which absorbed the "EF schema churn" + "Recent EF surface changes" sections from the prior SKILL.md (their content was already widget-shape commentary).
- **Three golden fixtures** under `examples/` extracted via `wpdev elementor:dump klarc`:
  - `ef-card.json` (post 2023, single-post template card).
  - `ef-wrapper.json` (post 2023, top-level `<main>` wrapper).
  - `ts-post-feed.json` (post 2025, Voxel-theme widget — the only one whose shape can't be introspected via `elementor:schema`).
  - `examples/README.md` documents the refresh workflow.
- **Verify-install script** at `scripts/verify-install.sh` (POSIX shell). Confirms `wpdev`, at least one local site, and optionally `jq`.
- **Documentation**: `README.md`, `AGENTS.md`, `LICENSE` (MIT).

### Migrating from the workspace skill

| Old path / mechanism | New home |
|---|---|
| `.claude/skills/voxel-builder/SKILL.md` (full 150-line file) | `claude-plugins/plugins/voxel-builder/skills/voxel-builder/SKILL.md` (76-line thin router) |
| SKILL.md "Seven rules" section | `references/seven-rules.md` |
| SKILL.md "Shared command surface" code block | `references/command-surface.md` |
| SKILL.md "EF schema churn" + "Recent EF surface changes" | Folded into `references/widgets.md` |
| SKILL.md "Success criteria" checklist | `references/seven-rules.md` (bottom) |
| Routing row "Audit page" | the audit workflow (`workflows/audit.md`) slash command, dispatches `voxel-page-auditor` |
| Routing row "Create CPT" | the CPT lifecycle (`workflows/cpt-lifecycle.md`) slash command |
| Routing row "Add fields to existing CPT" | the CPT lifecycle Phase 2 (`workflows/cpt-lifecycle.md`) slash command |
| Routing row "Build/modify elementor data" | the build workflow (`workflows/build.md`) slash command |
| Routing row "Scaffold preview cards" | the cards flow (`workflows/build.md` §Cards) slash command |
| Ad-hoc `general-purpose` subagent dispatch with copy-pasted briefs | Named agents (`voxel-widget-builder`, `voxel-page-auditor`, `voxel-elementor-fixer`, `voxel-schema-detective`) with description-triggered routing |
| Schema synthesis as a fallback when `wpdev elementor:dump` produces unfamiliar output | Three golden fixtures shipped under `examples/` so synthesis is never the right answer |

### Notes

- Hooks were considered (PreToolUse warnings before `_elementor_data` writes without a recent schema query) but skipped — `feedback_pretooluse_prompt_hooks.md` documents the prior failure mode where prompt-type hooks blocked legitimate writes during recovery work. The seven rules in `references/seven-rules.md` enforce the same discipline in-prompt without blocking valid operations.
- No MCP server bundled — the `wpdev` CLI plus the existing `mcp__elementor__*` and `mcp__mysql__*` MCPs cover every read/write surface.
