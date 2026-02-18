import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from uuid import uuid4
import json

app = FastAPI()


class MockKGService:
    def __init__(self):
        self.entities = {}
        self.relations = {}

    async def get_entities(self, name=None, entity_type=None, min_confidence=0.0, limit=100, offset=0):
        entities = list(self.entities.values())
        if name:
            entities = [e for e in entities if name.lower() in e.get("name", "").lower()]
        if entity_type:
            entities = [e for e in entities if e.get("type") == entity_type]
        entities = [e for e in entities if e.get("confidence", 0) >= min_confidence]
        return entities[offset:offset + limit], len(entities)

    async def get_entity_by_id(self, entity_id):
        return self.entities.get(entity_id)

    async def create_entity(self, entity_data):
        entity_id = str(uuid4())
        entity_data["id"] = entity_id
        self.entities[entity_id] = entity_data
        return entity_data

    async def get_relations(self, head_entity_id=None, tail_entity_id=None, relation_type=None, min_confidence=0.0, limit=100, offset=0):
        relations = list(self.relations.values())
        if head_entity_id:
            relations = [r for r in relations if r.get("head_entity_id") == head_entity_id]
        if tail_entity_id:
            relations = [r for r in relations if r.get("tail_entity_id") == tail_entity_id]
        if relation_type:
            relations = [r for r in relations if r.get("relation_type") == relation_type]
        relations = [r for r in relations if r.get("confidence", 0) >= min_confidence]
        return relations[offset:offset + limit], len(relations)

    async def traverse(self, start_entity_id, max_hops=3, direction="both", limit=100):
        nodes = []
        edges = []
        if start_entity_id in self.entities:
            nodes.append({"entity": self.entities[start_entity_id], "distance": 0})
        return nodes, edges

    async def find_path(self, start_entity_id, end_entity_id, max_hops=5):
        if start_entity_id in self.entities and end_entity_id in self.entities:
            return [{"nodes": [start_entity_id, end_entity_id], "edges": []}]
        return []

    async def get_subgraph(self, entity_ids, include_relations=True, max_depth=1):
        entities = [self.entities.get(eid) for eid in entity_ids if eid in self.entities]
        return entities, []

    async def extract(self, text, entity_types=None, relation_types=None):
        return [], [], 100.0

    async def resolve_entity(self, entity_name, entity_type=None):
        for entity in self.entities.values():
            if entity.get("name") == entity_name:
                return entity
        return None


mock_kg_service = MockKGService()


@app.get("/api/v1/kg/entities")
async def get_entities(name: str = None, entity_type: str = None, min_confidence: float = 0.0, limit: int = 100, offset: int = 0):
    entities, total = await mock_kg_service.get_entities(name, entity_type, min_confidence, limit, offset)
    return {"entities": entities, "total": total}


@app.get("/api/v1/kg/entities/{entity_id}")
async def get_entity_by_id(entity_id: str):
    entity = await mock_kg_service.get_entity_by_id(entity_id)
    if entity:
        return entity
    return {"error": "Entity not found"}, 404


@app.get("/api/v1/kg/relations")
async def get_relations(head_entity_id: str = None, tail_entity_id: str = None, relation_type: str = None, min_confidence: float = 0.0, limit: int = 100, offset: int = 0):
    relations, total = await mock_kg_service.get_relations(head_entity_id, tail_entity_id, relation_type, min_confidence, limit, offset)
    return {"relations": relations, "total": total}


@app.post("/api/v1/kg/traverse")
async def traverse(request: dict):
    nodes, edges = await mock_kg_service.traverse(
        request.get("start_entity_id"),
        request.get("max_hops", 3),
        request.get("direction", "both"),
        request.get("limit", 100)
    )
    return {"nodes": nodes, "edges": edges}


@app.post("/api/v1/kg/path")
async def find_path(request: dict):
    paths = await mock_kg_service.find_path(
        request.get("start_entity_id"),
        request.get("end_entity_id"),
        request.get("max_hops", 5)
    )
    return {"paths": paths, "total": len(paths)}


