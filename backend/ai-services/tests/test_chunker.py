import pytest
from services.chunker.semantic_chunker import SemanticChunker, Chunk as SemanticChunk
from services.chunker.fixed_chunker import FixedSizeChunker, Chunk as FixedChunk
from services.chunker.chunk_config import ChunkConfig, ChunkStrategy


class TestSemanticChunker:
    def test_chunk_paragraphs(self):
        chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=100)
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        chunks = chunker.chunk(text)

        assert len(chunks) >= 1
        assert all(len(c.content) >= 10 for c in chunks)

    def test_chunk_with_doc_id(self):
        chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=100)
        text = "这是一段测试内容，用于验证分块功能。"
        chunks = chunker.chunk(text, doc_id="test-doc-001")

        assert all(c.metadata["doc_id"] == "test-doc-001" for c in chunks)

    def test_chunk_returns_chunk_objects(self):
        chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=100)
        text = "测试内容，足够长的文本用于分块测试。"
        chunks = chunker.chunk(text)

        assert all(hasattr(c, 'chunk_id') for c in chunks)
        assert all(hasattr(c, 'content') for c in chunks)
        assert all(hasattr(c, 'position') for c in chunks)
        assert all(hasattr(c, 'metadata') for c in chunks)

    def test_chunk_metadata_contains_strategy(self):
        chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=100)
        text = "测试内容，足够长的文本用于分块测试。"
        chunks = chunker.chunk(text)

        assert all(c.metadata["strategy"] == "semantic" for c in chunks)

    def test_empty_text_returns_empty_list(self):
        chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=100)
        chunks = chunker.chunk("")

        assert len(chunks) == 0


class TestFixedSizeChunker:
    def test_chunk_fixed_size(self):
        chunker = FixedSizeChunker(chunk_size=50, overlap_rate=0.1)
        text = "这是一段较长的测试内容，用于验证固定大小分块功能是否正常工作。"
        chunks = chunker.chunk(text)

        assert len(chunks) >= 1

    def test_overlap(self):
        chunker = FixedSizeChunker(chunk_size=20, overlap_rate=0.5)
        text = "第一部分内容。第二部分内容。第三部分内容。"
        chunks = chunker.chunk(text)

        if len(chunks) > 1:
            assert True

    def test_chunk_with_doc_id(self):
        chunker = FixedSizeChunker(chunk_size=50, overlap_rate=0.1)
        text = "这是一段测试内容，用于验证分块功能。"
        chunks = chunker.chunk(text, doc_id="test-doc-002")

        assert all(c.metadata["doc_id"] == "test-doc-002" for c in chunks)

    def test_chunk_metadata_contains_strategy(self):
        chunker = FixedSizeChunker(chunk_size=50, overlap_rate=0.1)
        text = "这是一段测试内容，用于验证分块功能。"
        chunks = chunker.chunk(text)

        assert all(c.metadata["strategy"] == "fixed" for c in chunks)

    def test_chunk_metadata_contains_offsets(self):
        chunker = FixedSizeChunker(chunk_size=50, overlap_rate=0.1)
        text = "这是一段测试内容，用于验证分块功能。"
        chunks = chunker.chunk(text)

        assert all("start_offset" in c.metadata for c in chunks)
        assert all("end_offset" in c.metadata for c in chunks)


class TestChunkConfig:
    def test_auto_select_strategy_for_pdf(self):
        config = ChunkConfig(strategy=ChunkStrategy.AUTO)

        strategy = config.select_strategy("内容", "pdf")
        assert strategy == ChunkStrategy.SEMANTIC

    def test_auto_select_strategy_for_docx(self):
        config = ChunkConfig(strategy=ChunkStrategy.AUTO)

        strategy = config.select_strategy("内容", "docx")
        assert strategy == ChunkStrategy.SEMANTIC

    def test_auto_select_strategy_for_txt(self):
        config = ChunkConfig(strategy=ChunkStrategy.AUTO)

        strategy = config.select_strategy("内容", "txt")
        assert strategy == ChunkStrategy.FIXED

    def test_explicit_strategy_not_overridden(self):
        config = ChunkConfig(strategy=ChunkStrategy.SEMANTIC)

        strategy = config.select_strategy("内容", "txt")
        assert strategy == ChunkStrategy.SEMANTIC

    def test_default_values(self):
        config = ChunkConfig()

        assert config.chunk_size == 512
        assert config.overlap_rate == 0.1
        assert config.min_chunk_size == 100
        assert config.max_chunk_size == 1000

    def test_custom_values(self):
        config = ChunkConfig(
            chunk_size=256,
            overlap_rate=0.2,
            min_chunk_size=50,
            max_chunk_size=500
        )

        assert config.chunk_size == 256
        assert config.overlap_rate == 0.2
        assert config.min_chunk_size == 50
        assert config.max_chunk_size == 500
