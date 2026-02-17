package com.graphrag.common.mq.kafka;

/**
 * Kafka Topic 常量类
 * 定义GraphRAG项目中使用的所有Kafka Topic名称
 *
 * @author GraphRAG Team
 */
public final class KafkaTopicConstants {

    /**
     * 私有构造函数，防止实例化
     */
    private KafkaTopicConstants() {
        throw new UnsupportedOperationException("常量类不允许实例化");
    }

    // ==================== 文档处理相关Topic ====================

    /**
     * 文档处理Topic
     * 用于文档上传、解析等处理任务
     * 分区数: 3, 副本因子: 1
     */
    public static final String DOCUMENT_PROCESS = "document-process";

    /**
     * 文档分块Topic
     * 用于文档分块处理任务
     * 分区数: 3, 副本因子: 1
     */
    public static final String DOCUMENT_CHUNK = "document-chunk";

    // ==================== 向量化相关Topic ====================

    /**
     * 向量化任务Topic
     * 用于文档向量化和嵌入任务
     * 分区数: 3, 副本因子: 1
     */
    public static final String EMBEDDING_TASK = "embedding-task";

    // ==================== 知识图谱相关Topic ====================

    /**
     * 知识图谱抽取Topic
     *用于实体关系抽取和知识图谱构建任务
     * 分区数: 3, 副本因子: 1
     */
    public static final String KG_EXTRACTION = "kg-extraction";

    // ==================== 通知相关Topic ====================

    /**
     * 通知消息Topic
     * 用于系统通知、任务状态通知等
     * 分区数: 2, 副本因子: 1
     */
    public static final String NOTIFICATION = "notification";

    // ==================== Topic配置常量 ====================

    /**
     * 默认分区数
     */
    public static final int DEFAULT_PARTITIONS = 3;

    /**
     * 默认副本因子
     */
    public static final short DEFAULT_REPLICATION_FACTOR = 1;

    /**
     * 通知Topic分区数
     */
    public static final int NOTIFICATION_PARTITIONS = 2;
}
