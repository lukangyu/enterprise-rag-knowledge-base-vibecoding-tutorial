import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.qa.context_builder import ContextBuilder
from services.qa.stream_handler import SSEStreamHandler
from services.qa.reference_annotator import ReferenceAnnotator
from services.qa.prompt_template import QAPromptTemplate
from services.search.reranker import RerankerService
from models.qa_models import SourceReference, GraphContext


class TestContextBuilder:
    @pytest.fixture
    def context_builder(self):
        return ContextBuilder(max_context_tokens=1000)
    
    def test_build_context_with_search_results(self, context_builder):
        search_results = [
            {"doc_id": "doc1", "chunk_id": "chunk1", "content": "这是测试内容1", "score": 0.9},
            {"doc_id": "doc2", "chunk_id": "chunk2", "content": "这是测试内容2", "score": 0.8},
        ]
        
        result = context_builder.build_context(
            query="测试问题",
            search_results=search_results
        )
        
        assert result.context_text
        assert len(result.sources) == 2
        assert result.sources[0].doc_id == "doc1"
    
    def test_build_context_with_graph_context(self, context_builder):
        search_results = [
            {"doc_id": "doc1", "content": "测试内容", "score": 0.9}
        ]
        
        graph_context = GraphContext(
            entities=[{"name": "实体1", "type": "Person"}],
            relations=[{"head": "实体1", "type": "RELATES", "tail": "实体2"}],
            paths=[]
        )
        
        result = context_builder.build_context(
            query="测试问题",
            search_results=search_results,
            graph_context=graph_context
        )
        
        assert "相关实体" in result.context_text
    
    def test_estimate_tokens(self, context_builder):
        text = "这是一段测试文本"
        tokens = context_builder._estimate_tokens(text)
        assert tokens == len(text) // 2
    
    def test_truncate_text(self, context_builder):
        text = "这是一段很长的测试文本内容"
        truncated = context_builder._truncate_text(text, 5)
        assert len(truncated) <= 12
        assert truncated.endswith("...")


class TestReferenceAnnotator:
    @pytest.fixture
    def annotator(self):
        return ReferenceAnnotator()
    
    def test_annotate_response_with_existing_refs(self, annotator):
        response = "这是回答内容[1]，还有更多内容[2]。"
        sources = [
            SourceReference(source_id="[1]", doc_id="doc1", content="内容1", score=0.9),
            SourceReference(source_id="[2]", doc_id="doc2", content="内容2", score=0.8),
        ]
        
        result = annotator.annotate_response(response, sources)
        
        assert "[1]" in result.text
        assert "[2]" in result.text
        assert "[1]" in result.source_ids
        assert "[2]" in result.source_ids
    
    def test_extract_references(self, annotator):
        text = "内容[1]和[2]，还有[3]"
        refs = annotator.extract_references(text)
        
        assert len(refs) == 3
        assert refs[0][0] == "1"
    
    def test_format_source_list(self, annotator):
        sources = [
            SourceReference(source_id="[1]", doc_id="doc1", content="这是内容1", score=0.9),
            SourceReference(source_id="[2]", doc_id="doc2", content="这是内容2", score=0.8),
        ]
        
        formatted = annotator.format_source_list(sources)
        
        assert "参考来源" in formatted
        assert "doc1" in formatted


class TestQAPromptTemplate:
    @pytest.fixture
    def template(self):
        return QAPromptTemplate()
    
    def test_format_default_template(self, template):
        system_prompt, user_content = template.format(
            query="测试问题",
            context="测试上下文"
        )
        
        assert "测试问题" in user_content
        assert "测试上下文" in user_content
        assert system_prompt
    
    def test_set_template(self, template):
        template.set_template("simple")
        
        assert template.template == QAPromptTemplate.SIMPLE
    
    def test_custom_template(self, template):
        template.custom_template(
            system_prompt="自定义系统提示",
            user_template="自定义用户模板: {query}"
        )
        
        system_prompt, user_content = template.format(
            query="测试问题",
            context="测试上下文"
        )
        
        assert system_prompt == "自定义系统提示"
        assert "测试问题" in user_content


class TestRerankerService:
    @pytest.fixture
    def reranker(self):
        return RerankerService(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_rerank_without_api_key(self):
        reranker = RerankerService(api_key=None)
        documents = [
            {"content": "文档1", "score": 0.9},
            {"content": "文档2", "score": 0.8},
        ]
        
        result = await reranker.rerank("测试查询", documents, top_n=2)
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self, reranker):
        result = await reranker.rerank("测试查询", [])
        
        assert result == []


class TestStreamHandler:
    @pytest.fixture
    def handler(self):
        return SSEStreamHandler()
    
    def test_build_messages(self, handler):
        messages = handler._build_messages(
            query="测试问题",
            context="测试上下文",
            system_prompt="系统提示"
        )
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    def test_build_messages_with_history(self, handler):
        history = [
            {"role": "user", "content": "历史问题"},
            {"role": "assistant", "content": "历史回答"}
        ]
        
        messages = handler._build_messages(
            query="测试问题",
            context="测试上下文",
            history=history
        )
        
        assert len(messages) == 4
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "历史问题"
