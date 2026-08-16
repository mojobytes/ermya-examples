using Ermya.Vector.V1;

using SdkClient = Ermya.Client.ErmyaClient;
using SdkClientOptions = Ermya.Client.ErmyaClientOptions;

namespace RagQuickstart;

/// <summary>
/// Adapts the real Ermya SDK (protobuf request/response types) to the example's
/// simple <see cref="IErmyaClient"/> surface, keeping the protobuf stack out of
/// the pipeline and its unit tests.
/// </summary>
public sealed class ErmyaClientAdapter : IErmyaClient, IDisposable
{
    private readonly SdkClient _client;

    public ErmyaClientAdapter(ErmyaConfig config)
    {
        _client = new SdkClient(new SdkClientOptions
        {
            Endpoint = Endpoint.Compose(config.Host, config.Port, config.Secure),
            ApiKey = config.ApiKey,
            AllowInsecureCredentialTransport = !config.Secure,
            AllowUntrustedCertificates = !config.Secure,
        });
    }

    public async Task CreateTenantAsync(string tenantId, int dimension)
    {
        await _client.CreateTenantAsync(new CreateTenantRequest
        {
            TenantName = tenantId,
            DefaultDatabaseDimension = (uint)dimension,
        });
    }

    public async Task<long> InsertAsync(InsertCommand command)
    {
        var request = new InsertRequest { TenantId = command.TenantId };
        request.Vector.AddRange(command.Vector);
        foreach (var (key, value) in command.Metadata)
        {
            request.Metadata[key] = new MetadataValue { StringValue = value?.ToString() ?? string.Empty };
        }

        var response = await _client.InsertAsync(request);
        return (long)response.Id;
    }

    public async Task<IReadOnlyList<SearchHit>> SearchAsync(string tenantId, float[] vector, int k)
    {
        var request = new SearchRequest { TenantId = tenantId, K = (uint)k };
        request.Vector.AddRange(vector);

        var response = await _client.SearchAsync(request);
        return response.Results
            .Select(r => new SearchHit(
                (long)r.Id,
                r.Distance,
                r.Metadata.ToDictionary(kv => kv.Key, object (kv) => kv.Value.StringValue)))
            .ToList();
    }

    public void Dispose() => _client.Dispose();
}
