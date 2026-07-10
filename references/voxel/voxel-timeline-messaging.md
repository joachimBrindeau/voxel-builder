# Voxel Timeline: Direct Messages, Notifications, And Follows

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
