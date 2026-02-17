# 阶段一基础设施搭建完善 Spec

## Why
项目骨架、数据库初始化、Docker Compose环境和认证授权模块已完成，但基础设施层仍有部分组件需要完善，包括日志配置优化、MinIO对象存储集成、Kafka Topic初始化脚本、以及相关单元测试，以确保基础设施的完整性和稳定性。

## What Changes
- 完善Logback日志配置，支持多环境配置和日志分级
- 添加MinIO对象存储客户端配置和服务类
- 创建Kafka Topic初始化脚本和配置
- 添加基础设施组件的单元测试
- 完善Redis缓存工具类

## Impact
- Affected specs: 基础设施层
- Affected code: graphrag-common, graphrag-gateway

## ADDED Requirements

### Requirement: 日志配置完善
系统SHALL提供完善的日志配置，支持多环境（开发、测试、生产）配置。

#### Scenario: 开发环境日志输出
- **WHEN** 应用在开发环境运行
- **THEN** 日志输出到控制台，级别为DEBUG，格式包含时间、级别、类名、消息

#### Scenario: 生产环境日志输出
- **WHEN** 应用在生产环境运行
- **THEN** 日志输出到文件，按日期滚动，级别为INFO，保留30天

### Requirement: MinIO对象存储集成
系统SHALL集成MinIO对象存储服务，支持文档文件的存储和管理。

#### Scenario: MinIO客户端初始化
- **WHEN** 应用启动时
- **THEN** 自动初始化MinIO客户端，创建默认存储桶

#### Scenario: 文件上传
- **WHEN** 用户上传文档文件
- **THEN** 文件被存储到MinIO，返回文件访问路径

### Requirement: Kafka Topic初始化
系统SHALL提供Kafka Topic初始化脚本，确保消息队列就绪。

#### Scenario: Topic自动创建
- **WHEN** Kafka服务启动时
- **THEN** 自动创建业务所需的Topic分区

### Requirement: Redis缓存工具类
系统SHALL提供Redis缓存工具类，简化缓存操作。

#### Scenario: 缓存数据存储
- **WHEN** 调用缓存工具存储数据
- **THEN** 数据被正确存储到Redis，支持过期时间设置

#### Scenario: 缓存数据读取
- **WHEN** 调用缓存工具读取数据
- **THEN** 返回缓存的数据，若不存在返回null

### Requirement: 基础设施单元测试
系统SHALL为基础设施组件提供单元测试，验证功能的正确性。

#### Scenario: MinIO服务测试
- **WHEN** 执行MinIO服务测试
- **THEN** 验证文件上传、下载、删除功能正常

#### Scenario: Redis缓存测试
- **WHEN** 执行Redis缓存测试
- **THEN** 验证缓存的存取、过期、删除功能正常

## MODIFIED Requirements
无

## REMOVED Requirements
无
