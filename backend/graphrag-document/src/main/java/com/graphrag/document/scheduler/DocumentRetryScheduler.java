package com.graphrag.document.scheduler;

import com.graphrag.document.constant.TaskConstants;
import com.graphrag.document.service.DocumentRetryService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.Set;

@Component
@Slf4j
public class DocumentRetryScheduler {

    private final RedisTemplate<String, Object> redisTemplate;
    private final DocumentRetryService documentRetryService;

    public DocumentRetryScheduler(
            RedisTemplate<String, Object> redisTemplate,
            DocumentRetryService documentRetryService) {
        this.redisTemplate = redisTemplate;
        this.documentRetryService = documentRetryService;
    }

    @Scheduled(fixedDelay = 5000)
    public void checkPendingRetries() {
        String pendingKey = TaskConstants.TASK_RETRY_PENDING_KEY;
        long currentTime = System.currentTimeMillis();

        Set<Object> dueTasks = redisTemplate.opsForZSet().rangeByScore(pendingKey, 0, currentTime);

        if (dueTasks == null || dueTasks.isEmpty()) {
            return;
        }

        log.info("Found {} pending retry tasks", dueTasks.size());

        for (Object docIdObj : dueTasks) {
            String docId = (String) docIdObj;
            try {
                documentRetryService.executeRetry(docId);
            } catch (Exception e) {
                log.error("Error executing retry for docId: {}", docId, e);
            }
        }
    }

    @Scheduled(fixedDelay = 60000)
    public void cleanupExpiredRetries() {
        String pendingKey = TaskConstants.TASK_RETRY_PENDING_KEY;
        long expirationTime = System.currentTimeMillis() - 3600000;

        Long removed = redisTemplate.opsForZSet().removeRangeByScore(pendingKey, 0, expirationTime);

        if (removed != null && removed > 0) {
            log.info("Cleaned up {} expired retry tasks", removed);
        }
    }
}
