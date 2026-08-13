/**
 * Shared shapes for the Material Symbols icon reference generator.
 *
 * Split out so the generator and its renderers agree on one definition without
 * either importing the other's logic.
 */

export interface GoogleIconMetadata {
  name: string;
  version?: number;
  popularity?: number;
  codepoint?: number;
  unsupported_families?: string[];
  categories?: string[];
  tags?: string[];
  sizes_px?: number[];
}

export interface CompactIconMetadata {
  categories: string[];
  tags: string[];
  popularity: number | null;
  version: number | null;
  sizesPx: number[];
}

export interface IconEntry {
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
