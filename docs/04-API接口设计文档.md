# 企业级GraphRAG知识库系统 - API接口设计文档

> 文档版本: v1.0  
> 创建日期: 2026-02-17  
> 文档状态: 正式版  
> 依据文档: 系统架构设计文档v2.0、技术选型文档v2.2  
> API规范: RESTful API + OpenAPI 3.0

---

## 目录

- [1. API概述](#1-api概述)
- [2. 通用规范](#2-通用规范)
- [3. 认证授权](#3-认证授权)
- [4. 文档管理API](#4-文档管理api)
- [5. 知识图谱API](#5-知识图谱api)
- [6. 检索服务API](#6-检索服务api)
- [7. 问答服务API](#7-问答服务api)
- [8. 用户管理API](#8-用户管理api)
- [9. 系统管理API](#9-系统管理api)
- [10. 异步任务API](#10-异步任务api)
- [11. WebSocket接口](#11-websocket接口)
- [12. 错误码定义](#12-错误码定义)
- [13. 接口限流策略](#13-接口限流策略)
- [14. 版本控制策略](#14-版本控制策略)

---

## 1. API概述

### 1.1 基本信息

| 项目 | 说明 |
|------|------|
| **API名称** | GraphRAG知识库系统API |
| **API版本** | v1.0 |
| **基础URL** | `https://api.example.com/v1` |
| **协议** | HTTPS |
| **数据格式** | JSON |
| **字符编码** | UTF-8 |
| **API风格** | RESTful |

### 1.2 服务端点

| 服务 | 端点 | 说明 |
|------|------|------|
| **API网关** | `https://api.example.com` | 统一入口 |
| **业务服务** | `https://api.example.com/v1` | Spring Boot服务 |
| **AI服务** | `https://ai.example.com/v1` | FastAPI GraphRAG服务 |
| **WebSocket** | `wss://ws.example.com/v1` | 流式通信 |

### 1.3 API模块架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API模块架构                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    API网关层 (APISIX)                        │  │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │  │
│   │  │ 路由转发  │ │ 认证鉴权  │ │ 限流熔断  │ │ 日志追踪  │   │  │
│   │  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    业务API模块                               │  │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │  │
│   │  │ 文档管理  │ │ 用户管理  │ │ 权限管理  │ │ 系统管理  │   │  │
│   │  │ /docs     │ │ /users    │ │ /auth     │ │ /system   │   │  │
│   │  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    AI服务API模块                             │  │
│   │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │  │
│   │  │ 知识图谱  │ │ 检索服务  │ │ 问答服务  │ │ 任务管理  │   │  │
│   │  │ /kg       │ │ /search   │ │ /chat     │ │ /tasks    │   │  │
│   │  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 通用规范

### 2.1 请求规范

#### 2.1.1 请求头

| 头字段 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `Authorization` | 是 | 认证令牌 | `Bearer eyJhbGciOiJIUzI1NiIs...` |
| `Content-Type` | 是 | 内容类型 | `application/json` |
| `Accept` | 否 | 接受类型 | `application/json` |
| `X-Request-ID` | 否 | 请求追踪ID | `req_abc123def456` |
| `X-Tenant-ID` | 否 | 租户ID（多租户场景） | `tenant_001` |
| `Accept-Language` | 否 | 语言偏好 | `zh-CN` |

#### 2.1.2 请求方法

| 方法 | 用途 | 幂等性 | 示例 |
|------|------|--------|------|
| `GET` | 查询资源 | 是 | 获取文档列表 |
| `POST` | 创建资源 | 否 | 上传文档 |
| `PUT` | 全量更新资源 | 是 | 更新文档信息 |
| `PATCH` | 部分更新资源 | 是 | 更新文档状态 |
| `DELETE` | 删除资源 | 是 | 删除文档 |

#### 2.1.3 查询参数规范

```
分页参数：
├── page: 页码（从1开始）
├── size: 每页数量（默认20，最大100）
├── sort: 排序字段
└── order: 排序方向（asc/desc）

过滤参数：
├── status: 状态过滤
├── type: 类型过滤
├── created_from: 创建时间起始
└── created_to: 创建时间结束

示例：
GET /api/v1/documents?page=1&size=20&sort=created_at&order=desc&status=published
```

### 2.2 响应规范

#### 2.2.1 统一响应格式

```json
{
    "code": 200,
    "message": "success",
    "data": {
    },
    "timestamp": "2026-02-17T10:30:00Z",
    "request_id": "req_abc123def456"
}
```

#### 2.2.2 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 业务状态码，200表示成功 |
| `message` | string | 响应消息描述 |
| `data` | object | 响应数据主体 |
| `timestamp` | string | 响应时间戳（ISO 8601格式） |
| `request_id` | string | 请求追踪ID |

#### 2.2.3 分页响应格式

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            { "id": "doc_001", "title": "文档1" },
            { "id": "doc_002", "title": "文档2" }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 100,
            "total_pages": 5
        }
    },
    "timestamp": "2026-02-17T10:30:00Z",
    "request_id": "req_abc123def456"
}
```

#### 2.2.4 HTTP状态码

| 状态码 | 说明 | 使用场景 |
|--------|------|---------|
| `200` | 成功 | 请求处理成功 |
| `201` | 已创建 | 资源创建成功 |
| `202` | 已接受 | 异步任务已接受 |
| `204` | 无内容 | 删除成功（无返回体） |
| `400` | 请求错误 | 参数校验失败 |
| `401` | 未认证 | 缺少或无效的认证信息 |
| `403` | 无权限 | 无访问权限 |
| `404` | 未找到 | 资源不存在 |
| `409` | 冲突 | 资源冲突（如重复创建） |
| `422` | 实体错误 | 语义错误 |
| `429` | 请求过多 | 触发限流 |
| `500` | 服务器错误 | 内部服务错误 |
| `502` | 网关错误 | 上游服务不可用 |
| `503` | 服务不可用 | 服务暂时不可用 |
| `504` | 网关超时 | 上游服务超时 |

### 2.3 数据类型定义

#### 2.3.1 基础数据类型

| 类型 | 格式 | 说明 | 示例 |
|------|------|------|------|
| `string` | - | 字符串 | `"hello"` |
| `integer` | int32 | 32位整数 | `100` |
| `long` | int64 | 64位整数 | `1708123456789` |
| `float` | float | 浮点数 | `3.14` |
| `boolean` | - | 布尔值 | `true` |
| `date` | date | 日期 | `"2026-02-17"` |
| `datetime` | date-time | 日期时间 | `"2026-02-17T10:30:00Z"` |
| `uuid` | uuid | UUID | `"550e8400-e29b-41d4-a716-446655440000"` |
| `object` | - | 对象 | `{}` |
| `array` | - | 数组 | `[]` |

#### 2.3.2 通用数据模型

**文档模型 (Document)**

```json
{
    "id": "doc_abc123",
    "title": "系统设计文档",
    "source": "内部文档",
    "doc_type": "pdf",
    "file_size": 1024000,
    "file_path": "/documents/2026/02/doc_abc123.pdf",
    "content_hash": "sha256:abc123...",
    "status": "published",
    "metadata": {
        "author": "张三",
        "department": "技术部",
        "tags": ["架构", "设计"],
        "access_level": "internal"
    },
    "created_at": "2026-02-17T10:00:00Z",
    "updated_at": "2026-02-17T10:30:00Z",
    "created_by": "user_001",
    "updated_by": "user_001"
}
```

**实体模型 (Entity)**

```json
{
    "id": "entity_001",
    "name": "张三",
    "type": "Person",
    "description": "技术部高级工程师",
    "alias": ["老张", "张工"],
    "properties": {
        "department": "技术部",
        "position": "高级工程师"
    },
    "confidence": 0.95,
    "source_doc_id": "doc_abc123",
    "created_at": "2026-02-17T10:00:00Z"
}
```

**关系模型 (Relation)**

```json
{
    "id": "rel_001",
    "head_entity_id": "entity_001",
    "head_entity_name": "张三",
    "relation_type": "BELONGS_TO",
    "tail_entity_id": "entity_002",
    "tail_entity_name": "技术部",
    "evidence": "张三是技术部的高级工程师",
    "confidence": 0.92,
    "source_chunk_id": "chunk_001",
    "created_at": "2026-02-17T10:00:00Z"
}
```

**证据链模型 (EvidenceChain)**

```json
{
    "chain_id": "chain_001",
    "entity_path": ["张三", "技术部", "A项目"],
    "relation_path": ["属于", "负责"],
    "source_docs": [
        {
            "doc_id": "doc_001",
            "title": "组织架构文档",
            "chunk": "张三隶属于技术部..."
        }
    ],
    "confidence": 0.88,
    "hop_count": 2
}
```

---

## 3. 认证授权

### 3.1 认证方式

#### 3.1.1 JWT认证

系统采用JWT（JSON Web Token）进行身份认证。

**获取Token**

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "password123"
}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "Bearer",
        "expires_in": 7200,
        "user": {
            "id": "user_001",
            "username": "admin",
            "name": "管理员",
            "roles": ["admin"]
        }
    }
}
```

**刷新Token**

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 3.1.2 API Key认证

用于服务间调用或第三方集成。

```http
GET /api/v1/documents
X-API-Key: sk_live_abc123def456
```

### 3.2 JWT Token结构

```json
{
    "header": {
        "alg": "HS256",
        "typ": "JWT"
    },
    "payload": {
        "sub": "user_001",
        "name": "管理员",
        "roles": ["admin"],
        "permissions": ["doc:read", "doc:write", "kg:manage"],
        "tenant_id": "tenant_001",
        "iat": 1708123456,
        "exp": 1708130656
    },
    "signature": "..."
}
```

### 3.3 权限控制

#### 3.3.1 RBAC权限模型

| 角色 | 权限说明 |
|------|---------|
| `super_admin` | 超级管理员，全部权限 |
| `admin` | 系统管理员，用户、文档、系统管理 |
| `knowledge_mgr` | 知识管理员，文档上传、知识管理 |
| `user` | 普通用户，问答、文档查看 |
| `guest` | 访客，仅问答 |

#### 3.3.2 权限标识

| 权限 | 说明 |
|------|------|
| `doc:create` | 创建文档 |
| `doc:read` | 查看文档 |
| `doc:update` | 更新文档 |
| `doc:delete` | 删除文档 |
| `kg:manage` | 管理知识图谱 |
| `kg:query` | 查询知识图谱 |
| `chat:query` | 问答查询 |
| `user:manage` | 用户管理 |
| `sys:config` | 系统配置 |

#### 3.3.3 权限检查响应

```json
{
    "code": 403,
    "message": "Permission denied: doc:delete",
    "data": {
        "required_permission": "doc:delete",
        "current_permissions": ["doc:read", "doc:update"]
    },
    "timestamp": "2026-02-17T10:30:00Z",
    "request_id": "req_abc123"
}
```

---

## 4. 文档管理API

### 4.1 文档上传

**接口说明**

上传文档到知识库，支持多种格式（PDF、Word、Markdown、TXT等）。

**请求**

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: (binary)
metadata: {
    "title": "系统设计文档",
    "category": "技术文档",
    "tags": ["架构", "设计"],
    "access_level": "internal",
    "description": "系统架构设计文档"
}
```

**参数说明**

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `file` | body | file | 是 | 文档文件（最大50MB） |
| `title` | body | string | 否 | 文档标题（默认使用文件名） |
| `category` | body | string | 否 | 文档分类 |
| `tags` | body | array | 否 | 标签列表 |
| `access_level` | body | string | 否 | 访问级别：public/internal/private |
| `description` | body | string | 否 | 文档描述 |

**响应**

```json
{
    "code": 202,
    "message": "Document uploaded, processing started",
    "data": {
        "doc_id": "doc_abc123",
        "title": "系统设计文档",
        "status": "pending",
        "task_id": "task_xyz789",
        "message": "文档已上传，正在处理中"
    },
    "timestamp": "2026-02-17T10:30:00Z",
    "request_id": "req_abc123"
}
```

**支持的文件格式**

| 格式 | 扩展名 | 最大大小 |
|------|--------|---------|
| PDF | .pdf | 50MB |
| Word | .doc, .docx | 50MB |
| Markdown | .md | 10MB |
| 文本 | .txt | 10MB |
| HTML | .html, .htm | 10MB |

### 4.2 获取文档列表

**请求**

```http
GET /api/v1/documents?page=1&size=20&status=published&sort=created_at&order=desc
Authorization: Bearer {token}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `page` | integer | 否 | 1 | 页码 |
| `size` | integer | 否 | 20 | 每页数量（最大100） |
| `status` | string | 否 | - | 状态过滤：pending/processing/published/failed |
| `doc_type` | string | 否 | - | 文档类型过滤 |
| `category` | string | 否 | - | 分类过滤 |
| `keyword` | string | 否 | - | 关键词搜索 |
| `created_from` | string | 否 | - | 创建时间起始 |
| `created_to` | string | 否 | - | 创建时间结束 |
| `sort` | string | 否 | created_at | 排序字段 |
| `order` | string | 否 | desc | 排序方向：asc/desc |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": "doc_abc123",
                "title": "系统设计文档",
                "doc_type": "pdf",
                "file_size": 1024000,
                "status": "published",
                "chunk_count": 156,
                "entity_count": 89,
                "metadata": {
                    "author": "张三",
                    "department": "技术部",
                    "tags": ["架构", "设计"]
                },
                "created_at": "2026-02-17T10:00:00Z",
                "updated_at": "2026-02-17T10:30:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 156,
            "total_pages": 8
        }
    }
}
```

### 4.3 获取文档详情

**请求**

```http
GET /api/v1/documents/{doc_id}
Authorization: Bearer {token}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `doc_id` | string | 是 | 文档ID |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": "doc_abc123",
        "title": "系统设计文档",
        "source": "内部文档",
        "doc_type": "pdf",
        "file_size": 1024000,
        "file_path": "/documents/2026/02/doc_abc123.pdf",
        "content_hash": "sha256:abc123...",
        "status": "published",
        "chunk_count": 156,
        "entity_count": 89,
        "relation_count": 234,
        "metadata": {
            "author": "张三",
            "department": "技术部",
            "tags": ["架构", "设计"],
            "access_level": "internal"
        },
        "processing_info": {
            "parse_time": 12.5,
            "chunk_time": 3.2,
            "embedding_time": 45.8,
            "kg_time": 78.3,
            "total_time": 139.8
        },
        "created_at": "2026-02-17T10:00:00Z",
        "updated_at": "2026-02-17T10:30:00Z",
        "created_by": "user_001"
    }
}
```

### 4.4 更新文档信息

**请求**

```http
PUT /api/v1/documents/{doc_id}
Content-Type: application/json
Authorization: Bearer {token}

{
    "title": "系统设计文档v2",
    "category": "技术文档",
    "tags": ["架构", "设计", "v2"],
    "access_level": "internal",
    "description": "更新后的系统架构设计文档"
}
```

**响应**

```json
{
    "code": 200,
    "message": "Document updated successfully",
    "data": {
        "id": "doc_abc123",
        "title": "系统设计文档v2",
        "updated_at": "2026-02-17T11:00:00Z"
    }
}
```

### 4.5 删除文档

**请求**

```http
DELETE /api/v1/documents/{doc_id}?force=false
Authorization: Bearer {token}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `force` | boolean | 否 | false | 是否强制删除（包括关联数据） |

**响应**

```json
{
    "code": 200,
    "message": "Document deleted successfully",
    "data": {
        "doc_id": "doc_abc123",
        "deleted_chunks": 156,
        "deleted_entities": 89,
        "deleted_relations": 234
    }
}
```

### 4.6 获取文档处理状态

**请求**

```http
GET /api/v1/documents/{doc_id}/status
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "doc_id": "doc_abc123",
        "status": "processing",
        "progress": 65,
        "current_stage": "entity_extraction",
        "stages": [
            {
                "name": "parse",
                "status": "completed",
                "progress": 100,
                "duration": 12.5
            },
            {
                "name": "chunk",
                "status": "completed",
                "progress": 100,
                "duration": 3.2
            },
            {
                "name": "embedding",
                "status": "completed",
                "progress": 100,
                "duration": 45.8
            },
            {
                "name": "entity_extraction",
                "status": "in_progress",
                "progress": 65,
                "duration": null
            },
            {
                "name": "relation_extraction",
                "status": "pending",
                "progress": 0,
                "duration": null
            },
            {
                "name": "graph_build",
                "status": "pending",
                "progress": 0,
                "duration": null
            }
        ],
        "error": null,
        "started_at": "2026-02-17T10:00:00Z",
        "estimated_completion": "2026-02-17T10:05:00Z"
    }
}
```

### 4.7 批量上传文档

**请求**

```http
POST /api/v1/documents/batch-upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

files: (binary)[] 
metadata: {
    "category": "技术文档",
    "access_level": "internal"
}
```

**响应**

```json
{
    "code": 202,
    "message": "Batch upload accepted",
    "data": {
        "batch_id": "batch_xyz789",
        "total_files": 10,
        "accepted_files": 10,
        "rejected_files": 0,
        "task_ids": [
            "task_001",
            "task_002",
            "task_003"
        ]
    }
}
```

### 4.8 重新处理文档

**请求**

```http
POST /api/v1/documents/{doc_id}/reprocess
Content-Type: application/json
Authorization: Bearer {token}

{
    "stages": ["entity_extraction", "relation_extraction", "graph_build"],
    "config": {
        "entity_types": ["Person", "Organization", "Project"],
        "relation_types": ["BELONGS_TO", "PARTICIPATES_IN"]
    }
}
```

**响应**

```json
{
    "code": 202,
    "message": "Reprocess task started",
    "data": {
        "doc_id": "doc_abc123",
        "task_id": "task_reprocess_001",
        "status": "pending"
    }
}
```

---

## 5. 知识图谱API

### 5.1 实体查询

**请求**

```http
GET /api/v1/kg/entities?type=Person&keyword=张&page=1&size=20
Authorization: Bearer {token}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `type` | string | 否 | - | 实体类型过滤 |
| `keyword` | string | 否 | - | 关键词搜索 |
| `source_doc_id` | string | 否 | - | 来源文档过滤 |
| `min_confidence` | number | 否 | 0 | 最小置信度（0-1） |
| `page` | integer | 否 | 1 | 页码 |
| `size` | integer | 否 | 20 | 每页数量 |
| `sort` | string | 否 | created_at | 排序字段 |
| `order` | string | 否 | desc | 排序方向 |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": "entity_001",
                "name": "张三",
                "type": "Person",
                "description": "技术部高级工程师",
                "alias": ["老张", "张工"],
                "properties": {
                    "department": "技术部",
                    "position": "高级工程师"
                },
                "confidence": 0.95,
                "relation_count": 12,
                "source_doc_count": 3,
                "created_at": "2026-02-17T10:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 45,
            "total_pages": 3
        }
    }
}
```

### 5.2 获取实体详情

**请求**

```http
GET /api/v1/kg/entities/{entity_id}
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": "entity_001",
        "name": "张三",
        "type": "Person",
        "description": "技术部高级工程师",
        "alias": ["老张", "张工"],
        "properties": {
            "department": "技术部",
            "position": "高级工程师",
            "email": "zhangsan@example.com"
        },
        "confidence": 0.95,
        "source_docs": [
            {
                "doc_id": "doc_001",
                "title": "组织架构文档",
                "chunk": "张三是技术部的高级工程师..."
            }
        ],
        "relations": {
            "outgoing": [
                {
                    "relation_type": "BELONGS_TO",
                    "target_entity": {
                        "id": "entity_002",
                        "name": "技术部",
                        "type": "Organization"
                    },
                    "confidence": 0.92
                }
            ],
            "incoming": [
                {
                    "relation_type": "MANAGES",
                    "source_entity": {
                        "id": "entity_003",
                        "name": "李四",
                        "type": "Person"
                    },
                    "confidence": 0.88
                }
            ]
        },
        "created_at": "2026-02-17T10:00:00Z",
        "updated_at": "2026-02-17T10:30:00Z"
    }
}
```

### 5.3 关系查询

**请求**

```http
GET /api/v1/kg/relations?relation_type=BELONGS_TO&page=1&size=20
Authorization: Bearer {token}
```

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `relation_type` | string | 否 | - | 关系类型过滤 |
| `head_entity_id` | string | 否 | - | 头实体ID |
| `tail_entity_id` | string | 否 | - | 尾实体ID |
| `source_doc_id` | string | 否 | - | 来源文档过滤 |
| `min_confidence` | number | 否 | 0 | 最小置信度 |
| `page` | integer | 否 | 1 | 页码 |
| `size` | integer | 否 | 20 | 每页数量 |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": "rel_001",
                "head_entity": {
                    "id": "entity_001",
                    "name": "张三",
                    "type": "Person"
                },
                "relation_type": "BELONGS_TO",
                "tail_entity": {
                    "id": "entity_002",
                    "name": "技术部",
                    "type": "Organization"
                },
                "evidence": "张三是技术部的高级工程师",
                "confidence": 0.92,
                "source_doc": {
                    "id": "doc_001",
                    "title": "组织架构文档"
                },
                "created_at": "2026-02-17T10:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 234,
            "total_pages": 12
        }
    }
}
```

### 5.4 图遍历查询

**请求**

```http
POST /api/v1/kg/traverse
Content-Type: application/json
Authorization: Bearer {token}

{
    "start_entity_id": "entity_001",
    "start_entity_name": "张三",
    "traversal_type": "bfs",
    "max_hops": 3,
    "relation_types": ["BELONGS_TO", "PARTICIPATES_IN", "MANAGES"],
    "entity_types": ["Person", "Organization", "Project"],
    "min_confidence": 0.7,
    "limit": 50,
    "return_paths": true
}
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `start_entity_id` | string | 否* | - | 起始实体ID |
| `start_entity_name` | string | 否* | - | 起始实体名称（与ID二选一） |
| `traversal_type` | string | 否 | bfs | 遍历类型：bfs/dfs/shortest |
| `max_hops` | integer | 否 | 2 | 最大跳数（1-5） |
| `relation_types` | array | 否 | [] | 关系类型过滤（空为全部） |
| `entity_types` | array | 否 | [] | 目标实体类型过滤 |
| `min_confidence` | number | 否 | 0.5 | 最小置信度 |
| `limit` | integer | 否 | 50 | 结果数量限制 |
| `return_paths` | boolean | 否 | true | 是否返回路径 |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "start_entity": {
            "id": "entity_001",
            "name": "张三",
            "type": "Person"
        },
        "paths": [
            {
                "path_id": "path_001",
                "entity_path": [
                    {"id": "entity_001", "name": "张三", "type": "Person"},
                    {"id": "entity_002", "name": "技术部", "type": "Organization"},
                    {"id": "entity_005", "name": "A项目", "type": "Project"}
                ],
                "relation_path": ["BELONGS_TO", "RESPONSIBLE_FOR"],
                "hop_count": 2,
                "confidence": 0.88,
                "evidence": [
                    "张三是技术部的高级工程师",
                    "技术部负责A项目的开发"
                ]
            }
        ],
        "related_entities": [
            {
                "id": "entity_002",
                "name": "技术部",
                "type": "Organization",
                "distance": 1,
                "relation_count": 15
            },
            {
                "id": "entity_005",
                "name": "A项目",
                "type": "Project",
                "distance": 2,
                "relation_count": 8
            }
        ],
        "total_paths": 12,
        "query_time_ms": 45
    }
}
```

### 5.5 路径查询

**请求**

```http
POST /api/v1/kg/path
Content-Type: application/json
Authorization: Bearer {token}

{
    "source_entity": "张三",
    "target_entity": "A项目",
    "max_hops": 4,
    "algorithm": "shortest",
    "min_confidence": 0.6,
    "limit": 10
}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "source_entity": {
            "id": "entity_001",
            "name": "张三",
            "type": "Person"
        },
        "target_entity": {
            "id": "entity_005",
            "name": "A项目",
            "type": "Project"
        },
        "paths": [
            {
                "path_id": "path_001",
                "entity_path": ["张三", "技术部", "A项目"],
                "relation_path": ["BELONGS_TO", "RESPONSIBLE_FOR"],
                "hop_count": 2,
                "confidence": 0.88,
                "total_confidence": 0.77
            },
            {
                "path_id": "path_002",
                "entity_path": ["张三", "B系统", "A项目"],
                "relation_path": ["CREATED", "DEPENDS_ON"],
                "hop_count": 2,
                "confidence": 0.75,
                "total_confidence": 0.56
            }
        ],
        "shortest_path": {
            "path_id": "path_001",
            "hop_count": 2
        },
        "query_time_ms": 32
    }
}
```

### 5.6 子图查询

**请求**

```http
POST /api/v1/kg/subgraph
Content-Type: application/json
Authorization: Bearer {token}

