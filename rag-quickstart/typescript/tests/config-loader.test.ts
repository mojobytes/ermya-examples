import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { loadConfig } from "../src/config-loader.js";

const MINIMAL_CONFIG = {
  _warning: "w",
  schema_version: 1,
  ermya: { host: "myhost", port: 9999, api_key: "k", secure: false },
  embedding: {
    provider: "openai",
    endpoint: "",
    api_key: "ek",
    model: "text-embedding-3-small",
    deployment_name: "",
    dimension: 1536,
  },
  ingestion: {
    tenant_id: "t1",
    chunk_size: 800,
    chunk_overlap: 100,
    data_dir: "./data",
  },
};

function tempDir(): string {
  return mkdtempSync(join(tmpdir(), "ermya-cfg-"));
}

function writeConfig(dir: string, data: unknown = MINIMAL_CONFIG): void {
  writeFileSync(join(dir, "ermya_config.json"), JSON.stringify(data));
}

describe("loadConfig", () => {
  it("reads the ermya block from a present file", () => {
    const dir = tempDir();
    writeConfig(dir);
    const config = loadConfig(dir);
    expect(config.ermya.host).toBe("myhost");
    expect(config.ermya.port).toBe(9999);
    expect(config.ermya.apiKey).toBe("k");
    expect(config.ermya.secure).toBe(false);
  });

  it("reads embedding and ingestion blocks", () => {
    const dir = tempDir();
    writeConfig(dir);
    const config = loadConfig(dir);
    expect(config.embedding.provider).toBe("openai");
    expect(config.embedding.model).toBe("text-embedding-3-small");
    expect(config.embedding.dimension).toBe(1536);
    expect(config.ingestion.tenantId).toBe("t1");
    expect(config.ingestion.chunkSize).toBe(800);
    expect(config.ingestion.chunkOverlap).toBe(100);
  });

  it("returns documented defaults when the file is absent", () => {
    const dir = tempDir();
    const config = loadConfig(dir);
    expect(config.ermya.host).toBe("localhost");
    expect(config.ermya.port).toBe(50051);
    expect(config.embedding.provider).toBe("ollama");
    expect(config.embedding.endpoint).toBe("http://localhost:11434");
    expect(config.embedding.model).toBe("nomic-embed-text");
    expect(config.embedding.dimension).toBe(768);
    expect(config.ingestion.tenantId).toBe("rag-quickstart");
  });

  it("walks up to find the file in an ancestor directory", () => {
    const root = tempDir();
    const nested = join(root, "a", "b", "c");
    mkdirSync(nested, { recursive: true });
    writeConfig(root);
    const config = loadConfig(nested);
    expect(config.ermya.host).toBe("myhost");
  });

  it("throws on an unknown schema version", () => {
    const dir = tempDir();
    writeConfig(dir, { ...MINIMAL_CONFIG, schema_version: 99 });
    expect(() => loadConfig(dir)).toThrow(/schema_version/);
  });
});
