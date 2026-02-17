# 文档处理Pipeline Spec

## Why
实现企业级GraphRAG系统的文档处理核心流程，支持多格式文档的上传、解析、分块、向量化和异步任务管理，为知识图谱构建和智能问答提供数据基础。

## What Changes
- 创建文档实体类和数据库表结构
- 实现文档上传、查询、删除等管理API
- 实现文档处理状态机管理
- 创建Kafka异步任务处理机制
- 实现任务状态追踪和进度查询

## Impact
- Affected specs: 文档管理模块、异步任务处理
- Affected code: graphrag-document模块、graphrag-common模块

## ADDED Requirements

### Requirement: 文档实体设计
系统SHALL提供完整的文档实体模型，支持文档元数据管理和状态追踪。

#### Scenario: 文档实体创建
- **WHEN** 用户上传文档时
- **THEN** 系统创建Document实体，包含id、title、source、docType、filePath、fileSize、contentHash、status、metadata等字段

#### Scenario: 文档状态流转
- **WHEN** 文档处理状态变更时
- **THEN** 系统按状态机规则流转：PENDING -> PARSING -> CHUNKING -> EMBEDDING -> COMPLETED 或 FAILED

### Requirement: 文档上传接口
系统SHALL提供文档上传接口，支持多格式文档上传和元数据设置。

#### Scenario: 文档上传成功
- **WHEN** 用户通过POST /api/v1/documents/upload上传有效文档
- **THEN** 系统返回文档ID和pending状态，文件存储到MinIO

#### Scenario: 文档上传失败
- **WHEN** 上传文件格式不支持或文件损坏
- **THEN** 系统返回错误信息，不创建文档记录

### Requirement: 文档元数据管理
系统SHALL提供文档元数据的CRUD操作接口。

#### Scenario: 元数据更新
- **WHEN** 用户通过PUT /api/v1/documents/{id}/metadata更新元数据
- **THEN** 系统更新文档的metadata字段并记录更新时间

### Requirement: 文档状态管理
系统SHALL实现文档处理状态机，管理文档处理生命周期。

#### Scenario: 状态自动流转
- **WHEN** 文档解析完成时
- **THEN** 状态从PARSING自动流转到CHUNKING

#### Scenario: 状态异常处理
- **WHEN** 处理过程发生错误
- **THEN** 状态流转到FAILED并记录错误信息

### Requirement: 文档查询接口
系统SHALL提供文档列表分页查询和详情查询接口。

#### Scenario: 分页查询
- **WHEN** 用户通过GET /api/v1/documents查询文档列表
- **THEN** 系统返回分页结果，支持按状态、类型、时间筛选

#### Scenario: 详情查询
- **WHEN** 用户通过GET /api/v1/documents/{id}查询文档详情
- **THEN** 系统返回完整文档信息，包含处理状态和进度

### Requirement: 文档删除接口
系统SHALL实现文档级联删除，清理关联数据。

#### Scenario: 级联删除
- **WHEN** 用户通过DELETE /api/v1/documents/{id}删除文档
- **THEN** 系统删除MinIO文件、数据库记录、向量数据、图谱节点

### Requirement: Kafka消息队列集成
系统SHALL通过Kafka实现文档处理异步任务调度。

#### Scenario: 任务消息发送
- **WHEN** 文档上传成功后
- **THEN** 系统发送文档处理消息到Kafka topic

#### Scenario: 消息消费处理
- **WHEN** 消费者收到文档处理消息
- **THEN** 系统调用相应处理服务执行任务

### Requirement: 任务状态追踪
系统SHALL提供任务状态追踪管理器，记录处理进度。

#### Scenario: 进度记录
- **WHEN** 文档处理各阶段完成时
- **THEN** 系统更新任务进度百分比和当前阶段

### Requirement: 任务进度查询
系统SHALL提供任务进度查询接口。

#### Scenario: 进度查询
- **WHEN** 用户通过GET /api/v1/documents/{id}/progress查询进度
- **THEN** 系统返回当前阶段、进度百分比、预计剩余时间

### Requirement: 任务重试机制
系统SHALL实现任务失败重试策略。

#### Scenario: 自动重试
- **WHEN** 任务执行失败且重试次数未超限
- **THEN** 系统自动重新发送消息到延迟队列

#### Scenario: 重试次数限制
- **WHEN** 任务重试次数达到上限（默认3次）
- **THEN** 系统标记任务为最终失败，发送告警通知

## MODIFIED Requirements
无

## REMOVED Requirements
无
