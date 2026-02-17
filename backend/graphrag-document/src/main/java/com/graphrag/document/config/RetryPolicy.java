package com.graphrag.document.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "document.retry")
public class RetryPolicy {

    private int maxRetries = 3;

    private long initialDelayMs = 1000;

    private long maxDelayMs = 10000;

    private double multiplier = 2.0;
}
