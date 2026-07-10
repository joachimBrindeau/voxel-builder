# Voxel Timeline: Statuses, Reviews, Comments, And Social Actions

## Timeline (Statuses / Walls / Reviews)

- **Path**: `timeline/`, `timeline/status.php`, `post-types/post-type-timeline.php`, `controllers/timeline/`
- **Purpose**: A unified status-feed engine that drives FOUR distinct feed contexts off a single `{prefix}voxel_timeline` table. The `feed` column distinguishes which context a row belongs to:

  | `feed` value | Context | Where it renders |
  |---|---|---|
  | `user_timeline` | A user's own personal posts (Twitter-style profile feed) | User profile templates via `ts-timeline` with `feed=user_timeline` |
  | `post_timeline` | Posts published BY a Voxel post (e.g. a business profile posting updates) | Post single template, "Updates" tab |
  | `post_reviews` | Reviews left ON a post | Post single template, "Reviews" tab |
  | `post_wall` | Community wall ON a post (any user can post) | Post single template, "Wall" tab |

  Supports text, image/file attachments, link previews (including YouTube embeds), `@mentions`, threaded replies, likes, reposts, and quote-reposts. Every entry has a moderation status (`PENDING`/`APPROVED`/`REJECTED`).

- **CPT / data shape**:
  - `{prefix}voxel_timeline` (statuses) — columns: `id`, `feed`, `user_id` (author), `post_id`, `published_as` (the publisher persona — see below), `content`, `details` (JSON: files CSV, link preview, rating breakdown), `moderation`, `review_score` (-2..+2, only when `feed=post_reviews`), `repost_of`, `quote_of`, `created_at`.
  - `{prefix}voxel_timeline_replies` (comments + threaded replies) — `id`, `status_id`, `parent_id` (NULL = top-level comment; non-NULL = nested reply), `user_id`, `content`, `details`, `moderation`, `created_at`. Depth of nesting computed via recursive CTE in `Reply::get_depth()`.
  - `{prefix}voxel_timeline_status_likes` — `status_id`, `user_id`.
  - `{prefix}voxel_timeline_reply_likes_v2` — `reply_id`, `user_id`.
  - Files: stored as comma-separated attachment IDs inside the JSON `details` column under `files`. NOT a relational table.

- **Public API**:
  - `\Voxel\Timeline\Status::get( $id )` — singleton-cached row wrapper.
  - `\Voxel\Timeline\Status::query( $args )` — args: `feed`, `user_id`, `post_id`, `moderation`, `published_as`, `repost_of`, `quote_of`, `created_at`, `limit`, `offset`, `order_by`.
  - Per-status methods:
    - `->get_user()` — author user.
    - `->get_post()` — target post (NULL for `feed=user_timeline`).
    - `->get_publisher()` — returns either a User or a Post object (the persona under which the status was published; see `published_as` notes).
    - `->get_author()` — alias of `get_user()`.
    - `->get_content_for_display()` — text-formatted content (autolinks, mentions, hashtags rendered).
    - `->get_files()` — attachment IDs from `details.files`.
    - `->get_link_preview()` — returns `{title, image, domain, url}` for OG-scraped URLs, or `{type: 'youtube', embed_url, video_id}` for YouTube URLs.
    - `->get_review_score()` / `->get_review_rating()` / `->get_review_score_for_display()` — only meaningful when `feed=post_reviews`.
    - `->like()` / `->unlike()` / `->is_liked_by_current_user()`.
    - `->is_reposted_by_current_user()`.
    - `->is_viewable_by_current_user()` — applies the visibility ladder (see below).
    - `->is_editable_by_current_user()` / `->is_moderatable_by_current_user()`.
    - `->mark_approved()` — moves moderation from `PENDING` to `APPROVED` and fires the matching approval event.
    - `->send_mention_notifications()` — parses `@username` tokens and dispatches `User_Mentioned_In_Post_Event` (deduped via `details.approved_at` so re-approval does not re-notify).
    - `->get_frontend_config()` — the canonical shape sent to the timeline JS bundle. Use this to understand what data the timeline UI actually consumes.
  - `\Voxel\Timeline\Reply::get( $id )` — comment/reply wrapper. Methods: `->get_depth()` (recursive CTE), `->get_parent()` (parent reply or null), `->get_status()` (root status), `->like()` / `->unlike()`, `->is_viewable_by_current_user()`.