{
    "entity_ids": ["entity_001", "entity_002", "entity_005"],
    "include_relations": true,
    "relation_types": [],
    "max_depth": 2,
    "layout": "force"
}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "nodes": [
            {
                "id": "entity_001",
                "name": "张三",
                "type": "Person",
                "properties": {"department": "技术部"}
            },
            {
                "id": "entity_002",
                "name": "技术部",
                "type": "Organization",
                "properties": {}
            },
            {
                "id": "entity_005",
                "name": "A项目",
                "type": "Project",
                "properties": {}
            }
        ],
        "edges": [
            {
                "id": "rel_001",
                "source": "entity_001",
                "target": "entity_002",
                "relation_type": "BELONGS_TO",
                "confidence": 0.92
            },
            {
                "id": "rel_002",
                "source": "entity_002",
                "target": "entity_005",
                "relation_type": "RESPONSIBLE_FOR",
                "confidence": 0.88
            }
        ],
        "statistics": {
            "node_count": 3,
            "edge_count": 2,
            "density": 0.67
        }
    }
}
```

### 5.7 触发知识抽取

**请求**

```http
POST /api/v1/kg/extract
Content-Type: application/json
Authorization: Bearer {token}

{
    "doc_id": "doc_abc123",
    "chunk_ids": ["chunk_001", "chunk_002"],
    "config": {
        "entity_types": ["Person", "Organization", "Project", "Product"],
        "relation_types": ["BELONGS_TO", "PARTICIPATES_IN", "CREATED_BY", "DEPENDS_ON"],
        "min_confidence": 0.7,
        "deduplicate": true,
        "merge_existing": true
    }
}
```

**响应**

```json
{
    "code": 202,
    "message": "Knowledge extraction task started",
    "data": {
        "task_id": "task_kg_001",
        "doc_id": "doc_abc123",
        "status": "pending",
        "estimated_time": 120
    }
}
```

### 5.8 实体消歧

**请求**

```http
POST /api/v1/kg/entities/resolve
Content-Type: application/json
Authorization: Bearer {token}

