# Card Actions — define the `ts_actions` strip (and `ef-navbar` `cta_ts_actions`)

A numbered, gated pipeline for **deliberately defining the action buttons** on an
`ef-card` (`ts_actions`) or `ef-navbar` (`cta_ts_actions`). It turns "what should
this card's buttons do?" into a correct, SSOT-validated `ef-action-rows` envelope —
the right action `type`, the cells that `type` actually consumes, and a destination
that resolves at render time.

## Entry criteria

1. Target card/navbar widget and desired user action are known.
2. Live schema or committed SSOT for action rows is available.
3. Destination data source (`@post`, `@author`, static URL, phone, map, etc.) is valid for the target context.
4. Existing action rows are dumped before mutation.

## Exit criteria

1. Action rows use valid action `type` cells only; no ignored or phantom cells remain.
2. Dynamic destinations resolve for a representative record.
3. Elementor lint passes for the mutated post/template.
4. Browser verification confirms the buttons render and activate the intended destination.

## Why this exists

Action rows pass `wpdev elementor:lint` whenever the prop names are valid, so the two most common defects are invisible to the schema gate: a destination dtag that resolves to an empty string, and a Voxel-runtime action selected on a page that lacks the runtime piece it needs (renders an inert button). This workflow gates both at compose time.

**Reference (read first):** [`../references/ef/actions.md`](../references/ef/actions.md) —
the SSOT-generated action-type catalog (34 types + required cells), the action-row
cell table, the use-case→type map, the Voxel-runtime dependency table, and the
golden loopable-row envelopes. This workflow is the *process*; that file is the
*knowledge*. Do not restate the catalog here — query it (Phase 1/2).

**Not for:** the `link` card variant (transparent inline reference — it
intentionally has **no** `ts_actions`; skip it). Scaffolding the card itself →
the cards flow (`build.md` §Cards) / `wpdev voxel:cards`.
The heading-title permalink link is a *content-block* concern — the action suite on a
`content_blocks` row whose `kind` is `heading` (cell `type` + `link`), not an
`ts_actions` row — see [`build.md`](build.md) §Cards.

---

## Phase 0 — Preflight & host resolution

**Entry:** a target card or navbar exists (or is being built this session).

1. Resolve `<site>` and the target post id. Halt if `<site>` is missing.
2. Identify the **host prop**:
   - `ef-card` → `ts_actions` (footer/strip; also exposes `actions_embedded`).
   - `ef-navbar` → `cta_ts_actions` (always rendered as buttons, `embedded=true`).
3. Confirm the SSOT catalog is current (the reference is generated from it):
   ```bash
   wpdev elementor:docs:gen --check   # actions.md vs cli/src/generated/ef-catalogs.json
   ```
   On drift, run `wpdev elementor:docs:gen` before continuing.
4. **If mutating an existing card's actions**, this is an existing-data edit:
   author the Behavior Contract triple + DOM-text baseline first
   ([`behavior-contract.md`](../references/verification/behavior-contract.md)). Author ≠ repairer ≠ reviewer.

**Exit:** host prop known; catalog confirmed current; baseline captured if editing.

---

## Phase 1 — Choose the action(s)

**Entry:** the card's role in its feed/page is understood (what should a visitor *do* from this card?).

1. List the candidate types and their required cells from the SSOT:
   ```bash
   scripts/action-spec.sh          # all
   ```
   Map the desired outcome to a `type` via [`actions.md`](../references/ef/actions.md)
   §"Common patterns by use case".
2. **Runtime-dependency gate (hard).** Cross-check every chosen type against
   [`actions.md`](../references/ef/actions.md) §"Voxel-runtime dependencies". Types
   outside the resolver's self-contained set (`action_link`, `get_directions`,
   `call`, `send_email`, `open_modal`, `scroll_to_section`, `action_gcal`,
   `action_ical`, `share_post`) render an **inert button** unless the page mounts
   Voxel's runtime (and, for some, a specific widget — `show_post_on_map` needs a
   `ts-map`; `open_vx_*` need a user-bar; commerce/auth actions need their module +
   a logged-in user). If the target page lacks the piece, either drop the action or
   record that it only wakes inside Voxel's advanced-list template.
3. **No-redundancy check.** If the card's heading already links to the permalink
   (the standard preview-card wiring), a footer `action_link` to the *same*
   permalink adds nothing. Prefer an action that adds value — `call`,
   `send_email`, `get_directions`, `action_save`, `direct_message` — or omit the
   strip. A second permalink link is a smell, not a default.

**Exit:** an ordered list of `type`s, each justified and runtime-checked.

---

## Phase 2 — Resolve & collect required cells (SSOT-driven)

**Entry:** chosen `type`s from Phase 1.

1. For each chosen type, dump its required cells + field specs:
   ```bash
   scripts/action-spec.sh <type>
   ```
   Collect a value for **every** required cell — never invent extras the resolver
   ignores.
