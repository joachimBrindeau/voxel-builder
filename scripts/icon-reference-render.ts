/**
 * Renderers for every generated Material Symbols reference file.
 *
 * Text generation only: these take already-assembled entries and statistics and
 * return file bodies, so the generator owns IO and these own presentation.
 */

import type { CompactIconMetadata, IconEntry } from './icon-reference-types';

export interface IconReferenceContext {
  /** Absolute path to the EF codepoints file the entries were read from. */
  source: string;
  /** Metadata endpoint quoted in the generated docs. */
  metadataUrl: string;
  /** Render a repo-relative path for display. */
  rel: (path: string) => string;
  /** Group entries into the shard files linked from the README. */
  groupIntoShards: (entries: IconEntry[]) => [string, IconEntry[]][];
}

/** Exactly what `metadataStats` returns in the generator. */
export interface IconStats {
  source: string;
  sourceEntries: number;
  enriched: number;
  generatedFallback: number;
}

const USE_CASES: Record<string, string[]> = {
  'Actions / decisions': ['check_circle', 'cancel', 'edit', 'delete', 'add_circle', 'done', 'close', 'publish', 'save', 'visibility'],
  'Navigation / movement': ['arrow_forward', 'arrow_back', 'chevron_right', 'chevron_left', 'open_in_new', 'navigation', 'near_me'],
  'Contact / people': ['call', 'mail', 'person', 'groups', 'support_agent', 'chat', 'forum', 'badge'],
  'Places / local': ['location_on', 'map', 'directions', 'route', 'home', 'storefront', 'apartment', 'business'],
  'Commerce / booking': ['shopping_cart', 'payments', 'credit_card', 'calendar_month', 'event', 'schedule', 'receipt_long'],
  'Content / documents': ['article', 'description', 'folder', 'upload_file', 'download', 'image', 'photo_camera', 'attach_file'],
  'Trust / status': ['verified', 'shield', 'lock', 'warning', 'info', 'help', 'error', 'grade'],
  'Data / analytics': ['monitoring', 'query_stats', 'bar_chart', 'analytics', 'insights', 'trending_up', 'speed'],
};

export function renderReadme(entries: IconEntry[], stats: IconStats, context: IconReferenceContext): string {
  const shards = context.groupIntoShards(entries).map(
    ([prefix, bucket]) => `- [${prefix}.md](by-prefix/${prefix}.md) — ${bucket.length} icon${bucket.length === 1 ? '' : 's'}`,
  );
  return `# Material Symbols Icon Reference\n\nGenerated from the Elementor Framework installed icon font at \`${context.rel(context.source)}\`, enriched with Google Symbols metadata from \`${context.metadataUrl}\`. Do not hand-edit generated files; run:\n\n\`\`\`bash\nbun run ../skills/voxel-builder/scripts/generate-icon-reference.ts\n\`\`\`\n\n## Storage format\n\nUse one string cell:\n\n\`\`\`text\nms:ms ms-<icon_name>\n\`\`\`\n\nExample: \`ms:ms ms-calendar_month\`. Add \`ms-fill\` to the class only when a filled Material Symbol is intentionally required: \`ms:ms ms-bookmark ms-fill\`.\n\n## Fast lookup protocol\n\n1. Use the CLI search when available:\n\n\`\`\`bash\n./wpdev elementor:icon-search "calendar booking schedule" --limit 12\n./wpdev elementor:icon-search --categories\n\`\`\`\n\nThe CLI expands common intent synonyms, accepts partial \`--category\` matches, returns match evidence in the table/JSON, and suppresses popularity-only false positives.\n\n2. Or search the generated index with intent words, not guesses:\n\n\`\`\`bash\nrg -i "calendar|event|schedule|booking" ../skills/voxel-builder/references/icons/material-symbols/search.tsv\n\`\`\`\n\n3. Read [top-picks.md](top-picks.md) for common Voxel/EF use cases.\n4. If needed, open the matching shard under [by-prefix/](by-prefix/) to inspect nearby names.\n5. Write exactly \`ms:ms ms-<name>\` into EF icon cells.\n\n## Coverage\n\n- EF installed icons: ${entries.length}.\n- Google Symbols metadata-enriched icons: ${stats.enriched}.\n- EF icons using generated-name fallback terms: ${stats.generatedFallback}.\n\nEF's installed \`codepoints\` file remains the availability source of truth. Google metadata supplies categories, tags, popularity, versions, and sizes where the current metadata endpoint covers the installed icon name.\n\n## Files\n\n- [workflow.md](workflow.md) — choose, verify, and repair icons in live Elementor data.\n- [top-picks.md](top-picks.md) — short curated map for common build decisions.\n- [search.tsv](search.tsv) — full ${entries.length}-icon grep index: \`name css codepoint categories popularity terms\`.\n- [metadata.json](metadata.json) — compact metadata cache for EF-installed icons only.\n- [manifest.json](manifest.json) — count + source metadata.\n${shards.join('\n')}\n`;
}

