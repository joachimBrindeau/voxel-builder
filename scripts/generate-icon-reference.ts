import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

interface GoogleIconMetadata {
  name: string;
  version?: number;
  popularity?: number;
  codepoint?: number;
  unsupported_families?: string[];
  categories?: string[];
  tags?: string[];
  sizes_px?: number[];
}

interface CompactIconMetadata {
  categories: string[];
  tags: string[];
  popularity: number | null;
  version: number | null;
  sizesPx: number[];
}

interface IconEntry {
  name: string;
  codepoint: string;
  css: string;
  categories: string[];
  tags: string[];
  popularity: number | null;
  version: number | null;
  sizesPx: number[];
  terms: string[];
  metadataSource: 'google-symbols' | 'generated-name';
}

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = join(SCRIPT_DIR, '..');
const SOURCE = resolveCodepointsSource();
const OUT = join(SKILL_ROOT, 'references/icons/material-symbols');
const SHARD_DIR = join(OUT, 'by-prefix');
const MAX_SHARD_ENTRIES = 350;
const METADATA_FILE = join(OUT, 'metadata.json');
const GOOGLE_SYMBOLS_METADATA_URL = 'https://fonts.google.com/metadata/icons?incomplete=1&key=material_symbols';
const MATERIAL_SYMBOLS_FAMILIES = ['Material Symbols Outlined', 'Material Symbols Rounded', 'Material Symbols Sharp'];

const STOP = new Set(['alt', 'arrow', 'icon', 'ios', 'new', 'off', 'on', 'outline', 'rounded', 'sharp', 'symbol', 'ui', 'ux']);

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

async function main(): Promise<void> {
  const previousMetadata = readPreviousMetadata();
  const metadata = await readGoogleSymbolsMetadata(previousMetadata);
  const entries = readEntries(metadata);
  const stats = metadataStats(entries, metadata);

  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(SHARD_DIR, { recursive: true });

  write(
    OUT,
    'README.md',
    renderReadme(entries, stats)
      .replaceAll('workflow.md', 'lookup-and-repair.md')
      .replace('Do not hand-edit generated files; run:', 'Do not hand-edit generated files; from the skill root run:')
      .replace('bun run ../skills/voxel-builder/scripts/generate-icon-reference.ts', 'bun run scripts/generate-icon-reference.ts')
      .replace('\n\n## Storage format', '\n\nSet `WPDEV_ROOT` when the WordPress workspace is not a sibling checkout.\n\n## Storage format'),
  );
  write(OUT, 'lookup-and-repair.md', renderWorkflow(entries, stats));
  write(OUT, 'top-picks.md', renderTopPicks(entries));
  write(OUT, 'search.tsv', renderSearch(entries));
  write(OUT, 'metadata.json', `${JSON.stringify(renderMetadata(entries), null, 2)}\n`);
  write(OUT, 'manifest.json', `${JSON.stringify(renderManifest(entries, stats), null, 2)}\n`);

  for (const [prefix, bucket] of groupIntoShards(entries)) {
    write(SHARD_DIR, `${prefix}.md`, renderShard(prefix, bucket));
  }
}

function readPreviousMetadata(): Map<string, CompactIconMetadata> {
  if (!existsSync(METADATA_FILE)) return new Map();
  const raw = JSON.parse(readFileSync(METADATA_FILE, 'utf8')) as Record<string, CompactIconMetadata>;
  return new Map(Object.entries(raw));
}

async function readGoogleSymbolsMetadata(fallback: Map<string, CompactIconMetadata>): Promise<Map<string, CompactIconMetadata>> {
  try {
    const res = await fetch(GOOGLE_SYMBOLS_METADATA_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.text();
    const json = JSON.parse(body.replace(/^\)\]\}'\n?/, '')) as { icons?: GoogleIconMetadata[] };
    const out = new Map<string, CompactIconMetadata>();
    for (const icon of json.icons ?? []) {
      if (!icon.name || !supportsMaterialSymbols(icon)) continue;
      const existing = out.get(icon.name);
      const next = compact(icon);
      if (!existing || (next.popularity ?? -1) > (existing.popularity ?? -1)) out.set(icon.name, next);
    }
    if (out.size === 0) throw new Error('empty Material Symbols metadata set');
    return out;
  } catch (err) {
    if (fallback.size > 0) {
      console.warn(`Using cached icon metadata because Google metadata fetch failed: ${err instanceof Error ? err.message : String(err)}`);
      return fallback;
    }
    console.warn(`Continuing without Google icon metadata: ${err instanceof Error ? err.message : String(err)}`);
    return new Map();
  }
}

