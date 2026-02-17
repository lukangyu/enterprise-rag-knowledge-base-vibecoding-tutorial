# Tasks

## 项目结构搭建

- [x] Task 1: 创建FastAPI项目基础结构
  - [x] SubTask 1.1: 创建ai-services目录结构（app、services、models、config、tests等）
  - [x] SubTask 1.2: 创建requirements.txt依赖文件
  - [x] SubTask 1.3: 创建pyproject.toml项目配置文件
  - [x] SubTask 1.4: 创建Dockerfile和docker-compose配置
  - [x] SubTask 1.5: 创建.env.example环境变量模板文件

- [x] Task 2: 实现配置管理模块
  - [x] SubTask 2.1: 创建config/settings.py配置类，使用pydantic-settings
  - [x] SubTask 2.2: 创建config/logging.py日志配置
  - [x] SubTask 2.3: 创建config/database.py数据库连接配置（Milvus）
  - [x] SubTask 2.4: 创建config/dependencies.py依赖注入配置

## 文档解析服务

- [x] Task 3: 实现PDF解析器
  - [x] SubTask 3.1: 创建services/parser/pdf_parser.py，使用PyMuPDF解析PDF
  - [x] SubTask 3.2: 实现文本提取功能，保留文档结构
  - [x] SubTask 3.3: 实现大文件流式解析（≥100MB）
  - [x] SubTask 3.4: 实现解析异常处理和错误日志记录

- [x] Task 4: 实现Word解析器
  - [x] SubTask 4.1: 创建services/parser/word_parser.py，使用python-docx解析Word
  - [x] SubTask 4.2: 实现文本提取功能，保留文档结构
  - [x] SubTask 4.3: 实现表格和列表解析
  - [x] SubTask 4.4: 实现解析异常处理

- [x] Task 5: 实现Markdown解析器
  - [x] SubTask 5.1: 创建services/parser/markdown_parser.py
  - [x] SubTask 5.2: 实现Markdown文本解析，保留标题层级
  - [x] SubTask 5.3: 实现代码块和列表解析
  - [x] SubTask 5.4: 实现元数据提取（frontmatter）

- [x] Task 6: 实现文本清洗和预处理
  - [x] SubTask 6.1: 创建services/parser/text_cleaner.py
  - [x] SubTask 6.2: 实现空白字符清理
  - [x] SubTask 6.3: 实现编码格式检测和转换
  - [x] SubTask 6.4: 实现文本规范化处理

- [x] Task 7: 实现解析服务API
  - [x] SubTask 7.1: 创建models/parser_models.py请求/响应模型
  - [x] SubTask 7.2: 创建api/parser.py路由，实现POST /api/v1/parse接口
  - [x] SubTask 7.3: 实现文件类型自动检测和解析器选择
  - [x] SubTask 7.4: 实现解析进度和状态返回

## 文档分块服务

- [x] Task 8: 实现语义分块算法
  - [x] SubTask 8.1: 创建services/chunker/semantic_chunker.py
  - [x] SubTask 8.2: 实现基于句子边界的分块
  - [x] SubTask 8.3: 实现基于段落语义的分块
  - [x] SubTask 8.4: 实现语义完整性检测

- [x] Task 9: 实现固定大小分块算法
  - [x] SubTask 9.1: 创建services/chunker/fixed_chunker.py
  - [x] SubTask 9.2: 实现可配置块大小（默认512字符）
  - [x] SubTask 9.3: 实现可配置重叠率（默认10%）
  - [x] SubTask 9.4: 实现边界智能处理（避免截断单词）

- [x] Task 10: 实现分块策略配置
  - [x] SubTask 10.1: 创建services/chunker/chunk_config.py配置类
  - [x] SubTask 10.2: 实现分块策略选择逻辑
  - [x] SubTask 10.3: 实现自动策略选择（基于文档类型和内容）
  - [x] SubTask 10.4: 实现分块元数据生成

- [x] Task 11: 实现分块服务API
  - [x] SubTask 11.1: 创建models/chunker_models.py请求/响应模型
  - [x] SubTask 11.2: 创建api/chunker.py路由，实现POST /api/v1/chunk接口
  - [x] SubTask 11.3: 实现分块策略参数配置
  - [x] SubTask 11.4: 实现分块结果标准格式输出

