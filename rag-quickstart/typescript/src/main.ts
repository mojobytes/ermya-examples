/**
 * RAG quickstart entry point.
 *
 * Reads ermya_config.json (or documented defaults), builds the real Ermya
 * client and embedding provider, and runs the ingest + demo-search pipeline.
 *
 * Run: node --loader ts-node/esm src/main.ts
 */

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { loadConfig } from "./config-loader.js";
import { createProvider } from "./embedding.js";
import { runPipeline } from "./pipeline.js";
import { createClient } from "./ermya-client-factory.js";

export async function main(): Promise<void> {
  const config = loadConfig();
  const client = createClient(config.ermya);
  const provider = createProvider(config.embedding);

  const here = dirname(fileURLToPath(import.meta.url));
  const dataDir = resolve(here, "..", config.ingestion.dataDir);
  await runPipeline(config, client, provider, dataDir);
}

const isMainModule =
  import.meta.url === `file://${process.argv[1]}` ||
  process.argv[1]?.endsWith("main.ts");
if (isMainModule) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  });
}
