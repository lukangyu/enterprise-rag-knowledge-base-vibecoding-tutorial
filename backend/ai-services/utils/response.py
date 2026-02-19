from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    
    class Config:
        from_attributes = True


class PagedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    total_pages: int
    
    class Config:
        from_attributes = True


def success(data: Any = None, message: str = "success") -> Dict[str, Any]:
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error(message: str, code: int = 500, data: Any = None) -> Dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data
    }


def created(data: Any = None, message: str = "Created successfully") -> Dict[str, Any]:
    return {
        "code": 201,
        "message": message,
        "data": data
    }


def no_content(message: str = "No content") -> Dict[str, Any]:
    return {
        "code": 204,
        "message": message,
        "data": None
    }


def bad_request(message: str, data: Any = None) -> Dict[str, Any]:
    return {
        "code": 400,
        "message": message,
        "data": data
    }


def not_found(message: str = "Resource not found", data: Any = None) -> Dict[str, Any]:
    return {
        "code": 404,
        "message": message,
        "data": data
    }


def unauthorized(message: str = "Unauthorized") -> Dict[str, Any]:
    return {
        "code": 401,
        "message": message,
        "data": None
    }


def forbidden(message: str = "Forbidden") -> Dict[str, Any]:
    return {
        "code": 403,
        "message": message,
        "data": None
    }


def paged(
    items: List[Any],
    total: int,
    page: int,
    size: int
) -> Dict[str, Any]:
    total_pages = (total + size - 1) // size if size > 0 else 0
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": items,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages
            }
        }
    }
