from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.kg_settings import kg_settings
from config.logging import setup_logging
from services.kg.graph.neo4j_client import neo4j_client
from api.entity import router as entity_router
from api.relation import router as relation_router
from api.graph import router as graph_router
from api.kg_management import router as kg_management_router
from api.kg_health import router as kg_health_router
from api.kg_error_handlers import register_exception_handlers

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Knowledge Graph Service...")
    
    try:
        connected = await neo4j_client.connect()
        if connected:
            logger.info(f"Neo4j connection established at {kg_settings.NEO4J_URI}")
        else:
            logger.warning("Failed to connect to Neo4j on startup")
    except Exception as e:
        logger.error(f"Neo4j connection error: {e}")
    
    if kg_settings.LLM_API_KEY:
        logger.info(f"LLM service configured with model: {kg_settings.LLM_MODEL_NAME}")
    else:
        logger.warning("LLM API key not configured, extraction features may be limited")
    
    yield
    
    logger.info("Shutting down Knowledge Graph Service...")
    try:
        await neo4j_client.close()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j connection: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Knowledge Graph Service",
        version="1.0.0",
        description="Knowledge Graph Service for GraphRAG - Entity Management, Relation Extraction, and Graph Traversal",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    register_exception_handlers(app)
    
    app.include_router(entity_router)
    app.include_router(relation_router)
    app.include_router(graph_router)
    app.include_router(kg_management_router)
    app.include_router(kg_health_router)
    
    @app.get("/")
    async def root():
        return {
            "name": "Knowledge Graph Service",
            "version": "1.0.0",
            "status": "running",
            "features": [
                "entity_management",
                "relation_management",
                "graph_traversal",
                "knowledge_extraction",
                "graph_query"
            ],
            "endpoints": {
                "entities": "/api/v1/kg/entities",
                "relations": "/api/v1/kg/relations",
                "graph": "/api/v1/kg/graph",
                "management": "/api/v1/kg/management",
                "health": "/health/kg"
            }
        }
    
    @app.get("/info")
    async def info():
        return {
            "service": "knowledge-graph",
            "version": "1.0.0",
            "config": {
                "neo4j_uri": kg_settings.NEO4J_URI,
                "neo4j_database": kg_settings.NEO4J_DATABASE,
                "llm_model": kg_settings.LLM_MODEL_NAME,
                "entity_types": kg_settings.ENTITY_TYPES,
                "relation_types": kg_settings.RELATION_TYPES,
                "max_hops": kg_settings.MAX_HOPS,
                "default_limit": kg_settings.DEFAULT_LIMIT
            }
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.kg_main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
