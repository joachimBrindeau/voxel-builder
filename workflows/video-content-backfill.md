# Video Content Backfill Workflow

Complete imported Voxel `video` records after the YouTube importer has supplied only
authoritative platform metadata. This workflow owns editorial fields and relations; it
never replaces importer-owned IDs, URLs, dates, statistics, thumbnails, or channel state.

## Entry Criteria

**Entry:** site and Video record IDs are known; each record has `yt_video_id` and
`url-youtube`; `wpdev voxel:fields` and `wpdev voxel:data` can inspect the live schema.

**Exit:** every selected record is either evidence-complete and published, remains a draft
with an explicit missing-evidence reason, or is blocked without invented content. Stored
values, relations, author linkage, rendered page, and dedupe invariants are verified.

## Phase 1 — Freeze Sources and Ownership

**Entry:** Site and Video record IDs are known and inspectable via `wpdev`.


1. Read `references/core/rules.md`, `references/core/criteria.md`,
   `references/core/parallel-dispatch.md`, `references/voxel/claude-seo-authoring.md`,
   and `workflows/faq-authoring.md`.
2. Export a database rollback and capture for each Video:
   `wpdev voxel:data`, core title/content/excerpt/author/status/parent, `yt_video_id`,
   organization/service relations, and rendered URL.
3. Confirm global `yt_video_id` uniqueness before editing. Duplicate or cross-organization
   conflicts leave every affected record in draft and route to `curation.md`.
4. Partition source ownership:

   | Owner | Fields |
   |---|---|
   | YouTube importer | URL/ID, upload date, thumbnail, duration, tags, chapters from description, views/likes, source organization/channel |
   | Editorial backfill | WordPress author/presenter, service relation, H1, hook, excerpt, core `wp_posts.post_content` transcript, transcript-derived chapters, FAQ |

**Exit:** A DB rollback exists, per-record source metadata is captured, and YouTube-ID uniqueness is confirmed.

## Phase 2 — Build Evidence Packets

**Entry:** Sources are frozen and per-record ownership is partitioned.


Process 5–10 Videos per bounded batch. Keep one packet and verdict per Video.

1. Capture the YouTube title, description, published captions/subtitles when available,
   and timestamped chapter data. Prefer creator captions over automatic captions.
2. If captions are absent, transcribe the actual audio with an available approved
   transcription tool. Record tool/model, source URL/ID, language, and timestamp coverage.
   If neither captions nor audio transcription is available, mark transcript-dependent
   fields blocked; never reconstruct speech from the title or description.
3. Normalize captions into an edited transcript without changing claims: remove caption
   timing noise and verbal filler only where meaning is preserved; retain headings and
   speaker changes; keep timestamps in the evidence packet.
4. Identify the presenter from explicit video evidence (spoken introduction, caption
   attribution, on-screen/source description). Match that person to an existing Voxel
   profile and WordPress user in both directions. Ambiguous identity remains unassigned.
5. Select a service only when transcript/topic evidence maps unambiguously to a live
   service record. Record candidate IDs and the supporting passage; ambiguity remains
   unassigned rather than guessed.
6. Record a per-field evidence matrix with `supported`, `missing`, or `conflict` for:
   author, service, transcript, H1, hook, excerpt, chapters, and FAQ.


**Exit:** Each Video has an evidence packet with a `supported`/`missing`/`conflict` matrix.

## Phase 3 — Author Reader-Facing Fields

**Entry:** An evidence packet with a per-field matrix exists for the batch.


1. Run the required live-page BASELINE and apply `seo-content-brief` methodology through
   `references/voxel/claude-seo-authoring.md`; do not author ad-hoc SEO copy.
2. Produce:
   - `h1`: 20–70 characters, faithful to the video topic;
   - `hook`: 35–120 characters, concrete and non-promotional;
   - `post_excerpt`: 120–152 characters (never over the live field maximum);
   - `post_content`: the edited source transcript, not the YouTube description. This core
     column is the transcript's only storage owner; never create or update a `content`,
     `transcript`, or similar post-meta copy.
3. Derive chapters only from caption/audio timestamps. Preserve existing YouTube chapters
   unless the timestamped transcript supplies a demonstrably better complete set.
4. Enter `faq-authoring.md` for 3–6 FAQ rows supported by the transcript. Dispatch
   `voxel-faq-author` packets in bounded batches; reject generic or unsupported questions.
5. Reader-facing claims must be present in the transcript or an explicitly cited reliable
   source. Do not invent presenter credentials, legal/financial outcomes, prices, dates,
   statistics, or service promises.


**Exit:** H1/hook/excerpt/transcript/chapters/FAQ are authored or explicitly blocked.

## Phase 4 — Write Once

**Entry:** Reader-facing fields are authored and evidence-backed.


1. Gate each record independently. A publish-ready record requires:
   - unique YouTube ID and valid source organization;
   - evidence-backed author/profile and service when the live template exposes them;
   - non-empty transcript with recorded provenance;
   - H1/hook/excerpt passing live constraints;
   - FAQ and chapters either supported or explicitly omitted with a valid reason.
2. Keep failures as drafts with a concise `_voxel_addon_video_backfill_status` reason.
3. Centralize one write per record:
   - core columns via `wpdev wp <site> post update`, including the transcript only through
     `--post_content`;
   - Voxel fields/relations via `wpdev voxel:set-field` or the post-bound field updater;
   - author plus profile/user linkage without changing importer-owned source metadata.
4. Read every record back immediately. Confirm unrelated importer fields and the
   organization relation did not change.


**Exit:** Each record is written once and read-back-confirmed, or held as a draft with a reason.

## Phase 5 — Verify and Publish

**Entry:** Records have been written once and read back.


1. Re-run `wpdev voxel:data`; assert author/profile linkage, service relation, transcript,
   field lengths, FAQ/chapter JSON integrity, hierarchy parent, and YouTube-ID uniqueness.
2. Publish only records whose Phase 4 gate is green. Never bulk-publish a partially passing
   batch.
3. Reindex/purge through supported `wpdev` commands, then browser-verify every published
   Video when the batch is small; otherwise sample each presenter/service/content shape.
4. Each browser leaf must prove expected transcript/author/service/FAQ content, no dynamic
   tag leakage, no console/page errors, and a read screenshot.
5. Re-run the live SEO page audit and compare it to BASELINE. Record residual drafts and
   their exact missing evidence.


**Exit:** Green-gated records are published and browser-verified; residual drafts are recorded.

## Output Contract

Return one row per Video: ID/title, source packet, author/service verdict, transcript
provenance, authored-field QA, FAQ/chapter verdict, write/read-back result, publish status,
browser result, and remaining blocker. Aggregate counts must distinguish published,
draft-missing-source, conflict, and failed-verification records.
