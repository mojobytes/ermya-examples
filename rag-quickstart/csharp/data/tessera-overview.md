# Tessera Overview

Tessera is a vector database for similarity search. It stores high-dimensional
embedding vectors and retrieves the nearest neighbours of a query vector using
an HNSW index. Each tenant is an isolated namespace with its own vector
dimension, so different applications can share one Tessera instance without
their data mixing.

Vectors are inserted with optional metadata, which can be returned alongside
search results and used for filtering. A typical retrieval-augmented generation
(RAG) workflow chunks source documents, embeds each chunk, inserts the vectors
into a tenant, and later searches that tenant with the embedding of a user
question to find the most relevant chunks.
