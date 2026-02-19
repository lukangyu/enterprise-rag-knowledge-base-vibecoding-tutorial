# 项目架构重构计划 - Java与Python服务职责分离

> 创建日期: 2026-02-19
> 状态: 待确认
> 目标: 实现Java与Python服务的职责分离，优化项目架构

---

## 一、重构目标

### 1.1 核心原则
- **Java负责"管"**: 认证授权、用户管理、文档管理、API网关
- **Python负责"算"**: 检索、知识图谱、问答、AI能力

### 1.2 重构范围

| 操作 | 模块 | 说明 |
|------|------|------|
| ❌ 删除 | graphrag-search | Java检索模块，功能由Python实现 |
| ❌ 删除 | graphrag-knowledge | Java知识图谱模块（仅有pom.xml） |
| ✅ 完善 | graphrag-system | 新建完整的企业级系统管理模块 |
| ✅ 增强 | graphrag-gateway | 添加API转发、限流、聚合功能 |

---

## 二、详细任务清单

### 2.1 删除Java模块

#### T1: 删除graphrag-search模块

**删除文件：**
```
backend/graphrag-search/
├── pom.xml
├── src/
│   └── main/
│       └── java/com/graphrag/search/
│           ├── controller/SearchController.java
│           ├── dto/
│           │   ├── HybridSearchRequest.java
│           │   ├── HybridSearchResponse.java
│           │   └── SearchResult.java
│           ├── enums/FusionStrategy.java
│           └── service/impl/
│               ├── HybridSearchService.java
│               ├── KeywordSearchService.java
│               ├── RRFFusionService.java
│               └── VectorSearchService.java
```

**修改文件：**
- `backend/pom.xml` - 移除`<module>graphrag-search</module>`

#### T2: 删除graphrag-knowledge模块

**删除文件：**
```
backend/graphrag-knowledge/
└── pom.xml
```

**修改文件：**
- `backend/pom.xml` - 移除`<module>graphrag-knowledge</module>`

---

### 2.2 完善graphrag-system模块

#### T3: 创建graphrag-system模块结构

**目录结构：**
```
backend/graphrag-system/
├── pom.xml
└── src/main/
    ├── java/com/graphrag/system/
    │   ├── SystemApplication.java
    │   ├── config/
    │   │   ├── MybatisPlusConfig.java
    │   │   └── SwaggerConfig.java
    │   ├── controller/
    │   │   ├── AuditLogController.java
    │   │   ├── SystemConfigController.java
    │   │   └── SystemMonitorController.java
    │   ├── domain/
    │   │   ├── dto/
    │   │   │   ├── AuditLogQueryDTO.java
    │   │   │   └── SystemConfigDTO.java
    │   │   └── entity/
    │   │       ├── AuditLog.java
    │   │       └── SystemConfig.java
    │   ├── mapper/
    │   │   ├── AuditLogMapper.java
    │   │   └── SystemConfigMapper.java
    │   └── service/
    │       ├── impl/
    │       │   ├── AuditLogServiceImpl.java
    │       │   ├── SystemConfigServiceImpl.java
    │       │   └── SystemMonitorServiceImpl.java
    │       ├── AuditLogService.java
    │       ├── SystemConfigService.java
    │       └── SystemMonitorService.java
    └── resources/
        ├── application.yml
        └── mapper/
            ├── AuditLogMapper.xml
            └── SystemConfigMapper.xml
```

#### T4: 实现审计日志功能

**功能点：**
- 审计日志实体设计
- 审计日志持久化
- 审计日志查询API
- 操作行为记录切面

**API接口：**
```
GET  /api/v1/system/audit-logs      - 查询审计日志
GET  /api/v1/system/audit-logs/{id} - 获取日志详情
POST /api/v1/system/audit-logs      - 创建审计日志
```

#### T5: 实现系统配置管理

**功能点：**
- 系统配置实体设计
- 配置项CRUD操作
- 配置缓存机制
- 配置变更审计

**API接口：**
```
GET    /api/v1/system/config        - 获取系统配置
PUT    /api/v1/system/config        - 更新系统配置
GET    /api/v1/system/config/{key}  - 获取单个配置项
```

#### T6: 实现系统监控聚合

**功能点：**
- 调用Python系统监控API
- 聚合Java服务健康状态
- 统一监控数据输出

