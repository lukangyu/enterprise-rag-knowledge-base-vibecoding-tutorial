package com.graphrag.gateway.proxy;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

@Data
@Component
@ConfigurationProperties(prefix = "proxy")
public class ProxyProperties {
    
    private Map<String, Route> routes = new HashMap<>();
    
    @Data
    public static class Route {
        private String path;
        private String target;
        private boolean stripPrefix = true;
        private int connectTimeout = 5000;
        private int readTimeout = 30000;
    }
}
