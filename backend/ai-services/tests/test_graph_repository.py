import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from services.kg.graph.entity_repository import EntityRepository
from services.kg.graph.relation_repository import RelationRepository
from services.kg.graph.neo4j_client import Neo4jClient
from services.kg.graph.index_manager import IndexManager


class TestNeo4jClient:
    @pytest.mark.asyncio
    async def test_connect_success(self, neo4j_client):
        neo4j_client.connect = AsyncMock(return_value=True)
        result = await neo4j_client.connect()
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        client = Neo4jClient()
        with patch('services.kg.graph.neo4j_client.AsyncGraphDatabase') as mock_driver:
            mock_driver.driver.side_effect = Exception("Connection failed")
            result = await client.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_close(self, neo4j_client):
        neo4j_client._driver = MagicMock()
        neo4j_client._driver.close = AsyncMock()
        await neo4j_client.close()
        neo4j_client._driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, neo4j_client):
        neo4j_client._driver = MagicMock()
        neo4j_client._driver.verify_connectivity = AsyncMock()
        result = await neo4j_client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_no_driver(self, neo4j_client):
        neo4j_client._driver = None
        result = await neo4j_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_query(self, neo4j_client):
        expected_result = [{"name": "张三", "type": "Person"}]
        neo4j_client.execute_query = AsyncMock(return_value=expected_result)
        
        result = await neo4j_client.execute_query("MATCH (e:Entity) RETURN e")
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_execute_write(self, neo4j_client):
        expected_result = [{"e": {"id": "test-id"}}]
        neo4j_client.execute_write = AsyncMock(return_value=expected_result)
        
        result = await neo4j_client.execute_write("CREATE (e:Entity) RETURN e")
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_execute_read(self, neo4j_client):
        expected_result = [{"e": {"id": "test-id"}}]
        neo4j_client.execute_read = AsyncMock(return_value=expected_result)
        
        result = await neo4j_client.execute_read("MATCH (e:Entity) RETURN e")
        assert result == expected_result

    def test_get_session_without_driver(self):
        client = Neo4jClient()
        client._driver = None
        with pytest.raises(RuntimeError):
            client.get_session()

    def test_driver_property_without_driver(self):
        client = Neo4jClient()
        client._driver = None
        with pytest.raises(RuntimeError):
            _ = client.driver


