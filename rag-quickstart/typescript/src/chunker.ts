/**
 * Deterministic text chunking and markdown document parsing.
 *
 * Chunking is character-based and deterministic so the RAG pipeline is
 * reproducible.
 */

import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";

export function chunkText(
  text: string,
  chunkSize: number,
  chunkOverlap: number,
): string[] {
  if (text.length === 0) {
    return [];
  }
  if (text.length <= chunkSize) {
    return [text];
  }

  const step = Math.max(1, chunkSize - chunkOverlap);
  const chunks: string[] = [];
  let start = 0;
  for (;;) {
    chunks.push(text.slice(start, start + chunkSize));
    if (start + chunkSize >= text.length) {
      break;
    }
    start += step;
  }
  return chunks;
}

export async function parseMarkdownFiles(dataDir: string): Promise<string[]> {
  let entries: string[];
  try {
    entries = await readdir(dataDir);
  } catch {
    return [];
  }
  const markdown = entries.filter((name) => name.endsWith(".md")).sort();
  return Promise.all(
    markdown.map((name) => readFile(join(dataDir, name), "utf-8")),
  );
}
