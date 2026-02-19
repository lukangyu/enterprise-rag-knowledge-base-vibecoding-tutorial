package com.graphrag.gateway.ratelimit;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphrag.common.core.domain.Result;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Component
@Order(1)
@RequiredArgsConstructor
public class RateLimitFilter implements Filter {
    private final RateLimitService rateLimitService;
    private final RateLimitProperties properties;
    private final ObjectMapper objectMapper;
    
    private static final Pattern ROUTE_PATTERN = Pattern.compile("^/v1/([^/]+)");
    
    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        log.info("Rate limit filter initialized. Enabled: {}", properties.isEnabled());
    }
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        
        if (!properties.isEnabled()) {
            chain.doFilter(request, response);
            return;
        }
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        
        String path = httpRequest.getRequestURI();
        String routeName = extractRouteName(path);
        
        if (routeName == null) {
            chain.doFilter(request, response);
            return;
        }
        
        String clientId = getClientId(httpRequest);
        
        if (!rateLimitService.allowRequest(clientId, routeName)) {
            RateLimitService.RateLimitInfo info = rateLimitService.getRateLimitInfo(clientId, routeName);
            sendRateLimitResponse(httpResponse, info);
            return;
        }
        
        RateLimitService.RateLimitInfo info = rateLimitService.getRateLimitInfo(clientId, routeName);
        httpResponse.setHeader("X-RateLimit-Limit", String.valueOf(info.limit()));
        httpResponse.setHeader("X-RateLimit-Remaining", String.valueOf(info.getRemaining()));
        httpResponse.setHeader("X-RateLimit-Reset", String.valueOf(info.windowSeconds()));
        
        chain.doFilter(request, response);
    }
    
    private String extractRouteName(String path) {
        Matcher matcher = ROUTE_PATTERN.matcher(path);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return null;
    }
    
    private String getClientId(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return "token:" + authHeader.substring(7, Math.min(authHeader.length(), 20));
        }
        
        String apiKey = request.getHeader("X-API-Key");
        if (apiKey != null) {
            return "apikey:" + apiKey.substring(0, Math.min(apiKey.length(), 16));
        }
        
        String sessionId = request.getSession(false) != null ? 
            request.getSession().getId() : null;
        if (sessionId != null) {
            return "session:" + sessionId;
        }
        
        return "ip:" + request.getRemoteAddr();
    }
    
    private void sendRateLimitResponse(HttpServletResponse response, RateLimitService.RateLimitInfo info) 
            throws IOException {
        response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        
        response.setHeader("X-RateLimit-Limit", String.valueOf(info.limit()));
        response.setHeader("X-RateLimit-Remaining", "0");
        response.setHeader("X-RateLimit-Reset", String.valueOf(info.windowSeconds()));
        response.setHeader("Retry-After", String.valueOf(info.windowSeconds()));
        
        Result<Void> result = Result.error(429, "请求过于频繁，请稍后再试。限制: " + info.limit() + " 次/" + info.windowSeconds() + "秒");
        
        response.getWriter().write(objectMapper.writeValueAsString(result));
    }
    
    @Override
    public void destroy() {
        log.info("Rate limit filter destroyed");
    }
}
