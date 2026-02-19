# 前后端API接口对应性检查报告

## 一、检查概述

本报告对前端应用中所有API接口与后端服务进行了全面的对应性检查，包括URL路径、HTTP方法、请求/响应数据结构等方面。

---

## 二、架构分析

### 2.1 服务架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │  Java Gateway   │     │  Python AI      │
│   (React:3000)  │────▶│   (Port:8080)   │────▶│  (Port:8000)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │   /api/*              │   /v1/*               │
        └───────────────────────┴───────────────────────┘
```

### 2.2 当前代理配置

**vite.config.ts:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // ❌ 问题：直接指向Python服务
    changeOrigin: true,
  },
}
```

**前端 client.ts:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
```

---

## 三、问题清单

### 🔴 严重问题 (Critical)

#### C1. 前端代理配置指向错误服务

| 项目 | 当前配置 | 正确配置 |
|------|---------|---------|
| vite.config.ts | `target: 'http://localhost:8000'` | `target: 'http://localhost:8080'` |

**影响：** 前端请求无法到达Java Gateway，认证、用户管理等功能无法工作。

**修复建议：**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8080',  // 指向Java Gateway
    changeOrigin: true,
  },
}
```

---

#### C2. API路径前缀不一致

**后端控制器路径汇总：**

| 模块 | 控制器 | 实际路径 | 是否有/api前缀 |
|------|--------|---------|---------------|
| Gateway | AuthController | `/auth/*` | ❌ 无 |
| Gateway | UserController | `/system/user/*` | ❌ 无 |
| Gateway | HealthController | `/health/*` | ❌ 无 |
| Gateway | ProxyController | `/v1/search/**` 等 | ❌ 无 |
| Document | DocumentController | `/api/v1/documents/*` | ✅ 有 |
| System | SystemConfigController | `/v1/system/config/*` | ❌ 无 |
| System | SystemMonitorController | `/v1/system/*` | ❌ 无 |
| System | AuditLogController | `/v1/system/audit-logs/*` | ❌ 无 |

**前端API调用路径：**

| 前端API | 调用路径 | 后端期望路径 | 状态 |
|---------|---------|-------------|------|
| chatApi.chat | `/qa/chat` | `/v1/qa/chat` | ❌ 不匹配 |
| chatApi.chatStream | `/qa/chat/stream` | `/v1/qa/chat/stream` | ❌ 不匹配 |
| systemApi.getConfig | `/system/config` | `/v1/system/config` | ❌ 不匹配 |
| systemApi.getStatus | `/system/status` | `/v1/system/status` | ❌ 不匹配 |
| systemApi.getAuditLogs | `/system/audit-logs` | `/v1/system/audit-logs` | ❌ 不匹配 |
| documentApi.list | `/documents` | `/api/v1/documents/list` | ❌ 不匹配 |

**修复建议：** 统一所有后端控制器路径前缀为 `/api/v1`

---

### 🟠 中等问题 (Medium)

#### M1. 分页响应数据结构不匹配

**前端期望结构 (client.ts):**
```typescript
interface PaginationResponse<T> {
  items: T[]
  pagination: {
    page: number
    size: number
    total: number
    total_pages: number
  }
}
```

**后端实际结构 (PageResult.java):**
```java
public class PageResult<T> {
    private List<T> list;      // 不是 items
    private Long total;
    private Long pageNum;      // 不是 page
    private Long pageSize;     // 不是 size
    private Long pages;        // 不是 total_pages
    private Boolean hasNext;
    private Boolean hasPrevious;
}
```

**影响范围：** documentApi.list, systemApi.getAuditLogs 等分页接口

**修复建议：** 修改前端 PaginationResponse 以匹配后端结构，或修改后端 PageResult 字段名

---

#### M2. 缺少认证相关API定义

**后端已有接口：**

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/logout` | 用户登出 |
| POST | `/auth/refresh` | 刷新令牌 |
| GET | `/auth/me` | 获取当前用户信息 |

**前端状态：** ❌ 未定义对应API

**修复建议：** 在前端添加 `auth.ts` API模块

---

#### M3. 文档API方法与路径不匹配

| 前端方法 | 前端路径 | 后端路径 | HTTP方法 | 状态 |
|---------|---------|---------|---------|------|
| documentApi.list | `/documents` | `/api/v1/documents/list` | GET→POST | ❌ 不匹配 |
| documentApi.upload | `/documents/upload` | `/api/v1/documents/upload` | POST | ✅ 匹配 |
| documentApi.get | `/documents/{id}` | `/api/v1/documents/{id}` | GET | ✅ 匹配 |
| documentApi.delete | `/documents/{id}` | `/api/v1/documents/{id}` | DELETE | ✅ 匹配 |
| documentApi.batchDelete | `/documents/batch-delete` | ❌ 后端无此接口 | POST | ❌ 缺失 |
| documentApi.reprocess | `/documents/{id}/reprocess` | ❌ 后端无此接口 | POST | ❌ 缺失 |
| documentApi.download | `/documents/{id}/download` | ❌ 后端无此接口 | GET | ❌ 缺失 |

---

### 🟡 轻微问题 (Minor)

#### m1. 系统配置响应结构不匹配

**前端期望 (system.ts):**
```typescript
interface SystemConfig {
  general: { site_name, site_description, ... }
  search: { default_top_k, max_top_k, ... }
  llm: { default_model, max_tokens, ... }
  kg: { default_max_hops, ... }
}
```

**后端实际返回 (SystemConfigController):**
```java
Map<String, Object> // { configs: { type: { key: value } } }
```

---

#### m2. 系统状态响应结构不匹配

**前端期望 (system.ts):**
```typescript
interface SystemStatus {
  status: string
  version: string
  uptime: string
  components: ComponentStatus[]
  resources: { cpu_usage, memory_usage, ... }
  statistics: { total_documents, ... }
}
```

**后端实际返回 (Python):**
```python
{
  "code": 200,
  "message": "success",
  "data": SystemStatus(...)
}
```

**后端实际返回 (Java):**
```java
Result<Map<String, Object>> // { java: {...}, python: {...}, overall: {...} }
```

---

#### m3. SSE流式接口实现问题

**前端 chatStreamPost:**
- 使用 fetch API 手动解析 SSE
- 未传递 Authorization header

**后端期望:**
- 标准 SSE 格式
- 需要认证 token

---

## 四、详细接口对照表

### 4.1 认证接口

| 前端API | 方法 | 前端路径 | 后端路径 | 状态 |
|---------|------|---------|---------|------|
| - | POST | - | `/auth/login` | ❌ 缺失 |
| - | POST | - | `/auth/register` | ❌ 缺失 |
| - | POST | - | `/auth/logout` | ❌ 缺失 |
| - | POST | - | `/auth/refresh` | ❌ 缺失 |
| - | GET | - | `/auth/me` | ❌ 缺失 |

### 4.2 用户管理接口

| 前端API | 方法 | 前端路径 | 后端路径 | 状态 |
|---------|------|---------|---------|------|
| - | GET | - | `/system/user/list` | ❌ 缺失 |
| - | GET | - | `/system/user/{id}` | ❌ 缺失 |
| - | POST | - | `/system/user` | ❌ 缺失 |
| - | PUT | - | `/system/user/{id}` | ❌ 缺失 |
| - | DELETE | - | `/system/user/{id}` | ❌ 缺失 |

### 4.3 文档管理接口

| 前端API | 方法 | 前端路径 | 后端路径 | 状态 |
|---------|------|---------|---------|------|
| documentApi.list | GET | `/documents` | POST `/api/v1/documents/list` | ❌ 方法/路径不匹配 |
| documentApi.get | GET | `/documents/{id}` | GET `/api/v1/documents/{id}` | ⚠️ 路径前缀 |
| documentApi.upload | POST | `/documents/upload` | POST `/api/v1/documents/upload` | ⚠️ 路径前缀 |
| documentApi.delete | DELETE | `/documents/{id}` | DELETE `/api/v1/documents/{id}` | ⚠️ 路径前缀 |
| documentApi.getProgress | GET | `/documents/{id}/progress` | GET `/api/v1/documents/{id}/progress` | ⚠️ 路径前缀 |
| documentApi.batchDelete | POST | `/documents/batch-delete` | ❌ | ❌ 后端缺失 |
| documentApi.reprocess | POST | `/documents/{id}/reprocess` | ❌ | ❌ 后端缺失 |
| documentApi.download | GET | `/documents/{id}/download` | ❌ | ❌ 后端缺失 |

### 4.4 问答接口

| 前端API | 方法 | 前端路径 | 后端路径 | 状态 |
|---------|------|---------|---------|------|
| chatApi.chat | POST | `/qa/chat` | POST `/qa/chat` | ⚠️ 需代理 |
| chatApi.chatStream | POST | `/qa/chat/stream` | POST `/qa/chat/stream` | ⚠️ 需代理 |
| chatApi.simpleChat | POST | `/qa/simple` | POST `/qa/simple` | ⚠️ 需代理 |

### 4.5 系统管理接口

| 前端API | 方法 | 前端路径 | 后端路径 | 状态 |
|---------|------|---------|---------|------|
| systemApi.getConfig | GET | `/system/config` | GET `/v1/system/config` | ⚠️ 路径前缀 |
| systemApi.updateConfig | PUT | `/system/config` | PUT `/v1/system/config` | ⚠️ 路径前缀 |
| systemApi.getStatus | GET | `/system/status` | GET `/v1/system/status` | ⚠️ 路径前缀 |
| systemApi.getStatistics | GET | `/system/statistics` | GET `/v1/system/statistics` | ⚠️ 路径前缀 |
| systemApi.getAuditLogs | GET | `/system/audit-logs` | GET `/v1/system/audit-logs` | ⚠️ 路径前缀 |
| systemApi.healthCheck | GET | `/system/health` | GET `/v1/system/health` | ⚠️ 路径前缀 |

### 4.6 搜索接口

| 前端API | 方法 | 前端路径 | 后端路径 | 状态 |
|---------|------|---------|---------|------|
| - | POST | - | `/search/hybrid` | ❌ 前端缺失 |
| - | GET | - | `/search/keyword` | ❌ 前端缺失 |
| - | POST | - | `/search/vector` | ❌ 前端缺失 |

---

## 五、修复方案

### 5.1 立即修复 (Critical)

#### 修复1: 更新 vite.config.ts 代理配置

```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',  // 指向Java Gateway
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),  // 可选：移除/api前缀
      },
    },
  },
})
```

#### 修复2: 统一后端路径前缀

**方案A: 修改所有后端控制器添加 /api 前缀**

```java
// AuthController.java
@RequestMapping("/api/v1/auth")  // 添加前缀

// UserController.java
@RequestMapping("/api/v1/system/user")  // 添加前缀

// SystemConfigController.java
@RequestMapping("/api/v1/system/config")  // 已有 /v1，添加 /api

// DocumentController.java
// 已正确: /api/v1/documents
```

**方案B: 修改前端API路径**

```typescript
// client.ts
const API_BASE_URL = '/api/v1'  // 保持不变

// 所有API调用添加正确前缀
```

### 5.2 短期修复 (Medium)

#### 修复3: 添加认证API模块

创建 `src/api/auth.ts`:

```typescript
import apiClient from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  refreshToken: string
  expiresIn: number
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export const authApi = {
  async login(request: LoginRequest): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/auth/login', request)
  },

  async register(request: RegisterRequest): Promise<void> {
    await apiClient.post('/auth/register', request)
  },

  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },

  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>('/auth/refresh', { refreshToken })
  },

  async getCurrentUser(): Promise<UserInfoResponse> {
    return apiClient.get<UserInfoResponse>('/auth/me')
  },
}
```

#### 修复4: 修复分页响应结构

修改 `src/api/client.ts`:

```typescript
interface PaginationResponse<T> {
  list: T[]           // 改为 list
  total: number
  pageNum: number     // 改为 pageNum
  pageSize: number    // 改为 pageSize
  pages: number       // 改为 pages
  hasNext: boolean
  hasPrevious: boolean
}
```

### 5.3 长期优化 (Minor)

#### 优化1: 添加缺失的后端接口

- 文档批量删除接口
- 文档重新处理接口
- 文档下载接口

#### 优化2: 完善前端API类型定义

确保所有接口都有完整的 TypeScript 类型定义，与后端 DTO 保持一致。

---

## 六、测试建议

### 6.1 接口测试清单

| 测试场景 | 测试内容 | 预期结果 |
|---------|---------|---------|
| 正常请求 | 调用各API接口 | 返回正确数据和状态码 |
| 认证失败 | 无token访问需认证接口 | 返回401 |
| 权限不足 | 无权限访问需权限接口 | 返回403 |
| 参数错误 | 缺少必填参数 | 返回400 |
| 服务不可用 | 后端服务停止 | 返回503 |
| 超时处理 | 请求超时 | 返回超时错误 |

### 6.2 边界条件测试

- 分页参数边界值
- 文件上传大小限制
- 请求体大小限制
- 并发请求处理

---

## 七、总结

### 问题统计

| 严重程度 | 数量 | 说明 |
|---------|------|------|
| 🔴 Critical | 2 | 代理配置错误、路径前缀不一致 |
| 🟠 Medium | 3 | 响应结构不匹配、缺失API定义 |
| 🟡 Minor | 3 | 结构细节不匹配、功能缺失 |

### 优先级建议

1. **立即修复**: vite.config.ts 代理配置
2. **本周完成**: 统一API路径前缀、添加认证API
3. **下周完成**: 修复分页响应结构、添加缺失接口
4. **持续优化**: 完善类型定义、增加测试覆盖
