import { describe, expect, it, jest } from "@jest/globals";

// Mock the SDK-touching and IO modules so main() can be wired-tested without
// loading the gRPC stack or hitting the network.
const createClient = jest.fn(() => ({ tag: "client" }));
const createProvider = jest.fn(() => ({ tag: "provider" }));
const loadConfig = jest.fn(() => ({
  ermya: { host: "localhost", port: 50051, apiKey: "", secure: false },
  embedding: { provider: "ollama", endpoint: "", apiKey: "", model: "", deploymentName: "", dimension: 768 },
  ingestion: { tenantId: "rag-quickstart", chunkSize: 800, chunkOverlap: 100, dataDir: "./data" },
}));
const runPipeline = jest.fn(async () => {});

jest.unstable_mockModule("../src/ermya-client-factory.js", () => ({ createClient }));
jest.unstable_mockModule("../src/embedding.js", () => ({ createProvider }));
jest.unstable_mockModule("../src/config-loader.js", () => ({ loadConfig }));
jest.unstable_mockModule("../src/pipeline.js", () => ({ runPipeline }));

const { main } = await import("../src/main.js");

describe("main", () => {
  it("wires config, client and provider into the pipeline", async () => {
    await main();
    expect(loadConfig).toHaveBeenCalled();
    expect(createClient).toHaveBeenCalled();
    expect(createProvider).toHaveBeenCalled();
    expect(runPipeline).toHaveBeenCalled();
    const [config, client, provider] = runPipeline.mock.calls[0] as unknown[];
    expect((client as { tag: string }).tag).toBe("client");
    expect((provider as { tag: string }).tag).toBe("provider");
    expect(config).toBeDefined();
  });
});
