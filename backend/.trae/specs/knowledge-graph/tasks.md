# Tasks

## 项目结构搭建

- [x] Task 1: 创建知识图谱服务基础结构
  - [x] SubTask 1.1: 创建kg-services目录结构（services、models、api、config、tests等）
  - [x] SubTask 1.2: 更新requirements.txt添加Neo4j驱动等依赖
  - [x] SubTask 1.3: 创建kg服务的Dockerfile配置
  - [x] SubTask 1.4: 创建知识图谱相关环境变量配置

- [x] Task 2: 实现配置管理模块
  - [x] SubTask 2.1: 创建config/kg_settings.py知识图谱配置类
  - [x] SubTask 2.2: 创建config/neo4j_config.py Neo4j连接配置
  - [x] SubTask 2.3: 创建config/llm_config.py LLM服务配置

## 实体抽取服务

- [x] Task 3: 实现实体类型定义
  - [x] SubTask 3.1: 创建models/entity.py实体数据模型
  - [x] SubTask 3.2: 定义EntityType枚举（Person、Organization、Location、Product、Event、Concept）
  - [x] SubTask 3.3: 创建实体属性模型（name、type、description、alias、confidence）

- [x] Task 4: 实现LLM实体抽取器
  - [x] SubTask 4.1: 创建services/entity/llm_extractor.py
  - [x] SubTask 4.2: 设计实体抽取Prompt模板
  - [x] SubTask 4.3: 实现Qwen2.5-Max API调用封装
  - [x] SubTask 4.4: 实现JSON格式响应解析

- [x] Task 5: 实现实体处理逻辑
  - [x] SubTask 5.1: 创建services/entity/entity_processor.py
  - [x] SubTask 5.2: 实现实体去重算法
  - [x] SubTask 5.3: 实现实体合并逻辑
  - [x] SubTask 5.4: 实现实体置信度计算

- [x] Task 6: 实现实体抽取API
  - [x] SubTask 6.1: 创建models/entity_models.py请求/响应模型
  - [x] SubTask 6.2: 创建api/entity.py路由
  - [x] SubTask 6.3: 实现实体抽取接口
  - [x] SubTask 6.4: 实现批量实体抽取接口

## 关系抽取服务

- [x] Task 7: 实现关系类型定义
  - [x] SubTask 7.1: 创建models/relation.py关系数据模型
  - [x] SubTask 7.2: 定义RelationType枚举（BELONGS_TO、CONTAINS、LOCATED_AT、CREATED_BY、AFFECTS、DEPENDS_ON）
  - [x] SubTask 7.3: 创建关系属性模型（head_entity、relation_type、tail_entity、evidence、confidence）

- [x] Task 8: 实现LLM关系抽取器
  - [x] SubTask 8.1: 创建services/relation/llm_extractor.py
  - [x] SubTask 8.2: 设计关系抽取Prompt模板
  - [x] SubTask 8.3: 实现基于已识别实体的关系抽取
  - [x] SubTask 8.4: 实现关系置信度计算

- [x] Task 9: 实现关系处理逻辑
  - [x] SubTask 9.1: 创建services/relation/relation_processor.py
  - [x] SubTask 9.2: 实现关系验证逻辑
  - [x] SubTask 9.3: 实现低置信度关系过滤
  - [x] SubTask 9.4: 实现关系去重

- [x] Task 10: 实现关系抽取API
  - [x] SubTask 10.1: 创建models/relation_models.py请求/响应模型
  - [x] SubTask 10.2: 创建api/relation.py路由
  - [x] SubTask 10.3: 实现关系抽取接口

## 图谱存储服务

- [x] Task 11: 实现Neo4j客户端
  - [x] SubTask 11.1: 创建services/graph/neo4j_client.py
  - [x] SubTask 11.2: 实现Neo4j连接池管理
  - [x] SubTask 11.3: 实现会话管理
  - [x] SubTask 11.4: 实现连接健康检查

- [x] Task 12: 实现实体存储
  - [x] SubTask 12.1: 创建services/graph/entity_repository.py
  - [x] SubTask 12.2: 实现实体节点创建（CREATE/MERGE）
  - [x] SubTask 12.3: 实现实体属性更新
  - [x] SubTask 12.4: 实现实体查询与删除