## 向量化服务

- [x] Task 12: 实现Qwen-Embedding集成
  - [x] SubTask 12.1: 创建services/embedding/qwen_embedding.py
  - [x] SubTask 12.2: 实现Qwen-Embedding API调用封装
  - [x] SubTask 12.3: 实现批量向量化处理
  - [x] SubTask 12.4: 实现API调用重试和异常处理

- [x] Task 13: 实现Milvus向量存储
  - [x] SubTask 13.1: 创建services/embedding/milvus_client.py
  - [x] SubTask 13.2: 实现向量集合创建和配置
  - [x] SubTask 13.3: 实现向量插入和更新
  - [x] SubTask 13.4: 实现向量删除和批量操作

- [x] Task 14: 实现向量检索
  - [x] SubTask 14.1: 实现相似向量检索
  - [x] SubTask 14.2: 实现过滤条件支持
  - [x] SubTask 14.3: 实现向量索引优化配置
  - [x] SubTask 14.4: 实现检索性能监控（目标≤300ms）

- [x] Task 15: 实现向量化服务API
  - [x] SubTask 15.1: 创建models/embedding_models.py请求/响应模型
  - [x] SubTask 15.2: 创建api/embedding.py路由，实现POST /api/v1/embed接口
  - [x] SubTask 15.3: 实现POST /api/v1/search向量检索接口
  - [x] SubTask 15.4: 实现批量操作接口

## 服务集成与监控

- [x] Task 16: 实现主应用和路由整合
  - [x] SubTask 16.1: 创建app/main.py FastAPI主应用
  - [x] SubTask 16.2: 整合解析、分块、向量化路由
  - [x] SubTask 16.3: 配置CORS和中间件
  - [x] SubTask 16.4: 配置Swagger UI文档

- [x] Task 17: 实现健康检查和监控
  - [x] SubTask 17.1: 创建api/health.py健康检查路由
  - [x] SubTask 17.2: 实现服务状态检查
  - [x] SubTask 17.3: 实现依赖组件状态检查（Milvus、Qwen API）
  - [x] SubTask 17.4: 实现性能指标收集

- [x] Task 18: 实现异常处理
  - [x] SubTask 18.1: 创建exceptions.py自定义异常类
  - [x] SubTask 18.2: 创建api/error_handlers.py全局异常处理器
  - [x] SubTask 18.3: 实现统一错误响应格式
  - [x] SubTask 18.4: 实现错误日志记录

## 测试

- [x] Task 19: 编写单元测试
  - [x] SubTask 19.1: 创建tests/test_parser.py解析器测试
  - [x] SubTask 19.2: 创建tests/test_chunker.py分块器测试
  - [x] SubTask 19.3: 创建tests/test_embedding.py向量化测试
  - [x] SubTask 19.4: 创建tests/conftest.py测试配置和fixtures

- [x] Task 20: 编写集成测试
  - [x] SubTask 20.1: 创建tests/test_api.py API接口测试
  - [x] SubTask 20.2: 创建tests/test_integration.py服务集成测试
  - [x] SubTask 20.3: 实现测试覆盖率报告（目标≥80%）
  - [x] SubTask 20.4: 创建测试数据文件

# Task Dependencies
- [Task 2] depends on [Task 1] (配置管理依赖项目结构)
- [Task 3-7] depends on [Task 1, Task 2] (解析服务依赖基础结构和配置)
- [Task 8-11] depends on [Task 1, Task 2] (分块服务依赖基础结构和配置)
- [Task 12-15] depends on [Task 1, Task 2] (向量化服务依赖基础结构和配置)
- [Task 16] depends on [Task 7, Task 11, Task 15] (主应用整合依赖各服务API)
- [Task 17] depends on [Task 16] (监控依赖主应用)
- [Task 18] depends on [Task 16] (异常处理依赖主应用)
- [Task 19] depends on [Task 3-15] (单元测试依赖各服务实现)
- [Task 20] depends on [Task 16-18] (集成测试依赖完整服务)
