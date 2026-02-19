package com.graphrag.gateway.ratelimit;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@EnableScheduling
@RequiredArgsConstructor
public class RateLimitCleanupTask {
    private final RateLimitService rateLimitService;
    
    @Scheduled(fixedRate = 60000)
    public void cleanupExpiredEntries() {
        log.debug("Running rate limit cleanup task");
        rateLimitService.cleanupExpiredEntries();
    }
}
