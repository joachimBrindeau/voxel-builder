# Image generation workflow for Voxel / Elementor WordPress sites

Use this when generating featured images, hero images, OG/social images, schema images, or CPT/post thumbnails for Voxel/Elementor WordPress sites.

This workflow owns the Voxel/WordPress wiring and Joachim-specific quality gates. It does **not** duplicate global image-model logic. For model/tool behavior, backend usage, model tiers, cost, and prompt-engineering primitives, resolve the installed `seo-image-gen` capability first.

## Entry criteria

- Target is a Voxel/Elementor WordPress site or a Klarc-like site managed through the Voxel Builder workflow.
- Deliverable attaches images to WordPress content, not only local files.
- User wants unique, topic-specific, production assets.

## Phase 0 — backend smoke test

**Entry:** Entry criteria are met and no prompt batch has been authored.

1. Resolve `seo-image-gen` through the host's advertised skill catalog and invoke it
   natively when supported. Otherwise locate its `SKILL.md` through configured skill
   roots and follow it inline. Record the resolved source; if neither form is available,
   stop instead of substituting ad-hoc image-generation guidance.
2. Verify the actual generation backend is live in this session.
   - Preferred: NanoBanana MCP, Pro model (`gemini-3-pro-image-preview`) for Joachim/Klarc-quality work.
   - Check that generation tools are available before authoring a large batch.
   - If MCP absent, try the skill's direct fallback only if the required configured environment is present.
   - Do not assume a backend from a prior session is still attached.
3. Run one smoke-test image through the real backend.
4. If no backend is live, stop and report exact unblock options: reconnect MCP, set required API key/env, or add credits.

**Exit:** One generated smoke-test image exists, or the run is blocked plainly.

## Phase 1 — discover WordPress targets

**Entry:** Phase 0 proved a live backend.

1. Use project wrapper first when present, else `wp --path=/path/to/site`.
2. Confirm site with `wp core is-installed` and `wp option get siteurl`.
3. For Voxel CPTs or MCP schema bugs, query MySQL directly.
4. Collect `ID`, `post_type`, `post_title`, `post_name`, status, `_thumbnail_id`, attachment URL, alt text, file path.
5. For uniqueness, hash actual files on disk. Distinct attachment IDs are not enough.

**Exit:** Worklist has every target and a `needs_new` flag based on file hash, not DB ID.

## Phase 2 — concept and approval gate

**Entry:** Phase 1 target worklist is complete.

1. Use scene-first art direction, not prop shuffling.
2. Commit to a concept per image: who, where, action, topic anchors, composition, light, camera.
3. For batches over about 10 images, generate one family/core block first and build a labeled contact sheet unless user explicitly authorizes autonomous full run.
4. Brand colors are accents only, never an object prison.
5. Avoid generic law imagery and repeated oak-table / teal-folder / brass-token still lifes.

**Exit:** User approved direction, or explicitly chose autonomous full run.

## Phase 3 — prompt authoring

**Entry:** Phase 2 direction gate is approved.

1. Use `seo-image-gen` for global prompt-engineering structure.
2. Use the Voxel-specific reference `../references/voxel/image-generation.md` for Joachim/Klarc constraints.
3. For large sets, parallelize prompt authoring with subagents only. Leaf subagents write family JSON prompt files; they do not generate or QA.
4. Verify every prompt file exists, parses as JSON, and count/IDs match input before generation.
5. Each prompt must demand: photoreal scene, concrete action, varied camera, no readable text, no logos, no pseudo-text, no courtroom clichés.

**Exit:** Validated per-item prompt file(s), one prompt per target.

## Phase 4 — generate and QA

**Entry:** Phase 3 prompt manifest parses and covers every target exactly once.

1. Generate family-by-family with the live backend.
2. Use Pro/NanoBanana for important Joachim/Klarc work unless explicitly overridden.
3. QA every image with vision: topic read, no readable text, no logos, no malformed hands/faces, no forbidden clichés, score.
4. Minimum acceptance is the user-specified floor (for Klarc services/posts: 8/10 unless changed).
5. If the same defect survives two edits, swap object class instead of looping.
6. If no-text constraints create a hard concept ceiling, say so and request a narrow constraint relaxation rather than fabricating quality.

**Exit:** Accepted image per target, score at or above floor.

## Phase 5 — optimize before upload

**Entry:** Phase 4 images meet the quality floor.

1. Convert to WebP before upload.
2. Use target hero dimensions appropriate to the site; Klarc service/post heroes use 1600×900 unless changed.
3. Run the AI-marker nuke before import. Strip C2PA/JUMBF/AI metadata and write a rotating camera EXIF/XMP fingerprint.
4. Be honest: metadata cleanup does not remove pixel-domain SynthID.
5. Verify no residual metadata markers with `exiftool | grep -iE 'c2pa|jumbf|synthid|trainedalgo|generative'`.

**Exit:** Clean WebP file(s), correct dimensions, no removable AI metadata markers.

## Phase 6 — batch upload and attach

**Entry:** Phase 5 optimized files and target manifest are complete.

Always upload in batches. Do not drip-upload one accepted image at a time unless debugging a failed import.

1. Finish QA acceptance for the current family/block first.
2. Write a TSV manifest: `post_id<TAB>post_type<TAB>slug<TAB>webp_path<TAB>alt_text`.
3. Import the whole manifest with WP-CLI in one loop and parse clean integer attachment IDs; WP-CLI deprecation notices can pollute `--porcelain` stdout.
4. Set `_thumbnail_id` with a clean integer and verify `HEX(meta_value)` contains digits only.
5. Use descriptive French alt text for Klarc/French sites.
6. Preserve Voxel/Elementor source-of-truth boundaries; do not edit templates when only media attachment is needed.

**Exit:** Every target in the batch has correct new thumbnail attachment.

## Phase 7 — verify and purge

**Entry:** Phase 6 attachment read-back passes.

1. DB verify `_thumbnail_id`, attachment mime type, URL, alt text.
2. Disk verify WebP, dimensions, file exists, no AI metadata markers.
3. Hash all target files and prove every required target has distinct pixels.
4. Verify at least one listing/archive and one detail/single render the new image URL.
5. Purge LSCache / WP cache / Elementor CSS as needed.

**Exit:** Final report includes counts: total, unique hashes, WebP count, dimensions, AI-marker failures, missing files, and cache purge result.

## Failure rules

- Do not claim generation happened without a generated file and QA result.
- Do not claim uniqueness from distinct attachment IDs.
- Do not upload raw PNGs when WebP-first was required.
- Do not continue a large generation run when the visual direction is rejected unless user explicitly says full autonomous.
- Do not use generic `image_generate` if the task specifically requires claude-seo/NanoBanana Pro and that backend is unavailable; report the backend block instead.
