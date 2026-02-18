import logging
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LayoutType(str, Enum):
    FORCE_DIRECTED = "force_directed"
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    GRID = "grid"


@dataclass
class NodePosition:
    x: float
    y: float
    z: float = 0.0


@dataclass
class VisualNode:
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    position: Optional[NodePosition] = None
    size: float = 20.0
    color: str = "#4A90D9"
    confidence: float = 1.0


@dataclass
class VisualEdge:
    id: str
    source: str
    target: str
    label: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    color: str = "#999999"
    confidence: float = 1.0


@dataclass
class GraphData:
    nodes: List[VisualNode]
    edges: List[VisualEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutConfig:
    layout_type: LayoutType = LayoutType.FORCE_DIRECTED
    width: float = 800.0
    height: float = 600.0
    node_spacing: float = 100.0
    margin: float = 50.0


class VisualizationDataGenerator:
    def __init__(self):
        self.type_colors: Dict[str, str] = {
            "Person": "#4A90D9",
            "Organization": "#50C878",
            "Location": "#FFB347",
            "Product": "#DDA0DD",
            "Event": "#F0E68C",
            "Concept": "#B0C4DE"
        }
        self.default_color = "#808080"
        self.relation_colors: Dict[str, str] = {
            "BELONGS_TO": "#3498DB",
            "CONTAINS": "#2ECC71",
            "LOCATED_AT": "#E74C3C",
            "CREATED_BY": "#9B59B6",
            "AFFECTS": "#F39C12",
            "DEPENDS_ON": "#1ABC9C"
        }
        self.default_edge_color = "#999999"

    def format_nodes(
        self,
        entities: List[Dict[str, Any]]
    ) -> List[VisualNode]:
        nodes: List[VisualNode] = []
        
        for entity in entities:
            entity_id = entity.get("id", "")
            entity_name = entity.get("name", "")
            entity_type = entity.get("type", "Concept")
            properties = entity.get("properties", {})
            confidence = entity.get("confidence", 1.0)
            
            node = VisualNode(
                id=entity_id,
                label=entity_name,
                type=entity_type,
                properties=properties,
                size=self._calculate_node_size(entity),
                color=self.type_colors.get(entity_type, self.default_color),
                confidence=confidence
            )
            nodes.append(node)
        
        return nodes

    def format_edges(
        self,
        relations: List[Dict[str, Any]]
    ) -> List[VisualEdge]:
        edges: List[VisualEdge] = []
        
        for relation in relations:
            relation_id = relation.get("id", "")
            relation_type = relation.get("relation_type") or relation.get("type", "")
            head_entity_id = relation.get("head_entity_id") or relation.get("start_id", "")
            tail_entity_id = relation.get("tail_entity_id") or relation.get("end_id", "")
            properties = relation.get("properties", {})
            confidence = relation.get("confidence", 1.0)
            
            edge = VisualEdge(
                id=relation_id,
                source=head_entity_id,
                target=tail_entity_id,
                label=relation_type,
                type=relation_type,
                properties=properties,
                weight=self._calculate_edge_weight(relation),
                color=self.relation_colors.get(relation_type, self.default_edge_color),
                confidence=confidence
            )
            edges.append(edge)
        
        return edges

    def generate_graph_data(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
        layout_config: Optional[LayoutConfig] = None
    ) -> GraphData:
        nodes = self.format_nodes(entities)
        edges = self.format_edges(relations)
        
        if layout_config:
            nodes = self.generate_layout(nodes, edges, layout_config)
        
        metadata = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "entity_types": list(set(n.type for n in nodes)),
            "relation_types": list(set(e.type for e in edges))
        }
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )

    def generate_layout(
        self,
        nodes: List[VisualNode],
        edges: List[VisualEdge],
        config: LayoutConfig
    ) -> List[VisualNode]:
        if not nodes:
            return nodes
        
        if config.layout_type == LayoutType.FORCE_DIRECTED:
            return self._force_directed_layout(nodes, edges, config)
        elif config.layout_type == LayoutType.HIERARCHICAL:
            return self._hierarchical_layout(nodes, edges, config)
        elif config.layout_type == LayoutType.CIRCULAR:
            return self._circular_layout(nodes, config)
        elif config.layout_type == LayoutType.GRID:
            return self._grid_layout(nodes, config)
        
        return nodes

    def _force_directed_layout(
        self,
        nodes: List[VisualNode],
        edges: List[VisualEdge],
        config: LayoutConfig
    ) -> List[VisualNode]:
        node_positions: Dict[str, NodePosition] = {}
        
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            radius = min(config.width, config.height) / 3
            node_positions[node.id] = NodePosition(
                x=config.width / 2 + radius * math.cos(angle),
                y=config.height / 2 + radius * math.sin(angle)
            )
        
        iterations = 50
        k = config.node_spacing
        
        for _ in range(iterations):
            forces: Dict[str, List[float]] = {n.id: [0.0, 0.0] for n in nodes}
            
            for i, n1 in enumerate(nodes):
                for j, n2 in enumerate(nodes):
                    if i >= j:
                        continue
                    
                    pos1 = node_positions[n1.id]
                    pos2 = node_positions[n2.id]
                    
                    dx = pos2.x - pos1.x
                    dy = pos2.y - pos1.y
                    distance = math.sqrt(dx * dx + dy * dy) + 0.01
                    
                    repulsion = k * k / distance
                    
                    forces[n1.id][0] -= dx / distance * repulsion
                    forces[n1.id][1] -= dy / distance * repulsion
                    forces[n2.id][0] += dx / distance * repulsion
                    forces[n2.id][1] += dy / distance * repulsion
            
            for edge in edges:
                source_pos = node_positions.get(edge.source)
                target_pos = node_positions.get(edge.target)
                
                if source_pos and target_pos:
                    dx = target_pos.x - source_pos.x
                    dy = target_pos.y - source_pos.y
                    distance = math.sqrt(dx * dx + dy * dy) + 0.01
                    
                    attraction = distance * distance / k
                    
                    forces[edge.source][0] += dx / distance * attraction
                    forces[edge.source][1] += dy / distance * attraction
                    forces[edge.target][0] -= dx / distance * attraction
                    forces[edge.target][1] -= dy / distance * attraction
            
            for node in nodes:
                force = forces[node.id]
                pos = node_positions[node.id]
                
                new_x = pos.x + force[0] * 0.1
                new_y = pos.y + force[1] * 0.1
                
                new_x = max(config.margin, min(config.width - config.margin, new_x))
                new_y = max(config.margin, min(config.height - config.margin, new_y))
                
                node_positions[node.id] = NodePosition(x=new_x, y=new_y)
        
        for node in nodes:
            node.position = node_positions.get(node.id)
        
        return nodes

    def _hierarchical_layout(
        self,
        nodes: List[VisualNode],
        edges: List[VisualEdge],
        config: LayoutConfig
    ) -> List[VisualNode]:
        levels: Dict[str, int] = {n.id: 0 for n in nodes}
        
        adjacency: Dict[str, List[str]] = {n.id: [] for n in nodes}
        for edge in edges:
            if edge.source in adjacency and edge.target in adjacency:
                adjacency[edge.source].append(edge.target)
        
        changed = True
        max_iterations = 10
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for node in nodes:
                for neighbor_id in adjacency.get(node.id, []):
                    if levels[neighbor_id] <= levels[node.id]:
                        levels[neighbor_id] = levels[node.id] + 1
                        changed = True
        
        level_nodes: Dict[int, List[VisualNode]] = {}
        for node in nodes:
            level = levels[node.id]
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        max_level = max(levels.values()) if levels else 0
        level_height = (config.height - 2 * config.margin) / (max_level + 1)
        
        for level, level_node_list in level_nodes.items():
            y = config.margin + level * level_height
            level_width = (config.width - 2 * config.margin) / max(len(level_node_list), 1)
            
            for i, node in enumerate(level_node_list):
                x = config.margin + i * level_width + level_width / 2
                node.position = NodePosition(x=x, y=y)
        
        return nodes

    def _circular_layout(
        self,
        nodes: List[VisualNode],
        config: LayoutConfig
    ) -> List[VisualNode]:
        if not nodes:
            return nodes
        
        center_x = config.width / 2
        center_y = config.height / 2
        radius = min(config.width, config.height) / 2 - config.margin
        
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes) - math.pi / 2
            node.position = NodePosition(
                x=center_x + radius * math.cos(angle),
                y=center_y + radius * math.sin(angle)
            )
        
        return nodes

    def _grid_layout(
        self,
        nodes: List[VisualNode],
        config: LayoutConfig
    ) -> List[VisualNode]:
        if not nodes:
            return nodes
        
        cols = math.ceil(math.sqrt(len(nodes)))
        rows = math.ceil(len(nodes) / cols)
        
        cell_width = (config.width - 2 * config.margin) / cols
        cell_height = (config.height - 2 * config.margin) / rows
        
        for i, node in enumerate(nodes):
            col = i % cols
            row = i // cols
            
            node.position = NodePosition(
                x=config.margin + col * cell_width + cell_width / 2,
                y=config.margin + row * cell_height + cell_height / 2
            )
        
        return nodes

    def _calculate_node_size(self, entity: Dict[str, Any]) -> float:
        base_size = 20.0
        
        properties = entity.get("properties", {})
        relation_count = properties.get("relation_count", 0)
        
        if relation_count > 0:
            size_multiplier = min(2.0, 1.0 + relation_count * 0.1)
            return base_size * size_multiplier
        
        return base_size

    def _calculate_edge_weight(self, relation: Dict[str, Any]) -> float:
        confidence = relation.get("confidence", 1.0)
        return confidence

    def to_dict(self, graph_data: GraphData) -> Dict[str, Any]:
        nodes_data = []
        for node in graph_data.nodes:
            node_dict = {
                "id": node.id,
                "label": node.label,
                "type": node.type,
                "properties": node.properties,
                "size": node.size,
                "color": node.color,
                "confidence": node.confidence
            }
            if node.position:
                node_dict["position"] = {
                    "x": node.position.x,
                    "y": node.position.y,
                    "z": node.position.z
                }
            nodes_data.append(node_dict)
        
        edges_data = []
        for edge in graph_data.edges:
            edges_data.append({
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "label": edge.label,
                "type": edge.type,
                "properties": edge.properties,
                "weight": edge.weight,
                "color": edge.color,
                "confidence": edge.confidence
            })
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "metadata": graph_data.metadata
        }


visualization_data_generator = VisualizationDataGenerator()
