# Voxel / Joachim image-generation specifics

This reference carries the site-specific and operator-specific rules. Use it with `../workflows/image-generation.md`. For global model/tool behavior, load `seo/claude-seo/extensions/banana/skills/seo-image-gen`.

## Model and backend preference

- For Joachim/Klarc-quality work, prefer claude-seo / NanoBanana Pro (`gemini-3-pro-image-preview`).
- Do a real backend smoke test before batching prompts.
- If NanoBanana MCP is absent, do not silently switch to a lower-quality/generic backend for production images. Report the block and options.

## Art direction

- Images must be topic-specific real scenes with varied concrete items, humans, and context.
- Avoid generic law imagery and abstract-object-only still lifes.
- Brand colors are accents only: teal, pale rose, cream, brass. Do not make the palette an object prison.
- Rotate shot types: wide establishing, mid/over-shoulder, high three-quarter/overhead, and limited macro.
- Each prompt needs a named idea, not just props: WHO / WHERE / ACTION / TOPIC ANCHORS / COMPOSITION / LIGHT / CAMERA.

## Text and logo control

Readable text, pseudo-text, numbers, brand names, maker marks, silkscreen, engraved lettering, and logo-like emblems are hard failures unless explicitly allowed.

Text magnets and swaps:

- Leather folders leak embossing: use completely blank covers or face-down folders.
- Circuit/dev boards leak silkscreen: use a matte featureless black module, blank green PCB rectangle with traces only, optical disc, USB/microSD cue, or abstract software handoff cue.
- Calculators leak digits: use blank displays or replace with scale/curve cards.
- Ledgers/technical drawings leak figures: use blurred grey rows or line-art without characters.
- Angular marks drift into letters: use soft organic emblems, blobs, rings, or petal clusters.

If an object leaks text across two edits, swap object class instead of editing again.

## Klarc topic cue families

Use these as starting motifs, then vary scene/action per item so pixels stay unique.

- Brevets: machined prototype, exploded component, sealed invention dossier, registry slot, prototype inspection.
- Marques: one large soft-organic emblem, comparison of two emblems, protective glass, registry filing, brand-use handoff.
- Logiciels: featureless black module, blank data disc, dark non-readable UI blocks only if user allows, code escrow as sealed media, handover of software asset.
- Financement / CIR-CII: dossier sequencing, blurred grey rows under loupe, lab prototype beside funding file, blank calendar/timeline blocks, investor table without readable deck text.
- Savoir-faire: strongbox, sealed dossier, brass key, protected glass, blank method cards, wrapped prototype.
- Valorisation / R&D / PI strategy: prototype plinth, valuation curve card without figures, multi-asset table, portfolio review scene, due-diligence room.

## Batch discipline

- Large batches use block-and-approve by default. If user explicitly chooses full autonomous, continue but keep family progress and QA logs.
- Use subagents for prompt authoring only. They write prompt JSON files; command host generates and QA's because subagents do not own image/vision tools.
- Verify prompt file count and IDs before generation.

## WordPress and Voxel upload specifics

- Convert to WebP before upload.
- For Klarc service/post heroes, use 1600×900 unless changed.
- Import through WP-CLI and parse clean numeric IDs; deprecation warnings can pollute `--porcelain`.
- Verify `_thumbnail_id` in DB, not only CLI output.
- Distinct attachment IDs do not prove uniqueness. Hash the actual files on disk.
- Use LSCache/WP/Elementor purge paths after upload.
- Keep Voxel source-of-truth boundaries: media changes belong to attachments/post meta; do not mutate Elementor/Voxel templates unless the image surface is template-owned.

## QA acceptance

- Minimum score follows user floor; for the Klarc unique post/service run, floor is 8/10.
- Hard gates: no readable text, no logos, no wrong backend, correct dimensions/format, no AI metadata markers.
- Vision-QA topic ambiguity can be advisory when page heading disambiguates, but under-floor images must be regenerated or edited.

## AI-marker cleanup

Use the existing curation reference for text/content AI-marker cleanup and the image workflow's nuke step for generated files. Be precise: metadata/C2PA markers can be stripped; SynthID pixel watermark cannot be truthfully claimed removed.
