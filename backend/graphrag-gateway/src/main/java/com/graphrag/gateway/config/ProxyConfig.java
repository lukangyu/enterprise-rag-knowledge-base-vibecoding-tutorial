package com.graphrag.gateway.config;

import org.springframework.boot.web.client.ClientHttpRequestFactories;
import org.springframework.boot.web.client.ClientHttpRequestFactorySettings;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

/**
 * 代理配置类
 * 
 * 用于配置 Gateway 转发请求到 Python AI 服务所需的 HTTP 客户端。
 * 主要功能：
 * 1. 配置连接超时 - 建立与目标服务器连接的最大等待时间
 * 2. 配置读取超时 - 等待响应数据的最大时间
 * 
 * Spring Boot 3.x 使用 ClientHttpRequestFactorySettings 替代了旧版的直接超时配置方式。
 */
@Configuration
public class ProxyConfig {
    
    /**
     * 创建配置好超时设置的 RestTemplate Bean
     * 
     * @param builder Spring Boot 自动注入的 RestTemplateBuilder
     * @return 配置好的 RestTemplate 实例
     */
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        // 创建请求工厂设置
        // - connectTimeout: 连接超时5秒，防止长时间等待无法连接的服务器
        // - readTimeout: 读取超时60秒，考虑到 AI 服务可能需要较长处理时间
        ClientHttpRequestFactorySettings settings = ClientHttpRequestFactorySettings.DEFAULTS
            .withConnectTimeout(Duration.ofSeconds(5))
            .withReadTimeout(Duration.ofSeconds(60));
        
        // 根据设置创建请求工厂
        ClientHttpRequestFactory factory = ClientHttpRequestFactories.get(settings);
        
        // 构建并返回 RestTemplate
        return builder
            .requestFactory(() -> factory)
            .build();
    }
}
