from fastapi import APIRouter, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
import logging

from models.system_models import AuditLog, AuditLogCreate, AuditLogQuery

router = APIRouter(prefix="/system", tags=["审计日志"])
logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self):
        self._logs: List[AuditLog] = []
        self._max_logs = 10000
    
    def create_log(self, log_create: AuditLogCreate) -> AuditLog:
        log = AuditLog(
            id=f"log_{uuid.uuid4().hex[:12]}",
            **log_create.model_dump(),
            created_at=datetime.now()
        )
        
        self._logs.append(log)
        
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]
        
        logger.info(
            f"Audit log: user={log.username}, action={log.action}, "
            f"resource={log.resource_type}/{log.resource_id}"
        )
        
        return log
    
    def query_logs(self, query: AuditLogQuery) -> tuple[List[AuditLog], int]:
        filtered = self._logs.copy()
        
        if query.action:
            filtered = [l for l in filtered if l.action == query.action]
        
        if query.user_id:
            filtered = [l for l in filtered if l.user_id == query.user_id]
        
        if query.resource_type:
            filtered = [l for l in filtered if l.resource_type == query.resource_type]
        
        if query.start_time:
            filtered = [l for l in filtered if l.created_at >= query.start_time]
        
        if query.end_time:
            filtered = [l for l in filtered if l.created_at <= query.end_time]
        
        filtered.sort(key=lambda x: x.created_at, reverse=True)
        
        total = len(filtered)
        start = (query.page - 1) * query.size
        end = start + query.size
        
        return filtered[start:end], total
    
    def get_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        for log in self._logs:
            if log.id == log_id:
                return log
        return None
    
    def get_user_recent_logs(self, user_id: str, limit: int = 10) -> List[AuditLog]:
        user_logs = [l for l in self._logs if l.user_id == user_id]
        user_logs.sort(key=lambda x: x.created_at, reverse=True)
        return user_logs[:limit]


audit_service = AuditService()


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """查询审计日志"""
    query = AuditLogQuery(
        page=page,
        size=size,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time
    )
    
    logs, total = audit_service.query_logs(query)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [log.model_dump() for log in logs],
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": (total + size - 1) // size
            }
        }
    }


@router.post("/audit-logs")
async def create_audit_log(log: AuditLogCreate) -> Dict[str, Any]:
    """创建审计日志"""
    created_log = audit_service.create_log(log)
    
    return {
        "code": 201,
        "message": "Audit log created successfully",
        "data": created_log.model_dump()
    }


@router.get("/audit-logs/{log_id}")
async def get_audit_log(log_id: str) -> Dict[str, Any]:
    """获取审计日志详情"""
    log = audit_service.get_log_by_id(log_id)
    
    if not log:
        return {
            "code": 404,
            "message": "Audit log not found",
            "data": None
        }
    
    return {
        "code": 200,
        "message": "success",
        "data": log.model_dump()
    }


@router.get("/audit-logs/user/{user_id}/recent")
async def get_user_recent_logs(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50)
) -> Dict[str, Any]:
    """获取用户最近操作日志"""
    logs = audit_service.get_user_recent_logs(user_id, limit)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": user_id,
            "logs": [log.model_dump() for log in logs]
        }
    }


@router.get("/audit-logs/stats/summary")
async def get_audit_summary(
    days: int = Query(default=7, ge=1, le=30)
) -> Dict[str, Any]:
    """获取审计日志统计摘要"""
    start_time = datetime.now() - timedelta(days=days)
    
    recent_logs = [
        l for l in audit_service._logs
        if l.created_at >= start_time
    ]
    
    action_counts = {}
    resource_counts = {}
    user_counts = {}
    
    for log in recent_logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1
        user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "period_days": days,
            "total_logs": len(recent_logs),
            "by_action": action_counts,
            "by_resource_type": resource_counts,
            "unique_users": len(user_counts),
            "top_users": sorted(
                [{"user_id": k, "count": v} for k, v in user_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:5]
        }
    }
