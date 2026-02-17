package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Data
@Schema(description = "更新角色请求")
public class RoleUpdateRequest {

    @Schema(description = "角色名称", example = "管理员")
    private String roleName;

    @Schema(description = "描述", example = "系统管理员角色")
    private String description;

    @Schema(description = "状态:0-正常,1-禁用", example = "0")
    private Integer status;

    @Schema(description = "排序", example = "1")
    private Integer sortOrder;

    @Schema(description = "权限ID列表")
    private List<Long> permissionIds;
}
