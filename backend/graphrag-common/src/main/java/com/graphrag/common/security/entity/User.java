package com.graphrag.common.security.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@TableName("users")
public class User implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(type = IdType.AUTO)
    private Long id;

    private String username;

    private String password;

    private String email;

    private String phone;

    private String realName;

    private String avatar;

    private Integer gender;

    private Integer status;

    @TableLogic
    private Integer deleted;

    private LocalDateTime lastLoginTime;

    private String lastLoginIp;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    private Long createdBy;

    private Long updatedBy;

    @TableField(exist = false)
    private transient java.util.List<Role> roles;

    @TableField(exist = false)
    private transient java.util.List<String> roleCodes;

    @TableField(exist = false)
    private transient java.util.List<String> permissions;
}
