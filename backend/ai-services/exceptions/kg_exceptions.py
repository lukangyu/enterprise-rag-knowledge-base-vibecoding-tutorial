from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class KGBaseException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "KG_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class EntityNotFoundException(KGBaseException):
    def __init__(self, entity_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Entity not found: {entity_id}",
            code="ENTITY_NOT_FOUND",
            details={"entity_id": entity_id, **(details or {})}
        )


class RelationNotFoundException(KGBaseException):
    def __init__(self, relation_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Relation not found: {relation_id}",
            code="RELATION_NOT_FOUND",
            details={"relation_id": relation_id, **(details or {})}
        )


class GraphQueryException(KGBaseException):
    def __init__(self, message: str, query: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="GRAPH_QUERY_ERROR",
            details={"query": query, **(details or {})}
        )


class LLMServiceException(KGBaseException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_SERVICE_ERROR",
            details=details
        )


class Neo4jConnectionException(KGBaseException):
    def __init__(self, message: str = "Failed to connect to Neo4j", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NEO4J_CONNECTION_ERROR",
            details=details
        )


class EntityValidationException(KGBaseException):
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ENTITY_VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )


class RelationValidationException(KGBaseException):
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RELATION_VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )


class DuplicateEntityException(KGBaseException):
    def __init__(self, entity_name: str, entity_type: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Entity already exists: {entity_name} ({entity_type})",
            code="DUPLICATE_ENTITY",
            details={"entity_name": entity_name, "entity_type": entity_type, **(details or {})}
        )


class ExtractionException(KGBaseException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="EXTRACTION_ERROR",
            details=details
        )
