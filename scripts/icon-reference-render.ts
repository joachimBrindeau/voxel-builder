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
  return `# Material Symbols Icon Reference\n\nGenerated from the Elementor Framework installed icon font at \`${context.rel(context.source)}\`, enriched with Google Symbols metadata from \`${context.metadataUrl}\`. Do not hand-edit generated files; run:\n\n\`\`\`bash\nbun run ../skills/voxel-builder/scripts/generate-icon-reference.ts\n\`\`\`\n\n## Storage format\n\nUse one string cell:\n\n\`\`\`text\nms:ms ms-<icon_name>\n\`\`\`\n\nExample: \`ms:ms ms-calendar_month\`. Add \`ms-fill\` to the class only when a filled Material Symbol is intentionally required: \`ms:ms ms-bookmark ms-fill\`.\n\n## Fast lookup protocol\n\n1. Use the CLI search when available:\n\n\`\`\`bash\n./wpdev elementor:icon-search "calendar booking schedule" --limit 12\n./wpdev elementor:icon-search --categories\n\`\`\`\n\nThe CLI expands common intent synonyms, accepts partial \`--category\` matches, returns match evidence in the table/JSON, and suppresses popularity-only false positives. Hosted agents reach the same index through the \`wpdev_elementor__icon-search\` MCP tool.\n\n2. Or search the generated index with intent words, not guesses:\n\n\`\`\`bash\nrg -i "calendar|event|schedule|booking" ../skills/voxel-builder/references/icons/material-symbols/search.tsv\n\`\`\`\n\n3. Read [top-picks.md](top-picks.md) for common Voxel/EF use cases.\n4. Write exactly \`ms:ms ms-<name>\` into EF icon cells.\n\n## Coverage\n\n- EF installed icons: ${entries.length}.\n- Google Symbols metadata-enriched icons: ${stats.enriched}.\n- EF icons using generated-name fallback terms: ${stats.generatedFallback}.\n\nEF's installed \`codepoints\` file remains the availability source of truth. Google metadata supplies categories, tags, popularity, versions, and sizes where the current metadata endpoint covers the installed icon name.\n\n## Files\n\n- [workflow.md](workflow.md) — choose, verify, and repair icons in live Elementor data.\n- [top-picks.md](top-picks.md) — short curated map for common build decisions.\n- [search.tsv](search.tsv) — full ${entries.length}-icon grep index: \`name css codepoint categories popularity terms\`.\n- [manifest.json](manifest.json) — count + source metadata.\n`;
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
