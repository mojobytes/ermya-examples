using FluentAssertions;
using RagQuickstart;

namespace RagQuickstart.Tests;

public class ConfigLoaderTests
{
    private const string MinimalConfigJson = """
        {
          "_warning": "w",
          "schema_version": 1,
          "ermya": { "host": "myhost", "port": 9999, "api_key": "k", "secure": false },
          "embedding": {
            "provider": "openai", "endpoint": "", "api_key": "ek",
            "model": "text-embedding-3-small", "deployment_name": "", "dimension": 1536
          },
          "ingestion": {
            "tenant_id": "t1", "chunk_size": 800, "chunk_overlap": 100, "data_dir": "./data"
          }
        }
        """;

    private static string NewTempDir()
    {
        var dir = Path.Combine(Path.GetTempPath(), "ermya-cfg-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        return dir;
    }

    private static void WriteConfig(string dir, string json = MinimalConfigJson)
        => File.WriteAllText(Path.Combine(dir, "ermya_config.json"), json);

    [Fact]
    public void Load_ReadsErmyaBlock_FromPresentFile()
    {
        var dir = NewTempDir();
        WriteConfig(dir);
        var config = ConfigLoader.Load(dir);
        config.Ermya.Host.Should().Be("myhost");
        config.Ermya.Port.Should().Be(9999);
        config.Ermya.ApiKey.Should().Be("k");
        config.Ermya.Secure.Should().BeFalse();
    }

    [Fact]
    public void Load_ReadsEmbeddingAndIngestion()
    {
        var dir = NewTempDir();
        WriteConfig(dir);
        var config = ConfigLoader.Load(dir);
        config.Embedding.Provider.Should().Be("openai");
        config.Embedding.Model.Should().Be("text-embedding-3-small");
        config.Embedding.Dimension.Should().Be(1536);
        config.Ingestion.TenantId.Should().Be("t1");
        config.Ingestion.ChunkSize.Should().Be(800);
        config.Ingestion.ChunkOverlap.Should().Be(100);
    }

    [Fact]
    public void Load_ReturnsDefaults_WhenFileAbsent()
    {
        var config = ConfigLoader.Load(NewTempDir());
        config.Ermya.Host.Should().Be("localhost");
        config.Ermya.Port.Should().Be(50051);
        config.Embedding.Provider.Should().Be("ollama");
        config.Embedding.Endpoint.Should().Be("http://localhost:11434");
        config.Embedding.Model.Should().Be("nomic-embed-text");
        config.Embedding.Dimension.Should().Be(768);
        config.Ingestion.TenantId.Should().Be("rag-quickstart");
    }

    [Fact]
    public void Load_WalksUp_ToFindFileInAncestor()
    {
        var root = NewTempDir();
        var nested = Path.Combine(root, "a", "b", "c");
        Directory.CreateDirectory(nested);
        WriteConfig(root);
        var config = ConfigLoader.Load(nested);
        config.Ermya.Host.Should().Be("myhost");
    }

    [Fact]
    public void Load_Throws_OnUnknownSchemaVersion()
    {
        var dir = NewTempDir();
        WriteConfig(dir, MinimalConfigJson.Replace("\"schema_version\": 1", "\"schema_version\": 99"));
        var act = () => ConfigLoader.Load(dir);
        act.Should().Throw<InvalidOperationException>().WithMessage("*schema_version*");
    }
}
