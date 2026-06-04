namespace RagQuickstart;

/// <summary>
/// RAG quickstart entry point.
///
/// Reads tessera_config.json (or documented defaults), builds the real Tessera
/// client and embedding provider, and runs the ingest + demo-search pipeline.
///
/// Run: dotnet run --project src/RagQuickstart
/// </summary>
public static class Program
{
    public static async Task<int> Main(string[] args)
    {
        try
        {
            var config = ConfigLoader.Load();
            using var http = new HttpClient();
            using var client = new TesseraClientAdapter(config.Tessera);
            var provider = EmbeddingProviderFactory.Create(config.Embedding, http);

            var here = AppContext.BaseDirectory;
            var dataDir = Path.GetFullPath(Path.Combine(here, config.Ingestion.DataDir));
            if (!Directory.Exists(dataDir))
            {
                // Fall back to the data folder shipped next to the source.
                dataDir = Path.GetFullPath(Path.Combine(
                    AppContext.BaseDirectory, "..", "..", "..", "..", "..", "data"));
            }

            await Pipeline.RunAsync(config, client, provider, dataDir);
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }
}
