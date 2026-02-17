from fastapi import HTTPException, status


class AIServiceException(Exception):
    """AI服务基础异常"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ParseException(AIServiceException):
    """文档解析异常"""
    def __init__(self, message: str):
        super().__init__(message, "PARSE_ERROR")


class ChunkException(AIServiceException):
    """文档分块异常"""
    def __init__(self, message: str):
        super().__init__(message, "CHUNK_ERROR")


class EmbeddingException(AIServiceException):
    """向量化异常"""
    def __init__(self, message: str):
        super().__init__(message, "EMBEDDING_ERROR")


class MilvusException(AIServiceException):
    """Milvus数据库异常"""
    def __init__(self, message: str):
        super().__init__(message, "MILVUS_ERROR")


class QwenAPIException(AIServiceException):
    """Qwen API异常"""
    def __init__(self, message: str):
        super().__init__(message, "QWEN_API_ERROR")
