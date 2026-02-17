package com.graphrag.document.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@TableName("task_progress")
public class TaskProgress implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.ASSIGN_ID)
    private String id;

    private String docId;

    private String currentStage;

    private Integer progress;

    private String errorMessage;

    private Integer retryCount;

    private LocalDateTime startTime;

    private LocalDateTime updateTime;

    private LocalDateTime estimatedEndTime;
}
