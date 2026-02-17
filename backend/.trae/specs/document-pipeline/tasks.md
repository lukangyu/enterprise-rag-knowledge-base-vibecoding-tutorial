# Tasks

- [x] Task 1: 创建文档实体类和数据库表结构
  - [x] SubTask 1.1: 创建Document实体类，包含id、title、source、docType、filePath、fileSize、contentHash、status、metadata等字段
  - [x] SubTask 1.2: 创建DocumentChunk实体类，包含id、docId、content、position、tokenCount、embeddingId、metadata字段
  - [x] SubTask 1.3: 创建DocumentMapper和DocumentChunkMapper接口
  - [x] SubTask 1.4: 创建数据库初始化SQL脚本，添加documents和document_chunks表

- [x] Task 2: 实现文档状态枚举和状态机
  - [x] SubTask 2.1: 创建DocumentStatus枚举类，定义PENDING、PARSING、CHUNKING、EMBEDDING、COMPLETED、FAILED状态
  - [x] SubTask 2.2: 创建DocumentStatusMachine状态机类，实现状态流转逻辑和校验
  - [x] SubTask 2.3: 创建状态流转事件类DocumentStatusEvent

- [x] Task 3: 实现文档上传接口
  - [x] SubTask 3.1: 创建DocumentController，实现POST /api/v1/documents/upload上传接口
  - [x] SubTask 3.2: 创建DocumentService接口和DocumentServiceImpl实现类
  - [x] SubTask 3.3: 实现文件上传到MinIO的逻辑
  - [x] SubTask 3.4: 创建上传请求DTO和响应DTO
  - [x] SubTask 3.5: 添加文件类型校验（PDF、Word、Markdown、TXT）

- [x] Task 4: 实现文档元数据管理接口
  - [x] SubTask 4.1: 实现PUT /api/v1/documents/{id}/metadata元数据更新接口
  - [x] SubTask 4.2: 实现GET /api/v1/documents/{id}文档详情查询接口
  - [x] SubTask 4.3: 创建元数据更新请求DTO

- [x] Task 5: 实现文档列表查询接口
  - [x] SubTask 5.1: 实现GET /api/v1/documents分页查询接口
  - [x] SubTask 5.2: 创建DocumentQueryRequest查询条件DTO
  - [x] SubTask 5.3: 支持按状态、类型、创建时间范围筛选
  - [x] SubTask 5.4: 支持按标题模糊搜索

- [x] Task 6: 实现文档删除接口
  - [x] SubTask 6.1: 实现DELETE /api/v1/documents/{id}删除接口
  - [x] SubTask 6.2: 实现级联删除逻辑（MinIO文件、数据库记录）
  - [x] SubTask 6.3: 添加删除权限校验

- [x] Task 7: 实现Kafka消息生产者
  - [x] SubTask 7.1: 创建DocumentProcessMessage消息体类
  - [x] SubTask 7.2: 创建DocumentMessageProducer消息生产者类
  - [x] SubTask 7.3: 实现文档处理任务消息发送逻辑
  - [x] SubTask 7.4: 在文档上传成功后触发消息发送

- [x] Task 8: 实现Kafka消息消费者
  - [x] SubTask 8.1: 创建DocumentMessageConsumer消息消费者类
  - [x] SubTask 8.2: 实现消息消费和任务分发逻辑
  - [x] SubTask 8.3: 添加消息消费异常处理

- [x] Task 9: 实现任务状态追踪管理
  - [x] SubTask 9.1: 创建TaskProgress实体类，记录任务进度
  - [x] SubTask 9.2: 创建TaskStatusManager状态管理器
  - [x] SubTask 9.3: 实现进度更新和查询方法
  - [x] SubTask 9.4: 使用Redis缓存任务进度

- [x] Task 10: 实现任务进度查询接口
  - [x] SubTask 10.1: 实现GET /api/v1/documents/{id}/progress进度查询接口
  - [x] SubTask 10.2: 创建ProgressResponse响应DTO
  - [x] SubTask 10.3: 返回当前阶段、进度百分比、预计剩余时间

- [x] Task 11: 实现任务重试机制
  - [x] SubTask 11.1: 创建RetryPolicy重试策略配置类
  - [x] SubTask 11.2: 实现失败任务自动重试逻辑
  - [x] SubTask 11.3: 添加重试次数限制（默认3次）
  - [x] SubTask 11.4: 实现最终失败告警通知

- [x] Task 12: 编写单元测试和集成测试
  - [x] SubTask 12.1: 创建DocumentServiceTest单元测试类
  - [x] SubTask 12.2: 创建DocumentControllerTest集成测试类
  - [x] SubTask 12.3: 创建DocumentStatusMachineTest状态机测试类
  - [x] SubTask 12.4: 创建Kafka消息处理测试类

- [x] Task 13: 验证和文档更新
  - [x] SubTask 13.1: 编译验证所有模块
  - [x] SubTask 13.2: 运行单元测试验证功能正确性
  - [x] SubTask 13.3: 更新API接口文档

# Task Dependencies
- [Task 2] depends on [Task 1] (状态机依赖实体类)
- [Task 3] depends on [Task 1, Task 2] (上传接口依赖实体和状态)
- [Task 4] depends on [Task 1] (元数据管理依赖实体)
- [Task 5] depends on [Task 1] (查询接口依赖实体)
- [Task 6] depends on [Task 1] (删除接口依赖实体)
- [Task 7] depends on [Task 3] (消息发送在上传后触发)
- [Task 8] depends on [Task 7] (消费者依赖消息格式)
- [Task 9] depends on [Task 1] (状态追踪依赖实体)
- [Task 10] depends on [Task 9] (进度查询依赖状态管理)
- [Task 11] depends on [Task 8] (重试机制依赖消费者)
- [Task 12] depends on [Task 1-11] (测试依赖所有功能)
- [Task 13] depends on [Task 12] (验证依赖测试)
