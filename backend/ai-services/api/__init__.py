from .embedding import router as embedding_router
from .health import router as health_router
from .entity import router as entity_router
from .relation import router as relation_router
from .graph import router as graph_router
from .kg_management import router as kg_management_router
from .kg_health import router as kg_health_router

__all__ = [
    'embedding_router',
    'health_router',
    'entity_router',
    'relation_router',
    'graph_router',
    'kg_management_router',
    'kg_health_router'
]
