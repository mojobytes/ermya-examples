import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, beforeEach, describe, expect, it, jest } from "@jest/globals";

import type { Config } from "../src/config-loader.js";
import type { EmbeddingProvider } from "../src/embedding.js";
import type { TesseraClientLike } from "../src/tessera-client-factory.js";
import { runPipeline } from "../src/pipeline.js";

function makeConfig(overrides: { dimension?: number; tenantId?: string; chunkSize?: number; chunkOverlap?: number } = {}): Config {
  const { dimension = 4, tenantId = "rag-quickstart", chunkSize = 10, chunkOverlap = 0 } = overrides;
  return {
    tessera: { host: "localhost", port: 50051, apiKey: "k", secure: false },
    embedding: {
      provider: "ollama",
      endpoint: "http://localhost:11434",
      apiKey: "",
      model: "nomic-embed-text",
      deploymentName: "",
      dimension,
    },
    ingestion: { tenantId, chunkSize, chunkOverlap, dataDir: "./data" },
  };
}

function tempDataDir(content = "abcdefghijABCDEFGHIJ"): string {
  const dir = mkdtempSync(join(tmpdir(), "tessera-pipe-"));
  writeFileSync(join(dir, "doc.md"), content);
  return dir;
}

let client: jest.Mocked<TesseraClientLike>;
let provider: jest.Mocked<EmbeddingProvider>;

beforeEach(() => {
  client = {
    createTenant: jest.fn(async () => ({})),
    insert: jest.fn(async () => ({ id: 1 })),
    search: jest.fn(async () => ({ results: [] })),
  } as unknown as jest.Mocked<TesseraClientLike>;
  provider = {
    embed: jest.fn(async () => [0.5, 0.5, 0.5, 0.5]),
  } as unknown as jest.Mocked<EmbeddingProvider>;
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("runPipeline", () => {
  it("prints the plaintext banner", async () => {
    const log = jest.spyOn(console, "log").mockImplementation(() => {});
    await runPipeline(makeConfig(), client, provider, tempDataDir());
    const output = log.mock.calls.map((c) => String(c[0])).join("\n");
    expect(/QUICKSTART|EXAMPLE/i.test(output)).toBe(true);
    expect(/plaintext|not production/i.test(output)).toBe(true);
  });

  it("creates the tenant with the config dimension", async () => {
    await runPipeline(makeConfig({ dimension: 4, tenantId: "my-tenant" }), client, provider, tempDataDir());
    expect(client.createTenant).toHaveBeenCalledWith({ tenantId: "my-tenant", dimension: 4 });
  });

  it("embeds each chunk", async () => {
    await runPipeline(makeConfig({ chunkSize: 10, chunkOverlap: 0 }), client, provider, tempDataDir());
    expect(provider.embed).toHaveBeenCalledTimes(2);
  });

  it("verifies the dimension after the first embed and fails before inserting", async () => {
    provider.embed.mockResolvedValue(new Array(384).fill(0.1));
    await expect(
      runPipeline(makeConfig({ dimension: 1536 }), client, provider, tempDataDir()),
    ).rejects.toThrow(/Dimension mismatch/);
    expect(client.insert).not.toHaveBeenCalled();
  });

  it("inserts each chunk with metadata", async () => {
    await runPipeline(makeConfig({ dimension: 4, tenantId: "t1" }), client, provider, tempDataDir());
    expect(client.insert).toHaveBeenCalledTimes(2);
    for (const call of client.insert.mock.calls) {
      const arg = call[0];
      expect(arg.tenantId).toBe("t1");
      expect(arg.vector).toHaveLength(4);
      expect(arg.metadata).toHaveProperty("text");
      expect(arg.metadata).toHaveProperty("source");
    }
  });

  it("runs the demo search", async () => {
    await runPipeline(makeConfig({ dimension: 4 }), client, provider, tempDataDir());
    expect(client.search).toHaveBeenCalled();
  });

  it("does not insert when there are no documents", async () => {
    const emptyDir = mkdtempSync(join(tmpdir(), "tessera-empty-"));
    await runPipeline(makeConfig(), client, provider, emptyDir);
    expect(provider.embed).not.toHaveBeenCalled();
    expect(client.insert).not.toHaveBeenCalled();
  });
});
