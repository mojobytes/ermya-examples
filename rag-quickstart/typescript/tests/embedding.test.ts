import { afterEach, describe, expect, it, jest } from "@jest/globals";

import {
  AzureOpenAIProvider,
  OllamaProvider,
  OpenAIProvider,
  createProvider,
} from "../src/embedding.js";
import type { EmbeddingConfig } from "../src/config-loader.js";

function cfg(overrides: Partial<EmbeddingConfig> = {}): EmbeddingConfig {
  return {
    provider: "openai",
    endpoint: "",
    apiKey: "",
    model: "",
    deploymentName: "",
    dimension: 3,
    ...overrides,
  };
}

function mockFetch(jsonBody: unknown) {
  const spy = jest.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(jsonBody), { status: 200 }),
  );
  return spy;
}

afterEach(() => {
  jest.restoreAllMocks();
});

describe("OpenAIProvider", () => {
  it("builds the correct request and returns the vector", async () => {
    const spy = mockFetch({ data: [{ embedding: [0.1, 0.2, 0.3] }] });
    const provider = new OpenAIProvider(
      cfg({ provider: "openai", apiKey: "sk-test", model: "text-embedding-3-small" }),
    );
    const vec = await provider.embed("hello world");

    const [url, init] = spy.mock.calls[0];
    expect(url).toBe("https://api.openai.com/v1/embeddings");
    const headers = init!.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer sk-test");
    const body = JSON.parse(init!.body as string);
    expect(body.model).toBe("text-embedding-3-small");
    expect(body.input).toBe("hello world");
    expect(vec).toEqual([0.1, 0.2, 0.3]);
  });
});

describe("AzureOpenAIProvider", () => {
  it("uses the deployment URL and api-key header", async () => {
    const spy = mockFetch({ data: [{ embedding: [0.5, 0.6] }] });
    const provider = new AzureOpenAIProvider(
      cfg({
        provider: "azure-openai",
        endpoint: "https://myaccount.openai.azure.com",
        apiKey: "az-key",
        deploymentName: "my-deployment",
        dimension: 2,
      }),
    );
    const vec = await provider.embed("test text");

    const [url, init] = spy.mock.calls[0];
    expect(url).toContain(
      "https://myaccount.openai.azure.com/openai/deployments/my-deployment/embeddings",
    );
    expect(url).toContain("api-version=");
    const headers = init!.headers as Record<string, string>;
    expect(headers["api-key"]).toBe("az-key");
    expect(JSON.parse(init!.body as string).input).toBe("test text");
    expect(vec).toEqual([0.5, 0.6]);
  });
});

describe("OllamaProvider", () => {
  it("calls /api/embeddings with no auth header", async () => {
    const spy = mockFetch({ embedding: [0.9, 0.8, 0.7] });
    const provider = new OllamaProvider(
      cfg({
        provider: "ollama",
        endpoint: "http://localhost:11434",
        model: "nomic-embed-text",
      }),
    );
    const vec = await provider.embed("my text");

    const [url, init] = spy.mock.calls[0];
    expect(url).toBe("http://localhost:11434/api/embeddings");
    const headers = (init!.headers ?? {}) as Record<string, string>;
    expect(headers["Authorization"]).toBeUndefined();
    const body = JSON.parse(init!.body as string);
    expect(body.model).toBe("nomic-embed-text");
    expect(body.prompt).toBe("my text");
    expect(vec).toEqual([0.9, 0.8, 0.7]);
  });
});

describe("createProvider", () => {
  it.each([
    ["openai", OpenAIProvider],
    ["azure-openai", AzureOpenAIProvider],
    ["ollama", OllamaProvider],
  ])("returns the %s provider instance", (name, klass) => {
    const provider = createProvider(cfg({ provider: name }));
    expect(provider).toBeInstanceOf(klass as new (...args: any[]) => unknown);
  });

  it("throws on an unknown provider", () => {
    expect(() => createProvider(cfg({ provider: "not-a-provider" }))).toThrow(
      /Unknown embedding provider/,
    );
  });
});