**API接口：**
```
GET /api/v1/system/status           - 获取系统状态
GET /api/v1/system/status/resources - 获取资源使用
GET /api/v1/system/statistics       - 获取统计数据
```

---

### 2.3 增强graphrag-gateway模块

#### T7: 实现API转发代理

**新增配置类：**
```java
// ProxyConfig.java - 代理配置
@Configuration
public class ProxyConfig {
    @Bean
    public RestTemplate restTemplate() {
        // 配置HTTP客户端
    }
}
```

**新增服务类：**
```java
// ProxyService.java - 代理服务
@Service
public class ProxyService {
    // 转发请求到Python服务
    public ResponseEntity<?> forward(String path, HttpMethod method, 
                                      Object body, HttpHeaders headers);
}
```

#### T8: 配置API路由规则

**路由配置：**
```yaml
# application-proxy.yml
proxy:
  routes:
    search:
      path: /v1/search/**
      target: http://ai-services:8000/search
    kg:
      path: /v1/kg/**
      target: http://ai-services:8000/kg
    qa:
      path: /v1/qa/**
      target: http://ai-services:8000/qa
    system-status:
      path: /v1/system/status/**
      target: http://ai-services:8000/system/status
    system-statistics:
      path: /v1/system/statistics/**
      target: http://ai-services:8000/system/statistics
```

#### T9: 实现请求限流

**新增组件：**
```java
// RateLimitFilter.java - 限流过滤器
@Component
public class RateLimitFilter implements GatewayFilter {
    // 基于Redis的令牌桶限流
}

// RateLimitConfig.java - 限流配置
@Configuration
public class RateLimitConfig {
    // 配置各API的限流规则
}
```

#### T10: 实现统一错误处理

**新增组件：**
```java
// GlobalExceptionHandler.java
@RestControllerAdvice
public class GlobalExceptionHandler {
    // 统一异常处理
    // 统一错误响应格式
}
```

---

### 2.4 Python服务增强

#### T11: 完善Python知识图谱API

**新增/完善API：**
```
POST /kg/extract/entities      - 实体抽取
POST /kg/extract/relations     - 关系抽取
POST /kg/build                 - 构建知识图谱
GET  /kg/entities/{id}         - 获取实体详情
GET  /kg/relations             - 查询关系
POST /kg/traverse              - 图遍历
POST /kg/query/path            - 路径查询
POST /kg/query/multi-hop       - 多跳查询
```

#### T12: 完善Python检索API

**新增/完善API：**
```
POST /search/hybrid            - 混合检索
POST /search/vector            - 向量检索
POST /search/keyword           - 关键词检索
POST /search/rerank            - 重排序
```

---

## 三、API路由配置

### 3.1 路由规则

| 路径 | 处理方 | 说明 |
|------|--------|------|
| `/api/v1/auth/*` | Java gateway | 认证授权 |
| `/api/v1/users/*` | Java gateway | 用户管理 |
| `/api/v1/roles/*` | Java gateway | 角色管理 |
| `/api/v1/permissions/*` | Java gateway | 权限管理 |
| `/api/v1/documents/*` | Java document | 文档管理 |
| `/api/v1/search/*` | → Python ai-services | 检索服务 |
| `/api/v1/kg/*` | → Python ai-services | 知识图谱 |
| `/api/v1/qa/*` | → Python ai-services | 问答服务 |
| `/api/v1/system/config/*` | Java system | 系统配置 |
| `/api/v1/system/audit-logs/*` | Java system | 审计日志 |
| `/api/v1/system/status/*` | 聚合 Java + Python | 系统状态 |
| `/api/v1/system/statistics/*` | 聚合 Java + Python | 统计数据 |

### 3.2 聚合API实现

```java
// SystemMonitorController.java
@GetMapping("/system/status")
public ResponseEntity<?> getSystemStatus() {
    // 1. 获取Java服务状态
    Map<String, Object> javaStatus = getJavaServiceStatus();
    
    // 2. 调用Python API获取AI服务状态
    Map<String, Object> pythonStatus = proxyService.get(
        "http://ai-services:8000/system/status", Map.class);
    
    // 3. 聚合返回
    return ResponseEntity.ok(Map.of(
        "java", javaStatus,
        "python", pythonStatus,
        "overall", calculateOverallStatus(javaStatus, pythonStatus)
    ));
}
```

---

## 四、安全措施

### 4.1 认证Token验证

