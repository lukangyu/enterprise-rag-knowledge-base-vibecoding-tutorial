from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
from typing import Dict, Any

from exceptions.kg_exceptions import KGBaseException
from exceptions import AIServiceException

logger = logging.getLogger(__name__)


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    details: Dict[str, Any] = None,
    errors: list = None
) -> JSONResponse:
    content = {
        "code": code,
        "message": message,
        "timestamp": time.time()
    }
    
    if details:
        content["details"] = details
    
    if errors:
        content["errors"] = errors
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def handle_kg_exception(request: Request, exc: KGBaseException) -> JSONResponse:
    logger.error(f"KG Exception: {exc.code} - {exc.message}", extra={"details": exc.details})
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if exc.code == "ENTITY_NOT_FOUND":
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.code == "RELATION_NOT_FOUND":
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.code == "ENTITY_VALIDATION_ERROR":
        status_code = status.HTTP_400_BAD_REQUEST
    elif exc.code == "RELATION_VALIDATION_ERROR":
        status_code = status.HTTP_400_BAD_REQUEST
    elif exc.code == "DUPLICATE_ENTITY":
        status_code = status.HTTP_409_CONFLICT
    elif exc.code == "NEO4J_CONNECTION_ERROR":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif exc.code == "LLM_SERVICE_ERROR":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=status_code,
        details=exc.details
    )


async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error.get("type", "validation_error")
        })
    
    logger.warning(f"Validation error: {errors}")
    
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Parameter validation failed",
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=errors
    )


async def handle_ai_service_exception(request: Request, exc: AIServiceException) -> JSONResponse:
    logger.error(f"AI Service Exception: {exc.code} - {exc.message}")
    
    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unexpected error: {str(exc)}")
    
    return create_error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    from fastapi import HTTPException
    
    if isinstance(exc, HTTPException):
        logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        
        return create_error_response(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code
        )
    
    return await handle_generic_exception(request, exc)


def register_exception_handlers(app):
    from fastapi import HTTPException
    from exceptions.kg_exceptions import KGBaseException
    from exceptions import AIServiceException
    
    app.add_exception_handler(KGBaseException, handle_kg_exception)
    app.add_exception_handler(AIServiceException, handle_ai_service_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_generic_exception)
    
    logger.info("Exception handlers registered")
