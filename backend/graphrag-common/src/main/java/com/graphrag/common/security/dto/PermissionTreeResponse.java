package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "权限树响应")
public class PermissionTreeResponse {

    @Schema(description = "权限ID")
    private Long id;

    @Schema(description = "权限编码")
    private String permissionCode;

    @Schema(description = "权限名称")
    private String permissionName;

    @Schema(description = "资源类型")
    private String resourceType;

    @Schema(description = "资源路径")
    private String resourcePath;

    @Schema(description = "父权限ID")
    private Long parentId;

    @Schema(description = "描述")
    private String description;

    @Schema(description = "排序")
    private Integer sortOrder;

    @Schema(description = "子权限列表")
    private List<PermissionTreeResponse> children;
}
