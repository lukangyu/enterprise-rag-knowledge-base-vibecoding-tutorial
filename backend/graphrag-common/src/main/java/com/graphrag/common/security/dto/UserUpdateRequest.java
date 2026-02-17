package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Data
@Schema(description = "更新用户请求")
public class UserUpdateRequest {

    @Schema(description = "邮箱", example = "test@example.com")
    private String email;

    @Schema(description = "手机号", example = "13800138000")
    private String phone;

    @Schema(description = "真实姓名", example = "测试用户")
    private String realName;

    @Schema(description = "头像URL")
    private String avatar;

    @Schema(description = "性别:0-未知,1-男,2-女", example = "0")
    private Integer gender;

    @Schema(description = "状态:0-正常,1-禁用", example = "0")
    private Integer status;

    @Schema(description = "角色ID列表", example = "[3]")
    private List<Long> roleIds;
}
