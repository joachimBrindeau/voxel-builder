# Templates — master catalog

Reusable section-template store. One row per stored template, one folder per template (see [`README.md`](README.md)). Tables are split by `scope`: **Global** (header/footer, one active per site), **Sections** (reusable page parts, many per page), **Pages** (full-page compositions).

`dtags-used` lists only the universal Voxel dynamic tags a template keeps live (per the placeholder policy); every other static string is Lorem Ipsum. `preview` links an optional `preview.png`.

## Global

One active per site (Theme Builder location). Documented-but-empty for v1 — see `README.md` §Empty slots.

| id | type | tags | widgets | dtags-used | preview |
|---|---|---|---|---|---|

## Sections

Reusable page parts (heroes, feature rows, etc.), many per page.

| id | type | tags | widgets | dtags-used | preview |
|---|---|---|---|---|---|
| hero-services-search | hero | hero, search, services, header | ef-wrapper, ef-card | `@post(parent.title)` | — |
| hero-city-geo | hero | hero, geo, city, header, background-image | ef-wrapper, ef-card | `@post(parent.title)`, `@post(h1)`, `@post(_thumbnail_id.id)` | — |
| hero-headline-lead | hero | hero, headline, lead, intro | ef-wrapper, ef-card | — | — |
| features-services-grid | features | features, services, grid, cards, expertise | ef-wrapper, ef-card | — | — |
| content-media-split | content | content, media, split, image, text | ef-wrapper, ef-card | — | — |
| steps-how-it-works | steps | steps, process, how-it-works, timeline, cards | ef-wrapper, ef-card | — | — |
| testimonials-loop-feed | testimonials | testimonials, loop, feed, reviews, byline | ef-wrapper, ef-card | — | — |
| locations-map-feed | locations | locations, geo, map, loop, feed | ef-wrapper, ef-card | `@post(slug)` | — |
| posts-latest-feed | feed | feed, posts, blog, loop, articles | ef-wrapper, ef-card | — | — |
| faq-accordion | faq | faq, accordion, questions, support | ef-wrapper, ef-card | — | — |
| cta-conversion-band | cta | cta, conversion, band, call-to-action | ef-wrapper, ef-card | — | — |

## Pages

Full-page compositions. One row per stored page; splice as a whole-page starting tree and replace documented `__TOKEN__` slots before import.

| id | type | tags | widgets | dtags-used | preview |
|---|---|---|---|---|---|
| glossary | glossary | glossary, dictionary, defined-terms, az-index, loop, hub | ef-wrapper, ef-card | `@post(parent.title)`, `@post(h1)`, `@post(title)` | — |
| video-single | single | video, single, chapters, author, related-content, wrapper | ef-wrapper, ef-card | `@post(parent.title)`, `@post(h1)`, `@post(:excerpt)`, `@author(display_name)`, `@author(profile.permalink)` | — |
| search-hub-index | search-hub | search, hub, index, cpt, archive-replacement | ef-wrapper, ef-card | `@post(parent.title)`, `@post(h1)` | — |
| archive | archive | archive, search, results, cpt, voxel | ef-wrapper, ef-card, ts-search-form, ts-post-feed | `@post(parent.title)`, `@post(h1)` | — |
