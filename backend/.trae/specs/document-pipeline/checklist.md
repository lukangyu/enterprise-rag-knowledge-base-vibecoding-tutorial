# Document Pipeline Checklist

## 文档实体设计
- [x] Document实体类包含所有必需字段（id、title、source、docType、filePath、fileSize、contentHash、status、metadata）
- [x] DocumentChunk实体类包含所有必需字段（id、docId、content、position、tokenCount、embeddingId、metadata）
- [x] DocumentMapper和DocumentChunkMapper接口正确创建
- [x] 数据库表结构符合设计文档规范

## 文档状态管理
- [x] DocumentStatus枚举定义完整（PENDING、PARSING、CHUNKING、EMBEDDING、COMPLETED、FAILED）
- [x] 状态机实现正确的状态流转逻辑
- [x] 状态流转校验正确，不允许非法状态转换

## 文档上传接口
- [x] POST /api/v1/documents/upload接口正常工作
- [x] 文件成功上传到MinIO
- [x] 文件类型校验正确（PDF、Word、Markdown、TXT）
- [x] 上传失败时返回正确的错误信息

## 文档元数据管理
- [x] PUT /api/v1/documents/{id}/metadata接口正常工作
- [x] GET /api/v1/documents/{id}接口返回完整文档信息

## 文档列表查询
- [x] GET /api/v1/documents分页查询接口正常工作
- [x] 支持按状态筛选
- [x] 支持按类型筛选
- [x] 支持按时间范围筛选
- [x] 支持按标题模糊搜索

## 文档删除接口
- [x] DELETE /api/v1/documents/{id}接口正常工作
- [x] MinIO文件正确删除
- [x] 数据库记录正确删除

## Kafka消息处理
- [x] DocumentProcessMessage消息体格式正确
- [x] 消息生产者正确发送消息到Kafka
- [x] 消息消费者正确消费消息
- [x] 文档上传成功后自动触发消息发送

## 任务状态追踪
- [x] TaskProgress实体类正确创建
- [x] TaskStatusManager正确管理任务状态
- [x] Redis缓存正确存储任务进度
- [x] GET /api/v1/documents/{id}/progress接口返回正确进度信息

## 任务重试机制
- [x] 失败任务自动重试
- [x] 重试次数限制正确（默认3次）
- [x] 最终失败时发送告警通知

## 单元测试
- [x] DocumentServiceTest测试覆盖率>80%
- [x] DocumentControllerTest测试覆盖率>80%
- [x] DocumentStatusMachineTest测试覆盖率>80%
- [x] Kafka消息处理测试通过

## 编译验证
- [x] 所有模块编译成功
- [x] 所有单元测试通过
- [x] 代码符合项目编码规范
