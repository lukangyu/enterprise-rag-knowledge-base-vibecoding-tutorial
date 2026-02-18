import logging
import heapq
from typing import Optional, List, Dict, Any, Set, Tuple
from collections import deque
from services.kg.graph.neo4j_client import neo4j_client
from services.kg.graph.entity_repository import entity_repository
from services.kg.graph.relation_repository import relation_repository

logger = logging.getLogger(__name__)


class TraversalEngine:
    def __init__(self):
        self.client = neo4j_client
        self.entity_repo = entity_repository
        self.relation_repo = relation_repository

    async def bfs_traverse(
        self,
        start_entity_id: str,
        max_hops: int = 3,
        relation_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100,
        return_paths: bool = False
    ) -> Dict[str, Any]:
        visited: Set[str] = set()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        paths: List[List[Dict[str, Any]]] = []
        queue: deque = deque([(start_entity_id, 0, [])])
        visited.add(start_entity_id)

        while queue and len(nodes) < limit:
            current_id, hop, path = queue.popleft()
            
            entity = await self.entity_repo.get_entity_by_id(current_id)
            if not entity:
                continue

            if entity_types and entity.get("type") not in entity_types:
                continue

            nodes.append({
                "entity": entity,
                "distance": hop
            })

            if return_paths:
                paths.append(path + [{"entity_id": current_id, "entity_name": entity.get("name")}])

            if hop >= max_hops:
                continue

            neighbors = await self.get_neighbors(
                current_id,
                relation_types=relation_types,
                min_confidence=min_confidence
            )

            for neighbor in neighbors:
                neighbor_id = neighbor["entity"]["id"]
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_path = path + [{
                        "entity_id": current_id,
                        "entity_name": entity.get("name"),
                        "relation": neighbor["relation"]
                    }]
                    queue.append((neighbor_id, hop + 1, new_path))
                    edges.append({
                        "relation": neighbor["relation"],
                        "source_id": current_id,
                        "target_id": neighbor_id,
                        "distance": hop + 1
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "paths": paths if return_paths else None,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    async def dfs_traverse(
        self,
        start_entity_id: str,
        max_hops: int = 3,
        relation_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100,
        return_paths: bool = False
    ) -> Dict[str, Any]:
        visited: Set[str] = set()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        paths: List[List[Dict[str, Any]]] = []
        stack: List[Tuple[str, int, List[Dict[str, Any]]]] = [(start_entity_id, 0, [])]

        while stack and len(nodes) < limit:
            current_id, hop, path = stack.pop()
            
            if current_id in visited:
                continue
            visited.add(current_id)

            entity = await self.entity_repo.get_entity_by_id(current_id)
            if not entity:
                continue

            if entity_types and entity.get("type") not in entity_types:
                continue

            nodes.append({
                "entity": entity,
                "distance": hop
            })

            if return_paths:
                paths.append(path + [{"entity_id": current_id, "entity_name": entity.get("name")}])

            if hop >= max_hops:
                continue

            neighbors = await self.get_neighbors(
                current_id,
                relation_types=relation_types,
                min_confidence=min_confidence
            )

            for neighbor in reversed(neighbors):
                neighbor_id = neighbor["entity"]["id"]
                if neighbor_id not in visited:
                    new_path = path + [{
                        "entity_id": current_id,
                        "entity_name": entity.get("name"),
                        "relation": neighbor["relation"]
                    }]
                    stack.append((neighbor_id, hop + 1, new_path))
                    edges.append({
                        "relation": neighbor["relation"],
                        "source_id": current_id,
                        "target_id": neighbor_id,
                        "distance": hop + 1
                    })

        return {
            "nodes": nodes,
            "edges": edges,
            "paths": paths if return_paths else None,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }

    async def shortest_path(
        self,
        source_id: str,
        target_id: str,
        relation_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        max_hops: int = 10
    ) -> Optional[Dict[str, Any]]:
        distances: Dict[str, float] = {source_id: 0}
        previous: Dict[str, Optional[str]] = {source_id: None}
        edge_info: Dict[str, Dict[str, Any]] = {}
        pq: List[Tuple[float, str]] = [(0, source_id)]
        visited: Set[str] = set()

        while pq:
            current_dist, current_id = heapq.heappop(pq)

            if current_id in visited:
                continue
            visited.add(current_id)

            if current_id == target_id:
                break

            if current_dist >= max_hops:
                continue

            neighbors = await self.get_neighbors(
                current_id,
                relation_types=relation_types,
                min_confidence=min_confidence
            )

            for neighbor in neighbors:
                neighbor_id = neighbor["entity"]["id"]
                relation = neighbor["relation"]
                weight = 1.0 / max(relation.get("confidence", 1.0), 0.1)
                new_dist = current_dist + weight

                if neighbor_id not in distances or new_dist < distances[neighbor_id]:
                    distances[neighbor_id] = new_dist
                    previous[neighbor_id] = current_id
                    edge_info[neighbor_id] = {
                        "relation": relation,
                        "source_id": current_id,
                        "target_id": neighbor_id
                    }
                    heapq.heappush(pq, (new_dist, neighbor_id))

        if target_id not in distances:
            return None

        path_nodes: List[Dict[str, Any]] = []
        path_edges: List[Dict[str, Any]] = []
        current = target_id

        while current is not None:
            entity = await self.entity_repo.get_entity_by_id(current)
            if entity:
                path_nodes.insert(0, {
                    "entity_id": current,
                    "entity_name": entity.get("name"),
                    "entity_type": entity.get("type")
                })
            
            if current in edge_info:
                path_edges.insert(0, edge_info[current])
            
            current = previous.get(current)

        return {
            "path": {
                "nodes": path_nodes,
                "edges": path_edges,
                "length": len(path_edges)
            },
            "total_weight": distances.get(target_id, 0),
            "hops": len(path_edges)
        }

    async def multi_hop_query(
        self,
        start_entity_id: str,
        hops: int = 2,
        relation_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> Dict[str, Any]:
        if hops < 1 or hops > 4:
            raise ValueError("Hops must be between 1 and 4")

        query = """
        MATCH path = (start:Entity {id: $start_id})-[:RELATES*1..%d]-(end:Entity)
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ($entity_types IS NULL OR end.type IN $entity_types)
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path, end, 
             [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as node_list,
             [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as rel_list
        RETURN DISTINCT 
            end.id as entity_id,
            end.name as entity_name,
            end.type as entity_type,
            node_list as path_nodes,
            rel_list as path_relations,
            length(path) as hop_count
        ORDER BY hop_count
        LIMIT $limit
        """ % hops

        params = {
            "start_id": start_entity_id,
            "relation_types": relation_types,
            "entity_types": entity_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        results = await self.client.execute_read(query, params)

        return {
            "results": results,
            "total": len(results),
            "hops": hops
        }

    async def get_neighbors(
        self,
        entity_id: str,
        relation_types: Optional[List[str]] = None,
        direction: str = "both",
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        if direction == "outgoing":
            query = """
            MATCH (e:Entity {id: $entity_id})-[r:RELATES]->(neighbor:Entity)
            WHERE ($relation_types IS NULL OR r.type IN $relation_types)
              AND r.confidence >= $min_confidence
            RETURN neighbor, r
            LIMIT $limit
            """
        elif direction == "incoming":
            query = """
            MATCH (neighbor:Entity)-[r:RELATES]->(e:Entity {id: $entity_id})
            WHERE ($relation_types IS NULL OR r.type IN $relation_types)
              AND r.confidence >= $min_confidence
            RETURN neighbor, r
            LIMIT $limit
            """
        else:
            query = """
            MATCH (e:Entity {id: $entity_id})-[r:RELATES]-(neighbor:Entity)
            WHERE ($relation_types IS NULL OR r.type IN $relation_types)
              AND r.confidence >= $min_confidence
            RETURN neighbor, r
            LIMIT $limit
            """

        params = {
            "entity_id": entity_id,
            "relation_types": relation_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        results = await self.client.execute_read(query, params)

        neighbors = []
        for record in results:
            neighbors.append({
                "entity": record.get("neighbor", {}),
                "relation": record.get("r", {})
            })

        return neighbors


traversal_engine = TraversalEngine()
