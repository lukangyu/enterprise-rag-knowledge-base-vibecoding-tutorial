package com.graphrag.common.storage.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * MinIO 配置属性类
 * 用于读取 application.yml 中的 minio 配置
 *
 * @author GraphRAG Team
 */
@Data
@Component
@ConfigurationProperties(prefix = "minio")
public class MinioProperties {

    /**
     * MinIO 服务地址
     * 例如: http://localhost:9000
     */
    private String endpoint;

    /**
     * 访问密钥（用户名）
     */
    private String accessKey;

    /**
     * 私有密钥（密码）
     */
    private String secretKey;

    /**
     * 默认存储桶名称
     */
    private String bucketName;

    /**
     * 是否自动创建存储桶
     * 默认为 true
     */
    private Boolean autoCreateBucket = true;

    /**
     * 文件访问URL前缀
     * 如果配置了nginx代理，可以设置为代理地址
     * 例如: http://localhost:9000
     */
    private String fileHost;

    /**
     * 连接超时时间（秒）
     * 默认10秒
     */
    private Integer connectTimeout = 10;

    /**
     * 写入超时时间（秒）
     * 默认60秒
     */
    private Integer writeTimeout = 60;

    /**
     * 读取超时时间（秒）
     * 默认60秒
     */
    private Integer readTimeout = 60;
}
