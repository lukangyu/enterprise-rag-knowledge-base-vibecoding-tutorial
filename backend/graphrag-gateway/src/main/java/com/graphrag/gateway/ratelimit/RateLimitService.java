package com.graphrag.gateway.ratelimit;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Slf4j
@Service
@RequiredArgsConstructor
public class RateLimitService {
    private final RateLimitProperties properties;
    private final Map<String, RateLimitEntry> rateLimitMap = new ConcurrentHashMap<>();
    
    public boolean allowRequest(String clientId, String routeName) {
        if (!properties.isEnabled()) {
            return true;
        }
        
        String key = clientId + ":" + routeName;
        int limit = properties.getLimitForRoute(routeName);
        int windowSeconds = properties.getDefaultWindow();
        
        long currentTime = System.currentTimeMillis();
        long windowStart = currentTime - (windowSeconds * 1000L);
        
        RateLimitEntry entry = rateLimitMap.computeIfAbsent(key, k -> new RateLimitEntry());
        
        synchronized (entry) {
            if (entry.windowStart < windowStart) {
                entry.windowStart = currentTime;
                entry.count.set(0);
            }
            
            long currentCount = entry.count.get();
            if (currentCount < limit) {
                entry.count.incrementAndGet();
                return true;
            }
            
            log.warn("Rate limit exceeded for client {} on route {}. Count: {}/{}", 
                clientId, routeName, currentCount, limit);
            return false;
        }
    }
    
    public RateLimitInfo getRateLimitInfo(String clientId, String routeName) {
        String key = clientId + ":" + routeName;
        int limit = properties.getLimitForRoute(routeName);
        
        RateLimitEntry entry = rateLimitMap.get(key);
        if (entry == null) {
            return new RateLimitInfo(0, limit, properties.getDefaultWindow());
        }
        
        return new RateLimitInfo(entry.count.get(), limit, properties.getDefaultWindow());
    }
    
    public void cleanupExpiredEntries() {
        long windowStart = System.currentTimeMillis() - (properties.getDefaultWindow() * 1000L);
        rateLimitMap.entrySet().removeIf(entry -> entry.getValue().windowStart < windowStart);
        log.debug("Cleaned up expired rate limit entries. Current size: {}", rateLimitMap.size());
    }
    
    private static class RateLimitEntry {
        volatile long windowStart = System.currentTimeMillis();
        AtomicLong count = new AtomicLong(0);
    }
    
    public record RateLimitInfo(long current, int limit, int windowSeconds) {
        public int getRemaining() {
            return Math.max(0, limit - (int) current);
        }
    }
}
