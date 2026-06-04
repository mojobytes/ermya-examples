using FluentAssertions;
using RagQuickstart;

namespace RagQuickstart.Tests;

public class EndpointTests
{
    [Fact]
    public void Compose_UsesHttp_WhenNotSecure()
    {
        Endpoint.Compose("localhost", 50051, false).Should().Be("http://localhost:50051");
    }

    [Fact]
    public void Compose_UsesHttps_WhenSecure()
    {
        Endpoint.Compose("api.example.com", 443, true).Should().Be("https://api.example.com:443");
    }
}
