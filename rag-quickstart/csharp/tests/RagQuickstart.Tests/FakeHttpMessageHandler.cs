using System.Net;

namespace RagQuickstart.Tests;

/// <summary>
/// Captures the outgoing request and returns a canned JSON response, so
/// embedding providers can be tested without real network access.
/// </summary>
public sealed class FakeHttpMessageHandler : HttpMessageHandler
{
    private readonly string _responseJson;

    public HttpRequestMessage? LastRequest { get; private set; }
    public string? LastBody { get; private set; }

    public FakeHttpMessageHandler(string responseJson) => _responseJson = responseJson;

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        LastRequest = request;
        LastBody = request.Content is null ? null : await request.Content.ReadAsStringAsync(cancellationToken);
        return new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(_responseJson),
        };
    }
}
