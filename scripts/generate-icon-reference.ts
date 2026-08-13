import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import type { CompactIconMetadata, GoogleIconMetadata, IconEntry } from './icon-reference-types';
import type { IconReferenceContext } from './icon-reference-render';
import {
  renderManifest,
  renderMetadata,
  renderReadme,
  renderSearch,
  renderShard,
  renderTopPicks,
  renderWorkflow,
} from './icon-reference-render';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = join(SCRIPT_DIR, '..');
const SOURCE = resolveCodepointsSource();
const OUT = join(SKILL_ROOT, 'references/icons/material-symbols');
// The CLI (`wpdev elementor:icon-search`) reads the search index from the in-repo,
// force-tracked snapshot dir, so mirror search.tsv there on every generate.
const REPO_SNAPSHOT_TSV = resolveRepoSnapshotTsv();
const SHARD_DIR = join(OUT, 'by-prefix');
const MAX_SHARD_ENTRIES = 350;
const METADATA_FILE = join(OUT, 'metadata.json');
const GOOGLE_SYMBOLS_METADATA_URL = 'https://fonts.google.com/metadata/icons?incomplete=1&key=material_symbols';
const MATERIAL_SYMBOLS_FAMILIES = ['Material Symbols Outlined', 'Material Symbols Rounded', 'Material Symbols Sharp'];

const STOP = new Set(['alt', 'arrow', 'icon', 'ios', 'new', 'off', 'on', 'outline', 'rounded', 'sharp', 'symbol', 'ui', 'ux']);

async function main(): Promise<void> {
  const previousMetadata = readPreviousMetadata();
  const metadata = await readGoogleSymbolsMetadata(previousMetadata);
  const entries = readEntries(metadata);
  const stats = metadataStats(entries, metadata);

  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(SHARD_DIR, { recursive: true });

  const context: IconReferenceContext = {
    source: SOURCE,
    metadataUrl: GOOGLE_SYMBOLS_METADATA_URL,
    rel,
    groupIntoShards,
  };

  write(
    OUT,
    'README.md',
    renderReadme(entries, stats, context)
      .replaceAll('workflow.md', 'lookup-and-repair.md')
      .replace('Do not hand-edit generated files; run:', 'Do not hand-edit generated files; from the skill root run:')
      .replace('bun run ../skills/voxel-builder/scripts/generate-icon-reference.ts', 'bun run scripts/generate-icon-reference.ts')
      .replace('\n\n## Storage format', '\n\nSet `WPDEV_ROOT` when the WordPress workspace is not a sibling checkout.\n\n## Storage format'),
  );
  write(OUT, 'lookup-and-repair.md', renderWorkflow(entries, stats));
  write(OUT, 'top-picks.md', renderTopPicks(entries));
  const searchTsv = renderSearch(entries);
  write(OUT, 'search.tsv', searchTsv);
  if (REPO_SNAPSHOT_TSV) {
    mkdirSync(dirname(REPO_SNAPSHOT_TSV), { recursive: true });
    writeFileSync(REPO_SNAPSHOT_TSV, searchTsv);
  }
  write(OUT, 'metadata.json', `${JSON.stringify(renderMetadata(entries), null, 2)}\n`);
  write(OUT, 'manifest.json', `${JSON.stringify(renderManifest(entries, stats, context), null, 2)}\n`);

  for (const [prefix, bucket] of groupIntoShards(entries)) {
    write(SHARD_DIR, `${prefix}.md`, renderShard(prefix, bucket));
  }
}

function readPreviousMetadata(): Map<string, CompactIconMetadata> {
  if (!existsSync(METADATA_FILE)) return new Map();
  const raw = JSON.parse(readFileSync(METADATA_FILE, 'utf8')) as Record<string, CompactIconMetadata>;
  return new Map(Object.entries(raw));
}

/**
 * Fold Google's icon list into one entry per name, keeping the most popular
 * variant when a name appears more than once.
 */
function collectSymbolMetadata(icons: GoogleIconMetadata[]): Map<string, CompactIconMetadata> {
  const out = new Map<string, CompactIconMetadata>();
  for (const icon of icons) {
    if (!icon.name || !supportsMaterialSymbols(icon)) continue;
    const existing = out.get(icon.name);
    const next = compact(icon);
    if (!existing || (next.popularity ?? -1) > (existing.popularity ?? -1)) out.set(icon.name, next);
  }
  return out;
}

/** Report why live metadata was unusable and fall back to the cached set. */
function fallbackMetadata(fallback: Map<string, CompactIconMetadata>, err: unknown): Map<string, CompactIconMetadata> {
  const detail = err instanceof Error ? err.message : String(err);
  if (fallback.size > 0) {
    console.warn(`Using cached icon metadata because Google metadata fetch failed: ${detail}`);
    return fallback;
  }
  console.warn(`Continuing without Google icon metadata: ${detail}`);
  return new Map();
}

async function readGoogleSymbolsMetadata(fallback: Map<string, CompactIconMetadata>): Promise<Map<string, CompactIconMetadata>> {
  try {
    const res = await fetch(GOOGLE_SYMBOLS_METADATA_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.text();
    const json = JSON.parse(body.replace(/^\)\]\}'\n?/, '')) as { icons?: GoogleIconMetadata[] };
    const out = collectSymbolMetadata(json.icons ?? []);
    if (out.size === 0) throw new Error('empty Material Symbols metadata set');
    return out;
  } catch (err) {
    return fallbackMetadata(fallback, err);
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

/**
 * Build one reference entry, defaulting every field Google's metadata may
 * omit. Icons absent from that metadata still get an entry, marked so the
 * manifest can report how much of the set is name-derived.
 */
const EMPTY_METADATA: CompactIconMetadata = { categories: [], tags: [], popularity: null, version: null, sizesPx: [] };

function toIconEntry(name: string, codepoint: string, meta: CompactIconMetadata | undefined): IconEntry {
  const { categories, tags, popularity, version, sizesPx } = meta ?? EMPTY_METADATA;
  return {
    name,
    codepoint,
    css: `ms:ms ms-${name}`,
    categories,
    tags,
    popularity,
    version,
    sizesPx,
    terms: termsFor(name, categories, tags),
    metadataSource: meta ? 'google-symbols' : 'generated-name',
  } satisfies IconEntry;
}

function readEntries(metadata: Map<string, CompactIconMetadata>): IconEntry[] {
  const raw = readFileSync(SOURCE, 'utf8');
  const codepoints = SOURCE.endsWith('.json')
    ? Object.entries(JSON.parse(raw) as Record<string, string>)
    : raw.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => line.split(/\s+/, 2) as [string, string]);

  return codepoints
    .map(([name, codepoint]) => {
      if (!name || !codepoint) throw new Error(`Bad codepoint row: ${name ?? ''} ${codepoint ?? ''}`);
      return toIconEntry(name, codepoint, metadata.get(name));
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

function resolveRepoSnapshotTsv(): string | undefined {
  const roots = [
    process.env.WPDEV_ROOT,
    process.cwd(),
    join(SKILL_ROOT, '../../wordpress'),
  ].filter((path): path is string => Boolean(path));

  const root = roots.find((candidate) =>
    existsSync(join(candidate, 'plugins/custom/elementor-framework/assets/icons/material-symbols')),
  );
  return root
    ? join(root, 'cli/src/generated/material-symbols-search.tsv')
    : undefined;
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
