using System.Text;
using System.Text.Json;

namespace RagQuickstart;

/// <summary>
/// Real embedding providers selectable by config: openai, azure-openai, ollama.
/// Each calls the provider's HTTP embeddings API; HttpClient is injected so the
/// providers are testable without real network access.
/// </summary>
public interface IEmbeddingProvider
{
    Task<float[]> EmbedAsync(string text);
}

internal static class EmbeddingHttp
{
    public const string AzureApiVersion = "2024-02-01";

    public static async Task<JsonElement> PostJsonAsync(
        HttpClient client,
        string url,
        object body,
        IReadOnlyDictionary<string, string>? headers = null)
    {
        using var request = new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json"),
        };
        if (headers is not null)
        {
            foreach (var (key, value) in headers)
            {
                request.Headers.TryAddWithoutValidation(key, value);
            }
        }

        using var response = await client.SendAsync(request);
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        return JsonDocument.Parse(json).RootElement.Clone();
    }

    public static float[] ReadOpenAiVector(JsonElement root)
        => ReadFloats(root.GetProperty("data")[0].GetProperty("embedding"));

    public static float[] ReadOllamaVector(JsonElement root)
        => ReadFloats(root.GetProperty("embedding"));

    private static float[] ReadFloats(JsonElement array)
    {
        var result = new float[array.GetArrayLength()];
        var i = 0;
        foreach (var item in array.EnumerateArray())
        {
            result[i++] = item.GetSingle();
        }

        return result;
    }
}

public sealed class OpenAIEmbeddingProvider : IEmbeddingProvider
{
    private readonly EmbeddingConfig _config;
    private readonly HttpClient _client;

    public OpenAIEmbeddingProvider(EmbeddingConfig config, HttpClient client)
    {
        _config = config;
        _client = client;
    }

    public async Task<float[]> EmbedAsync(string text)
    {
        var root = await EmbeddingHttp.PostJsonAsync(
            _client,
            "https://api.openai.com/v1/embeddings",
            new { model = _config.Model, input = text },
            new Dictionary<string, string> { ["Authorization"] = $"Bearer {_config.ApiKey}" });
        return EmbeddingHttp.ReadOpenAiVector(root);
    }
}

public sealed class AzureOpenAIEmbeddingProvider : IEmbeddingProvider
{
    private readonly EmbeddingConfig _config;
    private readonly HttpClient _client;

    public AzureOpenAIEmbeddingProvider(EmbeddingConfig config, HttpClient client)
    {
        _config = config;
        _client = client;
    }

    public async Task<float[]> EmbedAsync(string text)
    {
        var endpoint = _config.Endpoint.TrimEnd('/');
        var url =
            $"{endpoint}/openai/deployments/{_config.DeploymentName}/embeddings" +
            $"?api-version={EmbeddingHttp.AzureApiVersion}";
        var root = await EmbeddingHttp.PostJsonAsync(
            _client,
            url,
            new { input = text },
            new Dictionary<string, string> { ["api-key"] = _config.ApiKey });
        return EmbeddingHttp.ReadOpenAiVector(root);
    }
}

public sealed class OllamaEmbeddingProvider : IEmbeddingProvider
{
    private readonly EmbeddingConfig _config;
    private readonly HttpClient _client;

    public OllamaEmbeddingProvider(EmbeddingConfig config, HttpClient client)
    {
        _config = config;
        _client = client;
    }

    public async Task<float[]> EmbedAsync(string text)
    {
        var endpoint = _config.Endpoint.TrimEnd('/');
        var root = await EmbeddingHttp.PostJsonAsync(
            _client,
            $"{endpoint}/api/embeddings",
            new { model = _config.Model, prompt = text });
        return EmbeddingHttp.ReadOllamaVector(root);
    }
}

public static class EmbeddingProviderFactory
{
    public static IEmbeddingProvider Create(EmbeddingConfig config, HttpClient client) => config.Provider switch
    {
        "openai" => new OpenAIEmbeddingProvider(config, client),
        "azure-openai" => new AzureOpenAIEmbeddingProvider(config, client),
        "ollama" => new OllamaEmbeddingProvider(config, client),
        _ => throw new ArgumentException(
            $"Unknown embedding provider: '{config.Provider}'. " +
            "Supported: azure-openai, ollama, openai.",
            nameof(config)),
    };
}
