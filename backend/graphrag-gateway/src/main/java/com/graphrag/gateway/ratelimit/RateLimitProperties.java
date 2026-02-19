package com.graphrag.gateway.ratelimit;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Data
@Component
@ConfigurationProperties(prefix = "rate-limit")
public class RateLimitProperties {
    private boolean enabled = true;
    private int defaultLimit = 100;
    private int defaultWindow = 60;
    private Map<String, Integer> routes = new HashMap<>();
    
    public int getLimitForRoute(String routeName) {
        return routes.getOrDefault(routeName, defaultLimit);
    }
}