{
    "entity_name": "张三",
    "context": "张三负责A项目的开发工作",
    "candidate_limit": 5
}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "query": "张三",
        "context": "张三负责A项目的开发工作",
        "candidates": [
            {
                "entity_id": "entity_001",
                "name": "张三",
                "type": "Person",
                "description": "技术部高级工程师",
                "confidence": 0.92,
                "match_reason": "与项目A相关联"
            },
            {
                "entity_id": "entity_010",
                "name": "张三",
                "type": "Person",
                "description": "产品部产品经理",
                "confidence": 0.35,
                "match_reason": "同名实体"
            }
        ],
        "best_match": {
            "entity_id": "entity_001",
            "confidence": 0.92
        }
    }
}
```

---

## 6. 检索服务API

### 6.1 向量检索

**请求**

```http
POST /api/v1/search/vector
Content-Type: application/json
Authorization: Bearer {token}

{
    "query": "张三参与了哪些项目",
    "top_k": 20,
    "threshold": 0.7,
    "filters": {
        "doc_type": ["pdf", "docx"],
        "category": "技术文档",
        "created_after": "2025-01-01"
    },
    "include_metadata": true,
    "include_content": true
}
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 查询文本 |
| `top_k` | integer | 否 | 10 | 返回数量（最大100） |
| `threshold` | number | 否 | 0.5 | 相似度阈值（0-1） |
| `filters` | object | 否 | {} | 过滤条件 |
| `include_metadata` | boolean | 否 | true | 是否包含元数据 |
| `include_content` | boolean | 否 | true | 是否包含内容 |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "query": "张三参与了哪些项目",
        "query_embedding_time_ms": 15,
        "results": [
            {
                "chunk_id": "chunk_001",
                "doc_id": "doc_001",
                "doc_title": "组织架构文档",
                "content": "张三是技术部的高级工程师，负责A项目的核心模块开发...",
                "score": 0.92,
                "metadata": {
                    "author": "李四",
                    "department": "技术部",
                    "page": 5
                }
            },
            {
                "chunk_id": "chunk_045",
                "doc_id": "doc_002",
                "doc_title": "项目人员分配表",
                "content": "项目组成员：张三（技术负责人）、李四（产品经理）...",
                "score": 0.88,
                "metadata": {
                    "author": "HR部门",
                    "department": "人力资源部"
                }
            }
        ],
        "total": 20,
        "search_time_ms": 45
    }
}
```

### 6.2 图遍历检索

**请求**

```http
POST /api/v1/search/graph
Content-Type: application/json
Authorization: Bearer {token}

