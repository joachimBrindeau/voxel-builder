# Site Port Workflow

Port one Elementor page, Voxel template, reusable section, or widget from a source site
to a target site. Preserve useful structure, but rebuild site-owned meaning: language,
site focus, CPT bindings, field tags, referenced templates, post IDs, URLs, and media.

## Entry Criteria

- Source site and artifact resolve by post ID, URL, template role, saved section, or widget path.
- Target site and intended target artifact are identified.
- User requested mutation. For inspection only, use `audit.md`.
- Read `references/core/rules.md`, `references/core/criteria.md`,
  `references/core/command-surface.md`, `references/core/elementor-mutation-tools.md`,
  and `references/verification/browser.md`.

## Phase 1 — Inventory Both Sites

**Entry:** source and target identifiers resolve.

1. Capture both sites' language, purpose, brand vocabulary, relevant URLs, Elementor
   kit/tokens, active Voxel post types, and template assignments.
2. Inspect source with `wpdev elementor:tree` and `wpdev elementor:dump`. Inspect target
   too when replacing or merging existing data.
3. Read `_voxel_page_settings` for both artifacts. Treat page settings as source-owned
   state even when empty-looking; copy only understood keys and map site-local values.
4. Run `wpdev voxel:templates`, `wpdev voxel:fields`, and `wpdev voxel:sample` for each
   source CPT used and each plausible target CPT.
5. Run `wpdev voxel:data` on representative source and target records. Never infer field
   availability or value shape from labels.
6. Inventory dependencies in one pass: dynamic tags, CPT and field keys, relations,
   template/card/post/taxonomy/media IDs, URLs, CSS IDs, global tokens, shortcodes,
   queries, filters, and custom widget types.
7. Recursively inspect every referenced Elementor template/card. Continue until the
   dependency graph closes; a clean page payload does not prove its referenced templates
   are portable.
8. Flag implicit loop context: `_vx_loop` using `@site(loop_post)` while
   `_ef_loop_query.post_type` is blank, plus visibility rules comparing
   `@site(loop_post.type.slug)` to a source CPT. These require explicit target mapping.

**Exit:** evidence bundle contains both site profiles, Elementor trees, CPT/field
inventories, representative data, and complete dependency inventory.

## Phase 2 — Build Adaptation Manifest

**Entry:** Phase 1 evidence complete.

1. Create one mapping row per dependency with source value, semantic purpose, target
   value, evidence, transformation, fallback, and status.
2. Map CPTs by purpose and behavior, not slug similarity. Map fields by meaning, Voxel
   field type, cardinality, storage shape, and representative values.
3. Classify every source element as `preserve`, `translate`, `adapt`, `rebind`, `replace`,
   or `omit`.
4. For missing target fields, choose exactly one disposition: valid existing field,
   supported literal/fallback, omit dependent UI, or handoff to `cpt-lifecycle.md`.
   Never invent a field key or bind a merely similar field silently.
5. Mark unresolved rows `blocked`. Do not write while any critical row is blocked.
6. Give each implicit loop an explicit target CPT whenever the target artifact is not
   guaranteed to run inside the same archive/search context. Remove source-CPT visibility
   gates when the explicit query already provides the required scope.
7. Decide whether referenced templates are preserved, recursively ported, replaced, or
   inlined. A numeric target ID without dependency-level evidence is not a valid mapping.

**Exit:** manifest accounts for every dependency and visible-content block; all critical
rows have evidence-backed target values.

## Phase 3 — Produce Target Blueprint

**Entry:** no critical manifest row blocked.

1. Convert source tree into target blueprint using `build.md` conventions and target
   widget schemas. Source JSON is evidence, not a write-ready payload.
2. Apply target language to headings, labels, buttons, forms, empty states,
   accessibility names, validation text, and SEO-facing copy.
3. Adapt narrative and CTAs to target audience, offering, geography, and conversion goal.
   Do not use word-for-word translation when site focus differs.
4. Rewrite every site-local reference from manifest. Preserve Elementor element IDs only
   when scoped CSS/JS requires them and they are collision-free.
5. Validate widgets and props against current target schemas. Remove unsupported source
   settings instead of carrying dead or unknown props.

**Exit:** blueprint contains no unresolved source IDs, URLs, CPT/field keys, media IDs,
or untranslated visible copy unless explicitly preserved.

## Phase 4 — Safety Gate And Write

**Entry:** blueprint and manifest pass review.

1. Present source, target, create/replace/merge mode, omissions, schema handoffs, and
   fallbacks. Get confirmation when replacement scope or lossy omission was not explicit.
2. Capture target rollback evidence. Apply revision snapshot/prune requirements from
   `references/core/rules.md` before non-trivial existing-template changes.
3. Prefer supported `wpdev elementor:*` mutation commands. Assemble and write once;
   never mutate source site.
4. Read target data back immediately. Compare structural counts and every critical mapped
   value against blueprint and manifest.
5. Save reusable ports as library templates when requested. Keep the final page and each
   recursively ported dependency independently lintable and rollbackable.

**Exit:** target stores intended artifact, rollback exists, source remains unchanged, and
read-back matches critical mappings.

## Phase 5 — Static And Data Verification

**Entry:** write read-back passed.

1. Run `wpdev elementor:lint <target> --post <id>`. Resolve unknown widgets/props, type
   mismatches, malformed tags, and invalid referenced post IDs.
2. Re-run `wpdev voxel:data` for representative target records. Prove each dynamic binding
   resolves with correct target shape or declared fallback.
3. Search written data for source domain, source-only IDs, source CPT/field keys, leaked
   `@post(...)` text, untranslated strings, and Unicode corruption.
4. Run the same leak scan against every newly created referenced template, not only the
   target page.
5. Open/save in Elementor when required, regenerate CSS/assets, then purge caches through
   supported `wpdev rebuild` flow.

**Exit:** lint passes, dependency leak scan is clean, and data bindings resolve.

## Phase 6 — Render Verification And Handoff

**Entry:** Phase 5 passes.

1. Verify target at desktop and mobile widths with a unique browser session.
2. Check selectors, headings, language, focus, CTAs, dynamic values, forms/filters, links,
   media, responsive layout, console errors, page errors, and literal tag leakage.
3. Assert expected loop cardinality. Count rendered feed/card items and compare with the
   source behavior or manifest; one featured item does not prove the recent-feed loop ran.
4. Verify content after every loop. Check the next sibling section's heading, copy, form,
   and CTA because loop context leakage can silently empty later static cards.
5. For CPT templates, test representative target records including one sparse record to
   prove fallbacks and conditional visibility.
6. Detect visible fixed overlays/drawers and compare the untouched source before assigning
   ownership; shared header defects must be reported separately from the port verdict.
7. Capture and read screenshots. Compare with source only for intentionally preserved
   structure; target correctness outranks pixel identity.
8. Report target IDs, manifest summary, omissions/fallbacks, evidence, and named handoffs
   to `cpt-lifecycle.md`, `curation.md`, `content-generation.md`, `image-generation.md`,
   or `settings.md`.

**Exit:** target renders in target language and focus, uses valid target CPT fields and
dependencies, passes runtime checks, and contains no accidental source-site residue.

## Failure Routing

- Missing target CPT or field schema: stop write; hand off to `cpt-lifecycle.md`.
- Target records need content rather than layout changes: hand off to `curation.md` or
  `content-generation.md` with exact fields.
- Missing target media: hand off to `image-generation.md`; never reuse source attachment IDs.
- Unknown widget or schema mismatch: use `audit.md` or source/plugin repair first.
- Ambiguous language, brand voice, or target focus: ask one focused question before copy mutation.
