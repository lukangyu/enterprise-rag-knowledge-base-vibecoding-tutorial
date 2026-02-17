# GraphRAG Backend

企业级GraphRAG知识库系统后端服务

## 项目结构

```
graphrag-backend/
├── graphrag-common/          # 公共模块
│   └── 统一响应、异常处理、常量定义
├── graphrag-system/          # 系统管理模块
│   └── 用户、角色、权限、日志管理
├── graphrag-document/        # 文档管理模块
│   └── 文档上传、解析、分块管理
├── graphrag-knowledge/       # 知识图谱模块
│   └── 实体抽取、关系抽取、图谱构建
├── graphrag-search/          # 检索问答模块
│   └── 向量检索、图遍历、融合重排、LLM问答
├── graphrag-gateway/         # 网关模块（启动入口）
│   └── 应用入口、统一配置
├── sql/                      # 数据库脚本
│   └── init-database.sql     # 数据库初始化脚本
├── docker-compose.yml        # Docker开发环境
├── mvnw.cmd                  # Maven Wrapper (Windows)
├── start.bat                 # 快速启动脚本 (Windows)
└── pom.xml                   # 父POM
```

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| JDK | 17+ | Java运行环境 |
| Spring Boot | 3.2.5 | 核心框架 |
| Spring Security | 6.x | 安全框架 |
| MyBatis Plus | 3.5.5 | ORM框架 |
| PostgreSQL | 15+ | 关系数据库 |
| Redis | 7.x | 缓存数据库 |
| Kafka | 3.6+ | 消息队列 |
| Neo4j | 5.x | 图数据库 |
| Milvus | 2.3+ | 向量数据库 |
| MinIO | 8.5+ | 对象存储 |
| Knife4j | 4.5.0 | API文档 |

## 快速开始

### 方式一：使用Docker Compose（推荐）

1. **启动基础服务**
```bash
# 启动PostgreSQL和Redis
docker-compose up -d postgres redis

# 启动所有服务
docker-compose up -d
```

2. **编译并运行**
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

3. **启动应用**
```bash
./mvnw spring-boot:run -pl graphrag-gateway
```

### 方式二：手动配置

1. **环境要求**
   - JDK 17 或更高版本
   - Maven 3.8+（或使用项目内置的Maven Wrapper）
   - PostgreSQL 15+
   - Redis 7+

2. **创建数据库**
```sql
CREATE DATABASE graphrag WITH ENCODING='UTF8';
```

3. **执行初始化脚本**
```bash
psql -U postgres -d graphrag -f sql/init-database.sql
```

4. **修改配置**
编辑 `graphrag-gateway/src/main/resources/application-dev.yml`

5. **编译运行**
```bash
./mvnw clean compile
./mvnw spring-boot:run -pl graphrag-gateway
```

## Docker服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 关系数据库 |
| Redis | 6379 | 缓存服务 |
| Kafka | 9092 | 消息队列 |
| Kafka UI | 8081 | Kafka管理界面 |
| MinIO | 9000/9001 | 对象存储 |
| Neo4j | 7474/7687 | 图数据库 |
| Milvus | 19530 | 向量数据库 |

## 配置说明

### 开发环境配置

编辑 `graphrag-gateway/src/main/resources/application-dev.yml`:

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/graphrag
    username: postgres
    password: postgres
  data:
    redis:
      host: localhost
      port: 6379
```

### 生产环境配置

使用环境变量或编辑 `application-prod.yml`:

```bash
export DB_HOST=your-db-host
export DB_USERNAME=your-username
export DB_PASSWORD=your-password
export REDIS_HOST=your-redis-host
```

## API文档

启动服务后访问：

- Swagger UI: http://localhost:8080/api/swagger-ui.html
- Knife4j: http://localhost:8080/api/doc.html

## 健康检查

- 健康检查: http://localhost:8080/api/health
- 就绪检查: http://localhost:8080/api/health/ready
- 存活检查: http://localhost:8080/api/health/live

## 数据库表结构

### 核心表

| 表名 | 说明 |
|------|------|
| users | 用户表 |
| roles | 角色表 |
| permissions | 权限表 |
| documents | 文档表 |
| document_chunks | 文档片段表 |
| entities | 实体表 |
| relations | 关系表 |
| chat_sessions | 对话会话表 |
| chat_messages | 对话消息表 |
| audit_logs | 审计日志表 |

### 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 超级管理员 |

## 开发指南

### 模块依赖关系

```
graphrag-gateway (启动入口)
    ├── graphrag-common (公共模块)
    ├── graphrag-system (系统管理)
    ├── graphrag-document (文档管理)
    ├── graphrag-knowledge (知识图谱)
    └── graphrag-search (检索问答)
```

### 代码规范

- 遵循阿里巴巴Java开发规范
- 使用Lombok简化代码
- 统一使用Result<T>响应格式
- 异常使用BusinessException

### 常用命令

```bash
# 编译项目
./mvnw clean compile

# 运行测试
./mvnw test

# 打包项目
./mvnw clean package -DskipTests

# 运行应用
./mvnw spring-boot:run -pl graphrag-gateway

# 查看依赖树
./mvnw dependency:tree
```

## 许可证

Apache License 2.0
