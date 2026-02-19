from api.system.config import router as config_router
from api.system.status import router as status_router
from api.system.audit import router as audit_router
from api.system.statistics import router as statistics_router

__all__ = [
    "config_router",
    "status_router",
    "audit_router",
    "statistics_router",
]
