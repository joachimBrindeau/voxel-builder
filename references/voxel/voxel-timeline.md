# Voxel Timeline, Reviews, Comments, Messages, Notifications, Follows

The social-graph surface of Voxel: status feeds, reviews, threaded comments, likes/reposts/quotes, mentions, link previews, direct messages, notifications, and follows. Stable across recent Voxel releases — the underlying tables (`voxel_timeline*`, `voxel_messages`, `voxel_notifications`, `voxel_followers`, `voxel_chats`) have not changed shape in years.

Source theme: `sites/<site>/wp-content/themes/voxel/app/` (paths below are relative to `app/` unless noted).

## How to use this reference

Read this file when:
- Building or auditing a single-post template that embeds a wall, reviews tab, or comment thread.
- Building or auditing a user profile template that renders `user_timeline`.
- Wiring a Direct Messages "Contact" button on a CPT card / single.
- Adding a Notifications dropdown to a custom navbar.
- Implementing followers-only / customers-only gating on any content surface.
- Writing a Voxel event-driven action (review-created webhook, comment-approved hook, follow-event trigger).

For dynamic-tag syntax (`@timeline/status(...)`, `@timeline/review(...)`, `@message(...)` properties) see `voxel-tags.md`. This file documents the *system* — tables, classes, settings, events, gotchas.

For commerce-side surfaces that this file touches (`customers_only` visibility uses `Customer_Trait::has_bought_product()`) see `voxel-commerce.md`.

---

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

## Direct Messages (Inbox / Chat)

- **Path**: `modules/direct-messages/`
- **Purpose**: Two-party chat between any combination of user↔user, user↔post, or post↔post (e.g. business profile receiving messages on behalf of the owner). Inbox search, threaded conversation, attachments, seen/unseen, per-side "cleared below" cursor.

- **Data shape**:
  - `{prefix}voxel_chats` — one row per conversation. Columns: `id`, `p1_type` (`user`/`post`), `p1_id`, `p1_last_message_id`, `p1_cleared_below` (cursor: messages with `id <= p1_cleared_below` are hidden for party 1 only), `p2_type`, `p2_id`, `p2_last_message_id`, `p2_cleared_below`.
  - `{prefix}voxel_messages` — `id`, `sender_type`, `sender_id`, `receiver_type`, `receiver_id`, `content`, `details` (JSON: attachments), `seen` (boolean), `created_at`.

- **Public API**: `\Voxel\Modules\Direct_Messages\Chat`:
  - `::get_inbox( $user_id, $limit, $offset )` — paginated inbox for a user (joins chats where they are p1 OR p2).
  - `::search_inbox( $user_id, $term, $limit, $offset )` — MySQL fulltext `MATCH ... AGAINST ... IN BOOLEAN MODE` across `display_name` / `post_title` of the other party.
  - `::mark_as_seen( $p1, $p2 )` — flips `seen=1` on all messages from p2 → p1.
  - `::load_messages( $p1, $p2, $cursor, $limit )` — paginated message list with cursor-based pagination (cursor is a message ID; loads messages with `id < cursor`).
  - `::clear_conversation( $p1, $p2 )` — sets the calling party's `cleared_below` to the latest message ID. The other party still sees the full history.
  - `::get_chat( $p1, $p2 )` — looks up the chat row; creates it if missing.
  - `\Voxel\Modules\Direct_Messages\Message` — per-message wrapper.

