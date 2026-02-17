from fastapi import APIRouter
from typing import Dict, Any
import time
import logging

from config.database import milvus_connection
from config.settings import settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    components = []

    milvus_status = "healthy" if milvus_connection.is_connected() else "unhealthy"
    components.append({
        "name": "milvus",
        "status": milvus_status
    })

    qwen_status = "configured" if settings.QWEN_API_KEY else "not_configured"
    components.append({
        "name": "qwen_api",
        "status": qwen_status
    })

    overall_status = "healthy" if all(
        c["status"] in ["healthy", "configured"] for c in components
    ) else "degraded"

    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "components": components,
        "timestamp": time.time()
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """就绪检查接口"""
    try:
        if not milvus_connection.is_connected():
            milvus_connection.connect()

        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "error": str(e)}


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """存活检查接口"""
    return {"status": "alive"}
