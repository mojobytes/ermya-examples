/**
 * Load tessera_config.json by walking up to the repo root, or fall back to
 * documented defaults so the example runs standalone.
 *
 * The Tessera Launchpad writes tessera_config.json into the repository root.
 * Examples live in rag-quickstart/<lang>/, so we search upward from the start
 * directory to find it.
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

const CONFIG_FILENAME = "tessera_config.json";
const SUPPORTED_SCHEMA_VERSION = 1;

export interface TesseraConfig {
  host: string;
  port: number;
  apiKey: string;
  secure: boolean;
}

export interface EmbeddingConfig {
  provider: string;
  endpoint: string;
  apiKey: string;
  model: string;
  deploymentName: string;
  dimension: number;
}

export interface IngestionConfig {
  tenantId: string;
  chunkSize: number;
  chunkOverlap: number;
  dataDir: string;
}

export interface Config {
  tessera: TesseraConfig;
  embedding: EmbeddingConfig;
  ingestion: IngestionConfig;
}

function defaultConfig(): Config {
  return {
    tessera: { host: "localhost", port: 50051, apiKey: "", secure: false },
    embedding: {
      provider: "ollama",
      endpoint: "http://localhost:11434",
      apiKey: "",
      model: "nomic-embed-text",
      deploymentName: "",
      dimension: 768,
    },
    ingestion: {
      tenantId: "rag-quickstart",
      chunkSize: 800,
      chunkOverlap: 100,
      dataDir: "./data",
    },
  };
}

function findConfigFile(startDir: string): string | null {
  let current = resolve(startDir);
  for (;;) {
    const candidate = join(current, CONFIG_FILENAME);
    if (existsSync(candidate)) {
      return candidate;
    }
    const parent = dirname(current);
    if (parent === current) {
      return null;
    }
    current = parent;
  }
}

function parseConfig(data: any): Config {
  if (data.schema_version !== SUPPORTED_SCHEMA_VERSION) {
    throw new Error(
      `Unsupported schema_version ${JSON.stringify(data.schema_version)}; ` +
        `this example supports schema_version ${SUPPORTED_SCHEMA_VERSION}.`,
    );
  }
  const t = data.tessera;
  const e = data.embedding;
  const i = data.ingestion;
  return {
    tessera: {
      host: t.host,
      port: Number(t.port),
      apiKey: t.api_key ?? "",
      secure: Boolean(t.secure ?? false),
    },
    embedding: {
      provider: e.provider,
      endpoint: e.endpoint ?? "",
      apiKey: e.api_key ?? "",
      model: e.model ?? "",
      deploymentName: e.deployment_name ?? "",
      dimension: Number(e.dimension),
    },
    ingestion: {
      tenantId: i.tenant_id,
      chunkSize: Number(i.chunk_size),
      chunkOverlap: Number(i.chunk_overlap),
      dataDir: i.data_dir ?? "./data",
    },
  };
}

export function loadConfig(startDir: string = process.cwd()): Config {
  const configPath = findConfigFile(startDir);
  if (configPath === null) {
    return defaultConfig();
  }
  const data = JSON.parse(readFileSync(configPath, "utf-8"));
  return parseConfig(data);
}
