package com.graphrag.system.domain.dto;

import lombok.Data;
import jakarta.validation.constraints.NotBlank;

@Data
public class AuditLogCreateDTO {
    @NotBlank(message = "User ID cannot be empty")
    private String userId;
    
    @NotBlank(message = "Username cannot be empty")
    private String username;
    
    @NotBlank(message = "Action cannot be empty")
    private String action;
    
    @NotBlank(message = "Resource type cannot be empty")
    private String resourceType;
    
    private String resourceId;
    private String details;
    
    @NotBlank(message = "IP address cannot be empty")
    private String ipAddress;
    
    private String userAgent;
    private String status;
    private String errorMessage;
}
