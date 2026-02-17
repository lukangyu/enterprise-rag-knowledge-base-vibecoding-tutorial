package com.graphrag.document.service;

import com.graphrag.document.config.RetryPolicy;
import com.graphrag.document.constant.TaskConstants;
import com.graphrag.document.entity.TaskProgress;
import com.graphrag.document.message.DocumentProcessMessage;
import com.graphrag.document.producer.DocumentMessageProducer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
@Slf4j
public class DocumentRetryService {

    private final DocumentMessageProducer documentMessageProducer;
    private final TaskStatusManager taskStatusManager;
    private final RetryPolicy retryPolicy;
    private final RedisTemplate<String, Object> redisTemplate;

    public DocumentRetryService(
            DocumentMessageProducer documentMessageProducer,
            TaskStatusManager taskStatusManager,
            RetryPolicy retryPolicy,
            RedisTemplate<String, Object> redisTemplate) {
        this.documentMessageProducer = documentMessageProducer;
        this.taskStatusManager = taskStatusManager;
        this.retryPolicy = retryPolicy;
        this.redisTemplate = redisTemplate;
    }

    public void scheduleRetry(String docId, String action) {
        TaskProgress progress = taskStatusManager.getProgress(docId);
        if (progress == null) {
            log.warn("Task progress not found for docId: {}, cannot schedule retry", docId);
            return;
        }

        int retryCount = progress.getRetryCount();
        if (retryCount >= retryPolicy.getMaxRetries()) {
            log.error("Max retries exceeded for docId: {}, marking as failed", docId);
            taskStatusManager.markFailed(docId, "Max retries exceeded");
            return;
        }

        long delayMs = calculateDelay(retryCount);
        LocalDateTime scheduledTime = LocalDateTime.now().plusNanos(delayMs * 1_000_000);

        Map<String, Object> retryTask = new HashMap<>();
        retryTask.put("docId", docId);
        retryTask.put("action", action);
        retryTask.put("retryCount", retryCount + 1);
        retryTask.put("scheduledTime", scheduledTime.toString());
        retryTask.put("createdAt", LocalDateTime.now().toString());

        String retryKey = TaskConstants.TASK_RETRY_KEY + docId;
        redisTemplate.opsForValue().set(retryKey, retryTask, delayMs + 60000, TimeUnit.MILLISECONDS);

        String pendingKey = TaskConstants.TASK_RETRY_PENDING_KEY;
        redisTemplate.opsForZSet().add(pendingKey, docId, System.currentTimeMillis() + delayMs);

        log.info("Scheduled retry for docId: {}, action: {}, retryCount: {}, delayMs: {}",
                docId, action, retryCount + 1, delayMs);
    }

    public long calculateDelay(int retryCount) {
        if (retryCount <= 0) {
            return retryPolicy.getInitialDelayMs();
        }

        double delay = retryPolicy.getInitialDelayMs() * Math.pow(retryPolicy.getMultiplier(), retryCount);
        return Math.min((long) delay, retryPolicy.getMaxDelayMs());
    }

    public boolean shouldRetry(String docId) {
        TaskProgress progress = taskStatusManager.getProgress(docId);
        if (progress == null) {
            return false;
        }

        return progress.getRetryCount() < retryPolicy.getMaxRetries();
    }

    public void executeRetry(String docId) {
        String retryKey = TaskConstants.TASK_RETRY_KEY + docId;
        Object retryTaskObj = redisTemplate.opsForValue().get(retryKey);

        if (retryTaskObj instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> retryTask = (Map<String, Object>) retryTaskObj;
            String action = (String) retryTask.get("action");
            Integer retryCount = (Integer) retryTask.get("retryCount");

            taskStatusManager.incrementRetry(docId);

            DocumentProcessMessage message = DocumentProcessMessage.builder()
                    .docId(docId)
                    .action(action)
                    .build();

            documentMessageProducer.sendProcessMessage(message);

            redisTemplate.delete(retryKey);
            redisTemplate.opsForZSet().remove(TaskConstants.TASK_RETRY_PENDING_KEY, docId);

            log.info("Executed retry for docId: {}, action: {}, retryCount: {}", docId, action, retryCount);
        }
    }

    public void cancelRetry(String docId) {
        String retryKey = TaskConstants.TASK_RETRY_KEY + docId;
        redisTemplate.delete(retryKey);
        redisTemplate.opsForZSet().remove(TaskConstants.TASK_RETRY_PENDING_KEY, docId);
        log.info("Cancelled retry for docId: {}", docId);
    }
}
