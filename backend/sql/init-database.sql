-- GraphRAG Database Initialization Script
-- Version: 1.0.0
-- Database: PostgreSQL 15+

-- Create database (run as superuser)
-- CREATE DATABASE graphrag WITH ENCODING='UTF8';

-- Connect to graphrag database
-- \c graphrag

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema
CREATE SCHEMA IF NOT EXISTS graphrag;

-- Set search path
SET search_path TO graphrag, public;

-- ============================================================================
-- User Management Tables
-- ============================================================================

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    real_name VARCHAR(50),
    avatar VARCHAR(255),
    gender SMALLINT DEFAULT 0,
    status SMALLINT DEFAULT 0,
    deleted SMALLINT DEFAULT 0,
    last_login_time TIMESTAMP,
    last_login_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    updated_by BIGINT
);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.id IS '用户ID';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.password IS '密码(BCrypt加密)';
COMMENT ON COLUMN users.email IS '邮箱';
COMMENT ON COLUMN users.phone IS '手机号';
COMMENT ON COLUMN users.real_name IS '真实姓名';
COMMENT ON COLUMN users.avatar IS '头像URL';
COMMENT ON COLUMN users.gender IS '性别:0-未知,1-男,2-女';
COMMENT ON COLUMN users.status IS '状态:0-正常,1-禁用';
COMMENT ON COLUMN users.deleted IS '删除标记:0-正常,1-已删除';

CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    role_code VARCHAR(50) NOT NULL UNIQUE,
    role_name VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    status SMALLINT DEFAULT 0,
    deleted SMALLINT DEFAULT 0,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    updated_by BIGINT
);

COMMENT ON TABLE roles IS '角色表';
COMMENT ON COLUMN roles.role_code IS '角色编码';
COMMENT ON COLUMN roles.role_name IS '角色名称';
COMMENT ON COLUMN roles.status IS '状态:0-正常,1-禁用';

CREATE TABLE permissions (
    id BIGSERIAL PRIMARY KEY,
    permission_code VARCHAR(100) NOT NULL UNIQUE,
    permission_name VARCHAR(100) NOT NULL,
    resource_type VARCHAR(20) NOT NULL,
    resource_path VARCHAR(255),
    parent_id BIGINT DEFAULT 0,
    description VARCHAR(255),
    status SMALLINT DEFAULT 0,
    deleted SMALLINT DEFAULT 0,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE permissions IS '权限表';
COMMENT ON COLUMN permissions.permission_code IS '权限编码';
COMMENT ON COLUMN permissions.permission_name IS '权限名称';
COMMENT ON COLUMN permissions.resource_type IS '资源类型:menu-button-api';
COMMENT ON COLUMN permissions.resource_path IS '资源路径';
COMMENT ON COLUMN permissions.parent_id IS '父权限ID';

CREATE TABLE user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);

COMMENT ON TABLE user_roles IS '用户角色关联表';

CREATE TABLE role_permissions (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);

COMMENT ON TABLE role_permissions IS '角色权限关联表';

-- ============================================================================
-- Document Management Tables
-- ============================================================================

CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    doc_id VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255),
    file_path VARCHAR(1000),
    file_size BIGINT,
    file_type VARCHAR(20),
    mime_type VARCHAR(100),
    storage_type VARCHAR(20) DEFAULT 'minio',
    checksum VARCHAR(64),
    status SMALLINT DEFAULT 0,
    parse_status SMALLINT DEFAULT 0,
    chunk_count INT DEFAULT 0,
    entity_count INT DEFAULT 0,
    relation_count INT DEFAULT 0,
    error_message TEXT,
    metadata JSONB,
    owner_id BIGINT,
    department_id BIGINT,
    access_level SMALLINT DEFAULT 0,
    deleted SMALLINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    updated_by BIGINT
);

COMMENT ON TABLE documents IS '文档表';
COMMENT ON COLUMN documents.doc_id IS '文档唯一标识';
COMMENT ON COLUMN documents.status IS '状态:0-待处理,1-处理中,2-已完成,3-失败';
COMMENT ON COLUMN documents.parse_status IS '解析状态:0-待解析,1-解析中,2-已解析,3-解析失败';
COMMENT ON COLUMN documents.storage_type IS '存储类型:local-minio';
COMMENT ON COLUMN documents.access_level IS '访问级别:0-私有,1-部门,2-公开';

CREATE INDEX idx_documents_owner_id ON documents(owner_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);

CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    chunk_id VARCHAR(64) NOT NULL UNIQUE,
    doc_id VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    position INT NOT NULL,
    start_offset INT,
    end_offset INT,
    token_count INT,
    embedding_id VARCHAR(64),
    embedding_status SMALLINT DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE document_chunks IS '文档片段表';