@app.post("/api/v1/kg/subgraph")
async def get_subgraph(request: dict):
    entities, relations = await mock_kg_service.get_subgraph(
        request.get("entity_ids", []),
        request.get("include_relations", True),
        request.get("max_depth", 1)
    )
    return {"entities": entities, "relations": relations}


@app.post("/api/v1/kg/extract")
async def extract(request: dict):
    entities, relations, extraction_time = await mock_kg_service.extract(
        request.get("text"),
        request.get("entity_types"),
        request.get("relation_types")
    )
    return {"entities": entities, "relations": relations, "extraction_time_ms": extraction_time}


@app.post("/api/v1/kg/resolve")
async def resolve_entity(request: dict):
    entity = await mock_kg_service.resolve_entity(
        request.get("entity_name"),
        request.get("entity_type")
    )
    if entity:
        return entity
    return {"error": "Entity not resolved"}, 404


class TestKGAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def setup_data(self):
        mock_kg_service.entities = {
            "entity-1": {"id": "entity-1", "name": "张三", "type": "Person", "confidence": 0.9},
            "entity-2": {"id": "entity-2", "name": "阿里巴巴", "type": "Organization", "confidence": 0.85},
            "entity-3": {"id": "entity-3", "name": "杭州", "type": "Location", "confidence": 0.8}
        }
        mock_kg_service.relations = {
            "rel-1": {"id": "rel-1", "head_entity_id": "entity-1", "tail_entity_id": "entity-2", "relation_type": "BELONGS_TO", "confidence": 0.9}
        }

    def test_get_entities(self, client):
        response = client.get("/api/v1/kg/entities")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "total" in data
        assert data["total"] == 3

    def test_get_entities_with_name_filter(self, client):
        response = client.get("/api/v1/kg/entities?name=张")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entities"][0]["name"] == "张三"

    def test_get_entities_with_type_filter(self, client):
        response = client.get("/api/v1/kg/entities?entity_type=Person")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entities"][0]["type"] == "Person"

    def test_get_entities_with_confidence_filter(self, client):
        response = client.get("/api/v1/kg/entities?min_confidence=0.85")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_entities_with_pagination(self, client):
        response = client.get("/api/v1/kg/entities?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 2
        assert data["total"] == 3

    def test_get_entity_by_id(self, client):
        response = client.get("/api/v1/kg/entities/entity-1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "entity-1"
        assert data["name"] == "张三"

    def test_get_entity_by_id_not_found(self, client):
        response = client.get("/api/v1/kg/entities/non-existent-id")
        assert response.status_code == 404

    def test_get_relations(self, client):
        response = client.get("/api/v1/kg/relations")
        assert response.status_code == 200
        data = response.json()
        assert "relations" in data
        assert "total" in data
        assert data["total"] == 1

    def test_get_relations_with_head_entity_filter(self, client):
        response = client.get("/api/v1/kg/relations?head_entity_id=entity-1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_relations_with_type_filter(self, client):
        response = client.get("/api/v1/kg/relations?relation_type=BELONGS_TO")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_relations_with_confidence_filter(self, client):
        response = client.get("/api/v1/kg/relations?min_confidence=0.95")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_traverse(self, client):
        response = client.post(
            "/api/v1/kg/traverse",
            json={"start_entity_id": "entity-1", "max_hops": 2, "direction": "both"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    def test_traverse_with_limit(self, client):
        response = client.post(
            "/api/v1/kg/traverse",
            json={"start_entity_id": "entity-1", "max_hops": 3, "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) <= 10

    def test_traverse_non_existent_entity(self, client):
        response = client.post(
            "/api/v1/kg/traverse",
            json={"start_entity_id": "non-existent-id"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) == 0

    def test_path(self, client):
        response = client.post(
            "/api/v1/kg/path",
            json={"start_entity_id": "entity-1", "end_entity_id": "entity-2", "max_hops": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "total" in data

    def test_path_same_entity(self, client):
        response = client.post(
            "/api/v1/kg/path",
            json={"start_entity_id": "entity-1", "end_entity_id": "entity-1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_path_no_path(self, client):
        response = client.post(
            "/api/v1/kg/path",
            json={"start_entity_id": "entity-1", "end_entity_id": "entity-3", "max_hops": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_subgraph(self, client):
        response = client.post(
            "/api/v1/kg/subgraph",
            json={"entity_ids": ["entity-1", "entity-2"], "include_relations": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "relations" in data
        assert len(data["entities"]) == 2

    def test_subgraph_without_relations(self, client):
        response = client.post(
            "/api/v1/kg/subgraph",
            json={"entity_ids": ["entity-1"], "include_relations": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 1
        assert len(data["relations"]) == 0

    def test_subgraph_empty_ids(self, client):
        response = client.post(
            "/api/v1/kg/subgraph",
            json={"entity_ids": []}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 0

    def test_extract(self, client):
        response = client.post(
            "/api/v1/kg/extract",
            json={"text": "张三在阿里巴巴工作"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "relations" in data
        assert "extraction_time_ms" in data

    def test_extract_with_types(self, client):
        response = client.post(
            "/api/v1/kg/extract",
            json={
                "text": "张三在阿里巴巴工作",
                "entity_types": ["Person", "Organization"],
                "relation_types": ["BELONGS_TO"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data

    def test_extract_empty_text(self, client):
        response = client.post(
            "/api/v1/kg/extract",
            json={"text": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["entities"] == []
        assert data["relations"] == []

    def test_resolve_entity(self, client):
        response = client.post(
            "/api/v1/kg/resolve",
            json={"entity_name": "张三"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "张三"

    def test_resolve_entity_with_type(self, client):
        response = client.post(
            "/api/v1/kg/resolve",
            json={"entity_name": "张三", "entity_type": "Person"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "张三"
        assert data["type"] == "Person"

    def test_resolve_entity_not_found(self, client):
        response = client.post(
            "/api/v1/kg/resolve",
            json={"entity_name": "不存在的实体"}
        )
        assert response.status_code == 404


class TestKGAPIErrorHandling:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_invalid_entity_id_format(self, client):
        response = client.get("/api/v1/kg/entities/")
        assert response.status_code == 404

    def test_missing_required_field_traverse(self, client):
        response = client.post(
            "/api/v1/kg/traverse",
            json={}
        )
        assert response.status_code == 200

    def test_missing_required_field_path(self, client):
        response = client.post(
            "/api/v1/kg/path",
            json={}
        )
        assert response.status_code == 200

    def test_missing_required_field_subgraph(self, client):
        response = client.post(
            "/api/v1/kg/subgraph",
            json={}
        )
        assert response.status_code == 200

    def test_missing_required_field_extract(self, client):
        response = client.post(
            "/api/v1/kg/extract",
            json={}
        )
        assert response.status_code == 200

    def test_invalid_confidence_value(self, client):
        response = client.get("/api/v1/kg/entities?min_confidence=1.5")
        assert response.status_code == 200

    def test_invalid_limit_value(self, client):
        response = client.get("/api/v1/kg/entities?limit=-1")
        assert response.status_code == 200

    def test_invalid_offset_value(self, client):
        response = client.get("/api/v1/kg/entities?offset=-1")
        assert response.status_code == 200


class TestKGAPIPerformance:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def setup_large_data(self):
        for i in range(100):
            mock_kg_service.entities[f"entity-{i}"] = {
                "id": f"entity-{i}",
                "name": f"实体{i}",
                "type": "Person" if i % 2 == 0 else "Organization",
                "confidence": 0.5 + (i % 5) * 0.1
            }

    def test_large_dataset_pagination(self, client):
        response = client.get("/api/v1/kg/entities?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entities"]) == 10

    def test_large_dataset_filter(self, client):
        response = client.get("/api/v1/kg/entities?entity_type=Person&limit=50")
        assert response.status_code == 200
        data = response.json()
        for entity in data["entities"]:
            assert entity["type"] == "Person"

    def test_multiple_concurrent_requests(self, client):
        responses = []
        for i in range(5):
            response = client.get(f"/api/v1/kg/entities?limit=10&offset={i*10}")
            responses.append(response)
        
        for response in responses:
            assert response.status_code == 200
