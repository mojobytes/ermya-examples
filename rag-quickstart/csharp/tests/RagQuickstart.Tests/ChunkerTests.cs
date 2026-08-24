using FluentAssertions;
using RagQuickstart;

namespace RagQuickstart.Tests;

public class ChunkerTests
{
    [Fact]
    public void ChunkText_SplitsWithoutOverlap()
    {
        Chunker.ChunkText(new string('a', 100), 50, 0)
            .Should().Equal(new string('a', 50), new string('a', 50));
    }

    [Fact]
    public void ChunkText_SplitsWithOverlapAtExactBoundaries()
    {
        // "abcdefghij" (10), size=6, overlap=2 -> step=4
        Chunker.ChunkText("abcdefghij", 6, 2).Should().Equal("abcdef", "efghij");
    }

    [Fact]
    public void ChunkText_ReturnsSingleChunk_WhenShorterThanChunkSize()
    {
        Chunker.ChunkText("hello", 100, 10).Should().Equal("hello");
    }

    [Fact]
    public void ChunkText_ReturnsSingleChunk_WhenEqualToChunkSize()
    {
        Chunker.ChunkText("abcde", 5, 2).Should().Equal("abcde");
    }

    [Fact]
    public void ChunkText_ReturnsEmpty_ForEmptyText()
    {
        Chunker.ChunkText("", 100, 10).Should().BeEmpty();
    }

    [Fact]
    public void ChunkText_Terminates_WhenOverlapGreaterThanOrEqualToChunkSize()
    {
        var chunks = Chunker.ChunkText("abcdefgh", 4, 4);
        chunks.Should().NotBeEmpty();
        chunks.Should().OnlyContain(c => c.Length <= 4);
    }

    [Fact]
    public async Task ParseMarkdownFiles_ReadsOnlyMd()
    {
        var dir = Path.Combine(Path.GetTempPath(), "ermya-chunk-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        await File.WriteAllTextAsync(Path.Combine(dir, "doc1.md"), "# Title\nSome content here.");
        await File.WriteAllTextAsync(Path.Combine(dir, "other.txt"), "ignored");
        var docs = await Chunker.ParseMarkdownFilesAsync(dir);
        docs.Should().HaveCount(1);
        docs[0].Should().Contain("Some content here.");
    }

    [Fact]
    public async Task ParseMarkdownFiles_ReturnsSortedDeterministic()
    {
        var dir = Path.Combine(Path.GetTempPath(), "ermya-chunk-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        await File.WriteAllTextAsync(Path.Combine(dir, "b.md"), "beta");
        await File.WriteAllTextAsync(Path.Combine(dir, "a.md"), "alpha");
        var docs = await Chunker.ParseMarkdownFilesAsync(dir);
        docs.Should().Equal("alpha", "beta");
    }

    [Fact]
    public async Task ParseMarkdownFiles_ReturnsEmpty_ForEmptyDirectory()
    {
        var dir = Path.Combine(Path.GetTempPath(), "ermya-empty-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(dir);
        (await Chunker.ParseMarkdownFilesAsync(dir)).Should().BeEmpty();
    }
}