COMMENT ON COLUMN document_chunks.chunk_id IS '片段唯一标识';
COMMENT ON COLUMN document_chunks.position IS '片段在文档中的位置';
COMMENT ON COLUMN document_chunks.embedding_status IS '向量化状态:0-待处理,1-处理中,2-已完成,3-失败';

CREATE INDEX idx_document_chunks_doc_id ON document_chunks(doc_id);
CREATE INDEX idx_document_chunks_embedding_status ON document_chunks(embedding_status);

-- ============================================================================
-- Knowledge Graph Tables
-- ============================================================================

CREATE TABLE entities (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(64) NOT NULL UNIQUE,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    description TEXT,
    alias TEXT[],
    confidence DECIMAL(5,4) DEFAULT 1.0,
    source_doc_id VARCHAR(64),
    source_chunk_id VARCHAR(64),
    properties JSONB,
    embedding_id VARCHAR(64),
    status SMALLINT DEFAULT 0,
    deleted SMALLINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE entities IS '实体表';
COMMENT ON COLUMN entities.entity_type IS '实体类型:Person-Organization-Location-Product-Event-Concept';
COMMENT ON COLUMN entities.confidence IS '置信度(0-1)';
COMMENT ON COLUMN entities.status IS '状态:0-正常,1-合并,2-删除';

CREATE INDEX idx_entities_entity_type ON entities(entity_type);
CREATE INDEX idx_entities_entity_name ON entities(entity_name);
CREATE INDEX idx_entities_source_doc_id ON entities(source_doc_id);

CREATE TABLE relations (
    id BIGSERIAL PRIMARY KEY,
    relation_id VARCHAR(64) NOT NULL UNIQUE,
    head_entity_id VARCHAR(64) NOT NULL,
    tail_entity_id VARCHAR(64) NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    evidence TEXT,
    confidence DECIMAL(5,4) DEFAULT 1.0,
    source_doc_id VARCHAR(64),
    source_chunk_id VARCHAR(64),
    properties JSONB,
    status SMALLINT DEFAULT 0,
    deleted SMALLINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE relations IS '关系表';
COMMENT ON COLUMN relations.relation_type IS '关系类型:BELONGS_TO-CONTAINS-LOCATED_AT-CREATED_BY-AFFECTS-DEPENDS_ON';
COMMENT ON COLUMN relations.evidence IS '原文证据';
COMMENT ON COLUMN relations.confidence IS '置信度(0-1)';

CREATE INDEX idx_relations_head_entity_id ON relations(head_entity_id);
CREATE INDEX idx_relations_tail_entity_id ON relations(tail_entity_id);
CREATE INDEX idx_relations_relation_type ON relations(relation_type);
CREATE INDEX idx_relations_source_doc_id ON relations(source_doc_id);

-- ============================================================================
-- Chat & Search Tables
-- ============================================================================

CREATE TABLE chat_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    title VARCHAR(255),
    status SMALLINT DEFAULT 0,
    message_count INT DEFAULT 0,
    last_message_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chat_sessions IS '对话会话表';
COMMENT ON COLUMN chat_sessions.status IS '状态:0-活跃,1-已关闭';

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);

CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(64) NOT NULL UNIQUE,
    session_id VARCHAR(64) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    tokens INT,
    model VARCHAR(50),
    retrieval_sources JSONB,
    evidence_chain JSONB,
    feedback SMALLINT,
    feedback_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chat_messages IS '对话消息表';
COMMENT ON COLUMN chat_messages.role IS '角色:user-assistant-system';
COMMENT ON COLUMN chat_messages.retrieval_sources IS '检索来源列表';
COMMENT ON COLUMN chat_messages.evidence_chain IS '证据链';
COMMENT ON COLUMN chat_messages.feedback IS '反馈:1-好评,-1-差评';

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- ============================================================================
-- System Tables
-- ============================================================================

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    log_id VARCHAR(64) NOT NULL UNIQUE,
    user_id BIGINT,
    username VARCHAR(50),
    operation VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(64),
    request_method VARCHAR(10),
    request_url VARCHAR(500),
    request_params TEXT,
    response_code INT,
    response_time INT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    status SMALLINT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE audit_logs IS '审计日志表';
COMMENT ON COLUMN audit_logs.operation IS '操作类型';
COMMENT ON COLUMN audit_logs.status IS '状态:0-成功,1-失败';

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

CREATE TABLE system_configs (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string',
    description VARCHAR(255),
    status SMALLINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT
);

COMMENT ON TABLE system_configs IS '系统配置表';
COMMENT ON COLUMN system_configs.config_type IS '配置类型:string-number-boolean-json';

CREATE TABLE task_records (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL UNIQUE,
    task_type VARCHAR(50) NOT NULL,
    task_name VARCHAR(255),
    status SMALLINT DEFAULT 0,
    progress INT DEFAULT 0,
    total_count INT,
    success_count INT,
    fail_count INT,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE task_records IS '任务记录表';
COMMENT ON COLUMN task_records.task_type IS '任务类型:parse-embed-extract-relation';
COMMENT ON COLUMN task_records.status IS '状态:0-待执行,1-执行中,2-已完成,3-失败,4-已取消';

CREATE INDEX idx_task_records_task_type ON task_records(task_type);
CREATE INDEX idx_task_records_status ON task_records(status);
CREATE INDEX idx_task_records_created_at ON task_records(created_at);

-- ============================================================================
-- Initial Data
-- ============================================================================

-- Insert default roles
INSERT INTO roles (role_code, role_name, description, sort_order) VALUES
('super_admin', '超级管理员', '系统最高权限角色', 1),
('admin', '管理员', '系统管理员角色', 2),
('user', '普通用户', '普通用户角色', 3);

-- Insert default permissions
INSERT INTO permissions (permission_code, permission_name, resource_type, resource_path, parent_id, sort_order) VALUES
('system', '系统管理', 'menu', '/system', 0, 1),
('system:user', '用户管理', 'menu', '/system/user', 1, 1),
('system:user:list', '用户列表', 'button', 'system:user:list', 2, 1),
('system:user:add', '新增用户', 'button', 'system:user:add', 2, 2),
('system:user:edit', '编辑用户', 'button', 'system:user:edit', 2, 3),
('system:user:delete', '删除用户', 'button', 'system:user:delete', 2, 4),
('system:role', '角色管理', 'menu', '/system/role', 1, 2),
('system:permission', '权限管理', 'menu', '/system/permission', 1, 3),
('document', '文档管理', 'menu', '/document', 0, 2),
('document:list', '文档列表', 'menu', '/document/list', 9, 1),
('document:upload', '上传文档', 'button', 'document:upload', 10, 1),
('document:delete', '删除文档', 'button', 'document:delete', 10, 2),
('knowledge', '知识图谱', 'menu', '/knowledge', 0, 3),
('knowledge:graph', '图谱可视化', 'menu', '/knowledge/graph', 13, 1),
('chat', '智能问答', 'menu', '/chat', 0, 4),
('chat:index', '问答界面', 'menu', '/chat/index', 17, 1);

-- Assign all permissions to super_admin role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions;

-- Assign basic permissions to user role
INSERT INTO role_permissions (role_id, permission_id)
SELECT 3, id FROM permissions WHERE permission_code IN (
    'document', 'document:list', 'document:upload',
    'knowledge', 'knowledge:graph',
    'chat', 'chat:index'
);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, password, email, real_name, status) VALUES
('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5EH', 'admin@graphrag.com', '系统管理员', 0);

-- Assign super_admin role to admin user
INSERT INTO user_roles (user_id, role_id) VALUES (1, 1);

-- Insert default system configs
INSERT INTO system_configs (config_key, config_value, config_type, description) VALUES
('system.name', 'GraphRAG知识库系统', 'string', '系统名称'),
('system.logo', '/logo.png', 'string', '系统Logo'),
('upload.maxSize', '104857600', 'number', '上传文件最大大小(字节)'),
('upload.allowedTypes', 'pdf,doc,docx,txt,md', 'string', '允许上传的文件类型'),
('chat.maxHistory', '100', 'number', '对话历史最大保存条数'),
('embedding.dimension', '1024', 'number', '向量维度'),
('embedding.model', 'qwen-embedding', 'string', '嵌入模型'),
('llm.model', 'qwen2.5-max', 'string', '大语言模型'),
('rerank.model', 'qwen-reranker', 'string', '重排序模型');

-- ============================================================================
-- Create Views
-- ============================================================================

CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id AS user_id,
    u.username,
    p.permission_code,
    p.permission_name,
    p.resource_type,
    p.resource_path
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role_permissions rp ON ur.role_id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.deleted = 0 AND u.status = 0;

COMMENT ON VIEW v_user_permissions IS '用户权限视图';

-- ============================================================================
-- Create Functions
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'graphrag' 
        AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trigger_update_%s ON graphrag.%s;
            CREATE TRIGGER trigger_update_%s
            BEFORE UPDATE ON graphrag.%s
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END $$;

-- Grant permissions
-- GRANT ALL PRIVILEGES ON SCHEMA graphrag TO graphrag_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA graphrag TO graphrag_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA graphrag TO graphrag_user;

-- Complete
SELECT 'Database initialization completed successfully!' AS status;