{
    "query": "张三参与了哪些项目",
    "entities": ["张三"],
    "max_hops": 3,
    "relation_types": ["PARTICIPATES_IN", "BELONGS_TO", "RESPONSIBLE_FOR"],
    "target_entity_types": ["Project"],
    "min_confidence": 0.6,
    "limit": 20
}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "query": "张三参与了哪些项目",
        "linked_entities": [
            {
                "entity_id": "entity_001",
                "name": "张三",
                "type": "Person",
                "confidence": 0.95
            }
        ],
        "results": [
            {
                "entity": {
                    "id": "entity_005",
                    "name": "A项目",
                    "type": "Project",
                    "description": "企业级知识库系统"
                },
                "evidence_chains": [
                    {
                        "path": ["张三", "技术部", "A项目"],
                        "relations": ["BELONGS_TO", "RESPONSIBLE_FOR"],
                        "confidence": 0.88,
                        "source_chunks": [
                            {
                                "chunk_id": "chunk_001",
                                "content": "张三是技术部的高级工程师...",
                                "doc_title": "组织架构文档"
                            }
                        ]
                    }
                ],
                "score": 0.88
            }
        ],
        "total": 3,
        "search_time_ms": 78
    }
}
```

### 6.3 混合检索（GraphRAG核心）

**请求**

```http
POST /api/v1/search/hybrid
Content-Type: application/json
Authorization: Bearer {token}

