namespace RagQuickstart;

/// <summary>
/// Fail-fast verification that the provider returns vectors of the configured
/// dimension. The config is the source of truth; the example verifies reality
/// matches it (important for Ollama and custom models the launchpad cannot map).
/// </summary>
public static class DimensionCheck
{
    public static void Verify(IReadOnlyCollection<float> vector, int expected)
    {
        var actual = vector.Count;
        if (actual != expected)
        {
            throw new InvalidOperationException(
                $"Dimension mismatch: the embedding provider returned a vector of " +
                $"length {actual}, but ermya_config.json declares " +
                $"embedding.dimension = {expected}. Update embedding.dimension to " +
                $"match the model's output size, or pick a matching model.");
        }
    }
}