/**
 * The closing half of workflow.md: provisioning and anti-patterns. Static
 * prose, hoisted out of the template so the renderer stays readable and the
 * guidance can be edited without touching generation logic.
 */
const WORKFLOW_REFERENCE_SECTIONS = `## Provision a Voxel icon field

When the CPT itself needs an icon field for templates/cards to read, use the Voxel settings command instead of editing \`voxel:post_types\` directly:

\`\`\`bash
./wpdev voxel:settings <site> ensure-field --type <cpt_key> --fieldKey icon --fieldType icon --label Icon --dry
./wpdev voxel:settings <site> ensure-field --type <cpt_key> --fieldKey icon --fieldType icon --label Icon --yes
\`\`\`

If legacy icon values are numeric media IDs, migrate them to Voxel's SVG icon string form:

\`\`\`bash
./wpdev voxel:settings <site> ensure-field --type <cpt_key> --fieldKey icon --fieldType icon --migrate-image-ids --yes
\`\`\`

## Anti-patterns

- Do not invent \`ms-*\` class names. Search [search.tsv](search.tsv).
- Do not use Font Awesome / Line Awesome as the default for new EF work; prefer Material Symbols unless preserving existing visual parity.
- Do not store bare \`ms ms-foo\`; EF icon cells should store \`ms:ms ms-foo\`.
- Do not fill icons casually. \`ms-fill\` changes visual weight and should be a design choice.`;

export function renderWorkflow(entries: IconEntry[], stats: IconStats): string {
  return `# Icon Selection And Repair Workflow

This workflow keeps context small while giving access to the full ${entries.length}-icon Material Symbols library installed by Elementor Framework. Search is enriched for ${stats.enriched} installed icons with Google Symbols categories/tags/popularity; the rest use generated name terms.

## Pick the right icon

1. Name the visual job in plain words: action, object, status, place, commerce, document, navigation.
2. Prefer the CLI search for ranked results:

\`\`\`bash
./wpdev elementor:icon-search "calendar booking schedule" --limit 12
./wpdev elementor:icon-search "external link new tab" --category "UI"
./wpdev elementor:icon-search "trust verified badge" --json
./wpdev elementor:icon-search --categories
\`\`\`

The CLI expands common workspace intent words such as \`reservation\`, \`trust\`, \`external\`, \`address\`, and \`seo\`; use \`--json\` when you need score, matches, and reasons for each candidate.

3. Or search [search.tsv](search.tsv):

\`\`\`bash
rg -i "calendar|event|schedule|booking" ../skills/voxel-builder/references/icons/material-symbols/search.tsv
\`\`\`

4. Prefer literal Material names over cute metaphors. For example, use \`calendar_month\` for booking, \`location_on\` for address, \`verified\` for trust, \`open_in_new\` for external links.
5. Emit the EF icon string: \`ms:ms ms-<name>\`.

## Verify site usage

Use the DB scanner after any icon work:

\`\`\`bash
./wpdev elementor:icons <site> --unique
./wpdev elementor:icons <site> --json
./wpdev elementor:icons <site> --library ms --unique
\`\`\`

The scanner reads stored \`_elementor_data\` for pages and templates, including \`header\`, \`footer\`, \`single-post\`, \`archive\`, \`card\`, and regular pages.

## Fix a wrong icon

Use the scanner's \`postId\`, \`nodeId\`, and \`keyPath\`. Scanner paths include the \`settings.\` prefix and use bracket array indexes; \`elementor:set-value\` wants a path relative to \`settings\` with dotted array indexes. Convert before writing:

\`\`\`bash
key_path='settings.ts_actions.value[0].value.icon.value'
set_path=$(printf '%s' "$key_path" | sed 's/^settings\\.//; s/\\[\\([0-9][0-9]*\\)\\]/.\\1/g')

./wpdev elementor:set-value <site> --post <post_id> --node <node_id> --path "$set_path" --value 'ms:ms ms-<name>' --yes
\`\`\`

For batch edits, write a JSON map with dotted \`path\` values and run:

\`\`\`bash
./wpdev elementor:set-value <site> --map /tmp/icon-fixes.json --yes
\`\`\`

Then verify:

\`\`\`bash
./wpdev elementor:icons <site> --post <post_id> --json
./wpdev elementor:lint <site> --post <post_id>
\`\`\`

For non-scalar icon cells or broad structural edits, prefer a small mutator or \`elementor:mutate\` over forcing \`set-value\`.

${WORKFLOW_REFERENCE_SECTIONS}
`;
}