{
    "query": "张三参与了哪些项目？这些项目的当前状态如何？",
    "options": {
        "vector_search": {
            "enabled": true,
            "top_k": 50,
            "threshold": 0.6
        },
        "graph_search": {
            "enabled": true,
            "max_hops": 3,
            "entity_types": ["Person", "Project", "Organization"],
            "min_confidence": 0.6
        },
        "fusion": {
            "strategy": "weighted",
            "vector_weight": 0.4,
            "graph_weight": 0.6
        },
        "rerank": {
            "enabled": true,
            "model": "qwen-reranker",
            "top_k": 10
        }
    },
    "filters": {
        "access_level": ["public", "internal"]
    },
    "return_evidence": true
}
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 查询文本 |
| `options.vector_search.enabled` | boolean | 否 | true | 是否启用向量检索 |
| `options.vector_search.top_k` | integer | 否 | 50 | 向量检索返回数量 |
| `options.vector_search.threshold` | number | 否 | 0.5 | 相似度阈值 |
| `options.graph_search.enabled` | boolean | 否 | true | 是否启用图遍历 |
| `options.graph_search.max_hops` | integer | 否 | 2 | 最大跳数 |
| `options.fusion.strategy` | string | 否 | weighted | 融合策略：weighted/rrf/max/multiply |
| `options.rerank.enabled` | boolean | 否 | true | 是否启用重排 |
| `options.rerank.model` | string | 否 | qwen-reranker | 重排模型 |
| `options.rerank.top_k` | integer | 否 | 10 | 重排后返回数量 |
| `return_evidence` | boolean | 否 | true | 是否返回证据链 |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "query": "张三参与了哪些项目？这些项目的当前状态如何？",
        "query_analysis": {
            "intent": "multi_hop_query",
            "entities": [
                {"name": "张三", "type": "Person", "confidence": 0.95}
            ],
            "expected_answer_type": "project_list_with_status"
        },
        "results": [
            {
                "rank": 1,
                "chunk_id": "chunk_001",
                "doc_id": "doc_001",
                "doc_title": "组织架构文档",
                "content": "张三是技术部的高级工程师，负责A项目的核心模块开发。A项目目前处于开发阶段，预计下月上线...",
                "vector_score": 0.92,
                "graph_score": 0.88,
                "rerank_score": 0.95,
                "final_score": 0.93,
                "evidence_chains": [
                    {
                        "chain_id": "chain_001",
                        "entity_path": ["张三", "技术部", "A项目"],
                        "relation_path": ["BELONGS_TO", "RESPONSIBLE_FOR"],
                        "confidence": 0.88,
                        "source_docs": [
                            {
                                "doc_id": "doc_001",
                                "title": "组织架构文档",
                                "chunk": "张三是技术部的高级工程师..."
                            }
                        ]
                    }
                ]
            }
        ],
        "search_metrics": {
            "vector_search_time_ms": 45,
            "graph_search_time_ms": 78,
            "fusion_time_ms": 5,
            "rerank_time_ms": 120,
            "total_time_ms": 248
        },
        "total": 10
    }
}
```

### 6.4 重排序

**请求**

```http
POST /api/v1/search/rerank
Content-Type: application/json
Authorization: Bearer {token}

{
    "query": "张三参与了哪些项目",
    "documents": [
        {
            "id": "doc_001",
            "content": "张三是技术部的高级工程师，负责A项目..."
        },
        {
            "id": "doc_002",
            "content": "李四负责B项目的开发工作..."
        }
    ],
    "model": "qwen-reranker",
    "top_k": 5,
    "return_scores": true
}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "query": "张三参与了哪些项目",
        "results": [
            {
                "id": "doc_001",
                "content": "张三是技术部的高级工程师，负责A项目...",
                "score": 0.95,
                "rank": 1
            },
            {
                "id": "doc_002",
                "content": "李四负责B项目的开发工作...",
                "score": 0.32,
                "rank": 2
            }
        ],
        "model": "qwen-reranker",
        "rerank_time_ms": 85
    }
}
```

### 6.5 查询建议

**请求**

```http
GET /api/v1/search/suggestions?query=张三&limit=5
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "query": "张三",
        "suggestions": [
            {
                "text": "张三参与了哪些项目",
                "type": "query",
                "score": 0.92
            },
            {
                "text": "张三的职位是什么",
                "type": "query",
                "score": 0.88
            },
            {
                "text": "张三 技术部",
                "type": "entity",
                "score": 0.85
            }
        ]
    }
}
```

---

## 7. 问答服务API

### 7.1 问答请求（同步）

**请求**

```http
POST /api/v1/chat/completions
Content-Type: application/json
Authorization: Bearer {token}

