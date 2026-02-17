package com.graphrag.document.dto;

import com.graphrag.document.entity.TaskProgress;
import lombok.Builder;
import lombok.Data;

import java.io.Serializable;
import java.time.Duration;
import java.time.LocalDateTime;

@Data
@Builder
public class ProgressResponse implements Serializable {

    private static final long serialVersionUID = 1L;

    private String docId;

    private String currentStage;

    private Integer progress;

    private String errorMessage;

    private Integer retryCount;

    private Long estimatedRemainingTime;

    public static ProgressResponse fromEntity(TaskProgress taskProgress) {
        if (taskProgress == null) {
            return null;
        }

        Long estimatedRemainingTime = null;
        if (taskProgress.getEstimatedEndTime() != null && taskProgress.getProgress() != null && taskProgress.getProgress() < 100) {
            Duration duration = Duration.between(LocalDateTime.now(), taskProgress.getEstimatedEndTime());
            estimatedRemainingTime = duration.isNegative() ? 0L : duration.getSeconds();
        }

        return ProgressResponse.builder()
                .docId(taskProgress.getDocId())
                .currentStage(taskProgress.getCurrentStage())
                .progress(taskProgress.getProgress())
                .errorMessage(taskProgress.getErrorMessage())
                .retryCount(taskProgress.getRetryCount())
                .estimatedRemainingTime(estimatedRemainingTime)
                .build();
    }
}
