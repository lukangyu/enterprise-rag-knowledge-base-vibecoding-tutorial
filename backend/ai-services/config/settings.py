from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    APP_NAME: str = "AI Services"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "document_vectors"

    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ES_INDEX: str = "doc_index"
    ES_USERNAME: Optional[str] = None
    ES_PASSWORD: Optional[str] = None
    ES_SCHEME: str = "http"

    QWEN_API_KEY: str = ""
    QWEN_API_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
    QWEN_MODEL: str = "text-embedding-v2"
    EMBEDDING_DIMENSION: int = 1536

    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    SUPPORTED_FORMATS: List[str] = ["pdf", "docx", "md", "txt"]

    DEFAULT_CHUNK_SIZE: int = 512
    DEFAULT_OVERLAP_RATE: float = 0.1

    RRF_K: int = 60
    DEFAULT_TOP_K: int = 100

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
