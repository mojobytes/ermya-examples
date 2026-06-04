"""Tests for chunker: deterministic text chunking and markdown parsing."""

from chunker import chunk_text, parse_markdown_files


def test_chunk_no_overlap():
    chunks = chunk_text("a" * 100, chunk_size=50, chunk_overlap=0)
    assert chunks == ["a" * 50, "a" * 50]


def test_chunk_with_overlap_exact_boundaries():
    # "abcdefghij" (10 chars), size=6, overlap=2 -> step=4
    # window 0: [0:6]="abcdef", window 1: [4:10]="efghij"
    chunks = chunk_text("abcdefghij", chunk_size=6, chunk_overlap=2)
    assert chunks == ["abcdef", "efghij"]


def test_chunk_text_shorter_than_chunk_size():
    assert chunk_text("hello", chunk_size=100, chunk_overlap=10) == ["hello"]


def test_chunk_text_equal_to_chunk_size():
    assert chunk_text("abcde", chunk_size=5, chunk_overlap=2) == ["abcde"]


def test_chunk_empty_text():
    assert chunk_text("", chunk_size=100, chunk_overlap=10) == []


def test_chunk_overlap_does_not_loop_forever():
    # A pathological overlap >= size would mean step <= 0; must still terminate.
    chunks = chunk_text("abcdefgh", chunk_size=4, chunk_overlap=4)
    assert chunks  # non-empty, finite
    assert all(len(c) <= 4 for c in chunks)


def test_parse_markdown_files_reads_only_md(tmp_path):
    (tmp_path / "doc1.md").write_text("# Title\nSome content here.")
    (tmp_path / "other.txt").write_text("ignored")
    docs = parse_markdown_files(tmp_path)
    assert len(docs) == 1
    assert "Some content here." in docs[0]


def test_parse_markdown_files_sorted_deterministic(tmp_path):
    (tmp_path / "b.md").write_text("beta")
    (tmp_path / "a.md").write_text("alpha")
    docs = parse_markdown_files(tmp_path)
    assert docs == ["alpha", "beta"]


def test_parse_markdown_empty_dir(tmp_path):
    assert parse_markdown_files(tmp_path) == []
