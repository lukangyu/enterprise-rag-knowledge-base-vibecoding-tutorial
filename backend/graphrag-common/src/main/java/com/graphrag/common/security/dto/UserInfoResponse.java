package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "用户信息响应")
public class UserInfoResponse {

    @Schema(description = "用户ID")
    private Long id;

    @Schema(description = "用户名")
    private String username;

    @Schema(description = "邮箱")
    private String email;

    @Schema(description = "手机号")
    private String phone;

    @Schema(description = "真实姓名")
    private String realName;

    @Schema(description = "头像URL")
    private String avatar;

    @Schema(description = "性别:0-未知,1-男,2-女")
    private Integer gender;

    @Schema(description = "状态:0-正常,1-禁用")
    private Integer status;

    @Schema(description = "角色列表")
    private List<RoleInfo> roles;

    @Schema(description = "权限列表")
    private List<String> permissions;

    @Schema(description = "最后登录时间")
    private LocalDateTime lastLoginTime;

    @Schema(description = "创建时间")
    private LocalDateTime createdAt;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "角色信息")
    public static class RoleInfo {
        @Schema(description = "角色ID")
        private Long id;

        @Schema(description = "角色编码")
        private String roleCode;

        @Schema(description = "角色名称")
        private String roleName;
    }
}
