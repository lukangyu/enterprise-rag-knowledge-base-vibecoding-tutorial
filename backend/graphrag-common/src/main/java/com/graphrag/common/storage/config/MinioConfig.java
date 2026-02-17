package com.graphrag.common.storage.config;

import io.minio.MinioClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.OkHttpClient;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.TimeUnit;

/**
 * MinIO 客户端配置类
 * 用于创建和配置 MinIO 客户端连接
 *
 * @author GraphRAG Team
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "minio", name = "endpoint")
public class MinioConfig {

    private final MinioProperties minioProperties;

    /**
     * 创建 MinIO 客户端 Bean
     *
     * @return MinioClient 实例
     */
    @Bean
    public MinioClient minioClient() {
        log.info("初始化 MinIO 客户端, endpoint: {}", minioProperties.getEndpoint());

        OkHttpClient httpClient = new OkHttpClient.Builder()
                .connectTimeout(minioProperties.getConnectTimeout(), TimeUnit.SECONDS)
                .writeTimeout(minioProperties.getWriteTimeout(), TimeUnit.SECONDS)
                .readTimeout(minioProperties.getReadTimeout(), TimeUnit.SECONDS)
                .build();

        return MinioClient.builder()
                .endpoint(minioProperties.getEndpoint())
                .credentials(minioProperties.getAccessKey(), minioProperties.getSecretKey())
                .httpClient(httpClient)
                .build();
    }
}
