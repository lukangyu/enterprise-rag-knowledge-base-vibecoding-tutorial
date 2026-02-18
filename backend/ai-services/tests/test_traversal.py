import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from collections import deque
from typing import List, Dict, Any, Set, Tuple


class GraphTraversalService:
    def __init__(self, neo4j_client):
        self.client = neo4j_client

    async def bfs_traverse(
        self,
        start_entity_id: str,
        max_hops: int = 3,
        relation_types: List[str] = None,
        direction: str = "both",
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        visited: Set[str] = set()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        queue: deque = deque([(start_entity_id, 0)])
        
        while queue and len(nodes) < limit:
            current_id, distance = queue.popleft()
            
            if current_id in visited or distance > max_hops:
                continue
            
            visited.add(current_id)
            
            entity = await self._get_entity(current_id)
            if entity:
                nodes.append({"entity": entity, "distance": distance})
            
            if distance < max_hops:
                relations = await self._get_relations(current_id, direction, relation_types)
                for rel in relations:
                    neighbor_id = self._get_neighbor_id(rel, current_id, direction)
                    if neighbor_id and neighbor_id not in visited:
                        queue.append((neighbor_id, distance + 1))
                        edges.append({"relation": rel, "distance": distance + 1})
        
        return nodes, edges

    async def dfs_traverse(
        self,
        start_entity_id: str,
        max_hops: int = 3,
        relation_types: List[str] = None,
        direction: str = "both",
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        visited: Set[str] = set()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        
        async def dfs(entity_id: str, distance: int):
            if len(nodes) >= limit or distance > max_hops or entity_id in visited:
                return
            
            visited.add(entity_id)
            
            entity = await self._get_entity(entity_id)
            if entity:
                nodes.append({"entity": entity, "distance": distance})
            
            if distance < max_hops:
                relations = await self._get_relations(entity_id, direction, relation_types)
                for rel in relations:
                    neighbor_id = self._get_neighbor_id(rel, entity_id, direction)
                    if neighbor_id and neighbor_id not in visited:
                        edges.append({"relation": rel, "distance": distance + 1})
                        await dfs(neighbor_id, distance + 1)
        
        await dfs(start_entity_id, 0)
        return nodes, edges

    async def shortest_path(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_hops: int = 5,
        relation_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        if start_entity_id == end_entity_id:
            return [{"entity_id": start_entity_id}]
        
        visited: Set[str] = {start_entity_id}
        parent: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        queue: deque = deque([start_entity_id])
        
        while queue:
            current_id = queue.popleft()
            
            relations = await self._get_relations(current_id, "both", relation_types)
            for rel in relations:
                neighbor_id = self._get_neighbor_id(rel, current_id, "both")
                
                if neighbor_id and neighbor_id not in visited:
                    visited.add(neighbor_id)
                    parent[neighbor_id] = (current_id, rel)
                    
                    if neighbor_id == end_entity_id:
                        return self._reconstruct_path(parent, start_entity_id, end_entity_id)
                    
                    if len(parent) < max_hops * 10:
                        queue.append(neighbor_id)
        
        return []

    async def multi_hop_query(
        self,
        start_entity_id: str,
        relation_path: List[str],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        current_ids = [start_entity_id]
        
        for relation_type in relation_path:
            next_ids = []
            for entity_id in current_ids:
                relations = await self._get_relations(entity_id, "outgoing", [relation_type])
                for rel in relations:
                    neighbor_id = rel.get("target", {}).get("id")
                    if neighbor_id:
                        next_ids.append(neighbor_id)
            current_ids = list(set(next_ids))
            
            if not current_ids:
                return []
        
        results = []
        for entity_id in current_ids[:limit]:
            entity = await self._get_entity(entity_id)
            if entity:
                results.append(entity)
        
        return results

    async def path_query(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_hops: int = 5,
        relation_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        paths = []
        visited: Set[str] = set()
        
        async def find_paths(current_id: str, path: List[Dict[str, Any]], depth: int):
            if depth > max_hops or len(paths) >= 10:
                return
            
            if current_id == end_entity_id:
                paths.append(path.copy())
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            
            relations = await self._get_relations(current_id, "both", relation_types)
            for rel in relations:
                neighbor_id = self._get_neighbor_id(rel, current_id, "both")
                if neighbor_id and neighbor_id not in visited:
                    path.append({
                        "from": current_id,
                        "relation": rel,
                        "to": neighbor_id
                    })
                    await find_paths(neighbor_id, path, depth + 1)
                    path.pop()
            
            visited.remove(current_id)
        
        await find_paths(start_entity_id, [], 0)
        return paths

    async def subgraph_query(
        self,
        entity_ids: List[str],
        include_relations: bool = True,
        max_depth: int = 1
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        entities = []
        relations = []
        visited: Set[str] = set()
        
        for entity_id in entity_ids:
            if entity_id not in visited:
                entity = await self._get_entity(entity_id)
                if entity:
                    entities.append(entity)
                    visited.add(entity_id)
        
        if include_relations and max_depth > 0:
            for entity_id in entity_ids:
                entity_relations = await self._get_relations(entity_id, "both", None)
                for rel in entity_relations:
                    source_id = rel.get("source", {}).get("id")
                    target_id = rel.get("target", {}).get("id")
                    if source_id and target_id:
                        relations.append(rel)
                        if target_id not in visited:
                            entity = await self._get_entity(target_id)
                            if entity:
                                entities.append(entity)
                                visited.add(target_id)
        
        return entities, relations

    async def _get_entity(self, entity_id: str) -> Dict[str, Any]:
        query = "MATCH (e:Entity {id: $entity_id}) RETURN e"
        result = await self.client.execute_read(query, {"entity_id": entity_id})
        if result:
            return result[0].get("e", {})
        return {}

    async def _get_relations(
        self,
        entity_id: str,
        direction: str,
        relation_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        if direction == "outgoing":
            query = "MATCH (source:Entity {id: $entity_id})-[r:RELATES]->(target) RETURN source, r, target"
        elif direction == "incoming":
            query = "MATCH (source)-[r:RELATES]->(target:Entity {id: $entity_id}) RETURN source, r, target"
        else:
            query = "MATCH (source)-[r:RELATES]-(target:Entity {id: $entity_id}) RETURN source, r, target"
        
        result = await self.client.execute_read(query, {"entity_id": entity_id})
        return [
            {
                "source": record.get("source", {}),
                "relation": record.get("r", {}),
                "target": record.get("target", {})
            }
            for record in result
        ]

    def _get_neighbor_id(self, rel: Dict[str, Any], current_id: str, direction: str) -> str:
        source_id = rel.get("source", {}).get("id")
        target_id = rel.get("target", {}).get("id")
        
        if direction == "outgoing":
            return target_id
        elif direction == "incoming":
            return source_id
        else:
            if source_id == current_id:
                return target_id
            return source_id

    def _reconstruct_path(
        self,
        parent: Dict[str, Tuple[str, Dict[str, Any]]],
        start_id: str,
        end_id: str
    ) -> List[Dict[str, Any]]:
        path = []
        current_id = end_id
        
        while current_id != start_id:
            if current_id not in parent:
                return []
            prev_id, relation = parent[current_id]
            path.append({
                "from": prev_id,
                "relation": relation,
                "to": current_id
            })
            current_id = prev_id
        
        path.reverse()
        return path


class TestGraphTraversal:
    @pytest.fixture
    def traversal_service(self, neo4j_client):
        return GraphTraversalService(neo4j_client)

    @pytest.fixture
    def sample_graph_data(self):
        return {
            "entities": [
                {"id": "entity-1", "name": "张三", "type": "Person"},
                {"id": "entity-2", "name": "阿里巴巴", "type": "Organization"},
                {"id": "entity-3", "name": "杭州", "type": "Location"},
                {"id": "entity-4", "name": "李四", "type": "Person"},
                {"id": "entity-5", "name": "腾讯", "type": "Organization"}
            ],
            "relations": [
                {"source": {"id": "entity-1"}, "relation": {"type": "BELONGS_TO"}, "target": {"id": "entity-2"}},
                {"source": {"id": "entity-2"}, "relation": {"type": "LOCATED_AT"}, "target": {"id": "entity-3"}},
                {"source": {"id": "entity-4"}, "relation": {"type": "BELONGS_TO"}, "target": {"id": "entity-5"}}
            ]
        }

    @pytest.mark.asyncio
    async def test_bfs_traverse(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            elif "MATCH (source)-[r:RELATES]" in query:
                relations = []
                for r in sample_graph_data["relations"]:
                    if r["source"]["id"] == entity_id or r["target"]["id"] == entity_id:
                        relations.append(r)
                return relations
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        nodes, edges = await traversal_service.bfs_traverse("entity-1", max_hops=2)
        
        assert len(nodes) > 0
        assert nodes[0]["entity"]["id"] == "entity-1"
        assert nodes[0]["distance"] == 0

    @pytest.mark.asyncio
    async def test_bfs_traverse_with_limit(self, traversal_service, sample_graph_data):
        traversal_service.client.execute_read = AsyncMock(return_value=[])
        
        nodes, edges = await traversal_service.bfs_traverse("entity-1", max_hops=3, limit=1)
        
        assert len(nodes) <= 1

    @pytest.mark.asyncio
    async def test_bfs_traverse_with_relation_types(self, traversal_service, sample_graph_data):
        traversal_service.client.execute_read = AsyncMock(return_value=[])
        
        nodes, edges = await traversal_service.bfs_traverse(
            "entity-1",
            max_hops=2,
            relation_types=["BELONGS_TO"]
        )
        
        assert isinstance(nodes, list)
        assert isinstance(edges, list)

    @pytest.mark.asyncio
    async def test_dfs_traverse(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            elif "MATCH (source)-[r:RELATES]" in query:
                relations = []
                for r in sample_graph_data["relations"]:
                    if r["source"]["id"] == entity_id or r["target"]["id"] == entity_id:
                        relations.append(r)
                return relations
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        nodes, edges = await traversal_service.dfs_traverse("entity-1", max_hops=2)
        
        assert len(nodes) > 0
        assert nodes[0]["entity"]["id"] == "entity-1"
        assert nodes[0]["distance"] == 0

    @pytest.mark.asyncio
    async def test_dfs_traverse_with_limit(self, traversal_service, sample_graph_data):
        traversal_service.client.execute_read = AsyncMock(return_value=[])
        
        nodes, edges = await traversal_service.dfs_traverse("entity-1", max_hops=3, limit=1)
        
        assert len(nodes) <= 1

    @pytest.mark.asyncio
    async def test_shortest_path(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            elif "MATCH (source)-[r:RELATES]" in query:
                relations = []
                for r in sample_graph_data["relations"]:
                    if r["source"]["id"] == entity_id or r["target"]["id"] == entity_id:
                        relations.append(r)
                return relations
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        path = await traversal_service.shortest_path("entity-1", "entity-2", max_hops=3)
        
        assert isinstance(path, list)

    @pytest.mark.asyncio
    async def test_shortest_path_same_entity(self, traversal_service):
        path = await traversal_service.shortest_path("entity-1", "entity-1")
        
        assert len(path) == 1
        assert path[0]["entity_id"] == "entity-1"

    @pytest.mark.asyncio
    async def test_shortest_path_no_path(self, traversal_service, sample_graph_data):
        traversal_service.client.execute_read = AsyncMock(return_value=[])
        
        path = await traversal_service.shortest_path("entity-1", "entity-4", max_hops=2)
        
        assert path == []

    @pytest.mark.asyncio
    async def test_multi_hop_query(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            elif "MATCH (source:Entity {id: $entity_id})-[r:RELATES]->(target)" in query:
                relations = []
                for r in sample_graph_data["relations"]:
                    if r["source"]["id"] == entity_id:
                        relations.append(r)
                return relations
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        results = await traversal_service.multi_hop_query(
            "entity-1",
            ["BELONGS_TO"]
        )
        
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_multi_hop_query_no_results(self, traversal_service):
        traversal_service.client.execute_read = AsyncMock(return_value=[])
        
        results = await traversal_service.multi_hop_query(
            "entity-1",
            ["NON_EXISTENT_RELATION"]
        )
        
        assert results == []

    @pytest.mark.asyncio
    async def test_multi_hop_query_multiple_hops(self, traversal_service, sample_graph_data):
        traversal_service.client.execute_read = AsyncMock(return_value=[])
        
        results = await traversal_service.multi_hop_query(
            "entity-1",
            ["BELONGS_TO", "LOCATED_AT"]
        )
        
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_path_query(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            elif "MATCH (source)-[r:RELATES]" in query:
                relations = []
                for r in sample_graph_data["relations"]:
                    if r["source"]["id"] == entity_id or r["target"]["id"] == entity_id:
                        relations.append(r)
                return relations
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        paths = await traversal_service.path_query("entity-1", "entity-3", max_hops=3)
        
        assert isinstance(paths, list)

    @pytest.mark.asyncio
    async def test_path_query_no_path(self, traversal_service):
        traversal_service.client.execute_read = AsyncMock(return_value=[])
        
        paths = await traversal_service.path_query("entity-1", "entity-4", max_hops=2)
        
        assert paths == []

    @pytest.mark.asyncio
    async def test_subgraph_query(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            elif "MATCH (source)-[r:RELATES]" in query:
                relations = []
                for r in sample_graph_data["relations"]:
                    if r["source"]["id"] == entity_id or r["target"]["id"] == entity_id:
                        relations.append(r)
                return relations
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        entities, relations = await traversal_service.subgraph_query(
            ["entity-1", "entity-2"],
            include_relations=True
        )
        
        assert len(entities) > 0
        assert isinstance(relations, list)

    @pytest.mark.asyncio
    async def test_subgraph_query_without_relations(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        entities, relations = await traversal_service.subgraph_query(
            ["entity-1", "entity-2"],
            include_relations=False
        )
        
        assert len(entities) > 0
        assert relations == []

    @pytest.mark.asyncio
    async def test_subgraph_query_empty_ids(self, traversal_service):
        entities, relations = await traversal_service.subgraph_query([])
        
        assert entities == []
        assert relations == []

    @pytest.mark.asyncio
    async def test_subgraph_query_with_depth(self, traversal_service, sample_graph_data):
        def mock_execute_read(query, params):
            entity_id = params.get("entity_id")
            if "MATCH (e:Entity" in query:
                for e in sample_graph_data["entities"]:
                    if e["id"] == entity_id:
                        return [{"e": e}]
                return []
            elif "MATCH (source)-[r:RELATES]" in query:
                relations = []
                for r in sample_graph_data["relations"]:
                    if r["source"]["id"] == entity_id or r["target"]["id"] == entity_id:
                        relations.append(r)
                return relations
            return []
        
        traversal_service.client.execute_read = AsyncMock(side_effect=mock_execute_read)
        
        entities, relations = await traversal_service.subgraph_query(
            ["entity-1"],
            include_relations=True,
            max_depth=2
        )
        
        assert isinstance(entities, list)
        assert isinstance(relations, list)

    def test_get_neighbor_id_outgoing(self, traversal_service):
        rel = {
            "source": {"id": "entity-1"},
            "target": {"id": "entity-2"}
        }
        
        neighbor_id = traversal_service._get_neighbor_id(rel, "entity-1", "outgoing")
        assert neighbor_id == "entity-2"

    def test_get_neighbor_id_incoming(self, traversal_service):
        rel = {
            "source": {"id": "entity-1"},
            "target": {"id": "entity-2"}
        }
        
        neighbor_id = traversal_service._get_neighbor_id(rel, "entity-2", "incoming")
        assert neighbor_id == "entity-1"

    def test_get_neighbor_id_both(self, traversal_service):
        rel = {
            "source": {"id": "entity-1"},
            "target": {"id": "entity-2"}
        }
        
        neighbor_id = traversal_service._get_neighbor_id(rel, "entity-1", "both")
        assert neighbor_id == "entity-2"
        
        neighbor_id = traversal_service._get_neighbor_id(rel, "entity-2", "both")
        assert neighbor_id == "entity-1"

    def test_reconstruct_path(self, traversal_service):
        parent = {
            "entity-3": ("entity-2", {"type": "LOCATED_AT"}),
            "entity-2": ("entity-1", {"type": "BELONGS_TO"})
        }
        
        path = traversal_service._reconstruct_path(parent, "entity-1", "entity-3")
        
        assert len(path) == 2
        assert path[0]["from"] == "entity-1"
        assert path[1]["to"] == "entity-3"

    def test_reconstruct_path_no_path(self, traversal_service):
        parent = {
            "entity-2": ("entity-1", {"type": "BELONGS_TO"})
        }
        
        path = traversal_service._reconstruct_path(parent, "entity-1", "entity-3")
        
        assert path == []