```java
// 所有API请求需验证JWT Token
// 转发请求时携带认证信息
public ResponseEntity<?> forward(HttpServletRequest request) {
    String token = request.getHeader("Authorization");
    // 验证Token有效性
    // 转发时携带Token
}
```

### 4.2 请求限流配置

```yaml
rate-limit:
  default:
    capacity: 100        # 令牌桶容量
    refill-rate: 10      # 每秒补充令牌数
  apis:
    /api/v1/search/*:
      capacity: 50
      refill-rate: 5
    /api/v1/qa/*:
      capacity: 20
      refill-rate: 2
```

### 4.3 数据加密

- 所有API使用HTTPS
- 敏感配置使用Jasypt加密
- 密码使用BCrypt加密存储

---

## 五、错误处理规范

### 5.1 统一错误响应格式

```json
{
  "code": 40001,
  "message": "Invalid parameter",
  "data": null,
  "timestamp": "2026-02-19T10:00:00Z",
  "traceId": "abc123"
}
```

### 5.2 错误码定义

| 错误码范围 | 类型 |
|-----------|------|
| 20000-20999 | 成功 |
| 40000-40999 | 客户端错误 |
| 50000-50999 | 服务端错误 |
| 60000-60999 | Python服务错误 |

---

## 六、文件创建/删除清单

### 6.1 删除文件

| 文件/目录 | 说明 |
|----------|------|
| `backend/graphrag-search/` | 整个目录删除 |
| `backend/graphrag-knowledge/` | 整个目录删除 |

### 6.2 新建文件

| 文件 | 说明 |
|------|------|
| `backend/graphrag-system/pom.xml` | 模块配置 |
| `backend/graphrag-system/src/main/java/.../SystemApplication.java` | 启动类 |
| `backend/graphrag-system/src/main/java/.../controller/*.java` | 控制器 |
| `backend/graphrag-system/src/main/java/.../service/*.java` | 服务类 |
| `backend/graphrag-system/src/main/java/.../domain/**/*.java` | 领域模型 |
| `backend/graphrag-system/src/main/resources/application.yml` | 配置文件 |
| `backend/graphrag-gateway/src/main/java/.../proxy/*.java` | 代理服务 |
| `backend/graphrag-gateway/src/main/java/.../filter/*.java` | 过滤器 |
| `backend/graphrag-gateway/src/main/resources/application-proxy.yml` | 代理配置 |

### 6.3 修改文件

| 文件 | 修改内容 |
|------|---------|
| `backend/pom.xml` | 移除search和knowledge模块 |
| `backend/graphrag-gateway/pom.xml` | 添加代理相关依赖 |
| `backend/graphrag-gateway/src/main/resources/application.yml` | 添加代理配置 |

---

## 七、开发时间线

```
Day 1:
├── 删除graphrag-search模块
├── 删除graphrag-knowledge模块
└── 更新父pom.xml

Day 2:
├── 创建graphrag-system模块骨架
├── 实现审计日志功能
└── 实现系统配置管理

Day 3:
├── 实现系统监控聚合
├── 实现API转发代理
└── 配置路由规则

Day 4:
├── 实现请求限流
├── 实现统一错误处理
└── 完善安全措施

Day 5:
├── 集成测试
├── 文档更新
└── 部署验证
```

---

## 八、验收标准

### 8.1 功能验收

| 功能 | 验收标准 |
|------|---------|
| 模块删除 | graphrag-search和graphrag-knowledge完全移除 |
| 审计日志 | 支持记录、查询、分页 |
| 系统配置 | 支持动态配置读取和更新 |
| API转发 | 所有AI相关API正确转发到Python |
| 限流 | 超过限制返回429错误 |
| 错误处理 | 统一错误格式，包含traceId |

### 8.2 性能验收

| 指标 | 目标值 |
|------|--------|
| API转发延迟 | < 10ms |
| 限流准确性 | > 99% |
| 系统状态聚合 | < 500ms |

---

## 九、风险与应对

| 风险 | 等级 | 应对措施 |
|------|------|---------|
| 服务间通信故障 | 高 | 实现熔断降级机制 |
| 数据一致性 | 中 | 使用分布式事务或最终一致性 |
| 性能瓶颈 | 中 | 添加缓存层 |

---

## 十、执行确认

本计划完成后，项目架构将实现：
1. Java与Python服务职责清晰分离
2. 统一的API网关和路由
3. 完善的企业级系统管理功能
4. 可靠的安全措施和错误处理
