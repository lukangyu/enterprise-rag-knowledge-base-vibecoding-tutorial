import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from services.kg.relation.llm_extractor import LLMRelationExtractor, Relation
from services.kg.relation.relation_processor import RelationProcessor, ProcessedRelation
from services.kg.entity.llm_extractor import Entity


class TestLLMRelationExtractor:
    @pytest.mark.asyncio
    async def test_extract_single_relation(self, relation_extractor):
        mock_response = json.dumps({
            "relations": [
                {"head": "张三", "relation": "BELONGS_TO", "tail": "阿里巴巴", "evidence": "张三在阿里巴巴工作"}
            ]
        })
        
        entities = [Entity(name="张三", type="Person", description="工程师")]
        
        with patch.object(relation_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            relations = await relation_extractor.extract("张三在阿里巴巴工作", entities)
            
            assert len(relations) == 1
            assert relations[0].head == "张三"
            assert relations[0].relation == "BELONGS_TO"
            assert relations[0].tail == "阿里巴巴"

    @pytest.mark.asyncio
    async def test_extract_multiple_relations(self, relation_extractor):
        mock_response = json.dumps({
            "relations": [
                {"head": "张三", "relation": "BELONGS_TO", "tail": "阿里巴巴", "evidence": "张三在阿里巴巴工作"},
                {"head": "阿里巴巴", "relation": "LOCATED_AT", "tail": "杭州", "evidence": "阿里巴巴位于杭州"},
                {"head": "张三", "relation": "CREATED_BY", "tail": "项目A", "evidence": "张三创建了项目A"}
            ]
        })
        
        entities = [
            Entity(name="张三", type="Person", description="工程师"),
            Entity(name="阿里巴巴", type="Organization", description="公司"),
            Entity(name="杭州", type="Location", description="城市")
        ]
        
        with patch.object(relation_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            relations = await relation_extractor.extract("张三在阿里巴巴工作，公司位于杭州", entities)
            
            assert len(relations) == 3

    @pytest.mark.asyncio
    async def test_extract_by_type(self, relation_extractor):
        mock_response = json.dumps({
            "relations": [
                {"head": "张三", "relation": "BELONGS_TO", "tail": "阿里巴巴", "evidence": "张三在阿里巴巴工作"},
                {"head": "李四", "relation": "BELONGS_TO", "tail": "腾讯", "evidence": "李四在腾讯工作"}
            ]
        })
        
        entities = [
            Entity(name="张三", type="Person", description="工程师"),
            Entity(name="李四", type="Person", description="设计师")
        ]
        
        with patch.object(relation_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            relations = await relation_extractor.extract("张三和李四的工作情况", entities)
            
            belongs_to_relations = [r for r in relations if r.relation == "BELONGS_TO"]
            assert len(belongs_to_relations) == 2

    @pytest.mark.asyncio
    async def test_batch_extract(self, relation_extractor):
        texts = [
            "张三在阿里巴巴工作",
            "李四在腾讯工作",
            "王五在百度工作"
        ]
        
        entities_list = [
            [Entity(name="张三", type="Person", description="工程师")],
            [Entity(name="李四", type="Person", description="设计师")],
            [Entity(name="王五", type="Person", description="产品经理")]
        ]
        
        mock_responses = [
            json.dumps({"relations": [{"head": "张三", "relation": "BELONGS_TO", "tail": "阿里巴巴", "evidence": "张三在阿里巴巴工作"}]}),
            json.dumps({"relations": [{"head": "李四", "relation": "BELONGS_TO", "tail": "腾讯", "evidence": "李四在腾讯工作"}]}),
            json.dumps({"relations": [{"head": "王五", "relation": "BELONGS_TO", "tail": "百度", "evidence": "王五在百度工作"}]})
        ]
        
        with patch.object(relation_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = mock_responses
            results = await relation_extractor.batch_extract(texts, entities_list)
            
            assert len(results) == 3
            assert len(results[0]) == 1

    @pytest.mark.asyncio
    async def test_batch_extract_mismatched_lengths(self, relation_extractor):
        texts = ["文本1", "文本2"]
        entities_list = [[Entity(name="张三", type="Person", description="工程师")]]
        
        with pytest.raises(ValueError):
            await relation_extractor.batch_extract(texts, entities_list)

    @pytest.mark.asyncio
    async def test_extract_empty_text(self, relation_extractor):
        entities = [Entity(name="张三", type="Person", description="工程师")]
        
        relations = await relation_extractor.extract("", entities)
        assert relations == []
        
        relations = await relation_extractor.extract("   ", entities)
        assert relations == []

    @pytest.mark.asyncio
    async def test_extract_empty_entities(self, relation_extractor):
        relations = await relation_extractor.extract("测试文本", [])
        assert relations == []

    @pytest.mark.asyncio
    async def test_extract_with_custom_types(self, relation_extractor):
        custom_types = {"CUSTOM_RELATION": "自定义关系"}
        mock_response = json.dumps({
            "relations": [
                {"head": "张三", "relation": "CUSTOM_RELATION", "tail": "李四", "evidence": "张三与李四有关系"}
            ]
        })
        
        entities = [
            Entity(name="张三", type="Person", description="工程师"),
            Entity(name="李四", type="Person", description="设计师")
        ]
        
        with patch.object(relation_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            relations = await relation_extractor.extract_with_custom_types("测试文本", entities, custom_types)
            
            assert len(relations) == 1
            assert relations[0].relation == "CUSTOM_RELATION"

    @pytest.mark.asyncio
    async def test_extract_llm_error(self, relation_extractor):
        entities = [Entity(name="张三", type="Person", description="工程师")]
        
        with patch.object(relation_extractor, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM API Error")
            relations = await relation_extractor.extract("测试文本", entities)
            
            assert relations == []

    def test_parse_response_valid_json(self, relation_extractor):
        response_text = json.dumps({
            "relations": [
                {"head": "张三", "relation": "BELONGS_TO", "tail": "阿里巴巴", "evidence": "证据"}
            ]
        })
        
        relations = relation_extractor._parse_response(response_text)
        assert len(relations) == 1
        assert relations[0].head == "张三"

    def test_parse_response_invalid_json(self, relation_extractor):
        response_text = "invalid json"
        relations = relation_extractor._parse_response(response_text)
        assert relations == []

    def test_parse_response_missing_fields(self, relation_extractor):
        response_text = json.dumps({
            "relations": [
                {"head": "张三"},
                {"relation": "BELONGS_TO"},
                {}
            ]
        })
        
        relations = relation_extractor._parse_response(response_text)
        assert len(relations) == 0

    def test_build_entities_str_with_objects(self, relation_extractor):
        entities = [
            Entity(name="张三", type="Person", description="工程师"),
            Entity(name="阿里巴巴", type="Organization", description="公司")
        ]
        
        result = relation_extractor._build_entities_str(entities)
        assert "张三" in result
        assert "Person" in result
        assert "阿里巴巴" in result
        assert "Organization" in result

    def test_build_entities_str_with_dicts(self, relation_extractor):
        entities = [
            {"name": "张三", "type": "Person"},
            {"name": "阿里巴巴", "type": "Organization"}
        ]
        
        result = relation_extractor._build_entities_str(entities)
        assert "张三" in result
        assert "阿里巴巴" in result


class TestRelationProcessor:
    def test_validate_valid_relations(self, relation_processor):
        relations = [
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9),
            Relation(head="李四", relation="BELONGS_TO", tail="腾讯", evidence="证据", confidence=0.8)
        ]
        
        valid_entities = [
            MagicMock(name="张三", normalized_name="张三"),
            MagicMock(name="阿里巴巴", normalized_name="阿里巴巴"),
            MagicMock(name="李四", normalized_name="李四"),
            MagicMock(name="腾讯", normalized_name="腾讯")
        ]
        
        valid, invalid = relation_processor.validate(relations, valid_entities)
        assert len(valid) == 2
        assert len(invalid) == 0

    def test_validate_invalid_relations(self, relation_processor):
        relations = [
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9),
            Relation(head="不存在的实体", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.8)
        ]
        
        valid_entities = [
            MagicMock(name="张三", normalized_name="张三"),
            MagicMock(name="阿里巴巴", normalized_name="阿里巴巴")
        ]
        
        valid, invalid = relation_processor.validate(relations, valid_entities)
        assert len(valid) == 1
        assert len(invalid) == 1

    def test_validate_with_dict_entities(self, relation_processor):
        relations = [
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9)
        ]
        
        valid_entities = [
            {"name": "张三", "normalized_name": "张三"},
            {"name": "阿里巴巴", "normalized_name": "阿里巴巴"}
        ]
        
        valid, invalid = relation_processor.validate(relations, valid_entities)
        assert len(valid) == 1
        assert len(invalid) == 0

    def test_filter_low_confidence(self, relation_processor):
        relations = [
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9),
            Relation(head="李四", relation="BELONGS_TO", tail="腾讯", evidence="证据", confidence=0.3)
        ]
        
        filtered = relation_processor.filter_low_confidence(relations, threshold=0.5)
        assert len(filtered) == 1
        assert filtered[0].head == "张三"

    def test_deduplicate_same_relations(self, relation_processor):
        relations = [
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据1", confidence=0.9),
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据2", confidence=0.85),
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据3", confidence=0.8)
        ]
        
        result = relation_processor.deduplicate(relations)
        assert len(result) == 1
        assert result[0].source_count == 3

    def test_deduplicate_different_relations(self, relation_processor):
        relations = [
            Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9),
            Relation(head="李四", relation="BELONGS_TO", tail="腾讯", evidence="证据", confidence=0.85),
            Relation(head="王五", relation="BELONGS_TO", tail="百度", evidence="证据", confidence=0.8)
        ]
        
        result = relation_processor.deduplicate(relations)
        assert len(result) == 3

    def test_deduplicate_empty_list(self, relation_processor):
        result = relation_processor.deduplicate([])
        assert result == []

    def test_confidence_calculation_basic(self, relation_processor):
        relation = Relation(
            head="张三",
            relation="BELONGS_TO",
            tail="阿里巴巴",
            evidence="张三在阿里巴巴工作",
            confidence=0.8
        )
        
        confidence = relation_processor.calculate_confidence(relation)
        assert 0.0 <= confidence <= 1.0

    def test_confidence_calculation_with_evidence(self, relation_processor):
        relation_with_evidence = Relation(
            head="张三",
            relation="BELONGS_TO",
            tail="阿里巴巴",
            evidence="张三在阿里巴巴工作，是一名高级工程师",
            confidence=0.8
        )
        
        relation_without_evidence = Relation(
            head="张三",
            relation="BELONGS_TO",
            tail="阿里巴巴",
            evidence="",
            confidence=0.8
        )
        
        confidence_with = relation_processor.calculate_confidence(relation_with_evidence)
        confidence_without = relation_processor.calculate_confidence(relation_without_evidence)
        
        assert confidence_with > confidence_without

    def test_confidence_calculation_with_co_occurrence(self, relation_processor):
        relation = Relation(
            head="张三",
            relation="BELONGS_TO",
            tail="阿里巴巴",
            evidence="证据",
            confidence=0.8
        )
        
        confidence = relation_processor.calculate_confidence(relation, co_occurrence_count=5)
        assert confidence >= relation.confidence

    def test_confidence_calculation_short_entity_names(self, relation_processor):
        relation = Relation(
            head="A",
            relation="BELONGS_TO",
            tail="B",
            evidence="证据",
            confidence=0.9
        )
        
        confidence = relation_processor.calculate_confidence(relation)
        assert confidence < relation.confidence

    def test_group_by_type(self, relation_processor):
        processed_relations = [
            ProcessedRelation(
                head="张三",
                head_normalized="张三",
                relation="BELONGS_TO",
                tail="阿里巴巴",
                tail_normalized="阿里巴巴",
                evidence="证据",
                confidence=0.9,
                properties={},
                source_count=1
            ),
            ProcessedRelation(
                head="阿里巴巴",
                head_normalized="阿里巴巴",
                relation="LOCATED_AT",
                tail="杭州",
                tail_normalized="杭州",
                evidence="证据",
                confidence=0.85,
                properties={},
                source_count=1
            ),
            ProcessedRelation(
                head="李四",
                head_normalized="李四",
                relation="BELONGS_TO",
                tail="腾讯",
                tail_normalized="腾讯",
                evidence="证据",
                confidence=0.8,
                properties={},
                source_count=1
            )
        ]
        
        grouped = relation_processor.group_by_type(processed_relations)
        assert "BELONGS_TO" in grouped
        assert "LOCATED_AT" in grouped
        assert len(grouped["BELONGS_TO"]) == 2
        assert len(grouped["LOCATED_AT"]) == 1

    def test_build_adjacency_list(self, relation_processor):
        processed_relations = [
            ProcessedRelation(
                head="张三",
                head_normalized="张三",
                relation="BELONGS_TO",
                tail="阿里巴巴",
                tail_normalized="阿里巴巴",
                evidence="证据",
                confidence=0.9,
                properties={},
                source_count=1
            ),
            ProcessedRelation(
                head="张三",
                head_normalized="张三",
                relation="CREATED_BY",
                tail="项目A",
                tail_normalized="项目a",
                evidence="证据",
                confidence=0.85,
                properties={},
                source_count=1
            )
        ]
        
        adjacency = relation_processor.build_adjacency_list(processed_relations)
        assert "张三" in adjacency
        assert len(adjacency["张三"]) == 2

    def test_process_batch(self, relation_processor):
        relations_list = [
            [Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9)],
            [Relation(head="李四", relation="BELONGS_TO", tail="腾讯", evidence="证据", confidence=0.85)],
            [Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据2", confidence=0.8)]
        ]
        
        result = relation_processor.process_batch(relations_list)
        assert len(result) == 2

    def test_process_batch_with_validation(self, relation_processor):
        relations_list = [
            [Relation(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9)],
            [Relation(head="不存在的实体", relation="BELONGS_TO", tail="腾讯", evidence="证据", confidence=0.85)]
        ]
        
        valid_entities = [
            MagicMock(name="张三", normalized_name="张三"),
            MagicMock(name="阿里巴巴", normalized_name="阿里巴巴")
        ]
        
        result = relation_processor.process_batch(relations_list, valid_entities)
        assert len(result) == 1

    def test_normalize_entity_name(self, relation_processor):
        assert relation_processor._normalize_entity_name("张三") == "张三"
        assert relation_processor._normalize_entity_name("  张三  ") == "张三"
        assert relation_processor._normalize_entity_name("ZHANG SAN") == "zhang san"