- **Visibility ladder** (per feed context, per post-type):

  Configured under each CPT's Timeline tab. The ladder is the same for all four feed contexts; only the setting key changes:

  | Setting key (per CPT) | Controls |
  |---|---|
  | `timeline.visibility` | Who can READ `user_timeline` statuses by users of this role-bound CPT (profile CPT only) |
  | `post_timeline.posts.visibility` | Who can READ `post_timeline` statuses on posts of this CPT |
  | `post_reviews.posts.visibility` | Who can READ `post_reviews` statuses on posts of this CPT |
  | `post_wall.posts.visibility` | Who can READ `post_wall` statuses on posts of this CPT |

  Each setting takes one of five values:

  | Value | Gate |
  |---|---|
  | `public` | Anyone, including logged-out visitors |
  | `logged_in` | Any authenticated user |
  | `followers_only` | Only users who follow the target user (for `user_timeline`) or post (for `post_*` feeds) — see Follows below |
  | `customers_only` | Only users who have purchased a product from the target user/post via `Customer_Trait::has_bought_product()` — see `voxel-commerce.md` |
  | `private` | Author + moderators only |

  Pending statuses (`moderation = PENDING`) are ALWAYS visible to the author + moderators regardless of the visibility setting.

- **Moderation**: per-CPT, per-feed. Configured via `Post_Type_Timeline::get_moderation_settings()` which reads from the global `settings.timeline.moderation.post_types.<key>` option. Per-feed knobs:

  | Setting | Effect |
  |---|---|
  | `post_timeline.posts.require_approval` | New `post_timeline` statuses start `PENDING` |
  | `post_timeline.comments.require_approval` | New `post_timeline` comments start `PENDING` |
  | `post_wall.posts.require_approval` | New `post_wall` statuses start `PENDING` |
  | `post_wall.comments.require_approval` | New `post_wall` comments start `PENDING` |
  | `post_reviews.posts.require_approval` | New reviews start `PENDING` |
  | `post_reviews.comments.require_approval` | New review-comments start `PENDING` |

- **Voxel-native widgets**: `ts-timeline` (the main feed widget; takes `feed` setting + per-feed visibility/order repeater controls), `ts-timeline-kit` (composable building blocks for custom feed UIs), `ts-review-stats` (aggregate rating bar / breakdown chart), `ts-ring-chart` (can surface review-aggregate metrics). **Never hand-author `ts-*` JSON from memory** — dump a real production instance: `wpdev elementor:dump <site> ts-timeline --post <real_id> --json` (see [`rules.md`](../core/rules.md) Rule 2).

- **Dynamic tags**: `@timeline/status(...)`, `@timeline/reply(...)`, `@timeline/review(...)` — see `voxel-tags.md`. Aggregate post-level tags: `@post(:reviews.*)`, `@post(:timeline.*)`, `@post(:wall.*)`.

- **Settings surface**:
  - Per CPT: `wp-admin/edit.php?post_type=<key>&page=edit-post-type-<key>` → Timeline tab.
  - Global: Voxel → Settings → Timeline (mentions cap, link previews, default `user_timeline` visibility).

- **Triggers / events** (full event catalog at `events/timeline/`):
  - `events/timeline/statuses/`:
    - `Post_Reviews_Status_Created_Event`, `Post_Reviews_Status_Approved_Event`
    - `Post_Timeline_Status_Created_Event`, `Post_Timeline_Status_Approved_Event`
    - `Post_Wall_Status_Created_Event`, `Post_Wall_Status_Approved_Event`
    - `User_Timeline_Status_Created_Event`, `User_Timeline_Status_Approved_Event`
    - `User_Liked_Event`, `User_Quoted_Event`, `User_Reposted_Event`
  - `events/timeline/comments/`:
    - `Comment_Submitted_Event`, `Comment_Approved_Event`, `Comment_Liked_Event`
    - `Comment_Reply_Submitted_Event`, `Comment_Reply_Approved_Event`
  - `events/timeline/mentions/`:
    - `User_Mentioned_In_Post_Event`, `User_Mentioned_In_Comment_Event`
  - `events/timeline/followers/`:
    - `User_Followed_Event`, `Post_Followed_Event`

- **Common usage patterns**:
  - Post single template embeds `ts-timeline` set to `feed=post_wall` (community wall) or `feed=post_reviews` (reviews tab). Often inside a `ts-template-tabs` widget.
  - User profile template embeds `ts-timeline` set to `feed=user_timeline` filtered by `user_id=@author(:id)`.
  - "Featured updates" homepage block: `ts-timeline` with `feed=post_timeline` and no `post_id` filter to pull a global feed.

