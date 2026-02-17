# AI服务层 Python/FastAPI 模块 Spec

## Why
实现企业级GraphRAG系统的AI服务层核心功能，包括文档解析、文档分块和向量化服务，为知识图谱构建和智能问答提供数据基础。这些服务使用Python/FastAPI开发，与Spring Boot业务服务层协同工作。

## What Changes
- 创建FastAPI项目结构和配置
- 实现多格式文档解析服务（PDF、Word、Markdown）
- 实现智能文档分块服务（语义分块、固定大小分块）
- 实现向量化服务（Qwen-Embedding集成、Milvus存储）
- 提供RESTful API接口供Spring Boot服务调用
- 实现服务监控、日志记录和异常处理

## Impact
- Affected specs: 文档处理Pipeline、知识图谱模块
- Affected code: 新增ai-services目录，包含解析、分块、向量化三个子模块

## ADDED Requirements

### Requirement: FastAPI项目架构
系统SHALL提供标准的FastAPI项目结构，支持模块化开发和部署。

#### Scenario: 项目初始化
- **WHEN** 开发人员创建AI服务项目时
- **THEN** 系统提供标准的项目结构，包括app、services、models、config、tests等目录

#### Scenario: 配置管理
- **WHEN** 服务启动时
- **THEN** 系统从环境变量和配置文件加载配置，支持多环境配置

### Requirement: 文档解析服务
系统SHALL提供多格式文档解析功能，支持PDF、Word、Markdown等格式。

#### Scenario: PDF解析
- **WHEN** 用户上传PDF文档时
- **THEN** 系统提取文本内容，保留文档结构信息（标题层级、列表等），解析准确率≥95%

#### Scenario: Word解析
- **WHEN** 用户上传Word文档（.docx）时
- **THEN** 系统提取文本内容，保留文档结构和格式信息

#### Scenario: Markdown解析
- **WHEN** 用户上传Markdown文档时
- **THEN** 系统提取文本内容，保留标题层级和格式标记

#### Scenario: 大文件处理
- **WHEN** 上传文件≥100MB时
- **THEN** 系统采用流式解析，避免内存溢出

#### Scenario: 解析异常处理
- **WHEN** 文档解析失败时
- **THEN** 系统记录错误日志，返回明确的错误信息

### Requirement: 文档分块服务
系统SHALL提供智能文档分块功能，支持语义分块和固定大小分块策略。

#### Scenario: 语义分块
- **WHEN** 用户选择语义分块策略时
- **THEN** 系统基于文本语义关联性进行智能分块，确保语义完整性

#### Scenario: 固定大小分块
- **WHEN** 用户选择固定大小分块策略时
- **THEN** 系统按可配置的块大小（默认512字符）和重叠率（默认10%）进行分块

#### Scenario: 分块策略选择
- **WHEN** 调用方指定分块方式时
- **THEN** 系统按指定策略分块；若未指定，自动选择最优策略

#### Scenario: 分块元数据输出
- **WHEN** 分块完成时
- **THEN** 系统输出包含块ID、原始文档ID、块内容、位置信息及分块元数据的标准格式

### Requirement: 向量化服务
系统SHALL提供文本向量化功能，支持Qwen-Embedding模型和Milvus向量存储。

#### Scenario: 文本向量化
- **WHEN** 接收到文本块时
- **THEN** 系统调用Qwen-Embedding模型生成向量表示

#### Scenario: 批量向量化
- **WHEN** 接收到多个文本块时
- **THEN** 系统支持批量向量化处理，提高处理效率

#### Scenario: 向量存储
- **WHEN** 向量生成完成时
- **THEN** 系统将向量存储到Milvus向量数据库，建立索引

#### Scenario: 向量检索
- **WHEN** 接收到查询向量时
- **THEN** 系统在Milvus中检索相似向量，响应时间≤300ms

#### Scenario: 向量维度处理
- **WHEN** 需要统一向量维度时
- **THEN** 系统支持维度转换或降维处理

### Requirement: API接口设计
系统SHALL提供RESTful API接口，遵循FastAPI最佳实践。

#### Scenario: 解析接口
- **WHEN** 调用POST /api/v1/parse接口时
- **THEN** 系统接收文档文件，返回解析后的文本内容和结构信息

#### Scenario: 分块接口
- **WHEN** 调用POST /api/v1/chunk接口时
- **THEN** 系统接收文本内容，返回分块结果

#### Scenario: 向量化接口
- **WHEN** 调用POST /api/v1/embed接口时
- **THEN** 系统接收文本块，返回向量ID和存储状态

#### Scenario: API文档
- **WHEN** 访问/docs路径时
- **THEN** 系统提供Swagger UI自动生成的API文档

### Requirement: 服务监控与日志
系统SHALL提供服务监控和日志记录功能。

#### Scenario: 日志记录
- **WHEN** 执行关键操作时
- **THEN** 系统记录操作日志，包含时间戳、操作类型、执行结果

#### Scenario: 性能指标
- **WHEN** 服务运行时
- **THEN** 系统记录关键性能指标（处理时间、成功率等）

#### Scenario: 健康检查
- **WHEN** 调用/health接口时
- **THEN** 系统返回服务状态和依赖组件状态

### Requirement: 测试覆盖
系统SHALL提供完整的单元测试和集成测试。

#### Scenario: 单元测试
- **WHEN** 运行单元测试时
- **THEN** 代码覆盖率≥80%

#### Scenario: 集成测试
- **WHEN** 运行集成测试时
- **THEN** 验证API接口和服务集成正确性

## MODIFIED Requirements
无

## REMOVED Requirements
无
