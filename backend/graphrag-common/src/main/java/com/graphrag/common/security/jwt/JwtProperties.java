package com.graphrag.common.security.jwt;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "jwt")
public class JwtProperties {

    private String secret;
    private Long accessTokenExpire;
    private Long refreshTokenExpire;
    private String issuer;
    private String header = "Authorization";
    private String tokenPrefix = "Bearer ";
}
