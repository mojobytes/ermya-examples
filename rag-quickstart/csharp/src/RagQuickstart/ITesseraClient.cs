namespace RagQuickstart;

/// <summary>
/// A command to insert one vector with its metadata into a tenant.
/// </summary>
public sealed record InsertCommand(
    string TenantId,
    float[] Vector,
    IReadOnlyDictionary<string, object> Metadata);

/// <summary>
/// One nearest-neighbour result from a search.
/// </summary>
public sealed record SearchHit(long Id, float Distance, IReadOnlyDictionary<string, object> Metadata);

/// <summary>
/// The slice of Tessera the example uses. Keeping our own interface (instead of
/// depending on the SDK's protobuf types directly) lets the pipeline be mocked
/// without dragging the gRPC stack into unit tests. A thin adapter over the real
/// SDK implements this.
/// </summary>
public interface ITesseraClient
{
    Task CreateTenantAsync(string tenantId, int dimension);

    Task<long> InsertAsync(InsertCommand command);

    Task<IReadOnlyList<SearchHit>> SearchAsync(string tenantId, float[] vector, int k);
}
