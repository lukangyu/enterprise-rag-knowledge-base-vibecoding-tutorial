from fastapi import APIRouter
from typing import Dict, Any
import time
import logging

from services.kg.graph.neo4j_client import neo4j_client
from config.kg_settings import kg_settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health/kg")
async def kg_health_check() -> Dict[str, Any]:
    components = []
    overall_status = "healthy"

    neo4j_start = time.time()
    neo4j_connected = await neo4j_client.health_check()
    neo4j_latency = (time.time() - neo4j_start) * 1000

    neo4j_status = "healthy" if neo4j_connected else "unhealthy"
    if neo4j_status == "unhealthy":
        overall_status = "unhealthy"

    components.append({
        "name": "neo4j",
        "status": neo4j_status,
        "latency_ms": round(neo4j_latency, 2)
    })

    llm_status = "configured" if kg_settings.LLM_API_KEY else "not_configured"
    if llm_status == "not_configured":
        overall_status = "degraded" if overall_status == "healthy" else overall_status

    components.append({
        "name": "llm_service",
        "status": llm_status,
        "model": kg_settings.LLM_MODEL_NAME if kg_settings.LLM_API_KEY else None
    })

    return {
        "status": overall_status,
        "service": "knowledge-graph",
        "components": components,
        "config": {
            "neo4j_uri": kg_settings.NEO4J_URI,
            "neo4j_database": kg_settings.NEO4J_DATABASE,
            "llm_model": kg_settings.LLM_MODEL_NAME,
            "entity_types": kg_settings.ENTITY_TYPES,
            "relation_types": kg_settings.RELATION_TYPES
        },
        "timestamp": time.time()
    }


@router.get("/health/kg/neo4j")
async def neo4j_health_check() -> Dict[str, Any]:
    start_time = time.time()
    
    try:
        is_connected = await neo4j_client.health_check()
        latency = (time.time() - start_time) * 1000

        if is_connected:
            stats_query = """
            MATCH (e:Entity) WITH count(e) as entity_count
            MATCH ()-[r:RELATES]->() 
            RETURN entity_count, count(r) as relation_count
            """
            try:
                result = await neo4j_client.execute_read(stats_query)
                entity_count = result[0].get("entity_count", 0) if result else 0
                relation_count = result[0].get("relation_count", 0) if result else 0
            except Exception:
                entity_count = 0
                relation_count = 0

            return {
                "status": "healthy",
                "connection": "connected",
                "latency_ms": round(latency, 2),
                "database": kg_settings.NEO4J_DATABASE,
                "stats": {
                    "entities": entity_count,
                    "relations": relation_count
                }
            }
        else:
            return {
                "status": "unhealthy",
                "connection": "disconnected",
                "latency_ms": round(latency, 2),
                "error": "Failed to connect to Neo4j"
            }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "connection": "error",
            "latency_ms": round(latency, 2),
            "error": str(e)
        }


@router.get("/health/kg/llm")
async def llm_health_check() -> Dict[str, Any]:
    start_time = time.time()
    
    if not kg_settings.LLM_API_KEY:
        return {
            "status": "not_configured",
            "message": "LLM API key not configured"
        }

    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{kg_settings.LLM_API_BASE}/models",
                headers={"Authorization": f"Bearer {kg_settings.LLM_API_KEY}"},
                timeout=10.0
            )
        
        latency = (time.time() - start_time) * 1000

        if response.status_code == 200:
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "model": kg_settings.LLM_MODEL_NAME,
                "api_base": kg_settings.LLM_API_BASE
            }
        else:
            return {
                "status": "unhealthy",
                "latency_ms": round(latency, 2),
                "error": f"API returned status {response.status_code}"
            }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "latency_ms": round(latency, 2),
            "error": str(e)
        }


@router.get("/ready/kg")
async def kg_readiness_check() -> Dict[str, Any]:
    neo4j_ready = await neo4j_client.health_check()
    
    if neo4j_ready:
        return {"status": "ready", "service": "knowledge-graph"}
    else:
        return {"status": "not_ready", "service": "knowledge-graph", "error": "Neo4j not connected"}


@router.get("/live/kg")
async def kg_liveness_check() -> Dict[str, Any]:
    return {"status": "alive", "service": "knowledge-graph"}
