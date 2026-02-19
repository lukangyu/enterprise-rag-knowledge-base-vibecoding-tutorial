package com.graphrag.gateway.exception;

import lombok.Getter;

@Getter
public class ProxyException extends RuntimeException {
    private final int statusCode;
    private final String routeName;
    
    public ProxyException(String routeName, String message) {
        super(message);
        this.statusCode = 502;
        this.routeName = routeName;
    }
    
    public ProxyException(String routeName, int statusCode, String message) {
        super(message);
        this.statusCode = statusCode;
        this.routeName = routeName;
    }
    
    public ProxyException(String routeName, String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 502;
        this.routeName = routeName;
    }
    
    public static ProxyException connectionFailed(String routeName, String target) {
        return new ProxyException(routeName, "无法连接到目标服务: " + target);
    }
    
    public static ProxyException timeout(String routeName, String target) {
        return new ProxyException(routeName, 504, "请求目标服务超时: " + target);
    }
    
    public static ProxyException upstreamError(String routeName, int statusCode, String message) {
        return new ProxyException(routeName, statusCode, "上游服务错误: " + message);
    }
}
