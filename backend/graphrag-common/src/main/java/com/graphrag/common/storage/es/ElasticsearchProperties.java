package com.graphrag.common.storage.es;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "elasticsearch")
public class ElasticsearchProperties {

    private String host = "localhost";

    private int port = 9200;

    private String username;

    private String password;

    private String scheme = "http";

    private int connectionTimeout = 5000;

    private int socketTimeout = 30000;

    private int maxConnections = 100;

    private int maxConnectionsPerRoute = 20;

    private boolean enabled = true;
}
