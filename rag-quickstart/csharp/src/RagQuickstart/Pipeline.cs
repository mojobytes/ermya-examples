namespace RagQuickstart;

/// <summary>
/// RAG quickstart orchestration: parse -> chunk -> embed -> insert -> search.
/// The Ermya client and embedding provider are injected so the whole flow is
/// unit-testable without a live Ermya or real HTTP.
/// </summary>
public static class Pipeline
{
    private static readonly string Banner =
        new string('=', 64) +
        "\n  EXAMPLE / QUICKSTART — keys in plaintext, not production-ready.\n" +
        new string('=', 64);

    public static async Task RunAsync(
        Config config,
        IErmyaClient client,
        IEmbeddingProvider provider,
        string dataDir)
    {
        Console.WriteLine(Banner);
        Console.WriteLine(
            $"\nTarget Ermya: {config.Ermya.Host}:{config.Ermya.Port} " +
            $"(tenant '{config.Ingestion.TenantId}', dimension {config.Embedding.Dimension})");
        Console.WriteLine($"Embedding provider: {config.Embedding.Provider}\n");

        await client.CreateTenantAsync(config.Ingestion.TenantId, config.Embedding.Dimension);

        var firstVector = await IngestDocumentsAsync(client, provider, config, dataDir);
        if (firstVector is null)
        {
            Console.WriteLine($"No documents found in {dataDir}; nothing ingested.");
            return;
        }

        await DemoSearchAsync(client, config, firstVector);
    }

    private static async Task<float[]?> IngestDocumentsAsync(
        IErmyaClient client,
        IEmbeddingProvider provider,
        Config config,
        string dataDir)
    {
        var documents = await Chunker.ParseMarkdownFilesAsync(dataDir);
        float[]? firstVector = null;
        var dimension = config.Embedding.Dimension;
        var tenantId = config.Ingestion.TenantId;

        for (var sourceIndex = 0; sourceIndex < documents.Count; sourceIndex++)
        {
            var chunks = Chunker.ChunkText(
                documents[sourceIndex],
                config.Ingestion.ChunkSize,
                config.Ingestion.ChunkOverlap);

            for (var chunkIndex = 0; chunkIndex < chunks.Count; chunkIndex++)
            {
                var vector = await provider.EmbedAsync(chunks[chunkIndex]);
                if (firstVector is null)
                {
                    DimensionCheck.Verify(vector, dimension);
                    firstVector = vector;
                }

                await client.InsertAsync(new InsertCommand(
                    tenantId,
                    vector,
                    new Dictionary<string, object>
                    {
                        ["text"] = chunks[chunkIndex],
                        ["source"] = $"doc:{sourceIndex}",
                        ["chunk"] = chunkIndex,
                    }));
            }
        }

        return firstVector;
    }

    private static async Task DemoSearchAsync(IErmyaClient client, Config config, float[] queryVector)
    {
        var results = await client.SearchAsync(config.Ingestion.TenantId, queryVector, 5);
        Console.WriteLine($"\nDemo search returned {results.Count} result(s):");
        foreach (var hit in results)
        {
            var text = hit.Metadata.TryGetValue("text", out var value) ? value?.ToString() ?? "" : "";
            var preview = text.Length > 60 ? text[..60] : text;
            Console.WriteLine($"  - id={hit.Id} distance={hit.Distance}: {preview}");
        }
    }
}
