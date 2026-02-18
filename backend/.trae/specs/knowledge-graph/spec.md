# 知识图谱模块 Spec

## Why
实现企业级GraphRAG系统的知识图谱核心功能，包括实体抽取、关系抽取、图谱存储与查询，为智能问答提供多跳推理和证据链追溯能力。知识图谱模块是GraphRAG架构的核心组件，实现向量检索与图遍历融合的检索增强。

## What Changes
- 创建知识图谱服务模块（FastAPI）
- 实现基于LLM的实体抽取服务（Qwen2.5-Max）
- 实现基于LLM的关系抽取服务
- 实现Neo4j图谱存储与查询服务
- 实现图遍历与多跳查询服务
- 实现实体消歧与链接服务
- 实现证据链构建服务
- 提供知识图谱RESTful API接口
- 实现图谱统计与质量管理功能

## Impact
- Affected specs: ai-services（实体/关系抽取依赖文档解析）、检索问答模块（依赖图谱查询）
- Affected code: 新增kg-services目录，包含实体抽取、关系抽取、图谱存储、图遍历四个子模块

## ADDED Requirements

### Requirement: 实体抽取服务
系统SHALL提供基于LLM的实体抽取功能，支持多种实体类型的识别与抽取。

#### Scenario: 实体类型识别
- **WHEN** 接收到文本内容时
- **THEN** 系统调用Qwen2.5-Max识别实体，支持Person、Organization、Location、Product、Event、Concept等类型

#### Scenario: 实体属性抽取
- **WHEN** 识别到实体时
- **THEN** 系统抽取实体名称、类型、描述、别名等属性信息

#### Scenario: 批量实体抽取
- **WHEN** 接收到多个文本块时
- **THEN** 系统支持批量实体抽取处理，提高处理效率

#### Scenario: 实体去重
- **WHEN** 抽取到多个相同名称的实体时
- **THEN** 系统进行实体去重与合并处理

#### Scenario: 实体置信度计算
- **WHEN** 实体抽取完成时
- **THEN** 系统计算实体识别的置信度分数（0-1）

### Requirement: 关系抽取服务
系统SHALL提供基于LLM的关系抽取功能，识别实体之间的语义关系。

#### Scenario: 关系类型识别
- **WHEN** 接收到包含多个实体的文本时
- **THEN** 系统识别实体间关系，支持BELONGS_TO、CONTAINS、LOCATED_AT、CREATED_BY、AFFECTS、DEPENDS_ON等类型

#### Scenario: 关系证据提取
- **WHEN** 识别到关系时
- **THEN** 系统提取原文中支持该关系的证据文本

#### Scenario: 关系置信度计算
- **WHEN** 关系抽取完成时
- **THEN** 系统计算关系识别的置信度分数（0-1）

#### Scenario: 关系验证
- **WHEN** 关系置信度低于阈值时
- **THEN** 系统进行关系验证或过滤处理

### Requirement: 图谱存储服务
系统SHALL提供Neo4j图谱存储功能，支持实体和关系的持久化存储。

#### Scenario: 实体节点创建
- **WHEN** 新实体被识别时
- **THEN** 系统在Neo4j中创建实体节点，包含id、name、type、description等属性

#### Scenario: 关系边创建
- **WHEN** 新关系被识别时
- **THEN** 系统在Neo4j中创建关系边，包含type、evidence、confidence等属性

#### Scenario: 实体属性更新
- **WHEN** 实体信息变更时
- **THEN** 系统更新Neo4j中的实体节点属性

#### Scenario: 图谱索引创建
- **WHEN** 图谱存储完成时
- **THEN** 系统创建必要的索引以支持高效查询

### Requirement: 图遍历查询服务
系统SHALL提供图遍历与多跳查询功能，支持BFS、DFS、最短路径等算法。

#### Scenario: BFS遍历
- **WHEN** 用户请求广度优先遍历时
- **THEN** 系统从起始实体出发，按BFS算法遍历关联实体

#### Scenario: DFS遍历
- **WHEN** 用户请求深度优先遍历时
- **THEN** 系统从起始实体出发，按DFS算法遍历关联实体

#### Scenario: 多跳查询
- **WHEN** 用户请求多跳查询（2-4跳）时
- **THEN** 系统返回指定跳数内的关联实体和路径

#### Scenario: 路径查询
- **WHEN** 用户查询两个实体间的路径时
- **THEN** 系统返回最短路径或所有可行路径

#### Scenario: 遍历性能
- **WHEN** 执行图遍历查询时
- **THEN** 响应时间≤100ms

### Requirement: 实体消歧服务
系统SHALL提供实体消歧与链接功能，解决同名实体歧义问题。

#### Scenario: 实体候选检索
- **WHEN** 接收到实体名称时
- **THEN** 系统检索图谱中的候选实体列表

#### Scenario: 上下文匹配
- **WHEN** 存在多个候选实体时
- **THEN** 系统根据上下文信息计算匹配度

#### Scenario: 最佳匹配选择
- **WHEN** 候选实体匹配完成时
- **THEN** 系统返回置信度最高的匹配实体

### Requirement: 证据链构建服务
系统SHALL提供证据链构建功能，生成可解释的关系路径。

#### Scenario: 证据链生成
- **WHEN** 查询涉及多跳关系时
- **THEN** 系统生成包含实体路径、关系路径、来源文档的证据链

#### Scenario: 证据链置信度
- **WHEN** 证据链构建完成时
- **THEN** 系统计算整条证据链的综合置信度

#### Scenario: 证据链可视化数据
- **WHEN** 返回证据链时
- **THEN** 系统提供可视化所需的节点和边数据

### Requirement: 知识图谱API接口
系统SHALL提供RESTful API接口，遵循项目API设计规范。

#### Scenario: 实体查询接口
- **WHEN** 调用GET /api/v1/kg/entities接口时
- **THEN** 系统返回符合条件的实体列表，支持分页和过滤

#### Scenario: 实体详情接口
- **WHEN** 调用GET /api/v1/kg/entities/{entity_id}接口时
- **THEN** 系统返回实体详情，包括关联关系

#### Scenario: 关系查询接口
- **WHEN** 调用GET /api/v1/kg/relations接口时
- **THEN** 系统返回符合条件的关系列表

#### Scenario: 图遍历接口
- **WHEN** 调用POST /api/v1/kg/traverse接口时
- **THEN** 系统执行图遍历并返回路径和关联实体

#### Scenario: 路径查询接口
- **WHEN** 调用POST /api/v1/kg/path接口时
- **THEN** 系统返回两实体间的路径

#### Scenario: 子图查询接口
- **WHEN** 调用POST /api/v1/kg/subgraph接口时
- **THEN** 系统返回指定实体的子图数据

#### Scenario: 知识抽取接口
- **WHEN** 调用POST /api/v1/kg/extract接口时
- **THEN** 系统触发知识抽取任务

#### Scenario: 实体消歧接口
- **WHEN** 调用POST /api/v1/kg/entities/resolve接口时
- **THEN** 系统返回实体消歧结果

### Requirement: 图谱统计与管理
系统SHALL提供图谱统计和管理功能。

#### Scenario: 图谱统计
- **WHEN** 请求图谱统计信息时
- **THEN** 系统返回实体数量、关系数量、类型分布等统计信息

#### Scenario: 图谱质量评估
- **WHEN** 执行图谱质量评估时
- **THEN** 系统评估图谱完整性、一致性、准确性

#### Scenario: 实体/关系编辑
- **WHEN** 用户编辑实体或关系时
- **THEN** 系统支持实体属性更新和关系修改

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
