import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from services.kg.graph.neo4j_client import neo4j_client
from services.kg.graph.entity_repository import entity_repository
from services.kg.graph.relation_repository import relation_repository

logger = logging.getLogger(__name__)


@dataclass
class EvidenceNode:
    entity_id: str
    entity_name: str
    entity_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_docs: List[str] = field(default_factory=list)


@dataclass
class EvidenceEdge:
    relation_id: str
    relation_type: str
    head_entity_id: str
    tail_entity_id: str
    evidence: Optional[str] = None
    confidence: float = 1.0
    source_docs: List[str] = field(default_factory=list)


@dataclass
class EvidencePath:
    nodes: List[EvidenceNode]
    edges: List[EvidenceEdge]
    length: int
    confidence: float
    source_docs: List[str] = field(default_factory=list)


@dataclass
class EvidenceChain:
    chain_id: str
    start_entity: EvidenceNode
    end_entity: Optional[EvidenceNode]
    paths: List[EvidencePath]
    total_confidence: float
    source_documents: List[str]
    created_at: datetime = field(default_factory=datetime.now)


class EvidenceChainBuilder:
    def __init__(self):
        self.max_path_length = 5
        self.min_confidence = 0.5
        self.max_paths = 10

    async def build_chain(
        self,
        start_entity_id: str,
        end_entity_id: Optional[str] = None,
        max_hops: int = 3,
        relation_types: Optional[List[str]] = None
    ) -> EvidenceChain:
        logger.info(f"Building evidence chain from: {start_entity_id}")
        
        start_entity_data = await entity_repository.get_entity_by_id(start_entity_id)
        if not start_entity_data:
            raise ValueError(f"Start entity not found: {start_entity_id}")
        
        start_entity = EvidenceNode(
            entity_id=start_entity_data.get("id", ""),
            entity_name=start_entity_data.get("name", ""),
            entity_type=start_entity_data.get("type", ""),
            properties=start_entity_data.get("properties", {}),
            source_docs=start_entity_data.get("source_docs", [])
        )
        
        end_entity: Optional[EvidenceNode] = None
        if end_entity_id:
            end_entity_data = await entity_repository.get_entity_by_id(end_entity_id)
            if end_entity_data:
                end_entity = EvidenceNode(
                    entity_id=end_entity_data.get("id", ""),
                    entity_name=end_entity_data.get("name", ""),
                    entity_type=end_entity_data.get("type", ""),
                    properties=end_entity_data.get("properties", {}),
                    source_docs=end_entity_data.get("source_docs", [])
                )
        
        paths = await self._find_paths(
            start_entity_id=start_entity_id,
            end_entity_id=end_entity_id,
            max_hops=max_hops,
            relation_types=relation_types
        )
        
        total_confidence = self.calculate_chain_confidence(paths)
        
        source_documents = self._collect_source_documents(paths)
        
        chain_id = f"chain_{start_entity_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        chain = EvidenceChain(
            chain_id=chain_id,
            start_entity=start_entity,
            end_entity=end_entity,
            paths=paths,
            total_confidence=total_confidence,
            source_documents=source_documents
        )
        
        logger.info(
            f"Evidence chain built: {len(paths)} paths, "
            f"confidence: {total_confidence:.3f}"
        )
        
        return chain

    async def extract_path(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_hops: int = 5
    ) -> List[EvidencePath]:
        paths = await self._find_paths(
            start_entity_id=start_entity_id,
            end_entity_id=end_entity_id,
            max_hops=max_hops,
            relation_types=None
        )
        
        return paths

    async def link_source_docs(
        self,
        chain: EvidenceChain,
        doc_ids: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        links: Dict[str, List[str]] = {}
        
        for path in chain.paths:
            for node in path.nodes:
                if node.entity_id not in links:
                    links[node.entity_id] = []
                links[node.entity_id].extend(node.source_docs)
            
            for edge in path.edges:
                edge_key = f"{edge.head_entity_id}_{edge.relation_type}_{edge.tail_entity_id}"
                if edge_key not in links:
                    links[edge_key] = []
                links[edge_key].extend(edge.source_docs)
        
        if doc_ids:
            filtered_links = {
                k: [d for d in v if d in doc_ids]
                for k, v in links.items()
            }
            return filtered_links
        
        return links

    def calculate_chain_confidence(
        self,
        paths: List[EvidencePath]
    ) -> float:
        if not paths:
            return 0.0
        
        path_confidences = [p.confidence for p in paths]
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for i, confidence in enumerate(path_confidences):
            weight = 1.0 / (i + 1)
            weighted_sum += confidence * weight
            total_weight += weight
        
        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        path_diversity = min(1.0, len(paths) / 5.0)
        final_confidence = base_confidence * (0.7 + 0.3 * path_diversity)
        
        return min(1.0, max(0.0, final_confidence))

    async def _find_paths(
        self,
        start_entity_id: str,
        end_entity_id: Optional[str],
        max_hops: int,
        relation_types: Optional[List[str]]
    ) -> List[EvidencePath]:
        paths: List[EvidencePath] = []
        
        try:
            if end_entity_id:
                cypher = self._build_path_query(
                    start_entity_id,
                    end_entity_id,
                    max_hops,
                    relation_types
                )
            else:
                cypher = self._build_traversal_query(
                    start_entity_id,
                    max_hops,
                    relation_types
                )
            
            result = await neo4j_client.execute_read(cypher, {
                "start_id": start_entity_id,
                "end_id": end_entity_id,
                "max_hops": max_hops,
                "relation_types": relation_types or []
            })
            
            for record in result[:self.max_paths]:
                path = self._parse_path_record(record)
                if path:
                    paths.append(path)
                    
        except Exception as e:
            logger.error(f"Error finding paths: {e}")
        
        return paths

    def _build_path_query(
        self,
        start_id: str,
        end_id: str,
        max_hops: int,
        relation_types: Optional[List[str]]
    ) -> str:
        rel_pattern = ""
        if relation_types:
            rel_pattern = ":" + "|".join(relation_types)
        
        return f"""
        MATCH path = (start:Entity {{id: $start_id}})-[r{rel_pattern}*1..{max_hops}]-(end:Entity {{id: $end_id}})
        RETURN 
            [node in nodes(path) | {{
                id: node.id,
                name: node.name,
                type: node.type,
                properties: node.properties,
                source_docs: node.source_docs
            }}] as nodes,
            [rel in relationships(path) | {{
                id: rel.id,
                type: type(rel),
                start_id: startNode(rel).id,
                end_id: endNode(rel).id,
                evidence: rel.evidence,
                confidence: rel.confidence,
                source_docs: rel.source_docs
            }}] as edges,
            length(path) as path_length
        ORDER BY path_length ASC
        LIMIT $max_paths
        """

    def _build_traversal_query(
        self,
        start_id: str,
        max_hops: int,
        relation_types: Optional[List[str]]
    ) -> str:
        rel_pattern = ""
        if relation_types:
            rel_pattern = ":" + "|".join(relation_types)
        
        return f"""
        MATCH path = (start:Entity {{id: $start_id}})-[r{rel_pattern}*1..{max_hops}]-(end:Entity)
        WHERE start <> end
        RETURN 
            [node in nodes(path) | {{
                id: node.id,
                name: node.name,
                type: node.type,
                properties: node.properties,
                source_docs: node.source_docs
            }}] as nodes,
            [rel in relationships(path) | {{
                id: rel.id,
                type: type(rel),
                start_id: startNode(rel).id,
                end_id: endNode(rel).id,
                evidence: rel.evidence,
                confidence: rel.confidence,
                source_docs: rel.source_docs
            }}] as edges,
            length(path) as path_length
        ORDER BY path_length ASC
        LIMIT $max_paths
        """

    def _parse_path_record(self, record: Dict[str, Any]) -> Optional[EvidencePath]:
        try:
            nodes_data = record.get("nodes", [])
            edges_data = record.get("edges", [])
            path_length = record.get("path_length", 0)
            
            nodes = [
                EvidenceNode(
                    entity_id=n.get("id", ""),
                    entity_name=n.get("name", ""),
                    entity_type=n.get("type", ""),
                    properties=n.get("properties", {}),
                    source_docs=n.get("source_docs", [])
                )
                for n in nodes_data
            ]
            
            edges = [
                EvidenceEdge(
                    relation_id=e.get("id", ""),
                    relation_type=e.get("type", ""),
                    head_entity_id=e.get("start_id", ""),
                    tail_entity_id=e.get("end_id", ""),
                    evidence=e.get("evidence"),
                    confidence=e.get("confidence", 1.0),
                    source_docs=e.get("source_docs", [])
                )
                for e in edges_data
            ]
            
            confidence = self._calculate_path_confidence(edges)
            source_docs = self._collect_path_source_docs(nodes, edges)
            
            return EvidencePath(
                nodes=nodes,
                edges=edges,
                length=path_length,
                confidence=confidence,
                source_docs=source_docs
            )
            
        except Exception as e:
            logger.error(f"Error parsing path record: {e}")
            return None

    def _calculate_path_confidence(self, edges: List[EvidenceEdge]) -> float:
        if not edges:
            return 0.0
        
        edge_confidences = [e.confidence for e in edges]
        
        product = 1.0
        for conf in edge_confidences:
            product *= conf
        
        length_penalty = 1.0 / len(edges)
        
        return product * (0.5 + 0.5 * length_penalty)

    def _collect_path_source_docs(
        self,
        nodes: List[EvidenceNode],
        edges: List[EvidenceEdge]
    ) -> List[str]:
        source_docs = set()
        
        for node in nodes:
            source_docs.update(node.source_docs)
        
        for edge in edges:
            source_docs.update(edge.source_docs)
        
        return list(source_docs)

    def _collect_source_documents(self, paths: List[EvidencePath]) -> List[str]:
        all_docs = set()
        for path in paths:
            all_docs.update(path.source_docs)
        return list(all_docs)


evidence_chain_builder = EvidenceChainBuilder()