function supportsMaterialSymbols(icon: GoogleIconMetadata): boolean {
  const unsupported = new Set(icon.unsupported_families ?? []);
  return MATERIAL_SYMBOLS_FAMILIES.some((family) => !unsupported.has(family));
}

function compact(icon: GoogleIconMetadata): CompactIconMetadata {
  return {
    categories: unique(icon.categories ?? []),
    tags: unique(icon.tags ?? []),
    popularity: typeof icon.popularity === 'number' ? icon.popularity : null,
    version: typeof icon.version === 'number' ? icon.version : null,
    sizesPx: uniqueNumbers(icon.sizes_px ?? []),
  };
}

function readEntries(metadata: Map<string, CompactIconMetadata>): IconEntry[] {
  const raw = readFileSync(SOURCE, 'utf8');
  const codepoints = SOURCE.endsWith('.json')
    ? Object.entries(JSON.parse(raw) as Record<string, string>)
    : raw.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => line.split(/\s+/, 2) as [string, string]);

  return codepoints
    .map(([name, codepoint]) => {
      if (!name || !codepoint) throw new Error(`Bad codepoint row: ${name ?? ''} ${codepoint ?? ''}`);
      const meta = metadata.get(name);
      const categories = meta?.categories ?? [];
      const tags = meta?.tags ?? [];
      return {
        name,
        codepoint,
        css: `ms:ms ms-${name}`,
        categories,
        tags,
        popularity: meta?.popularity ?? null,
        version: meta?.version ?? null,
        sizesPx: meta?.sizesPx ?? [],
        terms: termsFor(name, categories, tags),
        metadataSource: meta ? 'google-symbols' : 'generated-name',
      } satisfies IconEntry;
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

function resolveCodepointsSource(): string {
  const candidates = [
    process.env.MATERIAL_SYMBOLS_CODEPOINTS,
    process.env.WPDEV_ROOT
      ? join(process.env.WPDEV_ROOT, 'plugins/custom/elementor-framework/assets/icons/material-symbols/material-symbols.codepoints.json')
      : undefined,
    join(process.cwd(), 'plugins/custom/elementor-framework/assets/icons/material-symbols/material-symbols.codepoints.json'),
    join(process.cwd(), 'plugins/custom/elementor-framework/assets/icons/material-symbols/material-symbols.codepoints'),
    join(SKILL_ROOT, '../../wordpress/plugins/custom/elementor-framework/assets/icons/material-symbols/material-symbols.codepoints.json'),
  ].filter((path): path is string => Boolean(path));

  const source = candidates.find((path) => existsSync(path));
  if (!source) {
    throw new Error(`Material Symbols codepoints not found. Checked: ${candidates.join(', ')}`);
  }
  return source;
}

function termsFor(name: string, categories: string[], tags: string[]): string[] {
  const raw = name.split('_').filter(Boolean);
  const terms = new Set<string>([name, name.replace(/_/g, ' '), ...raw, ...categories, ...tags]);
  for (const token of raw) {
    if (!STOP.has(token)) terms.add(token.replace(/\d+/g, ''));
  }
  return unique([...terms].map((term) => normalizeTerm(term)).filter(Boolean)).sort((a, b) => a.localeCompare(b));
}

function normalizeTerm(term: string): string {
  return term.trim().replace(/\s+/g, ' ');
}

function metadataStats(entries: IconEntry[], metadata: Map<string, CompactIconMetadata>) {
  const enriched = entries.filter((entry) => entry.metadataSource === 'google-symbols').length;
  return {
    source: GOOGLE_SYMBOLS_METADATA_URL,
    sourceEntries: metadata.size,
    enriched,
    generatedFallback: entries.length - enriched,
  };
}

function groupByPrefix(entries: IconEntry[]): [string, IconEntry[]][] {
  const groups = new Map<string, IconEntry[]>();
  for (const entry of entries) {
    const prefix = /^[a-z]/.test(entry.name[0] ?? '') ? entry.name[0] : '0-9';
    const bucket = groups.get(prefix) ?? [];
    bucket.push(entry);
    groups.set(prefix, bucket);
  }
  return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

function groupIntoShards(entries: IconEntry[]): [string, IconEntry[]][] {
  return groupByPrefix(entries).flatMap(([prefix, bucket]) => {
    if (bucket.length <= MAX_SHARD_ENTRIES) return [[prefix, bucket]];

    const chunks: [string, IconEntry[]][] = [];
    for (let offset = 0; offset < bucket.length; offset += MAX_SHARD_ENTRIES) {
      chunks.push([`${prefix}-${chunks.length + 1}`, bucket.slice(offset, offset + MAX_SHARD_ENTRIES)]);
    }
    return chunks;
  });
}

function renderReadme(entries: IconEntry[], stats: ReturnType<typeof metadataStats>): string {
  const shards = groupIntoShards(entries).map(
    ([prefix, bucket]) => `- [${prefix}.md](by-prefix/${prefix}.md) — ${bucket.length} icon${bucket.length === 1 ? '' : 's'}`,
  );
  return `# Material Symbols Icon Reference\n\nGenerated from the Elementor Framework installed icon font at \`${rel(SOURCE)}\`, enriched with Google Symbols metadata from \`${GOOGLE_SYMBOLS_METADATA_URL}\`. Do not hand-edit generated files; run:\n\n\`\`\`bash\nbun run ../skills/voxel-builder/scripts/generate-icon-reference.ts\n\`\`\`\n\n## Storage format\n\nUse one string cell:\n\n\`\`\`text\nms:ms ms-<icon_name>\n\`\`\`\n\nExample: \`ms:ms ms-calendar_month\`. Add \`ms-fill\` to the class only when a filled Material Symbol is intentionally required: \`ms:ms ms-bookmark ms-fill\`.\n\n## Fast lookup protocol\n\n1. Use the CLI search when available:\n\n\`\`\`bash\n./wpdev elementor:icon-search \"calendar booking schedule\" --limit 12\n./wpdev elementor:icon-search --categories\n\`\`\`\n\nThe CLI expands common intent synonyms, accepts partial \`--category\` matches, returns match evidence in the table/JSON, and suppresses popularity-only false positives.\n\n2. Or search the generated index with intent words, not guesses:\n\n\`\`\`bash\nrg -i \"calendar|event|schedule|booking\" ../skills/voxel-builder/references/icons/material-symbols/search.tsv\n\`\`\`\n\n3. Read [top-picks.md](top-picks.md) for common Voxel/EF use cases.\n4. If needed, open the matching shard under [by-prefix/](by-prefix/) to inspect nearby names.\n5. Write exactly \`ms:ms ms-<name>\` into EF icon cells.\n\n## Coverage\n\n- EF installed icons: ${entries.length}.\n- Google Symbols metadata-enriched icons: ${stats.enriched}.\n- EF icons using generated-name fallback terms: ${stats.generatedFallback}.\n\nEF's installed \`codepoints\` file remains the availability source of truth. Google metadata supplies categories, tags, popularity, versions, and sizes where the current metadata endpoint covers the installed icon name.\n\n## Files\n\n- [workflow.md](workflow.md) — choose, verify, and repair icons in live Elementor data.\n- [top-picks.md](top-picks.md) — short curated map for common build decisions.\n- [search.tsv](search.tsv) — full ${entries.length}-icon grep index: \`name css codepoint categories popularity terms\`.\n- [metadata.json](metadata.json) — compact metadata cache for EF-installed icons only.\n- [manifest.json](manifest.json) — count + source metadata.\n${shards.join('\n')}\n`;
}

function renderWorkflow(entries: IconEntry[], stats: ReturnType<typeof metadataStats>): string {
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

## Provision a Voxel icon field

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
- Do not fill icons casually. \`ms-fill\` changes visual weight and should be a design choice.
`;
}

function renderTopPicks(entries: IconEntry[]): string {
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

function renderSearch(entries: IconEntry[]): string {
  return `name\tcss\tcodepoint\tcategories\tpopularity\tterms\n${entries
    .map((entry) => `${entry.name}\t${entry.css}\t${entry.codepoint}\t${entry.categories.join('|')}\t${entry.popularity ?? ''}\t${entry.terms.join(';')}`)
    .join('\n')}\n`;
}

function renderShard(prefix: string, entries: IconEntry[]): string {
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

function renderMetadata(entries: IconEntry[]): Record<string, CompactIconMetadata> {
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

function renderManifest(entries: IconEntry[], stats: ReturnType<typeof metadataStats>) {
  return {
    source: rel(SOURCE),
    count: entries.length,
    format: 'ms:ms ms-<name>',
    googleMetadata: stats,
    columns: ['name', 'css', 'codepoint', 'categories', 'popularity', 'terms'],
  };
}

function unique(values: string[]): string[] {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
}

function uniqueNumbers(values: number[]): number[] {
  return [...new Set(values.filter((value) => Number.isFinite(value)))].sort((a, b) => a - b);
}

function write(base: string, file: string, content: string): void {
  const path = join(base, file);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content);
}

function rel(path: string): string {
  return relative(process.cwd(), path);
}

await main();
