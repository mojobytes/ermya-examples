/**
 * Real embedding providers selectable by config: openai, azure-openai, ollama.
 *
 * Each provider implements EmbeddingProvider.embed(text) by calling the
 * provider's real HTTP embeddings API via fetch. The provider is chosen from
 * embedding.provider via createProvider().
 */

import type { EmbeddingConfig } from "./config-loader.js";

const AZURE_API_VERSION = "2024-02-01";

export interface EmbeddingProvider {
  embed(text: string): Promise<number[]>;
}

async function postJson(
  url: string,
  body: unknown,
  headers: Record<string, string>,
): Promise<any> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Embedding request failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export class OpenAIProvider implements EmbeddingProvider {
  constructor(private readonly config: EmbeddingConfig) {}

  async embed(text: string): Promise<number[]> {
    const data = await postJson(
      "https://api.openai.com/v1/embeddings",
      { model: this.config.model, input: text },
      { Authorization: `Bearer ${this.config.apiKey}` },
    );
    return data.data[0].embedding;
  }
}

export class AzureOpenAIProvider implements EmbeddingProvider {
  constructor(private readonly config: EmbeddingConfig) {}

  async embed(text: string): Promise<number[]> {
    const endpoint = this.config.endpoint.replace(/\/+$/, "");
    const url =
      `${endpoint}/openai/deployments/${this.config.deploymentName}/embeddings` +
      `?api-version=${AZURE_API_VERSION}`;
    const data = await postJson(url, { input: text }, { "api-key": this.config.apiKey });
    return data.data[0].embedding;
  }
}

export class OllamaProvider implements EmbeddingProvider {
  constructor(private readonly config: EmbeddingConfig) {}

  async embed(text: string): Promise<number[]> {
    const endpoint = this.config.endpoint.replace(/\/+$/, "");
    const data = await postJson(
      `${endpoint}/api/embeddings`,
      { model: this.config.model, prompt: text },
      {},
    );
    return data.embedding;
  }
}

type ProviderCtor = new (config: EmbeddingConfig) => EmbeddingProvider;

const PROVIDER_REGISTRY: Record<string, ProviderCtor> = {
  openai: OpenAIProvider,
  "azure-openai": AzureOpenAIProvider,
  ollama: OllamaProvider,
};

export function createProvider(config: EmbeddingConfig): EmbeddingProvider {
  const ctor = PROVIDER_REGISTRY[config.provider];
  if (ctor === undefined) {
    throw new Error(
      `Unknown embedding provider: ${JSON.stringify(config.provider)}. ` +
        `Supported: ${Object.keys(PROVIDER_REGISTRY).sort().join(", ")}.`,
    );
  }
  return new ctor(config);
}