{
    "query": "张三参与了哪些项目？这些项目的当前状态如何？",
    "session_id": "session_abc123",
    "options": {
        "stream": false,
        "show_evidence": true,
        "show_references": true,
        "max_tokens": 2048,
        "temperature": 0.7,
        "search_options": {
            "vector_search": {
                "enabled": true,
                "top_k": 20
            },
            "graph_search": {
                "enabled": true,
                "max_hops": 3
            },
            "rerank": {
                "enabled": true,
                "top_k": 5
            }
        }
    },
    "context": {
        "user_id": "user_001",
        "department": "技术部"
    }
}
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | string | 是 | - | 用户问题 |
| `session_id` | string | 否 | 自动生成 | 会话ID |
| `options.stream` | boolean | 否 | false | 是否流式输出 |
| `options.show_evidence` | boolean | 否 | true | 是否显示证据链 |
| `options.show_references` | boolean | 否 | true | 是否显示引用 |
| `options.max_tokens` | integer | 否 | 2048 | 最大生成token数 |
| `options.temperature` | number | 否 | 0.7 | 生成温度（0-1） |
| `context` | object | 否 | {} | 上下文信息 |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "answer": "根据知识库记录，张三参与了以下项目：\n\n1. **A项目**（企业级知识库系统）\n   - 角色：核心开发负责人\n   - 状态：开发阶段，预计下月上线\n   - 关联：通过技术部负责该项目\n\n2. **B系统**（内部管理平台）\n   - 角色：架构设计\n   - 状态：已上线运行\n   - 关联：作为主要架构师参与设计\n\n以上信息来源于组织架构文档和项目人员分配表。",
        "session_id": "session_abc123",
        "message_id": "msg_xyz789",
        "references": [
            {
                "doc_id": "doc_001",
                "doc_title": "组织架构文档",
                "chunk": "张三是技术部的高级工程师，负责A项目的核心模块开发...",
                "relevance": 0.95
            },
            {
                "doc_id": "doc_002",
                "doc_title": "项目人员分配表",
                "chunk": "项目组成员：张三（技术负责人）...",
                "relevance": 0.88
            }
        ],
        "evidence_chains": [
            {
                "chain_id": "chain_001",
                "entity_path": ["张三", "技术部", "A项目"],
                "relation_path": ["BELONGS_TO", "RESPONSIBLE_FOR"],
                "confidence": 0.88,
                "visualization_url": "/api/v1/kg/visualize/chain_001"
            }
        ],
        "metadata": {
            "model": "qwen2.5-max",
            "search_time_ms": 248,
            "generation_time_ms": 1250,
            "total_time_ms": 1498,
            "tokens_used": {
                "prompt": 512,
                "completion": 256,
                "total": 768
            }
        }
    }
}
```

### 7.2 流式问答（SSE）

**请求**

```http
POST /api/v1/chat/stream
Content-Type: application/json
Authorization: Bearer {token}
Accept: text/event-stream

{
    "query": "张三参与了哪些项目？",
    "session_id": "session_abc123",
    "options": {
        "stream": true,
        "show_evidence": true,
        "max_tokens": 2048
    }
}
```

**响应（Server-Sent Events）**

```
event: search_start
data: {"status": "searching", "message": "正在检索相关知识..."}

event: search_result
data: {"found": 5, "sources": ["组织架构文档", "项目人员分配表"]}

event: evidence_chain
data: {"chain": {"path": ["张三", "技术部", "A项目"], "confidence": 0.88}}

event: generation_start
data: {"status": "generating", "message": "正在生成回答..."}

event: token
data: {"content": "根据"}

event: token
data: {"content": "知识库"}

event: token
data: {"content": "记录"}

event: token
data: {"content": "，"}

event: token
data: {"content": "张三"}

event: token
data: {"content": "参与"}

event: token
data: {"content": "了"}

event: token
data: {"content": "以下"}

event: token
data: {"content": "项目"}

event: token
data: {"content": "..."}

event: done
data: {
    "message_id": "msg_xyz789",
    "references": [...],
    "evidence_chains": [...],
    "metadata": {
        "total_time_ms": 1498,
        "tokens_used": 768
    }
}
```

### 7.3 获取对话历史

**请求**

```http
GET /api/v1/chat/history/{session_id}?limit=20
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "session_id": "session_abc123",
        "created_at": "2026-02-17T10:00:00Z",
        "messages": [
            {
                "id": "msg_001",
                "role": "user",
                "content": "张三参与了哪些项目？",
                "created_at": "2026-02-17T10:00:00Z"
            },
            {
                "id": "msg_002",
                "role": "assistant",
                "content": "根据知识库记录，张三参与了以下项目...",
                "references": [...],
                "created_at": "2026-02-17T10:00:05Z"
            }
        ],
        "total": 4
    }
}
```

### 7.4 创建会话

**请求**

```http
POST /api/v1/chat/sessions
Content-Type: application/json
Authorization: Bearer {token}

{
    "title": "关于张三的查询",
    "context": {
        "department": "技术部"
    }
}
```

**响应**

```json
{
    "code": 201,
    "message": "Session created successfully",
    "data": {
        "session_id": "session_xyz789",
        "title": "关于张三的查询",
        "created_at": "2026-02-17T10:30:00Z"
    }
}
```

### 7.5 删除会话

**请求**

```http
DELETE /api/v1/chat/sessions/{session_id}
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "Session deleted successfully",
    "data": {
        "session_id": "session_xyz789",
        "deleted_messages": 10
    }
}
```

### 7.6 提交反馈

**请求**

```http
POST /api/v1/chat/feedback
Content-Type: application/json
Authorization: Bearer {token}

