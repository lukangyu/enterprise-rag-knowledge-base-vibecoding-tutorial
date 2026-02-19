from fastapi import APIRouter
from typing import Dict, Any, List
import time
import psutil
import logging
from datetime import datetime

from models.system_models import (
    SystemStatus, ComponentStatus, ResourceUsage, 
    SystemStatistics
)
from config.settings import settings
from config.database import milvus_connection
from services.embedding.es_client import es_client
from services.embedding.milvus_client import milvus_client

router = APIRouter(prefix="/system", tags=["系统状态"])
logger = logging.getLogger(__name__)

START_TIME = time.time()


class HealthCheckService:
    def __init__(self):
        self._query_count = 0
        self._document_count = 0
        self._entity_count = 0
    
    def increment_query_count(self):
        self._query_count += 1
    
    def get_query_count(self) -> int:
        return self._query_count
    
    def reset_query_count(self):
        self._query_count = 0
    
    def set_document_count(self, count: int):
        self._document_count = count
    
    def set_entity_count(self, count: int):
        self._entity_count = count


health_service = HealthCheckService()


def get_uptime() -> str:
    elapsed = time.time() - START_TIME
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)
    return f"{days}d {hours}h {minutes}m"


async def check_milvus() -> ComponentStatus:
    try:
        start = time.time()
        connected = milvus_connection.is_connected()
        latency = (time.time() - start) * 1000
        
        return ComponentStatus(
            name="milvus",
            status="healthy" if connected else "unhealthy",
            latency_ms=round(latency, 2),
            message="Connected" if connected else "Disconnected"
        )
    except Exception as e:
        return ComponentStatus(
            name="milvus",
            status="unhealthy",
            message=str(e)
        )


async def check_elasticsearch() -> ComponentStatus:
    try:
        start = time.time()
        if es_client.client:
            info = es_client.client.info()
            latency = (time.time() - start) * 1000
            return ComponentStatus(
                name="elasticsearch",
                status="healthy",
                latency_ms=round(latency, 2),
                message=f"Version: {info.get('version', {}).get('number', 'unknown')}"
            )
        return ComponentStatus(
            name="elasticsearch",
            status="unhealthy",
            message="Client not initialized"
        )
    except Exception as e:
        return ComponentStatus(
            name="elasticsearch",
            status="unhealthy",
            message=str(e)
        )


async def check_qwen_api() -> ComponentStatus:
    configured = bool(settings.QWEN_API_KEY)
    return ComponentStatus(
        name="qwen_api",
        status="configured" if configured else "not_configured",
        message="API key configured" if configured else "API key not set"
    )


def get_resource_usage() -> ResourceUsage:
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    gpu = None
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0].load * 100
    except ImportError:
        logger.debug("GPUtil not installed, GPU monitoring disabled")
    except Exception as e:
        logger.warning(f"Failed to get GPU usage: {e}")
    
    return ResourceUsage(
        cpu_usage=round(cpu, 1),
        memory_usage=round(memory, 1),
        disk_usage=round(disk, 1),
        gpu_usage=round(gpu, 1) if gpu else None
    )


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """获取系统状态"""
    components = [
        await check_milvus(),
        await check_elasticsearch(),
        await check_qwen_api()
    ]
    
    all_healthy = all(
        c.status in ["healthy", "configured"] for c in components
    )
    
    status = SystemStatus(
        status="healthy" if all_healthy else "degraded",
        version=settings.APP_VERSION,
        uptime=get_uptime(),
        components=components,
        resources=get_resource_usage(),
        statistics=SystemStatistics(
            total_documents=health_service._document_count,
            total_chunks=0,
            total_entities=health_service._entity_count,
            total_relations=0,
            total_users=0,
            queries_today=health_service.get_query_count()
        )
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": status.model_dump()
    }


@router.get("/status/components")
async def get_component_status() -> Dict[str, Any]:
    """获取组件状态"""
    components = [
        await check_milvus(),
        await check_elasticsearch(),
        await check_qwen_api()
    ]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "components": [c.model_dump() for c in components],
            "overall_status": "healthy" if all(
                c.status in ["healthy", "configured"] for c in components
            ) else "degraded"
        }
    }


@router.get("/status/resources")
async def get_resource_usage_api() -> Dict[str, Any]:
    """获取资源使用情况"""
    resources = get_resource_usage()
    
    return {
        "code": 200,
        "message": "success",
        "data": resources.model_dump()
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    components = [
        await check_milvus(),
        await check_elasticsearch(),
        await check_qwen_api()
    ]
    
    overall_status = "healthy" if all(
        c.status in ["healthy", "configured"] for c in components
    ) else "degraded"
    
    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "components": [c.model_dump() for c in components],
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