2. Choose static vs dynamic per cell (Rule 5):
   - **`action_link` `link.destination`** → `@post(permalink)` for "open this post".
     **Never `@post(url)`** — it resolves to an empty string in this Voxel build
     (verify any permalink dtag with `wpdev wp <site> eval` + `\Voxel\render` before
     trusting it; `@post(permalink)` and `@post(:url)` resolve, `@post(url)` and
     `@post(:permalink)` do not).
   - **`phone` / `email` / `address`** → bind to the CPT field
     (`@post(<field_key>)`) when the card loops posts; static only for fixed
     navbar CTAs.
   - **`cal_*`** → date fields via `@post(<date_field>)`; see the
     `action-spec.sh` placeholders for the accepted formats.
3. Set the per-row presentation cells as needed: `label` (localized — this is a
   French B2B site; e.g. "Voir le profil", "Appeler", "Itinéraire"), `icon`,
   `variant` (`''` inherits the host default; else `primary`/`white`/…), `tooltip`.
4. **Loop / visibility** (contact-method repeaters, per-sub-type rows): use the
   golden `_vx_loop` / `_vx_visibility` envelopes in
   [`actions.md`](../references/ef/actions.md) §"Loopable action-rows". Comparator
   rule: taxonomy/multiselect/relation sub-fields use `contains`, never
   `is_equal_to`.

**Exit:** a fully-specified row per action — `type` + its required cells + presentation cells.

---

## Phase 3 — Build the canonical envelope

**Entry:** fully-specified rows.

1. Read the exact prop + row shape from the committed SSOT (offline, preferred):
   ```bash
   jq '.widgets[] | select(.name=="ef-card") | .props.ts_actions, .rows."action-row"' \
     cli/src/generated/widget-schemas.json
   ```
   Live fallback: `wpdev elementor:schema <site> ef-card --prop ts_actions`.
2. Wrap rows in the composite-repeater envelope: `{$$type:"ef-action-rows", value:[ {$$type:"ef-action-row", value:{…cells}} ]}`.
   Each cell carries its own `$$type` (`string` for label/icon/type, `link` for
   `link`, etc.). The `link` cell's destination is a `vx` envelope:
   `{"$$type":"link","value":{"destination":{"$$type":"vx","value":"@post(permalink)"}}}`.
3. For `ef-card`, set `actions_embedded` intentionally (`''` inherit / `'yes'`
   footer chips / `'no'` stacked buttons) — see [`actions.md`](../references/ef/actions.md) §`actions_embedded`.

**Exit:** a schema-valid `ef-action-rows` payload for the host prop.

---

## Phase 4 — Apply

**Entry:** the envelope from Phase 3.

Write through the CLI loop, never a raw postmeta poke. Prefer the atomic mutator
(lint → CSS regen → cache purge → optional fetch):
```bash
wpdev elementor:mutate <site> <post_id> <mutator.php>   # mutator sets settings.ts_actions
# or, for a whole-card replace:
wpdev elementor:import <site> <post_id> <file.json>     # passes the pre-write schema gate
```
The mutator/import must emit clean JSON via the canonical write path (direct SQL by
`meta_id`, `JSON_UNESCAPED_UNICODE`) — see `cli/src/utils/elementor/write.ts`.

**Exit:** `ts_actions` written; CSS regenerated; caches purged.

---

## Phase 5 — Verify

**Entry:** actions applied.

1. **Schema:** `wpdev elementor:lint <site> --post <post_id>` — halt on new findings.
2. **Resolution:** render the card against a real post and assert each action's
   destination/payload is non-empty:
   ```bash
   wpdev wp <site> eval '$p=get_posts(["post_type"=>"<cpt>","numberposts"=>1])[0];
     \Voxel\set_current_post(\Voxel\Post::get($p->ID));
     echo \Elementor\Plugin::$instance->documents->get(<card_id>)->get_content();' | grep -o 'href="[^"]*"'
   ```
   Confirm `action_link` hrefs equal `get_permalink($p->ID)` — an empty `href=""`
   means the destination dtag did not resolve (the `@post(url)` trap).
3. **Runtime actions:** for any non-self-contained type, verify in a real browser
   per [`browser.md`](../references/verification/browser.md) — an inert `<button>` in the live
   DOM means the page is missing the required Voxel piece (Phase 1 gate missed it).

**Exit:** lint clean; every `action_link` resolves to its permalink; runtime
actions are live (or consciously accepted as advanced-list-only).

---

## Mistake guards

- Never add cells outside the action-type SSOT; ignored cells create false confidence.
- Never assume Voxel runtime actions work on pages missing required runtime widgets/modules.
- Never use `@post(url)` for permalink; verify dynamic destinations before write.

## Anti-patterns

- `@post(url)` as a destination — resolves empty; use `@post(permalink)`.
- A footer `action_link` duplicating the heading's permalink link — adds no value.
- Selecting a Voxel-runtime action (`add_to_cart`, `action_save`, `show_post_on_map`, `open_vx_*`, …) on a page without its runtime piece — renders an inert button.
- Adding `ts_actions` to the `link` card variant — it is title-only by design.
- Hand-writing `_elementor_data` without the lint gate / CSS regen — use `elementor:mutate` or `elementor:import`.
- `is_equal_to` on a taxonomy/multiselect/relation sub-field in a loop visibility rule — use `contains`.