- **Gotchas**:
  - `published_as` lets a status be authored under a non-default persona. Example: a user who manages a business profile can post on the business's timeline AS the business (the `published_as` column references the profile post). `get_publisher()` returns whichever persona is set; `get_user()` always returns the actual author user. See `User::get_timeline_publisher_config()` for the persona dropdown logic.
  - Quote-reposts inline-render the original publisher block. The original status is referenced via `quote_of`; deleting the original sets that FK dangling, and `Status::get( $quote_of )` returns null — handle gracefully.
  - Mentions are capped per post (default 5) via the filter `voxel/timeline/mentions/max-per-post`. Excess mentions are silently dropped from notification dispatch.
  - The `approved_at` timestamp in `details` is the dedup key for mention-notification re-sends. If you manually toggle a status from APPROVED → PENDING → APPROVED and then call `send_mention_notifications()`, it will NOT re-notify unless you also clear `details.approved_at`.
  - The 4 feed contexts share one table; an `INDEX(feed, post_id, moderation, created_at)` powers most queries. When writing custom SQL, always include `feed` in the WHERE clause for index usage.

---
## Reviews (schema layer over Timeline)

- **Path**: `post-types/post-type-reviews.php`, `timeline/status.php` (with `feed=post_reviews`)
- **Purpose**: A typed layer over the timeline. Reviews ARE timeline statuses with `feed=post_reviews`, but with structured `score` (-2..+2) and a configurable `categories` matrix (per-CPT) for multi-axis ratings.

- **Reviews schema** (per CPT, via `Post_Type_Reviews::get_settings_schema()`):

  | Key | Type | Notes |
  |---|---|---|
  | `categories` | array of `{key, label, icon, required}` | Auto-injects a `score` category at the front of the list (the overall rating) |
  | `input_mode` | `numeric` \| `stars` | UI for category sliders |
  | `active_icon` | icon ID | Filled state (default star) |
  | `inactive_icon` | icon ID | Empty state |
  | `rating_levels` | `{poor: -2, fair: -1, good: 0, very_good: 1, excellent: 2}` | Label map for the 5-point scale. Keys are fixed; only labels are editable |

- **Score scale**: -2..+2 (5 discrete values). Storage column: `review_score`. Aggregate per-post: `@post(:reviews.average)`, `@post(:reviews.count)`, `@post(:reviews.breakdown.<level>)`. Per-category breakdown lives in `details.rating` JSON on the status row.

- **Public API**: Reviews use the same `Status` class as other timeline rows; the review-specific bits are:
  - `Status::get_review_score()` — raw -2..+2 integer.
  - `Status::get_review_rating()` — full `details.rating` JSON (per-category).
  - `Status::get_review_score_for_display()` — formatted (e.g. "Excellent").
  - `\Voxel\User::has_reviewed_post( $post_id )` — boolean (one review per user per post).
  - `\Voxel\User::can_review_post( $post_id )` — combines `has_reviewed_post()` + CPT-level "can review" gating.

- **Voxel-native widgets**: `ts-review-stats` (renders aggregate bar/breakdown), `ts-timeline` with `feed=post_reviews`, `ts-ring-chart` (renders rating ring).

- **Common usage patterns**: post single template "Reviews" tab = `ts-template-tabs` containing `ts-review-stats` + `ts-timeline[feed=post_reviews]`. Submit form is the standard status composer with rating UI enabled.

- **Gotchas**:
  - One review per user per post. To allow multiple, you'd need to bypass `User::has_reviewed_post()` — not a supported config knob.
  - `input_mode=stars` and `input_mode=numeric` produce identical stored data (integer -2..+2); only the UI differs.
  - Category `required=true` on submit; partial reviews are rejected at the controller.

---
## Comments & Replies (threaded)

- **Path**: `timeline/reply.php`, `controllers/timeline/` (REST controllers)
- **Purpose**: Threaded comments on any timeline status. Top-level comments have `parent_id IS NULL`; nested replies set `parent_id` to the parent reply's ID. Depth is computed lazily via a recursive CTE.

- **Data shape**: `{prefix}voxel_timeline_replies` (see Timeline section above).

- **Public API**:
  - `\Voxel\Timeline\Reply::get( $id )` / `::query( $args )`.
  - `->get_depth()` — recursive CTE: `WITH RECURSIVE depth AS (SELECT id, parent_id, 0 AS d FROM replies WHERE id = ? UNION ALL SELECT r.id, r.parent_id, depth.d+1 FROM replies r JOIN depth ON r.id = depth.parent_id) SELECT MAX(d) FROM depth`.
  - `->get_parent()` — direct parent reply (or null if top-level).
  - `->get_status()` — the root status row this thread belongs to.
  - `->like()` / `->unlike()` / `->is_liked_by_current_user()`.
  - `->is_viewable_by_current_user()` — inherits root status visibility.
  - `->mark_approved()` — moves moderation PENDING → APPROVED.

