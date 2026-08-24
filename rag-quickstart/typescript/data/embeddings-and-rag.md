# Embeddings and RAG

An embedding is a list of floating-point numbers that captures the meaning of a
piece of text. Texts with similar meaning produce vectors that are close
together in the embedding space, which is what makes semantic search possible.

This quickstart can generate embeddings with three providers. OpenAI and Azure
OpenAI are cloud services that require an API key. Ollama runs locally on your
machine and needs no key, which makes it the easiest way to try Ermya end to
end without signing up for anything.

The embedding model determines the vector dimension. The example reads the
expected dimension from the configuration and verifies that the provider really
returns vectors of that size, failing early with a clear message if they differ.
