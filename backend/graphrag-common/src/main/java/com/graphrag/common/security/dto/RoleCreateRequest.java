package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "创建角色请求")
public class RoleCreateRequest {

    @NotBlank(message = "角色编码不能为空")
    @Schema(description = "角色编码", example = "manager")
    private String roleCode;

    @NotBlank(message = "角色名称不能为空")
    @Schema(description = "角色名称", example = "管理员")
    private String roleName;

    @Schema(description = "描述", example = "系统管理员角色")
    private String description;

    @Schema(description = "排序", example = "1")
    private Integer sortOrder;
}
