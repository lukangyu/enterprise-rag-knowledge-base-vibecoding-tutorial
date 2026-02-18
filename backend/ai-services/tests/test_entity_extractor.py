import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from services.kg.entity.llm_extractor import LLMEntityExtractor, Entity
from services.kg.entity.entity_processor import EntityProcessor, ProcessedEntity


class TestLLMEntityExtractor:
    @pytest.mark.asyncio
    async def test_extract_single_entity(self, entity_extractor):
        mock_response = json.dumps({
            "entities": [
                {"name": "张三", "type": "Person", "description": "测试人员"}
            ]
        })
        
        with patch.object(entity_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            entities = await entity_extractor.extract("张三是测试人员")
            
            assert len(entities) == 1
            assert entities[0].name == "张三"
            assert entities[0].type == "Person"
            assert entities[0].description == "测试人员"

    @pytest.mark.asyncio
    async def test_extract_multiple_entities(self, entity_extractor):
        mock_response = json.dumps({
            "entities": [
                {"name": "张三", "type": "Person", "description": "工程师"},
                {"name": "阿里巴巴", "type": "Organization", "description": "科技公司"},
                {"name": "杭州", "type": "Location", "description": "城市"}
            ]
        })
        
        with patch.object(entity_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            entities = await entity_extractor.extract("张三在阿里巴巴工作，公司位于杭州")
            
            assert len(entities) == 3
            entity_names = [e.name for e in entities]
            assert "张三" in entity_names
            assert "阿里巴巴" in entity_names
            assert "杭州" in entity_names

    @pytest.mark.asyncio
    async def test_extract_by_type(self, entity_extractor):
        mock_response = json.dumps({
            "entities": [
                {"name": "张三", "type": "Person", "description": "工程师"},
                {"name": "李四", "type": "Person", "description": "设计师"},
                {"name": "阿里巴巴", "type": "Organization", "description": "科技公司"}
            ]
        })
        
        with patch.object(entity_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            entities = await entity_extractor.extract("张三和李四在阿里巴巴工作")
            
            person_entities = [e for e in entities if e.type == "Person"]
            assert len(person_entities) == 2

    @pytest.mark.asyncio
    async def test_batch_extract(self, entity_extractor):
        texts = [
            "张三是工程师",
            "阿里巴巴是科技公司",
            "杭州是城市"
        ]
        
        mock_responses = [
            json.dumps({"entities": [{"name": "张三", "type": "Person", "description": "工程师"}]}),
            json.dumps({"entities": [{"name": "阿里巴巴", "type": "Organization", "description": "科技公司"}]}),
            json.dumps({"entities": [{"name": "杭州", "type": "Location", "description": "城市"}]})
        ]
        
        with patch.object(entity_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = mock_responses
            results = await entity_extractor.batch_extract(texts)
            
            assert len(results) == 3
            assert len(results[0]) == 1
            assert results[0][0].name == "张三"

    @pytest.mark.asyncio
    async def test_extract_empty_text(self, entity_extractor):
        entities = await entity_extractor.extract("")
        assert entities == []
        
        entities = await entity_extractor.extract("   ")
        assert entities == []

    @pytest.mark.asyncio
    async def test_extract_with_custom_types(self, entity_extractor):
        custom_types = {"CustomType": "自定义类型"}
        mock_response = json.dumps({
            "entities": [
                {"name": "测试实体", "type": "CustomType", "description": "描述"}
            ]
        })
        
        with patch.object(entity_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            entities = await entity_extractor.extract_with_custom_types("测试文本", custom_types)
            
            assert len(entities) == 1
            assert entities[0].type == "CustomType"

    @pytest.mark.asyncio
    async def test_extract_llm_error(self, entity_extractor):
        with patch.object(entity_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM API Error")
            entities = await entity_extractor.extract("测试文本")
            
            assert entities == []

    def test_parse_response_valid_json(self, entity_extractor):
        response_text = json.dumps({
            "entities": [
                {"name": "张三", "type": "Person", "description": "工程师"}
            ]
        })
        
        entities = entity_extractor._parse_response(response_text)
        assert len(entities) == 1
        assert entities[0].name == "张三"

    def test_parse_response_invalid_json(self, entity_extractor):
        response_text = "invalid json"
        entities = entity_extractor._parse_response(response_text)
        assert entities == []

    def test_parse_response_missing_fields(self, entity_extractor):
        response_text = json.dumps({
            "entities": [
                {"name": "张三"},
                {"type": "Person"},
                {}
            ]
        })
        
        entities = entity_extractor._parse_response(response_text)
        assert len(entities) == 0


class TestEntityProcessor:
    def test_deduplicate_same_entities(self, entity_processor):
        entities = [
            Entity(name="张三", type="Person", description="工程师", confidence=0.9),
            Entity(name="张三", type="Person", description="开发人员", confidence=0.85),
            Entity(name="张三", type="Person", description="程序员", confidence=0.8)
        ]
        
        result = entity_processor.deduplicate(entities)
        assert len(result) == 1
        assert result[0].name == "张三"
        assert len(result[0].aliases) == 2

    def test_deduplicate_different_entities(self, entity_processor):
        entities = [
            Entity(name="张三", type="Person", description="工程师", confidence=0.9),
            Entity(name="李四", type="Person", description="设计师", confidence=0.85),
            Entity(name="王五", type="Person", description="产品经理", confidence=0.8)
        ]
        
        result = entity_processor.deduplicate(entities)
        assert len(result) == 3

    def test_deduplicate_similar_names(self, entity_processor):
        entities = [
            Entity(name="阿里巴巴", type="Organization", description="科技公司", confidence=0.9),
            Entity(name="阿里巴巴集团", type="Organization", description="互联网公司", confidence=0.85)
        ]
        
        result = entity_processor.deduplicate(entities)
        assert len(result) == 1

    def test_deduplicate_empty_list(self, entity_processor):
        result = entity_processor.deduplicate([])
        assert result == []

    def test_confidence_calculation_basic(self, entity_processor):
        entity = Entity(
            name="张三",
            type="Person",
            description="工程师",
            confidence=0.8
        )
        
        confidence = entity_processor.calculate_confidence(entity)
        assert 0.0 <= confidence <= 1.0

    def test_confidence_calculation_with_context(self, entity_processor):
        entity = Entity(
            name="张三",
            type="Person",
            description="工程师",
            confidence=0.8
        )
        
        confidence = entity_processor.calculate_confidence(
            entity,
            context_length=500,
            mention_count=3
        )
        assert confidence >= entity.confidence

    def test_confidence_calculation_short_name(self, entity_processor):
        entity = Entity(
            name="A",
            type="Person",
            description="测试",
            confidence=0.9
        )
        
        confidence = entity_processor.calculate_confidence(entity)
        assert confidence < entity.confidence

    def test_confidence_calculation_long_name(self, entity_processor):
        entity = Entity(
            name="A" * 60,
            type="Organization",
            description="测试",
            confidence=0.9
        )
        
        confidence = entity_processor.calculate_confidence(entity)
        assert confidence < entity.confidence

    def test_confidence_calculation_no_description(self, entity_processor):
        entity = Entity(
            name="张三",
            type="Person",
            description=None,
            confidence=0.9
        )
        
        confidence = entity_processor.calculate_confidence(entity)
        assert confidence < entity.confidence

    def test_filter_by_confidence(self, entity_processor):
        processed_entities = [
            ProcessedEntity(
                name="张三",
                normalized_name="张三",
                type="Person",
                description="工程师",
                confidence=0.9,
                properties={},
                aliases=[],
                source_count=1
            ),
            ProcessedEntity(
                name="李四",
                normalized_name="李四",
                type="Person",
                description="设计师",
                confidence=0.3,
                properties={},
                aliases=[],
                source_count=1
            )
        ]
        
        filtered = entity_processor.filter_by_confidence(processed_entities, threshold=0.5)
        assert len(filtered) == 1
        assert filtered[0].name == "张三"

    def test_group_by_type(self, entity_processor):
        processed_entities = [
            ProcessedEntity(
                name="张三",
                normalized_name="张三",
                type="Person",
                description="工程师",
                confidence=0.9,
                properties={},
                aliases=[],
                source_count=1
            ),
            ProcessedEntity(
                name="阿里巴巴",
                normalized_name="阿里巴巴",
                type="Organization",
                description="科技公司",
                confidence=0.85,
                properties={},
                aliases=[],
                source_count=1
            ),
            ProcessedEntity(
                name="李四",
                normalized_name="李四",
                type="Person",
                description="设计师",
                confidence=0.8,
                properties={},
                aliases=[],
                source_count=1
            )
        ]
        
        grouped = entity_processor.group_by_type(processed_entities)
        assert "Person" in grouped
        assert "Organization" in grouped
        assert len(grouped["Person"]) == 2
        assert len(grouped["Organization"]) == 1

    def test_normalize_entity(self, entity_processor):
        entity = Entity(
            name="张三",
            type="Person",
            description="工程师",
            confidence=0.9,
            properties={"age": 30}
        )
        
        processed = entity_processor.normalize_entity(entity)
        assert processed.name == "张三"
        assert processed.normalized_name == "张三"
        assert processed.type == "Person"
        assert processed.confidence == 0.9

    def test_merge_entities(self, entity_processor):
        entities = [
            Entity(name="张三", type="Person", description="工程师", confidence=0.9, properties={"age": 30}),
            Entity(name="张三", type="Person", description="开发人员", confidence=0.85, properties={"city": "杭州"}),
            Entity(name="张三", type="Person", description="程序员", confidence=0.8, properties={"level": "senior"})
        ]
        
        merged = entity_processor.merge(entities)
        assert merged.name == "张三"
        assert "工程师" in merged.description
        assert "开发人员" in merged.description
        assert "程序员" in merged.description
        assert "age" in merged.properties
        assert "city" in merged.properties
        assert "level" in merged.properties

    def test_merge_empty_list(self, entity_processor):
        with pytest.raises(ValueError):
            entity_processor.merge([])

    def test_process_batch(self, entity_processor):
        entities_list = [
            [Entity(name="张三", type="Person", description="工程师", confidence=0.9)],
            [Entity(name="李四", type="Person", description="设计师", confidence=0.85)],
            [Entity(name="张三", type="Person", description="开发人员", confidence=0.8)]
        ]
        
        result = entity_processor.process_batch(entities_list)
        assert len(result) == 2

    def test_normalize_name(self, entity_processor):
        assert entity_processor._normalize_name("张三") == "张三"
        assert entity_processor._normalize_name("  张三  ") == "张三"
        assert entity_processor._normalize_name("张-三") == "张三"
        assert entity_processor._normalize_name("Zhang San") == "zhangsan"

    def test_calculate_similarity(self, entity_processor):
        similarity = entity_processor._calculate_similarity("张三", "张三")
        assert similarity == 1.0
        
        similarity = entity_processor._calculate_similarity("张三", "李四")
        assert 0.0 <= similarity < 1.0
        
        similarity = entity_processor._calculate_similarity("", "张三")
        assert similarity == 0.0