- [x] Task 13: 实现关系存储
  - [x] SubTask 13.1: 创建services/graph/relation_repository.py
  - [x] SubTask 13.2: 实现关系边创建
  - [x] SubTask 13.3: 实现关系属性更新
  - [x] SubTask 13.4: 实现关系查询与删除

- [x] Task 14: 实现图谱索引
  - [x] SubTask 14.1: 创建实体名称索引
  - [x] SubTask 14.2: 创建实体类型索引
  - [x] SubTask 14.3: 创建关系类型索引
  - [x] SubTask 14.4: 创建全文搜索索引

## 图遍历查询服务

- [x] Task 15: 实现图遍历引擎
  - [x] SubTask 15.1: 创建services/graph/traversal_engine.py
  - [x] SubTask 15.2: 实现BFS遍历算法
  - [x] SubTask 15.3: 实现DFS遍历算法
  - [x] SubTask 15.4: 实现最短路径算法（Dijkstra）

- [x] Task 16: 实现多跳查询
  - [x] SubTask 16.1: 创建services/graph/multi_hop_query.py
  - [x] SubTask 16.2: 实现2跳查询
  - [x] SubTask 16.3: 实现3-4跳查询
  - [x] SubTask 16.4: 实现查询结果缓存

- [x] Task 17: 实现路径查询
  - [x] SubTask 17.1: 创建services/graph/path_query.py
  - [x] SubTask 17.2: 实现两实体间路径查询
  - [x] SubTask 17.3: 实现所有路径查询
  - [x] SubTask 17.4: 实现路径置信度计算

- [x] Task 18: 实现图遍历API
  - [x] SubTask 18.1: 创建models/graph_models.py请求/响应模型
  - [x] SubTask 18.2: 创建api/graph.py路由
  - [x] SubTask 18.3: 实现POST /api/v1/kg/traverse接口
  - [x] SubTask 18.4: 实现POST /api/v1/kg/path接口
  - [x] SubTask 18.5: 实现POST /api/v1/kg/subgraph接口

## 实体消歧服务

- [x] Task 19: 实现实体消歧器
  - [x] SubTask 19.1: 创建services/entity/entity_resolver.py
  - [x] SubTask 19.2: 实现实体候选检索
  - [x] SubTask 19.3: 实现上下文相似度计算
  - [x] SubTask 19.4: 实现最佳匹配选择

- [x] Task 20: 实现实体消歧API
  - [x] SubTask 20.1: 创建models/resolution_models.py请求/响应模型
  - [x] SubTask 20.2: 实现POST /api/v1/kg/entities/resolve接口

## 证据链构建服务

- [x] Task 21: 实现证据链构建器
  - [x] SubTask 21.1: 创建services/evidence/chain_builder.py
  - [x] SubTask 21.2: 实现证据链路径提取
  - [x] SubTask 21.3: 实现来源文档关联
  - [x] SubTask 21.4: 实现证据链置信度计算

- [x] Task 22: 实现证据链可视化数据
  - [x] SubTask 22.1: 创建services/evidence/visualization.py
  - [x] SubTask 22.2: 实现节点数据格式化
  - [x] SubTask 22.3: 实现边数据格式化

## 知识抽取Pipeline

- [x] Task 23: 实现知识抽取Pipeline
  - [x] SubTask 23.1: 创建services/pipeline/kg_pipeline.py
  - [x] SubTask 23.2: 实现实体抽取→关系抽取→图谱存储流程
  - [x] SubTask 23.3: 实现异步任务处理
  - [x] SubTask 23.4: 实现进度追踪

- [x] Task 24: 实现知识抽取API
  - [x] SubTask 24.1: 创建models/extraction_models.py请求/响应模型
  - [x] SubTask 24.2: 实现POST /api/v1/kg/extract接口
  - [x] SubTask 24.3: 实现抽取任务状态查询

## 图谱统计与管理

