using System.Text.Json;

using FluentAssertions;
using RagQuickstart;

namespace RagQuickstart.Tests;

public class EmbeddingProviderTests
{
    private static EmbeddingConfig Cfg(
        string provider = "openai",
        string endpoint = "",
        string apiKey = "",
        string model = "",
        string deploymentName = "",
        int dimension = 3)
        => new(provider, endpoint, apiKey, model, deploymentName, dimension);

    private static JsonElement ParseBody(string? body)
        => JsonDocument.Parse(body!).RootElement;

    [Fact]
    public async Task OpenAi_BuildsCorrectRequest_AndReturnsVector()
    {
        var handler = new FakeHttpMessageHandler("""{ "data": [ { "embedding": [0.1, 0.2, 0.3] } ] }""");
        var provider = new OpenAIEmbeddingProvider(
            Cfg(provider: "openai", apiKey: "sk-test", model: "text-embedding-3-small"),
            new HttpClient(handler));

        var vec = await provider.EmbedAsync("hello world");

        handler.LastRequest!.RequestUri!.ToString().Should().Be("https://api.openai.com/v1/embeddings");
        handler.LastRequest.Headers.Authorization!.ToString().Should().Be("Bearer sk-test");
        var body = ParseBody(handler.LastBody);
        body.GetProperty("model").GetString().Should().Be("text-embedding-3-small");
        body.GetProperty("input").GetString().Should().Be("hello world");
        vec.Should().Equal(0.1f, 0.2f, 0.3f);
    }

    [Fact]
    public async Task AzureOpenAi_UsesDeploymentUrl_AndApiKeyHeader()
    {
        var handler = new FakeHttpMessageHandler("""{ "data": [ { "embedding": [0.5, 0.6] } ] }""");
        var provider = new AzureOpenAIEmbeddingProvider(
            Cfg(provider: "azure-openai", endpoint: "https://myaccount.openai.azure.com",
                apiKey: "az-key", deploymentName: "my-deployment", dimension: 2),
            new HttpClient(handler));

        var vec = await provider.EmbedAsync("test text");

        var url = handler.LastRequest!.RequestUri!.ToString();
        url.Should().Contain("https://myaccount.openai.azure.com/openai/deployments/my-deployment/embeddings");
        url.Should().Contain("api-version=");
        handler.LastRequest.Headers.GetValues("api-key").Should().ContainSingle().Which.Should().Be("az-key");
        ParseBody(handler.LastBody).GetProperty("input").GetString().Should().Be("test text");
        vec.Should().Equal(0.5f, 0.6f);
    }

    [Fact]
    public async Task Ollama_CallsApiEmbeddings_WithNoAuthHeader()
    {
        var handler = new FakeHttpMessageHandler("""{ "embedding": [0.9, 0.8, 0.7] }""");
        var provider = new OllamaEmbeddingProvider(
            Cfg(provider: "ollama", endpoint: "http://localhost:11434", model: "nomic-embed-text"),
            new HttpClient(handler));

        var vec = await provider.EmbedAsync("my text");

        handler.LastRequest!.RequestUri!.ToString().Should().Be("http://localhost:11434/api/embeddings");
        handler.LastRequest.Headers.Authorization.Should().BeNull();
        var body = ParseBody(handler.LastBody);
        body.GetProperty("model").GetString().Should().Be("nomic-embed-text");
        body.GetProperty("prompt").GetString().Should().Be("my text");
        vec.Should().Equal(0.9f, 0.8f, 0.7f);
    }

    [Theory]
    [InlineData("openai", typeof(OpenAIEmbeddingProvider))]
    [InlineData("azure-openai", typeof(AzureOpenAIEmbeddingProvider))]
    [InlineData("ollama", typeof(OllamaEmbeddingProvider))]
    public void Factory_Creates_CorrectProvider(string provider, Type expected)
    {
        var instance = EmbeddingProviderFactory.Create(Cfg(provider: provider), new HttpClient());
        instance.Should().BeOfType(expected);
    }

    [Fact]
    public void Factory_Throws_OnUnknownProvider()
    {
        var act = () => EmbeddingProviderFactory.Create(Cfg(provider: "not-a-provider"), new HttpClient());
        act.Should().Throw<ArgumentException>().WithMessage("*Unknown embedding provider*");
    }
}
