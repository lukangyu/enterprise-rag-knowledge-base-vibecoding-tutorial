package com.graphrag.common.security.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
@Schema(description = "注册请求")
public class RegisterRequest {

    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度必须在3-50个字符之间")
    @Pattern(regexp = "^[a-zA-Z0-9_]+$", message = "用户名只能包含字母、数字和下划线")
    @Schema(description = "用户名", example = "testuser")
    private String username;

    @NotBlank(message = "密码不能为空")
    @Size(min = 8, max = 100, message = "密码长度必须在8-100个字符之间")
    @Pattern(regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).+$", message = "密码必须包含大小写字母和数字")
    @Schema(description = "密码", example = "Password123")
    private String password;

    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    @Schema(description = "邮箱", example = "test@example.com")
    private String email;

    @Schema(description = "手机号", example = "13800138000")
    private String phone;

    @Schema(description = "真实姓名", example = "测试用户")
    private String realName;
}
