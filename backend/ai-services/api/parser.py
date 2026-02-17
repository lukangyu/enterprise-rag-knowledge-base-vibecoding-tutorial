from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import tempfile
import time
import logging
import os

from models.parser_models import ParseResponse, FileType, StructureItem
from services.parser import PDFParser, WordParser, MarkdownParser, TextCleaner

router = APIRouter(prefix="/api/v1", tags=["parser"])
logger = logging.getLogger(__name__)


@router.post("/parse", response_model=ParseResponse)
async def parse_document(
    file: UploadFile = File(...),
    file_type: Optional[FileType] = None
):
    """解析上传的文档"""
    start_time = time.time()

    detected_type = file_type or detect_file_type(file.filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{detected_type.value}") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if detected_type == FileType.PDF:
            parser = PDFParser()
            result = parser.parse(tmp_path)
        elif detected_type == FileType.DOCX:
            parser = WordParser()
            result = parser.parse(tmp_path)
        elif detected_type == FileType.MD:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            parser = MarkdownParser()
            result = parser.parse(content)
        else:
            raise HTTPException(400, f"Unsupported file type: {detected_type}")

        result.content = TextCleaner.normalize(result.content)

        parse_time = (time.time() - start_time) * 1000

        return ParseResponse(
            content=result.content,
            metadata=result.metadata,
            structure=[StructureItem(**s) for s in result.structure],
            page_count=result.page_count,
            content_hash=result.content_hash,
            parse_time_ms=parse_time
        )
    finally:
        os.unlink(tmp_path)


def detect_file_type(filename: str) -> FileType:
    ext = filename.lower().split('.')[-1]
    mapping = {
        'pdf': FileType.PDF,
        'docx': FileType.DOCX,
        'md': FileType.MD,
        'txt': FileType.TXT
    }
    return mapping.get(ext, FileType.TXT)
