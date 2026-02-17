-- Document Management Tables
-- Version: 1.0.0
-- Database: PostgreSQL 15+

SET search_path TO graphrag, public;

-- ============================================================================
-- Documents Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source VARCHAR(255),
    doc_type VARCHAR(50),
    file_path VARCHAR(1000),
    file_size BIGINT,
    content_hash VARCHAR(64),
    status VARCHAR(20) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    updated_by VARCHAR(64)
);

COMMENT ON TABLE documents IS '文档表';
COMMENT ON COLUMN documents.id IS '文档ID';
COMMENT ON COLUMN documents.title IS '文档标题';
COMMENT ON COLUMN documents.source IS '文档来源';
COMMENT ON COLUMN documents.doc_type IS '文档类型';
COMMENT ON COLUMN documents.file_path IS 'MinIO存储路径';
COMMENT ON COLUMN documents.file_size IS '文件大小(字节)';
COMMENT ON COLUMN documents.content_hash IS '内容哈希值';
COMMENT ON COLUMN documents.status IS '状态:pending-processing-completed-failed';
COMMENT ON COLUMN documents.metadata IS 'JSON元数据';

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);

-- ============================================================================
-- Document Chunks Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(64) PRIMARY KEY,
    doc_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    position INT NOT NULL,
    token_count INT,
    embedding_id VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE document_chunks IS '文档片段表';
COMMENT ON COLUMN document_chunks.id IS '片段ID';
COMMENT ON COLUMN document_chunks.doc_id IS '文档ID';
COMMENT ON COLUMN document_chunks.content IS '片段内容';
COMMENT ON COLUMN document_chunks.position IS '片段在文档中的位置';
COMMENT ON COLUMN document_chunks.token_count IS 'token数量';
COMMENT ON COLUMN document_chunks.embedding_id IS '向量ID';
COMMENT ON COLUMN document_chunks.metadata IS 'JSON元数据';

CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_id ON document_chunks(embedding_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_position ON document_chunks(doc_id, position);

-- Add foreign key constraint
ALTER TABLE document_chunks 
ADD CONSTRAINT fk_document_chunks_doc_id 
FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE;

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS trigger_update_documents ON documents;
CREATE TRIGGER trigger_update_documents
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
