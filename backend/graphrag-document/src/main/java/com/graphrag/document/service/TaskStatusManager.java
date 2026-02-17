package com.graphrag.document.service;

import com.graphrag.document.constant.TaskConstants;
import com.graphrag.document.entity.TaskProgress;
import com.graphrag.document.mapper.TaskProgressMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

@Service
@Slf4j
public class TaskStatusManager {

    private final TaskProgressMapper taskProgressMapper;
    private final RedisTemplate<String, Object> redisTemplate;

    public TaskStatusManager(TaskProgressMapper taskProgressMapper, RedisTemplate<String, Object> redisTemplate) {
        this.taskProgressMapper = taskProgressMapper;
        this.redisTemplate = redisTemplate;
    }

    public TaskProgress initProgress(String docId) {
        TaskProgress progress = new TaskProgress();
        progress.setDocId(docId);
        progress.setCurrentStage("INIT");
        progress.setProgress(0);
        progress.setRetryCount(0);
        progress.setStartTime(LocalDateTime.now());
        progress.setUpdateTime(LocalDateTime.now());
        
        taskProgressMapper.insert(progress);
        cacheProgress(docId, progress);
        
        log.info("Task progress initialized for docId: {}", docId);
        return progress;
    }

    public void updateProgress(String docId, String stage, int progressValue) {
        Optional<TaskProgress> optionalProgress = taskProgressMapper.findByDocId(docId);
        
        if (optionalProgress.isPresent()) {
            TaskProgress progress = optionalProgress.get();
            progress.setCurrentStage(stage);
            progress.setProgress(Math.min(100, Math.max(0, progressValue)));
            progress.setUpdateTime(LocalDateTime.now());
            
            if (progressValue > 0 && progress.getStartTime() != null) {
                long elapsedSeconds = Duration.between(progress.getStartTime(), LocalDateTime.now()).getSeconds();
                long estimatedTotalSeconds = (elapsedSeconds * 100) / progressValue;
                progress.setEstimatedEndTime(progress.getStartTime().plusSeconds(estimatedTotalSeconds));
            }
            
            taskProgressMapper.updateById(progress);
            cacheProgress(docId, progress);
            
            log.info("Task progress updated for docId: {}, stage: {}, progress: {}%", docId, stage, progressValue);
        } else {
            log.warn("Task progress not found for docId: {}", docId);
        }
    }

    public TaskProgress getProgress(String docId) {
        String cacheKey = TaskConstants.TASK_PROGRESS_KEY + docId;
        Object cached = redisTemplate.opsForValue().get(cacheKey);
        
        if (cached instanceof TaskProgress) {
            return (TaskProgress) cached;
        }
        
        Optional<TaskProgress> optionalProgress = taskProgressMapper.findByDocId(docId);
        if (optionalProgress.isPresent()) {
            TaskProgress progress = optionalProgress.get();
            cacheProgress(docId, progress);
            return progress;
        }
        
        return null;
    }

    public void markFailed(String docId, String errorMessage) {
        Optional<TaskProgress> optionalProgress = taskProgressMapper.findByDocId(docId);
        
        if (optionalProgress.isPresent()) {
            TaskProgress progress = optionalProgress.get();
            progress.setCurrentStage("FAILED");
            progress.setErrorMessage(errorMessage);
            progress.setUpdateTime(LocalDateTime.now());
            
            taskProgressMapper.updateById(progress);
            cacheProgress(docId, progress);
            
            log.error("Task marked as failed for docId: {}, error: {}", docId, errorMessage);
        } else {
            log.warn("Task progress not found for docId: {} when marking as failed", docId);
        }
    }

    public int incrementRetry(String docId) {
        Optional<TaskProgress> optionalProgress = taskProgressMapper.findByDocId(docId);
        
        if (optionalProgress.isPresent()) {
            TaskProgress progress = optionalProgress.get();
            int newRetryCount = progress.getRetryCount() + 1;
            progress.setRetryCount(newRetryCount);
            progress.setUpdateTime(LocalDateTime.now());
            progress.setErrorMessage(null);
            progress.setCurrentStage("RETRY");
            
            taskProgressMapper.updateById(progress);
            cacheProgress(docId, progress);
            
            log.info("Retry count incremented for docId: {}, new count: {}", docId, newRetryCount);
            return newRetryCount;
        }
        
        log.warn("Task progress not found for docId: {} when incrementing retry", docId);
        return -1;
    }

    public boolean canRetry(String docId, int maxRetries) {
        TaskProgress progress = getProgress(docId);
        
        if (progress == null) {
            return false;
        }
        
        return progress.getRetryCount() < maxRetries;
    }

    public boolean acquireLock(String docId, long timeoutSeconds) {
        String lockKey = TaskConstants.TASK_LOCK_KEY + docId;
        Boolean acquired = redisTemplate.opsForValue().setIfAbsent(lockKey, "locked", timeoutSeconds, TimeUnit.SECONDS);
        return Boolean.TRUE.equals(acquired);
    }

    public void releaseLock(String docId) {
        String lockKey = TaskConstants.TASK_LOCK_KEY + docId;
        redisTemplate.delete(lockKey);
    }

    private void cacheProgress(String docId, TaskProgress progress) {
        String cacheKey = TaskConstants.TASK_PROGRESS_KEY + docId;
        redisTemplate.opsForValue().set(cacheKey, progress, 1, TimeUnit.HOURS);
    }
}
