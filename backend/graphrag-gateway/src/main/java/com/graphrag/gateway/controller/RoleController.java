package com.graphrag.gateway.controller;

import com.graphrag.common.core.domain.Result;
import com.graphrag.common.security.annotation.RequirePermission;
import com.graphrag.common.security.dto.RoleCreateRequest;
import com.graphrag.common.security.dto.RoleUpdateRequest;
import com.graphrag.common.security.entity.Role;
import com.graphrag.gateway.service.RoleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "角色管理", description = "角色管理相关接口")
@RestController
@RequestMapping("/system/role")
@RequiredArgsConstructor
public class RoleController {

    private final RoleService roleService;

    @Operation(summary = "角色列表", description = "获取所有角色列表")
    @GetMapping("/list")
    @RequirePermission("system:role")
    public Result<List<Role>> list() {
        List<Role> roles = roleService.listRoles();
        return Result.success(roles);
    }

    @Operation(summary = "角色详情", description = "根据ID获取角色详情")
    @GetMapping("/{id}")
    @RequirePermission("system:role")
    public Result<Role> getById(@PathVariable Long id) {
        Role role = roleService.getRoleById(id);
        return Result.success(role);
    }

    @Operation(summary = "创建角色", description = "创建新角色")
    @PostMapping
    @RequirePermission("system:role")
    public Result<Role> create(@Valid @RequestBody RoleCreateRequest request) {
        Role role = roleService.createRole(request);
        return Result.success(role);
    }

    @Operation(summary = "更新角色", description = "更新角色信息")
    @PutMapping("/{id}")
    @RequirePermission("system:role")
    public Result<Role> update(@PathVariable Long id, @RequestBody RoleUpdateRequest request) {
        Role role = roleService.updateRole(id, request);
        return Result.success(role);
    }

    @Operation(summary = "删除角色", description = "删除指定角色")
    @DeleteMapping("/{id}")
    @RequirePermission("system:role")
    public Result<Void> delete(@PathVariable Long id) {
        roleService.deleteRole(id);
        return Result.success();
    }

    @Operation(summary = "分配权限", description = "为角色分配权限")
    @PutMapping("/{id}/permissions")
    @RequirePermission("system:role")
    public Result<Void> assignPermissions(@PathVariable Long id, @RequestBody List<Long> permissionIds) {
        roleService.assignPermissions(id, permissionIds);
        return Result.success();
    }

    @Operation(summary = "获取角色权限", description = "获取角色的权限ID列表")
    @GetMapping("/{id}/permissions")
    @RequirePermission("system:role")
    public Result<List<Long>> getPermissionIds(@PathVariable Long id) {
        List<Long> permissionIds = roleService.getPermissionIds(id);
        return Result.success(permissionIds);
    }
}
