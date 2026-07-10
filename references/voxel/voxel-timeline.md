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

## Split Timeline Map

| Concern | Reference |
|---|---|
| Statuses/walls, reviews, comments, likes/reposts/quotes, mentions, link previews | `voxel-timeline-social.md` |
| Direct messages, notifications, follows | `voxel-timeline-messaging.md` |
