import pytest
from services.parser.markdown_parser import MarkdownParser
from services.parser.text_cleaner import TextCleaner
from services.chunker.semantic_chunker import SemanticChunker
from services.chunker.fixed_chunker import FixedSizeChunker
from services.chunker.chunk_config import ChunkConfig, ChunkStrategy


class TestDocumentProcessingPipeline:
    def test_parse_and_chunk_pipeline(self, client, sample_text):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": sample_text,
                "doc_id": "integration-test",
                "strategy": "semantic"
            }
        )

        assert response.status_code == 200
        data = response.json()
        chunks = data["chunks"]

        assert len(chunks) >= 1
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "content" in chunk
            assert len(chunk["content"]) > 0

    def test_full_pipeline_with_markdown(self):
        parser = MarkdownParser()
        chunker = SemanticChunker(min_chunk_size=50, max_chunk_size=500)

        markdown_content = """
# 文档标题

这是文档的简介部分。

## 第一章

第一章的内容，包含多个段落。
每个段落都应该被正确处理。

## 第二章

第二章的内容。
"""

        parsed = parser.parse(markdown_content)
        assert parsed.content is not None
        assert len(parsed.structure) >= 1

        cleaned_content = TextCleaner.normalize(parsed.content)
        chunks = chunker.chunk(cleaned_content, doc_id="test-doc")

        assert len(chunks) >= 1
        assert all(hasattr(c, 'chunk_id') for c in chunks)

    def test_chunk_config_integration(self):
        config = ChunkConfig(
            strategy=ChunkStrategy.AUTO,
            chunk_size=256,
            min_chunk_size=50,
            max_chunk_size=500
        )

        content = "这是一段测试内容。" * 50

        strategy = config.select_strategy(content, "pdf")
        assert strategy == ChunkStrategy.SEMANTIC

        chunker = SemanticChunker(
            min_chunk_size=config.min_chunk_size,
            max_chunk_size=config.max_chunk_size
        )
        chunks = chunker.chunk(content, doc_id="integration-test")

        assert len(chunks) >= 1

    def test_text_cleaner_and_chunker_integration(self):
        raw_text = "第一段内容。\r\n\r\n\r\n第二段内容。  \n\n第三段内容。"

        normalized = TextCleaner.normalize(raw_text)
        assert "\r\n" not in normalized

        cleaned = TextCleaner.clean(normalized)

        chunker = FixedSizeChunker(chunk_size=50, overlap_rate=0.1)
        chunks = chunker.chunk(cleaned, doc_id="cleaner-test")

        assert len(chunks) >= 1


class TestErrorHandling:
    def test_invalid_json(self, client):
        response = client.post(
            "/api/v1/chunk",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_field(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={}
        )

        assert response.status_code == 422

    def test_empty_content_handling(self, client):
        response = client.post(
            "/api/v1/chunk",
            json={
                "content": "",
                "doc_id": "empty-test"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_chunks"] == 0


class TestChunkerStrategies:
    def test_semantic_vs_fixed_comparison(self):
        text = "第一段内容，包含足够的文字用于测试。\n\n第二段内容，同样需要足够的长度。\n\n第三段内容，确保分块正确。"

        semantic_chunker = SemanticChunker(min_chunk_size=20, max_chunk_size=100)
        fixed_chunker = FixedSizeChunker(chunk_size=50, overlap_rate=0.1)

        semantic_chunks = semantic_chunker.chunk(text, doc_id="semantic-test")
        fixed_chunks = fixed_chunker.chunk(text, doc_id="fixed-test")

        assert len(semantic_chunks) >= 1
        assert len(fixed_chunks) >= 1

        for chunk in semantic_chunks:
            assert chunk.metadata["strategy"] == "semantic"

        for chunk in fixed_chunks:
            assert chunk.metadata["strategy"] == "fixed"

    def test_large_document_chunking(self):
        large_text = "这是测试内容。" * 1000

        chunker = SemanticChunker(min_chunk_size=100, max_chunk_size=500)
        chunks = chunker.chunk(large_text, doc_id="large-doc")

        assert len(chunks) >= 1

        for i, chunk in enumerate(chunks):
            assert chunk.position == i


class TestParserFeatures:
    def test_markdown_heading_levels(self):
        parser = MarkdownParser()
        content = "# 一级标题\n## 二级标题\n### 三级标题\n#### 四级标题"
        result = parser.parse(content)

        assert len(result.structure) == 4
        levels = [s["level"] for s in result.structure]
        assert levels == [1, 2, 3, 4]

    def test_markdown_metadata_extraction(self):
        parser = MarkdownParser()
        content = """---
title: 测试文档
author: 测试作者
date: 2024-01-01
---

# 文档内容

这是正文内容。
"""
        result = parser.parse(content)

        assert result.metadata.get("title") == "测试文档"
        assert result.metadata.get("author") == "测试作者"
        assert result.metadata.get("date") == "2024-01-01"
