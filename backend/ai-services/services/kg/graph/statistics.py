import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from services.kg.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


@dataclass
class EntityStats:
    total_count: int
    type_distribution: Dict[str, int]
    avg_confidence: float
    avg_relations_per_entity: float


@dataclass
class RelationStats:
    total_count: int
    type_distribution: Dict[str, int]
    avg_confidence: float
    avg_evidence_length: float


@dataclass
class GraphDensity:
    node_count: int
    edge_count: int
    density: float
    max_possible_edges: int
    connectivity_ratio: float


@dataclass
class OverviewStats:
    total_entities: int
    total_relations: int
    entity_types: int
    relation_types: int
    graph_density: float
    avg_entity_confidence: float
    avg_relation_confidence: float
    last_updated: str


class GraphStatisticsService:
    def __init__(self):
        self.client = neo4j_client

    async def get_entity_stats(self) -> EntityStats:
        count_query = """
        MATCH (e:Entity)
        RETURN count(e) as total_count
        """
        count_result = await self.client.execute_read(count_query)
        total_count = count_result[0].get("total_count", 0) if count_result else 0

        type_query = """
        MATCH (e:Entity)
        RETURN e.type as type, count(e) as count
        ORDER BY count DESC
        """
        type_result = await self.client.execute_read(type_query)
        type_distribution = {
            record.get("type", "Unknown"): record.get("count", 0)
            for record in type_result
        }

        confidence_query = """
        MATCH (e:Entity)
        WHERE e.confidence IS NOT NULL
        RETURN avg(e.confidence) as avg_confidence
        """
        confidence_result = await self.client.execute_read(confidence_query)
        avg_confidence = 0.0
        if confidence_result and confidence_result[0].get("avg_confidence"):
            avg_confidence = round(confidence_result[0].get("avg_confidence", 0.0), 4)

        relations_query = """
        MATCH (e:Entity)
        OPTIONAL MATCH (e)-[r:RELATES]-()
        WITH e, count(r) as rel_count
        RETURN avg(rel_count) as avg_relations
        """
        relations_result = await self.client.execute_read(relations_query)
        avg_relations = 0.0
        if relations_result and relations_result[0].get("avg_relations") is not None:
            avg_relations = round(relations_result[0].get("avg_relations", 0.0), 4)

        return EntityStats(
            total_count=total_count,
            type_distribution=type_distribution,
            avg_confidence=avg_confidence,
            avg_relations_per_entity=avg_relations
        )

    async def get_relation_stats(self) -> RelationStats:
        count_query = """
        MATCH ()-[r:RELATES]->()
        RETURN count(r) as total_count
        """
        count_result = await self.client.execute_read(count_query)
        total_count = count_result[0].get("total_count", 0) if count_result else 0

        type_query = """
        MATCH ()-[r:RELATES]->()
        RETURN r.type as type, count(r) as count
        ORDER BY count DESC
        """
        type_result = await self.client.execute_read(type_query)
        type_distribution = {
            record.get("type", "Unknown"): record.get("count", 0)
            for record in type_result
        }

        confidence_query = """
        MATCH ()-[r:RELATES]->()
        WHERE r.confidence IS NOT NULL
        RETURN avg(r.confidence) as avg_confidence
        """
        confidence_result = await self.client.execute_read(confidence_query)
        avg_confidence = 0.0
        if confidence_result and confidence_result[0].get("avg_confidence"):
            avg_confidence = round(confidence_result[0].get("avg_confidence", 0.0), 4)

        evidence_query = """
        MATCH ()-[r:RELATES]->()
        WHERE r.evidence IS NOT NULL
        RETURN avg(size(r.evidence)) as avg_length
        """
        evidence_result = await self.client.execute_read(evidence_query)
        avg_evidence_length = 0.0
        if evidence_result and evidence_result[0].get("avg_length"):
            avg_evidence_length = round(evidence_result[0].get("avg_length", 0.0), 2)

        return RelationStats(
            total_count=total_count,
            type_distribution=type_distribution,
            avg_confidence=avg_confidence,
            avg_evidence_length=avg_evidence_length
        )

    async def get_graph_density(self) -> GraphDensity:
        node_query = """
        MATCH (e:Entity)
        RETURN count(e) as node_count
        """
        node_result = await self.client.execute_read(node_query)
        node_count = node_result[0].get("node_count", 0) if node_result else 0

        edge_query = """
        MATCH ()-[r:RELATES]->()
        RETURN count(r) as edge_count
        """
        edge_result = await self.client.execute_read(edge_query)
        edge_count = edge_result[0].get("edge_count", 0) if edge_result else 0

        max_possible_edges = node_count * (node_count - 1) if node_count > 1 else 0

        density = 0.0
        if max_possible_edges > 0:
            density = round(edge_count / max_possible_edges, 6)

        connectivity_query = """
        MATCH (e:Entity)
        WHERE (e)-[:RELATES]-()
        RETURN count(e) as connected_count
        """
        connectivity_result = await self.client.execute_read(connectivity_query)
        connected_count = connectivity_result[0].get("connected_count", 0) if connectivity_result else 0

        connectivity_ratio = 0.0
        if node_count > 0:
            connectivity_ratio = round(connected_count / node_count, 4)

        return GraphDensity(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            max_possible_edges=max_possible_edges,
            connectivity_ratio=connectivity_ratio
        )

    async def get_overview_stats(self) -> OverviewStats:
        entity_stats = await self.get_entity_stats()
        relation_stats = await self.get_relation_stats()
        graph_density = await self.get_graph_density()

        entity_types_query = """
        MATCH (e:Entity)
        RETURN count(DISTINCT e.type) as type_count
        """
        entity_types_result = await self.client.execute_read(entity_types_query)
        entity_types = entity_types_result[0].get("type_count", 0) if entity_types_result else 0

        relation_types_query = """
        MATCH ()-[r:RELATES]->()
        RETURN count(DISTINCT r.type) as type_count
        """
        relation_types_result = await self.client.execute_read(relation_types_query)
        relation_types = relation_types_result[0].get("type_count", 0) if relation_types_result else 0

        return OverviewStats(
            total_entities=entity_stats.total_count,
            total_relations=relation_stats.total_count,
            entity_types=entity_types,
            relation_types=relation_types,
            graph_density=graph_density.density,
            avg_entity_confidence=entity_stats.avg_confidence,
            avg_relation_confidence=relation_stats.avg_confidence,
            last_updated=datetime.utcnow().isoformat()
        )

    async def get_entity_type_distribution(self) -> Dict[str, int]:
        query = """
        MATCH (e:Entity)
        RETURN e.type as type, count(e) as count
        ORDER BY count DESC
        """
        result = await self.client.execute_read(query)
        return {
            record.get("type", "Unknown"): record.get("count", 0)
            for record in result
        }

    async def get_relation_type_distribution(self) -> Dict[str, int]:
        query = """
        MATCH ()-[r:RELATES]->()
        RETURN r.type as type, count(r) as count
        ORDER BY count DESC
        """
        result = await self.client.execute_read(query)
        return {
            record.get("type", "Unknown"): record.get("count", 0)
            for record in result
        }

    async def get_top_entities_by_relations(self, limit: int = 10) -> List[Dict[str, Any]]:
        query = """
        MATCH (e:Entity)
        OPTIONAL MATCH (e)-[r:RELATES]-()
        WITH e, count(r) as relation_count
        ORDER BY relation_count DESC
        LIMIT $limit
        RETURN e.id as entity_id, e.name as name, e.type as type, relation_count
        """
        result = await self.client.execute_read(query, {"limit": limit})
        return [
            {
                "entity_id": record.get("entity_id"),
                "name": record.get("name"),
                "type": record.get("type"),
                "relation_count": record.get("relation_count", 0)
            }
            for record in result
        ]

    async def get_orphan_entities(self, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
        MATCH (e:Entity)
        WHERE NOT (e)-[:RELATES]-()
        RETURN e.id as entity_id, e.name as name, e.type as type, e.confidence as confidence
        LIMIT $limit
        """
        result = await self.client.execute_read(query, {"limit": limit})
        return [
            {
                "entity_id": record.get("entity_id"),
                "name": record.get("name"),
                "type": record.get("type"),
                "confidence": record.get("confidence", 0.0)
            }
            for record in result
        ]

    async def get_confidence_distribution(self) -> Dict[str, Any]:
        entity_query = """
        MATCH (e:Entity)
        WHERE e.confidence IS NOT NULL
        WITH CASE 
            WHEN e.confidence >= 0.9 THEN 'high'
            WHEN e.confidence >= 0.7 THEN 'medium'
            WHEN e.confidence >= 0.5 THEN 'low'
            ELSE 'very_low'
        END as confidence_level
        RETURN confidence_level, count(*) as count
        ORDER BY confidence_level
        """
        entity_result = await self.client.execute_read(entity_query)
        entity_distribution = {
            record.get("confidence_level"): record.get("count", 0)
            for record in entity_result
        }

        relation_query = """
        MATCH ()-[r:RELATES]->()
        WHERE r.confidence IS NOT NULL
        WITH CASE 
            WHEN r.confidence >= 0.9 THEN 'high'
            WHEN r.confidence >= 0.7 THEN 'medium'
            WHEN r.confidence >= 0.5 THEN 'low'
            ELSE 'very_low'
        END as confidence_level
        RETURN confidence_level, count(*) as count
        ORDER BY confidence_level
        """
        relation_result = await self.client.execute_read(relation_query)
        relation_distribution = {
            record.get("confidence_level"): record.get("count", 0)
            for record in relation_result
        }

        return {
            "entity_confidence": entity_distribution,
            "relation_confidence": relation_distribution
        }


graph_statistics_service = GraphStatisticsService()
