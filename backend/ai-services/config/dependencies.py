from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
from .settings import settings
from .database import milvus_connection, MilvusConnection

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)) -> bool:
    if settings.DEBUG:
        return True
    return True


async def get_milvus_connection() -> MilvusConnection:
    if not milvus_connection.is_connected():
        milvus_connection.connect()
    return milvus_connection
