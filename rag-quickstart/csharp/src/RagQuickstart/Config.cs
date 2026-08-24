using System.Text.Json.Serialization;

namespace RagQuickstart;

public sealed record ErmyaConfig(
    [property: JsonPropertyName("host")] string Host,
    [property: JsonPropertyName("port")] int Port,
    [property: JsonPropertyName("api_key")] string ApiKey,
    [property: JsonPropertyName("secure")] bool Secure);

public sealed record EmbeddingConfig(
    [property: JsonPropertyName("provider")] string Provider,
    [property: JsonPropertyName("endpoint")] string Endpoint,
    [property: JsonPropertyName("api_key")] string ApiKey,
    [property: JsonPropertyName("model")] string Model,
    [property: JsonPropertyName("deployment_name")] string DeploymentName,
    [property: JsonPropertyName("dimension")] int Dimension);

public sealed record IngestionConfig(
    [property: JsonPropertyName("tenant_id")] string TenantId,
    [property: JsonPropertyName("chunk_size")] int ChunkSize,
    [property: JsonPropertyName("chunk_overlap")] int ChunkOverlap,
    [property: JsonPropertyName("data_dir")] string DataDir);

public sealed record Config(
    [property: JsonPropertyName("schema_version")] int SchemaVersion,
    [property: JsonPropertyName("ermya")] ErmyaConfig Ermya,
    [property: JsonPropertyName("embedding")] EmbeddingConfig Embedding,
    [property: JsonPropertyName("ingestion")] IngestionConfig Ingestion);
