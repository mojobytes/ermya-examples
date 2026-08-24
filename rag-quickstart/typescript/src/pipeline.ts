/**
 * RAG quickstart orchestration: parse -> chunk -> embed -> insert -> search.
 *
 * The Ermya client and embedding provider are injected so the whole flow is
 * unit-testable without a live Ermya or real HTTP. main.ts wires the real
 * implementations from config.
 */

import { chunkText, parseMarkdownFiles } from "./chunker.js";
import type { Config } from "./config-loader.js";
import { verifyDimension } from "./dimension-check.js";
import type { EmbeddingProvider } from "./embedding.js";
import type { ErmyaClientLike } from "./ermya-client-factory.js";

const BANNER =
  "=".repeat(64) +
  "\n  EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.\n" +
  "=".repeat(64);

async function ingestDocuments(
  client: ErmyaClientLike,
  provider: EmbeddingProvider,
  config: Config,
  dataDir: string,
): Promise<number[] | null> {
  const documents = await parseMarkdownFiles(dataDir);
  let firstVector: number[] | null = null;
  const { dimension } = config.embedding;
  const { tenantId } = config.ingestion;

  for (let sourceIndex = 0; sourceIndex < documents.length; sourceIndex++) {
    const chunks = chunkText(
      documents[sourceIndex],
      config.ingestion.chunkSize,
      config.ingestion.chunkOverlap,
    );
    for (let chunkIndex = 0; chunkIndex < chunks.length; chunkIndex++) {
      const vector = await provider.embed(chunks[chunkIndex]);
      if (firstVector === null) {
        verifyDimension(vector, dimension);
        firstVector = vector;
      }
      await client.insert({
        tenantId,
        vector,
        metadata: { text: chunks[chunkIndex], source: `doc:${sourceIndex}`, chunk: chunkIndex },
      });
    }
  }
  return firstVector;
}

async function demoSearch(
  client: ErmyaClientLike,
  config: Config,
  queryVector: number[],
): Promise<void> {
  const { results } = await client.search({
    tenantId: config.ingestion.tenantId,
    vector: queryVector,
    k: 5,
  });
  console.log(`\nDemo search returned ${results.length} result(s):`);
  for (const result of results) {
    const text = (result.metadata?.text as string | undefined) ?? "";
    console.log(`  - id=${result.id} distance=${result.distance}: ${text.slice(0, 60)}`);
  }
}

export async function runPipeline(
  config: Config,
  client: ErmyaClientLike,
  provider: EmbeddingProvider,
  dataDir: string,
): Promise<void> {
  console.log(BANNER);
  console.log(
    `\nTarget Ermya: ${config.ermya.host}:${config.ermya.port} ` +
      `(tenant '${config.ingestion.tenantId}', dimension ${config.embedding.dimension})`,
  );
  console.log(`Embedding provider: ${config.embedding.provider}\n`);

  await client.createTenant({
    tenantId: config.ingestion.tenantId,
    dimension: config.embedding.dimension,
  });

  const firstVector = await ingestDocuments(client, provider, config, dataDir);
  if (firstVector === null) {
    console.log(`No documents found in ${dataDir}; nothing ingested.`);
    return;
  }

  await demoSearch(client, config, firstVector);
}