export function renderTopPicks(entries: IconEntry[]): string {
  const byName = new Map(entries.map((entry) => [entry.name, entry]));
  const rows: string[] = [];
  for (const [useCase, names] of Object.entries(USE_CASES)) {
    for (const name of names) {
      const entry = byName.get(name);
      if (entry) rows.push(`| ${useCase} | \`${name}\` | \`${entry.css}\` | ${entry.categories.join(', ')} | ${entry.terms.filter((term) => term !== name).slice(0, 8).join(', ')} |`);
    }
  }
  return `# Material Symbols Top Picks\n\nShort list for common Voxel/EF build decisions. This is curated from the generated full catalog; if none fit, search [search.tsv](search.tsv) or run \`wpdev elementor:icon-search\`.\n\n| Use case | Icon | EF value | Category | Search terms |\n|---|---|---|---|---|\n${rows.join('\n')}\n`;
}

export function renderSearch(entries: IconEntry[]): string {
  return `name\tcss\tcodepoint\tcategories\tpopularity\tterms\n${entries
    .map((entry) => `${entry.name}\t${entry.css}\t${entry.codepoint}\t${entry.categories.join('|')}\t${entry.popularity ?? ''}\t${entry.terms.join(';')}`)
    .join('\n')}\n`;
}

export function renderShard(prefix: string, entries: IconEntry[]): string {
  return `# Material Symbols: ${prefix}\n\n${entries.length} icons. Use exact EF value \`ms:ms ms-<name>\`.\n\n| Name | EF value | Category | Popularity | Terms |\n|---|---|---|---:|---|\n${entries
    .map(
      (entry) =>
        `| \`${entry.name}\` | \`${entry.css}\` | ${entry.categories.join(', ')} | ${entry.popularity ?? ''} | ${entry.terms
          .filter((term) => term !== entry.name)
          .slice(0, 18)
          .join(', ')} |`,
    )
    .join('\n')}\n`;
}

export function renderMetadata(entries: IconEntry[]): Record<string, CompactIconMetadata> {
  return Object.fromEntries(
    entries.map((entry) => [
      entry.name,
      {
        categories: entry.categories,
        tags: entry.tags,
        popularity: entry.popularity,
        version: entry.version,
        sizesPx: entry.sizesPx,
      } satisfies CompactIconMetadata,
    ]),
  );
}

export function renderManifest(entries: IconEntry[], stats: IconStats, context: IconReferenceContext) {
  return {
    source: context.rel(context.source),
    count: entries.length,
    format: 'ms:ms ms-<name>',
    googleMetadata: stats,
    columns: ['name', 'css', 'codepoint', 'categories', 'popularity', 'terms'],
  };
}