- **Chat URL format**: `?chat=<id_chars>` on the inbox page (the page bound to `templates.inbox`). `<id_chars>` is `Chat::get_link()`'s packed encoding — *the current viewer's perspective on the conversation*:
  - User → user contact: `?chat=u<target_user_id>` (e.g. `?chat=u42` opens chat with user 42).
  - User → post contact: `?chat=p<target_post_id>` (e.g. `?chat=p57` opens chat with post 57's author).
  - Post-as-author → target: `<author_post_id><sep><target_id>` where `<sep>` is `p` or `u` based on target type (e.g. `?chat=42u17` = business profile 42 messaging user 17). Source: `app/modules/direct-messages/chat.php::get_link()`.

- **Voxel-native widgets**: `ts-messages` (the inbox widget — source `app/modules/direct-messages/widgets/messages-widget.php`). Bind a page to `templates.inbox` in Voxel → Settings → Direct Messages so `Chat::get_link()` resolves to it.

- **Dynamic tags**: `@message(...)` — see `voxel-tags.md`. Properties: `sender.name`, `sender.link`, `sender.avatar`, `sender.chat_link`, `receiver.{name, link, avatar, chat_link}`, `content`.

- **Settings surface**:
  - Voxel → Settings → Direct Messages (module toggle, attachment limits, throttling).
  - `templates.inbox` page setting drives chat permalinks.

- **Triggers / events** (under `events/direct-messages/`):
  - `User_Received_Message_Event` (throttled — debounces multiple messages from the same sender into one notification).
  - `User_Received_Message_Unthrottled_Event` (per-message, for use cases that need real-time signaling).

- **Common usage patterns**:
  - "Contact" button on a business profile single template: links to `?chat={{post.id}}p{{current_user.id}}` on the inbox page.
  - Vendor dashboard "Customer messages" tab embeds the inbox filtered to chats involving the vendor's product orders.

- **Gotchas**:
  - The `cleared_below` cursor is asymmetric. If user A "deletes" a conversation, user B still sees the full thread — only A's view is truncated. A new message from B clears A's `cleared_below` (resets to NULL) and restores the conversation.
  - Search uses FULLTEXT — short search terms (< 3 chars by default in MySQL) return no rows. Configurable via `ft_min_word_len` in `my.cnf`.
  - Post-as-party chats: when a chat has a post as p1 or p2, the post's AUTHOR (and any users with edit access to the post) receive notifications. The chat metadata still references the post, not the user.

---

## Notifications

- **Path**: `notification.php`, `controllers/frontend/notification-controller.php`, `events/`
- **Purpose**: In-app notification feed. Each event class (under `events/`) emits both an inbox notification and (optionally) an email/webhook. Notifications resolve their event at READ time so the rendered subject/links/actions reflect current state (e.g. if a referenced post was renamed, the notification shows the new title).

- **Data shape**: `{prefix}voxel_notifications` — `id`, `user_id` (recipient), `type` (event class FQN), `details` (JSON — event-specific payload), `seen` (boolean), `created_at`.

- **Public API**: `\Voxel\Notification`:
  - `::get( $id )` / `::query( $args )` / `::create( $data )`.
  - `::get_unread_count( $user_id, $since? )` — count of `seen=0` notifications, optionally filtered to those created after `$since`.
  - `->get_subject()` — rendered notification headline (e.g. "Alice followed you").
  - `->get_links_to()` — destination URL when notification is clicked.
  - `->get_actions( $page )` — paginated list of inline actions (e.g. "5 new comments" expands to a paginated list of 5 comment links).
  - `->get_actions_page_count()` — total action pages (used to render pagination).
  - `->get_image_url()` — avatar/thumbnail for the notification.
  - `->is_seen()` / `->is_valid()`.
  - `ACTIONS_PER_PAGE = 10` (constant).

- **In-app notification anatomy**: A notification has 4 callables resolved at read time:

  | Field | Resolves to | Used by |
  |---|---|---|
  | `subject` | string (HTML allowed) | List item headline |
  | `links_to` | URL string | Click target |
  | `actions(page)` | array of `{label, url, image}` | Inline action list (paginated) |
  | `image_id` | attachment ID | Avatar/thumbnail |

  These are defined per-event class in `Event::get_notifications()` returning a map of `destination => { inapp: { subject, links_to, ... }, email: { subject, body, ... } }`.

- **Per-event tag tokens**: Each event class implements `->get_dynamic_tags()` which returns a map like `{user.name, post.title, comment.content, ...}`. Subject/body strings use these tokens (e.g. `"{{user.name}} commented on {{post.title}}"`) and are rendered via `\Voxel\render( $template, $tags )`.

- **Voxel-native widgets**: Rendered inline inside `ts-navbar` / `ts-user-bar` (no standalone widget). The bell-icon dropdown reads from `Notification::query({ user_id: current_user })`.

- **Settings surface**: Voxel → Settings → Notifications. Per-event toggles for `inapp` / `email`; `admin_user` setting for fallback vendor (events that need a vendor target but the post has none — e.g. claim requests on an unowned listing).

- **Triggers / events**: every `\Voxel\Events\Base_Event` subclass defines `get_notifications()`. Discoverable via `\Voxel\Events\Base_Event::get_all()`.

- **Common usage patterns**:
  - Navbar bell-icon dropdown: shows last 10 notifications + unread count badge.
  - Per-user dedicated "/notifications" page (the `templates.notifications` page setting): full paginated list.

- **Gotchas**:
  - Notifications resolve at READ time, NOT at write time. If you delete a referenced post, `is_valid()` returns false and the notification renders a placeholder.
  - `get_unread_count( $user_id, $since )` is the cheap query (single COUNT); use it for the badge. `query()` is the expensive query — only call on actual dropdown expansion.
  - The `details` JSON shape is event-class-specific. Custom event classes MUST document their `details` shape.

---

## Follows (Users / Posts)

- **Path**: `users/social-trait.php`, `posts/social-trait.php`, `events/timeline/followers/`
- **Purpose**: Per-user follow lists. Can follow EITHER a user OR a post. Three-state status model with a fourth "no row" state.

- **Three-state model** (constants defined in `app/utils/constants.php`):

  | Constant | Value | Meaning |
  |---|---|---|
  | `\Voxel\FOLLOW_REQUESTED` | `0` | Follow requested, awaiting approval (used when the target has private/approval-required follow setting) |
  | `\Voxel\FOLLOW_ACCEPTED` | `1` | Active follow (the common state) |
  | `\Voxel\FOLLOW_BLOCKED` | `-1` | Follower is blocked (cannot follow, cannot see followers-only content) |
  | `\Voxel\FOLLOW_NONE` | `null` (no row) | Not following — the row is absent from `voxel_followers`; `set_follow_status( …, FOLLOW_NONE )` DELETEs the row |

- **Data shape**: `{prefix}voxel_followers`:
  - `object_type` ENUM(`post`, `user`) — what is being followed.
  - `object_id` — target ID.
  - `follower_type` ENUM(`post`, `user`) — who is following. Both `\Voxel\User` and `\Voxel\Post` carry a `set_follow_status()` (`app/users/social-trait.php`, `app/posts/social-trait.php`); the inbox controller writes `follower_type='post'` rows when a post-persona blocks a counterparty. Treat both as live in the schema.
  - `follower_id` — follower ID (matches `follower_type`).
  - `status` — see above.

  Stats are cached via `\Voxel\cache_user_follow_stats()` / `\Voxel\cache_post_follow_stats()` (writes counts to user/post meta on follow-state change for fast badge rendering).

- **Public API**:
  - `\Voxel\User::get_follow_status( $type, $id )` — returns one of the four constants.
  - `\Voxel\User::set_follow_status( $type, $id, $status )` — writes the row + fires events + invalidates caches.
  - `\Voxel\User::follows_user( $id )` / `->follows_post( $id )` — convenience: returns `true` iff status == FOLLOW_ACCEPTED.
  - `\Voxel\Post::repository->get_follow_stats()` — `{accepted: int, requested: int, blocked: int}`.

- **Visibility-rule binding**: follows gate three things:
  1. `followers_only` timeline visibility (any feed context) — only followers see content.
  2. `customers_only` is a SEPARATE gate (not a follow check) — see `voxel-commerce.md`.
  3. Dynamic-tag visibility rules `user-follows-author`, `user-follows-post` (under `dynamic-data/visibility-rules/`).

- **Dynamic tags**: `@post(:followers.accepted)`, `@post(:followers.blocked)`, `@post(:followers.requested)`, plus `@user(...)` follow counts.

- **Settings surface**: Per-CPT timeline.visibility can be set to `followers_only`. Per-user follow lists are rendered via a `ts-timeline`-bundled "followers" modal (not a separate widget).

- **Triggers / events**: `User_Followed_Event`, `Post_Followed_Event` (under `events/timeline/followers/`). Both fire only on transition TO `FOLLOW_ACCEPTED` (not on requested or blocked).

- **Common usage patterns**:
  - "Follow" button on a user profile: toggles `set_follow_status('user', $profile_user_id, FOLLOW_ACCEPTED)`.
  - "Follow this listing" button: toggles `set_follow_status('post', $post_id, FOLLOW_ACCEPTED)`.
  - Followers-only feed: a `ts-timeline` widget on a post single template with `feed=post_wall` and the CPT-level `post_wall.posts.visibility=followers_only` setting — the visibility check is server-side, JS never receives non-visible rows.

- **Gotchas**:
  - `set_follow_status( …, FOLLOW_NONE )` DELETEs the row (it doesn't write `status=NULL`). Any other unsupported value coerces to a no-op — only the four canonical constants are persisted.
  - Blocked status is one-way (follower is blocked from following the target). It does NOT prevent the target from following the blocker.
  - Cache: follow-stats are denormalized into user/post meta. After raw SQL changes to `voxel_followers`, run `\Voxel\cache_user_follow_stats( $user_id )` / `\Voxel\cache_post_follow_stats( $post_id )` to resync — otherwise stale counts render until the next natural recompute.

---

## Cross-reference — other feature files in this cluster

| File | Covers | When to read |
|---|---|---|
| [`voxel-commerce.md`](voxel-commerce.md) | Product types, cart, orders, bookings, paid memberships, paid listings, promotions, claims, Stripe Connect, payment methods | Commerce-side flows. `customers_only` timeline visibility uses `Customer_Trait::has_bought_product()` documented there. Order-driven notifications + events also live there |
| [`voxel-search.md`](voxel-search.md) | Search filters, sort clauses, index table, maps + geocoding, recurring dates + work hours | When wiring a search page that filters by author, by followers, or by review rating — the relevant filters (`user-filter`, `followed-by-filter`, `rating-order`) live there |
| [`voxel-platform.md`](voxel-platform.md) | Post types, taxonomies, roles + registration, collections, full Voxel widget catalog, post relations, verification, async jobs, auth, print templates | When you need the full `ts-*` widget catalog (incl. `ts-timeline`, `ts-user-bar`, `ts-navbar` settings), Role/User registration mechanics, or the event-dispatcher async architecture |

For dynamic-tag syntax of any group mentioned here (`@timeline/status`, `@timeline/review`, `@timeline/reply`, `@message`, `@user`, `@current_user`), see `voxel-tags.md`.
