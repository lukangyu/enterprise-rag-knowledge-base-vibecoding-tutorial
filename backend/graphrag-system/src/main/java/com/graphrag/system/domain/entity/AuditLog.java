package com.graphrag.system.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sys_audit_log")
public class AuditLog {
    
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;
    
    private String userId;
    
    private String username;
    
    private String action;
    
    private String resourceType;
    
    private String resourceId;
    
    private String details;
    
    private String ipAddress;
    
    private String userAgent;
    
    private String status;
    
    private String errorMessage;
    
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
    
    @TableLogic
    private Integer deleted;
}
