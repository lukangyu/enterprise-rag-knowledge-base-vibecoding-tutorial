package com.graphrag.gateway.controller;

import com.graphrag.common.core.domain.Result;
import com.graphrag.common.security.annotation.RequirePermission;
import com.graphrag.common.security.dto.PermissionCreateRequest;
import com.graphrag.common.security.dto.PermissionTreeResponse;
import com.graphrag.common.security.entity.Permission;
import com.graphrag.gateway.service.PermissionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "权限管理", description = "权限管理相关接口")
@RestController
@RequestMapping("/system/permission")
@RequiredArgsConstructor
public class PermissionController {

    private final PermissionService permissionService;

    @Operation(summary = "权限列表", description = "获取所有权限列表")
    @GetMapping("/list")
    @RequirePermission("system:permission")
    public Result<List<Permission>> list() {
        List<Permission> permissions = permissionService.listPermissions();
        return Result.success(permissions);
    }

    @Operation(summary = "权限树", description = "获取权限树结构")
    @GetMapping("/tree")
    @RequirePermission("system:permission")
    public Result<List<PermissionTreeResponse>> tree() {
        List<PermissionTreeResponse> tree = permissionService.getPermissionTree();
        return Result.success(tree);
    }

    @Operation(summary = "权限详情", description = "根据ID获取权限详情")
    @GetMapping("/{id}")
    @RequirePermission("system:permission")
    public Result<Permission> getById(@PathVariable Long id) {
        Permission permission = permissionService.getPermissionById(id);
        return Result.success(permission);
    }

    @Operation(summary = "创建权限", description = "创建新权限")
    @PostMapping
    @RequirePermission("system:permission")
    public Result<Permission> create(@Valid @RequestBody PermissionCreateRequest request) {
        Permission permission = permissionService.createPermission(request);
        return Result.success(permission);
    }

    @Operation(summary = "更新权限", description = "更新权限信息")
    @PutMapping("/{id}")
    @RequirePermission("system:permission")
    public Result<Permission> update(@PathVariable Long id, @RequestBody PermissionCreateRequest request) {
        Permission permission = permissionService.updatePermission(id, request);
        return Result.success(permission);
    }

    @Operation(summary = "删除权限", description = "删除指定权限")
    @DeleteMapping("/{id}")
    @RequirePermission("system:permission")
    public Result<Void> delete(@PathVariable Long id) {
        permissionService.deletePermission(id);
        return Result.success();
    }
}
