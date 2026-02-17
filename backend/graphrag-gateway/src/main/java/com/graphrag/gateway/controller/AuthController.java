package com.graphrag.gateway.controller;

import com.graphrag.common.core.domain.Result;
import com.graphrag.common.security.dto.*;
import com.graphrag.gateway.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "认证管理", description = "认证相关接口")
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @Operation(summary = "用户登录", description = "通过用户名密码登录，返回JWT令牌")
    @PostMapping("/login")
    public Result<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        LoginResponse response = authService.login(request);
        return Result.success(response);
    }

    @Operation(summary = "用户注册", description = "注册新用户账号")
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterRequest request) {
        authService.register(request);
        return Result.success();
    }

    @Operation(summary = "用户登出", description = "退出登录，撤销令牌")
    @PostMapping("/logout")
    public Result<Void> logout() {
        authService.logout();
        return Result.success();
    }

    @Operation(summary = "刷新令牌", description = "使用刷新令牌获取新的访问令牌")
    @PostMapping("/refresh")
    public Result<LoginResponse> refreshToken(@Valid @RequestBody RefreshTokenRequest request) {
        LoginResponse response = authService.refreshToken(request);
        return Result.success(response);
    }

    @Operation(summary = "获取当前用户信息", description = "获取当前登录用户的详细信息")
    @GetMapping("/me")
    public Result<UserInfoResponse> getCurrentUser() {
        UserInfoResponse userInfo = authService.getCurrentUser();
        return Result.success(userInfo);
    }
}