- **Moderation**: see Timeline `*.comments.require_approval` settings. Pending replies are visible only to author + moderators.

- **Triggers / events**: `Comment_Submitted_Event`, `Comment_Approved_Event`, `Comment_Liked_Event`, `Comment_Reply_Submitted_Event`, `Comment_Reply_Approved_Event` (under `events/timeline/comments/`).

- **Common usage patterns**: rendered inline by `ts-timeline` under each status; the JS bundle handles lazy-loading deeper threads. The depth limit is a CSS-only concern — Voxel does not enforce a hard server-side max depth.

- **Gotchas**:
  - Like counts on replies are stored in `{prefix}voxel_timeline_reply_likes_v2` (note the `_v2` suffix — the original table was rebuilt during a Voxel migration). Custom SQL against the old `voxel_timeline_reply_likes` table will silently miss rows.
  - Deleting a parent reply does NOT cascade to children at the SQL level (no FK). The Voxel controller manually walks descendants; manual SQL deletes leave orphans.

---

## Likes / Reposts / Quotes

- **Path**: `timeline/status.php`, `controllers/timeline/`
- **Purpose**: Three engagement primitives on top of statuses.

  | Action | Storage | Notes |
  |---|---|---|
  | Like | `voxel_timeline_status_likes` row (or `voxel_timeline_reply_likes_v2` for comments) | Idempotent. One like per user per status |
  | Repost | New status row with `repost_of = original_id`, blank `content` | The reposter's `user_id`/`published_as`; rendered as a card embedding the original |
  | Quote | New status row with `quote_of = original_id`, populated `content` | Same as repost but with the quoter's text on top |

- **Public API**: `Status::like()` / `->unlike()`, `->is_liked_by_current_user()`, `->is_reposted_by_current_user()`. Quote/repost flow is handled by the REST controllers in `controllers/timeline/`.

- **Triggers / events**: `User_Liked_Event`, `User_Reposted_Event`, `User_Quoted_Event` (under `events/timeline/statuses/`).

- **Gotchas**:
  - A repost is itself a Status row — it appears in feeds, can be liked, can be commented on, can be re-reposted.
  - Deleting the original sets `repost_of` / `quote_of` to dangling values. `Status::get( $original )` returns null; the UI shows a "deleted content" placeholder.

---

## Mentions

- **Path**: `utils/text-formatter/` (mention parsing), `events/timeline/mentions/`
- **Purpose**: `@username` tokens in status content auto-link to user profiles and dispatch in-app notifications to the mentioned user.

- **Flow**:
  1. User types `@alice` in a status composer.
  2. On submit, `text-formatter()` parses the content, extracts mention tokens, resolves them to user IDs.
  3. `Status::send_mention_notifications()` dispatches `User_Mentioned_In_Post_Event` (or `User_Mentioned_In_Comment_Event` for replies) per resolved user, up to the cap.
  4. On render, `text-formatter()` rewrites `@alice` to `<a href="<profile_link>">@alice</a>`.

- **Cap**: 5 mentions per post by default. Override:
  ```php
  add_filter( 'voxel/timeline/mentions/max-per-post', fn() => 10 );
  ```

- **Dedup**: `details.approved_at` is set on first APPROVED transition. `send_mention_notifications()` skips if `approved_at` is already set, so re-approving does not re-notify.

- **Gotchas**: Resolution is by exact `user_login` (case-insensitive). Display-name mentions don't work. If a user is renamed, old mention tokens become broken links.

---

## Link Previews (OG cards + YouTube embeds)

- **Path**: `utils/link-previewer/`
- **Purpose**: Scrape OG / Twitter / oEmbed metadata from the first URL in a status and render it as a rich card under the status. Detects YouTube URLs and substitutes an embed player.

- **API**: `\Voxel\link_previewer( $url )` returns:
  - For YouTube: `{type: 'youtube', video_id, embed_url}`
  - For other URLs: `{title, image, url, domain}` (or null if scrape fails)

- **Storage**: Result cached in the status's `details.link_preview` JSON. Re-scraping does not happen on read.

- **Gotchas**: First-link wins. If a status has multiple URLs, only the first is previewed. To force a different preview, manually edit `details.link_preview` (no UI for this).

---
