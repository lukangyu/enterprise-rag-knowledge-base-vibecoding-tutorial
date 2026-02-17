from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    MD = "md"
    TXT = "txt"


class ParseRequest(BaseModel):
    file_type: Optional[FileType] = None
    options: Optional[Dict[str, Any]] = None


class StructureItem(BaseModel):
    type: str
    text: str
    level: Optional[int] = None
    page: Optional[int] = None


class ParseResponse(BaseModel):
    content: str
    metadata: Dict[str, Any]
    structure: List[StructureItem]
    page_count: int
    content_hash: str
    parse_time_ms: float