class TestEntityRepository:
    @pytest.mark.asyncio
    async def test_create_entity(self, entity_repository, sample_entity_data):
        entity_repository.client.execute_write = AsyncMock(
            return_value=[{"e": sample_entity_data}]
        )
        
        result = await entity_repository.create_entity(
            entity_id=sample_entity_data["id"],
            name=sample_entity_data["name"],
            entity_type=sample_entity_data["type"],
            properties=sample_entity_data.get("properties")
        )
        
        assert result == sample_entity_data
        entity_repository.client.execute_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_entity_with_properties(self, entity_repository):
        entity_id = str(uuid4())
        entity_repository.client.execute_write = AsyncMock(
            return_value=[{"e": {"id": entity_id, "name": "张三", "type": "Person", "age": 30}}]
        )
        
        result = await entity_repository.create_entity(
            entity_id=entity_id,
            name="张三",
            entity_type="Person",
            properties={"age": 30, "city": "杭州"}
        )
        
        assert result["id"] == entity_id
        assert result["name"] == "张三"

    @pytest.mark.asyncio
    async def test_get_entity_by_id(self, entity_repository, sample_entity_data):
        entity_repository.client.execute_read = AsyncMock(
            return_value=[{"e": sample_entity_data}]
        )
        
        result = await entity_repository.get_entity_by_id(sample_entity_data["id"])
        assert result == sample_entity_data

    @pytest.mark.asyncio
    async def test_get_entity_by_id_not_found(self, entity_repository):
        entity_repository.client.execute_read = AsyncMock(return_value=[])
        
        result = await entity_repository.get_entity_by_id("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_entity_by_name(self, entity_repository, sample_entity_data):
        entity_repository.client.execute_read = AsyncMock(
            return_value=[{"e": sample_entity_data}]
        )
        
        result = await entity_repository.get_entity_by_name(sample_entity_data["name"])
        assert result == sample_entity_data

    @pytest.mark.asyncio
    async def test_get_entities_by_type(self, entity_repository):
        entities = [
            {"id": str(uuid4()), "name": "张三", "type": "Person"},
            {"id": str(uuid4()), "name": "李四", "type": "Person"}
        ]
        entity_repository.client.execute_read = AsyncMock(
            return_value=[{"e": e} for e in entities]
        )
        
        result = await entity_repository.get_entities_by_type("Person")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_entity(self, entity_repository, sample_entity_data):
        updated_data = {**sample_entity_data, "description": "更新后的描述"}
        entity_repository.client.execute_write = AsyncMock(
            return_value=[{"e": updated_data}]
        )
        
        result = await entity_repository.update_entity(
            sample_entity_data["id"],
            {"description": "更新后的描述"}
        )
        
        assert result == updated_data

    @pytest.mark.asyncio
    async def test_update_entity_not_found(self, entity_repository):
        entity_repository.client.execute_write = AsyncMock(return_value=[])
        
        result = await entity_repository.update_entity(
            "non-existent-id",
            {"description": "更新后的描述"}
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity(self, entity_repository):
        entity_repository.client.execute_write = AsyncMock(
            return_value=[{"deleted": 1}]
        )
        
        result = await entity_repository.delete_entity("test-id")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_entity_not_found(self, entity_repository):
        entity_repository.client.execute_write = AsyncMock(
            return_value=[{"deleted": 0}]
        )
        
        result = await entity_repository.delete_entity("non-existent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_search_entities(self, entity_repository):
        entities = [
            {"id": str(uuid4()), "name": "张三", "type": "Person"},
            {"id": str(uuid4()), "name": "张四", "type": "Person"}
        ]
        entity_repository.client.execute_read = AsyncMock(
            return_value=[{"e": e} for e in entities]
        )
        
        result = await entity_repository.search_entities("张")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_entities_with_type(self, entity_repository):
        entities = [
            {"id": str(uuid4()), "name": "张三", "type": "Person"}
        ]
        entity_repository.client.execute_read = AsyncMock(
            return_value=[{"e": e} for e in entities]
        )
        
        result = await entity_repository.search_entities("张", entity_type="Person")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_count_entities_by_type(self, entity_repository):
        entity_repository.client.execute_read = AsyncMock(
            return_value=[{"count": 10}]
        )
        
        result = await entity_repository.count_entities_by_type("Person")
        assert result == 10


class TestRelationRepository:
    @pytest.mark.asyncio
    async def test_create_relation(self, relation_repository, sample_relation_data):
        relation_repository.client.execute_write = AsyncMock(
            return_value=[{
                "source": {"id": sample_relation_data["source_id"]},
                "r": {"id": sample_relation_data["id"], "type": sample_relation_data["type"]},
                "target": {"id": sample_relation_data["target_id"]}
            }]
        )
        
        result = await relation_repository.create_relation(
            relation_id=sample_relation_data["id"],
            source_id=sample_relation_data["source_id"],
            target_id=sample_relation_data["target_id"],
            relation_type=sample_relation_data["type"],
            properties={"confidence": 0.9}
        )
        
        assert result["relation"]["id"] == sample_relation_data["id"]

    @pytest.mark.asyncio
    async def test_get_relation_by_id(self, relation_repository, sample_relation_data):
        relation_repository.client.execute_read = AsyncMock(
            return_value=[{
                "source": {"id": sample_relation_data["source_id"]},
                "r": {"id": sample_relation_data["id"], "type": sample_relation_data["type"]},
                "target": {"id": sample_relation_data["target_id"]}
            }]
        )
        
        result = await relation_repository.get_relation_by_id(sample_relation_data["id"])
        assert result is not None
        assert result["relation"]["id"] == sample_relation_data["id"]

    @pytest.mark.asyncio
    async def test_get_relation_by_id_not_found(self, relation_repository):
        relation_repository.client.execute_read = AsyncMock(return_value=[])
        
        result = await relation_repository.get_relation_by_id("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_relations_by_entity_outgoing(self, relation_repository):
        relations = [
            {
                "source": {"id": "entity-1", "name": "张三"},
                "r": {"id": "rel-1", "type": "BELONGS_TO"},
                "target": {"id": "entity-2", "name": "阿里巴巴"}
            }
        ]
        relation_repository.client.execute_read = AsyncMock(return_value=relations)
        
        result = await relation_repository.get_relations_by_entity(
            "entity-1",
            direction="outgoing"
        )
        
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_relations_by_entity_incoming(self, relation_repository):
        relations = [
            {
                "source": {"id": "entity-2", "name": "阿里巴巴"},
                "r": {"id": "rel-1", "type": "BELONGS_TO"},
                "target": {"id": "entity-1", "name": "张三"}
            }
        ]
        relation_repository.client.execute_read = AsyncMock(return_value=relations)
        
        result = await relation_repository.get_relations_by_entity(
            "entity-1",
            direction="incoming"
        )
        
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_relations_by_entity_both(self, relation_repository):
        relations = [
            {
                "source": {"id": "entity-1", "name": "张三"},
                "r": {"id": "rel-1", "type": "BELONGS_TO"},
                "target": {"id": "entity-2", "name": "阿里巴巴"}
            },
            {
                "source": {"id": "entity-3", "name": "项目A"},
                "r": {"id": "rel-2", "type": "CREATED_BY"},
                "target": {"id": "entity-1", "name": "张三"}
            }
        ]
        relation_repository.client.execute_read = AsyncMock(return_value=relations)
        
        result = await relation_repository.get_relations_by_entity(
            "entity-1",
            direction="both"
        )
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_relations_by_type(self, relation_repository):
        relations = [
            {
                "source": {"id": "entity-1", "name": "张三"},
                "r": {"id": "rel-1", "type": "BELONGS_TO"},
                "target": {"id": "entity-2", "name": "阿里巴巴"}
            },
            {
                "source": {"id": "entity-3", "name": "李四"},
                "r": {"id": "rel-2", "type": "BELONGS_TO"},
                "target": {"id": "entity-4", "name": "腾讯"}
            }
        ]
        relation_repository.client.execute_read = AsyncMock(return_value=relations)
        
        result = await relation_repository.get_relations_by_type("BELONGS_TO")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_relation(self, relation_repository):
        relation_repository.client.execute_write = AsyncMock(
            return_value=[{"r": {"id": "rel-1", "confidence": 0.95}}]
        )
        
        result = await relation_repository.update_relation(
            "rel-1",
            {"confidence": 0.95}
        )
        
        assert result is not None
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_update_relation_not_found(self, relation_repository):
        relation_repository.client.execute_write = AsyncMock(return_value=[])
        
        result = await relation_repository.update_relation(
            "non-existent-id",
            {"confidence": 0.95}
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_relation(self, relation_repository):
        relation_repository.client.execute_write = AsyncMock(
            return_value=[{"deleted": 1}]
        )
        
        result = await relation_repository.delete_relation("rel-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_relation_not_found(self, relation_repository):
        relation_repository.client.execute_write = AsyncMock(
            return_value=[{"deleted": 0}]
        )
        
        result = await relation_repository.delete_relation("non-existent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_count_relations_by_entity(self, relation_repository):
        relation_repository.client.execute_read = AsyncMock(
            return_value=[{"count": 5}]
        )
        
        result = await relation_repository.count_relations_by_entity("entity-1")
        assert result == 5


class TestIndexManager:
    @pytest.mark.asyncio
    async def test_create_entity_name_index(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.create_entity_name_index()
        assert result is True

    @pytest.mark.asyncio
    async def test_create_entity_type_index(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.create_entity_type_index()
        assert result is True

    @pytest.mark.asyncio
    async def test_create_entity_id_index(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.create_entity_id_index()
        assert result is True

    @pytest.mark.asyncio
    async def test_create_fulltext_index(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.create_fulltext_index()
        assert result is True

    @pytest.mark.asyncio
    async def test_create_relation_id_index(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.create_relation_id_index()
        assert result is True

    @pytest.mark.asyncio
    async def test_create_relation_type_index(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.create_relation_type_index()
        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_indexes(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.ensure_indexes()
        
        assert result["entity_id_index"] is True
        assert result["entity_name_index"] is True
        assert result["entity_type_index"] is True
        assert result["entity_fulltext"] is True
        assert result["relation_id_index"] is True
        assert result["relation_type_index"] is True

    @pytest.mark.asyncio
    async def test_list_indexes(self, neo4j_client):
        expected_indexes = [
            {"name": "entity_id_index", "type": "BTREE"},
            {"name": "entity_name_index", "type": "BTREE"}
        ]
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_read = AsyncMock(return_value=expected_indexes)
        
        result = await index_manager.list_indexes()
        assert result == expected_indexes

    @pytest.mark.asyncio
    async def test_drop_index(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(return_value=[])
        
        result = await index_manager.drop_index("test_index")
        assert result is True

    @pytest.mark.asyncio
    async def test_create_index_failure(self, neo4j_client):
        index_manager = IndexManager()
        index_manager.client = neo4j_client
        neo4j_client.execute_write = AsyncMock(side_effect=Exception("Index creation failed"))
        
        result = await index_manager.create_entity_name_index()
        assert result is False