- [x] Task 25: 实现图谱统计服务
  - [x] SubTask 25.1: 创建services/graph/statistics.py
  - [x] SubTask 25.2: 实现实体统计（数量、类型分布）
  - [x] SubTask 25.3: 实现关系统计（数量、类型分布）
  - [x] SubTask 25.4: 实现图谱密度计算

- [x] Task 26: 实现图谱质量评估
  - [x] SubTask 26.1: 创建services/graph/quality_evaluator.py
  - [x] SubTask 26.2: 实现完整性评估
  - [x] SubTask 26.3: 实现一致性检查
  - [x] SubTask 26.4: 实现准确性评估

- [x] Task 27: 实现图谱管理API
  - [x] SubTask 27.1: 创建api/kg_management.py路由
  - [x] SubTask 27.2: 实现图谱统计接口
  - [x] SubTask 27.3: 实现实体/关系编辑接口
  - [x] SubTask 27.4: 实现图谱质量评估接口

## 服务集成与监控

- [x] Task 28: 实现主应用和路由整合
  - [x] SubTask 28.1: 创建app/kg_main.py FastAPI主应用
  - [x] SubTask 28.2: 整合实体、关系、图谱路由
  - [x] SubTask 28.3: 配置CORS和中间件
  - [x] SubTask 28.4: 配置Swagger UI文档

- [x] Task 29: 实现健康检查和监控
  - [x] SubTask 29.1: 创建api/health.py健康检查路由
  - [x] SubTask 29.2: 实现Neo4j连接状态检查
  - [x] SubTask 29.3: 实现LLM服务状态检查
  - [x] SubTask 29.4: 实现性能指标收集

- [x] Task 30: 实现异常处理
  - [x] SubTask 30.1: 创建exceptions/kg_exceptions.py自定义异常类
  - [x] SubTask 30.2: 创建api/error_handlers.py全局异常处理器
  - [x] SubTask 30.3: 实现统一错误响应格式
  - [x] SubTask 30.4: 实现错误日志记录

## 测试

- [x] Task 31: 编写单元测试
  - [x] SubTask 31.1: 创建tests/test_entity_extractor.py实体抽取测试
  - [x] SubTask 31.2: 创建tests/test_relation_extractor.py关系抽取测试
  - [x] SubTask 31.3: 创建tests/test_graph_repository.py图谱存储测试
  - [x] SubTask 31.4: 创建tests/test_traversal.py图遍历测试
  - [x] SubTask 31.5: 创建tests/conftest.py测试配置和fixtures

- [x] Task 32: 编写集成测试
  - [x] SubTask 32.1: 创建tests/test_kg_api.py API接口测试
  - [x] SubTask 32.2: 创建tests/test_kg_pipeline.py Pipeline集成测试
  - [x] SubTask 32.3: 实现测试覆盖率报告（目标≥80%）
  - [x] SubTask 32.4: 创建测试数据文件

# Task Dependencies
- [Task 2] depends on [Task 1] (配置管理依赖项目结构)
- [Task 3-6] depends on [Task 1, Task 2] (实体抽取服务依赖基础结构和配置)
- [Task 7-10] depends on [Task 1, Task 2] (关系抽取服务依赖基础结构和配置)
- [Task 11-14] depends on [Task 1, Task 2] (图谱存储服务依赖基础结构和配置)
- [Task 15-18] depends on [Task 11-14] (图遍历服务依赖图谱存储)
- [Task 19-20] depends on [Task 11-14] (实体消歧依赖图谱存储)
- [Task 21-22] depends on [Task 15-18] (证据链构建依赖图遍历)
- [Task 23-24] depends on [Task 3-10, Task 11-14] (知识抽取Pipeline依赖实体抽取、关系抽取和图谱存储)
- [Task 25-27] depends on [Task 11-14] (图谱统计与管理依赖图谱存储)
- [Task 28] depends on [Task 6, Task 10, Task 18, Task 20, Task 24, Task 27] (主应用整合依赖各服务API)
- [Task 29] depends on [Task 28] (监控依赖主应用)
- [Task 30] depends on [Task 28] (异常处理依赖主应用)
- [Task 31] depends on [Task 3-22] (单元测试依赖各服务实现)
- [Task 32] depends on [Task 28-30] (集成测试依赖完整服务)
