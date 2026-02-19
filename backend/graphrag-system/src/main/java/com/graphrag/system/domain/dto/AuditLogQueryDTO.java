package com.graphrag.system.domain.dto;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class AuditLogQueryDTO {
    private Integer page = 1;
    private Integer size = 20;
    private String userId;
    private String username;
    private String action;
    private String resourceType;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
}
