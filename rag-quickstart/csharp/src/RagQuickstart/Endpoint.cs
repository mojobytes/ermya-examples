namespace RagQuickstart;

/// <summary>
/// Compose the scheme-prefixed endpoint URL the .NET SDK expects.
/// </summary>
public static class Endpoint
{
    public static string Compose(string host, int port, bool secure)
    {
        var scheme = secure ? "https" : "http";
        return $"{scheme}://{host}:{port}";
    }
}
