namespace RagQuickstart;

/// <summary>
/// Deterministic character-based text chunking and Markdown document parsing.
/// </summary>
public static class Chunker
{
    public static IReadOnlyList<string> ChunkText(string text, int chunkSize, int chunkOverlap)
    {
        if (text.Length == 0)
        {
            return Array.Empty<string>();
        }

        if (text.Length <= chunkSize)
        {
            return new[] { text };
        }

        var step = Math.Max(1, chunkSize - chunkOverlap);
        var chunks = new List<string>();
        var start = 0;
        while (true)
        {
            var end = Math.Min(start + chunkSize, text.Length);
            chunks.Add(text[start..end]);
            if (start + chunkSize >= text.Length)
            {
                break;
            }

            start += step;
        }

        return chunks;
    }

    public static async Task<IReadOnlyList<string>> ParseMarkdownFilesAsync(string dataDir)
    {
        if (!Directory.Exists(dataDir))
        {
            return Array.Empty<string>();
        }

        var files = Directory.GetFiles(dataDir, "*.md").OrderBy(p => p, StringComparer.Ordinal);
        var docs = new List<string>();
        foreach (var file in files)
        {
            docs.Add(await File.ReadAllTextAsync(file));
        }

        return docs;
    }
}
