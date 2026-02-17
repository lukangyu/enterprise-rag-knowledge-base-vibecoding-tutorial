package com.graphrag.gateway.controller;

import com.graphrag.common.core.domain.PageResult;
import com.graphrag.common.core.domain.Result;
import com.graphrag.common.security.annotation.RequirePermission;
import com.graphrag.common.security.dto.*;
import com.graphrag.common.security.entity.User;
import com.graphrag.gateway.service.AuthService;
import com.graphrag.gateway.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "用户管理", description = "用户管理相关接口")
@RestController
@RequestMapping("/system/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;
    private final AuthService authService;

    @Operation(summary = "用户列表", description = "分页查询用户列表")
    @GetMapping("/list")
    @RequirePermission("system:user:list")
    public Result<PageResult<User>> list(UserQueryRequest request) {
        PageResult<User> result = userService.listUsers(request);
        return Result.success(result);
    }

    @Operation(summary = "用户详情", description = "根据ID获取用户详情")
    @GetMapping("/{id}")
    @RequirePermission("system:user:list")
    public Result<User> getById(@PathVariable Long id) {
        User user = userService.getUserById(id);
        return Result.success(user);
    }

    @Operation(summary = "创建用户", description = "创建新用户")
    @PostMapping
    @RequirePermission("system:user:add")
    public Result<User> create(@Valid @RequestBody UserCreateRequest request) {
        User user = userService.createUser(request);
        return Result.success(user);
    }

    @Operation(summary = "更新用户", description = "更新用户信息")
    @PutMapping("/{id}")
    @RequirePermission("system:user:edit")
    public Result<User> update(@PathVariable Long id, @RequestBody UserUpdateRequest request) {
        User user = userService.updateUser(id, request);
        return Result.success(user);
    }

    @Operation(summary = "删除用户", description = "删除指定用户")
    @DeleteMapping("/{id}")
    @RequirePermission("system:user:delete")
    public Result<Void> delete(@PathVariable Long id) {
        userService.deleteUser(id);
        return Result.success();
    }

    @Operation(summary = "修改密码", description = "修改用户密码")
    @PutMapping("/{id}/password")
    @RequirePermission("system:user:edit")
    public Result<Void> updatePassword(@PathVariable Long id, @Valid @RequestBody PasswordUpdateRequest request) {
        userService.updatePassword(id, request);
        return Result.success();
    }

    @Operation(summary = "分配角色", description = "为用户分配角色")
    @PutMapping("/{id}/roles")
    @RequirePermission("system:user:edit")
    public Result<Void> assignRoles(@PathVariable Long id, @RequestBody List<Long> roleIds) {
        userService.assignRoles(id, roleIds);
        return Result.success();
    }

    @Operation(summary = "更新状态", description = "启用/禁用用户")
    @PutMapping("/{id}/status")
    @RequirePermission("system:user:edit")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        userService.updateStatus(id, status);
        return Result.success();
    }

    @Operation(summary = "重置密码", description = "重置用户密码为默认密码")
    @PutMapping("/{id}/reset-password")
    @RequirePermission("system:user:edit")
    public Result<Void> resetPassword(@PathVariable Long id) {
        userService.resetPassword(id);
        return Result.success();
    }

    @Operation(summary = "当前用户信息", description = "获取当前登录用户信息")
    @GetMapping("/me")
    public Result<UserInfoResponse> getCurrentUser() {
        UserInfoResponse userInfo = authService.getCurrentUser();
        return Result.success(userInfo);
    }
}
