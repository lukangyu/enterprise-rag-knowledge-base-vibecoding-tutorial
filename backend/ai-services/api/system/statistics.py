from fastapi import APIRouter, Query
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from models.system_models import (
    StatisticsResponse, DocumentStats, QueryStats, 
    KGStats, UserStats
)
from api.system.status import health_service

router = APIRouter(prefix="/system/statistics", tags=["统计分析"])
logger = logging.getLogger(__name__)


class StatisticsService:
    def __init__(self):
        self._query_history: list = []
        self._document_stats = DocumentStats()
        self._kg_stats = KGStats()
        self._user_stats = UserStats()
    
    def record_query(self, response_time_ms: float, satisfaction: float = 0.0):
        self._query_history.append({
            "timestamp": datetime.now(),
            "response_time_ms": response_time_ms,
            "satisfaction": satisfaction
        })
        
        if len(self._query_history) > 10000:
            self._query_history = self._query_history[-10000:]
    
    def update_document_stats(self, stats: DocumentStats):
        self._document_stats = stats
    
    def update_kg_stats(self, stats: KGStats):
        self._kg_stats = stats
    
    def update_user_stats(self, stats: UserStats):
        self._user_stats = stats
    
    def get_query_stats(self, days: int = 7) -> QueryStats:
        start_time = datetime.now() - timedelta(days=days)
        
        recent_queries = [
            q for q in self._query_history
            if q["timestamp"] >= start_time
        ]
        
        if not recent_queries:
            return QueryStats()
        
        total = len(recent_queries)
        avg_time = sum(q["response_time_ms"] for q in recent_queries) / total
        avg_satisfaction = sum(q["satisfaction"] for q in recent_queries) / total
        
        by_day = {}
        for q in recent_queries:
            date_str = q["timestamp"].strftime("%Y-%m-%d")
            by_day[date_str] = by_day.get(date_str, 0) + 1
        
        return QueryStats(
            total_queries=total,
            avg_response_time_ms=round(avg_time, 2),
            avg_satisfaction=round(avg_satisfaction, 2),
            by_day=[
                {"date": k, "count": v}
                for k, v in sorted(by_day.items())
            ]
        )


statistics_service = StatisticsService()


@router.get("")
async def get_statistics(
    period: str = Query(default="7d", description="统计周期: 1d, 7d, 30d")
) -> Dict[str, Any]:
    """获取统计数据"""
    days_map = {"1d": 1, "7d": 7, "30d": 30}
    days = days_map.get(period, 7)
    
    response = StatisticsResponse(
        period=period,
        document_stats=statistics_service._document_stats,
        query_stats=statistics_service.get_query_stats(days),
        kg_stats=statistics_service._kg_stats,
        user_stats=statistics_service._user_stats
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": response.model_dump()
    }


@router.get("/documents")
async def get_document_stats() -> Dict[str, Any]:
    """获取文档统计"""
    stats = statistics_service._document_stats
    
    return {
        "code": 200,
        "message": "success",
        "data": stats.model_dump()
    }


@router.get("/queries")
async def get_query_stats(
    days: int = Query(default=7, ge=1, le=30)
) -> Dict[str, Any]:
    """获取查询统计"""
    stats = statistics_service.get_query_stats(days)
    
    return {
        "code": 200,
        "message": "success",
        "data": stats.model_dump()
    }


@router.get("/knowledge-graph")
async def get_kg_stats() -> Dict[str, Any]:
    """获取知识图谱统计"""
    stats = statistics_service._kg_stats
    
    return {
        "code": 200,
        "message": "success",
        "data": stats.model_dump()
    }


@router.get("/users")
async def get_user_stats() -> Dict[str, Any]:
    """获取用户统计"""
    stats = statistics_service._user_stats
    
    return {
        "code": 200,
        "message": "success",
        "data": stats.model_dump()
    }


@router.get("/realtime")
async def get_realtime_stats() -> Dict[str, Any]:
    """获取实时统计"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "queries_today": health_service.get_query_count(),
            "active_connections": 0,
            "pending_tasks": 0,
            "cache_hit_rate": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    }


@router.post("/refresh")
async def refresh_statistics() -> Dict[str, Any]:
    """刷新统计数据"""
    try:
        from services.embedding.milvus_client import milvus_client
        from services.embedding.es_client import es_client
        
        doc_count = 0
        try:
            if milvus_client._collection:
                stats = milvus_client._collection.num_entities
                doc_count = stats
        except Exception as e:
            logger.warning(f"Failed to get document count from Milvus: {e}")
        
        statistics_service._document_stats = DocumentStats(
            total=doc_count,
            by_type={"pdf": 0, "docx": 0, "md": 0, "txt": 0},
            by_status={"published": doc_count, "processing": 0, "failed": 0}
        )
        
        health_service.set_document_count(doc_count)
        
        return {
            "code": 200,
            "message": "Statistics refreshed successfully",
            "data": {
                "document_count": doc_count,
                "refreshed_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to refresh statistics: {e}")
        return {
            "code": 500,
            "message": f"Failed to refresh statistics: {str(e)}",
            "data": None
        }
