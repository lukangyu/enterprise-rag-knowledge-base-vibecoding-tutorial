import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from uuid import uuid4
from datetime import datetime
from faker import Faker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

fake = Faker('zh_CN')


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_pdf_content():
    return b"%PDF-1.4\n%fake pdf content"


@pytest.fixture
def sample_text():
    return """
# 标题一

这是第一段内容，包含一些测试文本。

## 标题二

这是第二段内容，用于测试分块功能。
包含多行文本，用于验证分块算法的正确性。

### 标题三

最后一段内容。
"""


@pytest.fixture
def sample_chunks():
    return [
        {"content": "这是第一个分块", "position": 0},
        {"content": "这是第二个分块", "position": 1},
        {"content": "这是第三个分块", "position": 2}
    ]


@pytest.fixture
def neo4j_client():
    mock_client = MagicMock()
    mock_client._driver = MagicMock()
    mock_client.connect = AsyncMock(return_value=True)
    mock_client.close = AsyncMock(return_value=None)
    mock_client.health_check = AsyncMock(return_value=True)
    mock_client.execute_query = AsyncMock(return_value=[])
    mock_client.execute_write = AsyncMock(return_value=[])
    mock_client.execute_read = AsyncMock(return_value=[])
    return mock_client


@pytest.fixture
def entity_repository(neo4j_client):
    from services.kg.graph.entity_repository import EntityRepository
    repo = EntityRepository()
    repo.client = neo4j_client
    return repo


@pytest.fixture
def relation_repository(neo4j_client):
    from services.kg.graph.relation_repository import RelationRepository
    repo = RelationRepository()
    repo.client = neo4j_client
    return repo


@pytest.fixture
def entity_extractor():
    from services.kg.entity.llm_extractor import LLMEntityExtractor
    with patch('services.kg.entity.llm_extractor.kg_settings') as mock_settings:
        mock_settings.DASHSCOPE_API_URL = "http://test-api.com"
        mock_settings.DASHSCOPE_API_KEY = "test-key"
        mock_settings.QWEN_MODEL = "qwen-test"
        mock_settings.ENTITY_TYPES = {"Person": "人物", "Organization": "组织"}
        mock_settings.MAX_TOKENS = 1000
        mock_settings.REQUEST_TIMEOUT = 30
        mock_settings.MAX_RETRY_ATTEMPTS = 3
        mock_settings.RETRY_MIN_WAIT = 1
        mock_settings.RETRY_MAX_WAIT = 10
        mock_settings.BATCH_SIZE = 10
        extractor = LLMEntityExtractor()
    return extractor


@pytest.fixture
def relation_extractor():
    from services.kg.relation.llm_extractor import LLMRelationExtractor
    with patch('services.kg.relation.llm_extractor.kg_settings') as mock_settings:
        mock_settings.DASHSCOPE_API_URL = "http://test-api.com"
        mock_settings.DASHSCOPE_API_KEY = "test-key"
        mock_settings.QWEN_MODEL = "qwen-test"
        mock_settings.RELATION_TYPES = {"BELONGS_TO": "属于", "CREATED_BY": "创建"}
        mock_settings.MAX_TOKENS = 1000
        mock_settings.REQUEST_TIMEOUT = 30
        mock_settings.MAX_RETRY_ATTEMPTS = 3
        mock_settings.RETRY_MIN_WAIT = 1
        mock_settings.RETRY_MAX_WAIT = 10
        mock_settings.BATCH_SIZE = 10
        extractor = LLMRelationExtractor()
    return extractor


@pytest.fixture
def entity_processor():
    from services.kg.entity.entity_processor import EntityProcessor
    with patch('services.kg.entity.entity_processor.kg_settings') as mock_settings:
        mock_settings.SIMILARITY_THRESHOLD = 0.8
        mock_settings.ENTITY_CONFIDENCE_THRESHOLD = 0.5
        processor = EntityProcessor()
    return processor


@pytest.fixture
def relation_processor():
    from services.kg.relation.relation_processor import RelationProcessor
    with patch('services.kg.relation.relation_processor.kg_settings') as mock_settings:
        mock_settings.RELATION_CONFIDENCE_THRESHOLD = 0.5
        processor = RelationProcessor()
    return processor


@pytest.fixture
def sample_entities():
    from services.kg.entity.llm_extractor import Entity
    return [
        Entity(
            name=fake.name(),
            type="Person",
            description=fake.sentence(),
            confidence=0.9,
            properties={"age": fake.random_int(min=18, max=80)}
        ),
        Entity(
            name=fake.company(),
            type="Organization",
            description=fake.sentence(),
            confidence=0.85,
            properties={"industry": fake.word()}
        ),
        Entity(
            name=fake.city(),
            type="Location",
            description=fake.sentence(),
            confidence=0.8,
            properties={"country": "中国"}
        ),
    ]


@pytest.fixture
def sample_relations():
    from services.kg.relation.llm_extractor import Relation
    return [
        Relation(
            head="张三",
            relation="BELONGS_TO",
            tail="阿里巴巴",
            evidence="张三在阿里巴巴工作",
            confidence=0.9
        ),
        Relation(
            head="阿里巴巴",
            relation="LOCATED_AT",
            tail="杭州",
            evidence="阿里巴巴总部位于杭州",
            confidence=0.85
        ),
        Relation(
            head="张三",
            relation="CREATED_BY",
            tail="项目A",
            evidence="张三创建了项目A",
            confidence=0.8
        ),
    ]


@pytest.fixture
def sample_entity_data():
    return {
        "id": str(uuid4()),
        "name": fake.name(),
        "type": "Person",
        "description": fake.sentence(),
        "confidence": 0.9,
        "properties": {"age": fake.random_int(min=18, max=80)},
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_relation_data():
    return {
        "id": str(uuid4()),
        "source_id": str(uuid4()),
        "target_id": str(uuid4()),
        "type": "BELONGS_TO",
        "confidence": 0.9,
        "evidence": "测试证据",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_text_for_extraction():
    return """
    张三是阿里巴巴的高级工程师，他负责开发公司的核心产品。
    阿里巴巴总部位于杭州，是一家全球知名的科技公司。
    李四也是阿里巴巴的员工，他和张三一起工作。
    """


@pytest.fixture
def mock_llm_response_entities():
    return {
        "entities": [
            {"name": "张三", "type": "Person", "description": "阿里巴巴高级工程师"},
            {"name": "阿里巴巴", "type": "Organization", "description": "全球知名的科技公司"},
            {"name": "杭州", "type": "Location", "description": "城市"},
            {"name": "李四", "type": "Person", "description": "阿里巴巴员工"}
        ]
    }


@pytest.fixture
def mock_llm_response_relations():
    return {
        "relations": [
            {"head": "张三", "relation": "BELONGS_TO", "tail": "阿里巴巴", "evidence": "张三是阿里巴巴的高级工程师"},
            {"head": "阿里巴巴", "relation": "LOCATED_AT", "tail": "杭州", "evidence": "阿里巴巴总部位于杭州"},
            {"head": "李四", "relation": "BELONGS_TO", "tail": "阿里巴巴", "evidence": "李四也是阿里巴巴的员工"}
        ]
    }
