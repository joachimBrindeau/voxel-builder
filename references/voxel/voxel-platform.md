# Voxel Platform — Post Types, Taxonomies, Roles, Collections, Widget Catalog, Relations, Verification, Async, Auth, Misc

The foundational platform surface of Voxel: the post-type / taxonomy / role abstractions every other feature builds on, the full catalog of `ts-*` / `vx-*` Elementor widgets, post relations, verification, the file uploader, statistics, async jobs, privacy, nav menus, the templates library, text-formatter / link-previewer / sharer utilities, auth (social + 2FA), and print/QR templates.

Source theme: `sites/<site>/wp-content/themes/voxel/app/` (paths below are relative to `app/` unless noted).

## How to use this reference

Read this file when:
- Building or auditing any Voxel template — you need the full `ts-*` / `vx-*` widget catalog.
- Working with `\Voxel\Post` / `\Voxel\Post_Type` / `\Voxel\Taxonomy` / `\Voxel\User` PHP APIs.
- Setting up Roles + Registration fields (gating which profile fields users fill at signup).
- Implementing Collections (user-saved post lists / wishlists).
- Wiring Post Relations (cross-CPT linking with optional approval flow).
- Implementing Verification badges (`voxel:verified` meta + visibility rules).
- Configuring private File Uploads (e.g. claim-listing proofs).
- Enabling per-post visit Statistics + `ts-visits-chart`.
- Adding async background jobs or scheduled cron tasks.
- Wiring social-login (Google/Facebook/Apple OAuth) or 2FA.
- Adding QR-code or print-template (invoice) outputs.

For dynamic-tag syntax (`@post`, `@user`, `@term`, etc.) see `voxel-tags.md`. This file documents the *system* — APIs, settings, widget catalog, events, gotchas.

For commerce-touching widgets and APIs see `voxel-commerce.md`. For social/timeline widgets and APIs see `voxel-timeline.md`. For search-related widgets see `voxel-search.md`.

---

## Split Platform Map

| Concern | Reference |
|---|---|
| Post types, taxonomies, roles/accounts, collections | `voxel-platform-content-model.md` |
| Voxel widget catalog, relations, verification, media, statistics | `voxel-platform-widgets-relations.md` |
| Dynamic data, onboarding, jobs, privacy, menus, library, auth, print utilities | `voxel-platform-runtime.md` |
