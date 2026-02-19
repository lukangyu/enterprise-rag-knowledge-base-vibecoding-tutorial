from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import logging
import time
from contextlib import asynccontextmanager

from config.settings import settings
from config.logging import setup_logging
from config.database import milvus_connection
from api import parser, chunker, embedding
from api.search import router as search_router
from api.health import router as health_router
from api.entity import router as entity_router
from api.qa import router as qa_router
from api.system.config import router as config_router
from api.system.status import router as status_router
from api.system.audit import router as audit_router
from api.system.statistics import router as statistics_router
from api.error_handlers import (
    ai_service_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from exceptions import AIServiceException
from services.embedding.es_client import es_client

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Services...")
    
    try:
        milvus_connection.connect()
        logger.info("Milvus connection established")
    except Exception as e:
        logger.warning(f"Failed to connect to Milvus: {e}")

    try:
        es_client.create_index()
        logger.info("Elasticsearch connection established")
    except Exception as e:
        logger.warning(f"Failed to connect to Elasticsearch: {e}")

    yield

    logger.info("Shutting down AI Services...")
    milvus_connection.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Services for GraphRAG - Document Parsing, Chunking, Embedding, and Hybrid Search",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AIServiceException, ai_service_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(parser.router)
app.include_router(chunker.router)
app.include_router(embedding.router)
app.include_router(search_router)
app.include_router(health_router)
app.include_router(entity_router)
app.include_router(qa_router)
app.include_router(config_router)
app.include_router(status_router)
app.include_router(audit_router)
app.include_router(statistics_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "features": ["parsing", "chunking", "embedding", "hybrid_search", "graph_traversal", "qa", "streaming"]
    }
