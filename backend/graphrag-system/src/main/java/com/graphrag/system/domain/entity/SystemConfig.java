package com.graphrag.system.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sys_config")
public class SystemConfig {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private String configKey;
    
    private String configValue;
    
    private String configType;
    
    private String description;
    
    private Integer sortOrder;
    
    private Integer status;
    
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
    
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
    
    @TableLogic
    private Integer deleted;
}
