using FluentAssertions;
using Moq;
using RagQuickstart;

namespace RagQuickstart.Tests;

public class PipelineTests
{
    private static Config MakeConfig(int dimension = 4, string tenantId = "rag-quickstart", int chunkSize = 10, int chunkOverlap = 0)
        => new(
            SchemaVersion: 1,
            Tessera: new TesseraConfig("localhost", 50051, "k", false),
            Embedding: new EmbeddingConfig("ollama", "http://localhost:11434", "", "nomic-embed-text", "", dimension),
            Ingestion: new IngestionConfig(tenantId, chunkSize, chunkOverlap, "./data"));

    private static string TempDataDir(string content = "abcdefghijABCDEFGHIJ")
    {
        var dir = Path.Combine(Path.GetTempPath(), "tessera-pipe-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        File.WriteAllText(Path.Combine(dir, "doc.md"), content);
        return dir;
    }

    private static (Mock<ITesseraClient> client, Mock<IEmbeddingProvider> provider) Mocks(int dimension = 4)
    {
        var client = new Mock<ITesseraClient>();
        client.Setup(c => c.CreateTenantAsync(It.IsAny<string>(), It.IsAny<int>())).Returns(Task.CompletedTask);
        client.Setup(c => c.InsertAsync(It.IsAny<InsertCommand>())).ReturnsAsync(1L);
        client.Setup(c => c.SearchAsync(It.IsAny<string>(), It.IsAny<float[]>(), It.IsAny<int>()))
            .ReturnsAsync(Array.Empty<SearchHit>());

        var provider = new Mock<IEmbeddingProvider>();
        provider.Setup(p => p.EmbedAsync(It.IsAny<string>()))
            .ReturnsAsync(new float[dimension]);
        return (client, provider);
    }

    [Fact]
    public async Task CreatesTenant_WithConfigDimension()
    {
        var (client, provider) = Mocks();
        await Pipeline.RunAsync(MakeConfig(dimension: 4, tenantId: "my-tenant"), client.Object, provider.Object, TempDataDir());
        client.Verify(c => c.CreateTenantAsync("my-tenant", 4), Times.Once);
    }

    [Fact]
    public async Task EmbedsEachChunk()
    {
        var (client, provider) = Mocks();
        await Pipeline.RunAsync(MakeConfig(chunkSize: 10, chunkOverlap: 0), client.Object, provider.Object, TempDataDir());
        provider.Verify(p => p.EmbedAsync(It.IsAny<string>()), Times.Exactly(2));
    }

    [Fact]
    public async Task VerifiesDimensionAfterFirstEmbed_FailsBeforeInserting()
    {
        var (client, provider) = Mocks();
        provider.Setup(p => p.EmbedAsync(It.IsAny<string>())).ReturnsAsync(new float[384]);
        var act = async () => await Pipeline.RunAsync(MakeConfig(dimension: 1536), client.Object, provider.Object, TempDataDir());
        await act.Should().ThrowAsync<InvalidOperationException>().WithMessage("*Dimension mismatch*");
        client.Verify(c => c.InsertAsync(It.IsAny<InsertCommand>()), Times.Never);
    }

    [Fact]
    public async Task InsertsEachChunk_WithMetadata()
    {
        var (client, provider) = Mocks();
        var captured = new List<InsertCommand>();
        client.Setup(c => c.InsertAsync(It.IsAny<InsertCommand>()))
            .Callback<InsertCommand>(captured.Add)
            .ReturnsAsync(1L);

        await Pipeline.RunAsync(MakeConfig(dimension: 4, tenantId: "t1"), client.Object, provider.Object, TempDataDir());

        captured.Should().HaveCount(2);
        captured.Should().OnlyContain(cmd =>
            cmd.TenantId == "t1" && cmd.Vector.Length == 4 &&
            cmd.Metadata.ContainsKey("text") && cmd.Metadata.ContainsKey("source"));
    }

    [Fact]
    public async Task RunsDemoSearch()
    {
        var (client, provider) = Mocks();
        await Pipeline.RunAsync(MakeConfig(dimension: 4), client.Object, provider.Object, TempDataDir());
        client.Verify(c => c.SearchAsync(It.IsAny<string>(), It.IsAny<float[]>(), It.IsAny<int>()), Times.Once);
    }

    [Fact]
    public async Task NoDocuments_DoesNotInsert()
    {
        var (client, provider) = Mocks();
        var emptyDir = Path.Combine(Path.GetTempPath(), "tessera-empty-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(emptyDir);
        await Pipeline.RunAsync(MakeConfig(), client.Object, provider.Object, emptyDir);
        provider.Verify(p => p.EmbedAsync(It.IsAny<string>()), Times.Never);
        client.Verify(c => c.InsertAsync(It.IsAny<InsertCommand>()), Times.Never);
    }
}
