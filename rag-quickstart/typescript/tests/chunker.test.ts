import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { chunkText, parseMarkdownFiles } from "../src/chunker.js";

function tempDir(): string {
  return mkdtempSync(join(tmpdir(), "tessera-chunk-"));
}

describe("chunkText", () => {
  it("splits without overlap", () => {
    expect(chunkText("a".repeat(100), 50, 0)).toEqual(["a".repeat(50), "a".repeat(50)]);
  });

  it("splits with overlap at exact boundaries", () => {
    // "abcdefghij" (10), size=6, overlap=2 -> step=4
    expect(chunkText("abcdefghij", 6, 2)).toEqual(["abcdef", "efghij"]);
  });

  it("returns a single chunk when text is shorter than chunk size", () => {
    expect(chunkText("hello", 100, 10)).toEqual(["hello"]);
  });

  it("returns a single chunk when text equals chunk size", () => {
    expect(chunkText("abcde", 5, 2)).toEqual(["abcde"]);
  });

  it("returns empty array for empty text", () => {
    expect(chunkText("", 100, 10)).toEqual([]);
  });

  it("terminates even when overlap >= chunk size", () => {
    const chunks = chunkText("abcdefgh", 4, 4);
    expect(chunks.length).toBeGreaterThan(0);
    expect(chunks.every((c) => c.length <= 4)).toBe(true);
  });
});

describe("parseMarkdownFiles", () => {
  it("reads only .md files", async () => {
    const dir = tempDir();
    writeFileSync(join(dir, "doc1.md"), "# Title\nSome content here.");
    writeFileSync(join(dir, "other.txt"), "ignored");
    const docs = await parseMarkdownFiles(dir);
    expect(docs).toHaveLength(1);
    expect(docs[0]).toContain("Some content here.");
  });

  it("returns documents in deterministic sorted order", async () => {
    const dir = tempDir();
    writeFileSync(join(dir, "b.md"), "beta");
    writeFileSync(join(dir, "a.md"), "alpha");
    expect(await parseMarkdownFiles(dir)).toEqual(["alpha", "beta"]);
  });

  it("returns empty array for an empty directory", async () => {
    expect(await parseMarkdownFiles(tempDir())).toEqual([]);
  });
});
