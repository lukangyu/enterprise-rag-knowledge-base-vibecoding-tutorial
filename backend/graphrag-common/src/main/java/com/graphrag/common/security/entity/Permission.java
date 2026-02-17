package com.graphrag.common.security.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@TableName("permissions")
public class Permission implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private String permissionCode;

    private String permissionName;

    private String resourceType;

    private String resourcePath;

    private Long parentId;

    private String description;

    private Integer status;

    @TableLogic
    private Integer deleted;

    private Integer sortOrder;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableField(exist = false)
    private transient java.util.List<Permission> children;
}
