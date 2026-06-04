using FluentAssertions;
using RagQuickstart;

namespace RagQuickstart.Tests;

public class DimensionCheckTests
{
    [Fact]
    public void Verify_Passes_WhenDimensionMatches()
    {
        var act = () => DimensionCheck.Verify(new float[1536], 1536);
        act.Should().NotThrow();
    }

    [Theory]
    [InlineData(384)]
    [InlineData(0)]
    public void Verify_Throws_NamingBothValues(int actualLength)
    {
        var act = () => DimensionCheck.Verify(new float[actualLength], 1536);
        act.Should().Throw<InvalidOperationException>()
            .Where(e => e.Message.Contains(actualLength.ToString()) && e.Message.Contains("1536"));
    }
}
