/**
 * Fail-fast verification that the provider returns vectors of the configured
 * dimension. The config is the source of truth; the example verifies reality
 * matches it (important for Ollama and custom models the launchpad cannot map).
 */

export function verifyDimension(vector: number[], expected: number): void {
  const actual = vector.length;
  if (actual !== expected) {
    throw new Error(
      `Dimension mismatch: the embedding provider returned a vector of length ` +
        `${actual}, but tessera_config.json declares embedding.dimension = ` +
        `${expected}. Update embedding.dimension to match the model's output ` +
        `size, or pick a matching model.`,
    );
  }
}