{
    "message_id": "msg_xyz789",
    "rating": 5,
    "feedback_type": "helpful",
    "comment": "回答准确，证据链清晰",
    "details": {
        "accuracy": 5,
        "relevance": 5,
        "completeness": 4
    }
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message_id` | string | 是 | 消息ID |
| `rating` | integer | 是 | 评分（1-5） |
| `feedback_type` | string | 是 | 反馈类型：helpful/not_helpful/incorrect |
| `comment` | string | 否 | 评论内容 |
| `details` | object | 否 | 详细评分 |

**响应**

```json
{
    "code": 200,
    "message": "Feedback submitted successfully",
    "data": {
        "feedback_id": "fb_001",
        "message_id": "msg_xyz789",
        "created_at": "2026-02-17T10:35:00Z"
    }
}
```

---

## 8. 用户管理API

### 8.1 用户登录

**请求**

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "password123"
}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "Bearer",
        "expires_in": 7200,
        "user": {
            "id": "user_001",
            "username": "admin",
            "name": "管理员",
            "email": "admin@example.com",
            "roles": ["admin"],
            "permissions": ["doc:create", "doc:read", "doc:update", "doc:delete", "kg:manage"]
        }
    }
}
```

### 8.2 用户登出

**请求**

```http
POST /api/v1/auth/logout
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "Logout successful"
}
```

### 8.3 获取用户列表

**请求**

```http
GET /api/v1/users?page=1&size=20&status=active
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": "user_001",
                "username": "admin",
                "name": "管理员",
                "email": "admin@example.com",
                "phone": "138****1234",
                "department": "技术部",
                "roles": ["admin"],
                "status": "active",
                "last_login": "2026-02-17T09:00:00Z",
                "created_at": "2025-01-01T00:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 156,
            "total_pages": 8
        }
    }
}
```

### 8.4 创建用户

**请求**

```http
POST /api/v1/users
Content-Type: application/json
Authorization: Bearer {token}

{
    "username": "zhangsan",
    "password": "Password123!",
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "13812345678",
    "department": "技术部",
    "roles": ["user"],
    "status": "active"
}
```

**响应**

```json
{
    "code": 201,
    "message": "User created successfully",
    "data": {
        "id": "user_002",
        "username": "zhangsan",
        "name": "张三",
        "created_at": "2026-02-17T10:00:00Z"
    }
}
```

### 8.5 更新用户

**请求**

```http
PUT /api/v1/users/{user_id}
Content-Type: application/json
Authorization: Bearer {token}

{
    "name": "张三",
    "email": "zhangsan_new@example.com",
    "department": "产品部",
    "roles": ["knowledge_mgr"]
}
```

**响应**

```json
{
    "code": 200,
    "message": "User updated successfully",
    "data": {
        "id": "user_002",
        "updated_at": "2026-02-17T11:00:00Z"
    }
}
```

### 8.6 删除用户

**请求**

```http
DELETE /api/v1/users/{user_id}
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "User deleted successfully"
}
```

### 8.7 修改密码

**请求**

```http
POST /api/v1/users/{user_id}/change-password
Content-Type: application/json
Authorization: Bearer {token}

{
    "old_password": "OldPassword123!",
    "new_password": "NewPassword456!"
}
```

**响应**

```json
{
    "code": 200,
    "message": "Password changed successfully"
}
```

### 8.8 角色管理

**获取角色列表**

```http
GET /api/v1/roles
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": "role_001",
                "name": "admin",
                "display_name": "系统管理员",
                "description": "系统管理员角色",
                "permissions": ["doc:create", "doc:read", "doc:update", "doc:delete", "kg:manage", "user:manage", "sys:config"],
                "user_count": 2,
                "created_at": "2025-01-01T00:00:00Z"
            },
            {
                "id": "role_002",
                "name": "user",
                "display_name": "普通用户",
                "description": "普通用户角色",
                "permissions": ["doc:read", "chat:query"],
                "user_count": 150,
                "created_at": "2025-01-01T00:00:00Z"
            }
        ]
    }
}
```

---

## 9. 系统管理API

### 9.1 系统配置

**获取系统配置**

```http
GET /api/v1/system/config
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "general": {
            "site_name": "GraphRAG知识库系统",
            "site_description": "企业级知识库问答系统",
            "max_upload_size": 52428800,
            "supported_formats": ["pdf", "docx", "md", "txt"]
        },
        "search": {
            "default_top_k": 10,
            "max_top_k": 100,
            "default_threshold": 0.5,
            "enable_hybrid_search": true
        },
        "llm": {
            "default_model": "qwen2.5-max",
            "max_tokens": 4096,
            "default_temperature": 0.7
        },
        "kg": {
            "default_max_hops": 3,
            "default_min_confidence": 0.6,
            "enable_auto_extraction": true
        }
    }
}
```

**更新系统配置**

```http
PUT /api/v1/system/config
Content-Type: application/json
Authorization: Bearer {token}

{
    "search": {
        "default_top_k": 20,
        "default_threshold": 0.6
    }
}
```

### 9.2 系统状态

**请求**

```http
GET /api/v1/system/status
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": "15d 8h 32m",
        "components": [
            {
                "name": "api_gateway",
                "status": "healthy",
                "latency_ms": 5
            },
            {
                "name": "business_service",
                "status": "healthy",
                "latency_ms": 12
            },
            {
                "name": "ai_service",
                "status": "healthy",
                "latency_ms": 25
            },
            {
                "name": "postgresql",
                "status": "healthy",
                "latency_ms": 3
            },
            {
                "name": "milvus",
                "status": "healthy",
                "latency_ms": 8
            },
            {
                "name": "neo4j",
                "status": "healthy",
                "latency_ms": 10
            },
            {
                "name": "redis",
                "status": "healthy",
                "latency_ms": 1
            }
        ],
        "resources": {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 38.5,
            "gpu_usage": 78.3
        },
        "statistics": {
            "total_documents": 12500,
            "total_chunks": 156000,
            "total_entities": 89000,
            "total_relations": 234000,
            "total_users": 1250,
            "queries_today": 5678
        }
    }
}
```

### 9.3 审计日志

**请求**

```http
GET /api/v1/system/audit-logs?page=1&size=20&action=login&user_id=user_001
Authorization: Bearer {token}
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `page` | integer | 否 | 页码 |
| `size` | integer | 否 | 每页数量 |
| `action` | string | 否 | 操作类型过滤 |
| `user_id` | string | 否 | 用户ID过滤 |
| `resource_type` | string | 否 | 资源类型过滤 |
| `start_time` | string | 否 | 开始时间 |
| `end_time` | string | 否 | 结束时间 |

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "id": "log_001",
                "user_id": "user_001",
                "username": "admin",
                "action": "login",
                "resource_type": "auth",
                "resource_id": null,
                "details": {
                    "ip": "192.168.1.100",
                    "user_agent": "Mozilla/5.0...",
                    "location": "北京市"
                },
                "status": "success",
                "created_at": "2026-02-17T10:00:00Z"
            },
            {
                "id": "log_002",
                "user_id": "user_001",
                "username": "admin",
                "action": "create",
                "resource_type": "document",
                "resource_id": "doc_abc123",
                "details": {
                    "title": "系统设计文档",
                    "doc_type": "pdf"
                },
                "status": "success",
                "created_at": "2026-02-17T10:05:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 1560,
            "total_pages": 78
        }
    }
}
```

### 9.4 统计分析

**请求**

```http
GET /api/v1/system/statistics?period=7d
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "period": "7d",
        "document_stats": {
            "total": 12500,
            "new_this_period": 156,
            "by_type": {
                "pdf": 8500,
                "docx": 2500,
                "md": 1000,
                "txt": 500
            },
            "by_status": {
                "published": 12000,
                "processing": 150,
                "failed": 350
            }
        },
        "query_stats": {
            "total_queries": 45678,
            "avg_response_time_ms": 1250,
            "avg_satisfaction": 4.2,
            "by_day": [
                {"date": "2026-02-11", "count": 6500},
                {"date": "2026-02-12", "count": 7200},
                {"date": "2026-02-13", "count": 5800}
            ]
        },
        "kg_stats": {
            "total_entities": 89000,
            "total_relations": 234000,
            "entity_types": {
                "Person": 15000,
                "Organization": 8000,
                "Project": 5000,
                "Product": 3000
            },
            "relation_types": {
                "BELONGS_TO": 45000,
                "PARTICIPATES_IN": 38000,
                "DEPENDS_ON": 25000
            }
        },
        "user_stats": {
            "total_users": 1250,
            "active_users": 856,
            "new_users_this_period": 23
        }
    }
}
```

---

## 10. 异步任务API

### 10.1 任务状态查询

**请求**

```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "task_id": "task_xyz789",
        "type": "document_process",
        "status": "running",
        "progress": 65,
        "created_at": "2026-02-17T10:00:00Z",
        "started_at": "2026-02-17T10:00:05Z",
        "estimated_completion": "2026-02-17T10:05:00Z",
        "resource_id": "doc_abc123",
        "resource_type": "document",
        "stages": [
            {
                "name": "parse",
                "status": "completed",
                "progress": 100,
                "started_at": "2026-02-17T10:00:05Z",
                "completed_at": "2026-02-17T10:00:17Z",
                "duration_ms": 12500
            },
            {
                "name": "chunk",
                "status": "completed",
                "progress": 100,
                "started_at": "2026-02-17T10:00:17Z",
                "completed_at": "2026-02-17T10:00:20Z",
                "duration_ms": 3200
            },
            {
                "name": "embedding",
                "status": "completed",
                "progress": 100,
                "started_at": "2026-02-17T10:00:20Z",
                "completed_at": "2026-02-17T10:01:06Z",
                "duration_ms": 45800
            },
            {
                "name": "entity_extraction",
                "status": "running",
                "progress": 65,
                "started_at": "2026-02-17T10:01:06Z",
                "completed_at": null,
                "duration_ms": null
            },
            {
                "name": "relation_extraction",
                "status": "pending",
                "progress": 0,
                "started_at": null,
                "completed_at": null,
                "duration_ms": null
            },
            {
                "name": "graph_build",
                "status": "pending",
                "progress": 0,
                "started_at": null,
                "completed_at": null,
                "duration_ms": null
            }
        ],
        "result": null,
        "error": null
    }
}
```

### 10.2 任务列表

**请求**

```http
GET /api/v1/tasks?type=document_process&status=running&page=1&size=20
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [
            {
                "task_id": "task_xyz789",
                "type": "document_process",
                "status": "running",
                "progress": 65,
                "resource_id": "doc_abc123",
                "created_at": "2026-02-17T10:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 5,
            "total_pages": 1
        }
    }
}
```

### 10.3 取消任务

**请求**

```http
POST /api/v1/tasks/{task_id}/cancel
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 200,
    "message": "Task cancelled successfully",
    "data": {
        "task_id": "task_xyz789",
        "status": "cancelled"
    }
}
```

### 10.4 重试任务

**请求**

```http
POST /api/v1/tasks/{task_id}/retry
Authorization: Bearer {token}
```

**响应**

```json
{
    "code": 202,
    "message": "Task retry started",
    "data": {
        "task_id": "task_xyz789",
        "new_task_id": "task_xyz789_retry_1",
        "status": "pending"
    }
}
```

---

## 11. WebSocket接口

### 11.1 连接建立

**连接URL**

```
wss://ws.example.com/v1/chat?token={jwt_token}
```

### 11.2 消息格式

**客户端发送消息**

```json
{
    "type": "query",
    "id": "msg_001",
    "payload": {
        "query": "张三参与了哪些项目？",
        "session_id": "session_abc123",
        "options": {
            "show_evidence": true,
            "max_tokens": 2048
        }
    }
}
```

**服务端响应消息**

```json
{
    "type": "search_start",
    "id": "msg_001",
    "payload": {
        "status": "searching",
        "message": "正在检索相关知识..."
    }
}
```

```json
{
    "type": "token",
    "id": "msg_001",
    "payload": {
        "content": "根据"
    }
}
```

```json
{
    "type": "done",
    "id": "msg_001",
    "payload": {
        "message_id": "msg_xyz789",
        "references": [...],
        "evidence_chains": [...]
    }
}
```

### 11.3 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `query` | 客户端→服务端 | 发送查询 |
| `search_start` | 服务端→客户端 | 检索开始 |
| `search_result` | 服务端→客户端 | 检索结果 |
| `evidence_chain` | 服务端→客户端 | 证据链 |
| `generation_start` | 服务端→客户端 | 生成开始 |
| `token` | 服务端→客户端 | 生成Token |
| `done` | 服务端→客户端 | 完成 |
| `error` | 服务端→客户端 | 错误 |
| `ping` | 双向 | 心跳 |
| `pong` | 双向 | 心跳响应 |

### 11.4 心跳机制

客户端每30秒发送心跳：

```json
{
    "type": "ping",
    "timestamp": "2026-02-17T10:30:00Z"
}
```

服务端响应：

```json
{
    "type": "pong",
    "timestamp": "2026-02-17T10:30:00Z"
}
```

---

## 12. 错误码定义

### 12.1 业务错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `10001` | 400 | 参数校验失败 |
| `10002` | 400 | 请求格式错误 |
| `10003` | 400 | 文件格式不支持 |
| `10004` | 400 | 文件大小超限 |
| `20001` | 401 | 未登录 |
| `20002` | 401 | Token过期 |
| `20003` | 401 | Token无效 |
| `20004` | 403 | 无权限访问 |
| `20005` | 403 | 账号被禁用 |
| `30001` | 404 | 资源不存在 |
| `30002` | 404 | 文档不存在 |
| `30003` | 404 | 实体不存在 |
| `40001` | 409 | 资源已存在 |
| `40002` | 409 | 文档已存在 |
| `50001` | 429 | 请求频率超限 |
| `50002` | 429 | 并发数超限 |
| `60001` | 500 | 服务器内部错误 |
| `60002` | 500 | 数据库错误 |
| `60003` | 500 | 向量检索服务异常 |
| `60004` | 500 | 图数据库服务异常 |
| `60005` | 500 | LLM服务异常 |
| `60006` | 503 | 服务暂时不可用 |
| `60007` | 504 | 服务超时 |

### 12.2 错误响应格式

```json
{
    "code": 10001,
    "message": "Parameter validation failed",
    "data": {
        "errors": [
            {
                "field": "title",
                "message": "标题不能为空"
            },
            {
                "field": "file",
                "message": "文件大小超过限制（最大50MB）"
            }
        ]
    },
    "timestamp": "2026-02-17T10:30:00Z",
    "request_id": "req_abc123"
}
```

---

## 13. 接口限流策略

### 13.1 限流规则

| 接口类型 | 限流策略 | 说明 |
|---------|---------|------|
| **认证接口** | 10次/分钟/IP | 登录、注册等 |
| **查询接口** | 100次/分钟/用户 | 文档列表、实体查询等 |
| **问答接口** | 30次/分钟/用户 | 对话、检索等 |
| **上传接口** | 10次/分钟/用户 | 文档上传 |
| **管理接口** | 60次/分钟/用户 | 用户管理、系统配置等 |

### 13.2 限流响应

当触发限流时，返回HTTP 429：

```json
{
    "code": 50001,
    "message": "Rate limit exceeded",
    "data": {
        "limit": 30,
        "remaining": 0,
        "reset_at": "2026-02-17T10:31:00Z",
        "retry_after": 45
    },
    "timestamp": "2026-02-17T10:30:15Z",
    "request_id": "req_abc123"
}
```

### 13.3 限流响应头

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1708130656
Retry-After: 45
```

---

## 14. 版本控制策略

### 14.1 版本号规范

采用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**：不兼容的API变更
- **MINOR**：向后兼容的功能新增
- **PATCH**：向后兼容的问题修复

### 14.2 版本传递方式

**URL路径方式（推荐）**

```
https://api.example.com/v1/documents
https://api.example.com/v2/documents
```

**请求头方式**

```http
GET /api/documents
Accept: application/vnd.graphrag.v1+json
```

### 14.3 版本生命周期

| 阶段 | 持续时间 | 说明 |
|------|---------|------|
| **Current** | 当前版本 | 完全支持和维护 |
| **Deprecated** | 6个月 | 停止新增功能，仅修复关键问题 |
| **Sunset** | 3个月 | 通知用户迁移，准备下线 |
| **Retired** | - | 停止服务 |

### 14.4 版本废弃通知

在响应头中添加废弃通知：

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Aug 2026 00:00:00 GMT
Link: </v2/documents>; rel="successor-version"
```

---

## 附录

### A. OpenAPI规范

完整的OpenAPI 3.0规范文档可通过以下方式获取：

```http
GET /api/v1/openapi.json
Accept: application/json
```

或

```http
GET /api/v1/openapi.yaml
Accept: application/yaml
```

### B. Postman集合

Postman集合可从以下地址导入：

```
https://api.example.com/postman/collection.json
```

### C. SDK下载

| 语言 | 下载地址 |
|------|---------|
| Java | https://github.com/example/graphrag-java-sdk |
| Python | https://github.com/example/graphrag-python-sdk |
| JavaScript | https://github.com/example/graphrag-js-sdk |

### D. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-02-17 | 初始版本，完整API接口定义 | 技术团队 |

---

> 📝 **文档维护说明**
> 
> 本文档为GraphRAG系统API接口设计正式版，遵循RESTful API设计规范。
> API接口需要根据实际开发进度进行调整，如有变更请更新文档版本。
