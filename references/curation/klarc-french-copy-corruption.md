# Klarc French copy corruption pattern bank

Session source: `klarc.test` WordPress/Voxel/Elementor copy repair.

## Durable lessons

- User explicitly corrected workflow: use backups to recover original intent, but **do not restore in batch**. Perform surgical manual edits.
- Start with requested priority page (homepage), then scan all public pages/CPTs.
- Delegate grammar audits for proposals, but keep final DB writes and verification in orchestrator context.

## Useful commands

List public post types:

```bash
wp post-type list --public=1 --field=name
```

List published public content:

```bash
wp post list --post_type=post,page,events,exp,geo,glossaire,testimonials --post_status=publish --fields=ID,post_type,post_title,post_name --format=json
```

Extract homepage Elementor data:

```bash
wp post meta get 4453 _elementor_data > /tmp/home.json
```

When WP-CLI emits deprecation warnings, strip `Deprecated:` lines before JSON parsing.

## Corruption patterns found

Homepage examples:

- `La combinaison de ces compétences permet à nos de vous accompagner...` → missing noun (`experts`).
- `un suivi et adapté` → missing adjective (`personnalisé`).
- `Des dédiés à votre réussite appréhender vos projets` → broken heading.
- `est pour le développement` → missing `essentiel`.
- `brevets, marques,.` → malformed list punctuation.
- Question headings missing French space before `?`.
- Heading casing: `Propriété Intellectuelle` / `Propriété Industrielle` should usually be sentence case in French.

CPT/testimonial examples:

- `de manière et sans stress` → `de manière fluide et sans stress`.
- `une effet` → `une efficacité`.
- `conseil assez` → `conseil complet`.
- `Un, compétent...` → likely missing noun; rewrite minimally.
- `dactifs`, `dun`, `dexplorer` → lost apostrophes: `d’actifs`, `d’un`, `d’explorer`.

## Verification gate

After fixes:

1. `wp cache flush`
2. Reload affected URLs with `?nocache=...`
3. Browser-evaluate `document.body.innerText` for old bad fragments.
4. Re-run full public-content pattern scan and inspect any remaining false positives.
