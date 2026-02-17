package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "创建权限请求")
public class PermissionCreateRequest {

    @NotBlank(message = "权限编码不能为空")
    @Schema(description = "权限编码", example = "system:user:add")
    private String permissionCode;

    @NotBlank(message = "权限名称不能为空")
    @Schema(description = "权限名称", example = "新增用户")
    private String permissionName;

    @NotBlank(message = "资源类型不能为空")
    @Schema(description = "资源类型:menu-button-api", example = "button")
    private String resourceType;

    @Schema(description = "资源路径", example = "system:user:add")
    private String resourcePath;

    @Schema(description = "父权限ID", example = "0")
    private Long parentId;

    @Schema(description = "描述", example = "新增用户权限")
    private String description;

    @Schema(description = "排序", example = "1")
    private Integer sortOrder;
}
