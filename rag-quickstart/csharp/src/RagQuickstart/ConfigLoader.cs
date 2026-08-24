using System.Text.Json;

namespace RagQuickstart;

/// <summary>
/// Load ermya_config.json by walking up to the repo root, or fall back to
/// documented defaults so the example runs standalone.
/// </summary>
public static class ConfigLoader
{
    private const string ConfigFilename = "ermya_config.json";
    private const int SupportedSchemaVersion = 1;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public static Config Default() => new(
        SchemaVersion: SupportedSchemaVersion,
        Ermya: new ErmyaConfig("localhost", 50051, ApiKey: "", Secure: false),
        Embedding: new EmbeddingConfig(
            Provider: "ollama",
            Endpoint: "http://localhost:11434",
            ApiKey: "",
            Model: "nomic-embed-text",
            DeploymentName: "",
            Dimension: 768),
        Ingestion: new IngestionConfig(
            TenantId: "rag-quickstart",
            ChunkSize: 800,
            ChunkOverlap: 100,
            DataDir: "./data"));

    public static Config Load(string? startDir = null)
    {
        var path = FindConfigFile(startDir ?? Directory.GetCurrentDirectory());
        if (path is null)
        {
            return Default();
        }

        var config = JsonSerializer.Deserialize<Config>(File.ReadAllText(path), JsonOptions)
            ?? throw new InvalidOperationException($"Failed to parse {ConfigFilename}.");

        if (config.SchemaVersion != SupportedSchemaVersion)
        {
            throw new InvalidOperationException(
                $"Unsupported schema_version {config.SchemaVersion}; this example " +
                $"supports schema_version {SupportedSchemaVersion}.");
        }

        return config;
    }

    private static string? FindConfigFile(string startDir)
    {
        var current = new DirectoryInfo(Path.GetFullPath(startDir));
        while (current is not null)
        {
            var candidate = Path.Combine(current.FullName, ConfigFilename);
            if (File.Exists(candidate))
            {
                return candidate;
            }

            current = current.Parent;
        }

        return null;
    }
}
