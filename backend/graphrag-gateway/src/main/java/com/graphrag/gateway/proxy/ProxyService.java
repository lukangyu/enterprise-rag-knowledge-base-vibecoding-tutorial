package com.graphrag.gateway.proxy;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.graphrag.gateway.exception.ProxyException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import jakarta.servlet.http.HttpServletRequest;
import java.net.SocketTimeoutException;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeoutException;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProxyService {
    
    private final RestTemplate restTemplate;
    private final ProxyProperties proxyProperties;
    private final ObjectMapper objectMapper;
    
    public ResponseEntity<String> forward(
        String routeName,
        HttpServletRequest request,
        HttpMethod method,
        String body
    ) {
        ProxyProperties.Route route = proxyProperties.getRoutes().get(routeName);
        if (route == null) {
            log.error("Route not found: {}", routeName);
            throw ProxyException.upstreamError(routeName, 404, "Route configuration not found");
        }
        
        String path = request.getRequestURI();
        String queryString = request.getQueryString();
        
        if (route.isStripPrefix()) {
            String routePath = route.getPath().replace("/**", "");
            path = path.replaceFirst(routePath, "");
        }
        
        String targetUrl = route.getTarget() + path;
        if (queryString != null && !queryString.isEmpty()) {
            targetUrl += "?" + queryString;
        }
        
        log.debug("Forwarding request: {} -> {}", request.getRequestURI(), targetUrl);
        
        try {
            HttpHeaders headers = extractHeaders(request);
            
            HttpEntity<String> entity = new HttpEntity<>(body, headers);
            
            ResponseEntity<String> response = restTemplate.exchange(
                targetUrl,
                method,
                entity,
                String.class
            );
            
            log.debug("Response status: {}", response.getStatusCode());
            return response;
            
        } catch (ResourceAccessException e) {
            if (e.getCause() instanceof SocketTimeoutException || e.getCause() instanceof TimeoutException) {
                log.error("Request timeout: {} - {}", targetUrl, e.getMessage());
                throw ProxyException.timeout(routeName, route.getTarget());
            }
            log.error("Connection failed: {} - {}", targetUrl, e.getMessage());
            throw ProxyException.connectionFailed(routeName, route.getTarget());
        } catch (HttpClientErrorException e) {
            log.warn("Client error from upstream: {} - Status: {}", targetUrl, e.getStatusCode());
            throw ProxyException.upstreamError(routeName, e.getStatusCode().value(), e.getResponseBodyAsString());
        } catch (HttpServerErrorException e) {
            log.error("Server error from upstream: {} - Status: {}", targetUrl, e.getStatusCode());
            throw ProxyException.upstreamError(routeName, e.getStatusCode().value(), e.getResponseBodyAsString());
        } catch (Exception e) {
            log.error("Proxy request failed: {} - {}", targetUrl, e.getMessage(), e);
            throw new ProxyException(routeName, "Proxy request failed: " + e.getMessage(), e);
        }
    }
    
    public <T> T get(String url, Class<T> responseType) {
        try {
            ResponseEntity<T> response = restTemplate.getForEntity(url, responseType);
            return response.getBody();
        } catch (Exception e) {
            log.error("GET request failed: {} - {}", url, e.getMessage());
            return null;
        }
    }
    
    public <T> T post(String url, Object body, Class<T> responseType) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<Object> entity = new HttpEntity<>(body, headers);
            
            ResponseEntity<T> response = restTemplate.postForEntity(url, entity, responseType);
            return response.getBody();
        } catch (Exception e) {
            log.error("POST request failed: {} - {}", url, e.getMessage());
            return null;
        }
    }
    
    private HttpHeaders extractHeaders(HttpServletRequest request) {
        HttpHeaders headers = new HttpHeaders();
        
        Enumeration<String> headerNames = request.getHeaderNames();
        while (headerNames.hasMoreElements()) {
            String headerName = headerNames.nextElement();
            if (!shouldSkipHeader(headerName)) {
                headers.set(headerName, request.getHeader(headerName));
            }
        }
        
        return headers;
    }
    
    private boolean shouldSkipHeader(String headerName) {
        String lowerName = headerName.toLowerCase();
        return lowerName.equals("host") || 
               lowerName.equals("content-length") ||
               lowerName.equals("transfer-encoding");
    }
}
