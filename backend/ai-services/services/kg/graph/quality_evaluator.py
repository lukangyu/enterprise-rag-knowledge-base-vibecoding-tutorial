import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from services.kg.graph.neo4j_client import neo4j_client
from services.kg.graph.statistics import graph_statistics_service

logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class CompletenessScore:
    score: float
    entity_coverage: float
    relation_coverage: float
    property_completeness: float
    description_coverage: float
    details: Dict[str, Any]


@dataclass
class ConsistencyScore:
    score: float
    type_consistency: float
    naming_consistency: float
    relation_consistency: float
    details: Dict[str, Any]


@dataclass
class AccuracyScore:
    score: float
    avg_entity_confidence: float
    avg_relation_confidence: float
    high_confidence_ratio: float
    low_confidence_count: int
    details: Dict[str, Any]


@dataclass
class QualityReport:
    overall_score: float
    level: QualityLevel
    completeness: CompletenessScore
    consistency: ConsistencyScore
    accuracy: AccuracyScore
    recommendations: List[str]
    generated_at: str


class GraphQualityEvaluator:
    def __init__(self):
        self.client = neo4j_client
        self.excellent_threshold = 0.85
        self.good_threshold = 0.70
        self.fair_threshold = 0.55

    async def evaluate_completeness(self) -> CompletenessScore:
        entity_count_query = """
        MATCH (e:Entity)
        RETURN count(e) as count
        """
        entity_result = await self.client.execute_read(entity_count_query)
        entity_count = entity_result[0].get("count", 0) if entity_result else 0

        relation_count_query = """
        MATCH ()-[r:RELATES]->()
        RETURN count(r) as count
        """
        relation_result = await self.client.execute_read(relation_count_query)
        relation_count = relation_result[0].get("count", 0) if relation_result else 0

        entity_coverage = min(1.0, entity_count / 1000) if entity_count > 0 else 0.0

        expected_relations = entity_count * 2
        relation_coverage = min(1.0, relation_count / expected_relations) if expected_relations > 0 else 0.0

        property_query = """
        MATCH (e:Entity)
        WITH e, keys(e) as props
        WITH avg(size(props)) as avg_props
        RETURN avg_props
        """
        property_result = await self.client.execute_read(property_query)
        avg_props = property_result[0].get("avg_props", 0) if property_result else 0
        property_completeness = min(1.0, avg_props / 5)

        description_query = """
        MATCH (e:Entity)
        WHERE e.description IS NOT NULL AND size(e.description) > 10
        RETURN count(e) as count
        """
        desc_result = await self.client.execute_read(description_query)
        entities_with_desc = desc_result[0].get("count", 0) if desc_result else 0
        description_coverage = entities_with_desc / entity_count if entity_count > 0 else 0.0

        score = (
            entity_coverage * 0.25 +
            relation_coverage * 0.25 +
            property_completeness * 0.25 +
            description_coverage * 0.25
        )

        return CompletenessScore(
            score=round(score, 4),
            entity_coverage=round(entity_coverage, 4),
            relation_coverage=round(relation_coverage, 4),
            property_completeness=round(property_completeness, 4),
            description_coverage=round(description_coverage, 4),
            details={
                "entity_count": entity_count,
                "relation_count": relation_count,
                "entities_with_description": entities_with_desc,
                "avg_properties_per_entity": round(avg_props, 2)
            }
        )

    async def evaluate_consistency(self) -> ConsistencyScore:
        type_query = """
        MATCH (e:Entity)
        WITH e.type as type, count(e) as count
        WITH collect({type: type, count: count}) as type_stats
        UNWIND type_stats as stat
        WITH sum(stat.count) as total, type_stats
        WITH [s IN type_stats WHERE s.count > total * 0.01] as significant_types
        RETURN size(significant_types) as significant_type_count, size(type_stats) as total_type_count
        """
        type_result = await self.client.execute_read(type_query)
        if type_result:
            significant_types = type_result[0].get("significant_type_count", 0)
            total_types = type_result[0].get("total_type_count", 0)
            type_consistency = significant_types / total_types if total_types > 0 else 0.0
        else:
            type_consistency = 0.0

        naming_query = """
        MATCH (e:Entity)
        WITH e.name as name
        WITH collect(name) as names
        WITH [n IN names WHERE size(n) >= 2 AND size(n) <= 50] as valid_names
        RETURN size(valid_names) as valid_count, size(names) as total_count
        """
        naming_result = await self.client.execute_read(naming_query)
        if naming_result:
            valid_names = naming_result[0].get("valid_count", 0)
            total_names = naming_result[0].get("total_count", 0)
            naming_consistency = valid_names / total_names if total_names > 0 else 0.0
        else:
            naming_consistency = 0.0

        relation_query = """
        MATCH ()-[r:RELATES]->()
        WITH r.type as type, count(r) as count
        WITH collect({type: type, count: count}) as rel_stats
        UNWIND rel_stats as stat
        WITH sum(stat.count) as total, rel_stats
        WITH [s IN rel_stats WHERE s.count > total * 0.01] as significant_types
        RETURN size(significant_types) as significant_type_count, size(rel_stats) as total_type_count
        """
        relation_result = await self.client.execute_read(relation_query)
        if relation_result:
            significant_rel_types = relation_result[0].get("significant_type_count", 0)
            total_rel_types = relation_result[0].get("total_type_count", 0)
            relation_consistency = significant_rel_types / total_rel_types if total_rel_types > 0 else 0.0
        else:
            relation_consistency = 0.0

        score = (
            type_consistency * 0.4 +
            naming_consistency * 0.3 +
            relation_consistency * 0.3
        )

        return ConsistencyScore(
            score=round(score, 4),
            type_consistency=round(type_consistency, 4),
            naming_consistency=round(naming_consistency, 4),
            relation_consistency=round(relation_consistency, 4),
            details={
                "significant_entity_types": significant_types if type_result else 0,
                "total_entity_types": total_types if type_result else 0,
                "valid_entity_names": valid_names if naming_result else 0,
                "total_entity_names": total_names if naming_result else 0
            }
        )

    async def evaluate_accuracy(self) -> AccuracyScore:
        entity_confidence_query = """
        MATCH (e:Entity)
        WHERE e.confidence IS NOT NULL
        RETURN avg(e.confidence) as avg_confidence
        """
        entity_conf_result = await self.client.execute_read(entity_confidence_query)
        avg_entity_confidence = entity_conf_result[0].get("avg_confidence", 0.0) if entity_conf_result else 0.0

        relation_confidence_query = """
        MATCH ()-[r:RELATES]->()
        WHERE r.confidence IS NOT NULL
        RETURN avg(r.confidence) as avg_confidence
        """
        relation_conf_result = await self.client.execute_read(relation_confidence_query)
        avg_relation_confidence = relation_conf_result[0].get("avg_confidence", 0.0) if relation_conf_result else 0.0

        high_confidence_query = """
        MATCH (e:Entity)
        WHERE e.confidence >= 0.8
        WITH count(e) as high_conf_entities
        MATCH ()-[r:RELATES]->()
        WHERE r.confidence >= 0.8
        RETURN high_conf_entities + count(r) as high_conf_count
        """
        high_conf_result = await self.client.execute_read(high_confidence_query)
        high_conf_count = high_conf_result[0].get("high_conf_count", 0) if high_conf_result else 0

        total_count_query = """
        MATCH (e:Entity)
        WITH count(e) as entity_count
        MATCH ()-[r:RELATES]->()
        RETURN entity_count + count(r) as total_count
        """
        total_result = await self.client.execute_read(total_count_query)
        total_count = total_result[0].get("total_count", 0) if total_result else 0

        high_confidence_ratio = high_conf_count / total_count if total_count > 0 else 0.0

        low_confidence_query = """
        MATCH (e:Entity)
        WHERE e.confidence < 0.5
        WITH count(e) as low_conf_entities
        MATCH ()-[r:RELATES]->()
        WHERE r.confidence < 0.5
        RETURN low_conf_entities + count(r) as low_conf_count
        """
        low_conf_result = await self.client.execute_read(low_confidence_query)
        low_confidence_count = low_conf_result[0].get("low_conf_count", 0) if low_conf_result else 0

        score = (
            avg_entity_confidence * 0.35 +
            avg_relation_confidence * 0.35 +
            high_confidence_ratio * 0.30
        )

        return AccuracyScore(
            score=round(score, 4),
            avg_entity_confidence=round(avg_entity_confidence, 4),
            avg_relation_confidence=round(avg_relation_confidence, 4),
            high_confidence_ratio=round(high_confidence_ratio, 4),
            low_confidence_count=low_confidence_count,
            details={
                "high_confidence_count": high_conf_count,
                "total_elements": total_count,
                "entity_confidence_avg": round(avg_entity_confidence, 4),
                "relation_confidence_avg": round(avg_relation_confidence, 4)
            }
        )

    def _determine_quality_level(self, score: float) -> QualityLevel:
        if score >= self.excellent_threshold:
            return QualityLevel.EXCELLENT
        elif score >= self.good_threshold:
            return QualityLevel.GOOD
        elif score >= self.fair_threshold:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR

    def _generate_recommendations(
        self,
        completeness: CompletenessScore,
        consistency: ConsistencyScore,
        accuracy: AccuracyScore
    ) -> List[str]:
        recommendations = []

        if completeness.entity_coverage < 0.5:
            recommendations.append("建议增加更多实体以提升图谱覆盖率")

        if completeness.relation_coverage < 0.5:
            recommendations.append("建议增加实体间的关系以丰富图谱结构")

        if completeness.description_coverage < 0.5:
            recommendations.append("建议为实体添加描述信息以提升可理解性")

        if consistency.naming_consistency < 0.8:
            recommendations.append("建议规范化实体命名，确保名称长度在2-50字符之间")

        if consistency.type_consistency < 0.7:
            recommendations.append("建议统一实体类型分类，减少过于分散的类型")

        if accuracy.avg_entity_confidence < 0.7:
            recommendations.append("建议重新审核低置信度实体，提升实体抽取准确性")

        if accuracy.avg_relation_confidence < 0.7:
            recommendations.append("建议重新审核低置信度关系，提升关系抽取准确性")

        if accuracy.low_confidence_count > 0:
            recommendations.append(f"发现{accuracy.low_confidence_count}个低置信度元素，建议人工审核")

        if not recommendations:
            recommendations.append("图谱质量良好，建议持续监控和维护")

        return recommendations

    async def generate_report(self) -> QualityReport:
        completeness = await self.evaluate_completeness()
        consistency = await self.evaluate_consistency()
        accuracy = await self.evaluate_accuracy()

        overall_score = (
            completeness.score * 0.35 +
            consistency.score * 0.30 +
            accuracy.score * 0.35
        )

        level = self._determine_quality_level(overall_score)
        recommendations = self._generate_recommendations(completeness, consistency, accuracy)

        return QualityReport(
            overall_score=round(overall_score, 4),
            level=level,
            completeness=completeness,
            consistency=consistency,
            accuracy=accuracy,
            recommendations=recommendations,
            generated_at=datetime.utcnow().isoformat()
        )

    async def evaluate_entity_quality(self, entity_id: str) -> Dict[str, Any]:
        query = """
        MATCH (e:Entity {id: $entity_id})
        OPTIONAL MATCH (e)-[r:RELATES]-()
        RETURN e.id as id, e.name as name, e.type as type, 
               e.confidence as confidence, e.description as description,
               count(r) as relation_count, keys(e) as properties
        """
        result = await self.client.execute_read(query, {"entity_id": entity_id})
        
        if not result:
            return {"error": "Entity not found", "entity_id": entity_id}

        entity_data = result[0]
        
        quality_score = 0.0
        factors = {}

        if entity_data.get("confidence"):
            factors["confidence"] = entity_data["confidence"]
            quality_score += entity_data["confidence"] * 0.3

        if entity_data.get("description") and len(entity_data["description"]) > 10:
            factors["has_description"] = True
            quality_score += 0.2
        else:
            factors["has_description"] = False

        relation_count = entity_data.get("relation_count", 0)
        factors["relation_count"] = relation_count
        quality_score += min(0.3, relation_count * 0.1)

        properties = entity_data.get("properties", [])
        property_count = len([p for p in properties if p not in ["id", "name", "type", "created_at", "updated_at"]])
        factors["property_count"] = property_count
        quality_score += min(0.2, property_count * 0.05)

        return {
            "entity_id": entity_id,
            "name": entity_data.get("name"),
            "type": entity_data.get("type"),
            "quality_score": round(quality_score, 4),
            "factors": factors
        }

    async def evaluate_relation_quality(self, relation_id: str) -> Dict[str, Any]:
        query = """
        MATCH (source)-[r:RELATES {id: $relation_id}]->(target)
        RETURN r.id as id, r.type as type, r.confidence as confidence,
               r.evidence as evidence, source.name as source_name,
               target.name as target_name, keys(r) as properties
        """
        result = await self.client.execute_read(query, {"relation_id": relation_id})
        
        if not result:
            return {"error": "Relation not found", "relation_id": relation_id}

        relation_data = result[0]
        
        quality_score = 0.0
        factors = {}

        if relation_data.get("confidence"):
            factors["confidence"] = relation_data["confidence"]
            quality_score += relation_data["confidence"] * 0.4

        if relation_data.get("evidence") and len(relation_data["evidence"]) > 5:
            factors["has_evidence"] = True
            quality_score += 0.3
        else:
            factors["has_evidence"] = False

        properties = relation_data.get("properties", [])
        property_count = len([p for p in properties if p not in ["id", "type", "created_at", "updated_at"]])
        factors["property_count"] = property_count
        quality_score += min(0.3, property_count * 0.1)

        return {
            "relation_id": relation_id,
            "type": relation_data.get("type"),
            "source_name": relation_data.get("source_name"),
            "target_name": relation_data.get("target_name"),
            "quality_score": round(quality_score, 4),
            "factors": factors
        }


graph_quality_evaluator = GraphQualityEvaluator()
